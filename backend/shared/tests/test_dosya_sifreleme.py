"""`shared.dosya_sifreleme` birim testleri — dosya kabı, sarmal, depo adı, tür, atomik yazım.

Tasarım TK22, §4.4.4 "Dosya anahtarı", §4.4.7; plan F1b-3 "Dosya deposu". DB istemez. Bütün
içerikler uydurmadır (KVKK): gerçek bir belge, ad ya da numara taşımaz. Altın vektörler DONMUŞTUR:
kap ya da sarmal biçimi değişirse depodaki ve yedeklerdeki bütün ekler açılmaz olur.
"""

from __future__ import annotations

import ast
import base64
import errno
import hashlib
import os
import socket
import stat
import sys
import threading
import uuid
from collections.abc import Callable
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from conftest import TEST_DEK
from shared import crypto
from shared import dosya_sifreleme as ds

#: Altın vektör girdileri (uydurma).
_DOSYA_ANAHTARI = bytes(range(32, 64))
_AD = "6f1c2a3b4d5e4f608a710b2c3d4e5f60"
_BASKA_AD = "0b4c2d1e7a3f4e5d9c8b1a2b3c4d5e6f"
_ACIK = b"%PDF-1.7\n% uydurma ek\n"
_KAP_NONCE = bytes(range(100, 112))
_SARMAL_NONCE = bytes(range(200, 212))

#: DONMUŞ değerler (tasarım §2.3.1 MAGIC ve HKDF dizgesi; plan F1b-3 "Dosya deposu").
_ALTIN_SARMAL_ANAHTARI = "ebaf847c939314dead95db481a93f68b2d089ed59c0a0dfa0a31193c31683a40"
_ALTIN_KAP = (
    "4f44444f53594101"  # ODDOSYA\x01
    "6465666768696a6b6c6d6e6f"  # nonce
    "903dca95f280dafad671ffadf373eb1fa4e3c51b55c048"  # şifreli metin (23 bayt)
    "cc4c60a2a5fd9fb171a437987f36ab"  # etiket (16 bayt)
)
_ALTIN_KEY_WRAP = "yMnKy8zNzs/Q0dLTFKZUJFAb+kEJg//IWM4o/ftLmY9mI00RYTS7RtkYE6MzACz+XjHqCt1c7XTsJ3Ik"


def _sarmal_anahtari() -> bytes:
    return crypto.file_wrap_key(TEST_DEK)


def _altin_kap() -> bytes:
    return ds._kap_kur(_ACIK, _DOSYA_ANAHTARI, _AD, _KAP_NONCE)


# ---------------------------------------------------------------------------
# Altın vektörler
# ---------------------------------------------------------------------------
def test_altin_vektor_kap_baytlari_donmustur() -> None:
    """`ODDOSYA\\x01` ‖ nonce ‖ AES-256-GCM(şifreli metin ‖ etiket), AAD = depo adının ASCII'si.

    Kap hem donmuş baytla hem `cryptography` ile yeniden kurularak karşılaştırılır: AAD'yi,
    MAGIC'i, alan sırasını ya da algoritmayı değiştiren her değişiklik bu testi düşürür."""
    assert ds.MAGIC == b"ODDOSYA\x01"
    kap = _altin_kap()
    beklenen = (
        ds.MAGIC
        + _KAP_NONCE
        + AESGCM(_DOSYA_ANAHTARI).encrypt(_KAP_NONCE, _ACIK, _AD.encode("ascii"))
    )
    assert kap == beklenen
    assert kap.hex() == _ALTIN_KAP
    assert len(kap) == ds.sifreli_boy(len(_ACIK)) == len(_ACIK) + 36
    assert ds.coz(kap, dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD) == _ACIK


def test_altin_vektor_key_wrap_donmustur() -> None:
    """`key_wrap` = base64(nonce 12 ‖ şifreli anahtar 32 ‖ etiket 16): 80 karakter, standart alfabe.

    Sarmal anahtarı `HKDF(DEK, "od-dosya-sarmal/v1")`'dir (tasarım §4.4.4); formül açıkça yeniden
    hesaplanır. Donmuş metin hem `+` hem `/` taşır: URL-güvenli alfabeye geçiş de düşer."""
    sarmal = _sarmal_anahtari()
    assert sarmal == HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None, info=b"od-dosya-sarmal/v1"
    ).derive(TEST_DEK)
    assert sarmal.hex() == _ALTIN_SARMAL_ANAHTARI
    key_wrap = ds._sar(_DOSYA_ANAHTARI, sarmal, _AD, _SARMAL_NONCE)
    ham = _SARMAL_NONCE + AESGCM(sarmal).encrypt(
        _SARMAL_NONCE, _DOSYA_ANAHTARI, _AD.encode("ascii")
    )
    assert key_wrap == base64.b64encode(ham).decode("ascii")
    assert key_wrap == _ALTIN_KEY_WRAP
    assert len(key_wrap) == ds.KEY_WRAP_UZUNLUK == 80
    assert ds.anahtari_ac(key_wrap, sarmal_anahtari=sarmal, stored_name=_AD) == _DOSYA_ANAHTARI


def test_bicim_sabitleri_tasarimdakidir() -> None:
    """Biçim üst sınırı 64 MiB şifrelidir; açık sınır ondan 36 bayt azdır (plan F1b-3)."""
    assert ds.AZAMI_SIFRELI_BOY == 64 * 1024 * 1024
    assert ds.KAP_EK_BAYT == 36
    assert ds.AZAMI_ACIK_BOY == 64 * 1024 * 1024 - 36
    assert ds.DOSYA_KIPI == 0o600


# ---------------------------------------------------------------------------
# Tur dönüşü, özet ve boy
# ---------------------------------------------------------------------------
def test_dosya_hazirla_tur_donusu_ve_acik_ozet() -> None:
    """Hazırlanan dosya açılınca aynı baytları verir; `sha256` ve `size` AÇIK içeriğindir."""
    acik = b"\x89PNG\r\n\x1a\n" + b"uydurma-gorsel" * 50
    hazir = ds.dosya_hazirla(acik, sarmal_anahtari=_sarmal_anahtari())
    assert hazir.mime == "image/png"
    assert hazir.size == len(acik)
    assert hazir.sha256 == hashlib.sha256(acik).hexdigest() == ds.acik_ozet(acik)
    assert hazir.sha256 != hashlib.sha256(hazir.kap).hexdigest()
    assert len(hazir.kap) == ds.sifreli_boy(hazir.size)
    assert ds.DEPO_ADI_DESENI.fullmatch(hazir.stored_name)
    assert uuid.UUID(hex=hazir.stored_name).version == 4
    assert len(hazir.key_wrap) == 80
    assert acik not in hazir.kap
    anahtar = ds.anahtari_ac(
        hazir.key_wrap, sarmal_anahtari=_sarmal_anahtari(), stored_name=hazir.stored_name
    )
    assert ds.coz(hazir.kap, dosya_anahtari=anahtar, stored_name=hazir.stored_name) == acik
    assert "kap=" not in repr(hazir)


def test_her_dosya_kendi_adini_anahtarini_ve_nonce_unu_alir() -> None:
    """Dosya anahtarı DEK'ten türemez, rastgeledir (tasarım §4.4.4): aynı içerik iki kez
    hazırlanınca ad, kap ve sarmal ayrışır; anahtarlar birbirinin kabını açmaz."""
    sarmal = _sarmal_anahtari()
    bir = ds.dosya_hazirla(_ACIK, sarmal_anahtari=sarmal)
    iki = ds.dosya_hazirla(_ACIK, sarmal_anahtari=sarmal)
    assert bir.stored_name != iki.stored_name
    assert bir.kap != iki.kap
    assert bir.key_wrap != iki.key_wrap
    # Sarmal anahtarı bütün eklerde aynıdır: nonce tekrarı AES-GCM'i orada kırar (§4.4.4).
    assert bir.kap[8:20] != iki.kap[8:20]
    assert base64.b64decode(bir.key_wrap)[:12] != base64.b64decode(iki.key_wrap)[:12]
    assert bir.sha256 == iki.sha256
    bir_anahtar = ds.anahtari_ac(bir.key_wrap, sarmal_anahtari=sarmal, stored_name=bir.stored_name)
    with pytest.raises(ds.DogrulamaHatasi):
        ds.coz(iki.kap, dosya_anahtari=bir_anahtar, stored_name=iki.stored_name)
    assert bir_anahtar not in {TEST_DEK, sarmal}


def test_depoya_yaz_ve_depodan_ac_tur_donusu(tmp_path: Path) -> None:
    hazir = ds.dosya_hazirla(_ACIK, sarmal_anahtari=_sarmal_anahtari())
    yol = ds.depoya_yaz(tmp_path, hazir.stored_name, hazir.kap)
    assert yol == tmp_path / hazir.stored_name
    assert sorted(p.name for p in tmp_path.iterdir()) == [hazir.stored_name]
    assert yol.read_bytes() == hazir.kap
    acik = ds.depodan_ac(
        tmp_path,
        hazir.stored_name,
        key_wrap=hazir.key_wrap,
        sarmal_anahtari=_sarmal_anahtari(),
    )
    assert acik == _ACIK


def test_depodan_ac_dosya_yoksa_dosya_bulunamadi_verir(tmp_path: Path) -> None:
    """Bu katman yalnız `FileNotFoundError` verir; "dosya yok" depo servisinin kararıdır."""
    with pytest.raises(FileNotFoundError):
        ds.depodan_ac(tmp_path, _AD, key_wrap=_ALTIN_KEY_WRAP, sarmal_anahtari=_sarmal_anahtari())


# ---------------------------------------------------------------------------
# AAD bağı, yanlış anahtar, bit çevirme, kesik kap
# ---------------------------------------------------------------------------
def test_kap_baska_depo_adiyla_acilmaz() -> None:
    """AAD = depo adı: dosya başka bir satırın adıyla konursa açılmaz (tasarım §4.4.4)."""
    with pytest.raises(ds.DogrulamaHatasi):
        ds.coz(_altin_kap(), dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_BASKA_AD)


def test_sarmal_baska_depo_adiyla_acilmaz() -> None:
    """Sarmal da depo adına bağlıdır: başka satıra taşınan `key_wrap` açılmaz."""
    with pytest.raises(ds.DogrulamaHatasi):
        ds.anahtari_ac(_ALTIN_KEY_WRAP, sarmal_anahtari=_sarmal_anahtari(), stored_name=_BASKA_AD)


def test_yanlis_dosya_anahtariyla_kap_acilmaz() -> None:
    with pytest.raises(ds.DogrulamaHatasi):
        ds.coz(_altin_kap(), dosya_anahtari=bytes(32), stored_name=_AD)


def test_sarmal_baska_dek_ile_ve_dek_in_kendisiyle_acilmaz() -> None:
    """Sarmal anahtarı DEK'in HKDF türevidir: başka DEK'in türevi de, türetilmemiş DEK de açmaz."""
    baska = crypto.file_wrap_key(bytes(range(1, 33)))
    for anahtar in (baska, TEST_DEK):
        with pytest.raises(ds.DogrulamaHatasi):
            ds.anahtari_ac(_ALTIN_KEY_WRAP, sarmal_anahtari=anahtar, stored_name=_AD)


def test_kabin_her_baytinda_cevrilen_bit_reddedilir() -> None:
    """MAGIC'teki bit biçim hatasıdır; nonce, şifreli metin ve etiketteki bit GCM'de düşer."""
    kap = _altin_kap()
    for konum in range(len(kap)):
        bozuk = bytearray(kap)
        bozuk[konum] ^= 0x01
        beklenen = ds.KapBicimiHatasi if konum < len(ds.MAGIC) else ds.DogrulamaHatasi
        with pytest.raises(beklenen) as hata:
            ds.coz(bytes(bozuk), dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD)
        assert type(hata.value) is beklenen, konum


def test_sarmalin_her_baytinda_cevrilen_bit_reddedilir() -> None:
    ham = base64.b64decode(_ALTIN_KEY_WRAP)
    for konum in range(len(ham)):
        bozuk = bytearray(ham)
        bozuk[konum] ^= 0x80
        metin = base64.b64encode(bytes(bozuk)).decode("ascii")
        with pytest.raises(ds.DogrulamaHatasi):
            ds.anahtari_ac(metin, sarmal_anahtari=_sarmal_anahtari(), stored_name=_AD)


def test_kesik_kap_reddedilir() -> None:
    """En kısa kaptan (36 bayt) kısası `KesikKapHatasi`; gövdesi kesilmiş ya da uzatılmış kap GCM'de
    düşer (`DogrulamaHatasi`). Boş dosya da kesiktir."""
    kap = _altin_kap()
    for boy in range(ds.KAP_EK_BAYT):
        with pytest.raises(ds.KesikKapHatasi):
            ds.coz(kap[:boy], dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD)
    for boy in range(ds.KAP_EK_BAYT, len(kap)):
        with pytest.raises(ds.DogrulamaHatasi):
            ds.coz(kap[:boy], dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD)
    with pytest.raises(ds.DogrulamaHatasi):
        ds.coz(kap + b"\x00", dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD)


@pytest.mark.parametrize(
    "kap",
    [
        b"ODDOSYA\x02" + bytes(40),  # başka sürüm: bu sürüm açmaz
        b"ODBAK\x03" + bytes(40),  # yedek kabı
        _ACIK + bytes(40),  # şifrelenmemiş açık dosya depoya konmuş
        b"abc",  # MAGIC'in öneki olmayan kısa çöp kesik sayılmaz
    ],
    ids=["baska_surum", "yedek_kabi", "acik_dosya", "kisa_cop"],
)
def test_tanimayan_kap_bicim_hatasi_verir(kap: bytes) -> None:
    with pytest.raises(ds.KapBicimiHatasi) as hata:
        ds.coz(kap, dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD)
    assert type(hata.value) is ds.KapBicimiHatasi


def test_istisnalarin_iletisi_turkcedir_ve_ad_ya_da_anahtar_tasimaz() -> None:
    with pytest.raises(ds.DogrulamaHatasi) as hata:
        ds.coz(_altin_kap(), dosya_anahtari=bytes(32), stored_name=_BASKA_AD)
    ileti = str(hata.value)
    assert "doğrulanamadı" in ileti
    assert _BASKA_AD not in ileti and _DOSYA_ANAHTARI.hex() not in ileti
    assert issubclass(ds.DogrulamaHatasi, ds.DosyaSifrelemeHatasi)
    assert issubclass(ds.DosyaSifrelemeHatasi, ValueError)


@pytest.mark.parametrize(
    "key_wrap",
    [
        _ALTIN_KEY_WRAP[:-1],  # 79 karakter
        _ALTIN_KEY_WRAP + "A",  # 81 karakter
        _ALTIN_KEY_WRAP[:-1] + "\n",  # satır sonu
        _ALTIN_KEY_WRAP[:-1] + " ",  # boşluk
        _ALTIN_KEY_WRAP.replace("+", "-").replace("/", "_"),  # URL-güvenli alfabe
        _ALTIN_KEY_WRAP[:-1] + "ç",  # ASCII dışı
        base64.b64encode(bytes(58)).decode("ascii"),  # 80 karakter ama dolgulu, 58 bayt
        "",
        # Satırlara bölünmüş geçerli sarmal (84 karakter): hoşgörülü çözücü satır sonlarını atıp
        # 60 bayt bulurdu. Uzunluk ve katı alfabe denetiminden biri tek başına bunu keser.
        "\n".join(_ALTIN_KEY_WRAP[i : i + 20] for i in range(0, 80, 20)) + "\n",
    ],
    ids=[
        "kisa",
        "uzun",
        "satir_sonu",
        "bosluk",
        "url_guvenli",
        "ascii_disi",
        "dolgulu",
        "bos",
        "satirlara_bolunmus",
    ],
)
def test_bicimi_tutmayan_sarmal_reddedilir(key_wrap: str) -> None:
    """Biçim katıdır (plan F1b-3: sabit 80 karakter): aynı 60 baytın başka yazımı kabul edilmez."""
    with pytest.raises(ds.SarmalBicimiHatasi):
        ds.anahtari_ac(key_wrap, sarmal_anahtari=_sarmal_anahtari(), stored_name=_AD)


@pytest.mark.parametrize("deger", [None, _ALTIN_KEY_WRAP.encode("ascii"), 80])
def test_metin_olmayan_sarmal_reddedilir(deger: object) -> None:
    with pytest.raises(ds.SarmalBicimiHatasi):
        ds.anahtari_ac(deger, sarmal_anahtari=_sarmal_anahtari(), stored_name=_AD)


@pytest.mark.parametrize("boy", [0, 16, 24, 31, 33])
def test_anahtarlar_tam_32_bayt_olmalidir(boy: int) -> None:
    """AES-256: 16 ya da 24 baytlık anahtar sessizce AES-128/192'ye düşmez. Bu çağıranın hatasıdır
    (`ValueError`), dosyanın bozukluğu değildir (`DosyaSifrelemeHatasi` değil)."""
    kisa = bytes(boy)
    cagrilar: list[Callable[[], object]] = [
        lambda: ds.sifrele(_ACIK, dosya_anahtari=kisa, stored_name=_AD),
        lambda: ds.coz(_altin_kap(), dosya_anahtari=kisa, stored_name=_AD),
        lambda: ds.anahtari_sar(_DOSYA_ANAHTARI, sarmal_anahtari=kisa, stored_name=_AD),
        lambda: ds.anahtari_sar(kisa, sarmal_anahtari=_sarmal_anahtari(), stored_name=_AD),
        lambda: ds.anahtari_ac(_ALTIN_KEY_WRAP, sarmal_anahtari=kisa, stored_name=_AD),
        lambda: ds.dosya_hazirla(_ACIK, sarmal_anahtari=kisa),
    ]
    for cagri in cagrilar:
        with pytest.raises(ValueError) as hata:
            cagri()
        assert not isinstance(hata.value, ds.DosyaSifrelemeHatasi)


# ---------------------------------------------------------------------------
# Üst sınır: çözmeden ve okumadan ÖNCE
# ---------------------------------------------------------------------------
def test_sinir_asan_kap_cozulmeden_reddedilir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Geçerli bir kap bile sınırı aşıyorsa çözülmez: sınır GCM'den önce denetlenir."""
    kap = _altin_kap()
    monkeypatch.setattr(ds, "AZAMI_SIFRELI_BOY", len(kap) - 1)
    with pytest.raises(ds.BoyutSiniriHatasi):
        ds.coz(kap, dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD)
    # Sıra: etiketi bozuk kap da GCM'e varmadan sınırda düşer (sonra olsa `DogrulamaHatasi`).
    bozuk = kap[:-1] + bytes([kap[-1] ^ 1])
    with pytest.raises(ds.BoyutSiniriHatasi):
        ds.coz(bozuk, dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD)
    monkeypatch.setattr(ds, "AZAMI_SIFRELI_BOY", len(kap))
    assert ds.coz(kap, dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD) == _ACIK


def test_sinir_asan_icerik_sifrelenmez(monkeypatch: pytest.MonkeyPatch) -> None:
    """Açık sınır, şifreli sınırdan 36 bayt azdır; sınırdaki içerik tam sınır boyunda kap verir."""
    monkeypatch.setattr(ds, "AZAMI_SIFRELI_BOY", 136)
    monkeypatch.setattr(ds, "AZAMI_ACIK_BOY", 100)
    kap = ds.sifrele(b"%PDF-" + bytes(95), dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD)
    assert len(kap) == 136
    cagrilar: list[Callable[[], object]] = [
        lambda: ds.sifrele(b"%PDF-" + bytes(96), dosya_anahtari=_DOSYA_ANAHTARI, stored_name=_AD),
        lambda: ds.dosya_hazirla(b"%PDF-" + bytes(96), sarmal_anahtari=_sarmal_anahtari()),
    ]
    for cagri in cagrilar:
        with pytest.raises(ds.BoyutSiniriHatasi):
            cagri()


def test_sinir_asan_dosya_diskten_okunmadan_reddedilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gerçek sınırın bir bayt fazlası (seyrek dosya): `fstat` reddeder, tek bayt okunmaz."""
    yol = tmp_path / _AD
    with yol.open("wb") as dosya:
        dosya.truncate(ds.AZAMI_SIFRELI_BOY + 1)

    def okunmamali(tanitici: int, en_cok: int) -> bytes:
        raise AssertionError("sınırı aşan dosya okundu")

    monkeypatch.setattr(ds, "_oku", okunmamali)
    with pytest.raises(ds.BoyutSiniriHatasi):
        ds.kabi_oku(yol)


def test_okurken_buyuyen_dosya_da_siniri_asamaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`fstat` küçük gösterse de en çok sınırın bir baytı fazlası okunur ve reddedilir."""
    monkeypatch.setattr(ds, "AZAMI_SIFRELI_BOY", 64)
    yol = tmp_path / _AD
    yol.write_bytes(bytes(65))
    gercek_fstat = os.fstat

    def kucuk_gosteren(tanitici: int) -> os.stat_result:
        b = gercek_fstat(tanitici)
        return os.stat_result(
            (b.st_mode, b.st_ino, b.st_dev, b.st_nlink, b.st_uid, b.st_gid, 1, 0, 0, 0)
        )

    monkeypatch.setattr(os, "fstat", kucuk_gosteren)
    with pytest.raises(ds.BoyutSiniriHatasi):
        ds.kabi_oku(yol)
    monkeypatch.setattr(os, "fstat", gercek_fstat)
    yol.write_bytes(bytes(64))
    assert ds.kabi_oku(yol) == bytes(64)


@pytest.mark.skipif(os.name != "posix", reason="Windows'ta dizin dosya gibi açılamaz")
def test_duzenli_olmayan_dosya_okunmaz(tmp_path: Path) -> None:
    (tmp_path / _AD).mkdir()
    with pytest.raises(ds.KapBicimiHatasi):
        ds.kabi_oku(tmp_path / _AD)


def test_windows_dizin_izin_hatasi_bicim_hatasidir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows'ta dizin `os.open`'da EACCES verir; ham hata iletide tam yolu taşırdı."""
    (tmp_path / _AD).mkdir()

    def reddet(yol: object, *_: object) -> int:
        raise PermissionError(errno.EACCES, "Permission denied", str(yol))

    monkeypatch.setattr(os, "open", reddet)
    with pytest.raises(ds.KapBicimiHatasi) as hata:
        ds.kabi_oku(tmp_path / _AD)
    assert str(tmp_path) not in str(hata.value)  # tam yol kullanıcı adını taşıyabilir


def test_dosyadaki_izin_hatasi_gizlenmez(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """İzin hatası yalnız dizinde biçim hatasına çevrilir: dosyadaki gerçek hata çağırana gider."""
    (tmp_path / _AD).write_bytes(_altin_kap())

    def reddet(yol: object, *_: object) -> int:
        raise PermissionError(errno.EACCES, "Permission denied", str(yol))

    monkeypatch.setattr(os, "open", reddet)
    with pytest.raises(PermissionError):
        ds.kabi_oku(tmp_path / _AD)


@pytest.mark.skipif(os.name != "posix", reason="sembolik bağ ve O_NOFOLLOW POSIX'e özgüdür")
def test_depodaki_sembolik_bag_izlenmez(tmp_path: Path) -> None:
    """Depoda sembolik bağ bir yol geçişidir: geçerli bir kabı gösterse de okunmaz."""
    gercek = tmp_path / "baska-yer"
    gercek.write_bytes(_altin_kap())
    (tmp_path / _AD).symlink_to(gercek)
    with pytest.raises(ds.KapBicimiHatasi) as hata:
        ds.kabi_oku(tmp_path / _AD)
    assert str(tmp_path) not in str(hata.value)  # tam yol kullanıcı adını taşıyabilir


@pytest.mark.skipif(os.name != "posix", reason="FIFO POSIX'e özgüdür")
def test_fifo_beklemeden_reddedilir(tmp_path: Path) -> None:
    """Yazarı olmayan FIFO'da `open` süresiz beklerdi: sunucu işçisi asılı kalmasın."""
    yol = tmp_path / _AD
    os.mkfifo(yol)
    hatalar: list[Exception] = []

    def oku() -> None:
        try:
            ds.kabi_oku(yol)
        except Exception as hata:  # noqa: BLE001 — sınıfını ana iş parçacığı sınar
            hatalar.append(hata)

    is_parcacigi = threading.Thread(target=oku, daemon=True)
    is_parcacigi.start()
    is_parcacigi.join(timeout=5)
    asili = is_parcacigi.is_alive()
    if asili:  # testin kendisi asılı kalmasın: bekleyen `open`'ı serbest bırak
        os.close(os.open(yol, os.O_RDWR))
        is_parcacigi.join(timeout=5)
    assert not asili
    assert [type(hata) for hata in hatalar] == [ds.KapBicimiHatasi]


@pytest.mark.skipif(os.name != "posix", reason="unix soketi POSIX'e özgüdür")
def test_depodaki_soket_okunmaz(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Soketi açmak `ENXIO`'dur: ham `OSError` tam yolu taşırdı. Adres göreli: soket yolu kısadır."""
    monkeypatch.chdir(tmp_path)
    with socket.socket(socket.AF_UNIX) as soket:
        soket.bind(_AD)
        with pytest.raises(ds.KapBicimiHatasi) as hata:
            ds.kabi_oku(tmp_path / _AD)
    assert str(tmp_path) not in str(hata.value)


# ---------------------------------------------------------------------------
# Depo adı: yol geçişi yok
# ---------------------------------------------------------------------------
_GECERSIZ_ADLAR = [
    "../" + "a" * 29,
    "..",
    "a" * 31,
    "a" * 33,
    "A" * 32,
    _AD.upper(),
    str(uuid.UUID(hex=_AD)),
    _AD + "\n",
    " " + _AD[1:],
    _AD[:-1] + "/",
    _AD[:16] + "\\" + _AD[17:],
    "٠" * 32,  # ARAPÇA-HİNT rakamı sıfır: `\d` kabul ederdi
    "０" * 32,  # tam genişlikli sıfır
    _AD + ".tmp",
    "",
]
_GECERSIZ_ADLAR_KIMLIK = [
    "ust_dizin",
    "iki_nokta",
    "31_hane",
    "33_hane",
    "buyuk_harf",
    "buyuk_harfli_uuid",
    "tireli_uuid",
    "satir_sonu",
    "bosluk",
    "egik_cizgi",
    "ters_egik_cizgi",
    "arapca_rakam",
    "tam_genislik",
    "tmp_eki",
    "bos",
]


@pytest.mark.parametrize("ad", _GECERSIZ_ADLAR, ids=_GECERSIZ_ADLAR_KIMLIK)
def test_desene_uymayan_ad_her_kapida_reddedilir(ad: str, tmp_path: Path) -> None:
    """Yol, AAD ve sarmal desen denetiminden önce kurulmaz; dizin dışına hiçbir şey yazılmaz."""
    dizin = tmp_path / "dosyalar"
    dizin.mkdir()
    cagrilar: list[Callable[[], object]] = [
        lambda: ds.depo_adi_denetle(ad),
        lambda: ds.depo_yolu(dizin, ad),
        lambda: ds.depoya_yaz(dizin, ad, _altin_kap()),
        lambda: ds.depodan_ac(
            dizin, ad, key_wrap=_ALTIN_KEY_WRAP, sarmal_anahtari=_sarmal_anahtari()
        ),
        lambda: ds.sifrele(_ACIK, dosya_anahtari=_DOSYA_ANAHTARI, stored_name=ad),
        lambda: ds.coz(_altin_kap(), dosya_anahtari=_DOSYA_ANAHTARI, stored_name=ad),
        lambda: ds.anahtari_sar(
            _DOSYA_ANAHTARI, sarmal_anahtari=_sarmal_anahtari(), stored_name=ad
        ),
        lambda: ds.anahtari_ac(_ALTIN_KEY_WRAP, sarmal_anahtari=_sarmal_anahtari(), stored_name=ad),
    ]
    for cagri in cagrilar:
        with pytest.raises(ds.GecersizAdHatasi):
            cagri()
    assert sorted(p.name for p in tmp_path.rglob("*")) == ["dosyalar"]


@pytest.mark.parametrize("deger", [_AD.encode("ascii"), uuid.UUID(hex=_AD), None, 42])
def test_metin_olmayan_ad_reddedilir(deger: object) -> None:
    """`uuid.UUID` nesnesi de metne çevrilmez: AAD'ye ve yola giden metin tektir."""
    with pytest.raises(ds.GecersizAdHatasi):
        ds.depo_adi_denetle(deger)


def test_yeni_depo_adi_uuid4_hex_desenindedir() -> None:
    adlar = {ds.yeni_depo_adi() for _ in range(50)}
    assert len(adlar) == 50
    for ad in adlar:
        assert ds.depo_adi_denetle(ad) == ad
        assert uuid.UUID(hex=ad).hex == ad and uuid.UUID(hex=ad).version == 4


def test_gecici_artik_adi_tanir() -> None:
    assert ds.gecici_artik_mi(_AD + ".tmp")
    for ad in (_AD, "x.tmp", _AD + ".tmp.tmp", _AD.upper() + ".tmp", ".tmp", "../" + _AD + ".tmp"):
        assert not ds.gecici_artik_mi(ad), ad


# ---------------------------------------------------------------------------
# Tür: imza baytı
# ---------------------------------------------------------------------------
def test_kabul_edilen_turler_f1b_de_uc_turdur() -> None:
    """Tasarım §5.2.8: PDF, JPEG, PNG. Üretilen evrakın türleri F1c'de bilinçli eklenir."""
    assert [tur.mime for tur in ds.KABUL_EDILEN_TURLER] == [
        "application/pdf",
        "image/jpeg",
        "image/png",
    ]


@pytest.mark.parametrize(
    ("acik", "mime"),
    [
        (b"%PDF-1.4\n%uydurma\n", "application/pdf"),
        (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00", "image/jpeg"),
        (b"\xff\xd8\xff\xdb\x00\x43", "image/jpeg"),
        (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "image/png"),
    ],
    ids=["pdf", "jpeg_jfif", "jpeg_ham", "png"],
)
def test_tur_imza_baytindan_belirlenir(acik: bytes, mime: str) -> None:
    assert ds.tur_belirle(acik) == mime


@pytest.mark.parametrize(
    "acik",
    [
        b"",  # boş dosya
        b"MZ\x90\x00\x03\x00",  # "rapor.pdf" adlı bir program dosyası: uzantıya bakılmaz
        b"<!DOCTYPE html><title>uydurma</title>",  # "rapor.pdf" adlı HTML (F1b'de yok)
        b"PK\x03\x04\x14\x00",  # DOCX/XLSX (ZIP; F1b'de yok)
        b"GIF89a\x01\x00",
        b"%PDF",  # imzanın yarısı
        b"%pdf-1.7",  # küçük harf
        b" %PDF-1.7",  # imza başta değil
        b"\x89PNG",  # PNG imzasının yarısı
        b"\xff\xd8",  # JPEG imzasının yarısı
        b"uydurma metin %PDF-1.7",  # imza ortada
    ],
    ids=[
        "bos",
        "program_dosyasi",
        "html",
        "zip",
        "gif",
        "yarim_pdf",
        "kucuk_harf_pdf",
        "bastaki_bosluk",
        "yarim_png",
        "yarim_jpeg",
        "ortadaki_imza",
    ],
)
def test_kabul_edilmeyen_icerik_tur_hatasi_verir(acik: bytes) -> None:
    with pytest.raises(ds.TurHatasi):
        ds.tur_belirle(acik)
    with pytest.raises(ds.TurHatasi):
        ds.dosya_hazirla(acik, sarmal_anahtari=_sarmal_anahtari())


def test_bos_dosyanin_iletisi_ayridir() -> None:
    with pytest.raises(ds.TurHatasi, match="Boş dosya eklenemez"):
        ds.tur_belirle(b"")
    with pytest.raises(ds.TurHatasi, match="yalnız PDF, JPEG ve PNG"):
        ds.tur_belirle(b"GIF89a")


# ---------------------------------------------------------------------------
# Atomik yazıcı
# ---------------------------------------------------------------------------
def test_atomik_yazim_hedefi_yazar_ve_gecici_dosya_birakmaz(tmp_path: Path) -> None:
    hedef = tmp_path / _AD
    ds.atomik_yaz(hedef, b"uydurma-bayt")
    assert hedef.read_bytes() == b"uydurma-bayt"
    assert sorted(p.name for p in tmp_path.iterdir()) == [_AD]


def test_var_olan_adin_uzerine_yazilmaz(tmp_path: Path) -> None:
    """Depo tek yazımlıdır (tasarım §4.4.7): var olan ad hata verir, eski içerik kalır."""
    hedef = tmp_path / _AD
    hedef.write_bytes(b"eski")
    with pytest.raises(ds.HedefVarHatasi) as hata:
        ds.depoya_yaz(tmp_path, _AD, _altin_kap())
    assert isinstance(hata.value, FileExistsError)
    assert str(tmp_path) not in str(hata.value)
    assert hedef.read_bytes() == b"eski"
    assert sorted(p.name for p in tmp_path.iterdir()) == [_AD]


def test_yazim_sirasinda_beliren_hedefin_uzerine_yazilmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ad, `os.replace`'ten hemen önce yeniden denetlenir: arada beliren dosya ezilmez."""
    hedef = tmp_path / _AD
    gercek_fsync = os.fsync

    def araya_giren(tanitici: int) -> None:
        if stat.S_ISREG(os.fstat(tanitici).st_mode) and not hedef.exists():
            hedef.write_bytes(b"araya-giren")
        gercek_fsync(tanitici)

    monkeypatch.setattr(os, "fsync", araya_giren)
    with pytest.raises(ds.HedefVarHatasi):
        ds.atomik_yaz(hedef, b"yeni")
    assert hedef.read_bytes() == b"araya-giren"
    assert sorted(p.name for p in tmp_path.iterdir()) == [_AD]


@pytest.mark.parametrize("hata", [OSError("uydurma disk hatası"), KeyboardInterrupt()])
def test_yazim_kesilirse_hedef_olusmaz_ve_gecici_dosya_silinir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hata: BaseException
) -> None:
    """Kesinti (disk hatası ya da süreç durdurma) yarım bir hedef bırakmaz."""

    def kesen(tanitici: int) -> None:
        raise hata

    monkeypatch.setattr(os, "fsync", kesen)
    with pytest.raises(type(hata)):
        ds.atomik_yaz(tmp_path / _AD, b"uydurma-bayt")
    assert list(tmp_path.iterdir()) == []


def test_kesintiden_kalan_gecici_dosyaya_dokunulmaz(tmp_path: Path) -> None:
    """Önceki kesintinin `<ad>.tmp`'si `O_EXCL` ile açılamaz: yazım reddedilir, artık aynen kalır,
    hedef oluşmaz; artığı `gecici_artik_mi` tanır (silmek açılıştaki artık temizliğinin işidir)."""
    artik = tmp_path / (_AD + ".tmp")
    artik.write_bytes(b"yarim")
    with pytest.raises(ds.GeciciDosyaVarHatasi):
        ds.depoya_yaz(tmp_path, _AD, _altin_kap())
    assert artik.read_bytes() == b"yarim"
    assert sorted(p.name for p in tmp_path.iterdir()) == [_AD + ".tmp"]
    assert ds.gecici_artik_mi(artik.name)


@pytest.mark.skipif(os.name != "posix", reason="POSIX kipi")
@pytest.mark.parametrize("umask", [0o022, 0o000, 0o277], ids=["022", "000", "277"])
def test_depo_dosyasi_umask_ne_olursa_olsun_0600_yazilir(tmp_path: Path, umask: int) -> None:
    """Tasarım §4.5: dosya deposu 0600; yazıcı umask'a güvenmez (plan F1b-3 "Dosya deposu")."""
    onceki = os.umask(umask)
    try:
        yol = ds.depoya_yaz(tmp_path, _AD, _altin_kap())
    finally:
        os.umask(onceki)
    assert stat.S_IMODE(yol.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "posix", reason="dizin fsync'i POSIX'e özgüdür")
def test_once_dosya_sonra_dizin_fsync_edilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gercek_fsync = os.fsync
    gorulen: list[str] = []

    def kaydeden(tanitici: int) -> None:
        gorulen.append("dizin" if stat.S_ISDIR(os.fstat(tanitici).st_mode) else "dosya")
        gercek_fsync(tanitici)

    monkeypatch.setattr(os, "fsync", kaydeden)
    ds.atomik_yaz(tmp_path / _AD, b"uydurma-bayt")
    assert gorulen == ["dosya", "dizin"]


# ---------------------------------------------------------------------------
# Saf katman
# ---------------------------------------------------------------------------
def test_modul_yalniz_standart_kitaplik_ve_cryptography_kullanir() -> None:
    """Plan F1b-3 "Dosya deposu": modül modelleri, Django'yu ve `shared.crypto`'yu tanımaz."""
    agac = ast.parse(Path(ds.__file__).read_text(encoding="utf-8"))
    kokler: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Import):
            kokler.update(ad.name.split(".")[0] for ad in dugum.names)
        elif isinstance(dugum, ast.ImportFrom):
            assert dugum.level == 0 and dugum.module is not None
            kokler.add(dugum.module.split(".")[0])
    yabanci = {kok for kok in kokler if kok not in sys.stdlib_module_names} - {"cryptography"}
    assert yabanci == set()
    assert "cryptography" in kokler
