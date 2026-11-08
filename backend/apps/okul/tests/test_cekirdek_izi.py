"""Okul çekirdeğinin yazma servisleri denetim izinde (TK16; tasarım §4.6.2; plan F1b-1 alt commit c).

`denetim_izi.degisiklik` türü modelden seçer: yeni kayıt `OLUSTUR`, veri alanı `GUNCELLE`,
durum alanı (`IZ_DURUM_ALANLARI`: ayrılış, aktiflik, havuz, yumuşak silme, koşu durumu)
`DURUM`; ikisi birden değiştiyse iki satır ("her durum geçişi ayrı satırdır", §4.6.2 kural
3). Toplu yazım kayıt başına satır yazar; iz yazılamazsa veri de yazılmaz. Bütün testlerin
ortak değişmezi `butun_kayitlar_dogrulanir`'dır: izi olan her kaydın bugünkü içerik MAC'i
son iz satırını tutar (izsiz bir güncelleme MAC'i bozar ve burada görünür).

Varsayılan ortam kök `conftest.py`'dedir (oturum program yöneticisiyle açık); modül `bos_zincir`
işaretlidir: hesabın iz satırı yazılmaz, zincir boş başlar (yazıcının satırları sırayla sayılır).
Kişi kaydı örnekleri personeldir (öğrenci sicili ve şube kataloğu F1b 5. adımda söküldü; tasarım
§5.1 ALMA). Kişi adları UYDURMADIR.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from django.apps import apps as django_apps
from django.core.management import call_command
from django.db import transaction

from apps.okul import denetim_izi, masaustu_kanca, oturum
from apps.okul.excel_ortak import ParserError
from apps.okul.models import (
    Account,
    AuditTrail,
    Holiday,
    ImportRun,
    ImportStatus,
    MemberKind,
    Personnel,
    SchoolTerm,
    SchoolYear,
)
from apps.okul.services import app_password, dis_yedek, persons
from apps.okul.services import calendar as calendar_service
from apps.okul.services import imports as import_service
from apps.okul.services import school_year as school_year_service
from apps.okul.services import terms as term_service
from apps.okul.tests.hesap_ortak import YENI_PAROLA
from conftest import TEST_HESAP_ID, TEST_KURTARMA_ANAHTARI

pytestmark = [pytest.mark.django_db, pytest.mark.bos_zincir]

PERSONEL_BASLIGI = "Adı Soyadı\tGörevi"


def satirlar(**suz: Any) -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(**suz).order_by("seq"))


def son_seq() -> int:
    bas = denetim_izi.zincir_basi()
    return 0 if bas is None else bas[0]


def yeni_satirlar(bas: int) -> list[AuditTrail]:
    return satirlar(seq__gt=bas)


def butun_kayitlar_dogrulanir() -> None:
    """İzi olan her kaydın içerik MAC'i son iz satırını tutar; zincir bütündür."""
    assert denetim_izi.zinciri_dogrula() == []
    izli = set(
        AuditTrail.objects.exclude(record_mac="").values_list("model", "object_id").distinct()
    )
    for etiket, kimlik in izli:
        model = django_apps.get_model(etiket)
        if model._base_manager.filter(pk=kimlik).exists():
            assert denetim_izi.kaydi_dogrula(model, kimlik) is True, (etiket, kimlik)


def personel(**alanlar: Any) -> Personnel:
    varsayilan: dict[str, Any] = {"first_name": "Uydurcan", "last_name": "Örnekoğlu"}
    return persons.create_personnel(**{**varsayilan, **alanlar})


def yil(ad: str = "2026-2027", *, aktif: bool = True, kayma: int = 0) -> SchoolYear:
    return school_year_service.create_school_year(
        name=ad,
        start_date=date(2026 + kayma, 9, 7),
        end_date=date(2027 + kayma, 6, 25),
        activate=aktif,
    )


# ============================================================ türün seçimi (degisiklik)


def test_yeni_kayit_olustur_satiridir_degerler_izin_listesinden() -> None:
    gun = calendar_service.create_holiday(
        name="Uydurma ara tatil",
        start_date=date(2026, 11, 9),
        end_date=date(2026, 11, 13),
        kind="SCHOOL_BREAK",
    )
    (satir,) = satirlar()
    assert (satir.action, satir.model, satir.object_id) == ("OLUSTUR", "okul.Holiday", str(gun.pk))
    assert "name" in satir.changed_fields  # ad yalnız ADIYLA
    assert satir.values == {
        "start_date": [None, "2026-11-09"],
        "end_date": [None, "2026-11-13"],
        "kind": [None, "SCHOOL_BREAK"],
        "is_estimated": [None, False],
        "deleted_at": [None, None],
    }
    assert satir.record_mac == denetim_izi.kayit_mac_hesapla(Holiday, gun.pk)


def test_yalniz_veri_alani_degisirse_tek_guncelle_satiri() -> None:
    kayit = personel()
    bas = son_seq()
    persons.update_personnel(kayit, member_kind=MemberKind.DIGER)
    (satir,) = yeni_satirlar(bas)
    assert satir.action == "GUNCELLE"
    assert satir.changed_fields == ["updated_at", "member_kind"]
    assert satir.values == {}  # KVKK silme kümesi: değer yok


def test_yalniz_durum_alani_degisirse_tek_durum_satiri() -> None:
    kayit = personel()
    bas = son_seq()
    persons.leave_personnel(kayit)
    (satir,) = yeni_satirlar(bas)
    assert satir.action == "DURUM"
    assert satir.changed_fields == ["updated_at", "is_active", "left_at"]


def test_veri_ve_durum_birlikte_degisirse_iki_satir_ayni_icerik_maci() -> None:
    """§4.6.2 kural 3: durum geçişi ayrı satırdır; iki satır aynı yazımın özetidir."""
    kayit = personel()
    onceki = denetim_izi.anlik(kayit)
    bas = son_seq()
    with transaction.atomic():
        Personnel.objects.filter(pk=kayit.pk).update(
            member_kind=MemberKind.DIGER, is_active=False, left_at=date(2026, 11, 1)
        )
        denetim_izi.degisiklik(kayit, onceki=onceki)
    guncelle, durum = yeni_satirlar(bas)
    assert (guncelle.action, durum.action) == ("GUNCELLE", "DURUM")
    assert guncelle.changed_fields == ["member_kind"]
    assert durum.changed_fields == ["is_active", "left_at"]
    assert (
        guncelle.record_mac
        == durum.record_mac
        == denetim_izi.kayit_mac_hesapla(Personnel, kayit.pk)
    )


def test_yalniz_guncellenme_ani_degisirse_guncelle_satiri() -> None:
    kayit = yil()
    onceki = denetim_izi.anlik(kayit)
    bas = son_seq()
    with transaction.atomic():
        kayit.save(update_fields=["updated_at"])
        denetim_izi.degisiklik(kayit, onceki=onceki)
    (satir,) = yeni_satirlar(bas)
    assert (satir.action, satir.changed_fields) == ("GUNCELLE", ["updated_at"])


def test_durum_alanlarini_tanimlamayan_model_degisiklikle_izlenmez() -> None:
    hesap = Account.objects.get(pk=TEST_HESAP_ID)
    with transaction.atomic(), pytest.raises(denetim_izi.IzYazilamadi, match="IZ_DURUM_ALANLARI"):
        denetim_izi.degisiklik(hesap, onceki=denetim_izi.anlik(hesap))


# ============================================================ servisler


def test_aktiflestirme_kayit_basina_durum_satiri_yazar() -> None:
    """Öteki aktif yılı kapatan toplu güncelleme de kayıt başına satırdır (önce/sonra)."""
    birinci = yil()
    ikinci = yil("2027-2028", aktif=False, kayma=1)
    bas = son_seq()
    school_year_service.activate_school_year(ikinci)
    kapanan, acilan = yeni_satirlar(bas)
    assert (kapanan.action, kapanan.object_id) == ("DURUM", str(birinci.pk))
    assert kapanan.values == {"is_active": [True, False]}
    assert (acilan.action, acilan.object_id) == ("DURUM", str(ikinci.pk))
    assert acilan.values == {"is_active": [False, True]}
    butun_kayitlar_dogrulanir()


def test_donemler_olusur_degismeyen_yazilmaz_degisen_guncellenir() -> None:
    kayit = yil()
    bas = son_seq()
    term_service.configure_terms(kayit, first_end=date(2027, 1, 22), second_start=date(2027, 2, 8))
    assert [s.action for s in yeni_satirlar(bas)] == ["OLUSTUR", "OLUSTUR"]
    bas = son_seq()
    term_service.configure_terms(kayit, first_end=date(2027, 1, 22), second_start=date(2027, 2, 8))
    assert yeni_satirlar(bas) == []  # kayıt değişmedi: yazım ve satır yok
    term_service.configure_terms(kayit, first_end=date(2027, 1, 15), second_start=date(2027, 2, 8))
    (satir,) = yeni_satirlar(bas)
    assert satir.action == "GUNCELLE"
    assert satir.object_id == str(SchoolTerm.objects.get(school_year=kayit, sequence=1).pk)
    assert satir.values == {"end_date": ["2027-01-22", "2027-01-15"]}
    butun_kayitlar_dogrulanir()


def test_yumusak_silme_deleted_at_li_durum_satiridir() -> None:
    gun = calendar_service.create_holiday(
        name="Uydurma idari izin",
        start_date=date(2026, 11, 20),
        end_date=date(2026, 11, 20),
        kind="OTHER",
    )
    bas = son_seq()
    calendar_service.delete_holiday(gun)
    (satir,) = yeni_satirlar(bas)
    assert (satir.action, satir.model) == ("DURUM", "okul.Holiday")
    assert satir.changed_fields == ["updated_at", "deleted_at"]
    assert satir.values["deleted_at"][0] is None
    assert satir.values["deleted_at"][1].endswith("Z")  # UTC
    assert denetim_izi.kaydi_dogrula(Holiday, gun.pk) is True


def test_tohumlama_eklenen_her_kayit_icin_olustur_yazar() -> None:
    sonuc = calendar_service.seed_holidays(2026)
    assert len(satirlar(model="okul.Holiday", action="OLUSTUR")) == sonuc.created
    bas = son_seq()
    assert calendar_service.seed_holidays(2026).created == 0
    assert yeni_satirlar(bas) == []  # fikirdeş: yazım yok, satır yok


def test_havuz_giris_cikis_ve_karar_kisi_basina_durumdur() -> None:
    birinci = personel()
    ikinci = personel(first_name="Uydurmay")
    ucuncu = personel(first_name="Uydurnur", last_name="Örnekkaya")
    for kisi in (birinci, ikinci, ucuncu):
        persons.add_to_leave_pool(kisi, run=None)
    bas = son_seq()
    persons.resolve_leave_pool(
        personnel=persons.PoolDecision(leave=(birinci.pk,), keep=(ikinci.pk, ucuncu.pk)),
    )
    yeni = yeni_satirlar(bas)
    assert [(s.action, s.model, s.object_id) for s in yeni] == [
        ("DURUM", "okul.Personnel", str(birinci.pk)),
        ("DURUM", "okul.Personnel", str(ikinci.pk)),
        ("DURUM", "okul.Personnel", str(ucuncu.pk)),
    ]
    assert yeni[0].changed_fields == [
        "updated_at",
        "is_active",
        "left_at",
        "leave_candidate_since",
    ]
    butun_kayitlar_dogrulanir()


def test_degismeyen_guncelleme_yazmaz_satir_da_yazmaz() -> None:
    kayit = personel()
    bas = son_seq()
    persons.update_personnel(kayit, member_kind=MemberKind.OGRETMEN, first_name="Uydurcan")
    assert yeni_satirlar(bas) == []


# ============================================================ içe aktarma


def _metin(*satirlar_: str) -> str:
    return "\n".join([PERSONEL_BASLIGI, *satirlar_])


def test_aktarim_kayit_basina_satir_yazar_ve_kosuyu_izler() -> None:
    import_service.commit_personnel_text(
        text=_metin("UYDURCAN ÖRNEKOĞLU\tÖğretmen", "UYDURMAY ÖRNEKSOY\tMemur")
    )
    kosu = ImportRun.objects.get(status=ImportStatus.COMPLETED)
    kosu_satirlari = satirlar(model="okul.ImportRun")
    assert [s.action for s in kosu_satirlari] == ["OLUSTUR", "DURUM"]
    assert kosu_satirlari[1].values["status"] == ["RUNNING", "COMPLETED"]
    assert "report" in kosu_satirlari[1].changed_fields
    assert "report" not in kosu_satirlari[1].values  # rapor yalnız adıyla
    assert len(satirlar(model="okul.Personnel", action="OLUSTUR")) == 2
    assert kosu_satirlari[0].object_id == str(kosu.pk)
    butun_kayitlar_dogrulanir()


def test_tur_degisimi_ve_havuzdan_cikis_iki_satirdir_yeniden_aktiflesme_durumdur() -> None:
    """Listede görülmeyen kişi havuza girer; yeni görevle dönünce tür `GUNCELLE`, havuz `DURUM`."""
    import_service.commit_personnel_text(
        text=_metin("UYDURCAN ÖRNEKOĞLU\tÖğretmen", "UYDURMAY ÖRNEKSOY\tÖğretmen")
    )
    import_service.commit_personnel_text(text=_metin("UYDURMAY ÖRNEKSOY\tÖğretmen"))
    tasinan = next(p for p in Personnel.objects.all() if p.first_name == "UYDURCAN")
    assert tasinan.leave_candidate_since is not None
    bas = son_seq()
    import_service.commit_personnel_text(
        text=_metin("UYDURCAN ÖRNEKOĞLU\tMemur", "UYDURMAY ÖRNEKSOY\tÖğretmen")
    )
    kisi_satirlari = [
        s
        for s in yeni_satirlar(bas)
        if s.model == "okul.Personnel" and s.object_id == str(tasinan.pk)
    ]
    assert [(s.action, s.changed_fields) for s in kisi_satirlari] == [
        ("GUNCELLE", ["updated_at", "member_kind"]),
        ("DURUM", ["leave_candidate_since", "leave_candidate_run"]),
    ]
    # Ayrılmış kişi listede yeniden görülürse yeniden aktifleşir: durum geçişi.
    persons.leave_personnel(Personnel.objects.get(pk=tasinan.pk))
    bas = son_seq()
    import_service.commit_personnel_text(
        text=_metin("UYDURCAN ÖRNEKOĞLU\tMemur", "UYDURMAY ÖRNEKSOY\tÖğretmen")
    )
    (donus,) = [
        s
        for s in yeni_satirlar(bas)
        if s.model == "okul.Personnel" and s.object_id == str(tasinan.pk)
    ]
    assert donus.action == "DURUM" and {"is_active", "left_at"} <= set(donus.changed_fields)
    butun_kayitlar_dogrulanir()


def test_onizlemenin_kayit_satirlari_geri_sarilir_kalici_iz_previewed_kosusudur() -> None:
    import_service.preview_personnel_text(text=_metin("UYDURCAN ÖRNEKOĞLU\tÖğretmen"))
    (satir,) = satirlar()
    assert (satir.action, satir.model) == ("OLUSTUR", "okul.ImportRun")
    assert satir.values["status"] == [None, "PREVIEWED"]
    assert not Personnel.objects.exists()
    butun_kayitlar_dogrulanir()


def test_ayristirilamayan_dosyanin_failed_kosusu_izlidir() -> None:
    with pytest.raises(ParserError):
        import_service.commit_personnel_file(file_bytes=b"bozuk", file_name="uydurma.xlsx")
    (satir,) = satirlar()
    assert (satir.action, satir.model) == ("OLUSTUR", "okul.ImportRun")
    assert satir.values["status"] == [None, "FAILED"]
    assert "file_name" in satir.changed_fields and "file_name" not in satir.values


def test_ayni_dosyanin_yeniden_uygulanmasi_kosuyu_yeniden_acar() -> None:
    metin = _metin("UYDURCAN ÖRNEKOĞLU\tÖğretmen")
    import_service.commit_personnel_text(text=metin)
    bas = son_seq()
    import_service.commit_personnel_text(text=metin)
    kosu = [s for s in yeni_satirlar(bas) if s.model == "okul.ImportRun"]
    assert [s.action for s in kosu] == ["DURUM", "DURUM"]
    assert kosu[0].values["status"] == ["COMPLETED", "RUNNING"]
    assert not [s for s in yeni_satirlar(bas) if s.model == "okul.Personnel"]  # değişmedi
    butun_kayitlar_dogrulanir()


# ============================================================ iz yazılamazsa veri de yazılmaz


def test_iz_yazilamazsa_kayit_ve_aktarim_geri_alinir(monkeypatch: pytest.MonkeyPatch) -> None:
    def yazilamadi(*_a: object, **_k: object) -> None:
        raise denetim_izi.IzYazilamadi("deneme")

    monkeypatch.setattr(denetim_izi, "degisiklik", yazilamadi)
    with pytest.raises(denetim_izi.IzYazilamadi):
        personel()
    with pytest.raises(denetim_izi.IzYazilamadi):
        import_service.commit_personnel_text(text=_metin("UYDURCAN ÖRNEKOĞLU\tÖğretmen"))
    with pytest.raises(denetim_izi.IzYazilamadi):
        calendar_service.seed_holidays(2026)
    assert not Personnel.objects.exists()
    assert not ImportRun.objects.exists()
    assert not Holiday.objects.exists()
    assert AuditTrail.objects.count() == 0


def test_kilitliyken_cekirdek_yazilmaz() -> None:
    """DEK yokken iş verisi yazılmaz (tasarım §4.1): yazıcı reddeder, kayıt geri alınır."""
    app_password.lock()
    with pytest.raises(denetim_izi.IzAnahtariBellekteDegil):
        yil()
    assert not SchoolYear.objects.exists()


# ============================================================ dosyadaki yazımlar


def test_dis_yedek_suresi_guncelle_satiridir() -> None:
    dis_yedek.hatirlatma_suresini_ayarla(14)
    (satir,) = satirlar()
    assert (satir.action, satir.model, satir.object_id) == (
        "GUNCELLE",
        denetim_izi.DIS_YEDEK_AYARI,
        "hatirlatma_gun",
    )
    assert satir.values == {"hatirlatma_gun": [30, 14]}
    assert str(satir.account_id) == TEST_HESAP_ID


def test_dis_yedek_dosyasi_yazilamazsa_satir_geri_alinir(monkeypatch: pytest.MonkeyPatch) -> None:
    def yazilamadi(_veri: dict[str, Any]) -> None:
        raise OSError("disk dolu")

    monkeypatch.setattr(dis_yedek, "_yaz", yazilamadi)
    with pytest.raises(OSError):
        dis_yedek.hatirlatma_suresini_ayarla(14)
    assert AuditTrail.objects.count() == 0


def test_kurtarma_anahtarinin_dogrulanmasi_kurtarma_satiridir() -> None:
    app_password.confirm_recovery_key(TEST_KURTARMA_ANAHTARI)
    (satir,) = satirlar()
    assert (satir.action, satir.model, satir.object_id) == (
        "KURTARMA",
        denetim_izi.KURTARMA_ANAHTARI,
        "1",
    )
    assert satir.changed_fields == [app_password.RECOVERY_CONFIRMED_FIELD]
    assert satir.values == {}  # damga yalnız adıyla


def test_kurtarma_damgasi_dosyaya_yazilamazsa_satir_geri_alinir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def yazilamadi(_veri: dict[str, Any]) -> None:
        raise OSError("disk dolu")

    monkeypatch.setattr(app_password, "_write_state", yazilamadi)
    with pytest.raises(OSError):
        app_password.confirm_recovery_key(TEST_KURTARMA_ANAHTARI)
    assert AuditTrail.objects.count() == 0
    assert not app_password.recovery_key_confirmed()


# ============================================================ gün işi


def test_gun_isi_sistem_yazariyla_kosar_yazimi_sistemin_satiridir() -> None:
    """Plan F1b-1: gün işi `SISTEM`'i açıkça verir. `od-gunluk` iş parçacığının bağlamı boş
    başlar (burada `yazar_olarak(None)` taklit eder); kayıt kanalı işi `SISTEM` ile koşturur."""
    gorulen: list[object] = []

    def tohumla() -> bool:
        gorulen.append(oturum.yazar())
        return calendar_service.seed_holidays(2026).created > 0

    masaustu_kanca.gunluk_is_kaydet("deneme-tohum", tohumla)
    try:
        (kayit,) = [is_ for is_ in masaustu_kanca.gunluk_isler() if is_.ad == "deneme-tohum"]
        with oturum.yazar_olarak(None):
            assert kayit.calistir() is True
    finally:
        masaustu_kanca._reset_for_tests()
    assert gorulen == [oturum.SISTEM]
    yeni = satirlar()
    assert yeni and all(s.actor == "SISTEM" and s.account_id is None for s in yeni)


# ============================================================ konsol komutu


def test_konsol_komutu_yazarini_sistem_olarak_verir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Konsolda istek yoktur: komut yazarı açıkça `SISTEM`'dir (oturum katmanı belge dizesi)."""
    gorulen: list[object] = []
    gercek = app_password.status

    def durum() -> dict[str, Any]:
        gorulen.append(oturum.yazar())
        return gercek()

    monkeypatch.setattr(app_password, "status", durum)
    with oturum.yazar_olarak(None):
        call_command("app_password", "status")
    assert gorulen == [oturum.SISTEM]


@pytest.mark.hesapsiz
def test_konsoldan_ilk_hesap_satirlari_o_hesabindir(parolasiz: Path) -> None:
    """Plan F1b-1: ilk hesabın satırları o hesabındır (konsol bağlamı `SISTEM` olsa da)."""
    with oturum.yazar_olarak(None):
        call_command(
            "app_password",
            "enable",
            "--tanitici",
            "yonetici",
            "--ad",
            "Uydurma Yönetici",
            "--password",
            YENI_PAROLA,
        )
    hesap = Account.objects.get(login_name="yonetici")
    yeni = satirlar()
    assert {s.action for s in yeni} == {"HESAP", "KURTARMA", "OLUSTUR"}
    assert all(s.actor == "HESAP" and s.account_id == hesap.pk for s in yeni)
    assert json.loads(app_password.state_path().read_text(encoding="utf-8"))["hesaplar"]


# ============================================================ izli modeller ve değerler


def test_kisi_modelleri_deger_listesi_bostur() -> None:
    """KVKK silme kümesi (tasarım §4.6.2): `Personnel` satırları değer taşımaz."""
    assert Personnel.IZ_DEGER_ALANLARI == ()
