"""Kural testlerinin faz süzmesi (tasarım §6.3 D6, §10.5 `ev::test_katalogdaki_her_kodun_testi_var`).

Bir kuralın davranış testi ya da bir evrakın kabul testi ancak fazı geldiğinde istenir. Tek süzme
burasıdır: evrak kataloğu (kod → faz) ve kural paketi (kimlik → `davranis_fazi`) aynı işlevi kullanır.

`GECERLI_FAZ`, kabul ve davranış testleri tamamlanmış son fazdır; bir faz kapısının kalemleri
bitmeden ilerlemez. F1c'nin 10. adımı (plan "F1c adımları") onu `F1c` yaptı: F1c'nin evrakları
(E01-E03) kabul testleriyle, F1c kurallarının hepsi davranış testleriyle istenir; kalem eksikse
testler düşer (`test_katalogdaki_her_kodun_testi_var`, `test_davranis_fazi_gelen_kuralin_davranis_testi_var`).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

#: Fazların sırası (plan §1 ve §3). `F8+` katalogdaki "F8 ve sonrası" fazıdır (tasarım §9.5).
FAZ_SIRASI: Final[tuple[str, ...]] = (
    "F1a",
    "F1b",
    "F1c",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F8+",
)
GECERLI_FAZ: Final = "F1c"


def faz_geldi_mi(faz: str, *, gecerli: str = GECERLI_FAZ) -> bool:
    """`faz` geçerli faza eşit ya da ondan küçük mü? Bilinmeyen faz `ValueError` verir."""
    if faz not in FAZ_SIRASI:
        raise ValueError(f"Bilinmeyen faz: {faz}")
    return FAZ_SIRASI.index(faz) <= FAZ_SIRASI.index(gecerli)


def fazi_gelenler(fazlar: Mapping[str, str], *, gecerli: str = GECERLI_FAZ) -> set[str]:
    """Fazı gelmiş anahtarlar (katalogda evrak kodu, pakette kural kimliği)."""
    return {anahtar for anahtar, faz in fazlar.items() if faz_geldi_mi(faz, gecerli=gecerli)}
