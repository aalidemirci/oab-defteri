"""Geçiş kurulumunun uçları (tasarım §7.9 adım 1-4; plan F1c 8. adımın servisleri, uçları 11. adımda).

Servisin kuralları `test_gecis.py`'dedir; burada uçların sözleşmesi sınanır: durum okuması (açık adımlar,
geçiş dönemi, karar defteri, görev süresi uyarısı ve uyum satırları), devralınan kurul ve temsilci,
seçilme sayısı beyanı ("bilinmiyor" tek gerekçe, verilmeyen alan değişmez), karar defteri ve iptali,
dönem iptali ve "Geçiş kurulumu tamamlandı" işaretinden sonra 409 `gecis_kapali`. Dönem kopyası
bozukken okuma açık kalır, kurallar okunmaz (plan F1c 3. adım notları). Adlar ve tarihler UYDURMADIR.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.oab.kurallar import DonemKopyasiDogrulanamadi, kural
from apps.oab.models import (
    BookStatus,
    MembershipSource,
    MembershipStatus,
    OabPerson,
    OabTerm,
    OrganMembership,
    TermStatus,
)
from apps.oab.services import gecis
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import SchoolYear

pytestmark = pytest.mark.django_db

UC = "/api/v1/oab/transition/"
GEREKCE = "Uydurma gerekçe: eski karar defteri elde değil."


def _bugun() -> date:
    return timezone.localdate()


def _yil(bas: date) -> SchoolYear:
    kayit: SchoolYear = SchoolYear.objects.create(
        name="2026-2027",
        start_date=bas - timedelta(days=40),
        end_date=bas + timedelta(days=280),
        is_active=True,
    )
    return kayit


def _istemci() -> APIClient:
    return APIClient()


def _durum() -> dict[str, Any]:
    yanit = _istemci().get(UC)
    assert yanit.status_code == 200, yanit.content
    veri: dict[str, Any] = yanit.json()
    return veri


def _ac(gun_once: int = 30) -> OabTerm:
    bas = _bugun() - timedelta(days=gun_once)
    yil = _yil(bas)
    yanit = _istemci().post(
        "/api/v1/oab/terms/",
        {"name": "Uydurma birlik dönemi", "school_year": yil.pk, "start_date": bas.isoformat()},
        format="json",
    )
    assert yanit.status_code == 201, yanit.content
    return OabTerm.objects.get(pk=yanit.json()["id"])


def test_durum_ucu_baslamadi_suruyor_ve_acilis_uyarisi() -> None:
    bos = _durum()
    assert bos["state"] == gecis.DURUM_BASLAMADI
    assert (bos["donem"], bos["karar_defteri"]) == (None, None)
    assert bos["open_steps"] == [gecis.ADIM_DONEM]
    # Son genel kurulun üzerinden bir yıl geçmiş: dönem açılır, görev süresi uyarısı yanıttadır.
    bas = _bugun() - timedelta(days=400)
    yil = _yil(bas)
    yanit = _istemci().post(
        "/api/v1/oab/terms/",
        {"name": "Uydurma birlik dönemi", "school_year": yil.pk, "start_date": bas.isoformat()},
        format="json",
    )
    assert yanit.status_code == 201, yanit.content
    uyarilar = yanit.json()["uyarilar"]
    assert {u["atif"] for u in uyarilar} == {"md. 12/2", "md. 14/2"}
    assert all(u["metin"].endswith(f"({u['atif']}).") for u in uyarilar)
    durum = _durum()
    assert durum["state"] == gecis.DURUM_SURUYOR
    assert durum["open_steps"] == [
        gecis.ADIM_KURUL,
        gecis.ADIM_KARAR_DEFTERI,
        gecis.ADIM_TAMAMLA,
    ]
    assert durum["donem"]["transition_completed_on"] is None
    assert durum["donem"]["status"] == TermStatus.ACIK
    assert len(durum["gorev_suresi_uyarilari"]) == 2
    assert durum["uyum_satirlari"] == []


def test_devralinan_ucu_kurul_ve_temsilci() -> None:
    _ac()
    veli = o.kisi(external_yk_terms=1)
    yanit = _istemci().post(
        f"{UC}inherited/",
        {"organ": "YK", "person": veli.pk, "role": "MUHASIP", "evidence_note": "Uydurma kanıt"},
        format="json",
    )
    assert yanit.status_code == 201, yanit.content
    veri = yanit.json()
    assert (veri["source"], veri["status"], veri["role"]) == (
        MembershipSource.DEVRALINAN,
        MembershipStatus.SECILDI,
        "MUHASIP",
    )
    temsilci = o.kisi()
    eksik = _istemci().post(f"{UC}inherited/", {"organ": "TEMSILCI", "person": temsilci.pk})
    assert eksik.status_code == 400
    assert "representation" in eksik.json()["fields"]
    yanit = _istemci().post(
        f"{UC}inherited/",
        {"organ": "TEMSILCI", "person": temsilci.pk, "representation": "KAMPUS_YONETIMI"},
        format="json",
    )
    assert yanit.status_code == 201, yanit.content
    assert (yanit.json()["organ"], yanit.json()["source"]) == ("TEMSILCI", "DEVRALINAN")
    assert gecis.ADIM_KURUL not in _durum()["open_steps"]


def test_koltuk_uygunlugu_devralinan_kayitta_da_serttir() -> None:
    """Okul müdürü yönetim kuruluna giremez (altın kural 3, kullanıcı kararı): 400, kayıt yok."""
    _ac()
    mudur = o.kisi(kind="IDARECI", is_parent=True)
    OabPerson.objects.filter(pk=mudur.pk).update(is_principal=True)
    yanit = _istemci().post(f"{UC}inherited/", {"organ": "YK", "person": mudur.pk})
    assert yanit.status_code == 400, yanit.content
    assert not OrganMembership.objects.exists()


def test_sayac_beyani_ucu_bilinmiyor_tek_gerekce_ve_uyum_satiri() -> None:
    _ac()
    birinci, ikinci = o.kisi(), o.kisi()
    govde = {"beyanlar": [{"person": birinci.pk, "yk": None}, {"person": ikinci.pk, "yk": None}]}
    gerekcesiz = _istemci().post(f"{UC}election-counts/", govde, format="json")
    assert gerekcesiz.status_code == 400
    assert gerekcesiz.json()["code"] == "gerekce_gerekli"
    yanit = _istemci().post(f"{UC}election-counts/", {**govde, "gerekce": GEREKCE}, format="json")
    assert yanit.status_code == 200, yanit.content
    assert yanit.json()["bilinmeyen_sayisi"] == 2
    satirlar = _durum()["uyum_satirlari"]
    assert {s["konu"] for s in satirlar} == {str(birinci.pk), str(ikinci.pk)}
    assert {(s["tur"], s["atif"], s["gerekceli"], s["sayac_alani"]) for s in satirlar} == {
        ("SAPMA", "md. 12/4", True, "yk")
    }
    # Verilmeyen alan değişmez; sayı girilince satır kapanır (düzeltme değil, bilginin girilmesi).
    yanit = _istemci().post(
        f"{UC}election-counts/",
        {"beyanlar": [{"person": birinci.pk, "yk": 2}, {"person": ikinci.pk}]},
        format="json",
    )
    assert yanit.status_code == 200, yanit.content
    kisiler = {k["id"]: k for k in yanit.json()["kisiler"]}
    assert kisiler[birinci.pk]["external_yk_terms"] == 2
    assert kisiler[ikinci.pk]["external_yk_terms"] is None
    assert {s["konu"] for s in _durum()["uyum_satirlari"]} == {str(ikinci.pk)}
    # Verilmiş sayının düzeltmesi gerekçe ister.
    yanit = _istemci().post(
        f"{UC}election-counts/", {"beyanlar": [{"person": birinci.pk, "yk": 3}]}, format="json"
    )
    assert yanit.status_code == 400
    assert "gerekçe" in yanit.json()["message"]


def test_karar_defteri_ucu_tasdiksiz_gerekce_ve_iptal() -> None:
    _ac()
    govde = {"last_no_before_program": 5, "last_page_before_program": 2}
    gerekcesiz = _istemci().post(f"{UC}decision-book/", govde, format="json")
    assert gerekcesiz.status_code == 400
    assert gerekcesiz.json()["code"] == "gerekce_gerekli"
    assert "(md. 23/2)." in gerekcesiz.json()["message"]
    bos = _istemci().post(f"{UC}decision-book/", {}, format="json")
    assert bos.status_code == 400 and "son sıra no" in bos.json()["message"]
    sayfasiz = _istemci().post(f"{UC}decision-book/", {"last_no_before_program": 4}, format="json")
    assert sayfasiz.status_code == 400 and "sayfası" in sayfasiz.json()["message"]
    yanit = _istemci().post(f"{UC}decision-book/", {**govde, "gerekce": GEREKCE}, format="json")
    assert yanit.status_code == 201, yanit.content
    defter = yanit.json()
    assert (defter["last_no_before_program"], defter["status"]) == (5, BookStatus.KULLANIMDA)
    durum = _durum()
    assert durum["karar_defteri"]["id"] == defter["id"]
    (satir,) = durum["uyum_satirlari"]
    assert (satir["tur"], satir["atif"], satir["konu"], satir["sayac_alani"]) == (
        "SAPMA",
        "md. 23/2",
        str(defter["id"]),
        "",
    )
    gerekcesiz_iptal = _istemci().post(
        f"{UC}decision-book/{defter['id']}/cancel/", {"cancel_reason": " "}, format="json"
    )
    assert gerekcesiz_iptal.status_code == 400
    iptal = _istemci().post(
        f"{UC}decision-book/{defter['id']}/cancel/",
        {"cancel_reason": "Uydurma: sayfa yanlış."},
        format="json",
    )
    assert iptal.status_code == 200, iptal.content
    assert iptal.json()["status"] == BookStatus.IPTAL
    durum = _durum()
    assert durum["karar_defteri"] is None and durum["uyum_satirlari"] == []


def test_donem_iptal_ucu() -> None:
    donem = _ac()
    yanit = _istemci().post(f"/api/v1/oab/terms/{donem.pk}/cancel/", {}, format="json")
    assert yanit.status_code == 400
    yanit = _istemci().post(
        f"/api/v1/oab/terms/{donem.pk}/cancel/",
        {"cancel_reason": "Uydurma: dönem başı yanlış girildi."},
        format="json",
    )
    assert yanit.status_code == 200, yanit.content
    assert yanit.json()["status"] == TermStatus.IPTAL
    assert _durum()["state"] == gecis.DURUM_BASLAMADI


def test_tamamlandi_isaretinden_sonra_gecis_yazmalari_409() -> None:
    donem = _ac()
    veli = o.kisi(external_yk_terms=0)
    yanit = _istemci().post(f"{UC}complete/", None, format="json")
    assert yanit.status_code == 200, yanit.content
    assert yanit.json()["transition_completed_on"] == _bugun().isoformat()
    durum = _durum()
    assert (durum["state"], durum["open_steps"]) == (gecis.DURUM_TAMAMLANDI, [])
    for yol, govde in (
        (f"{UC}inherited/", {"organ": "YK", "person": veli.pk}),
        (f"{UC}election-counts/", {"beyanlar": [{"person": veli.pk, "yk": 1}]}),
        (f"{UC}decision-book/", {"last_no_before_program": 1, "last_page_before_program": 1}),
        (f"{UC}complete/", None),
        (f"/api/v1/oab/terms/{donem.pk}/cancel/", {"cancel_reason": "Uydurma."}),
    ):
        yanit = _istemci().post(yol, govde, format="json")
        assert yanit.status_code == 409, (yol, yanit.content)
        assert yanit.json()["code"] == "gecis_kapali", yol


def test_bozuk_kopyada_okuma_acik_kurallar_okunmaz() -> None:
    """D7 dönem kolu: dönem, kadro ve geçiş durumu okunur; uyarı ve atıf bozuk kopyadan okunmaz."""
    donem = _ac(gun_once=400)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE oab_rulepackage SET content_sha256 = %s WHERE id = %s",
            ["0" * 64, donem.rule_package_id],
        )
    donem = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    with pytest.raises(DonemKopyasiDogrulanamadi):
        kural("yonetim_kurulu.gorev_suresi_yil", tarih=_bugun(), donem=donem)
    durum = _durum()
    assert durum["donem"]["kural_kopyasi_tutuyor"] is False
    assert durum["gorev_suresi_uyarilari"] == []
    kadro = _istemci().get(f"/api/v1/oab/terms/{donem.pk}/roster/YK/")
    assert kadro.status_code == 200, kadro.content
    assert kadro.json()["kadro_uyarilari"] == []


def test_sihirbaz_adimlari_on_yuzle_birebir() -> None:
    """Sihirbazın adımları (zorunlu üçü ve atlanabilir Birlik Dönemi) ön yüzdekiyle aynıdır
    (`okul/api.ts` `SETUP_STEPS`, `WIZARD_STEPS`; plan F1c 8. adım "sihirbaz kaydı")."""
    from pathlib import Path

    from apps.okul.services import setup as setup_service

    for kok in (Path(__file__).resolve().parents[4], Path("/repo")):
        yol = kok / "frontend/src/modules/okul/api.ts"
        if yol.is_file():
            kaynak = yol.read_text(encoding="utf-8")
            break
    else:
        pytest.fail("frontend/src/modules/okul/api.ts bulunamadı.")
    assert (
        'export const SETUP_STEPS: readonly SetupStep[] = ["password", "school", "calendar"];'
        in kaynak
    )
    assert setup_service.SETUP_STEPS == ("password", "school", "calendar")
    assert (
        'export const WIZARD_STEPS: readonly WizardStep[] = [...SETUP_STEPS, "birlik_donemi"];'
        in (kaynak)
    )
    assert setup_service.WIZARD_STEPS == (*setup_service.SETUP_STEPS, "birlik_donemi")
