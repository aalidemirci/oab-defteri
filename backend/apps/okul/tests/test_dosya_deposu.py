"""Dosya deposu: `Attachment`, depo servisi, ayarlar (tasarım TK22, §4.4.7, §5.2.8; plan F1b-3).

Bölümler: model (kısıtlar, silinmezlik, boş olabilirlik) · denetim izi (satır, alan sınıfları,
sızıntı) · yazım (diskteki kap, sıra, yetim, kipler) · red (R9, tür, sınır, sahip, ad) · uzun iş ·
okuma (özet, "dosya yok", erişim günlüğü) · DEK yokken · tek yazar (kaynak taraması) · ayarlar
(bellek işleyicisi, yollar). Saf katmanın testleri `shared/tests/test_dosya_sifreleme.py`'de,
gömülü sunucunun tamponu `desktop/tests/test_server.py`'dedir. Kişi adları ve içerikler UYDURMADIR.
Sahip kümesinin bugünkü tek üyesi üretilen evraktır (`oab.GeneratedDocument`, F1c 9. adım); testler
geçici sahip kaydeder (`sahip` fikstürü).
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import logging
import os
import re
import stat
import sys
from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from desktop import paths as masaustu_yollari
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler
from django.db import IntegrityError, connection, models, transaction
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.utils.module_loading import import_string
from rest_framework.test import APIClient

from apps.okul import denetim_izi, erisim_gunlugu, iz_dogrulama
from apps.okul.models import (
    AccessKind,
    AccessLog,
    Attachment,
    AttachmentSensitivity,
    AuditAction,
    AuditActor,
    AuditTrail,
    DeletionNotAllowed,
    SchoolYear,
)
from apps.okul.oturum import SISTEM, Yazar, sistem_olarak, yazar_olarak
from apps.okul.services import dosya_deposu
from apps.okul.services import school_year as school_year_service
from apps.okul.tests.test_erisim_gunlugu import _kok_yazimlari, _program_kaynaklari
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_ROL, varsayilan_yazar
from shared import bakim, crypto
from shared import dosya_sifreleme as ds
from shared.models import BaseModel

pytestmark = pytest.mark.django_db

PDF = b"%PDF-1.7\nuydurma belge icerigi\n"
JPEG = b"\xff\xd8\xff\xe0uydurma resim"
PNG = b"\x89PNG\r\n\x1a\nuydurma resim"
#: Uydurma kişi adı taşıyan dosya adı (gerçek kişi değildir).
UYDURMA_DOSYA_ADI = "Uydurgül Masalcıoğlu dilekçesi.pdf"
ARANACAK_PARCALAR = ("Uydurgül", "Masalcıoğlu", "dilekçesi", "uydurgül")
ORNEK_AN = datetime(2026, 11, 4, 9, 0, tzinfo=UTC)
HESAP_YAZARI = Yazar(hesap_id=TEST_HESAP_ID, rol=TEST_ROL)


@pytest.fixture
def sahip(monkeypatch: pytest.MonkeyPatch) -> SchoolYear:
    """Geçici sahip kümesi (`SchoolYear`) ve kaydedilmiş bir sahip satırı."""
    monkeypatch.setattr(dosya_deposu, "_SAHIP_ETIKETLERI", set())
    dosya_deposu.sahip_kaydet(SchoolYear)
    return school_year_service.create_school_year(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), activate=True
    )


def _yaz(sahip: models.Model, icerik: bytes = PDF, **alanlar: Any) -> Attachment:
    varsayilan: dict[str, Any] = {
        "original_name": UYDURMA_DOSYA_ADI,
        "sensitivity": AttachmentSensitivity.NORMAL,
        "owner": sahip,
        "yazar": varsayilan_yazar(),
        "kisi_listesi": False,
    }
    return dosya_deposu.yaz(icerik, **{**varsayilan, **alanlar})


def _depodaki_adlar() -> set[str]:
    dizin = dosya_deposu.depo_dizini()
    return {yol.name for yol in dizin.iterdir()} if dizin.exists() else set()


def _ek_izleri() -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(model="okul.Attachment").order_by("seq"))


def _dosya(ek: Attachment) -> Path:
    return dosya_deposu.depo_dizini() / ek.stored_name


def _guncelle(ek: Attachment, **alanlar: Any) -> None:
    """Program dışı yazım taklidi: iz satırı yazılmaz."""
    Attachment.objects.filter(pk=ek.pk).update(**alanlar)


# ============================================================ model


def test_ek_satiri_silinmez() -> None:
    """Altın kural 4, tasarım §5 O1: örnek ve toplu silme reddedilir, yumuşak silme yoktur."""
    assert not issubclass(Attachment, BaseModel)
    assert {"deleted_at", "updated_at"}.isdisjoint(f.name for f in Attachment._meta.get_fields())
    with pytest.raises(DeletionNotAllowed):
        Attachment(stored_name="0" * 32).delete()
    with pytest.raises(DeletionNotAllowed):
        Attachment.objects.all().delete()
    with pytest.raises(DeletionNotAllowed):
        Attachment._base_manager.all().delete()


def test_var_olan_ek_silinemez_ve_temsili_ozgun_adi_tasimaz(sahip: SchoolYear) -> None:
    ek = _yaz(sahip)
    with pytest.raises(DeletionNotAllowed):
        ek.delete()
    with pytest.raises(DeletionNotAllowed):
        Attachment.objects.filter(pk=ek.pk).delete()
    assert Attachment.objects.filter(pk=ek.pk).exists()
    assert str(ek) == f"Ek {ek.stored_name}"


def test_alanlarin_bos_olabilirligi_donmustur() -> None:
    """Plan F1b-3: göçler 6. adımda sıkışır; F1c'de değişmesin diye bugünden kesin."""
    bos_olabilen = {
        alan.name: alan.null
        for alan in Attachment._meta.fields
        if not alan.primary_key and (alan.null or alan.blank)
    }
    assert bos_olabilen == {
        "original_name": False,
        "key_wrap": False,
        "retention_until": True,
        "uploaded_by": True,
        "purged_at": True,
    }


@pytest.mark.parametrize(
    "tur",
    [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ],
    ids=["docx", "xlsx"],
)
def test_uretilen_evrakin_tur_adi_sutuna_sigar(tur: str) -> None:
    """Plan F1b-3: üretilen evrakın türleri F1c'de eklenir; sütun o zaman göç istemesin."""
    uzunluk = Attachment._meta.get_field("mime").max_length
    assert uzunluk is not None and len(tur) <= uzunluk


def test_yukleyen_hesap_korunur() -> None:
    alan = Attachment._meta.get_field("uploaded_by")
    assert alan.remote_field.on_delete is models.PROTECT
    assert alan.remote_field.model.__name__ == "Account"


@pytest.mark.parametrize(
    ("alanlar", "kisit"),
    [
        ({"purged_at": ORNEK_AN}, "ck_attachment_purged_fields"),
        ({"purged_at": ORNEK_AN, "key_wrap": ""}, "ck_attachment_purged_fields"),
        ({"purged_at": ORNEK_AN, "original_name": ""}, "ck_attachment_purged_fields"),
        ({"key_wrap": ""}, "ck_attachment_purged_fields"),
        ({"original_name": ""}, "ck_attachment_purged_fields"),
        ({"sensitivity": "GIZLI"}, "ck_attachment_sensitivity"),
        ({"stored_name": "kisa"}, "ck_attachment_stored_name"),
        ({"sha256": "abc"}, "ck_attachment_sha256"),
        ({"size": 0}, "ck_attachment_size"),
        ({"owner_type": ""}, "ck_attachment_owner"),
        ({"owner_id": ""}, "ck_attachment_owner"),
    ],
    ids=lambda deger: deger if isinstance(deger, str) else "-".join(deger),
)
def test_veritabani_kisitlari(sahip: SchoolYear, alanlar: dict[str, Any], kisit: str) -> None:
    ek = _yaz(sahip)
    with pytest.raises(IntegrityError, match=kisit), transaction.atomic():
        _guncelle(ek, **alanlar)


def test_imhali_satirda_sarmal_ve_ad_bostur(sahip: SchoolYear) -> None:
    """Kısıt anahtar imhasını kabul eder: `purged_at` dolu, sarmal ve ad boş, satır kalır."""
    ek = _yaz(sahip)
    _guncelle(ek, purged_at=ORNEK_AN, key_wrap="", original_name="")
    ek.refresh_from_db()
    assert (ek.key_wrap, ek.original_name, ek.sha256) == ("", "", hashlib.sha256(PDF).hexdigest())


def test_depo_adi_tekildir(sahip: SchoolYear) -> None:
    ilk, ikinci = _yaz(sahip), _yaz(sahip)
    with pytest.raises(IntegrityError, match="stored_name"), transaction.atomic():
        _guncelle(ikinci, stored_name=ilk.stored_name)


# ============================================================ denetim izi


def test_yazim_tek_olustur_satiri_yazar_ve_kayit_dogrulanir(sahip: SchoolYear) -> None:
    ek = _yaz(sahip)
    (satir,) = _ek_izleri()
    assert (satir.action, satir.object_id) == (AuditAction.OLUSTUR, str(ek.pk))
    assert (str(satir.account_id), satir.role) == (TEST_HESAP_ID, TEST_ROL)
    assert set(satir.values) == set(Attachment.IZ_DEGER_ALANLARI)
    assert satir.values["size"] == [None, len(PDF)]
    assert satir.values["owner_type"] == [None, "okul.SchoolYear"]
    assert satir.record_mac != ""
    assert denetim_izi.kaydi_dogrula(Attachment, ek.pk) is True
    assert denetim_izi.zinciri_dogrula() == []


def test_ozet_ve_depo_adi_iz_satirina_deger_olarak_girmez(sahip: SchoolYear) -> None:
    """Plan F1b-3 "Dosya deposu": `sha256` değere girmez; şifreli alan ve sarmal da girmez."""
    assert {"sha256", "stored_name", "key_wrap", "original_name", "uploaded_by"}.isdisjoint(
        Attachment.IZ_DEGER_ALANLARI
    )
    ek = _yaz(sahip)
    (satir,) = _ek_izleri()
    metin = f"{satir.values} {satir.changed_fields}"
    for deger in (ek.sha256, ek.stored_name, ek.key_wrap):
        assert deger not in metin
    assert {"original_name", "key_wrap", "sha256"} <= set(satir.changed_fields)  # yalnız adlar


@pytest.mark.parametrize(
    "alanlar",
    [
        {"stored_name": "f" * 32},
        {"sha256": "0" * 64},
        {"mime": "image/png"},
        {"size": 9},
        {"sensitivity": AttachmentSensitivity.OZEL_NITELIKLI},
        {"retention_until": date(2030, 1, 1)},
        {"owner_type": "okul.Holiday"},
        {"owner_id": "99"},
        {"uploaded_by": None},
        {"uploaded_at": ORNEK_AN},
        {"purged_at": ORNEK_AN, "key_wrap": "", "original_name": ""},
    ],
    ids=lambda alanlar: next(iter(alanlar)),
)
def test_icerik_maci_ozet_alanlarini_kapsar(sahip: SchoolYear, alanlar: dict[str, Any]) -> None:
    ek = _yaz(sahip)
    once = denetim_izi.kayit_mac_hesapla(Attachment, ek.pk)
    _guncelle(ek, **alanlar)
    assert denetim_izi.kayit_mac_hesapla(Attachment, ek.pk) != once
    assert denetim_izi.kaydi_dogrula(Attachment, ek.pk) is False


def test_ozgun_ad_ve_sarmal_icerik_macina_girmez(sahip: SchoolYear) -> None:
    """Tasarım §4.6.2 "imha edilen dosya": imhada boşalan iki alan MAC'i değiştirmez."""
    ek = _yaz(sahip)
    once = denetim_izi.kayit_mac_hesapla(Attachment, ek.pk)
    _guncelle(ek, original_name="Başka Uydurma Ad.pdf", key_wrap="A" * 80)
    assert denetim_izi.kayit_mac_hesapla(Attachment, ek.pk) == once
    assert denetim_izi.kaydi_dogrula(Attachment, ek.pk) is True


def test_imha_durum_gecisidir_bosalan_alanlar_yalniz_adiyla_gorunur(sahip: SchoolYear) -> None:
    """`purged_at` durum alanıdır (§4.6.2 kural 3). İmhanın kendisi F4-F6'dadır; burada izi sınanır."""
    ek = _yaz(sahip)
    with transaction.atomic():
        onceki = denetim_izi.anlik(ek)
        _guncelle(ek, purged_at=ORNEK_AN, key_wrap="", original_name="")
        denetim_izi.degisiklik(ek, onceki=onceki)
    _, veri, durum = _ek_izleri()
    assert (veri.action, set(veri.changed_fields)) == (
        AuditAction.GUNCELLE,
        {"original_name", "key_wrap"},
    )
    assert veri.values == {}
    assert (durum.action, durum.changed_fields) == (AuditAction.DURUM, ["purged_at"])
    assert set(durum.values) == {"purged_at"}


def test_ozgun_ad_ize_gunluge_ve_erisim_gunlugune_sizmaz(
    sahip: SchoolYear, caplog: pytest.LogCaptureFixture
) -> None:
    """R1, tasarım §4.6.2 kural 6: uydurma kişi adlı dosya adı yalnız şifreli sütunda durur."""
    caplog.set_level(logging.DEBUG)
    ek = _yaz(sahip, sensitivity=AttachmentSensitivity.OZEL_NITELIKLI)
    dosya_deposu.oku(ek)
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM okul_audittrail WHERE model = 'okul.Attachment'")
        iz = str(cursor.fetchall())
        cursor.execute("SELECT * FROM okul_accesslog")
        gunluk = str(cursor.fetchall())
        cursor.execute("SELECT original_name FROM okul_attachment")
        (ham,) = cursor.fetchone()
    assert iz and gunluk
    for parca in ARANACAK_PARCALAR:
        for metin in (iz, gunluk, caplog.text, ham):
            assert parca not in metin
    assert ham not in iz  # şifreli token de satıra girmez
    assert Attachment.objects.get(pk=ek.pk).original_name == UYDURMA_DOSYA_ADI


def test_sistem_yazari_hesapsiz_yazar(sahip: SchoolYear) -> None:
    ek = _yaz(sahip, yazar=SISTEM)
    (satir,) = _ek_izleri()
    assert Attachment.objects.get(pk=ek.pk).uploaded_by_id is None
    assert (satir.actor, satir.account_id, satir.role) == (AuditActor.SISTEM, None, "")


def test_iz_satiri_verilen_yazarladir_baglamdaki_degil(sahip: SchoolYear) -> None:
    with sistem_olarak():
        ek = _yaz(sahip, yazar=HESAP_YAZARI)
    (satir,) = _ek_izleri()
    assert str(Attachment.objects.get(pk=ek.pk).uploaded_by_id) == TEST_HESAP_ID
    assert str(satir.account_id) == TEST_HESAP_ID


def test_yazarsiz_yazim_dosya_birakmaz(sahip: SchoolYear) -> None:
    with pytest.raises(denetim_izi.IzYazilamadi):
        _yaz(sahip, yazar=None)
    assert _depodaki_adlar() == set()


# ============================================================ yazım


def test_satir_acik_icerigi_ve_sarmali_tasir(sahip: SchoolYear) -> None:
    ek = Attachment.objects.get(pk=_yaz(sahip).pk)
    assert ek.sha256 == hashlib.sha256(PDF).hexdigest()
    assert (ek.size, ek.mime, ek.sensitivity) == (len(PDF), "application/pdf", "NORMAL")
    assert (ek.owner_type, ek.owner_id) == ("okul.SchoolYear", str(sahip.pk))
    assert (ek.purged_at, ek.retention_until) == (None, None)
    sarmal_anahtari = crypto.file_wrap_key(TEST_DEK)
    anahtar = ds.anahtari_ac(
        ek.key_wrap, sarmal_anahtari=sarmal_anahtari, stored_name=ek.stored_name
    )
    kap = _dosya(ek).read_bytes()
    assert ds.coz(kap, dosya_anahtari=anahtar, stored_name=ek.stored_name) == PDF


def test_diskteki_dosya_uzantisiz_kaptir_acik_icerik_tasimaz(sahip: SchoolYear) -> None:
    ek = _yaz(sahip)
    assert ds.DEPO_ADI_DESENI.fullmatch(ek.stored_name)
    assert _depodaki_adlar() == {ek.stored_name}  # `.tmp` artığı da yok
    kap = _dosya(ek).read_bytes()
    assert kap.startswith(ds.MAGIC) and len(kap) == ds.sifreli_boy(len(PDF))
    assert PDF not in kap and b"uydurma" not in kap


def test_dosya_satirdan_once_yazilir_satir_islem_icindedir(
    sahip: SchoolYear, monkeypatch: pytest.MonkeyPatch
) -> None:
    asil = denetim_izi.degisiklik
    gorulen: list[tuple[bool, bool]] = []

    def casus(ek: Attachment, **alanlar: Any) -> Any:
        gorulen.append((_dosya(ek).is_file(), connection.in_atomic_block))
        return asil(ek, **alanlar)

    monkeypatch.setattr(denetim_izi, "degisiklik", casus)
    _yaz(sahip)
    assert gorulen == [(True, True)]


@pytest.mark.parametrize("dusen", ["satir", "iz"])
def test_islem_duserse_dosya_yetim_kalir_satir_ve_iz_kalmaz(
    sahip: SchoolYear, monkeypatch: pytest.MonkeyPatch, dusen: str
) -> None:
    """Plan F1b-3: "İşlem geri alınırsa dosya yetim kalır, açılış taraması toplar"."""

    def patla(*_: Any, **__: Any) -> Any:
        raise IntegrityError("uydurma veritabanı hatası")

    if dusen == "iz":
        monkeypatch.setattr(denetim_izi, "degisiklik", patla)
    else:
        monkeypatch.setattr(Attachment.objects, "create", patla)
    with pytest.raises(IntegrityError, match="uydurma"):
        _yaz(sahip)
    (ad,) = _depodaki_adlar()
    assert ds.DEPO_ADI_DESENI.fullmatch(ad)  # silinmedi, `.tmp` değil
    assert not Attachment.objects.exists()
    assert _ek_izleri() == []


def test_iz_satiri_yazilamazsa_satir_geri_alinir(
    sahip: SchoolYear, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Satır yazıldıktan sonra iz düşerse satır da geri alınır (yazma kuralı 1)."""
    gorulen: list[int] = []

    def patla(ek: Attachment, **_: Any) -> Any:
        gorulen.append(Attachment.objects.count())
        raise denetim_izi.IzYazilamadi("uydurma iz hatası")

    monkeypatch.setattr(denetim_izi, "degisiklik", patla)
    with pytest.raises(denetim_izi.IzYazilamadi):
        _yaz(sahip)
    assert gorulen == [1]
    assert not Attachment.objects.exists()


def test_dosya_yazilamazsa_satir_yazilmaz(
    sahip: SchoolYear, monkeypatch: pytest.MonkeyPatch
) -> None:
    def patla(*_: Any, **__: Any) -> Any:
        raise OSError("uydurma disk hatası")

    monkeypatch.setattr(ds, "depoya_yaz", patla)
    with pytest.raises(OSError, match="uydurma"):
        _yaz(sahip)
    assert not Attachment.objects.exists()
    assert _ek_izleri() == []


@pytest.mark.django_db(transaction=True)
def test_satir_ve_iz_satiri_tek_immediate_islemdedir(sahip: SchoolYear) -> None:
    with CaptureQueriesContext(connection) as yakalanan:
        _yaz(sahip)
    sorgular = [str(sorgu["sql"]) for sorgu in yakalanan.captured_queries]
    baslangiclar = [i for i, sorgu in enumerate(sorgular) if sorgu.startswith("BEGIN")]
    assert [sorgular[i] for i in baslangiclar] == ["BEGIN IMMEDIATE"]
    bitis = sorgular.index("COMMIT")
    islem = sorgular[baslangiclar[0] : bitis]
    assert any('INSERT INTO "okul_attachment"' in sorgu for sorgu in islem)
    assert any('INSERT INTO "okul_audittrail"' in sorgu for sorgu in islem)
    assert not any("INSERT INTO" in sorgu for sorgu in sorgular[bitis:])


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX dosya kipleri")
def test_dizin_ve_dosya_kipleri_umaska_guvenmez(sahip: SchoolYear) -> None:
    """Tasarım §4.5; plan F1b-3 "Yazıcılar umask'a güvenmez": geniş kipli dizin de daralır."""
    dizin = dosya_deposu.depo_dizini()
    dizin.mkdir(parents=True)
    dizin.chmod(0o755)
    eski_umask = os.umask(0o022)
    try:
        ek = _yaz(sahip)
    finally:
        os.umask(eski_umask)
    assert stat.S_IMODE(dizin.stat().st_mode) == 0o700
    assert stat.S_IMODE(_dosya(ek).stat().st_mode) == 0o600


def test_depo_dizini_yoksa_kurulur(sahip: SchoolYear) -> None:
    assert not dosya_deposu.depo_dizini().exists()
    _yaz(sahip)
    assert dosya_deposu.depo_dizini().is_dir()


# ============================================================ red


def _hicbir_sey_yazilmadi() -> None:
    assert _depodaki_adlar() == set()
    assert not Attachment.objects.exists()
    assert _ek_izleri() == []
    assert bakim.UZUN_ISLER.sayi == 0


def test_veli_adi_tasiyan_belge_depoya_yazilmaz(sahip: SchoolYear) -> None:
    """R9, tasarım §4.4.7, §5.2.8: adlı E07 ve E08 depoya hiç yazılmaz."""
    with pytest.raises(dosya_deposu.KisiListesiSaklanmaz):
        _yaz(sahip, kisi_listesi=True)
    _hicbir_sey_yazilmadi()


def test_kisi_listesi_karari_cagiranindir(sahip: SchoolYear) -> None:
    """R9 varsayılanda açık kalmasın: bayrağı yazmayan çağrı veli adlı belgeyi saklayamaz."""
    parametre = inspect.signature(dosya_deposu.yaz).parameters["kisi_listesi"]
    assert parametre.default is inspect.Parameter.empty
    with pytest.raises(TypeError, match="kisi_listesi"):
        dosya_deposu.yaz(  # type: ignore[call-arg]
            PDF,
            original_name=UYDURMA_DOSYA_ADI,
            sensitivity=AttachmentSensitivity.NORMAL,
            owner=sahip,
            yazar=varsayilan_yazar(),
        )
    _hicbir_sey_yazilmadi()


@pytest.mark.parametrize(
    ("icerik", "tur"),
    [(PDF, "application/pdf"), (JPEG, "image/jpeg"), (PNG, "image/png")],
    ids=["pdf", "jpeg", "png"],
)
def test_tur_imza_baytindandir(sahip: SchoolYear, icerik: bytes, tur: str) -> None:
    assert _yaz(sahip, icerik, original_name="uzantisi-yaniltici.exe").mime == tur


@pytest.mark.parametrize(
    "icerik",
    [b"", b"PK\x03\x04uydurma calisma kitabi", b"duz metin"],
    ids=["bos", "zip", "metin"],
)
def test_kabul_edilmeyen_dosya_diske_yazilmaz(sahip: SchoolYear, icerik: bytes) -> None:
    with pytest.raises(ds.TurHatasi):
        _yaz(sahip, icerik)
    _hicbir_sey_yazilmadi()


def test_bildirilen_tur_icerige_uymali(sahip: SchoolYear) -> None:
    with pytest.raises(ds.TurHatasi):
        _yaz(sahip, mime="image/png")
    _hicbir_sey_yazilmadi()
    assert _yaz(sahip, mime="application/pdf").mime == "application/pdf"


def test_yukleme_sinirini_asan_ek_reddedilir(sahip: SchoolYear, settings: Any) -> None:
    settings.FILE_UPLOAD_MAX_MEMORY_SIZE = len(PDF)
    assert _yaz(sahip).size == len(PDF)  # sınırın kendisi kabul edilir
    onceki = _depodaki_adlar()
    with pytest.raises(ds.BoyutSiniriHatasi):
        _yaz(sahip, PDF + b"x")
    assert _depodaki_adlar() == onceki


def test_yukleme_siniri_ayarla_bicim_sinirinin_kucugudur(settings: Any) -> None:
    assert dosya_deposu.yukleme_siniri() == settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    settings.FILE_UPLOAD_MAX_MEMORY_SIZE = 10**12
    assert dosya_deposu.yukleme_siniri() == ds.AZAMI_ACIK_BOY


def test_sahip_kumesinde_yalniz_uretilen_evrak_vardir() -> None:
    """İlk ve bugünkü tek sahip `oab.GeneratedDocument`'tır ve üretilen evrak sahibidir (PDF, DOCX;
    plan F1c 9. adım); kullanıcı eki sahibi henüz yoktur."""
    assert dosya_deposu._SAHIP_ETIKETLERI == {"oab.GeneratedDocument"}
    assert dosya_deposu._URETILEN_EVRAK_SAHIPLERI == {"oab.GeneratedDocument"}
    assert dosya_deposu.kabul_turleri(SchoolYear) == ds.KABUL_EDILEN_TURLER


DOCX_KAPI = "Bu dosya türü eklenemez; yalnız PDF, JPEG ve PNG dosyaları kabul edilir."


def _docx() -> bytes:
    from shared import evrak

    return evrak.docx_ciz(evrak.ornek_belge())


def test_kullanici_eki_sahibine_docx_yazilmaz(sahip: SchoolYear) -> None:
    """DOCX türü yalnız üretilen evrak sahibinindir; kullanıcı eki kümesi PDF, JPEG, PNG kalır."""
    onceki = _depodaki_adlar()
    with pytest.raises(ds.TurHatasi, match=re.escape(DOCX_KAPI)):
        _yaz(sahip, _docx())
    assert _depodaki_adlar() == onceki and not Attachment.objects.exists()


def test_uretilen_evrak_sahibi_docx_ve_pdf_alir_jpeg_almaz(sahip: SchoolYear) -> None:
    dosya_deposu.sahip_kaydet(SchoolYear, uretilen_evrak=True)
    try:
        assert _yaz(sahip, _docx()).mime == ds.DOCX.mime
        assert _yaz(sahip, PDF).mime == "application/pdf"
        with pytest.raises(ds.TurHatasi, match="yalnız PDF ya da Word"):
            _yaz(sahip, JPEG)
        # DOCX imzası (ZIP) tek başına yetmez: Word girdileri olmayan ZIP reddedilir.
        with pytest.raises(ds.TurHatasi):
            _yaz(sahip, b"PK\x03\x04" + bytes(64))
    finally:
        dosya_deposu.sahip_kaydet(SchoolYear)
    assert dosya_deposu.kabul_turleri(SchoolYear) == ds.KABUL_EDILEN_TURLER


def test_silinmis_sahibin_bayat_ornegine_ek_yazilmaz(sahip: SchoolYear) -> None:
    """`pk`'sı dolu ama satırı artık olmayan sahip (`_sahip_bagi`'nin bayat örnek boşluğu; plan F1b-3
    ekleri): reddedilir, diske bir şey yazılmaz."""
    bayat = SchoolYear(pk=sahip.pk + 1000, name="2030-2031")
    bayat._state.adding = False
    onceki = _depodaki_adlar()
    with pytest.raises(dosya_deposu.EkSahibiHatasi, match="kaydedilmiş bir kayda"):
        _yaz(bayat)
    assert _depodaki_adlar() == onceki


def test_bakim_kapisi_kapaliyken_ek_yazilmaz(sahip: SchoolYear) -> None:
    """Canlı geri yükleme depoyu takas ederken yazım başlamaz (plan F1b-3 ekleri, F1c 9. adım):
    `DepoBakimda`, diske ve veritabanına bir şey yazılmaz; kapı açılınca yazım yürür."""
    onceki = _depodaki_adlar()
    assert bakim.KAPI.bakima_al(bekleme_sn=0.1)
    try:
        with pytest.raises(dosya_deposu.DepoBakimda, match="Geri yükleme sürüyor"):
            _yaz(sahip)
    finally:
        bakim.KAPI.bakimdan_cik()
    assert _depodaki_adlar() == onceki and not Attachment.objects.exists()
    assert bakim.KAPI.ucusta == 0
    _yaz(sahip)
    assert bakim.KAPI.ucusta == 0


def test_yazim_suren_is_olarak_bakim_kapisindan_gecer(
    sahip: SchoolYear, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Yazım sürerken kapının uçuştaki iş sayacı birdir: geri yükleme onu bekler."""
    gorulen: list[int] = []
    asil = ds.depoya_yaz

    def say(*args: Any, **kwargs: Any) -> Any:
        gorulen.append(bakim.KAPI.ucusta)
        return asil(*args, **kwargs)

    monkeypatch.setattr(ds, "depoya_yaz", say)
    _yaz(sahip)
    assert gorulen == [1] and bakim.KAPI.ucusta == 0


def test_kayitli_olmayan_model_eke_sahip_olamaz() -> None:
    yil = school_year_service.create_school_year(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), activate=True
    )
    with pytest.raises(dosya_deposu.EkSahibiHatasi):
        _yaz(yil)
    _hicbir_sey_yazilmadi()


def test_kaydedilmemis_kayit_eke_sahip_olamaz(sahip: SchoolYear) -> None:
    with pytest.raises(dosya_deposu.EkSahibiHatasi):
        _yaz(SchoolYear(name="2027-2028"))
    _hicbir_sey_yazilmadi()


def test_silinmis_kayit_eke_sahip_olamaz(sahip: SchoolYear) -> None:
    """Silinen örnekte `pk` boşalır, `adding` değişmez: `owner_id` "None" metni olurdu."""
    sahip.hard_delete()
    assert sahip.pk is None and not sahip._state.adding
    with pytest.raises(dosya_deposu.EkSahibiHatasi):
        _yaz(sahip)
    _hicbir_sey_yazilmadi()


@pytest.mark.parametrize(
    "ad",
    ["", "   ", "x" * (dosya_deposu.OZGUN_AD_UZUNLUGU + 1), None],
    ids=["bos", "bosluk", "uzun", "metin-degil"],
)
def test_gecersiz_ozgun_ad_reddedilir(sahip: SchoolYear, ad: Any) -> None:
    with pytest.raises(dosya_deposu.DosyaDeposuHatasi):
        _yaz(sahip, original_name=ad)
    _hicbir_sey_yazilmadi()


def test_en_uzun_ozgun_ad_kabul_edilir(sahip: SchoolYear) -> None:
    ad = "ş" * dosya_deposu.OZGUN_AD_UZUNLUGU
    assert Attachment.objects.get(pk=_yaz(sahip, original_name=ad).pk).original_name == ad


def test_gecersiz_hassasiyet_reddedilir(sahip: SchoolYear) -> None:
    with pytest.raises(dosya_deposu.DosyaDeposuHatasi):
        _yaz(sahip, sensitivity="GIZLI")
    _hicbir_sey_yazilmadi()


# ============================================================ uzun iş


def test_uzun_is_sayaci_yazim_boyunca_tutulur(
    sahip: SchoolYear, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Plan F1b-3 "Ek yazımı uzun iştir": dosya yazımında da satır yazımında da sayaç birdir."""
    gorulen: list[int] = []
    asil_dosya, asil_iz = ds.depoya_yaz, denetim_izi.degisiklik

    def dosya_casusu(*args: Any, **alanlar: Any) -> Any:
        gorulen.append(bakim.UZUN_ISLER.sayi)
        return asil_dosya(*args, **alanlar)

    def iz_casusu(*args: Any, **alanlar: Any) -> Any:
        gorulen.append(bakim.UZUN_ISLER.sayi)
        return asil_iz(*args, **alanlar)

    monkeypatch.setattr(ds, "depoya_yaz", dosya_casusu)
    monkeypatch.setattr(denetim_izi, "degisiklik", iz_casusu)
    _yaz(sahip)
    assert gorulen == [1, 1]
    assert bakim.UZUN_ISLER.sayi == 0


@pytest.mark.parametrize("dusen", ["dosya", "iz", "anahtar"])
def test_uzun_is_sayaci_istisnada_da_birakilir(
    sahip: SchoolYear, monkeypatch: pytest.MonkeyPatch, dusen: str
) -> None:
    gorulen: list[int] = []

    def patla(*_: Any, **__: Any) -> Any:
        gorulen.append(bakim.UZUN_ISLER.sayi)
        raise OSError("uydurma hata")

    if dusen == "dosya":
        monkeypatch.setattr(ds, "depoya_yaz", patla)
    elif dusen == "iz":
        monkeypatch.setattr(denetim_izi, "degisiklik", patla)
    else:
        monkeypatch.setattr(crypto, "file_wrap_key", patla)
    with pytest.raises(OSError, match="uydurma"):
        _yaz(sahip)
    assert gorulen == [1]
    assert bakim.UZUN_ISLER.sayi == 0


# ============================================================ okuma


def test_oku_acik_icerigi_bellekte_verir(sahip: SchoolYear) -> None:
    ek = Attachment.objects.get(pk=_yaz(sahip).pk)
    onceki = _depodaki_adlar()
    assert dosya_deposu.oku(ek) == PDF
    assert dosya_deposu.oku(ek, TEST_DEK) == PDF
    assert _depodaki_adlar() == onceki  # açık kopya bırakılmaz


def test_ozet_tutmazsa_bayt_verilmez(sahip: SchoolYear) -> None:
    ek = _yaz(sahip, sensitivity=AttachmentSensitivity.OZEL_NITELIKLI)
    _guncelle(ek, sha256="0" * 64)
    ek.refresh_from_db()
    with pytest.raises(dosya_deposu.EkOzetiTutmuyor):
        dosya_deposu.oku(ek)
    assert not AccessLog.objects.exists()


def test_diskte_olmayan_dosya_dosya_yoktur(sahip: SchoolYear) -> None:
    ek = _yaz(sahip, sensitivity=AttachmentSensitivity.OZEL_NITELIKLI)
    _dosya(ek).unlink()
    with pytest.raises(dosya_deposu.EkDosyasiYok):
        dosya_deposu.oku(ek)
    assert not AccessLog.objects.exists()


def test_imhali_ek_dosya_yoktur_dosya_diskte_olsa_da(sahip: SchoolYear) -> None:
    ek = _yaz(sahip)
    _guncelle(ek, purged_at=ORNEK_AN, key_wrap="", original_name="")
    ek.refresh_from_db()
    assert _dosya(ek).is_file()
    with pytest.raises(dosya_deposu.EkDosyasiYok):
        dosya_deposu.oku(ek)


def test_baska_ekin_kabi_acilmaz(sahip: SchoolYear) -> None:
    ilk, ikinci = _yaz(sahip), _yaz(sahip, PNG)
    _dosya(ikinci).write_bytes(_dosya(ilk).read_bytes())
    with pytest.raises(ds.DogrulamaHatasi):
        dosya_deposu.oku(ikinci)


def test_bozulmus_dosya_acilmaz(sahip: SchoolYear) -> None:
    ek = _yaz(sahip)
    kap = bytearray(_dosya(ek).read_bytes())
    kap[-1] ^= 0x01
    _dosya(ek).write_bytes(bytes(kap))
    with pytest.raises(ds.DogrulamaHatasi):
        dosya_deposu.oku(ek)


def test_baska_dek_ile_acilmaz(sahip: SchoolYear) -> None:
    with pytest.raises(ds.DogrulamaHatasi):
        dosya_deposu.oku(_yaz(sahip), b"\x07" * 32)


def test_degistirilmis_depo_adi_yol_kurmaz(sahip: SchoolYear) -> None:
    ek = _yaz(sahip)
    ek.stored_name = "../../guvenlik.json"
    with pytest.raises(ds.GecersizAdHatasi):
        dosya_deposu.oku(ek)


def test_ozel_nitelikli_ekin_okunmasi_erisim_gunlugune_yazilir(sahip: SchoolYear) -> None:
    ek = _yaz(sahip, sensitivity=AttachmentSensitivity.OZEL_NITELIKLI)
    assert not AccessLog.objects.exists()  # yazım okuma değildir
    assert dosya_deposu.oku(ek) == PDF
    satir = AccessLog.objects.get()
    assert (satir.kind, satir.model) == (AccessKind.OZEL_NITELIKLI_EK, "okul.Attachment")
    assert (satir.object_id, satir.field) == (str(ek.pk), "")
    assert (str(satir.account_id), satir.role) == (TEST_HESAP_ID, TEST_ROL)
    assert (satir.document_sha256, satir.row_count) == ("", None)


def test_olagan_ekin_okunmasi_erisim_gunlugune_yazilmaz(sahip: SchoolYear) -> None:
    dosya_deposu.oku(_yaz(sahip))
    assert not AccessLog.objects.exists()


@pytest.mark.parametrize("kim", [SISTEM, None], ids=["sistem", "baglamsiz"])
def test_gunluge_yazilamayan_ozel_nitelikli_ek_verilmez(
    sahip: SchoolYear, kim: Yazar | None
) -> None:
    """Tasarım §4.6.4; `erisim_gunlugu` "KULLANIM": satır yazılamazsa bayt verilmez."""
    ek = _yaz(sahip, sensitivity=AttachmentSensitivity.OZEL_NITELIKLI)
    with yazar_olarak(kim), pytest.raises(erisim_gunlugu.ErisimGunluguYazilamadi):
        dosya_deposu.oku(ek)
    assert not AccessLog.objects.exists()


# ============================================================ DEK yokken


@pytest.fixture
def anahtarsiz() -> Iterator[None]:
    crypto.unload_key()
    yield


def test_dek_yokken_hicbir_sey_yazilmaz(sahip: SchoolYear, anahtarsiz: None) -> None:
    """Fail-closed (tasarım §5.3): anahtar bellekte değilken dosya da satır da yazılmaz."""
    with pytest.raises(crypto.KeyMissingError):
        _yaz(sahip)
    assert _depodaki_adlar() == set()
    assert Attachment._base_manager.count() == 0
    assert bakim.UZUN_ISLER.sayi == 0


def test_dek_yokken_okunmaz_imhali_ekte_de(sahip: SchoolYear) -> None:
    ek = _yaz(sahip)
    imhali = _yaz(sahip)
    _guncelle(imhali, purged_at=ORNEK_AN, key_wrap="", original_name="")
    imhali.refresh_from_db()
    crypto.unload_key()
    with pytest.raises(crypto.KeyMissingError):
        dosya_deposu.oku(ek)
    with pytest.raises(crypto.KeyMissingError):
        dosya_deposu.oku(imhali)


# ============================================================ tek yazar

#: Dizede modelin (`Attachment`, `okul.Attachment`) ya da tablonun (`okul_attachment`) adı.
#: Django ve SQLite büyük-küçük harf ayırmaz; yalın küçük `attachment` yalnız tek başına bir dize
#: olunca sayılır, `Content-Disposition`'daki `attachment; filename=…` sayılmaz.
_EK_ADI = re.compile(r"\bAttachment\b|(?i:\bokul[._]attachment\b)|^attachment$")
#: `Attachment`'a yazan zincirlerin İZİNLİ yerleri: (dosya, birim, zincirin adları). Sahip kümesi,
#: R9, tür denetimi ve önce-dosya sırası yalnız `yaz`'dadır; veritabanı `owner_type` kümesini
#: zorlayamaz. F4-F6 imhası ve TK12 sarmal yenilemesi gelince kendi yerleri adıyla eklenir.
EK_YAZIM_YERLERI = {("apps/okul/services/dosya_deposu.py", "yaz", ("objects", "create"))}
#: Tabloyu ham SQL ile OKUYAN üç yer: masaüstü manifestosu Django'dan ve göçten önce koşar, ORM
#: kullanamaz (plan F1b-3 "Kap ve manifesto"); geri yükleme bozuk olabilecek bir veritabanını
#: ORM'siz okur (plan F1b-3 "Geri yükleme"); yetim taraması okunamayan tabloda depoya dokunmaz ve
#: Django bağlantısı açmaz (plan F1b-3 "Geri yükleme"). İzin dosyaya ya da birime değil bu dizelerin TAM
#: METNİNE verilir ve burada elle yazılıdır: kaynaktan alınsaydı sorgu `DELETE`'e dönünce izin de
#: onunla değişirdi. Aynı dosyadaki başka dize yine yakalanır.
EK_OKUMA_DIZELERI = (
    ("desktop/backup.py", "okul_attachment"),
    (
        "desktop/backup.py",
        "SELECT stored_name, size, sha256 FROM okul_attachment "
        "WHERE purged_at IS NULL ORDER BY stored_name",
    ),
    (
        "apps/okul/services/geri_yukleme_ekleri.py",
        "SELECT stored_name, key_wrap, size, sha256, owner_type, owner_id, uploaded_at "
        "FROM okul_attachment WHERE purged_at IS NULL ORDER BY stored_name",
    ),
    ("apps/okul/masaustu_kanca.py", "SELECT stored_name FROM okul_attachment"),
)

#: Programa eklenen ek yazımları ve atlatmaları: her biri yakalanmalıdır.
_EK_SONDASI = """
from apps.okul import denetim_izi, models
from apps.okul.models import Attachment
from apps.okul.models import Attachment as Ek
from django.apps import apps as django_apps


def izli_serviste_serbest_sahip():
    yeni = Attachment.objects.create(owner_type="serbest.Metin", owner_id="1")
    denetim_izi.degisiklik(yeni, onceki=None)


def toplu_ekleme():
    models.Attachment.objects.bulk_create([Attachment(owner_id="1")])


def kurucuyla_yazim():
    Attachment(owner_id="1").save()


def yoneticiyi_atlayan_silme(pk):
    Attachment._base_manager.filter(pk=pk).delete()


def ham_silme(pk):
    Attachment.objects.filter(pk=pk)._raw_delete("default")


def sessiz_guncelleme(pk):
    Attachment.objects.filter(pk=pk).update(owner_id="2")


def tablo_adi_dizeyle(cursor):
    cursor.execute("DELETE FROM okul_attachment")


def model_adi_dizeyle():
    return django_apps.get_model("okul", "Attachment")


def buyuk_harfli_tablo(cursor):
    cursor.execute("DELETE FROM OKUL_ATTACHMENT")


def kucuk_harfli_model_adi():
    return django_apps.get_model("okul", "attachment")


def noktali_kucuk_harfli_model_adi():
    return django_apps.get_model("okul.attachment")


def okuma(pk):
    return Attachment.objects.filter(pk=pk).first(), "attachment; filename=belge.pdf"
"""


def _ek_yazimlari(kaynaklar: dict[str, str]) -> set[tuple[str, str, tuple[str, ...]]]:
    return _kok_yazimlari(
        kaynaklar, kok="Attachment", ad_deseni=_EK_ADI, okuma_dizeleri=EK_OKUMA_DIZELERI
    )


def test_ekin_tek_yazari_depo_servisidir() -> None:
    """Plan F1b-3: `owner_type` kayıtlı kümeden gelir; `Attachment` belge dizesi "tek yazarı odur".

    İzsiz yazım taraması izli bir işlevdeki doğrudan yazımı izli saydığı için bunu göremez
    (`AccessLog`'un eşi: `test_erisim_gunlugu.py`). Eşitlik iki yönlüdür.
    """
    assert _ek_yazimlari(_program_kaynaklari()) == EK_YAZIM_YERLERI


def test_manifestonun_okuma_dizeleri_programda_durur() -> None:
    """İzin iki yönlüdür: sorgu değişirse ya da kalkarsa izin bayat kalmaz."""
    kaynaklar = _program_kaynaklari()
    for yol, dize in EK_OKUMA_DIZELERI:
        dugumler = ast.walk(ast.parse(kaynaklar[yol]))
        assert dize in {dugum.value for dugum in dugumler if isinstance(dugum, ast.Constant)}


@pytest.mark.parametrize(
    "dize",
    [
        "DELETE FROM okul_attachment",
        "UPDATE okul_attachment SET purged_at = NULL",
        "SELECT stored_name, size, sha256, key_wrap FROM okul_attachment",
        "okul.Attachment",
    ],
)
def test_manifestonun_okuma_izni_ayni_dosyadaki_baska_dizeyi_ortmez(dize: str) -> None:
    """İzin tam metnedir: manifestonun dosyasına eklenen yazım da, geniş okuma da yakalanır."""
    assert _ek_yazimlari({"desktop/backup.py": f"_SORGU = {dize!r}\n"}) == {
        ("desktop/backup.py", "<modül>", ("<dize>",))
    }


def test_ek_taramasi_yazimlari_ve_atlatmalari_yakalar() -> None:
    """Taramanın `Attachment` kökünde çalıştığı: izli işlevdeki yazım, kurucu, yöneticiyi atlayan
    silme, `_raw_delete`, takma ad ve dize (büyük-küçük harf ayırmadan) yakalanır; okuma ve
    `Content-Disposition`'daki `attachment;` sayılmaz."""
    bulunan = {birim for _, birim, _ in _ek_yazimlari({"apps/okul/services/sonda.py": _EK_SONDASI})}
    assert bulunan == {
        "<modül>",  # takma ad
        "izli_serviste_serbest_sahip",
        "toplu_ekleme",
        "kurucuyla_yazim",
        "yoneticiyi_atlayan_silme",
        "ham_silme",
        "sessiz_guncelleme",
        "tablo_adi_dizeyle",
        "model_adi_dizeyle",
        "buyuk_harfli_tablo",
        "kucuk_harfli_model_adi",
        "noktali_kucuk_harfli_model_adi",
    }


# ============================================================ ayarlar


def test_genel_yukleme_isleyicisi_yalniz_bellektir(settings: Any) -> None:
    (isleyici,) = settings.FILE_UPLOAD_HANDLERS
    sinif = import_string(isleyici)
    assert issubclass(sinif, MemoryFileUploadHandler)
    assert not issubclass(sinif, TemporaryFileUploadHandler)


def test_yukleme_ayarlari_tek_siniri_tasir(settings: Any) -> None:
    sinir = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    assert settings.FILE_UPLOAD_MAX_MEMORY_SIZE == sinir
    assert settings.DATA_UPLOAD_MAX_MEMORY_SIZE == sinir


def test_ailenin_medya_ayari_kalkti() -> None:
    from config import settings as ayarlar

    assert not hasattr(ayarlar, "MEDIA_ROOT")


def test_depo_yollari_masaustu_yerlesimiyle_aynidir() -> None:
    """Backend `desktop`'a bağımlı olmadığı için ad iki yerdedir; eşitliği burada sabitlenir."""
    from config import settings as ayarlar

    assert ayarlar.DOSYA_DEPOSU_DIR == ayarlar.DATA_DIR / masaustu_yollari.DOSYA_DEPOSU_DIR_NAME
    assert ds.YETIM_DIZINI == masaustu_yollari.YETIM_DIR_NAME


def test_eski_esigi_asan_yukleme_bellekte_kalir() -> None:
    """Django'nun 2,5 MB'lık varsayılanı geçici dizine DÜZ yazardı (açık kopya kuralı, §4.4.7).

    Bu test yalnız Django katmanını görür; sunucu tamponu `desktop/tests/test_server.py`'dedir.
    """
    dosya = SimpleUploadedFile("liste.xlsx", b"x" * (3 * 1024 * 1024))
    istek = RequestFactory().post("/api/v1/imports/personnel/preview/", {"file": dosya})
    assert isinstance(istek.FILES["file"], InMemoryUploadedFile)


def test_sinirdan_buyuk_yukleme_iletisiyle_reddedilir(settings: Any) -> None:
    """Bellek işleyicisi dosyayı sessizce düşürürdü; uç "dosya seçin" derdi (`shared.yukleme`)."""
    settings.FILE_UPLOAD_MAX_MEMORY_SIZE = 1024
    settings.MAX_UPLOAD_SIZE_MB = 7
    yanit = APIClient().post(
        "/api/v1/imports/personnel/preview/",
        {"file": SimpleUploadedFile("liste.xlsx", b"x" * 2048)},
        format="multipart",
    )
    assert yanit.status_code == 400
    assert yanit.json()["message"] == "Dosya çok büyük; en çok 7 MB olabilir."


# ============================================================ eksik ekler (Genel Bakış kartı)


def test_eksik_ekler_satiri_olup_dosyasi_olmayan_eki_verir(sahip: SchoolYear) -> None:
    """Tasarım §4.4.7: satırı olup dosyası olmayan kayıt Genel Bakış'ta Eksik Ekler kartını
    çıkarır; plan: asıl dosya adı bu kartta görünür."""
    yerinde = _yaz(sahip)
    kayip = _yaz(sahip, PNG, original_name="Örnek rapor.png")
    _guncelle(kayip, uploaded_at=datetime(2026, 11, 3, 21, 30, tzinfo=UTC))
    _dosya(kayip).unlink()

    assert dosya_deposu.eksik_ekler() == [
        {
            "kayit_turu": "ders yılı",
            "kayit_no": kayip.owner_id,
            "yukleme_tarihi": "2026-11-04",  # 21:30 UTC yerelde ertesi gündür
            "boyut": len(PNG),
            "ozgun_ad": "Örnek rapor.png",
        }
    ]
    assert _dosya(yerinde).is_file()


def test_eksik_ekler_eskiden_yeniye_dizilir(sahip: SchoolYear) -> None:
    yeni, eski = _yaz(sahip, original_name="yeni.pdf"), _yaz(sahip, original_name="eski.pdf")
    _guncelle(yeni, uploaded_at=datetime(2026, 11, 4, 9, 0, tzinfo=UTC))
    _guncelle(eski, uploaded_at=datetime(2026, 10, 4, 9, 0, tzinfo=UTC))
    _dosya(yeni).unlink()
    _dosya(eski).unlink()

    assert [satir["ozgun_ad"] for satir in dosya_deposu.eksik_ekler()] == ["eski.pdf", "yeni.pdf"]


def test_eksik_ekler_imhali_satiri_saymaz(sahip: SchoolYear) -> None:
    ek = _yaz(sahip)
    _dosya(ek).unlink()
    _guncelle(ek, purged_at=ORNEK_AN, key_wrap="", original_name="")

    assert dosya_deposu.eksik_ekler() == []


def test_eksik_ekler_dosya_yerine_dizin_duruyorsa_eksik_sayar(sahip: SchoolYear) -> None:
    ek = _yaz(sahip)
    _dosya(ek).unlink()
    _dosya(ek).mkdir()

    assert len(dosya_deposu.eksik_ekler()) == 1


def test_eksik_ekler_cozulemeyen_adi_bos_verir_yanit_kodlanabilir(sahip: SchoolYear) -> None:
    """`CorruptField` metin değildir: uç onu JSON'a çeviremez, kart okunamaz görünürdü."""
    ek = _yaz(sahip)
    _dosya(ek).unlink()
    with connection.cursor() as imlec:
        imlec.execute(
            "UPDATE okul_attachment SET original_name = %s WHERE stored_name = %s",
            ["duz-metin", ek.stored_name],
        )

    (satir,) = dosya_deposu.eksik_ekler()

    assert satir["ozgun_ad"] is None
    json.dumps(satir)


def test_eksik_ekler_yalniz_eksik_ekin_adini_cozer(sahip: SchoolYear) -> None:
    """Depodaki ekin özgün adı okunmaz: kart her açılışta bütün satırları çözmesin."""
    _yaz(sahip)
    kayip = _yaz(sahip)
    _dosya(kayip).unlink()

    with CaptureQueriesContext(connection) as sorgular:
        dosya_deposu.eksik_ekler()

    assert len(sorgular) == 2  # liste ve eksik ekin ertelenen adı


def test_denetim_kartlari_eksik_ekleri_tasir_depo_okunamazsa_kart_okunamaz_der(
    sahip: SchoolYear, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Hata gerçek biçimindedir: `OSError` yolu taşır, yol hesap adını içerir, günlüğe düşmez."""
    ek = _yaz(sahip)
    _dosya(ek).unlink()

    (satir,) = iz_dogrulama.denetim_kartlari(TEST_HESAP_ID)["eksik_ekler"]
    assert satir["ozgun_ad"] == UYDURMA_DOSYA_ADI

    depo = dosya_deposu.depo_dizini()

    def duser(_depo: Path) -> list[str]:
        raise PermissionError(13, "Erişim engellendi", str(depo))

    monkeypatch.setattr(ds, "depodaki_dosyalar", duser)

    with caplog.at_level(logging.ERROR, logger="oab_defteri.okul"):
        kartlar = iz_dogrulama.denetim_kartlari(TEST_HESAP_ID)

    assert kartlar["eksik_ekler"] == []
    assert "eksik_ekler" in kartlar["okunamayan"]
    assert "Dosya deposu okunamadı (PermissionError)." in caplog.text
    assert str(depo) not in caplog.text


def test_kendi_kartlari_eksik_ekleri_tasimaz(sahip: SchoolYear) -> None:
    """Özgün ad her role gitmez: alan yalnız denetim kartlarındadır (program yöneticisi ve DK)."""
    ek = _yaz(sahip)
    _dosya(ek).unlink()

    assert "eksik_ekler" not in iz_dogrulama.kendi_kartlari(TEST_HESAP_ID)
