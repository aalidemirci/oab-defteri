"""apps.okul.eokul — e-Okul personel ihracının önişlenmesi (dipnot temizliği) ve .xls okuma.

Girdiler SENTETİKTİR: `tests/veri/uret_eokul_ornekleri.py` yerleşimi sıfırdan
kurar, adların hepsi uydurmadır (KVKK — gerçek ihraç depoya girmez).

Sınıf listesi (OOG01001R020) blok düzleştiricisi ve testleri F1b 5. adımda söküldü: öğrenci
aktarımı T5 gereği yoktur, veli listesi okulun şablonundan gelir (`excel_veli`; plan "F1b-5
uygulama kararları"). Sınıf yazımının normalleşmesi `test_excel_veli_parser.py`'dedir.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from apps.okul import eokul
from apps.okul.excel_ortak import ParserError, is_legacy_xls, read_sheet

VERI = Path(__file__).resolve().parent / "veri"
PERSONEL_LISTESI = VERI / "eokul_personel_listesi.xls"


def _matris(yol: Path) -> list[list[Any]]:
    return read_sheet(yol.read_bytes())


class TestXlsOkuma:
    """e-Okul'un "Excel" düğmesi .xlsx değil, Excel 97-2003 (.xls) üretir."""

    def test_xls_kabi_okunur(self) -> None:
        grid = _matris(PERSONEL_LISTESI)
        assert grid, "BIFF (.xls) matrisi boş döndü"
        assert any("Toplam Personel Sayısı" in str(h) for satir in grid for h in satir)

    def test_xls_imzasi_taninir(self) -> None:
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


class TestDuzSablonYolu:
    """e-Okul imzası YOKKEN (şablon/pano) sayısal-satır kuralı uygulanmaz."""

    def test_bozuk_satir_dipnot_sanilmaz(self) -> None:
        """Adı ve sınıfı boş bırakılmış satır, 'rapor dipnotu' diye yutulmamalı.

        Bu yolda böyle bir satır kullanıcının hatasıdır ve satır numarasıyla
        raporlanmalıdır; boşaltılırsa kullanıcı hangi satırı düzelteceğini
        göremez ve kendisine yanlış sebep söylenir.
        """
        grid: list[list[Any]] = [
            ["Adı", "Soyadı", "Görev Türü"],
            ["AYSU", "DEMİR", "Öğretmen"],
            ["", 102, ""],  # dolu hücrelerin tamamı sayı
            ["CEM", "AK", "Öğretmen"],
        ]
        temiz, notlar = eokul.hazirla_personel_matrisi(grid)
        assert notlar == []
        assert temiz == grid  # satır boşaltılmadı: ayrıştırıcı satır no ile raporlar
        assert temiz[2] == ["", 102, ""]

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
        # GÖREVİ sütunu yalnız görev türüne çevrilir; metni satıra girmez (tasarım §8.4).
        turler = {r.last_name: r.member_kind for r in rows}
        assert turler == {
            "YURTSEVEN": "YONETICI",  # Müdür
            "DALGIÇ": "YONETICI",  # Müdür Yardımcısı
            "IŞIKÇI": "OGRETMEN",
            "ÖZGÜNEŞ": "OGRETMEN",  # Sözleşmeli Öğretmen(657 S.K. 4/B)
        }
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
        assert sozlesmeli.member_kind == "OGRETMEN"
        degerler = " ".join(str(v) for r in rows for v in vars(r).values())
        for iz in ("Sözleşmeli", "Müdür", "Tarih", "İngilizce", "KADROLU"):
            assert iz not in degerler, iz
