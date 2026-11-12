"""PyInstaller çalışma zamanı kancası (`rthook_od.py`).

Kanca giriş betiğinden ÖNCE her çağrıda çalışır. Aile iskeletindeki yükseltilmiş
güvenlik duvarı yardımcı kipi (UAC, `--guvenlik-duvari-kurali`) ağ kataloğuyla
birlikte söküldü (tasarım §4.1): kancada da o kipin dalı kalmamalıdır.

Kanca içe aktarılınca `setup()` modül düzeyinde koşar: ortam değişkenlerine
dokunduğu için `os.environ` testte kopyayla değiştirilir; Linux'ta font yapılandırmasını
önbellek dizinine yazdığı için önbellek kökü geçici dizine yönlendirilir.

Font yapılandırması (tasarım §9.1-8: iki sistemde paketli yazı tipleri, sistem dizini
taranmaz): Windows'ta süreç geneli `FONTCONFIG_FILE`, Linux'ta yalnız evrak yoluna
`OD_EVRAK_FONTCONFIG` (süreç geneli değişken pencere yazı tiplerini değiştirirdi).
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
PDF_KAPISI = Path(__file__).resolve().parents[2] / "backend" / "shared" / "pdf.py"
SABLON = KANCA.parent / "fonts.conf.tmpl"


def _kanca(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ModuleType:
    monkeypatch.setattr(os, "environ", dict(os.environ))
    os.environ["XDG_CACHE_HOME"] = str(tmp_path / "xdg-onbellek")
    os.environ["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    tanim = importlib.util.spec_from_file_location("rthook_od_sinama", KANCA)
    assert tanim is not None and tanim.loader is not None
    modul = importlib.util.module_from_spec(tanim)
    tanim.loader.exec_module(modul)
    return modul


def test_yukseltilmis_yardimci_kip_dali_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    kanca = _kanca(monkeypatch, tmp_path)

    assert not hasattr(kanca, "UAC_BAYRAGI")
    assert not hasattr(kanca, "yukseltilmis_yardimci_mi")
    assert "--guvenlik-duvari-kurali" not in KANCA.read_text(encoding="utf-8")


def test_windowsta_font_yapilandirmasi_kurulur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    kanca = _kanca(monkeypatch, tmp_path)
    cagrilar: list[Any] = []
    monkeypatch.setattr(kanca.sys, "platform", "win32")
    monkeypatch.setattr(sys, "argv", ["oab-defteri.exe"])
    monkeypatch.setattr(kanca, "_bundle_root", lambda: tmp_path)
    monkeypatch.setattr(kanca, "setup_fontconfig", lambda *a: cagrilar.append(a))
    monkeypatch.setattr(kanca, "_cache_root", lambda: tmp_path / "onbellek")

    kanca.setup()

    assert len(cagrilar) == 1


def test_linuxta_yalniz_evrak_font_yapilandirmasi_bildirilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Linux paketinde de paketteki `fonts/` tek dizindir (tasarım §9.1-8): kanca şablonu işler ve
    yolunu `OD_EVRAK_FONTCONFIG` ile evrak yoluna bildirir; süreç geneli `FONTCONFIG_FILE` kurulmaz."""
    kanca = _kanca(monkeypatch, tmp_path)
    kok = tmp_path / "paket"
    (kok / "fonts").mkdir(parents=True)
    (kok / "fonts.conf.tmpl").write_text(SABLON.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(kanca.sys, "platform", "linux")
    monkeypatch.setattr(kanca, "_bundle_root", lambda: kok)
    monkeypatch.setattr(kanca, "_cache_root", lambda: tmp_path / "onbellek")
    os.environ.pop("FONTCONFIG_FILE", None)
    os.environ.pop("OD_EVRAK_FONTCONFIG", None)

    kanca.setup()

    conf = tmp_path / "onbellek" / "fonts.conf"
    assert os.environ["OD_EVRAK_FONTCONFIG"] == str(conf)
    assert "FONTCONFIG_FILE" not in os.environ
    metin = conf.read_text(encoding="utf-8")
    assert f"<dir>{(kok / 'fonts').as_posix()}</dir>" in metin
    assert metin.count("<dir") == 1 and "@FONT_DIR@" not in metin and "@CACHE_DIR@" not in metin


def test_evrak_font_degiskeni_pdf_kapisiyla_ayni_ad() -> None:
    """Kanca backend'i içe aktarmaz; değişken adı iki yerde yazılıdır ve aynı olmalıdır."""
    tanim = 'ENV_EVRAK_FONTCONFIG = "OD_EVRAK_FONTCONFIG"'
    assert tanim in KANCA.read_text(encoding="utf-8")
    assert tanim in PDF_KAPISI.read_text(encoding="utf-8")
