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
