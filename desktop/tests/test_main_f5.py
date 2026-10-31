"""Açılış/kapanış akışının F5 bağlantıları (tasarım §4.2, §4.5, T9, T16, TB13, TB14).

* Tepsideki Çık görevli kipinde parolayı SPA'da ister.
* (Çık kancası, WAL checkpoint, iş parçacığı bağlantısı ve günlük yedek işi
  testleri `test_main.py`'ye taşındı — tasarım §12.B.)
* `--tepside`: pencere yalnız tepsi kurulduysa gizli açılır.
* Yükseltilmiş yardımcı kip veri dizini, günlük ve kilit AÇMAZ.
* Gün değişimi kapısının yerleşik işleri (IP denetimi, uyku dinleyicisi).

Backend kancası (`apps.okul.masaustu_kanca`) ve `app/quit/` görünümü backend
testlerindedir (`backend/apps/okul/tests/test_cikis_ucu.py`).
"""

from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from desktop import guvenlik_duvari
from desktop import main as main_mod
from desktop.paths import ENV_APP_HOME, resolve_app_paths
from desktop.tray import TrayActions
from desktop.window import WindowController

def test_tepsi_eylemleri_kip_matrisi_hedeflerine_baglanir() -> None:
    denetci = WindowController(platform="linux")
    kontrol = SimpleNamespace(
        tepsi_satiri=lambda: "Ağ Kataloğu: kapalı",
        acik_mi=lambda: False,
        kapatilabilir_mi=lambda: False,
        sunulur_mu=lambda: True,
        ac=lambda: {},
        kapat=lambda: {},
        adres=lambda: None,
    )

    eylemler = main_mod.tepsi_eylemleri(denetci, kontrol)  # type: ignore[arg-type]

    assert eylemler.show == denetci.show
    assert eylemler.quit == denetci.request_quit
    assert eylemler.quit_gorevli == denetci.ask_quit_in_spa  # parola SPA'da (§4.2-4)
    assert eylemler.kip is main_mod.kip_durumu  # tek durum kaynağı KipDurumu (T16)
    assert eylemler.katalog_satiri is kontrol.tepsi_satiri
    # Aç/kapa "kapat"ı ayar açık ama katalog açılamamışken de sunar (F5 düzeltmesi).
    assert eylemler.katalog_kapatilabilir is kontrol.kapatilabilir_mi
    # KB-2: taşınabilir arşivde "aç" tepside yoktur; karar denetçinindir (T16).
    assert eylemler.katalog_sunulur is kontrol.sunulur_mu
    assert eylemler.gorevli_kipine_gec is not None and eylemler.kilitle is not None


def test_katalog_denetcisi_yoksa_tepsi_yalniz_ac_ve_cik() -> None:
    denetci = WindowController(platform="linux")

    eylemler = main_mod.tepsi_eylemleri(denetci, None)

    assert eylemler == TrayActions(show=denetci.show, quit=denetci.request_quit)


def test_katalog_ac_kapa_tepsi_dongusunu_bekletmez() -> None:
    """Güvenlik duvarı denetimi saniyeler sürer: tepsi komutu ayrı iş parçacığında koşar."""
    olay = threading.Event()
    adlar: list[str] = []

    def yavas() -> None:
        adlar.append(threading.current_thread().name)
        olay.set()

    main_mod._arka_planda("od-katalog-ac", yavas)()

    assert olay.wait(5)
    assert adlar == ["od-katalog-ac"]


# ----------------------------------------------------------- tepside açılış


class _Tepsi:
    def __init__(self, var: bool) -> None:
        self.available = var

    def stop(self) -> None:
        pass


@pytest.mark.parametrize(("tepsi_var", "gizli"), [(True, True), (False, False)])
def test_tepside_acilis_yalniz_tepsi_varsa_gizli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tepsi_var: bool, gizli: bool
) -> None:
    kayit: dict[str, Any] = {}
    monkeypatch.setattr(main_mod, "start_tray", lambda eylemler, **_: _Tepsi(tepsi_var))

    def pencere(url: str, **kw: Any) -> None:
        kayit.update(kw)

    monkeypatch.setattr(main_mod, "open_window", pencere)

    main_mod.run_window_session(
        "http://127.0.0.1:1/", tmp_path, None, platform="linux", tepside=True
    )

    assert kayit["hidden"] is gizli


def test_tepside_bayragi() -> None:
    assert main_mod.build_parser().parse_args([]).tepside is False
    assert main_mod.build_parser().parse_args(["--tepside"]).tepside is True


# ------------------------------------------------------ yükseltilmiş kip


def test_yukseltilmis_yardimci_kip_veri_dizini_gunluk_ve_kilit_acmaz(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alinan: list[list[str]] = []

    def acilmamali(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("yükseltilmiş kip olağan açılışa girdi")

    monkeypatch.setattr(main_mod, "resolve_paths", acilmamali)
    monkeypatch.setattr(main_mod, "configure_logging", acilmamali)
    monkeypatch.setattr(main_mod, "SingleInstanceLock", acilmamali)

    def yukseltilmis(argv: list[str]) -> int:
        alinan.append(list(argv))
        return 0

    monkeypatch.setattr(guvenlik_duvari, "yukseltilmis_kip", yukseltilmis)

    kod = main_mod.run(["--guvenlik-duvari-kurali", "--port", "9100"])

    assert kod == 0
    assert alinan == [["--guvenlik-duvari-kurali", "--port", "9100"]]


def test_gun_kapisi_yerlesik_isleri_kaydeder_ve_uyku_dinleyicisini_baglar(tmp_path: Path) -> None:
    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)})
    dinleyiciler: list[Any] = []
    kontrol = SimpleNamespace(
        uyku_gerekli=lambda: False,
        ip_denetle=lambda: True,
        saatlik_denetle=lambda: True,
        uyku_dinleyicisi_ekle=dinleyiciler.append,
    )

    kapi = main_mod.gun_kapisi_kur(paths, kontrol)  # type: ignore[arg-type]

    assert kapi.is_adlari[:2] == ("gunluk-yedek", "ip-denetimi")
    assert dinleyiciler == [kapi.uyandir]
