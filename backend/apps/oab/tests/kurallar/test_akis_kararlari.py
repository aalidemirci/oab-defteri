"""Akış, model ve KVKK kararları (`ak`, tasarım §10.7; F1c 5. adım: organ üyeliğinin kısıtları).

`OrganMembership`'in iki kısmi tekil kısıtı, ikisi de `IPTAL` olmayan kayıtlarda (tasarım §5.2.2; plan
F1c kararları; denetim UY-10): genel kurul bağı boşken (dönem, organ, kişi, temsil türü), doluyken
(dönem, organ, kişi, genel kurul). SQLite tekil dizinde NULL'ları ayrı saydığından tek kısıt genel
kurul dışı seçimlerde etkisiz kalırdı. Geçiş kurulumunda görevdeki kurul `DEVRALINAN` üyelikle aday
şartı olmadan seçilmiş açılır (§7.9); toplu sayaç beyanı geçiş kurulumunun adımıdır (8. adım).
Bir kişi aynı dönemde aynı kurulda tek koltuk tutar (kullanıcı kararı 10.11.2026). F2 4. adımdan
beri genel kurulun hazırlık dönemi senaryoları, 5. adımdan beri veli listesinin katılım işareti
(dosyanın sonu).
Kişi adları UYDURMADIR.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from django.db import IntegrityError, transaction

from apps.oab.hatalar import GecisKapali, GerekceGerekli, KuralSert
from apps.oab.models import (
    AssemblyKind,
    AssemblyMeeting,
    AssemblyStatus,
    AttendanceCorrection,
    ComplianceItem,
    ComplianceJustification,
    ComplianceKind,
    DropKind,
    ElectedBy,
    GeneralAssembly,
    MembershipSource,
    MembershipStatus,
    OabTerm,
    OrganMembership,
    Representation,
    SeatGroup,
    TermStatus,
)
from apps.oab.services import donem_kilidi, gecis, genel_kurul, kisiler, uyelikler
from apps.oab.tests import genel_kurul_ortak as gko
from apps.oab.tests import uyelik_ortak as o
from apps.oab.tests.kurallar import paket_ortak
from apps.okul.models import (
    AccessKind,
    AccessLog,
    AccountRole,
    AuditAction,
    AuditTrail,
    ParentRoster,
)
from apps.okul.services import imports as import_service
from shared.exceptions import RolYetkisiz

pytestmark = pytest.mark.django_db


def _ham(**alanlar: Any) -> OrganMembership:
    """Kısıtın kendisini sınamak için servissiz yazım (servis aynı durumu Türkçe iletiyle keser)."""
    varsayilan: dict[str, Any] = {
        "organ": "YK",
        "seat_type": "ASIL",
        "elected_by": ElectedBy.GENEL_KURUL,
        "status": MembershipStatus.SECILDI,
    }
    return OrganMembership.objects.create(**{**varsayilan, **alanlar})


def test_genel_kurulsuz_ayni_uyelik_iki_kez_reddedilir() -> None:
    donem = o.donem()
    kisi = o.kisi()
    o.devralinan(donem, kisi)
    with pytest.raises(ValueError, match="zaten var"):
        o.devralinan(donem, kisi)
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(term=donem, person=kisi)
    assert OrganMembership.objects.count() == 1


def test_iptal_uyelik_tekil_kisita_girmez() -> None:
    donem = o.donem()
    kisi = o.kisi()
    yanlis = o.devralinan(donem, kisi)
    yanlis.status = MembershipStatus.IPTAL
    yanlis.save(update_fields=["status"])
    yeniden = o.devralinan(donem, kisi)
    assert yeniden.pk != yanlis.pk
    assert OrganMembership.objects.filter(person=kisi).count() == 2
    # Genel kurullu kısıtta da `IPTAL` kısıt dışıdır.
    kurul = o.olaganustu_genel_kurul(donem)
    ikinci = o.kisi()
    aday = o.yk_adayi(donem, ikinci, kurul)
    aday.status = MembershipStatus.IPTAL
    aday.save(update_fields=["status"])
    assert o.yk_adayi(donem, ikinci, kurul).status == MembershipStatus.ADAY


def test_genel_kurulsuz_kisitta_temsil_turu_ayirir() -> None:
    """Aynı veli iki kurulda temsilci olabilir; aynı kurulda iki kez olamaz (plan F1c kararları)."""
    donem = o.donem()
    kisi = o.kisi()
    temsilci = {"term": donem, "person": kisi, "organ": "TEMSILCI", "elected_by": "YK_KARARI"}
    _ham(**temsilci, representation=Representation.ODUL_DISIPLIN_KURULU)
    _ham(**temsilci, representation=Representation.SOSYAL_ETKINLIKLER_KURULU)
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(**temsilci, representation=Representation.ODUL_DISIPLIN_KURULU)
    assert OrganMembership.objects.filter(organ="TEMSILCI").count() == 2
    # Temsil türü temsilcide zorunlu, öteki organlarda boş dizedir (`NULL` değil).
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(**{**temsilci, "person": o.kisi()}, representation="")
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(term=donem, person=o.kisi(), representation=Representation.DIGER)


def test_genel_kurullu_kisit_genel_kurulu_ayirir() -> None:
    """Aynı kişi aynı genel kurulda iki kez aday olamaz; başka genel kurulda olabilir (md. 13/8)."""
    donem = o.donem()
    kisi = o.kisi()
    ilk = o.olaganustu_genel_kurul(donem)
    o.yk_adayi(donem, kisi, ilk)
    with pytest.raises(ValueError, match="zaten var"):
        o.yk_adayi(donem, kisi, ilk)
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(term=donem, person=kisi, assembly=ilk, status=MembershipStatus.ADAY)
    ikinci = o.olaganustu_genel_kurul(donem)
    assert o.yk_adayi(donem, kisi, ikinci).status == MembershipStatus.ADAY


def test_devralinan_uyelik_aday_sarti_olmadan_secildi() -> None:
    """Geçiş kurulumunda görevdeki kurul devralınan üyelikle, aday kaydı olmadan seçilmiş açılır;
    genel kurul bağı yoktur, koltuk uygunluğu yine serttir (§7.9)."""
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi(), role="BASKAN")
    assert (uyelik.status, uyelik.source, uyelik.assembly_id) == (
        MembershipStatus.SECILDI,
        MembershipSource.DEVRALINAN,
        None,
    )
    assert uyelik.start_date == o.GUN
    assert not OrganMembership.objects.filter(status=MembershipStatus.ADAY).exists()
    kurul = o.olaganustu_genel_kurul(donem)
    with pytest.raises(ValueError, match="yalnız genel kurul seçiminde"):
        uyelikler.assign_membership(
            term=donem,
            person=o.kisi(),
            organ="YK",
            seat_type="ASIL",
            elected_by=ElectedBy.GENEL_KURUL,
            assembly=kurul,
            source=MembershipSource.DEVRALINAN,
        )


# ============================================================ tek koltuk (kullanıcı kararı 10.11.2026)
# Bir kişi aynı dönemde aynı kurulda tek koltuk tutar (sert, hesap bütünlüğü; plan F1c 5. adım
# notları). Koltuk seçilmiş kayıttır: aday, düşmüş ve iptal kaydı koltuk değildir. Kural yalnız
# yönetim kurulunda ve Denetleme Kurulunda uygulanır.


def _dusur(uyelik: OrganMembership, tur: str) -> None:
    """Düşme servisi 6. adımda; durum makinesi geçişi ORM'le."""
    uyelik.status, uyelik.drop_kind = MembershipStatus.DUSTU, tur
    uyelik.save(update_fields=["status", "drop_kind"])


def test_dusen_uye_ayni_donemde_ayni_kurula_yeniden_secilebilir() -> None:
    """Olağanüstü genel kurul aynı dönemde yeni kurul seçer, görevdeki eski üyelikler düşer
    (`OLAGANUSTU_GK_SECIMI`; tasarım §7.1, md. 13/8); eski üye yeniden seçilebilir. Düşmüş kayıt
    koltuk değildir; seçilme sayacına ise ikisi de girer (§15 B-12)."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    kurul = o.olaganustu_genel_kurul(donem)
    eski = o.devralinan(donem, kisi)
    aday = o.yk_adayi(donem, kisi, kurul)  # aday kaydı koltuk değil: görevdeki üye aday olabilir
    with pytest.raises(ValueError, match="tek koltuk"):
        uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
    _dusur(eski, DropKind.OLAGANUSTU_GK_SECIMI)
    yeni = uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
    assert yeni.status == MembershipStatus.SECILDI
    durumlar = sorted(OrganMembership.objects.filter(person=kisi).values_list("status", flat=True))
    assert durumlar == [MembershipStatus.DUSTU, MembershipStatus.SECILDI]


def test_secilmeyen_aday_kaydi_koltuk_degil() -> None:
    """Seçilmeyen aday kaydı aday kalır; aynı kişi dönemin başka genel kurulunda seçilebilir
    (md. 13/8). Aday kaydı koltuk değildir: seçilme anında yalnız seçilmiş kayıtlar sayılır."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    ilk = o.yk_adayi(donem, kisi, o.olaganustu_genel_kurul(donem))
    ikinci = o.yk_adayi(donem, kisi, o.olaganustu_genel_kurul(donem))
    assert uyelikler.elect_membership(ikinci, start_date=o.SECIM_GUNU).status == (
        MembershipStatus.SECILDI
    )
    assert OrganMembership.objects.get(pk=ilk.pk).status == MembershipStatus.ADAY


def test_iptal_kayit_koltuk_degil() -> None:
    """İptal edilmiş kayıt hiç olmamıştır (yanlış kayıt): aynı kurulda başka koltuğu engellemez."""
    donem = o.donem()
    kisi = o.ogretmen(is_parent=True)
    yanlis = o.dk_ogretmeni(donem, kisi)
    yanlis.status = MembershipStatus.IPTAL
    yanlis.save(update_fields=["status"])
    kurul = o.olaganustu_genel_kurul(donem)
    aday = uyelikler.assign_membership(
        term=donem,
        person=kisi,
        organ="DK",
        seat_type="ASIL",
        seat_group=SeatGroup.VELI,
        elected_by=ElectedBy.GENEL_KURUL,
        assembly=kurul,
    )
    assert uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU).status == (
        MembershipStatus.SECILDI
    )


def test_tek_koltuk_temsilcide_uygulanmaz() -> None:
    """Temsilcide temsil türleri ayrı koltuktur (genel kurulsuz tekil kısıt temsil türüyle ayırır):
    aynı veli iki kurulda temsilci olabilir; tek koltuk yalnız yönetim kurulu ve Denetleme Kurulunda."""
    assert frozenset({"YK", "DK"}) == uyelikler.TEK_KOLTUKLU_KURULLAR
    donem = o.donem()
    kisi = o.kisi()
    temsilci = {"term": donem, "person": kisi, "organ": "TEMSILCI", "elected_by": "YK_KARARI"}
    _ham(**temsilci, representation=Representation.ODUL_DISIPLIN_KURULU)
    ikinci = _ham(**temsilci, representation=Representation.SOSYAL_ETKINLIKLER_KURULU)
    assert not uyelikler._ikinci_koltuk(ikinci)
    # Aynı durum yönetim kurulunda ikinci koltuktur (servis dışı yazılmış kayıt üstünde).
    _ham(term=donem, person=kisi, assembly=o.olaganustu_genel_kurul(donem))
    yk = _ham(term=donem, person=kisi, assembly=o.olaganustu_genel_kurul(donem))
    assert uyelikler._ikinci_koltuk(yk)


# ============================================================ geçiş kurulumu (F1c 8. adım; tasarım §7.9)
# Devralınan kurul aday şartı olmadan seçilmiş açılır, koltuk uygunluğu yine serttir (adım 2);
# programdan önceki seçilme sayılarının "bilinmiyor" beyanı tek gerekçeyle kapanır (adım 3, R5).

SAYAC = "yonetim_kurulu.secilme_siniri"


def test_devralinan_uyelik_koltuk_uygunlugu_yine_serttir() -> None:
    """§7.9 adım 2 [S]: kişi türü, müdür yasağı, aynı kişi iki kurulda, görev tekilliği."""
    donem = o.donem()
    with pytest.raises(KuralSert):
        gecis.devralinan_ekle(person=o.ogretmen(), organ="YK")  # veli değil
    mudur = kisiler.update_person(o.kisi(), is_principal=True)
    with pytest.raises(KuralSert):
        gecis.devralinan_ekle(person=mudur, organ="YK")
    hayirsever = o.kisi(kind="HAYIRSEVER", is_parent=False)
    with pytest.raises(KuralSert):
        gecis.devralinan_ekle(person=hayirsever, organ="DK", seat_group=SeatGroup.VELI)
    ikili = o.kisi()
    gecis.devralinan_ekle(person=ikili, organ="YK", role="BASKAN")
    with pytest.raises(KuralSert):
        gecis.devralinan_ekle(person=ikili, organ="DK", seat_group=SeatGroup.VELI)
    with pytest.raises(KuralSert):
        gecis.devralinan_ekle(person=o.kisi(), organ="YK", role="BASKAN")  # görev tekil
    assert list(OrganMembership.objects.values_list("person_id", "organ")) == [(ikili.pk, "YK")]
    assert OrganMembership.objects.get().term_id == donem.pk


def test_devralinan_uyelik_gecis_tamamlaninca_acilmaz() -> None:
    """Devralınan üyelik geçiş kaydıdır: "Geçiş kurulumu tamamlandı" işaretinden sonra açılmaz."""
    donem = o.donem()
    o.devralinan(donem, o.kisi())
    gecis.gecisi_tamamla(donem)
    kisi = o.kisi()
    with pytest.raises(GecisKapali):
        o.devralinan(donem, kisi)
    assert OrganMembership.objects.count() == 1


def test_gecis_toplu_sayac_beyani_tek_gerekce() -> None:
    """§7.9 adım 3 [U], §5 O3 "toplu gerekçe": "bilinmiyor" denen bütün kişiler için seçilme sınırı
    satırı bir kez, tek gerekçeyle kapanır; sonraki beyanda yeniden sorulmaz. Programdaki seçimin açık
    sayaç eksiği de aynı gerekçeye bağlanır, sayı beyan edilince kapanır."""
    donem = o.donem()
    gorevdekiler = [o.kisi() for _ in range(3)]
    for kisi in gorevdekiler:
        gecis.devralinan_ekle(person=kisi, organ="YK")
    beyan = [gecis.SayacBeyani(kisi=kisi, yk=None) for kisi in gorevdekiler]
    with pytest.raises(GerekceGerekli):
        gecis.sayac_beyani(beyan)
    assert not ComplianceItem.objects.exists()
    sonuc = gecis.sayac_beyani(beyan, gerekce="Uydurma: eski karar defteri elde değil.")
    assert len(sonuc.bilinmeyenler) == 3
    assert {(s.kind, s.subject_type, s.rule_id) for s in sonuc.bilinmeyenler} == {
        (ComplianceKind.SAPMA, "oab.OabPerson", SAYAC)
    }
    tek = ComplianceJustification.objects.get(rule_id=SAYAC)
    assert tek.root_cause == gecis.sayac_kok_nedeni(donem)
    assert {s.justification_group_id for s in sonuc.bilinmeyenler} == {tek.pk}
    # Sonra eklenen kişi de aynı gerekçeye bağlanır: aday başına yeniden sorulmaz.
    sonraki = gecis.sayac_beyani([gecis.SayacBeyani(kisi=o.kisi(), yk=None)])
    assert sonraki.bilinmeyenler[0].justification_group_id == tek.pk
    # Aynı beyan yinelenirse yeni satır açılmaz.
    assert gecis.sayac_beyani(beyan).bilinmeyenler == sonuc.bilinmeyenler
    # Programdaki seçimin sayaç eksiği: "bilinmiyor"da toplu gerekçeye bağlanır, sayıda kapanır.
    kurul = o.olaganustu_genel_kurul(donem)
    a, b = o.kisi(), o.kisi()
    ua = uyelikler.elect_membership(o.yk_adayi(donem, a, kurul), start_date=o.SECIM_GUNU)
    ub = uyelikler.elect_membership(o.yk_adayi(donem, b, kurul), start_date=o.SECIM_GUNU)

    def satir(uyelik: OrganMembership) -> ComplianceItem:
        return ComplianceItem.objects.get(
            subject_type="oab.OrganMembership", subject_id=str(uyelik.pk), rule_id=SAYAC
        )

    assert {satir(ua).kind, satir(ub).kind} == {ComplianceKind.EKSIK}
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=a, yk=None), gecis.SayacBeyani(kisi=b, yk=0)])
    assert (satir(ua).kind, satir(ua).justification_group_id, satir(ua).resolved_at) == (
        ComplianceKind.SAPMA,
        tek.pk,
        None,
    )
    assert satir(ub).resolved_at is not None
    assert ComplianceJustification.objects.filter(rule_id=SAYAC).count() == 1


# ---------------------------------------------------------------------------
# F2 4. adım: hazırlık dönemi (tasarım §5.2.1, §7.1, §7.8; plan F2 §5.2, §7 U2-U5)
# ---------------------------------------------------------------------------
def test_hazirlik_donemi_gk_planlaninca_acilir() -> None:
    """Olağan genel kurul planlanınca yeni birlik dönemi `HAZIRLIK` açılır: aynı işlemde genel kurula
    bağlanır (U3; geçiş dönemi sanılmaz), en yeni revizyona bağlanır (U2), ders yılı birinci toplantı
    gününü içeren yıldır (U5), başlangıç günü boştur. Kapanacak dönem açık kalır. Olağanüstü genel
    kurul dönem açmaz (md. 13/8)."""
    acik = gko.acik_donem()
    kurul = gko.planla()
    hazirlik = OabTerm.objects.select_related("rule_package", "school_year").get(
        status=TermStatus.HAZIRLIK
    )
    assert kurul.term_id == acik.pk
    assert kurul.opens_term_id == hazirlik.pk
    assert hazirlik.opened_by_assembly_id == kurul.pk
    assert (hazirlik.rule_package.package, hazirlik.rule_package.rev) == (
        paket_ortak.PAKET,
        paket_ortak.EN_YENI_REV,
    )
    assert hazirlik.school_year.name == "2026-2027"
    assert (hazirlik.start_date, hazirlik.end_date) == (None, None)
    assert hazirlik.name == "2026-2027 birlik dönemi"
    assert not donem_kilidi.gecis_donemi_mi(hazirlik)
    assert gecis.gecis_donemi() == acik
    assert OabTerm.objects.get(pk=acik.pk).status == TermStatus.ACIK
    assert AuditTrail.objects.filter(model="oab.OabTerm", object_id=str(hazirlik.pk)).exists()

    olaganustu = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    assert olaganustu.opens_term_id is None
    assert OabTerm.objects.filter(status=TermStatus.HAZIRLIK).count() == 1
    # Aynı anda tek olağan genel kurul hazırlanır (tek hazırlık dönemi).
    with pytest.raises(ValueError, match="Hazırlıkta bir birlik dönemi var"):
        gko.planla()


def test_gk_iptalinde_hazirlik_donemi_iptal() -> None:
    """Genel kurul `IPTAL` olursa hazırlık dönemi de `IPTAL` olur (tasarım §7.1, sert); gerekçe zorunlu
    ve şifrelidir, iptali yalnız program yöneticisi yapar. İlan ve dondurulmuş yeter sayı iz olarak
    kalır; iptal edilmiş kurulun yeter sayısı dondurulmaz (U7). Sonra yeni genel kurul planlanabilir."""
    acik = gko.acik_donem()
    kurul = gko.planla()
    with pytest.raises(ValueError, match="İptal gerekçesi"):
        genel_kurul.iptal_et(kurul, cancel_reason="  ")
    with o.rol_olarak(AccountRole.SEKRETER), pytest.raises(RolYetkisiz):
        genel_kurul.iptal_et(kurul, cancel_reason="Uydurma: tarih yanlış.")
    iptal = genel_kurul.iptal_et(kurul, cancel_reason="Uydurma: tarih yanlış.")
    assert iptal.status == AssemblyStatus.IPTAL
    assert GeneralAssembly.objects.get(pk=kurul.pk).cancel_reason == "Uydurma: tarih yanlış."
    hazirlik = OabTerm.objects.get(opened_by_assembly=kurul)
    assert hazirlik.status == TermStatus.IPTAL
    assert OabTerm.objects.get(pk=acik.pk).status == TermStatus.ACIK
    with pytest.raises(ValueError, match="İptal edilmiş genel kurulun yeter sayısı"):
        genel_kurul.yeter_sayiyi_dondur(kurul, tarih=gko.BIRINCI_GUN)
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul.iptal_et(kurul, cancel_reason="Uydurma: ikinci kez.")

    yeni = gko.planla()
    assert OabTerm.objects.get(status=TermStatus.HAZIRLIK).pk == yeni.opens_term_id
    # İlandan sonra da iptal edilir; dondurulmuş yeter sayı kalır.
    gko.olagan_cagir(yeni)
    genel_kurul.ilan_et(yeni, kanallar=gko.kanallar())
    genel_kurul.iptal_et(yeni, cancel_reason="Uydurma: salon kullanılamadı.")
    sonra = GeneralAssembly.objects.get(pk=yeni.pk)
    assert (sonra.status, sonra.quorum_required) == (AssemblyStatus.IPTAL, 64)
    assert not OabTerm.objects.filter(status=TermStatus.HAZIRLIK).exists()


# ---------------------------------------------------------------------------
# F2 5. adım: veli listesinin katılım işareti (plan F2 §7 U33, S12)
# ---------------------------------------------------------------------------
#: Uydurma veli satırları (veli adı, öğrencinin sınıfı).
_VELILER = (
    ("Uydurnur Örnekkaya", "9-A"),
    ("Masalgül Hayalkaya", "9-A"),
    ("Uydurhan Örnekçi", "10-B"),
)


def _isaretli_kurul() -> GeneralAssembly:
    """Veli listesi aktarılmış, ilan edilmiş (birinci toplantısı sürmekte olan) olağan genel kurul."""
    gko.acik_donem()
    gko.veli_aktar(_VELILER)
    kurul = gko.olagan_cagir(gko.planla())
    return genel_kurul.ilan_et(kurul, kanallar=gko.kanallar()).kurul


def _satirlar(sinif: str) -> list[int]:
    return list(
        ParentRoster.objects.filter(student_class=sinif).order_by("pk").values_list("pk", flat=True)
    )


@pytest.mark.parametrize(
    "rol",
    [
        AccountRole.SEKRETER,
        AccountRole.BASKAN,
        AccountRole.MUDUR,
        AccountRole.DENETLEME_KURULU,
    ],
)
def test_katilim_isareti_yalniz_yonetici_ve_erisim_gunlugu(rol: AccountRole) -> None:
    """U33 (R9, dipnot ¹⁰): işaret penceresi veli adını gösterir; okuması da yazması da yalnız program
    yöneticisinin (kişisel veri içeren çıktı kapısı). Öteki roller `RolYetkisiz` alır, ret ne erişim
    günlüğüne ne işarete yazar. Program yöneticisinin okuması erişim günlüğüne düşer (tür veli
    listesi çıktısı, kayıt genel kurul, listenin sha256'sı ve satır sayısı; ad yok). İşaretin izi
    kişisiz `ISARET` satırıdır: satır kimliği, ad ve sınıf ize girmez."""
    kurul = _isaretli_kurul()
    dokuz_a = _satirlar("9-A")
    with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
        genel_kurul.katilim_isaretleri(kurul, toplanti=AssemblyMeeting.BIRINCI)
    with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
        genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.BIRINCI, isaretle=dokuz_a)
    assert not AccessLog.objects.exists()
    assert genel_kurul.katilim_isareti_sayisi(kurul, AssemblyMeeting.BIRINCI) == 0

    liste = genel_kurul.katilim_isaretleri(kurul, toplanti=AssemblyMeeting.BIRINCI)
    assert [s["sinif"] for s in liste] == ["9-A", "10-B"]
    assert [v["veli"] for v in liste[0]["satirlar"]] == ["Masalgül Hayalkaya", "Uydurnur Örnekkaya"]
    assert not any(v["isaretli"] or v["baska_isaret"] for s in liste for v in s["satirlar"])
    gunluk = AccessLog.objects.get()
    assert (gunluk.kind, gunluk.model, gunluk.object_id, gunluk.row_count, gunluk.role) == (
        AccessKind.VELI_LISTESI_CIKTISI,
        "oab.GeneralAssembly",
        str(kurul.pk),
        3,
        "yonetici",
    )
    assert len(gunluk.document_sha256) == 64

    assert (
        genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.BIRINCI, isaretle=dokuz_a) == 2
    )
    iz = AuditTrail.objects.get(model="okul.ParentRoster", action=AuditAction.ISARET)
    assert (iz.object_id, iz.values, iz.term_id) == ("", {}, kurul.term_id)
    assert sorted(iz.changed_fields) == ["attended_assembly", "attended_meeting"]
    metin = " ".join(
        str(deger)
        for satir in AuditTrail.objects.all()
        for deger in (satir.values, satir.changed_fields, satir.object_id)
    )
    for ad, _ in _VELILER:
        assert ad not in metin
    tekrar = genel_kurul.katilim_isaretleri(kurul, toplanti=AssemblyMeeting.BIRINCI)
    assert [v["isaretli"] for v in tekrar[0]["satirlar"]] == [True, True]
    assert AccessLog.objects.count() == 2


def test_katilim_isareti_sayiyi_degistirmez() -> None:
    """U33: işaret sayım yardımıdır. İşaret sayısı katılım sayısına öneridir; toplantının katılım
    sayısı elle girilen alan kalır, işaretten hesaplanmaz ve işaretle değişmez (düzeltme satırı da
    açılmaz). İşaret yapılmakta ya da yapılmış toplantıya konur, kaldırılabilir; birinci toplantıda
    yapılan genel kurulun ikinci toplantısı yoktur; başka genel kurulun işaretli satırı
    işaretlenmez."""
    kurul = _isaretli_kurul()
    dokuz_a, (on_b,) = _satirlar("9-A"), _satirlar("10-B")
    assert (
        genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.BIRINCI, isaretle=dokuz_a) == 2
    )
    yapildi = genel_kurul.birinci_toplanti(kurul, katilim=gko.katilim(70)).kurul
    assert (yapildi.status, yapildi.first_attendee_count) == (AssemblyStatus.YAPILDI, 70)
    assert (
        genel_kurul.katilim_isaretle(
            kurul, toplanti=AssemblyMeeting.BIRINCI, isaretle=[on_b], kaldir=dokuz_a[:1]
        )
        == 2
    )
    sonra = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (sonra.first_attendee_count, sonra.attendance_by_kind) == (70, {})
    assert not AttendanceCorrection.objects.exists()
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.IKINCI, isaretle=[on_b])
    with pytest.raises(ValueError, match="işareti yok"):
        genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.BIRINCI, kaldir=dokuz_a[:1])
    with pytest.raises(ValueError, match="veli listesinde yok"):
        genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.BIRINCI, isaretle=[0])
    # Başka (olağanüstü) genel kurulun işareti olan satır bu genel kurulda işaretlenmez.
    olaganustu = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    genel_kurul.ilan_et(olaganustu, kanallar=gko.kanallar())
    with pytest.raises(ValueError, match="başka bir genel kurulun"):
        genel_kurul.katilim_isaretle(olaganustu, toplanti=AssemblyMeeting.BIRINCI, isaretle=[on_b])
    # Planlanmış (ilan edilmemiş) genel kurulda toplantı yoktur.
    planli = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul.katilim_isaretle(planli, toplanti=AssemblyMeeting.BIRINCI, isaretle=dokuz_a)


def test_ikinci_toplantinin_katilim_isareti() -> None:
    """Pilot akışı (U33: toplantı `BIRINCI` · `IKINCI` seçilir): birinci toplantıda yeter sayı
    sağlanamayınca ikinci toplantıya işaret konur; ikinci toplantının işaret listesi okunur (erişim
    günlüğüne düşer) ve sayısı sayılır. İkinci toplantıya ilandan önce ve yeter sayı sorulmadan
    işaret konmaz. Satır tek işaret taşır: birinci toplantıda işaretli satır ikinci toplantıda
    işaretlenince işaret ikinci toplantıya taşınır (birincinin sayısı kurulda dondurulmuştur);
    liste bu satırı `oteki_toplanti` diye gösterir. Katılım sayıları işaretle değişmez."""
    gko.acik_donem()
    gko.veli_aktar(_VELILER)
    kurul = gko.olagan_cagir(gko.planla())
    genel_kurul.ilan_et(kurul, kanallar=gko.kanallar(), second_meeting_at=gko.an(date(2026, 11, 3)))
    dokuz_a, (on_b,) = _satirlar("9-A"), _satirlar("10-B")
    genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.BIRINCI, isaretle=dokuz_a)
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.IKINCI, isaretle=[on_b])
    genel_kurul.birinci_toplanti(kurul, katilim=gko.katilim(10))
    assert GeneralAssembly.objects.get(pk=kurul.pk).status == AssemblyStatus.YETER_SAYI_YOK

    gunluk_oncesi = AccessLog.objects.count()
    liste = genel_kurul.katilim_isaretleri(kurul, toplanti=AssemblyMeeting.IKINCI)
    assert AccessLog.objects.count() == gunluk_oncesi + 1
    assert [
        (v["isaretli"], v["oteki_toplanti"], v["baska_isaret"]) for v in liste[0]["satirlar"]
    ] == [(False, True, False), (False, True, False)]
    assert genel_kurul.katilim_isareti_sayisi(kurul, AssemblyMeeting.IKINCI) == 0

    assert (
        genel_kurul.katilim_isaretle(
            kurul, toplanti=AssemblyMeeting.IKINCI, isaretle=[dokuz_a[0], on_b]
        )
        == 2
    )
    assert genel_kurul.katilim_isareti_sayisi(kurul, AssemblyMeeting.BIRINCI) == 1
    tasinan = ParentRoster.objects.get(pk=dokuz_a[0])
    assert (tasinan.attended_assembly_id, tasinan.attended_meeting) == (
        kurul.pk,
        AssemblyMeeting.IKINCI,
    )
    with pytest.raises(ValueError, match="işareti yok"):
        genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.IKINCI, kaldir=dokuz_a[1:])

    genel_kurul.ikinci_toplanti(kurul, katilim=gko.katilim(5))
    assert genel_kurul.katilim_isaretle(kurul, toplanti=AssemblyMeeting.IKINCI, kaldir=[on_b]) == 1
    tekrar = genel_kurul.katilim_isaretleri(kurul, toplanti=AssemblyMeeting.IKINCI)
    assert {v["id"]: v["isaretli"] for s in tekrar for v in s["satirlar"]} == {
        dokuz_a[0]: True,
        dokuz_a[1]: False,
        on_b: False,
    }
    sonra = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (sonra.status, sonra.held_at_meeting) == (
        AssemblyStatus.YAPILDI,
        AssemblyMeeting.IKINCI,
    )
    assert (sonra.first_attendee_count, sonra.second_attendee_count) == (10, 5)
    assert not AttendanceCorrection.objects.exists()


def _ilanli_olaganustu() -> GeneralAssembly:
    kurul = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    return genel_kurul.ilan_et(kurul, kanallar=gko.kanallar()).kurul


def test_iptal_edilen_kurulun_isareti_yeni_kurulu_engellemez() -> None:
    """U33: işaret yalnız `TUTANAK_TAMAM`'a dek yazılan sayım yardımıdır, kanıt değildir (sayılar
    kurulda dondurulur). İşareti engel sayılan başka kurul yalnız işareti hâlâ yazılabilen
    (ilan edilmiş, yeter sayısı sağlanamamış ya da yapılmış) kuruldur. İptal edilen kurulun işareti
    kaldırılamaz ama aynı dönemdeki yeni kurulda üzerine yazılır; liste onu engel diye göstermez."""
    gko.acik_donem()
    gko.veli_aktar(_VELILER)
    iptal = _ilanli_olaganustu()
    dokuz_a = _satirlar("9-A")
    genel_kurul.katilim_isaretle(iptal, toplanti=AssemblyMeeting.BIRINCI, isaretle=dokuz_a)
    genel_kurul.iptal_et(iptal, cancel_reason="Uydurma: salon kullanılamadı.")
    with pytest.raises(ValueError, match="bu durumdayken"):
        genel_kurul.katilim_isaretle(iptal, toplanti=AssemblyMeeting.BIRINCI, kaldir=dokuz_a)

    yeni = _ilanli_olaganustu()
    liste = genel_kurul.katilim_isaretleri(yeni, toplanti=AssemblyMeeting.BIRINCI)
    assert not any(
        v["isaretli"] or v["oteki_toplanti"] or v["baska_isaret"]
        for s in liste
        for v in s["satirlar"]
    )
    assert (
        genel_kurul.katilim_isaretle(yeni, toplanti=AssemblyMeeting.BIRINCI, isaretle=dokuz_a) == 2
    )
    assert genel_kurul.katilim_isareti_sayisi(iptal, AssemblyMeeting.BIRINCI) == 0
    assert set(
        ParentRoster.objects.filter(pk__in=dokuz_a).values_list("attended_assembly_id", flat=True)
    ) == {yeni.pk}

    # İşareti hâlâ yazılabilen (ilan edilmiş) kurulun işareti ise öteki kurulu engeller.
    ucuncu = _ilanli_olaganustu()
    engelli = genel_kurul.katilim_isaretleri(ucuncu, toplanti=AssemblyMeeting.BIRINCI)
    assert [v["baska_isaret"] for v in engelli[0]["satirlar"]] == [True, True]
    with pytest.raises(ValueError, match="başka bir genel kurulun"):
        genel_kurul.katilim_isaretle(ucuncu, toplanti=AssemblyMeeting.BIRINCI, isaretle=dokuz_a)
    assert genel_kurul.katilim_isareti_sayisi(yeni, AssemblyMeeting.BIRINCI) == 2


def test_yeniden_aktarimda_dusen_isaret_sayisi_onizlemede() -> None:
    """Kullanıcı kararı S12 (a): önceki parti kuralı aynen; yeniden aktarılan sınıfın işaretli
    satırları işaretleriyle düşer. Önizleme düşecek işaret sayısını sınıf başına ve toplamda yalnız
    SAYI olarak gösterir (ad yok) ve hiçbir şey yazmaz; aktarım işaretleri düşürür, dokunulmayan
    sınıfın işareti kalır. Genel kuruldaki katılım sayısı dondurulmuştur, değişmez."""
    kurul = _isaretli_kurul()
    genel_kurul.katilim_isaretle(
        kurul,
        toplanti=AssemblyMeeting.BIRINCI,
        isaretle=[*_satirlar("9-A"), *_satirlar("10-B")],
    )
    genel_kurul.birinci_toplanti(kurul, katilim=gko.katilim(70))
    dosya = gko.veli_xlsx([("Hayalnur Masalcı", "9-A"), ("Uydurgül Örnekoğlu", "9-A")])

    rapor = import_service.preview_parents_file(file_bytes=dosya, file_name="yeni.xlsx")
    assert rapor.dry_run is True
    assert [(c.student_class, c.rows, c.replaced_rows, c.dropped_marks) for c in rapor.classes] == [
        ("9-A", 2, 2, 2)
    ]
    assert rapor.dropped_marks == 2
    govde = str(rapor.to_dict())
    for ad, _ in _VELILER:
        assert ad not in govde
    assert genel_kurul.katilim_isareti_sayisi(kurul, AssemblyMeeting.BIRINCI) == 3

    aktarim = import_service.commit_parents_file(file_bytes=dosya, file_name="yeni.xlsx")
    assert aktarim.dropped_marks == 2
    assert genel_kurul.katilim_isareti_sayisi(kurul, AssemblyMeeting.BIRINCI) == 1
    assert ParentRoster.objects.get(student_class="10-B").attended_assembly_id == kurul.pk
    assert GeneralAssembly.objects.get(pk=kurul.pk).first_attendee_count == 70
