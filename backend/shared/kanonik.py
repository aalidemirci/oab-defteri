"""Kanonik kodlama — hesap mührünün, içerik MAC'inin ve zincirin tek biçimi (tasarım §4.6).

F1b-1 uygulama kararı (plan §2.2, "guvenlik.json şema 2"): mühür ve MAC'lerin
kodlaması TEK ve ORM'SİZ bir işlevdedir. Bugün hesap mührü (`Account.seal`,
tasarım §4.6.1) bu modülü kullanır; denetim izinin içerik MAC'i ve zinciri
(§4.6.2-§4.6.3) ve 2. adımda konsol geri yüklemesinin salt okunur `sqlite3`
denetimi (§4.4.4) aynı işlevi kullanacaktır. Bu yüzden modül yalnız standart
kitaplığa dayanır: Django içe aktarmaz, model örneği tanımaz; çağıran değerleri
sözlük olarak verir.

BİÇİM (bu adımda DONAR; kâğıda inen zincir başı buna bağlıdır):

* UTF-8 JSON; anahtarlar sıralı; ayırıcıda boşluk yok (`,` ve `:`);
  `ensure_ascii=False` (Türkçe harf kaçışsız, UTF-8 baytı olarak).
* Zaman (`datetime`): saat dilimli olmalıdır; UTC'ye çevrilir, ISO 8601,
  mikrosaniyeli, `Z` ekli (`2026-11-01T07:30:00.000000Z`). Saat dilimsiz zaman
  HATADIR: hangi ana ait olduğu bilinmeyen değer mühre giremez.
* Gün (`date`): ISO (`2026-11-01`).
* `Decimal`: metin (`str`), olduğu gibi (`"12.50"` ≠ `"12.5"`; ölçeği değer taşır).
* `UUID`: tireli metin.
* Yabancı anahtar kimliği YALNIZ kimliğin metnidir (çağıran `str(pk)` verir) ya da
  `null`; tamsayı verilmez. Aynı anahtar `5` ve `"5"` diye iki ayrı baytla
  kodlanabilseydi ORM yolu ile 2. adımın salt okunur `sqlite3` denetimi aynı satır
  için farklı mühür hesaplardı. Kodlayıcı alanın yabancı anahtar olduğunu bilemez
  (sayaç gibi alanlar meşru tamsayıdır); kuralı alanları adıyla tanıyan işlev
  uygular (`hesap_muhru`, `HESAP_MUHRU_YABANCI_ANAHTARLARI`).
* `None` → `null`; `bool`, `int`, `str` JSON'daki gibidir. Kayan nokta, bayt
  dizisi ve başka her tür HATADIR (`KanonikHata`): mühre sessizce `repr` girmez.
* İç içe sözlük ve liste aynı kurallarla kodlanır; sözlük anahtarı metin
  olmalıdır.

Biçim değişirse var olan bütün mühürler tutmaz olur; tasarım tutmayan mührün
yeniden hesaplanmasını yasaklar (§4.6.1 kural 1). Bu yüzden biçim
`test_kanonik.py`'deki donmuş örnekle (altın vektör) sabitlenir.

DENETİM İZİ (tasarım §4.6.2-§4.6.3; plan F1b-1 alt commit c). Aynı kodlayıcı üç
yerde kullanılır, üçü de altın vektörle donar:

* **Zincir** — `iz_mac`: `HMAC(HKDF(İA, "od-denetim-izi/v1"), kanonik(satır) ‖
  prev_mac)`. `kanonik(satır)` `IZ_SATIRI_ALANLARI`'nın sözlüğüdür; `prev_mac`
  kanoniğe GİRMEZ, onaltılık metninin ASCII baytları olarak SONA eklenir (ilk satırda
  boş dize). `term` ve `compliance_item` hedef modelleri F1c'de gelir; anahtarlar
  bugünden `null` olarak kanoniktedir (hesap mührünün `person`/`membership`/`term`
  deseni): sütunlar eklenince var olan MAC'ler değişmez. Hesap kimliği (`account`)
  UUID'nin TİRELİ metnidir (`str(uuid)`); SQLite sütunu tiresiz 32 hane saklar, salt
  okunur `sqlite3` denetimi tireli biçime çevirir.
* **İçerik MAC'i** — `kayit_mac`: `HMAC(HKDF(İA, "od-kayit-ozeti/v1"),
  kanonik({"model", "object_id", "fields"}))`; `fields` modelin özet alanlarının
  YAZMADAN SONRAKİ çözülmüş değerleridir (alan listesi modelde, `IZ_OZET_ALANLARI`).
* **Çözülemeyen şifreli alan** (tasarım §13 D48) — `bozuk_alan`: `CorruptField`
  metin değildir ve düz metne çevrilmez; içerik MAC'ine `{"bozuk": sha256(ham)}`
  sözlüğü olarak girer. Belirlenimcidir (aynı ham değer aynı MAC'i verir) ve şifreli
  alanın meşru değeri daima metin olduğu için meşru bir değerle çakışamaz. Düz metin
  yazılmış sütun ya da başka satırdan taşınmış token böylece MAC'i değiştirir;
  ham değerin kendisi hiçbir yere yazılmaz.

ÇAPA VE KİLİTLİ KİP (tasarım §4.6.3; plan F1b-1 alt commit c). Üç bayt biçimi daha
burada donar (altın vektörler `test_kanonik.py`'de):

* **`seq ‖ mac`** — `capa_baytlari`: çapanın mührünün (`muhur = HMAC(HKDF(İA,
  "od-iz-capa/v1"), seq ‖ mac)`) ve kilitli kip tohumunun tuzunun (`tohum₀ = HKDF(İA,
  "od-iz-kilitli/v1", tuz = seq ‖ mac)`) girdisi. Biçim: `seq`'in ondalık ASCII metni,
  `:` ayırıcısı, `mac`'in 64 haneli küçük harf onaltılık ASCII metni (`b"42:3fa1…"`).
  `mac` sabit uzunlukta olduğu için ayırıcısız da tek anlamlı olurdu; ayırıcı, değerin
  başka bir araçla elle yeniden üretilmesini kolaylaştırır.
* **İleri tohum** — `ileri_tohum`: `tohumₖ₊₁ = SHA-256("ileri" ‖ tohumₖ)`; "ileri"
  ASCII baytlarıdır, tohum 32 ham bayttır. Tek yönlüdür: bugünkü tohumdan dünkü
  bulunmaz (ileriye dönük güvenli mühür).
* **Mühürsüz kilitli satır** — `MUHURSUZ_ANAHTAR`: `iz-durumu.json` yok ya da bozukken
  kilitli kip satırı zincire yine bağlanır, ama sırsız (herkesin bildiği) bu anahtarla:
  `SHA-256("od-iz-muhursuz/v1")`. Satırın `key_ref`'i boştur; doğrulama onu "çapa yok"
  bulgusuyla gösterir. Zincir böylece kopmaz, satır da mühürlü gibi görünmez.

Kâğıt çapasının zincir parçası (`zincir_kisaltmasi`: "Kayıt no: N · Zincir: XXXX-XXXX")
`mac`'in ilk 8 onaltılık hanesidir, büyük harfle ve dörder hane tireyle (elle yazımda
okunurluk; tasarım §4.6.3 "Kâğıt çapası").
"""

from __future__ import annotations

import hmac
import json
from collections.abc import Mapping
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any
from uuid import UUID


class KanonikHata(TypeError):
    """Kanonik biçime giremeyen değer (saat dilimsiz zaman, desteklenmeyen tür)."""


def _deger(value: Any) -> Any:
    """Tek değeri JSON'un tanıdığı türe çevirir (kurallar modül başlığında)."""
    # bool, int'in alt sınıfıdır; ikisi de JSON'da olduğu gibi kalır.
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise KanonikHata("Saat dilimsiz zaman kanonik biçime giremez.")
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        sonuc: dict[str, Any] = {}
        for anahtar, ic in value.items():
            if not isinstance(anahtar, str):
                raise KanonikHata("Kanonik sözlüğün anahtarı metin olmalıdır.")
            sonuc[anahtar] = _deger(ic)
        return sonuc
    if isinstance(value, list | tuple):
        return [_deger(ic) for ic in value]
    raise KanonikHata(f"Kanonik biçimde desteklenmeyen tür: {type(value).__name__}")


def kodla(value: Mapping[str, Any]) -> bytes:
    """Sözlüğü kanonik UTF-8 JSON baytlarına çevirir (biçim modül başlığında)."""
    if not isinstance(value, Mapping):
        raise KanonikHata("Kanonik kodlamanın girdisi sözlük olmalıdır.")
    metin = json.dumps(
        _deger(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return metin.encode("utf-8")


def hmac_sha256(key: bytes, data: bytes) -> str:
    """`HMAC-SHA256(key, data)` — 64 onaltılık hane (küçük harf)."""
    return hmac.new(key, data, sha256).hexdigest()


def esit(a: object, b: object) -> bool:
    """İki mührün sabit sürede karşılaştırılması (zamanlama sızıntısı olmasın).

    Mühür metindir. Metin olmayan değer (program dışından metin sütununa yazılmış ikili değer:
    SQLite BLOB'u çevirmeden saklar) hiçbir mühre eşit değildir: False (fail-closed), hata
    yükseltip doğrulamayı yarıda kesmez.
    """
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    return hmac.compare_digest(a.encode("ascii", "replace"), b.encode("ascii", "replace"))


# ---------------------------------------------------------------------------
# Hesap mührü (tasarım §4.6.1)
# ---------------------------------------------------------------------------
#: Mühre giren `Account` alanları. `person`, `membership` ve `term`in hedef
#: modelleri F1c'de gelir; alanlar bugün de anahtar olarak (değeri `null`)
#: mühürdedir: alanlar eklenince var olan mühürler değişmez. `last_login_at`,
#: `password_changed_at`, sıfırlama alanları ve `display_name` mührün dışındadır
#: (oturum ve bildirim izleri; ad şifrelidir ve DEK yenilemesinde yeniden yazılır).
HESAP_MUHRU_ALANLARI: tuple[str, ...] = (
    "id",
    "login_name",
    "role",
    "status",
    "person",
    "membership",
    "term",
    "opened_at",
    "closed_at",
)
#: Hesap mührünün yabancı anahtar alanları: değer kimliğin METNİ ya da `None`dır.
HESAP_MUHRU_YABANCI_ANAHTARLARI: tuple[str, ...] = ("person", "membership", "term")


def hesap_muhru(seal_key: bytes, fields: Mapping[str, Any]) -> str:
    """`HMAC(mühür anahtarı, kanonik(hesap alanları))` — onaltılık mühür.

    `seal_key` DEK'ten `od-hesap-muhru/v1` bilgisiyle türeyen anahtardır
    (`shared.crypto.derive_subkey`); bu modül DEK görmez. `fields` en az
    `HESAP_MUHRU_ALANLARI`'nı taşır; fazlası mühre GİRMEZ (yanlışlıkla eklenen alan
    mührü sessizce değiştirmesin). Eksik alan hatadır; yabancı anahtar alanında
    metin ya da `None` dışındaki değer (tamsayı kimlik dahil) de hatadır (modül
    başlığı: biçim tektir).
    """
    eksik = [ad for ad in HESAP_MUHRU_ALANLARI if ad not in fields]
    if eksik:
        raise KanonikHata(f"Hesap mühründe eksik alan: {', '.join(eksik)}")
    for ad in HESAP_MUHRU_YABANCI_ANAHTARLARI:
        deger = fields[ad]
        if deger is not None and not isinstance(deger, str):
            raise KanonikHata(
                f"Yabancı anahtar ({ad}) kimliğin metni olarak verilir (str(pk)); "
                f"verilen tür: {type(deger).__name__}"
            )
    yuk = {ad: fields[ad] for ad in HESAP_MUHRU_ALANLARI}
    return hmac_sha256(seal_key, kodla(yuk))


def duz(value: Any) -> Any:
    """Değeri JSON'a yazılacak İLKEL kanonik biçimine çevirir (zaman UTC `Z` metni vb.).

    Denetim izinin `values` sütunu değerleri bu biçimde saklar: satır doğrulanırken
    veritabanından okunan JSON aynı baytlara kodlanır (biçim modül başlığında).
    """
    return _deger(value)


# ---------------------------------------------------------------------------
# Denetim izi satırı (tasarım §4.6.2-§4.6.3)
# ---------------------------------------------------------------------------
#: Zincir MAC'inin kapsadığı `AuditTrail` alanları — satırın kanonik biçimi. `prev_mac`
#: kanoniğe girmez, sona eklenir; `mac` satırın kendi sonucudur (modül başlığı).
IZ_SATIRI_ALANLARI: tuple[str, ...] = (
    "seq",
    "at",
    "actor",
    "account",
    "role",
    "action",
    "model",
    "object_id",
    "term",
    "changed_fields",
    "values",
    "record_mac",
    "compliance_item",
    "label",
    "key_mode",
    "key_ref",
)
#: Satırın yabancı anahtar alanları: değer kimliğin METNİ ya da `None`dır. `term` ve
#: `compliance_item` F1c'ye dek daima `None`dır.
IZ_SATIRI_YABANCI_ANAHTARLARI: tuple[str, ...] = ("account", "term", "compliance_item")
#: Satırın metin alanları (boş olabilir, `None` olamaz).
_IZ_SATIRI_METINLERI: tuple[str, ...] = (
    "actor",
    "role",
    "action",
    "model",
    "object_id",
    "record_mac",
    "label",
    "key_mode",
    "key_ref",
)
_ONALTILIK = frozenset("0123456789abcdef")


def _mac_metni_mi(deger: object) -> bool:
    """64 haneli küçük harf onaltılık metin mi? (HMAC-SHA256 çıktısı)"""
    return isinstance(deger, str) and len(deger) == 64 and set(deger) <= _ONALTILIK


def iz_satiri(fields: Mapping[str, Any]) -> bytes:
    """Denetim izi satırının kanonik baytları (`IZ_SATIRI_ALANLARI`; fazlası GİRMEZ).

    Eksik alan, tamsayı olmayan `seq`, metin olmayan yabancı anahtar, metin listesi
    olmayan `changed_fields`, `{alan: [önce, sonra]}` olmayan `values` HATADIR: biçim
    tektir, ORM yolu ile salt okunur `sqlite3` denetimi aynı satıra aynı baytı üretmelidir.
    """
    eksik = [ad for ad in IZ_SATIRI_ALANLARI if ad not in fields]
    if eksik:
        raise KanonikHata(f"Denetim izi satırında eksik alan: {', '.join(eksik)}")
    seq = fields["seq"]
    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 1:
        raise KanonikHata("Denetim izi satırının sırası (seq) en az 1 olan bir tamsayıdır.")
    if not isinstance(fields["at"], datetime):
        raise KanonikHata("Denetim izi satırının zamanı (at) saat dilimli bir zamandır.")
    for ad in IZ_SATIRI_YABANCI_ANAHTARLARI:
        deger = fields[ad]
        if deger is not None and not isinstance(deger, str):
            raise KanonikHata(
                f"Yabancı anahtar ({ad}) kimliğin metni olarak verilir (str(pk)); "
                f"verilen tür: {type(deger).__name__}"
            )
    for ad in _IZ_SATIRI_METINLERI:
        if not isinstance(fields[ad], str):
            raise KanonikHata(f"Denetim izi satırının {ad} alanı metindir.")
    degisen = fields["changed_fields"]
    if not isinstance(degisen, list | tuple) or not all(isinstance(a, str) for a in degisen):
        raise KanonikHata("changed_fields alan adlarının listesidir.")
    degerler = fields["values"]
    if not isinstance(degerler, Mapping) or not all(
        isinstance(cift, list | tuple) and len(cift) == 2 for cift in degerler.values()
    ):
        raise KanonikHata("values {alan: [önce, sonra]} biçimindedir.")
    return kodla({ad: fields[ad] for ad in IZ_SATIRI_ALANLARI})


def iz_mac(chain_key: bytes, fields: Mapping[str, Any], prev_mac: str) -> str:
    """Zincir MAC'i: `HMAC(zincir anahtarı, kanonik(satır) ‖ prev_mac)` (tasarım §4.6.3).

    `chain_key` İA'dan `od-denetim-izi/v1` bilgisiyle türeyen anahtardır (kilitli kipte
    kilitli kip tohumundan türeyen anahtar; alt commit c'nin kilitli kipi); bu modül İA
    görmez. `prev_mac` önceki satırın MAC'idir, ilk satırda boş dize.
    """
    if prev_mac != "" and not _mac_metni_mi(prev_mac):
        raise KanonikHata("prev_mac boş ya da 64 haneli küçük harf onaltılık metindir.")
    return hmac_sha256(chain_key, iz_satiri(fields) + prev_mac.encode("ascii"))


# ---------------------------------------------------------------------------
# İçerik MAC'i — "kaydın özeti" (tasarım §4.6.2)
# ---------------------------------------------------------------------------
#: `CorruptField`'ın içerik MAC'indeki temsilinin anahtarı (modül başlığı).
BOZUK_ALAN_ANAHTARI = "bozuk"


def bozuk_alan(ham: str) -> dict[str, str]:
    """Çözülemeyen şifreli alanın içerik MAC'indeki temsili: `{"bozuk": sha256(ham)}`.

    Ham değer düz metin kişi verisi olabilir: kendisi değil özeti girer, o da yalnız
    anahtarlı MAC'in girdisidir (hiçbir sütuna yazılmaz).
    """
    return {BOZUK_ALAN_ANAHTARI: sha256(ham.encode("utf-8")).hexdigest()}


def kayit_ozeti(model: str, object_id: str, fields: Mapping[str, Any]) -> bytes:
    """İçerik MAC'inin kanonik baytları: `{"fields", "model", "object_id"}`.

    `model` modelin etiketi (`okul.Account`), `object_id` kaydın kimliğinin metnidir;
    `fields` özet alanlarının değerleridir (yabancı anahtar kimliğin metni, şifreli alan
    çözülmüş metni ya da `bozuk_alan` temsili).
    """
    if not isinstance(model, str) or not isinstance(object_id, str):
        raise KanonikHata("İçerik MAC'inde model ve object_id metindir.")
    if not isinstance(fields, Mapping):
        raise KanonikHata("İçerik MAC'inin alanları sözlüktür.")
    return kodla({"model": model, "object_id": object_id, "fields": fields})


def kayit_mac(summary_key: bytes, model: str, object_id: str, fields: Mapping[str, Any]) -> str:
    """İçerik MAC'i: `HMAC(HKDF(İA, "od-kayit-ozeti/v1"), kayit_ozeti(...))` (§4.6.2).

    `summary_key` İA'dan `od-kayit-ozeti/v1` bilgisiyle türeyen anahtardır; bu modül İA
    görmez.
    """
    return hmac_sha256(summary_key, kayit_ozeti(model, object_id, fields))


# ---------------------------------------------------------------------------
# Çapa ve kilitli kip (tasarım §4.6.3)
# ---------------------------------------------------------------------------
#: İleri tohumun öneki (`tohumₖ₊₁ = SHA-256("ileri" ‖ tohumₖ)`).
ILERI_ONEKI = b"ileri"
#: Kilitli kip tohumunun uzunluğu (bayt; HKDF ve SHA-256 çıktısı).
TOHUM_BAYT = 32
#: Mühürsüz kilitli satırın zincir anahtarı — sırsızdır (modül başlığı).
MUHURSUZ_ANAHTAR = sha256(b"od-iz-muhursuz/v1").digest()


def capa_baytlari(seq: int, mac: str) -> bytes:
    """`seq ‖ mac` — çapanın mührünün ve kilitli kip tohumunun tuzunun baytları (modül başlığı).

    `seq` en az 1 olan tamsayı, `mac` 64 haneli küçük harf onaltılık metindir; başkası
    HATADIR (biçim tektir).
    """
    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 1:
        raise KanonikHata("Çapanın sırası (seq) en az 1 olan bir tamsayıdır.")
    if not _mac_metni_mi(mac):
        raise KanonikHata("Çapanın MAC'i 64 haneli küçük harf onaltılık metindir.")
    return f"{seq}:{mac}".encode("ascii")


def capa_muhru(anchor_key: bytes, seq: int, mac: str) -> str:
    """Çapanın mührü: `HMAC(HKDF(İA, "od-iz-capa/v1"), seq ‖ mac)` (tasarım §4.6.3).

    `anchor_key` İA'dan `od-iz-capa/v1` bilgisiyle türeyen anahtardır; bu modül İA görmez.
    """
    return hmac_sha256(anchor_key, capa_baytlari(seq, mac))


def ileri_tohum(tohum: bytes) -> bytes:
    """Bir sonraki kilitli kip tohumu: `SHA-256("ileri" ‖ tohum)` (tasarım §4.6.3)."""
    if not isinstance(tohum, bytes) or len(tohum) != TOHUM_BAYT:
        raise KanonikHata("Kilitli kip tohumu 32 baytlık bir bayt dizisidir.")
    return sha256(ILERI_ONEKI + tohum).digest()


def zincir_kisaltmasi(mac: str) -> str:
    """Kâğıt çapasının zincir parçası: `mac`'in ilk 8 hanesi, büyük harf, `XXXX-XXXX`."""
    if not _mac_metni_mi(mac):
        raise KanonikHata("Zincir başının MAC'i 64 haneli küçük harf onaltılık metindir.")
    return f"{mac[:4]}-{mac[4:8]}".upper()
