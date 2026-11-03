"""Geri yüklemede parola kaydı özetlerinin onarımı — ORM'SİZ (kullanıcı kararı 03.11.2026).

Hesabın mühürlü `Account` satırı `guvenlik.json`'daki güncel sarmalın özetini taşır
(`wrap_digest`, iki aşamalı yazımın ara hâli `wrap_digest_pending`; `app_password` modül başlığı
"SARMALIN TAZELİĞİ"). Geri yükleme veritabanını yedektekiyle değiştirir ama güvenlik dosyasına
(parola yolunda ve güncel dosyanın kullanıldığı kurtarma anahtarı yolunda) dokunmaz: GÜNCEL
`guvenlik.json` ile ESKİ veritabanı birleşir (`backup_restore` modül başlığı). Onarımsız, yedekten
sonra parolası değişen hesabın geri yüklenen satırı yedek günündeki sarmalın özetini taşırdı:
meşru kullanıcı yeni parolasıyla kilitlenir, arşivdeki yedek günü sarmalı ise eski parolayla
açılırdı.

GÜVEN ÇAPASI geri yüklemeden ÖNCEKİ (kenara alınacak) veritabanının mühürlü satırlarıdır: o
veritabanı güncel `guvenlik.json`'la birlikte yaşamıştır ve hangi sarmalın meşru olduğunu söyler —
ama YALNIZ TAZEYSE. Dosya veri dizinindedir; program kapalıyken eski bir düz kopyasıyla
(önceden alınmış bir kopya, bir `db-onceki-*`) değiştirilebilir ve böyle bir kopyanın satırları da
bu DEK'le mühürlüdür. Eski kopya çapa sayılsaydı o günün özetini, o gün geçerli olan (arşivden geri
konmuş) sarmalla birlikte TAZE bir yedeğin satırına taşıtırdı (bağımsız denetim bulgusu: çapa
ikamesi). Çapa bu yüzden ancak geri yüklenen yedeğin ZİNCİR BAŞINI (`okul_audittrail`'in son
satırının `seq`'i ve `mac`'i) aynen içeriyorsa, yani yedekten türemişse TAZEDİR (zincir MAC'lidir: son satırın
`mac`'i bütün öneki bağlar; boş zincir her zincirin önekidir). İçermiyorsa ya da yedeğin zincir
başı okunamıyorsa (soy doğrulanamaz) BAYATTIR: değiştirilmiş eski bir kopya olabilir, önceki bir
geri yüklemenin veritabanı olabilir (çift geri yükleme: önce eski A, sonra daha yeni B yedeği;
ya da bir geri yüklemeden sonra öbür zaman çizgisinden bir yedek). Bayat çapa hiçbir özet
VERMEZ, yalnız kısıtlar.

Her hesap için, geri yüklenen satırın mührü bu DEK'le tutuyorsa (tutmuyorsa satıra dokunulmaz,
tutmayan mühür yeniden hesaplanmaz — tasarım §4.6.1 kural 1):

* hesabın çapada SATIRI YOKSA çapa o hesap için hiçbir sarmalı doğrulayamaz: iki özet BOŞALTILIR
  ve satır yeniden mühürlenir (BOŞALTILAN). Hâl çift geri yüklemede doğar (ikinci geri yüklemenin
  çapası birincinin yazdığı eski veritabanıdır; o tarihten sonra açılan hesap orada yoktur); taze
  çapada yalnız satır program dışından silinmişse. Hesap parolayla açılmaz, iki depo kartının
  `digest_mismatch` listesinde görünür; çaresi program yöneticisinin parola sıfırlaması, program
  yöneticisinin kendi hesabıysa kurtarma anahtarıyla açılıştır;
* çapadaki satırın MÜHRÜ TUTMUYORSA satıra dokunulmaz (DEĞİŞMEYEN): çapa o hesap için güvenilir
  değildir; geri yüklenen satır yedekteki özeti taşır (kalan risk, aşağıda);
* çapadaki (mührü tutan) satır `KAPALI` ise iki özet BOŞALTILIR (BOŞALTILAN; TK11): kapanan
  hesabın sarmalı her yerden silinmiştir; hesabın açık olduğu bir yedek geri yüklenince satır açık
  döner ve kapanıştaki son özet ona geçseydi o sarmalın saklanmış bir kopyası eski parolayla
  açardı. Hesap ancak program yöneticisinin parola sıfırlamasıyla yeniden açılır;
* çapa BAYATSA satıra dokunulmaz (yedekteki özet kalır; DEĞİŞMEYEN). Geri yükleyen program
  yöneticisi de buna dahildir: yedekten sonra parolasını değiştirdiyse kurtarma anahtarıyla açar;
* çapa TAZEYSE: güncel `guvenlik.json`'daki sarmalının özeti çapadaki satırın asıl ya da bekleyen
  özetini tutuyorsa geri yüklenen satırın asıl özeti o olur, bekleyen boşalır (TAŞINAN); tutmuyorsa
  (dosyada sarmal yok, eski ya da program dışından konmuş sarmal) çapadaki İKİ özet aynen geçer
  (ÇAPADAN). Görev metnindeki "dokunulmaz" seçeneğinden bilinçli sapmadır: dokunulmasaydı geri
  yüklenen satır yedek günündeki sarmalın özetini taşırdı ve geri yüklemeden önce
  `guvenlik.json`'a konan (yedek gününde güncel olan) eski sarmal eski parolayla açılırdı.
  Çapanın özetleri yalnız çapanın bildiği en yeni meşru sarmalı açar; o sarmal dosyada yoksa hesap
  parolayla açılmaz (`digest_mismatch`).

Böylece, ÖNCEKİ VERİTABANI SAĞLAM VE TAZE OLDUĞU SÜRECE, geri yüklemeden önce `guvenlik.json`'a
eski sarmal koyup geri yüklemeyle onu "aklama" yolu kapanır: aklanacak sarmalın özeti çapayı
tutmaz. Kalan hâller (kalan risk; `app_password` modül başlığı "KALAN RİSKLER" (c)): çapa
OKUNAMIYORSA (dosya yok, `sqlite3` hatası, okul kartı tek satır değil ya da parmak izi bu DEK'inki
değil — `geri_yukleme_yetkisi` modül başlığındaki dört hâl) hiçbir satıra dokunulmaz; çapa
bayatsa ya da hesabın çapadaki satırının mührü bozuksa o satırlara dokunulmaz. Bu hâllerde geri
yüklenen satırlar yedek günündeki özetleri taşır ve o günün parola kaydı (arşivden geri konursa) o
günün parolasıyla açılır. Çapayı okunamaz kılmak (`db.sqlite3`'ü silmek ya da adını değiştirmek)
ya da bir satırın mührünü bozmak kod istemez, kasıtla da yapılabilir; olay geri yükleme kartıyla
(`GERI_YUKLEME` satırı; mühür bozuksa ayrıca `BUTUNLUK` kartıyla) görünür olur, kriptografik
olarak kapanmaz. Bu hâllerde özetlerin boşaltılması (fail-closed) kullanıcı kararını bekler.

YAZIM YERİ: geri yüklenecek içerik önce yanına `.tmp` olarak yazılır; onarım o dosyada, TAKASTAN
ÖNCE yapılır ve commit edilir; ancak sonra `.tmp` veritabanının yerine konur
(`backup_restore._swap_database_files`). Onarım yazılamazsa (`sqlite3` yazım hatası, WAL dosyası
ana dosyaya aktarılamadı) geri yükleme yarıda kalır ve hiçbir dosya değişmez
(`OnarimYazilamadi`, bir `OSError`). Geri yüklenen veritabanında hesap tablosu ya da özet
sütunları okunamıyorsa (bu göçten önceki bir yedek) onarım atlanır ve uyarı günlüğe düşer. Göç
sütunları boş ekler; ama o satırların mührü özet alanları mühre girmeden hesaplanmıştır ve yeni
biçimle tutmaz: hiçbir hesap açılmaz, kurtarma anahtarıyla açılış dahil; parola sıfırlaması da
yapılamaz (fail-closed; kullanıcı kararı 03.11.2026, 3: göç gerekmez, deneme kurulumları silinip
yeniden kurulur).

İZ: onarım ORM'siz bir yazımdır ve satır yazmaz (geri yüklemenin kendisi `GERI_YUKLEME`
satırıyla ilk kilit açılışında izlenir; izsiz yazım taramasında adıyla muaftır). Sonucu sırsız
günlüğe yazılır: hesap kimlikleri (kişisiz) ve sayılar; tanıtıcı, özet ve mühür yazılmaz.
Geri yüklenen satırların içerik MAC'i bu yüzden son iz satırınkinden ayrılabilir (kalan; plan
F1b-2 ekleri).

METİN: satırlar `surrogateescape` ile çözülür (`_metin`): geçersiz UTF-8'li satır kanonik
kodlamada reddedilir ve mühür tutmamış sayılır, bir satır bütün okumayı düşürmez. Geri yükleme
yetkisinin kuralından (`geri_yukleme_yetkisi._metin`: geçersiz metin `_GecersizMetin` olarak
çağırana çıkar) bilinçli olarak ayrılır: orada tek satırın kararı verilir, burada bütün satırlar
okunur.

Modül yalnız standart kitaplığın `sqlite3`'üne, `shared.kanonik`'e, `shared.crypto`'nun saf
işlevlerine ve `geri_yukleme_yetkisi`'nin satır okuyucusuna dayanır (Django ayarı, uygulama
kaydı ve sorgusu gerekmez).
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from apps.okul.services import geri_yukleme_yetkisi as yetki
from shared import crypto, kanonik, sqlite_adres

logger = logging.getLogger("oab_defteri.restore")

#: SQLite'ın yan dosyaları (onarımdan sonra `.tmp`'nin yanında kalmamalı).
_WAL = "-wal"
_SHM = "-shm"

#: `AccountStatus.KAPALI` (modeller ORM istediği için değer burada metindir; eşitliği test sabitler).
DURUM_KAPALI: Final = "KAPALI"

#: Onarımın türleri (`OnarimSonucu` listeleri; modül başlığı).
_TASINAN: Final = "tasinan"
_CAPADAN: Final = "capadan"
_BOSALTILAN: Final = "bosaltilan"

#: Çapanın okunamama nedeni olmayan, onarımın günlüğe yazdığı bayatlık nedeni.
NEDEN_BAYAT: Final = "capa_bayat"

#: İzi boş veritabanının zincir başı (`geri_yukleme_notu.BOS_ZINCIR` ile aynı: "zincir yoktu").
BOS_ZINCIR: Final[tuple[int, str]] = (0, "")


class OnarimYazilamadi(OSError):
    """Onarım geri yüklenecek dosyaya yazılamadı: geri yükleme yarıda kalır, takas yapılmaz."""


@dataclass(frozen=True)
class OnarimSonucu:
    """Onarımın sırsız özeti (kimlikler kişisizdir; tanıtıcı yoktur)."""

    #: Özeti güncel `guvenlik.json`'daki sarmalınkine çekilen hesaplar.
    tasinan: tuple[str, ...] = ()
    #: Özetleri çapadan (önceki veritabanından) aynen geçen hesaplar.
    capadan: tuple[str, ...] = ()
    #: Özetleri boşaltılan hesaplar (çapada satırı yok ya da çapada `KAPALI`).
    bosaltilan: tuple[str, ...] = ()
    #: Çapa okunamadı (ya da geri yüklenen satırlar okunamadı): hiçbir satıra dokunulmadı.
    atlandi: bool = False
    #: Çapa geri yüklenen yedeğin zincir başını içermiyor: özet verilmedi, yalnız kısıtlandı.
    bayat: bool = False
    neden: str = ""
    degismeyen: tuple[str, ...] = field(default=())


@dataclass(frozen=True)
class _Capa:
    """Okunabilen çapa (modül başlığı)."""

    #: Mührü tutan satırlar: `{kanonik kimlik: (asıl özet, bekleyen özet, durum)}`.
    satirlar: dict[str, tuple[str, str, str]]
    #: Satırı olan ama mührü tutmayan (ya da aynı kimliği iki kez taşıyan) hesaplar.
    muhursuz: frozenset[str]
    #: Geri yüklenen yedeğin zincir başını içeriyor mu (taze çapa).
    taze: bool


def _metin(ham: bytes) -> str:
    """Geçersiz UTF-8 satırın içeriğidir: `surrogateescape` ile çözülür, kanonik kodlama onu
    reddeder ve satır mühür tutmamış sayılır (bir satır bütün okumayı düşürmez; modül başlığı)."""
    return ham.decode("utf-8", errors="surrogateescape")


def _sqlite_nedeni(exc: sqlite3.Error) -> str:
    kod = getattr(exc, "sqlite_errorname", None)
    return f"{type(exc).__name__}/{kod}" if kod else type(exc).__name__


def _zincir_basi(baglanti: sqlite3.Connection) -> tuple[int, str] | None:
    """Denetim izinin son satırının `(seq, mac)`'i; iz boşsa `BOS_ZINCIR`, biçimsizse None.

    `geri_yukleme_notu.zincir_basi_oku` ile aynı sorgu ve aynı boş zincir (o modül Django ister,
    bu modül istemez). Boş zincir her zincirin önekidir: her çapa onu içerir. Programda hesabı
    olan bir veritabanının zinciri boş olamaz (ilk hesap `HESAP` satırıyla açılır); boş zincirli
    yedek ancak kurulumdan önceki ya da izi program dışından silinmiş bir veritabanıdır.
    """
    satir = baglanti.execute(
        "SELECT seq, mac FROM okul_audittrail ORDER BY seq DESC LIMIT 1"
    ).fetchone()
    if satir is None:
        return BOS_ZINCIR
    seq, mac = satir
    if isinstance(seq, bool) or not isinstance(seq, int) or not isinstance(mac, str) or not mac:
        return None
    return seq, mac


def _yedegi_oku(yeni_db: Path) -> tuple[list[Any], tuple[int, str] | None] | str:
    """Geri yüklenecek dosyanın hesap satırları ve zincir başı; satırlar okunamıyorsa neden.

    Salt okunur açılır: değişecek satır yoksa geri yüklenecek dosyaya yazılmaz (baytları aynen
    kalır). Zincir başı okunamıyorsa (tablo yok) None: çapa bayat sayılır.
    """
    try:
        with closing(
            sqlite3.connect(sqlite_adres.salt_okunur_adres(yeni_db), uri=True, timeout=5)
        ) as okuyucu:
            okuyucu.text_factory = _metin
            satirlar = yetki.hesap_satirlari(okuyucu)
            try:
                bas = _zincir_basi(okuyucu)
            except sqlite3.Error:
                bas = None
    except sqlite3.Error as exc:
        return _sqlite_nedeni(exc)
    return satirlar, bas


def _basi_iceriyor_mu(baglanti: sqlite3.Connection, bas: tuple[int, str]) -> bool:
    """Çapa, yedeğin zincir başını (aynı `seq`'te aynı `mac`) taşıyor mu? (modül başlığı)"""
    if bas == BOS_ZINCIR:
        return True
    return (
        baglanti.execute(
            "SELECT 1 FROM okul_audittrail WHERE seq = ? AND mac = ? LIMIT 1", bas
        ).fetchone()
        is not None
    )


def _capa_oku(onceki_db: Path, dek: bytes, yedek_basi: tuple[int, str] | None) -> _Capa | str:
    """Çapa: önceki veritabanının satırları ve tazeliği; okunamıyorsa nedeni (metin) döner.

    Salt okunur açılır (`mode=ro`; adres `sqlite_adres`'ten, `geri_yukleme_yetkisi` ile aynı):
    kenara alınacak dosya değişmez. Kimliği çevrilemeyen satır hiçbir hesabı anlatmaz, atlanır.
    """
    if not onceki_db.is_file():
        return yetki.OKUNAMAMA_DOSYA_YOK
    try:
        with closing(
            sqlite3.connect(sqlite_adres.salt_okunur_adres(onceki_db), uri=True, timeout=5)
        ) as baglanti:
            baglanti.text_factory = _metin
            neden = yetki.okul_karti_okunamaz_mi(baglanti, dek)
            if neden is not None:
                return neden
            satirlar = yetki.hesap_satirlari(baglanti)
            taze = yedek_basi is not None and _basi_iceriyor_mu(baglanti, yedek_basi)
    except sqlite3.Error as exc:
        return _sqlite_nedeni(exc)
    muhurlu: dict[str, tuple[str, str, str]] = {}
    muhursuz: set[str] = set()
    for satir in satirlar:
        kimlik = yetki.satir_kimligi(satir)
        if kimlik is None:
            continue
        asil, bekleyen = satir[yetki.SIRA_OZET], satir[yetki.SIRA_BEKLEYEN]
        if (
            kimlik in muhurlu
            or kimlik in muhursuz
            or not isinstance(asil, str)
            or not isinstance(bekleyen, str)
            or not yetki.muhurlu_satir_mi(satir, dek)
        ):
            muhurlu.pop(kimlik, None)
            muhursuz.add(kimlik)
            continue
        durum = str(yetki.satirdan_muhur_alanlari(satir)["status"])
        muhurlu[kimlik] = (asil, bekleyen, durum)
    return _Capa(satirlar=muhurlu, muhursuz=frozenset(muhursuz), taze=taze)


def _hedef(capa: _Capa, kimlik: str, dosyadaki: str | None) -> tuple[tuple[str, str], str] | None:
    """Geri yüklenen satırın özetleri ve onarımın türü; dokunulmayacaksa None (modül başlığı).

    Çağıran, çapada mührü tutmayan satırı önceden ayırmıştır.
    """
    capadaki = capa.satirlar.get(kimlik)
    if capadaki is None or capadaki[2] == DURUM_KAPALI:
        return ("", ""), _BOSALTILAN
    if not capa.taze:
        return None
    asil, bekleyen, _durum = capadaki
    tutar = bool(dosyadaki) and (
        (bool(asil) and kanonik.esit(asil, dosyadaki))
        or (bool(bekleyen) and kanonik.esit(bekleyen, dosyadaki))
    )
    if tutar:
        return (str(dosyadaki), ""), _TASINAN
    return (asil, bekleyen), _CAPADAN


def _yan_dosyalari_temizle(yeni_db: Path) -> None:
    """Onarımdan sonra `.tmp`'nin `-wal`'ı boş olmalı (ana dosyaya aktarılmış); değilse yazım
    eksik kalmıştır ve takas yapılmaz. Boş `-wal` ve `-shm` silinir."""
    wal = yeni_db.with_name(yeni_db.name + _WAL)
    if wal.exists() and wal.stat().st_size > 0:
        raise OnarimYazilamadi("Onarımın WAL dosyası ana dosyaya aktarılamadı.")
    wal.unlink(missing_ok=True)
    yeni_db.with_name(yeni_db.name + _SHM).unlink(missing_ok=True)


def ozetleri_onar(
    *,
    onceki_db: Path,
    yeni_db: Path,
    dek: bytes,
    sarmal_ozetleri: Mapping[str, str | None],
) -> OnarimSonucu:
    """Geri yüklenecek `yeni_db`'deki (takastan önceki `.tmp`) hesap özetlerini onarır.

    `onceki_db` kenara alınacak (henüz yerinde duran) veritabanıdır — çapa; `sarmal_ozetleri`
    güncel `guvenlik.json`'daki sarmalların `{kanonik kimlik: özet}` sözlüğüdür (kurtarma
    başlığından yazılacak dosyada boştur). Kurallar modül başlığındadır. Yazım hatasında
    `OnarimYazilamadi`.
    """
    yedek = _yedegi_oku(yeni_db)
    if isinstance(yedek, str):
        logger.warning(
            "Geri yüklemede parola kaydı özetleri onarılmadı: geri yüklenen veritabanının hesap "
            "satırları okunamadı (neden: %s).",
            yedek,
        )
        _yan_dosyalari_temizle(yeni_db)
        return OnarimSonucu(atlandi=True, neden=yedek)
    satirlar, yedek_basi = yedek
    capa = _capa_oku(onceki_db, dek, yedek_basi)
    if isinstance(capa, str):
        logger.warning(
            "Geri yüklemede parola kaydı özetleri onarılmadı: önceki veritabanı okunamadı "
            "(neden: %s); geri yüklenen hesaplar yedekteki özetleri taşır.",
            capa,
        )
        _yan_dosyalari_temizle(yeni_db)
        return OnarimSonucu(atlandi=True, neden=capa)
    if not capa.taze:
        logger.warning(
            "Önceki veritabanı geri yüklenen yedeğin zincir başını içermiyor (bayat çapa: eski "
            "bir kopya ya da önceki bir geri yüklemenin veritabanı); özet taşınmaz, yalnız "
            "çapada olmayan ve kapalı hesapların özetleri boşaltılır."
        )
    guncellemeler: list[tuple[str, str, str, Any]] = []
    turler: dict[str, list[str]] = {_TASINAN: [], _CAPADAN: [], _BOSALTILAN: []}
    degismeyen: list[str] = []
    anahtar = crypto.account_seal_key(dek)
    for satir in satirlar:
        kimlik = yetki.satir_kimligi(satir)
        if kimlik is None or not yetki.muhurlu_satir_mi(satir, dek):
            continue
        hedef = (
            None if kimlik in capa.muhursuz else _hedef(capa, kimlik, sarmal_ozetleri.get(kimlik))
        )
        if hedef is None or (satir[yetki.SIRA_OZET], satir[yetki.SIRA_BEKLEYEN]) == hedef[0]:
            degismeyen.append(kimlik)
            continue
        (asil, bekleyen), tur = hedef
        alanlar = {
            **yetki.satirdan_muhur_alanlari(satir),
            "wrap_digest": asil,
            "wrap_digest_pending": bekleyen,
        }
        guncellemeler.append(
            (asil, bekleyen, kanonik.hesap_muhru(anahtar, alanlar), satir[yetki.SIRA_KIMLIK])
        )
        turler[tur].append(kimlik)
    if guncellemeler:
        try:
            with closing(sqlite3.connect(yeni_db, timeout=5)) as yazici:
                yazici.executemany(
                    "UPDATE okul_account SET wrap_digest = ?, wrap_digest_pending = ?, seal = ? "
                    "WHERE id = ?",
                    guncellemeler,
                )
                yazici.commit()
        except sqlite3.Error as exc:
            raise OnarimYazilamadi(_sqlite_nedeni(exc)) from exc
    _yan_dosyalari_temizle(yeni_db)
    sonuc = OnarimSonucu(
        tasinan=tuple(sorted(turler[_TASINAN])),
        capadan=tuple(sorted(turler[_CAPADAN])),
        bosaltilan=tuple(sorted(turler[_BOSALTILAN])),
        bayat=not capa.taze,
        neden="" if capa.taze else NEDEN_BAYAT,
        degismeyen=tuple(sorted(degismeyen)),
    )
    if guncellemeler:
        logger.info(
            "Geri yüklemede parola kaydı özetleri onarıldı: %d hesap güncel güvenlik dosyasına "
            "(%s), %d hesap önceki veritabanına göre (%s), %d hesabın özeti boşaltıldı (%s).",
            len(sonuc.tasinan),
            ", ".join(sonuc.tasinan) or "-",
            len(sonuc.capadan),
            ", ".join(sonuc.capadan) or "-",
            len(sonuc.bosaltilan),
            ", ".join(sonuc.bosaltilan) or "-",
        )
    return sonuc
