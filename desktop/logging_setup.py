"""Uygulama günlüğü — erişim logu KAPALI, PII yazılmaz.

Aile iskeletinin denetim bulgusu: `?search=<öğrenci adı>` gibi sorgu dizeleri istek
loglarına düşerse, kişisel veri düz metin olarak diske yazılır. Gömülü sunucuda
erişim logu üretmenin hiçbir faydası yok (tek kullanıcı, tek makine), zararı var
→ waitress/Django istek günlükçüleri susturulur.

Uygulama günlüğü YALNIZ veri dizinindeki `logs/` altına yazılır (kurulum
dizinine değil — orası salt-okunur olabilir). Sigorta olarak biçimlendirici
mesajlardaki sorgu dizelerini kırpar: bir kütüphane yine de URL loglarsa
`?search=...` bölümü diske ulaşmaz.

Ev dizini (kullanıcı kararı 06.11.2026 "Biçimleyici silsin"): Windows'ta ev dizininin yolu hesap
adını taşır, hesap adı çoğu bilgisayarda kişinin adıdır. Yığın izleri ve ham `OSError` metinleri
yolu tam verir; çağıranda tek tek kırpmak bir yeri unuturdu. Biçimlendirici her satırın ÇIKTISINDA
ev dizinini `~` yapar: bütün satırlar tek yerden kapanır. Tek ters bölü, `repr`'deki çift ters bölü
ve düz bölü aynı yoldur; Windows'ta büyük-küçük harf ayrılmaz. Ev dizini okunamıyorsa, kök dizinse
ya da mutlak değilse hiçbir şeye dokunulmaz: bütün yolları `~` yapmaktansa kırpmamak yeğdir. Adı
sürdüren yol başka bir dizindir (`/root` yolu `/rootfs`'u kırpmaz). Boşluk sınır sayılır, çünkü
iletide yolun ardından söz gelir: "Ali" hesabında başka hesabın "Ali Veli" dizini `~ Veli` olur.
Çökme günlüğü (`faulthandler`) bu yoldan geçmez: dosyaya süreç kendisi yazar, yalnız kod konumu
taşır (`enable_crash_log`).
"""

from __future__ import annotations

import faulthandler
import logging
import logging.handlers
import os
import re
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path, PureWindowsPath
from typing import TextIO

LOGGER_NAME = "oab_defteri"
LOG_FILE_NAME = "uygulama.log"
CRASH_LOG_NAME = "cokme.log"

_CRASH_LOG_MAX_BYTES = 512_000
# `faulthandler` dosyanın tanıtıcısını kullanır; dosya süreç ömrünce açık kalmalı.
_crash_log_file: TextIO | None = None
#: Oturum başlığının altındaki not, yalnız Windows'ta (`enable_crash_log`).
_CRASH_LOG_WINDOWS_NOTU = (
    "Not: Program kendiliğinden kapanmadıysa bu kayıtlar çökme değildir; gömülü pencere bileşeninin "
    "yakalanan hatalarıdır."
)

_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 3
_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

# Sorgu dizesi: "?" ile başlar, boşluk/tırnak/satır sonuna kadar sürer.
_QUERY_RE = re.compile(r"\?[^\s\"']*")

# Yol ayırıcısı: tek ters bölü, `repr`'deki çift ters bölü ve düz bölü aynı yoldur.
_AYIRICI = r"[\\/]+"
# Dizin adı sürüyorsa eşleşme geçersizdir; cümleyi bitiren nokta ad sayılmaz.
_AD_SURUYOR = r"(?![\w\-]|\.\w)"
_SURUCU_RE = re.compile(r"[A-Za-z]:")

# İstek günlüğü üreten kütüphane günlükçüleri (PII riski).
_ACCESS_LOGGERS = ("waitress", "waitress.queue", "django.server")

# `configure_logging` tarafından kurulan dosya handler'ı — `apply_access_log_policy`
# yeniden uygulanırken aynı dosyaya bağlanabilsin diye saklanır.
_file_handler: logging.Handler | None = None


def _ev_dizini() -> str:
    """Kullanıcının ev dizini; okunamazsa `RuntimeError` yükselir."""
    return str(Path.home())


def _yerel_uygulama_verisi() -> str:
    """Windows'ta `%LOCALAPPDATA%`; tanımsızsa `KeyError` yükselir (`gunluk_dosyasi_yeri`)."""
    return os.environ["LOCALAPPDATA"]


def _ev_deseni(okuyucu: Callable[[], str], *, windows: bool) -> re.Pattern[str] | None:
    """Ev dizininin yazımlarını yakalayan desen; dokunulmayacak dizinde `None` (modül başlığı)."""
    try:
        ev = okuyucu()
    except (OSError, RuntimeError, KeyError):
        return None
    parcalar = [parca for parca in re.split(_AYIRICI, ev) if parca]
    surucu = bool(parcalar) and _SURUCU_RE.fullmatch(parcalar[0]) is not None
    kokten = ev.startswith(("\\", "/"))
    if not (surucu or kokten) or len(parcalar) <= int(surucu):
        return None
    on = r"(?<![\w.\-])" if surucu else rf"(?<![\w.\-\\/]){_AYIRICI}"
    govde = _AYIRICI.join(re.escape(parca) for parca in parcalar)
    return re.compile(on + govde + _AD_SURUYOR, re.IGNORECASE if windows else 0)


def gunluk_dosyasi_yeri(
    log_dir: Path,
    *,
    platform: str | None = None,
    ev_dizini: Callable[[], str] = _ev_dizini,
    yerel_veri: Callable[[], str] = _yerel_uygulama_verisi,
) -> str:
    """Hata iletilerinin günlük dosyasını anışı (kullanıcı metni; sözlük §1 "Yedek").

    Günlük iki platformda da `paths.data`nın içinde değildir (`desktop.paths`): iletiler gerçek
    yerini yazar. Windows'ta yer `%LOCALAPPDATA%` ile başlar (BTR Dosya Gezgini'nin adres çubuğuna
    yapıştırır), Pardus'ta ev dizini `~` olur; ikisinde de hesap adı iletiye girmez. Bu kökün
    dışındaki yer (`--data-dir`, `XDG_STATE_HOME`) olduğu gibi yazılır; ileti onu taşıdığı için
    çağıran günlüğe ayrı metin verir (R1). Windows metni "veri klasöründeki logs/uygulama.log"
    diyordu; öteki iletilerin "veri klasörü" (`db-onceki-*`) `paths.data`dır, günlük onun içinde
    değil yanındadır (07.11.2026 sınama turu, kod okuması).
    """
    dosya = log_dir / LOG_FILE_NAME
    if (sys.platform if platform is None else platform).startswith("win"):
        windows_yolu = PureWindowsPath(str(dosya))
        try:
            goreli = windows_yolu.relative_to(PureWindowsPath(yerel_veri()))
        except (OSError, RuntimeError, KeyError, ValueError):
            return str(windows_yolu)
        return f"%LOCALAPPDATA%\\{goreli}"
    try:
        return f"~/{dosya.relative_to(ev_dizini())}"
    except (OSError, RuntimeError, KeyError, ValueError):
        return str(dosya)


class PiiSafeFormatter(logging.Formatter):
    """Çıktıda ev dizinini `~` yapar, sorgu dizesini kırpar (`?search=Ayşe` → `?…`).

    Ev dizinini okuyan işlev ve platform enjekte edilebilir: Windows yolu Docker'da da sınanır.
    """

    def __init__(
        self,
        fmt: str | None = None,
        *,
        ev_dizini: Callable[[], str] = _ev_dizini,
        windows: bool = os.name == "nt",
    ) -> None:
        super().__init__(fmt)
        self._ev_deseni = _ev_deseni(ev_dizini, windows=windows)

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        if self._ev_deseni is not None:
            text = self._ev_deseni.sub("~", text)
        return _QUERY_RE.sub("?…", text)


def configure_logging(
    log_dir: Path, *, level: int = logging.INFO, echo: bool = False
) -> logging.Logger:
    """Uygulama günlükçüsünü kurar ve döndürür. Tekrar çağrılabilir (idempotent)."""
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    # Kök günlükçüye yayılmasın: kök yapılandırması (varsa) PII filtresiz olabilir.
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = PiiSafeFormatter(_FORMAT)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / LOG_FILE_NAME,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if echo:
        # `--autotest` ve hata iletisi geri dönüşü için (konsol varsa görünür).
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    global _file_handler
    _file_handler = file_handler
    apply_access_log_policy()

    return logger


def enable_crash_log(log_dir: Path, app_version: str, *, platform: str | None = None) -> Path:
    """Yerel (C katmanı) çöküşte Python yığınını `logs/cokme.log`a yazdırır.

    Aile iskeletinin 19.09.2026 çöküş tanısı: PDF motorunun (WeasyPrint → Pango) C katmanındaki
    erişim ihlali süreci ANINDA kapattı; Python istisnası olmadığı için
    `uygulama.log`a hiçbir şey düşmedi ve hangi belgenin basıldığı
    bilinemedi. `faulthandler` o anda bütün iş parçacıklarının Python yığınını
    (dosya, satır, işlev) yazar. Yalnız KOD KONUMU yazılır — değişken değeri,
    ad, numara yazılmaz (KVKK).

    Her açılışta bir ayraç satırı eklenir: çöküş kaydı son ayracın altına düşer
    ve `uygulama.log`daki açılış satırıyla eşleştirilir. Dosya büyüdüyse
    (>500 KB) önceki içerik `cokme.log.1` olarak kenara alınır.

    Windows notu: Python'un yakalayıcısı işlenmiş sistem istisnalarını da yazar. 07.11.2026
    sınamasında gömülü pencere bileşeninin yakalanan COM hataları 8 dakikada 71 kayıt oldu, program
    çökmedi. Yakalayıcı kapatılmaz (gerçek çöküşün tek kanıtıdır); dosyayı okuyan yanılmasın diye
    Windows'ta her başlığın altına not yazılır.
    """
    global _crash_log_file
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / CRASH_LOG_NAME
    try:
        if _crash_log_file is None and path.exists():
            if path.stat().st_size > _CRASH_LOG_MAX_BYTES:
                path.replace(path.with_name(f"{CRASH_LOG_NAME}.1"))
        handle = path.open("a", encoding="utf-8")
        handle.write(
            f"=== {datetime.now():%Y-%m-%d %H:%M:%S} OAB Defteri {app_version} açıldı ===\n"
        )
        if (sys.platform if platform is None else platform).startswith("win"):
            handle.write(f"{_CRASH_LOG_WINDOWS_NOTU}\n")
        handle.flush()
        faulthandler.enable(file=handle, all_threads=True)
    except OSError:
        logging.getLogger(LOGGER_NAME).warning("Çöküş kaydı açılamadı.", exc_info=True)
        return path
    # Önceki tanıtıcı ancak faulthandler yeni dosyaya geçtikten SONRA kapatılır.
    onceki, _crash_log_file = _crash_log_file, handle
    if onceki is not None:
        onceki.close()
    return path


def apply_access_log_policy() -> None:
    """İstek (erişim) günlüklerini susturur — `django.setup()` SONRASINDA da çağrılır.

    Django kendi `DEFAULT_LOGGING`'ini `dictConfig` ile uygular; `dictConfig`,
    yapılandırmada adı geçen bir günlükçünün (`django`) ALTINDAKİ mevcut
    günlükçüleri sıfırlar: seviye NOTSET, handler listesi boş, `propagate=True`.
    Yani açılışta kurduğumuz `django.request` susturması `django.setup()` ile
    SİLİNİR ve istek yolları (DEBUG açıkken) konsola düşmeye başlar. Bu yüzden
    politika `django_bootstrap.prepare_django()` içinde yeniden uygulanır.
    """
    for name in _ACCESS_LOGGERS:
        access_logger = logging.getLogger(name)
        access_logger.setLevel(logging.ERROR)
        access_logger.propagate = False
        access_logger.handlers = [logging.NullHandler()]

    # Sunucu hataları teşhis edilebilsin: yol yazılır, sorgu dizesi kırpılır.
    # (Günlük dosyası henüz kurulmadıysa hiçbir yere yazılmaz — sessiz kalır.)
    request_logger = logging.getLogger("django.request")
    request_logger.setLevel(logging.ERROR)
    request_logger.propagate = False
    request_logger.handlers = [_file_handler] if _file_handler else [logging.NullHandler()]
