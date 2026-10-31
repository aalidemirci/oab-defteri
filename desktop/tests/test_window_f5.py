"""Pencere denetçisinin `loaded` davranışı ve pencere kurulumu (tasarım §4.2, §4.5).

* `shown` olayı bazı arka uçlarda geç gelebilir: sayfa yüklenince (`loaded`)
  pencere komut alır, açılışta gelen Çık uygulanır.
* Pencere her zaman görünür kurulur: OAB'de tepsi ve tepside gizli açılış yoktur (T6).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from desktop.window import WindowController, open_window


class _Olay:
    def __init__(self) -> None:
        self.isleyiciler: list[Callable[[], Any]] = []

    def __iadd__(self, isleyici: Callable[[], Any]) -> _Olay:
        self.isleyiciler.append(isleyici)
        return self

    def set(self) -> None:
        for isleyici in self.isleyiciler:
            isleyici()


class _Pencere:
    def __init__(self) -> None:
        self.events = SimpleNamespace(
            closing=_Olay(),
            shown=_Olay(),
            loaded=_Olay(),
            minimized=_Olay(),
            maximized=_Olay(),
            restored=_Olay(),
        )
        self.cagrilar: list[str] = []
        self.native: Any = None

    def show(self) -> None:
        self.cagrilar.append("show")

    def destroy(self) -> None:
        self.cagrilar.append("destroy")


def test_pencere_yuklenince_komut_alir() -> None:
    denetci = WindowController(platform="linux")
    pencere = _Pencere()
    denetci.bind(pencere)

    denetci.show()
    assert pencere.cagrilar == []  # henüz ne gösterildi ne yüklendi

    pencere.events.loaded.set()
    denetci.show()
    assert pencere.cagrilar == ["show"]


def test_acilista_gelen_cik_yuklenince_uygulanir() -> None:
    denetci = WindowController(platform="linux")
    pencere = _Pencere()
    denetci.bind(pencere)

    denetci.request_quit()
    assert pencere.cagrilar == []
    pencere.events.loaded.set()

    assert pencere.cagrilar == ["destroy"]


class _Webview:
    def __init__(self) -> None:
        self.settings: dict[str, Any] = {}
        self.kw: dict[str, Any] = {}

    def create_window(self, title: str, url: str, **kw: Any) -> _Pencere:
        self.kw = kw
        return _Pencere()

    def start(self, **kw: Any) -> None:
        return None


def test_pencere_gorunur_kurulur(tmp_path: Path) -> None:
    """T6: tepside gizli açılış (`--tepside`) sökülmüştür; pencere hep görünür açılır."""
    webview = _Webview()

    open_window("http://127.0.0.1:1/", storage_path=tmp_path, webview=webview, platform="linux")

    assert webview.kw.get("hidden", False) is False
