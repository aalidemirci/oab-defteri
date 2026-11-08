"""e-Okul rapor önişleyicisi — personel ihracının rapor dipnotlarını temizler.

e-Okul'un "Excel" ihraçları uygulama şablonuna BENZEMEZ: **Personel listesi (OOK01001R1)** düz
tablodur ama sonunda ``Toplam Personel Sayısı: N`` dipnotu ve tarih/saat seri numaralarından
oluşan bir satır vardır; bunlar temizlenmezse dipnot satırı personel kaydı olarak yazılır.

Bu modül SAFTIR (DB'siz, Django'suz) ve **satır sayısını korur**: gürültü
satırları silinmez, BOŞALTILIR. Böylece rapordaki "satır 47 atlandı" uyarıları
kullanıcının Excel'de gördüğü satır numarasıyla aynı kalır.

SINIF LİSTESİ BLOK DÜZLEŞTİRİCİSİ SÖKÜLDÜ (F1b 5. adım): öğrenci aktarımı T5 gereği söküldü,
veli listesi de e-Okul'dan değil okulun doldurduğu iki sütunlu şablondan gelir (kullanıcı
08.11.2026: e-Okul veli adı veren rapor sunmaz; `excel_veli`). Sınıf listesi (OOG01001R020)
düzleştiricisinin kullanıcısı kalmadı; tasarım §12.B'nin "blok düzleştirici veli listesine
kalır" satırından sapmadır (plan "F1b-5 uygulama kararları"; ek F1b-5 eklerinde).
"""

from __future__ import annotations

import re
from typing import Any

from apps.okul.normalize import _ascii_upper

#: Dipnot: 'Toplam Öğrenci Sayısı : 35', 'Toplam Personel Sayısı: 103'.
_DIPNOT_RE = re.compile(r"(OGRENCI|PERSONEL|TOPLAM)\s*\w*\s*SAYISI")
#: e-Okul rapor kodu ('OOG01001R020', 'OOK01001R1') — sayfa altı imzası.
_RAPOR_KODU_RE = re.compile(r"\bOO[A-Z]\d+R\d+\b")


def _metin(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _bos_satir(cells: list[Any]) -> bool:
    return all(_metin(c) == "" for c in cells)


def sayac_veya_kod_mu(cells: list[Any]) -> bool:
    """Satır METİNSEL bir rapor imzası mı? ('Toplam Öğrenci Sayısı', 'OOG01001R020')."""
    for cell in cells:
        ham = _metin(cell)
        if not ham:
            continue
        katli = _ascii_upper(ham)
        if _DIPNOT_RE.search(katli) or _RAPOR_KODU_RE.search(katli):
            return True
    return False


def _yalniz_sayi_satiri(cells: list[Any]) -> bool:
    """Satırın dolu hücrelerinin TAMAMI sayı mı? (e-Okul sayfa altı tarih/saat damgası)."""
    dolu = [c for c in cells if _metin(c) != ""]
    return bool(dolu) and all(_sayi_mi(c) for c in dolu)


def dipnot_mu(cells: list[Any]) -> bool:
    """Satır rapor gürültüsü mü? (sayaç dipnotu, rapor kodu, tarih/saat serisi)."""
    return sayac_veya_kod_mu(cells) or _yalniz_sayi_satiri(cells)


def _sayi_mi(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int | float):
        return True
    try:
        float(str(value).replace(",", ".").strip())
    except (TypeError, ValueError):
        return False
    return True


def temizle_rapor_dipnotlari(grid: list[list[Any]]) -> tuple[list[list[Any]], list[str]]:
    """Sayaç dipnotu / rapor kodu / tarih damgası satırlarını boşaltır.

    "Dolu hücrelerinin tamamı sayı" kuralı YALNIZ e-Okul imzası taşıyan
    matrislerde uygulanır (sayaç dipnotu ya da rapor kodu görülmüşse). Uygulama
    şablonunda ve pano yapıştırmasında böyle bir satır rapor gürültüsü değil,
    ADI EKSİK BİR VERİ SATIRIDIR: orada boşaltmak, `parse_rows`ın satır
    numarasıyla yazacağı uyarıyı yok eder ve
    kullanıcıya sebebini yanlış söylerdi.
    """
    eokul_imzasi = any(sayac_veya_kod_mu(cells) for cells in grid)
    cikti: list[list[Any]] = []
    temizlenen = 0
    for cells in grid:
        if _bos_satir(cells):
            cikti.append(list(cells))
            continue
        gurultu = sayac_veya_kod_mu(cells) or (eokul_imzasi and _yalniz_sayi_satiri(cells))
        if gurultu:
            cikti.append([])
            temizlenen += 1
        else:
            cikti.append(list(cells))
    if temizlenen == 0:
        return grid, []
    return cikti, [f"e-Okul rapor dipnotu olarak {temizlenen} satır atlandı (sayaç/tarih satırı)."]


def hazirla_personel_matrisi(grid: list[list[Any]]) -> tuple[list[list[Any]], list[str]]:
    """Personel girdisini ayrıştırıcıya hazır hâle getirir (dipnot temizliği)."""
    return temizle_rapor_dipnotlari(grid)


__all__ = [
    "dipnot_mu",
    "hazirla_personel_matrisi",
    "sayac_veya_kod_mu",
    "temizle_rapor_dipnotlari",
]
