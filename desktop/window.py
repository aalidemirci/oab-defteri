"""pywebview penceresi + pencere motoru denetimi (tasarım §1, §4.5).

**MSHTML düşüşü KODLA ENGELLİDİR.** pywebview, Windows'ta EdgeChromium (WebView2)
bulamazsa sessizce eski MSHTML (Internet Explorer) motoruna düşer; React 18 orada
çalışmaz ve kullanıcı boş beyaz bir pencere görür. Bu yüzden:
  1. Açılışta WebView2 runtime'ı kayıt defterinden aranır, yoksa Türkçe yönlendirme
     verilir ve pencere hiç açılmaz;
  2. `webview.start()` çağrısına GUI motoru AÇIKÇA verilir (`gui="edgechromium"`),
     böylece pywebview'ın kendi düşüş mantığı devreye giremez.

pywebview TEMBEL içe aktarılır: paket kurulu olmayan geliştirme/test ortamında bu
modül yine de import edilebilir ve testler koşar.

**Çarpı programı kapatır, onay sorulmaz** (T6, §4.5; `WindowController`).
pywebview 5.3.2'nin `closing` olayı pencere motorunun iş parçacığında ESZAMANLI
koşar (`Event(window, should_lock=True)`: `event.py` işleyiciyi çağıranda koşturur) ve
işleyicilerden biri `False` döndürürse kapanma iptal edilir (winforms `on_closing` →
`args.Cancel`, qt `closeEvent` → `event.ignore()`). OAB'de tepsi yoktur: uzun yazma işi
yokken işleyici kapanmayı iptal etmez, pencere kapanır, `webview.start` döner ve düzenli
kapanış sürer (`desktop/main.py`).

**Uzun iş sürerken kapanış bir kez ertelenir** (§4.2, TK5; plan F1b-3 "Uzun iş, çarpı, temiz
kapanış"). `on_closing` iş yapmaz: sayaç sıfır değilse `False` döner ve yardımcı iş parçacığını
başlatır. İşleyici pencere iş parçacığında koştuğu için içinden `evaluate_js` ya da `destroy`
çağrılmaz, pencere kilitlenirdi. Yardımcı iş parçacığı en çok `KAPANIS_BEKLEME_SN` bekler, sonra
kapanışı bir kez yapar (`destroy`'un tetiklediği `closing` geçer). Pencereyi gösterme ve
`od:kapanis-bekliyor` olayı ayrı bir iş parçacığındadır: `evaluate_js` sonucu süresiz bekleyebilir,
60 sn sınırını aşmasın. Bekleme sırasında gelen kapatma istekleri (ikinci çarpı, Çık, kurucunun
kapatma olayı, kanal, SIGTERM) beklemeye katılır. Windows oturum kapanışı da aynı yoldan geçer:
`closing` olayı nedeni taşımaz, kapanış bir kez, en çok 60 sn ertelenir (plan "Sorulmadı, tasarım
cevaplıyor"); iptali geri alan .NET işleyicisi yoktur. Sayaç okunamazsa kapanış beklemez (T6); temiz
kapanış işaretini kendi okuması belirler (`clean_shutdown.write_marker_if_idle`).

**Kaydetme yeri soran köprü** (`PencereKoprusu`; kullanıcı kararı 04.11.2026 "Şifreli yedeği
program kaydeder"). Ön yüz `window.pywebview.api.kaydetme_yeri_sor(ad)` ile sorar, dönen yolu
isteğin içinde sunucuya verir: masaüstü sunucuyu doğrudan çağırmaz (§4.1). pywebview 5.3.2'de js_api
çağrısı her seferinde yeni bir iş parçacığında koşar (`util.js_bridge_call`): pencere iş parçacığı
bekletilmez, dönüş sonrası `evaluate_js` ile ön yüze gider. `create_file_dialog`'un kaydetme
dönüşü iki platformda ayrıdır: WinForms düz metin, Qt tek öğeli demet verir, ikisi de iptalde
`None`'dır (`_secilen_yol` tek biçime indirir; metni dizi sanmak yolun ilk harfini verirdi). Qt
kolu tür süzgecini kaydetmede uygulamaz, uzantı eklemez; uzantıyı sunucu denetler. Seçilen yol
günlüğe yazılmaz: Windows yolu hesap adını taşır.

**Yedek dosyası soran köprü** (`yedek_dosyasi_sor`; kullanıcı kararı 06.11.2026 "Yedek dosyası
yüklenmez, programın Aç penceresiyle seçilir"; plan F1b-3). Geri yüklemede dosya gövdesi sunucuya
gitmez: ön yüz Aç penceresinin verdiği yolu küçük istekle yollar, sır waitress'in geçici dosyasına
inmez (`desktop/server.py` başlığı). Aç penceresinde iki platform da tek öğeli demet verir (WinForms
`tuple(dialog.FileNames)`, Qt `(self._file_name[0],)`), iptalde `None`'dır; `_secilen_yol` aynı işlevdir.
Qt kolu pencerenin başlığını `linux.openFile`'dan alır (`PENCERE_METINLERI`), tür süzgecini bu
pencerede uygular; Windows'ta başlığı işletim sistemi yazar. Süzgeç yalnız kolaylıktır, kullanıcı
başka dosya seçebilir: dosyanın yedek olup olmadığını sunucu okur.

**Dosyayı program kaydeder** (`dosya_kaydet`; kullanıcı kararı 07.11.2026 "Program kaydetsin"). PDF,
Excel ve kurulum dosyasını WebView'ın indirmesine bırakmak sonucu bilmez: Windows'ta kaydetme penceresi
açıkken ve iptalde de "kaydedildi" bildirimi çıkıyor, İndirilenler'de geçici dosya duruyor, Edge'in
indirme paneli açılıyordu; Pardus'ta 1 sn'den uzun açık pencerede blob adresi kapanıp dosya boş
kalabiliyordu. Ön yüz içeriği base64 metin olarak verir, köprü pencereyi açar, seçilen yere yazar,
yalnız durum döner (`kaydedildi`, `iptal`, `hata`). Yol ön yüze, günlüğe, yanıta girmez; içerik
günlüğe girmez: kurtarma belgesi anahtar taşır. İçerik pencereden önce çözülür, bozuksa pencere
açılmaz. Yazım atomiktir (`_atomik_yaz`): yarım dosya seçilen adda görünmez.

Tür süzgeci uzantıya göredir (`TUR_SUZGECLERI`); Windows'ta süzgecin uzantısını ve üzerine yazma
sorusunu pencere kendi yapar. Qt kolu kaydetmede süzgeç uygulamaz, uzantı eklemez: ad uzantısız
kaldıysa önerilen addaki uzantıyı köprü ekler. Noktalı son ek her zaman uzantı değildir (`_uzanti`):
programın adları tarihle biter, `Rapor_07.11.2026`nin `.2026`sı uzantı sayılsaydı dosya `.pdf`siz
yazılırdı. Pencere yalnız yazılan adı sormuştur: uzantı eklenen ad zaten varsa dosya ezilmez, pencere
kullanıcının seçtiği klasörde o adla yeniden açılır, soruyu pencere sorar.

**Son klasör.** Üç pencere de son seçilen klasörde açılır; klasör yalnız bellektedir,
süreç kapanınca unutulur, diske ve günlüğe yazılmaz. İptal onu değiştirmez; klasör artık yoksa (bellek
çekildi) ev dizinine düşülür. Kurtarma anahtarı belgesinin penceresi (`ev_klasorunde`) bunun dışındadır:
her seferinde ev dizininde açılır, son klasörü ne okur ne değiştirir (kullanıcı kararı 07.11.2026 "Hep ev
klasöründe"). Şifreli yedek USB belleğe kaydedildikten hemen sonra anahtar onun yanına önerilseydi,
bellek kaybolunca yedek de onu açan anahtar da birlikte giderdi; yedek de anahtarın yanına önerilmez.
"""

from __future__ import annotations

import base64
import logging
import os
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final, Protocol

from desktop.errors import WebViewUnavailableError
from desktop.paths import resource_root

logger = logging.getLogger("oab_defteri.window")

WINDOW_TITLE = "OAB Defteri"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 860
WINDOW_MIN_SIZE = (1024, 700)
WINDOW_ICON_FILE = "oab-defteri.ico"
WINDOW_APP_ID = "OABDefteri.Desktop"

# Microsoft Edge WebView2 Runtime'ın sabit ürün kimliği (Evergreen).
WEBVIEW2_CLIENT_ID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
_WEBVIEW2_KEYS = (
    ("HKLM", rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_CLIENT_ID}"),
    ("HKLM", rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_CLIENT_ID}"),
    ("HKCU", rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_CLIENT_ID}"),
)
# "0.0.0.0" burada bir IP değil, kaldırılmış runtime'ın bıraktığı SÜRÜM damgasıdır.
_EMPTY_VERSIONS = {"", "0.0.0.0"}  # noqa: S104

RegistryReader = Callable[[str, str, str], "str | None"]
DwmSetter = Callable[[int, int, bool], int]

_WEBVIEW2_MESSAGE = "Pencere açılamadı: Microsoft Edge WebView2 Çalışma Zamanı bulunamadı."
_WEBVIEW2_HINT = (
    "Programın kurulum klasöründeki 'MicrosoftEdgeWebView2Setup.exe' dosyasını çalıştırıp "
    "WebView2'yi kurun, sonra programı yeniden açın. Kurulum yetkiniz yoksa okul bilişim "
    "sorumlusundan 'WebView2 Runtime' kurulumunu isteyin."
)
#: Kaydetme ve Aç pencerelerinin tür süzgeci. pywebview açıklamada yalnız harf, rakam ve boşluk kabul
#: eder (`util.parse_file_type`); uymayan süzgeç pencereyi açmadan `ValueError` verirdi.
KAYDETME_SUZGECI = ("OAB Defteri yedeği (*.odbak)",)
#: `dosya_kaydet` penceresinin uzantıya göre tür süzgeci; açıklama kuralı yukarıdakinin aynısıdır.
TUR_SUZGECLERI: Final = {
    ".pdf": ("PDF belgesi (*.pdf)",),
    ".xlsx": ("Excel dosyası (*.xlsx)",),
}
#: Öteki uzantıların süzgeci: süzgeç hiç verilmezse pywebview İngilizce "All files" yazardı.
GENEL_SUZGEC: Final = ("Tüm dosyalar (*.*)",)
#: `dosya_kaydet`'in dönüşleri; ön yüze yalnız bunlar gider (modül başlığı).
KAYIT_KAYDEDILDI: Final = "kaydedildi"
KAYIT_IPTAL: Final = "iptal"
KAYIT_HATA: Final = "hata"
#: pywebview'ın kendi metinleri (`webview.start(localization=...)`). Qt kolu kaydetme ve Aç
#: pencerelerinin başlığını buradan alır (`qt.py`); Windows'ta başlığı işletim sistemi yazar.
#: `windows.fileFilter.allFiles` WebView2'nin indirme penceresinin tür kutusudur
#: (`edgechromium.py`): köprü sayfaya yetişmeden basılan düğmede `saveBlob` o yola düşer.
PENCERE_METINLERI: Final = {
    "global.saveFile": "Farklı kaydet",
    "linux.openFile": "Dosya aç",
    "windows.fileFilter.allFiles": "Tüm dosyalar",
}
#: Uzun iş sürerken kapanışın en çok bekleyeceği süre (tasarım §4.2, TK5).
KAPANIS_BEKLEME_SN: Final = 60.0
#: Süre enjekte edilen saatle ölçülür; sayaç bu aralıklarla sorulur (iş bitince hemen uyanır).
_BEKLEME_DILIMI_SN: Final = 1.0
#: Ön yüzün "İşlem bitiyor, program kendiliğinden kapanacak" penceresini açtıran DOM olayı.
KAPANIS_BEKLIYOR_OLAYI: Final = "od:kapanis-bekliyor"
_KAPANIS_BEKLIYOR_BETIGI: Final = (
    f"window.dispatchEvent(new CustomEvent('{KAPANIS_BEKLIYOR_OLAYI}'))"
)


class UzunIsBeklenebilir(Protocol):
    """Kapanışın kullandığı sayaç yüzeyi (`shared.bakim.UzunIsSayaci`; testte sahtesi verilir)."""

    @property
    def sayi(self) -> int: ...

    def sifirlanmasini_bekle(self, sure: float) -> bool: ...


def _read_registry_value(hive: str, subkey: str, value_name: str) -> str | None:
    """Windows kayıt defterinden tek bir değer okur (Windows dışında None)."""
    if sys.platform != "win32":
        return None
    import winreg

    hives = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}
    try:
        with winreg.OpenKey(hives[hive], subkey) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
    except OSError:
        return None
    return str(value)


def webview2_installed(*, registry_reader: RegistryReader | None = None) -> bool:
    """WebView2 Runtime kurulu mu? (Evergreen kaydındaki `pv` sürümüne bakar)"""
    reader = registry_reader or _read_registry_value
    for hive, subkey in _WEBVIEW2_KEYS:
        version = reader(hive, subkey, "pv")
        if version and version.strip() not in _EMPTY_VERSIONS:
            return True
    return False


def gui_backend_for(platform: str) -> str:
    """Platforma göre AÇIK GUI motoru — pywebview'ın sessiz düşüşünü engeller."""
    if platform.startswith("win"):
        return "edgechromium"  # asla "mshtml"
    if platform == "darwin":
        return "cocoa"
    # Pardus/Linux: pywebview'ın Qt arka ucu (PySide6 + QtWebEngine; bağlayıcı
    # `desktop/qt_kurulum.py::load_qt` içinde `QT_API` ile sabitlenir).
    return "qt"


def require_window_runtime(
    *,
    platform: str | None = None,
    registry_reader: RegistryReader | None = None,
) -> None:
    """Pencere motoru yoksa açılışı durdurur (Windows/WebView2)."""
    system = sys.platform if platform is None else platform
    if not system.startswith("win"):
        return
    if not webview2_installed(registry_reader=registry_reader):
        raise WebViewUnavailableError(_WEBVIEW2_MESSAGE, hint=_WEBVIEW2_HINT)


def import_webview() -> Any:
    import webview

    return webview


def _native_window_handle(window: Any) -> int | None:
    """pywebview/WinForms penceresinin HWND değerini güvenle çözer."""
    native = getattr(window, "native", None)
    handle = getattr(native, "Handle", None)
    if handle is None:
        return None
    try:
        return int(handle.ToInt64())
    except AttributeError:
        try:
            return int(handle)
        except (TypeError, ValueError):
            return None


def _dwm_set_titlebar(hwnd: int, attribute: int, dark: bool) -> int:
    """DWM başlık çubuğu temasını ayarlar; dönüş değeri Windows HRESULT'tur."""
    import ctypes
    from ctypes import wintypes

    enabled = wintypes.BOOL(bool(dark))
    return int(
        ctypes.windll.dwmapi.DwmSetWindowAttribute(  # type: ignore[attr-defined]
            wintypes.HWND(hwnd),
            wintypes.DWORD(attribute),
            ctypes.byref(enabled),
            ctypes.sizeof(enabled),
        )
    )


def set_windows_app_id(*, platform: str | None = None) -> bool:
    """Görev çubuğu gruplaması ve ikon çözümü için kararlı Windows uygulama kimliği."""
    system = sys.platform if platform is None else platform
    if not system.startswith("win"):
        return False
    try:
        import ctypes

        result = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(  # type: ignore[attr-defined]
            ctypes.c_wchar_p(WINDOW_APP_ID)
        )
    except (OSError, AttributeError):
        logger.warning("Windows uygulama kimliği atanamadı.", exc_info=True)
        return False
    return int(result) == 0


def app_icon_path(*, root: Path | None = None) -> Path | None:
    """Uygulama ikonu (.ico): paketli programda kökte, depoda `packaging/ikonlar/`.

    Spec ikonu paket köküne koyar (`oab_defteri.spec` → `datas`); kök
    `paths.resource_root()`'tur (PyInstaller'da `sys._MEIPASS`).
    """
    base = resource_root() if root is None else root
    for candidate in (base / WINDOW_ICON_FILE, base / "packaging" / "ikonlar" / WINDOW_ICON_FILE):
        if candidate.is_file():
            return candidate
    return None


def set_windows_window_icon(
    window: Any,
    *,
    platform: str | None = None,
    icon_path: Path | None = None,
    loader: Callable[[Path], Any] | None = None,
) -> bool:
    """WinForms ana penceresine paketlenmiş uygulama ikonunu doğrudan atar."""
    system = sys.platform if platform is None else platform
    if not system.startswith("win"):
        return False
    native = getattr(window, "native", None)
    if native is None:
        return False
    path = icon_path or app_icon_path()
    if path is None or not path.is_file():
        return False
    try:
        if loader is None:
            from System.Drawing import Icon

            icon = Icon(str(path))
        else:
            icon = loader(path)
        native.Icon = icon
    except (ImportError, OSError, AttributeError):
        logger.warning("Windows pencere ikonu uygulanamadı.", exc_info=True)
        return False
    return True


def set_windows_titlebar_theme(
    window: Any,
    dark: bool,
    *,
    platform: str | None = None,
    setter: DwmSetter | None = None,
) -> bool:
    """Windows başlık çubuğunu uygulamanın açık/koyu temasıyla eşitler."""
    system = sys.platform if platform is None else platform
    if not system.startswith("win"):
        return False
    hwnd = _native_window_handle(window)
    if hwnd is None:
        return False

    apply_attribute = setter or _dwm_set_titlebar
    # 20: Windows 10 20H1+; 19: daha eski Windows 10 yapıları için geri dönüş.
    for attribute in (20, 19):
        if apply_attribute(hwnd, attribute, dark) == 0:
            return True
    return False


class TitleBarApi:
    """Frontend temasını yerel Windows başlık çubuğuna taşıyan küçük JS köprüsü."""

    def __init__(self, *, platform: str) -> None:
        self._platform = platform
        self._window: Any | None = None
        self._icon_applied = False

    def bind_window(self, window: Any) -> None:
        self._window = window

    def set_titlebar_theme(self, dark: bool) -> bool:
        if self._window is None:
            return False
        try:
            if not self._icon_applied:
                self._icon_applied = set_windows_window_icon(
                    self._window,
                    platform=self._platform,
                )
            return set_windows_titlebar_theme(
                self._window,
                bool(dark),
                platform=self._platform,
            )
        except OSError:
            logger.warning("Windows başlık çubuğu teması uygulanamadı.", exc_info=True)
            return False


def _secilen_yol(sonuc: object) -> str:
    """`create_file_dialog`'un dönüşünü tek biçime indirir: seçilen yol, iptalde boş metin."""
    if sonuc is None:
        return ""
    if isinstance(sonuc, list | tuple):
        return str(sonuc[0]) if sonuc else ""
    return str(sonuc)


def _tur_suzgeci(ad: str) -> tuple[str, ...]:
    return TUR_SUZGECLERI.get(Path(ad).suffix.lower(), GENEL_SUZGEC)


def _uzanti(ad: str) -> str:
    """Addaki uzantı, yoksa boş metin: uzantı boşluk taşımaz, en az bir harf içerir (modül başlığı)."""
    son_ek = Path(ad).suffix
    if " " in son_ek or not any(harf.isalpha() for harf in son_ek):
        return ""
    return son_ek


def _atomik_yaz(hedef: Path, veri: bytes) -> None:
    """Aynı dizinde geçici adla yazar, `fsync` eder, `os.replace` ile yerine koyar.

    Hata olursa geçici dosya kalmaz, var olan dosya bozulmaz. `mkstemp` dosyayı yalnız kullanıcıya
    açık kurar (0600): kurtarma belgesi anahtar taşır.
    """
    tanitici, gecici = tempfile.mkstemp(dir=hedef.parent, prefix=".oab-defteri-", suffix=".tmp")
    try:
        with os.fdopen(tanitici, "wb") as akis:
            akis.write(veri)
            akis.flush()
            os.fsync(akis.fileno())
        os.replace(gecici, hedef)
    finally:
        Path(gecici).unlink(missing_ok=True)


class PencereKoprusu(TitleBarApi):
    """Pencerenin `js_api`'si: başlık çubuğu teması, kaydetme yeri, yedek dosyası, dosya kaydı.

    Köprünün varlığı ön yüzün yetenek işaretidir: `kaydetme_yeri_sor` yoksa (geliştirme kipi,
    tarayıcı) "Şifreli yedeği kaydet" düğmesi kapalıdır, `yedek_dosyasi_sor` yoksa geri yüklemede
    yükleme kutusu çıkar, `dosya_kaydet` yoksa `saveBlob` tarayıcının indirmesine düşer. Adları `_`
    ile başlayan öznitelikler ön yüze açılmaz: pywebview `js_api`'nin açık özniteliklerini dolaşır.
    Her çağrı ayrı iş parçacığında koşar; `_son_klasor`'e tek atama yapılır, kilit gerekmez.
    """

    def __init__(self, *, platform: str, webview: Any) -> None:
        super().__init__(platform=platform)
        self._webview = webview
        self._son_klasor: Path | None = None

    def _acilis_klasoru(self, *, son_klasor: bool) -> Path:
        """Pencerenin açılacağı klasör: son klasör, yoksa ya da istenmezse ev dizini."""
        klasor = self._son_klasor if son_klasor else None
        return klasor if klasor is not None and os.path.isdir(klasor) else Path.home()

    def _dosya_penceresi(self, window: Any, tur: int, **secenekler: Any) -> str:
        """Pencereyi son klasörde açar; seçilen yolu döndürür, iptalde boş metin (modül başlığı)."""
        acilis = self._acilis_klasoru(son_klasor=True)
        yol = _secilen_yol(window.create_file_dialog(tur, directory=str(acilis), **secenekler))
        if yol:
            self._son_klasor = Path(yol).parent
        return yol

    def _kayit_hedefi(self, window: Any, ad: str, *, son_klasor: bool) -> Path | None:
        """Kaydetme penceresinin seçtirdiği yer; iptalde `None` (uzantı kuralı modül başlığında).

        `son_klasor=False` pencereyi ev dizininde açar, son klasöre dokunmaz (kurtarma belgesi).
        Uzantı eklenen ad zaten varsa pencere kullanıcının seçtiği klasörde, o adla yeniden açılır;
        son klasör yalnız iş iptalsiz biterse yazılır (iptal onu değiştirmez).
        """
        uzanti = _uzanti(ad)
        suzgec = _tur_suzgeci(ad)
        acilis = self._acilis_klasoru(son_klasor=son_klasor)
        while True:
            yol = _secilen_yol(
                window.create_file_dialog(
                    self._webview.SAVE_DIALOG,
                    directory=str(acilis),
                    save_filename=ad,
                    file_types=suzgec,
                )
            )
            if not yol:
                return None
            hedef = Path(yol)
            if not _uzanti(hedef.name) and uzanti:
                hedef = hedef.with_name(hedef.name.rstrip(".") + uzanti)
                if os.path.lexists(hedef):
                    ad, acilis = hedef.name, hedef.parent
                    continue
            if son_klasor:
                self._son_klasor = hedef.parent
            return hedef

    def dosya_kaydet(self, icerik: str, onerilen_ad: str = "", ev_klasorunde: bool = False) -> str:
        """Kaydetme penceresini açar, içeriği (base64) seçilen yere yazar; yalnız durum döndürür.

        `kaydedildi`, `iptal` ya da `hata`; hata ön yüze ham geçmez, yol ve içerik hiçbir yere
        çıkmaz (modül başlığı). Pencere yoksa (`--autotest`, bağlanmadan gelen çağrı) dosya
        yazılmamıştır: ön yüz bunu bilsin diye `hata` döner, günlüğe düşmez. `ev_klasorunde`
        yalnız `True` iken pencere ev dizininde açılır (kurtarma belgesi, modül başlığı). Seçilen
        yer son klasör olur, dosya sonra yazılamasa da: kullanıcı o klasörü seçmiştir.
        """
        window = self._window
        if window is None:
            return KAYIT_HATA
        try:
            veri = base64.b64decode(icerik, validate=True)
            hedef = self._kayit_hedefi(
                window,
                Path(str(onerilen_ad)).name,
                son_klasor=ev_klasorunde is not True,
            )
            if hedef is None:
                return KAYIT_IPTAL
            _atomik_yaz(hedef, veri)
        except Exception as hata:  # noqa: BLE001 — köprü hatası ön yüze ham geçmesin
            logger.warning("Dosya kaydedilemedi (%s).", type(hata).__name__)
            return KAYIT_HATA
        return KAYIT_KAYDEDILDI

    def kaydetme_yeri_sor(self, onerilen_ad: str = "") -> str:
        """Kaydetme penceresini açar; seçilen yolu döndürür.

        İptalde, pencere yoksa ya da pencere açılamazsa boş metin döner, hata ön yüze geçmez:
        boş dönüşte ön yüz istek göndermez, hiçbir şey yazılmaz.
        """
        window = self._window
        if window is None:
            return ""
        try:
            return self._dosya_penceresi(
                window,
                self._webview.SAVE_DIALOG,
                save_filename=Path(str(onerilen_ad)).name,
                file_types=KAYDETME_SUZGECI,
            )
        except Exception as hata:  # noqa: BLE001 — köprü hatası ön yüze ham geçmesin
            logger.warning("Kaydetme penceresi açılamadı (%s).", type(hata).__name__)
            return ""

    def yedek_dosyasi_sor(self) -> str:
        """Aç penceresini açar; seçilen yedek dosyasının yolunu döndürür.

        İptalde, pencere yoksa ya da pencere açılamazsa boş metin döner, hata ön yüze geçmez: boş
        dönüşte ön yüzün seçili kaynağı değişmez, istek gitmez. Yol günlüğe yazılmaz.
        """
        window = self._window
        if window is None:
            return ""
        try:
            return self._dosya_penceresi(
                window,
                self._webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=KAYDETME_SUZGECI,
            )
        except Exception as hata:  # noqa: BLE001 — köprü hatası ön yüze ham geçmesin
            logger.warning("Aç penceresi açılamadı (%s).", type(hata).__name__)
            return ""


class WindowController:
    """Pencerenin göster / çık davranışı (T6, §4.2, §4.5).

    İki yerden çağrılır: pywebview olayları (pencere iş parçacığı) ve tek kopya
    kanalı (`od-kanal`: ikinci açılışta `goster`, kurucunun `kapat`'ı). Arayüzdeki
    Çık da masaüstü kancasıyla `request_quit`'e gelir. Durum bu yüzden kilit
    altındadır; pywebview çağrıları kilit DIŞINDA yapılır (pencere iş parçacığına
    sıralanıp bloklayabilirler).

    pywebview'ın `shown` olayı bazı arka uçlarda geç gelebilir; sayfa yüklenince
    gelen `loaded` olayı da pencereyi "hazır" sayar (göster/kapat komutları işler).

    `sayac` uzun iş sayacıdır (`desktop.main.uzun_is_sayaci`); verilmezse beklenecek iş yoktur.
    `bekleme_sn` ve `saat` kapanış beklemesinin süresi ve saatidir (modül başlığı).
    """

    def __init__(
        self,
        *,
        platform: str | None = None,
        sayac: UzunIsBeklenebilir | None = None,
        bekleme_sn: float = KAPANIS_BEKLEME_SN,
        saat: Callable[[], float] = time.monotonic,
    ) -> None:
        self._platform = sys.platform if platform is None else platform
        self._sayac = sayac
        self._bekleme_sn = bekleme_sn
        self._saat = saat
        self._lock = threading.Lock()
        self._window: Any | None = None
        self._shown = False
        self._quitting = False
        self._destroy_requested = False
        # Kapanış uzun işi bekliyor: kapatma istekleri bu beklemeye katılır.
        self._bekliyor = False
        self._minimized = False
        self._maximized = False

    @property
    def quitting(self) -> bool:
        with self._lock:
            return self._quitting

    def bind(self, window: Any) -> None:
        """pywebview penceresine bağlanır (`webview.start`'tan ÖNCE)."""
        with self._lock:
            self._window = window
        events = window.events
        events.closing += self.on_closing
        events.shown += self._on_shown
        loaded = getattr(events, "loaded", None)
        if loaded is not None:
            events.loaded += self._on_loaded
        events.minimized += self._on_minimized
        events.maximized += self._on_maximized
        events.restored += self._on_restored

    # ------------------------------------------------------------ pywebview olayları

    def on_closing(self) -> bool:
        """Çarpı (ya da işletim sisteminin kapatması): program kapanır, onay sorulmaz (T6).

        Pencere iş parçacığında eşzamanlı koşar, iş yapmaz (modül başlığı). Uzun iş sürüyorsa
        kapanmayı iptal eder, yardımcı iş parçacığı kapanışı bir kez yapar; ikinci çarpı
        beklemeye katılır. Pencere zaten kapanmakta olduğu için ikinci bir `destroy` çağrılmaz.
        """
        with self._lock:
            if self._destroy_requested:
                return True
            ilk = not self._quitting
            self._quitting = True
            if self._bekliyor:
                return False
            bekle = self._bekleme_kararini_ver()
            window = self._window
        if bekle:
            self._beklemeyi_baslat(window)
            return False
        if ilk:
            logger.info("Pencere kapatıldı; program düzenli kapanıyor.")
        return True

    def _on_shown(self) -> None:
        with self._lock:
            self._shown = True
            window = self._window
            pending_quit = self._quitting
        if window is not None and pending_quit:
            self._kapat_ya_da_bekle(window)

    def _on_loaded(self) -> None:
        """Sayfa yüklendi: gizli başlatılan pencere de artık komut alabilir."""
        with self._lock:
            if self._shown:
                return
            self._shown = True
            window = self._window
            pending_quit = self._quitting
        if window is not None and pending_quit:
            self._kapat_ya_da_bekle(window)

    def _on_minimized(self) -> None:
        with self._lock:
            self._minimized = True

    def _on_maximized(self) -> None:
        with self._lock:
            self._minimized, self._maximized = False, True

    def _on_restored(self) -> None:
        with self._lock:
            self._minimized, self._maximized = False, False

    # --------------------------------------------------------------- kanal komutları

    def show(self) -> None:
        """İkinci açılış: pencereyi öne getirir, küçültülmüşse eski boyutuna döndürür."""
        with self._lock:
            window = self._window if self._shown and not self._quitting else None
            minimized, maximized = self._minimized, self._maximized
        if window is not None:
            self._one_getir(window, minimized=minimized, maximized=maximized)

    def request_quit(self) -> None:
        """Çık (arayüz, kurucu, SIGTERM): pencereyi kapatır; `webview.start` döner, çıkış sürer.

        Pencere henüz gösterilmediyse (komut açılış sırasında geldi) kapanma
        `shown` olayında yapılır; `open_window` başlatmadan önce de bakar. Uzun iş sürüyorsa
        kapanış onun bitmesini bekler; SIGTERM köprüsü Qt iş parçacığından çağırır, burası
        beklemez.
        """
        with self._lock:
            self._quitting = True
            window = self._window if self._shown else None
        logger.info("Çıkış istendi; program düzenli kapanıyor.")
        if window is not None:
            self._kapat_ya_da_bekle(window)

    def _one_getir(self, window: Any, *, minimized: bool, maximized: bool) -> None:
        try:
            window.show()
            if minimized:
                if maximized:
                    window.maximize()
                else:
                    window.restore()
        except Exception:  # noqa: BLE001 — kanal komutu programı düşürmesin
            logger.warning("Pencere gösterilemedi.", exc_info=True)

    def _bekleme_kararini_ver(self) -> bool:
        """Kilit altında: kapanış bekleyecekse bekleme durumuna, beklemeyecekse kapanmaya geçer.

        Sayaç okunamazsa beklenmez (modül başlığı); okuma kısadır, pywebview'a gitmez.
        """
        try:
            suruyor = self._sayac is not None and self._sayac.sayi != 0
        except Exception:  # noqa: BLE001 — kapanış sayaç yüzünden takılmasın (T6)
            logger.warning("Uzun iş sayacı okunamadı; kapanış beklemiyor.", exc_info=True)
            suruyor = False
        self._bekliyor = suruyor
        self._destroy_requested = not suruyor
        return suruyor

    def _kapat_ya_da_bekle(self, window: Any) -> None:
        """Kapanışın tek kapısı: uzun iş sürüyorsa bekler, yoksa kapatır; bir kez yapılır."""
        with self._lock:
            if self._destroy_requested or self._bekliyor:
                return
            bekle = self._bekleme_kararini_ver()
        if bekle:
            self._beklemeyi_baslat(window)
        else:
            self._pencereyi_kapat(window)

    def _beklemeyi_baslat(self, window: Any) -> None:
        logger.info("Uzun iş sürüyor; kapanış işin bitmesini bekliyor.")
        threading.Thread(
            target=self._kapanisi_bekle, args=(window,), name="od-kapanis", daemon=True
        ).start()

    def _kapanisi_bekle(self, window: Any) -> None:
        """Yardımcı iş parçacığı: iş bitince ya da süre dolunca kapanışı yapar (modül başlığı)."""
        threading.Thread(
            target=self._bekledigini_bildir, args=(window,), name="od-kapanis-bildirim", daemon=True
        ).start()
        try:
            if not self._is_bitene_dek_bekle():
                logger.warning(
                    "Uzun iş %d sn içinde bitmedi; program kapanıyor.", int(self._bekleme_sn)
                )
        except Exception:  # noqa: BLE001 — kapanış sayaç yüzünden takılmasın (T6)
            logger.exception("Uzun iş beklenemedi; program kapanıyor.")
        with self._lock:
            self._destroy_requested = True
        self._pencereyi_kapat(window)

    def _is_bitene_dek_bekle(self) -> bool:
        if self._sayac is None:
            return True
        son = self._saat() + self._bekleme_sn
        while (kalan := son - self._saat()) > 0:
            if self._sayac.sifirlanmasini_bekle(min(kalan, _BEKLEME_DILIMI_SN)):
                return True
        return False

    def _bekledigini_bildir(self, window: Any) -> None:
        """Pencereyi gösterir, ön yüze DOM olayını yollar; hata beklemeyi bozmaz."""
        with self._lock:
            minimized, maximized = self._minimized, self._maximized
        self._one_getir(window, minimized=minimized, maximized=maximized)
        try:
            window.evaluate_js(_KAPANIS_BEKLIYOR_BETIGI)
        except Exception:  # noqa: BLE001 — ileti gösterilemese de kapanış sürer
            logger.warning("Kapanış bekleme iletisi ön yüze gönderilemedi.", exc_info=True)

    def _pencereyi_kapat(self, window: Any) -> None:
        try:
            window.destroy()
        except Exception:  # noqa: BLE001 — çıkış yolu hata yüzünden takılmasın
            logger.exception("Pencere kapatılamadı.")


def open_window(
    url: str,
    *,
    title: str = WINDOW_TITLE,
    storage_path: Path,
    webview: Any | None = None,
    platform: str | None = None,
    importer: Callable[[], Any] | None = None,
    controller: WindowController | None = None,
) -> None:
    """Pencereyi açar ve kapanana kadar bloklar (pywebview'ın olay döngüsü).

    `controller` verilirse pencere olaylarına bağlanır; çarpı programı kapatır
    (T6), kanal ve arayüz komutları denetçiden geçer.
    """
    system = sys.platform if platform is None else platform
    module = webview
    if module is None:
        try:
            module = (importer or import_webview)()
        except ImportError as exc:
            raise WebViewUnavailableError(
                "Pencere açılamadı: pencere bileşeni (pywebview) yüklü değil.",
                hint="Kurulum eksik görünüyor; programı yeniden kurun.",
            ) from exc

    storage_path.mkdir(parents=True, exist_ok=True)
    set_windows_app_id(platform=system)
    # pywebview 5.x dosya indirmelerini varsayılan olarak engeller. `saveBlob` dosyayı köprüyle
    # kaydeder (`dosya_kaydet`); köprü sayfaya yetişmeden gelen istek `<a download>` yoluna düşer.
    # İzin o yol için pencere oluşturulmadan önce açılır: tıklama sessizce yutulmasın.
    module.settings["ALLOW_DOWNLOADS"] = True
    kopru = PencereKoprusu(platform=system, webview=module)
    window = module.create_window(
        title,
        url,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=WINDOW_MIN_SIZE,
        text_select=True,
        js_api=kopru,
    )
    kopru.bind_window(window)
    if controller is not None:
        controller.bind(window)
        if controller.quitting:
            logger.info("Çıkış pencere açılmadan istendi; pencere açılmıyor.")
            return
    logger.info("Pencere açılıyor (%s).", gui_backend_for(system))
    module.start(
        gui=gui_backend_for(system),
        localization=dict(PENCERE_METINLERI),
        private_mode=False,  # oturum çerezi + taslaklar pencere ömrü boyunca kalsın
        storage_path=str(storage_path),
        debug=False,
    )
