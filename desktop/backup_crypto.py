"""OAB Defteri yedek kabı (`ODBAK\\x03`; tasarım §2.3.1, §4.4.4, §4.4.7; plan F1b-3 "Kap ve manifesto").

Yedekleme için asimetrik zarf şifrelemesi kullanılır: veri anahtarından türetilen
X25519 özel anahtar yalnız bir hesabın parolasıyla kilit açıldığında elde edilebilir;
açık anahtar ise başlangıçta parola sorulmadan yedek alınabilmesi için diskte tutulur.
Yedek içeriği AES-256-GCM ile hem şifrelenir hem de doğrulanır.

Yedeğin kurtarma başlığı (tasarım TK10, §4.4.4) `guvenlik.json`'un yalnız kurtarma
bölümünü ve kurtarma anahtarının kimliğini (no, tarih) taşır; hesap sarmalları
yedeğe girmez (`recovery_header_from_state`). Aynı bilgisayarda geri yükleme güncel
`guvenlik.json` ve bir hesabın parolasıyla, yeni bilgisayarda kurtarma anahtarıyla
yapılır. Anahtarın kimliğini okuyan tek kural `recovery_key_identity`'dir (durum
özeti, kurtarma anahtarı belgesi, yedek listesi ve geri yüklemenin iletisi).

BAŞLIKSIZ YEDEK ÜRETİLMEZ (plan F1b-3 "Kap ve manifesto"): her yazıcı kullanılabilir kurtarma
başlığı ister (`usable_recovery_header`; arşiv kopyasına ve boş başlığa düşüş yoktur). Yedeği
başka bilgisayarda açmanın tek yolu bu başlıktır (tasarım §4.3 tehdit 8).

BAYT DÜZENİ. İlk 54+L bayt aile kabındaki gibidir; ardına kapsam ve uzunluk gelir. Şifreli
metinden önceki HER BAYT AAD'dir (bir bitin dönmesi çözmeyi düşürür):

    MAGIC 6 ‖ geçici X25519 açık anahtarı 32 ‖ nonce 12 ‖ L 4 ‖ kurtarma başlığı L ‖
    kapsam 1 (`01` yerel, `02` tam) ‖ S 8 ‖ mühürlü bölüm S ‖ [dosya bölümü]

Uzunluk alanları big-endian'dır; mühürlü bölüm AES-256-GCM şifreli metin ve 16 baytlık etikettir.
Mühürlü düz metin: veritabanı uzunluğu 8 ‖ SQLite görüntüsü ‖ manifesto. Veritabanı görüntüsü ve
manifesto bellekte şifrelenir (aile kabı). Yedek listesi kapsamı kurtarma anahtarı olmadan,
dosyanın yalnız başından okur (`kap_basligini_oku`). Yerel yedek mühürlü bölümde biter: ardında
bayt kalırsa yedek reddedilir. Kapsam baytı AAD'de olduğu için kesik bir tam yedek yerel yedek
sanılamaz.

MANİFESTO: kanonik UTF-8 JSON (`Manifesto`): `surum`, `kapsam`, `dosyalar: [{ad, boyut, sha256,
eksik?}]`; kapsamı başlıktaki baytla eşit olmalıdır. `boyut` ve `sha256` eklerin AÇIK
içeriğinindir (`shared.dosya_sifreleme` "ÖZET VE BOY"). `eksik` yalnız tam yedekte, diskte
düzenli dosya olarak ve beklenen boyda bulunmayan ya da açılamayan ek (`_diskteki_hali`) ve ön
okumada okunamayan ya da tutmayan ek (`encrypted_backup`) içindir: o ek dosya bölümüne girmez. Geri yükleme veritabanını ve manifestoyu AYRI alır (`YedekIcerigi`): yetki denetimine ve takasa yalnız
veritabanı baytları gider.

DOSYA BÖLÜMÜ (yalnız tam yedek): manifesto sırasıyla, `eksik` olmayan her ek için

    ad 32 (ASCII) ‖ şifreli boy 8 (big-endian) ‖ `ODDOSYA` kabının baytları

ve bitiş işareti (`DOSYA_BOLUMU_SONU`; ad alanı desene uymadığı için girdiyle karışmaz). Ekler
zaten dosya anahtarıyla şifrelidir, ikinci kez şifrelenmez; sarmalları mühürlü veritabanının
içindedir. Bellekte toplanmaz, parça parça kopyalanır (`tam_yedek_yaz`, `dosya_bolumunu_oku`).
Bölüm AAD'nin dışındadır, bütünlüğünü mühürlü manifesto kurar: okuyucu sırayı, adı ve boyu
manifestoyla karşılaştırır. Adı manifestodaki adla bayt bayt eşit olmayan girdi reddedildiği için
dışarı çıkan her ad desenden geçmiştir (yol geçişi yok).

BOZUKLUĞUN İKİ DÜZEYİ (kullanıcı kararı 04.11.2026 "Bozuk ekte geri yükleme durur, ikinci onayla
sürer"): kesik, sırası bozuk ya da manifestoda olmayan girdi KAP düzeyindedir
(`DosyaBolumuHatasi`): geri yükleme yapılmaz, onayla da sürdürülmez. Özeti tutmayan ek GİRDİ
düzeyindedir (`EkTutmuyorHatasi`): kararı geri yükleme verir.

MASAÜSTÜ KATMANI BACKEND'İ İÇE AKTARMAZ: dosya kabının bu modülün bilmesi gereken üç sabiti (ad
deseni, şifreli boy farkı, biçim üst sınırı) burada yeniden yazılıdır; `shared.dosya_sifreleme`
ile eşitliği backend testinde sabittir.

DOSYA YAZIMI (tasarım §4.5; plan F1b-3 "Dosya deposu"): yazıcılar umask'a güvenmez, `.odbak` açıkça
0600 açılır ve kipi çekilir. Yerel yedek geçici adla yazılır, `fsync` edilir, `os.replace` ile
asıl adına konur.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import stat
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import IO, Any, Final

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAGIC = b"ODBAK\x03"
#: F1b-3'ten önceki kap (plan "Kap ve manifesto"): açılmaz, ayrı iletiyle reddedilir.
DENEME_MAGIC = b"ODBAK\x02"
CONFIG_FILE_NAME = "yedekleme.json"
# Kurtarma başlığının kaynağı (`apps.okul.services.app_password.STATE_FILE_NAME`
# ile aynı ad; masaüstü katmanı backend'i import etmez).
SECURITY_STATE_FILE_NAME = "guvenlik.json"
BACKUP_SUFFIX = ".odbak"
#: Kapsam baytı: yerel yedek (veritabanı + manifesto) ve tam yedek (+ dosya bölümü).
KAPSAM_YEREL: Final = 1
KAPSAM_TAM: Final = 2
MANIFESTO_SURUMU: Final = 1
_NONCE_BYTES = 12
_PUBLIC_BYTES = 32
_LENGTH_BYTES = 4
_KAPSAM_BYTES = 1
_SEALED_LENGTH_BYTES = 8
_DB_LENGTH_BYTES = 8
_TAG_BYTES = 16
_PRIVATE_INFO = b"OABDefteri/backup/private/v1"
_ENVELOPE_INFO = b"OABDefteri/backup/envelope/v1"
#: Sabit başlığın boyu: sihirli bayt + geçici açık anahtar + nonce + başlık uzunluğu.
_FIXED_HEADER_BYTES = len(MAGIC) + _PUBLIC_BYTES + _NONCE_BYTES + _LENGTH_BYTES
#: Gömülü kurtarma başlığının üst sınırı (bayt); yazarken de okurken de aynı sınır.
MAX_RECOVERY_HEADER_BYTES = 1_000_000
#: AES-GCM'nin tek çağrıda aldığı en büyük girdi (`cryptography`: 2^31 - 1 bayt). Şifreli metin
#: etiketi de taşıdığı için sınır mühürlü bölüme konur.
_AZAMI_MUHURLU_BOY: Final = 2**31 - 1
#: En kısa mühürlü bölüm: veritabanı uzunluğu ve etiket.
_EN_KISA_MUHURLU_BOY: Final = _DB_LENGTH_BYTES + _TAG_BYTES

#: Dosya bölümü girdisinin başı: ad + şifreli boy (bitiş işareti de bu boydadır).
_DOSYA_AD_BAYT: Final = 32
_DOSYA_BOY_BAYT: Final = 8
_GIRDI_BASI_BAYT: Final = _DOSYA_AD_BAYT + _DOSYA_BOY_BAYT
#: Dosya bölümünün bitiş işareti. Tanınır bir metindir: sıfırla dolmuş kuyruk işaret sayılmaz.
DOSYA_BOLUMU_SONU: Final = b"ODBAK-DOSYA-BOLUMU-SONU".ljust(_GIRDI_BASI_BAYT, b"\x00")
#: Akışla kopyanın parçası (bayt): bellekte aynı anda en çok bu kadar ek gövdesi durur.
KOPYA_PARCASI: Final = 1024 * 1024

# Dosya kabının sabitleri (modül başlığı; eşitlik backend testinde).
#: Depo adının deseni (`uuid4().hex`); `fullmatch` ile uygulanır.
DEPO_ADI_DESENI: Final = re.compile(r"[0-9a-f]{32}")
#: `ODDOSYA` kabının açık içeriğe eklediği bayt: şifreli boy = açık boy + 36.
DOSYA_KAP_EK_BAYT: Final = 36
#: Dosya kabının biçim üst sınırı (şifreli boy, bayt).
DOSYA_AZAMI_SIFRELI_BOY: Final = 64 * 1024 * 1024

_SHA256_DESENI: Final = re.compile(r"[0-9a-f]{64}")
#: `.odbak` dosyasının POSIX kipi (tasarım §4.5).
YEDEK_DOSYA_KIPI: Final = 0o600
# `O_CREAT | O_EXCL` var olan adı (sembolik bağ dâhil) açmaz; Windows'ta da geçerlidir.
_YAZMA_BAYRAKLARI: Final = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
# Depodan okumada sembolik bağ izlenmez; `O_NONBLOCK` FIFO'da süresiz beklemeyi keser
# (`shared.dosya_sifreleme` ile aynı bayraklar).
_OKUMA_BAYRAKLARI: Final = (
    os.O_RDONLY
    | getattr(os, "O_BINARY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_NONBLOCK", 0)
)

_BOZUK_BASLIK_ILETISI: Final = "Yedek başlığı bozuk veya eksik."
_BOZUK_ICERIK_ILETISI: Final = "Yedek çözüldü ama içeriği bozuk; dosya bozulmuş olabilir."
_BOZUK_LISTE_ILETISI: Final = "Yedeğin dosya listesi bozuk."
_BOZUK_DOSYA_BOLUMU_ILETISI: Final = (
    "Yedeğin ekleri taşıyan bölümü bozuk ya da eksik; bu yedek geri yüklenemez."
)


class BackupCryptoError(ValueError):
    """Bozuk/uyumsuz yedek veya anahtar hatası."""


class YedekAnahtariHatasi(BackupCryptoError):
    """Mühürlü bölüm bu anahtarla açılmadı.

    Yanlış anahtar ve AAD'si ya da şifreli metni değişmiş dosya aynı sonucu verir: GCM bunları
    ayırmaz. Geri yükleme bu hatada sıradaki adayı dener; öteki hatalar yedeğin kendisini anlatır.
    """


class DenemeYedegiHatasi(BackupCryptoError):
    """`ODBAK\\x02`: deneme sürümünün kabı açılmaz (plan F1b-1 "Eski veri", F1b-3 "Kap ve manifesto")."""

    def __init__(self) -> None:
        super().__init__("Bu yedek programın deneme sürümüyle alınmış; bu sürümle açılamaz.")


class DosyaBolumuHatasi(BackupCryptoError):
    """KAP DÜZEYİ: dosya bölümünün kendisi bozuk (kesik, sırası bozuk, manifestoda olmayan girdi).

    Geri yükleme yapılmaz, onayla da sürdürülmez (modül başlığı "BOZUKLUĞUN İKİ DÜZEYİ").
    """

    def __init__(self) -> None:
        super().__init__(_BOZUK_DOSYA_BOLUMU_ILETISI)


class EkTutmuyorHatasi(BackupCryptoError):
    """GİRDİ DÜZEYİ: bölümün yapısı sağlam, bir ekin içeriği manifestoyu tutmuyor.

    Yalnız bu ek bozuktur; geri yüklemenin durması ve ikinci onayla sürmesi çağıranın kararıdır
    (modül başlığı "BOZUKLUĞUN İKİ DÜZEYİ"). `ad` depo adıdır, kişisizdir.
    """

    def __init__(self, ad: str) -> None:
        super().__init__("Bir ekin içeriği yedek alınırkenki özetini tutmuyor.")
        self.ad = ad


def _hkdf(value: bytes, *, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(value)


def private_key_from_data_key(data_key: bytes) -> X25519PrivateKey:
    """Uygulama DEK'inden alan şifrelemesinden bağımsız yedek özel anahtarı türetir."""
    return X25519PrivateKey.from_private_bytes(_hkdf(data_key, info=_PRIVATE_INFO))


def public_key_bytes(data_key: bytes) -> bytes:
    return (
        private_key_from_data_key(data_key)
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    )


def config_path(data_dir: Path) -> Path:
    return data_dir / CONFIG_FILE_NAME


def ensure_public_config(data_dir: Path, data_key: bytes, *, replace: bool = False) -> Path:
    """Açık yedek anahtarını atomik yazar; mevcut farklı anahtarı sessizce ezmez."""
    path = config_path(data_dir)
    encoded = base64.b64encode(public_key_bytes(data_key)).decode("ascii")
    if path.is_file() and not replace:
        current = load_public_key(data_dir)
        if current.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ) != base64.b64decode(encoded):
            raise BackupCryptoError("Yedekleme anahtarı bu veri anahtarıyla eşleşmiyor.")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(
        json.dumps({"surum": 1, "algoritma": "X25519+AES-256-GCM", "acik_anahtar": encoded}),
        encoding="utf-8",
    )
    temp.replace(path)
    return path


def load_public_key(data_dir: Path) -> X25519PublicKey:
    try:
        raw = json.loads(config_path(data_dir).read_text(encoding="utf-8"))
        key = base64.b64decode(str(raw["acik_anahtar"]), validate=True)
        if len(key) != _PUBLIC_BYTES:
            raise ValueError
        return X25519PublicKey.from_public_bytes(key)
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise BackupCryptoError(
            "Şifreli yedekleme anahtarı yok veya bozuk; önce program yöneticisi hesabını "
            "kurup kilidi açın."
        ) from exc


def can_encrypt(data_dir: Path) -> bool:
    try:
        load_public_key(data_dir)
    except BackupCryptoError:
        return False
    return True


#: `guvenlik.json` şema sürümü (tasarım §2.3.1, §4.4.4). Şema 1 (tek yönetici
#: parolası) KULLANILAMAZ sayılır: çevirici yazılmadı, deneme kurulumları yeniden
#: kurulur (plan F1b-1 "Eski veri"). Hesap sarmalının kimliğe bağlanması (02.11.2026)
#: sürümü DEĞİŞTİRMEDİ: sürüm yedek başlığında da geçer ve başlığın taşıdığı kurtarma
#: bölümü değişmedi; yükseltmek eski yedekleri ve bağdan önceki dosyaların kurtarma
#: yolunu kapatırdı. Bağsız sarmalı `app_password` kendi etiketiyle reddeder.
SECURITY_STATE_VERSION = 2


def is_usable_security_state(data: object) -> bool:
    """Güvenlik durumu (`guvenlik.json` içeriği ya da yedek başlığı) DEK'i açmaya yeter mi? — TEK KURAL.

    Aynı kural üç yerde uygulanır ve yalnız burada tanımlıdır:

    * günlük/göç öncesi yedeğin kurtarma başlığı (`desktop.backup`): kullanılamaz
      başlıkla yedek ALINMAZ, rotasyon da koşmaz;
    * güvenlik dosyası kayıp kilidi (`app_password.security_file_missing`): dosya
      var ama kullanılamıyorsa kayıp sayılır (tasarım §4.3 tehdit 8);
    * geri yüklemede aday durumlar (`backup_restore`).

    Biçim yapısaldır (kriptografik doğrulama değildir; yanlış sarmal çözümde
    açık hatayla düşer). Şema 2 (tasarım §4.4.4): JSON sözlük; `surum` 2; `kdf`
    sözlük; `hesaplar` varsa liste; hesap sarmallarından (`{id, tanitici, salt,
    sarmal}`) EN AZ BİRİ ya da `kurtarma` bölümü (`{salt, sarmal}`) tam. Yedek
    başlığı yalnız kurtarma bölümünü taşır (TK10; `hesaplar` yoktur) ve aynı
    kuraldan geçer. Kurtarmayla geri yüklemeden sonra `hesaplar` boştur: dosya
    yalnız kurtarma bölümüyle kullanılabilir (kurtarma anahtarıyla aç + program
    yöneticisi parolası). Tek tam sarmal DEK'i açmaya yeter (o sırla); birini şart
    koşmak, açılabilecek bir dosyayı "kayıp" sayıp kilidi açtırmaz, yedeği de
    durdururdu. Hesap sarmalının kimliğe bağlı türetim etiketi (`turetim`) bu kurala
    GİRMEZ: bağdan önce yazılmış sarmallı dosya kurtarma bölümüyle kullanılabilir kalır
    (kurtarma anahtarı yolu açık); bağsız sarmalı parola yolunda `app_password` reddeder.
    """
    if not isinstance(data, dict):
        return False
    if data.get("surum") != SECURITY_STATE_VERSION:
        return False
    if not isinstance(data.get("kdf"), dict):
        return False
    hesaplar = data.get("hesaplar", [])
    if not isinstance(hesaplar, list):
        return False
    if any(_is_complete_account_wrap(hesap) for hesap in hesaplar):
        return True
    return _is_complete_wrap(data.get("kurtarma"))


def _is_complete_wrap(bolum: object) -> bool:
    """Sarmal bölümü (`{"salt": ..., "sarmal": ...}`) iki alanı da dolu dize mi?"""
    if not isinstance(bolum, dict):
        return False
    return all(isinstance(bolum.get(alan), str) and bolum[alan] for alan in ("salt", "sarmal"))


def _is_complete_account_wrap(hesap: object) -> bool:
    """Hesap sarmalı kimliği, tanıtıcısı, tuzu ve sarmalı dolu mu?"""
    if not isinstance(hesap, dict) or not _is_complete_wrap(hesap):
        return False
    return all(isinstance(hesap.get(alan), str) and hesap[alan] for alan in ("id", "tanitici"))


def parse_security_state(raw: bytes) -> dict[str, Any] | None:
    """Ham `guvenlik.json` baytlarını ayrıştırır; kullanılamazsa None (hata değil).

    Derin iç içe JSON (`[[[[…]]]]`, 1 MB başlık sınırının çok altında) `json.loads`'ta
    `RecursionError` yükseltir; o da "kullanılamaz"dır. Yakalanmasaydı yedek klasörüne
    konmuş tek bir bozuk ya da kasıtlı hazırlanmış yedek, yedek listesini (kayıp kilidinin
    çıkış yolu) ve geri yükleme çekirdeğini 500'e düşürürdü.
    """
    try:
        data: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None
    return data if is_usable_security_state(data) else None


def recovery_header_from_state(data: object) -> dict[str, Any] | None:
    """Güvenlik durumunun yedek başlığına giden izdüşümü; kurtarma bölümü yoksa None.

    TK10 (tasarım §4.4.4): başlık YALNIZ `{surum, kdf, kurtarma: {no, tarih, salt,
    sarmal}}` taşır. Hesap sarmalları yedeğe GİRMEZ (dönemi biten üyenin eski
    parolası eski yedeği açmasın; §4.3 tehdit 5) ve doğrulama damgası da girmez
    (başlık yeni bilgisayarda anahtarın no'sunu ve tarihini gösterir, kâğıdın
    saklanıp saklanmadığını değil).
    """
    if not isinstance(data, dict) or not is_usable_security_state(data):
        return None
    kurtarma = data.get("kurtarma")
    if not isinstance(kurtarma, dict) or not _is_complete_wrap(kurtarma):
        return None
    bolum: dict[str, Any] = {"salt": kurtarma["salt"], "sarmal": kurtarma["sarmal"]}
    for alan in ("no", "tarih"):
        if alan in kurtarma:
            bolum[alan] = kurtarma[alan]
    return {"surum": SECURITY_STATE_VERSION, "kdf": data["kdf"], "kurtarma": bolum}


def recovery_key_identity(data: object) -> dict[str, Any] | None:
    """Kurtarma anahtarının kimliği `{no, tarih}` — hangi kâğıdın açtığı (TK10); yoksa None.

    `data` güvenlik durumu (`guvenlik.json`) ya da yedek başlığıdır; kurtarma
    bölümünün YALNIZ `no` ve `tarih` alanı okunur, tuz ve sarmal dönmez. `no` 1 ya
    da daha büyük bir tamsayıdır (bool değil; her yeni anahtarda bir artar), `tarih`
    üretim gününün ISO biçimidir (`YYYY-AA-GG`; ekranda ve kâğıtta gg.aa.yyyy
    yazılır). Biçimsiz alan None olur; ikisi de yoksa sonuç None'dır. Durumun
    kullanılabilirliğine bakmaz: kullanılamaz başlığı çağıran önce eler
    (`parse_security_state`).
    """
    if not isinstance(data, dict):
        return None
    bolum = data.get("kurtarma")
    if not isinstance(bolum, dict):
        return None
    no = bolum.get("no")
    if not isinstance(no, int) or isinstance(no, bool) or no < 1:
        no = None
    tarih = bolum.get("tarih")
    gun: str | None = None
    if isinstance(tarih, str) and tarih:
        try:
            gun = date.fromisoformat(tarih).isoformat()
        except ValueError:
            gun = None
    if no is None and gun is None:
        return None
    return {"no": no, "tarih": gun}


def _header_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")


def usable_recovery_header(data_dir: Path) -> bytes | None:
    """Güncel `guvenlik.json`'un yedek başlığı (TK10 izdüşümü); kullanılamazsa None.

    Yok, okunamıyor, boş, biçimsiz ya da kurtarma bölümü eksik dosya aynı sonucu
    verir: böyle bir başlıkla alınan yedek başka bilgisayarda hiçbir sırla
    açılamazdı (tasarım §4.3 tehdit 8). Dosyanın kendisi gömülmez.
    """
    try:
        raw = (data_dir / SECURITY_STATE_FILE_NAME).read_bytes()
    except OSError:
        return None
    baslik = recovery_header_from_state(parse_security_state(raw))
    return _header_bytes(baslik) if baslik is not None else None


def _kurtarma_basligi_denetle(baslik: bytes) -> None:
    """Başlıksız yedek üretilmez (modül başlığı): kurtarma bölümü kullanılamıyorsa yazım durur."""
    if recovery_header_from_state(parse_security_state(baslik)) is None:
        raise BackupCryptoError("Kurtarma başlığı kullanılamıyor; yedek yazılmadı.")


# ---------------------------------------------------------------------------
# Manifesto
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ManifestoGirdisi:
    """Bir ek: depo adı, açık boyu ve açık içeriğinin özeti; `eksik` yalnız tam yedekte.

    Kurulurken denetlenir: adı desene uymayan girdi manifestoya giremez, bu yüzden manifestodan
    çıkan ad yol birleştirmesine uygundur. Boy, kaba sığan en büyük açık içerikle sınırlıdır.
    """

    ad: str
    boyut: int
    sha256: str
    eksik: bool = False

    def __post_init__(self) -> None:
        if (
            not isinstance(self.ad, str)
            or DEPO_ADI_DESENI.fullmatch(self.ad) is None
            or not isinstance(self.boyut, int)
            or isinstance(self.boyut, bool)
            or not 0 < self.boyut <= DOSYA_AZAMI_SIFRELI_BOY - DOSYA_KAP_EK_BAYT
            or not isinstance(self.sha256, str)
            or _SHA256_DESENI.fullmatch(self.sha256) is None
        ):
            raise BackupCryptoError(_BOZUK_LISTE_ILETISI)

    @property
    def sifreli_boy(self) -> int:
        """Kabın boyu (`shared.dosya_sifreleme.sifreli_boy`)."""
        return self.boyut + DOSYA_KAP_EK_BAYT


@dataclass(frozen=True)
class Manifesto:
    """Yedeğin ek listesi; `kapsam` başlıktaki kapsam baytıyla eşittir (modül başlığı)."""

    kapsam: int
    dosyalar: tuple[ManifestoGirdisi, ...] = ()

    def __post_init__(self) -> None:
        if self.kapsam not in (KAPSAM_YEREL, KAPSAM_TAM):
            raise BackupCryptoError(_BOZUK_LISTE_ILETISI)
        if len({girdi.ad for girdi in self.dosyalar}) != len(self.dosyalar):
            raise BackupCryptoError(_BOZUK_LISTE_ILETISI)
        if self.kapsam == KAPSAM_YEREL and any(girdi.eksik for girdi in self.dosyalar):
            raise BackupCryptoError(_BOZUK_LISTE_ILETISI)

    @property
    def tasinanlar(self) -> tuple[ManifestoGirdisi, ...]:
        """Dosya bölümünde bulunması gereken girdiler, bölümdeki sırayla (`eksik` olmayanlar)."""
        return tuple(girdi for girdi in self.dosyalar if not girdi.eksik)

    def baytlar(self) -> bytes:
        """Kanonik UTF-8 JSON: anahtarlar sıralı, boşluksuz; `eksik` yalnız doğruysa yazılır."""
        dosyalar: list[dict[str, Any]] = []
        for girdi in self.dosyalar:
            satir: dict[str, Any] = {
                "ad": girdi.ad,
                "boyut": girdi.boyut,
                "sha256": girdi.sha256,
            }
            if girdi.eksik:
                satir["eksik"] = True
            dosyalar.append(satir)
        veri = {"surum": MANIFESTO_SURUMU, "kapsam": self.kapsam, "dosyalar": dosyalar}
        return json.dumps(veri, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )


#: Eki olmayan yerel yedeğin manifestosu (`pre-parola`; tasarım §4.4.7 tablosu "Veritabanı").
BOS_YEREL_MANIFESTO: Final = Manifesto(KAPSAM_YEREL)


def manifesto_ayristir(ham: bytes, *, kapsam: int) -> Manifesto:
    """Mühürlü bölümden çıkan manifestoyu okur; kapsamı başlıktaki baytla eşit olmalıdır.

    Biçim katıdır: manifesto başlığın kapsamıyla yeniden kurulur ve kanonik baytları gelen baytları
    tutmalıdır. Böylece başka kapsam, başka sürüm, bilinmeyen anahtar ve kanonik olmayan yazım tek
    denetimde düşer.
    """
    try:
        veri: Any = json.loads(ham.decode("utf-8"))
        manifesto = Manifesto(
            kapsam, tuple(ManifestoGirdisi(**satir) for satir in veri["dosyalar"])
        )
    except (ValueError, RecursionError, KeyError, TypeError) as exc:
        raise BackupCryptoError(_BOZUK_LISTE_ILETISI) from exc
    if manifesto.baytlar() != ham:
        raise BackupCryptoError(_BOZUK_LISTE_ILETISI)
    return manifesto


def ek_denetle(girdi: ManifestoGirdisi, acik: bytes) -> None:
    """Çözülmüş ekin açık içeriğini manifestoyla karşılaştırır; tutmazsa `EkTutmuyorHatasi`.

    Özet açık içeriğindir: ek ancak görüntüdeki sarmal ve DEK'le çözülünce sınanabilir, bunu
    geri yükleme yapar. Bu işlev yalnız karşılaştırır.
    """
    if len(acik) != girdi.boyut or hashlib.sha256(acik).hexdigest() != girdi.sha256:
        raise EkTutmuyorHatasi(girdi.ad)


# ---------------------------------------------------------------------------
# Mühürleme ve yazım
# ---------------------------------------------------------------------------
def _muhurle(
    database: bytes,
    manifesto: bytes,
    kapsam: int,
    public_key: X25519PublicKey,
    recovery_header: bytes,
    *,
    ephemeral: X25519PrivateKey | None = None,
    nonce: bytes | None = None,
) -> tuple[bytes, bytes]:
    """(şifreli metinden önceki baytlar, mühürlü bölüm).

    Başlık kapısı yazıcılardadır. `ephemeral` ve `nonce` yalnız altın vektör testinde verilir.
    """
    if len(recovery_header) > MAX_RECOVERY_HEADER_BYTES:
        raise BackupCryptoError("Yedek kurtarma başlığı beklenenden büyük.")
    acik = len(database).to_bytes(_DB_LENGTH_BYTES, "big") + database + manifesto
    muhurlu_boy = len(acik) + _TAG_BYTES
    if muhurlu_boy > _AZAMI_MUHURLU_BOY:
        raise BackupCryptoError("Veritabanı tek yedeğe sığmayacak kadar büyük.")
    gecici = ephemeral if ephemeral is not None else X25519PrivateKey.generate()
    gecici_acik = gecici.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    aes_key = _hkdf(gecici.exchange(public_key), info=_ENVELOPE_INFO)
    tek_seferlik = nonce if nonce is not None else os.urandom(_NONCE_BYTES)
    aad = (
        MAGIC
        + gecici_acik
        + tek_seferlik
        + len(recovery_header).to_bytes(_LENGTH_BYTES, "big")
        + recovery_header
        + kapsam.to_bytes(_KAPSAM_BYTES, "big")
        + muhurlu_boy.to_bytes(_SEALED_LENGTH_BYTES, "big")
    )
    return aad, AESGCM(aes_key).encrypt(tek_seferlik, acik, aad)


def encrypt_bytes(
    database: bytes,
    public_key: X25519PublicKey,
    *,
    recovery_header: bytes,
    manifesto: Manifesto = BOS_YEREL_MANIFESTO,
) -> bytes:
    """Yerel kapsamlı kabı bellekte kurar; tam yedek `tam_yedek_yaz`'la akışla yazılır."""
    if manifesto.kapsam != KAPSAM_YEREL:
        raise BackupCryptoError("Tam yedek bellekte kurulmaz.")
    _kurtarma_basligi_denetle(recovery_header)
    aad, muhurlu = _muhurle(
        database, manifesto.baytlar(), KAPSAM_YEREL, public_key, recovery_header
    )
    return aad + muhurlu


def yeni_yedek_dosyasi(yol: Path) -> IO[bytes]:
    """Yeni dosyayı 0600 açar: var olan adı açmaz, kip umask'tan bağımsız çekilir (modül başlığı)."""
    tanitici = os.open(yol, _YAZMA_BAYRAKLARI, YEDEK_DOSYA_KIPI)
    try:
        if hasattr(os, "fchmod"):  # Windows'ta yoktur; dosya kullanıcı profilindedir.
            os.fchmod(tanitici, YEDEK_DOSYA_KIPI)
        return os.fdopen(tanitici, "wb")
    except BaseException:
        os.close(tanitici)
        raise


def _diske_indir(akis: IO[bytes]) -> None:
    akis.flush()
    os.fsync(akis.fileno())


def _dizini_esitle(dizin: Path) -> None:
    """POSIX'te ad değişikliğini diske indirir; Windows'ta dizin açılamaz, gerek de yoktur."""
    if os.name != "posix":
        return
    tanitici = os.open(dizin, os.O_RDONLY)
    try:
        os.fsync(tanitici)
    finally:
        os.close(tanitici)


def encrypt_to_path(
    database: bytes,
    target: Path,
    public_key: X25519PublicKey,
    *,
    recovery_header: bytes,
    manifesto: Manifesto = BOS_YEREL_MANIFESTO,
) -> None:
    """Yerel yedeği atomik yazar: geçici ad, 0600, `fsync`, `os.replace`."""
    icerik = encrypt_bytes(
        database, public_key, recovery_header=recovery_header, manifesto=manifesto
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.unlink(missing_ok=True)
    try:
        with yeni_yedek_dosyasi(temp) as akis:
            akis.write(icerik)
            _diske_indir(akis)
        os.replace(temp, target)
        _dizini_esitle(target.parent)
    finally:
        temp.unlink(missing_ok=True)


def _acilan_boy(yol: Path) -> int | None:
    """Dosyanın açılarak okunan boyu; düzenli dosya değilse ya da açılamıyorsa None.

    Önce `lstat`: bağ izlenmez (Windows'ta `O_NOFOLLOW` yoktur), düzenli olmayan dosya açılmaz.
    Düzenli dosya da açılıp sınanır: virüs tarayıcısının paylaşım ihlali ya da bozuk izin `lstat`'ta görünmez.
    """
    try:
        if not stat.S_ISREG(os.lstat(yol).st_mode):
            return None
        with os.fdopen(os.open(yol, _OKUMA_BAYRAKLARI), "rb", buffering=0) as dosya:
            return os.fstat(dosya.fileno()).st_size
    except OSError:
        return None


def _diskteki_hali(girdi: ManifestoGirdisi, store_dir: Path) -> ManifestoGirdisi:
    """Dosyası diskte düzenli dosya olarak ve beklenen boyda durmayan ya da açılamayan ek `eksik`.

    Karar manifesto mühürlenmeden burada verilir, sonra `eksik` yazılamaz. Boyu tutmayan dosyayı
    taşımak tam yedeği kap düzeyinde bozardı: okuyucu boyu manifestoyla karşılaştırır ve bütün
    yedeği reddeder. Açılamayan dosya da yedeği düşürmez (yedeksiz kalmak eksik ekli yedekten
    ağırdır; plan "Kap ve manifesto"). Çağıranın `eksik` verdiği ek öyle kalır: bu katman DEK'i
    tanımaz, ekin baştan sona okunmasını şifreli yedek servisi yazımdan önce yapar (kullanıcı kararı
    05.11.2026 "Şifreli yedek yazılmadan önce her ek bir kez okunur"). Servis elindeki DEK'le ekin
    içeriğini de sınar (kullanıcı kararı 06.11.2026; `encrypted_backup` başlığı, 4. adım). Bu
    sınamadan geçmemiş boyu tutan bozuk dosya taşınır, geri yükleme onu girdi düzeyinde yakalar.
    """
    eksik = girdi.eksik or _acilan_boy(store_dir / girdi.ad) != girdi.sifreli_boy
    return ManifestoGirdisi(girdi.ad, girdi.boyut, girdi.sha256, eksik=eksik)


def _ek_govdesini_kopyala(hedef: IO[bytes], kaynak: Path, boy: int) -> None:
    """Depo dosyasını parça parça kopyalar; hiçbir anda bir parçadan fazlası bellekte durmaz."""
    with os.fdopen(os.open(kaynak, _OKUMA_BAYRAKLARI), "rb", buffering=0) as dosya:
        bilgi = os.fstat(dosya.fileno())
        if not stat.S_ISREG(bilgi.st_mode) or bilgi.st_size != boy:
            raise BackupCryptoError("Ek dosyası yedek alınırken değişti; yedek yazılmadı.")
        kalan = boy
        while kalan:
            parca = dosya.read(min(KOPYA_PARCASI, kalan))
            if not parca:
                raise BackupCryptoError("Ek dosyası yedek alınırken değişti; yedek yazılmadı.")
            hedef.write(parca)
            kalan -= len(parca)


def _dosya_bolumunu_yaz(hedef: IO[bytes], manifesto: Manifesto, store_dir: Path) -> None:
    for girdi in manifesto.tasinanlar:
        hedef.write(girdi.ad.encode("ascii"))
        hedef.write(girdi.sifreli_boy.to_bytes(_DOSYA_BOY_BAYT, "big"))
        _ek_govdesini_kopyala(hedef, store_dir / girdi.ad, girdi.sifreli_boy)
    hedef.write(DOSYA_BOLUMU_SONU)


def tam_yedek_yaz(
    target: Path,
    database: bytes,
    files: Iterable[ManifestoGirdisi],
    store_dir: Path,
    public_key: X25519PublicKey,
    *,
    recovery_header: bytes,
) -> Manifesto:
    """Tam yedeği `target`'a akışla yazar; yedeğin manifestosunu döndürür.

    Manifesto mühürlü bölümde dosyalardan ÖNCE durduğu için `eksik` işaretleri yazımdan önce
    konur (`_diskteki_hali`); dönen manifestodaki `eksik` sayısını ekran söyler (plan "Kap ve
    manifesto"). Mühürden sonra `eksik` yazılamaz: gövde okunurken çıkan hata yazımı düşürür ve
    çağırana geçer. `target` çağıranın seçtiği geçici addır: var olan adın üzerine yazılmaz (0600,
    `O_EXCL`), yarıda kalan yazımın dosyası silinir. Asıl adı vermek çağıranındır.
    """
    _kurtarma_basligi_denetle(recovery_header)
    manifesto = Manifesto(KAPSAM_TAM, tuple(_diskteki_hali(girdi, store_dir) for girdi in files))
    aad, muhurlu = _muhurle(database, manifesto.baytlar(), KAPSAM_TAM, public_key, recovery_header)
    target.parent.mkdir(parents=True, exist_ok=True)
    akis = yeni_yedek_dosyasi(target)
    try:
        with akis:
            akis.write(aad)
            akis.write(muhurlu)
            _dosya_bolumunu_yaz(akis, manifesto, store_dir)
            _diske_indir(akis)
        _dizini_esitle(target.parent)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return manifesto


# ---------------------------------------------------------------------------
# Okuma
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class KapBasligi:
    """Şifreli metinden önceki baytların çözülmeden okunan alanları."""

    kapsam: int
    kurtarma_basligi: bytes = field(repr=False)
    muhurlu_boy: int
    #: Şifreli metinden önceki bütün baytlar (AAD).
    aad: bytes = field(repr=False)

    @property
    def dosya_bolumu_konumu(self) -> int:
        """Mühürlü bölümün bittiği yer: tam yedekte dosya bölümü buradan başlar."""
        return len(self.aad) + self.muhurlu_boy


@dataclass(frozen=True)
class YedekIcerigi:
    """Mühürlü bölümün açılmış hâli: veritabanı baytları ve manifesto AYRI (modül başlığı)."""

    veritabani: bytes = field(repr=False)
    manifesto: Manifesto


def baslik_oku(akis: IO[bytes], toplam_boy: int) -> KapBasligi:
    """Akışın başından kabın başlığını okur; akış mühürlü bölümün başında kalır. ANAHTAR İSTEMEZ.

    Uzunluk alanları okumadan önce sınanır: bozuk bir dosya okuyucuyu büyük bir okumaya
    sürükleyemez. `toplam_boy` dosyanın boyudur: mühürlü bölüm sığmıyorsa kap kesiktir, yerel
    yedekte ardında bayt kalıyorsa uzatılmıştır. Tam yedeğin dosya bölümünü `dosya_bolumunu_oku`
    sınar.
    """
    sabit = akis.read(_FIXED_HEADER_BYTES)
    if sabit.startswith(DENEME_MAGIC):
        raise DenemeYedegiHatasi()
    if len(sabit) < _FIXED_HEADER_BYTES or not sabit.startswith(MAGIC):
        raise BackupCryptoError("Dosya geçerli bir OAB Defteri yedeği değil.")
    metadata_len = int.from_bytes(sabit[-_LENGTH_BYTES:], "big")
    if metadata_len > MAX_RECOVERY_HEADER_BYTES:
        raise BackupCryptoError(_BOZUK_BASLIK_ILETISI)
    kuyruk_boy = metadata_len + _KAPSAM_BYTES + _SEALED_LENGTH_BYTES
    kuyruk = akis.read(kuyruk_boy)
    if len(kuyruk) < kuyruk_boy:
        raise BackupCryptoError(_BOZUK_BASLIK_ILETISI)
    kapsam = kuyruk[metadata_len]
    muhurlu_boy = int.from_bytes(kuyruk[metadata_len + _KAPSAM_BYTES :], "big")
    baslik = KapBasligi(
        kapsam=kapsam,
        kurtarma_basligi=kuyruk[:metadata_len],
        muhurlu_boy=muhurlu_boy,
        aad=sabit + kuyruk,
    )
    fazlalik = toplam_boy - baslik.dosya_bolumu_konumu
    if (
        kapsam not in (KAPSAM_YEREL, KAPSAM_TAM)
        or not _EN_KISA_MUHURLU_BOY <= muhurlu_boy <= _AZAMI_MUHURLU_BOY
        or fazlalik < 0
        or (kapsam == KAPSAM_YEREL and fazlalik != 0)
    ):
        raise BackupCryptoError(_BOZUK_BASLIK_ILETISI)
    return baslik


def kap_basligi(container: bytes) -> KapBasligi:
    """Bellekteki kabın başlığı (`baslik_oku`)."""
    return baslik_oku(io.BytesIO(container), len(container))


def kap_basligini_oku(path: Path) -> KapBasligi:
    """Yedek dosyasının başlığı: dosyanın YALNIZ başı okunur, kurtarma anahtarı gerekmez.

    Yedek listesi her dosyanın başlığından kapsamı ve kurtarma anahtarının kimliğini okur, bunun
    için veritabanı belleğe alınmaz. Okuma hatası (`OSError`) çağırana geçer.
    """
    with path.open("rb") as dosya:
        return baslik_oku(dosya, os.fstat(dosya.fileno()).st_size)


def embedded_recovery_metadata(container: bytes) -> bytes:
    """Yedekteki parola KDF/sarmal bilgisini geri yükleme aracına verir."""
    return kap_basligi(container).kurtarma_basligi


def read_embedded_recovery_metadata(path: Path) -> bytes:
    """Yedek dosyasının gömülü kurtarma başlığı (`kap_basligini_oku`)."""
    return kap_basligini_oku(path).kurtarma_basligi


def _acik_icerigi_ayir(acik: bytes, kapsam: int) -> YedekIcerigi:
    db_boy = int.from_bytes(acik[:_DB_LENGTH_BYTES], "big")
    db_sonu = _DB_LENGTH_BYTES + db_boy
    if db_sonu >= len(acik):
        raise BackupCryptoError(_BOZUK_ICERIK_ILETISI)
    return YedekIcerigi(
        veritabani=acik[_DB_LENGTH_BYTES:db_sonu],
        manifesto=manifesto_ayristir(acik[db_sonu:], kapsam=kapsam),
    )


def muhurlu_bolumu_ac(akis: IO[bytes], baslik: KapBasligi, data_key: bytes) -> YedekIcerigi:
    """Mühürlü bölümü okuyup çözer; akış başlığın hemen ardında olmalıdır.

    Akış mühürlü bölümün sonunda kalır: tam yedekte `dosya_bolumunu_oku` buradan sürer.
    Kimlik doğrulaması başarısızsa `YedekAnahtariHatasi`.
    """
    onek = len(MAGIC)
    ephemeral = X25519PublicKey.from_public_bytes(baslik.aad[onek : onek + _PUBLIC_BYTES])
    nonce_start = onek + _PUBLIC_BYTES
    nonce = baslik.aad[nonce_start : nonce_start + _NONCE_BYTES]
    muhurlu = akis.read(baslik.muhurlu_boy)
    try:
        aes_key = _hkdf(
            private_key_from_data_key(data_key).exchange(ephemeral),
            info=_ENVELOPE_INFO,
        )
        acik = AESGCM(aes_key).decrypt(nonce, muhurlu, baslik.aad)
    except Exception as exc:  # InvalidTag ayrıntısı kullanıcıya/saldırgana sızdırılmaz.
        raise YedekAnahtariHatasi(
            "Yedek anahtarı yanlış veya dosyanın bütünlüğü bozulmuş."
        ) from exc
    return _acik_icerigi_ayir(acik, baslik.kapsam)


class DosyaBolumuGirdisi:
    """Dosya bölümünün bir girdisi: manifestodaki kaydı ve şifreli gövdesi.

    Gövde `parcalar()` ile parça parça alınır; alınmayan kısmı okuyucu sonraki girdiye geçerken
    atlar. Girdi yalnız `dosya_bolumunu_oku` bir sonraki adıma geçene dek geçerlidir.
    """

    def __init__(self, girdi: ManifestoGirdisi, akis: IO[bytes]) -> None:
        self.girdi = girdi
        self._akis = akis
        self._kalan = girdi.sifreli_boy

    def parcalar(self) -> Iterator[bytes]:
        """`ODDOSYA` baytları, en çok `KOPYA_PARCASI` boyunda; gövde kesikse `DosyaBolumuHatasi`."""
        while self._kalan:
            parca = self._akis.read(min(KOPYA_PARCASI, self._kalan))
            if not parca:
                raise DosyaBolumuHatasi()
            self._kalan -= len(parca)
            yield parca

    def _atla(self) -> None:
        for _parca in self.parcalar():
            pass


def dosya_bolumunu_oku(akis: IO[bytes], manifesto: Manifesto) -> Iterator[DosyaBolumuGirdisi]:
    """Dosya bölümünü girdi girdi verir; akış bölümün başında olmalıdır.

    Her girdinin başı manifestonun sıradaki kaydıyla bayt bayt eşit olmalıdır: ad (sıra ve
    "manifestoda olmayan girdi" tek denetimdir) ve boy. Boy gövdeden önce sınandığı için bozuk boy
    alanı büyük bir okumaya yol açamaz. Bitiş işareti gelmeli, ardında bayt kalmamalıdır. Bunların
    hepsi KAP düzeyindedir (`DosyaBolumuHatasi`) ve iterasyon bitmeden bölüm sağlam sayılmaz.
    Eklerin içeriğini bu işlev sınamaz: özet açık içeriğindir (`ek_denetle`).
    """
    for beklenen in manifesto.tasinanlar:
        bas = akis.read(_GIRDI_BASI_BAYT)
        if bas != beklenen.ad.encode("ascii") + beklenen.sifreli_boy.to_bytes(
            _DOSYA_BOY_BAYT, "big"
        ):
            raise DosyaBolumuHatasi()
        girdi = DosyaBolumuGirdisi(beklenen, akis)
        yield girdi
        girdi._atla()
    if akis.read(_GIRDI_BASI_BAYT) != DOSYA_BOLUMU_SONU or akis.read(1):
        raise DosyaBolumuHatasi()


def decrypt_bytes(container: bytes, data_key: bytes) -> YedekIcerigi:
    """Bellekteki kabı çözer: başlık, mühürlü bölüm ve tam yedekte dosya bölümünün yapısı.

    Kimlik doğrulaması başarısızsa `YedekAnahtariHatasi`; öteki `BackupCryptoError`'lar yedeğin
    kendisinin bozuk olduğunu söyler. Eklerin içeriği geri yüklemede sınanır.
    """
    akis = io.BytesIO(container)
    baslik = baslik_oku(akis, len(container))
    icerik = muhurlu_bolumu_ac(akis, baslik, data_key)
    if baslik.kapsam == KAPSAM_TAM:
        for _girdi in dosya_bolumunu_oku(akis, icerik.manifesto):
            pass
    return icerik
