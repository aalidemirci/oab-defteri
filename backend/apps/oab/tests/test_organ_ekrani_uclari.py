"""Organlar ve Temsilciler ekranlarının uçları (plan F1c 11. adımın ikinci parçası).

Kadro okumasına eklenenler (üyeliklerin açık uyum satırları role göre süzülür, seçilme sayaçları),
yönetim kurulunun aylık toplantı günü kuralı (E01'in D bölümü; serbest metin, program kural koymaz)
ve bağlanabilecek kararların listesi (yalnız kabul edilmiş ya da deftere işlenmiş yönetim kurulu
kararı). Adlar ve tarihler UYDURMADIR.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.oab.models import (
    BoardDecision,
    BoardMeeting,
    ComplianceItem,
    DecisionStatus,
    EligibilityBar,
    OabTerm,
    TermStatus,
)
from apps.oab.services import gorev_evraki, uyelik_gecisleri, uyelikler, uyum
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import AccountRole

pytestmark = pytest.mark.django_db


def _kadro(donem: OabTerm, organ: str) -> dict[str, Any]:
    yanit = APIClient().get(f"/api/v1/oab/terms/{donem.pk}/roster/{organ}/")
    assert yanit.status_code == 200, yanit.content
    veri: dict[str, Any] = yanit.json()
    return veri


def _engelli_uye(donem: OabTerm) -> int:
    """Görev alma engeli (suç dayanağı) işaretli adayı gerekçeyle seçer; uyum satırı açık kalır."""
    aday = o.yk_adayi(donem, o.kisi(external_yk_terms=0), o.olaganustu_genel_kurul(donem))
    uyelik_gecisleri.engel_yaz(
        aday,
        eligibility_bar=EligibilityBar.VAR,
        eligibility_bar_basis="SUC_12_5_14_7",
        eligibility_bar_found_on=date(2026, 10, 14),
    )
    secilen = uyelikler.elect_membership(
        aday, start_date=o.SECIM_GUNU, gerekce=uyum.Gerekce(metin="Uydurma gerekçe.")
    )
    return secilen.pk


def test_kadro_uyum_satirlari_role_gore_suzulur() -> None:
    """Engel satırını program yöneticisi ve yönetim kurulu rolleri atfıyla, Denetleme Kurulu ve müdür
    atıfsız genel metinle görür (kullanıcı kararı 10.11.2026; `uyum_satiri_gorunumu`). Gerekçe dönmez."""
    donem = o.donem()
    uyelik = _engelli_uye(donem)
    satir = ComplianceItem.objects.get(rule_id="uyelik.suc_engeli", subject_id=str(uyelik))

    (yonetici,) = [s for s in _kadro(donem, "YK")["uyum_satirlari"] if s["uyelik"] == uyelik]
    assert yonetici["metin"] == satir.message and yonetici["atif"].startswith("md. 12/5")
    assert yonetici["tur"] == "SAPMA" and yonetici["gerekceli"] is True
    assert "Uydurma gerekçe" not in str(yonetici)
    with o.rol_olarak(AccountRole.SEKRETER):
        (sekreter,) = _kadro(donem, "YK")["uyum_satirlari"]
    assert sekreter["atif"] == yonetici["atif"]
    for rol in (AccountRole.DENETLEME_KURULU, AccountRole.MUDUR):
        with o.rol_olarak(rol):
            (gorunum,) = _kadro(donem, "YK")["uyum_satirlari"]
        assert gorunum["metin"] == uyum.ENGEL_GENEL_METNI, rol
        assert gorunum["atif"] == "" and "12/" not in str(gorunum), rol


def test_kadro_secilme_sayaclari() -> None:
    """Yönetim kurulunda seçilme sayısı (program + beyan), Denetleme Kurulunda başkanlık sayısı; beyan
    "bilinmiyor"sa boş. Alım komisyonunda sayaç yoktur."""
    donem = o.donem()
    bilinen = o.secilmis(donem, o.kisi(external_yk_terms=2))
    bilinmeyen = o.secilmis(donem, o.kisi(external_yk_terms=None))
    sayaclar = {s["uyelik"]: s for s in _kadro(donem, "YK")["secilme_sayaclari"]}
    # Devralınan kayıt sayaç dışıdır (beyan görevdeki seçimi içerir).
    assert sayaclar[bilinen.pk] == {"uyelik": bilinen.pk, "program": 0, "beyan": 2}
    assert sayaclar[bilinmeyen.pk]["beyan"] is None
    veli, *_ = o.dk_kurulu(donem)
    dk = {s["uyelik"]: s for s in _kadro(donem, "DK")["secilme_sayaclari"]}
    assert dk[veli.pk]["program"] == 0 and set(dk[veli.pk]) == {"uyelik", "program", "beyan"}
    assert _kadro(donem, "ALIM_KOMISYONU")["secilme_sayaclari"] == []


def test_toplanti_gunu_yazilir_ve_e01e_basilir() -> None:
    """Toplantı günü serbest metindir: boşluklar sadeleşir, E01'in D bölümünün ilk satırına basılır,
    boş metin siler ("………"). Aynı değer yeniden yazılınca değişiklik yoktur."""
    donem = o.donem()
    uc = f"/api/v1/oab/terms/{donem.pk}/meeting-day/"
    yanit = APIClient().put(uc, {"yk_meeting_day_rule": "  Her ayın   ilk salısı "}, format="json")
    assert yanit.status_code == 200, yanit.content
    assert yanit.json()["yk_meeting_day_rule"] == "Her ayın ilk salısı"
    donem.refresh_from_db()
    belge, _ = gorev_evraki.e01_belgesi(donem)
    assert "Her ayın ilk salısı" in str(belge)
    assert APIClient().put(uc, {"yk_meeting_day_rule": ""}, format="json").status_code == 200
    donem.refresh_from_db()
    assert donem.yk_meeting_day_rule == ""


def test_toplanti_gunu_sinir_rol_ve_kapanmis_donem() -> None:
    """64 karakterden uzun metin 400; başkan yazamaz (403, E01'i üretenler: program yöneticisi ve
    sekreter); kapanmış dönem 409 `donem_kapali`."""
    donem = o.donem()
    uc = f"/api/v1/oab/terms/{donem.pk}/meeting-day/"
    assert APIClient().put(uc, {"yk_meeting_day_rule": "x" * 65}, format="json").status_code == 400
    with o.rol_olarak(AccountRole.BASKAN):
        assert (
            APIClient().put(uc, {"yk_meeting_day_rule": "Salı"}, format="json").status_code == 403
        )
    with o.rol_olarak(AccountRole.SEKRETER):
        assert (
            APIClient().put(uc, {"yk_meeting_day_rule": "Salı"}, format="json").status_code == 200
        )
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.KAPANDI, end_date=date(2027, 10, 1)
    )
    yanit = APIClient().put(uc, {"yk_meeting_day_rule": "Çarşamba"}, format="json")
    assert yanit.status_code == 409 and yanit.json()["code"] == "donem_kapali"


def test_baglanabilir_kararlar_yalniz_kabul_ya_da_defter() -> None:
    """Liste yalnız bu dönemin yönetim kurulu toplantısının kabul edilmiş ya da deftere işlenmiş
    kararıdır; taslak (görev bölümünün kararı), Denetleme Kurulu toplantısının kararı ve başka dönemin
    kararı gelmez. Karar metni dönmez."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    sonuc = o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=date(2026, 10, 16))
    dk = o.dk_kurulu(donem)
    dk_sonuc = o.dk_gorev_bolumu(donem, dk[0], gun=date(2026, 10, 16))
    uc = f"/api/v1/oab/terms/{donem.pk}/linkable-decisions/"
    assert APIClient().get(uc).json() == []
    # Kabul F3'ün akışıdır: test durumu doğrudan yazar. Denetleme Kurulunun kabul edilmiş kararı
    # yönetim kurulu kararı değildir (organ süzgeci).
    BoardDecision.objects.filter(pk__in=[sonuc.karar.pk, dk_sonuc.karar.pk]).update(
        status=DecisionStatus.KABUL_EDILDI
    )
    (karar,) = APIClient().get(uc).json()
    assert karar["id"] == sonuc.karar.pk and karar["status"] == DecisionStatus.KABUL_EDILDI
    assert karar["toplanti_gunu"] == "2026-10-16"
    assert "text" not in karar
    with o.rol_olarak(AccountRole.MUDUR):
        assert len(APIClient().get(uc).json()) == 1
    # Dönem süzgeci: toplantısı başka döneme ait yönetim kurulu kararı bu dönemin listesine gelmez.
    oteki = OabTerm.objects.create(
        name="2025-2026 birlik dönemi",
        school_year=donem.school_year,
        rule_package=donem.rule_package,
        status=TermStatus.KAPANDI,
        start_date=date(2025, 10, 10),
        end_date=date(2026, 10, 9),
    )
    BoardMeeting.objects.filter(pk=sonuc.toplanti.pk).update(term=oteki)
    assert APIClient().get(uc).json() == []
    oteki_uc = f"/api/v1/oab/terms/{oteki.pk}/linkable-decisions/"
    assert [k["id"] for k in APIClient().get(oteki_uc).json()] == [sonuc.karar.pk]
