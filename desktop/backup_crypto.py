"""OAB Defteri yedek kapsayıcısı.

Yedekleme için asimetrik zarf şifrelemesi kullanılır: veri anahtarından türetilen
X25519 özel anahtar yalnız bir hesabın parolasıyla kilit açıldığında elde edilebilir;
açık anahtar ise başlangıçta parola sorulmadan yedek alınabilmesi için diskte tutulur.
Yedek içeriği AES-256-GCM ile hem şifrelenir hem de doğrulanır.

Yedeğin kurtarma başlığı (tasarım TK10, §4.4.4) `guvenlik.json`'un yalnız kurtarma
bölümünü ve kurtarma anahtarının kimliğini (no, tarih) taşır; hesap sarmalları
yedeğe girmez (`recovery_header_from_state`). Aynı bilgisayarda geri yükleme güncel
`guvenlik.json` ve bir hesabın parolasıyla, yeni bilgisayarda kurtarma anahtarıyla
yapılır.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAGIC = b"ODBAK\x02"
CONFIG_FILE_NAME = "yedekleme.json"
# Kurtarma başlığının kaynağı (`apps.okul.services.app_password.STATE_FILE_NAME`
# ile aynı ad; masaüstü katmanı backend'i import etmez).
SECURITY_STATE_FILE_NAME = "guvenlik.json"
BACKUP_SUFFIX = ".odbak"
_NONCE_BYTES = 12
_PUBLIC_BYTES = 32
_LENGTH_BYTES = 4
_PRIVATE_INFO = b"OABDefteri/backup/private/v1"
_ENVELOPE_INFO = b"OABDefteri/backup/envelope/v1"


class BackupCryptoError(ValueError):
    """Bozuk/uyumsuz yedek veya anahtar hatası."""


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
#: kurulur (plan F1b-1 "Eski veri").
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
    durdururdu.
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
    """Ham `guvenlik.json` baytlarını ayrıştırır; kullanılamazsa None (hata değil)."""
    try:
        data: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
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


def recovery_metadata(data_dir: Path) -> bytes:
    """Kişisel veri ve hesap sarmalı içermeyen kurtarma başlığı (TK10); yoksa b"".

    Önce güncel `guvenlik.json`, o kullanılamazsa en yeni `guvenlik-arsiv-*`
    kopyası denenir. Dönen baytlar dosyanın kendisi değil izdüşümüdür
    (`recovery_header_from_state`).
    """
    current = data_dir / SECURITY_STATE_FILE_NAME
    candidates = [current] if current.is_file() else []
    candidates.extend(sorted(data_dir.glob("guvenlik-arsiv-*.json"), reverse=True))
    for aday in candidates:
        try:
            raw = aday.read_bytes()
        except OSError:
            continue
        baslik = recovery_header_from_state(parse_security_state(raw))
        if baslik is not None:
            return _header_bytes(baslik)
    return b""


def encrypt_bytes(
    plaintext: bytes,
    public_key: X25519PublicKey,
    *,
    recovery_header: bytes = b"",
) -> bytes:
    ephemeral = X25519PrivateKey.generate()
    ephemeral_public = ephemeral.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    aes_key = _hkdf(ephemeral.exchange(public_key), info=_ENVELOPE_INFO)
    nonce = os.urandom(_NONCE_BYTES)
    if len(recovery_header) > 1_000_000:
        raise BackupCryptoError("Yedek kurtarma başlığı beklenenden büyük.")
    header = (
        MAGIC
        + ephemeral_public
        + nonce
        + len(recovery_header).to_bytes(_LENGTH_BYTES, "big")
        + recovery_header
    )
    return header + AESGCM(aes_key).encrypt(nonce, plaintext, header)


def encrypt_to_path(
    plaintext: bytes,
    target: Path,
    public_key: X25519PublicKey,
    *,
    recovery_header: bytes = b"",
) -> None:
    """Şifreli kapsayıcıyı atomik yazar."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.unlink(missing_ok=True)
    try:
        temp.write_bytes(encrypt_bytes(plaintext, public_key, recovery_header=recovery_header))
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)


def embedded_recovery_metadata(container: bytes) -> bytes:
    """Yedekteki parola KDF/sarmal bilgisini geri yükleme aracına verir."""
    fixed_len = len(MAGIC) + _PUBLIC_BYTES + _NONCE_BYTES + _LENGTH_BYTES
    if len(container) <= fixed_len or not container.startswith(MAGIC):
        raise BackupCryptoError("Dosya geçerli bir OAB Defteri yedeği değil.")
    length_start = fixed_len - _LENGTH_BYTES
    metadata_len = int.from_bytes(container[length_start:fixed_len], "big")
    end = fixed_len + metadata_len
    if end >= len(container):
        raise BackupCryptoError("Yedek başlığı bozuk veya eksik.")
    return container[fixed_len:end]


def decrypt_bytes(container: bytes, data_key: bytes) -> bytes:
    """Geri yükleme/test aracı; kimlik doğrulaması başarısızsa açık hata verir."""
    fixed_len = len(MAGIC) + _PUBLIC_BYTES + _NONCE_BYTES + _LENGTH_BYTES
    if len(container) <= fixed_len or not container.startswith(MAGIC):
        raise BackupCryptoError("Dosya geçerli bir OAB Defteri yedeği değil.")
    offset = len(MAGIC)
    ephemeral = X25519PublicKey.from_public_bytes(container[offset : offset + _PUBLIC_BYTES])
    nonce_start = offset + _PUBLIC_BYTES
    nonce_end = nonce_start + _NONCE_BYTES
    nonce = container[nonce_start:nonce_end]
    metadata_len = int.from_bytes(container[nonce_end:fixed_len], "big")
    header_len = fixed_len + metadata_len
    if header_len >= len(container):
        raise BackupCryptoError("Yedek başlığı bozuk veya eksik.")
    aes_key = _hkdf(
        private_key_from_data_key(data_key).exchange(ephemeral),
        info=_ENVELOPE_INFO,
    )
    try:
        return AESGCM(aes_key).decrypt(nonce, container[header_len:], container[:header_len])
    except Exception as exc:  # InvalidTag ayrıntısı kullanıcıya/saldırgana sızdırılmaz.
        raise BackupCryptoError("Yedek anahtarı yanlış veya dosyanın bütünlüğü bozulmuş.") from exc
