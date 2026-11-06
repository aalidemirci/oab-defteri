"""`ODBAK\\x03` yedek kabı: bayt düzeni, AAD bağı, manifesto, dosya bölümü, yazım kipi.

Dayanak: plan F1b-3 "Kap ve manifesto", tasarım §4.4.7. Kabı `kap_ortak.kap_kur` kurar. Ek gövdeleri
burada yapı sınaması içindir (kabın biçimi boyuyla tutar, içeriği uydurmadır); gerçek `ODDOSYA` kabıyla
tur dönüşü `backend/shared/tests/test_dosya_sifreleme.py`'dedir. Adlar ve özetler uydurmadır.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import tracemalloc
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from desktop import backup_crypto
from desktop.backup_crypto import (
    BOS_YEREL_MANIFESTO,
    DENEME_MAGIC,
    DOSYA_AZAMI_SIFRELI_BOY,
    DOSYA_BOLUMU_SONU,
    DOSYA_KAP_EK_BAYT,
    KAPSAM_TAM,
    KAPSAM_YEREL,
    KOPYA_PARCASI,
    MAGIC,
    MAX_RECOVERY_HEADER_BYTES,
    BackupCryptoError,
    DenemeYedegiHatasi,
    DosyaBolumuHatasi,
    EkTutmuyorHatasi,
    Manifesto,
    ManifestoGirdisi,
    YedekAnahtariHatasi,
    baslik_oku,
    decrypt_bytes,
    dosya_bolumunu_oku,
    ek_denetle,
    embedded_recovery_metadata,
    encrypt_bytes,
    encrypt_to_path,
    kap_basligi,
    kap_basligini_oku,
    manifesto_ayristir,
    muhurlu_bolumu_ac,
    private_key_from_data_key,
    read_embedded_recovery_metadata,
    tam_yedek_yaz,
)
from desktop.tests.kap_ortak import bolum_girdisi, kap_kur

_DEK = bytes(range(32))
_BASKA_DEK = bytes(range(1, 33))
#: Üretim yazıcılarının kapısından geçen TK10 başlığı (uydurma sarmal).
_BASLIK = json.dumps(
    {
        "surum": 2,
        "kdf": {"time_cost": 1},
        "kurtarma": {"no": 1, "tarih": "2026-07-24", "salt": "dHV6Mg==", "sarmal": "ornek-sarmal"},
    },
    sort_keys=True,
).encode("utf-8")
_DB = b"SQLite format 3\x00uydurma-goruntu"
_AD_1 = "1" * 32
_AD_2 = "2" * 32
_AD_3 = "3" * 32
#: Mühürlü bölümün başlangıcı: 54 + L + kapsam + uzunluk.
_AAD_BOY = 54 + len(_BASLIK) + 9


def _ozet(acik: bytes) -> str:
    return hashlib.sha256(acik).hexdigest()


def _girdi(ad: str, acik: bytes, *, eksik: bool = False) -> ManifestoGirdisi:
    return ManifestoGirdisi(ad, len(acik), _ozet(acik), eksik=eksik)


def _govde(acik: bytes) -> bytes:
    """Boyu kabınkiyle tutan uydurma gövde (yapı sınaması; içerik şifreli değildir)."""
    return b"ODDOSYA\x01" + bytes(12) + acik + bytes(16)


def _depo(dizin: Path, **ekler: bytes) -> dict[str, ManifestoGirdisi]:
    """`dizin`e uydurma ek gövdeleri yazar; ada göre manifesto girdileri döner."""
    dizin.mkdir(parents=True, exist_ok=True)
    girdiler = {}
    for ad, acik in ekler.items():
        (dizin / ad).write_bytes(_govde(acik))
        girdiler[ad] = _girdi(ad, acik)
    return girdiler


class _SayanAkis(io.BytesIO):
    """Okunan baytları ve tek seferde istenen en büyük okumayı sayar."""

    def __init__(self, veri: bytes) -> None:
        super().__init__(veri)
        self.okunan = 0
        self.en_buyuk_istek = 0

    def read(self, boy: int | None = -1) -> bytes:
        veri = super().read(boy)
        self.okunan += len(veri)
        self.en_buyuk_istek = max(self.en_buyuk_istek, -1 if boy is None else boy)
        return veri


def _tuket(bolum: bytes, manifesto: Manifesto) -> list[tuple[str, bytes]]:
    return [
        (girdi.girdi.ad, b"".join(girdi.parcalar()))
        for girdi in dosya_bolumunu_oku(io.BytesIO(bolum), manifesto)
    ]


def _tam_manifesto(*girdiler: ManifestoGirdisi) -> Manifesto:
    return Manifesto(KAPSAM_TAM, tuple(girdiler))


def _tam_kap(*, manifesto: Manifesto | None = None, bolum: bytes | None = None) -> bytes:
    return kap_kur(
        _DB,
        _DEK,
        baslik=_BASLIK,
        manifesto=manifesto if manifesto is not None else _tam_manifesto(),
        dosya_bolumu=bolum,
    )


def _yerel_kap(manifesto: Manifesto = BOS_YEREL_MANIFESTO) -> bytes:
    return kap_kur(_DB, _DEK, baslik=_BASLIK, manifesto=manifesto)


# ---------------------------------------------------------------- bayt düzeni ve altın vektör
_ALTIN_GECICI = bytes(range(32, 64))
_ALTIN_NONCE = bytes(range(64, 76))
_ALTIN_BASLIK = b'{"kdf":{},"kurtarma":{"salt":"eA==","sarmal":"eA=="},"surum":2}'
_ALTIN_GIRDI = ManifestoGirdisi(_AD_1, 5, _ozet(b"abcde"))
_ALTIN_YEREL = (
    "4f4442414b03358072d6365880d1aeea329adf9121383851ed21a28e3b75e965d0d2cd16625440414243444546"
    "4748494a4b0000003f7b226b6466223a7b7d2c226b75727461726d61223a7b2273616c74223a2265413d3d222c"
    "227361726d616c223a2265413d3d227d2c22737572756d223a327d0100000000000000da7234ab550f43c8a8e0"
    "f4fb84014ea249dbc4c005a98c47927d1fb228fdfbcda1dad25a32ae44356aa2480044d7f80809c00534ad3aca"
    "d52ac8d203dca16cc37824016b6da46137824d3ff0a28f996302605c2cdb785b1a6a8b84c46cfd8cadca02809a"
    "da8c10d73bb6cad5174826c18cc6400b6cae687b5f49647b23a3c14371feed5d3ad35353d29c97bbf3901c20d6"
    "c5e0a548c97e21f1e5e513d85830d6f6ac27f788ef319ec57e8f0e62f764acf85fd72c49a7575efe8e27faf455"
    "2255be41697f1565dbfc911f45b4cfef857d34e2b10db07782468ae71c"
)
_ALTIN_TAM = (
    "4f4442414b03358072d6365880d1aeea329adf9121383851ed21a28e3b75e965d0d2cd16625440414243444546"
    "4748494a4b0000003f7b226b6466223a7b7d2c226b75727461726d61223a7b2273616c74223a2265413d3d222c"
    "227361726d616c223a2265413d3d227d2c22737572756d223a327d0200000000000000da7234ab550f43c8a8e0"
    "f4fb84014ea249dbc4c005a98c47927d1fb228fdfbcda1dad25a32ae44356aa2480044d7f80809c00534ad3aca"
    "d52ac8d203dca16cc37824016b6da46137824d3ff0a28f996302605c2cdb785b1a6a8b84c46cfd8cadca02809a"
    "da8c10d73bb6cad5174826c18cc6400b6cae687b5f49647b23a3c14371feed5d3ad35353d29c97bbf3901c20d6"
    "c5e0a548c97e21f1e5e513d85830d6f6ac27f788ef319ec57e8f0e62f764acf85fd72c49a7575efe8e27faf455"
    "2256be41697f1565dbfc911f4598b9c6aa42f902dba1e5f74d53354c8231313131313131313131313131313131"
    "3131313131313131313131313131313100000000000000294f44444f5359410100000000000000000000000061"
    "62636465000000000000000000000000000000004f4442414b2d444f5359412d424f4c554d552d534f4e550000"
    "000000000000000000000000000000"
)


def _altin_kap(manifesto: Manifesto, dosya_bolumu: bytes | None = None) -> bytes:
    return kap_kur(
        _DB,
        _DEK,
        baslik=_ALTIN_BASLIK,
        manifesto=manifesto,
        dosya_bolumu=dosya_bolumu,
        ephemeral=X25519PrivateKey.from_private_bytes(_ALTIN_GECICI),
        nonce=_ALTIN_NONCE,
    )


def test_kap_altin_vektoru_yerel() -> None:
    """Sabit girdilerle baytlar donar: düzen değişirse eski yedekler açılmaz, bilerek değişir."""
    assert _altin_kap(Manifesto(KAPSAM_YEREL, (_ALTIN_GIRDI,))).hex() == _ALTIN_YEREL


def test_kap_altin_vektoru_tam_dosya_bolumuyle() -> None:
    bolum = bolum_girdisi(_AD_1.encode("ascii"), _govde(b"abcde")) + DOSYA_BOLUMU_SONU
    kap = _altin_kap(_tam_manifesto(_ALTIN_GIRDI), bolum)
    assert kap.hex() == _ALTIN_TAM


def test_manifesto_kanonik_baytlari_donar() -> None:
    manifesto = _tam_manifesto(
        ManifestoGirdisi(_AD_1, 5, "a" * 64),
        ManifestoGirdisi(_AD_2, 7, "b" * 64, eksik=True),
    )
    assert manifesto.baytlar() == (
        b'{"dosyalar":[{"ad":"' + _AD_1.encode() + b'","boyut":5,"sha256":"' + b"a" * 64 + b'"},'
        b'{"ad":"' + _AD_2.encode() + b'","boyut":7,"eksik":true,"sha256":"' + b"b" * 64 + b'"}],'
        b'"kapsam":2,"surum":1}'
    )


def test_bitis_isareti_donar_ve_girdi_adiyla_karismaz() -> None:
    assert DOSYA_BOLUMU_SONU == b"ODBAK-DOSYA-BOLUMU-SONU" + bytes(17)
    assert backup_crypto.DEPO_ADI_DESENI.fullmatch(DOSYA_BOLUMU_SONU[:32].decode("latin-1")) is None


def _hkdf(deger: bytes, bilgi: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=bilgi).derive(deger)


@pytest.mark.parametrize(
    ("kap", "kapsam_bayti"),
    [(_yerel_kap(), 1), (_tam_kap(), 2)],
    ids=["yerel", "tam"],
)
def test_kap_elle_cozulur_sifreli_metinden_onceki_her_bayt_aad(
    kap: bytes, kapsam_bayti: int
) -> None:
    """Düzen, kodun ayrıştırıcısından bağımsız, yalnız ilkellerle açılır: AAD tam olarak şifreli
    metinden önceki bütün baytlardır (bir alan AAD'den çıkarsa etiket tutmaz)."""
    assert kap[:6] == b"ODBAK\x03"
    baslik_boy = int.from_bytes(kap[50:54], "big")
    assert kap[54 : 54 + baslik_boy] == _BASLIK
    assert kap[54 + baslik_boy] == kapsam_bayti
    muhurlu_boy = int.from_bytes(kap[55 + baslik_boy : 63 + baslik_boy], "big")
    aad_sonu = 63 + baslik_boy
    ozel = X25519PrivateKey.from_private_bytes(_hkdf(_DEK, b"OABDefteri/backup/private/v1"))
    ortak = ozel.exchange(X25519PublicKey.from_public_bytes(kap[6:38]))
    anahtar = _hkdf(ortak, b"OABDefteri/backup/envelope/v1")
    acik = AESGCM(anahtar).decrypt(
        kap[38:50], kap[aad_sonu : aad_sonu + muhurlu_boy], kap[:aad_sonu]
    )
    db_boy = int.from_bytes(acik[:8], "big")
    assert acik[8 : 8 + db_boy] == _DB
    assert json.loads(acik[8 + db_boy :]) == {"surum": 1, "kapsam": kapsam_bayti, "dosyalar": []}
    kuyruk = kap[aad_sonu + muhurlu_boy :]
    assert kuyruk == (DOSYA_BOLUMU_SONU if kapsam_bayti == KAPSAM_TAM else b"")


# ---------------------------------------------------------------- tur dönüşü
def test_yerel_tur_donusu_veritabani_ve_manifestoyu_ayri_verir() -> None:
    manifesto = Manifesto(KAPSAM_YEREL, (_girdi(_AD_1, b"ek"),))

    icerik = decrypt_bytes(
        encrypt_bytes(
            _DB,
            private_key_from_data_key(_DEK).public_key(),
            recovery_header=_BASLIK,
            manifesto=manifesto,
        ),
        _DEK,
    )

    assert icerik.veritabani == _DB
    assert icerik.manifesto == manifesto


def test_tam_tur_donusu_veritabani_manifesto_ve_ekler(tmp_path: Path) -> None:
    depo = tmp_path / "dosyalar"
    girdiler = _depo(depo, **{_AD_1: b"bir", _AD_2: b"ikinci-ek"})
    hedef = tmp_path / "tam.odbak"

    yazilan = tam_yedek_yaz(
        hedef,
        _DB,
        [girdiler[_AD_2], girdiler[_AD_1]],
        depo,
        private_key_from_data_key(_DEK).public_key(),
        recovery_header=_BASLIK,
    )

    icerik = decrypt_bytes(hedef.read_bytes(), _DEK)
    assert icerik.veritabani == _DB
    assert icerik.manifesto == yazilan == _tam_manifesto(girdiler[_AD_2], girdiler[_AD_1])
    with hedef.open("rb") as akis:
        baslik = baslik_oku(akis, hedef.stat().st_size)
        assert baslik.kapsam == KAPSAM_TAM
        assert muhurlu_bolumu_ac(akis, baslik, _DEK).veritabani == _DB
        okunan = [
            (girdi.girdi.ad, b"".join(girdi.parcalar()))
            for girdi in dosya_bolumunu_oku(akis, yazilan)
        ]
    # Manifesto sırasıyla ve ikinci kez şifrelenmeden: gövde depodaki baytların aynısıdır.
    assert okunan == [(_AD_2, _govde(b"ikinci-ek")), (_AD_1, _govde(b"bir"))]


def test_yanlis_anahtarla_acilmaz() -> None:
    for kap in (_yerel_kap(), _tam_kap()):
        with pytest.raises(YedekAnahtariHatasi, match="bütünlüğü"):
            decrypt_bytes(kap, _BASKA_DEK)


# ---------------------------------------------------------------- AAD bağı
def _cevir(kap: bytes, konum: int) -> bytes:
    bozuk = bytearray(kap)
    bozuk[konum] ^= 1
    return bytes(bozuk)


@pytest.mark.parametrize(
    ("ad", "bas", "son"),
    [
        ("gecici_acik_anahtar", 6, 38),
        ("nonce", 38, 50),
        ("kurtarma_basligi", 54, 54 + len(_BASLIK)),
    ],
)
def test_basligin_bir_biti_donunce_cozme_duser(ad: str, bas: int, son: int) -> None:
    kap = _yerel_kap()
    for konum in range(bas, son):
        with pytest.raises(YedekAnahtariHatasi):
            decrypt_bytes(_cevir(kap, konum), _DEK)


def test_aad_nin_her_baytinda_bit_donunce_kap_acilmaz() -> None:
    for kap in (_yerel_kap(), _tam_kap()):
        for konum in range(_AAD_BOY):
            with pytest.raises(BackupCryptoError):
                decrypt_bytes(_cevir(kap, konum), _DEK)


def test_kapsam_bayti_ac_a_baglidir_yerel_tam_yapilamaz() -> None:
    """Yapısı tam yedeğe uydurulan yerel yedek: kapsam baytı çevrilip bitiş işareti eklenir."""
    kap = bytearray(_yerel_kap())
    kap[_AAD_BOY - 9] = KAPSAM_TAM
    with pytest.raises(YedekAnahtariHatasi):
        decrypt_bytes(bytes(kap) + DOSYA_BOLUMU_SONU, _DEK)


def test_kesik_tam_yedek_yerel_sanilamaz() -> None:
    """Dosya bölümü kesilip kapsam baytı `01`e çevrilse de kap açılmaz (plan "Kap ve manifesto")."""
    kap = bytearray(_tam_kap()[: -len(DOSYA_BOLUMU_SONU)])
    kap[_AAD_BOY - 9] = KAPSAM_YEREL
    with pytest.raises(YedekAnahtariHatasi):
        decrypt_bytes(bytes(kap), _DEK)


def test_muhurlu_bolumun_son_biti_donunce_cozme_duser() -> None:
    with pytest.raises(YedekAnahtariHatasi):
        decrypt_bytes(_cevir(_yerel_kap(), len(_yerel_kap()) - 1), _DEK)


# ---------------------------------------------------------------- kesik ve uzatılmış kap
def test_yerel_kap_hicbir_noktada_kesilemez() -> None:
    kap = _yerel_kap()
    for boy in range(len(kap)):
        with pytest.raises(BackupCryptoError):
            kap_basligi(kap[:boy])


def test_tam_kap_hicbir_noktada_kesilemez() -> None:
    bolum = bolum_girdisi(_AD_1.encode("ascii"), _govde(b"ek")) + DOSYA_BOLUMU_SONU
    kap = _tam_kap(manifesto=_tam_manifesto(_girdi(_AD_1, b"ek")), bolum=bolum)
    for boy in range(len(kap)):
        with pytest.raises(BackupCryptoError):
            decrypt_bytes(kap[:boy], _DEK)
    assert decrypt_bytes(kap, _DEK).veritabani == _DB


def test_yerel_kap_uzatilamaz() -> None:
    with pytest.raises(BackupCryptoError, match="başlığı bozuk"):
        decrypt_bytes(_yerel_kap() + b"\x00", _DEK)


def test_tam_kap_uzatilamaz() -> None:
    with pytest.raises(DosyaBolumuHatasi):
        decrypt_bytes(_tam_kap() + b"\x00", _DEK)


@pytest.mark.parametrize(
    "muhurlu_boy",
    [0, 23, 2**31, 2**63, 2**64 - 1],
    ids=["sifir", "en_kisadan_kisa", "gcm_siniri_ustu", "dev", "en_buyuk"],
)
def test_sinir_disi_muhurlu_boy_okumadan_reddedilir(muhurlu_boy: int) -> None:
    onek = _yerel_kap()[: _AAD_BOY - 8] + muhurlu_boy.to_bytes(8, "big")
    akis = _SayanAkis(onek + bytes(64))

    with pytest.raises(BackupCryptoError, match="başlığı bozuk"):
        # Dosya boyu alanı tutar: reddeden boyun kendi sınırıdır.
        baslik_oku(akis, toplam_boy=len(onek) + muhurlu_boy)

    assert akis.okunan == len(onek)


def test_muhurlu_bolumu_sigmayan_tam_yedegin_basligi_reddedilir() -> None:
    """Tam yedekte mühürlü bölümden sonrası serbesttir ama mühürlü bölüm dosyaya sığmalıdır."""
    kap = _tam_kap()
    konum = kap_basligi(kap).dosya_bolumu_konumu

    assert kap_basligi(kap[:konum]).kapsam == KAPSAM_TAM
    with pytest.raises(BackupCryptoError, match="başlığı bozuk"):
        kap_basligi(kap[: konum - 1])


def test_dusuk_dereceli_gecici_anahtar_cozme_hatasidir() -> None:
    """Hazırlanmış dosya anahtar değişimini düşürür: ham `ValueError` değil, adayı geçen hata."""
    kap = _yerel_kap()
    with pytest.raises(YedekAnahtariHatasi):
        decrypt_bytes(kap[:6] + bytes(32) + kap[38:], _DEK)


def test_kurtarma_basligi_siniri_okumadan_reddedilir() -> None:
    kap = _yerel_kap()
    alan = (MAX_RECOVERY_HEADER_BYTES + 1).to_bytes(4, "big")
    akis = _SayanAkis(kap[:50] + alan + kap[54:])

    with pytest.raises(BackupCryptoError, match="başlığı bozuk"):
        baslik_oku(akis, len(kap))

    assert akis.okunan == 54


@pytest.mark.parametrize("kapsam", [0, 3, 255])
def test_bilinmeyen_kapsam_bayti_reddedilir(kapsam: int) -> None:
    kap = bytearray(_yerel_kap())
    kap[_AAD_BOY - 9] = kapsam
    with pytest.raises(BackupCryptoError, match="başlığı bozuk"):
        kap_basligi(bytes(kap))


# ---------------------------------------------------------------- manifesto
def test_manifesto_kapsami_baslikla_ayni_olmali() -> None:
    """Mühür tutar, manifesto başlıktan başka kapsam söyler: yanlış anahtar sayılmaz."""
    kap = kap_kur(
        _DB,
        _DEK,
        baslik=_BASLIK,
        ham_manifesto=Manifesto(KAPSAM_TAM).baytlar(),
        kapsam=KAPSAM_YEREL,
    )
    with pytest.raises(BackupCryptoError, match="dosya listesi") as hata:
        decrypt_bytes(kap, _DEK)
    assert not isinstance(hata.value, YedekAnahtariHatasi)


def test_manifestosuz_muhurlu_bolum_reddedilir() -> None:
    kap = kap_kur(_DB, _DEK, baslik=_BASLIK, ham_manifesto=b"")
    with pytest.raises(BackupCryptoError, match="içeriği bozuk"):
        decrypt_bytes(kap, _DEK)


_GIRDI_METNI = {"ad": _AD_1, "boyut": 5, "sha256": "a" * 64}


def _manifesto_metni(**degisen: Any) -> bytes:
    veri = {"surum": 1, "kapsam": KAPSAM_TAM, "dosyalar": [_GIRDI_METNI], **degisen}
    return json.dumps(veri, sort_keys=True, separators=(",", ":")).encode("utf-8")


@pytest.mark.parametrize(
    "ham",
    [
        b"",
        b"\xff",
        b"[]",
        b"[" * 100_000,
        _manifesto_metni(surum=2),
        _manifesto_metni(surum=True),
        _manifesto_metni(kapsam=1),
        _manifesto_metni(kapsam=2.0),
        _manifesto_metni(dosyalar={}),
        _manifesto_metni(fazla="alan"),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "fazla": 1}]),
        _manifesto_metni(dosyalar=[{"ad": _AD_1, "boyut": 5}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "ad": "../../guvenlik.json"}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "ad": _AD_1.upper().replace("1", "A")}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "ad": _AD_1 + "\n"}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "boyut": 0}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "boyut": True}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "boyut": "5"}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "boyut": DOSYA_AZAMI_SIFRELI_BOY}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "sha256": "A" * 64}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "sha256": "a" * 63}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "eksik": False}]),
        _manifesto_metni(dosyalar=[{**_GIRDI_METNI, "eksik": 1}]),
        _manifesto_metni(dosyalar=[_GIRDI_METNI, _GIRDI_METNI]),
        _manifesto_metni() + b" ",
    ],
    ids=[
        "bos",
        "utf8_degil",
        "liste",
        "derin_ic_ice",
        "bilinmeyen_surum",
        "surum_bool",
        "kapsam_baska",
        "kapsam_ondalik",
        "dosyalar_liste_degil",
        "fazla_alan",
        "girdide_fazla_alan",
        "girdide_eksik_alan",
        "yol_gecisi_adi",
        "buyuk_harf_ad",
        "satir_sonlu_ad",
        "sifir_boy",
        "bool_boy",
        "metin_boy",
        "sinir_ustu_boy",
        "buyuk_harf_ozet",
        "kisa_ozet",
        "eksik_yanlis_kanonik_degil",
        "eksik_bool_degil",
        "ayni_ad_iki_kez",
        "kanonik_degil",
    ],
)
def test_bozuk_manifesto_reddedilir(ham: bytes) -> None:
    with pytest.raises(BackupCryptoError, match="dosya listesi"):
        manifesto_ayristir(ham, kapsam=KAPSAM_TAM)


def test_sinirdaki_en_buyuk_ek_kabul_edilir() -> None:
    en_buyuk = DOSYA_AZAMI_SIFRELI_BOY - DOSYA_KAP_EK_BAYT
    assert ManifestoGirdisi(_AD_1, en_buyuk, "a" * 64).sifreli_boy == DOSYA_AZAMI_SIFRELI_BOY


def test_yerel_yedekte_eksik_isareti_olmaz() -> None:
    with pytest.raises(BackupCryptoError, match="dosya listesi"):
        Manifesto(KAPSAM_YEREL, (_girdi(_AD_1, b"ek", eksik=True),))


def test_bilinmeyen_kapsamla_manifesto_kurulmaz() -> None:
    with pytest.raises(BackupCryptoError, match="dosya listesi"):
        Manifesto(3)


def test_manifesto_tur_donusu_eksik_isaretini_korur() -> None:
    manifesto = _tam_manifesto(_girdi(_AD_1, b"ek"), _girdi(_AD_2, b"yok", eksik=True))
    assert manifesto_ayristir(manifesto.baytlar(), kapsam=KAPSAM_TAM) == manifesto
    assert manifesto.tasinanlar == (_girdi(_AD_1, b"ek"),)


# ---------------------------------------------------------------- deneme kabı
def test_deneme_sabiti_bir_onceki_kaptir() -> None:
    assert DENEME_MAGIC == b"ODBAK\x02" and MAGIC == b"ODBAK\x03"


@pytest.mark.parametrize("kuyruk", [b"", bytes(200)], ids=["yalniz_sihirli_bayt", "tam_boy"])
def test_deneme_yedegi_her_okuyucuda_ayri_iletiyle_reddedilir(
    tmp_path: Path, kuyruk: bytes
) -> None:
    kap = DENEME_MAGIC + kuyruk
    yol = tmp_path / "gunluk-2026-08-01.odbak"
    yol.write_bytes(kap)

    for okuyucu in (
        lambda: kap_basligi(kap),
        lambda: kap_basligini_oku(yol),
        lambda: embedded_recovery_metadata(kap),
        lambda: read_embedded_recovery_metadata(yol),
        lambda: decrypt_bytes(kap, _DEK),
    ):
        with pytest.raises(DenemeYedegiHatasi, match="deneme sürümüyle alınmış"):
            okuyucu()


def test_tanimadik_dosya_deneme_iletisi_almaz() -> None:
    with pytest.raises(BackupCryptoError, match="geçerli bir OAB Defteri") as hata:
        kap_basligi(b"ODBAK\x01" + bytes(200))
    assert not isinstance(hata.value, DenemeYedegiHatasi)


# ---------------------------------------------------------------- başlık okuyucu
@pytest.mark.parametrize(
    ("kap", "kapsam"),
    [(_yerel_kap(), KAPSAM_YEREL), (_tam_kap(), KAPSAM_TAM)],
    ids=["yerel", "tam"],
)
def test_baslik_okuyucu_cozmeden_kapsam_verir(kap: bytes, kapsam: int) -> None:
    """Yedek listesi kapsamı kurtarma anahtarı olmadan, dosyanın yalnız başından okur."""
    akis = _SayanAkis(kap)

    baslik = baslik_oku(akis, len(kap))

    assert (baslik.kapsam, baslik.kurtarma_basligi) == (kapsam, _BASLIK)
    assert akis.okunan == _AAD_BOY == len(baslik.aad)
    assert akis.en_buyuk_istek < 1024 + len(_BASLIK)


def test_dosyadan_baslik_muhurlu_bolume_bakmaz(tmp_path: Path) -> None:
    """Mühürlü bölümü sıfırla doldurulmuş dosyanın başlığı yine okunur: orası hiç açılmaz."""
    baslik = kap_basligi(_yerel_kap())
    yol = tmp_path / "yedek.odbak"
    yol.write_bytes(baslik.aad + bytes(baslik.muhurlu_boy))

    assert kap_basligini_oku(yol).kapsam == KAPSAM_YEREL
    assert read_embedded_recovery_metadata(yol) == _BASLIK


def test_dosya_bolumu_konumu_muhurlu_bolumun_sonudur() -> None:
    kap = _tam_kap()
    assert kap[kap_basligi(kap).dosya_bolumu_konumu :] == DOSYA_BOLUMU_SONU


# ---------------------------------------------------------------- dosya bölümü okuyucusu
_ACIK_1 = b"birinci-ek"
_ACIK_2 = b"ikinci"
_G1 = _girdi(_AD_1, _ACIK_1)
_G2 = _girdi(_AD_2, _ACIK_2)
_B1 = bolum_girdisi(_AD_1.encode("ascii"), _govde(_ACIK_1))
_B2 = bolum_girdisi(_AD_2.encode("ascii"), _govde(_ACIK_2))
_IKI_EK = _tam_manifesto(_G1, _G2)


def test_bolum_girdi_girdi_manifesto_sirasiyla_okunur() -> None:
    assert _tuket(_B1 + _B2 + DOSYA_BOLUMU_SONU, _IKI_EK) == [
        (_AD_1, _govde(_ACIK_1)),
        (_AD_2, _govde(_ACIK_2)),
    ]


def test_bos_bolum_yalniz_bitis_isaretidir() -> None:
    assert _tuket(DOSYA_BOLUMU_SONU, _tam_manifesto()) == []


def test_eksik_ek_bolumde_aranmaz() -> None:
    manifesto = _tam_manifesto(_G1, _girdi(_AD_3, b"yok", eksik=True), _G2)
    assert [ad for ad, _ in _tuket(_B1 + _B2 + DOSYA_BOLUMU_SONU, manifesto)] == [_AD_1, _AD_2]


def test_eksik_ek_bolumde_duruyorsa_kap_duzeyinde_reddedilir() -> None:
    manifesto = _tam_manifesto(_G1, _girdi(_AD_2, _ACIK_2, eksik=True))
    with pytest.raises(DosyaBolumuHatasi):
        _tuket(_B1 + _B2 + DOSYA_BOLUMU_SONU, manifesto)


@pytest.mark.parametrize(
    "bolum",
    [
        _B2 + _B1 + DOSYA_BOLUMU_SONU,
        _B1 + bolum_girdisi(_AD_3.encode("ascii"), _govde(_ACIK_2)) + DOSYA_BOLUMU_SONU,
        _B1 + _B1 + DOSYA_BOLUMU_SONU,
        bolum_girdisi(b"../../guvenlik.json".ljust(32, b"\x00"), _govde(_ACIK_1)) + _B2,
        _B1 + DOSYA_BOLUMU_SONU,
        DOSYA_BOLUMU_SONU,
        _B1 + _B2 + _B2 + DOSYA_BOLUMU_SONU,
        _B1 + _B2,
        _B1 + _B2 + bytes(len(DOSYA_BOLUMU_SONU)),
        _B1 + _B2 + DOSYA_BOLUMU_SONU + b"\x00",
        _B1 + _B2 + DOSYA_BOLUMU_SONU + DOSYA_BOLUMU_SONU,
    ],
    ids=[
        "sira_bozuk",
        "manifestoda_olmayan_ad",
        "ayni_girdi_iki_kez",
        "yol_gecisi_adi",
        "erken_bitis",
        "yalniz_bitis",
        "fazla_girdi",
        "bitis_yok",
        "sifirla_dolu_kuyruk",
        "bitisten_sonra_bayt",
        "iki_bitis",
    ],
)
def test_bolumun_yapisi_bozuksa_kap_duzeyinde_reddedilir(bolum: bytes) -> None:
    with pytest.raises(DosyaBolumuHatasi):
        _tuket(bolum, _IKI_EK)


def test_bolum_hicbir_noktada_kesilemez() -> None:
    bolum = _B1 + _B2 + DOSYA_BOLUMU_SONU
    for boy in range(len(bolum)):
        with pytest.raises(DosyaBolumuHatasi):
            _tuket(bolum[:boy], _IKI_EK)


def test_kesik_govde_parcalar_icinde_kap_duzeyinde_duser() -> None:
    akis = io.BytesIO(_B1[:-1])
    girdi = next(dosya_bolumunu_oku(akis, _IKI_EK))
    with pytest.raises(DosyaBolumuHatasi):
        list(girdi.parcalar())


@pytest.mark.parametrize(
    "boy",
    [DOSYA_AZAMI_SIFRELI_BOY + 1, 2**40, 2**64 - 1, len(_govde(_ACIK_1)) - 1, 0],
    ids=["sinir_ustu", "dev", "en_buyuk", "manifestodan_kisa", "sifir"],
)
def test_boy_alani_tutmayan_girdi_govde_okunmadan_reddedilir(boy: int) -> None:
    """64 MiB üstü ya da manifestoyu tutmayan boy alanı büyük bir okumaya yol açamaz."""
    akis = _SayanAkis(bolum_girdisi(_AD_1.encode("ascii"), _govde(_ACIK_1), boy=boy))

    with pytest.raises(DosyaBolumuHatasi):
        next(dosya_bolumunu_oku(akis, _IKI_EK))

    assert akis.okunan == 40


def test_govdesi_okunmayan_girdi_atlanir() -> None:
    """Kısmen ya da hiç okunmayan gövde sonraki girdiyi kaydırmaz."""
    akis = io.BytesIO(_B1 + _B2 + DOSYA_BOLUMU_SONU)
    adlar = []
    for sira, girdi in enumerate(dosya_bolumunu_oku(akis, _IKI_EK)):
        adlar.append(girdi.girdi.ad)
        if sira == 0:
            next(girdi.parcalar())
    assert adlar == [_AD_1, _AD_2]


def test_atlanan_kesik_govde_de_kap_duzeyinde_duser() -> None:
    with pytest.raises(DosyaBolumuHatasi):
        for _ in dosya_bolumunu_oku(io.BytesIO(_B1[:-1]), _IKI_EK):
            pass


def test_ozeti_tutmayan_ek_girdi_duzeyindedir() -> None:
    """Yapı sağlamken içerik tutmuyorsa kap hatası değil, adı bilinen girdi hatasıdır."""
    ek_denetle(_G1, _ACIK_1)
    with pytest.raises(EkTutmuyorHatasi) as hata:
        ek_denetle(_G1, b"X" * len(_ACIK_1))
    assert hata.value.ad == _AD_1
    with pytest.raises(EkTutmuyorHatasi):
        ek_denetle(_G1, _ACIK_1 + b"x")
    with pytest.raises(EkTutmuyorHatasi):
        ek_denetle(ManifestoGirdisi(_AD_1, len(_ACIK_1) + 1, _ozet(_ACIK_1)), _ACIK_1)


def test_kap_duzeyi_ile_girdi_duzeyi_ayri_siniflardir() -> None:
    """Kullanıcı kararı "Bozuk ekte geri yükleme durur, ikinci onayla sürer": biri ötekini
    yakalamamalıdır, yoksa kap düzeyindeki bozukluk onayla sürdürülebilirdi."""
    assert not issubclass(DosyaBolumuHatasi, EkTutmuyorHatasi)
    assert not issubclass(EkTutmuyorHatasi, DosyaBolumuHatasi)
    assert issubclass(DosyaBolumuHatasi, BackupCryptoError)
    assert issubclass(EkTutmuyorHatasi, BackupCryptoError)


# ---------------------------------------------------------------- akışla yazım ve bellek
@pytest.fixture
def acik_anahtar() -> X25519PublicKey:
    return private_key_from_data_key(_DEK).public_key()


def test_tam_yedek_bellekte_toplanmaz(tmp_path: Path, acik_anahtar: X25519PublicKey) -> None:
    """Büyük gövde parça parça geçer: yazımda ve okumada tepe bellek gövdenin çok altındadır."""
    depo = tmp_path / "dosyalar"
    depo.mkdir()
    boy = 48 * 1024 * 1024
    with (depo / _AD_1).open("wb") as dosya:
        dosya.truncate(boy)  # seyrek dosya: test diski doldurmaz
    girdi = ManifestoGirdisi(_AD_1, boy - DOSYA_KAP_EK_BAYT, "a" * 64)
    hedef = tmp_path / "tam.odbak"

    tracemalloc.start()
    try:
        manifesto = tam_yedek_yaz(hedef, _DB, [girdi], depo, acik_anahtar, recovery_header=_BASLIK)
        yazim_tepesi = tracemalloc.get_traced_memory()[1]
        tracemalloc.reset_peak()
        toplam = 0
        with hedef.open("rb") as akis:
            akis.seek(kap_basligini_oku(hedef).dosya_bolumu_konumu)
            for okunan in dosya_bolumunu_oku(akis, manifesto):
                for parca in okunan.parcalar():
                    assert len(parca) <= KOPYA_PARCASI
                    toplam += len(parca)
        okuma_tepesi = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()

    assert toplam == boy
    assert yazim_tepesi < 4 * KOPYA_PARCASI
    assert okuma_tepesi < 4 * KOPYA_PARCASI


def test_okuyucu_parcadan_buyuk_okuma_istemez() -> None:
    boy = 3 * KOPYA_PARCASI + 5
    govde = bytes(boy)
    girdi = ManifestoGirdisi(_AD_1, boy - DOSYA_KAP_EK_BAYT, "a" * 64)
    akis = _SayanAkis(
        bolum_girdisi(_AD_1.encode("ascii"), govde) + DOSYA_BOLUMU_SONU,
    )

    parcalar = [
        len(parca)
        for okunan in dosya_bolumunu_oku(akis, _tam_manifesto(girdi))
        for parca in okunan.parcalar()
    ]

    assert parcalar == [KOPYA_PARCASI] * 3 + [5]
    assert akis.en_buyuk_istek == KOPYA_PARCASI


@pytest.mark.parametrize("durum", ["yok", "kisa", "uzun", "dizin"])
def test_diskte_duzgun_bulunmayan_ek_eksik_isaretlenir_yedek_yine_alinir(
    tmp_path: Path, acik_anahtar: X25519PublicKey, durum: str
) -> None:
    """Plan "Kap ve manifesto": yedeksiz kalmak eksik ekli yedekten ağırdır. Boyu tutmayan dosya
    taşınsaydı okuyucu bütün yedeği kap düzeyinde reddederdi."""
    depo = tmp_path / "dosyalar"
    girdiler = _depo(depo, **{_AD_1: b"saglam", _AD_2: b"bozulan"})
    bozulan = depo / _AD_2
    bozulan.unlink()
    if durum == "kisa":
        bozulan.write_bytes(_govde(b"bozulan")[:-1])
    elif durum == "uzun":
        bozulan.write_bytes(_govde(b"bozulan") + b"x")
    elif durum == "dizin":
        bozulan.mkdir()
    hedef = tmp_path / "tam.odbak"

    manifesto = tam_yedek_yaz(
        hedef, _DB, list(girdiler.values()), depo, acik_anahtar, recovery_header=_BASLIK
    )

    assert [g.eksik for g in manifesto.dosyalar] == [False, True]
    assert manifesto.tasinanlar == (girdiler[_AD_1],)
    assert decrypt_bytes(hedef.read_bytes(), _DEK).manifesto == manifesto


def _acilamayan_ek(monkeypatch: pytest.MonkeyPatch, yol: Path, hata: OSError) -> list[int]:
    """`yol` açılırken `hata` verir; öteki açılışların tanıtıcılarını döndürülen listeye yazar.

    Test konteynerde kök kullanıcıyla koşar: kip 000 etkisizdir, açılış hatası taklit edilir.
    """
    gercek = os.open
    acilanlar: list[int] = []

    def sahte(hedef: Any, bayraklar: int, *args: Any, **kwargs: Any) -> int:
        if Path(hedef) == yol:
            raise hata
        tanitici = gercek(hedef, bayraklar, *args, **kwargs)
        acilanlar.append(tanitici)
        return tanitici

    monkeypatch.setattr(os, "open", sahte)
    return acilanlar


@pytest.mark.parametrize(
    "hata",
    [PermissionError(13, "Permission denied"), OSError(5, "Input/output error")],
    ids=["paylasim_ihlali", "disk_hatasi"],
)
def test_acilamayan_ek_eksik_isaretlenir_yedek_yine_alinir(
    tmp_path: Path,
    acik_anahtar: X25519PublicKey,
    monkeypatch: pytest.MonkeyPatch,
    hata: OSError,
) -> None:
    """Karar mühürden önce verilir: dosya diskte düzgün görünse de açılamıyorsa manifesto onu
    `eksik` yazar, sağlam ek ve veritabanı yedeğe girer (yedeksiz kalmak daha ağırdır)."""
    depo = tmp_path / "dosyalar"
    girdiler = _depo(depo, **{_AD_1: b"saglam", _AD_2: b"acilamayan"})
    _acilamayan_ek(monkeypatch, depo / _AD_2, hata)
    hedef = tmp_path / "tam.odbak"

    manifesto = tam_yedek_yaz(
        hedef, _DB, list(girdiler.values()), depo, acik_anahtar, recovery_header=_BASLIK
    )

    assert [g.eksik for g in manifesto.dosyalar] == [False, True]
    assert manifesto.tasinanlar == (girdiler[_AD_1],)
    icerik = decrypt_bytes(hedef.read_bytes(), _DEK)
    assert icerik.veritabani == _DB and icerik.manifesto == manifesto


def test_caginin_eksik_verdigi_ek_saglam_dosyayla_da_tasinmaz(tmp_path: Path) -> None:
    """Ön okumanın kararı korunur (kullanıcı kararı 05.11.2026): bu katman DEK'i tanımaz, dosyanın
    diskte sağlam görünmesi çağıranın kararını geri almaz."""
    depo = tmp_path / "dosyalar"
    girdi = _depo(depo, **{_AD_1: b"saglam"})[_AD_1]

    assert backup_crypto._diskteki_hali(replace(girdi, eksik=True), depo).eksik is True
    assert backup_crypto._diskteki_hali(girdi, depo).eksik is False


def test_ek_sinanirken_acilan_dosya_kapatilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows'ta açık kalan tanıtıcı dosyayı kilitler, POSIX'te tükenir."""
    depo = tmp_path / "dosyalar"
    girdi = _depo(depo, **{_AD_1: b"saglam"})[_AD_1]
    acilanlar = _acilamayan_ek(monkeypatch, tmp_path / "ilgisiz", OSError(5, "Input/output error"))

    assert backup_crypto._diskteki_hali(girdi, depo).eksik is False

    assert len(acilanlar) == 1
    with pytest.raises(OSError, match="Bad file descriptor"):
        os.fstat(acilanlar[0])


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO POSIX'te sınanır")
def test_duzenli_olmayan_ek_acilmadan_eksik_sayilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`lstat` açmadan önce eler: düzenli olmayan dosya hiç açılmaz (`O_NONBLOCK` FIFO'nun
    beklemesini ayrıca keser; açılış yasaklanarak ilk elemenin yeri sabitlenir)."""
    depo = tmp_path / "dosyalar"
    girdi = _depo(depo, **{_AD_1: b"saglam"})[_AD_1]
    (depo / _AD_1).unlink()
    os.mkfifo(depo / _AD_1)

    def acilmamali(*args: Any, **kwargs: Any) -> int:
        raise AssertionError("düzenli olmayan dosya açılmamalıydı")

    monkeypatch.setattr(os, "open", acilmamali)

    assert backup_crypto._diskteki_hali(girdi, depo).eksik is True


@pytest.mark.skipif(os.name != "posix", reason="sembolik bağ POSIX'te sınanır")
@pytest.mark.parametrize("bag", ["saglam_dosyaya_giden", "kendi_boyu_kabinki_kadar"])
def test_sembolik_bag_ek_sayilmaz(tmp_path: Path, acik_anahtar: X25519PublicKey, bag: str) -> None:
    """Depoda yalnız düzenli dosya ek sayılır: bağın hedefi sağlam olsa da, bağın kendi boyu
    kabınkiyle aynı olsa da (boy denetimi yakalamazdı) ek `eksik` işaretlenir."""
    depo = tmp_path / "dosyalar"
    girdiler = _depo(depo, **{_AD_1: b"saglam"})
    if bag == "saglam_dosyaya_giden":
        (depo / _AD_1).rename(tmp_path / "disarida")
        (depo / _AD_1).symlink_to(tmp_path / "disarida")
    else:
        (depo / _AD_1).unlink()
        (depo / _AD_1).symlink_to("x" * girdiler[_AD_1].sifreli_boy)

    manifesto = tam_yedek_yaz(
        tmp_path / "tam.odbak",
        _DB,
        list(girdiler.values()),
        depo,
        acik_anahtar,
        recovery_header=_BASLIK,
    )

    assert manifesto.dosyalar[0].eksik is True


def test_var_olan_dosyanin_uzerine_tam_yedek_yazilmaz(
    tmp_path: Path, acik_anahtar: X25519PublicKey
) -> None:
    hedef = tmp_path / "tam.odbak"
    hedef.write_bytes(b"onceki-yedek")

    with pytest.raises(FileExistsError):
        tam_yedek_yaz(hedef, _DB, [], tmp_path, acik_anahtar, recovery_header=_BASLIK)

    assert hedef.read_bytes() == b"onceki-yedek"


def test_yazim_duserse_yarim_tam_yedek_kalmaz(
    tmp_path: Path, acik_anahtar: X25519PublicKey, monkeypatch: pytest.MonkeyPatch
) -> None:
    depo = tmp_path / "dosyalar"
    girdiler = _depo(depo, **{_AD_1: b"ek"})
    hedef = tmp_path / "tam.odbak"

    def disk_doldu(*_a: object) -> None:
        raise OSError("disk dolu")

    monkeypatch.setattr(backup_crypto, "_ek_govdesini_kopyala", disk_doldu)
    with pytest.raises(OSError, match="disk dolu"):
        tam_yedek_yaz(
            hedef, _DB, list(girdiler.values()), depo, acik_anahtar, recovery_header=_BASLIK
        )

    assert not hedef.exists()


@pytest.mark.parametrize("fark", [-1, 1], ids=["kucuk", "buyuk"])
def test_yazim_sirasinda_boyu_degisen_ek_yedegi_durdurur(tmp_path: Path, fark: int) -> None:
    """Manifesto mühürlendikten sonra boyu değişen dosya taşınamaz: yedek kap düzeyinde bozulurdu."""
    kaynak = tmp_path / _AD_1
    kaynak.write_bytes(_govde(b"ek"))

    with pytest.raises(BackupCryptoError, match="değişti"):
        backup_crypto._ek_govdesini_kopyala(io.BytesIO(), kaynak, kaynak.stat().st_size + fark)


# ---------------------------------------------------------------- başlıksız yedek üretilmez
@pytest.mark.parametrize(
    "baslik",
    [
        b"",
        b"{}",
        b'{"surum":1,"kdf":{},"parola":{"salt":"eA==","sarmal":"eA=="}}',
        b'{"surum":2,"kdf":{},"hesaplar":[{"id":"x","tanitici":"y","salt":"eA==","sarmal":"eA=="}]}',
    ],
    ids=["bos", "bos_nesne", "sema_1", "kurtarma_bolumu_yok"],
)
def test_kullanilamaz_baslikla_yedek_yazilmaz(
    tmp_path: Path, acik_anahtar: X25519PublicKey, baslik: bytes
) -> None:
    hedef = tmp_path / "yedek.odbak"
    tam = tmp_path / "tam.odbak"

    with pytest.raises(BackupCryptoError, match="Kurtarma başlığı"):
        encrypt_bytes(_DB, acik_anahtar, recovery_header=baslik)
    with pytest.raises(BackupCryptoError, match="Kurtarma başlığı"):
        encrypt_to_path(_DB, hedef, acik_anahtar, recovery_header=baslik)
    with pytest.raises(BackupCryptoError, match="Kurtarma başlığı"):
        tam_yedek_yaz(tam, _DB, [], tmp_path, acik_anahtar, recovery_header=baslik)

    assert not hedef.exists() and not tam.exists()


def test_arsiv_kopyasina_dusen_baslik_okuyucusu_kalkti() -> None:
    assert not hasattr(backup_crypto, "recovery_metadata")


def test_buyuk_kurtarma_basligi_yazilmaz(acik_anahtar: X25519PublicKey) -> None:
    with pytest.raises(BackupCryptoError, match="beklenenden büyük"):
        kap_kur(_DB, _DEK, baslik=bytes(MAX_RECOVERY_HEADER_BYTES + 1))


def test_tek_yedege_sigmayan_veritabani_acik_hatayla_durur(
    acik_anahtar: X25519PublicKey, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(backup_crypto, "_AZAMI_MUHURLU_BOY", len(_DB))
    with pytest.raises(BackupCryptoError, match="sığmayacak"):
        encrypt_bytes(_DB, acik_anahtar, recovery_header=_BASLIK)


def test_tam_manifesto_bellekte_kurulmaz(acik_anahtar: X25519PublicKey) -> None:
    """Dosya bölümü olmayan tam yedek üretilemez: `encrypt_bytes` yalnız yerel kap kurar."""
    with pytest.raises(BackupCryptoError, match="Tam yedek"):
        encrypt_bytes(_DB, acik_anahtar, recovery_header=_BASLIK, manifesto=_tam_manifesto())


# ---------------------------------------------------------------- yazım: kip ve atomiklik
@pytest.fixture
def umask_degistir() -> Iterator[Any]:
    eski = os.umask(0o077)
    os.umask(eski)
    try:
        yield os.umask
    finally:
        os.umask(eski)


@pytest.mark.skipif(os.name != "posix", reason="kip POSIX'te sınanır")
@pytest.mark.parametrize("umask", [0o000, 0o022, 0o277], ids=["acik", "olagan", "dar"])
def test_yedek_dosyasi_umasktan_bagimsiz_0600_yazilir(
    tmp_path: Path, acik_anahtar: X25519PublicKey, umask_degistir: Any, umask: int
) -> None:
    """Tasarım §4.5: yazıcılar umask'a güvenmez; `manage.py` yolunda umask ayarlı değildir."""
    yerel = tmp_path / "gunluk-2026-08-01.odbak"
    tam = tmp_path / "tam.odbak"
    umask_degistir(umask)

    encrypt_to_path(_DB, yerel, acik_anahtar, recovery_header=_BASLIK)
    tam_yedek_yaz(tam, _DB, [], tmp_path, acik_anahtar, recovery_header=_BASLIK)

    assert stat.S_IMODE(yerel.stat().st_mode) == 0o600
    assert stat.S_IMODE(tam.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "posix", reason="kip POSIX'te sınanır")
def test_gecici_dosya_da_baslangictan_0600dur(
    tmp_path: Path,
    acik_anahtar: X25519PublicKey,
    umask_degistir: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Geniş kipli bir anı yoktur: dosya yerine konmadan önce de kipi 0600'dür."""
    hedef = tmp_path / "gunluk-2026-08-01.odbak"
    goruler: list[int] = []
    gercek = os.replace

    def goren_replace(kaynak: Path, yeni: Path) -> None:
        goruler.append(stat.S_IMODE(Path(kaynak).stat().st_mode))
        gercek(kaynak, yeni)

    monkeypatch.setattr(os, "replace", goren_replace)
    umask_degistir(0o000)

    encrypt_to_path(_DB, hedef, acik_anahtar, recovery_header=_BASLIK)

    assert goruler == [0o600]


def test_yerel_yedek_yazimi_atomiktir(
    tmp_path: Path, acik_anahtar: X25519PublicKey, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Yerine koyma düşerse eski yedek durur, geçici dosya kalmaz."""
    hedef = tmp_path / "gunluk-2026-08-01.odbak"
    hedef.write_bytes(b"onceki")

    def yerine_konamadi(*_a: object) -> None:
        raise OSError("kilitli")

    monkeypatch.setattr(os, "replace", yerine_konamadi)
    with pytest.raises(OSError, match="kilitli"):
        encrypt_to_path(_DB, hedef, acik_anahtar, recovery_header=_BASLIK)

    assert hedef.read_bytes() == b"onceki"
    assert [yol.name for yol in tmp_path.iterdir()] == [hedef.name]


def test_onceki_kesintiden_kalan_gecici_dosya_yazimi_engellemez(
    tmp_path: Path, acik_anahtar: X25519PublicKey
) -> None:
    hedef = tmp_path / "gunluk-2026-08-01.odbak"
    hedef.with_name(hedef.name + ".tmp").write_bytes(b"yarim")

    encrypt_to_path(_DB, hedef, acik_anahtar, recovery_header=_BASLIK)

    assert decrypt_bytes(hedef.read_bytes(), _DEK).veritabani == _DB
    assert [yol.name for yol in tmp_path.iterdir()] == [hedef.name]


def test_yazim_diske_indirilir(
    tmp_path: Path, acik_anahtar: X25519PublicKey, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Elektrik kesintisinde adı yeni, içeriği boş yedek kalmasın: `os.replace`'ten önce `fsync`."""
    olaylar: list[str] = []
    gercek_fsync = os.fsync
    gercek_replace = os.replace

    def fsync(tanitici: int) -> None:
        olaylar.append("fsync")
        gercek_fsync(tanitici)

    def replace(kaynak: Path, yeni: Path) -> None:
        olaylar.append("replace")
        gercek_replace(kaynak, yeni)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "replace", replace)

    encrypt_to_path(
        _DB, tmp_path / "gunluk-2026-08-01.odbak", acik_anahtar, recovery_header=_BASLIK
    )

    assert olaylar[:2] == ["fsync", "replace"]
