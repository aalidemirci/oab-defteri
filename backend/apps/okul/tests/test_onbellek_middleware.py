"""API yanıtları önbelleğe yazılmaz (tasarım §4.3 tehdit 24; `apps.okul.onbellek_middleware`).

Windows sınamasında (07.11.2026) pencere bileşeninin disk önbelleğinde hesap ve öğrenci listeleri
adlarla birlikte bulundu. Her `/api/` yanıtı `Cache-Control: no-store` taşımalıdır; kapıların
kendi yanıtları da (423, 503, 403) dahil.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from desktop.server import HEALTH_PATH
from django.conf import settings
from django.http import FileResponse, HttpResponse, HttpResponseBase, JsonResponse
from django.test import Client, RequestFactory

from apps.okul.onbellek_middleware import ApiNoStoreMiddleware

KATMAN = "apps.okul.onbellek_middleware.ApiNoStoreMiddleware"


def _direktifler(yanit: HttpResponseBase) -> list[str]:
    deger = yanit.get("Cache-Control", "") or ""
    return [parca.strip() for parca in deger.split(",") if parca.strip()]


def _sar(yanit: HttpResponseBase, yol: str) -> HttpResponseBase:
    return ApiNoStoreMiddleware(lambda _istek: yanit)(RequestFactory().get(yol))  # type: ignore[arg-type,return-value]


def test_kisi_verisi_tasiyan_api_yaniti_onbellege_yazilmaz() -> None:
    yanit = _sar(JsonResponse({"full_name": "Uydurma Kişi"}), "/api/v1/accounts/")

    assert "no-store" in _direktifler(yanit)


@pytest.mark.parametrize("durum", [200, 201, 400, 403, 404, 409, 423, 503])
def test_her_durum_kodunda_no_store(durum: int) -> None:
    assert "no-store" in _direktifler(_sar(HttpResponse(status=durum), "/api/v1/personnel/"))


def test_gorunumun_basligi_korunur_no_store_eklenir() -> None:
    yanit = HttpResponse()
    yanit["Cache-Control"] = "private, max-age=60"

    assert set(_direktifler(_sar(yanit, "/api/v1/personnel/"))) == {
        "private",
        "max-age=60",
        "no-store",
    }


def test_gorunum_zaten_no_store_dediyse_yinelenmez() -> None:
    """`views_yedek.py`, `views_hesaplar.py` ve `views.py`'deki dosya yanıtları başlığı kendi koyar."""
    yanit = HttpResponse()
    yanit["Cache-Control"] = "no-store"

    assert _direktifler(_sar(yanit, "/api/v1/backups/")) == ["no-store"]


def test_dosya_yaniti_da_onbellege_yazilmaz(tmp_path: Path) -> None:
    dosya = tmp_path / "rapor.pdf"
    dosya.write_bytes(b"%PDF-1.7")

    with dosya.open("rb") as akim:
        yanit = _sar(FileResponse(akim), "/api/v1/documents/1/pdf/")

    assert "no-store" in _direktifler(yanit)


@pytest.mark.parametrize("yol", ["/", "/kisiler", "/assets/index-abc123.js", "/app-logo.png"])
def test_api_disi_yollara_dokunulmaz(yol: str) -> None:
    """Arayüzün kendi dosyaları kişi verisi taşımaz (modül başlığı)."""
    assert _sar(HttpResponse(), yol).get("Cache-Control") is None


@pytest.mark.django_db
def test_gercek_zincirde_saglik_yolu_onbellege_yazilmaz() -> None:
    yanit = Client().get(HEALTH_PATH)

    assert yanit.status_code == 200
    assert "no-store" in _direktifler(yanit)


@pytest.mark.django_db
def test_gercek_zincirde_kilit_kapisinin_yaniti_da_onbellege_yazilmaz(kilitli: Path) -> None:
    yanit = Client().get("/api/v1/personnel/")

    assert yanit.status_code == 423
    assert "no-store" in _direktifler(yanit)


@pytest.mark.django_db
def test_gercek_zincirde_hesap_listesi_onbellege_yazilmaz() -> None:
    yanit = Client().get("/api/v1/security/accounts/")

    assert yanit.status_code == 200
    assert "no-store" in _direktifler(yanit)


def test_katman_kapilardan_ve_whitenoiseden_once_durur() -> None:
    """Kapıların kesip döndürdüğü yanıt da bu katmandan geçsin (tasarım §4.4.3)."""
    zincir = list(settings.MIDDLEWARE)
    sira = zincir.index(KATMAN)
    for sonraki in (
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.middleware.common.CommonMiddleware",
        "apps.okul.restart_gate.RestartRequiredMiddleware",
        "apps.okul.lock_middleware.AppLockMiddleware",
        "apps.okul.rol_middleware.RolMiddleware",
    ):
        assert sira < zincir.index(sonraki), sonraki
