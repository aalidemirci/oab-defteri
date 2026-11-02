"""Geri yükleme yetkisi (tasarım §4.4.4 "Geri yükleme yetkisi", §10.6, §14 F1b kapısı; plan F1b-2).

Geri yükleme yalnız KURTARMA ANAHTARIYLA ya da rolü program yöneticisi olan hesabın PAROLASIYLA
yapılır. Uygulama içi yol rol kapısından geçer (`RolMiddleware`: açık oturumda yalnız program
yöneticisi) ve servis parola yolunda ayrıca denetler: parolası verilen hesap isteğin yazarının
hesabıdır ve rolü program yöneticisidir (`live_restore` modül başlığı "YETKİ"). Kurtarma anahtarı
yolunda rol denetimi yoktur: güvenlik dosyası kayıp kilidinden çıkış, oturumsuz da açık kalmış
bir organ oturumuyla da açıktır.

`test_yonetici_olmayan_hesapla_geri_yukle_reddedilir` parametrelidir: konsol kolu
(`--geri-yukle`, `restore_backup`; ORM'siz hesap denetimi) aynı teste eklenir.

Testler ORM'e dokunmaz (`live_restore` testleriyle aynı kurgu): hedef veritabanı geçici bir
dosyadır, yedek bu kurulumun DEK'iyle alınır.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Any, cast

import pytest
from desktop.backup_crypto import (
    encrypt_bytes,
    private_key_from_data_key,
    recovery_header_from_state,
)
from django.conf import settings
from django.db import connections
from rest_framework.test import APIClient

from apps.okul import restart_gate
from apps.okul.oturum import Yazar, yazar_olarak
from apps.okul.services import app_password, live_restore
from apps.okul.tests.hesap_ortak import durum_yaz
from conftest import TEST_DEK, TEST_KURTARMA_ANAHTARI, TEST_PAROLA, oturumu_ac_test
from shared import bakim
from shared.exceptions import ROL_YETKISIZ_MESAJI, RolYetkisiz

GERI_YUKLE_URL = "/api/v1/backups/restore/"
YEDEK = "gunluk-2026-10-31.odbak"
#: Uydurma muhasip hesabı: güvenlik dosyasında program yöneticisinin parolasıyla açılan bir
#: sarmalı vardır — rol denetimi olmasaydı parola yolu bu hesapla geri yüklerdi.
MUHASIP_ID = "0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f"


@pytest.fixture
def ortam(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    """Hedef veritabanı geçici dosya; yedek klasöründe bu kurulumun DEK'iyle bir yedek."""
    db = tmp_path / "canli" / "db.sqlite3"
    db.parent.mkdir()
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(db))
    # Test veritabanı bellek içi olabilir; takas öncesi kapatma onu yok ederdi.
    monkeypatch.setattr(connections, "close_all", lambda: None)
    db.write_bytes(_sqlite(tmp_path, "eski"))
    yedekler = app_password.backup_dir()
    yedekler.mkdir(parents=True, exist_ok=True)
    yeni = _sqlite(tmp_path, "yeni")
    durum = app_password.read_state() or {}
    baslik = json.dumps(recovery_header_from_state(durum), ensure_ascii=False).encode("utf-8")
    kapsayici = encrypt_bytes(
        yeni, private_key_from_data_key(TEST_DEK).public_key(), recovery_header=baslik
    )
    (yedekler / YEDEK).write_bytes(cast("bytes", kapsayici))
    yield {"db": db, "eski": db.read_bytes(), "yeni": yeni}


def _sqlite(dizin: Path, isaret: str) -> bytes:
    yol = dizin / f"kaynak-{isaret}.sqlite3"
    with closing(sqlite3.connect(yol)) as baglanti:
        baglanti.execute("CREATE TABLE kayit (deger TEXT)")
        baglanti.execute("INSERT INTO kayit VALUES (?)", (isaret,))
        baglanti.commit()
    return yol.read_bytes()


def _muhasip_sarmali_ekle() -> None:
    """Güvenlik dosyasına program yöneticisinin sarmalının kopyasını muhasip adıyla ekler."""
    durum = app_password.read_state() or {}
    kopya = dict(durum["hesaplar"][0])
    kopya.update({"id": MUHASIP_ID, "tanitici": "muhasip"})
    durum["hesaplar"].append(kopya)
    durum_yaz(durum)


def _degismedi(ortam: dict[str, Any]) -> None:
    """Ret: hedefe dokunulmadı, kapı kurulmadı, bakım kapısı açık, kenara alma yok."""
    assert ortam["db"].read_bytes() == ortam["eski"]
    assert restart_gate.restart_required() is False
    assert bakim.KAPI.bakimda is False
    assert not list(ortam["db"].parent.glob("db-onceki-*"))


@pytest.mark.parametrize("kol", ["uygulama_ici"])
def test_yonetici_olmayan_hesapla_geri_yukle_reddedilir(kol: str, ortam: dict[str, Any]) -> None:
    """Tasarım §10.6 ve §14 F1b kapısı: "yönetici olmayan hesapla geri yükleme reddedilir"."""
    _muhasip_sarmali_ekle()
    assert kol == "uygulama_ici"

    # 1. Açık muhasip oturumu: rol kapısı (uç katmanı) 403.
    oturumu_ac_test(MUHASIP_ID, tanitici="muhasip", rol="muhasip")
    yanit = APIClient().post(
        GERI_YUKLE_URL, {"name": YEDEK, "password": TEST_PAROLA}, format="json"
    )
    assert yanit.status_code == 403
    assert yanit.json()["code"] == "rol_yetkisiz"
    _degismedi(ortam)

    # 2. Servis kapısı (derin savunma): muhasibin yazarıyla parola yolu.
    with yazar_olarak(Yazar(hesap_id=MUHASIP_ID, rol="muhasip")), pytest.raises(RolYetkisiz):
        live_restore.restore_and_require_restart(name=YEDEK, password=TEST_PAROLA)
    _degismedi(ortam)

    # 3. Program yöneticisi oturumunda başka hesabın (muhasibin) parolası geçmez: 400.
    oturumu_ac_test()
    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {"name": YEDEK, "hesap": "muhasip", "password": TEST_PAROLA},
        format="json",
    )
    assert yanit.status_code == 400
    assert yanit.json()["message"] == live_restore.PAROLA_YALNIZ_OTURUM_HESABI
    with pytest.raises(live_restore.LiveRestoreError):
        live_restore.restore_and_require_restart(name=YEDEK, hesap=MUHASIP_ID, password=TEST_PAROLA)
    _degismedi(ortam)

    # 4. Oturum yokken (yazar yok) parola yolu reddedilir.
    with yazar_olarak(None), pytest.raises(live_restore.LiveRestoreError):
        live_restore.restore_and_require_restart(name=YEDEK, password=TEST_PAROLA)
    _degismedi(ortam)


def test_program_yoneticisi_kendi_parolasiyla_geri_yukler(ortam: dict[str, Any]) -> None:
    """Olumlu yarı: hesap verilmezse ya da kendi tanıtıcısıyla oturumdaki hesabın parolası."""
    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {"name": YEDEK, "hesap": "yonetici", "password": TEST_PAROLA},
        format="json",
    )
    assert yanit.status_code == 200, yanit.json()
    assert ortam["db"].read_bytes() == ortam["yeni"]


def test_rol_yetkisiz_ileti_sabittir(ortam: dict[str, Any]) -> None:
    oturumu_ac_test(MUHASIP_ID, tanitici="muhasip", rol="muhasip")
    with yazar_olarak(Yazar(hesap_id=MUHASIP_ID, rol="muhasip")):
        with pytest.raises(RolYetkisiz, match=ROL_YETKISIZ_MESAJI):
            live_restore.restore_and_require_restart(name=YEDEK, password=TEST_PAROLA)
    # Kurtarma anahtarı yolunda rol denetimi yoktur (konsolla aynı; anahtarın kendisi yetkidir).
    with yazar_olarak(Yazar(hesap_id=MUHASIP_ID, rol="muhasip")):
        sonuc = live_restore.restore_and_require_restart(
            name=YEDEK, recovery_key=TEST_KURTARMA_ANAHTARI
        )
    assert sonuc["restart_required"] is True
    assert ortam["db"].read_bytes() == ortam["yeni"]


# ============================================================ kayıp kilidinden çıkış


@pytest.mark.django_db
@pytest.mark.parametrize("oturum", ["oturumsuz", "muhasip_oturumu"])
def test_kayip_kilidinde_kurtarma_anahtariyla_geri_yukleme(
    oturum: str, ortam: dict[str, Any], parmak_izi_yazili: str
) -> None:
    """Güvenlik dosyası kayıpken çıkış yolu açık kalır (tasarım §4.3 tehdit 8, §4.4.4; plan
    F1b-1 "Kayıp dosya kipinde yedekten geri yükleme yalnız kurtarma anahtarı ister"): oturum
    yokken de, açık kalmış bir muhasip oturumuyla da kurtarma anahtarıyla geri yükleme başarılı.
    Rol kapısı kayıp kipinde kesmez, servis kurtarma yolunda rol sormaz."""
    if oturum == "muhasip_oturumu":
        oturumu_ac_test(MUHASIP_ID, tanitici="muhasip", rol="muhasip")
    else:
        app_password.lock()
    app_password.state_path().unlink()
    client = APIClient()
    assert client.get("/api/v1/security/session/").json()["durum"] == "guvenlik_dosyasi_kayip"

    yanit = client.post(
        GERI_YUKLE_URL, {"name": YEDEK, "recovery_key": TEST_KURTARMA_ANAHTARI}, format="json"
    )

    assert yanit.status_code == 200, yanit.json()
    assert yanit.json()["state_written"] is True
    assert ortam["db"].read_bytes() == ortam["yeni"]
    assert app_password.read_state() is not None


@pytest.mark.django_db
def test_kayip_kilidinde_oturumsuz_parola_yolu_reddedilir(
    ortam: dict[str, Any], parmak_izi_yazili: str
) -> None:
    """Oturum yokken parola yolu reddedilir: ileti kurtarma anahtarını gösterir."""
    app_password.lock()
    app_password.state_path().unlink()
    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {"name": YEDEK, "hesap": "yonetici", "password": TEST_PAROLA},
        format="json",
    )
    assert yanit.status_code == 400
    assert yanit.json()["message"] == live_restore.PAROLA_YOLU_OTURUM_ISTER
    _degismedi(ortam)
