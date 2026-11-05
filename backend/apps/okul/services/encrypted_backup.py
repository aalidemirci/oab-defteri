"""Kullanıcının istediğinde indirebildiği şifreli yedek.

Başlık TK10 izdüşümüdür (`backup_crypto.usable_recovery_header`): yalnız kurtarma bölümü ve
kurtarma anahtarının kimliği; hesap sarmalları yedeğe girmez (tasarım §4.4.4). Başlıksız yedek
üretilmez (plan F1b-3 "Kap ve manifesto"): güvenlik dosyası kullanılamıyorsa yedek verilmez.

KAPSAM (plan F1b-3 "Sıra"): bu alt commit'te yedek hâlâ bellekte kurulur ve yerel kapsamlıdır;
yerel yedekler gibi görüntünün manifestosunu taşır (`backup.goruntu_ve_manifesto`).
Tam yedeğin programca kaydedilmesi ve bellek içi indirmenin kalkması sonraki alt commit'tedir (d).

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

from desktop.backup import goruntu_ve_manifesto
from desktop.backup_crypto import encrypt_bytes, load_public_key, usable_recovery_header
from django.conf import settings
from django.db import transaction

from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AuditAction
from apps.okul.services import app_password, dis_yedek

#: Kurtarma başlığı kullanılamıyor (başlıksız yedek üretilmez; modül başlığı).
GUVENLIK_DOSYASI_OKUNAMIYOR = "Güvenlik dosyası okunamıyor; şifreli yedek alınmadı."


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
    baslik = usable_recovery_header(data_dir)
    if baslik is None:
        raise EncryptedBackupError(GUVENLIK_DOSYASI_OKUNAMIYOR)

    try:
        public_key = load_public_key(data_dir)
        veritabani, manifesto = goruntu_ve_manifesto(database_path)
        encrypted = encrypt_bytes(
            veritabani,
            public_key,
            recovery_header=baslik,
            manifesto=manifesto,
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
