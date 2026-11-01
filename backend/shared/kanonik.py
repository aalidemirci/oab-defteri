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


def esit(a: str, b: str) -> bool:
    """İki mührün sabit sürede karşılaştırılması (zamanlama sızıntısı olmasın)."""
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
