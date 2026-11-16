"""Genel kurul evrakı testlerinin ortak kurulumu.

8. adım (plan F2 §8: "hattın sınanması için en az bir deneme kurucusu"): hat (kayıt, dosya, kip,
toplantı, veli adlı çıktı, basım) deneme kurucularıyla sınanır; kurucular yalnız testte `KURUCULAR` ve
`ADLI_KURUCULAR` sözlüklerine konur (`kuruculari_kur`).

9. adım (E05, E06, E07, E08, E64'ün gerçek kurucuları): çağıranın kolu başına çağrılmış genel kurul
(`kurulum`; görev bölümlü yönetim kurulu ve Denetleme Kurulu, okul kartı, veli listesi), ilan ve
toplantılar. 10. adım (E09-E14): tutanağı yazılmış genel kurul (`tutanakli`; gündem değişikliği,
kararlar, ibra, seçim, tutanak bilgileri), yeni yönetim kurulunun görev bölümü (`gorev_bolumlu`) ve
dönemin okul planı (`takvimli_donem`); E04'ün okul kartı (`aydinlatma_okulu`). Adlar UYDURMADIR; veli
adları aranacak belirgin dizgilerdir.
"""

from __future__ import annotations

from datetime import date

import pytest
from django.db import models

from apps.oab.models import (
    AgendaItem,
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


def aydinlatma_okulu(*, uzun: bool = False, veri_sorumlusu: str = VERI_SORUMLUSU) -> SchoolConfig:
    """E04'ün konusu: okul kartı (uydurma; veri sorumlusu verilen metin, boş da olabilir)."""
    ge_ortak.okul_karti(uzun=uzun, data_controller_text=veri_sorumlusu)
    return SchoolConfig.load()


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


def kurulum(
    kol: str,
    *,
    ogrenci: int | None = 120,
    uzun: bool = False,
    gundem: tuple[gk.GundemMaddesi, ...] | None = None,
) -> GeneralAssembly:
    """Kolun çağrılmış genel kurulu (`gke.KOLLAR`). Yeni okul dışında: açık dönem, görev bölümlü
    yönetim kurulu ve Denetleme Kurulu (`kurullar`), uydurma veli listesi; birinci toplantı
    `genel_kurul_ortak.BIRINCI_GUN`, yer `YER`. Olağanüstü kollarda çağrının gündemi `gundem`
    (verilmezse `genel_kurul_ortak.OLAGANUSTU_GUNDEM`)."""

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
    neden, gundem = gko.OLAGANUSTU_NEDEN, gundem or gko.OLAGANUSTU_GUNDEM
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


# ---------------------------------------------------------------------------
# 10. adım: tutanağı yazılmış genel kurul (E09-E13) ve dönemin takvimi (E14)
# ---------------------------------------------------------------------------
#: Gündeme oylamayla eklenen uydurma madde ve oyları (md. 9/4).
EKLENEN_MADDE = "Uydurma ek madde: okul bahçesinin düzenlenmesi"
EKLEME_OYLARI = (50, 10)


def oranli(oylar: tuple[int, int], katilan: int) -> tuple[int, int]:
    """Birinci toplantının 70 katılanına göre yazılmış oyların `katilan`a oranlanmışı (ikinci
    toplantının 20 katılanında da oylar katılımı aşmaz, kabul yine çoğunluktadır)."""
    return oylar[0] * katilan // gko.KATILAN, oylar[1] * katilan // gko.KATILAN


#: Yetkilendirme kararının oyları (salonda 70; 60 > 35: kabul) ve uydurma sonuç metni.
YETKILENDIRME_OYLARI = (60, 5)
YETKILENDIRME_METNI = "Uydurma sınır: tahmini bütçe çerçevesinde."
#: İbra edilmeyen muhasebe evrakının uydurma listesi (tutanağın şifreli notu; satır başına bir evrak).
IBRA_EDILMEYEN_EVRAK = (
    "Uydurma gider belgeleri dosyası (Ocak-Mart)\nUydurma banka dekontları (12 adet)\n"
)
#: Yönetim kurulunun seçilen asıl ve yedek sayısı, Denetleme Kurulu veli koltuğu (asıl ve yedek).
YK_ASIL = 5
YK_YEDEK = 1


def tutanakli(kurul: GeneralAssembly, *, ibra_edilmedi: bool = False) -> GeneralAssembly:
    """Yapılmış genel kurulun (`YAPILDI`) tutanağı: oylamayla eklenen madde, yetkilendirme kabul
    (oylu, sonuç metniyle), öteki maddeler "görüşüldü", ibra (yönetim kurulu edildi ya da edilmedi —
    evrak notuyla; Denetleme Kurulu edildi), seçim (yönetim kurulu beş asıl bir yedek; olağanda
    Denetleme Kurulunun veli koltuğu bir asıl bir yedek; adayların biri seçilmez), tutanak bilgileri
    (okuyanlar ve bütçeyi sunan). Oylar yapıldığı toplantının katılımına oranlanır."""
    katilan = (
        kurul.second_attendee_count
        if kurul.held_at_meeting == "IKINCI"
        else kurul.first_attendee_count
    )
    assert katilan is not None
    gk.gundeme_madde_ekle(
        kurul,
        title=EKLENEN_MADDE,
        change_votes_for=oranli(EKLEME_OYLARI, katilan)[0],
        change_votes_against=oranli(EKLEME_OYLARI, katilan)[1],
        gerekce=gko.GEREKCE,
    )
    for madde in AgendaItem.objects.filter(assembly=kurul).order_by("order"):
        if madde.kind in ("IBRA", "SECIM_YK", "SECIM_DK"):
            continue
        if madde.kind == "YETKILENDIRME":
            gk.karar_sonucu_yaz(
                madde,
                votes_for=oranli(YETKILENDIRME_OYLARI, katilan)[0],
                votes_against=oranli(YETKILENDIRME_OYLARI, katilan)[1],
                result_text=YETKILENDIRME_METNI,
            )
        else:
            gk.karar_sonucu_yaz(madde, result="GORUSULDU")
    if AgendaItem.objects.filter(assembly=kurul, kind="IBRA").exists():
        gk.ibra_yaz(
            gko.madde(kurul, "IBRA"),
            yk=gko.IBRA_EDILMEDI if ibra_edilmedi else gko.IBRA_EDILDI,
            dk=gko.IBRA_EDILDI,
            unaudited_documents_note=IBRA_EDILMEYEN_EVRAK if ibra_edilmedi else "",
        )
    yk = [gko.aday(kurul) for _ in range(YK_ASIL)]
    yk += [gko.aday(kurul, seat_type="YEDEK") for _ in range(YK_YEDEK)]
    secilmeyen = gko.aday(kurul, seat_type="YEDEK")
    gk.secim_sonucu_yaz(
        gko.madde(kurul, "SECIM_YK"),
        adaylar=[
            *(
                gk.AdayOyu(uyelik=u, votes=katilan - 10 - sira, secildi=True)
                for sira, u in enumerate(yk)
            ),
            gk.AdayOyu(uyelik=secilmeyen, votes=3, secildi=False),
        ],
        liste=True,
        acik_oy=True,
    )
    if kurul.kind == AssemblyKind.OLAGAN:
        dk = [gko.aday(kurul, organ="DK"), gko.aday(kurul, organ="DK", seat_type="YEDEK")]
        gko.secim(kurul, "SECIM_DK", dk, oylar=list(oranli((55, 40), katilan)))
    gk.tutanak_bilgilerini_yaz(
        kurul,
        yk_report_reader=o.kisi(),
        dk_report_reader=o.kisi(),
        budget_presenter=o.kisi(),
    )
    return GeneralAssembly.objects.get(pk=kurul.pk)


def yapilmis_tutanakli(*, ibra_edilmedi: bool = False, uzun: bool = False) -> GeneralAssembly:
    """Yönetim kurulunun çağrısıyla birinci toplantıda yapılmış olağan genel kurul ve tutanağı."""
    kurul = birinci_toplantida_yapilmis(ilanli(kurulum(gke.KOL_YK, uzun=uzun)))
    return tutanakli(kurul, ibra_edilmedi=ibra_edilmedi)


#: Yeni yönetim kurulunun görev bölümü günü (genel kuruldan iki gün sonra) ve gerekçesi.
YENI_GOREV_BOLUMU_GUNU = date(2026, 10, 22)


def gorev_bolumlu(kurul: GeneralAssembly) -> GeneralAssembly:
    """Tutanak tamamlanır, dönem geçişi onaylanır (U32), yeni yönetim kurulu görev bölümü yapar:
    başkan ve sekreter seçilenlerin ilk ikisidir (U21: E12 ve E13 yeni başkanı ister)."""
    gk.tutanagi_tamamla(kurul, gerekce=gko.GEREKCE)
    yeni = gk.donem_gecisini_onayla(kurul).yeni_donem
    secilenler = [
        u
        for u in gke._kurul_secilenleri(kurul, "YK")
        if u.seat_type == "ASIL" and u.status == "SECILDI"
    ]
    o.yk_gorev_bolumu(
        yeni,
        {MembershipRole.BASKAN: secilenler[0], MembershipRole.SEKRETER: secilenler[1]},
        gun=YENI_GOREV_BOLUMU_GUNU,
        gerekce=GOREV_BOLUMU_GEREKCESI,
    )
    return GeneralAssembly.objects.get(pk=kurul.pk)


#: Dönemin okul planı (E14): yönetim kurulunun aylık toplantı günü ve denetim planı (uydurma).
YK_TOPLANTI_GUNU = "Her ayın ilk salı günü"
DENETIM_PLANI = (date(2026, 1, 15), date(2026, 4, 15))


def takvimli_donem(*, kantin: str = "KIRAYA_VERILIYOR", uzun: bool = False) -> OabTerm:
    """Açık dönem (başlangıcı `genel_kurul_ortak.DONEM_BASI`), okul kartı, dönemin okul planı ve
    kantin işletme biçimi; dönemi kapatacak olağan genel kurul henüz planlanmadı."""
    donem = gko.acik_donem()
    okul_ve_mevcut(uzun=uzun)
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(canteen_mode=kantin)
    OabTerm.objects.filter(pk=donem.pk).update(
        yk_meeting_day_rule=YK_TOPLANTI_GUNU,
        dk_audit_plan_dates=[gun.isoformat() for gun in DENETIM_PLANI],
    )
    return OabTerm.objects.get(pk=donem.pk)
