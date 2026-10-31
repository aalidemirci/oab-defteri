"""Linux kurulum provasının Debian sürümleri (tasarım §13 D17, §11.3).

Pardus 21/23/25 sırasıyla Debian 11 (bullseye), 12 (bookworm) ve 13 (trixie)
tabanlıdır. Prova yerelde `test-kurulum.sh`, CI'da `paketleme.yml`
`linux-kurulum` matrisiyle koşar; iki liste aynı üç sürümü taşımalıdır, biri
eksilirse o Pardus sürümünün kurulumu sessizce sınanmaz olur.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BEKLENEN = ["11", "12", "13"]


def test_yerel_prova_uc_debian_surumunu_kosar() -> None:
    metin = (REPO / "packaging" / "linux" / "test-kurulum.sh").read_text(encoding="utf-8")
    eslesme = re.search(r"^\s+SURUMLER=\(([^)]*)\)$", metin, re.MULTILINE)
    assert eslesme is not None
    assert eslesme.group(1).split() == BEKLENEN


def test_ci_matrisi_uc_debian_surumunu_kosar() -> None:
    metin = (REPO / ".github" / "workflows" / "paketleme.yml").read_text(encoding="utf-8")
    blok = metin.split("\n  linux-kurulum:", 1)[1].split("\n  windows:", 1)[0]
    eslesme = re.search(r"^\s+debian: \[([^\]]*)\]$", blok, re.MULTILINE)
    assert eslesme is not None
    assert re.findall(r'"(\d+)"', eslesme.group(1)) == BEKLENEN
