"""Genel kurul yeter sayısının saf hesabı (tasarım §5.2.3, §6.4.1; §12.A S-1, S-2 düzeltmeleri).

Taban kurul bileşiminden gelir, üyelik kaydı sayılmaz: eksik kadroyla da yeter sayı aynıdır. Olağanüstü
genel kurulda da aynı hesap uygulanır (md. 9/2, 9/6). Değerler dönemin kural kopyasından, dönem
verilmezse dağıtılan en yeni revizyondan okunur. Çarpanın seçimi sert kuraldır (hesap bütünlüğü):
kullanıcı değeri değiştiremez.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from apps.oab.kurallar.erisim import DonemBagi, kural


@dataclass(frozen=True)
class YeterSayi:
    """Toplantı yeter sayısının dökümü (`GeneralAssembly.quorum_*`)."""

    taban: int
    carpan: int
    gerekli: int


def genel_kurul_yeter_sayisi(
    ogrenci_mevcudu: int, *, tarih: date, donem: DonemBagi | None = None
) -> YeterSayi:
    """Öğrenci mevcuduna göre yeter sayı: 16 × 4 (mevcut ≥ 100) ya da 16 × 2 (mevcut < 100)."""
    if ogrenci_mevcudu < 0:
        raise ValueError("Öğrenci mevcudu eksi olamaz.")
    taban = kural("genel_kurul.yeter_sayi_taban", tarih=tarih, donem=donem)
    esik = kural("genel_kurul.kucuk_okul_esik", tarih=tarih, donem=donem)
    if ogrenci_mevcudu < esik:
        carpan = kural("genel_kurul.kucuk_okul_carpan", tarih=tarih, donem=donem)
    else:
        carpan = kural("genel_kurul.yeter_sayi_carpan", tarih=tarih, donem=donem)
    return YeterSayi(taban=taban, carpan=carpan, gerekli=taban * carpan)


def genel_kurul_oylamasindaki_koltuklar(
    *, tarih: date, donem: DonemBagi | None = None
) -> dict[str, dict[str, int]]:
    """Genel kurulun seçeceği koltuklar: Yönetim Kurulu ve Denetleme Kurulunun veli koltukları.

    Denetleme Kurulunun öğretmen koltukları genel kurul oylamasına girmez, öğretmenler kurulunca
    seçilir (md. 14/1, `denetleme_kurulu.koltuklar`).
    """
    koltuklar: dict[str, Any] = kural("denetleme_kurulu.koltuklar", tarih=tarih, donem=donem)
    return {
        "YK": {
            "ASIL": kural("yonetim_kurulu.asil_uye", tarih=tarih, donem=donem),
            "YEDEK": kural("yonetim_kurulu.yedek_uye", tarih=tarih, donem=donem),
        },
        "DK_VELI": dict(koltuklar["VELI"]),
    }
