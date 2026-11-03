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
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from apps.okul.services import app_password
from shared import crypto, kanonik

#: Uydurma açılış anı (UTC; mikrosaniyesiz: Django kesirsiz yazar).
ACILIS = datetime(2026, 10, 31, 7, 30, tzinfo=UTC)


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
    """Okul kartı ve mühürlü hesap satırları taşıyan SQLite dosyası kurar; baytlarını döndürür.

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
            "status varchar(24) NOT NULL, opened_at datetime NOT NULL, closed_at datetime NULL, "
            "wrap_digest varchar(64) NOT NULL, wrap_digest_pending varchar(64) NOT NULL, "
            "seal varchar(64) NOT NULL)"
        )
        sabitler = [ozetli(dek, satir) for satir in hesaplar]
        baglanti.executemany(
            "INSERT INTO okul_account VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    uuid.UUID(satir.id).hex,
                    satir.login_name,
                    satir.role,
                    satir.status,
                    _django_zamani(satir.opened_at),
                    _django_zamani(satir.closed_at),
                    satir.ozet,
                    satir.bekleyen_ozet,
                    muhur(dek, satir) if satir.muhur is None else satir.muhur,
                )
                for satir in sabitler
            ],
        )
        baglanti.commit()
    return yol.read_bytes()


def duz_sqlite(yol: Path, isaret: str) -> bytes:
    """Yalnız `kayit` tablosu taşıyan SQLite dosyası (okul kartı ve hesap tablosu yok)."""
    yol.unlink(missing_ok=True)
    with closing(sqlite3.connect(yol)) as baglanti:
        baglanti.execute("CREATE TABLE kayit (deger TEXT)")
        baglanti.execute("INSERT INTO kayit VALUES (?)", (isaret,))
        baglanti.commit()
    return yol.read_bytes()
