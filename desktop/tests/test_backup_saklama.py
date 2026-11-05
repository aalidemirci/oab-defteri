"""Rotasyon kümesi ve KVKK tetiğinin araçları (tasarım §4.4.7, §5.4, §10.6; plan F1b-3).

- Rotasyon tek işlevdir, kapalı önek kümesi tek sabittedir: her önek 15. günde silinir,
  `pre-migrate` son 5'le tutulur; adı desene uymayan dosyaya dokunulmaz, yaş addaki gündendir;
  tek dosyanın silinememesi rotasyonu düşürmez.
- `db-onceki` veri dizinindedir, `-wal`/`-shm` eşleriyle karar görür.
- `pre-anonim-<tarih>-<saat>.odbak` tetikten ÖNCE alınır, şifrelidir ve rotasyonda
  günlük yedekler gibi **14 gün** tutulur; aynı gün ikinci tetik ayrı dosya alır.
- Tetik, tetik anından ESKİ `pre-migrate` yedeklerini siler (yazılma zamanına göre);
  sonra alınanlar ve başka önekli dosyalar kalır. Tetiğe bağlanması F4'tedir.
- Anahtar yoksa yedek alınmaz (`None`) — çağıran tetiği çalıştırmaz.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from desktop.backup import (
    DAILY_PREFIX,
    DEFAULT_KEEP_DAYS,
    DEFAULT_KEEP_PRE_MIGRATE,
    OLD_DB_PREFIX,
    PRE_ANONIM_PREFIX,
    PRE_DEK_YENILEME_PREFIX,
    PRE_KAPANIS_PREFIX,
    PRE_MIGRATE_PREFIX,
    PRE_PAROLA_PREFIX,
    ROTASYON_KUMESI,
    daily_backup_path,
    old_database_stamp,
    pre_anonim_backup,
    pre_migrate_backup_path,
    pre_migrate_before,
    remove_pre_migrate_before,
    remove_pre_migrate_named,
    rotate_backups,
    wal_bosalt,
)
from desktop.backup_crypto import MAGIC
from desktop.tests.test_backup import _db_olustur


def test_pre_anonim_yedegi_sifreli_ve_saatli(tmp_path: Path) -> None:
    db = tmp_path / "veri" / "db.sqlite3"
    _db_olustur(db)
    dizin = tmp_path / "yedekler"

    birinci = pre_anonim_backup(db, dizin, now=datetime(2028, 9, 24, 10, 15, 30))
    ikinci = pre_anonim_backup(db, dizin, now=datetime(2028, 9, 24, 10, 15, 30))

    assert birinci is not None and ikinci is not None
    assert birinci.name == f"{PRE_ANONIM_PREFIX}-2028-09-24-101530.odbak"
    assert ikinci != birinci and ikinci.name.startswith(f"{PRE_ANONIM_PREFIX}-2028-09-24-")
    assert birinci.read_bytes()[: len(MAGIC)] == MAGIC


def test_anahtar_yoksa_pre_anonim_yedegi_alinmaz(tmp_path: Path) -> None:
    db = tmp_path / "veri" / "db.sqlite3"
    _db_olustur(db, parola_kurulu=False)
    assert pre_anonim_backup(db, tmp_path / "yedekler") is None
    assert not list((tmp_path / "yedekler").glob("*"))


def test_anahtar_dizini_ayri_verilebilir(tmp_path: Path) -> None:
    """Çalışan programın backend'i güvenlik dizinini ayrıca verir (`data_dir`)."""
    anahtarlar = tmp_path / "anahtar"
    _db_olustur(anahtarlar / "db.sqlite3")
    db = tmp_path / "baska" / "db.sqlite3"
    _db_olustur(db, parola_kurulu=False)
    assert pre_anonim_backup(db, tmp_path / "yedekler", data_dir=anahtarlar) is not None


def test_pre_anonim_rotasyonda_on_dort_gun(tmp_path: Path) -> None:
    for ad in (
        "pre-anonim-2026-09-01-090000.odbak",
        "pre-anonim-2026-09-20-090000.odbak",
        "gunluk-2026-09-01.odbak",
        "elle-konmus-pre-anonim.odbak",
    ):
        (tmp_path / ad).write_bytes(b"x")

    silinen = rotate_backups(tmp_path, tmp_path / "veri", today=date(2026, 9, 27))

    assert sorted(p.name for p in silinen) == [
        "gunluk-2026-09-01.odbak",
        "pre-anonim-2026-09-01-090000.odbak",
    ]
    assert (tmp_path / "pre-anonim-2026-09-20-090000.odbak").exists()
    assert (tmp_path / "elle-konmus-pre-anonim.odbak").exists()


def test_tetik_anindan_eski_pre_migrate_silinir(tmp_path: Path) -> None:
    an = datetime(2028, 9, 24, 12, 0, 0)
    eski = tmp_path / "pre-migrate-2026.9.0-2026-09-01.odbak"
    ayni_gun_sonra = tmp_path / "pre-migrate-2028.9.0-2028-09-24.odbak"
    gunluk = tmp_path / "gunluk-2026-09-01.odbak"
    for yol in (eski, ayni_gun_sonra, gunluk):
        yol.write_bytes(b"x")
    os.utime(eski, (an.timestamp() - 86400, an.timestamp() - 86400))
    os.utime(ayni_gun_sonra, (an.timestamp() + 60, an.timestamp() + 60))
    os.utime(gunluk, (an.timestamp() - 86400, an.timestamp() - 86400))

    silinen = remove_pre_migrate_before(tmp_path, an)

    assert silinen == [eski]
    assert ayni_gun_sonra.exists() and gunluk.exists()
    assert remove_pre_migrate_before(tmp_path / "yok", an) == []


def test_ada_gore_silme_yalniz_pre_migrate_adlarina_dokunur(tmp_path: Path) -> None:
    """Aile iskeletinin düzeltmesi: gün değişimi kapısı silinemeyenleri ADIYLA yeniden dener.

    Dosya zamanına bakılmaz; yol ayırıcısı taşıyan ya da `pre-migrate-*.odbak` biçiminde
    olmayan ada dokunulmaz; klasörde olmayan ad beklemede kalmaz.
    """
    hedef = tmp_path / "pre-migrate-2026.9.0-2026-09-01.odbak"
    gunluk = tmp_path / "gunluk-2026-09-01.odbak"
    for yol in (hedef, gunluk):
        yol.write_bytes(b"x")
    ust = tmp_path.parent / "pre-migrate-disarida.odbak"
    ust.write_bytes(b"x")

    silinen, kalan = remove_pre_migrate_named(
        tmp_path,
        [
            hedef.name,
            gunluk.name,
            "../pre-migrate-disarida.odbak",
            "pre-migrate-olmayan.odbak",
        ],
    )

    assert silinen == [hedef] and kalan == []
    assert gunluk.exists() and ust.exists()
    ust.unlink()


def test_pre_migrate_before_silmez_yalniz_listeler(tmp_path: Path) -> None:
    an = datetime(2028, 9, 24, 12, 0, 0)
    eski = tmp_path / "pre-migrate-2026.9.0-2026-09-01.odbak"
    eski.write_bytes(b"x")
    os.utime(eski, (an.timestamp() - 60, an.timestamp() - 60))

    assert pre_migrate_before(tmp_path, an) == [eski]
    assert eski.exists()


# ------------------------------------------------- rotasyon kümesi (§4.4.7; §13 D49)

_BUGUN = date(2026, 9, 27)
#: Kümenin gün sınırıyla tutulan önekleri: (yedek adı biçimi, veri dizininde mi).
_GUNLE_TUTULANLAR: dict[str, tuple[str, bool]] = {
    "gunluk": ("gunluk-{gun}.odbak", False),
    "pre_parola": ("pre-parola-acilis-{gun}-101530.odbak", False),
    "pre_anonim": ("pre-anonim-{gun}-101530.odbak", False),
    "pre_kapanis": ("pre-kapanis-{gun}.odbak", False),
    "pre_dek_yenileme": ("pre-dek-yenileme-{gun}.odbak", False),
    "db_onceki": ("db-onceki-{gun}-101530.sqlite3", True),
}


@pytest.fixture
def dizinler(tmp_path: Path) -> tuple[Path, Path]:
    yedekler = tmp_path / "backups"
    veri = tmp_path / "data"
    yedekler.mkdir()
    veri.mkdir()
    return yedekler, veri


def _gun_once(gun_sayisi: int) -> str:
    return (_BUGUN - timedelta(days=gun_sayisi)).isoformat()


def _kilitli_ad(monkeypatch: pytest.MonkeyPatch, *adlar: str) -> None:
    """Bu adlar başka programda açıkmış gibi: silme `PermissionError` verir (Windows)."""
    ozgun = Path.unlink

    def sil(yol: Path, missing_ok: bool = False) -> None:
        if yol.name in adlar:
            raise PermissionError("başka bir programda açık")
        ozgun(yol, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", sil)


def test_rotasyon_onek_kumesi() -> None:
    """Tasarım §2.3.2, §4.4.7: küme kapalıdır; önek eklemek bu testi ve 15. gün testini değiştirir."""
    assert {kural.onek: (kural.adetle, kural.veri_dizininde) for kural in ROTASYON_KUMESI} == {
        DAILY_PREFIX: (False, False),
        PRE_PAROLA_PREFIX: (False, False),
        PRE_ANONIM_PREFIX: (False, False),
        PRE_KAPANIS_PREFIX: (False, False),
        PRE_DEK_YENILEME_PREFIX: (False, False),
        PRE_MIGRATE_PREFIX: (True, False),
        OLD_DB_PREFIX: (False, True),
    }
    assert len(ROTASYON_KUMESI) == 7
    assert (DEFAULT_KEEP_DAYS, DEFAULT_KEEP_PRE_MIGRATE) == (14, 5)
    # Testin 15. gün tablosu kümeyi tam kapsar (`pre-migrate` adetledir).
    assert {ad.replace("_", "-") for ad in _GUNLE_TUTULANLAR} == {
        kural.onek for kural in ROTASYON_KUMESI if not kural.adetle
    }


def test_kume_disi_onek_rotasyona_girmez(dizinler: tuple[Path, Path]) -> None:
    yedekler, veri = dizinler
    yabanci = yedekler / "pre-yeni-is-2020-01-01.odbak"
    yabanci.write_bytes(b"x")

    assert rotate_backups(yedekler, veri, today=_BUGUN) == []
    assert yabanci.exists()


@pytest.mark.parametrize("onek", list(_GUNLE_TUTULANLAR))
def test_her_onekte_15_gun_silme(onek: str, dizinler: tuple[Path, Path]) -> None:
    """14. günde durur, 15. günde silinir; yaş addaki gündendir (tasarım §4.4.7 madde 1)."""
    yedekler, veri = dizinler
    bicim, veri_dizininde = _GUNLE_TUTULANLAR[onek]
    dizin = veri if veri_dizininde else yedekler
    on_dorduncu = dizin / bicim.format(gun=_gun_once(14))
    on_besinci = dizin / bicim.format(gun=_gun_once(15))
    for yol in (on_dorduncu, on_besinci):
        yol.write_bytes(b"x")

    assert rotate_backups(yedekler, veri, today=_BUGUN) == [on_besinci]

    assert on_dorduncu.exists() and not on_besinci.exists()


@pytest.mark.parametrize("onek", list(_GUNLE_TUTULANLAR))
def test_yas_dosya_zamanindan_degil_addaki_gunden_okunur(
    onek: str, dizinler: tuple[Path, Path]
) -> None:
    """`os.replace` dosya zamanını korur: dün kenara alınan veritabanı aylar önceki zamanı taşır."""
    yedekler, veri = dizinler
    bicim, veri_dizininde = _GUNLE_TUTULANLAR[onek]
    dizin = veri if veri_dizininde else yedekler
    yeni = dizin / bicim.format(gun=_gun_once(1))
    yeni.write_bytes(b"x")
    os.utime(yeni, (0, 0))

    assert rotate_backups(yedekler, veri, today=_BUGUN) == []
    assert yeni.exists()


def test_uretilen_adlar_kumenin_desenine_uyar(dizinler: tuple[Path, Path], tmp_path: Path) -> None:
    """Üreticiler kümenin tanımadığı ad yazarsa o yedek sessizce süresiz kalırdı."""
    yedekler, _veri = dizinler
    desen = {kural.onek: kural.desen for kural in ROTASYON_KUMESI}
    db = tmp_path / "veri" / "db.sqlite3"
    _db_olustur(db)
    anonim = pre_anonim_backup(db, yedekler, now=datetime(2026, 9, 24, 10, 15, 30))
    ikinci = pre_anonim_backup(db, yedekler, now=datetime(2026, 9, 24, 10, 15, 30))
    assert anonim is not None and ikinci is not None

    assert desen[DAILY_PREFIX].fullmatch(daily_backup_path(yedekler, _BUGUN).name)
    goc = pre_migrate_backup_path(yedekler, "1.0/rc:1", _BUGUN).name
    assert desen[PRE_MIGRATE_PREFIX].fullmatch(goc)
    assert desen[PRE_ANONIM_PREFIX].fullmatch(anonim.name)
    assert desen[PRE_ANONIM_PREFIX].fullmatch(ikinci.name)


@pytest.mark.parametrize(
    "ad",
    [
        "gunluk-2020-01-01 Uydurgül Masalcıoğlu.odbak",
        "kopya-gunluk-2020-01-01.odbak",
        "gunluk-2020-01-01.odbak.tmp",
        "gunluk-2020-01-01.sqlite3",
        "gunluk-2020-13-40.odbak",
        "gunluk-2020-01-01xodbak",
        "gunluk-yil-2020.odbak",
        "pre-parola-2020-01-01-101530.odbak",
        "pre-parola-Uydurgul-2020-01-01-101530.odbak",
        "pre-anonim-2020-01-01.odbak",
        "pre-kapanis-2020-01-01-Uydurgul.odbak",
        "pre-dek-yenileme-2020-01-01-101530.odbak",
        "pre-migrate-2020-01-01.odbak",
        "pre-migrate-1.0.0 kopya-2020-01-01.odbak",
    ],
)
def test_adi_desene_uymayan_yedek_dosyasina_dokunulmaz(
    ad: str, dizinler: tuple[Path, Path]
) -> None:
    yedekler, veri = dizinler
    yol = yedekler / ad
    yol.write_bytes(b"x")

    assert rotate_backups(yedekler, veri, today=_BUGUN, keep_pre_migrate=0) == []
    assert yol.exists()


@pytest.mark.parametrize(
    "ad",
    [
        "db-onceki-elle.sqlite3",
        "db-onceki-2020-01-01.sqlite3",
        "db-onceki-2020-13-40-101530.sqlite3",
        "db-onceki-2020-01-01-999999.sqlite3",
        "db-onceki-2020-01-01-101530.sqlite3.bak",
        "db-onceki-2020-01-01-101530.sqlite3-journal",
        "db-onceki-2020-01-01-101530.odbak",
        "kopya-db-onceki-2020-01-01-101530.sqlite3",
        "db.sqlite3",
    ],
)
def test_adi_desene_uymayan_veri_dizini_dosyasina_dokunulmaz(
    ad: str, dizinler: tuple[Path, Path]
) -> None:
    yedekler, veri = dizinler
    yol = veri / ad
    yol.write_bytes(b"x")

    assert rotate_backups(yedekler, veri, today=_BUGUN) == []
    assert yol.exists()


def test_onekler_yalniz_kendi_dizininde_aranir(dizinler: tuple[Path, Path]) -> None:
    """Veri dizinindeki `gunluk-` ve yedek dizinindeki `db-onceki-` programın yazdığı dosya değildir."""
    yedekler, veri = dizinler
    veride = veri / "gunluk-2020-01-01.odbak"
    yedekte = yedekler / "db-onceki-2020-01-01-101530.sqlite3"
    # Veri dizinindeki yabancı dosya `pre-migrate`'in son 5 sayısına da girmez.
    veride_goc = veri / "pre-migrate-9.9.9-2026-09-01.odbak"
    gocler = [yedekler / f"pre-migrate-0.{i}.0-2026-01-0{i}.odbak" for i in range(1, 6)]
    for yol in (veride, yedekte, veride_goc, *gocler):
        yol.write_bytes(b"x")

    assert rotate_backups(yedekler, veri, today=_BUGUN) == []
    assert veride.exists() and yedekte.exists() and veride_goc.exists()
    assert all(yol.exists() for yol in gocler)


def test_pre_migrate_gunle_degil_son_besle_tutulur(dizinler: tuple[Path, Path]) -> None:
    """Haftalar sonra fark edilen yükseltme sorunu için: 15 günlük olsa da son 5 kalır."""
    yedekler, veri = dizinler
    adlar = [f"pre-migrate-0.{i}.0-2026-0{i}-01.odbak" for i in range(1, 8)]
    for ad in adlar:
        (yedekler / ad).write_bytes(b"x")

    silinen = rotate_backups(yedekler, veri, today=_BUGUN)

    assert sorted(yol.name for yol in silinen) == adlar[:2]
    assert sorted(yol.name for yol in yedekler.iterdir()) == adlar[2:]


def test_tek_dosya_silinemezse_rotasyon_surer_ad_gunluge_yazilir(
    dizinler: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """Windows'ta kilitli dosya rotasyonu düşürmez (plan F1b-3); kalan dosya yedek sayılmaz."""
    yedekler, veri = dizinler
    kilitli = yedekler / "gunluk-2020-01-01.odbak"
    goc_kilitli = yedekler / "pre-migrate-0.1.0-2020-01-01.odbak"
    ardindaki = yedekler / "gunluk-2020-01-02.odbak"
    baska_onek = yedekler / "pre-anonim-2020-01-01-101530.odbak"
    onceki = veri / "db-onceki-2020-01-01-101530.sqlite3"
    for yol in (kilitli, goc_kilitli, ardindaki, baska_onek, onceki):
        yol.write_bytes(b"x")
    _kilitli_ad(monkeypatch, kilitli.name, goc_kilitli.name)

    silinen = rotate_backups(yedekler, veri, today=_BUGUN, keep_pre_migrate=0)

    assert sorted(silinen) == sorted([ardindaki, baska_onek, onceki])
    assert kilitli.exists() and goc_kilitli.exists()
    uyarilar = [kayit.getMessage() for kayit in od_gunlugu if kayit.levelno == logging.WARNING]
    assert sorted(uyarilar) == sorted(
        f"Yedek silinemedi: {ad}" for ad in (kilitli.name, goc_kilitli.name)
    )


def test_silinemeyen_elle_adli_yedegin_adi_gunluge_yazilmaz(
    dizinler: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """Elle konmuş dosyanın adı serbest metindir (R1); program adı günlüğe adıyla düşmeye sürer."""
    yedekler, veri = dizinler
    elle = yedekler / "pre-migrate-Uydurgul-Masalcioglu-2020-01-01.odbak"
    program = yedekler / "pre-migrate-2026.1.0-alpha.1-2020-01-02.odbak"
    ardindaki = yedekler / "pre-migrate-0.1.0-2020-01-03.odbak"
    for yol in (elle, program, ardindaki):
        yol.write_bytes(b"x")
    _kilitli_ad(monkeypatch, elle.name, program.name)

    silinen = rotate_backups(yedekler, veri, today=_BUGUN, keep_pre_migrate=0)

    assert silinen == [ardindaki]
    assert elle.exists() and program.exists()
    uyarilar = [kayit.getMessage() for kayit in od_gunlugu if kayit.levelno == logging.WARNING]
    assert sorted(uyarilar) == sorted(
        ["Elle adlandırılmış bir yedek silinemedi.", f"Yedek silinemedi: {program.name}"]
    )
    assert not any("Uydurgul" in kayit.getMessage() for kayit in od_gunlugu)


def test_dizin_okunamazsa_oteki_dizinin_rotasyonu_surer(
    dizinler: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    od_gunlugu: list[logging.LogRecord],
) -> None:
    yedekler, veri = dizinler
    gunluk = yedekler / "gunluk-2020-01-01.odbak"
    gunluk.write_bytes(b"x")
    ozgun = Path.iterdir

    def listele(yol: Path) -> Any:
        if yol == veri:
            raise PermissionError("erişim yok")
        return ozgun(yol)

    monkeypatch.setattr(Path, "iterdir", listele)

    assert rotate_backups(yedekler, veri, today=_BUGUN) == [gunluk]
    assert any("dizin okunamadı" in kayit.getMessage() for kayit in od_gunlugu)


# ------------------------------------------- db-onceki eşleri (§4.4.7; plan F1b-3)


def test_db_onceki_esleriyle_silinir_listede_yalniz_kendisi_doner(
    dizinler: tuple[Path, Path],
) -> None:
    """`YEDEK` satırı dosya başınadır: eşler silinir, `-wal` adı kayda ayrı olay olarak düşmez."""
    yedekler, veri = dizinler
    ana = veri / "db-onceki-2020-01-01-101530.sqlite3"
    esler = [ana.with_name(ana.name + ek) for ek in ("-wal", "-shm")]
    for yol in (ana, *esler):
        yol.write_bytes(b"x")

    assert rotate_backups(yedekler, veri, today=_BUGUN) == [ana]
    assert not any(yol.exists() for yol in (ana, *esler))


def test_db_onceki_silinemezse_esleri_de_kalir_ve_rotasyon_surer(
    dizinler: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """Kalan kopyanın işlenmiş sayfaları `-wal`'da olabilir: eşini silmek onu eksik bırakırdı."""
    yedekler, veri = dizinler
    kilitli = veri / "db-onceki-2020-01-01-101530.sqlite3"
    esler = [kilitli.with_name(kilitli.name + ek) for ek in ("-wal", "-shm")]
    ikinci = veri / "db-onceki-2020-01-02-101530.sqlite3"
    ikinci_es = ikinci.with_name(ikinci.name + "-wal")
    for yol in (kilitli, *esler, ikinci, ikinci_es):
        yol.write_bytes(b"x")
    _kilitli_ad(monkeypatch, kilitli.name)

    assert rotate_backups(yedekler, veri, today=_BUGUN) == [ikinci]

    assert kilitli.exists() and all(yol.exists() for yol in esler)
    assert not ikinci.exists() and not ikinci_es.exists()
    assert any(kilitli.name in kayit.getMessage() for kayit in od_gunlugu)


def test_tek_kalmis_es_de_sureden_sonra_silinir_listede_donmez(
    dizinler: tuple[Path, Path],
) -> None:
    yedekler, veri = dizinler
    es = veri / "db-onceki-2020-01-01-101530.sqlite3-wal"
    es.write_bytes(b"x")

    assert rotate_backups(yedekler, veri, today=_BUGUN) == []
    assert not es.exists()


def test_db_onceki_damgasi_gecerli_tarih_ister() -> None:
    assert old_database_stamp("db-onceki-2026-09-01-101530.sqlite3") == datetime(
        2026, 9, 1, 10, 15, 30
    )
    assert old_database_stamp("db-onceki-2026-09-01-101530.sqlite3-wal") == datetime(
        2026, 9, 1, 10, 15, 30
    )
    assert old_database_stamp("db-onceki-2026-09-01-251530.sqlite3") is None
    assert old_database_stamp("db-onceki-2026-09-01-101530.sqlite3\n") is None


# ------------------------------------------- KVKK tetiği araçları (§4.4.7 madde 2)


def _bekleyen_wal(db: Path) -> sqlite3.Connection:
    """İşlenmiş sayfası `-wal`'da bekleyen veritabanı; açık bağlantı WAL'i tutar."""
    baglanti = sqlite3.connect(db)
    baglanti.execute("PRAGMA journal_mode=WAL")
    baglanti.execute("CREATE TABLE kisi (ad TEXT)")
    baglanti.execute("INSERT INTO kisi VALUES ('Uydurgül Masalcıoğlu')")
    baglanti.commit()
    return baglanti


def test_kvkk_tetiginden_eski_pre_migrate_silinir(tmp_path: Path) -> None:
    """Tasarım §4.4.7 madde 2, §13 D49: silmeden sonra WAL kırpılır, tetik anından eski güncelleme
    yedekleri adıyla silinir. Silinecekler tetik ANINDA belirlenir: saat sonradan kayıp tetikten
    sonraki yedeği "eski" gösterse de o yedek listede olmadığı için kalır."""
    yedekler = tmp_path / "backups"
    yedekler.mkdir()
    an = datetime(2028, 9, 24, 12, 0, 0)
    eski = yedekler / "pre-migrate-0.1.0-2028-09-01.odbak"
    silinemeyen = yedekler / "pre-migrate-0.2.0-2028-09-02.odbak"
    sonraki = yedekler / "pre-migrate-0.3.0-2028-09-24.odbak"
    gunluk = yedekler / "gunluk-2028-09-01.odbak"
    for yol in (eski, silinemeyen, sonraki, gunluk):
        yol.write_bytes(b"x")
    os.utime(eski, (an.timestamp() - 86_400, an.timestamp() - 86_400))
    os.utime(silinemeyen, (an.timestamp() - 86_400, an.timestamp() - 86_400))
    os.utime(sonraki, (an.timestamp() + 60, an.timestamp() + 60))
    os.utime(gunluk, (an.timestamp() - 86_400, an.timestamp() - 86_400))
    db = tmp_path / "db.sqlite3"
    with closing(_bekleyen_wal(db)):
        wal = db.with_name(db.name + "-wal")
        assert wal.stat().st_size > 0

        adlar = [yol.name for yol in pre_migrate_before(yedekler, an)]
        assert wal_bosalt(db) is True
        assert wal.stat().st_size == 0

    assert adlar == [eski.name, silinemeyen.name]
    with pytest.MonkeyPatch.context() as yama:
        _kilitli_ad(yama, silinemeyen.name)
        silinen, kalan = remove_pre_migrate_named(yedekler, adlar)
    assert silinen == [eski] and kalan == [silinemeyen.name]

    # Silinemeyen adıyla yeniden denenir; dosya zamanına bakılmaz.
    os.utime(sonraki, (an.timestamp() - 86_400, an.timestamp() - 86_400))
    assert remove_pre_migrate_named(yedekler, kalan) == ([silinemeyen], [])
    assert sonraki.exists() and gunluk.exists()


def test_wal_bosalt_veritabani_yoksa_sessiz(tmp_path: Path) -> None:
    assert wal_bosalt(tmp_path / "yok.sqlite3") is False
    assert not (tmp_path / "yok.sqlite3").exists()


def test_wal_bosalt_okuyucu_varken_kismi_kalir_hata_yukseltmez(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    with closing(_bekleyen_wal(db)) as baglanti, closing(sqlite3.connect(db)) as okuyucu:
        baglanti.execute("INSERT INTO kisi VALUES ('Masal Uydurmakaya')")
        baglanti.commit()
        okuyucu.execute("BEGIN")
        assert okuyucu.execute("SELECT COUNT(*) FROM kisi").fetchone() == (2,)
        baglanti.execute("INSERT INTO kisi VALUES ('Uydurma Üçüncü')")
        baglanti.commit()

        assert wal_bosalt(db) is False


def test_wal_bosalt_bozuk_dosyada_false_doner(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    db.write_bytes(b"veritabani degil" * 100)

    assert wal_bosalt(db) is False
