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
    # Sarmal özetleri (kullanıcı kararı 03.11.2026): asıl dolu, bekleyen boş (olağan hâl).
    "wrap_digest": "ab" * 32,
    "wrap_digest_pending": "",
}
ALTIN_HESAP_BAYTLARI = (
    b'{"closed_at":null,"id":"6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60","login_name":"yonetici",'
    b'"membership":null,"opened_at":"2026-11-01T07:30:00.000000Z","person":null,'
    b'"role":"yonetici","status":"ACIK","term":null,'
    b'"wrap_digest":"abababababababababababababababababababababababababababababababab",'
    b'"wrap_digest_pending":""}'
)
#: `hesap_muhru(bytes(range(32)), ALTIN_HESAP)` — DONMUŞ değer (03.11.2026'da özet alanlarıyla
#: yeniden dondu: program sahada değil, göç gerekmez — kullanıcı kararı 3).
ALTIN_HESAP_MUHRU = "2d0aa91ef58bdab7cfc2fc5c428823a7ed5e5c1ff0d87316b03d37043057d6c1"

#: Yabancı anahtarları dolu hesap (F1c'de `person`, `membership`, `term` dolar): kimliğin
#: METNİ (plan F1b-1). Uydurma kimlikler.
ALTIN_HESAP_BAGLI = {**ALTIN_HESAP, "person": "42", "membership": "7", "term": "3"}
ALTIN_HESAP_BAGLI_BAYTLARI = (
    b'{"closed_at":null,"id":"6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60","login_name":"yonetici",'
    b'"membership":"7","opened_at":"2026-11-01T07:30:00.000000Z","person":"42",'
    b'"role":"yonetici","status":"ACIK","term":"3",'
    b'"wrap_digest":"abababababababababababababababababababababababababababababababab",'
    b'"wrap_digest_pending":""}'
)
#: `hesap_muhru(bytes(range(32)), ALTIN_HESAP_BAGLI)` — DONMUŞ değer.
ALTIN_HESAP_BAGLI_MUHRU = "4fa1fbe9d9a7ac52cec7b995aed7278f2f32a03df6a1c74501348ea67408de6b"

#: Sarmal özeti (`kanonik.sarmal_ozeti`; kullanıcı kararı 03.11.2026). Uydurma tuz ve belirteç.
ALTIN_SARMAL = {
    "id": "6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60",
    "salt": "AAECAwQFBgcICQoLDA0ODw==",
    "sarmal": "gAAAAABu-ornek-belirtec",
}
ALTIN_SARMAL_BAYTLARI = (
    b'{"id":"6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60","salt":"AAECAwQFBgcICQoLDA0ODw==",'
    b'"sarmal":"gAAAAABu-ornek-belirtec"}'
)
#: `sarmal_ozeti(bytes(range(32)), ALTIN_SARMAL)` — DONMUŞ değer.
ALTIN_SARMAL_OZETI = "7cb945435dd8b2e2d509323847d8e508b71db89ad8b61610393a6d99c98c425d"

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


def test_altin_vektor_sarmal_ozeti() -> None:
    """Sarmal özetinin biçimi donar: ORM yolu (kilit açılışı) ile geri yüklemenin ORM'siz yolu
    aynı sarmala aynı özeti üretir; fazla alan (sayaç, askı, tanıtıcı, etiket) girmez."""
    assert kanonik.kodla(ALTIN_SARMAL) == ALTIN_SARMAL_BAYTLARI
    assert kanonik.sarmal_ozeti(bytes(range(32)), ALTIN_SARMAL) == ALTIN_SARMAL_OZETI
    beklenen = hmac.new(bytes(range(32)), ALTIN_SARMAL_BAYTLARI, sha256).hexdigest()
    assert beklenen == ALTIN_SARMAL_OZETI
    fazlali = {**ALTIN_SARMAL, "hatali": 3, "askida": True, "tanitici": "x", "turetim": "y"}
    assert kanonik.sarmal_ozeti(bytes(range(32)), fazlali) == ALTIN_SARMAL_OZETI


@pytest.mark.parametrize("alan", kanonik.SARMAL_OZETI_ALANLARI)
def test_sarmal_ozetinde_alan_eksik_ya_da_metin_disi_hatadir(alan: str) -> None:
    eksik = {ad: deger for ad, deger in ALTIN_SARMAL.items() if ad != alan}
    with pytest.raises(kanonik.KanonikHata, match=alan):
        kanonik.sarmal_ozeti(bytes(range(32)), eksik)
    with pytest.raises(kanonik.KanonikHata, match=alan):
        kanonik.sarmal_ozeti(bytes(range(32)), {**ALTIN_SARMAL, alan: b"bayt"})


@pytest.mark.parametrize("alan", kanonik.HESAP_MUHRU_METINLERI)
@pytest.mark.parametrize("deger", [None, b"ab", 42])
def test_hesap_muhrunde_ozet_alanlari_yalniz_metin(alan: str, deger: object) -> None:
    """Özet alanı metindir (boş metin "özet yok"); `None` ve ikili değer mühre girmez."""
    with pytest.raises(kanonik.KanonikHata, match=alan):
        kanonik.hesap_muhru(bytes(range(32)), {**ALTIN_HESAP, alan: deger})


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
    opened_at, closed_at) — F1c alanları bugünden `null` olarak mühürdedir — ve sarmal özetleri
    (kullanıcı kararı 03.11.2026 "tazelik kapatılır")."""
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
        "wrap_digest",
        "wrap_digest_pending",
    )


def test_esit_sabit_surede_karsilastirir() -> None:
    assert kanonik.esit("ab", "ab") is True
    assert kanonik.esit("ab", "ac") is False


@pytest.mark.parametrize("deger", [b"ab", bytearray(b"ab"), None, 171])
def test_esit_metin_olmayan_degerde_hata_yukseltmez_tutmaz(deger: object) -> None:
    """Program dışından metin sütununa yazılmış ikili değer (BLOB) mühür değildir: False;
    `AttributeError` doğrulamayı yarıda kesip öteki bulguları kaybettiriyordu."""
    assert kanonik.esit(deger, "ab") is False
    assert kanonik.esit("ab", deger) is False


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


# ---------------------------------------------------------------------------
# Denetim izi: zincir satırı ve içerik MAC'i (tasarım §4.6.2-§4.6.3; plan F1b-1 alt commit c)
# ---------------------------------------------------------------------------
#: Zincir vektörlerinin örnek MAC'leri: hesap mührünün özet alanlarından ÖNCEKİ altın değerleri
#: (03.11.2026). Zincir satırının biçimi değişmedi; vektörü mühürden ayırmak için sabittir.
ORNEK_RECORD_MAC = "0f03c8e9d7e678e3c3296380c671a151070479fddac397971fc44ad8255a6f28"
ORNEK_PREV_MAC = "8a224e5911fdb9714030aeff8881bdf65eea799910bded40d4a39d8da3475d92"

ALTIN_IZ_SATIRI: dict[str, object] = {
    "seq": 7,
    "at": datetime(2026, 11, 1, 10, 30, 15, 123456, tzinfo=ZoneInfo("Europe/Istanbul")),
    "actor": "HESAP",
    "account": "6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60",
    "role": "yonetici",
    "action": "GUNCELLE",
    "model": "okul.SchoolConfig",
    "object_id": "1",
    "term": None,
    "changed_fields": ["idle_lock_minutes", "updated_at"],
    "values": {"idle_lock_minutes": [10, 15]},
    "record_mac": ORNEK_RECORD_MAC,
    "compliance_item": None,
    "label": "",
    "key_mode": "ACIK",
    "key_ref": "1",
}
ALTIN_IZ_SATIRI_BAYTLARI = (
    b'{"account":"6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60","action":"GUNCELLE","actor":"HESAP",'
    b'"at":"2026-11-01T07:30:15.123456Z","changed_fields":["idle_lock_minutes","updated_at"],'
    b'"compliance_item":null,"key_mode":"ACIK","key_ref":"1","label":"",'
    b'"model":"okul.SchoolConfig","object_id":"1",'
    b'"record_mac":"0f03c8e9d7e678e3c3296380c671a151070479fddac397971fc44ad8255a6f28",'
    b'"role":"yonetici","seq":7,"term":null,"values":{"idle_lock_minutes":[10,15]}}'
)
#: `iz_mac(bytes(range(32)), ALTIN_IZ_SATIRI, ORNEK_PREV_MAC)` — DONMUŞ değer.
ALTIN_IZ_MAC = "c3ed8364e85586483986d3656d9f64519d34dd96d8be6305468a4fded57fa3b6"
#: Aynı satır zincirin ilk satırı olsaydı (`seq = 1`, `prev_mac` boş) — DONMUŞ değer.
ALTIN_IZ_ILK_MAC = "a5f981a49fc97cef177fa32e203d83c5e3613e00a14d251fd00ad4ab1b5e5d6e"

#: İçerik MAC'inin özeti: şifreli ad çözülmüş metniyle, bozuk alan temsiliyle (uydurma ad).
ALTIN_OZET_ALANLARI: dict[str, object] = {
    "login_name": "yonetici",
    "display_name": "Örnek Yönetici",
    "status": "ACIK",
    "opened_at": datetime(2026, 11, 1, 10, 30, tzinfo=ZoneInfo("Europe/Istanbul")),
    "opened_by": None,
    "reset_notice_pending": False,
    "seal": kanonik.bozuk_alan("düz metin"),
}
ALTIN_OZET_METNI = (
    '{"fields":{"display_name":"Örnek Yönetici","login_name":"yonetici",'
    '"opened_at":"2026-11-01T07:30:00.000000Z","opened_by":null,'
    '"reset_notice_pending":false,'
    '"seal":{"bozuk":"6d658e73854f5f47c0ee72025304264c9ee37b16633d67774e26319989a5cf1e"},'
    '"status":"ACIK"},"model":"okul.Account","object_id":"6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60"}'
)
#: `kayit_mac(bytes(range(32)), "okul.Account", ALTIN_HESAP["id"] metni, ...)` — DONMUŞ değer.
ALTIN_OZET_MAC = "478cfa8eca3bf2666c0223e4aca7b4c66b8b9d4080537c0bb30f20184aae2b46"


def test_altin_vektor_iz_satiri_ve_zincir_mac() -> None:
    """Zincir başı kâğıda iner (§4.6.3 kâğıt çapası): biçim bu vektörle DONAR."""
    assert kanonik.iz_satiri(ALTIN_IZ_SATIRI) == ALTIN_IZ_SATIRI_BAYTLARI
    assert kanonik.iz_mac(bytes(range(32)), ALTIN_IZ_SATIRI, ORNEK_PREV_MAC) == (ALTIN_IZ_MAC)
    # MAC, kanonik baytlara önceki MAC'in ASCII baytları eklenerek alınan düz HMAC'tir.
    beklenen = hmac.new(
        bytes(range(32)), ALTIN_IZ_SATIRI_BAYTLARI + ORNEK_PREV_MAC.encode(), sha256
    ).hexdigest()
    assert beklenen == ALTIN_IZ_MAC


def test_altin_vektor_zincirin_ilk_satiri_bos_onceki_macla() -> None:
    ilk = {**ALTIN_IZ_SATIRI, "seq": 1}
    assert kanonik.iz_mac(bytes(range(32)), ilk, "") == ALTIN_IZ_ILK_MAC


def test_iz_satirinda_term_ve_gerekce_bagi_bugunden_null() -> None:
    """F1c'de `term` ve `compliance_item` sütunları eklenince var olan MAC'ler değişmez."""
    assert {"term", "compliance_item"} <= set(kanonik.IZ_SATIRI_ALANLARI)
    assert b'"term":null' in ALTIN_IZ_SATIRI_BAYTLARI
    assert b'"compliance_item":null' in ALTIN_IZ_SATIRI_BAYTLARI


def test_iz_satiri_alanlari_tasarimdaki_listedir() -> None:
    """Tasarım §4.6.2 tablosu: `prev_mac` ve `mac` kanoniğe girmez (MAC'in girdisi/çıktısı)."""
    assert kanonik.IZ_SATIRI_ALANLARI == (
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


def test_iz_satiri_fazla_alani_almaz() -> None:
    fazlali = {**ALTIN_IZ_SATIRI, "prev_mac": "x", "mac": "y", "gizli": "Örnek Veli"}
    assert kanonik.iz_satiri(fazlali) == ALTIN_IZ_SATIRI_BAYTLARI


@pytest.mark.parametrize(
    ("alan", "deger"),
    [
        ("seq", 0),
        ("seq", True),
        ("seq", "7"),
        ("at", "2026-11-01"),
        ("account", 42),
        ("term", 3),
        ("compliance_item", UUID("6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60")),
        ("role", None),
        ("key_ref", 1),
        ("changed_fields", "idle_lock_minutes"),
        ("changed_fields", [1]),
        ("values", {"idle_lock_minutes": 15}),
        ("values", {"idle_lock_minutes": [10, 15, 20]}),
    ],
)
def test_iz_satirinin_bicimi_tektir(alan: str, deger: object) -> None:
    with pytest.raises(kanonik.KanonikHata):
        kanonik.iz_satiri({**ALTIN_IZ_SATIRI, alan: deger})


def test_iz_satirinda_eksik_alan_hatadir() -> None:
    eksik = dict(ALTIN_IZ_SATIRI)
    del eksik["term"]
    with pytest.raises(kanonik.KanonikHata, match="term"):
        kanonik.iz_satiri(eksik)


@pytest.mark.parametrize("prev_mac", ["abc", "G" * 64, ALTIN_IZ_MAC.upper()])
def test_onceki_mac_bos_ya_da_64_haneli_kucuk_harf_onaltiliktir(prev_mac: str) -> None:
    with pytest.raises(kanonik.KanonikHata, match="prev_mac"):
        kanonik.iz_mac(bytes(range(32)), ALTIN_IZ_SATIRI, prev_mac)


def test_altin_vektor_icerik_mac_ve_bozuk_alan_temsili() -> None:
    """§4.6.2 içerik MAC'i: model, kimlik, özet alanları; bozuk alan `{"bozuk": sha256}`."""
    baytlar = kanonik.kayit_ozeti(
        "okul.Account", "6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60", ALTIN_OZET_ALANLARI
    )
    assert baytlar == ALTIN_OZET_METNI.encode("utf-8")
    assert (
        kanonik.kayit_mac(
            bytes(range(32)),
            "okul.Account",
            "6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60",
            ALTIN_OZET_ALANLARI,
        )
        == ALTIN_OZET_MAC
    )


def test_bozuk_alan_temsili_belirlenimci_ve_ham_degeri_tasimaz() -> None:
    """D48: çözülemeyen alan düz metne çevrilmez; temsil ham değerin özetidir, kendisi değil."""
    temsil = kanonik.bozuk_alan("Örnek Veli 0532 000 00 00")
    assert temsil == kanonik.bozuk_alan("Örnek Veli 0532 000 00 00")
    assert temsil != kanonik.bozuk_alan("Örnek Veli 0532 000 00 01")
    assert list(temsil) == [kanonik.BOZUK_ALAN_ANAHTARI]
    assert "Örnek" not in kanonik.kodla({"x": temsil}).decode("utf-8")
    # Şifreli alanın meşru değeri metindir: temsil (sözlük) hiçbir metinle aynı kodlanmaz.
    assert kanonik.kodla({"x": temsil}) != kanonik.kodla({"x": temsil["bozuk"]})


def test_duz_deger_json_ilkel_bicimdir() -> None:
    an = datetime(2026, 11, 1, 10, 30, tzinfo=ZoneInfo("Europe/Istanbul"))
    assert kanonik.duz(an) == "2026-11-01T07:30:00.000000Z"
    assert kanonik.duz(date(2026, 11, 1)) == "2026-11-01"
    assert kanonik.duz(Decimal("12.50")) == "12.50"
    assert kanonik.duz([None, True, 3]) == [None, True, 3]


# ---------------------------------------------------------------------------
# Çapa ve kilitli kip (tasarım §4.6.3; plan F1b-1 alt commit c)
# ---------------------------------------------------------------------------
#: `seq ‖ mac` için altın vektör: ondalık seq, `:`, 64 haneli mac (ASCII) — DONMUŞ biçim.
ALTIN_CAPA_BAYTLARI = b"7:" + ALTIN_IZ_MAC.encode("ascii")
#: `capa_muhru(bytes(range(32)), 7, ALTIN_IZ_MAC)` — DONMUŞ değer.
ALTIN_CAPA_MUHRU = "ac66e9887d01b34a72a6878c002b5568d91d78f141d71b30da2877540bf2a97c"
#: `ileri_tohum(bytes(range(32)))` — DONMUŞ değer.
ALTIN_ILERI_TOHUM = "e2c2f3b847ef759fdc28bb63edb3d0632fb6d0a87d91aa0e1ee30874dccf11a0"
#: `MUHURSUZ_ANAHTAR` = SHA-256("od-iz-muhursuz/v1") — DONMUŞ değer.
ALTIN_MUHURSUZ_ANAHTAR = "a52137f0bfe627b7b24442fab86013d70034909656336f3885f685c77e82ea83"


def test_altin_vektor_capa_baytlari_ve_muhru() -> None:
    """Çapanın `seq ‖ mac` biçimi ve mührü DONAR (kâğıda inen çapa ve tohum ona bağlıdır)."""
    assert kanonik.capa_baytlari(7, ALTIN_IZ_MAC) == ALTIN_CAPA_BAYTLARI
    assert kanonik.capa_muhru(bytes(range(32)), 7, ALTIN_IZ_MAC) == ALTIN_CAPA_MUHRU
    beklenen = hmac.new(bytes(range(32)), ALTIN_CAPA_BAYTLARI, sha256).hexdigest()
    assert beklenen == ALTIN_CAPA_MUHRU


@pytest.mark.parametrize(
    ("seq", "mac"),
    [(0, ALTIN_IZ_MAC), (True, ALTIN_IZ_MAC), ("7", ALTIN_IZ_MAC), (7, "abc"), (7, "G" * 64)],
)
def test_capa_baytlarinin_bicimi_tektir(seq: object, mac: str) -> None:
    with pytest.raises(kanonik.KanonikHata):
        kanonik.capa_baytlari(seq, mac)  # type: ignore[arg-type]


def test_altin_vektor_ileri_tohum_tek_yonlu_zincirdir() -> None:
    """`tohumₖ₊₁ = SHA-256("ileri" ‖ tohumₖ)`; yanlış uzunluk hatadır."""
    tohum = bytes(range(32))
    ileri = kanonik.ileri_tohum(tohum)
    assert ileri.hex() == ALTIN_ILERI_TOHUM
    assert ileri == sha256(b"ileri" + tohum).digest()
    assert kanonik.ileri_tohum(ileri) != tohum
    with pytest.raises(kanonik.KanonikHata):
        kanonik.ileri_tohum(b"\x00" * 31)


def test_muhursuz_anahtar_sirsiz_ve_donmustur() -> None:
    assert kanonik.MUHURSUZ_ANAHTAR.hex() == ALTIN_MUHURSUZ_ANAHTAR
    assert kanonik.MUHURSUZ_ANAHTAR == sha256(b"od-iz-muhursuz/v1").digest()


def test_kagit_capasinin_zincir_parcasi() -> None:
    """Kâğıt çapası "Kayıt no: N · Zincir: XXXX-XXXX": mac'in ilk 8 hanesi, büyük harf."""
    assert kanonik.zincir_kisaltmasi(ALTIN_IZ_MAC) == "C3ED-8364"
    with pytest.raises(kanonik.KanonikHata):
        kanonik.zincir_kisaltmasi("kisa")
