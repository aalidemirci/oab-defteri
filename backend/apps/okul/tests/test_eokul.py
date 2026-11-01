"""apps.okul.eokul — e-Okul ihraçlarının önişlenmesi (blok düzleştirme, dipnot).

Girdiler SENTETİKTİR: `tests/veri/uret_eokul_ornekleri.py` yerleşimi sıfırdan
kurar, adların hepsi uydurmadır (KVKK — gerçek ihraç depoya girmez). Öğrenci
sınıf listesi örneği (`.xls`) T5 gereği F1a-2'de söküldü; blok düzleştirici F1b'nin
veli listesi ayrıştırıcısına kalacağı için (tasarım §12.B) aynı yerleşim burada
bellekte kurulur (`_sinif_listesi_matrisi`, xlrd'nin döndürdüğü hücre türleriyle).

Yerleşim referansı aile iskeletinde (30.08.2026) iki gerçek raporun incelenmesinden çıkarıldı:
sınıf/şube bilgisi blok BAŞLIĞINDADIR, sütun olarak yoktur.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from apps.okul import eokul
from apps.okul.excel_ogrenci import ParserError, detect_columns, parse_rows, read_sheet

VERI = Path(__file__).resolve().parent / "veri"
PERSONEL_LISTESI = VERI / "eokul_personel_listesi.xls"

_KURUM_BASLIGI = (
    "T.C.\n"
    "ÖRNEK VALİLİĞİ\n"
    "Örnek İlçe / Örnek Anadolu Lisesi Müdürlüğü\n"
    "AL - {sinif}. Sınıf / {sube} Şubesi (ALANI YOK) Sınıf Listesi "
)
# Uydurma adlar — gerçek hiçbir kişiye ait değildir. I ve İ şubeleri bilerek yan yana.
_SUBE_OGRENCILERI: dict[str, list[tuple[int, str, str, str]]] = {
    "I": [
        (13, "ALTAY", "GÖKMEN", "Erkek"),
        (19, "NAZLI SU", "IŞIKÇI", "Kız"),
        (204, "BERKAY", "ÖZDEMİRCİ", "Erkek"),
    ],
    "İ": [
        (7, "ELİF NAZ", "ÇINARLI", "Kız"),
        (88, "TUNAHAN", "ŞAHBAZ", "Erkek"),
        (145, "İREM", "ULUDAĞLI", "Kız"),
    ],
}


def _matris(yol: Path) -> list[list[Any]]:
    return read_sheet(yol.read_bytes())


def _sinif_listesi_matrisi() -> list[list[Any]]:
    """OOG01001R020 yerleşimi (iki şube bloğu: 10/I ve 10/İ), xlrd'nin okuduğu biçimde.

    xlrd sayıları `float`, boş hücreyi `""` döndürür; satırlar en geniş sütuna (15)
    tamamlanır.
    """
    satirlar: list[list[Any]] = []

    def yaz(hucreler: dict[int, Any]) -> None:
        satir: list[Any] = [""] * 15
        for sutun, deger in hucreler.items():
            satir[sutun] = float(deger) if isinstance(deger, int) else deger
        satirlar.append(satir)

    for sube, ogrenciler in _SUBE_OGRENCILERI.items():
        yaz({0: _KURUM_BASLIGI.format(sinif=10, sube=sube)})
        yaz({0: "Sınıf Öğretmeni: ", 7: "Sınıf Başkanı:"})
        yaz({0: "Sınıf Müdür Yrd: KEREM DALGIÇ", 7: "Sınıf Başkan Yrd:"})
        yaz(
            {
                0: "S.No",
                1: "Öğrenci No",
                3: "Adı",
                7: "Soyadı",
                11: "Cinsiyeti",
                13: "Pansiyon Durum",
            }
        )
        for i, (no, ad, soyad, cinsiyet) in enumerate(ogrenciler, start=1):
            yaz({0: i, 1: no, 3: ad, 7: soyad, 11: cinsiyet})
        kiz = sum(1 for o in ogrenciler if o[3] == "Kız")
        yaz(
            {
                0: "Kız Öğrenci Sayısı        :",
                4: kiz,
                5: "Erkek Öğrenci Sayısı    :",
                9: len(ogrenciler) - kiz,
                11: "Toplam Öğrenci Sayısı    :",
                14: len(ogrenciler),
            }
        )
    yaz({11: 46261.0, 12: 0.755370370367018, 14: 1})
    yaz({1: "OOG01001R020"})
    return satirlar


class TestXlsOkuma:
    """e-Okul'un "Excel" düğmesi .xlsx değil, Excel 97-2003 (.xls) üretir."""

    def test_xls_kabi_okunur(self) -> None:
        grid = _matris(PERSONEL_LISTESI)
        assert grid, "BIFF (.xls) matrisi boş döndü"
        assert any("Toplam Personel Sayısı" in str(h) for satir in grid for h in satir)

    def test_xls_imzasi_taninir(self) -> None:
        from apps.okul.excel_ogrenci import is_legacy_xls

        assert is_legacy_xls(PERSONEL_LISTESI.read_bytes())
        assert not is_legacy_xls(b"PK\x03\x04 sahte xlsx")

    def test_bozuk_xls_turkce_hata(self) -> None:
        bozuk = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 512
        with pytest.raises(ParserError, match="Excel 97-2003"):
            read_sheet(bozuk)

    @pytest.mark.parametrize("oran", [0.10, 0.25, 0.50, 0.75, 0.90, 0.99])
    def test_yarim_inmis_dosya_turkce_hata(self, oran: float) -> None:
        """Kesik .xls de ParserError olmalı — 500 DEĞİL.

        xlrd bozuk kapta yalnız XLRDError atmaz: kesme oranına göre
        `struct.error` ya da `IndexError` yükseltir. Bunlar ParserError'a
        çevrilmezse istek 500 ile düşer, kullanıcı Türkçe açıklamayı görmez ve
        İçe Aktarma Geçmişi'ne FAILED izi yazılmaz.
        """
        tam = PERSONEL_LISTESI.read_bytes()
        with pytest.raises(ParserError, match="Excel 97-2003"):
            read_sheet(tam[: int(len(tam) * oran)])

    def test_ortasi_bozulmus_dosya_turkce_hata(self) -> None:
        # Personel örneği küçüktür (5.632 bayt); bozulan bölge çalışma kitabı akışının
        # ortasına denk gelir (silinen sınıf listesi örneğinde 3000. bayttı).
        tam = bytearray(PERSONEL_LISTESI.read_bytes())
        tam[1024:1224] = b"\xff" * 200
        with pytest.raises(ParserError, match="Excel 97-2003"):
            read_sheet(bytes(tam))


class TestBlokBasligi:
    def test_sinif_ve_sube_cozulur(self) -> None:
        baslik = ["AL - 10. Sınıf / A Şubesi (ALANI YOK) Sınıf Listesi "]
        assert eokul.blok_sinifi(baslik) == "10/A"

    def test_cok_satirli_kurum_basligindan_okunur(self) -> None:
        baslik = ["T.C.\nÖRNEK VALİLİĞİ\nÖrnek Lise\nAL - 9. Sınıf / C Şubesi (SAYISAL) Liste"]
        assert eokul.blok_sinifi(baslik) == "9/C"

    def test_noktali_i_subesi_katlanmaz(self) -> None:
        """Blok başlığındaki 'İ' şubesi 'I'ya çökmez (iki ayrı şube)."""
        assert eokul.blok_sinifi(["AL - 10. Sınıf / İ Şubesi (ALANI YOK)"]) == "10/İ"
        assert eokul.blok_sinifi(["AL - 10. Sınıf / I Şubesi (ALANI YOK)"]) == "10/I"

    def test_hazirlik_blogu(self) -> None:
        assert eokul.blok_sinifi(["AL - Hazırlık Sınıfı / B Şubesi Sınıf Listesi"]) == "Hazırlık/B"

    def test_veri_satiri_baslik_degildir(self) -> None:
        assert eokul.blok_sinifi(["1", "13", "", "ALTAY", "", "GÖKMEN"]) is None


class TestDipnot:
    def test_sayac_dipnotu(self) -> None:
        assert eokul.dipnot_mu(["Toplam Öğrenci Sayısı    :", "", 35])
        assert eokul.dipnot_mu(["Toplam Personel Sayısı: 103"])

    def test_rapor_kodu(self) -> None:
        assert eokul.dipnot_mu(["", "OOG01001R020"])

    def test_yalniz_tarih_serisi(self) -> None:
        assert eokul.dipnot_mu(["", "", 46261.0, 0.7553703703])

    def test_veri_satiri_dipnot_degildir(self) -> None:
        assert not eokul.dipnot_mu(["1", 13, "", "ALTAY", "", "GÖKMEN"])

    def test_bos_satir_dipnot_degildir(self) -> None:
        assert not eokul.dipnot_mu(["", "", ""])

    def test_adi_bos_ogrenci_satiri_yutulmaz(self) -> None:
        """Blok içinde yalnız sayı içeren satır dipnot sayılmaz — 'adı boş' diye raporlanır.

        Aksi hâlde adı eksik bir e-Okul satırı sessizce kaybolur; kullanıcı
        eksiği ancak toplam sayıyı elle sayarak fark ederdi.
        """
        grid: list[list[Any]] = [
            ["AL - 10. Sınıf / A Şubesi (ALANI YOK) Sınıf Listesi"],
            ["S.No", "Öğrenci No", "", "Adı", "", "", "", "Soyadı"],
            [1, 13, "", "ALTAY", "", "", "", "GÖKMEN"],
            [2, 27, "", "", "", "", "", ""],  # adı-soyadı boş: yalnız sayılar
            ["Toplam Öğrenci Sayısı    :", "", "", "", 2],
        ]
        duz, _ = eokul.duzlestir_sinif_listesi(grid)
        rows = parse_rows(duz, detect_columns(duz, scan_limit=30), valid_levels=(10,))
        assert [r.student_number for r in rows] == ["13", "27"]
        assert rows[1].raw_student_name == ""


class TestSinifListesiDuzlestirme:
    def test_bicim_taninir(self) -> None:
        assert eokul.sinif_listesi_mi(_sinif_listesi_matrisi())

    def test_duz_sablon_bicimi_taninmaz(self) -> None:
        duz = [["Sınıf", "Okul No", "Adı Soyadı"], ["10/A", "101", "ALİ VELİ"]]
        assert not eokul.sinif_listesi_mi(duz)

    def test_satir_sayisi_korunur(self) -> None:
        """Gürültü satırları SİLİNMEZ, boşaltılır — uyarılardaki satır no'su kaymasın."""
        ham = _sinif_listesi_matrisi()
        duz, _ = eokul.duzlestir_sinif_listesi(ham)
        assert len(duz) == len(ham)

    def test_sinif_sutunu_eklenir_ve_ayristirilir(self) -> None:
        ham = _sinif_listesi_matrisi()
        duz, notlar = eokul.duzlestir_sinif_listesi(ham)
        assert notlar and "2 şube bloğu" in notlar[0]

        mapping = detect_columns(duz, scan_limit=30)
        assert mapping.is_usable
        assert "class" in mapping.fields and mapping.fields["class"] == 0

        rows = parse_rows(duz, mapping, valid_levels=(9, 10, 11, 12))
        assert len(rows) == 6  # iki blok × üç öğrenci
        assert {r.student_number for r in rows} == {"13", "19", "204", "7", "88", "145"}

    def test_iki_sube_ayri_kalir(self) -> None:
        """KORUMA TESTİ: 10/I ve 10/İ blokları tek şubeye çökmez."""
        duz, _ = eokul.duzlestir_sinif_listesi(_sinif_listesi_matrisi())
        rows = parse_rows(duz, detect_columns(duz, scan_limit=30), valid_levels=(10,))
        subeler = {r.class_section for r in rows}
        assert subeler == {"I", "İ"}
        assert len([r for r in rows if r.class_section == "I"]) == 3
        assert len([r for r in rows if r.class_section == "İ"]) == 3

    def test_dipnot_ve_ogretmen_satirlari_veri_olmaz(self) -> None:
        """Sayaç dipnotu, sınıf öğretmeni ve rapor kodu satırları öğrenci sayılmaz."""
        duz, _ = eokul.duzlestir_sinif_listesi(_sinif_listesi_matrisi())
        rows = parse_rows(duz, detect_columns(duz, scan_limit=30), valid_levels=(9, 10, 11, 12))
        adlar = {r.raw_student_name for r in rows}
        assert not any("Öğrenci Sayısı" in ad for ad in adlar)
        assert not any("Sınıf Müdür" in ad for ad in adlar)
        assert all(r.student_number.isdigit() for r in rows)

    def test_ad_ve_soyad_ayri_sutunlardan_gelir(self) -> None:
        duz, _ = eokul.duzlestir_sinif_listesi(_sinif_listesi_matrisi())
        rows = parse_rows(duz, detect_columns(duz, scan_limit=30), valid_levels=(10,))
        kayit = next(r for r in rows if r.student_number == "19")
        assert (kayit.student_first, kayit.student_last) == ("NAZLI SU", "IŞIKÇI")

    def test_veri_cikmayan_varyantta_ham_matris_korunur(self) -> None:
        """Blok başlığı var ama tanınan sütun başlığı yoksa matris değiştirilmez."""
        garip = [["AL - 10. Sınıf / A Şubesi Sınıf Listesi"], ["bilinmeyen", "yerleşim"]]
        duz, notlar = eokul.duzlestir_sinif_listesi(garip)
        assert duz == garip and notlar == []


class TestBlokBasligiCozulemezse:
    """Bir bloğun başlığı tanınmazsa: KOMŞU ŞUBEYE YAZMA, SESSİZCE DÜŞÜRME."""

    #: İkinci bloğun başlığı bilerek tanınmaz biçimde ("Şubesi" kelimesi yok).
    KARISIK: list[list[Any]] = [
        ["AL - 10. Sınıf / A Şubesi (ALANI YOK) Sınıf Listesi"],
        ["S.No", "Öğrenci No", "", "Adı", "", "", "", "Soyadı"],
        [1, 13, "", "ALTAY", "", "", "", "GÖKMEN"],
        ["Toplam Öğrenci Sayısı    :", "", "", "", 1],
        ["AL - 10. Sınıf - B kolu (tanınmayan başlık)"],
        ["S.No", "Öğrenci No", "", "Adı", "", "", "", "Soyadı"],
        [1, 55, "", "TUNAHAN", "", "", "", "ŞAHBAZ"],
        ["Toplam Öğrenci Sayısı    :", "", "", "", 1],
    ]

    def test_onceki_subenin_sinifi_devralinmaz(self) -> None:
        duz, notlar = eokul.duzlestir_sinif_listesi(self.KARISIK)
        rows = parse_rows(duz, detect_columns(duz, scan_limit=30), valid_levels=(10,))
        cozulen = {r.student_number: r.class_section for r in rows}
        assert cozulen["13"] == "A"
        assert cozulen["55"] == "", "tanınmayan bloğun öğrencisi 10/A'ya yazılmış"
        assert any("çözülemedi" in n for n in notlar)

    def test_satir_kaybolmaz_ve_raporlanir(self) -> None:
        """Sınıfı çözülemeyen satır düşürülmez; satır numarasıyla raporlanır."""
        duz, _ = eokul.duzlestir_sinif_listesi(self.KARISIK)
        rows = parse_rows(duz, detect_columns(duz, scan_limit=30), valid_levels=(10,))
        assert len(rows) == 2
        kayip = next(r for r in rows if r.student_number == "55")
        assert kayip.class_level is None  # servis katmanı bunu "atlandı" diye yazar
        assert kayip.row_number == 7  # Excel'deki gerçek satır numarası


class TestDuzSablonYolu:
    """e-Okul imzası YOKKEN (şablon/pano) sayısal-satır kuralı uygulanmaz."""

    def test_bozuk_satir_dipnot_sanilmaz(self) -> None:
        """Adı ve sınıfı boş bırakılmış satır, 'rapor dipnotu' diye yutulmamalı.

        Bu yolda böyle bir satır kullanıcının hatasıdır ve satır numarasıyla
        raporlanmalıdır; boşaltılırsa kullanıcı hangi satırı düzelteceğini
        göremez ve kendisine yanlış sebep söylenir.
        """
        grid: list[list[Any]] = [
            ["Sınıf/Şube", "Okul No", "Adı Soyadı"],
            ["10/A", 101, "AYSU DEMİR"],
            ["", 102, ""],  # dolu hücrelerin tamamı sayı
            ["10/A", 103, "CEM AK"],
        ]
        temiz, notlar = eokul.hazirla_ogrenci_matrisi(grid)
        assert notlar == []
        rows = parse_rows(temiz, detect_columns(temiz), valid_levels=(10,))
        assert [r.student_number for r in rows] == ["101", "102", "103"]
        assert rows[1].class_level is None  # "Sınıf/şube çözülemedi" diye raporlanır

    def test_eokul_imzasi_varsa_tarih_satiri_yine_temizlenir(self) -> None:
        grid: list[list[Any]] = [
            ["ADI SOYADI", "GÖREVİ"],
            ["SELMA YURTSEVEN", "Müdür"],
            ["Toplam Personel Sayısı: 1"],
            ["", "", 46260.0, 0.898055],
        ]
        temiz, notlar = eokul.hazirla_personel_matrisi(grid)
        assert temiz[2] == [] and temiz[3] == []
        assert notlar and "2 satır atlandı" in notlar[0]


class TestPersonelListesi:
    def test_dipnot_temizlenir_satir_sayisi_korunur(self) -> None:
        ham = _matris(PERSONEL_LISTESI)
        temiz, notlar = eokul.temizle_rapor_dipnotlari(ham)
        assert len(temiz) == len(ham)
        assert notlar and "2 satır atlandı" in notlar[0]

    def test_personel_satirlari_ayristirilir(self) -> None:
        from apps.okul.excel_personel import detect_columns as personel_sutunlari
        from apps.okul.excel_personel import parse_rows as personel_satirlari

        temiz, _ = eokul.hazirla_personel_matrisi(_matris(PERSONEL_LISTESI))
        mapping = personel_sutunlari(temiz)
        assert mapping.is_usable
        rows = personel_satirlari(temiz, mapping)
        assert len(rows) == 4  # dipnot ve tarih satırı personel sayılmadı
        assert {r.last_name for r in rows} == {"YURTSEVEN", "DALGIÇ", "IŞIKÇI", "ÖZGÜNEŞ"}
        # GÖREVİ sütunu yalnız üye türüne çevrilir; metni satıra girmez (tasarım §8.4).
        assert {r.member_kind for r in rows} == {"TEACHER"}
        assert not any(r.member_kind_unrecognized for r in rows)

    def test_gorev_metni_ve_brans_satira_girmez(self) -> None:
        """e-Okul GÖREVİ ve BRANŞI sütunları satır nesnesinde iz bırakmaz."""
        from apps.okul.excel_personel import detect_columns as personel_sutunlari
        from apps.okul.excel_personel import parse_rows as personel_satirlari

        temiz, _ = eokul.hazirla_personel_matrisi(_matris(PERSONEL_LISTESI))
        mapping = personel_sutunlari(temiz)
        assert set(mapping.fields) == {"full_name", "role"}  # BRANŞI eşlenmez
        rows = personel_satirlari(temiz, mapping)
        sozlesmeli = next(r for r in rows if r.last_name == "ÖZGÜNEŞ")
        assert sozlesmeli.member_kind == "TEACHER"
        degerler = " ".join(str(v) for r in rows for v in vars(r).values())
        for iz in ("Sözleşmeli", "Müdür", "Tarih", "İngilizce", "KADROLU"):
            assert iz not in degerler, iz
