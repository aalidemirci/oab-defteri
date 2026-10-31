"""PyInstaller çalışma zamanı kancası (`rthook_od.py`).

Kanca giriş betiğinden ÖNCE her çağrıda çalışır. Aile iskeletindeki yükseltilmiş
güvenlik duvarı yardımcı kipi (UAC, `--guvenlik-duvari-kurali`) ağ kataloğuyla
birlikte söküldü (tasarım §4.1): kancada da o kipin dalı kalmamalıdır.

Kanca içe aktarılınca `setup()` modül düzeyinde koşar: ortam değişkenlerine
dokunduğu için `os.environ` testte kopyayla değiştirilir.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

KANCA = Path(__file__).resolve().parents[1] / "pyinstaller" / "rthook_od.py"


def _kanca(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.setattr(os, "environ", dict(os.environ))
    tanim = importlib.util.spec_from_file_location("rthook_od_sinama", KANCA)
    assert tanim is not None and tanim.loader is not None
    modul = importlib.util.module_from_spec(tanim)
    tanim.loader.exec_module(modul)
    return modul


def test_yukseltilmis_yardimci_kip_dali_yok(monkeypatch: pytest.MonkeyPatch) -> None:
    kanca = _kanca(monkeypatch)

    assert not hasattr(kanca, "UAC_BAYRAGI")
    assert not hasattr(kanca, "yukseltilmis_yardimci_mi")
    assert "--guvenlik-duvari-kurali" not in KANCA.read_text(encoding="utf-8")


def test_windowsta_font_yapilandirmasi_kurulur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    kanca = _kanca(monkeypatch)
    cagrilar: list[Any] = []
    monkeypatch.setattr(kanca.sys, "platform", "win32")
    monkeypatch.setattr(sys, "argv", ["oab-defteri.exe"])
    monkeypatch.setattr(kanca, "_bundle_root", lambda: tmp_path)
    monkeypatch.setattr(kanca, "setup_fontconfig", lambda *a: cagrilar.append(a))
    monkeypatch.setattr(kanca, "_cache_root", lambda: tmp_path / "onbellek")

    kanca.setup()

    assert len(cagrilar) == 1
