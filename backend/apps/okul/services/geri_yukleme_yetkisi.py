"""Geri yükleme yetkisi — parola yolunun ORM'SİZ hesap denetimi (tasarım §4.4.4, §4.6.1; plan F1b-2).

Yedekten geri yükleme yalnız KURTARMA ANAHTARIYLA ya da rolü program yöneticisi olan hesabın
PAROLASIYLA yapılır (tasarım §4.4.4 "Geri yükleme yetkisi", denetim GA-3, tehdit 21). Uygulama
içi yol ayrıca rol kapısından (`RolMiddleware`) ve servis kapısından (`live_restore`) geçer;
konsol yolu (`oab-defteri --geri-yukle`, Başlat menüsündeki "Yedekten Geri Yükle" kısayolu,
`manage.py restore_backup`) Django ara katmanından geçmez. Bu yüzden denetim üç kapının ortak
çekirdeğindedir: `backup_restore.restore_database` bu modülü YALNIZ PAROLA YOLUNDA, yedek
parolayla çözüldükten (DEK ve görüntü elde edildikten) SONRA ve hiçbir dosyaya dokunmadan
ÖNCE çağırır. Yanlış parola rolü sızdırmaz: denetime ancak doğru parola ulaşır. KURTARMA
ANAHTARI YOLUNDA ROL DENETİMİ YOKTUR: anahtarın kendisi yetkidir, zarfı okul müdürlüğündedir.

ORM YOK. Geri yüklemenin varlık sebebi bozuk bir veritabanıdır ve ailenin "geri yükleme
veritabanına yazmaz" kuralı korunur. Modül yalnız standart kitaplığın `sqlite3`'üne,
`shared.kanonik`'e (hesap mührünün tek biçimi), `shared.crypto`'nun saf işlevlerine (alt
anahtar, parmak izi) ve `shared.sqlite_adres`'e (salt okunur adres) dayanır; Django ayarı,
uygulama kaydı ve sorgusu gerekmez.
Satır güncel veritabanından `mode=ro` URI'siyle okunur; adres `shared.sqlite_adres`'tendir
(`geri_yukleme_notu.zincir_basi_oku` ile ortak): yol `resolve()` edilmez, UNC yol authority'siz
yazılır — yoksa ağdaki ya da eşlenmiş sürücüdeki veri dizininde adres açılmaz ve okunabilen
veritabanı sessizce "okunamıyor" sayılırdı. `immutable` KULLANILMAZ: henüz WAL'dan ana dosyaya
aktarılmamış son yazım (ör. az önce kapatılan hesap) görünmelidir; `immutable` bayat satırı
"açık" gösterirdi. Bedeli (F1b-2 ekleri; planın "hiçbir dosya değişmez"inin niteliği): program
kapalıyken (WAL başlıklı dosyanın yanında `-wal` ve `-shm` yokken) okuma, ret ve kabul
yolunda, Windows'ta da Linux'ta da 0 baytlık bir `-wal` ve 32 KiB'lık bir `-shm` bırakır;
veritabanının baytları, önceden var olan `-wal`'ın baytları ve öteki dosyalar değişmez (testte
`_anlik` sabitler). Aynı davranış F1b-1'den beri kabul yolunda `zincir_basi_oku`'da vardı.
Hatalı deneme sayacına dokunulmaz (geri yükleme denemesinin gecikmesi hesapsız ve süreç içidir;
plan F1b-1).

KABUL (tasarım §4.6.1 kural 1'in giriş koşullarıyla aynı; hepsi birden):

* hesabın `okul_account` satırı vardır ve mührü bu DEK'le tutar;
* rolü `yonetici`dir;
* durumu `ACIK` ya da `PAROLA_YENILENMELI`dir (`ASKIDA`, `KAPALI` ret);
* güvenlik dosyasındaki sarmalında hatalı deneme askısı (`askida`) yoktur.

Geçici ya da 180 günü dolmuş parola engel DEĞİLDİR: konsolda parola yenileme adımı yoktur,
yenileme geri yüklemeden sonraki ilk girişte istenir; geçici parolayı başka bir program
yöneticisi vermiştir, yetki genişlemez.

Satır, Django'nun SQLite'a yazdığı biçimden mühür sözleşmesinin biçimine çevrilir
(`satirdan_muhur_alanlari`; `Account.seal_fields()` ile aynı sözlük): kimlik tiresiz 32 hane
→ tireli UUID metni; zaman saat dilimsiz UTC metni (`2026-11-02 07:30:00[.ffffff]`; ayarlarda
veritabanı saat dilimi verilmediği için bağlantı saat dilimi UTC'dir) → saat dilimli UTC
`datetime`; `person`, `membership`, `term` F1c'ye dek `None`dır. Çevrilmezse her mühür tutmuyor
görünürdü; biçim eşitliği ORM'in yazdığı satırla testte sabitlenir. **F1c'de bu üç sütun
gelince okuyucu da onları okumalıdır** (eski şemalı görüntüde sütun yoksa `None`); aksi hâlde
mühürler tutmaz ve konsol geri yüklemesi kapanır (fail-closed).

GÜNCEL VERİTABANI OKUNAMIYORSA aynı denetim yedeğin görüntüsünde yapılır. Okunamıyor sayılan
hâller YALNIZ şunlardır:

* dosya yok;
* `sqlite3` hatası (bozuk dosya, tablo ya da sütun yok);
* okul kartı (`okul_schoolconfig`) tek satır değil;
* okul kartının parmak izi bu DEK'inkine eşit değil (başka kurulumun veritabanı ya da boş
  parmak izi).

Hesap satırının bulunmaması, rolün, durumun ya da mührün tutmaması OKUNAMAMA DEĞİLDİR, RETTİR
(fail-closed); hesap satırındaki geçersiz UTF-8 metin de satırın içeriğidir, mühür tutmamış
sayılır (`sqlite3`'ün kod çözme hatasına dönüşüp geri düşüşü tetiklemesin diye metin burada
çözülür). Gerekçe: geri düşüş, güncel kaydın verdiği bir "hayır"ı eski bir görüntünün
"evet"iyle değiştirmenin yolu olmamalıdır. Güncel veritabanında askıya alınmış, kapatılmış ya
da program dışından değiştirilmiş bir hesap, yedeğin alındığı gün açık bir program
yöneticisi olabilir; hesabın SATIRINI (durumu, mührü, metni) bozmak ya da silmek o eski rolüne
sığınmaya yetseydi denetim, veritabanına yazabilen herkese açık olurdu. Geri düşüş bu yüzden
hesap satırına değil, yalnız yukarıdaki dört hâle bağlıdır (plan F1b-2; tasarım §4.4.4
"güncel veritabanı okunamıyorsa"). Kabul edilen kalan risk (F1b-2 ekleri): veritabanına
yazabilen biri dosyayı bütünüyle bozmadan da görüntüye düşürebilir — okul kartını bozan
(parmak izini boşaltan, ikinci bir kart ekleyen) ya da hesap tablosunu silen veya bir sütunun
adını değiştiren TEK bir yazımla, ya da dosyayı 5 sn'den uzun özel kilitle tutarak; dosyayı
bütünüyle bozmak ya da silmek de aynı sonucu verir. O zaman bile görüntüdeki satır bu DEK'le
mühürlü, açık bir program yöneticisi olmalı ve sarmalı GÜNCEL güvenlik dosyasında askısız
durmalıdır (kapatılan hesabın sarmalı silinir, TK11); geri yükleme de notla ilk kilit
açılışında denetim izine ve Denetleme Kurulunun panosuna düşer. Görüntüye düşüş günlüğe
nedeniyle (`dosya_yok`, `okul_karti`, `parmak_izi` ya da `sqlite3` hatasının sınıfı ve kodu;
ileti ve yol yazılmaz) uyarı olarak yazılır: sessiz düşüş sonradan görülebilir. Görüntü de
okunamıyorsa ret verilir.

Rol kriptografik bir önlem değildir (tasarım §4.4.6-1). **Bilinen sınır (F1b-2 ekleri;
kullanıcı kararı bekliyor):** denetlenen hesap, parolanın açtığı SARMALIN `id` alanıdır ve bu
alan sarmalın türetimine bağlı değildir (F1b-1'in sarmal biçimi: kimlik ne KDF'ye ne Fernet'e
girer). Veri dizinine yazabilen ve HERHANGİ bir hesabın parolasını bilen biri,
`guvenlik.json`'da kendi sarmalının `id`'sini metin düzenleyiciyle program yöneticisininkine
çevirerek kilit açılışını ve konsol geri yüklemesini program yöneticisi adına yapabilir;
denetim izi ve geri yükleme notunun hesap kimliği program yöneticisini gösterir (`tanitici` da
değiştirilirse not bütünüyle). Bu kod gerektirmez, yani tasarımın tehdit 19 çıtasının ("kod
yazmayı gerektiren bir iş") altındadır; tanıtıcıyı satırın `login_name`'iyle karşılaştırmak
kapatmaz (tanıtıcı da aynı dosyadadır). Kalıcı çözüm kimliği
sarmalın türetimine bağlamaktır (ör. KDF girdisine katmak); F1b-1'in giriş yolunu ve
`guvenlik.json` türetimini değiştirdiği için kullanıcıya sorulur. O güne dek sınır
`test_bilinen_sinir_sarmal_kimligi_degistirilirse_yonetici_adina_gecer` ile sabitlenir;
bağlama yapılınca onun yerine ret testi gelir. Bunun ötesinde parolayı bilen DEK'i açar ve
mühürlü sahte bir yönetici satırı taşıyan veritabanı da üretebilir (kod ister). Bu denetim kaza
önleyicidir ve izlenebilirlik sağlar; GA-3'ü kesin olarak kapatmaz.

YEDEĞİN GÖRÜNTÜSÜ BELLEKTE açılır: `sqlite3.connect(":memory:")` + `deserialize`. Programın
yedeği WAL kipindeki kaynaktan `Connection.backup()` ile alındığı için görüntünün başlığı WAL
işaretlidir (18-19. baytlar 2); `deserialize` böyle görüntüyü açmaz ("unable to open database
file"). Bu yüzden görüntünün BELLEKTEKİ kopyasında iki bayt 1'e çekilir (geri yükleme ise
görüntünün kendisini aynen yazar). Görüntü bugün yalnız veritabanı baytlarıdır; F1b 3. adımda
kap manifesto ya da dosya bölümü taşırsa buraya yalnız veritabanı baytları verilmelidir.

**Tasarımın "bellekte" lafzından sapma (F1b-2 ekleri):** `deserialize` olmayan SQLite'ta
(< 3.36; Pardus 21'in 3.34'ü) görüntü, veri dizini altında 0700 izinli bir geçici dizine
yazılır, salt okunur açılır ve okunur okunmaz (hata yolunda da) silinir. Aile emsali
`desktop/backup.py::database_snapshot`'tır (aynı platform için aynı kısa temas bilerek kabul
edilir). Çözülen görüntü alan düzeyinde şifrelidir: geçici dosyanın açıklığı, diskte her zaman
duran `db.sqlite3` ile aynıdır; yine de kalıcı düz kopya bırakılmaz.
"""

from __future__ import annotations

import logging
import sqlite3
import tempfile
import uuid
from collections.abc import Iterator, Sequence
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from shared import crypto, kanonik, sqlite_adres

logger = logging.getLogger("oab_defteri.restore")

#: Geri yükleyebilen rol ve durumlar (`AccountRole.YONETICI`, `AccountStatus`; modeller ORM
#: istediği için değerler burada metindir, eşitliği test sabitler).
ROL_YONETICI: Final = "yonetici"
GIRIS_DURUMLARI: Final = frozenset({"ACIK", "PAROLA_YENILENMELI"})

#: Ret iletileri (docs/sozluk.md "Yedek" ve "Program yöneticisi ve roller" satırları).
ILETI_ROL: Final = (
    "Yedekten geri yüklemeyi yalnız program yöneticisi hesabıyla ya da kurtarma anahtarıyla "
    "yapabilirsiniz."
)
ILETI_DURUM: Final = "Bu hesap açık değil; geri yükleme yapılmadı. Kurtarma anahtarıyla deneyin."
ILETI_MUHUR: Final = (
    "Hesap kaydı program dışından değiştirilmiş görünüyor; geri yükleme yapılmadı. Program "
    "yöneticisine ve Denetleme Kuruluna bildirin."
)

#: Ret nedenleri (günlüğe ve teste; kullanıcı metnine çıkmaz) → ileti.
RET_SATIR_YOK: Final = "satir_yok"
RET_MUHUR: Final = "muhur"
RET_ROL: Final = "rol"
RET_DURUM: Final = "durum"
RET_ASKIDA: Final = "askida"
RET_OKUNAMADI: Final = "okunamadi"
_ILETILER: Final[dict[str, str]] = {
    RET_SATIR_YOK: ILETI_ROL,
    RET_OKUNAMADI: ILETI_ROL,
    RET_ROL: ILETI_ROL,
    RET_MUHUR: ILETI_MUHUR,
    RET_DURUM: ILETI_DURUM,
    RET_ASKIDA: ILETI_DURUM,
}

#: Kararı veren kaynak.
KAYNAK_GUNCEL: Final = "guncel"
KAYNAK_GORUNTU: Final = "goruntu"

#: `deserialize` olmayan SQLite'ta görüntünün yazıldığı geçici dizinin öneki (modül başlığı).
GECICI_DIZIN_ONEKI: Final = ".geri-yukleme-denetimi-"

# CPython `Connection.deserialize`'ı ancak SQLite ≥ 3.36 ile sunar (desktop/backup.py ile aynı
# tespit); testte yamalanır.
_DESERIALIZE_VAR = hasattr(sqlite3.Connection, "deserialize")

#: Okunamamanın günlüğe giden nedenleri (`sqlite3` hatasında hata sınıfı ve kodu yazılır).
OKUNAMAMA_DOSYA_YOK: Final = "dosya_yok"
OKUNAMAMA_OKUL_KARTI: Final = "okul_karti"
OKUNAMAMA_PARMAK_IZI: Final = "parmak_izi"

#: WAL kipinin dosya başlığındaki işareti: 18. (yazma) ve 19. (okuma) bayt.
_WAL_BAYTLARI: Final = (18, 19)


class YetkiReddi(Exception):
    """Parolası verilen hesap program yöneticisi olarak doğrulanmadı.

    `kod` ret nedenidir (`RET_*`), `kaynak` kararı veren veritabanıdır (`KAYNAK_*`). Çekirdek
    bunu `backup_restore.GeriYuklemeYetkisiz`'e çevirir (çıkış 9, `CommandError`, 400).
    """

    def __init__(self, kod: str, *, kaynak: str) -> None:
        super().__init__(_ILETILER[kod])
        self.kod = kod
        self.kaynak = kaynak

    @property
    def ileti(self) -> str:
        return _ILETILER[self.kod]


class _Okunamaz:
    """Kaynağın okunamadığını bildiren iç işaret (ret kodu değildir); `neden` günlüğe gider."""

    __slots__ = ("neden",)

    def __init__(self, neden: str) -> None:
        self.neden = neden


def _sqlite_hatasi(exc: sqlite3.Error) -> _Okunamaz:
    """`sqlite3` hatasının içeriksiz adı: sınıfı ve (varsa) kodu; ileti ve yol yazılmaz."""
    kod = getattr(exc, "sqlite_errorname", None)
    return _Okunamaz(f"{type(exc).__name__}/{kod}" if kod else type(exc).__name__)


class _GecersizMetin(Exception):
    """Metin sütununda geçersiz UTF-8 (satırın içeriğidir, okunamama değil; modül başlığı)."""


def _metin(ham: bytes) -> str:
    try:
        return ham.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _GecersizMetin from exc


def yonetici_dogrula(
    *, db_path: Path, goruntu: bytes, dek: bytes, hesap_id: object, askida: bool
) -> str:
    """Hesabı program yöneticisi olarak doğrular; kararı veren kaynağı döndürür.

    Önce güncel veritabanı (`db_path`) okunur; okunamıyorsa (modül başlığındaki dört hâl)
    yedeğin görüntüsü (`goruntu`, çözülmüş veritabanı baytları). `hesap_id` parolası doğrulanan
    sarmalın kimliğidir, `askida` o sarmalın hatalı deneme askısı. Kabulde `KAYNAK_GUNCEL` ya da
    `KAYNAK_GORUNTU`; aksi hâlde `YetkiReddi`. Hiçbir dosyaya yazmaz.
    """
    anahtar = _hesap_anahtari(hesap_id)
    kaynak = KAYNAK_GUNCEL
    karar = _guncel_karari(db_path, dek, anahtar)
    if isinstance(karar, _Okunamaz):
        logger.warning(
            "Güncel veritabanı okunamadı (neden: %s); hesap yedeğin görüntüsünde denetleniyor.",
            karar.neden,
        )
        kaynak = KAYNAK_GORUNTU
        karar = _goruntu_karari(db_path.parent, goruntu, dek, anahtar)
        if isinstance(karar, _Okunamaz):
            logger.warning("Yedeğin görüntüsü de okunamadı (neden: %s).", karar.neden)
            raise YetkiReddi(RET_OKUNAMADI, kaynak=kaynak)
    if isinstance(karar, str):
        raise YetkiReddi(karar, kaynak=kaynak)
    if askida:
        raise YetkiReddi(RET_ASKIDA, kaynak=kaynak)
    return kaynak


def satirdan_muhur_alanlari(satir: Sequence[Any]) -> dict[str, Any]:
    """`okul_account` satırını (`hesap_satiri` sırası) mühür alanlarına çevirir.

    Sonuç `Account.seal_fields()` ile aynı sözlüktür (modül başlığı). Biçimsiz kimlik ya da
    zaman `ValueError`, beklenmeyen tür `TypeError` yükseltir (çağıran "mühür tutmadı" sayar).
    """
    kimlik, tanitici, rol, durum, acilis, kapanis, _muhur = satir
    return {
        "id": _kimlik(kimlik),
        "login_name": tanitici,
        "role": rol,
        "status": durum,
        "person": None,
        "membership": None,
        "term": None,
        "opened_at": _zaman(acilis),
        "closed_at": _zaman(kapanis),
    }


def hesap_satiri(baglanti: sqlite3.Connection, anahtar: str) -> Any:
    """Hesabın mühre giren sütunları ve mührü (`satirdan_muhur_alanlari` bu sırayı açar).

    `anahtar` SQLite'taki kimliktir (tiresiz 32 hane); satır yoksa None. Sorgu kaynakta sabit
    bir `SELECT`'tir (izsiz yazım taraması salt okuma sayar).
    """
    return baglanti.execute(
        "SELECT id, login_name, role, status, opened_at, closed_at, seal "
        "FROM okul_account WHERE id = ?",
        (anahtar,),
    ).fetchone()


# ---------------------------------------------------------------------------
# İç yardımcılar
# ---------------------------------------------------------------------------
def _hesap_anahtari(hesap_id: object) -> str | None:
    """Sarmal kimliğinin SQLite'taki biçimi (tiresiz 32 hane); biçimsizse None (satır yok)."""
    try:
        return uuid.UUID(str(hesap_id)).hex
    except ValueError:
        return None


def _kimlik(deger: object) -> str:
    if not isinstance(deger, str):
        raise TypeError("Hesap kimliği metin değil.")
    return str(uuid.UUID(deger))


def _zaman(deger: object) -> datetime | None:
    """Django'nun saat dilimsiz UTC metni → saat dilimli zaman (Django'nun dönüştürücüsü gibi)."""
    if deger is None:
        return None
    if not isinstance(deger, str):
        raise TypeError("Zaman sütunu metin değil.")
    an = datetime.fromisoformat(deger)
    return an.replace(tzinfo=UTC) if an.tzinfo is None else an


def _baglanti_hazirla(baglanti: sqlite3.Connection) -> sqlite3.Connection:
    # Metin sütunları burada çözülür: geçersiz UTF-8 `sqlite3` hatası olup geri düşüşü
    # tetiklemesin (modül başlığı).
    baglanti.text_factory = _metin
    return baglanti


def _karar(baglanti: sqlite3.Connection, dek: bytes, anahtar: str | None) -> object:
    """Tek kaynağın kararı: None (kabul), ret kodu ya da `_Okunamaz`.

    `sqlite3.Error` yükseltebilir; çağıran onu okunamama sayar.
    """
    try:
        kartlar = baglanti.execute("SELECT app_password_hash FROM okul_schoolconfig LIMIT 2")
        parmak_izleri = kartlar.fetchall()
    except _GecersizMetin:
        # Okunamayan parmak izi bu DEK'inkine eşit değildir.
        return _Okunamaz(OKUNAMAMA_PARMAK_IZI)
    if len(parmak_izleri) != 1:
        return _Okunamaz(OKUNAMAMA_OKUL_KARTI)
    if not kanonik.esit(parmak_izleri[0][0], crypto.key_fingerprint(dek)):
        return _Okunamaz(OKUNAMAMA_PARMAK_IZI)
    if anahtar is None:
        return RET_SATIR_YOK
    try:
        satir = hesap_satiri(baglanti, anahtar)
    except _GecersizMetin:
        return RET_MUHUR
    if satir is None:
        return RET_SATIR_YOK
    return _satir_karari(satir, dek)


def _satir_karari(satir: Sequence[Any], dek: bytes) -> str | None:
    """Mühür (önce: tutmuyorsa öteki değerlere güvenilmez), rol, durum."""
    muhur = satir[6]
    try:
        beklenen = kanonik.hesap_muhru(crypto.account_seal_key(dek), satirdan_muhur_alanlari(satir))
    except (TypeError, ValueError):  # KanonikHata bir TypeError'dır
        return RET_MUHUR
    if not muhur or not kanonik.esit(muhur, beklenen):
        return RET_MUHUR
    if satir[2] != ROL_YONETICI:
        return RET_ROL
    if satir[3] not in GIRIS_DURUMLARI:
        return RET_DURUM
    return None


def _guncel_karari(db_path: Path, dek: bytes, anahtar: str | None) -> object:
    """Güncel veritabanının kararı; dosya yoksa ya da `sqlite3` hatasında `_Okunamaz`."""
    if not db_path.is_file():
        return _Okunamaz(OKUNAMAMA_DOSYA_YOK)
    adres = sqlite_adres.salt_okunur_adres(db_path)
    try:
        with closing(sqlite3.connect(adres, uri=True, timeout=5)) as baglanti:
            return _karar(_baglanti_hazirla(baglanti), dek, anahtar)
    except sqlite3.Error as exc:
        return _sqlite_hatasi(exc)


def _goruntu_karari(dizin: Path, goruntu: bytes, dek: bytes, anahtar: str | None) -> object:
    """Yedeğin görüntüsünün kararı (bellekte; `deserialize` yoksa geçici dizinde)."""
    try:
        with _goruntu_baglantisi(dizin, wal_basligini_yama(goruntu)) as baglanti:
            return _karar(_baglanti_hazirla(baglanti), dek, anahtar)
    except sqlite3.Error as exc:
        return _sqlite_hatasi(exc)
    except OSError as exc:
        logger.warning("Yedeğin görüntüsü geçici dizine yazılamadı; hesap denetlenemedi.")
        return _Okunamaz(type(exc).__name__)


def wal_basligini_yama(goruntu: bytes) -> bytes:
    """WAL işaretli başlığın (18-19. bayt = 2) bellekteki kopyasını 1'e çeker (modül başlığı).

    Girdi değişmez; başlık WAL işaretli değilse aynı baytlar döner.
    """
    if not any(len(goruntu) > i and goruntu[i] == 2 for i in _WAL_BAYTLARI):
        return goruntu
    kopya = bytearray(goruntu)
    for i in _WAL_BAYTLARI:
        if kopya[i] == 2:
            kopya[i] = 1
    return bytes(kopya)


@contextmanager
def _goruntu_baglantisi(dizin: Path, goruntu: bytes) -> Iterator[sqlite3.Connection]:
    """Görüntüyü salt okumak için açar; çıkışta bağlantı kapanır, geçici dizin silinir."""
    if _DESERIALIZE_VAR:
        baglanti = sqlite3.connect(":memory:")
        try:
            baglanti.deserialize(goruntu)
            yield baglanti
        finally:
            baglanti.close()
        return
    # Pardus 21 (SQLite 3.34): veri dizini altında 0700 dizin (`mkdtemp`), hemen silinir.
    dizin.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dizin, prefix=GECICI_DIZIN_ONEKI) as gecici:
        yol = Path(gecici).resolve() / "goruntu.sqlite3"
        yol.write_bytes(goruntu)
        baglanti = sqlite3.connect(sqlite_adres.salt_okunur_adres(yol), uri=True)
        try:
            yield baglanti
        finally:
            baglanti.close()
