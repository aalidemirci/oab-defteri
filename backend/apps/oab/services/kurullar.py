"""Karar defteri, kurul toplantısı, katılım ve karar taslağı (tasarım §5.2.4, §5.2.8; plan F1c-5).

Ekransız yapı taşlarıdır (plan "F1c uygulama kararları"): yönetim kurulu görev bölümü ve yedek
çağrısı (6. adım) toplantı, katılım ve karar taslağını bunlarla yazar; karar defterinin geçiş kaydı
(son sıra no ve sayfa) 8. adımın sihirbazındadır. Rol kapıları o adımların uçlarındadır.

Kural kullanmazlar (`yazma_kapisi()` çağrılmaz): toplantı ve karar yeter sayısı (`yonetim_kurulu.
toplanti_yeter_sayi`, `karar_yeter_sayi`), deftere işleme ve sakat karar F3'tedir. Dönemli kayıt
dönem kilidinden geçer (O2); her yazım veriyle aynı işlemde iz satırı yazar.

Tek istisna karar defterinin noter tasdikidir (`tasdik_denetimi`, `yonetim_kurulu.karar_defteri_noter_
tasdiki`, md. 23/2; plan F1c 8. adım notları): kayıt yazmaz, defterin uyum satırını `uyum.denetle` ile
yazar (o da `yazma_kapisi()`'ndan geçer). Konu defterdir, gerekçe defter başına birdir (O3): geçiş
kurulumu (8. adım) ve F3'ün "deftere işlendi" işareti aynı kimlik ve kök nedenle denetler.

F1c'de yalnız karar defteri açılır ve yalnız iki karar türü yazılır: görev bölümü ve yedek çağırma.
Yedek çağırma kararı yalnız yönetim kurulu toplantısına yazılır: Denetleme Kurulunun yedeği karar
olmadan, program yöneticisinin üyelik kaydıyla çağrılır (md. 14/6; tasarım E65). Katılım yalnız
görevdeki asıla yazılır (seçilmiş asıl ya da yedekten çağrılan; `selectors.gorevdeki_asil_mi`):
çağrılmamış yedek kurulun üyesi değildir, katılımı yeter sayıyı ve devamsızlık zincirini bozar
(md. 12/1, 12/3, 13/6).
Kararın varsayılanı `TASLAK`'tır: program karar defterinin yerine geçmez, karar defterine el ile
yazılır (md. 13/5).

TOPLANTININ YAPILDI GEÇİŞİ (tasarım §7.2 "`PLANLANDI → YAPILDI`"): görevdeki her asıl üyenin katılım
satırı girilmeden geçiş yoktur (sert; devamsızlık sayımı). Toplantı yeter sayısı (`yonetim_kurulu.
toplanti_yeter_sayi`) F3'tedir. F1c'de bu geçişi yalnız görev bölümü kaydı yapar (6. adım).

KARARIN DURUM SERVİSİ (6. adım): durum makinesi modeldedir (`BoardDecision.save`). F1c'de yalnız
taslağın iptali yazılır (`TASLAK → IPTAL`); kabul ve ret toplantı ve karar yeter sayısıyla (md. 13/3),
"deftere işlendi" işareti (`Eylem.ISARET_KARAR_DEFTERE_ISLENDI`) ve sakat karar F3'tedir.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Final

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.oab import selectors
from apps.oab.kurallar import VERI_YOK
from apps.oab.models import (
    BoardDecision,
    BoardMeeting,
    BoardMeetingAttendance,
    BookCertifier,
    BookKind,
    DecisionKind,
    DecisionStatus,
    KararDurumuGecersiz,
    MeetingKind,
    MeetingStatus,
    MembershipStatus,
    OabTerm,
    OfficialBook,
    OrganMembership,
    OrganType,
)
from apps.oab.models.kurul import KURUL_ORGANLARI
from apps.oab.services import donem_kilidi, iz, uyum
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
TOPLANTI_PLANLANMIS_DEGIL = "Yalnız planlanmış toplantı yapıldı olarak kaydedilir."
KATILIM_EKSIK = (
    "Görevdeki her asıl üyenin katılım satırı (katıldı, özürlü ya da özürsüz) girilmeden toplantı "
    "yapıldı olarak kaydedilmez."
)
KARAR_GECISI_F3 = (
    "Kararın kabulü, reddi ve deftere işlenmesi karar defteri ekranıyla yapılır; bu sürümde yalnız "
    "taslak iptal edilir."
)

#: F1c'de durum servisinin yazdığı geçişler (modül başlığı "Kararın durum servisi").
F1C_KARAR_GECISLERI: Final = frozenset({DecisionStatus.IPTAL})


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


#: Karar defterinin noter tasdiki (md. 23/2; modül başlığı). Düz atama: D6'nın statik taraması
#: `uyum.denetle(TASDIK_KURALI, …)` çağrısının kimliğini bu satırdan okur.
TASDIK_KURALI = "yonetim_kurulu.karar_defteri_noter_tasdiki"


def tasdik_kok_nedeni(defter: OfficialBook) -> str:
    """Karar defterinin tasdik sapmasının kök nedeni: defter başına bir gerekçe (§5 O3)."""
    return f"karar_defteri:{defter.pk}"


def tasdik_gozlenen(defter: OfficialBook) -> Any:
    """Kuralın gözlenen değeri: tasdik eden makam. Makam ya da tasdik günü girilmemişse `VERI_YOK`;
    kural `eksik_veri: sapma`dır, eksik tasdik bilgisi de uyarı + gerekçedir."""
    if not defter.certified_by or defter.certified_on is None:
        return VERI_YOK
    return defter.certified_by


def tasdik_denetimi(
    defter: OfficialBook, *, donem: OabTerm, gerekce: str = "", tarih: date | None = None
) -> uyum.UyumSonucu:
    """Karar defterinin noter tasdiki (md. 23/2): noter tasdiki ve günü girilmişse uygun (açık satır
    kapanır); tasdik bilgisi eksikse ya da il/ilçe millî eğitim müdürlüğü tasdiki girilmişse uyarı +
    gerekçe. Konu defterdir; gerekçe defterin kök nedenine bağlanır, aynı defterde yeniden sorulmaz.
    `tarih` olay günüdür (defterin kullanıldığı gün; verilmezse bugün)."""
    return uyum.denetle(
        TASDIK_KURALI,
        tasdik_gozlenen(defter),
        donem=donem,
        konu=defter,
        tarih=tarih if tarih is not None else timezone.localdate(),
        gerekce=uyum.Gerekce(metin=gerekce, kok_neden=tasdik_kok_nedeni(defter)),
    )


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


@transaction.atomic
def toplanti_yapildi(toplanti: BoardMeeting, *, held_at: datetime) -> BoardMeeting:
    """`PLANLANDI → YAPILDI` (`DURUM`): görevdeki her asılın katılım satırı olmalıdır (sert)."""
    guncel = _yazilabilir_toplanti(toplanti)
    if guncel.status != MeetingStatus.PLANLANDI:
        raise ValueError(TOPLANTI_PLANLANMIS_DEGIL)
    gorevdekiler = {u.pk for u in selectors.gorevdeki_asillar(guncel.term, guncel.organ)}
    yazilan = set(guncel.attendances.values_list("membership_id", flat=True))
    if not gorevdekiler <= yazilan:
        raise ValueError(KATILIM_EKSIK)
    onceki = denetim_izi.anlik(guncel)
    guncel.held_at = held_at
    guncel.status = MeetingStatus.YAPILDI
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=["held_at", "status", "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel


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


@transaction.atomic
def karar_durumu_yaz(karar: BoardDecision, hedef: str) -> BoardDecision:
    """Kararın durum geçişi (`DURUM`; modül başlığı "Kararın durum servisi").

    Geçiş modelin durum makinesine uymalıdır (`KararDurumuGecersiz`); F1c'de yalnız taslağın iptali
    yazılır, öteki geçişler F3'ün karar defteri akışındadır.
    """
    guncel = BoardDecision.objects.select_related("meeting__term__rule_package").get(pk=karar.pk)
    if hedef not in F1C_KARAR_GECISLERI:
        raise KararDurumuGecersiz(KARAR_GECISI_F3)
    donem_kilidi.yazma_denetimi(guncel.meeting.term)
    if guncel.status == hedef:
        return guncel
    onceki = denetim_izi.anlik(guncel)
    guncel.status = hedef
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=["status", "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel
