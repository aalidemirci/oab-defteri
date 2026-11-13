"""Linux'ta kaydetme ve Aç pencereleri: masaüstünün kendi penceresi, dış süreçte (saha bulgusu K-P3).

**Sorun** (Pardus 25.2, XFCE, Linux paketi, 12.11.2026). Köprünün pencereleri (`desktop/window.py`
`PencereKoprusu`) pywebview 5.3.2'nin Qt kolundan açılıyordu (`platforms/qt.py` `on_file_dialog`:
`QFileDialog.getSaveFileName` / `getOpenFileName` statik işlevleri). Pardus'ta Qt'nin kendi çizdiği,
İngilizce, masaüstüne yabancı pencere çıkıyor, kenar çubuğunda takılı USB bellek (`/media/<kullanıcı>/…`)
görünmüyordu; şifreli yedeği USB belleğe almak programın ana işidir. Masaüstünün penceresini Qt'ye
`platformthemes/libqgtk3.so` verir; eklenti süreç İÇİNDE sistemin GTK3'ünü yükler, GTK3 de pakete
gömülü bullseye glib'ine bağlanıp yüklenemez (debian:13 kabında paketle, `QT_QPA_PLATFORMTHEME=gtk3
QT_DEBUG_PLUGINS=1`: "libatspi.so.0: undefined symbol: g_once_init_leave_pointer", 13.11.2026). Paket
yığınını değiştirmek bu turun işi değildir; Qt kendi penceresine düşer.

**Çare.** Pencere dış süreçte açılır: önce zenity (GTK; Pardus'ta kurulu gelir), yoksa kdialog (KDE),
programın ortamı temizlenerek (`desktop.dis_surec.temiz_ortam`; temizlenmezse zenity paketin
kütüphanelerine bağlanıp çöker, K-P2). Dış süreç sistemin kütüphaneleriyle, sistemin dilinde açılır,
kenar çubuğunda takılı bellekler görünür. İkisi de yoksa, başlatılamazsa ya da beklenmeyen bir kodla
biterse (seçeneği tanımayan sürüm 255 döner, çöken süreç 127 ya da sinyal) `ac` `None` döner, köprü
pywebview'ın Qt penceresine düşer (artık Türkçe, `desktop.qt_kurulum.qt_cevirisini_kur`).

**Seçenekler üç Debian'da kaplarda denendi** (13.11.2026; `zenity --help-file-selection`,
`--help-general`, `kdialog --help` ve Xvfb altında gerçek açılış): Debian 11 zenity 3.32.0 ve kdialog
20.12, Debian 12 zenity 3.44.0 ve kdialog 22.12, Debian 13 (Pardus 25) zenity 4.1.90 ve kdialog 25.04.
`--file-selection`, `--save`, `--filename`, `--file-filter=AD | DESEN …` ve `--title` üçünde de
geçerlidir. `--confirm-overwrite` zenity 3'te üzerine yazma sorusunu açar; zenity 4'te "DEPRECATED;
does nothing" (GTK4 soruyu kendisi sorar) ve uyarı basar, "gelecek sürümde kaldırılacak" der:
kaldırılırsa seçenek pencereyi açmadan 255'le düşürürdü. Bu yüzden yalnız sürüm 4'ten küçükse
verilir; sürüm okunamazsa da verilir (tanınmazsa Qt penceresine düşülür, o da sorar). `--attach`
(pencereyi ana pencereye bağlar) zenity 4'te etkisizdir ve kaldırılacaktır: kullanılmaz. kdialog
`--title AD --getsavefilename YOL SÜZGEÇ` ve `--getopenfilename KLASÖR SÜZGEÇ` biçimini kabul eder;
süzgeç kdialog'un belgelediği "*.pdf|PDF belgesi" biçimindedir. Türkçe başlık UTF-8 yerel ayarda
geçer; C yerel ayarında (UTF-8 olmayan) zenity ASCII dışı argümanı 255'le reddeder, köprü Qt
penceresine düşer.

**Dönüş kodları.** 0: seçildi, yol standart çıktıdadır (`os.fsdecode`, sondaki satır sonu atılır);
1: iptal ya da pencere kapatıldı (kdialog tanımadığı seçenekte de 1 döner; kullanılan seçenekler
yukarıda doğrulandı). Başka her kod, başlatılamama ya da boş seçim zenity için kdialog'a, sonra Qt'ye
düşüştür (boş seçim iptal sayılır).

**Pencere ana pencereye bağlı değildir** (dış süreç; `--attach` yukarıda). Ana pencere tıklanabilir
kalır: köprü aynı anda ikinci pencereyi açmaz, ikinci çağrı beklemeden iptal döner
(`PencereKoprusu._tek_pencere`). Program kapanırken açık pencere sonlandırılır (`kapat`): pywebview'ın
köprü iş parçacığı gündelik (daemon olmayan) iş parçacığıdır, pencere açık kaldıkça süreç bitmezdi;
sonlandırılan pencere iptal sayılır, dosya yazılmaz. Seçilen yol günlüğe yazılmaz (hesap adını taşır).

**Sayfanın dosya kutuları da** (`<input type="file">`: Kişiler'de e-Okul personel listesi ve okulun veli
listesi şablonu; bağımsız denetim 13.11.2026) aynı pencereyle açılır. Bu kutular köprüden geçmez:
QtWebEngine `QWebEnginePage.chooseFiles`'ı çağırır, pywebview 5.3.2'nin sayfası (`BrowserView.WebPage`)
onu ezmez, Qt'nin varsayılanı kendi `QFileDialog`'unu açardı (kenar çubuğunda USB bellek yok).
`yukleme_penceresini_bagla` arka uç yüklenince, sayfa kurulmadan önce o sınıfa `chooseFiles` koyar
(`desktop.window.open_window`; pencerenin indirme işleyicisiyle aynı yol, `desktop/qt_kurulum.py`).
Çağrı Qt'nin ana iş parçacığında ve eşzamanlıdır, seçilen dosyaları döndürmelidir: dış süreç ayrı bir
iş parçacığında beklenir, ana iş parçacığı o sırada iç içe bir `QEventLoop` döndürür (Qt'nin kendi
`QFileDialog`'u da kipli açılışta aynısını yapar): pencere donmaz, sayfa çizilmeye devam eder. Yalnız
tek dosyalık kutu (`FileSelectOpen`) masaüstü penceresine gider; programda başka kip yoktur, olursa
Qt'nin varsayılanı kalır. Masaüstü penceresi açılamazsa da Qt'nin varsayılanına düşülür. Program
kapanırken iç döngü Qt'nin çıkışıyla biter, kutu iptal sayılır (açık pencereyi `kapat` sonlandırır).
Gerçek PySide6 6.8.3 + pywebview 5.3.2 + zenity 4.1.90 (Debian 13 kabı, Xvfb, 13.11.2026) ile sınandı:
kutuya tıklanınca "Dosya aç" başlıklı zenity penceresi açıldı (süzgeç "Uygun dosyalar | *.xls *.XLS
*.xlsx …", ortamında programın değişkenleri yoktu), yazılan yol seçilince kutu dosyayı aldı; zenity
açılamayınca Qt'nin penceresi Türkçe ("Aç") açıldı.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import threading
from collections.abc import Callable, Sequence
from typing import Any, Final

from desktop.dis_surec import temiz_ortam

logger = logging.getLogger("oab_defteri.yerel_pencere")

ZENITY: Final = "zenity"
KDIALOG: Final = "kdialog"
#: zenity'de `--confirm-overwrite`'ın etkili olduğu son ana sürüm (modül başlığı).
ZENITY_SORAN_SON_SURUM: Final = 3
#: Sürüm sorusunun en uzun süresi; pencere açmaz, hemen döner.
SURUM_SORUSU_SN: Final = 5.0
#: Dosya kutusunun penceresi beklenirken iç döngünün dış süreci yoklama aralığı.
BEKLEME_ARALIGI_MS: Final = 50
DONUS_SECILDI: Final = 0
DONUS_IPTAL: Final = 1
#: pywebview'ın süzgeç biçimi: "Açıklama (*.uz;*.uz2)" (`util.parse_file_type`).
_SUZGEC_BICIMI: Final = re.compile(r"^(?P<ad>.*?)\s*\((?P<desenler>[^()]*)\)\s*$")

Bulucu = Callable[[str], "str | None"]
#: Dosya kutusunun kabul ettiği türlerden seçilen yolları verir: iptalde boş liste, masaüstü penceresi
#: açılamazsa `None` (`desktop.window.PencereKoprusu._yukleme_dosyasi_sec`).
Secici = Callable[[list[str]], "list[str] | None"]
#: İşi bekler: (iş bitti mi, dönüşü). Hata ya da program kapanışı `(False, None)`'dır.
Bekleyici = Callable[[Callable[[], Any]], "tuple[bool, Any]"]


def suzgec_parcalari(suzgec: str) -> tuple[str, list[str]]:
    """ "PDF belgesi (*.pdf)" → ("PDF belgesi", ["*.pdf", "*.PDF"]); "*.*" her dosyadır ("*").

    GTK'nın deseni büyük-küçük harf ayırır (zenity 3): büyük harfli eş de verilir.
    """
    eslesme = _SUZGEC_BICIMI.match(suzgec)
    if eslesme is None:
        return suzgec.strip(), ["*"]
    desenler: list[str] = []
    for desen in re.split(r"[;\s]+", eslesme["desenler"]):
        if not desen:
            continue
        desen = "*" if desen == "*.*" else desen
        for es in (desen, desen.upper()):
            if es not in desenler:
                desenler.append(es)
    return eslesme["ad"], desenler or ["*"]


def zenity_argv(
    arac: str,
    *,
    kaydet: bool,
    baslik: str,
    klasor: str,
    ad: str,
    suzgecler: Sequence[str],
    ana_surum: int | None,
) -> list[str]:
    """zenity'nin argümanları; üzerine yazma sorusu sürüme göredir (modül başlığı)."""
    argv = [arac, "--file-selection", f"--title={baslik}"]
    if kaydet:
        argv += ["--save", f"--filename={os.path.join(klasor, ad)}"]
        if ana_surum is None or ana_surum <= ZENITY_SORAN_SON_SURUM:
            argv.append("--confirm-overwrite")
    else:
        # Sondaki ayraç: zenity bu klasörü açar, içinde bir dosya seçmez.
        argv.append(f"--filename={os.path.join(klasor, '')}")
    for suzgec in suzgecler:
        suzgec_adi, desenler = suzgec_parcalari(suzgec)
        argv.append(f"--file-filter={suzgec_adi} | {' '.join(desenler)}")
    return argv


def kdialog_argv(
    arac: str, *, kaydet: bool, baslik: str, klasor: str, ad: str, suzgecler: Sequence[str]
) -> list[str]:
    """kdialog'un argümanları; süzgeç "*.pdf *.PDF|PDF belgesi" satırlarıdır (modül başlığı)."""
    satirlar = []
    for suzgec in suzgecler:
        suzgec_adi, desenler = suzgec_parcalari(suzgec)
        satirlar.append(f"{' '.join(desenler)}|{suzgec_adi}")
    if kaydet:
        argv = [arac, "--title", baslik, "--getsavefilename", os.path.join(klasor, ad)]
    else:
        argv = [arac, "--title", baslik, "--getopenfilename", os.path.join(klasor, "")]
    if satirlar:
        argv.append("\n".join(satirlar))
    return argv


def _ana_surum(cikti: str) -> int | None:
    eslesme = re.match(r"\s*(\d+)\.", cikti)
    return int(eslesme.group(1)) if eslesme else None


class YerelDosyaPenceresi:
    """zenity/kdialog ile kaydetme ve Aç penceresi; `ac` yolu, iptalde boş metni, olmazsa `None` döner.

    `bul` aracı arar (`shutil.which`), `baslat` süreci başlatır (`subprocess.Popen`); testler sahtesini
    verir. Açık süreçler `kapat` için tutulur.
    """

    def __init__(
        self,
        *,
        bul: Bulucu = shutil.which,
        baslat: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    ) -> None:
        self._bul = bul
        self._baslat = baslat
        self._kilit = threading.Lock()
        self._surecler: set[subprocess.Popen[bytes]] = set()
        self._kapandi = False
        self._zenity_surumu: dict[str, int | None] = {}

    def ac(
        self,
        *,
        kaydet: bool,
        baslik: str,
        klasor: str,
        ad: str = "",
        suzgecler: Sequence[str] = (),
    ) -> str | None:
        """Pencereyi açar: seçilen yol, iptalde `""`, yerel pencere açılamazsa `None` (Qt'ye düşülür)."""
        for arac_adi in (ZENITY, KDIALOG):
            if self._kapandi:
                return ""
            arac = self._bul(arac_adi)
            if arac is None:
                continue
            if arac_adi == ZENITY:
                argv = zenity_argv(
                    arac,
                    kaydet=kaydet,
                    baslik=baslik,
                    klasor=klasor,
                    ad=ad,
                    suzgecler=suzgecler,
                    ana_surum=self._zenity_ana_surumu(arac),
                )
            else:
                argv = kdialog_argv(
                    arac, kaydet=kaydet, baslik=baslik, klasor=klasor, ad=ad, suzgecler=suzgecler
                )
            sonuc = self._calistir(arac_adi, argv)
            if sonuc is not None:
                return sonuc
        return None

    def _calistir(self, arac_adi: str, argv: list[str]) -> str | None:
        """Pencereyi açar, kapanmasını bekler; dönüş `ac`'ınkiyle aynı anlamdadır (modül başlığı)."""
        try:
            with self._kilit:
                if self._kapandi:
                    return ""
                surec = self._baslat(
                    argv,
                    env=temiz_ortam(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                self._surecler.add(surec)
            try:
                cikti, _ = surec.communicate()
            finally:
                with self._kilit:
                    self._surecler.discard(surec)
        except (OSError, subprocess.SubprocessError, ValueError) as hata:
            logger.warning("%s penceresi açılamadı (%s).", arac_adi, type(hata).__name__)
            return None
        if self._kapandi:
            return ""
        if surec.returncode == DONUS_IPTAL:
            return ""
        if surec.returncode != DONUS_SECILDI:
            logger.warning("%s penceresi %s koduyla bitti.", arac_adi, surec.returncode)
            return None
        return os.fsdecode(cikti).removesuffix("\n")

    def _zenity_ana_surumu(self, arac: str) -> int | None:
        """`zenity --version`'ın ana sürümü (süreç başına bir kez sorulur); okunamazsa `None`."""
        if arac not in self._zenity_surumu:
            surum: int | None = None
            try:
                surec = self._baslat(
                    [arac, "--version"],
                    env=temiz_ortam(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                try:
                    cikti, _ = surec.communicate(timeout=SURUM_SORUSU_SN)
                except subprocess.TimeoutExpired:
                    surec.kill()
                    surec.communicate()
                else:
                    if surec.returncode == 0:
                        surum = _ana_surum(os.fsdecode(cikti))
            except (OSError, subprocess.SubprocessError, ValueError) as hata:
                logger.warning("zenity sürümü okunamadı (%s).", type(hata).__name__)
            self._zenity_surumu[arac] = surum
        return self._zenity_surumu[arac]

    def kapat(self) -> None:
        """Program kapanıyor: açık pencereler sonlandırılır, yenisi açılmaz (iptal sayılır)."""
        with self._kilit:
            self._kapandi = True
            surecler = list(self._surecler)
        for surec in surecler:
            try:
                surec.terminate()
            except OSError:
                pass


def qt_dongusunde_bekleyici(qt_core: Any) -> Bekleyici:
    """İşi ayrı iş parçacığında koşturur, biterken Qt'nin olay döngüsünü iç içe döndürür (modül başlığı).

    Döngü yalnız ana iş parçacığında, zamanlayıcıyla sonlanır: iş parçacığı Qt'ye dokunmaz. Program
    kapanırken Qt bütün döngüleri bitirir; iş o sırada bitmemişse `(False, None)` döner.
    """

    def bekle(is_: Callable[[], Any]) -> tuple[bool, Any]:
        sonuc: list[Any] = []
        bitti = threading.Event()

        def kos() -> None:
            try:
                sonuc.append(is_())
            except Exception as hata:  # noqa: BLE001 — kutu iptal sayılır, pencere düşmez
                logger.warning("Dosya kutusunun penceresi açılamadı (%s).", type(hata).__name__)
            finally:
                bitti.set()

        threading.Thread(target=kos, name="od-dosya-kutusu", daemon=True).start()
        dongu = qt_core.QEventLoop()
        zamanlayici = qt_core.QTimer()
        zamanlayici.timeout.connect(lambda: dongu.quit() if bitti.is_set() else None)
        zamanlayici.start(BEKLEME_ARALIGI_MS)
        try:
            if not bitti.is_set():
                dongu.exec()
        finally:
            zamanlayici.stop()
        return (True, sonuc[0]) if bitti.is_set() and sonuc else (False, None)

    return bekle


def yukleme_isleyicisi(
    sec: Secici, *, taban: Callable[..., Any], tek_secim: Any, bekle: Bekleyici
) -> Callable[[Any, Any, Any, Any], list[str]]:
    """`QWebEnginePage.chooseFiles`'ın yerine geçen yöntem (modül başlığı).

    Tek dosyalık kutu masaüstü penceresine gider; öteki kipler ve açılamayan masaüstü penceresi
    `taban`'a (Qt'nin varsayılanı) düşer. İptal, hata ve program kapanışı boş listedir.
    """

    def chooseFiles(sayfa: Any, kip: Any, eski: Any, kabul: Any) -> list[str]:  # noqa: N802 — Qt adı
        if kip != tek_secim:
            return list(taban(sayfa, kip, eski, kabul))
        kabul_edilen = [str(tur) for tur in kabul]
        tamam, yollar = bekle(lambda: sec(kabul_edilen))
        if not tamam:
            return []
        if yollar is None:
            return list(taban(sayfa, kip, eski, kabul))
        return list(yollar)

    return chooseFiles


def yukleme_penceresini_bagla(arka_uc: Any, sec: Secici) -> None:
    """pywebview Qt kolunun sayfa sınıfına dosya kutusunun penceresini koyar (modül başlığı).

    Arka uç yüklenince, sayfa kurulmadan önce çağrılır (`desktop.window.open_window`).
    """
    taban = arka_uc.QWebPage
    arka_uc.BrowserView.WebPage.chooseFiles = yukleme_isleyicisi(
        sec,
        taban=taban.chooseFiles,
        tek_secim=taban.FileSelectionMode.FileSelectOpen,
        bekle=qt_dongusunde_bekleyici(arka_uc.QtCore),
    )
