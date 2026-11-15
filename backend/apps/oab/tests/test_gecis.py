"""Geçiş kurulumu, organ kısmı (tasarım §7.9 adım 1-4 ve "Senaryolar"; plan F1c-8 ve "8. adımın kararı").

* 1. adım: ilk dönem `ACIK`, genel kurulsuz; ders yılı dönem başını kapsar (yoksa ret), programa başlama
  günü verilmezse bugün, dönem başından önce olamaz; bir yıl geçmişse dönem açılır, görev süresi uyarısı.
* 2. adım: devralınan üyelik ve temsilci; görevli kayıt hesap açar, E63 basılır.
* 4. adım: karar defterinin son sıra no ve sayfası; noter tasdiki kuralı (`yonetim_kurulu.karar_
  defteri_noter_tasdiki`, md. 23/2): tasdik bilgisi yoksa ya da makam noter değilse defter başına
  gerekçe.
* İptal ve düzeltme yolları; "Geçiş kurulumu tamamlandı" işaretinden sonra hepsi kilitli (409).
* Bütün geçiş yazmaları `GECIS` etiketli; yol haritası ve sihirbaz kaydı.

Toplu sayaç beyanının tek gerekçesi ve devralınan üyeliğin koltuk kuralları `ak::` testlerindedir
(`kurallar/test_akis_kararlari.py`). Adlar ve tarihler UYDURMADIR.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from io import BytesIO

import pytest
from openpyxl import Workbook

from apps.oab.hatalar import GecisKapali, GerekceGerekli
from apps.oab.models import (
    BookCertifier,
    BookStatus,
    ComplianceItem,
    ComplianceJustification,
    ComplianceKind,
    MembershipRole,
    MembershipSource,
    MembershipStatus,
    OabTerm,
    OfficialBook,
    OrganMembership,
    Representation,
    SeatGroup,
    SeatType,
    TermStatus,
)
from apps.oab.services import (
    gecis,
    kisiler,
    kurullar,
    temsilciler,
    uyelik_gecisleri,
    uyelikler,
    uyum,
)
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import (
    Account,
    AccountRole,
    AccountStatus,
    AuditLabel,
    AuditTrail,
    ParentRoster,
    SchoolYear,
)
from apps.okul.services import hesaplar
from apps.okul.services import imports as import_service
from apps.okul.services import setup as setup_service
from apps.okul.services.templates import PARENT_TEMPLATE_HEADERS
from apps.okul.tests.hesap_ortak import GECICI_PAROLA
from conftest import TEST_HESAP_ID
from shared.exceptions import RolYetkisiz

pytestmark = pytest.mark.django_db

GEREKCE = "Uydurma gerekçe: eski defter elde değil."
TASDIK = "yonetim_kurulu.karar_defteri_noter_tasdiki"
#: Kuralın ekran metni (paketten gelir; burada elle yazıldı, değişirse test kırmızıya döner).
TASDIK_METNI = (
    "Yönetim kurulu karar defterinin noterce tasdik edilmesi zorunludur; programa defterin noter "
    "tasdiki ve tasdik günü girilmedi."
)


def _bugun() -> date:
    from django.utils import timezone

    return timezone.localdate()


def _yil(baslangic: date, *, aktif: bool = True, ad: str = "2026-2027") -> SchoolYear:
    """Günü kapsayan uydurma ders yılı (testin günü gerçek tarihe göre kurulur)."""
    kayit: SchoolYear = SchoolYear.objects.create(
        name=ad,
        start_date=baslangic - timedelta(days=40),
        end_date=baslangic + timedelta(days=280),
        is_active=aktif,
    )
    return kayit


def _ac(gun: date | None = None) -> OabTerm:
    """Geçiş dönemi: dönem başı bugünden 30 gün önce (ya da verilen gün)."""
    bas = gun or _bugun() - timedelta(days=30)
    _yil(bas)
    return gecis.ilk_donemi_ac(start_date=bas).donem


def _son_seq() -> int:
    son = AuditTrail.objects.order_by("-seq").values_list("seq", flat=True).first()
    return int(son or 0)


def _satirlar_sonra(seq: int) -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(seq__gt=seq).order_by("seq"))


# ============================================================ 1. adım: ilk birlik dönemi


def test_ilk_donem_gecisle_acilir_varsayilanlar_ve_gecis_etiketi() -> None:
    bas = _bugun() - timedelta(days=30)
    yil = _yil(bas)
    once = _son_seq()
    acilis = gecis.ilk_donemi_ac(start_date=bas)
    donem = acilis.donem
    assert (donem.status, donem.opened_by_assembly_id) == (TermStatus.ACIK, None)
    assert donem.school_year_id == yil.pk
    assert donem.name == "2026-2027 birlik dönemi"
    assert donem.program_start_date == _bugun()  # varsayılan bugün
    assert donem.transition_completed_on is None
    assert acilis.uyarilar == []  # görev süresi dolmadı
    satirlar = _satirlar_sonra(once)
    assert satirlar and {s.label for s in satirlar} == {AuditLabel.GECIS}


def test_ders_yili_donem_basini_kapsamalidir() -> None:
    bas = _bugun() - timedelta(days=30)
    with pytest.raises(ValueError, match="ders yılı tanımlı değil"):
        gecis.ilk_donemi_ac(start_date=bas)
    # Geçmiş yıl etkin olmadan açılabilir (sihirbaz açar); kapsamayan yıl seçilemez.
    gecmis = _yil(bas, aktif=False)
    baska = SchoolYear.objects.create(
        name="2030-2031", start_date=date(2030, 9, 9), end_date=date(2031, 6, 20)
    )
    with pytest.raises(ValueError, match="kapsamıyor"):
        gecis.ilk_donemi_ac(start_date=bas, school_year=baska)
    assert not OabTerm.objects.exists()
    assert gecis.ilk_donemi_ac(start_date=bas).donem.school_year_id == gecmis.pk


def test_programa_baslama_donem_basindan_once_olamaz() -> None:
    bas = _bugun() - timedelta(days=30)
    _yil(bas)
    with pytest.raises(ValueError, match="dönem başından önce"):
        gecis.ilk_donemi_ac(start_date=bas, program_start_date=bas - timedelta(days=1))
    assert not OabTerm.objects.exists()
    donem = gecis.ilk_donemi_ac(start_date=bas, program_start_date=bas).donem
    assert donem.program_start_date == bas


def test_bir_yil_gecmisse_donem_acilir_gorev_suresi_uyarisi() -> None:
    """Senaryo (plan F1c kararları): son genel kurulun üzerinden bir yıl geçmişse dönem yine açılır,
    `gorev_suresi_yil` uyarısı döner; uyarı kaydedilmez, gerekçe istemez."""
    bas = _bugun() - timedelta(days=400)
    _yil(bas, aktif=False, ad="2025-2026")
    acilis = gecis.ilk_donemi_ac(start_date=bas)
    assert acilis.donem.status == TermStatus.ACIK
    assert {u["kural"] for u in acilis.uyarilar} == {
        "yonetim_kurulu.gorev_suresi_yil",
        "denetleme_kurulu.gorev_suresi_yil",
    }
    assert not ComplianceItem.objects.exists()


def test_gecis_yalniz_program_yoneticisinin() -> None:
    bas = _bugun() - timedelta(days=30)
    _yil(bas)
    with o.rol_olarak(AccountRole.SEKRETER), pytest.raises(RolYetkisiz):
        gecis.ilk_donemi_ac(start_date=bas)
    donem = gecis.ilk_donemi_ac(start_date=bas).donem
    with o.rol_olarak(AccountRole.MUDUR):
        with pytest.raises(RolYetkisiz):
            gecis.devralinan_ekle(person=o.kisi(), organ="YK")
        with pytest.raises(RolYetkisiz):
            gecis.gecisi_tamamla(donem)


def test_uc_ilk_donemi_gecisle_acar() -> None:
    from rest_framework.test import APIClient

    bas = _bugun() - timedelta(days=30)
    yil = _yil(bas)
    govde = {"name": "uydurma dönem", "school_year": yil.pk, "start_date": bas.isoformat()}
    yanit = APIClient().post("/api/v1/oab/terms/", govde, format="json")
    assert yanit.status_code == 201, yanit.json()
    donem = OabTerm.objects.get()
    assert donem.program_start_date == _bugun()
    assert AuditTrail.objects.get(model="oab.OabTerm").label == AuditLabel.GECIS


# ============================================================ 2. adım: görevdeki kurul


def test_devralinan_gorevli_kayit_hesap_acar_ve_e63_basilir() -> None:
    """§7.9 adım 2: görev girilince hesap açılabilir; hesabı yonetici açar, E63 basılır (§4.4.5)."""
    donem = _ac()
    kisi = o.kisi(external_yk_terms=1)
    once = _son_seq()
    sekreter = gecis.devralinan_ekle(
        person=kisi,
        organ="YK",
        role=MembershipRole.SEKRETER,
        evidence_note="Görev bölümü: karar defteri 12. sıra (uydurma)",
    )
    assert (sekreter.source, sekreter.status) == (
        MembershipSource.DEVRALINAN,
        MembershipStatus.SECILDI,
    )
    assert sekreter.start_date == donem.start_date  # varsayılan dönem başı
    assert {s.label for s in _satirlar_sonra(once)} == {AuditLabel.GECIS}
    hesap = hesaplar.open_account(
        by_hesap_id=TEST_HESAP_ID,
        role=AccountRole.SEKRETER,
        tanitici=hesaplar.default_login_name(AccountRole.SEKRETER),
        display_name="Uydurma Sekreter",
        temp_password=GECICI_PAROLA,
        uyelik=sekreter.pk,
    )
    assert (hesap.membership_id, hesap.person_id, hesap.term_id) == (
        sekreter.pk,
        sekreter.person_id,
        donem.pk,
    )
    pusula = hesaplar.teslim_pusulasi(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.pk)
    assert pusula.pdf.startswith(b"%PDF")
    basim = AuditTrail.objects.get(action="BASIM", object_id=str(hesap.pk))
    assert basim.values["kod"][-1] == "E63"


def test_devralinan_temsilci_gecis_kaydidir() -> None:
    _ac()
    veli, ikinci = o.kisi(), o.kisi()
    once = _son_seq()
    temsilci = gecis.devralinan_temsilci_ekle(
        person=veli, representation=Representation.KAMPUS_YONETIMI
    )
    assert (temsilci.organ, temsilci.source) == ("TEMSILCI", MembershipSource.DEVRALINAN)
    assert {s.label for s in _satirlar_sonra(once)} == {AuditLabel.GECIS}
    # Program kaydı aynı yoldan etiketsiz yazılır.
    once = _son_seq()
    program = temsilciler.temsilci_ekle(
        term=temsilci.term, person=ikinci, representation=Representation.KAMPUS_YONETIMI
    )
    assert program.source == MembershipSource.PROGRAM
    assert AuditTrail.objects.get(seq__gt=once, model="oab.OrganMembership").label == ""


# ============================================================ 4. adım: karar defteri


def test_karar_defteri_son_no_ve_sayfa_zorunlu() -> None:
    _ac()
    with pytest.raises(ValueError, match="son sıra no"):
        gecis.karar_defteri_kaydet(last_no_before_program=None, last_page_before_program=4)
    with pytest.raises(ValueError, match="sayfası"):
        gecis.karar_defteri_kaydet(last_no_before_program=4, last_page_before_program=None)
    defter = gecis.karar_defteri_kaydet(
        last_no_before_program=37,
        last_page_before_program=12,
        certified_by=BookCertifier.NOTER,
        certified_on=date(2024, 10, 1),
        certification_no="Uydurma-123",
    )
    assert (defter.last_no_before_program, defter.last_page_before_program) == (37, 12)
    assert not ComplianceItem.objects.exists()  # noter tasdiki ve günü var: uygun, gerekçe yok
    with pytest.raises(ValueError, match="zaten kayıtlı"):
        gecis.karar_defteri_kaydet(last_no_before_program=1, last_page_before_program=1)


def test_tasdik_yoksa_defter_basina_bir_gerekce() -> None:
    donem = _ac()
    with pytest.raises(GerekceGerekli) as hata:
        gecis.karar_defteri_kaydet(last_no_before_program=5, last_page_before_program=2)
    assert f"{TASDIK_METNI.rstrip('.')} (md. 23/2)." in str(hata.value.detail)
    assert not OfficialBook.objects.exists()
    once = _son_seq()
    defter = gecis.karar_defteri_kaydet(
        last_no_before_program=5, last_page_before_program=2, gerekce=GEREKCE
    )
    satir = ComplianceItem.objects.get(rule_id=kurullar.TASDIK_KURALI)
    assert (satir.kind, satir.term_id, satir.subject_id) == (
        ComplianceKind.SAPMA,
        donem.pk,
        str(defter.pk),
    )
    # Kural satırıdır (akış satırı değil): paket ve revizyon taşır, ileti kuralın ekran metnidir.
    assert (satir.rule_package, satir.rev, satir.message) == ("OAB-2023.12", 1, TASDIK_METNI)
    assert satir.justification_group is not None
    assert satir.justification_group.root_cause == kurullar.tasdik_kok_nedeni(defter)
    assert {s.label for s in _satirlar_sonra(once)} == {AuditLabel.GECIS}
    # Yanlış kayıt iptal edilir; açık tasdik satırı kapanır, yeni defter yeni gerekçe ister.
    iptal = gecis.karar_defterini_iptal_et(defter, cancel_reason="Uydurma: sayfa yanlış.")
    assert (iptal.status, iptal.cancel_reason) == (BookStatus.IPTAL, "Uydurma: sayfa yanlış.")
    assert ComplianceItem.objects.get(pk=satir.pk).resolved_at is not None
    with pytest.raises(GerekceGerekli):
        gecis.karar_defteri_kaydet(last_no_before_program=5, last_page_before_program=3)
    yeni = gecis.karar_defteri_kaydet(
        last_no_before_program=5, last_page_before_program=3, gerekce=GEREKCE
    )
    assert ComplianceJustification.objects.filter(rule_id=kurullar.TASDIK_KURALI).count() == 2
    with pytest.raises(ValueError, match="gerekçesi"):
        gecis.karar_defterini_iptal_et(yeni, cancel_reason="  ")


# ============================================================ iptal ve düzeltme yolları


def _veli_aktar(satirlar: list[tuple[str, str]]) -> None:
    kitap = Workbook()
    sayfa = kitap.active
    assert sayfa is not None
    sayfa.append(list(PARENT_TEMPLATE_HEADERS))
    for satir in satirlar:
        sayfa.append(list(satir))
    tampon = BytesIO()
    kitap.save(tampon)
    import_service.commit_parents_file(file_bytes=tampon.getvalue(), file_name="veli.xlsx")


def test_donem_iptali_once_uyelikler_sonra_yeni_donem() -> None:
    bas = _bugun() - timedelta(days=30)
    _yil(bas)
    _veli_aktar([("UYDURMA VELİ", "9-A")])
    yanlis = gecis.ilk_donemi_ac(start_date=bas - timedelta(days=3)).donem
    assert ParentRoster.objects.get().term_id == yanlis.pk
    uye = gecis.devralinan_ekle(person=o.kisi(), organ="YK")
    with pytest.raises(ValueError, match="üyelikler iptal edilmelidir"):
        gecis.donemi_iptal_et(yanlis, cancel_reason="Uydurma: tarih yanlış.")
    with pytest.raises(ValueError, match="gerekçesi"):
        gecis.devralinan_iptal_et(uye, cancel_reason=" ")
    gecis.devralinan_iptal_et(uye, cancel_reason="Uydurma: dönemi yanlış.")
    with pytest.raises(ValueError, match="gerekçesi"):
        gecis.donemi_iptal_et(yanlis, cancel_reason="")
    once = _son_seq()
    iptal = gecis.donemi_iptal_et(yanlis, cancel_reason="Uydurma: tarih yanlış.")
    assert (iptal.status, iptal.start_date, iptal.cancel_reason) == (
        TermStatus.IPTAL,
        bas - timedelta(days=3),
        "Uydurma: tarih yanlış.",
    )
    assert {s.label for s in _satirlar_sonra(once)} == {AuditLabel.GECIS}
    assert ParentRoster.objects.get().term_id is None  # veli satırı dönemsiz kaldı
    dogru = gecis.ilk_donemi_ac(start_date=bas).donem
    assert dogru.pk != yanlis.pk and dogru.name == yanlis.name
    assert ParentRoster.objects.get().term_id == dogru.pk
    assert gecis.gecis_donemi() == dogru


def test_devralinan_iptali_hesabi_askiya_alir_yeniden_girilir() -> None:
    _ac()
    kisi = o.kisi(external_yk_terms=0)
    muhasip = gecis.devralinan_ekle(person=kisi, organ="YK", role=MembershipRole.MUHASIP)
    hesap = hesaplar.open_account(
        by_hesap_id=TEST_HESAP_ID,
        role=AccountRole.MUHASIP,
        tanitici=hesaplar.default_login_name(AccountRole.MUHASIP),
        display_name="Uydurma Muhasip",
        temp_password=GECICI_PAROLA,
        uyelik=muhasip.pk,
    )
    gecis.devralinan_iptal_et(muhasip, cancel_reason="Uydurma: koltuk yanlış.")
    assert Account.objects.get(pk=hesap.pk).status == AccountStatus.ASKIDA
    yeniden = gecis.devralinan_ekle(person=kisi, organ="YK", role=MembershipRole.MUHASIP)
    assert yeniden.status == MembershipStatus.SECILDI
    program = o.dk_ogretmeni(yeniden.term, o.ogretmen())
    with pytest.raises(ValueError, match="yalnız devralınan"):
        gecis.devralinan_iptal_et(program, cancel_reason="Uydurma.")


def test_sayac_beyani_yeni_beyanla_gerekceli_duzeltilir() -> None:
    donem = _ac()
    kisi = o.kisi()
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=2)])
    with pytest.raises(ValueError, match="düzeltmesi için gerekçe"):
        gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=3)])
    once = _son_seq()
    sonuc = gecis.sayac_beyani(
        [gecis.SayacBeyani(kisi=kisi, yk=3)], duzeltme_gerekcesi="Uydurma: defter yeniden sayıldı."
    )
    kisi.refresh_from_db()
    assert kisi.external_yk_terms == 3
    (kayit,) = sonuc.duzeltmeler
    assert (kayit.rule_id, kayit.kind, kayit.term_id) == (
        gecis.DUZELTME_AKISI,
        ComplianceKind.SAPMA,
        donem.pk,
    )
    assert kayit.resolved_at is not None  # düzeltme kaydı açık sapma listesine düşmez
    iz_satiri = AuditTrail.objects.get(seq__gt=once, model="oab.OabPerson")
    assert "external_yk_terms" in iz_satiri.changed_fields
    assert iz_satiri.compliance_item_id == kayit.pk and iz_satiri.label == AuditLabel.GECIS
    assert iz_satiri.values == {}  # kişi KVKK silme kümesinde: değer yazılmaz
    # Kişi kaydından düzeltilemez; ilk beyan (boş → sayı) kişi kaydından da girilir.
    with pytest.raises(ValueError, match="yalnız geçiş kurulumunda"):
        kisiler.update_person(kisi, external_yk_terms=1)
    assert kisiler.update_person(kisi, external_dk_chair_terms=0).external_dk_chair_terms == 0


def test_bilinmiyordan_sayiya_gecis_duzeltme_degil_satir_kapanir() -> None:
    _ac()
    kisi = o.kisi()
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=None)], gerekce=GEREKCE)
    satir = ComplianceItem.objects.get(subject_type="oab.OabPerson", subject_id=str(kisi.pk))
    assert satir.kind == ComplianceKind.SAPMA and satir.resolved_at is None
    # "Bilinmiyor" beyanı da beyandır: kişi kaydından değişmez.
    with pytest.raises(ValueError, match="yalnız geçiş kurulumunda"):
        kisiler.update_person(kisi, external_yk_terms=1)
    sonuc = gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=1)])
    assert sonuc.duzeltmeler == []
    assert ComplianceItem.objects.get(pk=satir.pk).resolved_at is not None
    # Sayıdan "bilinmiyor"a dönüş düzeltmedir.
    with pytest.raises(ValueError, match="düzeltmesi için gerekçe"):
        gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=None)])
    gecis.sayac_beyani(
        [gecis.SayacBeyani(kisi=kisi, yk=None)], duzeltme_gerekcesi="Uydurma: sayı doğrulanamadı."
    )
    acik = ComplianceItem.objects.get(
        subject_id=str(kisi.pk), rule_id="yonetim_kurulu.secilme_siniri", resolved_at__isnull=True
    )
    assert acik.justification_group is not None
    assert acik.justification_group.root_cause == gecis.sayac_kok_nedeni(acik.term)


def test_sayac_degeri_ve_kisi_tekilligi() -> None:
    _ac()
    kisi = o.kisi()
    for deger in (-1, True, "2"):
        with pytest.raises(ValueError, match="tam sayı"):
            gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=deger)])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="bir kez"):
        gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=1), gecis.SayacBeyani(kisi=kisi)])


# ============================================================ tamamlandı işareti: kilit


def test_kapanmis_gecis_yeniden_yazilamaz() -> None:
    """Plan F1c 8. adımın kararı: geçiş kayıtları ve iptal yolları işarete kadar açık, sonra kilitli."""
    donem = _ac()
    kisi = o.kisi(external_yk_terms=0)
    uye = gecis.devralinan_ekle(person=kisi, organ="YK")
    kanitli = gecis.devralinan_ekle(
        person=o.kisi(), organ="YK", evidence_note="GK 20.10.2025, karar 14 (uydurma)"
    )
    defter = gecis.karar_defteri_kaydet(
        last_no_before_program=3,
        last_page_before_program=1,
        certified_by=BookCertifier.NOTER,
        certified_on=date(2025, 10, 1),
    )
    once = _son_seq()
    tamam = gecis.gecisi_tamamla()
    assert tamam.transition_completed_on == _bugun()
    (satir,) = _satirlar_sonra(once)
    assert (satir.action, satir.label, satir.values["transition_completed_on"][1]) == (
        "GUNCELLE",
        AuditLabel.GECIS,
        _bugun().isoformat(),
    )
    yazimlar: list[Callable[[], object]] = [
        lambda: gecis.devralinan_ekle(person=o.kisi(), organ="YK"),
        lambda: gecis.devralinan_temsilci_ekle(
            person=o.kisi(), representation=Representation.DIGER
        ),
        lambda: temsilciler.temsilci_ekle(
            term=donem,
            person=o.kisi(),
            representation=Representation.DIGER,
            source=MembershipSource.DEVRALINAN,
            start_date=donem.start_date,
        ),
        lambda: uyelikler.update_membership(kanitli, evidence_note="Başka kanıt (uydurma)"),
        lambda: uyelikler.assign_membership(
            term=donem,
            person=o.kisi(),
            organ="YK",
            seat_type="ASIL",
            elected_by="GENEL_KURUL",
            source=MembershipSource.DEVRALINAN,
        ),
        lambda: gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=1)], duzeltme_gerekcesi="x"),
        lambda: gecis.karar_defteri_kaydet(last_no_before_program=1, last_page_before_program=1),
        lambda: gecis.karar_defterini_iptal_et(defter, cancel_reason="Uydurma."),
        lambda: gecis.devralinan_iptal_et(uye, cancel_reason="Uydurma."),
        lambda: uyelik_gecisleri.uyeligi_iptal_et(uye, cancel_reason="Uydurma."),
        lambda: gecis.donemi_iptal_et(donem, cancel_reason="Uydurma."),
        lambda: gecis.gecisi_tamamla(donem),
    ]
    for yazim in yazimlar:
        with pytest.raises(GecisKapali):
            yazim()
    # Argüman olarak açılan kişi kayıtları yazıldı; hiçbir geçiş kaydı yazılmadı.
    assert not AuditTrail.objects.filter(seq__gt=once + 1, label=AuditLabel.GECIS).exists()
    assert OrganMembership.objects.get(pk=uye.pk).status == MembershipStatus.SECILDI
    assert OrganMembership.objects.get(pk=kanitli.pk).evidence_note.startswith("GK 20.10.2025")
    assert OfficialBook.objects.get(pk=defter.pk).status == BookStatus.KULLANIMDA
    assert OabTerm.objects.get(pk=donem.pk).status == TermStatus.ACIK
    with pytest.raises(ValueError, match="yalnız geçiş kurulumunda"):
        kisiler.update_person(kisi, external_yk_terms=2)
    # Programın olağan akışı sürer: genel kurul dışı kanaldan seçilen DK öğretmeni yazılır.
    assert o.dk_ogretmeni(donem, o.ogretmen()).source == MembershipSource.PROGRAM


def test_gecis_donemi_yoksa_adimlar_yazilmaz() -> None:
    with pytest.raises(ValueError, match="açılmadı"):
        gecis.devralinan_ekle(person=o.kisi(), organ="YK")
    with pytest.raises(ValueError, match="açılmadı"):
        gecis.gecisi_tamamla()


# ============================================================ sihirbaz kaydı ve yol haritası


def test_sihirbazin_atlanabilir_adimi_kurulumu_engellemez() -> None:
    assert setup_service.STEP_BIRLIK_DONEMI == "birlik_donemi"
    assert setup_service.STEP_BIRLIK_DONEMI not in setup_service.SETUP_STEPS
    assert setup_service.WIZARD_STEPS == (
        *setup_service.SETUP_STEPS,
        setup_service.STEP_BIRLIK_DONEMI,
    )
    assert setup_service.STEP_BIRLIK_DONEMI not in setup_service.missing_setup_steps()


def test_yol_haritasi_gecisin_acik_adimlarini_gosterir() -> None:
    durum = setup_service.setup_status
    assert durum()["transition_setup"] == {"state": "BASLAMADI", "open_steps": ["donem"]}
    assert setup_service.roadmap_auto_items(durum())["gecis_kurulumu"] is False
    _ac()
    assert durum()["transition_setup"] == {
        "state": "SURUYOR",
        "open_steps": ["kurul", "karar_defteri", "tamamla"],
    }
    bilinmeyen = o.kisi()
    gecis.devralinan_ekle(person=bilinmeyen, organ="YK", role=MembershipRole.BASKAN)
    baskan = o.ogretmen()
    gecis.devralinan_ekle(
        person=baskan,
        organ="DK",
        seat_group=SeatGroup.OGRETMEN,
        elected_by="OGRETMENLER_KURULU",
        role=MembershipRole.BASKAN,
    )
    assert durum()["transition_setup"]["open_steps"] == ["sayac_beyani", "karar_defteri", "tamamla"]
    gecis.sayac_beyani(
        [
            gecis.SayacBeyani(kisi=bilinmeyen, yk=None),
            gecis.SayacBeyani(kisi=baskan, dk_baskanlik=1),
        ],
        gerekce=GEREKCE,
    )
    assert durum()["transition_setup"]["open_steps"] == ["karar_defteri", "tamamla"]
    gecis.gecisi_tamamla()
    assert durum()["transition_setup"] == {"state": "TAMAMLANDI", "open_steps": []}
    assert setup_service.roadmap_auto_items(durum())["gecis_kurulumu"] is True


# ============================================================ denetim bulguları (10.11.2026)


def test_devralinan_gecis_alani_degismez_bos_alan_tamamlanir() -> None:
    """Tasarım §7.9 giriş ve "Senaryolar": geçişte girilen alanın dolu değeri değişmez (düzeltme iptal +
    yeni kayıt; işaretten önce 400, sonra 409); boş alanın doldurulması eksiğin tamamlanmasıdır, geçiş
    açıkken `GECIS` etiketlidir; görevdeki üyenin sonraki beyanları geçiş kaydı değildir."""
    from rest_framework.test import APIClient

    donem = _ac()
    yedek = gecis.devralinan_ekle(
        person=o.kisi(),
        organ="YK",
        seat_type=SeatType.YEDEK,
        seat_order=2,
        votes=40,
        evidence_note="GK 20.10.2025, karar 14 (uydurma)",
    )
    sirasiz = gecis.devralinan_ekle(person=o.kisi(), organ="YK", seat_type=SeatType.YEDEK)
    mem = gecis.devralinan_ekle(
        person=o.ogretmen(),
        organ="DK",
        seat_group=SeatGroup.OGRETMEN,
        elected_by="MEM_GOREVLENDIRME",
    )
    once = _son_seq()
    for alanlar in (
        {"seat_order": 1},
        {"seat_order": None},
        {"votes": 41},
        {"evidence_note": "Başka kanıt (uydurma)"},
    ):
        with pytest.raises(ValueError, match="iptal edilip yeniden"):
            uyelikler.update_membership(yedek, **alanlar)
    assert _son_seq() == once
    tamam = uyelikler.update_membership(sirasiz, seat_order=3, votes=12)
    assert (tamam.seat_order, tamam.votes) == (3, 12)
    assert [s.label for s in _satirlar_sonra(once)] == [AuditLabel.GECIS]
    once = _son_seq()
    uyelikler.update_membership(yedek, eligibility_declared_on=_bugun())
    assert {s.label for s in _satirlar_sonra(once)} == {""}
    gecis.gecisi_tamamla(donem)
    with pytest.raises(GecisKapali):
        uyelikler.update_membership(yedek, seat_order=1)
    yanit = APIClient().patch(
        f"/api/v1/oab/memberships/{yedek.pk}/", {"evidence_note": "Başka (uydurma)"}, format="json"
    )
    assert yanit.status_code == 409, yanit.content
    guncel = OrganMembership.objects.get(pk=yedek.pk)
    assert (guncel.seat_order, guncel.votes) == (2, 40)
    assert guncel.evidence_note == "GK 20.10.2025, karar 14 (uydurma)"
    # İşaretten sonra da eksik tamamlanır (etiketsiz), dolu değer yine değişmez.
    once = _son_seq()
    tamamlanan = uyelikler.update_membership(mem, mem_approval_no="Uydurma-7")
    assert tamamlanan.mem_approval_no == "Uydurma-7"
    assert AuditTrail.objects.get(seq__gt=once, model="oab.OrganMembership").label == ""
    with pytest.raises(GecisKapali):
        uyelikler.update_membership(mem, mem_approval_no="Uydurma-8")
    beyanli = uyelikler.update_membership(yedek, single_birlik_declared_on=_bugun())
    assert beyanli.single_birlik_declared_on == _bugun()


def test_devralinan_iptali_genel_uctan_da_yalniz_yoneticinin() -> None:
    """Tasarım §7.9 adım 2 "Kim: yonetici": geçiş kaydını hangi uçtan gelirse gelsin yalnız program
    yöneticisi iptal eder; programda açılmış kaydın iptali M2'nin yazanlarına açık kalır."""
    from rest_framework.test import APIClient

    donem = _ac()
    kisi = o.kisi(external_yk_terms=0)
    baskan = gecis.devralinan_ekle(person=kisi, organ="YK", role=MembershipRole.BASKAN)
    hesap = hesaplar.open_account(
        by_hesap_id=TEST_HESAP_ID,
        role=AccountRole.BASKAN,
        tanitici=hesaplar.default_login_name(AccountRole.BASKAN),
        display_name="Uydurma Başkan",
        temp_password=GECICI_PAROLA,
        uyelik=baskan.pk,
    )
    program = o.dk_ogretmeni(donem, o.ogretmen())
    once = _son_seq()
    for rol in (AccountRole.SEKRETER, AccountRole.MUHASIP):
        with o.rol_olarak(rol):
            yanit = APIClient().post(
                f"/api/v1/oab/memberships/{baskan.pk}/cancel/",
                {"cancel_reason": "Uydurma."},
                format="json",
            )
            assert yanit.status_code == 403, yanit.content
            with pytest.raises(RolYetkisiz):
                uyelik_gecisleri.uyeligi_iptal_et(baskan, cancel_reason="Uydurma.")
    assert OrganMembership.objects.get(pk=baskan.pk).status == MembershipStatus.SECILDI
    assert Account.objects.get(pk=hesap.pk).status != AccountStatus.ASKIDA
    assert not AuditTrail.objects.filter(seq__gt=once, label=AuditLabel.GECIS).exists()
    with o.rol_olarak(AccountRole.SEKRETER):
        yanit = APIClient().post(
            f"/api/v1/oab/memberships/{program.pk}/cancel/",
            {"cancel_reason": "Uydurma."},
            format="json",
        )
    assert yanit.status_code == 200 and yanit.json()["status"] == "IPTAL"


def test_karar_defteri_makami_noter_degilse_defter_basina_gerekce() -> None:
    """Md. 23/2 (karar defteri noterce, öteki defterler il/ilçe millî eğitim müdürlüğünce tasdik
    edilir); tasarım `OfficialBook`: "yanlış makamla kullanım — uyarı (defter başına bir toplu
    gerekçe, O3)". F3'ün "deftere işlendi" işareti aynı defteri aynı kuralla yeniden denetler:
    açık satır ve gerekçe yerinde kalır, gerekçe yeniden sorulmaz."""
    donem = _ac()

    def kaydet(gerekce: str = "") -> OfficialBook:
        return gecis.karar_defteri_kaydet(
            last_no_before_program=12,
            last_page_before_program=8,
            certified_by=BookCertifier.IL_ILCE_MEM,
            certified_on=date(2024, 9, 2),
            gerekce=gerekce,
        )

    with pytest.raises(GerekceGerekli):
        kaydet()
    assert not OfficialBook.objects.exists()
    defter = kaydet(GEREKCE)
    satir = ComplianceItem.objects.get(rule_id=kurullar.TASDIK_KURALI)
    assert (satir.kind, satir.term_id, satir.subject_id, satir.message) == (
        ComplianceKind.SAPMA,
        donem.pk,
        str(defter.pk),
        TASDIK_METNI,
    )
    assert satir.justification_group is not None
    assert satir.justification_group.root_cause == kurullar.tasdik_kok_nedeni(defter)
    tekrar = kurullar.tasdik_denetimi(defter, donem=donem)  # gerekçesiz: yeniden sorulmaz
    assert tekrar.satir is not None and tekrar.satir.pk == satir.pk
    assert ComplianceJustification.objects.filter(rule_id=TASDIK).count() == 1
    gecis.karar_defterini_iptal_et(defter, cancel_reason="Uydurma: makam yanlış.")
    assert ComplianceItem.objects.get(pk=satir.pk).resolved_at is not None


def test_tasdik_gunu_yoksa_makam_dolu_olsa_da_gerekce() -> None:
    _ac()

    def kaydet(gerekce: str = "") -> OfficialBook:
        return gecis.karar_defteri_kaydet(
            last_no_before_program=4,
            last_page_before_program=2,
            certified_by=BookCertifier.NOTER,
            certified_on=None,
            gerekce=gerekce,
        )

    with pytest.raises(GerekceGerekli):
        kaydet()
    kaydet(GEREKCE)
    assert ComplianceItem.objects.get(rule_id=kurullar.TASDIK_KURALI).message == TASDIK_METNI


def test_donem_iptali_tasdik_satiri_varken_once_defter_iptal_edilir() -> None:
    """Defter dönemsiz, tasdik satırı dönemli: satır iptal edilen dönemde kalmasın diye dönem iptalinden
    önce defter kaydı iptal edilir (satır kapanır); yeni dönemde defter yeniden girilir, satırı yeni
    döneme bağlanır. Tasdik bilgisi tam defter dönem iptaline engel değildir."""
    bas = _bugun() - timedelta(days=30)
    _yil(bas)
    yanlis = gecis.ilk_donemi_ac(start_date=bas - timedelta(days=3)).donem
    defter = gecis.karar_defteri_kaydet(
        last_no_before_program=5, last_page_before_program=2, gerekce=GEREKCE
    )
    satir = ComplianceItem.objects.get(rule_id=kurullar.TASDIK_KURALI)
    with pytest.raises(ValueError, match="karar defteri kaydı iptal edilmelidir"):
        gecis.donemi_iptal_et(yanlis, cancel_reason="Uydurma: tarih yanlış.")
    assert OabTerm.objects.get(pk=yanlis.pk).status == TermStatus.ACIK
    gecis.karar_defterini_iptal_et(defter, cancel_reason="Uydurma: dönemi yanlış.")
    assert ComplianceItem.objects.get(pk=satir.pk).resolved_at is not None
    gecis.donemi_iptal_et(yanlis, cancel_reason="Uydurma: tarih yanlış.")
    dogru = gecis.ilk_donemi_ac(start_date=bas).donem
    yeni = gecis.karar_defteri_kaydet(
        last_no_before_program=5, last_page_before_program=2, gerekce=GEREKCE
    )
    acik = ComplianceItem.objects.filter(rule_id=kurullar.TASDIK_KURALI, resolved_at__isnull=True)
    assert [(s.term_id, s.subject_id) for s in acik] == [(dogru.pk, str(yeni.pk))]
    gecis.karar_defterini_iptal_et(yeni, cancel_reason="Uydurma.")
    gecis.karar_defteri_kaydet(
        last_no_before_program=5,
        last_page_before_program=2,
        certified_by=BookCertifier.NOTER,
        certified_on=date(2024, 9, 2),
    )
    assert gecis.donemi_iptal_et(dogru, cancel_reason="Uydurma.").status == TermStatus.IPTAL


def test_iptal_edilen_donemin_kayitlari_secilme_sayacina_girmez() -> None:
    """Dönem iptal edilince düşmüş program kayıtları (iptal edilemezler) sayaçtan dönemle düşer."""
    yanlis = o.donem()
    kisi = o.ogretmen(is_parent=True)
    OrganMembership.objects.create(
        term=yanlis,
        person=kisi,
        seat_type=SeatType.ASIL,
        organ="YK",
        elected_by="GENEL_KURUL",
        status=MembershipStatus.SECILDI,
        start_date=o.SECIM_GUNU,
    )
    OrganMembership.objects.create(
        term=yanlis,
        person=kisi,
        seat_type=SeatType.ASIL,
        organ="DK",
        seat_group=SeatGroup.OGRETMEN,
        elected_by="OGRETMENLER_KURULU",
        status=MembershipStatus.SECILDI,
        chair_elections=1,
        start_date=o.SECIM_GUNU,
    )
    # Kayıt seçilmiş açılır (model kuralı); ikisi de düşmüştür.
    OrganMembership.objects.filter(person=kisi).update(
        status=MembershipStatus.DUSTU, drop_kind="ISTIFA", end_date=date(2026, 11, 2)
    )
    assert (uyelikler.yk_secilme_sayisi(kisi), uyelikler.dk_baskanlik_sayisi(kisi)) == (1, 1)
    gecis.donemi_iptal_et(yanlis, cancel_reason="Uydurma: dönem yanlış.")
    gecis.ilk_donemi_ac(start_date=o.GUN)
    assert (uyelikler.yk_secilme_sayisi(kisi), uyelikler.dk_baskanlik_sayisi(kisi)) == (0, 0)


@pytest.mark.parametrize("beyan", [0, None])
def test_sayac_beyani_dusmus_uyeligin_acik_satirini_da_isler(beyan: int | None) -> None:
    """§5 O3: seçimde açılan sayaç eksiği, üye sonradan düşse de beyanla kapanır ("bilinmiyor"da toplu
    gerekçeye bağlanır); seçilme düşmeyle silinmez."""
    donem = o.donem()
    kisi = o.kisi()
    kurul = o.olaganustu_genel_kurul(donem)
    uye = uyelikler.elect_membership(o.yk_adayi(donem, kisi, kurul), start_date=o.SECIM_GUNU)

    def satir() -> ComplianceItem:
        kayit: ComplianceItem = ComplianceItem.objects.get(
            subject_type="oab.OrganMembership",
            subject_id=str(uye.pk),
            rule_id="yonetim_kurulu.secilme_siniri",
        )
        return kayit

    assert (satir().kind, satir().resolved_at) == (ComplianceKind.EKSIK, None)
    uyelik_gecisleri.uyeligi_dusur(uye, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=beyan)], gerekce=GEREKCE)
    if beyan is None:
        assert (satir().kind, satir().resolved_at) == (ComplianceKind.SAPMA, None)
        grup = satir().justification_group
        assert grup is not None and grup.root_cause == gecis.sayac_kok_nedeni(donem)
    else:
        assert satir().resolved_at is not None


def test_sayac_beyani_siniri_asarsa_uyelikte_kisiye_ozgu_gerekce() -> None:
    """Beyanla sınırın aşılması uyarı + gerekçedir (md. 12/4); gerekçe kişiye özgüdür (kök nedensiz)."""
    donem = o.donem()
    kisi = o.kisi()
    kurul = o.olaganustu_genel_kurul(donem)
    uye = uyelikler.elect_membership(o.yk_adayi(donem, kisi, kurul), start_date=o.SECIM_GUNU)
    with pytest.raises(GerekceGerekli):
        gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=10)])
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=10)], gerekce=GEREKCE)
    satir = ComplianceItem.objects.get(
        subject_type="oab.OrganMembership",
        subject_id=str(uye.pk),
        rule_id="yonetim_kurulu.secilme_siniri",
    )
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.SAPMA, None)
    assert satir.justification_group is not None
    assert not satir.justification_group.root_cause


def test_iptal_edilen_donemin_bilinmiyor_satiri_ilk_beyani_engellemez() -> None:
    bas = _bugun() - timedelta(days=30)
    _yil(bas)
    yanlis = gecis.ilk_donemi_ac(start_date=bas - timedelta(days=3)).donem
    kisi = o.kisi()
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=None)], gerekce=GEREKCE)
    gecis.donemi_iptal_et(yanlis, cancel_reason="Uydurma: tarih yanlış.")
    gecis.ilk_donemi_ac(start_date=bas)
    assert kisiler.update_person(kisi, external_yk_terms=1).external_yk_terms == 1


@pytest.mark.parametrize("kenar", ["ilk", "son"])
def test_ders_yili_ilk_ve_son_gunu_donem_basini_kapsar(kenar: str) -> None:
    yil = SchoolYear.objects.create(
        name="2025-2026",
        start_date=_bugun() - timedelta(days=300),
        end_date=_bugun() - timedelta(days=10),
    )
    gun = yil.start_date if kenar == "ilk" else yil.end_date
    assert gecis.ilk_donemi_ac(start_date=gun).donem.school_year_id == yil.pk


def test_baskan_olmayan_devralinan_dk_uyesi_sayac_adimi_acmaz() -> None:
    """Denetleme Kurulunda yalnız başkanlık sayılır (md. 14/3): başkan olmayan devralınan üye için
    sayaç beyanı adımı açılmaz."""
    _ac()
    gecis.devralinan_ekle(
        person=o.ogretmen(),
        organ="DK",
        seat_group=SeatGroup.OGRETMEN,
        elected_by="OGRETMENLER_KURULU",
    )
    assert setup_service.setup_status()["transition_setup"]["open_steps"] == [
        "karar_defteri",
        "tamamla",
    ]


# ============================================================ 3. adım: devralınan üyenin beyanı sınırla
# Devralınan kayıt sayıma girmez (beyan görevdeki seçimi içerir; tasarım §15 B-12), ama beyanın kendisi
# sınırla karşılaştırılır (kullanıcı kararı 12.11.2026): md. 12/4 yönetim kurulunda "en fazla dört
# defa", md. 14/3 Denetleme Kurulu başkanlığında "üç defa"; sınırın üstü uyarı + gerekçedir.

YK_SAYAC = "yonetim_kurulu.secilme_siniri"
DK_SAYAC = "denetleme_kurulu.baskan_secilme_siniri"


def _uyelik_satirlari(uyelik: OrganMembership, kural_id: str) -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(
            subject_type="oab.OrganMembership", subject_id=str(uyelik.pk), rule_id=kural_id
        ).order_by("pk")
    )


def _ozet(uyelik: OrganMembership, kural_id: str) -> list[dict[str, object]]:
    guncel = OrganMembership.objects.get(pk=uyelik.pk)
    return [u for u in (guncel.rule_warnings or []) if u["kural"] == kural_id]


@pytest.mark.kural_davranis(YK_SAYAC)
def test_devralinan_yk_baskani_dort_beyaninda_uyarisiz() -> None:
    """Sınırın içi: dört seçilme beyanı (görevdeki seçim dâhil) uyarısızdır, satır açılmaz."""
    _ac()
    kisi = o.kisi()
    uye = gecis.devralinan_ekle(person=kisi, organ="YK", role=MembershipRole.BASKAN)
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=4)])
    assert _uyelik_satirlari(uye, YK_SAYAC) == []
    assert _ozet(uye, YK_SAYAC) == []
    kisi.refresh_from_db()
    assert uyelikler.secilme_sayaci(kisi, "YK") == 4  # devralınan kayıt ayrıca sayılmaz


@pytest.mark.kural_davranis(YK_SAYAC)
@pytest.mark.parametrize(
    ("seat_type", "role"),
    [(SeatType.ASIL, MembershipRole.BASKAN), (SeatType.YEDEK, MembershipRole.UYE)],
)
def test_devralinan_yk_uyesi_bes_beyani_uyari_gerekce_ve_duzeltmeyle_kapanir(
    seat_type: str, role: str
) -> None:
    """Beşinci seçilme beyanı (md. 12/4): gerekçesiz geri alınır (beyan yazılmaz), toplu gerekçeyle
    üyelikte kişiye özgü gerekçeli `SAPMA`; dörde düzeltilince açık satır kapanır. Yedek de sayılır."""
    _ac()
    kisi = o.kisi()
    uye = gecis.devralinan_ekle(person=kisi, organ="YK", seat_type=seat_type, role=role)
    with pytest.raises(GerekceGerekli) as hata:
        gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=5)])
    assert "md. 12/4" in str(hata.value.detail)
    kisi.refresh_from_db()
    assert kisi.external_yk_terms is None  # işlem bütünüyle geri alındı
    assert not ComplianceItem.objects.exists()
    once = _son_seq()
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=5)], gerekce=GEREKCE)
    (satir,) = _uyelik_satirlari(uye, YK_SAYAC)
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.SAPMA, None)
    assert satir.justification_group is not None
    assert not satir.justification_group.root_cause  # kişiye özgü
    assert (satir.rule_package, satir.rev) == ("OAB-2023.12", 1)
    (ozet,) = _ozet(uye, YK_SAYAC)
    assert (ozet["durum"], ozet["atif"]) == ("uyari", "md. 12/4")
    assert "5 defa" in str(ozet["mesaj"])
    iz_satiri = AuditTrail.objects.get(
        seq__gt=once, model="oab.OrganMembership", object_id=str(uye.pk)
    )
    assert "rule_warnings" in iz_satiri.changed_fields and iz_satiri.label == AuditLabel.GECIS
    # Aynı beyanın yinelenmesi yeniden sorulmaz.
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=5)])
    assert len(_uyelik_satirlari(uye, YK_SAYAC)) == 1
    # Dörde düzeltme (düzeltme gerekçesiyle): uyarı kalkar.
    gecis.sayac_beyani(
        [gecis.SayacBeyani(kisi=kisi, yk=4)], duzeltme_gerekcesi="Uydurma: defter yeniden sayıldı."
    )
    assert ComplianceItem.objects.get(pk=satir.pk).resolved_at is not None
    assert _ozet(uye, YK_SAYAC) == []


@pytest.mark.kural_davranis(DK_SAYAC)
def test_devralinan_dk_baskaninin_dorduncu_baskanligi_uyari_baskan_olmayanda_satir_yok() -> None:
    """md. 14/3: Denetleme Kurulunda yalnız başkanlık sayılır; görevdeki devralınan başkanın dördüncü
    başkanlık beyanı uyarı + gerekçedir, başkan olmayan devralınan üyede aynı beyan satır açmaz."""
    _ac()
    baskan = o.ogretmen()
    uye = gecis.devralinan_ekle(
        person=baskan,
        organ="DK",
        seat_group=SeatGroup.OGRETMEN,
        elected_by="OGRETMENLER_KURULU",
        role=MembershipRole.BASKAN,
    )
    oteki = o.kisi()
    diger = gecis.devralinan_ekle(person=oteki, organ="DK", seat_group=SeatGroup.VELI)
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=oteki, dk_baskanlik=4)])
    assert _uyelik_satirlari(diger, DK_SAYAC) == []
    with pytest.raises(GerekceGerekli):
        gecis.sayac_beyani([gecis.SayacBeyani(kisi=baskan, dk_baskanlik=4)])
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=baskan, dk_baskanlik=4)], gerekce=GEREKCE)
    (satir,) = _uyelik_satirlari(uye, DK_SAYAC)
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.SAPMA, None)
    (ozet,) = _ozet(uye, DK_SAYAC)
    assert (ozet["durum"], ozet["atif"]) == ("uyari", "md. 14/3")
    assert _ozet(diger, DK_SAYAC) == []


@pytest.mark.kural_davranis(DK_SAYAC)
def test_devralinan_dk_baskaninin_ucuncu_baskanligi_uyarisiz() -> None:
    _ac()
    baskan = o.ogretmen()
    uye = gecis.devralinan_ekle(
        person=baskan,
        organ="DK",
        seat_group=SeatGroup.OGRETMEN,
        elected_by="OGRETMENLER_KURULU",
        role=MembershipRole.BASKAN,
    )
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=baskan, dk_baskanlik=3)])
    assert _uyelik_satirlari(uye, DK_SAYAC) == []


@pytest.mark.kural_davranis(YK_SAYAC)
def test_devralinan_bilinmiyor_beyani_uyelikte_yeni_satir_acmaz() -> None:
    """Kişinin "bilinmiyor" beyanı toplu gerekçeli `SAPMA` satırıdır; devralınan üyelikte ikinci satır
    açılmaz. Sayıyla açılmış uyarı "bilinmiyor"a düzeltilince kapanır (sınır artık denetlenemiyor)."""
    _ac()
    kisi = o.kisi()
    uye = gecis.devralinan_ekle(person=kisi, organ="YK", role=MembershipRole.BASKAN)
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=None)], gerekce=GEREKCE)
    assert _uyelik_satirlari(uye, YK_SAYAC) == []
    assert _ozet(uye, YK_SAYAC) == []
    (kisinin,) = ComplianceItem.objects.filter(subject_type="oab.OabPerson", rule_id=YK_SAYAC)
    assert (kisinin.kind, kisinin.resolved_at) == (ComplianceKind.SAPMA, None)
    # Sayı (5) girilir: üyelikte uyarı; sonra "bilinmiyor"a düzeltme: üyeliğin satırı kapanır.
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=5)], gerekce=GEREKCE)
    (satir,) = _uyelik_satirlari(uye, YK_SAYAC)
    assert satir.resolved_at is None
    gecis.sayac_beyani(
        [gecis.SayacBeyani(kisi=kisi, yk=None)],
        gerekce=GEREKCE,
        duzeltme_gerekcesi="Uydurma: sayı doğrulanamadı.",
    )
    assert ComplianceItem.objects.get(pk=satir.pk).resolved_at is not None
    assert len(_uyelik_satirlari(uye, YK_SAYAC)) == 1  # yeni satır açılmadı
    assert _ozet(uye, YK_SAYAC) == []
    assert ComplianceItem.objects.filter(
        subject_type="oab.OabPerson", rule_id=YK_SAYAC, resolved_at__isnull=True
    ).exists()


def _acik_uyelik_satirlari(kural_id: str) -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(
            subject_type="oab.OrganMembership", rule_id=kural_id, resolved_at__isnull=True
        ).order_by("pk")
    )


@pytest.mark.kural_davranis(YK_SAYAC)
def test_iptal_edilip_yeniden_girilen_devralinan_uyede_beyan_uyarisi_korunur() -> None:
    """Devralınan alanın düzeltme yolu iptal + yeniden giriştir (`GECIS_ALANI_DEGISMEZ`): beyan
    verilmişse yeni üyeliğin ilk girişinde de beyan sınırla karşılaştırılır (gerekçesiz geri alınır,
    gerekçeyle `SAPMA`); iptal edilen üyeliğin açık sayaç satırı kapanır (tek açık satır kalır)."""
    _ac()
    kisi = o.kisi()
    eski = gecis.devralinan_ekle(person=kisi, organ="YK", role=MembershipRole.BASKAN)
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=5)], gerekce=GEREKCE)
    (eski_satir,) = _uyelik_satirlari(eski, YK_SAYAC)
    gecis.devralinan_iptal_et(eski, cancel_reason="Uydurma: başlangıç günü yanlış.")
    assert ComplianceItem.objects.get(pk=eski_satir.pk).resolved_at is not None
    assert _acik_uyelik_satirlari(YK_SAYAC) == []
    with pytest.raises(GerekceGerekli) as hata:
        gecis.devralinan_ekle(person=kisi, organ="YK", role=MembershipRole.BASKAN)
    assert "md. 12/4" in str(hata.value.detail)
    assert not OrganMembership.objects.filter(
        person=kisi, status=MembershipStatus.SECILDI
    ).exists()  # işlem geri alındı
    yeni = gecis.devralinan_ekle(
        person=kisi, organ="YK", role=MembershipRole.BASKAN, gerekce=uyum.Gerekce(metin=GEREKCE)
    )
    (satir,) = _acik_uyelik_satirlari(YK_SAYAC)
    assert (satir.subject_id, satir.kind) == (str(yeni.pk), ComplianceKind.SAPMA)
    (ozet,) = _ozet(yeni, YK_SAYAC)
    assert (ozet["durum"], ozet["atif"]) == ("uyari", "md. 12/4")
    kisi.refresh_from_db()
    assert uyelikler.secilme_sayaci(kisi, "YK") == 5  # devralınan kayıt yine sayılmaz


@pytest.mark.kural_davranis(DK_SAYAC)
def test_beyani_verilmis_devralinan_dk_baskaninin_ilk_girisi_sinirla_karsilastirilir() -> None:
    _ac()
    baskan = o.ogretmen()
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=baskan, dk_baskanlik=4)])  # henüz üyeliği yok

    def _ekle(gerekce: uyum.Gerekce | None = None) -> OrganMembership:
        return gecis.devralinan_ekle(
            person=baskan,
            organ="DK",
            seat_group=SeatGroup.OGRETMEN,
            elected_by="OGRETMENLER_KURULU",
            role=MembershipRole.BASKAN,
            gerekce=gerekce,
        )

    with pytest.raises(GerekceGerekli) as hata:
        _ekle()
    assert "md. 14/3" in str(hata.value.detail)
    uye = _ekle(uyum.Gerekce(metin=GEREKCE))
    (satir,) = _uyelik_satirlari(uye, DK_SAYAC)
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.SAPMA, None)


@pytest.mark.kural_davranis(YK_SAYAC)
def test_dusmus_devralinan_uyede_beyan_duzeltilince_sinir_uyarisi_kapanir() -> None:
    """Düşmüş devralınan kaydın açık sayaç satırı beyan yolunda yeniden denetlenir (program kaydının
    `_dusmus_sayaci` karşılığı): dörde düzeltilince kapanır, özetten düşer. Düşmüş kayıtta yeni satır
    açılmaz."""
    _ac()
    kisi = o.kisi()
    uye = gecis.devralinan_ekle(person=kisi, organ="YK")
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=kisi, yk=5)], gerekce=GEREKCE)
    (satir,) = _uyelik_satirlari(uye, YK_SAYAC)
    uyelik_gecisleri.uyeligi_dusur(uye, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    gecis.sayac_beyani(
        [gecis.SayacBeyani(kisi=kisi, yk=4)], duzeltme_gerekcesi="Uydurma: defter yeniden sayıldı."
    )
    assert ComplianceItem.objects.get(pk=satir.pk).resolved_at is not None
    assert _ozet(uye, YK_SAYAC) == []
    # Beyandan önce düşmüş devralınan üyede sınır üstü beyan satır açmaz (gerekçe de istemez).
    oteki = o.kisi()
    dusmus = gecis.devralinan_ekle(person=oteki, organ="YK")
    uyelik_gecisleri.uyeligi_dusur(dusmus, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    gecis.sayac_beyani([gecis.SayacBeyani(kisi=oteki, yk=5)])
    assert _uyelik_satirlari(dusmus, YK_SAYAC) == []
