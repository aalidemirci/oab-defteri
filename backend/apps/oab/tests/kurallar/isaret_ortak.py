"""D6 ve D8 bekçilerinin statik taramaları (tasarım §6.3).

İşaretler `session.items`'tan okunmaz: `-k` ya da tek dosyalık koşuda eksik kalır ve bekçi yalancı
kırmızı verirdi. Test modülleri içe aktarılır, işaretler işlevlerin `pytestmark`'ından ve
`parametrize` satırlarının `marks`'ından toplanır.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil
from collections.abc import Iterable, Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

ISARETLER = ("kural_deger", "kural_davranis")


def _isaretin_kimligi(isaret: Any) -> tuple[str, str] | None:
    gercek = getattr(isaret, "mark", isaret)
    if gercek.name not in ISARETLER:
        return None
    if len(gercek.args) != 1 or not isinstance(gercek.args[0], str):
        raise ValueError(f"{gercek.name} tek bir kural kimliği alır: {gercek.args!r}")
    return gercek.name, gercek.args[0]


def _nesne_isaretleri(nesne: Any) -> Iterator[tuple[str, str]]:
    isaretler = getattr(nesne, "pytestmark", [])
    if not isinstance(isaretler, list):
        isaretler = [isaretler]
    for isaret in isaretler:
        gercek = getattr(isaret, "mark", isaret)
        if gercek.name == "parametrize":
            for satir in gercek.args[1] if len(gercek.args) > 1 else gercek.kwargs["argvalues"]:
                for ic in getattr(satir, "marks", ()):
                    kimlik = _isaretin_kimligi(ic)
                    if kimlik is not None:
                        yield kimlik
        kimlik = _isaretin_kimligi(gercek)
        if kimlik is not None:
            yield kimlik


def modul_isaretleri(modul: ModuleType) -> set[tuple[str, str]]:
    """Modüldeki `(işaret adı, kural kimliği)` çiftleri."""
    bulunan = set(_nesne_isaretleri(modul))
    for ad, nesne in vars(modul).items():
        if ad.startswith("test") and callable(nesne):
            bulunan |= set(_nesne_isaretleri(nesne))
        elif ad.startswith("Test") and inspect.isclass(nesne):
            bulunan |= set(_nesne_isaretleri(nesne))
            for ic_ad, ic in vars(nesne).items():
                if ic_ad.startswith("test"):
                    bulunan |= set(_nesne_isaretleri(ic))
    return bulunan


def kural_test_modulleri(paket: str = "apps.oab.tests") -> Iterator[ModuleType]:
    kok = importlib.import_module(paket)
    for bilgi in pkgutil.walk_packages(kok.__path__, f"{paket}."):
        if bilgi.name.rsplit(".", 1)[-1].startswith("test_"):
            yield importlib.import_module(bilgi.name)


def kural_isaretleri(moduller: Iterable[ModuleType]) -> dict[str, set[str]]:
    """İşaret adı → o işareti taşıyan kural kimlikleri."""
    sonuc: dict[str, set[str]] = {ad: set() for ad in ISARETLER}
    for modul in moduller:
        for ad, kimlik in modul_isaretleri(modul):
            sonuc[ad].add(kimlik)
    return sonuc


def _is_kodu(kok: Path) -> Iterator[Path]:
    for yol in sorted(kok.rglob("*.py")):
        if not {"tests", "migrations"} & set(yol.parts):
            yield yol


def kural_cagrilari(kaynak: str) -> tuple[set[str], list[int]]:
    """Kaynaktaki `kural("…")` ve `denetle("…")` kimlikleri; sabit olmayan çağrıların satırları."""
    kimlikler: set[str] = set()
    sabitsiz: list[int] = []
    for dugum in ast.walk(ast.parse(kaynak)):
        if not isinstance(dugum, ast.Call):
            continue
        ad = (
            dugum.func.attr
            if isinstance(dugum.func, ast.Attribute)
            else getattr(dugum.func, "id", "")
        )
        if ad not in ("kural", "denetle", "bilgi_notu") or not dugum.args:
            continue
        ilk = dugum.args[0]
        if isinstance(ilk, ast.Constant) and isinstance(ilk.value, str):
            kimlikler.add(ilk.value)
        elif isinstance(ilk, ast.Name) and ilk.id.isupper():
            sabit = _modul_sabiti(kaynak, ilk.id)
            if sabit is None:
                sabitsiz.append(dugum.lineno)
            else:
                kimlikler.add(sabit)
        else:
            sabitsiz.append(dugum.lineno)
    return kimlikler, sabitsiz


def _modul_sabiti(kaynak: str, ad: str) -> str | None:
    for dugum in ast.parse(kaynak).body:
        if (
            isinstance(dugum, ast.Assign)
            and any(isinstance(hedef, ast.Name) and hedef.id == ad for hedef in dugum.targets)
            and isinstance(dugum.value, ast.Constant)
            and isinstance(dugum.value.value, str)
        ):
            return dugum.value.value
    return None


def koddaki_kural_cagrilari(kokler: Iterable[Path]) -> tuple[set[str], list[str]]:
    """İş kodundaki bütün kimlikler ve kimliği statik okunamayan çağrılar."""
    kimlikler: set[str] = set()
    okunamayan: list[str] = []
    for kok in kokler:
        for yol in _is_kodu(kok):
            bulunan, sabitsiz = kural_cagrilari(yol.read_text(encoding="utf-8"))
            kimlikler |= bulunan
            okunamayan += [f"{yol}:{satir}" for satir in sabitsiz]
    return kimlikler, okunamayan


def _sayilar(deger: Any) -> Iterator[int | str]:
    if isinstance(deger, bool):
        return
    if isinstance(deger, int | str):
        yield deger
    elif isinstance(deger, list):
        for ic in deger:
            yield from _sayilar(ic)
    elif isinstance(deger, dict):
        for ic in deger.values():
            yield from _sayilar(ic)


def paket_sayilari(kurallar: Iterable[dict[str, Any]]) -> tuple[set[int], set[str]]:
    """Paketteki tamsayılar (2 ve üstü) ile ondalık dizeler."""
    tamsayilar: set[int] = set()
    ondaliklar: set[str] = set()
    for kural in kurallar:
        for deger in _sayilar(kural["deger"]):
            if isinstance(deger, int) and deger >= 2:
                tamsayilar.add(deger)
            elif isinstance(deger, str) and deger[:1].isdigit():
                ondaliklar.add(deger)
    return tamsayilar, ondaliklar


def _timedelta_gunu(dugum: ast.Call) -> int | None:
    ad = dugum.func.attr if isinstance(dugum.func, ast.Attribute) else getattr(dugum.func, "id", "")
    if ad != "timedelta":
        return None
    for kelime in dugum.keywords:
        if (
            kelime.arg == "days"
            and isinstance(kelime.value, ast.Constant)
            and isinstance(kelime.value.value, int)
        ):
            return kelime.value.value
    return None


def sabit_bulgulari(
    kaynak: str, tamsayilar: set[int], ondaliklar: set[str]
) -> list[tuple[int, str]]:
    """D8 (sezgisel): paket değerinin çıplak yazımı. `(satır, kalıp)` listesi."""
    bulgular: list[tuple[int, str]] = []
    for dugum in ast.walk(ast.parse(kaynak)):
        if (
            isinstance(dugum, ast.Constant)
            and isinstance(dugum.value, str)
            and dugum.value in ondaliklar
        ):
            bulgular.append((dugum.lineno, f'"{dugum.value}"'))
        elif isinstance(dugum, ast.Call):
            gun = _timedelta_gunu(dugum)
            if gun in tamsayilar:
                bulgular.append((dugum.lineno, f"timedelta(days={gun})"))
        elif isinstance(dugum, ast.BinOp) and isinstance(dugum.op, ast.Mult):
            for yan in (dugum.left, dugum.right):
                if (
                    isinstance(yan, ast.Constant)
                    and isinstance(yan.value, int)
                    and yan.value in tamsayilar
                ):
                    bulgular.append((dugum.lineno, f"* {yan.value}"))
    return sorted(bulgular)


def oab_sabit_bulgulari(
    oab_koku: Path, tamsayilar: set[int], ondaliklar: set[str], izinli: set[tuple[str, str]]
) -> list[str]:
    """`apps/oab` iş kodunun D8 taraması (testler ve `kurallar/` hariç); izin listesi `(dosya, kalıp)`."""
    sonuc: list[str] = []
    for yol in _is_kodu(oab_koku):
        goreli = yol.relative_to(oab_koku).as_posix()
        if goreli.startswith("kurallar/"):
            continue
        for satir, kalip in sabit_bulgulari(
            yol.read_text(encoding="utf-8"), tamsayilar, ondaliklar
        ):
            if (goreli, kalip) not in izinli:
                sonuc.append(f"{goreli}:{satir}: {kalip}")
    return sonuc
