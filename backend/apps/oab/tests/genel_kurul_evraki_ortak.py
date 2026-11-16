"""Genel kurul evrakı testlerinin ortak kurulumu.

8. adım (plan F2 §8: "hattın sınanması için en az bir deneme kurucusu"): hat (kayıt, dosya, kip,
toplantı, veli adlı çıktı, basım) deneme kurucularıyla sınanır; kurucular yalnız testte `KURUCULAR` ve
`ADLI_KURUCULAR` sözlüklerine konur (`kuruculari_kur`).

9. adım (E05, E06, E07, E08, E64'ün gerçek kurucuları): çağıranın kolu başına çağrılmış genel kurul
(`kurulum`; görev bölümlü yönetim kurulu ve Denetleme Kurulu, okul kartı, veli listesi), ilan ve
toplantılar. Adlar UYDURMADIR; veli adları aranacak belirgin dizgilerdir.
"""

from __future__ import annotations

from datetime import date

import pytest
from django.db import models

from apps.oab.models import (
    AssemblyCaller,
    AssemblyKind,
    GeneralAssembly,
    MembershipRole,
    OabTerm,
    SeatGroup,
)
from apps.oab.services import denetim
from apps.oab.services import genel_kurul as gk
from apps.oab.services import genel_kurul_evraki as gke
from apps.oab.tests import genel_kurul_ortak as gko
from apps.oab.tests import uyelik_ortak as o
from apps.oab.tests.kurallar import gorev_evraki_ortak as ge_ortak
from apps.okul.models import AccountRole, Personnel, SchoolConfig
from shared import evrak

#: Uydurma veli adları (dosyada bulunur; kayıtta, izde, günlükte bulunmaz).
VELILER = (("Pelinsu UYDURMAKAYA", "5-A"), ("Şahinbey DENEMEOĞLU", "5-B"))
#: Deneme kişisiz belgesinin cümlesi.
DENEME_CUMLESI = "Deneme kurucusu: evrak hattı sınanıyor."


def _antet() -> evrak.Antet:
    okul = SchoolConfig.load()
    return evrak.birlik_anteti(okul_adi=okul.school_name, ilce=okul.district)


def kisisiz_kurucu(kod: str) -> gke.Kurucu:
    """Kişisiz deneme kurucusu: başlık, toplantı ve kip satırı, deneme cümlesi."""

    def kur(konu: models.Model, secim: gke.Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
        bloklar: list[evrak.Blok] = [
            evrak.Baslik(gke.BELGE_ADLARI[kod]),
            evrak.Paragraf(DENEME_CUMLESI),
        ]
        if secim.toplanti:
            bloklar.append(evrak.Paragraf(f"Toplantı: {secim.toplanti}"))
        if secim.kip:
            bloklar.append(evrak.Paragraf(f"Kip: {secim.kip}"))
        return evrak.Belge(kod=kod, antet=_antet(), bloklar=tuple(bloklar)), ("Deneme uyarısı.",)

    return kur


def adli_kurucu(kod: str) -> gke.AdliKurucu:
    """Veli adlı deneme kurucusu: sınıf başına sayfa, veli adı ve sınıf; satır sayısı veli sayısı."""

    def kur(kurul: GeneralAssembly, toplanti: str) -> gke.AdliIcerik:
        bloklar: list[evrak.Blok] = [evrak.Baslik(gke.BELGE_ADLARI[kod])]
        for sira, (veli, sinif) in enumerate(VELILER):
            if sira:
                bloklar.append(evrak.SayfaSonu())
            bloklar.append(evrak.AltBaslik(f"Sınıf: {sinif}"))
            bloklar.append(
                evrak.Tablo(
                    basliklar=("Sıra", "Velinin adı ve soyadı", "Öğrencinin sınıfı", "İmza"),
                    satirlar=(("1", veli, sinif, ""),),
                )
            )
        bloklar.append(evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU))
        return gke.AdliIcerik(
            belge=evrak.Belge(kod=kod, antet=_antet(), bloklar=tuple(bloklar)),
            satir_sayisi=len(VELILER),
        )

    return kur


def kuruculari_kur(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deneme kurucularını bütün kodlara koyar (yalnız testin süresince)."""
    for kod in gke.KODLAR:
        monkeypatch.setitem(gke.KURUCULAR, kod, kisisiz_kurucu(kod))
    for kod in gke.ADLI_KODLAR:
        monkeypatch.setitem(gke.ADLI_KURUCULAR, kod, adli_kurucu(kod))


# ---------------------------------------------------------------------------
# 9. adım: gerçek kurucuların uydurma kurulumu (E05, E06, E07, E08, E64)
# ---------------------------------------------------------------------------
#: Okul kartının veri sorumlusu ve toplantının yeri (uydurma).
VERI_SORUMLUSU = "Örnek Ortaokulu Müdürlüğü, Örnek Mah. Örnek Sok. No: 1, Örnek İlçe"
YER = "Okulun çok amaçlı salonu"
#: Okul kartındaki müdür adının imza bloğundaki biçimi (`ge_ortak.MUDUR`; RYUE md. 17/2).
MUDUR_IMZASI = "Gülten UYDURMACA"
#: Uydurma personel (öğretmen ve idareci; adlı katılım cetvelinde).
PERSONEL = (("Sınamanur", "Kurgucu", "OGRETMEN"), ("Denemeli", "Yapaycı", "YONETICI"))


def okul_ve_mevcut(ogrenci: int | None = 120, *, uzun: bool = False) -> None:
    """Okul kartı (müdür adı, veri sorumlusu) ve öğrenci mevcudu (yeter sayının girdisi)."""
    ge_ortak.okul_karti(uzun=uzun, data_controller_text=VERI_SORUMLUSU)
    gko.mevcut(ogrenci)


def personel_ekle() -> None:
    """Uydurma öğretmen ve idareci (ORM; testin kurgusu)."""
    for ad, soyad, tur in PERSONEL:
        Personnel.objects.create(first_name=ad, last_name=soyad, member_kind=tur)


#: Görev bölümlerinin günleri ve gerekçesi: kapanacak dönem geçişle açıldı (dönemin başı genel kurulun
#: günü sayılır), görev bölümü bir haftadan sonra kayda geçer (uyarı + gerekçe; testin kurgusu).
DK_GOREV_BOLUMU_GUNU = date(2026, 10, 16)
YK_GOREV_BOLUMU_GUNU = date(2026, 10, 17)
GOREV_BOLUMU_GEREKCESI = "Uydurma gerekçe: görev bölümü geçiş kurulumundan sonra kayda geçti."


def kurullar(donem: OabTerm, *, uzun: bool = False) -> None:
    """Görevdeki yönetim kurulu (beş asıl; başkan ve sekreter görevli) ve Denetleme Kurulu (bir veli,
    iki öğretmen; başkan veli)."""
    adlar = ge_ortak._Adlar(uzun)
    yk = [o.secilmis(donem, o.kisi(**adlar())) for _ in range(5)]
    dk = [
        o.secilmis(donem, o.kisi(**adlar()), organ="DK", seat_group=SeatGroup.VELI),
        *(
            o.secilmis(donem, o.ogretmen(**adlar()), organ="DK", seat_group=SeatGroup.OGRETMEN)
            for _ in range(2)
        ),
    ]
    o.dk_gorev_bolumu(donem, dk[0], gun=DK_GOREV_BOLUMU_GUNU, gerekce=GOREV_BOLUMU_GEREKCESI)
    o.yk_gorev_bolumu(
        donem,
        {MembershipRole.BASKAN: yk[0], MembershipRole.SEKRETER: yk[1]},
        gun=YK_GOREV_BOLUMU_GUNU,
        gerekce=GOREV_BOLUMU_GEREKCESI,
    )


def kurulum(kol: str, *, ogrenci: int | None = 120, uzun: bool = False) -> GeneralAssembly:
    """Kolun çağrılmış genel kurulu (`gke.KOLLAR`). Yeni okul dışında: açık dönem, görev bölümlü
    yönetim kurulu ve Denetleme Kurulu (`kurullar`), uydurma veli listesi; birinci toplantı
    `genel_kurul_ortak.BIRINCI_GUN`, yer `YER`."""

    birinci = gko.an(gko.BIRINCI_GUN)
    if kol == gke.KOL_MUDUR_9_1:
        gko.ders_yillari()
        okul_ve_mevcut(ogrenci, uzun=uzun)
        SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(opened_on=date(2026, 9, 7))
        gko.veli_aktar(VELILER)
        kurul = gk.planla(kind=AssemblyKind.OLAGAN, first_meeting_at=birinci, venue=YER).kurul
        with o.rol_olarak(AccountRole.MUDUR):
            return gk.cagir(kurul).kurul
    donem = gko.acik_donem(ogrenci)
    okul_ve_mevcut(ogrenci, uzun=uzun)
    kurullar(donem, uzun=uzun)
    gko.veli_aktar(VELILER)
    if kol == gke.KOL_YK:
        kurul = gk.planla(kind=AssemblyKind.OLAGAN, first_meeting_at=birinci, venue=YER).kurul
        return gko.olagan_cagir(kurul)
    kurul = gk.planla(kind=AssemblyKind.OLAGANUSTU, first_meeting_at=birinci, venue=YER).kurul
    neden, gundem = gko.OLAGANUSTU_NEDEN, gko.OLAGANUSTU_GUNDEM
    if kol == gke.KOL_DK_14_5:
        with o.rol_olarak(AccountRole.DENETLEME_KURULU):
            rapor = denetim.denetim_raporu_yaz(
                kind="ARA", report_date=date(2026, 9, 30), md6_violation_found=True
            )
            return gk.cagir(
                kurul,
                called_by=AssemblyCaller.DENETLEME_KURULU,
                call_audit_report=rapor,
                call_reason=neden,
                gundem=gundem,
            ).kurul
    if kol == gke.KOL_YUZDE_10:
        return gk.cagir(
            kurul,
            called_by=AssemblyCaller.UYE_BASVURUSU,
            member_application_count=10,
            member_count_declared=100,
            call_reason=neden,
            gundem=gundem,
        ).kurul
    cagiranlar = {
        gke.KOL_BASKAN_13_8: (AccountRole.BASKAN, AssemblyCaller.BASKAN_VEYA_MUDUR_13_8),
        gke.KOL_MUDUR_9_6: (AccountRole.MUDUR, AssemblyCaller.OKUL_MUDURU),
        gke.KOL_MUDUR_13_8: (AccountRole.MUDUR, AssemblyCaller.BASKAN_VEYA_MUDUR_13_8),
        gke.KOL_MUDUR_25_2: (AccountRole.MUDUR, AssemblyCaller.MUDUR_25_2),
    }
    rol, cagiran = cagiranlar[kol]
    with o.rol_olarak(rol):
        return gk.cagir(kurul, called_by=cagiran, call_reason=neden, gundem=gundem).kurul


def ilanli(kurul: GeneralAssembly, *, ikinci_gun: bool = True) -> GeneralAssembly:
    """Üç kanalda ilan (15 gün); ikinci toplantının günü ilk ilanda."""

    ikinci = gko.an(gko.IKINCI_GUN) if ikinci_gun else None
    return gk.ilan_et(kurul, kanallar=gko.kanallar(), second_meeting_at=ikinci).kurul


#: Birinci toplantının uydurma dağılımı (toplamı katılana eşit) ve gözlemcisi.
DAGILIM_BIRINCI = {"VELI_KURSIYER": 60, "OGRETMEN": 8, "IDARECI": 2}
DAGILIM_YETERSIZ = {"VELI_KURSIYER": 7, "OGRETMEN": 3}
DAGILIM_IKINCI = {"VELI_KURSIYER": 15, "OGRETMEN": 4, "HAYIRSEVER": 1}


def birinci_toplantida_yapilmis(kurul: GeneralAssembly) -> GeneralAssembly:
    """Birinci toplantıda yeter sayı sağlandı (70 ≥ 64); divan seçildi (uydurma veliler)."""

    gk.birinci_toplanti(
        kurul, katilim=gko.katilim(70, dagilim=DAGILIM_BIRINCI, gozlemci=6, velisi_katilan=62)
    )
    gk.divan_sec(kurul, baskan=o.kisi(), katip=o.kisi())
    return GeneralAssembly.objects.get(pk=kurul.pk)


def birinci_toplantida_yetersiz(kurul: GeneralAssembly) -> GeneralAssembly:
    """Birinci toplantıda yeter sayı sağlanamadı (10 < 64)."""

    return gk.birinci_toplanti(
        kurul, katilim=gko.katilim(10, dagilim=DAGILIM_YETERSIZ, gozlemci=3)
    ).kurul


def ikinci_toplantida_yapilmis(kurul: GeneralAssembly) -> GeneralAssembly:
    """İkinci toplantı (çoğunluk aranmaz; 20 katılan) ve divan."""

    gk.ikinci_toplanti(kurul, katilim=gko.katilim(20, dagilim=DAGILIM_IKINCI, gozlemci=2))
    gk.divan_sec(kurul, baskan=o.kisi(), katip=o.kisi())
    return GeneralAssembly.objects.get(pk=kurul.pk)
