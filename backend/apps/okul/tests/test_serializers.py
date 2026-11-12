"""`okul` serializer doğrulamalarının başka dosyada sınanmayan dalları.

Kişi doğrulamaları kendi test dosyasındadır (`test_persons`; öğrenci ve şube serileştiricileri
F1b 5. adımda söküldü). Burada kalanlar:

- Serializer alan kümeleri — ön yüz tiplerinin sözleşmesi (anlık görüntü; tipler elle, TK2).
  Aile iskeletinin atasından kaldırılan alanların (zil, vardiya, şube kümesi, zümre, cinsiyet, okul
  türü/çizelge) geri sızması burada yakalanır.
- `SchoolConfigSerializer` — okul kartının ileti tablosu (F1b 4. adım; plan F1b-4 kararları):
  her satır ayrı dal, iletiler ön yüzle BİREBİR aynıdır. Uçtan akışlar `test_setup.py`'dedir.
- `SchoolYearSerializer` — tarih sırası ve ad tekliği.
- `ImportRequestSerializer` — dosya ile pano metni BİRBİRİNİ DIŞLAR.

Kişisel veri yoktur.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul.models import ImportRun, SchoolConfig, SchoolYear
from apps.okul.serializers import (
    DEMIRBAS_ONAYI_ZORUNLU,
    IL_ZORUNLU,
    ILCE_ZORUNLU,
    KADEME_GECERSIZ,
    KADEME_ZORUNLU,
    KANTIN_ZORUNLU,
    KURUM_KODU_GECERSIZ,
    KURUM_KODU_ZORUNLU,
    MEVCUT_GECERSIZ,
    MEVCUT_TARIHI_GELECEKTE,
    MEVCUT_TARIHI_ZORUNLU,
    MEVCUT_ZORUNLU,
    OKUL_ADI_ZORUNLU,
    PERSONEL_ZORUNLU,
    SECENEK_GECERSIZ,
    YERLESIM_ZORUNLU,
    ImportRequestSerializer,
    PersonnelSerializer,
    SchoolConfigSerializer,
)
from apps.okul.tests.okul_karti_ortak import okul_karti_govdesi

pytestmark = pytest.mark.django_db

AYAR_URL = "/api/v1/setup/school-config/"
YIL_URL = "/api/v1/school-years/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


# ---------------------------------------------------------------------------
# Alan kümeleri (ön yüz sözleşmesi)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("serializer", "alanlar"),
    [
        (
            SchoolConfigSerializer,
            {
                "school_name",
                "province",
                "district",
                "principal_name",
                "institution_code",
                "levels",
                "student_count",
                "student_count_as_of",
                "settlement_type",
                "canteen_mode",
                "staffing_mode",
                "in_campus",
                "opened_on",
                "demirbas_onayi",
                "demirbas_no",
                "data_controller_text",
                "setup_completed",
            },
        ),
        (
            PersonnelSerializer,
            {
                "id",
                "first_name",
                "last_name",
                "full_name",
                "member_kind",
                "is_active",
                "left_at",
                "leave_candidate_since",
            },
        ),
    ],
)
def test_serializer_alan_kumesi_sabittir(serializer: Any, alanlar: set[str]) -> None:
    assert set(serializer().fields) == alanlar


def test_okul_ayarinda_kaldirilan_alanlar_yok_sayilir(client: APIClient) -> None:
    """Eski ön yüzün gönderebileceği kaldırılmış alanlar 400 üretmez, hiçbir yere de yazılmaz."""
    yanit = client.put(
        AYAR_URL,
        {
            "school_name": "Örnek Okul",
            "has_prep_class": True,
            "school_type": "ANADOLU_LISESI",
            "bell_schedule": [],
            "default_separation_mode": "ROOM",
        },
        format="json",
    )

    assert yanit.status_code == 200
    assert set(yanit.json()) == set(SchoolConfigSerializer().fields)
    ayar = SchoolConfig.load()
    # `has_prep_class` okul kartından çıktı (F1b 4. adım), alanı 5. adımda düştü.
    assert ayar.school_name == "Örnek Okul"
    assert not hasattr(ayar, "has_prep_class")


def test_ice_aktarma_girdisinde_eski_tam_liste_onayi_yoktur() -> None:
    """Öğrenci aktarımının `full_list` onayı öğrenci tarafıyla söküldü; gelirse yok sayılır."""
    serializer = ImportRequestSerializer(data={"text": "x", "full_list": True})
    assert serializer.is_valid(), serializer.errors
    assert "full_list" not in serializer.validated_data
    assert "full_list" not in ImportRequestSerializer().fields


# ---------------------------------------------------------------------------
# Okul kartı: ileti tablosu (tablo satırı başına bir dal)
# ---------------------------------------------------------------------------


def _hatalar(govde: dict[str, Any]) -> dict[str, list[str]]:
    serializer = SchoolConfigSerializer(data=govde)
    assert not serializer.is_valid()
    return {ad: [str(ileti) for ileti in iletiler] for ad, iletiler in serializer.errors.items()}


def _yarin() -> str:
    return (timezone.localdate() + timedelta(days=1)).isoformat()


@pytest.mark.parametrize(
    ("alan", "deger", "ileti"),
    [
        ("school_name", "", OKUL_ADI_ZORUNLU),
        ("school_name", "   ", OKUL_ADI_ZORUNLU),
        ("province", "", IL_ZORUNLU),
        ("district", " ", ILCE_ZORUNLU),
        ("institution_code", "", KURUM_KODU_ZORUNLU),
        ("institution_code", None, KURUM_KODU_ZORUNLU),
        ("institution_code", "12345", KURUM_KODU_GECERSIZ),
        ("institution_code", "1234567", KURUM_KODU_GECERSIZ),
        ("institution_code", "12a456", KURUM_KODU_GECERSIZ),
        ("institution_code", "١٢٣٤٥٦", KURUM_KODU_GECERSIZ),
        ("institution_code", ["999001"], KURUM_KODU_GECERSIZ),
        ("levels", [], KADEME_ZORUNLU),
        ("levels", ["UNIVERSITE"], KADEME_GECERSIZ),
        ("levels", ["ILKOKUL", "KARMA"], KADEME_GECERSIZ),
        ("levels", [1], KADEME_GECERSIZ),
        ("levels", "ILKOKUL", KADEME_GECERSIZ),
        ("levels", None, KADEME_GECERSIZ),
        ("student_count", None, MEVCUT_ZORUNLU),
        ("student_count", -1, MEVCUT_GECERSIZ),
        ("student_count", 100000, MEVCUT_GECERSIZ),
        ("student_count", 12.5, MEVCUT_GECERSIZ),
        ("student_count", "çok", MEVCUT_GECERSIZ),
        ("student_count", True, MEVCUT_GECERSIZ),
        ("student_count_as_of", None, MEVCUT_TARIHI_ZORUNLU),
        ("student_count_as_of", "yarın", MEVCUT_TARIHI_GELECEKTE),
        ("settlement_type", "", YERLESIM_ZORUNLU),
        ("settlement_type", None, YERLESIM_ZORUNLU),
        ("settlement_type", "KOY", SECENEK_GECERSIZ),
        ("canteen_mode", "", KANTIN_ZORUNLU),
        ("canteen_mode", "KIRALIK", SECENEK_GECERSIZ),
        ("staffing_mode", "", PERSONEL_ZORUNLU),
        ("staffing_mode", "TASERON", SECENEK_GECERSIZ),
        ("demirbas_onayi", False, DEMIRBAS_ONAYI_ZORUNLU),
    ],
)
def test_okul_karti_iletileri(alan: str, deger: object, ileti: str) -> None:
    """Sözleşmenin ileti tablosu: alan gövdede VARSA uygulanır, ileti yalnız o alandadır.

    ASCII olmayan rakam (Arapça-Hint rakamları) kurum kodu sayılmaz; "yarın" bugünden
    (Europe/Istanbul) bir gün sonrasının yer tutucusudur.
    """
    deger = _yarin() if deger == "yarın" else deger
    assert _hatalar(okul_karti_govdesi(**{alan: deger})) == {alan: [ileti]}


@pytest.mark.parametrize(
    ("govde", "beklenen"),
    [
        ({"student_count": 10}, {"student_count_as_of": [MEVCUT_TARIHI_ZORUNLU]}),
        ({"student_count_as_of": "2026-10-01"}, {"student_count": [MEVCUT_ZORUNLU]}),
    ],
    ids=["tarih_eksik", "mevcut_eksik"],
)
def test_mevcut_ve_tarihi_biri_gelirse_eksik_olan_zorunludur(
    govde: dict[str, Any], beklenen: dict[str, list[str]]
) -> None:
    assert _hatalar(govde) == beklenen


def test_bos_govde_gecerlidir_ve_hicbir_alan_yazilmaz() -> None:
    """Kısmi PUT: gövdede olmayan alana dokunulmaz (bütün alanlar `required=False`)."""
    serializer = SchoolConfigSerializer(data={})
    assert serializer.is_valid(), serializer.errors
    assert dict(serializer.validated_data) == {}


def test_eksiksiz_kart_gecerlidir_istege_bagli_alanlar_bos_olabilir() -> None:
    serializer = SchoolConfigSerializer(
        data=okul_karti_govdesi(principal_name="", in_campus=False, opened_on=None)
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["opened_on"] is None


def test_mevcudun_tarihi_bugun_olabilir() -> None:
    bugun = timezone.localdate().isoformat()
    serializer = SchoolConfigSerializer(data=okul_karti_govdesi(student_count_as_of=bugun))
    assert serializer.is_valid(), serializer.errors


@pytest.mark.parametrize("sayi", [0, 99999, "250"])
def test_mevcut_sinirlari_ve_metin_sayi_kabul_edilir(sayi: object) -> None:
    serializer = SchoolConfigSerializer(data=okul_karti_govdesi(student_count=sayi))
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["student_count"] == int(str(sayi))


def test_kademeler_normallestirilir() -> None:
    """Tekrarlar atılır, `SchoolLevel` sırasına dizilir (sessiz normalleştirme)."""
    serializer = SchoolConfigSerializer(
        data={"levels": ["ORTAOKUL", "OKUL_ONCESI", "ORTAOKUL", "ILKOKUL", "ORTAOGRETIM"]}
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["levels"] == [
        "OKUL_ONCESI",
        "ILKOKUL",
        "ORTAOKUL",
        "ORTAOGRETIM",
    ]


# ---------------------------------------------------------------------------
# Ders yılı
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bitis", ["2026-09-01", "2026-06-30"])
def test_ders_yili_bitisi_baslangictan_sonra_olmalidir(client: APIClient, bitis: str) -> None:
    """Aynı gün de reddedilir — sıfır günlük ders yılına dönem kurulamaz."""
    yanit = client.post(
        YIL_URL, {"name": "2026-2027", "start_date": "2026-09-01", "end_date": bitis}, format="json"
    )

    assert yanit.status_code == 400
    assert "başlangıçtan sonra" in str(yanit.json()["fields"]["end_date"])
    assert not SchoolYear.objects.exists()


def test_ders_yili_adi_tekildir_ve_yeni_yil_pasif_acilir(client: APIClient) -> None:
    """Çakışma 500 (IntegrityError) DEĞİL 400'dür. Aktiflik yalnız `activate/` ucundan
    değişir — gövdeyle gönderilen `is_active` yok sayılır (tek-aktif kuralı serviste)."""
    govde = {
        "name": "2026-2027",
        "start_date": "2026-09-01",
        "end_date": "2027-06-30",
        "is_active": True,
    }

    ilk = client.post(YIL_URL, govde, format="json")
    assert ilk.status_code == 201 and ilk.json()["is_active"] is False

    tekrar = client.post(YIL_URL, govde, format="json")
    assert tekrar.status_code == 400
    assert "name" in tekrar.json()["fields"]
    assert SchoolYear.objects.count() == 1


# ---------------------------------------------------------------------------
# İçe aktarma girdisi: dosya YA DA metin
# ---------------------------------------------------------------------------


def _dosya() -> SimpleUploadedFile:
    return SimpleUploadedFile("liste.xlsx", b"icerik", content_type="application/octet-stream")


@pytest.mark.parametrize(
    "govde",
    [
        {},
        {"text": "   \n "},  # yalnız boşluk = metin yok
    ],
)
def test_ice_aktarma_girdisi_bos_olamaz(govde: dict[str, Any]) -> None:
    serializer = ImportRequestSerializer(data=govde)

    assert not serializer.is_valid()
    assert "tam olarak biri" in str(serializer.errors)


def test_ice_aktarma_girdisi_dosya_ve_metni_birlikte_kabul_etmez(client: APIClient) -> None:
    """İkisi birden gelirse hangisinin işleneceği belirsizdir — sessiz tercih yerine ret.

    Ret ayrıştırmadan ÖNCEDİR: geçmişe FAILED/PREVIEWED izi de düşmez.
    """
    yanit = client.post(
        "/api/v1/imports/personnel/preview/",
        {"file": _dosya(), "text": "Adı\tSoyadı\nDENEME\tÖĞRETMEN"},
        format="multipart",
    )

    assert yanit.status_code == 400
    assert yanit.json()["code"] == "validation_error"
    assert "tam olarak biri" in str(yanit.json()["fields"]["non_field_errors"])
    assert not ImportRun.objects.exists()


def test_ice_aktarma_metni_bosluklari_kirpilmadan_tasinir() -> None:
    """Pano metninde baştaki sekme BOŞ HÜCREDİR; kırpılırsa sütunlar bir sola kayar."""
    metin = "\tAdı\tSoyadı\n"

    serializer = ImportRequestSerializer(data={"text": metin})

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["text"] == metin
