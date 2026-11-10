"""Üyeliğin geçişleri: iptal, düşme, görev alma engeli ve öneriler (F1c 6. adım; tasarım §5 O1,
§5.2.2, §7.2).

Kural davranışları `kurallar/`'dadır (`yk`, `dk`, `tm`). Burada kuralsız davranış ve uç sözleşmesi
sınanır: iptalin gerekçesi zorunlu ve şifrelidir, kim iz satırındadır, iptal kaydı hiç olmamış sayılır;
engelin dayanağı şifreli yazılır, iz satırına ve yazım yanıtına değeri girmez; uçların rol daraltmaları
tasarım §7.2'nin "Kim" sütunudur. Kişi adları UYDURMADIR.
"""

from __future__ import annotations

from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.oab.models import (
    ComplianceItem,
    ElectedBy,
    EligibilityBar,
    MeetingKind,
    MembershipStatus,
    OrganMembership,
    SeatGroup,
    SeatType,
    UyelikDurumuGecersiz,
)
from apps.oab.services import kurullar, uyelik_gecisleri, uyelikler, uyum
from apps.oab.tests import uyelik_ortak as o
from apps.okul import denetim_izi
from apps.okul.models import AccessLog, AccountRole, AuditTrail
from conftest import TEST_HESAP_ID

pytestmark = pytest.mark.django_db

UC = "/api/v1/oab/memberships/"


def test_iptal_gerekcesi_zorunlu_kim_iz_satirinda() -> None:
    """Yanlış kayıt `IPTAL` olur (O1): gerekçe zorunlu ve şifreli (`cancel_reason`), kim `updated_by`
    ve iz satırının hesabıdır; iptal son durumdur, kayıt hiç olmamış sayılır (aynı kişi yeniden
    yazılabilir)."""
    donem = o.donem()
    kisi = o.kisi()
    uyelik = o.secilmis(donem, kisi)
    with pytest.raises(ValueError, match="İptal gerekçesi"):
        uyelik_gecisleri.uyeligi_iptal_et(uyelik, cancel_reason="   ")
    iptal = uyelik_gecisleri.uyeligi_iptal_et(uyelik, cancel_reason=" Uydurma yanlış kayıt. ")
    assert (iptal.status, iptal.cancel_reason) == (MembershipStatus.IPTAL, "Uydurma yanlış kayıt.")
    assert str(iptal.updated_by_id) == TEST_HESAP_ID
    iz = AuditTrail.objects.filter(model="oab.OrganMembership", object_id=str(uyelik.pk)).last()
    assert iz is not None and iz.action == "DURUM" and str(iz.account_id) == TEST_HESAP_ID
    # Gerekçenin değeri iz satırına girmez; içerik MAC'i onu da kapsar (kayıt bütünlüğü tutar).
    assert "cancel_reason" not in iz.values
    assert denetim_izi.kaydi_dogrula(OrganMembership, str(uyelik.pk)) is True
    with pytest.raises(UyelikDurumuGecersiz):
        uyelik_gecisleri.uyeligi_iptal_et(iptal, cancel_reason="İkinci kez.")
    yeniden = o.secilmis(donem, kisi)
    assert yeniden.pk != uyelik.pk and yeniden.status == MembershipStatus.SECILDI
    dusmus = o.secilmis(donem)
    uyelik_gecisleri.uyeligi_dusur(dusmus, drop_kind="ISTIFA")
    with pytest.raises(UyelikDurumuGecersiz):
        uyelik_gecisleri.uyeligi_iptal_et(dusmus, cancel_reason="Düşmüş kayıt iptal edilmez.")


def test_engel_yazimi_dayanagi_disari_vermez() -> None:
    """Engel `VAR`'da dayanak ve tespit günü zorunludur; `YOK`'ta ikisi de boştur. Dayanak şifreli
    yazılır: iz satırında yalnız adı, yazım yanıtında hiç yoktur; erişim günlüğüne okuma düşmez."""
    donem = o.donem()
    uyelik = o.secilmis(donem)
    with pytest.raises(ValueError, match="Engel yoksa"):
        uyelik_gecisleri.engel_yaz(
            uyelik, eligibility_bar=EligibilityBar.YOK, eligibility_bar_basis="SUC_12_5_14_7"
        )
    yanit = APIClient().put(
        f"{UC}{uyelik.pk}/eligibility-basis/",
        {
            "eligibility_bar": "VAR",
            "eligibility_bar_basis": "SUC_12_5_14_7",
            "eligibility_bar_found_on": "2026-11-05",
        },
        format="json",
    )
    assert yanit.status_code == 200, yanit.content
    assert yanit.json() == {"eligibility_bar": "VAR", "eligibility_bar_found_on": "2026-11-05"}
    assert not AccessLog.objects.exists()
    iz = AuditTrail.objects.filter(model="oab.OrganMembership", object_id=str(uyelik.pk)).last()
    assert iz is not None and "eligibility_bar_basis" in iz.changed_fields
    assert "eligibility_bar_basis" not in iz.values and iz.values["eligibility_bar"][1] == "VAR"
    guncel = OrganMembership.objects.get(pk=uyelik.pk)
    assert guncel.eligibility_bar_basis == "SUC_12_5_14_7"
    kaldirilan = uyelik_gecisleri.engel_yaz(guncel, eligibility_bar=EligibilityBar.YOK)
    assert (kaldirilan.eligibility_bar_basis, kaldirilan.eligibility_bar_found_on) == ("", None)
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        assert (
            APIClient()
            .put(f"{UC}{uyelik.pk}/eligibility-basis/", {"eligibility_bar": "YOK"}, format="json")
            .status_code
            == 403
        )


def test_dusme_ve_iptal_uclarinin_rolleri() -> None:
    """Düşmeyi program yöneticisi ve sekreter yazar (tasarım §7.2 "Öğrencisi ayrılan veli"); iptal
    satırın bütün yazanlarınadır; Denetleme Kurulu ikisini de yazamaz. İptal edilen kayıt programda
    açılmış kayıttır: devralınan kaydı yalnız program yöneticisi iptal eder (`test_gecis`)."""
    donem = o.donem()
    birinci, ucuncu = (o.secilmis(donem) for _ in range(2))
    ikinci = o.dk_ogretmeni(donem, o.ogretmen())
    govde = {"drop_kind": "ISTIFA", "end_date": "2026-11-02"}
    with o.rol_olarak(AccountRole.BASKAN):
        assert APIClient().post(f"{UC}{birinci.pk}/drop/", govde, format="json").status_code == 403
    with o.rol_olarak(AccountRole.SEKRETER):
        yanit = APIClient().post(f"{UC}{birinci.pk}/drop/", govde, format="json")
    assert yanit.status_code == 200, yanit.content
    assert (yanit.json()["status"], yanit.json()["drop_kind"]) == ("DUSTU", "ISTIFA")
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        assert (
            APIClient()
            .post(f"{UC}{ikinci.pk}/cancel/", {"cancel_reason": "Yanlış."}, format="json")
            .status_code
            == 403
        )
    with o.rol_olarak(AccountRole.MUHASIP):
        yanit = APIClient().post(
            f"{UC}{ikinci.pk}/cancel/", {"cancel_reason": "Yanlış."}, format="json"
        )
    assert yanit.status_code == 200 and yanit.json()["status"] == "IPTAL"
    assert "cancel_reason" not in yanit.json()
    bos = APIClient().post(f"{UC}{ucuncu.pk}/cancel/", {}, format="json")
    assert bos.status_code == 400 and "cancel_reason" in bos.json()["fields"]


def test_kadro_ucu_onerileri_kisisizdir() -> None:
    """Kadro okuması önerileri ve hatırlatmaları taşır (saklanmaz); engelin dayanağını söylemez."""
    donem = o.donem()
    uye = o.secilmis(donem)
    uyelik_gecisleri.engel_yaz(
        uye,
        eligibility_bar=EligibilityBar.VAR,
        eligibility_bar_basis="TEK_BIRLIK_12_4",
        eligibility_bar_found_on=date(2026, 11, 5),
    )
    with o.rol_olarak(AccountRole.MUDUR):
        veri = APIClient().get(f"/api/v1/oab/terms/{donem.pk}/roster/YK/").json()
    turler = {(oneri["uyelik"], oneri["tur"]) for oneri in veri["oneriler"]}
    assert (uye.pk, "DUSURME") in turler and (uye.pk, "HATIRLATMA") in turler
    dusurme = next(x for x in veri["oneriler"] if x["tur"] == "DUSURME")
    assert dusurme["gun"] == "2026-11-05" and dusurme["drop_kind"] == "DIGER"
    assert "birlik" not in dusurme["metin"] and "12/4" not in dusurme["metin"]


@pytest.mark.parametrize(
    ("dayanak", "oneri_var"),
    [
        pytest.param("TEK_BIRLIK_12_4", False, id="tek_birlik"),
        pytest.param("SUC_12_5_14_7", True, id="suc"),
    ],
)
def test_dk_uyesinde_engel_onerisi_dayanaga_gore(dayanak: str, oneri_var: bool) -> None:
    """Başka birlik yönetimi engeli yalnız yönetim kurulunda hükümdür (md. 12/4 2. cümle): Denetleme
    Kurulu üyesinde düşürme önerisi üretmez; suç engeli Denetleme Kurulunda da hükümdür (md. 14/7)."""
    donem = o.donem()
    veli = o.secilmis(donem, organ="DK", seat_group=SeatGroup.VELI)
    uyelik_gecisleri.engel_yaz(
        veli,
        eligibility_bar=EligibilityBar.VAR,
        eligibility_bar_basis=dayanak,
        eligibility_bar_found_on=date(2026, 11, 5),
    )
    veri = APIClient().get(f"/api/v1/oab/terms/{donem.pk}/roster/DK/").json()
    turler = {(oneri["uyelik"], oneri["tur"]) for oneri in veri["oneriler"]}
    assert ((veli.pk, "DUSURME") in turler) is oneri_var


def test_dk_adayinda_tek_birlik_engeli_yk_kurali_degil() -> None:
    """Denetleme Kurulu adayında başka birlik yönetimi işareti yönetim kurulu kuralını koşturmaz:
    seçim gerekçesiz geçer, `yonetim_kurulu.tek_birlik` satırı açılmaz."""
    donem = o.donem()
    aday = uyelikler.assign_membership(
        term=donem,
        person=o.kisi(),
        organ="DK",
        seat_type=SeatType.ASIL,
        seat_group=SeatGroup.VELI,
        elected_by=ElectedBy.GENEL_KURUL,
        assembly=o.olaganustu_genel_kurul(donem),
    )
    uyelik_gecisleri.engel_yaz(
        aday,
        eligibility_bar=EligibilityBar.VAR,
        eligibility_bar_basis="TEK_BIRLIK_12_4",
        eligibility_bar_found_on=date(2026, 10, 14),
    )
    secilen = uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
    assert secilen.status == MembershipStatus.SECILDI
    assert not ComplianceItem.objects.filter(rule_id="yonetim_kurulu.tek_birlik").exists()


#: Engelin dayanağını (ve onu ele veren kural kimliğini) okuyan roller (tasarım §4.4.2 ¹¹).
_DAYANAK_OKUYAN = {
    AccountRole.YONETICI,
    AccountRole.BASKAN,
    AccountRole.BASKAN_YARDIMCISI,
    AccountRole.MUHASIP,
    AccountRole.SEKRETER,
}


@pytest.mark.parametrize(
    ("dayanak", "kural", "atif"),
    [
        pytest.param("SUC_12_5_14_7", "uyelik.suc_engeli", "md. 12/5", id="suc"),
        pytest.param("TEK_BIRLIK_12_4", "yonetim_kurulu.tek_birlik", "md. 12/4", id="tek_birlik"),
    ],
)
def test_engel_uyum_satirini_dk_ve_mudur_genel_adla_gorur(
    dayanak: str, kural: str, atif: str
) -> None:
    """Görev alma engeli uyarısının kural kimliği uyum satırında, uyarı özetinde ve denetim izinde
    kalır; program yöneticisi ve yönetim kurulu rolleri onu görür, Denetleme Kurulu, müdür ve rolü
    bilinmeyen oturum yalnız "görev alma engeli" genel adını görür (kimlik ve atıf dayanağı ele verir;
    kullanıcı kararı 10.11.2026). Gerekçe metni görünüme girmez."""
    donem = o.donem()
    aday = o.yk_adayi(donem, o.kisi(external_yk_terms=0), o.olaganustu_genel_kurul(donem))
    uyelik_gecisleri.engel_yaz(
        aday,
        eligibility_bar=EligibilityBar.VAR,
        eligibility_bar_basis=dayanak,
        eligibility_bar_found_on=date(2026, 10, 14),
    )
    secilen = uyelikler.elect_membership(
        aday, start_date=o.SECIM_GUNU, gerekce=uyum.Gerekce(metin="Uydurma gerekçe.")
    )
    (satir,) = ComplianceItem.objects.filter(rule_id=kural, subject_id=str(secilen.pk))
    (ozet,) = [u for u in secilen.rule_warnings if u["kural"] == kural]
    iz = AuditTrail.objects.filter(model="oab.ComplianceItem", object_id=str(satir.pk)).last()
    assert iz is not None and iz.values.get("rule_id") == [None, kural]  # izde kimlik kalır
    for rol in [*AccountRole, None]:
        gorunum = uyum.uyum_satiri_gorunumu(satir, None if rol is None else rol.value)
        ozet_gorunumu = uyum.uyum_satiri_gorunumu(ozet, None if rol is None else rol.value)
        assert "text" not in gorunum and "justification_group" not in gorunum
        if rol in _DAYANAK_OKUYAN:
            assert (gorunum["rule_id"], gorunum["message"]) == (satir.rule_id, satir.message)
            assert (ozet_gorunumu["kural"], ozet_gorunumu["atif"]) == (kural, atif)
            continue
        assert gorunum["rule_id"] == uyum.ENGEL_GENEL_KIMLIGI, rol
        assert gorunum["ad"] == "Görev alma engeli" and gorunum["message"] == uyum.ENGEL_GENEL_METNI
        assert (ozet_gorunumu["kural"], ozet_gorunumu["atif"]) == (uyum.ENGEL_GENEL_KIMLIGI, "")
        assert "12/" not in str(gorunum) and "12/" not in str(ozet_gorunumu)
    # Satırın kendisi değişmedi; engel dışı satır her rolde olduğu gibi görünür.
    assert ComplianceItem.objects.get(pk=satir.pk).rule_id == kural
    baska = {"kural": "yonetim_kurulu.secilme_siniri", "atif": "md. 12/4", "mesaj": "x"}
    assert uyum.uyum_satiri_gorunumu(baska, AccountRole.MUDUR.value) == baska


@pytest.mark.parametrize("son_durum", ["DUSTU", "IPTAL"])
def test_dusmus_ya_da_iptal_uyelikte_engel_degismez(son_durum: str) -> None:
    """Düşmüş ya da iptal edilmiş üyeliğin görev alma engeli değiştirilemez (son durum)."""
    donem = o.donem()
    uyelik = o.secilmis(donem)
    if son_durum == "DUSTU":
        uyelik_gecisleri.uyeligi_dusur(uyelik, drop_kind="ISTIFA")
    else:
        uyelik_gecisleri.uyeligi_iptal_et(uyelik, cancel_reason="Uydurma yanlış kayıt.")
    with pytest.raises(UyelikDurumuGecersiz, match="değiştirilemez"):
        uyelik_gecisleri.engel_yaz(
            uyelik,
            eligibility_bar=EligibilityBar.VAR,
            eligibility_bar_basis="SUC_12_5_14_7",
            eligibility_bar_found_on=date(2026, 11, 5),
        )


def test_yapilmis_toplanti_yeniden_yapilamaz() -> None:
    """Yalnız planlanmış toplantı yapıldı olarak kaydedilir (durum makinesi)."""
    donem = o.donem()
    o.yk_kurulu(donem, asil=1)
    toplanti = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.AYLIK)
    for uyelik in OrganMembership.objects.filter(term=donem, organ="YK"):
        kurullar.katilim_yaz(toplanti, uyelik, present=True)
    yapildi = kurullar.toplanti_yapildi(toplanti, held_at=o.saat(date(2026, 11, 2)))
    with pytest.raises(ValueError, match="Yalnız planlanmış"):
        kurullar.toplanti_yapildi(yapildi, held_at=o.saat(date(2026, 11, 3)))


def test_dk_velisinin_ogrenci_ayrildi_dusmesi_md_7_2_disinda() -> None:
    """md. 7/2 2. cümle yalnız yönetim kurulu üyeliğidir: Denetleme Kurulu velisinin öğrencisi
    ayrılınca üyelik gerekçesiz düşer, `uyelik.ayrilan_veli_devam` satırı açılmaz (yönetim kurulunun
    sayısı burada aranmaz)."""
    donem = o.donem()
    veli = o.secilmis(donem, organ="DK", seat_group=SeatGroup.VELI)
    dusen = uyelik_gecisleri.uyeligi_dusur(veli, drop_kind="OGRENCI_AYRILDI")
    assert dusen.status == MembershipStatus.DUSTU
    assert not ComplianceItem.objects.filter(rule_id="uyelik.ayrilan_veli_devam").exists()


def test_bekleyen_yedekte_gorevlendirme_onerisi_yok() -> None:
    """Dört aydan uzun görevlendirmede yedek çağrısı önerisi yalnız görevdeki asıldadır; çağrılmamış
    yedekte öneri yoktur (md. 14/6 "yerine yedeği çağrılır")."""
    donem = o.donem()
    yedek = o.secilmis(donem, organ="DK", seat_group=SeatGroup.OGRETMEN, seat_type=SeatType.YEDEK)
    guncel = uyelikler.update_membership(
        yedek,
        external_assignment_start=date(2026, 11, 1),
        external_assignment_end=date(2027, 6, 1),
    )
    assert "YEDEK_CAGRISI" not in [x.tur for x in uyelik_gecisleri.oneriler(guncel)]
