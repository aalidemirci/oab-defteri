"""Genel kurulun durum makinesi: rol kapısı, hazırlık koşulları ve geçişlerin hesap bütünlüğü (F2 4.
adım; tasarım §4.4.2 M3, §7.1; plan F2 §6.2, §7 U1, U7, S1). F2 5. adımdan beri gündem, karar, divan
ve katılım düzeltmesinin rol kapısı, hesap bütünlüğü ve ekleme-yalnızlığı (dosyanın sonu).

Rol kapısı iki katlıdır: `Eylem.GENEL_KURUL_YAZMA` (program yöneticisi ve yönetim kurulu rolleri) ve
geçişin "Kim"i (tasarım §7.1). Ret `RolYetkisiz`'dir; uç katmanında 403 `rol_yetkisiz` olur
(`shared.exceptions.RolYetkisizResponse`). Kural testleri `kurallar/test_genel_kurul_kurallari.py`'de,
hazırlık dönemi senaryoları `kurallar/test_akis_kararlari.py`'dedir. Adlar UYDURMADIR.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from datetime import date, timedelta
from typing import Any

import pytest
from django.utils import timezone
from rest_framework import status

from apps.oab.hatalar import (
    DonemKapali,
    GerekceGerekli,
    KuralSurumuGuncellenmeli,
    YeterSayiDonduruldu,
)
from apps.oab.kurallar import genel_kurul as gk_kurallari
from apps.oab.kurallar import yukleyici as yk
from apps.oab.models import (
    AgendaItem,
    Announcement,
    AnnouncementStatus,
    AssemblyCaller,
    AssemblyKind,
    AssemblyMeeting,
    AssemblyStatus,
    AttendanceCorrection,
    ComplianceItem,
    ComplianceKind,
    GeneralAssembly,
    OabTerm,
    OrganMembership,
    OrganType,
    PersonStatus,
    TermStatus,
)
from apps.oab.services import genel_kurul as gk
from apps.oab.services import kisiler, kural_bagi, uyum
from apps.oab.tests import genel_kurul_ortak as gko
from apps.oab.tests import uyelik_ortak as o
from apps.oab.tests.kurallar import paket_ortak
from apps.okul.models import (
    AccountRole,
    AuditAction,
    AuditTrail,
    ImmutableRecord,
    SchoolConfig,
    SchoolYear,
)
from apps.okul.services import app_password
from shared.exceptions import RolYetkisiz, RolYetkisizResponse

pytestmark = pytest.mark.django_db


# ============================================================ rol kapısı (M3, tasarım §7.1 "Kim")
def test_rol_yetkisiz_403_yaniti_olur() -> None:
    assert RolYetkisizResponse.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "rol",
    [
        AccountRole.DENETLEME_KURULU,
        AccountRole.MUDUR,
        AccountRole.BASKAN,
        AccountRole.BASKAN_YARDIMCISI,
        AccountRole.MUHASIP,
    ],
)
def test_planlama_yalniz_program_yoneticisi_ve_sekreter(rol: AccountRole) -> None:
    """Denetleme Kurulu ve müdür genel kurulu okur (M3; müdürün kendi yazıları 7. adımda); başkan,
    başkan yardımcısı ve muhasip M3'te yazar ama planlamanın "Kim"i değildir. Ret yazmaz."""
    gko.acik_donem()
    with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
        gko.planla()
    assert not GeneralAssembly.objects.exists()
    assert not OabTerm.objects.filter(status=TermStatus.HAZIRLIK).exists()
    with o.rol_olarak(AccountRole.SEKRETER):
        assert gko.planla().status == AssemblyStatus.PLANLANDI


def test_yonetim_kurulunun_cagrisini_yalniz_sekreter_kaydeder() -> None:
    """Tasarım §7.1 olağan çağrı "Kim": sekreter (YK kararı); program yöneticisi çağrıyı yazmaz."""
    gko.acik_donem()
    kurul = gko.planla()
    with pytest.raises(RolYetkisiz):
        gk.cagir(kurul, gerekce=gko.KARAR_GEREKCESI)
    with o.rol_olarak(AccountRole.MUDUR), pytest.raises(RolYetkisiz):
        gk.cagir(kurul, gerekce=gko.KARAR_GEREKCESI)
    assert gko.olagan_cagir(kurul).status == AssemblyStatus.CAGRILDI


@pytest.mark.parametrize(
    "cagiran",
    [
        AssemblyCaller.OKUL_MUDURU,
        AssemblyCaller.MUDUR_25_2,
        AssemblyCaller.DENETLEME_KURULU,
        AssemblyCaller.MUDUR_YENI_OKUL,
    ],
)
@pytest.mark.parametrize("rol", [AccountRole.YONETICI, AccountRole.SEKRETER, AccountRole.BASKAN])
def test_mudurun_ve_denetleme_kurulunun_cagrisi_bu_yoldan_kaydedilmez(
    cagiran: str, rol: AccountRole
) -> None:
    """Müdürün (md. 9/1, 9/6, 25/2) ve Denetleme Kurulunun (md. 14/5) çağrısı kendi hesaplarından,
    kendi eylemleriyle yazılır (7. adım); program yöneticisi ve yönetim kurulu rolleri adlarına
    kaydedemez."""
    gko.acik_donem()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
        gk.cagir(
            kurul,
            called_by=cagiran,
            call_reason=gko.OLAGANUSTU_NEDEN,
            gundem=gko.OLAGANUSTU_GUNDEM,
        )
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.PLANLANDI


@pytest.mark.parametrize(
    "rol", [AccountRole.BASKAN, AccountRole.MUHASIP, AccountRole.DENETLEME_KURULU]
)
def test_ilan_ve_toplanti_yalniz_program_yoneticisi_ve_sekreter(rol: AccountRole) -> None:
    kurul = gko.cagrilmis_olagan()
    with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
        gk.ilan_et(kurul, kanallar=gko.kanallar())
    with o.rol_olarak(AccountRole.SEKRETER):
        gk.ilan_et(kurul, kanallar=gko.kanallar())
    with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
        gk.birinci_toplanti(kurul, katilim=gko.katilim(70))
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.ILAN_EDILDI


#: Planlamanın ve ilan/toplantı geçişlerinin "Kim"i dışında kalan roller (M3: müdür ve Denetleme
#: Kurulu genel kurulu okur; başkan, başkan yardımcısı ve muhasip bu geçişlerin "Kim"i değildir).
_KIM_DISI_ROLLER = (
    AccountRole.MUDUR,
    AccountRole.DENETLEME_KURULU,
    AccountRole.BASKAN,
    AccountRole.BASKAN_YARDIMCISI,
    AccountRole.MUHASIP,
)


def _kayitlarin_anligi() -> tuple[Any, ...]:
    """Genel kurul akışının yazdığı kayıtların anlık görüntüsü (ret hiçbirini değiştirmez)."""
    return (
        list(GeneralAssembly.objects.order_by("pk").values()),
        list(Announcement.objects.order_by("pk").values()),
        list(OabTerm.objects.order_by("pk").values()),
        list(ComplianceItem.objects.order_by("pk").values()),
        AuditTrail.objects.count(),
    )


def _tarih_degisikligi() -> Callable[[], object]:
    gko.acik_donem()
    kurul = gko.planla()
    return lambda: gk.toplanti_bilgisini_degistir(
        kurul, first_meeting_at=gko.an(date(2026, 10, 21))
    )


def _kanit_yazimi() -> Callable[[], object]:
    kurul = gko.cagrilmis_olagan()
    gk.ilan_et(kurul)
    (duyuru,) = gk.kurulun_duyurulari(kurul)
    return lambda: gk.ilan_kanitlarini_yaz(duyuru, kanallar=gko.kanallar())


def _ikinci_ilan() -> Callable[[], object]:
    kurul = gko.ilanli_olagan()
    gk.birinci_toplanti(kurul, katilim=gko.katilim(10))
    return lambda: gk.ikinci_toplanti_ilani(
        kurul,
        second_meeting_at=gko.an(date(2026, 11, 10)),
        kanallar=gko.kanallar(date(2026, 10, 24)),
    )


def _ikinci_toplanti() -> Callable[[], object]:
    kurul = gko.ilanli_olagan(second_meeting_at=gko.an(date(2026, 11, 10)))
    gk.birinci_toplanti(kurul, katilim=gko.katilim(10))
    return lambda: gk.ikinci_toplanti(kurul, katilim=gko.katilim(9))


@pytest.mark.parametrize("rol", _KIM_DISI_ROLLER)
@pytest.mark.parametrize(
    "kurulum",
    [_tarih_degisikligi, _kanit_yazimi, _ikinci_ilan, _ikinci_toplanti],
    ids=["toplanti_bilgisi", "ilan_kaniti", "ikinci_ilan", "ikinci_toplanti"],
)
def test_toplanti_bilgisi_kanit_ve_ikinci_toplanti_yalniz_program_yoneticisi_ve_sekreter(
    kurulum: Callable[[], Callable[[], object]], rol: AccountRole
) -> None:
    """Tasarım §7.1 "Kim": tarih değişimi planlamanın, kanal kanıtı ile ikinci toplantının ilanı ve
    sonucu ilan ve toplantının geçişidir (program yöneticisi, sekreter). Öteki roller `RolYetkisiz`
    alır, kayıt değişmez; sekreter aynı işlemi yapar."""
    cagri = kurulum()
    with o.rol_olarak(rol):
        once = _kayitlarin_anligi()
        with pytest.raises(RolYetkisiz):
            cagri()
        assert _kayitlarin_anligi() == once
    with o.rol_olarak(AccountRole.SEKRETER):
        cagri()


def test_parola_kurulmadan_yazilmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    gko.acik_donem()
    monkeypatch.setattr(app_password, "is_password_set", lambda: False)
    with pytest.raises(app_password.PasswordRequired):
        gko.planla()
    assert not GeneralAssembly.objects.exists()


# ============================================================ planlama koşulları
def _dagit(monkeypatch: pytest.MonkeyPatch, *icerikler: dict[str, Any]) -> None:
    monkeypatch.setattr(
        yk._Onbellek,
        "durum",
        yk.PaketDurumu(paketler=tuple(yk.Paket.sozlukten(icerik) for icerik in icerikler)),
    )


def test_r1e_bagli_acik_donemde_planlama_kural_surumu_gecisi_ister(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """U1: genel kurul kuralları kapanacak dönemin kopyasından okunur; `r1` genel kurulun F2 kurallarını
    taşımaz. Planlama yapılmaz (409), hazırlık dönemi açılmaz; geçişten sonra planlanır."""
    _dagit(monkeypatch, paket_ortak.oku("OAB-2023.12.r1.json"))
    acik = gko.acik_donem()
    _dagit(monkeypatch, *paket_ortak.REVIZYONLAR)
    with pytest.raises(KuralSurumuGuncellenmeli) as hata:
        gko.planla()
    assert hata.value.status_code == status.HTTP_409_CONFLICT
    assert not OabTerm.objects.filter(status=TermStatus.HAZIRLIK).exists()
    kural_bagi.revizyon_gecisi(acik, paket=paket_ortak.PAKET, rev=paket_ortak.EN_YENI_REV)
    assert gko.planla().status == AssemblyStatus.PLANLANDI


def test_ders_yili_tanimli_degilse_planlanmaz() -> None:
    """U5: hazırlık döneminin ders yılı birinci toplantının gününü içeren yıldır; tanımlı değilse
    Ayarlar → Ders Yılları'na yönlendirilir."""
    gko.acik_donem()
    with pytest.raises(ValueError, match="Ders Yılları"):
        gko.planla(birinci=gko.an(date(2027, 10, 20)))
    assert not GeneralAssembly.objects.exists()


def test_birlik_donemi_yoksa_acilis_tarihi_ister() -> None:
    """S5: hiç birlik dönemi olmayan okulda olağan genel kurul yeni açılan okulun ilk genel kuruludur;
    okul kartında açılış tarihi yoksa önce geçiş kurulumu (ya da açılış tarihi) istenir. Olağanüstü
    genel kurul açık dönem ister."""
    gko.ders_yillari()
    gko.mevcut()
    with pytest.raises(ValueError, match="geçiş kurulumunda"):
        gko.planla()
    with pytest.raises(ValueError, match="açık birlik döneminde"):
        gko.planla(kind=AssemblyKind.OLAGANUSTU)


def test_yeni_okulda_hazirliktaki_genel_kurul_varken_ikinci_planlama_nedenini_soyler() -> None:
    """Yeni açılan okulda açık dönem olamaz: ilk olağan genel kurul hazırlıktayken ikinci planlamanın
    reddi "açık dönem yok" değil, hazırlıktaki dönemdir (önceki genel kurul tamamlanmalı ya da iptal
    edilmeli). İptalden sonra yeniden planlanır."""
    gko.ders_yillari()
    gko.mevcut()
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(opened_on=date(2026, 9, 7))
    ilk = gko.planla()
    assert (ilk.term_id, ilk.called_by) == (None, AssemblyCaller.MUDUR_YENI_OKUL)
    assert ilk.opens_term_id is not None
    with pytest.raises(ValueError, match="Hazırlıkta bir birlik dönemi var"):
        gko.planla()
    assert GeneralAssembly.objects.count() == 1
    gk.iptal_et(ilk, cancel_reason="Uydurma: tarih yanlış girildi.")
    assert OabTerm.objects.get(opened_by_assembly=ilk).status == TermStatus.IPTAL
    assert gko.planla().opens_term_id != ilk.opens_term_id


def _ders_yili_2027() -> SchoolYear:
    yil: SchoolYear = SchoolYear.objects.create(
        name="2027-2028", start_date=date(2027, 9, 6), end_date=date(2028, 6, 23)
    )
    return yil


def test_tarih_baska_ders_yilina_tasininca_hazirlik_donemi_izler() -> None:
    """U5: hazırlık döneminin ders yılı birinci toplantının gününü içeren yıldır; tarih başka ders
    yılına taşınınca dönemin ders yılı ve adı izli olarak değişir. Yeni gün tanımlı bir ders yılında
    değilse Ayarlar → Ders Yılları'na yönlendirilir, kayıt değişmez."""
    gko.acik_donem()
    kurul = gko.planla()
    hazirlik = OabTerm.objects.get(opened_by_assembly=kurul)
    assert hazirlik.name == "2026-2027 birlik dönemi"
    once = _kayitlarin_anligi()
    with pytest.raises(ValueError, match="Ders Yılları"):
        gk.toplanti_bilgisini_degistir(kurul, first_meeting_at=gko.an(date(2027, 10, 20)))
    assert _kayitlarin_anligi() == once

    yil = _ders_yili_2027()
    izler = AuditTrail.objects.filter(model="oab.OabTerm", object_id=str(hazirlik.pk)).count()
    sonuc = gk.toplanti_bilgisini_degistir(kurul, first_meeting_at=gko.an(date(2027, 10, 20)))
    assert sonuc.kurul.first_meeting_at is not None
    assert gk.yerel_gun(sonuc.kurul.first_meeting_at) == date(2027, 10, 20)
    hazirlik.refresh_from_db()
    assert (hazirlik.school_year_id, hazirlik.name) == (yil.pk, "2027-2028 birlik dönemi")
    assert (
        AuditTrail.objects.filter(model="oab.OabTerm", object_id=str(hazirlik.pk)).count()
        == izler + 1
    )
    # Ekim 2027, yeni ders yılının Ekim'idir: toplantı günü uyarısı yoktur.
    assert sonuc.uyarilar == ()


def test_planlama_bilgileri_mevcut_ve_veli_listesi_onerisi() -> None:
    """Tasarım §7.1 `PLANLANDI` [B]: öğrenci mevcudu ve tarihi; veli listesi aktarılmadıysa öneri.
    Bilgi satırı saklanmaz, gerekçe istemez."""
    gko.acik_donem()
    bilgiler = gk.planla(
        kind=AssemblyKind.OLAGAN, first_meeting_at=gko.an(gko.BIRINCI_GUN)
    ).bilgiler
    assert any("120" in b and "15.09.2026" in b for b in bilgiler)
    assert gk.VELI_LISTESI_ONERISI in bilgiler
    gko.mevcut(None)
    assert any("girilmemiş" in b for b in gk.planlama_bilgileri())


def test_tarih_degisikliginde_toplanti_gunu_yeniden_denetlenir() -> None:
    """Plan F2 §3.1: `olagan_son_ay` planlamada ve tarih değişiminde denetlenir; tarih ilandan sonra
    değişmez."""
    gko.acik_donem()
    kurul = gko.planla()
    with pytest.raises(GerekceGerekli):
        gk.toplanti_bilgisini_degistir(kurul, first_meeting_at=gko.an(date(2026, 11, 5)))
    sonuc = gk.toplanti_bilgisini_degistir(
        kurul,
        first_meeting_at=gko.an(date(2026, 11, 5)),
        venue="Uydurma Konferans Salonu",
        gerekce=gko.GEREKCE,
    )
    assert sonuc.kurul.venue == "Uydurma Konferans Salonu"
    assert ComplianceItem.objects.filter(
        rule_id="genel_kurul.olagan_son_ay", kind=ComplianceKind.SAPMA
    ).exists()
    # Ekim'e dönülünce uyarı kalkar, satır kapanır.
    gk.toplanti_bilgisini_degistir(kurul, first_meeting_at=gko.an(gko.BIRINCI_GUN))
    assert not ComplianceItem.objects.filter(
        rule_id="genel_kurul.olagan_son_ay", resolved_at__isnull=True
    ).exists()
    assert GeneralAssembly.objects.get(pk=kurul.pk).rule_warnings == []
    gko.olagan_cagir(kurul)
    gk.ilan_et(kurul, kanallar=gko.kanallar())
    with pytest.raises(ValueError, match="ilandan önce"):
        gk.toplanti_bilgisini_degistir(kurul, first_meeting_at=gko.an(date(2026, 10, 22)))


# ============================================================ çağrı
def test_olagan_cagrida_karar_bagi_akis_uyarisi() -> None:
    """Kullanıcı kararı S1: olağan çağrının yönetim kurulu kararı bağı F3'e dek uyarı + gerekçedir
    (genel kurul başına bir). Atıfsız akış satırıdır; kurulun uyarı özetine girer."""
    gko.acik_donem()
    kurul = gko.planla()
    with o.rol_olarak(AccountRole.SEKRETER), pytest.raises(GerekceGerekli):
        gk.cagir(kurul)
    cagrilan = gko.olagan_cagir(kurul)
    (satir,) = ComplianceItem.objects.filter(rule_id=gk.KARARSIZ_CAGRI_AKISI)
    assert (satir.kind, satir.rule_package, satir.rev) == (ComplianceKind.SAPMA, "", None)
    assert cagrilan.called_by == AssemblyCaller.YONETIM_KURULU
    assert [s["kural"] for s in cagrilan.rule_warnings] == [gk.KARARSIZ_CAGRI_AKISI]


def test_olaganustu_cagri_nedeni_ve_gundemi_zorunlu() -> None:
    """md. 9/6: olağanüstü genel kurulun çağıranı ve çağrı nedeni zorunlu alandır; gündem çağrıda
    girilir (U19, U30). Olağan çağrıda bu alanlar girilmez."""
    gko.acik_donem()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.SEKRETER):
        with pytest.raises(ValueError, match="çağıran seçilmelidir"):
            gk.cagir(kurul, call_reason=gko.OLAGANUSTU_NEDEN, gundem=gko.OLAGANUSTU_GUNDEM)
        with pytest.raises(ValueError, match="çağrı nedeni"):
            gk.cagir(kurul, called_by=AssemblyCaller.YONETIM_KURULU, gundem=gko.OLAGANUSTU_GUNDEM)
        with pytest.raises(ValueError, match="gündem maddesi"):
            gk.cagir(
                kurul, called_by=AssemblyCaller.YONETIM_KURULU, call_reason=gko.OLAGANUSTU_NEDEN
            )
    assert not AgendaItem.objects.filter(assembly=kurul).exists()
    olagan = gko.planla()
    with o.rol_olarak(AccountRole.SEKRETER), pytest.raises(ValueError, match="tohum gündem"):
        gk.cagir(olagan, call_reason="Uydurma.", gerekce=gko.KARAR_GEREKCESI)


def test_basvuru_sayilarinin_hesap_butunlugu() -> None:
    gko.acik_donem()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    ortak: dict[str, Any] = {
        "called_by": AssemblyCaller.UYE_BASVURUSU,
        "call_reason": gko.OLAGANUSTU_NEDEN,
        "gundem": gko.OLAGANUSTU_GUNDEM,
    }
    with pytest.raises(ValueError, match="büyük olamaz"):
        gk.cagir(kurul, member_application_count=120, member_count_declared=100, **ortak)
    with pytest.raises(ValueError, match="sıfırdan büyük"):
        gk.cagir(kurul, member_application_count=0, member_count_declared=0, **ortak)
    with o.rol_olarak(AccountRole.SEKRETER), pytest.raises(ValueError, match="yalnız üyelerin"):
        gk.cagir(
            kurul,
            called_by=AssemblyCaller.YONETIM_KURULU,
            call_reason=gko.OLAGANUSTU_NEDEN,
            gundem=gko.OLAGANUSTU_GUNDEM,
            member_application_count=5,
        )


# ============================================================ ilan ve toplantılar
def test_ilan_yeter_sayiyi_okul_kartindaki_mevcuttan_dondurur() -> None:
    """U7: yeter sayı ilanda okul kartındaki mevcuttan hesaplanır ve dondurulur (99 → 32); okul kartı
    sonra değişse de değişmez. Mevcut girilmemişse ilan yapılmaz (hesap bütünlüğü). İlan kaydı
    kanıt günüyle yayımlanır."""
    gko.acik_donem(ogrenci=None)
    kurul = gko.olagan_cagir(gko.planla())
    with pytest.raises(ValueError, match="öğrenci mevcudu"):
        gk.ilan_et(kurul, kanallar=gko.kanallar())
    assert not Announcement.objects.exists()
    gko.mevcut(99)
    sonuc = gk.ilan_et(kurul, kanallar=gko.kanallar())
    assert (sonuc.kurul.student_count_snapshot, sonuc.kurul.quorum_required) == (99, 32)
    gko.mevcut(500)
    assert GeneralAssembly.objects.get(pk=kurul.pk).quorum_required == 32
    (duyuru,) = gk.kurulun_duyurulari(kurul)
    assert duyuru.status == AnnouncementStatus.YAYIMLANDI
    assert duyuru.term_id == kurul.term_id


_CARPAN_KURALI = "genel_kurul.yeter_sayi_carpan"


def _carpan_birinci_toplantidan_sonra_degisir() -> dict[str, Any]:
    """Sentetik revizyon (en yeni gerçek revizyonun üstüne): yeter sayı çarpanı birinci toplantı
    gününe dek 4, ertesi günden 3 (eski kaydın bitişi dolar, yeni kayıt eklenir; §6.2-3)."""
    kopya = deepcopy(paket_ortak.EN_YENI)
    kopya["rev"] = paket_ortak.EN_YENI_REV + 1
    kopya["degisiklikler"] = [{"id": _CARPAN_KURALI, "tur": "deger_degisikligi"}]
    eski = next(k for k in kopya["kurallar"] if k["id"] == _CARPAN_KURALI)
    yeni = deepcopy(eski)
    eski["yururluk"]["bitis"] = f"{gko.BIRINCI_GUN:%d.%m.%Y}"
    yeni["deger"] = 3
    yeni["yururluk"] = {
        "baslangic": f"{gko.BIRINCI_GUN + timedelta(days=1):%d.%m.%Y}",
        "bitis": None,
    }
    kopya["kurallar"].append(yeni)
    return kopya


def test_ilan_yeter_sayiyi_birinci_toplanti_gununun_kuraliyla_dondurur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """U7: yeter sayı birinci toplantı gününde yürürlükte olan kuralla dondurulur. Çarpan birinci
    toplantıdan sonraki gün değişir (4 → 3); ilanın yapıldığı gün (bugün) değil, birinci toplantının
    günü esastır: 16 × 4 = 64 (bugünün kuralıyla 48 olurdu)."""
    bugun = timezone.localdate()
    assert bugun > gko.BIRINCI_GUN  # ön koşul: bugünün kuralı yeni değerdir
    _dagit(monkeypatch, *paket_ortak.REVIZYONLAR, _carpan_birinci_toplantidan_sonra_degisir())
    kurul = gko.cagrilmis_olagan()
    acik = OabTerm.objects.select_related("rule_package").get(status=TermStatus.ACIK)
    assert acik.rule_package.rev == paket_ortak.EN_YENI_REV + 1
    assert gk_kurallari.genel_kurul_yeter_sayisi(120, tarih=bugun, donem=acik).gerekli == 48
    sonuc = gk.ilan_et(kurul, kanallar=gko.kanallar())
    assert (sonuc.kurul.quorum_multiplier, sonuc.kurul.quorum_required) == (4, 64)


def test_birinci_toplantinin_sonucunu_program_hesaplar() -> None:
    """md. 9/2: katılım yeter sayıdan az değilse yapıldı (64 → `YAPILDI`, birinci toplantı); açılışı okul
    müdürü yapar (md. 10/1-b; bilgi). Dağılımın toplamı katılımı tutmazsa kaydedilmez."""
    kurul = gko.ilanli_olagan()
    with pytest.raises(ValueError, match="toplamı"):
        gk.birinci_toplanti(kurul, katilim=gko.katilim(64, dagilim={"VELI_KURSIYER": 60}))
    with pytest.raises(ValueError, match="tanımlı türlerin"):
        gk.birinci_toplanti(kurul, katilim=gko.katilim(64, dagilim={"OGRENCI": 64}))
    sonuc = gk.birinci_toplanti(
        kurul,
        katilim=gko.katilim(
            64, dagilim={"VELI_KURSIYER": 60, "OGRETMEN": 4}, velisi_katilan=70, gozlemci=8
        ),
    )
    assert (sonuc.kurul.status, sonuc.kurul.held_at_meeting) == (
        AssemblyStatus.YAPILDI,
        AssemblyMeeting.BIRINCI,
    )
    assert (sonuc.kurul.first_attendee_count, sonuc.kurul.observer_count) == (64, 8)
    assert sonuc.kurul.parent_students_count == 70
    assert gk.MUDUR_ACILIS_BILGISI in sonuc.bilgiler
    with pytest.raises(ValueError, match="bu durumdayken"):
        gk.ikinci_toplanti(kurul, katilim=gko.katilim(3))


def test_kanal_kaniti_sonradan_girilince_15_gun_yeniden_denetlenir() -> None:
    """U9: bağlayıcı gün en geç kanalın günüdür; sonradan girilen geç kanal 15 günü bozarsa uyarı +
    gerekçe ister. İlan kanıtsız açılırsa taslak kalır, kanıt girilince yayımlanır."""
    kurul = gko.cagrilmis_olagan()
    gk.ilan_et(kurul)
    (duyuru,) = gk.kurulun_duyurulari(kurul)
    assert duyuru.status == AnnouncementStatus.TASLAK
    assert ComplianceItem.objects.filter(
        rule_id="genel_kurul.ilan_en_az_gun", kind=ComplianceKind.EKSIK
    ).exists()
    gec = gk.IlanKanallari(
        distributed_written_on=gko.ILAN_GUNU,
        posted_board_on=gko.ILAN_GUNU,
        published_web_on=date(2026, 10, 10),
    )
    with pytest.raises(GerekceGerekli):
        gk.ilan_kanitlarini_yaz(duyuru, kanallar=gec)
    sonuc = gk.ilan_kanitlarini_yaz(duyuru, kanallar=gec, gerekce=gko.GEREKCE)
    assert sonuc.kurul.announced_on == date(2026, 10, 10)
    duyuru.refresh_from_db()
    assert duyuru.status == AnnouncementStatus.YAYIMLANDI
    assert ComplianceItem.objects.get(
        rule_id="genel_kurul.ilan_en_az_gun", resolved_at__isnull=True
    ).kind == (ComplianceKind.SAPMA)


def test_durum_makinesi_disi_gecis_reddedilir() -> None:
    gko.acik_donem()
    kurul = gko.planla()
    with pytest.raises(ValueError, match="bu durumdayken"):
        gk.ilan_et(kurul, kanallar=gko.kanallar())
    with pytest.raises(ValueError, match="bu durumdayken"):
        gk.birinci_toplanti(kurul, katilim=gko.katilim(70))
    with pytest.raises(ValueError, match="bu durumdayken"):
        gk.ikinci_toplanti_ilani(kurul, second_meeting_at=gko.an(date(2026, 11, 1)))
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.PLANLANDI


def test_cagri_yalniz_planlanmis_kurulda() -> None:
    """Tasarım §7.1 `PLANLANDI → CAGRILDI`: çağrılmış ya da ilan edilmiş kurul yeniden çağrılmaz;
    durum geri sarılmaz, olağanüstünün gündemi ikinci kez yazılmaz."""
    kurul = gko.cagrilmis_olagan()
    with pytest.raises(ValueError, match="bu durumdayken"):
        gko.olagan_cagir(kurul)
    gk.ilan_et(kurul, kanallar=gko.kanallar())
    gundem = AgendaItem.objects.filter(assembly=kurul).count()
    with pytest.raises(ValueError, match="bu durumdayken"):
        gko.olagan_cagir(kurul)
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.ILAN_EDILDI
    assert AgendaItem.objects.filter(assembly=kurul).count() == gundem

    olaganustu = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    assert AgendaItem.objects.filter(assembly=olaganustu).count() == len(gko.OLAGANUSTU_GUNDEM)
    with pytest.raises(ValueError, match="bu durumdayken"):
        gko.olaganustu_cagir(olaganustu)
    assert AgendaItem.objects.filter(assembly=olaganustu).count() == len(gko.OLAGANUSTU_GUNDEM)
    assert GeneralAssembly.objects.get(pk=olaganustu.pk).status == AssemblyStatus.CAGRILDI


def test_yapilmis_genel_kurul_iptal_edilmez() -> None:
    """Tasarım §7.1 `… → IPTAL` yapılmış genel kurulu kapsamaz: iptal reddedilir, kurul `YAPILDI`,
    hazırlık dönemi `HAZIRLIK` kalır."""
    kurul = gko.ilanli_olagan()
    gk.birinci_toplanti(kurul, katilim=gko.katilim(70))
    with pytest.raises(ValueError, match="bu durumdayken"):
        gk.iptal_et(kurul, cancel_reason="Uydurma: geç fark edildi.")
    sonra = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (sonra.status, sonra.cancel_reason) == (AssemblyStatus.YAPILDI, "")
    assert OabTerm.objects.get(opened_by_assembly=kurul).status == TermStatus.HAZIRLIK


def test_ikinci_toplanti_ilani_bir_kez_ve_birinciden_sonra() -> None:
    """İkinci toplantı bir kez ilan edilir (ilk ilan birinci toplantınındır, ikincisi ikinci
    toplantının) ve birinci toplantıdan sonra olmalıdır (hesap bütünlüğü; sert, Türkçe ileti)."""
    kurul = gko.cagrilmis_olagan()
    birinci = gko.an(gko.BIRINCI_GUN)
    for ikinci in (birinci, birinci - timedelta(hours=1)):
        with pytest.raises(ValueError, match="birinci toplantıdan sonra"):
            gk.ilan_et(kurul, kanallar=gko.kanallar(), second_meeting_at=ikinci)
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.CAGRILDI
    assert not Announcement.objects.exists()

    gk.ilan_et(kurul, kanallar=gko.kanallar())
    gk.birinci_toplanti(kurul, katilim=gko.katilim(10))
    with pytest.raises(ValueError, match="birinci toplantıdan sonra"):
        gk.ikinci_toplanti_ilani(kurul, second_meeting_at=birinci, kanallar=gko.kanallar())
    assert len(gk.kurulun_duyurulari(kurul)) == 1
    gk.ikinci_toplanti_ilani(
        kurul,
        second_meeting_at=gko.an(date(2026, 11, 10)),
        kanallar=gko.kanallar(date(2026, 10, 24)),
    )
    with pytest.raises(ValueError, match="ayrıca ilan edildi"):
        gk.ikinci_toplanti_ilani(
            kurul,
            second_meeting_at=gko.an(date(2026, 11, 12)),
            kanallar=gko.kanallar(date(2026, 10, 24)),
        )
    assert len(gk.kurulun_duyurulari(kurul)) == 2
    sonra = GeneralAssembly.objects.get(pk=kurul.pk)
    assert sonra.second_meeting_at == gko.an(date(2026, 11, 10))


def test_ikinci_ilanin_kaniti_ikinci_toplanti_gunune_gore_ve_kendi_alanina() -> None:
    """Kanıtsız açılan ikinci toplantı ilanının kanıtı sonradan girilince `second_announced_on`
    yazılır, birinci ilanın bağlayıcı günü (`announced_on`) değişmez; 15 gün ikinci toplantının
    gününe göre denetlenir (24.10 → 10.11 on yedi gün: uyarı yok; birinci toplantıya göre olsaydı
    sapma gerekçe isterdi)."""
    kurul = gko.ilanli_olagan()
    gk.birinci_toplanti(kurul, katilim=gko.katilim(10))
    gk.ikinci_toplanti_ilani(kurul, second_meeting_at=gko.an(date(2026, 11, 10)))
    _, ikinci = gk.kurulun_duyurulari(kurul)
    eksikler = ComplianceItem.objects.filter(
        subject_type="oab.Announcement",
        subject_id=str(ikinci.pk),
        kind=ComplianceKind.EKSIK,
        resolved_at__isnull=True,
    )
    assert set(eksikler.values_list("rule_id", flat=True)) == {
        "genel_kurul.ilan_en_az_gun",
        "genel_kurul.ilan_kanallari",
    }
    sonuc = gk.ilan_kanitlarini_yaz(ikinci, kanallar=gko.kanallar(date(2026, 10, 24)))
    assert sonuc.uyarilar == ()
    assert (sonuc.kurul.announced_on, sonuc.kurul.second_announced_on) == (
        gko.ILAN_GUNU,
        date(2026, 10, 24),
    )
    assert not eksikler.exists()
    assert not ComplianceItem.objects.filter(
        subject_type="oab.Announcement", subject_id=str(ikinci.pk), resolved_at__isnull=True
    ).exists()


# ============================================================ iptal
def test_iptalde_kurulun_ve_ilaninin_eksikleri_kapanir() -> None:
    """Kanalsız ilan edilen genel kurul iptal edilince ilanın açık eksikleri (15 gün, üç kanal)
    kapanır: girilecek kanıt artık girilmeyecek (O3), dönem kapanışında gerekçe istenmez. Satırlar
    silinmez, kapanışları izlidir. İptal edilen kurulun ilanına kanıt yazılmaz."""
    kurul = gko.cagrilmis_olagan()
    gk.ilan_et(kurul)
    (duyuru,) = gk.kurulun_duyurulari(kurul)
    eksikler = ComplianceItem.objects.filter(kind=ComplianceKind.EKSIK, resolved_at__isnull=True)
    kurallar = {"genel_kurul.ilan_en_az_gun", "genel_kurul.ilan_kanallari"}
    assert set(eksikler.values_list("rule_id", flat=True)) == kurallar
    satirlar = list(eksikler.all())  # `eksikler` önbelleğe alınmasın
    sapmalar = list(
        ComplianceItem.objects.filter(kind=ComplianceKind.SAPMA, resolved_at__isnull=True)
    )
    assert sapmalar  # olağan çağrının karar bağı akış satırı (gerekçeli)

    gk.iptal_et(kurul, cancel_reason="Uydurma: salon kullanılamadı.")
    assert not eksikler.exists()
    for satir in satirlar:
        satir.refresh_from_db()
        assert (satir.kind, satir.resolved_at is not None) == (ComplianceKind.EKSIK, True)
        assert (
            AuditTrail.objects.filter(model="oab.ComplianceItem", object_id=str(satir.pk)).count()
            == 2
        )
    # Gerekçeli sapma kapanmaz; iz olarak kalır.
    assert all(ComplianceItem.objects.get(pk=s.pk).resolved_at is None for s in sapmalar)
    acik = OabTerm.objects.get(status=TermStatus.ACIK)
    assert uyum.kapanis_gecisi(acik, gerekceler={}, tarih=gko.BIRINCI_GUN) == []
    with pytest.raises(ValueError, match="bu durumdayken"):
        gk.ilan_kanitlarini_yaz(duyuru, kanallar=gko.kanallar())


def test_iptalde_basvuru_sayilarinin_eksigi_kapanir() -> None:
    """Üyelerin başvurusuyla çağrılan olağanüstü genel kurulda sayılar girilmediyse oran eksiktir
    (konusu kurul); kurul iptal edilince eksik kapanır."""
    gko.acik_donem()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    gk.cagir(
        kurul,
        called_by=AssemblyCaller.UYE_BASVURUSU,
        call_reason=gko.OLAGANUSTU_NEDEN,
        gundem=gko.OLAGANUSTU_GUNDEM,
    )
    eksik = ComplianceItem.objects.filter(
        rule_id="genel_kurul.olaganustu_basvuru_oran",
        kind=ComplianceKind.EKSIK,
        resolved_at__isnull=True,
    )
    assert eksik.count() == 1
    gk.iptal_et(kurul, cancel_reason="Uydurma: başvuru geri çekildi.")
    assert not eksik.exists()
    assert ComplianceItem.objects.filter(rule_id="genel_kurul.olaganustu_basvuru_oran").count() == 1


# ============================================================ denetim izi
def test_akisin_her_yazimi_denetim_izine_duser() -> None:
    """İzli servis kalıbı (altın kural 4): planlama, çağrı, ilan ve toplantılar; genel kurul, hazırlık
    dönemi ve ilan kayıtlarının yazımları iz satırı yazar, yazan hesabın adına (çağrıyı sekreter,
    ötekileri program yöneticisi yazar)."""
    gko.acik_donem()
    kurul = gko.planla()
    with o.rol_olarak(AccountRole.SEKRETER) as sekreter:
        gk.cagir(kurul, gerekce=gko.KARAR_GEREKCESI)
    gk.ilan_et(kurul, kanallar=gko.kanallar())
    gk.birinci_toplanti(kurul, katilim=gko.katilim(10))
    gk.ikinci_toplanti_ilani(
        kurul,
        second_meeting_at=gko.an(date(2026, 11, 10)),
        kanallar=gko.kanallar(date(2026, 10, 24)),
    )
    gk.ikinci_toplanti(kurul, katilim=gko.katilim(9))
    satirlar = AuditTrail.objects.filter(model="oab.GeneralAssembly", object_id=str(kurul.pk))
    eylemler = list(satirlar.order_by("seq").values_list("action", flat=True))
    assert eylemler[0] == AuditAction.OLUSTUR
    # Planlandı → çağrıldı → ilan edildi → yeter sayı yok → yapıldı: her geçiş ayrı DURUM satırı.
    assert eylemler.count(AuditAction.DURUM) == 4
    durumlar = list(
        satirlar.filter(action=AuditAction.DURUM).order_by("seq").values_list("account_id", "role")
    )
    # Çağrı sekreterin hesabıyla, öteki geçişler program yöneticisinin hesabıyla yazılır.
    assert durumlar[0] == (sekreter.pk, AccountRole.SEKRETER.value)
    yonetici = satirlar.order_by("seq").values_list("account_id", "role").first()
    assert yonetici is not None
    assert yonetici[0] is not None and yonetici[0] != sekreter.pk
    assert durumlar[1:] == [yonetici] * 3
    for duyuru in gk.kurulun_duyurulari(kurul):
        assert AuditTrail.objects.filter(
            model="oab.Announcement", object_id=str(duyuru.pk), account_id=yonetici[0]
        ).exists()
    assert (
        AuditTrail.objects.filter(model="oab.OabTerm", object_id=str(kurul.opens_term_id)).count()
        >= 2
    )


def test_iptal_denetim_izine_duser() -> None:
    """İptal genel kurul ve hazırlık dönemi için birer `DURUM` satırı yazar, iptal eden program
    yöneticisinin hesabıyla (altın kural 4)."""
    kurul = gko.ilanli_olagan()
    gk.iptal_et(kurul, cancel_reason="Uydurma: salon kullanılamadı.")
    for model, kimlik in (
        ("oab.GeneralAssembly", kurul.pk),
        ("oab.OabTerm", kurul.opens_term_id),
    ):
        son = AuditTrail.objects.filter(model=model, object_id=str(kimlik)).order_by("seq").last()
        assert son is not None
        assert son.action == AuditAction.DURUM
        assert son.role == AccountRole.YONETICI.value
        assert son.account_id is not None


# ============================================================ 5. adım: gündem, karar, divan, düzeltme
def _yaz_gundem_ekle(kurul: GeneralAssembly) -> None:
    gk.gundeme_madde_ekle(
        kurul, title="Uydurma madde", change_votes_for=40, change_votes_against=10
    )


def _yaz_gundem_cikar(kurul: GeneralAssembly) -> None:
    gk.gundemden_madde_cikar(
        gko.madde(kurul, "DILEK"), change_votes_for=40, change_votes_against=10
    )


def _yaz_sira(kurul: GeneralAssembly) -> None:
    maddeler = list(AgendaItem.objects.filter(assembly=kurul).order_by("order"))
    gk.gundem_sirasini_degistir(kurul, sira=[m.pk for m in reversed(maddeler)])


def _yaz_karar(kurul: GeneralAssembly) -> None:
    gk.karar_sonucu_yaz(gko.madde(kurul, "YETKILENDIRME"), votes_for=50, votes_against=10)


def _yaz_divan(kurul: GeneralAssembly) -> None:
    gk.divan_sec(kurul, baskan=o.kisi(), katip=o.kisi())


def _yaz_duzeltme(kurul: GeneralAssembly) -> None:
    gk.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        degerler={"first_attendee_count": 71},
        justification="Uydurma: cetvelde bir imza sonradan sayıldı.",
    )


_TUTANAK_YAZIMLARI: dict[str, Callable[[GeneralAssembly], None]] = {
    "gundem_ekle": _yaz_gundem_ekle,
    "gundem_cikar": _yaz_gundem_cikar,
    "sira": _yaz_sira,
    "karar": _yaz_karar,
    "divan": _yaz_divan,
    "duzeltme": _yaz_duzeltme,
}


@pytest.mark.parametrize("yazim", sorted(_TUTANAK_YAZIMLARI))
@pytest.mark.parametrize(
    "rol",
    [
        AccountRole.BASKAN,
        AccountRole.BASKAN_YARDIMCISI,
        AccountRole.MUHASIP,
        AccountRole.DENETLEME_KURULU,
        AccountRole.MUDUR,
    ],
)
def test_tutanak_yazimlari_yalniz_program_yoneticisi_ve_sekreter(
    yazim: str, rol: AccountRole
) -> None:
    """Tasarım §7.1 `YAPILDI → TUTANAK_TAMAM` "Kim": gündem değişikliği, karar, divan ve katılım
    düzeltmesi program yöneticisi ve sekreterdir; Denetleme Kurulu ve müdür okur (M3), başkan,
    başkan yardımcısı ve muhasip bu geçişin "Kim"i değildir. Ret hiçbir şey yazmaz; sekreter yazar."""
    kurul = gko.yapilmis_olagan()
    # Rol hesabının ve divana yazılacak kişilerin açılışı sayılmaz; genel kurulun kayıtları sayılır.
    genel_kurul_izleri = AuditTrail.objects.exclude(model__in=["okul.Account", "oab.OabPerson"])
    izler = genel_kurul_izleri.count()
    with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
        _TUTANAK_YAZIMLARI[yazim](kurul)
    assert genel_kurul_izleri.count() == izler
    with o.rol_olarak(AccountRole.SEKRETER):
        _TUTANAK_YAZIMLARI[yazim](kurul)
    assert genel_kurul_izleri.count() > izler


def test_karar_sonucunun_hesap_butunlugu() -> None:
    """Karar sonucu (S6 (iii), S2): oyların toplamı paydayı aşamaz, salondaki sayı katılımı aşamaz
    (hesap bütünlüğü, sert; Türkçe ileti). Oylanmayan madde "görüşüldü"dür, oy almaz; oylanan madde
    iki oyu da ister. İbra ve seçim sonuçları 6. adımın yolundadır. Sonuç yalnız yapılmış genel
    kurulda yazılır."""
    kurul = gko.yapilmis_olagan()
    yetki = gko.madde(kurul, "YETKILENDIRME")
    with pytest.raises(ValueError, match="aşamaz"):
        gk.karar_sonucu_yaz(yetki, votes_for=60, votes_against=11)
    with pytest.raises(ValueError, match="aşamaz"):
        gk.karar_sonucu_yaz(yetki, votes_for=30, votes_against=11, present_count=40)
    with pytest.raises(ValueError, match="salonda bulunan"):
        gk.karar_sonucu_yaz(yetki, votes_for=30, votes_against=11, present_count=71)
    with pytest.raises(ValueError, match="ret oyları girilmelidir"):
        gk.karar_sonucu_yaz(yetki, votes_for=30)
    rapor = gko.madde(kurul, "YK_FAALIYET_RAPORU")
    with pytest.raises(ValueError, match="oy girilmez"):
        gk.karar_sonucu_yaz(rapor, result="GORUSULDU", votes_for=30, votes_against=1)
    sonuc = gk.karar_sonucu_yaz(rapor, result="GORUSULDU")
    assert (sonuc.madde.result, sonuc.madde.votes_for) == ("GORUSULDU", None)
    for tur in ("IBRA", "SECIM_YK", "SECIM_DK"):
        with pytest.raises(ValueError, match="kendi adımında"):
            gk.karar_sonucu_yaz(gko.madde(kurul, tur), votes_for=50, votes_against=1)
    with pytest.raises(ValueError, match="kabul, ret ya da görüşüldü"):
        gk.karar_sonucu_yaz(yetki, result="BELKI", votes_for=50, votes_against=1)
    assert AgendaItem.objects.get(pk=yetki.pk).result == ""

    olaganustu = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    gk.ilan_et(olaganustu, kanallar=gko.kanallar())
    with pytest.raises(ValueError, match="bu durumdayken"):
        gk.karar_sonucu_yaz(gko.madde(olaganustu, "ACILIS"), result="GORUSULDU")


def test_gundemden_cikarilan_madde_silinmez_ve_gorusulmez() -> None:
    """md. 9/4, altın kural 4: çıkarılan madde silinmez, yerinde kalır, görüşülmez (sonuç yazılmaz);
    ikinci kez çıkarılmaz. Sonucu girilmiş madde çıkarılmaz; oylamayla eklenen madde ayrıca
    çıkarılmaz. Oylar birlikte girilir ve katılımı aşamaz."""
    kurul = gko.yapilmis_olagan()
    dilek = gko.madde(kurul, "DILEK")
    with pytest.raises(ValueError, match="birlikte"):
        gk.gundemden_madde_cikar(dilek, change_votes_for=40)
    with pytest.raises(ValueError, match="aşamaz"):
        gk.gundemden_madde_cikar(dilek, change_votes_for=40, change_votes_against=31)
    gk.gundemden_madde_cikar(dilek, change_votes_for=40, change_votes_against=30)
    with pytest.raises(ImmutableRecord):
        AgendaItem.objects.filter(pk=dilek.pk).delete()
    assert AgendaItem.objects.get(pk=dilek.pk).removed_by_vote is True
    with pytest.raises(ValueError, match="çıkarıldı"):
        gk.gundemden_madde_cikar(dilek, change_votes_for=40, change_votes_against=30)
    with pytest.raises(ValueError, match="çıkarıldı"):
        gk.karar_sonucu_yaz(dilek, result="GORUSULDU")

    yetki = gko.madde(kurul, "YETKILENDIRME")
    gk.karar_sonucu_yaz(yetki, votes_for=50, votes_against=10)
    with pytest.raises(ValueError, match="Sonucu girilmiş"):
        gk.gundemden_madde_cikar(yetki, change_votes_for=40, change_votes_against=30)
    eklenen = gk.gundeme_madde_ekle(
        kurul, title="Uydurma madde", change_votes_for=40, change_votes_against=10
    ).madde
    with pytest.raises(ValueError, match="ayrıca çıkarılamaz"):
        gk.gundemden_madde_cikar(eklenen, change_votes_for=40, change_votes_against=10)
    with pytest.raises(ValueError, match="sırası"):
        gk.gundeme_madde_ekle(
            kurul, title="Uydurma", sira=99, change_votes_for=40, change_votes_against=10
        )


def test_gundem_degisikligi_yalniz_toplantida() -> None:
    """Gündeme ekleme ve çıkarma toplantıda oylanır (md. 9/4): ilandan önce, ilan edilmiş ama
    toplanmamış ya da yeter sayı sağlanamamış genel kurulda yapılmaz."""
    kurul = gko.ilanli_olagan()
    with pytest.raises(ValueError, match="bu durumdayken"):
        _yaz_gundem_ekle(kurul)
    gk.birinci_toplanti(kurul, katilim=gko.katilim(10))
    with pytest.raises(ValueError, match="bu durumdayken"):
        _yaz_gundem_cikar(kurul)


def test_divan_tek_ve_ayri_kisiler() -> None:
    """md. 10/1-c "bir divan başkanı ve bir kâtip": aynı kişi ikisi olamaz; bir genel kurulun tek
    divanı vardır; pasif kişi divana yazılmaz. Divan yalnız yapılmış genel kurulda seçilir."""
    kurul = gko.ilanli_olagan()
    veli = o.kisi()
    with pytest.raises(ValueError, match="bu durumdayken"):
        gk.divan_sec(kurul, baskan=veli, katip=o.kisi())
    gk.birinci_toplanti(kurul, katilim=gko.katilim(70))
    with pytest.raises(ValueError, match="ayrı kişilerdir"):
        gk.divan_sec(kurul, baskan=veli, katip=veli)
    pasif = o.kisi()
    kisiler.update_person(pasif, status=PersonStatus.PASIF)
    with pytest.raises(ValueError, match="Pasif"):
        gk.divan_sec(kurul, baskan=veli, katip=pasif)
    assert not OrganMembership.objects.filter(organ=OrganType.DIVAN).exists()
    gk.divan_sec(kurul, baskan=veli, katip=o.kisi())
    with pytest.raises(ValueError, match="divanı seçildi"):
        gk.divan_sec(kurul, baskan=o.kisi(), katip=o.kisi())
    assert len(gk.kurulun_divani(kurul)) == 2


def test_ikinci_toplantida_divan_ikinci_toplanti_gunuyle() -> None:
    """İkinci toplantıda yapılan genel kurulun divanı ikinci toplantının günüyle yazılır; payda
    ikinci toplantının katılımıdır (md. 9/2: çoğunluk aranmaz, kararlar katılanların çoğunluğuyla)."""
    kurul = gko.ilanli_olagan(second_meeting_at=gko.an(date(2026, 11, 3)))
    gk.birinci_toplanti(kurul, katilim=gko.katilim(10))
    gk.ikinci_toplanti(kurul, katilim=gko.katilim(5))
    gk.divan_sec(kurul, baskan=o.kisi(), katip=o.kisi())
    assert {u.start_date for u in gk.kurulun_divani(kurul)} == {date(2026, 11, 3)}
    yetki = gko.madde(kurul, "YETKILENDIRME")
    assert gk.karar_sonucu_yaz(yetki, votes_for=3, votes_against=2).madde.result == "KABUL"
    with pytest.raises(ValueError, match="aşamaz"):
        gk.karar_sonucu_yaz(yetki, votes_for=3, votes_against=3)


# ------------------------------------------------------------ katılım düzeltmesi
def test_katilim_duzeltmesi_ekleme_yalniz() -> None:
    """Tasarım §5.2.3: düzeltme ekleme-yalnızdır; her düzeltme yeni satırdır, satır değişmez ve
    silinmez. Genel kuruldaki sayı son düzeltme satırının değeridir; toplantıda girilen ilk değer
    ilk satırın önceki değerinden okunur. Durum değişmez; yazımlar izlidir."""
    kurul = gko.yapilmis_olagan()
    _yaz_duzeltme(kurul)
    gk.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        degerler={"first_attendee_count": 72, "observer_count": 4},
        justification="Uydurma: ikinci sayım.",
    )
    sonra = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (sonra.status, sonra.first_attendee_count, sonra.observer_count) == (
        AssemblyStatus.YAPILDI,
        72,
        4,
    )
    satirlar = gk.katilim_duzeltmeleri(kurul)
    assert [(s.field, s.old_value, s.new_value) for s in satirlar] == [
        ("first_attendee_count", 70, 71),
        ("first_attendee_count", 71, 72),
        ("observer_count", None, 4),
    ]
    assert satirlar[0].justification == "Uydurma: cetvelde bir imza sonradan sayıldı."
    assert gk.ilk_girilen_deger(sonra, "first_attendee_count") == 70
    assert gk.ilk_girilen_deger(sonra, "second_attendee_count") is None
    ilk = satirlar[0]
    ilk.new_value = 99
    with pytest.raises(ImmutableRecord):
        ilk.save()
    with pytest.raises(ImmutableRecord):
        AttendanceCorrection.objects.filter(pk=ilk.pk).update(new_value=99)
    with pytest.raises(ImmutableRecord):
        AttendanceCorrection.objects.filter(pk=ilk.pk).delete()
    with pytest.raises(ImmutableRecord):
        AttendanceCorrection.objects.get(pk=ilk.pk).delete()
    assert AttendanceCorrection.objects.get(pk=ilk.pk).new_value == 71
    assert (
        AuditTrail.objects.filter(
            model="oab.AttendanceCorrection", action=AuditAction.OLUSTUR
        ).count()
        == 3
    )


def test_katilim_duzeltmesi_gerekce_ister_ve_yeter_sayiya_uzanmaz() -> None:
    """Gerekçe zorunludur (boş gerekçe satır yazmaz). Dondurulmuş yeter sayının dört alanı
    düzeltilemez (sert — hesap bütünlüğü); bilinmeyen alan, aynı değer, başka toplantının sayısı ve
    yapılmamış ikinci toplantı reddedilir."""
    kurul = gko.yapilmis_olagan()
    with pytest.raises(ValueError, match="gerekçesi"):
        gk.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.BIRINCI,
            degerler={"first_attendee_count": 71},
            justification="   ",
        )
    for alan in ("quorum_required", "quorum_base", "quorum_multiplier", "student_count_snapshot"):
        with pytest.raises(YeterSayiDonduruldu):
            gk.katilim_duzelt(
                kurul,
                toplanti=AssemblyMeeting.BIRINCI,
                degerler={alan: 10},
                justification="Uydurma: yanlış.",
            )
    durumlar: list[tuple[str, dict[str, Any], str]] = [
        (AssemblyMeeting.BIRINCI, {"venue": 1}, "Düzeltilen sayı"),
        (AssemblyMeeting.BIRINCI, {"first_attendee_count": 70}, "aynı"),
        (AssemblyMeeting.IKINCI, {"first_attendee_count": 71}, "seçilen toplantının"),
        (AssemblyMeeting.IKINCI, {"second_attendee_count": 3}, "İkinci toplantı yapılmadı"),
        (AssemblyMeeting.BIRINCI, {}, "en az bir"),
    ]
    for toplanti, degerler, ileti in durumlar:
        with pytest.raises(ValueError, match=ileti):
            gk.katilim_duzelt(
                kurul, toplanti=toplanti, degerler=degerler, justification="Uydurma: yanlış."
            )
    assert not AttendanceCorrection.objects.exists()
    assert GeneralAssembly.objects.get(pk=kurul.pk).quorum_required == 64


def test_yeter_sayi_sonucunu_degistiren_duzeltme_gerekce_ister() -> None:
    """Tasarım §5.2.3: düzeltme birinci toplantıda yeter sayının sağlanıp sağlanmadığını
    değiştiriyorsa uyarı + gerekçedir (akış satırı; atıfsız). Gerekçesiz ret satır yazmaz;
    gerekçeyle düzeltme kaydedilir, sapma satırının konusu düzeltmedir, iz satırı ona bağlıdır.
    Genel kurulun durumu değişmez."""
    kurul = gko.yapilmis_olagan()
    with pytest.raises(GerekceGerekli):
        gk.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.BIRINCI,
            degerler={"first_attendee_count": 60},
            justification="Uydurma: mükerrer imzalar ayıklandı.",
        )
    assert not AttendanceCorrection.objects.exists()
    sonuc = gk.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        degerler={"first_attendee_count": 60},
        justification="Uydurma: mükerrer imzalar ayıklandı.",
        gerekce=gko.GEREKCE,
    )
    assert [u["kural"] for u in sonuc.uyarilar] == [gk.DUZELTME_YETER_SAYI_AKISI]
    assert (sonuc.kurul.status, sonuc.kurul.first_attendee_count) == (AssemblyStatus.YAPILDI, 60)
    duzeltme = AttendanceCorrection.objects.get()
    satir = ComplianceItem.objects.get(rule_id=gk.DUZELTME_YETER_SAYI_AKISI)
    assert (satir.kind, satir.subject_type, satir.subject_id) == (
        ComplianceKind.SAPMA,
        "oab.AttendanceCorrection",
        str(duzeltme.pk),
    )
    iz = AuditTrail.objects.get(model="oab.AttendanceCorrection", object_id=str(duzeltme.pk))
    assert iz.compliance_item_id == satir.pk
    # Yeter sayının aynı yanında kalan düzeltme uyarı üretmez.
    gk.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        degerler={"first_attendee_count": 61},
        justification="Uydurma: bir imza daha.",
    )
    assert ComplianceItem.objects.filter(rule_id=gk.DUZELTME_YETER_SAYI_AKISI).count() == 1
    # Eşitlik sınırı (yeter sayı 64; birinci toplantının hesabıyla aynı `>=`): 64'e çıkan düzeltme
    # yeter sayıyı sağlatır, 63'e inen düşürür; ikisi de gerekçe ister. 64'te ya da üstünde kalan
    # düzeltme uyarısızdır.
    adimlar = ((64, True), (65, False), (64, False), (63, True))
    for sayi, uyarili in adimlar:
        degerler = {"first_attendee_count": sayi}
        if uyarili:
            with pytest.raises(GerekceGerekli):
                gk.katilim_duzelt(
                    kurul,
                    toplanti=AssemblyMeeting.BIRINCI,
                    degerler=degerler,
                    justification="Uydurma: sayım.",
                )
        sonuc = gk.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.BIRINCI,
            degerler=degerler,
            justification="Uydurma: sayım.",
            gerekce=gko.GEREKCE if uyarili else None,
        )
        assert bool(sonuc.uyarilar) is uyarili, sayi
        assert sonuc.kurul.status == AssemblyStatus.YAPILDI
    assert ComplianceItem.objects.filter(rule_id=gk.DUZELTME_YETER_SAYI_AKISI).count() == 3


def test_yeter_sayi_yokken_yeter_sayiyi_saglatan_duzeltme_gerekce_ister() -> None:
    """Tasarım §5.2.3'ün en ağır hâli: birinci toplantıda yeter sayı aslında sağlanmıştı
    (`YETER_SAYI_YOK` kurulda katılım 10'dan 64'e düzeltilir). Düzeltme gerekçe ister; genel kurulun
    durumu değişmez (`YETER_SAYI_YOK` kalır, ikinci toplantı yolu açık kalır)."""
    kurul = gko.ilanli_olagan(second_meeting_at=gko.an(date(2026, 11, 3)))
    gk.birinci_toplanti(kurul, katilim=gko.katilim(10))
    with pytest.raises(GerekceGerekli):
        gk.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.BIRINCI,
            degerler={"first_attendee_count": 64},
            justification="Uydurma: ikinci sayfa sayılmamış.",
        )
    assert not AttendanceCorrection.objects.exists()
    sonuc = gk.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        degerler={"first_attendee_count": 64},
        justification="Uydurma: ikinci sayfa sayılmamış.",
        gerekce=gko.GEREKCE,
    )
    assert [u["kural"] for u in sonuc.uyarilar] == [gk.DUZELTME_YETER_SAYI_AKISI]
    sonra = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (sonra.status, sonra.first_attendee_count) == (AssemblyStatus.YETER_SAYI_YOK, 64)
    assert not sonra.held_at_meeting
    assert gk.ilk_girilen_deger(sonra, "first_attendee_count") == 10


def test_duzeltmede_dagilim_toplami_katilimi_tutar() -> None:
    """Hesap bütünlüğü (4. adım kararı): türe göre dağılımın toplamı katılım sayısını tutar; katılım
    düzeltilirse dağılım aynı işlemde düzeltilir. İkinci toplantı yapıldıysa dağılım ikincinindir
    (`test_ikinci_toplantinin_katilimi_dagilimla_duzeltilir`)."""
    kurul = gko.ilanli_olagan()
    gk.birinci_toplanti(
        kurul, katilim=gko.katilim(70, dagilim={"VELI_KURSIYER": 60, "OGRETMEN": 10})
    )
    with pytest.raises(ValueError, match="toplamı"):
        _yaz_duzeltme(kurul)
    gk.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        degerler={"first_attendee_count": 71, "attendance_by_kind.OGRETMEN": 11},
        justification="Uydurma: bir öğretmen geç imzaladı.",
    )
    sonra = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (sonra.first_attendee_count, sonra.attendance_by_kind) == (
        71,
        {"VELI_KURSIYER": 60, "OGRETMEN": 11},
    )
    assert gk.ilk_girilen_deger(sonra, "attendance_by_kind.OGRETMEN") == 10
    assert gk.ilk_girilen_deger(sonra, "attendance_by_kind.VELI_KURSIYER") == 60

    with pytest.raises(ValueError, match="seçilen toplantının"):
        gk.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.IKINCI,
            degerler={"observer_count": 2},
            justification="Uydurma.",
        )


def test_ikinci_toplantinin_katilimi_dagilimla_duzeltilir() -> None:
    """Pilot akışı: birinci toplantıda yeter sayı yok, genel kurul ikinci toplantıda yapılır. Dağılım
    ikinci toplantınındır: ikinci toplantının katılımı dağılımla birlikte düzeltilir, toplamı ikinci
    katılımı tutmayan dağılım reddedilir, dağılım birinci toplantı adıyla düzeltilemez. Kararların
    paydası ikinci toplantının katılımıdır: birincinin katılımı oyların altına inebilir, ikincininki
    inemez (hesap bütünlüğü)."""
    kurul = gko.ilanli_olagan(second_meeting_at=gko.an(date(2026, 11, 3)))
    gk.birinci_toplanti(kurul, katilim=gko.katilim(10))
    gk.ikinci_toplanti(kurul, katilim=gko.katilim(5, dagilim={"VELI_KURSIYER": 4, "OGRETMEN": 1}))
    yetki = gko.madde(kurul, "YETKILENDIRME")
    assert gk.karar_sonucu_yaz(yetki, votes_for=4, votes_against=1).madde.result == "KABUL"
    with pytest.raises(ValueError, match="toplamı"):
        gk.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.IKINCI,
            degerler={"second_attendee_count": 7},
            justification="Uydurma: iki imza sonradan sayıldı.",
        )
    with pytest.raises(ValueError, match="seçilen toplantının"):
        gk.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.BIRINCI,
            degerler={"attendance_by_kind.OGRETMEN": 3},
            justification="Uydurma: iki imza sonradan sayıldı.",
        )
    assert not AttendanceCorrection.objects.exists()
    sonuc = gk.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.IKINCI,
        degerler={"second_attendee_count": 7, "attendance_by_kind.OGRETMEN": 3},
        justification="Uydurma: iki imza sonradan sayıldı.",
    )
    assert (sonuc.uyarilar, sonuc.bilgiler) == ((), ())
    sonra = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (
        sonra.status,
        sonra.held_at_meeting,
        sonra.first_attendee_count,
        sonra.second_attendee_count,
        sonra.attendance_by_kind,
    ) == (
        AssemblyStatus.YAPILDI,
        AssemblyMeeting.IKINCI,
        10,
        7,
        {"VELI_KURSIYER": 4, "OGRETMEN": 3},
    )
    satirlar = gk.katilim_duzeltmeleri(kurul)
    assert [(s.meeting, s.field, s.old_value, s.new_value) for s in satirlar] == [
        (AssemblyMeeting.IKINCI, "second_attendee_count", 5, 7),
        (AssemblyMeeting.IKINCI, "attendance_by_kind.OGRETMEN", 1, 3),
    ]
    assert gk.ilk_girilen_deger(sonra, "second_attendee_count") == 5
    assert gk.ilk_girilen_deger(sonra, "attendance_by_kind.OGRETMEN") == 1
    # Birinci toplantının katılımı kararların paydası değildir: oyların (5) altına inebilir, karar
    # yeniden hesaplanmaz. İkinci toplantının katılımı paydadır: oyların altına inemez.
    gk.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        degerler={"first_attendee_count": 3},
        justification="Uydurma: mükerrer imzalar.",
    )
    assert AgendaItem.objects.get(pk=yetki.pk).result == "KABUL"
    with pytest.raises(ValueError, match="altına düzeltilemez"):
        gk.katilim_duzelt(
            kurul,
            toplanti=AssemblyMeeting.IKINCI,
            degerler={"second_attendee_count": 4, "attendance_by_kind.OGRETMEN": 0},
            justification="Uydurma: mükerrer imzalar.",
        )
    assert GeneralAssembly.objects.get(pk=kurul.pk).second_attendee_count == 7


def _karar_duzelt(
    kurul: GeneralAssembly, sayi: int, gerekce: uyum.Gerekce | None = None
) -> gk.GenelKurulSonucu:
    return gk.katilim_duzelt(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        degerler={"first_attendee_count": sayi},
        justification="Uydurma: katılım cetveli yeniden sayıldı.",
        gerekce=gerekce,
    )


def test_duzeltme_karar_paydasini_degistirince_sonuc_yeniden_hesaplanir() -> None:
    """Kullanıcı kararı S6 (iii) (sert — hesap bütünlüğü): karar sonucu oylardan hesaplanır, oylarla
    çelişen sonuç kayıtta durmaz. Salondaki sayısı girilmemiş maddenin paydası genel kurulun
    yapıldığı toplantının katılımıdır; bu sayı düzeltilince sonuç aynı işlemde yeni paydayla yeniden
    hesaplanıp yazılır. Sonucu değiştiren düzeltme uyarı + gerekçedir (plan F2 §5.1; akış satırı,
    konusu düzeltme satırı; maddenin iz satırı ona bağlı); gerekçesiz ret hiçbir şey yazmaz.
    Oyların, salondaki sayının ve gündem değişikliği oylarının toplamı yeni katılımı aşamaz (sert)."""
    kurul = gko.yapilmis_olagan()  # katılım 70
    yetki = gko.madde(kurul, "YETKILENDIRME")
    assert gk.karar_sonucu_yaz(yetki, votes_for=36, votes_against=30).madde.result == "KABUL"
    with pytest.raises(ValueError, match="altına düzeltilemez"):
        _karar_duzelt(kurul, 65)  # kabul + ret = 66
    # Salondaki sayısı girilmiş madde: payda salondaki sayıdır, katılım onun altına inemez.
    eklenen = gk.gundeme_madde_ekle(
        kurul, title="Uydurma: okul bahçesi", change_votes_for=40, change_votes_against=10
    ).madde
    gk.karar_sonucu_yaz(eklenen, votes_for=35, votes_against=20, present_count=68)
    with pytest.raises(ValueError, match="altına düzeltilemez"):
        _karar_duzelt(kurul, 67)
    # Gündem değişikliğinin oyları da katılımı aşamaz.
    gk.gundemden_madde_cikar(gko.madde(kurul, "DILEK"), change_votes_for=60, change_votes_against=9)
    with pytest.raises(ValueError, match="altına düzeltilemez"):
        _karar_duzelt(kurul, 68)
    assert not AttendanceCorrection.objects.exists()

    # 36/75 çoğunluk değildir: sonuç ret olur; gerekçesiz ret hiçbir şey yazmaz.
    with pytest.raises(GerekceGerekli):
        _karar_duzelt(kurul, 75)
    assert not AttendanceCorrection.objects.exists()
    assert AgendaItem.objects.get(pk=yetki.pk).result == "KABUL"
    sonuc = _karar_duzelt(kurul, 75, gko.GEREKCE)
    assert [u["kural"] for u in sonuc.uyarilar] == [gk.DUZELTME_KARAR_AKISI]
    assert len(sonuc.bilgiler) == 1
    assert "(Kabul → Ret)" in sonuc.bilgiler[0]
    sonra = AgendaItem.objects.get(pk=yetki.pk)
    assert (sonra.result, sonra.votes_for, sonra.votes_against, sonra.present_count) == (
        "RET",
        36,
        30,
        None,
    )
    assert AgendaItem.objects.get(pk=eklenen.pk).result == "KABUL"  # payda salondaki sayı
    duzeltme = AttendanceCorrection.objects.get()
    satir = ComplianceItem.objects.get(rule_id=gk.DUZELTME_KARAR_AKISI)
    assert (satir.kind, satir.subject_type, satir.subject_id) == (
        ComplianceKind.SAPMA,
        "oab.AttendanceCorrection",
        str(duzeltme.pk),
    )
    madde_izi = AuditTrail.objects.filter(model="oab.AgendaItem", object_id=str(yetki.pk)).latest(
        "pk"
    )
    assert madde_izi.compliance_item_id == satir.pk
    assert "result" in madde_izi.changed_fields
    # Aynı oyların yeniden yazımı aynı sonucu hesaplar (kayıt oylarla tutarlıdır).
    assert gk.karar_sonucu_yaz(yetki, votes_for=36, votes_against=30).madde.result == "RET"

    # Sonucu değiştirmeyen düzeltme (36/72 yine çoğunluk değil) uyarısızdır.
    sonuc = _karar_duzelt(kurul, 72)
    assert (sonuc.uyarilar, sonuc.bilgiler) == ((), ())
    # Ters yönde de (36/71 çoğunluk) gerekçe ister ve sonuç kabul olur.
    with pytest.raises(GerekceGerekli):
        _karar_duzelt(kurul, 71)
    assert AgendaItem.objects.get(pk=yetki.pk).result == "RET"
    sonuc = _karar_duzelt(kurul, 71, gko.GEREKCE)
    assert "(Ret → Kabul)" in sonuc.bilgiler[0]
    assert AgendaItem.objects.get(pk=yetki.pk).result == "KABUL"
    assert ComplianceItem.objects.filter(rule_id=gk.DUZELTME_KARAR_AKISI).count() == 2


def test_kapanmis_donemde_duzeltme_ve_tutanak_yazimlari_reddedilir() -> None:
    """O2 dönem kilidi: genel kurulun dönemi kapanmışsa düzeltme, karar, gündem ve divan yazılmaz
    (`DonemKapali`); ret satır yazmaz."""
    kurul = gko.yapilmis_olagan()
    assert kurul.term_id is not None
    OabTerm.objects.filter(pk=kurul.term_id).update(
        status=TermStatus.KAPANDI, end_date=date(2027, 10, 1)
    )
    for yazim in _TUTANAK_YAZIMLARI.values():
        with pytest.raises(DonemKapali):
            yazim(kurul)
    assert not AttendanceCorrection.objects.exists()
    assert not OrganMembership.objects.filter(organ=OrganType.DIVAN).exists()
