# Windows paketleme — doğrulanmamış varsayımlar ve ilk koşu çek-listesi

> **Durum (31.10.2026, F1a):** Bu hat aile iskeletinden devralındı ve orada
> doğrulandı: ailenin 29.08.2026 CI koşusu uçtan uca yeşildi (setup.exe +
> portable.zip üretildi, Türkçe PDF duman testi gömülü DejaVu ile geçti,
> `--autotest` çıkış 0; W1 ve W5 fiilen, W2-W4 ve W6-W8 dolaylı doğrulandı). W9 da
> ailede doğrulandı (30.08.2026): paketlenmiş exe Windows 11'de gerçek pencere açtı,
> WebView2/pythonnet zinciri çalıştı. Kurucu düzeltmeler (PS1 BOM'u, MSYS2 python
> gölgelemesi, paket içi fontconfig) de aileden gelir.
>
> **OAB Defteri adıyla** CI Windows işi F1a'da yeşil geçti (plan §2.1 "F1a
> durumu"): DLL kapanışı, PyInstaller, paket veri sızıntısı denetimi, Inno
> derlemesi, setup.exe + portable.zip; `--bagimlilik-duman`, `--pdf-duman`,
> `--evrak-duman`, `--autotest`. Windows'ta çarpıyla kapanma (T6) ve 1366×768
> görünümü elle doğrulandı. Kurucunun iki kipi (TK7), UAC ve kapatma olayı henüz
> elle sınanmadı — aşağıdaki çek-listesi.
>
> **Aile iskeletinin F0 spike'ı, kapatma olayı (21.09.2026, Windows 11 + Inno
> Setup 6):** iskeletin `.iss`'i yerel ISCC ile derlendi. Aynı `[Code]` işlevleriyle
> derlenen düşük yetkili bir deneme kurucusu, gerçek `desktop/lock.py` +
> `desktop/instance_channel.py` modüllerini çalıştıran bir taklit programa karşı
> koşturuldu: kapatma olayı gönderildi, program düzenli kapandı, kurucu iki mutex'in
> kaybolmasını süreç bitene dek bekledi (~1 sn). Kapanmayan programda 30 sn
> beklendi, ileti (bastırılmış) İptal'e düştü, süreç zorla sonlandırılmadı. İkinci
> açılış kilidi reddetti ve `Goster` olayını teslim etti. OAB'de olay adı
> `OABDefteri.Kapat`'tır; spike OAB adıyla yinelenmedi. **Doğrulanmayanlar:** gerçek
> kurucu ve kaldırıcı (iki kip), UAC'ye başka bir hesabın kimliği girilmesi (W12),
> paketli exe'de oturum kapanışı — W11, W12, W14 ve çek-listesi 4, 8-12. Çarpıyla
> kapanma (W13, çek-listesi 7) F1a kapısında elle doğrulandı (plan §2.1).

## 1. Doğrulanması gereken varsayımlar

| # | Varsayım | Nerede | Yanlışsa belirtisi |
|---|---|---|---|
| W1 | MSYS2 `mingw-w64-x86_64-ntldd-git` paket adı doğru | CI iş akışı, `dll_kapanisi.py` | pacman "target not found"; `objdump` yedeğine düşülür (betik bunu zaten yapar) |
| W2 | WeasyPrint'in aradığı DLL adları `libpango-1.0-0.dll`, `libpangoft2-1.0-0.dll`, `libharfbuzz-0.dll`, `libgobject-2.0-0.dll`, `libfontconfig-1.dll` desenlerine uyuyor | `dll_kapanisi.py::SEED_PATTERNS` | `--pdf-duman` "cannot load library" ile çöker |
| W3 | `WEASYPRINT_DLL_DIRECTORIES` paket kökünü göstermek yeterli (WeasyPrint ≥60) | `rthook_od.py` | aynı hata; alternatif `os.add_dll_directory()` |
| W4 | fontconfig `<dir>` mutlak yol + `<cachedir>` yazılabilir dizin kabul ediyor | `fonts.conf.tmpl` | PDF üretilir ama font DejaVu değildir → `--pdf-duman` "gömülü DejaVu ile dizilmemiş" hatası verir (duman testi bunu YAKALAR) |
| W5 | WebView2 Evergreen bootstrapper bağlantısı `https://go.microsoft.com/fwlink/p/?LinkId=2124703` | CI iş akışı | indirme 404; elle indirilip `packaging/windows/` altına konur |
| W6 | Inno Setup 6.3+ `ArchitecturesAllowed=x64compatible` destekliyor | `oab-defteri.iss` | derleme hatası → `x64` yazılır (6.2 ve öncesi) |
| W7 | `compiler:Languages\Turkish.isl` Inno kurulumunda mevcut | `oab-defteri.iss` | derleme hatası → dosya Inno deposundan indirilip eklenir |
| W8 | TK7: `PrivilegesRequired=lowest` + `PrivilegesRequiredOverridesAllowed=dialog`; yönetici kipinde `{autopf}` = `Program Files`, kullanıcı kipinde `%LOCALAPPDATA%\Programs`; paketlenmiş program kurulum dizinine hiçbir şey YAZMAZ (fontconfig önbelleği `%LOCALAPPDATA%` altında) | `oab-defteri.iss`, `rthook_od.py` | standart hesapta açılışta "erişim reddedildi" ya da PDF'te font hatası; `OD_RTHOOK_UYARI` değeri `uygulama.log`'a "Paket ortamı uyarısı:" satırı olarak, duman kiplerinde `logs\tanilama.log`'a düşer |
| W9 | pywebview `edgechromium` arka ucu `pythonnet` ile çalışıyor ve PyInstaller ile paketleniyor | `requirements-paketleme.txt`, spec | pencere açılmaz; `webview/lib/*.dll` elle `datas`'a eklenmesi gerekebilir |
| W10 | Kurulum sonrası "programı çalıştır" adımı yükseltilmemiş (kurucuyu başlatan) hesapla koşar | `oab-defteri.iss` `[Run]` (`runasoriginaluser`) | yönetici kipinde veri UAC'ye kimliği girilen hesabın profilinde oluşur |
| W11 | Kapatma olayı kurucu VE kaldırıcıda çalışır: `InitializeSetup`/`InitializeUninstall` → `OpenEventW`+`SetEvent` (kernel32 `external`) → `CheckForMutexes` döngüsü; `AppMutex` yok (tasarım §4.2 "Kurucu ve kaldırıcı"). Derleme ve düşük yetkili spike geçti (yukarıdaki not) | `oab-defteri.iss` `[Code]`, `desktop/instance_channel.py` | kurucu program açıkken dosyaların üzerine yazar ("dosya kullanımda") ya da her seferinde 30 sn bekleyip "Programı kapatıp Yeniden Dene'ye basın" der; kurulum günlüğünde (`/LOG`) "Kapatma olayı açılamadı" satırı |
| W12 | Yönetici kipinde UAC'ye BAŞKA hesabın kimliği girildiğinde yükseltilmiş kurucu programı çalıştıran hesabın olay ve mutex'lerini açabilir: nesneler SY/BA/IU/OW'ye açık güvenlik tanımlayıcısıyla kurulur | `desktop/win32_objects.py` (`MUTEX_SDDL`, `EVENT_SDDL`) | varsayılan tanımlayıcıda olduğu gibi erişim reddi: kurucu "program kapalı" sanıp kuruluma geçer (Inno `OpenMutex` reddini "yok" okur); günlükte "Kapatma olayı açılamadı" |
| W13 | T6 (tasarım §4.5): çarpı programı kapatır, onay sorulmaz; `webview.start` döner, düzenli kapanış (WAL checkpoint + temiz kapanış işareti) yazılır ve çıkış kodu 0'dır; süreç Görev Yöneticisi'nde KALMAZ (elle doğrulama — CI pencereye tıklayamaz) | `desktop/window.py` (`WindowController.on_closing`), `desktop/main.py` | çarpıdan sonra süreç asılı kalır (mutex'ler bırakılmaz, kurucu 30 sn bekler) ya da sonraki açılışta "Önceki oturum beklenmedik biçimde kapandı" |
| W14 | Windows oturum kapanışı/yeniden başlatma programca engellenmez: `closing` işleyicisi kapanmayı hiç iptal etmez (T6); ailedeki `FormClosing` iptal-geri-alma işleyicisi bu yüzden söküldü | `desktop/window.py` | Windows kapanırken "Bu uygulama kapanmayı engelliyor" ekranı; sonraki açılışta günlükte "Önceki oturum beklenmedik biçimde kapandı" |
| W15-W20 | *(F1a-2'de düştü)* Aile iskeletinin ağ kataloğu, güvenlik duvarı, otomatik başlatma, UAC yardımcısı, uyku engeli ve tepsi menüsü varsayımlarıydı; bileşenler sökülünce düştüler. Numaralar yeniden kullanılmaz | — | — |
| W21 | *(lisans kapısı, tasarım §11.4)* Lisans denetimi Windows'ta: PyInstaller'ın son aşama TOC dosyaları (`COLLECT/PYZ/PKG/EXE-00.toc`) `dist\_build-win\oab_defteri\` altında; MSYS2 pacman yerel veritabanı `<msys64>\var\lib\pacman\local\*\{desc,files,mtree}` (setup-msys2 kurulumunda da) ve her DLL'in paketi `share/licenses/` dosyası taşıyor; setup-python'ın `LICENSE.txt`'si `Lib\` ya da kökte. **29.09.2026 aile iskeletinin ilk CI koşusu:** TOC'lar, `D:\a\_temp\msys64` veritabanı, kapanıştaki 30 DLL'in sahibi ve lisans dosyaları, Python'un `LICENSE.txt`'si bulundu — varsayım DOĞRU. Denetim dört bulgu sınıfıyla durdu, hepsi giderildi (`packaging/README.md` "Aile iskeletinin ilk CI Windows koşusunun bulguları"): (A) koşucunun PATH'indeki JDK'dan Universal CRT (43 dosya) → spec `ucrt_suz` + yalın PATH + Inno `MinVersion=10.0`; (B) hooks-contrib `hook-weasyprint`'in topladığı MSYS2 `etc/fonts` (25 dosya) "sahipsiz" → veritabanı %FILES%'teki her tam yolu tutar, DLL dışı dosyada `mtree` sha256 özeti doğrulanır; (C) colorama ve `packaging` (W24); (D) `pywebview-android.jar` → `_webview_platform_disi` Analysis'ten sonra da. Aynı günün doğrulama turu: depo içindeki sanal ortamın RECORD'suz dosyası artık hatadır (en dar kök kuralı); fontconfig yapılandırması spec'te yerleşir, (B)'nin MSYS2 `etc/fonts` dosyaları artık pakete GİRMEZ. Düzeltmeli hat OAB Defteri adıyla F1a CI'ında yeşil geçti (plan §2.1). **Koşuda beklenenler (gerileme DEĞİL):** PyInstaller yalın PATH'te UCRT'yi bulamaz ve çok sayıda `Library not found: could not resolve 'api-ms-win-crt-…'` uyarısı basar (Windows Server 2025'te PyInstaller'ın bu uyarıyı bastırması çalışmaz: `platform.win32_ver()` "2025Server" döndürür); hiçbir ikili `ucrtbase.dll`'i doğrudan içe aktarmadığı için spec'in "Universal CRT'den N dosya ayıklandı" satırı hiç görünmeyebilir; spec "fontconfig: MSYS2'nin etc/fonts ağacından N dosya ayıklandı" yazar (ailenin 29.09.2026 koşusunda 25); `Hidden import 'PySide6…' not found` hataları zararsızdır (`OD_WITH_QT=1`, PySide6 Windows'ta kurulmaz); `paket-icerigi.txt` fontconfig paketi için yalnız `libfontconfig-1.dll`'i yazar | `packaging/lisanslar/lisanslar.py` (`paket`), `build.ps1` "lisans denetimi", spec (`ucrt_suz`, `_webview_platform_disi`, `fontconfig_yerlestir`) | derleme "MSYS2 paket veritabanı yok", "MSYS2 sahibi bulunamayan DLL/dosya", "lisans/telif dosyası bulunamadı", "Universal C çalışma zamanı dosyası pakete girmiş", "MSYS2 dosyasının … özeti yok" / "yerelde değiştirilmiş" , "COLLECT TOC dosyası yok" ya da "paket içi fontconfig …" ile durur |
| W22 | *(F1a-2'de düştü)* Aile iskeletinin pystray kaynak dosyası (`module_collection_mode`) varsayımıydı; tepsi söküldü (tasarım T6, §11 B18). |
| W23 | *(lisans kapısı, tasarım §11.4)* Inno `LicenseFile` UTF-8 **BOM'lu** `LICENSE.txt`'yi Türkçe karakterleri bozmadan gösterir ("DEMİRCİ"); `{app}\THIRD_PARTY_LICENSES\` ve `{app}\LICENSE.txt` kurulur. `MinVersion=10.0` (29.09.2026) Windows 10'dan eski sistemde kurulumu durdurur (paket UCRT taşımaz). Ailenin 29.09.2026 ilk CI koşusu Inno adımına gelmedi; ISCC derlemesi OAB Defteri adıyla F1a CI'ında geçti (plan §2.1), lisans sayfasının görünüşü elle denetlenir | `.iss` `[Setup]`, `lisanslar.py` (`encoding="utf-8-sig"`) | lisans sayfasında "DEMÄ°RCÄ°" gibi bozuk harfler; lisans dizini kurulum klasöründe yok; ISCC `MinVersion` satırında hata |
| W24 | *(aile iskeletinin düzeltme turu)* Pip kısıt dosyası (`lisanslar.py kisitlar --platform windows`): listedeki geçişli bağımlılık sürümlerinin Windows tekerlekleri PyPI'da var (Linux derlemesinde sınandı); kısıt geliştirme kabının sürümlerinden üretilir. **Ailenin 29.09.2026 ilk CI koşusu:** `pip install -c` geçti (tekerlekler var — DOĞRU), ama iki eksik çıktı: (1) kurulum koşucunun PAYLAŞILAN varsayılan Python'una yapılıyordu (actions/runner-images `Install-Pipx.ps1` oraya `pip install pipx` koşar; pipx'in Windows bağımlılığı colorama'yı Django koşullu import eder) → `build.ps1` artık yalıtılmış sanal ortamda (`dist\_venv-win`) kurar ve derler; colorama hiçbir pinin kapanışında olmadığı için listeye girmez; (2) `packaging` Windows kısıtında yoktu (liste onu yalnız Linux'ta biliyordu) → üretici iki platformu ayrı çözer, setuptools'un tercih ettiği kurulu vendored bağımlılık (`KURULUYU_TERCIH_EDEN`) iki platformda işaretlenir. Pakete girmeyen derleme araçları bağımlılıkları (altgraph, pefile, pywin32-ctypes) kısıtta değildir | `build.ps1` adım 2 (sanal ortam), `lisanslar.py` (`Uretici.coz`) | `pip install` "No matching distribution" ya da kaynaktan derleme hatasıyla durur — liste `uret.sh` ile tazelenir; sanal ortam kurulamazsa "Sanal ortam kurulamadı"; kısıtta olmayan bir dağıtım pakete girerse lisans denetimi "THIRD_PARTY_LICENSES'ta olmayan" ya da "… için işaretli değil" der |
| W25 | *(aile iskeletinin düzeltme turu)* MSYS2 paketlerinin `%LICENSE%` alanı SPDX'tir ve pakete giren DLL'lerin sahibi olan paketlerden yalnız GPL görünenler `MSYS2_GPL_IZINLERI`'ndedir (gcc-libs, gettext-runtime, libiconv — DLL düzeyinde izin). **Ailenin 29.09.2026 ilk CI koşusu:** kapanıştaki 30 DLL'in paketlerinde "yalnız GPL" hatası ya da "ayrıştırılamadı" uyarısı çıkmadı — varsayım bugünkü kapanış için DOĞRU. (CI'dan değil, geliştirme makinesinin yerel MSYS2 veritabanından — fontconfig 2.18.2-1: `etc/fonts` dosyalarının sahibi mingw-w64-x86_64-fontconfig'in lisansı `custom`'dır, GPL değil. CI koşusunda bu dosyalar sahiplenilemeden durulmuştu; doğrulama turundan sonra pakete girmezler.) | `lisanslar.py` (`msys2_lisans_denetimi`) | derleme "yalnız GPL lisanslı MSYS2 paketi pakete girmiş: …" ile durur; DLL'in kendi lisansı doğrulanıp izin listesine gerekçeyle eklenir ya da bağımlılık kapanıştan çıkarılır |
| W26 | *(aile iskeletinin doğrulama turu, 29.09.2026)* (a) Paketin statik DLL kapanışı: paketteki her `.exe`, `.dll` ve `.pyd` dosyasının içe aktardığı (gecikmeli dahil) her DLL pakette ya da Windows 10/11'in bileşenidir (`api-ms-win-*`, `ext-ms-win-*`, `WINDOWS_SISTEM_DLL`). Liste geliştirme makinesindeki CPython 3.12, paketin Windows tekerlekleri ve kapanışın 30 MSYS2 DLL'i (88 PE dosyası) okunarak çıkarıldı. Denetim `build.ps1`'in adımıdır; OAB Defteri adıyla F1a CI'ında paketin gerçek içeriğiyle geçti (plan §2.1). (b) Duman testleri Windows'un varsayılan sistem PATH'iyle (`Get-SistemPath`: System32, Windows, Wbem, WindowsPowerShell) geçer — paket koşucunun mingw64\bin'ine, Python'una ya da JDK'sına dayanmaz | `packaging/windows/paket_kapanisi.py`, `build.ps1` (`Invoke-Uygulama`, "paketin statik DLL kapanışı") | (a) derleme "<ad>: ne pakette ne Windows 10/11'in bileşeni" ile durur → eksik DLL kapanışa girer (`dll_kapanisi.py`), ya da ad Windows 10'un System32'sinde bulunduğu doğrulanarak `WINDOWS_SISTEM_DLL`'e gerekçesiyle eklenir; (b) `--bagimlilik-duman` / `--pdf-duman` "cannot load library" ile düşer → eksik DLL pakete girmeli (kullanıcının makinesinde de açılmazdı) |

## 2. Bilinen Windows tuzakları (kodda karşılığı var)

* **GUI exe'yi PowerShell beklemez.** `console=False` ile derlenen exe `&` ile
  çağrılınca PowerShell hemen döner ve `$LASTEXITCODE` anlamsızdır. `build.ps1`
  bu yüzden duman testlerini `Start-Process -Wait -PassThru` ile koşturur.
* **`sys.stdout`/`sys.stderr` `None`'dır.** Penceresiz derlemede konsol yoktur;
  `print()` `AttributeError` üretir. `giris.py` bu yüzden `print` kullanmaz,
  `sys.stderr`'i `None` kontrolüyle yazar. `desktop/logging_setup.py`
  `--autotest` kipinde `StreamHandler(sys.stderr)` kuruyor; Windows'ta bu
  handler sessizce hiçbir şey yazmaz (çökmez, ama Windows'ta `--autotest`
  çıktısı YALNIZ günlük dosyasındadır).
* **MSHTML düşüşü.** pywebview WebView2 bulamazsa eski IE motoruna düşer ve
  React 18 çalışmaz (beyaz pencere). `desktop/window.py` motoru açıkça
  `edgechromium` verir ve registry denetimi yapar — düşüş KODLA ENGELLİ.
* **`%APPDATA%` (Roaming) kullanılmaz.** Gezici profil/OneDrive senkronu açık
  SQLite dosyasını bozar; veri `%LOCALAPPDATA%` altındadır (`desktop/paths.py`).

## 3. İlk Windows koşusu çek-listesi

1. `npm run build` → `frontend\dist` oluştu mu?
2. `powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1`
3. `dist\cikti\pdf-duman.pdf` açılıyor mu; antet, "ĞÜŞİÖÇ ığüşiöç" ve "Sayfa
   1 / 1" altlığı düzgün görünüyor mu? (Duman testi metni zaten pypdf ile
   doğrular; gözle de bakılmalı.)
4. Kurulum paketini **yönetici olmayan** bir hesapta çalıştır → kurucu iki
   seçeneği sunsun (TK7). "Yalnız benim için" → program
   `%LOCALAPPDATA%\Programs\OAB Defteri` altına UAC'siz kurulsun. "Bütün
   kullanıcılar için" → UAC yönetici kimliği istesin, program `C:\Program
   Files\OAB Defteri` altına kurulsun. İki kipte de son adımdaki "çalıştır"
   programı kurucuyu başlatan hesapla açsın ve veri `%LOCALAPPDATA%\OABDefteri`
   altında oluşsun (W8, W10).
5. **WebView2 kurulu OLMAYAN** bir makinede/VM'de aç → Türkçe yönlendirme
   diyaloğu çıksın, program çıkış kodu 7 versin (beyaz pencere DEĞİL).
6. Taşınabilir zip'i USB'den çalıştır → MotW olmadığından SmartScreen çıkmamalı.
7. **Çarpı = çık (T6, W13):** exe açılır, pencerenin çarpısına basılınca
   program onay sormadan kapanır; `oab-defteri.exe` Görev Yöneticisi'nde KALMAZ,
   çıkış kodu 0'dır ve `temiz-kapanis.json` yazılır. Tepsi simgesi yoktur.
8. **İkinci açılış:** program açıkken kısayoldan yeniden aç → pencere öne
   gelir, ikinci süreç 0 koduyla çıkar, ileti kutusu çıkmaz. "Yedekten Geri
   Yükle" kısayolu → "OAB Defteri açık. Programı kapatıp yeniden deneyin." ve
   çıkış kodu 2.
9. **F0 spike: kapatma olayı — CI Windows derlemesinde ve elle kurulum/kaldırmada
   doğrulanacak (W11, W12).** Program açıkken kurucuyu yeniden çalıştır →
   program ≤30 sn içinde kendiliğinden düzenli kapanır ve kurulum sürer; aynısı
   Denetim Masası'ndan kaldırmada. Yönetici kipinde kurucuyu yönetici olmayan
   hesapta başlatıp UAC'ye başka hesabın kimliğini girerek de dene (W12). Program
   kapanmazsa "OAB Defteri açık. Programı kapatıp Yeniden Dene'ye basın." iletisi,
   Yeniden Dene/İptal;
   süreç zorla sonlandırılMAZ. `/LOG` ile koşturulursa günlükte "Kapatma olayı
   gönderildi." ve "Program düzenli kapandı." satırları görünür.
10. **Temiz kapanış işareti (T15):** çarpı ya da "Çık" sonrası
    `%LOCALAPPDATA%\OABDefteri\data\temiz-kapanis.json` VAR; program
    Görev Yöneticisi'nden sonlandırılınca YOK ve sonraki açılışta
    `logs\uygulama.log`'da "Önceki oturum beklenmedik biçimde kapandı" satırı.
11. **Oturum kapanışı (W14):** program açıkken Windows'u yeniden başlat ya
    da oturumu kapat → kapanış engellenmez; sonraki açılışta günlükte "Önceki
    oturum düzenli kapanmış."
12. `--autotest` çıkış kodu 0 ve `uygulama.log`'da "Temiz kapanış işareti
    yazıldı." (duman testi; pencere açılmaz).
13. Defender/AV taraması: onedir olduğu için imzasız da olsa engellenmemeli;
    engellenirse istisna adımları kılavuza yazılır (tasarım §13 D24, F7).

## 3b. Inno kalemlerinin kod durumu

Inno kalemleri kodda ve testte sabittir; ISCC derlemesi OAB Defteri adıyla F1a
CI'ında geçti (plan §2.1). Kurucunun kendisi elle doğrulanır (son sütun). Aile
iskeletinde yerel ISCC 6 ile `/O-` derlemesi 27.09.2026'da iki dalda geçmişti: lisans
dosyaları paket kökündeyken başarılı, `THIRD_PARTY_LICENSES` yokken `#error` ile durdu.

| Kalem | Kodda | Sabitleyen test | Sahada |
|---|---|---|---|
| Yeni AppId GUID, değişmez | `AppId={{A9D4215F-2BDD-4851-8B81-86286AFDE787}` — OAB Defteri'ne özgüdür: F1a-1'de `uuid.uuid4()` ile yeni üretildi; aile programlarının kurucularındaki AppId'lerden farklı olduğu 31.10.2026'da yerel depolarda denetlendi | `packaging/tests/test_surum_yolu.py` (GUID sabit) | aynı sürümün üstüne kurulum ve beta → kararlı yükseltme yan yana kurmaz |
| WebView2 | Evergreen önyükleyicisi CI'da ve `build.ps1`'de indirilir, `[Files]` sonunda koşullu girer (yoksa derleme uyarısı), `[Run]` yalnız `WebView2Eksik` iken sessiz kurar | `packaging/tests/test_kurucu.py::test_iss_her_satir_kendi_bolumunde` | W5, çek-listesi 5 |
| İki mutex | `[Code]` `ProgramMutexleri = 'OABDefteri,Global\OABDefteri'`; `AppMutex` YOK | `desktop/tests/test_lock.py` (adlar programla aynı) | W11, W12, çek-listesi 9 |
| Kapatma olayı | `InitializeSetup`/`InitializeUninstall` → `OABDefteri.Kapat` + 30 sn bekleme, zorla sonlandırma yok | `desktop/tests/test_instance_channel.py`; F0 spike'ı | W11, W12 |
| Lisans sayfası ve üçüncü taraf lisansları | `LicenseFile={#LisansDosyasi}` (paket kökündeki BOM'lu `LICENSE.txt`); `THIRD_PARTY_LICENSES\` `{#SourceDir}\*` ile `{app}`'e kurulur; ikisi yoksa `#error` | `packaging/tests/test_lisans_kapisi.py` | W23 |

## 4. Sonraki sürüm (v2) için

* **Kod imzalama** — Azure Trusted Signing veya SignPath (açık kaynak ücretsiz
  katmanı). İmzalanınca SmartScreen uyarısı ve AV yanlış-pozitif riski düşer.
* **Fixed-Version WebView2** — kilitli/çevrimdışı okul bilgisayarları için
  WebView2'nin sabit sürümünü paketin içine gömen "full" zip varyantı. Bu
  varyant henüz üretilmiyor.

## 5. Saha kabul protokolündeki karşılıklar

W maddelerinin ve §3 çek-listesinin saha kabulü protokolündeki karşılıkları F7'de,
protokolle birlikte yazılır (tasarım §14 F7: ailenin saha kabulü protokolü OAB'ye
uyarlanır). O güne dek bu maddeler §3'teki çek-listesiyle elle doğrulanır.
