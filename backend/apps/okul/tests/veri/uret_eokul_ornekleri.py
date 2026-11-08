"""Sentetik e-Okul .xls ve veli listesi .xlsx örneklerini üretir (testlerin ikili fixture'ları).

KVKK: Bu betik gerçek bir e-Okul dosyasını OKUMAZ, maskelemez, dönüştürmez —
yerleşimi sıfırdan kurar ve tüm adlar UYDURMADIR. Depoya giren ikililer yalnız bunlardır;
gerçek ihraçlar ve listeler `.gitignore` ile engellenir (`*.xls`, `*.XLS`, `*.xlsx`, `*.csv`).

Yerleşim gerçek rapor incelenerek çıkarıldı:

* ``OOK01001R1`` (Personel Listesi) — düz tablo + ``Toplam Personel Sayısı``
  dipnotu + tarih/saat seri numaralarından oluşan sayfa altı satırı.

* Veli listesi (``veli_listesi_ornegi.xlsx``; T5, F1b 5. adım): e-Okul veli adı veren rapor
  sunmaz, liste okulun doldurduğu şablondan gelir. Örnek şablonun iki sütununu ve ARADA okunmaması
  gereken sütunları (öğrencinin adı, okul no, veli telefonu — hepsi uydurma) taşır: ayrıştırıcının
  beyaz listesi (tasarım §8.1 A3) gerçek bir dosya biçiminde sınanır. Yazım çeşitleri ("9/A",
  "10. Sınıf / B Şubesi", "Hazırlık/A") ve bir sorunlu satır (sınıfı boş) bilerek vardır.

Öğrenci sınıf listesi örneği (``OOG01001R020``) T5 gereği F1a-2'de söküldü; blok düzleştiricisi de
F1b 5. adımda söküldü (tasarım §12.B'den sapma: veli listesi e-Okul'dan gelmez).

Yeniden üretmek için (xlwt yalnız personel örneği için gerekir, projenin bağımlılığı DEĞİLDİR;
veli örneği projenin openpyxl'iyle üretilir — `veli` argümanı yalnız onu üretir):

    docker compose run --rm backend sh -c \\
        "pip install -q xlwt==1.3.0 && python apps/okul/tests/veri/uret_eokul_ornekleri.py"
    docker compose run --rm backend python apps/okul/tests/veri/uret_eokul_ornekleri.py veli
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook

BURASI = Path(__file__).resolve().parent

#: Veli listesi örneği: (öğrencinin adı, okul no, VELİNİN ADI SOYADI, veli telefonu, ÖĞRENCİNİN
#: SINIFI). Yalnız büyük harfle yazılan iki sütun okunur; hepsi uydurmadır.
VELI = [
    ("ÇAĞAN ÖRNEKSOY", 4711, "SEVİM ÖRNEKSOY", "0000 000 00 01", "9-A"),
    ("İPEK UYDURMA", 4712, "HAKAN UYDURMA", "0000 000 00 02", "9/A"),
    ("NAZ UYDURMA", 4713, "HAKAN UYDURMA", "0000 000 00 02", "10. Sınıf / B Şubesi"),
    ("ARDA DENEMECİ", 4714, "IŞIL DENEMECİ", "0000 000 00 03", "Hazırlık/A"),
    ("ECE SORUNLU", 4715, "MERT SORUNLU", "0000 000 00 04", ""),
]
#: Belge özelliklerindeki oluşturma ve değiştirme anı sabittir (openpyxl yoksa üretim anını yazar).
_SABIT_AN = datetime(2026, 11, 8, 12, 0, 0)

PERSONEL = [
    ("SELMA YURTSEVEN", "Müdür", "KADROLU", "Tarih"),
    ("KEREM DALGIÇ", "Müdür Yardımcısı", "KADROLU", "Matematik"),
    ("NURAY IŞIKÇI", "Öğretmen", "KADROLU", "Fizik"),
    ("İLKAY ÖZGÜNEŞ", "Sözleşmeli Öğretmen(657 S.K. 4/B)", "SÖZLEŞMELİ", "İngilizce"),
]


def _yaz(sh: Any, satir: int, hucreler: dict[int, object]) -> None:
    for sutun, deger in hucreler.items():
        sh.write(satir, sutun, deger)


def personel_listesi(hedef: Path) -> None:
    """OOK01001R1 yerleşimini kurar (düz tablo + sayaç dipnotu + tarih satırı)."""
    try:
        import xlwt
    except ImportError:  # pragma: no cover — yalnız fixture üretiminde çalışır
        sys.exit("Personel örneği xlwt gerektirir: pip install xlwt==1.3.0")
    wb = xlwt.Workbook(encoding="utf-8")
    sh = wb.add_sheet("Sheet1")
    _yaz(sh, 0, {0: "ADI SOYADI", 6: "GÖREVİ", 8: "KADRO DURUMU", 10: "BRANŞI"})
    for i, (ad_soyad, gorev, kadro, brans) in enumerate(PERSONEL, start=1):
        _yaz(sh, i, {0: ad_soyad, 6: gorev, 8: kadro, 10: brans})
    _yaz(sh, len(PERSONEL) + 1, {0: f"Toplam Personel Sayısı: {len(PERSONEL)}"})
    _yaz(sh, len(PERSONEL) + 2, {12: 46260.0, 14: 0.898055555553583})
    wb.save(str(hedef))


def veli_listesi(hedef: Path) -> None:
    """Okulun doldurduğu veli listesi: şablonun iki sütunu + okunmayan uydurma sütunlar."""
    kitap = Workbook()
    sayfa = kitap.active
    assert sayfa is not None
    sayfa.title = "Veli Listesi"
    sayfa.append(["Örnek Ortaokulu Veli Listesi"])
    sayfa.append([])
    sayfa.append(
        [
            "Öğrencinin Adı Soyadı",
            "Okul No",
            "Velinin Adı Soyadı",
            "Veli Telefonu",
            "Öğrencinin Sınıfı",
        ]
    )
    for satir in VELI:
        sayfa.append(list(satir))
    kitap.properties.created = _SABIT_AN
    kitap.properties.modified = _SABIT_AN
    kitap.save(str(hedef))


if __name__ == "__main__":
    veli_listesi(BURASI / "veli_listesi_ornegi.xlsx")
    if sys.argv[1:] != ["veli"]:
        personel_listesi(BURASI / "eokul_personel_listesi.xls")
    print("Sentetik örnekler üretildi:", BURASI)
