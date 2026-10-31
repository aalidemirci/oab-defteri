"""SQLite bağlantı ayarlarının koruma testi (tasarım §4.3 tehdit 18).

`synchronous=FULL` bilinçli bir karardır: WAL + NORMAL kipi elektrik
kesintisinde son işlemleri geri alabilir; bu, girilmiş bir gelir-gider kaydının
ya da karar taslağının sessizce kaybolması demektir. Ayar sessizce NORMAL'e
dönerse bu test kırılır.
"""

from __future__ import annotations

import pytest
from django.db import connection

# SQLite `PRAGMA synchronous` değerleri: 0=OFF, 1=NORMAL, 2=FULL, 3=EXTRA.
_FULL = 2


@pytest.mark.django_db
def test_synchronous_full() -> None:
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA synchronous")
        (deger,) = cursor.fetchone()
    assert deger == _FULL


@pytest.mark.django_db
def test_secure_delete_acik() -> None:
    """Tasarım §5.3 (`secure_delete=ON`): silinen/güncellenen içerik serbest sayfada okunur kalmaz."""
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA secure_delete")
        (deger,) = cursor.fetchone()
    assert deger == 1


@pytest.mark.django_db
def test_yabanci_anahtarlar_acik() -> None:
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys")
        (deger,) = cursor.fetchone()
    assert deger == 1
