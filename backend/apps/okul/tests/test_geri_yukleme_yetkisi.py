"""Geri yükleme yetkisi (tasarım §4.4.4 "Geri yükleme yetkisi", §10.6, §14 F1b kapısı; plan F1b-2).

Geri yükleme yalnız KURTARMA ANAHTARIYLA ya da rolü program yöneticisi olan hesabın PAROLASIYLA
yapılır. Uygulama içi yol rol kapısından geçer (`RolMiddleware`: açık oturumda yalnız program
yöneticisi) ve servis parola yolunda ayrıca denetler: parolası verilen hesap isteğin yazarının
hesabıdır ve rolü program yöneticisidir (`live_restore` modül başlığı "YETKİ"). Kurtarma anahtarı
yolunda rol denetimi yoktur: güvenlik dosyası kayıp kilidinden çıkış, oturumsuz da açık kalmış
bir organ oturumuyla da açıktır.

Konsol yolu (`--geri-yukle`, `restore_backup`) Django ara katmanından geçmez; denetim üç kapının
ortak çekirdeğindedir (`backup_restore.restore_database` → `geri_yukleme_yetkisi`, ORM'siz):
parola doğrulandıktan sonra ve hiçbir dosyaya dokunulmadan önce, güncel veritabanında, o
okunamıyorsa yedeğin görüntüsünde. `test_yonetici_olmayan_hesapla_geri_yukle_reddedilir` iki
kolludur (`uygulama_ici`, `konsol`); öteki testler çekirdeğin kabul ve ret koşullarını, geri
düşüşü, ORM'le biçim eşitliğini ve retten sonra dosyaların değişmediğini sınar.

Testler (biçim eşitliği testi dışında) ORM'e dokunmaz: hedef veritabanı geçici bir dosyadır,
yedek bu kurulumun DEK'iyle alınır; okul kartı ve hesap satırları ORM'siz kurulur
(`geri_yukleme_ortak`). Adlar ve kimlikler uydurmadır.
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import sqlite3
import stat
import uuid
from collections.abc import Callable, Iterator
from contextlib import closing
from dataclasses import replace
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

import pytest
from desktop import restore as restore_mod
from desktop.backup_crypto import (
    config_path,
    encrypt_bytes,
    private_key_from_data_key,
    recovery_header_from_state,
)
from desktop.errors import EXIT_RESTORE_FAILED
from desktop.main import build_parser
from desktop.paths import VERSION_STAMP_FILE_NAME, AppPaths
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, connections
from rest_framework.test import APIClient

from apps.okul import restart_gate
from apps.okul.models import Account, AccountRole, AccountStatus
from apps.okul.oturum import Yazar, yazar_olarak
from apps.okul.services import (
    app_password,
    backup_restore,
    geri_yukleme_notu,
    geri_yukleme_yetkisi,
    live_restore,
)
from apps.okul.services.geri_yukleme_yetkisi import (
    ILETI_DURUM,
    ILETI_MUHUR,
    ILETI_ROL,
    KAYNAK_GORUNTU,
    KAYNAK_GUNCEL,
    YetkiReddi,
)
from apps.okul.tests.geri_yukleme_ortak import (
    ACILIS,
    HesapSatiri,
    duz_sqlite,
    muhur,
    program_disindan,
    yetkili_sqlite,
)
from apps.okul.tests.hesap_ortak import bagsiz_sarmal, durum_yaz
from conftest import (
    TEST_DEK,
    TEST_HESAP_ID,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
    TEST_TANITICI,
    oturumu_ac_test,
)
from shared import bakim, crypto, kanonik, sqlite_adres
from shared.exceptions import ROL_YETKISIZ_MESAJI, RolYetkisiz

GERI_YUKLE_URL = "/api/v1/backups/restore/"
YEDEK = "gunluk-2026-10-31.odbak"
#: Uydurma muhasip hesabı: güvenlik dosyasında program yöneticisinin parolasıyla açılan, KENDİ
#: kimliğine bağlı bir sarmalı vardır — rol denetimi olmasaydı parola yolu bu hesapla geri
#: yüklerdi.
MUHASIP_ID = "0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f"
#: Muhasibin KENDİ (uydurma) parolası: sarmal kimliği testlerinde sarmalı bununla kurulur.
MUHASIP_PAROLASI = "Uydurma-Muhasip-Parolasi-2"
YONETICI = HesapSatiri(TEST_HESAP_ID, TEST_TANITICI)
MUHASIP = HesapSatiri(MUHASIP_ID, "muhasip", role="muhasip")
#: Yedekten SONRA açılmış ikinci program yöneticisi (tasarım §4.4.4 `yonetici-2`; uydurma).
YONETICI_2 = HesapSatiri("5a7b9c1d-2e3f-4a5b-8c6d-7e8f9a0b1c2d", "yonetici-2")
KAPANIS = ACILIS + timedelta(days=3)


def _yedek(icerik: bytes) -> bytes:
    """Bu kurulumun DEK'iyle, güncel kurtarma başlığını gömen şifreli yedek."""
    durum = app_password.read_state() or {}
    baslik = json.dumps(recovery_header_from_state(durum), ensure_ascii=False).encode("utf-8")
    acik = private_key_from_data_key(TEST_DEK).public_key()
    return cast("bytes", encrypt_bytes(icerik, acik, recovery_header=baslik))


@pytest.fixture
def ortam(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    """Güncel veritabanı ve yedek: ikisinde de mühürlü program yöneticisi ve muhasip satırı."""
    db = tmp_path / "canli" / "db.sqlite3"
    db.parent.mkdir()
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(db))
    # Test veritabanı bellek içi olabilir; takas öncesi kapatma onu yok ederdi.
    monkeypatch.setattr(connections, "close_all", lambda: None)
    yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[YONETICI, MUHASIP], isaret="eski")
    yeni = yetkili_sqlite(
        tmp_path / "kaynak-yeni.sqlite3", dek=TEST_DEK, hesaplar=[YONETICI, MUHASIP], isaret="yeni"
    )
    yedekler = app_password.backup_dir()
    yedekler.mkdir(parents=True, exist_ok=True)
    (yedekler / YEDEK).write_bytes(_yedek(yeni))
    yield {"db": db, "eski": db.read_bytes(), "yeni": yeni, "yedek": yedekler / YEDEK}


def _sarmal_ekle(hesap: HesapSatiri, *, parola: str = TEST_PAROLA) -> None:
    """Güvenlik dosyasına bu hesabın KENDİ kimliğine bağlı sarmalını ekler (programın yazıcısı,
    `_account_wrap`). Varsayılan parola program yöneticisininkidir (tuz ayrıdır). Yöneticinin
    sarmalını kopyalayıp kimliğini değiştirmek artık işe yaramaz: sarmal kimliğe bağlıdır."""
    durum = app_password.read_state() or {}
    durum["hesaplar"].append(
        app_password._account_wrap(
            TEST_DEK,
            hesap_id=hesap.id,
            tanitici=hesap.login_name,
            password=parola,
            kdf=app_password._kdf_of(durum),
        )
    )
    durum_yaz(durum)


def _muhasip_sarmali_ekle() -> None:
    """Güvenlik dosyasına muhasibin, program yöneticisinin parolasıyla açılan sarmalını ekler."""
    _sarmal_ekle(MUHASIP)


def _yan_dosyalar(db: Path) -> set[str]:
    return {f"{db.name}-wal", f"{db.name}-shm"}


def _anlik(db: Path) -> dict[str, Any]:
    """Retten sonra değişmemesi gereken her şey.

    Salt okunur denetimin bedeli (`geri_yukleme_yetkisi` başlığı; F1b-2 ekleri): program
    kapalıyken 0 baytlık bir `-wal` ve bir `-shm` oluşabilir. Bu yüzden `-wal` yoksa boş
    sayılır ama baytları sabitlenir (önceden doluysa aynı kalmalı, yoksa boş kalmalı); `-shm`
    yalnız adıyla muaftır. Veri dizininin ve güvenlik dosyası dizininin öteki her dosyası
    adıyla sabitlenir: yeni bir yan dosya (kopya, geçici dosya) da değişiklik sayılır.
    """
    dizin = app_password.state_path().parent
    wal = db.with_name(f"{db.name}-wal")
    return {
        "db": db.read_bytes() if db.exists() else None,
        "wal": wal.read_bytes() if wal.exists() else b"",
        "veri_dizini": sorted(
            yol.name for yol in db.parent.iterdir() if yol.name not in _yan_dosyalar(db)
        ),
        "guvenlik_dizini": sorted(yol.name for yol in dizin.iterdir()),
        "onceki": sorted(yol.name for yol in db.parent.glob("db-onceki-*")),
        "surum": (db.parent / VERSION_STAMP_FILE_NAME).exists(),
        "guvenlik": app_password.state_path().read_bytes(),
        "yedekleme": config_path(dizin).read_bytes(),
        "not": geri_yukleme_notu.yol(dizin).exists(),
        "arsiv": sorted(yol.name for yol in dizin.glob("guvenlik-arsiv-*")),
    }


def _degismedi(ortam: dict[str, Any]) -> None:
    """Uygulama içi ret: hedefe dokunulmadı, kapı kurulmadı, bakım kapısı açık."""
    assert ortam["db"].read_bytes() == ortam["eski"]
    assert restart_gate.restart_required() is False
    assert bakim.KAPI.bakimda is False
    assert not list(ortam["db"].parent.glob("db-onceki-*"))


def _dogrula(
    db: Path, *, goruntu: bytes = b"", hesap_id: str = TEST_HESAP_ID, askida: bool = False
) -> str:
    return geri_yukleme_yetkisi.yonetici_dogrula(
        db_path=db, goruntu=goruntu, dek=TEST_DEK, hesap_id=hesap_id, askida=askida
    )


# ============================================================ iki kol (tasarım §10.6)


@pytest.mark.parametrize("kol", ["uygulama_ici", "konsol"])
def test_yonetici_olmayan_hesapla_geri_yukle_reddedilir(
    kol: str,
    ortam: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Tasarım §10.6 ve §14 F1b kapısı: "yönetici olmayan hesapla geri yükleme reddedilir"."""
    _muhasip_sarmali_ekle()
    if kol == "uygulama_ici":
        _uygulama_ici_kolu(ortam)
    else:
        _konsol_kolu(ortam, tmp_path, monkeypatch, capsys)


def _uygulama_ici_kolu(ortam: dict[str, Any]) -> None:
    once = _anlik(ortam["db"])
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
    assert _anlik(ortam["db"]) == once


def _konsol_kolu(
    ortam: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Konsol: ara katman yok; muhasibin parolası yedeği AÇAR ama çekirdeğin ORM'siz denetimi
    reddeder. Masaüstü kipi 9 ile çıkar, komut `CommandError` verir; hiçbir dosya değişmez."""
    (ortam["db"].parent / VERSION_STAMP_FILE_NAME).write_text("{}", encoding="utf-8")
    once = _anlik(ortam["db"])
    paths = AppPaths(
        root=tmp_path,
        data=ortam["db"].parent,
        backups=app_password.backup_dir(),
        logs=tmp_path / "gunlukler",
        cache=tmp_path / "onbellek",
    )
    # Django testte zaten kurulu; masaüstü kipinin hazırlığı atlanır, çekirdek gerçektir.
    monkeypatch.setattr(restore_mod, "prepare_django", lambda *a, **k: None)
    args = build_parser().parse_args(
        ["--geri-yukle", YEDEK, "--evet", "--hesap", "muhasip", "--parola", TEST_PAROLA]
    )

    assert restore_mod._restore_flow(paths, args) == EXIT_RESTORE_FAILED
    assert f"HATA: {ILETI_ROL}" in capsys.readouterr().out
    assert _anlik(ortam["db"]) == once

    with pytest.raises(CommandError) as hata:
        call_command(
            "restore_backup",
            str(ortam["yedek"]),
            "--yes",
            "--hesap",
            "muhasip",
            "--password",
            TEST_PAROLA,
            stdout=StringIO(),
        )
    assert str(hata.value) == ILETI_ROL
    assert _anlik(ortam["db"]) == once


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


def test_uygulama_icinde_cekirdegin_reddi_400_ve_kapi_kurulmaz(ortam: dict[str, Any]) -> None:
    """Rol kapısı ve servis kapısı oturumdaki program yöneticisini geçirir; kaydı program
    dışından değiştirilmişse çekirdek reddeder. `GeriYuklemeYetkisiz` bir `BackupRestoreError`
    (`ValueError`) olduğu için uygulama içinde 400'dür (bilinçli; plan F1b-2)."""
    bozuk = program_disindan(TEST_DEK, replace(YONETICI, role="muhasip"), role="yonetici")
    yetkili_sqlite(ortam["db"], dek=TEST_DEK, hesaplar=[bozuk, MUHASIP], isaret="eski")
    ortam["eski"] = ortam["db"].read_bytes()

    yanit = APIClient().post(
        GERI_YUKLE_URL, {"name": YEDEK, "password": TEST_PAROLA}, format="json"
    )

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ILETI_MUHUR
    _degismedi(ortam)


# ============================================================ çekirdeğin ret ve kabul koşulları


@pytest.mark.parametrize(
    ("satir", "beklenen"),
    [
        pytest.param(YONETICI, None, id="ACIK_kabul"),
        pytest.param(
            replace(YONETICI, status="PAROLA_YENILENMELI"), None, id="PAROLA_YENILENMELI_kabul"
        ),
        pytest.param(replace(YONETICI, status="ASKIDA"), "durum", id="ASKIDA_ret"),
        pytest.param(
            replace(YONETICI, status="KAPALI", closed_at=KAPANIS), "durum", id="KAPALI_ret"
        ),
        *[
            pytest.param(replace(YONETICI, role=rol), "rol", id=f"{rol}_ret")
            for rol in AccountRole.values
            if rol != AccountRole.YONETICI
        ],
        pytest.param(
            program_disindan(TEST_DEK, replace(YONETICI, role="muhasip"), role="yonetici"),
            "muhur",
            id="rolu_program_disindan_degismis_ret",
        ),
        pytest.param(
            program_disindan(
                TEST_DEK, replace(YONETICI, status="KAPALI", closed_at=KAPANIS), status="ACIK"
            ),
            "muhur",
            id="durumu_program_disindan_degismis_ret",
        ),
        pytest.param(replace(YONETICI, muhur=""), "muhur", id="muhursuz_ret"),
        # Mühür ÖNCE denetlenir: satırdaki değer rol ya da durum reddini tetiklerdi, ama mühür
        # eski (doğru) değere aittir; ret nedeni ve ileti "değiştirilmiş kayıt"tır.
        pytest.param(
            program_disindan(TEST_DEK, YONETICI, status="KAPALI"),
            "muhur",
            id="kapaliya_cekilmis_muhur_eski_ret",
        ),
        pytest.param(
            program_disindan(TEST_DEK, YONETICI, status="ASKIDA"),
            "muhur",
            id="askiya_cekilmis_muhur_eski_ret",
        ),
        pytest.param(
            program_disindan(TEST_DEK, YONETICI, role="muhasip"),
            "muhur",
            id="muhasibe_cekilmis_muhur_eski_ret",
        ),
    ],
)
def test_konsol_geri_yukleme_durum_kumesi(
    satir: HesapSatiri, beklenen: str | None, tmp_path: Path
) -> None:
    """Kabul: rol `yonetici`, durum ACIK ya da PAROLA_YENILENMELI, mühür tutar (tasarım §4.6.1
    kural 1). Mühür önce denetlenir: değiştirilmiş satırın rolüne ve durumuna güvenilmez."""
    db = tmp_path / "db.sqlite3"
    yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[satir, MUHASIP])
    # Görüntü daima REDDEDER (hesabın satırı yok): kabul de ret de güncel veritabanından
    # gelmelidir; görüntüye danışan bir kod kabulde `satir_yok`, retde başka kod verirdi.
    goruntu = yetkili_sqlite(tmp_path / "goruntu.sqlite3", dek=TEST_DEK, hesaplar=[MUHASIP])

    if beklenen is None:
        assert _dogrula(db, goruntu=goruntu) == KAYNAK_GUNCEL
        return
    with pytest.raises(YetkiReddi) as ret:
        _dogrula(db, goruntu=goruntu)
    assert (ret.value.kod, ret.value.kaynak) == (beklenen, KAYNAK_GUNCEL)
    ileti = {"durum": ILETI_DURUM, "rol": ILETI_ROL, "muhur": ILETI_MUHUR}[beklenen]
    assert ret.value.ileti == ileti == str(ret.value)


def test_okunabilen_guncel_kabul_ederse_goruntuye_bakilmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Karar KABUL yönünde de güncel veritabanındadır (plan F1b-2: görüntüye yalnız güncel
    okunamıyorsa bakılır). Yedekten sonra açılmış ikinci program yöneticisinin (`yonetici-2`,
    tasarım §4.4.4) görüntüde satırı yoktur; güncel veritabanı okunabildiği için kabul edilir."""
    goruntu = yetkili_sqlite(tmp_path / "goruntu.sqlite3", dek=TEST_DEK, hesaplar=[YONETICI])
    # Ön koşul: görüntü tek başına bu hesabı reddeder.
    with pytest.raises(YetkiReddi) as ret:
        _dogrula(tmp_path / "yok.sqlite3", goruntu=goruntu, hesap_id=YONETICI_2.id)
    assert (ret.value.kod, ret.value.kaynak) == ("satir_yok", KAYNAK_GORUNTU)
    db = tmp_path / "db.sqlite3"
    yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[YONETICI, YONETICI_2])
    monkeypatch.setattr(
        geri_yukleme_yetkisi,
        "_goruntu_karari",
        lambda *_a: pytest.fail("okunabilen veritabanında görüntüye bakılmamalı"),
    )

    assert _dogrula(db, goruntu=goruntu, hesap_id=YONETICI_2.id) == KAYNAK_GUNCEL


def test_yedekten_sonra_acilan_program_yoneticisi_parolasiyla_geri_yukler(
    ortam: dict[str, Any],
) -> None:
    """Uçtan uca: `yonetici-2` yedekte yoktur, güncel veritabanında açık program yöneticisidir;
    kendi parolasıyla (sarmalı güncel güvenlik dosyasında) geri yükler."""
    _sarmal_ekle(YONETICI_2)
    yetkili_sqlite(ortam["db"], dek=TEST_DEK, hesaplar=[YONETICI, MUHASIP, YONETICI_2])

    backup_restore.restore_database(
        ortam["yedek"], ortam["db"], hesap=YONETICI_2.login_name, password=TEST_PAROLA
    )

    assert ortam["db"].read_bytes() == ortam["yeni"]


def _kimligi_degistir(eski: str, yeni: str, *, one_al: bool = False) -> None:
    """Metin düzenleyici taklidi (kod gerekmez): güvenlik dosyasında TEK sarmalın `id` alanı.

    `one_al`: değiştirilen sarmal listenin başına taşınır (kes-yapıştır); kimliğiyle arayan yol
    (uygulama içi parola yolu) aynı kimliği taşıyan sarmallardan önce onu bulur.
    """
    durum = app_password.read_state() or {}
    (sarmal,) = [h for h in durum["hesaplar"] if h["id"] == eski]
    sarmal["id"] = yeni
    if one_al:
        durum["hesaplar"].remove(sarmal)
        durum["hesaplar"].insert(0, sarmal)
    durum_yaz(durum)


def _rol_denetimi_kosmamali(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        geri_yukleme_yetkisi,
        "yonetici_dogrula",
        lambda **_k: pytest.fail("kimliği değiştirilmiş sarmal açılmamalı; denetime varılmamalı"),
    )


@pytest.mark.parametrize("kol", ["konsol", "uygulama_ici"])
def test_sarmal_kimligi_degistirilirse_geri_yukleme_reddedilir(
    kol: str,
    ortam: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Sarmal kimliği parola kaydına bağlıdır (kullanıcı kararı 02.11.2026; `geri_yukleme_yetkisi`
    başlığı). Muhasip KENDİ parolasıyla önce rolden reddedilir. `guvenlik.json`'da sarmalının
    `id`'sini metin düzenleyiciyle program yöneticisininkine çevirince sarmal o kimlikle AÇILMAZ:
    yanıt yanlış parolanınkidir ("açılamadı"), rol denetimine hiç varılmaz, hiçbir dosya değişmez,
    not yazılmaz. Konsol kolu çekirdek, masaüstü kipi ve `restore_backup`'tır; uygulama içi kol
    masada açık bırakılmış program yöneticisi oturumudur (rol ve servis kapısı geçer, parola yolu
    oturum hesabının sarmalını kimliğiyle arar ve değiştirilmiş sarmalı bulur). Bağ kaldırılsaydı
    (türetimden kimlik çıksaydı) iki kol da program yöneticisi adına geri yüklerdi."""
    _sarmal_ekle(MUHASIP, parola=MUHASIP_PAROLASI)
    with pytest.raises(backup_restore.GeriYuklemeYetkisiz) as hata:
        backup_restore.restore_database(
            ortam["yedek"], ortam["db"], hesap="muhasip", password=MUHASIP_PAROLASI
        )
    assert hata.value.kod == "rol"  # ön koşul: parola sarmalı muhasibin kendi kimliğiyle açar

    _kimligi_degistir(MUHASIP_ID, TEST_HESAP_ID, one_al=kol == "uygulama_ici")
    _rol_denetimi_kosmamali(monkeypatch)
    (ortam["db"].parent / VERSION_STAMP_FILE_NAME).write_text("{}", encoding="utf-8")
    once = _anlik(ortam["db"])

    if kol == "konsol":
        with pytest.raises(backup_restore.BackupRestoreError) as ret:
            backup_restore.restore_database(
                ortam["yedek"], ortam["db"], hesap="muhasip", password=MUHASIP_PAROLASI
            )
        assert not isinstance(ret.value, backup_restore.GeriYuklemeYetkisiz)
        assert "açılamadı" in str(ret.value)
        assert _anlik(ortam["db"]) == once

        paths = AppPaths(
            root=tmp_path,
            data=ortam["db"].parent,
            backups=app_password.backup_dir(),
            logs=tmp_path / "gunlukler",
            cache=tmp_path / "onbellek",
        )
        monkeypatch.setattr(restore_mod, "prepare_django", lambda *a, **k: None)
        args = build_parser().parse_args(
            ["--geri-yukle", YEDEK, "--evet", "--hesap", "muhasip", "--parola", MUHASIP_PAROLASI]
        )
        assert restore_mod._restore_flow(paths, args) == EXIT_RESTORE_FAILED
        cikti = capsys.readouterr().out
        assert "HATA: Yedek açılamadı" in cikti and ILETI_ROL not in cikti
        assert _anlik(ortam["db"]) == once

        with pytest.raises(CommandError, match="açılamadı"):
            call_command(
                "restore_backup",
                str(ortam["yedek"]),
                "--yes",
                "--hesap",
                "muhasip",
                "--password",
                MUHASIP_PAROLASI,
                stdout=StringIO(),
            )
    else:
        for govde in (
            {"name": YEDEK, "password": MUHASIP_PAROLASI},
            {"name": YEDEK, "hesap": "muhasip", "password": MUHASIP_PAROLASI},
        ):
            yanit = APIClient().post(GERI_YUKLE_URL, govde, format="json")
            assert yanit.status_code == 400, yanit.json()
            assert "açılamadı" in yanit.json()["message"]
            _degismedi(ortam)

    assert _anlik(ortam["db"]) == once
    assert geri_yukleme_notu.oku(app_password.state_path().parent) is None


#: Kanonik olmayan yazımlar: satırı bulan okuyucu (`uuid.UUID`) çoğunu aynı satıra çevirir.
#: Başka hesabın kimliğinin yazımıyla BAĞIN yazım oyunuyla atlatılamadığını, kendi kimliğinin
#: yazımıyla KANONİK KATILIĞI (okuyucu kimliği Argon2id'den önce kurala sokar) sınarlar.
KIMLIK_YAZIMLARI: dict[str, Callable[[str], str]] = {
    "buyuk_harf": str.upper,
    "tiresiz": lambda kimlik: kimlik.replace("-", ""),
    "bosluklu": lambda kimlik: f" {kimlik} ",
    "suslu_ayracli": lambda kimlik: f"{{{kimlik}}}",
    "urn_onekli": lambda kimlik: f"urn:uuid:{kimlik}",
}


@pytest.mark.parametrize("yazim", sorted(KIMLIK_YAZIMLARI))
def test_sarmal_kimligi_kanonik_olmayan_yazimla_da_gecmez(
    yazim: str, ortam: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bağ kanonik biçim oyunuyla atlatılamaz: muhasibin sarmalı program yöneticisinin kimliğinin
    büyük harfli, tiresiz, boşluklu, ayraçlı ya da önekli yazımını taşısa da açılmaz; meşru
    program yöneticisi kendi parolasıyla geri yüklemeye devam eder. Bu test BAĞI sınar, kanonik
    katılığı değil (sarmal muhasibin kimliğine bağlıdır; gevşek okuyucu da açamazdı); katılık
    `test_kendi_kimliginin_kanonik_olmayan_yazimi_geri_yuklemede_de_acmaz`'dadır."""
    _sarmal_ekle(MUHASIP, parola=MUHASIP_PAROLASI)
    _kimligi_degistir(MUHASIP_ID, KIMLIK_YAZIMLARI[yazim](TEST_HESAP_ID))
    with monkeypatch.context() as yama:
        _rol_denetimi_kosmamali(yama)
        with pytest.raises(backup_restore.BackupRestoreError, match="açılamadı") as ret:
            backup_restore.restore_database(
                ortam["yedek"], ortam["db"], hesap="muhasip", password=MUHASIP_PAROLASI
            )
    assert not isinstance(ret.value, backup_restore.GeriYuklemeYetkisiz)

    backup_restore.restore_database(
        ortam["yedek"], ortam["db"], hesap=TEST_TANITICI, password=TEST_PAROLA
    )
    assert ortam["db"].read_bytes() == ortam["yeni"]


@pytest.mark.parametrize("yazim", sorted(KIMLIK_YAZIMLARI))
def test_kendi_kimliginin_kanonik_olmayan_yazimi_geri_yuklemede_de_acmaz(
    yazim: str, ortam: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """KANONİK KATILIK, geri yükleme kolu: program yöneticisinin KENDİ sarmalının `id`'si aynı
    kimliğin kanonik olmayan bir yazımına çevrilince `--hesap yonetici` + doğru parola yedeği
    açmaz ("açılamadı"); okuyucu kimliği Argon2id'den önce kanonik kurala sokar (türetim
    koşmaz), rol denetimine varılmaz, hiçbir dosya değişmez. Kanonik metin geri gelince aynı
    parola geri yükler."""
    _kimligi_degistir(TEST_HESAP_ID, KIMLIK_YAZIMLARI[yazim](TEST_HESAP_ID))
    with monkeypatch.context() as yama:
        _rol_denetimi_kosmamali(yama)
        yama.setattr(crypto, "derive_key", lambda *_a, **_k: pytest.fail("Argon2id koşmamalı"))
        with pytest.raises(backup_restore.BackupRestoreError, match="açılamadı") as ret:
            backup_restore.restore_database(
                ortam["yedek"], ortam["db"], hesap=TEST_TANITICI, password=TEST_PAROLA
            )
    assert not isinstance(ret.value, backup_restore.GeriYuklemeYetkisiz)
    assert ortam["db"].read_bytes() == ortam["eski"]
    assert geri_yukleme_notu.oku(app_password.state_path().parent) is None

    _kimligi_degistir(KIMLIK_YAZIMLARI[yazim](TEST_HESAP_ID), TEST_HESAP_ID)
    backup_restore.restore_database(
        ortam["yedek"], ortam["db"], hesap=TEST_TANITICI, password=TEST_PAROLA
    )
    assert ortam["db"].read_bytes() == ortam["yeni"]


def test_tanitici_takasi_geri_yuklemede_yetki_yukseltmez(ortam: dict[str, Any]) -> None:
    """Tanıtıcı yalnız sarmalı BULMAYA yarar. Muhasip, sarmalının tanıtıcısını `yonetici`, program
    yöneticisininkini `muhasip` yaparsa `--hesap yonetici` muhasibin sarmalını bulur; sarmal
    muhasibin KENDİ kimliğiyle açılır ve denetim o kimliği reddeder (rol). Hiçbir dosya değişmez."""
    _sarmal_ekle(MUHASIP, parola=MUHASIP_PAROLASI)
    durum = app_password.read_state() or {}
    takas = {TEST_TANITICI: "muhasip", "muhasip": TEST_TANITICI}
    for sarmal in durum["hesaplar"]:
        sarmal["tanitici"] = takas[sarmal["tanitici"]]
    durum_yaz(durum)
    once = _anlik(ortam["db"])

    with pytest.raises(backup_restore.GeriYuklemeYetkisiz) as hata:
        backup_restore.restore_database(
            ortam["yedek"], ortam["db"], hesap=TEST_TANITICI, password=MUHASIP_PAROLASI
        )

    assert (hata.value.kod, str(hata.value)) == ("rol", ILETI_ROL)
    assert _anlik(ortam["db"]) == once


def test_bagsiz_sarmalla_parola_yolu_acilmaz(
    ortam: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bağdan önceki biçimde (F1b-1: kimlik türetime girmez, `turetim` alanı yok) yazılmış
    sarmal doğru parolayla da açılmaz: geri düşüş yoktur. Yanıt yanlış parolanınkidir ve yedeği
    açan kurtarma anahtarını anar; kurtarma anahtarı yolu açık kalır."""
    durum = app_password.read_state() or {}
    durum["hesaplar"] = [bagsiz_sarmal(TEST_HESAP_ID, TEST_TANITICI, TEST_PAROLA)]
    durum_yaz(durum)
    with monkeypatch.context() as yama:
        _rol_denetimi_kosmamali(yama)
        with pytest.raises(backup_restore.BackupRestoreError, match="kurtarma anahtarıyla"):
            backup_restore.restore_database(
                ortam["yedek"], ortam["db"], hesap=TEST_TANITICI, password=TEST_PAROLA
            )
    assert ortam["db"].read_bytes() == ortam["eski"]

    backup_restore.restore_database(
        ortam["yedek"], ortam["db"], recovery_key=TEST_KURTARMA_ANAHTARI
    )
    assert ortam["db"].read_bytes() == ortam["yeni"]


def test_sarmalinda_askida_olan_program_yoneticisi_reddedilir(ortam: dict[str, Any]) -> None:
    """Güvenlik dosyasındaki hatalı deneme askısı da kabul koşuludur (girişle aynı)."""
    durum = app_password.read_state() or {}
    durum["hesaplar"][0]["askida"] = True
    durum_yaz(durum)
    once = _anlik(ortam["db"])

    with pytest.raises(backup_restore.GeriYuklemeYetkisiz) as hata:
        backup_restore.restore_database(
            ortam["yedek"], ortam["db"], hesap=TEST_TANITICI, password=TEST_PAROLA
        )

    assert (hata.value.kod, str(hata.value)) == ("askida", ILETI_DURUM)
    assert _anlik(ortam["db"]) == once


class _GunlukToplayici(logging.Handler):
    """Geri yükleme günlükçüsünün kayıtlarını toplar (`caplog`'dan bağımsız)."""

    def __init__(self, level: int) -> None:
        super().__init__(level=level)
        self.kayitlar: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.kayitlar.append(record)


@pytest.mark.parametrize("neden", ["rol", "muhur", "satir_yok"])
def test_ret_sonrasi_hicbir_dosya_degismez(neden: str, ortam: dict[str, Any]) -> None:
    """Ret takastan önce: db baytları, `db-onceki-*` yokluğu, not yokluğu, sürüm damgası,
    `guvenlik.json`, `yedekleme.json`, arşivler ve iki dizinin dosya listesi aynı; `-wal` boş
    (salt okunur okumanın bedeli `_anlik`'te: 0 baytlık `-wal` ve bir `-shm` oluşabilir)."""
    _muhasip_sarmali_ekle()
    hesap = "muhasip" if neden == "rol" else TEST_TANITICI
    if neden == "muhur":
        bozuk = program_disindan(TEST_DEK, replace(YONETICI, role="muhasip"), role="yonetici")
        yetkili_sqlite(ortam["db"], dek=TEST_DEK, hesaplar=[bozuk, MUHASIP])
    elif neden == "satir_yok":
        yetkili_sqlite(ortam["db"], dek=TEST_DEK, hesaplar=[MUHASIP])
    (ortam["db"].parent / VERSION_STAMP_FILE_NAME).write_text("{}", encoding="utf-8")
    once = _anlik(ortam["db"])
    toplayici = _GunlukToplayici(level=logging.WARNING)
    kayitlar = toplayici.kayitlar
    gunlukcu = logging.getLogger("oab_defteri.restore")
    gunlukcu.addHandler(toplayici)
    try:
        with pytest.raises(backup_restore.GeriYuklemeYetkisiz) as hata:
            backup_restore.restore_database(
                ortam["yedek"], ortam["db"], hesap=hesap, password=TEST_PAROLA
            )
    finally:
        gunlukcu.removeHandler(toplayici)

    assert hata.value.kod == neden
    assert _anlik(ortam["db"]) == once
    assert once["surum"] is True and once["not"] is False and once["onceki"] == []
    # Ret günlüğe sırsız uyarı olarak düşer: neden kodu var; parola ve tanıtıcı yok.
    (kayit,) = [k for k in kayitlar if k.levelno == logging.WARNING]
    metin = kayit.getMessage()
    assert f"neden: {neden}" in metin
    assert TEST_PAROLA not in metin and hesap not in metin


@pytest.mark.parametrize("program", ["kapali", "acik"])
def test_ret_yan_dosyalarin_sinirini_asmaz(program: str, ortam: dict[str, Any]) -> None:
    """Salt okunur denetimin bedeli (`geri_yukleme_yetkisi` başlığı; F1b-2 ekleri: planın
    "hiçbir dosya değişmez"inin niteliği). Program kapalıyken (`-wal` ve `-shm` yok) ret en çok
    0 baytlık bir `-wal` ve bir `-shm` bırakır; program açıkken (yazan bağlantı, `-wal` dolu)
    `-wal`'ın baytları aynı kalır. Veritabanının baytları ve öteki dosyalar değişmez."""
    _muhasip_sarmali_ekle()
    db = ortam["db"]
    wal = db.with_name(f"{db.name}-wal")
    yazan: sqlite3.Connection | None = None
    if program == "acik":
        yazan = sqlite3.connect(db)
        yazan.execute("PRAGMA wal_autocheckpoint=0")
        yazan.execute("UPDATE kayit SET deger = 'acik'")
        yazan.commit()
        assert wal.stat().st_size > 0
    else:
        assert not {yol.name for yol in db.parent.iterdir()} & _yan_dosyalar(db)
    once = _anlik(db)
    try:
        with pytest.raises(backup_restore.GeriYuklemeYetkisiz):
            backup_restore.restore_database(
                ortam["yedek"], db, hesap="muhasip", password=TEST_PAROLA
            )
        sonra = _anlik(db)
    finally:
        if yazan is not None:
            yazan.close()

    assert sonra == once
    if program == "acik":
        assert sonra["wal"] != b""
    else:
        assert not wal.exists() or wal.stat().st_size == 0


def test_yanlis_parola_rolu_sizdirmaz(
    ortam: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rol denetimi parola doğrulandıktan SONRA koşar: yanlış parola yalnız "açılamadı" der."""
    _muhasip_sarmali_ekle()
    monkeypatch.setattr(
        geri_yukleme_yetkisi,
        "yonetici_dogrula",
        lambda **_k: pytest.fail("yanlış parolada rol denetimi koşmamalı"),
    )

    with pytest.raises(backup_restore.BackupRestoreError) as hata:
        backup_restore.restore_database(
            ortam["yedek"], ortam["db"], hesap="muhasip", password="Yanlis-Parola-9"
        )

    assert not isinstance(hata.value, backup_restore.GeriYuklemeYetkisiz)
    assert "açılamadı" in str(hata.value)
    assert ILETI_ROL not in str(hata.value)


@pytest.mark.parametrize("oturum_hesabi", [None, MUHASIP_ID], ids=["konsol", "muhasip_oturumu"])
def test_kurtarma_anahtari_yolunda_rol_denetimi_yok(
    oturum_hesabi: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Anahtarın kendisi yetkidir (tasarım §4.4.4): hesap tablosu olmayan bozuk veritabanından
    ve görüntüsünden de geri yüklenir; denetim hiç çağrılmaz."""
    monkeypatch.setattr(
        geri_yukleme_yetkisi,
        "yonetici_dogrula",
        lambda **_k: pytest.fail("kurtarma anahtarı yolunda rol denetimi koşmamalı"),
    )
    db = tmp_path / "veri" / "db.sqlite3"
    db.parent.mkdir()
    duz_sqlite(db, "eski")
    goruntu = duz_sqlite(tmp_path / "goruntu.sqlite3", "yeni")
    yedek = tmp_path / YEDEK
    yedek.write_bytes(_yedek(goruntu))

    backup_restore.restore_database(
        yedek, db, recovery_key=TEST_KURTARMA_ANAHTARI, oturum_hesabi=oturum_hesabi
    )

    assert db.read_bytes() == goruntu


# ============================================================ geri düşüş (okunamayan güncel)


def _okunamayan_guncel(db: Path, bozulma: str, karsit: HesapSatiri) -> None:
    """Güncel veritabanını okunamaz kılar; okunabilen parçası görüntünün tersini söyler."""
    if bozulma == "dosya_yok":
        return
    if bozulma == "bozuk_bayt":
        db.write_bytes(b"bozuk veritabani " * 512)
    elif bozulma == "tablo_yok":
        duz_sqlite(db, "eski")
    elif bozulma == "okul_karti_yok":
        yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[karsit], okul_karti=0)
    elif bozulma == "iki_okul_karti":
        yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[karsit], okul_karti=2)
    elif bozulma == "baska_dek_parmak_izi":
        yetkili_sqlite(
            db,
            dek=TEST_DEK,
            hesaplar=[karsit],
            parmak_izi=crypto.key_fingerprint(crypto.new_data_key()),
        )
    elif bozulma == "bos_parmak_izi":
        yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[karsit], parmak_izi="")
    elif bozulma == "gecersiz_utf8_parmak_izi":
        # Okunamayan parmak izi bu DEK'inkine eşit değildir (modül başlığı): `sqlite3` hatası
        # olmayan kod çözme hatası da geri düşüşe gider, kaçıp "beklenmeyen hata" olmaz.
        yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[karsit])
        _yaz(db, "UPDATE okul_schoolconfig SET app_password_hash = CAST(X'FF61' AS TEXT)")
    elif bozulma == "hesap_tablosu_yok":
        # Okul kartı sağlam, hesap tablosu silinmiş: tek yazımla geri düşüş (kabul edilen kalan
        # risk; modül başlığı).
        yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[karsit])
        _yaz(db, "DROP TABLE okul_account")
    else:  # pragma: no cover — parametre listesi kapalıdır
        raise AssertionError(bozulma)


def _yaz(db: Path, sql: str) -> None:
    """Program dışından tek bir yazım."""
    with closing(sqlite3.connect(db)) as baglanti:
        baglanti.execute(sql)
        baglanti.commit()


OKUNAMAYAN_GUNCEL_HALLERI = [
    "dosya_yok",
    "bozuk_bayt",
    "tablo_yok",
    "okul_karti_yok",
    "iki_okul_karti",
    "baska_dek_parmak_izi",
    "bos_parmak_izi",
    "gecersiz_utf8_parmak_izi",
    "hesap_tablosu_yok",
]


@pytest.mark.parametrize("goruntudeki", ["yonetici", "muhasip"])
@pytest.mark.parametrize("bozulma", OKUNAMAYAN_GUNCEL_HALLERI)
def test_guncel_veritabani_okunamazsa_yedek_goruntusunde_denetlenir(
    bozulma: str, goruntudeki: str, tmp_path: Path
) -> None:
    """Okunamıyor sayılan dört hâl (dosya yok; `sqlite3` hatası; okul kartı tek satır değil;
    parmak izi bu DEK'inki değil — okunamayan parmak izi dahil): karar yedeğin görüntüsünden
    verilir. Okunabilen parça görüntünün tersini söyler; kararı görüntünün verdiği böyle
    görünür."""
    goruntudeki_satir = YONETICI if goruntudeki == "yonetici" else replace(YONETICI, role="muhasip")
    karsit = replace(YONETICI, role="muhasip") if goruntudeki == "yonetici" else YONETICI
    db = tmp_path / "veri" / "db.sqlite3"
    db.parent.mkdir()
    _okunamayan_guncel(db, bozulma, karsit)
    goruntu = yetkili_sqlite(
        tmp_path / "goruntu.sqlite3", dek=TEST_DEK, hesaplar=[goruntudeki_satir, MUHASIP]
    )

    if goruntudeki == "yonetici":
        assert _dogrula(db, goruntu=goruntu) == KAYNAK_GORUNTU
    else:
        with pytest.raises(YetkiReddi) as ret:
            _dogrula(db, goruntu=goruntu)
        assert (ret.value.kod, ret.value.kaynak) == ("rol", KAYNAK_GORUNTU)


@pytest.mark.parametrize(
    ("bozulma", "neden"),
    [
        ("dosya_yok", "dosya_yok"),
        ("bozuk_bayt", "DatabaseError"),
        ("tablo_yok", "OperationalError"),
        ("iki_okul_karti", "okul_karti"),
        ("baska_dek_parmak_izi", "parmak_izi"),
        ("gecersiz_utf8_parmak_izi", "parmak_izi"),
    ],
)
def test_goruntuye_dusus_nedeniyle_uyari_olarak_gunluge_yazilir(
    bozulma: str, neden: str, tmp_path: Path
) -> None:
    """Geri düşüş sessiz değildir (denetim bulgusu: ağdaki veri dizininde adres açılmayınca karar
    sessizce görüntüye kalıyordu): neden uyarı düzeyinde günlüğe yazılır — `sqlite3` hatasında
    sınıfı ve kodu; hatanın iletisi ve dosya yolu yazılmaz."""
    db = tmp_path / "veri-dizini" / "db.sqlite3"
    db.parent.mkdir()
    _okunamayan_guncel(db, bozulma, YONETICI)
    goruntu = yetkili_sqlite(tmp_path / "goruntu.sqlite3", dek=TEST_DEK, hesaplar=[YONETICI])
    toplayici = _GunlukToplayici(level=logging.WARNING)
    gunlukcu = logging.getLogger("oab_defteri.restore")
    gunlukcu.addHandler(toplayici)
    try:
        assert _dogrula(db, goruntu=goruntu) == KAYNAK_GORUNTU
    finally:
        gunlukcu.removeHandler(toplayici)

    (kayit,) = toplayici.kayitlar
    metin = kayit.getMessage()
    assert re.search(rf"\(neden: {neden}(/SQLITE_\w+)?\)", metin), metin
    # Yol ve `sqlite3` iletisi ("file is not a database", "no such table: …") yazılmaz.
    assert "veri-dizini" not in metin and "file is not" not in metin and "no such" not in metin


def test_iki_orm_siz_okuyucu_ortak_salt_okunur_adresi_kullanir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hesap denetimi ve zincir başı aynı adres kurucusundan geçer (`shared.sqlite_adres`):
    yol `resolve()` edilmeden verilir (Windows'ta eşlenmiş sürücü UNC'ye dönmez; burada
    sembolik bağla sınanır), UNC yol authority'siz yazılır (`shared/tests/test_sqlite_adres`)."""
    if not hasattr(os, "symlink") or os.name != "posix":
        pytest.skip("Sembolik bağ POSIX'te sınanır (testler Docker'da koşar).")
    gercek = tmp_path / "gercek"
    gercek.mkdir()
    bag = tmp_path / "bag"
    bag.symlink_to(gercek, target_is_directory=True)
    db = bag / "db.sqlite3"
    yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[YONETICI])
    gorulen: list[Any] = []
    asil = sqlite_adres.salt_okunur_adres

    def izleyen(yol: Any) -> str:
        gorulen.append(yol)
        return asil(yol)

    monkeypatch.setattr(sqlite_adres, "salt_okunur_adres", izleyen)

    assert _dogrula(db) == KAYNAK_GUNCEL
    assert geri_yukleme_notu.zincir_basi_oku(db) is None  # iz tablosu yok: "bilinmiyor"

    assert gorulen == [db, db]
    assert "/bag/" in asil(db) and "/gercek/" not in asil(db)


def _gecersiz_metin(db: Path) -> None:
    """Açık program yöneticisi satırının tanıtıcısına geçersiz UTF-8 yazar (program dışından)."""
    yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[YONETICI])
    with closing(sqlite3.connect(db)) as baglanti:
        baglanti.execute(
            "UPDATE okul_account SET login_name = CAST(X'FF61' AS TEXT) WHERE id = ?",
            (uuid.UUID(TEST_HESAP_ID).hex,),
        )
        baglanti.commit()


def _bicimsiz_zaman(db: Path) -> None:
    """Açık program yöneticisi satırının açılış anına zaman olmayan bir metin yazar."""
    yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[YONETICI])
    with closing(sqlite3.connect(db)) as baglanti:
        baglanti.execute(
            "UPDATE okul_account SET opened_at = 'dün' WHERE id = ?",
            (uuid.UUID(TEST_HESAP_ID).hex,),
        )
        baglanti.commit()


@pytest.mark.parametrize(
    ("kurulum", "beklenen"),
    [
        pytest.param(
            lambda db: yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[MUHASIP]),
            "satir_yok",
            id="satir_yok",
        ),
        pytest.param(
            lambda db: yetkili_sqlite(
                db, dek=TEST_DEK, hesaplar=[replace(YONETICI, status="KAPALI", closed_at=KAPANIS)]
            ),
            "durum",
            id="guncelde_kapali",
        ),
        pytest.param(
            lambda db: yetkili_sqlite(
                db, dek=TEST_DEK, hesaplar=[replace(YONETICI, role="muhasip")]
            ),
            "rol",
            id="guncelde_muhasip",
        ),
        pytest.param(
            lambda db: yetkili_sqlite(
                db, dek=TEST_DEK, hesaplar=[replace(YONETICI, muhur="0" * 64)]
            ),
            "muhur",
            id="guncelde_muhur_bozuk",
        ),
        pytest.param(
            _gecersiz_metin,
            "muhur",
            id="guncelde_gecersiz_utf8",
        ),
        pytest.param(
            _bicimsiz_zaman,
            "muhur",
            id="guncelde_bicimsiz_zaman",
        ),
    ],
)
def test_okunabilen_veritabaninda_karar_guncelde_kalir_yedege_dusulmez(
    kurulum: Any, beklenen: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fail-closed (modül başlığı): okunabilen ve bu DEK'e ait veritabanında satır yoksa, rol,
    durum ya da mühür tutmuyorsa (geçersiz metin ve biçimsiz zaman dahil) görüntüye DÜŞÜLMEZ —
    görüntü aynı hesabı açık program yöneticisi gösterse de. Aksi hâlde tek bir satırı bozan,
    yedeğin alındığı günkü rolüne sığınırdı."""
    goruntu = yetkili_sqlite(tmp_path / "goruntu.sqlite3", dek=TEST_DEK, hesaplar=[YONETICI])
    assert _dogrula(tmp_path / "yok.sqlite3", goruntu=goruntu) == KAYNAK_GORUNTU
    monkeypatch.setattr(
        geri_yukleme_yetkisi,
        "_goruntu_karari",
        lambda *_a: pytest.fail("okunabilen veritabanında görüntüye düşülmemeli"),
    )
    db = tmp_path / "db.sqlite3"
    kurulum(db)

    with pytest.raises(YetkiReddi) as ret:
        _dogrula(db, goruntu=goruntu)

    assert (ret.value.kod, ret.value.kaynak) == (beklenen, KAYNAK_GUNCEL)


def test_guncel_veritabaninda_wal_daki_son_yazim_gorunur(tmp_path: Path) -> None:
    """`immutable` kullanılmaz (modül başlığı): henüz ana dosyaya aktarılmamış son yazım (az önce
    kapatılan hesap) görünmelidir; yalnız ana dosyayı okuyan bir okuyucu hesabı açık sanardı."""
    db = tmp_path / "db.sqlite3"
    yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[YONETICI])
    kapali = replace(YONETICI, status="KAPALI", closed_at=KAPANIS)
    with closing(sqlite3.connect(db)) as yazan:
        yazan.execute("PRAGMA wal_autocheckpoint=0")
        yazan.execute(
            "UPDATE okul_account SET status = 'KAPALI', closed_at = ?, seal = ? WHERE id = ?",
            (
                str(KAPANIS.replace(tzinfo=None)),
                muhur(TEST_DEK, kapali),
                uuid.UUID(TEST_HESAP_ID).hex,
            ),
        )
        yazan.commit()
        # Yazan bağlantı açıkken son yazım yalnız `-wal`'dadır.
        assert (tmp_path / "db.sqlite3-wal").stat().st_size > 0

        with pytest.raises(YetkiReddi) as ret:
            _dogrula(db)

    assert (ret.value.kod, ret.value.kaynak) == ("durum", KAYNAK_GUNCEL)


def test_goruntu_de_okunamazsa_reddedilir(tmp_path: Path) -> None:
    goruntu = duz_sqlite(tmp_path / "goruntu.sqlite3", "yeni")

    with pytest.raises(YetkiReddi) as ret:
        _dogrula(tmp_path / "yok.sqlite3", goruntu=goruntu)

    assert (ret.value.kod, ret.value.kaynak, ret.value.ileti) == (
        "okunamadi",
        KAYNAK_GORUNTU,
        ILETI_ROL,
    )


def test_cekirdek_okunamayan_guncelde_yedegin_goruntusuyle_geri_yukler(
    ortam: dict[str, Any],
) -> None:
    """Uçtan uca: güncel veritabanı bozuk (konsol geri yüklemesinin varlık sebebi), program
    yöneticisi yedeğin görüntüsünde doğrulanır, geri yükleme yapılır."""
    ortam["db"].write_bytes(b"bozuk veritabani " * 512)

    sonuc = backup_restore.restore_database(
        ortam["yedek"], ortam["db"], hesap=TEST_TANITICI, password=TEST_PAROLA
    )

    assert ortam["db"].read_bytes() == ortam["yeni"]
    assert sonuc.old_db_path is not None


# ============================================================ görüntünün açılması


def _izleyen_karar(monkeypatch: pytest.MonkeyPatch, gorulen: list[Path | None]) -> None:
    """`_karar`'ı sarar: görüntünün hangi dosyadan açıldığını kaydeder (bellekteyse None)."""
    asil = geri_yukleme_yetkisi._karar

    def izleyen(baglanti: sqlite3.Connection, dek: bytes, anahtar: str | None) -> object:
        dosya = str(baglanti.execute("PRAGMA database_list").fetchone()[2])
        gorulen.append(Path(dosya) if dosya else None)
        return asil(baglanti, dek, anahtar)

    monkeypatch.setattr(geri_yukleme_yetkisi, "_karar", izleyen)


def test_yedek_goruntusu_wal_basligiyla_bellekte_acilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Programın yedeği WAL işaretli başlık taşır (18-19. bayt 2): bellekteki kopya yamanır,
    görüntünün kendisi değişmez; diske düz kopya yazılmaz."""
    goruntu = yetkili_sqlite(tmp_path / "goruntu.sqlite3", dek=TEST_DEK, hesaplar=[YONETICI])
    assert goruntu[18:20] == b"\x02\x02"
    yamali = geri_yukleme_yetkisi.wal_basligini_yama(goruntu)
    assert yamali[18:20] == b"\x01\x01" and goruntu[18:20] == b"\x02\x02"
    assert yamali[:18] == goruntu[:18] and yamali[20:] == goruntu[20:]
    duz = duz_sqlite(tmp_path / "duz.sqlite3", "x")
    assert geri_yukleme_yetkisi.wal_basligini_yama(duz) is duz
    veri = tmp_path / "veri"
    veri.mkdir()
    gorulen: list[Path | None] = []
    _izleyen_karar(monkeypatch, gorulen)

    assert _dogrula(veri / "db.sqlite3", goruntu=goruntu) == KAYNAK_GORUNTU

    assert gorulen == [None]  # bellek içi bağlantı
    assert list(veri.iterdir()) == []


@pytest.mark.parametrize("yol", ["kabul", "sqlite_hatasi", "beklenmeyen_hata"])
def test_deserialize_yokken_gecici_dizin_kullanilir_ve_silinir(
    yol: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pardus 21 (SQLite 3.34, `deserialize` yok): görüntü veri dizini altında 0700 izinli
    geçici dizine yazılır, salt okunur açılır ve okunur okunmaz silinir; hata yolunda da
    (tasarımın "bellekte" lafzından sapma, aile emsali `desktop/backup.py`)."""
    monkeypatch.setattr(geri_yukleme_yetkisi, "_DESERIALIZE_VAR", False)
    veri = tmp_path / "veri"
    veri.mkdir()
    goruntu = yetkili_sqlite(tmp_path / "goruntu.sqlite3", dek=TEST_DEK, hesaplar=[YONETICI])
    if yol == "sqlite_hatasi":
        goruntu = goruntu[:100] + b"\xff" * (len(goruntu) - 100)
    gorulen: list[Path | None] = []
    kipler: list[int] = []
    asil = geri_yukleme_yetkisi._karar

    def izleyen(baglanti: sqlite3.Connection, dek: bytes, anahtar: str | None) -> object:
        dosya = Path(str(baglanti.execute("PRAGMA database_list").fetchone()[2]))
        gorulen.append(dosya)
        kipler.append(stat.S_IMODE(dosya.parent.stat().st_mode))
        if yol == "beklenmeyen_hata":
            raise RuntimeError("beklenmeyen hata")
        return asil(baglanti, dek, anahtar)

    monkeypatch.setattr(geri_yukleme_yetkisi, "_karar", izleyen)

    if yol == "kabul":
        assert _dogrula(veri / "db.sqlite3", goruntu=goruntu) == KAYNAK_GORUNTU
    elif yol == "sqlite_hatasi":
        with pytest.raises(YetkiReddi) as ret:
            _dogrula(veri / "db.sqlite3", goruntu=goruntu)
        assert ret.value.kod == "okunamadi"
    else:
        with pytest.raises(RuntimeError):
            _dogrula(veri / "db.sqlite3", goruntu=goruntu)

    (dosya,) = gorulen
    assert dosya is not None
    assert dosya.parent.parent == veri.resolve()
    assert dosya.parent.name.startswith(geri_yukleme_yetkisi.GECICI_DIZIN_ONEKI)
    if os.name == "posix":
        assert kipler == [0o700]
    assert not dosya.parent.exists()
    assert list(veri.iterdir()) == []


# ============================================================ ORM ile biçim eşitliği


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mikrosaniye", [0, 123456])
def test_orm_siz_okuyucu_orm_muhruyle_ayni(mikrosaniye: int) -> None:
    """ORM'in yazıp commit ettiği satır, test veritabanı DOSYASINDAN ORM'siz okunur: biçim
    (tiresiz kimlik, saat dilimsiz UTC metni; mikrosaniye sıfırsa kesirsiz) ve mühür ORM'inkiyle
    aynıdır. Satır Europe/Istanbul saatiyle verilir: UTC'ye çevrim de sınanır."""
    an = datetime(2026, 10, 31, 10, 15, 30, mikrosaniye, tzinfo=ZoneInfo("Europe/Istanbul"))
    hesap = Account(
        id=uuid.UUID("3d9e8f70-1a2b-4c3d-8e9f-a0b1c2d3e4f5"),
        login_name="dk-1",
        role=AccountRole.DENETLEME_KURULU,
        display_name="Örnek Üye",
        status=AccountStatus.KAPALI,
        opened_at=an,
        closed_at=an + timedelta(days=3),
    )
    hesap.seal = hesap.compute_seal(TEST_DEK)
    hesap.save(force_insert=True)
    hesap.refresh_from_db()
    db = Path(str(connection.settings_dict["NAME"]))
    adres = sqlite_adres.salt_okunur_adres(db)

    with closing(sqlite3.connect(adres, uri=True)) as baglanti:
        satir = geri_yukleme_yetkisi.hesap_satiri(baglanti, hesap.id.hex)

    kesir = f".{mikrosaniye:06d}" if mikrosaniye else ""
    assert satir[0] == hesap.id.hex
    assert satir[4] == f"2026-10-31 07:15:30{kesir}"  # saat dilimsiz UTC
    alanlar = geri_yukleme_yetkisi.satirdan_muhur_alanlari(satir)
    assert kanonik.kodla(alanlar) == kanonik.kodla(hesap.seal_fields())
    assert kanonik.hesap_muhru(crypto.account_seal_key(TEST_DEK), alanlar) == hesap.seal
    # Uçtan uca: aynı dosyada ORM'in yazdığı program yöneticisi kabul, DK rolle reddedilir.
    assert _dogrula(db) == KAYNAK_GUNCEL
    with pytest.raises(YetkiReddi) as ret:
        _dogrula(db, hesap_id=str(hesap.id))
    assert ret.value.kod == "rol"


# ============================================================ modülün sözleşmesi


def test_rol_ve_durum_sabitleri_modelle_ayni() -> None:
    assert geri_yukleme_yetkisi.ROL_YONETICI == AccountRole.YONETICI.value
    assert geri_yukleme_yetkisi.GIRIS_DURUMLARI == {
        AccountStatus.ACIK.value,
        AccountStatus.PAROLA_YENILENMELI.value,
    }


def test_okuyucu_orm_ve_django_ice_aktarmaz() -> None:
    """Modül masaüstü konsolunda Django kurulmadan da koşabilmelidir: yalnız standart kitaplık
    ile `shared.kanonik`, `shared.crypto` ve `shared.sqlite_adres` (modül başlığı "ORM YOK");
    adres kurucusu da yalnız standart kitaplığa dayanır."""
    adres_kaynagi = Path(sqlite_adres.__file__).read_text(encoding="utf-8")
    for dugum in ast.walk(ast.parse(adres_kaynagi)):
        if isinstance(dugum, ast.Import):
            pytest.fail(f"sqlite_adres beklenmeyen içe aktarım: {ast.dump(dugum)}")
        elif isinstance(dugum, ast.ImportFrom):
            assert dugum.module in {"__future__", "pathlib", "urllib.parse"}, dugum.module
    kaynak = Path(geri_yukleme_yetkisi.__file__).read_text(encoding="utf-8")
    izinli = {
        "__future__",
        "logging",
        "sqlite3",
        "tempfile",
        "uuid",
        "collections.abc",
        "contextlib",
        "datetime",
        "pathlib",
        "typing",
    }
    for dugum in ast.walk(ast.parse(kaynak)):
        if isinstance(dugum, ast.Import):
            assert {ad.name for ad in dugum.names} <= izinli
        elif isinstance(dugum, ast.ImportFrom):
            if dugum.module == "shared":
                assert {ad.name for ad in dugum.names} <= {"crypto", "kanonik", "sqlite_adres"}
            else:
                assert dugum.module in izinli, dugum.module


def _depo_koku() -> Path:
    """Yerelde `depo/backend/...`; konteynerde backend `/app`, depo `/repo`."""
    yerel = Path(__file__).resolve().parents[4]
    for kok in (yerel, Path("/repo")):
        if (kok / "docs").is_dir() and (kok / "backend").is_dir():
            return kok
    pytest.fail(f"Depo kökü bulunamadı ({yerel} ya da /repo).")


def test_iletiler_sozlukte_yazilidir() -> None:
    """Kullanıcı metni sözlükten (docs/sozluk.md "Yedek" satırı) sapmaz."""
    sozluk = (_depo_koku() / "docs" / "sozluk.md").read_text(encoding="utf-8")
    for ileti in (ILETI_ROL, ILETI_DURUM, ILETI_MUHUR):
        assert re.search(re.escape(f'**"{ileti}"**'), sozluk), ileti


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
