"""Takvim aritmetiği: ay ve yıl ekleme, başlamış ay ve yıl sayısı (plan F1c 6. adım).

Kural değerleri (süre, ay, yıl) koda yazılmaz (altın kural 2, D8); bu modül yalnız takvimi sayar, eşiği
çağıran kural paketinden okur. Ayın son günü yoksa ayın son gününe iner (31.10 + 4 ay = 28.02 ya da
29.02); 29.02 + 1 yıl 28.02 olur.
"""

from __future__ import annotations

import calendar
from datetime import date

#: Bir yıldaki ay sayısı (takvim sabiti; kural değeri değildir).
YILDAKI_AY = 12


def ay_ekle(gun: date, ay: int) -> date:
    """`gun`'e `ay` takvim ayı ekler; hedef ayda o gün yoksa ayın son günü."""
    toplam = gun.year * YILDAKI_AY + (gun.month - 1) + ay
    yil, ay_sira = divmod(toplam, YILDAKI_AY)
    son = calendar.monthrange(yil, ay_sira + 1)[1]
    return date(yil, ay_sira + 1, min(gun.day, son))


def yil_ekle(gun: date, yil: int) -> date:
    """`gun`'e `yil` takvim yılı ekler (29.02 → 28.02)."""
    return ay_ekle(gun, yil * YILDAKI_AY)


def baslamis_ay(baslangic: date, bitis: date) -> int:
    """`baslangic` ile `bitis` (ikisi de dâhil) arasında başlamış ay sayısı.

    01.11 – 28.02 dört aydır; 01.11 – 01.03 dört ay bir gündür, beşinci ay başlamıştır.
    """
    sayi = 0
    while ay_ekle(baslangic, sayi) <= bitis:
        sayi += 1
    return sayi


def baslamis_yil(baslangic: date, gun: date) -> int:
    """`baslangic`'tan `gun`'e (dâhil) başlamış yıl sayısı; yıl dönümünde yeni yıl başlamıştır."""
    sayi = 0
    while yil_ekle(baslangic, sayi) <= gun:
        sayi += 1
    return sayi
