"""Çalışan program içinden geri yükleme (services.live_restore + API uçları).

Çekirdek senaryolar `test_backup_restore.py`'dedir; burada API ayağına özgü
davranışlar sınanır: yedek listesi, ad/yükleme kaynak seçimi, yol ayracı
reddi, bağlantı kapatma ve "yeniden başlat" kapısının (restart_gate) yalnız
BAŞARIDA kurulması. Çekirdek gibi bu testler de ORM'e dokunmaz (`django_db`
işareti bilinçli olarak yoktur); hedef veritabanı geçici bir dosyadır.

Veri dizini `backend/conftest.py`'nin güvenlik dizinidir (geçerli bir
`guvenlik.json` içerir; kilit kapısı böylece DB'ye sormadan geçer). Yedekler
varsayılan olarak bu kurulumun DEK'iyle alınır ve oturumdaki hesabın parolasıyla
açılır (aynı bilgisayar yolu; tasarım §4.4.4). Başka DEK'le alınan yedeği güncel
dosya açamaz; başlık yalnız kurtarma bölümünü taşıdığı için (TK10) o yedek yalnız
kurtarma anahtarıyla açılır ve `guvenlik.json` yalnız kurtarma bölümüyle yazılır.
Güvenlik dosyası KAYIPKEN geri yükleme `test_app_password.py::TestGuvenlikDosyasiKayip`'tadır.

Parola yolunda çekirdek hesabı program yöneticisi olarak ORM'siz doğrular (tasarım §4.4.4;
`geri_yukleme_yetkisi`): buradaki bütün SQLite görüntüleri bu kurulumun DEK'iyle mühürlü
program yöneticisi satırını (`TEST_HESAP_ID`) ve okul kartını taşır (`geri_yukleme_ortak`).
Yetkinin kendi testleri `test_geri_yukleme_yetkisi.py`'dedir.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from desktop.backup_crypto import (
    DENEME_MAGIC,
    KAPSAM_TAM,
    Manifesto,
    recovery_header_from_state,
)
from desktop.tests.kap_ortak import durum_basligi, kap_kur
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connections
from rest_framework.test import APIClient

from apps.okul import restart_gate
from apps.okul.services import app_password, backup_restore, live_restore
from apps.okul.tests.geri_yukleme_ortak import HesapSatiri, yetkili_sqlite
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_KURTARMA_ANAHTARI, TEST_PAROLA, TEST_TANITICI
from shared import bakim, crypto

PAROLA = TEST_PAROLA
LISTE_URL = "/api/v1/backups/"
GERI_YUKLE_URL = "/api/v1/backups/restore/"


@pytest.fixture(autouse=True)
def ortam(
    guvenlik_ortami: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[dict[str, Path]]:
    """Veri dizini conftest'inki; hedef veritabanı geçici dosya; kapı bayrağı temiz."""
    yedekler = app_password.backup_dir()
    yedekler.mkdir(parents=True, exist_ok=True)
    db = tmp_path / "canli" / "db.sqlite3"
    db.parent.mkdir()
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(db))
    yield {"veri": guvenlik_ortami, "yedekler": yedekler, "db": db}


def _sqlite_baytlari(dizin: Path, isaret: str) -> bytes:
    """`isaret` değerini ve bu kurulumun mühürlü program yöneticisi satırını taşıyan SQLite."""
    return yetkili_sqlite(
        dizin / f"kaynak-{isaret}.sqlite3",
        dek=TEST_DEK,
        hesaplar=[HesapSatiri(TEST_HESAP_ID, TEST_TANITICI)],
        isaret=isaret,
    )


def _sifreli_kapsayici(icerik: bytes, *, yabanci: bool = False) -> tuple[bytes, dict[str, Any]]:
    """Başlıklı (TK10 izdüşümü) şifreli `.odbak` ve başlığın güvenlik durumu.

    Varsayılan: bu kurulumun DEK'i — oturumdaki hesabın parolasıyla açılır.
    `yabanci`: başka DEK — yalnız `TEST_KURTARMA_ANAHTARI` ile (başlıktan) açılır.
    """
    if yabanci:
        dek = crypto.new_data_key()
        durum = app_password._build_state(
            dek,
            hesap_id="5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9",
            tanitici=TEST_TANITICI,
            password="Baska-Parola-7",
            recovery_key=TEST_KURTARMA_ANAHTARI,
        )
    else:
        dek = TEST_DEK
        durum = app_password.read_state() or {}
    return cast("bytes", kap_kur(icerik, dek, baslik=durum_basligi(durum))), durum


# ---------------------------------------------------------------------------
# Yedek listesi
# ---------------------------------------------------------------------------
def test_yedek_listesi_en_yeniden_eskiye(tmp_path: Path, ortam: dict[str, Path]) -> None:
    eski = ortam["yedekler"] / "gunluk-2026-08-01.odbak"
    eski.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "eski"))[0])
    os.utime(eski, (1_000_000_000, 1_000_000_000))
    yeni = ortam["yedekler"] / "gunluk-2026-08-02.odbak"
    yeni.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"))[0])
    os.utime(yeni, (2_000_000_000, 2_000_000_000))
    # Uzantısı farklı dosyalar listeye girmez.
    (ortam["yedekler"] / "not.txt").write_text("ilgisiz", encoding="utf-8")

    yanit = APIClient().get(LISTE_URL)

    assert yanit.status_code == 200
    veri = yanit.json()
    assert veri["backup_dir"] == str(ortam["yedekler"])
    adlar = [satir["name"] for satir in veri["backups"]]
    assert adlar == ["gunluk-2026-08-02.odbak", "gunluk-2026-08-01.odbak"]
    # Yedekler daima şifrelidir; "şifreli mi" alanı artık yok (§13 D29). `kurtarma`
    # yedeği açan kurtarma anahtarının kimliğidir (TK10).
    assert set(veri["backups"][0]) == {"name", "size", "modified_at", "kurtarma"}
    assert all(satir["size"] > 0 and satir["modified_at"] for satir in veri["backups"])


def test_yedek_listesi_dizin_yokken_bos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ortam: dict[str, Path]
) -> None:
    monkeypatch.setenv(app_password.ENV_BACKUP_DIR, str(tmp_path / "yok"))

    yanit = APIClient().get(LISTE_URL)

    assert yanit.status_code == 200
    assert yanit.json()["backups"] == []


def _baslikli_yedek(tmp_path: Path, baslik: bytes) -> bytes:
    """Bu kurulumun DEK'iyle, verilen ham kurtarma başlığını gömen şifreli yedek."""
    return cast("bytes", kap_kur(_sqlite_baytlari(tmp_path, "kimlik"), TEST_DEK, baslik=baslik))


def _liste_satiri(ad: str) -> dict[str, Any]:
    yanit = APIClient().get(LISTE_URL)
    assert yanit.status_code == 200
    satirlar: list[dict[str, Any]] = yanit.json()["backups"]
    return next(satir for satir in satirlar if satir["name"] == ad)


def test_yedek_listesi_yedegi_acan_kurtarma_anahtarini_soyler(
    tmp_path: Path, ortam: dict[str, Path]
) -> None:
    """Tasarım §4.4.4, TK10: hangi kâğıdın hangi yedeği açtığı listede görünür.

    Kimlik güncel `guvenlik.json`'dan değil yedeğin gömülü başlığından okunur (burada
    güncel dosyanın anahtarı 1 numaralı, yedeğinki 3). Tarih başlıktaki ISO biçimiyle
    döner (arayüz gg.aa.yyyy yazar); başlığın tuzu ve sarmalı yanıta hiçbir biçimde
    girmez.
    """
    durum = app_password.read_state() or {}
    durum["kurtarma"].update(no=3, tarih="2026-11-01")
    baslik = recovery_header_from_state(durum)
    assert baslik is not None
    (ortam["yedekler"] / "gunluk-2026-11-02.odbak").write_bytes(
        _baslikli_yedek(tmp_path, json.dumps(baslik, ensure_ascii=False).encode("utf-8"))
    )

    satir = _liste_satiri("gunluk-2026-11-02.odbak")

    assert satir["kurtarma"] == {"no": 3, "tarih": "2026-11-01"}
    metin = APIClient().get(LISTE_URL).content.decode("utf-8")
    assert baslik["kurtarma"]["salt"] not in metin
    assert baslik["kurtarma"]["sarmal"] not in metin
    assert "salt" not in metin and "sarmal" not in metin and "kdf" not in metin


@pytest.mark.parametrize(
    "baslik",
    [
        b"",
        b"{bozuk",
        json.dumps({"surum": 1, "kdf": {}, "parola": {"salt": "eA==", "sarmal": "eA=="}}).encode(),
        # Kurtarma bölümü sarmalsız: başlık kullanılamaz, no/tarih olsa da gösterilmez.
        json.dumps({"surum": 2, "kdf": {}, "kurtarma": {"no": 4, "tarih": "2026-11-01"}}).encode(),
        # Derin iç içe JSON (40 KB; 1 MB sınırının altında): `json.loads` RecursionError
        # yükseltir; liste 500'e düşmez, satır kimliksiz görünür.
        b"[" * 20000 + b"]" * 20000,
    ],
    ids=["basliksiz", "bozuk_json", "sema_1", "sarmalsiz", "derin_ic_ice"],
)
def test_kullanilamayan_baslikta_kurtarma_kimligi_bostur(
    tmp_path: Path, ortam: dict[str, Path], baslik: bytes
) -> None:
    (ortam["yedekler"] / "eski.odbak").write_bytes(_baslikli_yedek(tmp_path, baslik))

    assert _liste_satiri("eski.odbak")["kurtarma"] is None


def test_yedek_listesi_tam_yedegi_de_baslikten_okur(tmp_path: Path, ortam: dict[str, Path]) -> None:
    """Kimlik başlıktadır: dosya bölümü taşıyan yedek de aynı okuyucudan geçer."""
    (ortam["yedekler"] / "tam.odbak").write_bytes(
        kap_kur(
            _sqlite_baytlari(tmp_path, "tam"),
            TEST_DEK,
            baslik=durum_basligi(app_password.read_state() or {}),
            manifesto=Manifesto(KAPSAM_TAM),
        )
    )

    assert _liste_satiri("tam.odbak")["kurtarma"] is not None


def test_deneme_yedegi_listede_kimliksiz_durur_geri_yuklenmez(ortam: dict[str, Path]) -> None:
    """Plan F1b-3 "Kap ve manifesto": `ODBAK\\x02` listeyi düşürmez, geri yüklemesi ayrı iletiyle
    400 döner; kapı kurulmaz."""
    (ortam["yedekler"] / "gunluk-2026-08-01.odbak").write_bytes(DENEME_MAGIC + bytes(200))

    assert _liste_satiri("gunluk-2026-08-01.odbak")["kurtarma"] is None
    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {"name": "gunluk-2026-08-01.odbak", "recovery_key": "UYDURMA-ANAHTAR"},
        format="json",
    )

    assert yanit.status_code == 400
    assert "deneme sürümüyle alınmış" in yanit.json()["message"]
    assert restart_gate.restart_required() is False


def test_bozuk_yedek_dosyasi_listeyi_dusurmez(tmp_path: Path, ortam: dict[str, Path]) -> None:
    """Yedek olmayan ya da kesik dosya listede kimliksiz görünür; liste 200 döner."""
    (ortam["yedekler"] / "yedek-degil.odbak").write_bytes(b"duz metin, yedek degil")
    tam = _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "kesik"))[0]
    (ortam["yedekler"] / "kesik.odbak").write_bytes(tam[:80])
    (ortam["yedekler"] / "saglam.odbak").write_bytes(tam)

    assert _liste_satiri("yedek-degil.odbak")["kurtarma"] is None
    assert _liste_satiri("kesik.odbak")["kurtarma"] is None
    assert _liste_satiri("saglam.odbak")["kurtarma"] == {
        "no": 1,
        "tarih": app_password.status()["recovery_key_date"],
    }


# ---------------------------------------------------------------------------
# Geri yükleme — ad ile (yedek klasöründen)
# ---------------------------------------------------------------------------
def test_addan_geri_yukleme_kapiyi_kurar(tmp_path: Path, ortam: dict[str, Path]) -> None:
    ortam["db"].write_bytes(_sqlite_baytlari(tmp_path, "eski"))
    yeni = _sqlite_baytlari(tmp_path, "yeni")
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(_sifreli_kapsayici(yeni)[0])

    yanit = APIClient().post(
        GERI_YUKLE_URL, {"name": "gunluk.odbak", "password": PAROLA}, format="json"
    )

    assert yanit.status_code == 200
    veri = yanit.json()
    assert veri["restart_required"] is True
    assert "encrypted" not in veri
    assert veri["old_db_name"].startswith("db-onceki-")
    assert ortam["db"].read_bytes() == yeni
    # Kapı kuruldu: bundan sonraki HER API isteği 503 restart_required döner.
    sonraki = APIClient().get(LISTE_URL)
    assert sonraki.status_code == 503
    assert sonraki.json()["code"] == "restart_required"
    # Bellekteki DEK eski veritabanına aitti; düşürüldü.
    assert crypto.is_unlocked() is False


def test_duz_sqlite_yedegi_400_ile_reddedilir(tmp_path: Path, ortam: dict[str, Path]) -> None:
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(_sqlite_baytlari(tmp_path, "duz"))

    yanit = APIClient().post(
        GERI_YUKLE_URL, {"name": "gunluk.odbak", "password": TEST_PAROLA}, format="json"
    )

    assert yanit.status_code == 400
    assert "şifrelenmemiş" in yanit.json()["message"]
    assert not ortam["db"].exists()
    assert restart_gate.restart_required() is False


def test_sirsiz_istek_400_ile_reddedilir(tmp_path: Path, ortam: dict[str, Path]) -> None:
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(
        _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"))[0]
    )

    yanit = APIClient().post(GERI_YUKLE_URL, {"name": "gunluk.odbak"}, format="json")

    assert yanit.status_code == 400
    assert (
        "program yöneticisi hesabının tanıtıcısı ve parolası ya da kurtarma anahtarı"
        in yanit.json()["message"]
    )


@pytest.mark.parametrize(
    "kdf",
    [{"time_cost": "x"}, {"time_cost": None}, {"parallelism": 0}, {"memory_cost": 2**40}],
    ids=["metin", "bos", "kulvar_sifir", "bellek_uint32_ustu"],
)
def test_sinir_disi_baslik_kdfsi_400_ve_turkce_ileti_verir(
    tmp_path: Path, ortam: dict[str, Path], kdf: dict[str, Any]
) -> None:
    """Hazırlanmış başlık canlı uçta 500 ya da "invalid literal for int()" iletisi vermez."""
    dek = crypto.new_data_key()
    durum = app_password._build_state(
        dek,
        hesap_id="5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9",
        tanitici=TEST_TANITICI,
        password="Baska-Parola-7",
        recovery_key=TEST_KURTARMA_ANAHTARI,
    )
    (ortam["yedekler"] / "hazirlanmis.odbak").write_bytes(
        kap_kur(
            _sqlite_baytlari(tmp_path, "yabanci"),
            dek,
            baslik=durum_basligi({**durum, "kdf": {**durum["kdf"], **kdf}}),
        )
    )

    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {"name": "hazirlanmis.odbak", "recovery_key": TEST_KURTARMA_ANAHTARI},
        format="json",
    )

    assert yanit.status_code == 400
    assert yanit.json()["message"].startswith("Yedek açılamadı")
    assert not ortam["db"].exists()
    assert restart_gate.restart_required() is False


def test_yol_ayracli_ad_reddedilir(tmp_path: Path, ortam: dict[str, Path]) -> None:
    gizli = ortam["yedekler"].parent / "disarida.odbak"
    gizli.write_bytes(_sqlite_baytlari(tmp_path, "disarida"))

    for ad in ("../disarida.odbak", "..\\disarida.odbak", "alt/dosya.odbak", "duz-ad"):
        yanit = APIClient().post(GERI_YUKLE_URL, {"name": ad}, format="json")
        assert yanit.status_code == 400, ad
        assert "Geçerli bir yedek dosyası adı" in yanit.json()["message"]
    assert not ortam["db"].exists()


def test_olmayan_ad_turkce_hata_verir(ortam: dict[str, Path]) -> None:
    yanit = APIClient().post(GERI_YUKLE_URL, {"name": "yok.odbak"}, format="json")

    assert yanit.status_code == 400
    assert "böyle bir dosya yok" in yanit.json()["message"]


# ---------------------------------------------------------------------------
# Geri yükleme — dosya yükleyerek
# ---------------------------------------------------------------------------
def test_yuklenen_sifreli_dosya_oturum_hesabinin_parolasiyla_geri_yuklenir(
    tmp_path: Path, ortam: dict[str, Path]
) -> None:
    """Parola yolunda hesap verilmezse oturumdaki hesap kullanılır (aynı bilgisayar)."""
    icerik = _sqlite_baytlari(tmp_path, "gizli")
    kapsayici, _durum = _sifreli_kapsayici(icerik)
    once = (ortam["veri"] / "guvenlik.json").read_bytes()

    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {"file": SimpleUploadedFile("elden.odbak", kapsayici), "password": PAROLA},
        format="multipart",
    )

    assert yanit.status_code == 200, yanit.json()
    assert yanit.json()["state_written"] is False  # güncel dosya açtı: dokunulmadı
    assert ortam["db"].read_bytes() == icerik
    assert (ortam["veri"] / "guvenlik.json").read_bytes() == once
    assert not list(ortam["yedekler"].glob(".yukleme-*"))


def test_yuklenen_yedek_genel_yukleme_sinirina_takilmaz(
    tmp_path: Path, ortam: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Genel bellek işleyicisi ve sınırı bu ucu kesmez (plan F1b-3 "Dosya deposu"): yedek
    yükleme sınırından büyük olabilir, sınırı aşan yedek geçici dosyaya iner."""
    icerik = _sqlite_baytlari(tmp_path, "gizli")
    kapsayici, _durum = _sifreli_kapsayici(icerik)
    monkeypatch.setattr(settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", len(kapsayici) // 2)

    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {"file": SimpleUploadedFile("elden.odbak", kapsayici), "password": PAROLA},
        format="multipart",
    )

    assert yanit.status_code == 200, yanit.json()
    assert ortam["db"].read_bytes() == icerik


def test_baska_kurulumun_yedegi_yalniz_kurtarma_anahtariyla_acilir(
    tmp_path: Path, ortam: dict[str, Path]
) -> None:
    """TK10: başlıkta hesap sarmalı yok; açılınca `guvenlik.json` yalnız kurtarma bölümüdür."""
    icerik = _sqlite_baytlari(tmp_path, "gizli")
    kapsayici, durum = _sifreli_kapsayici(icerik, yabanci=True)
    (ortam["yedekler"] / "elden.odbak").write_bytes(kapsayici)

    parolali = APIClient().post(
        GERI_YUKLE_URL,
        {"name": "elden.odbak", "hesap": TEST_TANITICI, "password": "Baska-Parola-7"},
        format="json",
    )
    assert parolali.status_code == 400
    assert "1 numaralı" in parolali.json()["message"]

    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {"name": "elden.odbak", "recovery_key": TEST_KURTARMA_ANAHTARI},
        format="json",
    )

    assert yanit.status_code == 200, yanit.json()
    assert yanit.json()["state_written"] is True
    assert ortam["db"].read_bytes() == icerik
    yazilan = json.loads((ortam["veri"] / "guvenlik.json").read_text(encoding="utf-8"))
    assert yazilan["hesaplar"] == []
    assert yazilan["kurtarma"]["sarmal"] == durum["kurtarma"]["sarmal"]
    assert yazilan["kurtarma"]["dogrulandi"]


def test_yanlis_parola_400_kapi_kurulmaz(tmp_path: Path, ortam: dict[str, Path]) -> None:
    orijinal = _sqlite_baytlari(tmp_path, "orijinal")
    ortam["db"].write_bytes(orijinal)
    kapsayici, _durum = _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"))
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(kapsayici)

    yanit = APIClient().post(
        GERI_YUKLE_URL, {"name": "gunluk.odbak", "password": "Yanlis-Parola-9"}, format="json"
    )

    assert yanit.status_code == 400
    assert "açılamadı" in yanit.json()["message"]
    assert ortam["db"].read_bytes() == orijinal
    # Kapı KURULMADI: kullanıcı yeniden deneyebilir.
    assert APIClient().get(LISTE_URL).status_code == 200
    # Başarısız denemenin geçici yükleme dosyası da kalmaz.
    assert not list(ortam["yedekler"].glob(".yukleme-*"))


# ---------------------------------------------------------------------------
# İstek doğrulama + tesisat
# ---------------------------------------------------------------------------
def test_ad_ve_dosya_birlikte_veya_hic_verilmezse_400(
    tmp_path: Path, ortam: dict[str, Path]
) -> None:
    icerik = _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"))[0]
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(icerik)

    ikisi = APIClient().post(
        GERI_YUKLE_URL,
        {"name": "gunluk.odbak", "file": SimpleUploadedFile("elden.odbak", icerik)},
        format="multipart",
    )
    hicbiri = APIClient().post(GERI_YUKLE_URL, {}, format="json")

    assert ikisi.status_code == 400
    assert hicbiri.status_code == 400
    assert not ortam["db"].exists()


def test_bellek_ici_veritabani_reddedilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ortam: dict[str, Path]
) -> None:
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", ":memory:")
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(
        _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"))[0]
    )

    yanit = APIClient().post(
        GERI_YUKLE_URL, {"name": "gunluk.odbak", "password": PAROLA}, format="json"
    )

    assert yanit.status_code == 400
    assert "dosya tabanlı değil" in yanit.json()["message"]


def test_takas_oncesi_baglantilar_kapatilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ortam: dict[str, Path]
) -> None:
    """Windows'ta açık SQLite tanıtıcısı `os.replace`'i düşürür; sıra sözleşmedir."""
    cagrildi: list[str] = []
    monkeypatch.setattr(connections, "close_all", lambda: cagrildi.append("kapat"))
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(
        _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"))[0]
    )

    sonuc = live_restore.restore_and_require_restart(name="gunluk.odbak", password=PAROLA)

    assert cagrildi == ["kapat"]
    assert sonuc["restart_required"] is True
    assert restart_gate.restart_required() is True


# ---------------------------------------------------------------------------
# Ortak bakım kapısı (tasarım §4.1, §13 D3)
# ---------------------------------------------------------------------------
def test_bakim_kapisi_takastan_once_kapanir_ve_basarida_kapali_kalir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ortam: dict[str, Path]
) -> None:
    """Geri yükleme sürerken gün işi (günlük yedek) başlamaz; başarıda kapı program
    yeniden açılana dek kapalı kalır."""
    kapi = bakim.BakimKapisi()
    monkeypatch.setattr(bakim, "KAPI", kapi)
    ortam["db"].write_bytes(_sqlite_baytlari(tmp_path, "eski"))
    gorulen: list[bool] = []
    asil = backup_restore.restore_database

    def izleyen(*args: Any, **kwargs: Any) -> Any:
        gorulen.append(kapi.bakimda)  # takas anında kapı kapalı mı?
        with kapi.is_() as izin:  # bu sırada gelen gün işi başlamaz
            gorulen.append(izin)
        return asil(*args, **kwargs)

    monkeypatch.setattr(backup_restore, "restore_database", izleyen)
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(
        _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"))[0]
    )

    live_restore.restore_and_require_restart(name="gunluk.odbak", password=PAROLA)

    assert gorulen == [True, False]
    assert kapi.bakimda is True


def test_basarisiz_geri_yuklemede_bakim_kapisi_yeniden_acilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ortam: dict[str, Path]
) -> None:
    kapi = bakim.BakimKapisi()
    monkeypatch.setattr(bakim, "KAPI", kapi)
    ortam["db"].write_bytes(_sqlite_baytlari(tmp_path, "eski"))
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(
        _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"))[0]
    )

    yanit = APIClient().post(
        GERI_YUKLE_URL, {"name": "gunluk.odbak", "password": "Yanlis-Parola-9"}, format="json"
    )

    assert yanit.status_code == 400
    assert kapi.bakimda is False  # hedefe dokunulmadı; gün işleri yeniden koşabilir


def test_yedek_adi_gecersizse_bakim_kapisina_dokunulmaz(
    monkeypatch: pytest.MonkeyPatch, ortam: dict[str, Path]
) -> None:
    """Ad doğrulaması kapıdan önce: yanlış tıklama gün işlerini durdurmaz."""
    kapi = bakim.BakimKapisi()
    monkeypatch.setattr(bakim, "KAPI", kapi)

    yanit = APIClient().post(
        GERI_YUKLE_URL, {"name": "../disari.odbak", "password": PAROLA}, format="json"
    )

    assert yanit.status_code == 400
    assert kapi.bakimda is False


# ---------------------------------------------------------------------------
# Uzun iş sayacı (tasarım §4.2, §4.4.3; plan F1b-1 "Oturum")
# ---------------------------------------------------------------------------
def test_geri_yukleme_uzun_is_olarak_sayilir_ve_basarida_oturum_kapanir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ortam: dict[str, Path]
) -> None:
    """Geri yükleme sürerken oturumun kilidi ertelenir (DEK işin ortasında silinmez);
    başarıda oturum HEMEN kapanır: DEK artık bu veritabanına ait değildir."""
    from apps.okul.oturum import OTURUM

    ortam["db"].write_bytes(_sqlite_baytlari(tmp_path, "eski"))
    gorulen: list[tuple[int, str]] = []
    asil = backup_restore.restore_database

    def izleyen(*args: Any, **kwargs: Any) -> Any:
        gorulen.append((bakim.UZUN_ISLER.sayi, OTURUM.kilitle(neden="elle")))
        return asil(*args, **kwargs)

    monkeypatch.setattr(backup_restore, "restore_database", izleyen)
    (ortam["yedekler"] / "gunluk.odbak").write_bytes(
        _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"))[0]
    )

    live_restore.restore_and_require_restart(name="gunluk.odbak", password=PAROLA)

    assert gorulen == [(1, "ertelendi")]  # iş sürerken Kilitle ertelendi
    assert bakim.UZUN_ISLER.sayi == 0
    assert OTURUM.acik_mi() is False
    assert crypto.is_unlocked() is False
