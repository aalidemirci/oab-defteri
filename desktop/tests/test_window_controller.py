"""Pencere denetçisi testleri — çarpı = çık, onay sorulmaz (T6; tasarım §4.2, §4.5).

pywebview Docker imajında yoktur: pencere ve olayları sahtedir. Sahte olay,
pywebview 5.3.2'nin `Event.set()` sözleşmesini taklit eder (işleyicilerden biri
`False` dönerse kapanma iptal). "Exe açılır, çarpıyla kapanır, çıkış kodu doğru"
F1a kapısında elle doğrulanır (packaging/windows/NOTLAR.md).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from desktop import window as window_mod
from desktop.window import WindowController, open_window


class _SahteOlay:
    """pywebview `Event`: `+=` ile işleyici eklenir; `set()` iptal edildiyse `True` döner."""

    def __init__(self) -> None:
        self.isleyiciler: list[Callable[[], Any]] = []

    def __iadd__(self, isleyici: Callable[[], Any]) -> _SahteOlay:
        self.isleyiciler.append(isleyici)
        return self

    def set(self) -> bool:
        donenler = [isleyici() for isleyici in self.isleyiciler]
        return any(deger is False for deger in donenler)


class _SahtePencere:
    _YONTEMLER = frozenset({"hide", "show", "minimize", "restore", "maximize", "destroy"})

    def __init__(self) -> None:
        self.events = SimpleNamespace(
            closing=_SahteOlay(),
            shown=_SahteOlay(),
            minimized=_SahteOlay(),
            maximized=_SahteOlay(),
            restored=_SahteOlay(),
        )
        self.cagrilar: list[str] = []
        self.native: Any = None
        self.patlayan: str | None = None

    def __getattr__(self, ad: str) -> Callable[[], None]:
        if ad not in self._YONTEMLER:
            raise AttributeError(ad)

        def yontem() -> None:
            if ad == self.patlayan:
                raise RuntimeError("pencere motoru meşgul")
            self.cagrilar.append(ad)

        return yontem

    def carpiya_bas(self) -> bool:
        """`True` = pencere kapandı, `False` = kapanma iptal edildi."""
        return not self.events.closing.set()


class _SahteWebview:
    def __init__(self, pencere: _SahtePencere) -> None:
        self.settings: dict[str, Any] = {}
        self.pencere = pencere
        self.start_kwargs: dict[str, Any] | None = None

    def create_window(self, title: str, url: str, **kwargs: Any) -> _SahtePencere:
        return self.pencere

    def start(self, **kwargs: Any) -> None:
        self.start_kwargs = kwargs


def _bagli(
    *, gosterildi: bool = True, platform: str = "linux"
) -> tuple[WindowController, _SahtePencere]:
    denetci = WindowController(platform=platform)
    pencere = _SahtePencere()
    denetci.bind(pencere)
    if gosterildi:
        pencere.events.shown.set()
    return denetci, pencere


# ------------------------------------------------------------------ çarpı


@pytest.mark.parametrize("platform", ["linux", "win32"])
def test_carpi_programi_kapatir_onay_sormaz(platform: str) -> None:
    """T6: kapanma iptal edilmez; pencere gizlenmez, küçültülmez (tepsi yok)."""
    denetci, pencere = _bagli(platform=platform)

    assert pencere.carpiya_bas() is True
    assert pencere.cagrilar == []  # pencereyi kullanıcı kapatıyor: ikinci destroy yok
    assert denetci.quitting is True


def test_carpidan_sonra_gelen_komutlar_etkisiz() -> None:
    denetci, pencere = _bagli()
    pencere.carpiya_bas()

    denetci.show()
    denetci.request_quit()

    assert pencere.cagrilar == []


def test_tepsi_ve_arayuze_cikis_olayi_yolu_yok() -> None:
    """T6: tepsi, gizleme ve görevli kipinde arayüze `od:cik-iste` olayı sökülmüştür."""
    denetci = WindowController(platform="linux")

    assert not hasattr(denetci, "tray_available")
    assert not hasattr(denetci, "ask_quit_in_spa")
    assert not hasattr(WindowController, "SPA_QUIT_EVENT")


# ------------------------------------------------------------------ Çık


def test_cik_pencereyi_kapatir() -> None:
    denetci, pencere = _bagli()

    denetci.request_quit()

    assert pencere.cagrilar == ["destroy"]
    assert pencere.carpiya_bas() is True  # destroy'un tetiklediği closing geçer
    assert denetci.quitting is True


def test_cik_iki_kez_gelse_de_pencere_bir_kez_kapatilir() -> None:
    denetci, pencere = _bagli()

    denetci.request_quit()
    denetci.request_quit()  # tepsiden Çık + kurucunun kapatma olayı

    assert pencere.cagrilar == ["destroy"]


def test_pencere_gosterilmeden_gelen_cik_gosterilince_uygulanir() -> None:
    """Kapatma olayı açılış sırasında gelebilir; pywebview API'si `shown`'ı bekler."""
    denetci, pencere = _bagli(gosterildi=False)

    denetci.request_quit()
    assert pencere.cagrilar == []

    pencere.events.shown.set()
    assert pencere.cagrilar == ["destroy"]


def test_kapatma_hatasi_yutulur() -> None:
    denetci, pencere = _bagli()
    pencere.patlayan = "destroy"

    denetci.request_quit()  # hata yükseltmez

    assert denetci.quitting is True


# ---------------------------------------------------------- Pencereyi aç


def test_pencereyi_ac_pencereyi_one_getirir() -> None:
    """İkinci açılış (`goster` komutu) çalışan pencereyi öne getirir."""
    denetci, pencere = _bagli()

    denetci.show()

    assert pencere.cagrilar == ["show"]


def test_pencereyi_ac_kucultulmus_pencereyi_eski_boyutuna_dondurur() -> None:
    denetci, pencere = _bagli()
    pencere.events.minimized.set()
    denetci.show()  # normal boyuttan küçültülmüş → restore

    pencere.events.maximized.set()
    pencere.events.minimized.set()
    denetci.show()  # büyütülmüşken küçültülmüş → maximize (restore normal boyuta düşürürdü)

    pencere.events.restored.set()
    denetci.show()  # küçültülmemiş → yalnız show

    assert pencere.cagrilar == ["show", "restore", "show", "maximize", "show"]


def test_pencereyi_ac_cikista_ya_da_pencere_yokken_etkisiz() -> None:
    WindowController(platform="linux").show()  # bağlanmamış
    denetci, pencere = _bagli()
    denetci.request_quit()

    denetci.show()

    assert pencere.cagrilar == ["destroy"]


def test_pencereyi_ac_hatasi_yutulur() -> None:
    denetci, pencere = _bagli()
    pencere.patlayan = "show"

    denetci.show()  # hata yükseltmez


# ------------------------------------------------------------ open_window


def test_denetci_pencereye_start_tan_once_baglanir(tmp_path: Path) -> None:
    sahte = _SahteWebview(_SahtePencere())
    denetci = WindowController(platform="linux")

    open_window(
        "http://127.0.0.1:1/",
        webview=sahte,
        platform="linux",
        storage_path=tmp_path,
        controller=denetci,
    )

    assert sahte.start_kwargs is not None and sahte.start_kwargs["gui"] == "qt"
    assert sahte.pencere.events.closing.isleyiciler == [denetci.on_closing]


def test_cik_acilista_istendiyse_pencere_hic_baslatilmaz(tmp_path: Path) -> None:
    sahte = _SahteWebview(_SahtePencere())
    denetci = WindowController(platform="linux")
    denetci.request_quit()

    open_window(
        "http://127.0.0.1:1/",
        webview=sahte,
        platform="linux",
        storage_path=tmp_path,
        controller=denetci,
    )

    assert sahte.start_kwargs is None


# ------------------------------------------ Windows oturum kapanışı (FormClosing)


class _NetOlayi:
    def __init__(self) -> None:
        self.isleyiciler: list[Callable[[Any, Any], None]] = []

    def __iadd__(self, isleyici: Callable[[Any, Any], None]) -> _NetOlayi:
        self.isleyiciler.append(isleyici)
        return self


def test_windows_oturum_kapanisinda_iptal_yok_ve_ek_isleyici_baglanmaz() -> None:
    """§4.5: kapanma hiç iptal edilmediği için oturum kapanışında iptali geri alan
    .NET işleyicisi gereksizleşti; davranış testle sabitlendi, işleyici silindi."""
    denetci = WindowController(platform="win32")
    pencere = _SahtePencere()
    pencere.native = SimpleNamespace(FormClosing=_NetOlayi())
    denetci.bind(pencere)
    pencere.events.shown.set()

    assert pencere.carpiya_bas() is True  # WindowsShutDown da UserClosing da iptal edilmez
    assert pencere.native.FormClosing.isleyiciler == []
    assert not hasattr(window_mod, "install_session_end_passthrough")
