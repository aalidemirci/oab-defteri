"""Denetim izi (TK16; tasarım §4.6.2-§4.6.3; plan F1b-1 alt commit c) — çekirdek testleri.

Varsayılan test ortamı kök `conftest.py`'dedir: oturum program yöneticisi hesabıyla açık,
yazar bağlamı o hesap; veritabanı kullanan testte hesabın satırı ve `TEST_IA`'lı iz
anahtarı kurulu, zincir boş. Kişi adları ve numaralar UYDURMADIR.

Bölümler: model ve göç (kapalı tür kümesi, ekleme-yalnızlık, tetikleyiciler) · yazıcı
(zincir, işlem ve yazar şartı, geri alınan işlem) · içerik MAC'i (program dışı değişiklik,
taşınmış token, bozuk alan) · hesap ve oturum olayları · KVKK (kaydın özeti).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date
from typing import Any

import pytest
from django.core.management import call_command
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from rest_framework.test import APIClient

from apps.okul import denetim_izi, iz_dogrulama, masaustu_kanca
from apps.okul.lock_middleware import AppLockMiddleware
from apps.okul.models import (
    Account,
    AccountRole,
    AccountStatus,
    AuditAction,
    AuditActor,
    AuditKeyMode,
    AuditTrail,
    ClassSection,
    Holiday,
    ImmutableRecord,
    ImportRun,
    Personnel,
    SchoolConfig,
    SchoolTerm,
    SchoolYear,
    Student,
    SuspendReason,
)
from apps.okul.oturum import (
    OTURUM,
    OturumDurumu,
    OturumHesabi,
    Yazar,
    kapanista_kilitle,
    sistem_olarak,
    yazar_olarak,
)
from apps.okul.services import app_password, hesaplar, persons
from apps.okul.services import setup as setup_service
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    YENI_PAROLA,
    durum,
    durum_yaz,
    ham_guncelle,
    hesap_ac,
    muhurle,
    sarmal,
)
from apps.okul.tests.iz_ortak import sahte_satir
from apps.okul.tests.oturum_ortak import SahteSaat, kurulum_durumunu_yaz, oturum_saatini_kur
from conftest import (
    TEST_DEK,
    TEST_HESAP_ADI,
    TEST_HESAP_ID,
    TEST_IA,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
    TEST_TANITICI,
    oturumu_ac_test,
)
from shared import bakim, crypto, kanonik

pytestmark = pytest.mark.django_db

HESAP = "okul.Account"
OKUL = "okul.SchoolConfig"
#: Göç 0009'un tetikleyici adları.
TETIKLEYICILER = ("okul_audittrail_no_delete", "okul_audittrail_no_update")


def satirlar(**suz: Any) -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(**suz).order_by("seq"))


def son_satir() -> AuditTrail:
    satir: AuditTrail | None = AuditTrail.objects.order_by("-seq").first()
    assert satir is not None
    return satir


def olay_yaz(object_id: str = TEST_HESAP_ID) -> AuditTrail:
    """Kayıt yazımı olmayan bir olay (işlem içinde; varsayılan yazar)."""
    with transaction.atomic():
        return denetim_izi.olay(AuditAction.KILIT, model=HESAP, object_id=object_id)


def tetikleyicisiz(sql: str, params: list[Any]) -> None:
    """Program DIŞINDAN yazım taklidi: tetikleyiciler bu işlemde düşürülür (test işlemi
    sonunda geri alınır; SQLite'ta tanım da işlemseldir)."""
    with connection.cursor() as cursor:
        for ad in TETIKLEYICILER:
            cursor.execute(f"DROP TRIGGER IF EXISTS {ad}")
        cursor.execute(sql, params)


# ============================================================ model ve göç


def test_tur_kumesi_anlik_goruntusu() -> None:
    """Tasarım §4.6.2: kapalı küme; yeni tür göçle eklenir (DB kısıtı da aynı kümedir)."""
    assert AuditAction.values == [
        "OLUSTUR",
        "GUNCELLE",
        "DURUM",
        "TERS_KAYIT",
        "ISARET",
        "BASIM",
        "KVKK_SILME",
        "GIRIS",
        "KILIT",
        "HESAP",
        "PAROLA",
        "KURTARMA",
        "YEDEK",
        "GOC",
        "GERI_YUKLEME",
        "DEK_YENILEME",
        "BUTUNLUK",
        "GUN_ISI",
    ]
    assert AuditActor.values == ["HESAP", "SISTEM"]
    assert AuditKeyMode.values == ["ACIK", "KILITLI"]


def test_kume_disi_tur_veritabaninda_reddedilir() -> None:
    satir = olay_yaz()
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO okul_audittrail (seq, at, actor, account_id, role, action, model, "
            'object_id, changed_fields, "values", record_mac, label, key_mode, key_ref, '
            "prev_mac, mac) VALUES (%s, %s, 'SISTEM', NULL, '', 'SIL', 'x', '1', '[]', '{}', "
            "'', '', 'ACIK', '1', %s, %s)",
            [satir.seq + 1, "2026-11-01 07:30:00", satir.mac, "0" * 64],
        )


def test_tetikleyiciler_goc_sonrasi_yerindedir() -> None:
    """Şema düzenleyicisi tabloyu yeniden kurarsa tetikleyiciler düşer; göçten sonra ikisi de var."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' "
            "AND tbl_name = 'okul_audittrail' ORDER BY name"
        )
        bulunan = cursor.fetchall()
    assert tuple(ad for ad, _ in bulunan) == TETIKLEYICILER
    assert all("RAISE(ABORT" in sql for _, sql in bulunan)
    assert "BEFORE DELETE" in bulunan[0][1] and "BEFORE UPDATE" in bulunan[1][1]


def test_ham_sql_ile_guncelleme_ve_silme_reddedilir() -> None:
    satir = olay_yaz()
    for sql in (
        "UPDATE okul_audittrail SET object_id = 'x' WHERE seq = %s",
        "DELETE FROM okul_audittrail WHERE seq = %s",
    ):
        with pytest.raises(IntegrityError, match="ekleme-yalnız"):
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute(sql, [satir.seq])
    assert AuditTrail.objects.get(seq=satir.seq).mac == satir.mac


def test_orm_ile_guncelleme_ve_silme_reddedilir() -> None:
    satir = olay_yaz()
    satir.object_id = "x"
    with pytest.raises(ImmutableRecord):
        satir.save()
    with pytest.raises(ImmutableRecord):
        satir.delete()
    with pytest.raises(ImmutableRecord):
        AuditTrail.objects.filter(seq=satir.seq).update(object_id="x")
    with pytest.raises(ImmutableRecord):
        AuditTrail.objects.all().delete()
    with pytest.raises(ImmutableRecord):
        AuditTrail.objects.bulk_update([satir], ["object_id"])
    assert AuditTrail.objects.get(seq=satir.seq).object_id == TEST_HESAP_ID


@pytest.mark.django_db(transaction=True)
def test_flush_tetikleyicileri_korur() -> None:
    """Testlerin `flush`'ı (kök conftest) satırları boşaltır, tetikleyici tanımları AYNEN kalır."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE tbl_name = 'okul_audittrail'")
        once = sorted(cursor.fetchall())
    olay_yaz()
    call_command("flush", verbosity=0, interactive=False)
    assert AuditTrail.objects.count() == 0
    with connection.cursor() as cursor:
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE tbl_name = 'okul_audittrail'")
        assert sorted(cursor.fetchall()) == once


# ============================================================ yazıcı: zincir ve şartlar


def test_zincir_satirlari_birbirine_baglanir_ve_dogrulanir() -> None:
    bir, iki, uc = olay_yaz(), olay_yaz(), olay_yaz()
    assert (bir.seq, iki.seq, uc.seq) == (1, 2, 3)
    assert bir.prev_mac == "" and iki.prev_mac == bir.mac and uc.prev_mac == iki.mac
    assert {s.key_ref for s in (bir, iki, uc)} == {str(denetim_izi.anahtari_coz(TEST_DEK).kayit_id)}
    assert denetim_izi.zinciri_dogrula() == []
    assert denetim_izi.son_satirlari_dogrula(2) == []
    assert denetim_izi.zincir_basi() == (3, uc.mac)


def test_mac_satirin_kanonik_bicimi_ve_ia_ile_hesaplanir() -> None:
    satir = olay_yaz()
    beklenen = kanonik.iz_mac(
        crypto.audit_chain_key(TEST_IA), denetim_izi.satir_alanlari(satir), satir.prev_mac
    )
    assert satir.mac == beklenen
    # Veritabanından okunan satır aynı baytlara kodlanır (zaman UTC, kimlik tireli).
    okunan = AuditTrail.objects.get(seq=satir.seq)
    assert kanonik.iz_satiri(denetim_izi.satir_alanlari(okunan)) == kanonik.iz_satiri(
        denetim_izi.satir_alanlari(satir)
    )


def test_geri_alinan_islemden_sonra_bosluk_ve_bayat_kuyruk_yok() -> None:
    """Önizleme işlemi geri sarar: kuyruk bellekte tutulsaydı geri alınan satıra bağlanırdı."""
    bir = olay_yaz()
    with pytest.raises(RuntimeError), transaction.atomic():
        geri_alinan = denetim_izi.olay(AuditAction.KILIT, model=HESAP, object_id=TEST_HESAP_ID)
        assert geri_alinan.seq == 2
        raise RuntimeError("önizleme geri sarıldı")
    with transaction.atomic():
        denetim_izi.olay(AuditAction.KILIT, model=HESAP, object_id=TEST_HESAP_ID)
        transaction.set_rollback(True)  # içe aktarma önizlemesinin yolu
    iki = olay_yaz()
    assert iki.seq == 2 and iki.prev_mac == bir.mac
    assert denetim_izi.zinciri_dogrula() == []


@pytest.mark.django_db(transaction=True)
def test_islem_disinda_yazilmaz_islemler_arasi_zincir_bozulmaz() -> None:
    """Yazma kuralı 1: iz satırı veri satırıyla aynı işlemde; işlem dışında yazılmaz."""
    with pytest.raises(denetim_izi.IzYazilamadi, match="işlem"):
        denetim_izi.olay(AuditAction.KILIT, model=HESAP, object_id=TEST_HESAP_ID)
    assert AuditTrail.objects.count() == 0
    bir = olay_yaz()
    with pytest.raises(RuntimeError), transaction.atomic():
        denetim_izi.olay(AuditAction.KILIT, model=HESAP, object_id=TEST_HESAP_ID)
        raise RuntimeError("işlem düştü")
    iki = olay_yaz()
    assert (bir.seq, iki.seq) == (1, 2) and iki.prev_mac == bir.mac
    assert denetim_izi.zinciri_dogrula() == []


def test_yazar_baglami_yoksa_yazilmaz() -> None:
    with yazar_olarak(None), transaction.atomic():
        with pytest.raises(denetim_izi.IzYazilamadi, match="Yazar bağlamı"):
            denetim_izi.olay(AuditAction.KILIT, model=HESAP, object_id=TEST_HESAP_ID)
        with pytest.raises(denetim_izi.IzYazilamadi):
            setup_service.set_idle_lock_minutes(dakika=15)
    assert AuditTrail.objects.count() == 0
    assert SchoolConfig.load().idle_lock_minutes == 10  # veri yazımı da geri alındı


def test_sistem_yazari_hesapsiz_ve_rolsuz_yazilir() -> None:
    with sistem_olarak():
        satir = olay_yaz()
    assert (satir.actor, satir.account_id, satir.role) == ("SISTEM", None, "")


def test_yazar_istek_basindaki_baglamdir_oturum_istekte_degisse_de() -> None:
    """Oturum istek sürerken başka hesaba geçse de yazar açılıştaki hesaptır (TK16)."""
    muhasip = hesap_ac(AccountRole.MUHASIP, ad="Örnek Muhasip")

    def gorunum(_request: HttpRequest) -> HttpResponse:
        oturumu_ac_test(str(muhasip.id), tanitici=muhasip.login_name, rol="muhasip")
        setup_service.set_idle_lock_minutes(dakika=15)
        return HttpResponse("tamam")

    with yazar_olarak(None):
        AppLockMiddleware(gorunum)(RequestFactory().put("/api/v1/security/idle-lock/"))

    satir = son_satir()
    assert (satir.model, satir.action) == (OKUL, "GUNCELLE")
    assert (str(satir.account_id), satir.role) == (TEST_HESAP_ID, "yonetici")


def test_bellekteki_iz_anahtari_etkin_kayit_degilse_yazilmaz() -> None:
    crypto.load_key(TEST_DEK, audit_key=b"\x01" * 32)
    with pytest.raises(denetim_izi.IzYazilamadi, match="etkin anahtar değil"):
        olay_yaz()


def test_kilitliyken_acik_kipte_yazilmaz_ret_409_ailesindendir() -> None:
    app_password.lock()
    with pytest.raises(crypto.KeyMissingError):
        olay_yaz()


def test_izinsiz_alanin_degeri_yazilamaz() -> None:
    with transaction.atomic(), pytest.raises(denetim_izi.IzYazilamadi, match="display_name"):
        denetim_izi.olay(
            AuditAction.HESAP,
            model=HESAP,
            object_id=TEST_HESAP_ID,
            values={"display_name": ["", "Örnek Kişi"]},
        )
    with transaction.atomic(), pytest.raises(denetim_izi.IzYazilamadi, match="değeri"):
        denetim_izi.olay(
            AuditAction.KURTARMA,
            model=denetim_izi.KURTARMA_ANAHTARI,
            object_id="1",
            values={"sarmal": ["x", "y"]},
        )


def test_listesiz_model_izlenmez() -> None:
    """İzin listelerini tanımlamayan model izlenemez (iz anahtarının kendisi izlenmez)."""
    from apps.okul.models import AuditKey

    with transaction.atomic(), pytest.raises(denetim_izi.IzYazilamadi, match="listelerini"):
        denetim_izi.kayit(AuditAction.GUNCELLE, AuditKey(pk=1), onceki=None)


@pytest.mark.parametrize(
    "model",
    [
        Account,
        SchoolConfig,
        SchoolYear,
        SchoolTerm,
        Holiday,
        Student,
        Personnel,
        ClassSection,
        ImportRun,
    ],
    ids=lambda m: m.__name__,
)
def test_izin_listeleri_modelin_alanlarini_eksiksiz_siniflar(model: Any) -> None:
    """Kimlik dışındaki her alan ya içerik MAC'indedir ya MAC dışıdır (§4.6.2'nin MAC dışı
    alanları: KVKK gereği boşaltılan ya da SİLİNEN alanlar — tasarım §5 O4; veli listesi
    okul çekirdeğinde yok); değer listesi özetin alt kümesidir, şifreli alan içermez. MAC
    dışı alan yalnız KVKK silme kümesindeki modelin (değer listesi boş) kişi alanıdır."""
    alanlar = {a.name for a in model._meta.concrete_fields if not a.primary_key}
    ozet = set(model.IZ_OZET_ALANLARI)
    mac_disi = set(getattr(model, "IZ_MAC_DISI_ALANLARI", ()))
    assert ozet | mac_disi == alanlar and not ozet & mac_disi
    assert set(model.IZ_DEGER_ALANLARI) <= ozet
    sifreli = {a.name for a in crypto.encrypted_fields_of(model)}
    assert not sifreli & set(model.IZ_DEGER_ALANLARI)
    if mac_disi:
        assert model in (Student, Personnel) and model.IZ_DEGER_ALANLARI == ()
        assert sifreli <= mac_disi  # silinen kişi verisinin hiçbiri MAC'e girmez


@pytest.mark.parametrize(
    ("model", "kisi_alanlari"),
    [
        (Personnel, {"first_name": "Uydurgül", "last_name": "Masalcıoğlu"}),
        (
            Student,
            {
                "first_name": "Uydurgül",
                "last_name": "Masalcıoğlu",
                "student_number": "9090",
            },
        ),
    ],
    ids=["Personnel", "Student"],
)
def test_kvkk_silme_kumesinin_kisi_alanlari_icerik_macina_girmez(
    model: Any, kisi_alanlari: dict[str, str]
) -> None:
    """Tasarım §5 O4: silinen kişinin adı, soyadı ve okul no'su içerik MAC'inden aday
    sözlüğüyle geri bulunamaz — MAC bu alanlar değişince DEĞİŞMEZ; MAC'teki öteki alan
    (ayrılış) değişince değişir. Kişi verisi UYDURMADIR."""
    kayit: Personnel | Student
    if model is Personnel:
        kayit = persons.create_personnel(first_name="Uydurnur", last_name="Örnekkaya")
    else:
        kayit = persons.create_student(
            first_name="Uydurcan", last_name="Örnekoğlu", student_number="501", class_level=9
        )
    once = denetim_izi.kayit_mac_hesapla(model, kayit.pk)
    ek = {"student_number_index": "0" * 64} if model is Student else {}
    # Program dışı yazım taklidi (şifreli değer geçerli token'dır; iz satırı yazılmaz).
    model._base_manager.filter(pk=kayit.pk).update(**kisi_alanlari, **ek)
    assert model._base_manager.get(pk=kayit.pk).first_name == "Uydurgül"
    assert denetim_izi.kayit_mac_hesapla(model, kayit.pk) == once
    assert denetim_izi.kaydi_dogrula(model, kayit.pk) is True
    model._base_manager.filter(pk=kayit.pk).update(left_at=date(2026, 11, 2))
    assert denetim_izi.kayit_mac_hesapla(model, kayit.pk) != once


def test_degerlerde_serbest_metin_ve_kisi_adi_yok() -> None:
    """Kaydın özeti (R1): okul adı, il, ilçe, kısa ad, müdür adı, tanıtıcı değer taşımaz."""
    assert not {
        "school_name",
        "province",
        "district",
        "kisa_ad",
        "principal_name",
        "kutuphane_saatleri",
        "app_password_hash",
        "yol_haritasi",
    } & set(SchoolConfig.IZ_DEGER_ALANLARI)
    assert not {"login_name", "display_name", "seal"} & set(Account.IZ_DEGER_ALANLARI)


# ============================================================ içerik MAC'i (kaydın özeti)


def test_okul_karti_yazimi_degerleri_ve_icerik_macini_tasir() -> None:
    setup_service.set_idle_lock_minutes(dakika=15)
    satir = son_satir()
    assert (satir.action, satir.model, satir.object_id) == ("GUNCELLE", OKUL, "1")
    assert satir.changed_fields == ["updated_at", "idle_lock_minutes"]
    assert satir.values == {"idle_lock_minutes": [10, 15]}
    assert satir.record_mac == denetim_izi.kayit_mac_hesapla(SchoolConfig, 1)
    assert denetim_izi.kaydi_dogrula(SchoolConfig, 1) is True


def test_okul_bilgilerinin_metni_yalniz_alan_adiyla_gorunur() -> None:
    setup_service.update_school_config(
        fields={
            "school_name": "Uydurma Ortaokulu",
            "principal_name": "Örnek Müdür",
            "kademe": "ORTAOKUL",
        }
    )
    satir = son_satir()
    assert {"school_name", "principal_name", "kademe"} <= set(satir.changed_fields)
    assert satir.values == {"kademe": ["", "ORTAOKUL"]}


def test_program_disindan_degisiklik_icerik_macinda_gorunur() -> None:
    setup_service.set_idle_lock_minutes(dakika=15)
    assert denetim_izi.kaydi_dogrula(SchoolConfig, 1) is True
    ham_okul = "UPDATE okul_schoolconfig SET idle_lock_minutes = 30 WHERE id = 1"
    with connection.cursor() as cursor:
        cursor.execute(ham_okul)
    assert denetim_izi.kaydi_dogrula(SchoolConfig, 1) is False


def test_satirlar_arasi_tasinmis_ad_tokeni_gorunur() -> None:
    """Geçerli bir Fernet token'ı başka satıra taşınınca çözülür ama içerik MAC'i tutmaz (GA-9)."""
    birinci = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Birinci")
    ikinci = hesap_ac(AccountRole.SEKRETER, ad="Uydurma İkinci")
    assert denetim_izi.kaydi_dogrula(Account, birinci.id) is True
    assert denetim_izi.kaydi_dogrula(Account, ikinci.id) is True
    with connection.cursor() as cursor:
        cursor.execute("SELECT display_name FROM okul_account WHERE id = %s", [birinci.id.hex])
        token = cursor.fetchone()[0]
    ham_guncelle(ikinci.id, display_name=token)
    assert Account.objects.get(pk=ikinci.id).display_name == "Uydurma Birinci"  # çözülür
    assert denetim_izi.kaydi_dogrula(Account, ikinci.id) is False
    assert denetim_izi.kaydi_dogrula(Account, birinci.id) is True


def test_sifreli_sutuna_duz_metin_bozuk_alan_olarak_ozetlenir() -> None:
    """D48: `CorruptField` hata vermez, düz metne çevrilmez; içerik MAC'i değişir."""
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Kişi")
    ham_guncelle(hesap.id, display_name="Düz Yazılmış Ad")
    okunan = Account.objects.get(pk=hesap.id)
    assert crypto.is_corrupt(okunan.display_name)
    assert denetim_izi.kaydi_dogrula(Account, hesap.id) is False
    alanlar = denetim_izi.anlik(okunan)
    assert alanlar["display_name"] == kanonik.bozuk_alan("Düz Yazılmış Ad")
    # Belirlenimci: aynı ham değer aynı MAC'i verir.
    assert denetim_izi.kayit_mac_hesapla(Account, hesap.id) == denetim_izi.kayit_mac_hesapla(
        Account, hesap.id
    )


def test_izsiz_kayit_dogrulanamaz() -> None:
    assert denetim_izi.kaydi_dogrula(Account, TEST_HESAP_ID) is None


# ============================================================ zincir doğrulama bulguları


def test_program_disindan_degistirilen_satir_mac_tutmaz() -> None:
    olay_yaz()
    iki = olay_yaz()
    olay_yaz()
    tetikleyicisiz("UPDATE okul_audittrail SET object_id = %s WHERE seq = %s", ["baska", iki.seq])
    assert denetim_izi.zinciri_dogrula() == [denetim_izi.ZincirBulgusu(2, denetim_izi.MAC_TUTMADI)]


def test_silinen_ara_satir_sira_boslugu_ve_kopuk_zincirdir() -> None:
    olay_yaz()
    iki = olay_yaz()
    olay_yaz()
    tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [iki.seq])
    assert denetim_izi.zinciri_dogrula() == [
        denetim_izi.ZincirBulgusu(3, denetim_izi.SIRA_BOSLUGU),
        denetim_izi.ZincirBulgusu(3, denetim_izi.ZINCIR_KOPUK),
    ]


def test_aralik_dogrulamasi_onceki_satira_baglanir() -> None:
    for _ in range(4):
        olay_yaz()
    assert denetim_izi.zinciri_dogrula(ilk=3, son=4) == []
    tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = 2", [])
    assert denetim_izi.zinciri_dogrula(ilk=3) == [
        denetim_izi.ZincirBulgusu(3, denetim_izi.SIRA_BOSLUGU)
    ]


def _ham_kilitli_satir(seq: int, prev_mac: str, key_ref: str) -> None:
    """Program DIŞINDAN eklenmiş kilitli kip satırı (sahte MAC'le)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO okul_audittrail (seq, at, actor, account_id, role, action, model, "
            'object_id, changed_fields, "values", record_mac, label, key_mode, key_ref, '
            "prev_mac, mac) VALUES (%s, '2026-11-01 07:30:00', 'SISTEM', NULL, '', 'YEDEK', "
            "'yedek', 'x', '[]', '{}', '', '', 'KILITLI', %s, %s, %s)",
            [seq, key_ref, prev_mac, "0" * 64],
        )


def test_kilitli_kip_satirinin_anahtari_veritabanindan_turer_sahtesi_tutmaz() -> None:
    """Kilitli satırın anahtarı çapa satırından ve İA'dan türer (`kilitli_zincir_anahtarlari`):
    sahte MAC tutmaz; biçimsiz başvurunun anahtarı yoktur; verilen çözücü kullanılır."""
    bir = olay_yaz()
    _ham_kilitli_satir(2, bir.mac, "1:0")
    assert denetim_izi.zinciri_dogrula() == [denetim_izi.ZincirBulgusu(2, denetim_izi.MAC_TUTMADI)]
    assert denetim_izi.zinciri_dogrula(kilitli_anahtar=lambda _s: None) == [
        denetim_izi.ZincirBulgusu(2, denetim_izi.ANAHTAR_YOK)
    ]


@pytest.mark.parametrize("key_ref", ["bozuk", "1:x", "0:0", f"1:{denetim_izi.AZAMI_ADIM + 1}"])
def test_kilitli_kip_satirinin_bicimsiz_ya_da_sinir_disi_basvurusu_anahtarsizdir(
    key_ref: str,
) -> None:
    bir = olay_yaz()
    _ham_kilitli_satir(2, bir.mac, key_ref)
    assert denetim_izi.zinciri_dogrula() == [denetim_izi.ZincirBulgusu(2, denetim_izi.ANAHTAR_YOK)]


@pytest.mark.parametrize("key_ref", ["²", "١", "1²", " 1", "-1", ""])
def test_acik_kip_basvurusu_yalniz_ascii_rakamdir_bicimsizi_anahtarsizdir(key_ref: str) -> None:
    """`"²".isdigit()` doğrudur ama `int("²")` çevirmez: program dışından yazılmış böyle bir
    `key_ref` doğrulamayı istisnayla kesmez; satırın bulgusu `anahtar_yok`, sonraki satırlar
    yine doğrulanır, kayıt bütünlüğü tutmaz (False)."""
    setup_service.set_idle_lock_minutes(dakika=15)
    satir = son_satir()
    olay_yaz()
    tetikleyicisiz("UPDATE okul_audittrail SET key_ref = %s WHERE seq = %s", [key_ref, satir.seq])
    tetikleyicisiz("UPDATE okul_audittrail SET object_id = 'x' WHERE seq = %s", [satir.seq + 1])
    assert denetim_izi.acik_ref_coz(key_ref) is None
    assert denetim_izi.zinciri_dogrula() == [
        denetim_izi.ZincirBulgusu(satir.seq, denetim_izi.ANAHTAR_YOK),
        denetim_izi.ZincirBulgusu(satir.seq + 1, denetim_izi.MAC_TUTMADI),
    ]
    assert denetim_izi.kaydi_dogrula(SchoolConfig, 1) is False


def test_ikili_prev_mac_dogrulamayi_kesmez_onceki_bulgular_kaybolmaz() -> None:
    """Bağımsız denetim bulgusu: sırrı olmayan biri sona `prev_mac`'i ikili (BLOB) bir satır
    ekler. `kanonik.esit(bytes, …)` `AttributeError` veriyor, doğrulama yarıda düşüyor, o ana
    dek toplanan gerçek değişiklik (`mac_tutmadi`) kayboluyor, kilit açılışı yalnız
    "denetlenemedi" yazıyordu. Artık satır kuralı çiğner (değişiklik), denetim sürer."""
    bir = olay_yaz()
    olay_yaz()
    tetikleyicisiz("UPDATE okul_audittrail SET object_id = 'x' WHERE seq = %s", [bir.seq])
    ikili = sahte_satir(ham={"prev_mac": b"\x00" * 32})
    sonraki = sahte_satir()  # ardına biçimi doğru bir satır: program yazmayı sürdürür

    assert isinstance(ikili.prev_mac, bytes)
    assert denetim_izi.satir_kurali_tutuyor(ikili) is False
    assert denetim_izi.zinciri_dogrula() == [
        denetim_izi.ZincirBulgusu(bir.seq, denetim_izi.MAC_TUTMADI),
        denetim_izi.ZincirBulgusu(ikili.seq, denetim_izi.ZINCIR_KOPUK),
        denetim_izi.ZincirBulgusu(ikili.seq, denetim_izi.MUHURSUZ),
        denetim_izi.ZincirBulgusu(ikili.seq, denetim_izi.SATIR_KURALI),
        denetim_izi.ZincirBulgusu(ikili.seq, denetim_izi.MAC_TUTMADI),
        denetim_izi.ZincirBulgusu(sonraki.seq, denetim_izi.MUHURSUZ),
    ]


def test_ikili_mac_satiri_kurali_cigner_kart_suzgecini_dusurmez() -> None:
    """Bağımsız denetim bulgusu: `mac` sütunu ikili (BLOB), anahtar başvurusu geçerli açık kip
    satırı kartların süzgecini (`acik_satir_dogrulayici`) `AttributeError` ile düşürüyor, Son
    Girişler "okunamadı" oluyordu. Artık süzgeçten geçmez; zincirde değişiklik bulgusudur."""
    bir = olay_yaz()
    ikili = sahte_satir(key_mode="ACIK", key_ref=bir.key_ref, ham={"mac": b"\x00" * 32})
    sonraki = sahte_satir(prev_mac="0" * 64)

    assert isinstance(ikili.mac, bytes)
    assert denetim_izi.acik_satir_dogrulayici()(ikili) is False
    assert denetim_izi.zinciri_dogrula() == [
        denetim_izi.ZincirBulgusu(ikili.seq, denetim_izi.SATIR_KURALI),
        denetim_izi.ZincirBulgusu(ikili.seq, denetim_izi.MAC_TUTMADI),
        denetim_izi.ZincirBulgusu(sonraki.seq, denetim_izi.ZINCIR_KOPUK),
        denetim_izi.ZincirBulgusu(sonraki.seq, denetim_izi.MUHURSUZ),
    ]


@pytest.mark.parametrize("ham", [{"key_ref": b"1"}, {"key_ref": b"1:0", "key_mode": "KILITLI"}])
def test_ikili_anahtar_basvurusu_anahtarsizdir_kurali_cigner(ham: dict[str, Any]) -> None:
    """`bytes.isdigit` doğrudur, `int(b"1")` çevirir: ikili başvuru yine de başvuru değildir;
    kilitli kipte `bytes.split(":")` doğrulamayı istisnayla keserdi."""
    olay_yaz()
    satir = sahte_satir(key_mode="ACIK", key_ref="1", ham=ham)

    assert denetim_izi.acik_ref_coz(satir.key_ref) is None
    assert denetim_izi.kilitli_ref_coz(satir.key_ref) is None
    assert denetim_izi.zinciri_dogrula() == [
        denetim_izi.ZincirBulgusu(satir.seq, denetim_izi.SATIR_KURALI),
        denetim_izi.ZincirBulgusu(satir.seq, denetim_izi.ANAHTAR_YOK),
    ]


def test_satirin_beklenmeyen_hatasi_o_satirin_bulgusudur_denetim_surer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bir satırın denetimi beklenmeyen bir hata verirse o satırın bulgusu `satir_kurali` olur;
    önceki ve sonraki satırların bulguları kaybolmaz. Kartın süzgeci o satırı atlar. Veritabanı
    hatası ise yükselir (bulgu uydurulmaz; kilit açılışı "denetlenemedi" yazar)."""
    bir = olay_yaz()
    iki = olay_yaz()
    uc = olay_yaz()
    tetikleyicisiz("UPDATE okul_audittrail SET object_id = 'x' WHERE seq = %s", [bir.seq])
    tetikleyicisiz("UPDATE okul_audittrail SET object_id = 'y' WHERE seq = %s", [uc.seq])
    asil = denetim_izi.mac_tutuyor

    def bicimsiz(anahtar: bytes, satir: AuditTrail) -> bool:
        if satir.seq == iki.seq:
            raise RuntimeError("program dışından yazılmış beklenmeyen biçim")
        return asil(anahtar, satir)

    monkeypatch.setattr(denetim_izi, "mac_tutuyor", bicimsiz)
    assert denetim_izi.zinciri_dogrula() == [
        denetim_izi.ZincirBulgusu(bir.seq, denetim_izi.MAC_TUTMADI),
        denetim_izi.ZincirBulgusu(iki.seq, denetim_izi.SATIR_KURALI),
        denetim_izi.ZincirBulgusu(uc.seq, denetim_izi.MAC_TUTMADI),
    ]
    assert denetim_izi.acik_satir_dogrulayici()(AuditTrail.objects.get(seq=iki.seq)) is False

    def kilitli_vt(*_a: object, **_k: object) -> bool:
        raise DatabaseError("database is locked")

    monkeypatch.setattr(denetim_izi, "mac_tutuyor", kilitli_vt)
    with pytest.raises(DatabaseError):
        denetim_izi.zinciri_dogrula()
    with pytest.raises(DatabaseError):
        denetim_izi.acik_satir_dogrulayici()(AuditTrail.objects.get(seq=iki.seq))


@pytest.mark.parametrize(
    "alanlar",
    [
        # Mühürsüz anahtarla, hesabın adına sahte bir giriş (kısıtlar kapatılarak).
        {
            "action": "GIRIS",
            "actor": "HESAP",
            "account": TEST_HESAP_ID,
            "role": "yonetici",
            "model": "okul.Account",
            "object_id": TEST_HESAP_ID,
        },
        # Kapalı küme dışı tür (SISTEM bile olsa).
        {"action": "GERI_YUKLEME", "model": denetim_izi.GERI_YUKLEME_KAYDI},
        # Kilitli kipte içerik MAC'i.
        {"record_mac": "ab" * 32},
        # Ne açık ne kilitli kip: kilitli sayılmaz, anahtarı yoktur.
        {"key_mode": "XYZ"},
    ],
    ids=["sahte-giris", "kume-disi", "icerik-maci", "gecersiz-kip"],
)
def test_kuralina_uymayan_satir_mac_tutsa_da_bulgudur(alanlar: dict[str, Any]) -> None:
    """Tasarım §4.6.3 "satır da mühürlü gibi görünmez": mühürsüz (sırsız) anahtarla MAC'i
    doğru hesaplanmış satır yalnız kapalı kümedeki kişisiz SISTEM olayı olabilir. Kuralı
    çiğneyen satır `satir_kurali` bulgusudur; geçersiz kipteki satır kilitli sayılmaz.
    Kartların süzgeci hiçbirini geçirmez."""
    olay_yaz()
    satir = sahte_satir(**alanlar)
    assert satir.seq == 2
    assert denetim_izi.satir_kurali_tutuyor(satir) is False
    bulgular = denetim_izi.zinciri_dogrula()
    if alanlar.get("key_mode") == "XYZ":
        assert bulgular == [
            denetim_izi.ZincirBulgusu(2, denetim_izi.SATIR_KURALI),
            denetim_izi.ZincirBulgusu(2, denetim_izi.ANAHTAR_YOK),
        ]
    else:
        # MAC sırsız anahtarla doğru: kural olmasa yalnız "mühürsüz" sayılırdı.
        assert bulgular == [
            denetim_izi.ZincirBulgusu(2, denetim_izi.MUHURSUZ),
            denetim_izi.ZincirBulgusu(2, denetim_izi.SATIR_KURALI),
        ]
    assert denetim_izi.acik_satir_dogrulayici()(satir) is False


def test_kurala_uyan_muhursuz_satir_yalniz_muhursuz_bulgusudur_kartlara_gecmez() -> None:
    """Kısıtları kapatmadan da eklenebilen satır (kapalı kümedeki SISTEM olayı): kurala uyar,
    bulgusu `muhursuz`; açık kipte mühürlü olmadığı için kart süzgecinden geçmez."""
    bir = olay_yaz()
    satir = sahte_satir(kisitsiz=False, action="BUTUNLUK", model=denetim_izi.IZ_DOGRULAMASI)
    assert denetim_izi.satir_kurali_tutuyor(satir) is True
    assert denetim_izi.zinciri_dogrula() == [denetim_izi.ZincirBulgusu(2, denetim_izi.MUHURSUZ)]
    gecerli = denetim_izi.acik_satir_dogrulayici()
    assert gecerli(satir) is False and gecerli(bir) is True


# ============================================================ hesap ve oturum olayları


def test_ilk_hesap_zincirin_ilk_satirlarini_o_hesapla_yazar(parolasiz: object) -> None:
    app_password.enable(tanitici="yonetici", display_name="Uydurma Yönetici", password=YENI_PAROLA)
    hesap = Account.objects.get()
    ilk = satirlar()
    assert [(s.action, s.model) for s in ilk] == [
        ("HESAP", HESAP),
        ("KURTARMA", denetim_izi.KURTARMA_ANAHTARI),
        ("OLUSTUR", OKUL),
    ]
    assert {(str(s.account_id), s.role, s.actor) for s in ilk} == {
        (str(hesap.id), "yonetici", "HESAP")
    }
    assert ilk[0].values["status"] == [None, "ACIK"]
    assert ilk[1].object_id == "1" and ilk[1].values["no"] == [None, 1]
    assert "app_password_hash" in ilk[2].changed_fields
    assert denetim_izi.zinciri_dogrula() == []
    assert denetim_izi.kaydi_dogrula(Account, hesap.id) is True


def test_kurulum_veritabani_islemi_duserse_iz_satiri_da_kalmaz(
    parolasiz: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    def patla(_value: str) -> None:
        raise RuntimeError("kesinti")

    monkeypatch.setattr(app_password, "_write_fingerprint", patla)
    with pytest.raises(RuntimeError):
        app_password.enable(
            tanitici="yonetici", display_name="Uydurma Yönetici", password=YENI_PAROLA
        )
    assert AuditTrail.objects.count() == 0


def test_kilit_acilisi_o_hesabin_giris_satirini_yazar(kilitli: object) -> None:
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    satir = son_satir()
    assert (satir.action, satir.model, satir.object_id) == ("GIRIS", HESAP, TEST_HESAP_ID)
    assert (str(satir.account_id), satir.role) == (TEST_HESAP_ID, "yonetici")
    assert satir.changed_fields == ["last_login_at"]
    assert satir.values["last_login_at"][0] is None
    assert denetim_izi.kaydi_dogrula(Account, TEST_HESAP_ID) is True


def test_parola_yenilenerek_acilista_parola_ve_giris_satirlari(kilitli: object) -> None:
    muhurle(Account.objects.get(pk=TEST_HESAP_ID), status=AccountStatus.PAROLA_YENILENMELI)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA, new_password=YENI_PAROLA)
    parola, giris = satirlar()
    assert (parola.action, giris.action) == ("PAROLA", "GIRIS")
    assert parola.values["status"] == ["PAROLA_YENILENMELI", "ACIK"]
    assert {str(parola.account_id), str(giris.account_id)} == {TEST_HESAP_ID}


def test_iz_yazilamazsa_oturum_acilmaz_anahtarlar_duser(
    kilitli: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    def yazilamadi(*_a: object, **_k: object) -> None:
        raise denetim_izi.IzYazilamadi("deneme")

    monkeypatch.setattr(denetim_izi, "kayit", yazilamadi)
    with pytest.raises(denetim_izi.IzYazilamadi):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert OTURUM.hesap() is None and crypto.is_unlocked() is False
    assert Account.objects.get(pk=TEST_HESAP_ID).last_login_at is None


def _yazilamadi(*_a: object, **_k: object) -> None:
    raise denetim_izi.IzYazilamadi("deneme")


def _dosya_kilitli(*_a: object, **_k: object) -> None:
    raise OSError("dosyayı başka bir program tutuyor")


@pytest.mark.parametrize(
    ("hedef", "yer"),
    [(iz_dogrulama, "yaz"), (app_password, "ensure_public_config")],
    ids=["islemde-iz-yazilamadi", "islemden-once-dosya-hatasi"],
)
def test_kurtarmayla_acilis_duserse_parola_degismez_iz_ve_bildirim_kalmaz(
    kilitli: object, monkeypatch: pytest.MonkeyPatch, hedef: object, yer: str
) -> None:
    """Sarmal, `KURTARMA` ve `GIRIS` satırlarından SONRA aynı işlemde yazılır: işlem düşen
    kurtarma girişinde program yöneticisinin parolası DEĞİŞMEZ. Kurtarma anahtarını elinde
    tutan biri parolayı izde `KURTARMA` satırı ve sahibine bildirim olmadan yenileyemez
    (tasarım §4.3 tehdit 10 ve 12, §4.4.3)."""
    once = sarmal(TEST_HESAP_ID)
    with monkeypatch.context() as yama, pytest.raises((denetim_izi.IzYazilamadi, OSError)):
        yama.setattr(hedef, yer, _yazilamadi if yer == "yaz" else _dosya_kilitli)
        app_password.unlock_with_recovery(
            recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_TANITICI, new_password=YENI_PAROLA
        )

    assert sarmal(TEST_HESAP_ID) == once
    assert OTURUM.hesap() is None and crypto.is_unlocked() is False
    assert not satirlar(action="KURTARMA")
    hesap = Account.objects.get(pk=TEST_HESAP_ID)
    assert (hesap.reset_notice_pending, hesap.reset_kind) == (False, "")
    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)  # eski parola açar


def test_parola_yenilenerek_acilis_duserse_parola_degismez(
    kilitli: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Geçici ya da süresi dolan parolanın kilit açılışında yenilenmesi de aynı sıradadır:
    işlem düşerse sarmal değişmez, satır `PAROLA_YENILENMELI` kalır, `PAROLA` satırı yoktur."""
    muhurle(Account.objects.get(pk=TEST_HESAP_ID), status=AccountStatus.PAROLA_YENILENMELI)
    once = sarmal(TEST_HESAP_ID)
    with monkeypatch.context() as yama, pytest.raises(denetim_izi.IzYazilamadi):
        yama.setattr(iz_dogrulama, "yaz", _yazilamadi)
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA, new_password=YENI_PAROLA)

    assert sarmal(TEST_HESAP_ID) == once
    assert not satirlar(action="PAROLA")
    assert Account.objects.get(pk=TEST_HESAP_ID).status == AccountStatus.PAROLA_YENILENMELI
    with pytest.raises(app_password.PasswordRenewalRequired):  # eski parola hâlâ açar
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


def test_kurtarma_anahtariyla_acilis_kurtarma_ve_giris_satirlari(kilitli: object) -> None:
    app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_TANITICI, new_password=YENI_PAROLA
    )
    kurtarma, giris = satirlar()
    assert (kurtarma.action, kurtarma.model, kurtarma.object_id) == (
        "KURTARMA",
        HESAP,
        TEST_HESAP_ID,
    )
    assert kurtarma.values["reset_kind"] == ["", "KURTARMA"]
    assert kurtarma.values["reset_notice_pending"] == [False, True]
    assert "opened_at" not in kurtarma.changed_fields  # var olan hesap; yeni değil
    assert giris.action == "GIRIS"
    assert {str(kurtarma.account_id), str(giris.account_id)} == {TEST_HESAP_ID}
    assert denetim_izi.zinciri_dogrula() == []


def test_girista_muhur_tutmazsa_butunluk_satiri_sistemle_satir_degismez(kilitli: object) -> None:
    ham_guncelle(TEST_HESAP_ID, role="muhasip")
    with pytest.raises(app_password.AccountSealMismatch):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    satir = son_satir()
    assert (satir.action, satir.actor, satir.account_id) == ("BUTUNLUK", "SISTEM", None)
    assert (satir.model, satir.object_id, satir.changed_fields) == (HESAP, TEST_HESAP_ID, ["seal"])
    assert Account.objects.get(pk=TEST_HESAP_ID).role == "muhasip"  # dokunulmadı
    assert OTURUM.hesap() is None and crypto.is_unlocked() is False
    oturumu_ac_test()
    assert denetim_izi.zinciri_dogrula() == []


def test_elle_kilit_hesabin_bosta_kilit_sistemin_satiridir() -> None:
    kurulum_durumunu_yaz(tamam=True)
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"
    elle = son_satir()
    assert (elle.action, str(elle.account_id), elle.object_id) == (
        "KILIT",
        TEST_HESAP_ID,
        TEST_HESAP_ID,
    )

    oturumu_ac_test()
    saat = SahteSaat()
    oturum_saatini_kur(saat)
    saat.ilerlet(10 * 60)
    OTURUM.degerlendir()
    bosta = son_satir()
    assert (bosta.action, bosta.actor, bosta.object_id) == ("KILIT", "SISTEM", TEST_HESAP_ID)
    assert crypto.is_unlocked() is False
    # Satırlar anahtarlar düşmeden, açık anahtarla yazıldı: zincir İA ile doğrulanır.
    oturumu_ac_test()
    assert denetim_izi.zinciri_dogrula() == []


def test_ertelenen_elle_kilit_uygulaninca_hesabin_satiridir() -> None:
    with bakim.UZUN_ISLER.is_():
        assert OTURUM.kilitle(neden="elle") == "ertelendi"
        assert AuditTrail.objects.count() == 0
    OTURUM.degerlendir()  # iş bitti: ilk istekte bekleyen kilit
    satir = son_satir()
    assert (satir.action, str(satir.account_id)) == ("KILIT", TEST_HESAP_ID)


def test_kapanis_kilidi_sistemin_satiridir() -> None:
    """Pencerenin çarpısı, kurucunun kapatma olayı ve SIGTERM backend'e kaynağını iletmez
    (masaüstünde tek `request_quit` yolu; pywebview `closing` olayı nedeni taşımaz):
    kapanış kilidi `SISTEM`'in satırıdır (`apps.okul.oturum` "KİLİDİN İZİ")."""
    assert kapanista_kilitle() is True
    satir = son_satir()
    assert (satir.action, satir.actor) == ("KILIT", "SISTEM")


@pytest.fixture
def cikis_kancasi() -> Any:
    """Masaüstünün çıkış kancası yerine sayaç (kapanış kilidini test kendisi çağırır)."""
    masaustu_kanca._reset_for_tests()
    cagrilar: list[str] = []
    masaustu_kanca.kaydet(cikis=lambda: cagrilar.append("cik"))
    yield cagrilar
    masaustu_kanca._reset_for_tests()


def test_arayuzden_cik_kapanis_kilidini_hesabin_satiri_yapar(cikis_kancasi: list[str]) -> None:
    """Arayüzdeki Çık kullanıcının kendi eylemidir ve açık oturumun isteğidir (yazar bağlamı):
    kapanış kilidinin `KILIT` satırı oturumdaki hesabındır."""
    yanit = APIClient().post("/api/v1/app/quit/", {}, format="json")
    assert yanit.status_code == 202 and cikis_kancasi == ["cik"]

    assert kapanista_kilitle() is True

    satir = son_satir()
    assert (satir.action, satir.actor, str(satir.account_id), satir.role) == (
        "KILIT",
        "HESAP",
        TEST_HESAP_ID,
        "yonetici",
    )
    assert satir.object_id == TEST_HESAP_ID
    oturumu_ac_test()
    assert denetim_izi.zinciri_dogrula() == []


def test_cik_istegi_oturuma_baglidir(cikis_kancasi: list[str]) -> None:
    """Çık'ın kaydı onu isteyen oturumundur: arada kilitlenip yeniden açılan oturumun kapanışı
    `SISTEM`'in kalır; kilitliyken istenen Çık hesap kaydı bırakmaz."""
    APIClient().post("/api/v1/app/quit/", {}, format="json")
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"
    assert APIClient().post("/api/v1/app/quit/", {}, format="json").status_code == 202
    oturumu_ac_test()

    assert kapanista_kilitle() is True

    assert (son_satir().action, son_satir().actor) == ("KILIT", "SISTEM")
    assert OTURUM.cikisi_hesap_istedi(None) is False  # oturum kapalı ve yazar yok


def test_kilit_izi_yazilamasa_da_kilit_uygulanir(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="oab_defteri.okul")

    def yazilamadi(_hesap: OturumHesabi, _kim: Yazar) -> None:
        raise denetim_izi.IzYazilamadi("deneme")

    oturum = OturumDurumu(
        kilit_izi=yazilamadi, hesap_kurulu=lambda: True, dosya_kayip=lambda: False
    )
    oturum.ac(
        OturumHesabi(id=TEST_HESAP_ID, tanitici=TEST_TANITICI, rol="yonetici"),
        veri_anahtari=TEST_DEK,
        iz_anahtari=TEST_IA,
    )
    assert oturum.kilitle() == "kilitlendi"
    assert crypto.is_unlocked() is False
    assert "Kilit denetim izine yazılamadı" in caplog.text


def test_servis_ici_kapatma_satir_yazmaz() -> None:
    """Geri yükleme sonrası ve sıfırlamada `kapat`: veritabanı artık o oturumun değildir."""
    app_password.lock()
    assert AuditTrail.objects.count() == 0


def test_kendi_parolasini_degistirme_parola_satiridir() -> None:
    app_password.change_password(
        hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
    )
    satir = son_satir()
    assert (satir.action, satir.object_id, satir.changed_fields) == (
        "PAROLA",
        TEST_HESAP_ID,
        ["password_changed_at"],
    )
    assert denetim_izi.kaydi_dogrula(Account, TEST_HESAP_ID) is True


def test_parola_dosyaya_yazilamazsa_satir_ve_iz_geri_alinir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def yazilamadi(_data: dict[str, Any]) -> None:
        raise OSError("disk dolu")

    monkeypatch.setattr(app_password, "_write_structural", yazilamadi)
    with pytest.raises(OSError):
        app_password.change_password(
            hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
        )
    assert AuditTrail.objects.count() == 0


def test_kurtarma_anahtarinin_yenilenmesi_kurtarma_satiridir() -> None:
    app_password.renew_recovery_key(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    satir = son_satir()
    assert (satir.action, satir.model, satir.object_id) == (
        "KURTARMA",
        denetim_izi.KURTARMA_ANAHTARI,
        "2",
    )
    assert satir.values["no"] == [1, 2]
    assert {"salt", "sarmal"} <= set(satir.changed_fields)
    assert not set(satir.values) - {"no", "tarih"}  # tuz ve sarmal değer olarak girmez


def test_hesap_acma_kapama_sifirlama_satirlari() -> None:
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    acma = son_satir()
    assert (acma.action, acma.object_id) == ("HESAP", str(hesap.id))
    assert acma.values["status"] == [None, "PAROLA_YENILENMELI"]
    assert acma.values["role"] == [None, "muhasip"]

    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
    )
    sifirlama = son_satir()
    assert sifirlama.action == "PAROLA"
    assert sifirlama.values["reset_kind"] == ["", "SIFIRLAMA"]

    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    kapama = son_satir()
    assert kapama.action == "HESAP"
    assert kapama.values["status"] == ["PAROLA_YENILENMELI", "KAPALI"]
    assert {str(s.account_id) for s in (acma, sifirlama, kapama)} == {TEST_HESAP_ID}
    assert denetim_izi.zinciri_dogrula() == []
    assert denetim_izi.kaydi_dogrula(Account, hesap.id) is True


def test_veritabani_askisindan_cikarma_hesap_satiridir() -> None:
    hesap = hesap_ac(AccountRole.MUHASIP)
    muhurle(hesap, status=AccountStatus.ASKIDA, suspend_reason=SuspendReason.UYELIK_DUSTU)
    hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    satir = son_satir()
    assert (satir.action, satir.model) == ("HESAP", HESAP)
    assert satir.values["suspend_reason"] == ["UYELIK_DUSTU", ""]


def test_hatali_deneme_askisi_o_an_izlenmez_kaldirilirken_izlenir() -> None:
    """Askı kilitliyken, DEK yokken dosyaya yazılır: o an iz yazılamaz (kilitli kip yalnız
    kişisiz sistem olaylarını yazar). Askı `guvenlik.json`'da ve kilit ekranında görünür;
    program yöneticisinin askıyı kaldırması `guvenlik.sarmal` satırıyla önceki değerleri yazar."""
    hesap = hesap_ac(AccountRole.MUHASIP)
    once = AuditTrail.objects.count()
    for _ in range(app_password.SUSPEND_AFTER_FAILURES - 1):
        with pytest.raises(app_password.WrongPassword):
            app_password.unlock(hesap_id=hesap.id, password="Yanlis-Parola-9")
    with pytest.raises(app_password.AccountSuspended):
        app_password.unlock(hesap_id=hesap.id, password="Yanlis-Parola-9")
    assert AuditTrail.objects.count() == once
    assert app_password.wrap_is_suspended(hesap.id) is True

    hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    satir = son_satir()
    assert (satir.action, satir.model, satir.object_id) == (
        "HESAP",
        denetim_izi.HESAP_SARMALI,
        str(hesap.id),
    )
    assert satir.values == {"hatali": [10, 0], "askida": [True, False]}
    assert str(satir.account_id) == TEST_HESAP_ID


def test_sahipsiz_sarmalin_silinmesi_satir_yazar() -> None:
    hayalet = str(uuid.uuid4())
    app_password.write_account_wrap(
        data_key=TEST_DEK, hesap_id=hayalet, tanitici="hayalet", password=GECICI_PAROLA
    )
    assert hesaplar.remove_orphan_wraps(by_hesap_id=TEST_HESAP_ID, hesap_idler=[hayalet]) == [
        hayalet
    ]
    satir = son_satir()
    assert (satir.action, satir.model, satir.object_id, satir.changed_fields) == (
        "HESAP",
        denetim_izi.HESAP_SARMALI,
        hayalet,
        ["sarmal"],
    )


def _sayac_yaz(hesap_id: object, **alanlar: Any) -> None:
    """Sarmalın hatalı deneme sayacı ve askısı (kilitliyken izsiz yazılan dosya alanları)."""
    veri = durum()
    for kayit in veri["hesaplar"]:
        if kayit["id"] == str(hesap_id):
            kayit.update(alanlar)
    durum_yaz(veri)


def test_parola_sifirlama_ve_kapama_askinin_izini_onceki_degerlerle_yazar() -> None:
    """Askının izi kaldırılırken düşer: parola sıfırlama sarmalı yeniden kurarken, kapama
    sarmalı silerken sayaç ve askının önceki değerlerini `guvenlik.sarmal` satırına yazar
    (askıdan çıkarmadaki gibi); satır veritabanı satırından SONRA, dosyadan önce."""
    hesap = hesap_ac(AccountRole.MUHASIP)
    _sayac_yaz(hesap.id, hatali=10, askida=True)

    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
    )

    parola, sarmal_izi = satirlar()[-2:]
    assert (parola.action, parola.model) == ("PAROLA", HESAP)
    assert (sarmal_izi.action, sarmal_izi.model, sarmal_izi.object_id) == (
        "HESAP",
        denetim_izi.HESAP_SARMALI,
        str(hesap.id),
    )
    assert sarmal_izi.changed_fields == ["hatali", "askida"]
    assert sarmal_izi.values == {"hatali": [10, 0], "askida": [True, False]}
    assert str(sarmal_izi.account_id) == TEST_HESAP_ID
    assert (sarmal(hesap.id)["hatali"], sarmal(hesap.id)["askida"]) == (0, False)

    _sayac_yaz(hesap.id, hatali=3)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)

    kapama, silme = satirlar()[-2:]
    assert (kapama.model, kapama.values["status"]) == (HESAP, ["PAROLA_YENILENMELI", "KAPALI"])
    assert (silme.model, silme.object_id) == (denetim_izi.HESAP_SARMALI, str(hesap.id))
    assert silme.changed_fields == ["sarmal", "hatali"]
    assert silme.values == {"hatali": [3, None]}  # sarmal silindi: sonrası yok
    assert denetim_izi.zinciri_dogrula() == []


def test_sarmal_yazilamazsa_sifirlamanin_sayac_satiri_geri_alinir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """İki depo sırası (önce veritabanı, sonra sarmal) korunur: `PAROLA` satırı kalır, sarmal
    yazılamadıysa sayaç kalkmamıştır, onun satırı da yoktur."""
    hesap = hesap_ac(AccountRole.MUHASIP)
    _sayac_yaz(hesap.id, hatali=4)

    def yazilamadi(**_k: object) -> None:
        raise OSError("disk dolu")

    monkeypatch.setattr(app_password, "write_account_wrap", yazilamadi)
    with pytest.raises(OSError):
        hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
        )

    assert son_satir().action == "PAROLA"
    assert not satirlar(model=denetim_izi.HESAP_SARMALI)
    assert sarmal(hesap.id)["hatali"] == 4


def test_kapali_hesap_sarmalinin_temizligi_kilit_acilisinda_sistem_satiri_yazar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """İki depo kuralı 3: kapamanın dosya adımı yarıda kalırsa kilit açılışındaki temizlik
    sarmalı siler; silme `SISTEM`'in `guvenlik.sarmal` satırıdır (programın düzeltmesi), kilit
    açılışının işleminin SONUNDA, dosyadan önce. Ana dosya yazılamazsa yalnız bu satırlar geri
    alınır, giriş sürer; sonraki açılış yineler."""
    hesap = hesap_ac(AccountRole.MUHASIP)
    _sayac_yaz(hesap.id, hatali=2)

    def yarida(_: set[str]) -> None:
        raise OSError("dosya kilitli")

    with monkeypatch.context() as yama:
        yama.setattr(app_password, "remove_account_wraps", yarida)
        with pytest.raises(OSError):
            hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    assert not satirlar(model=denetim_izi.HESAP_SARMALI)  # sarmal silinmedi: satırı da yok
    OTURUM.kilitle(neden="elle")

    with monkeypatch.context() as yama:  # temizliğin ana dosya yazımı da düşer
        yama.setattr(app_password, "_remove_wraps", yarida)
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert OTURUM.hesap() is not None  # giriş sürer
    assert son_satir().action == "GIRIS"
    assert str(hesap.id) in [h["id"] for h in durum()["hesaplar"]]

    OTURUM.kilitle(neden="elle")
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    giris, temizlik = satirlar()[-2:]
    assert giris.action == "GIRIS"
    assert (temizlik.action, temizlik.actor, temizlik.account_id) == ("HESAP", "SISTEM", None)
    assert (temizlik.model, temizlik.object_id) == (denetim_izi.HESAP_SARMALI, str(hesap.id))
    assert temizlik.changed_fields == ["sarmal", "hatali"]
    assert temizlik.values == {"hatali": [2, None]}
    assert str(hesap.id) not in [h["id"] for h in durum()["hesaplar"]]
    assert denetim_izi.zinciri_dogrula() == []


def test_geri_yukleme_karsilastirmasinin_duzeltmesi_sistemin_satiridir() -> None:
    hesap = hesap_ac(AccountRole.MUHASIP)
    muhurle(hesap, status=AccountStatus.ACIK)
    app_password.remove_account_wraps({str(hesap.id)})
    hesaplar.reconcile_two_stores()
    satir = son_satir()
    assert (satir.action, satir.actor, satir.object_id) == ("HESAP", "SISTEM", str(hesap.id))
    assert satir.values["status"] == ["ACIK", "PAROLA_YENILENMELI"]


def test_kurulumun_tamamlanmasi_durum_satiridir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(setup_service, "missing_setup_steps", lambda **_k: [])
    setup_service.mark_setup_completed()
    satir = son_satir()
    assert (satir.action, satir.values["setup_completed"]) == ("DURUM", [False, True])


# ============================================================ KVKK: kaydın özeti (R1)


def _iz_metni() -> str:
    """`okul_audittrail`'in BÜTÜN sütunları, ham SQL ile (ORM dönüşümü yok)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM okul_audittrail ORDER BY seq")
        return json.dumps(
            [list(map(str, satir)) for satir in cursor.fetchall()], ensure_ascii=False
        )


def test_hesap_sahibinin_uydurma_adi_hicbir_iz_sutununda_gecmez() -> None:
    """Tasarım §4.6.2 kural 6'nın hesap ayağı: ad-soyad ne açık ne şifreli olarak iz satırına girer."""
    ad = "Zeynepnur Uydurmaoğlu"
    hesap = hesap_ac(AccountRole.MUHASIP, ad=ad)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
    )
    muhurle(Account.objects.get(pk=hesap.id), status=AccountStatus.ACIK)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    app_password.change_password(
        hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
    )
    OTURUM.kilitle()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA)
    with connection.cursor() as cursor:
        cursor.execute("SELECT display_name FROM okul_account WHERE id = %s", [hesap.id.hex])
        token = str(cursor.fetchone()[0])

    metin = _iz_metni()
    assert AuditTrail.objects.count() >= 6
    for parca in (ad, "Zeynepnur", "Uydurmaoğlu", ad.casefold(), TEST_HESAP_ADI, token):
        assert parca not in metin
    assert "display_name" in metin  # şifreli alanın değiştiği yalnız ADIYLA görünür


# ============================================================ yazıcının retleri (programlama hataları)


@pytest.mark.parametrize(
    ("eylem", "etiket", "alanlar", "parca"),
    [
        ("SIL", "", ["seal"], "Bilinmeyen iz satırı türü"),
        ("KILIT", "GIZLI", ["seal"], "etiketi"),
        ("KILIT", "", [1], "alan adları"),
    ],
)
def test_kume_disi_tur_etiket_ve_alan_adi_yazilmaz(
    eylem: str, etiket: str, alanlar: list[Any], parca: str
) -> None:
    with transaction.atomic(), pytest.raises(denetim_izi.IzYazilamadi, match=parca):
        denetim_izi.olay(
            eylem, model=HESAP, object_id=TEST_HESAP_ID, changed_fields=alanlar, label=etiket
        )
    assert AuditTrail.objects.count() == 0


def test_bilinmeyen_nesnenin_degeri_yazilamaz() -> None:
    with transaction.atomic(), pytest.raises(denetim_izi.IzYazilamadi):
        denetim_izi.olay(AuditAction.HESAP, model="yok.Model", object_id="1", values={"no": [1, 2]})
    with transaction.atomic(), pytest.raises(denetim_izi.IzYazilamadi, match="çiftidir"):
        denetim_izi.olay(
            AuditAction.KURTARMA,
            model=denetim_izi.KURTARMA_ANAHTARI,
            object_id="1",
            values={"no": [1]},
        )


def test_iz_anahtari_cozulemezse_okunamadi_sayilir() -> None:
    with connection.cursor() as cursor:
        cursor.execute("UPDATE okul_auditkey SET key = 'bozuk-token'")
    with pytest.raises(denetim_izi.IzAnahtariOkunamadi):
        denetim_izi.anahtari_coz(TEST_DEK)
    with pytest.raises(denetim_izi.IzYazilamadi):
        olay_yaz()


def test_kilitliyken_icerik_maci_hesaplanmaz() -> None:
    app_password.lock()
    with pytest.raises(crypto.KeyMissingError):
        denetim_izi.kayit_mac_hesapla(SchoolConfig, 1)


def test_kaydi_silinen_ya_da_anahtari_bulunamayan_izin_dogrulamasi_tutmaz() -> None:
    setup_service.set_idle_lock_minutes(dakika=15)
    satir = son_satir()
    tetikleyicisiz("UPDATE okul_audittrail SET key_ref = 'x' WHERE seq = %s", [satir.seq])
    assert denetim_izi.kaydi_dogrula(SchoolConfig, 1) is False
    assert denetim_izi.zinciri_dogrula() == [
        denetim_izi.ZincirBulgusu(satir.seq, denetim_izi.ANAHTAR_YOK)
    ]


def test_kaydi_silinmis_kaydin_dogrulamasi_tutmaz() -> None:
    setup_service.set_idle_lock_minutes(dakika=15)
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM okul_schoolconfig")
    assert denetim_izi.kaydi_dogrula(SchoolConfig, 1) is False


def test_kayit_kimligi_tek_metne_iner() -> None:
    """UUID tiresiz onaltılık ya da nesne olarak verilse de iz satırının kimliği tirelidir."""
    hesap = hesap_ac(AccountRole.MUHASIP)
    assert son_satir().object_id == str(hesap.id)
    assert denetim_izi.kimlik_metni(Account, hesap.id.hex) == str(hesap.id)
    assert denetim_izi.kimlik_metni(SchoolConfig, "1") == "1"
    assert denetim_izi.kaydi_dogrula(Account, hesap.id.hex) is True


def _hayalet_sarmal() -> str:
    hayalet = str(uuid.uuid4())
    app_password.write_account_wrap(
        data_key=TEST_DEK, hesap_id=hayalet, tanitici="hayalet", password=GECICI_PAROLA
    )
    return hayalet


def test_sahipsiz_sarmal_ana_dosyadan_silinemezse_iz_geri_alinir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hayalet = _hayalet_sarmal()

    def yazilamadi(_idler: set[str]) -> None:
        raise OSError("dosya kilitli")

    monkeypatch.setattr(app_password, "remove_account_wraps", yazilamadi)
    with pytest.raises(OSError):
        hesaplar.remove_orphan_wraps(by_hesap_id=TEST_HESAP_ID, hesap_idler=[hayalet])
    assert AuditTrail.objects.count() == 0
    assert hayalet in app_password.wrap_ids()


def test_sahipsiz_sarmal_yalniz_arsivde_kalirsa_iz_kalir(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Ana dosyadan silinmiş sarmal artık kilit açmaz: iz doğrudur, arşiv uyarısı günlüğe."""
    caplog.set_level(logging.WARNING, logger="oab_defteri.guvenlik")
    hayalet = _hayalet_sarmal()

    def arsivde_kaldi(idler: set[str]) -> None:
        durum = app_password.read_state()
        assert durum is not None
        durum["hesaplar"] = [h for h in durum["hesaplar"] if h["id"] not in idler]
        app_password._write_state(durum)
        raise OSError("arşiv kilitli")

    monkeypatch.setattr(app_password, "remove_account_wraps", arsivde_kaldi)
    assert hesaplar.remove_orphan_wraps(by_hesap_id=TEST_HESAP_ID, hesap_idler=[hayalet]) == [
        hayalet
    ]
    assert son_satir().object_id == hayalet
    assert "arşiv kopyaları" in caplog.text
