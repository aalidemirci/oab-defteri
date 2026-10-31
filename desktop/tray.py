"""Sistem tepsisi (tasarım §4.1, §4.4 tepsi kip matrisi, §4.5).

**Kip matrisi (F5, §5.10-13).** Tepsi kip durumunu `KipDurumu`'ndan OKUR (T16;
`TrayActions.kip`) ve komutları sütuna göre sunar:

| Komut | Kilitli | Görevli | Yönetici |
|---|---|---|---|
| Pencereyi aç | ✓ | ✓ | ✓ |
| Ağ Kataloğu durumu ve adresi | bilgi | bilgi | ✓ (katalogu tarayıcıda açar) |
| Ağ Kataloğunu aç/kapat | — | — | ✓ |
| Görevli kipine geç | — | — | ✓ |
| Kilitle | — | ✓ | ✓ |
| Çık | ✓ | parola (SPA) | ✓ |

Kurulum, güvenlik dosyası kayıp ve yeniden başlat durumları "kilitli"
sütunundadır. Menü yalnız görünürlüğü belirlemez: komut ÇALIŞTIRILDIĞI anda
kip yeniden okunur ve matrise uymayan komut reddedilir (`komutu_calistir`) —
görevli kipinde ayar değiştiren komut eski bir menüden de çalışmaz. Görevli
kipinde Çık pencereyi öne getirir ve arayüz yönetici parolasını sorar; çıkış
`POST app/quit/` ile olur (§4.2-4). Bu koruma kaza önleyicidir.

**Taşınabilir arşiv (KB-2, 28.09.2026).** Pardus'un taşınabilir arşivinde Ağ
Kataloğu sunulmaz (`desktop/dagitim.py`): durum satırı "Ağ Kataloğu: taşınabilir
sürümde sunulmaz" der, "Ağ Kataloğunu aç" görünmez ve eski bir menüden de
çalışmaz; ayar önceki bir açılıştan açık kalmışsa "Ağ Kataloğunu kapat" kalır.

**Windows — pystray (0.19.5).** `Icon.run_detached()` Win32 ileti döngüsünü
DAEMON OLMAYAN bir iş parçacığında açar (pystray `_win32._run_detached`). Bu
yüzden çıkışta `icon.stop()` ŞARTTIR: çağrılmazsa pencere kapansa da süreç asılı
kalır, mutex'ler bırakılmaz ve kurucu 30 sn bekleyip "tepsiden Çık'ı seçin"
der. Menü geri çağrıları o iş parçacığında koşar.

**Linux.** Tepsi yoktur; Qt kurulumu ve SIGTERM köprüsü `desktop/qt_kurulum.py`'ye
ayrıldı (tasarım §13 D1). Bu modülün tamamı F1a-2'nin söküm adımında kalkar (T6).

Tepsi kurulamazsa program yine çalışır; neden günlüğe yazılır.
"""

from __future__ import annotations

import importlib
import logging
import sys
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Protocol

from desktop.qt_kurulum import load_icon_image
from desktop.window import app_icon_path

logger = logging.getLogger("oab_defteri.tepsi")

MENU_SHOW: Final = "Pencereyi aç"
MENU_QUIT: Final = "Çık"
TRAY_NAME: Final = "oab-defteri"
TRAY_TITLE: Final = "OAB Defteri"


MENU_KATALOG_AC: Final = "Ağ Kataloğunu aç"
MENU_KATALOG_KAPAT: Final = "Ağ Kataloğunu kapat"
MENU_GOREVLI: Final = "Görevli kipine geç"
MENU_KILITLE: Final = "Kilitle"
#: pystray menüsünün yeniden kurulma denetimi aralığı (saniye; aşağıdaki not).
_MENU_YENILEME_SN: Final = 2.0

# Kip matrisinin sütunları (§4.4). `kurulum`, `guvenlik_dosyasi_kayip` ve
# yeniden başlat gerektiren durum KİLİTLİ sütununa düşer: kilit açık değildir.
SUTUN_KILITLI: Final = "kilitli"
SUTUN_GOREVLI: Final = "gorevli"
SUTUN_YONETICI: Final = "yonetici"

# Komut kodları, menü sırasıyla.
KOMUT_PENCERE: Final = "pencere"
KOMUT_KATALOG_DURUM: Final = "katalog_durum"
KOMUT_KATALOG_AC_KAPA: Final = "katalog_ac_kapa"
KOMUT_GOREVLI: Final = "gorevli"
KOMUT_KILITLE: Final = "kilitle"
KOMUT_CIK: Final = "cik"
KOMUT_SIRASI: Final = (
    KOMUT_PENCERE,
    KOMUT_KATALOG_DURUM,
    KOMUT_KATALOG_AC_KAPA,
    KOMUT_GOREVLI,
    KOMUT_KILITLE,
    KOMUT_CIK,
)

#: Tepsi kip matrisi (§4.4, §5.10-13): komut → çalıştığı sütunlar. Ağ Kataloğu
#: durum satırı kilitli ve görevli kipinde YALNIZ bilgidir (tıklanmaz); Çık
#: görevli kipinde pencereyi öne getirip yönetici parolasını SPA'da ister.
KIP_MATRISI: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {
        KOMUT_PENCERE: frozenset({SUTUN_KILITLI, SUTUN_GOREVLI, SUTUN_YONETICI}),
        KOMUT_KATALOG_DURUM: frozenset({SUTUN_KILITLI, SUTUN_GOREVLI, SUTUN_YONETICI}),
        KOMUT_KATALOG_AC_KAPA: frozenset({SUTUN_YONETICI}),
        KOMUT_GOREVLI: frozenset({SUTUN_YONETICI}),
        KOMUT_KILITLE: frozenset({SUTUN_GOREVLI, SUTUN_YONETICI}),
        KOMUT_CIK: frozenset({SUTUN_KILITLI, SUTUN_GOREVLI, SUTUN_YONETICI}),
    }
)


@dataclass(frozen=True)
class TrayActions:
    """Tepsi komutlarının hedefleri.

    `show` ve `quit` F0'dan beri vardır (`WindowController`). Kip matrisinin
    kalanı isteğe bağlıdır; verilmeyen komut menüde görünmez. `kip`, tepsinin
    kip durumunu OKUDUĞU yerdir (`apps.okul.kip.KIP.durum`, T16): ikinci bir
    durum kaynağı yoktur. Komut her çalıştırıldığında kip YENİDEN okunur; menü
    açıkken kip değişmişse eski menüdeki komut yeni kipe göre reddedilir.
    """

    show: Callable[[], None]
    quit: Callable[[], None]
    kip: Callable[[], str] | None = None
    #: Görevli kipinde Çık: pencere öne gelir, SPA yönetici parolasını sorar (§4.2-4).
    quit_gorevli: Callable[[], None] | None = None
    katalog_satiri: Callable[[], str] | None = None
    katalog_acik: Callable[[], bool] | None = None
    #: Aç/kapa komutu "kapat" mı göstersin? Ayar açık ama katalog açılamadıysa da evet
    #: (verilmezse `katalog_acik`); durum satırının tıklanabilirliği `katalog_acik`'tir.
    katalog_kapatilabilir: Callable[[], bool] | None = None
    #: KB-2: Ağ Kataloğu bu dağıtımda sunulur mu? Yanlışsa (Pardus taşınabilir arşivi)
    #: "aç" hiç görünmez ve çalıştırılmaz; "kapat" ayar açıkken kalır. Verilmezse evet.
    katalog_sunulur: Callable[[], bool] | None = None
    katalog_ac: Callable[[], None] | None = None
    katalog_kapat: Callable[[], None] | None = None
    #: Yönetici kipinde durum satırı: katalogu harici tarayıcıda LAN adresiyle açar.
    katalog_goster: Callable[[], None] | None = None
    gorevli_kipine_gec: Callable[[], None] | None = None
    kilitle: Callable[[], None] | None = None


@dataclass(frozen=True)
class MenuOgesi:
    """Bir menü öğesinin o anki hâli (metin, tıklanabilir mi, görünür mü)."""

    kod: str
    metin: str
    etkin: bool
    gorunur: bool


class Tray(Protocol):
    @property
    def available(self) -> bool: ...

    def stop(self) -> None: ...


def kip_sutunu(kip: str | None) -> str:
    """Kip durumu → matris sütunu. Bilinmeyen durum KİLİTLİ sayılır (fail-closed)."""
    if kip == SUTUN_YONETICI:
        return SUTUN_YONETICI
    if kip == SUTUN_GOREVLI:
        return SUTUN_GOREVLI
    return SUTUN_KILITLI


def _guncel_sutun(actions: TrayActions) -> str:
    if actions.kip is None:
        return SUTUN_KILITLI
    try:
        return kip_sutunu(actions.kip())
    except Exception:  # noqa: BLE001 — okunamazsa en dar sütun
        logger.warning("Tepsi kip durumunu okuyamadı.", exc_info=True)
        return SUTUN_KILITLI


def _katalog_acik(actions: TrayActions) -> bool:
    try:
        return bool(actions.katalog_acik()) if actions.katalog_acik is not None else False
    except Exception:  # noqa: BLE001
        return False


def _katalog_kapatilabilir(actions: TrayActions) -> bool:
    if actions.katalog_kapatilabilir is None:
        return _katalog_acik(actions)
    try:
        return bool(actions.katalog_kapatilabilir())
    except Exception:  # noqa: BLE001
        return _katalog_acik(actions)


def _katalog_sunulur(actions: TrayActions) -> bool:
    if actions.katalog_sunulur is None:
        return True
    try:
        return bool(actions.katalog_sunulur())
    except Exception:  # noqa: BLE001 — okunamazsa "aç" sunulmaz (denetçi de reddeder)
        return False


def menu_durumu(actions: TrayActions, *, sutun: str | None = None) -> tuple[MenuOgesi, ...]:
    """Kip matrisine göre menü (§4.4). İlk öğe varsayılan eylemdir (simgeye tıklama)."""
    sutun = sutun or _guncel_sutun(actions)
    izinli = {kod for kod, sutunlar in KIP_MATRISI.items() if sutun in sutunlar}
    acik = _katalog_acik(actions)
    kapatilabilir = _katalog_kapatilabilir(actions)
    satir = ""
    if actions.katalog_satiri is not None:
        try:
            satir = actions.katalog_satiri()
        except Exception:  # noqa: BLE001
            satir = "Ağ Kataloğu"
    return (
        MenuOgesi(KOMUT_PENCERE, MENU_SHOW, True, True),
        MenuOgesi(
            KOMUT_KATALOG_DURUM,
            satir or "Ağ Kataloğu",
            # Kilitli ve görevli kipinde yalnız bilgi (§4.4 "✓ (bilgi)").
            sutun == SUTUN_YONETICI and actions.katalog_goster is not None and acik,
            actions.katalog_satiri is not None and KOMUT_KATALOG_DURUM in izinli,
        ),
        MenuOgesi(
            KOMUT_KATALOG_AC_KAPA,
            MENU_KATALOG_KAPAT if kapatilabilir else MENU_KATALOG_AC,
            True,
            KOMUT_KATALOG_AC_KAPA in izinli
            and actions.katalog_ac is not None
            and actions.katalog_kapat is not None
            # KB-2: taşınabilir arşivde "aç" yoktur; açık kalmış ayar kapatılabilir.
            and (kapatilabilir or _katalog_sunulur(actions)),
        ),
        MenuOgesi(
            KOMUT_GOREVLI,
            MENU_GOREVLI,
            True,
            KOMUT_GOREVLI in izinli and actions.gorevli_kipine_gec is not None,
        ),
        MenuOgesi(
            KOMUT_KILITLE,
            MENU_KILITLE,
            True,
            KOMUT_KILITLE in izinli and actions.kilitle is not None,
        ),
        MenuOgesi(KOMUT_CIK, MENU_QUIT, True, True),
    )


def komutu_calistir(actions: TrayActions, kod: str) -> bool:
    """Komutu, kipi YENİDEN okuyarak çalıştırır; matrise uymayan komut reddedilir (§5.10-13).

    Dönüş: komut çalıştı mı. Görevli kipinde ayar değiştiren komut (Ağ
    Kataloğunu aç/kapa, görevli kipine geç) menüde görünmez; eski bir menüden
    tıklansa da burada REDDEDİLİR.
    """
    sutun = _guncel_sutun(actions)
    if sutun not in KIP_MATRISI.get(kod, frozenset()):
        logger.warning("Tepsi komutu bu kipte yapılamaz; reddedildi: %s", kod)
        return False
    if kod == KOMUT_PENCERE:
        actions.show()
    elif kod == KOMUT_KATALOG_DURUM:
        if sutun != SUTUN_YONETICI or actions.katalog_goster is None:
            return False  # bilgi satırı
        actions.katalog_goster()
    elif kod == KOMUT_KATALOG_AC_KAPA:
        kapat = _katalog_kapatilabilir(actions)
        if not kapat and not _katalog_sunulur(actions):
            logger.warning("Tepsi: Ağ Kataloğu taşınabilir arşivde sunulmaz; aç reddedildi.")
            return False
        hedef = actions.katalog_kapat if kapat else actions.katalog_ac
        if hedef is None:
            return False
        hedef()
    elif kod == KOMUT_GOREVLI:
        if actions.gorevli_kipine_gec is None:
            return False
        actions.gorevli_kipine_gec()
    elif kod == KOMUT_KILITLE:
        if actions.kilitle is None:
            return False
        actions.kilitle()
    elif kod == KOMUT_CIK:
        if sutun == SUTUN_GOREVLI and actions.quit_gorevli is not None:
            actions.quit_gorevli()  # parola SPA'da (§4.2-4)
        else:
            actions.quit()
    else:
        return False
    return True


def menu_entries(actions: TrayActions) -> tuple[tuple[str, Callable[[], None]], ...]:
    """Şu an görünen menü öğeleri ve eylemleri (ilk öğe varsayılan eylemdir)."""
    return tuple(
        (oge.metin, _komut_eylemi(actions, oge.kod)) for oge in menu_durumu(actions) if oge.gorunur
    )


def _komut_eylemi(actions: TrayActions, kod: str) -> Callable[[], None]:
    def calistir() -> None:
        komutu_calistir(actions, kod)

    return calistir


def _guarded(text: str, action: Callable[[], None]) -> Callable[..., None]:
    """Geri çağrıyı sarar: hata tepsi döngüsünü düşürmez, günlüğe yazılır.

    Konumsal argümanı yoktur, fazlasını yutar: pystray eylemin
    `__code__.co_argcount`'una bakıp (0) argümansız çağırır; Qt'nin
    `triggered(bool)` sinyali `checked` değerini verir, o da yutulur.
    """

    def run(*_signal_args: object) -> None:
        try:
            action()
        except Exception:  # noqa: BLE001 — tepsi döngüsü ayakta kalmalı
            logger.exception("Tepsi komutu başarısız: %s", text)

    return run


class NullTray:
    """Tepsi yok (desteklenmeyen platform)."""

    available = False

    def stop(self) -> None:
        return None


def _dinamik_mi(actions: TrayActions) -> bool:
    """Menü kipe ya da katalog durumuna göre değişiyor mu? (F0 menüsü değişmez.)"""
    return actions.kip is not None or actions.katalog_satiri is not None


class PystrayTray:
    """Windows tepsisi (pystray, daemon olmayan iş parçacığı).

    **Menü yenileme.** pystray 0.19.5'in Win32 arka ucu menüyü bir kez kurar ve
    sağ tıkta hazır tutamağı gösterir (`_on_notify` → `TrackPopupMenuEx`); öğe
    metni ve görünürlüğü ancak `icon.update_menu()` çağrılınca yeniden
    değerlendirilir (kaynaktan doğrulandı). Kip ve katalog durumu tepsinin
    dışında değiştiği için `od-tepsi` iş parçacığı menünün anlık görüntüsünü
    iki saniyede bir hesaplar ve yalnız DEĞİŞTİYSE menüyü yeniden kurar.
    Komutlar yine de kipi çalıştırıldıkları anda yeniden okur
    (`komutu_calistir`): eski bir menüden gelen tıklama yetki vermez.
    """

    def __init__(
        self,
        actions: TrayActions,
        *,
        icon_path: Path | None = None,
        pystray_module: Any | None = None,
        yenileme_sn: float = _MENU_YENILEME_SN,
    ) -> None:
        self._actions = actions
        self._icon_path = icon_path
        self._module = pystray_module
        self._icon: Any | None = None
        self._yenileme_sn = yenileme_sn
        self._anlik: dict[str, MenuOgesi] = {}
        self._dur = threading.Event()
        self._yenileyici: threading.Thread | None = None

    @property
    def available(self) -> bool:
        return self._icon is not None

    def _anligi_hesapla(self) -> tuple[MenuOgesi, ...]:
        ogeler = menu_durumu(self._actions)
        self._anlik = {oge.kod: oge for oge in ogeler}
        return ogeler

    def _oge(self, kod: str) -> MenuOgesi:
        oge = self._anlik.get(kod)
        return oge if oge is not None else MenuOgesi(kod, kod, False, False)

    def start(self) -> bool:
        try:
            pystray = self._module or importlib.import_module("pystray")
            self._anligi_hesapla()
            items = [
                pystray.MenuItem(
                    lambda _item, kod=kod: self._oge(kod).metin,
                    _guarded(kod, _komut_eylemi(self._actions, kod)),
                    default=kod == KOMUT_PENCERE,
                    enabled=lambda _item, kod=kod: self._oge(kod).etkin,
                    visible=lambda _item, kod=kod: self._oge(kod).gorunur,
                )
                for kod in KOMUT_SIRASI
            ]
            icon = pystray.Icon(
                TRAY_NAME, load_icon_image(self._icon_path), TRAY_TITLE, pystray.Menu(*items)
            )
            icon.run_detached()
        except Exception:  # noqa: BLE001 — tepsisiz de çalışılır
            logger.warning("Sistem tepsisi başlatılamadı; program tepsisiz sürüyor.", exc_info=True)
            return False
        self._icon = icon
        if _dinamik_mi(self._actions):
            self._dur.clear()
            self._yenileyici = threading.Thread(
                target=self._yenile_dongusu, name="od-tepsi", daemon=True
            )
            self._yenileyici.start()
        logger.info("Sistem tepsisi hazır.")
        return True

    def yenile(self) -> bool:
        """Anlık görüntü değiştiyse menüyü yeniden kurar; kurduysa `True`."""
        icon = self._icon
        if icon is None:
            return False
        onceki = tuple(self._anlik.values())
        if self._anligi_hesapla() == onceki:
            return False
        try:
            icon.update_menu()
        except Exception:  # noqa: BLE001 — menü eski hâliyle kalır
            logger.warning("Tepsi menüsü yenilenemedi.", exc_info=True)
            return False
        return True

    def _yenile_dongusu(self) -> None:
        while not self._dur.wait(self._yenileme_sn):
            try:
                self.yenile()
            except Exception:  # noqa: BLE001 — iş parçacığı sessizce ölmesin
                logger.warning("Tepsi menüsü yenilenirken hata.", exc_info=True)

    def stop(self) -> None:
        """`icon.stop()` — tepsi iş parçacığını bitirir (çağrılmazsa süreç asılı kalır)."""
        self._dur.set()
        yenileyici, self._yenileyici = self._yenileyici, None
        if yenileyici is not None and yenileyici is not threading.current_thread():
            yenileyici.join(timeout=2.0)
        icon, self._icon = self._icon, None
        if icon is None:
            return
        try:
            icon.stop()
        except Exception:  # noqa: BLE001 — çıkış sürmeli
            logger.warning("Sistem tepsisi kapatılamadı.", exc_info=True)


def start_tray(
    actions: TrayActions,
    *,
    platform: str = sys.platform,
    icon_path: Path | None = None,
) -> Tray:
    """Platforma uygun tepsiyi kurar. Nesne her durumda döner; `available` sonucu söyler.

    Windows'ta `stop()` ŞART (pystray iş parçacığı daemon değildir).
    """
    path = icon_path if icon_path is not None else app_icon_path()
    if platform != "win32":
        # Linux'ta Qt kurulumu ve SIGTERM köprüsü `desktop/qt_kurulum.py`'dedir.
        logger.info("Bu platformda sistem tepsisi yok (%s).", platform)
        return NullTray()
    tray = PystrayTray(actions, icon_path=path)
    tray.start()
    return tray
