"""Oturum — süreç içi TEK oturum nesnesi (tasarım §4.1, §4.4.3, TK14; plan F1b-1 "Oturum").

Aile iskeletinin kip katmanının (görevli kipi / yönetici kipi) yerini alır; "kip"
kavramı bilinçli olarak kalkar (tasarım §12.B). Programda aynı anda en çok BİR
oturum vardır: kilidi açan hesap (kimlik, tanıtıcı, rol). Kullanıcı değiştirmek =
Kilitle + başka hesapla açmak (TK14). Kilit kapısı (`lock_middleware`), rol kapısı
(`rol_middleware`; yazar bağlamı üzerinden), denetim izi yazıcısı (`denetim_izi`) ve uzun iş
sayacı aynı nesneyi okur (`OTURUM`); ikinci bir durum kaynağı açılmaz.

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
verir (`apps.okul.denetim_izi`). Yazar istek başında alınır (bağlam değişkeni; ara katman
`yazar_olarak` ile kurar) ve istek boyunca değişmez: istek sürerken oturum kilitlense
de o isteğin yazarı açılıştaki hesaptır. Kullanıcı eylemi olmayan iş (gün işleri,
`od-gunluk`) `sistem_olarak()` ile `SISTEM`'i açıkça verir. Bağlam yoksa `yazar()`
None döner; yazar bağlamı olmayan yazmayı denetim izi yazıcısı reddeder.

KİLİDİN İZİ (tasarım §4.6.2; plan F1b-1 alt commit c). Her kilitlenme `KILIT` satırı
yazar: elle Kilitle oturumdaki hesabın, boşta kilit `SISTEM`'in (kullanıcı eylemi yoktur);
uzun iş yüzünden ertelenip sonra uygulanan kilit ilk nedenin yazarını taşır (elle
istendiyse hesap). Düzenli kapanışın kilidi, kapanışı bu oturumun içinden arayüzdeki Çık
istediyse (`POST app/quit/`; `cikisi_hesap_istedi`) hesabın, öteki kaynaklarda `SISTEM`'in
satırıdır. Kaynağı backend yalnız Çık'ta bilir: pencerenin çarpısı (pywebview `closing`
olayı), kurucunun `OABDefteri.Kapat` olayı, tek kopya kanalının `kapat` komutu ve SIGTERM
masaüstünde aynı `request_quit` yoluna iner; `closing` olayı nedenini taşımaz (Windows'ta
oturum kapanışı ve görev yöneticisi de pencereyi aynı olayla kapatır), çarpıyı kullanıcının
eylemi diye ayırmanın güvenilir yolu yoktur. Bu yüzden çarpının kilidi `SISTEM`'dir.

Satır uçuştaki istekler bittikten sonra, DEK ve İA DÜŞMEDEN ÖNCE, açık anahtarla ve oturum
kilidinin DIŞINDA (SQLite yazımı) yazılır. Yazılamazsa (veritabanı yazılamıyor) kilit yine
uygulanır ve olay günlüğe düşer: kilit bir güvenlik eylemidir, iz satırının yazılamaması
onu durdurmaz (fail-closed). Satır yalnız kilit gerçekten uygulanacaksa yazılır:
uçuştakiler beklenirken kilit ekranından yeniden giriş yapılırsa (nesil değişti) eski
oturumun kilidi düşer, satır da çapa da yazılmaz (hesap değiştirmenin olağan yolu da eski
hesaba `KILIT` yazmaz). Servis içi hemen kapatma (`kapat`: geri yükleme sonrası, güvenlik
dosyasının sıfırlanması) satır yazmaz: veritabanı artık o oturumun değildir; bekleyen kilit
bunu yeniden girişten ayırır (oturum açık değil) ve `zaten_kilitli` döner. Kilit ekranından
yapılıp DÜŞEN bir giriş, kendisinden önce süren oturuma (açık ya da kilitlenmekte) dokunmaz
(`app_password._start_session`): bekleyen kilidin satırı ve çapası yazılır.

DÜZENLİ KAPANIŞ (`kapanis_kilidi`; tasarım §4.2 kapanış sırası). Kapanış önce işaret koyar
(`kapaniyor_mu`; tek yönlü): `IZ_KIP_KILIDI`'ne bu işaretten sonra giren kilit açılışı
reddedilir. Sonra oturum açıksa kilitler; başka bir iş parçacığının kilidi sürüyorsa onun
bitmesini, oturum kapalıysa uçuştaki istekleri (süren bir kilit açılışı ya da kurulumun ilk
hesabı da uçuştaki bir istektir) bekler ve bu arada açılan oturumu da kilitler. Yalnız aynı
turda önce uçuşta istek kalmadığını, SONRA oturumun kapalı olduğunu görünce döner (ters sırada
iki okuma arasında açılıp biten bir açılış gözden kaçardı). Bekleme `UCUSTA_BEKLEME_SN` ile
sınırlıdır; süre dolduğunda açık olan oturum (uzun bir isteğin yanında biten kilit açılışının
oturumu da) beklemeden kilitlenir. Böylece masaüstü yönetim sunucusunu durdurduğunda
(`desktop/main.py` `serve`) bu oturumun `KILIT` satırı ve çapası yazılmıştır; süren bir kilit
ya da açılış kapanışın arkasında kalıp süreçle birlikte ölmez.

ÇAPA (tasarım §4.6.3; plan F1b-1 "Denetim izi"). `KILIT` satırından hemen sonra, yine
anahtarlar düşmeden, zincir başı `iz-durumu.json`'a çapa olarak yazılır ve kilitli kip
tohumu sıfırlanır (`apps.okul.iz_durumu.capa_yaz`); düzenli kapanışın kilidi de aynı yoldan
geçer. Çapa yazılamazsa kilit yine uygulanır (olay günlüğe düşer) ve ESKİ çapa silinir: ilk
kilit açılışı "çapa yok" der; silinemezse, çapadan sonra kalan bu `KILIT` satırını görüp
"çapa bayat" der (`iz_durumu.capa_yaz`, `iz_dogrulama`). Eski çapa sessizce geçerli
kalsaydı bu oturumun kuyruğunun silinmesi görünmezdi. Satır, çapa ve anahtarların düşmesi
`IZ_KIP_KILIDI` altında, tek parça yapılır: aynı anda yazmak isteyen bir sistem olayı (gün
işi, yedek) ya hepsinden önce açık anahtarla ya da hepsinden sonra yeni çapanın tohumuyla
yazılır; arada eski çapanın tohumuyla yazılan satır olmaz. Kilit sırası: (güvenlik dosyası
kilidi, `app_password._start_session`) → `IZ_KIP_KILIDI` → veritabanı → oturum kilidi; ters
yönde alan yol yoktur.

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

#: Kilidin nedeni (günlük; `KILIT` iz satırının yazarını belirler: "elle" hesabındır,
#: "kapanis" yalnız arayüzdeki Çık bu oturumdan istendiyse; modül başlığı "KİLİDİN İZİ").
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

    def ozet(self) -> dict[str, Any]:
        """`security/session/` yanıtındaki `hesap` nesnesi.

        `yetenekler`: rolün yetenek adları (`rol_izinleri.yetenekler`; plan F1b-2). Ön yüz
        süzmesinin tek kaynağıdır: ön yüz matrisi kopyalamaz.
        """
        # Döngüsel içe aktarım olmasın: rol_izinleri yazar bağlamı için bu modülü içe aktarır.
        from apps.okul.rol_izinleri import yetenekler

        return {
            "id": self.id,
            "tanitici": self.tanitici,
            "rol": self.rol,
            "rol_etiketi": rol_etiketi(self.rol),
            "yetenekler": yetenekler(self.rol),
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

#: Kilitlenmenin iz satırını (ve çapayı) yazan işlev: (kilitlenen hesap, yazar). Testte
#: taklit edilir.
KilitIzi = Callable[[OturumHesabi, Yazar], None]

#: Kilitli kip ile oturumun kilitlenmesini sıralayan süreç içi kilit (modül başlığı "ÇAPA").
#: Sahipleri: kilitlenmenin satır + çapa + anahtar düşürme parçası, sistem olayının kip seçimi
#: ve kilitli yazımı (`iz_durumu`), kilit açılışındaki doğrulama ve çapa yenilemesi
#: (`app_password._start_session`). Yeniden girilebilir: kip seçen yazıcı kilitli yazıcıyı
#: aynı kilit altında çağırır.
IZ_KIP_KILIDI: Final = threading.RLock()

_yazar: ContextVar[Yazar | None] = ContextVar("od_yazar", default=None)


def yazar() -> Yazar | None:
    """Bu isteğin ya da işin yazarı; bağlam kurulmamışsa None (denetim izi yazıcısı reddeder)."""
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


def _kilit_izini_yaz(hesap: OturumHesabi, kim: Yazar) -> None:
    """`KILIT` iz satırı ve çapa (modül başlığı "KİLİDİN İZİ", "ÇAPA").

    Satır kendi işleminde, açık anahtarla yazılır; satır yazılamasa da çapa denenir (zincir
    başı ne ise çapa odur). Çapa hata yükseltmez (`iz_durumu.capa_yaz`).
    """
    # Geç içe aktarım: denetim izi yazıcısı ve kilitli kip yazar bağlamını bu modülden alır.
    from apps.okul import denetim_izi, iz_durumu

    try:
        denetim_izi.kilit_olayi(hesap_id=hesap.id, kim=kim)
    finally:
        iz_durumu.capa_yaz()


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
        kilit_izi: KilitIzi = _kilit_izini_yaz,
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
        self._kilit_izi = kilit_izi
        self._hesap: OturumHesabi | None = None
        self._son_etkinlik = 0.0
        self._kilit_bekliyor = False
        # Ertelenen kilidin ilk nedeni ("elle" öncelikli): uygulanınca iz satırının yazarı.
        self._bekleyen_neden: KilitNedeni | None = None
        self._kilitleniyor = False
        # Oturum açıldı, kapandı ya da kilit bitti: bekleyenleri uyandırır (kapanış kilidi
        # süren bir kilidin bitmesini bununla bekler; modül başlığı "DÜZENLİ KAPANIŞ").
        self._degisti = threading.Condition(self._kilit)
        # Düzenli kapanış başladı (tek yönlü): yeni kilit açılışı reddedilir.
        self._kapaniyor = False
        # Her açılış ve kapanışta artar: bekleyen bir kilit, arada açılan oturumu düşürmez.
        self._nesil = 0
        # Arayüzdeki Çık'ı isteyen oturum: (nesil, hesap kimliği); kapanış kilidinin yazarı.
        self._cikis_isteyen: tuple[int, str] | None = None
        # Kurulumun tamamlandığı BİR KEZ görüldü mü? (D15; modül başlığı)
        self._kurulum_gorulen = False

    # ------------------------------------------------------------ iç yardımcılar
    def _tutarli_kil(self) -> None:
        """DEK oturumun dışından düşürülmüşse oturum da kapanmış sayılır. Kilit tutulur."""
        if self._hesap is not None and not crypto.is_unlocked():
            logger.warning("Veri anahtarı oturum dışında bellekten düştü; oturum kapandı.")
            self._hesap = None
            self._kilit_bekliyor = False
            self._bekleyen_neden = None
            self._kilitleniyor = False
            self._nesil += 1
            self._degisti.notify_all()

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
        self._bekleyen_neden = None
        self._kilitleniyor = False
        self._cikis_isteyen = None
        self._nesil += 1
        self._degisti.notify_all()

    # ------------------------------------------------------------ sorgular (yan etkisiz)
    def acik_mi(self) -> bool:
        """Oturum açık mı? (ara katmanın sıcak yolu; tembel kilidi UYGULAMAZ)"""
        with self._kilit:
            return self._acik()

    def suruyor_mu(self) -> bool:
        """Bir oturum sürüyor mu: açık YA DA kilitlenmekte (DEK uçuştakiler bitince düşecek)?

        Kilit açılışı düşerse yalnız kendi açtığı anahtarları düşürür; kendisinden önce süren
        oturumun anahtarlarına ve bekleyen kilidine dokunmaz (`app_password._start_session`).
        """
        with self._kilit:
            self._tutarli_kil()
            return self._hesap is not None

    def kapaniyor_mu(self) -> bool:
        """Düzenli kapanış başladı mı? (modül başlığı "DÜZENLİ KAPANIŞ"; kilit açılışı reddedilir)"""
        with self._kilit:
            return self._kapaniyor

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

    def cikisi_hesap_istedi(self, kim: Yazar | None) -> bool:
        """Arayüzdeki Çık bu oturumun hesabınca istendi (`POST app/quit/`; modül başlığı).

        Kapanış kilidinin `KILIT` satırı o zaman hesabın olur. Yalnız açık oturumda ve yazar
        oturumdaki hesapsa kaydedilir (kaydedildiyse True); kayıt oturuma (nesle) bağlıdır:
        arada kilitlenip yeniden açılan oturumun kapanışı `SISTEM`'in kalır.
        """
        with self._kilit:
            if not self._acik() or self._hesap is None or kim is None or kim.sistem_mi:
                return False
            if kim.hesap_id != self._hesap.id:
                return False
            self._cikis_isteyen = (self._nesil, self._hesap.id)
            return True

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
            self._bekleyen_neden = None
            self._kilitleniyor = False
            self._nesil += 1
            self._degisti.notify_all()

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
        """Oturumu kilitler: uçuştaki istekleri bekler, `KILIT` satırı yazılır, DEK ve İA düşer.

        Uzun iş sürerken (ve `ertelenebilir` iken) kilit ertelenir: `kilit_bekliyor`
        işaretlenir, iş bitince ilk istekte uygulanır (`degerlendir`). Oturum yoksa, başka
        bir iş parçacığı zaten kilitliyorsa ya da beklerken oturum servis içinden
        kapatıldıysa `zaten_kilitli`. İz satırının yazarı nedenden çıkar (modül başlığı
        "KİLİDİN İZİ").
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
        return self._kilitle_ayrintili(
            neden=neden, ertelenebilir=ertelenebilir, bekleme_sn=bekleme_sn, nesil=nesil
        )[0]

    def _kilitle_ayrintili(
        self,
        *,
        neden: KilitNedeni,
        ertelenebilir: bool,
        bekleme_sn: float,
        nesil: int | None = None,
    ) -> tuple[KilitSonucu, bool]:
        """`_kilitle`; ikinci değer kilidi BU çağrının uygulayıp uygulamadığıdır (satır + çapa)."""
        with self._kilit:
            if not self._acik() or (nesil is not None and nesil != self._nesil):
                return ZATEN_KILITLI, False
            if ertelenebilir and self._uzun_is_sayisi() > 0:
                if not self._kilit_bekliyor:
                    logger.info(
                        "Uzun iş sürüyor; oturum kilidi iş bitince uygulanacak (%s).", neden
                    )
                self._kilit_bekliyor = True
                if neden == "elle" or self._bekleyen_neden is None:
                    self._bekleyen_neden = neden
                return ERTELENDI, False
            etkin_neden: KilitNedeni = (
                self._bekleyen_neden
                if neden == "bekleyen" and self._bekleyen_neden is not None
                else neden
            )
            hesap = self._hesap
            self._kilitleniyor = True
            beklenen_nesil = self._nesil
        bitti = uygulanacak = kapatildi = False
        try:
            bitti = self._ucusta.bosalmasini_bekle(bekleme_sn=bekleme_sn)
        finally:
            # Satır + çapa + anahtarların düşmesi tek parça (modül başlığı "ÇAPA"). Satır ve
            # çapa YALNIZ kilit uygulanacaksa yazılır: bekleme sürerken kilit ekranından
            # yeniden giriş yapıldıysa (`ac`, nesil değişti) kilit uygulanmaz, açık oturumu
            # kilitlenmiş gösteren bir `KILIT` satırı da yazılmaz. Yeniden giriş
            # `IZ_KIP_KILIDI`'ni tutan `_start_session`'dan geçer: denetim ile kapanış
            # arasında nesil bu yoldan değişemez. Nesil oturum servis içinden kapatıldığı
            # için değiştiyse (`kapat`; açık oturum yok) bu yeniden giriş DEĞİLDİR.
            with IZ_KIP_KILIDI:
                with self._kilit:
                    uygulanacak = self._nesil == beklenen_nesil
                    kapatildi = not uygulanacak and self._hesap is None
                    # Çık'ı isteyen istek uçuştaydı; kayıt beklemeden SONRA okunur.
                    cikis_hesabin = hesap is not None and self._cikis_isteyen == (
                        beklenen_nesil,
                        hesap.id,
                    )
                if uygulanacak and hesap is not None:
                    self._kilidi_ize_yaz(
                        hesap, etkin_neden, cikis_hesabin=etkin_neden == "kapanis" and cikis_hesabin
                    )
                with self._kilit:
                    if self._nesil == beklenen_nesil:
                        self._kapat_kilitli()
        if kapatildi:
            logger.info("Kilit beklerken oturum servis içinden kapatıldı; kilit satırı yazılmadı.")
            return ZATEN_KILITLI, False
        if not uygulanacak:
            logger.info("Kilit beklerken oturum yeniden açıldı; önceki oturumun kilidi düştü.")
            return KILITLENDI, False
        if not bitti:
            logger.warning(
                "Uçuştaki istekler %.0f sn içinde bitmedi; oturum yine de kilitlendi.", bekleme_sn
            )
        logger.info("Oturum kilitlendi (%s).", neden)
        return KILITLENDI, True

    def kapanis_kilidi(self, *, bekleme_sn: float = UCUSTA_BEKLEME_SN) -> bool:
        """Düzenli kapanışın kilidi (modül başlığı "DÜZENLİ KAPANIŞ"); bu çağrı kilitlediyse True.

        İşaret konur; oturum açıksa kilitlenir (ertelenmez). Başka bir iş parçacığının kilidi
        sürüyorsa bitmesi, oturum kapalıyken uçuştaki istekler (süren bir kilit açılışı)
        beklenir; bu arada açılan oturum da kilitlenir. Yalnız AYNI turda hem uçuşta istek
        yok hem oturum kapalı görülünce döner. Toplam bekleme `bekleme_sn` ile sınırlıdır: süre
        dolarsa o ana dek açılmış oturum beklemeden kilitlenir (fail-closed), günlüğe uyarı
        düşer, kapanış sürer.
        """
        bitis = time.monotonic() + bekleme_sn
        with self._kilit:
            self._kapaniyor = True
        kilitledi = False
        while True:
            _, uygulandi = self._kilitle_ayrintili(
                neden="kapanis",
                ertelenebilir=False,
                bekleme_sn=max(bitis - time.monotonic(), 0.0),
            )
            kilitledi = kilitledi or uygulandi
            with self._degisti:
                # Başka bir iş parçacığının kilidi (elle, boşta) sürüyor: satırı ve çapası
                # yazılıp anahtarlar düşene dek (ya da yeniden giriş olana dek) beklenir.
                self._degisti.wait_for(
                    lambda: not self._kilitleniyor, timeout=max(bitis - time.monotonic(), 0.0)
                )
            # ÖNCE uçuştaki istekler, SONRA oturum okunur (ikisi ayrı kilitlerdedir). Uçuşta
            # istek yokken okunan kapalı oturum bir daha açılamaz: işaretten sonra başlayan
            # kilit açılışı reddedilir, önce başlayan uçuşta sayılırdı. Ters sırada iki okuma
            # arasında açılıp biten bir kilit açılışı, açık oturumu kapanışın arkasında bırakırdı.
            bos = self._ucusta.bosalmasini_bekle(bekleme_sn=0.0)
            with self._kilit:
                kapali = not self._acik() and not self._kilitleniyor
            if kapali and bos:
                return kilitledi
            if time.monotonic() >= bitis:
                break
            if kapali:
                # Süren bir açılış ya da başka bir istek: bitince (ya da süre dolunca) oturum
                # yeniden okunur; bu arada açılan oturum bir sonraki turda kilitlenir.
                self._ucusta.bosalmasini_bekle(bekleme_sn=max(bitis - time.monotonic(), 0.0))
        # Süre doldu: o ana dek açılmış oturum (uçuştaki uzun bir isteğin yanında biten kilit
        # açılışı da) beklemeden kilitlenir (fail-closed); kapalıysa bu çağrı bir şey yapmaz.
        _, uygulandi = self._kilitle_ayrintili(neden="kapanis", ertelenebilir=False, bekleme_sn=0.0)
        kilitledi = kilitledi or uygulandi
        logger.warning(
            "Kapanışta uçuştaki istekler ya da süren bir kilit %.0f sn içinde bitmedi; program "
            "yine de kapanıyor.",
            bekleme_sn,
        )
        return kilitledi

    def _kilidi_ize_yaz(
        self, hesap: OturumHesabi, neden: KilitNedeni, *, cikis_hesabin: bool = False
    ) -> None:
        """`KILIT` satırı: anahtarlar düşmeden önce, oturum kilidi DIŞINDA (modül başlığı).

        Elle Kilitle ve bu oturumun arayüzden istediği Çık'ın kapanış kilidi (`cikis_hesabin`)
        oturumdaki hesabın, öteki nedenler `SISTEM`'indir. Yazılamazsa kilit yine uygulanır
        (fail-closed); olay günlüğe düşer.
        """
        kim = Yazar.hesaptan(hesap) if neden == "elle" or cikis_hesabin else SISTEM
        try:
            self._kilit_izi(hesap, kim)
        except Exception:  # noqa: BLE001 — kilit güvenlik eylemidir, iz yazılamasa da uygulanır
            logger.warning(
                "Kilit denetim izine yazılamadı; oturum yine de kilitlendi (%s).",
                neden,
                exc_info=True,
            )

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
        kilit_izi: KilitIzi | None = None,
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
            self._kilit_izi = kilit_izi if kilit_izi is not None else _kilit_izini_yaz
            self._hesap = None
            self._son_etkinlik = 0.0
            self._kilit_bekliyor = False
            self._bekleyen_neden = None
            self._kilitleniyor = False
            self._kapaniyor = False
            self._cikis_isteyen = None
            self._nesil += 1
            self._kurulum_gorulen = False
            self._degisti.notify_all()


def _kalan_sn(deger: float) -> int:
    # Yuvarlama kayan nokta artığını siler: (t + 600) - t = 600.00000000003 → 601 olmasın.
    return max(0, math.ceil(round(deger, 3)))


#: Süreç içi TEK oturum nesnesi.
OTURUM: Final = OturumDurumu()


def kapanista_kilitle() -> bool:
    """Düzenli kapanışta oturum açıksa kilitler; kilitlediyse True (tasarım §4.2 kapanış sırası).

    Masaüstü kabuğu `od-gunluk` durduktan sonra, yönetim sunucusu durmadan önce
    `masaustu_kanca.kapanista_kilitle` üzerinden çağırır (`OkulConfig.ready` kaydeder).
    Uçuştaki istekleri bekler, uzun işte ERTELENMEZ: süreç zaten bitmektedir. `KILIT`
    satırı, kapanışı bu oturumdan arayüzdeki Çık istediyse hesabın, değilse (çarpı, kurucu,
    SIGTERM) `SISTEM`'indir (modül başlığı "KİLİDİN İZİ"); ardından çapa `iz-durumu.json`'a
    yazılır (tasarım §4.2 kapanış sırası, §4.6.3: "oturum açıkken düzenli kapanışta").
    Süren bir kilit (başka iş parçacığında) ya da kilit açılışı varsa onun bitmesi beklenir,
    açılan oturum da kilitlenir (`OturumDurumu.kapanis_kilidi`; modül başlığı "DÜZENLİ
    KAPANIŞ"): dönüşte bu oturumun kuyruğu çapalanmıştır. Oturum kapalıysa ve süren bir iş
    yoksa çapa yazılmaz: son kilitlenmenin çapası yerindedir, bu açılışın kilitli satırları
    onun tohumunu ilerletmiştir.
    """
    return OTURUM.kapanis_kilidi()
