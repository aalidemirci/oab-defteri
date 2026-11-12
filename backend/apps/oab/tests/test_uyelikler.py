"""Organ çekirdeği (F1c'nin 5. adımı; tasarım §5.2.2, §5.2.4, §5.2.8, §4.6.4).

Kural testleri `kurallar/`'dadır (`yk`, `dk`, `ak`). Burada kuralsız davranış sınanır:

* **Durum makinesi:** kayıt aday ya da seçilmiş açılır; `DUSTU` ve `IPTAL` geri dönmez, aday
  düşürülmez (kaynak modülün kusuru, §12.A); düşmede `drop_kind` zorunlu (veritabanı kısıtı).
* **Yapı:** pasif kişi organa eklenemez; seçim kanalı, koltuk grubu, genel kurul bağı; dönem kilidi.
* **Tek kaynak seçicileri:** sıra Python'da, çözülmüş adla; görevdeki asıl yedekten çağrılanı içerir.
* **Uçlar:** kadro serileştiricisinde dayanak, düşme gerekçesi ve uyarı özeti yoktur; dayanak ayrı
  uçtan okunur, okuması erişim günlüğüne yazılır, okuru üyeliği yazan rollerdir.
* **Denetim izi:** üyelik satırı kişisiz değer taşır; şifreli alan yalnız adıyla görünür.
* **Kurul kayıtları:** toplantı no'su sırası, katılım tekil ve yalnız görevdeki asıla, karar taslağı
  varsayılanı ve türü; yedek çağırma kararı yalnız yönetim kurulu toplantısına.

Kişi adları UYDURMADIR.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from apps.oab import selectors
from apps.oab.hatalar import DonemKapali
from apps.oab.models import (
    AssemblyKind,
    BoardDecision,
    BoardMeetingAttendance,
    DecisionKind,
    DecisionStatus,
    EligibilityBar,
    MeetingKind,
    MeetingStatus,
    MembershipStatus,
    OabTerm,
    OrganMembership,
    PersonStatus,
    SeatType,
    TermStatus,
    UyelikDurumuGecersiz,
)
from apps.oab.services import genel_kurul as genel_kurul_servisi
from apps.oab.services import kisiler, kurullar, uyelik_gecisleri, uyelikler, uyum
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import AccessKind, AccessLog, AccountRole, AuditTrail
from apps.okul.tests.hesap_ortak import rol_hesabi
from conftest import oturumu_ac_test
from shared import crypto

pytestmark = pytest.mark.django_db

UC = "/api/v1/oab/memberships/"


def _rol_oturumu(rol: AccountRole) -> None:
    hesap = rol_hesabi(rol)
    oturumu_ac_test(str(hesap.id), tanitici=hesap.login_name, rol=rol.value)


# ============================================================ durum makinesi


def test_alanlar_tasarimin_lafzidir() -> None:
    """Tasarım §5.2.2, §5.3: üç şifreli alan ve iptal gerekçesi (6. adım: tasarım "IPTAL, gerekçe ve
    kim" der, alan adı vermez; `ReceiptLeaf.cancel_reason` gibi şifreli); kaynak modülün (§12.A)
    beyan notu ve uyarı alanları yoktur (D41)."""
    alanlar = {alan.name for alan in OrganMembership._meta.get_fields()}
    assert (
        not {
            "eligibility_declared",
            "eligibility_declaration_note",
            "compliance_warnings",
            "compliance_justification",
            "status_changed_at",
            "deleted_at",
        }
        & alanlar
    )
    assert {"mem_approval_no", "representative_decision", "external_assignment_start"} <= alanlar
    assert {f.name for f in crypto.encrypted_fields_of(OrganMembership)} == {
        "evidence_note",
        "dropped_reason",
        "eligibility_bar_basis",
        "cancel_reason",
    }
    assert OrganMembership._meta.get_field("representation").null is False


@pytest.mark.parametrize("durum", [MembershipStatus.DUSTU, MembershipStatus.IPTAL])
def test_kayit_dusmus_ya_da_iptal_acilamaz(durum: str) -> None:
    donem = o.donem()
    with pytest.raises(UyelikDurumuGecersiz):
        OrganMembership.objects.create(
            term=donem,
            person=o.kisi(),
            organ="YK",
            seat_type="ASIL",
            elected_by="GENEL_KURUL",
            status=durum,
            drop_kind="ISTIFA" if durum == MembershipStatus.DUSTU else "",
        )


def test_dusen_geri_donmez_iptal_son_durumdur() -> None:
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi())
    uyelik.status, uyelik.drop_kind = MembershipStatus.DUSTU, "ISTIFA"
    uyelik.save()
    for hedef in (MembershipStatus.SECILDI, MembershipStatus.ADAY, MembershipStatus.IPTAL):
        uyelik.status = hedef
        with pytest.raises(UyelikDurumuGecersiz):
            uyelik.save()
    iptal = o.devralinan(donem, o.kisi())
    iptal.status = MembershipStatus.IPTAL
    iptal.save(update_fields=["status"])
    iptal.status = MembershipStatus.SECILDI
    with pytest.raises(UyelikDurumuGecersiz):
        iptal.save(update_fields=["status"])


def test_secilmis_adaya_donmez() -> None:
    """`ADAY` → `SECILDI` tek yönlüdür (tasarım §5.2.2): seçilmiş kayıt yeniden aday olmaz."""
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi())
    uyelik.status = MembershipStatus.ADAY
    with pytest.raises(UyelikDurumuGecersiz):
        uyelik.save()
    assert OrganMembership.objects.get(pk=uyelik.pk).status == MembershipStatus.SECILDI


def test_aday_dusurulmez() -> None:
    donem = o.donem()
    aday = o.yk_adayi(donem, o.kisi(), o.olaganustu_genel_kurul(donem))
    aday.status, aday.drop_kind = MembershipStatus.DUSTU, "ISTIFA"
    with pytest.raises(UyelikDurumuGecersiz):
        aday.save()
    assert OrganMembership.objects.get(pk=aday.pk).status == MembershipStatus.ADAY


def test_dusmede_tur_zorunlu_ve_yalniz_dusmede() -> None:
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi())
    uyelik.status = MembershipStatus.DUSTU
    with pytest.raises(IntegrityError), transaction.atomic():
        uyelik.save(update_fields=["status"])
    ikinci = o.devralinan(donem, o.kisi())
    ikinci.drop_kind = "ISTIFA"
    with pytest.raises(IntegrityError), transaction.atomic():
        ikinci.save(update_fields=["drop_kind"])


@pytest.mark.parametrize(
    ("durum", "tur"), [(MembershipStatus.DUSTU, "ISTIFA"), (MembershipStatus.IPTAL, "")]
)
def test_iptal_ve_dusmus_uyelik_guncellenmez(durum: str, tur: str) -> None:
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi())
    uyelik.status, uyelik.drop_kind = durum, tur
    uyelik.save()
    with pytest.raises(UyelikDurumuGecersiz):
        uyelikler.update_membership(uyelik, votes=3)
    assert OrganMembership.objects.get(pk=uyelik.pk).votes is None


# ============================================================ yapı


def test_pasif_kisi_organa_eklenemez() -> None:
    donem = o.donem()
    kisi = kisiler.update_person(o.kisi(), status=PersonStatus.PASIF)
    with pytest.raises(ValueError, match="Pasif kişi organa eklenemez"):
        o.devralinan(donem, kisi)
    kurul = o.olaganustu_genel_kurul(donem)
    etkin = o.kisi(external_yk_terms=0)
    aday = o.yk_adayi(donem, etkin, kurul)
    kisiler.update_person(etkin, status=PersonStatus.PASIF)
    with pytest.raises(ValueError, match="Pasif kişi"):
        uyelikler.elect_membership(aday)
    assert not OrganMembership.objects.filter(status=MembershipStatus.SECILDI).exists()


@pytest.mark.parametrize(
    ("alanlar", "ileti"),
    [
        ({"organ": "TEMSILCI"}, "yalnız yönetim kurulu ve Denetleme Kurulu"),
        ({"organ": "DK"}, "koltuk grubu"),
        ({"seat_group": "VELI"}, "yalnız Denetleme Kurulu"),
        ({"organ": "DK", "seat_group": "OGRETMEN"}, "seçim kanalıyla"),
        ({"elected_by": "YK_KARARI"}, "seçim kanalıyla"),
        ({"seat_order": 1}, "Yedek sırası"),
        ({"mem_approval_no": "X-1"}, "öğretmen koltuğunda"),
    ],
    ids=["organ", "dk-grubu", "grup-yk", "dk-ogretmen-kanal", "yk-kanal", "sira", "mem"],
)
def test_yapisal_ret(alanlar: dict[str, object], ileti: str) -> None:
    donem = o.donem()
    temel: dict[str, object] = {
        "term": donem,
        "person": o.kisi(),
        "organ": "YK",
        "seat_type": "ASIL",
        "elected_by": "GENEL_KURUL",
        "source": "DEVRALINAN",
    }
    with pytest.raises(ValueError, match=ileti):
        uyelikler.assign_membership(**{**temel, **alanlar})  # type: ignore[arg-type]
    assert not OrganMembership.objects.exists()


def test_genel_kurul_baska_donemin_ise_reddedilir() -> None:
    """Olağan genel kurulun seçtiği üye açılacak (`HAZIRLIK`) döneme yazılır; açık döneme değil."""
    donem = o.donem()
    olagan = genel_kurul_servisi.genel_kurul_olustur(donem=donem, kind=AssemblyKind.OLAGAN)
    with pytest.raises(ValueError, match="açtığı döneme"):
        o.yk_adayi(donem, o.kisi(), olagan)


def test_kapanmis_doneme_uyelik_yazilmaz() -> None:
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi())
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.KAPANDI, end_date=date(2027, 9, 30)
    )
    with pytest.raises(DonemKapali):
        o.devralinan(donem, o.kisi())
    with pytest.raises(DonemKapali):
        uyelikler.update_membership(uyelik, votes=4)
    with pytest.raises(DonemKapali):
        kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.GOREV_BOLUMU)


# ============================================================ tek kaynak seçicileri


def test_secicilerin_sirasi_pythonda_turk_alfabesiyle() -> None:
    """Şifreli adda veritabanı sıralaması anlamsızdır: asıl önce, yedek sırası, sonra çözülmüş ad."""
    donem = o.donem()
    adlar = ["Çiçek", "Cemre", "Ilgın", "İpek"]
    for ad in adlar:
        o.devralinan(donem, o.kisi(first_name=ad, last_name="Örnekkaya"))
    yedekler = [
        o.devralinan(
            donem, o.kisi(first_name=f"Yedek {ad}", last_name="Uydurma"), seat_type="YEDEK"
        )
        for ad in ("Zeren", "Ayla")
    ]
    uyelikler.update_membership(yedekler[0], seat_order=1)
    uyelikler.update_membership(yedekler[1], seat_order=2)
    sirali = [u.person.first_name for u in selectors.membership_list(donem, "YK")]
    assert sirali == ["Cemre", "Çiçek", "Ilgın", "İpek", "Yedek Zeren", "Yedek Ayla"]
    kadro = selectors.elected_roster(donem, "YK")
    assert [u.person.first_name for u in kadro["yedek"]] == ["Yedek Zeren", "Yedek Ayla"]
    assert selectors.candidate_roster(donem, "YK") == {"asil": [], "yedek": []}


def test_gorevdeki_asil_yedekten_cagrilani_icerir() -> None:
    """`seat_type` değişmez; yedekten çağrıyı `promoted_on` gösterir (plan F1c kararları)."""
    donem = o.donem()
    asil = o.devralinan(donem, o.kisi())
    yedek = o.devralinan(donem, o.kisi(), seat_type="YEDEK")
    asil.status, asil.drop_kind = MembershipStatus.DUSTU, "ISTIFA"
    asil.save()
    yedek.promoted_on = date(2026, 11, 2)
    yedek.save(update_fields=["promoted_on"])
    assert [u.pk for u in selectors.gorevdeki_asillar(donem, "YK")] == [yedek.pk]
    assert selectors.bekleyen_yedekler(donem, "YK") == []
    assert OrganMembership.objects.get(pk=yedek.pk).seat_type == SeatType.YEDEK
    assert selectors.kadro_sayilari(donem, "YK") == {SeatType.ASIL: 1, SeatType.YEDEK: 0}


# ============================================================ uçlar


def test_kadro_serilestiricisinde_dayanak_gerekce_ve_uyari_ozeti_yok() -> None:
    donem = o.donem()
    uyelik = o.dk_ogretmeni(donem, o.ogretmen(), elected_by="MEM_GOREVLENDIRME")
    uyelik.eligibility_bar, uyelik.eligibility_bar_basis = EligibilityBar.VAR, "SUC_12_5_14_7"
    uyelik.save(update_fields=["eligibility_bar", "eligibility_bar_basis"])
    istemci = APIClient()
    yanitlar = [
        istemci.get(f"{UC}{uyelik.pk}/").json(),
        istemci.get(UC, {"term": str(donem.pk), "organ": "DK"}).json()[0],
        istemci.get(f"/api/v1/oab/terms/{donem.pk}/roster/DK/").json()["gorevdeki_asillar"][0],
    ]
    for govde in yanitlar:
        assert not {"eligibility_bar_basis", "dropped_reason", "rule_warnings"} & set(govde)
        assert govde["eligibility_bar"] == "VAR" and govde["person_name"]
        assert "SUC_12_5_14_7" not in str(govde)
    assert not AccessLog.objects.exists()  # kadro okuması günlüğe yazmaz


def test_kadro_ucu_sayilar_ve_uyarilar() -> None:
    donem = o.donem()
    o.devralinan(donem, o.kisi())
    govde = APIClient().get(f"/api/v1/oab/terms/{donem.pk}/roster/YK/").json()
    assert govde["kadro"] == {"asil": 1, "yedek": 0}
    uyarilar = [u for u in govde["kadro_uyarilari"] if u["durum"] == "uyari"]
    assert len(uyarilar) == 2
    assert all(u["metin"].endswith("(md. 12/1).") for u in uyarilar)
    # Görevdeki asıl başkansız: eksik satırı (md. 12/3; gerekçe istemez).
    (eksik,) = [u for u in govde["kadro_uyarilari"] if u["durum"] == "eksik"]
    assert eksik["atif"] == "md. 12/3"
    assert APIClient().get(f"/api/v1/oab/terms/{donem.pk}/roster/DIVAN/").status_code == 400
    assert APIClient().get(UC, {"organ": "YK"}).status_code == 400


def test_uc_ile_kayit_ve_guncelleme() -> None:
    donem = o.donem()
    kisi = o.ogretmen()
    istemci = APIClient()
    yanit = istemci.post(
        UC,
        {
            "term": donem.pk,
            "person": kisi.pk,
            "organ": "DK",
            "seat_type": "YEDEK",
            "seat_group": "OGRETMEN",
            "elected_by": "OGRETMENLER_KURULU",
            "start_date": "2026-10-15",
            "seat_order": 2,
            "evidence_note": "Uydurma not",
        },
        format="json",
    )
    assert yanit.status_code == 201, yanit.json()
    govde = yanit.json()
    assert (govde["status"], govde["source"], govde["seat_order"]) == ("SECILDI", "PROGRAM", 2)
    yanit = istemci.patch(f"{UC}{govde['id']}/", {"votes": 17}, format="json")
    assert yanit.status_code == 200 and yanit.json()["votes"] == 17
    # Uç devralınan üyelik yazmaz (geçiş kurulumunun işidir); `source` alanı yok sayılır.
    yanit = istemci.post(
        UC,
        {
            "term": donem.pk,
            "person": o.kisi().pk,
            "organ": "DIVAN",
            "seat_type": "ASIL",
            "elected_by": "GENEL_KURUL",
        },
        format="json",
    )
    assert yanit.status_code == 400


def test_engel_dayanagi_erisim_gunlugune_yazilarak_okunur() -> None:
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi())
    istemci = APIClient()
    bos = istemci.get(f"{UC}{uyelik.pk}/eligibility-basis/").json()
    assert bos["eligibility_bar_basis"] is None
    assert not AccessLog.objects.exists()  # boş dayanakta okunan özel nitelikli veri yok
    uyelik.eligibility_bar, uyelik.eligibility_bar_basis = EligibilityBar.VAR, "TEK_BIRLIK_12_4"
    uyelik.eligibility_bar_found_on = date(2026, 11, 3)
    uyelik.save(
        update_fields=["eligibility_bar", "eligibility_bar_basis", "eligibility_bar_found_on"]
    )
    govde = istemci.get(f"{UC}{uyelik.pk}/eligibility-basis/").json()
    assert govde == {
        "eligibility_bar": "VAR",
        "eligibility_bar_basis": "TEK_BIRLIK_12_4",
        "eligibility_bar_found_on": "2026-11-03",
    }
    satir = AccessLog.objects.get()
    assert (satir.kind, satir.model, satir.object_id, satir.field) == (
        AccessKind.OZEL_NITELIKLI_ALAN,
        "oab.OrganMembership",
        str(uyelik.pk),
        "eligibility_bar_basis",
    )
    assert "TEK_BIRLIK" not in str(satir.__dict__)


def test_engel_dayanaginin_okuru_uyeligi_yazan_rollerdir() -> None:
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi())
    uyelik.eligibility_bar_basis = "SUC_12_5_14_7"
    uyelik.save(update_fields=["eligibility_bar_basis"])
    for rol, beklenen in (
        (AccountRole.DENETLEME_KURULU, 403),
        (AccountRole.MUDUR, 403),
        (AccountRole.SEKRETER, 200),
    ):
        _rol_oturumu(rol)
        yanit = APIClient().get(f"{UC}{uyelik.pk}/eligibility-basis/")
        assert yanit.status_code == beklenen, rol
        # Kadroyu her rol okur; yazmayı Denetleme Kurulu ve müdür yapamaz.
        assert APIClient().get(f"{UC}{uyelik.pk}/").status_code == 200
    assert AccessLog.objects.count() == 1
    _rol_oturumu(AccountRole.DENETLEME_KURULU)
    yanit = APIClient().patch(f"{UC}{uyelik.pk}/", {"votes": 3}, format="json")
    assert yanit.status_code == 403 and yanit.json()["code"] == "rol_yetkisiz"


# ============================================================ denetim izi


def test_uyelik_izi_kisisiz_degerler_tasir() -> None:
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi())
    uyelikler.update_membership(uyelik, evidence_note="Uydurma dayanak", votes=12)
    satirlar = list(
        AuditTrail.objects.filter(model="oab.OrganMembership", object_id=str(uyelik.pk)).order_by(
            "seq"
        )
    )
    assert [s.action for s in satirlar] == ["OLUSTUR", "GUNCELLE"]
    assert all(s.term_id == donem.pk for s in satirlar)
    assert satirlar[0].values["status"] == [None, "SECILDI"]
    assert "person" not in satirlar[0].values and "evidence_note" not in satirlar[0].values
    assert "evidence_note" in satirlar[1].changed_fields
    assert satirlar[1].values == {"votes": [None, 12]}


# ============================================================ kurul kayıtları


def test_toplanti_no_donem_ve_organ_icinde_siradir() -> None:
    donem = o.donem()
    ilk = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.GOREV_BOLUMU)
    ikinci = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.AYLIK)
    dk = kurullar.toplanti_olustur(donem=donem, organ="DK", kind=MeetingKind.GOREV_BOLUMU)
    assert (ilk.meeting_no, ikinci.meeting_no, dk.meeting_no) == (1, 2, 1)
    assert ilk.status == MeetingStatus.PLANLANDI
    with pytest.raises(ValueError, match="yalnız yönetim kurulu"):
        kurullar.toplanti_olustur(donem=donem, organ="DIVAN", kind=MeetingKind.AYLIK)
    ilk.status = MeetingStatus.YAPILDI
    with pytest.raises(IntegrityError), transaction.atomic():
        ilk.save(update_fields=["status"])  # yapılan toplantının zamanı vardır


def test_katilim_tekil_ve_ozur_yalniz_katilmayanda() -> None:
    donem = o.donem()
    toplanti = kurullar.toplanti_olustur(
        donem=donem,
        organ="YK",
        kind=MeetingKind.GOREV_BOLUMU,
        scheduled_at=datetime(2026, 10, 20, 15, 0, tzinfo=UTC),
    )
    uyelik = o.devralinan(donem, o.kisi())
    ilk = kurullar.katilim_yaz(toplanti, uyelik, present=False, excused=True)
    ayni = kurullar.katilim_yaz(toplanti, uyelik, present=True)
    assert ilk.pk == ayni.pk and BoardMeetingAttendance.objects.count() == 1
    assert (ayni.present, ayni.excused) == (True, False)
    with pytest.raises(ValueError, match="özürlü"):
        kurullar.katilim_yaz(toplanti, uyelik, present=True, excused=True)
    dk = o.dk_ogretmeni(donem, o.ogretmen())
    with pytest.raises(ValueError, match="aynı kurulun"):
        kurullar.katilim_yaz(toplanti, dk, present=True)
    izler = AuditTrail.objects.filter(model="oab.BoardMeetingAttendance").order_by("seq")
    assert [s.action for s in izler] == ["OLUSTUR", "GUNCELLE"]
    assert all(s.term_id == donem.pk for s in izler)  # dönem toplantıdan gelir


def test_katilim_yalniz_gorevdeki_asila() -> None:
    """Çağrılmamış yedek kurulun üyesi değildir (md. 12/1, 13/6): katılımı yeter sayıyı ve devamsızlık
    zincirini bozar. Yedekten çağrılan asıl yerindedir (`selectors.gorevdeki_asillar` ile aynı koşul)."""
    donem = o.donem()
    toplanti = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.AYLIK)
    yedek = o.devralinan(donem, o.kisi(), seat_type=SeatType.YEDEK)
    with pytest.raises(ValueError, match="çağrılmamış yedeğe"):
        kurullar.katilim_yaz(toplanti, yedek, present=True)
    assert not BoardMeetingAttendance.objects.exists()
    # Yedek çağrısı (6. adım): karar bağı F3'e dek yoksa uyarı + gerekçedir.
    yedek = uyelik_gecisleri.yedek_cagir(
        yedek, organ="YK", promoted_on=date(2026, 11, 2), gerekce=uyum.Gerekce(metin="Uydurma.")
    )
    satir = kurullar.katilim_yaz(toplanti, yedek, present=True)
    assert satir.membership_id == yedek.pk
    assert [u.pk for u in selectors.gorevdeki_asillar(donem, "YK")] == [yedek.pk]


def test_karar_taslagi_varsayilan_ve_f1c_turleri() -> None:
    donem = o.donem()
    toplanti = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.GOREV_BOLUMU)
    karar = kurullar.karar_taslagi_olustur(
        toplanti, kind=DecisionKind.GOREV_BOLUMU, text="Uydurma görev bölümü metni."
    )
    assert karar.status == DecisionStatus.TASLAK
    assert (karar.book_id, karar.decision_no, karar.page_no) == (None, None, None)
    kurullar.karar_taslagi_olustur(toplanti, kind=DecisionKind.YEDEK_CAGIRMA)
    with pytest.raises(ValueError, match="bu sürümde"):
        kurullar.karar_taslagi_olustur(toplanti, kind=DecisionKind.HARCAMA)
    iz = AuditTrail.objects.get(model="oab.BoardDecision", object_id=str(karar.pk))
    assert iz.term_id == donem.pk and "text" in iz.changed_fields and "text" not in iz.values
    # Defterdeki (defter, sıra no) tekildir; deftere işlenen kararın defter bilgisi vardır.
    defter = kurullar.karar_defteri_olustur(last_no_before_program=41, last_page_before_program=12)
    BoardDecision.objects.filter(pk=karar.pk).update(book=defter, decision_no=42, page_no=13)
    ikinci = BoardDecision.objects.exclude(pk=karar.pk).get()
    with pytest.raises(IntegrityError), transaction.atomic():
        BoardDecision.objects.filter(pk=ikinci.pk).update(book=defter, decision_no=42)
    with pytest.raises(IntegrityError), transaction.atomic():
        BoardDecision.objects.filter(pk=ikinci.pk).update(status=DecisionStatus.DEFTERE_ISLENDI)
    assert defter.kind == "KARAR_DEFTERI" and defter.status == "KULLANIMDA"
    # Denetleme Kurulunun yedeği karar olmadan çağrılır (md. 14/6; tasarım E65): DK toplantısına
    # yedek çağırma kararı yazılmaz, görev bölümü kararı yazılır.
    dk = kurullar.toplanti_olustur(donem=donem, organ="DK", kind=MeetingKind.GOREV_BOLUMU)
    with pytest.raises(ValueError, match="yalnız yönetim kurulu"):
        kurullar.karar_taslagi_olustur(dk, kind=DecisionKind.YEDEK_CAGIRMA)
    assert not BoardDecision.objects.filter(meeting=dk).exists()
    assert kurullar.karar_taslagi_olustur(dk, kind=DecisionKind.GOREV_BOLUMU).meeting_id == dk.pk
