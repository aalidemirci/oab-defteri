"""Birlik temsilcileri (`tm`, tasarım §6.4.4, §10.3; F1c 6. adım).

Kurul temsilcisi sayıları kademe koşuluyla (`okul.kademe`; karma okulda iki kademenin satırları
birlikte): fazla temsilci yazımda uyarı + gerekçedir, eksik temsilci çizelgede tamamlanacaktır.
Başkanın kendiliğinden üye olduğu üç komisyon görev bölümüyle açılır; başkan olmayan temsilci uyarı +
gerekçedir. Pay dağıtım komisyonu yalnız kayıttır. Kantin denetim komisyonunun temsilcisi görevdeki
asıl yönetim kurulu üyesi ve velidir. Kampüs yönetimi kayıt satırıdır. E03'ün satırları bu çizelgeden
basılır (`test_e03_cizelgeyle_ayni_kaynaktan`; F1c 10. adım). Kişi adları ve okul kartı UYDURMADIR.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.oab.hatalar import GerekceGerekli
from apps.oab.models import (
    BoardDecision,
    ComplianceItem,
    ComplianceKind,
    DecisionKind,
    DecisionStatus,
    MeetingKind,
    OabTerm,
    OrganMembership,
    PersonKind,
    Representation,
    SeatType,
)
from apps.oab.services import gorev_evraki, kurullar, temsilciler, uyum
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import AccountRole, CanteenMode, SchoolLevel
from apps.okul.tests.okul_karti_ortak import okul_kartini_dogrudan_yaz
from shared import evrak

pytestmark = pytest.mark.django_db

GUN = date(2026, 10, 20)


def _ekle(donem: OabTerm, temsil: str, kisi: Any = None, **alanlar: Any) -> OrganMembership:
    return temsilciler.temsilci_ekle(
        term=donem,
        person=kisi if kisi is not None else o.kisi(),
        representation=temsil,
        start_date=GUN,
        **alanlar,
    )


def _cizelge(donem: OabTerm) -> dict[str, temsilciler.TemsilciSatiri]:
    return {
        satir.representation: satir for satir in temsilciler.temsilci_cizelgesi(donem, tarih=GUN)
    }


def _donem_satirlari(donem: OabTerm, kural_id: str) -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(
            subject_type="oab.OabTerm", subject_id=str(donem.pk), rule_id=kural_id
        )
    )


def _kantin_temsilcisi() -> Any:
    """Kantin denetim komisyonunun uygun temsilcisi: görevdeki asıl yönetim kurulu velisi."""
    donem = OabTerm.objects.get()
    return o.secilmis(donem).person


#: (temsil, kural, uygulanan okul kartı, uygulanmayan okul kartı, uygun temsilci fabrikası)
SAYI_KURALLARI = [
    pytest.param(
        Representation.ODUL_DISIPLIN_KURULU,
        "temsilci.odul_disiplin_kurulu",
        {"levels": [SchoolLevel.ORTAOGRETIM.value]},
        {"levels": [SchoolLevel.ORTAOKUL.value]},
        None,
        id="odul_disiplin",
        marks=pytest.mark.kural_davranis("temsilci.odul_disiplin_kurulu"),
    ),
    pytest.param(
        Representation.DAVRANIS_DEGERLENDIRME_KURULU,
        "temsilci.davranis_degerlendirme_kurulu",
        {"levels": [SchoolLevel.ORTAOKUL.value]},
        {"levels": [SchoolLevel.ORTAOGRETIM.value]},
        None,
        id="davranis_degerlendirme",
        marks=pytest.mark.kural_davranis("temsilci.davranis_degerlendirme_kurulu"),
    ),
    pytest.param(
        Representation.SOSYAL_ETKINLIKLER_KURULU,
        "temsilci.sosyal_etkinlikler_kurulu",
        {},
        None,
        None,
        id="sosyal_etkinlikler",
        marks=pytest.mark.kural_davranis("temsilci.sosyal_etkinlikler_kurulu"),
    ),
    pytest.param(
        Representation.KONTENJAN_KOMISYONU,
        "temsilci.kontenjan_komisyonu",
        {"levels": [SchoolLevel.ORTAOGRETIM.value]},
        {"levels": [SchoolLevel.ILKOKUL.value]},
        None,
        id="kontenjan",
        marks=pytest.mark.kural_davranis("temsilci.kontenjan_komisyonu"),
    ),
    pytest.param(
        Representation.RPD_YURUTME_KOMISYONU,
        "temsilci.rpd_yurutme_komisyonu",
        {},
        None,
        None,
        id="rpd_yurutme",
        marks=pytest.mark.kural_davranis("temsilci.rpd_yurutme_komisyonu"),
    ),
    pytest.param(
        Representation.KANTIN_DENETIM_KOMISYONU,
        "temsilci.kantin_denetim_komisyonu",
        {"canteen_mode": CanteenMode.BIRLIKCE_ISLETILIYOR.value},
        {"canteen_mode": CanteenMode.KANTIN_YOK.value},
        _kantin_temsilcisi,
        id="kantin_denetim",
        marks=pytest.mark.kural_davranis("temsilci.kantin_denetim_komisyonu"),
    ),
]


@pytest.mark.parametrize(
    ("temsil", "kural_id", "uygulanan", "uygulanmayan", "uygun"), SAYI_KURALLARI
)
def test_kademeye_gore_temsilci_satirlari(
    temsil: str,
    kural_id: str,
    uygulanan: dict[str, Any],
    uygulanmayan: dict[str, Any] | None,
    uygun: Any,
) -> None:
    """Koşulu tutmayan okulda satır yoktur; tutan okulda satır temsilcisizken tamamlanacaktır
    (gerekçe istemez), kural sayısında uygundur, fazlası gerekçesiz reddedilir, gerekçeyle
    kaydedilir (uyum satırının konusu birlik dönemidir)."""
    donem = o.donem()
    if uygulanmayan is not None:
        okul_kartini_dogrudan_yaz(**uygulanmayan)
        assert temsil not in _cizelge(donem)
    okul_kartini_dogrudan_yaz(**uygulanan)
    satir = _cizelge(donem)[temsil]
    assert (satir.kural, satir.durum, satir.uyeler) == (kural_id, "eksik", [])
    fabrika = uygun or o.kisi
    _ekle(donem, temsil, fabrika())
    if temsil == Representation.ODUL_DISIPLIN_KURULU:
        assert _cizelge(donem)[temsil].durum == "eksik"  # yedek henüz yok
        _ekle(donem, temsil, o.kisi(), seat_type=SeatType.YEDEK)
    assert _cizelge(donem)[temsil].durum == "uygun"
    assert _donem_satirlari(donem, kural_id) == []
    fazla = fabrika()
    with pytest.raises(GerekceGerekli) as hata:
        _ekle(donem, temsil, fazla)
    assert "temsil" in str(hata.value.detail).lower() or "veli" in str(hata.value.detail)
    _ekle(donem, temsil, fazla, gerekce=uyum.Gerekce(metin="Uydurma gerekçe."))
    (uyum_satiri,) = _donem_satirlari(donem, kural_id)
    assert uyum_satiri.kind == ComplianceKind.SAPMA
    assert _cizelge(donem)[temsil].durum == "uyari"


@pytest.mark.kural_davranis("temsilci.odul_disiplin_kurulu")
@pytest.mark.kural_davranis("temsilci.davranis_degerlendirme_kurulu")
def test_karma_okulda_iki_kademenin_satirlari() -> None:
    """Karma okulda (ortaokul + ortaöğretim) iki kademenin satırları birlikte görünür (UY-12);
    yalnız ortaokulda ortaöğretimin satırları görünmez."""
    donem = o.donem()
    okul_kartini_dogrudan_yaz(levels=[SchoolLevel.ORTAOKUL.value, SchoolLevel.ORTAOGRETIM.value])
    karma = set(_cizelge(donem))
    assert {
        Representation.ODUL_DISIPLIN_KURULU,
        Representation.KONTENJAN_KOMISYONU,
        Representation.DAVRANIS_DEGERLENDIRME_KURULU,
    } <= karma
    okul_kartini_dogrudan_yaz(levels=[SchoolLevel.ORTAOKUL.value])
    yalniz_ortaokul = set(_cizelge(donem))
    assert Representation.DAVRANIS_DEGERLENDIRME_KURULU in yalniz_ortaokul
    assert (
        not {
            Representation.ODUL_DISIPLIN_KURULU,
            Representation.KONTENJAN_KOMISYONU,
        }
        & yalniz_ortaokul
    )


@pytest.mark.parametrize(
    "temsil",
    [
        pytest.param(
            Representation.TASIMACI_TESPIT_KOMISYONU,
            id="tasimaci_tespit",
            marks=pytest.mark.kural_davranis("temsilci.tasimaci_tespit_komisyonu"),
        ),
        pytest.param(
            Representation.MUHAMMEN_BEDEL_KOMISYONU,
            id="muhammen_bedel",
            marks=pytest.mark.kural_davranis("temsilci.muhammen_bedel_komisyonu"),
        ),
        pytest.param(
            Representation.KIRALAMA_IHALE_KOMISYONU,
            id="kiralama_ihale",
            marks=pytest.mark.kural_davranis("temsilci.kiralama_ihale_komisyonu"),
        ),
    ],
)
def test_baskan_kendiliginden_uye(temsil: str) -> None:
    """Başkan bu komisyonlara kendiliğinden üyedir (seçim yok): görev bölümü başkanı atayınca satır
    açılır ve kuralı uygundur; başkan olmayan temsilci uyarı + gerekçedir (konu üyeliktir)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    assert _cizelge(donem)[temsil].durum == "eksik"
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=GUN)
    satir = _cizelge(donem)[temsil]
    assert [u.person_id for u in satir.uyeler] == [uyeler[0].person_id]
    assert satir.uyeler[0].elected_by == "KENDILIGINDEN" and satir.durum == "uygun"
    with pytest.raises(GerekceGerekli) as hata:
        _ekle(donem, temsil, uyeler[1].person)
    assert "birlik başkanı temsil eder" in str(hata.value.detail)
    vekil = _ekle(donem, temsil, uyeler[1].person, gerekce=uyum.Gerekce(metin="Başkan izinli."))
    (uyum_satiri,) = ComplianceItem.objects.filter(
        subject_id=str(vekil.pk), rule_id__startswith="temsilci."
    )
    assert uyum_satiri.subject_type == "oab.OrganMembership"
    assert [u["durum"] for u in OrganMembership.objects.get(pk=vekil.pk).rule_warnings] == ["uyari"]


@pytest.mark.kural_davranis("temsilci.pay_dagitim_komisyonu")
def test_pay_dagitim_komisyonu_yalniz_secildiyse() -> None:
    """Yalnız kayıt (plan F1c 2. adım notları): satır başkan seçildiyse görünür; sayı uyarısı ve uyum
    satırı yoktur (`karsilastirma: parametre`, `denetle` çağrılmaz)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    assert Representation.PAY_DAGITIM_KOMISYONU not in _cizelge(donem)
    o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=GUN)
    assert Representation.PAY_DAGITIM_KOMISYONU not in _cizelge(donem)  # kendiliğinden açılmaz
    for uye in uyeler[:3]:
        _ekle(donem, Representation.PAY_DAGITIM_KOMISYONU, uye.person)
    satir = _cizelge(donem)[Representation.PAY_DAGITIM_KOMISYONU]
    assert (satir.durum, satir.metin, len(satir.uyeler)) == (None, "", 3)
    # Üyelik komisyona seçilmedir (md. 17/1-b-3), başkanlık sıfatıyla kendiliğinden değildir.
    assert {u.elected_by for u in satir.uyeler} == {"MEM_GOREVLENDIRME"}
    assert not ComplianceItem.objects.filter(rule_id="temsilci.pay_dagitim_komisyonu").exists()


@pytest.mark.kural_davranis("temsilci.rpd_yurutme_komisyonu")
def test_rpd_satirinda_ogretmenler_kurulu_notu() -> None:
    """RPD satırı, komisyonun öteki üyelerini öğretmenler kurulunun belirlediğini not eder (RPD
    16/5; kuralın yorumu): yönetim kurulu kararı bu satırda öneri ve bilgi niteliğindedir."""
    donem = o.donem()
    satir = _cizelge(donem)[Representation.RPD_YURUTME_KOMISYONU]
    assert any("öğretmenler kurulu" in metin for metin in satir.notlar)
    assert all(not s.notlar for t, s in _cizelge(donem).items() if t != "RPD_YURUTME_KOMISYONU")


@pytest.mark.kural_davranis("temsilci.kantin_denetim_komisyonu")
def test_kantin_denetim_temsilcisi_yk_velisi_degilse_uyari() -> None:
    """Temsilci birlik yönetiminden (görevdeki asıl yönetim kurulu üyesi) ve veli değilse uyarı +
    gerekçe (Genelge 2020/8 A-1/a-b "birlik yönetiminden bir veli"); kantini olmayan okulda kural
    sessizdir, satır kayıt olarak açılabilir."""
    donem = o.donem()
    okul_kartini_dogrudan_yaz(canteen_mode=CanteenMode.KIRAYA_VERILIYOR.value)
    with pytest.raises(GerekceGerekli):
        _ekle(donem, Representation.KANTIN_DENETIM_KOMISYONU, o.kisi())  # YK üyesi değil
    kursiyer = o.kisi(kind=PersonKind.KURSIYER, is_parent=False, adult_declared=True)
    o.secilmis(donem, kursiyer)  # YK üyesi ama veli değil
    with pytest.raises(GerekceGerekli) as hata:
        _ekle(donem, Representation.KANTIN_DENETIM_KOMISYONU, kursiyer)
    assert "birlik yönetiminden" in str(hata.value.detail)
    assert not ComplianceItem.objects.filter(rule_id="temsilci.kantin_denetim_komisyonu").exists()
    okul_kartini_dogrudan_yaz(canteen_mode=CanteenMode.KANTIN_YOK.value)
    assert Representation.KANTIN_DENETIM_KOMISYONU not in _cizelge(donem)
    kayit = _ekle(donem, Representation.KANTIN_DENETIM_KOMISYONU, o.kisi())  # sessiz
    assert kayit.status == "SECILDI"
    assert _cizelge(donem)[Representation.KANTIN_DENETIM_KOMISYONU].durum == "uygun"


def test_kampus_yonetimi_kayit_satiri() -> None:
    """Kampüs yönetimi (md. 13/7) kuralsız kayıt satırıdır: okul kampüsteyse çizelgede görünür."""
    donem = o.donem()
    okul_kartini_dogrudan_yaz(in_campus=False)
    assert Representation.KAMPUS_YONETIMI not in _cizelge(donem)
    okul_kartini_dogrudan_yaz(in_campus=True)
    satir = _cizelge(donem)[Representation.KAMPUS_YONETIMI]
    assert (satir.kural, satir.durum) == (None, None)
    kayit = _ekle(donem, Representation.KAMPUS_YONETIMI)
    assert kayit.elected_by == "YK_KARARI"


def test_temsilci_kaydi_ve_karar_bagi() -> None:
    """Aynı kişi iki kurulda temsilci olabilir, aynı kurulda iki kez olamaz; karar bağı bu dönemin
    yönetim kurulu toplantısının kararıdır (E03'ün karar no'su)."""
    donem = o.donem()
    kisi = o.kisi()
    toplanti = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.GOREV_BOLUMU)
    karar = kurullar.karar_taslagi_olustur(toplanti, kind=DecisionKind.GOREV_BOLUMU)
    # Kabul F3'ün karar defteri akışındadır; burada ORM'le yazılır.
    BoardDecision.objects.filter(pk=karar.pk).update(status=DecisionStatus.KABUL_EDILDI)
    sosyal = _ekle(
        donem, Representation.SOSYAL_ETKINLIKLER_KURULU, kisi, representative_decision=karar
    )
    assert sosyal.representative_decision_id == karar.pk
    _ekle(donem, Representation.RPD_YURUTME_KOMISYONU, kisi)
    with pytest.raises(ValueError, match="zaten var"):
        _ekle(donem, Representation.SOSYAL_ETKINLIKLER_KURULU, kisi)
    dk_toplantisi = kurullar.toplanti_olustur(
        donem=donem, organ="DK", kind=MeetingKind.GOREV_BOLUMU
    )
    dk_karari = kurullar.karar_taslagi_olustur(dk_toplantisi, kind=DecisionKind.GOREV_BOLUMU)
    with pytest.raises(ValueError, match="yönetim kurulu toplantısının"):
        _ekle(donem, Representation.KONTENJAN_KOMISYONU, representative_decision=dk_karari)


@pytest.mark.parametrize("durum", [DecisionStatus.TASLAK, DecisionStatus.IPTAL])
def test_kabul_edilmemis_temsilci_karari_baglanamaz(durum: str) -> None:
    """Bağlanan karar kabul edilmiş olmalıdır (tasarım §7.2 "Notlar"): görev bölümünün ürettiği taslak
    ya da iptal edilmiş karar temsilci kararı diye bağlanamaz (servis ve uç 400; kayıt yazılmaz)."""
    donem = o.donem()
    toplanti = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.GOREV_BOLUMU)
    karar = kurullar.karar_taslagi_olustur(toplanti, kind=DecisionKind.GOREV_BOLUMU)
    if durum == DecisionStatus.IPTAL:
        karar = kurullar.karar_durumu_yaz(karar, DecisionStatus.IPTAL)
    with pytest.raises(ValueError, match="kabul edilmiş olmalı"):
        _ekle(donem, Representation.SOSYAL_ETKINLIKLER_KURULU, representative_decision=karar)
    govde = {
        "term": donem.pk,
        "person": o.kisi().pk,
        "representation": "SOSYAL_ETKINLIKLER_KURULU",
        "start_date": "2026-10-20",
        "representative_decision": karar.pk,
    }
    yanit = APIClient().post("/api/v1/oab/representatives/", govde, format="json")
    assert yanit.status_code == 400, yanit.content
    assert not OrganMembership.objects.filter(organ="TEMSILCI").exists()


def test_temsilciler_ucu() -> None:
    """Çizelge her role açıktır; kaydı program yöneticisi ve yönetim kurulu rolleri yazar."""
    donem = o.donem()
    govde = {
        "term": donem.pk,
        "person": o.kisi().pk,
        "representation": "SOSYAL_ETKINLIKLER_KURULU",
        "start_date": "2026-10-20",
    }
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        istemci = APIClient()
        assert istemci.get(f"/api/v1/oab/representatives/?term={donem.pk}").status_code == 200
        assert istemci.post("/api/v1/oab/representatives/", govde, format="json").status_code == 403
    yanit = APIClient().post("/api/v1/oab/representatives/", govde, format="json")
    assert yanit.status_code == 201, yanit.content
    cizelge = APIClient().get(f"/api/v1/oab/representatives/?term={donem.pk}").json()
    (sosyal,) = [s for s in cizelge if s["representation"] == "SOSYAL_ETKINLIKLER_KURULU"]
    assert sosyal["durum"] == "uygun" and len(sosyal["uyeler"]) == 1


def test_e03_cizelgeyle_ayni_kaynaktan() -> None:
    """E03'ün satırları yalnız temsilciler çizelgesindendir (tasarım §9.6 E03 satırı ve §6.4.4; plan
    F1c-10): kurul ve komisyonlar çizelgenin sırasıyla, temsilciler çizelgenin üyeleri; kademe,
    kantin ve kampüs koşulu değişince belge de değişir. Rehberlik komisyonunun notu çizelgenin
    notundan basılır."""
    donem = o.donem()
    okul_kartini_dogrudan_yaz(
        levels=[SchoolLevel.ORTAOKUL.value],
        canteen_mode=CanteenMode.KANTIN_YOK.value,
        in_campus=False,
    )
    _ekle(donem, Representation.SOSYAL_ETKINLIKLER_KURULU)

    def belge_ve_cizelge() -> tuple[list[tuple[str, ...]], list[temsilciler.TemsilciSatiri]]:
        belge, _ = gorev_evraki.e03_belgesi(donem)
        (tablo,) = [b for b in belge.bloklar if isinstance(b, evrak.Tablo)]
        notlu = evrak.Paragraf(gorev_evraki.RPD_NOTU) in belge.bloklar
        cizelge = temsilciler.temsilci_cizelgesi(donem)
        rpd = [s for s in cizelge if s.representation == Representation.RPD_YURUTME_KOMISYONU]
        assert notlu is bool(rpd and rpd[0].notlar)
        return list(tablo.satirlar), cizelge

    satirlar, cizelge = belge_ve_cizelge()
    assert [s[1] for s in satirlar if s[1]] == [s.ad for s in cizelge]
    assert Representation.KAMPUS_YONETIMI not in {s.representation for s in cizelge}
    (sosyal,) = [s for s in satirlar if s[1] == str(Representation.SOSYAL_ETKINLIKLER_KURULU.label)]
    (uye,) = _cizelge(donem)[Representation.SOSYAL_ETKINLIKLER_KURULU].uyeler
    assert sosyal[2] == evrak.ad_soyad(uye.person.first_name, uye.person.last_name)
    okul_kartini_dogrudan_yaz(
        levels=[SchoolLevel.ORTAOKUL.value, SchoolLevel.ORTAOGRETIM.value],
        canteen_mode=CanteenMode.KIRAYA_VERILIYOR.value,
        in_campus=True,
    )
    satirlar, cizelge = belge_ve_cizelge()
    adlar = [s[1] for s in satirlar if s[1]]
    assert adlar == [s.ad for s in cizelge]
    for temsil in (
        Representation.ODUL_DISIPLIN_KURULU,
        Representation.KAMPUS_YONETIMI,
        Representation.KANTIN_DENETIM_KOMISYONU,
    ):
        assert str(temsil.label) in adlar, temsil
