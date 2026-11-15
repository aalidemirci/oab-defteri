"""Evrakın Excel çizicisi — openpyxl'in evrak YAZIM kapısı (plan F2 §4.2, 8. adım; tasarım §9.5).

`shared/docx.py`'nin eşidir: belgenin İÇERİĞİ burada kurulmaz, içerik `shared/evrak.py`'deki modelden
gelir (`evrak.xlsx_ciz` blokları sırasıyla buraya verir); bu modül yalnız düzeni çizer. Excel çıktısı
E08 katılım cetvelinin ve E14 yıllık iş takviminin biçimidir (tasarım §9.5); dosya deposunda
saklanmaz, kayıtlı içerikten istendikçe çizilir (plan F2 §7 U18). Okulun doldurduğu Excel
şablonlarının OKUNMASI bu modülün işi değildir (`apps.okul.excel_*`).

Biçim kararları (Word ve PDF ile aynı):

- **Yazı tipi** "Times New Roman" adıyla yazılır, gömülmez; gövde 12, 5-7 sütunlu tablo 10, konum
  cümlesi ve dipnot 9 punto (`shared.evrak.tablo_punto`; RYUE md. 7/1 alt sınırı `EN_KUCUK_PUNTO`).
- **Tek çalışma sayfası**, adı belgenin kodudur; A4 dikey, kenar boşlukları PDF'inkiyle aynı, baskıda
  sayfa genişliğine sığdırılır. Sütun genişlikleri en geniş tablonun oranındandır (`sutun_yuzdeleri`).
- **Resmî yazı çizilmez** (`shared.evrak.xlsx_ciz` reddeder): sayfanın tek sütun ızgarası
  tablonundur, RYUE başının ızgarası onunla birlikte korunamaz. F2'de Excel'i olan E08 ve E14 resmî
  yazı değildir.
- **Altlık** "OAB Defteri · <kod> · Sayfa &P/&N" (Excel'in sayfa alanları); hücrede değildir,
  metin akışına girmez.
- **Sayfa sonu** Excel'in elle sayfa sonudur (`row_breaks`): sınıf başına sayfa baskıda korunur.
- Bütün değerler METİN olarak yazılır: içerik modelinin hücreleri metindir, sayıya çevrilmez (tek
  içerik; "05" gibi değerler bozulmaz).
- Büyük harf verinin kendisindedir; Excel'de harf dönüştüren biçim yoktur.

Birleştirilmiş hücreler Excel'de satır yüksekliğini kendiliğinden büyütmez: paragrafın satır sayısı
sütun genişliğinden kestirilir (`_satir_sayisi`), satır yüksekliği buna göre yazılır.

openpyxl tembel içe aktarılır.
"""

from __future__ import annotations

import io
import math
from collections.abc import Sequence
from typing import Any

#: Yazı tipi ve boyutları (`shared.docx` ile aynı değerler).
YAZI_TIPI = "Times New Roman"
GOVDE_PUNTO = 12
EN_KUCUK_PUNTO = 9
KONUM_PUNTO = 9
DIPNOT_PUNTO = 9
ALTLIK_PUNTO = 12
#: Sayfanın toplam sütun genişliği (Excel'in karakter birimi): A4 dikeyin yazı alanı (17,4 cm)
#: Times New Roman 12 puntoda yaklaşık bu kadar karakter alır.
TOPLAM_GENISLIK = 86.0
#: Kenar boşlukları (inç; PDF taban şablonunun 1,4 / 1,8 / 1,5 / 1,8 cm'si).
KENARLAR = {"top": 0.55, "right": 0.71, "bottom": 0.59, "left": 0.71, "header": 0.2, "footer": 0.2}
#: Satır yüksekliği katsayısı (punto başına nokta).
SATIR_ARALIGI = 1.35


class Kitap:
    """Tek sayfalık Excel kitabı; bloklar sırayla eklenir (`shared.evrak.xlsx_ciz`)."""

    def __init__(self, kod: str, yuzdeler: Sequence[float]) -> None:
        from openpyxl import Workbook
        from openpyxl.utils import get_column_letter

        if not yuzdeler:
            raise ValueError("Excel sayfası en az bir sütun taşır.")
        self.kitap = Workbook()
        self.sayfa: Any = self.kitap.active
        self.sayfa.title = kod
        self.genislik = len(yuzdeler)
        self.sutun_genislikleri = [TOPLAM_GENISLIK * yuzde / sum(yuzdeler) for yuzde in yuzdeler]
        for sira, deger in enumerate(self.sutun_genislikleri, start=1):
            self.sayfa.column_dimensions[get_column_letter(sira)].width = round(deger, 2)
        self.satir = 1
        self._sayfa_ayari(kod)

    # -- sayfa ayarı ---------------------------------------------------------------
    def _sayfa_ayari(self, kod: str) -> None:
        ayar = self.sayfa.page_setup
        ayar.paperSize = self.sayfa.PAPERSIZE_A4
        ayar.orientation = self.sayfa.ORIENTATION_PORTRAIT
        ayar.fitToWidth = 1
        ayar.fitToHeight = 0
        self.sayfa.sheet_properties.pageSetUpPr.fitToPage = True
        for ad, deger in KENARLAR.items():
            setattr(self.sayfa.page_margins, ad, deger)
        altlik = self.sayfa.oddFooter.center
        altlik.text = f"OAB Defteri · {kod} · Sayfa &P/&N"
        altlik.size = ALTLIK_PUNTO
        altlik.font = YAZI_TIPI

    # -- yardımcılar ---------------------------------------------------------------
    def _yazi(self, punto: int, *, kalin: bool = False) -> Any:
        from openpyxl.styles import Font

        if punto < EN_KUCUK_PUNTO:
            raise ValueError("Yazı alanında 9 puntodan küçük metin yoktur (RYUE md. 7/1).")
        return Font(name=YAZI_TIPI, size=punto, bold=kalin)

    def _satir_sayisi(self, metin: str, ilk: int, son: int, punto: int) -> int:
        genislik = sum(self.sutun_genislikleri[ilk - 1 : son])
        karakter = max(1, int(genislik * GOVDE_PUNTO / punto))
        return sum(max(1, math.ceil(len(parca) / karakter)) for parca in metin.split("\n"))

    def _yukseklik(self, satir_sayisi: int, punto: int) -> None:
        mevcut = self.sayfa.row_dimensions[self.satir].height or 0
        yeni = round(satir_sayisi * punto * SATIR_ARALIGI, 2)
        self.sayfa.row_dimensions[self.satir].height = max(mevcut, yeni)

    def _hucre(
        self,
        metin: str,
        ilk: int,
        son: int,
        *,
        hiza: str,
        punto: int = GOVDE_PUNTO,
        kalin: bool = False,
        cerceve: bool = False,
    ) -> None:
        from openpyxl.styles import Alignment, Border, Side

        if son > ilk:
            self.sayfa.merge_cells(
                start_row=self.satir, start_column=ilk, end_row=self.satir, end_column=son
            )
        hucre = self.sayfa.cell(row=self.satir, column=ilk)
        if metin:
            hucre.value = metin
            hucre.data_type = "s"
        hucre.font = self._yazi(punto, kalin=kalin)
        hucre.alignment = Alignment(horizontal=hiza, vertical="top", wrap_text=True)
        if cerceve:
            ince = Side(style="thin")
            for sutun in range(ilk, son + 1):
                self.sayfa.cell(row=self.satir, column=sutun).border = Border(
                    left=ince, right=ince, top=ince, bottom=ince
                )
        if metin:
            self._yukseklik(self._satir_sayisi(metin, ilk, son, punto), punto)

    # -- düzen öğeleri ---------------------------------------------------------------
    def bos_satir(self) -> None:
        """Boş satır (RYUE'nün satır boşluğu; metin akışına girmez)."""
        self.satir += 1

    def ortali_satir(self, metin: str, *, kalin: bool = False, punto: int = GOVDE_PUNTO) -> None:
        """Sayfa boyu ortalı satır (antet, başlık, muhatap)."""
        self._hucre(metin, 1, self.genislik, hiza="center", punto=punto, kalin=kalin)
        self.satir += 1

    def sola_satir(self, metin: str, *, kalin: bool = False) -> None:
        """Sayfa boyu sola yaslı satır (bölüm başlığı, ek bölümü)."""
        self._hucre(metin, 1, self.genislik, hiza="left", kalin=kalin)
        self.satir += 1

    def paragraf(self, metin: str, *, punto: int = GOVDE_PUNTO) -> None:
        """İki yana yaslı paragraf; sayfa boyu birleştirilmiş tek hücre."""
        self._hucre(metin, 1, self.genislik, hiza="justify", punto=punto)
        self.satir += 1

    def tablo(
        self, basliklar: Sequence[str], satirlar: Sequence[Sequence[str]], *, punto: int
    ) -> None:
        """Çerçeveli veri tablosu; başlık satırı kalın. Dar tablonun son sütunu sayfanın kalan
        sütunlarına yayılır."""
        sutun = len(basliklar)
        if sutun > self.genislik:
            raise ValueError("Tablo sayfanın sütun sayısından geniş.")
        for kalin, degerler in ((True, basliklar), *((False, satir) for satir in satirlar)):
            for sira, metin in enumerate(degerler, start=1):
                son = self.genislik if sira == sutun else sira
                self._hucre(metin, sira, son, hiza="left", punto=punto, kalin=kalin, cerceve=True)
            self.satir += 1

    def imza(self, tarih: str, sahipler: Sequence[tuple[str, str]]) -> None:
        """İmza: sağda tarih, altında yan yana sahipler (ad ve görev aynı hücrede, alt alta)."""
        self.bos_satir()
        if tarih:
            self._hucre(tarih, 1, self.genislik, hiza="right")
            self.satir += 1
        if not sahipler:
            return
        if len(sahipler) > self.genislik:
            for ad, gorev in sahipler:
                self._hucre("\n".join((ad, gorev)), 1, self.genislik, hiza="center")
                self.satir += 1
            return
        pay = self.genislik // len(sahipler)
        for sira, (ad, gorev) in enumerate(sahipler):
            ilk = sira * pay + 1
            son = self.genislik if sira == len(sahipler) - 1 else ilk + pay - 1
            self._hucre("\n".join((ad, gorev)), ilk, son, hiza="center")
        self.satir += 1

    def sayfa_sonu(self) -> None:
        """Elle sayfa sonu: sonraki satır yeni sayfada başlar."""
        from openpyxl.worksheet.pagebreak import Break

        self.sayfa.row_breaks.append(Break(id=self.satir - 1))

    def kaydet(self) -> bytes:
        tampon = io.BytesIO()
        self.kitap.save(tampon)
        return tampon.getvalue()


def ac(veri: bytes) -> Any:
    """.xlsx baytlarını openpyxl kitabı olarak açar (geri okuma, testler)."""
    from openpyxl import load_workbook

    return load_workbook(io.BytesIO(veri))


def metin_akisi(veri: bytes) -> list[str]:
    """Kitabın etkin sayfasının metin akışı: satır satır, soldan sağa; hücre içindeki satırlar
    sırayla (imza hücresinde ad ve görev). Boş hücre ve birleştirilmiş hücrenin gizli parçaları
    girmez; altlık hücrede olmadığı için girmez (`shared.evrak.metin_akisi`'nin eşi)."""
    akis: list[str] = []
    for satir in ac(veri).active.iter_rows(values_only=True):
        for deger in satir:
            if deger is None:
                continue
            akis += [parca for parca in str(deger).split("\n") if parca.strip()]
    return akis
