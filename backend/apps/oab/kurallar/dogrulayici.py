"""Kural paketi şemasının açılıştaki küçük doğrulayıcısı (tasarım §6.1, plan F1c kararları).

`jsonschema` yalnız `requirements-dev`'dedir (derlenmiş `rpds-py` pakete girmesin diye). Açılışta
aynı şema dosyasını bu dosya okur; bozuk örneklerde ikisinin aynı sonucu verdiği
`kp::test_kucuk_dogrulayici_jsonschema_ile_ayni_sonucu_verir` ile sınanır.

Yalnız şemada kullanılan anahtarları tanır. Tanımadığı anahtarı **yok saymaz**, `SemaHatasi` verir:
şemaya eklenen yeni anahtar, karşılığı burada yazılmadan sessizce denetimsiz kalmasın.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

#: Doğrulamayı etkilemeyen, yalnız açıklama taşıyan anahtarlar.
_ACIKLAMA_ANAHTARLARI = frozenset({"$schema", "$id", "title", "description", "$defs"})
_TIPLER: dict[str, type] = {
    "string": str,
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


class SemaHatasi(ValueError):
    """Şema dosyası bu doğrulayıcının okuyamayacağı bir anahtar ya da başvuru taşıyor."""


def _sayi_mi(deger: Any) -> bool:
    return isinstance(deger, int | float) and not isinstance(deger, bool)


def _tur_uyar(deger: Any, tur: str) -> bool:
    # JSON Schema 2020-12: `1.0` tamsayıdır, mantıksal değer sayı değildir (`jsonschema` ile aynı).
    if tur == "integer":
        return _sayi_mi(deger) and float(deger).is_integer()
    if tur == "number":
        return _sayi_mi(deger)
    if tur not in _TIPLER:
        raise SemaHatasi(f"Bilinmeyen tür: {tur}")
    return isinstance(deger, _TIPLER[tur])


def _json_esit(a: Any, b: Any) -> bool:
    """JSON eşitliği: `1` ile `True` farklıdır, `1` ile `1.0` aynıdır."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_json_esit(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_json_esit(a[k], b[k]) for k in a)
    if _sayi_mi(a) and _sayi_mi(b):
        return bool(a == b)
    return type(a) is type(b) and bool(a == b)


class _Dogrulayici:
    def __init__(self, kok: Mapping[str, Any]) -> None:
        self.kok = kok
        self.anahtarlar: dict[str, Callable[[Any, Any, Mapping[str, Any], str], list[str]]] = {
            "$ref": self._ref,
            "type": self._type,
            "enum": self._enum,
            "const": self._const,
            "pattern": self._pattern,
            "minLength": self._min_length,
            "minimum": self._minimum,
            "required": self._required,
            "dependentRequired": self._dependent_required,
            "properties": self._properties,
            "additionalProperties": self._additional_properties,
            "items": self._items,
            "minItems": self._min_items,
            "uniqueItems": self._unique_items,
            "anyOf": self._any_of,
            "allOf": self._all_of,
            "not": self._not,
            "if": self._if,
        }

    def dogrula(self, deger: Any, sema: Mapping[str, Any], yol: str) -> list[str]:
        hatalar: list[str] = []
        for anahtar, ic in sema.items():
            if anahtar in _ACIKLAMA_ANAHTARLARI or anahtar in ("then", "else"):
                continue
            islev = self.anahtarlar.get(anahtar)
            if islev is None:
                raise SemaHatasi(f"Doğrulayıcının tanımadığı şema anahtarı: {anahtar}")
            hatalar += islev(deger, ic, sema, yol)
        return hatalar

    def _ref(self, deger: Any, ic: str, _s: Mapping[str, Any], yol: str) -> list[str]:
        if not ic.startswith("#/$defs/"):
            raise SemaHatasi(f"Yalnız yerel başvuru okunur: {ic}")
        return self.dogrula(deger, self.kok["$defs"][ic.removeprefix("#/$defs/")], yol)

    def _type(self, deger: Any, ic: str | list[str], _s: Mapping[str, Any], yol: str) -> list[str]:
        turler = [ic] if isinstance(ic, str) else ic
        return [] if any(_tur_uyar(deger, t) for t in turler) else [f"{yol}: tür {turler} olmalı"]

    def _enum(self, deger: Any, ic: list[Any], _s: Mapping[str, Any], yol: str) -> list[str]:
        return [] if any(_json_esit(deger, x) for x in ic) else [f"{yol}: izinli değerlerde yok"]

    def _const(self, deger: Any, ic: Any, _s: Mapping[str, Any], yol: str) -> list[str]:
        return [] if _json_esit(deger, ic) else [f"{yol}: {ic!r} olmalı"]

    def _pattern(self, deger: Any, ic: str, _s: Mapping[str, Any], yol: str) -> list[str]:
        if not isinstance(deger, str) or re.search(ic, deger):
            return []
        return [f"{yol}: biçim uymuyor"]

    def _min_length(self, deger: Any, ic: int, _s: Mapping[str, Any], yol: str) -> list[str]:
        return [f"{yol}: boş olamaz"] if isinstance(deger, str) and len(deger) < ic else []

    def _minimum(self, deger: Any, ic: int, _s: Mapping[str, Any], yol: str) -> list[str]:
        return [f"{yol}: en az {ic} olmalı"] if _sayi_mi(deger) and deger < ic else []

    def _required(self, deger: Any, ic: list[str], _s: Mapping[str, Any], yol: str) -> list[str]:
        if not isinstance(deger, dict):
            return []
        return [f"{yol}.{ad}: zorunlu alan yok" for ad in ic if ad not in deger]

    def _dependent_required(
        self, deger: Any, ic: Mapping[str, list[str]], _s: Mapping[str, Any], yol: str
    ) -> list[str]:
        if not isinstance(deger, dict):
            return []
        return [
            f"{yol}.{gereken}: {ad} varken zorunlu"
            for ad, gerekenler in ic.items()
            if ad in deger
            for gereken in gerekenler
            if gereken not in deger
        ]

    def _properties(
        self, deger: Any, ic: Mapping[str, Any], _s: Mapping[str, Any], yol: str
    ) -> list[str]:
        if not isinstance(deger, dict):
            return []
        hatalar: list[str] = []
        for ad, alt_sema in ic.items():
            if ad in deger:
                hatalar += self.dogrula(deger[ad], alt_sema, f"{yol}.{ad}")
        return hatalar

    def _additional_properties(
        self, deger: Any, ic: bool | Mapping[str, Any], sema: Mapping[str, Any], yol: str
    ) -> list[str]:
        if not isinstance(deger, dict):
            return []
        bilinen = sema.get("properties", {})
        hatalar: list[str] = []
        for ad, alt in deger.items():
            if ad in bilinen:
                continue
            if ic is False:
                hatalar.append(f"{yol}.{ad}: tanımsız alan")
            elif isinstance(ic, Mapping):
                hatalar += self.dogrula(alt, ic, f"{yol}.{ad}")
        return hatalar

    def _items(
        self, deger: Any, ic: Mapping[str, Any], _s: Mapping[str, Any], yol: str
    ) -> list[str]:
        if not isinstance(deger, list):
            return []
        hatalar: list[str] = []
        for sira, alt in enumerate(deger):
            hatalar += self.dogrula(alt, ic, f"{yol}[{sira}]")
        return hatalar

    def _min_items(self, deger: Any, ic: int, _s: Mapping[str, Any], yol: str) -> list[str]:
        if isinstance(deger, list) and len(deger) < ic:
            return [f"{yol}: en az {ic} öğe olmalı"]
        return []

    def _unique_items(self, deger: Any, ic: bool, _s: Mapping[str, Any], yol: str) -> list[str]:
        if not ic or not isinstance(deger, list):
            return []
        for sira, oge in enumerate(deger):
            if any(_json_esit(oge, oteki) for oteki in deger[:sira]):
                return [f"{yol}: yinelenen öğe"]
        return []

    def _any_of(
        self, deger: Any, ic: list[Mapping[str, Any]], _s: Mapping[str, Any], yol: str
    ) -> list[str]:
        if any(not self.dogrula(deger, alt, yol) for alt in ic):
            return []
        return [f"{yol}: izinli biçimlerin hiçbirine uymuyor"]

    def _all_of(
        self, deger: Any, ic: list[Mapping[str, Any]], _s: Mapping[str, Any], yol: str
    ) -> list[str]:
        hatalar: list[str] = []
        for alt in ic:
            hatalar += self.dogrula(deger, alt, yol)
        return hatalar

    def _not(self, deger: Any, ic: Mapping[str, Any], _s: Mapping[str, Any], yol: str) -> list[str]:
        return [] if self.dogrula(deger, ic, yol) else [f"{yol}: bu alan burada olamaz"]

    def _if(
        self, deger: Any, ic: Mapping[str, Any], sema: Mapping[str, Any], yol: str
    ) -> list[str]:
        dal = "then" if not self.dogrula(deger, ic, yol) else "else"
        return self.dogrula(deger, sema[dal], yol) if dal in sema else []


def sema_hatalari(deger: Any, sema: Mapping[str, Any]) -> list[str]:
    """`deger` şemaya uyuyorsa boş liste; uymuyorsa Türkçe hata satırları."""
    return _Dogrulayici(sema).dogrula(deger, sema, "$")
