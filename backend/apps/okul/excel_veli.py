"""Veli listesini okuma: başlık tespiti, iki alanlı beyaz liste, sınıf yazımının normalleşmesi.

T5 (kullanıcı 08.11.2026; plan "F1b-5 uygulama kararları"): e-Okul veli adı veren bir rapor
sunmaz; veli listesi okulun doldurduğu iki sütunlu şablondan gelir (`services.templates`). Biçim
.xlsx, e-Okul'un .xls'i ya da .csv'dir (`excel_ortak.dosyayi_oku`; makrolu dosya okunmadan
reddedilir). Tasarım §8.4'ün öğrenci ayrıştırıcısından UYARLA'ya dönen kısmı (başlık bulma ve
Türkçe katlama) `excel_ortak`'tadır.

YALNIZ İKİ ALAN OKUNUR (tasarım §8.1 A3, §8.4): velinin adı-soyadı (tek sütun ya da ad + soyad)
ve öğrencinin sınıfı. Başka her sütun — öğrencinin adı ve numarası, T.C. kimlik no, telefon,
adres, yakınlık, e-posta — eşleme sözlüğünde karşılığı olmadığı için hiç okunmaz. Başlıklar
BİREBİR eşlenir (`basligi_bul(tam_eslesme=True)`): "sınıf" "Sınıf Öğretmeni"ne, "veli adı"
başka bir sütuna kaymaz; tanınmayan başlıkta aktarım ParserError'la durur.

Satır sorunları (ad boş, sınıf boş ya da tanınmadı) satır numarası ve nedenle döner; hücrenin
DEĞERİ hiçbir yere yazılmaz (önizleme yalnız sayı gösterir, tasarım §8.4 (2)). Sınıf yazımı
`normalize.normalize_class_section` ile normalleşir ve "10-A" biçiminde saklanır (hazırlık
sınıfı "Hazırlık-A"); normalleşmeyen değer satır sorunudur.

Modül SAFTIR (DB'siz, Django'suz): ayrıştırıcı DB'siz test edilir. DB yazımı
`services/imports.py`'dadır.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Final

from apps.okul import normalize
from apps.okul.excel_ortak import (
    ParserError,
    basligi_bul,
    bos_satir,
    hucre,
    hucre_metni,
)
from apps.okul.normalize import _ascii_upper

#: Velinin adı-soyadının üst sınırı (`models.PARENT_NAME_MAX` ile aynı; eşitliği test sınar).
AD_EN_COK: Final = 200
#: Şube harflerinin üst sınırı ("10-A", "11-FEN"); uzun metin sınıf sayılmaz.
_SUBE_EN_COK: Final = 4
#: Hazırlık sınıfının saklanan adı ("Hazırlık-A").
HAZIRLIK: Final = "Hazırlık"

# Mantıksal alan → normalize edilmiş başlıklar (BİREBİR eşleşme; `excel_ortak.normalize_header`).
# Şablonun başlıkları "Velinin Adı Soyadı" ve "Öğrencinin Sınıfı"dır (`services.templates`).
COLUMN_SYNONYMS: Final[dict[str, list[str]]] = {
    "full_name": [
        "velinin adi soyadi",
        "veli adi soyadi",
        "velinin adi ve soyadi",
        "veli adi ve soyadi",
        "veli ad soyad",
        "veli adsoyad",
    ],
    "first_name": ["velinin adi", "veli adi"],
    "last_name": ["velinin soyadi", "veli soyadi"],
    "student_class": [
        "ogrencinin sinifi",
        "ogrenci sinifi",
        "ogrencinin sinifi ve subesi",
        "sinifi",
        "sinif",
        "sinif sube",
        "sinifi subesi",
        "sinif ve sube",
    ],
}

#: Satır sorunlarının iletileri (sözlük §1 "Veli listesi"; değer yazılmaz).
VELI_ADI_BOS: Final = "Velinin adı-soyadı boş; satır aktarılmadı."
VELI_ADI_UZUN: Final = f"Velinin adı-soyadı {AD_EN_COK} karakterden uzun; satır aktarılmadı."
SINIF_BOS: Final = "Öğrencinin sınıfı boş; satır aktarılmadı."
SINIF_TANINMADI: Final = (
    "Öğrencinin sınıfı tanınmadı (9-A, 10/B ya da Hazırlık-A biçiminde yazın); satır aktarılmadı."
)
#: Zorunlu sütun eksik (ParserError; aktarım durur).
SUTUN_EKSIK: Final = (
    "Veli listesinde “Velinin Adı Soyadı” ve “Öğrencinin Sınıfı” sütunları bulunamadı. "
    "Programın veli listesi şablonunu indirip başlıklarını değiştirmeden doldurun."
)

#: Sınıf metnindeki dolgu sözcükleri ("9. Sınıf / A Şubesi" → "9 A"); ASCII'ye katlanmış.
_DOLGU_SOZCUKLERI: Final = frozenset({"SINIF", "SINIFI", "SUBE", "SUBESI"})
_SOZCUK: Final = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]+")
_HAZIRLIK_SEVIYELERI: Final = (normalize.PREP_LEVEL, *normalize.GRADE_LEVELS)
#: Hazırlık sınıfının adı ('HAZIRLIK', 'HAZ', 'HZ'; ASCII'ye katlanmış metinde).
_HAZIRLIK_SOZCUGU: Final = re.compile(r"\bHA?Z(IRLIK)?\b")


def sinif_metni(value: Any) -> str | None:
    """Öğrencinin sınıfının saklanan yazımı ("10-A", "Hazırlık-B"); boş ya da tanınmazsa None.

    '10/A', '10-A', '10 A', '10A', '10. Sınıf / A Şubesi' → '10-A'; 'Hazırlık/B', 'HZ B' →
    'Hazırlık-B'. Şube harfi Türkçe büyük harfle yazılır ('10/i' → '10-İ'; I ve İ iki ayrı
    şubedir, `normalize.tr_upper`). Seviye 1-12 ya da hazırlıktır.
    """
    metin = hucre_metni(value)
    if not metin:
        return None
    sade = _SOZCUK.sub(
        lambda m: " " if _ascii_upper(m.group()) in _DOLGU_SOZCUKLERI else m.group(),
        metin,
    )
    cozulen = normalize.normalize_class_section(sade, valid_levels=_HAZIRLIK_SEVIYELERI)
    if cozulen is None:
        return None
    seviye, sube = cozulen
    if not sube or len(sube) > _SUBE_EN_COK:
        return None
    # Hazırlık yalnız adıyla tanınır: "0-A" hazırlık sayılmaz (sıfırıncı sınıf yoktur).
    if seviye == normalize.PREP_LEVEL and not _HAZIRLIK_SOZCUGU.search(_ascii_upper(sade)):
        return None
    on = HAZIRLIK if seviye == normalize.PREP_LEVEL else str(seviye)
    return f"{on}-{sube}"


def sinif_sira_anahtari(sinif: str) -> tuple[int, tuple[tuple[int, int], ...]]:
    """Sınıfların gösterim sırası: hazırlık, 1, 2, … 12; şube Türk alfabesiyle."""
    on, _, sube = sinif.partition("-")
    seviye = normalize.PREP_LEVEL if on == HAZIRLIK else int(on) if on.isdigit() else 99
    return seviye, normalize.tr_sort_key(sube)


@dataclass
class ParentColumnMapping:
    """Tespit edilen başlık satırı ve alan → sütun indeksi eşlemesi."""

    header_row: int
    fields: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        return _kullanilir_mi(self.fields)


@dataclass(frozen=True)
class ParsedParentRow:
    """Aktarılabilir bir veli satırı: yalnız iki alan (A3 beyaz listesi)."""

    row_number: int  # 1-tabanlı Excel satır no
    full_name: str
    student_class: str


@dataclass(frozen=True)
class ParentRowIssue:
    """Aktarılamayan satır: satır no, alan kodu ve neden. Hücrenin DEĞERİ YOKTUR."""

    row_number: int
    field: str
    issue: str


def _kullanilir_mi(fields: dict[str, int]) -> bool:
    ad = "full_name" in fields or ("first_name" in fields and "last_name" in fields)
    return ad and "student_class" in fields


def detect_columns(rows: list[list[Any]], scan_limit: int = 10) -> ParentColumnMapping:
    """İlk satırlar içinde başlık satırını bulur; başlıklar birebir eşlenir (`excel_ortak`)."""
    bulunan = basligi_bul(
        rows,
        COLUMN_SYNONYMS,
        kullanilir_mi=_kullanilir_mi,
        scan_limit=scan_limit,
        tam_eslesme=True,
    )
    return ParentColumnMapping(
        header_row=bulunan.header_row, fields=bulunan.fields, warnings=bulunan.warnings
    )


def _ad(cells: list[Any], f: dict[str, int]) -> str:
    """Velinin adı-soyadı: tek sütun ya da ad + soyad; boşluklar tekleşir."""
    if "full_name" in f:
        ham = hucre_metni(hucre(cells, f["full_name"]))
    else:
        ham = (
            f"{hucre_metni(hucre(cells, f.get('first_name')))} "
            f"{hucre_metni(hucre(cells, f.get('last_name')))}"
        )
    return " ".join(ham.split())


def parse_rows(
    rows: list[list[Any]], mapping: ParentColumnMapping
) -> tuple[list[ParsedParentRow], list[ParentRowIssue]]:
    """Başlıktan sonraki satırlar → (aktarılabilir satırlar, satır sorunları); boş satır atlanır."""
    f = mapping.fields
    satirlar: list[ParsedParentRow] = []
    sorunlar: list[ParentRowIssue] = []
    for r in range(mapping.header_row + 1, len(rows)):
        cells = rows[r]
        if bos_satir(cells):
            continue
        satir_no = r + 1
        ad = _ad(cells, f)
        sinif_hucresi = hucre_metni(hucre(cells, f.get("student_class")))
        sinif = sinif_metni(sinif_hucresi)
        if not ad:
            sorunlar.append(ParentRowIssue(satir_no, "full_name", VELI_ADI_BOS))
        elif len(ad) > AD_EN_COK:
            sorunlar.append(ParentRowIssue(satir_no, "full_name", VELI_ADI_UZUN))
        if not sinif_hucresi:
            sorunlar.append(ParentRowIssue(satir_no, "student_class", SINIF_BOS))
        elif sinif is None:
            sorunlar.append(ParentRowIssue(satir_no, "student_class", SINIF_TANINMADI))
        if ad and len(ad) <= AD_EN_COK and sinif is not None:
            satirlar.append(ParsedParentRow(satir_no, ad, sinif))
    return satirlar, sorunlar


def parse_grid(
    grid: list[list[Any]],
) -> tuple[ParentColumnMapping, list[ParsedParentRow], list[ParentRowIssue]]:
    """Matristen (eşleme, satırlar, sorunlar); zorunlu sütun yoksa ParserError (`SUTUN_EKSIK`)."""
    mapping = detect_columns(grid)
    if not mapping.is_usable:
        raise ParserError(SUTUN_EKSIK)
    satirlar, sorunlar = parse_rows(grid, mapping)
    return mapping, satirlar, sorunlar


__all__ = [
    "AD_EN_COK",
    "COLUMN_SYNONYMS",
    "HAZIRLIK",
    "ParentColumnMapping",
    "ParentRowIssue",
    "ParsedParentRow",
    "detect_columns",
    "parse_grid",
    "parse_rows",
    "sinif_metni",
    "sinif_sira_anahtari",
]
