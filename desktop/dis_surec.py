"""Dış süreçlerin ortamı: programın açtığı her dış program temiz ortamla başlar (saha bulgusu K-P2).

**Sorun** (Pardus 25.2 = Debian 13, Linux paketi, 12.11.2026). PyInstaller'ın onedir paketi
açılışta kendi kütüphane yolunu süreç ortamına yazar ve kendini yeniden başlatır (PyInstaller
6.11.1 önyükleyicisi, `pyi_main.c` `_pyi_main_handle_posix_onedir` ve `pyi_utils_posix.c`
`pyi_utils_set_library_search_path`; kaynaktan doğrulandı): `LD_LIBRARY_PATH=<paket>/_internal`,
değişkenin önceki değeri varsa `LD_LIBRARY_PATH_ORIG`'de saklanır, yoksa `_ORIG` hiç yazılmaz.
Programın açtığı dış süreç (açılış hatası iletisindeki zenity) bu yolu devralır ve pakete gömülü
bullseye kütüphanelerine (glib, cairo, pango, harfbuzz, freetype, X11 …) bağlanır. Debian 13'ün
zenity'si böyle çöker, ileti hiç görünmez (debian:13 kabında paketle sınandı, 13.11.2026:
`LD_LIBRARY_PATH=_internal zenity` → "symbol lookup error: libcairo-script-interpreter.so.2:
undefined symbol: cairo_set_hairline", çıkış 127; değişken kaldırılınca pencere açılır). Programın
sistem tarayıcısına verdiği bağlantılar da (`xdg-open` → Firefox) aynı ortamı devralırdı.

**Çare** PyInstaller belgesinin "Launching external programs from the frozen application"
yöntemidir: dış sürecin ortamında `LD_LIBRARY_PATH`, `LD_LIBRARY_PATH_ORIG` varsa ona döner, yoksa
silinir. `temiz_ortam` bunu ve şunları yapar (yalnız Linux'ta; Windows'ta `None` döner, çağrı yeri
ortamı eskisi gibi devralır, Windows davranışı değişmez):

- **Donmuş pakette** (`sys.frozen`): `LD_LIBRARY_PATH` yukarıdaki kuralla düzelir, `_ORIG` atılır.
  Önyükleyicinin kendi süreçleri arasında haberleşme için yazdığı `_PYI_*` değişkenleri
  (`_PYI_ARCHIVE_FILE`, `_PYI_APPLICATION_HOME_DIR`, `_PYI_PARENT_PROCESS_LEVEL`,
  `_PYI_SPLASH_IPC`, `_PYI_LINUX_PROCESS_NAME`) atılır: başka bir PyInstaller programı onları
  arşiv adına bakarak zaten sıfırlar, öteki programlar için anlamsızdırlar. PyInstaller'ın PySide6
  kancası (`pyi_rth_pyside6.py`) `QT_PLUGIN_PATH` ve `QML2_IMPORT_PATH`'i eski değeri saklamadan
  paketin Qt dizinine yazar: değer paketin içini gösteriyorsa atılır. Yoksa açılan bir Qt
  programı (kdialog) sistem Qt'siyle paketin Qt 6.8.3 eklentilerini yüklemeye kalkardı.
- **`QT_QPA_PLATFORM`** yalnız çalışma zamanı kancası onu kendisi kurduysa atılır
  (`packaging/pyinstaller/rthook_od.py` madde 4; kanca bunu `OD_QT_PLATFORM_KANCADAN=1` ile
  bildirir, işaret de atılır). Dışarıdan verilmiş değer korunur.
- **Programın kendi değişkenleri ve içindeki bileşenlerin yazdıkları** dış sürece geçmez (bağımsız
  denetim 13.11.2026: debian:13 kabında paketin `QtWebEngineProcess`'inin ortamında görüldü):
  `OD_*` (programın değişkenleri: oturum belirteci `OD_SESSION_TOKEN`, veri ve uygulama dizini,
  arayüz dizini, evrakın yazı tipi yapılandırması, önceki oturum, kancanın işaretleri), `DJANGO_*`
  (`DJANGO_SETTINGS_MODULE`), `QTWEBENGINE_*` (pywebview `platforms/qt.py` pencereyi kurarken
  `QTWEBENGINE_CHROMIUM_FLAGS`'e `--use-fake-ui-for-media-stream` yazar: kamera ve mikrofon izni
  sorulmadan verilir; Arch/Manjaro/NixOS'ta `--no-sandbox` da; hata ayıklamada
  `QTWEBENGINE_REMOTE_DEBUGGING`), `PYSIDE6_*`, `QT_API` (qtpy'nin bağlayıcı seçimi, `load_qt`),
  Chromium'un `force_s3tc_enable`'ı ve boş `QT_STYLE_OVERRIDE` (pywebview ve `prepare_qt_application`
  yazar; boş değer zaten etkisizdir). QtWebEngine tabanlı bir tarayıcı (Falkon, Konqueror) bu
  bayraklarla açılsaydı o oturumda her site kamera ve mikrofonu sormadan alırdı. Kural ad ve önekle
  atar, izin listesi değildir: masaüstü oturumunun değişkenleri (`DISPLAY`, `DBUS_SESSION_BUS_ADDRESS`,
  `XDG_*`, `LANG` …) zenity'nin ve tarayıcının işidir, eksik bırakılmaz. Evrakın yazı tipi
  yapılandırması (`FONTCONFIG_FILE`, `shared.pdf.font_yapilandirmasi` PDF dizilirken kısa süre kurar)
  paketin dosyasını gösteriyorsa atılır: o anda açılan pencere yalnız evrakın iki yazı tipini görürdü.

Geliştirme ortamında (donmuş değil) `LD_LIBRARY_PATH` kullanıcınındır, dokunulmaz.

**Bütün dış süreçler buradan geçer.** Çağrı yerleri `subprocess`'e `env=temiz_ortam()` verir:
`desktop/dialogs.py` (açılış hatası iletisi), `desktop/yerel_pencere.py` (Linux'ta kaydetme ve Aç
pencereleri, zenity/kdialog) ve bu modüldeki bağlantı açıcısı. pywebview'ın Qt kolu sayfadaki dış
bağlantıyı (`target="_blank"`: Hakkında'daki lisans, güncellemedeki indirme sayfası) modülünün
`webbrowser` adıyla açar (`platforms/qt.py` `NavigationHandler`: yalnız `webbrowser.open`); Python'un
`webbrowser`'ı süreci ortamı vermeden başlatır. `dis_tarayiciyi_bagla` Linux'ta, arka uç yüklenince ve
pencere kurulmadan önce, o adı `TemizOrtamTarayicisi` ile değiştirir: bağlantı `xdg-open`'a temiz
ortamla gider; `xdg-open` yoksa pywebview'ın eski yolu (`webbrowser.open`) sürer. Python'un
`webbrowser` kaydına (`register`) dokunulmaz: kayıt sırası ilk kullanımda `xdg-settings`'i eski ortamla
çalıştırır ve ayrı iş parçacığında yapılan kayıt, aynı anda tıklanan bağlantıyla yarışıyordu
(`register_standard_browsers` sırayı boşaltıp `xdg-settings`'i beklerken `open` boş sırayı dolaşıp
`False` döner; bağımsız denetim 13.11.2026). Değişim eşzamanlıdır, `xdg-settings` hiç çalışmaz. Açılan
`xdg-open` arka plandaki (daemon) bir iş parçacığında beklenir: tarayıcı kapanana dek dönmeyebilir,
beklenmezse zombi kalırdı. Bu modül `webbrowser`'ı içe aktarmaz: ağ istemcisi kapısının izin
listesine (`backend/apps/okul/tests/test_dis_istek_kapilari.py` `IZINLI`) girmez. Kural
`desktop/tests/test_dis_surec.py`'de kaynak düzeyinde kilitlidir: yeni bir dış süreç çağrısı
`env=temiz_ortam()` vermezse ya da `subprocess`, `webbrowser`, `os.exec*` takma adla veya doğrudan
içe aktarılırsa test düşer.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Final

logger = logging.getLogger("oab_defteri.dis_surec")

#: PyInstaller önyükleyicisinin yazdığı kütüphane yolu ve sakladığı asıl değer (modül başlığı).
ENV_KUTUPHANE_YOLU: Final = "LD_LIBRARY_PATH"
ENV_KUTUPHANE_YOLU_ASIL: Final = "LD_LIBRARY_PATH_ORIG"
#: Önyükleyicinin kendi süreçleri arasındaki değişkenlerin ortak öneki.
PYI_ONEKI: Final = "_PYI_"
#: PyInstaller'ın PySide6 kancasının paketin Qt dizinine yazdığı değişkenler.
QT_PAKET_DEGISKENLERI: Final = ("QT_PLUGIN_PATH", "QML2_IMPORT_PATH")
#: Çalışma zamanı kancasının sabitlediği Qt platformu ve bunu kendisinin yaptığını bildiren işaret
#: (`packaging/pyinstaller/rthook_od.py` ile aynı adlar; kanca bu modülü içe aktarmaz).
ENV_QT_PLATFORM: Final = "QT_QPA_PLATFORM"
ENV_QT_PLATFORM_KANCADAN: Final = "OD_QT_PLATFORM_KANCADAN"
#: `desktop.session_guard.ENV_TOKEN` ile aynı ad (o modül Django'yu içe aktarır, burası aktarmaz).
ENV_OTURUM_BELIRTECI: Final = "OD_SESSION_TOKEN"  # noqa: S105 — değişken adı, sır değil
#: Evrakın yazı tipi yapılandırması (`shared.pdf.ENV_EVRAK_FONTCONFIG`) ve fontconfig'in değişkeni.
ENV_EVRAK_FONTCONFIG: Final = "OD_EVRAK_FONTCONFIG"
ENV_FONTCONFIG: Final = "FONTCONFIG_FILE"
#: Programın ve içindeki bileşenlerin değişkenleri: önekleri ve tam adları (modül başlığı).
PROGRAM_ONEKLERI: Final = ("OD_", "DJANGO_", "QTWEBENGINE_", "PYSIDE6_")
PROGRAM_DEGISKENLERI: Final = ("QT_API", "force_s3tc_enable")
#: pywebview'ın ve `prepare_qt_application`'ın boş yazdığı stil değişkeni.
ENV_QT_STIL: Final = "QT_STYLE_OVERRIDE"
#: Dış bağlantıyı açan araç.
BAGLANTI_ACICI: Final = "xdg-open"

BaglantiAcici = Callable[[str, int, bool], bool]


def _windows_mu(platform: str) -> bool:
    return platform.startswith("win")


def _paketin_icinde(deger: str, kok: str) -> bool:
    """Değişkenin değeri (yol listesi) paketin kökünün içini gösteriyor mu?"""
    kok_yolu = Path(kok)
    for parca in deger.split(os.pathsep):
        if not parca:
            continue
        yol = Path(parca)
        if yol == kok_yolu or kok_yolu in yol.parents:
            return True
    return False


def _programin_mi(ad: str, deger: str) -> bool:
    """Değişken programın ya da içindeki bileşenlerin mi (modül başlığı)?"""
    if ad.startswith(PROGRAM_ONEKLERI) or ad in PROGRAM_DEGISKENLERI:
        return True
    return ad == ENV_QT_STIL and deger == ""


def temiz_ortam(
    *,
    platform: str | None = None,
    ortam: Mapping[str, str] | None = None,
    donmus: bool | None = None,
    paket_koku: str | None = None,
) -> dict[str, str] | None:
    """Dış süreç için ortam; Windows'ta (ve macOS'ta) `None`: süreç ortamı eskisi gibi devralır.

    Süreç ortamının kopyası düzeltilir, `os.environ` değişmez (program kendi yolunda sürer).
    Parametreler testler içindir; varsayılanlar süreçten okunur (modül başlığı).
    """
    sistem = sys.platform if platform is None else platform
    if _windows_mu(sistem) or sistem == "darwin":
        return None
    yeni = dict(os.environ if ortam is None else ortam)
    if getattr(sys, "frozen", False) if donmus is None else donmus:
        asil = yeni.pop(ENV_KUTUPHANE_YOLU_ASIL, None)
        if asil is not None:
            yeni[ENV_KUTUPHANE_YOLU] = asil
        else:
            yeni.pop(ENV_KUTUPHANE_YOLU, None)
        for ad in [ad for ad in yeni if ad.startswith(PYI_ONEKI)]:
            del yeni[ad]
        kok = paket_koku if paket_koku is not None else getattr(sys, "_MEIPASS", None)
        if kok:
            for ad in QT_PAKET_DEGISKENLERI:
                if _paketin_icinde(yeni.get(ad, ""), str(kok)):
                    del yeni[ad]
    # İşarete ve evrakın yapılandırmasına program değişkenleri atılmadan bakılır.
    if ENV_QT_PLATFORM_KANCADAN in yeni:
        yeni.pop(ENV_QT_PLATFORM, None)
    evrak_fontlari = yeni.get(ENV_EVRAK_FONTCONFIG)
    if evrak_fontlari and yeni.get(ENV_FONTCONFIG) == evrak_fontlari:
        del yeni[ENV_FONTCONFIG]
    for ad in [ad for ad, deger in yeni.items() if _programin_mi(ad, deger)]:
        del yeni[ad]
    return yeni


class TemizOrtamTarayicisi:
    """pywebview'ın Qt kolunun `webbrowser` adının yerine geçer (modül başlığı).

    Kolun kullandığı tek yüzey `open(url, new, autoraise)`'dır. Bağlantı `xdg-open`'a temiz ortamla
    verilir; araç yoksa `yedek` (kolun eski `webbrowser.open`'ı) denenir, o da yoksa `False` döner.
    """

    def __init__(self, yedek: BaglantiAcici | None = None) -> None:
        self._yedek = yedek

    def open(self, url: str, new: int = 0, autoraise: bool = True) -> bool:
        sys.audit("webbrowser.open", url)
        arac = shutil.which(BAGLANTI_ACICI)
        if arac is None:
            logger.warning(
                "%s bulunamadı; bağlantı Python'un tarayıcı sırasına verildi.", BAGLANTI_ACICI
            )
            return self._yedek(url, new, autoraise) if self._yedek is not None else False
        try:
            surec = subprocess.Popen(  # noqa: S603 — sabit araç, kabuk yok; adres tek argümandır
                [arac, url],
                env=temiz_ortam(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as hata:
            logger.warning("Bağlantı sistemin tarayıcısında açılamadı (%s).", type(hata).__name__)
            return False
        # `xdg-open` tarayıcı kapanana dek dönmeyebilir: arka planda beklenir, zombi kalmaz.
        threading.Thread(target=surec.wait, name="od-xdg-open", daemon=True).start()
        return True


def dis_tarayiciyi_bagla(arka_uc: Any, *, platform: str | None = None) -> bool:
    """Linux: pywebview Qt kolunun `webbrowser` adını temiz ortamlı açıcıyla değiştirir.

    Arka uç yüklenince, pencere kurulmadan önce çağrılır (`desktop.window.open_window`); ikinci
    çağrı bir şey değiştirmez. Windows'ta (ve macOS'ta) hiçbir şey yapmaz. Hata pencereyi durdurmaz.
    """
    sistem = sys.platform if platform is None else platform
    if _windows_mu(sistem) or sistem == "darwin":
        return False
    asil = getattr(arka_uc, "webbrowser", None)
    if isinstance(asil, TemizOrtamTarayicisi):
        return True
    yedek = getattr(asil, "open", None)
    if not callable(yedek):
        logger.warning("Pencere bileşeninin dış bağlantı açıcısı bulunamadı.")
        return False
    arka_uc.webbrowser = TemizOrtamTarayicisi(yedek)
    return True
