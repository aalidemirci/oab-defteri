"""`/api/` URL desenlerinin gezgini — koruma testlerinin ortak yardımcısı.

Uç listesi ELLE TUTULMAZ: URL desenleri çalışma anında dolaşılır, dönüştürücüler
örnek değerle doldurulur. Aile iskeletinde bu gezgin ağ kataloğunun koruma
testlerindeydi (`katalog/tests/test_koruma.py`); katalog sökülünce kip koruma
testleri onu kaybetmesin diye buraya taşındı (tasarım §12.B, F1a-2).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from django.urls import URLPattern, URLResolver, get_resolver
from django.urls.converters import (
    IntConverter,
    PathConverter,
    SlugConverter,
    StringConverter,
    UUIDConverter,
)
from django.urls.resolvers import RegexPattern, RoutePattern

#: `desktop/server.py::HEALTH_PATH` ile aynı yol; masaüstü sağlık denetimi bunu yoklar.
SAGLIK_YOLU = "/api/v1/setup/status/"

_ORNEK_UUID = "12345678-1234-5678-1234-567812345678"
_DONUSTURUCU_ORNEKLERI: dict[type[Any], str] = {
    IntConverter: "1",
    StringConverter: "x",
    SlugConverter: "x",
    PathConverter: "x",
    UUIDConverter: _ORNEK_UUID,
}
# `re_path` grupları için sırayla denenen adaylar (ör. DRF yönlendiricisinin
# `(?P<pk>[^/.]+)` ve `(?P<format>[a-z0-9]+)` grupları).
_REGEX_ADAYLARI = ("1", "x", _ORNEK_UUID, "json")

_ROUTE_PARAMETRESI = re.compile(r"<(?:(?P<donusturucu>[^>:]+):)?(?P<ad>[^>]+)>")
_ADLI_GRUP = re.compile(r"\(\?P<(?P<ad>\w+)>(?P<govde>(?:[^()\\]|\\.)*)\)")
# Kaçırılmamış düzenli ifade işleci kalırsa örnek yol güvenilir değildir.
_KACIRILMAMIS_ISLEC = re.compile(r"(?<!\\)[.()\[\]{}*+?|^$]")


def _route_ornegi(desen: RoutePattern) -> str:
    """`path()` deseninin örnek yolu: her dönüştürücü bilinen bir değer alır."""
    donusturuculer: dict[str, Any] = dict(desen.converters)

    def degistir(eslesme: re.Match[str]) -> str:
        donusturucu = donusturuculer[eslesme["ad"]]
        ornek = _DONUSTURUCU_ORNEKLERI.get(type(donusturucu))
        if ornek is None:
            raise AssertionError(
                f"{type(donusturucu).__name__} için örnek değer yok ({desen}); "
                "_DONUSTURUCU_ORNEKLERI'ne ekleyin."
            )
        return ornek

    return _ROUTE_PARAMETRESI.sub(degistir, str(desen))


def _regex_ornegi(regex: str) -> str:
    """`re_path()` deseninin örnek yolu (fail-closed: çözemediği desende düşer)."""

    def grup(eslesme: re.Match[str]) -> str:
        for aday in _REGEX_ADAYLARI:
            if re.fullmatch(eslesme["govde"], aday):
                return aday
        raise AssertionError(f"'{eslesme['ad']}' grubu için örnek değer yok: {regex!r}")

    govde = regex.removeprefix("^").removesuffix("$").removesuffix(r"\Z")
    govde = govde.replace("/?", "/")  # isteğe bağlı eğik çizgi örnekte bulunur
    govde = _ADLI_GRUP.sub(grup, govde)
    if _KACIRILMAMIS_ISLEC.search(govde):
        raise AssertionError(f"örnek yol üretilemedi: {regex!r} (üreteci genişletin)")
    return re.sub(r"\\(.)", r"\1", govde)


def _parca_ornegi(desen: object) -> str:
    if isinstance(desen, RoutePattern):
        return _route_ornegi(desen)
    if isinstance(desen, RegexPattern):
        return _regex_ornegi(str(desen))
    raise AssertionError(f"bilinmeyen desen türü: {type(desen).__name__} ({desen})")


def _rota_birlestir(on: str, parca: str) -> str:
    """Django'nun `URLResolver._join_route` kuralı: ikinci parçanın `^`'i düşer."""
    return parca if not on else on + parca.removeprefix("^")


def api_desenleri() -> list[tuple[str, str]]:
    """`api/` altındaki her uç için (Django rotası, örnek yol) çiftleri."""
    sonuc: list[tuple[str, str]] = []

    def gez(desenler: Sequence[URLPattern | URLResolver], rota: str, zincir: list[object]) -> None:
        for desen in desenler:
            tam = _rota_birlestir(rota, str(desen.pattern))
            yeni_zincir = [*zincir, desen.pattern]
            if isinstance(desen, URLResolver):
                gez(desen.url_patterns, tam, yeni_zincir)
            elif tam.removeprefix("^").startswith("api/"):
                ornek = "/" + "".join(_parca_ornegi(parca) for parca in yeni_zincir)
                sonuc.append((tam, ornek))

    gez(get_resolver().url_patterns, "", [])
    return sonuc
