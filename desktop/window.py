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

Tür süzgeci uzantıya göredir (`TUR_SUZGECLERI`): ön yüzün `saveBlob` ile kaydettiği her uzantının
süzgeci vardır (PDF, Word, Excel, kurulum dosyası; saha bulgusu K-yeni-3, Pardus 25, 13.11.2026: Word
evrakı "Tüm dosyalar | *" ile kaydediliyordu). Eşitlik `desktop/tests/test_kayit_suzgecleri.py`'de ön
yüz kaynağı taranarak bağlıdır: yeni bir uzantı süzgeçsiz kalırsa test düşer. Süzgeç Windows'ta da
gelir. Windows'ta süzgecin uzantısını ve üzerine yazma sorusunu pencere kendi yapar. Qt kolu
kaydetmede süzgeç uygulamaz, uzantı eklemez: ad uzantısız kaldıysa önerilen addaki
uzantıyı köprü ekler. Noktalı son ek her zaman uzantı değildir (`_uzanti`): programın adları
tarihle biter, `Rapor_07.11.2026`nin `.2026`sı uzantı sayılsaydı dosya `.pdf`siz yazılırdı. Pencere yalnız yazılan adı sormuştur: uzantı eklenen ad zaten varsa dosya ezilmez, pencere
kullanıcının seçtiği klasörde o adla yeniden açılır, soruyu pencere sorar.

**Linux'ta pencere masaüstünündür** (saha bulgusu K-P3, Pardus 25, 12.11.2026; `desktop/yerel_pencere.py`).
pywebview'ın Qt kolunun penceresi Pardus'ta Qt'nin kendi çizdiği, İngilizce, kenar çubuğunda takılı USB
belleği göstermeyen pencereydi. Köprü Linux'ta önce masaüstünün penceresini dış süreçte açar (zenity, yoksa
kdialog; programın kütüphane yolundan temizlenmiş ortamla, `desktop/dis_surec.py`), açılamazsa pywebview'ın
Qt penceresine düşer (`_pencere_ac`). İki yol aynı seçenekleri alır: başlık `PENCERE_METINLERI`, açılış
klasörü ve önerilen ad yukarıdaki kurallarla, süzgeç `TUR_SUZGECLERI`; zenity de uzantı eklemez, uzantı ve
"eklenen uzantılı ad varsa yeniden aç" kuralı (`_kayit_hedefi`) iki yolda da aynen çalışır; üzerine yazma
sorusunu zenity sorar. Dış süreç kipli değildir, ana pencere tıklanabilir kalır; X11 oturumunda dış pencere
ana pencereye bağlanır (`WM_TRANSIENT_FOR`; saha bulgusu K-yeni-2, `desktop/x11_pencere.py`): pencere
yöneticisi onu ana pencerenin üstünde tutar, görev çubuğunda ayrı girdi olmaz. Pencere açıkken gelen
ikinci pencere çağrısı beklemeden iptal döner (`_tek_pencere`; ön yüzde Excel şablonu düğmeleri bekleme
sırasında kilitlenmez, başka ekrana da geçilebilir). İptal sessiz kalmaz: açık pencere öne getirilir
(`YerelPencere.one_getir`), köprü ön yüze `od:dosya-penceresi-acik` olayını yollar, ön yüz "Açık bir
dosya penceresi var" bildirimini gösterir (`frontend/src/DosyaPenceresiBildirimi.tsx`; bağlanamayan dış
pencere, örneğin Wayland'da, ana pencerenin arkasında kalmış olabilir).
Sayfanın dosya kutuları (`<input type="file">`) da aynı pencereyle ve aynı kilitle açılır
(`_yukleme_dosyasi_sec`, `desktop/yerel_pencere.py` "Sayfanın dosya kutuları da"): kutunun kabul ettiği
uzantılar "Uygun dosyalar" süzgecidir, "Tüm dosyalar" da seçilebilir (sunucu türü yine denetler).
pywebview'ın Qt kolunda bağlananlar (dosya kutusu; dış bağlantıların temiz ortamla açılması ve yeni
pencere isteğinin pencerenin profiliyle karşılanması, `desktop/dis_surec.py`; ana pencerenin X kimliği,
`desktop/x11_pencere.py`; sayfa önbelleği, aşağıda) arka uç yüklenince, pencere kurulmadan önce kurulur
(`_arka_uc_kurulunca`).
Program kapanırken açık pencere sonlandırılır (`open_window`). Windows yolu değişmez.

**Son klasör.** Üç pencere de son seçilen klasörde açılır; klasör yalnız bellektedir,
süreç kapanınca unutulur, diske ve günlüğe yazılmaz. İptal onu değiştirmez; klasör artık yoksa (bellek
çekildi) ev dizinine düşülür. Kurtarma anahtarı belgesinin penceresi (`ev_klasorunde`) bunun dışındadır:
her seferinde ev dizininde açılır, son klasörü ne okur ne değiştirir (kullanıcı kararı 07.11.2026 "Hep ev
klasöründe"). Şifreli yedek USB belleğe kaydedildikten hemen sonra anahtar onun yanına önerilseydi,
bellek kaybolunca yedek de onu açan anahtar da birlikte giderdi; yedek de anahtarın yanına önerilmez.

**WebView2'nin form önerisi kapalıdır, öneri veritabanı ve sayfa önbelleği açılışta silinir** (KVKK;
tasarım §4.3 tehdit 24; Windows sınaması 07.11.2026, bilinen kusurlar 23 ve 24). WebView2 iki yerde
şifresiz iz bırakıyordu:
  - Genel otomatik doldurma formlara yazılanları (adlar, okul adı, kurtarma anahtarı) profil dizinindeki
    `EBWebView/Default/Web Data` SQLite dosyasına yazıyor, sonraki kullanıcıya öneri olarak gösteriyordu.
    Öneri yalnız aynı alanda çıkmaz: kayıtlar alanın kimliğiyle tutulur, React'in `useId` kimlikleri
    (`:r4:` gibi) ekranlar arasında yinelenir; sınamada kurulumda yazılan okul adı kilit ekranının parola
    alanında, oturum açılmadan önerildi. Alanlardaki `autoComplete="off"` saklamayı önlemedi.
  - Sayfa önbelleği (`EBWebView/Default/Cache`) sunucu yanıtlarını çözülmüş hâliyle tutuyordu. Sunucu
    artık her `/api/` yanıtına `Cache-Control: no-store` koyar (`apps.okul.onbellek_middleware`).

pywebview 5.3.2 bu ayarlara dokunmaz (`edgechromium.py` `on_webview_ready`); `form_onerisini_kapat`
pywebview'ı `window.native` üzerinden aşar. Pencere gösterilince (`shown`) `CoreWebView2.Settings`'in
`IsGeneralAutofillEnabled` ve `IsPasswordAutosaveEnabled` değerlerini kapatır (parola saklama WebView2'de
zaten kapalı gelir, açıkça da kapatılır). Bileşen henüz hazır değilse hazır olduğunu bildiren olaya
bağlanır. Bileşenin nesneleri yalnız pencere iş parçacığında kullanılabilir: denetim de bağlanma da
oradadır (`Invoke`), hazır olma olayı da orada koşar, ikisinin arasında yarış yoktur. Kapatılamazsa
pencere yine açılır, günlüğe yalnız hata türü düşer.

Profil önbellektir, programın verisi değildir: `pencere_onbellegini_temizle` öneri veritabanını ve sayfa
önbelleğini her açılışta bileşen başlamadan siler. Önceki sürümlerin bıraktığı da, kapatmanın tutmadığı
bir oturumda yazılan da sonraki açılışta gider; silme kapanışta yapılmaz, o güne dek dosyada durur.
Önceki oturumun bileşen süreci programdan sonra kapanır, o sırada dosyalar kilitlidir: kilitli dosya
`TEMIZLIK_BEKLEME_SN` boyunca yeniden denenir, süre dolarsa açılış uyarıyla sürer. Günlük dosyaları ana
veritabanından önce silinir: ana dosya gidip günlük kalsaydı yeni veritabanına eski sayfalar uygulanabilirdi.
`pencere_onbellegini_temizle`'nin sildiği yollar yalnız WebView2'nindir; Qt kolunda (Pardus) o işlev
hiçbir şey silmez. Orada kapatılacak form önerisi ayarı da yoktur: Qt WebEngine'in ayarlarında
(`QWebEngineSettings`) karşılığı bulunmaz.

**Qt kolunda sayfa önbelleği bellektedir** (saha bulgusu N-2, Pardus 25.2, 13.11.2026). Qt'nin HTTP disk
önbelleği profil dizininin (`storage_path`) dışındadır (`QWebEngineProfile.cachePath`:
`~/.cache/oab-defteri/QtWebEngine/pywebview`); sunucu her açılışta yeni port aldığı için aynı varlıklar
her açılışta yeniden yazılıyordu (`Cache` 79 MB; 3,9 MB'lık simge yazı tipi 17 kez). `qt_onbellegini_bagla`
pencerenin sayfası profiliyle kurulurken, sayfa yüklenmeden önce profilin HTTP önbelleğini bellek içi
yapar (`QWebEngineProfile.setHttpCacheType(MemoryHttpCache)`: diske hiçbir şey yazılmaz, oturum içinde
yine önbellek vardır) ve önceki sürümlerin bıraktığı disk önbelleğini (`cachePath`) siler. Silme yalnız
yol (bağlar çözülerek) programın önbellek kökünün (`storage_path`'in üst dizini, `AppPaths.cache`:
`~/.cache/oab-defteri`) içindeyse yapılır; kökün kendisi, pencerenin deposu (`storage_path`: oturum
çerezi, taslaklar) ve onu içeren dizinler, boş ya da göreli yol (gizli profilin `cachePath`'i boştur,
çalışma dizinine çözülürdü; bağımsız denetim 14.11.2026) silinmez (`eski_qt_onbellegini_sil`). Silinemezse
pencere yine açılır, günlüğe yalnız hata türü düşer. `/api/` yanıtlarını ayrıca sunucunun `no-store`u
korur. Öteki kalan riskler (kapatmanın tutmadığı oturumda açılışa dek bekleyen dosya, silinen dosyanın diskte kalan
içeriği, bileşenin çökme dökümleri `EBWebView/Crashpad`) tasarım §4.3 tehdit 24'tedir.
"""

from __future__ import annotations

import base64
import logging
import os
import shutil
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final, Protocol

from desktop.dis_surec import dis_tarayiciyi_bagla, yeni_pencere_isleyicisini_bagla
from desktop.errors import WebViewUnavailableError
from desktop.paths import resource_root
from desktop.x11_pencere import SARMALAYICI_ISARETI, DisPencereBaglayici, ana_pencereyi_bagla
from desktop.yerel_pencere import YerelDosyaPenceresi, yukleme_penceresini_bagla

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
#: Ön yüzün kaydettiği her uzantı buradadır (modül başlığı; `test_kayit_suzgecleri.py`).
TUR_SUZGECLERI: Final = {
    ".pdf": ("PDF belgesi (*.pdf)",),
    ".docx": ("Word belgesi (*.docx)",),
    ".xlsx": ("Excel dosyası (*.xlsx)",),
    ".exe": ("Kurulum dosyası (*.exe)",),
}
#: Öteki uzantıların süzgeci: süzgeç hiç verilmezse pywebview İngilizce "All files" yazardı.
GENEL_SUZGEC: Final = ("Tüm dosyalar (*.*)",)
#: Sayfanın dosya kutusunda kutunun kabul ettiği uzantıların süzgecinin açıklaması (modül başlığı).
UYGUN_DOSYALAR: Final = "Uygun dosyalar"
#: Pencere açıkken gelen ikinci çağrıda ön yüze yollanan DOM olayı (modül başlığı).
DOSYA_PENCERESI_ACIK_OLAYI: Final = "od:dosya-penceresi-acik"
_DOSYA_PENCERESI_ACIK_BETIGI: Final = (
    f"window.dispatchEvent(new CustomEvent('{DOSYA_PENCERESI_ACIK_OLAYI}'))"
)
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
#: WebView2'nin form önerisi veritabanı, profil dizinine göre (modül başlığı). Önce aynı SQLite
#: veritabanının günlük dosyaları gelir (hangisinin oluştuğu bileşenin sürümüne bağlıdır), ana dosya sondadır.
FORM_ONERISI_DOSYALARI: Final = tuple(
    Path("EBWebView", "Default", ad)
    for ad in ("Web Data-journal", "Web Data-wal", "Web Data-shm", "Web Data")
)
#: WebView2'nin sayfa önbelleği (HTTP disk önbelleği), profil dizinine göre (modül başlığı).
SAYFA_ONBELLEGI_DIZINI: Final = Path("EBWebView", "Default", "Cache")
#: Önceki oturumun bileşen süreci kapanırken kilitli dosyanın yeniden deneneceği en uzun süre.
TEMIZLIK_BEKLEME_SN: Final = 3.0
_TEMIZLIK_ARALIGI_SN: Final = 0.25


class UzunIsBeklenebilir(Protocol):
    """Kapanışın kullandığı sayaç yüzeyi (`shared.bakim.UzunIsSayaci`; testte sahtesi verilir)."""

    @property
    def sayi(self) -> int: ...

    def sifirlanmasini_bekle(self, sure: float) -> bool: ...


class YerelPencere(Protocol):
    """Linux'ta masaüstünün dosya penceresi (`desktop.yerel_pencere.YerelDosyaPenceresi`).

    `ac` seçilen yolu, iptalde boş metni, pencere açılamazsa `None` döndürür (Qt'ye düşülür).
    """

    def ac(
        self, *, kaydet: bool, baslik: str, klasor: str, ad: str, suzgecler: Sequence[str]
    ) -> str | None: ...

    def one_getir(self) -> None:
        """Açık pencereyi öne getirir (X11'de, bağlanmışsa); yoksa bir şey yapmaz."""


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


def yukleme_suzgecleri(kabul: Sequence[str]) -> tuple[str, ...]:
    """Dosya kutusunun `accept` değerlerinden pencerenin süzgeçleri (modül başlığı).

    Uzantılar (".xls") "Uygun dosyalar" süzgecine girer, MIME türleri atlanır (uzantılar onları
    karşılar); "Tüm dosyalar" her zaman sondadır. Uzantı yoksa yalnız o kalır.
    """
    uzantilar: list[str] = []
    for tur in kabul:
        uzanti = tur.strip().lower()
        if uzanti.startswith(".") and uzanti[1:].isalnum() and f"*{uzanti}" not in uzantilar:
            uzantilar.append(f"*{uzanti}")
    if not uzantilar:
        return GENEL_SUZGEC
    return (f"{UYGUN_DOSYALAR} ({';'.join(uzantilar)})", *GENEL_SUZGEC)


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
    `yerel_pencere` yalnız Linux'ta kullanılır (modül başlığı: "Linux'ta pencere masaüstünündür").
    """

    def __init__(
        self, *, platform: str, webview: Any, yerel_pencere: YerelPencere | None = None
    ) -> None:
        super().__init__(platform=platform)
        self._webview = webview
        self._son_klasor: Path | None = None
        self._yerel_pencere = yerel_pencere if platform.startswith("linux") else None
        self._pencere_kilidi = threading.Lock()

    @contextmanager
    def _tek_pencere(self) -> Iterator[bool]:
        """Linux: pencere açıkken ikinci çağrı beklemeden `False` alır, iptal döner (modül başlığı).

        İptal sessiz kalmaz: ön yüze `od:dosya-penceresi-acik` olayı yollanır.
        """
        if self._yerel_pencere is None:
            yield True
            return
        if not self._pencere_kilidi.acquire(blocking=False):
            self._acik_pencereyi_bildir()
            yield False
            return
        try:
            yield True
        finally:
            self._pencere_kilidi.release()

    def _acik_pencereyi_bildir(self) -> None:
        """Açık pencereyi öne getirir, ön yüze "açık bir dosya penceresi var" olayını yollar.

        Çağıranı bekletmez: `evaluate_js` sonucu bekler, dosya kutusunda çağıranın beklediği Qt'nin ana
        iş parçacığıdır; ikisi de ayrı iş parçacığından gider. Hata iptali bozmaz.
        """
        window = self._window
        yerel = self._yerel_pencere

        def yolla() -> None:
            try:
                if yerel is not None:
                    yerel.one_getir()
            except Exception as hata:  # noqa: BLE001 — öne getirilemese de bildirim çıkar
                logger.warning("Açık pencere öne getirilemedi (%s).", type(hata).__name__)
            if window is None:
                return
            try:
                window.evaluate_js(_DOSYA_PENCERESI_ACIK_BETIGI)
            except Exception as hata:  # noqa: BLE001 — bildirim gitmese de iptal sürer
                logger.warning("Açık pencere bildirimi gönderilemedi (%s).", type(hata).__name__)

        threading.Thread(target=yolla, name="od-pencere-acik", daemon=True).start()

    def _pencere_ac(self, window: Any, tur: int, **secenekler: Any) -> str:
        """Tek pencere açılışı: Linux'ta önce masaüstünün penceresi, açılamazsa pywebview'ınki.

        Seçilen yolu, iptalde boş metni döndürür. Seçenekler `create_file_dialog`'unkilerdir.
        """
        if self._yerel_pencere is not None:
            kaydet = tur == self._webview.SAVE_DIALOG
            yol = self._yerel_pencere.ac(
                kaydet=kaydet,
                baslik=PENCERE_METINLERI["global.saveFile" if kaydet else "linux.openFile"],
                klasor=str(secenekler.get("directory", Path.home())),
                ad=str(secenekler.get("save_filename", "")),
                suzgecler=tuple(secenekler.get("file_types", ())),
            )
            if yol is not None:
                return yol
        return _secilen_yol(window.create_file_dialog(tur, **secenekler))

    def _acilis_klasoru(self, *, son_klasor: bool) -> Path:
        """Pencerenin açılacağı klasör: son klasör, yoksa ya da istenmezse ev dizini."""
        klasor = self._son_klasor if son_klasor else None
        return klasor if klasor is not None and os.path.isdir(klasor) else Path.home()

    def _dosya_penceresi(self, window: Any, tur: int, **secenekler: Any) -> str:
        """Pencereyi son klasörde açar; seçilen yolu döndürür, iptalde boş metin (modül başlığı)."""
        acilis = self._acilis_klasoru(son_klasor=True)
        yol = self._pencere_ac(window, tur, directory=str(acilis), **secenekler)
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
            yol = self._pencere_ac(
                window,
                self._webview.SAVE_DIALOG,
                directory=str(acilis),
                save_filename=ad,
                file_types=suzgec,
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

    def _yukleme_dosyasi_sec(self, kabul: Sequence[str]) -> list[str] | None:
        """Linux: sayfanın dosya kutusunun Aç penceresi (modül başlığı).

        `desktop.yerel_pencere.qt_dongusunde_bekleyici`'nin iş parçacığından çağrılır. Seçilen yolun
        listesi; iptalde ve başka pencere açıkken boş liste; masaüstü penceresi yoksa ya da açılamazsa
        `None` (Qt'nin varsayılan penceresine düşülür). Pencere son klasörde açılır, seçim son klasör
        olur. Ad `_` ile başlar: ön yüze açılmaz.
        """
        yerel = self._yerel_pencere
        if yerel is None:
            return None
        with self._tek_pencere() as serbest:
            if not serbest:
                return []
            yol = yerel.ac(
                kaydet=False,
                baslik=PENCERE_METINLERI["linux.openFile"],
                klasor=str(self._acilis_klasoru(son_klasor=True)),
                ad="",
                suzgecler=yukleme_suzgecleri(kabul),
            )
        if yol is None:
            return None
        if not yol:
            return []
        self._son_klasor = Path(yol).parent
        return [yol]

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
        with self._tek_pencere() as serbest:
            if not serbest:
                return KAYIT_IPTAL
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
        with self._tek_pencere() as serbest:
            if not serbest:
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
        with self._tek_pencere() as serbest:
            if not serbest:
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


def _arka_uc_kurulunca(webview: Any, *islevler: Callable[[Any], object]) -> None:
    """`webview.initialize`'ı sarar: arka uç yüklenince, pencere kurulmadan önce `islevler` koşar.

    `desktop.qt_kurulum.indirme_isleyicisini_bagla` ile aynı yol: `webview.platforms.qt` `start`'tan
    önce içe aktarılamaz (pencere deposu). `initialize` birden çok çağrılabilir; işlevler bunu kaldırır
    (ikinci bağlama yeniden sarmaz). Her işlev ayrı denenir: biri bağlanamazsa ötekiler yine bağlanır.
    Hata pencereyi durdurmaz.
    """
    asil = webview.initialize

    def initialize(*args: Any, **kwargs: Any) -> Any:
        arka_uc = asil(*args, **kwargs)
        for islev in islevler:
            try:
                islev(arka_uc)
            except Exception as hata:  # noqa: BLE001 — bağlanamasa da pencere açılır
                logger.warning("Pencere bileşenine bağlanılamadı (%s).", type(hata).__name__)
        return arka_uc

    webview.initialize = initialize


def _sil(hedef: Path, *, dizin: bool) -> None:
    """Dosyayı ya da dizini (içiyle) siler; yoksa sessizdir."""
    if not dizin:
        hedef.unlink(missing_ok=True)
        return
    try:
        shutil.rmtree(hedef)
    except FileNotFoundError:
        pass


def eski_qt_onbellegini_sil(
    dizin: Path, onbellek_koku: Path, *, korunanlar: Iterable[Path] = ()
) -> bool:
    """Qt'nin eski disk önbelleğini siler; yol programın önbellek kökünün içinde değilse dokunmaz.

    Göreli ya da boş yol (gizli profilin boş `cachePath`'i çalışma dizinine çözülürdü) silinmez. Yol
    ve kök bağlar çözülerek karşılaştırılır; kökün kendisi, `korunanlar` (pencerenin deposu) ve
    onları içeren dizinler silinmez. Silindiyse ya da zaten yoksa `True` (modül başlığı "Qt kolunda
    sayfa önbelleği bellektedir").
    """
    if not dizin.is_absolute():
        logger.warning("Pencerenin önbellek yolu boş ya da göreli; silinmedi.")
        return False
    try:
        gercek = dizin.resolve()
        kok = onbellek_koku.resolve()
        korunan = [yol.resolve() for yol in korunanlar]
    except (OSError, RuntimeError) as hata:
        logger.warning("Pencerenin eski önbelleği çözülemedi (%s).", type(hata).__name__)
        return False
    if kok not in gercek.parents:
        # Uyarı değil: `--data-dir` kipinde kök `<veri>/cache`dir, Qt'nin `cachePath`'i ise
        # `~/.cache/oab-defteri`de kalır; her açılışta günlüğe uyarı düşerdi (Pardus sınaması,
        # 14.11.2026). Önbellek yine bellek içidir, diske yazılmaz.
        logger.debug("Pencerenin önbelleği programın önbellek dizininin dışında; silinmedi.")
        return False
    if any(yol == gercek or gercek in yol.parents for yol in korunan):
        logger.warning("Pencerenin önbelleği pencerenin deposunu kapsıyor; silinmedi.")
        return False
    try:
        _sil(gercek, dizin=True)
    except OSError as hata:
        logger.warning("Pencerenin eski önbelleği silinemedi (%s).", type(hata).__name__)
        return False
    return True


def qt_profilinin_onbellegini_duzenle(
    profil: Any, onbellek_koku: Path, *, korunanlar: Iterable[Path] = ()
) -> None:
    """Profilin HTTP önbelleği bellek içi olur, eski disk önbelleği silinir (modül başlığı)."""
    profil.setHttpCacheType(type(profil).HttpCacheType.MemoryHttpCache)
    eski_qt_onbellegini_sil(Path(str(profil.cachePath())), onbellek_koku, korunanlar=korunanlar)


def qt_onbellegini_bagla(
    arka_uc: Any, onbellek_koku: Path, *, korunanlar: Iterable[Path] = ()
) -> None:
    """pywebview Qt kolunun sayfası profiliyle kurulurken önbelleği düzenler (modül başlığı).

    `BrowserView.WebPage.__init__` sarılır: profil pencerenin kurucusunda yaratılır, sayfaya verilir;
    ilk yükleme (`setUrl`) sayfa kurulduktan sonradır. Arka uç yüklenince, pencere kurulmadan önce
    çağrılır (`open_window`). Hata pencereyi durdurmaz.
    """
    sayfa_sinifi = arka_uc.BrowserView.WebPage
    asil = sayfa_sinifi.__init__
    if getattr(asil, SARMALAYICI_ISARETI, False):
        return
    korunan = tuple(korunanlar)

    def __init__(sayfa: Any, parent: Any = None, profile: Any = None) -> None:
        if profile is not None:
            try:
                qt_profilinin_onbellegini_duzenle(profile, onbellek_koku, korunanlar=korunan)
            except Exception as hata:  # noqa: BLE001 — önbellek düzenlenemese de pencere açılır
                logger.warning("Pencerenin önbelleği düzenlenemedi (%s).", type(hata).__name__)
        asil(sayfa, parent, profile)

    setattr(__init__, SARMALAYICI_ISARETI, True)
    sayfa_sinifi.__init__ = __init__


def pencere_onbellegini_temizle(
    storage_path: Path,
    *,
    bekle: Callable[[float], None] = time.sleep,
    saat: Callable[[], float] = time.monotonic,
    bekleme_sn: float = TEMIZLIK_BEKLEME_SN,
) -> None:
    """WebView2'nin önceki oturumlarda bıraktığı öneri ve sayfa önbelleğini siler (modül başlığı).

    Bileşen başlamadan, iki platformda da çağrılır; Qt kolunda bu yollar yoktur, işlev sessizdir. Kilitli öğe (`PermissionError`) süre dolana dek yeniden denenir; süre
    bütün öğeler için ortaktır. Silinemeyen öğe açılışı durdurmaz: günlüğe tek uyarı, yalnız hata
    türleriyle gider (yol hesap adını taşır).
    """
    son = saat() + bekleme_sn
    silinemeyen: list[str] = []
    ogeler = [(goreli, False) for goreli in FORM_ONERISI_DOSYALARI]
    ogeler.append((SAYFA_ONBELLEGI_DIZINI, True))
    for goreli, dizin in ogeler:
        while True:
            try:
                _sil(storage_path / goreli, dizin=dizin)
            except PermissionError as hata:
                if saat() < son:
                    bekle(_TEMIZLIK_ARALIGI_SN)
                    continue
                silinemeyen.append(type(hata).__name__)
            except OSError as hata:
                silinemeyen.append(type(hata).__name__)
            break
    if silinemeyen:
        logger.warning(
            "Pencere bileşeninin eski önbelleğinden %d öğe silinemedi (%s).",
            len(silinemeyen),
            ", ".join(sorted(set(silinemeyen))),
        )


def _pencere_is_parcaciginda(form: Any, islev: Callable[[], None]) -> None:
    """İşlevi WinForms formunun iş parçacığında koşturur, bitene dek bekler (pywebview'ın kalıbı)."""
    from System import Func, Type  # pythonnet; yalnız Windows'ta, pywebview yükler

    form.Invoke(Func[Type](islev))


def _oneriyi_kapat(core: Any) -> None:
    ayarlar = core.Settings
    ayarlar.IsGeneralAutofillEnabled = False
    ayarlar.IsPasswordAutosaveEnabled = False


def form_onerisini_kapat(
    window: Any,
    *,
    is_parcaciginda: Callable[[Any, Callable[[], None]], None] | None = None,
) -> None:
    """WebView2'nin form önerisini ve parola saklamasını kapatır (Windows; modül başlığı).

    `shown` olayında, ayrı bir iş parçacığından çağrılır. Hata pencereyi durdurmaz.
    """
    form = getattr(window, "native", None)
    denetim = getattr(form, "webview", None)
    if form is None or denetim is None:
        logger.warning("Pencere bileşeninin form önerisi kapatılamadı (bileşen bulunamadı).")
        return

    def hazir(gonderen: Any, olay: Any) -> None:
        # Bileşenin olayı pencere iş parçacığında koşar; hata .NET'e taşmasın.
        try:
            if olay.IsSuccess:
                _oneriyi_kapat(gonderen.CoreWebView2)
        except Exception as hata:  # noqa: BLE001 — pencere hata yüzünden düşmesin
            logger.warning(
                "Pencere bileşeninin form önerisi kapatılamadı (%s).", type(hata).__name__
            )

    def bagla() -> None:
        core = denetim.CoreWebView2
        if core is not None:
            _oneriyi_kapat(core)
        else:
            denetim.CoreWebView2InitializationCompleted += hazir

    try:
        (is_parcaciginda or _pencere_is_parcaciginda)(form, bagla)
    except Exception as hata:  # noqa: BLE001 — pencere hata yüzünden düşmesin
        logger.warning("Pencere bileşeninin form önerisi kapatılamadı (%s).", type(hata).__name__)


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
    pencere_onbellegini_temizle(storage_path)
    set_windows_app_id(platform=system)
    # pywebview 5.x dosya indirmelerini varsayılan olarak engeller. `saveBlob` dosyayı köprüyle
    # kaydeder (`dosya_kaydet`); köprü sayfaya yetişmeden gelen istek `<a download>` yoluna düşer.
    # İzin o yol için pencere oluşturulmadan önce açılır: tıklama sessizce yutulmasın.
    module.settings["ALLOW_DOWNLOADS"] = True
    # Linux: kaydetme ve Aç pencereleri masaüstünün, dış bağlantılar temiz ortamla (modül başlığı).
    baglayici = DisPencereBaglayici() if system.startswith("linux") else None
    yerel = YerelDosyaPenceresi(baglayici=baglayici) if baglayici is not None else None
    kopru = PencereKoprusu(platform=system, webview=module, yerel_pencere=yerel)
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
    if system.startswith("win"):
        window.events.shown += lambda: form_onerisini_kapat(window)
    if controller is not None:
        controller.bind(window)
        if controller.quitting:
            logger.info("Çıkış pencere açılmadan istendi; pencere açılmıyor.")
            return
    if yerel is not None and baglayici is not None:
        # `storage_path` `AppPaths.webview_storage_path`'tir: programın önbellek kökü üst dizinidir.
        onbellek_koku = storage_path.parent

        _arka_uc_kurulunca(
            module,
            lambda arka_uc: dis_tarayiciyi_bagla(arka_uc, platform=system),
            lambda arka_uc: yeni_pencere_isleyicisini_bagla(arka_uc, platform=system),
            lambda arka_uc: yukleme_penceresini_bagla(arka_uc, kopru._yukleme_dosyasi_sec),
            lambda arka_uc: ana_pencereyi_bagla(arka_uc, baglayici),
            lambda arka_uc: qt_onbellegini_bagla(
                arka_uc, onbellek_koku, korunanlar=(storage_path,)
            ),
        )
    logger.info("Pencere açılıyor (%s).", gui_backend_for(system))
    try:
        module.start(
            gui=gui_backend_for(system),
            localization=dict(PENCERE_METINLERI),
            private_mode=False,  # oturum çerezi + taslaklar pencere ömrü boyunca kalsın
            storage_path=str(storage_path),
            debug=False,
        )
    finally:
        if yerel is not None:
            # Açık dış pencere köprünün (daemon olmayan) iş parçacığını, o da süreci tutmasın.
            yerel.kapat()
