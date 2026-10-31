"""Sentetik e-Okul .xls örneklerini üretir (testlerin ikili fixture'ları).

KVKK: Bu betik gerçek bir e-Okul dosyasını OKUMAZ, maskelemez, dönüştürmez —
yerleşimi sıfırdan kurar ve tüm adlar UYDURMADIR. Depoya giren tek ikili budur;
gerçek ihraçlar `.gitignore` ile engellenir (`*.xls`, `*.XLS`).

Yerleşim gerçek rapor incelenerek çıkarıldı:

* ``OOK01001R1`` (Personel Listesi) — düz tablo + ``Toplam Personel Sayısı``
  dipnotu + tarih/saat seri numaralarından oluşan sayfa altı satırı.

Öğrenci sınıf listesi örneği (``OOG01001R020``) T5 gereği F1a-2'de söküldü
(öğrenci listesi alınmaz); blok yerleşimi `test_eokul.py`'de bellekte kurulur.
F1b'nin sentetik veli örneği bu betiğe eklenir (tasarım §12.B).

Yeniden üretmek için (xlwt yalnız burada gerekir, projenin bağımlılığı DEĞİLDİR):

    docker compose run --rm backend sh -c \\
        "pip install -q xlwt==1.3.0 && python apps/okul/tests/veri/uret_eokul_ornekleri.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import xlwt
except ImportError:  # pragma: no cover — yalnız fixture üretiminde çalışır
    sys.exit("Bu betik xlwt gerektirir: pip install xlwt==1.3.0")

BURASI = Path(__file__).resolve().parent

PERSONEL = [
    ("SELMA YURTSEVEN", "Müdür", "KADROLU", "Tarih"),
    ("KEREM DALGIÇ", "Müdür Yardımcısı", "KADROLU", "Matematik"),
    ("NURAY IŞIKÇI", "Öğretmen", "KADROLU", "Fizik"),
    ("İLKAY ÖZGÜNEŞ", "Sözleşmeli Öğretmen(657 S.K. 4/B)", "SÖZLEŞMELİ", "İngilizce"),
]


def _yaz(sh: xlwt.Worksheet, satir: int, hucreler: dict[int, object]) -> None:
    for sutun, deger in hucreler.items():
        sh.write(satir, sutun, deger)


def personel_listesi(hedef: Path) -> None:
    """OOK01001R1 yerleşimini kurar (düz tablo + sayaç dipnotu + tarih satırı)."""
    wb = xlwt.Workbook(encoding="utf-8")
    sh = wb.add_sheet("Sheet1")
    _yaz(sh, 0, {0: "ADI SOYADI", 6: "GÖREVİ", 8: "KADRO DURUMU", 10: "BRANŞI"})
    for i, (ad_soyad, gorev, kadro, brans) in enumerate(PERSONEL, start=1):
        _yaz(sh, i, {0: ad_soyad, 6: gorev, 8: kadro, 10: brans})
    _yaz(sh, len(PERSONEL) + 1, {0: f"Toplam Personel Sayısı: {len(PERSONEL)}"})
    _yaz(sh, len(PERSONEL) + 2, {12: 46260.0, 14: 0.898055555553583})
    wb.save(str(hedef))


if __name__ == "__main__":
    personel_listesi(BURASI / "eokul_personel_listesi.xls")
    print("Sentetik e-Okul örnekleri üretildi:", BURASI)
