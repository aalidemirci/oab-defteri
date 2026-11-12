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
   özeti verir (§9.1-2): `belge_coz` kanonik JSON'u modele geri çevirir, geri
   çevrilen modelin kanonik JSON'u kayıtlı metnin AYNISIDIR (değilse ret;
   `apps.oab.models.GeneratedDocument.content_json`).
3. **Türkçe büyük harf verinin kendisindedir** (`shared.text.tr_upper`); iki
   çizici de harf dönüştürmez (`text-transform`, `w:caps` yok).

Konum cümlesi (§9.2) gövdenin sonunda, imza bloğunun HEMEN üstündedir; model
bunu kurarken denetler. Dipnot (`Dipnot`; tasarım §9.1-5 kişisel veri dipnotu) belgenin EN
SONUNDADIR: ardından yalnız başka dipnot gelebilir (model denetler). Kısaltmanın açılımı dipnota
konmaz: kısaltma ilk geçtiği yerde açık biçimiyle yazılır (sözlük §3 "Kısaltma", RYUE md. 16/11).
Altlık değildir: iki çizicide gövdenin son paragrafları olarak küçük puntoyla çizilir ve
içerik eşdeğerliğine girer.

BİÇİM KARARLARI (tasarım §9.1-8; plan F1c kararları "Evrak biçimi"): yazı tipi iki çizicide Times
New Roman ölçüsündedir — Word'de adı "Times New Roman" yazılır, gömülmez; PDF'te paketli Liberation
Serif dizer, DejaVu yalnız eksik glif yedeğidir. Gövde 12 punto; 5-7 sütunlu tablo 10 punto
(`tablo_punto`; RYUE md. 7 gerekli hâllerde 9 puntoya izin verir); daha geniş tablo için karar
yoktur, model reddeder. Yazı alanında 9 puntodan küçük metin yoktur (konum cümlesi ve dipnot 9),
altlık 12 punto (RYUE md. 7/1, md. 27; kullanıcı kararı 11.11.2026; `shared.docx.EN_KUCUK_PUNTO`). Tablonun sütun oranı (`Tablo.oranlar`) iki çizicide aynı yüzdeyle çizilir
(`sutun_yuzdeleri`). Bölüm başlığı (`AltBaslik`, "A. Toplantı" gibi) harf dönüştürmez, kendinden
sonraki bloğa bağlıdır. Antet okulundur (`okul_anteti`); birliğin kendi belgeleri antedin altına
"Okul-Aile Birliği" satırını ekler (`birlik_anteti`; ayrı logo yok, kurum kodu antede girmez). Karar
taslağının konum cümlesi tek sabittir (`KDT`, tasarım §9.2), başlıktaki taslak ibaresi
`TASLAK_IBARESI`'dir. İmza bloğunda ad "Ad SOYAD" biçimindedir (`ad_soyad`; RYUE md. 17/2).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path
from typing import Any

from shared.letterhead import BIRLIK_SATIRI, letterhead_authority, letterhead_unit
from shared.text import tr_lower, tr_upper

#: PDF çizicisinin şablonu (`backend/templates` altında).
PDF_SABLONU = "documents/evrak.html"

#: Gövde puntosu (RYUE md. 7: Times New Roman 12; Word'de `shared.docx.GOVDE_PUNTO` aynıdır).
GOVDE_PUNTO = 12
#: 5-7 sütunlu tablonun puntosu (tasarım §9.1-8 "Punto"; plan F1c kararları "Evrak biçimi").
GENIS_TABLO_PUNTO = 10
#: Gövde puntosuyla çizilen tablonun en çok sütunu ve punto kararı olan en geniş tablo.
DAR_TABLO_EN_COK = 4
GENIS_TABLO_EN_COK = 7

#: Karar taslağının konum cümlesi (tasarım §9.2 KDT; Yönetmelik md. 13/5, 23/2). BİREBİR.
KDT = (
    "Bu metin yönetim kurulu karar taslağıdır. Kararlar noterce tasdikli yönetim kurulu karar "
    "defterine el ile yazılarak imzalanır; bu belge karar defterinin yerine geçmez."
)
#: KDT taşıyan belgenin başlığındaki ibare (tasarım §9.2); "deftere işlendi" işaretinden sonra da
#: kalkmaz.
TASLAK_IBARESI = "TASLAK — karar defterine geçirilecek metin"


@dataclass(frozen=True)
class Antet:
    """Resmî antet (RYUE md. 10; `shared.letterhead` bağlamından)."""

    tc: str
    authority: str
    unit_line: str
    #: Birliğin kendi belgelerinde antedin altına eklenen satır (§9.1-8; `birlik_anteti`).
    alt_birim: str = ""


@dataclass(frozen=True)
class Baslik:
    """Belge başlığı. Metin büyük harfe `tr_upper` ile çevrilerek saklanır."""

    metin: str
    alt: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "metin", tr_upper(self.metin))


@dataclass(frozen=True)
class AltBaslik:
    """Bölüm başlığı ("A. Toplantı" gibi). Harf dönüştürülmez; çizicide sonraki bloğa bağlıdır."""

    metin: str


@dataclass(frozen=True)
class Paragraf:
    metin: str


@dataclass(frozen=True)
class Tablo:
    """Veri tablosu. `oranlar` verilirse sütun genişliklerinin göreli payıdır (pozitif tamsayı, sütun
    başına bir); verilmezse sütunlar eşittir. Punto sütun sayısından çıkar (`tablo_punto`)."""

    basliklar: tuple[str, ...]
    satirlar: tuple[tuple[str, ...], ...]
    oranlar: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        tablo_punto(len(self.basliklar))
        for satir in self.satirlar:
            if len(satir) != len(self.basliklar):
                raise ValueError("Tablo satırı başlık sayısıyla aynı sayıda hücre taşımalı.")
        if self.oranlar:
            if len(self.oranlar) != len(self.basliklar):
                raise ValueError("Tablonun sütun oranı her sütun için bir pay taşımalı.")
            if any(type(pay) is not int or pay <= 0 for pay in self.oranlar):
                raise ValueError("Tablonun sütun oranı pozitif tamsayılardan oluşur.")


def tablo_punto(sutun_sayisi: int) -> int:
    """Tablonun puntosu: 1-4 sütunda gövde puntosu (12), 5-7 sütunda 10 (tasarım §9.1-8).

    Sütunsuz ya da 7'den geniş tablo için biçim kararı yoktur: `ValueError` (çağıran tabloyu böler
    ya da karar alınır; altın kural 1).
    """
    if sutun_sayisi < 1:
        raise ValueError("Tablo en az bir sütun taşımalı.")
    if sutun_sayisi <= DAR_TABLO_EN_COK:
        return GOVDE_PUNTO
    if sutun_sayisi <= GENIS_TABLO_EN_COK:
        return GENIS_TABLO_PUNTO
    raise ValueError(
        f"{GENIS_TABLO_EN_COK} sütundan geniş tablo için evrak biçimi kararı yok (tasarım §9.1-8)."
    )


def sutun_yuzdeleri(tablo: Tablo) -> tuple[float, ...]:
    """Sütun genişlikleri, yazı alanının yüzdesi olarak (iki çizicinin ortak hesabı).

    Oran yoksa sütunlar eşittir. Yüzdeler iki ondalığa yuvarlanır; toplam 100'den en çok yuvarlama
    payı kadar sapar.
    """
    paylar = tablo.oranlar or (1,) * len(tablo.basliklar)
    toplam = sum(paylar)
    return tuple(round(pay * 100 / toplam, 2) for pay in paylar)


@dataclass(frozen=True)
class KonumCumlesi:
    """Programın konumunu söyleyen cümle (§9.2: KDT, TFB, DFT kalıpları)."""

    metin: str


@dataclass(frozen=True)
class Dipnot:
    """Belgenin sonundaki dipnot (tasarım §9.1-5; plan F1b-2 "E63 hesap teslim pusulası").

    Gövdenin en sonunda, imza bloğundan sonra durur; ardından yalnız başka dipnot gelebilir
    (`Belge` denetler). Gövdeden küçük, 9 puntoyla çizilir (RYUE md. 7/1'in yazı alanı alt sınırı;
    kullanıcı kararı 11.11.2026; `shared.docx.DIPNOT_PUNTO`); altlık değildir, metin akışına girer.
    """

    metin: str


#: Kişi adı taşıyan iç belgelerin dipnotu (tasarım §9.1-5; sözlük §1 "Hesap teslim pusulası").
KISISEL_VERI_DIPNOTU = "Kişisel veri içerir — asılmaz, okul dışına verilmez."


def ad_soyad(ad: str, soyad: str) -> str:
    """İmza bloğundaki ad: "Ad SOYAD" (RYUE md. 17/2: adın ilk harfi büyük diğerleri küçük, soyadı
    büyük harflerle).

    Türkçe harf kuralı `tr_upper`/`tr_lower`'dandır (çıplak `.upper()` yok); fazla boşluk katlanır,
    her ad sözcüğü ayrı büyür ("ayşe nur" → "Ayşe Nur"). Soyadı boşsa yalnız ad döner.
    """
    adlar = " ".join(tr_upper(sozcuk[:1]) + tr_lower(sozcuk[1:]) for sozcuk in ad.split())
    return " ".join(parca for parca in (adlar, tr_upper(" ".join(soyad.split()))) if parca)


@dataclass(frozen=True)
class ImzaSahibi:
    ad: str
    gorev: str


@dataclass(frozen=True)
class Imza:
    sahipler: tuple[ImzaSahibi, ...]
    tarih: str = ""


Blok = Baslik | AltBaslik | Paragraf | Tablo | KonumCumlesi | Imza | Dipnot

_BLOK_TURLERI: dict[str, type[Any]] = {
    "baslik": Baslik,
    "alt_baslik": AltBaslik,
    "paragraf": Paragraf,
    "tablo": Tablo,
    "konum": KonumCumlesi,
    "imza": Imza,
    "dipnot": Dipnot,
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
        dipnot_basladi = False
        for sira, blok in enumerate(self.bloklar):
            if isinstance(blok, Dipnot):
                dipnot_basladi = True
            elif dipnot_basladi:
                raise ValueError(
                    "Dipnot belgenin sonunda durur; ardından yalnız başka dipnot gelebilir."
                )
            if isinstance(blok, KonumCumlesi):
                sonraki = self.bloklar[sira + 1] if sira + 1 < len(self.bloklar) else None
                if not isinstance(sonraki, Imza):
                    raise ValueError(
                        "Konum cümlesi gövdenin sonunda, imza bloğunun hemen üstünde olmalı "
                        "(tasarım §9.2)."
                    )


# ---------------------------------------------------------------------------
# Antet (tasarım §9.1-8 "Birlik antedi"; `shared.letterhead`)
# ---------------------------------------------------------------------------


def okul_anteti(*, okul_adi: str, ilce: str | None) -> Antet:
    """Okul antedi: "T.C." · "<İLÇE> KAYMAKAMLIĞI" · "<Okul Adı> Müdürlüğü" (RYUE md. 10).

    Okul idaresinin yazıları ve program belgeleri (E63) bunu kullanır. Kurum kodu basılmaz (plan F1c
    kararları).
    """
    return Antet(
        tc="T.C.", authority=letterhead_authority(ilce), unit_line=letterhead_unit(okul_adi)
    )


def birlik_anteti(*, okul_adi: str, ilce: str | None) -> Antet:
    """Birliğin kendi belgelerinin antedi: okul antedi + "Okul-Aile Birliği" satırı (§9.1-8)."""
    return replace(okul_anteti(okul_adi=okul_adi, ilce=ilce), alt_birim=BIRLIK_SATIRI)


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
    return metin_ozeti(kanonik_json(belge))


def metin_ozeti(json_metni: str) -> str:
    """Kanonik JSON metninin SHA-256'sı (kayıtlı içeriğin özeti; `icerik_ozeti`'nin eşi)."""
    return hashlib.sha256(json_metni.encode("utf-8")).hexdigest()


class BelgeCozulemedi(ValueError):
    """Kayıtlı içerik JSON'u modele geri çevrilemedi ya da kanonik biçimi tutmuyor."""

    def __init__(self) -> None:
        super().__init__(
            "Kayıtlı evrak içeriği okunamadı; belge yeniden basılmadı (kayıt bozulmuş olabilir)."
        )


def _alanlar(tur: type[Any], veri: Any) -> dict[str, Any]:
    """`veri` `tur`'un alanlarıyla birebir eşleşmeli (fazla ya da eksik alan ret)."""
    if not isinstance(veri, dict) or set(veri) != {f.name for f in fields(tur)}:
        raise BelgeCozulemedi()
    return veri


def _metin_alanlari(tur: type[Any], veri: Any) -> dict[str, str]:
    alanlar = _alanlar(tur, veri)
    if not all(isinstance(deger, str) for deger in alanlar.values()):
        raise BelgeCozulemedi()
    return alanlar


def _metinler(veri: Any) -> tuple[str, ...]:
    if not isinstance(veri, list) or not all(isinstance(oge, str) for oge in veri):
        raise BelgeCozulemedi()
    return tuple(veri)


def _blok_coz(veri: Any) -> Blok:
    if not isinstance(veri, dict):
        raise BelgeCozulemedi()
    tur = _BLOK_TURLERI.get(veri.get("tur"))  # type: ignore[arg-type]
    if tur is None:
        raise BelgeCozulemedi()
    alanlar = _alanlar(tur, {ad: deger for ad, deger in veri.items() if ad != "tur"})
    if tur is Tablo:
        satirlar, oranlar = alanlar["satirlar"], alanlar["oranlar"]
        if not isinstance(satirlar, list) or not isinstance(oranlar, list):
            raise BelgeCozulemedi()
        if not all(type(pay) is int for pay in oranlar):
            raise BelgeCozulemedi()
        return Tablo(
            basliklar=_metinler(alanlar["basliklar"]),
            satirlar=tuple(_metinler(satir) for satir in satirlar),
            oranlar=tuple(oranlar),
        )
    if tur is Imza:
        sahipler = alanlar["sahipler"]
        if not isinstance(sahipler, list) or not isinstance(alanlar["tarih"], str):
            raise BelgeCozulemedi()
        return Imza(
            sahipler=tuple(ImzaSahibi(**_metin_alanlari(ImzaSahibi, sahip)) for sahip in sahipler),
            tarih=alanlar["tarih"],
        )
    blok: Blok = tur(**_metin_alanlari(tur, alanlar))
    return blok


def belge_coz(json_metni: str) -> Belge:
    """Kanonik JSON'u içerik modeline geri çevirir (yeniden basım; tasarım §9.1-2, §6.2-6).

    Kayıtlı metin kanonik biçimdedir: geri çevrilen modelin `kanonik_json`'u metnin AYNISI olmalıdır.
    Değilse (alan eklenmiş ya da eksilmiş, sırası ya da biçimi değişmiş, model kuralını bozan içerik)
    `BelgeCozulemedi`: yeniden basım kayıtlı özeti verir ya da hiç basılmaz.
    """
    try:
        veri = json.loads(json_metni)
        if not isinstance(veri, dict) or set(veri) != {"kod", "antet", "bloklar"}:
            raise BelgeCozulemedi()
        if not isinstance(veri["kod"], str) or not isinstance(veri["bloklar"], list):
            raise BelgeCozulemedi()
        belge = Belge(
            kod=veri["kod"],
            antet=Antet(**_metin_alanlari(Antet, veri["antet"])),
            bloklar=tuple(_blok_coz(blok) for blok in veri["bloklar"]),
        )
    except (TypeError, ValueError):  # JSONDecodeError ve model kuralları da ValueError'dır
        raise BelgeCozulemedi() from None
    if kanonik_json(belge) != json_metni:
        raise BelgeCozulemedi()
    return belge


def metin_akisi(belge: Belge) -> list[str]:
    """Modelin kanonik metin akışı — iki çizicinin çıktısı buna eşit olmalıdır.

    Sıra: antet satırları, sonra bloklar belge sırasıyla; tablo başlık ve
    hücreleri satır satır; imzada tarih, sonra her sahibin adı ve görevi; dipnotlar
    en sonda. Boş metinler akışa girmez.
    """
    akis = [belge.antet.tc, belge.antet.authority, belge.antet.unit_line, belge.antet.alt_birim]
    for blok in belge.bloklar:
        if isinstance(blok, Baslik):
            akis += [blok.metin, blok.alt]
        elif isinstance(blok, AltBaslik | Paragraf | KonumCumlesi | Dipnot):
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
    ayarı kullanılır. İlk dipnot (`ilk_dipnot`) gövdeden ince bir çizgiyle ayrılır. Antedin birlik
    satırı (`alt_birim`) taban şablonun antet bloğunda, birim satırının altındadır. Tablonun puntosu
    ve sütun yüzdeleri burada hesaplanır (`tablo_punto`, `sutun_yuzdeleri`); Word çizicisi aynı
    işlevleri çağırır.
    """
    ilk_dipnot = next((b for b in belge.bloklar if isinstance(b, Dipnot)), None)
    baglam = {
        "belge": belge,
        "tc": belge.antet.tc,
        "authority": belge.antet.authority,
        "unit_line": belge.antet.unit_line,
        "alt_birim": belge.antet.alt_birim,
        "bloklar": [_html_ogesi(blok, ilk=blok is ilk_dipnot) for blok in belge.bloklar],
    }
    if sablonlar is not None:
        from django.template import Context, Engine

        motor = Engine(dirs=[str(sablonlar)])
        return motor.get_template(PDF_SABLONU).render(Context(baglam))
    from django.template.loader import render_to_string

    return render_to_string(PDF_SABLONU, baglam)


def _html_ogesi(blok: Blok, *, ilk: bool) -> dict[str, Any]:
    oge: dict[str, Any] = {"tur": _TUR_ADI[type(blok)], "blok": blok, "ilk_dipnot": ilk}
    if isinstance(blok, Tablo):
        oge["punto"] = tablo_punto(len(blok.basliklar))
        # CSS'te ondalık ayracı noktadır; şablonun yerel sayı biçimine (virgül) bırakılmaz.
        oge["genislikler"] = [f"{yuzde:.2f}%" for yuzde in sutun_yuzdeleri(blok)]
    return oge


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
        elif isinstance(blok, AltBaslik):
            cizici.alt_baslik(d, blok.metin)
        elif isinstance(blok, Paragraf):
            cizici.paragraf(d, blok.metin)
        elif isinstance(blok, KonumCumlesi):
            cizici.paragraf(d, blok.metin, punto=cizici.KONUM_PUNTO)
        elif isinstance(blok, Tablo):
            cizici.tablo(
                d,
                blok.basliklar,
                blok.satirlar,
                punto=tablo_punto(len(blok.basliklar)),
                yuzdeler=sutun_yuzdeleri(blok),
            )
        elif isinstance(blok, Imza):
            cizici.imza(d, blok.tarih, [(sahip.ad, sahip.gorev) for sahip in blok.sahipler])
        elif isinstance(blok, Dipnot):
            cizici.dipnot(d, blok.metin)

    cizici.altlik_yaz(d, belge.kod)
    return cizici.kaydet(d)


# ---------------------------------------------------------------------------
# Teşhis belgesi
# ---------------------------------------------------------------------------

#: Türkçe'ye özgü altı harf, büyük ve küçük (PDF duman testinin örneğiyle aynı).
TURKCE_ORNEK = "ĞÜŞİÖÇ ığüşiöç"


def ornek_belge() -> Belge:
    """Duman testi ve eşdeğerlik testi için örnek belge. Bütün adlar UYDURMADIR.

    Hattın bütün blok türlerini taşır: birlik antedi, başlık, bölüm başlığı, dar (12 punto) ve
    geniş (5 sütun, 10 punto) tablo, sütun oranı, KDT, "Ad SOYAD" imza ve dipnot.
    """
    return Belge(
        kod="DUMAN",
        antet=birlik_anteti(okul_adi="Örnek Ortaokulu", ilce="Örnek İlçe"),
        bloklar=(
            Baslik("evrak hattı duman testi", alt="OAB Defteri — paket doğrulama belgesi"),
            AltBaslik("A. Türkçe örnek"),
            Paragraf(f"Türkçe örnek: {TURKCE_ORNEK}. İzmir, Iğdır, Şırnak, Çığır."),
            Tablo(
                basliklar=("Sıra", "Açıklama", "Tutar"),
                satirlar=(
                    ("1", "Kırtasiye gideri", "1.250,00"),
                    ("2", "İçme suyu", "480,50"),
                ),
                oranlar=(1, 4, 2),
            ),
            AltBaslik("B. Geniş tablo"),
            Tablo(
                basliklar=("Sıra", "Görev", "Ad ve soyadı", "Koltuk", "Başlangıç"),
                satirlar=(("1", "Başkan", "Ayşe ÖRNEK", "Veli", "01.11.2026"),),
                oranlar=(1, 3, 4, 2, 3),
            ),
            Paragraf("Bu belge paketin evrak üretim zincirini sınar; veritabanına dokunmaz."),
            KonumCumlesi(KDT),
            Imza(
                tarih="01.11.2026",
                sahipler=(
                    ImzaSahibi(ad_soyad("ayşe", "örnek"), "Birlik Başkanı"),
                    ImzaSahibi(ad_soyad("İsmail", "Deneme"), "Sekreter"),
                ),
            ),
            Dipnot(KISISEL_VERI_DIPNOTU),
        ),
    )
