"""Oturum — süreç içi TEK oturum nesnesi (tasarım §4.1, §4.4.3, TK14; plan F1b-1 "Oturum").

Aile iskeletinin kip katmanının (görevli kipi / yönetici kipi) yerini alır; "kip"
kavramı bilinçli olarak kalkar (tasarım §12.B). Programda aynı anda en çok BİR
oturum vardır: kilidi açan hesap (kimlik, tanıtıcı, rol). Kullanıcı değiştirmek =
Kilitle + başka hesapla açmak (TK14). Kilit kapısı (`lock_middleware`), 2. adımın
`RolMiddleware`'i, denetim izi yazıcısı (alt commit c) ve uzun iş sayacı aynı nesneyi
okur (`OTURUM`); ikinci bir durum kaynağı açılmaz.

DURUMLAR (API ve arayüz bu dizeleri kullanır; `durum()`):

* ``kurulum`` — ilk program yöneticisi hesabı kurulmamış;
* ``guvenlik_dosyasi_kayip`` — parmak izi dolu ama `guvenlik.json` yok ya da
  kullanılamıyor (§4.3 tehdit 8; `app_password.security_file_missing`); kilit açılamaz;
* ``kilitli`` — hesap kurulu, oturum yok (DEK bellekte değil);
* ``acik`` — oturum açık: hesap, rol, DEK ve iz anahtarı (İA) bellekte.

YENİDEN_BAŞLAT_GEREK (§4.4.3) burada yoktur: geri yükleme sonrası kapı
(`restart_gate`) bütün API'yi 503 ile keser, oturum ucu da dahil.

AÇILIŞ YALNIZ AÇIK ÇAĞRIYLA. Oturumu `ac()` açar; onu yalnız güvenlik çekirdeğinin
üç yolu çağırır: kilit açma (`app_password.unlock`), kurtarma anahtarıyla açılış
(`app_password.unlock_with_recovery`) ve kurulumdaki ilk hesap (`app_password.enable`).
Aile iskeletinin kip katmanı açılışı `crypto.key_epoch()` sayacının değişiminden
çıkarıyordu; sayaç hesap bilgisi taşımadığı için o yol kalktı (parola değişimi de
"yeni açılış" sayılıyordu). DEK ve İA belleğe `ac()` içinde, hesapla AYNI kilit
altında alınır; kilitleme ikisini birlikte düşürür. Oturum açık görünüp DEK'in
olmadığı an yoktur: DEK oturumun dışından düşürülmüşse oturum kapanmış sayılır.
Açıkken yeniden `ac()` çağrılırsa (kilit ekranı dışından gelen ikinci bir açma)
oturum o hesaba geçer: parolayla kanıtlanmış bir "Kilitle + aç"tır, DEK aynıdır,
uçuştaki istekler etkilenmez.

BOŞTA KİLİT (TK14, §4.4.3). Zamanlayıcı iş parçacığı YOKTUR; kural her API isteğinin
başında tembel değerlendirilir (`degerlendir`, ara katman çağırır): ``son_etkinlik +
N <= şimdi`` ise oturum kilitlenir ve DEK ile İA bellekten silinir (ailede süre
dolunca görevli kipine inilir, DEK kalırdı; OAB'de iniş yoktur). Sınır anı kilit
sayılır (fail-closed). `son_etkinlik` YALNIZ `X-OD-Etkinlik` başlıklı (kullanıcı
eylemli) ve kapıdan geçen istekle tazelenir (`etkinlik`); durum ve pano yoklamaları
tazelemez. Süresi dolmuş oturum geç gelen başlıklı bir istekle dirilmez. Mutlak süre
YOKTUR (TK14; görevli kipi olmadığından ailenin 30 dk gerekçesi düşer).

* N, `SchoolConfig.idle_lock_minutes`'tir (varsayılan 10, 3-30; tasarım §13 D11:
  aile varsayılanına sessiz düşüş yok). Değer süreç içinde önbelleğe alınır, satır
  kaydedilince boşalır (`OkulConfig.ready` bağlar): sıcak yol veritabanına gitmez.
  Üstelik geçen süre alt sınırın (3 dk) altındaysa değer hiç sorulmaz. Satır yoksa
  alanın kendi varsayılanı (10) geçer; veritabanı okunamazsa da o geçer ama önbelleğe
  alınmaz (bir sonraki değerlendirme yeniden okur).
* **Kurulum sihirbazı bitene dek boşta kilit yoktur** (tasarım §13 D15; TB19 dersi):
  sihirbazın ilk adımında kurtarma anahtarı ekrandadır, kilitlenme pencereyi yeniden
  yükleyip anahtarı ekrandan silerdi. `SchoolConfig.setup_completed` yalnız süre
  dolduğu anda sorulur; olumlu yanıt önbelleğe alınır (kurulum tek yönlüdür), yani
  kurulumu bitmiş programda hiç sorulmaz. Kurulum sürüyorsa sayaç yeniden başlar.
  Veritabanı okunamazsa kurulum o an için tamamlanmış sayılır (fail-closed: süre
  işler) ama bu yanıt önbelleğe ALINMAZ: tek bir geçici hata sihirbaz sürerken
  D15'i süreç sonuna dek kapatıp kurtarma anahtarını ekrandan sildirmesin. Elle
  Kilitle kurulumda da çalışır. `setup/complete/` sonrası sayaç sıfırdan başlar
  (`sureyi_yeniden_baslat`).
* **Saat uykuyu sayar** (`UykuyuSayanSaat`; aşağıda). Ön yüzdeki geri sayım yalnız
  görseldir; karar her istekte sunucuda verilir.

Tembel seçimin kalan riski (tasarım §4.3 tehdit 3): hiç istek gelmezse (pencere
kapalı ama süreç açık) DEK süre dolduktan sonra da bellektedir; ön yüz durum ucunu
kısa aralıkla yokladığı için pratikte süre kısadır.

UZUN İŞ (§4.2, §4.4.3; denetim UY-1). Uzun yazma işi sürerken (`shared.bakim.UZUN_ISLER`
sıfır değilken) hem elle hem boşta kilit ERTELENİR: oturum açık kalır, `kilit_bekliyor`
işaretlenir (ekranda "İşlem bitince kilitlenecek"), etkinlik oturumu artık
diriltmez; iş bitince gelen İLK istekte kilit uygulanır. DEK işin ortasında silinmez.
Düzenli kapanışın kilidi (`kapanista_kilitle`) ertelenmez.

UÇUŞTAKİ İSTEKLER. Kilitleme (elle, boşta, bekleyen, kapanış) uçuştaki API isteklerinin
bitmesini bekler (`UCUSTA`; ara katman her `/api/` isteğini sayar). Kilit kararı
verildiği an oturum yeni istekler için kapanır (423), DEK uçuştakiler bitince düşer.
Bekleme sınırlıdır (`UCUSTA_BEKLEME_SN`): süre dolarsa kilit yine uygulanır ve günlüğe
uyarı düşer (fail-closed; uçuştaki istek `KeyMissingError` alır, işlemi geri sarılır).
Kilidi isteyen istek kendini beklemez (bağlam değişkeni `_bu_istek_sayildi`).

KİLİT SIRASI VE İŞ PARÇACIKLARI (waitress birden çok iş parçacığında koşar).
Oturumun kilidi (`_kilit`) yalnız bellekteki alanları korur ve kısa tutulur: içinde
Argon2id, SQLite yazımı, dosya yazımı ya da bekleme YAPILMAZ. Veritabanından okunan
iki ayar (boşta süre, kurulum bitti mi) kilit dışında okunur. Kilit tutulurken
çağrılanlar yalnız `crypto`'nun anahtar tutucusu, saat ve uzun iş sayacıdır; ters
yönde (onların içinden oturuma) çağrı yoktur. Uçuştaki isteklerin beklenmesi oturum
kilidi bırakılmış hâlde yapılır; bekleme sürerken oturuma yeniden açılan (`ac`)
hesap, bekleyen kilidin sonunda düşürülmez (`_nesil`).

YAZAR BAĞLAMI (TK16, §4.1). Her yazma, oturumdaki hesabı "yazar" olarak denetim izine
verir (alt commit c). Yazar istek başında alınır (bağlam değişkeni; ara katman
`yazar_olarak` ile kurar) ve istek boyunca değişmez: istek sürerken oturum kilitlense
de o isteğin yazarı açılıştaki hesaptır. Kullanıcı eylemi olmayan iş (gün işleri,
`od-gunluk`) `sistem_olarak()` ile `SISTEM`'i açıkça verir. Bağlam yoksa `yazar()`
None döner; yazar bağlamı olmayan yazma alt commit (c)'de reddedilir.

SAAT: UYKU DA SÜREDİR (aile iskeletinin denetim bulgusu). Tasarım §4.5 kapak
kapatmayı ve kullanıcının başlattığı uykuyu engellemez. `time.monotonic` Linux'ta
(Pardus) `CLOCK_MONOTONIC`tır ve askıya alınan süreyi SAYMAZ: oturum açıkken
uyutulup ertesi sabah uyandırılan makinede boşta süre uykudan önce kalan yerden devam
ederdi. `UykuyuSayanSaat` iki kaynağın son okumadan beri ilerlemesinin BÜYÜĞÜNÜ
biriktirir: monoton kaynak (Linux'ta `CLOCK_BOOTTIME`, yoksa `time.monotonic`; duvar
saati geri alınsa da ilerler) ve duvar saati (`time.time`; uyanışta uyunan süre
kadar ileri geçer). Duvar saati ileri sıçrarsa süre erken dolar (fail-closed), geri
sıçrarsa monoton ilerleme kullanılır, süre UZAMAZ.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, Literal

from django.db import DatabaseError

from apps.okul.models import (
    IDLE_LOCK_MINUTES_DEFAULT,
    IDLE_LOCK_MINUTES_MAX,
    IDLE_LOCK_MINUTES_MIN,
    AccountRole,
    SchoolConfig,
)
from shared import bakim, crypto

if TYPE_CHECKING:
    from apps.okul.models import Account

logger = logging.getLogger("oab_defteri.okul")

OturumDurumAdi = Literal["kurulum", "kilitli", "acik", "guvenlik_dosyasi_kayip"]

KURULUM: Final = "kurulum"
KILITLI: Final = "kilitli"
ACIK: Final = "acik"
GUVENLIK_DOSYASI_KAYIP: Final = "guvenlik_dosyasi_kayip"

#: Kullanıcı eylemini taşıyan istek başlığı (tasarım §2.3.1); yalnız o boşta sayacını tazeler.
ETKINLIK_BASLIGI: Final = "X-OD-Etkinlik"

KilitSonucu = Literal["kilitlendi", "ertelendi", "zaten_kilitli"]
KILITLENDI: Final = "kilitlendi"
ERTELENDI: Final = "ertelendi"
ZATEN_KILITLI: Final = "zaten_kilitli"

#: Kilidin nedeni (günlük; alt commit c'de `KILIT` iz satırı da taşır).
KilitNedeni = Literal["elle", "bosta", "bekleyen", "kapanis"]

#: Kilitlemenin uçuştaki istekleri en çok bekleyeceği süre (sn; modül başlığı).
UCUSTA_BEKLEME_SN: Final = 30.0

#: Boşta sürenin alt sınırı (sn): geçen süre bunun altındaysa ayar hiç okunmaz.
_ALT_SINIR_SN: Final = IDLE_LOCK_MINUTES_MIN * 60

#: Rol etiketleri: kilit ekranı ve üst çubuk (plan F1b-1 "Oturum"). `yonetici`'nin
#: kısa etiketi; öteki roller `AccountRole` etiketini (sözlük §1) kullanır.
_KISA_ROL_ETIKETLERI: Final[dict[str, str]] = {AccountRole.YONETICI.value: "Program yöneticisi"}
#: Rolü veritabanından okunamayan hesabın etiketi (kilit ekranında seçilemez).
ROL_OKUNAMADI_ETIKETI: Final = "Hesap kaydı okunamadı"


def rol_etiketi(rol: str | None) -> str:
    """Kullanıcıya görünen rol etiketi; `yonetici` için kısa "Program yöneticisi".

    Rol kodu kullanıcı metnine çıkmaz (sözlük §2): bilinmeyen kod "Hesap kaydı
    okunamadı" olur.
    """
    if rol is None:
        return ROL_OKUNAMADI_ETIKETI
    kisa = _KISA_ROL_ETIKETLERI.get(rol)
    if kisa is not None:
        return kisa
    try:
        return str(AccountRole(rol).label)
    except ValueError:
        return ROL_OKUNAMADI_ETIKETI


@dataclass(frozen=True)
class OturumHesabi:
    """Oturumdaki hesabın kişisiz özeti: kimlik, tanıtıcı, rol (ad-soyad TAŞIMAZ)."""

    id: str
    tanitici: str
    rol: str

    @classmethod
    def hesaptan(cls, hesap: Account) -> OturumHesabi:
        return cls(id=str(hesap.id), tanitici=hesap.login_name, rol=str(hesap.role))

    def ozet(self) -> dict[str, str]:
        """`security/session/` yanıtındaki `hesap` nesnesi."""
        return {
            "id": self.id,
            "tanitici": self.tanitici,
            "rol": self.rol,
            "rol_etiketi": rol_etiketi(self.rol),
        }


# ---------------------------------------------------------------------------
# Yazar bağlamı (TK16; modül başlığı)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Yazar:
    """Bir yazmanın yazarı: oturumdaki hesap + rol ya da `SISTEM` (hesap yok)."""

    hesap_id: str | None
    rol: str | None

    @property
    def sistem_mi(self) -> bool:
        return self.hesap_id is None

    @classmethod
    def hesaptan(cls, hesap: OturumHesabi) -> Yazar:
        return cls(hesap_id=hesap.id, rol=hesap.rol)


#: Kullanıcı eylemi olmayan işlerin yazarı (gün işleri, sistem olayları).
SISTEM: Final = Yazar(hesap_id=None, rol=None)

_yazar: ContextVar[Yazar | None] = ContextVar("od_yazar", default=None)


def yazar() -> Yazar | None:
    """Bu isteğin ya da işin yazarı; bağlam kurulmamışsa None (yazma reddedilir, alt commit c)."""
    return _yazar.get()


@contextmanager
def yazar_olarak(kim: Yazar | None) -> Iterator[None]:
    """Bağlam süresince yazarı `kim` yapar; çıkışta önceki bağlam geri gelir."""
    jeton = _yazar.set(kim)
    try:
        yield
    finally:
        _yazar.reset(jeton)


def sistem_olarak() -> AbstractContextManager[None]:
    """Gün işi ve sistem işi yazarı `SISTEM`'i açıkça verir (plan F1b-1 "Denetim izi")."""
    return yazar_olarak(SISTEM)


# ---------------------------------------------------------------------------
# Uçuştaki API istekleri (modül başlığı "UÇUŞTAKİ İSTEKLER")
# ---------------------------------------------------------------------------
#: Bu iş parçacığındaki istek uçuştaki sayaca girdi mi? (kilitleyen kendini beklemesin)
_bu_istek_sayildi: ContextVar[bool] = ContextVar("od_bu_istek_sayildi", default=False)


class UcustakiIstekler:
    """Ara katmandan geçen ve henüz bitmemiş `/api/` isteklerini sayar (iş parçacığı güvenli)."""

    def __init__(self) -> None:
        self._kosul = threading.Condition()
        self._sayi = 0

    @property
    def sayi(self) -> int:
        with self._kosul:
            return self._sayi

    @contextmanager
    def istek(self) -> Iterator[None]:
        """Bir isteği uçuşta sayar; çıkışta sayaç düşer ve bekleyen kilit uyanır."""
        with self._kosul:
            self._sayi += 1
        jeton = _bu_istek_sayildi.set(True)
        try:
            yield
        finally:
            _bu_istek_sayildi.reset(jeton)
            with self._kosul:
                self._sayi -= 1
                self._kosul.notify_all()

    def bosalmasini_bekle(self, *, bekleme_sn: float) -> bool:
        """Uçuştaki istekler (çağıranın kendi isteği hariç) bitene dek bekler; süre dolarsa False."""
        kendisi = 1 if _bu_istek_sayildi.get() else 0
        with self._kosul:
            return self._kosul.wait_for(lambda: self._sayi - kendisi <= 0, timeout=bekleme_sn)


#: Süreç içi tek uçuştaki istek sayacı (ara katman artırır, kilitleme bekler).
UCUSTA: Final = UcustakiIstekler()


# ---------------------------------------------------------------------------
# Ayarlar: boşta süre ve kurulum bilgisi (veritabanı; kilit dışında okunur)
# ---------------------------------------------------------------------------
_ayar_kilidi = threading.Lock()
_bosta_dk_onbellegi: int | None = None


def bosta_suresi_onbellegini_bosalt(*_args: object, **_kwargs: object) -> None:
    """Boşta süre önbelleğini boşaltır (`SchoolConfig` kaydedilince; `post_save` alıcısı)."""
    global _bosta_dk_onbellegi
    with _ayar_kilidi:
        _bosta_dk_onbellegi = None


def bosta_suresi_dk() -> int:
    """Boşta kilit süresi (dakika): `SchoolConfig.idle_lock_minutes` (modül başlığı).

    Satır yoksa alanın kendi varsayılanı (10) — aile iskeletinin 3 dakikasına sessiz
    düşüş yoktur (tasarım §13 D11). Program dışından aralık dışına yazılmış değer
    sınıra çekilir ve günlüğe uyarı düşer. Veritabanı okunamazsa yine alanın
    varsayılanı döner ama önbelleğe ALINMAZ.
    """
    global _bosta_dk_onbellegi
    with _ayar_kilidi:
        if _bosta_dk_onbellegi is not None:
            return _bosta_dk_onbellegi
    try:
        deger = (
            SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK)
            .values_list("idle_lock_minutes", flat=True)
            .first()
        )
    except Exception:  # noqa: BLE001 — veritabanı okunamıyor: alan varsayılanı, önbelleksiz
        logger.warning(
            "Boşta kilit süresi okunamadı; alanın varsayılanı (%d dk) kullanılıyor.",
            IDLE_LOCK_MINUTES_DEFAULT,
        )
        return IDLE_LOCK_MINUTES_DEFAULT
    if deger is None:
        dakika = IDLE_LOCK_MINUTES_DEFAULT
    else:
        dakika = min(max(int(deger), IDLE_LOCK_MINUTES_MIN), IDLE_LOCK_MINUTES_MAX)
        if dakika != deger:
            logger.warning(
                "Boşta kilit süresi aralık dışında (%s); %d dk uygulanıyor.", deger, dakika
            )
    with _ayar_kilidi:
        _bosta_dk_onbellegi = dakika
    return dakika


def kurulum_durumu() -> bool | None:
    """Kurulum sihirbazı tamamlandı mı? (`SchoolConfig.setup_completed`; D15)

    Satır yoksa kurulum sürüyordur (False). Veritabanı okunamazsa None: yanıt
    BİLİNMİYOR. Karar veren fail-closed davranır (süre işler) ama bu yanıtı önbelleğe
    almaz (`OturumDurumu._kurulum_tamam_mi`): tek bir geçici hata kurulum sürerken
    D15'i süreç sonuna dek kapatmasın.
    """
    try:
        return SchoolConfig.objects.filter(
            pk=SchoolConfig.SINGLETON_PK, setup_completed=True
        ).exists()
    except DatabaseError:
        return None


def kurulum_tamamlandi_mi() -> bool:
    """`kurulum_durumu`nun fail-closed hâli: okunamazsa DOĞRU (boşta süre işler)."""
    durum = kurulum_durumu()
    return True if durum is None else durum


def _hesap_kurulu_mu() -> bool:
    # Geç içe aktarım bilinçli: güvenlik çekirdeği oturumu açar (`app_password` →
    # `oturum`); ters yönde modül düzeyinde içe aktarım döngü kurardı.
    from apps.okul.services import app_password

    return app_password.is_password_set()


def _guvenlik_dosyasi_kayip_mi() -> bool:
    from apps.okul.services import app_password

    return app_password.security_file_missing()


# ---------------------------------------------------------------------------
# Saat
# ---------------------------------------------------------------------------
def uykuyu_sayan_monoton_kaynak() -> Callable[[], float]:
    """Uykuyu da sayan monoton kaynak: Linux'ta `CLOCK_BOOTTIME`, yoksa `time.monotonic`."""
    boottime: int | None = getattr(time, "CLOCK_BOOTTIME", None)
    if boottime is None:
        return time.monotonic
    try:
        time.clock_gettime(boottime)
    except OSError:  # pragma: no cover — çok eski çekirdek
        return time.monotonic
    return lambda: time.clock_gettime(boottime)


class UykuyuSayanSaat:
    """Süre ölçümü saati: sistem uykusunu da sayar, geri sıçramada süreyi uzatmaz.

    Her çağrıda monoton kaynağın ve duvar saatinin son çağrıdan beri ilerlemesinin
    BÜYÜĞÜ (negatifse 0) birikime eklenir (gerekçe modül başlığında). Değer yalnız
    farklar için anlamlıdır ve hiç azalmaz. İş parçacığı güvenlidir.
    """

    def __init__(
        self,
        *,
        monoton: Callable[[], float] | None = None,
        duvar: Callable[[], float] = time.time,
    ) -> None:
        self._monoton = monoton if monoton is not None else uykuyu_sayan_monoton_kaynak()
        self._duvar = duvar
        self._kilit = threading.Lock()
        self._son_monoton = self._monoton()
        self._son_duvar = self._duvar()
        self._birikim = 0.0

    def __call__(self) -> float:
        with self._kilit:
            monoton = self._monoton()
            duvar = self._duvar()
            adim = max(monoton - self._son_monoton, duvar - self._son_duvar, 0.0)
            self._son_monoton = monoton
            self._son_duvar = duvar
            self._birikim += adim
            return self._birikim


# ---------------------------------------------------------------------------
# Oturum nesnesi
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _Bakis:
    """Açık oturumun kilit altında alınmış anlık görüntüsü (karar kilit dışında verilir)."""

    nesil: int
    gecen_sn: float
    kilit_bekliyor: bool


class OturumDurumu:
    """Süreç içi oturum (tek nesne, `OTURUM`). İş parçacığı güvenlidir (modül başlığı).

    Bağımlılıklar testte taklit edilir; üretimde varsayılanlar kullanılır (saat
    verilmezse yeni bir `UykuyuSayanSaat`; ayarlar ve güvenlik durumu veritabanından
    ve `guvenlik.json`'dan).
    """

    def __init__(
        self,
        *,
        saat: Callable[[], float] | None = None,
        bosta_dk: Callable[[], int] = bosta_suresi_dk,
        kurulum_tamam: Callable[[], bool | None] = kurulum_durumu,
        uzun_is_sayisi: Callable[[], int] | None = None,
        ucusta: UcustakiIstekler | None = None,
        hesap_kurulu: Callable[[], bool] = _hesap_kurulu_mu,
        dosya_kayip: Callable[[], bool] = _guvenlik_dosyasi_kayip_mi,
    ) -> None:
        self._kilit = threading.RLock()
        self._saat: Callable[[], float] = saat if saat is not None else UykuyuSayanSaat()
        self._bosta_dk = bosta_dk
        self._kurulum_tamam = kurulum_tamam
        self._uzun_is_sayisi: Callable[[], int] = (
            uzun_is_sayisi if uzun_is_sayisi is not None else (lambda: bakim.UZUN_ISLER.sayi)
        )
        self._ucusta = ucusta if ucusta is not None else UCUSTA
        self._hesap_kurulu = hesap_kurulu
        self._dosya_kayip = dosya_kayip
        self._hesap: OturumHesabi | None = None
        self._son_etkinlik = 0.0
        self._kilit_bekliyor = False
        self._kilitleniyor = False
        # Her açılış ve kapanışta artar: bekleyen bir kilit, arada açılan oturumu düşürmez.
        self._nesil = 0
        # Kurulumun tamamlandığı BİR KEZ görüldü mü? (D15; modül başlığı)
        self._kurulum_gorulen = False

    # ------------------------------------------------------------ iç yardımcılar
    def _tutarli_kil(self) -> None:
        """DEK oturumun dışından düşürülmüşse oturum da kapanmış sayılır. Kilit tutulur."""
        if self._hesap is not None and not crypto.is_unlocked():
            logger.warning("Veri anahtarı oturum dışında bellekten düştü; oturum kapandı.")
            self._hesap = None
            self._kilit_bekliyor = False
            self._nesil += 1

    def _acik(self) -> bool:
        """Kilit tutulurken: oturum yeni istekler için açık mı?"""
        self._tutarli_kil()
        return self._hesap is not None and not self._kilitleniyor

    def _bakis(self) -> _Bakis | None:
        with self._kilit:
            if not self._acik():
                return None
            return _Bakis(
                nesil=self._nesil,
                gecen_sn=self._saat() - self._son_etkinlik,
                kilit_bekliyor=self._kilit_bekliyor,
            )

    def _bosta_sn(self) -> int:
        return self._bosta_dk() * 60

    def _suresi_doldu(self, gecen_sn: float) -> bool:
        """Boşta süre doldu mu? Alt sınırın altında ayar hiç okunmaz (sıcak yol)."""
        return gecen_sn >= _ALT_SINIR_SN and gecen_sn >= self._bosta_sn()

    def _kurulum_tamam_mi(self) -> bool:
        """Kurulum tamamlandı mı? DOĞRU yanıt görülünce bir daha SORULMAZ (kilit dışında).

        Yalnız gerçekten okunmuş DOĞRU önbelleğe girer. Okunamayan yanıt (None) o anki
        karar için DOĞRU sayılır (fail-closed) ama önbelleğe ALINMAZ: bir sonraki
        sorgu veritabanına yeniden gider (modül başlığı, D15).
        """
        with self._kilit:
            if self._kurulum_gorulen:
                return True
        tamam = self._kurulum_tamam()
        if tamam is None:
            return True
        if tamam:
            with self._kilit:
                self._kurulum_gorulen = True
        return tamam

    def _kapat_kilitli(self) -> None:
        """Kilit tutulurken: DEK ve İA düşer, oturum kapanır."""
        crypto.unload_key()
        self._hesap = None
        self._kilit_bekliyor = False
        self._kilitleniyor = False
        self._nesil += 1

    # ------------------------------------------------------------ sorgular (yan etkisiz)
    def acik_mi(self) -> bool:
        """Oturum açık mı? (ara katmanın sıcak yolu; tembel kilidi UYGULAMAZ)"""
        with self._kilit:
            return self._acik()

    def hesap(self) -> OturumHesabi | None:
        """Oturumdaki hesap; oturum yoksa (ya da kilitleniyorsa) None."""
        with self._kilit:
            return self._hesap if self._acik() else None

    def hesap_id(self) -> str | None:
        hesap = self.hesap()
        return hesap.id if hesap is not None else None

    def kilit_bekliyor(self) -> bool:
        """Uzun iş yüzünden ertelenmiş bir kilit var mı?"""
        with self._kilit:
            return self._acik() and self._kilit_bekliyor

    # ------------------------------------------------------------ tam durum
    def durum(self) -> OturumDurumAdi:
        """Tam durum (kurulum ve kayıp dahil). Önce tembel kilidi uygular."""
        self.degerlendir()
        return self._durum_hesapla()

    def _durum_hesapla(self) -> OturumDurumAdi:
        if not self._hesap_kurulu():
            return KURULUM
        if self._dosya_kayip():
            return GUVENLIK_DOSYASI_KAYIP
        return ACIK if self.acik_mi() else KILITLI

    def ozet(self) -> dict[str, Any]:
        """`GET security/session/` yanıtı (kişi adı içermez).

        `bosta_kalan_sn` yalnız açık oturumda, kilit beklemiyorken ve kurulum
        tamamlanmışken doludur (kurulumda süre işlemez; D15). Arayüzdeki geri sayım
        yalnız görseldir. `kurulum_tamam` kurulumun bittiği bir kez görülünce
        veritabanına bir daha sorulmaz.
        """
        durum = self.durum()
        bosta_dk = self._bosta_dk()
        kurulum_tamam = self._kurulum_tamam_mi()
        bakis = self._bakis() if durum == ACIK else None
        hesap = self.hesap() if bakis is not None else None
        kalan: int | None = None
        if bakis is not None and not bakis.kilit_bekliyor and kurulum_tamam:
            kalan = _kalan_sn(bosta_dk * 60 - bakis.gecen_sn)
        return {
            "durum": durum,
            "hesap": hesap.ozet() if hesap is not None else None,
            "bosta_dk": bosta_dk,
            "bosta_kalan_sn": kalan,
            "kilit_bekliyor": bool(bakis is not None and bakis.kilit_bekliyor),
            "kurulum_tamam": kurulum_tamam,
        }

    # ------------------------------------------------------------ açılış ve kapanış
    def ac(self, hesap: OturumHesabi, *, veri_anahtari: bytes, iz_anahtari: bytes) -> None:
        """Oturumu bu hesapla açar; DEK ve İA belleğe hesapla AYNI kilit altında alınır.

        Yalnız güvenlik çekirdeğinin açılış yolları çağırır (modül başlığı). Bütün
        denetimler (sarmal, parmak izi, mühür, durum, iz anahtarı) çağırandadır.
        Boşta sayacı sıfırdan başlar; bekleyen kilit kalkar (taze parola kanıtı).
        """
        with self._kilit:
            crypto.load_key(veri_anahtari, audit_key=iz_anahtari)
            self._hesap = hesap
            self._son_etkinlik = self._saat()
            self._kilit_bekliyor = False
            self._kilitleniyor = False
            self._nesil += 1

    def kapat(self) -> None:
        """Oturumu HEMEN kapatır, DEK ve İA düşer (beklemesiz, ertelemesiz).

        Servis içi yollar içindir: geri yükleme sonrası (DEK artık bu veritabanına ait
        değildir), güvenlik dosyasının sıfırlanması, testler. Kullanıcının Kilitle'si
        ve boşta kilit `kilitle`'dir.
        """
        with self._kilit:
            self._kapat_kilitli()

    def kilitle(
        self,
        *,
        neden: KilitNedeni = "elle",
        ertelenebilir: bool = True,
        bekleme_sn: float = UCUSTA_BEKLEME_SN,
    ) -> KilitSonucu:
        """Oturumu kilitler: uçuştaki istekleri bekler, sonra DEK ve İA düşer.

        Uzun iş sürerken (ve `ertelenebilir` iken) kilit ertelenir: `kilit_bekliyor`
        işaretlenir, iş bitince ilk istekte uygulanır (`degerlendir`). Oturum yoksa ya
        da başka bir iş parçacığı zaten kilitliyorsa `zaten_kilitli`.
        """
        return self._kilitle(neden=neden, ertelenebilir=ertelenebilir, bekleme_sn=bekleme_sn)

    def _kilitle(
        self,
        *,
        neden: KilitNedeni,
        ertelenebilir: bool,
        bekleme_sn: float,
        nesil: int | None = None,
    ) -> KilitSonucu:
        with self._kilit:
            if not self._acik() or (nesil is not None and nesil != self._nesil):
                return ZATEN_KILITLI
            if ertelenebilir and self._uzun_is_sayisi() > 0:
                if not self._kilit_bekliyor:
                    logger.info(
                        "Uzun iş sürüyor; oturum kilidi iş bitince uygulanacak (%s).", neden
                    )
                self._kilit_bekliyor = True
                return ERTELENDI
            self._kilitleniyor = True
            beklenen_nesil = self._nesil
        bitti = False
        try:
            bitti = self._ucusta.bosalmasini_bekle(bekleme_sn=bekleme_sn)
        finally:
            with self._kilit:
                if self._nesil == beklenen_nesil:
                    self._kapat_kilitli()
        if not bitti:
            logger.warning(
                "Uçuştaki istekler %.0f sn içinde bitmedi; oturum yine de kilitlendi.", bekleme_sn
            )
        logger.info("Oturum kilitlendi (%s).", neden)
        return KILITLENDI

    # ------------------------------------------------------------ istek başı (ara katman)
    def degerlendir(self) -> None:
        """Tembel kilit: bekleyen kilidi ya da dolan boşta süreyi uygular (modül başlığı).

        Ara katman her `/api/` isteğinin başında çağırır. Oturum kilidi yalnız anlık
        görüntü için tutulur; ayar okuma, kurulum sorgusu ve uçuştakileri bekleme kilit
        dışındadır.
        """
        bakis = self._bakis()
        if bakis is None:
            return
        neden: KilitNedeni
        if bakis.kilit_bekliyor:
            neden = "bekleyen"
        elif self._suresi_doldu(bakis.gecen_sn):
            if not self._kurulum_tamam_mi():
                # D15: kurulum sürüyor, süre kilitlemez; sayaç yeniden başlar (veritabanına
                # en erken bir alt sınır süresi sonra yeniden sorulur).
                with self._kilit:
                    if self._acik() and self._nesil == bakis.nesil:
                        self._son_etkinlik = self._saat()
                return
            neden = "bosta"
        else:
            return
        self._kilitle(
            neden=neden, ertelenebilir=True, bekleme_sn=UCUSTA_BEKLEME_SN, nesil=bakis.nesil
        )

    def etkinlik(self) -> None:
        """Kullanıcı eylemi (`X-OD-Etkinlik`): açık oturumun boşta sayacını tazeler.

        Süresi dolmuş ya da kilidi beklenen oturum DİRİLMEZ (§4.4.3). Ara katman bunu
        yalnız kapıdan geçen istekte ve `degerlendir`'den SONRA çağırır.
        """
        bakis = self._bakis()
        if bakis is None or bakis.kilit_bekliyor or self._suresi_doldu(bakis.gecen_sn):
            return
        with self._kilit:
            if self._acik() and self._nesil == bakis.nesil and not self._kilit_bekliyor:
                self._son_etkinlik = self._saat()

    def sureyi_yeniden_baslat(self) -> None:
        """Açık oturumun boşta sayacını sıfırdan başlatır (`setup/complete/` sonrası; D15)."""
        with self._kilit:
            if self._acik():
                self._son_etkinlik = self._saat()

    @contextmanager
    def istek(self) -> Iterator[None]:
        """Ara katman: isteği uçuşta sayar (kilitleme bitmesini bekler)."""
        with self._ucusta.istek():
            yield

    # ------------------------------------------------------------ test desteği
    def _reset_for_tests(
        self,
        *,
        saat: Callable[[], float] | None = None,
        bosta_dk: Callable[[], int] | None = None,
        kurulum_tamam: Callable[[], bool | None] | None = None,
    ) -> None:
        """Yalnız testler için: nesne süreç içi olduğundan durum testler arasında sızar.

        DEK'e DOKUNMAZ (kök `conftest` anahtarı ayrıca yükler ve düşürür); boşta süre
        önbelleği de boşaltılır.
        """
        bosta_suresi_onbellegini_bosalt()
        with self._kilit:
            self._saat = saat if saat is not None else UykuyuSayanSaat()
            self._bosta_dk = bosta_dk if bosta_dk is not None else bosta_suresi_dk
            self._kurulum_tamam = kurulum_tamam if kurulum_tamam is not None else kurulum_durumu
            self._hesap = None
            self._son_etkinlik = 0.0
            self._kilit_bekliyor = False
            self._kilitleniyor = False
            self._nesil += 1
            self._kurulum_gorulen = False


def _kalan_sn(deger: float) -> int:
    # Yuvarlama kayan nokta artığını siler: (t + 600) - t = 600.00000000003 → 601 olmasın.
    return max(0, math.ceil(round(deger, 3)))


#: Süreç içi TEK oturum nesnesi.
OTURUM: Final = OturumDurumu()


def kapanista_kilitle() -> bool:
    """Düzenli kapanışta oturum açıksa kilitler; kilitlediyse True (tasarım §4.2 kapanış sırası).

    Masaüstü kabuğu `od-gunluk` durduktan sonra, yönetim sunucusu durmadan önce
    `masaustu_kanca.kapanista_kilitle` üzerinden çağırır (`OkulConfig.ready` kaydeder).
    Uçuştaki istekleri bekler, uzun işte ERTELENMEZ: süreç zaten bitmektedir. Çapanın
    `iz-durumu.json`'a yazımı alt commit (c)'de bu kilide eklenir.
    """
    return OTURUM.kilitle(neden="kapanis", ertelenebilir=False) == KILITLENDI
