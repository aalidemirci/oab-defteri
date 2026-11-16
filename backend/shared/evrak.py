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

F2 EKLERİ (plan F2 §4.2, 8. adım):

- **Resmî yazı bloğu** (`ResmiYazi`; RYUE md. 10-14): okul idaresinin resmî yazısının (E12) başı.
  Başlık (antet) md. 10/3'e göre okul kartından kurulur (`okul_anteti`; yeni iş değildir). Blok
  belgenin İLK bloğudur (md. 11/2: "Sayı:" başlığın son satırından iki satır boşlukla); "Sayı:" ve
  tarih aynı satırdadır, tarih yazı alanının en sağında (md. 12/1); "Konu:" bir alt satırdadır ve
  yazı alanının dikey orta hizasını geçmez, sonunda noktalama yoktur (md. 13/1); iki yan başlığın
  iki noktası aynı hizadadır (md. 15/3). Word, PDF ve web sayfası bu satırları dört sütunlu
  çerçevesiz bir ızgarada çizer (`RYUE_SUTUNLARI`, `resmi_yazi_izgarasi`): sola yaslı yan başlık adı
  (hücre iç boşluğu yok: yazı alanının solundan başlar, md. 11/2), kendi dar sütununda iki nokta
  (iki satırda aynı sütun: aynı hiza, md. 15/3), değer ve sağa yaslı tarih. Muhatap konudan iki
  satır boşlukla ortalanır (md. 14/1); idarenin adı büyük harftir (md. 14/2, `tr_upper`), birim adı
  alt satırda parantez içindedir (md. 14/2, 14/5; `muhatap_satirlari`). Muhatabın biçimi kullanıcı
  kararı S11 (a)'dır (`shared.letterhead.mem_muhatabi`); alan serbest metindir, basımda düzenlenir.
  "Sayı:"nın içeriği EBYS'nindir (md. 11/1; program numara üretmez, plan F2 §7 U20). Excel çizicisi
  resmî yazı çizmez (`xlsx_ciz` reddeder): F2'de Excel'i olan E08 ve E14 resmî yazı değildir.
- **Ek bloğu** (`Ekler`; RYUE md. 18): imza bölümünden sonra, yazı alanının solundan (md. 18/1).
  Program sözleşmesi olarak ek bölümü imza bloğunun hemen ardından gelir (aralarına başka blok
  girmez; dağıtım bölümü ekten sonra, olur bölümü imzadan sonra gelir, bu sıra onlarla çelişmez). Tek
  ekte "Ek: <ibare>", birden çok ekte "Ek:" ve altında numaralı ekler (md. 18/2).
- **Sayfa sonu** (`SayfaSonu`): sonraki blok yeni sayfada başlar (E08'in sınıf başına sayfası, plan
  F2 §7 U16). Metin taşımaz, akışa girmez; belgenin ilk ya da son bloğu olamaz, art arda gelmez.
- **Çiziciler:** Word ve PDF'in yanında Excel (`xlsx_ciz`; openpyxl'e yalnız `shared.xlsx`
  kapısından) ve tek dosyalık, dış kaynaksız web sayfası (`web_html_ciz`; E06'nın internet sayfası).
  Web sayfası WeasyPrint baskı şablonunun yerine kullanılmaz; ikisi de aynı içerik modelinden çizilir.
- **Resmî yazının metni ve imzası** (plan F2 10. adım; E12): F1c'nin `Paragraf` ve `Imza` blokları
  değişmez (kayıtlı içerikleri aynı özeti vermeli), resmî yazı iki yeni blok kullanır. Metin paragrafı
  (`MetinParagrafi`, RYUE md. 16/4) ilk satırında 1,25 cm içeriden başlar, iki yana yaslıdır,
  paragraflar arasında boşluk yoktur. İmza bölümü (`ResmiImza`, md. 17/1, 17/11) metinden iki satır
  boşlukla, yazı alanını ikiye bölen iki hücrede çizilir: tek imza yazı alanının en sağında (sağ
  yarıda) ortalanır (md. 17/1); iki imzada üst unvan sağdadır (md. 17/11, birinci cümle; kurucu
  sahipleri soldan sağa verir, üst unvan sonda). İkiden çok imza bu blokta yoktur (md. 17/11'in
  ikinci cümlesi sıralamayı tersine çevirir; onu gerektiren belgenin fazında eklenir).
- **Konum cümlesi TFB** (tasarım §9.2; md. 23/5): `TFB` sabiti BİREBİR (F2'de E13).
"""

from __future__ import annotations

import hashlib
import html
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
#: TEFBİS konum cümlesi (tasarım §9.2 TFB; Yönetmelik md. 23/5). BİREBİR.
TFB = (
    "Birliğin gelir ve gider kayıtları ile diğer mali işlemleri TEFBİS'e okul idaresince "
    "kaydedilir; bu belge TEFBİS kaydının yerine geçmez."
)


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


# ---------------------------------------------------------------------------
# Resmî yazı (RYUE md. 10-14, 18) ve sayfa sonu (modül başlığı "F2 ekleri")
# ---------------------------------------------------------------------------

#: "Sayı:", "Konu:" ve "Ek:" yan başlıkları (RYUE md. 11/1, 13/1, 18/1; yönetmeliğin yazımıyla).
SAYI_ETIKETI = "Sayı:"
KONU_ETIKETI = "Konu:"
EK_ETIKETI = "Ek:"
#: Yan başlığın iki noktası. Izgarada yan başlığın adından ayrı, kendi dar sütununda durur: "Sayı" ve
#: "Konu" yazı alanının solundan başlar (md. 11/2), iki noktaları aynı hizadadır (md. 15/3).
IKI_NOKTA = ":"
#: Resmî yazı başının dört sütunu, yazı alanının yüzdesi: sola yaslı yan başlık adı (md. 11/2), iki
#: nokta (md. 15/3), değer ve sağa yaslı tarih (md. 12/1). İlk üç sütun yazı alanının yarısıdır: konu
#: dikey orta hizayı geçmez (md. 13/1). Ad sütunu 12 puntoda "Konu" sözcüğünü (~0,95 cm) alır.
#: Word ve PDF aynı yüzdeleri kullanır; hücrelerin iç boşluğu yoktur.
RYUE_SUTUNLARI: tuple[float, float, float, float] = (7.5, 2.5, 40.0, 50.0)
#: Excel çizicisinin resmî yazıyı reddi (`xlsx_ciz`; F2'de Excel'i olan E08 ve E14 resmî yazı değildir).
RESMI_YAZI_EXCEL_DISI = (
    "Resmî yazı Excel'e çizilmez: RYUE düzeni Excel sayfasının ızgarasında korunamaz. Resmî yazı Word "
    "ya da PDF olarak verilir."
)
#: Konunun sonunda bulunmayacak işaretler (md. 13/1: "herhangi bir noktalama işareti konulmaksızın"):
#: nokta, virgül, iki nokta, noktalı virgül, soru, ünlem, üç nokta; açma ve kapama ayraçları;
#: tırnaklar ve kesme; kısa çizgi, uzun çizgi, eğik ve ters eğik çizgi.
_KONU_SONU_NOKTALAMA = frozenset(".,;:!?…()[]{}\"'‘’“”«»-‐–—/\\")


@dataclass(frozen=True)
class ResmiYazi:
    """Resmî yazının başı (modül başlığı "F2 ekleri"; RYUE md. 11-14).

    `muhatap` idarenin adıdır, büyük harfe `tr_upper` ile çevrilerek saklanır (md. 14/2); `birim`
    verilirse alt satırda parantez içinde basılır (md. 14/2, 14/5; parantezsiz saklanır). Sayı,
    tarih, konu ve muhatap boş olamaz (md. 11/1 "sayı bulunması zorunludur"). Sayının yer tutucusu
    vardır: program sayıyı kuramaz, çağıran "………" verir (plan F2 §7 U20); muhatap önerisinde adı
    bilinmeyen il ya da ilçe de yer tutucuyla basılır (`letterhead.mem_muhatabi`). Konu her zaman
    kurucunun metnidir, yer tutucu olamaz: sonunda noktalama olmaz (md. 13/1) ve "…" de noktalamadır.

    Muhatap biçimi idare ya da özel hukuk tüzel kişisi içindir (md. 14/2; E12 bu hâldedir). Gerçek
    kişi muhatap ("Sayın" + adın ilk harfi büyük + SOYADI, md. 14/3) bu blokta yoktur; seçeneği onu
    gerektiren evrakın fazında (E35, E77) eklenir.
    """

    sayi: str
    tarih: str
    konu: str
    muhatap: str
    birim: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "muhatap", tr_upper(self.muhatap))
        for alan in (self.sayi, self.tarih, self.konu, self.muhatap):
            if not alan.strip():
                raise ValueError("Resmî yazının sayısı, tarihi, konusu ve muhatabı boş olamaz.")
        if self.konu.rstrip()[-1] in _KONU_SONU_NOKTALAMA:
            raise ValueError("Resmî yazının konusu noktalama işaretiyle bitmez (RYUE md. 13/1).")


def resmi_yazi_izgarasi(blok: ResmiYazi) -> tuple[tuple[str, str, str, str], ...]:
    """Resmî yazı başının iki satırı, `RYUE_SUTUNLARI`'nın dört sütunuyla: yan başlık adı, iki nokta,
    değer, tarih ("Sayı" satırında; md. 12/1) — "Konu" satırının tarih hücresi boştur (md. 13/1)."""
    return (
        (SAYI_ETIKETI.removesuffix(IKI_NOKTA), IKI_NOKTA, blok.sayi, blok.tarih),
        (KONU_ETIKETI.removesuffix(IKI_NOKTA), IKI_NOKTA, blok.konu, ""),
    )


def muhatap_satirlari(blok: ResmiYazi) -> tuple[str, ...]:
    """Muhatabın basılan satırları: idarenin adı ve (varsa) parantez içinde birim (md. 14/2, 14/5)."""
    return (blok.muhatap, f"({blok.birim})") if blok.birim else (blok.muhatap,)


@dataclass(frozen=True)
class Ekler:
    """Belgenin ekleri (RYUE md. 18): imza bölümünden sonra (md. 18/1; programda imza bloğunun hemen
    ardından); en az bir ek."""

    ekler: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.ekler or any(not ek.strip() for ek in self.ekler):
            raise ValueError("Ek bölümü en az bir ek taşır; ekin ibaresi boş olamaz.")


def ek_satirlari(blok: Ekler) -> tuple[str, ...]:
    """Ek bölümünün satırları: tek ekte "Ek: <ibare>", birden çok ekte "Ek:" ve altında numaralı
    ekler (md. 18/2)."""
    if len(blok.ekler) == 1:
        return (f"{EK_ETIKETI} {blok.ekler[0]}",)
    return (EK_ETIKETI, *(f"{sira}- {ek}" for sira, ek in enumerate(blok.ekler, start=1)))


@dataclass(frozen=True)
class SayfaSonu:
    """Sonraki blok yeni sayfada başlar (E08'in sınıf sayfaları). Metin taşımaz."""


#: Resmî yazının metin paragrafının ilk satır girintisi (cm; RYUE md. 16/4 "1,25 cm içeriden").
METIN_GIRINTISI_CM = 1.25
#: Resmî yazının imza bölümünün en çok imza sayısı (md. 17/1 tek, 17/11 birinci cümle iki imza).
RESMI_IMZA_EN_COK = 2


@dataclass(frozen=True)
class MetinParagrafi:
    """Resmî yazının metin paragrafı (modül başlığı "F2 ekleri"; RYUE md. 16/4): ilk satırı 1,25 cm
    içeriden başlar, iki yana yaslıdır; paragraflar arasında satır boşluğu yoktur."""

    metin: str


@dataclass(frozen=True)
class ResmiImza:
    """Resmî yazının imza bölümü (RYUE md. 17/1, 17/11; modül başlığı "F2 ekleri"). Sahipler soldan
    sağa verilir: iki imzada üst unvan sondadır (sağda, md. 17/11). Tarih satırı yoktur (tarih yazının
    başındadır, md. 12). En az bir, en çok iki imza."""

    sahipler: tuple[ImzaSahibi, ...]

    def __post_init__(self) -> None:
        if not 1 <= len(self.sahipler) <= RESMI_IMZA_EN_COK:
            raise ValueError(
                "Resmî yazının imza bölümü bir ya da iki imza taşır (RYUE md. 17/1, 17/11)."
            )


def resmi_imza_hucreleri(blok: ResmiImza) -> tuple[ImzaSahibi | None, ImzaSahibi | None]:
    """İmza bölümünün iki hücresi (yazı alanının sol ve sağ yarısı): tek imza sağ yarıdadır (md.
    17/1 "yazı alanının en sağında ortalanarak"), iki imzada üst unvan sağdadır (md. 17/11)."""
    if len(blok.sahipler) == 1:
        return None, blok.sahipler[0]
    return blok.sahipler[0], blok.sahipler[1]


Blok = (
    Baslik
    | AltBaslik
    | Paragraf
    | Tablo
    | KonumCumlesi
    | Imza
    | Dipnot
    | ResmiYazi
    | Ekler
    | SayfaSonu
    | MetinParagrafi
    | ResmiImza
)

_BLOK_TURLERI: dict[str, type[Any]] = {
    "baslik": Baslik,
    "alt_baslik": AltBaslik,
    "paragraf": Paragraf,
    "tablo": Tablo,
    "konum": KonumCumlesi,
    "imza": Imza,
    "dipnot": Dipnot,
    "resmi_yazi": ResmiYazi,
    "ekler": Ekler,
    "sayfa_sonu": SayfaSonu,
    "metin_paragrafi": MetinParagrafi,
    "resmi_imza": ResmiImza,
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
            onceki = self.bloklar[sira - 1] if sira > 0 else None
            sonraki = self.bloklar[sira + 1] if sira + 1 < len(self.bloklar) else None
            if isinstance(blok, Dipnot):
                dipnot_basladi = True
            elif dipnot_basladi:
                raise ValueError(
                    "Dipnot belgenin sonunda durur; ardından yalnız başka dipnot gelebilir."
                )
            if isinstance(blok, KonumCumlesi) and not isinstance(sonraki, Imza):
                raise ValueError(
                    "Konum cümlesi gövdenin sonunda, imza bloğunun hemen üstünde olmalı "
                    "(tasarım §9.2)."
                )
            if isinstance(blok, ResmiYazi) and sira != 0:
                raise ValueError(
                    "Resmî yazının başı (sayı, tarih, konu, muhatap) belgenin ilk bloğudur "
                    "(RYUE md. 11/2)."
                )
            if isinstance(blok, Ekler) and not isinstance(onceki, Imza | ResmiImza):
                raise ValueError(
                    "Ek bölümü imza bölümünden sonra gelir (RYUE md. 18/1); programda imza "
                    "bloğunun hemen ardındadır."
                )
            if isinstance(blok, SayfaSonu) and (
                onceki is None or sonraki is None or isinstance(onceki, SayfaSonu)
            ):
                raise ValueError(
                    "Sayfa sonu belgenin ilk ya da son bloğu olamaz ve art arda gelmez."
                )
        if sum(isinstance(blok, Ekler) for blok in self.bloklar) > 1:
            raise ValueError("Belgenin tek ek bölümü olur (RYUE md. 18).")


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
    if tur is Ekler:
        return Ekler(ekler=_metinler(alanlar["ekler"]))
    if tur is ResmiImza:
        sahipler = alanlar["sahipler"]
        if not isinstance(sahipler, list):
            raise BelgeCozulemedi()
        return ResmiImza(
            sahipler=tuple(ImzaSahibi(**_metin_alanlari(ImzaSahibi, sahip)) for sahip in sahipler)
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
    en sonda. Resmî yazının başı ızgaranın hücreleriyle ("Sayı", ":", sayı, tarih, "Konu", ":",
    konu; `resmi_yazi_izgarasi`), sonra muhatabın satırları; ek bölümü satır satır. Sayfa sonu
    metin taşımaz. Boş metinler akışa girmez.
    """
    akis = [belge.antet.tc, belge.antet.authority, belge.antet.unit_line, belge.antet.alt_birim]
    for blok in belge.bloklar:
        if isinstance(blok, ResmiYazi):
            for izgara_satiri in resmi_yazi_izgarasi(blok):
                akis += list(izgara_satiri)
            akis += list(muhatap_satirlari(blok))
        elif isinstance(blok, Ekler):
            akis += list(ek_satirlari(blok))
        elif isinstance(blok, Baslik):
            akis += [blok.metin, blok.alt]
        elif isinstance(blok, AltBaslik | Paragraf | KonumCumlesi | Dipnot | MetinParagrafi):
            akis.append(blok.metin)
        elif isinstance(blok, Tablo):
            akis += list(blok.basliklar)
            for satir in blok.satirlar:
                akis += list(satir)
        elif isinstance(blok, Imza):
            akis.append(blok.tarih)
            for sahip in blok.sahipler:
                akis += [sahip.ad, sahip.gorev]
        elif isinstance(blok, ResmiImza):
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
    elif isinstance(blok, ResmiYazi):
        oge["genislikler"] = [f"{yuzde:.2f}%" for yuzde in RYUE_SUTUNLARI]
        oge["satirlar"] = resmi_yazi_izgarasi(blok)
        oge["muhatap"] = muhatap_satirlari(blok)
    elif isinstance(blok, Ekler):
        oge["satirlar"] = ek_satirlari(blok)
    elif isinstance(blok, ResmiImza):
        oge["hucreler"] = resmi_imza_hucreleri(blok)
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
        if isinstance(blok, ResmiYazi):
            cizici.resmi_yazi_basi(
                d,
                satirlar=resmi_yazi_izgarasi(blok),
                muhatap=muhatap_satirlari(blok),
                yuzdeler=RYUE_SUTUNLARI,
            )
        elif isinstance(blok, Ekler):
            cizici.ekler(d, ek_satirlari(blok))
        elif isinstance(blok, SayfaSonu):
            cizici.sayfa_sonu(d)
        elif isinstance(blok, MetinParagrafi):
            cizici.metin_paragrafi(d, blok.metin, girinti_cm=METIN_GIRINTISI_CM)
        elif isinstance(blok, ResmiImza):
            cizici.resmi_imza(
                d,
                [None if s is None else (s.ad, s.gorev) for s in resmi_imza_hucreleri(blok)],
            )
        elif isinstance(blok, Baslik):
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


def xlsx_ciz(belge: Belge) -> bytes:
    """Belgenin Excel dosyası (E08 katılım cetveli, E14 yıllık iş takvimi; tasarım §9.5). openpyxl'e
    yalnız `shared.xlsx` kapısından gidilir; içerik aynı modeldendir (tek içerik).

    Tek çalışma sayfası, A4 dikey, sayfa genişliğine sığdırılır. Sayfanın sütun sayısı belgedeki en
    geniş tablonun sütun sayısıdır; dar tablonun son sütunu ve paragraflar kalan sütunlara yayılır.
    Sayfa sonu Excel'in elle sayfa sonudur. Altlık Word ve PDF'tekiyle aynıdır ("OAB Defteri · <kod>
    · Sayfa n/m"), metin akışına girmez.

    Resmî yazı (`ResmiYazi`) Excel'e çizilmez, `ValueError` verir: sayfanın tek sütun ızgarası
    tablonundur, RYUE başının sütunları (yan başlık, iki nokta, konu yazı alanının yarısında) onunla
    birlikte korunamaz. F2'de Excel'i olan E08 ve E14 resmî yazı değildir; resmî yazı Word ve PDF'tir.
    """
    from shared import xlsx as cizici

    if any(isinstance(blok, ResmiYazi) for blok in belge.bloklar):
        raise ValueError(RESMI_YAZI_EXCEL_DISI)
    tablolar = [blok for blok in belge.bloklar if isinstance(blok, Tablo)]
    genislik = max([1, *(len(t.basliklar) for t in tablolar)])
    en_genis = next((t for t in tablolar if len(t.basliklar) == genislik), None)
    yuzdeler = sutun_yuzdeleri(en_genis) if en_genis is not None else (100.0,) * genislik
    k = cizici.Kitap(belge.kod, yuzdeler)
    for satir in (belge.antet.tc, belge.antet.authority, belge.antet.unit_line):
        if satir:
            k.ortali_satir(satir, kalin=True)
    if belge.antet.alt_birim:
        k.ortali_satir(belge.antet.alt_birim)
    for blok in belge.bloklar:
        if isinstance(blok, Ekler):
            k.bos_satir()
            for satir in ek_satirlari(blok):
                k.sola_satir(satir)
        elif isinstance(blok, SayfaSonu):
            k.sayfa_sonu()
        elif isinstance(blok, Baslik):
            k.ortali_satir(blok.metin, kalin=True)
            if blok.alt:
                k.ortali_satir(blok.alt, punto=10)
        elif isinstance(blok, AltBaslik):
            k.sola_satir(blok.metin, kalin=True)
        elif isinstance(blok, Paragraf | MetinParagrafi):
            k.paragraf(blok.metin)
        elif isinstance(blok, ResmiImza):
            k.imza("", [(sahip.ad, sahip.gorev) for sahip in blok.sahipler])
        elif isinstance(blok, KonumCumlesi):
            k.paragraf(blok.metin, punto=cizici.KONUM_PUNTO)
        elif isinstance(blok, Tablo):
            k.tablo(blok.basliklar, blok.satirlar, punto=tablo_punto(len(blok.basliklar)))
        elif isinstance(blok, Imza):
            k.imza(blok.tarih, [(sahip.ad, sahip.gorev) for sahip in blok.sahipler])
        elif isinstance(blok, Dipnot):
            k.paragraf(blok.metin, punto=cizici.DIPNOT_PUNTO)
    return k.kaydet()


# ---------------------------------------------------------------------------
# Web sayfası (E06'nın internet sayfası; tasarım §9.6 "html tek dosya, dış bağlantısız")
# ---------------------------------------------------------------------------

#: Web sayfasının biçemi. Dış kaynak YOKTUR: yazı tipi adla istenir (indirilmez), görsel, `url(...)`
#: ve `@import` yoktur; sayfa tek dosyadır ve çevrimdışı açılır. Harf dönüşümü yoktur (büyük harf
#: verinin kendisinde). Baskıda sayfa sonu korunur.
WEB_BICEMI = (
    "*{box-sizing:border-box}"
    "body{margin:0;background:#fff;color:#1f2937;"
    "font-family:'Times New Roman','Liberation Serif',serif;font-size:1rem;line-height:1.45}"
    "main{max-width:48rem;margin:0 auto;padding:1.5rem 1rem}"
    ".antet{text-align:center;font-weight:bold;margin-bottom:1rem}"
    ".antet p{margin:0}.antet .alt-birim{font-weight:normal}"
    "h1{font-size:1.15rem;text-align:center;margin:1rem 0 .25rem}"
    ".alt{text-align:center;margin:0 0 .75rem}"
    "h2{font-size:1rem;margin:1rem 0 .25rem}"
    "p{margin:.5rem 0}.govde{text-align:justify}"
    ".girintili{text-indent:1.25cm;margin:0}"
    ".resmi-imza{display:grid;grid-template-columns:1fr 1fr;margin-top:2rem}"
    ".tablo{overflow-x:auto}"
    "table{border-collapse:collapse;width:100%;table-layout:fixed;margin:.5rem 0}"
    "th,td{border:1px solid #9ca3af;padding:.25rem .4rem;text-align:left;vertical-align:top;"
    "overflow-wrap:break-word}"
    "th{background:#f3f4f6}"
    ".ryue td{border:0;padding:0}.ryue .tarih{text-align:right}"
    ".ryue .ad{width:3.5em}.ryue .iki-nokta{width:1em}.ryue col.tarih{width:50%}"
    ".muhatap{text-align:center;margin:1.5rem 0}.muhatap p{margin:0}"
    ".imza{margin-top:1.5rem}.imza .tarih{text-align:right}"
    ".sahipler{display:flex;flex-wrap:wrap;justify-content:space-around;gap:1rem}"
    ".sahip{text-align:center;min-width:9rem}.sahip p{margin:0}.sahip .ad{font-weight:bold}"
    ".ekler p{margin:0}"
    ".konum,.dipnot{font-size:.875rem}"
    ".sayfa-sonu{border:0;border-top:1px dashed #9ca3af;margin:1.5rem 0}"
    "@media print{.sayfa-sonu{border:0;break-after:page}}"
)


def web_html_ciz(belge: Belge) -> str:
    """Belgenin tek dosyalık web sayfası (E06; modül başlığı "F2 ekleri").

    Bütün metin `html.escape` ile kaçışlıdır; sayfada bağlantı, betik, görsel ya da başka bir dış
    kaynak yoktur (`WEB_BICEMI`). WeasyPrint baskı şablonunun yerine geçmez: baskı PDF'i `pdf_ciz`'dir.
    Gövdenin metni `metin_akisi` ile aynıdır (içerik eşdeğerliği); sayfanın adı (`<title>`) başlıktan
    gelir ve gövdede değildir. Altlık yoktur.
    """

    def e(metin: str) -> str:
        return html.escape(metin, quote=True)

    def p(metin: str, sinif: str = "") -> str:
        return f'<p class="{sinif}">{e(metin)}</p>' if sinif else f"<p>{e(metin)}</p>"

    antet = belge.antet
    parcalar = ['<header class="antet">']
    parcalar += [p(satir) for satir in (antet.tc, antet.authority, antet.unit_line) if satir]
    if antet.alt_birim:
        parcalar.append(p(antet.alt_birim, "alt-birim"))
    parcalar.append("</header>")
    for blok in belge.bloklar:
        if isinstance(blok, ResmiYazi):
            # Ad ve iki nokta sütunu yazı biriminde (dar ekranda "Konu" sığsın); tarih sütunu yarıdır,
            # konu yarıyı geçmez (md. 13/1).
            gen = '<col class="ad"><col class="iki-nokta"><col><col class="tarih">'
            satirlar = "".join(
                f'<tr><td>{e(ad)}</td><td>{e(iki)}</td><td>{e(deger)}</td><td class="tarih">'
                f"{e(sag)}</td></tr>"
                for ad, iki, deger, sag in resmi_yazi_izgarasi(blok)
            )
            parcalar.append(f'<table class="ryue"><colgroup>{gen}</colgroup>{satirlar}</table>')
            satirlar = "".join(p(satir) for satir in muhatap_satirlari(blok))
            parcalar.append(f'<div class="muhatap">{satirlar}</div>')
        elif isinstance(blok, Ekler):
            satirlar = "".join(p(satir) for satir in ek_satirlari(blok))
            parcalar.append(f'<div class="ekler">{satirlar}</div>')
        elif isinstance(blok, SayfaSonu):
            parcalar.append('<hr class="sayfa-sonu">')
        elif isinstance(blok, Baslik):
            parcalar.append(f"<h1>{e(blok.metin)}</h1>")
            if blok.alt:
                parcalar.append(p(blok.alt, "alt"))
        elif isinstance(blok, AltBaslik):
            parcalar.append(f"<h2>{e(blok.metin)}</h2>")
        elif isinstance(blok, Paragraf):
            parcalar.append(p(blok.metin, "govde"))
        elif isinstance(blok, MetinParagrafi):
            parcalar.append(p(blok.metin, "govde girintili"))
        elif isinstance(blok, ResmiImza):
            hucreler = "".join(
                '<div class="sahip"></div>'
                if sahip is None
                else f'<div class="sahip">{p(sahip.ad, "ad")}{p(sahip.gorev, "gorev")}</div>'
                for sahip in resmi_imza_hucreleri(blok)
            )
            parcalar.append(f'<div class="imza resmi-imza">{hucreler}</div>')
        elif isinstance(blok, KonumCumlesi):
            parcalar.append(p(blok.metin, "konum"))
        elif isinstance(blok, Tablo):
            gen = "".join(f'<col style="width:{yuzde:.2f}%">' for yuzde in sutun_yuzdeleri(blok))
            bas = "".join(f"<th>{e(hucre)}</th>" for hucre in blok.basliklar)
            govde = "".join(
                "<tr>" + "".join(f"<td>{e(hucre)}</td>" for hucre in satir) + "</tr>"
                for satir in blok.satirlar
            )
            parcalar.append(
                f'<div class="tablo"><table><colgroup>{gen}</colgroup>'
                f"<thead><tr>{bas}</tr></thead><tbody>{govde}</tbody></table></div>"
            )
        elif isinstance(blok, Imza):
            sahipler = "".join(
                f'<div class="sahip">{p(sahip.ad, "ad")}{p(sahip.gorev, "gorev")}</div>'
                for sahip in blok.sahipler
            )
            tarih = p(blok.tarih, "tarih") if blok.tarih else ""
            parcalar.append(
                f'<div class="imza">{tarih}<div class="sahipler">{sahipler}</div></div>'
            )
        elif isinstance(blok, Dipnot):
            parcalar.append(p(blok.metin, "dipnot"))
    baslik = next((b.metin for b in belge.bloklar if isinstance(b, Baslik)), belge.kod)
    return (
        '<!DOCTYPE html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{e(baslik)}</title>\n<style>{WEB_BICEMI}</style>\n</head>\n<body>\n<main>\n"
        + "\n".join(parcalar)
        + "\n</main>\n</body>\n</html>\n"
    )


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


def ornek_resmi_yazi() -> Belge:
    """Resmî yazı bloğunun ve ek bölümünün örneği (çizici testleri). Adlar UYDURMADIR.

    Okul antedi (RYUE md. 10/3), "Sayı:" ve tarih aynı satırda, konu, iki satırlı muhatap (kullanıcı
    kararı S11 (a): ilçe millî eğitim müdürlüğüne kaymakamlık üzerinden), girintili metin paragrafları
    (md. 16/4), "Ad SOYAD" imzalı iki imzalı imza bölümü (üst unvan sağda, md. 17/11) ve iki ek.
    """
    from shared.letterhead import MEM_ILCE, mem_muhatabi

    muhatap, birim = mem_muhatabi(MEM_ILCE, il="Örnek İl", ilce="Örnek İlçe")
    return Belge(
        kod="DUMAN",
        antet=okul_anteti(okul_adi="Örnek Ortaokulu", ilce="Örnek İlçe"),
        bloklar=(
            ResmiYazi(
                sayi="………",
                tarih="01.11.2026",
                konu="Genel Kurulda İbra Edilmeyen Yönetim Kurulu",
                muhatap=muhatap,
                birim=birim,
            ),
            MetinParagrafi(
                f"Türkçe örnek: {TURKCE_ORNEK}. Bu yazı evrak hattının resmî yazı bloğunu sınar."
            ),
            MetinParagrafi("Bilgilerinizi ve gereğini arz ederim."),
            ResmiImza(
                sahipler=(
                    ImzaSahibi(ad_soyad("ayşe", "örnek"), "Birlik Başkanı"),
                    ImzaSahibi(ad_soyad("İsmail", "Deneme"), "Okul Müdürü"),
                ),
            ),
            Ekler(("Teslim tutanağı (1 sayfa)", "Genel kurul tutanağı örneği (2 sayfa)")),
        ),
    )


def ornek_sayfali_belge() -> Belge:
    """Sayfa sonu bloğunun örneği (sınıf başına sayfa; çizici testleri). Adlar UYDURMADIR."""
    basliklar = ("Sıra", "Velinin adı ve soyadı", "Öğrencinin sınıfı", "İmza")
    return Belge(
        kod="DUMAN",
        antet=birlik_anteti(okul_adi="Örnek Ortaokulu", ilce="Örnek İlçe"),
        bloklar=(
            Baslik("sayfa sonu örneği"),
            AltBaslik("Sınıf: 5-A"),
            Tablo(
                basliklar=basliklar,
                satirlar=(("1", "Ayşe ÖRNEK", "5-A", ""),),
                oranlar=(1, 5, 3, 3),
            ),
            SayfaSonu(),
            AltBaslik("Sınıf: 5-B"),
            Tablo(
                basliklar=basliklar,
                satirlar=(("1", "Şükrü DENEME", "5-B", ""),),
                oranlar=(1, 5, 3, 3),
            ),
            Imza(sahipler=(ImzaSahibi(ad_soyad("ayşe", "örnek"), "Divan Başkanı"),)),
            Dipnot(KISISEL_VERI_DIPNOTU),
        ),
    )
