"""Organ üyeliği testlerinin ortak kurulumu (F1c 5. adım; `yk`, `dk`, `ak` ve üyelik testleri).

OYS fabrikalarının (`OabPersonFactory`, `OrganMembershipFactory`) karşılığıdır, AYNEN alınmadı:
kişi VARSAYILAN olarak velidir (`is_parent=True`), genel kurul dışı kanaldaki ya da devralınan üyelik
seçilmiş (`SECILDI`) açılır. Programdan önceki dönemler ve seçilmeler sayaç testleri için ORM'le
doğrudan yazılır (geçmiş dönem kapanmıştır, servis yazmaz). Kişi adları UYDURMADIR.
"""

from __future__ import annotations

import itertools
from datetime import UTC, date, datetime
from typing import Any

from apps.oab.models import (
    AssemblyKind,
    ElectedBy,
    GeneralAssembly,
    MembershipSource,
    MembershipStatus,
    OabPerson,
    OabTerm,
    OrganMembership,
    PersonKind,
    SeatGroup,
    SeatType,
    TermStatus,
)
from apps.oab.services import donemler, kisiler, uyelikler
from apps.oab.services import genel_kurul as genel_kurul_servisi
from apps.okul.models import SchoolYear

#: Dönemin açıldığı gün ve organ seçilmelerinin günü.
GUN = date(2026, 10, 10)
SECIM_GUNU = date(2026, 10, 15)

_SIRA = itertools.count(1)
_AD_HARFLERI = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"


def _ad_eki() -> str:
    """Adaşlık sorusu çıkmasın diye her kişiye ayrı harf dizisi (rakamsız; sıralama testleri için)."""
    sayi, harfler = next(_SIRA), ""
    while sayi:
        sayi, kalan = divmod(sayi - 1, len(_AD_HARFLERI))
        harfler = _AD_HARFLERI[kalan] + harfler
    return harfler


def yil() -> SchoolYear:
    kayit: SchoolYear = SchoolYear.objects.create(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), is_active=True
    )
    return kayit


def donem() -> OabTerm:
    return donemler.create_term(name="2026-2027 birlik dönemi", school_year=yil(), start_date=GUN)


def kisi(**alanlar: Any) -> OabPerson:
    """Varsayılan: veli. Ad uydurmadır, her çağrıda ayrıdır."""
    varsayilan: dict[str, Any] = {
        "kind": PersonKind.VELI,
        "first_name": f"Uydurnur {_ad_eki()}",
        "last_name": "Örnekkaya",
        "ayni_kisi_degil": True,
    }
    return kisiler.create_person(**{**varsayilan, **alanlar})


def ogretmen(**alanlar: Any) -> OabPerson:
    """Varsayılan: veli olmayan öğretmen."""
    return kisi(**{"kind": PersonKind.OGRETMEN, "is_parent": False, **alanlar})


def olaganustu_genel_kurul(donem_: OabTerm) -> GeneralAssembly:
    """Aynı dönemde organ yenileyen genel kurul (md. 13/8): seçilenler kendi dönemine yazılır."""
    return genel_kurul_servisi.genel_kurul_olustur(
        donem=donem_,
        kind=AssemblyKind.OLAGANUSTU,
        first_meeting_at=datetime(2026, 10, 15, 7, 0, tzinfo=UTC),
    )


def devralinan(
    donem_: OabTerm,
    kisi_: OabPerson,
    *,
    organ: str = "YK",
    seat_type: str = SeatType.ASIL,
    seat_group: str = "",
    role: str = "UYE",
    elected_by: str = ElectedBy.GENEL_KURUL,
) -> OrganMembership:
    """Geçiş kurulumunda devralınan, programdan önce seçilmiş görevdeki üye (aday şartı yok)."""
    return uyelikler.assign_membership(
        term=donem_,
        person=kisi_,
        organ=organ,
        seat_type=seat_type,
        seat_group=seat_group,
        role=role,
        elected_by=elected_by,
        source=MembershipSource.DEVRALINAN,
        start_date=GUN,
    )


def yk_adayi(
    donem_: OabTerm,
    kisi_: OabPerson,
    kurul: GeneralAssembly,
    *,
    seat_type: str = SeatType.ASIL,
    role: str = "UYE",
) -> OrganMembership:
    return uyelikler.assign_membership(
        term=donem_,
        person=kisi_,
        organ="YK",
        seat_type=seat_type,
        role=role,
        elected_by=ElectedBy.GENEL_KURUL,
        assembly=kurul,
    )


def dk_ogretmeni(
    donem_: OabTerm,
    kisi_: OabPerson,
    *,
    seat_type: str = SeatType.ASIL,
    role: str = "UYE",
    elected_by: str = ElectedBy.OGRETMENLER_KURULU,
    **alanlar: Any,
) -> OrganMembership:
    """Öğretmenler kurulunun seçtiği öğretmen: genel kurul dışı kanal, kayıt seçilmiş açılır."""
    return uyelikler.assign_membership(
        term=donem_,
        person=kisi_,
        organ="DK",
        seat_type=seat_type,
        seat_group=SeatGroup.OGRETMEN,
        role=role,
        elected_by=elected_by,
        start_date=SECIM_GUNU,
        **alanlar,
    )


def gecmis_secilmeler(
    kisi_: OabPerson, *, organ: str = "YK", role: str = "UYE", adet: int = 1, **alanlar: Any
) -> list[OrganMembership]:
    """Programın önceki (kapanmış) dönemlerindeki seçilmeler; her biri ayrı dönemde (ORM'le)."""
    bagli = OabTerm.objects.exclude(status=TermStatus.IPTAL).first()
    assert bagli is not None, "Önce açık dönem kurulmalı (kural kopyası onunla donar)."
    okul_yili = SchoolYear.objects.order_by("pk").first()
    assert okul_yili is not None
    seat_type = alanlar.pop("seat_type", SeatType.ASIL)
    seat_group = alanlar.pop("seat_group", SeatGroup.VELI if organ == "DK" else "")
    kayitlar: list[OrganMembership] = []
    for _ in range(adet):
        sira = OabTerm.objects.count()
        gecmis = OabTerm.objects.create(
            name=f"geçmiş dönem {sira}",
            school_year=okul_yili,
            start_date=date(2015 + sira, 10, 1),
            end_date=date(2016 + sira, 9, 30),
            status=TermStatus.KAPANDI,
            rule_package=bagli.rule_package,
        )
        kayitlar.append(
            OrganMembership.objects.create(
                term=gecmis,
                person=kisi_,
                organ=organ,
                role=role,
                seat_type=seat_type,
                seat_group=seat_group,
                elected_by=ElectedBy.GENEL_KURUL,
                status=MembershipStatus.SECILDI,
                start_date=date(2015 + sira, 10, 1),
                **alanlar,
            )
        )
    return kayitlar
