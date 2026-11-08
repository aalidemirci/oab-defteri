"""Veli listesi ayrıştırıcısı (`excel_veli`) — DB'siz (T5; tasarım §8.1 A3, §8.4).

Kapsam: iki alanlı beyaz liste (öğrencinin adı, numarası, T.C. kimlik no, telefon ve adres
sütunları hiç okunmaz), başlıkların birebir eşlenmesi, sınıf yazımının normalleşmesi, satır
sorunlarının değersiz bildirilmesi. Adların hepsi UYDURMADIR.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from apps.okul import excel_veli
from apps.okul.excel_ortak import ParserError, read_sheet
from apps.okul.models import PARENT_NAME_MAX, STUDENT_CLASS_MAX
from apps.okul.services.templates import PARENT_TEMPLATE_HEADERS


def _satirlar(grid: list[list[Any]]) -> tuple[list[excel_veli.ParsedParentRow], list[Any]]:
    _, satirlar, sorunlar = excel_veli.parse_grid(grid)
    return satirlar, sorunlar


class TestSinifMetni:
    @pytest.mark.parametrize(
        ("girdi", "beklenen"),
        [
            ("9-A", "9-A"),
            ("9/A", "9-A"),
            ("9 a", "9-A"),
            ("10A", "10-A"),
            (" 12 - C ", "12-C"),
            ("10. Sınıf / B Şubesi", "10-B"),
            ("11. SINIF C ŞUBESİ", "11-C"),
            ("10/i", "10-İ"),  # Türkçe büyük harf: I ve İ iki ayrı şubedir
            ("10/I", "10-I"),
            ("Hazırlık/A", "Hazırlık-A"),
            ("HZ B", "Hazırlık-B"),
            (9.0, None),  # şubesiz sayı sınıf değildir
        ],
    )
    def test_yazim_normallesir(self, girdi: Any, beklenen: str | None) -> None:
        assert excel_veli.sinif_metni(girdi) == beklenen

    @pytest.mark.parametrize("girdi", ["", None, "A", "13-A", "0-A", "0/B", "9-ABCDE"])
    def test_taninmayan_yazim_none(self, girdi: Any) -> None:
        assert excel_veli.sinif_metni(girdi) is None

    @pytest.mark.parametrize(
        ("girdi", "beklenen"),
        [
            ("Anasınıfı A", "Anasınıfı-A"),
            ("Ana Sınıfı-A", "Anasınıfı-A"),
            ("anasınıfı/a", "Anasınıfı-A"),
            ("ANASINIFI B", "Anasınıfı-B"),
            ("Anasınıfı", "Anasınıfı"),  # şubesiz grup
            ("5 yaş A", "5 Yaş-A"),
            ("5 Yaş-A", "5 Yaş-A"),
            ("5 YAŞ / A", "5 Yaş-A"),
            ("5yaş a", "5 Yaş-A"),
            ("5 Yaş Grubu A Şubesi", "5 Yaş-A"),
            ("4 yaş B", "4 Yaş-B"),
            ("3 yaş C", "3 Yaş-C"),
            ("6 Yaş", "6 Yaş"),  # şubesiz grup
            ("Anasınıfı 5 Yaş A", "5 Yaş-A"),  # yaş esastır
            ("5 yaş i", "5 Yaş-İ"),  # Türkçe büyük harf
        ],
    )
    def test_okul_oncesi_gruplari_ayri_tutulur(self, girdi: str, beklenen: str) -> None:
        assert excel_veli.sinif_metni(girdi) == beklenen

    @pytest.mark.parametrize(
        "girdi",
        [
            "2 yaş A",  # yaş 3-6 dışında
            "7 yaş A",
            "Yaş A",  # önünde yaş yok
            "5YAŞA",  # yaş sözcüğü ayrılmamış
            "Anasınıfı 1",  # yaşın dışında rakam
            "5 yaş 2",
            "Anasınıfı A B",  # iki şube
            "5 yaş ABCDE",  # şube dört harften uzun
            "Hazırlık 5 yaş A",
        ],
    )
    def test_cozulmeyen_okul_oncesi_satir_sorunudur(self, girdi: str) -> None:
        assert excel_veli.sinif_metni(girdi) is None

    def test_yas_yazimi_ilkokul_seviyesine_dusmez(self) -> None:
        """Eski kusur: "5 yaş A" 5. sınıfın "YAŞ" şubesi ("5-YAŞ") sayılıyordu; A ve B şubeleri
        aynı uydurma sınıfta birleşiyordu. İlkokulun 5-A'sı etkilenmez."""
        assert excel_veli.sinif_metni("5 yaş A") != excel_veli.sinif_metni("5 yaş B")
        for girdi in ("5 yaş A", "4 yaş B", "7 yaş A", "2 yaş A"):
            sonuc = excel_veli.sinif_metni(girdi)
            assert sonuc is None or "Yaş" in sonuc
            assert sonuc not in {"5-YAŞ", "4-YAŞ", "7-YAŞ", "2-YAŞ"}
        assert excel_veli.sinif_metni("5-A") == "5-A"
        assert excel_veli.sinif_metni("5/A") == "5-A"
        assert excel_veli.sinif_metni("5 A") == "5-A"
        assert excel_veli.sinif_metni("5-A") != excel_veli.sinif_metni("5 yaş A")

    def test_saklanan_yazim_alana_sigar(self) -> None:
        assert len("Hazırlık-ABCD") <= STUDENT_CLASS_MAX
        assert excel_veli.sinif_metni("Hazırlık ABCD") == "Hazırlık-ABCD"
        assert len("Anasınıfı-ABCD") <= STUDENT_CLASS_MAX
        assert excel_veli.sinif_metni("Anasınıfı ABCD") == "Anasınıfı-ABCD"

    def test_sira_hazirlik_seviye_ve_turk_alfabesi(self) -> None:
        siniflar = ["10-B", "9-Ç", "Hazırlık-A", "9-C", "12-A", "10-A", "9-D"]
        assert sorted(siniflar, key=excel_veli.sinif_sira_anahtari) == [
            "Hazırlık-A",
            "9-C",
            "9-Ç",
            "9-D",
            "10-A",
            "10-B",
            "12-A",
        ]

    def test_sira_okul_oncesi_basta(self) -> None:
        siniflar = [
            "1-A",
            "Anasınıfı-B",
            "5-A",
            "5 Yaş-B",
            "Hazırlık-A",
            "Anasınıfı",
            "4 Yaş-A",
            "5 Yaş-A",
            "Anasınıfı-A",
            "3 Yaş",
            "6 Yaş-A",
        ]
        assert sorted(siniflar, key=excel_veli.sinif_sira_anahtari) == [
            "3 Yaş",
            "4 Yaş-A",
            "5 Yaş-A",
            "5 Yaş-B",
            "6 Yaş-A",
            "Anasınıfı",
            "Anasınıfı-A",
            "Anasınıfı-B",
            "Hazırlık-A",
            "1-A",
            "5-A",
        ]


class TestBasliklar:
    def test_sablon_basliklari_taninir(self) -> None:
        mapping = excel_veli.detect_columns([list(PARENT_TEMPLATE_HEADERS)])
        assert mapping.is_usable
        assert set(mapping.fields) == {"full_name", "student_class"}

    def test_ad_ve_soyad_ayri_sutunlardan_okunur(self) -> None:
        satirlar, sorunlar = _satirlar(
            [["Velinin Adı", "Velinin Soyadı", "Sınıfı"], ["ÖRNEK", "VELİ", "9-A"]]
        )
        assert sorunlar == []
        assert [(s.full_name, s.student_class) for s in satirlar] == [("ÖRNEK VELİ", "9-A")]

    def test_baslik_ilk_satirlarda_aranir(self) -> None:
        grid: list[list[Any]] = [
            ["Örnek Ortaokulu Veli Listesi"],
            [],
            ["Velinin Adı Soyadı", "Öğrencinin Sınıfı"],
            ["DENEME VELİ", "7/B"],
        ]
        satirlar, _ = _satirlar(grid)
        assert [(s.row_number, s.student_class) for s in satirlar] == [(4, "7-B")]

    def test_baslik_birebir_eslenir(self) -> None:
        """'Sınıf Öğretmeni' sınıf sütunu, 'Veli Telefonu' ad sütunu sayılmaz (A3)."""
        with pytest.raises(ParserError) as hata:
            excel_veli.parse_grid([["Veli Telefonu", "Sınıf Öğretmeni"], ["x", "y"]])
        assert str(hata.value) == excel_veli.SUTUN_EKSIK

    @pytest.mark.parametrize(
        "basliklar",
        [["Velinin Adı Soyadı"], ["Öğrencinin Sınıfı"], ["Adı Soyadı", "Sınıfı"]],
        ids=["sinifsiz", "adsiz", "ogrenci_adi_veli_sayilmaz"],
    )
    def test_zorunlu_sutun_eksikse_durur(self, basliklar: list[str]) -> None:
        with pytest.raises(ParserError, match="Velinin Adı Soyadı"):
            excel_veli.parse_grid([basliklar, ["DENEME", "9-A"]])


class TestBeyazListe:
    """Tasarım §8.4: öğrencinin adı ve numarası, T.C. kimlik no, telefon, adres, yakınlık,
    e-posta okunmaz — yalnız iki alan (veli adı-soyadı ve öğrencinin sınıfı)."""

    GRID: list[list[Any]] = [
        [
            "Öğrencinin Adı Soyadı",
            "Okul No",
            "Velinin Adı Soyadı",
            "Yakınlığı",
            "T.C. Kimlik No",
            "Veli Telefonu",
            "Adres",
            "E-posta",
            "Öğrencinin Sınıfı",
        ],
        [
            "UYDURMA ÖĞRENCİ",
            "4711",
            "UYDURMA VELİ",
            "Anne",
            "12345678900",
            "05329876543",
            "Hayal Mahallesi",
            "uydurma@ornek.invalid",
            "8/C",
        ],
    ]

    def test_yalniz_iki_alan_eslenir(self) -> None:
        mapping = excel_veli.detect_columns(self.GRID)
        assert set(mapping.fields) == {"full_name", "student_class"}
        assert mapping.fields["full_name"] == 2
        assert mapping.fields["student_class"] == 8

    def test_satir_nesnesi_yalniz_iki_alan_tasir(self) -> None:
        satirlar, sorunlar = _satirlar(self.GRID)
        assert sorunlar == []
        assert len(satirlar) == 1
        satir = satirlar[0]
        assert set(vars(satir)) == {"row_number", "full_name", "student_class"}
        degerler = " ".join(str(v) for v in vars(satir).values())
        for iz in ("ÖĞRENCİ", "4711", "Anne", "12345678900", "0532", "Hayal", "@"):
            assert iz not in degerler, iz


class TestSatirSorunlari:
    def test_bos_satir_atlanir_sorunlu_satir_nedeniyle_bildirilir(self) -> None:
        grid: list[list[Any]] = [
            list(PARENT_TEMPLATE_HEADERS),
            ["ÖRNEK VELİ", "9-A"],
            ["", ""],
            ["", "9-A"],
            ["DENEME VELİ", ""],
            ["UYDURMA VELİ", "Sınıf Öğretmeni"],
            ["X" * (PARENT_NAME_MAX + 1), "9-B"],
        ]
        satirlar, sorunlar = _satirlar(grid)
        assert [s.row_number for s in satirlar] == [2]
        assert [(s.row_number, s.field, s.issue) for s in sorunlar] == [
            (4, "full_name", excel_veli.VELI_ADI_BOS),
            (5, "student_class", excel_veli.SINIF_BOS),
            (6, "student_class", excel_veli.SINIF_TANINMADI),
            (7, "full_name", excel_veli.VELI_ADI_UZUN),
        ]

    def test_sorun_hucre_degerini_tasimaz(self) -> None:
        _, sorunlar = _satirlar([list(PARENT_TEMPLATE_HEADERS), ["GİZLİ UYDURMA", "garip sınıf"]])
        assert len(sorunlar) == 1
        assert set(vars(sorunlar[0])) == {"row_number", "field", "issue"}
        assert "GİZLİ" not in sorunlar[0].issue and "garip" not in sorunlar[0].issue

    def test_ad_bosluklari_teklesir(self) -> None:
        satirlar, _ = _satirlar([list(PARENT_TEMPLATE_HEADERS), ["  ÖRNEK   VELİ ", "9-A"]])
        assert satirlar[0].full_name == "ÖRNEK VELİ"

    def test_iki_cocuklu_veli_iki_satirdir(self) -> None:
        """Bir satır bir öğrencidir: aynı ad iki satır olarak kalır (birleştirme yok)."""
        grid: list[list[Any]] = [
            list(PARENT_TEMPLATE_HEADERS),
            ["ÖRNEK VELİ", "9-A"],
            ["ÖRNEK VELİ", "6-B"],
        ]
        satirlar, _ = _satirlar(grid)
        assert [(s.full_name, s.student_class) for s in satirlar] == [
            ("ÖRNEK VELİ", "9-A"),
            ("ÖRNEK VELİ", "6-B"),
        ]


def test_ad_siniri_modeldekiyle_aynidir() -> None:
    assert excel_veli.AD_EN_COK == PARENT_NAME_MAX


def test_sentetik_veli_listesi_ornegi_okunur() -> None:
    """Okulun doldurduğu liste biçiminde sentetik örnek (`tests/veri`; uydurma adlar): başlık
    üçüncü satırdadır, aradaki öğrenci adı, okul no ve veli telefonu sütunları okunmaz, sınıf
    yazımları normalleşir, sınıfı boş satır numarasıyla bildirilir."""
    yol = Path(__file__).resolve().parent / "veri" / "veli_listesi_ornegi.xlsx"
    grid = read_sheet(yol.read_bytes())
    mapping, satirlar, sorunlar = excel_veli.parse_grid(grid)

    assert set(mapping.fields) == {"full_name", "student_class"}
    assert [(s.row_number, s.full_name, s.student_class) for s in satirlar] == [
        (4, "SEVİM ÖRNEKSOY", "9-A"),
        (5, "HAKAN UYDURMA", "9-A"),
        (6, "HAKAN UYDURMA", "10-B"),
        (7, "IŞIL DENEMECİ", "Hazırlık-A"),
    ]
    assert [(s.row_number, s.field) for s in sorunlar] == [(8, "student_class")]
    degerler = " ".join(str(v) for s in satirlar for v in vars(s).values())
    for iz in ("ÇAĞAN", "İPEK", "4711", "0000"):
        assert iz not in degerler, iz
