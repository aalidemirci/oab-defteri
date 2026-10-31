"""Ana marka logosunu ve elle çizilmiş küçük ikon kesimlerini üretir.

Tasarım — "Okul çatısı ve aile" (31.10.2026 kullanıcı kararı; plan §2.2 F1b
adım 0, genel tasarım §13 D31): cilt laciverti, köşeleri yuvarlatılmış bir karo
üzerinde safran bir çatı (kalın, uçları yuvarlak bir ters V) ve aynı safranla bir
taban; çatının altında, tabana basan üç yalın figür — iki yetişkin ve aralarında
daha kısa bir çocuk. Okul ile ailenin bir çatı altında buluşması: okul-aile
birliği. Figürler yuvarlak bir baş ve üstü yuvarlatılmış bir gövdedir; gölge,
degrade ve metin yoktur. Karo, palet ve kenar boşluğu kuralı ailenin öteki
programlarıyla aynıdır; motif yalnız bu programındır (aileden gelen raf ve kitap
logosu F1b'de değişti).

Palet okulapp.org'daki program paletidir: cilt laciverti #1c3259 (karo), safran
#eea23f (çatı, taban), kâğıt #f1f3f8 (yetişkinler); gök mavisi #8fb4ee çocuktur.

Çıktılar (bu dizine; depoya COMMIT EDİLİR):

* ``oab-defteri-logo.png`` — 1024×1024 ana çizim, saydam kenar boşluklu.
  48 px ve üstü kesimleri ``ikon_uret.py`` bundan türetir.
* ``oab-defteri-16.png``, ``-24.png``, ``-32.png`` — ÖLÇEKLENMEZ: piksel
  ızgarasına oturtulmuş ayrı ve sade çizimlerdir. Figürler tam piksele oturan
  dikdörtgenlerdir (başın ve gövde omzunun köşesi bir piksel kırpılır), taban
  düz bir banttır. Çatı 16'da elle dizilmiş iki piksel kalınlığında bir
  merdivendir (çokgen orada bulanık bir leke olur); 24 ve 32'de yumuşatılmış iki
  koldur. ``ikon_uret.py`` bunları olduğu gibi ``.ico``'ya koyar.

Kenar boşluğu (bütün boyutlarda tek kural; ``ikon_uret.py`` 48+ için aynısını
uygular, ``packaging/tests/test_ikonlar.py`` sınar): karo, tuvalin kenarına
⌈boyut/32⌉ px saydam boşluk bırakır — 24 ve 32'de 1 px, 48 ve 64'te 2, 256'da 8,
bu 1024'te 32. Karo doluluğu böylece ~%94'tür (24 ve 48'de tam piksele
yuvarlandığı için %91,7). Gerekçe: Windows bir boyutu tam bulamazsa bir üstünü
küçültür (Microsoft Learn, "Construct your Windows app's icon" → Icon scaling);
ölçek %125'te görev çubuğu 30 px'i elle çizilmiş 32'den, %150'de 36 px'i ana
çizimden (48) alır, Başlat sabitlemesi %100'de 32'yi, %125'te 48'i kullanır.
Pardus'un hicolor temasında da menü 24/32'yi, uygulama ızgarası 48 ve üstünü
seçer. İki aile yan yana geçtiği için doluluğu aynı olmalıdır. Tek istisna
16'dır: 1 px boşluk çizim alanının %23'ünü götürür; 16 kesimi karoyu tuvalin
kenarına dek doldurur. 16'nın ölçekli komşusu olan 20 px (%125'te başlık çubuğu
ve bağlam menüsü) 24'ten küçültülür.

Çalıştırma (depo kökünden, Docker içinde — host'a kurulum YASAK):

    docker compose run --rm -w /repo backend python packaging/ikonlar/logo_uret.py
    docker compose run --rm -w /repo backend python packaging/ikonlar/ikon_uret.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

KLASOR = Path(__file__).resolve().parent
LOGO = KLASOR / "oab-defteri-logo.png"
KENAR = 1024
SS = 4  # süper örnekleme katsayısı (yumuşak kenar için)

Renk = tuple[int, int, int, int]
Nokta = tuple[float, float]

# --- Palet ------------------------------------------------------------------
LACIVERT: Renk = (0x1C, 0x32, 0x59, 255)  # cilt laciverti: karo
SAFRAN: Renk = (0xEE, 0xA2, 0x3F, 255)  # çatı ve taban
KAGIT: Renk = (0xF1, 0xF3, 0xF8, 255)  # yetişkinler
GOK: Renk = (0x8F, 0xB4, 0xEE, 255)  # çocuk

ZEMIN = LACIVERT
CATI = SAFRAN
TABAN = SAFRAN
#: Soldan sağa: yetişkin, çocuk, yetişkin.
FIGUR_RENKLERI: tuple[Renk, Renk, Renk] = (KAGIT, GOK, KAGIT)
RENKLER: dict[str, Renk] = {
    "zemin": ZEMIN,
    "cati": CATI,
    "taban": TABAN,
    "kagit": KAGIT,
    "gok": GOK,
}

# --- 1024 geometrisi (px) -----------------------------------------------------
ZEMIN_PAY = math.ceil(KENAR / 32)  # kenar boşluğu kuralı (başlık): 32 px
ZEMIN_YARICAP = 197  # karo kenarının ~%20,5'i (küçük kesimlerle aynı oran)


@dataclass(frozen=True)
class Figur:
    """Taban üstüne basan figür: yerel x merkezi, gövde (genişlik, yükseklik), baş yarıçapı."""

    merkez_x: float
    govde: tuple[float, float]
    bas_yaricap: float


#: Grup yerel koordinatta kurulur: x = 0 karo ortası, y = 0 taban üstü (yukarı eksi).
FIGURLER: tuple[Figur, Figur, Figur] = (
    Figur(merkez_x=-198, govde=(176, 250), bas_yaricap=66),
    Figur(merkez_x=0, govde=(132, 176), bas_yaricap=52),
    Figur(merkez_x=198, govde=(176, 250), bas_yaricap=66),
)
BAS_BOSLUK = 20  # başın altı ile gövdenin üstü arası

TABAN_YARIM_GENISLIK = 330
TABAN_KALINLIK = 52
TABAN_YARICAP = 18

CATI_YARIM_GENISLIK = 312  # tepe ile kol ucu arası, yatay (kolun orta çizgisi)
CATI_YUKSEKLIK = 214  # tepe ile kol ucu arası, dikey
CATI_KALINLIK = 78
CATI_BOSLUK = 52  # çatının alt yüzü ile yetişkin başı arasındaki en kısa uzaklık
OPTIK_KAYMA = 6  # grubun kütle merkezi aşağıda durduğu için hafif yukarı


def _s(*degerler: float) -> tuple[int, ...]:
    return tuple(round(d * SS) for d in degerler)


def _kol(ciz: ImageDraw.ImageDraw, a: Nokta, b: Nokta, kalinlik: float, renk: Renk) -> None:
    """İki nokta arası, uçları yuvarlak kalın çizgi (süper örneklenmiş tuvalde)."""
    (ax, ay), (bx, by) = a, b
    uzunluk = math.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / uzunluk * kalinlik / 2, (bx - ax) / uzunluk * kalinlik / 2
    ciz.polygon(
        [
            _s(ax + nx, ay + ny),
            _s(bx + nx, by + ny),
            _s(bx - nx, by - ny),
            _s(ax - nx, ay - ny),
        ],
        fill=renk,
    )
    r = kalinlik / 2
    for x, y in (a, b):
        ciz.ellipse(_s(x - r, y - r, x + r, y + r), fill=renk)


def _cati_tepesi(figur: Figur, ust: float) -> float:
    """Yetişkin başını `CATI_BOSLUK` kadar açıkta bırakan en alçak çatı tepesi (yerel y).

    Kolun alt yüzü ile başın merkezi arasındaki uzaklık baş yarıçapı + boşluk
    olmalıdır; kolun orta çizgisi bundan yarım kalınlık kadar yukarıdadır.
    """
    egim = CATI_YUKSEKLIK / CATI_YARIM_GENISLIK
    aci = math.atan(egim)
    bas_y = ust - BAS_BOSLUK - figur.bas_yaricap
    gereken = figur.bas_yaricap + CATI_BOSLUK + CATI_KALINLIK / 2
    # Orta çizgi: y = tepe + |x| * egim; noktanın doğruya dik uzaklığı = (bas_y - y) * cos(aci).
    return bas_y - abs(figur.merkez_x) * egim - gereken / math.cos(aci)


@dataclass(frozen=True)
class _Yerlesim:
    ofset: Nokta  # yerel → tuval
    cati_tepe_y: float  # yerel


def _yerlesim() -> _Yerlesim:
    yetiskin = FIGURLER[0]
    tepe = _cati_tepesi(yetiskin, -yetiskin.govde[1])
    ust = tepe - CATI_KALINLIK / 2
    alt = TABAN_KALINLIK
    oy = KENAR / 2 - (ust + alt) / 2 - OPTIK_KAYMA
    return _Yerlesim(ofset=(KENAR / 2, oy), cati_tepe_y=tepe)


def buyuk() -> Image.Image:
    """1024×1024 ana çizim (saydam kenar boşluğuyla)."""
    tuval = Image.new("RGBA", (KENAR * SS, KENAR * SS), (0, 0, 0, 0))
    ciz = ImageDraw.Draw(tuval)
    ciz.rounded_rectangle(
        (
            ZEMIN_PAY * SS,
            ZEMIN_PAY * SS,
            (KENAR - ZEMIN_PAY) * SS - 1,
            (KENAR - ZEMIN_PAY) * SS - 1,
        ),
        radius=ZEMIN_YARICAP * SS,
        fill=ZEMIN,
    )
    yer = _yerlesim()
    ox, oy = yer.ofset

    # Çatı: tepeden iki kol.
    tepe = (ox, oy + yer.cati_tepe_y)
    for yon in (-1, 1):
        uc = (ox + yon * CATI_YARIM_GENISLIK, oy + yer.cati_tepe_y + CATI_YUKSEKLIK)
        _kol(ciz, tepe, uc, CATI_KALINLIK, CATI)

    # Taban.
    ciz.rounded_rectangle(
        _s(ox - TABAN_YARIM_GENISLIK, oy, ox + TABAN_YARIM_GENISLIK, oy + TABAN_KALINLIK),
        radius=TABAN_YARICAP * SS,
        fill=TABAN,
    )

    # Figürler: gövdenin üstü yarım daire (omuz), altı tabana düz basar.
    for figur, renk in zip(FIGURLER, FIGUR_RENKLERI, strict=True):
        w, h = figur.govde
        x0, x1 = ox + figur.merkez_x - w / 2, ox + figur.merkez_x + w / 2
        ciz.rounded_rectangle(
            _s(x0, oy - h, x1, oy),
            radius=w / 2 * SS,
            fill=renk,
            corners=(True, True, False, False),
        )
        r = figur.bas_yaricap
        by = oy - h - BAS_BOSLUK - r
        bx = ox + figur.merkez_x
        ciz.ellipse(_s(bx - r, by - r, bx + r, by + r), fill=renk)
    return tuval.resize((KENAR, KENAR), Image.Resampling.BOX)


# --- Elle çizilmiş küçük kesimler (piksel ızgarası) -------------------------------
# Koordinatlar tam sayı ve yarı açıktır: (x0, y0, x1, y1) → [x0, x1) × [y0, y1).
# Satır parçası (y, x0, x1) tek satırdır. Renk adları `RENKLER` anahtarlarıdır.
Dikdortgen = tuple[int, int, int, int, str]
Satir = tuple[int, int, int, str]


@dataclass(frozen=True)
class KucukCizim:
    karo: tuple[int, int, int, int]  # kenar boşluğu kuralı (başlık)
    yaricap: float
    #: Tam piksele oturan parçalar (taban, gövdeler, başlar).
    dikdortgenler: tuple[Dikdortgen, ...]
    #: Elle dizilmiş satırlar (16'nın çatısı, kırpılmış köşeler).
    satirlar: tuple[Satir, ...] = ()
    #: Yumuşatılmış çatı: (tepe, sol uç, sağ uç, kalınlık) — piksel cinsinden, 24 ve 32.
    cati: tuple[Nokta, Nokta, Nokta, float] | None = None


def _figur(
    x0: int, x1: int, ust: int, alt: int, bas: tuple[int, int], renk: str
) -> tuple[Satir, ...]:
    """Omuzlu gövde, bir satır boşluk ve üstünde ortalanmış baş.

    Gövde [x0, x1) genişliğinde, [ust, alt) satırlarındadır; ilk satırı iki yandan bir
    piksel içeridedir (omuz). Baş (genişlik, yükseklik) gövdenin ortasındadır; dört ya da
    daha geniş başın ilk ve son satırı iki yandan birer piksel içeridedir (yuvarlak baş).
    Üç piksellik baş kırpılmaz: kırpılınca artı işaretine (sağlık haçı) dönüyordu.
    """
    satirlar: list[Satir] = [(ust, x0 + 1, x1 - 1, renk)]
    satirlar += [(y, x0, x1, renk) for y in range(ust + 1, alt)]
    genislik, yukseklik = bas
    bx0 = x0 + (x1 - x0 - genislik) // 2
    bx1 = bx0 + genislik
    bas_ust = ust - 1 - yukseklik
    for i in range(yukseklik):
        kirp = 1 if i in (0, yukseklik - 1) and genislik >= 4 else 0
        satirlar.append((bas_ust + i, bx0 + kirp, bx1 - kirp, renk))
    return tuple(satirlar)


KUCUK: dict[int, KucukCizim] = {
    16: KucukCizim(
        karo=(0, 0, 16, 16),
        yaricap=3.5,
        dikdortgenler=((1, 13, 15, 14, "taban"),),
        satirlar=(
            # Çatı: iki piksel kalın merdiven, tepe 1. satırda.
            (1, 7, 9, "cati"),
            (2, 6, 10, "cati"),
            (3, 5, 7, "cati"),
            (3, 9, 11, "cati"),
            (4, 4, 6, "cati"),
            (4, 10, 12, "cati"),
            (5, 3, 5, "cati"),
            (5, 11, 13, "cati"),
            (6, 2, 4, "cati"),
            (6, 12, 14, "cati"),
            # Yetişkinler: 2×2 baş, bir satır boşluk, üç satır gövde (omuz kırpık).
            *((y, 4, 6, "kagit") for y in (7, 8, 10)),
            *((y, 3, 7, "kagit") for y in (11, 12)),
            *((y, 10, 12, "kagit") for y in (7, 8, 10)),
            *((y, 9, 13, "kagit") for y in (11, 12)),
            # Çocuk: 2×2 baş yetişkinlerinkinden bir satır aşağıda, iki satır gövde.
            *((y, 7, 9, "gok") for y in (8, 9, 11, 12)),
        ),
    ),
    24: KucukCizim(
        karo=(1, 1, 23, 23),
        yaricap=4.5,
        dikdortgenler=((3, 19, 21, 21, "taban"),),
        satirlar=(
            *_figur(4, 9, 13, 19, (3, 3), "kagit"),
            *_figur(10, 14, 15, 19, (2, 2), "gok"),
            *_figur(15, 20, 13, 19, (3, 3), "kagit"),
        ),
        cati=((12, 3.2), (3.0, 9.0), (21.0, 9.0), 2.2),
    ),
    32: KucukCizim(
        karo=(1, 1, 31, 31),
        yaricap=6.5,
        dikdortgenler=((4, 25, 28, 27, "taban"),),
        satirlar=(
            *_figur(5, 12, 17, 25, (5, 4), "kagit"),
            *_figur(13, 19, 20, 25, (4, 4), "gok"),
            *_figur(20, 27, 17, 25, (5, 4), "kagit"),
        ),
        cati=((16, 4.4), (3.4, 12.6), (28.6, 12.6), 2.8),
    ),
}


def kucuk(boyut: int) -> Image.Image:
    """Elle çizilmiş kesim (16, 24 ya da 32 px)."""
    cizim = KUCUK[boyut]
    tuval = Image.new("RGBA", (boyut * SS, boyut * SS), (0, 0, 0, 0))
    ciz = ImageDraw.Draw(tuval)

    def dik(x0: int, y0: int, x1: int, y1: int, renk: str) -> None:
        ciz.rectangle((x0 * SS, y0 * SS, x1 * SS - 1, y1 * SS - 1), fill=RENKLER[renk])

    kx0, ky0, kx1, ky1 = cizim.karo
    ciz.rounded_rectangle(
        (kx0 * SS, ky0 * SS, kx1 * SS - 1, ky1 * SS - 1),
        radius=round(cizim.yaricap * SS),
        fill=ZEMIN,
    )
    if cizim.cati is not None:
        tepe, sol, sag, kalinlik = cizim.cati
        for uc in (sol, sag):
            _kol(ciz, tepe, uc, kalinlik, CATI)
    for x0, y0, x1, y1, renk in cizim.dikdortgenler:
        dik(x0, y0, x1, y1, renk)
    for y, x0, x1, renk in cizim.satirlar:
        dik(x0, y, x1, y + 1, renk)
    return tuval.resize((boyut, boyut), Image.Resampling.BOX)


def kucuk_yolu(boyut: int) -> Path:
    return KLASOR / f"oab-defteri-{boyut}.png"


def generate() -> list[Path]:
    """Ana çizimi ve elle çizilmiş kesimleri yazar; yolları döndürür."""
    yazilan: list[Path] = []
    buyuk().save(LOGO, format="PNG", optimize=True)
    yazilan.append(LOGO)
    for boyut in KUCUK:
        yol = kucuk_yolu(boyut)
        kucuk(boyut).save(yol, format="PNG", optimize=True)
        yazilan.append(yol)
    return yazilan


if __name__ == "__main__":
    import sys

    for yol in generate():
        # Betik yalnız elle çalıştırılır; çıktı listesi bilinçli olarak yazılır.
        sys.stderr.write(f"yazıldı: {yol}\n")
