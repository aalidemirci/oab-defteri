"""`shared.crypto` birim testleri — fail-closed alan, kör indeks (tasarım §5.3), anahtar sayacı.

DB istemez: alan davranışı `get_prep_value` üzerinden, kör indeks doğrudan
sınanır. Varsayılan ortam `backend/conftest.py`'dedir (anahtar `TEST_DEK` yüklü).
"""

from __future__ import annotations

import hmac
import re
from hashlib import sha256
from pathlib import Path

import pytest
from cryptography.fernet import InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from conftest import TEST_DEK
from shared import crypto

_ALAN = crypto.EncryptedCharField("ad", max_length=100)


# ---------------------------------------------------------------------------
# Fail-closed şifreli alan (§5.3)
# ---------------------------------------------------------------------------
def test_anahtar_yokken_bos_olmayan_deger_yazilmaz(kilitli: Path) -> None:
    with pytest.raises(crypto.KeyMissingError):
        _ALAN.get_prep_value("EMRE")


def test_anahtar_yokken_bos_dize_ve_none_serbest(kilitli: Path) -> None:
    assert _ALAN.get_prep_value("") == ""
    assert _ALAN.get_prep_value(None) is None


def test_anahtar_varken_token_yazilir_ve_cozulur() -> None:
    token = _ALAN.get_prep_value("EMRE")
    assert token is not None and token.startswith("gAAAA")
    assert "EMRE" not in token
    assert _ALAN.from_db_value(token, None, None) == "EMRE"


def test_kilitliyken_okuma_tokeni_oldugu_gibi_dondurur() -> None:
    token = _ALAN.get_prep_value("EMRE")
    crypto.unload_key()
    assert _ALAN.from_db_value(token, None, None) == token


def test_key_missing_error_runtime_error_alt_sinifidir() -> None:
    """Servis `ValueError` çevirisi (400) onu yutmamalı: 409'a giden yol ayrıdır."""
    assert issubclass(crypto.KeyMissingError, RuntimeError)
    assert not issubclass(crypto.KeyMissingError, ValueError)


# ---------------------------------------------------------------------------
# Kör indeks (§5.3)
# ---------------------------------------------------------------------------
def test_kor_indeks_belirlenimci_ve_64_haneli() -> None:
    ilk = crypto.blind_index("1234")
    assert ilk == crypto.blind_index("1234")
    assert re.fullmatch(r"[0-9a-f]{64}", ilk)
    assert crypto.blind_index("1235") != ilk


def test_kor_indeks_tasarimdaki_formulle_hesaplanir() -> None:
    """HMAC-SHA256(HKDF-SHA256(DEK, salt=None, info="od-kor-indeks", 32), değer)."""
    anahtar = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"od-kor-indeks").derive(
        TEST_DEK
    )
    beklenen = hmac.new(anahtar, "Öğrenci-42".encode(), sha256).hexdigest()
    assert crypto.blind_index("Öğrenci-42") == beklenen


def test_kor_indeks_farkli_dekte_farklidir() -> None:
    ilk = crypto.blind_index("1234")
    crypto.load_key(b"\x07" * 32)
    assert crypto.blind_index("1234") != ilk


def test_kor_indeks_yeniden_yuklemede_ayni_kalir() -> None:
    """Anahtar yalnız DEK'e bağlıdır (parola değişimi DEK'i değiştirmez; uçtan uca
    kanıtı `test_app_password.py::test_kor_indeks_parola_degisiminden_sonra_ayni_kalir`)."""
    ilk = crypto.blind_index("1234")
    crypto.unload_key()
    crypto.load_key(TEST_DEK)
    assert crypto.blind_index("1234") == ilk


def test_kor_indeks_bos_dizede_bos_doner(kilitli: Path) -> None:
    assert crypto.blind_index("") == ""


def test_kor_indeks_kilitliyken_key_missing_error(kilitli: Path) -> None:
    with pytest.raises(crypto.KeyMissingError):
        crypto.blind_index("1234")


def test_kor_indeks_normallestirme_yapmaz() -> None:
    """Normalleştirme çağıranın işidir: "0123" ile "123" farklı indeks verir."""
    assert crypto.blind_index("0123") != crypto.blind_index("123")


# ---------------------------------------------------------------------------
# Anahtar sayacı (teşhis ve test içindir; oturum açılışı buradan çıkarılmaz)
# ---------------------------------------------------------------------------
def test_key_epoch_yukleme_ve_bosaltmada_artar() -> None:
    ilk = crypto.key_epoch()
    crypto.unload_key()
    assert crypto.key_epoch() == ilk + 1
    crypto.load_key(TEST_DEK)
    assert crypto.key_epoch() == ilk + 2
    crypto.load_key(TEST_DEK)  # aynı anahtarın yeniden yüklenmesi de yeni açılıştır
    assert crypto.key_epoch() == ilk + 3


def test_kaldirilan_duz_yazma_araclari_yoktur() -> None:
    for ad in ("plaintext_writes", "writes_encrypted"):
        assert not hasattr(crypto, ad), ad
    assert not hasattr(crypto._holder, "_encrypt_writes")


# ---------------------------------------------------------------------------
# Katı kip (tasarım TK8 (3), §13 D48; F1 kapısı `test_from_db_value_kati_kip`)
# ---------------------------------------------------------------------------
class _SahteModel:
    """`from_db_value`'nun okuduğu `_meta.label` için en küçük taklit."""

    class _meta:  # noqa: N801 — Django'nun `_meta` adı
        label = "okul.Ornek"


def _kati_alan() -> crypto.EncryptedCharField:
    alan = crypto.EncryptedCharField("ad", max_length=100)
    alan.name = "first_name"
    alan.model = _SahteModel  # type: ignore[assignment]
    return alan


def test_from_db_value_kati_kip() -> None:
    """Kilit açıkken token olmayan ya da bu DEK'in olmayan dolu değer METİN DÖNMEZ."""
    alan = _kati_alan()
    # 1) SQLite'ta şifreli sütuna yazılmış düz metin (Türkçe harfli ve ASCII).
    for duz in ("ŞÜKRÜ", "EMRE"):
        okunan = alan.from_db_value(duz, None, None)
        assert isinstance(okunan, crypto.CorruptField)
        assert not isinstance(okunan, str)
        assert okunan.raw == duz
        assert okunan.model_label == "okul.Ornek" and okunan.field_name == "first_name"
    # 2) Başka bir DEK'in token'ı (satırdan satıra taşınmış ya da başka kurulum).
    crypto.load_key(b"\x09" * 32)
    yabanci = alan.get_prep_value("AYŞE")
    crypto.load_key(TEST_DEK)
    assert isinstance(alan.from_db_value(yabanci, None, None), crypto.CorruptField)
    # 3) Kendi token'ı çözülür; boş ve None olduğu gibi kalır.
    token = alan.get_prep_value("AYŞE")
    assert alan.from_db_value(token, None, None) == "AYŞE"
    assert alan.from_db_value("", None, None) == ""
    assert alan.from_db_value(None, None, None) is None


def test_kilitliyken_kati_kip_uygulanmaz_token_aynen_doner(kilitli: Path) -> None:
    """Anahtar yokken çözme denenmez: değer olduğu gibi döner (okunamaz ama patlamaz)."""
    assert _kati_alan().from_db_value("EMRE", None, None) == "EMRE"


def test_bozuk_alan_isareti_yazilirken_ham_deger_aynen_doner() -> None:
    """İşaret şifrelenip meşru veriye DÖNMEZ; eski ham değer olduğu gibi geri yazılır."""
    alan = _kati_alan()
    isaret = alan.from_db_value("DÜZ METİN", None, None)
    assert isinstance(isaret, crypto.CorruptField)
    assert alan.get_prep_value(isaret) == "DÜZ METİN"


def test_bozuk_alan_isareti_kilitliyken_de_ham_yazilir() -> None:
    isaret = crypto.CorruptField("gAAAAbozuk")
    crypto.unload_key()
    assert _kati_alan().get_prep_value(isaret) == "gAAAAbozuk"


def test_bozuk_alan_isareti_metin_gibi_sizdirmaz() -> None:
    isaret = crypto.CorruptField("ÖZEL BİLGİ", model_label="okul.Ornek", field_name="ad")
    assert str(isaret) == ""
    assert f"{isaret} SOYAD".strip() == "SOYAD"
    assert not isaret
    assert "ÖZEL" not in repr(isaret)
    assert crypto.is_corrupt(isaret) and not crypto.is_corrupt("metin")
    assert isaret == crypto.CorruptField("ÖZEL BİLGİ") and isaret != "ÖZEL BİLGİ"


def test_bozuk_alan_isareti_temizlemede_metne_cevrilmez() -> None:
    """`full_clean` işareti "" yapsaydı kayıt bozuk değeri boşla ezerdi."""
    alan = _kati_alan()
    isaret = crypto.CorruptField("x" * 500)  # uzunluk denetimi işarete uygulanmaz
    assert alan.to_python(isaret) is isaret
    assert alan.clean(isaret, None) is isaret
    assert alan.to_python("ad") == "ad"


def test_bozuk_okuma_kaydi_sayar_ve_sifirlanir() -> None:
    crypto.record_corrupt_read("okul.Ornek", 7, "first_name")
    crypto.record_corrupt_read("okul.Ornek", 7, "first_name")  # aynı kayıt-alan bir kez
    crypto.record_corrupt_read("okul.Ornek", None, "last_name")
    assert crypto.corrupt_read_count() == 2
    assert crypto.corrupt_reads() == [
        ("okul.Ornek", "", "last_name"),
        ("okul.Ornek", "7", "first_name"),
    ]
    crypto._reset_corrupt_reads_for_tests()
    assert crypto.corrupt_read_count() == 0


# ---------------------------------------------------------------------------
# Alt anahtarlar ve iz anahtarı tutucusu (tasarım §2.3.1, §4.6.3)
# ---------------------------------------------------------------------------
def test_hesap_muhru_anahtari_tasarimdaki_hkdf_dizgesiyle_turer() -> None:
    beklenen = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None, info=b"od-hesap-muhru/v1"
    ).derive(TEST_DEK)
    assert crypto.ACCOUNT_SEAL_INFO == b"od-hesap-muhru/v1"
    assert crypto.account_seal_key(TEST_DEK) == beklenen
    assert crypto.derive_subkey(TEST_DEK, info=b"od-kor-indeks") != beklenen


#: Uydurma hesap kimlikleri (gerçek kayıt değildir).
_KIMLIK = "6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60"
_BASKA_KIMLIK = "0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f"
_TUZ = bytes(range(16))
_UCUZ = crypto.KdfParams(time_cost=1, memory_cost=8, parallelism=1)


def _sarma_anahtari(
    kimlik: object, *, parola: str = "Uydurma-Parola-1", tuz: bytes = _TUZ
) -> bytes:
    return crypto.account_wrapping_key(parola, salt=tuz, account_id=kimlik, params=_UCUZ)


def test_hesap_sarmali_anahtari_kimlige_bagli_hkdf_ile_turer() -> None:
    """Kullanıcı kararı 02.11.2026: `HKDF(Argon2id(parola, tuz), "od-hesap-sarmali/v1" ‖ kimlik)`.

    Formül açıkça yeniden hesaplanır: bilgi dizgesinden kimliği çıkaran ya da Argon2id çıktısını
    doğrudan kullanan bir değişiklik bu testi düşürür."""
    argon = crypto.derive_key("Uydurma-Parola-1", salt=_TUZ, params=_UCUZ)
    beklenen = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"od-hesap-sarmali/v1" + _KIMLIK.encode("ascii"),
    ).derive(argon)
    assert crypto.ACCOUNT_WRAP_INFO == b"od-hesap-sarmali/v1"
    assert _sarma_anahtari(_KIMLIK) == beklenen
    assert beklenen != argon  # bağsız (F1b-1) türetim bu değildir
    assert crypto.ACCOUNT_WRAP_INFO not in {
        crypto.ACCOUNT_SEAL_INFO,
        crypto.ACCOUNT_WRAP_DIGEST_INFO,
        crypto.BLIND_INDEX_INFO,
        crypto.AUDIT_CHAIN_INFO,
        crypto.RECORD_SUMMARY_INFO,
        crypto.FILE_WRAP_INFO,
    }


def test_sarmal_ozeti_tasarimdaki_hkdf_dizgesiyle_ve_bicimle_hesaplanir() -> None:
    """Kullanıcı kararı 03.11.2026 "tazelik kapatılır": `HMAC(HKDF(DEK, "od-sarmal-ozeti/v1"),
    kanonik(id, salt, sarmal))`. Formül açıkça yeniden hesaplanır: özet anahtarını mühür anahtarıyla
    aynı bilgiden türeten (amaç ayrımını bozan), kimliği kanonik metne çevirmeyen ya da tuzu kanonik
    base64 dışında yazan bir değişiklik bu testi düşürür (tasarım §2.3.1 kimlik tablosu)."""
    import base64
    import uuid

    anahtar = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None, info=b"od-sarmal-ozeti/v1"
    ).derive(TEST_DEK)
    assert crypto.ACCOUNT_WRAP_DIGEST_INFO == b"od-sarmal-ozeti/v1"
    assert crypto.account_wrap_digest_key(TEST_DEK) == anahtar
    assert anahtar != crypto.account_seal_key(TEST_DEK)
    assert crypto.ACCOUNT_WRAP_DIGEST_INFO not in {
        crypto.ACCOUNT_SEAL_INFO,
        crypto.BLIND_INDEX_INFO,
        crypto.AUDIT_CHAIN_INFO,
        crypto.RECORD_SUMMARY_INFO,
        crypto.FILE_WRAP_INFO,
    }
    assert base64.b64encode(_TUZ) == b"AAECAwQFBgcICQoLDA0ODw=="
    yuk = (
        b'{"id":"6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60",'
        b'"salt":"AAECAwQFBgcICQoLDA0ODw==","sarmal":"gAAAAB-uydurma-belirtec"}'
    )
    beklenen = hmac.new(anahtar, yuk, sha256).hexdigest()
    assert (
        crypto.account_wrap_digest(
            TEST_DEK,
            account_id=uuid.UUID(_KIMLIK.upper()),
            salt=_TUZ,
            wrapped="gAAAAB-uydurma-belirtec",
        )
        == beklenen
    )


def test_farkli_kimlik_farkli_anahtar_verir_ve_sarmali_acmaz() -> None:
    """Başka kimlikle türetilen anahtar sarmalı açmaz (Fernet'in HMAC'i tutmaz)."""
    anahtar = _sarma_anahtari(_KIMLIK)
    assert anahtar != _sarma_anahtari(_BASKA_KIMLIK)
    assert anahtar != _sarma_anahtari(_KIMLIK, parola="Uydurma-Parola-2")
    assert anahtar != _sarma_anahtari(_KIMLIK, tuz=bytes(16))
    sarmal = crypto.wrap_key(TEST_DEK, wrapping_key=anahtar)
    assert crypto.unwrap_key(sarmal, wrapping_key=anahtar) == TEST_DEK
    with pytest.raises(InvalidToken):
        crypto.unwrap_key(sarmal, wrapping_key=_sarma_anahtari(_BASKA_KIMLIK))


def test_uuid_nesnesi_ve_kanonik_metin_ayni_anahtari_verir() -> None:
    import uuid

    assert crypto.canonical_account_id(uuid.UUID(_KIMLIK)) == _KIMLIK
    assert crypto.canonical_account_id(_KIMLIK) == _KIMLIK
    assert _sarma_anahtari(uuid.UUID(_KIMLIK)) == _sarma_anahtari(_KIMLIK)


@pytest.mark.parametrize(
    "yazim",
    [
        _KIMLIK.upper(),
        _KIMLIK.replace("-", ""),
        f" {_KIMLIK}",
        f"{_KIMLIK} ",
        f"{{{_KIMLIK}}}",
        f"urn:uuid:{_KIMLIK}",
        # ASCII dışı rakam: `uuid.UUID` onu da aynı kimliğe çevirir (int() Unicode rakam okur).
        _KIMLIK.replace("6", "６"),
        "",
        "yonetici",
    ],
    ids=[
        "buyuk_harf",
        "tiresiz",
        "bastaki_bosluk",
        "sondaki_bosluk",
        "suslu_ayracli",
        "urn_onekli",
        "ascii_disi_rakam",
        "bos",
        "kimlik_degil",
    ],
)
def test_kanonik_olmayan_yazim_reddedilir(yazim: str) -> None:
    """Kural tek kanonik biçimdir: varyant aynı anahtara çevrilmez, REDDEDİLİR (Argon2id koşmaz)."""
    with pytest.raises(ValueError):
        crypto.canonical_account_id(yazim)
    with pytest.raises(ValueError):
        _sarma_anahtari(yazim)


@pytest.mark.parametrize("deger", [None, 42, b"6f1c2a3b", ["x"]])
def test_metin_ve_uuid_disindaki_kimlik_reddedilir(deger: object) -> None:
    with pytest.raises(TypeError):
        crypto.canonical_account_id(deger)
    with pytest.raises(TypeError):
        _sarma_anahtari(deger)


def test_dosya_sarmal_anahtari_tasarimdaki_hkdf_dizgesiyle_turer() -> None:
    """Tasarım §2.3.1, §4.4.4 "Dosya anahtarı": `HKDF(DEK, "od-dosya-sarmal/v1")`. Formül açıkça
    yeniden hesaplanır ve değer DONMUŞTUR (`test_dosya_sifreleme` altın vektörü aynı anahtarla
    sarar): dizgeyi ya da HKDF kullanımını değiştiren, sarmalı DEK'in kendisiyle kuran bir
    değişiklik bu testi düşürür."""
    beklenen = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None, info=b"od-dosya-sarmal/v1"
    ).derive(TEST_DEK)
    assert crypto.FILE_WRAP_INFO == b"od-dosya-sarmal/v1"
    assert crypto.file_wrap_key(TEST_DEK) == beklenen
    assert beklenen.hex() == "ebaf847c939314dead95db481a93f68b2d089ed59c0a0dfa0a31193c31683a40"
    assert beklenen not in {
        TEST_DEK,
        crypto.account_seal_key(TEST_DEK),
        crypto.account_wrap_digest_key(TEST_DEK),
        crypto._derive_blind_index_key(TEST_DEK),
    }


#: Tasarım §2.3.1 kimlik tablosundaki HKDF bilgi dizgeleri (`shared.crypto`'daki `*_INFO`
#: sabitleri). Yeni dizge buraya BİLİNÇLİ eklenir: modüldeki küme bununla birebir eşit olmalı.
_HKDF_DIZGELERI = {
    "BLIND_INDEX_INFO": b"od-kor-indeks",
    "ACCOUNT_SEAL_INFO": b"od-hesap-muhru/v1",
    "ACCOUNT_WRAP_DIGEST_INFO": b"od-sarmal-ozeti/v1",
    "ACCOUNT_WRAP_INFO": b"od-hesap-sarmali/v1",
    "FILE_WRAP_INFO": b"od-dosya-sarmal/v1",
    "AUDIT_CHAIN_INFO": b"od-denetim-izi/v1",
    "RECORD_SUMMARY_INFO": b"od-kayit-ozeti/v1",
    "AUDIT_ANCHOR_INFO": b"od-iz-capa/v1",
    "AUDIT_LOCKED_SEED_INFO": b"od-iz-kilitli/v1",
    "AUDIT_LOCKED_MAC_INFO": b"od-iz-kilitli-mac/v1",
}


def test_hkdf_dizgeleri_tam_listedir_ve_birbirleriyle_cakismaz() -> None:
    """Her amaç ayrı dizge kullanır; bir amacın anahtarı ötekini vermez (tasarım §2.3.1).

    Kümeye yedek kabının iki dizgesi de girer (`desktop.backup_crypto`; DEK'ten türer ama masaüstü
    katmanında durur). Hiçbir dizge ötekinin öneki de değildir: hesap sarmalının bilgisi önek ‖
    36 karakterlik kimliktir ve başka bir amacın dizgesine denk gelmemelidir."""
    from desktop import backup_crypto

    modulde = {ad: deger for ad, deger in vars(crypto).items() if ad.endswith("_INFO")}
    assert modulde == _HKDF_DIZGELERI
    hepsi = [
        *modulde.values(),
        backup_crypto._PRIVATE_INFO,
        backup_crypto._ENVELOPE_INFO,
    ]
    assert len(set(hepsi)) == len(hepsi)
    for bir in hepsi:
        for oteki in hepsi:
            assert bir == oteki or not oteki.startswith(bir), (bir, oteki)


def test_iz_anahtari_turevlerinin_hkdf_dizgeleri_tasarimdakidir() -> None:
    """Tasarım §4.6.2-§4.6.3: beş dizge AYNEN; değişirse kâğıttaki zincir başları tutmaz."""
    assert crypto.AUDIT_CHAIN_INFO == b"od-denetim-izi/v1"
    assert crypto.RECORD_SUMMARY_INFO == b"od-kayit-ozeti/v1"
    assert crypto.AUDIT_ANCHOR_INFO == b"od-iz-capa/v1"
    assert crypto.AUDIT_LOCKED_SEED_INFO == b"od-iz-kilitli/v1"
    assert crypto.AUDIT_LOCKED_MAC_INFO == b"od-iz-kilitli-mac/v1"


def test_zincir_ve_icerik_anahtarlari_ia_dan_hkdf_ile_turer() -> None:
    ia = bytes(range(64, 96))
    for info, turet in (
        (b"od-denetim-izi/v1", crypto.audit_chain_key),
        (b"od-kayit-ozeti/v1", crypto.record_summary_key),
    ):
        beklenen = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(ia)
        assert turet(ia) == beklenen
    # DONMUŞ değer: HKDF kullanımı (tuzsuz, 32 bayt) sessizce değişmesin.
    assert crypto.audit_chain_key(ia).hex() == (
        "7c51685fa9b15f0940115b95fc21821cf5c38700d79e465de1800e416ecd9a69"
    )
    assert crypto.audit_chain_key(ia) != crypto.record_summary_key(ia)


def test_kilitli_kip_tohumu_tuzla_turer() -> None:
    """Kilitli kip tohumu `HKDF(İA, "od-iz-kilitli/v1", tuz = seq ‖ mac)` (§4.6.3)."""
    ia = bytes(range(64, 96))
    tuz = b"7" + b"a" * 64
    beklenen = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=tuz, info=crypto.AUDIT_LOCKED_SEED_INFO
    ).derive(ia)
    assert crypto.derive_subkey(ia, info=crypto.AUDIT_LOCKED_SEED_INFO, salt=tuz) == beklenen
    assert crypto.derive_subkey(ia, info=crypto.AUDIT_LOCKED_SEED_INFO) != beklenen


def test_iz_anahtari_dek_ile_yuklenir_ve_dusurulur() -> None:
    crypto.load_key(TEST_DEK, audit_key=b"\x05" * 32)
    assert crypto.active_audit_key() == b"\x05" * 32
    crypto.load_key(TEST_DEK)  # yeni yükleme önceki iz anahtarını bırakmaz
    assert crypto.active_audit_key() is None
    crypto.load_key(TEST_DEK, audit_key=b"\x05" * 32)
    crypto.unload_key()
    assert crypto.active_audit_key() is None


def test_decrypt_with_bellekteki_anahtardan_bagimsizdir() -> None:
    token = crypto._fernet_for(b"\x03" * 32).encrypt(b"iz").decode("ascii")
    assert crypto.decrypt_with(b"\x03" * 32, token) == b"iz"
    with pytest.raises(InvalidToken):
        crypto.decrypt_with(TEST_DEK, token)


#: Kilitli kip türevlerinin altın vektörleri (İA = bytes(64..95), çapa 7 + altın zincir MAC'i;
#: `shared/tests/test_kanonik.py`). Değerler DONMUŞTUR: çapa ve kilitli satırların mührü bunlara bağlı.
_ALTIN_CAPA_BAYTLARI = b"7:c3ed8364e85586483986d3656d9f64519d34dd96d8be6305468a4fded57fa3b6"


def test_altin_vektor_capa_ve_kilitli_kip_anahtarlari() -> None:
    """Tasarım §4.6.3: çapa anahtarı, `tohum₀` (tuz = seq ‖ mac) ve k'ıncı satırın anahtarı."""
    ia = bytes(range(64, 96))
    capa = crypto.audit_anchor_key(ia)
    assert capa == HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None, info=b"od-iz-capa/v1"
    ).derive(ia)
    assert capa.hex() == "806ddf4aed2a13bc0b126107ed1654ea7f871a47e99f5c4e457de9092447bb5e"
    tohum = crypto.audit_locked_seed(ia, _ALTIN_CAPA_BAYTLARI)
    assert tohum == HKDF(
        algorithm=hashes.SHA256(), length=32, salt=_ALTIN_CAPA_BAYTLARI, info=b"od-iz-kilitli/v1"
    ).derive(ia)
    assert tohum.hex() == "ec1aae25e0300364fd71ef6ca149c2aab049286ff9a25b202f43ff6a3711ae0e"
    anahtar = crypto.audit_locked_mac_key(tohum)
    assert anahtar.hex() == "e5873077c47dd0f08aaedf95ee5bdcccb0d15e0c1ab510cfd85e912d02a7c75f"
    # Üç amaç birbirinden ayrıdır; zincir anahtarı da hiçbiri değildir.
    assert len({capa, tohum, anahtar, crypto.audit_chain_key(ia)}) == 4


def test_altin_vektor_kilitli_kip_satirinin_mac_i() -> None:
    """Uçtan uca: çapa 7'nin ilk kilitli satırı (`GOC`, `key_ref = "7:0"`) — DONMUŞ MAC."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from shared import kanonik

    ia = bytes(range(64, 96))
    onceki = "c3ed8364e85586483986d3656d9f64519d34dd96d8be6305468a4fded57fa3b6"
    satir = {
        "seq": 8,
        "at": datetime(2026, 11, 1, 10, 31, tzinfo=ZoneInfo("Europe/Istanbul")),
        "actor": "SISTEM",
        "account": None,
        "role": "",
        "action": "GOC",
        "model": "sema.goc",
        "object_id": "0.2.0",
        "term": None,
        "changed_fields": ["gocler"],
        "values": {"gocler": [None, ["okul.0010_ornek"]]},
        "record_mac": "",
        "compliance_item": None,
        "label": "",
        "key_mode": "KILITLI",
        "key_ref": "7:0",
    }
    anahtar = crypto.audit_locked_mac_key(
        crypto.audit_locked_seed(ia, kanonik.capa_baytlari(7, onceki))
    )
    assert kanonik.iz_mac(anahtar, satir, onceki) == (
        "e637ed638195fdb0fa5ed25b0b0b5856e2d58b7adb08694a89e6a947068a485f"
    )
