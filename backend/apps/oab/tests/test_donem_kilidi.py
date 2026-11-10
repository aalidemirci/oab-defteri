"""Birlik dönemi, O2 dönem kilidi, M1 uçları ve iz bağı (F1c'nin 3. adımı; tasarım §5 O2, §5.2.1, §4.6.2).

Kişi ve okul adları UYDURMADIR. Kapanış testleri sentetik dönemle kurulur, gerçek kapanış F4'tedir.
"""

from __future__ import annotations

import ast
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from django.db import IntegrityError, connection, migrations, transaction
from django.db.migrations.loader import MigrationLoader
from django.utils import timezone
from rest_framework.test import APIClient

from apps.oab.hatalar import DonemKapali, DonemSaltOkur, DonemYazilamaz
from apps.oab.kurallar import yukleyici
from apps.oab.kurallar.hatalar import KuralPaketiKullanilamaz
from apps.oab.models import (
    AssemblyKind,
    ComplianceItem,
    ComplianceJustification,
    ComplianceKind,
    DraftText,
    GeneralAssembly,
    OabTerm,
    RulePackage,
    TermStatus,
)
from apps.oab.services import donem_kilidi, donemler, uyum, yarim_metin
from apps.oab.services import genel_kurul as genel_kurul_servisi
from apps.oab.services import iz as iz_yazari
from apps.okul import denetim_izi
from apps.okul.models import (
    AccountRole,
    AccountStatus,
    AuditLabel,
    AuditTrail,
    ImmutableRecord,
    SchoolYear,
)
from apps.okul.oturum import Yazar, yazar_olarak
from apps.okul.services import satir_izi
from apps.okul.tests.hesap_ortak import hesap_ac, muhurle
from conftest import oturumu_ac_test
from shared import crypto
from shared.exceptions import RolYetkisiz

GUN = date(2026, 10, 10)
ILAN_KURALI = "genel_kurul.ilan_en_az_gun"
UC = "/api/v1/oab/terms/"


def _yil() -> SchoolYear:
    yil: SchoolYear = SchoolYear.objects.create(
        name="2026-2027",
        start_date=date(2026, 9, 7),
        end_date=date(2027, 6, 25),
        is_active=True,
    )
    return yil


def _donem() -> OabTerm:
    return donemler.create_term(name="2026-2027 birlik dönemi", school_year=_yil(), start_date=GUN)


def _kapat(donem: OabTerm) -> OabTerm:
    """Sentetik kapanış (gerçek kapanış F4)."""
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.KAPANDI, end_date=date(2027, 10, 1)
    )
    return OabTerm.objects.get(pk=donem.pk)


# ============================================================ model kısıtları


@pytest.mark.django_db
def test_donem_acilisi_ilk_donemi_en_yeni_revizyona_baglar() -> None:
    donem = _donem()
    assert donem.status == TermStatus.ACIK
    assert donem.opened_by_assembly is None
    assert (donem.rule_package.package, donem.rule_package.rev) == ("OAB-2023.12", 1)
    assert donem_kilidi.kural_kopyasi_tutuyor(donem)


@pytest.mark.django_db
def test_ikinci_donem_bu_yoldan_acilamaz() -> None:
    donem = _donem()
    with pytest.raises(ValueError, match="genel kurulla"):
        donemler.create_term(name="ikinci", school_year=donem.school_year, start_date=GUN)
    assert OabTerm.objects.count() == 1


@pytest.mark.django_db
def test_program_baslangici_donem_basindan_once_olamaz() -> None:
    with pytest.raises(ValueError, match="dönem başından önce"):
        donemler.create_term(
            name="d", school_year=_yil(), start_date=GUN, program_start_date=date(2026, 10, 9)
        )
    assert not OabTerm.objects.exists()


@pytest.mark.django_db
def test_paket_yuklenemezse_donem_acilmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(yukleyici._Onbellek, "durum", yukleyici.PaketDurumu(hatalar=("bozuk",)))
    with pytest.raises(KuralPaketiKullanilamaz):
        donemler.create_term(name="d", school_year=_yil(), start_date=GUN)
    assert not OabTerm.objects.exists()


@pytest.mark.django_db
def test_en_cok_bir_acik_donem() -> None:
    donem = _donem()
    kopya = donem.rule_package
    with pytest.raises(IntegrityError), transaction.atomic():
        OabTerm.objects.create(
            name="ikinci",
            school_year=donem.school_year,
            start_date=GUN,
            rule_package=kopya,
            status=TermStatus.ACIK,
        )


@pytest.mark.django_db
def test_hazirlik_donemi_tarihsizdir_ve_en_cok_bir_tanedir() -> None:
    donem = _donem()
    kopya = donem.rule_package
    with pytest.raises(IntegrityError, match="ck_oabterm_baslangic"), transaction.atomic():
        OabTerm.objects.create(
            name="tarihli hazırlık",
            school_year=donem.school_year,
            rule_package=kopya,
            status=TermStatus.HAZIRLIK,
            start_date=GUN,
        )
    OabTerm.objects.create(
        name="hazırlık",
        school_year=donem.school_year,
        rule_package=kopya,
        status=TermStatus.HAZIRLIK,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        OabTerm.objects.create(
            name="ikinci hazırlık",
            school_year=donem.school_year,
            rule_package=kopya,
            status=TermStatus.HAZIRLIK,
        )


@pytest.mark.django_db
def test_donem_adi_iptal_olmayanlarda_tekildir() -> None:
    """OYS `uq_oabterm_name_alive`'ın karşılığı (O1): iptal edilen dönemin adı yeniden kullanılır."""
    donem = _donem()
    ortak = {
        "name": donem.name,
        "school_year": donem.school_year,
        "rule_package": donem.rule_package,
    }
    with pytest.raises(IntegrityError), transaction.atomic():
        OabTerm.objects.create(**ortak, status=TermStatus.HAZIRLIK)
    OabTerm.objects.create(**ortak, status=TermStatus.IPTAL)  # iptal satır kısıta girmez
    OabTerm.objects.filter(pk=donem.pk).update(status=TermStatus.IPTAL, start_date=None)
    OabTerm.objects.create(**ortak, status=TermStatus.HAZIRLIK)
    assert OabTerm.objects.filter(name=donem.name).count() == 3


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("alanlar", "kisit"),
    [
        ({"status": TermStatus.KAPANDI}, "ck_oabterm_bitis"),
        (
            {"status": TermStatus.KAPANDI, "end_date": date(2026, 10, 9)},
            "ck_oabterm_bitis_sirasi",
        ),
        ({"program_start_date": date(2026, 10, 9)}, "ck_oabterm_programa_baslama"),
    ],
)
def test_donem_tarih_kisitlari(alanlar: dict[str, Any], kisit: str) -> None:
    donem = _donem()
    with pytest.raises(IntegrityError, match=rf"{kisit}$"), transaction.atomic():
        OabTerm.objects.filter(pk=donem.pk).update(**alanlar)


@pytest.mark.django_db
def test_ikinci_acik_uyum_satiri_olamaz() -> None:
    donem = _donem()
    ortak = {
        "term": donem,
        "kind": ComplianceKind.EKSIK,
        "subject_type": "oab.GeneralAssembly",
        "subject_id": "1",
        "rule_id": ILAN_KURALI,
    }
    ComplianceItem.objects.create(**ortak)
    with pytest.raises(IntegrityError), transaction.atomic():
        ComplianceItem.objects.create(**ortak)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("alanlar", "kisit"),
    [
        ({"kind": "YOK", "rule_id": ILAN_KURALI}, "ck_complianceitem_kind"),
        ({"kind": ComplianceKind.EKSIK, "rule_id": ""}, "ck_complianceitem_kural_dolu"),
        ({"kind": ComplianceKind.TAKVIM}, "ck_complianceitem_takvim_dolu"),
    ],
)
def test_uyum_satiri_kisitlari(alanlar: dict[str, Any], kisit: str) -> None:
    donem = _donem()
    with pytest.raises(IntegrityError, match=rf"{kisit}$"), transaction.atomic():
        ComplianceItem.objects.create(term=donem, **alanlar)


@pytest.mark.django_db
def test_kok_neden_kural_basina_tektir() -> None:
    ortak = {
        "rule_id": ILAN_KURALI,
        "root_cause": "ilan-kaniti:1",
        "text": "Uydurma gerekçe",
        "justified_by_id": iz_yazari.hesap_zorunlu(),
        "justified_at": timezone.now(),
    }
    ComplianceJustification.objects.create(**ortak)
    with pytest.raises(IntegrityError), transaction.atomic():
        ComplianceJustification.objects.create(**ortak)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("alanlar", "kisit"),
    [
        (
            {
                "student_count_snapshot": 120,
                "quorum_base": 16,
                "quorum_multiplier": 4,
                "quorum_required": 63,
            },
            "ck_generalassembly_yeter_sayi",
        ),
        ({"kind": "YOK"}, "ck_generalassembly_kind"),
        ({"status": "YOK"}, "ck_generalassembly_status"),
    ],
)
def test_genel_kurul_kisitlari(alanlar: dict[str, Any], kisit: str) -> None:
    kurul = GeneralAssembly.objects.create(term=_donem(), kind=AssemblyKind.OLAGAN)
    with pytest.raises(IntegrityError, match=rf"{kisit}$"), transaction.atomic():
        GeneralAssembly.objects.filter(pk=kurul.pk).update(**alanlar)


@pytest.mark.django_db
def test_kural_kopyasi_orm_yoluyla_degistirilemez() -> None:
    kopya = _donem().rule_package
    with pytest.raises(ImmutableRecord):
        kopya.save()
    with pytest.raises(ImmutableRecord):
        RulePackage.objects.filter(pk=kopya.pk).update(rev=9)
    with pytest.raises(ImmutableRecord):
        kopya.delete()
    with pytest.raises(ImmutableRecord):
        RulePackage.objects.filter(pk=kopya.pk).delete()


@pytest.mark.django_db
def test_sapma_gerekcesiz_satir_olamaz() -> None:
    donem = _donem()
    with pytest.raises(IntegrityError), transaction.atomic():
        ComplianceItem.objects.create(term=donem, kind=ComplianceKind.SAPMA, rule_id=ILAN_KURALI)


# ============================================================ O2 dönem kilidi


@pytest.mark.django_db
def test_kapanmis_doneme_yazma_reddedilir() -> None:
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGAN)
    kapali = _kapat(donem)
    with pytest.raises(DonemKapali):
        uyum.denetle(ILAN_KURALI, 20, donem=kapali, konu=kurul, tarih=GUN)
    with pytest.raises(DonemKapali):
        genel_kurul_servisi.genel_kurul_olustur(donem=kapali, kind=AssemblyKind.OLAGAN)
    assert not ComplianceItem.objects.exists()


@pytest.mark.django_db
def test_kapanmis_donemde_kapanis_gecisi_ve_yeter_sayi_reddedilir() -> None:
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGAN)
    uyum.denetle(ILAN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    kapali = _kapat(donem)
    gerekceler = {ILAN_KURALI: uyum.Gerekce(metin="Uydurma gerekçe")}
    with pytest.raises(DonemKapali):
        uyum.kapanis_gecisi(kapali, gerekceler=gerekceler, tarih=GUN)
    with pytest.raises(DonemKapali):
        genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert ComplianceItem.objects.get().kind == ComplianceKind.EKSIK
    assert GeneralAssembly.objects.get(pk=kurul.pk).quorum_required is None


@pytest.mark.django_db
def test_bayat_donem_nesnesi_kilidi_asamaz() -> None:
    """Çağıranın elindeki nesne `ACIK` kalsa da kilit veritabanındaki satıra bakar (O2)."""
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGAN)
    uyum.denetle(ILAN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    _kapat(donem)
    assert donem.status == TermStatus.ACIK
    with pytest.raises(DonemKapali):
        uyum.denetle(ILAN_KURALI, 20, donem=donem, konu=kurul, tarih=GUN)
    with pytest.raises(DonemKapali):
        uyum.kapanis_gecisi(
            donem, gerekceler={ILAN_KURALI: uyum.Gerekce(metin="Uydurma")}, tarih=GUN
        )
    with pytest.raises(DonemKapali):
        genel_kurul_servisi.genel_kurul_olustur(donem=donem, kind=AssemblyKind.OLAGAN)
    satir = ComplianceItem.objects.get()
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.EKSIK, None)
    assert GeneralAssembly.objects.count() == 1


@pytest.mark.django_db
def test_kapanmis_donemde_beyaz_listedeki_eksik_kapanir_ve_ayri_iz_yazar() -> None:
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGAN)
    satir = uyum.denetle(ILAN_KURALI, donem=donem, konu=kurul, tarih=GUN).satir
    assert satir is not None
    _kapat(donem)
    with pytest.raises(DonemKapali):
        uyum.eksik_kapat(satir)
    kapanan = uyum.eksik_kapat(satir, beyaz_liste=True)
    assert kapanan.resolved_at is not None
    iz = AuditTrail.objects.filter(model="oab.ComplianceItem", label=AuditLabel.KAPALI_DONEM)
    assert iz.count() == 1
    assert iz.get().compliance_item_id == kapanan.pk


@pytest.mark.django_db
def test_kapanmis_donemde_beyaz_liste_sapmayi_kapatmaz() -> None:
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGAN)
    satir = uyum.denetle(
        ILAN_KURALI,
        3,
        donem=donem,
        konu=kurul,
        tarih=GUN,
        gerekce=uyum.Gerekce(metin="Uydurma gerekçe"),
    ).satir
    assert satir is not None
    _kapat(donem)
    with pytest.raises(ValueError, match="eksik"):
        uyum.eksik_kapat(satir, beyaz_liste=True)


@pytest.mark.django_db
def test_hazirlik_donemine_yalniz_genel_kurul_hazirligi_yazilir() -> None:
    donem = _donem()
    hazirlik = OabTerm.objects.create(
        name="hazırlık",
        school_year=donem.school_year,
        rule_package=donem.rule_package,
        status=TermStatus.HAZIRLIK,
    )
    kurul = GeneralAssembly.objects.create(term=hazirlik, kind=AssemblyKind.OLAGAN)
    with pytest.raises(DonemYazilamaz):
        uyum.denetle(ILAN_KURALI, 20, donem=hazirlik, konu=kurul, tarih=GUN)
    sonuc = uyum.denetle(
        ILAN_KURALI, 20, donem=hazirlik, konu=kurul, tarih=GUN, hazirlik_yazimi=True
    )
    assert sonuc.sonuc["durum"] == "uygun"


@pytest.mark.django_db
def test_iptal_donemine_yazilamaz() -> None:
    donem = _donem()
    iptal = OabTerm.objects.create(
        name="iptal",
        school_year=donem.school_year,
        rule_package=donem.rule_package,
        status=TermStatus.IPTAL,
    )
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGAN)
    with pytest.raises(DonemYazilamaz):
        uyum.denetle(ILAN_KURALI, 20, donem=iptal, konu=kurul, tarih=GUN, hazirlik_yazimi=True)


@pytest.mark.django_db
def test_kural_kopyasi_bozulursa_donem_salt_okur_acilir() -> None:
    """D7 dönem kolu: okuma açık, yazma kapalı."""
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGAN)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE oab_rulepackage SET content_sha256 = %s WHERE id = %s",
            ["0" * 64, donem.rule_package_id],
        )
    donem = OabTerm.objects.get(pk=donem.pk)
    assert not donem_kilidi.kural_kopyasi_tutuyor(donem)
    with pytest.raises(DonemSaltOkur):
        uyum.denetle(ILAN_KURALI, 20, donem=donem, konu=kurul, tarih=GUN)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE oab_rulepackage SET content = json_set(content, '$.bozuk', 1.5) WHERE id = %s",
        "UPDATE oab_rulepackage SET content = '\"bozuk\"' WHERE id = %s",
        "UPDATE oab_rulepackage SET content = '[1, 2]' WHERE id = %s",
        "UPDATE oab_rulepackage SET content = '{\"kurallar\": [' WHERE id = %s",
    ],
    ids=["kayan-nokta", "json-dizesi", "liste", "yarim-json"],
)
def test_kanonik_bicime_girmeyen_kopyada_okuma_acik_yazma_kapali(sql: str) -> None:
    """D7: `KanonikHata` 500 olmaz; yarım JSON `JSONField`'dan ham metin olarak gelir."""
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGAN)
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA ignore_check_constraints = ON")  # yarım JSON JSON_VALID'e takılır
        try:
            cursor.execute(sql, [donem.rule_package_id])
        finally:
            cursor.execute("PRAGMA ignore_check_constraints = OFF")
    liste = _istemci().get(UC)
    assert liste.status_code == 200, liste.content
    assert [d["kural_kopyasi_tutuyor"] for d in liste.json()] == [False]
    ayrinti = _istemci().get(f"{UC}{donem.pk}/")
    assert ayrinti.status_code == 200, ayrinti.content
    assert ayrinti.json()["kural_kopyasi_tutuyor"] is False
    with pytest.raises(DonemSaltOkur):
        uyum.denetle(ILAN_KURALI, 20, donem=donem, konu=kurul, tarih=GUN)
    assert not ComplianceItem.objects.exists()


# ============================================================ yarım metin


@pytest.mark.django_db
def test_yarim_metin_hesap_basina_tek_sifreli_kayittir() -> None:
    yarim_metin.kaydet("Uydurma yarım metin", baglam="uyum")
    yarim_metin.kaydet("Uydurma ikinci yarım metin", baglam="uyum")
    assert DraftText.objects.count() == 1
    kayit = yarim_metin.oku()
    assert kayit is not None and kayit.text == "Uydurma ikinci yarım metin"
    with connection.cursor() as cursor:
        cursor.execute("SELECT text FROM oab_drafttext")
        ham = cursor.fetchone()[0]
    assert ham != "Uydurma ikinci yarım metin"
    assert crypto.decrypt_with(crypto.active_key() or b"", ham).decode("utf-8") == (
        "Uydurma ikinci yarım metin"
    )


@pytest.mark.django_db
def test_yarim_metin_temizlenir_ve_iz_yazmaz() -> None:
    once = AuditTrail.objects.count()
    yarim_metin.kaydet("Uydurma metin")
    yarim_metin.temizle()
    assert not DraftText.objects.exists()
    yarim_metin.kaydet("Uydurma metin")
    yarim_metin.kaydet("   ")
    assert not DraftText.objects.exists()
    assert AuditTrail.objects.count() == once


# ============================================================ iz bağı


@pytest.mark.django_db
def test_donem_kayitlari_iz_satirina_donemle_yazilir() -> None:
    donem = _donem()
    kurul = genel_kurul_servisi.genel_kurul_olustur(donem=donem, kind=AssemblyKind.OLAGAN)
    assert AuditTrail.objects.get(model="oab.OabTerm").term_id == donem.pk
    assert AuditTrail.objects.get(model="oab.GeneralAssembly").term_id == donem.pk
    uyum.denetle(ILAN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    satir = AuditTrail.objects.get(model="oab.ComplianceItem")
    assert satir.term_id == donem.pk
    assert satir.compliance_item_id == ComplianceItem.objects.get().pk
    assert denetim_izi.zinciri_dogrula() == []


@pytest.mark.django_db
def test_orm_ve_ham_yol_donem_bagini_ayni_kodlar() -> None:
    """Zincirin MAC'i ORM yolunda ve ORM'siz okuyucuda aynı baytlardan kurulur."""
    donem = _donem()
    satir = AuditTrail.objects.get(model="oab.OabTerm")
    ham = satir_izi._iz_satirlari(connection.connection, "seq = ?", (satir.seq,)).fetchone()
    okunan = satir_izi._iz_satiri(ham[1:])
    assert okunan.alanlar == denetim_izi.satir_alanlari(satir)
    assert okunan.alanlar["term"] == str(donem.pk)


def _uyum_iz_satiri() -> AuditTrail:
    donem = _donem()
    kurul = GeneralAssembly.objects.create(term=donem, kind=AssemblyKind.OLAGAN)
    uyum.denetle(ILAN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    return AuditTrail.objects.get(model="oab.ComplianceItem")


@pytest.mark.django_db
def test_orm_ve_ham_yol_uyum_satiri_bagini_ayni_kodlar() -> None:
    satir = _uyum_iz_satiri()
    ham = satir_izi._iz_satirlari(connection.connection, "seq = ?", (satir.seq,)).fetchone()
    okunan = satir_izi._iz_satiri(ham[1:])
    assert okunan.alanlar == denetim_izi.satir_alanlari(satir)
    assert okunan.alanlar["compliance_item"] == str(satir.compliance_item_id)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE okul_audittrail SET compliance_item_id = NULL WHERE seq = %s",
        "UPDATE okul_audittrail SET term_id = NULL WHERE seq = %s",
    ],
    ids=["compliance_item", "term"],
)
def test_zincir_iz_satirinin_baglarini_kapsar(sql: str) -> None:
    """Satırdaki bağ tetikleyici düşürülerek değiştirilse zincir fark eder (§4.6.2)."""
    satir = _uyum_iz_satiri()
    assert denetim_izi.zinciri_dogrula() == []
    with connection.cursor() as cursor:
        cursor.execute("DROP TRIGGER okul_audittrail_no_update")
        cursor.execute(sql, [satir.seq])
    assert denetim_izi.zinciri_dogrula() != []


def test_ham_yol_donem_sutunu_olmayan_goruntuyu_okur() -> None:
    """`okul.0002`'den önceki görüntüde bağ sütunları yoktur: NULL okunur (plan F1c-7)."""
    baglanti = sqlite3.connect(":memory:")
    baglanti.execute(
        'CREATE TABLE okul_audittrail (seq INTEGER, "at" TEXT, actor TEXT, account_id TEXT, '
        'role TEXT, action TEXT, model TEXT, object_id TEXT, changed_fields TEXT, "values" TEXT, '
        "record_mac TEXT, label TEXT, key_mode TEXT, key_ref TEXT, prev_mac TEXT, mac TEXT)"
    )
    baglanti.execute(
        "INSERT INTO okul_audittrail VALUES (1, '2026-11-01 07:30:00', 'SISTEM', NULL, '', 'YEDEK', "
        "'m', '1', '[]', '{}', '', '', 'ACIK', '1', '', 'a')"
    )
    ham = satir_izi._iz_satirlari(baglanti, "seq = ?", (1,)).fetchone()
    assert ham[-2:] == (None, None)
    assert satir_izi._iz_satiri(ham[1:]).alanlar["term"] is None


def _goc(uygulama: str, ad: str) -> Any:
    return MigrationLoader(None).disk_migrations[(uygulama, ad)]


def test_goc_grafigi_oab_okula_okul_oabye_baglidir() -> None:
    """Plan "F1c adımları": `oab.0001 -> okul.0001`, `okul.0002 -> oab.0001`."""
    oab = _goc("oab", "0001_initial")
    okul = _goc("okul", "0002_audittrail_compliance_item_audittrail_term")
    assert ("okul", "0001_initial") in oab.dependencies
    assert ("oab", "0001_initial") in okul.dependencies
    assert ("okul", "0001_initial") in okul.dependencies


def test_okul_0002_tetikleyicileri_yeniden_kurar() -> None:
    operasyonlar = _goc("okul", "0002_audittrail_compliance_item_audittrail_term").operations
    assert isinstance(operasyonlar[0], migrations.RunSQL)
    assert isinstance(operasyonlar[-1], migrations.RunSQL)
    assert all("DROP TRIGGER" in sql for sql in operasyonlar[0].sql)
    assert all("CREATE TRIGGER" in sql for sql in operasyonlar[-1].sql)


@pytest.mark.django_db
def test_goc_sonrasi_denetim_izi_tetikleyicileri_sqlite_masterda() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' "
            "AND tbl_name = 'okul_audittrail' ORDER BY name"
        )
        bulunan = cursor.fetchall()
    assert [ad for ad, _ in bulunan] == ["okul_audittrail_no_delete", "okul_audittrail_no_update"]
    assert all("RAISE(ABORT" in sql for _, sql in bulunan)
    assert "BEFORE DELETE" in bulunan[0][1] and "BEFORE UPDATE" in bulunan[1][1]


# ============================================================ M1 uçları


def _istemci() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_birlik_donemi_ucu_acilis_liste_ve_ayrinti() -> None:
    yil = _yil()
    govde = {"name": "2026-2027 birlik dönemi", "school_year": yil.pk, "start_date": "2026-10-10"}
    yanit = _istemci().post(UC, govde, format="json")
    assert yanit.status_code == 201, yanit.content
    veri = yanit.json()
    assert veri["status"] == "ACIK"
    assert veri["kural_paketi"] == {"paket": "OAB-2023.12", "rev": 1}
    assert veri["kural_kopyasi_tutuyor"] is True

    liste = _istemci().get(UC).json()
    assert [d["id"] for d in liste] == [veri["id"]]
    assert _istemci().get(f"{UC}{veri['id']}/").json()["id"] == veri["id"]

    ikinci = _istemci().post(UC, govde, format="json")
    assert ikinci.status_code == 400
    assert ikinci.json()["code"] == "validation_error"


@pytest.mark.django_db
def test_birlik_donemi_yazmasi_yalniz_program_yoneticisine_acik() -> None:
    """Matris M1: başkan okur, yazamaz."""
    yil = _yil()
    baskan = muhurle(hesap_ac(AccountRole.BASKAN), status=AccountStatus.ACIK)
    oturumu_ac_test(str(baskan.id), tanitici=baskan.login_name, rol=AccountRole.BASKAN.value)
    yanit = _istemci().post(
        UC, {"name": "d", "school_year": yil.pk, "start_date": "2026-10-10"}, format="json"
    )
    assert yanit.status_code == 403
    assert yanit.json()["code"] == "rol_yetkisiz"
    assert _istemci().get(UC).status_code == 200


@pytest.mark.django_db
def test_servis_rol_kapisi() -> None:
    yil = _yil()
    with yazar_olarak(Yazar(hesap_id=None, rol=None)), pytest.raises(RolYetkisiz):
        donemler.create_term(name="d", school_year=yil, start_date=GUN)


# ============================================================ `yazma_kapisi` bekçisi

#: Kural kullanan yazma servisleri: hepsi `yazma_kapisi()` ile başlar (plan "Adım notları").
YAZMA_SERVISLERI = frozenset(
    {
        "donemler.create_term",
        "genel_kurul.genel_kurul_olustur",
        "genel_kurul.yeter_sayiyi_dondur",
        "kural_bagi.revizyon_gecisi",
        "uyum.denetle",
        "uyum.kapanis_gecisi",
    }
)
#: `@transaction.atomic` taşıyıp kural okumayan servisler ve gerekçesi.
_KISI_KURALSIZ = (
    "Birlik kişisi kaydı kural paketi değeri ya da denetimi kullanmaz (koltuk uygunluğu ve seçilme "
    "sayacı organ üyeliğindedir, F1c 5. adım); dönemsiz kayıttır, kilidi kendi durumudur (O2)."
)
KURALSIZ = {
    "uyum.eksik_kapat": "Yalnız satırı kapatır: kural okumaz; dönem kilidi yine denetlenir.",
    "kisiler.create_person": _KISI_KURALSIZ,
    "kisiler.update_person": _KISI_KURALSIZ,
    "kisiler.copy_from_personnel": _KISI_KURALSIZ,
    "kisiler.copy_from_parent": _KISI_KURALSIZ,
}
SERVISLER = Path(__file__).resolve().parents[1] / "services"


def _birinci_govde(islev: ast.FunctionDef) -> ast.stmt:
    govde = islev.body
    return (
        govde[1]
        if isinstance(govde[0], ast.Expr)
        and isinstance(govde[0].value, ast.Constant)
        and isinstance(govde[0].value.value, str)
        else govde[0]
    )


def test_kural_kullanan_yazma_servisleri_yazma_kapisi_ile_baslar() -> None:
    bulunan: set[str] = set()
    for yol in sorted(SERVISLER.glob("*.py")):
        agac = ast.parse(yol.read_text(encoding="utf-8"))
        for dugum in agac.body:
            if not isinstance(dugum, ast.FunctionDef) or not any(
                ast.unparse(d) == "transaction.atomic" for d in dugum.decorator_list
            ):
                continue
            ad = f"{yol.stem}.{dugum.name}"
            if ad in KURALSIZ:
                continue
            bulunan.add(ad)
            ilk = _birinci_govde(dugum)
            assert isinstance(ilk, ast.Expr) and ast.unparse(ilk.value) == "yazma_kapisi()", ad
    assert bulunan == YAZMA_SERVISLERI
