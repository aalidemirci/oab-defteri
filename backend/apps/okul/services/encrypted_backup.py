"""Kullanıcının istediğinde indirebildiği şifreli SQLite yedeği.

Başlık TK10 izdüşümüdür (`backup_crypto.recovery_metadata`): yalnız kurtarma bölümü ve
kurtarma anahtarının kimliği; hesap sarmalları yedeğe girmez (tasarım §4.4.4).

DENETİM İZİ (tasarım §4.6.3 `YEDEK`; plan F1b-1 alt commit c): kilit açıkken alınan yedek
oturumdaki hesabın `YEDEK` satırıdır (açık kip; nesne `yedek.dosya`, kimliği dosyanın
adı). Satır yedek şifrelendikten SONRA, indirme verilmeden ÖNCE kendi işleminde yazılır:
yazılamazsa yedek verilmez (izsiz yedek yoktur). Yedek görüntüsü satırdan önce
alındığı için yedeğin içinde kendi `YEDEK` satırı yoktur. Açılıştaki günlük ve göç öncesi
yedekler kilitli kipte, masaüstü kancası üzerinden yazılır (§4.6.3).

YETKİ (tasarım §4.4.2 Güvenlik satırı "yedek indirme"): yalnız program yöneticisi. Rol
kapısının ardından servis de isteğin yazarının rolünü yetki kapısına sorar (`RolYetkisiz`,
403); ret görüntü alınmadan verilir.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from desktop.backup import database_snapshot
from desktop.backup_crypto import encrypt_bytes, load_public_key, recovery_metadata
from django.conf import settings
from django.db import transaction

from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AuditAction
from apps.okul.services import app_password, dis_yedek


class EncryptedBackupError(ValueError):
    """Kullanıcıya gösterilebilen yedek oluşturma hatası."""


def create_encrypted_backup() -> tuple[bytes, str]:
    """Tutarlı veritabanı görüntüsünü RAM'de şifreleyip indirmeye hazırlar."""
    if app_password.is_locked():
        raise EncryptedBackupError("Şifreli yedek oluşturmak için önce hesabınızla kilidi açın.")
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.YEDEK_INDIRME)

    data_dir = app_password.state_path().parent
    database_path = Path(str(settings.DATABASES["default"]["NAME"]))
    if not database_path.is_file():
        raise EncryptedBackupError("Yedeklenecek veritabanı bulunamadı.")

    try:
        public_key = load_public_key(data_dir)
        encrypted = encrypt_bytes(
            database_snapshot(database_path),
            public_key,
            recovery_header=recovery_metadata(data_dir),
        )
    except ValueError as exc:
        raise EncryptedBackupError(str(exc)) from exc
    except (OSError, sqlite3.Error) as exc:
        raise EncryptedBackupError("Şifreli yedek oluşturulamadı.") from exc

    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")
    filename = f"oab-defteri-yedek-{timestamp}.odbak"
    with transaction.atomic():
        denetim_izi.olay(AuditAction.YEDEK, model=denetim_izi.YEDEK_DOSYASI, object_id=filename)
    # Tasarım §16 R6: dış yedek hatırlatmasının saati bu indirmeyle sıfırlanır.
    # Kayıt veri dizinindeki dosyadadır ve hata yükseltmez (`dis_yedek` modül başlığı).
    dis_yedek.indirme_kaydet()
    return encrypted, filename
