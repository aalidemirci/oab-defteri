"""Ağ yüzeyi ayarları — `ALLOWED_HOSTS` koşulu (tasarım §4.1, §4.3 tehdit 2, §13 D46).

Program ağ servisi sunmaz: yönetim sunucusu yalnız 127.0.0.1'de, rastgele portta ve
oturum belirteciyle dinler; hiçbir port okul ağına açılmaz. Masaüstü kabuğu açılışta
`OD_SESSION_TOKEN` verir: o zaman Django yalnız loopback adlarını kabul eder (DNS
rebinding'e karşı). Geliştirme ağının servis adı (`backend`, Vite proxy'si) yalnız
belirteç BOŞKEN eklenir. Aile iskeletinde bu koşul yazılıydı ama kodda yoktu.
"""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from config import settings as ayarlar

AYAR_DOSYASI = Path(ayarlar.__file__)
LOOPBACK = ["127.0.0.1", "localhost"]


def test_belirtec_doluyken_yalniz_loopback_adlari_kabul_edilir() -> None:
    assert ayarlar.izinli_hostlar({"OD_SESSION_TOKEN": "belirtec"}) == LOOPBACK


@pytest.mark.parametrize("ortam", [{}, {"OD_SESSION_TOKEN": ""}])
def test_belirtec_bosken_gelistirme_agi_servis_adi_eklenir(ortam: dict[str, str]) -> None:
    assert ayarlar.izinli_hostlar(ortam) == [*LOOPBACK, "backend"]


def test_ayar_dosyasi_belirtecle_yuklenince_backend_adi_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ayar dosyasının kendisi (modül düzeyi) belirteçle yüklenir: paketli yapının hâli."""
    monkeypatch.setenv("OD_SESSION_TOKEN", "sinama-belirteci")
    monkeypatch.setenv("OD_DATA_DIR", str(tmp_path))

    degerler = runpy.run_path(str(AYAR_DOSYASI))

    assert degerler["ALLOWED_HOSTS"] == LOOPBACK
    # Aynı koşul oturum belirteci middleware'ini de yükler (§5.3).
    assert degerler["MIDDLEWARE"][0] == "desktop.session_guard.SessionTokenMiddleware"


def test_ayar_dosyasi_belirtecsiz_yuklenince_backend_adi_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("OD_SESSION_TOKEN", raising=False)
    monkeypatch.setenv("OD_DATA_DIR", str(tmp_path))

    degerler = runpy.run_path(str(AYAR_DOSYASI))

    assert degerler["ALLOWED_HOSTS"] == [*LOOPBACK, "backend"]
    assert "desktop.session_guard.SessionTokenMiddleware" not in degerler["MIDDLEWARE"]
