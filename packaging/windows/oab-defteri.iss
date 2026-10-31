; =============================================================================
;  oab-defteri.iss — Inno Setup kurulum betiği (Windows)
; =============================================================================
;  BU DOSYA BU ORTAMDA DOĞRULANMADI — ilk Windows koşusunda sınanacak.
;
;  Kurulum yetkisi (tasarım §2.2 TK7, §15 M-1):
;   * PrivilegesRequired=lowest + PrivilegesRequiredOverridesAllowed=dialog →
;     kurucu iki seçeneği sunar. Kullanıcı başına kurulum ({autopf} =
;     %LOCALAPPDATA%\Programs) yalnız programı kendi Windows hesabında tek başına
;     kullanan senaryo içindir. Ortak "OAB" Windows hesabında kurulum YÖNETİCİ
;     kipinde yapılır ({autopf} = Program Files): kurulum dizini standart
;     kullanıcıya salt okunur kalır (tasarım §4.3 tehdit 20). Kılavuz iki
;     senaryoyu ayrı yazar.
;   * Program kurulum dizinine hiçbir şey yazmaz (veri, günlük ve fontconfig
;     önbelleği %LOCALAPPDATA% altında).
;   * WebView2 Runtime yoksa gömülü Evergreen kurucusu sessizce çalıştırılır.
;   * Kullanıcı verisi kurulum dizininde DEĞİLDİR; kaldırma veriyi silmez.
;   * Lisans sayfası LICENSE.txt'dir (PolyForm Noncommercial); üçüncü taraf
;     lisansları {app}\THIRD_PARTY_LICENSES\ altına kurulur (F12, TB28).
;   * Kurucu ve kaldırıcı açık programı `OABDefteri.Kapat` adlı olayıyla DÜZENLİ
;     kapatır ve iki mutex'in kaybolmasını bekler (tasarım §4.2; aşağıdaki
;     [Code]). Inno `AppMutex` KULLANILMAZ.
;   * Program ağ servisi sunmaz: yönetim sunucusu yalnız 127.0.0.1'de, rastgele
;     portta ve oturum belirteciyle dinler; hiçbir port okul ağına açılmaz. Bu
;     yüzden güvenlik duvarı kuralı, otomatik başlatma ve tepsi görevi yoktur
;     (tasarım §4.1, §4.5 T6).
;
;  Derleme (build.ps1 çağırır):
;    iscc /DAppVersion=2026.9.0 /DNumericVersion=2026.9.0.0 ^
;         /DSourceDir=...\dist\paket-win\oab-defteri /DOutputDir=...\dist\cikti ^
;         packaging\windows\oab-defteri.iss
; =============================================================================

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef NumericVersion
  #define NumericVersion "0.0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\..\dist\paket-win\oab-defteri"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\dist\cikti"
#endif

#define AppName "OAB Defteri"
#define AppExeName "oab-defteri.exe"
#define AppUserModelId "OABDefteri.Desktop"
#define AppIconSource "..\ikonlar\oab-defteri.ico"
#define InstalledIconName "oab-defteri-" + AppVersion + ".ico"
#define WebView2Setup "MicrosoftEdgeWebView2Setup.exe"
; Lisanslar (F12, TB28): build.ps1 PyInstaller çıktısının KÖKÜNE LICENSE.txt'yi
; (PolyForm Noncommercial, UTF-8 BOM'lu — Inno BOM'suz metni ANSI okur) ve
; THIRD_PARTY_LICENSES\ dizinini koyar (packaging/lisanslar/lisanslar.py paket).
; İkisi `{#SourceDir}\*` ile {app}'e kurulur. Biri eksikse kurucu DERLENMEZ:
; lisanssız kurulum dosyası üretilmez.
#define LisansDosyasi AddBackslash(SourceDir) + "LICENSE.txt"
#define UcuncuTarafDizini AddBackslash(SourceDir) + "THIRD_PARTY_LICENSES"
#if !FileExists(LisansDosyasi) && !FileExists(AddBackslash(SourcePath) + LisansDosyasi)
  #error "LICENSE.txt paket kökünde yok — önce build.ps1'in lisans adımı koşmalı."
#endif
#if !FileExists(UcuncuTarafDizini + "\BENIOKU.txt") && !FileExists(AddBackslash(SourcePath) + UcuncuTarafDizini + "\BENIOKU.txt")
  #error "THIRD_PARTY_LICENSES paket kökünde yok — önce build.ps1'in lisans adımı koşmalı."
#endif

[Setup]
; AppId ASLA DEĞİŞMEZ — değişirse yükseltmeler yan yana kurulur.
AppId={{A9D4215F-2BDD-4851-8B81-86286AFDE787}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
VersionInfoVersion={#NumericVersion}
AppPublisher=OAB Defteri
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; TK7: kurucu "yalnız benim için" (kullanıcı başına) ve "bütün kullanıcılar için"
; (yönetici) seçeneklerini sunar; {autopf}, {group} ve {autodesktop} seçilen kipe
; göre çözülür (başlıktaki açıklama).
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Program yalnız Windows 10/11'i hedefler. Paket Windows'un Universal C çalışma zamanını
; (ucrtbase.dll, api-ms-win-*.dll) TAŞIMAZ: Windows 10 ve sonrasında işletim sisteminin
; bileşenidir (packaging/lisanslar/lisanslar.py UCRT_DLL). Daha eski sürümde kurucu durur.
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename=oab-defteri-{#AppVersion}-win64-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#AppIconSource}
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
; Kurulum sihirbazının lisans sayfası: programın kendi lisansı. Üçüncü taraf
; lisansları {app}\THIRD_PARTY_LICENSES\ altına kurulur (BENIOKU.txt).
LicenseFile={#LisansDosyasi}
; `AppMutex` bilerek YOK (tasarım §2.3, §4.2-5, denetim GA-15): Inno onu hem
; kurucuda hem kaldırıcıda denetler; kaldırıcı kapatma olayını gönderecek aşamaya
; gelmeden "programı kapatın" iletisinde beklerdi. Program çalışırken yükseltme
; yapılmaması güvencesi `[Code]` içindeki `ProgramiKapat`tadır.

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Ek kısayollar:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#AppIconSource}"; DestDir: "{app}"; DestName: "{#InstalledIconName}"; Flags: ignoreversion
; WebView2 Evergreen kurucusu — build.ps1 indirdiyse pakete girer. Bu blok [Files]
; bölümünün SONUNDA kalır: arasına başka bölüm başlığı girerse `Source:` satırı o
; bölüme düşer ve ISCC derlemeyi kırar (paket testi bölüm yerleşimini sınar).
#if FileExists(AddBackslash(SourcePath) + WebView2Setup)
Source: "{#WebView2Setup}"; DestDir: "{app}"; Flags: ignoreversion
#else
; Sessiz düşme tuzağı kapatıldı: dosya yoksa derleme kırılmaz ama uyarı basılır
; (WebView2'siz makinede kurulum biter, program çıkış kodu 7 ile kapanırdı).
#pragma warning "WebView2 kurucusu (" + WebView2Setup + ") bulunamadı — paket onsuz üretiliyor."
#endif

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#InstalledIconName}"; AppUserModelID: "{#AppUserModelId}"
; Geri yükleme kipi: bozuk veritabanında bütünlük denetimi pencereyi açmaz;
; hata iletisi kullanıcıyı bu kısayola yönlendirir (desktop/integrity.py).
; Kip kendi konsol penceresini açar (desktop/restore.py, AllocConsole).
Name: "{group}\{#AppName} — Yedekten Geri Yükle"; Filename: "{app}\{#AppExeName}"; Parameters: "--geri-yukle"; IconFilename: "{app}\{#InstalledIconName}"; Comment: "Veritabanını bir yedekten geri yükler"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#InstalledIconName}"; AppUserModelID: "{#AppUserModelId}"; Tasks: desktopicon

[InstallDelete]
; Sürüm bazlı ad Windows ikon önbelleğini yeniler; eski sürüm ikonları temizlenir.
Type: files; Name: "{app}\oab-defteri-*.ico"

[Run]
; WebView2 yoksa önce onu kur (sessiz). Kurulamazsa kurulum yine tamamlanır;
; program ilk açılışta Türkçe yönlendirme verir (desktop/window.py).
Filename: "{app}\{#WebView2Setup}"; Parameters: "/silent /install"; \
    StatusMsg: "Microsoft Edge WebView2 bileşeni kuruluyor..."; \
    Check: WebView2Eksik and WebView2KurucusuVar; Flags: waituntilterminated skipifdoesntexist
; Program YÜKSELTİLMİŞ kimlikle açılmamalı: veri, programı çalıştıran hesabın
; %LOCALAPPDATA%'sına yazılır; yönetici kurulumunda UAC'ye başka bir kimlik
; girildiyse yükseltilmiş süreç veriyi o hesabın profiline açardı. `runasoriginaluser` postinstall girdilerinde
; zaten varsayılandır; niyet belgelensin diye açıkça yazılır.
Filename: "{app}\{#AppExeName}"; Description: "{#AppName} programını çalıştır"; \
    Flags: nowait postinstall skipifsilent runasoriginaluser

[Messages]
turkish.FinishedLabel=Kurulum tamamlandı.%n%nVerileriniz (birlik kayıtları ve yedekler) programın kurulduğu klasörde DEĞİL, kullanıcı klasörünüzde saklanır. Programı kaldırsanız bile kayıtlarınız silinmez.

[Code]
const
  WebView2ClientId = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';
  // Kapatma yolu (tasarım §4.2-5). Adlar programla BİREBİR aynı olmak zorunda:
  // desktop/instance_channel.py::QUIT_EVENT_NAME ve desktop/lock.py::APP_MUTEX_NAMES
  // (eşitliği desktop/tests/test_lock.py ve test_instance_channel.py denetler).
  KapatOlayi = 'OABDefteri.Kapat';
  ProgramMutexleri = 'OABDefteri,Global\OABDefteri';
  EVENT_MODIFY_STATE = $0002;
  KapanmaSuresiMs = 30000;
  BeklemeAdimiMs = 250;

// kernel32 — Pascal Script'in kendi işlevleriyle çakışmasın diye `Od` önekli.
// Program olayı ve mutex'leri Yöneticiler'e açık bir güvenlik tanımlayıcısıyla
// kurar (desktop/win32_objects.py): yönetici kipinde yükseltilmiş kurucu, programı
// çalıştıran hesabın nesnelerini böylece açabilir.
function OdOpenEvent(DesiredAccess: DWORD; InheritHandle: BOOL; Name: String): THandle;
  external 'OpenEventW@kernel32.dll stdcall';
function OdSetEvent(Event: THandle): BOOL;
  external 'SetEvent@kernel32.dll stdcall';
function OdCloseHandle(Handle: THandle): BOOL;
  external 'CloseHandle@kernel32.dll stdcall';

function ProgramCalisiyor: Boolean;
begin
  Result := CheckForMutexes(ProgramMutexleri);
end;

// Program açıksa `Kapat` olayını işaretler; program düzenli kapanır
// (pencere, yönetim sunucusu, temiz kapanış işareti). Olay yoksa (program
// başka bir Windows oturumunda ya da henüz açılıyor) yalnız beklenir.
procedure KapatmaOlayiniGonder;
var
  Olay: THandle;
begin
  Olay := OdOpenEvent(EVENT_MODIFY_STATE, False, KapatOlayi);
  if Olay = 0 then
  begin
    Log('Kapatma olayı açılamadı (program bu oturumda dinlemiyor olabilir).');
    Exit;
  end;
  if OdSetEvent(Olay) then
    Log('Kapatma olayı gönderildi.')
  else
    Log('Kapatma olayı işaretlenemedi.');
  OdCloseHandle(Olay);
end;

// İki mutex de kaybolana dek (süreç tamamen bitene dek) en çok `Sure` ms bekler.
function ProgramKapanincaDekBekle(Sure: Integer): Boolean;
var
  Gecen: Integer;
begin
  Gecen := 0;
  while ProgramCalisiyor and (Gecen < Sure) do
  begin
    Sleep(BeklemeAdimiMs);
    Gecen := Gecen + BeklemeAdimiMs;
  end;
  Result := not ProgramCalisiyor;
end;

// Kurucu ve kaldırıcının ortak kapısı. Süreç ZORLA sonlandırılmaz: program
// 30 sn'de kapanmazsa kullanıcıdan programı kapatması istenir (tasarım §4.2);
// Yeniden Dene olayı yeniden gönderir, İptal kurulumu/kaldırmayı durdurur.
function ProgramiKapat: Boolean;
begin
  Result := True;
  while ProgramCalisiyor do
  begin
    KapatmaOlayiniGonder;
    if ProgramKapanincaDekBekle(KapanmaSuresiMs) then
    begin
      Log('Program düzenli kapandı.');
      Exit;
    end;
    if SuppressibleMsgBox('OAB Defteri açık. Programı kapatıp Yeniden Dene''ye basın.',
        mbError, MB_RETRYCANCEL, IDCANCEL) <> IDRETRY then
    begin
      Log('Program kapanmadı; kullanıcı vazgeçti.');
      Result := False;
      Exit;
    end;
  end;
end;

function InitializeSetup: Boolean;
begin
  Result := ProgramiKapat;
end;

function InitializeUninstall: Boolean;
begin
  Result := ProgramiKapat;
end;

// Evergreen WebView2 Runtime kayıt defterinde 'pv' sürümüyle kendini bildirir.
// (Aynı üç anahtar desktop/window.py'de de denetlenir — tek doğruluk kaynağı
// orasıdır; burada yalnız kurucunun çalıştırılıp çalıştırılmayacağı belirlenir.)
function WebView2Eksik: Boolean;
var
  Surum: String;
begin
  Result := True;
  if RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\' + WebView2ClientId, 'pv', Surum) then
    if (Surum <> '') and (Surum <> '0.0.0.0') then Result := False;
  if Result and RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\' + WebView2ClientId, 'pv', Surum) then
    if (Surum <> '') and (Surum <> '0.0.0.0') then Result := False;
  if Result and RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\' + WebView2ClientId, 'pv', Surum) then
    if (Surum <> '') and (Surum <> '0.0.0.0') then Result := False;
end;

function WebView2KurucusuVar: Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\{#WebView2Setup}'));
end;

