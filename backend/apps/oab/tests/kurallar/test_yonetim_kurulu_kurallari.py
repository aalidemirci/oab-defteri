"""Yönetim kurulu kuralları (`yk`, tasarım §6.4.2, §10.3; F1c 5. adım: bileşim ve seçilme sayacı).

Bileşim: kim oturabilir (veli, 18 yaşını doldurmuş kursiyer, hayırsever; SERT), okul müdürü giremez
(SERT, kullanıcı kararı KE-15), dört görev görevdeki seçilmiş asıllar arasında tekildir (SERT), kadro
sayıları uyarıdır ve yalnız seçilmiş kayıt sayılır. Görev seçimde verilmez (md. 12/3): programda açılan
kayıt `UYE`'dir, görevli kayıt yalnız devralınan asıldır. Sayaç: başkan ve üye tek sayaç, asıl ve yedek
her seçilme; `SECILDI` ve `DUSTU` sayılır, `ADAY`, `IPTAL` ve `DEVRALINAN` sayılmaz; yalnız yönetim
kurulu seçilmeleri; programın kayıtları + beyan; beyan bilinmiyorsa eksik (R5).

Görev bölümü, yedek çağrısı, düşme, suç ve tek birlik engelleri, alım komisyonu 6. adımdadır. Kişi
adları UYDURMADIR.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.oab import selectors
from apps.oab.hatalar import GerekceGerekli, KuralSert
from apps.oab.models import (
    ComplianceItem,
    ComplianceKind,
    GeneralAssembly,
    MembershipStatus,
    OrganMembership,
    PersonKind,
    SeatType,
)
from apps.oab.services import kisiler, uyelikler, uyum
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import AuditTrail

pytestmark = pytest.mark.django_db

YK = "yonetim_kurulu"


def _satirlar(uyelik: OrganMembership, kural_id: str) -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(
            subject_type="oab.OrganMembership", subject_id=str(uyelik.pk), rule_id=kural_id
        ).order_by("pk")
    )


def _secilmis_yk(donem: Any, kisi: Any, **alanlar: Any) -> OrganMembership:
    """Genel kurulun aday kaydından seçilen yönetim kurulu üyesi (tek kaynak)."""
    kurul = alanlar.pop("kurul", None) or o.olaganustu_genel_kurul(donem)
    gerekce = alanlar.pop("gerekce", None)
    aday = o.yk_adayi(donem, kisi, kurul, **alanlar)
    return uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU, gerekce=gerekce)


# ============================================================ kadro sayıları


@pytest.mark.parametrize(
    ("koltuk", "kural"),
    [
        pytest.param(
            SeatType.ASIL,
            f"{YK}.asil_uye",
            id="asil",
            marks=pytest.mark.kural_davranis(f"{YK}.asil_uye"),
        ),
        pytest.param(
            SeatType.YEDEK,
            f"{YK}.yedek_uye",
            id="yedek",
            marks=pytest.mark.kural_davranis(f"{YK}.yedek_uye"),
        ),
    ],
)
def test_yk_eksik_kadro_uyari(koltuk: str, kural: str) -> None:
    """Eksik kadro uyarıdır: yazım engellenmez, kadro okumasında atıflı uyarı çıkar."""
    donem = o.donem()
    o.devralinan(donem, o.kisi(), seat_type=koltuk)
    uyarilar = uyelikler.kadro_uyarilari(donem, "YK", tarih=o.SECIM_GUNU)
    ad = "asıl" if koltuk == SeatType.ASIL else "yedek"
    ilgili = [u for u in uyarilar if f"{ad} üye var" in u["mesaj"]]
    assert len(ilgili) == 1 and ilgili[0]["durum"] == "uyari"
    assert ilgili[0]["atif"] == "md. 12/1"
    assert ilgili[0]["mesaj"] == f"Yönetim kurulunda 1 {ad} üye var; 5 {ad} üye olmalı."
    assert not ComplianceItem.objects.filter(rule_id=kural).exists()  # okuma satır yazmaz


@pytest.mark.kural_davranis(f"{YK}.asil_uye")
@pytest.mark.kural_davranis(f"{YK}.yedek_uye")
def test_yk_tam_kadro_uyarisiz() -> None:
    donem = o.donem()
    for koltuk in (SeatType.ASIL, SeatType.YEDEK):
        for _ in range(5):
            o.devralinan(donem, o.kisi(), seat_type=koltuk)
    assert uyelikler.kadro_uyarilari(donem, "YK", tarih=o.SECIM_GUNU) == []


@pytest.mark.kural_davranis(f"{YK}.asil_uye")
def test_dusen_koltuk_sayima_girmez() -> None:
    """OYS AYNEN: düşen koltuk sayılmaz; aday da sayılmaz (kadro sayımı yalnız `SECILDI`)."""
    donem = o.donem()
    asillar = [o.devralinan(donem, o.kisi()) for _ in range(5)]
    dusen = asillar[0]
    dusen.status, dusen.drop_kind = MembershipStatus.DUSTU, "ISTIFA"
    dusen.save(update_fields=["status", "drop_kind"])
    kurul = o.olaganustu_genel_kurul(donem)
    o.yk_adayi(donem, o.kisi(), kurul)  # aday sayılmaz
    sayilar = selectors.kadro_sayilari(donem, "YK")
    assert sayilar[SeatType.ASIL] == 4
    mesajlar = [u["mesaj"] for u in uyelikler.kadro_uyarilari(donem, "YK", tarih=o.SECIM_GUNU)]
    assert any("4 asıl üye var" in m for m in mesajlar)


def test_ayni_kisi_asil_ve_yedek_koltukta_olamaz() -> None:
    """Bir kişi aynı dönemde yönetim kurulunda tek koltuk tutar: asıl üye aynı dönemin başka genel
    kurulunda yedek seçilemez (sert, hesap bütünlüğü; kullanıcı kararı 10.11.2026). Aynı genel
    kurulda ikinci kayıt zaten kısmi tekil kısıtla kesilir; aday kaydı koltuk değildir."""
    donem = o.donem()
    ikinci_kurul = o.olaganustu_genel_kurul(donem)
    secilmis = o.kisi()
    devralinmis = o.kisi()
    _secilmis_yk(donem, secilmis)
    o.devralinan(donem, devralinmis)
    for kisi in (secilmis, devralinmis):
        aday = o.yk_adayi(donem, kisi, ikinci_kurul, seat_type=SeatType.YEDEK)
        with pytest.raises(ValueError, match="tek koltuk"):
            uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
        assert OrganMembership.objects.get(pk=aday.pk).status == MembershipStatus.ADAY
    assert selectors.kadro_sayilari(donem, "YK") == {SeatType.ASIL: 2, SeatType.YEDEK: 0}
    # Genel kurulsuz kanalda (devralınan) ikinci kayıt servisin "zaten var" iletisiyle kesilir.
    with pytest.raises(ValueError, match="zaten var"):
        o.devralinan(donem, devralinmis, seat_type=SeatType.YEDEK)


# ============================================================ kim oturabilir


@pytest.mark.kural_davranis(f"{YK}.uye_turleri")
@pytest.mark.parametrize("tur", [PersonKind.OGRETMEN, PersonKind.IDARECI, PersonKind.DIGER])
def test_yk_ye_veli_olmayan_ogretmen_ve_idareci_eklenemez(tur: str) -> None:
    donem = o.donem()
    kisi = o.kisi(kind=tur, is_parent=False)
    with pytest.raises(KuralSert) as hata:
        o.devralinan(donem, kisi)
    assert "md. 12/1" in str(hata.value.detail)
    assert not OrganMembership.objects.exists()  # işlem geri alındı
    # Uç da aynı kuraldan geçer: aday kaydı da sert reddedilir.
    kurul = o.olaganustu_genel_kurul(donem)
    yanit = APIClient().post(
        "/api/v1/oab/memberships/",
        {
            "term": donem.pk,
            "person": kisi.pk,
            "organ": "YK",
            "seat_type": "ASIL",
            "elected_by": "GENEL_KURUL",
            "assembly": kurul.pk,
        },
        format="json",
    )
    assert yanit.status_code == 400 and yanit.json()["code"] == "kural_sert"
    assert not OrganMembership.objects.exists()


@pytest.mark.kural_davranis(f"{YK}.uye_turleri")
@pytest.mark.parametrize("tur", [PersonKind.OGRETMEN, PersonKind.IDARECI])
def test_veli_olan_ogretmen_yk_ye_eklenebilir(tur: str) -> None:
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi(kind=tur, is_parent=True))
    assert uyelik.status == MembershipStatus.SECILDI


@pytest.mark.kural_davranis(f"{YK}.uye_turleri")
def test_yk_ye_kursiyer_ve_hayirsever_eklenebilir() -> None:
    donem = o.donem()
    o.devralinan(donem, o.kisi(kind=PersonKind.KURSIYER, adult_declared=True))
    o.devralinan(donem, o.kisi(kind=PersonKind.HAYIRSEVER))
    assert OrganMembership.objects.count() == 2
    # 18 yaşını doldurduğu beyan edilmemiş kursiyer giremez (md. 12/1).
    with pytest.raises(KuralSert):
        o.devralinan(donem, o.kisi(kind=PersonKind.KURSIYER, adult_declared=False))


@pytest.mark.kural_davranis(f"{YK}.okul_muduru_uye_olamaz")
def test_veli_olan_okul_muduru_yk_ye_eklenemez() -> None:
    donem = o.donem()
    mudur = kisiler.update_person(
        o.kisi(kind=PersonKind.IDARECI, is_parent=True), is_principal=True
    )
    with pytest.raises(KuralSert):
        o.devralinan(donem, mudur)
    kurul = o.olaganustu_genel_kurul(donem)
    with pytest.raises(KuralSert):
        o.yk_adayi(donem, mudur, kurul)
    assert not OrganMembership.objects.exists()


@pytest.mark.kural_davranis(f"{YK}.okul_muduru_uye_olamaz")
def test_atif_kullanici_karari_ke15_diye_basilir() -> None:
    donem = o.donem()
    mudur = kisiler.update_person(o.kisi(), is_principal=True)
    with pytest.raises(KuralSert) as hata:
        o.devralinan(donem, mudur)
    metin = str(hata.value.detail)
    assert "kullanıcı kararı KE-15 (gerekçe md. 12/1, 27/2-3)" in metin
    assert "Yönetmelik gereği" not in metin


@pytest.mark.kural_davranis(f"{YK}.gorevler")
def test_ikinci_baskan_kaydedilemez() -> None:
    """Dört görev seçilmiş üyeler arasında tekildir; başka görev ve üye sayısız yazılır."""
    donem = o.donem()
    o.devralinan(donem, o.kisi(), role="BASKAN")
    o.devralinan(donem, o.kisi(), role="MUHASIP")
    o.devralinan(donem, o.kisi(), role="UYE")
    o.devralinan(donem, o.kisi(), role="UYE")
    with pytest.raises(KuralSert) as hata:
        o.devralinan(donem, o.kisi(), role="BASKAN")
    assert "md. 12/3" in str(hata.value.detail)
    assert OrganMembership.objects.count() == 4


@pytest.mark.kural_davranis(f"{YK}.gorevler")
def test_gorev_tekilligi_yalniz_secilmisleri_sayar() -> None:
    """İstifayla düşen ya da iptal edilen başkan yeni başkanı engellemez (yanlış sert engel olurdu;
    altın kural 3)."""
    donem = o.donem()
    eski = o.devralinan(donem, o.kisi(), role="BASKAN")
    eski.status, eski.drop_kind = MembershipStatus.DUSTU, "ISTIFA"
    eski.save(update_fields=["status", "drop_kind"])
    yanlis = o.devralinan(donem, o.kisi(), role="MUHASIP")
    yanlis.status = MembershipStatus.IPTAL
    yanlis.save(update_fields=["status"])
    yeni = o.devralinan(donem, o.kisi(), role="BASKAN")
    muhasip = o.devralinan(donem, o.kisi(), role="MUHASIP")
    for uyelik in (yeni, muhasip):
        assert uyelik.status == MembershipStatus.SECILDI
        assert _satirlar(uyelik, f"{YK}.gorevler") == []


def test_secimde_gorev_verilmez_yedege_hic_verilmez() -> None:
    """Görevleri kurul görev bölümünde "üyeleri arasından" seçer (md. 12/3): genel kurulun adayı
    görevle açılmaz; yedek (devralınan da olsa) görev almaz, yoksa 6. adımın görev bölümünde seçilecek
    asıl muhasip görev tekilliğine takılırdı. Uç da aynı yapısal retten geçer."""
    donem = o.donem()
    kurul = o.olaganustu_genel_kurul(donem)
    for rol in ("BASKAN", "MUHASIP"):
        with pytest.raises(ValueError, match="görev bölümünde"):
            o.yk_adayi(donem, o.kisi(), kurul, role=rol)
        with pytest.raises(ValueError, match="yedek üye çağrılmadan"):
            o.yk_adayi(donem, o.kisi(), kurul, role=rol, seat_type=SeatType.YEDEK)
        with pytest.raises(ValueError, match="yedek üye çağrılmadan"):
            o.devralinan(donem, o.kisi(), role=rol, seat_type=SeatType.YEDEK)
    assert not OrganMembership.objects.exists()
    govde = {
        "term": donem.pk,
        "person": o.kisi().pk,
        "organ": "YK",
        "seat_type": "ASIL",
        "role": "MUHASIP",
        "elected_by": "GENEL_KURUL",
        "assembly": kurul.pk,
    }
    for alanlar in ({}, {"seat_type": "YEDEK"}):
        yanit = APIClient().post("/api/v1/oab/memberships/", {**govde, **alanlar}, format="json")
        assert yanit.status_code == 400, yanit.json()
    assert not OrganMembership.objects.exists()


def test_gorev_organda_yoksa_yapisal_ret() -> None:
    donem = o.donem()
    with pytest.raises(ValueError, match="Bu görev bu organda yoktur"):
        o.devralinan(donem, o.kisi(), role="KATIP")


# ============================================================ seçilme sayacı (md. 12/4)


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
def test_baskan_besinci_secim_gerekcesiz_reddedilir() -> None:
    """Dört kez başkan seçilmiş kişinin beşinci seçilmesi (başkan ve üye tek sayaç; görev seçimde değil
    görev bölümünde verilir)."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    o.gecmis_secilmeler(kisi, role="BASKAN", adet=4)
    with pytest.raises(GerekceGerekli) as hata:
        _secilmis_yk(donem, kisi)
    assert "5 defa" in str(hata.value.detail) and "md. 12/4" in str(hata.value.detail)
    # Seçilme geri alındı; aday kaydı aday kalır.
    assert OrganMembership.objects.get(term=donem).status == MembershipStatus.ADAY


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
def test_baskan_besinci_secim_gerekceyle_gecer() -> None:
    """Gerekçeyle kaydedilir; sapma satırı kural kimliği, paket ve revizyonla izde durur."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    o.gecmis_secilmeler(kisi, role="BASKAN", adet=4)
    uyelik = _secilmis_yk(donem, kisi, gerekce=uyum.Gerekce(metin="Uydurma gerekçe metni."))
    assert uyelik.status == MembershipStatus.SECILDI
    (satir,) = _satirlar(uyelik, f"{YK}.secilme_siniri")
    assert satir.kind == ComplianceKind.SAPMA and satir.justification_group is not None
    assert (satir.rule_package, satir.rev) == ("OAB-2023.12", 1)
    iz = AuditTrail.objects.filter(model="oab.ComplianceItem", object_id=str(satir.pk)).first()
    assert iz is not None and iz.values["rule_id"][1] == f"{YK}.secilme_siniri"
    assert iz.values["rev"][1] == 1
    ozet = {u["kural"]: u for u in OrganMembership.objects.get(pk=uyelik.pk).rule_warnings}
    assert ozet[f"{YK}.secilme_siniri"]["durum"] == "uyari"
    assert ozet[f"{YK}.secilme_siniri"]["atif"] == "md. 12/4"


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
def test_uye_dorduncu_secimde_uyarisiz_besincide_uyari() -> None:
    """Sınırın iki yanı: dördüncü seçilme uyarısız, beşinci uyarı (yedek de sayılır; B-12)."""
    donem = o.donem()
    kurul = o.olaganustu_genel_kurul(donem)
    dorduncu = o.kisi(external_yk_terms=1)
    o.gecmis_secilmeler(dorduncu, adet=1, seat_type=SeatType.YEDEK)
    o.gecmis_secilmeler(dorduncu, adet=1)
    uyelik = _secilmis_yk(donem, dorduncu, kurul=kurul)
    assert _satirlar(uyelik, f"{YK}.secilme_siniri") == []
    assert uyelikler.secilme_sayaci(dorduncu, "YK") == 4
    besinci = o.kisi(external_yk_terms=2)
    o.gecmis_secilmeler(besinci, adet=2, seat_type=SeatType.YEDEK)
    with pytest.raises(GerekceGerekli):
        _secilmis_yk(donem, besinci, kurul=kurul)


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
def test_aday_ve_iptal_sayaca_girmez() -> None:
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    o.gecmis_secilmeler(kisi, adet=3)
    iptal = o.gecmis_secilmeler(kisi, adet=1)[0]
    iptal.status = MembershipStatus.IPTAL
    iptal.save(update_fields=["status"])
    kurul = o.olaganustu_genel_kurul(donem)
    aday = o.yk_adayi(donem, kisi, kurul)
    assert uyelikler.yk_secilme_sayisi(kisi) == 3
    uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)  # dördüncü: uyarısız
    assert uyelikler.yk_secilme_sayisi(kisi) == 4


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
def test_dusen_secilme_sayaca_girer() -> None:
    """Seçilip düşmüş kayıt sayılır (§15 B-12): istifa eden başkanın seçilmeleri sayaçtan çıkmaz."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    o.gecmis_secilmeler(kisi, adet=3)
    (dusen,) = o.gecmis_secilmeler(kisi, role="BASKAN", adet=1)
    dusen.status, dusen.drop_kind = MembershipStatus.DUSTU, "ISTIFA"
    dusen.save(update_fields=["status", "drop_kind"])
    assert uyelikler.yk_secilme_sayisi(kisi) == 4
    with pytest.raises(GerekceGerekli):
        _secilmis_yk(donem, kisi)


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
def test_dk_secilmeleri_yk_sayacina_girmez() -> None:
    """md. 12/4 yalnız yönetim kurulundaki seçilmeleri sayar: Denetleme Kurulu üyelikleri ve
    başkanlıkları yönetim kurulu sayacına girmez."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    o.gecmis_secilmeler(kisi, organ="DK", adet=4)
    o.gecmis_secilmeler(kisi, organ="DK", role="BASKAN", adet=1)
    uyelik = _secilmis_yk(donem, kisi)  # gerekçesiz geçer
    assert _satirlar(uyelik, f"{YK}.secilme_siniri") == []
    assert uyelikler.yk_secilme_sayisi(kisi) == 1
    assert uyelikler.secilme_sayaci(kisi, "YK") == 1


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
def test_gecmis_eksikse_tamamlanacak_engel_yok() -> None:
    """Beyan "bilinmiyor"sa sayaç eksiktir: gerekçe istemez, eksik satırı açılır (R5)."""
    donem = o.donem()
    kisi = o.kisi()  # external_yk_terms = None
    o.gecmis_secilmeler(kisi, adet=2)
    uyelik = _secilmis_yk(donem, kisi)
    (satir,) = _satirlar(uyelik, f"{YK}.secilme_siniri")
    assert satir.kind == ComplianceKind.EKSIK and satir.justification_group is None
    assert uyelikler.secilme_sayaci(kisi, "YK") is None
    ozet = OrganMembership.objects.get(pk=uyelik.pk).rule_warnings
    assert [u["durum"] for u in ozet if u["kural"] == f"{YK}.secilme_siniri"] == ["eksik"]


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
def test_beyan_bilinmese_de_bilinen_kayitlar_siniri_asiyorsa_uyari() -> None:
    donem = o.donem()
    kisi = o.kisi()
    o.gecmis_secilmeler(kisi, adet=4)
    with pytest.raises(GerekceGerekli):
        _secilmis_yk(donem, kisi)


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
def test_devralinan_kayit_sayac_disinda() -> None:
    """Devralınan üyelik sayaca girmez: beyan görevdeki seçimi içerir (plan F1c kararları). Beyan
    sınırın üstünde ya da bilinmiyor; denetim koşsaydı gerekçe ya da eksik satırı isterdi."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=5)
    uyelik = o.devralinan(donem, kisi, role="BASKAN")
    assert uyelik.status == MembershipStatus.SECILDI
    assert _satirlar(uyelik, f"{YK}.secilme_siniri") == []
    assert uyelikler.yk_secilme_sayisi(kisi) == 0
    assert uyelikler.secilme_sayaci(kisi, "YK") == 5
    bilinmeyen = o.devralinan(donem, o.kisi())  # external_yk_terms = None
    assert _satirlar(bilinmeyen, f"{YK}.secilme_siniri") == []


# ============================================================ tek kaynak


def test_aday_ve_secilen_ayni_kayit() -> None:
    """Genel kurulda seçilen, aynı genel kurulun aday kaydının kendisidir (OYS ilkesi AYNEN)."""
    donem = o.donem()
    kurul = o.olaganustu_genel_kurul(donem)
    kisi = o.kisi(external_yk_terms=0)
    aday = o.yk_adayi(donem, kisi, kurul)
    assert (aday.status, aday.start_date) == (MembershipStatus.ADAY, None)
    secilen = uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU, votes=41)
    assert secilen.pk == aday.pk and secilen.assembly_id == kurul.pk
    assert (secilen.status, secilen.start_date, secilen.votes) == (
        MembershipStatus.SECILDI,
        o.SECIM_GUNU,
        41,
    )
    assert OrganMembership.objects.count() == 1
    # Genel kurul kanalında kayıt doğrudan seçilmiş açılamaz; seçilmiş yeniden seçilemez.
    with pytest.raises(ValueError, match="genel kurula bağlanır"):
        uyelikler.assign_membership(
            term=donem,
            person=o.kisi(),
            organ="YK",
            seat_type="ASIL",
            elected_by="GENEL_KURUL",
            start_date=date(2026, 10, 15),
        )
    with pytest.raises(ValueError, match="Yalnız aday"):
        uyelikler.elect_membership(secilen)
    durumlar = list(
        AuditTrail.objects.filter(model="oab.OrganMembership", object_id=str(aday.pk))
        .order_by("seq")
        .values_list("action", flat=True)
    )
    assert durumlar[0] == "OLUSTUR" and "DURUM" in durumlar


def test_secilme_gunu_genel_kurulun_yerel_gunudur() -> None:
    """Gün verilmezse seçilme günü genel kurulun birinci toplantısının İstanbul'daki günüdür: UTC
    14.10.2026 22.30, yerelde 15.10.2026 01.30'dur (UTC günü ya da bugün değil)."""
    donem = o.donem()
    kurul = o.olaganustu_genel_kurul(donem)
    GeneralAssembly.objects.filter(pk=kurul.pk).update(
        first_meeting_at=datetime(2026, 10, 14, 22, 30, tzinfo=UTC)
    )
    aday = o.yk_adayi(donem, o.kisi(external_yk_terms=0), kurul)
    secilen = uyelikler.elect_membership(aday)
    assert secilen.start_date == date(2026, 10, 15)
