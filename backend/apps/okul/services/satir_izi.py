"""Hesap satırının izi — ORM'SİZ okuyucu ve geri yükleme onarımının yazıcısı (kullanıcı kararı
03.11.2026 "Girişte reddet").

SORUN. Hesabın `Account` satırı DEK'le mühürlüdür (tasarım §4.6.1) ve güncel parola kaydının
özetini taşır (`app_password` modül başlığı "SARMALIN TAZELİĞİ"). Mühür satırın BİR ZAMANLAR
program tarafından yazıldığını kanıtlar, BUGÜNKÜ hâli olduğunu kanıtlamaz: veritabanına yazabilen
biri (okulda tek bilgisayar; bir SQLite tarayıcısı yeter, kod gerekmez) satırı mührüyle birlikte
eski bir düz kopyadan (kendi aldığı `db.sqlite3` kopyası ya da `db-onceki-*`) geri koyarsa mühür
tutar, özet o günün sarmalını anlatır ve arşivden geri konan o günün sarmalı o günün parolasıyla
açılırdı (Senaryo 1: geçici parolayla sıfırlanan muhasibin satırı, sahibi parolasını yeniledikten
sonra geri sarılır; rolü düşürülmüş ya da kapatılmış hesabın eski hâli de aynı yoldan döner).

KURAL. Satır denetim izindeki SON içerik MAC'li kaydını tutmalıdır (tasarım §4.6.2 "içerik MAC'i";
`denetim_izi.kaydi_dogrula`'nın mantığı): her meşru `Account` yazımı aynı işlemde satırın SON
hâlinin içerik MAC'ini taşıyan bir iz satırı yazar; eski bir kopyadan geri konan satır, ondan sonra
yazılmış iz satırını tutmaz. Tutmazsa satır mühür uyuşmazlığıyla AYNI muameleyi görür (giriş, oturum
işlemi, kurtarma ve hesap işlemi açılmaz; `app_password.AccountRecordStale`, 409
`hesap_muhru_tutmadi`; `BUTUNLUK` satırının alanı `kayit_mac`; geri yüklemenin parola yolunda
`geri_yukleme_yetkisi.RET_KAYIT_IZI`). Çıkış yedekten geri yüklemedir (zarfın üçüncü durumu).

`hesap_izi_tutuyor` (gövdesi `hesap_izi_sirasi`; eşleşen iz satırının sırasını da verir) TEK karar
işlevidir: kilit açılışında (DEK belleğe alınmadan, aday DEK'le), oturumdaki parola doğrulamasında,
hesap servislerinde (`denetim_izi.hesap_izi_tutuyor` Django'nun bağlantısını verir), geri
yüklemenin parola yolunda (`geri_yukleme_yetkisi`; salt okunur `sqlite3`) ve özet onarımında
(`ozet_onarimi`) AYNI işlev koşar. Adımları:

1. Satırın içerik MAC'ine giren alanlar (`HESAP_OZET_ALANLARI`; `Account.IZ_OZET_ALANLARI` ile
   birebir, altın listeyle sabit) ham sütunlardan okunur ve ORM'in verdiği değerlere çevrilir
   (`hesap_ozet_alanlari`): ad-soyad verilen DEK'le çözülür (çözülemezse `kanonik.bozuk_alan`,
   ORM'in `CorruptField`'ı gibi), zaman saat dilimli UTC, yabancı anahtar tireli kimlik metni,
   bildirim bayrağı `bool`. Sütunlar `CAST(… AS BLOB)` ile okunur: Django bağlantısının sütun
   türü dönüştürücüleri (`detect_types`) ve metin fabrikası devreye girmez; iki bağlantı aynı
   baytları görür. Biçimsiz değer (geçersiz UTF-8, çözülemeyen zaman, 0/1 dışı bayrak) satırı
   tutmaz sayar (fail-closed).
2. Hesabın iz satırları (`model = "okul.Account"`, `object_id` = kanonik kimlik) EN YENİDEN
   geriye okunur. Okunan HER satırın sırası SQLite'ta tamsayı türünde olmalı, satır açık kipte
   olmalı ve kendi zincir MAC'i, `key_ref`'teki iz anahtarıyla (DEK'le çözülür) tutmalıdır; o
   anahtar satırın sırasında YÜRÜRLÜKTEKİ anahtar olmalıdır (geçerli ilk sırası satırınkine eşit
   ya da küçük olanların en yenisi; `denetim_izi.sirayi_muhurleyen_ia`'nın kuralı). Tutmayan satır
   karşılaştırmayı DÜŞÜRÜR (fail-closed). Böylece son satırın `record_mac`'ini boşaltmak,
   `key_ref`'ini başka bir `AuditKey`'e çevirmek ya da kipini değiştirmek denetimi daha eski bir
   satıra kaydıramaz: o satırın kendi MAC'i bozulur; DEK yenilemesinden (F4) kalan eski bir İA'yı
   bilen biri de satırı o anahtarla yeniden mühürleyemez (yürürlükteki anahtar o değildir).
   TÜR ŞARTI (bağımsız denetim bulgusu): `seq` sütunu `bigint unsigned PRIMARY KEY`'dir, rowid
   takma adı değildir; program dışından BLOB ya da metin değer saklayabilir ve SQLite'ın
   sıralamasında BLOB ve metin bütün tamsayılardan BÜYÜKTÜR. Eski eşleşen satırın sırası BLOB'a
   çevrilseydi (`CAST(seq AS BLOB)` aynı baytları, dolayısıyla aynı zincir MAC'ini verir) o satır
   "en yeni" okunur, hesabın yeni satırları hiç okunmazdı. Bu yüzden her satırın `typeof(seq)`'i
   okunur, tamsayı olmayan ilk satırda karar "tutmuyor"dur (sorguya tür süzgeci KONMAZ: süzgeç yeni
   satırları BLOB'a çevirip gizlemenin yolu olurdu; tamsayı olmayan değerler üstte sıralandığı için
   önce onlar okunur). Aynı şart iz anahtarı satırlarının `valid_from_seq`'i için de geçerlidir:
   biçimsiz bir anahtar satırı varsa hiçbir hesabın izi doğrulanamaz.
3. İçerik MAC'i boş satır (kilitlenmenin `KILIT`'i, mühür bulgusunun `BUTUNLUK`'u) atlanır; ilk
   içerik MAC'li satır KARŞILAŞTIRMANIN satırıdır: `record_mac`, satırın bugünkü alanlarının o
   satırı mühürleyen İA ile hesaplanan içerik MAC'ine sabit sürede eşit olmalıdır.
4. Hesabın içerik MAC'li iz satırı HİÇ yoksa satır tutmaz (fail-closed). Meşru hiçbir hâl böyle
   doğmaz: ilk hesap (`enable`) ve her yeni hesap (`hesaplar.open_account`) satırla aynı işlemde
   `HESAP` satırını yazar; geri yüklenen veritabanı kendi izini taşır, onarımın değiştirdiği
   satırlar kendi satırını alır (aşağıda). İz anahtarı ya da iz tablosu okunamıyorsa da satır
   doğrulanamaz: veritabanı hatası çağırana yükselir (geri yükleme yetkisinde "okunamıyor"dur).
5. Çağıran satırı kendisi okuyup ona göre karar veriyorsa (ORM'li denetim noktaları, geri
   yüklemenin satır okuyucusu) okuduğu mührü `beklenen_muhur` olarak verir: ham okumadaki mühür ona
   sabit sürede eşit değilse satır tutmaz sayılır. Mühür kararın bütün alanlarını (rol, durum,
   özetler) kapsadığı için böylece çağıranın kararı verdiği hâl ile izi doğrulanan hâl AYNI hâldir
   (iki okuma arasında satırı değiştiren biri denetimi bir hâlde, kararı öbür hâlde geçiremez).

TEK ANLIK GÖRÜNTÜ (`okuma_islemi`; bağımsız denetim bulgusu "yanlış alarm"). Satır, iz anahtarları
ve hesabın iz satırları TEK okuma işleminde okunur: bağlantı bir işlemde değilse `BEGIN … COMMIT`
ile sarılır (Django'nun otomatik commit kipindeki bağlantısı da, geri yüklemenin salt okunur
bağlantıları da), işlemdeyse (Django `atomic`'i) o işlemin anlık görüntüsü kullanılır. Ayrı
deyimler WAL kipinde ayrı anlık görüntüler okurdu: satır okunduktan sonra aynı hesaba commit edilen
meşru bir yazım (satır + son hâlin iz satırı) eski satırı yeni iz satırıyla karşılaştırtır, yanlış
"tutmuyor" kararı silinemez bir `BUTUNLUK` satırı doğururdu. Çağıranın ORM okuması ile bu okuma
arasındaki yarış (beklenen mühür değişmiş) ayrıca `app_password.satir_izini_denetle`'de yazıcılarla
sıralı bir işlemde yinelenen denetimle ayrılır.

KAPSAMIN SINIRI (dürüst; `app_password` modül başlığı "KALAN RİSKLER" (b)). Denetim hesabın KENDİ
iz satırlarını doğrular; zincirin geri kalanını doğrulamaz. Zinciri F1b'de yalnız kilit açılışı
doğrular: son 200 satır (`iz_dogrulama.SON_SATIR`) ve çapa; bulgu girişi engellemez (altın kural
3). Zincirin tamamını doğrulayan Denetleme Kurulu denetiminin üretim yolu F3/F4'tedir (plan). Bu
yüzden:

* veritabanının BÜTÜNÜYLE (iz dahil) eski bir kopyayla değiştirilmesi ve iz kuyruğunun satırla
  birlikte kesilmesi bu denetimle yakalanmaz (satır, kopyanın son iz satırını tutar);
* hesabın yeni iz satırlarını silmek ya da `model`/`object_id`'lerini değiştirip onları hesabın
  satırı olmaktan çıkarmak, satırı geri sarmakla birlikte yapılırsa bu denetimden geçer. Silinen
  satırdan sonrakiler yeniden numaralanırsa kayma zincir başına ulaşır; çapa (`kuyruk_kesik`) ve son
  200 satır onu her zaman `BUTUNLUK` bulgusu olarak gösterir. Yeniden numaralamasız silme ve
  `model`/`object_id` değişikliği ise yalnız değişen satır kilit açılışının 200 satırlık doğrulama
  penceresindeyse (ya da hemen önündeyse) bulgu olur. Bulgu girişi engellemez (altın kural 3).
  Pencerenin dışındaysa F1b'de HİÇBİR yerde görünmez: çapa ve kâğıt çapası yalnız zincir başını
  görür. Hesabın son kaydından sonra 200'den çok satır yazılmışsa geri sarma bütünüyle sessizdir.
  Geri yükleme yollarında (geri yükleme yetkisi ve özet onarımının çapası) kenara alınan
  veritabanının zinciri hiç doğrulanmaz; bu varyant orada pencere içinde de görünmez, görünürlüğü
  yalnız geri yükleme kartı ve onarım satırlarıdır (çapa kolunu `ozet_onarimi`'nin sıra kuralı
  kapatır). Bu bölümü girişte sert engele çevirmek kullanıcı kararını bekler (plan F1b-2 ekleri).

ONARIMIN İZİ (`hesap_satirlarini_izle`; K-e). Geri yüklemenin özet onarımı (`ozet_onarimi`)
satırları ORM'siz, takastan ÖNCE `.tmp`'de yazar; o veritabanında oturum yoktur. Değiştirdiği her
satır için AYNI `sqlite3` işleminde zincirin sonuna `SISTEM` `HESAP` satırı eklenir: açık kip,
`key_ref` etkin `AuditKey`'in kimliği (İA verilen DEK'le çözülür), içerik MAC'i satırın onarılmış
hâlinden, zincir MAC'i `kanonik.iz_mac` ile — `denetim_izi._ekle`'nin yazdığıyla BİREBİR (sütun
biçimi Django'nunkidir; eşitlik testte ORM'le sabit). Böylece ilk kilit açılışı onarılan satırı
reddetmez; onarım denetim izinde `SISTEM` `HESAP` satırı olarak kalır (değişen alan adlarıyla:
`wrap_digest`, `wrap_digest_pending`, `seal`, yalnız değişenler; değer yok — özet ve mühür izinli
değer değildir; izi okuma ekranı Denetleme Kurulu modülüyle F4'te gelir) ve satırlar zincir
doğrulamasından bulgusuz geçer. Satırın anı geri yüklemenin anıdır. İA çözülemez ya da zincir başı biçimsizse onarım yazılamaz (`IzYazilamadi`): geri yükleme
yarıda kalır, hiçbir dosya değişmez. Zincir başı onarımın satırlarına kayar; geri yükleme notu
KENARA ALINAN veritabanının zincir başını taşır (değişmez), çapa ilk kilit açılışında yenilenir.

Neden geri yükleme notunda MAC'li bir liste değil: not program dışından değiştirilebilen MAC'siz
bir JSON'dur; listeye güvenmek için DEK'ten türeyen ikinci bir anahtar, notu okuyan her denetim
noktasında (geri yüklemenin parola yolu dahil) bir "bekleyen eşitleme" kuralı ve ilk açılışta ayrı
bir yazım gerekirdi. Satır izi veritabanının kendisinde, onu üreten işlemde durunca bekleyen hâl
yoktur.

Modül yalnız standart kitaplığa, `shared.kanonik`'e ve `shared.crypto`'nun saf işlevlerine dayanır
(Django ayarı, uygulama kaydı ve sorgusu gerekmez); konsol geri yüklemesi onu Django kurulmadan da
kullanır.
"""

from __future__ import annotations

import base64
import binascii
import json
import sqlite3
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final, Protocol

from cryptography.fernet import InvalidToken

from shared import crypto, kanonik

#: Hesap satırının iz satırlarındaki model etiketi (`denetim_izi.model_etiketi(Account)`).
HESAP_MODELI: Final = "okul.Account"

#: İçerik MAC'ine giren `Account` alanları — `Account.IZ_OZET_ALANLARI` ile BİREBİR (sıra dahil;
#: altın liste `test_satir_izi.py`'de). KURAL: bu kümeyi ya da var olan satırların bu alanlardaki
#: değerini değiştiren her değişiklik (F4'ün DEK yenilemesindeki mühür, özet ve ad-soyad yeniden
#: yazımı dahil), `KAPALI` olanlar DAHİL BÜTÜN `Account` satırlarının izini aynı işlemde yeniden
#: kurmalıdır: her satıra, satırın yeni hâlinin içerik MAC'ini taşıyan ve o sırada yürürlükteki iz
#: anahtarıyla mühürlü bir iz satırı yazılır — ama YALNIZ satır önce ESKİ hâliyle (eski alan
#: kümesi, eski anahtar) son içerik MAC'li kaydını tutuyorsa; tutmayana dokunulmaz (doğrulamasız
#: yeniden kurma geri sarılmış satırı aklardı). Yoksa açık satırların girişi reddedilir, `KAPALI`
#: satırlar "kaydı program dışından değiştirilmiş görünen hesaplar" listesine (`seal_mismatch`)
#: düşer ve sarmallarının temizliği durur. Bu yolun bugün yeri YOKTUR: satırın izi kilit
#: açılışında, DEK belleğe alınmadan ve her veri göçünden ÖNCE denetlenir; şema göçü kilitliyken
#: iz yazamaz. Kümeyi değiştiren değişiklik bu adım tasarlanmadan yapılmaz (kullanıcı kararı
#: bekler; `denetim_izi` modül başlığı "ÖZET ALANLARI VE ŞEMA DEĞİŞİMİ").
HESAP_OZET_ALANLARI: Final[tuple[str, ...]] = (
    "login_name",
    "role",
    "display_name",
    "status",
    "suspend_reason",
    "opened_at",
    "opened_by",
    "closed_at",
    "closed_by",
    "password_changed_at",
    "reset_at",
    "reset_by",
    "reset_kind",
    "reset_notice_pending",
    "last_login_at",
    "wrap_digest",
    "wrap_digest_pending",
    "seal",
)
#: Türlerine göre alanlar (ham değerin ORM değerine çevrilmesi; `hesap_ozet_alanlari`).
_SIFRELI: Final = frozenset({"display_name"})
_ZAMANLAR: Final = frozenset(
    {"opened_at", "closed_at", "password_changed_at", "reset_at", "last_login_at"}
)
_YABANCI_ANAHTARLAR: Final = frozenset({"opened_by", "closed_by", "reset_by"})
_MANTIKSALLAR: Final = frozenset({"reset_notice_pending"})

#: Onarımın iz satırının sabitleri (`AuditActor.SISTEM`, `AuditAction.HESAP`,
#: `AuditKeyMode.ACIK`; modeller ORM istediği için değerler burada metindir, eşitliği test sabitler).
AKTOR_SISTEM: Final = "SISTEM"
TUR_HESAP: Final = "HESAP"
KIP_ACIK: Final = "ACIK"
#: Onarımın değiştirebildiği sütunlar, model sırasıyla (iz satırının `changed_fields`'ı).
ONARIM_ALANLARI: Final[tuple[str, ...]] = ("wrap_digest", "wrap_digest_pending", "seal")

#: İz anahtarının uzunluğu (`denetim_izi.IZ_ANAHTARI_BAYT`; eşitliği test sabitler).
IZ_ANAHTARI_BAYT: Final = 32


class _Bicimsiz(Exception):
    """Ham değer ORM'in verdiği değere çevrilemiyor: satır tutmaz sayılır (fail-closed)."""


class IzYazilamadi(Exception):
    """Onarımın iz satırı yazılamadı (İA çözülemiyor, zincir başı biçimsiz): onarım yapılmaz."""


class _Imlec(Protocol):
    def fetchall(self) -> list[Any]: ...

    def fetchone(self) -> Any: ...

    def close(self) -> None: ...


class Baglanti(Protocol):
    """`sqlite3.Connection` biçiminde bağlantı (`execute(sql, parametreler)` → imleç; açık bir
    işlemin içinde mi)."""

    @property
    def in_transaction(self) -> bool: ...

    def execute(self, sql: str, parameters: Sequence[Any] = ..., /) -> _Imlec: ...


@contextmanager
def okuma_islemi(baglanti: Baglanti) -> Iterator[None]:
    """Okumaları TEK bir okuma işleminde (tek anlık görüntü) toplar (modül başlığı "TEK ANLIK
    GÖRÜNTÜ").

    Bağlantı zaten bir işlemdeyse (Django `atomic`'i, çağıranın açtığı işlem) hiçbir şey eklemez:
    okumalar o işlemin anlık görüntüsündedir. Değilse `BEGIN` (ertelenmiş; salt okunur `mode=ro`
    bağlantıda da çalışır) gönderilir ve çıkışta işlem kapatılır — hata yolunda `ROLLBACK`; Django'nun
    otomatik commit kipindeki bağlantısında açık işlem kalmaz. Gövde yalnız okur.
    """
    if baglanti.in_transaction:
        yield
        return
    baglanti.execute("BEGIN")
    try:
        yield
    except BaseException:
        if baglanti.in_transaction:
            with suppress(sqlite3.Error):
                baglanti.execute("ROLLBACK")
        raise
    if baglanti.in_transaction:
        baglanti.execute("COMMIT")


# ---------------------------------------------------------------------------
# Ham değerlerin çevrilmesi
# ---------------------------------------------------------------------------
def _metin(ham: object) -> str:
    """`CAST(… AS BLOB)` baytlarının metni (katı UTF-8); bayt değilse ya da çözülmezse `_Bicimsiz`."""
    if not isinstance(ham, bytes):
        raise _Bicimsiz
    try:
        return ham.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _Bicimsiz from exc


def _metin_ya_da_none(ham: object) -> str | None:
    return None if ham is None else _metin(ham)


def _zaman(ham: object) -> datetime | None:
    """Django'nun saat dilimsiz UTC metni → saat dilimli zaman (ORM'in dönüştürücüsü gibi)."""
    if ham is None:
        return None
    try:
        an = datetime.fromisoformat(_metin(ham))
    except ValueError as exc:
        raise _Bicimsiz from exc
    return an.replace(tzinfo=UTC) if an.tzinfo is None else an


def _kimlik_metni(ham: object) -> str | None:
    """Ham kimlik (tiresiz 32 hane) → tireli UUID metni; boşsa None."""
    if ham is None:
        return None
    try:
        return str(uuid.UUID(_metin(ham)))
    except ValueError as exc:
        raise _Bicimsiz from exc


def _mantiksal(ham: object) -> bool:
    if ham == b"1":
        return True
    if ham == b"0":
        return False
    raise _Bicimsiz


def _tamsayi(ham: object) -> int:
    metin = _metin(ham)
    if not metin.isascii() or not metin.isdigit():
        raise _Bicimsiz
    return int(metin)


def _sifreli(ham: object, dek: bytes) -> object:
    """Şifreli alanın ORM değeri: boşsa olduğu gibi, çözülürse metin, çözülmezse bozuk temsil.

    `crypto.EncryptedTextField.from_db_value` ve `denetim_izi._alan_degeri` ile aynı kural
    (kilit açıkken katı kip; `CorruptField` → `kanonik.bozuk_alan(ham)`).
    """
    if ham is None:
        return None
    token = _metin(ham)
    if token == "":
        return ""
    try:
        return crypto.decrypt_with(dek, token).decode("utf-8")
    except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError):
        return kanonik.bozuk_alan(token)


def hesap_ozet_alanlari(ham: Sequence[Any], dek: bytes) -> dict[str, Any]:
    """`_hesap_satiri`'nın satırını içerik MAC'inin alanlarına çevirir (ORM'in değerleriyle aynı).

    Biçimsiz değer `_Bicimsiz` yükseltir (çağıran "tutmuyor" sayar).
    """
    alanlar: dict[str, Any] = {}
    for alan, deger in zip(HESAP_OZET_ALANLARI, ham, strict=True):
        if alan in _SIFRELI:
            alanlar[alan] = _sifreli(deger, dek)
        elif alan in _ZAMANLAR:
            alanlar[alan] = _zaman(deger)
        elif alan in _YABANCI_ANAHTARLAR:
            alanlar[alan] = _kimlik_metni(deger)
        elif alan in _MANTIKSALLAR:
            alanlar[alan] = _mantiksal(deger)
        else:
            alanlar[alan] = _metin_ya_da_none(deger)
    return alanlar


def _hesap_satiri(baglanti: Baglanti, kimlik: str) -> Sequence[Any] | None:
    """Hesabın ham satırı (`HESAP_OZET_ALANLARI` sırası, `CAST(… AS BLOB)`); yoksa ya da birden
    çoksa None. Sorgu kaynakta sabit bir `SELECT`'tir (izsiz yazım taraması salt okuma sayar);
    sütun sırasını `test_satir_izi.py` `HESAP_OZET_ALANLARI`'yla karşılaştırır."""
    satirlar = baglanti.execute(
        "SELECT CAST(login_name AS BLOB), CAST(role AS BLOB), CAST(display_name AS BLOB), "
        "CAST(status AS BLOB), CAST(suspend_reason AS BLOB), CAST(opened_at AS BLOB), "
        "CAST(opened_by_id AS BLOB), CAST(closed_at AS BLOB), CAST(closed_by_id AS BLOB), "
        "CAST(password_changed_at AS BLOB), CAST(reset_at AS BLOB), CAST(reset_by_id AS BLOB), "
        "CAST(reset_kind AS BLOB), CAST(reset_notice_pending AS BLOB), "
        "CAST(last_login_at AS BLOB), CAST(wrap_digest AS BLOB), "
        "CAST(wrap_digest_pending AS BLOB), CAST(seal AS BLOB) FROM okul_account WHERE id = ?",
        (uuid.UUID(kimlik).hex,),
    ).fetchall()
    return satirlar[0] if len(satirlar) == 1 else None


# ---------------------------------------------------------------------------
# İz satırı ve iz anahtarı
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _IzSatiri:
    seq: int
    alanlar: dict[str, Any]
    record_mac: str
    key_mode: str
    key_ref: str
    prev_mac: str
    mac: str


def _iz_satiri(ham: Sequence[Any]) -> _IzSatiri:
    """`hesap_izi_sirasi`'nın iz sorgusunun satırı (tür sütunu hariç) → zincir MAC'inin alanları
    (`denetim_izi.satir_alanlari` ile aynı).

    `term` ve `compliance_item` F1c'ye dek None'dır; `denetim_izi.satir_alanlari` ile birlikte
    değişir (sütunlar gelince ham sorguya da eklenir).
    """
    (
        seq_ham,
        an_ham,
        aktor,
        hesap,
        rol,
        tur,
        model,
        kimlik,
        degisen,
        degerler,
        record_mac,
        etiket,
        kip,
        key_ref,
        prev_mac,
        mac,
    ) = ham
    seq = _tamsayi(seq_ham)
    an = _zaman(an_ham)
    if an is None:
        raise _Bicimsiz
    try:
        degisen_alanlar = json.loads(_metin(degisen))
        deger_sozlugu = json.loads(_metin(degerler))
    except (ValueError, RecursionError) as exc:
        raise _Bicimsiz from exc
    alanlar = {
        "seq": seq,
        "at": an,
        "actor": _metin(aktor),
        "account": _kimlik_metni(hesap),
        "role": _metin(rol),
        "action": _metin(tur),
        "model": _metin(model),
        "object_id": _metin(kimlik),
        "term": None,
        "changed_fields": degisen_alanlar,
        "values": deger_sozlugu,
        "record_mac": _metin(record_mac),
        "compliance_item": None,
        "label": _metin(etiket),
        "key_mode": _metin(kip),
        "key_ref": _metin(key_ref),
    }
    return _IzSatiri(
        seq=seq,
        alanlar=alanlar,
        record_mac=alanlar["record_mac"],
        key_mode=alanlar["key_mode"],
        key_ref=alanlar["key_ref"],
        prev_mac=_metin(prev_mac),
        mac=_metin(mac),
    )


def _ia_coz(token: str, dek: bytes) -> bytes | None:
    """`AuditKey.key` belirtecini DEK'le çözer (`denetim_izi._token_coz` ile aynı); olmazsa None."""
    try:
        ia = base64.b64decode(crypto.decrypt_with(dek, token), validate=True)
    except (InvalidToken, UnicodeEncodeError, binascii.Error, ValueError):
        return None
    return ia if len(ia) == IZ_ANAHTARI_BAYT else None


class _IzAnahtarlari:
    """`AuditKey` satırları (küçük tablo; bir kez okunur) ve çözülmüş İA'lar (önbellekte).

    Kimliği ya da geçerli ilk sırası SQLite'ta tamsayı türünde olmayan (program dışından BLOB ya da
    metin yazılmış) ya da çevrilemeyen bir satır varsa `bozuk`'tur: yürürlük kuralı güvenilir
    değildir, hiçbir hesabın izi doğrulanmaz (fail-closed; modül başlığı adım 2, "TÜR ŞARTI").
    """

    def __init__(self, baglanti: Baglanti, dek: bytes) -> None:
        self._dek = dek
        self.bozuk = False
        self._kayitlar: dict[int, tuple[bytes | None, int]] = {}
        for tamsayi_mi, ham_id, ham_key, ham_gecerli in baglanti.execute(
            "SELECT typeof(id) = 'integer' AND typeof(valid_from_seq) = 'integer', "
            "CAST(id AS BLOB), CAST(key AS BLOB), CAST(valid_from_seq AS BLOB) FROM okul_auditkey"
        ).fetchall():
            try:
                if tamsayi_mi != 1:
                    raise _Bicimsiz
                kayit_id = _tamsayi(ham_id)
                gecerli = _tamsayi(ham_gecerli)
            except _Bicimsiz:
                self.bozuk = True
                continue
            self._kayitlar[kayit_id] = (ham_key if isinstance(ham_key, bytes) else None, gecerli)
        self._cozulen: dict[int, bytes | None] = {}

    def _yururlukteki(self, seq: int) -> int | None:
        """`seq` satırını mühürlemesi gereken anahtar: geçerli ilk sırası `seq`'e eşit ya da küçük
        olanların EN YENİSİ (`denetim_izi.sirayi_muhurleyen_ia` ile aynı kural)."""
        adaylar = [
            (gecerli, kayit_id)
            for kayit_id, (_, gecerli) in self._kayitlar.items()
            if gecerli <= seq
        ]
        return max(adaylar)[1] if adaylar else None

    def satirin(self, key_ref: str, seq: int) -> bytes | None:
        """Açık kip satırını mühürleyen İA: `key_ref` ASCII ondalık kimlik, kayıt var, DEK'le
        çözülüyor ve satırın sırasında YÜRÜRLÜKTEKİ anahtar odur; değilse None.

        Yürürlük şartı `denetim_izi._acik_zincir_anahtarlari`'nın "satır anahtarın geçerli ilk
        sırasından önce olamaz" kuralından katıdır: DEK yenilemesinden (TK12, F4) kalan eski bir
        İA'yı bilen biri, yenilemeden sonraki bir satırı o anahtarla yeniden mühürleyip (`key_ref`,
        `record_mac` ve `mac` birlikte) eski bir hâli aklatamasın. Program her satırı yürürlükteki
        (etkin) anahtarla yazar.
        """
        if not key_ref or not (key_ref.isascii() and key_ref.isdigit()):
            return None
        kayit_id = int(key_ref)
        kayit = self._kayitlar.get(kayit_id)
        if kayit is None or self._yururlukteki(seq) != kayit_id:
            return None
        if kayit_id not in self._cozulen:
            ia: bytes | None = None
            if kayit[0] is not None:
                try:
                    ia = _ia_coz(_metin(kayit[0]), self._dek)
                except _Bicimsiz:
                    ia = None
            self._cozulen[kayit_id] = ia
        return self._cozulen[kayit_id]


def _mac_tutuyor(ia: bytes, satir: _IzSatiri) -> bool:
    """Satırın zincir MAC'i İA'nın zincir anahtarıyla yeniden hesaplanınca tutuyor mu?"""
    try:
        beklenen = kanonik.iz_mac(crypto.audit_chain_key(ia), satir.alanlar, satir.prev_mac)
    except kanonik.KanonikHata:
        return False
    return kanonik.esit(satir.mac, beklenen)


# ---------------------------------------------------------------------------
# Karar
# ---------------------------------------------------------------------------
def kanonik_kimlik(hesap_id: object) -> str | None:
    """Hesap kimliğinin tireli metni (iz satırının `object_id`'si); UUID değilse None."""
    try:
        return str(hesap_id if isinstance(hesap_id, uuid.UUID) else uuid.UUID(str(hesap_id)))
    except ValueError:
        return None


def hesap_izi_tutuyor(
    baglanti: Baglanti, hesap_id: object, dek: bytes, *, beklenen_muhur: str | None = None
) -> bool:
    """Hesap satırı denetim izindeki son içerik MAC'li kaydını tutuyor mu? (modül başlığı)

    `hesap_izi_sirasi(...) is not None`; ayrıntılar orada.
    """
    return hesap_izi_sirasi(baglanti, hesap_id, dek, beklenen_muhur=beklenen_muhur) is not None


def hesap_izi_sirasi(
    baglanti: Baglanti, hesap_id: object, dek: bytes, *, beklenen_muhur: str | None = None
) -> int | None:
    """Satırın tuttuğu (eşleştiği) iz satırının sırası; tutmuyorsa None (modül başlığı).

    Satır yoksa, biçimsizse, mührü verilen `beklenen_muhur`'a eşit değilse (adım 5), hesabın okunan
    bir iz satırının sırası tamsayı değilse ya da zincir MAC'i tutmuyorsa, iz anahtarı tablosunda
    biçimsiz satır varsa ya da içerik MAC'li iz satırı yoksa None (fail-closed). Bütün okumalar tek
    anlık görüntüdedir (`okuma_islemi`). Hiçbir şey yazmaz. Veritabanı hatası (tablo yok, dosya
    kilitli) çağırana yükselir. Sıra, geri yüklemenin özet onarımında çapanın soyunu sınar
    (`ozet_onarimi` modül başlığı "SIRA KURALI").
    """
    kimlik = kanonik_kimlik(hesap_id)
    if kimlik is None:
        return None
    with okuma_islemi(baglanti):
        return _eslesen_sira(baglanti, kimlik, dek, beklenen_muhur)


def _eslesen_sira(
    baglanti: Baglanti, kimlik: str, dek: bytes, beklenen_muhur: str | None
) -> int | None:
    """`hesap_izi_sirasi`'nın gövdesi; çağıran okuma işlemini açmıştır."""
    ham = _hesap_satiri(baglanti, kimlik)
    if ham is None:
        return None
    try:
        alanlar = hesap_ozet_alanlari(ham, dek)
    except _Bicimsiz:
        return None
    if beklenen_muhur is not None and not kanonik.esit(alanlar["seal"], beklenen_muhur):
        return None  # çağıranın kararı verdiği hâl bu hâl değil (adım 5)
    anahtarlar = _IzAnahtarlari(baglanti, dek)
    if anahtarlar.bozuk:
        return None
    imlec = baglanti.execute(
        "SELECT typeof(seq) = 'integer', "
        'CAST(seq AS BLOB), CAST("at" AS BLOB), CAST(actor AS BLOB), '
        "CAST(account_id AS BLOB), CAST(role AS BLOB), CAST(action AS BLOB), "
        "CAST(model AS BLOB), CAST(object_id AS BLOB), CAST(changed_fields AS BLOB), "
        'CAST("values" AS BLOB), CAST(record_mac AS BLOB), CAST(label AS BLOB), '
        "CAST(key_mode AS BLOB), CAST(key_ref AS BLOB), CAST(prev_mac AS BLOB), "
        "CAST(mac AS BLOB) FROM okul_audittrail WHERE model = ? AND object_id = ? "
        "ORDER BY seq DESC",
        (HESAP_MODELI, kimlik),
    )
    try:
        while True:
            satir_ham = imlec.fetchone()
            if satir_ham is None:
                return None  # içerik MAC'li iz satırı yok (adım 4)
            if satir_ham[0] != 1:
                return None  # sırası tamsayı değil: BLOB/metin en yeni sıralanır (adım 2)
            try:
                satir = _iz_satiri(satir_ham[1:])
            except _Bicimsiz:
                return None
            ia = anahtarlar.satirin(satir.key_ref, satir.seq)
            if satir.key_mode != KIP_ACIK or ia is None or not _mac_tutuyor(ia, satir):
                return None  # hesabın satırı program dışından değişmiş (adım 2)
            if not satir.record_mac:
                continue
            try:
                guncel = kanonik.kayit_mac(
                    crypto.record_summary_key(ia), HESAP_MODELI, kimlik, alanlar
                )
            except kanonik.KanonikHata:
                return None
            return satir.seq if kanonik.esit(satir.record_mac, guncel) else None
    finally:
        imlec.close()


# ---------------------------------------------------------------------------
# Onarımın izi (yazıcı; modül başlığı "ONARIMIN İZİ")
# ---------------------------------------------------------------------------
def _etkin_anahtar(baglanti: Baglanti, dek: bytes) -> tuple[int, bytes]:
    """Etkin (emekli olmamış, en yeni) iz anahtarı: (kimlik, İA); `denetim_izi._etkin_kayit` gibi."""
    kayit = baglanti.execute(
        "SELECT CAST(id AS BLOB), CAST(key AS BLOB) FROM okul_auditkey "
        "WHERE retired_at IS NULL ORDER BY valid_from_seq DESC LIMIT 1"
    ).fetchone()
    if kayit is None:
        raise IzYazilamadi("Geri yüklenen veritabanında etkin iz anahtarı yok.")
    try:
        kayit_id = _tamsayi(kayit[0])
        ia = _ia_coz(_metin(kayit[1]), dek)
    except _Bicimsiz as exc:
        raise IzYazilamadi("Geri yüklenen veritabanının iz anahtarı biçimsiz.") from exc
    if ia is None:
        raise IzYazilamadi("Geri yüklenen veritabanının iz anahtarı bu DEK'le çözülemedi.")
    return kayit_id, ia


def django_zamani(an: datetime) -> str:
    """Django'nun SQLite'a yazdığı zaman metni: saat dilimsiz UTC, `str(datetime)`."""
    return str(an.astimezone(UTC).replace(tzinfo=None))


def hesap_satirlarini_izle(
    baglanti: Baglanti,
    degisenler: Mapping[str, Sequence[str]],
    dek: bytes,
    *,
    an: datetime,
) -> list[int]:
    """Onarılan her hesap satırı için zincirin sonuna `SISTEM` `HESAP` satırı ekler.

    `degisenler`: {kanonik kimlik: değişen alan adları (model sırasıyla)}. Çağıranın açık
    `sqlite3` işleminde ve satırlar YAZILDIKTAN sonra çağrılır: içerik MAC'i satırın onarılmış
    hâlinden okunur. Commit çağıranındır. Eklenen satırların sıralarını döndürür. İA çözülemez,
    zincir başı ya da satır biçimsizse `IzYazilamadi` (hiçbir satır eklenmeden önce de olabilir;
    çağıran işlemi geri alır).
    """
    if not degisenler:
        return []
    kayit_id, ia = _etkin_anahtar(baglanti, dek)
    bas = baglanti.execute(
        "SELECT typeof(seq) = 'integer', CAST(seq AS BLOB), CAST(mac AS BLOB) "
        "FROM okul_audittrail ORDER BY seq DESC LIMIT 1"
    ).fetchone()
    try:
        if bas is None:
            seq, prev_mac = 0, ""
        elif bas[0] != 1:
            raise _Bicimsiz
        else:
            seq, prev_mac = _tamsayi(bas[1]), _metin(bas[2])
    except _Bicimsiz as exc:
        raise IzYazilamadi("Geri yüklenen veritabanının zincir başı biçimsiz.") from exc
    zincir = crypto.audit_chain_key(ia)
    ozet = crypto.record_summary_key(ia)
    eklenen: list[int] = []
    for kimlik in sorted(degisenler):
        ham = _hesap_satiri(baglanti, kimlik)
        if ham is None:
            raise IzYazilamadi("Onarılan hesap satırı okunamadı.")
        try:
            record_mac = kanonik.kayit_mac(
                ozet, HESAP_MODELI, kimlik, hesap_ozet_alanlari(ham, dek)
            )
        except (_Bicimsiz, kanonik.KanonikHata) as exc:
            raise IzYazilamadi("Onarılan hesap satırının içerik MAC'i hesaplanamadı.") from exc
        seq += 1
        satir: dict[str, Any] = {
            "seq": seq,
            "at": an,
            "actor": AKTOR_SISTEM,
            "account": None,
            "role": "",
            "action": TUR_HESAP,
            "model": HESAP_MODELI,
            "object_id": kimlik,
            "term": None,
            "changed_fields": list(degisenler[kimlik]),
            "values": {},
            "record_mac": record_mac,
            "compliance_item": None,
            "label": "",
            "key_mode": KIP_ACIK,
            "key_ref": str(kayit_id),
        }
        try:
            mac = kanonik.iz_mac(zincir, satir, prev_mac)
        except kanonik.KanonikHata as exc:
            raise IzYazilamadi("Geri yüklenen veritabanının zincir başı biçimsiz.") from exc
        baglanti.execute(
            'INSERT INTO okul_audittrail (seq, "at", actor, account_id, role, action, model, '
            'object_id, changed_fields, "values", record_mac, label, key_mode, key_ref, '
            "prev_mac, mac) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                seq,
                django_zamani(an),
                AKTOR_SISTEM,
                "",
                TUR_HESAP,
                HESAP_MODELI,
                kimlik,
                json.dumps(satir["changed_fields"]),
                json.dumps(satir["values"]),
                record_mac,
                "",
                KIP_ACIK,
                str(kayit_id),
                prev_mac,
                mac,
            ),
        )
        eklenen.append(seq)
        prev_mac = mac
    return eklenen
