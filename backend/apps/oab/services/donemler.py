"""Birlik döneminin açılışı (tasarım §5.2.1, §7.9 adım 1; OYS `create_term` UYARLA).

F1c'de gerçek yol yalnız ilk dönemin doğrudan `ACIK` açılmasıdır: `opened_by_assembly` boştur, dönem
programla gelen en yeni revizyona bağlanır (§6.2-4). Sonraki dönemler genel kurulla açılır (F2).
"""

from __future__ import annotations

from datetime import date

from django.db import transaction

from apps.oab.kurallar import yazma_kapisi
from apps.oab.models import OabTerm, TermStatus
from apps.oab.services import iz, kural_bagi
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import SchoolYear

ILK_DONEM_ZATEN_ACIK = "Birlik dönemi zaten açılmış; sonraki dönemler genel kurulla açılır."
PROGRAM_BASLANGICI_ONCE = "Programa başlama günü dönem başından önce olamaz."


@transaction.atomic
def create_term(
    *,
    name: str,
    school_year: SchoolYear,
    start_date: date,
    program_start_date: date | None = None,
) -> OabTerm:
    """İlk birlik dönemini `ACIK` açar. Kural kullanan yazma: paket yoksa kapalı (D1)."""
    yazma_kapisi()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.BIRLIK_DONEMI_YAZMA)
    if program_start_date is not None and program_start_date < start_date:
        raise ValueError(PROGRAM_BASLANGICI_ONCE)
    if OabTerm.objects.exclude(status=TermStatus.IPTAL).exists():
        raise ValueError(ILK_DONEM_ZATEN_ACIK)
    hesap = iz.yazar_hesabi()
    donem = OabTerm.objects.create(
        name=name,
        school_year=school_year,
        start_date=start_date,
        program_start_date=program_start_date,
        rule_package=kural_bagi.en_yeni_kopya(),
        status=TermStatus.ACIK,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(donem, onceki=None)
    return donem
