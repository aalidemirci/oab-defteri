"""F11 uçtan uca testlerinin alt süreç yardımcıları (toplanmaz: `test_` ile başlamaz).

Gerçek program (`python -m desktop.main`) ve prova betiği
(`python -m desktop.tests.prova_betigi`) AYRI süreçte, depo kökünde koşar: masaüstü
testlerinin asgari Django ayarları gerçek şemayı ve şifrelemeyi taşımaz.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ZAMAN_ASIMI_SN = 300


def kos(
    argv: list[str], *, ortam: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Python'u verilen argümanlarla depo kökünde koşar (kabuk yok)."""
    return subprocess.run(  # noqa: S603 — argümanlar testin kendi sabitleri, kabuk yok
        [sys.executable, *argv],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=ZAMAN_ASIMI_SN,
        env={**os.environ, **(ortam or {})},
    )


def program(*argv: str, ortam: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """`oab-defteri <argv>` — gerçek masaüstü girişi."""
    return kos(["-m", "desktop.main", *argv], ortam=ortam)


def betik(*argv: str) -> dict[str, Any]:
    """Prova betiği; başarısızsa testi stderr ile düşürür, son satırdaki JSON'u döndürür."""
    sonuc = kos(["-m", "desktop.tests.prova_betigi", *argv])
    assert sonuc.returncode == 0, sonuc.stderr[-4000:]
    satirlar = [satir for satir in sonuc.stdout.strip().splitlines() if satir.strip()]
    assert satirlar, sonuc.stderr[-4000:]
    veri: dict[str, Any] = json.loads(satirlar[-1])
    return veri


def gunluk(veri_koku: Path) -> str:
    """Programın günlük dosyası (yoksa boş)."""
    yol = veri_koku / "logs" / "uygulama.log"
    return yol.read_text(encoding="utf-8") if yol.is_file() else ""


