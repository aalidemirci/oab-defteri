"""Genel kurul modelleri ve göçleri (plan F2 3. adım, §5.1; tasarım §5.2.3, §5.2.4, §5.2.7, §5.2.8).

Sabitlenenler: (1) `GeneralAssembly`'nin kısıtları — `term` yalnız `MUDUR_YENI_OKUL`'da boş (S5 (i)),
olağanüstü dönem açmaz, çağrıdan itibaren çağıran, iki toplantı tek kayıtta (U8), ibra yalnız yapılmış
genel kurulda, md. 14/5 raporu ve üye başvurusu alanları yalnız kendi çağıranında; bir hazırlık dönemini
tek genel kurul açar, bir genel kurul tek dönem açar (U3); (2) dondurulmuş yeter sayı değişmez (U7; örnek
kaydı da toplu güncelleme de); durum makinesi `save()`'dedir; (3) gündem maddesinin tekilliği ve oy
kısıtları; (4) katılım düzeltmesi ekleme-yalnızdır, dondurulmuş yeter sayıya uzanmaz; (5) asgari
`AuditReport`: md. 14/5 bağı yalnız md. 6 işaretiyle, genel kuruldaki ve rapordaki iki bağ birbirini
gösterir, çağrıya bağlı raporun işareti kaldırılmaz (U13, S6 (ii); model katmanı); yeni okulun ilk genel
kurulunda yeter sayı hazırlık döneminin kopyasından ve kilidiyle dondurulur (S5 (i), U1); (6) duyurunun
durum makinesi,
gelen-giden evrakın (defter, yıl, kayıt no) tekilliği; (7) `GeneratedDocument`'in kip ve toplantı
başına tek geçerli satırı (U34) ve `kaydet`'in süzgeci; (8) veli listesinin katılım işareti (U33);
(9) kayıt silinmez; (10) göç F1c verisini bozmaz (geriye uyum). Adlar ve sayılar UYDURMADIR.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, date, datetime
from typing import Any

import pytest
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from apps.oab.hatalar import DonemSaltOkur, DonemYazilamaz
from apps.oab.kurallar.yukleyici import icerik_ozeti
from apps.oab.models import (
    AgendaItem,
    AgendaItemKind,
    Announcement,
    AnnouncementKind,
    AnnouncementStatus,
    AssemblyCaller,
    AssemblyKind,
    AssemblyMeeting,
    AssemblyMinutes,
    AssemblyStatus,
    AttendanceCorrection,
    AuditReport,
    AuditReportKind,
    BookKind,
    DenetimRaporuKaydiGecersiz,
    DocumentDirection,
    DocumentRecord,
    DocumentStatus,
    DocumentVariant,
    DuyuruKaydiGecersiz,
    GenelKurulKaydiGecersiz,
    GeneralAssembly,
    GeneratedDocument,
    OabTerm,
    OfficialBook,
    RulePackage,
    TermStatus,
)
from apps.oab.services import donemler
from apps.oab.services import evrak as evrak_servisi
from apps.oab.services import genel_kurul as genel_kurul_servisi
from apps.okul.models import ImmutableRecord, ImportRun, ParentRoster, SchoolConfig, SchoolYear
from shared import evrak

GUN = date(2026, 10, 10)
BIRINCI_AN = datetime(2026, 10, 20, 15, 0, tzinfo=UTC)
IKINCI_AN = datetime(2026, 10, 27, 15, 0, tzinfo=UTC)
OZET = "a" * 64


def _yil() -> SchoolYear:
    yil: SchoolYear = SchoolYear.objects.create(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), is_active=True
    )
    return yil


def _donem() -> OabTerm:
    return donemler.create_term(name="2026-2027 birlik dönemi", school_year=_yil(), start_date=GUN)


def _hazirlik(donem: OabTerm) -> OabTerm:
    """Sentetik hazırlık dönemi (açan servis F2 4. adımda)."""
    hazirlik: OabTerm = OabTerm.objects.create(
        name="2027-2028 birlik dönemi",
        school_year=donem.school_year,
        rule_package=donem.rule_package,
        status=TermStatus.HAZIRLIK,
    )
    return hazirlik


def _kurul(donem: OabTerm | None = None, **alanlar: Any) -> GeneralAssembly:
    kurul: GeneralAssembly = GeneralAssembly.objects.create(
        term=donem if donem is not None else _donem(), kind=AssemblyKind.OLAGAN, **alanlar
    )
    return kurul


#: Birinci toplantıda yapılmış genel kurulun tutarlı alanları (toplu güncellemeyle kurulur).
YAPILDI_BIRINCIDE: dict[str, Any] = {
    "status": AssemblyStatus.YAPILDI,
    "called_by": AssemblyCaller.YONETIM_KURULU,
    "student_count_snapshot": 120,
    "quorum_base": 16,
    "quorum_multiplier": 4,
    "quorum_required": 64,
    "first_meeting_at": BIRINCI_AN,
    "first_attendee_count": 70,
    "held_at_meeting": AssemblyMeeting.BIRINCI,
}


def _yapildi() -> GeneralAssembly:
    kurul = _kurul()
    GeneralAssembly.objects.filter(pk=kurul.pk).update(**YAPILDI_BIRINCIDE)
    return GeneralAssembly.objects.get(pk=kurul.pk)


# ============================================================ genel kurul: kısıtlar


@pytest.mark.django_db
def test_f1c_bicimli_kayit_yeni_alanlarda_bos_ve_varsayilandir() -> None:
    """F1c'nin genel kurulu (planlandı, dönemli) yeni kısıtların hepsini tutar; alanlar boştur."""
    kurul = genel_kurul_servisi.genel_kurul_olustur(donem=_donem(), kind=AssemblyKind.OLAGAN)
    kurul.refresh_from_db()
    assert kurul.called_by == "" and kurul.held_at_meeting == ""
    assert kurul.discharge_yk == "" and kurul.discharge_dk == ""
    assert kurul.attendance_by_kind == {} and kurul.rule_warnings == []
    assert kurul.second_meeting_at is None and kurul.member_count_declared is None
    assert kurul.call_reason == "" and kurul.cancel_reason == ""


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("alanlar", "kisit"),
    [
        ({"called_by": "YOK"}, "ck_generalassembly_called_by"),
        ({"term": None}, "ck_generalassembly_donem"),
        (
            {"term": None, "called_by": AssemblyCaller.MUDUR_YENI_OKUL},
            "ck_generalassembly_donem",
        ),
        (
            {"status": AssemblyStatus.CAGRILDI},
            "ck_generalassembly_cagiran",
        ),
        (
            {
                "kind": AssemblyKind.OLAGANUSTU,
                "status": AssemblyStatus.CAGRILDI,
                "called_by": AssemblyCaller.YONETIM_KURULU,
            },
            "ck_generalassembly_olaganustu_neden",
        ),
        ({"status": AssemblyStatus.IPTAL}, "ck_generalassembly_iptal_gerekcesi"),
        (
            {"status": AssemblyStatus.ILAN_EDILDI, "called_by": AssemblyCaller.YONETIM_KURULU},
            "ck_generalassembly_yeter_sayi_ilanda",
        ),
        (
            {"first_meeting_at": IKINCI_AN, "second_meeting_at": BIRINCI_AN},
            "ck_generalassembly_ikinci_toplanti_sirasi",
        ),
        ({"second_announced_on": GUN}, "ck_generalassembly_ikinci_toplanti_alanlari"),
        ({"second_attendee_count": 12}, "ck_generalassembly_ikinci_toplanti_alanlari"),
        ({"discharge_yk": "EDILDI"}, "ck_generalassembly_ibra"),
        ({"member_application_count": 30}, "ck_generalassembly_uye_basvurusu"),
        ({"member_count_declared": 300}, "ck_generalassembly_uye_basvurusu"),
        # Kısıtın ikinci yarısı: yapılmamış genel kurulda yapıldığı toplantı boştur (birinci
        # toplantının alanları dolu, yalnız bu kısıt bozulur).
        (
            {
                "held_at_meeting": AssemblyMeeting.BIRINCI,
                "first_meeting_at": BIRINCI_AN,
                "first_attendee_count": 70,
            },
            "ck_generalassembly_yapildigi_toplanti",
        ),
    ],
)
def test_planlanmis_genel_kurulun_kisitlari(alanlar: dict[str, Any], kisit: str) -> None:
    kurul = _kurul()
    with pytest.raises(IntegrityError, match=rf"{kisit}$"), transaction.atomic():
        GeneralAssembly.objects.filter(pk=kurul.pk).update(**alanlar)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("alanlar", "kisit"),
    [
        ({"held_at_meeting": "UCUNCU"}, "ck_generalassembly_held_at_meeting"),
        ({"discharge_dk": "YOK"}, "ck_generalassembly_discharge"),
        ({"held_at_meeting": ""}, "ck_generalassembly_yapildigi_toplanti"),
        ({"first_attendee_count": None}, "ck_generalassembly_birinci_toplanti"),
        ({"held_at_meeting": AssemblyMeeting.IKINCI}, "ck_generalassembly_ikinci_toplanti"),
        (
            {
                "status": AssemblyStatus.YETER_SAYI_YOK,
                "held_at_meeting": "",
                "first_attendee_count": None,
            },
            "ck_generalassembly_yeter_sayi_yok",
        ),
    ],
)
def test_yapilmis_genel_kurulun_kisitlari(alanlar: dict[str, Any], kisit: str) -> None:
    kurul = _yapildi()
    with pytest.raises(IntegrityError, match=rf"{kisit}$"), transaction.atomic():
        GeneralAssembly.objects.filter(pk=kurul.pk).update(**alanlar)


@pytest.mark.django_db
def test_ikinci_toplantida_yapilan_genel_kurul_tek_kayittadir() -> None:
    """U8: birinci toplantıda yeter sayı yok, ikinci toplantı aynı kayıtta; ibra yazılır."""
    kurul = _yapildi()
    GeneralAssembly.objects.filter(pk=kurul.pk).update(
        first_attendee_count=40,
        second_meeting_at=IKINCI_AN,
        second_announced_on=date(2026, 10, 21),
        second_attendee_count=35,
        held_at_meeting=AssemblyMeeting.IKINCI,
        discharge_yk="EDILDI",
        discharge_dk="GORUSULMEDI",
        observer_count=6,
        parent_students_count=41,
        attendance_by_kind={"VELI_KURSIYER": 30, "OGRETMEN": 5},
    )
    kurul.refresh_from_db()
    assert kurul.held_at_meeting == AssemblyMeeting.IKINCI
    assert (kurul.first_attendee_count, kurul.quorum_required) == (40, 64)


@pytest.mark.django_db
def test_olaganustu_genel_kurul_donem_acmaz() -> None:
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGANUSTU)
    with (
        pytest.raises(IntegrityError, match=r"ck_generalassembly_olaganustu_donem_acmaz$"),
        transaction.atomic(),
    ):
        GeneralAssembly.objects.filter(pk=kurul.pk).update(opens_term=_hazirlik(donem))


@pytest.mark.django_db
def test_yeni_okulun_ilk_genel_kurulunda_donem_bos_acilacak_donem_dolu() -> None:
    """S5 (i): `term` yalnız `MUDUR_YENI_OKUL`'da boş; açılacak dönem doludur."""
    hazirlik = _hazirlik(_donem())
    kurul = GeneralAssembly.objects.create(
        term=None,
        opens_term=hazirlik,
        kind=AssemblyKind.OLAGAN,
        called_by=AssemblyCaller.MUDUR_YENI_OKUL,
    )
    assert kurul.term is None and kurul.opens_term_id == hazirlik.pk
    with pytest.raises(IntegrityError, match=r"ck_generalassembly_donem$"), transaction.atomic():
        GeneralAssembly.objects.filter(pk=kurul.pk).update(called_by=AssemblyCaller.OKUL_MUDURU)


@pytest.mark.django_db
def test_bir_hazirlik_donemini_tek_genel_kurul_acar() -> None:
    donem = _donem()
    hazirlik = _hazirlik(donem)
    _kurul(donem, opens_term=hazirlik)
    with (
        pytest.raises(IntegrityError, match=r"oab_generalassembly\.opens_term_id"),
        transaction.atomic(),
    ):
        _kurul(donem, opens_term=hazirlik)


@pytest.mark.django_db
def test_bir_genel_kurul_tek_donem_acar() -> None:
    """U3: `opened_by_assembly` tekildir."""
    donem = _donem()
    hazirlik = _hazirlik(donem)
    kurul = _kurul(donem, opens_term=hazirlik)
    OabTerm.objects.filter(pk=hazirlik.pk).update(opened_by_assembly=kurul)
    yeni_yil = SchoolYear.objects.create(
        name="2027-2028", start_date=date(2027, 9, 6), end_date=date(2028, 6, 23)
    )
    with (
        pytest.raises(IntegrityError, match=r"oab_oabterm\.opened_by_assembly_id"),
        transaction.atomic(),
    ):
        OabTerm.objects.create(
            name="Uydurma iptal dönemi",
            school_year=yeni_yil,
            rule_package=donem.rule_package,
            status=TermStatus.IPTAL,
            opened_by_assembly=kurul,
        )


@pytest.mark.django_db
def test_dk_raporu_yalniz_denetleme_kurulunun_cagrisinda() -> None:
    donem = _donem()
    rapor = AuditReport.objects.create(
        term=donem, kind=AuditReportKind.ARA, report_date=GUN, md6_violation_found=True
    )
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGANUSTU)
    with (
        pytest.raises(IntegrityError, match=r"ck_generalassembly_dk_raporu$"),
        transaction.atomic(),
    ):
        GeneralAssembly.objects.filter(pk=kurul.pk).update(call_audit_report=rapor)
    GeneralAssembly.objects.filter(pk=kurul.pk).update(
        call_audit_report=rapor, called_by=AssemblyCaller.DENETLEME_KURULU
    )


# ============================================================ genel kurul: yeter sayı ve durum


@pytest.mark.django_db
def test_dondurulmus_yeter_sayi_degistirilemez() -> None:
    """U7, O7: dondurulduktan sonra yeter sayının dört alanı ne kayıtla ne toplu güncellemeyle değişir."""
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK, defaults={"student_count": 99, "student_count_as_of": GUN}
    )
    kurul = genel_kurul_servisi.genel_kurul_olustur(donem=_donem(), kind=AssemblyKind.OLAGAN)
    kurul = genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert (kurul.quorum_base, kurul.quorum_multiplier, kurul.quorum_required) == (16, 2, 32)
    kurul.quorum_required = 64
    kurul.quorum_multiplier = 4
    with pytest.raises(ImmutableRecord):
        kurul.save()
    with pytest.raises(ImmutableRecord):
        kurul.save(update_fields=["quorum_required", "quorum_multiplier"])
    with pytest.raises(ImmutableRecord):
        GeneralAssembly.objects.filter(pk=kurul.pk).update(student_count_snapshot=150)
    # Öteki alanlar yazılır; dondurulmuş değer olduğu gibi kalır.
    GeneralAssembly.objects.filter(pk=kurul.pk).update(venue="Uydurma konferans salonu")
    guncel = GeneralAssembly.objects.get(pk=kurul.pk)
    guncel.announced_on = GUN
    guncel.save(update_fields=["announced_on"])
    guncel.refresh_from_db()
    assert (guncel.student_count_snapshot, guncel.quorum_required) == (99, 32)


KUCUK_OKUL_CARPANI = "genel_kurul.kucuk_okul_carpan"


def _okul_mevcudu(mevcut: int) -> None:
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK, defaults={"student_count": mevcut, "student_count_as_of": GUN}
    )


def _sentetik_kopyali_hazirlik(
    donem: OabTerm, *, durum: str = TermStatus.HAZIRLIK, ozet: str | None = None
) -> OabTerm:
    """Küçük okul çarpanı 3 olan sentetik kural kopyasına bağlı dönem (gerçek kopyada 2).

    Kopya kapanacak dönemin kopyasından farklıdır: yeter sayının hangi kopyadan okunduğu sonuçtan
    ayırt edilir. `ozet` verilirse kopya kanonik özetini tutmaz (D7).
    """
    gercek = donem.rule_package
    icerik = deepcopy(gercek.content)
    next(k for k in icerik["kurallar"] if k["id"] == KUCUK_OKUL_CARPANI)["deger"] = 3
    kopya = RulePackage.objects.create(
        package=gercek.package,
        rev=gercek.rev + 100,
        schema_version=gercek.schema_version,
        content=icerik,
        content_sha256=ozet if ozet is not None else icerik_ozeti(icerik),
    )
    hazirlik: OabTerm = OabTerm.objects.create(
        name="2027-2028 birlik dönemi",
        school_year=donem.school_year,
        rule_package=kopya,
        status=durum,
    )
    return hazirlik


def _yeni_okul_kurulu(hazirlik: OabTerm) -> GeneralAssembly:
    kurul: GeneralAssembly = GeneralAssembly.objects.create(
        term=None,
        opens_term=hazirlik,
        kind=AssemblyKind.OLAGAN,
        called_by=AssemblyCaller.MUDUR_YENI_OKUL,
    )
    return kurul


@pytest.mark.django_db
def test_yeni_okulun_ilk_genel_kurulunda_yeter_sayi_hazirlik_doneminin_kopyasindan() -> None:
    """S5 (i), U1: kapanacak dönem yoksa kurallar açılacak (hazırlık) dönemin kopyasından okunur."""
    _okul_mevcudu(99)
    kurul = _yeni_okul_kurulu(_sentetik_kopyali_hazirlik(_donem()))
    donmus = genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert (
        donmus.student_count_snapshot,
        donmus.quorum_base,
        donmus.quorum_multiplier,
        donmus.quorum_required,
    ) == (99, 16, 3, 48)


@pytest.mark.django_db
def test_donemli_genel_kurulda_yeter_sayi_kapanacak_donemin_kopyasindan() -> None:
    """Açılacak dönem dolu olsa da kapanacak dönem varsa kurallar onun kopyasındandır (U1)."""
    _okul_mevcudu(99)
    donem = _donem()
    kurul = _kurul(donem, opens_term=_sentetik_kopyali_hazirlik(donem))
    donmus = genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert (donmus.quorum_multiplier, donmus.quorum_required) == (2, 32)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("durum", "ozet", "hata"),
    [
        (TermStatus.IPTAL, None, DonemYazilamaz),
        (TermStatus.HAZIRLIK, "0" * 64, DonemSaltOkur),
    ],
)
def test_yeni_okulun_ilk_genel_kurulunda_hazirlik_doneminin_kilidi(
    durum: str, ozet: str | None, hata: type[Exception]
) -> None:
    """Dönem kilidi hazırlık dönemine uygulanır: iptal dönemde, bozuk kopyada dondurulmaz (O2, D7)."""
    _okul_mevcudu(99)
    kurul = _yeni_okul_kurulu(_sentetik_kopyali_hazirlik(_donem(), durum=durum, ozet=ozet))
    with pytest.raises(hata):
        genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert GeneralAssembly.objects.get(pk=kurul.pk).quorum_required is None


@pytest.mark.django_db
def test_genel_kurul_durum_makinesi() -> None:
    donem = _donem()
    with pytest.raises(GenelKurulKaydiGecersiz):
        GeneralAssembly.objects.create(
            term=donem, kind=AssemblyKind.OLAGAN, status=AssemblyStatus.YAPILDI
        )
    kurul = _kurul(donem)
    kurul.status = AssemblyStatus.YAPILDI
    with pytest.raises(GenelKurulKaydiGecersiz):
        kurul.save()
    kurul.status, kurul.called_by = AssemblyStatus.CAGRILDI, AssemblyCaller.YONETIM_KURULU
    kurul.save()
    kurul.status, kurul.cancel_reason = AssemblyStatus.IPTAL, "Uydurma iptal gerekçesi"
    kurul.save()
    kurul.status = AssemblyStatus.PLANLANDI
    with pytest.raises(GenelKurulKaydiGecersiz):
        kurul.save(update_fields=["status"])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "dagilim",
    [{"YONETICI": 3}, {"OGRETMEN": -1}, {"OGRETMEN": "3"}, {"OGRETMEN": True}, [1, 2]],
)
def test_katilim_dagilimi_tanimli_turlerin_sayilaridir(dagilim: Any) -> None:
    kurul = _kurul()
    kurul.attendance_by_kind = dagilim
    with pytest.raises(GenelKurulKaydiGecersiz):
        kurul.save()


# ============================================================ gündem ve tutanak


@pytest.mark.django_db
def test_gundem_sirasi_genel_kurulda_tekildir() -> None:
    donem = _donem()
    kurul = _kurul(donem)
    AgendaItem.objects.create(assembly=kurul, order=1, kind=AgendaItemKind.ACILIS, title="Açılış")
    with pytest.raises(IntegrityError, match=r"oab_agendaitem\.order"), transaction.atomic():
        AgendaItem.objects.create(
            assembly=kurul, order=1, kind=AgendaItemKind.KAPANIS, title="Kapanış"
        )
    AgendaItem.objects.create(
        assembly=_kurul(donem), order=1, kind=AgendaItemKind.ACILIS, title="Açılış"
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("alanlar", "kisit"),
    [
        ({"kind": "YOK"}, "ck_agendaitem_kind"),
        ({"result": "YOK"}, "ck_agendaitem_result"),
        ({"change_votes_for": 20}, "ck_agendaitem_degisiklik_oylari"),
        (
            {"removed_by_vote": True, "result": "GORUSULDU"},
            "ck_agendaitem_cikarilan_sonucsuz",
        ),
        ({"result": "KABUL", "votes_for": 40}, "ck_agendaitem_sonuc_oylari"),
        ({"present_count": 10}, "ck_agendaitem_salondaki_sayi"),
        (
            {"result": "KABUL", "votes_for": 30, "votes_against": 11, "present_count": 40},
            "ck_agendaitem_salondaki_sayi",
        ),
    ],
)
def test_gundem_maddesi_kisitlari(alanlar: dict[str, Any], kisit: str) -> None:
    madde = AgendaItem.objects.create(
        assembly=_kurul(), order=1, kind=AgendaItemKind.DIGER, title="Uydurma madde"
    )
    with pytest.raises(IntegrityError, match=rf"{kisit}$"), transaction.atomic():
        AgendaItem.objects.filter(pk=madde.pk).update(**alanlar)


@pytest.mark.django_db
def test_tutanak_genel_kurula_bire_birdir() -> None:
    kurul = _kurul()
    AssemblyMinutes.objects.create(assembly=kurul, unaudited_documents_note="Uydurma liste")
    with pytest.raises(IntegrityError, match=r"assembly_id"), transaction.atomic():
        AssemblyMinutes.objects.create(assembly=kurul)


# ============================================================ katılım düzeltmesi


def _duzeltme(kurul: GeneralAssembly, **alanlar: Any) -> AttendanceCorrection:
    varsayilan: dict[str, Any] = {
        "assembly": kurul,
        "meeting": AssemblyMeeting.BIRINCI,
        "field": "first_attendee_count",
        "old_value": 70,
        "new_value": 72,
        "justification": "Uydurma: cetvelde iki imza sonradan sayıldı.",
        "corrected_at": timezone.now(),
    }
    duzeltme: AttendanceCorrection = AttendanceCorrection.objects.create(
        **{**varsayilan, **alanlar}
    )
    return duzeltme


@pytest.mark.django_db
def test_katilim_duzeltmesi_ekleme_yalnizdir() -> None:
    duzeltme = _duzeltme(_yapildi())
    duzeltme.new_value = 75
    with pytest.raises(ImmutableRecord):
        duzeltme.save()
    with pytest.raises(ImmutableRecord):
        AttendanceCorrection.objects.filter(pk=duzeltme.pk).update(new_value=75)
    with pytest.raises(ImmutableRecord):
        duzeltme.delete()
    with pytest.raises(ImmutableRecord):
        AttendanceCorrection.objects.filter(pk=duzeltme.pk).delete()
    assert AttendanceCorrection.objects.get(pk=duzeltme.pk).new_value == 72


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("alanlar", "kisit"),
    [
        # Dondurulmuş yeter sayının alanları düzeltilemez.
        ({"field": "quorum_required"}, "ck_attendancecorrection_field"),
        ({"field": "student_count_snapshot"}, "ck_attendancecorrection_field"),
        ({"field": "attendance_by_kind.YONETICI"}, "ck_attendancecorrection_field"),
        ({"field": "observer_count", "meeting": "UCUNCU"}, "ck_attendancecorrection_meeting"),
        ({"meeting": AssemblyMeeting.IKINCI}, "ck_attendancecorrection_birinci"),
        (
            {"field": "second_attendee_count", "meeting": AssemblyMeeting.BIRINCI},
            "ck_attendancecorrection_ikinci",
        ),
        ({"new_value": 70}, "ck_attendancecorrection_degisiklik"),
        ({"justification": ""}, "ck_attendancecorrection_gerekce"),
    ],
)
def test_katilim_duzeltmesi_kisitlari(alanlar: dict[str, Any], kisit: str) -> None:
    kurul = _yapildi()
    with pytest.raises(IntegrityError, match=rf"{kisit}$"), transaction.atomic():
        _duzeltme(kurul, **alanlar)


@pytest.mark.django_db
def test_katilim_duzeltmesi_dagilimi_ve_gozlemciyi_duzeltir() -> None:
    kurul = _yapildi()
    _duzeltme(
        kurul, field="attendance_by_kind.OGRETMEN", meeting="IKINCI", old_value=None, new_value=4
    )
    _duzeltme(kurul, field="observer_count", old_value=5, new_value=6)
    assert kurul.attendance_corrections.count() == 2


# ============================================================ Denetleme Kurulu raporu (asgari)


@pytest.mark.django_db
@pytest.mark.parametrize("usulsuzluk", [False, True])
def test_dk_cagrisi_yalniz_md6_aykirilik_isaretiyle(usulsuzluk: bool) -> None:
    """U13, S6 (ii): `irregularity_found` tek başına md. 14/5 bağını açmaz."""
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGANUSTU)
    with pytest.raises(IntegrityError, match=r"ck_auditreport_md6_cagri$"), transaction.atomic():
        AuditReport.objects.create(
            term=donem,
            kind=AuditReportKind.ARA,
            report_date=GUN,
            irregularity_found=usulsuzluk,
            escalated_assembly=kurul,
        )
    rapor = AuditReport.objects.create(
        term=donem,
        kind=AuditReportKind.ARA,
        report_date=GUN,
        irregularity_found=usulsuzluk,
        md6_violation_found=True,
        escalated_assembly=kurul,
    )
    assert rapor.status == "TASLAK"


def _isaretli_rapor(donem: OabTerm) -> AuditReport:
    rapor: AuditReport = AuditReport.objects.create(
        term=donem, kind=AuditReportKind.ARA, report_date=GUN, md6_violation_found=True
    )
    return rapor


def _dk_cagrisi(donem: OabTerm, **alanlar: Any) -> GeneralAssembly:
    kurul: GeneralAssembly = GeneralAssembly.objects.create(
        term=donem,
        kind=AssemblyKind.OLAGANUSTU,
        called_by=AssemblyCaller.DENETLEME_KURULU,
        **alanlar,
    )
    return kurul


@pytest.mark.django_db
def test_dk_cagrisi_isaretsiz_rapora_baglanamaz() -> None:
    """S6 (ii): genel kuruldaki bağ da md. 6 işaretli rapor ister; usulsüzlük bayrağı yetmez (U13).

    Kısıt rapor tablosunu okuyamaz; koruma kayıtta, `update_fields`'ta ve toplu güncellemededir."""
    donem = _donem()
    isaretsiz = AuditReport.objects.create(
        term=donem, kind=AuditReportKind.ARA, report_date=GUN, irregularity_found=True
    )
    with pytest.raises(GenelKurulKaydiGecersiz, match="md. 6"):
        _dk_cagrisi(donem, call_audit_report=isaretsiz)
    kurul = _dk_cagrisi(donem)
    kurul.call_audit_report = isaretsiz
    with pytest.raises(GenelKurulKaydiGecersiz, match="md. 6"):
        kurul.save(update_fields=["call_audit_report"])
    with pytest.raises(GenelKurulKaydiGecersiz, match="md. 6"):
        GeneralAssembly.objects.filter(pk=kurul.pk).update(call_audit_report=isaretsiz)
    with pytest.raises(GenelKurulKaydiGecersiz, match="md. 6"):
        GeneralAssembly.objects.filter(pk=kurul.pk).update(call_audit_report_id=isaretsiz.pk)
    assert GeneralAssembly.objects.get(pk=kurul.pk).call_audit_report_id is None


@pytest.mark.django_db
def test_md14_5_cagrisinin_iki_bagi_birbirini_gosterir() -> None:
    """Genel kuruldaki `call_audit_report` ile rapordaki `escalated_assembly` başka kayıtları göstermez."""
    donem = _donem()
    rapor = _isaretli_rapor(donem)
    kurul = _dk_cagrisi(donem, call_audit_report=rapor)
    rapor.escalated_assembly = kurul
    rapor.save()
    # Rapor çağırdığı genel kurulu gösteriyor: ikinci bir çağrıya bağlanmaz.
    with pytest.raises(GenelKurulKaydiGecersiz, match="başka"):
        _dk_cagrisi(donem, call_audit_report=rapor)
    ikinci = _dk_cagrisi(donem)
    with pytest.raises(GenelKurulKaydiGecersiz, match="başka"):
        GeneralAssembly.objects.filter(pk=ikinci.pk).update(call_audit_report=rapor)
    # Başka raporla çağrılmış genel kurulu başka rapor göstermez.
    baska = _isaretli_rapor(donem)
    baska.escalated_assembly = kurul
    with pytest.raises(DenetimRaporuKaydiGecersiz, match="başka"):
        baska.save()
    with pytest.raises(DenetimRaporuKaydiGecersiz, match="başka"):
        AuditReport.objects.filter(pk=baska.pk).update(escalated_assembly=kurul)
    with pytest.raises(DenetimRaporuKaydiGecersiz, match="başka"):
        AuditReport.objects.create(
            term=donem,
            kind=AuditReportKind.NIHAI,
            report_date=GUN,
            md6_violation_found=True,
            escalated_assembly=kurul,
        )
    # İki bağ sırayla yazılır: önce rapordaki (genel kurulun bağı boşken), sonra genel kuruldaki.
    AuditReport.objects.filter(pk=baska.pk).update(escalated_assembly=ikinci)
    GeneralAssembly.objects.filter(pk=ikinci.pk).update(call_audit_report=baska)
    assert AuditReport.objects.get(pk=baska.pk).escalated_assembly_id == ikinci.pk
    assert GeneralAssembly.objects.get(pk=ikinci.pk).call_audit_report_id == baska.pk


@pytest.mark.django_db
def test_cagriya_bagli_raporun_md6_isareti_kaldirilamaz() -> None:
    """İşaret kaldırılsa genel kuruldaki bağ geriye dönük olarak işaretsiz rapora bağlı kalırdı."""
    donem = _donem()
    rapor = _isaretli_rapor(donem)
    _dk_cagrisi(donem, call_audit_report=rapor)
    rapor.md6_violation_found = False
    with pytest.raises(DenetimRaporuKaydiGecersiz, match="kaldırılamaz"):
        rapor.save()
    with pytest.raises(DenetimRaporuKaydiGecersiz, match="kaldırılamaz"):
        rapor.save(update_fields=["md6_violation_found"])
    with pytest.raises(DenetimRaporuKaydiGecersiz, match="kaldırılamaz"):
        AuditReport.objects.filter(pk=rapor.pk).update(md6_violation_found=False)
    assert AuditReport.objects.get(pk=rapor.pk).md6_violation_found
    # Çağrıya bağlı olmayan raporun işareti düzeltilebilir.
    bagsiz = _isaretli_rapor(donem)
    AuditReport.objects.filter(pk=bagsiz.pk).update(md6_violation_found=False)
    bagsiz.refresh_from_db()
    assert not bagsiz.md6_violation_found


# ============================================================ duyuru


@pytest.mark.django_db
def test_duyuru_durum_makinesi_ve_pano_sirasi() -> None:
    donem = _donem()
    with pytest.raises(DuyuruKaydiGecersiz):
        Announcement.objects.create(
            term=donem, kind=AnnouncementKind.GK_CAGRISI, status=AnnouncementStatus.YAYIMLANDI
        )
    duyuru = Announcement.objects.create(
        term=donem,
        kind=AnnouncementKind.GK_CAGRISI,
        subject_type="oab.GeneralAssembly",
        subject_id=str(_kurul(donem).pk),
    )
    duyuru.status = AnnouncementStatus.KALDIRILDI
    with pytest.raises(DuyuruKaydiGecersiz):
        duyuru.save()
    duyuru.status = AnnouncementStatus.YAYIMLANDI
    duyuru.posted_board_on = GUN
    duyuru.save()
    with (
        pytest.raises(IntegrityError, match=r"ck_announcement_pano_sirasi$"),
        transaction.atomic(),
    ):
        Announcement.objects.filter(pk=duyuru.pk).update(removed_board_on=date(2026, 10, 9))
    with pytest.raises(IntegrityError, match=r"ck_announcement_konu$"), transaction.atomic():
        Announcement.objects.filter(pk=duyuru.pk).update(subject_id="")


# ============================================================ gelen-giden evrak


def _evrak_defteri() -> OfficialBook:
    defter: OfficialBook = OfficialBook.objects.create(kind=BookKind.GELEN_GIDEN_EVRAK_DEFTERI)
    return defter


def _evrak_kaydi(defter: OfficialBook, donem: OabTerm, **alanlar: Any) -> DocumentRecord:
    varsayilan: dict[str, Any] = {
        "book": defter,
        "term": donem,
        "direction": DocumentDirection.GELEN,
        "year": 2026,
        "record_no": 1,
        "date": GUN,
        "counterparty": "Uydurma Okul Müdürlüğü",
        "subject": "Uydurma konu",
    }
    kayit: DocumentRecord = DocumentRecord.objects.create(**{**varsayilan, **alanlar})
    return kayit


@pytest.mark.django_db
def test_gelen_giden_evrak_defter_yil_ve_no_ile_tekildir() -> None:
    donem, defter = _donem(), _evrak_defteri()
    _evrak_kaydi(defter, donem)
    with (
        pytest.raises(IntegrityError, match=r"oab_documentrecord\.record_no"),
        transaction.atomic(),
    ):
        _evrak_kaydi(defter, donem, direction=DocumentDirection.GIDEN)
    _evrak_kaydi(defter, donem, year=2027)
    _evrak_kaydi(_evrak_defteri(), donem)


@pytest.mark.django_db
def test_gelen_evrak_uretilen_evraka_baglanmaz() -> None:
    donem, defter = _donem(), _evrak_defteri()
    belge = _kaydet(donem)
    with (
        pytest.raises(IntegrityError, match=r"ck_documentrecord_giden_evrak$"),
        transaction.atomic(),
    ):
        _evrak_kaydi(defter, donem, generated_document=belge)
    with pytest.raises(IntegrityError, match=r"ck_documentrecord_record_no$"), transaction.atomic():
        _evrak_kaydi(defter, donem, record_no=0)
    giden = _evrak_kaydi(defter, donem, direction="GIDEN", generated_document=belge)
    assert giden.generated_document_id == belge.pk


# ============================================================ üretilen evrak: kip ve toplantı (U34)


def _belge(kod: str = "E07") -> evrak.Belge:
    return evrak.Belge(
        kod=kod,
        antet=evrak.birlik_anteti(okul_adi="Örnek Ortaokulu", ilce="Örnek İlçe"),
        bloklar=(evrak.Paragraf("Uydurma genel kurul daveti."),),
    )


def _kaydet(konu: Any, **alanlar: Any) -> GeneratedDocument:
    donem = konu if isinstance(konu, OabTerm) else konu.term
    return evrak_servisi.kaydet(
        alanlar.pop("belge", _belge()), konu=konu, bicimler=("PDF",), donem=donem, **alanlar
    )


def _gecerliler(kurul: GeneralAssembly, kod: str) -> set[tuple[str, str]]:
    return set(
        GeneratedDocument.objects.filter(
            doc_type=kod, subject_id=str(kurul.pk), status=DocumentStatus.GECERLI
        ).values_list("variant", "meeting")
    )


@pytest.mark.django_db
def test_kip_ve_toplanti_basina_tek_gecerli_satir() -> None:
    """U34: kişisiz ve adlı kip, birinci ve ikinci toplantı birbirini geçersiz kılmaz; aynı kip ve
    toplantıda yeniden üretim öncekinin yerini alır. Sürüm numarası kod ve konu başınadır."""
    kurul = _kurul()
    kisisiz = _kaydet(kurul, kip=DocumentVariant.KISISIZ)
    adli = _kaydet(kurul, kip=DocumentVariant.ADLI, kisi_listesi=True, satir_sayisi=24)
    assert _gecerliler(kurul, "E07") == {("KISISIZ", ""), ("ADLI", "")}
    birinci = _kaydet(kurul, belge=_belge("E64"), toplanti=AssemblyMeeting.BIRINCI)
    ikinci = _kaydet(kurul, belge=_belge("E64"), toplanti=AssemblyMeeting.IKINCI)
    assert _gecerliler(kurul, "E64") == {("", "BIRINCI"), ("", "IKINCI")}
    yeniden = _kaydet(kurul, kip=DocumentVariant.KISISIZ)
    assert (kisisiz.version, adli.version, yeniden.version) == (1, 2, 3)
    assert (birinci.version, ikinci.version) == (1, 2)
    kisisiz.refresh_from_db()
    adli.refresh_from_db()
    assert kisisiz.status == DocumentStatus.YERINI_ALDI and adli.status == DocumentStatus.GECERLI
    assert _gecerliler(kurul, "E07") == {("KISISIZ", ""), ("ADLI", "")}


@pytest.mark.django_db
def test_ayni_kip_ve_toplantida_ikinci_gecerli_satir_kisitla_reddedilir() -> None:
    kurul = _kurul()
    ilk = _kaydet(kurul, toplanti=AssemblyMeeting.BIRINCI, belge=_belge("E05"))
    alanlar = {
        "doc_type": ilk.doc_type,
        "subject_type": ilk.subject_type,
        "subject_id": ilk.subject_id,
        "version": 2,
        "formats": ["PDF"],
        "content_sha256": OZET,
        "content_json": "{}",
        "generated_at": timezone.now(),
        "meeting": AssemblyMeeting.BIRINCI,
    }
    with pytest.raises(IntegrityError, match=r"meeting"), transaction.atomic():
        GeneratedDocument.objects.create(**alanlar)
    GeneratedDocument.objects.create(**{**alanlar, "meeting": AssemblyMeeting.IKINCI})


@pytest.mark.django_db
def test_adli_kip_veli_adi_tasir_ve_kip_kapali_listededir() -> None:
    kurul = _kurul()
    with (
        pytest.raises(IntegrityError, match=r"ck_generateddocument_adli_kip$"),
        transaction.atomic(),
    ):
        _kaydet(kurul, kip=DocumentVariant.ADLI)
    with pytest.raises(ValueError, match="kipi ya da toplantısı"):
        _kaydet(kurul, kip="YOK")
    with pytest.raises(ValueError, match="kipi ya da toplantısı"):
        _kaydet(kurul, toplanti="UCUNCU")


@pytest.mark.django_db
def test_f1c_evraki_kipsiz_ve_toplantisiz_yazilir() -> None:
    """F1c belgeleri iki alanı boş yazar; davranışları değişmez (yeniden üretim yerini alır)."""
    donem = _donem()
    ilk = _kaydet(donem, belge=_belge("E01"))
    ikinci = _kaydet(donem, belge=_belge("E01"))
    ilk.refresh_from_db()
    assert (ilk.variant, ilk.meeting, ilk.status) == ("", "", DocumentStatus.YERINI_ALDI)
    assert (ikinci.version, ikinci.status) == (2, DocumentStatus.GECERLI)


# ============================================================ veli listesinin katılım işareti (U33)


def _veli_satiri(**alanlar: Any) -> ParentRoster:
    parti = ImportRun.objects.create(source_type="VELI", file_hash=OZET)
    satir: ParentRoster = ParentRoster.objects.create(
        import_run=parti, full_name="Uydurnur Örnekkaya", student_class="9-A", **alanlar
    )
    return satir


@pytest.mark.django_db
def test_katilim_isareti_genel_kurul_ve_toplantiyla_birliktedir() -> None:
    kurul = _kurul()
    satir = _veli_satiri(attended_assembly=kurul, attended_meeting=AssemblyMeeting.IKINCI)
    assert satir.attended_assembly_id == kurul.pk
    assert _veli_satiri().attended_meeting == ""
    for alanlar in (
        {"attended_assembly": kurul},
        {"attended_meeting": AssemblyMeeting.BIRINCI},
        {"attended_assembly": kurul, "attended_meeting": "UCUNCU"},
    ):
        with (
            pytest.raises(IntegrityError, match=r"ck_parentroster_katilim_isareti$"),
            transaction.atomic(),
        ):
            _veli_satiri(**alanlar)
    # İşaret satırla düşer: satır silinir, genel kurul kalır.
    ParentRoster.objects.filter(pk=satir.pk).delete()
    assert GeneralAssembly.objects.filter(pk=kurul.pk).exists()


# ============================================================ kayıt silinmez


@pytest.mark.django_db
def test_genel_kurul_kayitlari_silinmez() -> None:
    donem = _donem()
    kurul = _kurul(donem)
    kayitlar: list[Any] = [
        kurul,
        AgendaItem.objects.create(assembly=kurul, order=1, kind="ACILIS", title="Açılış"),
        AssemblyMinutes.objects.create(assembly=kurul),
        AuditReport.objects.create(term=donem, kind="NIHAI", report_date=GUN),
        Announcement.objects.create(term=donem, kind=AnnouncementKind.GK_CAGRISI),
        _evrak_kaydi(_evrak_defteri(), donem),
    ]
    for kayit in kayitlar:
        with pytest.raises(ImmutableRecord):
            kayit.delete()
        with pytest.raises(ImmutableRecord):
            type(kayit).objects.filter(pk=kayit.pk).delete()
        assert type(kayit).objects.filter(pk=kayit.pk).exists()


# ============================================================ göç: geriye uyum


ESKI_DUGUMLER = [("oab", "0006_uretilen_evrak"), ("okul", "0004_account_bonds")]


def _goc_et(hedef: list[tuple[str, str]]) -> Any:
    yurutucu = MigrationExecutor(connection)
    yurutucu.loader.build_graph()
    yurutucu.migrate(hedef)
    return MigrationExecutor(connection).loader.project_state(hedef).apps


def _son_dugumler() -> list[tuple[str, str]]:
    dugumler: list[tuple[str, str]] = MigrationExecutor(connection).loader.graph.leaf_nodes()
    return dugumler


@pytest.mark.django_db(transaction=True)
def test_goc_f1c_verisini_bozmaz_yeni_alanlar_bos_ve_varsayilandir() -> None:
    """`oab.0007` ve `okul.0005`: F1c şemasındaki kayıtlar göçten sonra yerindedir; yeni alanlar boş
    ya da varsayılandır, yeni kısıtların hepsini tutar (göç yalnız şema değiştirir)."""
    try:
        eski = _goc_et(ESKI_DUGUMLER)
        yil = eski.get_model("okul", "SchoolYear").objects.create(
            name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25)
        )
        kopya = eski.get_model("oab", "RulePackage").objects.create(
            package="OAB-UYDURMA", rev=1, schema_version=1, content={}, content_sha256=OZET
        )
        donem = eski.get_model("oab", "OabTerm").objects.create(
            name="Uydurma dönem",
            school_year=yil,
            rule_package=kopya,
            status="ACIK",
            start_date=GUN,
        )
        kurul = eski.get_model("oab", "GeneralAssembly").objects.create(
            term=donem,
            kind="OLAGAN",
            first_meeting_at=BIRINCI_AN,
            student_count_snapshot=120,
            quorum_base=16,
            quorum_multiplier=4,
            quorum_required=64,
        )
        belge = eski.get_model("oab", "GeneratedDocument").objects.create(
            doc_type="E01",
            subject_type="oab.OabTerm",
            subject_id=str(donem.pk),
            term=donem,
            version=1,
            formats=["PDF"],
            content_sha256=OZET,
            content_json="{}",
            generated_at=timezone.now(),
        )
        parti = eski.get_model("okul", "ImportRun").objects.create(
            source_type="VELI", file_hash=OZET
        )
        veli = eski.get_model("okul", "ParentRoster").objects.create(
            import_run=parti, full_name="Uydurnur Örnekkaya", student_class="9-A", term=donem
        )

        _goc_et(_son_dugumler())

        yeni_kurul = GeneralAssembly.objects.get(pk=kurul.pk)
        assert yeni_kurul.term_id == donem.pk and yeni_kurul.quorum_required == 64
        assert (yeni_kurul.called_by, yeni_kurul.held_at_meeting, yeni_kurul.venue) == ("", "", "")
        assert yeni_kurul.attendance_by_kind == {} and yeni_kurul.rule_warnings == []
        assert yeni_kurul.status == AssemblyStatus.PLANLANDI
        yeni_belge = GeneratedDocument.objects.get(pk=belge.pk)
        assert (yeni_belge.variant, yeni_belge.meeting) == ("", "")
        assert yeni_belge.status == DocumentStatus.GECERLI
        yeni_veli = ParentRoster.objects.get(pk=veli.pk)
        assert yeni_veli.attended_assembly_id is None and yeni_veli.attended_meeting == ""
        assert yeni_veli.full_name == "Uydurnur Örnekkaya"
        with connection.cursor() as imlec:
            imlec.execute("PRAGMA foreign_key_check")
            assert imlec.fetchall() == []
    finally:
        _goc_et(_son_dugumler())
