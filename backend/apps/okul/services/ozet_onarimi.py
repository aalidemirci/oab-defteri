"""Geri yüklemede parola kaydı özetlerinin onarımı — ORM'SİZ (kullanıcı kararı 03.11.2026).

Hesabın mühürlü `Account` satırı `guvenlik.json`'daki güncel sarmalın özetini taşır
(`wrap_digest`, iki aşamalı yazımın ara hâli `wrap_digest_pending`; `app_password` modül başlığı
"SARMALIN TAZELİĞİ"). Geri yükleme veritabanını yedektekiyle değiştirir ama güvenlik dosyasına
(parola yolunda ve güncel dosyanın kullanıldığı kurtarma anahtarı yolunda) dokunmaz: GÜNCEL
`guvenlik.json` ile ESKİ veritabanı birleşir (`backup_restore` modül başlığı). Onarımsız, yedekten
sonra parolası değişen hesabın geri yüklenen satırı yedek günündeki sarmalın özetini taşırdı:
meşru kullanıcı yeni parolasıyla kilitlenir, arşivdeki yedek günü sarmalı ise eski parolayla
açılırdı.

GÜVEN ÇAPASI geri yüklemeden ÖNCEKİ (kenara alınacak) veritabanının mührü VE izi tutan
satırlarıdır (izi: denetim izindeki son içerik MAC'li kaydı; `satir_izi`, kullanıcı kararı
03.11.2026 "Girişte reddet"): o veritabanı güncel `guvenlik.json`'la birlikte yaşamıştır ve hangi
sarmalın meşru olduğunu söyler — ama YALNIZ TAZEYSE. Dosya veri dizinindedir; program kapalıyken
eski bir düz kopyasıyla (önceden alınmış bir kopya, bir `db-onceki-*`) değiştirilebilir ve böyle
bir kopyanın satırları da bu DEK'le mühürlüdür. Eski kopya çapa sayılsaydı o günün özetini, o gün
geçerli olan (arşivden geri konmuş) sarmalla birlikte TAZE bir yedeğin satırına taşıtırdı (bağımsız
denetim bulgusu: çapa ikamesi). Çapa bu yüzden ancak geri yüklenen yedeğin ZİNCİR BAŞINI
(`okul_audittrail`'in son satırının `seq`'i ve `mac`'i) aynen içeriyorsa, yani yedekten türemişse
TAZEDİR (zincir MAC'lidir: son satırın `mac`'i bütün öneki bağlar; boş zincir her zincirin
önekidir). Baş satırın varlığı tek başına soy kanıtı değildir: çapa program dışından
değiştirilebilir ve tek bir INSERT eski bir kopyaya yedeğin başını ekler (bağımsız denetim bulgusu:
sahte tazelik; çapanın zinciri burada doğrulanmaz). Bu yüzden taze çapada da hesabın çapadaki
satırının eşleştiği iz satırı, geri yüklenen satırın kendi izinde eşleştiği satırdan eski olamaz;
eskiyse çapa o hesap için kullanılamaz (K-a) — SIRA KURALI. Meşru taze çapa yedeğin önekini taşır:
geri yüklenen satırın eşleştiği iz satırı çapada da vardır, çapadaki satır onu ya da daha yeni bir
satırı tutar. Eski bir kopyadaki satır ise kopyanın kendi (daha eski) iz satırını tutar; sırası
SQLite'ta tamsayı olmayan (BLOB'a çevrilmiş) iz satırı da çapa satırını tutmaz sayar (`satir_izi`
adım 2). İçermiyorsa ya da yedeğin zincir başı okunamıyorsa (soy doğrulanamaz) BAYATTIR:
değiştirilmiş eski bir kopya olabilir, önceki bir geri yüklemenin veritabanı olabilir (çift geri
yükleme: önce eski A, sonra daha yeni B yedeği; ya da bir geri yüklemeden sonra öbür zaman
çizgisinden bir yedek). Bayat çapa hiçbir özet VERMEZ, yalnız kısıtlar (sıra kuralı bayat çapada
uygulanmaz: iki zaman çizgisinin sıraları karşılaştırılamaz ve kısıtları gevşetirdi). Taze çapada
da tek bir satırı eski bir kopyadan geri sarılmış olabilir (Senaryo 1: geri sarılmış satır,
ardından taze bir yedeğin geri yüklenmesi): izi tutmayan çapa satırı mührü bozuk satır gibi
KULLANILAMAZ.

Her hesap için, geri yüklenen satırın mührü ve izi bu DEK'le (geri yüklenen veritabanının kendi
izine karşı) tutuyorsa — tutmuyorsa satıra dokunulmaz, tutmayan mühür yeniden hesaplanmaz, izi
tutmayan satır yeniden mühürlenip yeni bir iz satırıyla AKLANMAZ (tasarım §4.6.1 kural 1):

* hesabın çapada SATIRI YOKSA çapa o hesap için hiçbir sarmalı doğrulayamaz: iki özet BOŞALTILIR
  ve satır yeniden mühürlenir (BOŞALTILAN). Hâl çift geri yüklemede doğar (ikinci geri yüklemenin
  çapası birincinin yazdığı eski veritabanıdır; o tarihten sonra açılan hesap orada yoktur); taze
  çapada yalnız satır program dışından silinmişse. Hesap parolayla açılmaz, iki depo kartının
  `digest_mismatch` listesinde görünür; çaresi program yöneticisinin parola sıfırlaması, program
  yöneticisinin kendi hesabıysa kurtarma anahtarıyla açılıştır;
* çapadaki (mührü ve izi tutan) satır `KAPALI` ise iki özet BOŞALTILIR (BOŞALTILAN; TK11): kapanan
  hesabın sarmalı her yerden silinmiştir; hesabın açık olduğu bir yedek geri yüklenince satır açık
  döner ve kapanıştaki son özet ona geçseydi o sarmalın saklanmış bir kopyası eski parolayla
  açardı. Hesap ancak program yöneticisinin parola sıfırlamasıyla yeniden açılır;
* çapa TAZEYSE ve hesabın çapadaki satırı kullanılabiliyorsa: güncel `guvenlik.json`'daki sarmalının
  özeti çapadaki satırın asıl ya da bekleyen özetini tutuyorsa geri yüklenen satırın asıl özeti o
  olur, bekleyen boşalır (TAŞINAN); tutmuyorsa (dosyada sarmal yok, eski ya da program dışından
  konmuş sarmal) çapadaki İKİ özet aynen geçer (ÇAPADAN). Görev metnindeki "dokunulmaz"
  seçeneğinden bilinçli sapmadır: dokunulmasaydı geri yüklenen satır yedek günündeki sarmalın
  özetini taşırdı ve geri yüklemeden önce `guvenlik.json`'a konan (yedek gününde güncel olan) eski
  sarmal eski parolayla açılırdı. Çapanın özetleri yalnız çapanın bildiği en yeni meşru sarmalı
  açar; o sarmal dosyada yoksa hesap parolayla açılmaz (`digest_mismatch`);
* ÇAPA KULLANILAMIYORSA — okunamıyor (dosya yok, `sqlite3` hatası, okul kartı tek satır değil ya da
  parmak izi bu DEK'inki değil: `geri_yukleme_yetkisi` modül başlığındaki dört hâl), bayat ya da
  hesabın çapadaki satırının mührü veya izi bozuk ya da sıra kuralını tutmuyor — K-a (orkestratör
  kararı, b4; fail-closed):
  güncel `guvenlik.json`'daki o kimliğin sarmalının özeti geri yüklenen satırın asıl ya da bekleyen
  özetini tutuyorsa özetler kalır (DEĞİŞMEYEN); tutmuyorsa ya da dosyada o kimliğin sarmalı yoksa
  iki özet BOŞALTILIR ve satır yeniden mühürlenir (BOŞALTILAN). Meşru kullanıcıya bedeli yoktur
  (tutmayan sarmal zaten açmıyordu; çıkış parola sıfırlaması, program yöneticisinin kendi hesabıysa
  kurtarma anahtarıyla açılış); geri yüklemeden SONRA arşivden geri konacak yedek günü sarmalının
  yolu kapanır. Geri yükleyen program yöneticisi de buna dahildir: yedekten sonra parolasını
  değiştirdiyse ve çapa kullanılamıyorsa kurtarma anahtarıyla açar.

Böylece, ÖNCEKİ VERİTABANI SAĞLAM VE TAZE OLDUĞU SÜRECE, geri yüklemeden önce `guvenlik.json`'a
eski sarmal koyup geri yüklemeyle onu "aklama" yolu kapanır: aklanacak sarmalın özeti çapayı
tutmaz. Çapa kullanılamadığında yalnız güncel dosyada duran ve geri yüklenen satırı tutan sarmal
kalır. KALAN RİSK (`app_password` modül başlığı "KALAN RİSKLER" (c)): geri yüklemeden ÖNCE
`guvenlik.json`'a konmuş yedek günü sarmalı (çapayı okunamaz kılan ya da bir satırın mührünü bozan,
o günün parolasını bilen biri) geri yüklenen satırın özetini tutar ve o günün parolasıyla açar.
Çapayı okunamaz kılmak (`db.sqlite3`'ü silmek ya da adını değiştirmek) ya da bir satırın mührünü
bozmak kod istemez; olay geri yükleme kartıyla (`GERI_YUKLEME` satırı; mühür bozuksa ayrıca
`BUTUNLUK` kartıyla) ve onarımın `SISTEM` `HESAP` satırlarıyla görünür olur, kriptografik olarak
kapanmaz. Kapatılmış hesap da bu yoldan döner: kapanıştan önce saklanmış sarmal geri yüklemeden
ÖNCE dosyaya konur ve çapa kullanılamaz kılınırsa (dosyayı kaldırmak ya da o satırın mührünü
bozmak tek bir yazımdır), kapanıştan önceki yedekle hesap `ACIK` olarak eski parolayla açılır
("çapada `KAPALI` → boşalt" kuralı yalnız kullanılabilen çapada işler; K-a ve K-d korunur).

YAZIM YERİ: geri yüklenecek içerik önce yanına `.tmp` olarak yazılır; onarım o dosyada, TAKASTAN
ÖNCE yapılır ve commit edilir; ancak sonra `.tmp` veritabanının yerine konur
(`backup_restore._swap_database_files`). Onarım yazılamazsa (`sqlite3` yazım hatası, WAL dosyası
ana dosyaya aktarılamadı) geri yükleme yarıda kalır ve hiçbir dosya değişmez
(`OnarimYazilamadi`, bir `OSError`). Geri yüklenen veritabanında hesap tablosu ya da özet
sütunları okunamıyorsa (bu göçten önceki bir yedek) onarım atlanır ve uyarı günlüğe düşer. Göç
sütunları boş ekler; ama o satırların mührü özet alanları mühre girmeden hesaplanmıştır ve yeni
biçimle tutmaz: hiçbir hesap açılmaz, kurtarma anahtarıyla açılış dahil; parola sıfırlaması da
yapılamaz (fail-closed; plan F1b-1 "Eski veri": göç gerekmez, deneme kurulumları silinip
yeniden kurulur).

İZ (K-e; `satir_izi` modül başlığı "ONARIMIN İZİ"): değiştirilen her satır için AYNI `sqlite3`
işleminde, satırlar yazıldıktan sonra zincirin sonuna `SISTEM` `HESAP` satırı eklenir
(`satir_izi.hesap_satirlarini_izle`): açık kip, etkin iz anahtarı (DEK'le çözülür), içerik MAC'i
satırın onarılmış hâlinden, değişen alanların adları (`wrap_digest`, `wrap_digest_pending`, `seal`;
değer yok), anı geri yüklemenin anı. Satır `denetim_izi`'nin yazdığıyla birebirdir: ilk kilit
açılışı onarılan satırı reddetmez (satırın izi tutar); onarım denetim izinde `SISTEM` `HESAP`
satırı olarak kalır (değişen alan adlarıyla; izi okuma ekranı Denetleme Kurulu modülüyle F4'te
gelir); zincir doğrulaması bulgusuzdur. Etkin iz anahtarı çözülemez ya da zincir başı biçimsizse iz yazılamaz:
onarım da yapılmaz (`OnarimYazilamadi`; geri yükleme yarıda kalır, hiçbir dosya değişmez). Geri
yüklemenin kendisi ilk kilit açılışında `GERI_YUKLEME` satırıyla izlenir. Sonuç ayrıca sırsız
günlüğe yazılır: hesap kimlikleri (kişisiz) ve sayılar; tanıtıcı, özet ve mühür yazılmaz.

METİN: satırlar `surrogateescape` ile çözülür (`_metin`): geçersiz UTF-8'li satır kanonik
kodlamada reddedilir ve mühür tutmamış sayılır, bir satır bütün okumayı düşürmez. Geri yükleme
yetkisinin kuralından (`geri_yukleme_yetkisi._metin`: geçersiz metin `_GecersizMetin` olarak
çağırana çıkar) bilinçli olarak ayrılır: orada tek satırın kararı verilir, burada bütün satırlar
okunur.

Modül yalnız standart kitaplığın `sqlite3`'üne, `shared.kanonik`'e, `shared.crypto`'nun saf
işlevlerine, `geri_yukleme_yetkisi`'nin satır okuyucusuna ve `satir_izi`'nin ORM'siz okuyucusu ile
yazıcısına dayanır (Django ayarı, uygulama kaydı ve sorgusu gerekmez).
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from apps.okul.services import geri_yukleme_yetkisi as yetki
from apps.okul.services import satir_izi
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
#: Kullanılamayan çapada dosyadaki sarmalı tutmayan özetler boşaltılır (K-a; `bosaltilan`'a girer).
_KULLANILAMAYAN: Final = "kullanilamayan"

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
    #: Özetleri boşaltılan hesaplar (çapada satırı yok, çapada `KAPALI` ya da çapa kullanılamıyor
    #: ve güncel `guvenlik.json`'daki sarmal satırın özetlerini tutmuyor — K-a).
    bosaltilan: tuple[str, ...] = ()
    #: Geri yüklenen satırlar okunamadı: hiçbir satıra dokunulmadı.
    atlandi: bool = False
    #: Çapa okunamadı: özet verilmedi; dosyadaki sarmalı tutmayan özetler boşaltıldı (K-a).
    capa_okunamadi: bool = False
    #: Çapa geri yüklenen yedeğin zincir başını içermiyor: özet verilmedi, yalnız kısıtlandı.
    bayat: bool = False
    neden: str = ""
    degismeyen: tuple[str, ...] = field(default=())


@dataclass(frozen=True)
class _Capa:
    """Okunabilen çapa (modül başlığı)."""

    #: Mührü ve izi tutan satırlar: `{kanonik kimlik: (asıl özet, bekleyen özet, durum)}`.
    satirlar: dict[str, tuple[str, str, str]]
    #: Satırı olan ama mührü ya da izi tutmayan, taze çapada sıra kuralını tutmayan (ya da aynı
    #: kimliği iki kez taşıyan) hesaplar: çapa bu hesaplar için kullanılamaz (K-a).
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


def _izli_siralar(baglanti: sqlite3.Connection, satirlar: list[Any], dek: bytes) -> dict[str, int]:
    """Mührü ve İZİ tutan satırların kimlikleri → satırın eşleştiği iz satırının sırası (modül
    başlığı "SATIRIN İZİ" ve "SIRA KURALI"; `satir_izi.hesap_izi_sirasi`). Satırın izi, okunan
    mührüne bağlıdır (`beklenen_muhur`): mühür ve iz aynı satır hâlini anlatır."""
    izli: dict[str, int] = {}
    for satir in satirlar:
        kimlik = yetki.satir_kimligi(satir)
        if kimlik is None or not yetki.muhurlu_satir_mi(satir, dek):
            continue
        muhur = satir[yetki.SIRA_MUHUR]
        sira = satir_izi.hesap_izi_sirasi(
            baglanti, kimlik, dek, beklenen_muhur=muhur if isinstance(muhur, str) else None
        )
        if sira is not None:
            izli[kimlik] = sira
    return izli


def _yedegi_oku(
    yeni_db: Path, dek: bytes
) -> tuple[list[Any], tuple[int, str] | None, dict[str, int]] | str:
    """Geri yüklenecek dosyanın hesap satırları, zincir başı ve mührü ve izi tutan satırların
    kimlikleri (eşleştikleri iz sırasıyla); satırlar okunamıyorsa neden.

    Salt okunur açılır: değişecek satır yoksa geri yüklenecek dosyaya yazılmaz (baytları aynen
    kalır). Bütün okumalar tek okuma işlemindedir (`satir_izi.okuma_islemi`). Zincir başı
    okunamıyorsa (tablo yok) None: çapa bayat sayılır. İz tablosu okunamıyorsa satırlar okunamamış
    sayılır (onarım atlanır; izsiz yazılmaz).
    """
    try:
        with closing(
            sqlite3.connect(sqlite_adres.salt_okunur_adres(yeni_db), uri=True, timeout=5)
        ) as okuyucu:
            okuyucu.text_factory = _metin
            with satir_izi.okuma_islemi(okuyucu):
                satirlar = yetki.hesap_satirlari(okuyucu)
                try:
                    bas = _zincir_basi(okuyucu)
                except sqlite3.Error:
                    bas = None
                izli = _izli_siralar(okuyucu, satirlar, dek)
    except sqlite3.Error as exc:
        return _sqlite_nedeni(exc)
    return satirlar, bas, izli


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


def _capa_oku(
    onceki_db: Path,
    dek: bytes,
    yedek_basi: tuple[int, str] | None,
    yedek_siralari: Mapping[str, int],
) -> _Capa | str:
    """Çapa: önceki veritabanının satırları ve tazeliği; okunamıyorsa nedeni (metin) döner.

    Salt okunur açılır (`mode=ro`; adres `sqlite_adres`'ten, `geri_yukleme_yetkisi` ile aynı):
    kenara alınacak dosya değişmez. Bütün okumalar tek okuma işlemindedir. Kimliği çevrilemeyen
    satır hiçbir hesabı anlatmaz, atlanır. `yedek_siralari` geri yüklenen satırların eşleştiği iz
    sıralarıdır: taze çapada satırın eşleştiği sıra ondan küçükse çapa o hesap için kullanılamaz
    (modül başlığı "SIRA KURALI").
    """
    if not onceki_db.is_file():
        return yetki.OKUNAMAMA_DOSYA_YOK
    try:
        with closing(
            sqlite3.connect(sqlite_adres.salt_okunur_adres(onceki_db), uri=True, timeout=5)
        ) as baglanti:
            baglanti.text_factory = _metin
            with satir_izi.okuma_islemi(baglanti):
                neden = yetki.okul_karti_okunamaz_mi(baglanti, dek)
                if neden is not None:
                    return neden
                satirlar = yetki.hesap_satirlari(baglanti)
                taze = yedek_basi is not None and _basi_iceriyor_mu(baglanti, yedek_basi)
                izli = _izli_siralar(baglanti, satirlar, dek)
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
            or kimlik not in izli
            # Sıra kuralı: taze çapanın satırı geri yüklenen satırdan ESKİ bir iz kaydını
            # tutamaz (sahte tazelik: eski kopyaya eklenmiş baş satırı; modül başlığı).
            or (taze and kimlik in yedek_siralari and izli[kimlik] < yedek_siralari[kimlik])
        ):
            muhurlu.pop(kimlik, None)
            muhursuz.add(kimlik)
            continue
        durum = str(yetki.satirdan_muhur_alanlari(satir)["status"])
        muhurlu[kimlik] = (asil, bekleyen, durum)
    return _Capa(satirlar=muhurlu, muhursuz=frozenset(muhursuz), taze=taze)


def _hedef(
    capa: _Capa | None, kimlik: str, dosyadaki: str | None, satir: Any
) -> tuple[tuple[str, str], str] | None:
    """Geri yüklenen satırın özetleri ve onarımın türü; dokunulmayacaksa None (modül başlığı).

    `capa` None ise çapa okunamadı. Çağıran, geri yüklenen satırın mührünü doğrulamıştır.
    """
    if capa is not None and kimlik not in capa.muhursuz:
        capadaki = capa.satirlar.get(kimlik)
        if capadaki is None or capadaki[2] == DURUM_KAPALI:
            return ("", ""), _BOSALTILAN
        if capa.taze:
            asil, bekleyen, _durum = capadaki
            tutar = bool(dosyadaki) and (
                (bool(asil) and kanonik.esit(asil, dosyadaki))
                or (bool(bekleyen) and kanonik.esit(bekleyen, dosyadaki))
            )
            if tutar:
                return (str(dosyadaki), ""), _TASINAN
            return (asil, bekleyen), _CAPADAN
    # Kullanılamayan çapa (okunamıyor, bayat ya da hesabın çapadaki satırının mührü, izi ya da
    # sırası tutmuyor; K-a):
    # dosyadaki sarmal geri yüklenen satırın özetlerinden birini tutuyorsa özetler kalır,
    # tutmuyorsa ya da sarmal yoksa iki özet boşaltılır (fail-closed).
    if yetki.ozet_tutuyor_mu(satir, dosyadaki):
        return None
    return ("", ""), _KULLANILAMAYAN


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
    an: datetime | None = None,
) -> OnarimSonucu:
    """Geri yüklenecek `yeni_db`'deki (takastan önceki `.tmp`) hesap özetlerini onarır.

    `onceki_db` kenara alınacak (henüz yerinde duran) veritabanıdır — çapa; `sarmal_ozetleri`
    güncel `guvenlik.json`'daki sarmalların `{kanonik kimlik: özet}` sözlüğüdür (kurtarma
    başlığından yazılacak dosyada boştur). Değişen her satır için aynı işlemde `SISTEM` `HESAP`
    iz satırı yazılır (`satir_izi.hesap_satirlarini_izle`; anı `an`, verilmezse şimdi). Kurallar
    modül başlığındadır. Yazım hatasında `OnarimYazilamadi`.
    """
    yedek = _yedegi_oku(yeni_db, dek)
    if isinstance(yedek, str):
        logger.warning(
            "Geri yüklemede parola kaydı özetleri onarılmadı: geri yüklenen veritabanının hesap "
            "satırları okunamadı (neden: %s).",
            yedek,
        )
        _yan_dosyalari_temizle(yeni_db)
        return OnarimSonucu(atlandi=True, neden=yedek)
    satirlar, yedek_basi, izli = yedek
    okunan = _capa_oku(onceki_db, dek, yedek_basi, izli)
    capa = None if isinstance(okunan, str) else okunan
    if capa is None:
        logger.warning(
            "Geri yüklemede önceki veritabanı okunamadı (neden: %s); çapa kullanılamıyor: güncel "
            "güvenlik dosyasındaki parola kaydını tutmayan özetler boşaltılır.",
            okunan,
        )
    elif not capa.taze:
        logger.warning(
            "Önceki veritabanı geri yüklenen yedeğin zincir başını içermiyor (bayat çapa: eski "
            "bir kopya ya da önceki bir geri yüklemenin veritabanı); özet taşınmaz, çapada "
            "olmayan ve kapalı hesapların ve güncel parola kaydını tutmayan özetler boşaltılır."
        )
    guncellemeler: list[tuple[str, str, str, Any]] = []
    degisenler: dict[str, list[str]] = {}
    turler: dict[str, list[str]] = {_TASINAN: [], _CAPADAN: [], _BOSALTILAN: []}
    degismeyen: list[str] = []
    anahtar = crypto.account_seal_key(dek)
    for satir in satirlar:
        kimlik = yetki.satir_kimligi(satir)
        if kimlik is None or kimlik not in izli:
            # Mührü ya da izi tutmayan satıra dokunulmaz: yeniden mühürleyip iz satırı yazmak
            # program dışından değiştirilmiş (eski bir kopyadan geri konmuş) satırı aklardı.
            continue
        hedef = _hedef(capa, kimlik, sarmal_ozetleri.get(kimlik), satir)
        if hedef is None or (satir[yetki.SIRA_OZET], satir[yetki.SIRA_BEKLEYEN]) == hedef[0]:
            degismeyen.append(kimlik)
            continue
        (asil, bekleyen), tur = hedef
        alanlar = {
            **yetki.satirdan_muhur_alanlari(satir),
            "wrap_digest": asil,
            "wrap_digest_pending": bekleyen,
        }
        muhur = kanonik.hesap_muhru(anahtar, alanlar)
        guncellemeler.append((asil, bekleyen, muhur, satir[yetki.SIRA_KIMLIK]))
        once = (satir[yetki.SIRA_OZET], satir[yetki.SIRA_BEKLEYEN], satir[yetki.SIRA_MUHUR])
        degisenler[kimlik] = [
            ad
            for ad, eski, yeni in zip(
                satir_izi.ONARIM_ALANLARI, once, (asil, bekleyen, muhur), strict=True
            )
            if eski != yeni
        ]
        turler[_BOSALTILAN if tur == _KULLANILAMAYAN else tur].append(kimlik)
    if guncellemeler:
        try:
            with closing(sqlite3.connect(yeni_db, timeout=5)) as yazici:
                yazici.executemany(
                    "UPDATE okul_account SET wrap_digest = ?, wrap_digest_pending = ?, seal = ? "
                    "WHERE id = ?",
                    guncellemeler,
                )
                # Onarımın izi (modül başlığı "İZ"): aynı işlemde, satırlar yazıldıktan sonra.
                satir_izi.hesap_satirlarini_izle(
                    yazici, degisenler, dek, an=an if an is not None else datetime.now(UTC)
                )
                yazici.commit()
        except sqlite3.Error as exc:
            raise OnarimYazilamadi(_sqlite_nedeni(exc)) from exc
        except satir_izi.IzYazilamadi as exc:
            raise OnarimYazilamadi(str(exc)) from exc
    _yan_dosyalari_temizle(yeni_db)
    sonuc = OnarimSonucu(
        tasinan=tuple(sorted(turler[_TASINAN])),
        capadan=tuple(sorted(turler[_CAPADAN])),
        bosaltilan=tuple(sorted(turler[_BOSALTILAN])),
        capa_okunamadi=capa is None,
        bayat=capa is not None and not capa.taze,
        neden=str(okunan) if capa is None else ("" if capa.taze else NEDEN_BAYAT),
        degismeyen=tuple(sorted(degismeyen)),
    )
    if guncellemeler:
        logger.info(
            "Geri yüklemede parola kaydı özetleri onarıldı ve denetim izine yazıldı: %d hesap "
            "güncel güvenlik dosyasına (%s), %d hesap önceki veritabanına göre (%s), %d hesabın "
            "özeti boşaltıldı (%s).",
            len(sonuc.tasinan),
            ", ".join(sonuc.tasinan) or "-",
            len(sonuc.capadan),
            ", ".join(sonuc.capadan) or "-",
            len(sonuc.bosaltilan),
            ", ".join(sonuc.bosaltilan) or "-",
        )
    return sonuc
