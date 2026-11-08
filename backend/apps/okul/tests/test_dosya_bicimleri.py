"""İçe aktarılan dosyanın biçimi — CSV (tasarım §8.1 A4) ve makrolu dosyanın reddi (tasarım TK18).

Ortak okuma `excel_ortak.dosyayi_oku`'dadır (personel ve veli listesi aktarımı kullanır; veli
listesinin CSV ve makro sınaması `test_veli_listesi.py`'dedir):

- CSV: UTF-8 BOM'lu ya da BOM'suz, değilse Windows-1254 (ISO-8859-9 son çare); ayırıcı `;`,
  `,` ya da sekme sezilir. Düz metin olmayan `.csv` Türkçe iletiyle reddedilir.
- Makro: `.xlsm`/`.xltm`/`.xlam` uzantısı, içinde `vbaProject.bin` bulunan zip kabı ve VBA
  bölümü taşıyan Excel 97-2003 kabı okunmadan reddedilir; aktarım FAILED izi bırakır.

Sentetik dosyalar testin içinde üretilir (VBA projesinin İÇERİĞİ yoktur; yalnız kabın adı
ya da dizin girdisi). Adlar uydurmadır (KVKK).
"""

from __future__ import annotations

import struct
import zipfile
from io import BytesIO
from pathlib import Path

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


def _xlsx(*, vba: bool = False) -> bytes:
    kitap = Workbook()
    for satir in _SATIRLAR:
        kitap.active.append(satir)
    tampon = BytesIO()
    kitap.save(tampon)
    if vba:
        # Makrolu kitabın parçası: içerik önemsizdir, kabın içinde bulunması yeter.
        with zipfile.ZipFile(tampon, "a") as kap:
            kap.writestr("xl/vbaProject.bin", b"uydurma vba projesi")
    return tampon.getvalue()


# ---------------------------------------------------------------------------
# Sentetik Excel 97-2003 (OLE2/CFB) kabı — yalnız dizin; VBA bölümü isteğe bağlı
# ---------------------------------------------------------------------------
_SERBEST = 0xFFFFFFFF  # FREESECT / NOSTREAM
_ZINCIR_SONU = 0xFFFFFFFE  # ENDOFCHAIN
_FAT_SEKTORU = 0xFFFFFFFD  # FATSECT


def _dizin_girdisi(ad: str, tur: int, *, sag: int = _SERBEST, cocuk: int = _SERBEST) -> bytes:
    """128 baytlık CFB dizin girdisi (ad UTF-16LE; boyut 0, başlangıç sektörü yok)."""
    ad_baytlari = ad.encode("utf-16-le")
    girdi = ad_baytlari.ljust(64, b"\x00")
    girdi += struct.pack("<HBB", len(ad_baytlari) + 2 if ad else 0, tur, 1)
    girdi += struct.pack("<III", _SERBEST, sag, cocuk)
    girdi += b"\x00" * 16 + b"\x00" * 4 + b"\x00" * 16  # CLSID, durum, zamanlar
    girdi += struct.pack("<IQ", _ZINCIR_SONU, 0)
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
    [(_xlsx(), "liste.xlsm"), (_xlsx(vba=True), "liste.xlsx"), (_ole2(vba=True), "liste.xls")],
    ids=["xlsm", "vba_xlsx", "vba_xls"],
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
