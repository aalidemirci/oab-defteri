"""Açılış ve kapanış orkestrasyonu testleri (tasarım §4.2 açılış ve kapanış sırası).

Buradaki testler Django'yu çalıştırmaz — sıra ve karar mantığı sahte adımlarla
doğrulanır. Gerçek uçtan uca açılış (migrate + waitress + belirteç koruması)
`test_autotest_kipi_gercek_acilisi_dogrular` içinde ALT SÜREÇ olarak koşar.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import threading
import time
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from desktop import main as main_mod
from desktop import qt_kurulum as qt_kurulum_mod
from desktop import restore as restore_mod
from desktop.clean_shutdown import ENV_PREVIOUS_SESSION, MARKER_FILE_NAME
from desktop.django_bootstrap import is_parcacigi_baglantisiyla, wal_checkpoint
from desktop.errors import (
    EXIT_ALREADY_RUNNING,
    EXIT_DATABASE_CORRUPT,
    EXIT_OK,
    EXIT_WEBVIEW_UNAVAILABLE,
    DatabaseCorruptError,
    WebViewUnavailableError,
)
from desktop.instance_channel import open_channel
from desktop.lock import SingleInstanceLock
from desktop.paths import ENV_APP_HOME, resolve_app_paths

REPO_ROOT = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------------ argümanlar


def test_autotest_bayragi_varsayilan_kapali() -> None:
    assert main_mod.build_parser().parse_args([]).autotest is False
    assert main_mod.build_parser().parse_args(["--autotest"]).autotest is True


def test_veri_dizini_bayragi_yerlesimi_gecersiz_kilar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_APP_HOME, raising=False)

    paths = main_mod.resolve_paths(
        main_mod.build_parser().parse_args(["--data-dir", str(tmp_path)])
    )

    assert paths.root == tmp_path


# ----------------------------------------------------------------- açılış sırası


@pytest.fixture
def izlenen_adimlar(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """`_prepare_data` içindeki tüm adımları kayda geçirir (Django çalışmaz)."""
    sira: list[str] = []

    def kaydet(ad: str, sonuc: Any = None) -> Any:
        def sahte(*args: Any, **kwargs: Any) -> Any:
            sira.append(ad)
            return sonuc

        return sahte

    monkeypatch.setattr(main_mod, "ensure_stamp_compatible", kaydet("surum-damgasi"))
    monkeypatch.setattr(main_mod, "check_database_integrity", kaydet("butunluk"))
    monkeypatch.setattr(
        main_mod, "daily_backup", kaydet("gunluk-yedek", Path("gunluk-2026-09-22.odbak"))
    )
    monkeypatch.setattr(main_mod, "rotate_backups", kaydet("rotasyon", []))
    monkeypatch.setattr(main_mod, "prepare_django", kaydet("django-hazirla"))
    monkeypatch.setattr(main_mod, "unknown_applied_migrations", kaydet("taninmayan-goc", []))
    monkeypatch.setattr(main_mod, "ensure_no_unknown_migrations", kaydet("goc-surumu"))
    monkeypatch.setattr(main_mod, "has_pending_migrations", kaydet("bekleyen-goc-var-mi", True))
    monkeypatch.setattr(main_mod, "pre_migrate_backup", kaydet("goc-oncesi-yedek"))
    monkeypatch.setattr(main_mod, "run_migrations", kaydet("goc"))
    monkeypatch.setattr(main_mod, "write_version_stamp", kaydet("damga-yaz"))
    return sira


def test_acilis_sirasi_tasarimla_birebir(tmp_path: Path, izlenen_adimlar: list[str]) -> None:
    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)})

    main_mod.prepare_data(paths, "0.1.0")

    assert izlenen_adimlar == [
        "surum-damgasi",  # eski program yeni veriyi açmasın
        "butunluk",  # bozuk veriyle yedek rotasyonu ÇALIŞTIRILMAZ
        "gunluk-yedek",
        "rotasyon",
        "django-hazirla",
        # F11 ikinci hat: damga silinmişse (geri yükleme) tanınmayan göç eski programı durdurur.
        "taninmayan-goc",
        "goc-surumu",
        "bekleyen-goc-var-mi",
        "goc-oncesi-yedek",
        "goc",
        "damga-yaz",
    ]


def test_gunluk_yedek_alinmadiysa_rotasyon_kosmaz(
    tmp_path: Path, izlenen_adimlar: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Yedek atlandıysa (parola yok, anahtar bozuk, guvenlik.json kayıp) eski yedekler
    silinmez: kayıp kilidinden çıkış yolu onlardır (GA-2)."""

    def yedek_atlandi(*args: Any, **kwargs: Any) -> None:
        izlenen_adimlar.append("gunluk-yedek")

    monkeypatch.setattr(main_mod, "daily_backup", yedek_atlandi)
    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)})

    main_mod.prepare_data(paths, "0.1.0")

    assert "gunluk-yedek" in izlenen_adimlar
    assert "rotasyon" not in izlenen_adimlar


def test_bekleyen_goc_yoksa_ek_yedek_alinmaz(
    tmp_path: Path, izlenen_adimlar: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(main_mod, "has_pending_migrations", lambda: False)
    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)})

    main_mod.prepare_data(paths, "0.1.0")

    assert "goc-oncesi-yedek" not in izlenen_adimlar


# ------------------------------------------------------------ hata senaryoları


@pytest.fixture
def sahte_calisma(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """`run()` çevresini izole eder: veri hazırlığı ve sunucu sahte."""
    kayit: dict[str, Any] = {"pencere": 0, "hata": [], "servis": 0}

    def sahte_serve(paths: Any, token: str, autotest: bool, channel: Any = None, **_: Any) -> int:
        kayit["servis"] += 1
        kayit["kanal"] = channel
        return EXIT_OK

    def sahte_hata(title: str, message: str) -> None:
        kayit["hata"].append((title, message))

    monkeypatch.setattr(main_mod, "prepare_data", lambda paths, version: None)
    monkeypatch.setattr(main_mod, "serve", sahte_serve)
    monkeypatch.setattr(main_mod, "show_error", sahte_hata)
    # `run` bu değişkeni süreç ortamına yazar; test sonunda geri alınsın.
    monkeypatch.setenv(ENV_PREVIOUS_SESSION, "")
    return kayit


def test_ikinci_kopya_pencere_acmadan_cikar(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    ilk = SingleInstanceLock(resolve_app_paths().lock_path)
    ilk.acquire()
    try:
        kod = main_mod.run([])
    finally:
        ilk.release()

    assert kod == EXIT_ALREADY_RUNNING
    assert sahte_calisma["servis"] == 0
    assert "zaten çalışıyor" in sahte_calisma["hata"][0][1]


def test_bozuk_veritabani_pencere_actirmaz(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))

    def patla(paths: Any, version: str) -> None:
        raise DatabaseCorruptError("Veri dosyası bozuk görünüyor.", hint="Son yedekten dönün.")

    monkeypatch.setattr(main_mod, "prepare_data", patla)

    kod = main_mod.run([])

    assert kod == EXIT_DATABASE_CORRUPT
    assert sahte_calisma["servis"] == 0
    baslik, mesaj = sahte_calisma["hata"][0]
    assert "bozuk" in mesaj.lower()
    assert "yedek" in mesaj.lower()
    assert baslik


def test_webview_yoksa_ozel_cikis_kodu(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))

    def patla(paths: Any, token: str, autotest: bool, channel: Any = None, **_: Any) -> int:
        raise WebViewUnavailableError("WebView2 yok.", hint="Kurun.")

    monkeypatch.setattr(main_mod, "serve", patla)

    assert main_mod.run([]) == EXIT_WEBVIEW_UNAVAILABLE


def test_beklenmeyen_hata_da_turkce_iletiyle_biter(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))

    def patla(paths: Any, version: str) -> None:
        raise RuntimeError("beklenmedik")

    monkeypatch.setattr(main_mod, "prepare_data", patla)

    kod = main_mod.run([])

    assert kod == 1
    assert sahte_calisma["hata"]
    assert "beklenmedik" not in sahte_calisma["hata"][0][1]  # ham teknik metin gösterilmez


def test_kilit_cikista_birakilir(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))

    main_mod.run([])
    main_mod.run([])  # kilit bırakılmamış olsaydı ikinci koşu reddedilirdi

    assert sahte_calisma["servis"] == 2


# ------------------------------------------------- ikinci açılış (§4.2-1, GA-11)


def test_bayraksiz_ikinci_acilis_pencereyi_one_getirip_sifirla_cikar(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    sinyal: list[Path] = []

    def gonder(kok: Path) -> bool:
        sinyal.append(kok)
        return True

    monkeypatch.setattr(main_mod, "signal_running_instance", gonder)

    with SingleInstanceLock(resolve_app_paths().lock_path):
        kod = main_mod.run([])

    assert kod == EXIT_OK
    assert sinyal == [tmp_path]
    assert sahte_calisma["servis"] == 0
    assert sahte_calisma["hata"] == []  # ileti kutusu yok: pencere öne geldi


def test_calisan_kopya_gercek_kanalla_one_getirilir(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Uçtan uca (Linux): ilk kopyanın kanalı ikinci açılışın `goster` komutunu alır."""
    if not sys.platform.startswith("linux"):
        pytest.skip("UNIX soketi kanalı yalnız Linux'ta")
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    paths = resolve_app_paths()
    alinan: list[str] = []
    kanal = open_channel(paths.root)
    assert kanal is not None
    kanal.start(alinan.append)
    try:
        with SingleInstanceLock(paths.lock_path):
            kod = main_mod.run([])
        for _ in range(300):
            if alinan:
                break
            time.sleep(0.01)
    finally:
        kanal.close()

    assert kod == EXIT_OK
    assert alinan == ["goster"]


def test_sinyal_ulasmazsa_zaten_calisiyor_iletisi(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    monkeypatch.setattr(main_mod, "signal_running_instance", lambda kok: False)

    with SingleInstanceLock(resolve_app_paths().lock_path):
        kod = main_mod.run([])

    assert kod == EXIT_ALREADY_RUNNING
    assert "zaten çalışıyor" in sahte_calisma["hata"][0][1]


@pytest.mark.parametrize(
    "bayraklar", [["--autotest"], ["--geri-yukle"], ["--geri-yukle", "yedek.odbak"]]
)
def test_bayrakli_acilis_calisan_kopyada_2_ile_cikar_sinyal_gondermez(
    tmp_path: Path,
    sahte_calisma: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    bayraklar: list[str],
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    monkeypatch.setattr(
        main_mod, "signal_running_instance", lambda kok: pytest.fail("sinyal gönderilmemeli")
    )
    monkeypatch.setattr(restore_mod, "show_error", lambda baslik, mesaj: None)

    with SingleInstanceLock(resolve_app_paths().lock_path):
        kod = main_mod.run(bayraklar)

    assert kod == EXIT_ALREADY_RUNNING
    assert sahte_calisma["servis"] == 0


def test_bayraksiz_acilis_tanimi() -> None:
    parser = main_mod.build_parser()

    assert main_mod.is_plain_launch(parser.parse_args([])) is True
    assert main_mod.is_plain_launch(parser.parse_args(["--data-dir", "x"])) is True
    assert main_mod.is_plain_launch(parser.parse_args(["--autotest"])) is False
    assert main_mod.is_plain_launch(parser.parse_args(["--geri-yukle"])) is False


# ---------------------------------------------------------- tek kopya kanalı


def test_normal_acilis_kanal_kurar_ve_cikista_kapatir(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    kanallar: list[_SahteKanal] = []

    def ac(kok: Path) -> _SahteKanal:
        kanal = _SahteKanal(kok)
        kanallar.append(kanal)
        return kanal

    monkeypatch.setattr(main_mod, "open_channel", ac)

    assert main_mod.run([]) == EXIT_OK

    (kanal,) = kanallar
    assert kanal.kok == tmp_path
    assert sahte_calisma["kanal"] is kanal
    assert kanal.kapatildi is True


def test_autotest_kanal_kurmaz(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    monkeypatch.setattr(main_mod, "open_channel", lambda kok: pytest.fail("kanal kurulmamalı"))

    assert main_mod.run(["--autotest"]) == EXIT_OK
    assert sahte_calisma["kanal"] is None


def test_kanal_komutlari_pencere_denetcisine_gider() -> None:
    denetci = _SahteDenetci()

    main_mod.dispatch_command("goster", denetci)  # type: ignore[arg-type]
    main_mod.dispatch_command("kapat", denetci)  # type: ignore[arg-type]
    main_mod.dispatch_command("bilinmeyen", denetci)  # type: ignore[arg-type]

    assert denetci.cagrilar == ["show", "request_quit"]


# ------------------------------------------------ pencere oturumu (T6)


class _SahteKanal:
    def __init__(self, kok: Path | None = None) -> None:
        self.kok = kok
        self.isleyici: Any = None
        self.kapatildi = False

    def start(self, isleyici: Any) -> None:
        self.isleyici = isleyici

    def close(self) -> None:
        self.kapatildi = True


class _SahteDenetci:
    def __init__(self) -> None:
        self.cagrilar: list[str] = []

    def show(self) -> None:
        self.cagrilar.append("show")

    def request_quit(self) -> None:
        self.cagrilar.append("request_quit")


@pytest.fixture
def pencere_oturumu(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    kayit: dict[str, Any] = {"sira": []}
    sira: list[str] = kayit["sira"]

    def pencere(url: str, *, storage_path: Path, controller: Any, **kw: Any) -> None:
        sira.append("pencere")
        kayit["denetci"] = controller
        kayit["pencere_kw"] = kw
        if kayit.get("pencere_hatasi"):
            raise RuntimeError("pencere motoru çöktü")

    class _SahteQt:
        def durdur(self) -> None:
            sira.append("qt-dur")

    def qt_hazirla(cikis: Any) -> _SahteQt:
        sira.append("qt-hazirla")
        kayit["qt_cikis"] = cikis
        return _SahteQt()

    monkeypatch.setattr(main_mod, "open_window", pencere)
    monkeypatch.setattr(qt_kurulum_mod, "hazirla", qt_hazirla)
    return kayit


def test_linuxta_qt_kurulumu_pencereden_once_ve_cikista_durdurulur(
    tmp_path: Path, pencere_oturumu: dict[str, Any]
) -> None:
    """§4.2 adım 11, §13 D1: Qt uygulaması ve SIGTERM köprüsü pencereden önce kurulur;
    SIGTERM düzenli kapanışa (pencere denetçisinin Çık'ı) bağlanır."""
    main_mod.run_window_session("http://127.0.0.1:1/", tmp_path, None, platform="linux")

    assert pencere_oturumu["sira"].index("qt-hazirla") < pencere_oturumu["sira"].index("pencere")
    assert pencere_oturumu["sira"][-1] == "qt-dur"
    assert pencere_oturumu["qt_cikis"] == pencere_oturumu["denetci"].request_quit


def test_windowsta_qt_kurulmaz(tmp_path: Path, pencere_oturumu: dict[str, Any]) -> None:
    main_mod.run_window_session("http://127.0.0.1:1/", tmp_path, None, platform="win32")

    assert "qt-hazirla" not in pencere_oturumu["sira"]


def test_pencere_oturumu_kanal_ve_qt_koprusunu_cikista_kapatir(
    tmp_path: Path, pencere_oturumu: dict[str, Any]
) -> None:
    """T6: tepsi yoktur; pencere görünür açılır, gizli açılış seçeneği yoktur."""
    kanal = _SahteKanal()

    main_mod.run_window_session("http://127.0.0.1:1/", tmp_path, kanal, platform="linux")

    assert pencere_oturumu["sira"] == ["qt-hazirla", "pencere", "qt-dur"]
    assert kanal.kapatildi is True
    assert "hidden" not in pencere_oturumu["pencere_kw"]


def test_pencere_hatasinda_da_kanal_ve_qt_koprusu_kapanir(
    tmp_path: Path, pencere_oturumu: dict[str, Any]
) -> None:
    pencere_oturumu["pencere_hatasi"] = True
    kanal = _SahteKanal()

    with pytest.raises(RuntimeError):
        main_mod.run_window_session("http://127.0.0.1:1/", tmp_path, kanal, platform="linux")

    assert pencere_oturumu["sira"][-1] == "qt-dur"
    assert kanal.kapatildi is True


def test_tepsi_bayragi_ve_modulu_yok() -> None:
    """T6 (§4.5): `--tepside` ve tepsi modülü sökülmüştür."""
    with pytest.raises(SystemExit):
        main_mod.build_parser().parse_args(["--tepside"])
    assert not hasattr(main_mod, "start_tray")
    assert not (REPO_ROOT / "desktop" / "tray.py").exists()


def test_kanaldan_kapat_gelince_pencere_kapanir(
    tmp_path: Path, pencere_oturumu: dict[str, Any]
) -> None:
    kanal = _SahteKanal()
    main_mod.run_window_session("http://127.0.0.1:1/", tmp_path, kanal, platform="linux")

    kanal.isleyici("kapat")

    assert pencere_oturumu["denetci"].quitting is True


# ------------------------------------------------- temiz kapanış işareti (T15)


def _isaret(tmp_path: Path) -> Path:
    return tmp_path / "data" / MARKER_FILE_NAME


def _db_olustur(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "db.sqlite3").write_bytes(b"SQLite format 3\x00")


def test_duzenli_cikista_isaret_yazilir(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))

    assert main_mod.run([]) == EXIT_OK

    assert _isaret(tmp_path).is_file()


def test_ilk_acilista_alarm_yok_sonraki_acilista_temiz(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))

    main_mod.run([])
    assert os.environ[ENV_PREVIOUS_SESSION] == "ilk"

    _db_olustur(tmp_path)
    main_mod.run([])
    assert os.environ[ENV_PREVIOUS_SESSION] == "temiz"


def test_isaret_yoksa_beklenmedik_kapanma_backende_bildirilir(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    _db_olustur(tmp_path)  # önceki oturum vardı, işaret yazmadan öldü
    gorulen: list[str] = []

    def serve(paths: Any, token: str, autotest: bool, channel: Any = None, **_: Any) -> int:
        gorulen.append(os.environ[ENV_PREVIOUS_SESSION])  # Django ayarlarından önce yazılmış
        return EXIT_OK

    monkeypatch.setattr(main_mod, "serve", serve)

    main_mod.run([])

    assert gorulen == ["beklenmedik"]


def test_beklenmeyen_hatada_isaret_yazilmaz(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Zorla sonlandırmanın karşılığı: açılışta silinen işaret geri gelmez."""
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    _db_olustur(tmp_path)
    main_mod.run([])
    assert _isaret(tmp_path).is_file()

    def patla(paths: Any, token: str, autotest: bool, channel: Any = None, **_: Any) -> int:
        raise RuntimeError("pencere motoru çöktü")

    monkeypatch.setattr(main_mod, "serve", patla)

    assert main_mod.run([]) == 1
    assert not _isaret(tmp_path).exists()


@pytest.mark.parametrize(("onceki_temiz", "sonra_isaret"), [(True, True), (False, False)])
def test_acilis_hatasi_onceki_oturumun_durumunu_korur(
    tmp_path: Path,
    sahte_calisma: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    onceki_temiz: bool,
    sonra_isaret: bool,
) -> None:
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    _db_olustur(tmp_path)
    if onceki_temiz:
        _isaret(tmp_path).write_text("{}", encoding="utf-8")

    def patla(paths: Any, version: str) -> None:
        raise DatabaseCorruptError("Veri dosyası bozuk görünüyor.")

    monkeypatch.setattr(main_mod, "prepare_data", patla)

    assert main_mod.run([]) == EXIT_DATABASE_CORRUPT
    assert _isaret(tmp_path).exists() is sonra_isaret


def test_ikinci_kopya_isarete_dokunmaz(
    tmp_path: Path, sahte_calisma: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Çalışan kopya varken açılış işareti okumaz/silmez: o kopyanın durumu bozulmaz."""
    monkeypatch.setenv(ENV_APP_HOME, str(tmp_path))
    monkeypatch.setattr(main_mod, "signal_running_instance", lambda kok: True)
    _db_olustur(tmp_path)
    _isaret(tmp_path).write_text("{}", encoding="utf-8")

    with SingleInstanceLock(resolve_app_paths().lock_path):
        main_mod.run([])

    assert _isaret(tmp_path).is_file()


# ------------------------------------------------------------ uçtan uca açılış


@pytest.mark.slow
def test_autotest_kipi_gercek_acilisi_dogrular(tmp_path: Path) -> None:
    """Gerçek açılış: kilit → yedek → migrate → waitress → belirteç → çıkış (pencere YOK)."""
    sonuc = subprocess.run(  # noqa: S603 — sabit argümanlar, kabuk yok
        [
            sys.executable,
            "-m",
            "desktop.main",
            "--autotest",
            "--data-dir",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert sonuc.returncode == EXIT_OK, sonuc.stderr
    assert (tmp_path / "data" / "db.sqlite3").is_file()
    assert (tmp_path / "data" / "surum.json").is_file()
    assert (tmp_path / "logs" / "uygulama.log").is_file()
    # İlk açılışta veritabanı henüz yoktu → yedek yok; ilk yedek yönetici parolası
    # kurulduktan sonraki açılışta alınır.
    assert (tmp_path / "backups").is_dir()
    # T15: düzenli çıkış işareti yazar; ilk açılış alarm vermez.
    assert (tmp_path / "data" / MARKER_FILE_NAME).is_file()
    gunluk = (tmp_path / "logs" / "uygulama.log").read_text(encoding="utf-8")
    assert "İlk açılış" in gunluk
    assert "beklenmedik" not in gunluk


@pytest.mark.slow
def test_parola_kurulmadan_ikinci_acilista_gunluk_yedek_atlanir(tmp_path: Path) -> None:
    """Tasarım §6.3-6: ilk açılışta `yedekleme.json` (ve kişi verisi) yokken günlük
    yedek ATLANIR; düz kopya hiçbir koşulda yazılmaz. İlk yedek, yönetici parolası
    kurulduktan sonraki açılışta şifreli alınır."""
    for _ in range(2):
        sonuc = subprocess.run(  # noqa: S603 — sabit argümanlar, kabuk yok
            [
                sys.executable,
                "-m",
                "desktop.main",
                "--autotest",
                "--data-dir",
                str(tmp_path),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert sonuc.returncode == EXIT_OK, sonuc.stderr

    # İkinci açılış birincinin işaretini okuyup sildi, çıkışta yenisini yazdı.
    gunluk = (tmp_path / "logs" / "uygulama.log").read_text(encoding="utf-8")
    assert "Önceki oturum düzenli kapanmış." in gunluk
    assert (tmp_path / "data" / MARKER_FILE_NAME).is_file()

    # Parola kurulmadı → yedek anahtarı yok → yedek atlandı; düz kopya da yok.
    assert not (tmp_path / "data" / "yedekleme.json").exists()
    assert not list((tmp_path / "backups").glob("gunluk-*"))
    assert "yedek alınmadı" in gunluk


def _autotest_sureci(tmp_path: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(  # noqa: S603 — sabit argümanlar, kabuk yok
        [sys.executable, "-m", "desktop.main", "--autotest", "--data-dir", str(tmp_path)],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


@pytest.mark.slow
def test_zorla_sonlandirmada_isaret_eksik_kalir_ve_sonraki_acilis_uyarir(
    tmp_path: Path,
) -> None:
    """F0 kapısı (T15): öldürülen süreç işareti yazamaz; sonraki açılış bunu görür."""
    ilk = _autotest_sureci(tmp_path)
    assert ilk.wait(timeout=300) == EXIT_OK
    isaret = tmp_path / "data" / MARKER_FILE_NAME
    assert isaret.is_file()

    ikinci = _autotest_sureci(tmp_path)
    try:
        son = time.monotonic() + 120
        while isaret.exists() and ikinci.poll() is None and time.monotonic() < son:
            time.sleep(0.005)
        if ikinci.poll() is not None:
            pytest.fail("süreç işaret okunduktan sonra öldürülemeden bitti")
        ikinci.kill()  # SIGKILL: temizlik kodu koşmaz
    finally:
        ikinci.wait(timeout=60)
    assert not isaret.exists()

    ucuncu = _autotest_sureci(tmp_path)
    assert ucuncu.wait(timeout=300) == EXIT_OK
    gunluk = (tmp_path / "logs" / "uygulama.log").read_text(encoding="utf-8")
    assert "Önceki oturum beklenmedik biçimde kapandı" in gunluk
    assert isaret.is_file()  # üçüncü oturum düzenli kapandı


@pytest.mark.slow
def test_gunluge_ogrenci_arama_sorgusu_dusmez(tmp_path: Path) -> None:
    """Erişim logu kapalı: istek yolu ne dosyaya ne de konsola düşmeli (KS F2 #20).

    `OD_DEBUG=1` ile koşar: Django'nun konsol handler'ı ancak DEBUG açıkken
    yayın yapar, yani sızıntı bu kipte görünür hale gelir.
    """
    sonuc = subprocess.run(  # noqa: S603 — sabit argümanlar, kabuk yok
        [
            sys.executable,
            "-m",
            "desktop.main",
            "--autotest",
            "--data-dir",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "OD_DEBUG": "1"},
    )

    gunluk = (tmp_path / "logs" / "uygulama.log").read_text(encoding="utf-8")
    assert "setup/status" not in gunluk  # istek yolu bile loglanmaz
    assert "?" not in gunluk
    assert "setup/status" not in sonuc.stderr
    assert "Forbidden" not in sonuc.stderr
    assert "Logging error" not in sonuc.stderr


# ------------------------------------------------- Çık kancası (§4.2, TB13)


def test_arayuzden_cik_yanittan_sonra_ayri_is_parcaciginda_kapanisi_baslatir() -> None:
    goruldu: list[str] = []
    olay = threading.Event()

    class _Denetci:
        def request_quit(self) -> None:
            goruldu.append(threading.current_thread().name)
            olay.set()

    kanca = main_mod.cikis_kancasi(_Denetci())  # type: ignore[arg-type]
    baslangic = time.monotonic()
    kanca()  # HTTP isteği iş parçacığı: hemen döner
    assert time.monotonic() - baslangic < 0.1
    assert goruldu == []

    assert olay.wait(5)
    assert goruldu == ["od-cikis"]


# ------------------------------------------------------------ WAL (TB14)


def test_kapanista_wal_checkpoint_wal_dosyasini_bosaltir(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    with closing(sqlite3.connect(db)) as yazar:
        yazar.execute("PRAGMA journal_mode=WAL")
        yazar.execute("PRAGMA wal_autocheckpoint=0")
        yazar.execute("CREATE TABLE odunc (id INTEGER PRIMARY KEY, barkod TEXT)")
        yazar.executemany("INSERT INTO odunc (barkod) VALUES (?)", [(str(i),) for i in range(200)])
        yazar.commit()
        wal = db.with_name("db.sqlite3-wal")
        assert wal.stat().st_size > 0  # işlenmiş sayfalar hâlâ WAL'de

        assert wal_checkpoint(db) is True

        assert wal.stat().st_size == 0  # TRUNCATE: WAL ana dosyaya aktarıldı ve kırpıldı
    with closing(sqlite3.connect(db)) as okur:
        assert okur.execute("SELECT COUNT(*) FROM odunc").fetchone()[0] == 200


def test_wal_checkpoint_veritabani_yoksa_sessiz(tmp_path: Path) -> None:
    assert wal_checkpoint(tmp_path / "yok.sqlite3") is False


def test_wal_checkpoint_okuyucu_varken_kismi_kalir_ve_cikisi_durdurmaz(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    with closing(sqlite3.connect(db)) as yazar, closing(sqlite3.connect(db)) as okur:
        yazar.execute("PRAGMA journal_mode=WAL")
        yazar.execute("PRAGMA wal_autocheckpoint=0")
        yazar.execute("CREATE TABLE t (x)")
        yazar.commit()
        okur.execute("BEGIN")
        okur.execute("SELECT * FROM t").fetchall()  # okuma işlemi açık: anlık görüntü tutuluyor
        yazar.execute("INSERT INTO t VALUES (1)")
        yazar.commit()

        assert wal_checkpoint(db) is False
        okur.execute("COMMIT")


# ----------------------------------------------------- iş parçacığı bağlantısı


class _Baglanti:
    def __init__(self) -> None:
        self.connection: object | None = None
        self.in_atomic_block = False
        self.kapatildi = 0

    def close(self) -> None:
        self.kapatildi += 1


def test_is_parcacigi_baglantisi_yalniz_kendi_actigini_kapatir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tepsi ve `od-gunluk` bağlantı bırakırsa Windows'ta geri yükleme takası düşer."""
    sahte = _Baglanti()
    monkeypatch.setattr("django.db.connections", {"default": sahte})

    assert is_parcacigi_baglantisiyla(lambda: 42) == 42
    assert sahte.kapatildi == 1  # çağrının açtığı (önceden yoktu) kapatıldı

    sahte.connection = object()  # HTTP isteği iş parçacığı: bağlantı önceden açık
    is_parcacigi_baglantisiyla(lambda: None)
    assert sahte.kapatildi == 1  # isteğin bağlantısına dokunulmadı


# ------------------------------------------------------ gün değişimi işleri


def test_gunluk_yedek_isi_yedek_alinmazsa_rotasyon_kosmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)})
    olaylar: list[str] = []
    monkeypatch.setattr(main_mod, "daily_backup", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "rotate_backups", lambda *a, **k: olaylar.append("rotasyon"))

    assert main_mod.gunluk_yedek_isi(paths, bugun=lambda: date(2026, 9, 24))() is False
    assert olaylar == []

    monkeypatch.setattr(main_mod, "daily_backup", lambda *a, **k: tmp_path / "gunluk.odbak")
    assert main_mod.gunluk_yedek_isi(paths, bugun=lambda: date(2026, 9, 24))() is True
    assert olaylar == ["rotasyon"]


def _sahte_gunluk_yedek(monkeypatch: pytest.MonkeyPatch) -> None:
    """Günlük yedeği yalnız dosya adıyla taklit eder (şifreleme `test_backup.py`'dedir)."""
    from desktop.backup import DAILY_PREFIX
    from desktop.backup_crypto import BACKUP_SUFFIX

    def yedek(db: Path, klasor: Path, *, today: date) -> Path:
        klasor.mkdir(parents=True, exist_ok=True)
        hedef = klasor / f"{DAILY_PREFIX}-{today.isoformat()}{BACKUP_SUFFIX}"
        hedef.write_bytes(b"x")
        return hedef

    monkeypatch.setattr(main_mod, "daily_backup", yedek)


def test_saat_ileri_sicrarsa_oturum_ici_rotasyon_gecmis_yedekleri_silmez(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bulgu: günlerce açık kalan programda saat 14 günden fazla ileri sıçrarsa bütün günlük
    yedekler silinirdi. Rotasyon gerçek geçen süreye (uyku dahil açık kalma saati) göre
    kesilir; "en çok 14 gün" saklama sözü (TB8) bozulmaz."""
    from desktop.backup import DAILY_PREFIX
    from desktop.backup_crypto import BACKUP_SUFFIX

    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)})
    paths.ensure()
    _sahte_gunluk_yedek(monkeypatch)
    gun = [date(2026, 9, 24)]
    saat = [1_000.0]
    is_ = main_mod.gunluk_yedek_isi(paths, bugun=lambda: gun[0], saat=lambda: saat[0])
    for i in range(1, 10):  # geçmiş dokuz günün yedekleri
        onceki = date(2026, 9, 24) - timedelta(days=i)
        (paths.backups / f"{DAILY_PREFIX}-{onceki.isoformat()}{BACKUP_SUFFIX}").write_bytes(b"x")

    assert is_() is True  # çapa: 24.09, saat 1000
    gun[0] = date(2026, 10, 30)  # saat bir saat içinde 36 gün ileri sıçradı
    saat[0] += 3_600
    assert is_() is True

    kalan = sorted(p.name for p in paths.backups.glob(f"{DAILY_PREFIX}-*{BACKUP_SUFFIX}"))
    assert f"{DAILY_PREFIX}-2026-09-15{BACKUP_SUFFIX}" in kalan  # geçmiş yedekler duruyor
    assert f"{DAILY_PREFIX}-2026-10-30{BACKUP_SUFFIX}" in kalan
    assert len(kalan) == 11


def test_gercekten_gecen_gunlerde_rotasyon_olagan_calisir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Uyku dahil saat de ilerlediyse (tatilde uykuda kalan bilgisayar) kesim olağandır."""
    from desktop.backup import DAILY_PREFIX
    from desktop.backup_crypto import BACKUP_SUFFIX

    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)})
    paths.ensure()
    _sahte_gunluk_yedek(monkeypatch)
    gun = [date(2026, 9, 24)]
    saat = [1_000.0]
    is_ = main_mod.gunluk_yedek_isi(paths, bugun=lambda: gun[0], saat=lambda: saat[0])
    assert is_() is True

    gun[0] = date(2026, 10, 30)
    saat[0] += 36 * 86_400
    assert is_() is True

    kalan = sorted(p.name for p in paths.backups.glob(f"{DAILY_PREFIX}-*{BACKUP_SUFFIX}"))
    assert kalan == [f"{DAILY_PREFIX}-2026-10-30{BACKUP_SUFFIX}"]  # 24.09 kesimden eski


# ------------------------------------------------- kapanış sırası (§4.2, TB14)


class _SahteYonetim:
    """Yönetim `BackgroundServer`'ının yerine geçer; sırayı kaydeder."""

    sira: list[str] = []

    def __init__(self, application: object) -> None:
        self.base_url = "http://127.0.0.1:54321"

    def start(self) -> str:
        self.sira.append("yonetim-basla")
        return self.base_url

    def wait_until_ready(self) -> None:
        pass

    def stop(self) -> None:
        self.sira.append("yonetim-dur")


class _SahteKapi:
    def __init__(self, sira: list[str]) -> None:
        self.sira = sira

    def baslat(self) -> None:
        self.sira.append("od-gunluk")

    def durdur(self) -> None:
        self.sira.append("od-gunluk-dur")


@pytest.fixture
def sahte_servis(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    """`serve()` çevresini izole eder: Django ve pencere sahte, sıra kayıtlı."""
    sira: list[str] = []
    monkeypatch.setattr(_SahteYonetim, "sira", sira)
    kayit: dict[str, Any] = {
        "sira": sira,
        "paths": resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)}),
    }
    monkeypatch.setattr(main_mod, "build_wsgi_application", lambda: object())
    monkeypatch.setattr(main_mod, "assert_session_guard_installed", lambda: None)
    monkeypatch.setattr(main_mod, "BackgroundServer", _SahteYonetim)
    monkeypatch.setattr(main_mod, "check_health", lambda url, token: sira.append("saglik"))
    monkeypatch.setattr(main_mod, "require_window_runtime", lambda: None)
    monkeypatch.setattr(
        main_mod, "run_window_session", lambda url, storage, channel, **_: sira.append("pencere")
    )
    monkeypatch.setattr(main_mod, "gun_kapisi_kur", lambda paths, **_: _SahteKapi(sira))
    monkeypatch.setattr(main_mod, "wal_checkpoint", lambda yol: sira.append("wal-checkpoint"))
    return kayit


def test_kapanis_sirasi_gun_kapisi_sunucu_ve_wal_checkpoint(sahte_servis: dict[str, Any]) -> None:
    kod = main_mod.serve(sahte_servis["paths"], "belirtec", False)

    assert kod == EXIT_OK
    assert sahte_servis["sira"] == [
        "yonetim-basla",
        "saglik",
        "od-gunluk",  # yönetim ayakta ve korumalı olduktan SONRA
        "pencere",
        "od-gunluk-dur",
        "yonetim-dur",
        "wal-checkpoint",  # TB14: sunucu durduktan SONRA
    ]


def test_autotest_pencere_ve_gun_kapisi_acmaz_ag_dinleyicisi_kurmaz(
    sahte_servis: dict[str, Any],
) -> None:
    """§13 D5: `--autotest` 1-9 + sağlık denetimidir; katalog adımı yoktur."""
    kod = main_mod.serve(sahte_servis["paths"], "belirtec", True)

    assert kod == EXIT_OK
    assert sahte_servis["sira"] == ["yonetim-basla", "saglik", "yonetim-dur", "wal-checkpoint"]


def test_pencere_motoru_yoksa_gun_kapisi_kalkmaz(
    sahte_servis: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def pencere_yok() -> None:
        raise WebViewUnavailableError("WebView2 yok.")

    monkeypatch.setattr(main_mod, "require_window_runtime", pencere_yok)

    with pytest.raises(WebViewUnavailableError):
        main_mod.serve(sahte_servis["paths"], "belirtec", False)

    assert sahte_servis["sira"][-2:] == ["yonetim-dur", "wal-checkpoint"]
    assert "od-gunluk" not in sahte_servis["sira"]


def test_pencere_hatasinda_da_gun_kapisi_ve_sunucu_durdurulur(
    sahte_servis: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def pencere_coktu(url: str, storage: Path, channel: Any, **_: Any) -> None:
        raise RuntimeError("pencere motoru çöktü")

    monkeypatch.setattr(main_mod, "run_window_session", pencere_coktu)

    with pytest.raises(RuntimeError):
        main_mod.serve(sahte_servis["paths"], "belirtec", False)

    assert sahte_servis["sira"][-3:] == ["od-gunluk-dur", "yonetim-dur", "wal-checkpoint"]


def test_gun_kapisi_yerlesik_isi_gunluk_yedektir(tmp_path: Path) -> None:
    """Ağ kataloğunun IP denetimi, saatlik denetimi ve uyku engeli sökülmüştür."""
    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)})

    kapi = main_mod.gun_kapisi_kur(paths)

    assert kapi.is_adlari[0] == "gunluk-yedek"
    assert "ip-denetimi" not in kapi.is_adlari


def test_eski_duz_yedek_donusturucusu_yok() -> None:
    """§13 D29: OAB'de düz yedek hiç olmadı; dönüştürücü ve düz kalıplar sökülmüştür."""
    from desktop import backup

    assert not hasattr(backup, "encrypt_legacy_backups")
    assert not hasattr(main_mod, "encrypt_legacy_backups")


def test_acilista_umask_dizinlerden_ve_gunlukten_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """§4.2 adım 1, §13 D52: Linux'ta `umask 077` veri dizinleri ve günlük açılmadan önce."""
    sira: list[str] = []

    class _Dur(Exception):
        pass

    class _Yerlesim:
        logs = tmp_path

        def ensure(self) -> None:
            sira.append("dizinler")

    def gunluk(*_args: Any, **_kwargs: Any) -> None:
        sira.append("gunluk")
        raise _Dur

    monkeypatch.setattr(main_mod, "resolve_paths", lambda _args: _Yerlesim())
    monkeypatch.setattr(main_mod, "gizli_kipleri_uygula", lambda: sira.append("umask"))
    monkeypatch.setattr(main_mod, "configure_logging", gunluk)

    with pytest.raises(_Dur):
        main_mod.run([])

    assert sira == ["umask", "dizinler", "gunluk"]
