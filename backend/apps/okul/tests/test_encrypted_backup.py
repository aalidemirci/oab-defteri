from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest import mock

import pytest
from desktop.backup_crypto import MAGIC, decrypt_bytes, ensure_public_config
from django.http import StreamingHttpResponse
from rest_framework.test import APIClient

from apps.okul import denetim_izi
from apps.okul.models import AuditTrail
from apps.okul.services import app_password, dis_yedek, encrypted_backup
from conftest import TEST_HESAP_ID


@pytest.mark.django_db
def test_veritabani_ramde_sifrelenerek_odbak_uretilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    database = data_dir / "db.sqlite3"
    secret = "ogrenci-kisisel-verisi"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE kayit (deger TEXT)")
        connection.execute("INSERT INTO kayit VALUES (?)", (secret,))

    data_key = b"\x42" * 32
    ensure_public_config(data_dir, data_key)
    monkeypatch.setattr(app_password, "state_path", lambda: data_dir / "guvenlik.json")
    monkeypatch.setattr(app_password, "is_locked", lambda: False)
    # Görüntü yalnız bu dosyadan alınır; iz satırı test veritabanının açık bağlantısına
    # yazılır (ayarın kendisi değişmez, bağlantı yeniden kurulmaz).
    monkeypatch.setattr(
        encrypted_backup, "settings", SimpleNamespace(DATABASES={"default": {"NAME": database}})
    )

    content, filename = encrypted_backup.create_encrypted_backup()

    assert filename.endswith(".odbak")
    assert content.startswith(MAGIC)
    assert secret.encode() not in content
    restored = decrypt_bytes(content, data_key)
    assert restored.startswith(b"SQLite format 3")
    assert secret.encode() in restored
    # Kullanıcının istediği yedek oturumdaki hesabın `YEDEK` satırıdır (tasarım §4.6.3).
    satir = AuditTrail.objects.get()
    assert (satir.action, satir.model, satir.object_id) == (
        "YEDEK",
        denetim_izi.YEDEK_DOSYASI,
        filename,
    )
    assert str(satir.account_id) == TEST_HESAP_ID
    assert satir.key_mode == "ACIK"


@pytest.mark.django_db
def test_iz_yazilamazsa_yedek_verilmez(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """İzsiz yedek yoktur: satır yazılamazsa indirme verilmez, dış yedek tarihi de yazılmaz."""
    database = tmp_path / "db.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE kayit (deger TEXT)")
    monkeypatch.setattr(
        encrypted_backup, "settings", SimpleNamespace(DATABASES={"default": {"NAME": database}})
    )
    indirmeler: list[object] = []
    monkeypatch.setattr(dis_yedek, "indirme_kaydet", indirmeler.append)

    def yazilamadi(*_a: object, **_k: object) -> None:
        raise denetim_izi.IzYazilamadi("deneme")

    monkeypatch.setattr(denetim_izi, "olay", yazilamadi)
    with pytest.raises(denetim_izi.IzYazilamadi):
        encrypted_backup.create_encrypted_backup()
    assert indirmeler == []
    assert AuditTrail.objects.count() == 0


def test_kilitliyken_yedek_olusturulmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_password, "is_locked", lambda: True)

    with pytest.raises(encrypted_backup.EncryptedBackupError, match="kilidi açın"):
        encrypted_backup.create_encrypted_backup()


def test_indirme_ucu_sifreli_dosyayi_ek_olarak_dondurur() -> None:
    with mock.patch(
        "apps.okul.views.encrypted_backup_service.create_encrypted_backup",
        return_value=(b"ODBAK-encrypted", "yedek.odbak"),
    ):
        response = APIClient().post("/api/v1/backups/encrypted/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/octet-stream"
    assert "yedek.odbak" in response["Content-Disposition"]
    assert isinstance(response, StreamingHttpResponse)
    content = cast(Iterable[bytes], response.streaming_content)
    assert b"".join(content) == b"ODBAK-encrypted"
