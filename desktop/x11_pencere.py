"""Linux X11: dış süreçte açılan dosya penceresini ana pencereye bağlama (saha bulgusu K-yeni-2).

**Sorun** (Pardus 25.2, XFCE + x11, PR #11'in paketi, 13.11.2026). Kaydetme ve Aç pencereleri dış
süreçte açılır (`desktop/yerel_pencere.py`: zenity, yoksa kdialog). Pencere ana pencereye bağlı
değildi: kullanıcı ana pencereye tıklayınca zenity arkaya düşüyor, ekranda gri "Yer seçiliyor…"
düğmesi kalıyor, görev çubuğunda ayrı "Farklı kaydet" girdisi görünüyordu. zenity 4'te `--attach`
etkisizdir ("DEPRECATED; does nothing"; `src/option.c` yalnız uyarı basar, zenity 4.1.90 kaynağı).

**Çare.** X11 oturumunda dış pencereye `WM_TRANSIENT_FOR` = ana pencerenin X kimliği yazılır (ICCCM
4.1.2.6): pencere yöneticisi onu ana pencerenin üstünde tutar, ana pencereye tıklanınca da arkaya
düşürmez. Kimlik pywebview'ın `BrowserView`'ı gösterilirken Qt'nin ana iş parçacığında bir kez
okunur (`ana_pencereyi_bagla`: `showEvent`, yalnız Qt'nin platformu `xcb` iken; Wayland'da kimlik X
kimliği değildir). Dış süreç başlayınca ayrı bir iş parçacığı (`izle`) kök pencerenin
`_NET_CLIENT_LIST`'inde `_NET_WM_PID`'i sürecin kimliği olan pencereyi kısa aralıklarla (`ARAMA_ARALIGI_SN`)
en çok `ARAMA_SURESI_SN` arar; bulunca bağlar. Süreç biterse arama durur. Pencere açıkken gelen ikinci
dosya penceresi çağrısında ("Açık bir dosya penceresi var" bildirimi) bulunan pencere öne getirilir
(`one_getir`: `_NET_ACTIVE_WINDOW` istemci iletisi, EWMH; kaynak 2 = kullanıcı adına, pencere
yöneticisinin odak çalma korumasına takılmaz; ardından `XRaiseWindow`).

**Portal.** zenity 4 (GTK4) masaüstünde `xdg-desktop-portal` varsa pencereyi kendisi çizmez, portala
(`xdg-desktop-portal-gtk`) çizdirir: pencerenin `_NET_WM_PID`'i portalınkidir, zenity'ninki değildir;
portal üst pencereyi de bilmez ("Unhandled parent window type"). debian:13 kabında xfwm4 + portal ile
ölçüldü (13.11.2026). `desktop/yerel_pencere.py` bu yüzden zenity'yi `GDK_DEBUG=no-portals` ile açar
(N-1'in kök nedeni de budur; o modülün başlığı): pencere zenity'nin kendi penceresidir, burada bulunur.

**Kütüphane** sistemin değil, sürecin zaten yüklediği `libX11.so.6`'dır (`ctypes.CDLL` adıyla): Qt'nin
xcb eklentisi onu yüklemiştir (pakette gömülü kopya; `LD_LIBRARY_PATH` paketin dizinini gösterir).
Tam yolla ikinci bir libX11 yüklemek aynı süreçte iki kütüphaneyi çakıştırırdı. `ctypes.util.find_library`
kullanılmaz: Linux'ta `ldconfig`'i dış süreç olarak çalıştırır (`desktop/dis_surec.py` "Bütün dış süreçler").
Her işlem kendi X bağlantısını açar ve kapatır (Qt'ninkiyle paylaşılmaz); Qt `XInitThreads`'i çağırmıştır.

**Hata pencereyi bozmaz.** Xlib'in varsayılan hata işleyicisi `BadWindow` gibi bir hatada süreci
sonlandırır; pencere bağlanırken kapanmış olabilir. İşlem süresince süreç geneli işleyicinin yerine
hatayı yutan bir işleyici konur (Qt'nin xcb bağlantısının koyduğu da aynısını yapar), `XSync`'ten
sonra eskisi geri konur. X11 değilse (`DISPLAY` yok), kütüphane yüklenemezse, ana pencerenin kimliği
yoksa, arama iş parçacığı başlatılamazsa (kaynak tükenmesi; `izle` hatayı çağırana, yani dosya
penceresinin `communicate`'ine taşırmaz, zenity yetim kalmaz) ya da pencere süre içinde bulunamazsa
hiçbir şey yapılmaz, dosya penceresi eskisi gibi açılır. Günlüğe yalnız olay ve hata türü yazılır;
pencere adı, yol ve kimlik yazılmaz.

**Sınama.** `Xlib` çağrıları kaydeden sahte bir kütüphaneyle birim testinde bağlıdır (bağımsız denetim
14.11.2026): istenen atom türü, pid eşlemesi, her özellik verisinin `XFree`'si, her işlemde ve hata
yolunda `XSync` → eski hata işleyicisi → `XCloseDisplay` sırası, `WM_TRANSIENT_FOR`, istemci
iletilerinin `data[0..4]` değerleri, `XOpenDisplay` NULL dönünce `OSError`.

Gerçek pencerede sınandı (debian:13 zenity 4.1.90 ve debian:12 zenity 3.44, Xvfb + xfwm4 + gerçek Qt
penceresi, 13.11.2026): `xprop` `WM_TRANSIENT_FOR`'u gösterdi, ana pencereye `xdotool` ile
tıklandıktan sonra `_NET_CLIENT_LIST_STACKING`'de zenity ana pencerenin üstünde kaldı.
"""

from __future__ import annotations

import ctypes
import logging
import os
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Final, Protocol

logger = logging.getLogger("oab_defteri.x11")

#: Sürecin yüklediği Xlib (modül başlığı "Kütüphane").
X11_KUTUPHANESI: Final = "libX11.so.6"
#: Dış pencerenin aranma süresi ve aralığı (modül başlığı "Çare"); zenity GTK4 1-2 sn'de açılır.
ARAMA_SURESI_SN: Final = 15.0
ARAMA_ARALIGI_SN: Final = 0.1
#: pywebview sınıflarına konan sarmalayıcıların işareti: ikinci bağlama yeniden sarmaz.
SARMALAYICI_ISARETI: Final = "_od_sarmalayici"
#: Qt'nin X11 platform eklentisinin adı (`QGuiApplication.platformName()`).
QT_X11_PLATFORMU: Final = "xcb"

_XA_CARDINAL: Final = 6
_XA_WINDOW: Final = 33
_CLIENT_MESSAGE: Final = 33
#: `SubstructureRedirectMask | SubstructureNotifyMask` (EWMH istemci iletisinin olay maskesi).
_KOK_OLAY_MASKESI: Final = (1 << 20) | (1 << 19)
#: `_NET_ACTIVE_WINDOW`'un kaynak göstergesi: 2 = kullanıcı adına (pager), EWMH 1.5.
_KAYNAK_KULLANICI: Final = 2
#: `_NET_WM_STATE` iletisinin "ekle" eylemi (EWMH `_NET_WM_STATE_ADD`).
_DURUM_EKLE: Final = 1
_LISTE_EN_COK: Final = 4096


class _XClientMessageEvent(ctypes.Structure):
    _fields_ = [  # noqa: RUF012 — ctypes yapısı
        ("type", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("send_event", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("window", ctypes.c_ulong),
        ("message_type", ctypes.c_ulong),
        ("format", ctypes.c_int),
        ("data", ctypes.c_long * 5),
    ]


class _XEvent(ctypes.Union):
    _fields_ = [("xclient", _XClientMessageEvent), ("dolgu", ctypes.c_long * 24)]  # noqa: RUF012


_HataIsleyicisi = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)


def _hatayi_yut(_ekran: Any, _olay: Any) -> int:
    return 0


#: Modül ömrünce yaşar: Xlib işleyicinin adresini tutar, nesne toplanırsa süreç çökerdi.
_YUTAN_ISLEYICI: Final = _HataIsleyicisi(_hatayi_yut)


class X11Arayuzu(Protocol):
    """Bağlayıcının kullandığı X11 işlemleri (`Xlib`; testlerde sahtesi verilir)."""

    def pencere_bul(self, pid: int) -> int | None: ...

    def gecici_yap(self, pencere: int, ana: int) -> None: ...

    def one_getir(self, pencere: int) -> None: ...


class Xlib:
    """`libX11.so.6` üzerinden üç işlem; her biri kendi bağlantısını açar (modül başlığı)."""

    def __init__(self, kutuphane: Any) -> None:
        self._x = kutuphane
        x = kutuphane
        isaretci = ctypes.c_void_p
        ulong = ctypes.c_ulong
        x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x.XOpenDisplay.restype = isaretci
        x.XCloseDisplay.argtypes = [isaretci]
        x.XDefaultRootWindow.argtypes = [isaretci]
        x.XDefaultRootWindow.restype = ulong
        x.XInternAtom.argtypes = [isaretci, ctypes.c_char_p, ctypes.c_int]
        x.XInternAtom.restype = ulong
        x.XGetWindowProperty.argtypes = [
            isaretci,
            ulong,
            ulong,
            ctypes.c_long,
            ctypes.c_long,
            ctypes.c_int,
            ulong,
            ctypes.POINTER(ulong),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ulong),
            ctypes.POINTER(ulong),
            ctypes.POINTER(isaretci),
        ]
        x.XGetWindowProperty.restype = ctypes.c_int
        x.XFree.argtypes = [isaretci]
        x.XSetTransientForHint.argtypes = [isaretci, ulong, ulong]
        x.XRaiseWindow.argtypes = [isaretci, ulong]
        x.XSendEvent.argtypes = [
            isaretci,
            ulong,
            ctypes.c_int,
            ctypes.c_long,
            ctypes.POINTER(_XEvent),
        ]
        x.XSync.argtypes = [isaretci, ctypes.c_int]
        x.XSetErrorHandler.argtypes = [isaretci]
        x.XSetErrorHandler.restype = isaretci

    @classmethod
    def yukle(cls, *, ortam: Mapping[str, str] | None = None) -> Xlib | None:
        """X11 oturumunda kütüphaneyi yükler; `DISPLAY` yoksa ya da yüklenemezse `None`."""
        if not (os.environ if ortam is None else ortam).get("DISPLAY"):
            return None
        try:
            return cls(ctypes.CDLL(X11_KUTUPHANESI))
        except (OSError, AttributeError) as hata:
            logger.warning("X11 kütüphanesi yüklenemedi (%s).", type(hata).__name__)
            return None

    @contextmanager
    def _baglanti(self) -> Iterator[Any]:
        x = self._x
        ekran = x.XOpenDisplay(None)
        if not ekran:
            raise OSError("X ekranına bağlanılamadı")
        onceki = x.XSetErrorHandler(ctypes.cast(_YUTAN_ISLEYICI, ctypes.c_void_p))
        try:
            yield ekran
        finally:
            x.XSync(ekran, 0)
            x.XSetErrorHandler(onceki)
            x.XCloseDisplay(ekran)

    def _atom(self, ekran: Any, ad: str) -> int:
        return int(self._x.XInternAtom(ekran, ad.encode("ascii"), 0))

    def _ozellik(self, ekran: Any, pencere: int, ad: str, tur: int) -> list[int]:
        """32 bitlik özelliğin değerleri (Xlib onları `long` dizisi olarak verir); yoksa boş liste."""
        gercek_tur = ctypes.c_ulong()
        bicim = ctypes.c_int()
        adet = ctypes.c_ulong()
        kalan = ctypes.c_ulong()
        veri = ctypes.c_void_p()
        sonuc = self._x.XGetWindowProperty(
            ekran,
            pencere,
            self._atom(ekran, ad),
            0,
            _LISTE_EN_COK,
            0,
            tur,
            ctypes.byref(gercek_tur),
            ctypes.byref(bicim),
            ctypes.byref(adet),
            ctypes.byref(kalan),
            ctypes.byref(veri),
        )
        try:
            if sonuc != 0 or not veri.value or bicim.value != 32 or gercek_tur.value != tur:
                return []
            dizi = ctypes.cast(veri, ctypes.POINTER(ctypes.c_ulong))
            return [int(dizi[i]) for i in range(adet.value)]
        finally:
            if veri.value:
                self._x.XFree(veri)

    def pencere_bul(self, pid: int) -> int | None:
        """`_NET_CLIENT_LIST`'te `_NET_WM_PID`'i `pid` olan son pencere; yoksa `None`."""
        with self._baglanti() as ekran:
            kok = int(self._x.XDefaultRootWindow(ekran))
            bulunan: int | None = None
            for pencere in self._ozellik(ekran, kok, "_NET_CLIENT_LIST", _XA_WINDOW):
                if self._ozellik(ekran, pencere, "_NET_WM_PID", _XA_CARDINAL) == [pid]:
                    bulunan = pencere
            return bulunan

    def _kok_iletisi(self, ekran: Any, pencere: int, ileti_adi: str, *veriler: int) -> None:
        """Pencere yöneticisine EWMH istemci iletisi (kök pencereye, `_KOK_OLAY_MASKESI` ile)."""
        olay = _XEvent()
        ileti = olay.xclient
        ileti.type = _CLIENT_MESSAGE
        ileti.send_event = 1
        ileti.window = pencere
        ileti.message_type = self._atom(ekran, ileti_adi)
        ileti.format = 32
        for sira, deger in enumerate(veriler):
            ileti.data[sira] = deger
        kok = int(self._x.XDefaultRootWindow(ekran))
        self._x.XSendEvent(ekran, kok, 0, _KOK_OLAY_MASKESI, ctypes.byref(olay))

    def gecici_yap(self, pencere: int, ana: int) -> None:
        """`WM_TRANSIENT_FOR` yazılır, pencere görev çubuğundan düşürülür (modül başlığı)."""
        with self._baglanti() as ekran:
            self._x.XSetTransientForHint(ekran, pencere, ana)
            self._kok_iletisi(
                ekran,
                pencere,
                "_NET_WM_STATE",
                _DURUM_EKLE,
                self._atom(ekran, "_NET_WM_STATE_SKIP_TASKBAR"),
                0,
                _KAYNAK_KULLANICI,
            )

    def one_getir(self, pencere: int) -> None:
        with self._baglanti() as ekran:
            self._kok_iletisi(ekran, pencere, "_NET_ACTIVE_WINDOW", _KAYNAK_KULLANICI)
            self._x.XRaiseWindow(ekran, pencere)


class DisPencereBaglayici:
    """Dış dosya penceresini ana pencereye bağlar, istenince öne getirir (modül başlığı).

    `x11_yukle` X11 arayüzünü ilk kullanımda bir kez yükler (Windows'ta modül içe aktarılır ama
    hiç çağrılmaz). `bekle` ve `saat` aramanın beklemesi ve saatidir; testler sahtesini verir.
    """

    def __init__(
        self,
        *,
        x11_yukle: Callable[[], X11Arayuzu | None] = Xlib.yukle,
        bekle: Callable[[float], None] = time.sleep,
        saat: Callable[[], float] = time.monotonic,
        arama_sn: float = ARAMA_SURESI_SN,
        aralik_sn: float = ARAMA_ARALIGI_SN,
    ) -> None:
        self._x11_yukle = x11_yukle
        self._x11: X11Arayuzu | None = None
        self._yuklendi = False
        self._bekle = bekle
        self._saat = saat
        self._arama_sn = arama_sn
        self._aralik_sn = aralik_sn
        self._kilit = threading.Lock()
        self._ana: int | None = None
        self._dis: dict[int, int] = {}

    @property
    def ana_pencere_kimligi(self) -> int | None:
        with self._kilit:
            return self._ana

    def ana_pencere(self, kimlik: int | None) -> None:
        """Ana pencerenin X kimliği (Qt'nin ana iş parçacığında okunur; `ana_pencereyi_bagla`)."""
        with self._kilit:
            self._ana = kimlik or None

    def _arayuz(self) -> X11Arayuzu | None:
        with self._kilit:
            if not self._yuklendi:
                self._yuklendi = True
                try:
                    self._x11 = self._x11_yukle()
                except Exception as hata:  # noqa: BLE001 — X11 yoksa pencere eskisi gibi açılır
                    logger.warning("X11 kütüphanesi yüklenemedi (%s).", type(hata).__name__)
            return self._x11

    def izle(self, pid: int, suruyor: Callable[[], bool]) -> threading.Thread | None:
        """Dış sürecin penceresini ayrı iş parçacığında arar ve bağlar; arama yoksa `None` döner."""
        ana = self.ana_pencere_kimligi
        if ana is None:
            return None
        x11 = self._arayuz()
        if x11 is None:
            return None
        is_parcacigi = threading.Thread(
            target=self._ara, args=(x11, pid, ana, suruyor), name="od-x11-bagla", daemon=True
        )
        try:
            is_parcacigi.start()
        except Exception as hata:  # noqa: BLE001 — "can't start new thread": pencere bağımsız açılır
            logger.warning(
                "Dosya penceresi bağlama araması başlatılamadı (%s).", type(hata).__name__
            )
            return None
        return is_parcacigi

    def _ara(self, x11: X11Arayuzu, pid: int, ana: int, suruyor: Callable[[], bool]) -> None:
        son = self._saat() + self._arama_sn
        try:
            while suruyor():
                pencere = x11.pencere_bul(pid)
                if pencere is not None:
                    x11.gecici_yap(pencere, ana)
                    with self._kilit:
                        self._dis[pid] = pencere
                    logger.info("Dosya penceresi ana pencereye bağlandı.")
                    return
                if self._saat() >= son:
                    logger.info("Dosya penceresi süre içinde bulunamadı; bağlanmadı.")
                    return
                self._bekle(self._aralik_sn)
        except Exception as hata:  # noqa: BLE001 — bağlanamasa da pencere açık kalır
            logger.warning("Dosya penceresi ana pencereye bağlanamadı (%s).", type(hata).__name__)

    def birak(self, pid: int) -> None:
        """Süreç bitti: penceresi unutulur."""
        with self._kilit:
            self._dis.pop(pid, None)

    def one_getir(self) -> bool:
        """Açık dış pencereyi öne getirir; bağlanmış pencere yoksa `False` (modül başlığı)."""
        with self._kilit:
            pencereler = list(self._dis.values())
            x11 = self._x11
        if not pencereler or x11 is None:
            return False
        try:
            x11.one_getir(pencereler[-1])
        except Exception as hata:  # noqa: BLE001 — öne getirilemese de bildirim çıkar
            logger.warning("Dosya penceresi öne getirilemedi (%s).", type(hata).__name__)
            return False
        return True


def ana_pencereyi_bagla(arka_uc: Any, baglayici: DisPencereBaglayici) -> None:
    """pywebview Qt kolunun penceresi gösterilirken X kimliğini bağlayıcıya verir (modül başlığı).

    `BrowserView.showEvent` sarılır: Qt'nin ana iş parçacığında koşar, pywebview'ın `shown` olayını
    da o tetikler. Arka uç yüklenince, pencere kurulmadan önce çağrılır (`desktop.window.open_window`).
    Kimlik yalnız Qt'nin platformu `xcb` iken alınır; hata pencereyi durdurmaz.
    """
    pencere_sinifi = arka_uc.BrowserView
    asil = pencere_sinifi.showEvent
    if getattr(asil, SARMALAYICI_ISARETI, False):
        return
    uygulama = arka_uc.QApplication

    def showEvent(pencere: Any, olay: Any) -> Any:  # noqa: N802 — Qt adı
        try:
            if uygulama.platformName() == QT_X11_PLATFORMU:
                baglayici.ana_pencere(int(pencere.winId()))
        except Exception as hata:  # noqa: BLE001 — kimliksiz de pencere açılır
            logger.warning("Ana pencerenin X kimliği okunamadı (%s).", type(hata).__name__)
        return asil(pencere, olay)

    setattr(showEvent, SARMALAYICI_ISARETI, True)
    pencere_sinifi.showEvent = showEvent
