"""Denetleme Kurulu kuralları (`dk`, tasarım §6.4.3, §10.3; F1c 5. adım: bileşim ve başkanlık sayacı).

Veli koltuğu veli ya da 18 yaşını doldurmuş kursiyer, hayırsever değil; öğretmen koltuğu öğretmen
(SERT, md. 14/1). Grubun hücresi doluysa fazlası da SERT'tir. Başka okulun öğretmeninin MEM onay no'su
girilmemişse EKSİK'tir. Aynı kişi aynı dönemde yönetim kurulunda ve Denetleme Kurulunda olamaz (SERT,
kullanıcı kararı A-2; seçilip düşmüş üyelik de engeldir). Aynı kişi aynı dönemde Denetleme Kurulunda
tek koltuk tutar: veli ve öğretmen koltuğu aynı kişide olamaz (SERT, hesap bütünlüğü; kullanıcı kararı
10.11.2026). Kadro sayıları uyarıdır; sayılan kişidir.
Başkanlık sayacı yalnız Denetleme Kurulu başkanlığını sayar (md. 14/3) ve seçimde değil görev
bölümünde koşar (md. 14/1): seçimde görev verilmez, yedeğe hiç verilmez.

6. adım: başkanı Denetleme Kurulunun görev bölümü seçer (`gorev_bolumu.dk_gorev_bolumu`, yalnız Denetleme
Kurulu hesabıyla; başkanlık sayacı orada koşar), görev bölümü genel kuruldan sonraki ilk haftadadır,
görev süresi bir yıldır, öğretmenin başka kurumda dört aydan uzun görevlendirilmesi yedek önerisidir
ve yedeği yönetim kurulu kararı olmadan program yöneticisi çağırır (md. 14/6). Kişi adları UYDURMADIR.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.oab import selectors
from apps.oab.hatalar import GerekceGerekli, KuralSert
from apps.oab.kurallar import VERI_YOK
from apps.oab.models import (
    AssemblyKind,
    ComplianceItem,
    ComplianceKind,
    DecisionKind,
    ElectedBy,
    MeetingKind,
    MembershipStatus,
    OabPerson,
    OabTerm,
    OrganMembership,
    PersonKind,
    SeatGroup,
    SeatType,
)
from apps.oab.services import genel_kurul as genel_kurul_servisi
from apps.oab.services import gorev_bolumu, kurullar, uyelik_gecisleri, uyelikler
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import AccountRole, AuditTrail
from shared.exceptions import RolYetkisiz

pytestmark = pytest.mark.django_db

DK = "denetleme_kurulu"


def _dk_velisi(donem: OabTerm, kisi: OabPerson, **alanlar: Any) -> OrganMembership:
    """Genel kurulun seçtiği veli koltuğu (devralınan: aday şartı yok)."""
    return o.devralinan(donem, kisi, organ="DK", seat_group=SeatGroup.VELI, **alanlar)


def _satirlar(uyelik: OrganMembership, kural_id: str) -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(
            subject_type="oab.OrganMembership", subject_id=str(uyelik.pk), rule_id=kural_id
        ).order_by("pk")
    )


def _baskan_secer(uyelik: OrganMembership, gerekce: str = "") -> OrganMembership:
    """Denetleme Kurulunun görev bölümü (6. adım): asıl üyeler başkanı seçer, başkanlık sayacı orada
    koşar (md. 14/1, 14/3). Seçilme gününün ertesi günü (süre uyarısı yok)."""
    o.dk_gorev_bolumu(uyelik.term, uyelik, gun=date(2026, 10, 16), gerekce=gerekce)
    return OrganMembership.objects.get(pk=uyelik.pk)


def _dusur(uyelik: OrganMembership, tur: str = "ISTIFA") -> None:
    """Düşme servisi 6. adımda; durum makinesi geçişi ORM'le."""
    uyelik.status, uyelik.drop_kind = MembershipStatus.DUSTU, tur
    uyelik.save(update_fields=["status", "drop_kind"])


# ============================================================ kadro sayıları


@pytest.mark.parametrize(
    ("koltuk", "ad"),
    [
        pytest.param(
            SeatType.ASIL, "asıl", id="asil", marks=pytest.mark.kural_davranis(f"{DK}.asil_uye")
        ),
        pytest.param(
            SeatType.YEDEK,
            "yedek",
            id="yedek",
            marks=pytest.mark.kural_davranis(f"{DK}.yedek_uye"),
        ),
    ],
)
def test_dk_eksik_kadro_uyari(koltuk: str, ad: str) -> None:
    donem = o.donem()
    o.dk_ogretmeni(donem, o.ogretmen(), seat_type=koltuk)
    uyarilar = uyelikler.kadro_uyarilari(donem, "DK", tarih=o.SECIM_GUNU)
    mesajlar = [u["mesaj"] for u in uyarilar]
    assert f"Denetleme kurulunda 1 {ad} üye var; 3 {ad} üye olmalı." in mesajlar
    # Tam kadro (veli 1+1, öğretmen 2+2) uyarısızdır; görevdeki başkan da varsa eksik de yoktur.
    oteki = SeatType.YEDEK if koltuk == SeatType.ASIL else SeatType.ASIL
    for koltuk_ in (SeatType.ASIL, SeatType.YEDEK):
        rol = "BASKAN" if koltuk_ == SeatType.ASIL else "UYE"
        _dk_velisi(donem, o.kisi(), seat_type=koltuk_, role=rol)
    for ogretmen_koltugu in (koltuk, oteki, oteki):
        o.dk_ogretmeni(donem, o.ogretmen(), seat_type=ogretmen_koltugu)
    assert uyelikler.kadro_uyarilari(donem, "DK", tarih=o.SECIM_GUNU) == []


# ============================================================ koltuklar (md. 14/1)


@pytest.mark.kural_davranis(f"{DK}.koltuklar")
def test_veli_ogretmen_ayrimi() -> None:
    """Öğretmen koltuğuna öğretmen olmayan veli, veli koltuğuna veli olmayan öğretmen oturamaz;
    veli olan öğretmen veli koltuğuna oturabilir."""
    donem = o.donem()
    with pytest.raises(KuralSert) as hata:
        o.dk_ogretmeni(donem, o.kisi())
    assert "md. 14/1" in str(hata.value.detail)
    with pytest.raises(KuralSert):
        _dk_velisi(donem, o.ogretmen())
    veli_ogretmen = _dk_velisi(donem, o.ogretmen(is_parent=True))
    ogretmen = o.dk_ogretmeni(donem, o.ogretmen())
    assert {veli_ogretmen.seat_group, ogretmen.seat_group} == {"VELI", "OGRETMEN"}
    # 18 yaşını doldurmuş kursiyer veli koltuğuna oturur.
    _dk_velisi(donem, o.kisi(kind=PersonKind.KURSIYER, adult_declared=True), seat_type="YEDEK")
    assert OrganMembership.objects.count() == 3


@pytest.mark.kural_davranis(f"{DK}.koltuklar")
def test_veli_koltuguna_hayirsever_giremez() -> None:
    """OYS hayırseveri sayıyordu (envanter S-8); Denetleme Kurulunda hayırsever koltuğu yoktur."""
    donem = o.donem()
    with pytest.raises(KuralSert):
        _dk_velisi(donem, o.kisi(kind=PersonKind.HAYIRSEVER, is_parent=False))
    assert not OrganMembership.objects.exists()


@pytest.mark.kural_davranis(f"{DK}.koltuklar")
def test_dolu_ogretmen_koltuguna_ucuncu_asil_giremez() -> None:
    """Grubun hücresi (öğretmen asıl 2) doluysa fazlası sert; düşen koltuk boşalır."""
    donem = o.donem()
    ilk = o.dk_ogretmeni(donem, o.ogretmen())
    o.dk_ogretmeni(donem, o.ogretmen())
    with pytest.raises(KuralSert):
        o.dk_ogretmeni(donem, o.ogretmen())
    ilk.status, ilk.drop_kind = MembershipStatus.DUSTU, "BASKA_KURUMDA_GOREV"
    ilk.save(update_fields=["status", "drop_kind"])
    yeni = o.dk_ogretmeni(donem, o.ogretmen())
    assert yeni.status == MembershipStatus.SECILDI
    # Yedekten çağrılan asıl hücresindedir: bir asıl düşer, yedek çağrılır, hücre yine doludur.
    yedek = o.dk_ogretmeni(donem, o.ogretmen(), seat_type=SeatType.YEDEK)
    _dusur(yeni, "BASKA_KURUMDA_GOREV")
    yedek.promoted_on = o.SECIM_GUNU  # çağrı servisi 6. adımda (test_uyelikler emsali)
    yedek.save(update_fields=["promoted_on"])
    with pytest.raises(KuralSert):
        o.dk_ogretmeni(donem, o.ogretmen())
    # Çağrılan yedeğin kendi denetimi de asıl hücresine bakar: yedek hücresi dolu olsa da (iki
    # bekleyen yedek) onay no'sunun girilmesi koltuğu sert yapmaz.
    o.dk_ogretmeni(donem, o.ogretmen(), seat_type=SeatType.YEDEK)
    o.dk_ogretmeni(donem, o.ogretmen(), seat_type=SeatType.YEDEK)
    guncel = uyelikler.update_membership(yedek, mem_approval_no="Uydurma-2026/7")
    assert guncel.mem_approval_no == "Uydurma-2026/7"
    assert not _satirlar(yedek, f"{DK}.koltuklar")


@pytest.mark.kural_davranis(f"{DK}.koltuklar")
def test_baska_okul_ogretmeni_onay_no_ister() -> None:
    """MEM görevlendirmesiyle gelen öğretmenin onay no'su yoksa eksik (gerekçe istemez); onay no
    girilince eksik kapanır. Tür yine serttir."""
    donem = o.donem()
    uyelik = o.dk_ogretmeni(donem, o.ogretmen(), elected_by=ElectedBy.MEM_GOREVLENDIRME)
    satir = ComplianceItem.objects.get(subject_id=str(uyelik.pk), rule_id=f"{DK}.koltuklar")
    assert satir.kind == ComplianceKind.EKSIK and satir.resolved_at is None
    assert [u["durum"] for u in OrganMembership.objects.get(pk=uyelik.pk).rule_warnings] == [
        "eksik"
    ]
    uyelikler.update_membership(uyelik, mem_approval_no="Uydurma-2026/41")
    satir.refresh_from_db()
    assert satir.resolved_at is not None
    assert OrganMembership.objects.get(pk=uyelik.pk).rule_warnings == []
    # Onay no'su baştan girilmişse eksik açılmaz.
    ikinci = o.dk_ogretmeni(
        donem,
        o.ogretmen(),
        elected_by=ElectedBy.MEM_GOREVLENDIRME,
        mem_approval_no="Uydurma-2026/42",
    )
    assert not ComplianceItem.objects.filter(subject_id=str(ikinci.pk)).exists()
    # Veli koltuğunda MEM onay no'su yapısal olarak yoktur.
    with pytest.raises(ValueError, match="öğretmen koltuğunda"):
        uyelikler.update_membership(_dk_velisi(donem, o.kisi()), mem_approval_no="X-1")


# ============================================================ başkanlık sayacı (md. 14/3)


@pytest.mark.kural_davranis(f"{DK}.baskan_secilme_siniri")
def test_dk_baskan_siniri_farkli_organi_etkilemez() -> None:
    """OYS AYNEN: yönetim kurulu başkanlığı Denetleme Kurulu başkanlık sayacına girmez."""
    donem = o.donem()
    kisi = o.ogretmen(external_yk_terms=0, external_dk_chair_terms=0)
    o.gecmis_secilmeler(kisi, role="BASKAN", adet=4)
    uyelik = _baskan_secer(o.dk_ogretmeni(donem, kisi))  # gerekçesiz geçer
    assert (uyelik.status, uyelik.role) == (MembershipStatus.SECILDI, "BASKAN")
    assert uyelikler.dk_baskanlik_sayisi(kisi) == 1
    assert not ComplianceItem.objects.filter(subject_id=str(uyelik.pk)).exists()


@pytest.mark.kural_davranis(f"{DK}.baskan_secilme_siniri")
def test_dk_baskani_ucuncu_secimde_uyarisiz_dorduncude_uyari() -> None:
    donem = o.donem()
    ucuncu = o.ogretmen(external_dk_chair_terms=1)
    o.gecmis_secilmeler(ucuncu, organ="DK", role="BASKAN", adet=1, seat_group="OGRETMEN")
    _baskan_secer(o.dk_ogretmeni(donem, ucuncu))
    assert uyelikler.secilme_sayaci(ucuncu, "DK") == 3
    # Üyelik (başkanlık değil) sayılmaz.
    dorduncu = o.ogretmen(external_dk_chair_terms=2)
    o.gecmis_secilmeler(dorduncu, organ="DK", adet=3, seat_group="OGRETMEN")
    o.gecmis_secilmeler(dorduncu, organ="DK", role="BASKAN", adet=1, seat_group="OGRETMEN")
    uye = o.dk_ogretmeni(donem, dorduncu)
    assert not _satirlar(uye, f"{DK}.baskan_secilme_siniri")  # seçimde sayaç koşmaz (md. 14/1)
    with pytest.raises(GerekceGerekli) as hata:
        _baskan_secer(uye)
    assert "4 defa" in str(hata.value.detail) and "md. 14/3" in str(hata.value.detail)
    (satir,) = _satirlar(_baskan_secer(uye, "Uydurma gerekçe."), f"{DK}.baskan_secilme_siniri")
    assert satir.kind == ComplianceKind.SAPMA and satir.justification_group is not None


@pytest.mark.kural_davranis(f"{DK}.baskan_secilme_siniri")
def test_dk_baskanlik_beyani_bilinmiyorsa_eksik() -> None:
    """Beyan "bilinmiyor"sa (`None`) sayaç eksiktir, gerekçe istemez (R5); bilinen başkanlıklar
    sınırı zaten aşıyorsa uyarıdır."""
    donem = o.donem()
    kisi = o.ogretmen()  # external_dk_chair_terms = None
    o.gecmis_secilmeler(kisi, organ="DK", role="BASKAN", adet=1, seat_group="OGRETMEN")
    uyelik = _baskan_secer(o.dk_ogretmeni(donem, kisi))
    (satir,) = _satirlar(uyelik, f"{DK}.baskan_secilme_siniri")
    assert satir.kind == ComplianceKind.EKSIK and satir.justification_group is None
    assert uyelikler.secilme_sayaci(kisi, "DK") is None
    assert [u["durum"] for u in uyelik.rule_warnings] == ["eksik"]
    izler = AuditTrail.objects.filter(model="oab.OrganMembership", object_id=str(uyelik.pk))
    son_iz = izler.order_by("seq").last()
    assert son_iz is not None and "rule_warnings" in son_iz.changed_fields  # özet izli
    asan = o.ogretmen()
    o.gecmis_secilmeler(asan, organ="DK", role="BASKAN", adet=3, seat_group="OGRETMEN")
    with pytest.raises(GerekceGerekli):
        _baskan_secer(o.dk_ogretmeni(donem, asan))


@pytest.mark.kural_davranis(f"{DK}.baskan_secilme_siniri")
def test_donem_ici_a_b_a_donusunde_a_iki_kez_sayilir() -> None:
    """Her görev bölümündeki başkan seçimi bir seçilmedir (md. 14/3 "seçilebilir"; kullanıcı kararı
    10.11.2026): aynı dönemde A → B → A dönüşünde A iki kez sayılır, başkanlığı bırakmak seçilmeyi
    sayaçtan düşürmez. Geçmiş bir başkanlıkla A'nın dönemdeki ikinci seçilmesi (toplam üç) uyarısız,
    üçüncüsü (toplam dört) uyarı + gerekçedir; gerekçesiz deneme işlemi geri alır."""
    donem = o.donem()
    a = o.ogretmen(external_dk_chair_terms=0)
    o.gecmis_secilmeler(a, organ="DK", role="BASKAN", adet=1, seat_group="OGRETMEN")
    a_uyelik = o.dk_ogretmeni(donem, a)
    b_uyelik = o.dk_ogretmeni(donem, o.ogretmen(external_dk_chair_terms=0))
    _baskan_secer(a_uyelik)  # A: ikinci başkanlık
    assert uyelikler.dk_baskanlik_sayisi(a) == 2
    o.dk_gorev_bolumu(donem, b_uyelik, gun=date(2026, 10, 17))  # B
    assert OrganMembership.objects.get(pk=a_uyelik.pk).role == "UYE"
    assert uyelikler.dk_baskanlik_sayisi(a) == 2  # bırakılan başkanlık düşmez
    o.dk_gorev_bolumu(donem, a_uyelik, gun=date(2026, 11, 2))  # yeniden A: üçüncü, uyarısız
    guncel = OrganMembership.objects.get(pk=a_uyelik.pk)
    assert (guncel.role, guncel.chair_elections) == ("BASKAN", 2)
    assert uyelikler.dk_baskanlik_sayisi(a) == 3
    assert not _satirlar(guncel, f"{DK}.baskan_secilme_siniri")
    o.dk_gorev_bolumu(donem, b_uyelik, gun=date(2026, 11, 3))  # B
    with pytest.raises(GerekceGerekli) as hata:
        o.dk_gorev_bolumu(donem, a_uyelik, gun=date(2026, 11, 4))  # A: dördüncü
    assert "4 defa" in str(hata.value.detail) and "md. 14/3" in str(hata.value.detail)
    assert OrganMembership.objects.get(pk=a_uyelik.pk).chair_elections == 2  # geri alındı
    o.dk_gorev_bolumu(donem, a_uyelik, gun=date(2026, 11, 4), gerekce="Uydurma gerekçe.")
    assert uyelikler.dk_baskanlik_sayisi(a) == 4
    (satir,) = _satirlar(a_uyelik, f"{DK}.baskan_secilme_siniri")
    assert satir.kind == ComplianceKind.SAPMA and satir.justification_group is not None


@pytest.mark.kural_davranis(f"{DK}.baskan_secilme_siniri")
def test_gorevdeki_baskanin_yeniden_secilmesi_sayilmaz() -> None:
    """Görevdeki başkanın yeni görev bölümünde yeniden başkan seçilmesi (A → A) yeni seçilme değildir:
    dönem içinde başka bir görev için yapılan görev bölümü süren başkanlığı sınıra yaklaştırmaz (plan
    F1c 6. adım notları). Sınırdaki başkan bu yüzden gerekçe istenmeden yeniden seçilir."""
    donem = o.donem()
    a = o.ogretmen(external_dk_chair_terms=2)
    a_uyelik = _baskan_secer(o.dk_ogretmeni(donem, a))  # üçüncü başkanlık: uyarısız
    assert uyelikler.dk_baskanlik_sayisi(a) == 1
    o.dk_gorev_bolumu(donem, a_uyelik, gun=date(2026, 10, 20))  # A → A: gerekçesiz geçer
    o.dk_gorev_bolumu(donem, a_uyelik, gun=date(2027, 1, 15))
    guncel = OrganMembership.objects.get(pk=a_uyelik.pk)
    assert (guncel.role, guncel.chair_elections) == ("BASKAN", 1)
    assert uyelikler.secilme_sayaci(a, "DK") == 3
    assert not _satirlar(guncel, f"{DK}.baskan_secilme_siniri")


@pytest.mark.kural_davranis(f"{DK}.baskan_secilme_siniri")
def test_gecmiste_secilip_gorevi_birakilan_baskanlik_sayilir() -> None:
    """Dördüncü seçilme uyarıdır: geçmiş dönemlerde üç başkan seçilmesi, biri sonradan görevi
    bırakmış (rolü üye, `chair_elections` bir)."""
    donem = o.donem()
    c = o.ogretmen(external_dk_chair_terms=0)
    o.gecmis_secilmeler(c, organ="DK", role="BASKAN", adet=2, seat_group="OGRETMEN")
    o.gecmis_secilmeler(c, organ="DK", role="UYE", adet=1, seat_group="OGRETMEN", chair_elections=1)
    assert uyelikler.dk_baskanlik_sayisi(c) == 3
    with pytest.raises(GerekceGerekli) as hata:
        _baskan_secer(o.dk_ogretmeni(donem, c))
    assert "4 defa" in str(hata.value.detail)


@pytest.mark.kural_davranis(f"{DK}.baskan_secilme_siniri")
def test_dusen_baskanlik_sayaca_girer() -> None:
    """Seçilip düşmüş başkanlık sayılır (§15 B-12); istifa sayacı sıfırlamaz."""
    donem = o.donem()
    kisi = o.ogretmen(external_dk_chair_terms=0)
    o.gecmis_secilmeler(kisi, organ="DK", role="BASKAN", adet=2, seat_group="OGRETMEN")
    (dusen,) = o.gecmis_secilmeler(kisi, organ="DK", role="BASKAN", adet=1, seat_group="OGRETMEN")
    _dusur(dusen)
    assert uyelikler.dk_baskanlik_sayisi(kisi) == 3
    with pytest.raises(GerekceGerekli):
        _baskan_secer(o.dk_ogretmeni(donem, kisi))


def test_secimde_gorev_verilmez_yedege_hic_verilmez() -> None:
    """Başkanı asıl üyeler görev bölümünde seçer (md. 14/1); öğretmenler kurulu ya da genel kurul
    seçmez, yedek başkan olmaz. Uç da aynı yapısal retten geçer."""
    donem = o.donem()
    with pytest.raises(ValueError, match="görev bölümünde"):
        o.dk_ogretmeni(donem, o.ogretmen(), role="BASKAN")
    with pytest.raises(ValueError, match="yedek üye çağrılmadan"):
        o.dk_ogretmeni(donem, o.ogretmen(), role="BASKAN", seat_type=SeatType.YEDEK)
    with pytest.raises(ValueError, match="yedek üye çağrılmadan"):
        _dk_velisi(donem, o.kisi(), role="BASKAN", seat_type=SeatType.YEDEK)
    # Devralınan asıl görevle girilir (geçişte görev bölümü yapılmıştır; tasarım §7.9 adım 2).
    assert _dk_velisi(donem, o.kisi(), role="BASKAN").role == "BASKAN"
    assert OrganMembership.objects.count() == 1
    govde = {
        "term": donem.pk,
        "person": o.ogretmen().pk,
        "organ": "DK",
        "seat_type": "ASIL",
        "seat_group": "OGRETMEN",
        "role": "BASKAN",
        "elected_by": "OGRETMENLER_KURULU",
        "start_date": "2026-10-15",
    }
    for alanlar in ({}, {"seat_type": "YEDEK"}):
        yanit = APIClient().post("/api/v1/oab/memberships/", {**govde, **alanlar}, format="json")
        assert yanit.status_code == 400, yanit.json()
        assert "görev" in str(yanit.json()).lower()
    assert OrganMembership.objects.count() == 1


# ============================================================ aynı kişi iki koltukta (tek koltuk)


@pytest.mark.parametrize("sira", ["veli-once", "ogretmen-once"])
def test_ayni_kisi_veli_ve_ogretmen_koltugunda_olamaz(sira: str) -> None:
    """Veli olan öğretmen hem veli koltuğuna (genel kurul) hem öğretmen koltuğuna (öğretmenler
    kurulu) seçilemez: bir kişi aynı dönemde aynı kurulda tek koltuk tutar (sert, hesap bütünlüğü;
    kullanıcı kararı 10.11.2026). Aday kaydı koltuk değildir; ret ikinci koltuğun seçildiği anda
    olur ve işlem geri alınır."""
    donem = o.donem()
    kisi = o.ogretmen(is_parent=True)
    kurul = o.olaganustu_genel_kurul(donem)

    def veli_adayi() -> OrganMembership:
        return uyelikler.assign_membership(
            term=donem,
            person=kisi,
            organ="DK",
            seat_type=SeatType.ASIL,
            seat_group=SeatGroup.VELI,
            elected_by=ElectedBy.GENEL_KURUL,
            assembly=kurul,
        )

    if sira == "veli-once":
        uyelikler.elect_membership(veli_adayi(), start_date=o.SECIM_GUNU)
        with pytest.raises(ValueError, match="tek koltuk"):
            o.dk_ogretmeni(donem, kisi)
        kalan = {MembershipStatus.SECILDI: 1}
    else:
        o.dk_ogretmeni(donem, kisi)
        aday = veli_adayi()  # aday kaydı koltuk değil
        with pytest.raises(ValueError, match="tek koltuk"):
            uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
        assert OrganMembership.objects.get(pk=aday.pk).status == MembershipStatus.ADAY
        kalan = {MembershipStatus.SECILDI: 1, MembershipStatus.ADAY: 1}
    durumlar = list(OrganMembership.objects.filter(person=kisi).values_list("status", flat=True))
    assert {d: durumlar.count(d) for d in set(durumlar)} == kalan
    assert selectors.kadro_sayilari(donem, "DK")[SeatType.ASIL] == 1
    if sira == "veli-once":
        # Uç da aynı retten geçer: 400, Türkçe ileti, kayıt yazılmaz.
        yanit = APIClient().post(
            "/api/v1/oab/memberships/",
            {
                "term": donem.pk,
                "person": kisi.pk,
                "organ": "DK",
                "seat_type": "YEDEK",
                "seat_group": "OGRETMEN",
                "elected_by": "OGRETMENLER_KURULU",
                "start_date": "2026-10-15",
            },
            format="json",
        )
        assert yanit.status_code == 400, yanit.json()
        assert uyelikler.TEK_KOLTUK in str(yanit.json())
        assert OrganMembership.objects.filter(person=kisi).count() == 1


# ============================================================ aynı dönemde iki kurul (A-2)


@pytest.mark.kural_davranis(f"{DK}.yk_uyesi_olamaz")
def test_yk_uyesi_dk_ye_eklenemez() -> None:
    donem = o.donem()
    kisi = o.kisi(kind=PersonKind.OGRETMEN, is_parent=True)
    o.devralinan(donem, kisi)
    with pytest.raises(KuralSert):
        _dk_velisi(donem, kisi)
    with pytest.raises(KuralSert):
        o.dk_ogretmeni(donem, kisi)
    assert OrganMembership.objects.count() == 1


@pytest.mark.kural_davranis(f"{DK}.yk_uyesi_olamaz")
def test_dk_uyesi_yk_ye_eklenemez() -> None:
    """Seçilmiş Denetleme Kurulu üyesi yönetim kuruluna aday da olamaz; düşmesi de engeli kaldırmaz
    (kullanıcı kararı A-2'nin lafzı "aynı dönemde")."""
    donem = o.donem()
    kisi = o.kisi()
    dk = _dk_velisi(donem, kisi)
    with pytest.raises(KuralSert):
        o.devralinan(donem, kisi)
    kurul = o.olaganustu_genel_kurul(donem)
    with pytest.raises(KuralSert):
        o.yk_adayi(donem, kisi, kurul)
    _dusur(dk)
    with pytest.raises(KuralSert):
        o.yk_adayi(donem, kisi, kurul)
    assert OrganMembership.objects.filter(person=kisi).count() == 1


@pytest.mark.kural_davranis(f"{DK}.yk_uyesi_olamaz")
def test_yk_den_dusen_ayni_donemde_dk_ye_giremez() -> None:
    """Denetleyen ile denetlenen ayrılığı (md. 14/4): yönetim kurulundan düşen, kendi üye olduğu
    dönemin Denetleme Kurulunun veli ya da öğretmen koltuğuna giremez."""
    donem = o.donem()
    kisi = o.kisi(kind=PersonKind.OGRETMEN, is_parent=True)
    _dusur(o.devralinan(donem, kisi))
    with pytest.raises(KuralSert):
        _dk_velisi(donem, kisi)
    with pytest.raises(KuralSert):
        o.dk_ogretmeni(donem, kisi)
    kurul = o.olaganustu_genel_kurul(donem)
    with pytest.raises(KuralSert):
        uyelikler.assign_membership(
            term=donem,
            person=kisi,
            organ="DK",
            seat_type=SeatType.ASIL,
            seat_group=SeatGroup.VELI,
            elected_by=ElectedBy.GENEL_KURUL,
            assembly=kurul,
        )
    assert OrganMembership.objects.count() == 1


@pytest.mark.kural_davranis(f"{DK}.yk_uyesi_olamaz")
def test_iptal_kayit_engel_degil() -> None:
    """İptal edilmiş kayıt hiç olmamıştır (yanlış kayıt): öteki kurula girişi engellemez."""
    donem = o.donem()
    kisi = o.kisi(kind=PersonKind.OGRETMEN, is_parent=True)
    yanlis = o.devralinan(donem, kisi)
    yanlis.status = MembershipStatus.IPTAL
    yanlis.save(update_fields=["status"])
    assert o.dk_ogretmeni(donem, kisi).status == MembershipStatus.SECILDI


@pytest.mark.kural_davranis(f"{DK}.yk_uyesi_olamaz")
def test_aday_secilirken_oteki_kurul_yeniden_denetlenir() -> None:
    """Aday kaydı engel değildir; seçilme anında öteki kurulda seçilmiş üyelik sert."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    kurul = o.olaganustu_genel_kurul(donem)
    aday = o.yk_adayi(donem, kisi, kurul)
    _dk_velisi(donem, kisi)  # aday kaydı engel değil
    with pytest.raises(KuralSert):
        uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)


@pytest.mark.kural_davranis(f"{DK}.yk_uyesi_olamaz")
def test_ekim_2026_genel_kurulunda_da_gecerli() -> None:
    """Yürürlük paket metninin tarihidir (01.12.2023): 15.10.2026 genel kurulu da kapsanır (MA-1)."""
    donem = o.donem()
    kurul = genel_kurul_servisi.genel_kurul_olustur(
        donem=donem,
        kind=AssemblyKind.OLAGANUSTU,
        first_meeting_at=datetime(2026, 10, 15, 7, 0, tzinfo=UTC),
    )
    kisi = o.kisi(external_yk_terms=0)
    o.devralinan(donem, kisi, organ="DK", seat_group=SeatGroup.VELI)
    with pytest.raises(KuralSert):
        o.yk_adayi(donem, kisi, kurul)


@pytest.mark.kural_davranis(f"{DK}.yk_uyesi_olamaz")
def test_atif_kullanici_karari_a2_diye_basilir() -> None:
    donem = o.donem()
    kisi = o.kisi()
    o.devralinan(donem, kisi)
    with pytest.raises(KuralSert) as hata:
        _dk_velisi(donem, kisi)
    metin = str(hata.value.detail)
    assert "kullanıcı kararı A-2 (gerekçe md. 14/4)" in metin
    assert "Yönetmelik gereği" not in metin


# ============================================================ 6. adım: görev bölümü (md. 14/1)


@pytest.mark.kural_davranis(f"{DK}.gorev_bolumu_gun")
def test_dk_gorev_bolumu_7_gun_uyarisiz() -> None:
    """Asıl üyeler genel kuruldan sonraki ilk hafta içinde toplanır (md. 14/1; yorum KE-12): süre
    dönemi açan genel kuruldan (10.10.2026) sayılır, üyelerin seçilme gününden (15.10.2026) değil.
    7. gün (17.10) uyarısız."""
    donem = o.donem()
    veli, *_ = o.dk_kurulu(donem)
    sonuc = o.dk_gorev_bolumu(donem, veli, gun=date(2026, 10, 17), plan=[date(2027, 2, 15)])
    assert not ComplianceItem.objects.filter(rule_id=f"{DK}.gorev_bolumu_gun").exists()
    assert sonuc.toplanti.organ == "DK" and sonuc.karar.status == "TASLAK"
    assert OabTerm.objects.get(pk=donem.pk).dk_audit_plan_dates == ["2027-02-15"]


@pytest.mark.kural_davranis(f"{DK}.gorev_bolumu_gun")
def test_dk_gorev_bolumu_8_gun_uyari() -> None:
    """Genel kuruldan sonra 8. gün (18.10; üyelerin seçilmesinden 3 gün sonra) uyarı + gerekçedir;
    uyum satırının konusu görev bölümü toplantısıdır."""
    donem = o.donem()
    veli, *_ = o.dk_kurulu(donem)
    with pytest.raises(GerekceGerekli) as hata:
        o.dk_gorev_bolumu(donem, veli, gun=date(2026, 10, 18))
    assert "8 gün" in str(hata.value.detail) and "md. 14/1" in str(hata.value.detail)
    sonuc = o.dk_gorev_bolumu(donem, veli, gun=date(2026, 10, 18), gerekce="Uydurma gerekçe.")
    (satir,) = ComplianceItem.objects.filter(
        rule_id=f"{DK}.gorev_bolumu_gun", subject_id=str(sonuc.toplanti.pk)
    )
    assert satir.subject_type == "oab.BoardMeeting" and satir.kind == ComplianceKind.SAPMA


@pytest.mark.kural_davranis(f"{DK}.gorev_bolumu_gun")
def test_dk_yedek_cagrisindan_sonraki_gorev_bolumu_sureye_bagli_degil() -> None:
    """md. 14/1 süreyi yalnız genel kuruldan sonraki ilk görev bölümüne koyar; md. 14/6 yedek
    çağrısından sonra süre öngörmez: yeniden görev bölümü uyarı ve gerekçe istemez."""
    donem = o.donem()
    veli, ogretmen1, _ = o.dk_kurulu(donem)
    o.dk_gorev_bolumu(donem, veli, gun=date(2026, 10, 16))
    yedek = o.secilmis(donem, organ="DK", seat_group=SeatGroup.OGRETMEN, seat_type=SeatType.YEDEK)
    uyelik_gecisleri.uyeligi_dusur(
        ogretmen1, drop_kind="BASKA_KURUMDA_GOREV", end_date=date(2027, 3, 1)
    )
    uyelik_gecisleri.yedek_cagir(yedek, organ="DK", promoted_on=date(2027, 3, 2))
    sonuc = o.dk_gorev_bolumu(donem, yedek, gun=date(2027, 3, 20))
    assert not ComplianceItem.objects.filter(rule_id=f"{DK}.gorev_bolumu_gun").exists()
    assert OrganMembership.objects.get(pk=sonuc.uyelikler[0].pk).role == "BASKAN"


@pytest.mark.kural_davranis(f"{DK}.gorev_bolumu_gun")
@pytest.mark.parametrize(("gun", "uyari"), [(date(2027, 3, 8), False), (date(2027, 3, 9), True)])
def test_olaganustu_genel_kurulla_yenilenen_dk_suresi_o_genel_kuruldan(
    gun: date, uyari: bool
) -> None:
    """Süre kurulu seçen genel kuruldan sayılır (md. 14/1; kullanıcı kararı 10.11.2026): olağanüstü
    genel kurul (01.03.2027) Denetleme Kurulunun veli koltuğunu yenilediyse ilk görev bölümünün
    süresi o günden başlar; dönem içindeki önceki görev bölümü süreyi kapatmaz. 7. gün uyarısız,
    8. gün uyarı + gerekçe (ayrı kurulumlar)."""
    donem = o.donem()
    veli, *_ = o.dk_kurulu(donem)
    o.dk_gorev_bolumu(donem, veli, gun=date(2026, 10, 16))
    kurul = genel_kurul_servisi.genel_kurul_olustur(
        donem=donem,
        kind=AssemblyKind.OLAGANUSTU,
        first_meeting_at=datetime(2027, 3, 1, 7, 0, tzinfo=UTC),
    )
    uyelik_gecisleri.uyeligi_dusur(
        veli, drop_kind="OLAGANUSTU_GK_SECIMI", end_date=date(2027, 3, 1)
    )
    aday = uyelikler.assign_membership(
        term=donem,
        person=o.kisi(),
        organ="DK",
        seat_type=SeatType.ASIL,
        seat_group=SeatGroup.VELI,
        elected_by=ElectedBy.GENEL_KURUL,
        assembly=kurul,
    )
    yeni_veli = uyelikler.elect_membership(aday, start_date=date(2027, 3, 1))
    assert gorev_bolumu.dk_secen_genel_kurul_gunu(donem) == date(2027, 3, 1)
    if not uyari:
        sonuc = o.dk_gorev_bolumu(donem, yeni_veli, gun=gun)
        assert not ComplianceItem.objects.filter(rule_id=f"{DK}.gorev_bolumu_gun").exists()
        assert OrganMembership.objects.get(pk=sonuc.uyelikler[0].pk).role == "BASKAN"
        return
    with pytest.raises(GerekceGerekli) as hata:
        o.dk_gorev_bolumu(donem, yeni_veli, gun=gun)
    assert "8 gün" in str(hata.value.detail) and "md. 14/1" in str(hata.value.detail)
    sonuc = o.dk_gorev_bolumu(donem, yeni_veli, gun=gun, gerekce="Uydurma gerekçe.")
    (satir,) = ComplianceItem.objects.filter(rule_id=f"{DK}.gorev_bolumu_gun")
    assert satir.subject_id == str(sonuc.toplanti.pk) and satir.kind == ComplianceKind.SAPMA


def test_dk_suresinin_referansi_olagan_ya_da_devralinan_kurulda_donem_basi() -> None:
    """Veli koltuğu devralınan (genel kurul bağı yok) ya da boş kurulda referans dönemi açan genel
    kurulun günüdür (`OabTerm.start_date`)."""
    donem = o.donem()
    veli, *_ = o.dk_kurulu(donem)
    assert gorev_bolumu.dk_secen_genel_kurul_gunu(donem) == o.GUN
    uyelik_gecisleri.uyeligi_dusur(veli, drop_kind="ISTIFA", end_date=date(2026, 11, 1))
    assert gorev_bolumu.dk_secen_genel_kurul_gunu(donem) == o.GUN


@pytest.mark.kural_davranis(f"{DK}.gorev_bolumu_gun")
def test_dk_baskansiz_kadro_okumasinda_eksik() -> None:
    """Görevdeki asıllar arasında başkan yoksa (görev bölümü henüz yapılmadı ya da başkan düştü) kadro
    okumasında eksiktir: atıf md. 14/1, gerekçe istemez, uyum satırı açılmaz (plan F1c 6. adım
    notları)."""
    donem = o.donem()
    veli, *_ = o.dk_kurulu(donem)

    def eksikler() -> list[tuple[str, str]]:
        return [
            (s["mesaj"], s["atif"])
            for s in uyelikler.kadro_uyarilari(donem, "DK", tarih=date(2026, 12, 1))
            if s["durum"] == "eksik"
        ]

    beklenen = [(uyelikler.BASKAN_YOK["DK"], "md. 14/1")]
    assert eksikler() == beklenen
    o.dk_gorev_bolumu(donem, veli, gun=date(2026, 10, 16))
    assert eksikler() == []
    uyelik_gecisleri.uyeligi_dusur(veli, drop_kind="ISTIFA", end_date=date(2026, 11, 1))
    assert eksikler() == beklenen
    assert not ComplianceItem.objects.filter(kind=ComplianceKind.EKSIK).exists()


def test_gorev_bolumu_suresi_donem_basi_yoksa_eksik() -> None:
    """Dönem başı (genel kurul günü) bilinmiyorsa süre ve görev süresi eksiktir (gerekçe istemez, R5);
    sapma açılmaz. Hazırlıktaki dönemde görev bölümü yazılmaz; ölçü doğrudan sınanır."""
    donem = o.donem()
    OabTerm.objects.filter(pk=donem.pk).update(
        status="HAZIRLIK", start_date=None, end_date=None, program_start_date=None
    )
    hazirlik = OabTerm.objects.get(pk=donem.pk)
    assert gorev_bolumu._sure_gozlenen(hazirlik, "DK", date(2026, 10, 20)) is VERI_YOK
    assert uyelikler.gorev_suresi_gozlenen(hazirlik, date(2026, 10, 20)) is VERI_YOK


def test_denetim_plani_donem_basindan_once_olamaz() -> None:
    """Denetim planı tarihleri dönem başından önce olamaz (sert, tarih sırası)."""
    donem = o.donem()
    veli, *_ = o.dk_kurulu(donem)
    with pytest.raises(ValueError, match="döneminin başından önce"):
        o.dk_gorev_bolumu(donem, veli, gun=date(2026, 10, 16), plan=[date(2026, 10, 1)])
    assert OabTerm.objects.get(pk=donem.pk).dk_audit_plan_dates in ([], None)


@pytest.mark.kural_davranis(f"{DK}.gorev_bolumu_gun")
def test_dk_gorev_bolumunu_yalniz_denetleme_kurulu_yazar() -> None:
    """YK rolleri ve program yöneticisi DK görev bölümünü yazmaz (tasarım §4.4.2 ⁵): servis kapısı
    (`Eylem.DK_GOREV_BOLUMU_YAZMA`) ve uç kuralı (M8) aynı sonucu verir; başkan tektir."""
    donem = o.donem()
    veli, ogretmen1, _ = o.dk_kurulu(donem)
    with pytest.raises(RolYetkisiz):
        gorev_bolumu.dk_gorev_bolumu(
            term=donem, held_at=o.saat(date(2026, 10, 16)), baskan=veli, katilim=[]
        )
    govde = {
        "held_at": "2026-10-16T15:00:00+03:00",
        "baskan": ogretmen1.pk,
        "katilim": [
            {"membership": u.pk, "present": True} for u in selectors.gorevdeki_asillar(donem, "DK")
        ],
        "denetim_plani": ["2027-01-15", "2027-05-15"],
    }
    yol = f"/api/v1/oab/terms/{donem.pk}/duty-assignment/dk/"
    assert APIClient().post(yol, govde, format="json").status_code == 403  # program yöneticisi
    with o.rol_olarak(AccountRole.SEKRETER):
        assert APIClient().post(yol, govde, format="json").status_code == 403
    o.dk_gorev_bolumu(donem, veli, gun=date(2026, 10, 16))
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        yanit = APIClient().post(yol, govde, format="json")
    assert yanit.status_code == 201, yanit.content
    roller = {u.pk: u.role for u in selectors.gorevdeki_asillar(donem, "DK")}
    assert roller[ogretmen1.pk] == "BASKAN" and roller[veli.pk] == "UYE"
    assert list(roller.values()).count("BASKAN") == 1
    assert OabTerm.objects.get(pk=donem.pk).dk_audit_plan_dates == ["2027-01-15", "2027-05-15"]


@pytest.mark.kural_davranis(f"{DK}.gorev_suresi_yil")
def test_dk_gorev_suresi_bitiminde_uyari() -> None:
    """Görev süresi bir yıldır (md. 14/2): yıl dönümünden bir gün önce uyarısız, yıl dönümünde uyarı."""
    donem = o.donem()
    o.dk_kurulu(donem)

    def sure(gun: date) -> list[str]:
        return [
            s["atif"]
            for s in uyelikler.kadro_uyarilari(donem, "DK", tarih=gun)
            if "görev süresi" in s["mesaj"]
        ]

    assert sure(date(2027, 10, 9)) == []
    assert sure(date(2027, 10, 10)) == ["md. 14/2"]


# ============================================================ başka kurumda görevlendirme (md. 14/6)


def _gorevlendirme_onerileri(uyelik: OrganMembership) -> list[str]:
    guncel = OrganMembership.objects.select_related("term__rule_package", "person").get(
        pk=uyelik.pk
    )
    return [x.metin for x in uyelik_gecisleri.oneriler(guncel) if x.tur == "YEDEK_CAGRISI"]


@pytest.mark.kural_davranis(f"{DK}.ogretmen_gorevlendirme_ay")
def test_4_ay_uyarisiz_4_ay_1_gun_yedek_onerisi() -> None:
    """Dört aydan fazla görevlendirmede yerine yedeği çağrılır (md. 14/6): 01.11.2026-28.02.2027 dört
    aydır, öneri yok; 01.03.2027 bitişi dört ay bir gündür, yedek çağrısı önerilir. Kayıt
    engellenmez, gerekçe istemez; görevlendirme günleri yalnız DK öğretmen koltuğundadır."""
    donem = o.donem()
    _, ogretmen1, _ = o.dk_kurulu(donem)
    dort = uyelikler.update_membership(
        ogretmen1,
        external_assignment_start=date(2026, 11, 1),
        external_assignment_end=date(2027, 2, 28),
    )
    assert _gorevlendirme_onerileri(dort) == []
    uyelikler.update_membership(ogretmen1, external_assignment_end=date(2027, 3, 1))
    (metin,) = _gorevlendirme_onerileri(ogretmen1)
    assert "yerine yedeği" in metin and "md. 14/6" in metin
    assert not ComplianceItem.objects.filter(rule_id=f"{DK}.ogretmen_gorevlendirme_ay").exists()
    with pytest.raises(ValueError, match="öğretmen koltuğunda"):
        uyelikler.update_membership(o.secilmis(donem), external_assignment_start=date(2026, 11, 1))
    with pytest.raises(ValueError, match="başlangıcından önce"):
        uyelikler.update_membership(ogretmen1, external_assignment_end=date(2026, 10, 1))


@pytest.mark.kural_davranis(f"{DK}.ogretmen_gorevlendirme_ay")
def test_dk_yedegi_cagrisi_yk_karari_istemez() -> None:
    """DK yedeğini yönetim kurulu kararı olmadan program yöneticisi çağırır (md. 14/6; tasarım E65):
    karar bağı verilmez, uyarı yok. Asıl hücresi doluysa çağrı serttir (önce ayrılan düşürülür).
    Uç yalnız program yöneticisinindir; yönetim kurulu yedeğinin ucu sekreterindir."""
    donem = o.donem()
    _, ogretmen1, _ = o.dk_kurulu(donem)
    yedek = o.secilmis(donem, organ="DK", seat_group=SeatGroup.OGRETMEN, seat_type=SeatType.YEDEK)
    with pytest.raises(KuralSert):
        uyelik_gecisleri.yedek_cagir(yedek, organ="DK", promoted_on=date(2027, 3, 2))
    uyelik_gecisleri.uyeligi_dusur(
        ogretmen1, drop_kind="BASKA_KURUMDA_GOREV", end_date=date(2027, 3, 1)
    )
    yk_toplantisi = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.AYLIK)
    karar = kurullar.karar_taslagi_olustur(yk_toplantisi, kind=DecisionKind.YEDEK_CAGIRMA)
    with pytest.raises(ValueError, match="yönetim kurulu kararıyla çağrılmaz"):
        uyelik_gecisleri.yedek_cagir(yedek, organ="DK", karar=karar)
    yol = f"/api/v1/oab/memberships/{yedek.pk}/substitute-call/dk/"
    with o.rol_olarak(AccountRole.SEKRETER):
        assert APIClient().post(yol, {}, format="json").status_code == 403
    yanit = APIClient().post(yol, {"promoted_on": "2027-03-02"}, format="json")
    assert yanit.status_code == 200, yanit.content
    assert (yanit.json()["promoted_on"], yanit.json()["promoted_by_decision"]) == (
        "2027-03-02",
        None,
    )
    assert not ComplianceItem.objects.filter(rule_id="yonetim_kurulu.yedek_cagirma").exists()
    assert yedek.pk in {u.pk for u in selectors.gorevdeki_asillar(donem, "DK")}
