"""Yedekten geri yükleme çekirdeği (services.backup_restore) testleri.

Yedekler YALNIZ X25519+AES-GCM kapsayıcısıdır (tasarım §4.4.7; düz yedek dalı
söküldü, §13 D29): düz SQLite dosyası reddedilir. Çekirdeğin sözleşmesi gereği testler
ORM'e HİÇ dokunmaz — geri yükleme bozuk bir veritabanıyla da çalışabilmelidir
(`django_db` işareti bilinçli olarak yoktur).

Yedek başlığı yalnız kurtarma bölümünü taşır (tasarım TK10, §4.4.4): aday sırası
(1) güncel `guvenlik.json` + hesabın tanıtıcısı ve parolası, (2) yedek başlığı +
kurtarma anahtarı. Başlıkla açılınca `guvenlik.json` yalnız kurtarma bölümüyle
yazılır.

Parola yolunda geri yüklemeyi yalnız program yöneticisi yapar (tasarım §4.4.4; plan F1b-2):
çekirdek hesabı ORM'siz okuyucuyla güncel veritabanında, o okunamıyorsa yedeğin görüntüsünde
doğrular. Bu yüzden parola yolunda BAŞARI bekleyen testlerin görüntüsü, o testin DEK'iyle
mühürlü bir program yöneticisi satırı ve okul kartı taşır (`_sqlite_baytlari(..., dek=...)`;
`geri_yukleme_ortak`). Yetkinin kendi testleri `test_geri_yukleme_yetkisi.py`'dedir.

Her test kendi (başlangıçta `guvenlik.json` içermeyen) veri dizininde koşar;
ucuz Argon2 profili ve gecikmesiz deneme `backend/conftest.py`'dendir.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any, cast

import pytest
from argon2.exceptions import HashingError
from desktop.backup import (
    is_old_database_file,
    old_database_stamp,
    remove_old_databases_named,
)
from desktop.backup_crypto import (
    DENEME_MAGIC,
    DOSYA_BOLUMU_SONU,
    KAPSAM_TAM,
    KAPSAM_YEREL,
    Manifesto,
    ManifestoGirdisi,
    ensure_public_config,
)
from desktop.tests.kap_ortak import bolum_girdisi, durum_basligi, kap_kur
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.okul.management.commands.restore_backup import Command as RestoreBackupCommand
from apps.okul.services import app_password, backup_restore
from apps.okul.tests.geri_yukleme_ortak import HesapSatiri, yetkili_sqlite
from shared import crypto

PAROLA = "Deneme-Parola-1"
HESAP = "yonetici"
HESAP_ID = "0b6f5c1e-2a3d-4e5f-8a9b-0c1d2e3f4a5b"


@pytest.fixture(autouse=True)
def veri_dizini(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Her test kendi veri dizininde koşar (güncel `guvenlik.json` yok — senaryo kurar)."""
    veri = tmp_path / "veri"
    veri.mkdir()
    monkeypatch.setenv(app_password.ENV_SECURITY_DIR, str(veri))
    monkeypatch.setenv(app_password.ENV_BACKUP_DIR, str(tmp_path / "yedekler"))
    return veri


def _sqlite_baytlari(dizin: Path, isaret: str, dek: bytes | None = None) -> bytes:
    """`isaret` değerini taşıyan gerçek bir SQLite dosyasının baytları.

    `dek` verilirse dosya o DEK'le mühürlü program yöneticisi satırını (`HESAP_ID`, `HESAP`) ve
    okul kartını da taşır: parola yolunda geri yükleme hesabı bu görüntüde doğrular.
    """
    yol = dizin / f"kaynak-{isaret}.sqlite3"
    if dek is not None:
        return yetkili_sqlite(yol, dek=dek, hesaplar=[HesapSatiri(HESAP_ID, HESAP)], isaret=isaret)
    with closing(sqlite3.connect(yol)) as baglanti:
        baglanti.execute("CREATE TABLE kayit (deger TEXT)")
        baglanti.execute("INSERT INTO kayit VALUES (?)", (isaret,))
        baglanti.commit()
    return yol.read_bytes()


def _durum(dek: bytes, parola: str, kurtarma: str) -> dict[str, Any]:
    return app_password._build_state(
        dek, hesap_id=HESAP_ID, tanitici=HESAP, password=parola, recovery_key=kurtarma
    )


def _dek_ile_durum(parola: str, kurtarma: str | None = None) -> tuple[bytes, dict[str, Any]]:
    dek = crypto.new_data_key()
    return dek, _durum(dek, parola, kurtarma or app_password.generate_recovery_key())


def _sifreli_kapsayici(icerik: bytes, dek: bytes, durum: dict[str, Any] | None) -> bytes:
    """Başlığa güvenlik durumunun TK10 izdüşümü (yalnız kurtarma bölümü) gömülür."""
    # desktop.* backend mypy koşusunda çözümlenmez (Any) → dönüş tipi sabitlenir.
    return cast("bytes", kap_kur(icerik, dek, baslik=durum_basligi(durum)))


def _guncel_yaz(veri_dizini: Path, durum: dict[str, Any]) -> None:
    (veri_dizini / "guvenlik.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Düz yedek dalı yok (§13 D29) + dosya takası
# ---------------------------------------------------------------------------
def test_duz_sqlite_dosyasi_reddedilir_ve_hedefe_dokunulmaz(
    tmp_path: Path, veri_dizini: Path
) -> None:
    db = veri_dizini / "db.sqlite3"
    orijinal = _sqlite_baytlari(tmp_path, "orijinal")
    db.write_bytes(orijinal)
    yedek = tmp_path / "gunluk-2026-08-01.odbak"
    yedek.write_bytes(_sqlite_baytlari(tmp_path, "duz"))

    with pytest.raises(backup_restore.BackupRestoreError, match="şifrelenmemiş"):
        backup_restore.restore_database(yedek, db, hesap=HESAP, password=PAROLA)

    assert db.read_bytes() == orijinal
    assert not list(veri_dizini.glob("db-onceki-*"))


def test_yedek_geri_yuklenir_eski_dosya_ve_wal_kenara_alinir(
    tmp_path: Path, veri_dizini: Path
) -> None:
    db = veri_dizini / "db.sqlite3"
    db.write_bytes(_sqlite_baytlari(tmp_path, "eski"))
    (veri_dizini / "db.sqlite3-wal").write_bytes(b"wal-kalintisi")
    (veri_dizini / "db.sqlite3-shm").write_bytes(b"shm-kalintisi")
    (veri_dizini / "surum.json").write_text("{}", encoding="utf-8")
    dek, durum = _dek_ile_durum(PAROLA)
    # Önce güvenlik dosyası: görüntüdeki satır onun sarmalının özetini taşır (geri_yukleme_ortak).
    _guncel_yaz(veri_dizini, durum)
    yeni = _sqlite_baytlari(tmp_path, "yeni", dek)
    yedek = tmp_path / "gunluk-2026-08-01.odbak"
    yedek.write_bytes(_sifreli_kapsayici(yeni, dek, durum))

    sonuc = backup_restore.restore_database(yedek, db, hesap=HESAP, password=PAROLA)

    assert db.read_bytes() == yeni
    # Eski veritabanı SİLİNMEZ, kenara alınır; WAL/SHM de onun yanına taşınır.
    assert sonuc.old_db_path is not None
    assert sonuc.old_db_path.name.startswith("db-onceki-")
    assert b"eski" in sonuc.old_db_path.read_bytes()
    yan_wal = sonuc.old_db_path.with_name(sonuc.old_db_path.name + "-wal")
    assert yan_wal.read_bytes() == b"wal-kalintisi"
    assert not (veri_dizini / "db.sqlite3-wal").exists()
    assert not (veri_dizini / "db.sqlite3-shm").exists()
    # Damga artık geri yüklenen veriyi tarif etmiyor → silinir (eksik damga engel değil).
    assert not (veri_dizini / "surum.json").exists()
    # Saklama tetiği yaşı adın damgasından okur (aile iskeletinin kullanıcı kararı): adı üreten ile
    # okuyan aynı biçimi konuşur; damga geri yüklemenin yerel anıdır, eşler aynı damgayı taşır.
    damga = old_database_stamp(sonuc.old_db_path.name)
    assert damga is not None
    assert abs(damga - timezone.localtime().replace(tzinfo=None)) < timedelta(minutes=5)
    assert old_database_stamp(yan_wal.name) == damga
    assert is_old_database_file(sonuc.old_db_path.name)
    assert not is_old_database_file(yan_wal.name)


def test_hedef_yokken_calisir_ve_basibos_wal_temizlenir(tmp_path: Path, veri_dizini: Path) -> None:
    db = veri_dizini / "db.sqlite3"
    (veri_dizini / "db.sqlite3-wal").write_bytes(b"basibos")
    yeni = _sqlite_baytlari(tmp_path, "yeni")
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(yeni, dek, durum))

    sonuc = backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert db.read_bytes() == yeni
    assert sonuc.old_db_path is None
    assert not (veri_dizini / "db.sqlite3-wal").exists()


# ---------------------------------------------------------------------------
# Kenara alınan veritabanının akıbeti (14 günlük rotasyon — tasarım §4.4.7)
# ---------------------------------------------------------------------------
ESKI_AD = "db-onceki-2026-09-01-101010.sqlite3"


def _aile(dizin: Path, ad: str) -> list[Path]:
    yollar = [dizin / ad, dizin / f"{ad}-wal", dizin / f"{ad}-shm"]
    for yol in yollar:
        yol.write_bytes(b"x")
    return yollar


def test_onceki_veritabani_damgasi_addan_okunur() -> None:
    beklenen = datetime(2026, 9, 1, 10, 10, 10)
    for ek in ("", "-wal", "-shm"):
        assert old_database_stamp(ESKI_AD + ek) == beklenen


@pytest.mark.parametrize(
    "ad",
    [
        "db-onceki-elle.sqlite3",
        "db-onceki-2026-13-40-101010.sqlite3",
        f"{ESKI_AD}.bak",
        f"{ESKI_AD}-journal",
        f"../{ESKI_AD}",
        f"alt/{ESKI_AD}",
        "db.sqlite3",
        "guvenlik-arsiv-2026-09-01-101010.json",
    ],
)
def test_programin_bicimi_olmayan_ad_taninmaz_ve_silinmez(ad: str, veri_dizini: Path) -> None:
    assert old_database_stamp(ad) is None
    disarida = veri_dizini.parent / ESKI_AD
    disarida.write_bytes(b"x")
    hedef = veri_dizini / Path(ad).name
    hedef.write_bytes(b"x")

    silinen, kalan = remove_old_databases_named(veri_dizini, [ad])

    assert (silinen, kalan) == ([], [])
    assert disarida.exists() and hedef.exists()


def test_eskiler_addaki_damgaya_gore_esleriyle_listelenir(veri_dizini: Path) -> None:
    eski = _aile(veri_dizini, ESKI_AD)
    yeni = _aile(veri_dizini, "db-onceki-2026-09-20-080000.sqlite3")
    (veri_dizini / "db-onceki-elle.sqlite3").write_bytes(b"x")
    # Dosya zamanı ölçü değildir: yeni dosya çok eski, eski dosya çok yeni görünse de.
    for yol in yeni:
        os.utime(yol, (0, 0))
    sinir = datetime(2026, 9, 15, 12, 0)

    beklenen = sorted(yol.name for yol in eski)
    assert backup_restore.old_databases_before(veri_dizini, sinir) == beklenen
    # Saat dilimli sınır yerel saate çevrilir (damga yerel saattir).
    assert backup_restore.old_databases_before(veri_dizini, timezone.make_aware(sinir)) == beklenen
    assert backup_restore.old_databases_before(veri_dizini / "yok", sinir) == []


def test_veritabani_silinemezse_esleri_de_kalir(
    veri_dizini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kalan kopyanın işlenmiş sayfaları `-wal`'da olabilir: eşini silmek onu eksik bırakırdı."""
    kilitli = _aile(veri_dizini, ESKI_AD)
    ikinci = _aile(veri_dizini, "db-onceki-2026-09-02-101010.sqlite3")
    ozgun = Path.unlink

    def sil(yol: Path, missing_ok: bool = False) -> None:
        if yol.name == ESKI_AD:
            raise PermissionError("başka bir programda açık")
        ozgun(yol, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", sil)
    adlar = [yol.name for yol in (*kilitli, *ikinci)] + ["db-onceki-2026-09-03-101010.sqlite3"]

    silinen, kalan = remove_old_databases_named(veri_dizini, adlar)

    assert kalan == [ESKI_AD, f"{ESKI_AD}-shm", f"{ESKI_AD}-wal"]
    assert all(yol.exists() for yol in kilitli)
    assert silinen == sorted(yol.name for yol in ikinci)
    assert not any(yol.exists() for yol in ikinci)
    # Klasörde olmayan ad silinmiş sayılmaz, beklemede de kalmaz.
    assert "db-onceki-2026-09-03-101010.sqlite3" not in silinen + kalan


@pytest.mark.parametrize(
    "icerik",
    [b"SQLite format 3\x00" + b"\x00" * 100, b"HERHANGI BIR ICERIK"],
    ids=["duz", "yabanci"],
)
def test_ret_iletileri_teknik_uzanti_anmaz(icerik: bytes, tmp_path: Path) -> None:
    """Sözlük: ".odbak" ve "kapsayıcı" kullanıcı metninde geçmez (yalnız Hakkında)."""
    yedek = tmp_path / "yedek.odbak"
    yedek.write_bytes(icerik)
    with pytest.raises(backup_restore.BackupRestoreError) as hata:
        backup_restore.inspect_backup(yedek)

    ileti = str(hata.value)
    assert "odbak" not in ileti
    assert "kapsayıcı" not in ileti


def test_gecersiz_dosya_reddedilir(tmp_path: Path, veri_dizini: Path) -> None:
    yedek = tmp_path / "bozuk.odbak"
    yedek.write_bytes(b"HERHANGI BIR ICERIK")

    with pytest.raises(backup_restore.BackupRestoreError, match="geçerli bir"):
        backup_restore.restore_database(
            yedek, veri_dizini / "db.sqlite3", hesap=HESAP, password=PAROLA
        )


# ---------------------------------------------------------------------------
# Şifreli kapsayıcı ve aday sırası (TK10)
# ---------------------------------------------------------------------------
def test_baslikta_hesap_sarmali_olmadigi_icin_parola_yolu_kapali(
    tmp_path: Path, veri_dizini: Path
) -> None:
    """Yeni bilgisayar / kayıp güvenlik dosyası: hesap parolası başlıkla DEK vermez (TK10)."""
    dek, durum = _dek_ile_durum(PAROLA)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, durum))
    db = veri_dizini / "db.sqlite3"

    with pytest.raises(backup_restore.BackupRestoreError) as hata:
        backup_restore.restore_database(yedek, db, hesap=HESAP, password=PAROLA)

    ileti = str(hata.value)
    tarih = timezone.localdate().strftime("%d.%m.%Y")
    assert f"Bu yedek 1 numaralı, {tarih} tarihli kurtarma anahtarıyla açılır." in ileti
    assert not db.exists()
    assert not (veri_dizini / "guvenlik.json").exists()


def test_kurtarma_anahtariyla_acilir_ve_yalniz_kurtarma_bolumu_yazilir(
    tmp_path: Path, veri_dizini: Path
) -> None:
    """Kayıp dosya senaryosu: başlık DEK'i verir, dosya YALNIZ kurtarma bölümüyle onarılır;
    anahtar kullanıldığı için saklandı damgası doludur (plan F1b-1)."""
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    icerik = _sqlite_baytlari(tmp_path, "gizli")
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(icerik, dek, durum))
    db = veri_dizini / "db.sqlite3"

    sonuc = backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert db.read_bytes() == icerik
    assert sonuc.state_written is True
    yazilan = json.loads((veri_dizini / "guvenlik.json").read_text(encoding="utf-8"))
    assert yazilan["surum"] == 2 and yazilan["gecis"] is None
    assert yazilan["hesaplar"] == []
    assert yazilan["kdf"] == durum["kdf"]
    for alan in ("no", "tarih", "salt", "sarmal"):
        assert yazilan["kurtarma"][alan] == durum["kurtarma"][alan]
    assert yazilan["kurtarma"]["dogrulandi"]
    assert app_password._unwrap_with_recovery(yazilan, kurtarma) == dek


@pytest.mark.parametrize("kapsam", [KAPSAM_YEREL, KAPSAM_TAM], ids=["yerel", "tam"])
def test_iki_kapsam_da_geri_yuklenir_hedefe_yalniz_veritabani_yazilir(
    kapsam: int, tmp_path: Path, veri_dizini: Path
) -> None:
    """Plan F1b-3 "Kap ve manifesto" (manifesto boşken; dosyalar (c)'dedir): kap taşısa da
    manifesto ve dosya bölümü hedefe girmez, veritabanı bayt bayt aynıdır."""
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    icerik = _sqlite_baytlari(tmp_path, "gizli")
    yedek = tmp_path / "yedek.odbak"
    yedek.write_bytes(
        kap_kur(icerik, dek, baslik=durum_basligi(durum), manifesto=Manifesto(kapsam))
    )
    db = veri_dizini / "db.sqlite3"

    backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert db.read_bytes() == icerik


_EK = ManifestoGirdisi("1" * 32, 2, "a" * 64)
_EK_BOLUMU = bolum_girdisi(_EK.ad.encode("ascii"), bytes(_EK.sifreli_boy))


@pytest.mark.parametrize(
    "dosya_bolumu",
    [
        b"",
        DOSYA_BOLUMU_SONU,
        _EK_BOLUMU,
        _EK_BOLUMU + DOSYA_BOLUMU_SONU + b"x",
    ],
    ids=["bolum_yok", "girdi_yok", "bitis_yok", "fazla_bayt"],
)
def test_dosya_bolumu_kap_duzeyinde_bozuk_tam_yedek_geri_yuklenmez(
    dosya_bolumu: bytes, tmp_path: Path, veri_dizini: Path
) -> None:
    """Kullanıcı kararı "Bozuk ekte geri yükleme durur, ikinci onayla sürer": kap düzeyinde bozuk
    yedek geri yüklenmez, ileti de yanlış sır gibi anlatmaz. Hiçbir dosya değişmez."""
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "yedek.odbak"
    yedek.write_bytes(
        kap_kur(
            _sqlite_baytlari(tmp_path, "gizli"),
            dek,
            baslik=durum_basligi(durum),
            manifesto=Manifesto(KAPSAM_TAM, (_EK,)),
            dosya_bolumu=dosya_bolumu,
        )
    )
    db = veri_dizini / "db.sqlite3"
    db.write_bytes(b"onceki")

    with pytest.raises(backup_restore.BackupRestoreError, match="bölümü bozuk") as hata:
        backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert "Yedek açılamadı" not in str(hata.value)
    assert db.read_bytes() == b"onceki"
    assert not list(veri_dizini.glob("db-onceki-*"))
    assert not (veri_dizini / "guvenlik.json").exists()


def test_kapsami_tutmayan_manifesto_yanlis_sir_gibi_anlatilmaz(
    tmp_path: Path, veri_dizini: Path
) -> None:
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "yedek.odbak"
    yedek.write_bytes(
        kap_kur(
            _sqlite_baytlari(tmp_path, "gizli"),
            dek,
            baslik=durum_basligi(durum),
            ham_manifesto=Manifesto(KAPSAM_TAM).baytlar(),
            kapsam=KAPSAM_YEREL,
        )
    )

    with pytest.raises(backup_restore.BackupRestoreError, match="dosya listesi"):
        backup_restore.restore_database(yedek, veri_dizini / "db.sqlite3", recovery_key=kurtarma)


def test_baska_kurulumun_tam_yedegi_guncel_dosyayla_acilmaz_baslikla_acilir(
    tmp_path: Path, veri_dizini: Path
) -> None:
    """Aday sırası kapsamdan bağımsızdır: güncel dosyanın DEK'i bu yedeği açmaz, sıradaki aday
    (gömülü başlık) açar. Yanlış anahtar yedeğin bozukluğu sayılsaydı ilk adayda dururdu."""
    kurtarma = app_password.generate_recovery_key()
    _guncel_yaz(veri_dizini, _durum(crypto.new_data_key(), PAROLA, kurtarma))
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    icerik = _sqlite_baytlari(tmp_path, "gizli")
    yedek = tmp_path / "yedek.odbak"
    yedek.write_bytes(
        kap_kur(icerik, dek, baslik=durum_basligi(durum), manifesto=Manifesto(KAPSAM_TAM))
    )
    db = veri_dizini / "db.sqlite3"

    backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert db.read_bytes() == icerik


@pytest.mark.parametrize("kuyruk", [b"", bytes(200)], ids=["yalniz_sihirli_bayt", "tam_boy"])
def test_deneme_yedegi_ayri_iletiyle_reddedilir(
    kuyruk: bytes, tmp_path: Path, veri_dizini: Path
) -> None:
    """Plan F1b-3 "Kap ve manifesto": `ODBAK\\x02` açılmaz; sır sorulmadan, hedefe dokunulmadan
    "deneme sürümüyle alınmış" denir."""
    yedek = tmp_path / "gunluk-2026-08-01.odbak"
    yedek.write_bytes(DENEME_MAGIC + kuyruk)
    db = veri_dizini / "db.sqlite3"
    db.write_bytes(b"onceki")

    with pytest.raises(backup_restore.BackupRestoreError, match="deneme sürümüyle alınmış"):
        backup_restore.restore_database(yedek, db)

    assert db.read_bytes() == b"onceki"


def test_parola_hesapsiz_verilirse_reddedilir(tmp_path: Path, veri_dizini: Path) -> None:
    dek, durum = _dek_ile_durum(PAROLA)
    _guncel_yaz(veri_dizini, durum)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, durum))

    with pytest.raises(backup_restore.BackupRestoreError, match="tanıtıcısını"):
        backup_restore.restore_database(yedek, veri_dizini / "db.sqlite3", password=PAROLA)


def test_hesap_kimligiyle_de_acilir(tmp_path: Path, veri_dizini: Path) -> None:
    dek, durum = _dek_ile_durum(PAROLA)
    _guncel_yaz(veri_dizini, durum)
    icerik = _sqlite_baytlari(tmp_path, "gizli", dek)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(icerik, dek, durum))

    backup_restore.restore_database(
        yedek, veri_dizini / "db.sqlite3", hesap=HESAP_ID, password=PAROLA
    )

    assert (veri_dizini / "db.sqlite3").read_bytes() == icerik


def test_yanlis_parola_hedefe_dokunmaz(tmp_path: Path, veri_dizini: Path) -> None:
    dek, durum = _dek_ile_durum(PAROLA)
    _guncel_yaz(veri_dizini, durum)
    orijinal = _sqlite_baytlari(tmp_path, "orijinal")
    db = veri_dizini / "db.sqlite3"
    db.write_bytes(orijinal)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, durum))

    with pytest.raises(backup_restore.BackupRestoreError, match="açılamadı"):
        backup_restore.restore_database(yedek, db, hesap=HESAP, password="Yanlis-Parola-9")
    with pytest.raises(backup_restore.BackupRestoreError, match="açılamadı"):
        backup_restore.restore_database(yedek, db, hesap="baska-hesap", password=PAROLA)

    assert db.read_bytes() == orijinal
    assert not list(veri_dizini.glob("db-onceki-*"))
    # Geri yükleme denemesi hesap sayacına dokunmaz (gecikme süreç içidir; plan F1b-1).
    guncel = json.loads((veri_dizini / "guvenlik.json").read_text(encoding="utf-8"))
    assert guncel["hesaplar"][0]["hatali"] == 0


def test_sifreli_yedek_sir_olmadan_acilmaz(tmp_path: Path, veri_dizini: Path) -> None:
    dek, durum = _dek_ile_durum(PAROLA)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, durum))

    with pytest.raises(backup_restore.BackupRestoreError, match="şifreli"):
        backup_restore.restore_database(yedek, veri_dizini / "db.sqlite3")


def test_cozulen_icerik_sqlite_degilse_reddedilir(tmp_path: Path, veri_dizini: Path) -> None:
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(b"duz metin, veritabani degil", dek, durum))
    db = veri_dizini / "db.sqlite3"

    with pytest.raises(backup_restore.BackupRestoreError, match="SQLite"):
        backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert not db.exists()


def test_parola_degisse_de_guncel_dosya_ile_acilir(tmp_path: Path, veri_dizini: Path) -> None:
    """Yedek eski parolayla alınmış; kullanıcı YENİ parolasını bilir.

    DEK parola değişiminde değişmediği için güncel guvenlik.json yeni parolayla
    aynı DEK'i verir → yedek açılır ve güncel dosyaya DOKUNULMAZ (en yeni
    sarmalı taşıyan odur)."""
    dek = crypto.new_data_key()
    kurtarma = app_password.generate_recovery_key()
    eski_durum = _durum(dek, "Eski-Parola-1", kurtarma)
    yeni_durum = _durum(dek, "Yeni-Parola-2!", kurtarma)
    _guncel_yaz(veri_dizini, yeni_durum)
    icerik = _sqlite_baytlari(tmp_path, "gizli", dek)
    yedek = tmp_path / "eski-donem.odbak"
    yedek.write_bytes(_sifreli_kapsayici(icerik, dek, eski_durum))
    db = veri_dizini / "db.sqlite3"

    sonuc = backup_restore.restore_database(yedek, db, hesap=HESAP, password="Yeni-Parola-2!")

    assert db.read_bytes() == icerik
    assert sonuc.state_written is False
    guncel = json.loads((veri_dizini / "guvenlik.json").read_text(encoding="utf-8"))
    assert guncel["hesaplar"] == yeni_durum["hesaplar"]


def test_yabanci_guvenlik_dosyasi_arsivlenip_baslik_yazilir(
    tmp_path: Path, veri_dizini: Path
) -> None:
    """Veri klasöründe BAŞKA kuruluma ait dosya: hesap sarmalı aynı parolayla açılır ama
    DEK yanlıştır; AES-GCM reddeder, başlık hesap taşımadığı için parola yolu kapanır.
    Kurtarma anahtarıyla başlık kazanır, yabancı dosya silinmeden arşivlenir."""
    _yabanci_dek, yabanci_durum = _dek_ile_durum(PAROLA)
    _guncel_yaz(veri_dizini, yabanci_durum)
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    icerik = _sqlite_baytlari(tmp_path, "gizli")
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(icerik, dek, durum))
    db = veri_dizini / "db.sqlite3"

    with pytest.raises(backup_restore.BackupRestoreError, match="açılamadı"):
        backup_restore.restore_database(yedek, db, hesap=HESAP, password=PAROLA)
    sonuc = backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert db.read_bytes() == icerik
    assert sonuc.state_written is True
    arsivler = list(veri_dizini.glob("guvenlik-arsiv-*.json"))
    assert len(arsivler) == 1
    arsiv = json.loads(arsivler[0].read_text(encoding="utf-8"))
    assert arsiv["hesaplar"] == yabanci_durum["hesaplar"]
    guncel = json.loads((veri_dizini / "guvenlik.json").read_text(encoding="utf-8"))
    assert guncel["kurtarma"]["sarmal"] == durum["kurtarma"]["sarmal"]
    assert guncel["hesaplar"] == []


def test_capraz_dek_geri_yukleme_yedekleme_json_u_da_esitler(
    tmp_path: Path, veri_dizini: Path
) -> None:
    """Birleşme incelemesi bulgusu: yalnız guvenlik.json onarılıp kardeş
    yedekleme.json bayat kalsaydı kilit açma "anahtar eşleşmiyor" hatasına
    düşer, açılıştaki günlük yedek de İÇERİĞİ eski anahtarla mühürleyip
    başlığa yeni durumu gömerdi — o yedek bir daha açılamazdı."""
    from desktop.backup_crypto import load_public_key, public_key_bytes

    yerli_dek, yerli_durum = _dek_ile_durum(PAROLA)
    _guncel_yaz(veri_dizini, yerli_durum)
    ensure_public_config(veri_dizini, yerli_dek, replace=True)  # bayat kalacak aday
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, durum))

    backup_restore.restore_database(yedek, veri_dizini / "db.sqlite3", recovery_key=kurtarma)

    from cryptography.hazmat.primitives import serialization

    guncel_acik = load_public_key(veri_dizini).public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    assert guncel_acik == public_key_bytes(dek)  # üçlü (db, guvenlik, yedekleme) tutarlı


def test_bassiz_yedek_guncel_guvenlik_dosyasiyla_acilir(tmp_path: Path, veri_dizini: Path) -> None:
    dek, durum = _dek_ile_durum(PAROLA)
    _guncel_yaz(veri_dizini, durum)
    icerik = _sqlite_baytlari(tmp_path, "gizli", dek)
    yedek = tmp_path / "bassiz.odbak"
    yedek.write_bytes(_sifreli_kapsayici(icerik, dek, None))
    db = veri_dizini / "db.sqlite3"

    sonuc = backup_restore.restore_database(yedek, db, hesap=HESAP, password=PAROLA)

    assert db.read_bytes() == icerik
    assert sonuc.state_written is False


def test_bassiz_yedek_guvenlik_dosyasi_yokken_yol_gosterir(
    tmp_path: Path, veri_dizini: Path
) -> None:
    dek, _durum = _dek_ile_durum(PAROLA)
    yedek = tmp_path / "bassiz.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, None))

    with pytest.raises(backup_restore.BackupRestoreError, match="guvenlik.json"):
        backup_restore.restore_database(
            yedek, veri_dizini / "db.sqlite3", hesap=HESAP, password=PAROLA
        )


def test_sema_1_baslikli_eski_yedek_aday_degildir(tmp_path: Path, veri_dizini: Path) -> None:
    """Şema 1 başlığı (tek parola bölümü) kullanılamaz sayılır (plan F1b-1 "Eski veri")."""
    dek = crypto.new_data_key()
    sema_1 = {"surum": 1, "kdf": {}, "parola": {"salt": "eA==", "sarmal": "eA=="}}
    yedek = tmp_path / "eski.odbak"
    yedek.write_bytes(
        cast(
            "bytes",
            kap_kur(
                _sqlite_baytlari(tmp_path, "eski"), dek, baslik=json.dumps(sema_1).encode("utf-8")
            ),
        )
    )

    assert backup_restore.inspect_backup(yedek).embedded_state is None


# ---------------------------------------------------------------------------
# Yedek başlığının `kdf`'si: mühürden önce kullanılır, güvenilmezdir
# ---------------------------------------------------------------------------
#: Sayılar yazılıdır: tavan `crypto.KdfParams()`'tan türer, test de türetseydi katın kayması ya da
#: tavanın testlerde ucuz profile inen `DEFAULT_KDF`'e bağlanması görünmezdi.
_UCUZ_KDF = {"time_cost": 1, "memory_cost": 8, "parallelism": 1}
_PROFIL_KDF = {"time_cost": 3, "memory_cost": 65536, "parallelism": 4}
_TAVAN_KDF = {"time_cost": 48, "memory_cost": 1048576, "parallelism": 64}

_SINIR_DISI_KDF = [
    pytest.param({**_TAVAN_KDF, "time_cost": 49}, id="sure_tavan_ustu"),
    pytest.param({**_TAVAN_KDF, "memory_cost": 1048577}, id="bellek_tavan_ustu"),
    pytest.param({**_TAVAN_KDF, "parallelism": 65}, id="kulvar_tavan_ustu"),
    pytest.param({**_UCUZ_KDF, "time_cost": 0}, id="sure_sifir"),
    pytest.param({**_UCUZ_KDF, "time_cost": -1}, id="sure_eksi"),
    pytest.param({**_UCUZ_KDF, "parallelism": 0}, id="kulvar_sifir"),
    pytest.param({**_UCUZ_KDF, "memory_cost": 7}, id="bellek_kulvarin_altinda"),
    pytest.param({**_PROFIL_KDF, "memory_cost": 31}, id="bellek_dort_kulvarin_altinda"),
    pytest.param({**_UCUZ_KDF, "memory_cost": 2**40}, id="bellek_uint32_ustu"),
    pytest.param({**_UCUZ_KDF, "time_cost": "x"}, id="metin"),
    pytest.param({**_UCUZ_KDF, "time_cost": None}, id="bos"),
    pytest.param({**_UCUZ_KDF, "parallelism": []}, id="liste"),
    pytest.param({**_UCUZ_KDF, "memory_cost": float("inf")}, id="sonsuz"),
    pytest.param({**_UCUZ_KDF, "memory_cost": float("nan")}, id="sayi_degil"),
]


def _argon2_kosamaz(*args: Any, **kwargs: Any) -> bytes:
    raise HashingError("Memory allocation error")


@pytest.mark.parametrize("kdf", _SINIR_DISI_KDF)
def test_sinir_disi_baslik_kdfsi_argon2ye_gitmez(
    tmp_path: Path, veri_dizini: Path, monkeypatch: pytest.MonkeyPatch, kdf: dict[str, Any]
) -> None:
    """Yeni bilgisayar: tek aday başlıktı, aday olmaz. Mühür sınanmadan süreç belleğe boğulmaz,
    bitmeyen bir işe girmez, ham hata çıkmaz; hiçbir dosya değişmez."""
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "hazirlanmis.odbak"
    yedek.write_bytes(
        _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, {**durum, "kdf": kdf})
    )
    db = veri_dizini / "db.sqlite3"
    turetimler: list[Any] = []
    monkeypatch.setattr(crypto, "derive_key", lambda *a, **k: turetimler.append(k))

    with pytest.raises(backup_restore.BackupRestoreError, match="kurtarma başlığı yok"):
        backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert turetimler == []
    assert not db.exists()
    assert not (veri_dizini / "guvenlik.json").exists()


@pytest.mark.parametrize(
    "kdf",
    [
        pytest.param(_UCUZ_KDF, id="en_ucuz"),
        pytest.param(_PROFIL_KDF, id="programin_profili"),
        pytest.param(_TAVAN_KDF, id="tavanin_kendisi"),
        pytest.param({**_PROFIL_KDF, "memory_cost": 32}, id="dort_kulvarin_alt_siniri"),
        pytest.param({}, id="yazilmamis_alan_profildir"),
    ],
)
def test_makul_baslik_kdfsi_aday_kalir(kdf: dict[str, Any]) -> None:
    _dek, durum = _dek_ile_durum(PAROLA)
    baslik = {**durum, "kdf": kdf}

    adaylar = backup_restore._candidate_states(backup_restore.BackupInfo(embedded_state=baslik))

    assert adaylar == [(backup_restore._SOURCE_EMBEDDED, baslik)]


def test_sinir_disi_baslik_guncel_dosyayla_acilmayi_engellemez(
    tmp_path: Path, veri_dizini: Path
) -> None:
    """Başlık aday olmasa da aynı bilgisayarda güncel dosya yedeği açar."""
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    _guncel_yaz(veri_dizini, durum)
    icerik = _sqlite_baytlari(tmp_path, "gizli")
    yedek = tmp_path / "hazirlanmis.odbak"
    yedek.write_bytes(_sifreli_kapsayici(icerik, dek, {**durum, "kdf": {"memory_cost": 2**40}}))
    db = veri_dizini / "db.sqlite3"

    sonuc = backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert db.read_bytes() == icerik
    assert sonuc.state_written is False


def test_guncel_dosyanin_kdfsi_baslik_sinirindan_gecmez(veri_dizini: Path) -> None:
    """Sınır yalnız güvenilmez başlığındır: güncel dosya aday kalır, "kayıp" sayılmaz (kural tek;
    `guvenlik.json`'un biçimsiz `kdf`'si kabul edilmiş kalan risktir, plan F1b-2 ekleri)."""
    _dek, durum = _dek_ile_durum(PAROLA)
    guncel = {**durum, "kdf": {**durum["kdf"], "parallelism": 0}}
    _guncel_yaz(veri_dizini, guncel)

    adaylar = backup_restore._candidate_states(backup_restore.BackupInfo())

    assert adaylar == [(backup_restore._SOURCE_CURRENT, guncel)]
    assert app_password.security_file_missing() is False


@pytest.mark.parametrize("neden", ["bellek_ayrilamadi", "tuz_kisa"])
def test_baslikta_argon2_hatasi_turkce_hataya_cikar(
    tmp_path: Path,
    veri_dizini: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    neden: str,
) -> None:
    """Değerleri makul başlıkta Argon2 yine de koşamayabilir; ham hata kullanıcıya çıkmaz.

    Doğru anahtarın "hatalı" görünmesinin nedeni günlükte durur (BTR için); sır yazılmaz."""
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    if neden == "tuz_kisa":
        durum = {**durum, "kurtarma": {**durum["kurtarma"], "salt": "eA=="}}
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, durum))
    if neden == "bellek_ayrilamadi":
        monkeypatch.setattr(crypto, "derive_key", _argon2_kosamaz)
    db = veri_dizini / "db.sqlite3"

    with (
        caplog.at_level(logging.WARNING, logger="oab_defteri.restore"),
        pytest.raises(backup_restore.BackupRestoreError, match="Yedek açılamadı"),
    ):
        backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert not db.exists()
    uyarilar = [
        kayit.getMessage() for kayit in caplog.records if kayit.name == "oab_defteri.restore"
    ]
    assert uyarilar == [
        "Yedek başlığıyla anahtar türetilemedi (bellek yetersiz ya da başlık bozuk); "
        "sıradaki aday deneniyor."
    ]
    assert kurtarma not in caplog.text


def test_guncel_dosyada_argon2_hatasi_cagirana_cikar(
    tmp_path: Path, veri_dizini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Güncel dosyanın kolu değişmez: `_try_unwrap_account`'un "kdf hatası çağırana çıkar" kuralı."""
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    _guncel_yaz(veri_dizini, durum)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, durum))
    monkeypatch.setattr(crypto, "derive_key", _argon2_kosamaz)

    with pytest.raises(HashingError):
        backup_restore.restore_database(yedek, veri_dizini / "db.sqlite3", recovery_key=kurtarma)


def test_baslikta_kdf_bolumunun_tek_bit_donmesi_turkce_hataya_cikar(
    tmp_path: Path, veri_dizini: Path
) -> None:
    """Kasıtsız yol: gerçek bir yedeğin başlığında tek bit dönmesi kulvarı sıfıra indirebilir
    (0x31 → 0x30). Her dönmede kullanıcı Türkçe iletiyi görür, hiçbir dosya değişmez."""
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    kap = _sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, durum)
    yedek = tmp_path / "bit.odbak"
    db = veri_dizini / "db.sqlite3"

    for konum in range(kap.index(b'"kdf"'), kap.index(b'"kurtarma"')):
        for bit in range(8):
            bozuk = bytearray(kap)
            bozuk[konum] ^= 1 << bit
            yedek.write_bytes(bozuk)
            with pytest.raises(backup_restore.BackupRestoreError):
                backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert not db.exists()


def test_yedek_kurtarma_anahtarinin_kimligini_soyler(tmp_path: Path) -> None:
    dek, durum = _dek_ile_durum(PAROLA)
    durum["kurtarma"].update(no=3, tarih="2026-11-01")
    yedek = tmp_path / "yedek.odbak"
    yedek.write_bytes(_sifreli_kapsayici(b"x", dek, durum))
    bilgi = backup_restore.inspect_backup(yedek)
    assert bilgi.recovery_key_label == "3 numaralı, 01.11.2026 tarihli"
    assert bilgi.kapsam == KAPSAM_YEREL
    yedek.write_bytes(_sifreli_kapsayici(b"x", dek, None))
    assert backup_restore.inspect_backup(yedek).recovery_key_label == ""


# ---------------------------------------------------------------------------
# manage.py restore_backup komutu
# ---------------------------------------------------------------------------
def test_komut_duz_yedegi_reddeder(
    tmp_path: Path, veri_dizini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = veri_dizini / "db.sqlite3"
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(db))
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sqlite_baytlari(tmp_path, "komut"))

    with pytest.raises(CommandError, match="şifrelenmemiş"):
        call_command("restore_backup", str(yedek), "--yes", "--hesap", HESAP, "--password", PAROLA)

    assert not db.exists()


def test_komut_sifreli_yedegi_hesap_ve_parolayla_acar(
    tmp_path: Path, veri_dizini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = veri_dizini / "db.sqlite3"
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(db))
    dek, durum = _dek_ile_durum(PAROLA)
    _guncel_yaz(veri_dizini, durum)
    icerik = _sqlite_baytlari(tmp_path, "gizli", dek)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(icerik, dek, durum))
    cikti = StringIO()

    call_command(
        "restore_backup",
        str(yedek),
        "--yes",
        "--hesap",
        HESAP,
        "--password",
        PAROLA,
        stdout=cikti,
    )

    assert db.read_bytes() == icerik
    assert "kurtarma başlığından" not in cikti.getvalue()
    # `db-onceki` rotasyondadır (tasarım §4.4.7): "silinmez" sözü verilmez.
    assert "14 gün saklanır, sonra silinir" in cikti.getvalue()
    assert "silinmez" not in cikti.getvalue()


def test_komut_kurtarma_anahtariyla_baslik_yazar(
    tmp_path: Path, veri_dizini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = veri_dizini / "db.sqlite3"
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(db))
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "gizli"), dek, durum))
    cikti = StringIO()

    call_command("restore_backup", str(yedek), "--yes", "--recovery-key", kurtarma, stdout=cikti)

    assert "kurtarma başlığından" in cikti.getvalue()
    assert "program yöneticisinin parolasını" in cikti.getvalue()


def test_komut_onay_reddinde_dokunmaz(
    tmp_path: Path, veri_dizini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = veri_dizini / "db.sqlite3"
    orijinal = _sqlite_baytlari(tmp_path, "orijinal")
    db.write_bytes(orijinal)
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(db))
    monkeypatch.setattr("builtins.input", lambda *args: "h")
    dek, durum = _dek_ile_durum(PAROLA)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"), dek, durum))
    cikti = StringIO()

    call_command("restore_backup", str(yedek), stdout=cikti)

    assert "iptal" in cikti.getvalue()
    assert db.read_bytes() == orijinal


def test_komut_istemi_ve_yardimi_program_yoneticisini_anar(
    tmp_path: Path, veri_dizini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Parolayla geri yüklemeyi yalnız program yöneticisi yapar (sözlük "Yedek"; tasarım
    §4.4.4): istem, yardım ve sırsız ret iletisi bunu baştan söyler."""
    db = veri_dizini / "db.sqlite3"
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(db))
    dek, durum = _dek_ile_durum(PAROLA)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"), dek, durum))
    istemler: list[str] = []

    def girdi(istem: str = "") -> str:
        istemler.append(istem)
        return ""

    monkeypatch.setattr("builtins.input", girdi)

    with pytest.raises(CommandError) as hata:
        call_command("restore_backup", str(yedek), "--yes", stdout=StringIO())

    assert istemler[0] == (
        "Program yöneticisi hesabının tanıtıcısı (kurtarma anahtarıyla açmak için boş bırakın): "
    )
    assert "program yöneticisi hesabının tanıtıcısı ve parolası ya da kurtarma anahtarı" in str(
        hata.value
    )
    assert not db.exists()
    yardim = {
        eylem.dest: eylem.help
        for eylem in RestoreBackupCommand().create_parser("manage.py", "restore_backup")._actions
    }
    assert yardim["hesap"] == "Program yöneticisi hesabının tanıtıcısı (parola yolu)."
    assert str(yardim["password"]).startswith("Program yöneticisi hesabının parolası")


def test_komut_bellek_ici_veritabanini_reddeder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", ":memory:")
    dek, durum = _dek_ile_durum(PAROLA)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"), dek, durum))

    with pytest.raises(CommandError, match="dosya tabanlı değil"):
        call_command("restore_backup", str(yedek), "--yes")


def test_komut_okunamayan_dosyada_turkce_hata_verir(tmp_path: Path) -> None:
    with pytest.raises(CommandError, match="okunamadı"):
        call_command("restore_backup", str(tmp_path / "yok.odbak"), "--yes")


# ---------------------------------------------------------------------------
# Geri yükleme notu (tasarım §4.4.4; plan F1b-1 alt commit c)
# ---------------------------------------------------------------------------
def _izli_sqlite(dizin: Path, satirlar: list[tuple[int, str]]) -> bytes:
    """Denetim izi tablosu taşıyan (yalnız `seq`, `mac`) gerçek bir SQLite dosyası."""
    yol = dizin / f"izli-{len(satirlar)}.sqlite3"
    with closing(sqlite3.connect(yol)) as baglanti:
        baglanti.execute("CREATE TABLE okul_audittrail (seq INTEGER PRIMARY KEY, mac TEXT)")
        baglanti.executemany("INSERT INTO okul_audittrail VALUES (?, ?)", satirlar)
        baglanti.commit()
    return yol.read_bytes()


def _not(veri_dizini: Path) -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        json.loads((veri_dizini / "geri-yukleme-notu.json").read_text(encoding="utf-8")),
    )


def test_geri_yukleme_notu_kenara_alinanin_ozetini_zincir_basini_ve_hesabi_yazar(
    tmp_path: Path, veri_dizini: Path
) -> None:
    db = veri_dizini / "db.sqlite3"
    db.write_bytes(_izli_sqlite(tmp_path, [(1, "aa" * 32), (7, "bb" * 32)]))
    dek, durum = _dek_ile_durum(PAROLA)
    _guncel_yaz(veri_dizini, durum)
    yedek = tmp_path / "gunluk-2026-10-30.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni", dek), dek, durum))

    sonuc = backup_restore.restore_database(yedek, db, hesap=HESAP, password=PAROLA)

    assert sonuc.old_db_path is not None
    (kayit,) = _not(veri_dizini)["geri_yuklemeler"]
    assert kayit["yedek"] == "gunluk-2026-10-30.odbak"
    assert kayit["onceki"] == {
        "dosya": sonuc.old_db_path.name,
        "sha256": hashlib.sha256(sonuc.old_db_path.read_bytes()).hexdigest(),
        "zincir_basi": {"seq": 7, "mac": "bb" * 32},
    }
    assert kayit["yol"] == {"tur": "hesap", "hesap": HESAP_ID, "tanitici": HESAP}
    assert _not(veri_dizini)["bekleyen_olaylar"] == []
    if os.name == "posix":
        kip = (veri_dizini / "geri-yukleme-notu.json").stat().st_mode & 0o777
        assert kip == 0o600


def test_kurtarma_yolunda_not_anahtarin_no_sunu_yazar_ikinci_geri_yukleme_eklenir(
    tmp_path: Path, veri_dizini: Path
) -> None:
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"), dek, durum))
    db = veri_dizini / "db.sqlite3"

    backup_restore.restore_database(yedek, db, recovery_key=kurtarma)  # hedef yokken
    backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    ilk, ikinci = _not(veri_dizini)["geri_yuklemeler"]
    assert ilk["onceki"] is None
    assert ilk["yol"] == {"tur": "kurtarma", "no": 1}
    # İkinci geri yüklemede kenara alınan, birincinin getirdiği (izsiz) veritabanıdır.
    assert ikinci["onceki"]["zincir_basi"] is None
    assert ikinci["onceki"]["dosya"].startswith("db-onceki-")


def test_uygulama_icinde_kurtarma_yolunda_not_oturumdaki_hesabi_da_yazar(
    tmp_path: Path, veri_dizini: Path
) -> None:
    """Hakkında "Açık oturum, sahibinin imzasıdır": oturum açıkken kurtarma anahtarıyla yapılan
    geri yükleme de onu başlatan hesaba bağlanır (`oturum`); konsolda oturum yoktur."""
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"), dek, durum))
    db = veri_dizini / "db.sqlite3"

    backup_restore.restore_database(yedek, db, recovery_key=kurtarma, oturum_hesabi=HESAP_ID)
    backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    ilk, ikinci = _not(veri_dizini)["geri_yuklemeler"]
    assert ilk["yol"] == {"tur": "kurtarma", "no": 1} and ilk["oturum"] == HESAP_ID
    assert "oturum" not in ikinci


@pytest.mark.parametrize("capa", ["yok", "var", "bozuk"])
def test_geri_yukleme_notu_takastan_onceki_capayi_yazar(
    tmp_path: Path, veri_dizini: Path, capa: str
) -> None:
    """Bağımsız denetim bulgusu: kurulumdan sonra hiç kilitlenmeden yapılan geri yükleme ilk
    kilit açılışında yanlış "kilit işareti bulunamadı" uyarısı veriyordu. Not takastan önceki
    çapayı da yazar: yoksa `null` ("çapa yoktu"), varsa `{seq, mac}` (mühür ve tohum nota
    GİRMEZ), okunamıyorsa alan hiç yazılmaz ("bilinmiyor")."""
    iz = veri_dizini / "iz-durumu.json"
    if capa == "var":
        iz.write_text(
            json.dumps(
                {
                    "surum": 1,
                    "capa": {"seq": 7, "mac": "bb" * 32, "muhur": "cc" * 32},
                    "tohum": "dd" * 32,
                    "adim": 0,
                }
            ),
            encoding="utf-8",
        )
    elif capa == "bozuk":
        iz.write_text("{bozuk", encoding="utf-8")
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"), dek, durum))

    backup_restore.restore_database(yedek, veri_dizini / "db.sqlite3", recovery_key=kurtarma)

    (kayit,) = _not(veri_dizini)["geri_yuklemeler"]
    if capa == "yok":
        assert kayit["capa"] is None
    elif capa == "var":
        assert kayit["capa"] == {"seq": 7, "mac": "bb" * 32}
        assert "cc" * 32 not in json.dumps(kayit) and "dd" * 32 not in json.dumps(kayit)
    else:
        assert "capa" not in kayit


def test_not_yazilamasa_da_geri_yukleme_basarilidir(
    tmp_path: Path, veri_dizini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from apps.okul.services import geri_yukleme_notu

    def yazilamadi(*_a: object, **_k: object) -> None:
        raise OSError("disk dolu")

    monkeypatch.setattr(geri_yukleme_notu, "atomik_json_yaz", yazilamadi)
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yeni = _sqlite_baytlari(tmp_path, "yeni")
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(yeni, dek, durum))
    db = veri_dizini / "db.sqlite3"

    backup_restore.restore_database(yedek, db, recovery_key=kurtarma)

    assert db.read_bytes() == yeni
    assert not (veri_dizini / "geri-yukleme-notu.json").exists()


def test_basarisiz_geri_yukleme_not_yazmaz(tmp_path: Path, veri_dizini: Path) -> None:
    dek, durum = _dek_ile_durum(PAROLA)
    _guncel_yaz(veri_dizini, durum)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"), dek, durum))

    with pytest.raises(backup_restore.BackupRestoreError):
        backup_restore.restore_database(
            yedek, veri_dizini / "db.sqlite3", hesap=HESAP, password="Yanlis-Parola-9"
        )

    assert not (veri_dizini / "geri-yukleme-notu.json").exists()


#: Bozuk not içerikleri: biçimsiz JSON ve derin iç içe dizi (`json.loads`'un `RecursionError`'ı;
#: bağımsız denetim bulgusu: takastan SONRA notun yazımında düşüyordu).
_BOZUK_NOTLAR = {"bicimsiz": "{bozuk", "derin_ic_ice": "[" * 30_000 + "]" * 30_000}


@pytest.mark.parametrize("icerik", sorted(_BOZUK_NOTLAR))
def test_bozuk_notun_ustune_yeni_kayit_isaretle_yazilir(
    icerik: str, tmp_path: Path, veri_dizini: Path
) -> None:
    """Bozuk not geri yüklemeyi düşürmez: takas yapılır, yeni not `bozuk_not_vardi` taşır."""
    (veri_dizini / "geri-yukleme-notu.json").write_text(_BOZUK_NOTLAR[icerik], encoding="utf-8")
    kurtarma = app_password.generate_recovery_key()
    dek, durum = _dek_ile_durum(PAROLA, kurtarma)
    yedek = tmp_path / "gunluk.odbak"
    yedek.write_bytes(_sifreli_kapsayici(_sqlite_baytlari(tmp_path, "yeni"), dek, durum))

    backup_restore.restore_database(yedek, veri_dizini / "db.sqlite3", recovery_key=kurtarma)

    notu = _not(veri_dizini)
    assert notu["bozuk_not_vardi"] is True
    assert len(notu["geri_yuklemeler"]) == 1
    assert (veri_dizini / "db.sqlite3").is_file()  # takas yapıldı, hata yükselmedi
