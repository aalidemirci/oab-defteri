"""Otomatik yedek testleri (tasarım §4.2 — `Connection.backup()`, 14 gün rotasyon).

Yedek YALNIZ şifreli alınır (tasarım §4.4.7; ailenin düz yedek dalı söküldü, §13 D29).
Yedek anahtarı (`yedekleme.json`) ya da kurtarma başlığı (`guvenlik.json`) yoksa
yedek ATLANIR; düz kopya hiçbir koşulda yazılmaz. Yardımcı `_db_olustur`
varsayılan olarak ikisini de yazar (ilk hesabı kurulu kurulum). Başlık dosyanın
kendisi değil, yalnız kurtarma bölümünün izdüşümüdür (tasarım TK10).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from desktop import backup as backup_mod
from desktop.backup import (
    daily_backup,
    pre_migrate_backup,
    rotate_backups,
)
from desktop.backup_crypto import (
    MAGIC,
    MAX_RECOVERY_HEADER_BYTES,
    BackupCryptoError,
    decrypt_bytes,
    embedded_recovery_metadata,
    ensure_public_config,
    is_usable_security_state,
    parse_security_state,
    read_embedded_recovery_metadata,
    recovery_header_from_state,
    recovery_key_identity,
)

_TEST_KEY = b"k" * 32
# Kurtarma başlığının kaynağı olan örnek şema 2 durum dosyası. Sarmallar kriptografik
# olarak anlamsızdır (yedek başlığı opaktır), ama biçim `is_usable_security_state`
# kuralına uyar: tam bir hesap sarmalı ve tam bir kurtarma bölümü.
_GUVENLIK = (
    b'{"surum":2,"olusturma":"2026-07-24T09:00:00+03:00","kdf":{"time_cost":1},'
    b'"hesaplar":[{"id":"6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60","tanitici":"yonetici",'
    b'"salt":"dHV6MQ==","sarmal":"ornek-hesap-sarmali","hatali":0,"askida":false}],'
    b'"kurtarma":{"no":1,"tarih":"2026-07-24","salt":"dHV6Mg==",'
    b'"sarmal":"ornek-kurtarma-sarmali","dogrulandi":"2026-07-24T09:05:00+03:00"},'
    b'"gecis":null}'
)
#: `_GUVENLIK`'in yedek başlığı (TK10): yalnız kurtarma bölümü ve anahtarın kimliği.
_BASLIK = {
    "surum": 2,
    "kdf": {"time_cost": 1},
    "kurtarma": {
        "no": 1,
        "tarih": "2026-07-24",
        "salt": "dHV6Mg==",
        "sarmal": "ornek-kurtarma-sarmali",
    },
}


def _baslik(yedek: Path) -> Any:
    return json.loads(embedded_recovery_metadata(yedek.read_bytes()))


def _db_olustur(path: Path, satir_sayisi: int = 3, *, parola_kurulu: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if parola_kurulu:
        ensure_public_config(path.parent, _TEST_KEY)
        (path.parent / "guvenlik.json").write_bytes(_GUVENLIK)
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE ogrenci (id INTEGER PRIMARY KEY, ad TEXT)")
        conn.executemany(
            "INSERT INTO ogrenci (ad) VALUES (?)",
            [(f"Öğrenci {i}",) for i in range(satir_sayisi)],
        )
        conn.commit()
    finally:
        conn.close()


def _satir_sayisi(path: Path) -> int:
    content = path.read_bytes()
    restored = path.with_name(path.name + ".restored.sqlite3")
    assert content.startswith(MAGIC)  # düz yedek hiçbir durumda yazılmaz (§13 D29)
    restored.write_bytes(decrypt_bytes(content, _TEST_KEY))
    conn = sqlite3.connect(restored)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM ogrenci").fetchone()[0])
    finally:
        conn.close()
        restored.unlink(missing_ok=True)


def test_gunluk_yedek_tarihli_deterministik_ad_alir(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    yedekler = tmp_path / "backups"

    sonuc = daily_backup(db, yedekler, today=date(2026, 7, 24))

    assert sonuc == yedekler / "gunluk-2026-07-24.odbak"
    assert sonuc is not None and sonuc.is_file()
    assert _satir_sayisi(sonuc) == 3


def test_yedek_basligi_yalniz_kurtarma_bolumunu_tasir_ve_dogrulanir(tmp_path: Path) -> None:
    """TK10 (tasarım §4.4.4): hesap sarmalları ve saklandı damgası yedeğe GİRMEZ."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    guvenlik = _GUVENLIK.replace(b'"time_cost":1', b'"time_cost":3')
    (tmp_path / "guvenlik.json").write_bytes(guvenlik)

    sonuc = daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24))

    assert sonuc is not None
    container = sonuc.read_bytes()
    baslik = json.loads(embedded_recovery_metadata(container))
    assert baslik == {**_BASLIK, "kdf": {"time_cost": 3}}
    assert "hesaplar" not in baslik and "dogrulandi" not in baslik["kurtarma"]
    assert b"ornek-hesap-sarmali" not in container
    bozuk = bytearray(container)
    bozuk[-1] ^= 1
    with pytest.raises(BackupCryptoError, match="bütünlüğü"):
        decrypt_bytes(bytes(bozuk), _TEST_KEY)


def test_gunluk_yedek_ayni_gun_yeniden_uretilmez(tmp_path: Path) -> None:
    """Gün içinde ikinci açılış, o günün (daha eski, daha değerli) yedeğini EZMEZ."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db, satir_sayisi=3)
    yedekler = tmp_path / "backups"
    ilk = daily_backup(db, yedekler, today=date(2026, 7, 24))
    assert ilk is not None

    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO ogrenci (ad) VALUES ('sonradan')")
    conn.commit()
    conn.close()
    ikinci = daily_backup(db, yedekler, today=date(2026, 7, 24))

    assert ikinci == ilk
    assert _satir_sayisi(ilk) == 3


class _IzlenenBaglanti:
    """`sqlite3.Connection` sarmalayıcısı — `backup()` çağrısını kaydeder.

    `sqlite3.Connection` C tarafında değiştirilemez bir tip olduğu için doğrudan
    yamalanamaz; bu yüzden `sqlite3.connect` sarılır.
    """

    calls: list[str] = []
    patla: bool = False

    def __init__(self, real: sqlite3.Connection) -> None:
        self._real = real

    def backup(self, target: object, **kwargs: object) -> None:
        _IzlenenBaglanti.calls.append("backup")
        if _IzlenenBaglanti.patla:
            raise sqlite3.OperationalError("disk dolu")
        gercek = target._real if isinstance(target, _IzlenenBaglanti) else target
        self._real.backup(gercek, **kwargs)  # type: ignore[arg-type]

    def close(self) -> None:
        self._real.close()

    def __getattr__(self, name: str) -> Any:
        # Sarmalanmayan her şey gerçek bağlantıya gider (execute/commit/…).
        return getattr(self._real, name)


@pytest.fixture
def izlenen_connect(monkeypatch: pytest.MonkeyPatch) -> type[_IzlenenBaglanti]:
    _IzlenenBaglanti.calls = []
    _IzlenenBaglanti.patla = False
    gercek_connect: Any = sqlite3.connect

    def sarmala(*args: Any, **kwargs: Any) -> _IzlenenBaglanti:
        return _IzlenenBaglanti(gercek_connect(*args, **kwargs))

    # `desktop.backup` de aynı modül nesnesini kullanır (`import sqlite3`).
    monkeypatch.setattr(sqlite3, "connect", sarmala)
    return _IzlenenBaglanti


def test_yedek_sqlite_backup_api_ile_alinir(
    tmp_path: Path, izlenen_connect: type[_IzlenenBaglanti]
) -> None:
    """Yedek `Connection.backup()` ile alınır (dosya kopyalama değil)."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)

    daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24))

    assert izlenen_connect.calls == ["backup"]


def test_yedek_wal_de_bekleyen_sayfalari_da_icerir(tmp_path: Path) -> None:
    """Dosya kopyalama DEĞİL kanıtı: WAL'daki satırlar yedekte OLMALI.

    WAL kipinde işlenen satırların bir bölümü hâlâ `-wal` dosyasındadır;
    `db.sqlite3` tek başına kopyalansaydı bu satırlar yedeğe girmezdi.
    """
    db = tmp_path / "db.sqlite3"
    ensure_public_config(db.parent, _TEST_KEY)
    (db.parent / "guvenlik.json").write_bytes(_GUVENLIK)
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE ogrenci (id INTEGER PRIMARY KEY, ad TEXT)")
    conn.executemany("INSERT INTO ogrenci (ad) VALUES (?)", [(f"Öğrenci {i}",) for i in range(3)])
    conn.commit()
    try:  # bağlantı AÇIK kalır → checkpoint yok, satırlar WAL'da
        assert db.with_name(db.name + "-wal").stat().st_size > 0

        yedek = daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24))
        assert yedek is not None

        # Ham dosya kopyası (yanlış yöntem) satırları GÖREMEZ...
        ham = tmp_path / "ham.sqlite3"
        ham.write_bytes(db.read_bytes())
        ham_conn = sqlite3.connect(ham)
        try:
            ham_satir = ham_conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE name='ogrenci'"
            ).fetchone()[0]
        finally:
            ham_conn.close()
        assert ham_satir == 0
    finally:
        conn.close()

    # ...ama `Connection.backup()` ile alınan yedek tam veriyi taşır.
    assert _satir_sayisi(yedek) == 3


def test_veritabani_yoksa_yedek_alinmaz(tmp_path: Path) -> None:
    assert daily_backup(tmp_path / "yok.sqlite3", tmp_path / "backups") is None


def test_yarim_kalan_yedek_dosyasi_birakilmaz(
    tmp_path: Path, izlenen_connect: type[_IzlenenBaglanti]
) -> None:
    """Kopyalama ortasında hata olursa bozuk yedek "sağlam" adıyla kalmamalı."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    yedekler = tmp_path / "backups"
    izlenen_connect.patla = True

    with pytest.raises(sqlite3.Error):
        daily_backup(db, yedekler, today=date(2026, 7, 24))

    assert list(yedekler.glob("gunluk-*.odbak")) == []
    assert list(yedekler.glob("*.tmp")) == []


def test_rotasyon_14_gunden_eskileri_siler_yenileri_korur(tmp_path: Path) -> None:
    yedekler = tmp_path / "backups"
    yedekler.mkdir()
    for gun in ("2026-07-24", "2026-07-11", "2026-07-10", "2026-07-09"):
        (yedekler / f"gunluk-{gun}.odbak").write_bytes(b"x")

    silinen = rotate_backups(yedekler, today=date(2026, 7, 24))

    kalanlar = sorted(p.name for p in yedekler.glob("gunluk-*.odbak"))
    # 14 gün: 10 Temmuz sınırda (korunur), 9 Temmuz düşer.
    assert kalanlar == [
        "gunluk-2026-07-10.odbak",
        "gunluk-2026-07-11.odbak",
        "gunluk-2026-07-24.odbak",
    ]
    assert [p.name for p in silinen] == ["gunluk-2026-07-09.odbak"]


def test_rotasyon_yabanci_dosyalara_dokunmaz(tmp_path: Path) -> None:
    yedekler = tmp_path / "backups"
    yedekler.mkdir()
    (yedekler / "elle-alinan-yedek.sqlite3").write_bytes(b"x")
    (yedekler / "gunluk-bozukad.sqlite3").write_bytes(b"x")
    (yedekler / "notlar.txt").write_bytes(b"x")

    rotate_backups(yedekler, today=date(2026, 7, 24))

    assert (yedekler / "elle-alinan-yedek.sqlite3").exists()
    assert (yedekler / "gunluk-bozukad.sqlite3").exists()
    assert (yedekler / "notlar.txt").exists()


# ----------------------------------------------- yalnız şifreli (§4.4.7)


def test_serialize_olmayan_sqlite_ile_yedek_alinir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Pardus 21/bullseye: libsqlite3 3.34 `Connection.serialize` sunmaz (ailede görülen çökme).

    Geçici-dosya yedek yolu da tutarlı görüntü üretmeli ve artık bırakmamalı.
    """
    monkeypatch.setattr(backup_mod, "_HAS_SERIALIZE", False)
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)

    sonuc = daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24))

    assert sonuc is not None and sonuc.read_bytes().startswith(MAGIC)
    assert _satir_sayisi(sonuc) == 3
    # Geçici görüntü dizini veri dizininde kalıntı bırakmaz.
    assert not list(tmp_path.glob("tmp*")) and not list(tmp_path.glob("*goruntu*"))


def test_ilk_acilista_yedek_anahtari_yokken_gunluk_yedek_atlanir(tmp_path: Path) -> None:
    """Tasarım §4.2 adım 7 (yedek kabı §4.4.7): ilk program yöneticisi hesabı kurulmadan
    (yedekleme.json yok, kişi verisi de yok) günlük yedek ATLANIR; düz kopya YAZILMAZ."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db, parola_kurulu=False)

    assert daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24)) is None
    assert pre_migrate_backup(db, tmp_path / "backups", "0.2.0", today=date(2026, 7, 24)) is None
    assert not list((tmp_path / "backups").glob("*"))


def test_bozuk_anahtar_dosyasiyla_duz_yedek_yazilmaz(tmp_path: Path) -> None:
    """Anahtar dosyası VAR ama bozuksa düz kopya SIZDIRILMAZ, yedek atlanır."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    (tmp_path / "yedekleme.json").write_text("{bozuk", encoding="utf-8")

    assert daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24)) is None
    assert pre_migrate_backup(db, tmp_path / "backups", "0.2.0", today=date(2026, 7, 24)) is None
    assert list((tmp_path / "backups").glob("*.odbak")) == []


def test_guvenlik_dosyasi_kayipken_basliksiz_yedek_alinmaz(tmp_path: Path) -> None:
    """Tehdit 8 (§4.3): guvenlik.json kayıpken yedek kurtarma başlığı taşıyamaz; başlıksız yedek
    ancak kaybolan dosyayla açılabilirdi. Yedek atlanır (eski başlıklı yedekler çıkış
    yoludur; açılış akışı bu durumda rotasyonu da koşmaz — test_main)."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    (tmp_path / "guvenlik.json").unlink()

    assert daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24)) is None
    assert not list((tmp_path / "backups").glob("*.odbak"))


_KULLANILAMAZ_GUVENLIK = {
    "bos": b"",
    "bozuk_json": b"{bozuk",
    "utf8_degil": b"\xff\xfe\x00",
    "sozluk_degil": b'["parola"]',
    "bos_sozluk": b"{}",
    # Şema 1 (tek parola bölümü) kullanılamaz sayılır (plan F1b-1 "Eski veri").
    "sema_1": (
        b'{"surum":1,"kdf":{"time_cost":1},"parola":{"salt":"dHV6","sarmal":"s"},'
        b'"kurtarma":{"salt":"dHV6","sarmal":"s"},"gecis":"TAMAM"}'
    ),
    "surum_yok": b'{"kdf":{},"kurtarma":{"salt":"dHV6","sarmal":"s"}}',
    "sarmal_bolumu_yok": b'{"surum":2,"kdf":{"time_cost":1},"hesaplar":[],"gecis":null}',
    "hesaplar_liste_degil": (
        b'{"surum":2,"kdf":{},"hesaplar":{},"kurtarma":{"salt":"dHV6","sarmal":"s"}}'
    ),
    "sarmallar_bos": (
        b'{"surum":2,"kdf":{},"hesaplar":[{"id":"a","tanitici":"b","salt":"dHV6",'
        b'"sarmal":""}],"kurtarma":{"salt":"","sarmal":"s"}}'
    ),
    "tuz_dize_degil": b'{"surum":2,"kdf":{},"kurtarma":{"salt":5,"sarmal":"s"}}',
    "kdf_sozluk_degil": b'{"surum":2,"kdf":"x","kurtarma":{"salt":"dHV6","sarmal":"s"}}',
    # Derin iç içe JSON: `json.loads` RecursionError yükseltir; o da "kullanılamaz"dır
    # (yedek atlanır, istisna sızmaz — `parse_security_state`).
    "derin_ic_ice": b"[" * 20000 + b"]" * 20000,
    # Kullanılabilir (hesap sarmalı tam) ama kurtarma bölümü yok: başlık başka
    # bilgisayarda hiçbir sırla açılamazdı (TK10) → yedek alınmaz.
    "kurtarma_yok": (
        b'{"surum":2,"kdf":{},"hesaplar":[{"id":"a","tanitici":"b","salt":"dHV6",'
        b'"sarmal":"s"}],"gecis":null}'
    ),
}


@pytest.mark.parametrize("icerik", _KULLANILAMAZ_GUVENLIK.values(), ids=_KULLANILAMAZ_GUVENLIK)
def test_bos_ya_da_bozuk_guvenlik_json_ile_yedek_alinmaz(tmp_path: Path, icerik: bytes) -> None:
    """Tehdit 8 türevi: dosya SİLİNMEZ ama içi boşaltılır/bozulur. Varlık denetimi yetmez;
    başlık `is_usable_security_state` kuralından geçmezse yedek atlanır (None)."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    (tmp_path / "guvenlik.json").write_bytes(icerik)

    assert daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24)) is None
    assert pre_migrate_backup(db, tmp_path / "backups", "0.2.0", today=date(2026, 7, 24)) is None
    assert not list((tmp_path / "backups").glob("*.odbak"))


def test_yalniz_kurtarma_bolumu_basliga_yeter(tmp_path: Path) -> None:
    """Kurtarma anahtarıyla geri yüklemeden sonra `hesaplar` boştur: yedek yine alınır."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    yalniz_kurtarma = (
        b'{"surum":2,"kdf":{"time_cost":1},"hesaplar":[],'
        b'"kurtarma":{"no":4,"tarih":"2026-10-01","salt":"dHV6","sarmal":"s"},"gecis":null}'
    )
    (tmp_path / "guvenlik.json").write_bytes(yalniz_kurtarma)

    sonuc = daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24))

    assert sonuc is not None
    assert _baslik(sonuc) == {
        "surum": 2,
        "kdf": {"time_cost": 1},
        "kurtarma": {"no": 4, "tarih": "2026-10-01", "salt": "dHV6", "sarmal": "s"},
    }


def test_baslik_kurallari_dogrudan() -> None:
    """Tek kural: hesap sarmalı ya da kurtarma bölümü tam olmalı; başlık yalnız kurtarma."""
    durum = json.loads(_GUVENLIK)
    assert is_usable_security_state(durum)
    assert recovery_header_from_state(durum) == _BASLIK
    assert is_usable_security_state(_BASLIK)  # başlık da aynı kuraldan geçer
    durum["kurtarma"] = {}
    assert is_usable_security_state(durum)  # hesap sarmalı tam
    assert recovery_header_from_state(durum) is None  # ama başlık olamaz


def test_derin_ic_ice_json_recursionerror_sizdirmaz() -> None:
    """`json.loads` derin iç içe dizide RecursionError yükseltir; ayrıştırıcı None döner.

    Yedek listesi (kayıp kilidinin çıkış yolu) ve geri yükleme çekirdeği bu kuralı
    çağırır: tek bir bozuk başlık ikisini de 500'e düşürmemeli.
    """
    with pytest.raises(RecursionError):
        json.loads("[" * 20000 + "]" * 20000)
    assert parse_security_state(b"[" * 20000 + b"]" * 20000) is None
    assert parse_security_state(_GUVENLIK) is not None


def test_kurtarma_anahtarinin_kimligi_yalniz_no_ve_tarihtir() -> None:
    """TK10: başlık ve durum dosyası aynı kuraldan `{no, tarih}` verir; tuz ve sarmal dönmez."""
    assert recovery_key_identity(json.loads(_GUVENLIK)) == {"no": 1, "tarih": "2026-07-24"}
    assert recovery_key_identity(_BASLIK) == {"no": 1, "tarih": "2026-07-24"}
    # Biçimsiz alan tek başına düşer; ikisi de yoksa kimlik yoktur.
    assert recovery_key_identity({"kurtarma": {"no": True, "tarih": "2026-07-24"}}) == {
        "no": None,
        "tarih": "2026-07-24",
    }
    assert recovery_key_identity({"kurtarma": {"no": 2, "tarih": "24.07.2026"}}) == {
        "no": 2,
        "tarih": None,
    }
    bos_durumlar: tuple[object, ...] = (
        None,
        [],
        {},
        {"kurtarma": []},
        {"kurtarma": {"no": 0, "tarih": ""}},
    )
    for bos in bos_durumlar:
        assert recovery_key_identity(bos) is None


def test_gomulu_baslik_dosyanin_yalniz_basindan_okunur(tmp_path: Path) -> None:
    """Yedek listesinin okuyucusu bellekteki kuralla aynı sonucu verir, bozuğu reddeder."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    yedek = daily_backup(db, tmp_path / "backups", today=date(2026, 7, 24))
    assert yedek is not None
    icerik = yedek.read_bytes()
    assert read_embedded_recovery_metadata(yedek) == embedded_recovery_metadata(icerik)

    sabit = len(MAGIC) + 32 + 12 + 4  # sihirli bayt + açık anahtar + nonce + uzunluk
    uzunluk = int.from_bytes(icerik[sabit - 4 : sabit], "big")
    bozuklar = {
        "yedek_degil": b"duz metin",
        "kisa": icerik[: sabit - 1],
        "baslik_kesik": icerik[: sabit + uzunluk - 1],
        "icerik_yok": icerik[: sabit + uzunluk],
        "uzunluk_sinir_disi": icerik[: sabit - 4]
        + (MAX_RECOVERY_HEADER_BYTES + 1).to_bytes(4, "big")
        + icerik[sabit:],
    }
    for ad, bayt in bozuklar.items():
        yol = tmp_path / f"{ad}.odbak"
        yol.write_bytes(bayt)
        with pytest.raises(BackupCryptoError):
            read_embedded_recovery_metadata(yol)


def test_bosaltilan_guvenlik_json_eski_baslikli_yedekleri_rotasyona_kurban_etmez(
    tmp_path: Path,
) -> None:
    """Denetçi senaryosu: sağlam başlıklı 01.09 yedeği var; kilitliyken guvenlik.json
    boşaltılır; program 21.09'da açılır. Başlıksız yedek ALINMAZ, açılış akışı
    (`main.prepare_data`: yalnız yedek alındıysa rotasyon) eski yedeği silmez."""
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    yedekler = tmp_path / "backups"
    eski = daily_backup(db, yedekler, today=date(2026, 9, 1))
    assert eski is not None
    assert _baslik(eski) == _BASLIK

    (tmp_path / "guvenlik.json").write_bytes(b"")
    bugun = date(2026, 9, 21)
    alinan = daily_backup(db, yedekler, today=bugun)
    if alinan is not None:  # `desktop/main.py::prepare_data` ile aynı koşul
        rotate_backups(yedekler, today=bugun)

    assert alinan is None
    assert sorted(p.name for p in yedekler.glob("*.odbak")) == ["gunluk-2026-09-01.odbak"]
    assert _baslik(eski) == _BASLIK


def test_rotasyon_olmayan_dizinde_patlamaz(tmp_path: Path) -> None:
    assert rotate_backups(tmp_path / "yok", today=date(2026, 7, 24)) == []


def test_migrate_oncesi_yedek_surum_adiyla_alinir(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)
    yedekler = tmp_path / "backups"

    sonuc = pre_migrate_backup(db, yedekler, "0.2.0", today=date(2026, 7, 24))

    assert sonuc == yedekler / "pre-migrate-0.2.0-2026-07-24.odbak"
    assert sonuc is not None and _satir_sayisi(sonuc) == 3


def test_migrate_oncesi_yedek_dosya_adini_temizler(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)

    sonuc = pre_migrate_backup(db, tmp_path / "backups", "1.0/rc:1", today=date(2026, 7, 24))

    assert sonuc is not None
    assert sonuc.name == "pre-migrate-1.0_rc_1-2026-07-24.odbak"


def test_migrate_oncesi_yedek_var_olani_ezmez(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    _db_olustur(db, satir_sayisi=2)
    yedekler = tmp_path / "backups"
    ilk = pre_migrate_backup(db, yedekler, "0.2.0", today=date(2026, 7, 24))
    assert ilk is not None

    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO ogrenci (ad) VALUES ('sonradan')")
    conn.commit()
    conn.close()
    ikinci = pre_migrate_backup(db, yedekler, "0.2.0", today=date(2026, 7, 24))

    assert ikinci == ilk
    assert _satir_sayisi(ilk) == 2


def test_rotasyon_migrate_oncesi_yedeklerin_son_besini_tutar(tmp_path: Path) -> None:
    """Yükseltme öncesi kopyalar gün değil ADET ile sınırlanır (14 günden uzun yaşayabilir)."""
    yedekler = tmp_path / "backups"
    yedekler.mkdir()
    for i in range(1, 8):
        (yedekler / f"pre-migrate-0.{i}.0-2020-01-0{i}.odbak").write_bytes(b"x")

    rotate_backups(yedekler, today=date(2026, 7, 24), keep_pre_migrate=5)

    kalanlar = sorted(p.name for p in yedekler.glob("pre-migrate-*.odbak"))
    assert len(kalanlar) == 5
    assert "pre-migrate-0.7.0-2020-01-07.odbak" in kalanlar
    assert "pre-migrate-0.1.0-2020-01-01.odbak" not in kalanlar


def test_yedek_dizini_yoksa_olusturulur(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    _db_olustur(db)

    daily_backup(db, tmp_path / "a" / "b" / "backups", today=date(2026, 7, 24))

    assert (tmp_path / "a" / "b" / "backups").is_dir()


def test_varsayilan_saklama_suresi_14_gun(tmp_path: Path) -> None:
    assert backup_mod.DEFAULT_KEEP_DAYS == 14
