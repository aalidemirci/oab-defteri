"""Linux Qt kurulumu ve SIGTERM köprüsü (tasarım §4.1, §4.2 adım 11, §4.5; §13 D1).

Pardus/Linux'ta pencere pywebview'ın Qt arka ucuyla (PySide6 + QtWebEngine)
açılır. Bu modül pencereden ÖNCE, ana iş parçacığında çağrılır (`hazirla`). Aile
iskeletinde bu iş tepsi modülündeydi; OAB'de tepsi yoktur (T6), kurulum buraya
ayrıldı ki tepsiyle birlikte silinmesin.

pywebview 5.3.2'nin Qt arka ucu uygulamayı `QApplication.instance() or
QApplication(sys.argv)` ile alır (`platforms/qt.py`: `setup_app` ve
`create_window`; kaynaktan doğrulandı): burada kurulan örnek aynen kullanılır.
Üç kural:

- **Bağlayıcı PySide6'dır** (LGPLv3; `packaging/requirements-paketleme.txt`
  başlığı). pywebview bağlayıcıya `qtpy` üzerinden ulaşır ve qtpy kurulu ilk
  bağlayıcıyı seçer; seçim `QT_API` ile `load_qt` içinde, ilk `import qtpy`'den
  önce sabitlenir.
- `QtWebEngineWidgets`, `QApplication` kurulmadan ÖNCE içe aktarılmalıdır: bu
  import `Qt::AA_ShareOpenGLContexts` özniteliğini kurar. Sonraya kalırsa Qt
  "Attribute Qt::AA_ShareOpenGLContexts must be set before QCoreApplication is
  created" uyarısı basar ve OpenGL bağlam paylaşımı kurulmaz. `load_qt` sırayı
  uygular.
- `setQuitOnLastWindowClosed(False)`: kapanan bir iletişim kutusu "son pencere
  kapandı" sayılıp programı sonlandırmasın. pywebview son pencere gerçekten
  kapanınca döngüyü kendisi bitirir (`_app.exit()`). Değer ve Pardus davranışı
  F1a'da elle doğrulanır (tasarım §4.5).

Uygulamanın pencere simgesi de burada atanır (`prepare_qt_application`).

**Linux oturum kapanışı.** Oturum kapanırken süreç SIGTERM alır; varsayılan
davranış sessiz ölümdür ve temiz kapanış işareti (T15) yazılmazdı. Qt döngüsü
C++'ta beklerken Python sinyal işleyicisi koşamaz; kısa aralıklı bir `QTimer`
yorumlayıcıya sıra verir ve işaretlenen istek düzenli kapanış yoluna (pencere
denetçisinin `request_quit`'i) çevrilir.

Qt yüklenemezse kurulum günlüğe yazar ve boş bir nesne döner; pencere açılışı
kendi hatasını verir.
"""

from __future__ import annotations

import importlib
import io
import logging
import os
import signal
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from types import FrameType, SimpleNamespace
from typing import TYPE_CHECKING, Any, Final

from desktop.window import app_icon_path

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger("oab_defteri.qt")

#: .deb'in kurduğu hicolor tema ikonu (packaging/linux/build.sh).
THEME_ICON_NAME: Final = "oab-defteri"
_FALLBACK_ICON_COLOR: Final = "#1f4e79"
_FALLBACK_ICON_SIZE: Final = 64
#: SIGTERM'in Qt döngüsünde fark edilme aralığı.
_SIGNAL_POLL_MS: Final = 500
#: Linux Qt bağlayıcısı (LGPLv3). Python paketi ve qtpy'nin `QT_API` değeri.
QT_PACKAGE: Final = "PySide6"
QT_BINDING: Final = "pyside6"

SignalInstaller = Callable[..., Any]


def load_icon_image(icon_path: Path | None) -> Image.Image:
    """Pencere simgesi: uygulama ikonu (.ico'nun en büyük boyutu) ya da düz renk yedek."""
    from PIL import Image

    if icon_path is not None:
        try:
            with Image.open(icon_path) as source:
                return source.convert("RGBA")
        except OSError:
            logger.warning("Uygulama ikonu okunamadı: %s", icon_path, exc_info=True)
    size = (_FALLBACK_ICON_SIZE, _FALLBACK_ICON_SIZE)
    return Image.new("RGBA", size, _FALLBACK_ICON_COLOR)


def load_qt() -> SimpleNamespace:
    """PySide6 sınıfları; `QtWebEngineWidgets` `QApplication`'dan ÖNCE yüklenir (modül belgesi).

    Bağlayıcı seçimi burada sabitlenir: qtpy kararını ilk `import qtpy` anında
    verir ve o an pywebview'ın Qt arka ucu yüklenirken gelir — kurulum ondan önce
    yapıldığı için değişken burada yazılabilir. `setdefault`, dışarıdan verilmiş
    bir seçimi ezmez (sahada teşhis için).
    """
    os.environ.setdefault("QT_API", QT_BINDING)
    importlib.import_module(f"{QT_PACKAGE}.QtWebEngineWidgets")
    qt_core = importlib.import_module(f"{QT_PACKAGE}.QtCore")
    qt_gui = importlib.import_module(f"{QT_PACKAGE}.QtGui")
    qt_widgets = importlib.import_module(f"{QT_PACKAGE}.QtWidgets")
    return SimpleNamespace(
        QApplication=qt_widgets.QApplication,
        QIcon=qt_gui.QIcon,
        QPixmap=qt_gui.QPixmap,
        QTimer=qt_core.QTimer,
    )


def prepare_qt_application(qt: Any, icon_path: Path | None = None) -> Any:
    """pywebview'ın da kullanacağı tek `QApplication` örneği (ana iş parçacığında).

    **Pencere simgesi.** pywebview'a `icon=` verilmez; Qt penceresi simgesini
    `QApplication.windowIcon()`'dan alır. Burada atanmazsa pencerenin simgesi
    boş kalır ve X11'de `_NET_WM_ICON` yazılmaz: simgeyi pencereden okuyan
    masaüstlerinde (XFCE görev listesi, Alt+Tab) genel simge görünür. Tema
    simgesi hicolor 16…256'yı, yani elle çizilmiş 16/24/32'yi de verir. Simge
    atanamazsa program sürer, günlüğe yazılır.
    """
    app = qt.QApplication.instance()
    if app is None:
        # pywebview `platforms/qt.py` içe aktarılırken aynısını yapar (bazı
        # dağıtımlarda geçersiz stil uyarısı); uygulama ondan ÖNCE kurulduğu
        # için değişken burada, kurulumdan önce yazılır.
        os.environ["QT_STYLE_OVERRIDE"] = ""
        app = qt.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    try:
        # QIcon/QPixmap uygulama örneği kurulmadan yaratılamaz: sıra bu.
        app.setWindowIcon(_qt_icon(qt, icon_path))
    except Exception:  # noqa: BLE001 — simgesiz pencere de açılır
        logger.warning("Pencere simgesi atanamadı.", exc_info=True)
    return app


def _qt_icon(qt: Any, icon_path: Path | None) -> Any:
    """Tema ikonu (.deb) → yoksa .ico Pillow ile PNG'ye çevrilir (Qt'nin ico eklentisi gerekmez)."""
    themed = qt.QIcon.fromTheme(THEME_ICON_NAME)
    if not themed.isNull():
        return themed
    buffer = io.BytesIO()
    load_icon_image(icon_path).save(buffer, format="PNG")
    pixmap = qt.QPixmap()
    pixmap.loadFromData(buffer.getvalue(), "PNG")
    return qt.QIcon(pixmap)


class QtKurulumu:
    """Linux Qt kurulumu + SIGTERM → düzenli kapanış köprüsü (ana iş parçacığı).

    `kur()` uygulamayı hazırlar ve köprüyü bağlar; `durdur()` zamanlayıcıyı
    durdurur ve önceki SIGTERM işleyicisini geri koyar. Qt yüklenemezse `kur()`
    `False` döner; nesne yine durdurulabilir.
    """

    def __init__(
        self,
        cikis: Callable[[], None],
        *,
        icon_path: Path | None = None,
        qt_loader: Callable[[], Any] = load_qt,
        signal_installer: SignalInstaller = signal.signal,
    ) -> None:
        self._cikis = cikis
        self._icon_path = icon_path
        self._qt_loader = qt_loader
        self._install_signal = signal_installer
        self._app: Any | None = None
        self._timer: Any | None = None
        self._previous_sigterm: Any | None = None
        self._termination_requested = threading.Event()

    @property
    def hazir(self) -> bool:
        """Qt uygulama örneği kuruldu mu?"""
        return self._app is not None

    def kur(self) -> bool:
        try:
            qt = self._qt_loader()
            app = prepare_qt_application(qt, self._icon_path)
        except Exception:  # noqa: BLE001 — Qt yoksa pencere de açılmaz; hata orada söylenir
            logger.warning("Qt yüklenemedi; pencere açılışı hata verecek.", exc_info=True)
            return False
        self._app = app
        self._watch_termination(qt)
        logger.info("Qt uygulaması hazır.")
        return True

    def _watch_termination(self, qt: Any) -> None:
        try:
            self._previous_sigterm = self._install_signal(signal.SIGTERM, self._on_sigterm)
        except (ValueError, OSError):  # ana iş parçacığı dışında kurulamaz
            logger.warning("SIGTERM işleyicisi kurulamadı.", exc_info=True)
            return
        timer = qt.QTimer()
        timer.timeout.connect(self.poll_termination)
        timer.start(_SIGNAL_POLL_MS)
        self._timer = timer

    def _on_sigterm(self, _signum: int, _frame: FrameType | None) -> None:
        self._termination_requested.set()

    def poll_termination(self) -> None:
        """Qt zamanlayıcısından: SIGTERM geldiyse düzenli kapanışı başlatır."""
        if not self._termination_requested.is_set():
            return
        self._termination_requested.clear()
        logger.info("Oturum kapanıyor (SIGTERM); program düzenli kapanıyor.")
        try:
            self._cikis()
        except Exception:  # noqa: BLE001 — Qt döngüsü ayakta kalmalı
            logger.exception("SIGTERM sonrası düzenli kapanış başlatılamadı.")

    def durdur(self) -> None:
        timer, self._timer = self._timer, None
        if timer is not None:
            timer.stop()
        if self._previous_sigterm is not None:
            try:
                self._install_signal(signal.SIGTERM, self._previous_sigterm)
            except (ValueError, OSError):
                pass
            self._previous_sigterm = None


def hazirla(
    cikis: Callable[[], None],
    *,
    icon_path: Path | None = None,
    qt_loader: Callable[[], Any] = load_qt,
    signal_installer: SignalInstaller = signal.signal,
) -> QtKurulumu:
    """Linux: Qt uygulamasını pencereden ÖNCE kurar ve SIGTERM köprüsünü bağlar.

    Nesne her durumda döner; çıkışta `durdur()` ŞART (önceki SIGTERM işleyicisi
    geri konur).
    """
    kurulum = QtKurulumu(
        cikis,
        icon_path=icon_path if icon_path is not None else app_icon_path(),
        qt_loader=qt_loader,
        signal_installer=signal_installer,
    )
    kurulum.kur()
    return kurulum
