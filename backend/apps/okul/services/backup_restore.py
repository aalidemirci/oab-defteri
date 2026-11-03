"""Yedekten geri yükleme — yalnız şifreli `.odbak` (tasarım §4.3, §4.4.4, §4.4.7).

İlk hesap zorunludur ve bütün yedekler X25519 + AES-256-GCM
kapsayıcısıdır; ailenin eski düz SQLite yedek dalı aile iskeletinde
sökülmüştü, kalıntıları OAB'de de söküldü (tasarım §13 D29). Düz bir SQLite
dosyası "yedek" olarak verilirse açık bir Türkçe hatayla reddedilir:
şifresiz bir kopyayı geri yüklemek, kişi alanları düz metin olan ve parmak
izi taşımayan bir veritabanı getirirdi. Bu çekirdek üç giriş kapısından
çağrılır:

    * son kullanıcı: `oab-defteri --geri-yukle` (desktop/restore.py)
    * çalışan program: Güvenlik sekmesi (`live_restore`, `POST backups/restore/`)
    * destek/geliştirme: `python manage.py restore_backup`

VERİTABANINA HİÇ DOKUNULMAZ: geri yüklemenin varlık sebebi bozuk bir
db.sqlite3'tür; bu modülde ORM importu ve sorgusu yoktur. Django'dan yalnız
ayarlar (`settings.DATA_DIR`, `app_password` yol çözümü üzerinden) ve saat
dilimi kullanılır.

DEK NEREDEN GELİR (tasarım TK10, §4.4.4): şifreli kapsayıcının başlığında
yalnız `guvenlik.json`'un KURTARMA bölümü ve kurtarma anahtarının kimliği (no,
tarih) durur (`backup_crypto.recovery_header_from_state`); hesap sarmalları
yedeğe girmez. Çözerken aday sırası:

    1. Veri dizinindeki GÜNCEL guvenlik.json + bir hesabın tanıtıcısı ve
       parolası (aynı bilgisayar; her hesabın parolası çözer, geri yüklemeyi ise
       yalnız program yöneticisi hesabı yapar — aşağıda "GERİ YÜKLEME
       YETKİSİ"). DEK parola değişiminde DEĞİŞMEDİĞİ için
       güncel parola yedekten önceki veriyi de açar; geri yüklenen satırların
       sarmal özetleri güncel dosyaya göre onarılır ("ÖZET ONARIMI"). Güncel
       dosyanın kurtarma bölümü kurtarma anahtarıyla da denenir.
    2. Yedeğe GÖMÜLÜ başlık + kurtarma anahtarı (yeni bilgisayar, kayıp ya da
       başka kuruluma ait dosya). Yedek "<no> numaralı, <tarih> tarihli kurtarma
       anahtarıyla açılır" diye kendini tarif eder (`BackupInfo.recovery_key_label`).

GERİ YÜKLEME YETKİSİ (tasarım §4.4.4; plan F1b-2): parola yolunda geri yüklemeyi yalnız
program yöneticisi yapar. Denetim bu çekirdektedir, üç giriş kapısı da ondan geçer
(`geri_yukleme_yetkisi`; ORM'siz): yedek parolayla çözüldükten SONRA (yanlış parola rolü
sızdırmaz) ve zincir başı okunmadan, veritabanı kenara alınmadan, `guvenlik.json`,
`yedekleme.json`, sürüm damgası ve not yazılmadan ÖNCE. Hesabın satırı güncel veritabanından
salt okunur okunur; okunamıyorsa yedeğin görüntüsünden. Satır mührünün yanında denetim
izindeki son içerik MAC'li kaydını da tutmalıdır (eski bir kopyadan geri konmuş satır reddedilir;
kullanıcı kararı 03.11.2026 "Girişte reddet"). Ret `GeriYuklemeYetkisiz`'dir: hiçbir
dosya değişmez (salt okunur okuma, program kapalıyken WAL başlıklı dosyanın yanında 0 baytlık
`-wal` ve 32 KiB'lık `-shm` bırakabilir; `geri_yukleme_yetkisi` başlığı, F1b-2 ekleri),
masaüstünde çıkış 9, komutta `CommandError`,
uygulama içinde 400 (`BackupRestoreError` bir `ValueError`'dır; uygulama içinde rol kapısı ve
servis kapısı zaten 403 verir, bu ret ancak oturumdaki program yöneticisinin kaydı tutmazsa
düşer). Ret günlüğe sırsız uyarı olarak yazılır; konsolda denetim izi satırı yazılmaz (ORM
yok). KURTARMA ANAHTARI YOLUNDA ROL DENETİMİ YOKTUR: anahtarın kendisi yetkidir.

Yanlış denemelerin gecikmesi hesapsız ve süreç içidir (plan F1b-1). AES-GCM
kimlik doğrulaması nihai hakemdir: yanlış DEK açık hata verir, sessizce bozuk
çıktı üretilemez.

GÜVENLİK DOSYASI KAYIP KİLİDİNDEN ÇIKIŞ (tasarım §4.3 tehdit 8): güncel `guvenlik.json` yoksa
aday listesinde yalnız gömülü başlık kalır; çözüm onunla (kurtarma anahtarıyla)
başarılırsa `guvenlik.json` YALNIZ KURTARMA BÖLÜMÜYLE yazılır (`_ensure_state_file`):
`hesaplar` boştur, `kurtarma.dogrulandi` doludur (anahtar kullanılarak açıldı).
Program açılınca "kurtarma anahtarıyla aç + program yöneticisi parolası" yolu
yöneticinin sarmalını yeniden kurar (kilit ekranı listesi boştur; hesap kilitliyken
açık kurtarma listesinden seçilir, `GET security/recover/`); iki depo karşılaştırması
öteki hesapları parola yenilemeye çeker (`hesaplar.reconcile_two_stores`).

ÖZET ONARIMI (kullanıcı kararı 03.11.2026 "tazelik kapatılır"; `ozet_onarimi`): hesabın mühürlü
satırı güncel sarmalın özetini taşır. Geri yükleme GÜNCEL `guvenlik.json` ile ESKİ veritabanını
birleştirdiği için (parola yolunda ve güncel dosyanın kullanıldığı kurtarma anahtarı yolunda)
yedekten sonra parolası değişen hesabın geri yüklenen satırı yedek günündeki sarmalın özetini
taşırdı. Onarım, takastan ÖNCE `.tmp` dosyasında, güven çapası olarak geri yüklemeden önceki
(kenara alınacak) veritabanının mührü ve izi tutan satırlarını kullanır. Çapa yalnız geri
yüklenen yedeğin zincir başını içeriyorsa (yedekten türemişse) TAZEDİR; baş satırın varlığı tek
başına soy kanıtı olmadığı için taze çapada da hesabın çapadaki satırının eşleştiği iz satırı geri
yüklenen satırınkinden eski olamaz (sıra kuralı; eskiyse çapa o hesap için kullanılamaz). Taze
çapada dosyadaki sarmal çapayı tutuyorsa özet ona çekilir, tutmuyorsa çapanın özetleri aynen
geçer. Çapada satırı olmayan ya da çapada `KAPALI` olan hesabın özetleri boşaltılır. Çapa
kullanılamıyorsa (okunamıyor, bayat, ya da hesabın çapadaki satırının mührü, izi ya da sırası
tutmuyor) dosyadaki sarmal geri yüklenen satırın özetini tutuyorsa özetler kalır, tutmuyorsa
boşaltılır (K-a; kalan risk `ozet_onarimi` modül başlığında). Mührü ya da izi tutmayan geri
yüklenen satıra dokunulmaz (aklanmaz). Onarılan her satır aynı işlemde `SISTEM` `HESAP` iz
satırını alır (`satir_izi.hesap_satirlarini_izle`): ilk kilit açılışı onu reddetmez; onarım
denetim izinde `SISTEM` `HESAP` satırı olarak kalır (değişen alan adlarıyla; izi okuma ekranı
Denetleme Kurulu modülüyle F4'te gelir). Kurtarma başlığından
yazılacak dosyada (hesaplar boş) onarılacak sarmal yoktur; taze çapanın özetleri yine geçer.
Onarım ya da izi yazılamazsa geri yükleme yarıda kalır, hiçbir dosya değişmez. Onarım parola
yolunun yanında kurtarma anahtarı yollarında da (güncel dosyayla ve yedek başlığından) koşar.

GERİ YÜKLEME NOTU (tasarım §4.4.4; plan F1b-1 alt commit c): başarılı geri yükleme
`geri-yukleme-notu.json`'a yedeğin adını, kenara alınan `db-onceki-*` dosyasının adını ve
sha256'sını, kullanılan yolu (parolası verilen hesap ya da kurtarma anahtarı no'su) ve
kenara alınan veritabanının zincir başını yazar (`geri_yukleme_notu`; zincir başı takastan
önce salt okunur `sqlite3` ile, ORM'siz). Not ilk kilit açılışında `GERI_YUKLEME` satırı
olur (`apps.okul.iz_dogrulama`). Üç giriş kapısı da bu çekirdekten geçtiği için not her
yolda yazılır.

KVKK: çözülen içerik diske YALNIZ hedef veritabanı dosyası olarak yazılır
(aynı dizinde .tmp → atomik yer değiştirme; hata hâlinde .tmp silinir).
Ayrı bir düz kopya bırakılmaz. Mevcut (bozuk) veritabanı da SİLİNMEZ:
`db-onceki-<damga>.sqlite3` adıyla kenara alınır — veri kurtarma denemesi
için tek nüsha oydu.

KENARA ALINAN VERİTABANININ AKIBETİ (aile iskeletinden; OAB'de tasarım §4.4.7):
geri yükleme onu silmez. 14 günden eskileri `-wal`/`-shm` eşleriyle silmenin
araçları buradadır (`old_databases_before` + `remove_old_databases_named`). Aile
iskeletinde bunları saklama tetiği çağırıyordu; o servis OAB'ye alınmadı, bugün
çağıran yoktur. Tasarıma göre `db-onceki-` yerel yedeklerin 14 günlük
rotasyonuna girecektir (tasarım §4.4.7, §12.B `desktop/backup.py`; bugünkü
`rotate_backups` bu öneki kapsamaz). Yaş dosyanın ADINDAKİ damgadan okunur, dosya
zamanından değil: `os.replace` dosya zamanını korur, yani dosya zamanı kenara
alınma anını değil eski veritabanına son yazılan anı söyler (program yaz tatilinde
kapalı kaldıysa haftalar öncesini) — dosya zamanına bakılsa dün yapılan geri
yüklemenin dönüş yolu ertesi tetikte silinirdi. Damga değişmez (taşıma, kopyalama,
virüs tarayıcısı dosya zamanını değiştirebilir) ve `-wal`/`-shm` eşleri aynı damgayı
taşıdığı için bir çift birlikte karar görür.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

from desktop.backup_crypto import (
    MAGIC,
    BackupCryptoError,
    decrypt_bytes,
    embedded_recovery_metadata,
    ensure_public_config,
    is_usable_security_state,
    parse_security_state,
    recovery_key_identity,
)
from desktop.paths import VERSION_STAMP_FILE_NAME
from django.utils import timezone

from apps.okul.services import app_password, geri_yukleme_notu, geri_yukleme_yetkisi, ozet_onarimi

logger = logging.getLogger("oab_defteri.restore")

SQLITE_MAGIC = b"SQLite format 3\x00"
# Kenara alınan eski veritabanının ad öneki (integrity ipucu bu adı anar).
OLD_DB_PREFIX = "db-onceki"
#: Kenara alınan veritabanının adındaki damga: geri yükleme anının YEREL saati,
#: saniyesiyle (`_swap_database_files`). Saklama tetiği dosyanın yaşını bundan okur.
OLD_DB_STAMP_FORMAT = "%Y-%m-%d-%H%M%S"
#: SQLite'ın yan dosyaları; kenara alınan veritabanının adıyla yanına taşınır.
_SQLITE_EKLERI = ("-wal", "-shm")
#: Programın ürettiği adlar: `db-onceki-<damga>.sqlite3` ve `-wal`/`-shm` eşleri. Bu
#: biçimde olmayan (elle konmuş, yol ayırıcılı) ada saklama tetiği dokunmaz.
_OLD_DB_NAME_RE = re.compile(
    rf"^{re.escape(OLD_DB_PREFIX)}-(\d{{4}}-\d{{2}}-\d{{2}}-\d{{6}})\.sqlite3(?:-wal|-shm)?$"
)

_SOURCE_CURRENT = "guncel"
_SOURCE_EMBEDDED = "gomulu"


class BackupRestoreError(ValueError):
    """Kullanıcıya gösterilecek Türkçe geri yükleme hatası."""


class GeriYuklemeYetkisiz(BackupRestoreError):
    """Parola yolunda hesap program yöneticisi olarak doğrulanmadı (tasarım §4.4.4).

    `kod` ret nedenidir (`geri_yukleme_yetkisi.RET_*`; günlüğe ve teste, kullanıcı metnine
    çıkmaz). Masaüstünde çıkış 9, komutta `CommandError`, uygulama içinde 400 (modül başlığı).
    """

    def __init__(self, message: str, *, kod: str) -> None:
        super().__init__(message)
        self.kod = kod


@dataclass(frozen=True)
class BackupInfo:
    """`.odbak` kapsayıcısının gömülü kurtarma başlığı (varsa)."""

    embedded_state: dict[str, Any] | None = None
    embedded_raw: bytes = field(default=b"", repr=False)

    @property
    def recovery_key_label(self) -> str:
        """Yedeği açan kurtarma anahtarının kimliği ("3 numaralı, 01.11.2026 tarihli"); yoksa "".

        Tarih kâğıttaki biçimiyle (gg.aa.yyyy) yazılır; no ya da tarih eksikse eldeki kadarı.
        Kimliği okuyan kural tektir (`backup_crypto.recovery_key_identity`).
        """
        kimlik = recovery_key_identity(self.embedded_state) or {}
        parcalar: list[str] = []
        if kimlik.get("no") is not None:
            parcalar.append(f"{kimlik['no']} numaralı")
        if kimlik.get("tarih") is not None:
            parcalar.append(f"{date.fromisoformat(kimlik['tarih']).strftime('%d.%m.%Y')} tarihli")
        return ", ".join(parcalar)


@dataclass(frozen=True)
class RestoreResult:
    db_path: Path
    # Kenara alınan önceki veritabanı (hedef yoksa None).
    old_db_path: Path | None
    # guvenlik.json gömülü başlıktan (yeniden) yazıldı mı?
    state_written: bool


def inspect_backup(container: bytes) -> BackupInfo:
    """Dosyanın şifreli yedek kapsayıcısı olduğunu doğrular, gömülü başlığı çıkarır."""
    if container.startswith(MAGIC):
        try:
            ham = embedded_recovery_metadata(container)
        except BackupCryptoError as exc:
            raise BackupRestoreError(str(exc)) from exc
        return BackupInfo(embedded_state=_parse_state(ham), embedded_raw=ham)
    # Kullanıcı metni: dosya uzantısı ve kapsayıcı gibi teknik adlar geçmez
    # (docs/sozluk.md "Yedek" satırı — teknik adlar yalnız Hakkında sayfasında).
    if container.startswith(SQLITE_MAGIC):
        raise BackupRestoreError(
            "Bu dosya şifrelenmemiş bir veritabanı kopyası. OAB Defteri yalnız "
            "kendi şifreli yedeklerini geri yükler."
        )
    raise BackupRestoreError(
        "Dosya geçerli bir OAB Defteri yedeği değil (şifreli yedek dosyası bekleniyordu)."
    )


def restore_database(
    backup_path: Path,
    db_path: Path,
    *,
    hesap: str | None = None,
    password: str | None = None,
    recovery_key: str | None = None,
    oturum_hesabi: str | None = None,
) -> RestoreResult:
    """Yedeği hedef veritabanının yerine koyar; eski dosyayı KENARA ALIR (silmez).

    Sır ikisinden biridir: `hesap` (tanıtıcı ya da kimlik) + `password` — güncel
    `guvenlik.json`'daki o hesabın sarmalı denenir — YA DA `recovery_key`.
    `oturum_hesabi`: uygulama içi geri yüklemede oturumdaki hesabın kimliği (kurtarma
    anahtarı yolunda da); geri yükleme notuna ve `GERI_YUKLEME` satırına geçer: geri yükleme
    onu başlatan oturumun hesabına bağlanır. Konsol yolunda oturum yoktur (None).

    Parola yolunda hesap, parola doğrulandıktan sonra ve hiçbir dosyaya dokunulmadan önce
    program yöneticisi olarak doğrulanır; değilse `GeriYuklemeYetkisiz` (modül başlığı
    "GERİ YÜKLEME YETKİSİ"). Kurtarma anahtarı yolunda rol denetimi yoktur.
    """
    hesap_adi = (hesap or "").strip() or None
    parola = password or None
    anahtar = recovery_key or None
    try:
        container = backup_path.read_bytes()
    except OSError as exc:
        raise BackupRestoreError(f"Yedek dosyası okunamadı: {backup_path}") from exc

    info = inspect_backup(container)
    if not parola and not anahtar:
        raise BackupRestoreError(
            "Bu yedek şifreli; açmak için program yöneticisi hesabının tanıtıcısı ve parolası "
            "ya da kurtarma anahtarı gerekli."
        )
    if parola and not hesap_adi:
        raise BackupRestoreError(
            "Parolayla açmak için program yöneticisi hesabının tanıtıcısını da verin; ya da "
            "kurtarma anahtarını kullanın."
        )
    icerik, kaynak, dek, acan_durum = _decrypt_container(
        container, info, hesap=hesap_adi, password=parola, recovery_key=anahtar
    )
    if not icerik.startswith(SQLITE_MAGIC):
        raise BackupRestoreError(
            "Yedek çözüldü ama içeriği SQLite veritabanı çıkmadı; dosya bozulmuş olabilir."
        )
    if parola:
        # Geri yükleme yetkisi (modül başlığı): parola doğrulandı, hiçbir dosya değişmedi.
        _yetkiyi_denetle(db_path, icerik, dek, acan_durum, hesap_adi or "")

    # Kenara alınacak veritabanının zincir başı ve çapa takastan ÖNCE, salt okunur (geri
    # yükleme notu).
    onceki_bas = geri_yukleme_notu.zincir_basi_oku(db_path)
    onceki_capa = _capa_durumu()
    # Özet onarımı (modül başlığı): `.tmp`'de, takastan ÖNCE; çapa henüz yerinde duran veritabanı.
    sarmal_ozetleri = _sarmal_ozetleri(acan_durum, dek) if kaynak == _SOURCE_CURRENT else {}

    def _onar(gecici: Path) -> None:
        ozet_onarimi.ozetleri_onar(
            onceki_db=db_path, yeni_db=gecici, dek=dek, sarmal_ozetleri=sarmal_ozetleri
        )

    eski = _swap_database_files(db_path, icerik, hazirla=_onar)
    yazildi = _ensure_state_file(info, kaynak)
    # KARDEŞ DOSYA da eşitlenir (birleşme incelemesi bulgusu): yedekleme.json
    # bayat kalırsa (a) `_adopt_key` her kilit açılışında "anahtar eşleşmiyor"
    # hatası verir; (b) daha kötüsü, açılıştaki günlük yedek İÇERİĞİ eski açık
    # anahtarla mühürleyip başlığına yeni guvenlik.json'ı gömer — o yedek
    # hiçbir adayla açılamaz ve rotasyon sağlam eskileri süpürür. replace=True
    # güvenli: DEK az önce AES-GCM doğrulamasıyla bu veriye ait olduğunu kanıtladı.
    ensure_public_config(app_password.state_path().parent, dek, replace=True)
    # Sürüm damgası artık geri yüklenen veriyi tarif etmiyor (yedeğin hangi
    # sürümle yazıldığı bilinmez). Eksik damga açılışa engel DEĞİLDİR
    # (desktop/version.py); ilk başarılı migrate damgayı yeniden yazar.
    (db_path.parent / VERSION_STAMP_FILE_NAME).unlink(missing_ok=True)
    _notu_yaz(
        backup_path,
        eski,
        onceki_bas,
        _yol_bilgisi(acan_durum, hesap=hesap_adi if parola else None),
        oturum_hesabi=oturum_hesabi,
        onceki_capa=onceki_capa,
    )
    logger.info("Yedekten geri yükleme tamamlandı: %s.", backup_path.name)
    return RestoreResult(
        db_path=db_path,
        old_db_path=eski,
        state_written=yazildi,
    )


# ---------------------------------------------------------------------------
# Kenara alınan veritabanının akıbeti (14 günlük rotasyon — tasarım §4.4.7)
# ---------------------------------------------------------------------------
def old_database_stamp(name: str) -> datetime | None:
    """`db-onceki-<damga>.sqlite3[-wal|-shm]` adındaki geri yükleme anı (yerel, saf).

    Programın ürettiği biçimde olmayan ad (elle konmuş dosya, yol ayırıcılı ad,
    geçersiz tarih) için None: saklama tetiği o dosyaya dokunmaz.
    """
    eslesme = _OLD_DB_NAME_RE.match(name)
    if eslesme is None:
        return None
    try:
        return datetime.strptime(eslesme.group(1), OLD_DB_STAMP_FORMAT)
    except ValueError:
        return None


def is_old_database_file(name: str) -> bool:
    """Ad bir önceki veritabanının KENDİSİ mi (`-wal`/`-shm` eşi değil)? Sayım içindir."""
    return old_database_stamp(name) is not None and name.endswith(".sqlite3")


def old_databases_before(data_dir: Path, cutoff: datetime) -> list[str]:
    """Adındaki damga `cutoff`'tan ÖNCE olan önceki veritabanı dosyalarının ADLARI (SİLMEZ).

    Eşler (`-wal`/`-shm`) aynı damgayı taşıdığı için veritabanıyla birlikte listelenir.
    `cutoff` saat dilimli ise yerel saate çevrilir (damga yerel saattir). Yalnız saklama
    tetiği ANINDA sorulur; silinemeyenler sonra yalnız ADLARIYLA yeniden denenir
    (`remove_old_databases_named`). Ölçünün neden dosya zamanı değil ad olduğu modül
    başlığındadır.
    """
    sinir = timezone.localtime(cutoff).replace(tzinfo=None) if timezone.is_aware(cutoff) else cutoff
    try:
        yollar = sorted(data_dir.glob(f"{OLD_DB_PREFIX}-*")) if data_dir.is_dir() else []
    except OSError:
        return []
    adlar: list[str] = []
    for yol in yollar:
        damga = old_database_stamp(yol.name)
        if damga is not None and damga < sinir and yol.is_file():
            adlar.append(yol.name)
    return adlar


def _ana_ad(ad: str) -> str:
    for ek in _SQLITE_EKLERI:
        if ad.endswith(ek):
            return ad[: -len(ek)]
    return ad


def remove_old_databases_named(data_dir: Path, names: Iterable[str]) -> tuple[list[str], list[str]]:
    """ADI verilen önceki veritabanı dosyalarını siler: (silinen adlar, silinemeyen adlar).

    * Yalnız programın ürettiği biçimdeki ad (`old_database_stamp` tanır); öbür adlara
      dokunulmaz ve beklemede de kalmaz. Dosya zamanına BAKILMAZ: hangi dosyaların
      silineceğini çağıran tetik anında belirler; sistem saati sonradan kaysa da
      yeniden deneme yalnız bu adları siler (aile iskeletinin düzeltme ilkesi).
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
        logger.info("Saklama tetiği: %d önceki veritabanı dosyası silindi.", len(silinen))
    return silinen, kalan


# ---------------------------------------------------------------------------
# İç yardımcılar
# ---------------------------------------------------------------------------
def _parse_state(raw: bytes) -> dict[str, Any] | None:
    """Gömülü başlığı ayrıştırır; kullanılamazsa None (aday listesinden düşer, hata değil).

    Kural tektir (`backup_crypto.is_usable_security_state`): günlük yedek aynı
    kuralla başlık gömer, kayıp kilidi aynı kuralla dosyayı "kayıp" sayar.
    """
    if not raw:
        return None
    return cast("dict[str, Any] | None", parse_security_state(raw))


def _candidate_states(info: BackupInfo) -> list[tuple[str, dict[str, Any]]]:
    """Denenecek durum dosyaları: önce güncel guvenlik.json, sonra gömülü başlık."""
    adaylar: list[tuple[str, dict[str, Any]]] = []
    try:
        guncel = app_password.read_state()
    except app_password.AppPasswordError:
        guncel = None  # bozuk güncel dosya gömülü başlıkla çözümü engellemesin
    if guncel is not None and not is_usable_security_state(guncel):
        guncel = None  # bölümleri eksik dosya aday değildir (kayıp kilidiyle aynı kural)
    if guncel is not None:
        adaylar.append((_SOURCE_CURRENT, guncel))
    if info.embedded_state is not None and info.embedded_state != guncel:
        adaylar.append((_SOURCE_EMBEDDED, info.embedded_state))
    return adaylar


def _decrypt_container(
    container: bytes,
    info: BackupInfo,
    *,
    hesap: str | None,
    password: str | None,
    recovery_key: str | None,
) -> tuple[bytes, str, bytes, dict[str, Any]]:
    """Kapsayıcıyı çözer; (düz içerik, DEK kaynağı, DEK, açan durum dosyası) döndürür.

    Parola yolu yalnız güncel `guvenlik.json`'un hesap sarmallarıyla işler (yedek
    başlığında hesap yoktur, TK10); kurtarma anahtarı iki adayda da denenir. Açan durum
    geri yükleme notunun "kullanılan yol"udur (hangi hesap, hangi kurtarma anahtarı).
    """
    adaylar = _candidate_states(info)
    if not adaylar:
        raise BackupRestoreError(
            "Yedeğin kurtarma başlığı yok ve veri klasöründe guvenlik.json bulunamadı. "
            "Kurtarma başlığı taşıyan başka bir yedek seçin ya da yedeğin alındığı "
            "dönemin guvenlik.json (veya guvenlik-arsiv-*.json) dosyasını veri klasörüne "
            "koyup yeniden deneyin."
        )
    for kaynak, durum in adaylar:
        try:
            if password:
                dek = app_password._unwrap_with_account(durum, hesap or "", password)
            else:
                dek = app_password._unwrap_with_recovery(durum, recovery_key or "")
        except app_password.AppPasswordError:
            continue  # bu durum dosyası bu sırla açılmadı; diğer adaya geç
        try:
            return decrypt_bytes(container, dek), kaynak, dek, durum
        except BackupCryptoError:
            continue  # sarmal açıldı ama DEK bu yedeğe ait değil (başka kurulum)
    ileti = (
        "Yedek açılamadı: tanıtıcı, parola ya da kurtarma anahtarı hatalı veya yedek bu "
        "kuruluma ait değil. Başka bilgisayarda alınmış yedek yalnız kurtarma anahtarıyla "
        "açılır."
    )
    kimlik = info.recovery_key_label
    if kimlik:
        ileti += f" Bu yedek {kimlik} kurtarma anahtarıyla açılır."
    raise BackupRestoreError(ileti)


def _yetkiyi_denetle(
    db_path: Path, icerik: bytes, dek: bytes, durum: dict[str, Any], hesap: str
) -> None:
    """Parolası doğrulanan hesap program yöneticisi mi? Değilse `GeriYuklemeYetkisiz`.

    Hesap, yedeği açan güncel `guvenlik.json`'un sarmalından bulunur (tanıtıcı ya da kimlikle
    verilmiş olabilir); sarmal kendi kimliğine bağlı açıldığı için (`app_password` modül başlığı
    "HESAP SARMALI KİMLİĞE BAĞLIDIR") bu kimlik parolası doğrulanan hesabın kendisidir. Sarmalın
    hatalı deneme askısı ve özetinin satırınkini tutması da kabul koşuludur ("SARMALIN
    TAZELİĞİ": eski ya da program dışından konmuş sarmal parolayla geri yükleyemez). Ret günlüğe sırsız
    uyarı olarak düşer: neden kodu ve kararı veren kaynak, hesabın kimliği (tanıtıcı kişinin
    adını içerebilir, yazılmaz).
    """
    sarmal = app_password._find_wrap_by_login_name(durum, hesap) or {}
    try:
        kaynak = geri_yukleme_yetkisi.yonetici_dogrula(
            db_path=db_path,
            goruntu=icerik,
            dek=dek,
            hesap_id=sarmal.get("id"),
            askida=bool(sarmal.get("askida")),
            sarmal_ozeti=app_password.wrap_digest(dek, sarmal) if sarmal else None,
        )
    except geri_yukleme_yetkisi.YetkiReddi as ret:
        logger.warning(
            "Geri yükleme reddedildi: parolası verilen hesap (%s) program yöneticisi olarak "
            "doğrulanmadı (neden: %s; denetlenen: %s); geri yükleme yapılmadı.",
            sarmal.get("id"),
            ret.kod,
            ret.kaynak,
        )
        raise GeriYuklemeYetkisiz(ret.ileti, kod=ret.kod) from ret
    if kaynak == geri_yukleme_yetkisi.KAYNAK_GORUNTU:
        logger.info(
            "Güncel veritabanı okunamadı; program yöneticisi yedeğin görüntüsünde doğrulandı."
        )


def _sarmal_ozetleri(durum: dict[str, Any], dek: bytes) -> dict[str, str | None]:
    """Durum dosyasındaki her hesabın İLK sarmalının özeti, kanonik kimlikle (özet onarımı)."""
    ozetler: dict[str, str | None] = {}
    for bolum in app_password._accounts_in(durum):
        kimlik = str(bolum.get("id", ""))
        if kimlik not in ozetler:
            ozetler[kimlik] = app_password.wrap_digest(dek, bolum)
    return ozetler


def _swap_database_files(
    db_path: Path, content: bytes, *, hazirla: Callable[[Path], None] | None = None
) -> Path | None:
    """Yeni içeriği atomik yerleştirir; eskiyi ve WAL/SHM kalıntılarını kenara alır.

    Sıra bilinçli: önce .tmp TAM yazılır (hata hâlinde hedefe dokunulmamış olur), varsa
    `hazirla` .tmp üzerinde koşar (özet onarımı; eski dosya o an hâlâ yerindedir ve çapadır),
    sonra eski dosya kenara alınır, en son .tmp yerine konur. Eski veritabanının
    `-wal`/`-shm` dosyaları YENİ dosyaya uygulanmamalıdır — silinmez, kenara
    alınan dosyanın adıyla yanına taşınır (SQLite eşleşmeyi dosya adından yapar;
    veri kurtarma denemesinde birlikte açılabilirler).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temp = db_path.with_name(db_path.name + ".yeni.tmp")
    temp.unlink(missing_ok=True)
    try:
        temp.write_bytes(content)
        if hazirla is not None:
            hazirla(temp)
        eski_hedef: Path | None = None
        if db_path.exists():
            damga = timezone.localtime().strftime(OLD_DB_STAMP_FORMAT)
            eski_hedef = db_path.with_name(f"{OLD_DB_PREFIX}-{damga}.sqlite3")
            db_path.replace(eski_hedef)
            for ek in _SQLITE_EKLERI:
                kalinti = db_path.with_name(db_path.name + ek)
                if kalinti.exists():
                    kalinti.replace(eski_hedef.with_name(eski_hedef.name + ek))
            logger.info("Önceki veritabanı kenara alındı: %s", eski_hedef.name)
        else:
            # Hedef yokken kalan başıboş WAL/SHM yeni dosyayı zehirlemesin.
            for ek in _SQLITE_EKLERI:
                db_path.with_name(db_path.name + ek).unlink(missing_ok=True)
        temp.replace(db_path)
        return eski_hedef
    except OSError as exc:
        raise BackupRestoreError(
            f"Geri yükleme yazılamadı ({exc.__class__.__name__}); diskte yer olduğundan "
            "ve dosyanın başka bir programda açık olmadığından emin olun."
        ) from exc
    finally:
        temp.unlink(missing_ok=True)
        for ek in _SQLITE_EKLERI:
            temp.with_name(temp.name + ek).unlink(missing_ok=True)


def _yol_bilgisi(durum: dict[str, Any], *, hesap: str | None) -> dict[str, Any]:
    """Geri yükleme notunun "kullanılan yol"u: parolası verilen hesap ya da kurtarma anahtarı no'su.

    Parola yolunda hesap güncel dosyanın sarmalından bulunur (tanıtıcı ya da kimlikle
    verilmiş olabilir); notta kimlik ve tanıtıcı durur, iz satırına yalnız kimlik geçer.
    """
    if hesap is not None:
        sarmal = app_password._find_wrap_by_login_name(durum, hesap) or {}
        return {
            "tur": geri_yukleme_notu.YOL_HESAP,
            "hesap": str(sarmal.get("id", "")) or None,
            "tanitici": str(sarmal.get("tanitici", "")) or None,
        }
    kimlik = recovery_key_identity(durum) or {}
    return {"tur": geri_yukleme_notu.YOL_KURTARMA, "no": kimlik.get("no")}


def _notu_yaz(
    backup_path: Path,
    eski: Path | None,
    onceki_bas: dict[str, Any] | None,
    yol_bilgisi: dict[str, Any],
    *,
    oturum_hesabi: str | None = None,
    onceki_capa: dict[str, Any] | str | None = geri_yukleme_notu.CAPA_BILINMIYOR,
) -> None:
    """Geri yükleme notunu yazar (tasarım §4.4.4; `geri_yukleme_notu`). Hata yükseltmez.

    Takas yapılmıştır: not yazılamazsa geri yükleme yine başarılıdır. O durumda ilk kilit
    açılışı çapayı tutmayan zincir görür ve "kuyruk kesilmiş ya da veritabanı geri sarılmış"
    uyarısını verir (fail-safe: olay yine görünür, yalnız adı farklıdır).
    """
    try:
        kayit = geri_yukleme_notu.geri_yukleme_kaydi(
            yedek=backup_path.name,
            onceki_dosya=eski.name if eski is not None else None,
            onceki_sha256=geri_yukleme_notu.dosya_ozeti(eski) if eski is not None else None,
            onceki_zincir_basi=onceki_bas,
            yol_bilgisi=yol_bilgisi,
            oturum_hesabi=oturum_hesabi,
            onceki_capa=onceki_capa,
        )
        geri_yukleme_notu.geri_yukleme_ekle(app_password.state_path().parent, kayit)
    except OSError:
        logger.warning("Geri yükleme notu yazılamadı; ilk kilit açılışı çapa uyarısı verecek.")
    else:
        logger.info("Geri yükleme notu yazıldı; ilk kilit açılışında denetim izine işlenir.")


def _capa_durumu() -> dict[str, Any] | str | None:
    """Takastan önceki çapa `{seq, mac}` (geri yükleme notu); dosya yoksa None, okunamıyorsa
    `CAPA_BILINMIYOR`. Mühür ve tohum nota girmez. Hata yükseltmez."""
    # Geç içe aktarım: kilitli kip modülü güvenlik çekirdeğini ve ORM'yi içe aktarır.
    from apps.okul import iz_durumu

    try:
        durum = iz_durumu.oku()
    except iz_durumu.IzDurumuYok:
        return None
    except Exception:  # noqa: BLE001 — okunamayan çapa "bilinmiyor"dur, geri yüklemeyi durdurmaz
        return geri_yukleme_notu.CAPA_BILINMIYOR
    return {"seq": durum.capa_seq, "mac": durum.capa_mac}


def _creation_stamp(kurtarma: dict[str, Any]) -> str:
    """Kurtarmayla yazılan durumun `olusturma` damgası: kurtarma anahtarının üretim günü.

    Damga dış yedek hatırlatmasının ilk günüdür (`dis_yedek`; plan F1b-1 "şema 2":
    `olusturma` korunur). Yedek başlığı `olusturma` taşımaz (TK10), ama kurtarma
    bölümünün `tarih`'ini taşır: o gün hesap kurulduğu ya da anahtar yenilendiği
    gündür, yani eski bir tarihtir. Yeni bilgisayara taşınan kurulumda kart bu yüzden
    eskisi gibi hemen çıkar: yeni diskte henüz dış kopya yoktur (`dis_yedek` modül
    başlığı). Tarih yoksa ya da biçimsizse geri yükleme anı yazılır.
    """
    tarih = kurtarma.get("tarih")
    if isinstance(tarih, str) and tarih:
        try:
            gun = date.fromisoformat(tarih)
        except ValueError:
            pass
        else:
            an = timezone.make_aware(datetime.combine(gun, datetime.min.time()))
            return timezone.localtime(an).isoformat(timespec="seconds")
    return timezone.localtime().isoformat(timespec="seconds")


def _state_from_header(header: dict[str, Any]) -> dict[str, Any]:
    """Yedek başlığından yalnız kurtarma bölümlü şema 2 durumu (TK10; plan F1b-1).

    `hesaplar` boştur (başlık hesap taşımaz); `kurtarma.dogrulandi` doludur, çünkü
    yedek kurtarma anahtarı KULLANILARAK açıldı. `olusturma` kurtarma anahtarının
    üretim günüdür (`_creation_stamp`).
    """
    kurtarma = dict(header.get("kurtarma") or {})
    kurtarma[app_password.RECOVERY_CONFIRMED_FIELD] = timezone.localtime().isoformat(
        timespec="seconds"
    )
    return {
        "surum": app_password.STATE_VERSION,
        "olusturma": _creation_stamp(kurtarma),
        "kdf": header.get("kdf", {}),
        "hesaplar": [],
        "kurtarma": kurtarma,
        "gecis": None,
    }


def _ensure_state_file(info: BackupInfo, kaynak: str) -> bool:
    """Geri yüklenen veritabanı ile guvenlik.json'ın tutarlı kalmasını sağlar.

    Çözüm GÜNCEL dosyayla başarıldıysa o dosya doğru DEK'i sarmalıyor demektir
    (parola değiştiyse en yeni sarmalı taşıyan da odur) → DOKUNULMAZ. Çözüm
    GÖMÜLÜ başlıkla (kurtarma anahtarıyla) başarıldıysa güncel dosya ya yok ya da
    bu veriye ait değil: varsa arşivlenir (silinmez: eski yedekleri açan tek sarmal
    olabilir), yerine YALNIZ kurtarma bölümlü durum yazılır (`_state_from_header`).
    Böylece geri yüklemeden çıkan (veritabanı, durum dosyası) çifti DAİMA aynı DEK'i
    anlatır; kilit açılışı kurtarma anahtarıyla program yöneticisinin sarmalını kurar.

    Yazım güvenlik dosyasının süreç içi kilidi altındadır (`app_password._state_lock`):
    çalışan programdaki geri yükleme, kilit açılışındaki sarmal ve `.tmp` artığı
    temizliğiyle çakışmasın. Arşive taşınan dosyanın, sonradan kapanan hesaplara ait
    sarmallarını o temizlik siler (adaylar arşivlerden de toplanır; TK11).
    """
    if kaynak != _SOURCE_EMBEDDED or info.embedded_state is None:
        return False
    hedef = app_password.state_path()
    with app_password._state_lock:
        if hedef.is_file():
            # Aynı saniyedeki ikinci arşiv öncekini ezmesin (`app_password._archive_target`).
            arsiv = app_password._archive_target()
            hedef.replace(arsiv)
            logger.info("Geri yüklenen veriyle eşleşmeyen guvenlik.json arşivlendi: %s", arsiv.name)
        hedef.parent.mkdir(parents=True, exist_ok=True)
        temp = hedef.with_name(hedef.name + ".tmp")
        temp.write_text(
            json.dumps(_state_from_header(info.embedded_state), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(hedef)
    logger.info("guvenlik.json yedekteki kurtarma başlığından (yalnız kurtarma bölümü) yazıldı.")
    return True
