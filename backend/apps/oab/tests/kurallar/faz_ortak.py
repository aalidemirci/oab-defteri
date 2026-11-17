"""Kural testlerinin faz süzmesi (tasarım §6.3 D6, §10.5 `ev::test_katalogdaki_her_kodun_testi_var`).

Bir kuralın davranış testi ya da bir evrakın kabul testi ancak fazı geldiğinde istenir. Tek süzme
burasıdır: evrak kataloğu (kod → faz) ve kural paketi (kimlik → `davranis_fazi`) aynı işlevi kullanır.

`GECERLI_FAZ`, kabul ve davranış testleri tamamlanmış son fazdır; bir faz kapısının kalemleri
bitmeden ilerlemez. F1c'nin 10. adımı (plan "F1c adımları") onu `F1c`, F2'nin kapısı (plan F2 §2)
`F2` yaptı: F2'ye dek gelen evraklar (F1b'nin E63'ü, F1c'nin E01-E03'ü, F2'nin E04-E14'ü ve E64'ü)
kabul testleriyle, F1c ve F2'nin kurallarının hepsi (F2'de `r2`'nin davranış fazı F2 olan 13 kuralı)
davranış testleriyle istenir; kalem eksikse testler düşer (`test_katalogdaki_her_kodun_testi_var`,
`test_davranis_fazi_gelen_kuralin_davranis_testi_var`). Değerin kendisi
`test_f2_kurallarinin_davranis_testi_tamam` ve `test_gecerli_fazin_evraklari_f2_kapisidir` ile
kilitlidir.
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
GECERLI_FAZ: Final = "F2"


def faz_geldi_mi(faz: str, *, gecerli: str = GECERLI_FAZ) -> bool:
    """`faz` geçerli faza eşit ya da ondan küçük mü? Bilinmeyen faz `ValueError` verir."""
    if faz not in FAZ_SIRASI:
        raise ValueError(f"Bilinmeyen faz: {faz}")
    return FAZ_SIRASI.index(faz) <= FAZ_SIRASI.index(gecerli)


def fazi_gelenler(fazlar: Mapping[str, str], *, gecerli: str = GECERLI_FAZ) -> set[str]:
    """Fazı gelmiş anahtarlar (katalogda evrak kodu, pakette kural kimliği)."""
    return {anahtar for anahtar, faz in fazlar.items() if faz_geldi_mi(faz, gecerli=gecerli)}
