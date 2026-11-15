"""Genel kurul kuralları (`gk`, tasarım §10.3): yeter sayının hesabı ve anlık görüntüsü; F2 4.
adımdan beri genel kurulun durum makinesinin kuralları (dosyanın sonu).

Yeter sayı 16 × 4 (mevcut ≥ 100) ya da 16 × 2 (mevcut < 100); taban kurul bileşiminden gelir, üyelik
kaydı sayılmaz; olağanüstü genel kurulda da aynıdır (tasarım §12.A S-1, S-2 düzeltmeleri). Değerler
`DEGER_TABLOSU` ile elle karşılaştırılmıştır.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from apps.oab.hatalar import GerekceGerekli, YeterSayiDonduruldu
from apps.oab.kurallar import denetle, genel_kurul, kural
from apps.oab.models import (
    AgendaItem,
    AgendaItemKind,
    Announcement,
    AssemblyCaller,
    AssemblyKind,
    AssemblyMeeting,
    AssemblyStatus,
    ComplianceItem,
    ComplianceKind,
    GeneralAssembly,
    OabTerm,
    TermStatus,
)
from apps.oab.services import donemler, uyum
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


def _uye_basvurusu(
    basvuran: int | None, uye: int | None, gerekce: uyum.Gerekce | None = None
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
        gerekce=gerekce,
    )


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_basvuru_oran")
def test_yuzde_10_alti_basvuru_uyari() -> None:
    """md. 9/6 "birlik üyelerinin %10'unun yazılı başvurusu": 9 / 100 uyarı + gerekçe (U12: üye sayısı
    elle girilir); başvuruyu program yöneticisi kaydeder."""
    with pytest.raises(GerekceGerekli):
        _uye_basvurusu(9, 100)
    sonuc = _uye_basvurusu(9, 100, gko.GEREKCE)
    (satir,) = _sapmalar("genel_kurul.olaganustu_basvuru_oran")
    assert satir.subject_id == str(sonuc.kurul.pk)
    assert (sonuc.kurul.member_application_count, sonuc.kurul.member_count_declared) == (9, 100)
    assert sonuc.kurul.call_document_id is None  # gelen evrak bağı 7. adımda; eksik, gerekçesiz
    assert genel_kurul_servisi.BASVURU_YAZISI_BILGISI in sonuc.bilgiler


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.olaganustu_basvuru_oran")
def test_yuzde_10_basvuru_uyarisiz() -> None:
    """10 / 100 tam sınır: uyarı yok (ondalık karşılaştırma, `Decimal`). Üye sayısı girilmemişse oran
    eksiktir: gerekçe istemez, tamamlanacaklara düşer."""
    sonuc = _uye_basvurusu(10, 100)
    assert sonuc.uyarilar == ()
    assert not ComplianceItem.objects.filter(rule_id="genel_kurul.olaganustu_basvuru_oran").exists()
    sonuc = _uye_basvurusu(12, None)
    (satir,) = _acik_satirlar("genel_kurul.olaganustu_basvuru_oran")
    assert satir.kind == ComplianceKind.EKSIK
    assert [u["durum"] for u in sonuc.uyarilar] == ["eksik"]


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
