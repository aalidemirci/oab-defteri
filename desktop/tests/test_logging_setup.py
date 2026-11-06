"""Günlük yapılandırması testleri — erişim logu KAPALI, PII yazılmaz (aile denetim bulgusu)."""

from __future__ import annotations

import faulthandler
import logging
import logging.config
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest

from desktop import logging_setup
from desktop.logging_setup import (
    CRASH_LOG_NAME,
    LOG_FILE_NAME,
    LOGGER_NAME,
    PiiSafeFormatter,
    apply_access_log_policy,
    configure_logging,
    enable_crash_log,
)

REPO = Path(__file__).resolve().parents[2]

# Django'nun `DEFAULT_LOGGING`'inin bizi ilgilendiren iskeleti: "django" günlükçüsünü
# tanımlar, "django.request"i tanımlamaz. `dictConfig`, tanımlı bir günlükçünün
# ALTINDA kalan mevcut günlükçüleri (child_loggers) SIFIRLAR — seviye NOTSET,
# handler listesi boş, propagate True.
DJANGO_VARSAYILAN_GUNLUK = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django": {"handlers": ["console"], "level": "INFO"}},
}


def test_gunluk_veri_dizinindeki_logs_altina_yazilir(tmp_path: Path) -> None:
    logger = configure_logging(tmp_path)

    logger.info("Program açıldı.")
    logging.shutdown()

    icerik = (tmp_path / LOG_FILE_NAME).read_text(encoding="utf-8")
    assert "Program açıldı." in icerik


def test_yapilandirma_tekrarlanabilir_ve_handler_cogaltmaz(tmp_path: Path) -> None:
    configure_logging(tmp_path)
    configure_logging(tmp_path)
    logger = configure_logging(tmp_path)

    assert len(logger.handlers) == 1


def test_erisim_logu_uretilmez(tmp_path: Path) -> None:
    """waitress/Django istek logları `?search=<öğrenci adı>` sızdırır → kapalı."""
    configure_logging(tmp_path)

    for ad in ("waitress", "waitress.queue", "django.server"):
        assert logging.getLogger(ad).level >= logging.ERROR

    logging.getLogger("django.server").info('"GET /api/v1/students/?search=Ayşe" 200')
    logging.shutdown()

    icerik = (tmp_path / LOG_FILE_NAME).read_text(encoding="utf-8")
    assert "Ayşe" not in icerik


def test_sorgu_dizesi_gunluge_yazilmaz(tmp_path: Path) -> None:
    """Sigorta: bir kütüphane yine de URL loglarsa sorgu dizesi kırpılır."""
    logger = configure_logging(tmp_path)

    logger.warning("İstek başarısız: /api/v1/students/?search=Ayşe%20Yılmaz&limit=25")
    logging.shutdown()

    icerik = (tmp_path / LOG_FILE_NAME).read_text(encoding="utf-8")
    assert "Ayşe" not in icerik
    assert "/api/v1/students/" in icerik


# ---------------------------------------------------------------------------
# Ev dizini (kullanıcı kararı 06.11.2026 "Biçimleyici silsin"): Windows yolu hesap adını taşır,
# hesap adı çoğu bilgisayarda kişinin adıdır. Windows yolu işlev parametrelenerek sınanır.
# ---------------------------------------------------------------------------
WINDOWS_EVI = r"C:\Users\Ali Veli"


def _bicimle(ev: str, mesaj: str, *, windows: bool = False) -> str:
    bicimleyici = PiiSafeFormatter("%(message)s", ev_dizini=lambda: ev, windows=windows)
    return bicimleyici.format(_kayit(mesaj))


def _kayit(mesaj: str, exc_info: Any = None) -> logging.LogRecord:
    return logging.LogRecord(LOGGER_NAME, logging.ERROR, __file__, 1, mesaj, None, exc_info)


@pytest.mark.parametrize(
    ("ham", "beklenen"),
    [
        (r"C:\Users\Ali Veli\AppData\yedek.odbak", r"~\AppData\yedek.odbak"),
        (repr(r"C:\Users\Ali Veli\AppData"), repr("~\\AppData")),
        ("C:/Users/Ali Veli/AppData", "~/AppData"),
        (r"C:\Users/Ali Veli\AppData", r"~\AppData"),
        (r"c:\users\ali veli\AppData", r"~\AppData"),
        (r"C:\USERS\ALİ VELİ\AppData", r"~\AppData"),
        (r"C:\Users\Ali Veli", "~"),
        (r"Klasör açılamadı: C:\Users\Ali Veli.", "Klasör açılamadı: ~."),
        (r"'C:\Users\Ali Veli' ve 'C:\Users\Ali Veli\x'", r"'~' ve '~\x'"),
        (r"\\?\C:\Users\Ali Veli\x", r"\\?…"),
    ],
)
def test_windows_ev_dizini_her_yazimda_silinir(ham: str, beklenen: str) -> None:
    assert _bicimle(WINDOWS_EVI, ham, windows=True) == beklenen


def test_ev_dizini_turkce_hesap_adinda_buyuk_kucuk_harf_ayirmaz() -> None:
    ev = r"C:\Users\Ayşe Işık"

    assert _bicimle(ev, r"C:\USERS\AYŞE IŞIK\x", windows=True) == r"~\x"


def test_posixte_buyuk_kucuk_harf_ayrilir() -> None:
    assert _bicimle("/home/ali", "/HOME/ALI/x") == "/HOME/ALI/x"
    assert _bicimle("/home/ali", "/home/ali/x") == "~/x"


def test_windows_kipi_yolu_bilmeyen_platformda_da_buyuk_kucuk_harf_ayirmaz() -> None:
    assert _bicimle("/home/ali", "/HOME/ALI/x", windows=True) == "~/x"


@pytest.mark.skipif(os.name == "nt", reason="varsayılan kip platformdan okunur")
def test_varsayilan_kip_calisilan_platformun_kuralidir() -> None:
    bicimleyici = PiiSafeFormatter("%(message)s", ev_dizini=lambda: "/home/ali")

    assert bicimleyici.format(_kayit("/HOME/ALI/x")) == "/HOME/ALI/x"


@pytest.mark.parametrize(
    ("ev", "yol"),
    [
        ("/root", "/rootfs/x"),
        ("/root", "/root2/x"),
        ("/root", "/root-yedek/x"),
        ("/root", "/root_yedek/x"),
        ("/root", "/root.bak/x"),
        ("/root", "/srv/root/x"),
        ("/root", "/srv//root/x"),
        ("/home/ali", "/home/alican/x"),
        ("/home/ali", "/mnt/yedek/home/ali/x"),
        (WINDOWS_EVI, r"C:\Users\Ali Veliye\x"),
        (WINDOWS_EVI, r"D:\Users\Ali Veli\x"),
        (WINDOWS_EVI, r"XC:\Users\Ali Veli\x"),
    ],
)
def test_benzer_onekli_baska_yol_kirpilmaz(ev: str, yol: str) -> None:
    assert _bicimle(ev, yol, windows=ev == WINDOWS_EVI) == yol


@pytest.mark.parametrize("ev", ["/", "//", "\\", "C:\\", "C:/", "C:", "", "ali", "~", "./ali"])
def test_ev_dizini_kok_ya_da_mutlak_degilse_dokunulmaz(ev: str) -> None:
    metin = "C:\\Users\\Ali Veli\\x /home/ali/x /ali/x /./ali/x ali ~"

    assert _bicimle(ev, metin, windows=True) == metin


@pytest.mark.parametrize("hata", [RuntimeError("yok"), OSError("yok"), KeyError("HOME")])
def test_ev_dizini_okunamiyorsa_dokunulmaz(hata: Exception) -> None:
    def okuyucu() -> str:
        raise hata

    bicimleyici = PiiSafeFormatter("%(message)s", ev_dizini=okuyucu, windows=True)

    assert bicimleyici.format(_kayit(r"C:\Users\Ali Veli\x")) == r"C:\Users\Ali Veli\x"


def test_tek_dizinli_ev_kirpilir() -> None:
    assert _bicimle("/root", "/root/.cache/x") == "~/.cache/x"
    assert _bicimle("/root", "Dizin /root açılamadı") == "Dizin ~ açılamadı"


def test_ev_dizinindeki_duzenli_ifade_isareti_sozdur() -> None:
    assert _bicimle("/home/a+b", "/home/a+b/x") == "~/x"
    assert _bicimle("/home/a+b", "/home/aab/x") == "/home/aab/x"


def test_unc_ev_dizini_kirpilir() -> None:
    assert _bicimle(r"\\sunucu\ev\ali", r"\\sunucu\ev\ali\x", windows=True) == r"~\x"


def test_yigin_izindeki_ev_dizini_de_silinir() -> None:
    """Ham `OSError` metni `repr`'le yazar, yığın izi dosya yolunu tek ters bölüyle."""
    try:
        raise OSError(2, "Dosya yok", WINDOWS_EVI + r"\AppData\yedek.odbak")
    except OSError:
        bilgi = sys.exc_info()
    kayit = _kayit("Yedek okunamadı.", bilgi)
    kayit.exc_text = None
    bicimleyici = PiiSafeFormatter("%(message)s", ev_dizini=lambda: WINDOWS_EVI, windows=True)

    cikti = bicimleyici.format(kayit)

    assert "Ali Veli" not in cikti
    assert r"~\\AppData\\yedek.odbak" in cikti
    assert "Traceback" in cikti


def test_yigin_izi_metnindeki_ev_dizini_de_silinir() -> None:
    bicimleyici = PiiSafeFormatter("%(message)s", ev_dizini=lambda: WINDOWS_EVI, windows=True)
    kayit = _kayit("Yedek okunamadı.")
    kayit.exc_text = f'File "{WINDOWS_EVI}\\kod.py", line 1'
    kayit.stack_info = f'File "{WINDOWS_EVI}\\yigin.py", line 2'

    cikti = bicimleyici.format(kayit)

    assert "Ali Veli" not in cikti
    assert 'File "~\\kod.py"' in cikti
    assert 'File "~\\yigin.py"' in cikti


def test_ev_dizini_ve_sorgu_dizesi_birlikte_kirpilir() -> None:
    assert _bicimle("/home/ali", "/home/ali/x ?search=Ayşe") == "~/x ?…"


def test_gunluk_dosyasinda_ev_dizini_yoktur(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Varsayılan okuyucu gerçek ev dizinini okur; `configure_logging`'in biçimleyicisi bu sınıftır."""
    ev = tmp_path / "ali.veli"
    monkeypatch.setenv("HOME", str(ev))
    logger = configure_logging(tmp_path / "logs")

    try:
        raise OSError(2, "Dosya yok", str(ev / "yedek.odbak"))
    except OSError:
        logger.exception("Yedek okunamadı: %s", ev / "yedek.odbak")
    logging.shutdown()

    icerik = (tmp_path / "logs" / LOG_FILE_NAME).read_text(encoding="utf-8")
    assert "ali.veli" not in icerik
    assert "Yedek okunamadı: ~/yedek.odbak" in icerik
    assert "'~/yedek.odbak'" in icerik


def test_django_kurulumu_erisim_logu_susturmasini_ezer(tmp_path: Path) -> None:
    """`django.setup()` kendi günlük yapılandırmasını uygular ve bizimkini SİLER.

    Bu yüzden `django.request` susturması `django.setup()` SONRASINDA yeniden
    uygulanmalıdır; yoksa istek yolları (DEBUG açıkken sorgu dizeleri de) konsola
    düşer.
    """
    configure_logging(tmp_path)

    logging.config.dictConfig(DJANGO_VARSAYILAN_GUNLUK)

    assert logging.getLogger("django.request").level == logging.NOTSET  # ezildi

    apply_access_log_policy()

    request_logger = logging.getLogger("django.request")
    assert request_logger.level >= logging.ERROR
    assert request_logger.propagate is False


def test_erisim_logu_politikasi_yapilandirmadan_once_de_cagrilabilir() -> None:
    apply_access_log_policy()

    assert logging.getLogger("waitress").level >= logging.ERROR


def test_echo_kipi_ikinci_handler_ekler(tmp_path: Path) -> None:
    logger = configure_logging(tmp_path, echo=True)

    assert len(logger.handlers) == 2


def test_dizin_yoksa_olusturulur(tmp_path: Path) -> None:
    hedef = tmp_path / "a" / "logs"

    configure_logging(hedef)

    assert hedef.is_dir()


def test_logger_adi_paket_ile_hizali(tmp_path: Path) -> None:
    logger = configure_logging(tmp_path)

    assert logger.name == LOGGER_NAME
    assert LOGGER_NAME == "oab_defteri"


# ---------------------------------------------------------------------------
# Çöküş kaydı (aile iskeletinde 19.09.2026): PDF motorunun C katmanındaki çöküş süreci anında
# kapatıyor, `uygulama.log`a iz düşmüyordu.
# ---------------------------------------------------------------------------
def test_cokme_kaydi_ayrac_yazar_ve_tum_is_parcaciklarini_dosyaya_baglar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cagri: dict[str, Any] = {}

    def kaydet(file: Any = None, all_threads: bool = False) -> None:
        cagri["dosya"], cagri["tum"] = file, all_threads

    monkeypatch.setattr(faulthandler, "enable", kaydet)
    monkeypatch.setattr(logging_setup, "_crash_log_file", None)

    yol = enable_crash_log(tmp_path, "2026.9.0-beta.9")

    assert yol == tmp_path / CRASH_LOG_NAME
    assert cagri["tum"] is True
    assert Path(cagri["dosya"].name) == yol
    assert "OAB Defteri 2026.9.0-beta.9 açıldı" in yol.read_text(encoding="utf-8")


def test_cokme_kaydi_buyuyunce_kenara_alinir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(logging_setup, "_crash_log_file", None)
    kayit = tmp_path / CRASH_LOG_NAME
    kayit.write_text("x" * 600_000, encoding="utf-8")

    enable_crash_log(tmp_path, "deneme")

    assert (tmp_path / f"{CRASH_LOG_NAME}.1").stat().st_size == 600_000
    assert kayit.stat().st_size < 200


def test_gercek_yerel_cokmede_python_yigini_dosyaya_duser(tmp_path: Path) -> None:
    """AYRI süreçte gerçek bir bellek erişim ihlali: yığın `cokme.log`a düşer.

    Programdaki çöküş de böyleydi (Pango'da erişim ihlali — Python istisnası
    yok). Kayıt hangi işlevde öldüğünü (burada `evrak_basiliyor`) göstermeli.
    """
    betik = textwrap.dedent(
        f"""
        import faulthandler
        import sys
        from pathlib import Path

        sys.path.insert(0, {str(REPO)!r})
        from desktop.logging_setup import enable_crash_log

        enable_crash_log(Path({str(tmp_path)!r}), "deneme")

        def evrak_basiliyor():
            faulthandler._sigsegv()

        evrak_basiliyor()
        """
    )
    sonuc = subprocess.run(  # noqa: S603 — sabit argümanlar, kabuk yok
        [sys.executable, "-c", betik], capture_output=True, timeout=60
    )

    assert sonuc.returncode != 0, "alt süreç çökmedi"
    icerik = (tmp_path / CRASH_LOG_NAME).read_text(encoding="utf-8")
    assert "OAB Defteri deneme açıldı" in icerik
    assert "Segmentation fault" in icerik or "access violation" in icerik
    assert "evrak_basiliyor" in icerik
