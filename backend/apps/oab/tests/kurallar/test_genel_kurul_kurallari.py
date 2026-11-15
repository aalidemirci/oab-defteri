"""Genel kurul kuralları (`gk`, tasarım §10.3): yeter sayının hesabı ve anlık görüntüsü; F2 4.
adımdan beri genel kurulun durum makinesinin kuralları, 5. adımdan beri gündem, karar ve divan
kuralları, 6. adımdan beri seçim, ibra ve tutanak kuralları (dosyanın sonu), 7. adımdan beri müdürün ve
Denetleme Kurulunun çağrısı ile üyelerin başvurusunun gelen evrak bağı (çağıran testlerinin yanında).

Yeter sayı 16 × 4 (mevcut ≥ 100) ya da 16 × 2 (mevcut < 100); taban kurul bileşiminden gelir, üyelik
kaydı sayılmaz; olağanüstü genel kurulda da aynıdır (tasarım §12.A S-1, S-2 düzeltmeleri). Değerler
`DEGER_TABLOSU` ile elle karşılaştırılmıştır.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from apps.oab.hatalar import GerekceGerekli, KuralSert, YeterSayiDonduruldu
from apps.oab.kurallar import denetle, genel_kurul, kural
from apps.oab.models import (
    AgendaItem,
    AgendaItemKind,
    AgendaResult,
    Announcement,
    AssemblyCaller,
    AssemblyKind,
    AssemblyMeeting,
    AssemblyMinutes,
    AssemblyStatus,
    AuditReport,
    ComplianceItem,
    ComplianceKind,
    DocumentDirection,
    DocumentRecord,
    GeneralAssembly,
    MembershipRole,
    MembershipStatus,
    OabTerm,
    OrganMembership,
    OrganType,
    PersonKind,
    TermStatus,
)
from apps.oab.services import denetim, donemler, gelen_giden_evrak, uyum
from apps.oab.services import genel_kurul as genel_kurul_servisi
from apps.oab.tests import genel_kurul_ortak as gko
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import AccountRole, AuditAction, AuditTrail, SchoolConfig, SchoolYear
from shared.exceptions import RolYetkisiz

GUN = date(2026, 10, 1)


def _donem() -> OabTerm:
    yil = SchoolYear.objects.create(
        name="2026-2027",
        start_date=date(2026, 9, 7),
        end_date=date(2027, 6, 25),
        is_active=True,
    )
    return donemler.create_term(name="2026-2027 birlik dönemi", school_year=yil, start_date=GUN)


def _okul_mevcudu(mevcut: int) -> None:
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK,
        defaults={"student_count": mevcut, "student_count_as_of": GUN},
    )


@pytest.mark.kural_davranis("genel_kurul.yeter_sayi_taban")
def test_taban_uyelik_kayitlarindan_bagimsiz_16() -> None:
    """Hesabın girdisinde üyelik yoktur: eksik kadroda da 64/32 (tasarım §12.A S-1 düzeltmesi)."""
    buyuk = genel_kurul.genel_kurul_yeter_sayisi(100, tarih=GUN)
    kucuk = genel_kurul.genel_kurul_yeter_sayisi(99, tarih=GUN)
    assert (buyuk.taban, buyuk.gerekli) == (16, 64)
    assert (kucuk.taban, kucuk.gerekli) == (16, 32)


@pytest.mark.kural_davranis("genel_kurul.yeter_sayi_carpan")
def test_yeter_sayi_mevcut_100_ve_ustu_64() -> None:
    for mevcut in (100, 101, 1200):
        hesap = genel_kurul.genel_kurul_yeter_sayisi(mevcut, tarih=GUN)
        assert (hesap.taban, hesap.carpan, hesap.gerekli) == (16, 4, 64)


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.yeter_sayi_carpan")
def test_olaganustu_gk_yeter_sayi_64() -> None:
    """Olağanüstü genel kurulda da aynı çarpan (md. 9/6; tasarım §12.A S-2 düzeltmesi)."""
    _okul_mevcudu(150)
    kurul = genel_kurul_servisi.genel_kurul_olustur(donem=_donem(), kind=AssemblyKind.OLAGANUSTU)
    donmus = genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert (donmus.quorum_base, donmus.quorum_multiplier, donmus.quorum_required) == (16, 4, 64)


@pytest.mark.kural_davranis("genel_kurul.kucuk_okul_carpan")
def test_yeter_sayi_mevcut_99_32() -> None:
    hesap = genel_kurul.genel_kurul_yeter_sayisi(99, tarih=GUN)
    assert (hesap.taban, hesap.carpan, hesap.gerekli) == (16, 2, 32)


@pytest.mark.kural_davranis("genel_kurul.kucuk_okul_esik")
def test_esik_99_ve_100() -> None:
    """Sınırın iki yanı: 99 → küçük okul, 100 → büyük okul."""
    assert genel_kurul.genel_kurul_yeter_sayisi(99, tarih=GUN).gerekli == 32
    assert genel_kurul.genel_kurul_yeter_sayisi(100, tarih=GUN).gerekli == 64


def test_eksi_mevcut_hatadir() -> None:
    with pytest.raises(ValueError, match="eksi"):
        genel_kurul.genel_kurul_yeter_sayisi(-1, tarih=GUN)


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.kucuk_okul_esik")
def test_mevcut_gk_kaydina_anlik_yazilir() -> None:
    """Okul kartı sonradan değişse de genel kurulun dondurulmuş hesabı değişmez (O7)."""
    _okul_mevcudu(120)
    kurul = genel_kurul_servisi.genel_kurul_olustur(
        donem=_donem(),
        kind=AssemblyKind.OLAGAN,
        first_meeting_at=datetime(2026, 10, 20, tzinfo=UTC),
    )
    donmus = genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert donmus.student_count_snapshot == 120
    assert donmus.quorum_required == 64

    _okul_mevcudu(40)
    assert GeneralAssembly.objects.get(pk=kurul.pk).student_count_snapshot == 120
    with pytest.raises(YeterSayiDonduruldu):
        genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert GeneralAssembly.objects.get(pk=kurul.pk).quorum_required == 64


@pytest.mark.django_db
def test_mevcut_girilmemisse_yeter_sayi_hesaplanmaz() -> None:
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK,
        defaults={"student_count": None, "student_count_as_of": None},
    )
    kurul = genel_kurul_servisi.genel_kurul_olustur(donem=_donem(), kind=AssemblyKind.OLAGAN)
    with pytest.raises(ValueError, match="öğrenci mevcudu"):
        genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)


@pytest.mark.kural_davranis("denetleme_kurulu.koltuklar")
def test_dk_ogretmen_koltugu_gk_oylamasina_girmez() -> None:
    """Denetleme Kurulunun öğretmen koltukları öğretmenler kurulunca seçilir (md. 14/1)."""
    koltuklar = genel_kurul.genel_kurul_oylamasindaki_koltuklar(tarih=GUN)
    assert koltuklar == {"YK": {"ASIL": 5, "YEDEK": 5}, "DK_VELI": {"ASIL": 1, "YEDEK": 1}}


# ======================================================================= F2 4. adım: genel kurul akışı
# Durum makinesinin kuralları (tasarım §7.1; plan F2 §3.1, §3.2, §7 U7-U12, U19). Kurulum
# `genel_kurul_ortak`'tadır: kapanacak dönem 2025-2026, birinci toplantı 20.10.2026, mevcut 120 (yeter
# sayı 64). Adlar UYDURMADIR.


def _sapmalar(kural_id: str) -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(rule_id=kural_id, kind=ComplianceKind.SAPMA).order_by("pk")
    )


def _acik_satirlar(kural_id: str) -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(rule_id=kural_id, resolved_at__isnull=True).order_by("pk")
    )


def _iptal(kurul: GeneralAssembly) -> None:
    genel_kurul_servisi.iptal_et(kurul, cancel_reason="Uydurma: tarih yanlış girildi.")


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olagan_son_ay")
def test_olagan_gk_31_ekim_uyarisiz_1_kasim_uyari() -> None:
    """md. 9/1 "en geç Ekim ayının sonuna kadar"; S3: birinci toplantının günü, Europe/Istanbul. 31.10
    akşamı uyarısız; 01.11'in ilk saati (UTC'de hâlâ 31.10) uyarı + gerekçe."""
    gko.acik_donem()
    ekim_sonu = gko.an(date(2026, 10, 31), saat=23, dakika=30)
    sonuc = genel_kurul_servisi.planla(kind=AssemblyKind.OLAGAN, first_meeting_at=ekim_sonu)
    assert sonuc.uyarilar == ()
    assert _acik_satirlar("genel_kurul.olagan_son_ay") == []
    _iptal(sonuc.kurul)

    kasim_ilk_saat = datetime(2026, 10, 31, 21, 30, tzinfo=UTC)  # 01.11.2026 00:30 yerel
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.planla(kind=AssemblyKind.OLAGAN, first_meeting_at=kasim_ilk_saat)
    assert not OabTerm.objects.filter(status=TermStatus.HAZIRLIK).exists()
    sonuc = genel_kurul_servisi.planla(
        kind=AssemblyKind.OLAGAN, first_meeting_at=kasim_ilk_saat, gerekce=gko.GEREKCE
    )
    (satir,) = _sapmalar("genel_kurul.olagan_son_ay")
    assert satir.subject_id == str(sonuc.kurul.pk)
    assert satir.subject_type == "oab.GeneralAssembly"
    assert [u["kural"] for u in sonuc.uyarilar] == ["genel_kurul.olagan_son_ay"]
    assert sonuc.kurul.rule_warnings[0]["kural"] == "genel_kurul.olagan_son_ay"


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.yeni_okul_ay")
def test_yeni_okul_gk_acilistan_2_ay() -> None:
    """md. 9/1 "okulun açıldığı tarihten itibaren en geç iki ay içinde"; takvim ayı aritmetiği. Açılış
    15.09.2026: 15.11 uyarısız, 16.11 uyarı + gerekçe. Kapanacak dönem yoktur (S5): uyum satırı
    hazırlık dönemine yazılır, çağıran okul müdürüdür (çağrısı 7. adımda)."""
    gko.ders_yillari()
    gko.mevcut()
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(opened_on=date(2026, 9, 15))
    sonuc = genel_kurul_servisi.planla(
        kind=AssemblyKind.OLAGAN, first_meeting_at=gko.an(date(2026, 11, 15))
    )
    kurul = sonuc.kurul
    assert sonuc.uyarilar == ()
    assert kurul.term_id is None
    assert kurul.called_by == AssemblyCaller.MUDUR_YENI_OKUL
    assert kurul.opens_term is not None and kurul.opens_term.status == TermStatus.HAZIRLIK
    _iptal(kurul)

    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.planla(
            kind=AssemblyKind.OLAGAN, first_meeting_at=gko.an(date(2026, 11, 16))
        )
    sonuc = genel_kurul_servisi.planla(
        kind=AssemblyKind.OLAGAN, first_meeting_at=gko.an(date(2026, 11, 16)), gerekce=gko.GEREKCE
    )
    (satir,) = _sapmalar("genel_kurul.yeni_okul_ay")
    assert satir.term_id == sonuc.kurul.opens_term_id
    # Takvim ayı ayın son günüyle sınırlıdır: 31.12'den iki ay 28.02'dir (artık olmayan yıl).
    assert genel_kurul_servisi.ay_farki(date(2026, 12, 31), date(2027, 2, 28)) == 2
    assert genel_kurul_servisi.ay_farki(date(2026, 12, 31), date(2027, 3, 1)) == 3


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ilan_en_az_gun")
def test_ilan_15_gun_uyarisiz() -> None:
    """md. 9/3 "en az onbeş gün önceden": 05.10 → 20.10 on beş gün; uyarı yok, yeter sayı donar (U7)."""
    kurul = gko.cagrilmis_olagan()
    sonuc = genel_kurul_servisi.ilan_et(kurul, kanallar=gko.kanallar(date(2026, 10, 5)))
    assert sonuc.uyarilar == ()
    assert sonuc.kurul.status == AssemblyStatus.ILAN_EDILDI
    assert sonuc.kurul.announced_on == date(2026, 10, 5)
    assert sonuc.kurul.quorum_required == 64
    assert _acik_satirlar("genel_kurul.ilan_en_az_gun") == []


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ilan_en_az_gun")
def test_ilan_13_gun_gerekcesiz_reddedilir() -> None:
    """OYS AYNEN (uyarı + gerekçeli geçiş): 13 gün gerekçesiz geçmez; işlem bütünüyle geri alınır
    (ilan kaydı yazılmaz, yeter sayı donmaz, durum değişmez)."""
    kurul = gko.cagrilmis_olagan()
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.ilan_et(kurul, kanallar=gko.kanallar(date(2026, 10, 7)))
    guncel = GeneralAssembly.objects.get(pk=kurul.pk)
    assert guncel.status == AssemblyStatus.CAGRILDI
    assert guncel.quorum_required is None
    assert not Announcement.objects.exists()


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ilan_en_az_gun")
def test_ilan_13_gun_gerekceyle_gecer() -> None:
    """13 gün gerekçeyle kayda geçer; satırın konusu ilan kaydıdır (ikinci ilan birincinin satırını
    ezmez). Bağlayıcı gün en geç kanalınkidir (U9): iki kanal 01.10, biri 07.10 → 13 gün."""
    kurul = gko.cagrilmis_olagan()
    sonuc = genel_kurul_servisi.ilan_et(
        kurul,
        kanallar=genel_kurul_servisi.IlanKanallari(
            distributed_written_on=date(2026, 10, 1),
            posted_board_on=date(2026, 10, 7),
            published_web_on=date(2026, 10, 1),
        ),
        gerekce=gko.GEREKCE,
    )
    (duyuru,) = genel_kurul_servisi.kurulun_duyurulari(sonuc.kurul)
    (satir,) = _sapmalar("genel_kurul.ilan_en_az_gun")
    assert (satir.subject_type, satir.subject_id) == ("oab.Announcement", str(duyuru.pk))
    assert "13 gün" in satir.message
    assert sonuc.kurul.announced_on == date(2026, 10, 7)
    assert sonuc.kurul.status == AssemblyStatus.ILAN_EDILDI


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ilan_en_az_gun")
def test_ilan_sinir_14_uyari_15_uyarisiz() -> None:
    """Sınırın iki yanı (yerel takvim günü, U9): 14 gün uyarı, 15 gün uyarısız."""
    kurul = gko.cagrilmis_olagan()
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.ilan_et(kurul, kanallar=gko.kanallar(date(2026, 10, 6)))
    sonuc = genel_kurul_servisi.ilan_et(kurul, kanallar=gko.kanallar(date(2026, 10, 5)))
    assert sonuc.uyarilar == ()
    assert ComplianceItem.objects.filter(rule_id="genel_kurul.ilan_en_az_gun").count() == 0


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ilan_kanallari")
def test_uc_kanal_kaniti_eksikse_tamamlanacak() -> None:
    """md. 9/3 üç kanal: kanıt günü girilmemiş kanal eksiktir (tamamlanacaklar), gerekçe istemez; kanıt
    sonradan girilince satır kapanır."""
    kurul = gko.cagrilmis_olagan()
    iki_kanal = genel_kurul_servisi.IlanKanallari(
        distributed_written_on=gko.ILAN_GUNU, posted_board_on=gko.ILAN_GUNU
    )
    sonuc = genel_kurul_servisi.ilan_et(kurul, kanallar=iki_kanal)
    (duyuru,) = genel_kurul_servisi.kurulun_duyurulari(sonuc.kurul)
    (satir,) = _acik_satirlar("genel_kurul.ilan_kanallari")
    assert satir.kind == ComplianceKind.EKSIK
    assert satir.justification_group_id is None
    assert (satir.subject_type, satir.subject_id) == ("oab.Announcement", str(duyuru.pk))
    assert [u["durum"] for u in sonuc.uyarilar] == ["eksik"]

    genel_kurul_servisi.ilan_kanitlarini_yaz(duyuru, kanallar=gko.kanallar())
    assert _acik_satirlar("genel_kurul.ilan_kanallari") == []
    duyuru.refresh_from_db()
    assert duyuru.published_web_on == gko.ILAN_GUNU


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ikinci_toplanti_en_gec_gun")
def test_ikinci_toplanti_baglantisi() -> None:
    """OYS UYARLA (U8, U31): iki toplantı tek kayıttadır. Birinci toplantıda 40 < 64: durum `IPTAL`
    değil `YETER_SAYI_YOK`; ikinci toplantı ayrı ilanla aynı kayda yazılır, yeter sayı aynı kalır."""
    kurul = gko.ilanli_olagan()
    sonuc = genel_kurul_servisi.birinci_toplanti(kurul, katilim=gko.katilim(40))
    assert sonuc.kurul.status == AssemblyStatus.YETER_SAYI_YOK
    assert (sonuc.kurul.first_attendee_count, sonuc.kurul.held_at_meeting) == (40, "")
    with pytest.raises(ValueError, match="toplantının tarihi ilan edilmedi"):
        genel_kurul_servisi.ikinci_toplanti(kurul, katilim=gko.katilim(25))
    ikinci = gko.an(date(2026, 11, 10))
    genel_kurul_servisi.ikinci_toplanti_ilani(
        kurul, second_meeting_at=ikinci, kanallar=gko.kanallar(date(2026, 10, 24))
    )
    sonuc = genel_kurul_servisi.ikinci_toplanti(kurul, katilim=gko.katilim(25))
    yapildi = sonuc.kurul
    assert GeneralAssembly.objects.count() == 1
    assert yapildi.status == AssemblyStatus.YAPILDI
    assert yapildi.held_at_meeting == AssemblyMeeting.IKINCI
    assert (yapildi.second_meeting_at, yapildi.second_announced_on) == (ikinci, date(2026, 10, 24))
    assert (yapildi.first_attendee_count, yapildi.second_attendee_count) == (40, 25)
    assert yapildi.quorum_required == 64
    assert len(genel_kurul_servisi.kurulun_duyurulari(yapildi)) == 2


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ikinci_toplanti_en_gec_gun")
def test_ikinci_toplanti_30_gun_uyarisiz_31_uyari() -> None:
    """md. 9/2 "en geç otuz gün içinde", birinci toplantının gününden: ilanda 30 gün uyarısız (19.11);
    ayrı ikinci toplantı ilanında 31 gün (20.11) uyarı + gerekçe, satırın konusu genel kuruldur."""
    kurul = gko.cagrilmis_olagan()
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.ilan_et(
            kurul, kanallar=gko.kanallar(), second_meeting_at=gko.an(date(2026, 11, 20))
        )
    sonuc = genel_kurul_servisi.ilan_et(
        kurul, kanallar=gko.kanallar(), second_meeting_at=gko.an(date(2026, 11, 19))
    )
    assert sonuc.uyarilar == ()
    genel_kurul_servisi.birinci_toplanti(kurul, katilim=gko.katilim(10))
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.ikinci_toplanti_ilani(
            kurul, second_meeting_at=gko.an(date(2026, 11, 20)), kanallar=gko.kanallar()
        )
    genel_kurul_servisi.ikinci_toplanti_ilani(
        kurul,
        second_meeting_at=gko.an(date(2026, 11, 20)),
        kanallar=gko.kanallar(),
        gerekce=gko.GEREKCE,
    )
    (satir,) = _sapmalar("genel_kurul.ikinci_toplanti_en_gec_gun")
    assert (satir.subject_type, satir.subject_id) == ("oab.GeneralAssembly", str(kurul.pk))
    assert "31 gün" in satir.message


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ikinci_toplanti_cogunluk_aranmaz")
def test_ikinci_toplanti_cogunluksuz() -> None:
    """md. 9/2 "çoğunluk aranmaksızın": ikinci toplantı 3 kişiyle de yapılır (64'ün altında). Gözlemci
    öğrenci (md. 9/5) katılım sayısına girmez; dağılımın toplamı katılımı tutar."""
    kurul = gko.ilanli_olagan(second_meeting_at=gko.an(date(2026, 11, 3)))
    genel_kurul_servisi.birinci_toplanti(kurul, katilim=gko.katilim(10))
    sonuc = genel_kurul_servisi.ikinci_toplanti(
        kurul,
        katilim=gko.katilim(3, dagilim={"VELI_KURSIYER": 2, "OGRETMEN": 1}, gozlemci=5),
    )
    assert sonuc.uyarilar == ()
    yapildi = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (yapildi.status, yapildi.held_at_meeting) == (
        AssemblyStatus.YAPILDI,
        AssemblyMeeting.IKINCI,
    )
    assert (yapildi.second_attendee_count, yapildi.observer_count) == (3, 5)
    assert not ComplianceItem.objects.filter(
        rule_id="genel_kurul.ikinci_toplanti_cogunluk_aranmaz"
    ).exists()


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ikinci_toplanti_cogunluk_aranmaz")
def test_olaganustu_ikinci_toplanti_cogunluksuz() -> None:
    """Kullanıcı kararı A-1: md. 9/2'nin ikinci toplantısı olağanüstü genel kurulda da açılır. 31 günlük
    ikinci toplantının uyarısı A-1 atfını taşır (U10); ikinci toplantıda çoğunluk aranmaz."""
    gko.acik_donem()
    kurul = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    with pytest.raises(GerekceGerekli) as hata:
        genel_kurul_servisi.ilan_et(
            kurul, kanallar=gko.kanallar(), second_meeting_at=gko.an(date(2026, 11, 20))
        )
    assert "A-1" in str(hata.value.detail)
    genel_kurul_servisi.ilan_et(
        kurul,
        kanallar=gko.kanallar(),
        second_meeting_at=gko.an(date(2026, 11, 20)),
        gerekce=gko.GEREKCE,
    )
    (satir,) = _sapmalar("genel_kurul.ikinci_toplanti_en_gec_gun")
    assert satir.message.endswith(genel_kurul_servisi.A1_ATFI)
    genel_kurul_servisi.birinci_toplanti(kurul, katilim=gko.katilim(5))
    sonuc = genel_kurul_servisi.ikinci_toplanti(kurul, katilim=gko.katilim(2))
    assert (sonuc.kurul.status, sonuc.kurul.held_at_meeting) == (
        AssemblyStatus.YAPILDI,
        AssemblyMeeting.IKINCI,
    )
    assert sonuc.kurul.opens_term_id is None  # olağanüstü genel kurul dönem açmaz (md. 13/8)


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_cagiranlar")
def test_olaganustu_cagiran_listede() -> None:
    """md. 9/6 (2023 ek ibaresiyle), 13/8, 14/5, 25/2: listedeki çağıran uyarısızdır; listede olmayan
    tek değer yeni okulun müdür davetidir (olağanda geçerli, olağanüstüde uyarı). Yönetim kurulunun
    olağanüstü çağrısı servis yolundan uyarısız geçer; olağanüstüde çağrı kararı akış satırı yoktur."""
    donem = gko.acik_donem()
    cagrilan = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    assert cagrilan.status == AssemblyStatus.CAGRILDI
    assert cagrilan.called_by == AssemblyCaller.YONETIM_KURULU
    assert cagrilan.call_reason == gko.OLAGANUSTU_NEDEN
    assert not ComplianceItem.objects.filter(
        rule_id__in=("genel_kurul.olaganustu_cagiranlar", genel_kurul_servisi.KARARSIZ_CAGRI_AKISI)
    ).exists()
    assert [m.title for m in AgendaItem.objects.filter(assembly=cagrilan).order_by("order")] == [
        m.title for m in gko.OLAGANUSTU_GUNDEM
    ]
    donem = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    liste = kural("genel_kurul.olaganustu_cagiranlar", tarih=gko.BIRINCI_GUN, donem=donem)
    for cagiran in liste:
        sonuc = denetle(
            "genel_kurul.olaganustu_cagiranlar", cagiran, tarih=gko.BIRINCI_GUN, donem=donem
        )
        assert sonuc["durum"] == "uygun", cagiran
    disinda = denetle(
        "genel_kurul.olaganustu_cagiranlar",
        AssemblyCaller.MUDUR_YENI_OKUL,
        tarih=gko.BIRINCI_GUN,
        donem=donem,
    )
    assert disinda["durum"] == "uyari"
    assert set(AssemblyCaller.values) - set(liste) == {AssemblyCaller.MUDUR_YENI_OKUL}


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_cagiranlar")
def test_baskanin_13_8_cagrisi_listede() -> None:
    """md. 13/8: yönetim kurulu yedeklerle karar yeter sayısının altına düşünce başkan olağanüstü genel
    kurulu çağırır; çağıran listededir, uyarı yoktur. Kayıt başkanın hesabından (tasarım §7.1 "Kim");
    sekreter bu çağrıyı kaydedemez. Bir aylık süre F3'tedir (U11)."""
    gko.acik_donem()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.SEKRETER), pytest.raises(RolYetkisiz):
        genel_kurul_servisi.cagir(
            kurul,
            called_by=AssemblyCaller.BASKAN_VEYA_MUDUR_13_8,
            call_reason=gko.OLAGANUSTU_NEDEN,
            gundem=gko.OLAGANUSTU_GUNDEM,
        )
    with o.rol_olarak(AccountRole.BASKAN):
        sonuc = genel_kurul_servisi.cagir(
            kurul,
            called_by=AssemblyCaller.BASKAN_VEYA_MUDUR_13_8,
            call_reason=gko.OLAGANUSTU_NEDEN,
            gundem=gko.OLAGANUSTU_GUNDEM,
        )
    assert sonuc.uyarilar == ()
    assert sonuc.kurul.called_by == AssemblyCaller.BASKAN_VEYA_MUDUR_13_8
    assert sonuc.kurul.status == AssemblyStatus.CAGRILDI
    # Başkanın çağrısı müdürün yazısı değildir: evrak defterine programca işlenmez (⁷). Yazanın rolü
    # kayıttadır (E05'in imzası başkanın).
    assert sonuc.kurul.call_document_id is None
    assert sonuc.kurul.called_by_role == AccountRole.BASKAN
    assert genel_kurul_servisi.cagri_sahibi(sonuc.kurul) is None


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_cagiranlar")
def test_mudurun_13_8_cagrisi_mudur_hesabindan_listede() -> None:
    """md. 13/8 "birlik başkanı ya da okul müdürü": müdürün hesabından müdürün eylemiyle
    (`OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR`; tasarım §4.4.2 ¹) yazılır, çağıran listededir; müdürün yazısı
    evrak defterine giden evrak olarak işlenir (⁷). Yazanın rolü kayıttadır (`called_by_role`): çağrı
    müdürün yazısıdır, sahibi müdürdür."""
    gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.MUDUR):
        sonuc = genel_kurul_servisi.cagir(
            kurul,
            called_by=AssemblyCaller.BASKAN_VEYA_MUDUR_13_8,
            call_reason=gko.OLAGANUSTU_NEDEN,
            gundem=gko.OLAGANUSTU_GUNDEM,
        )
    assert sonuc.uyarilar == ()
    assert sonuc.kurul.called_by_role == AccountRole.MUDUR
    assert genel_kurul_servisi.cagri_sahibi(sonuc.kurul) == "mudur"
    yazi = DocumentRecord.objects.get()
    assert sonuc.kurul.call_document_id == yazi.pk
    assert (yazi.direction, yazi.subject) == (
        DocumentDirection.GIDEN,
        genel_kurul_servisi.MUDUR_YAZISI_KONUSU[AssemblyCaller.BASKAN_VEYA_MUDUR_13_8],
    )


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.yeni_okul_ay")
def test_yeni_okul_cagrisi_mudur_hesabindan() -> None:
    """md. 9/1 "yeni açılan okullarda … okul müdürünün daveti"; K2 ve §15 M-11: davet müdürün yazısıdır,
    müdürün hesabından yazılır (`Eylem.GENEL_KURUL_YENI_OKUL_DAVETI`; tasarım §4.4.2 ¹). Program yöneticisi,
    yönetim kurulu rolleri ve Denetleme Kurulu yazamaz; ret hiçbir şey yazmaz. Müdür genel kurulun öteki
    işlerinde okurdur (planlama, ilan). Kapanacak dönem yoktur (`term` boş, `opens_term` hazırlık dönemi;
    S5 (i)); yönetim kurulu kararı bağı akış satırı yazılmaz. Gelen-giden evrak defteri kayıtlıysa müdürün
    yazısı hazırlık dönemine giden evrak olarak programca işlenir (⁷), kaydın izi müdürün hesabıyladır."""
    gko.ders_yillari()
    gko.mevcut()
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(opened_on=date(2026, 9, 15))
    gelen_giden_evrak.evrak_defteri_olustur()
    kurul = gko.planla(birinci=gko.an(date(2026, 11, 10)))
    once = AuditTrail.objects.exclude(action=AuditAction.HESAP).count()
    for rol in (
        AccountRole.YONETICI,
        AccountRole.SEKRETER,
        AccountRole.BASKAN,
        AccountRole.DENETLEME_KURULU,
    ):
        with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
            genel_kurul_servisi.cagir(kurul)
    # Rolün oturumu için açılan hesabın `HESAP` satırı dışında iz yazılmaz.
    assert AuditTrail.objects.exclude(action=AuditAction.HESAP).count() == once
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.PLANLANDI
    with o.rol_olarak(AccountRole.MUDUR) as mudur:
        with pytest.raises(RolYetkisiz):
            gko.planla(birinci=gko.an(date(2026, 11, 11)))
        sonuc = genel_kurul_servisi.cagir(kurul)
        with pytest.raises(RolYetkisiz):
            genel_kurul_servisi.ilan_et(kurul, kanallar=gko.kanallar(date(2026, 10, 20)))
    cagrilan = sonuc.kurul
    assert (cagrilan.status, cagrilan.called_by, cagrilan.term_id) == (
        AssemblyStatus.CAGRILDI,
        AssemblyCaller.MUDUR_YENI_OKUL,
        None,
    )
    assert cagrilan.opens_term is not None and cagrilan.opens_term.status == TermStatus.HAZIRLIK
    assert sonuc.uyarilar == ()
    assert not ComplianceItem.objects.filter(
        rule_id=genel_kurul_servisi.KARARSIZ_CAGRI_AKISI
    ).exists()
    yazi = DocumentRecord.objects.get()
    assert cagrilan.call_document_id == yazi.pk
    assert (yazi.direction, yazi.term_id, yazi.record_no) == (
        DocumentDirection.GIDEN,
        cagrilan.opens_term_id,
        1,
    )
    durum = AuditTrail.objects.filter(
        model="oab.GeneralAssembly", object_id=str(kurul.pk), action=AuditAction.DURUM
    ).latest("seq")
    kayit_izi = AuditTrail.objects.get(model="oab.DocumentRecord", object_id=str(yazi.pk))
    for satir in (durum, kayit_izi):
        assert (str(satir.account_id), satir.role) == (str(mudur.id), "mudur")
    assert kayit_izi.action == AuditAction.OLUSTUR


def _md6_raporu(md6: bool = True, *, usulsuzluk: bool = False) -> AuditReport:
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        return denetim.denetim_raporu_yaz(
            kind="ARA",
            report_date=date(2026, 9, 30),
            md6_violation_found=md6,
            irregularity_found=usulsuzluk,
        )


def _baska_donem() -> OabTerm:
    """Genel kurulun döneminden başka bir birlik dönemi: olağan genel kurulun açtığı hazırlık dönemi
    (kaydı başka döneme taşımak için; testin kurgusu)."""
    hazirlik = OabTerm.objects.filter(status=TermStatus.HAZIRLIK).first()
    if hazirlik is not None:
        return hazirlik
    acilan = gko.planla().opens_term
    assert acilan is not None
    return acilan


def _dk_cagrisi(
    kurul: GeneralAssembly,
    rapor: AuditReport | None,
    *,
    yazi: DocumentRecord | None = None,
) -> genel_kurul_servisi.GenelKurulSonucu:
    return genel_kurul_servisi.cagir(
        kurul,
        called_by=AssemblyCaller.DENETLEME_KURULU,
        call_reason=gko.OLAGANUSTU_NEDEN,
        gundem=gko.OLAGANUSTU_GUNDEM,
        call_document=yazi,
        call_audit_report=rapor,
    )


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_cagiranlar")
def test_dk_14_5_cagrisi_yalniz_md6_aykirilik_isaretiyle() -> None:
    """md. 14/5: Denetleme Kurulu, yönetim kurulunun md. 6'da sayılan görev ve yetkilere aykırı faaliyetini
    tespit ederse olağanüstü genel kurulu çağırır. Çağrı yalnız md. 6 aykırılık işaretli raporla açılır
    (kullanıcı kararı S6 (ii), sert): raporsuz ve yalnız usulsüzlük işaretli (`irregularity_found`, MB-10:
    müdürün md. 27/3 yolu) raporla reddedilir, hiçbir şey yazılmaz. Çağrı Denetleme Kurulunun hesabından
    (`Eylem.DK_GENEL_KURUL_YAZMA`; K2: yalnız denetim modülüne yazar); program yöneticisi ve yönetim kurulu
    rolleri adına yazamaz. İki bağ aynı işlemde yazılır; çağıran listededir, uyarı yoktur."""
    gko.acik_donem()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    usulsuzluk = _md6_raporu(False, usulsuzluk=True)
    isaretli = _md6_raporu()
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        once = AuditTrail.objects.count()
        for rapor in (None, usulsuzluk):
            with pytest.raises(ValueError, match="md. 14/5"):
                _dk_cagrisi(kurul, rapor)
        assert AuditTrail.objects.count() == once
    for rol in (AccountRole.YONETICI, AccountRole.SEKRETER, AccountRole.MUDUR):
        with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
            _dk_cagrisi(kurul, isaretli)
    # Yönetim kurulunun çağrısına denetim raporu bağlanmaz.
    with o.rol_olarak(AccountRole.SEKRETER), pytest.raises(ValueError):
        genel_kurul_servisi.cagir(
            kurul,
            called_by=AssemblyCaller.YONETIM_KURULU,
            call_reason=gko.OLAGANUSTU_NEDEN,
            gundem=gko.OLAGANUSTU_GUNDEM,
            call_audit_report=isaretli,
        )
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.PLANLANDI
    # Rapor genel kurulun birlik dönemine ait olmalıdır (S6 (ii), sert): başka dönemin işaretli raporu
    # çağrı açmaz, hiçbir şey yazılmaz.
    baska_donem = _md6_raporu()
    AuditReport.objects.filter(pk=baska_donem.pk).update(term=_baska_donem())
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        once = AuditTrail.objects.count()
        with pytest.raises(ValueError, match="birlik dönemine ait"):
            _dk_cagrisi(kurul, baska_donem)
        assert AuditTrail.objects.count() == once
    assert AuditReport.objects.get(pk=baska_donem.pk).escalated_assembly_id is None
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.PLANLANDI
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        sonuc = _dk_cagrisi(kurul, isaretli)
    assert sonuc.uyarilar == ()
    assert sonuc.kurul.called_by_role == AccountRole.DENETLEME_KURULU
    # Denetleme Kurulunun yazısını program işlemez; evrak bağı girilmedi (bilgi satırı).
    assert sonuc.kurul.call_document_id is None
    assert genel_kurul_servisi.DK_YAZISI_BAGSIZ in sonuc.bilgiler
    cagrilan = sonuc.kurul
    assert (cagrilan.status, cagrilan.called_by, cagrilan.call_audit_report_id) == (
        AssemblyStatus.CAGRILDI,
        AssemblyCaller.DENETLEME_KURULU,
        isaretli.pk,
    )
    assert AuditReport.objects.get(pk=isaretli.pk).escalated_assembly_id == kurul.pk
    assert AuditReport.objects.get(pk=usulsuzluk.pk).escalated_assembly_id is None
    assert genel_kurul_servisi.cagri_sahibi(cagrilan) == "denetleme_kurulu"
    # Bir rapor iki genel kurulu çağırmaz.
    ikinci = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.DENETLEME_KURULU), pytest.raises(ValueError):
        _dk_cagrisi(ikinci, isaretli)


def _uye_basvurusu(
    basvuran: int | None,
    uye: int | None,
    gerekce: uyum.Gerekce | None = None,
    *,
    yazi: DocumentRecord | None = None,
) -> genel_kurul_servisi.GenelKurulSonucu:
    if not OabTerm.objects.exists():
        gko.acik_donem()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    return genel_kurul_servisi.cagir(
        kurul,
        called_by=AssemblyCaller.UYE_BASVURUSU,
        call_reason=gko.OLAGANUSTU_NEDEN,
        gundem=gko.OLAGANUSTU_GUNDEM,
        member_application_count=basvuran,
        member_count_declared=uye,
        call_document=yazi,
        gerekce=gerekce,
    )


def _basvuru_yazisi(yon: str = DocumentDirection.GELEN) -> DocumentRecord:
    """Üyelerin yazılı başvurusunun gelen evrak kaydı (program yöneticisi; karşı taraf ve konu uydurma)."""
    if gelen_giden_evrak.evrak_defteri() is None:
        gelen_giden_evrak.evrak_defteri_olustur()
    return gelen_giden_evrak.evrak_kaydet(
        direction=yon,
        tarih=date(2026, 9, 25),
        counterparty="Uydurma başvuran üyeler",
        subject="Olağanüstü genel kurul başvurusu",
    ).kayit


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_basvuru_oran")
def test_yuzde_10_alti_basvuru_uyari() -> None:
    """md. 9/6 "birlik üyelerinin %10'unun yazılı başvurusu": 9 / 100 uyarı + gerekçe (U12: üye sayısı
    elle girilir); başvuruyu program yöneticisi kaydeder. Başvuru yazısının gelen evrak bağı girilmemişse
    akış eksiğidir (gerekçe istemez)."""
    with pytest.raises(GerekceGerekli):
        _uye_basvurusu(9, 100)
    sonuc = _uye_basvurusu(9, 100, gko.GEREKCE)
    (satir,) = _sapmalar("genel_kurul.olaganustu_basvuru_oran")
    assert satir.subject_id == str(sonuc.kurul.pk)
    assert (sonuc.kurul.member_application_count, sonuc.kurul.member_count_declared) == (9, 100)
    assert sonuc.kurul.call_document_id is None
    (eksik,) = _acik_satirlar(genel_kurul_servisi.BASVURU_YAZISI_AKISI)
    assert (eksik.kind, eksik.subject_id) == (ComplianceKind.EKSIK, str(sonuc.kurul.pk))


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_basvuru_oran")
def test_yuzde_10_basvuru_uyarisiz() -> None:
    """10 / 100 tam sınır: uyarı yok (ondalık karşılaştırma, `Decimal`; başvuru yazısı bağlı). Üye sayısı
    girilmemişse oran eksiktir: gerekçe istemez, tamamlanacaklara düşer."""
    gko.acik_donem()
    sonuc = _uye_basvurusu(10, 100, yazi=_basvuru_yazisi())
    assert sonuc.uyarilar == ()
    assert not ComplianceItem.objects.filter(rule_id="genel_kurul.olaganustu_basvuru_oran").exists()
    sonuc = _uye_basvurusu(12, None, yazi=_basvuru_yazisi())
    (satir,) = _acik_satirlar("genel_kurul.olaganustu_basvuru_oran")
    assert satir.kind == ComplianceKind.EKSIK
    assert [u["durum"] for u in sonuc.uyarilar] == ["eksik"]


@pytest.mark.django_db
def test_yuzde_10_basvurusu_gelen_evrak_kaydina_baglanir() -> None:
    """U12: üyelerin yazılı başvurusu gelen evrak olarak kaydedilir (`DocumentRecord(GELEN)`), kişi listesi
    tutulmaz; çağrı yazısı bağı (`call_document`) çağrıda girilmezse akış eksiğidir (gerekçe istemez; 4.
    adımda boş bırakılmıştı), sonra bağlanınca eksik kapanır ve kurulun özetinden düşer. Bağı başvuruyu
    kaydeden program yöneticisi girer; giden evrak ve başka genel kurulun kaydı bağlanmaz (başka dönemin
    kaydı: `test_baska_donemin_evrak_kaydi_cagri_yazisi_olarak_baglanmaz`), bağ bir kez girilir."""
    gko.acik_donem()
    sonuc = _uye_basvurusu(10, 100)
    kurul = sonuc.kurul
    assert [u["kural"] for u in sonuc.uyarilar] == [genel_kurul_servisi.BASVURU_YAZISI_AKISI]
    assert [s["kural"] for s in kurul.rule_warnings] == [genel_kurul_servisi.BASVURU_YAZISI_AKISI]
    (eksik,) = _acik_satirlar(genel_kurul_servisi.BASVURU_YAZISI_AKISI)
    assert (eksik.kind, eksik.justification_group_id) == (ComplianceKind.EKSIK, None)

    yazi = _basvuru_yazisi()
    giden = _basvuru_yazisi(DocumentDirection.GIDEN)
    with o.rol_olarak(AccountRole.SEKRETER), pytest.raises(RolYetkisiz):
        genel_kurul_servisi.cagri_yazisini_bagla(kurul, kayit=yazi)
    with o.rol_olarak(AccountRole.MUDUR), pytest.raises(RolYetkisiz):
        genel_kurul_servisi.cagri_yazisini_bagla(kurul, kayit=yazi)
    with pytest.raises(ValueError, match="gelen evrak"):
        genel_kurul_servisi.cagri_yazisini_bagla(kurul, kayit=giden)
    bagli = genel_kurul_servisi.cagri_yazisini_bagla(kurul, kayit=yazi).kurul
    assert bagli.call_document_id == yazi.pk
    assert bagli.rule_warnings == []
    assert not _acik_satirlar(genel_kurul_servisi.BASVURU_YAZISI_AKISI)
    assert ComplianceItem.objects.get(pk=eksik.pk).resolved_at is not None
    with pytest.raises(ValueError, match="bağlı"):
        genel_kurul_servisi.cagri_yazisini_bagla(kurul, kayit=_basvuru_yazisi())
    # Aynı başvuru yazısı başka genel kurulun çağrı yazısı olamaz (tek kaynak).
    with pytest.raises(ValueError, match="başka bir genel kurulun"):
        _uye_basvurusu(10, 100, yazi=yazi)
    # Başvurunun bağı yalnız üyelerin başvurusunda girilir.
    yk_kurulu = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    with pytest.raises(ValueError, match="yalnız üyelerin"):
        genel_kurul_servisi.cagri_yazisini_bagla(yk_kurulu, kayit=_basvuru_yazisi())


@pytest.mark.django_db
def test_iptal_edilen_14_5_cagrisinin_raporu_yeni_cagriya_baglanir() -> None:
    """md. 14/5 çağrısının iki bağı (S6 (ii)): iptal edilmiş genel kurulu gösteren rapor "başka genel
    kurulu çağırmış" sayılmaz; Denetleme Kurulu aynı raporla yeniden çağırır, ikinci rapor gerekmez.
    Raporun bağı izli güncellemeyle yeni kurula taşınır, iptal edilen kurulun bağı iz olarak kalır
    (kayıt silinmez). İptal edilmemiş başka kurulu gösteren rapor ise yine çağrı açmaz."""
    gko.acik_donem()
    rapor = _md6_raporu()
    ilk = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        _dk_cagrisi(ilk, rapor)
    _iptal(ilk)
    yeni = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        sonuc = _dk_cagrisi(yeni, rapor)
    assert (sonuc.kurul.status, sonuc.kurul.call_audit_report_id) == (
        AssemblyStatus.CAGRILDI,
        rapor.pk,
    )
    assert AuditReport.objects.get(pk=rapor.pk).escalated_assembly_id == yeni.pk
    iptal_edilen = GeneralAssembly.objects.get(pk=ilk.pk)
    assert (iptal_edilen.status, iptal_edilen.call_audit_report_id) == (
        AssemblyStatus.IPTAL,
        rapor.pk,
    )
    izler = AuditTrail.objects.filter(model="oab.AuditReport", object_id=str(rapor.pk))
    assert izler.filter(action=AuditAction.GUNCELLE).count() == 2
    ucuncu = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with (
        o.rol_olarak(AccountRole.DENETLEME_KURULU),
        pytest.raises(ValueError, match="başka bir olağanüstü genel kurulun"),
    ):
        _dk_cagrisi(ucuncu, rapor)


def _dk_yazisi(yon: str = DocumentDirection.GIDEN) -> DocumentRecord:
    """Denetleme Kurulunun çağrı yazısının evrak kaydı (program yöneticisi; metinler uydurma)."""
    if gelen_giden_evrak.evrak_defteri() is None:
        gelen_giden_evrak.evrak_defteri_olustur()
    return gelen_giden_evrak.evrak_kaydet(
        direction=yon,
        tarih=date(2026, 9, 30),
        counterparty="Uydurma birlik üyeleri",
        subject="Denetleme Kurulunun olağanüstü genel kurul çağrısı",
    ).kayit


@pytest.mark.django_db
def test_dk_cagrisinin_yazisi_evrak_kaydina_baglanir() -> None:
    """Tasarım §5.2.3 `call_document` ("müdür ya da DK yazısı, üye başvurusu") ve plan F2 §1.1-11:
    Denetleme Kurulunun çağrı yazısının evrak kaydı çağrıya bağlanır. Program DK'nin yazısını işlemez
    (DK evrak kaydı yazmaz, M10): kaydı yetkili rol girer, bağ çağrıda ya da sonra program yöneticisince
    girilir. Yazının yönü denetlenmez (kaynaklar söylemez). Bağ girilmemişse bilgi satırıdır (eksik
    değil); Denetleme Kurulu, sekreter ve müdür bağ giremez."""
    gko.acik_donem()
    yazi = _dk_yazisi()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        sonuc = _dk_cagrisi(kurul, _md6_raporu(), yazi=yazi)
    assert sonuc.kurul.call_document_id == yazi.pk
    assert genel_kurul_servisi.DK_YAZISI_BAGSIZ not in sonuc.bilgiler

    ikinci = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        ikinci = _dk_cagrisi(ikinci, _md6_raporu()).kurul
    sonra = _dk_yazisi(DocumentDirection.GELEN)
    for rol in (AccountRole.DENETLEME_KURULU, AccountRole.SEKRETER, AccountRole.MUDUR):
        with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
            genel_kurul_servisi.cagri_yazisini_bagla(ikinci, kayit=sonra)
    assert GeneralAssembly.objects.get(pk=ikinci.pk).call_document_id is None
    with pytest.raises(ValueError, match="başka bir genel kurulun"):
        genel_kurul_servisi.cagri_yazisini_bagla(ikinci, kayit=yazi)
    bagli = genel_kurul_servisi.cagri_yazisini_bagla(ikinci, kayit=sonra).kurul
    assert bagli.call_document_id == sonra.pk
    assert not ComplianceItem.objects.filter(
        rule_id=genel_kurul_servisi.BASVURU_YAZISI_AKISI
    ).exists()


@pytest.mark.django_db
def test_cagri_yazisi_bagi_mudurun_ve_yk_cagrisinda_girilmez() -> None:
    """Çağrı yazısı bağı yalnız üyelerin başvurusunda ve Denetleme Kurulunun çağrısında girilir: yönetim
    kurulunun çağrısında yazı yoktur, müdürün yazısını program işler (⁷). Verilen kayıt reddedilir;
    kurul planlı kalır, evrak kaydı ve iz yazılmaz (müdürün yazısı da işlenmez)."""
    gko.acik_donem()
    yazi = _basvuru_yazisi()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    once = (
        DocumentRecord.objects.count(),
        AuditTrail.objects.exclude(action=AuditAction.HESAP).count(),
    )
    for rol, cagiran in (
        (AccountRole.SEKRETER, AssemblyCaller.YONETIM_KURULU),
        (AccountRole.MUDUR, AssemblyCaller.OKUL_MUDURU),
    ):
        with o.rol_olarak(rol), pytest.raises(ValueError, match="yalnız üyelerin"):
            genel_kurul_servisi.cagir(
                kurul,
                called_by=cagiran,
                call_reason=gko.OLAGANUSTU_NEDEN,
                gundem=gko.OLAGANUSTU_GUNDEM,
                call_document=yazi,
            )
    assert (
        DocumentRecord.objects.count(),
        AuditTrail.objects.exclude(action=AuditAction.HESAP).count(),
    ) == once
    guncel = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (guncel.status, guncel.call_document_id) == (AssemblyStatus.PLANLANDI, None)


@pytest.mark.django_db
def test_baska_donemin_evrak_kaydi_cagri_yazisi_olarak_baglanmaz() -> None:
    """Çağrı yazısının evrak kaydı genel kurulun birlik dönemine ait olmalıdır (tek kaynak): başka dönemin
    gelen evrakı ne çağrıda ne sonra bağlanır; ret hiçbir şey yazmaz, akış eksiği açık kalır."""
    gko.acik_donem()
    baska = _basvuru_yazisi()
    DocumentRecord.objects.filter(pk=baska.pk).update(term=_baska_donem())
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    once = AuditTrail.objects.count()
    with pytest.raises(ValueError, match="birlik dönemine ait"):
        genel_kurul_servisi.cagir(
            kurul,
            called_by=AssemblyCaller.UYE_BASVURUSU,
            call_reason=gko.OLAGANUSTU_NEDEN,
            gundem=gko.OLAGANUSTU_GUNDEM,
            member_application_count=10,
            member_count_declared=100,
            call_document=baska,
        )
    assert AuditTrail.objects.count() == once
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.PLANLANDI
    cagrilan = _uye_basvurusu(10, 100).kurul
    once = AuditTrail.objects.count()
    with pytest.raises(ValueError, match="birlik dönemine ait"):
        genel_kurul_servisi.cagri_yazisini_bagla(cagrilan, kayit=baska)
    assert AuditTrail.objects.count() == once
    assert GeneralAssembly.objects.get(pk=cagrilan.pk).call_document_id is None
    (eksik,) = _acik_satirlar(genel_kurul_servisi.BASVURU_YAZISI_AKISI)
    assert eksik.subject_id == str(cagrilan.pk)


@pytest.mark.django_db
def test_iptal_edilen_basvurunun_yazisi_yeni_cagriya_baglanir_iptalde_bag_girilmez() -> None:
    """Bağ tutanak tamamlanana dek girilir: iptal edilmiş genel kurula bağ girilmez (durum kapısı).
    İptal edilmiş genel kurulun başvuru yazısı "başka genel kurulun yazısı" sayılmaz, yeni çağrıya
    bağlanır; iptal edilen kurulun bağı iz olarak kalır (kayıt silinmez)."""
    gko.acik_donem()
    yazi = _basvuru_yazisi()
    ilk = _uye_basvurusu(10, 100, yazi=yazi).kurul
    _iptal(ilk)
    yazisiz = _uye_basvurusu(10, 100).kurul
    _iptal(yazisiz)
    sonra = _basvuru_yazisi()
    once = AuditTrail.objects.count()
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul_servisi.cagri_yazisini_bagla(yazisiz, kayit=sonra)
    assert AuditTrail.objects.count() == once
    assert GeneralAssembly.objects.get(pk=yazisiz.pk).call_document_id is None
    yeni = _uye_basvurusu(10, 100, yazi=yazi).kurul
    assert yeni.call_document_id == yazi.pk
    assert GeneralAssembly.objects.get(pk=ilk.pk).call_document_id == yazi.pk


@pytest.mark.django_db
def test_basvuru_yazisi_eksigi_tutanak_tamamlanirken_gerekceyle_sapmaya_doner() -> None:
    """U12 ve O3: üyelerin başvurusuyla (10/100, yazısız) çağrılan, ilan edilen ve birinci toplantıda
    yapılan genel kurulda başvuru yazısının akış eksiği tutanak tamamlanırken hâlâ açıksa gerekçe ister
    (kural paketinde olmayan akış satırı da kapatıcı geçişe girer); gerekçesiz ret hiçbir şey yazmaz.
    Gerekçeyle satır sapmaya döner ve gerekçeye bağlanır, kurul `TUTANAK_TAMAM`; sonra bağ girilmez."""
    gko.acik_donem()
    kurul = _uye_basvurusu(10, 100).kurul
    genel_kurul_servisi.ilan_et(kurul, kanallar=gko.kanallar())
    genel_kurul_servisi.birinci_toplanti(kurul, katilim=gko.katilim(gko.KATILAN))
    (eksik,) = _acik_satirlar(genel_kurul_servisi.BASVURU_YAZISI_AKISI)
    once = (list(ComplianceItem.objects.order_by("pk").values()), AuditTrail.objects.count())
    with pytest.raises(GerekceGerekli) as hata:
        genel_kurul_servisi.tutanagi_tamamla(kurul)
    assert genel_kurul_servisi.BASVURU_YAZISI_EKSIK in str(hata.value.detail)
    assert (
        list(ComplianceItem.objects.order_by("pk").values()),
        AuditTrail.objects.count(),
    ) == once
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.YAPILDI
    sonuc = genel_kurul_servisi.tutanagi_tamamla(kurul, gerekce=gko.GEREKCE)
    assert sonuc.kurul.status == AssemblyStatus.TUTANAK_TAMAM
    eksik.refresh_from_db()
    assert (eksik.kind, eksik.resolved_at) == (ComplianceKind.SAPMA, None)
    assert eksik.justification_group is not None
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul_servisi.cagri_yazisini_bagla(kurul, kayit=_basvuru_yazisi())
    assert GeneralAssembly.objects.get(pk=kurul.pk).call_document_id is None


@pytest.mark.django_db
def test_olagan_planlamada_tohum_gundem_yazilir() -> None:
    """U19, U24: olağan genel kurulun gündemi planlamayla aynı işlemde OYS şablonundan yazılır (md.
    11/1-e yetkilendirme ve 11/1-f öneriler dâhil; saygı duruşu `DIGER`); her madde izlidir.
    Olağanüstüde tohum yoktur; planlama geri alınırsa tohum da yazılmaz."""
    gko.acik_donem()
    kurul = gko.planla()
    maddeler = list(AgendaItem.objects.filter(assembly=kurul).order_by("order"))
    assert [m.order for m in maddeler] == list(range(1, len(genel_kurul_servisi.TOHUM_GUNDEM) + 1))
    assert [(m.kind, m.title) for m in maddeler] == list(genel_kurul_servisi.TOHUM_GUNDEM)
    turler = [m.kind for m in maddeler]
    assert turler[0] == AgendaItemKind.ACILIS and turler[-1] == AgendaItemKind.KAPANIS
    assert {AgendaItemKind.YETKILENDIRME, AgendaItemKind.ONERILER} <= set(turler)
    assert (maddeler[2].kind, maddeler[2].title) == (
        AgendaItemKind.DIGER,
        "Saygı duruşu ve İstiklal Marşı",
    )
    assert AuditTrail.objects.filter(
        model="oab.AgendaItem", action=AuditAction.OLUSTUR
    ).count() == len(maddeler)

    olaganustu = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    assert not AgendaItem.objects.filter(assembly=olaganustu).exists()

    _iptal(kurul)
    oncesi = AgendaItem.objects.count()
    with pytest.raises(GerekceGerekli):  # 01.11: Ekim sonu uyarısı gerekçesiz
        gko.planla(birinci=gko.an(date(2026, 11, 1)))
    assert AgendaItem.objects.count() == oncesi


# ======================================================================= F2 5. adım: gündem, karar, divan
# md. 9/2, 9/4, 9/6, 10/1-c (tasarım §5.2.3, §7.1, §10.3; plan F2 §3.2, §7 U25, S2, S6 (iii)). Genel
# kurul birinci toplantıda 70 katılımla yapılır (yeter sayı 64). Adlar UYDURMADIR.


def _acik_kurallar(kural_id: str) -> list[ComplianceItem]:
    return list(ComplianceItem.objects.filter(rule_id=kural_id).order_by("pk"))


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.karar_cogunlugu")
def test_karar_katilanlarin_cogunluguyla() -> None:
    """md. 9/2 "kararlar katılanların çoğunluğu ile alınır" (kullanıcı kararı S2 (a)): kabul oyu
    katılan üye sayısının yarısından fazlaysa karar alınır; çekimser ve kullanılmayan oy kabul
    sayılmaz (30 kabul, 10 ret, 70 katılan: kabul retten çok olsa da karar alınmadı). Toplantıdan
    ayrılan olursa payda oylamada salonda bulunan sayıdır (50 kişide 30 kabul çoğunluktur). Sonuç
    hesaplanmış değerdir: uyum satırı açılmaz."""
    kurul = gko.yapilmis_olagan()
    yetki = gko.madde(kurul, AgendaItemKind.YETKILENDIRME)
    sonuc = genel_kurul_servisi.karar_sonucu_yaz(
        yetki, votes_for=36, votes_against=20, result_text="Uydurma: yetki verildi."
    )
    assert (sonuc.madde.result, sonuc.madde.votes_for, sonuc.madde.votes_against) == (
        AgendaResult.KABUL,
        36,
        20,
    )
    assert AgendaItem.objects.get(pk=yetki.pk).result_text == "Uydurma: yetki verildi."

    oneriler = gko.madde(kurul, AgendaItemKind.ONERILER)
    ret = genel_kurul_servisi.karar_sonucu_yaz(oneriler, votes_for=30, votes_against=10)
    assert (ret.madde.result, ret.madde.present_count) == (AgendaResult.RET, None)
    salonda = genel_kurul_servisi.karar_sonucu_yaz(
        oneriler, votes_for=30, votes_against=10, present_count=50
    )
    assert (salonda.madde.result, salonda.madde.present_count) == (AgendaResult.KABUL, 50)
    assert not ComplianceItem.objects.filter(rule_id="genel_kurul.karar_cogunlugu").exists()


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.karar_cogunlugu")
def test_oy_esitliginde_karar_alinmadi() -> None:
    """Kuralın karşılaştırması `buyuktur`: yarı yarıya oy çoğunluk değildir (35/70 karar alınmadı,
    ret); bir oy fazlası çoğunluktur (36/70 kabul). Saf hesap da aynı sonucu verir."""
    kurul = gko.yapilmis_olagan()
    oneriler = gko.madde(kurul, AgendaItemKind.ONERILER)
    sonuc = genel_kurul_servisi.karar_sonucu_yaz(oneriler, votes_for=35, votes_against=35)
    assert sonuc.madde.result == AgendaResult.RET
    sonuc = genel_kurul_servisi.karar_sonucu_yaz(oneriler, votes_for=36, votes_against=34)
    assert sonuc.madde.result == AgendaResult.KABUL
    karar = genel_kurul.karar_cogunlugu(35, 70, tarih=gko.BIRINCI_GUN)
    assert (karar["durum"], karar["atif"]) == ("sert", "md. 9/2")
    karar = genel_kurul.karar_cogunlugu(36, 70, tarih=gko.BIRINCI_GUN)
    assert karar["durum"] == "uygun"


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.karar_cogunlugu")
def test_oylarla_celisen_kabul_isareti_konamaz() -> None:
    """Kullanıcı kararı S6 (iii) (hesap bütünlüğü, sert): kararın sonucu oylardan hesaplanır;
    çoğunluk yokken "kabul" konamaz, çoğunluk varken "ret" de konamaz. Ret kaydı yazmaz; atıf
    görünür. Oylarla tutan sonuç kaydedilir."""
    kurul = gko.yapilmis_olagan()
    yetki = gko.madde(kurul, AgendaItemKind.YETKILENDIRME)
    with pytest.raises(KuralSert) as hata:
        genel_kurul_servisi.karar_sonucu_yaz(
            yetki, result=AgendaResult.KABUL, votes_for=20, votes_against=10
        )
    assert "md. 9/2" in str(hata.value.detail)
    with pytest.raises(KuralSert):
        genel_kurul_servisi.karar_sonucu_yaz(
            yetki, result=AgendaResult.RET, votes_for=50, votes_against=10
        )
    oncesi = AgendaItem.objects.get(pk=yetki.pk)
    assert (oncesi.result, oncesi.votes_for, oncesi.votes_against) == ("", None, None)
    assert not AuditTrail.objects.filter(
        model="oab.AgendaItem", object_id=str(yetki.pk), action=AuditAction.GUNCELLE
    ).exists()
    sonuc = genel_kurul_servisi.karar_sonucu_yaz(
        yetki, result=AgendaResult.KABUL, votes_for=50, votes_against=10
    )
    assert sonuc.madde.result == AgendaResult.KABUL


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.gundem_degisikligi")
def test_oylanmadan_gundem_eklemesi_gerekceyle_kaydedilir() -> None:
    """md. 9/4 "ekleme ve çıkarma yapılarak değiştirilmesinde oy çokluğu aranır" (uyarı; tasarım
    §6.4.1 "tutanak olduğu gibi girilir"): oylama satırı yoksa ya da kabul retten fazla değilse
    gerekçesiz geçmez, gerekçeyle kaydedilir (konusu madde). Gerekçesiz ret hiçbir şey yazmaz."""
    kurul = gko.yapilmis_olagan()
    oncesi = gko.gundem(kurul)
    with pytest.raises(GerekceGerekli) as hata:
        genel_kurul_servisi.gundeme_madde_ekle(kurul, title="Uydurma: okul bahçesi")
    assert "md. 9/4" in str(hata.value.detail)
    assert gko.gundem(kurul) == oncesi
    sonuc = genel_kurul_servisi.gundeme_madde_ekle(
        kurul, title="Uydurma: okul bahçesi", gerekce=gko.GEREKCE
    )
    madde = sonuc.madde
    assert (madde.added_by_vote, madde.change_votes_for, madde.order) == (True, None, 14)
    assert [u["kural"] for u in sonuc.uyarilar] == ["genel_kurul.gundem_degisikligi"]
    (satir,) = _acik_kurallar("genel_kurul.gundem_degisikligi")
    assert (satir.kind, satir.subject_type, satir.subject_id) == (
        ComplianceKind.SAPMA,
        "oab.AgendaItem",
        str(madde.pk),
    )
    # Oy çokluğu yoksa (10 kabul, 20 ret) da uyarıdır; çıkarmada da aynı kural.
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.gundeme_madde_ekle(
            kurul, title="Uydurma: kantin", change_votes_for=10, change_votes_against=20
        )
    dilek = gko.madde(kurul, AgendaItemKind.DILEK)
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.gundemden_madde_cikar(dilek)
    genel_kurul_servisi.gundemden_madde_cikar(dilek, gerekce=gko.GEREKCE)
    assert len(_sapmalar("genel_kurul.gundem_degisikligi")) == 2
    # Eşit oy (20 kabul, 20 ret) oy çokluğu değildir (S2: kabul > ret): ekleme de çıkarma da
    # gerekçesiz geçmez ve gerekçesiz ret hiçbir şey yazmaz; bir oy fazlası (21/20) uyarısızdır.
    oncesi = gko.gundem(kurul)
    oneriler = gko.madde(kurul, AgendaItemKind.ONERILER)
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.gundeme_madde_ekle(
            kurul, title="Uydurma: spor salonu", change_votes_for=20, change_votes_against=20
        )
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.gundemden_madde_cikar(
            oneriler, change_votes_for=20, change_votes_against=20
        )
    assert gko.gundem(kurul) == oncesi
    assert not AgendaItem.objects.get(pk=oneriler.pk).removed_by_vote
    assert len(_sapmalar("genel_kurul.gundem_degisikligi")) == 2
    eklenen = genel_kurul_servisi.gundeme_madde_ekle(
        kurul, title="Uydurma: spor salonu", change_votes_for=21, change_votes_against=20
    )
    cikan = genel_kurul_servisi.gundemden_madde_cikar(
        oneriler, change_votes_for=21, change_votes_against=20
    )
    assert (eklenen.uyarilar, cikan.uyarilar) == ((), ())
    assert len(_sapmalar("genel_kurul.gundem_degisikligi")) == 2


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.gundem_degisikligi")
def test_oy_coklugu_ile_ekleme_uyarisiz() -> None:
    """Kabul oyu retten fazlaysa ekleme ve çıkarma uyarısızdır (S2: md. 9/4'te kabul > ret). Araya
    eklenen madde sonrakileri kaydırır; çıkarılan madde silinmez (`removed_by_vote`), yerini korur."""
    kurul = gko.yapilmis_olagan()
    sonuc = genel_kurul_servisi.gundeme_madde_ekle(
        kurul,
        title="Uydurma: okul bahçesinin düzenlenmesi",
        sira=12,
        change_votes_for=40,
        change_votes_against=10,
    )
    assert sonuc.uyarilar == ()
    sira = gko.gundem(kurul)
    assert [s for s, _ in sira] == list(range(1, 15))
    assert sira[11] == (12, "Uydurma: okul bahçesinin düzenlenmesi")
    assert sira[12][1] == "Dilek ve temenniler" and sira[13][1] == "Kapanış"

    oneriler = gko.madde(kurul, AgendaItemKind.ONERILER)
    cikan = genel_kurul_servisi.gundemden_madde_cikar(
        oneriler, change_votes_for=40, change_votes_against=5
    )
    assert cikan.uyarilar == ()
    assert AgendaItem.objects.filter(pk=oneriler.pk).exists()
    sonra = AgendaItem.objects.get(pk=oneriler.pk)
    assert (sonra.removed_by_vote, sonra.change_votes_for, sonra.change_votes_against) == (
        True,
        40,
        5,
    )
    assert not ComplianceItem.objects.filter(rule_id="genel_kurul.gundem_degisikligi").exists()


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.gundem_degisikligi")
def test_sira_degisikligi_uyari_uretmez() -> None:
    """Sıra değişikliği md. 9/4'ün ekleme ve çıkarması değildir (MA-16): uyarı ve uyum satırı yok,
    bilgi satırı (md. 9/4 birinci cümle). (Genel kurul, sıra) tekil kısıtı ertelenmediği için yazım
    geçici sırayla iki adımdadır; her madde tek iz satırıyla izlenir. İlandan önce de değişir."""
    kurul = gko.yapilmis_olagan()
    maddeler = list(AgendaItem.objects.filter(assembly=kurul).order_by("order"))
    yeni = [maddeler[0], maddeler[2], maddeler[1], *maddeler[3:]]
    izler = AuditTrail.objects.filter(model="oab.AgendaItem").count()
    sonuc = genel_kurul_servisi.gundem_sirasini_degistir(kurul, sira=[m.pk for m in yeni])
    assert sonuc.uyarilar == ()
    assert sonuc.bilgiler == (genel_kurul_servisi.SIRA_BILGISI,)
    assert gko.gundem(kurul)[1:3] == [
        (2, "Saygı duruşu ve İstiklal Marşı"),
        (3, "Divan başkanı ve kâtip seçimi"),
    ]
    assert AuditTrail.objects.filter(model="oab.AgendaItem").count() == izler + 2
    assert not ComplianceItem.objects.filter(rule_id="genel_kurul.gundem_degisikligi").exists()
    with pytest.raises(ValueError, match="birer kez"):
        genel_kurul_servisi.gundem_sirasini_degistir(kurul, sira=[m.pk for m in yeni[1:]])

    # İlandan önce de (çağrılmış olağanüstü genel kurul): gündem çağrıda girildi, sırası değişir.
    olaganustu = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    ilk, ikinci = AgendaItem.objects.filter(assembly=olaganustu).order_by("order")
    genel_kurul_servisi.gundem_sirasini_degistir(olaganustu, sira=[ikinci.pk, ilk.pk])
    assert [baslik for _, baslik in gko.gundem(olaganustu)] == [ikinci.title, ilk.title]
    # İlan edilmiş ama toplanmamış genel kurulun ilan edilen gündemi değişmez.
    genel_kurul_servisi.ilan_et(olaganustu, kanallar=gko.kanallar())
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul_servisi.gundem_sirasini_degistir(olaganustu, sira=[ilk.pk, ikinci.pk])


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_gundeme_baglilik")
def test_olaganustu_gundem_disi_madde_uyari() -> None:
    """md. 9/6 "gündeme bağlılık ilkesi geçerlidir": olağanüstü genel kurulda toplantıda eklenen
    madde çağrı gündemi dışındadır; oy çokluğuyla eklense de gerekçesiz geçmez (B-13), ret yazmaz
    (olağan genel kurulda aynı ekleme uyarısızdır: `test_oy_coklugu_ile_ekleme_uyarisiz`)."""
    kurul = gko.yapilmis_olaganustu()
    oncesi = gko.gundem(kurul)
    with pytest.raises(GerekceGerekli) as hata:
        genel_kurul_servisi.gundeme_madde_ekle(
            kurul, title="Uydurma: bütçe", change_votes_for=40, change_votes_against=10
        )
    assert "md. 9/6" in str(hata.value.detail)
    assert gko.gundem(kurul) == oncesi
    assert not ComplianceItem.objects.filter(
        rule_id="genel_kurul.olaganustu_gundeme_baglilik"
    ).exists()


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_gundeme_baglilik")
def test_olaganustu_gundem_disi_madde_gerekceyle_kaydedilir() -> None:
    """B-13: sert değil, uyarı + gerekçe: gerekçeyle madde eklenir, `SAPMA` satırının konusu
    maddedir; oy çokluğu olduğu için gündem değişikliği uyarısı yoktur."""
    kurul = gko.yapilmis_olaganustu()
    sonuc = genel_kurul_servisi.gundeme_madde_ekle(
        kurul,
        title="Uydurma: bütçe",
        change_votes_for=40,
        change_votes_against=10,
        gerekce=gko.GEREKCE,
    )
    assert [u["kural"] for u in sonuc.uyarilar] == ["genel_kurul.olaganustu_gundeme_baglilik"]
    (satir,) = _sapmalar("genel_kurul.olaganustu_gundeme_baglilik")
    assert (satir.subject_type, satir.subject_id) == ("oab.AgendaItem", str(sonuc.madde.pk))
    assert not ComplianceItem.objects.filter(rule_id="genel_kurul.gundem_degisikligi").exists()
    assert sonuc.madde.added_by_vote is True


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.divan_uye_turleri")
def test_divana_veli_olmayan_ogretmen_secilirse_uyari() -> None:
    """md. 10/1-c "veliler/on sekiz yaşını doldurmuş kursiyerler arasından": veli olmayan öğretmen
    divana gerekçesiz seçilmez (uyarı; konu üyelik); ret hiçbir divan kaydı yazmaz. Gerekçeyle
    kaydedilir, uyarı üyeliğin özetinde durur."""
    kurul = gko.yapilmis_olagan()
    ogretmen = o.ogretmen()
    veli = o.kisi()
    with pytest.raises(GerekceGerekli) as hata:
        genel_kurul_servisi.divan_sec(kurul, baskan=ogretmen, katip=veli)
    assert "md. 10/1-c" in str(hata.value.detail)
    assert not OrganMembership.objects.filter(organ=OrganType.DIVAN).exists()
    sonuc = genel_kurul_servisi.divan_sec(kurul, baskan=ogretmen, katip=veli, gerekce=gko.GEREKCE)
    assert [u["kural"] for u in sonuc.uyarilar] == ["genel_kurul.divan_uye_turleri"]
    baskan, katip = genel_kurul_servisi.kurulun_divani(kurul)
    assert (baskan.person_id, baskan.role, katip.person_id, katip.role) == (
        ogretmen.pk,
        MembershipRole.BASKAN,
        veli.pk,
        MembershipRole.KATIP,
    )
    assert [s["kural"] for s in baskan.rule_warnings] == ["genel_kurul.divan_uye_turleri"]
    assert katip.rule_warnings == []
    (satir,) = _sapmalar("genel_kurul.divan_uye_turleri")
    assert (satir.subject_type, satir.subject_id) == ("oab.OrganMembership", str(baskan.pk))


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.divan_uye_turleri")
def test_divana_veli_olan_ogretmen_uyarisiz() -> None:
    """Uygunluk kişinin işine değil veli olup olmadığına bakar (MA-11): veli olan öğretmen uygundur;
    18 yaşını doldurduğu beyan edilmiş kursiyer de. Divan genel kurulun kendi dönemine (kapanacak
    dönem), seçilmiş, aday kaydı olmadan, genel kurulun yapıldığı günle yazılır (U25)."""
    kurul = gko.yapilmis_olagan()
    ogretmen = o.ogretmen(is_parent=True)
    kursiyer = o.kisi(kind=PersonKind.KURSIYER, is_parent=False, adult_declared=True)
    sonuc = genel_kurul_servisi.divan_sec(kurul, baskan=ogretmen, katip=kursiyer)
    assert sonuc.uyarilar == ()
    divan = genel_kurul_servisi.kurulun_divani(kurul)
    assert [(u.term_id, u.assembly_id, u.status, u.start_date) for u in divan] == [
        (kurul.term_id, kurul.pk, MembershipStatus.SECILDI, gko.BIRINCI_GUN)
    ] * 2
    assert not ComplianceItem.objects.filter(rule_id="genel_kurul.divan_uye_turleri").exists()


# ======================================================================= F2 6. adım: seçim, ibra, tutanak
# md. 10/1-d, 11/1-a, b, c, ç, 12/4, 13/8, 14/3 (tasarım §7.1; plan F2 §7 U26, U27, U32, S4, S6 (i),
# S10). Adlar UYDURMADIR.


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.secim_bicimi")
def test_secim_liste_ve_acik_oy() -> None:
    """md. 10/1-d "asıl ve yedek olarak liste hâlinde oylanarak", 11/1-a, b "açık oylamayla": liste
    hâlinde ve açık oyla yapılan seçim uyarısızdır (gözlenen küme değeri kapsar, sıra önemsiz). Gizli
    oyla kaydedilen seçim gerekçesiz geçmez (uyarı; ret hiçbir şey yazmaz, aday aday kalır);
    gerekçeyle sapma olarak kaydedilir, konu seçim maddesidir. Biçim girilmezse eksiktir."""
    kurul = gko.yapilmis_olagan()
    dk = [gko.aday(kurul, organ="DK")]
    gko.secim(kurul, AgendaItemKind.SECIM_DK, dk)
    assert not ComplianceItem.objects.filter(rule_id="genel_kurul.secim_bicimi").exists()

    yk = [gko.aday(kurul) for _ in range(2)]
    with pytest.raises(GerekceGerekli) as hata:
        gko.secim(kurul, AgendaItemKind.SECIM_YK, yk, acik_oy=False)
    assert "md. 10/1-d" in str(hata.value.detail)
    assert {OrganMembership.objects.get(pk=u.pk).status for u in yk} == {MembershipStatus.ADAY}
    assert gko.madde(kurul, AgendaItemKind.SECIM_YK).result == ""
    sonuc = gko.secim(kurul, AgendaItemKind.SECIM_YK, yk, acik_oy=False, gerekce=gko.GEREKCE)
    assert "genel_kurul.secim_bicimi" in [u["kural"] for u in sonuc.uyarilar]
    (satir,) = _sapmalar("genel_kurul.secim_bicimi")
    assert (satir.subject_type, satir.subject_id) == ("oab.AgendaItem", str(sonuc.madde.pk))
    assert sonuc.madde.result == AgendaResult.GORUSULDU

    tarih = gko.BIRINCI_GUN
    assert denetle("genel_kurul.secim_bicimi", ["ACIK_OY", "LISTE"], tarih=tarih)["durum"] == (
        "uygun"
    )
    assert denetle("genel_kurul.secim_bicimi", ["LISTE"], tarih=tarih)["durum"] == "uyari"
    assert denetle("genel_kurul.secim_bicimi", tarih=tarih)["durum"] == "eksik"


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.secim_bicimi")
def test_secim_bicimi_girilmezse_eksik_tutanakta_gerekce_ister() -> None:
    """Seçimin biçimi girilmediyse eksiktir (tamamlanacak; gerekçe istemez); tutanak tamamlanırken
    hâlâ eksikse sapmaya döner ve gerekçe ister (O3)."""
    kurul = gko.yapilmis_olagan()
    sonuc = gko.secim(kurul, AgendaItemKind.SECIM_DK, [gko.aday(kurul, organ="DK")], liste=None)
    (satir,) = _acik_satirlar("genel_kurul.secim_bicimi")
    assert (satir.kind, satir.subject_id) == (ComplianceKind.EKSIK, str(sonuc.madde.pk))
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.tutanagi_tamamla(kurul)
    genel_kurul_servisi.tutanagi_tamamla(kurul, gerekce=gko.GEREKCE)
    satir.refresh_from_db()
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.SAPMA, None)


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.ilan_kanallari")
def test_tutanak_tamamda_eksik_kanit_gerekce_ister() -> None:
    """İlanın kanallarından biri girilmediyse ilan kaydında eksiktir (konusu `Announcement`, 4. adım);
    tutanak tamamlanırken hâlâ eksikse sapmaya döner ve gerekçe ister (plan F2 §3.2, O3). Gerekçesiz
    ret hiçbir şey yazmaz: kurul yapıldı durumunda, satır eksik kalır. Gerekçeyle satır sapma olur,
    kurul `TUTANAK_TAMAM`; sonra kanıt girilemez."""
    gko.acik_donem()
    kurul = gko.olagan_cagir(gko.planla())
    iki_kanal = genel_kurul_servisi.IlanKanallari(
        distributed_written_on=gko.ILAN_GUNU, posted_board_on=gko.ILAN_GUNU
    )
    genel_kurul_servisi.ilan_et(kurul, kanallar=iki_kanal)
    genel_kurul_servisi.birinci_toplanti(kurul, katilim=gko.katilim(gko.KATILAN))
    (satir,) = _acik_satirlar("genel_kurul.ilan_kanallari")
    assert (satir.kind, satir.subject_type) == (ComplianceKind.EKSIK, "oab.Announcement")
    with pytest.raises(GerekceGerekli) as hata:
        genel_kurul_servisi.tutanagi_tamamla(kurul)
    assert "eksik bilgi" in str(hata.value.detail)
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.YAPILDI
    satir.refresh_from_db()
    assert satir.kind == ComplianceKind.EKSIK
    sonuc = genel_kurul_servisi.tutanagi_tamamla(kurul, gerekce=gko.GEREKCE)
    assert sonuc.kurul.status == AssemblyStatus.TUTANAK_TAMAM
    satir.refresh_from_db()
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.SAPMA, None)
    assert satir.justification_group is not None
    (duyuru,) = genel_kurul_servisi.kurulun_duyurulari(kurul)
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul_servisi.ilan_kanitlarini_yaz(duyuru, kanallar=gko.kanallar())


@pytest.mark.django_db
def test_dk_veli_adayina_baskanlik_sayaci_uygulanmaz() -> None:
    """Seçimde denetlenen tek seçilme sınırı md. 12/4'tür (U26; plan F2 §1.1-8): Denetleme Kurulunun
    veli koltuğunun seçilme sınırı yoktur, başkanlık sınırı (md. 14/3) görev bölümünde koşar.
    Başkanlığı sınırı aşmış kişi Denetleme Kuruluna seçilir, sayaç satırı açılmaz."""
    kurul = gko.yapilmis_olagan()
    kisi = o.kisi(external_dk_chair_terms=5)
    sonuc = gko.secim(kurul, AgendaItemKind.SECIM_DK, [gko.aday(kurul, organ="DK", kisi=kisi)])
    (secilen,) = sonuc.secilenler
    assert secilen.status == MembershipStatus.SECILDI
    assert not ComplianceItem.objects.filter(
        rule_id="denetleme_kurulu.baskan_secilme_siniri"
    ).exists()
    assert sonuc.uyarilar == ()


@pytest.mark.django_db
@pytest.mark.kural_davranis("yonetim_kurulu.secilme_siniri")
def test_secimde_yk_secilme_siniri_uyari_gerekce() -> None:
    """md. 12/4 "en fazla dört defa seçilebilir": dört kez seçilmiş kişinin yönetim kuruluna seçimi
    uyarı + gerekçedir (ret hiçbir kaydı seçmez); gerekçeyle kaydedilir. Beyanı bilinmeyen kişide
    sayaç eksiktir (gerekçe istemez)."""
    kurul = gko.yapilmis_olagan()
    dorduncu = gko.aday(kurul, kisi=o.kisi(external_yk_terms=4))
    bilinmeyen = gko.aday(kurul)
    with pytest.raises(GerekceGerekli) as hata:
        gko.secim(kurul, AgendaItemKind.SECIM_YK, [dorduncu, bilinmeyen])
    assert "md. 12/4" in str(hata.value.detail)
    assert not OrganMembership.objects.filter(status=MembershipStatus.SECILDI).exists()
    gko.secim(kurul, AgendaItemKind.SECIM_YK, [dorduncu, bilinmeyen], gerekce=gko.GEREKCE)
    satirlar = {
        s.subject_id: s.kind
        for s in ComplianceItem.objects.filter(rule_id="yonetim_kurulu.secilme_siniri")
    }
    assert satirlar == {
        str(dorduncu.pk): ComplianceKind.SAPMA,
        str(bilinmeyen.pk): ComplianceKind.EKSIK,
    }


@pytest.mark.django_db
def test_secilen_yalniz_ayni_genel_kurulun_adayindan() -> None:
    """Kullanıcı kararı S6 (i) (hesap bütünlüğü, sert): seçilen yalnız aynı genel kurulun aynı kurula
    aday kaydından olur. Başka genel kurulun adayı, öteki kurulun adayı ve zaten seçilmiş kayıt
    reddedilir; ret hiçbir şey yazmaz."""
    kurul = gko.yapilmis_olagan()
    olaganustu = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    baska_kurulun = gko.aday(olaganustu)
    dk_adayi = gko.aday(kurul, organ="DK")
    for yanlis in (baska_kurulun, dk_adayi):
        with pytest.raises(ValueError, match="tek kaynak"):
            gko.secim(kurul, AgendaItemKind.SECIM_YK, [gko.aday(kurul), yanlis])
    assert not OrganMembership.objects.filter(status=MembershipStatus.SECILDI).exists()
    gko.secim(kurul, AgendaItemKind.SECIM_DK, [dk_adayi])
    with pytest.raises(ValueError, match="tek kaynak"):
        gko.secim(kurul, AgendaItemKind.SECIM_YK, [dk_adayi])

    # Aynı kurulun aynı kuruldaki seçilmiş kaydı ikinci bir seçim maddesinde yeniden seçilmez (durum).
    secilen = gko.aday(kurul)
    gko.secim(kurul, AgendaItemKind.SECIM_YK, [secilen])
    ikinci_secim = genel_kurul_servisi.gundeme_madde_ekle(
        kurul,
        title="Yönetim kurulu ek seçimi",
        kind=AgendaItemKind.SECIM_YK,
        change_votes_for=50,
        change_votes_against=10,
    ).madde
    with pytest.raises(ValueError, match="tek kaynak"):
        genel_kurul_servisi.secim_sonucu_yaz(
            ikinci_secim,
            adaylar=[genel_kurul_servisi.AdayOyu(uyelik=secilen, votes=40, secildi=True)],
            liste=True,
            acik_oy=True,
        )
    assert AgendaItem.objects.get(pk=ikinci_secim.pk).result == ""
    assert OrganMembership.objects.get(pk=secilen.pk).status == MembershipStatus.SECILDI


@pytest.mark.django_db
def test_olaganustu_genel_kurul_dk_secimi_yapmaz() -> None:
    """Kullanıcı kararı S10 (a): olağanüstü genel kurul Denetleme Kuruluna seçim yapmaz (md. 13/8
    yalnız yönetim kurulunu sayar): aday kaydı açılmaz, gündeme eklenmiş seçim maddesinin sonucu
    yazılmaz. Görevdeki Denetleme Kurulu veli üyeliği sürer."""
    donem = gko.acik_donem()
    veli = o.secilmis(donem, organ="DK", seat_group="VELI")
    kurul = gko.yapilmis_olaganustu(donem_ac=False)
    with pytest.raises(ValueError, match="Denetleme Kuruluna seçim yapmaz"):
        gko.aday(kurul, organ="DK")
    madde = genel_kurul_servisi.gundeme_madde_ekle(
        kurul,
        title="Denetleme Kurulu seçimi",
        kind=AgendaItemKind.SECIM_DK,
        change_votes_for=50,
        change_votes_against=10,
        gerekce=gko.GEREKCE,
    ).madde
    with pytest.raises(ValueError, match="Denetleme Kuruluna seçim yapmaz"):
        genel_kurul_servisi.secim_sonucu_yaz(madde, adaylar=[], liste=True, acik_oy=True)
    assert OrganMembership.objects.get(pk=veli.pk).status == MembershipStatus.SECILDI


@pytest.mark.django_db
def test_olaganustu_secimde_eski_yk_uyelikleri_duser() -> None:
    """U27 (md. 13/8): olağanüstü genel kurul yönetim kurulunu seçince görevdeki eski üyelikler (asıl ve
    yedek) seçilenlerin kaydından önce `DUSTU (OLAGANUSTU_GK_SECIMI)` olur, bitişleri genel kurulun
    günüdür; eski üye yeniden seçilebilir (düşmüş kayıt koltuk değildir). Dönem değişmez; Denetleme
    Kurulunun veli üyeliği sürer (S10)."""
    donem = gko.acik_donem()
    eski = o.yk_kurulu(donem, asil=5, yedek=1)
    dk_velisi = o.secilmis(donem, organ="DK", seat_group="VELI")
    kurul = gko.yapilmis_olaganustu(donem_ac=False)
    yeniden = gko.aday(kurul, kisi=eski[0].person)
    yeni = [yeniden, *(gko.aday(kurul) for _ in range(4))]
    sonuc = gko.secim(kurul, AgendaItemKind.SECIM_YK, yeni)
    assert {u.pk for u in sonuc.dusenler} == {u.pk for u in eski}
    for uyelik in OrganMembership.objects.filter(pk__in=[u.pk for u in eski]):
        assert (uyelik.status, uyelik.drop_kind, uyelik.end_date) == (
            MembershipStatus.DUSTU,
            "OLAGANUSTU_GK_SECIMI",
            gko.BIRINCI_GUN,
        )
    assert [u.status for u in sonuc.secilenler] == [MembershipStatus.SECILDI] * 5
    assert {u.term_id for u in sonuc.secilenler} == {donem.pk}
    assert OrganMembership.objects.get(pk=dk_velisi.pk).status == MembershipStatus.SECILDI
    assert OabTerm.objects.get(pk=donem.pk).status == TermStatus.ACIK


@pytest.mark.django_db
def test_ibra_edilmedi_yan_akisi_takvime_girer() -> None:
    """md. 11/1-c, ç; kullanıcı kararı S4 (a): yönetim kurulunun hesapları ibra edilmezse ibra
    edilmeyen muhasebe evrakı tutanağa yazılır (şifreli) ve tutanak tamamlanınca il/ilçe MEM bildirimi
    takvim satırı olur (atıflı ileti, son gün genel kurulun günü). Evrak listesi yalnız ibra
    edilmediğinde yazılır. Denetleme Kurulunun ibra edilmemesi yan akış açmaz."""
    kurul = gko.yapilmis_olagan()
    ibra = gko.madde(kurul, AgendaItemKind.IBRA)
    with pytest.raises(ValueError, match="yalnız yönetim kurulunun hesapları"):
        genel_kurul_servisi.ibra_yaz(
            ibra,
            yk=gko.IBRA_EDILDI,
            dk=gko.IBRA_EDILDI,
            unaudited_documents_note="Uydurma evrak listesi.",
        )
    sonuc = genel_kurul_servisi.ibra_yaz(
        ibra,
        yk=gko.IBRA_EDILMEDI,
        dk=gko.IBRA_EDILDI,
        unaudited_documents_note="Uydurma: 3 harcama belgesi.",
    )
    assert "md. 11/1-ç" in sonuc.bilgiler[0]
    assert (sonuc.kurul.discharge_yk, sonuc.kurul.discharge_dk) == ("EDILMEDI", "EDILDI")
    assert AssemblyMinutes.objects.get(assembly=kurul).unaudited_documents_note == (
        "Uydurma: 3 harcama belgesi."
    )
    assert gko.madde(kurul, AgendaItemKind.IBRA).result == AgendaResult.GORUSULDU
    genel_kurul_servisi.tutanagi_tamamla(kurul)
    (takvim,) = ComplianceItem.objects.filter(kind=ComplianceKind.TAKVIM)
    assert (takvim.obligation, takvim.due_date, takvim.term_id) == (
        "IBRA_EDILMEDI_BILDIRIMI",
        gko.BIRINCI_GUN,
        kurul.term_id,
    )
    assert "md. 11/1-ç" in takvim.message and takvim.rule_id == ""

    olaganustu = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    genel_kurul_servisi.ilan_et(olaganustu, kanallar=gko.kanallar())
    yalniz_dk = genel_kurul_servisi.birinci_toplanti(
        olaganustu, katilim=gko.katilim(gko.KATILAN)
    ).kurul
    ibra2 = genel_kurul_servisi.gundeme_madde_ekle(
        yalniz_dk,
        title="Denetleme Kurulunun ibrası",
        kind=AgendaItemKind.IBRA,
        change_votes_for=50,
        change_votes_against=10,
        gerekce=gko.GEREKCE,
    ).madde
    sonuc = genel_kurul_servisi.ibra_yaz(ibra2, yk=None, dk=gko.IBRA_EDILMEDI)
    assert (sonuc.kurul.discharge_yk, sonuc.kurul.discharge_dk) == ("GORUSULMEDI", "EDILMEDI")
    assert sonuc.bilgiler == ()
    genel_kurul_servisi.tutanagi_tamamla(yalniz_dk)
    assert ComplianceItem.objects.filter(kind=ComplianceKind.TAKVIM).count() == 1


# ======================================================================= F2 6. adım: ibra oylaması
# md. 11/1-c, 9/2; kullanıcı kararı S2 (a), S6 (iii); tasarım §9.6 E10 "YK ve DK ibrası ayrı oylama
# satırı". Adlar UYDURMADIR.


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.karar_cogunlugu")
def test_ibra_sonucu_oylardan_hesaplanir() -> None:
    """İbra genel kurulun kararıdır (md. 11/1-c), sonucu oylardan hesaplanır (md. 9/2 "katılanların
    çoğunluğu"; S6 (iii), sert — hesap bütünlüğü): kabul oyu paydanın yarısından fazlaysa ibra edildi,
    eşitlikte edilmedi; payda oylamada salonda bulunan, girilmemişse katılım (S2). Yönetim kurulu ve
    Denetleme Kurulu ayrı oylanır, oyları ayrı yazılır. Oylarla çelişen sonuç, oysuz "ibra edildi",
    oylu "görüşülmedi" ve paydayı aşan oylar reddedilir; ret hiçbir şey yazmaz."""
    kurul = gko.yapilmis_olagan()  # katılım 70
    ibra = gko.madde(kurul, AgendaItemKind.IBRA)
    with pytest.raises(ValueError, match="oylardan hesaplanır"):
        genel_kurul_servisi.ibra_yaz(ibra, yk=None, dk=None, discharge_yk="EDILDI")
    with pytest.raises(KuralSert) as hata:
        genel_kurul_servisi.ibra_yaz(
            ibra,
            yk=genel_kurul_servisi.IbraOylamasi(votes_for=35, votes_against=35),
            dk=None,
            discharge_yk="EDILDI",
        )
    assert "md. 9/2" in str(hata.value.detail)
    with pytest.raises(ValueError, match="Görüşülmedi sonucunda"):
        genel_kurul_servisi.ibra_yaz(ibra, yk=gko.IBRA_EDILDI, dk=None, discharge_yk="GORUSULMEDI")
    with pytest.raises(ValueError, match="salonda bulunan"):
        genel_kurul_servisi.ibra_yaz(
            ibra,
            yk=genel_kurul_servisi.IbraOylamasi(votes_for=40, votes_against=1, present_count=71),
            dk=None,
        )
    with pytest.raises(ValueError, match="aşamaz"):
        genel_kurul_servisi.ibra_yaz(
            ibra,
            yk=None,
            dk=genel_kurul_servisi.IbraOylamasi(votes_for=30, votes_against=31, present_count=60),
        )
    guncel = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (guncel.discharge_yk, guncel.discharge_dk) == ("", "")
    assert gko.madde(kurul, AgendaItemKind.IBRA).result == ""

    sonuc = genel_kurul_servisi.ibra_yaz(
        ibra,
        yk=genel_kurul_servisi.IbraOylamasi(votes_for=36, votes_against=30),
        dk=genel_kurul_servisi.IbraOylamasi(votes_for=30, votes_against=10, present_count=60),
        discharge_dk="EDILMEDI",
    )
    yazilan = sonuc.kurul
    assert (
        yazilan.discharge_yk,
        yazilan.discharge_yk_votes_for,
        yazilan.discharge_yk_votes_against,
        yazilan.discharge_yk_present_count,
    ) == ("EDILDI", 36, 30, None)
    assert (
        yazilan.discharge_dk,
        yazilan.discharge_dk_votes_for,
        yazilan.discharge_dk_votes_against,
        yazilan.discharge_dk_present_count,
    ) == ("EDILMEDI", 30, 10, 60)
    assert gko.madde(kurul, AgendaItemKind.IBRA).result == AgendaResult.GORUSULDU


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.karar_cogunlugu")
def test_katilim_duzeltmesi_ibra_sonucunu_yeniden_hesaplar() -> None:
    """S6 (iii): salondaki sayısı girilmemiş ibranın paydası katılımdır; katılım düzeltilince sonuç
    yeniden hesaplanır (akış satırı gerekçe ister; bilgi satırı). Tutanak tamamlandıktan sonra yönetim
    kurulu "ibra edilmedi"ye dönerse il/ilçe MEM bildirimi takvime girer (md. 11/1-ç, S4 (a)). Katılım
    ibra oylarının toplamının altına düzeltilemez (sert)."""
    kurul = gko.yapilmis_olagan()  # katılım 70: 36 > 35
    genel_kurul_servisi.ibra_yaz(
        gko.madde(kurul, AgendaItemKind.IBRA),
        yk=genel_kurul_servisi.IbraOylamasi(votes_for=36, votes_against=30),
        dk=gko.IBRA_EDILDI,
    )
    genel_kurul_servisi.tutanagi_tamamla(kurul)
    assert not ComplianceItem.objects.filter(kind=ComplianceKind.TAKVIM).exists()
    with pytest.raises(ValueError, match="ibraya girilmiş oyların"):
        genel_kurul_servisi.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.BIRINCI,
            degerler={"first_attendee_count": 65},
            justification="Uydurma: sayım hatası.",
            gerekce=gko.GEREKCE,
        )
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.BIRINCI,
            degerler={"first_attendee_count": 72},
            justification="Uydurma: sayım hatası.",
        )
    assert GeneralAssembly.objects.get(pk=kurul.pk).discharge_yk == "EDILDI"
    sonuc = genel_kurul_servisi.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        degerler={"first_attendee_count": 72},
        justification="Uydurma: sayım hatası.",
        gerekce=gko.GEREKCE,
    )
    guncel = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (guncel.discharge_yk, guncel.discharge_dk) == ("EDILMEDI", "EDILDI")
    assert any("İbra (yönetim kurulu)" in b for b in sonuc.bilgiler)
    assert genel_kurul_servisi.IBRA_YAN_AKISI_GOZDEN_GECIR in sonuc.bilgiler
    (takvim,) = ComplianceItem.objects.filter(kind=ComplianceKind.TAKVIM)
    assert (takvim.obligation, takvim.due_date) == ("IBRA_EDILMEDI_BILDIRIMI", gko.BIRINCI_GUN)


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.secim_bicimi")
def test_secim_bicimi_sonradan_girilince_eksik_kapanir() -> None:
    """O3 ("eksik bilgi girilince `resolved_at` ile kapanır"; altın kural 3: girilmemiş veri eksiktir,
    gerekçe istemez): seçimin biçimi sonuçla girilmediyse tutanak tamamlanana dek sonradan girilir;
    liste hâlinde ve açık oyla yapılmışsa eksik kapanır, tutanak gerekçesiz tamamlanır. Gizli oy
    uyarı + gerekçedir (gerekçesiz ret hiçbir şey yazmaz); düzeltilince sapma da kapanır. Sonucu
    girilmemiş seçimde biçim yazılmaz."""
    kurul = gko.yapilmis_olagan()
    with pytest.raises(ValueError, match="sonucu girilmedi"):
        genel_kurul_servisi.secim_bicimini_yaz(
            gko.madde(kurul, AgendaItemKind.SECIM_YK), liste=True, acik_oy=True
        )
    sonuc = gko.secim(kurul, AgendaItemKind.SECIM_DK, [gko.aday(kurul, organ="DK")], liste=None)
    (satir,) = _acik_satirlar("genel_kurul.secim_bicimi")
    assert satir.kind == ComplianceKind.EKSIK
    with pytest.raises(ValueError, match="ikisi birlikte"):
        genel_kurul_servisi.secim_bicimini_yaz(sonuc.madde, liste=True, acik_oy=None)  # type: ignore[arg-type]
    with pytest.raises(GerekceGerekli):
        genel_kurul_servisi.secim_bicimini_yaz(sonuc.madde, liste=True, acik_oy=False)
    satir.refresh_from_db()
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.EKSIK, None)
    sapma = genel_kurul_servisi.secim_bicimini_yaz(
        sonuc.madde, liste=True, acik_oy=False, gerekce=gko.GEREKCE
    )
    assert "genel_kurul.secim_bicimi" in [u["kural"] for u in sapma.uyarilar]
    satir.refresh_from_db()
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.SAPMA, None)
    genel_kurul_servisi.secim_bicimini_yaz(sonuc.madde, liste=True, acik_oy=True)
    satir.refresh_from_db()
    assert satir.resolved_at is not None
    assert _acik_satirlar("genel_kurul.secim_bicimi") == []
    assert genel_kurul_servisi.tutanagi_tamamla(kurul).kurul.status == AssemblyStatus.TUTANAK_TAMAM
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul_servisi.secim_bicimini_yaz(sonuc.madde, liste=True, acik_oy=True)
