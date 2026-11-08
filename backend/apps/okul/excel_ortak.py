"""Excel ve pano girdisinin ortak yardımcıları — Türkçe başlık katlama, başlık bulma, okuma.

F1b 5. adımda öğrenci ayrıştırıcısı (`excel_ogrenci`) sökülürken onun ortak kısmı buraya
taşındı (tasarım §5.1 ALMA, §8.4; plan "F1b-5 uygulama kararları"): personel ayrıştırıcısı
(`excel_personel`), e-Okul önişleyicisi (`eokul`), ad eşleştirme (`name_match`), hesap adı
kuralı (`services.hesap_kurallari`) ve seçiciler bunu kullanır; veli listesi ayrıştırıcısı
(`excel_veli`) da başlığını buradaki yolla, birebir başlık eşleşmesiyle bulur (tasarım §8.4:
"başlık bulma ve Türkçe katlama veli listesine UYARLA").

- `normalize_header`: başlık ve ad katlaması ('Adı Soyadı' → 'adi soyadi').
- `basligi_bul`: ilk satırlar içinde eşleme sözlüğüne en iyi uyan başlık satırı.
- `read_sheet`: `.xlsx` (openpyxl) ve Excel 97-2003 `.xls` (xlrd; e-Okul ihracı) okuma.
- `read_csv`: `.csv` okuma (tasarım §8.1 A4): UTF-8 (BOM'lu ya da BOM'suz), değilse
  Windows-1254 (ISO-8859-9'un Türkçe harfleri aynı yerdedir; 1254'te tanımsız baytta 8859-9);
  ayırıcı `;` (Türkçe Excel'in yazdığı), `,` ya da sekme, ilk satırlardan sezilir.
- `dosyayi_oku`: yüklenen dosyanın tek giriş noktası. Makrolu dosyayı reddeder (tasarım TK18:
  `.xlsm`/`.xltm`/`.xlam` uzantısı, içinde `vbaProject.bin` bulunan zip kabı, VBA bölümü taşıyan
  `.xls`), türü imza baytından seçer, imzasız `.csv`'yi CSV okur. Boyut tavanı yüklemenin
  ortak sınırıdır (`OD_MAX_UPLOAD_SIZE_MB`, `shared.yukleme`): biçimden bağımsızdır; ayrıca
  satır sınırı yoktur.
- `ParserError`: girdi ayrıştırılamadı (kullanıcıya Türkçe açıklama).

Modül SAFTIR (DB'siz, Django'suz): ayrıştırıcılar DB'siz test edilir.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import PurePath
from typing import Any, Final

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

# Türkçe karakter → ASCII (başlık eşlemesi için; küçük harfe indirgenir).
_TR_MAP = str.maketrans(
    {
        "ş": "s",
        "Ş": "s",
        "ı": "i",
        "I": "i",
        "İ": "i",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
    }
)
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_header(text: Any) -> str:
    """Başlık hücresini eşleme için normalleştirir ('Adı Soyadı' → 'adi soyadi')."""
    if text is None:
        return ""
    s = str(text).translate(_TR_MAP).lower()
    s = _NON_ALNUM.sub(" ", s)
    return s.strip()


class ParserError(Exception):
    """Girdi ayrıştırılamadığında fırlatılır (kritik sütun eksik vb.)."""


def hucre(cells: Sequence[Any], idx: int | None) -> Any:
    """Satırın `idx`'inci hücresi; sütun eşlenmediyse ya da satır kısaysa None."""
    if idx is None or idx >= len(cells):
        return None
    return cells[idx]


def hucre_metni(value: Any) -> str:
    """Hücre değerinin kırpılmış metni; Excel'in sayı biçimi '2612.0' → '2612'."""
    if value is None:
        return ""
    s = str(value).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s


def bos_satir(cells: Sequence[Any]) -> bool:
    """Satırdaki bütün hücreler boş mu?"""
    return all(c is None or str(c).strip() == "" for c in cells)


@dataclass
class BaslikEslemesi:
    """Bulunan başlık satırı ve alan → sütun indeksi eşlemesi."""

    header_row: int
    fields: dict[str, int] = field(default_factory=dict)
    matched_headers: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _alan_bul(
    norm: str, synonyms: Mapping[str, Sequence[str]], *, tam_eslesme: bool = False
) -> str | None:
    """Normalize başlığı bir mantıksal alana eşler (sözlük sırasıyla, ilk eşleşen kazanır).

    Varsayılan eşleşme başlığın İÇİNDE arar ("ad soyad" → "personel ad soyad"). `tam_eslesme`
    yalnız birebir aynı başlığı kabul eder: veli listesinde "sınıf" "Sınıf Öğretmeni"ne, "veli
    adı" başka bir sütuna kaymasın diye (`excel_veli`; tasarım §8.1 A3 beyaz liste).
    """
    for fieldname, keywords in synonyms.items():
        for kw in keywords:
            if kw == norm or (not tam_eslesme and kw in norm):
                return fieldname
    return None


def basliklari_esle(
    cells: Sequence[Any], synonyms: Mapping[str, Sequence[str]], *, tam_eslesme: bool = False
) -> tuple[dict[str, int], dict[str, str], list[str]]:
    """Bir satırın hücrelerini alanlara eşler → (alan→indeks, alan→başlık, uyarılar).

    Aynı alana ikinci kez eşlenen sütun yok sayılır ve uyarıya yazılır (ilki kullanılır).
    """
    fields: dict[str, int] = {}
    matched: dict[str, str] = {}
    warnings: list[str] = []
    for idx, cell in enumerate(cells):
        norm = normalize_header(cell)
        if not norm:
            continue
        fieldname = _alan_bul(norm, synonyms, tam_eslesme=tam_eslesme)
        if fieldname is None:
            continue
        if fieldname in fields:
            warnings.append(
                f"'{cell}' sütunu '{fieldname}' için yinelenen eşleşme; ilki kullanıldı."
            )
            continue
        fields[fieldname] = idx
        matched[fieldname] = str(cell).strip()
    return fields, matched, warnings


def basligi_bul(
    rows: Sequence[Sequence[Any]],
    synonyms: Mapping[str, Sequence[str]],
    *,
    kullanilir_mi: Callable[[dict[str, int]], bool],
    scan_limit: int = 10,
    tam_eslesme: bool = False,
) -> BaslikEslemesi:
    """İlk `scan_limit` satır içinde en iyi başlık satırını bulur ve sütunları eşler.

    "En iyi": önce kullanılabilir olan (`kullanilir_mi`: zorunlu alanlar var), sonra en çok
    alan eşleyen. Kullanılabilir bir satır bulununca tarama durur. Hiç alan eşlenmezse
    0. satırla boş eşleme döner; çağıran zorunlu alan denetimini kendi iletisiyle yapar.
    """
    best: BaslikEslemesi | None = None
    best_usable = False
    for r in range(min(scan_limit, len(rows))):
        cells = rows[r]
        if bos_satir(cells):
            continue
        fields, matched, warnings = basliklari_esle(cells, synonyms, tam_eslesme=tam_eslesme)
        if not fields:
            continue
        usable = kullanilir_mi(fields)
        if best is None or (usable, len(fields)) > (best_usable, len(best.fields)):
            best = BaslikEslemesi(
                header_row=r, fields=fields, matched_headers=matched, warnings=warnings
            )
            best_usable = usable
        if best_usable and best.header_row == r:
            break
    return best or BaslikEslemesi(header_row=0)


#: OLE2/CFB kap imzası — Excel 97-2003 (.xls, BIFF5/BIFF8) dosyaları bununla başlar.
_OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
#: ZIP imzası — .xlsx (OOXML) bir zip kabıdır.
_ZIP_MAGIC = b"PK\x03\x04"


def is_legacy_xls(file_bytes: bytes) -> bool:
    """Bayt dizisi Excel 97-2003 (.xls) kabı mı? (openpyxl bu biçimi AÇAMAZ.)"""
    return file_bytes[:8] == _OLE2_MAGIC


def _read_xlsx(file_bytes: bytes, sheet_name: str | None = None) -> list[list[Any]]:
    wb = load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    try:
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        return [list(row) for row in ws.iter_rows(values_only=True)]
    finally:
        wb.close()


def _read_xls(file_bytes: bytes, sheet_name: str | None = None) -> list[list[Any]]:
    """Eski BIFF (.xls) baytlarını matrise çevirir — e-Okul ihraçlarının biçimi.

    e-Okul'un "Excel" düğmesi .xlsx DEĞİL, Excel 97-2003 (.xls) üretir; openpyxl
    bu kabı hiç açmaz (BadZipFile). xlrd 2.x yalnız .xls okur — ikisi birlikte
    tüm gerçek girdileri kapsar.
    """
    import xlrd  # yerel import: xlsx yolunda gereksiz yük olmasın

    try:
        wb = xlrd.open_workbook(file_contents=file_bytes)
    except ParserError:
        raise
    except Exception as exc:  # noqa: BLE001 — gerekçe aşağıda
        # GENİŞ yakalama BİLİNÇLİDİR. xlrd bozuk kapta yalnız XLRDError/
        # CompDocError atmaz: yarım inmiş bir dosyada `struct.error` ve
        # `IndexError`, kütüphanenin çıplak assert'lerinde `AssertionError`
        # yükselir. Bunlar ParserError'a dönmezse istek 500 ile düşer —
        # kullanıcı Türkçe açıklamayı GÖRMEZ ve İçe Aktarma Geçmişi'ne FAILED
        # izi de yazılmaz (`imports._personnel_entry` yalnız ParserError'da iz bırakır).
        # xlsx yolu aynı sözleşmeyi zaten sağlıyor (BadZipFile/InvalidFile).
        raise ParserError(
            "Excel 97-2003 (.xls) dosyası okunamadı; dosya eksik inmiş ya da bozuk olabilir. "
            "e-Okul'dan yeniden indirip deneyin."
        ) from exc
    try:
        if wb.nsheets == 0:
            raise ParserError("Excel dosyasında sayfa yok.")
        # Adlı sayfa istendiyse o sayfa alınır; yoksa ilk sayfaya düşülür.
        sayfalar = wb.sheet_names()
        sh = wb.sheet_by_name(sheet_name) if sheet_name in sayfalar else wb.sheet_by_index(0)
        return [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
    except ParserError:
        raise
    except Exception as exc:  # noqa: BLE001 — açılış dalıyla aynı gerekçe
        raise ParserError(
            "Excel 97-2003 (.xls) dosyasının içeriği okunamadı; dosya bozuk olabilir."
        ) from exc
    finally:
        wb.release_resources()


def read_sheet(file_bytes: bytes, *, sheet_name: str | None = None) -> list[list[Any]]:
    """Excel baytlarını satır-listesine çevirir (ilk/etkin sayfa, salt-okunur).

    Kap imzasına göre yol seçilir: `.xls` (OLE2) → xlrd, `.xlsx` (zip) → openpyxl.
    Uzantıya GÜVENİLMEZ — e-Okul dosyaları büyük harfli `.XLS` uzantısıyla iner
    ve kullanıcılar bunları elle `.xlsx` diye yeniden adlandırabiliyor.

    `sheet_name` verilirse O SAYFA okunur, bulunamazsa ilk/etkin sayfaya düşülür
    (çok sayfalı bir şablonda yalnız veri sayfasını okumak için; okulun kendi
    hazırladığı dosyada böyle bir sayfa adı bulunmayabilir). Aile iskeletinde bunu
    katalog aktarımı kullanıyordu; OAB'de bugün kullanan yoktur.
    """
    if is_legacy_xls(file_bytes):
        return _read_xls(file_bytes, sheet_name)
    return _read_xlsx(file_bytes, sheet_name)


# ---------------------------------------------------------------------------
# CSV (tasarım §8.1 A4)
# ---------------------------------------------------------------------------
_UTF8_BOM: Final = b"\xef\xbb\xbf"
#: Sezilen ayırıcılar, eşitlikte öncelik sırasıyla (Türkçe Excel `;` yazar).
CSV_AYIRICILARI: Final = (";", ",", "\t")
#: Ayırıcı sezgisinde bakılan dolu satır sayısı.
_SEZGI_SATIRI: Final = 30

CSV_METIN_DEGIL_ILETISI: Final = (
    "CSV dosyası okunamadı: dosya düz metin değil. Excel'de “CSV UTF-8 (virgülle ayrılmış)” ya "
    "da “CSV (virgülle ayrılmış)” olarak kaydedip yeniden deneyin."
)


def _csv_coz(file_bytes: bytes) -> str:
    """CSV baytlarını metne çevirir: UTF-8 BOM'lu, UTF-8, Windows-1254, ISO-8859-9 sırasıyla."""
    if file_bytes.startswith(_UTF8_BOM):
        try:
            return file_bytes[len(_UTF8_BOM) :].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ParserError(CSV_METIN_DEGIL_ILETISI) from exc
    for kodlama in ("utf-8", "cp1254"):
        try:
            return file_bytes.decode(kodlama)
        except UnicodeDecodeError:
            continue
    # ISO-8859-9 her baytı çözer; Windows-1254'te tanımsız bayt (0x81, 0x8D…) buraya düşer.
    return file_bytes.decode("iso-8859-9")


def _ayiriciyi_sez(satirlar: Sequence[str]) -> str:
    """İlk dolu satırlarda en çok alan üreten ayırıcı; eşitlikte `CSV_AYIRICILARI` sırası.

    Ölçü satır başına en çok alan sayısıdır: başlıktan önceki tek hücrelik rapor adı satırı
    sezgiyi bozmaz; tırnak içindeki ayırıcı (`"Yılmaz, Ali"`) alan saymaz.
    """
    ornek = [satir for satir in satirlar if satir.strip()][:_SEZGI_SATIRI]
    en_iyi, en_cok = CSV_AYIRICILARI[0], 0
    for ayirici in CSV_AYIRICILARI:
        alanlar = max((len(r) for r in csv.reader(ornek, delimiter=ayirici)), default=0)
        if alanlar > en_cok:
            en_iyi, en_cok = ayirici, alanlar
    return en_iyi


def read_csv(file_bytes: bytes) -> list[list[Any]]:
    """CSV baytlarını satır-listesine çevirir (tasarım §8.1 A4); metin değilse ParserError.

    Hücreler metindir (`read_sheet`'in ürettiği matrisle aynı biçim; boş hücre boş dize).
    """
    if b"\x00" in file_bytes:
        raise ParserError(CSV_METIN_DEGIL_ILETISI)
    metin = _csv_coz(file_bytes)
    ayirici = _ayiriciyi_sez(metin.splitlines())
    try:
        return [list(satir) for satir in csv.reader(io.StringIO(metin), delimiter=ayirici)]
    except csv.Error as exc:
        raise ParserError(CSV_METIN_DEGIL_ILETISI) from exc


# ---------------------------------------------------------------------------
# Makrolu dosyanın reddi ve tek giriş noktası (tasarım TK18)
# ---------------------------------------------------------------------------
#: Makro taşıyan Excel biçimlerinin uzantıları (küçük harf).
MAKROLU_UZANTILAR: Final = frozenset({".xlsm", ".xltm", ".xlam"})
#: OOXML kabında VBA projesinin parçası (`xl/vbaProject.bin`); ad büyük/küçük harfe duyarsız.
_VBA_PARCASI: Final = "vbaproject.bin"
#: Excel 97-2003 kabında VBA projesinin bölümleri (OLE2 dizin girdileri; küçük harf).
_OLE2_VBA_BOLUMLERI: Final = frozenset({"_vba_project_cur", "_vba_project", "vba"})

MAKROLU_DOSYA_ILETISI: Final = (
    "Makro içeren dosya kabul edilmez. Dosyayı Excel'de “Excel Çalışma Kitabı (*.xlsx)” "
    "olarak kaydedip yeniden yükleyin."
)
DESTEKLENMEYEN_DOSYA_ILETISI: Final = (
    "Dosya okunamadı. Desteklenen biçimler: e-Okul ihracı (.xls), uygulama şablonu (.xlsx) ve "
    "CSV (.csv). PDF desteklenmez."
)


def _uzanti(file_name: str) -> str:
    return PurePath(file_name).suffix.lower() if file_name else ""


def _zip_makrolu_mu(file_bytes: bytes) -> bool:
    """Zip kabında VBA projesi var mı? Kap açılamazsa False (okuma kendi iletisiyle düşer)."""
    try:
        with zipfile.ZipFile(BytesIO(file_bytes)) as kap:
            return any(ad.lower().endswith(_VBA_PARCASI) for ad in kap.namelist())
    except (zipfile.BadZipFile, OSError, ValueError):
        return False


def _ole2_makrolu_mu(file_bytes: bytes) -> bool:
    """Excel 97-2003 kabının dizininde VBA bölümü var mı? Dizin okunamazsa False.

    Dizin xlrd'nin kap okuyucusuyla okunur (`xlrd.compdoc`; `.xls` okuması da ondan geçer).
    Okunamayan kap `_read_xls`'in Türkçe iletisiyle düşer.
    """
    from xlrd import compdoc  # yerel import: xlsx ve CSV yolunda gereksiz yük olmasın

    try:
        kap = compdoc.CompDoc(file_bytes, logfile=io.StringIO())
    except Exception:  # noqa: BLE001 — bozuk kap okumada kendi Türkçe iletisiyle düşer
        return False
    return any(
        str(getattr(girdi, "name", "")).lower() in _OLE2_VBA_BOLUMLERI for girdi in kap.dirlist
    )


def makrolu_mu(file_bytes: bytes, file_name: str = "") -> bool:
    """Dosya makro taşıyor mu (tasarım TK18)? Uzantı YA DA içerik yeter."""
    if _uzanti(file_name) in MAKROLU_UZANTILAR:
        return True
    if file_bytes[:4] == _ZIP_MAGIC:
        return _zip_makrolu_mu(file_bytes)
    if is_legacy_xls(file_bytes):
        return _ole2_makrolu_mu(file_bytes)
    return False


def dosyayi_oku(file_bytes: bytes, file_name: str = "") -> list[list[Any]]:
    """Yüklenen dosyayı satır-listesine çevirir; okunamazsa Türkçe iletili ParserError.

    Sıra: makrolu dosya reddedilir (uzantı ya da içerik); tür imza baytından seçilir (`.xls`
    OLE2, `.xlsx` zip — uzantıya güvenilmez, `read_sheet`); imzasız dosya yalnız `.csv`
    uzantısıyla CSV okunur, değilse desteklenmeyen biçimdir.
    """
    if makrolu_mu(file_bytes, file_name):
        raise ParserError(MAKROLU_DOSYA_ILETISI)
    if is_legacy_xls(file_bytes) or file_bytes[:4] == _ZIP_MAGIC:
        try:
            return read_sheet(file_bytes)
        except (zipfile.BadZipFile, InvalidFileException, KeyError, OSError) as exc:
            raise ParserError(DESTEKLENMEYEN_DOSYA_ILETISI) from exc
    if _uzanti(file_name) == ".csv":
        return read_csv(file_bytes)
    raise ParserError(DESTEKLENMEYEN_DOSYA_ILETISI)
