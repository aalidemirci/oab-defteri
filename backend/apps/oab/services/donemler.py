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
from apps.oab.services import donem_kilidi, iz, kural_bagi
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AuditAction, AuditLabel, ParentRoster, SchoolYear

ILK_DONEM_ZATEN_ACIK = "Birlik dönemi zaten açılmış; sonraki dönemler genel kurulla açılır."
PROGRAM_BASLANGICI_ONCE = "Programa başlama günü dönem başından önce olamaz."
#: Yönetim kurulu toplantı günü kuralının üst sınırı (`OabTerm.yk_meeting_day_rule`).
TOPLANTI_GUNU_UST = 64


@transaction.atomic
def create_term(
    *,
    name: str,
    school_year: SchoolYear,
    start_date: date,
    program_start_date: date | None = None,
) -> OabTerm:
    """İlk birlik dönemini `ACIK` açar. Kural kullanan yazma: paket yoksa kapalı (D1).

    Geçiş kurulumunun 1. adımıdır (§7.9): satırları `GECIS` etiketlidir (tasarım §4.6.2). Varsayılanlar
    (ders yılı, ad, programa başlama günü) `gecis.ilk_donemi_ac`'tadır.
    """
    yazma_kapisi()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.BIRLIK_DONEMI_YAZMA)
    if program_start_date is not None and program_start_date < start_date:
        raise ValueError(PROGRAM_BASLANGICI_ONCE)
    if OabTerm.objects.exclude(status=TermStatus.IPTAL).exists():
        raise ValueError(ILK_DONEM_ZATEN_ACIK)
    hesap = iz.yazar_hesabi()
    with denetim_izi.etiketle(AuditLabel.GECIS):
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


@transaction.atomic
def toplanti_gunu_yaz(donem: OabTerm, metin: str) -> OabTerm:
    """Yönetim kurulunun aylık toplantı günü kuralı (dönem ayarı; `GUNCELLE`; tasarım §5.2.1 `OabTerm`
    "YK aylık toplantı günü kuralı, ör. 'her ayın ilk salısı'"; plan F1c 10. adım notları: E01'in D
    bölümünün ilk satırı, "Aylık toplantı günü (md. 13/3)").

    Serbest metindir, program bir kural koymaz ve denetlemez: md. 13/3 yalnız "ayda bir toplanır" der,
    günü kurul belirler (doğrulanamayan hüküm koda girmez, altın kural 1). Boş metin kuralı siler (E01'de
    "………"). Dönem kilidi denetlenir (kapanmış, iptal ya da kural kopyası doğrulanamayan dönem yazılmaz).
    Aynı değer yazılırsa satır yazılmaz. Rolü uç kuralı daraltır (E01'i üretenler: program yöneticisi ve
    sekreter, `rol_izinleri`).
    """
    deger = " ".join(metin.split())
    if len(deger) > TOPLANTI_GUNU_UST:
        raise ValueError(f"Toplantı günü en çok {TOPLANTI_GUNU_UST} karakter olabilir.")
    guncel = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(guncel)
    if guncel.yk_meeting_day_rule == deger:
        return guncel
    onceki = denetim_izi.anlik(guncel)
    guncel.yk_meeting_day_rule = deger
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=["yk_meeting_day_rule", "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel


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


def veli_listesini_coz(donem: OabTerm) -> int:
    """İptal edilen dönemin veli satırlarını dönemsiz bırakır (sonraki ilk dönem açılışı onları bağlar);
    satır varsa kişisiz `DURUM` olayı yazar (`_veli_listesini_bagla`'nın tersi, aynı biçim)."""
    adet = ParentRoster.objects.filter(term=donem).update(term=None)
    if adet:
        denetim_izi.olay(
            AuditAction.DURUM,
            model=denetim_izi.model_etiketi(ParentRoster),
            object_id="",
            changed_fields=["term"],
            term=donem.pk,
        )
    return adet
