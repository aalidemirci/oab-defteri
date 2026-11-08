"""Dosya deposunun kabı ve şifrelemesi — saf katman (tasarım TK22, §4.4.4 "Dosya anahtarı", §4.4.7).

Ekler ve üretilmiş evrak veri dizinindeki `dosyalar/<stored_name>`'de dosya başına rastgele
anahtarla AES-256-GCM şifreli durur (TK22; tasarım §2.3.2). Bu modül yalnız ilkelleri verir:
kap, dosya anahtarının sarmalı, depo adı, tür denetimi, diskten sınırlı okuma ve atomik bayt
yazımı. Modelleri, Django'yu, veritabanını ve bellekteki veri anahtarını (DEK) TANIMAZ; yalnız
standart kitaplık ve `cryptography` kullanır (plan F1b-3 "Dosya deposu").
`Attachment` satırı, yazım sırası (önce dosya, sonra tek işlemde satır ve iz satırı) ve yükleme
sınırı depo servisinindir.

KAP (`ODDOSYA\\x01`; tasarım §2.3.1): MAGIC (8 bayt) ‖ nonce (12 bayt) ‖ AES-256-GCM şifreli
metin ‖ etiket (16 bayt). AAD, `stored_name`'in ASCII baytlarıdır: kap başka bir adla (başka bir
satırın dosyası yerine) konursa açılmaz. Şifreli boy = açık boy + 36 (`sifreli_boy`). Biçim tek
parçadır (plan F1b-3 "Dosya deposu"): GCM etiketi sonda doğrular, doğrulanmamış açık metin dışarı
verilmez, açma bellekte yapılır. Biçim üst sınırı 64 MiB şifrelidir ve çözmeden ÖNCE, diskten
okurken okumadan önce denetlenir: program dışından büyütülmüş bir dosya belleği tüketemez.
Yükleme sınırı ayardaki değerle bu sınırın küçüğüdür (`AZAMI_ACIK_BOY`; depo servisi). Bu sürüm
başka bir sürüm baytını açmaz.

DOSYA ANAHTARI VE SARMAL (tasarım §4.4.4 "Dosya anahtarı"): her dosyanın anahtarı rastgele 32
bayttır, DEK'ten TÜREMEZ; DEK yenilemesi (TK12, F4) dosyaları yeniden yazmaz, yalnız sarmalları
yeniler. Dosya anahtarı `HKDF(DEK, "od-dosya-sarmal/v1")` ile türeyen sarmal anahtarıyla
AES-GCM sarılır (AAD = `stored_name`) ve `Attachment.key_wrap`'te durur. Sarmal anahtarını
`shared.crypto.file_wrap_key` `derive_subkey` kapısından türetir; bilgi dizgesi §2.3.1 kimlik
tablosundadır ve öteki dizgelerle çakışmadığı testle sabittir. Bu modül DEK'i görmez, yalnız
amaca özel anahtarı alır. `key_wrap` = base64(nonce 12 ‖ şifreli
anahtar 32 ‖ etiket 16): sabit 80 karakterlik ASCII metin (plan F1b-3 "Dosya deposu"; kanonik
kodlayıcı bayt dizisini reddettiği için metin). Kap ve sarmal biçimi altın vektör testiyle
donmuştur.

DEPO ADI (`stored_name`; tasarım §2.3.2, §5.2.8): `uuid4().hex`, yani 32 küçük onaltılık hane,
uzantısız (`generate_uuid_filename` UYARLA, tasarım §12.A: uuid adı AYNEN, uzantı kalkar). Her
yol birleştirmesinden ve AAD'den önce `^[0-9a-f]{32}$` denetlenir (`fullmatch`; `$` sondaki satır
sonunu da kabul ederdi): program dışından değiştirilmiş bir veritabanındaki `../guvenlik.json`
gibi bir ad yol geçişi yapamaz; tireli, büyük harfli, başka uzunlukta ya da ASCII dışı rakamlı
yazım reddedilir. ORM ile ham SQL aynı metni görür, çeviri gerekmez (UUIDField SQLite'ta tiresiz,
Python'da tireli metin verir; plan F1b-2'nin konsol geri yüklemesi maddesi).

TÜR (tasarım §5.2.8): imza baytından, libmagic'siz (tasarım §12.A: python-magic ve yalnız-PDF kuralı
kalkar). F1b'de kabul edilen türler PDF, JPEG ve PNG'dir. Uzantıya bakılmaz; bu modül dosyanın
adını hiç görmez. Üretilen evrakın türleri (DOCX, XLSX, HTML) F1c'de `GeneratedDocument`'la
eklenir (plan F1b-3 "Dosya deposu"); tür tablosu (`DosyaTuru`) buna açıktır, kabul kümesi
(`KABUL_EDILEN_TURLER`) F1b'de üç türdür.

ÖZET VE BOY (plan F1b-3 "Kap ve manifesto"): `sha256` ve `size` AÇIK içeriğin özeti ve boyudur
(`compute_sha256` AYNEN, tasarım §12.A); manifesto onları satırın açık sütunlarından anahtarsız alır.

ATOMİK YAZIM (plan F1b-3 "Dosya deposu"; tasarım §4.5 "Dosya izinleri"): hedef dizinde
`<ad>.tmp` `O_EXCL` ve 0600 ile açılır, yazılır, `fsync` edilir, `os.replace` ile asıl adına
konur; POSIX'te dizin de `fsync` edilir. Var olan bir adın üzerine YAZILMAZ (depo tek yazımlıdır,
§4.4.7): ad hem başta hem yerine koymadan hemen önce denetlenir. Kalan pencere bu iki denetim
arasıdır; adlar rastgele (`uuid4`) üretildiği için oraya ancak bir program hatası düşer. Önceki bir
kesintiden kalmış `.tmp`'ye dokunulmaz, yazım reddedilir; artığı `gecici_artik_mi` tanır, silmek
açılıştaki artık temizliğinin işidir. Kip açıkça çekilir (`fchmod`): yazıcı umask'a güvenmez.
Windows'ta dosya kullanıcı profilindedir, kip anlamsızdır.

DEPO DİZİNLERİ VE TAŞIMA (plan F1b-3 "Geri yükleme"; tasarım §4.4.7 "Yetim ve eksik dosya"): yetim
dosya `dosyalar/yetim/<yyyy-aa-gg>/<stored_name>`'dedir. Burada yalnız saf parçalar durur: dizinin
kurulması, tarih dizini, yetime taşıma, yetimdeki kopyaların bulunması ve geri yüklemenin hazırlık
dizini (`dosyalar/.hazirlik-<hex>/`). Hazırlık dizini depoyla aynı birimdedir: doğrulanmış kap
depoya tek `os.replace`'le geçer. Yetim taramasının saf parçaları da buradadır: dokunulabilecek
adlar (`depodaki_dosyalar`), taşıma (`yetime_tasi`), tarih dizini (`yetim_gun_dizini`). Hangi
dosyanın nereye gideceğini bu modül bilmez: veritabanını okuyan kararlar geri yükleme servisinin ve
açılış kancasınındır (`apps.okul.masaustu_kanca`). Taşıyıcılar var olan adın üzerine yazmaz (depo
tek yazımlıdır, §4.4.7).
"""

from __future__ import annotations

import base64
import binascii
import errno
import hashlib
import os
import re
import secrets
import stat
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Final

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

#: Dosya kabının sihirli baytları (tasarım §2.3.1): sürüm son bayttadır.
MAGIC: Final = b"ODDOSYA\x01"
#: AES-GCM nonce boyu (bayt); kapta ve sarmalda aynıdır.
NONCE_BAYT: Final = 12
#: AES-GCM etiket boyu (bayt).
ETIKET_BAYT: Final = 16
#: Dosya anahtarı ve sarmal anahtarı boyu (bayt; AES-256).
ANAHTAR_BAYT: Final = 32
#: Kabın açık içeriğe eklediği bayt: MAGIC + nonce + etiket (şifreli boy = açık boy + 36).
KAP_EK_BAYT: Final = len(MAGIC) + NONCE_BAYT + ETIKET_BAYT
#: Biçim üst sınırı (şifreli boy, bayt): 64 MiB. Çözmeden önce denetlenir (modül başlığı).
AZAMI_SIFRELI_BOY: Final = 64 * 1024 * 1024
#: Kaba girebilecek en büyük açık içerik (bayt); yükleme sınırı bununla ayarın küçüğüdür.
AZAMI_ACIK_BOY: Final = AZAMI_SIFRELI_BOY - KAP_EK_BAYT
#: `key_wrap` metninin boyu: base64(12 + 32 + 16 = 60 bayt) = 80 karakter, dolgusuz.
KEY_WRAP_UZUNLUK: Final = 80
#: Depo adının deseni (`uuid4().hex`); `fullmatch` ile uygulanır.
DEPO_ADI_DESENI: Final = re.compile(r"[0-9a-f]{32}")
#: Atomik yazımın geçici dosya eki (`<ad>.tmp`).
GECICI_EK: Final = ".tmp"
#: Depo dosyalarının POSIX kipi (tasarım §4.5).
DOSYA_KIPI: Final = 0o600
#: Depo dizinlerinin POSIX kipi (tasarım §4.5).
DIZIN_KIPI: Final = 0o700
#: `dosyalar/` altındaki yetim dizininin adı (modül başlığı "DEPO DİZİNLERİ VE TAŞIMA").
YETIM_DIZINI: Final = "yetim"
#: Geri yüklemenin hazırlık dizininin öneki; artığı açılış temizliği toplar.
HAZIRLIK_ONEKI: Final = ".hazirlik-"
#: Yetim dizinindeki gün dizinlerinin deseni (`fullmatch`).
_YETIM_GUNU_DESENI: Final = re.compile(r"\d{4}-\d{2}-\d{2}")
#: Aynı gün aynı adla yetime düşen kopyanın sıra eki (`<ad>-<n>`; `yetime_tasi`).
_SIRA_EKI_DESENI: Final = re.compile(r"-([1-9][0-9]*)")

_EN_KISA_KAP: Final = KAP_EK_BAYT
_OKUMA_PARCASI: Final = 1024 * 1024
# `O_CREAT | O_EXCL` var olan adı (sembolik bağ dâhil) açmaz; Windows'ta da geçerlidir.
_YAZMA_BAYRAKLARI: Final = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
# Okumada sembolik bağ izlenmez (POSIX): depoda yalnız bu modülün yazdığı düzenli dosyalar durur.
# `O_NONBLOCK` düzenli dosyada etkisizdir; FIFO'da `open` yazarı süresiz beklerdi, denetime
# gelinmezdi.
_OKUMA_BAYRAKLARI: Final = (
    os.O_RDONLY
    | getattr(os, "O_BINARY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_NONBLOCK", 0)
)
# Düzenli olmayan dosyayı açmanın `OSError`'ları: sembolik bağ (`O_NOFOLLOW`) ve soket.
_DUZENSIZ_DOSYA_HATALARI: Final = (errno.ELOOP, errno.ENXIO)
_DUZENSIZ_DOSYA_ILETISI: Final = (
    "Ek dosyası tanınmıyor: program dışından değiştirilmiş olabilir; açılmadı."
)
_BUYUK_KAP_ILETISI: Final = (
    "Ek dosyası izin verilen boydan büyük; açılmadı (program dışından değiştirilmiş olabilir)."
)
_BUYUK_DOSYA_ILETISI: Final = (
    f"Dosya çok büyük; en çok {AZAMI_SIFRELI_BOY // (1024 * 1024)} MB olabilir."
)


# ---------------------------------------------------------------------------
# İstisnalar
# ---------------------------------------------------------------------------
class DosyaSifrelemeHatasi(ValueError):
    """Dosya deposunun biçim, ad, tür, boyut ve doğrulama hatalarının tabanı (Türkçe ileti)."""


class GecersizAdHatasi(DosyaSifrelemeHatasi):
    """Depo adı `uuid4().hex` desenine uymuyor; yol kurulmaz, dosyaya dokunulmaz."""

    def __init__(self) -> None:
        super().__init__("Ek dosyasının depo adı geçersiz; dosyaya dokunulmadı.")


class KapBicimiHatasi(DosyaSifrelemeHatasi):
    """Dosya bu programın dosya kabı değil (sihirli baytlar ya da sürüm tutmuyor)."""


class KesikKapHatasi(KapBicimiHatasi):
    """Dosya, en kısa kaptan (MAGIC + nonce + etiket) kısa: yarım kalmış ya da kesilmiş."""

    def __init__(self) -> None:
        super().__init__("Ek dosyası eksik (yarım kalmış ya da kesilmiş); açılmadı.")


class BoyutSiniriHatasi(DosyaSifrelemeHatasi):
    """Biçim üst sınırı aşıldı; şifreleme yapılmaz, çözme ve okuma başlamaz."""


class DogrulamaHatasi(DosyaSifrelemeHatasi):
    """AES-GCM etiketi tutmadı.

    Yanlış anahtar, başka bir depo adı (AAD), çevrilmiş bit ve gövdeden kesilmiş kap aynı
    sonucu verir: GCM bunları birbirinden ayırmaz ve ayırmamalıdır (ayrım bilgi sızdırırdı).
    """


class SarmalBicimiHatasi(DosyaSifrelemeHatasi):
    """`key_wrap` metni 80 karakterlik katı base64 (60 bayt) değil."""

    def __init__(self) -> None:
        super().__init__("Ek dosyasının anahtar kaydı bozuk; dosya açılamadı.")


class TurHatasi(DosyaSifrelemeHatasi):
    """Dosyanın imza baytı kabul edilen türlerden birine uymuyor ya da dosya boş."""


class HedefVarHatasi(FileExistsError):
    """Hedef adda zaten bir dosya var; depo tek yazımlıdır, üzerine yazılmaz."""

    def __init__(self, ad: str) -> None:
        # İletide yalnız dosyanın adı geçer: tam yol kullanıcı adını taşıyabilir.
        super().__init__(f"'{ad}' adında bir dosya zaten var; üzerine yazılmadı.")


class GeciciDosyaVarHatasi(FileExistsError):
    """Önceki bir kesintiden kalmış `<ad>.tmp` duruyor; ona dokunulmaz, yazım yapılmaz."""

    def __init__(self, ad: str) -> None:
        super().__init__(
            f"'{ad}' için yarım kalmış bir yazımın geçici dosyası duruyor; yazım yapılmadı."
        )


# ---------------------------------------------------------------------------
# Depo adı ve yol (yol geçişi yok)
# ---------------------------------------------------------------------------
def yeni_depo_adi() -> str:
    """Yeni `stored_name`: `uuid4().hex` (32 küçük onaltılık hane; modül başlığı "DEPO ADI")."""
    return uuid.uuid4().hex


def depo_adi_denetle(ad: object) -> str:
    """Adı `^[0-9a-f]{32}$` desenine karşı denetler ve aynen döndürür; uymazsa `GecersizAdHatasi`.

    Metin dışındaki her tür (bayt, `uuid.UUID`, sayı) de reddedilir: AAD'ye ve yola giden metin
    tektir, çevrilmez.
    """
    if not isinstance(ad, str) or DEPO_ADI_DESENI.fullmatch(ad) is None:
        raise GecersizAdHatasi()
    return ad


def depo_yolu(dizin: Path, ad: object) -> Path:
    """`dizin/<ad>`; ad önce desen denetiminden geçer (her yol birleştirmesinin tek kapısı)."""
    return dizin / depo_adi_denetle(ad)


def gecici_artik_mi(dosya_adi: str) -> bool:
    """Ad, bu modülün atomik yazımının geçici dosyası mı (`<32 hane>.tmp`)? Açılış temizliği içindir."""
    return (
        dosya_adi.endswith(GECICI_EK)
        and DEPO_ADI_DESENI.fullmatch(dosya_adi[: -len(GECICI_EK)]) is not None
    )


def hazirlik_artigi_mi(dizin_adi: str) -> bool:
    """Ad, geri yüklemenin hazırlık dizini mi (`.hazirlik-<32 hane>`)? Açılış temizliği içindir."""
    return (
        dizin_adi.startswith(HAZIRLIK_ONEKI)
        and DEPO_ADI_DESENI.fullmatch(dizin_adi[len(HAZIRLIK_ONEKI) :]) is not None
    )


def _aad(ad: object) -> bytes:
    return depo_adi_denetle(ad).encode("ascii")


# ---------------------------------------------------------------------------
# Kap: ODDOSYA\x01 ‖ nonce ‖ şifreli metin ‖ etiket
# ---------------------------------------------------------------------------
def yeni_dosya_anahtari() -> bytes:
    """Dosya başına rastgele 32 baytlık anahtar (DEK'ten türemez; modül başlığı)."""
    return secrets.token_bytes(ANAHTAR_BAYT)


def _anahtar_denetle(anahtar: object, ne: str) -> bytes:
    """Anahtar 32 baytlık `bytes` olmalı (AES-256). Çağıranın hatasıdır, veri hatası değildir."""
    if not isinstance(anahtar, bytes) or len(anahtar) != ANAHTAR_BAYT:
        raise ValueError(f"{ne} {ANAHTAR_BAYT} baytlık bayt dizisi olmalıdır.")
    return anahtar


def sifreli_boy(acik_boy: int) -> int:
    """Açık içerik boyundan kabın boyu (açık boy + 36); dosya bölümünün uzunluk denetimi içindir."""
    return acik_boy + KAP_EK_BAYT


def acik_ozet(acik: bytes) -> str:
    """Açık içeriğin SHA-256 özeti (64 küçük onaltılık hane; tasarım §12.A AYNEN)."""
    return hashlib.sha256(acik).hexdigest()


def sifrele(acik: bytes, *, dosya_anahtari: bytes, stored_name: str) -> bytes:
    """Açık içerikten kap kurar (rastgele nonce, AAD = depo adı); sınırı aşan içerik reddedilir."""
    return _kap_kur(acik, dosya_anahtari, stored_name, secrets.token_bytes(NONCE_BAYT))


def _kap_kur(acik: bytes, dosya_anahtari: bytes, stored_name: str, nonce: bytes) -> bytes:
    """Kabın kendisi; nonce yalnız altın vektör testinde dışarıdan verilir."""
    aad = _aad(stored_name)
    anahtar = _anahtar_denetle(dosya_anahtari, "Dosya anahtarı")
    if len(acik) > AZAMI_ACIK_BOY:
        raise BoyutSiniriHatasi(_BUYUK_DOSYA_ILETISI)
    return MAGIC + nonce + AESGCM(anahtar).encrypt(nonce, acik, aad)


def coz(kap: bytes, *, dosya_anahtari: bytes, stored_name: str) -> bytes:
    """Kabı bellekte çözer; sırayla boy sınırı, sihirli baytlar, en kısa boy ve GCM etiketi.

    Boy sınırı her şeyden ÖNCE denetlenir (modül başlığı). Biçim hataları `KapBicimiHatasi` ve
    `KesikKapHatasi`, etiketin tutmaması `DogrulamaHatasi`'dır.
    """
    aad = _aad(stored_name)
    anahtar = _anahtar_denetle(dosya_anahtari, "Dosya anahtarı")
    if len(kap) > AZAMI_SIFRELI_BOY:
        raise BoyutSiniriHatasi(_BUYUK_KAP_ILETISI)
    bas = kap[: len(MAGIC)]
    if bas != MAGIC:
        if len(kap) < len(MAGIC) and MAGIC.startswith(bas):
            raise KesikKapHatasi()
        raise KapBicimiHatasi(
            "Ek dosyası tanınmıyor: bu programın dosya biçimi değil ya da başka bir sürümle "
            "yazılmış; açılmadı."
        )
    if len(kap) < _EN_KISA_KAP:
        raise KesikKapHatasi()
    nonce = kap[len(MAGIC) : len(MAGIC) + NONCE_BAYT]
    try:
        return AESGCM(anahtar).decrypt(nonce, kap[len(MAGIC) + NONCE_BAYT :], aad)
    except InvalidTag:
        raise DogrulamaHatasi(
            "Ek dosyası doğrulanamadı: bozulmuş, program dışından değiştirilmiş ya da başka bir "
            "kayda ait; açılmadı."
        ) from None


# ---------------------------------------------------------------------------
# Dosya anahtarının sarmalı (key_wrap)
# ---------------------------------------------------------------------------
def anahtari_sar(dosya_anahtari: bytes, *, sarmal_anahtari: bytes, stored_name: str) -> str:
    """Dosya anahtarını sarar: base64(nonce ‖ şifreli anahtar ‖ etiket), 80 karakter (AAD = ad).

    `sarmal_anahtari` `shared.crypto.file_wrap_key(DEK)`'tir; DEK'in kendisi verilmez.
    """
    return _sar(dosya_anahtari, sarmal_anahtari, stored_name, secrets.token_bytes(NONCE_BAYT))


def _sar(dosya_anahtari: bytes, sarmal_anahtari: bytes, stored_name: str, nonce: bytes) -> str:
    """Sarmalın kendisi; nonce yalnız altın vektör testinde dışarıdan verilir."""
    aad = _aad(stored_name)
    anahtar = _anahtar_denetle(dosya_anahtari, "Dosya anahtarı")
    saran = _anahtar_denetle(sarmal_anahtari, "Sarmal anahtarı")
    ham = nonce + AESGCM(saran).encrypt(nonce, anahtar, aad)
    return base64.b64encode(ham).decode("ascii")


def anahtari_ac(key_wrap: object, *, sarmal_anahtari: bytes, stored_name: str) -> bytes:
    """Sarmalı açar; biçimi tutmazsa `SarmalBicimiHatasi`, etiketi tutmazsa `DogrulamaHatasi`.

    Biçim katıdır: tam 80 karakter, yalnız standart base64 alfabesi (satır sonu, boşluk ve
    URL-güvenli `-`/`_` yok), çözülünce 60 bayt.
    """
    aad = _aad(stored_name)
    saran = _anahtar_denetle(sarmal_anahtari, "Sarmal anahtarı")
    if not isinstance(key_wrap, str) or len(key_wrap) != KEY_WRAP_UZUNLUK:
        raise SarmalBicimiHatasi()
    try:
        ham = base64.b64decode(key_wrap.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error):
        raise SarmalBicimiHatasi() from None
    if len(ham) != NONCE_BAYT + ANAHTAR_BAYT + ETIKET_BAYT:
        raise SarmalBicimiHatasi()
    try:
        return AESGCM(saran).decrypt(ham[:NONCE_BAYT], ham[NONCE_BAYT:], aad)
    except InvalidTag:
        raise DogrulamaHatasi(
            "Ek dosyasının anahtarı doğrulanamadı: anahtar kaydı bozulmuş, başka bir eke ait ya da "
            "veri anahtarı farklı; dosya açılamadı."
        ) from None


# ---------------------------------------------------------------------------
# Tür: imza baytı (libmagic yok)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DosyaTuru:
    """Bir dosya türü: MIME adı ve dosyanın başında aranan imza baytları (biri tutmalı)."""

    mime: str
    imzalar: tuple[bytes, ...]

    def tutar(self, acik: bytes) -> bool:
        return any(acik.startswith(imza) for imza in self.imzalar)


PDF: Final = DosyaTuru("application/pdf", (b"%PDF-",))
JPEG: Final = DosyaTuru("image/jpeg", (b"\xff\xd8\xff",))
PNG: Final = DosyaTuru("image/png", (b"\x89PNG\r\n\x1a\n",))
#: F1b'de kabul edilen türler (tasarım §5.2.8). Üretilen evrakın türleri F1c'de eklenir.
KABUL_EDILEN_TURLER: Final[tuple[DosyaTuru, ...]] = (PDF, JPEG, PNG)


def tur_belirle(acik: bytes) -> str:
    """İçeriğin MIME türü, imza baytından; boşsa ya da kabul edilen türlerden değilse `TurHatasi`."""
    if len(acik) == 0:
        raise TurHatasi("Boş dosya eklenemez.")
    for tur in KABUL_EDILEN_TURLER:
        if tur.tutar(acik):
            return tur.mime
    raise TurHatasi("Bu dosya türü eklenemez; yalnız PDF, JPEG ve PNG dosyaları kabul edilir.")


# ---------------------------------------------------------------------------
# Hazırlama: açık içerikten depoya yazılacak kap ve satırın açık sütunları
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HazirDosya:
    """Depoya yazılmaya hazır dosya ve `Attachment` satırının bu katmandan gelen sütunları.

    `sha256` ve `size` açık içeriğindir (modül başlığı "ÖZET VE BOY"). Dosya anahtarı yalnız
    sarmalıyla taşınır; kap `repr`'e girmez.
    """

    stored_name: str
    kap: bytes = field(repr=False)
    key_wrap: str
    sha256: str
    size: int
    mime: str


def dosya_hazirla(acik: bytes, *, sarmal_anahtari: bytes) -> HazirDosya:
    """Türü imzadan belirler, yeni ad ve anahtarla şifreler, anahtarı sarar; diske yazmaz.

    Reddedilen dosya için hiçbir şey üretilmez (tasarım §12.A `validate_upload` ilkesi:
    reddedilen dosya diske yazılmaz).
    """
    _anahtar_denetle(sarmal_anahtari, "Sarmal anahtarı")
    mime = tur_belirle(acik)
    ad = yeni_depo_adi()
    anahtar = yeni_dosya_anahtari()
    return HazirDosya(
        stored_name=ad,
        kap=sifrele(acik, dosya_anahtari=anahtar, stored_name=ad),
        key_wrap=anahtari_sar(anahtar, sarmal_anahtari=sarmal_anahtari, stored_name=ad),
        sha256=acik_ozet(acik),
        size=len(acik),
        mime=mime,
    )


# ---------------------------------------------------------------------------
# Disk: sınırlı okuma ve atomik yazım
# ---------------------------------------------------------------------------
def kabi_oku(yol: Path) -> bytes:
    """Kabı diskten okur; boy üst sınırı OKUMADAN önce `fstat` ile denetlenir.

    Yalnız düzenli dosya okunur: FIFO, soket ve dizin `KapBicimiHatasi`'dır, beklemeden döner ve
    iletisi yolu taşımaz. Sembolik bağ POSIX'te aynı hatayı verir; Windows'ta `O_NOFOLLOW` yoktur,
    izlenir. Windows'ta dizin `os.open`'da izin hatası verir, o da aynı hataya çevrilir. Dosya yoksa
    `FileNotFoundError` çağırana gider. Okuma sırasında büyüyen dosya da sınırı aşamaz: en çok
    sınırın bir baytı fazlası okunur ve reddedilir.
    """
    try:
        tanitici = os.open(yol, _OKUMA_BAYRAKLARI)
    except OSError as hata:
        if hata.errno in _DUZENSIZ_DOSYA_HATALARI or (
            isinstance(hata, PermissionError) and os.path.isdir(yol)
        ):
            raise KapBicimiHatasi(_DUZENSIZ_DOSYA_ILETISI) from None
        raise
    try:
        bilgi = os.fstat(tanitici)
        if not stat.S_ISREG(bilgi.st_mode):
            raise KapBicimiHatasi(_DUZENSIZ_DOSYA_ILETISI)
        if bilgi.st_size > AZAMI_SIFRELI_BOY:
            raise BoyutSiniriHatasi(_BUYUK_KAP_ILETISI)
        kap = _oku(tanitici, AZAMI_SIFRELI_BOY + 1)
    finally:
        os.close(tanitici)
    if len(kap) > AZAMI_SIFRELI_BOY:
        raise BoyutSiniriHatasi(_BUYUK_KAP_ILETISI)
    return kap


def _oku(tanitici: int, en_cok: int) -> bytes:
    parcalar: list[bytes] = []
    kalan = en_cok
    while kalan > 0:
        parca = os.read(tanitici, min(kalan, _OKUMA_PARCASI))
        if not parca:
            break
        parcalar.append(parca)
        kalan -= len(parca)
    return b"".join(parcalar)


def _tamamini_yaz(tanitici: int, veri: bytes) -> None:
    gorunum = memoryview(veri)
    while gorunum:
        yazilan = os.write(tanitici, gorunum)
        gorunum = gorunum[yazilan:]


def dizini_esitle(dizin: Path) -> None:
    """POSIX'te dizin girdisini diske indirir (yeniden adlandırma kesintiye dayansın)."""
    if os.name != "posix":
        return
    tanitici = os.open(dizin, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(tanitici)
    finally:
        os.close(tanitici)


def dosyayi_esitle(yol: Path) -> None:
    """Dosyanın baytlarını diske indirir: `fsync` yazan tanıtıcıdan bağımsızdır.

    Tanıtıcı yazılabilir açılır: Windows'ta salt okunur tanıtıcı `fsync` edilemez.
    """
    with yol.open("r+b") as dosya:
        os.fsync(dosya.fileno())


def atomik_yaz(hedef: Path, veri: bytes) -> None:
    """`veri`'yi `hedef`'e 0600 ile atomik yazar; var olan adın üzerine yazmaz (modül başlığı).

    Sıra: hedef varsa `HedefVarHatasi` → `<ad>.tmp` `O_EXCL` ile açılır (duruyorsa
    `GeciciDosyaVarHatasi`, artığa dokunulmaz) → POSIX'te kip `fchmod` ile 0600'e çekilir →
    yazılır, `fsync` → hedef yeniden denetlenir → `os.replace` → POSIX'te dizin `fsync`'i. Yerine
    koymadan önceki hata hâlinde yalnız bu çağrının açtığı geçici dosya silinir, hedefe dokunulmaz.
    Yerine koyduktan sonra dizin eşitlemesi düşerse dosya yerinde kalır ve hata çağırana gider
    (satırı yazılmayan dosya yetimdir; açılış taraması toplar).
    """
    if os.path.lexists(hedef):
        raise HedefVarHatasi(hedef.name)
    gecici = hedef.with_name(hedef.name + GECICI_EK)
    try:
        tanitici = os.open(gecici, _YAZMA_BAYRAKLARI, DOSYA_KIPI)
    except FileExistsError:
        raise GeciciDosyaVarHatasi(hedef.name) from None
    try:
        try:
            if os.name == "posix":
                os.fchmod(tanitici, DOSYA_KIPI)
            _tamamini_yaz(tanitici, veri)
            os.fsync(tanitici)
        finally:
            os.close(tanitici)
        if os.path.lexists(hedef):
            raise HedefVarHatasi(hedef.name)
        os.replace(gecici, hedef)
    except BaseException:
        gecici.unlink(missing_ok=True)
        raise
    dizini_esitle(hedef.parent)


def akisla_yaz(hedef: Path, parcalar: Iterable[bytes]) -> None:
    """Parçaları yeni bir dosyaya 0600 ile yazar, `fsync` eder; var olan adı açmaz.

    Geri yüklemenin hazırlık dizini içindir: kap bellekte toplanmaz (§4.4.7). Yazım hazırlık
    dizininde olduğu için atomik değildir; yarıda kalan dosya dizinle birlikte silinir.
    """
    tanitici = os.open(hedef, _YAZMA_BAYRAKLARI, DOSYA_KIPI)
    try:
        if os.name == "posix":
            os.fchmod(tanitici, DOSYA_KIPI)
        for parca in parcalar:
            _tamamini_yaz(tanitici, parca)
        os.fsync(tanitici)
    finally:
        os.close(tanitici)


def dizin_kur(dizin: Path) -> Path:
    """Dizini yoksa kurar, POSIX'te 0700'e çeker (yazıcılar umask'a güvenmez; §4.5)."""
    dizin.mkdir(mode=DIZIN_KIPI, parents=True, exist_ok=True)
    if os.name == "posix":
        dizin.chmod(DIZIN_KIPI)
    return dizin


def hazirlik_dizini_kur(depo: Path) -> Path:
    """Depo altında yeni bir hazırlık dizini kurar (modül başlığı "DEPO DİZİNLERİ VE TAŞIMA")."""
    dizin_kur(depo)
    hazirlik = depo / f"{HAZIRLIK_ONEKI}{uuid.uuid4().hex}"
    hazirlik.mkdir(mode=DIZIN_KIPI)
    if os.name == "posix":
        hazirlik.chmod(DIZIN_KIPI)
    return hazirlik


def yerine_tasi(kaynak: Path, hedef: Path) -> None:
    """Dosyayı `hedef`'e taşır; hedefte bir şey varsa `HedefVarHatasi` (üzerine yazılmaz)."""
    if os.path.lexists(hedef):
        raise HedefVarHatasi(hedef.name)
    os.replace(kaynak, hedef)
    dizini_esitle(hedef.parent)


def depodaki_dosyalar(depo: Path) -> list[str]:
    """`dosyalar/` altında adı desene uyan düzenli dosyalar, sıralı; dizin yoksa boş liste.

    Yetim taraması yalnız bunlara dokunur (plan F1b-3 "Geri yükleme"). Dizin, sembolik bağ ve desene
    uymayan ad listeye girmez. Dizin okunamazsa `OSError` çağırana gider: okunamayan depo boş değildir.
    """
    try:
        with os.scandir(depo) as girdiler:
            return sorted(
                girdi.name
                for girdi in girdiler
                if DEPO_ADI_DESENI.fullmatch(girdi.name) is not None
                and girdi.is_file(follow_symlinks=False)
            )
    except FileNotFoundError:
        return []


def yetim_gun_dizini(depo: Path, gun: date) -> Path:
    """`dosyalar/yetim/<yyyy-aa-gg>` yolu; dizini kurmaz."""
    return depo / YETIM_DIZINI / gun.isoformat()


def yetime_tasi(depo: Path, ad: str, gun: date) -> Path:
    """`dosyalar/<ad>`'ı o günün yetim dizinine taşır; dosyanın yeni yolunu döndürür.

    Aynı gün aynı adla yetime düşmüş kopya ezilmez: yenisi sıra ekiyle (`<ad>-<n>`) yanına konur,
    `yetimdeki_kopyalar` onu da verir. `yetim/` ayrıca kurulur: `dizin_kur` kipi yalnız son dizine
    çeker, ara dizin umask'la kalırdı (§4.5).
    """
    kaynak = depo_yolu(depo, ad)
    dizin_kur(depo / YETIM_DIZINI)
    dizin = dizin_kur(yetim_gun_dizini(depo, gun))
    hedef = dizin / ad
    sira = 0
    while os.path.lexists(hedef):
        sira += 1
        hedef = dizin / f"{ad}-{sira}"
    yerine_tasi(kaynak, hedef)
    return hedef


def _kopya_sirasi(kopya: str, ad: str) -> int | None:
    """Yetimdeki adın sıra eki: asıl adda 0, `<ad>-<n>`'de n; bu adın kopyası değilse None."""
    if kopya == ad:
        return 0
    eslesme = _SIRA_EKI_DESENI.fullmatch(kopya, len(ad)) if kopya.startswith(ad) else None
    return None if eslesme is None else int(eslesme[1])


def yetimdeki_kopyalar(depo: Path, ad: str) -> list[Path]:
    """`dosyalar/yetim/<gün>/`'deki `<ad>` ve `<ad>-<n>` kopyaları; okunamayan dizin atlanır.

    En yeni gün önce gelir; günün içinde asıl ad, sonra sıra ekleri artan sırayla.
    """
    depo_adi_denetle(ad)
    kok = depo / YETIM_DIZINI
    try:
        gunler = sorted(
            (gun for gun in os.listdir(kok) if _YETIM_GUNU_DESENI.fullmatch(gun)), reverse=True
        )
    except OSError:
        return []
    kopyalar: list[Path] = []
    for gun in gunler:
        try:
            adlar = os.listdir(kok / gun)
        except OSError:
            continue
        siralar = {kopya: _kopya_sirasi(kopya, ad) for kopya in adlar}
        bulunan = {kopya: sira for kopya, sira in siralar.items() if sira is not None}
        kopyalar += [kok / gun / kopya for kopya in sorted(bulunan, key=bulunan.__getitem__)]
    return kopyalar


def depoya_yaz(dizin: Path, stored_name: str, kap: bytes) -> Path:
    """Kabı `dizin/<stored_name>`'e atomik yazar (ad desen denetiminden geçer); yolu döndürür."""
    yol = depo_yolu(dizin, stored_name)
    atomik_yaz(yol, kap)
    return yol


def depodan_ac(dizin: Path, stored_name: str, *, key_wrap: str, sarmal_anahtari: bytes) -> bytes:
    """`dizin/<stored_name>`'deki kabı okur, sarmalı açar ve bellekte çözer; açık içeriği verir.

    Ad yol kurulmadan önce denetlenir; boy sınırı okumadan önce denetlenir. Dosya yoksa
    `FileNotFoundError` çağırana gider ("dosya yok" depo servisinin kararıdır).
    """
    yol = depo_yolu(dizin, stored_name)
    kap = kabi_oku(yol)
    anahtar = anahtari_ac(key_wrap, sarmal_anahtari=sarmal_anahtari, stored_name=stored_name)
    return coz(kap, dosya_anahtari=anahtar, stored_name=stored_name)
