"""Yönetim kurulu kuralları (`yk`, tasarım §6.4.2, §10.3; F1c 5. adım: bileşim ve seçilme sayacı).

Bileşim: kim oturabilir (veli, 18 yaşını doldurmuş kursiyer, hayırsever; SERT), okul müdürü giremez
(SERT, kullanıcı kararı KE-15), dört görev görevdeki seçilmiş asıllar arasında tekildir (SERT), kadro
sayıları uyarıdır ve yalnız seçilmiş kayıt sayılır. Görev seçimde verilmez (md. 12/3): programda açılan
kayıt `UYE`'dir, görevli kayıt yalnız devralınan asıldır. Sayaç: başkan ve üye tek sayaç, asıl ve yedek
her seçilme; `SECILDI` ve `DUSTU` sayılır, `ADAY`, `IPTAL` ve `DEVRALINAN` sayılmaz; yalnız yönetim
kurulu seçilmeleri; programın kayıtları + beyan; beyan bilinmiyorsa eksik (R5).

6. adım (bu dosyanın sonu): görev bölümü (dört görev tekil, bir hafta, uçtan gerekçe akışı), görev
süresi, yedek çağrısı (oy sırası, sıra dışı ve kararsız çağrı uyarı + gerekçe), düşme (tür zorunlu;
md. 7/2 istisnası), suç ve tek birlik engelleri (seçimde uyarı + gerekçe, görevdeki üyede düşürme
önerisi, beyan okul uygulaması), alım komisyonunun en az üç kişisi (organ ekranı). Kişi adları
UYDURMADIR.

8. adım (dosyanın en sonu): karar defterinin noter tasdiki (md. 23/2; plan F1c 8. adım notları):
noter tasdiki ve günü girilmişse uyarısız, tasdik bilgisi eksikse ya da il/ilçe millî eğitim
müdürlüğü tasdiki girilmişse uyarı + gerekçe; konu defter, gerekçe defter başına bir.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.oab import selectors
from apps.oab.hatalar import GerekceGerekli, KuralSert
from apps.oab.kurallar import VERI_YOK
from apps.oab.kurallar.erisim import denetle as paket_denetle
from apps.oab.models import (
    BoardDecision,
    BoardMeeting,
    BookCertifier,
    ComplianceItem,
    ComplianceJustification,
    ComplianceKind,
    DecisionKind,
    DecisionStatus,
    EligibilityBar,
    GeneralAssembly,
    MeetingKind,
    MembershipStatus,
    OfficialBook,
    OrganMembership,
    PersonKind,
    SeatType,
)
from apps.oab.services import (
    gorev_bolumu,
    kisiler,
    kurullar,
    temsilciler,
    uyelik_gecisleri,
    uyelikler,
    uyum,
)
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import AccountRole, AuditTrail

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
        for sira in range(5):
            rol = "BASKAN" if (koltuk, sira) == (SeatType.ASIL, 0) else "UYE"
            o.devralinan(donem, o.kisi(), seat_type=koltuk, role=rol)
    # Görevdeki başkanı olan tam kadro uyarısız ve eksiksizdir.
    assert uyelikler.kadro_uyarilari(donem, "YK", tarih=o.SECIM_GUNU) == []


@pytest.mark.kural_davranis(f"{YK}.asil_uye")
def test_dusen_koltuk_sayima_girmez() -> None:
    """AYNEN (§12.A): düşen koltuk sayılmaz; aday da sayılmaz (kadro sayımı yalnız `SECILDI`)."""
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


@pytest.mark.kural_davranis(f"{YK}.secilme_siniri")
@pytest.mark.kural_davranis("denetleme_kurulu.baskan_secilme_siniri")
def test_donem_siniri_ucu_gerekce() -> None:
    """Seçilme sınırının (dönem sınırı sayacı) gerekçesi uçtan da aynı akıştır: gerekçesiz istek 400
    `gerekce_gerekli` (kayıt yok), gerekçeyle 201 ve `SAPMA` satırı. Yönetim kurulu seçiminin ucu genel
    kurul sihirbazıyla gelir (F2): bugün sayacı uçtan koşturan yol Denetleme Kurulunun görev bölümüdür
    (md. 14/3; aynı sayaç hattı). Yönetim kurulu sayacının servis akışı yukarıdaki testlerdedir."""
    donem = o.donem()
    kisi = o.ogretmen(external_dk_chair_terms=3)
    uye = o.dk_ogretmeni(donem, kisi)
    govde = {
        "held_at": "2026-10-16T15:00:00+03:00",
        "baskan": uye.pk,
        "katilim": [
            {"membership": u.pk, "present": True} for u in selectors.gorevdeki_asillar(donem, "DK")
        ],
    }
    yol = f"/api/v1/oab/terms/{donem.pk}/duty-assignment/dk/"
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        ret = APIClient().post(yol, govde, format="json")
        assert ret.status_code == 400 and ret.json()["code"] == "gerekce_gerekli", ret.content
        assert not BoardMeeting.objects.exists()
        kabul = APIClient().post(yol, {**govde, "gerekce": "Uydurma gerekçe."}, format="json")
    assert kabul.status_code == 201, kabul.content
    (satir,) = _satirlar(uye, "denetleme_kurulu.baskan_secilme_siniri")
    assert satir.kind == ComplianceKind.SAPMA and satir.justification_group is not None


# ============================================================ tek kaynak


def test_aday_ve_secilen_ayni_kayit() -> None:
    """Genel kurulda seçilen, aynı genel kurulun aday kaydının kendisidir (§12.A ilkesi AYNEN)."""
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


# ============================================================ 6. adım: görev bölümü (md. 12/3)


def _toplanti_satirlari(toplanti: BoardMeeting, kural_id: str) -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(
            subject_type="oab.BoardMeeting", subject_id=str(toplanti.pk), rule_id=kural_id
        )
    )


@pytest.mark.kural_davranis(f"{YK}.gorev_bolumu_gun")
def test_gorev_bolumu_7_gun_uyarisiz() -> None:
    """Seçimden sonra bir hafta (md. 12/3; yorum KE-12: izleyen 7 takvim günü): 7. gün uyarısız."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)  # seçilme günü 15.10.2026
    yedinci = o.yk_gorev_bolumu(donem, {"SEKRETER": uyeler[0]}, gun=date(2026, 10, 22))
    assert not _toplanti_satirlari(yedinci.toplanti, f"{YK}.gorev_bolumu_gun")


@pytest.mark.kural_davranis(f"{YK}.gorev_bolumu_gun")
def test_gorev_bolumu_8_gun_uyari() -> None:
    """Kurulun ilk görev bölümü 8. gündeyse gerekçesiz reddedilir (işlem geri alınır), gerekçeyle
    kaydedilir. Sınırın öteki yanı ayrı kurulumdadır: önceki görev bölümü süreyi kapatır."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    with pytest.raises(GerekceGerekli) as hata:
        o.yk_gorev_bolumu(donem, {"MUHASIP": uyeler[1]}, gun=date(2026, 10, 23))
    assert "8 gün" in str(hata.value.detail) and "md. 12/3" in str(hata.value.detail)
    assert not BoardMeeting.objects.exists()  # toplantı da geri alındı
    assert OrganMembership.objects.get(pk=uyeler[1].pk).role == "UYE"
    sekizinci = o.yk_gorev_bolumu(
        donem, {"MUHASIP": uyeler[1]}, gun=date(2026, 10, 23), gerekce="Uydurma gerekçe."
    )
    (satir,) = _toplanti_satirlari(sekizinci.toplanti, f"{YK}.gorev_bolumu_gun")
    assert satir.kind == ComplianceKind.SAPMA and satir.justification_group is not None


def _yedegi_cagrilmis_kurul(donem: Any) -> list[OrganMembership]:
    """Bir asıl 01.11.2026'da istifa eder, birinci yedek 02.11.2026'da çağrılır (karar bağı F3'e dek
    yok: gerekçeyle)."""
    uyeler = o.yk_kurulu(donem, yedek=1)
    uyelik_gecisleri.uyeligi_dusur(uyeler[0], drop_kind="ISTIFA", end_date=date(2026, 11, 1))
    uyelik_gecisleri.yedek_cagir(
        uyeler[5],
        organ="YK",
        promoted_on=date(2026, 11, 2),
        gerekce=uyum.Gerekce(metin="Uydurma: karar defteri ekranı F3'te."),
    )
    return uyeler


@pytest.mark.kural_davranis(f"{YK}.gorev_bolumu_gun")
@pytest.mark.parametrize(("gun", "uyari"), [(date(2026, 11, 9), False), (date(2026, 11, 10), True)])
def test_yedek_cagrisindan_sonra_7_gun(gun: date, uyari: bool) -> None:
    """Yedeğin çağrılmasıyla oluşan yeni kurul bir hafta içinde görev dağılımı yapar (md. 12/3 2.
    cümle): süre çağrı gününden (`promoted_on`) başlar, seçilme gününden değil. 7. gün uyarısız,
    8. gün uyarı (ayrı kurulumlar: önceki görev bölümü süreyi kapatır)."""
    donem = o.donem()
    uyeler = _yedegi_cagrilmis_kurul(donem)
    if not uyari:
        sonuc = o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[5]}, gun=gun)
        assert not _toplanti_satirlari(sonuc.toplanti, f"{YK}.gorev_bolumu_gun")
        return
    with pytest.raises(GerekceGerekli) as hata:
        o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[5]}, gun=gun)
    assert "8 gün" in str(hata.value.detail)


@pytest.mark.kural_davranis(f"{YK}.gorev_bolumu_gun")
def test_bilesim_degismeden_gorev_degisimi_sureye_bagli_degil() -> None:
    """md. 12/3 süreyi yalnız seçimden ve yedek çağrısından sonraki görev bölümüne koyar: kurulun
    bileşimi değişmeden yapılan dönem içi görev değişimi gerekçe istemez, süre satırı açmaz."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)  # 15.10.2026
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=date(2026, 10, 20))
    degisim = o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[1]}, gun=date(2027, 1, 15))
    assert not _toplanti_satirlari(degisim.toplanti, f"{YK}.gorev_bolumu_gun")
    assert not ComplianceItem.objects.filter(rule_id=f"{YK}.gorev_bolumu_gun").exists()
    # Yedek çağrısıyla bileşim değişince süre yeniden başlar (çağrıdan önceki görev bölümü saymaz).
    uyelik_gecisleri.uyeligi_dusur(uyeler[2], drop_kind="ISTIFA", end_date=date(2027, 2, 1))
    yedek = o.secilmis(donem, seat_type=SeatType.YEDEK, seat_order=1)
    uyelik_gecisleri.yedek_cagir(
        yedek, organ="YK", promoted_on=date(2027, 2, 2), gerekce=uyum.Gerekce(metin="Uydurma.")
    )
    with pytest.raises(GerekceGerekli):
        o.yk_gorev_bolumu(donem, {"SEKRETER": yedek}, gun=date(2027, 2, 10))


@pytest.mark.kural_davranis(f"{YK}.gorevler")
def test_baskansiz_gorev_bolumu_yazilir_kadroda_eksik() -> None:
    """Başkansız görev bölümü yazılır (engel yok, gerekçe istemez); görevdeki asıllar arasında başkan
    yoksa kadro okumasında eksiktir: atıf md. 12/3, uyum satırı açılmaz, uç `kadro_uyarilari`'nda
    `eksik` durumuyla döner. Başkan seçilince kalkar (plan F1c 6. adım notları)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    yol = f"/api/v1/oab/terms/{donem.pk}/roster/YK/"

    def eksikler() -> list[tuple[str, str]]:
        return [
            (s["metin"], s["atif"])
            for s in APIClient().get(yol).json()["kadro_uyarilari"]
            if s["durum"] == "eksik"
        ]

    beklenen = [(f"{uyelikler.BASKAN_YOK['YK'].rstrip('.')} (md. 12/3).", "md. 12/3")]
    assert eksikler() == beklenen  # görev bölümü henüz yapılmadı
    sonuc = o.yk_gorev_bolumu(
        donem, {"MUHASIP": uyeler[1], "SEKRETER": uyeler[2]}, gun=date(2026, 10, 16)
    )
    assert sonuc.karar.status == "TASLAK"
    assert eksikler() == beklenen
    assert not ComplianceItem.objects.filter(rule_id=f"{YK}.gorevler").exists()
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=date(2026, 10, 20))
    assert eksikler() == []


@pytest.mark.kural_davranis(f"{YK}.gorev_bolumu_gun")
def test_gorev_bolumu_kurul_olusmadan_once_olamaz() -> None:
    """Görev bölümü görevdeki asılların seçilme ya da yedekten çağrı gününden önce olamaz (sert, tarih
    sırası)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)  # 15.10.2026
    with pytest.raises(ValueError, match="yedekten çağrıldığı günden önce"):
        o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=date(2026, 10, 14))
    assert not BoardMeeting.objects.exists()


@pytest.mark.kural_davranis(f"{YK}.gorev_bolumu_gun")
def test_gorev_bolumu_ucu_gerekce_akisi() -> None:
    """Uçtan gerekçe akışı: 8. günde gerekçesiz istek 400 `gerekce_gerekli` (kayıt yok), gerekçeyle
    201; toplantı `YAPILDI`, karar `TASLAK`, görev yazılı. Kaydı sekreter yazar (tasarım §7.2)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    govde = {
        "held_at": "2026-10-23T15:00:00+03:00",
        "sekreter": uyeler[0].pk,
        "katilim": [
            {"membership": u.pk, "present": i != 4, "excused": i == 4} for i, u in enumerate(uyeler)
        ],
    }
    yol = f"/api/v1/oab/terms/{donem.pk}/duty-assignment/yk/"
    with o.rol_olarak(AccountRole.SEKRETER):
        istemci = APIClient()
        ret = istemci.post(yol, govde, format="json")
        assert ret.status_code == 400, ret.content
        assert ret.json()["code"] == "gerekce_gerekli"
        assert not BoardMeeting.objects.exists()
        kabul = istemci.post(yol, {**govde, "gerekce": "Uydurma gerekçe."}, format="json")
    assert kabul.status_code == 201, kabul.content
    veri = kabul.json()
    assert veri["karar_durumu"] == DecisionStatus.TASLAK
    assert [u["role"] for u in veri["uyelikler"]] == ["SEKRETER"]
    toplanti = BoardMeeting.objects.get(pk=veri["toplanti"])
    assert (toplanti.kind, toplanti.status) == (MeetingKind.GOREV_BOLUMU, "YAPILDI")
    assert toplanti.attendances.count() == 5
    assert _toplanti_satirlari(toplanti, f"{YK}.gorev_bolumu_gun")[0].kind == ComplianceKind.SAPMA
    # Uç yalnız sekreterindir (program yöneticisi ve başkan yazmaz; tasarım §7.2 "Kim").
    for rol in (AccountRole.BASKAN,):
        with o.rol_olarak(rol):
            assert APIClient().post(yol, govde, format="json").status_code == 403


@pytest.mark.kural_davranis(f"{YK}.gorevler")
def test_gorev_bolumu_dort_gorev_tekil_ve_gorev_degisimi() -> None:
    """Dört görev görevdeki asıllar arasında tekildir: görevi yeni üye alınca önceki sahibi üye olur
    (dönem içi görev değişimi); bir üyeye iki görev ve yedeğe görev verilmez."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem, yedek=1)
    gun = date(2026, 10, 20)
    o.yk_gorev_bolumu(
        donem,
        {
            "BASKAN": uyeler[0],
            "BASKAN_YARDIMCISI": uyeler[1],
            "MUHASIP": uyeler[2],
            "SEKRETER": uyeler[3],
        },
        gun=gun,
    )
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[4]}, gun=gun)
    gorevler = {u.pk: u.role for u in selectors.gorevdeki_asillar(donem, "YK")}
    assert gorevler[uyeler[0].pk] == "UYE" and gorevler[uyeler[4].pk] == "BASKAN"
    assert sorted(r for r in gorevler.values() if r != "UYE") == [
        "BASKAN",
        "BASKAN_YARDIMCISI",
        "MUHASIP",
        "SEKRETER",
    ]
    with pytest.raises(ValueError, match="tek görev"):
        o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[1], "MUHASIP": uyeler[1]}, gun=gun)
    with pytest.raises(ValueError, match="yalnız asıl"):
        o.yk_gorev_bolumu(donem, {"MUHASIP": uyeler[5]}, gun=gun)
    with pytest.raises(ValueError, match="görev bölümünde verilmez"):
        o.yk_gorev_bolumu(donem, {"KATIP": uyeler[1]}, gun=gun)
    # Katılım görevdeki her asıl için zorunludur (tasarım §7.2 `YAPILDI` [S]).
    with pytest.raises(ValueError, match="katılım satırı"):
        gorev_bolumu.yk_gorev_bolumu(
            term=donem, held_at=o.saat(gun), gorevler={"MUHASIP": uyeler[1]}, katilim=[]
        )


def _baskan_satirlari(donem: Any) -> dict[str, set[tuple[int, str]]]:
    return {
        temsil: {
            (s.person_id, s.status)
            for s in OrganMembership.objects.filter(
                term=donem, organ="TEMSILCI", representation=temsil
            )
        }
        for temsil in temsilciler.BASKANIN_KOMISYONLARI
    }


@pytest.mark.kural_davranis(f"{YK}.gorevler")
def test_baskan_kendiliginden_komisyon_satirlarini_alir() -> None:
    """Görev bölümünün başkanı taşımacı, muhammen bedel ve kiralama komisyonlarına kendiliğinden
    yazılır; başkanlığı bırakanın bu satırları düşer (E03 "başkanın adı kendiliğinden")."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=date(2026, 10, 20))
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[1]}, gun=date(2026, 10, 21))
    for temsil in temsilciler.BASKANIN_KOMISYONLARI:
        satirlar = OrganMembership.objects.filter(
            term=donem, organ="TEMSILCI", representation=temsil
        )
        assert {(s.person_id, s.status) for s in satirlar} == {
            (uyeler[0].person_id, MembershipStatus.DUSTU),
            (uyeler[1].person_id, MembershipStatus.SECILDI),
        }


@pytest.mark.kural_davranis("temsilci.tasimaci_tespit_komisyonu")
@pytest.mark.parametrize(
    "eski_baskanin_gorevi",
    [
        pytest.param("MUHASIP", id="baska_goreve_gecis"),
        pytest.param("BASKAN_YARDIMCISI", id="takas"),
    ],
)
def test_baskanligi_birakip_baska_gorev_alanin_satirlari_duser(eski_baskanin_gorevi: str) -> None:
    """Başkanlığı bırakan önceki başkan aynı görev bölümünde başka görev alsa da kendiliğinden
    satırları düşer; her komisyonda tek başkan satırı kalır, çizelge uygundur (E03)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(
        donem, {"BASKAN": uyeler[0], "BASKAN_YARDIMCISI": uyeler[1]}, gun=date(2026, 10, 20)
    )
    o.yk_gorev_bolumu(
        donem, {"BASKAN": uyeler[1], eski_baskanin_gorevi: uyeler[0]}, gun=date(2026, 10, 21)
    )
    for satirlar in _baskan_satirlari(donem).values():
        assert satirlar == {
            (uyeler[0].person_id, MembershipStatus.DUSTU),
            (uyeler[1].person_id, MembershipStatus.SECILDI),
        }
    cizelge = {
        s.representation: s for s in temsilciler.temsilci_cizelgesi(donem, tarih=date(2026, 10, 21))
    }
    for temsil in temsilciler.BASKANIN_KOMISYONLARI:
        assert cizelge[temsil].durum == "uygun"


@pytest.mark.kural_davranis("temsilci.muhammen_bedel_komisyonu")
def test_baska_gorevi_birakanin_elle_satiri_dusmez() -> None:
    """Yalnız başkanlığı bırakanın satırları düşer: muhasipliği bırakanın gerekçeyle elle girilmiş
    komisyon satırı görev bölümünde kendiliğinden düşmez (kayıt bilinçsiz geçiş görmez)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0], "MUHASIP": uyeler[2]}, gun=date(2026, 10, 20))
    elle = temsilciler.temsilci_ekle(
        term=donem,
        person=uyeler[2].person,
        representation="MUHAMMEN_BEDEL_KOMISYONU",
        start_date=date(2026, 10, 20),
        gerekce=uyum.Gerekce(metin="Uydurma: başkan izinli."),
    )
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0], "MUHASIP": uyeler[3]}, gun=date(2026, 10, 21))
    assert OrganMembership.objects.get(pk=elle.pk).status == MembershipStatus.SECILDI


@pytest.mark.kural_davranis("temsilci.kiralama_ihale_komisyonu")
def test_baskan_duserse_satirlari_duser_yeni_baskan_tek_kalir() -> None:
    """Başkanlık kaydı düşünce (istifa) kendiliğinden satırları aynı işlemde düşer (`DIGER`, düşme
    günüyle); yedek çağrılır, yeni başkan atanır: her komisyonda tek seçilmiş satır yeni başkanındır."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem, yedek=1)
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=date(2026, 10, 20))
    uyelik_gecisleri.uyeligi_dusur(uyeler[0], drop_kind="ISTIFA", end_date=date(2026, 11, 1))
    dusenler = OrganMembership.objects.filter(
        term=donem, organ="TEMSILCI", person_id=uyeler[0].person_id
    )
    assert {(s.status, s.drop_kind, s.end_date) for s in dusenler} == {
        (MembershipStatus.DUSTU, "DIGER", date(2026, 11, 1))
    }
    uyelik_gecisleri.yedek_cagir(
        uyeler[5], organ="YK", promoted_on=date(2026, 11, 2), gerekce=uyum.Gerekce(metin="Uydurma.")
    )
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[1]}, gun=date(2026, 11, 5))
    for satirlar in _baskan_satirlari(donem).values():
        assert satirlar == {
            (uyeler[0].person_id, MembershipStatus.DUSTU),
            (uyeler[1].person_id, MembershipStatus.SECILDI),
        }


@pytest.mark.kural_davranis("temsilci.tasimaci_tespit_komisyonu")
def test_baskan_iptal_edilirse_satirlari_iptal_olur() -> None:
    """Başkanlık kaydı yanlış kayıt diye iptal edilirse kendiliğinden satırları da iptal olur (hiç
    olmamış sayılır); md. 7/2 ertelemesinde başkan görevde kalır, satırlar seçilmiş kalır."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=date(2026, 10, 20))
    uyelik_gecisleri.uyeligi_iptal_et(uyeler[0], cancel_reason="Uydurma yanlış kayıt.")
    for satirlar in _baskan_satirlari(donem).values():
        assert satirlar == {(uyeler[0].person_id, MembershipStatus.IPTAL)}
    # md. 7/2: dört asıl kalmış kurulda öğrencisi ayrılan başkanın düşmesi ertelenir.
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[1]}, gun=date(2026, 10, 21))
    uyelik_gecisleri.uyeligi_dusur(uyeler[1], drop_kind="OGRENCI_AYRILDI", ertele=True)
    for satirlar in _baskan_satirlari(donem).values():
        assert (uyeler[1].person_id, MembershipStatus.SECILDI) in satirlar


# ============================================================ görev süresi (md. 12/2)


def _sure_uyarilari(donem: Any, organ: str, gun: date) -> list[str]:
    return [
        s["atif"]
        for s in uyelikler.kadro_uyarilari(donem, organ, tarih=gun)
        if "görev süresi" in s["mesaj"]
    ]


@pytest.mark.kural_davranis(f"{YK}.gorev_suresi_yil")
def test_gorev_suresi_bitiminde_uyari() -> None:
    """Görev süresi bir yıldır, son genel kuruldan (dönemin başı 10.10.2026) sayılır: 09.10.2027
    uyarısız, yıl dönümü 10.10.2027 uyarı (kadro okuması; gerekçe istemez)."""
    donem = o.donem()
    o.yk_kurulu(donem)
    assert _sure_uyarilari(donem, "YK", date(2027, 10, 9)) == []
    assert _sure_uyarilari(donem, "YK", date(2027, 10, 10)) == ["md. 12/2"]


# ============================================================ yedek çağrısı (md. 13/6)


def _yedek_karari(donem: Any, *, durum: str = DecisionStatus.KABUL_EDILDI) -> Any:
    """Yedek çağırma kararı. Kabul F3'ün karar defteri akışındadır; burada ORM'le yazılır."""
    toplanti = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.OLAGANUSTU)
    karar = kurullar.karar_taslagi_olustur(toplanti, kind=DecisionKind.YEDEK_CAGIRMA)
    if durum == DecisionStatus.IPTAL:
        return kurullar.karar_durumu_yaz(karar, DecisionStatus.IPTAL)
    BoardDecision.objects.filter(pk=karar.pk).update(status=durum)
    return BoardDecision.objects.get(pk=karar.pk)


@pytest.mark.kural_davranis(f"{YK}.yedek_cagirma")
def test_yedek_oy_sirasi_alani() -> None:
    """Yedek sırası (aldığı oy sırası) yalnız yedekte verilir; bekleyen yedekler sırayla listelenir."""
    donem = o.donem()
    asil = o.secilmis(donem)
    ikinci = o.secilmis(donem, seat_type=SeatType.YEDEK, seat_order=2)
    birinci = o.secilmis(donem, seat_type=SeatType.YEDEK, seat_order=1)
    assert [y.pk for y in selectors.bekleyen_yedekler(donem, "YK")] == [birinci.pk, ikinci.pk]
    with pytest.raises(ValueError, match="yalnız yedek"):
        uyelikler.update_membership(asil, seat_order=1)


@pytest.mark.kural_davranis(f"{YK}.yedek_cagirma")
def test_yedek_oy_sirasiyla_cagrilir() -> None:
    """Sıradaki yedek kararla çağrılınca uyarı yoktur; kayıt aynıdır, koltuğu yedek kalır,
    `promoted_on` çağrıyı gösterir ve görevdeki asıllara girer."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem, asil=4, yedek=2)
    karar = _yedek_karari(donem)
    cagrilan = uyelik_gecisleri.yedek_cagir(
        uyeler[4], organ="YK", promoted_on=date(2026, 11, 2), karar=karar
    )
    assert (cagrilan.pk, cagrilan.seat_type) == (uyeler[4].pk, SeatType.YEDEK)
    assert cagrilan.promoted_on == date(2026, 11, 2)
    assert cagrilan.promoted_by_decision_id == karar.pk
    assert uyeler[4].pk in {u.pk for u in selectors.gorevdeki_asillar(donem, "YK")}
    assert _satirlar(cagrilan, f"{YK}.yedek_cagirma") == []
    with pytest.raises(ValueError, match="çağrılmamış yedek"):
        uyelik_gecisleri.yedek_cagir(uyeler[4], organ="YK", karar=karar)


@pytest.mark.kural_davranis(f"{YK}.yedek_cagirma")
def test_sira_disi_cagri_gerekce_ister() -> None:
    """Sıradakinin atlanması (yedeğin çekilmesi vb.) uyarı + gerekçedir (md. 13/6)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem, asil=4, yedek=2)
    karar = _yedek_karari(donem)
    with pytest.raises(GerekceGerekli) as hata:
        uyelik_gecisleri.yedek_cagir(uyeler[5], organ="YK", karar=karar)
    assert "sıra dışı" in str(hata.value.detail) and "md. 13/6" in str(hata.value.detail)
    assert OrganMembership.objects.get(pk=uyeler[5].pk).promoted_on is None
    cagrilan = uyelik_gecisleri.yedek_cagir(
        uyeler[5], organ="YK", karar=karar, gerekce=uyum.Gerekce(metin="Birinci yedek çekildi.")
    )
    (satir,) = _satirlar(cagrilan, f"{YK}.yedek_cagirma")
    assert satir.kind == ComplianceKind.SAPMA and satir.justification_group is not None


@pytest.mark.kural_davranis(f"{YK}.yedek_cagirma")
def test_karar_bagi_yoksa_uyari_ve_bag_dogrulanir() -> None:
    """Karar bağı F3'e dek yoksa uyarı + gerekçedir (plan F1c kararları; Yönetmelik hükmü değildir):
    ileti md. 13/6 atfı taşımaz, sıra doğruyken md. 13/6 satırı yazılmaz, gerekçe atıfsız akış
    satırındadır. Bağlanan karar yedek çağırma kararı, toplantısı yönetim kurulu toplantısı, dönemi
    yedeğin dönemi olmalı ve kabul edilmiş olmalıdır (sert, hesap bütünlüğü)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem, asil=4, yedek=2)
    with pytest.raises(GerekceGerekli) as hata:
        uyelik_gecisleri.yedek_cagir(uyeler[4], organ="YK")
    assert "kararına bağlanmadı" in str(hata.value.detail)
    assert "md." not in str(hata.value.detail)
    toplanti = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.GOREV_BOLUMU)
    gorev_karari = kurullar.karar_taslagi_olustur(toplanti, kind=DecisionKind.GOREV_BOLUMU)
    with pytest.raises(ValueError, match="yedek çağırma kararı olmalıdır"):
        uyelik_gecisleri.yedek_cagir(uyeler[4], organ="YK", karar=gorev_karari)
    with pytest.raises(ValueError, match="bu kurulun yedeği"):
        uyelik_gecisleri.yedek_cagir(uyeler[4], organ="DK", karar=_yedek_karari(donem))
    # Başka birlik döneminin kararı bağlanamaz (geçmiş dönem ORM'le; kapanmış dönem yazılmaz).
    (gecmis,) = o.gecmis_secilmeler(o.kisi())
    baska_donem_karari = _yedek_karari(donem)
    BoardMeeting.objects.filter(pk=baska_donem_karari.meeting_id).update(term=gecmis.term)
    with pytest.raises(ValueError, match="birlik döneminin kararı"):
        uyelik_gecisleri.yedek_cagir(uyeler[4], organ="YK", karar=baska_donem_karari)
    cagrilan = uyelik_gecisleri.yedek_cagir(
        uyeler[4], organ="YK", gerekce=uyum.Gerekce(metin="Karar defteri ekranı henüz yok.")
    )
    assert _satirlar(cagrilan, f"{YK}.yedek_cagirma") == []
    (satir,) = _satirlar(cagrilan, uyelik_gecisleri.KARARSIZ_CAGRI_AKISI)
    assert satir.kind == ComplianceKind.SAPMA and satir.justification_group is not None
    assert "kararına bağlanmadı" in satir.message and "md." not in satir.message
    assert (satir.rule_package, satir.rev) == ("", None)


@pytest.mark.kural_davranis(f"{YK}.yedek_cagirma")
@pytest.mark.parametrize("durum", [DecisionStatus.TASLAK, DecisionStatus.IPTAL])
def test_kabul_edilmemis_karar_baglanamaz(durum: str) -> None:
    """Bağlanan karar kabul edilmiş olmalıdır (tasarım §7.2 "Notlar"): taslak ya da iptal edilmiş
    karar bağlanamaz, karar bağı yokluğu uyarısını susturamaz (sert, hesap bütünlüğü)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem, asil=4, yedek=1)
    with pytest.raises(ValueError, match="kabul edilmiş olmalı"):
        uyelik_gecisleri.yedek_cagir(uyeler[4], organ="YK", karar=_yedek_karari(donem, durum=durum))
    assert OrganMembership.objects.get(pk=uyeler[4].pk).promoted_on is None


@pytest.mark.kural_davranis(f"{YK}.yedek_cagirma")
def test_sira_disi_ve_kararsiz_cagri_iki_ayri_satir() -> None:
    """Sıra dışı ve kararsız çağrıda iki denetim sırayla koşar: md. 13/6 satırı yalnız sıradandır,
    karar bağı yokluğu ayrı akış satırıdır; ikisi aynı gerekçeyle kaydedilir."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem, asil=4, yedek=2)
    with pytest.raises(GerekceGerekli) as hata:
        uyelik_gecisleri.yedek_cagir(uyeler[5], organ="YK")
    assert "sıra dışı" in str(hata.value.detail) and "md. 13/6" in str(hata.value.detail)
    cagrilan = uyelik_gecisleri.yedek_cagir(
        uyeler[5], organ="YK", gerekce=uyum.Gerekce(metin="Uydurma: birinci yedek çekildi.")
    )
    (sira,) = _satirlar(cagrilan, f"{YK}.yedek_cagirma")
    assert "sıra dışı" in sira.message and "kararına" not in sira.message
    (akis,) = _satirlar(cagrilan, uyelik_gecisleri.KARARSIZ_CAGRI_AKISI)
    assert akis.kind == ComplianceKind.SAPMA


def test_cagri_gunu_secimden_once_olamaz() -> None:
    """Yedeğin çağrı günü seçildiği günden önce olamaz (sert, tarih sırası)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem, asil=4, yedek=1)
    with pytest.raises(ValueError, match="seçildiği günden önce"):
        uyelik_gecisleri.yedek_cagir(
            uyeler[4], organ="YK", promoted_on=date(2026, 10, 14), karar=_yedek_karari(donem)
        )


@pytest.mark.kural_davranis(f"{YK}.yedek_cagirma")
def test_yedek_sirasi_girilmemisse_tamamlanacak() -> None:
    """Bekleyen yedeklerden birinin sırası girilmemişse sıra eksiktir (gerekçe istemez, R5)."""
    donem = o.donem()
    o.yk_kurulu(donem, asil=4)
    yedek = o.secilmis(donem, seat_type=SeatType.YEDEK)
    cagrilan = uyelik_gecisleri.yedek_cagir(yedek, organ="YK", karar=_yedek_karari(donem))
    (satir,) = _satirlar(cagrilan, f"{YK}.yedek_cagirma")
    assert satir.kind == ComplianceKind.EKSIK


# ============================================================ düşme ve md. 7/2


@pytest.mark.kural_davranis("uyelik.ayrilan_veli_devam")
@pytest.mark.parametrize("tur", ["veli", "kursiyer"])
def test_yk_4_altina_duserse_ayrilan_uye_devam_onerisi(tur: str) -> None:
    """Öğrencisi ayrılan velinin (eğitimini tamamlayan kursiyerin) üyeliği, kurul toplantı yeter
    sayısının (4) altına düşecekse olağanüstü genel kurula kadar sürer (md. 7/2): düşürme gerekçe
    ister, erteleme işaretlenir. Beş asıllı kurulda dört kalır: gerekçesiz düşer."""
    donem = o.donem()
    kisi = (
        o.kisi(kind=PersonKind.KURSIYER, is_parent=False, adult_declared=True)
        if tur == "kursiyer"
        else o.kisi()
    )
    ayrilan = o.secilmis(donem, kisi)
    o.yk_kurulu(donem, asil=3)
    with pytest.raises(GerekceGerekli) as hata:
        uyelik_gecisleri.uyeligi_dusur(ayrilan, drop_kind="OGRENCI_AYRILDI")
    assert "olağanüstü genel kurula kadar" in str(hata.value.detail)
    assert "md. 7/2" in str(hata.value.detail)
    ertelenen = uyelik_gecisleri.uyeligi_dusur(ayrilan, drop_kind="OGRENCI_AYRILDI", ertele=True)
    assert (ertelenen.status, ertelenen.retained_until_assembly) == (MembershipStatus.SECILDI, True)
    assert _satirlar(ertelenen, "uyelik.ayrilan_veli_devam") == []
    dusen = uyelik_gecisleri.uyeligi_dusur(
        ayrilan, drop_kind="OGRENCI_AYRILDI", gerekce=uyum.Gerekce(metin="Uydurma gerekçe.")
    )
    assert dusen.status == MembershipStatus.DUSTU
    (satir,) = _satirlar(dusen, "uyelik.ayrilan_veli_devam")
    assert satir.kind == ComplianceKind.SAPMA
    # Beş asıllı kurulda düşen veliyle dört asıl kalır: istisna yok, gerekçesiz düşer.
    yeterli = o.secilmis(donem)
    o.yk_kurulu(donem, asil=1)
    assert uyelik_gecisleri.uyeligi_dusur(yeterli, drop_kind="OGRENCI_AYRILDI").status == (
        MembershipStatus.DUSTU
    )
    with pytest.raises(ValueError, match="md. 7/2"):
        uyelik_gecisleri.uyeligi_dusur(o.secilmis(donem), drop_kind="ISTIFA", ertele=True)


@pytest.mark.kural_davranis("uyelik.ayrilan_veli_devam")
def test_dusurme_gerekcesiz_reddedilir() -> None:
    """UYARLA (tasarım §12.A): düşmede zorunlu olan türdür (`drop_kind`), serbest gerekçe isteğe
    bağlıdır; türsüz düşme servis ve uçta reddedilir, aday düşürülmez."""
    donem = o.donem()
    uyelik = o.secilmis(donem)
    with pytest.raises(ValueError, match="Düşme türü"):
        uyelik_gecisleri.uyeligi_dusur(uyelik, drop_kind="")
    yanit = APIClient().post(f"/api/v1/oab/memberships/{uyelik.pk}/drop/", {}, format="json")
    assert yanit.status_code == 400 and "drop_kind" in yanit.json()["fields"]
    assert OrganMembership.objects.get(pk=uyelik.pk).status == MembershipStatus.SECILDI
    aday = o.yk_adayi(donem, o.kisi(), o.olaganustu_genel_kurul(donem))
    with pytest.raises(ValueError, match="Yalnız seçilmiş"):
        uyelik_gecisleri.uyeligi_dusur(aday, drop_kind="ISTIFA")


@pytest.mark.kural_davranis("uyelik.ayrilan_veli_devam")
def test_dusme_gerekcesi_kaydi() -> None:
    """Düşme gerekçesi isteğe bağlı ve şifrelidir; KVKK boşaltma kümesindedir, iz satırına ve kadro
    serileştiricisine girmez."""
    donem = o.donem()
    uyelik = o.secilmis(donem)
    dusen = uyelik_gecisleri.uyeligi_dusur(
        uyelik,
        drop_kind="ISTIFA",
        end_date=date(2026, 11, 2),
        dropped_reason="Uydurma istifa dilekçesi.",
    )
    assert (dusen.status, dusen.drop_kind, dusen.end_date) == (
        MembershipStatus.DUSTU,
        "ISTIFA",
        date(2026, 11, 2),
    )
    assert OrganMembership.objects.get(pk=uyelik.pk).dropped_reason == "Uydurma istifa dilekçesi."
    iz = AuditTrail.objects.filter(model="oab.OrganMembership", object_id=str(uyelik.pk)).last()
    assert iz is not None and iz.action == "DURUM" and "dropped_reason" not in iz.values
    yanit = APIClient().get(f"/api/v1/oab/memberships/{uyelik.pk}/")
    assert "dropped_reason" not in yanit.json()
    with pytest.raises(ValueError, match="seçilme gününden önce"):
        uyelik_gecisleri.uyeligi_dusur(
            o.secilmis(donem), drop_kind="ISTIFA", end_date=date(2026, 10, 1)
        )


# ============================================================ suç ve tek birlik engelleri


def _engelli_aday(donem: Any, dayanak: str) -> OrganMembership:
    aday = o.yk_adayi(donem, o.kisi(external_yk_terms=0), o.olaganustu_genel_kurul(donem))
    return uyelik_gecisleri.engel_yaz(
        aday,
        eligibility_bar=EligibilityBar.VAR,
        eligibility_bar_basis=dayanak,
        eligibility_bar_found_on=date(2026, 10, 14),
    )


@pytest.mark.kural_davranis(f"{YK}.tek_birlik")
def test_baska_birlikte_gorevli_isaretiyle_uyari() -> None:
    """Başka birlik yönetiminde görev işaretli adayın seçimi uyarı + gerekçedir (md. 12/4 2. cümle);
    görevdeki üyede işaret düşürme önerisidir (kayıt engellenmez)."""
    donem = o.donem()
    aday = _engelli_aday(donem, "TEK_BIRLIK_12_4")
    with pytest.raises(GerekceGerekli) as hata:
        uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
    assert "md. 12/4" in str(hata.value.detail)
    secilen = uyelikler.elect_membership(
        aday, start_date=o.SECIM_GUNU, gerekce=uyum.Gerekce(metin="Uydurma gerekçe.")
    )
    (satir,) = _satirlar(secilen, f"{YK}.tek_birlik")
    assert satir.kind == ComplianceKind.SAPMA
    assert [oneri.tur for oneri in uyelik_gecisleri.oneriler(secilen)][0] == "DUSURME"


@pytest.mark.kural_davranis(f"{YK}.tek_birlik")
def test_tek_birlik_beyani_yoksa_mevzuat_uyarisi_yok() -> None:
    """Beyan almak okulun uygulamasıdır (KM-8): beyan günü yoksa mevzuat uyarısı ve uyum satırı
    yoktur, yalnız okul uygulaması hatırlatması (madde atfı taşımaz); beyan girilince kalkar."""
    donem = o.donem()
    aday = o.yk_adayi(donem, o.kisi(external_yk_terms=0), o.olaganustu_genel_kurul(donem))
    secilen = uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
    assert _satirlar(secilen, f"{YK}.tek_birlik") == []
    metinler = [oneri.metin for oneri in uyelik_gecisleri.oneriler(secilen)]
    assert uyelik_gecisleri.TEK_BIRLIK_BEYANI_HATIRLATMASI in metinler
    assert not any("md." in metin for metin in metinler)
    beyanli = uyelikler.update_membership(secilen, single_birlik_declared_on=date(2026, 10, 15))
    assert uyelik_gecisleri.TEK_BIRLIK_BEYANI_HATIRLATMASI not in [
        oneri.metin for oneri in uyelik_gecisleri.oneriler(beyanli)
    ]


@pytest.mark.kural_davranis("uyelik.suc_engeli")
def test_engel_tespitinde_dusurme_onerisi_tespit_tarihiyle() -> None:
    """Görevdeki üyede engel tespiti düşürme önerisidir: tespit günüyle, `DIGER` düşme türüyle
    (tür suçu ele vermez, KVKK md. 6/1); öneri metni dayanağı söylemez. Seçimde uyarı + gerekçedir."""
    donem = o.donem()
    uye = o.secilmis(donem)
    engelli = uyelik_gecisleri.engel_yaz(
        uye,
        eligibility_bar=EligibilityBar.VAR,
        eligibility_bar_basis="SUC_12_5_14_7",
        eligibility_bar_found_on=date(2026, 11, 5),
    )
    (oneri,) = [x for x in uyelik_gecisleri.oneriler(engelli) if x.tur == "DUSURME"]
    assert (oneri.gun, oneri.drop_kind) == (date(2026, 11, 5), "DIGER")
    assert "05.11.2026" in oneri.metin and "suç" not in oneri.metin.lower()
    assert _satirlar(engelli, "uyelik.suc_engeli") == []
    dusen = uyelik_gecisleri.uyeligi_dusur(engelli, drop_kind="DIGER", end_date=oneri.gun)
    assert (dusen.status, dusen.end_date) == (MembershipStatus.DUSTU, date(2026, 11, 5))
    aday = _engelli_aday(donem, "SUC_12_5_14_7")
    with pytest.raises(GerekceGerekli) as hata:
        uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
    assert "md. 12/5" in str(hata.value.detail)
    with pytest.raises(ValueError, match="dayanağı ve tespit günü"):
        uyelik_gecisleri.engel_yaz(o.secilmis(donem), eligibility_bar=EligibilityBar.VAR)


@pytest.mark.kural_davranis("uyelik.suc_engeli")
def test_beyansiz_uye_okul_uygulamasi_hatirlatmasi() -> None:
    """Okulun beyan uygulaması işaretlenmediyse yalnız hatırlatma: uyum satırı yok, gerekçe yok."""
    donem = o.donem()
    uye = o.secilmis(donem)
    assert uyelik_gecisleri.SUC_BEYANI_HATIRLATMASI in [
        oneri.metin for oneri in uyelik_gecisleri.oneriler(uye)
    ]
    assert not ComplianceItem.objects.filter(rule_id="uyelik.suc_engeli").exists()
    beyanli = uyelikler.update_membership(uye, eligibility_declared_on=date(2026, 10, 15))
    assert uyelik_gecisleri.SUC_BEYANI_HATIRLATMASI not in [
        oneri.metin for oneri in uyelik_gecisleri.oneriler(beyanli)
    ]


@pytest.mark.kural_davranis("uyelik.suc_engeli")
def test_beyan_yalniz_tarih() -> None:
    """Beyanın içeriği ve adli sicil verisi tutulmaz (KVKK; envanter S-20): yalnız tarih alanıdır."""
    alan = OrganMembership._meta.get_field("eligibility_declared_on")
    assert alan.get_internal_type() == "DateField"
    adlar = {f.name for f in OrganMembership._meta.get_fields()}
    assert not {a for a in adlar if "declaration" in a or a.startswith("eligibility_note")}


# ============================================================ alım komisyonu (md. 18/1)


def _alim_uyarilari(donem: Any) -> list[str]:
    return [s["atif"] for s in uyelikler.kadro_uyarilari(donem, "ALIM_KOMISYONU")]


@pytest.mark.kural_davranis("harcama.alim_komisyonu_en_az")
def test_alim_komisyonu_ucten_az_uyari() -> None:
    """Organ ekranında iki kişilik komisyon uyarıdır (gerekçe istemez; yazım engellenmez)."""
    donem = o.donem()
    for _ in range(2):
        temsilciler.alim_komisyonu_uyesi_ekle(term=donem, person=o.kisi())
    assert _alim_uyarilari(donem) == ["md. 18/1"]
    yanit = APIClient().get(f"/api/v1/oab/terms/{donem.pk}/roster/ALIM_KOMISYONU/")
    assert yanit.status_code == 200 and yanit.json()["kadro"]["asil"] == 2
    assert [u["atif"] for u in yanit.json()["kadro_uyarilari"]] == ["md. 18/1"]


@pytest.mark.kural_davranis("harcama.alim_komisyonu_en_az")
def test_uc_kisilik_alim_komisyonu_uyarisiz() -> None:
    donem = o.donem()
    for _ in range(3):
        temsilciler.alim_komisyonu_uyesi_ekle(term=donem, person=o.kisi())
    assert _alim_uyarilari(donem) == []
    kisi = OrganMembership.objects.filter(organ="ALIM_KOMISYONU").first()
    assert kisi is not None
    with pytest.raises(ValueError, match="zaten var"):
        temsilciler.alim_komisyonu_uyesi_ekle(term=donem, person=kisi.person)


# ============================================================ karar defterinin noter tasdiki (md. 23/2)

TASDIK = f"{YK}.karar_defteri_noter_tasdiki"
#: Kuralın ekran metni (paketten gelir; burada elle yazıldı). Atıf `madde`den eklenir.
TASDIK_METNI = (
    "Yönetim kurulu karar defterinin noterce tasdik edilmesi zorunludur; programa defterin noter "
    "tasdiki ve tasdik günü girilmedi."
)
TASDIK_GUNU = date(2024, 9, 2)


def _defter(makam: str = "", gun: date | None = None) -> OfficialBook:
    """Karar defteri kaydı (dönemsiz); tasdik bilgisi verilen makam ve gündür. Değerler uydurmadır."""
    return kurullar.karar_defteri_olustur(
        certified_by=makam, certified_on=gun, last_no_before_program=7, last_page_before_program=3
    )


def _tasdik_satirlari(defter: OfficialBook) -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(
            subject_type="oab.OfficialBook", subject_id=str(defter.pk), rule_id=TASDIK
        ).order_by("pk")
    )


@pytest.mark.kural_davranis(TASDIK)
def test_noter_tasdiki_ve_gunu_girilmis_karar_defteri_uyarisiz() -> None:
    """Sapma yokken uyarısız: noter tasdiki ve günü girilmiş defter `uygun`dur, satır açılmaz."""
    donem = o.donem()
    defter = _defter(BookCertifier.NOTER, TASDIK_GUNU)
    sonuc = kurullar.tasdik_denetimi(defter, donem=donem)
    assert sonuc.sonuc["durum"] == "uygun" and sonuc.satir is None
    assert _tasdik_satirlari(defter) == []


@pytest.mark.kural_davranis(TASDIK)
@pytest.mark.parametrize(
    ("makam", "gun"),
    [
        pytest.param("", None, id="tasdik-bilgisi-yok"),
        pytest.param(BookCertifier.NOTER, None, id="tasdik-gunu-yok"),
        pytest.param(BookCertifier.IL_ILCE_MEM, TASDIK_GUNU, id="il-ilce-mem-tasdiki"),
    ],
)
def test_noter_tasdiki_yoksa_gerekcesiz_reddedilir(makam: str, gun: date | None) -> None:
    """Eksik tasdik bilgisi de sapmadır (`eksik_veri: sapma`); il/ilçe millî eğitim müdürlüğü tasdiki
    öteki defterlerindir, karar defterine yetmez (md. 23/2). Gerekçesiz geçmez; ileti atıflıdır."""
    donem = o.donem()
    defter = _defter(makam, gun)
    with pytest.raises(GerekceGerekli) as hata:
        kurullar.tasdik_denetimi(defter, donem=donem)
    assert f"{TASDIK_METNI.rstrip('.')} (md. 23/2)." in str(hata.value.detail)
    assert "Yönetmelik gereği" not in str(hata.value.detail)
    assert _tasdik_satirlari(defter) == []


@pytest.mark.kural_davranis(TASDIK)
def test_noter_tasdiki_sapmasi_gerekceyle_kaydedilir_defter_basina_bir_gerekce() -> None:
    """Gerekçeyle kaydedilir; satır kural kimliği, paket ve revizyonla izde durur. Konu defterdir,
    gerekçe defter başına birdir (O3): aynı defter yeniden denetlenince (F3'ün "deftere işlendi"
    işareti) gerekçe yeniden sorulmaz; başka defter kendi gerekçesini ister."""
    donem = o.donem()
    defter = _defter(BookCertifier.IL_ILCE_MEM, TASDIK_GUNU)
    sonuc = kurullar.tasdik_denetimi(defter, donem=donem, gerekce="Uydurma gerekçe metni.")
    (satir,) = _tasdik_satirlari(defter)
    assert sonuc.satir is not None and sonuc.satir.pk == satir.pk
    assert (satir.kind, satir.rule_package, satir.rev, satir.message) == (
        ComplianceKind.SAPMA,
        "OAB-2023.12",
        1,
        TASDIK_METNI,
    )
    assert satir.justification_group is not None
    assert satir.justification_group.root_cause == kurullar.tasdik_kok_nedeni(defter)
    iz = AuditTrail.objects.filter(model="oab.ComplianceItem", object_id=str(satir.pk)).first()
    assert iz is not None and iz.values["rule_id"][1] == TASDIK and iz.values["rev"][1] == 1
    tekrar = kurullar.tasdik_denetimi(defter, donem=donem)
    assert tekrar.satir is not None and tekrar.satir.pk == satir.pk
    assert ComplianceJustification.objects.filter(rule_id=TASDIK).count() == 1
    with pytest.raises(GerekceGerekli):
        kurullar.tasdik_denetimi(_defter(), donem=donem)


@pytest.mark.kural_davranis(TASDIK)
def test_noter_tasdiki_kural_paketindedir_akis_satiri_degil() -> None:
    """Kimlik paketteki kuraldır (altın kural 1 ve 2): atıf md. 23/2, kimlik akış önekli değildir."""
    assert kurullar.TASDIK_KURALI == TASDIK
    assert not TASDIK.startswith(uyum.AKIS_ONEKI)
    sonuc = paket_denetle(TASDIK, BookCertifier.NOTER.value, tarih=TASDIK_GUNU)
    assert sonuc["durum"] == "uygun"
    for gozlenen in (BookCertifier.IL_ILCE_MEM.value, VERI_YOK):
        sonuc = paket_denetle(TASDIK, gozlenen, tarih=TASDIK_GUNU)
        assert (sonuc["durum"], sonuc["mesaj"], sonuc["atif"]) == (
            "uyari",
            TASDIK_METNI,
            "md. 23/2",
        )
