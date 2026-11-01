"""`shared.kanonik` — mühür ve MAC'lerin kanonik biçimi (plan F1b-1; tasarım §4.6.1-§4.6.3).

Biçim bu adımda DONAR: hesap mühürleri ve ileride kâğıda inen zincir başı ona
bağlıdır. Altın vektörler biçimin sessizce kaymasını yakalar; değişirse var olan
bütün mühürler tutmaz olur (tasarım tutmayan mührün yeniden hesaplanmasını yasaklar).
DB istemez; modül Django içe aktarmaz.
"""

from __future__ import annotations

import ast
import hmac
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from shared import kanonik

ALTIN_HESAP = {
    "id": UUID("6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60"),
    "login_name": "yonetici",
    "role": "yonetici",
    "status": "ACIK",
    "person": None,
    "membership": None,
    "term": None,
    "opened_at": datetime(2026, 11, 1, 10, 30, tzinfo=ZoneInfo("Europe/Istanbul")),
    "closed_at": None,
}
ALTIN_HESAP_BAYTLARI = (
    b'{"closed_at":null,"id":"6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60","login_name":"yonetici",'
    b'"membership":null,"opened_at":"2026-11-01T07:30:00.000000Z","person":null,'
    b'"role":"yonetici","status":"ACIK","term":null}'
)
#: `hesap_muhru(bytes(range(32)), ALTIN_HESAP)` — DONMUŞ değer.
ALTIN_HESAP_MUHRU = "0f03c8e9d7e678e3c3296380c671a151070479fddac397971fc44ad8255a6f28"

#: Yabancı anahtarları dolu hesap (F1c'de `person`, `membership`, `term` dolar): kimliğin
#: METNİ (plan F1b-1). Uydurma kimlikler.
ALTIN_HESAP_BAGLI = {**ALTIN_HESAP, "person": "42", "membership": "7", "term": "3"}
ALTIN_HESAP_BAGLI_BAYTLARI = (
    b'{"closed_at":null,"id":"6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60","login_name":"yonetici",'
    b'"membership":"7","opened_at":"2026-11-01T07:30:00.000000Z","person":"42",'
    b'"role":"yonetici","status":"ACIK","term":"3"}'
)
#: `hesap_muhru(bytes(range(32)), ALTIN_HESAP_BAGLI)` — DONMUŞ değer.
ALTIN_HESAP_BAGLI_MUHRU = "8a224e5911fdb9714030aeff8881bdf65eea799910bded40d4a39d8da3475d92"

ALTIN_KARMA = {
    "ad": "Şükrü Çağlayan",
    "tutar": Decimal("12.50"),
    "gun": date(2026, 11, 1),
    "liste": [1, True, None],
    "ic": {"b": 1, "a": 2},
}
ALTIN_KARMA_METNI = (
    '{"ad":"Şükrü Çağlayan","gun":"2026-11-01","ic":{"a":2,"b":1},'
    '"liste":[1,true,null],"tutar":"12.50"}'
)
#: `hmac_sha256(b"anahtar", kodla(ALTIN_KARMA))` — DONMUŞ değer.
ALTIN_KARMA_MAC = "ee1b19efd6a6de5d457c2cf7233c362f56feee1a255f58fa6b806df85d4e0f87"


def test_altin_vektor_hesap_muhru() -> None:
    assert kanonik.kodla(ALTIN_HESAP) == ALTIN_HESAP_BAYTLARI
    assert kanonik.hesap_muhru(bytes(range(32)), ALTIN_HESAP) == ALTIN_HESAP_MUHRU
    # Mühür, kanonik baytların düz HMAC-SHA256'sıdır (ara dönüşüm yok).
    beklenen = hmac.new(bytes(range(32)), ALTIN_HESAP_BAYTLARI, sha256).hexdigest()
    assert beklenen == ALTIN_HESAP_MUHRU


def test_altin_vektor_yabanci_anahtar_kimligin_metnidir() -> None:
    """Plan F1b-1 "yabancı anahtar kimliğin metni": biçim F1c'deki ilk dolu satırdan önce donar."""
    assert kanonik.kodla(ALTIN_HESAP_BAGLI) == ALTIN_HESAP_BAGLI_BAYTLARI
    assert kanonik.hesap_muhru(bytes(range(32)), ALTIN_HESAP_BAGLI) == ALTIN_HESAP_BAGLI_MUHRU


@pytest.mark.parametrize("alan", kanonik.HESAP_MUHRU_YABANCI_ANAHTARLARI)
@pytest.mark.parametrize("deger", [42, True, UUID("6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60")])
def test_hesap_muhrunde_yabanci_anahtar_yalniz_metin(alan: str, deger: object) -> None:
    """Tek biçim: `42` ve `"42"` iki ayrı baytla kodlanıp iki yolda (ORM ve 2. adımın
    salt okunur `sqlite3` denetimi) aynı satıra farklı mühür vermesin."""
    with pytest.raises(kanonik.KanonikHata, match=alan):
        kanonik.hesap_muhru(bytes(range(32)), {**ALTIN_HESAP, alan: deger})
    assert set(kanonik.HESAP_MUHRU_YABANCI_ANAHTARLARI) <= set(kanonik.HESAP_MUHRU_ALANLARI)


def test_altin_vektor_karma_turler() -> None:
    """Türkçe harf kaçışsız UTF-8, iç içe sözlük sıralı, Decimal ölçeğiyle metin."""
    assert kanonik.kodla(ALTIN_KARMA) == ALTIN_KARMA_METNI.encode("utf-8")
    assert kanonik.hmac_sha256(b"anahtar", kanonik.kodla(ALTIN_KARMA)) == ALTIN_KARMA_MAC


def test_zaman_utc_ye_cevrilir_ve_mikrosaniyeli_z_ekli() -> None:
    an = datetime(2026, 1, 2, 3, 4, 5, 6, tzinfo=timezone(timedelta(hours=3)))
    assert kanonik.kodla({"t": an}) == b'{"t":"2026-01-02T00:04:05.000006Z"}'
    # Aynı an farklı saat dilimiyle verilse de aynı kodlanır.
    assert kanonik.kodla({"t": an.astimezone(UTC)}) == kanonik.kodla({"t": an})


def test_saat_dilimsiz_zaman_hatadir() -> None:
    with pytest.raises(kanonik.KanonikHata, match="Saat dilimsiz"):
        kanonik.kodla({"t": datetime(2026, 1, 1, 12, 0)})


@pytest.mark.parametrize("deger", [1.5, b"bayt", {1, 2}, object()])
def test_desteklenmeyen_tur_hatadir(deger: object) -> None:
    with pytest.raises(kanonik.KanonikHata):
        kanonik.kodla({"x": deger})


def test_sozluk_anahtari_metin_olmali() -> None:
    with pytest.raises(kanonik.KanonikHata, match="anahtarı metin"):
        kanonik.kodla({"x": {1: "a"}})


def test_girdi_sozluk_olmali() -> None:
    with pytest.raises(kanonik.KanonikHata):
        kanonik.kodla(["liste"])  # type: ignore[arg-type]


def test_anahtar_sirasi_kodlamayi_degistirmez() -> None:
    assert kanonik.kodla({"b": 1, "a": 2}) == kanonik.kodla({"a": 2, "b": 1})


def test_hesap_muhru_fazla_alani_almaz_eksik_alanda_hata_verir() -> None:
    fazlali = {**ALTIN_HESAP, "last_login_at": datetime.now(UTC), "display_name": "Örnek"}
    assert kanonik.hesap_muhru(bytes(range(32)), fazlali) == ALTIN_HESAP_MUHRU
    eksik = dict(ALTIN_HESAP)
    del eksik["term"]
    with pytest.raises(kanonik.KanonikHata, match="term"):
        kanonik.hesap_muhru(bytes(range(32)), eksik)


def test_hesap_muhru_alanlari_tasarimdaki_listedir() -> None:
    """Tasarım §4.6.1: kanonik(id, login_name, role, status, person, membership, term,
    opened_at, closed_at) — F1c alanları bugünden `null` olarak mühürdedir."""
    assert kanonik.HESAP_MUHRU_ALANLARI == (
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


def test_esit_sabit_surede_karsilastirir() -> None:
    assert kanonik.esit("ab", "ab") is True
    assert kanonik.esit("ab", "ac") is False


def test_modul_django_ice_aktarmaz() -> None:
    """2. adımda konsol geri yüklemesi aynı işlevi ORM'siz kullanır (plan F1b-1)."""
    kaynak = Path(kanonik.__file__).read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    moduller: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Import):
            moduller.update(ad.name.split(".")[0] for ad in dugum.names)
        elif isinstance(dugum, ast.ImportFrom) and dugum.module:
            moduller.add(dugum.module.split(".")[0])
    assert "django" not in moduller
    assert moduller <= {
        "__future__",
        "hmac",
        "json",
        "collections",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
        "uuid",
    }
