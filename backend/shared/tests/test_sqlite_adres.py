"""Salt okunur SQLite adresi (`shared.sqlite_adres`; tasarım §4.4.4, plan F1b-2).

Geri yüklemenin iki ORM'siz okuyucusu (hesap denetimi, zincir başı) güncel veritabanını bu
adresle açar. Denetim bulgusu: `Path.resolve().as_uri()` UNC yolda `file://sunucu/…`
(SQLite "invalid uri authority" der) ve Windows'ta eşlenmiş sürücüyü UNC'ye çevirir; okunabilen
veritabanı sessizce "okunamıyor" sayılır, karar yedeğin görüntüsüne kalırdı. Biçim saf yollarla
(`PureWindowsPath`) her platformda sabitlenir; gerçek dosya açılışı POSIX'te (Docker) sınanır.
Yollar uydurmadır.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit

import pytest

from shared.sqlite_adres import salt_okunur_adres

POSIX = pytest.mark.skipif(os.name != "posix", reason="POSIX dosya sistemi (Docker) gerekir.")


@pytest.mark.parametrize(
    ("yol", "adres"),
    [
        pytest.param(
            PureWindowsPath(r"\\sunucu\pay\OAB\data\db.sqlite3"),
            "file:////sunucu/pay/OAB/data/db.sqlite3?mode=ro",
            id="unc",
        ),
        pytest.param(
            PureWindowsPath(r"\\localhost\C$\OAB\data\db.sqlite3"),
            "file:////localhost/C%24/OAB/data/db.sqlite3?mode=ro",
            id="unc_localhost",
        ),
        pytest.param(
            PureWindowsPath(r"Z:\OAB\data\db.sqlite3"),
            "file:///Z:/OAB/data/db.sqlite3?mode=ro",
            id="eslenmis_surucu",
        ),
        pytest.param(
            PureWindowsPath(r"C:\Users\Öğretmen\AppData\Local\OAB Defteri\data\db.sqlite3"),
            "file:///C:/Users/%C3%96%C4%9Fretmen/AppData/Local/OAB%20Defteri/data/db.sqlite3"
            "?mode=ro",
            id="windows_turkce_ve_bosluk",
        ),
        pytest.param(
            PurePosixPath("/home/ogretmen/.local/share/oab-defteri/data/db.sqlite3"),
            "file:///home/ogretmen/.local/share/oab-defteri/data/db.sqlite3?mode=ro",
            id="posix",
        ),
        pytest.param(
            PurePosixPath("/veri/a?b#c%d/db.sqlite3"),
            "file:///veri/a%3Fb%23c%25d/db.sqlite3?mode=ro",
            id="ozel_karakter",
        ),
    ],
)
def test_adres_bicimi(yol: PurePath, adres: str) -> None:
    assert salt_okunur_adres(yol) == adres


@pytest.mark.parametrize(
    "yol",
    [
        PureWindowsPath(r"\\sunucu\pay\OAB\data\db.sqlite3"),
        PureWindowsPath(r"Z:\OAB\data\db.sqlite3"),
        PurePosixPath("/veri/db.sqlite3"),
    ],
)
def test_adreste_authority_yoktur(yol: PurePath) -> None:
    """SQLite yalnız boş ya da `localhost` authority kabul eder; hiçbir yolda yazılmaz."""
    parca = urlsplit(salt_okunur_adres(yol))
    assert (parca.scheme, parca.netloc, parca.query) == ("file", "", "mode=ro")


@pytest.mark.parametrize(
    "yol", [PurePosixPath("data/db.sqlite3"), PureWindowsPath(r"Z:OAB\db.sqlite3")]
)
def test_goreli_saf_yol_reddedilir(yol: PurePath) -> None:
    with pytest.raises(ValueError, match="mutlak"):
        salt_okunur_adres(yol)


def test_goreli_yol_calisma_dizinine_gore_mutlak_yapilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert salt_okunur_adres(Path("db.sqlite3")) == salt_okunur_adres(tmp_path / "db.sqlite3")


@POSIX
def test_sembolik_bag_cozulmez(tmp_path: Path) -> None:
    """`resolve()` edilmez (Windows'ta eşlenmiş sürücüyü UNC'ye çevirirdi; POSIX karşılığı
    sembolik bağdır): adres verilen yolu taşır."""
    gercek = tmp_path / "gercek"
    gercek.mkdir()
    (tmp_path / "bag").symlink_to(gercek, target_is_directory=True)

    adres = salt_okunur_adres(tmp_path / "bag" / "db.sqlite3")

    assert "/bag/db.sqlite3" in adres and "/gercek/" not in adres


@POSIX
def test_ozel_karakterli_yoldaki_veritabani_salt_okunur_acilir(tmp_path: Path) -> None:
    """`?`, `#`, `%`, boşluk ve Türkçe harf taşıyan dizindeki dosya açılır, yazılamaz."""
    dizin = tmp_path / "a?b#c%d öğretmen"
    dizin.mkdir()
    db = dizin / "db.sqlite3"
    with closing(sqlite3.connect(db)) as baglanti:
        baglanti.execute("CREATE TABLE t (deger TEXT)")
        baglanti.execute("INSERT INTO t VALUES ('kayıt')")
        baglanti.commit()

    with closing(sqlite3.connect(salt_okunur_adres(db), uri=True)) as baglanti:
        assert baglanti.execute("SELECT deger FROM t").fetchone() == ("kayıt",)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            baglanti.execute("INSERT INTO t VALUES ('yazım')")
