"""PyInstaller çalışma-zamanı kancası — paketlenmiş uygulamanın ortamını kurar.

BU DOSYADAKİ WINDOWS YOLU BU ORTAMDA DOĞRULANMADI — ilk Windows koşusunda
sınanacak. Linux yolu (`OD_FRONTEND_DIR`) debian:11 + debian:12 kurulum
provalarında koşturuldu.

Kanca, giriş betiğinden (`giris.py`) ÖNCE çalışır; yaptığı işler "ilk
import'tan önce ortam değişkeni set etmek" gerektirdiği için başka bir yere
konulamaz:

1. **WeasyPrint DLL dizini (yalnız Windows).** WeasyPrint pango/harfbuzz/
   fontconfig kütüphanelerini çalışma anında `LoadLibrary` ile açar;
   paketleyici bunları statik çözümlemeyle göremediği için DLL'ler paket
   köküne ayrıca kopyalanır (`packaging/windows/dll_kapanisi.py`). WeasyPrint
   ≥60 `WEASYPRINT_DLL_DIRECTORIES` değişkenini resmen destekler ve bu değişken
   `weasyprint` import edilmeden ÖNCE dolu olmalıdır.

2. **Fontconfig yapılandırması (iki sistem).** Evrak iki sistemde de paketli yazı
   tipleriyle dizilir, sistem yazı tipi dizini taranmaz (tasarım §9.1-8; "fontconfig
   tuzağı": yalnız gömülü DejaVu Sans ve evrakın Liberation Serif'i). Paketteki
   `fonts.conf.tmpl` şablonu, YAZILABİLİR bir önbellek dizini (Windows'ta
   `%LOCALAPPDATA%\\OABDefteri\\cache\\fontconfig`) ve gömülü font dizini işlenerek
   kullanıcının önbellek dizinine yazılır. Kurulum dizini salt-okunur olabileceği
   için şablon paketin içinde İŞLENMEZ.
   - Windows: `FONTCONFIG_FILE` oraya bakar (mingw DLL'i değişkeni görmediği için asıl
     güvence paket içi `etc/fonts/fonts.conf`'tur; bkz. `fonts.paket.conf`).
   - Linux: süreç geneli `FONTCONFIG_FILE` KURULMAZ (Qt pencere yazı tipleri sistem
     yapılandırmasında kalır); yol `OD_EVRAK_FONTCONFIG` ile bildirilir ve yalnız
     evrakın WeasyPrint yazı tipi yapılandırması ondan kurulur
     (`shared.pdf.font_yapilandirmasi`).

3. **Frontend dizini (her platform).** Derlenmiş SPA paket içinde
   `frontend/dist` altındadır; Django tarafı bu yolu `OD_FRONTEND_DIR`
   değişkeninden okur.

4. **Qt platformu (yalnız Linux): xcb.** `QT_QPA_PLATFORM` boşsa `xcb` yazılır; dışarıdan
   verilen değer ezilmez (sahada teşhis için). Gerekçe (denetim bulgusu 13.11.2026):
   `libwayland-client` artık pakete gömülmez, sistemden alınır
   (`packaging/linux/sistem_kutuphaneleri.py`). Eskiden gömülü bullseye kopyası (Wayland
   1.18) Qt 6.8'in Wayland eklentisinin istediği `wl_proxy_marshal_flags`'i (1.20)
   vermiyordu (`ldd -r`: undefined symbol): Wayland yolu hiç çalışamazdı. Sistem kopyasıyla
   eklenti, libwayland-cursor0 ve libwayland-egl1'in kurulu olduğu her makinede
   (GNOME/GTK masaüstleri) eksiksiz bağlanır ve Qt `XDG_SESSION_TYPE=wayland` oturumunda
   onu xcb'den ÖNCE yükler (debian:13'te `QT_DEBUG_PLUGINS=1` ile görüldü, 13.11.2026);
   pencere hiç sınanmamış yola, WebEngine'in Wayland/EGL çizimine geçerdi. Sabitleme
   sınanmış pencere yolunu (xcb + GLX; saha: Pardus 25 XFCE) korur, Wayland oturumunda
   pencere XWayland üzerinden açılır. Değişken dış süreçlere geçmez: kanca değeri kendisi
   yazdıysa `OD_QT_PLATFORM_KANCADAN=1` bırakır, `desktop.dis_surec.temiz_ortam` programın
   açtığı süreçlerin ortamından (kdialog, tarayıcı) ikisini de atar; dışarıdan verilmiş değer
   onlara da geçer (saha bulgusu K-P2, 13.11.2026). Wayland yolunu açmak gerçek pencere
   sınaması ister.

Kancadaki hiçbir hata programı durdurmaz: eksik font yapılandırması PDF'i
bozar ama birlik kayıtlarına erişimi engellememeli. Sorunlar günlüğe değil
(günlük henüz kurulmadı) `OD_RTHOOK_UYARI` değişkenine yazılır.

Aile iskeletindeki yükseltilmiş güvenlik duvarı yardımcı kipi (UAC) ağ
kataloğuyla birlikte söküldü: program ağ servisi sunmaz (tasarım §4.1).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ENV_WARNING = "OD_RTHOOK_UYARI"
ENV_FRONTEND_DIR = "OD_FRONTEND_DIR"
ENV_WEASYPRINT_DLL = "WEASYPRINT_DLL_DIRECTORIES"
#: `shared.pdf.ENV_EVRAK_FONTCONFIG` ile aynı ad (kanca backend'i içe aktarmaz).
ENV_EVRAK_FONTCONFIG = "OD_EVRAK_FONTCONFIG"
#: Linux paketinin sınanmış pencere yolu (modül belgesi, madde 4).
ENV_QT_PLATFORM = "QT_QPA_PLATFORM"
QT_PLATFORM_LINUX = "xcb"
#: Kanca platformu kendisi kurduysa bırakılan işaret (`desktop.dis_surec` ile aynı ad).
ENV_QT_PLATFORM_KANCADAN = "OD_QT_PLATFORM_KANCADAN"

_FONTS_CONF_TEMPLATE = "fonts.conf.tmpl"
_FONTS_CONF = "fonts.conf"


def _bundle_root() -> Path:
    """Paketlenmiş kaynakların kökü (`sys._MEIPASS`)."""
    bundle = getattr(sys, "_MEIPASS", None)
    return Path(str(bundle)) if bundle else Path(__file__).resolve().parent


def _warn(message: str) -> None:
    """Uyarıyı ortam değişkenine biriktirir (günlük henüz kurulmadı)."""
    current = os.environ.get(ENV_WARNING, "")
    os.environ[ENV_WARNING] = f"{current} | {message}" if current else message


def _cache_root() -> Path:
    """Yazılabilir önbellek dizini — masaüstü kabuğuyla AYNI yerleşim."""
    try:
        from desktop.paths import resolve_app_paths

        return resolve_app_paths().cache
    except Exception:  # noqa: BLE001 — kanca hiçbir koşulda açılışı durdurmaz
        fallback = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or "."
        return Path(fallback) / "OABDefteri" / "cache"


def announce_frontend_dir(root: Path) -> None:
    """Derlenmiş SPA'nın yolunu `OD_FRONTEND_DIR` ile Django'ya bildirir."""
    dist = root / "frontend" / "dist"
    if dist.is_dir():
        os.environ.setdefault(ENV_FRONTEND_DIR, str(dist))
    else:
        _warn(f"Arayüz dosyaları bulunamadı: {dist}")


def announce_weasyprint_dll_dirs(root: Path) -> None:
    """WeasyPrint'in arayacağı DLL dizinlerini bildirir (Windows)."""
    candidates = [root, root / "dll"]
    existing = [str(path) for path in candidates if path.is_dir()]
    if existing:
        os.environ.setdefault(ENV_WEASYPRINT_DLL, os.pathsep.join(existing))


def write_fontconfig(root: Path, cache_root: Path) -> Path | None:
    """Gömülü fontları gösteren `fonts.conf`'u yazılabilir dizine üretir; yazılamazsa `None`.

    Şablondaki `@FONT_DIR@` ve `@CACHE_DIR@` yer tutucuları doldurulur. Dosya
    her açılışta yeniden yazılır: kurulum dizini değişmiş (taşınabilir zip başka
    bir klasöre açılmış) olabilir.
    """
    template = root / _FONTS_CONF_TEMPLATE
    if not template.is_file():
        _warn(f"Font yapılandırma şablonu bulunamadı: {template}")
        return None

    font_dir = root / "fonts"
    cache_dir = cache_root / "fontconfig"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        content = template.read_text(encoding="utf-8")
        content = content.replace("@FONT_DIR@", escape(font_dir.as_posix()))
        content = content.replace("@CACHE_DIR@", escape(cache_dir.as_posix()))
        target = cache_root / _FONTS_CONF
        target.write_text(content, encoding="utf-8")
    except OSError as error:
        _warn(f"Font yapılandırması yazılamadı: {error}")
        return None
    return target


def setup_fontconfig(root: Path, cache_root: Path) -> Path | None:
    """Windows: üretilen `fonts.conf`'u süreç geneli `FONTCONFIG_FILE` yapar."""
    target = write_fontconfig(root, cache_root)
    if target is not None:
        os.environ["FONTCONFIG_FILE"] = str(target)
        os.environ["FONTCONFIG_PATH"] = str(target.parent)
    return target


def announce_evrak_fontconfig(root: Path, cache_root: Path) -> Path | None:
    """Linux: üretilen `fonts.conf`'u yalnız evrakın yazı tipi yapılandırmasına bildirir.

    Süreç geneli `FONTCONFIG_FILE` değişmez; `shared.pdf.font_yapilandirmasi` WeasyPrint'in
    yapılandırmasını bu dosyayla kurar (sistem yazı tipi dizini taranmaz, tasarım §9.1-8).
    """
    target = write_fontconfig(root, cache_root)
    if target is not None:
        os.environ[ENV_EVRAK_FONTCONFIG] = str(target)
    return target


def pin_qt_platform() -> None:
    """Linux: Qt'yi sınanmış xcb yoluna sabitler; dışarıdan verilen değer ezilmez.

    Değeri kanca yazdıysa işaret bırakır: dış süreçler onu devralmaz (modül belgesi, madde 4).
    """
    if ENV_QT_PLATFORM not in os.environ:
        os.environ[ENV_QT_PLATFORM] = QT_PLATFORM_LINUX
        os.environ[ENV_QT_PLATFORM_KANCADAN] = "1"


def setup() -> None:
    """Kancanın tüm adımları (test edilebilirlik için ayrı fonksiyon)."""
    root = _bundle_root()
    announce_frontend_dir(root)
    if sys.platform.startswith("win"):
        announce_weasyprint_dll_dirs(root)
        setup_fontconfig(root, _cache_root())
    else:
        pin_qt_platform()
        announce_evrak_fontconfig(root, _cache_root())


setup()
