"""Birlik döneminin açılışı (tasarım §5.2.1, §7.9 adım 1; `create_term` UYARLA, tasarım §12.A).

F1c'de gerçek yol yalnız ilk dönemin doğrudan `ACIK` açılmasıdır: `opened_by_assembly` boştur, dönem
programla gelen en yeni revizyona bağlanır (§6.2-4). Sonraki dönemler genel kurulla açılır (F2).

Veli listesi (plan F1c-4): açık dönem yokken aktarılan dönemsiz satırlar ilk dönem açılırken o döneme
bağlanır; iz, satır başına değil, kişisiz tek olay satırıdır (veli listesi satır başına iz yazmaz,
`okul.ParentRoster`). Açık dönemin kimliğini veli listesi aktarımına `acik_donem_kimligi` bildirir
(`AppConfig.ready`; `okul` `oab`'yi içe aktarmaz).
"""

from __future__ import annotations

from datetime import date

from django.db import transaction

from apps.oab.kurallar import yazma_kapisi
from apps.oab.models import OabTerm, TermStatus
from apps.oab.services import iz, kural_bagi
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AuditAction, ParentRoster, SchoolYear

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
    _veli_listesini_bagla(donem)
    return donem


def acik_donem_kimligi() -> int | None:
    """Açık (`ACIK`) birlik döneminin kimliği; yoksa None (veli listesi aktarımının dönemi)."""
    kimlik: int | None = (
        OabTerm.objects.filter(status=TermStatus.ACIK).values_list("pk", flat=True).first()
    )
    return kimlik


def _veli_listesini_bagla(donem: OabTerm) -> int:
    """Dönemsiz veli satırlarını döneme bağlar; satır varsa kişisiz `DURUM` olayı yazar.

    Olay yalnız alanın adını (`term`) ve dönemi taşır; satırın kimliği, adı, sınıfı ve sayısı yoktur
    (veli listesinin hiçbir alanı satıra girmez, tasarım §4.6.2).
    """
    adet = ParentRoster.objects.filter(term__isnull=True).update(term=donem)
    if adet:
        denetim_izi.olay(
            AuditAction.DURUM,
            model=denetim_izi.model_etiketi(ParentRoster),
            object_id="",
            changed_fields=["term"],
            term=donem.pk,
        )
    return adet
