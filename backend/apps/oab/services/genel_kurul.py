"""Genel kurulun asgari kaydı ve yeter sayının dondurulması (tasarım §5.2.3, O7; plan F1c kararları).

Uç ve ekran yoktur; rol kapısı (`Eylem.GENEL_KURUL_YAZMA`) ve durum akışı F2'dedir. Yeter sayı hesabı
`kurallar.genel_kurul`'dadır; burada anlık görüntü kaydedilir: okul kartı sonradan değişse de geçmiş
hesap değişmez, dondurulan değer elle değiştirilemez.
"""

from __future__ import annotations

from datetime import date, datetime

from django.db import transaction

from apps.oab.hatalar import YeterSayiDonduruldu
from apps.oab.kurallar import genel_kurul, yazma_kapisi
from apps.oab.models import AssemblyKind, GeneralAssembly, OabTerm
from apps.oab.services import donem_kilidi, iz
from apps.okul import denetim_izi
from apps.okul.models import SchoolConfig

OGRENCI_MEVCUDU_BOS = "Okul kartında öğrenci mevcudu girilmemiş; yeter sayı hesaplanamadı."


@transaction.atomic
def genel_kurul_olustur(
    *,
    donem: OabTerm,
    kind: AssemblyKind,
    first_meeting_at: datetime | None = None,
    opens_term: OabTerm | None = None,
) -> GeneralAssembly:
    """Genel kurul kaydı açar (`PLANLANDI`). Kural kullanan yazma akışının parçasıdır."""
    yazma_kapisi()
    donem = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(donem, hazirlik_yazimi=True)
    hesap = iz.yazar_hesabi()
    kurul = GeneralAssembly.objects.create(
        term=donem,
        opens_term=opens_term,
        kind=kind,
        first_meeting_at=first_meeting_at,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(kurul, onceki=None)
    return kurul


@transaction.atomic
def yeter_sayiyi_dondur(kurul: GeneralAssembly, *, tarih: date) -> GeneralAssembly:
    """Okul kartındaki mevcudu kurula kopyalar, yeter sayıyı hesaplar ve dondurur (O7, §7.1 ilan)."""
    yazma_kapisi()
    guncel = GeneralAssembly.objects.select_related("term__rule_package").get(pk=kurul.pk)
    donem_kilidi.yazma_denetimi(guncel.term, hazirlik_yazimi=True)
    if guncel.quorum_required is not None:
        raise YeterSayiDonduruldu
    mevcut = SchoolConfig.objects.get(pk=SchoolConfig.SINGLETON_PK).student_count
    if mevcut is None:
        raise ValueError(OGRENCI_MEVCUDU_BOS)
    hesap = genel_kurul.genel_kurul_yeter_sayisi(mevcut, tarih=tarih, donem=guncel.term)
    onceki = denetim_izi.anlik(guncel)
    guncel.student_count_snapshot = mevcut
    guncel.quorum_base = hesap.taban
    guncel.quorum_multiplier = hesap.carpan
    guncel.quorum_required = hesap.gerekli
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(
        update_fields=[
            "student_count_snapshot",
            "quorum_base",
            "quorum_multiplier",
            "quorum_required",
            "updated_at",
            "updated_by",
        ]
    )
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel
