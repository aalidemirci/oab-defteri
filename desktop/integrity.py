"""Açılışta SQLite bütünlük denetimi (tasarım §4.2).

Bozuk bir veritabanıyla pencere AÇILMAZ: kullanıcı bozuk veri üzerinde çalışıp
kaydettikçe hasar büyür ve elindeki sağlam yedekler rotasyonla eskir. Bunun
yerine program durur ve "son yedekten dön" yolunu gösterir.

`PRAGMA integrity_check(1)` kullanılır: tam denetimin hızlı biçimi (ilk hatada
durur). Açılışa saniyeler eklememesi için tam tarama yerine bu seçildi; okulun
tek bilgisayarında birliğin veritabanı küçüktür (yılda ~400-500 banka hareketi,
organ üyeleri, personel ve veli listesi; tasarım §2.2 TK2).
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from desktop.backup import DEFAULT_KEEP_DAYS
from desktop.errors import DatabaseCorruptError

logger = logging.getLogger("oab_defteri.integrity")

_MESSAGE = "Veri dosyası bozuk görünüyor; program veriyi korumak için açılmadı."


def _geri_yukleme_yolu(platform: str) -> str:
    """Geri yüklemenin başlatıldığı yer: Başlat menüsü kısayolu yalnız Windows'ta vardır (sözlük §1
    "Yedek"; 07.11.2026 sınama listesi, kod okuması)."""
    if platform.startswith("win"):
        return (
            "Son sağlam yedeği geri yüklemek için Başlat menüsündeki "
            "'OAB Defteri — Yedekten Geri Yükle' kısayolunu çalıştırın "
            "(veya komut satırından: oab-defteri --geri-yukle)."
        )
    return (
        "Son sağlam yedeği geri yüklemek için uçbirimde oab-defteri --geri-yukle komutunu "
        "çalıştırın."
    )


def _hint(backup_dir: Path | None, platform: str) -> str:
    """Yol daima geri yükleme kipine çıkar: `--geri-yukle` şifreli yedeği açar
    (program yöneticisi hesabının tanıtıcısı ve parolası ya da kurtarma anahtarı sorulur; düz
    yedek dalı yok);
    elle kopyalama tarifi kaldırıldı — şifreli `.odbak` için çalışmaz."""
    yol = (
        f"{_geri_yukleme_yolu(platform)} Yedek listeden "
        "seçilir; program yöneticisi hesabının tanıtıcısı ve parolası ya da kurtarma anahtarı "
        "sorulur. Bozuk dosya 'db-onceki-*' adıyla veri klasöründe "
        f"{DEFAULT_KEEP_DAYS} gün saklanır, sonra silinir."
    )
    if backup_dir is None:
        return yol
    return f"Yedek klasörü: {backup_dir}\n{yol}"


def _bozuk(backup_dir: Path | None, platform: str) -> DatabaseCorruptError:
    """Kullanıcı yedek klasörünü görür; günlüğe yol yazılmaz (Windows yolu hesap adını taşır)."""
    return DatabaseCorruptError(
        _MESSAGE, hint=_hint(backup_dir, platform), gunluk_ipucu=_hint(None, platform)
    )


def check_database_integrity(
    db_path: Path, *, backup_dir: Path | None = None, platform: str | None = None
) -> None:
    """Veritabanını hızlı bütünlük denetiminden geçirir; bozuksa hata yükseltir.

    Dosya henüz yoksa sessizce döner — ilk açılışta `migrate` onu oluşturacaktır.
    """
    if not db_path.exists():
        return
    sistem = sys.platform if platform is None else platform
    try:
        with closing(sqlite3.connect(db_path)) as connection:
            rows = connection.execute("PRAGMA integrity_check(1)").fetchall()
    except sqlite3.DatabaseError as exc:
        # "file is not a database" / "database disk image is malformed" — dosya okunamıyor.
        logger.error("Bütünlük denetimi açılamadı: %s", exc.__class__.__name__)
        raise _bozuk(backup_dir, sistem) from exc

    result = str(rows[0][0]) if rows else ""
    if result != "ok":
        logger.error("Bütünlük denetimi başarısız.")
        raise _bozuk(backup_dir, sistem)
