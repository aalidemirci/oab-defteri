"""Kurulum sihirbazı uçları + kurulum durumu + Başlangıç Yol Haritası (plan §2.2).

`setup/status/` alan kümesi hem arayüz kurulum kapısının hem masaüstü sağlık
denetiminin sözleşmesidir — küme değişirse FE `SetupStatus` tipi ve
`desktop/server.py` birlikte gözden geçirilir.

Kural (tasarım §4.4.5; sihirbaz adımları plan §2.2): sihirbaz parola adımı olmadan
ilerlemez ve `setup/complete/` eksik adımda Türkçe 400 (`kurulum_eksik`) ile
HANGİ adımın eksik olduğunu söyler — her dal ayrı testtedir.

Bu dosyada kurtarma anahtarı DOĞRULANMIŞ başlanır (`anahtar_dogrulanmis`,
otomatik): 1. adımın ikinci koşulu (tasarım §4.4.4 `kurtarma.dogrulandi`) ve damgasız kurulumun
reddi `test_kurtarma_dogrulama.py`'dedir. Damga test verisi olarak doğrudan dosyaya yazılır:
servisi (`confirm_recovery_key`) `KURTARMA` iz satırı yazar, veritabanı ve hesap ister.

Hesap kurulmadan (`parolasiz`) servisler yazamaz (iz anahtarı yok; tasarım §4.6.3): o
testlerde okul bilgileri ve ders yılı test verisi olarak ORM ile yazılır
(`_aktif_yil_dogrudan`), kapının kendisi uçtan sınanır.

Okul kartı (F1b 4. adım; tasarım §5.1, plan F1b-4 kararları): eksiksiz uydurma kart
`okul_karti_ortak`'tadır. Serileştiricinin ileti tablosu `test_serializers.py`'dedir; burada
uçtan akışlar (boşaltma reddi, kısmi PUT, kademe normalleştirmesi, kaldırılan alanlar),
eksik alanların sırası ve kurulum kapısı, yol haritasının `okul_karti` maddesi sınanır.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul.models import (
    Holiday,
    HolidayKind,
    Personnel,
    SchoolConfig,
    SchoolTerm,
    SchoolYear,
)
from apps.okul.oturum import OTURUM
from apps.okul.serializers import (
    DEMIRBAS_ONAYI_ZORUNLU,
    IL_ZORUNLU,
    ILCE_ZORUNLU,
    KADEME_ZORUNLU,
    KANTIN_ZORUNLU,
    KURUM_KODU_ZORUNLU,
    MEVCUT_TARIHI_ZORUNLU,
    MEVCUT_ZORUNLU,
    OKUL_ADI_ZORUNLU,
    PERSONEL_ZORUNLU,
    YERLESIM_ZORUNLU,
)
from apps.okul.services import app_password
from apps.okul.services import school_year as school_year_service
from apps.okul.services import setup as setup_service
from apps.okul.services import terms as term_service
from apps.okul.tests.okul_karti_ortak import (
    okul_karti,
    okul_karti_govdesi,
    okul_kartini_dogrudan_yaz,
)
from apps.okul.tests.oturum_ortak import SahteSaat, kurulum_durumunu_yaz, oturum_saatini_kur
from conftest import TEST_HESAP_ID, TEST_PAROLA

DURUM_ALANLARI = {
    "setup_completed",
    "password_set",
    "recovery_key_confirmed",
    "school_name",
    "school_info_complete",
    "has_active_school_year",
    "active_school_year",
    "missing_steps",
    "personnel_count",
    "school_break_count",
    "roadmap",
}

URL = "/api/v1/setup/school-config/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def anahtar_dogrulanmis(guvenlik_ortami: Path) -> None:
    """Varsayılan ortamın kurtarma anahtarı saklandı olarak damgalanır (modül başlığı)."""
    yol = app_password.state_path()
    durum = json.loads(yol.read_text(encoding="utf-8"))
    durum["kurtarma"][app_password.RECOVERY_CONFIRMED_FIELD] = "2026-11-01T10:00:00+03:00"
    yol.write_text(json.dumps(durum, ensure_ascii=False, indent=2), encoding="utf-8")


def _okul_bilgileri(**degisiklik: Any) -> None:
    setup_service.update_school_config(fields=okul_karti(**degisiklik))


def _aktif_yil(*, donemler: bool = True) -> int:
    yil = school_year_service.create_school_year(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), activate=True
    )
    if donemler:
        term_service.configure_terms(
            yil, first_end=date(2027, 1, 22), second_start=date(2027, 2, 8)
        )
    return yil.pk


def _aktif_yil_dogrudan() -> None:
    """Hesapsız ortamda aktif yıl ve iki dönem (test verisi; servisler iz ister)."""
    yil = SchoolYear.objects.create(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), is_active=True
    )
    SchoolTerm.objects.create(
        school_year=yil, sequence=1, start_date=yil.start_date, end_date=date(2027, 1, 22)
    )
    SchoolTerm.objects.create(
        school_year=yil, sequence=2, start_date=date(2027, 2, 8), end_date=yil.end_date
    )


def _tamamla(client: APIClient) -> Any:
    return client.post("/api/v1/setup/complete/")


@pytest.mark.django_db
class TestSetupStatus:
    def test_alan_kumesi_ve_bos_kurulum(self, client: APIClient) -> None:
        yanit = client.get("/api/v1/setup/status/")
        assert yanit.status_code == 200
        veri = yanit.json()
        assert set(veri.keys()) == DURUM_ALANLARI
        assert veri["setup_completed"] is False
        # Varsayılan test ortamı: parola kurulu (anahtar doğrulanmış); okul ve takvim eksik.
        assert veri["password_set"] is True
        assert veri["recovery_key_confirmed"] is True
        assert veri["missing_steps"] == ["school", "calendar"]
        assert veri["active_school_year"] is None
        assert veri["school_break_count"] == 0
        assert veri["roadmap"] == {"marks": {}, "hidden": False}

    def test_parolasizken_ilk_eksik_adim_parola(self, client: APIClient, parolasiz: Path) -> None:
        veri = client.get("/api/v1/setup/status/").json()
        assert veri["password_set"] is False
        assert veri["recovery_key_confirmed"] is False
        assert veri["missing_steps"] == ["password", "school", "calendar"]

    def test_kurulum_sonrasi_sayimlar_ve_aktif_yil(self, client: APIClient) -> None:
        _okul_bilgileri()
        yil_id = _aktif_yil()
        assert _tamamla(client).status_code == 200

        veri = client.get("/api/v1/setup/status/").json()
        assert veri["setup_completed"] is True
        assert veri["school_name"] == "Örnek Anadolu Lisesi"
        assert veri["school_info_complete"] is True
        assert veri["has_active_school_year"] is True
        assert veri["missing_steps"] == []
        assert veri["active_school_year"] == {
            "id": yil_id,
            "name": "2026-2027",
            "start_date": "2026-09-07",
            "end_date": "2027-06-25",
            "terms_ready": True,
        }

    def test_ogrenciye_kapali_gun_sayisi_aktif_yil_araligiyla_ve_turuyle_sinirli(
        self, client: APIClient
    ) -> None:
        _aktif_yil()
        Holiday.objects.create(
            name="Yarıyıl",
            start_date=date(2027, 1, 25),
            end_date=date(2027, 2, 5),
            kind=HolidayKind.SCHOOL_BREAK,
        )
        # Yıl başlamadan önceki ara tatil ve resmî tatil sayılmaz.
        Holiday.objects.create(
            name="Eski ara tatil",
            start_date=date(2026, 4, 13),
            end_date=date(2026, 4, 17),
            kind=HolidayKind.SCHOOL_BREAK,
        )
        Holiday.objects.create(
            name="Cumhuriyet Bayramı",
            start_date=date(2026, 10, 29),
            end_date=date(2026, 10, 29),
            kind=HolidayKind.OFFICIAL,
        )
        assert client.get("/api/v1/setup/status/").json()["school_break_count"] == 1

    def test_durum_kisisel_veri_icermez(self, client: APIClient) -> None:
        """Sağlık denetimi ucu da olduğu için yanıtta kişi adı geçmez; yalnız sayı."""
        Personnel.objects.create(first_name="ZEYNEP", last_name="KARADUMAN")
        metin = client.get("/api/v1/setup/status/").content.decode("utf-8")
        for parca in ("ZEYNEP", "KARADUMAN"):
            assert parca not in metin
        assert client.get("/api/v1/setup/status/").json()["personnel_count"] == 1

    def test_ogrenci_ve_sube_sayilari_durumda_yoktur(self, client: APIClient) -> None:
        """Öğrenci sicili ve şube kataloğu söküldü (F1b 5. adım); öğrenci mevcudu okul kartındadır."""
        veri = client.get("/api/v1/setup/status/").json()
        assert not {"student_count", "class_section_count"} & set(veri)


@pytest.mark.django_db
class TestSetupComplete:
    """`setup/complete/` kapısı — eksik her adım ayrı dal (kod kapısı maddesi)."""

    def test_uc_adim_tamamsa_tamamlar(self, client: APIClient) -> None:
        _okul_bilgileri()
        _aktif_yil()
        yanit = _tamamla(client)
        assert yanit.status_code == 200
        assert yanit.json() == {"setup_completed": True}
        assert SchoolConfig.load().setup_completed is True

    def test_parola_adimi_olmadan_tamamlanmaz(self, client: APIClient, parolasiz: Path) -> None:
        # Hesap kurulmadan servis yazamaz (iz anahtarı yok; tasarım §4.6.3): okul bilgileri
        # ve ders yılı test verisi olarak doğrudan yazılır, kapının kendisi uçtan sınanır.
        okul_kartini_dogrudan_yaz()
        _aktif_yil_dogrudan()
        yanit = _tamamla(client)
        assert yanit.status_code == 400
        govde = yanit.json()
        assert govde["code"] == "kurulum_eksik"
        assert "1. adım (program yöneticisi hesabı)" in govde["message"]
        assert "2. adım" not in govde["message"] and "3. adım" not in govde["message"]
        assert SchoolConfig.load().setup_completed is False

    @pytest.mark.parametrize(
        ("degisiklik", "beklenen"),
        [
            ({"school_name": ""}, "okul adı"),
            ({"province": " "}, "il"),
            ({"district": ""}, "ilçe"),
            ({"institution_code": ""}, "kurum kodu"),
            ({"institution_code": "12a456"}, "kurum kodu"),
            ({"levels": []}, "kademe"),
            ({"levels": ["UNIVERSITE"]}, "kademe"),
            ({"levels": "ORTAOKUL"}, "kademe"),
            ({"student_count": None, "student_count_as_of": None}, "öğrenci mevcudu"),
            ({"settlement_type": ""}, "yerleşim türü"),
            ({"canteen_mode": ""}, "kantin işletme biçimi"),
            ({"staffing_mode": ""}, "personel çalıştırma biçimi"),
            ({"demirbas_onayi": False}, "“Bu bilgisayar okul demirbaşıdır” onayı"),
        ],
        ids=[
            "okul_adi",
            "il",
            "ilce",
            "kurum_kodu_bos",
            "kurum_kodu_harfli",
            "kademe_bos",
            "kademe_gecersiz",
            "kademe_liste_degil",
            "mevcut",
            "yerlesim",
            "kantin",
            "personel",
            "demirbas_onayi",
        ],
    )
    def test_okul_bilgisi_eksikse_hangi_alan_oldugunu_soyler(
        self, client: APIClient, degisiklik: dict[str, Any], beklenen: str
    ) -> None:
        _okul_bilgileri(**degisiklik)
        _aktif_yil()
        yanit = _tamamla(client)
        assert yanit.status_code == 400
        mesaj = yanit.json()["message"]
        assert "2. adım (okul bilgileri)" in mesaj
        assert f"{beklenen} eksik." in mesaj
        assert SchoolConfig.load().setup_completed is False

    def test_kurulum_suresince_bosta_kilit_yok_tamamlaninca_sayac_sifirdan_baslar(
        self, client: APIClient
    ) -> None:
        """Tasarım §13 D15: sihirbazda geçen süre oturumu kilitlemez; bitince tam süre."""
        saat = SahteSaat()
        oturum_saatini_kur(saat)
        assert OTURUM.durum() == "acik"
        _okul_bilgileri()
        _aktif_yil()
        saat.ilerlet(45 * 60)  # sihirbazda 45 dk (boşta süreden uzun)
        assert OTURUM.durum() == "acik"
        saat.ilerlet(9 * 60)

        assert _tamamla(client).status_code == 200

        ozet = OTURUM.ozet()
        assert ozet["durum"] == "acik"
        assert ozet["kurulum_tamam"] is True
        assert ozet["bosta_kalan_sn"] == 10 * 60
        saat.ilerlet(10 * 60)
        assert OTURUM.durum() == "kilitli"

    def test_demirbas_no_istege_baglidir(self, client: APIClient) -> None:
        _okul_bilgileri(demirbas_no="")
        _aktif_yil()
        assert _tamamla(client).status_code == 200

    def test_mudur_kampus_ve_acilis_tarihi_istege_baglidir(self, client: APIClient) -> None:
        _okul_bilgileri(principal_name="", in_campus=False, opened_on=None)
        _aktif_yil()
        assert _tamamla(client).status_code == 200

    def test_eksik_alanlar_kullanici_diliyle_sirasiyla_listelenir(self) -> None:
        """Boş okul kartında 2. adımın bütün zorunlu alanları, sözleşmedeki sırayla."""
        assert setup_service.missing_school_fields(SchoolConfig.load()) == [
            "okul adı",
            "il",
            "ilçe",
            "kurum kodu",
            "kademe",
            "öğrenci mevcudu",
            "yerleşim türü",
            "kantin işletme biçimi",
            "personel çalıştırma biçimi",
            "“Bu bilgisayar okul demirbaşıdır” onayı",
        ]

    def test_eksik_alanlar_ret_iletisinde_sirasiyla_gecer(self, client: APIClient) -> None:
        _okul_bilgileri(institution_code="", canteen_mode="")
        _aktif_yil()
        mesaj = _tamamla(client).json()["message"]
        assert "2. adım (okul bilgileri): kurum kodu, kantin işletme biçimi eksik." in mesaj

    def test_eksiksiz_kartta_eksik_alan_yoktur(self) -> None:
        _okul_bilgileri()
        assert setup_service.missing_school_fields(SchoolConfig.load()) == []

    def test_onceden_tamamlanmis_kurulumda_kapi_yeniden_kapanmaz(self, client: APIClient) -> None:
        """Okul kartının OAB alanlarından önce tamamlanmış kurulum: alanlar boştur, kapı açık
        kalır; eksik `school_info_complete` ve yol haritasının `okul_karti` maddesinden
        görünür (plan F1b-4 kararları)."""
        setup_service.update_school_config(fields={"school_name": "Örnek Ortaokulu"})
        kurulum_durumunu_yaz(tamam=True)
        veri = client.get("/api/v1/setup/status/").json()
        assert veri["setup_completed"] is True
        assert veri["school_info_complete"] is False
        assert "school" in veri["missing_steps"]
        assert setup_service.roadmap_auto_items(veri)["okul_karti"] is False

    def test_aktif_ders_yili_yoksa_reddeder(self, client: APIClient) -> None:
        _okul_bilgileri()
        yanit = _tamamla(client)
        assert yanit.status_code == 400
        assert "3. adım (ders yılı)" in yanit.json()["message"]

    def test_donemleri_tanimlanmamis_aktif_yil_yetmez(self, client: APIClient) -> None:
        _okul_bilgileri()
        _aktif_yil(donemler=False)
        veri = client.get("/api/v1/setup/status/").json()
        assert veri["active_school_year"]["terms_ready"] is False
        assert veri["missing_steps"] == ["calendar"]
        yanit = _tamamla(client)
        assert yanit.status_code == 400
        assert "iki dönemin tarihleri" in yanit.json()["message"]

    def test_birden_cok_eksik_adim_sirayla_listelenir(
        self, client: APIClient, parolasiz: Path
    ) -> None:
        mesaj = _tamamla(client).json()["message"]
        assert mesaj.startswith("Kurulum tamamlanamadı. ")
        assert mesaj.index("1. adım") < mesaj.index("2. adım") < mesaj.index("3. adım")
        # İç kodlar kullanıcı metnine girmez (sözlük §2).
        for kod in ("password", "calendar", "F1", "E14"):
            assert kod not in mesaj


@pytest.mark.django_db
class TestSchoolConfigApi:
    def test_okul_karti_yazilir_ve_okunur(self, client: APIClient) -> None:
        yanit = client.put(URL, okul_karti_govdesi(), format="json")
        assert yanit.status_code == 200, yanit.json()
        veri = client.get(URL).json()
        assert veri == {
            "school_name": "Örnek Anadolu Lisesi",
            "province": "Örnek İl",
            "district": "Örnek İlçe",
            "principal_name": "",
            "institution_code": "999001",
            "levels": ["ORTAOGRETIM"],
            "student_count": 1234,
            "student_count_as_of": "2026-10-01",
            "settlement_type": "BUYUKSEHIR",
            "canteen_mode": "KIRAYA_VERILIYOR",
            "staffing_mode": "HIZMET_ALIMI",
            "in_campus": False,
            "opened_on": None,
            "demirbas_onayi": True,
            "demirbas_no": "BLG-2026-017",
            "data_controller_text": "",
            "setup_completed": False,
        }
        assert setup_service.missing_school_fields(SchoolConfig.load()) == []

    def test_istege_bagli_alanlar_yazilir(self, client: APIClient) -> None:
        govde = okul_karti_govdesi(
            principal_name="Örnek Müdür", in_campus=True, opened_on="2026-09-01"
        )
        assert client.put(URL, govde, format="json").status_code == 200
        config = SchoolConfig.load()
        assert config.principal_name == "Örnek Müdür"
        assert config.in_campus is True
        assert config.opened_on == date(2026, 9, 1)

    def test_kismi_put_diger_alanlari_silmez(self, client: APIClient) -> None:
        client.put(URL, okul_karti_govdesi(), format="json")
        client.put(URL, {"demirbas_no": "YENİ-1"}, format="json")
        config = SchoolConfig.load()
        assert config.levels == ["ORTAOGRETIM"]
        assert (config.student_count, config.student_count_as_of) == (1234, date(2026, 10, 1))
        assert config.demirbas_onayi is True
        assert config.demirbas_no == "YENİ-1"
        assert setup_service.missing_school_fields(config) == []

    def test_kismi_put_yalniz_gonderilen_alani_degistirir(self, client: APIClient) -> None:
        client.put(URL, okul_karti_govdesi(), format="json")
        yanit = client.put(URL, {"canteen_mode": "BIRLIKCE_ISLETILIYOR"}, format="json")
        assert yanit.status_code == 200
        config = SchoolConfig.load()
        assert config.canteen_mode == "BIRLIKCE_ISLETILIYOR"
        assert config.settlement_type == "BUYUKSEHIR"
        assert config.institution_code == "999001"

    @pytest.mark.parametrize(
        ("alan", "bos_deger", "ileti"),
        [
            ("school_name", "  ", OKUL_ADI_ZORUNLU),
            ("province", "", IL_ZORUNLU),
            ("district", " ", ILCE_ZORUNLU),
            ("institution_code", "", KURUM_KODU_ZORUNLU),
            ("levels", [], KADEME_ZORUNLU),
            ("student_count", None, MEVCUT_ZORUNLU),
            ("student_count_as_of", None, MEVCUT_TARIHI_ZORUNLU),
            ("settlement_type", "", YERLESIM_ZORUNLU),
            ("canteen_mode", "", KANTIN_ZORUNLU),
            ("staffing_mode", "", PERSONEL_ZORUNLU),
            ("demirbas_onayi", False, DEMIRBAS_ONAYI_ZORUNLU),
        ],
    )
    def test_zorunlu_alan_gonderilirse_bosaltilamaz(
        self, client: APIClient, alan: str, bos_deger: object, ileti: str
    ) -> None:
        """KORUMA: kurulum bittikten sonra Okul Bilgileri'nden zorunlu alan geri alınamaz.

        Kısmi PUT gönderilmeyen alana dokunmaz; ama gönderilen zorunlu alan boş
        olamaz — aksi hâlde "tamamlanmış ama okul adımı eksik" kurulum doğar.
        """
        client.put(URL, okul_karti_govdesi(), format="json")

        yanit = client.put(URL, okul_karti_govdesi(**{alan: bos_deger}), format="json")

        assert yanit.status_code == 400
        assert yanit.json()["fields"][alan] == [ileti]
        assert setup_service.missing_school_fields(SchoolConfig.load()) == []

    def test_acilis_tarihi_bosaltilabilir(self, client: APIClient) -> None:
        client.put(URL, okul_karti_govdesi(opened_on="2026-09-01"), format="json")
        yanit = client.put(URL, {"opened_on": None}, format="json")
        assert yanit.status_code == 200
        assert yanit.json()["opened_on"] is None
        assert SchoolConfig.load().opened_on is None

    def test_veri_sorumlusu_yazilir_kirpilir_ve_bosaltilabilir(self, client: APIClient) -> None:
        """Veri sorumlusu isteğe bağlı serbest metindir (F1b 5. adım; E04, KVKK md. 10/1-a)."""
        metin = "Örnek Anadolu Lisesi Müdürlüğü, Örnek Mah. Örnek Sok. No: 1, Örnek İlçe"
        client.put(URL, okul_karti_govdesi(), format="json")
        yanit = client.put(URL, {"data_controller_text": f"  {metin} "}, format="json")
        assert yanit.status_code == 200, yanit.json()
        assert yanit.json()["data_controller_text"] == metin
        assert SchoolConfig.load().data_controller_text == metin
        # Kurulumun zorunlu alanı değildir: boşaltılır, eksik alan sayılmaz.
        yanit = client.put(URL, {"data_controller_text": ""}, format="json")
        assert yanit.status_code == 200
        assert SchoolConfig.load().data_controller_text == ""
        assert setup_service.missing_school_fields(SchoolConfig.load()) == []

    def test_veri_sorumlusu_ust_siniri(self, client: APIClient) -> None:
        yanit = client.put(URL, {"data_controller_text": "x" * 501}, format="json")
        assert yanit.status_code == 400
        assert yanit.json()["fields"]["data_controller_text"] == [
            "Veri sorumlusu en çok 500 karakter olabilir."
        ]
        assert (
            client.put(URL, {"data_controller_text": "x" * 500}, format="json").status_code == 200
        )

    def test_veri_sorumlusu_izde_yalniz_adiyla_gorunur(self, client: APIClient) -> None:
        """Serbest metin: denetim izine değeri girmez, alan adı ve içerik MAC'i girer."""
        from apps.okul import denetim_izi
        from apps.okul.models import AuditTrail

        client.put(URL, {"data_controller_text": "Uydurma Veri Sorumlusu"}, format="json")
        satir = AuditTrail.objects.filter(model="okul.SchoolConfig").order_by("-seq").first()
        assert satir is not None
        assert "data_controller_text" in satir.changed_fields
        assert "data_controller_text" not in satir.values
        assert "Uydurma Veri Sorumlusu" not in json.dumps(satir.values, ensure_ascii=False)
        assert denetim_izi.kaydi_dogrula(SchoolConfig, SchoolConfig.SINGLETON_PK) is True

    def test_kademeler_tekrarsiz_ve_kanonik_sirayla_saklanir(self, client: APIClient) -> None:
        yanit = client.put(
            URL,
            {"levels": ["ORTAOGRETIM", "ILKOKUL", "ORTAOGRETIM", "OKUL_ONCESI"]},
            format="json",
        )
        assert yanit.status_code == 200
        beklenen = ["OKUL_ONCESI", "ILKOKUL", "ORTAOGRETIM"]
        assert yanit.json()["levels"] == beklenen
        assert SchoolConfig.load().levels == beklenen

    def test_mevcut_ve_tarihi_birlikte_yazilir(self, client: APIClient) -> None:
        bugun = timezone.localdate()
        yanit = client.put(
            URL, {"student_count": 0, "student_count_as_of": bugun.isoformat()}, format="json"
        )
        assert yanit.status_code == 200, yanit.json()
        config = SchoolConfig.load()
        assert (config.student_count, config.student_count_as_of) == (0, bugun)

    def test_metin_alanlari_kirpilarak_kaydedilir(self, client: APIClient) -> None:
        yanit = client.put(
            URL,
            {
                "school_name": "  Örnek Okul  ",
                "district": " Örnek İlçe ",
                "principal_name": " Örnek Müdür ",
                "institution_code": " 999001 ",
                "demirbas_no": " BLG-1 ",
            },
            format="json",
        )
        assert yanit.status_code == 200, yanit.json()
        config = SchoolConfig.load()
        assert config.school_name == "Örnek Okul"
        assert config.district == "Örnek İlçe"
        assert config.principal_name == "Örnek Müdür"
        assert config.institution_code == "999001"
        assert config.demirbas_no == "BLG-1"

    def test_kaldirilan_alanlar_yok_sayilir(self, client: APIClient) -> None:
        """Eski ön yüzün gönderebileceği `has_prep_class`, `kademe`, `kisa_ad` yazılmaz."""
        yanit = client.put(
            URL,
            {"school_name": "Örnek Okul", "has_prep_class": True, "kademe": "X", "kisa_ad": "Y"},
            format="json",
        )
        assert yanit.status_code == 200
        assert not {"has_prep_class", "kademe", "kisa_ad"} & set(yanit.json())
        config = SchoolConfig.load()
        assert config.school_name == "Örnek Okul"
        assert not hasattr(config, "has_prep_class")

    def test_setup_completed_put_ile_degistirilemez(self, client: APIClient) -> None:
        """Kapı alanı yalnız `setup/complete/` ucuyla açılır (read-only)."""
        client.put(URL, {"school_name": "X", "setup_completed": True}, format="json")
        assert SchoolConfig.load().setup_completed is False

    def test_yol_haritasi_school_config_uzerinden_yazilamaz(self, client: APIClient) -> None:
        client.put(
            URL,
            {"yol_haritasi": {"isaretler": {"kurtarma_zarfi": "2026-09-22"}}},
            format="json",
        )
        assert SchoolConfig.load().yol_haritasi == {}


#: Kendiliğinden tespit edilen maddeleri tamamlayan `setup_status` alanları (test verisi).
_DOLU_SAYIMLAR: dict[str, Any] = {
    "school_info_complete": True,
    "personnel_count": 2,
    "school_break_count": 1,
}


@pytest.mark.django_db
@pytest.mark.usefixtures("yonetici_hesabi")  # kurtarma anahtarı yenilemesi hesap satırı ister
class TestYolHaritasi:
    """Başlangıç Yol Haritası — kullanıcı işaretleri `SchoolConfig.yol_haritasi`'nda."""

    def _isaretle(self, client: APIClient, madde: str, done: bool = True) -> Any:
        return client.post("/api/v1/setup/roadmap/", {"item": madde, "done": done}, format="json")

    def test_madde_isaretlenir_ve_durumda_gorunur(self, client: APIClient) -> None:
        yanit = self._isaretle(client, "kurtarma_zarfi")
        assert yanit.status_code == 200
        bugun = timezone.localdate().isoformat()
        assert yanit.json() == {"marks": {"kurtarma_zarfi": bugun}, "hidden": False}
        durum = client.get("/api/v1/setup/status/").json()
        assert durum["roadmap"]["marks"] == {"kurtarma_zarfi": bugun}

    def test_isaret_kaldirilir(self, client: APIClient) -> None:
        self._isaretle(client, "kurtarma_zarfi")
        yanit = self._isaretle(client, "kurtarma_zarfi", done=False)
        assert yanit.json()["marks"] == {}

    def test_elle_isaretlenen_madde_yalniz_kurtarma_zarfidir(self) -> None:
        """Parola paylaşımı maddesi yoktur: parola paylaşılmaz (T1; BSG Yön. md. 7/2)."""
        assert setup_service.ROADMAP_MANUAL_ITEMS == ("kurtarma_zarfi",)

    def test_kaldirilan_parola_paylasimi_maddesi_isaretlenemez(self, client: APIClient) -> None:
        yanit = self._isaretle(client, "parola_paylasimi")
        assert yanit.status_code == 400
        assert yanit.json()["message"] == "Bu madde elle işaretlenemez."
        assert SchoolConfig.load().yol_haritasi == {}

    def test_eski_parola_paylasimi_isareti_zararsizca_yok_sayilir(self, client: APIClient) -> None:
        """Aile iskeletinden kalma kayıtlı işaret okunmaz, ilk yazmada kayıttan düşer."""
        config, _ = SchoolConfig.objects.get_or_create(pk=SchoolConfig.SINGLETON_PK)
        config.yol_haritasi = {
            "isaretler": {"kurtarma_zarfi": "2026-09-22", "parola_paylasimi": "2026-09-22"},
            "gizli": False,
        }
        config.save()

        durum = client.get("/api/v1/setup/status/")
        assert durum.status_code == 200
        assert durum.json()["roadmap"] == {
            "marks": {"kurtarma_zarfi": "2026-09-22"},
            "hidden": False,
        }

        yanit = self._isaretle(client, "kurtarma_zarfi", done=False)
        assert yanit.status_code == 200
        assert yanit.json()["marks"] == {}
        assert SchoolConfig.load().yol_haritasi == {"isaretler": {}, "gizli": False}

    def test_kendiliginden_tespit_edilen_madde_elle_isaretlenemez(self, client: APIClient) -> None:
        yanit = self._isaretle(client, "personel_aktarimi")
        assert yanit.status_code == 400
        assert yanit.json()["message"] == "Bu madde elle işaretlenemez."

    def test_kaldirilan_ogrenci_aktarimi_maddesi_isaretlenemez(self, client: APIClient) -> None:
        yanit = self._isaretle(client, "ogrenci_aktarimi")
        assert yanit.status_code == 400
        assert yanit.json()["message"] == "Bu madde elle işaretlenemez."

    def test_govde_madde_ya_da_gizleme_olmali(self, client: APIClient) -> None:
        for govde in ({}, {"item": "kurtarma_zarfi"}, {"hidden": True, "item": "x", "done": True}):
            yanit = client.post("/api/v1/setup/roadmap/", govde, format="json")
            assert yanit.status_code == 400, govde

    def test_kendiliginden_tespit_edilen_maddeler(self) -> None:
        """`okul_karti` ilk maddedir (plan F1b-4 kararları); öğrenci aktarımı maddesi F1b 5.
        adımda öğrenci tarafıyla kalktı, veli listesi dönemlik olduğu için madde olmaz."""
        assert setup_service.roadmap_auto_items(
            {
                "school_info_complete": False,
                "personnel_count": 0,
                "school_break_count": 0,
            }
        ) == {
            "okul_karti": False,
            "personel_aktarimi": False,
            "kapali_gunler": False,
        }
        assert all(setup_service.roadmap_auto_items(_DOLU_SAYIMLAR).values())
        assert next(iter(setup_service.roadmap_auto_items(_DOLU_SAYIMLAR))) == "okul_karti"

    def test_okul_karti_maddesi_kartin_eksiksizligini_izler(self, client: APIClient) -> None:
        durum = client.get("/api/v1/setup/status/").json()
        assert setup_service.roadmap_auto_items(durum)["okul_karti"] is False
        _okul_bilgileri()
        durum = client.get("/api/v1/setup/status/").json()
        assert setup_service.roadmap_auto_items(durum)["okul_karti"] is True

    def test_okul_karti_eksikken_gizlenemez(
        self, client: APIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Öteki bütün maddeler tamam, okul kartı eksik: kart gizlenemez (kurulumu önceden
        tamamlanmış kurulumda yeni alanlar boştur; plan F1b-4 kararları)."""
        for madde in setup_service.ROADMAP_MANUAL_ITEMS:
            self._isaretle(client, madde)
        gercek = setup_service.setup_status

        def okul_karti_eksik() -> dict[str, Any]:
            return {**gercek(), **_DOLU_SAYIMLAR, "school_info_complete": False}

        monkeypatch.setattr(setup_service, "setup_status", okul_karti_eksik)
        yanit = client.post("/api/v1/setup/roadmap/", {"hidden": True}, format="json")
        assert yanit.status_code == 400
        assert "bütün maddeler tamamlanınca" in yanit.json()["message"]
        assert SchoolConfig.load().yol_haritasi.get("gizli") is not True

    def test_onceden_gizlenmis_kart_okul_karti_eksikken_yeniden_gorunur(
        self, client: APIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """KORUMA (bağımsız denetim, F1b-4): önceden tamamlanmış ve kartı gizlemiş bir kurulumda
        okul kartının OAB alanları boş olabilir. Kurulum
        kapısı yeniden kapanmadığı için eksiği gösteren tek yer karttır: kart görünür, saklanan
        gizleme tercihi silinmez, alanlar dolunca kart yine gizlenir."""
        gercek = setup_service.setup_status
        self._hepsi_tamam(client, monkeypatch)
        assert (
            client.post("/api/v1/setup/roadmap/", {"hidden": True}, format="json").json()["hidden"]
            is True
        )
        # Bundan sonra gerçek durum özeti (sayımlar kartın görünürlüğüne girmez).
        monkeypatch.setattr(setup_service, "setup_status", gercek)
        okul_kartini_dogrudan_yaz(levels=[], institution_code="")  # göçten sonraki boş hâl

        durum = client.get("/api/v1/setup/status/").json()
        assert durum["school_info_complete"] is False
        assert durum["roadmap"]["hidden"] is False
        assert SchoolConfig.load().yol_haritasi["gizli"] is True  # tercih duruyor

        _okul_bilgileri()
        assert client.get("/api/v1/setup/status/").json()["roadmap"]["hidden"] is True

    def test_eksik_madde_varken_gizlenemez(self, client: APIClient) -> None:
        for madde in setup_service.ROADMAP_MANUAL_ITEMS:
            self._isaretle(client, madde)
        # Öğrenci/personel aktarılmadı, öğrenciye kapalı gün yok.
        yanit = client.post("/api/v1/setup/roadmap/", {"hidden": True}, format="json")
        assert yanit.status_code == 400
        assert "bütün maddeler tamamlanınca" in yanit.json()["message"]
        assert SchoolConfig.load().yol_haritasi.get("gizli") is not True

    def test_butun_maddeler_tamamken_gizlenir_isaret_kalkinca_yeniden_gorunur(
        self, client: APIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _okul_bilgileri()
        for madde in setup_service.ROADMAP_MANUAL_ITEMS:
            self._isaretle(client, madde)
        gercek = setup_service.setup_status

        def dolu_durum() -> dict[str, Any]:
            return {**gercek(), **_DOLU_SAYIMLAR}

        monkeypatch.setattr(setup_service, "setup_status", dolu_durum)
        yanit = client.post("/api/v1/setup/roadmap/", {"hidden": True}, format="json")
        assert yanit.status_code == 200, yanit.json()
        assert yanit.json()["hidden"] is True

        yanit = self._isaretle(client, "kurtarma_zarfi", done=False)
        assert yanit.json()["hidden"] is False

    def _hepsi_tamam(self, client: APIClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Yol haritasının bütün maddelerini tamamlar (gizlemenin ön koşulu); okul kartı gerçekten
        doldurulur, çünkü kartın görünürlüğünü `roadmap_state` ondan okur."""
        _okul_bilgileri()
        for madde in setup_service.ROADMAP_MANUAL_ITEMS:
            self._isaretle(client, madde)
        gercek = setup_service.setup_status

        def dolu_durum() -> dict[str, Any]:
            return {**gercek(), **_DOLU_SAYIMLAR}

        monkeypatch.setattr(setup_service, "setup_status", dolu_durum)

    def test_kurtarma_anahtari_damgasizken_kart_gizli_kalmaz(
        self, client: APIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """KORUMA: "kurtarma anahtarı doğrulanmadı" uyarısı kartın İÇİNDEDİR.

        Kart gizliyken uyarı da basılmazdı ve kartı geri getirecek bir arayüz
        yolu yoktur (işaret kutuları ve gizleme düğmesi kartın içinde). Damgasız
        kurulumda kart görünür kalır; SAKLANAN gizleme tercihi silinmez.
        """
        self._hepsi_tamam(client, monkeypatch)
        assert (
            client.post("/api/v1/setup/roadmap/", {"hidden": True}, format="json").json()["hidden"]
            is True
        )

        yeni_anahtar = app_password.renew_recovery_key(
            hesap_id=TEST_HESAP_ID, password=TEST_PAROLA
        )  # damga silinir

        durum = client.get("/api/v1/setup/status/").json()
        assert durum["recovery_key_confirmed"] is False
        assert durum["roadmap"]["hidden"] is False
        assert SchoolConfig.load().yol_haritasi["gizli"] is True  # tercih duruyor

        app_password.confirm_recovery_key(yeni_anahtar)
        assert client.get("/api/v1/setup/status/").json()["roadmap"]["hidden"] is True

    def test_kurtarma_anahtari_damgasizken_gizlenemez(
        self, client: APIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._hepsi_tamam(client, monkeypatch)
        app_password.renew_recovery_key(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

        yanit = client.post("/api/v1/setup/roadmap/", {"hidden": True}, format="json")

        assert yanit.status_code == 400
        assert "doğrulanmadan" in yanit.json()["message"]
        assert SchoolConfig.load().yol_haritasi.get("gizli") is not True

    def test_damgasizken_isaretleme_saklanan_gizleme_tercihini_silmez(
        self, client: APIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Yazma yolu SAKLANAN durumu okur: kapı tercihi sessizce sıfırlamaz."""
        self._hepsi_tamam(client, monkeypatch)
        client.post("/api/v1/setup/roadmap/", {"hidden": True}, format="json")
        yeni_anahtar = app_password.renew_recovery_key(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

        yanit = self._isaretle(client, "kurtarma_zarfi")

        assert yanit.json()["hidden"] is False  # arayüz: kart görünür
        assert SchoolConfig.load().yol_haritasi["gizli"] is True  # saklanan: gizli
        app_password.confirm_recovery_key(yeni_anahtar)
        assert client.get("/api/v1/setup/status/").json()["roadmap"]["hidden"] is True

    def test_bozuk_ya_da_bilinmeyen_kayit_disari_sizmaz(self) -> None:
        _okul_bilgileri()  # okul kartı eksikken kart zaten gizli kalamaz (ayrı test)
        config, _ = SchoolConfig.objects.get_or_create(pk=SchoolConfig.SINGLETON_PK)
        config.yol_haritasi = {
            "isaretler": {"kurtarma_zarfi": "2026-09-22", "bilinmeyen": "x"},
            "gizli": "evet",
        }
        config.save()
        assert setup_service.roadmap_state(SchoolConfig.load()) == {
            "marks": {"kurtarma_zarfi": "2026-09-22"},
            "hidden": True,
        }
        # Bilinen maddenin bozuk değeri (tarih dizesi değil) de okunmaz.
        config.yol_haritasi = {"isaretler": {"kurtarma_zarfi": 5}}
        config.save()
        assert setup_service.roadmap_state(SchoolConfig.load()) == {"marks": {}, "hidden": False}
        config.yol_haritasi = ["liste"]
        config.save()
        assert setup_service.roadmap_state(SchoolConfig.load()) == {"marks": {}, "hidden": False}


@pytest.mark.django_db
class TestSchoolYearTerms:
    def test_donem_yapilandirma(self, client: APIClient) -> None:
        yil = client.post(
            "/api/v1/school-years/",
            {"name": "2026-2027", "start_date": "2026-09-01", "end_date": "2027-06-30"},
            format="json",
        ).json()
        yanit = client.put(
            f"/api/v1/school-years/{yil['id']}/terms/",
            {"first_term_end": "2027-01-16", "second_term_start": "2027-02-01"},
            format="json",
        )
        assert yanit.status_code == 200
        donemler = yanit.json()
        assert [d["sequence"] for d in donemler] == [1, 2]
        assert donemler[0]["start_date"] == "2026-09-01"
        assert donemler[1]["end_date"] == "2027-06-30"

    def test_ters_donem_tarihleri_reddedilir(self, client: APIClient) -> None:
        yil = client.post(
            "/api/v1/school-years/",
            {"name": "2026-2027", "start_date": "2026-09-01", "end_date": "2027-06-30"},
            format="json",
        ).json()
        yanit = client.put(
            f"/api/v1/school-years/{yil['id']}/terms/",
            {"first_term_end": "2027-02-01", "second_term_start": "2027-01-16"},
            format="json",
        )
        assert yanit.status_code == 400


def test_spa_catchall_arayuz_derlenmemisken_503_ve_turkce_yonerge() -> None:
    """SPA catch-all, dist yokken beyaz ekran yerine Türkçe yönerge döndürür."""
    yanit = APIClient().get("/olmayan-bir-rota")
    assert yanit.status_code in (200, 503)  # dist derlenmişse 200, temiz depoda 503
    if yanit.status_code == 503:
        assert "Arayüz derlenmemiş".encode() in yanit.content


@pytest.mark.django_db
def test_update_school_config_whitelist_disi_alan_yazmaz() -> None:
    parmak_izi = SchoolConfig.load().app_password_hash  # varsayılan ortamın parmak izi
    setup_service.update_school_config(
        fields={
            "school_name": "X",
            "app_password_hash": "hack",
            "setup_completed": True,
            "has_prep_class": True,  # F1b 5. adımda düştü
        }
    )
    config = SchoolConfig.load()
    assert config.app_password_hash == parmak_izi != "hack"
    assert config.setup_completed is False
    assert not hasattr(config, "has_prep_class")


@pytest.mark.django_db
def test_letterhead_identity_bos_okul_adi_yer_tutucuya_duser() -> None:
    assert setup_service.get_letterhead_identity()["school_name"] == "Okul"
