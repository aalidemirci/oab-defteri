"""Hata iletisi testleri — pencere açılamadığında kullanıcıya ulaşan tek yol."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from desktop.dialogs import show_error
from desktop.logging_setup import LOG_FILE_NAME, configure_logging


def test_hata_her_durumda_gunluge_yazilir(tmp_path: Path) -> None:
    configure_logging(tmp_path)

    show_error("Başlık", "Veri dosyası bozuk.", platform="linux", runner=lambda argv: False)
    logging.shutdown()

    assert "Veri dosyası bozuk." in (tmp_path / LOG_FILE_NAME).read_text(encoding="utf-8")


def test_linux_te_zenity_ile_gosterilir(tmp_path: Path) -> None:
    configure_logging(tmp_path)
    cagrilar: list[list[str]] = []

    def kaydet(argv: list[str]) -> bool:
        cagrilar.append(argv)
        return True

    show_error("Başlık", "Veri dosyası bozuk.", platform="linux", runner=kaydet)

    assert cagrilar
    assert any("Veri dosyası bozuk." in parca for parca in cagrilar[0])


def test_gorsel_ileti_basarisizsa_patlamaz(tmp_path: Path) -> None:
    configure_logging(tmp_path)

    def patla(argv: list[str]) -> bool:
        raise OSError("zenity yok")

    show_error("Başlık", "Mesaj", platform="linux", runner=patla)


def test_windows_ta_mesaj_kutusu_kullanilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_logging(tmp_path)
    import desktop.dialogs as dialogs_mod

    cagrilar: list[tuple[str, str]] = []

    def kutu(title: str, message: str) -> bool:
        cagrilar.append((title, message))
        return True

    monkeypatch.setattr(dialogs_mod, "_show_windows_message_box", kutu)

    show_error("Başlık", "Mesaj", platform="win32", runner=lambda argv: False)

    assert cagrilar == [("Başlık", "Mesaj")]


def test_gorsel_ileti_denenmeden_once_gunluk_yazilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Diyalog patlasa bile iz kalmalı → önce günlük, sonra ileti."""
    configure_logging(tmp_path)
    sira: list[str] = []
    import desktop.dialogs as dialogs_mod

    gercek_logger = dialogs_mod.logger

    class _Izleyici:
        def error(self, *args: Any, **kwargs: Any) -> None:
            sira.append("gunluk")
            gercek_logger.error(*args, **kwargs)

    monkeypatch.setattr(dialogs_mod, "logger", _Izleyici())

    def kaydet(argv: list[str]) -> bool:
        sira.append("ileti")
        return True

    show_error("Başlık", "Mesaj", platform="linux", runner=kaydet)

    assert sira == ["gunluk", "ileti"]


def test_gunluk_verilirse_ileti_gunluge_yazilmaz_kutuda_gosterilir(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """R1: ileti serbest ad ya da yol taşıyorsa günlüğe adsız hâli yazılır."""
    gorulen: list[list[str]] = []

    def kutu(argv: list[str]) -> bool:
        gorulen.append(argv)
        return True

    show_error(
        "Geri yükleme başarısız",
        "Yedek dosyası bulunamadı: Uydurgül Masalcıoğlu.odbak",
        gunluk="Yedek dosyası bulunamadı.",
        platform="linux",
        runner=kutu,
    )

    metin = " | ".join(kayit.getMessage() for kayit in od_gunlugu)
    assert "Yedek dosyası bulunamadı." in metin and "Masalcıoğlu" not in metin
    assert "Masalcıoğlu" in gorulen[0][-1]


def test_ileti_penceresi_temiz_ortamla_acilir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Saha bulgusu K-P2 (Pardus 25, 12.11.2026): zenity paketin `LD_LIBRARY_PATH`'ini devralıp
    gömülü bullseye cairo'suna bağlanıyor, "undefined symbol: cairo_set_hairline" ile çöküyordu;
    açılış hatası iletisi hiç görünmüyordu. Süreç `temiz_ortam()` ile başlar (`desktop/dis_surec.py`)."""
    import desktop.dialogs as dialogs_mod

    cagrilar: list[tuple[list[str], dict[str, Any]]] = []

    def calistir(argv: list[str], **anahtarlar: Any) -> None:
        cagrilar.append((argv, anahtarlar))

    monkeypatch.setattr(shutil, "which", lambda ad: f"/usr/bin/{ad}")
    monkeypatch.setattr(subprocess, "run", calistir)
    monkeypatch.setattr(dialogs_mod, "temiz_ortam", lambda: {"TEMIZ": "1"})

    assert dialogs_mod._run_dialog_command(["zenity", "--error", "--text=Uydurma"]) is True

    ((argv, anahtarlar),) = cagrilar
    assert argv == ["/usr/bin/zenity", "--error", "--text=Uydurma"]
    assert anahtarlar["env"] == {"TEMIZ": "1"}
