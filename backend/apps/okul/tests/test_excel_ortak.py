"""`apps.okul.excel_ortak` — Türkçe başlık katlama, başlık bulma, hücre yardımcıları.

Öğrenci ayrıştırıcısı (`excel_ogrenci`) F1b 5. adımda söküldü; onun türden bağımsız sınamaları
(başlık ilk satırlarda aranır, yinelenen eşleşme uyarı düşürür, zorunlu alan olmadan kullanılamaz,
Excel sayı biçimi temizlenir) ortak yardımcıya taşındı. Veli listesi ayrıştırıcısı başlığını bu
yolla bulacaktır (tasarım §8.4). Okuma (`read_sheet`) sınamaları `test_eokul.py`'dedir.

Saf testlerdir (DB'siz).
"""

from __future__ import annotations

from typing import Any

from apps.okul.excel_ortak import (
    YINELENEN_BASLIK_ILETISI,
    basligi_bul,
    basliklari_esle,
    bos_satir,
    hucre,
    hucre_metni,
    normalize_header,
)

#: Uydurma bir eşleme sözlüğü (veli listesi şablonuna benzer; sıra kritik: 'sinif sube' önce).
ESANLAMLILAR: dict[str, list[str]] = {
    "sinif": ["sinif sube", "sinif", "sube"],
    "ad": ["veli adi soyadi", "adi soyadi", "ad soyad"],
}
#: Alanların kullanıcıya görünen adları (yinelenen başlık uyarısı).
ALAN_ADLARI: dict[str, str] = {"sinif": "Öğrencinin sınıfı", "ad": "Velinin adı-soyadı"}


def _ad_var(fields: dict[str, int]) -> bool:
    return "ad" in fields


def _grid(*rows: list[Any]) -> list[list[Any]]:
    return [list(r) for r in rows]


class TestNormalizeHeader:
    def test_turkce_harfler_asciiye_katlanir(self) -> None:
        assert normalize_header("Adı Soyadı") == "adi soyadi"
        assert normalize_header("ŞUBE/SINIF") == "sube sinif"
        assert normalize_header("İçerik Ğğ Üü Öö Çç") == "icerik gg uu oo cc"

    def test_sapkali_harfler_duz_harfe_katlanir(self) -> None:
        """Düzeltme işareti adı ayırmaz: "Hâle" ≡ "Hale", "Kâzım" ≡ "Kazım" (ad eşleşmesi)."""
        assert normalize_header("Hâle Âşık Kâzım") == "hale asik kazim"
        assert normalize_header("Îlke Rûhi ÛMRAN") == "ilke ruhi umran"
        assert normalize_header("Hâle Yılmaz") == normalize_header("Hale Yılmaz") == "hale yilmaz"

    def test_ayrisik_yazim_birlesik_yazimla_ayni_anahtari_verir(self) -> None:
        """NFC: a + U+0302 (â) ve I + U+0307 (İ) tek harf gibi katlanır."""
        assert normalize_header("Hâle") == "hale"
        assert normalize_header("İLKAY") == normalize_header("İLKAY") == "ilkay"

    def test_bos_ve_metin_olmayan(self) -> None:
        assert normalize_header(None) == ""
        assert normalize_header("  -- ") == ""
        assert normalize_header(12.0) == "12 0"


class TestBaslikBulma:
    def test_esanlamli_basliklar_eslesir(self) -> None:
        bulunan = basligi_bul(
            _grid(["Sınıf/Şube", "Veli Adı Soyadı"]),
            ESANLAMLILAR,
            kullanilir_mi=_ad_var,
            alan_adlari=ALAN_ADLARI,
        )
        assert (bulunan.header_row, bulunan.fields) == (0, {"sinif": 0, "ad": 1})
        assert bulunan.matched_headers == {"sinif": "Sınıf/Şube", "ad": "Veli Adı Soyadı"}

    def test_baslik_ilk_satirlarda_aranir(self) -> None:
        grid = _grid(
            ["", ""],
            ["ÖRNEK OKUL LİSTESİ", ""],
            ["Sınıf", "Adı Soyadı"],
            ["9/A", "ÖRNEK KİŞİ"],
        )
        assert (
            basligi_bul(
                grid, ESANLAMLILAR, kullanilir_mi=_ad_var, alan_adlari=ALAN_ADLARI
            ).header_row
            == 2
        )

    def test_tarama_penceresi_disindaki_baslik_bulunmaz(self) -> None:
        grid = _grid(*([["not"]] * 12), ["Sınıf", "Adı Soyadı"])
        bulunan = basligi_bul(grid, ESANLAMLILAR, kullanilir_mi=_ad_var, alan_adlari=ALAN_ADLARI)
        assert bulunan.fields == {}
        assert (
            basligi_bul(
                grid, ESANLAMLILAR, kullanilir_mi=_ad_var, alan_adlari=ALAN_ADLARI, scan_limit=13
            ).header_row
            == 12
        )

    def test_kullanilabilir_satir_daha_cok_alan_eslesenden_once_gelir(self) -> None:
        """Zorunlu alanı olan satır kazanır; yalnız sınıf eşleyen üst satır başlık sayılmaz."""
        grid = _grid(["Sınıf", "Şube"], ["Sınıf", "Adı Soyadı"])
        bulunan = basligi_bul(grid, ESANLAMLILAR, kullanilir_mi=_ad_var, alan_adlari=ALAN_ADLARI)
        assert (bulunan.header_row, bulunan.fields) == (1, {"sinif": 0, "ad": 1})

    def test_zorunlu_alan_yoksa_en_iyi_eslesme_doner(self) -> None:
        bulunan = basligi_bul(
            _grid(["Sınıf", "Okul No"]),
            ESANLAMLILAR,
            kullanilir_mi=_ad_var,
            alan_adlari=ALAN_ADLARI,
        )
        assert bulunan.fields == {"sinif": 0}
        assert not _ad_var(bulunan.fields)

    def test_yinelenen_eslesme_uyari_duser_ilki_kullanilir(self) -> None:
        fields, matched, uyarilar = basliklari_esle(
            ["Sınıf", "Şube", "Ad Soyad"], ESANLAMLILAR, alan_adlari=ALAN_ADLARI
        )
        assert fields == {"sinif": 0, "ad": 2}
        assert matched["sinif"] == "Sınıf"
        # Uyarı alanı Türkçe adıyla anar; iç alan anahtarı ("sinif") kullanıcıya sızmaz.
        assert uyarilar == [
            "“Şube” sütunu da “Öğrencinin sınıfı” alanına uyuyor; ilk uyan sütun kullanıldı, "
            "bu sütun okunmadı."
        ]
        assert uyarilar[0] == YINELENEN_BASLIK_ILETISI.format(
            sutun="Şube", alan="Öğrencinin sınıfı"
        )


class TestHucreYardimcilari:
    def test_hucre_metni_excel_sayisini_temizler(self) -> None:
        assert hucre_metni(2612.0) == "2612"
        assert hucre_metni("  9/A ") == "9/A"
        assert hucre_metni(None) == ""
        assert hucre_metni("1.05") == "1.05"

    def test_hucre_eksik_sutunda_bos(self) -> None:
        assert hucre(["a", "b"], 1) == "b"
        assert hucre(["a"], 3) is None
        assert hucre(["a"], None) is None

    def test_bos_satir(self) -> None:
        assert bos_satir([None, "", "  "])
        assert not bos_satir([None, "x"])
