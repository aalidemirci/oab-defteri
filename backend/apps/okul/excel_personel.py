"""Personel Excel'ini okuma: başlık tespiti, esnek sütun eşleme, satır ayrıştırma.

Ailenin `excel_personel.py` dosyasından SADELEŞTİRİLEREK alındı: e-posta ve
Rol/Kapsam çiftleri KALDIRILDI — programda personel hesabı yoktur. Fuzzy başlık
eşleme kalıbı aynen korunur; başlık bulma ve okuma ortak yardımcıdadır (`excel_ortak`).

UNVAN VE BRANŞ SAKLANMAZ (tasarım §5.1 `Personnel`, §8.4): bir branşta çoğu
zaman 1-3 öğretmen olduğundan branş, öğretmeni kişiye bağlar. Bu yüzden:

- **Branş sütunu hiç okunmaz** — eşleme sözlüğünde karşılığı yoktur.
- **"Unvan" sütunu hiç okunmaz** (tasarım §8.4 okunmayanlar).
- **e-Okul'un "Görevi" sütunu** (ya da şablondaki "Görev Türü") YALNIZ görev türünü
  (öğretmen · yönetici · diğer personel) seçmek için satır ayrıştırılırken geçici okunur.
  Metin `ParsedPersonnelRow`'a GİRMEZ; yalnız sınıflama sonucu girer, dolayısıyla
  rapora, `ImportRun.report`'a ve günlüğe de ulaşamaz (tasarım §8.4: "Görevi"
  yalnız tür için geçici okunur).

Şablon: | Adı | Soyadı | Görev Türü |. e-Okul OOK01001R1: | ADI SOYADI | GÖREVİ | … |.
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
KIND_OGRETMEN = "OGRETMEN"
KIND_YONETICI = "YONETICI"
KIND_DIGER = "DIGER"

# Mantıksal alan → normalize edilmiş başlık anahtar kelimeleri (ilk eşleşen kazanır; eşleşme
# başlığın İÇİNDE aranır, bu yüzden "gorev turu" "gorev"den ÖNCE gelir). "kind" okulun
# şablonundaki "Görev Türü" sütunudur ("Üye Türü": 5. adımdan önce indirilmiş şablon);
# "role" e-Okul'un "Görevi" sütunudur. İkisinin de METNİ saklanmaz, yalnız türe dönüşür.
# "Unvan" sütunu OKUNMAZ (tasarım §8.4 okunmayanlar): eşleme sözlüğünde karşılığı yoktur.
COLUMN_SYNONYMS: dict[str, list[str]] = {
    "full_name": ["ad soyad", "adi soyadi", "ad ve soyad", "adsoyad", "ad soyadi", "isim"],
    "last_name": ["personel soyadi", "soyadi"],
    "first_name": ["personel adi", "adi"],
    "kind": ["gorev turu", "uye turu"],
    "role": ["gorevi", "gorev"],
}

#: Alanların kullanıcıya görünen adları (yinelenen başlık uyarısı; `excel_ortak.basligi_bul`).
ALAN_ADLARI: dict[str, str] = {
    "full_name": "Ad-soyad",
    "last_name": "Soyadı",
    "first_name": "Adı",
    "kind": "Görev türü",
    "role": "Görevi",
}
#: Ad sütunu bulunamadığında (ParserError; iç alan anahtarı kullanıcıya gösterilmez).
AD_SUTUNU_EKSIK = "“Adı Soyadı” (ya da ayrı “Adı” ve “Soyadı”)"

#: e-Okul'un "Görevi" sütununda yönetici sayılan görevler — Türkçe katlanmış TAM eşleşme
#: (plan "F1b-5 uygulama kararları": Müdür, Müdür Başyardımcısı, Müdür Yardımcısı).
_YONETICI_GOREVLERI: frozenset[str] = frozenset(
    {"mudur", "mudur basyardimcisi", "mudur yardimcisi"}
)
#: İçinde geçtiğinde görevi öğretmen yapan sözcük (katlanmış; "Ücretli Öğretmen", "Rehber
#: Öğretmen", "Sözleşmeli Öğretmen(657 S.K. 4/B)").
_OGRETMEN_SOZCUGU = "ogretmen"
#: Yönetici ya da öğretmen görevine benzeyip yukarıdaki tam eşleşmelere uymayan görevlerin
#: sözcükleri (katlanmış; "Okul Müdürü", "Müdür Yrd.", "Müdür Yardımcısı Vekili", "Psikolojik
#: Danışman", "Usta Öğretici"). Sınıflamayı DEĞİŞTİRMEZ (kullanıcı kararı harfiyen uygulanır);
#: yalnız önizlemede "Görev türünü denetleyin" uyarısı verdirir (`gorev_denetlenmeli`).
_DENETLENECEK_SOZCUKLER: tuple[str, ...] = ("mudur", "danisman", "ogretici")

#: Şablonun "Görev Türü" sütununun kabul ettiği değerler (katlanmış tam eşleşme; arayüz
#: etiketleri, sözlük "Personelin türü"). "Diğer" kısa yazımı da kabul edilir.
_SABLON_TURLERI: dict[str, str] = {
    "ogretmen": KIND_OGRETMEN,
    "yonetici": KIND_YONETICI,
    "diger personel": KIND_DIGER,
    "diger": KIND_DIGER,
}


def classify_member_kind(value: Any) -> str | None:
    """e-Okul "Görevi" metninden görev türü; hücre boşsa None.

    Sınıflama (plan "F1b-5 uygulama kararları"; metin Türkçe katlanır, büyük/küçük harf ve
    fazla boşluk önemsizdir): Müdür, Müdür Başyardımcısı ve Müdür Yardımcısı (tam eşleşme)
    yönetici; içinde "öğretmen" geçen görev öğretmen; öteki her görev diğer personel. Boş
    hücre None döner — çağıran öğretmen varsayar ve önizlemede "Görev türünü denetleyin"
    uyarısı verir. Metnin kendisi hiçbir yere yazılmaz.
    """
    katlanmis = normalize_header(value)
    if not katlanmis:
        return None
    if katlanmis in _YONETICI_GOREVLERI:
        return KIND_YONETICI
    if _OGRETMEN_SOZCUGU in katlanmis:
        return KIND_OGRETMEN
    return KIND_DIGER


def gorev_denetlenmeli(value: Any) -> bool:
    """e-Okul "Görevi" metni yönetici ya da öğretmen görevine benziyor ama tam tanınmadı mı?

    Katlanmış metin "mudur", "danisman" ya da "ogretici" içerip yöneticinin tam eşleşmelerinden
    biri değilse True (ör. "Okul Müdürü" ve "Müdür Yardımcısı Vekili" diğer personel, "Rehber
    Öğretmen (Psikolojik Danışman)" öğretmen sayılır, ama türleri denetlenmeli). Sınıflama
    `classify_member_kind`'dadır ve bundan etkilenmez; metin hiçbir yere yazılmaz.
    """
    katlanmis = normalize_header(value)
    if not katlanmis or katlanmis in _YONETICI_GOREVLERI:
        return False
    return any(sozcuk in katlanmis for sozcuk in _DENETLENECEK_SOZCUKLER)


def template_member_kind(value: Any) -> str | None:
    """Şablonun "Görev Türü" hücresinden görev türü; boş ya da tanınmayan değerde None.

    Yalnız üç etiket kabul edilir (öğretmen, yönetici, diğer personel); tanınmayan değer
    tahmin edilmez (yazım hatası "diğer personel"e düşmesin): None döner ve önizlemede
    "Görev türünü denetleyin" uyarısı verilir.
    """
    return _SABLON_TURLERI.get(normalize_header(value))


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
        return [] if has_combined_name or has_split_name else [AD_SUTUNU_EKSIK]

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
    #: Görev ya da görev türü sütunundan çıkarılan görev türü; sütun yoksa, hücre boşsa ya da
    #: şablon değeri tanınmadıysa None.
    member_kind: str | None = None
    #: Görev (türü) sütunu VAR ama bu satırın türü çıkarılamadı (boş hücre dahil).
    member_kind_unrecognized: bool = False
    #: e-Okul "Görevi" metninden tür çıkarıldı ama görev yönetici ya da öğretmen görevine benzeyip
    #: tam tanınmadı (`gorev_denetlenmeli`); tür sınıflamanın verdiğidir, uyarı ayrıdır.
    member_kind_uncertain: bool = False


def _kullanilir_mi(fields: dict[str, int]) -> bool:
    """Ad sütunu var mı (birleşik ad-soyad ya da ayrı ad ve soyad)?"""
    return "full_name" in fields or ("first_name" in fields and "last_name" in fields)


def detect_columns(rows: list[list[Any]], scan_limit: int = 10) -> PersonnelColumnMapping:
    """İlk satırlar içinde en iyi başlık satırını bulur ve sütunları eşler (`excel_ortak`)."""
    bulunan = basligi_bul(
        rows,
        COLUMN_SYNONYMS,
        kullanilir_mi=_kullanilir_mi,
        alan_adlari=ALAN_ADLARI,
        scan_limit=scan_limit,
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
    # Şablonun "Görev Türü" sütunu varsa o esastır; yoksa e-Okul'un "Görevi" sütunu.
    has_kind = "kind" in f
    has_role = has_kind or "role" in f
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
        supheli = False
        if has_kind:
            kind = template_member_kind(hucre(cells, f.get("kind")))
        elif has_role:
            kind = classify_member_kind(hucre(cells, f.get("role")))
            supheli = gorev_denetlenmeli(hucre(cells, f.get("role")))
        else:
            kind = None
        parsed.append(
            ParsedPersonnelRow(
                row_number=r + 1,
                raw_full_name=raw_name,
                first_name=first,
                last_name=last,
                member_kind=kind,
                member_kind_unrecognized=has_role and kind is None,
                member_kind_uncertain=supheli and kind is not None,
            )
        )
    return parsed


def parse_workbook(file_bytes: bytes) -> tuple[PersonnelColumnMapping, list[ParsedPersonnelRow]]:
    """Baytlardan (mapping, satırlar) üretir; kritik sütun yoksa ParserError."""
    grid = read_sheet(file_bytes)
    mapping = detect_columns(grid)
    if not mapping.is_usable:
        eksik = ", ".join(mapping.missing_critical)
        raise ParserError(f"Zorunlu sütun bulunamadı: {eksik}.")
    return mapping, parse_rows(grid, mapping)


# read_sheet `excel_ortak`'tan yeniden kullanılır (etkin sayfa, salt-okunur).
__all__ = [
    "ALAN_ADLARI",
    "KIND_DIGER",
    "KIND_OGRETMEN",
    "KIND_YONETICI",
    "ParsedPersonnelRow",
    "PersonnelColumnMapping",
    "classify_member_kind",
    "detect_columns",
    "gorev_denetlenmeli",
    "parse_rows",
    "parse_workbook",
    "read_sheet",
    "template_member_kind",
]
