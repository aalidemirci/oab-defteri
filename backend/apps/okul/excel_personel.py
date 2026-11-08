"""Personel Excel'ini okuma: başlık tespiti, esnek sütun eşleme, satır ayrıştırma.

Ailenin `excel_personel.py` dosyasından SADELEŞTİRİLEREK alındı: e-posta ve
Rol/Kapsam çiftleri KALDIRILDI — programda personel hesabı yoktur. Fuzzy başlık
eşleme kalıbı aynen korunur; başlık bulma ve okuma ortak yardımcıdadır (`excel_ortak`).

UNVAN VE BRANŞ SAKLANMAZ (tasarım §5.1 `Personnel`, §8.4): bir branşta çoğu
zaman 1-3 öğretmen olduğundan branş, öğretmeni kişiye bağlar. Bu yüzden:

- **Branş sütunu hiç okunmaz** — eşleme sözlüğünde karşılığı yoktur.
- **"Görevi/Unvan" sütunu** (ya da şablondaki "Üye Türü") YALNIZ üye türünü
  (öğretmen / diğer personel) seçmek için satır ayrıştırılırken geçici okunur.
  Metin `ParsedPersonnelRow`'a GİRMEZ; yalnız sınıflama sonucu girer, dolayısıyla
  rapora, `ImportRun.report`'a ve günlüğe de ulaşamaz (tasarım §8.4: "Görevi"
  yalnız tür için geçici okunur).

Şablon: | Adı | Soyadı | Üye Türü |. e-Okul OOK01001R1: | ADI SOYADI | GÖREVİ | … |.
Eski birleşik ``Ad Soyad`` biçimi de geriye uyum için kabul edilir.
DB yazımı `services/imports.py`'dadır (saf modül — DB'siz, test edilebilir).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.okul import normalize
from apps.okul.excel_ortak import (
    ParserError,
    basligi_bul,
    bos_satir,
    hucre,
    hucre_metni,
    normalize_header,
    read_sheet,
)

#: `models.MemberKind` değerleri (modül Django'suz kalsın diye düz metin; eşitliği
#: `tests/test_excel_personel_parser.py` sabitler).
KIND_TEACHER = "TEACHER"
KIND_STAFF = "STAFF"

# Mantıksal alan → normalize edilmiş başlık anahtar kelimeleri (ilk eşleşen kazanır).
# "role" sütununun METNİ saklanmaz; yalnız `classify_member_kind` sonucuna dönüşür.
COLUMN_SYNONYMS: dict[str, list[str]] = {
    "full_name": ["ad soyad", "adi soyadi", "ad ve soyad", "adsoyad", "ad soyadi", "isim"],
    "last_name": ["personel soyadi", "soyadi"],
    "first_name": ["personel adi", "adi"],
    "role": ["uye turu", "unvan", "gorev", "gorevi"],
}

#: Öğretmen sayılan görevler (kelime başı eşleşmesi; ASCII'ye katlanmış metinde).
#: Okul yöneticileri (müdür, müdür yardımcısı) öğretmen kökenlidir; rehberlik
#: servisi (rehber öğretmen, psikolojik danışman) ve usta öğretici de öğretmendir.
_TEACHER_KEYWORDS: tuple[str, ...] = (
    "ogretmen",
    "ogretici",
    "mudur",
    "rehber",
    "danisman",
)

#: Diğer personel sayılan görevler.
_STAFF_KEYWORDS: tuple[str, ...] = (
    "memur",
    "hizmetli",
    "teknisyen",
    "tekniker",
    "asci",
    "bekci",
    "sef",
    "sekreter",
    "sofor",
    "isci",
    "kalorifer",
    "temizlik",
    "guvenlik",
    "muhasebe",
    "ambar",
    "laborant",
    "isletmen",
    "personel",
    "diger",
)


def classify_member_kind(value: Any) -> str | None:
    """Görev metninden üye türü: `KIND_TEACHER`, `KIND_STAFF` ya da tanınmadıysa None.

    Anahtar kelimeler kelime BAŞINDAN eşleşir ("müdürü", "memuru" de tanınır).
    Öğretmen anahtarı önceliklidir ("Rehber Öğretmen", "Müdür Yardımcısı").
    Boş ya da tanınmayan metin None döner — çağıran öğretmen varsayar ve
    önizlemede "Üye türünü denetleyin" uyarısı verir. Metnin kendisi hiçbir yere
    yazılmaz.
    """
    kelimeler = normalize_header(value).split()
    if not kelimeler:
        return None

    def _var(anahtarlar: tuple[str, ...]) -> bool:
        return any(k.startswith(a) for k in kelimeler for a in anahtarlar)

    if _var(_TEACHER_KEYWORDS):
        return KIND_TEACHER
    if _var(_STAFF_KEYWORDS):
        return KIND_STAFF
    return None


@dataclass
class PersonnelColumnMapping:
    """Tespit edilen başlık satırı ve alan → kolon indeksi eşlemesi."""

    header_row: int
    fields: dict[str, int] = field(default_factory=dict)
    matched_headers: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def missing_critical(self) -> list[str]:
        has_combined_name = "full_name" in self.fields
        has_split_name = "first_name" in self.fields and "last_name" in self.fields
        return (
            [] if has_combined_name or has_split_name else ["full_name veya first_name+last_name"]
        )

    @property
    def is_usable(self) -> bool:
        return not self.missing_critical


@dataclass
class ParsedPersonnelRow:
    """Bir personel satırının çözümlenmiş hâli. Görev METNİ BURADA YOKTUR."""

    row_number: int  # 1-tabanlı Excel satır no
    raw_full_name: str = ""
    first_name: str = ""
    last_name: str = ""
    #: Görev sütunundan çıkarılan üye türü; sütun yoksa ya da tanınmadıysa None.
    member_kind: str | None = None
    #: Görev sütunu VAR ama bu satırın görevi tanınmadı (boş hücre dahil).
    member_kind_unrecognized: bool = False


def _kullanilir_mi(fields: dict[str, int]) -> bool:
    """Ad sütunu var mı (birleşik ad-soyad ya da ayrı ad ve soyad)?"""
    return "full_name" in fields or ("first_name" in fields and "last_name" in fields)


def detect_columns(rows: list[list[Any]], scan_limit: int = 10) -> PersonnelColumnMapping:
    """İlk satırlar içinde en iyi başlık satırını bulur ve sütunları eşler (`excel_ortak`)."""
    bulunan = basligi_bul(
        rows, COLUMN_SYNONYMS, kullanilir_mi=_kullanilir_mi, scan_limit=scan_limit
    )
    return PersonnelColumnMapping(
        header_row=bulunan.header_row,
        fields=bulunan.fields,
        matched_headers=bulunan.matched_headers,
        warnings=bulunan.warnings,
    )


def parse_rows(rows: list[list[Any]], mapping: PersonnelColumnMapping) -> list[ParsedPersonnelRow]:
    """Başlık satırından sonraki veri satırlarını çözümler (boş satırlar atlanır)."""
    f = mapping.fields
    has_role = "role" in f
    parsed: list[ParsedPersonnelRow] = []
    for r in range(mapping.header_row + 1, len(rows)):
        cells = rows[r]
        if bos_satir(cells):
            continue

        raw_name = hucre_metni(hucre(cells, f.get("full_name")))
        if raw_name:
            first, last = normalize.split_full_name(raw_name)
        else:
            first = hucre_metni(hucre(cells, f.get("first_name")))
            last = hucre_metni(hucre(cells, f.get("last_name")))
            raw_name = f"{first} {last}".strip()
        # Görev metni yalnız bu satırda, sınıflama için okunur; değişkene bile alınmaz.
        kind = classify_member_kind(hucre(cells, f.get("role"))) if has_role else None
        parsed.append(
            ParsedPersonnelRow(
                row_number=r + 1,
                raw_full_name=raw_name,
                first_name=first,
                last_name=last,
                member_kind=kind,
                member_kind_unrecognized=has_role and kind is None,
            )
        )
    return parsed


def parse_workbook(file_bytes: bytes) -> tuple[PersonnelColumnMapping, list[ParsedPersonnelRow]]:
    """Baytlardan (mapping, satırlar) üretir; kritik sütun yoksa ParserError."""
    grid = read_sheet(file_bytes)
    mapping = detect_columns(grid)
    if not mapping.is_usable:
        eksik = ", ".join(mapping.missing_critical)
        raise ParserError(f"Zorunlu sütun(lar) bulunamadı: {eksik}.")
    return mapping, parse_rows(grid, mapping)


# read_sheet `excel_ortak`'tan yeniden kullanılır (etkin sayfa, salt-okunur).
__all__ = [
    "KIND_STAFF",
    "KIND_TEACHER",
    "ParsedPersonnelRow",
    "PersonnelColumnMapping",
    "classify_member_kind",
    "detect_columns",
    "parse_rows",
    "parse_workbook",
    "read_sheet",
]
