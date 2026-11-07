"""Göç hatasının yol tarifi (sözlük §4.2): Başlat menüsü kısayolu yalnız Windows'ta vardır."""

from __future__ import annotations

import sys
from typing import Any

import pytest

from desktop.django_bootstrap import run_migrations
from desktop.errors import MigrationError

_WINDOWS_IPUCU = (
    "Yedek klasöründeki en son 'pre-migrate-*' veya günlük yedeği geri yüklemek için Başlat "
    "menüsündeki 'OAB Defteri — Yedekten Geri Yükle' kısayolunu (veya 'oab-defteri --geri-yukle' "
    "komutunu) çalıştırıp programı yeniden açın."
)
_PARDUS_IPUCU = (
    "Yedek klasöründeki en son 'pre-migrate-*' veya günlük yedeği geri yüklemek için uçbirimde "
    "oab-defteri --geri-yukle komutunu çalıştırıp programı yeniden açın."
)


def _goc_hatasi(monkeypatch: pytest.MonkeyPatch, **secenekler: Any) -> MigrationError:
    def patlat(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("göç düştü")

    monkeypatch.setattr("django.core.management.call_command", patlat)
    with pytest.raises(MigrationError) as hata:
        run_migrations(**secenekler)
    return hata.value


def test_windows_metni_kisayolu_ve_komutu_soyler(monkeypatch: pytest.MonkeyPatch) -> None:
    hata = _goc_hatasi(monkeypatch, platform="win32")

    assert hata.message == "Veritabanı güncellenemedi; program veriyi korumak için açılmadı."
    assert hata.hint == _WINDOWS_IPUCU


def test_pardus_metni_kisayolu_anmaz_komutu_soyler(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _goc_hatasi(monkeypatch, platform="linux").hint == _PARDUS_IPUCU


@pytest.mark.parametrize(
    ("sistem", "beklenen"),
    [("win32", _WINDOWS_IPUCU), ("linux", _PARDUS_IPUCU)],
    ids=["windows", "pardus"],
)
def test_platform_verilmezse_calisilan_sistemin_metni_yazilir(
    monkeypatch: pytest.MonkeyPatch, sistem: str, beklenen: str
) -> None:
    """Üretim `platform` vermez (`desktop.main`); testlerin açık verdiği değer bu yolu sınamaz."""
    monkeypatch.setattr(sys, "platform", sistem)

    assert _goc_hatasi(monkeypatch).hint == beklenen
