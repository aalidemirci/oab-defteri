"""Karar defteri, kurul toplantısı, katılım ve karar taslağı (tasarım §5.2.4, §5.2.8; plan F1c-5).

Ekransız yapı taşlarıdır (plan "F1c uygulama kararları"): yönetim kurulu görev bölümü ve yedek
çağrısı (6. adım) toplantı, katılım ve karar taslağını bunlarla yazar; karar defterinin geçiş kaydı
(son sıra no ve sayfa) 8. adımın sihirbazındadır. Rol kapıları o adımların uçlarındadır.

Kural kullanmazlar (`yazma_kapisi()` çağrılmaz): toplantı ve karar yeter sayısı (`yonetim_kurulu.
toplanti_yeter_sayi`, `karar_yeter_sayi`), deftere işleme ve sakat karar F3'tedir. Dönemli kayıt
dönem kilidinden geçer (O2); her yazım veriyle aynı işlemde iz satırı yazar.

F1c'de yalnız karar defteri açılır ve yalnız iki karar türü yazılır: görev bölümü ve yedek çağırma.
Yedek çağırma kararı yalnız yönetim kurulu toplantısına yazılır: Denetleme Kurulunun yedeği karar
olmadan, program yöneticisinin üyelik kaydıyla çağrılır (md. 14/6; tasarım E65). Katılım yalnız
görevdeki asıla yazılır (seçilmiş asıl ya da yedekten çağrılan; `selectors.gorevdeki_asil_mi`):
çağrılmamış yedek kurulun üyesi değildir, katılımı yeter sayıyı ve devamsızlık zincirini bozar
(md. 12/1, 12/3, 13/6).
Kararın varsayılanı `TASLAK`'tır: program karar defterinin yerine geçmez, karar defterine el ile
yazılır (md. 13/5).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Final

from django.db import transaction
from django.db.models import Max

from apps.oab import selectors
from apps.oab.models import (
    BoardDecision,
    BoardMeeting,
    BoardMeetingAttendance,
    BookCertifier,
    BookKind,
    DecisionKind,
    MeetingKind,
    MeetingStatus,
    MembershipStatus,
    OabTerm,
    OfficialBook,
    OrganMembership,
    OrganType,
)
from apps.oab.models.kurul import KURUL_ORGANLARI
from apps.oab.services import donem_kilidi, iz
from apps.okul import denetim_izi

#: F1c'de yazılan karar türleri (plan F1c kararları); öteki türler kendi fazlarının akışıyla gelir.
F1C_KARAR_TURLERI: Final = frozenset({DecisionKind.GOREV_BOLUMU, DecisionKind.YEDEK_CAGIRMA})

TOPLANTI_ORGANI_GECERSIZ = "Toplantı yalnız yönetim kurulu ve Denetleme Kurulu için kaydedilir."
TOPLANTI_TURU_GECERSIZ = "Toplantı türü geçersiz."
TOPLANTI_IPTAL = "İptal edilmiş toplantıya kayıt yazılmaz."
KATILIM_UYELIGI_TUTMUYOR = "Katılım yalnız toplantının dönemindeki aynı kurulun üyeliğine yazılır."
KATILIM_SECILMEMIS = "Katılım yalnız seçilmiş üyeye yazılır."
KATILIM_GOREVDEKI_ASIL_DEGIL = (
    "Katılım yalnız görevdeki asıl üyeye yazılır; çağrılmamış yedeğe yazılmaz."
)
OZURLU_KATILIM = "Katılan üye özürlü sayılmaz."
KARAR_TURU_GECERSIZ = "Bu karar türü bu sürümde yazılmaz."
YEDEK_CAGIRMA_YALNIZ_YK = "Yedek çağırma kararı yalnız yönetim kurulu toplantısına yazılır."
TASDIK_MAKAMI_GECERSIZ = "Tasdik eden makam geçersiz."


@transaction.atomic
def karar_defteri_olustur(
    *,
    certified_by: str = "",
    certified_on: date | None = None,
    certification_no: str = "",
    page_count: int | None = None,
    last_no_before_program: int | None = None,
    last_page_before_program: int | None = None,
    opened_on: date | None = None,
) -> OfficialBook:
    """Karar defteri kaydı (`OLUSTUR`). Dönemsizdir; tasdik bilgisi boş bırakılabilir (§7.9 adım 4)."""
    if certified_by and certified_by not in BookCertifier.values:
        raise ValueError(TASDIK_MAKAMI_GECERSIZ)
    hesap = iz.yazar_hesabi()
    defter = OfficialBook.objects.create(
        kind=BookKind.KARAR_DEFTERI,
        certified_by=certified_by,
        certified_on=certified_on,
        certification_no=certification_no,
        page_count=page_count,
        last_no_before_program=last_no_before_program,
        last_page_before_program=last_page_before_program,
        opened_on=opened_on,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(defter, onceki=None)
    return defter


@transaction.atomic
def toplanti_olustur(
    *,
    donem: OabTerm,
    organ: str,
    kind: str,
    scheduled_at: datetime | None = None,
    place: str = "",
    agenda: str = "",
) -> BoardMeeting:
    """Kurul toplantısı kaydı (`PLANLANDI`); toplantı no'su dönem ve organ içinde sıradır."""
    if organ not in KURUL_ORGANLARI:
        raise ValueError(TOPLANTI_ORGANI_GECERSIZ)
    if kind not in MeetingKind.values:
        raise ValueError(TOPLANTI_TURU_GECERSIZ)
    guncel = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(guncel)
    son = BoardMeeting.objects.filter(term=guncel, organ=organ).aggregate(son=Max("meeting_no"))
    hesap = iz.yazar_hesabi()
    toplanti = BoardMeeting.objects.create(
        term=guncel,
        organ=organ,
        meeting_no=(son["son"] or 0) + 1,
        kind=kind,
        scheduled_at=scheduled_at,
        place=place,
        agenda=agenda,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(toplanti, onceki=None)
    return toplanti


def _yazilabilir_toplanti(toplanti: BoardMeeting) -> BoardMeeting:
    guncel = BoardMeeting.objects.select_related("term__rule_package").get(pk=toplanti.pk)
    donem_kilidi.yazma_denetimi(guncel.term)
    if guncel.status == MeetingStatus.IPTAL:
        raise ValueError(TOPLANTI_IPTAL)
    return guncel


@transaction.atomic
def katilim_yaz(
    toplanti: BoardMeeting, uyelik: OrganMembership, *, present: bool, excused: bool = False
) -> BoardMeetingAttendance:
    """Katılımı yazar ya da günceller (toplantı ve üyelik başına tek satır). Özrün nedeni tutulmaz."""
    guncel = _yazilabilir_toplanti(toplanti)
    uye = OrganMembership.objects.get(pk=uyelik.pk)
    if (uye.term_id, uye.organ) != (guncel.term_id, guncel.organ):
        raise ValueError(KATILIM_UYELIGI_TUTMUYOR)
    if uye.status != MembershipStatus.SECILDI:
        raise ValueError(KATILIM_SECILMEMIS)
    if not selectors.gorevdeki_asil_mi(uye):
        raise ValueError(KATILIM_GOREVDEKI_ASIL_DEGIL)
    if present and excused:
        raise ValueError(OZURLU_KATILIM)
    hesap = iz.yazar_hesabi()
    satir = BoardMeetingAttendance.objects.filter(meeting=guncel, membership=uye).first()
    if satir is None:
        satir = BoardMeetingAttendance.objects.create(
            meeting=guncel,
            membership=uye,
            present=present,
            excused=excused,
            created_by_id=hesap,
            updated_by_id=hesap,
        )
        denetim_izi.degisiklik(satir, onceki=None)
        return satir
    if (satir.present, satir.excused) == (present, excused):
        return satir
    onceki = denetim_izi.anlik(satir)
    satir.present, satir.excused = present, excused
    satir.updated_by_id = hesap
    satir.save(update_fields=["present", "excused", "updated_at", "updated_by"])
    denetim_izi.degisiklik(satir, onceki=onceki)
    return satir


@transaction.atomic
def karar_taslagi_olustur(
    toplanti: BoardMeeting,
    *,
    kind: str,
    text: str = "",
    decision_date: date | None = None,
) -> BoardDecision:
    """Karar taslağı (`TASLAK`, `OLUSTUR`); F1c'de yalnız görev bölümü ve yedek çağırma."""
    if kind not in F1C_KARAR_TURLERI:
        raise ValueError(KARAR_TURU_GECERSIZ)
    guncel = _yazilabilir_toplanti(toplanti)
    if kind == DecisionKind.YEDEK_CAGIRMA and guncel.organ != OrganType.YONETIM_KURULU:
        raise ValueError(YEDEK_CAGIRMA_YALNIZ_YK)
    hesap = iz.yazar_hesabi()
    karar = BoardDecision.objects.create(
        meeting=guncel,
        kind=kind,
        text=text,
        decision_date=decision_date,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(karar, onceki=None)
    return karar
