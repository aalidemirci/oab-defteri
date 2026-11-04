"""Ders yılı yaşam döngüsü — oluşturma + tek-aktif kuralı (F1-T6).

Tek-aktif kuralı iki katmanlıdır: burada "önce eskisini kapat" sırası, DB'de
`uq_schoolyear_single_active` koşullu kısıtı (yarış/hata sigortası).

DENETİM İZİ (tasarım §4.6.2; plan F1b-1 alt commit c): her yazım aynı işlemde iz satırı
yazar (`denetim_izi.degisiklik`). Oluşturma `OLUSTUR`, aktifleştirme her iki yılda da
`DURUM` (`is_active`): öteki aktif yılları kapatan toplu güncelleme kayıt başına satır
yazar (önceki hâller güncellemeden önce alınır).
"""

from __future__ import annotations

from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.okul import denetim_izi
from apps.okul.models import SchoolYear


@transaction.atomic
def create_school_year(
    *, name: str, start_date: date, end_date: date, activate: bool = False
) -> SchoolYear:
    """Yeni ders yılı açar; `activate=True` ise tek-aktif kuralıyla aktifleştirir."""
    year: SchoolYear = SchoolYear.objects.create(
        name=name.strip(), start_date=start_date, end_date=end_date
    )
    denetim_izi.degisiklik(year, onceki=None)
    if activate:
        activate_school_year(year)
    return year


@transaction.atomic
def activate_school_year(year: SchoolYear) -> SchoolYear:
    """Verilen yılı aktifleştirir; diğer aktif yıllar ÖNCE kapatılır (kısıt sırası)."""
    digerleri = list(SchoolYear.objects.filter(is_active=True).exclude(pk=year.pk))
    if digerleri:
        oncekiler = {diger.pk: denetim_izi.anlik(diger) for diger in digerleri}
        SchoolYear.objects.filter(pk__in=list(oncekiler)).update(
            is_active=False, updated_at=timezone.now()
        )
        for diger in digerleri:
            denetim_izi.degisiklik(diger, onceki=oncekiler[diger.pk])
    if not year.is_active:
        onceki = denetim_izi.anlik(year)
        year.is_active = True
        year.save(update_fields=["is_active", "updated_at"])
        denetim_izi.degisiklik(year, onceki=onceki)
    return year
