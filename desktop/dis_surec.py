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

**Yeni pencere isteği pencerenin profiliyle karşılanır** (saha bulgusu K-yeni-1, Pardus 25.2, PR #11'in
paketi, 13.11.2026). Hakkında'daki "Lisansın resmî metni" bağlantısı tıklanınca hiçbir şey olmuyor,
her tıkta Qt "Can not adopt content from a different WebEngineProfile." basıyordu; `xdg-open`'a hiç
varılmıyordu. Kök neden pywebview 5.3.2'nin Qt kolundadır (`platforms/qt.py`, kaynaktan doğrulandı):
sayfa (`BrowserView.WebPage`) pencerenin kendi profiliyle kurulur (`QWebEngineProfile('pywebview')`,
`setPersistentStoragePath`), ama `createWindow` sayfanın `nav_handler`'ını döndürür;
`NavigationHandler` `QWebPage(page)` ile, yani ebeveyni sayfa olan ama VARSAYILAN profilli bir sayfa
olarak kurulur. Qt yeni pencerenin içeriğini başka profilin sayfasına aktaramaz (`QWebEnginePage`
`adoptNewWindow` bu iletiyle döner), `acceptNavigationRequest` hiç çağrılmaz. Kolun her sürümünde
böyledir: gizli kipte de profil `QWebEngineProfile()`'dur, varsayılan profil değildir.

`yeni_pencere_isleyicisini_bagla` Linux'ta, arka uç yüklenince ve pencere kurulmadan önce
`BrowserView.WebPage.createWindow`'u değiştirir (sayfanın dosya kutusuyla aynı yol,
`desktop/yerel_pencere.py` `yukleme_penceresini_bagla`): her istek için ana sayfanın profiliyle
(`sayfa.profile()`), ana sayfanın çocuğu olan yeni bir sayfa kurulur. Qt içeriği ona aktarır, gezinme
isteği o sayfanın `acceptNavigationRequest`'ine gelir; karar `yeni_pencere_karari`'dır:
- http/https dış adres pywebview'ın `OPEN_EXTERNAL_LINKS_IN_BROWSER` ayarına göre (varsayılanı
  açık, program değiştirmez) sistemin tarayıcısına gider: kolun modülündeki `webbrowser` adıyla, yani
  `dis_tarayiciyi_bagla`'nın koyduğu temiz ortamlı açıcıyla; ayar kapalıysa ana pencerede açılır
  (pywebview'ın davranışı);
- programın kendi kökeni (ana sayfanın şeması, adı ve portu) ve bu bilgisayarı gösteren adresler dış
  tarayıcıya verilmez, ana pencerede de açılmaz: reddedilir. Programın sunucusu oturum belirteci
  ister, tarayıcıda açılan sayfa çalışmazdı; programda böyle bağlantı yoktur. Bu bilgisayar: geri
  döngü ağı (127.0.0.0/8, `::1`), belirsiz adres (IPv4'ün dört sıfırlı adresi ve `::`; Linux'ta yerele bağlanır), bunların
  IPv4 eşlemli IPv6 yazılışı (`::ffff:127.0.0.1`; Python'un `ipaddress`'i eski 3.12 yama sürümlerinde
  bunu geri döngü saymıyordu, test kabının 3.12.16'sı sayar, paket hattı da yüzen
  `python:3.12-bullseye` etiketiyle son yamayı alır; gerilerse `test_yeni_pencere_karari` düşer),
  `localhost` ve `*.localhost` (RFC 6761 §6.3); sondaki nokta atılır (`localhost.`; bağımsız denetim
  14.11.2026). Ad `urlsplit`'ten küçük harfle gelir. `127.1` ya da `2130706433` gibi kısa yazılışlar
  buraya gelmez: Chromium adresi Qt'ye vermeden önce `127.0.0.1` biçimine çevirir (gerçek Qt'de
  ölçüldü, 14.11.2026);
- öteki şemalar (`file:`, `ftp:`, `ws:`, `data:`, `blob:`, `javascript:`, boş adres) reddedilir.
Sayfa her durumda gezinmeyi reddeder (`False`) ve kendini siler (`deleteLater`): yeni pencere açılmaz.
Günlüğe adres yazılmaz.

Windows'ta (EdgeChromium kolu) yol başkadır ve değişmez: `edgechromium.py` `on_new_window_request`
`NewWindowRequested`'i karşılar (`Handled = True`), ayar açıkken adresi `webbrowser.open`'a verir;
profil sorunu yoktur. O kol adresin şemasını ve kökenini süzmez; programın `target="_blank"`
bağlantıları yalnız sabit https adresleridir (`HakkindaPage.tsx`, `UpdatePanel.tsx`). Yeni pencere
isteği yalnız onlardan gelmez: program içi bir bağlantıya (React Router `<Link>`) Ctrl ya da orta
tuşla tıklanınca da gelir (`<Link>` değiştirici tuşta tarayıcının varsayılanına bırakır). Windows'ta
o istek sistemin tarayıcısını `http://127.0.0.1:<port>/<yol>` adresiyle açar; adreste ve tarayıcıda
oturum belirteci olmadığı için sunucu isteği 403 ile reddeder (`desktop/session_guard.py`), sayfa
çalışmaz. Linux kolu aynı isteği reddeder: iki platform burada ayrışır (bağımsız
denetim 14.11.2026; Windows koluna bu işte dokunulmadı, kullanıcıya raporlandı).
"""

from __future__ import annotations

import ipaddress
import logging
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Final, Literal
from urllib.parse import urlsplit

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

#: Yeni pencere isteğinin sistem tarayıcısına gidebilen şemaları (modül başlığı).
DIS_SEMALAR: Final = ("http", "https")
_YEREL_ADLAR: Final = frozenset({"localhost"})
#: `*.localhost` her zaman bu bilgisayardır (RFC 6761 §6.3; Chromium da öyle çözer).
_YEREL_SON_EK: Final = ".localhost"
#: `yeni_pencere_karari`'nın dönüşleri.
TARAYICIDA: Final = "tarayicida"
ANA_PENCEREDE: Final = "ana_pencerede"
REDDET: Final = "reddet"
YeniPencereKarari = Literal["tarayicida", "ana_pencerede", "reddet"]

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


def _yerel_mi(ad: str) -> bool:
    """Ad (`urlsplit`'in küçük harfli `hostname`'i) bu bilgisayarı mı gösteriyor (modül başlığı)?"""
    ad = ad.rstrip(".")
    if ad in _YEREL_ADLAR or ad.endswith(_YEREL_SON_EK):
        return True
    try:
        adres = ipaddress.ip_address(ad)
    except ValueError:
        return False
    return adres.is_loopback or adres.is_unspecified


def yeni_pencere_karari(adres: str, ana_adres: str, *, tarayicida: bool) -> YeniPencereKarari:
    """Yeni pencere isteğinin kararı (modül başlığı "Yeni pencere isteği")."""
    try:
        hedef = urlsplit(adres)
        ana = urlsplit(ana_adres)
        koken = (hedef.scheme, hedef.hostname, hedef.port)
        ana_koken = (ana.scheme, ana.hostname, ana.port)
    except ValueError:
        return REDDET
    if hedef.scheme not in DIS_SEMALAR or not hedef.hostname:
        return REDDET
    if koken == ana_koken or _yerel_mi(hedef.hostname):
        return REDDET
    return TARAYICIDA if tarayicida else ANA_PENCEREDE


def yeni_pencere_isleyicisi(arka_uc: Any) -> Callable[[Any, Any], Any]:
    """`BrowserView.WebPage.createWindow`'un yerine geçen yöntem (modül başlığı).

    Yeni sayfa ana sayfanın profiliyle kurulur; gezinme isteğine `yeni_pencere_karari` uygulanır.
    Dış adres kolun modülündeki `webbrowser` adıyla açılır (çağrı anında okunur: temiz ortamlı açıcı).
    """
    taban: Any = arka_uc.QWebPage
    ayarlar = arka_uc.settings

    class YeniPencereSayfasi(taban):  # type: ignore[misc]  # Qt sınıfı çalışma anında gelir
        def __init__(self, ana_sayfa: Any) -> None:
            super().__init__(ana_sayfa.profile(), ana_sayfa)
            self._ana_sayfa = ana_sayfa

        def acceptNavigationRequest(self, url: Any, _tur: Any, _ana_cerceve: Any) -> bool:  # noqa: N802
            try:
                adres = str(url.toString())
                karar = yeni_pencere_karari(
                    adres,
                    str(self._ana_sayfa.url().toString()),
                    tarayicida=bool(ayarlar.get("OPEN_EXTERNAL_LINKS_IN_BROWSER", True)),
                )
                if karar == TARAYICIDA:
                    arka_uc.webbrowser.open(adres, 2, True)
                elif karar == ANA_PENCEREDE:
                    self._ana_sayfa.setUrl(url)
                else:
                    logger.warning(
                        "Yeni pencere isteği reddedildi (program içi ya da dış olmayan adres)."
                    )
            except Exception as hata:  # noqa: BLE001 — Qt'nin yuvasından hata taşmasın
                logger.warning("Yeni pencere isteği karşılanamadı (%s).", type(hata).__name__)
            finally:
                self.deleteLater()
            return False

    def createWindow(sayfa: Any, _tur: Any) -> Any:  # noqa: N802 — Qt adı
        return YeniPencereSayfasi(sayfa)

    return createWindow


def yeni_pencere_isleyicisini_bagla(arka_uc: Any, *, platform: str | None = None) -> bool:
    """Linux: pywebview Qt kolunun yeni pencere isteğini pencerenin profiline bağlar (modül başlığı).

    Arka uç yüklenince, sayfa kurulmadan önce çağrılır (`desktop.window.open_window`). Windows'ta (ve
    macOS'ta) hiçbir şey yapmaz.
    """
    sistem = sys.platform if platform is None else platform
    if _windows_mu(sistem) or sistem == "darwin":
        return False
    arka_uc.BrowserView.WebPage.createWindow = yeni_pencere_isleyicisi(arka_uc)
    return True
