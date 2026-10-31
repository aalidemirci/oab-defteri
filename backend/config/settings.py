"""OAB Defteri — Django ayarları (tek dosya, tek bilgisayarda çalışan masaüstü uygulama).

Ağ-merkezli bir sunucu uygulamasının çok dosyalı ayar düzeninin
(config/settings/{base,dev,prod}.py) aksine burada TEK dosya yeterli: program tek
bilgisayarda çalışır ve bu ayarların sürdüğü YÖNETİM sunucusu yalnız 127.0.0.1'i
dinler (girişsiz yüzey bu varsayıma dayanır). Program ağ servisi sunmaz: yönetim
sunucusu yalnız 127.0.0.1'de, rastgele portta ve oturum belirteciyle dinler; hiçbir
port okul ağına açılmaz. Dış istek yalnız kullanıcının başlattığı güncelleme
denetiminden çıkar (tasarım §4.1). Sırlar `django-environ` OLMADAN doğrudan `os.environ` üzerinden okunur
(bağımlılık yüzeyi küçük tutulur).
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Veri dizini — masaüstü paket kurulumunda platform veri dizinine bağlanır
# ---------------------------------------------------------------------------
# `OD_DATA_DIR` env değişkeni ile geçersiz kılınabilir (Electron/PyInstaller
# paketleyicisi `platformdirs.user_data_dir()` sonucunu buraya verecek).
# Varsayılan geliştirmede `backend/data/` (repo içi, .gitignore'da).
DATA_DIR = Path(os.environ.get("OD_DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _bool_env(name: str, default: bool) -> bool:
    """Basit boolean env okuyucu (django-environ yok — settings sade kalsın)."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------------------
# Güvenlik
# ---------------------------------------------------------------------------
# Yerel tek-kullanıcılı masaüstü uygulaması — ağ üzerinden erişilmez, bu yüzden
# sabit bir geliştirme anahtarı güvenlik riski oluşturmaz (kriptografik oturum
# yok). Üretim paketlemesinde `OD_SECRET_KEY` env ile geçersiz kılınabilir.
SECRET_KEY = os.environ.get(
    "OD_SECRET_KEY",
    "django-insecure-oab-defteri-yerel-masaustu-gelistirme-anahtari",
)

# Varsayılan FALSE (KVKK): DEBUG hata sayfası yerel değişkenlerdeki ham
# TCKN/telefonu döker — paketlenmiş uygulamada asla açık kalmamalı. Geliştirme
# ortamı docker-compose.yml'de OD_DEBUG=1 ile açar.
DEBUG = _bool_env("OD_DEBUG", False)

# Kabul edilen Host adları (tasarım §4.1, §4.3 tehdit 2, §13 D46). Masaüstü kabuğu
# açılışta `OD_SESSION_TOKEN` verir: o zaman YALNIZ loopback adları kabul edilir
# (DNS rebinding'e karşı). Vite geliştirme proxy'si Docker Compose ağında servise
# ``backend`` adıyla ulaşır (frontend/vite.config.ts); bu ad yalnız belirteç BOŞKEN
# (geliştirme, test) eklenir. Koşul oturum belirteci middleware'iyle aynıdır (aşağıda).
LOOPBACK_HOSTLARI = ("127.0.0.1", "localhost")
GELISTIRME_HOSTU = "backend"


def izinli_hostlar(environ: Mapping[str, str]) -> list[str]:
    """`ALLOWED_HOSTS`: loopback adları; belirteç boşsa geliştirme ağının servis adı da."""
    hostlar = list(LOOPBACK_HOSTLARI)
    if not environ.get("OD_SESSION_TOKEN"):
        hostlar.append(GELISTIRME_HOSTU)
    return hostlar


ALLOWED_HOSTS = izinli_hostlar(os.environ)

# ---------------------------------------------------------------------------
# Uygulamalar
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.okul",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Yedekten geri yükleme uygulandıktan sonra "yeniden başlat" kapısı: süreç
    # içi durum (bellekteki anahtar, bekleyen göçler) diskteki veriyi artık
    # tarif etmez; tüm API 503 restart_required ile kesilir. Kilit kapısından
    # ÖNCE durur — geri yükleme kilit durumunu da bayatlatır.
    "apps.okul.restart_gate.RestartRequiredMiddleware",
    # Kilit kapısı (tasarım §4.3 tehdit 8, §4.4.3): güvenlik dosyası kayıpken (423
    # guvenlik_dosyasi_kayip) ve kilit açılmadıysa (423 locked) veri uçlarını
    # keser. Parola hiç kurulmamışsa kapı geçirir; kişi yazan uçları izin
    # sınıfı 409 parola_gerekli ile keser.
    "apps.okul.lock_middleware.AppLockMiddleware",
    # Kip kapısı (tasarım §4.4): kilit açık ve kip görevliyken izin listesi
    # dışındaki /api/ isteklerini 403 kip_yetkisiz ile keser; X-OD-Etkinlik
    # başlıklı istekte yönetici kipinin boşta sayacını tazeler. Kilit
    # kapısından SONRA durur: kilitliyken (423) istek buraya gelmez.
    "apps.okul.kip_middleware.KipMiddleware",
]

# Yerel oturum belirteci koruması (tasarım §4.3 tehdit 1). API'de istek başına
# kimlik doğrulaması bu belirteçtir: o olmasa, gömülü sunucu ayakta iken aynı
# makinedeki BAŞKA bir işlem 127.0.0.1'e istek atıp kilit açıkken birlik ve
# kişi verisini okuyabilirdi. Masaüstü başlatıcısı
# (`desktop/main.py`) açılışta rastgele bir belirteç üretip `OD_SESSION_TOKEN`
# ile verir; middleware belirteçsiz istekleri 403'ler.
# Geliştirme/test koşusunda değişken boştur → middleware HİÇ yüklenmez, yani
# backend'in `desktop` paketine bağımlılığı YOKTUR.
if os.environ.get("OD_SESSION_TOKEN"):
    MIDDLEWARE.insert(0, "desktop.session_guard.SessionTokenMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Veritabanı — SQLite (tek bilgisayarda çalışan masaüstü uygulama; Postgres yok)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {
            # WAL: eşzamanlı okuma/yazım; foreign_keys: Django varsayılan olarak
            # açar ama açıkça belirtmek niyeti netleştirir; busy_timeout: kilit
            # çakışmasında 5 sn bekle (masaüstü uygulamada tek süreç ama arka
            # plan görevi olabilir). synchronous=FULL (tasarım §4.3 tehdit 18):
            # WAL+NORMAL tutarlıdır ama elektrik kesintisinde son işlemleri geri
            # alabilir; bu, girilmiş bir gelir-gider kaydının ya da karar
            # taslağının sessizce kaybolması demektir. Yazma hacmi düşük olduğundan
            # her commit diske senkronlanır.
            # secure_delete=ON (tasarım §5.3): silinen ve güncellenen içerik
            # serbest sayfalarda okunur biçimde kalmaz, sıfırla ezilir (ör.
            # anonimleştirilen gerekçe metni, silinen kişinin eski satırı).
            "init_command": (
                "PRAGMA journal_mode=WAL;"
                "PRAGMA foreign_keys=ON;"
                "PRAGMA busy_timeout=5000;"
                "PRAGMA synchronous=FULL;"
                "PRAGMA secure_delete=ON;"
            ),
            "transaction_mode": "IMMEDIATE",
        },
        # Test veritabanı DOSYA TABANLIDIR (aile iskeletinden; orada gerekçe, ayrı
        # `mode=ro` bağlantı açan ve F1a-2'de sökülen ağ kataloğuydu — ayar aynen
        # korunur, bellek içi VT'ye geçiş ayrı karardır). Dosya sistemin geçici
        # dizinindedir: her `docker compose run` kabının kendi /tmp'si vardır,
        # paralel koşular aynı dosyayı paylaşmaz; depoya ve veri dizinine
        # (`backend/data/`) hiçbir şey yazılmaz.
        "TEST": {"NAME": str(Path(tempfile.gettempdir()) / "oab-defteri-test.sqlite3")},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Yerelleştirme
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Statik dosyalar (whitenoise — ayrı web sunucusu yok)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = DATA_DIR / "static"
# WhiteNoise dizin yoksa her istekte uyarı basar; açılışta oluşturmak yeterli.
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# Derlenmiş SPA. Masaüstü penceresi kök URL'yi açar; burası servis edilmezse
# kullanıcı programı değil Django hata sayfasını görür (aile iskeletinin denetiminde
# yakalandı). Paketlenmiş çalışmada PyInstaller çalışma-zamanı kancası
# OD_FRONTEND_DIR'i doldurur; geliştirmede depodaki frontend/dist kullanılır.
FRONTEND_DIR = Path(os.environ.get("OD_FRONTEND_DIR", str(BASE_DIR.parent / "frontend" / "dist")))
# WhiteNoise SPA varlıklarını (/assets/…) doğrudan verir; index.html'i istemci
# tarafı rotalar için config/urls.py'deki catch-all döndürür.
WHITENOISE_ROOT = FRONTEND_DIR
WHITENOISE_INDEX_FILE = True

# ---------------------------------------------------------------------------
# Medya (kullanıcı dosyaları — veri dizini altında)
# ---------------------------------------------------------------------------
MEDIA_ROOT = DATA_DIR / "media"

# Dosya eki yükleme sınırı (MB) — aile iskeletinden gelen varsayılan.
MAX_UPLOAD_SIZE_MB = int(os.environ.get("OD_MAX_UPLOAD_SIZE_MB", "20"))
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
# DRF kimlik doğrulaması kullanılmaz: istek kapıları ara katmandadır (oturum
# belirteci, kilit, kip). Kişisel hesaplar (T1) F1b'de oturum katmanıyla gelir
# (plan §2.2 adım 1). DEFAULT_AUTHENTICATION_CLASSES boş + UNAUTHENTICATED_USER
# None: DRF hiçbir kimlik doğrulama denemesi yapmaz.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 25,
    # `{code, message, fields}` hata sözleşmesi (tasarım §4.3; FE lib/api.ts bunu bekler).
    "EXCEPTION_HANDLER": "shared.exceptions.od_exception_handler",
}
