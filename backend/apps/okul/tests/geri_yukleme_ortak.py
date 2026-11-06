"""Geri yükleme testlerinin ortak yardımcıları (toplanmaz: dosya adı `test_` ile başlamaz).

Parola yolundaki geri yükleme, parolası verilen hesabı program yöneticisi olarak doğrular
(`services.geri_yukleme_yetkisi`; tasarım §4.4.4). Yetki okuyucusu ORM'siz iki tablo okur:
`okul_schoolconfig` (veri anahtarının parmak izi) ve `okul_account` (mühürlü hesap satırları).
`yetkili_sqlite` bu iki tabloyu ve içerik sınamaları için bir `kayit` tablosunu taşıyan gerçek
bir SQLite dosyası kurar. Satırlar Django'nun SQLite'a yazdığı biçimdedir: kimlik tiresiz 32
hane, zaman saat dilimsiz UTC metni (mikrosaniye sıfırsa kesirsiz). Bu biçimin ORM'inkiyle
aynı olduğunu `test_geri_yukleme_yetkisi.py::test_orm_siz_okuyucu_orm_muhruyle_ayni` sabitler.

Dosya varsayılan olarak WAL kipinde kurulur: programın yedeği WAL kipindeki veritabanından
alındığı için görüntünün başlığı WAL işaretlidir (18-19. baytlar 2) ve okuyucu bunu bellekte
yamamak zorundadır. Adlar ve kimlikler uydurmadır; gerçek kişi değildir.

Hesap satırı güvenlik dosyasındaki sarmalın özetini taşır (`wrap_digest`; kullanıcı kararı
03.11.2026 "tazelik kapatılır"). `HesapSatiri.ozet` verilmezse satır KURULDUĞU ANDA güvenlik
dosyasında o kimliği taşıyan ilk sarmalın özetiyle yazılır (sarmal yoksa boş); verilirse aynen.

Hesap satırı denetim izindeki son içerik MAC'li kaydını da tutmalıdır (kullanıcı kararı 03.11.2026
"Girişte reddet"; `services.satir_izi`). Dosya bu yüzden `okul_auditkey` (DEK'le şifreli uydurma
İA) ve `okul_audittrail` tablolarını da taşır; `HesapSatiri.iz` doğruysa her hesabın satırı için,
satırın YAZILDIĞI hâlinin içerik MAC'iyle `SISTEM` `HESAP` iz satırı yazılır (meşru program yazımı
gibi). İçerik MAC'i ve zincir MAC'i burada okuyucudan BAĞIMSIZ kurulur (`kanonik` ile, alanlar
sözlükten): okuyucunun ham sütun çevirisi böylece sınanır. Hesap tablosu içerik MAC'ine giren
bütün sütunları taşır; ad-soyad DEK'le şifreli uydurma addır.

Ekli görüntü (`ekli_sqlite`; plan F1b-3 "Geri yükleme"): `yetkili_sqlite`'ın dosyasına göçün kurduğu
`okul_attachment` sütunları eklenir, satırlar depo servisinin yazdığı biçimdedir. `OrnekEk` kabı ve
sarmalı gerçektir (`ds.dosya_hazirla`). Gerçek şema ve gerçek yazıcı
`test_tam_yedek.py::test_tam_yedekte_ekli_kayit_geri_yuklemeden_sonra_acilir`'de sınanır. Kişi adı
taşıyan özgün ad uydurmadır ve yalnız raporda ya da notta bulunmadığını göstermek içindir.
"""

from __future__ import annotations

import base64
import sqlite3
import uuid
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from cryptography.fernet import Fernet
from desktop.backup_crypto import (
    KAPSAM_YEREL,
    Manifesto,
    ManifestoGirdisi,
    private_key_from_data_key,
    tam_yedek_yaz,
)
from desktop.tests.kap_ortak import durum_basligi, kap_kur
from django.db import connection, transaction

from apps.okul.services import app_password, backup_restore, geri_yukleme_yetkisi
from conftest import TEST_DEK, TEST_IA
from shared import crypto, kanonik
from shared import dosya_sifreleme as ds

#: Uydurma açılış anı (UTC; mikrosaniyesiz: Django kesirsiz yazar).
ACILIS = datetime(2026, 10, 31, 7, 30, tzinfo=UTC)
#: Satırların uydurma ad-soyadı (DEK'le şifreli yazılır; gerçek kişi değildir).
AD_SOYAD = "Örnek Hesap Sahibi"
#: Görüntünün iz anahtarı (`conftest.TEST_IA`) ve `AuditKey` kimliği.
IZ_ANAHTARI = TEST_IA
IZ_KAYDI = 1


@dataclass(frozen=True)
class HesapSatiri:
    """`okul_account` satırı. `muhur` None ise DEK'le doğru mühür yazılır; verilirse aynen."""

    id: str
    login_name: str
    role: str = "yonetici"
    status: str = "ACIK"
    opened_at: datetime = ACILIS
    closed_at: datetime | None = None
    muhur: str | None = None
    #: Sarmal özeti; None ise güvenlik dosyasındaki sarmaldan hesaplanır (modül başlığı).
    ozet: str | None = None
    bekleyen_ozet: str = ""
    #: Satırın iz satırı yazılsın mı (modül başlığı); yanlışsa satırın izi yoktur (fail-closed).
    iz: bool = True


def sarmal_ozeti(dek: bytes, hesap_id: str) -> str:
    """Güvenlik dosyasında bu kimliği taşıyan İLK sarmalın özeti; sarmal yoksa boş metin."""
    sarmal = app_password._find_wrap(app_password.read_state() or {}, str(uuid.UUID(hesap_id)))
    return (app_password.wrap_digest(dek, sarmal) or "") if sarmal is not None else ""


def ozet(dek: bytes, satir: HesapSatiri) -> str:
    """Satırın yazılacak asıl özeti (verilmediyse dosyadaki sarmalınki)."""
    return sarmal_ozeti(dek, satir.id) if satir.ozet is None else satir.ozet


def ozetli(dek: bytes, satir: HesapSatiri) -> HesapSatiri:
    """Özeti BUGÜNKÜ dosyaya göre sabitlenmiş satır (dosya sonra değişse de satır değişmez)."""
    return replace(satir, ozet=ozet(dek, satir))


def muhur(dek: bytes, satir: HesapSatiri) -> str:
    """Satırın bu DEK'le mührü (`Account.compute_seal` ile aynı sözleşme)."""
    return kanonik.hesap_muhru(
        crypto.account_seal_key(dek),
        {
            "id": str(uuid.UUID(satir.id)),
            "login_name": satir.login_name,
            "role": satir.role,
            "status": satir.status,
            "person": None,
            "membership": None,
            "term": None,
            "opened_at": satir.opened_at,
            "closed_at": satir.closed_at,
            "wrap_digest": ozet(dek, satir),
            "wrap_digest_pending": satir.bekleyen_ozet,
        },
    )


def program_disindan(
    dek: bytes, satir: HesapSatiri, *, role: str | None = None, status: str | None = None
) -> HesapSatiri:
    """Mührü eski değerlerle kalıp rolü ya da durumu değiştirilmiş satır (program dışından
    yazım taklidi; tehdit 19)."""
    sabit = ozetli(dek, satir)
    return replace(
        sabit,
        role=satir.role if role is None else role,
        status=satir.status if status is None else status,
        muhur=muhur(dek, sabit),
    )


def _django_zamani(an: datetime | None) -> str | None:
    """Django'nun SQLite'a yazdığı biçim: saat dilimsiz UTC, `str(datetime)`."""
    if an is None:
        return None
    return str(an.astimezone(UTC).replace(tzinfo=None))


def _fernet(dek: bytes) -> Fernet:
    return Fernet(base64.urlsafe_b64encode(dek))


def ozet_alanlari(dek: bytes, satir: HesapSatiri, muhur_: str) -> dict[str, Any]:
    """Satırın içerik MAC'ine giren alanları (`Account.IZ_OZET_ALANLARI`), okuyucudan bağımsız."""
    return {
        "login_name": satir.login_name,
        "role": satir.role,
        "display_name": AD_SOYAD,
        "status": satir.status,
        "suspend_reason": "",
        "opened_at": satir.opened_at,
        "opened_by": None,
        "closed_at": satir.closed_at,
        "closed_by": None,
        "password_changed_at": None,
        "reset_at": None,
        "reset_by": None,
        "reset_kind": "",
        "reset_notice_pending": False,
        "last_login_at": None,
        "wrap_digest": ozet(dek, satir),
        "wrap_digest_pending": satir.bekleyen_ozet,
        "seal": muhur_,
    }


def iz_satiri_ekle(
    baglanti: sqlite3.Connection, *, hesap_id: str, alanlar: dict[str, Any], an: datetime = ACILIS
) -> None:
    """Zincirin sonuna hesabın `SISTEM` `HESAP` satırı: içerik MAC'i `alanlar`dan (okuyucudan
    bağımsız; `kanonik` ile), zincir MAC'i `IZ_ANAHTARI`yla."""
    bas = baglanti.execute(
        "SELECT seq, mac FROM okul_audittrail ORDER BY seq DESC LIMIT 1"
    ).fetchone()
    seq, prev = (1, "") if bas is None else (int(bas[0]) + 1, str(bas[1]))
    kimlik = str(uuid.UUID(hesap_id))
    record_mac = kanonik.kayit_mac(
        crypto.record_summary_key(IZ_ANAHTARI), "okul.Account", kimlik, alanlar
    )
    satir = {
        "seq": seq,
        "at": an,
        "actor": "SISTEM",
        "account": None,
        "role": "",
        "action": "HESAP",
        "model": "okul.Account",
        "object_id": kimlik,
        "term": None,
        "changed_fields": [],
        "values": {},
        "record_mac": record_mac,
        "compliance_item": None,
        "label": "",
        "key_mode": "ACIK",
        "key_ref": str(IZ_KAYDI),
    }
    mac = kanonik.iz_mac(crypto.audit_chain_key(IZ_ANAHTARI), satir, prev)
    baglanti.execute(
        "INSERT INTO okul_audittrail VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            seq,
            _django_zamani(an),
            "SISTEM",
            "",
            "HESAP",
            "okul.Account",
            kimlik,
            "[]",
            "{}",
            record_mac,
            "",
            "ACIK",
            str(IZ_KAYDI),
            prev,
            mac,
        ),
    )


def yetkili_sqlite(
    yol: Path,
    *,
    dek: bytes,
    hesaplar: Iterable[HesapSatiri],
    isaret: str = "",
    okul_karti: int = 1,
    parmak_izi: str | None = None,
    wal: bool = True,
) -> bytes:
    """Okul kartı, mühürlü hesap satırları, iz anahtarı ve satırların izini taşıyan SQLite dosyası
    kurar; baytlarını döndürür.

    `okul_karti` okul kartının satır sayısıdır (tek olmalı; 0 ve 2 "okunamıyor" sınaması);
    `parmak_izi` verilmezse bu DEK'in parmak izi yazılır.
    """
    yol.unlink(missing_ok=True)
    izi = crypto.key_fingerprint(dek) if parmak_izi is None else parmak_izi
    with closing(sqlite3.connect(yol)) as baglanti:
        if wal:
            baglanti.execute("PRAGMA journal_mode=WAL")
        baglanti.execute("CREATE TABLE kayit (deger TEXT)")
        baglanti.execute("INSERT INTO kayit VALUES (?)", (isaret,))
        baglanti.execute(
            "CREATE TABLE okul_schoolconfig "
            "(id integer NOT NULL PRIMARY KEY, app_password_hash varchar(255) NOT NULL)"
        )
        baglanti.executemany(
            "INSERT INTO okul_schoolconfig VALUES (?, ?)",
            [(sira, izi) for sira in range(1, okul_karti + 1)],
        )
        baglanti.execute(
            "CREATE TABLE okul_account (id char(32) NOT NULL PRIMARY KEY, "
            "login_name varchar(32) NOT NULL, role varchar(24) NOT NULL, "
            "display_name text NOT NULL, status varchar(24) NOT NULL, "
            "suspend_reason varchar(16) NOT NULL, opened_at datetime NOT NULL, "
            "opened_by_id char(32) NULL, closed_at datetime NULL, closed_by_id char(32) NULL, "
            "password_changed_at datetime NULL, reset_at datetime NULL, "
            "reset_by_id char(32) NULL, reset_kind varchar(16) NOT NULL, "
            "reset_notice_pending bool NOT NULL, last_login_at datetime NULL, "
            "wrap_digest varchar(64) NOT NULL, wrap_digest_pending varchar(64) NOT NULL, "
            "seal varchar(64) NOT NULL)"
        )
        baglanti.execute(
            "CREATE TABLE okul_auditkey (id integer NOT NULL PRIMARY KEY, [key] text NOT NULL, "
            "valid_from_seq bigint unsigned NOT NULL UNIQUE, created_at datetime NOT NULL, "
            "retired_at datetime NULL)"
        )
        baglanti.execute(
            "INSERT INTO okul_auditkey VALUES (?, ?, 1, ?, NULL)",
            (
                IZ_KAYDI,
                _fernet(dek).encrypt(base64.b64encode(IZ_ANAHTARI)).decode("ascii"),
                _django_zamani(ACILIS),
            ),
        )
        baglanti.execute(
            "CREATE TABLE okul_audittrail (seq bigint unsigned NOT NULL PRIMARY KEY, "
            "[at] datetime NOT NULL, actor varchar(8) NOT NULL, account_id char(32) NULL, "
            "role varchar(24) NOT NULL, action varchar(16) NOT NULL, model varchar(64) NOT NULL, "
            "object_id varchar(64) NOT NULL, changed_fields text NOT NULL, "
            "[values] text NOT NULL, record_mac varchar(64) NOT NULL, label varchar(16) NOT NULL, "
            "key_mode varchar(8) NOT NULL, key_ref varchar(64) NOT NULL, "
            "prev_mac varchar(64) NOT NULL, mac varchar(64) NOT NULL)"
        )
        sabitler = [ozetli(dek, satir) for satir in hesaplar]
        ad_belirteci = _fernet(dek).encrypt(AD_SOYAD.encode("utf-8")).decode("ascii")
        for satir in sabitler:
            muhur_ = muhur(dek, satir) if satir.muhur is None else satir.muhur
            baglanti.execute(
                "INSERT INTO okul_account (id, login_name, role, display_name, status, "
                "suspend_reason, opened_at, closed_at, reset_kind, reset_notice_pending, "
                "wrap_digest, wrap_digest_pending, seal) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)",
                (
                    uuid.UUID(satir.id).hex,
                    satir.login_name,
                    satir.role,
                    ad_belirteci,
                    satir.status,
                    "",
                    _django_zamani(satir.opened_at),
                    _django_zamani(satir.closed_at),
                    "",
                    satir.ozet,
                    satir.bekleyen_ozet,
                    muhur_,
                ),
            )
            if satir.iz:
                iz_satiri_ekle(
                    baglanti, hesap_id=satir.id, alanlar=ozet_alanlari(dek, satir, muhur_)
                )
        baglanti.commit()
    return yol.read_bytes()


#: Eklerin uydurma özgün adı: rapora, nota, günlüğe ve iz satırına girmemelidir.
OZGUN_AD = "Uydurgül Masalcıoğlu dilekçesi.pdf"
#: Uydurma ek içerikleri (imza baytı kabul edilen türden).
PDF = b"%PDF-1.7\nuydurma belge icerigi\n"
PNG = b"\x89PNG\r\n\x1a\nuydurma resim"


@dataclass(frozen=True)
class OrnekEk:
    """Uydurma bir ek: gerçek kabı ve sarmalı, satırının açık sütunları."""

    hazir: ds.HazirDosya = field(repr=False)
    owner_type: str = "okul.SchoolYear"
    owner_id: str = "7"
    #: Saat dilimsiz UTC metni; 21:30 UTC yerelde ertesi gündür (saat dilimi sınaması).
    uploaded_at: str = "2026-11-03 21:30:00"
    purged_at: str | None = None

    @property
    def ad(self) -> str:
        return self.hazir.stored_name

    @property
    def girdi(self) -> ManifestoGirdisi:
        return ManifestoGirdisi(self.ad, self.hazir.size, self.hazir.sha256)


def ornek_ek(acik: bytes = PDF, *, dek: bytes = TEST_DEK, **alanlar: Any) -> OrnekEk:
    return OrnekEk(ds.dosya_hazirla(acik, sarmal_anahtari=crypto.file_wrap_key(dek)), **alanlar)


def ek_tablosu_ekle(yol: Path, ekler: Iterable[OrnekEk]) -> None:
    """Var olan SQLite dosyasına `okul_attachment` tablosunu ve satırları yazar."""
    with closing(sqlite3.connect(yol)) as baglanti:
        baglanti.execute(
            "CREATE TABLE okul_attachment (stored_name varchar(32) NOT NULL PRIMARY KEY, "
            "original_name text NOT NULL, key_wrap text NOT NULL, sha256 varchar(64) NOT NULL, "
            "size integer NOT NULL, owner_type varchar(100) NOT NULL, "
            "owner_id varchar(64) NOT NULL, uploaded_at datetime NOT NULL, purged_at datetime NULL)"
        )
        baglanti.executemany(
            "INSERT INTO okul_attachment VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    ek.ad,
                    OZGUN_AD,
                    ek.hazir.key_wrap,
                    ek.hazir.sha256,
                    ek.hazir.size,
                    ek.owner_type,
                    ek.owner_id,
                    ek.uploaded_at,
                    ek.purged_at,
                )
                for ek in ekler
            ],
        )
        baglanti.commit()


def ekli_sqlite(
    yol: Path,
    ekler: Iterable[OrnekEk],
    *,
    dek: bytes = TEST_DEK,
    hesaplar: Iterable[HesapSatiri] = (),
    isaret: str = "",
) -> bytes:
    """`yetkili_sqlite` ve ek tablosu; dosyanın baytlarını döndürür."""
    yetkili_sqlite(yol, dek=dek, hesaplar=hesaplar, isaret=isaret)
    ek_tablosu_ekle(yol, ekler)
    return yol.read_bytes()


def depoya_koy(dizin: Path, *ekler: OrnekEk) -> None:
    """Eklerin kaplarını `dizin`'e yazar (depo ya da tam yedeğin kaynağı)."""
    ds.dizin_kur(dizin)
    for ek in ekler:
        ds.depoya_yaz(dizin, ek.ad, ek.hazir.kap)


def yerel_yedek_yaz(
    hedef: Path, goruntu: bytes, ekler: Iterable[OrnekEk], *, dek: bytes = TEST_DEK
) -> None:
    """Manifestosu `ekler` olan yerel yedek; kurtarma başlığı güncel güvenlik dosyasındandır."""
    manifesto = Manifesto(KAPSAM_YEREL, tuple(ek.girdi for ek in ekler))
    baslik = durum_basligi(app_password.read_state() or {})
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_bytes(kap_kur(goruntu, dek, baslik=baslik, manifesto=manifesto))


def tam_yedek_kur(
    hedef: Path,
    goruntu: bytes,
    ekler: Iterable[OrnekEk],
    kaynak_depo: Path,
    *,
    dek: bytes = TEST_DEK,
) -> Manifesto:
    """`kaynak_depo`'daki dosyalardan gerçek yazıcıyla tam yedek (`tam_yedek_yaz`)."""
    manifesto: Manifesto = tam_yedek_yaz(
        hedef,
        goruntu,
        [ek.girdi for ek in ekler],
        kaynak_depo,
        private_key_from_data_key(dek).public_key(),
        recovery_header=durum_basligi(app_password.read_state() or {}),
    )
    return manifesto


def duz_sqlite(yol: Path, isaret: str) -> bytes:
    """Yalnız `kayit` tablosu taşıyan SQLite dosyası (okul kartı ve hesap tablosu yok)."""
    yol.unlink(missing_ok=True)
    with closing(sqlite3.connect(yol)) as baglanti:
        baglanti.execute("CREATE TABLE kayit (deger TEXT)")
        baglanti.execute("INSERT INTO kayit VALUES (?)", (isaret,))
        baglanti.commit()
    return yol.read_bytes()


# ============================================================ gerçek veritabanıyla geri yükleme
# Programın (ORM'in) yazdığı test veritabanının görüntüsünü alıp geri yükleyen ve geri yüklenen
# veritabanını programa koyan yardımcılar (`test_sarmal_tazeligi.py`, `test_satir_izi.py`;
# `django_db(transaction=True)` testlerinde: görüntü commit edilmiş veriyi görmelidir).


def goruntu(yol: Path) -> bytes:
    """ORM'in yazdığı test veritabanının o anki görüntüsü (gerçek SQLite dosyası)."""
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.unlink(missing_ok=True)
    connection.ensure_connection()
    with closing(sqlite3.connect(yol)) as hedef:
        connection.connection.backup(hedef)
    return yol.read_bytes()


def sifreli_yedek(icerik: bytes) -> bytes:
    """Bu kurulumun DEK'iyle, güncel kurtarma başlığını gömen şifreli yedek."""
    return cast(
        "bytes", kap_kur(icerik, TEST_DEK, baslik=durum_basligi(app_password.read_state() or {}))
    )


def geri_yukle(
    tmp_path: Path,
    yedek: bytes,
    guncel: bytes | None,
    *,
    kapsayici: bytes | None = None,
    **sir: Any,
) -> Path:
    """`guncel` (yoksa veritabanı dosyası yok) yerine `yedek`i geri yükler; hedefin yolunu döndürür.

    `kapsayici` verilmezse yedek güncel güvenlik dosyasının kurtarma başlığıyla şifrelenir."""
    db = tmp_path / "canli" / "db.sqlite3"
    db.parent.mkdir(parents=True, exist_ok=True)
    db.unlink(missing_ok=True)
    if guncel is not None:
        db.write_bytes(guncel)
    kap = tmp_path / "gunluk-2026-11-03.odbak"
    kap.write_bytes(sifreli_yedek(yedek) if kapsayici is None else kapsayici)
    backup_restore.restore_database(kap, db, **sir)
    return db


def hesap_satiri_oku(db: Path, hesap_id: object) -> Any:
    with closing(sqlite3.connect(db)) as baglanti:
        satir = geri_yukleme_yetkisi.hesap_satiri(baglanti, str(hesap_id).replace("-", ""))
    assert satir is not None
    return satir


def programa_al(db: Path) -> None:
    """Program geri yüklenen veritabanıyla açılmış gibi: geri yüklenen dosyanın hesap satırlarını
    (bütün sütunlarıyla) ve DENETİM İZİNİ programın veritabanına koyar.

    Hesap satırı denetim izindeki son içerik MAC'li kaydını tutmalıdır (kullanıcı kararı
    03.11.2026 "Girişte reddet"): geri yüklenen satırlar ancak geri yüklenen izle (onarımın
    satırları dahil) birlikte sınanabilir. İz tablosunun tetikleyicileri bu işlemde düşürülüp
    tanımlarıyla yeniden kurulur (kök `conftest` `iz_tetikleyicili_flush` gibi). Geri yüklenen
    dosyada olmayan hesap satırlarına dokunulmaz (izleri gider: girişleri reddedilir)."""
    with closing(sqlite3.connect(db)) as baglanti:
        hesap_sutunlari = [str(s[1]) for s in baglanti.execute("PRAGMA table_info(okul_account)")]
        iz_sutunlari = [str(s[1]) for s in baglanti.execute("PRAGMA table_info(okul_audittrail)")]
        hesap_listesi = ", ".join(f'"{s}"' for s in hesap_sutunlari)
        iz_listesi = ", ".join(f'"{s}"' for s in iz_sutunlari)
        hesaplar_ = baglanti.execute(
            f"SELECT {hesap_listesi} FROM okul_account"  # noqa: S608 — test, şemanın adları
        ).fetchall()
        izler = baglanti.execute(
            f"SELECT {iz_listesi} FROM okul_audittrail ORDER BY seq"  # noqa: S608 — test
        ).fetchall()
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' "
            "AND tbl_name = 'okul_audittrail' ORDER BY name"
        )
        tetikleyiciler = [(str(ad), str(sql)) for ad, sql in cursor.fetchall()]
        for ad, _ in tetikleyiciler:
            cursor.execute(f'DROP TRIGGER "{ad}"')
        cursor.execute("DELETE FROM okul_audittrail")
        for satir in hesaplar_:
            degerler = dict(zip(hesap_sutunlari, satir, strict=True))
            kimlik = degerler.pop("id")
            atama = ", ".join(f'"{ad}" = %s' for ad in degerler)
            cursor.execute(
                f"UPDATE okul_account SET {atama} WHERE id = %s",  # noqa: S608 — test, sabit adlar
                [*degerler.values(), kimlik],
            )
        adlar = ", ".join(f'"{s}"' for s in iz_sutunlari)
        yer = ", ".join(["%s"] * len(iz_sutunlari))
        for satir in izler:
            cursor.execute(
                f"INSERT INTO okul_audittrail ({adlar}) VALUES ({yer})",  # noqa: S608 — test
                list(satir),
            )
        for _, sql in tetikleyiciler:
            cursor.execute(sql)
