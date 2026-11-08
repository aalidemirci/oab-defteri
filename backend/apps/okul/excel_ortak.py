"""Excel ve pano girdisinin ortak yardımcıları — Türkçe başlık katlama, başlık bulma, okuma.

F1b 5. adımda öğrenci ayrıştırıcısı (`excel_ogrenci`) sökülürken onun ortak kısmı buraya
taşındı (tasarım §5.1 ALMA, §8.4; plan "F1b-5 uygulama kararları"): personel ayrıştırıcısı
(`excel_personel`), e-Okul önişleyicisi (`eokul`), ad eşleştirme (`name_match`), hesap adı
kuralı (`services.hesap_kurallari`) ve seçiciler bunu kullanır; veli listesi ayrıştırıcısı da
başlığını buradaki yolla bulacaktır (tasarım §8.4: "başlık bulma ve Türkçe katlama veli
listesine UYARLA").

- `normalize_header`: başlık ve ad katlaması ('Adı Soyadı' → 'adi soyadi').
- `basligi_bul`: ilk satırlar içinde eşleme sözlüğüne en iyi uyan başlık satırı.
- `read_sheet`: `.xlsx` (openpyxl) ve Excel 97-2003 `.xls` (xlrd; e-Okul ihracı) okuma.
- `ParserError`: girdi ayrıştırılamadı (kullanıcıya Türkçe açıklama).

Modül SAFTIR (DB'siz, Django'suz): ayrıştırıcılar DB'siz test edilir.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from openpyxl import load_workbook

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


def _alan_bul(norm: str, synonyms: Mapping[str, Sequence[str]]) -> str | None:
    """Normalize başlığı bir mantıksal alana eşler (sözlük sırasıyla, ilk eşleşen kazanır)."""
    for fieldname, keywords in synonyms.items():
        for kw in keywords:
            if kw == norm or kw in norm:
                return fieldname
    return None


def basliklari_esle(
    cells: Sequence[Any], synonyms: Mapping[str, Sequence[str]]
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
        fieldname = _alan_bul(norm, synonyms)
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
        fields, matched, warnings = basliklari_esle(cells, synonyms)
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
