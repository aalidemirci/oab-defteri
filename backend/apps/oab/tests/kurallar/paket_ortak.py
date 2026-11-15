"""Programla gelen kural paketi revizyonları: testler en yeni revizyona bakar (plan F2 §3.3).

Yeni revizyon geldiğinde (F2'de `r2`) dönem en yeni revizyona bağlanır, `denetle` sonucu onun
numarasını taşır. Revizyon numarasını elle yazan test her revizyonda bozulmasın diye sayı buradan
okunur. Revizyonların listesi `MANIFEST.json`'dadır (D7); sıra dosya adının revizyon numarasıdır.
"""

from __future__ import annotations

import json
from typing import Any, Final

from apps.oab.kurallar import yukleyici as yk


def oku(dosya: str) -> dict[str, Any]:
    """Dağıtılan revizyon dosyasının içeriği."""
    icerik: dict[str, Any] = json.loads((yk.PAKETLER_DIZINI / dosya).read_text(encoding="utf-8"))
    return icerik


_MANIFEST: Final[dict[str, Any]] = json.loads(
    (yk.PAKETLER_DIZINI / yk.MANIFEST_ADI).read_text(encoding="utf-8")
)
#: `MANIFEST.json`'daki revizyon dosyaları, revizyon sırasıyla.
DOSYALAR: Final[tuple[str, ...]] = tuple(
    sorted((satir["dosya"] for satir in _MANIFEST["paketler"]), key=yk._ad_parcalari)
)
#: Revizyonların içeriği, aynı sırayla.
REVIZYONLAR: Final[tuple[dict[str, Any], ...]] = tuple(oku(dosya) for dosya in DOSYALAR)
EN_YENI: Final[dict[str, Any]] = REVIZYONLAR[-1]
EN_YENI_DOSYA: Final[str] = DOSYALAR[-1]
PAKET: Final[str] = EN_YENI["paket"]
#: Yeni dönemin bağlandığı revizyon (en yeni).
EN_YENI_REV: Final[int] = EN_YENI["rev"]
