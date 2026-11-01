"""Rol izinlerinin parametre denetçileri ve uç adları (aile iskeletinden; tasarım §4.4.2, TK13).

Aile iskeletinin kip koruma testlerinden (`test_kip_koruma.py`) taşındı: görevli kipi
1. adımda söküldü, parametre denetçileri (`yalniz_sorgu`, `govdede_yok`) ve uç adı
çözücüsü 2. adımın rol matrisine (`rol_izinleri.py`) kaldı. Matris, `RolMiddleware` ve
URL desenlerini dolaşan "her rol × her uç" koruma testi (`test_rol_koruma`, hücre
başına anlık görüntüyle) 2. adımda gelir.
"""

from __future__ import annotations

from collections import Counter

import pytest
from django.test import RequestFactory
from django.urls import resolve

from apps.okul.rol_izinleri import govdede_yok, uc_adi, utf8_mi, yalniz_sorgu
from apps.okul.tests.api_gezgini import api_desenleri


def test_yalniz_sorgu_denetcisi_bilinmeyen_anahtari_keser() -> None:
    denetci = yalniz_sorgu("q", "limit")

    assert denetci(RequestFactory().get("/api/v1/x/?q=a&limit=5")) is True
    assert denetci(RequestFactory().get("/api/v1/x/")) is True
    assert denetci(RequestFactory().get("/api/v1/x/?q=a&format=json")) is False


@pytest.mark.parametrize(
    ("icerik", "govde", "sorgu", "gecer"),
    [
        ("application/json", b'{"ad": "x"}', "", True),
        ("application/json", b"", "", True),  # boş gövde: görünüm doğrulamayla reddeder
        ("application/json", b'{"ad": "x", "yasak": ""}', "", False),  # değer değil varlık
        ("application/json", b'{"ad": "x"}', "?yasak=1", False),
        ("application/x-www-form-urlencoded", b"ad=x", "", False),
        ("application/json", b"[1, 2]", "", False),
        ("application/json", b"{bozuk", "", False),
        ("application/json; charset=utf-7", b'{"ad":"x","yasak+AF8-":"1"}', "", False),
        ("application/json; charset=latin-1", b'{"ad": "x"}', "", False),
        ("application/json; charset=UTF-8", b'{"ad": "x"}', "", True),
    ],
)
def test_govdede_yok_denetcisi_okuyamadigini_gecirmez(
    icerik: str, govde: bytes, sorgu: str, gecer: bool
) -> None:
    """Denetçi ile görünüm aynı baytları farklı okuyamasın: JSON nesnesi, UTF-8, fail-closed."""
    istek = RequestFactory().generic("POST", "/api/v1/x/" + sorgu, govde, content_type=icerik)

    assert govdede_yok("yasak")(istek) is gecer


def test_karakter_kumesi_adi_esnek_okunur() -> None:
    assert utf8_mi(None) is True
    assert utf8_mi(' "UTF_8" ') is True
    assert utf8_mi("utf8") is True
    assert utf8_mi("windows-1254") is False


def test_ad_alanli_uc_adi_cozulur() -> None:
    assert uc_adi("/api/v1/security/session/") == "security-session"
    assert uc_adi("/api/v1/boyle-bir-uc-yok/") is None


def test_api_uc_adlari_tekildir() -> None:
    """Rol matrisi URL ADIYLA eşleşecek (aile kuralı): aynı adı taşıyan ikinci bir desen
    (kopyala-yapıştır) matristeki izni sessizce devralırdı. Matrisin kanıtı bu tekliğe dayanır."""
    sayac = Counter(resolve(ornek).view_name for _, ornek in api_desenleri())
    assert sorted(ad for ad, adet in sayac.items() if adet > 1) == []
