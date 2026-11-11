"""E01, E02 ve E03 testlerinin uydurma kurulumu (`ev::` F1c kümesi; plan F1c 10. adım).

Bir karma okul (ortaokul + ortaöğretim), kantini kiraya verilmiş ve kampüste: yönetim kurulu 5 asıl
+ 5 yedek (geçişte devralınan, programdan önceki seçilme beyanlı), görev bölümü dört görevle (yer ve
katılımla), Denetleme Kurulu 3 asıl + 3 yedek ve görev bölümü (denetim planı iki tarih), temsilciler
(kademe, kantin ve kampüs satırları; başkanın kendiliğinden üye olduğu üç komisyon görev bölümüyle
açılır; sosyal etkinlikler temsilcisi kabul edilmiş kararla). `uzun=True` gerçek uzunlukta uydurma
veridir (sayfa bütçesi): uzun ad ve soyadlar, okul adı ve ilçe alanlarının üst sınırında.

Kişi adları, okul adı ve müdür adı UYDURMADIR (sözlük §2.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from apps.oab.models import (
    BoardDecision,
    DecisionKind,
    DecisionStatus,
    MeetingKind,
    MembershipRole,
    OabPerson,
    OabTerm,
    OrganMembership,
    Representation,
    SeatGroup,
    SeatType,
)
from apps.oab.services import gorev_bolumu, kurullar, temsilciler, uyelikler
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import AccountRole, CanteenMode, SchoolConfig, SchoolLevel
from apps.okul.tests.okul_karti_ortak import okul_kartini_dogrudan_yaz

#: Görev bölümlerinin ve beyanların günleri (seçilme 15.10.2026; süre içinde).
DK_GOREV_BOLUMU_GUNU = date(2026, 10, 16)
YK_GOREV_BOLUMU_GUNU = date(2026, 10, 17)
BEYAN_GUNU = date(2026, 10, 16)
TEMSILCI_GUNU = date(2026, 10, 20)
KARAR_GUNU = date(2026, 10, 20)
DENETIM_PLANI = [date(2027, 1, 15), date(2027, 4, 15)]
TOPLANTI_YERI = "Okul toplantı salonu"
TOPLANTI_GUNU_KURALI = "Her ayın ilk salı günü saat 15.00"
OKUL_ADI = "Örnek Ortaokulu"
ILCE = "Örnek İlçe"
MUDUR = "Gülten Uydurmaca"

#: Gerçek uzunlukta uydurma ad ve soyad parçaları (sayfa bütçesi).
_UZUN_ADLAR = (
    "Ayşegül Nurhayat",
    "Mehmet Emin Selahattin",
    "Fatma Zehra Gülizar",
    "Abdurrahman Kemalettin",
    "Hatice Kübra Şükriye",
    "Mustafa Kemal İsmail",
    "Zeynep Betül Nazlıgül",
    "Hüseyin Hüsnü Necmettin",
)
_UZUN_SOYADLAR = (
    "Örnekoğlu Uydurmakaya",
    "Deneyengil Sınamacıoğlu",
    "Kurgulayan Yapaydınoğlu",
    "Varsayımcıgil Örnekçioğlu",
)
_HARFLER = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"


def _alan_ust_siniri(ornek: str, alan: str) -> str:
    """Okul kartı alanının üst sınırında, sözcüklü uydurma metin."""
    sinir = getattr(SchoolConfig._meta.get_field(alan), "max_length", None)
    assert isinstance(sinir, int)
    return ((ornek + " ") * (sinir // len(ornek) + 1))[:sinir].rstrip().ljust(sinir, "a")


@dataclass
class Kurulum:
    """Kurulan dönem ve kayıtlar."""

    donem: OabTerm
    yk_asillar: list[OrganMembership]
    yk_yedekler: list[OrganMembership]
    dk_asillar: list[OrganMembership]
    dk_yedekler: list[OrganMembership]
    temsilciler: dict[str, list[OrganMembership]]
    sosyal_karari: BoardDecision


class _Adlar:
    """Her çağrıda ayrı uydurma ad (adaşlık sorusu çıkmaz)."""

    def __init__(self, uzun: bool) -> None:
        self.uzun = uzun
        self.sira = 0

    def __call__(self) -> dict[str, str]:
        sira, self.sira = self.sira, self.sira + 1
        ek = _HARFLER[sira % len(_HARFLER)] + _HARFLER[sira // len(_HARFLER)]
        if self.uzun:
            return {
                "first_name": f"{_UZUN_ADLAR[sira % len(_UZUN_ADLAR)]} {ek}",
                "last_name": _UZUN_SOYADLAR[sira % len(_UZUN_SOYADLAR)],
            }
        return {"first_name": f"Uydurnur {ek}", "last_name": "Örnekkaya"}


def okul_karti(*, uzun: bool = False, **alanlar: Any) -> None:
    """Karma okul, kantin kiraya verilmiş, kampüste; müdürün adı okul kartında."""
    varsayilan: dict[str, Any] = {
        "school_name": (
            _alan_ust_siniri(
                "Örnek Şehit Öğretmen Ayşe Örnekoğlu Mesleki ve Teknik Anadolu Lisesi",
                "school_name",
            )
            if uzun
            else OKUL_ADI
        ),
        "district": _alan_ust_siniri("Örnekşehirköyübeldesi", "district") if uzun else ILCE,
        "principal_name": MUDUR,
        "levels": [SchoolLevel.ORTAOKUL.value, SchoolLevel.ORTAOGRETIM.value],
        "canteen_mode": CanteenMode.KIRAYA_VERILIYOR.value,
        "in_campus": True,
    }
    okul_kartini_dogrudan_yaz(**{**varsayilan, **alanlar})


def _kisi(adlar: _Adlar, **alanlar: Any) -> OabPerson:
    return o.kisi(**{**adlar(), **alanlar})


def _beyan(uyelik: OrganMembership) -> OrganMembership:
    return uyelikler.update_membership(
        uyelik, eligibility_declared_on=BEYAN_GUNU, single_birlik_declared_on=BEYAN_GUNU
    )


def tam_kurulum(*, uzun: bool = False, okul: bool = True) -> Kurulum:
    """Modül başlığındaki uydurma birlik (servislerle yazılır; toplantı günü kuralı ORM'le)."""
    if okul:
        okul_karti(uzun=uzun)
    adlar = _Adlar(uzun)
    donem = o.donem()
    OabTerm.objects.filter(pk=donem.pk).update(yk_meeting_day_rule=TOPLANTI_GUNU_KURALI)
    donem.refresh_from_db()

    yk_asillar = [_beyan(o.secilmis(donem, _kisi(adlar, external_yk_terms=1))) for _ in range(5)]
    yk_yedekler = [
        o.secilmis(
            donem, _kisi(adlar, external_yk_terms=0), seat_type=SeatType.YEDEK, seat_order=sira
        )
        for sira in range(1, 6)
    ]
    dk_asillar = [
        o.secilmis(
            donem, _kisi(adlar, external_dk_chair_terms=1), organ="DK", seat_group=SeatGroup.VELI
        ),
        *(
            o.secilmis(
                donem,
                o.ogretmen(**adlar()),
                organ="DK",
                seat_group=SeatGroup.OGRETMEN,
            )
            for _ in range(2)
        ),
    ]
    dk_yedekler = [
        o.secilmis(
            donem,
            _kisi(adlar),
            organ="DK",
            seat_group=SeatGroup.VELI,
            seat_type=SeatType.YEDEK,
            seat_order=1,
        ),
        *(
            o.secilmis(
                donem,
                o.ogretmen(**adlar()),
                organ="DK",
                seat_group=SeatGroup.OGRETMEN,
                seat_type=SeatType.YEDEK,
                seat_order=sira,
            )
            for sira in (1, 2)
        ),
    ]
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        gorev_bolumu.dk_gorev_bolumu(
            term=donem,
            held_at=o.saat(DK_GOREV_BOLUMU_GUNU),
            baskan=dk_asillar[0],
            katilim=[gorev_bolumu.KatilimSatiri(uyelik=u, present=True) for u in dk_asillar],
            denetim_plani=DENETIM_PLANI,
            place=TOPLANTI_YERI,
        )
    gorev_bolumu.yk_gorev_bolumu(
        term=donem,
        held_at=o.saat(YK_GOREV_BOLUMU_GUNU),
        gorevler={
            MembershipRole.BASKAN: yk_asillar[0],
            MembershipRole.BASKAN_YARDIMCISI: yk_asillar[1],
            MembershipRole.MUHASIP: yk_asillar[2],
            MembershipRole.SEKRETER: yk_asillar[3],
        },
        katilim=[gorev_bolumu.KatilimSatiri(uyelik=u, present=True) for u in yk_asillar[:4]]
        + [gorev_bolumu.KatilimSatiri(uyelik=yk_asillar[4], present=False, excused=True)],
        place=TOPLANTI_YERI,
    )
    # Temsilci kararı: kabul edilmiş yönetim kurulu kararı. F1c'de yazılan karar türleri görev bölümü
    # ve yedek çağırmadır, kabul F3'ün akışındadır: `tm::test_temsilci_kaydi_ve_karar_bagi` gibi ORM'le.
    toplanti = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.GOREV_BOLUMU)
    sosyal_karari = kurullar.karar_taslagi_olustur(toplanti, kind=DecisionKind.GOREV_BOLUMU)
    BoardDecision.objects.filter(pk=sosyal_karari.pk).update(
        status=DecisionStatus.KABUL_EDILDI, decision_date=KARAR_GUNU
    )
    sosyal_karari.refresh_from_db()

    def ekle(temsil: str, kisi: OabPerson, **alanlar: Any) -> OrganMembership:
        return temsilciler.temsilci_ekle(
            term=donem, person=kisi, representation=temsil, start_date=TEMSILCI_GUNU, **alanlar
        )

    yeni = {
        Representation.ODUL_DISIPLIN_KURULU: [
            ekle(Representation.ODUL_DISIPLIN_KURULU, _kisi(adlar)),
            ekle(Representation.ODUL_DISIPLIN_KURULU, _kisi(adlar), seat_type=SeatType.YEDEK),
        ],
        Representation.DAVRANIS_DEGERLENDIRME_KURULU: [
            ekle(Representation.DAVRANIS_DEGERLENDIRME_KURULU, _kisi(adlar))
        ],
        Representation.SOSYAL_ETKINLIKLER_KURULU: [
            ekle(
                Representation.SOSYAL_ETKINLIKLER_KURULU,
                _kisi(adlar),
                representative_decision=sosyal_karari,
            )
        ],
        Representation.KONTENJAN_KOMISYONU: [
            ekle(Representation.KONTENJAN_KOMISYONU, _kisi(adlar))
        ],
        Representation.RPD_YURUTME_KOMISYONU: [
            ekle(Representation.RPD_YURUTME_KOMISYONU, _kisi(adlar))
        ],
        Representation.KANTIN_DENETIM_KOMISYONU: [
            ekle(Representation.KANTIN_DENETIM_KOMISYONU, yk_asillar[4].person)
        ],
        Representation.KAMPUS_YONETIMI: [
            ekle(Representation.KAMPUS_YONETIMI, yk_asillar[0].person)
        ],
    }
    return Kurulum(
        donem=OabTerm.objects.get(pk=donem.pk),
        yk_asillar=[uyelikler.guncel_kayit(u) for u in yk_asillar],
        yk_yedekler=yk_yedekler,
        dk_asillar=[uyelikler.guncel_kayit(u) for u in dk_asillar],
        dk_yedekler=dk_yedekler,
        temsilciler={str(k): v for k, v in yeni.items()},
        sosyal_karari=sosyal_karari,
    )
