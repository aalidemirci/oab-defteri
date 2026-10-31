"""Son oturum kartı (T15; tasarım §4.2 adım 3, §13 D4).

Kartın okuyucusu ve süreç başlangıç damgası okul çekirdeğindedir (aile
iskeletinde kütüphane uygulamasındaydı; uygulama sökülünce uyarı sessizce
kaybolurdu). Uç ORM'e dokunmaz.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path

import pytest
from desktop.clean_shutdown import (
    ENV_PREVIOUS_SESSION,
    PreviousSession,
    consume_marker,
    publish,
    write_marker,
)
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul import son_oturum

URL = "/api/v1/dashboard/last-session/"


@pytest.fixture(autouse=True)
def _onay_sifirla(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv(ENV_PREVIOUS_SESSION, raising=False)
    son_oturum._reset_for_tests()
    yield
    son_oturum._reset_for_tests()


def test_isaret_yoksa_kart_gorunur(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Önceki oturum veritabanı bıraktı ama temiz kapanış işareti yazmadı (elektrik kesintisi)."""
    veri = tmp_path / "data"
    veri.mkdir()
    (veri / "db.sqlite3").write_bytes(b"SQLite format 3\x00")
    ortam: dict[str, str] = {}

    publish(consume_marker(veri, veri / "db.sqlite3"), ortam)
    monkeypatch.setenv(ENV_PREVIOUS_SESSION, ortam[ENV_PREVIOUS_SESSION])

    yanit = APIClient().get(URL)

    assert yanit.status_code == 200
    assert yanit.json()["unexpected_shutdown"] is True


def test_isaret_varsa_kart_gorunmez(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    veri = tmp_path / "data"
    veri.mkdir()
    (veri / "db.sqlite3").write_bytes(b"SQLite format 3\x00")
    write_marker(veri, "2026.11.0-alpha.1")
    ortam: dict[str, str] = {}

    publish(consume_marker(veri, veri / "db.sqlite3"), ortam)
    monkeypatch.setenv(ENV_PREVIOUS_SESSION, ortam[ENV_PREVIOUS_SESSION])

    assert APIClient().get(URL).json()["unexpected_shutdown"] is False


@pytest.mark.parametrize("deger", [PreviousSession.FIRST_RUN.value, "", "tanimsiz"])
def test_ilk_acilista_ve_bilinmeyen_durumda_kart_gorunmez(
    monkeypatch: pytest.MonkeyPatch, deger: str
) -> None:
    monkeypatch.setenv(ENV_PREVIOUS_SESSION, deger)

    assert son_oturum.kart_gosterilsin() is False


def test_degisken_yoksa_kart_gorunmez() -> None:
    """Geliştirme sunucusu ve testler: masaüstü kabuğu yok, alarm yok."""
    assert APIClient().get(URL).json()["unexpected_shutdown"] is False


def test_kontrol_ettim_karti_bu_oturum_icin_kapatir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_PREVIOUS_SESSION, PreviousSession.UNEXPECTED.value)
    istemci = APIClient()
    assert istemci.get(URL).json()["unexpected_shutdown"] is True

    yanit = istemci.post(URL, {}, format="json")

    assert yanit.status_code == 200
    assert yanit.json()["unexpected_shutdown"] is False
    assert istemci.get(URL).json()["unexpected_shutdown"] is False


def test_surec_baslangici_hazirlikta_bir_kez_isaretlenir() -> None:
    """`OkulConfig.ready` damgayı koydu; sonraki çağrılar damgayı değiştirmez."""
    ilk = son_oturum.process_started_at()

    assert ilk <= timezone.now()
    assert son_oturum.mark_process_start(ilk + timedelta(hours=1)) == ilk
    assert APIClient().get(URL).json()["process_started_at"] == ilk.isoformat()
