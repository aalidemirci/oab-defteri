"""Evrak hattının cephesi — tek içerik, iki çizici (T2; tasarım §9.1, TK17).

Belgenin cümleleri, tabloları ve imza blokları BİR KEZ burada içerik modeli
(`Belge`) olarak kurulur; Word (`shared.docx`, python-docx) ve PDF
(`documents/evrak.html` → `shared.pdf`, WeasyPrint) yalnız düzeni çizer.
LibreOffice ya da Word gerekmez.

Üç sözleşme (tasarım §9.1):

1. **İçerik eşdeğerliği.** İki çıktıdan aynı kanonik metin akışı çıkar
   (`metin_akisi`): gövde blokları belge sırasıyla, tablo hücreleri satır
   satır. Altlık ("OAB Defteri · Exx · Sayfa n/m") akışa girmez (UY-18).
2. **İçerik özeti.** `icerik_ozeti` modelin kanonik JSON'unun SHA-256'sıdır;
   docx zip baytının değil. Yeniden basım kayıtlı JSON'dan çizilir ve aynı
   özeti verir (§9.1-2; `GeneratedDocument` F1c'de).
3. **Türkçe büyük harf verinin kendisindedir** (`shared.text.tr_upper`); iki
   çizici de harf dönüştürmez (`text-transform`, `w:caps` yok).

Konum cümlesi (§9.2) gövdenin sonunda, imza bloğunun HEMEN üstündedir; model
bunu kurarken denetler.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from shared.text import tr_upper

#: PDF çizicisinin şablonu (`backend/templates` altında).
PDF_SABLONU = "documents/evrak.html"


@dataclass(frozen=True)
class Antet:
    """Resmî antet (RYUE md. 10; `shared.letterhead` bağlamından)."""

    tc: str
    authority: str
    unit_line: str
    #: Birliğin kendi belgelerinde antedin altına eklenen satır (§9.1-8).
    alt_birim: str = ""


@dataclass(frozen=True)
class Baslik:
    """Belge başlığı. Metin büyük harfe `tr_upper` ile çevrilerek saklanır."""

    metin: str
    alt: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "metin", tr_upper(self.metin))


@dataclass(frozen=True)
class Paragraf:
    metin: str


@dataclass(frozen=True)
class Tablo:
    basliklar: tuple[str, ...]
    satirlar: tuple[tuple[str, ...], ...]

    def __post_init__(self) -> None:
        for satir in self.satirlar:
            if len(satir) != len(self.basliklar):
                raise ValueError("Tablo satırı başlık sayısıyla aynı sayıda hücre taşımalı.")


@dataclass(frozen=True)
class KonumCumlesi:
    """Programın konumunu söyleyen cümle (§9.2: KDT, TFB, DFT kalıpları)."""

    metin: str


@dataclass(frozen=True)
class ImzaSahibi:
    ad: str
    gorev: str


@dataclass(frozen=True)
class Imza:
    sahipler: tuple[ImzaSahibi, ...]
    tarih: str = ""


Blok = Baslik | Paragraf | Tablo | KonumCumlesi | Imza

_BLOK_TURLERI: dict[str, type[Any]] = {
    "baslik": Baslik,
    "paragraf": Paragraf,
    "tablo": Tablo,
    "konum": KonumCumlesi,
    "imza": Imza,
}
_TUR_ADI = {tur: ad for ad, tur in _BLOK_TURLERI.items()}


@dataclass(frozen=True)
class Belge:
    """Bir evrakın tek içerik modeli."""

    #: Evrak kataloğu kodu (E01…E79, §9.5) ya da teşhis belgesi için "DUMAN".
    kod: str
    antet: Antet
    bloklar: tuple[Blok, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for sira, blok in enumerate(self.bloklar):
            if isinstance(blok, KonumCumlesi):
                sonraki = self.bloklar[sira + 1] if sira + 1 < len(self.bloklar) else None
                if not isinstance(sonraki, Imza):
                    raise ValueError(
                        "Konum cümlesi gövdenin sonunda, imza bloğunun hemen üstünde olmalı "
                        "(tasarım §9.2)."
                    )


# ---------------------------------------------------------------------------
# Kanonik biçimler
# ---------------------------------------------------------------------------


def kanonik_json(belge: Belge) -> str:
    """Modelin kararlı JSON'u: anahtarlar sıralı, boşluksuz, UTF-8 metin."""
    veri = {
        "kod": belge.kod,
        "antet": asdict(belge.antet),
        "bloklar": [{"tur": _TUR_ADI[type(blok)], **asdict(blok)} for blok in belge.bloklar],
    }
    return json.dumps(veri, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def icerik_ozeti(belge: Belge) -> str:
    """İçerik özeti: kanonik JSON'un SHA-256'sı (onaltılık)."""
    return hashlib.sha256(kanonik_json(belge).encode("utf-8")).hexdigest()


def metin_akisi(belge: Belge) -> list[str]:
    """Modelin kanonik metin akışı — iki çizicinin çıktısı buna eşit olmalıdır.

    Sıra: antet satırları, sonra bloklar belge sırasıyla; tablo başlık ve
    hücreleri satır satır; imzada tarih, sonra her sahibin adı ve görevi.
    Boş metinler akışa girmez.
    """
    akis = [belge.antet.tc, belge.antet.authority, belge.antet.unit_line, belge.antet.alt_birim]
    for blok in belge.bloklar:
        if isinstance(blok, Baslik):
            akis += [blok.metin, blok.alt]
        elif isinstance(blok, Paragraf | KonumCumlesi):
            akis.append(blok.metin)
        elif isinstance(blok, Tablo):
            akis += list(blok.basliklar)
            for satir in blok.satirlar:
                akis += list(satir)
        elif isinstance(blok, Imza):
            akis.append(blok.tarih)
            for sahip in blok.sahipler:
                akis += [sahip.ad, sahip.gorev]
    return [parca for parca in akis if parca]


# ---------------------------------------------------------------------------
# Çiziciler
# ---------------------------------------------------------------------------


def html_ciz(belge: Belge, sablonlar: Path | None = None) -> str:
    """PDF çizicisinin HTML'i.

    `sablonlar` verilirse Django ayarı olmadan bağımsız bir şablon motoru
    kurulur (paket teşhis kipi `--evrak-duman`); verilmezse projenin şablon
    ayarı kullanılır.
    """
    baglam = {
        "belge": belge,
        "tc": belge.antet.tc,
        "authority": belge.antet.authority,
        "unit_line": belge.antet.unit_line,
        "bloklar": [{"tur": _TUR_ADI[type(blok)], "blok": blok} for blok in belge.bloklar],
    }
    if sablonlar is not None:
        from django.template import Context, Engine

        motor = Engine(dirs=[str(sablonlar)])
        return motor.get_template(PDF_SABLONU).render(Context(baglam))
    from django.template.loader import render_to_string

    return render_to_string(PDF_SABLONU, baglam)


def pdf_ciz(belge: Belge, sablonlar: Path | None = None) -> bytes:
    """Belgenin PDF'i — WeasyPrint'e `shared.pdf`'in tek kapısından gidilir."""
    from shared.pdf import html_to_pdf

    return html_to_pdf(html_ciz(belge, sablonlar))


def docx_ciz(belge: Belge) -> bytes:
    """Belgenin Word dosyası. python-docx'e yalnız `shared.docx` kapısından gidilir."""
    from shared import docx as cizici

    d = cizici.yeni_belge()
    for satir in (belge.antet.tc, belge.antet.authority, belge.antet.unit_line):
        if satir:
            cizici.ortali_satir(d, satir, kalin=True)
    if belge.antet.alt_birim:
        cizici.ortali_satir(d, belge.antet.alt_birim)

    for blok in belge.bloklar:
        if isinstance(blok, Baslik):
            cizici.ortali_satir(d, blok.metin, kalin=True)
            if blok.alt:
                cizici.ortali_satir(d, blok.alt, punto=10)
        elif isinstance(blok, Paragraf):
            cizici.paragraf(d, blok.metin)
        elif isinstance(blok, KonumCumlesi):
            cizici.paragraf(d, blok.metin, punto=cizici.KONUM_PUNTO)
        elif isinstance(blok, Tablo):
            cizici.tablo(d, blok.basliklar, blok.satirlar)
        elif isinstance(blok, Imza):
            cizici.imza(d, blok.tarih, [(sahip.ad, sahip.gorev) for sahip in blok.sahipler])

    cizici.altlik_yaz(d, belge.kod)
    return cizici.kaydet(d)


# ---------------------------------------------------------------------------
# Teşhis belgesi
# ---------------------------------------------------------------------------

#: Türkçe'ye özgü altı harf, büyük ve küçük (PDF duman testinin örneğiyle aynı).
TURKCE_ORNEK = "ĞÜŞİÖÇ ığüşiöç"


def ornek_belge() -> Belge:
    """Duman testi ve eşdeğerlik testi için örnek belge. Bütün adlar UYDURMADIR."""
    return Belge(
        kod="DUMAN",
        antet=Antet(
            tc="T.C.",
            authority="ÖRNEK İLÇE KAYMAKAMLIĞI",
            unit_line="Örnek Ortaokulu Müdürlüğü",
            alt_birim="Okul-Aile Birliği",
        ),
        bloklar=(
            Baslik("evrak hattı duman testi", alt="OAB Defteri — paket doğrulama belgesi"),
            Paragraf(f"Türkçe örnek: {TURKCE_ORNEK}. İzmir, Iğdır, Şırnak, Çığır."),
            Tablo(
                basliklar=("Sıra", "Açıklama", "Tutar"),
                satirlar=(
                    ("1", "Kırtasiye gideri", "1.250,00"),
                    ("2", "İçme suyu", "480,50"),
                ),
            ),
            Paragraf("Bu belge paketin evrak üretim zincirini sınar; veritabanına dokunmaz."),
            KonumCumlesi(
                "Bu metin yönetim kurulu karar taslağıdır. Kararlar noterce tasdikli yönetim "
                "kurulu karar defterine el ile yazılarak imzalanır; bu belge karar defterinin "
                "yerine geçmez."
            ),
            Imza(
                tarih="01.11.2026",
                sahipler=(
                    ImzaSahibi("Ayşe ÖRNEK", "Birlik Başkanı"),
                    ImzaSahibi("İsmail DENEME", "Sekreter"),
                ),
            ),
        ),
    )
