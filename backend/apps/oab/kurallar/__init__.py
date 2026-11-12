"""Kural motoru (tasarım §6): programın koyduğu her oran, süre ve sınırın tek kaynağı (altın kural 2).

Paket dosyaları `paketler/` altındadır, programla dağıtılır. Servisler değeri `kural("<id>")` ile okur,
denetimi `denetle("<id>", ...)` ile yapar; koda sayı yazılmaz (D8).
"""

from __future__ import annotations

from apps.oab.kurallar.erisim import (
    VERI_YOK,
    atifli_metin,
    bilgi_notu,
    denetle,
    kural,
    kural_kaydi,
    yazma_kapisi,
)
from apps.oab.kurallar.hatalar import (
    BilinmeyenKural,
    DonemKopyasiDogrulanamadi,
    KuralPaketiKullanilamaz,
    OlayTarihiGerekli,
    YururlukteDegerYok,
)

__all__ = [
    "VERI_YOK",
    "BilinmeyenKural",
    "DonemKopyasiDogrulanamadi",
    "KuralPaketiKullanilamaz",
    "OlayTarihiGerekli",
    "YururlukteDegerYok",
    "atifli_metin",
    "bilgi_notu",
    "denetle",
    "kural",
    "kural_kaydi",
    "yazma_kapisi",
]
