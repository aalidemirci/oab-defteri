"""Rol-izin matrisi, uç kuralları ve yetki kapısı (tasarım §4.4.2, TK13, §12.B; plan F1b-2).

Tasarım §4.4.2 matrisi rol yetkisinin TEK bağlayıcı kaynağıdır; bu dosya onu iki katmana
uygular ("Uygulama — iki katman"):

1. **Uç katmanı** (`RolMiddleware`, `apps/okul/rol_middleware.py`): her `/api/` ucu URL
   ADIYLA, yöntemiyle (ve isteğe bağlı parametre denetçisiyle) bir matris satırına bağlanır
   (`KURALLAR`). Kuraldaki roller elle yazılmaz, `MATRIS`'ten türer; kural matrisi
   AŞAMAZ: hücre "—" ise o role hiçbir şey açılmaz, "O" ise yalnız okuma açılır (tek istisna
   ²'nin rol-özel işaretidir, `ROL_OZEL_YAZMA_DIPNOTLARI`), dipnotlu Y hücresi yalnız o
   dipnotu adıyla anan kurala açılır. Daraltma (`yalniz`) serbesttir ve
   dayanağı yazılır (tasarımın "§7 ve §9 daraltır, genişletemez" kuralı). Kısmi yetki ayrı
   uçla verilir (TK13). **Yeni uç varsayılan kapalıdır**, program yöneticisi için de:
   `yonetici` süper kullanıcı değildir, yalnız Y olduğu satırda yazar (§4.4.2
   "Bağlayıcılık").
2. **Servis katmanı** (`yetki`, `yetki_oturum`): kapanmış dönem, maskesiz okuma, kişisel
   veri içeren çıktı, rol-özel işaretler ve kayıt sahipliği tek kapıdan geçer
   (`Eylem` kapalı kümesi, `EYLEM_KURALLARI`). Her eylem matris satırını ve varsa dipnotunu
   anar; izinli rolleri o satırın Y hücrelerini aşamaz. Ret `shared.exceptions.RolYetkisiz`
   ile verilir ve 403 `rol_yetkisiz` olur (uç katmanınınkiyle aynı gövde). Rolün kaynağı
   istek başındaki yazar bağlamıdır (`oturum.yazar()`): denetim izinin yazarıyla aynı
   görüntüdür, istek ortasındaki kilit ya da hesap değişimi kararı onu değiştirmez (planın
   "`OTURUM.hesap().rol` ile" lafzının istek başındaki karşılığı). Yazar yoksa ya da `SISTEM`
   ise ret (fail-closed).

MATRİS (`MATRIS`). Tasarım tablosunun birebir kopyasıdır; hücre harf + dipnottur ("Y",
"O²", "—"). `tests/test_rol_izinleri.py` tabloyu tasarım belgesinden ayrıştırıp bununla
karşılaştırır: belge ya da kod değişince test düşer. Matris dışında tek etiket vardır:
`OTURUM` (kilit ekranı ve durum yolları; her role açık). `KENDI` tablonun son satırıdır
("Kendi parolasını değiştirme, Kilitle, Çık"; her rolde Y); plan F1b-2'nin "kendi hesabı"
etiketi olarak oturumdaki hesabın kendi parola bildirimini ve kendi kartlarını da taşır.
Değişmez: kilitliyken açık olan her (uç, yöntem) açık oturumda her role açıktır
(`lock_middleware.KILITLI_IZINLI`; `test_rol_koruma` sınar) — oturum açmak kilitlemekten
az erişim vermemelidir.

BEKLEYENLER. Matristeki hücrelerin ve dipnotların çoğunun ucu ya da servisi sonraki
fazlardadır (müdür yazıları F2/F4, mali kayıtlar F3, DK modülü F4…). Ucu ya da servisi
olmayan Y hücresi `BEKLEYEN_HUCRELER`'de, gerçek servisi olmayan dipnot
`BEKLEYEN_DIPNOTLAR`'da, servise bağlanmamış eylem `BAGLANMAMIS_EYLEMLER`'de fazıyla durur
(plan F1b-2 kullanıcı kararı). Listeler testte anlık görüntüdür ve yalnız küçülebilir; her
fazın kapısında "bu fazın hücreleri ve dipnotları bağlandı" maddesi vardır. F1b'nin 2. adımının
kapısı: faz değeri "F1b" olan bekleyen KALMAZ (testle sabit) — Kullanıcılar hücresi uçlarıyla
(F1b-2 (c)), Denetleme Kurulunun M8 hücresi, ⁵ dipnotu ve `GERI_YUKLEME_GORDUM` eylemi geri
yükleme kartının "Gördüm"üyle (F1b-2 (c)) bağlandı. `etkin_hucreler(rol)`
bekleyende olmayan Y hücreleridir: hesap teslim pusulasının "bu programda sizin işiniz"
özeti ve hücre anlık görüntüsü bu tek yüklemi kullanır; ikinci bir matris doğmaz.

YETENEKLER (`YETENEKLER`). Ön yüz süzmesinin tek kaynağıdır: her yetenek bir (uç, yöntem)
kümesidir; rol, kümedeki her çift ona açıksa o yeteneğe sahiptir. Değer kurallardan türer,
elle yazılmaz; oturum özeti `hesap.yetenekler`'i taşır (`oturum.OturumHesabi.ozet`). Ön yüz
matrisi kopyalamaz.

PARAMETRE DENETÇİLERİ (aile iskeletinden AYNEN; §12.B). Parametre kuralı, isteği alıp geçip
geçmeyeceğini söyleyen bir denetçidir; yanlış dönerse istek kesilir. İki biçimi vardır:

* `yalniz_sorgu(...)`: GET ucunun sorgu dizesinde YALNIZ sayılan anahtarlar
  bulunabilir (bilinmeyen anahtar da kesilir, fail-closed);
* `govdede_yok(...)`: gövdede (ve sorgu dizesinde) sayılan anahtarların HİÇBİRİ
  bulunamaz. Gövde JSON değilse (ya da okunamıyorsa) istek kesilir: denetçinin
  okuyamadığı bir gövde görünüme ulaşmamalıdır. Boş gövde geçer (görünüm
  doğrulamayla reddeder). **Karakter kümesi yalnız UTF-8'dir**: denetçi baytları
  `json.loads` ile okur (UTF-8/16/32 kendiliğinden sezilir), DRF ise gövdeyi
  `Content-Type`'taki `charset` ile çözer; `charset=utf-7` gönderen bir istemci bir
  anahtarı denetçiye başka, görünüme başka gösterebilirdi. `charset` UTF-8 dışında
  bir şeyse istek kesilir.

Anahtarın DEĞERİNE bakılmaz, VARLIĞINA bakılır; bu yüzden aynı ucun değer üzerinden ayrılan
kısmi yetkisi (ör. `leave-pool/?summary=true`) parametreyle verilmez. F1b'de hiçbir kuralda
parametre denetçisi yoktur (testte anlık görüntü).

Uçlar Django URL ADIYLA tutulur (`uc_adi`; ad alanlı include'da `ad_alani:ad`): yol
dönüştürücü içerebilir, ad değişmez. Bu yüzden `/api/` altındaki adların TEKİL olması
şarttır; teklik `tests/test_rol_izinleri.py`'de sabitlenir.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Protocol

from django.http import HttpRequest
from django.urls import Resolver404, resolve

from apps.okul.models import AccountRole
from apps.okul.oturum import yazar
from shared.exceptions import RolYetkisiz

ParametreDenetcisi = Callable[[HttpRequest], bool]

#: Parametre denetçili uçların kabul ettiği tek gövde biçimi.
JSON_ICERIK = "application/json"
#: Gövdenin kabul edilen tek karakter kümesi (adı büyük/küçük harf ve tire farkı gözetmeden).
UTF8_ADLARI = frozenset({"utf-8", "utf8"})

#: Matrisin sütunları, tasarım tablosunun sırasıyla (`AccountRole` sırası aynıdır).
ROLLER: Final[tuple[str, ...]] = tuple(str(rol) for rol in AccountRole.values)
YONETICI: Final = AccountRole.YONETICI.value
DENETLEME_KURULU: Final = AccountRole.DENETLEME_KURULU.value
MUDUR: Final = AccountRole.MUDUR.value
#: Yönetim kurulu rolleri (başkan, başkan yardımcısı, muhasip, sekreter).
YK_ROLLERI: Final[frozenset[str]] = frozenset(
    {
        AccountRole.BASKAN.value,
        AccountRole.BASKAN_YARDIMCISI.value,
        AccountRole.MUHASIP.value,
        AccountRole.SEKRETER.value,
    }
)

#: Okuma yöntemleri: GET ile HEAD birlikte açılır (Django görünümü HEAD'i GET'e düşürür).
OKUMA: Final[frozenset[str]] = frozenset({"GET", "HEAD"})
#: Kurallarda geçebilecek yöntemler. OPTIONS hiçbir rolde açık değildir (DRF meta verisi
#: gereksiz bir yüzeydir); kurala yazılırsa tablo kurulmaz.
_KURAL_YONTEMLERI: Final[frozenset[str]] = OKUMA | {"POST", "PUT", "PATCH", "DELETE"}

#: Matris harfleri: yazar, okur, erişemez.
YAZAR: Final = "Y"
OKUR: Final = "O"
ERISEMEZ: Final = "—"
_HARFLER: Final = frozenset({YAZAR, OKUR, ERISEMEZ})
_UST_RAKAMLAR: Final = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
}

#: Okur ("O") hücresinin dipnotla yazma verdiği dipnotlar: YALNIZ ². Tasarım §4.4.2 "Okuma":
#: "Okur rolün bundan başka yazması yalnız dipnotla verilen rol-özel işarettir (² …)"; ²:
#: "Rol-özel işaretlerin tek kaynağı bu dipnottur" ("TEFBİS'e girildi" program yöneticisinde).
#: Plan F1b-2: "hücre O ise yalnız okuma açılır". ⁷ yazma VERMEZ: müdürün kendi yazısını evrak
#: defterine program işler (müdür yazısı eyleminin yan etkisi; ayrı eylemi ve ucu yoktur),
#: müdür gelen-giden evrakı yazmaz. ⁹ de yazma vermez (müdür kantin ve servis akışlarında iş
#: yapan rol değildir). Kümeyi genişletmek tasarım değişikliğidir (testler bağımsız sabitle sınar).
ROL_OZEL_YAZMA_DIPNOTLARI: Final[frozenset[int]] = frozenset({2})

Hucre = tuple[str, int | None]


class Satir(StrEnum):
    """Matrisin satırları (tasarım tablosunun sırasıyla) ve matris dışı `OTURUM` etiketi."""

    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M7 = "M7"
    M8 = "M8"
    MUDUR_YAZISI = "MUDUR_YAZISI"
    M9 = "M9"
    M10 = "M10"
    M11 = "M11"
    M13_M14 = "M13_M14"
    M15 = "M15"
    DENETIM_IZI = "DENETIM_IZI"
    ERISIM_GUNLUGU = "ERISIM_GUNLUGU"
    KULLANICILAR = "KULLANICILAR"
    GUVENLIK = "GUVENLIK"
    AYARLAR = "AYARLAR"
    KISISEL_VERI = "KISISEL_VERI"
    GUNCELLEME = "GUNCELLEME"
    #: "Kendi parolasını değiştirme, Kilitle, Çık" (+ kendi parola bildirimi ve kartları).
    KENDI = "KENDI"
    #: Matris dışı: kilit ekranı ve durum yolları (her role açık; modül başlığı).
    OTURUM = "OTURUM"


class KuralTuru(StrEnum):
    """Kuralın anlamsal türü: okuma Y ve O hücrelerine, yazma yalnız Y hücrelerine açılır."""

    OKUMA = "okuma"
    YAZMA = "yazma"


def hucre_coz(metin: str) -> Hucre:
    """Tasarım tablosunun hücresi ("Y", "O²", "Y¹⁰", "—") → (harf, dipnot)."""
    deger = metin.strip()
    harf, ust = deger[:1], deger[1:]
    if harf not in _HARFLER or any(k not in _UST_RAKAMLAR for k in ust):
        raise ValueError(f"Rol matrisinde tanınmayan hücre: {metin!r}")
    if harf == ERISEMEZ and ust:
        raise ValueError(f"Erişilemeyen hücre dipnot taşımaz: {metin!r}")
    return harf, (int("".join(_UST_RAKAMLAR[k] for k in ust)) if ust else None)


#: Tasarım §4.4.2 tablosu, sütunlar `ROLLER` sırasıyla (`yonetici`, `baskan`,
#: `baskan_yardimcisi`, `muhasip`, `sekreter`, `denetleme_kurulu`, `mudur`).
_TABLO: Final[tuple[tuple[Satir, tuple[str, ...]], ...]] = (
    (Satir.M1, ("Y", "O", "O", "O", "O", "O", "O")),
    (Satir.M2, ("Y", "Y", "Y", "Y", "Y", "O", "O")),
    (Satir.M3, ("Y", "Y", "Y", "Y", "Y", "O", "Y¹")),
    (Satir.M4, ("Y", "Y", "Y", "Y", "Y", "O", "O")),
    (Satir.M5, ("O²", "O", "O", "Y", "O", "O", "O")),
    (Satir.M6, ("Y³", "Y³", "Y³", "Y", "Y³", "O", "Y⁴")),
    (Satir.M7, ("Y", "Y", "Y", "Y", "Y", "O", "O")),
    (Satir.M8, ("O", "O", "O", "O", "O", "Y⁵", "O")),
    (Satir.MUDUR_YAZISI, ("O", "O", "O", "O", "O", "O", "Y⁶")),
    (Satir.M9, ("Y", "Y", "Y", "Y", "Y", "O", "O")),
    (Satir.M10, ("Y", "Y", "Y", "Y", "Y", "O", "O⁷")),
    (Satir.M11, ("Y⁸", "Y", "Y", "Y", "Y", "O", "O")),
    (Satir.M13_M14, ("Y", "Y", "Y", "Y", "Y", "O", "O⁹")),
    (Satir.M15, ("Y", "Y", "Y", "Y", "Y", "O", "O")),
    (Satir.DENETIM_IZI, ("O", "O", "O", "O", "O", "O", "O")),
    (Satir.ERISIM_GUNLUGU, ("O", "—", "—", "—", "—", "O", "—")),
    (Satir.KULLANICILAR, ("Y", "—", "—", "—", "—", "—", "—")),
    (Satir.GUVENLIK, ("Y", "—", "—", "—", "—", "—", "—")),
    (Satir.AYARLAR, ("Y", "O", "O", "O", "O", "O", "O")),
    (Satir.KISISEL_VERI, ("Y¹⁰", "—", "—", "—", "—", "—", "—")),
    (Satir.GUNCELLEME, ("Y", "—", "—", "—", "—", "—", "—")),
    (Satir.KENDI, ("Y", "Y", "Y", "Y", "Y", "Y", "Y")),
)

#: Rol-izin matrisi (tasarım §4.4.2): satır → rol → (harf, dipnot). `OTURUM` matriste yoktur.
MATRIS: Final[Mapping[Satir, Mapping[str, Hucre]]] = {
    satir: dict(zip(ROLLER, (hucre_coz(h) for h in hucreler), strict=True))
    for satir, hucreler in _TABLO
}


def okuyabilen_roller(satir: Satir) -> frozenset[str]:
    """Satırı okuyabilen roller: Y ya da O hücresi (dipnot okumayı kısmaz); `OTURUM` herkes."""
    if satir is Satir.OTURUM:
        return frozenset(ROLLER)
    return frozenset(rol for rol, (harf, _) in MATRIS[satir].items() if harf in (YAZAR, OKUR))


def yazabilen_roller(satir: Satir, dipnot: int | None = None) -> frozenset[str]:
    """Satıra yazabilen roller (modül başlığı "kural matrisi aşamaz").

    Dipnotsuz Y hücresi her zaman; dipnotlu Y hücresi yalnız `dipnot` o dipnotsa; okur
    hücresi yalnız rol-özel yazma dipnotunu (`ROL_OZEL_YAZMA_DIPNOTLARI`: ²) adıyla anınca.
    `OTURUM` herkese açıktır.
    """
    if satir is Satir.OTURUM:
        return frozenset(ROLLER)
    sonuc: set[str] = set()
    for rol, (harf, hucre_dipnotu) in MATRIS[satir].items():
        if harf == YAZAR and hucre_dipnotu in (None, dipnot):
            sonuc.add(rol)
        elif (
            harf == OKUR
            and hucre_dipnotu is not None
            and hucre_dipnotu == dipnot
            and hucre_dipnotu in ROL_OZEL_YAZMA_DIPNOTLARI
        ):
            sonuc.add(rol)
    return frozenset(sonuc)


def _satir_dipnotlari(satir: Satir) -> frozenset[int]:
    if satir is Satir.OTURUM:
        return frozenset()
    return frozenset(d for _, d in MATRIS[satir].values() if d is not None)


#: Matristeki bütün dipnotlar (1-10).
MATRIS_DIPNOTLARI: Final[frozenset[int]] = frozenset(
    dipnot for satir in MATRIS for dipnot in _satir_dipnotlari(satir)
)


# ---------------------------------------------------------------------------
# Uç kuralları (uç katmanı)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RolKurali:
    """Bir (uç, yöntemler) çiftinin matris satırına bağlanışı (modül başlığı).

    Roller yazılmaz, türetilir (`kural_rolleri`): okuma kuralı satırın Y ve O hücrelerine,
    yazma kuralı Y hücrelerine açılır; `dipnot` dipnotlu hücreyi açar (kısmi yetki),
    `yalniz` daraltır. `dipnot` ya da `yalniz` doluysa `dayanak` zorunludur.
    """

    uc: str
    yontemler: frozenset[str]
    satir: Satir
    tur: KuralTuru
    dipnot: int | None = None
    yalniz: frozenset[str] | None = None
    parametre: ParametreDenetcisi | None = None
    dayanak: str = ""
    gerekce: str = ""


def kural_rolleri(kural: RolKurali) -> frozenset[str]:
    """Kuralın açıldığı roller (matristen türer; `yalniz` yalnız daraltır)."""
    if kural.tur is KuralTuru.OKUMA:
        roller = okuyabilen_roller(kural.satir)
    else:
        roller = yazabilen_roller(kural.satir, kural.dipnot)
    return roller if kural.yalniz is None else roller & kural.yalniz


def _yontemler(yontemler: str | Iterable[str]) -> frozenset[str]:
    if isinstance(yontemler, str):
        return frozenset({yontemler})
    return frozenset(yontemler)


def _oku(
    uc: str, satir: Satir, *, yalniz: frozenset[str] | None = None, dayanak: str = ""
) -> RolKurali:
    """Okuma kuralı (GET + HEAD)."""
    return RolKurali(uc, OKUMA, satir, KuralTuru.OKUMA, yalniz=yalniz, dayanak=dayanak)


def _yaz(
    uc: str,
    yontemler: str | Iterable[str],
    satir: Satir,
    *,
    dipnot: int | None = None,
    yalniz: frozenset[str] | None = None,
    dayanak: str = "",
) -> RolKurali:
    """Yazma (eylem) kuralı."""
    return RolKurali(
        uc,
        _yontemler(yontemler),
        satir,
        KuralTuru.YAZMA,
        dipnot=dipnot,
        yalniz=yalniz,
        dayanak=dayanak,
    )


_YALNIZ_YONETICI: Final = frozenset({YONETICI})
_YONETICI_VE_DK: Final = frozenset({YONETICI, DENETLEME_KURULU})

_DAYANAK_PERSONEL = (
    "Tasarım §8.1 A7 ('e-Okul: yonetici'): okul çekirdeğinin e-Okul kaynaklı personel sicili "
    "F1b'de yalnız program yöneticisinin yazdığı kayıttır; M2'nin YK hücreleri OAB kişileriyle "
    "F1c'de bağlanır (plan F1b-2 'Bugünkü uçların eşlemi'; tasarımda bu daraltmanın satırı yok)."
)
_DAYANAK_HAVUZ = (
    "Plan F1b-2: ayrılış havuzu (özet dahil) yalnız program yöneticisinindir; karar e-Okul "
    "aktarımının parçasıdır (tasarım §8.1 A7). Parametre denetçisi değere bakmadığı için "
    "`?summary=true` ayrı açılamaz."
)
_DAYANAK_SABLON = "Plan F1b-2: şablonlar e-Okul aktarımının parçasıdır (tasarım §8.1 A7)."
_DAYANAK_VELI = (
    "Tasarım §8.4 (4) ve §4.4.2: veli listesini aktarmak kişisel veri içeren dışa aktarım "
    "yetkisidir (¹⁰, yalnız program yöneticisi); §5.4: program yöneticisi listeyi onayla elle "
    "siler (plan 'F1b-5 uygulama kararları')."
)
_DAYANAK_DENETIM_KARTLARI = (
    "Tasarım §4.6.3 (bütünlük kartı program yöneticisi ve DK panosuna), §4.6.1 kural 1 "
    "(mührü tutmayan hesap kartı), §4.4.4 (geri yükleme kartı DK 'gördüm' diyene dek); "
    "plan F1b-2 'Bütünlük ucu bölünür'. Pano kalemi daraltmasıdır."
)
_DAYANAK_GORDUM = (
    "Tasarım §4.4.4 (geri yükleme kartı DK 'gördüm' diyene dek kalır), §4.4.2 ⁵ (DK kendi "
    "modülünde yazar, kayıt bütünlüğü denetimi M8'dedir; YK rolleri DK modülüne yazamaz); plan "
    "F1b-2 '\"Gördüm.\"' ve kullanıcı kararı 02.11.2026 (bir DK üyesi yeter)."
)

#: Bugünkü BÜTÜN `/api/` uçlarının kuralları (plan F1b-2 "Bugünkü uçların eşlemi").
#: `ACIK_OTURUMDA_KAPALI`'daki uç dışında her ad burada olmalıdır (test).
KURALLAR: Final[tuple[RolKurali, ...]] = (
    # ------------------------------------------------ oturum ve durum (matris dışı)
    # Hiç kesilmeyen iki yol (sağlık denetimi ve güvenlik durumu) okumada rol kapısına hiç
    # gelmez; okuma dışı yöntemleri bu tablodan geçer (kuralı yok → kapalı).
    _oku("setup-status", Satir.OTURUM),
    _oku("security-status", Satir.OTURUM),
    _oku("security-session", Satir.OTURUM),
    _oku("security-accounts", Satir.OTURUM),
    _yaz("security-unlock", "POST", Satir.OTURUM),
    _oku("security-recover", Satir.OTURUM),
    _yaz("security-recover", "POST", Satir.OTURUM),
    # ------------------------------------------------ kendi hesabı (her rolde Y)
    _yaz("app-quit", "POST", Satir.KENDI),
    _yaz("security-lock", "POST", Satir.KENDI),
    _yaz("security-change-password", "POST", Satir.KENDI),
    # Oturumdaki hesabın kendi kartları: son girişler, parola yenilenme, kâğıt çapası.
    _oku("security-integrity", Satir.KENDI),
    # Oturumdaki hesabın parola yenilenme bildirimi ve "Gördüm"ü.
    _oku("security-integrity-reset-notice", Satir.KENDI),
    _yaz("security-integrity-reset-notice", "POST", Satir.KENDI),
    # ------------------------------------------------ denetim izi
    _oku(
        "security-integrity-audit",
        Satir.DENETIM_IZI,
        yalniz=_YONETICI_VE_DK,
        dayanak=_DAYANAK_DENETIM_KARTLARI,
    ),
    # ------------------------------------------------ M8: Denetleme Kurulu (⁵)
    # Geri yükleme kartının "Gördüm"ü (plan F1b-2): yalnız Denetleme Kurulu; satırın öteki
    # hücreleri "O"dur (program yöneticisi kartı görür, kaldıramaz).
    _yaz(
        "security-integrity-restore-seen",
        "POST",
        Satir.M8,
        dipnot=5,
        dayanak=_DAYANAK_GORDUM,
    ),
    # ------------------------------------------------ erişim günlüğü (§4.6.4)
    # Okuma ekranı (plan F1b-2 "Erişim günlüğü okuma ucu"): satırın "O" hücreleri program
    # yöneticisi ve Denetleme Kuruludur, öteki hücreler "—". Okuma iz bırakmaz.
    _oku("access-log", Satir.ERISIM_GUNLUGU),
    # ------------------------------------------------ M1: okul kartı, ders yılı, kapalı günler
    _oku("setup-school-config", Satir.M1),
    _yaz("setup-school-config", "PUT", Satir.M1),
    _yaz("setup-complete", "POST", Satir.M1),
    # Genel Bakış'ın "Başlangıç Yol Haritası" işaretleri (plan F1b-2: M1).
    _yaz("setup-roadmap", "POST", Satir.M1),
    _oku("school-year-list", Satir.M1),
    _yaz("school-year-list", "POST", Satir.M1),
    _oku("school-year-terms", Satir.M1),
    _yaz("school-year-terms", "PUT", Satir.M1),
    _yaz("school-year-activate", "POST", Satir.M1),
    _oku("holiday-list", Satir.M1),
    _yaz("holiday-list", "POST", Satir.M1),
    _yaz("holiday-seed", "POST", Satir.M1),
    _yaz("holiday-detail", "DELETE", Satir.M1),
    # ------------------------------------------------ M2: personel (her rol okur)
    _oku("personnel-list", Satir.M2),
    _yaz("personnel-list", "POST", Satir.M2, yalniz=_YALNIZ_YONETICI, dayanak=_DAYANAK_PERSONEL),
    _oku("personnel-detail", Satir.M2),
    _yaz(
        "personnel-detail",
        ("PUT", "PATCH", "DELETE"),
        Satir.M2,
        yalniz=_YALNIZ_YONETICI,
        dayanak=_DAYANAK_PERSONEL,
    ),
    _yaz("personnel-leave", "POST", Satir.M2, yalniz=_YALNIZ_YONETICI, dayanak=_DAYANAK_PERSONEL),
    _yaz("personnel-merge", "POST", Satir.M2, yalniz=_YALNIZ_YONETICI, dayanak=_DAYANAK_PERSONEL),
    _yaz(
        "import-personnel-preview",
        "POST",
        Satir.M2,
        yalniz=_YALNIZ_YONETICI,
        dayanak=_DAYANAK_PERSONEL,
    ),
    _yaz(
        "import-personnel-commit",
        "POST",
        Satir.M2,
        yalniz=_YALNIZ_YONETICI,
        dayanak=_DAYANAK_PERSONEL,
    ),
    _oku("template-personnel", Satir.M2, yalniz=_YALNIZ_YONETICI, dayanak=_DAYANAK_SABLON),
    _oku("leave-pool", Satir.M2, yalniz=_YALNIZ_YONETICI, dayanak=_DAYANAK_HAVUZ),
    _yaz("leave-pool-resolve", "POST", Satir.M2, yalniz=_YALNIZ_YONETICI, dayanak=_DAYANAK_HAVUZ),
    # ------------------------------------------------ Kişisel veri: veli listesi (T5; ¹⁰)
    # Özet (sınıf başına sayı) ve şablon okumadır; satırın tek okuru program yöneticisidir.
    _oku("parent-roster", Satir.KISISEL_VERI),
    _yaz("parent-roster", "DELETE", Satir.KISISEL_VERI, dipnot=10, dayanak=_DAYANAK_VELI),
    _yaz("import-parents-preview", "POST", Satir.KISISEL_VERI, dipnot=10, dayanak=_DAYANAK_VELI),
    _yaz("import-parents-commit", "POST", Satir.KISISEL_VERI, dipnot=10, dayanak=_DAYANAK_VELI),
    _oku("template-parents", Satir.KISISEL_VERI),
    # ------------------------------------------------ M9: pano (son oturum kartı)
    _oku("dashboard-last-session", Satir.M9),
    # "Kontrol ettim": M9'un Y hücreleri (program yöneticisi ve YK); DK ve müdür görür.
    _yaz("dashboard-last-session", "POST", Satir.M9),
    # ------------------------------------------------ Ayarlar (boşta süre)
    _oku("security-idle-lock", Satir.AYARLAR),
    _yaz("security-idle-lock", "PUT", Satir.AYARLAR),
    # ------------------------------------------------ Kullanıcılar (yalnız program yöneticisi)
    # Plan F1b-2 "Kullanıcılar uçları": liste (giriş yapamayanlar ve kapalılar dahil), rol
    # seçenekleri, ayrıntı ve son girişler; hesap açma, kapama, askıdan çıkarma, parola sıfırlama;
    # hesap teslim pusulası (E63; satırın adında: "hesap açma (hesap teslim pusulası E63)").
    # Okuma da yalnız program yöneticisinindir: satırın öteki hücreleri "—"dir.
    _oku("account-list", Satir.KULLANICILAR),
    _yaz("account-list", "POST", Satir.KULLANICILAR),
    _oku("account-options", Satir.KULLANICILAR),
    _oku("account-detail", Satir.KULLANICILAR),
    _yaz("account-close", "POST", Satir.KULLANICILAR),
    _yaz("account-unsuspend", "POST", Satir.KULLANICILAR),
    _yaz("account-reset-password", "POST", Satir.KULLANICILAR),
    _yaz("account-handover-slip", "POST", Satir.KULLANICILAR),
    # ------------------------------------------------ Güvenlik (yalnız program yöneticisi)
    _yaz("security-recovery-key-pdf", "POST", Satir.GUVENLIK),
    _yaz("security-recovery-key-confirm", "POST", Satir.GUVENLIK),
    _yaz("security-recovery-key-renew", "POST", Satir.GUVENLIK),
    # Güvenlik dosyası kayıp kilidinde rol kapısı kesmez (kilit kapısının listesi geçerlidir).
    _yaz("security-state-reset", "POST", Satir.GUVENLIK),
    # Şifreli yedek: önerilen ad (okuma) ve seçilen yere kaydetme (plan F1b-3 "Ötekiler").
    _oku("encrypted-backup-download", Satir.GUVENLIK),
    _yaz("encrypted-backup-download", "POST", Satir.GUVENLIK),
    _oku("backup-external-reminder", Satir.GUVENLIK),
    _yaz("backup-external-reminder", "PUT", Satir.GUVENLIK),
    _oku("backup-list", Satir.GUVENLIK),
    _yaz("backup-restore", "POST", Satir.GUVENLIK),
    # Seçilen dosyanın başlığı: yol gövdede gittiği için POST'tur, yalnız okur; geri yüklemenin
    # ilk adımıdır, öteki rollere o kadar kapalıdır.
    _yaz("backup-inspect", "POST", Satir.GUVENLIK),
    _yaz("backup-report", "POST", Satir.GUVENLIK),
    # İki depo farkı ve sahipsiz parola kayıtlarının onayla silinmesi: güvenlik dosyasının
    # bakımıdır (tasarım §4.6.1 kural 4: "fark yonetici'ye"; plan F1b-2).
    _oku("security-integrity-two-store", Satir.GUVENLIK),
    _yaz("security-integrity-orphan-wraps", "POST", Satir.GUVENLIK),
    # ------------------------------------------------ Güncelleme denetimi (tek dış istek)
    # GET'tir ama kullanıcının başlattığı eylemdir (tasarım TK4): yazma türü.
    _yaz("update-latest", OKUMA, Satir.GUNCELLEME),
    _yaz("update-installer", OKUMA, Satir.GUNCELLEME),
)

#: Açık oturumda HİÇBİR role açık olmayan uçlar (ad → gerekçe). Kuralları yoktur.
ACIK_OTURUMDA_KAPALI: Final[Mapping[str, str]] = {
    "security-enable": (
        "İlk program yöneticisi hesabı yalnız kurulum durumunda (hesap yokken) açılır; o "
        "durumda rol kapısı devrede değildir. Açık oturumda servisin ön koşulları da reddeder "
        "(tasarım §4.4.4 `enable()`)."
    ),
}


def _kurallari_dogrula(kurallar: tuple[RolKurali, ...]) -> dict[tuple[str, str], RolKurali]:
    """Kural tablosunu kurar; matrisi aşan ya da tutarsız kuralda ValueError (modül yüklenemez)."""
    tablo: dict[tuple[str, str], RolKurali] = {}
    for kural in kurallar:
        ad = f"{kural.uc} {sorted(kural.yontemler)}"
        if not kural.yontemler or not kural.yontemler <= _KURAL_YONTEMLERI:
            raise ValueError(f"Kuralda geçersiz yöntem (OPTIONS kapalıdır): {ad}")
        if ("GET" in kural.yontemler) != ("HEAD" in kural.yontemler):
            raise ValueError(f"GET ile HEAD birlikte açılır: {ad}")
        if kural.tur is KuralTuru.OKUMA and kural.yontemler != OKUMA:
            raise ValueError(f"Okuma kuralı yalnız GET ve HEAD taşır: {ad}")
        if kural.dipnot is not None and kural.dipnot not in _satir_dipnotlari(kural.satir):
            raise ValueError(f"Kuralın dipnotu satırında yok: {ad}")
        if (kural.dipnot is not None or kural.yalniz is not None) and not kural.dayanak.strip():
            raise ValueError(f"Dipnotlu ya da daraltılmış kural dayanak ister: {ad}")
        if kural.yalniz is not None:
            turetilen = (
                okuyabilen_roller(kural.satir)
                if kural.tur is KuralTuru.OKUMA
                else yazabilen_roller(kural.satir, kural.dipnot)
            )
            if not kural.yalniz or not kural.yalniz <= turetilen:
                raise ValueError(f"Kural matrisi aşıyor (daraltma genişletemez): {ad}")
        if not kural_rolleri(kural):
            raise ValueError(f"Kural hiçbir role açılmıyor: {ad}")
        if kural.uc in ACIK_OTURUMDA_KAPALI:
            raise ValueError(f"Açık oturumda kapalı uç kural taşıyamaz: {ad}")
        for yontem in kural.yontemler:
            if (kural.uc, yontem) in tablo:
                raise ValueError(f"Aynı (uç, yöntem) iki kuralda: {kural.uc} {yontem}")
            tablo[(kural.uc, yontem)] = kural
    return tablo


_TABLO_KURAL: Final[dict[tuple[str, str], RolKurali]] = _kurallari_dogrula(KURALLAR)
_TABLO_ROLLER: Final[dict[tuple[str, str], frozenset[str]]] = {
    cift: kural_rolleri(kural) for cift, kural in _TABLO_KURAL.items()
}


def acik_roller(uc: str, yontem: str) -> frozenset[str]:
    """(uç, yöntem) çiftinin açık olduğu roller (parametre denetçisi hesaba katılmaz)."""
    return _TABLO_ROLLER.get((uc, yontem.upper()), frozenset())


def izinli_mi(
    uc: str | None, yontem: str, rol: str | None, request: HttpRequest | None = None
) -> bool:
    """Rol bu (uç, yöntem)'e açık mı? Adsız uç, bilinmeyen rol ya da kuralsız çift: hayır.

    Kuralın parametre denetçisi varsa istekle sorulur (istek yoksa fail-closed: hayır).
    """
    if uc is None or rol is None:
        return False
    cift = (uc, yontem.upper())
    if rol not in _TABLO_ROLLER.get(cift, frozenset()):
        return False
    denetci = _TABLO_KURAL[cift].parametre
    if denetci is None:
        return True
    return request is not None and denetci(request)


# ---------------------------------------------------------------------------
# Bekleyen hücreler ve dipnotlar (modül başlığı "BEKLEYENLER")
# ---------------------------------------------------------------------------
def _bekleyen(satir: Satir, roller: Iterable[str], faz: str) -> dict[tuple[Satir, str], str]:
    return {(satir, rol): faz for rol in roller}


#: Ucu ya da servisi henüz olmayan Y hücreleri → bağlanacakları faz (tasarım §14 faz
#: ataması). Yalnız küçülebilir; testte anlık görüntüdür.
BEKLEYEN_HUCRELER: Final[Mapping[tuple[Satir, str], str]] = {
    # Kişiler ve organlar: YK rollerinin kişi yazımı OAB kişileriyle (personel e-Okul
    # kaydı yalnız program yöneticisinin; `_DAYANAK_PERSONEL`).
    **_bekleyen(Satir.M2, sorted(YK_ROLLERI), "F1c"),
    # Genel kurul (müdürün ¹ yazıları dahil).
    **_bekleyen(Satir.M3, (YONETICI, *sorted(YK_ROLLERI), MUDUR), "F2"),
    # YK toplantı ve karar; gelir-gider (mali kayıtları yalnız muhasip girer).
    **_bekleyen(Satir.M4, (YONETICI, *sorted(YK_ROLLERI)), "F3"),
    **_bekleyen(Satir.M5, (AccountRole.MUHASIP.value,), "F3"),
    # Harcama zinciri (müdürün ⁴ talebi dahil), bütçe-ilan-bildirim, müdürün md. 27/3 yazısı,
    # devir-teslim ve dönem kapanışı.
    **_bekleyen(Satir.M6, (YONETICI, *sorted(YK_ROLLERI), MUDUR), "F4"),
    **_bekleyen(Satir.M7, (YONETICI, *sorted(YK_ROLLERI)), "F4"),
    **_bekleyen(Satir.MUDUR_YAZISI, (MUDUR,), "F4"),
    **_bekleyen(Satir.M11, (YONETICI, *sorted(YK_ROLLERI)), "F4"),
    # Gelen-giden evrak: ilk kullanımı genel kurulun evrakıdır.
    **_bekleyen(Satir.M10, (YONETICI, *sorted(YK_ROLLERI)), "F2"),
    # Kantin (F5) ve servis (F6) aynı satırdadır; ilk bağlanacağı faz.
    **_bekleyen(Satir.M13_M14, (YONETICI, *sorted(YK_ROLLERI)), "F5"),
    # Personel modülü (doğrudan işveren okullar; K3) sürüm 2.
    **_bekleyen(Satir.M15, (YONETICI, *sorted(YK_ROLLERI)), "F8+"),
    # Kişisel veri: program yöneticisinin hücresi veli listesinin uçlarıyla bağlandı (F1b 5.
    # adım); adlı E07/E08 çıktısının kapısı ¹⁰ dipnotunun eylemidir (`BEKLEYEN_DIPNOTLAR`, F2).
    # F1b'de bekleyen kalmadı: Kullanıcılar (program yöneticisi) uçlarıyla, Denetleme Kurulunun
    # M8 hücresi geri yükleme kartının "Gördüm"üyle bağlandı (F1b-2 (c)). DK
    # modülünün öteki işleri (görev bölümü, denetim planı, rapor, md. 14/5 çağrısı) F4'tedir; M8
    # hücresi satır düzeyindedir, ilk ucu bağlayınca bekleyenden çıkar.
}

#: Gerçek servisi henüz olmayan dipnotlar → faz. Dipnotun kapı testi bugünden vardır
#: (`test_yetki_kapisi.py`, sahte kayıtla); gerçek servis gelince satır silinir.
BEKLEYEN_DIPNOTLAR: Final[Mapping[int, str]] = {
    1: "F2",
    2: "F3",
    3: "F4",
    4: "F4",
    # 5: bağlı — DK'nin "Gördüm"ü (`Eylem.GERI_YUKLEME_GORDUM`, `hesaplar.acknowledge_restore`).
    6: "F4",
    7: "F2",
    8: "F4",
    9: "F5",
    10: "F2",
}


def etkin_hucreler(rol: str) -> tuple[Satir, ...]:
    """Rolün bugün programda yazabildiği satırlar: MATRIS'te Y olup bekleyende olmayanlar.

    Hesap teslim pusulası (E63) bu satırları basar; her satırın BUGÜNKÜ işinin adı ve o işi yapan
    uçlar `services.hesap_teslim_pusulasi.BUGUNKU_ISLER`'dedir (orkestratör maddesi F-4). Bir faz
    bir hücreyi bekleyenden çıkarınca o satırın bugünkü adı da orada eklenir (`test_evrak_kurallari`
    eksik adı ve uçsuz adı düşürür).
    """
    return tuple(
        satir
        for satir, hucreler in MATRIS.items()
        if rol in hucreler and hucreler[rol][0] == YAZAR and (satir, rol) not in BEKLEYEN_HUCRELER
    )


# ---------------------------------------------------------------------------
# Yetenekler (ön yüz süzmesinin tek kaynağı)
# ---------------------------------------------------------------------------
def _ciftler(*ciftler: tuple[str, str | Iterable[str]]) -> frozenset[tuple[str, str]]:
    sonuc: set[tuple[str, str]] = set()
    for uc, yontemler in ciftler:
        sonuc |= {(uc, y) for y in _yontemler(yontemler)}
    return frozenset(sonuc)


#: Yetenek adı → (uç, yöntem) kümesi. Rolün yeteneği kümedeki HER çift ona açıksa vardır
#: (`yetenekler`); değer kurallardan türer. Ön yüzün kullandığı adlar.
YETENEKLER: Final[Mapping[str, frozenset[tuple[str, str]]]] = {
    # Kullanıcılar ekranı: liste, seçenekler, ayrıntı, hesap işlemleri ve hesap teslim pusulası
    # (hepsi birlikte).
    "kullanicilar": _ciftler(
        ("account-list", ("GET", "POST")),
        ("account-options", "GET"),
        ("account-detail", "GET"),
        ("account-close", "POST"),
        ("account-unsuspend", "POST"),
        ("account-reset-password", "POST"),
        ("account-handover-slip", "POST"),
    ),
    # Bütünlük kartları: denetim kartları (program yöneticisi ve DK) ve iki depo farkı.
    "butunluk_denetim": _ciftler(("security-integrity-audit", "GET")),
    # Geri yükleme kartının "Gördüm" düğmesi (yalnız Denetleme Kurulu).
    "geri_yukleme_gordum": _ciftler(("security-integrity-restore-seen", "POST")),
    # Erişim Günlüğü ekranı (program yöneticisi ve Denetleme Kurulu).
    "erisim_gunlugu": _ciftler(("access-log", "GET")),
    "iki_depo": _ciftler(
        ("security-integrity-two-store", "GET"), ("security-integrity-orphan-wraps", "POST")
    ),
    # Ayarlar → Güvenlik'in kurtarma ve yedek kartları.
    "guvenlik": _ciftler(
        ("security-recovery-key-pdf", "POST"),
        ("security-recovery-key-confirm", "POST"),
        ("security-recovery-key-renew", "POST"),
        ("encrypted-backup-download", ("GET", "POST")),
        ("backup-external-reminder", ("GET", "PUT")),
        ("backup-list", "GET"),
        ("backup-restore", "POST"),
        ("backup-inspect", "POST"),
        ("backup-report", "POST"),
    ),
    "guncelleme": _ciftler(("update-latest", "GET"), ("update-installer", "GET")),
    "bosta_sure_yazma": _ciftler(("security-idle-lock", "PUT")),
    # Okul sekmeleri: yazma denetimleri; öteki rollerde sekmeler salt okurdur.
    "okul_karti_yazma": _ciftler(("setup-school-config", "PUT")),
    "ders_yili_yazma": _ciftler(
        ("school-year-list", "POST"),
        ("school-year-terms", "PUT"),
        ("school-year-activate", "POST"),
    ),
    "kapali_gun_yazma": _ciftler(
        ("holiday-list", "POST"), ("holiday-seed", "POST"), ("holiday-detail", "DELETE")
    ),
    "kurulum_tamamlama": _ciftler(("setup-complete", "POST")),
    "yol_haritasi": _ciftler(("setup-roadmap", "POST")),
    "son_oturum_onay": _ciftler(("dashboard-last-session", "POST")),
    # Kişiler: personel yazmaları, e-Okul aktarımı ve ayrılış havuzu.
    "kisi_yazma": _ciftler(
        ("personnel-list", "POST"),
        ("personnel-detail", ("PUT", "PATCH", "DELETE")),
        ("personnel-leave", "POST"),
        ("personnel-merge", "POST"),
    ),
    "eokul_aktarimi": _ciftler(
        ("import-personnel-preview", "POST"),
        ("import-personnel-commit", "POST"),
        ("template-personnel", "GET"),
    ),
    "ayrilis_havuzu": _ciftler(("leave-pool", "GET"), ("leave-pool-resolve", "POST")),
    # Kişiler → Veli Listesi: özet, aktarım (önizleme ve uygulama), şablon ve silme (hepsi
    # birlikte; kişisel veri satırı, yalnız program yöneticisi).
    "veli_listesi": _ciftler(
        ("parent-roster", ("GET", "DELETE")),
        ("import-parents-preview", "POST"),
        ("import-parents-commit", "POST"),
        ("template-parents", "GET"),
    ),
}


def _yetenekleri_dogrula() -> None:
    for ad, ciftler in YETENEKLER.items():
        eksik = sorted(cift for cift in ciftler if cift not in _TABLO_ROLLER)
        if not ciftler or eksik:
            raise ValueError(f"Yeteneğin kuralı olmayan çifti var ({ad}): {eksik}")


_yetenekleri_dogrula()


def yetenekler(rol: str | None) -> list[str]:
    """Rolün yetenekleri (sıralı). Bilinmeyen ya da boş rol: hiçbiri."""
    if rol is None:
        return []
    return sorted(
        ad
        for ad, ciftler in YETENEKLER.items()
        if all(rol in _TABLO_ROLLER[cift] for cift in ciftler)
    )


# ---------------------------------------------------------------------------
# Yetki kapısı (servis katmanı)
# ---------------------------------------------------------------------------
class Eylem(StrEnum):
    """Servis katmanının kapalı eylem kümesi (tasarım §4.4.2 dipnotlar 1-10; plan F1b-2)."""

    # Dipnotsuz sistem işleri (F1b'de bağlı).
    HESAP_YONETIMI = "HESAP_YONETIMI"
    KURTARMA_ANAHTARI = "KURTARMA_ANAHTARI"
    GERI_YUKLEME = "GERI_YUKLEME"
    YEDEK_INDIRME = "YEDEK_INDIRME"
    BOSTA_SURE_YAZMA = "BOSTA_SURE_YAZMA"
    # ¹ genel kurul
    GENEL_KURUL_YAZMA = "GENEL_KURUL_YAZMA"
    GENEL_KURUL_YENI_OKUL_DAVETI = "GENEL_KURUL_YENI_OKUL_DAVETI"
    OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR = "OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR"
    # ² mali kayıtlar ve rol-özel işaretler
    MALI_KAYIT = "MALI_KAYIT"
    ISARET_DEFTERE_GECIRME = "ISARET_DEFTERE_GECIRME"
    ISARET_TEFBIS_GIRISI = "ISARET_TEFBIS_GIRISI"
    ISARET_KARAR_DEFTERE_ISLENDI = "ISARET_KARAR_DEFTERE_ISLENDI"
    KARAR_DEFTERDE_SAKAT = "KARAR_DEFTERDE_SAKAT"
    # ³ ⁴ harcama zinciri
    HARCAMA_MALI_HALKA = "HARCAMA_MALI_HALKA"
    HARCAMA_KARAR_KOMISYON_BELGE = "HARCAMA_KARAR_KOMISYON_BELGE"
    HARCAMA_TALEP = "HARCAMA_TALEP"
    # ⁵ Denetleme Kurulu
    DENETIM_YAZMA = "DENETIM_YAZMA"
    GERI_YUKLEME_GORDUM = "GERI_YUKLEME_GORDUM"
    # ⁶ müdürün md. 27/3 uyarısı
    MUDUR_UYARISI = "MUDUR_UYARISI"
    # ⁷ gelen-giden evrak (müdür yazmaz; kendi yazısının kaydı müdür yazısı eyleminin
    # programca yapılan yan etkisidir — ¹, ⁴, ⁶ eylemleri; ayrı eylemi yoktur)
    EVRAK_KAYDI = "EVRAK_KAYDI"
    # ⁸ dönem kilidi, hesap geçişi, DEK yenilemesi
    DONEM_KILIDI = "DONEM_KILIDI"
    HESAP_GECISI = "HESAP_GECISI"
    DEK_YENILEME = "DEK_YENILEME"
    # ⁹ kantin ve servis
    KANTIN_SERVIS_YAZMA = "KANTIN_SERVIS_YAZMA"
    # ¹⁰ kişisel veri içeren çıktı ve maskesiz okuma
    KISISEL_VERI_CIKTISI = "KISISEL_VERI_CIKTISI"
    MASKESIZ_TCKN = "MASKESIZ_TCKN"


@dataclass(frozen=True)
class EylemKurali:
    """Bir eylemin satırı, dipnotu, izinli rolleri ve kayıt kuralları.

    `kapanmis_donemde`: kapanmış dönemin kaydına da yazılabilir (tasarım §4.4.2 "Kapanmış
    dönem her rolde salt okurdur"; yalnız işaret alanları — §5 O2 beyaz listesi). Yeniden
    basım bir eylem değildir: evrak çıktısı okumanın kapsamındadır, kuralı evrak hattıyla gelir.
    `sahiplik`: kayıt, sahibi olan rolün hesaplarının ortak kaydıdır (plan F1b-2 "Kayıt
    sahipliği rol düzeyindedir"); başka rolün kaydı düzenlenmez.
    """

    satir: Satir
    roller: frozenset[str]
    dipnot: int | None = None
    kapanmis_donemde: bool = False
    sahiplik: bool = False
    dayanak: str = ""


def _ek(
    satir: Satir,
    roller: Iterable[str],
    *,
    dipnot: int | None = None,
    kapanmis_donemde: bool = False,
    sahiplik: bool = False,
    dayanak: str = "",
) -> EylemKurali:
    return EylemKurali(satir, frozenset(roller), dipnot, kapanmis_donemde, sahiplik, dayanak)


_YK_VE_YONETICI: Final = YK_ROLLERI | {YONETICI}
_MUHASIP: Final = frozenset({AccountRole.MUHASIP.value})
_SEKRETER: Final = frozenset({AccountRole.SEKRETER.value})

#: Eylem → kural. Her eylemin kuralı vardır; izinli roller satırın Y hücrelerini aşamaz.
EYLEM_KURALLARI: Final[Mapping[Eylem, EylemKurali]] = {
    Eylem.HESAP_YONETIMI: _ek(
        Satir.KULLANICILAR, (YONETICI,), dayanak="Tasarım §4.4.2 Kullanıcılar satırı, §4.4.5"
    ),
    Eylem.KURTARMA_ANAHTARI: _ek(
        Satir.GUVENLIK, (YONETICI,), dayanak="Tasarım §4.4.2 Güvenlik satırı; TK9"
    ),
    Eylem.GERI_YUKLEME: _ek(
        Satir.GUVENLIK, (YONETICI,), dayanak="Tasarım §4.4.2 Güvenlik satırı, §4.4.4"
    ),
    Eylem.YEDEK_INDIRME: _ek(
        Satir.GUVENLIK,
        (YONETICI,),
        dayanak="Tasarım §4.4.2 Güvenlik satırı (şifreli yedeğin kaydedilmesi)",
    ),
    Eylem.BOSTA_SURE_YAZMA: _ek(
        Satir.AYARLAR, (YONETICI,), dayanak="Tasarım §4.4.2 Ayarlar satırı (boşta süre)"
    ),
    Eylem.GENEL_KURUL_YAZMA: _ek(
        Satir.M3, _YK_VE_YONETICI, dipnot=1, dayanak="¹ müdür genel kurulun öteki işlerinde okur"
    ),
    Eylem.GENEL_KURUL_YENI_OKUL_DAVETI: _ek(
        Satir.M3, (MUDUR,), dipnot=1, sahiplik=True, dayanak="¹; md. 9/1"
    ),
    Eylem.OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR: _ek(
        Satir.M3, (MUDUR,), dipnot=1, sahiplik=True, dayanak="¹; md. 9/6, 13/8"
    ),
    Eylem.MALI_KAYIT: _ek(Satir.M5, _MUHASIP, dipnot=2, dayanak="²; K2, D2"),
    Eylem.ISARET_DEFTERE_GECIRME: _ek(
        Satir.M5, _MUHASIP, dipnot=2, kapanmis_donemde=True, dayanak="²; §5 O2"
    ),
    Eylem.ISARET_TEFBIS_GIRISI: _ek(
        Satir.M5, (YONETICI,), dipnot=2, kapanmis_donemde=True, dayanak="²; §5 O2; md. 23/5"
    ),
    Eylem.ISARET_KARAR_DEFTERE_ISLENDI: _ek(
        Satir.M4, _SEKRETER, dipnot=2, kapanmis_donemde=True, dayanak="²; §5 O2"
    ),
    Eylem.KARAR_DEFTERDE_SAKAT: _ek(Satir.M4, _SEKRETER, dipnot=2, dayanak="²"),
    Eylem.HARCAMA_MALI_HALKA: _ek(Satir.M6, _MUHASIP, dipnot=3, dayanak="³; D2"),
    Eylem.HARCAMA_KARAR_KOMISYON_BELGE: _ek(Satir.M6, _YK_VE_YONETICI, dipnot=3, dayanak="³"),
    Eylem.HARCAMA_TALEP: _ek(
        Satir.M6, (MUDUR,), dipnot=4, sahiplik=True, dayanak="⁴; md. 18/1; §15 M-11"
    ),
    Eylem.DENETIM_YAZMA: _ek(
        Satir.M8, (DENETLEME_KURULU,), dipnot=5, sahiplik=True, dayanak="⁵; md. 14/1, 14/4, 14/5"
    ),
    Eylem.GERI_YUKLEME_GORDUM: _ek(
        Satir.M8, (DENETLEME_KURULU,), dipnot=5, dayanak="⁵; §4.4.4 (DK 'gördüm')"
    ),
    Eylem.MUDUR_UYARISI: _ek(
        Satir.MUDUR_YAZISI, (MUDUR,), dipnot=6, sahiplik=True, dayanak="⁶; md. 27/3"
    ),
    Eylem.EVRAK_KAYDI: _ek(
        Satir.M10,
        _YK_VE_YONETICI,
        dipnot=7,
        dayanak="⁷ (müdür yazamaz; kendi yazısını program, yazının eylemiyle işler)",
    ),
    Eylem.DONEM_KILIDI: _ek(Satir.M11, (YONETICI,), dipnot=8, dayanak="⁸; R12"),
    Eylem.HESAP_GECISI: _ek(Satir.M11, (YONETICI,), dipnot=8, dayanak="⁸; §4.4.5"),
    Eylem.DEK_YENILEME: _ek(Satir.M11, (YONETICI,), dipnot=8, dayanak="⁸; TK12"),
    Eylem.KANTIN_SERVIS_YAZMA: _ek(
        Satir.M13_M14, _YK_VE_YONETICI, dipnot=9, dayanak="⁹ müdür iş yapan rol değildir"
    ),
    Eylem.KISISEL_VERI_CIKTISI: _ek(
        Satir.KISISEL_VERI, (YONETICI,), dipnot=10, dayanak="¹⁰; R9; BSG Yön. md. 5/8"
    ),
    Eylem.MASKESIZ_TCKN: _ek(Satir.KISISEL_VERI, (YONETICI,), dipnot=10, dayanak="¹⁰; K9"),
}

#: Gerçek servise henüz bağlanmamış eylemler → faz (yalnız küçülebilir; test kaynakta
#: `Eylem.<AD>` çağrısını arar). Bağlı olanlar: hesap yönetimi, kurtarma anahtarı, geri
#: yükleme, şifreli yedeğin kaydedilmesi, boşta süre yazımı, geri yükleme kartının "Gördüm"ü (⁵).
BAGLANMAMIS_EYLEMLER: Final[Mapping[Eylem, str]] = {
    Eylem.GENEL_KURUL_YAZMA: "F2",
    Eylem.GENEL_KURUL_YENI_OKUL_DAVETI: "F2",
    Eylem.OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR: "F2",
    Eylem.MALI_KAYIT: "F3",
    Eylem.ISARET_DEFTERE_GECIRME: "F3",
    Eylem.ISARET_TEFBIS_GIRISI: "F3",
    Eylem.ISARET_KARAR_DEFTERE_ISLENDI: "F3",
    Eylem.KARAR_DEFTERDE_SAKAT: "F3",
    Eylem.HARCAMA_MALI_HALKA: "F4",
    Eylem.HARCAMA_KARAR_KOMISYON_BELGE: "F4",
    Eylem.HARCAMA_TALEP: "F4",
    Eylem.DENETIM_YAZMA: "F4",
    Eylem.MUDUR_UYARISI: "F4",
    Eylem.EVRAK_KAYDI: "F2",
    Eylem.DONEM_KILIDI: "F4",
    Eylem.HESAP_GECISI: "F4",
    Eylem.DEK_YENILEME: "F4",
    Eylem.KANTIN_SERVIS_YAZMA: "F5",
    Eylem.KISISEL_VERI_CIKTISI: "F2",
    Eylem.MASKESIZ_TCKN: "F3",
}


def _eylemleri_dogrula() -> None:
    if set(EYLEM_KURALLARI) != set(Eylem):
        raise ValueError("Her eylemin bir kuralı olmalıdır.")
    for eylem, kural in EYLEM_KURALLARI.items():
        if kural.satir is Satir.OTURUM:
            raise ValueError(f"Eylem matris satırını anmalıdır: {eylem}")
        # Eylemin andığı dipnot matriste olmalıdır; satırında olması gerekmez (² M4'ün
        # "deftere işlendi" işaretini de sayar). Dipnotlu hücreyi yalnız kendi satırındaki
        # dipnot açar, okur hücresini yalnız ² (`yazabilen_roller`).
        if kural.dipnot is not None and kural.dipnot not in MATRIS_DIPNOTLARI:
            raise ValueError(f"Eylemin dipnotu matriste yok: {eylem}")
        if not kural.roller or not kural.roller <= yazabilen_roller(kural.satir, kural.dipnot):
            raise ValueError(f"Eylemin rolleri matrisi aşıyor: {eylem}")


_eylemleri_dogrula()


class YetkiKaydi(Protocol):
    """Kapının sorduğu kayıt: dönemi kapanmış mı, hangi rolün kaydı (yoksa None)."""

    @property
    def donem_kapali(self) -> bool: ...

    @property
    def sahip_rol(self) -> str | None: ...


def yetki(rol: str | None, eylem: Eylem, kayit: YetkiKaydi | None = None) -> None:
    """Rol bu eylemi (bu kayıtta) yapabilir mi? Yapamazsa `RolYetkisiz` (403 `rol_yetkisiz`).

    Sırasıyla: rol eylemin izinli rollerinde mi; kayıt verildiyse kapanmış dönemde yalnız
    `kapanmis_donemde` eylemleri, sahiplikli eylemde yalnız kaydın sahibi olan rol.
    "Adına" ya da operatör parametresi yoktur: her yazma girenin rolüne düşer.
    """
    kural = EYLEM_KURALLARI[eylem]
    if rol is None or rol not in kural.roller:
        raise RolYetkisiz
    if kayit is None:
        return
    if kayit.donem_kapali and not kural.kapanmis_donemde:
        raise RolYetkisiz
    if kural.sahiplik and kayit.sahip_rol is not None and kayit.sahip_rol != rol:
        raise RolYetkisiz


def yetki_oturum(eylem: Eylem, kayit: YetkiKaydi | None = None) -> None:
    """`yetki`, rol istek başındaki yazar bağlamından (modül başlığı); yazar yok ya da
    `SISTEM` ise ret."""
    kim = yazar()
    if kim is None or kim.sistem_mi:
        raise RolYetkisiz
    yetki(kim.rol, eylem, kayit)


# ---------------------------------------------------------------------------
# Uç adı ve parametre denetçileri (aile iskeletinden AYNEN)
# ---------------------------------------------------------------------------
def uc_adi(path_info: str) -> str | None:
    """Yolun Django URL adı (ad alanlı include'da `ad_alani:ad`); çözülemezse None."""
    try:
        eslesme = resolve(path_info)
    except Resolver404:
        return None
    return eslesme.view_name or None


def utf8_mi(charset: str | None) -> bool:
    """`Content-Type`'taki `charset` yok ya da UTF-8 mi? (Başkası → fail-closed.)"""
    if charset is None:
        return True
    return charset.strip().strip('"').lower().replace("_", "-") in UTF8_ADLARI


@dataclass(frozen=True)
class SorguSiniri:
    """GET ucunda sorgu dizesinde bulunabilecek anahtarlar (başkası → ret)."""

    izinli: frozenset[str]

    def __call__(self, request: HttpRequest) -> bool:
        return set(request.GET.keys()) <= self.izinli


@dataclass(frozen=True)
class GovdeYasagi:
    """Gövdede ve sorgu dizesinde bulunamayacak anahtarlar (varlık yeter → ret)."""

    yasak: frozenset[str]

    def __call__(self, request: HttpRequest) -> bool:
        if set(request.GET.keys()) & self.yasak:
            return False
        try:
            ham = request.body
        except Exception:  # okunamayan (ör. aşırı büyük) gövde: fail-closed
            return False
        if not ham.strip():
            return True
        if (request.content_type or "").lower() != JSON_ICERIK:
            return False
        if not utf8_mi((request.content_params or {}).get("charset")):
            return False
        try:
            govde = json.loads(ham)
        except (ValueError, UnicodeDecodeError):
            return False
        if not isinstance(govde, dict):
            return False
        return not (set(govde) & self.yasak)


def yalniz_sorgu(*anahtarlar: str) -> SorguSiniri:
    return SorguSiniri(frozenset(anahtarlar))


def govdede_yok(*anahtarlar: str) -> GovdeYasagi:
    return GovdeYasagi(frozenset(anahtarlar))
