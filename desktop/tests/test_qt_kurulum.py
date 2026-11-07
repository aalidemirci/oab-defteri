"""Linux Qt kurulumu ve SIGTERM köprüsü testleri (tasarım §4.2 adım 11, §4.5; §13 D1).

Testler aile iskeletinin tepsi testlerinden taşındı: Qt kurulum sırası, var olan
uygulama örneği, pencere simgesi, bağlayıcı seçimi ve oturum kapanışında SIGTERM
→ düzenli kapanış köprüsü. PySide6 Docker imajında yoktur; sahte modülle sınanır.
Gerçek davranış (Pardus'ta pencere, çarpı, oturum kapanışı) elle doğrulanır
(packaging/windows/NOTLAR.md).

İndirme işleyicisinin sahtesi gerçek PySide6 6.8.3'ün yüzeyini taşır: `setPath` YOKTUR. Yüzey ve
blob indirmesi gerçek paketlerle (PySide6 6.8.3, pywebview 5.3.2, offscreen) konteynerde bir kez
sınandı; imaja girmez, gerçek Pardus'ta elle denenir.
"""

from __future__ import annotations

import logging
import os
import signal
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from desktop import qt_kurulum
from desktop.qt_kurulum import QtKurulumu, hazirla, load_icon_image
from desktop.window import app_icon_path

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _qt_ortam_degiskenleri_geri_alinir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Qt ortam değişkenleri test sonunda eski hâline döner.

    `prepare_qt_application` `QT_STYLE_OVERRIDE`'ı, `load_qt` ise bağlayıcıyı
    seçen `QT_API`'yi yazar. `QT_API` sıfırlanır (silinir) ki `setdefault`
    davranışı sınanabilsin; monkeypatch teardown'da yazılan değeri kaldırır.
    """
    monkeypatch.setenv("QT_STYLE_OVERRIDE", "test-oncesi")
    monkeypatch.delenv("QT_API", raising=False)


class _Sayac:
    def __init__(self) -> None:
        self.cik = 0

    def __call__(self) -> None:
        self.cik += 1


# ------------------------------------------------------------------- simge


def test_uygulama_ikonu_depoda_bulunur() -> None:
    yol = app_icon_path(root=REPO_ROOT)

    assert yol == REPO_ROOT / "packaging" / "ikonlar" / "oab-defteri.ico"


def test_paketli_programda_ikon_kokte_aranir(tmp_path: Path) -> None:
    (tmp_path / "oab-defteri.ico").write_bytes(b"ico")

    assert app_icon_path(root=tmp_path) == tmp_path / "oab-defteri.ico"
    assert app_icon_path(root=tmp_path / "yok") is None


def test_pencere_simgesi_gercek_ikondan_yuklenir() -> None:
    goruntu = load_icon_image(app_icon_path(root=REPO_ROOT))

    assert goruntu.mode == "RGBA"
    # Pillow `.ico`'nun en büyük karesini açar (ana çizimden 256 px); kesimlerin
    # tutarlılığı packaging/tests/test_ikonlar.py'dedir.
    assert goruntu.size == (256, 256)


def test_ikon_bozuksa_duz_renk_yedek(tmp_path: Path) -> None:
    bozuk = tmp_path / "bozuk.ico"
    bozuk.write_bytes(b"ico degil")

    for kaynak in (bozuk, None):
        goruntu = load_icon_image(kaynak)
        assert goruntu.size == (64, 64)


# ---------------------------------------------------------------- sahte Qt


class _Sinyal:
    def __init__(self) -> None:
        self.baglananlar: list[Callable[..., Any]] = []

    def connect(self, hedef: Callable[..., Any]) -> None:
        self.baglananlar.append(hedef)

    def emit(self, *args: Any) -> None:
        for hedef in self.baglananlar:
            hedef(*args)


class _SahteDosyaPenceresi:
    """`QFileDialog.getSaveFileName`: seçilen yol ve süzgeç döner, iptalde boş metin."""

    def __init__(self, secilen: str) -> None:
        self.secilen = secilen
        self.sorulan: list[tuple[Any, str, str]] = []

    def getSaveFileName(self, ebeveyn: Any, baslik: str, yol: str) -> tuple[str, str]:
        self.sorulan.append((ebeveyn, baslik, yol))
        return self.secilen, ""


class _SahteIndirme:
    """`QWebEngineDownloadRequest`'in PySide6 6.8.3 yüzeyi: `setPath` ve `path` yoktur."""

    def __init__(self, onerilen: str = "Yedek-Raporu_06.11.2026.pdf") -> None:
        self.onerilen = onerilen
        self.cagrilar: list[tuple[str, ...]] = []

    def suggestedFileName(self) -> str:
        return self.onerilen

    def setDownloadDirectory(self, dizin: str) -> None:
        self.cagrilar.append(("dizin", dizin))

    def setDownloadFileName(self, ad: str) -> None:
        self.cagrilar.append(("ad", ad))

    def accept(self) -> None:
        self.cagrilar.append(("kabul",))


class _SahteArkaUc:
    """`webview.platforms.qt`: işleyici `BrowserView` sınıfındadır."""

    class BrowserView:
        localization = {"global.saveFile": "Farklı kaydet"}

        def on_download_requested(self, indirme: Any) -> None:
            indirme.setPath("/uydurma")  # pywebview 5.3.2'nin kırık çağrısı


class _SahteWebview:
    """pywebview paketi: `start`, arka ucu `initialize` ile ve modül düzeyinden alır."""

    def __init__(self) -> None:
        self.arka_uc = _SahteArkaUc()
        self.istenen: list[str] = []
        self.initialize = self._initialize

    def _initialize(self, gui: str) -> Any:
        self.istenen.append(gui)
        return self.arka_uc


class _SahteQt:
    """PySide6'nın kullandığımız yüzeyi; kurulum sırasını kaydeder."""

    def __init__(self, *, uygulama_var: bool = False) -> None:
        self.sira: list[str] = []
        self.zamanlayicilar: list[Any] = []
        #: `QIcon.fromTheme` bu adla çağrılınca dolu simge döner (kurulu hicolor teması).
        self.tema_simgesi: str | None = None
        self.simge_atanamaz = False
        disari = self

        class QApplication:
            _ornek: Any = None

            def __init__(self, argv: list[str]) -> None:
                disari.sira.append("QApplication")
                self.son_pencere_kapaninca_cik = True
                QApplication._ornek = self

            @classmethod
            def instance(cls) -> Any:
                return cls._ornek

            def setQuitOnLastWindowClosed(self, deger: bool) -> None:
                self.son_pencere_kapaninca_cik = deger

            def setWindowIcon(self, simge: Any) -> None:
                if disari.simge_atanamaz:
                    raise RuntimeError("simge atanamadı")
                self.pencere_simgesi = simge

        if uygulama_var:
            QApplication._ornek = QApplication.__new__(QApplication)
            QApplication._ornek.son_pencere_kapaninca_cik = True

        class QIcon:
            def __init__(self, kaynak: Any = None) -> None:
                self.kaynak = kaynak

            @staticmethod
            def fromTheme(ad: str) -> Any:
                return QIcon(f"tema:{ad}" if ad == disari.tema_simgesi else None)

            def isNull(self) -> bool:
                return self.kaynak is None

        class QPixmap:
            def __init__(self) -> None:
                self.veri = b""

            def loadFromData(self, veri: bytes, bicim: str) -> bool:
                self.veri = veri
                return True

        class QTimer:
            def __init__(self) -> None:
                self.timeout = _Sinyal()
                self.aralik: int | None = None
                disari.zamanlayicilar.append(self)

            def start(self, aralik: int) -> None:
                self.aralik = aralik

            def stop(self) -> None:
                self.aralik = None

        self.QApplication, self.QIcon, self.QPixmap, self.QTimer = (
            QApplication,
            QIcon,
            QPixmap,
            QTimer,
        )
        self.QFileDialog = _SahteDosyaPenceresi("")

    def yukleyici(self) -> Any:
        self.sira.append("QtWebEngineWidgets")
        return self


class _SinyalKaydi:
    def __init__(self) -> None:
        self.kurulan: list[tuple[int, Any]] = []

    def __call__(self, signum: int, isleyici: Any) -> Any:
        self.kurulan.append((signum, isleyici))
        return "onceki-isleyici" if len(self.kurulan) == 1 else None


def _kurulum(
    qt: _SahteQt,
    cikis: Callable[[], None],
    sinyal: _SinyalKaydi | None = None,
    webview: Any = None,
) -> Any:
    return hazirla(
        cikis,
        icon_path=app_icon_path(root=REPO_ROOT),
        qt_loader=qt.yukleyici,
        signal_installer=sinyal or _SinyalKaydi(),
        webview_loader=lambda: webview if webview is not None else _SahteWebview(),
    )


# ---------------------------------------------------------------- kurulum


def test_qt_webengine_uygulamadan_once_yuklenir() -> None:
    qt = _SahteQt()

    kurulum = _kurulum(qt, _Sayac())

    assert kurulum.hazir is True
    assert qt.sira == ["QtWebEngineWidgets", "QApplication"]
    uygulama = qt.QApplication.instance()
    assert uygulama.son_pencere_kapaninca_cik is False
    assert os.environ["QT_STYLE_OVERRIDE"] == ""  # pywebview qt.py ile aynı, kurulumdan önce
    kurulum.durdur()


def test_qt_var_olan_uygulama_ornegini_kullanir() -> None:
    """pywebview'ın Qt arka ucu da `QApplication.instance()`'ı kullanır: tek örnek."""
    qt = _SahteQt(uygulama_var=True)
    onceki = qt.QApplication.instance()

    kurulum = _kurulum(qt, _Sayac())

    assert "QApplication" not in qt.sira
    assert os.environ["QT_STYLE_OVERRIDE"] == "test-oncesi"
    assert qt.QApplication.instance() is onceki
    assert onceki.son_pencere_kapaninca_cik is False
    kurulum.durdur()


def test_qt_uygulamasi_pencere_simgesini_tasir() -> None:
    """pywebview'a `icon=` verilmez: pencere simgesi `QApplication.windowIcon()`'dır.

    Atanmazsa X11'de `_NET_WM_ICON` yazılmaz ve XFCE görev listesi genel simge
    gösterir.
    """
    qt = _SahteQt()

    kurulum = _kurulum(qt, _Sayac())

    simge = qt.QApplication.instance().pencere_simgesi
    assert simge.kaynak.veri.startswith(b"\x89PNG")  # tema yok: .ico Pillow ile PNG'ye
    kurulum.durdur()


def test_qt_pencere_simgesi_once_tema_simgesidir() -> None:
    """Kurulu hicolor teması elle çizilmiş 16/24/32'yi de verir; varsa o seçilir."""
    qt = _SahteQt(uygulama_var=True)
    qt.tema_simgesi = "oab-defteri"

    kurulum = _kurulum(qt, _Sayac())

    assert qt.QApplication.instance().pencere_simgesi.kaynak == "tema:oab-defteri"
    kurulum.durdur()


def test_qt_pencere_simgesi_atanamazsa_program_surer(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    qt = _SahteQt()
    qt.simge_atanamaz = True

    kurulum = _kurulum(qt, _Sayac())

    assert kurulum.hazir is True
    assert any("Pencere simgesi atanamadı" in k.getMessage() for k in od_gunlugu)
    kurulum.durdur()


def test_qt_yuklenemezse_kurulum_hazir_degil_ama_durdurulabilir(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    def yok() -> Any:
        raise ImportError("PySide6 yok")

    kurulum = hazirla(_Sayac(), qt_loader=yok, signal_installer=_SinyalKaydi())

    assert kurulum.hazir is False
    assert any("Qt yüklenemedi" in k.getMessage() for k in od_gunlugu)
    kurulum.durdur()


def test_pencere_simgesi_varsayilan_olarak_paket_yolundan_cozulur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alinan: list[Path | None] = []

    def kaydet(self: QtKurulumu) -> bool:
        alinan.append(self._icon_path)
        return True

    monkeypatch.setattr(QtKurulumu, "kur", kaydet)
    monkeypatch.setattr(qt_kurulum, "app_icon_path", lambda: Path("/paket/oab-defteri.ico"))

    hazirla(_Sayac())

    assert alinan == [Path("/paket/oab-defteri.ico")]


# ---------------------------------------------------------- SIGTERM köprüsü


def test_sigterm_duzenli_cikisa_cevrilir() -> None:
    """Linux oturum kapanışı: SIGTERM → Qt zamanlayıcısı → düzenli kapanış (T15 işareti yazılsın)."""
    qt = _SahteQt()
    sayac = _Sayac()
    sinyal = _SinyalKaydi()
    kurulum = _kurulum(qt, sayac, sinyal)

    ((signum, isleyici),) = sinyal.kurulan
    assert signum == signal.SIGTERM
    (zamanlayici,) = qt.zamanlayicilar
    assert zamanlayici.aralik is not None

    zamanlayici.timeout.emit()
    assert sayac.cik == 0  # sinyal yokken bir şey olmaz

    isleyici(signal.SIGTERM, None)
    zamanlayici.timeout.emit()
    zamanlayici.timeout.emit()
    assert sayac.cik == 1  # istek bir kez işlenir

    kurulum.durdur()
    assert sinyal.kurulan[-1] == (signal.SIGTERM, "onceki-isleyici")
    assert zamanlayici.aralik is None


def test_sigterm_kurulamazsa_uygulama_yine_kurulur() -> None:
    def ana_is_parcacigi_degil(signum: int, isleyici: Any) -> Any:
        raise ValueError("signal only works in main thread")

    qt = _SahteQt()

    kurulum = hazirla(_Sayac(), qt_loader=qt.yukleyici, signal_installer=ana_is_parcacigi_degil)

    assert kurulum.hazir is True
    assert qt.zamanlayicilar == []
    kurulum.durdur()


def test_sigterm_sonrasi_cikis_hatasi_qt_dongusunu_dusurmez(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    def patlayan() -> None:
        raise RuntimeError("çıkış başlatılamadı")

    qt = _SahteQt()
    sinyal = _SinyalKaydi()
    kurulum = _kurulum(qt, patlayan, sinyal)
    ((_, isleyici),) = sinyal.kurulan

    isleyici(signal.SIGTERM, None)
    qt.zamanlayicilar[0].timeout.emit()

    assert any("düzenli kapanış başlatılamadı" in k.getMessage() for k in od_gunlugu)
    kurulum.durdur()


# ---------------------------------------------------------------- yükleyici


def _qt_modulu_taklidi(_ad: str) -> SimpleNamespace:
    """`load_qt`'nin okuduğu bütün sınıfları taşıyan boş taklit modül."""
    return SimpleNamespace(
        QApplication=object, QFileDialog=object, QIcon=object, QPixmap=object, QTimer=object
    )


def test_qt_yukleyici_webengine_i_once_ice_aktarir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Qt kuralı: QtWebEngineWidgets, QApplication kurulmadan ÖNCE aktarılmalı."""
    sira: list[str] = []

    def sahte_import(ad: str) -> Any:
        sira.append(ad)
        return _qt_modulu_taklidi(ad)

    monkeypatch.setattr(qt_kurulum, "importlib", SimpleNamespace(import_module=sahte_import))

    qt_kurulum.load_qt()

    assert sira[0] == "PySide6.QtWebEngineWidgets"
    assert sira[1:] == ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"]


def test_qt_yukleyici_baglayiciyi_pyside6_ye_sabitler(monkeypatch: pytest.MonkeyPatch) -> None:
    """qtpy kurulu ilk bağlayıcıyı seçer; seçim `QT_API` ile ilk import'tan önce sabitlenir."""
    monkeypatch.setattr(qt_kurulum, "importlib", SimpleNamespace(import_module=_qt_modulu_taklidi))

    qt_kurulum.load_qt()

    assert os.environ["QT_API"] == "pyside6"


def test_qt_yukleyici_disaridan_verilen_baglayiciyi_ezmez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sahada teşhis için elle verilmiş `QT_API` korunur (`setdefault`)."""
    monkeypatch.setenv("QT_API", "pyqt6")
    monkeypatch.setattr(qt_kurulum, "importlib", SimpleNamespace(import_module=_qt_modulu_taklidi))

    qt_kurulum.load_qt()

    assert os.environ["QT_API"] == "pyqt6"


# ------------------------------------------------- indirme işleyicisi (plan F1b-3)


def _pencere() -> Any:
    return SimpleNamespace(localization={"global.saveFile": "Farklı kaydet"})


def test_indirme_secilen_yere_iner_ve_setpath_cagrilmaz(tmp_path: Path) -> None:
    """Qt6'da `setPath` yoktur: dizin ve ad ayrı verilir, sonra istek kabul edilir."""
    dosya_penceresi = _SahteDosyaPenceresi(str(tmp_path / "secilen.pdf"))
    indirme = _SahteIndirme()

    qt_kurulum.indirme_isleyicisi(dosya_penceresi)(_pencere(), indirme)

    assert indirme.cagrilar == [("dizin", str(tmp_path)), ("ad", "secilen.pdf"), ("kabul",)]


def test_indirme_penceresi_onerilen_adi_ve_turkce_basligi_kullanir() -> None:
    """Blob adresinin yolu ad değildir: ad `suggestedFileName`'dedir."""
    dosya_penceresi = _SahteDosyaPenceresi("")
    pencere = _pencere()

    qt_kurulum.indirme_isleyicisi(dosya_penceresi)(
        pencere, _SahteIndirme("Kurtarma-Anahtarı-Belgesi_06.11.2026.pdf")
    )

    ((ebeveyn, baslik, yol),) = dosya_penceresi.sorulan
    assert ebeveyn is pencere
    assert baslik == "Farklı kaydet"
    assert yol == str(Path.home() / "Kurtarma-Anahtarı-Belgesi_06.11.2026.pdf")


def test_indirme_onerilen_adi_yol_tasiyamaz() -> None:
    """Önerilen ad sayfadan gelir: ev dizininin dışına önermez."""
    dosya_penceresi = _SahteDosyaPenceresi("")

    qt_kurulum.indirme_isleyicisi(dosya_penceresi)(_pencere(), _SahteIndirme("../../gizli/x.pdf"))

    assert dosya_penceresi.sorulan[0][2] == str(Path.home() / "x.pdf")


def test_indirme_iptalinde_kabul_edilmez() -> None:
    indirme = _SahteIndirme()

    qt_kurulum.indirme_isleyicisi(_SahteDosyaPenceresi(""))(_pencere(), indirme)

    assert indirme.cagrilar == []


def test_isleyici_arka_uc_yuklenirken_degistirilir() -> None:
    """`webview.platforms.qt` erken içe aktarılmaz (modül belgesi): değişim `initialize`'ın ardındadır;
    sınıfın yöntemi olur, pencerenin kurucusu yuvayı oradan bağlar."""
    webview = _SahteWebview()
    dosya_penceresi = _SahteDosyaPenceresi("/uydurma/secilen.pdf")
    eski = _SahteArkaUc.BrowserView.on_download_requested

    try:
        qt_kurulum.indirme_isleyicisini_bagla(webview, dosya_penceresi)
        assert webview.istenen == []  # arka uç bu çağrıda yüklenmez
        assert _SahteArkaUc.BrowserView.on_download_requested is eski

        arka_uc = webview.initialize("qt")

        assert webview.istenen == ["qt"]
        assert arka_uc is webview.arka_uc
        indirme = _SahteIndirme()
        arka_uc.BrowserView().on_download_requested(indirme)
        assert indirme.cagrilar == [("dizin", "/uydurma"), ("ad", "secilen.pdf"), ("kabul",)]
    finally:
        _SahteArkaUc.BrowserView.on_download_requested = eski  # type: ignore[method-assign]


def test_kurulum_indirme_isleyicisini_baglar() -> None:
    qt = _SahteQt()
    webview = _SahteWebview()
    eski = webview.initialize

    kurulum = _kurulum(qt, _Sayac(), webview=webview)

    assert webview.initialize != eski
    kurulum.durdur()


def test_pencere_bileseni_yoksa_kurulum_surer(od_gunlugu: list[logging.LogRecord]) -> None:
    def yuklenemez() -> Any:
        raise ImportError("webview yok")

    qt = _SahteQt()
    kurulum = hazirla(
        _Sayac(),
        icon_path=None,
        qt_loader=qt.yukleyici,
        signal_installer=_SinyalKaydi(),
        webview_loader=yuklenemez,
    )

    assert kurulum.hazir is True
    assert any("İndirme işleyicisi bağlanamadı." in k.getMessage() for k in od_gunlugu)
    kurulum.durdur()
