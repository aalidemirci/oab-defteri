"""Otomatik şifreli yedekleme — SQLite çevrimiçi görüntü, manifesto ve rotasyon (tasarım §4.4.7).

**Dosya kopyalama YAPILMAZ.** WAL kipinde işlenmiş sayfaların bir bölümü hâlâ
`-wal` dosyasındadır; `db.sqlite3`'ü tek başına kopyalamak tutarsız (hatta bozuk)
bir yedek üretir. `Connection.backup()` ise SQLite'ın kendi çevrimiçi yedek API'sini
kullanır: kaynak veritabanını sayfa sayfa RAM'e okur, WAL dahil tutarlı bir görüntü
çıkarır.

**Yedek YALNIZ şifreli yazılır** (tasarım §4.4.7; ailenin eski "parolasız kipte
düz `.odbak`" dalı aile iskeletinde söküldü, tasarım §13 D29). Görüntü, yedek açık
anahtarıyla (`yedekleme.json`) X25519 + AES-256-GCM kapsayıcısına mühürlenir ve
başlığına o anki `guvenlik.json`'un kurtarma bölümünün izdüşümü (kurtarma başlığı)
gömülür: yalnız `{surum, kdf, kurtarma: {no, tarih, salt, sarmal}}`; hesap
sarmalları yedeğe girmez (tasarım TK10, `backup_crypto.usable_recovery_header`).
Yedek ATLANIR (uyarı loglanır, düz kopya asla yazılmaz):

* `yedekleme.json` yoksa: ilk program yöneticisi hesabı henüz kurulmamıştır (ilk
  açılış). Kişi verisi de yoktur (hesap kurulmadan kişi yazılamaz); ilk yedek hesap
  kurulduktan sonraki açılışta alınır. Bu davranış testle sabitlenir.
* `yedekleme.json` bozuksa: herhangi bir hesapla kilit bir kez açıldığında
  `ensure_public_config` dosyayı onarır.
* Kurtarma başlığı kullanılamıyorsa (`guvenlik.json` kayıp, okunamıyor, boş ya
  da biçimsiz — tasarım §4.3 tehdit 8): böyle bir başlıkla alınan yedek ancak kaybolan dosyayla
  açılabilirdi; üretmek yerine atlanır. "Kullanılabilir" kuralı tektir ve
  `backup_crypto.is_usable_security_state`'tedir (kayıp kilidi ve geri yükleme
  de onu kullanır). Yalnız dosyanın VARLIĞINA bakmak yetmez: içi boşaltılmış
  bir dosyayla başlıksız yedekler birikir, rotasyon da sağlam başlıklı eskileri
  süpürürdü. Açılış akışı (`desktop/main.py`) bugünün yedeği alınmadıkça
  rotasyonu da koşmaz: kayıp kilidinden çıkış yolu olan eski başlıklı yedekler
  silinmez.

Yedek adları tarihlidir ve deterministiktir: aynı gün ikinci kez açılan program o
günün yedeğini yeniden ÜRETMEZ (sabah alınan yedek, akşam bozulan veriyle ezilmez).

**Yerel yedek veritabanı ve manifesto taşır** (tasarım TK22, §4.4.7; plan F1b-3 "Kap ve
manifesto"): ek dosyaları yedeğe girmez, listeleri girer. Manifesto görüntünün kendisinden,
`purged_at`'i boş `Attachment` satırlarının açık sütunlarından (`stored_name`, `size`, `sha256`) ham
SQL ile kurulur (`goruntu_ve_manifesto`): DEK istemez, ORM ve depoyu okumaz; açılıştaki günlük yedek
Django'dan ve göçten önce, kilitliyken alınabilir. Tablo yoksa (göçten önceki veritabanı) manifesto
boştur. Program dışından bozulmuş satır o yedeği düşürmez, listeye girmez (yedeksiz kalmak eksik
ekli yedekten ağırdır). `pre-parola` kurulum yedeğidir, manifestosu boştur.

**Rotasyon** (tasarım §4.4.7 "Rotasyon ve KVKK sınırı"; plan F1b-3 "Rotasyon ve yerel yedekler"):
tek işlev (`rotate_backups`), kapalı önek kümesi tek sabitte (`ROTASYON_KUMESI`). 14 gün: `gunluk`,
`pre-parola`, `pre-anonim`, `pre-kapanis`, `pre-dek-yenileme` ve veri dizinindeki `db-onceki`;
`pre-migrate` son 5. Adı kümedeki desene uymayan dosyaya dokunulmaz. Yaş addaki günden okunur:
`os.replace` dosya zamanını korur, taşıma ve kopyalama değiştirir; dosya zamanı yedeğin anını
söylemez. `pre-kapanis` ve `pre-dek-yenileme`'nin üreticileri F4'tedir; bu adımda yalnız adları ve
kuralları vardır. Bir dosyanın silinememesi rotasyonu düşürmez, adı günlüğe yazılır.

Kenara alınan veritabanının ad kuralı da buradadır (`old_database_stamp`): rotasyon onu tanımak
zorundadır ve masaüstü backend'i içe aktarmaz; geri yükleme (`apps.okul.services.backup_restore`)
buradan alır. `-wal`/`-shm` eşleri veritabanıyla karar görür: veritabanı silinemezse eşleri de
kalır (`remove_old_databases_named`).

**KVKK tetiği araç düzeyindedir** (tasarım §4.4.7 madde 2; bir işleme bağlanması F4'tedir): tetikten
hemen ÖNCE `pre-anonim-<tarih>-<saat>.odbak` alınır (`pre_anonim_backup`; aynı gün ikinci tetik ayrı
dosya alır, sabahki yedeğin yerine geçmez). Silmeden sonra `wal_bosalt` WAL'deki eski sayfaları
kaldırır (TB24), tetik anından eski `pre-migrate` yedekleri silinir (`pre_migrate_before` +
`remove_pre_migrate_named`): onlar silinen veriyi "son 5 güncellemeye kadar" taşırdı. Silinemeyenler
ADIYLA yeniden denenir, dosya zamanıyla değil (saat kayması tetikten sonraki yedeği sildirmesin).
"""

from __future__ import annotations

import logging
import re
import sqlite3
import tempfile
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Final

from desktop.backup_crypto import (
    BACKUP_SUFFIX,
    BOS_YEREL_MANIFESTO,
    KAPSAM_YEREL,
    BackupCryptoError,
    Manifesto,
    ManifestoGirdisi,
    config_path,
    encrypt_to_path,
    load_public_key,
    usable_recovery_header,
)

DAILY_PREFIX = "gunluk"
PRE_MIGRATE_PREFIX = "pre-migrate"
#: Kurulum yedeği (`apps.okul.services.app_password.take_transition_backup`).
PRE_PAROLA_PREFIX = "pre-parola"
#: Onaylı saklama tetiğinden önceki yedek (§4.4.7; rotasyonda 14 gün).
PRE_ANONIM_PREFIX = "pre-anonim"
#: Dönem kapanışından ve DEK yenilemesinden önceki yedekler (§4.4.7); üreticileri F4'tedir.
PRE_KAPANIS_PREFIX = "pre-kapanis"
PRE_DEK_YENILEME_PREFIX = "pre-dek-yenileme"
#: Geri yüklemede kenara alınan veritabanının ad öneki (veri dizininde; §4.4.7).
OLD_DB_PREFIX = "db-onceki"
#: Kenara alınan veritabanının adındaki damga: geri yükleme anının YEREL saati, saniyesiyle.
OLD_DB_STAMP_FORMAT = "%Y-%m-%d-%H%M%S"
#: SQLite'ın yan dosyaları; kenara alınan veritabanının adıyla yanına taşınır.
SQLITE_EKLERI = ("-wal", "-shm")

DEFAULT_KEEP_DAYS = 14
DEFAULT_KEEP_PRE_MIGRATE = 5

#: `Attachment`'ın tablosu (Django'nun varsayılan adı). Masaüstü backend'i içe aktarmaz: eşitliği
#: ve sütunlar `apps/okul/tests/test_yedek_manifestosu.py`'de sabittir.
EK_TABLOSU: Final = "okul_attachment"
_EK_SORGUSU: Final = (
    "SELECT stored_name, size, sha256 FROM okul_attachment "
    "WHERE purged_at IS NULL ORDER BY stored_name"
)

# Dosya adında güvenli olmayan her şey alt çizgiye döner (sürüm etiketi "1.0/rc:1" olabilir).
_UNSAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")

_GUN: Final = r"(?P<gun>\d{4}-\d{2}-\d{2})"
_SAAT: Final = r"\d{6}"
_ODBAK: Final = re.escape(BACKUP_SUFFIX)
#: Programın ürettiği adlar: `db-onceki-<damga>.sqlite3` ve `-wal`/`-shm` eşleri. Bu biçimde
#: olmayan (elle konmuş, yol ayırıcılı) ada dokunulmaz.
_OLD_DB_NAME_RE: Final = re.compile(
    rf"{OLD_DB_PREFIX}-(?P<damga>{_GUN}-{_SAAT})\.sqlite3(?:-wal|-shm)?"
)


@dataclass(frozen=True)
class RotasyonKurali:
    """Kümedeki bir önek: tanınan adı ve saklama biçimi (`ROTASYON_KUMESI`)."""

    onek: str
    #: Programın ürettiği ad; `gun` grubu yedeğin günüdür (yaş buradan okunur; modül başlığı).
    desen: re.Pattern[str]
    #: Gün yerine adetle tutulur (`pre-migrate`).
    adetle: bool = False
    #: Yedek dizininde değil veri dizinindedir (`db-onceki`).
    veri_dizininde: bool = False


#: Rotasyonun KAPALI kümesi (tasarım §2.3.2, §4.4.7; §13 D49): yeni önek buraya, `_PROGRAM_YEDEGI`'ne
#: (`apps.okul.denetim_izi`) ve 15. gün testine birlikte girer; küme testle sabittir.
ROTASYON_KUMESI: Final[tuple[RotasyonKurali, ...]] = (
    RotasyonKurali(DAILY_PREFIX, re.compile(rf"{DAILY_PREFIX}-{_GUN}{_ODBAK}")),
    RotasyonKurali(
        PRE_PAROLA_PREFIX, re.compile(rf"{PRE_PAROLA_PREFIX}-acilis-{_GUN}-{_SAAT}{_ODBAK}")
    ),
    RotasyonKurali(
        PRE_ANONIM_PREFIX, re.compile(rf"{PRE_ANONIM_PREFIX}-{_GUN}-{_SAAT}(?:-\d+)?{_ODBAK}")
    ),
    RotasyonKurali(PRE_KAPANIS_PREFIX, re.compile(rf"{PRE_KAPANIS_PREFIX}-{_GUN}{_ODBAK}")),
    RotasyonKurali(
        PRE_DEK_YENILEME_PREFIX, re.compile(rf"{PRE_DEK_YENILEME_PREFIX}-{_GUN}{_ODBAK}")
    ),
    # Sürüm `_safe_name` alfabesindedir.
    RotasyonKurali(
        PRE_MIGRATE_PREFIX,
        re.compile(rf"{PRE_MIGRATE_PREFIX}-[A-Za-z0-9._-]+-{_GUN}{_ODBAK}"),
        adetle=True,
    ),
    RotasyonKurali(OLD_DB_PREFIX, _OLD_DB_NAME_RE, veri_dizininde=True),
)

#: Programın yazdığı `pre-migrate` adı (sürüm biçimi `denetim_izi._PROGRAM_YEDEGI` ile aynıdır).
#: Rotasyon deseni sürümü geniş alır ve elle adlandırılmış dosyayı da tanır: öyle bir dosyanın adı
#: serbest metindir, günlüğe yazılmaz (R1). Desen daraltılmaz: sürüm biçimi kayarsa program yedeği
#: süresiz kalırdı.
_PROGRAM_GOC_ADI: Final = re.compile(
    rf"{PRE_MIGRATE_PREFIX}-\d{{1,4}}\.\d{{1,4}}\.\d{{1,4}}"
    rf"(?:-(?:alpha|beta|rc|dev)(?:\.\d{{1,4}})?)?-{_GUN}{_ODBAK}"
)

logger = logging.getLogger("oab_defteri.backup")

# CPython `Connection.serialize`i ancak SQLite ≥3.36 (SQLITE_ENABLE_DESERIALIZE)
# ile derlendiyse sunar; Pardus 21/bullseye tabanının libsqlite3'ü 3.34'tür ve
# yöntem HİÇ yoktur — aile iskeletinin paketli `--autotest`i bullseye kabında bununla çöktü
# (eski kod parolasız kipte yedeği atladığı için tuzak hiç tetiklenmemişti).
_HAS_SERIALIZE = hasattr(sqlite3.Connection, "serialize")


def _goruntunun_manifestosu(goruntu: sqlite3.Connection) -> Manifesto:
    """Görüntüdeki canlı eklerin yerel manifestosu (modül başlığı); tablo yoksa boştur.

    Yalnız açık sütunlar okunur. Satır çözme hatası (UTF-8 olmayan metin) da satır düzeyinde
    kalsın diye metin hoşgörüyle okunur: bozuk ad desenden geçemez, girdi kurulamaz, atlanır.
    """
    tablo = goruntu.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (EK_TABLOSU,)
    ).fetchone()
    if tablo is None:
        return BOS_YEREL_MANIFESTO
    goruntu.text_factory = lambda ham: ham.decode("utf-8", "replace")
    girdiler: dict[str, ManifestoGirdisi] = {}
    atlanan = 0
    for ad, boyut, ozet in goruntu.execute(_EK_SORGUSU):
        try:
            girdi = ManifestoGirdisi(ad, boyut, ozet)
        except BackupCryptoError:
            atlanan += 1
            continue
        if girdiler.setdefault(girdi.ad, girdi) is not girdi:
            atlanan += 1
    if atlanan:
        logger.warning(
            "Biçimi bozuk %d ek kaydı yedeğin dosya listesine girmedi; yedek alınıyor.", atlanan
        )
    return Manifesto(KAPSAM_YEREL, tuple(girdiler.values()))


def goruntu_ve_manifesto(source_path: Path) -> tuple[bytes, Manifesto]:
    """WAL dahil tutarlı SQLite görüntüsü ve o görüntünün manifestosu (mümkünse RAM'de).

    `serialize` yoksa görüntü, veri dizini altında 0700 izinli geçici bir dizine
    `Connection.backup()` ile alınır; manifesto dosya silinmeden okunur, baytlar okunur okunmaz
    silinir. Şifreli kipte düz baytların diske bu KISA temasını, Pardus 21 uyumu için bilinçli
    kabul ediyoruz: kalıcı düz kopya yine yazılmaz.
    """
    with closing(sqlite3.connect(source_path)) as source:
        if _HAS_SERIALIZE:
            with closing(sqlite3.connect(":memory:")) as target:
                source.backup(target)
                return bytes(target.serialize()), _goruntunun_manifestosu(target)
        with tempfile.TemporaryDirectory(dir=source_path.parent) as tmp_dir:
            snapshot_path = Path(tmp_dir) / "goruntu.sqlite3"
            with closing(sqlite3.connect(snapshot_path)) as target:
                source.backup(target)
                manifesto = _goruntunun_manifestosu(target)
            return snapshot_path.read_bytes(), manifesto


def database_snapshot(source_path: Path) -> bytes:
    """Yalnız görüntünün baytları (`goruntu_ve_manifesto`); manifesto taşımayan `pre-parola` için."""
    return goruntu_ve_manifesto(source_path)[0]


def _copy_database(source_path: Path, target_path: Path, *, data_dir: Path | None = None) -> bool:
    """Tutarlı SQLite görüntüsünü manifestosuyla ŞİFRELİ yazar; yazıldıysa True döner.

    Düz kopya hiçbir durumda yazılmaz. Yedek anahtarı (`yedekleme.json`) yoksa,
    bozuksa ya da kurtarma başlığı (`guvenlik.json`) kullanılamıyorsa (yok,
    boş, bozuk, bölümleri eksik) yedek atlanır (False; gerekçeler modül başlığında).
    `data_dir` anahtar dosyalarının dizinidir; verilmezse veritabanının dizini
    (masaüstünde ikisi aynıdır; çalışan programın backend'i güvenlik dizinini verir).
    """
    data_dir = data_dir if data_dir is not None else source_path.parent
    if not config_path(data_dir).is_file():
        logger.info("İlk program yöneticisi hesabı henüz kurulmadı; yedek alınmadı.")
        return False
    try:
        public_key = load_public_key(data_dir)
    except BackupCryptoError:
        logger.warning(
            "Şifreli yedekleme anahtarı bozuk; yedek alınamadı (düz kopya yazılmadı). "
            "Herhangi bir hesapla kilidi açmak dosyayı onarır."
        )
        return False
    # Başlık DOĞRULANMIŞ baytlardan gömülür (varlık denetimi + ayrı okuma arasında
    # dosya değişse bile gömülen, denetlenenle aynıdır).
    header = usable_recovery_header(data_dir)
    if header is None:
        logger.warning(
            "Güvenlik dosyası (guvenlik.json) bulunamadı ya da okunamıyor; kurtarma "
            "başlığı olmadan yedek alınmadı. Eski yedekler korunuyor."
        )
        return False
    veritabani, manifesto = goruntu_ve_manifesto(source_path)
    encrypt_to_path(
        veritabani,
        target_path,
        public_key,
        recovery_header=header,
        manifesto=manifesto,
    )
    return True


def _safe_name(value: str) -> str:
    return _UNSAFE_RE.sub("_", value).strip("_") or "bilinmeyen"


def daily_backup_path(backup_dir: Path, day: date) -> Path:
    """Günün yedeğinin yolu (`gunluk-<tarih>.odbak`); açılış "yeni mi alındı"yı buradan sorar."""
    return backup_dir / f"{DAILY_PREFIX}-{day.isoformat()}{BACKUP_SUFFIX}"


def pre_migrate_backup_path(backup_dir: Path, app_version: str, day: date) -> Path:
    """Göç öncesi yedeğin yolu (`pre-migrate-<sürüm>-<tarih>.odbak`)."""
    name = f"{PRE_MIGRATE_PREFIX}-{_safe_name(app_version)}-{day.isoformat()}{BACKUP_SUFFIX}"
    return backup_dir / name


def daily_backup(db_path: Path, backup_dir: Path, *, today: date | None = None) -> Path | None:
    """Günün yedeğini alır. Veritabanı yoksa veya yedek zaten varsa yeniden üretmez."""
    if not db_path.exists():
        return None
    day = today or date.today()
    target = daily_backup_path(backup_dir, day)
    if target.exists():
        return target
    if not _copy_database(db_path, target):
        return None
    logger.info("Günlük yedek alındı: %s", target.name)
    return target


def pre_migrate_backup(
    db_path: Path,
    backup_dir: Path,
    app_version: str,
    *,
    today: date | None = None,
) -> Path | None:
    """Şema güncellemesinden ÖNCE ayrı bir kopya alır (yükseltme geri alınabilsin)."""
    if not db_path.exists():
        return None
    day = today or date.today()
    target = pre_migrate_backup_path(backup_dir, app_version, day)
    if target.exists():
        return target
    if not _copy_database(db_path, target):
        return None
    logger.info("Güncelleme öncesi yedek alındı: %s", target.name)
    return target


def pre_anonim_backup(
    db_path: Path,
    backup_dir: Path,
    *,
    data_dir: Path | None = None,
    now: datetime | None = None,
) -> Path | None:
    """Onaylı saklama tetiğinden ÖNCE şifreli yedek alır (§4.4.7, §5.4); alınamazsa `None`.

    Ad `pre-anonim-<YYYY-MM-DD>-<HHMMSS>.odbak`: tarih rotasyonun okuduğu kısımdır,
    saat aynı gün ikinci tetiğin ayrı yedek almasını sağlar. Aynı saniyede dosya
    varsa üzerine yazılmaz (sonek eklenir). Yedek alınamazsa tetik ÇALIŞMAZ —
    çağıranın kuralıdır (OAB'de saklama tetiği henüz yok; tasarım §5.4).
    """
    if not db_path.exists():
        return None
    an = now or datetime.now()
    backup_dir.mkdir(parents=True, exist_ok=True)
    kok = f"{PRE_ANONIM_PREFIX}-{an:%Y-%m-%d-%H%M%S}"
    target = backup_dir / f"{kok}{BACKUP_SUFFIX}"
    sira = 1
    while target.exists():
        sira += 1
        target = backup_dir / f"{kok}-{sira}{BACKUP_SUFFIX}"
    if not _copy_database(db_path, target, data_dir=data_dir):
        return None
    logger.info("Saklama tetiği öncesi yedek alındı: %s", target.name)
    return target


def pre_migrate_before(backup_dir: Path, moment: datetime) -> list[Path]:
    """`moment`'ten ÖNCE yazılmış güncelleme öncesi yedekler (SİLMEZ; ada göre sıralı).

    Ölçü dosyanın yazılma zamanıdır (ad yalnız günü taşır; aynı gün tetikten SONRA
    alınan güncelleme yedeği kalmalıdır). Yalnız tetik ANINDA sorulur: o an saat ile
    dosya zamanları aynı saatten gelir.
    """
    if not backup_dir.is_dir():
        return []
    sinir = moment.timestamp()
    eskiler: list[Path] = []
    for path in sorted(backup_dir.glob(f"{PRE_MIGRATE_PREFIX}-*{BACKUP_SUFFIX}")):
        try:
            if path.stat().st_mtime < sinir:
                eskiler.append(path)
        except OSError:
            continue
    return eskiler


def wal_bosalt(db_path: Path) -> bool:
    """`PRAGMA wal_checkpoint(TRUNCATE)`: WAL ana dosyaya işlenir, `-wal` sıfırlanır (TB24).

    KVKK silmesinden sonraki adımdır (modül başlığı): silinen verinin eski sayfası WAL'de kalmasın.
    Kapanış da bundan geçer (`django_bootstrap.wal_checkpoint`). Başka bir bağlantı okuyorsa kısmi
    kalır; dosya yoksa ya da SQLite hatasında da `False`. Hata yükseltmez, işi durdurmaz.
    """
    if not db_path.exists():
        return False
    try:
        with closing(sqlite3.connect(db_path, timeout=5)) as baglanti:
            mesgul, _, _ = baglanti.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    except sqlite3.Error:
        logger.warning("WAL boşaltılamadı.", exc_info=True)
        return False
    if mesgul:
        logger.warning("WAL boşaltması kısmi kaldı (veritabanı meşgul).")
        return False
    logger.info("WAL boşaltıldı.")
    return True


def _adlari_sil(dizin: Path, adlar: Iterable[str]) -> tuple[list[Path], list[str]]:
    """ADI verilen dosyaları siler: (silinenler, silinemeyen adlar); hiçbiri ötekini durdurmaz.

    Klasörde olmayan ad silinmiş sayılmaz, beklemede de kalmaz.
    """
    silinen: list[Path] = []
    kalan: list[str] = []
    for ad in adlar:
        yol = dizin / ad
        try:
            yol.unlink()
        except FileNotFoundError:
            continue
        except OSError:
            if ad.startswith(f"{PRE_MIGRATE_PREFIX}-") and not _PROGRAM_GOC_ADI.fullmatch(ad):
                logger.warning("Elle adlandırılmış bir yedek silinemedi.")
            else:
                logger.warning("Yedek silinemedi: %s", ad)
            kalan.append(ad)
            continue
        silinen.append(yol)
    return silinen, kalan


def _pre_migrate_adi_mi(ad: str) -> bool:
    """Yalnız yedek klasöründeki düz bir `pre-migrate-*.odbak` adı (yol ayırıcısı yok)."""
    return (
        bool(ad)
        and Path(ad).name == ad
        and ad.startswith(f"{PRE_MIGRATE_PREFIX}-")
        and ad.endswith(BACKUP_SUFFIX)
    )


def remove_pre_migrate_named(backup_dir: Path, names: list[str]) -> tuple[list[Path], list[str]]:
    """ADI verilen güncelleme öncesi yedekleri siler: (silinenler, silinemeyen adlar).

    Saklama tetiği silinecekleri tetik anında ADIYLA belirler; silinemeyenler yine ADIYLA
    yeniden denenir (adların tutulacağı yer tetikle birlikte F4'te kurulur).
    Yeniden deneme dosya zamanına bakmaz: sistem saati sonradan geri kayarsa tetikten
    SONRA alınmış bir güncelleme yedeği "tetikten eski" görünür ve silinirdi (aile
    iskeletinin düzeltmesi). Klasörde olmayan ad silinmiş sayılmaz ama beklemede de kalmaz;
    `pre-migrate-*.odbak` biçiminde olmayan ada dokunulmaz.
    """
    removed, kalan = _adlari_sil(backup_dir, [ad for ad in names if _pre_migrate_adi_mi(ad)])
    if removed:
        logger.info("Saklama tetiği: %d güncelleme öncesi yedek silindi.", len(removed))
    return removed, kalan


def remove_pre_migrate_before(backup_dir: Path, moment: datetime) -> list[Path]:
    """`moment`'ten ÖNCE yazılmış güncelleme öncesi yedekleri siler; sildiklerini döndürür.

    Onaylı saklama tetiği (§4.4.7, §5.4) o yedekleri siler: onlar
    anonimleştirilen bağları "son 5 güncellemeye kadar" taşırdı. Tetik silinemeyen
    adları da tutmak için iki adımı (`pre_migrate_before` + `remove_pre_migrate_named`)
    ayrı çağırır; bu kısayol ikisini birleştirir.
    """
    removed, _kalan = remove_pre_migrate_named(
        backup_dir, [path.name for path in pre_migrate_before(backup_dir, moment)]
    )
    return removed


def old_database_stamp(name: str) -> datetime | None:
    """`db-onceki-<damga>.sqlite3[-wal|-shm]` adındaki geri yükleme anı (yerel, saf).

    Programın ürettiği biçimde olmayan ad (elle konmuş dosya, yol ayırıcılı ad,
    geçersiz tarih) için None: rotasyon o dosyaya dokunmaz.
    """
    eslesme = _OLD_DB_NAME_RE.fullmatch(name)
    if eslesme is None:
        return None
    try:
        return datetime.strptime(eslesme["damga"], OLD_DB_STAMP_FORMAT)
    except ValueError:
        return None


def is_old_database_file(name: str) -> bool:
    """Ad bir önceki veritabanının KENDİSİ mi (`-wal`/`-shm` eşi değil)? Sayım içindir."""
    return old_database_stamp(name) is not None and name.endswith(".sqlite3")


def _ana_ad(ad: str) -> str:
    for ek in SQLITE_EKLERI:
        if ad.endswith(ek):
            return ad[: -len(ek)]
    return ad


def remove_old_databases_named(data_dir: Path, names: Iterable[str]) -> tuple[list[str], list[str]]:
    """ADI verilen önceki veritabanı dosyalarını siler: (silinen adlar, silinemeyen adlar).

    * Yalnız programın ürettiği biçimdeki ad (`old_database_stamp` tanır); öbür adlara
      dokunulmaz ve beklemede de kalmaz.
    * Önce veritabanının kendisi, sonra `-wal`/`-shm` eşleri. Kendisi silinemezse (ör. bir
      veritabanı aracında açık) eşleri de SİLİNMEZ, bekler: kalan kopyanın işlenmiş
      sayfaları `-wal`'da olabilir, eşini silmek o kopyayı eksik bırakırdı.
    * Klasörde olmayan dosya silinmiş sayılmaz ama beklemede de kalmaz.
    """
    gruplar: dict[str, list[str]] = {}
    for ad in dict.fromkeys(names):
        if old_database_stamp(ad) is not None:
            gruplar.setdefault(_ana_ad(ad), []).append(ad)
    silinen: list[str] = []
    kalan: list[str] = []
    for ana in sorted(gruplar):
        ana_kaldi = False
        for ad in sorted(gruplar[ana], key=lambda a: (a != ana, a)):
            if ana_kaldi:
                kalan.append(ad)
                continue
            try:
                (data_dir / ad).unlink()
            except FileNotFoundError:
                continue
            except OSError:
                logger.warning("Önceki veritabanı dosyası silinemedi: %s", ad)
                kalan.append(ad)
                ana_kaldi = ad == ana
                continue
            silinen.append(ad)
    if silinen:
        logger.info("%d önceki veritabanı dosyası silindi.", len(silinen))
    return silinen, kalan


def _dizin_adlari(dizin: Path) -> list[str]:
    """Dizindeki adlar; dizin yoksa ya da okunamıyorsa boş (öteki dizinin rotasyonu sürer)."""
    try:
        return sorted(yol.name for yol in dizin.iterdir())
    except FileNotFoundError:
        return []
    except OSError:
        logger.warning("Rotasyon için dizin okunamadı: %s", dizin.name)
        return []


def _adin_gunu(desen: re.Pattern[str], ad: str) -> date | None:
    """Adı desene uyuyorsa addaki gün; uymuyorsa ya da gün geçersizse None."""
    eslesme = desen.fullmatch(ad)
    if eslesme is None:
        return None
    try:
        return date.fromisoformat(eslesme["gun"])
    except ValueError:
        return None


def rotate_backups(
    backup_dir: Path,
    data_dir: Path,
    *,
    keep_days: int = DEFAULT_KEEP_DAYS,
    keep_pre_migrate: int = DEFAULT_KEEP_PRE_MIGRATE,
    today: date | None = None,
) -> list[Path]:
    """Eskimiş yerel yedekleri siler; sildiği yedekleri döndürür (kurallar modül başlığında).

    Kümedeki yedekler GÜN (varsayılan 14), güncelleme öncesi yedekler ADET (varsayılan son 5) ile
    sınırlanır: ikincisi haftalar sonra fark edilen bir yükseltme sorununda hâlâ elde olmalıdır.
    `db-onceki` eşleri veritabanının parçasıdır: silinir ama yedek sayılmaz, listede dönmez (denetim
    izine dosya başına bir `YEDEK` satırı gider). Tek dosyanın silinememesi ve dizinin okunamaması
    rotasyonu düşürmez.
    """
    sinir = (today or date.today()) - timedelta(days=keep_days)
    yedek_adlari = _dizin_adlari(backup_dir)
    veri_adlari = _dizin_adlari(data_dir)
    removed: list[Path] = []
    for kural in ROTASYON_KUMESI:
        gunler = [
            (gun, ad)
            for ad in (veri_adlari if kural.veri_dizininde else yedek_adlari)
            if (gun := _adin_gunu(kural.desen, ad)) is not None
        ]
        if kural.adetle:
            # En yeni tarih başta; aynı gün birden fazlaysa ad sırası belirleyicidir.
            eskiler = [ad for _gun, ad in sorted(gunler, reverse=True)[keep_pre_migrate:]]
        else:
            eskiler = [ad for gun, ad in gunler if gun < sinir]
        if kural.veri_dizininde:
            silinen_adlar, _kalan = remove_old_databases_named(data_dir, eskiler)
            removed += [data_dir / ad for ad in silinen_adlar if is_old_database_file(ad)]
        else:
            silinen, _kalan = _adlari_sil(backup_dir, eskiler)
            removed += silinen
    if removed:
        logger.info("Eskimiş %d yedek silindi.", len(removed))
    return removed
