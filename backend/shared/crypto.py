"""Hesaplı güvenlik çekirdeği — anahtar tutucu, Argon2id türetme, şifreli alanlar, kör indeks.

Tasarım §4.3, §4.4.4, §5.3; şema 2 (F1b-1): veri anahtarı (DEK) her hesap için
ayrı sarılır (`apps.okul.services.app_password`), bu modül yalnız ilkelleri
sağlar. SQLCipher ve "kapanışta dosyayı şifrele" reddedildi; seçilen yol ailenin
sahada denenmiş `shared/fields.py` Fernet alan şifrelemesidir. Bu dosya o alanı
bu programın gerçeklerine uyarlar. KAYNAKTAN FARKLAR:

1. **Anahtar ayardan değil, ÇALIŞMA ZAMANINDAN gelir.** Kaynakta anahtar
   `settings.FIELD_ENCRYPTION_KEY` (.env) ile sabittir; burada bir hesabın
   parolasından (ya da kurtarma anahtarından) çözülen veri anahtarıdır (DEK) ve
   programın kilidi açılana kadar YOKTUR. Bu yüzden `lru_cache`'li Fernet
   KULLANILAMAZ — anahtar süreç ömrü içinde yüklenir, boşaltılır, değişir.
2. **Hesapsız kip YOKTUR (fail-closed, §5.3).** İlk program yöneticisi hesabı
   kurulum sihirbazının ilk adımıdır ve hesap kurulmadan kişi yazan her uç 409
   döner. Anahtar bellekte değilken `EncryptedTextField` boş olmayan bir değeri
   YAZMAZ, `KeyMissingError` yükseltir: kilitliyken ya da hesap hiç
   kurulmamışken kişi adı düz metin olarak diske düşemez. Ailenin eski
   "parolasız kipte alanlar DÜZ yazılır" dalı ve onun geçiş aracı
   (`plaintext_writes`) aile iskeletinde sökülmüştü; OAB'de yoktur.
3. **Kör indeks VARDIR (§5.3 — ailenin eski "BLIND INDEX YOKTUR" kararından
   BİLİNÇLİ sapma).** Okul no da şifrelendiği için e-Okul eşleştirmesi tam
   eşleşmeyle `blind_index()` değerinden yapılır; teklik kısıtı indekse konur.
   Anahtar DEK'ten HKDF ile türediği için parola değişimi indeksi bozmaz.
   Normalleştirme çağıranın işidir (ör. `apps/okul/normalize.py`); bu modül
   yalnız HMAC'i hesaplar.
4. **Okuma KATI KİPTEDİR (tasarım TK8 (3), §13 D48).** Kilit açıkken çözülemeyen
   ya da token olmayan dolu değer düz metin diye DÖNMEZ: `CorruptField`
   işaretiyle döner (metin değildir) ve süreç içi kayda düşer
   (`corrupt_reads`); güvenlik durumu bozuk alan sayısını bildirir, pano kartı
   ön yüz commit'indedir. Ailenin hoşgörüsü düz metin döneminden kalmaydı;
   OAB'de düz metin dönemi hiç olmadı (§13 D29) ve hoşgörü SQLite'ta şifreli
   sütuna yazılmış düz metni meşru veri gibi gösterirdi (denetim GA-9). İşaret
   kaydedilirken eski ham değer AYNEN geri yazılır; şifrelenip meşru veriye
   dönmez. Hoşgörü 1. adımda hiçbir hâlde açılmaz: tek geçiş (`gecis:
   "KURULUM"`) kişi tabloları boşken koşar; DEK yenilemesinin geçişi F4'tedir.

HESAP SARMALI KİMLİĞE BAĞLIDIR (kullanıcı kararı 02.11.2026: "Hesap kimliği parola
kaydına bağlanır"; tasarım §4.4.4, tehdit 19 ve 21). Hesap sarmalının anahtarı
`HKDF(Argon2id(parola, tuz), bilgi = "od-hesap-sarmali/v1" ‖ kanonik hesap kimliği)`'dir
(`account_wrapping_key`). Eskiden kimlik ne KDF'ye ne Fernet'e giriyordu: `guvenlik.json`
düz metin olduğu için herhangi bir hesabın parolasını bilen biri kendi sarmalının `id`
alanını metin düzenleyiciyle program yöneticisininkine çevirip kilidi ve konsol geri
yüklemesini onun adına açabiliyordu (kod gerekmeden; tehdit 19'un çıtasının altında).
Artık başka kimlikle okunan sarmal açılmaz: Fernet'in HMAC'i tutmaz, sonuç yanlış
parolayla aynıdır. Neden HKDF (tuza ya da Argon2 girdisine katmak değil): Argon2id
çıktısı 32 baytlık tekdüze bir sırdır; HKDF-SHA256 onu bilgi dizgesiyle ayrışan
bağımsız anahtarlara açar (bir PRF'tir), türetimler §2.3.1 kimlik tablosundaki öteki
dizgelerle aynı kapıdan geçer (`derive_subkey`) ve Argon2id maliyeti değişmez. Bilgi
dizgesi sabit önek + sabit uzunlukta (36 karakter) kanonik kimliktir: kimlikten bilgiye
eşleme birebirdir, ayraç gerekmez. Kanonik biçim TEKTİR (`canonical_account_id`):
`uuid.UUID` nesnesinin metni ya da tam olarak o metin (küçük harf, tireli, boşluksuz).
Büyük harfli, tiresiz, boşluklu, süslü ayraçlı, `urn:uuid:` önekli ya da ASCII dışı
rakamlı yazımlar REDDEDİLİR (o sarmal açılmaz): satırı bulan okuyucu (`uuid.UUID(...)`,
Django `UUIDField`) bu yazımları aynı satıra çevirir; sarmalın açılması "kimlik metni
kanoniktir" demek olduğu için kimliği metin olarak karşılaştıran her sonraki adım (oturum
kimliği, geri yükleme notu, iz satırı) aynı hesabı aynı metinle görür. Kurtarma
bölümünün sarmalı hesaba bağlı DEĞİLDİR ve değişmedi (`derive_key` ham hâliyle). Bağın
çıtası: parolasını bildiği hesabın DEK'ini program dışında türetip başka kimlikle yeniden
saran ya da mühürlü sahte satır üreten biri yine geçer; bu artık KOD ister (tehdit 6, 19).
Bağ kimliği bağlar, tazeliği bağlamaz: aynı hesabın eski sarmalı eski parolasıyla açılır
(`app_password` modül başlığı "Kalan risk"; tehdit 12).

ANAHTARIN BELLEKTEKİ YERİ: anahtar süreç genelinde, bu modülün `_holder`
nesnesinde tutulur ve kilit açıldıktan sonra kilitlenene dek bellekte kalır.
Gerekçe: yönetim yüzeyi yalnız 127.0.0.1'de ve tek bilgisayara hizmet eder
(`desktop/session_guard.py`); süreçte tek oturum vardır (tasarım TK14).
Anahtarı her istekte yeniden türetmek Argon2id maliyetini (~0,2 sn) her
tıklamaya yayardı. Anahtarı oturum yükler ve düşürür (`apps/okul/oturum.py`:
kilit açılışı, Kilitle, boşta kilit, kapanış). Denetim izinin iz anahtarı (İA;
tasarım §4.6.3) DEK'ten türemez; kilit açılışında DEK'le birlikte yüklenir ve
onunla düşer (`load_key(..., audit_key=...)`). Her yükleme ve boşaltma
`key_epoch()` sayacını artırır (yalnız teşhis ve test içindir; oturumun açılışı bu
sayaçtan ÇIKARILMAZ, açık çağrıyla yapılır). Anahtar diske YAZILMAZ, loglanmaz,
hata mesajında yankılanmaz.

ŞİFRELİ ALANDA DB ARAMASI YOKTUR (§5.3): Fernet her şifrelemede farklı token
ürettiği için şifreli alan üzerinde DB tarafı filtre/LIKE/sıralama çalışmaz
(`Student.objects.filter(first_name=…)` daima boş döner). Ad temelli arama,
sıralama ve teklik selector katmanında Python ile; kimlik eşleştirmesi kör
indeksle yapılır. Arama ve eşleme `CorruptField` taşıyan kaydı dışarıda bırakır
(`has_corrupt`).
"""

from __future__ import annotations

import base64
import hmac
import secrets
import threading
import uuid
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, cast

from argon2.low_level import Type as Argon2Type
from argon2.low_level import hash_secret_raw
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.db import models
from django.db.models.signals import post_init

# Veri anahtarı (DEK) uzunluğu — Fernet 32 baytlık anahtar ister.
KEY_BYTES = 32
# Argon2id tuzu (parola başına ve kurtarma anahtarı başına ayrı üretilir).
SALT_BYTES = 16


@dataclass(frozen=True)
class KdfParams:
    """Argon2id maliyet parametreleri.

    Varsayılan, RFC 9106'nın "düşük bellek" profilidir (64 MiB / t=3 / p=4):
    okul bilgisayarında ~0,2 sn sürer, ama çalınmış bir veri klasörüne karşı
    kaba kuvvet denemesini de aynı oranda pahalılaştırır. Parametreler
    `guvenlik.json` içinde SAKLANIR; ileride artırılırsa eski dosyalar kendi
    parametreleriyle açılmaya devam eder (ileri uyumluluk).
    """

    time_cost: int = 3
    memory_cost: int = 65536  # KiB → 64 MiB
    parallelism: int = 4

    def to_dict(self) -> dict[str, int]:
        return {
            "time_cost": self.time_cost,
            "memory_cost": self.memory_cost,
            "parallelism": self.parallelism,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KdfParams:
        return cls(
            time_cost=int(data.get("time_cost", cls.time_cost)),
            memory_cost=int(data.get("memory_cost", cls.memory_cost)),
            parallelism=int(data.get("parallelism", cls.parallelism)),
        )


# Modül düzeyi varsayılan — testler ucuz profile indirir (Argon2 kasten yavaştır).
DEFAULT_KDF = KdfParams()


# ---------------------------------------------------------------------------
# Anahtar türetme ve sarmalama (zarf şifreleme)
# ---------------------------------------------------------------------------
# Neden ZARF (envelope) şifreleme? Kurtarma anahtarı şartı bunu ZORUNLU kılar:
# aynı veriyi hem parolayla hem kurtarma anahtarıyla açabilmek için, alanları
# şifreleyen anahtar (DEK) ikisinden de BAĞIMSIZ olmalı ve iki ayrı sarmalda
# saklanmalıdır. Yan faydaları:
#   * Parola değişimi veriyi YENİDEN ŞİFRELEMEZ — yalnız sarmal değişir (anlık,
#     yarıda kalma riski yok).
#   * DEK hiç değişmediği için ESKİ YEDEKLER (`gunluk-*.sqlite3`) parola
#     değiştikten sonra da açılabilir kalır.


def new_data_key() -> bytes:
    """Rastgele veri anahtarı (DEK) üretir."""
    return secrets.token_bytes(KEY_BYTES)


def new_salt() -> bytes:
    """Rastgele Argon2id tuzu üretir."""
    return secrets.token_bytes(SALT_BYTES)


def derive_key(secret: str, *, salt: bytes, params: KdfParams | None = None) -> bytes:
    """Sırdan Argon2id ile 32 baytlık anahtar türetir.

    Kurtarma bölümünün sarmalama anahtarı doğrudan budur. HESAP SARMALI bunu TEK BAŞINA
    kullanmaz: hesap kimliğine bağlı `account_wrapping_key`'den geçer (modül başlığı).
    """
    kdf = params or DEFAULT_KDF
    return hash_secret_raw(
        secret=secret.encode("utf-8"),
        salt=salt,
        time_cost=kdf.time_cost,
        memory_cost=kdf.memory_cost,
        parallelism=kdf.parallelism,
        hash_len=KEY_BYTES,
        type=Argon2Type.ID,
    )


def _fernet_for(raw_key: bytes) -> Fernet:
    """Ham 32 bayttan Fernet örneği (Fernet base64 kodlu anahtar ister)."""
    return Fernet(base64.urlsafe_b64encode(raw_key))


def wrap_key(data_key: bytes, *, wrapping_key: bytes) -> str:
    """DEK'i sarmalar (şifreler). Dönen metin `guvenlik.json` içinde saklanır."""
    return _fernet_for(wrapping_key).encrypt(data_key).decode("ascii")


def unwrap_key(wrapped: str, *, wrapping_key: bytes) -> bytes:
    """Sarmalı çözer. Yanlış parola/kurtarma anahtarında `InvalidToken` yükselir.

    AYRI BİR "doğrulama hash'i" TUTULMAZ: Fernet token'ı kimlik doğrulamalıdır
    (HMAC), yani sarmalın başarıyla çözülmesi parolanın doğruluğunun kanıtıdır.
    Ayrıca bir parola özeti saklamak, o özeti çevrimdışı kırma denemesine hedef
    yapardı — az sır, az yüzey.
    """
    return _fernet_for(wrapping_key).decrypt(wrapped.encode("ascii"))


def key_fingerprint(data_key: bytes) -> str:
    """Veri anahtarının tek yönlü parmak izi (DB ↔ güvenlik dosyası eşleşmesi için).

    `SchoolConfig.app_password_hash` alanına yazılır. Parolanın özeti DEĞİLDİR:
    DB kopyaları (yedekler) okul dışına çıkabilir, içlerinde parola özeti
    bulunması çevrimdışı kaba kuvvete davetiye olurdu.
    """
    return "v1:" + hmac.new(data_key, b"od-anahtar-parmak-izi", sha256).hexdigest()


# Kör indeks anahtarının HKDF bağlamı (tasarım §5.3). Değişirse bütün
# kör indeks sütunları yeniden hesaplanmalıdır — sabit, sürüm ekiyle değişir.
BLIND_INDEX_INFO = b"od-kor-indeks"
#: Hesap mührü anahtarının HKDF bağlamı (tasarım §2.3.1, §4.6.1): `Account.seal`
#: `HMAC(HKDF(DEK, "od-hesap-muhru/v1"), kanonik(...))`'tir (`shared.kanonik`).
#: Değişirse bütün mühürler tutmaz olur; tasarım tutmayan mührün yeniden
#: hesaplanmasını yasaklar. Sürüm eki yalnız DEK yenilemesiyle (F4) değişebilir.
ACCOUNT_SEAL_INFO = b"od-hesap-muhru/v1"
#: Hesap sarmalı anahtarının HKDF bağlamının öneki (tasarım §2.3.1, §4.4.4; kullanıcı kararı
#: 02.11.2026): anahtar `HKDF(Argon2id(parola, tuz), ACCOUNT_WRAP_INFO ‖ kanonik kimlik)`'tir
#: (`account_wrapping_key`). DEK'e değil parolanın Argon2id çıktısına uygulanır. Değişirse
#: bütün hesap sarmalları açılmaz olur (kurtarma bölümü etkilenmez); eski türetime geri
#: düşen yol YOKTUR.
ACCOUNT_WRAP_INFO = b"od-hesap-sarmali/v1"

# İz anahtarından (İA; tasarım §4.6.3) türeyen anahtarların HKDF bağlamları. İA DEK'ten
# TÜREMEZ; bu dizgeler yalnız İA'ya (kilitli kipte çapadan türeyen tohuma) uygulanır.
# Değişirse kâğıda inmiş zincir başları ve var olan bütün MAC'ler tutmaz olur.
#: Açık kipte zincir MAC'i: `HMAC(HKDF(İA, "od-denetim-izi/v1"), kanonik(satır) ‖ prev_mac)`.
AUDIT_CHAIN_INFO = b"od-denetim-izi/v1"
#: İçerik MAC'i ("kaydın özeti", §4.6.2): `HMAC(HKDF(İA, "od-kayit-ozeti/v1"), kanonik(...))`.
RECORD_SUMMARY_INFO = b"od-kayit-ozeti/v1"
#: Çapanın mührü (`iz-durumu.json`): `HMAC(HKDF(İA, "od-iz-capa/v1"), seq ‖ mac)`.
AUDIT_ANCHOR_INFO = b"od-iz-capa/v1"
#: Kilitli kip tohumu: `tohum₀ = HKDF(İA, "od-iz-kilitli/v1", tuz = seq ‖ mac)`.
AUDIT_LOCKED_SEED_INFO = b"od-iz-kilitli/v1"
#: Kilitli kipteki k'ıncı satırın anahtarı: `HKDF(tohumₖ, "od-iz-kilitli-mac/v1")`.
AUDIT_LOCKED_MAC_INFO = b"od-iz-kilitli-mac/v1"


def derive_subkey(key: bytes, *, info: bytes, salt: bytes | None = None) -> bytes:
    """Adlı amaç için 32 baytlık alt anahtar: HKDF-SHA256(salt, info=amaç).

    DEK'ten türeyen bütün anahtarların (kör indeks, hesap mührü; F3'te hareket
    parmak izi, 3. adımda dosya sarmalı), iz anahtarı türevlerinin (§4.6.3) ve hesap
    sarmalı anahtarının (parolanın Argon2id çıktısından; `account_wrapping_key`) tek
    kapısıdır. Bilgi dizgeleri kimlik tablosundadır (tasarım §2.3.1); her amaç
    ayrı dizge kullanır, bir amacın anahtarı ötekini vermez. Tuz yalnız kilitli kip
    tohumunda verilir (`tuz = seq ‖ mac`, §4.6.3); öteki türevlerde yoktur (None).
    """
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=info).derive(key)


def audit_chain_key(audit_key: bytes) -> bytes:
    """İA'dan açık kip zincir anahtarı (`od-denetim-izi/v1`; tasarım §4.6.3)."""
    return derive_subkey(audit_key, info=AUDIT_CHAIN_INFO)


def record_summary_key(audit_key: bytes) -> bytes:
    """İA'dan içerik MAC'i anahtarı (`od-kayit-ozeti/v1`; tasarım §4.6.2)."""
    return derive_subkey(audit_key, info=RECORD_SUMMARY_INFO)


def audit_anchor_key(audit_key: bytes) -> bytes:
    """İA'dan çapanın mühür anahtarı (`od-iz-capa/v1`; tasarım §4.6.3)."""
    return derive_subkey(audit_key, info=AUDIT_ANCHOR_INFO)


def audit_locked_seed(audit_key: bytes, anchor_bytes: bytes) -> bytes:
    """Kilitli kip tohumu: `tohum₀ = HKDF(İA, "od-iz-kilitli/v1", tuz = seq ‖ mac)` (§4.6.3).

    `anchor_bytes` çapanın `seq ‖ mac` baytlarıdır (`shared.kanonik.capa_baytlari`).
    """
    return derive_subkey(audit_key, info=AUDIT_LOCKED_SEED_INFO, salt=anchor_bytes)


def audit_locked_mac_key(seed: bytes) -> bytes:
    """Kilitli kipteki k'ıncı satırın zincir anahtarı: `HKDF(tohumₖ, "od-iz-kilitli-mac/v1")`."""
    return derive_subkey(seed, info=AUDIT_LOCKED_MAC_INFO)


def _derive_blind_index_key(data_key: bytes) -> bytes:
    """DEK'ten kör indeks HMAC anahtarı: HKDF-SHA256(salt=None, info="od-kor-indeks")."""
    return derive_subkey(data_key, info=BLIND_INDEX_INFO)


def account_seal_key(data_key: bytes) -> bytes:
    """DEK'ten hesap mührü anahtarı (`od-hesap-muhru/v1`; tasarım §4.6.1)."""
    return derive_subkey(data_key, info=ACCOUNT_SEAL_INFO)


def canonical_account_id(value: object) -> str:
    """Hesap kimliğinin TEK kanonik metni: `uuid.UUID` nesnesinin `str()`'i (modül başlığı).

    `uuid.UUID` nesnesi metnine çevrilir. Metin ancak tam olarak kanonik biçimdeyse (küçük
    harf, tireli, 36 karakter, boşluksuz) kabul edilir; büyük harfli, tiresiz, boşluklu,
    süslü ayraçlı, `urn:uuid:` önekli ya da ASCII dışı rakamlı yazım `ValueError`, metin ve
    UUID dışındaki tür `TypeError` yükseltir. Hesap sarmalının YAZICISI da OKUYUCUSU da
    kimliği buradan geçirir: çevrilemeyen kimlikle sarmal yazılmaz, açılmaz.
    """
    if isinstance(value, uuid.UUID):
        return str(value)
    if not isinstance(value, str):
        raise TypeError("Hesap kimliği UUID ya da metin olmalıdır.")
    kanonik = str(uuid.UUID(value))
    if value != kanonik:
        raise ValueError("Hesap kimliği kanonik biçimde değil.")
    return kanonik


def account_wrapping_key(
    password: str, *, salt: bytes, account_id: object, params: KdfParams | None = None
) -> bytes:
    """Hesap sarmalının anahtarı: `HKDF(Argon2id(parola, tuz), "od-hesap-sarmali/v1" ‖ kimlik)`.

    Kimlik `canonical_account_id`'den geçer (çevrilemezse `ValueError`/`TypeError`, Argon2id
    koşmadan). Başka kimlikle türetilen anahtar sarmalı açmaz (modül başlığı "HESAP SARMALI
    KİMLİĞE BAĞLIDIR"). Kurtarma bölümü bunu KULLANMAZ (hesaba bağlı değildir).
    """
    kimlik = canonical_account_id(account_id)
    return derive_subkey(
        derive_key(password, salt=salt, params=params),
        info=ACCOUNT_WRAP_INFO + kimlik.encode("ascii"),
    )


def decrypt_with(raw_key: bytes, token: str) -> bytes:
    """Verilen ham anahtarla (bellekteki DEK değil) Fernet token'ını çözer.

    Kilit açılışında iz anahtarı (İA) DEK BELLEĞE YÜKLENMEDEN önce aday DEK'le
    çözülür (tasarım §4.6.3; plan F1b-1 "Oturum"): çözülemezse oturum açılmaz.
    Yanlış anahtar ya da bozuk token `InvalidToken` yükseltir.
    """
    return _fernet_for(raw_key).decrypt(token.encode("ascii"))


class KeyMissingError(RuntimeError):
    """Veri anahtarı bellekte değilken şifreli alana boş olmayan değer yazılmak istendi.

    Fail-closed (§5.3): parola kurulmamışken ya da program kilitliyken kişi
    verisi düz metin olarak diske düşmez, işlem bu hatayla durur.
    `shared.exceptions.od_exception_handler` bunu 409 `parola_gerekli`
    yanıtına çevirir (parola kuruluysa kilitli durum zaten ara katmanda 423
    ile kesilir).
    """

    def __init__(self, message: str = "Veri anahtarı bellekte değil.") -> None:
        super().__init__(message)


# ---------------------------------------------------------------------------
# Süreç-geneli anahtar tutucu
# ---------------------------------------------------------------------------
class _KeyHolder:
    """Çalışma zamanı anahtar durumu (süreç geneli, iş parçacığı güvenli).

    `waitress` istekleri birden çok iş parçacığında karşılar; durum tek bilgisayara
    ait olduğu için süreç geneli tutulur, kilitle korunur. Kör indeks anahtarı
    yüklemede BİR KEZ türetilir ve anahtarla birlikte düşer.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._fernet: Fernet | None = None
        self._raw: bytes | None = None
        self._blind_key: bytes | None = None
        self._audit_key: bytes | None = None
        self._epoch = 0

    def load(self, raw_key: bytes, audit_key: bytes | None = None) -> None:
        blind_key = _derive_blind_index_key(raw_key)
        fernet = _fernet_for(raw_key)
        with self._lock:
            self._raw = raw_key
            self._fernet = fernet
            self._blind_key = blind_key
            self._audit_key = audit_key
            self._epoch += 1

    def unload(self) -> None:
        with self._lock:
            self._raw = None
            self._fernet = None
            self._blind_key = None
            self._audit_key = None
            self._epoch += 1

    @property
    def unlocked(self) -> bool:
        return self._fernet is not None

    @property
    def epoch(self) -> int:
        return self._epoch

    def fingerprint(self) -> str | None:
        raw = self._raw
        return key_fingerprint(raw) if raw is not None else None

    def raw(self) -> bytes | None:
        return self._raw

    def fernet(self) -> Fernet | None:
        return self._fernet

    def blind_key(self) -> bytes | None:
        return self._blind_key

    def audit_key(self) -> bytes | None:
        return self._audit_key


_holder = _KeyHolder()


def load_key(raw_key: bytes, *, audit_key: bytes | None = None) -> None:
    """Veri anahtarını (ve varsa iz anahtarını) belleğe alır; `key_epoch()` artar.

    İki anahtar tek adımda yüklenir: önceki oturumun iz anahtarı yeni DEK'le
    birlikte bellekte kalmaz. İz anahtarı verilmezse bellekte iz anahtarı yoktur
    (denetim izi yazıcısı bunu "iz yazılamaz" sayar; `apps.okul.denetim_izi`).
    """
    _holder.load(raw_key, audit_key)


def unload_key() -> None:
    """Anahtarı bellekten düşürür (kilitler); `key_epoch()` artar. Diske hiçbir şey yazılmaz."""
    _holder.unload()


def is_unlocked() -> bool:
    """Veri anahtarı bellekte mi?"""
    return _holder.unlocked


def key_epoch() -> int:
    """Her `load_key` ve `unload_key` çağrısında artan süreç içi sayaç.

    Teşhis ve test içindir (ör. "parola değişimi DEK'i yeniden yüklemedi"). Aile
    iskeletinin kip katmanı kilit açılışını bu sayacın değişiminden çıkarıyordu; OAB'de
    oturum yalnız açık çağrıyla açılır (`apps/okul/oturum.py`), sayaç hesap taşımaz.
    """
    return _holder.epoch


def active_fingerprint() -> str | None:
    """Yüklü anahtarın parmak izi; anahtar yoksa None."""
    return _holder.fingerprint()


def active_key() -> bytes | None:
    """Yüklü veri anahtarı (ham). Yalnız servis katmanı içindir; asla loglanmaz/döndürülmez."""
    return _holder.raw()


def active_audit_key() -> bytes | None:
    """Yüklü iz anahtarı (İA, ham; tasarım §4.6.3); yoksa None. Asla loglanmaz."""
    return _holder.audit_key()


def blind_index(normalized: str) -> str:
    """Kör indeks: `HMAC-SHA256(HKDF(DEK, info="od-kor-indeks"), değer)` (64 onaltılık hane).

    Belirlenimcidir: aynı DEK ve aynı değer daima aynı indeksi verir; bu yüzden
    tam eşleşme ve teklik kısıtı DB'de çalışır. Normalleştirme ÇAĞIRANIN
    işidir (ör. okul no için `normalize_student_number`). Boş dize `""` döner
    ("veri yok" hâli DB'de de boş görünür, kısmi teklik kısıtları buna
    dayanır). Anahtar bellekte değilse `KeyMissingError`.
    """
    if normalized == "":
        return ""
    key = _holder.blind_key()
    if key is None:
        raise KeyMissingError("Kör indeks için veri anahtarı bellekte değil.")
    return hmac.new(key, normalized.encode("utf-8"), sha256).hexdigest()


# ---------------------------------------------------------------------------
# Model alanları
# ---------------------------------------------------------------------------
class CorruptField:
    """Çözülemeyen şifreli alanın işareti (tasarım TK8 (3), §13 D48) — METİN DEĞİLDİR.

    Kilit açıkken bir şifreli sütunda token olmayan ya da bu DEK'le çözülemeyen
    dolu değer bulunursa `from_db_value` bunu döndürür. Bilinçli olarak `str`
    alt sınıfı DEĞİLDİR (plan F1b-1 "Denetim izi"): metin sanılıp şifrelenseydi
    işaret meşru veriye dönerdi.

    * `str()` boş dize verir, doğruluk değeri yanlıştır: ad birleştirme ve
      sıralama gibi yollar patlamaz, ama değer ekrana ve evraka düz metin olarak
      çıkmaz. Arama ve eşleme işaretli kaydı dışarıda bırakır (`has_corrupt`);
      serializer alanı `null` verir ve kaydın `bozuk_alanlar` listesine yazar.
    * Kaydedilirken `EncryptedTextField.get_prep_value` eski HAM değeri aynen
      geri yazar: bozukluk kayıtta görünür kalır, inceleme yapılabilir.
    * Ham değer `repr`'e ve günlüğe yazılmaz (düz metin kişi verisi olabilir).
    """

    __slots__ = ("_raw", "field_name", "model_label")

    def __init__(self, raw: str, *, model_label: str = "", field_name: str = "") -> None:
        self._raw = raw
        self.model_label = model_label
        self.field_name = field_name

    @property
    def raw(self) -> str:
        """Veritabanındaki ham değer (yalnız geri yazım içindir)."""
        return self._raw

    def __str__(self) -> str:
        return ""

    def __format__(self, format_spec: str) -> str:
        return format("", format_spec)

    def __repr__(self) -> str:
        return f"<CorruptField {self.model_label}.{self.field_name}>"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CorruptField) and other._raw == self._raw

    def __hash__(self) -> int:
        return hash(("CorruptField", self._raw))


def is_corrupt(value: object) -> bool:
    """Değer çözülemeyen şifreli alan işareti mi?"""
    return isinstance(value, CorruptField)


# Süreç içi bozuk okuma kaydı: (model etiketi, kayıt kimliği, alan adı). Güvenlik
# durumu sayıyı bildirir; pano kartı ön yüz commit'indedir (plan F1b-1 "Denetim
# izi": okuma GET isteğinde iz yazamaz, önce bellekte toplanır).
_bozuk_kilit = threading.Lock()
_bozuk_okumalar: set[tuple[str, str, str]] = set()
_sifreli_alan_onbellegi: dict[type[Any], tuple[str, ...]] = {}


def record_corrupt_read(model_label: str, pk: object, field_name: str) -> None:
    """Bozuk okumayı süreç içi kayda ekler (aynı kayıt-alan bir kez sayılır)."""
    with _bozuk_kilit:
        _bozuk_okumalar.add((model_label, "" if pk is None else str(pk), field_name))


def corrupt_reads() -> list[tuple[str, str, str]]:
    """Bu süreçte okunan bozuk alanlar: (model etiketi, kayıt kimliği, alan adı), sıralı."""
    with _bozuk_kilit:
        return sorted(_bozuk_okumalar)


def corrupt_read_count() -> int:
    """Bu süreçte okunan bozuk alanların sayısı (güvenlik durumu bildirir)."""
    with _bozuk_kilit:
        return len(_bozuk_okumalar)


def _reset_corrupt_reads_for_tests() -> None:
    """Yalnız testler için: süreç içi kayıt testler arasında sızmasın."""
    with _bozuk_kilit:
        _bozuk_okumalar.clear()


def corrupt_fields_of(instance: models.Model) -> list[str]:
    """Kaydın `CorruptField` taşıyan şifreli alanlarının adları (alan sırasıyla)."""
    return [
        alan.name
        for alan in encrypted_fields_of(type(instance))
        if isinstance(instance.__dict__.get(alan.attname), CorruptField)
    ]


def has_corrupt(instance: models.Model) -> bool:
    """Kayıtta çözülemeyen şifreli alan var mı? (arama ve eşleme dışarıda bırakır)"""
    return bool(corrupt_fields_of(instance))


def _bozuk_alanlari_kaydet(sender: type[Any], instance: models.Model, **kwargs: Any) -> None:
    """`post_init`: veritabanından gelen kayıttaki işaretleri kimliğiyle kaydeder.

    `from_db_value` kaydın kimliğini bilmez; kimlik ancak örnek kurulunca bellidir.
    Şifreli alanı olmayan modelde maliyet tek sözlük aramasıdır. `values()`
    sorgusu örnek kurmadığı için onun okuduğu işaret kayda düşmez; üretim kodu
    şifreli alanı model örneğiyle okur.
    """
    attnames = _sifreli_alan_onbellegi.get(sender)
    if attnames is None:
        attnames = tuple(alan.attname for alan in encrypted_fields_of(sender))
        _sifreli_alan_onbellegi[sender] = attnames
    for attname in attnames:
        deger = instance.__dict__.get(attname)
        if isinstance(deger, CorruptField):
            record_corrupt_read(deger.model_label, instance.pk, deger.field_name)


post_init.connect(_bozuk_alanlari_kaydet, weak=False, dispatch_uid="od-bozuk-alan-kaydi")


class EncryptedTextField(models.TextField):  # type: ignore[type-arg]  # Any davranışı korunur
    """Fernet ile şifreli saklanan metin alanı; anahtar yokken yazmaz (fail-closed).

    Python tarafında düz metin (str) gibi davranır. DB sütunu TEXT'tir,
    içerik base64 Fernet token'ıdır. Boş dize şifrelenmez.

    KİLİTLİYKEN OKUMA: anahtar yoksa `from_db_value` token'ı OLDUĞU GİBİ
    döndürür (okunamaz ama patlamaz); böyle okunmuş kaydı geri yazmak
    `KeyMissingError` verir (dolu değer anahtarsız yazılmaz).

    KİLİT AÇIKKEN OKUMA KATIDIR (tasarım §13 D48): çözülemeyen ya da token
    olmayan dolu değer `CorruptField` olarak döner; yazımda işaretin ham değeri
    aynen geri yazılır (`get_prep_value`), `clean`/`to_python` işareti metne
    çevirmez.
    """

    description = "Hesabın açtığı veri anahtarıyla Fernet ile şifrelenen metin alanı"

    def get_prep_value(self, value: Any) -> str | None:
        """Python değeri → DB'ye yazılacak şifreli metin; anahtar yoksa `KeyMissingError`."""
        if value is None:
            return None
        if isinstance(value, CorruptField):
            # Bozuk değer olduğu gibi geri yazılır: işaret ŞİFRELENİP meşru veriye
            # dönmez, bozukluk kayıtta görünür kalır (plan F1b-1, D48).
            return value.raw
        text = str(value)
        # Boş dize ŞİFRELENMEZ: "veri yok" hâli DB'de de boş görünmeli — kısmi
        # tekillik kısıtları ve `blank=True` semantiği buna dayanır.
        if text == "":
            return ""
        fernet = _holder.fernet()
        if fernet is None:
            # Fail-closed (§5.3): düz metin yazmak yerine dur.
            raise KeyMissingError()
        return fernet.encrypt(text.encode("utf-8")).decode("ascii")

    def from_db_value(
        self, value: Any, expression: Any, connection: Any
    ) -> str | CorruptField | None:
        """DB'den okunan metin → düz metin; kilit açıkken çözülemeyen → `CorruptField`."""
        if value is None or value == "":
            return cast("str | None", value)
        fernet = _holder.fernet()
        if fernet is None:
            # Kilitli: token çözülemez, olduğu gibi döner (okunamaz ama patlamaz).
            return cast("str | None", value)
        try:
            return fernet.decrypt(str(value).encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError):
            # Token değil (düz metin; Türkçe harfli değer tanım gereği tokensızdır,
            # UnicodeEncodeError) ya da bu DEK'in token'ı değil: KATI KİP (D48).
            model = getattr(self, "model", None)
            etiket = model._meta.label if model is not None else ""
            return CorruptField(str(value), model_label=etiket, field_name=self.name or "")

    def to_python(self, value: Any) -> Any:
        """`CorruptField` metne çevrilmez (aksi hâlde `full_clean` işareti "" yapardı)."""
        if isinstance(value, CorruptField):
            return value
        return super().to_python(value)

    def clean(self, value: Any, model_instance: models.Model | None) -> Any:
        """İşaretli değer doğrulanmadan aynen kalır (uzunluk denetimi metin ister)."""
        if isinstance(value, CorruptField):
            return value
        return super().clean(value, model_instance)


class EncryptedCharField(EncryptedTextField):
    """CharField arayüzlü şifreli alan (form/serializer `max_length` doğrulaması için)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Şifreli token düz metinden uzundur → DB sütunu TEXT kalır; max_length
        # YALNIZ doğrulama amaçlıdır. Atama super SONRASINDA: `Field.__init__`
        # kendi (None) değeriyle ezer (aileden gelen ders).
        max_length = kwargs.pop("max_length", None)
        super().__init__(*args, **kwargs)
        self.max_length = max_length

    def deconstruct(self) -> tuple[str, str, list[Any], dict[str, Any]]:
        """Göç dosyasına `max_length`'i geri koyar (`__init__`'te pop'landı)."""
        name, path, args, kwargs = cast(
            "tuple[str, str, list[Any], dict[str, Any]]", super().deconstruct()
        )
        if self.max_length is not None:
            kwargs["max_length"] = self.max_length
        return name, path, args, kwargs


def encrypted_fields_of(model: type[models.Model]) -> tuple[models.Field[Any, Any], ...]:
    """Modelin şifreli alanları (kayıt defteri elle tutulmaz, koddan okunur)."""
    return tuple(f for f in model._meta.get_fields() if isinstance(f, EncryptedTextField))
