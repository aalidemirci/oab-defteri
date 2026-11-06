"""`--geri-yukle` kipi testleri (desktop/restore.py).

Birim testleri backend çekirdeğini SAHTE servisle değiştirir: masaüstü testleri
asgari Django ayarlarıyla koşar ve `apps.okul` bu ortamda import edilemez
(bkz. conftest). Gerçek zincir (prepare_django → çekirdek → dosya değişimi)
sondaki yavaş alt-süreç testinde doğrulanır.
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import subprocess
import sys
import types
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from desktop import main as main_mod
from desktop import restore as restore_mod
from desktop.backup_crypto import BOS_YEREL_MANIFESTO, KAPSAM_TAM, MAGIC, Manifesto
from desktop.errors import (
    EXIT_ALREADY_RUNNING,
    EXIT_OK,
    EXIT_RESTORE_FAILED,
    AlreadyRunningError,
)
from desktop.lock import SingleInstanceLock
from desktop.paths import ENV_APP_HOME, AppPaths, resolve_app_paths

REPO_ROOT = Path(__file__).resolve().parents[2]

SQLITE_MAGIC = b"SQLite format 3\x00"


# ------------------------------------------------------------------ argümanlar


def test_read_secret_pencere_disi_platformda_getpass_kullanir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows dışında gizli okuma getpass'e devredilir (yankı korumalı yol).

    Windows dalı msvcrt ile konsoldan doğrudan okur — paketli exe'de stdlib
    getpass, CONIN$ ile değiştirilmiş stdin'i görüp YANKILI fallback'e düşerdi
    (birleşme incelemesi bulgusu); o dal ancak Windows'ta koşar.
    """
    monkeypatch.setattr(restore_mod, "getpass", lambda prompt: "gizli-deger")
    assert restore_mod._read_secret("Parola: ") == "gizli-deger"


def test_geri_yukle_bayragi_uc_bicimde_ayristirilir() -> None:
    parser = main_mod.build_parser()
    assert parser.parse_args([]).geri_yukle is None
    assert parser.parse_args(["--geri-yukle"]).geri_yukle == ""  # dosya yok → seçici
    assert parser.parse_args(["--geri-yukle", "x.odbak"]).geri_yukle == "x.odbak"

    args = parser.parse_args(
        [
            "--geri-yukle",
            "--hesap",
            "yonetici",
            "--parola",
            "p",
            "--kurtarma-anahtari",
            "k",
            "--evet",
        ]
    )
    assert args.geri_yukle == ""
    assert args.hesap == "yonetici"
    assert args.parola == "p"
    assert args.kurtarma_anahtari == "k"
    assert args.evet is True


def test_geri_yukle_kipinde_normal_acilis_kosulmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    cagri: dict[str, Any] = {}

    def sahte(paths: AppPaths, args: Any) -> int:
        cagri["paths"] = paths
        cagri["args"] = args
        return 42

    monkeypatch.setattr(main_mod, "run_restore", sahte)
    monkeypatch.setattr(
        main_mod, "prepare_data", lambda *a: pytest.fail("normal açılış koşulmamalı")
    )

    assert main_mod.run(["--geri-yukle"]) == 42
    assert cagri["args"].geri_yukle == ""
    assert cagri["paths"].root == tmp_path


# ------------------------------------------------------------------ tesisat


def _paths(tmp_path: Path) -> AppPaths:
    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)})
    paths.ensure()
    return paths


def test_program_acikken_geri_yukleme_reddedilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _paths(tmp_path)
    hatalar: list[str] = []
    monkeypatch.setattr(restore_mod, "show_error", lambda baslik, mesaj: hatalar.append(mesaj))
    monkeypatch.setattr(restore_mod, "_restore_flow", lambda *a: pytest.fail("akış koşulmamalı"))
    args = main_mod.build_parser().parse_args(["--geri-yukle"])

    ilk = SingleInstanceLock(paths.lock_path)
    ilk.acquire()
    try:
        kod = restore_mod.run_restore(paths, args)
    finally:
        ilk.release()

    # §4.2 adım 2: ileti tepsiyi anlatmaz (T6); program çarpıyla kapanır.
    assert kod == EXIT_ALREADY_RUNNING
    assert hatalar == ["OAB Defteri açık. Programı kapatıp yeniden deneyin."]


def test_yedekler_en_yeniden_eskiye_listelenir(tmp_path: Path) -> None:
    dizin = tmp_path / "backups"
    dizin.mkdir()
    eski = dizin / "gunluk-2026-08-01.odbak"
    eski.write_bytes(b"x")
    yeni = dizin / "gunluk-2026-08-20.odbak"
    yeni.write_bytes(b"y")
    (dizin / "alakasiz.txt").write_bytes(b"z")  # yalnız .odbak listelenir
    os.utime(eski, (1_000_000, 1_000_000))
    os.utime(yeni, (2_000_000, 2_000_000))

    assert restore_mod.list_backups(dizin) == [yeni, eski]
    assert restore_mod.list_backups(dizin / "yok") == []


def test_yedek_secici_gecersiz_girdiden_sonra_dogru_secer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    yedekler = [tmp_path / "a.odbak", tmp_path / "b.odbak"]
    for yol in yedekler:
        yol.write_bytes(SQLITE_MAGIC)
    girdiler = iter(["9", "2"])
    monkeypatch.setattr("builtins.input", lambda *args: next(girdiler))

    assert restore_mod._pick_backup(yedekler) == yedekler[1]
    assert "Geçersiz seçim" in capsys.readouterr().out


def test_yedek_secici_bos_girdiyle_vazgecer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    yedek = tmp_path / "a.odbak"
    yedek.write_bytes(SQLITE_MAGIC)
    monkeypatch.setattr("builtins.input", lambda *args: "")

    assert restore_mod._pick_backup([yedek]) is None


# ------------------------------------------------------------------ akış (sahte servis)


class SahteServisHatasi(Exception):
    pass


class SahteEkOnayi(SahteServisHatasi):
    """Çekirdeğin `EkOnayiGerekli`'sinin karşılığı (bir `BackupRestoreError`)."""

    def __init__(self, ileti: str, satirlar: list[str]) -> None:
        super().__init__(ileti)
        self.rapor = _sahte_rapor(satirlar)


def _sahte_rapor(satirlar: list[str]) -> Any:
    return SimpleNamespace(metin_satirlari=lambda: satirlar)


def _sahte_servis(
    kayit: dict[str, Any],
    *,
    hata: str | None = None,
    bozuk: list[str] | None = None,
    eksik: list[str] | None = None,
) -> Any:
    """`bozuk` verilirse çekirdek açık bayrak gelene dek `SahteEkOnayi` ile durur."""

    def restore_database(
        yedek: Path,
        db_path: Path,
        *,
        hesap: str | None = None,
        password: str | None = None,
        recovery_key: str | None = None,
        ekler_olmadan_surdur: bool = False,
    ) -> Any:
        kayit.setdefault("bayraklar", []).append(ekler_olmadan_surdur)
        if hata is not None:
            raise SahteServisHatasi(hata)
        if bozuk is not None and not ekler_olmadan_surdur:
            raise SahteEkOnayi("1 ek yedek alınırkenki hâlini tutmuyor.", bozuk)
        kayit["cagri"] = (yedek, db_path, password, recovery_key)
        kayit["hesap"] = hesap
        return SimpleNamespace(
            db_path=db_path,
            old_db_path=None,
            state_written=False,
            dosya_raporu=_sahte_rapor((bozuk or []) + (eksik or [])),
        )

    return SimpleNamespace(
        BackupRestoreError=SahteServisHatasi,
        EkOnayiGerekli=SahteEkOnayi,
        restore_database=restore_database,
    )


@pytest.fixture
def sahte_ortam(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Django hazırlığını ve backend çekirdeğini sahteler; çağrıları kaydeder."""
    kayit: dict[str, Any] = {}
    monkeypatch.setattr(restore_mod, "prepare_django", lambda *a, **k: None)
    monkeypatch.setattr(restore_mod, "_load_service", lambda: _sahte_servis(kayit))
    return kayit


def test_akis_yedegi_hesap_ve_parola_bayragini_servise_iletir(
    tmp_path: Path, sahte_ortam: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _paths(tmp_path)
    yedek = paths.backups / "gunluk-2026-08-29.odbak"
    yedek.write_bytes(MAGIC + b"\x00" * 64)
    args = main_mod.build_parser().parse_args(
        ["--geri-yukle", str(yedek), "--evet", "--hesap", "yonetici", "--parola", "Gizli-Parola-1"]
    )

    kod = restore_mod._restore_flow(paths, args)

    assert kod == EXIT_OK
    hedef_yedek, hedef_db, parola, anahtar = sahte_ortam["cagri"]
    assert hedef_yedek == yedek
    assert hedef_db == paths.db_path
    assert parola == "Gizli-Parola-1" and anahtar is None
    assert sahte_ortam["hesap"] == "yonetici"
    assert "tamamlandı" in capsys.readouterr().out


def test_akis_parola_hesapsiz_verilirse_reddedilir(
    tmp_path: Path, sahte_ortam: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    """Parola bir hesabındır (tasarım §4.4.4): tanıtıcısız parola servise gitmez."""
    paths = _paths(tmp_path)
    yedek = paths.backups / "gunluk.odbak"
    yedek.write_bytes(MAGIC)
    args = main_mod.build_parser().parse_args(
        ["--geri-yukle", str(yedek), "--evet", "--parola", "Gizli-Parola-1"]
    )

    assert restore_mod._restore_flow(paths, args) == EXIT_RESTORE_FAILED
    assert "cagri" not in sahte_ortam
    cikti = capsys.readouterr().out
    assert "--hesap" in cikti
    assert "program yöneticisi hesabının tanıtıcısını" in cikti


def test_akis_yalniz_dosya_adiyla_yedek_klasorunde_arar(
    tmp_path: Path, sahte_ortam: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _paths(tmp_path)
    yedek = paths.backups / "gunluk-2026-08-29.odbak"
    yedek.write_bytes(MAGIC)
    args = main_mod.build_parser().parse_args(
        ["--geri-yukle", yedek.name, "--evet", "--kurtarma-anahtari", "AAAA-BBBB"]
    )

    assert restore_mod._restore_flow(paths, args) == EXIT_OK
    assert sahte_ortam["cagri"][0] == yedek
    assert sahte_ortam["cagri"][3] == "AAAA-BBBB"


def test_akis_sir_verilmezse_her_yedekte_sorar(
    tmp_path: Path,
    sahte_ortam: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Düz yedek dalı yok (tasarım §4.4.7, §13 D29): her geri yükleme sır ister."""
    paths = _paths(tmp_path)
    yedek = paths.backups / "gunluk.odbak"
    yedek.write_bytes(MAGIC + b"\x00" * 64)
    monkeypatch.setattr(restore_mod, "_ask_secret", lambda: (None, None, "KURT-ARMA"))
    args = main_mod.build_parser().parse_args(["--geri-yukle", str(yedek), "--evet"])

    assert restore_mod._restore_flow(paths, args) == EXIT_OK
    assert sahte_ortam["cagri"][2:] == (None, "KURT-ARMA")


def test_sir_istemi_once_hesabi_sonra_parolayi_sorar(monkeypatch: pytest.MonkeyPatch) -> None:
    """İstem parola yolunun yalnız program yöneticisine açık olduğunu baştan söyler (sözlük
    "Yedek"; tasarım §4.4.4): Başlat menüsündeki kısayolun gösterdiği metin budur."""
    istemler: list[str] = []

    def girdi(istem: str = "") -> str:
        istemler.append(istem)
        return next(girdiler)

    girdiler = iter(["  yonetici "])
    monkeypatch.setattr("builtins.input", girdi)
    monkeypatch.setattr(restore_mod, "_read_secret", lambda istem: "Gizli-Parola-1")
    assert restore_mod._ask_secret() == ("yonetici", "Gizli-Parola-1", None)
    assert istemler == [
        "Program yöneticisi hesabının tanıtıcısı (kurtarma anahtarıyla açmak için boş bırakın): "
    ]

    girdiler = iter(["", "KURT-ARMA"])
    assert restore_mod._ask_secret() == (None, None, "KURT-ARMA")


def test_akis_konsolsuz_ve_sirsiz_turkce_hatayla_biter(
    tmp_path: Path, sahte_ortam: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _paths(tmp_path)
    yedek = paths.backups / "gunluk.odbak"
    yedek.write_bytes(MAGIC + b"\x00" * 64)
    hatalar: list[str] = []
    monkeypatch.setattr(restore_mod, "ensure_console", lambda: False)
    monkeypatch.setattr(restore_mod, "show_error", lambda _b, mesaj, **_k: hatalar.append(mesaj))
    args = main_mod.build_parser().parse_args(["--geri-yukle", str(yedek), "--evet"])

    assert restore_mod._restore_flow(paths, args) == EXIT_RESTORE_FAILED
    assert "cagri" not in sahte_ortam
    assert hatalar and "şifrelidir" in hatalar[0]


def test_bulunamayan_yedek_hata_koduyla_biter(
    tmp_path: Path, sahte_ortam: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _paths(tmp_path)
    args = main_mod.build_parser().parse_args(["--geri-yukle", "yok.odbak", "--evet"])

    kod = restore_mod._restore_flow(paths, args)

    assert kod == EXIT_RESTORE_FAILED
    cikti = capsys.readouterr().out
    assert "HATA" in cikti
    assert "bulunamadı" in cikti


def test_servis_hatasi_kullaniciya_mesajla_doner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    paths = _paths(tmp_path)
    yedek = paths.backups / "gunluk.odbak"
    yedek.write_bytes(MAGIC)
    monkeypatch.setattr(restore_mod, "prepare_django", lambda *a, **k: None)
    monkeypatch.setattr(
        restore_mod, "_load_service", lambda: _sahte_servis({}, hata="Yedek anahtarı yanlış.")
    )
    args = main_mod.build_parser().parse_args(
        ["--geri-yukle", str(yedek), "--evet", "--hesap", "yonetici", "--parola", "Gizli-Parola-1"]
    )

    kod = restore_mod._restore_flow(paths, args)

    assert kod == EXIT_RESTORE_FAILED
    assert "Yedek anahtarı yanlış." in capsys.readouterr().out


class SahteYetkisiz(SahteServisHatasi):
    """Çekirdeğin `GeriYuklemeYetkisiz`'inin karşılığı (bir `BackupRestoreError`)."""


def test_yetkisiz_geri_yuklemenin_cikis_kodu_9(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Tasarım §4.4.4 ve §12.B: parolası verilen hesap program yöneticisi değilse çekirdek
    `GeriYuklemeYetkisiz` yükseltir; kip iletiyi olduğu gibi gösterir ve 9 ile çıkar (çıkış
    kodu 9 "geri yükleme başarısız ya da yetkisiz"dir). Gerçek çekirdekle aynı ret
    `test_geri_yukleme_yetkisi.py`'nin konsol kolundadır."""
    ileti = (
        "Yedekten geri yüklemeyi yalnız program yöneticisi hesabıyla ya da kurtarma "
        "anahtarıyla yapabilirsiniz."
    )
    paths = _paths(tmp_path)
    yedek = paths.backups / "gunluk.odbak"
    yedek.write_bytes(MAGIC)

    def reddeden(*_a: Any, **_k: Any) -> Any:
        raise SahteYetkisiz(ileti)

    servis = SimpleNamespace(
        BackupRestoreError=SahteServisHatasi,
        EkOnayiGerekli=SahteEkOnayi,
        restore_database=reddeden,
    )
    monkeypatch.setattr(restore_mod, "prepare_django", lambda *a, **k: None)
    monkeypatch.setattr(restore_mod, "_load_service", lambda: servis)
    args = main_mod.build_parser().parse_args(
        ["--geri-yukle", str(yedek), "--evet", "--hesap", "muhasip", "--parola", "Gizli-Parola-1"]
    )

    kod = restore_mod._restore_flow(paths, args)

    assert kod == EXIT_RESTORE_FAILED == 9
    cikti = capsys.readouterr().out
    assert f"HATA: {ileti}" in cikti
    assert "beklenmeyen" not in cikti


def test_hesap_yardim_metni_program_yoneticisini_anar() -> None:
    """`--hesap` yalnız program yöneticisi hesabının tanıtıcısıdır (tasarım §4.4.4)."""
    eylem = next(
        eylem for eylem in main_mod.build_parser()._actions if "--hesap" in eylem.option_strings
    )
    assert eylem.help is not None and "program yöneticisi hesabının tanıtıcısı" in eylem.help


def test_onay_reddinde_servis_cagrilmaz(
    tmp_path: Path,
    sahte_ortam: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths = _paths(tmp_path)
    yedek = paths.backups / "gunluk.odbak"
    yedek.write_bytes(MAGIC)
    monkeypatch.setattr("builtins.input", lambda *args: "h")
    args = main_mod.build_parser().parse_args(
        ["--geri-yukle", str(yedek), "--hesap", "yonetici", "--parola", "Gizli-Parola-1"]
    )

    kod = restore_mod._restore_flow(paths, args)

    assert kod == EXIT_OK
    assert "cagri" not in sahte_ortam
    cikti = capsys.readouterr().out
    assert "iptal" in cikti
    # `db-onceki` rotasyondadır (tasarım §4.4.7): "silinmez" sözü verilmez.
    assert "14 gün saklanır, sonra silinir" in cikti
    assert "silinmez" not in cikti


# ------------------------------------------------------------------ ekler ve kapsam


_BOZUK_SATIR = "Bozuk · ders yılı · no 9 · 04.11.2026 · 1 KB"
_EKSIK_SATIR = "Eksik · ders yılı · no 4 · 30.10.2026 · 1 KB"


def _ekli_akis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *bayraklar: str,
    **servis: Any,
) -> tuple[AppPaths, argparse.Namespace, dict[str, Any]]:
    paths = _paths(tmp_path)
    yedek = paths.backups / "gunluk.odbak"
    yedek.write_bytes(MAGIC)
    kayit: dict[str, Any] = {}
    monkeypatch.setattr(restore_mod, "prepare_django", lambda *a, **k: None)
    monkeypatch.setattr(restore_mod, "_load_service", lambda: _sahte_servis(kayit, **servis))
    args = main_mod.build_parser().parse_args(
        [
            "--geri-yukle",
            str(yedek),
            "--hesap",
            "yonetici",
            "--parola",
            "Gizli-Parola-1",
            *bayraklar,
        ]
    )
    return paths, args, kayit


def test_bozuk_ekte_liste_yazilir_ikinci_soruya_evet_ekler_olmadan_surer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Kullanıcı kararı 04.11.2026: konsolda ikinci soru; ikinci çağrı açık bayrak taşır."""
    paths, args, kayit = _ekli_akis(tmp_path, monkeypatch, bozuk=[_BOZUK_SATIR])
    sorular: list[str] = []

    def evet(soru: str = "") -> str:
        sorular.append(soru)
        return "e"

    monkeypatch.setattr("builtins.input", evet)

    kod = restore_mod._restore_flow(paths, args)

    assert kod == EXIT_OK
    assert kayit["bayraklar"] == [False, True]
    assert sorular == [
        "Devam edilsin mi? [e/H] ",
        "Kayıtlar bu ekler olmadan geri yüklensin mi? [e/H] ",
    ]
    cikti = capsys.readouterr().out
    assert "1 ek yedek alınırkenki" in cikti
    assert cikti.count(_BOZUK_SATIR) == 2  # sorudan önce ve sonuçta
    assert "tamamlandı" in cikti


def test_ikinci_soruya_hayir_geri_yuklemeyi_iptal_eder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    paths, args, kayit = _ekli_akis(tmp_path, monkeypatch, "--evet", bozuk=[_BOZUK_SATIR])
    monkeypatch.setattr("builtins.input", lambda *a: "h")

    kod = restore_mod._restore_flow(paths, args)

    assert kod == EXIT_OK
    assert kayit["bayraklar"] == [False]
    assert "cagri" not in kayit
    cikti = capsys.readouterr().out
    assert "iptal" in cikti and "tamamlandı" not in cikti


def test_evet_bayragi_ikinci_onay_sayilmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Kullanıcı kararı "ikinci kez açıkça onaylarsa": `--evet` ilk soruyu atlar, ikinciyi değil."""
    paths, args, kayit = _ekli_akis(tmp_path, monkeypatch, "--evet", bozuk=[_BOZUK_SATIR])
    sorular: list[str] = []

    def hayir(soru: str = "") -> str:
        sorular.append(soru)
        return ""

    monkeypatch.setattr("builtins.input", hayir)

    restore_mod._restore_flow(paths, args)

    assert len(sorular) == 1 and "ekler olmadan" in sorular[0]
    assert kayit["bayraklar"] == [False]


def test_konsol_yokken_bozuk_ekte_geri_yukleme_yapilmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, args, kayit = _ekli_akis(tmp_path, monkeypatch, "--evet", bozuk=[_BOZUK_SATIR])
    monkeypatch.setattr(restore_mod, "ensure_console", lambda: False)
    hatalar: list[str] = []
    monkeypatch.setattr(restore_mod, "show_error", lambda _b, ileti, **_k: hatalar.append(ileti))

    kod = restore_mod._restore_flow(paths, args)

    assert kod == EXIT_RESTORE_FAILED
    assert kayit["bayraklar"] == [False]
    assert hatalar and "1 ek" in hatalar[0]


def test_eksik_ek_sormadan_listelenir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    paths, args, kayit = _ekli_akis(tmp_path, monkeypatch, "--evet", eksik=[_EKSIK_SATIR])

    kod = restore_mod._restore_flow(paths, args)

    assert kod == EXIT_OK
    assert kayit["bayraklar"] == [False]
    cikti = capsys.readouterr().out
    assert "Eksik ya da bozuk ekler:" in cikti and _EKSIK_SATIR in cikti


def test_eki_olmayan_geri_yuklemede_liste_basligi_yazilmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    paths, args, _kayit = _ekli_akis(tmp_path, monkeypatch, "--evet")

    restore_mod._restore_flow(paths, args)

    assert "Eksik ya da bozuk ekler" not in capsys.readouterr().out


@pytest.mark.parametrize(
    ("manifesto", "metin"),
    [
        (BOS_YEREL_MANIFESTO, "Kapsam: yalnız kayıtlar; ekler bu bilgisayardan alınır"),
        (Manifesto(KAPSAM_TAM), "Kapsam: kayıtlar, ekler ve üretilen evrak"),
    ],
    ids=["yerel", "tam"],
)
def test_onay_yedegin_kapsamini_soyler(
    manifesto: Manifesto,
    metin: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from desktop.tests.kap_ortak import kap_kur

    paths, args, _kayit = _ekli_akis(tmp_path, monkeypatch, "--evet")
    (paths.backups / "gunluk.odbak").write_bytes(
        kap_kur(b"veritabani", bytes(32), manifesto=manifesto)
    )

    restore_mod._restore_flow(paths, args)

    assert metin in capsys.readouterr().out


def test_kapsami_okunamayan_yedekte_kapsam_satiri_yazilmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Hatayı çekirdek söyler; konsol burada düşmez."""
    paths, args, _kayit = _ekli_akis(tmp_path, monkeypatch, "--evet")

    restore_mod._restore_flow(paths, args)

    assert "Kapsam:" not in capsys.readouterr().out


def _gunluk_metni(kayitlar: list[logging.LogRecord]) -> str:
    return " | ".join(kayit.getMessage() for kayit in kayitlar)


def test_kullanicinin_verdigi_dosya_adi_gunluge_yazilmaz(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """R1: dosyanın adı serbest metindir; ekran gösterir, günlük göstermez. Program adını çekirdek
    yazar."""
    paths, _args, _kayit = _ekli_akis(tmp_path, monkeypatch)
    ad = "Uydurgül Masalcıoğlu.odbak"
    (paths.backups / ad).write_bytes(MAGIC)
    args = main_mod.build_parser().parse_args(
        ["--geri-yukle", ad, "--evet", "--hesap", "yonetici", "--parola", "Gizli-Parola-1"]
    )

    assert restore_mod._restore_flow(paths, args) == EXIT_OK

    assert "Masalcıoğlu" in capsys.readouterr().out
    assert "Masalcıoğlu" not in _gunluk_metni(od_gunlugu)


def test_bulunamayan_dosyanin_adi_gunluge_yazilmaz(
    tmp_path: Path,
    sahte_ortam: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
    od_gunlugu: list[logging.LogRecord],
) -> None:
    args = main_mod.build_parser().parse_args(["--geri-yukle", "Masalcıoğlu.odbak", "--evet"])

    assert restore_mod._restore_flow(_paths(tmp_path), args) == EXIT_RESTORE_FAILED

    assert "Masalcıoğlu" in capsys.readouterr().out
    metin = _gunluk_metni(od_gunlugu)
    assert "bulunamadı" in metin and "Masalcıoğlu" not in metin


def test_konsolsuz_kolda_bulunamayan_dosyanin_adi_gunluge_yazilmaz(
    tmp_path: Path,
    sahte_ortam: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """Pencereli pakette konsol açılamazsa ileti kutusuna düşer; kutu da günlüğe yazar (R1)."""
    monkeypatch.setattr(restore_mod, "ensure_console", lambda: False)
    monkeypatch.setattr("desktop.dialogs._run_dialog_command", lambda _argv: True)
    args = main_mod.build_parser().parse_args(["--geri-yukle", "Masalcıoğlu.odbak", "--evet"])

    assert restore_mod._restore_flow(_paths(tmp_path), args) == EXIT_RESTORE_FAILED

    metin = _gunluk_metni(od_gunlugu)
    assert "bulunamadı" in metin and "Masalcıoğlu" not in metin


def test_yedek_klasoru_bosken_yol_gunluge_yazilmaz_konsolda_gorunur(
    tmp_path: Path,
    sahte_ortam: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """Yol işletim sistemi hesabının adını taşır; günlük destek için paylaşılabilir (uydurma ad)."""
    paths = _paths(tmp_path / "Uydurgül Masalcıoğlu")
    args = main_mod.build_parser().parse_args(["--geri-yukle"])

    assert restore_mod._restore_flow(paths, args) == EXIT_RESTORE_FAILED

    assert str(paths.backups) in capsys.readouterr().out
    metin = _gunluk_metni(od_gunlugu)
    assert "geri yüklenebilir dosya yok" in metin and "Masalcıoğlu" not in metin


# ------------------------------------------------------------------ yarım işlerin artıkları


@pytest.fixture
def artik_kancasi(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """`apps.okul.masaustu_kanca` yerine temizliği ve taramayı kaydeden sahte modül."""
    sira: list[Any] = []
    sahte = types.ModuleType("apps.okul.masaustu_kanca")
    sahte.artiklari_temizle = lambda *a: sira.append(("artik", *a))  # type: ignore[attr-defined]
    sahte.yetim_taramasi = lambda *a: sira.append(("tarama", *a))  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "apps.okul.masaustu_kanca", sahte)
    return sira


def test_geri_yukleme_kipi_artiklari_kilit_altinda_siler_tarama_yapmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artik_kancasi: list[Any]
) -> None:
    """Plan yalnız taramayı dışlar. Bozuk veritabanında açılış temizliği koşmaz, yeniden deneme
    kalan hazırlık dizininin yanına ikincisini açardı."""
    paths, args, kayit = _ekli_akis(tmp_path, monkeypatch, "--evet")
    asil = restore_mod._load_service

    def servis() -> Any:
        artik_kancasi.append(("servis",))
        return asil()

    monkeypatch.setattr(restore_mod, "_load_service", servis)
    kilitli: list[bool] = []
    temizle = sys.modules["apps.okul.masaustu_kanca"].artiklari_temizle

    def kilit_denetler(*a: Any) -> None:
        with pytest.raises(AlreadyRunningError):
            SingleInstanceLock(paths.lock_path).acquire()
        kilitli.append(True)
        temizle(*a)

    monkeypatch.setattr(
        sys.modules["apps.okul.masaustu_kanca"], "artiklari_temizle", kilit_denetler
    )

    assert restore_mod.run_restore(paths, args) == EXIT_OK

    assert artik_kancasi == [
        ("servis",),
        ("artik", paths.db_path, paths.backups, paths.dosya_deposu),
    ]
    assert kilitli == [True]
    assert kayit["bayraklar"] == [False]


def test_artik_temizligi_duserse_geri_yukleme_surer_yol_gunluge_yazilmaz(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artik_kancasi: list[Any],
    od_gunlugu: list[logging.LogRecord],
) -> None:
    paths, args, kayit = _ekli_akis(tmp_path, monkeypatch, "--evet")

    def patla(*_a: Any) -> None:
        raise OSError(f"silinemedi: {paths.backups}")

    monkeypatch.setattr(sys.modules["apps.okul.masaustu_kanca"], "artiklari_temizle", patla)

    assert restore_mod._restore_flow(paths, args) == EXIT_OK

    assert kayit["bayraklar"] == [False]
    metin = _gunluk_metni(od_gunlugu)
    assert "artıkları silinemedi (OSError)" in metin and str(paths.backups) not in metin


def test_backend_yoksa_artik_temizligi_sessizce_atlanir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "apps.okul.masaustu_kanca", None)

    restore_mod._artiklari_temizle(_paths(tmp_path))  # ImportError yutulur


# ------------------------------------------------------------------ uçtan uca


_E2E_KURTARMA = "ABCD-EFGH-JKLM-NPQR-STUV-WXYZ-2345-6723"


def _gomulu_durum(dek: bytes, kurtarma: str) -> bytes:
    """TK10 yedek başlığı: yalnız kurtarma bölümü (`backup_crypto.recovery_header_from_state`).

    Masaüstü testleri backend'i import edemediği için sarmal burada ucuz Argon2
    profiliyle elle kurulur; anahtar normalleştirilmiş biçimiyle (tiresiz) sarılır,
    çekirdek de öyle açar (`app_password.normalize_recovery_key`).
    """
    import base64
    import json

    from argon2.low_level import Type, hash_secret_raw
    from cryptography.fernet import Fernet

    kdf = {"time_cost": 1, "memory_cost": 8, "parallelism": 1}
    tuz = os.urandom(16)
    sarmalama = hash_secret_raw(
        secret=kurtarma.replace("-", "").encode("utf-8"),
        salt=tuz,
        time_cost=1,
        memory_cost=8,
        parallelism=1,
        hash_len=32,
        type=Type.ID,
    )
    sarmal = Fernet(base64.urlsafe_b64encode(sarmalama)).encrypt(dek).decode("ascii")
    baslik = {
        "surum": 2,
        "kdf": kdf,
        "kurtarma": {
            "no": 1,
            "tarih": "2026-08-29",
            "salt": base64.b64encode(tuz).decode("ascii"),
            "sarmal": sarmal,
        },
    }
    return json.dumps(baslik).encode("utf-8")


@pytest.mark.slow
def test_geri_yukleme_kipi_gercek_akista_calisir(tmp_path: Path) -> None:
    """Gerçek zincir: kilit → prepare_django → çekirdek → dosya değişimi (pencere YOK).

    Veri klasöründe `guvenlik.json` YOKTUR (tehdit 8, güvenlik dosyası kayıp senaryosu):
    geri yükleme dosyayı yedeğin kurtarma başlığından yeniden yazar.
    """
    from desktop.tests.kap_ortak import kap_kur

    veri = tmp_path / "data"
    veri.mkdir(parents=True)
    yedek_dizini = tmp_path / "backups"
    yedek_dizini.mkdir()

    def sqlite_yaz(yol: Path, isaret: str) -> None:
        with closing(sqlite3.connect(yol)) as baglanti:
            baglanti.execute("CREATE TABLE kayit (deger TEXT)")
            baglanti.execute("INSERT INTO kayit VALUES (?)", (isaret,))
            baglanti.commit()

    sqlite_yaz(veri / "db.sqlite3", "eski-icerik")
    (veri / "db.sqlite3-wal").write_bytes(b"wal-kalintisi")
    (veri / "surum.json").write_text("{}", encoding="utf-8")
    # Kesilen bir denemenin artıkları silinir, satırsız dosyaya dokunulmaz (tarama bu kipte yok).
    hazirlik = veri / "dosyalar" / f".hazirlik-{'ab' * 16}"
    hazirlik.mkdir(parents=True)
    (hazirlik / ("cd" * 16)).write_bytes(b"yarim kap")
    yukleme = yedek_dizini / f".yukleme-{'ab' * 16}.tmp"
    yukleme.write_bytes(b"yarim yukleme")
    satirsiz = veri / "dosyalar" / ("ef" * 16)
    satirsiz.write_bytes(b"satirsiz")
    kaynak = tmp_path / "yeni.sqlite3"
    sqlite_yaz(kaynak, "yeni-icerik")
    dek = os.urandom(32)
    baslik = _gomulu_durum(dek, _E2E_KURTARMA)
    yedek = yedek_dizini / "gunluk-2026-08-29.odbak"
    yedek.write_bytes(kap_kur(kaynak.read_bytes(), dek, baslik=baslik))

    sonuc = subprocess.run(  # noqa: S603 — sabit argümanlar, kabuk yok
        [
            sys.executable,
            "-m",
            "desktop.main",
            "--data-dir",
            str(tmp_path),
            "--geri-yukle",
            str(yedek),
            "--evet",
            "--kurtarma-anahtari",
            _E2E_KURTARMA,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert sonuc.returncode == EXIT_OK, sonuc.stderr
    assert b"yeni-icerik" in (veri / "db.sqlite3").read_bytes()
    assert not hazirlik.exists() and not yukleme.exists()
    assert satirsiz.read_bytes() == b"satirsiz"
    onceki = list(veri.glob("db-onceki-*.sqlite3"))
    assert len(onceki) == 1
    assert b"eski-icerik" in onceki[0].read_bytes()
    assert (onceki[0].with_name(onceki[0].name + "-wal")).is_file()
    assert not (veri / "db.sqlite3-wal").exists()
    assert not (veri / "surum.json").exists()
    # Kayıp güvenlik dosyası yedeğin kurtarma başlığından YALNIZ kurtarma bölümüyle yazıldı
    # (TK10; hesaplar boş, anahtar kullanıldığı için saklandı damgası dolu); yedek anahtarı
    # eşitlendi.
    import json

    yazilan = json.loads((veri / "guvenlik.json").read_text(encoding="utf-8"))
    beklenen = json.loads(baslik)
    assert yazilan["hesaplar"] == [] and yazilan["surum"] == 2
    assert yazilan["kurtarma"]["sarmal"] == beklenen["kurtarma"]["sarmal"]
    assert yazilan["kurtarma"]["dogrulandi"]
    assert (veri / "yedekleme.json").is_file()
    # Yedeğin kendisine dokunulmaz.
    assert yedek.is_file()
