"""`--geri-yukle` — yedekten geri yükleme konsol akışı (masaüstü kabuğu).

Bütünlük denetimi bozuk veritabanıyla pencereyi AÇMAZ (desktop/integrity.py);
kullanıcının o noktadaki tek çıkış yolu bu kiptir. Çekirdek iş
`apps.okul.services.backup_restore` içindedir; burası yalnız konsol
etkileşimini ve masaüstü tesisatını (kilit, yollar, Django hazırlığı) yönetir.

WINDOWS PAKETİ PENCERESİZDİR (`console=False`, oab_defteri.spec): std
akımlar None'dır, `input()`/`getpass()` çalışmaz. Bu kip kendi konsol
penceresini AÇAR (AllocConsole) — mevcut bir cmd/PowerShell konsoluna
İLİŞTİRİLMEZ: bekleyen kabuk aynı konsoldan okumaya devam ettiği için yazılan
parola kabuk istemine düşebilirdi (ekranda yankılanır, hatta komut olarak
çalışırdı). Ayrı pencere bu yarışı kökten keser ve akış "Başlat > Çalıştır"
üzerinden, hiç terminal bilmeden de kullanılabilir (kurulum Başlat menüsüne
"Yedekten Geri Yükle" kısayolu koyar — oab-defteri.iss).

Django BURADA AYAĞA KALDIRILIR ama veritabanına DOKUNULMAZ: `prepare_django`
yalnız ayarları ve uygulama kayıt defterini yükler; göç ve bütünlük denetimi
bu kipte KOŞULMAZ (bozuk veritabanı bu kipin varlık sebebidir).

Yedekler daima şifrelidir (tasarım §4.4.7; düz yedek dalı söküldü, §13 D29): program
yöneticisi hesabının tanıtıcısı ve parolası (`--hesap` + `--parola`; aynı bilgisayarda güncel
`guvenlik.json` ile) ya da kurtarma anahtarı her geri yüklemede istenir (tasarım
§4.4.4, TK10). Parola yolunda geri yüklemeyi yalnız program yöneticisi yapar: rol denetimi
çekirdektedir (`geri_yukleme_yetkisi`; güncel veritabanı salt okunur `sqlite3` ile, ORM'siz,
okunamazsa yedeğin görüntüsü), parola doğrulandıktan sonra ve kenara alma yapılmadan önce koşar.
Ret `GeriYuklemeYetkisiz`'dir (bir `BackupRestoreError`): hiçbir dosya değişmez, ileti
gösterilir, çıkış kodu 9'dur. Kurtarma anahtarı yolunda rol denetimi yoktur (anahtarın
kendisi yetkidir). Girişe açık program yöneticisi taşımayan yedek (kurulum yedeği) iki yolda da
reddedilir (kullanıcı kararı 07.11.2026; `backup_restore` modül başlığı "HESAPSIZ YEDEK"): hiçbir dosya
değişmez, ileti gösterilir, çıkış kodu 9'dur. Güvenlik dosyası kayıpsa (tasarım
§4.3 tehdit 8) bu kip de çıkış yoludur: çekirdek `guvenlik.json`'u yedeğin kurtarma
başlığından (yalnız kurtarma bölümüyle) yeniden yazar.

Onay yedeğin kapsamını söyler; çekirdek bozuk ek bulursa hiçbir şey değişmeden durur ve bu kip liste
yazıp ikinci kez sorar, onaylanırsa kayıtlar o ekler olmadan geri yüklenir (kullanıcı kararı 04.11.2026
"Bozuk ekte geri yükleme durur, ikinci onayla sürer"). `--evet` ikinci onay sayılmaz: konsol yoksa
geri yükleme yapılmaz. İkinci deneme doğrulamayı baştan koşar. Eksik ve bozuk ekler kişisiz listelenir.

Kullanıcının verdiği dosyanın adı ve yerel yollar günlüğe yazılmaz (R1; yol işletim sistemi hesabının
adını taşıyabilir): çekirdek adı süzerek kendisi yazar, konsol iletisi onları göstermeyi sürdürür.

Yarım işlerin artıkları bu kipte de silinir (plan F1b-3 "Geri yükleme"; `masaustu_kanca`): veritabanı
bozukken program açılmaz, açılış temizliği koşmaz; kesilen bir denemenin hazırlık dizini yeniden
denemenin yerini tüketirdi. Kilit alınmıştır, artıklar sahipsizdir. Yetim taraması bu kipte koşmaz.

Başarılı geri yükleme temiz kapanış işaretini yazar (07.11.2026 sınaması; `desktop.clean_shutdown`):
ilk açılış veritabanının yokluğundan anlaşılır, bu kip veritabanını koyar, işaret yazmazsa sonraki
açılış boş klasörde de yanlış "Son Oturumu Kontrol Edin" kartı verirdi. Bu kipte oturum açık değildir,
yerine konan kayıtlar tamdır; önceki oturum çökmüş ya da veritabanı bozuk olsa da aynıdır. İptal ve
hatada veritabanı değişmez: işarete dokunulmaz.
"""

from __future__ import annotations

import argparse
import logging
import sys
from getpass import getpass
from pathlib import Path
from typing import Any

from desktop.backup import DEFAULT_KEEP_DAYS, KAPSAM_METINLERI
from desktop.backup_crypto import BACKUP_SUFFIX, BackupCryptoError, kap_basligini_oku
from desktop.clean_shutdown import write_marker_quietly
from desktop.dialogs import show_error
from desktop.django_bootstrap import prepare_django
from desktop.errors import EXIT_OK, EXIT_RESTORE_FAILED, AlreadyRunningError
from desktop.lock import SingleInstanceLock
from desktop.logging_setup import gunluk_dosyasi_yeri
from desktop.paths import AppPaths, resolve_backend_dir
from desktop.version import get_app_version

logger = logging.getLogger("oab_defteri.restore")

#: Tasarım §4.2 adım 2: tepsi anlatılmaz (T6); program çarpıyla ya da Çık ile kapanır.
RUNNING_MESSAGE = "OAB Defteri açık. Programı kapatıp yeniden deneyin."

# Kendi açtığımız konsol penceresi süreçle birlikte kapanır; sonucu okutmak
# için çıkışta Enter beklenir. Yalnız AllocConsole başarılıysa True olur.
_allocated = False


class RestoreCliError(Exception):
    """Akışı durduran, kullanıcıya olduğu gibi gösterilecek Türkçe mesaj.

    `gunluk`: iletinin günlüğe yazılacak hâli; ileti serbest ad taşıyorsa verilir (R1).
    """

    def __init__(self, ileti: str, *, gunluk: str | None = None) -> None:
        super().__init__(ileti)
        self.gunluk = ileti if gunluk is None else gunluk


def run_restore(paths: AppPaths, args: argparse.Namespace) -> int:
    """Geri yükleme kipinin girişi; tek-instance kilidini kendisi alır.

    Çalışan kopya varsa pencere öne getirilmez (sinyal yalnız bayraksız normal
    açılışındır): ileti gösterilir ve 2 koduyla çıkılır.
    """
    lock = SingleInstanceLock(paths.lock_path)
    try:
        lock.acquire()
    except AlreadyRunningError as exc:
        logger.warning("Geri yükleme reddedildi: program çalışıyor.")
        show_error(exc.title, RUNNING_MESSAGE)
        return exc.exit_code
    try:
        return _restore_flow(paths, args)
    finally:
        lock.release()


def _restore_flow(paths: AppPaths, args: argparse.Namespace) -> int:
    interactive = False
    kod = EXIT_RESTORE_FAILED
    try:
        interactive = ensure_console()
        kod = _run_steps(paths, args, interactive)
    except RestoreCliError as hata:
        _report_error(str(hata), interactive, gunluk=hata.gunluk)
    except Exception:  # noqa: BLE001 — kip her hatada Türkçe mesajla bitmeli
        logger.exception("Geri yükleme beklenmeyen hatayla durdu.")
        _report_error(
            "Geri yükleme beklenmeyen bir hatayla durdu; ayrıntı "
            f"{gunluk_dosyasi_yeri(paths.logs)} dosyasındadır.",
            interactive,
            gunluk="Geri yükleme beklenmeyen bir hatayla durdu.",
        )
    _pause_before_exit(skip=bool(getattr(args, "evet", False)))
    return kod


def _run_steps(paths: AppPaths, args: argparse.Namespace, interactive: bool) -> int:
    # Ayarlar + uygulama kaydı; sorgu YOK (backup_restore importu bunu ister).
    prepare_django(resolve_backend_dir(), paths.data)
    servis = _load_service()
    _artiklari_temizle(paths)

    if interactive:
        print("OAB Defteri — yedekten geri yükleme")
        print(f"Veri klasörü : {paths.data}")
        print(f"Yedek klasörü: {paths.backups}\n")

    yedek = _choose_backup(paths, args, interactive)
    if yedek is None:
        if interactive:
            print("Geri yükleme iptal edildi.")
        return EXIT_OK

    hesap: str | None = str(getattr(args, "hesap", "") or "") or None
    parola: str | None = str(getattr(args, "parola", "") or "") or None
    anahtar: str | None = str(getattr(args, "kurtarma_anahtari", "") or "") or None
    if parola and not hesap:
        raise RestoreCliError(
            "--parola ile birlikte program yöneticisi hesabının tanıtıcısını da verin "
            "(--hesap); ya da --kurtarma-anahtari kullanın."
        )
    if not parola and not anahtar:
        if not interactive:
            raise RestoreCliError(
                "Yedekler şifrelidir; --hesap ile --parola ya da --kurtarma-anahtari verin "
                "veya komutu etkileşimli bir uçbirimden çalıştırın."
            )
        hesap, parola, anahtar = _ask_secret()

    if interactive:
        print(f"\nYedek : {yedek.name}")
        kapsam = _kapsam_metni(yedek)
        if kapsam is not None:
            print(f"Kapsam: {kapsam}")
        print(f"Hedef : {paths.db_path}")
        print(
            "Mevcut veritabanı 'db-onceki-*' adıyla aynı klasörde "
            f"{DEFAULT_KEEP_DAYS} gün saklanır, sonra silinir."
        )
    if not args.evet:
        if not interactive:
            raise RestoreCliError("Onay sorusu sorulamadı (konsol yok); --evet ile çalıştırın.")
        if not _confirm():
            print("Geri yükleme iptal edildi.")
            return EXIT_OK

    sonuc = _geri_yukle(
        servis,
        yedek,
        paths,
        hesap=hesap,
        parola=parola,
        anahtar=anahtar,
        interactive=interactive,
    )
    if sonuc is None:
        print("Geri yükleme iptal edildi.")
        return EXIT_OK

    write_marker_quietly(paths.data, get_app_version())
    if interactive:
        print("\nGeri yükleme tamamlandı.")
        _ekleri_yaz(sonuc.dosya_raporu)
        if sonuc.old_db_path is not None:
            print(f"Önceki veritabanı kenara alındı: {sonuc.old_db_path}")
        if sonuc.state_written:
            print(
                "guvenlik.json yedekteki kurtarma başlığından yeniden yazıldı; programı "
                "kurtarma anahtarıyla açıp program yöneticisinin parolasını belirleyin."
            )
        print("Programı şimdi normal şekilde açabilirsiniz.")
    return EXIT_OK


def _geri_yukle(
    servis: Any,
    yedek: Path,
    paths: AppPaths,
    *,
    hesap: str | None,
    parola: str | None,
    anahtar: str | None,
    interactive: bool,
) -> Any:
    """Çekirdeği çağırır; bozuk ekte durursa ikinci kez sorar. Vazgeçilirse None (modül başlığı)."""

    def _cagir(*, ekler_olmadan_surdur: bool) -> Any:
        return servis.restore_database(
            yedek,
            paths.db_path,
            hesap=hesap,
            password=parola,
            recovery_key=anahtar,
            ekler_olmadan_surdur=ekler_olmadan_surdur,
        )

    try:
        try:
            return _cagir(ekler_olmadan_surdur=False)
        except servis.EkOnayiGerekli as durma:
            if not interactive:
                raise
            print(f"\n{durma}")
            _ekleri_yaz(durma.rapor)
            if not _ikinci_onay():
                return None
            return _cagir(ekler_olmadan_surdur=True)
    except (BackupCryptoError, servis.BackupRestoreError) as hata:
        raise RestoreCliError(str(hata)) from hata


def _kapsam_metni(yedek: Path) -> str | None:
    """Yedeğin kapsamının metni, yalnız başlıktan; okunamıyorsa None: hatayı çekirdek söyler."""
    try:
        return KAPSAM_METINLERI[kap_basligini_oku(yedek).kapsam]
    except (OSError, BackupCryptoError):
        return None


def _ekleri_yaz(rapor: Any) -> None:
    """Eksik ve bozuk eklerin kişisiz listesi; yoksa bir şey yazılmaz."""
    satirlar = rapor.metin_satirlari()
    if satirlar:
        print("Eksik ya da bozuk ekler:")
    for satir in satirlar:
        print(f"  {satir}")


# ---------------------------------------------------------------------------
# Konsol tesisatı
# ---------------------------------------------------------------------------
def ensure_console() -> bool:
    """Etkileşimli konsol akımlarını hazırlar; başarısızsa False döner."""
    if sys.stdin is not None and sys.stdout is not None:
        return True
    if sys.platform != "win32":
        return False

    global _allocated
    import ctypes

    kernel32 = ctypes.windll.kernel32
    if kernel32.GetConsoleWindow() == 0:
        if not kernel32.AllocConsole():
            return False
        _allocated = True
    # Türkçe karakterler için UTF-8 kod sayfası; akımlar yeni konsola bağlanır.
    kernel32.SetConsoleCP(65001)
    kernel32.SetConsoleOutputCP(65001)
    kernel32.SetConsoleTitleW("OAB Defteri — yedekten geri yükleme")
    try:
        sys.stdin = open("CONIN$", encoding="utf-8")
        sys.stdout = open("CONOUT$", "w", encoding="utf-8")
        sys.stderr = open("CONOUT$", "w", encoding="utf-8")
    except OSError:
        return False
    return True


def _pause_before_exit(*, skip: bool) -> None:
    """Kendi konsol penceremiz varsa kullanıcı sonucu okuyana dek bekler."""
    if not _allocated or skip:
        return
    try:
        input("\nKapatmak için Enter tuşuna basın...")
    except (EOFError, OSError):
        pass


def _report_error(message: str, interactive: bool, *, gunluk: str | None = None) -> None:
    logger.error("Geri yükleme başarısız: %s", message if gunluk is None else gunluk)
    if interactive:
        print(f"\nHATA: {message}")
    else:
        show_error("Geri yükleme başarısız", message, gunluk=gunluk)


# ---------------------------------------------------------------------------
# Yedek seçimi ve sır istemleri
# ---------------------------------------------------------------------------
def list_backups(backup_dir: Path) -> list[Path]:
    """Yedek klasöründeki `.odbak` dosyaları — en yeniden eskiye."""
    if not backup_dir.is_dir():
        return []
    dosyalar = [yol for yol in backup_dir.glob(f"*{BACKUP_SUFFIX}") if yol.is_file()]
    dosyalar.sort(key=lambda yol: yol.stat().st_mtime, reverse=True)
    return dosyalar


def _choose_backup(paths: AppPaths, args: argparse.Namespace, interactive: bool) -> Path | None:
    istenen = str(args.geri_yukle or "")
    if istenen:
        yol = Path(istenen).expanduser()
        if yol.is_file():
            return yol
        # Yalnız dosya adı verildiyse yedek klasöründe aranır.
        aday = paths.backups / istenen
        if aday.is_file():
            return aday
        raise RestoreCliError(
            f"Yedek dosyası bulunamadı: {istenen}", gunluk="Yedek dosyası bulunamadı."
        )
    if not interactive:
        raise RestoreCliError("Yedek dosyası belirtilmedi ve seçim için konsol açılamadı.")
    yedekler = list_backups(paths.backups)
    if not yedekler:
        raise RestoreCliError(
            f"Yedek klasöründe geri yüklenebilir dosya yok: {paths.backups}",
            gunluk="Yedek klasöründe geri yüklenebilir dosya yok.",
        )
    return _pick_backup(yedekler)


def _pick_backup(yedekler: list[Path]) -> Path | None:
    print("Bu bilgisayardaki yedekler (en yeniden eskiye):")
    for sira, yol in enumerate(yedekler, start=1):
        boyut = max(1, yol.stat().st_size // 1024)
        print(f"  {sira:2d}) {yol.name}  ({boyut} KB)")
    while True:
        try:
            secim = input("Geri yüklenecek yedeğin numarası (vazgeçmek için boş bırakın): ").strip()
        except EOFError:
            return None
        if not secim:
            return None
        if secim.isdigit() and 1 <= int(secim) <= len(yedekler):
            return yedekler[int(secim) - 1]
        print("Geçersiz seçim; listedeki numaralardan birini yazın.")


def _read_secret(prompt: str) -> str:
    """Parolayı EKRANA YANSITMADAN okur (birleşme incelemesi bulgusu).

    Paketli Windows'ta `sys.stdin` CONIN$ ile DEĞİŞTİRİLMİŞTİR; stdlib
    `getpass.win_getpass` bunu görünce (`sys.stdin is not sys.__stdin__`)
    yankılı `fallback_getpass`e düşer ve parola ekranda görünürdü. Konsoldan
    doğrudan okuyan msvcrt yolu bu tuzağa girmez; diğer platformlarda getpass
    zaten doğru çalışır.
    """
    if sys.platform == "win32":
        import msvcrt

        print(prompt, end="", flush=True)
        karakterler: list[str] = []
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                print()
                return "".join(karakterler)
            if ch == "\x03":  # Ctrl+C → boş giriş say (akış "girilmedi" hatasıyla biter)
                print()
                return ""
            if ch == "\x08":  # Backspace
                if karakterler:
                    karakterler.pop()
                continue
            if ch in ("\x00", "\xe0"):  # işlev tuşu ön eki — ikinci kodu yut
                msvcrt.getwch()
                continue
            karakterler.append(ch)
    try:
        return getpass(prompt)
    except EOFError:
        return ""


def _ask_secret() -> tuple[str | None, str | None, str | None]:
    """(hesap tanıtıcısı, parola, kurtarma anahtarı) — parola ya da anahtar dolu döner."""
    try:
        hesap = input(
            "Program yöneticisi hesabının tanıtıcısı (kurtarma anahtarıyla açmak için boş bırakın): "
        )
    except EOFError:
        hesap = ""
    hesap = hesap.strip()
    if hesap:
        parola = _read_secret("Parolanız: ")
        if not parola:
            raise RestoreCliError("Parola girilmedi.")
        return hesap, parola, None
    try:
        anahtar = input("Kurtarma anahtarı (yazdırdığınız kâğıttaki): ").strip()
    except EOFError:
        anahtar = ""
    if not anahtar:
        raise RestoreCliError("Hesap ve parola ya da kurtarma anahtarı girilmedi.")
    return None, None, anahtar


def _evet_mi(soru: str) -> bool:
    try:
        yanit = input(soru).strip().lower()
    except EOFError:
        return False
    return yanit in {"e", "evet"}


def _confirm() -> bool:
    return _evet_mi("Devam edilsin mi? [e/H] ")


def _ikinci_onay() -> bool:
    return _evet_mi("Kayıtlar bu ekler olmadan geri yüklensin mi? [e/H] ")


def _artiklari_temizle(paths: AppPaths) -> None:
    """Yarım işlerin artıklarını siler (modül başlığı); hata geri yüklemeyi durdurmaz.

    Veritabanına dokunmaz. Backend yoksa (masaüstü birim testi) sessiz.
    """
    try:
        from apps.okul.masaustu_kanca import artiklari_temizle
    except ImportError:
        return
    try:
        artiklari_temizle(paths.db_path, paths.backups, paths.dosya_deposu)
    except Exception as hata:  # noqa: BLE001 — temizlik kurtuluş yolunu kapatamaz
        logger.warning("Yarım işlerin artıkları silinemedi (%s).", type(hata).__name__)


def _load_service() -> Any:
    """Backend çekirdeğini yükler (Django hazırlandıktan SONRA çağrılır).

    Import fonksiyon içindedir: masaüstü birim testleri asgari Django
    ayarlarıyla koşar ve `apps.okul` ancak gerçek ayarlarla import edilebilir.
    """
    from apps.okul.services import backup_restore

    return backup_restore
