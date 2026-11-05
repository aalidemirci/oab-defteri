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
anahtar, parmak izi), `shared.sqlite_adres`'e (salt okunur adres) ve satırın izinin ORM'siz karar
işlevine (`satir_izi`; kilit açılışıyla AYNI işlev) dayanır; Django ayarı, uygulama kaydı ve sorgusu
gerekmez.
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
* satır denetim izindeki son içerik MAC'li kaydını tutar ve o kayıttan sonra izde boşluk yoktur
  (kullanıcı kararları 03.11.2026 "Girişte reddet", "Boşluğu engelle";
  `satir_izi.hesap_izi_tutuyor`, aynı salt okunur bağlantıda): eski bir kopyadan geri konmuş satır
  mührü ve özeti tutsa da reddedilir (`RET_KAYIT_IZI`, ileti mührünkü); izdeki boşlukta ret
  `RET_IZ_BOSLUGU`, ileti kendisinindir (`ILETI_IZ_BOSLUGU`; orkestratör maddesi C-4);
* durumu `ACIK` ya da `PAROLA_YENILENMELI`dir (`ASKIDA`, `KAPALI` ret);
* parolanın açtığı sarmalın özeti satırın asıl ya da bekleyen özetini tutar (`wrap_digest`,
  `wrap_digest_pending`; kullanıcı kararı 03.11.2026 "tazelik kapatılır", `app_password` modül
  başlığı "SARMALIN TAZELİĞİ"); tutmazsa `RET_OZET`;
* güvenlik dosyasındaki sarmalında hatalı deneme askısı (`askida`) yoktur.

Sıra: mühür (tutmuyorsa öteki değerlere güvenilmez), satırın izi (tutmuyorsa satır eski bir
kopyadır: rolüne ve durumuna da güvenilmez — eski kopya, rolü askıyla düşürülmüş bir program
yöneticisinin askıdan önceki hâlini taşıyabilir), rol, durum, özet. Özet rolden SONRADIR: program
yöneticisi olmayan hesabın iletisi rolünkidir (geri yüklemeyi zaten yapamaz); özet ancak öteki
koşulları tutan program yöneticisini ayırır. Kilit açılışında özet durumdan ÖNCEDİR ve `BUTUNLUK`
satırı düşer; burada ORM yoktur, iz yazılmaz, ret günlüğe düşer. İzi tutmayan satır OKUNAMAMA
DEĞİLDİR, RETTİR (görüntüye düşülmez); iz tablosu ya da iz anahtarı tablosu okunamıyorsa (`sqlite3`
hatası) dört hâlden biridir.

Geçici ya da 180 günü dolmuş parola engel DEĞİLDİR: konsolda parola yenileme adımı yoktur,
yenileme geri yüklemeden sonraki ilk girişte istenir; geçici parolayı başka bir program
yöneticisi vermiştir, yetki genişlemez.

Satır, Django'nun SQLite'a yazdığı biçimden mühür sözleşmesinin biçimine çevrilir
(`satirdan_muhur_alanlari`; `Account.seal_fields()` ile aynı sözlük): kimlik tiresiz 32 hane
→ tireli UUID metni; zaman saat dilimsiz UTC metni (`2026-11-02 07:30:00[.ffffff]`; ayarlarda
veritabanı saat dilimi verilmediği için bağlantı saat dilimi UTC'dir) → saat dilimli UTC
`datetime`; `person`, `membership`, `term` F1c'ye dek `None`dır; sarmal özetleri metindir (`NULL`
ya da metin olmayan değer mühür tutmamış sayılır). Çevrilmezse her mühür tutmuyor
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

GÜNCEL VERİTABANI OKUNAMIYORSA VE PAROLA YEDEKTEN SONRA DEĞİŞTİYSE görüntüdeki satırın özeti
yedeğin alındığı günün sarmalınındır ve güncel dosyadaki sarmalı tutmaz: parola yolu reddedilir
(`RET_OZET`), ileti kurtarma anahtarı yolunu anar (zarfın üçüncü durumu: güvenlik dosyası ya da
kayıtlar kaybolduğunda, bozulduğunda ya da program dışından değiştirildiğinde). Kurtarma anahtarı
yolunda rol ve özet denetimi yoktur.

Rol kriptografik bir önlem değildir (tasarım §4.4.6-1). **Sarmal kimliği parola kaydına
bağlıdır (kullanıcı kararı 02.11.2026):** denetlenen hesap, parolanın açtığı SARMALIN `id`
alanıdır ve sarmalın anahtarı bu kimliğe bağlıdır: `HKDF(Argon2id(parola, tuz),
"od-hesap-sarmali/v1" ‖ kanonik kimlik)` (`shared.crypto.account_wrapping_key`). Bir hesabın
parolasını bilen biri `guvenlik.json`'da kendi sarmalının `id`'sini metin düzenleyiciyle program
yöneticisininkine çevirirse sarmal o kimlikle açılmaz: geri yükleme yanlış parolanın yanıtıyla
("Yedek açılamadı …") durur, bu denetime hiç ulaşılmaz ve hiçbir dosya değişmez; kilit açılışı
da aynı nedenle açılmaz (`app_password` modül başlığı "HESAP SARMALI KİMLİĞE BAĞLIDIR").
Tanıtıcıyı değiştirmek de yetki yükseltmez: tanıtıcı yalnız sarmalı BULMAYA yarar, denetlenen
kimlik açılan sarmalın kendi `id`'sidir (parolası bilinen hesabın kendisi). Bağdan önceki biçimde
yazılmış (`turetim` alanı olmayan) sarmal parolayla hiç açılmaz; geri düşüş yoktur. Kalan risk
(tehdit 6, 19): parolasını bildiği hesabın DEK'ini program dışında türetip başka bir kimlikle
yeniden sarmalayan ya da bu DEK'le mühürlü sahte bir yönetici satırı taşıyan veritabanı üreten
biri geçer — bu artık KOD ister (tasarımın tehdit 19 çıtası). **Sarmalın tazeliği de mühürlü
satıra bağlıdır (kullanıcı kararı 03.11.2026):** bir program yöneticisinin eski ya da geçici
parolasını bilen ve veri dizinine yazabilen biri o hesabın eski sarmalını
(`guvenlik-arsiv-*.json`'dan ya da önceden aldığı kopyadan) geri koyarsa sarmal açılır ama özeti
satırınkini tutmaz: geri yükleme `RET_OZET` ile durur, hiçbir dosya değişmez. **Satır da son iz kaydına bağlıdır (kullanıcı kararı 03.11.2026 "Girişte reddet"):** satırın
kendisinin eski bir kopyadan geri konması (rolü askıyla düşürülmüş program yöneticisinin askıdan
önceki satırı, sıfırlamadan sonra kopyalanmış satır) mühür ve özet tutsa da `RET_KAYIT_IZI` ile
durur (eski satırın iz sırasını BLOB'a çevirmek de geçmez: `satir_izi` adım 2). Hesabın yeni iz
satırlarını izin ARASINDAN SİLMEK (kuyruk değil), silinenden sonrakileri aşağı KAYDIRMAK (silinen
bölgeden sonra açık kipte, `BUTUNLUK` dışı bir satır kaldıysa ve o dayanak satırı bozulmadıysa;
iz anahtarı tablosuna eklenen sahte bir anahtar bunu örtmez) ya da bir satırı REAL bir sıraya
taşımak da geçmez (kullanıcı kararı 03.11.2026 "Boşluğu engelle"; `satir_izi` "İZ BOŞLUĞU", aynı
tek işlev): izinde boşluk olan güncel veritabanında ret `RET_IZ_BOSLUGU`'dur, görüntüye düşülmez;
izde ilgisiz bir satır silinmişse de son kaydı ondan eski program yöneticisi parolayla geri
yükleyemez (çıkış kurtarma anahtarı yoludur). Kalan risk (`app_password` modül başlığı "KALAN
RİSKLER" (b); liste orada ve `satir_izi` modül başlığı "KAPSAMIN SINIRI"nda aynıdır):
veritabanının iziyle BİRLİKTE eski bir kopyayla değiştirilmesi; iz kuyruğunun satırla birlikte
kesilmesi (açık kip satırların zincir başına dek silinip kalan girişsiz satırların — kilitli kip,
`BUTUNLUK` — aşağı kaydırılması dahil); hesabın yeni iz satırlarının silinmeden başka bir kayda
çevrilmesi ya da değiştirilmesi, iki satırın tamsayı sırayla yer değiştirmesi, hesabın yeni
satırının S'nin gerisinde boş bir tamsayıya taşınması, silinen satırın yerine başka bir satırın ya
da kopyasının (boşluğun sırasıyla) konması; dayanağı da bozan (tek hücre yeter) ya da zincir
başına sahte bir açık kip satırı ekleyen (tek INSERT), on binden büyük ya da oturum açıkken yapılan
kaydırma (askıya alınmış ya da kapatılmış bir program yöneticisinin
geri sarılmış satırı böyle geçer; satırların kendi MAC'i bozulur, burada doğrulanmaz) ve görüntüye
düşüşte görüntünün yedek günündeki satırı — yedek günündeki sarmalı geri koyan, o günün parolasını
bilen biri görüntüye düşürülmüş bir veritabanıyla geri yükler (görüntünün satırı görüntünün kendi
izini tutar). Bu denetim kaza önleyicidir ve izlenebilirlik sağlar; GA-3'ü kriptografik olarak
kapatmaz.

YEDEĞİN GÖRÜNTÜSÜ BELLEKTE açılır: `sqlite3.connect(":memory:")` + `deserialize`. Programın
yedeği WAL kipindeki kaynaktan `Connection.backup()` ile alındığı için görüntünün başlığı WAL
işaretlidir (18-19. baytlar 2); `deserialize` böyle görüntüyü açmaz ("unable to open database
file"). Bu yüzden görüntünün BELLEKTEKİ kopyasında iki bayt 1'e çekilir (geri yükleme ise
görüntünün kendisini aynen yazar). Görüntü yalnız veritabanı baytlarıdır: kabın manifestosunu ve
dosya bölümünü `backup_crypto` ayırır, buraya gelmezler (plan F1b-2 ekleri; çağıran
`backup_restore._yetkiyi_denetle`).

**Tasarımın "bellekte" lafzından sapma (F1b-2 ekleri):** `deserialize` olmayan SQLite'ta
(< 3.36; Pardus 21'in 3.34'ü) görüntü, veri dizini altında 0700 izinli bir geçici dizine
yazılır, salt okunur açılır ve okunur okunmaz (hata yolunda da) silinir. Aile emsali
`desktop/backup.py::goruntu_ve_manifesto`'dur (aynı platform için aynı kısa temas bilerek kabul
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

from apps.okul.services import satir_izi
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
#: Hesabın son kaydından sonra denetim izinde boşluk var (`satir_izi` "İZ BOŞLUĞU", "RET NEDENİ";
#: orkestratör maddesi C-4): değişen hesap kaydı değil denetim izidir; parola yolu her eski hesapta
#: aynı boşluğu görür, çıkış değişiklikten önceki yedeğin kurtarma anahtarıyla geri yüklenmesidir.
ILETI_IZ_BOSLUGU: Final = (
    "Denetim izinden kayıt silinmiş ya da kayıtların sırası program dışından değiştirilmiş "
    "görünüyor; geri yükleme yapılmadı. Yedeği kurtarma anahtarıyla geri yükleyin ve Denetleme "
    "Kuruluna bildirin."
)
#: Parola kaydının özeti satırınkini tutmuyor (eski ya da program dışından konmuş sarmal; görüntüye
#: düşüşte yedekten sonra değişmiş parola). Çıkış kurtarma anahtarı yoludur (zarfın üçüncü durumu).
ILETI_OZET: Final = (
    "Bu hesabın parola kaydı kayıtlardakiyle uyuşmuyor; geri yükleme yapılmadı. Güvenlik "
    "dosyası ya da kayıtlar bozulduysa ya da program dışından değiştirildiyse yedeği kurtarma "
    "anahtarıyla geri yükleyin ve Denetleme Kuruluna bildirin."
)

#: Ret nedenleri (günlüğe ve teste; kullanıcı metnine çıkmaz) → ileti.
RET_SATIR_YOK: Final = "satir_yok"
RET_MUHUR: Final = "muhur"
RET_ROL: Final = "rol"
RET_DURUM: Final = "durum"
RET_ASKIDA: Final = "askida"
RET_OKUNAMADI: Final = "okunamadi"
RET_OZET: Final = "ozet"
#: Satır denetim izindeki son içerik MAC'li kaydını tutmuyor (eski bir kopyadan geri konmuş satır;
#: `satir_izi`). İleti mührünküdür (kullanıcı kararı 03.11.2026: mühür uyuşmazlığıyla aynı muamele).
RET_KAYIT_IZI: Final = "kayit_izi"
#: Eşleşen satırdan sonra izde boşluk (silme, tür, kayma); ileti kendisinindir (`ILETI_IZ_BOSLUGU`).
RET_IZ_BOSLUGU: Final = "iz_boslugu"
_ILETILER: Final[dict[str, str]] = {
    RET_SATIR_YOK: ILETI_ROL,
    RET_OKUNAMADI: ILETI_ROL,
    RET_ROL: ILETI_ROL,
    RET_MUHUR: ILETI_MUHUR,
    RET_KAYIT_IZI: ILETI_MUHUR,
    RET_IZ_BOSLUGU: ILETI_IZ_BOSLUGU,
    RET_DURUM: ILETI_DURUM,
    RET_ASKIDA: ILETI_DURUM,
    RET_OZET: ILETI_OZET,
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
    *,
    db_path: Path,
    goruntu: bytes,
    dek: bytes,
    hesap_id: object,
    askida: bool,
    sarmal_ozeti: str | None,
) -> str:
    """Hesabı program yöneticisi olarak doğrular; kararı veren kaynağı döndürür.

    Önce güncel veritabanı (`db_path`) okunur; okunamıyorsa (modül başlığındaki dört hâl)
    yedeğin görüntüsü (`goruntu`, çözülmüş veritabanı baytları). `hesap_id` parolası doğrulanan
    sarmalın kimliğidir, `askida` o sarmalın hatalı deneme askısı, `sarmal_ozeti` o sarmalın DEK'li
    özeti (`crypto.account_wrap_digest`; biçimsiz sarmalda None — hiçbir özeti tutmaz). Kabulde
    `KAYNAK_GUNCEL` ya da `KAYNAK_GORUNTU`; aksi hâlde `YetkiReddi`. Hiçbir dosyaya yazmaz.
    """
    anahtar = _hesap_anahtari(hesap_id)
    kaynak = KAYNAK_GUNCEL
    karar = _guncel_karari(db_path, dek, anahtar, sarmal_ozeti)
    if isinstance(karar, _Okunamaz):
        logger.warning(
            "Güncel veritabanı okunamadı (neden: %s); hesap yedeğin görüntüsünde denetleniyor.",
            karar.neden,
        )
        kaynak = KAYNAK_GORUNTU
        karar = _goruntu_karari(db_path.parent, goruntu, dek, anahtar, sarmal_ozeti)
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
    kimlik, tanitici, rol, durum, acilis, kapanis, ozet, bekleyen, _muhur = satir
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
        "wrap_digest": ozet,
        "wrap_digest_pending": bekleyen,
    }


#: `hesap_satiri`'nın sütun sırası: mühre giren sütunlar, sarmal özetleri, mühür.
HESAP_SATIRI_SUTUNLARI: Final = (
    "id",
    "login_name",
    "role",
    "status",
    "opened_at",
    "closed_at",
    "wrap_digest",
    "wrap_digest_pending",
    "seal",
)
#: Satırdaki yerler (`satirdan_muhur_alanlari` sırayı açar).
SIRA_KIMLIK: Final = 0
_SIRA_ROL: Final = 2
_SIRA_DURUM: Final = 3
SIRA_OZET: Final = 6
SIRA_BEKLEYEN: Final = 7
SIRA_MUHUR: Final = 8


def hesap_satiri(baglanti: sqlite3.Connection, anahtar: str) -> Any:
    """Hesabın mühre giren sütunları, sarmal özetleri ve mührü (`HESAP_SATIRI_SUTUNLARI`).

    `anahtar` SQLite'taki kimliktir (tiresiz 32 hane); satır yoksa None. Sorgu kaynakta sabit
    bir `SELECT`'tir (izsiz yazım taraması salt okuma sayar).
    """
    return baglanti.execute(
        "SELECT id, login_name, role, status, opened_at, closed_at, wrap_digest, "
        "wrap_digest_pending, seal FROM okul_account WHERE id = ?",
        (anahtar,),
    ).fetchone()


def hesap_satirlari(baglanti: sqlite3.Connection) -> list[Any]:
    """Bütün hesap satırları, `hesap_satiri` sırasıyla (geri yüklemenin özet onarımı okur)."""
    return baglanti.execute(
        "SELECT id, login_name, role, status, opened_at, closed_at, wrap_digest, "
        "wrap_digest_pending, seal FROM okul_account"
    ).fetchall()


def muhurlu_satir_mi(satir: Sequence[Any], dek: bytes) -> bool:
    """Satırın mührü bu DEK'le tutuyor mu? Çevrilemeyen satır tutmaz (hata yükseltmez)."""
    muhur = satir[SIRA_MUHUR]
    try:
        beklenen = kanonik.hesap_muhru(crypto.account_seal_key(dek), satirdan_muhur_alanlari(satir))
    except (TypeError, ValueError):  # KanonikHata bir TypeError'dır
        return False
    return bool(muhur) and kanonik.esit(muhur, beklenen)


def satir_kimligi(satir: Sequence[Any]) -> str | None:
    """Satırın (`hesap_satiri` sırası) kanonik kimliği; yalnız kimlik sütunundan, öteki sütunlar
    biçimsiz olsa da (geri yüklemenin özet onarımı okur). Çevrilemezse None."""
    try:
        return _kimlik(satir[SIRA_KIMLIK])
    except (TypeError, ValueError):
        return None


def ozet_tutuyor_mu(satir: Sequence[Any], sarmal_ozeti: str | None) -> bool:
    """Sarmalın özeti satırın asıl ya da bekleyen özetini SABİT SÜREDE tutuyor mu? Boş alan hiçbir
    özeti tutmaz (`app_password._digest_slot` ile aynı kural; çağıran mührü doğrulamıştır)."""
    if not sarmal_ozeti:
        return False
    asil = satir[SIRA_OZET]
    bekleyen = satir[SIRA_BEKLEYEN]
    tutar_asil = bool(asil) and kanonik.esit(asil, sarmal_ozeti)
    tutar_bekleyen = bool(bekleyen) and kanonik.esit(bekleyen, sarmal_ozeti)
    return tutar_asil or tutar_bekleyen


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


def okul_karti_okunamaz_mi(baglanti: sqlite3.Connection, dek: bytes) -> str | None:
    """Okul kartı tek satır ve parmak izi bu DEK'inki değilse okunamamanın nedeni; öyleyse None.

    Modül başlığındaki okunamama hâllerinden ikisi (dosya yok ve `sqlite3` hatası çağıranındır).
    `sqlite3.Error` yükseltebilir; çağıran onu okunamama sayar.
    """
    try:
        kartlar = baglanti.execute("SELECT app_password_hash FROM okul_schoolconfig LIMIT 2")
        parmak_izleri = kartlar.fetchall()
    except _GecersizMetin:
        # Okunamayan parmak izi bu DEK'inkine eşit değildir.
        return OKUNAMAMA_PARMAK_IZI
    if len(parmak_izleri) != 1:
        return OKUNAMAMA_OKUL_KARTI
    if not kanonik.esit(parmak_izleri[0][0], crypto.key_fingerprint(dek)):
        return OKUNAMAMA_PARMAK_IZI
    return None


def _karar(
    baglanti: sqlite3.Connection, dek: bytes, anahtar: str | None, sarmal_ozeti: str | None
) -> object:
    """Tek kaynağın kararı: None (kabul), ret kodu ya da `_Okunamaz`.

    `sqlite3.Error` yükseltebilir; çağıran onu okunamama sayar.
    """
    neden = okul_karti_okunamaz_mi(baglanti, dek)
    if neden is not None:
        return _Okunamaz(neden)
    if anahtar is None:
        return RET_SATIR_YOK
    try:
        satir = hesap_satiri(baglanti, anahtar)
    except _GecersizMetin:
        return RET_MUHUR
    if satir is None:
        return RET_SATIR_YOK
    return _satir_karari(baglanti, satir, dek, sarmal_ozeti)


def _satir_karari(
    baglanti: sqlite3.Connection, satir: Sequence[Any], dek: bytes, sarmal_ozeti: str | None
) -> str | None:
    """Mühür (önce: tutmuyorsa öteki değerlere güvenilmez), satırın izi (tutmuyorsa satır eski bir
    kopyadır, rolüne ve durumuna güvenilmez), rol, durum, sarmal özeti (modül başlığı)."""
    if not muhurlu_satir_mi(satir, dek):
        return RET_MUHUR
    # Satırın izi okunan mühre bağlıdır (`satir_izi` adım 5): kararın satırı izi doğrulanan satırdır.
    # Retin nedeni iletiyi seçer (`satir_izi` "RET NEDENİ"): izdeki boşluk kendi iletisini alır.
    karar = satir_izi.hesap_izi_karari(
        baglanti, satir_kimligi(satir), dek, beklenen_muhur=satir[SIRA_MUHUR]
    )
    if not karar.tutuyor:
        bosluk = karar.neden is not None and karar.neden.bosluk_mu
        return RET_IZ_BOSLUGU if bosluk else RET_KAYIT_IZI
    if satir[_SIRA_ROL] != ROL_YONETICI:
        return RET_ROL
    if satir[_SIRA_DURUM] not in GIRIS_DURUMLARI:
        return RET_DURUM
    if not ozet_tutuyor_mu(satir, sarmal_ozeti):
        return RET_OZET
    return None


def _guncel_karari(
    db_path: Path, dek: bytes, anahtar: str | None, sarmal_ozeti: str | None
) -> object:
    """Güncel veritabanının kararı; dosya yoksa ya da `sqlite3` hatasında `_Okunamaz`."""
    if not db_path.is_file():
        return _Okunamaz(OKUNAMAMA_DOSYA_YOK)
    adres = sqlite_adres.salt_okunur_adres(db_path)
    try:
        with closing(sqlite3.connect(adres, uri=True, timeout=5)) as baglanti:
            # Kart, satır ve satırın izi TEK anlık görüntüden (`satir_izi.okuma_islemi`).
            with satir_izi.okuma_islemi(baglanti):
                return _karar(_baglanti_hazirla(baglanti), dek, anahtar, sarmal_ozeti)
    except sqlite3.Error as exc:
        return _sqlite_hatasi(exc)


def _goruntu_karari(
    dizin: Path, goruntu: bytes, dek: bytes, anahtar: str | None, sarmal_ozeti: str | None
) -> object:
    """Yedeğin görüntüsünün kararı (bellekte; `deserialize` yoksa geçici dizinde)."""
    try:
        with (
            _goruntu_baglantisi(dizin, wal_basligini_yama(goruntu)) as baglanti,
            satir_izi.okuma_islemi(baglanti),
        ):
            return _karar(_baglanti_hazirla(baglanti), dek, anahtar, sarmal_ozeti)
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
