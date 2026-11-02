"""OAB Defteri masaüstü başlatıcısı — açılış ve kapanış sırası (tasarım §4.2).

    1. Veri dizinleri (exe DIŞINDA) + günlük yapılandırması; Linux'ta önce
       `umask 077`, dizinler 0700 (§4.5, §13 D52)
    2. Tek-instance kilidi ................. ikinci kopya pencere AÇMAZ; bayraksız
       normal açılışsa çalışan kopyanın penceresini öne getirip 0 ile çıkar
    3. Temiz kapanış işareti okunur ve silinir (T15) + tek kopya kanalı kurulur
    4. Oturum belirteci ..................... ayarlar okunmadan ÖNCE üretilir
    5. Sürüm damgası ........................ eski program yeni veriyi AÇMAZ
       (damga yoksa 8'den önce veritabanının göç kaydı da denetlenir — §4.2 adım 5)
    6. Bütünlük denetimi .................... bozuk veriyle pencere AÇILMAZ
    7. Günlük yedek + 14 gün rotasyonu ...... `Connection.backup()`; yalnız şifreli
       `.odbak`. İlk program yöneticisi hesabı kurulmadan (ilk açılış) yedek atlanır; bugünün
       yedeği alınmadıysa rotasyon da koşmaz (tasarım §4.2 adım 7; yedekler §4.4.7)
    8. Göç öncesi yedek + `migrate --no-input`; ardından 7-8'in olguları (alınan ve silinen
       yedekler, uygulanan göçler) denetim izine `YEDEK` ve `GOC` olarak verilir — bu adımlar
       Django ve tablo hazır olmadan olur, olgular tamponlanır, göçten SONRA `masaustu_kanca`
       üzerinden yazılır (kilitli kipte; tasarım §4.6.3, plan F1b-1 "Denetim izi")
    9. Gömülü sunucu (waitress, 127.0.0.1, boş port) + sağlık denetimi
   10. Çıkış kancası backend'e kaydolur (`masaustu_kanca`, §4.2 adım 10); `od-gunluk`
       başlar: gün değişimi kapısını koşar (günlük yedek + rotasyon + backend'in kaydettiği
       işler, ör. erişim günlüğünün saklama silmesi; saatte bir yinelenir, her iş ortak bakım
       kapısından geçer — `shared/bakim.py`). Kapının "ertelenenleri şimdi dene" sinyali de
       kaydolur: kilit açılışı onu verir, kilitliyken ertelenen iş hemen denenir (TK19)
   11. Linux: Qt uygulaması + SIGTERM köprüsü (`desktop/qt_kurulum.py`)
   12. Pencere (pywebview)
   `--autotest` kipinde 1-9 + sağlık denetimi koşar, pencere açılmaz (§13 D5).

Adım sırası bilinçlidir: bütünlük denetimi yedeklemeden ÖNCE koşar; veritabanı
bozukken rotasyonun sağlam eski yedekleri silmesi istenmez.

**Kapanış — tek yol** (§4.2, §4.5 T6). Çarpı programı kapatır, onay sorulmaz.
Öteki kaynaklar: arayüzdeki Çık (`POST app/quit/`), kurucu ve kaldırıcının
`OABDefteri.Kapat` olayı, tek kopya kanalının `kapat` komutu ve Linux oturum
kapanışı (SIGTERM). Sıra: pencere → kanal → Qt köprüsü → kancalar bırakılır →
`od-gunluk` → oturum açıksa kilitlenir (`KILIT` satırı ve çapa `iz-durumu.json`'a, sonra DEK
ve iz anahtarı bellekten düşer) → yönetim sunucusu → WAL checkpoint (TB14) → temiz kapanış
işareti → kilit. Mutex'ler süreç bitene dek kalır (lock.py).

Herhangi bir adım başarısız olursa pencere açılmaz; kullanıcıya Türkçe ileti +
"son yedekten dön" yolu gösterilir ve hataya özel bir çıkış kodu döner (CI ve
paket kurulum testleri bu kodlara bakar). "Son yedekten dön" yolunun kendisi
`--geri-yukle` kipidir (desktop/restore.py): pencere/sunucu açılmadan yedek
seçtirilir ve veritabanının yerine konur.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from desktop import qt_kurulum
from desktop.backup import (
    daily_backup,
    daily_backup_path,
    pre_migrate_backup,
    pre_migrate_backup_path,
    rotate_backups,
)
from desktop.clean_shutdown import (
    consume_marker,
    publish,
    restore_after_failed_startup,
    write_marker_quietly,
)
from desktop.dialogs import show_error
from desktop.django_bootstrap import (
    assert_session_guard_installed,
    build_wsgi_application,
    pending_migrations,
    prepare_django,
    run_migrations,
    unknown_applied_migrations,
    wal_checkpoint,
)
from desktop.errors import (
    EXIT_OK,
    EXIT_UNEXPECTED,
    AlreadyRunningError,
    StartupError,
)
from desktop.gunluk import DAMGA_DOSYASI, GunDegisimiKapisi, acik_kalma_saati
from desktop.instance_channel import COMMAND_QUIT, COMMAND_SHOW, CommandChannel, open_channel
from desktop.integrity import check_database_integrity
from desktop.lock import SingleInstanceLock, signal_running_instance
from desktop.logging_setup import configure_logging, enable_crash_log
from desktop.paths import (
    ENV_APP_HOME,
    AppPaths,
    check_sync_hazard,
    gizli_kipleri_uygula,
    resolve_app_paths,
    resolve_backend_dir,
)
from desktop.restore import run_restore
from desktop.server import BackgroundServer, check_health
from desktop.session_guard import ENV_TOKEN, generate_session_token, window_url
from desktop.version import (
    ensure_no_unknown_migrations,
    ensure_stamp_compatible,
    get_app_version,
    write_version_stamp,
)
from desktop.window import WindowController, open_window, require_window_runtime

logger = logging.getLogger("oab_defteri")

_UNEXPECTED_MESSAGE = "Program açılırken beklenmeyen bir hata oluştu."
_UNEXPECTED_HINT = (
    "Programı yeniden başlatmayı deneyin. Sorun sürerse veri klasöründeki "
    "logs/uygulama.log dosyasını okulun bilişim teknolojileri rehber "
    "öğretmenine (BTR) iletin."
)


def build_parser() -> argparse.ArgumentParser:
    """Komut satırı arayüzü."""
    parser = argparse.ArgumentParser(
        prog="oab-defteri",
        description=(
            "OAB Defteri — okul-aile birliğinin işleri için çevrimdışı masaüstü programı."
        ),
    )
    parser.add_argument(
        "--autotest",
        action="store_true",
        help="Pencere açmadan açılış adımlarını koşar, sağlık denetimi yapıp çıkar.",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Veri klasörünü değiştirir (taşınabilir kip ve testler için).",
    )
    parser.add_argument(
        "--geri-yukle",
        nargs="?",
        const="",
        default=None,
        metavar="YEDEK",
        help=(
            "Programı açmak yerine verilen .odbak yedeğini veritabanının yerine "
            "geri yükler; dosya verilmezse yedek klasöründen seçtirir."
        ),
    )
    parser.add_argument(
        "--hesap",
        default=None,
        metavar="TANITICI",
        help="Geri yükleme: program yöneticisi hesabının tanıtıcısı (ör. yonetici).",
    )
    parser.add_argument(
        "--parola",
        default=None,
        help="Geri yükleme: --hesap ile verilen hesabın parolası (otomasyon içindir; komut "
        "geçmişine düşer).",
    )
    parser.add_argument(
        "--kurtarma-anahtari",
        default=None,
        help="Geri yükleme: kurtarma anahtarı (otomasyon içindir).",
    )
    parser.add_argument(
        "--evet",
        action="store_true",
        help="Geri yükleme onay sorusunu ve kapanış beklemesini atlar.",
    )
    return parser


def resolve_paths(args: argparse.Namespace) -> AppPaths:
    """`--data-dir` verildiyse yerleşimi ona bağlar."""
    if args.data_dir:
        os.environ[ENV_APP_HOME] = str(args.data_dir)
    return resolve_app_paths()


def is_plain_launch(args: argparse.Namespace) -> bool:
    """Bayraksız normal açılış mı? (pencereli kip; §4.2 adım 2)

    `--autotest` ve `--geri-yukle` kiptir: çalışan kopya bulurlarsa 2 koduyla
    çıkarlar, sinyal göndermezler. `--data-dir` kip değil konumdur; aynı veri
    dizinini kullanan kopyaya sinyal gider. (`--pdf-duman` ve
    `--bagimlilik-duman` bu işleve hiç gelmez: `packaging/pyinstaller/giris.py`.)
    """
    return not args.autotest and args.geri_yukle is None


@dataclass
class AcilisOlaylari:
    """Açılışın denetim izine düşecek olguları (tasarım §4.2 adım 7-8, §4.6.3).

    Günlük yedek ve göç öncesi yedek Django ve iz tablosu hazır olmadan alınır; olgular
    burada tamponlanır, göçten sonra `masaustu_kanca` üzerinden yazılır. Yalnız yeni alınan
    yedek sayılır (aynı gün ikinci açılışta var olan yedek "alındı" değildir).
    """

    alinan_yedekler: list[str] = field(default_factory=list)
    silinen_yedekler: list[str] = field(default_factory=list)
    gocler: list[str] = field(default_factory=list)


def prepare_data(paths: AppPaths, app_version: str) -> None:
    """Veriyi açılışa hazırlar: sürüm → bütünlük → yedek → göç sürümü → göç → damga → iz."""
    ensure_stamp_compatible(paths.version_stamp_path, app_version)
    check_database_integrity(paths.db_path, backup_dir=paths.backups)
    olaylar = AcilisOlaylari()

    # Rotasyon yalnız bugünün yedeği elde varken koşar: yedek atlandıysa
    # (parola henüz kurulmadı, yedek anahtarı bozuk, guvenlik.json kayıp) eski
    # yedekler silinmez — kayıp kilidinden çıkış yolu onlardır (tasarım §4.3 tehdit 8).
    bugunku_vardi = daily_backup_path(paths.backups, date.today()).exists()
    gunluk = daily_backup(paths.db_path, paths.backups)
    if gunluk is not None:
        if not bugunku_vardi:
            olaylar.alinan_yedekler.append(gunluk.name)
        olaylar.silinen_yedekler.extend(yol.name for yol in rotate_backups(paths.backups) or [])

    prepare_django(resolve_backend_dir(), paths.data)
    # İkinci hat (§4.2 adım 5): damga yoksa (geri yükleme siler) veritabanının göç kaydı
    # konuşur — tanınmayan göç = daha yeni sürümün şeması; göç ve yazım başlamadan dur.
    ensure_no_unknown_migrations(unknown_applied_migrations(), app_version)
    bekleyen = pending_migrations()
    if bekleyen:
        hedef_vardi = pre_migrate_backup_path(paths.backups, app_version, date.today()).exists()
        goc_oncesi = pre_migrate_backup(paths.db_path, paths.backups, app_version)
        if goc_oncesi is not None and not hedef_vardi:
            olaylar.alinan_yedekler.append(goc_oncesi.name)
    run_migrations()
    olaylar.gocler = list(bekleyen)
    write_version_stamp(paths.version_stamp_path, app_version)
    _acilis_olaylarini_yaz(olaylar, app_version)


def _acilis_olaylarini_yaz(olaylar: AcilisOlaylari, app_version: str) -> None:
    """Açılışın olgularını denetim izine verir (`masaustu_kanca`; §4.6.3 kilitli kip).

    Backend yoksa (masaüstü birim testi) sessiz; hata açılışı DURDURMAZ, günlüğe yazılır.
    İlk hesaptan önce (iz zinciri boş) backend olay yazmaz.
    """
    try:
        from apps.okul import masaustu_kanca
    except ImportError:
        return
    try:
        masaustu_kanca.yedek_olaylarini_yaz(
            alinan=olaylar.alinan_yedekler, silinen=olaylar.silinen_yedekler
        )
        masaustu_kanca.goc_olayini_yaz(surum=app_version, gocler=olaylar.gocler)
    except Exception:
        logger.exception("Açılışın olayları denetim izine yazılamadı; program açılıyor.")


def dispatch_command(command: str, controller: WindowController) -> None:
    """Tek kopya kanalından gelen komut → pencere denetçisi."""
    if command == COMMAND_SHOW:
        controller.show()
    elif command == COMMAND_QUIT:
        controller.request_quit()


#: Arayüzden gelen Çık (`POST app/quit/`) HTTP yanıtı gönderildikten SONRA başlasın.
_CIKIS_GECIKMESI_SN = 0.3


def cikis_kancasi(controller: WindowController) -> Callable[[], None]:
    """`app/quit/` için kanca: kapanışı ayrı iş parçacığında, yanıttan sonra başlatır."""

    def iste() -> None:
        zamanlayici = threading.Timer(_CIKIS_GECIKMESI_SN, controller.request_quit)
        zamanlayici.daemon = True
        zamanlayici.name = "od-cikis"
        zamanlayici.start()

    return iste


def run_window_session(
    url: str,
    storage_path: Path,
    channel: CommandChannel | None,
    *,
    platform: str = sys.platform,
) -> None:
    """Kanal + pencere; pencere kapanana dek bloklar (ANA iş parçacığında).

    Linux'ta Qt uygulaması ana iş parçacığında ve `webview.start`'tan önce
    kurulmak zorundadır (desktop/qt_kurulum.py). Çıkışta kanal ve Qt köprüsü her
    durumda kapatılır. Arayüzdeki Çık (`POST app/quit/`) aynı denetçiye bağlıdır
    (`masaustu_kanca`); pencere süslemesi olmayan Linux masaüstünün çıkış yolu
    odur (TB13).
    """
    controller = WindowController(platform=platform)
    # Linux: Qt uygulaması ve SIGTERM köprüsü pencereden ÖNCE, ana iş parçacığında
    # (§4.2 adım 11, §13 D1).
    qt = qt_kurulum.hazirla(controller.request_quit) if platform.startswith("linux") else None
    _kancalari_kaydet(cikis=cikis_kancasi(controller))
    try:
        if channel is not None:
            channel.start(lambda command: dispatch_command(command, controller))
        open_window(url, storage_path=storage_path, controller=controller)
    finally:
        if channel is not None:
            channel.close()
        if qt is not None:
            qt.durdur()
    logger.info("Pencere kapandı; program düzenli kapanıyor.")


def _kancalari_kaydet(**kancalar: Any) -> None:
    """Masaüstü kancalarını backend'e kaydeder (§4.2 adım 10). Backend yoksa (testte) sessiz."""
    try:
        from apps.okul import masaustu_kanca
    except ImportError:
        return
    masaustu_kanca.kaydet(**kancalar)


def _kancalari_birak() -> None:
    try:
        from apps.okul import masaustu_kanca
    except ImportError:
        return
    masaustu_kanca.kaldir()


def _oturumu_kilitle() -> None:
    """Düzenli kapanışta oturum açıksa kilitler (§4.2: `od-gunluk` durduktan sonra, sunucudan önce).

    Kilidi backend kaydeder (`masaustu_kanca.kapanista_kilitle`; `OkulConfig.ready`):
    uçuştaki isteklerin bitmesini sınırlı süre bekler, `KILIT` satırını ve çapayı
    (`iz-durumu.json`) yazar, sonra DEK ve iz anahtarı bellekten düşer. Backend yoksa (testte)
    sessiz; hata kapanışı DURDURMAZ, günlüğe yazılır.
    """
    try:
        from apps.okul.masaustu_kanca import kapanista_kilitle
    except ImportError:
        return
    try:
        if kapanista_kilitle():
            logger.info("Kapanışta oturum kilitlendi.")
    except Exception:
        logger.exception("Kapanışta oturum kilitlenemedi; program kapanmaya devam ediyor.")


def gun_kapisi_kur(
    paths: AppPaths,
    *,
    bugun: Callable[[], date] = date.today,
) -> GunDegisimiKapisi:
    """`od-gunluk`: yerleşik iş (günlük yedek + rotasyon) + backend'in kaydettiği işler."""
    kapi = GunDegisimiKapisi(damga_yolu=paths.data / DAMGA_DOSYASI, bugun=bugun)
    kapi.kaydet("gunluk-yedek", gunluk_yedek_isi(paths, bugun=bugun))
    kapi.backend_islerini_ekle()
    return kapi


def gunluk_yedek_isi(
    paths: AppPaths,
    *,
    bugun: Callable[[], date] = date.today,
    saat: Callable[[], float] = acik_kalma_saati,
) -> Callable[[], bool]:
    """Günlük yedek + 14 gün rotasyonu; yedek alınmadıysa rotasyon koşmaz (§4.3 tehdit 8).

    Oturum içi rotasyon SAAT SIÇRAMASINA karşı korunur: program günlerce açık
    kalırken sistem saati 14 günden fazla ileri sıçrarsa (NTP ya da elle yanlış
    ayar) `bugün - 14` kesimi geçmiş günlerin bütün yedeklerini silerdi. İşin
    ilk koşusu bir çapa tutar (o günkü tarih + uyku dahil açık kalma saati);
    rotasyon `min(bugün, çapa + gerçekte geçen gün + 1)` tarihiyle yapılır.
    Saat doğruyken iki değer aynıdır (tatilde uykuda kalan bilgisayarda da:
    açık kalma saati uykuyu sayar); saat ileri sıçramışsa kesim gerçek süreye
    göre konur. "En çok 14 gün" saklama sözü (§4.4.7) bozulmaz: hiçbir
    yedek gerçek yaşı 14 günü aştığı hâlde tutulmaz. Açılıştaki rotasyon
    (`prepare_data`) çapasızdır, aile iskeletindeki gibi kalır.
    """
    capa: list[tuple[date, float]] = []

    def calistir() -> bool:
        gun = bugun()
        simdi = saat()
        if not capa:
            capa.append((gun, simdi))
        capa_gunu, capa_saati = capa[0]
        gecen_gun = max(0, int((simdi - capa_saati) // 86_400))
        guvenilir = capa_gunu + timedelta(days=gecen_gun + 1)
        vardi = daily_backup_path(paths.backups, gun).exists()
        yedek = daily_backup(paths.db_path, paths.backups, today=gun)
        if yedek is None:
            return False  # parola kurulmadı / güvenlik dosyası kayıp: bir saat sonra yeniden
        rotasyon_gunu = min(gun, guvenilir)
        if rotasyon_gunu < gun:
            logger.warning(
                "Sistem saati programın açık kaldığı süreden %d gün ileride; eski yedekler "
                "gerçek süreye göre döndürülüyor. Saati denetleyin.",
                (gun - rotasyon_gunu).days,
            )
        silinen = rotate_backups(paths.backups, today=rotasyon_gunu) or []
        _yedek_olaylarini_yaz(
            alinan=[] if vardi else [yedek.name], silinen=[yol.name for yol in silinen]
        )
        return True

    return calistir


def _yedek_olaylarini_yaz(*, alinan: list[str], silinen: list[str]) -> None:
    """`od-gunluk`'un yedek olgularını denetim izine verir (`YEDEK`; kip backend'de seçilir).

    Oturum açıksa satır açık kipte, kilitliyse kilitli kipte `SISTEM` adına düşer
    (`masaustu_kanca.yedek_olaylarini_yaz`). Backend yoksa (testte) sessiz; hata işi
    durdurmaz.
    """
    if not alinan and not silinen:
        return
    try:
        from apps.okul import masaustu_kanca
    except ImportError:
        return
    try:
        masaustu_kanca.yedek_olaylarini_yaz(alinan=alinan, silinen=silinen)
    except Exception:
        logger.exception("Yedek olayı denetim izine yazılamadı.")


def serve(
    paths: AppPaths,
    token: str,
    autotest: bool,
    channel: CommandChannel | None = None,
) -> int:
    """Gömülü sunucuyu başlatır; `--autotest` değilse gün kapısını ve pencereyi açar."""
    application = build_wsgi_application()
    assert_session_guard_installed()

    server = BackgroundServer(application)
    server.start()
    kapi: GunDegisimiKapisi | None = None
    try:
        server.wait_until_ready()
        check_health(server.base_url, token)
        if autotest:
            # Duman testi: açılış zinciri + sağlık denetimi; pencere açılmaz (§13 D5).
            logger.info("Açılış denetimi başarılı.")
            return EXIT_OK
        require_window_runtime()
        kapi = gun_kapisi_kur(paths)
        kapi.baslat()
        # TK19: kilit açılışı ertelenen gün işlerini bu sinyalle hemen denetir (engellemez;
        # iş `od-gunluk`'ta koşar). Kapanışta `_kancalari_birak` kapıdan ÖNCE düşürür.
        _kancalari_kaydet(ertelenenleri_dene=kapi.ertelenenleri_dene)
        run_window_session(
            window_url(server.base_url, token),
            paths.webview_storage_path,
            channel,
        )
        return EXIT_OK
    finally:
        # Kapanış sırası (§4.2): kancalar → od-gunluk → oturum kilidi → sunucu → WAL.
        _kancalari_birak()
        if kapi is not None:
            kapi.durdur()
        _oturumu_kilitle()
        server.stop()
        wal_checkpoint(paths.db_path)


def _run_locked(paths: AppPaths, args: argparse.Namespace, app_version: str) -> int:
    """Kilit alındıktan sonraki akış: işaret → kanal → veri → sunucu/pencere → işaret."""
    previous = consume_marker(paths.data, paths.db_path)
    publish(previous)
    channel = open_channel(paths.root) if is_plain_launch(args) else None
    try:
        # Belirteç, ayarlar okunmadan ÖNCE üretilir: `config/settings.py`
        # middleware'i bu değişkene bakarak ekler.
        token = generate_session_token()
        os.environ[ENV_TOKEN] = token
        try:
            prepare_data(paths, app_version)
            code = serve(paths, token, args.autotest, channel)
        except StartupError:
            # Bu oturumda veriye işlem yazılmadı: önceki oturumun durumu korunur.
            restore_after_failed_startup(previous, paths.data, app_version)
            raise
        if code == EXIT_OK:
            write_marker_quietly(paths.data, app_version)
        return code
    finally:
        if channel is not None:
            channel.close()


def run(argv: Sequence[str] | None = None) -> int:
    """Programı çalıştırır ve süreç çıkış kodunu döndürür."""
    ham = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(ham)
    paths = resolve_paths(args)
    # Linux: umask 077 dizinlerden ve günlükten ÖNCE (tasarım §4.5, §13 D52).
    gizli_kipleri_uygula()
    paths.ensure()
    configure_logging(paths.logs, echo=args.autotest)

    # PyInstaller çalışma-zamanı kancası günlük yapılandırmasından ÖNCE koşar;
    # uyarısını env'e bırakır, buraya kadar taşınmazsa sessizce kaybolurdu.
    rthook_uyarisi = os.environ.pop("OD_RTHOOK_UYARI", "")
    if rthook_uyarisi:
        logger.warning("Paket ortamı uyarısı: %s", rthook_uyarisi)

    app_version = get_app_version()
    logger.info("OAB Defteri %s başlıyor.", app_version)
    # PDF motorunun C katmanındaki bir çöküş süreci anında kapatır ve bu günlüğe
    # hiçbir şey düşmez (aile iskeletinde 19.09.2026); o an Python yığını
    # `logs/cokme.log`a yazılır.
    enable_crash_log(paths.logs, app_version)
    hazard = check_sync_hazard(paths.root)
    if hazard:
        logger.warning("%s", hazard)

    if args.geri_yukle is not None:
        # Geri yükleme kipi: pencere/sunucu açılmaz; bütünlük denetimi ve göç
        # KOŞULMAZ — bozuk veritabanı bu kipin varlık sebebidir. Tek-instance
        # kilidini ve hata gösterimini akış kendi içinde yönetir.
        return run_restore(paths, args)

    lock = SingleInstanceLock(paths.lock_path)
    try:
        try:
            lock.acquire()
        except AlreadyRunningError:
            # §4.2 adım 2: YALNIZ bayraksız açılış çalışan kopyanın penceresini öne
            # getirir; sinyal ulaşmazsa (kanal yok) "zaten çalışıyor" iletisi.
            if is_plain_launch(args) and signal_running_instance(paths.root):
                logger.info("Program zaten çalışıyor; penceresi öne getirildi.")
                return EXIT_OK
            raise
        try:
            return _run_locked(paths, args, app_version)
        finally:
            os.environ.pop(ENV_TOKEN, None)
            lock.release()
    except StartupError as exc:
        logger.error("Açılış durdu: %s", exc.message)
        show_error(exc.title, exc.full_message)
        return exc.exit_code
    except Exception:
        logger.exception("Açılışta beklenmeyen hata.")
        show_error("OAB Defteri açılamadı", f"{_UNEXPECTED_MESSAGE}\n\n{_UNEXPECTED_HINT}")
        return EXIT_UNEXPECTED


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
