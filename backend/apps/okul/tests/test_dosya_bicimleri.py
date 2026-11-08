"""İçe aktarılan dosyanın biçimi — CSV (tasarım §8.1 A4) ve makrolu dosyanın reddi (tasarım TK18).

Ortak okuma `excel_ortak.dosyayi_oku`'dadır (personel ve veli listesi aktarımı kullanır; veli
listesinin CSV ve makro sınaması `test_veli_listesi.py`'dedir):

- CSV: UTF-8 BOM'lu ya da BOM'suz, değilse Windows-1254 (ISO-8859-9 son çare); ayırıcı `;`,
  `,` ya da sekme sezilir. Düz metin olmayan `.csv` Türkçe iletiyle reddedilir.
- Makro: `.xlsm`/`.xltm`/`.xlam` uzantısı, içinde `vbaProject.bin` ya da Excel 4.0 makro sayfası
  (`xl/macrosheets/`, `xl/intlMacrosheets/`) bulunan zip kabı, VBA bölümü ya da makro sayfası
  (BIFF BOUNDSHEET kaydında sayfa türü makro) taşıyan Excel 97-2003 kabı okunmadan reddedilir;
  aktarım FAILED izi bırakır.
- Matrisin tavanları (üç biçimde aynı): xlsx'in `<dimension>` beyanı matrisi şişirmez, sütunlar
  `_AZAMI_SUTUN`'da kesilir, `_AZAMI_SATIR`'ı aşan dosya Türkçe iletiyle reddedilir.
- Bozuk girdi 500 değil Türkçe iletili 400'dür ve FAILED izi bırakır: bozuk sayfa XML'i, alan
  boyu sınırını aşan CSV hücresi.

Sentetik dosyalar testin içinde üretilir (VBA projesinin ve makro sayfasının İÇERİĞİ yoktur;
yalnız kabın adı, dizin girdisi ya da sayfa tanımı). Adlar uydurmadır (KVKK).
"""

from __future__ import annotations

import csv
import re
import struct
import zipfile
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import Final

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook
from rest_framework.test import APIClient

from apps.okul import excel_ortak
from apps.okul.excel_ortak import ParserError
from apps.okul.models import ImportRun, ImportSourceType, ImportStatus, MemberKind, Personnel
from apps.okul.services import imports as import_service

VERI = Path(__file__).resolve().parent / "veri"
EOKUL_PERSONEL_LISTESI = VERI / "eokul_personel_listesi.xls"

#: Uydurma personel listesi: başlık + üç satır (üç görev türü).
_SATIRLAR = [
    ["Adı", "Soyadı", "Görev Türü"],
    ["ÇAĞLA", "IŞIKSOY", "Öğretmen"],
    ["İLKER", "ŞAHİNOĞLU", "Yönetici"],
    ["GÜLŞEN", "ÖZDOĞRU", "Diğer personel"],
]


def _csv(ayirici: str, *, satirlar: list[list[str]] | None = None) -> str:
    return "\r\n".join(ayirici.join(satir) for satir in satirlar or _SATIRLAR) + "\r\n"


def _xlsx(
    *,
    vba: bool = False,
    parca: str | None = None,
    hucreler: dict[tuple[int, int], str] | None = None,
) -> bytes:
    """Uydurma kitap; `vba` VBA projesini, `parca` verilen adlı parçayı (makro sayfası),
    `hucreler` (satır, sütun) → değer ek hücreleri ekler."""
    kitap = Workbook()
    for satir in _SATIRLAR:
        kitap.active.append(satir)
    for (satir_no, sutun_no), deger in (hucreler or {}).items():
        kitap.active.cell(row=satir_no, column=sutun_no, value=deger)
    tampon = BytesIO()
    kitap.save(tampon)
    if vba:
        # Makrolu kitabın parçası: içerik önemsizdir, kabın içinde bulunması yeter.
        with zipfile.ZipFile(tampon, "a") as kap:
            kap.writestr("xl/vbaProject.bin", b"uydurma vba projesi")
    if parca is not None:
        with zipfile.ZipFile(tampon, "a") as kap:
            kap.writestr(parca, b"<xm:macrosheet/>")
    return tampon.getvalue()


_SAYFA: Final = "xl/worksheets/sheet1.xml"


def _sayfayi_degistir(baytlar: bytes, degistir: Callable[[str], str]) -> bytes:
    """Kitabın ilk sayfasının XML'ini `degistir`le yeniden yazar (öteki parçalar aynen)."""
    tampon = BytesIO()
    with (
        zipfile.ZipFile(BytesIO(baytlar)) as giris,
        zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as cikis,
    ):
        for ad in giris.namelist():
            veri = giris.read(ad)
            if ad == _SAYFA:
                veri = degistir(veri.decode("utf-8")).encode("utf-8")
            cikis.writestr(ad, veri)
    return tampon.getvalue()


def _uzak_satir_ekle(satir_no: int) -> Callable[[str], str]:
    """Sayfanın sonuna `satir_no`'da tek hücrelik satır ekler (arada satır yok)."""
    ek = f'<row r="{satir_no}"><c r="A{satir_no}" t="inlineStr"><is><t>uzak</t></is></c></row>'
    return lambda xml: xml.replace("</sheetData>", ek + "</sheetData>")


# ---------------------------------------------------------------------------
# Sentetik Excel 97-2003 (OLE2/CFB) kabı — yalnız dizin; VBA bölümü isteğe bağlı
# ---------------------------------------------------------------------------
_SERBEST = 0xFFFFFFFF  # FREESECT / NOSTREAM
_ZINCIR_SONU = 0xFFFFFFFE  # ENDOFCHAIN
_FAT_SEKTORU = 0xFFFFFFFD  # FATSECT


def _dizin_girdisi(
    ad: str,
    tur: int,
    *,
    sag: int = _SERBEST,
    cocuk: int = _SERBEST,
    baslangic: int = _ZINCIR_SONU,
    boyut: int = 0,
) -> bytes:
    """128 baytlık CFB dizin girdisi (ad UTF-16LE; varsayılan boyut 0, başlangıç sektörü yok)."""
    ad_baytlari = ad.encode("utf-16-le")
    girdi = ad_baytlari.ljust(64, b"\x00")
    girdi += struct.pack("<HBB", len(ad_baytlari) + 2 if ad else 0, tur, 1)
    girdi += struct.pack("<III", _SERBEST, sag, cocuk)
    girdi += b"\x00" * 16 + b"\x00" * 4 + b"\x00" * 16  # CLSID, durum, zamanlar
    girdi += struct.pack("<IQ", baslangic, boyut)
    assert len(girdi) == 128
    return girdi


def _ole2(*, vba: bool) -> bytes:
    """İki sektörlük CFB v3 kabı: FAT ve dizin. Dizinde "Workbook" ve (istenirse) VBA bölümü."""
    baslik = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 16
    baslik += struct.pack("<HHHHH", 0x3E, 3, 0xFFFE, 9, 6) + b"\x00" * 6
    baslik += struct.pack("<IIIIIIIII", 0, 1, 1, 0, 4096, _ZINCIR_SONU, 0, _ZINCIR_SONU, 0)
    baslik += struct.pack("<I", 0) + struct.pack("<I", _SERBEST) * 108
    assert len(baslik) == 512
    fat = struct.pack("<II", _FAT_SEKTORU, _ZINCIR_SONU) + struct.pack("<I", _SERBEST) * 126
    girdiler = [
        _dizin_girdisi("Root Entry", 5, cocuk=1),
        _dizin_girdisi("Workbook", 2, sag=2 if vba else _SERBEST),
        _dizin_girdisi("_VBA_PROJECT_CUR", 1) if vba else _dizin_girdisi("", 0),
        _dizin_girdisi("", 0),
    ]
    return baslik + fat + b"".join(girdiler)


#: Kitap akışının boyu: 4096 bayt (sekiz sektör) — küçük akış kabına (mini stream) düşmez.
_AKIS_BOYU = 4096


def _biff_kaydi(tur: int, veri: bytes = b"") -> bytes:
    return struct.pack("<HH", tur, len(veri)) + veri


def _biff_akisi(sayfa_turleri: list[int]) -> bytes:
    """BIFF8 kitap akışının genel bölümü: BOF, her sayfa için BOUNDSHEET (`dt`), EOF; dolgu."""
    akis = _biff_kaydi(0x0809, struct.pack("<HHHHII", 0x0600, 0x0005, 0, 0, 0, 0))
    for sira, dt in enumerate(sayfa_turleri, start=1):
        ad = f"Sayfa{sira}".encode("latin-1")
        akis += _biff_kaydi(0x0085, struct.pack("<IBBBB", 0, 0, dt, len(ad), 0) + ad)
    akis += _biff_kaydi(0x000A)
    assert len(akis) <= _AKIS_BOYU
    return akis.ljust(_AKIS_BOYU, b"\x00")


def _ole2_biff(sayfa_turleri: list[int]) -> bytes:
    """CFB v3 kabı: FAT (0), dizin (1), "Workbook" akışı (2-9; BIFF sayfa tanımlarıyla).

    VBA bölümü YOKTUR: makro yalnız sayfa türüyle (`dt` 0x01 Excel 4.0 makro sayfası) gelir.
    """
    baslik = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 16
    baslik += struct.pack("<HHHHH", 0x3E, 3, 0xFFFE, 9, 6) + b"\x00" * 6
    baslik += struct.pack("<IIIIIIIII", 0, 1, 1, 0, 4096, _ZINCIR_SONU, 0, _ZINCIR_SONU, 0)
    baslik += struct.pack("<I", 0) + struct.pack("<I", _SERBEST) * 108
    akis_sektorleri = _AKIS_BOYU // 512
    zincir = [*range(3, 2 + akis_sektorleri), _ZINCIR_SONU]
    fat = struct.pack("<II", _FAT_SEKTORU, _ZINCIR_SONU) + struct.pack(f"<{len(zincir)}I", *zincir)
    fat = fat.ljust(512, b"\xff")
    girdiler = [
        _dizin_girdisi("Root Entry", 5, cocuk=1),
        _dizin_girdisi("Workbook", 2, baslangic=2, boyut=_AKIS_BOYU),
        _dizin_girdisi("", 0),
        _dizin_girdisi("", 0),
    ]
    return baslik + fat + b"".join(girdiler) + _biff_akisi(sayfa_turleri)


# ---------------------------------------------------------------------------
# CSV okuma
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("ayirici", "kodlama", "bom"),
    [
        (";", "utf-8", True),
        (";", "utf-8", False),
        (",", "utf-8", True),
        (",", "utf-8", False),
        (";", "cp1254", False),
        (",", "cp1254", False),
        ("\t", "utf-8", False),
    ],
    ids=[
        "noktali_virgul_utf8_bom",
        "noktali_virgul_utf8",
        "virgul_utf8_bom",
        "virgul_utf8",
        "noktali_virgul_1254",
        "virgul_1254",
        "sekme_utf8",
    ],
)
def test_csv_iki_ayirici_iki_kodlama_ve_bom_okunur(ayirici: str, kodlama: str, bom: bool) -> None:
    baytlar = _csv(ayirici).encode(kodlama)
    if bom:
        baytlar = b"\xef\xbb\xbf" + baytlar

    assert excel_ortak.read_csv(baytlar) == _SATIRLAR


def test_bom_basliga_karismaz() -> None:
    """BOM'lu dosyada ilk başlık "\\ufeffAdı" değil "Adı"dır (başlık eşlemesi düşmesin)."""
    grid = excel_ortak.read_csv(b"\xef\xbb\xbf" + _csv(";").encode("utf-8"))
    assert grid[0][0] == "Adı"


def test_windows_1254_turkce_harfleri_dogru_cozulur() -> None:
    baytlar = "Adı;Soyadı\r\nİĞNE;ŞÜÇÖĞI\r\n".encode("cp1254")
    with pytest.raises(UnicodeDecodeError):
        baytlar.decode("utf-8")  # sınama gerçekten UTF-8 olmayan dosyayla yapılır

    assert excel_ortak.read_csv(baytlar) == [["Adı", "Soyadı"], ["İĞNE", "ŞÜÇÖĞI"]]


def test_1254te_tanimsiz_bayt_iso_8859_9_ile_cozulur() -> None:
    baytlar = "Adı;Soyadı\r\n".encode("iso-8859-9") + b"\x81;\xfe\r\n"
    assert excel_ortak.read_csv(baytlar)[1] == ["\x81", "ş"]


def test_tirnak_icindeki_ayirici_alan_bolmez_ve_rapor_adi_satiri_sezgiyi_bozmaz() -> None:
    metin = 'PERSONEL LİSTESİ\r\nAd Soyad;Görevi\r\n"YILMAZ, ALİ";Öğretmen\r\n'
    assert excel_ortak.read_csv(metin.encode("utf-8")) == [
        ["PERSONEL LİSTESİ"],
        ["Ad Soyad", "Görevi"],
        ["YILMAZ, ALİ", "Öğretmen"],
    ]


@pytest.mark.parametrize("baytlar", [b"Ad\x00\x00Soyad", _xlsx()[:200] + b"\x00"])
def test_duz_metin_olmayan_csv_turkce_iletiyle_reddedilir(baytlar: bytes) -> None:
    with pytest.raises(ParserError, match="CSV dosyası okunamadı"):
        excel_ortak.read_csv(baytlar)


def test_imzasiz_dosya_yalniz_csv_uzantisiyla_csv_okunur() -> None:
    baytlar = _csv(";").encode("utf-8")
    assert excel_ortak.dosyayi_oku(baytlar, "liste.CSV") == _SATIRLAR
    for ad in ("liste.xlsx", "liste.txt", ""):
        with pytest.raises(ParserError, match="Desteklenen biçimler"):
            excel_ortak.dosyayi_oku(baytlar, ad)


def test_csv_uzantili_excel_imzasindan_okunur() -> None:
    """Tür imza baytından seçilir: `.csv` adıyla kaydedilmiş xlsx yine Excel olarak okunur."""
    assert excel_ortak.dosyayi_oku(_xlsx(), "liste.csv") == _SATIRLAR


@pytest.mark.parametrize(
    ("metin", "beklenen"),
    [
        (
            "Velinin Adı Soyadı;Öğrencinin Sınıfı\r\nAyşe, Fatma Kaya, Yılmaz;10-A\r\n",
            [["Velinin Adı Soyadı", "Öğrencinin Sınıfı"], ["Ayşe, Fatma Kaya, Yılmaz", "10-A"]],
        ),
        (
            "Ad;Sınıf;Not\r\nÖRNEK VELİ;9-A;Mah. 1, Sok. 2, No 3, Daire 4, Kat 5\r\n"
            "DENEME VELİ;9-B;yok\r\n",
            [
                ["Ad", "Sınıf", "Not"],
                ["ÖRNEK VELİ", "9-A", "Mah. 1, Sok. 2, No 3, Daire 4, Kat 5"],
                ["DENEME VELİ", "9-B", "yok"],
            ],
        ),
        (
            "Ad,Sınıf\r\nÖRNEK VELİ,9-A\r\nDENEME; VELİ,9-B\r\n",
            [["Ad", "Sınıf"], ["ÖRNEK VELİ", "9-A"], ["DENEME; VELİ", "9-B"]],
        ),
        (
            "Ad\tSınıf\r\nÖRNEK, VELİ\t9-A\r\nDENEME VELİ\t9-B\r\n",
            [["Ad", "Sınıf"], ["ÖRNEK, VELİ", "9-A"], ["DENEME VELİ", "9-B"]],
        ),
    ],
    ids=["tirnaksiz_virgullu_tek_satir", "cok_virgullu_ucuncu_sutun", "virgul", "sekme"],
)
def test_ayirici_en_tutarli_bolunmeyle_sezilir(metin: str, beklenen: list[list[str]]) -> None:
    """Ölçü en büyük alan sayısı değil, en sık alan sayısını taşıyan satır sayısıdır: `;`
    ayırıcılı dosyada tırnaksız virgüllü tek satır virgülü kazandırmaz (bağımsız denetim)."""
    assert excel_ortak.read_csv(metin.encode("utf-8")) == beklenen


def test_ayirici_esitlikte_noktali_virgul_once_gelir() -> None:
    """İki ayırıcı aynı tutarlılıkta bölüyorsa Türkçe Excel'in yazdığı `;` seçilir."""
    assert excel_ortak._ayiriciyi_sez(["a;b,c", "d;e,f"]) == ";"
    assert excel_ortak._ayiriciyi_sez(["tek sütun", "başka satır"]) == ";"


# ---------------------------------------------------------------------------
# Matrisin tavanları (üç biçimde aynı)
# ---------------------------------------------------------------------------
def test_satir_siniri_iletisi_tavanla_ayni_sayiyi_soyler() -> None:
    sayi = f"{excel_ortak._AZAMI_SATIR:,}".replace(",", ".")
    assert excel_ortak.SATIR_SINIRI_ILETISI.startswith(f"Dosya okunamadı: {sayi}'den çok satır")


def test_xlsx_dimension_beyani_matrisi_sisirmez() -> None:
    """Salt okur sayfa satırları `<dimension>` genişliğine dek doldururdu: 2000 × 16384 hücre
    beyan eden küçük dosya yüz megabaytlarca matrise dönüşürdü (bağımsız denetim)."""
    baytlar = _sayfayi_degistir(
        _xlsx(),
        lambda xml: re.sub(r'<dimension ref="[^"]*"/>', '<dimension ref="A1:XFD2000"/>', xml),
    )
    with zipfile.ZipFile(BytesIO(baytlar)) as kap:
        assert '<dimension ref="A1:XFD2000"/>' in kap.read(_SAYFA).decode()
    assert len(baytlar) < 10_000

    assert excel_ortak.dosyayi_oku(baytlar, "liste.xlsx") == _SATIRLAR


def test_xlsx_sutun_tavaninin_otesi_okunmaz() -> None:
    sinir = excel_ortak._AZAMI_SUTUN
    grid = excel_ortak.dosyayi_oku(
        _xlsx(hucreler={(2, sinir): "sınırda", (3, sinir + 1): "öte", (4, 16384): "en uzak"}),
        "liste.xlsx",
    )
    assert len(grid) == len(_SATIRLAR) and {len(satir) for satir in grid} == {sinir}
    assert grid[1][sinir - 1] == "sınırda"
    assert [satir[:3] for satir in grid] == _SATIRLAR
    assert "öte" not in str(grid) and "en uzak" not in str(grid)


def test_xlsx_satir_tavani_asilinca_reddedilir() -> None:
    """Arada satır olmasa da uzaktaki tek satır matrisi tavana dek uzatır; tavan dahil kabul."""
    sinir = excel_ortak._AZAMI_SATIR
    sinirda = excel_ortak.dosyayi_oku(_sayfayi_degistir(_xlsx(), _uzak_satir_ekle(sinir)), "a.xlsx")
    assert len(sinirda) == sinir and sinirda[-1] == ["uzak", None, None]

    for satir_no in (sinir + 1, 1_048_576):
        baytlar = _sayfayi_degistir(_xlsx(), _uzak_satir_ekle(satir_no))
        with pytest.raises(ParserError) as hata:
            excel_ortak.dosyayi_oku(baytlar, "liste.xlsx")
        assert str(hata.value) == excel_ortak.SATIR_SINIRI_ILETISI


def test_csv_satir_tavani_ve_sutun_tavani() -> None:
    sinir = excel_ortak._AZAMI_SATIR
    assert len(excel_ortak.read_csv(b"a;b\r\n" * sinir)) == sinir
    with pytest.raises(ParserError) as hata:
        excel_ortak.read_csv(b"a;b\r\n" * (sinir + 1))
    assert str(hata.value) == excel_ortak.SATIR_SINIRI_ILETISI

    genis = ";".join(f"s{i}" for i in range(excel_ortak._AZAMI_SUTUN + 10))
    grid = excel_ortak.read_csv(f"{genis}\r\n{genis}\r\n".encode())
    assert {len(satir) for satir in grid} == {excel_ortak._AZAMI_SUTUN}


def test_xls_satir_ve_sutun_tavani(monkeypatch: pytest.MonkeyPatch) -> None:
    """e-Okul örneği 7 satır, 15 sütundur; tavanlar küçültülerek sınanır (.xls üretilemez)."""
    baytlar = EOKUL_PERSONEL_LISTESI.read_bytes()
    tam = excel_ortak.dosyayi_oku(baytlar, "OOK01001R1.XLS")
    assert (len(tam), {len(satir) for satir in tam}) == (7, {15})

    monkeypatch.setattr(excel_ortak, "_AZAMI_SUTUN", 4)
    assert excel_ortak.dosyayi_oku(baytlar, "OOK01001R1.XLS") == [satir[:4] for satir in tam]
    monkeypatch.setattr(excel_ortak, "_AZAMI_SATIR", 6)
    with pytest.raises(ParserError) as hata:
        excel_ortak.dosyayi_oku(baytlar, "OOK01001R1.XLS")
    assert str(hata.value) == excel_ortak.SATIR_SINIRI_ILETISI


# ---------------------------------------------------------------------------
# Bozuk girdi: Türkçe iletili ParserError (500 değil)
# ---------------------------------------------------------------------------
#: Sayfa XML'i yarıda kesilmiş xlsx (zip kabı ve kitap parçası sağlam).
_BOZUK_SAYFALI_XLSX = _sayfayi_degistir(_xlsx(), lambda xml: xml[: xml.index("<sheetData>") + 20])
#: Alan boyu sınırını (`csv.field_size_limit`) aşan tek hücreli CSV.
_UZUN_ALANLI_CSV = (
    "Velinin Adı Soyadı;Öğrencinin Sınıfı\r\n" + "x" * (csv.field_size_limit() + 10) + ";9-A\r\n"
).encode()


def test_bozuk_sayfa_xmli_turkce_iletiyle_reddedilir() -> None:
    with pytest.raises(ParserError) as hata:
        excel_ortak.dosyayi_oku(_BOZUK_SAYFALI_XLSX, "liste.xlsx")
    assert str(hata.value) == excel_ortak.DESTEKLENMEYEN_DOSYA_ILETISI
    assert hata.value.__cause__ is not None  # özgün hata zincirde kalır


def test_alan_siniri_asan_csv_turkce_iletiyle_reddedilir() -> None:
    """Ayırıcı sezgisi de `csv.Error` verir: o da Türkçe iletiye döner (bağımsız denetim)."""
    with pytest.raises(csv.Error):
        excel_ortak._ayiriciyi_sez(_UZUN_ALANLI_CSV.decode().splitlines())
    with pytest.raises(ParserError) as hata:
        excel_ortak.read_csv(_UZUN_ALANLI_CSV)
    assert str(hata.value) == excel_ortak.CSV_METIN_DEGIL_ILETISI


# ---------------------------------------------------------------------------
# Makrolu dosyanın reddi
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ad", ["liste.xlsm", "LISTE.XLTM", "eklenti.xlam"])
def test_makrolu_uzanti_icerige_bakilmadan_reddedilir(ad: str) -> None:
    with pytest.raises(ParserError) as hata:
        excel_ortak.dosyayi_oku(_xlsx(), ad)
    assert str(hata.value) == excel_ortak.MAKROLU_DOSYA_ILETISI


@pytest.mark.parametrize("ad", ["liste.xlsx", "liste.csv", ""])
def test_vba_projesi_tasiyan_zip_kabi_reddedilir(ad: str) -> None:
    with pytest.raises(ParserError) as hata:
        excel_ortak.dosyayi_oku(_xlsx(vba=True), ad)
    assert str(hata.value) == excel_ortak.MAKROLU_DOSYA_ILETISI


def test_vba_bolumu_tasiyan_xls_reddedilir() -> None:
    assert excel_ortak.makrolu_mu(_ole2(vba=True), "liste.xls") is True
    with pytest.raises(ParserError) as hata:
        excel_ortak.dosyayi_oku(_ole2(vba=True), "liste.xls")
    assert str(hata.value) == excel_ortak.MAKROLU_DOSYA_ILETISI


@pytest.mark.parametrize(
    "parca",
    ["xl/macrosheets/sheet2.xml", "xl/intlMacrosheets/sheet1.xml", "XL/MacroSheets/Sheet3.xml"],
    ids=["makro_sayfasi", "uluslararasi_makro_sayfasi", "buyuk_harfli"],
)
def test_excel_4_makro_sayfasi_tasiyan_zip_kabi_reddedilir(parca: str) -> None:
    """VBA projesi olmadan da makro taşır (XLM); uzantı .xlsx olsa da içerik reddettirir."""
    baytlar = _xlsx(parca=parca)
    assert excel_ortak.makrolu_mu(baytlar, "liste.xlsx") is True
    with pytest.raises(ParserError) as hata:
        excel_ortak.dosyayi_oku(baytlar, "liste.xlsx")
    assert str(hata.value) == excel_ortak.MAKROLU_DOSYA_ILETISI


def test_makro_sayfasina_benzeyen_baska_parca_makrolu_sayilmaz() -> None:
    assert excel_ortak.makrolu_mu(_xlsx(parca="xl/worksheets/macrosheets.xml"), "a.xlsx") is False


@pytest.mark.parametrize(
    "sayfa_turleri",
    [[0x01], [0x00, 0x01], [0x00, 0x06]],
    ids=["yalniz_makro_sayfasi", "calisma_sayfasi_ve_makro_sayfasi", "vba_modul_sayfasi"],
)
def test_biff_makro_sayfasi_tasiyan_xls_reddedilir(sayfa_turleri: list[int]) -> None:
    """Dizinde VBA bölümü yoktur; makro BOUNDSHEET kaydının sayfa türünden tanınır."""
    baytlar = _ole2_biff(sayfa_turleri)
    assert excel_ortak.makrolu_mu(baytlar, "liste.xls") is True
    with pytest.raises(ParserError) as hata:
        excel_ortak.dosyayi_oku(baytlar, "liste.xls")
    assert str(hata.value) == excel_ortak.MAKROLU_DOSYA_ILETISI


@pytest.mark.parametrize(
    "sayfa_turleri", [[0x00], [0x00, 0x02], []], ids=["calisma", "calisma_ve_grafik", "sayfasiz"]
)
def test_biff_makrosuz_sayfa_turleri_makrolu_sayilmaz(sayfa_turleri: list[int]) -> None:
    assert excel_ortak.makrolu_mu(_ole2_biff(sayfa_turleri), "liste.xls") is False


def test_biff_eof_sonrasi_kayit_okunmaz_ve_kesik_akis_dusurmez() -> None:
    """Sayfa tanımları kitabın genel bölümündedir: ilk EOF'tan sonrası yürünmez; yarım kayıt
    (bildirilen boydan kısa veri) hata vermez."""
    bof = _biff_kaydi(0x0809, struct.pack("<HHHHII", 0x0600, 0x0005, 0, 0, 0, 0))
    calisma = _biff_kaydi(0x0085, struct.pack("<IBBBB", 0, 0, 0x00, 1, 0) + b"A")
    makro = _biff_kaydi(0x0085, struct.pack("<IBBBB", 0, 0, 0x01, 1, 0) + b"M")
    assert excel_ortak._biff_makro_sayfasi_var_mi(bof + calisma + makro) is True
    assert (
        excel_ortak._biff_makro_sayfasi_var_mi(bof + calisma + _biff_kaydi(0x000A) + makro) is False
    )
    kesik = bof + struct.pack("<HH", 0x0085, 200) + b"\x00\x00\x00"
    assert excel_ortak._biff_makro_sayfasi_var_mi(kesik) is False


def test_makrosuz_kaplar_makrolu_sayilmaz() -> None:
    assert excel_ortak.makrolu_mu(_ole2(vba=False), "liste.xls") is False
    assert excel_ortak.makrolu_mu(EOKUL_PERSONEL_LISTESI.read_bytes(), "OOK01001R1.XLS") is False
    assert excel_ortak.makrolu_mu(_xlsx(), "liste.xlsx") is False
    assert excel_ortak.makrolu_mu(b"bozuk", "liste.xls") is False


def test_makro_iletisi_turkce_ve_cozum_soyler() -> None:
    assert excel_ortak.MAKROLU_DOSYA_ILETISI.startswith("Makro içeren dosya kabul edilmez.")
    assert "(*.xlsx)" in excel_ortak.MAKROLU_DOSYA_ILETISI


# ---------------------------------------------------------------------------
# Personel aktarımı: CSV uçtan uca, makro reddi FAILED izi bırakır
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_personel_aktarimi_csv_kabul_eder() -> None:
    baytlar = b"\xef\xbb\xbf" + _csv(";").encode("utf-8")

    rapor = import_service.commit_personnel_file(file_bytes=baytlar, file_name="personel.csv")

    assert (rapor.created_personnel, rapor.warnings) == (3, [])
    turler = {p.last_name: p.member_kind for p in Personnel.objects.all()}
    assert turler == {
        "IŞIKSOY": MemberKind.OGRETMEN,
        "ŞAHİNOĞLU": MemberKind.YONETICI,
        "ÖZDOĞRU": MemberKind.DIGER,
    }
    kosu = ImportRun.objects.get(status=ImportStatus.COMPLETED)
    assert (kosu.source_type, kosu.file_name) == (ImportSourceType.PERSONEL, "personel.csv")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("baytlar", "ad"),
    [
        (_xlsx(), "liste.xlsm"),
        (_xlsx(vba=True), "liste.xlsx"),
        (_ole2(vba=True), "liste.xls"),
        (_xlsx(parca="xl/macrosheets/sheet1.xml"), "liste.xlsx"),
        (_ole2_biff([0x00, 0x01]), "liste.xls"),
    ],
    ids=["xlsm", "vba_xlsx", "vba_xls", "xlm_xlsx", "xlm_xls"],
)
def test_makrolu_dosya_aktarilmaz_failed_izi_birakir(baytlar: bytes, ad: str) -> None:
    with pytest.raises(ParserError):
        import_service.preview_personnel_file(file_bytes=baytlar, file_name=ad)

    assert not Personnel.all_objects.exists()
    kosu = ImportRun.objects.get()
    assert (kosu.status, kosu.source_type) == (ImportStatus.FAILED, ImportSourceType.PERSONEL)
    assert kosu.report == {"error": excel_ortak.MAKROLU_DOSYA_ILETISI}


@pytest.mark.django_db
def test_api_csv_yuklenir_makrolu_dosya_400() -> None:
    client = APIClient()
    csv_dosyasi = SimpleUploadedFile("personel.csv", _csv(",").encode("cp1254"), "text/csv")
    onizleme = client.post(
        "/api/v1/imports/personnel/preview/", {"file": csv_dosyasi}, format="multipart"
    )
    assert onizleme.status_code == 200, onizleme.content
    assert onizleme.json()["created_personnel"] == 3

    makrolu = SimpleUploadedFile("liste.xlsm", _xlsx())
    ret = client.post("/api/v1/imports/personnel/commit/", {"file": makrolu}, format="multipart")
    assert ret.status_code == 400
    assert ret.json()["message"] == excel_ortak.MAKROLU_DOSYA_ILETISI
    assert not Personnel.all_objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("baytlar", "ad", "ileti"),
    [
        (_BOZUK_SAYFALI_XLSX, "liste.xlsx", excel_ortak.DESTEKLENMEYEN_DOSYA_ILETISI),
        (_UZUN_ALANLI_CSV, "liste.csv", excel_ortak.CSV_METIN_DEGIL_ILETISI),
        (
            _sayfayi_degistir(_xlsx(), _uzak_satir_ekle(1_048_576)),
            "liste.xlsx",
            excel_ortak.SATIR_SINIRI_ILETISI,
        ),
    ],
    ids=["bozuk_sayfa_xml", "uzun_alanli_csv", "satir_tavani"],
)
@pytest.mark.parametrize(
    ("uc", "kaynak"),
    [
        ("/api/v1/imports/personnel/{}/", ImportSourceType.PERSONEL),
        ("/api/v1/imports/parents/{}/", ImportSourceType.VELI),
    ],
    ids=["personel", "veli"],
)
@pytest.mark.parametrize("asama", ["preview", "commit"])
def test_api_bozuk_girdi_400_ve_failed_izi(
    baytlar: bytes, ad: str, ileti: str, uc: str, kaynak: str, asama: str
) -> None:
    """Bozuk girdi istek düzeyinde 500 değil Türkçe iletili 400'dür; FAILED koşusu kalır."""
    yanit = APIClient().post(
        uc.format(asama), {"file": SimpleUploadedFile(ad, baytlar)}, format="multipart"
    )

    assert yanit.status_code == 400, yanit.content
    assert yanit.json()["message"] == ileti
    kosu = ImportRun.objects.get()
    assert (kosu.status, kosu.source_type) == (ImportStatus.FAILED, kaynak)
    assert kosu.report == {"error": ileti}
    assert not Personnel.all_objects.exists()
