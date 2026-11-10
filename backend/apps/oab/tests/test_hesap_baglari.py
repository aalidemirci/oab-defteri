"""Hesap ↔ üyelik bağı (plan F1c 7. adım; tasarım §4.4.1, §4.4.5, §4.6.1).

* Hesap açma: organ rolünde üyelik zorunlu (YK: seçilmiş + görev; DK: seçilmiş görevdeki asıl;
  devralınan yeter), öteki rollerde verilmez; kişi ve dönem üyelikten gelir; aynı üyeliğe tek açık
  hesap (servis ve DB kısıtı).
* Mühür ve içerik MAC'i bağı kapsar: program dışından değiştirilen bağ girişte ve ORM'siz geri yükleme
  okuyucusunda yakalanır.
* Askı: üyelik düşünce, iptal edilince ya da yönetim kurulunda görev değişince bağlı hesap AYNI işlemde
  `ASKIDA`; askı yazılamazsa üyelik kaydı da geri alınır; kaydı tutmayan hesaba dokunulmaz (durum en
  son: program dışından kapatılmış ya da askıya alınmış satır da `BUTUNLUK` alır); bağı geçersiz
  hesap askıdan çıkarılmaz; Denetleme Kurulunda görev değişimi hesabı askıya almaz.
* Hesap önerileri (kapanış, askıdan çıkarma, yeni hesap) ve "Yeni hesap" penceresinin üyelik seçimi.

Adlar uydurmadır; gerçek kişi değildir.
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from django.db import IntegrityError, connection, transaction
from pytest_django import DjangoCaptureOnCommitCallbacks
from rest_framework.test import APIClient

from apps.oab.models import (
    BoardMeeting,
    MembershipRole,
    MembershipStatus,
    OabTerm,
    OrganMembership,
    SeatType,
    TermStatus,
)
from apps.oab.services import hesap_baglari, uyelik_gecisleri
from apps.oab.tests import uyelik_ortak as o
from apps.okul import denetim_izi
from apps.okul.models import Account, AccountRole, AccountStatus, AuditAction, AuditTrail
from apps.okul.oturum import OTURUM, Yazar, yazar_olarak
from apps.okul.services import app_password, geri_yukleme_yetkisi, hesaplar, satir_izi
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    YENI_PAROLA,
    geri_sarilmis,
    ham_guncelle,
    hesap_ac,
    hesap_uyeligi,
)
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_PAROLA, oturumu_ac_test
from shared import crypto, kanonik
from shared.exceptions import RolYetkisiz

pytestmark = pytest.mark.django_db

API = "/api/v1/accounts/"
GOREV_GUNU = date(2026, 10, 20)


def _ac(rol: str, uyelik: OrganMembership | int | str | None, **alanlar: Any) -> Account:
    return hesaplar.open_account(
        by_hesap_id=TEST_HESAP_ID,
        role=rol,
        tanitici=alanlar.pop("tanitici", hesaplar.default_login_name(rol)),
        display_name=alanlar.pop("ad", "Uydurma Hesap Sahibi"),
        temp_password=GECICI_PAROLA,
        uyelik=getattr(uyelik, "pk", uyelik),
        **alanlar,
    )


def _ret(rol: str, uyelik: OrganMembership | int | str | None, ileti: str, **alanlar: Any) -> None:
    sayi = Account.objects.count()
    with pytest.raises(hesaplar.AccountServiceError) as hata:
        _ac(rol, uyelik, **alanlar)
    assert str(hata.value) == ileti
    assert Account.objects.count() == sayi


def _gorevli(donem: OabTerm, gorev: str) -> OrganMembership:
    return o.devralinan(donem, o.kisi(), role=gorev)


def _hesap(pk: Any) -> Account:
    return Account.objects.get(pk=pk)


# ============================================================ hesap açma


def test_bagli_hesabin_kisi_ve_donemi_uyelikten_gelir_muhur_ve_mac_kapsar() -> None:
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.MUHASIP)
    hesap = _ac(AccountRole.MUHASIP, uyelik)

    assert (hesap.person_id, hesap.membership_id, hesap.term_id) == (
        uyelik.person_id,
        uyelik.pk,
        donem.pk,
    )
    alanlar = hesap.seal_fields()
    assert (alanlar["person"], alanlar["membership"], alanlar["term"]) == (
        str(uyelik.person_id),
        str(uyelik.pk),
        str(donem.pk),
    )
    assert hesap.seal_matches(TEST_DEK)
    assert denetim_izi.kaydi_dogrula(Account, hesap.id) is True
    # Bağsız hâlin mührü başkadır: bağ mühürdedir (tehdit 19).
    bagsiz = dict(alanlar, person=None, membership=None, term=None)
    assert kanonik.hesap_muhru(crypto.account_seal_key(TEST_DEK), bagsiz) != hesap.seal
    # İçerik MAC'i de bağı kapsar (ORM'siz okuyucu aynı değerleri verir).
    connection.ensure_connection()
    ham = satir_izi._hesap_satiri(connection.connection, str(hesap.id))
    assert ham is not None
    ozet = satir_izi.hesap_ozet_alanlari(ham, TEST_DEK)
    assert (ozet["person"], ozet["membership"], ozet["term"]) == (
        str(uyelik.person_id),
        str(uyelik.pk),
        str(donem.pk),
    )


@pytest.mark.parametrize("rol", sorted(hesaplar.ORGAN_ROLLERI))
def test_organ_rolunde_uyeliksiz_hesap_acilmaz(rol: str) -> None:
    _ret(rol, None, hesaplar._BOND_REQUIRED_MESSAGE)


@pytest.mark.parametrize("rol", [AccountRole.YONETICI, AccountRole.MUDUR])
def test_yonetici_ve_mudur_uyelige_baglanmaz(rol: str) -> None:
    uyelik = _gorevli(o.donem(), MembershipRole.MUHASIP)
    _ret(rol, uyelik, hesaplar._BOND_NOT_ALLOWED_MESSAGE)
    _ret(rol, None, hesaplar._BOND_NOT_ALLOWED_MESSAGE, kisi=uyelik.person_id)
    hesap = _ac(rol, None)
    assert (hesap.person_id, hesap.membership_id, hesap.term_id) == (None, None, None)


def test_yonetim_kurulunda_secilmis_ve_gorevli_uye_gerekir() -> None:
    """Tasarım §4.4.1: YK rolünde üyelik `SECILDI` ve görev bölümü yapılmış (görevi rolün görevi)."""
    donem = o.donem()
    gorevsiz = o.secilmis(donem)
    _ret(AccountRole.MUHASIP, gorevsiz, hesap_baglari.GOREV_TUTMUYOR)
    sekreter = _gorevli(donem, MembershipRole.SEKRETER)
    _ret(AccountRole.MUHASIP, sekreter, hesap_baglari.GOREV_TUTMUYOR)
    kurul = o.olaganustu_genel_kurul(donem)
    aday = o.yk_adayi(donem, o.kisi(), kurul)
    _ret(AccountRole.BASKAN, aday, hesap_baglari.SECILMIS_DEGIL)
    dk = o.secilmis(donem, organ="DK", seat_group="VELI")
    _ret(AccountRole.MUHASIP, dk, hesap_baglari.ORGAN_TUTMUYOR)
    _ret(AccountRole.MUHASIP, 999_999, hesap_baglari.UYELIK_YOK)
    _ret(AccountRole.MUHASIP, "abc", hesap_baglari.UYELIK_YOK)
    # Görev bölümünde görevi alan program kaydı da açar.
    o.yk_gorev_bolumu(donem, {MembershipRole.MUHASIP: gorevsiz}, gun=GOREV_GUNU)
    assert _ac(AccountRole.MUHASIP, gorevsiz).membership_id == gorevsiz.pk
    # Devralınan görevli kayıt yeter (§7.9).
    assert sekreter.source == "DEVRALINAN"
    assert _ac(AccountRole.SEKRETER, sekreter).membership_id == sekreter.pk


def test_denetleme_kurulunda_secilmis_gorevdeki_asil_yeter() -> None:
    donem = o.donem()
    veli, ogretmen1, _ = o.dk_kurulu(donem)
    yedek = o.secilmis(
        donem, organ="DK", seat_group="OGRETMEN", seat_type=SeatType.YEDEK, seat_order=1
    )
    _ret(AccountRole.DENETLEME_KURULU, yedek, hesap_baglari.GOREVDEKI_ASIL_DEGIL)
    yk = _gorevli(donem, MembershipRole.SEKRETER)
    _ret(AccountRole.DENETLEME_KURULU, yk, hesap_baglari.ORGAN_TUTMUYOR)
    assert veli.role == MembershipRole.UYE  # görev aranmaz
    assert _ac(AccountRole.DENETLEME_KURULU, veli).membership_id == veli.pk
    assert _ac(AccountRole.DENETLEME_KURULU, ogretmen1).membership_id == ogretmen1.pk


def test_dusmus_uyelige_ve_acik_olmayan_doneme_hesap_acilmaz() -> None:
    donem = o.donem()
    dusen = _gorevli(donem, MembershipRole.MUHASIP)
    uyelik_gecisleri.uyeligi_dusur(dusen, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    _ret(AccountRole.MUHASIP, dusen, hesap_baglari.SECILMIS_DEGIL)
    sekreter = _gorevli(donem, MembershipRole.SEKRETER)
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.KAPANISTA, end_date=date(2027, 9, 30)
    )
    _ret(AccountRole.SEKRETER, sekreter, hesap_baglari.DONEM_ACIK_DEGIL)


def test_kisi_verilirse_uyeligin_kisisi_olmali() -> None:
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.MUHASIP)
    baska = o.kisi()
    _ret(AccountRole.MUHASIP, uyelik, hesaplar._BOND_PERSON_MESSAGE, kisi=baska.pk)
    assert _ac(AccountRole.MUHASIP, uyelik, kisi=uyelik.person_id).person_id == uyelik.person_id


def test_ayni_uyelige_tek_acik_hesap_servis_ve_db_kisiti() -> None:
    """Tasarım §4.6.1: aynı üyeliğe bağlı tek açık hesap; kapalı hesap yeri boşaltır."""
    donem = o.donem()
    veli = o.dk_kurulu(donem)[0]
    ilk = _ac(AccountRole.DENETLEME_KURULU, veli, tanitici="dk-1")
    _ret(AccountRole.DENETLEME_KURULU, veli, hesaplar._MEMBERSHIP_TAKEN_MESSAGE, tanitici="dk-2")
    # DB kısıtı (servis dışı yazım; yarışın son sözü).
    ikinci = Account(
        login_name="dk-9",
        role=AccountRole.DENETLEME_KURULU,
        display_name="Uydurma",
        person_id=veli.person_id,
        membership_id=veli.pk,
        term_id=donem.pk,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        ikinci.save(force_insert=True)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=ilk.id)
    assert _ac(AccountRole.DENETLEME_KURULU, veli, tanitici="dk-2").membership_id == veli.pk


def test_yarista_db_kisitinin_iletisi_uyeligi_soyler(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ön denetim geçilmiş ama işlemde kısıt tutmuş (eşzamanlı açılış): ileti üyeliğinkidir."""
    donem = o.donem()
    veli = o.dk_kurulu(donem)[0]
    _ac(AccountRole.DENETLEME_KURULU, veli, tanitici="dk-1")
    gercek = hesaplar._bagi_coz
    monkeypatch.setattr(
        hesaplar,
        "_bagi_coz",
        lambda rol, uyelik, kisi: hesaplar.HesapBagi(veli.person_id, veli.pk, donem.pk)
        if rol in hesaplar.ORGAN_ROLLERI
        else gercek(rol, uyelik, kisi),
    )
    _ret(AccountRole.DENETLEME_KURULU, veli, hesaplar._MEMBERSHIP_TAKEN_MESSAGE, tanitici="dk-2")


def _tek_seferlik(araya_giren: Any) -> Any:
    """`app_password.wrap_digest`'in yerine: ilk çağrıda (hesap açmanın ön denetiminden sonra,
    satırın işleminden önce) `araya_giren`'i koşar, sonra gerçek işleve devreder."""
    gercek = app_password.wrap_digest
    kostu: list[bool] = []

    def sarmalayici(*a: Any, **k: Any) -> Any:
        if not kostu:
            kostu.append(True)
            araya_giren()
        return gercek(*a, **k)

    return sarmalayici


def test_yarista_dusen_uyelige_hesap_acilmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ön denetimden sonra, satırın işleminden önce üyelik düşer: bağ işlemde yeniden denetlenir
    (modül başlığı "Bağ hesap açmanın işleminin İÇİNDE yeniden denetlenir")."""
    uyelik = _gorevli(o.donem(), MembershipRole.MUHASIP)
    monkeypatch.setattr(
        app_password,
        "wrap_digest",
        _tek_seferlik(
            lambda: uyelik_gecisleri.uyeligi_dusur(
                uyelik, drop_kind="ISTIFA", end_date=date(2026, 11, 2)
            )
        ),
    )
    _ret(AccountRole.MUHASIP, uyelik, hesap_baglari.SECILMIS_DEGIL)
    assert not Account.objects.filter(membership_id=uyelik.pk).exists()


def test_yarista_gorevi_degisen_uyeye_hesap_acilmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ön denetimden sonra, satırın işleminden önce görev başka üyeye geçer: işlemdeki denetim
    reddeder."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(donem, {MembershipRole.MUHASIP: uyeler[0]}, gun=GOREV_GUNU)
    monkeypatch.setattr(
        app_password,
        "wrap_digest",
        _tek_seferlik(
            lambda: o.yk_gorev_bolumu(
                donem, {MembershipRole.MUHASIP: uyeler[1]}, gun=date(2026, 10, 25)
            )
        ),
    )
    _ret(AccountRole.MUHASIP, uyeler[0], hesap_baglari.GOREV_TUTMUYOR)
    assert not Account.objects.filter(membership_id=uyeler[0].pk).exists()


def test_bag_kurali_kayitli_degilse_organ_hesabi_acilmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kural kayıtlı değilse organ rolüne hesap açılmaz ve var olan organ hesabının bağı geçersiz
    sayılır (fail-closed): askıdaki hesap askıdan çıkarılmaz, satırda bağ geçersiz görünür."""
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.MUHASIP)
    acik = _ac(AccountRole.SEKRETER, _gorevli(donem, MembershipRole.SEKRETER))
    with transaction.atomic():  # kurallar kayıtlıyken bağı geçerli askı
        hesaplar.uyelik_askisi(acik, "GOREV_BOLUMU")
    monkeypatch.setattr(hesaplar, "_bag_kurallari", [])
    _ret(AccountRole.MUHASIP, uyelik, hesaplar._BOND_RULES_MISSING_MESSAGE)
    assert hesaplar.bag_gecersizlik_nedeni(_hesap(TEST_HESAP_ID)) is None  # organ rolü değil
    assert hesaplar.bag_gecersizlik_nedeni(_hesap(acik.id)) == "UYELIK_DUSTU"
    with pytest.raises(hesaplar.AccountServiceError) as hata:
        hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=acik.id)
    assert str(hata.value) == hesaplar._BOND_INVALID_UNSUSPEND_MESSAGE
    satir = hesaplar.kullanici_satiri(acik.id)
    assert satir is not None and satir["uyelik_bagi"]["gecerli"] is False
    # "Yeni hesap" penceresinde organ rolleri kuralın yokluğunu söyler.
    roller = {r["rol"]: r for r in hesaplar.kullanici_secenekleri()["roller"]}
    for rol in hesaplar.ORGAN_ROLLERI - {AccountRole.SEKRETER.value}:
        assert (roller[rol]["acilabilir"], roller[rol]["neden"]) == (
            False,
            hesaplar._BOND_RULES_MISSING_MESSAGE,
        ), rol
    assert roller["mudur"]["acilabilir"] is True


# ============================================================ mühür ve ORM'siz okuyucu


@pytest.mark.parametrize("sutun", ["person_id", "membership_id", "term_id"])
def test_muhur_bagin_program_disindan_degismesini_yakalar(sutun: str) -> None:
    """Tehdit 19: bağ mühürdedir. Program dışından değiştirilen bağ (başka üyelik, kişi ya da dönem;
    boşaltma) girişi açmaz (`BUTUNLUK`, alan `seal`). ORM'siz okuyucunun kolu
    `test_geri_yukleme_yetkisi.py::test_orm_siz_okuyucu_program_disindan_degisen_bagi_yakalar`."""
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.MUHASIP)
    baska = _gorevli(donem, MembershipRole.SEKRETER)
    hesap = _ac(AccountRole.MUHASIP, uyelik)
    yeni = {"person_id": baska.person_id, "membership_id": baska.pk, "term_id": None}[sutun]
    ham_guncelle(hesap.id, **{sutun: yeni})

    assert not _hesap(hesap.id).seal_matches(TEST_DEK)
    son = int(AuditTrail.objects.order_by("-seq").values_list("seq", flat=True).first() or 0)
    app_password.lock()
    with pytest.raises(app_password.AccountSealMismatch):
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    butunluk = AuditTrail.objects.filter(seq__gt=son, action=AuditAction.BUTUNLUK).first()
    assert butunluk is not None and butunluk.changed_fields == ["seal"]


def test_orm_siz_muhur_okuyucusu_bicimsiz_bagi_tutmaz_sayar() -> None:
    """Tamsayı yakınlıklı sütuna program dışından yazılmış metin, kesirli sayı ya da bayt dizisi
    ORM'in mühür biçimine çevrilmez: satır mühür tutmamış sayılır (hata yükseltmez)."""
    satir = (
        "3d9e8f701a2b4c3d8e9fa0b1c2d3e4f5",
        "dk-1",
        "denetleme_kurulu",
        "ACIK",
        1,
        2,
        3,
        "2026-10-31 07:15:30",
        None,
        "",
        "",
        "ab" * 32,
    )
    assert geri_yukleme_yetkisi.satirdan_muhur_alanlari(satir)["membership"] == "2"
    for bozuk in ("2", 2.0, b"2", True):
        bicimsiz = satir[:5] + (bozuk,) + satir[6:]
        with pytest.raises(TypeError):
            geri_yukleme_yetkisi.satirdan_muhur_alanlari(bicimsiz)
        assert geri_yukleme_yetkisi.muhurlu_satir_mi(bicimsiz, TEST_DEK) is False


def test_orm_siz_mac_okuyucusu_bicimsiz_bagi_tutmaz_sayar() -> None:
    """`satir_izi`'nin ham çevirisi: ondalık rakam dışı ya da baştaki sıfırlı kimlik `_Bicimsiz`."""
    assert satir_izi._tamsayi_kimlik_metni(b"12") == "12"
    assert satir_izi._tamsayi_kimlik_metni(None) is None
    for bozuk in (b"012", b"-1", b"1.0", b"abc", b"", "12", 12):
        with pytest.raises(satir_izi._Bicimsiz):
            satir_izi._tamsayi_kimlik_metni(bozuk)


def test_bag_sutunlari_olmayan_eski_goruntu_bos_okunur(tmp_path: Path) -> None:
    """`okul.0004`'ten önceki görüntüde bağ sütunları yoktur: iki ORM'siz okuyucu NULL okur, hata
    vermez (plan F1c 7. adım)."""
    db = tmp_path / "eski.sqlite3"
    with closing(sqlite3.connect(db)) as baglanti:
        baglanti.execute(
            "CREATE TABLE okul_account (id char(32), login_name text, role text, status text, "
            "display_name text, suspend_reason text, opened_at text, opened_by_id char(32), "
            "closed_at text, closed_by_id char(32), password_changed_at text, reset_at text, "
            "reset_by_id char(32), reset_kind text, reset_notice_pending bool, "
            "last_login_at text, wrap_digest text, wrap_digest_pending text, seal text)"
        )
        baglanti.execute(
            "INSERT INTO okul_account VALUES ('3d9e8f701a2b4c3d8e9fa0b1c2d3e4f5', 'dk-1', "
            "'denetleme_kurulu', 'ACIK', '', '', '2026-10-31 07:15:30', NULL, NULL, NULL, NULL, "
            "NULL, NULL, '', 0, NULL, '', '', 'ab')"
        )
        assert satir_izi.hesap_bag_sutunlari_var(baglanti) is False
        satir = geri_yukleme_yetkisi.hesap_satiri(baglanti, "3d9e8f701a2b4c3d8e9fa0b1c2d3e4f5")
        alanlar = geri_yukleme_yetkisi.satirdan_muhur_alanlari(satir)
        assert (alanlar["person"], alanlar["membership"], alanlar["term"]) == (None, None, None)
        ham = satir_izi._hesap_satiri(baglanti, "3d9e8f70-1a2b-4c3d-8e9f-a0b1c2d3e4f5")
        assert ham is not None
        ozet = satir_izi.hesap_ozet_alanlari(ham, TEST_DEK)
        assert (ozet["person"], ozet["membership"], ozet["term"]) == (None, None, None)
        assert len(geri_yukleme_yetkisi.hesap_satirlari(baglanti)) == 1


# ============================================================ askı


def _askida(hesap: Account, neden: str) -> None:
    guncel = _hesap(hesap.id)
    assert (guncel.status, guncel.suspend_reason) == (AccountStatus.ASKIDA, neden)
    assert guncel.seal_matches(TEST_DEK)
    assert denetim_izi.kaydi_dogrula(Account, guncel.id) is True


def _hesap_izi(hesap: Account, son: int) -> list[AuditTrail]:
    return list(
        AuditTrail.objects.filter(
            seq__gt=son, model="okul.Account", object_id=str(hesap.id)
        ).order_by("seq")
    )


def _son() -> int:
    return int(AuditTrail.objects.order_by("-seq").values_list("seq", flat=True).first() or 0)


@pytest.mark.parametrize("gecis", ["dusme", "iptal"])
def test_uyelik_dusunce_ya_da_iptal_edilince_hesap_ayni_islemde_askida(gecis: str) -> None:
    """Tasarım §4.4.5: kayıtla aynı işlemde `ASKIDA (UYELIK_DUSTU)`; iz satırının yazarı kaydı yazan
    hesaptır; giriş kapanır; bağı geçersiz hesap askıdan çıkarılmaz, kapatılır."""
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.MUHASIP)
    hesap = _ac(AccountRole.MUHASIP, uyelik)
    son = _son()
    if gecis == "dusme":
        uyelik_gecisleri.uyeligi_dusur(uyelik, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    else:
        uyelik_gecisleri.uyeligi_iptal_et(uyelik, cancel_reason="Uydurma yanlış kayıt.")

    _askida(hesap, "UYELIK_DUSTU")
    (iz,) = _hesap_izi(hesap, son)
    assert (iz.action, iz.account_id, iz.values["status"]) == (
        AuditAction.HESAP,
        uuid.UUID(TEST_HESAP_ID),
        ["PAROLA_YENILENMELI", "ASKIDA"],
    )
    uyelik_izi = AuditTrail.objects.filter(
        seq__gt=son, model="oab.OrganMembership", object_id=str(uyelik.pk)
    ).first()
    assert uyelik_izi is not None and uyelik_izi.seq < iz.seq
    app_password.lock()
    with pytest.raises(app_password.AccountSuspended):
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    with pytest.raises(hesaplar.AccountServiceError) as hata:
        hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    assert str(hata.value) == hesaplar._BOND_INVALID_UNSUSPEND_MESSAGE
    satir = hesaplar.kullanici_satiri(hesap.id)
    assert satir is not None
    assert satir["eylemler"]["askidan_cikar"]["neden"] == hesaplar._BOND_INVALID_UNSUSPEND_MESSAGE
    # Sıfırlama ve giriş nedenleri de bağı söyler (askıdan çıkarma yolu açılmaz).
    assert satir["eylemler"]["parola_sifirla"] == {
        "yapilabilir": False,
        "neden": hesaplar._BOND_INVALID_RESET_MESSAGE,
    }
    assert satir["giris"] == {"yapabilir": False, "neden": hesaplar._LOGIN_BOND_INVALID_MESSAGE}
    with pytest.raises(hesaplar.AccountServiceError) as hata:
        hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
        )
    assert str(hata.value) == hesaplar._BOND_INVALID_RESET_MESSAGE
    assert satir["uyelik_bagi"] == {
        "kisi": uyelik.person_id,
        "uyelik": uyelik.pk,
        "donem": donem.pk,
        "gecerli": False,
    }
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    assert _hesap(hesap.id).status == AccountStatus.KAPALI


def test_yk_gorev_degisince_hesap_askida_dk_gorev_degisimi_askiya_almaz() -> None:
    """Tasarım §4.4.5 "görev değişti": görevi biten (UYE olan) ve başka göreve geçen üyenin hesabı
    `ASKIDA (GOREV_BOLUMU)`; görevi değişmeyenin hesabı açık kalır. Denetleme Kurulunda görev
    (başkan) hesabın koşulu değildir."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(
        donem,
        {
            MembershipRole.MUHASIP: uyeler[0],
            MembershipRole.SEKRETER: uyeler[1],
            MembershipRole.BASKAN: uyeler[3],
        },
        gun=GOREV_GUNU,
    )
    muhasip = _ac(AccountRole.MUHASIP, uyeler[0])
    sekreter = _ac(AccountRole.SEKRETER, uyeler[1])
    baskan = _ac(AccountRole.BASKAN, uyeler[3])
    o.yk_gorev_bolumu(
        donem,
        {MembershipRole.MUHASIP: uyeler[1], MembershipRole.SEKRETER: uyeler[2]},
        gun=date(2026, 10, 25),
    )
    _askida(muhasip, "GOREV_BOLUMU")
    _askida(sekreter, "GOREV_BOLUMU")
    assert _hesap(baskan.id).status == AccountStatus.PAROLA_YENILENMELI
    # Askıdaki eski muhasip hesabı rolün yerini tutar: yeni muhasibe hesap ondan sonra açılır.
    _ret(AccountRole.MUHASIP, uyeler[1], hesaplar._SINGLE_ROLE_MESSAGE, tanitici="muhasip-2")

    dk = o.dk_kurulu(donem)
    dk_hesabi = _ac(AccountRole.DENETLEME_KURULU, dk[1])
    o.dk_gorev_bolumu(donem, dk[1], gun=date(2026, 10, 16))
    o.dk_gorev_bolumu(donem, dk[2], gun=date(2026, 10, 26))
    assert OrganMembership.objects.get(pk=dk[1].pk).role == MembershipRole.UYE
    assert _hesap(dk_hesabi.id).status == AccountStatus.PAROLA_YENILENMELI


@pytest.mark.parametrize("gecis", ["dusme", "gorev_bolumu"])
def test_aski_yazilamazsa_uyelik_kaydi_da_geri_alinir(
    gecis: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(donem, {MembershipRole.MUHASIP: uyeler[0]}, gun=GOREV_GUNU)
    hesap = _ac(AccountRole.MUHASIP, uyeler[0])
    toplanti_sayisi = BoardMeeting.objects.count()

    def bozuk(*_: object, **__: object) -> None:
        raise RuntimeError("uydurma askı hatası")

    monkeypatch.setattr(hesaplar, "uyelik_askisi", bozuk)
    with pytest.raises(RuntimeError, match="uydurma"):
        if gecis == "dusme":
            uyelik_gecisleri.uyeligi_dusur(
                uyeler[0], drop_kind="ISTIFA", end_date=date(2026, 11, 2)
            )
        else:
            o.yk_gorev_bolumu(donem, {MembershipRole.MUHASIP: uyeler[1]}, gun=date(2026, 10, 25))
    guncel = OrganMembership.objects.get(pk=uyeler[0].pk)
    assert (guncel.status, guncel.role) == (MembershipStatus.SECILDI, MembershipRole.MUHASIP)
    assert BoardMeeting.objects.count() == toplanti_sayisi
    assert _hesap(hesap.id).status == AccountStatus.PAROLA_YENILENMELI


@pytest.mark.parametrize(("bozulma", "alan"), [("muhur", "seal"), ("satir_izi", "kayit_mac")])
def test_kaydi_tutmayan_hesaba_aski_dokunmaz_butunluk_satiri_yazilir(
    bozulma: str, alan: str
) -> None:
    """Kaydı ya da izi tutmayan satır yeniden mühürlenmez (değişikliği aklardı); üyelik yine düşer,
    satır olduğu gibi kalır. Olay tek bir `BUTUNLUK` satırıyla izlenir (yazar `SISTEM`; tasarım §4.4.5
    "Hesap kaydı ya da izi tutmadı")."""
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.MUHASIP)
    hesap = _ac(AccountRole.MUHASIP, uyelik)
    if bozulma == "muhur":
        ham_guncelle(hesap.id, login_name="program-disi")
    else:
        geri_sarilmis(hesap)
    once = _hesap(hesap.id)
    son = _son()
    uyelik_gecisleri.uyeligi_dusur(uyelik, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    assert OrganMembership.objects.get(pk=uyelik.pk).status == MembershipStatus.DUSTU
    guncel = _hesap(hesap.id)
    assert (guncel.status, guncel.login_name, guncel.seal) == (
        AccountStatus.PAROLA_YENILENMELI,
        once.login_name,
        once.seal,
    )
    (iz,) = _hesap_izi(hesap, son)
    assert (iz.action, iz.actor, iz.account_id, iz.changed_fields) == (
        AuditAction.BUTUNLUK,
        "SISTEM",
        None,
        [alan],
    )


@pytest.mark.parametrize(
    ("durum", "neden"),
    [(AccountStatus.KAPALI, ""), (AccountStatus.ASKIDA, "UYELIK_DUSTU")],
)
def test_program_disindan_kapatilan_ya_da_askiya_alinan_satir_atlanmaz(
    durum: str, neden: str
) -> None:
    """Durum en son: askı önce satırın mührünü ve izini doğrular, durumu ancak doğrulanmış satırdan
    okur. Program dışından `KAPALI` ya da aynı nedenle `ASKIDA` yapılmış (mührü tutmayan) satır
    sessizce atlanmaz: üyelik yine düşer, satıra dokunulmaz, olay tek bir `BUTUNLUK` satırıyla izlenir
    (yazar `SISTEM`, alan `seal`)."""
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.MUHASIP)
    hesap = _ac(AccountRole.MUHASIP, uyelik)
    kapanis = "2026-11-02 09:00:00" if durum == AccountStatus.KAPALI else None
    ham_guncelle(hesap.id, status=durum, suspend_reason=neden, closed_at=kapanis)
    once = _hesap(hesap.id)
    assert not once.seal_matches(TEST_DEK)
    son = _son()
    uyelik_gecisleri.uyeligi_dusur(uyelik, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    assert OrganMembership.objects.get(pk=uyelik.pk).status == MembershipStatus.DUSTU
    guncel = _hesap(hesap.id)
    assert (guncel.status, guncel.suspend_reason, guncel.seal) == (durum, neden, once.seal)
    (iz,) = _hesap_izi(hesap, son)
    assert (iz.action, iz.actor, iz.account_id, iz.changed_fields) == (
        AuditAction.BUTUNLUK,
        "SISTEM",
        None,
        ["seal"],
    )


def test_mesru_kapali_hesaba_aski_ve_iz_yazilmaz() -> None:
    """Kaydı tutan kapalı hesap (program kapattı) askıya verilir ama dokunulmaz: iz satırı yok."""
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.MUHASIP)
    hesap = _ac(AccountRole.MUHASIP, uyelik)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    son = _son()
    uyelik_gecisleri.uyeligi_dusur(uyelik, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    assert _hesap(hesap.id).status == AccountStatus.KAPALI
    assert _hesap_izi(hesap, son) == []


@contextmanager
def _oturumda(hesap: Account) -> Iterator[None]:
    """Hesabın oturumu ve yazar bağlamı (kaydı yazan organ hesabı); çıkışta varsayılan oturum."""
    oturumu_ac_test(str(hesap.id), tanitici=hesap.login_name, rol=str(hesap.role))
    try:
        with yazar_olarak(Yazar(hesap_id=str(hesap.id), rol=str(hesap.role))):
            yield
    finally:
        oturumu_ac_test()


@pytest.mark.parametrize("gecis", ["gorev_bolumu", "dusme", "iptal"])
def test_oturumdaki_hesap_kendi_askisini_yazinca_oturum_kilitlenir(
    gecis: str, django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks
) -> None:
    """Tasarım §4.4.5 "giriş kapanır": sekreter kendi görevini değiştiren görev bölümünü ya da kendi
    düşmesini, başkan kendi iptalini yazarsa askıya alınan oturumdaki hesaptır; işlem commit edilince
    bekleyen kilit kurulur, sonraki istek 423 alır (`KILIT` satırı `SISTEM`'in)."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(
        donem,
        {MembershipRole.SEKRETER: uyeler[0], MembershipRole.BASKAN: uyeler[1]},
        gun=GOREV_GUNU,
    )
    sekreter = _ac(AccountRole.SEKRETER, uyeler[0])
    baskan = _ac(AccountRole.BASKAN, uyeler[1])
    yazan, uyelik = (baskan, uyeler[1]) if gecis == "iptal" else (sekreter, uyeler[0])
    with _oturumda(yazan):
        with django_capture_on_commit_callbacks(execute=True):
            if gecis == "gorev_bolumu":
                o.yk_gorev_bolumu(
                    donem, {MembershipRole.SEKRETER: uyeler[2]}, gun=date(2026, 10, 25)
                )
            elif gecis == "dusme":
                uyelik_gecisleri.uyeligi_dusur(
                    uyelik, drop_kind="ISTIFA", end_date=date(2026, 11, 2)
                )
            else:
                uyelik_gecisleri.uyeligi_iptal_et(uyelik, cancel_reason="Uydurma yanlış kayıt.")
        assert _hesap(yazan.id).status == AccountStatus.ASKIDA
        assert OTURUM.kilit_bekliyor() is True
        son = _son()
        assert APIClient().get("/api/v1/oab/terms/").status_code == 423
        assert OTURUM.acik_mi() is False
        (kilit,) = AuditTrail.objects.filter(seq__gt=son, action=AuditAction.KILIT)
        assert (kilit.actor, kilit.account_id, kilit.object_id) == ("SISTEM", None, str(yazan.id))


def test_baska_hesabin_ya_da_geri_alinan_askinin_kilidi_kurulmaz(
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    """Askı oturumdaki hesabın değilse oturum sürer; işlem geri alınırsa kilit kurulmaz."""
    donem = o.donem()
    sekreter_uyeligi = _gorevli(donem, MembershipRole.SEKRETER)
    muhasip_uyeligi = _gorevli(donem, MembershipRole.MUHASIP)
    sekreter = _ac(AccountRole.SEKRETER, sekreter_uyeligi)
    muhasip = _ac(AccountRole.MUHASIP, muhasip_uyeligi)
    with _oturumda(sekreter):
        with django_capture_on_commit_callbacks(execute=True) as cagrilar:
            with pytest.raises(RuntimeError, match="uydurma"), transaction.atomic():
                uyelik_gecisleri.uyeligi_dusur(
                    sekreter_uyeligi, drop_kind="ISTIFA", end_date=date(2026, 11, 2)
                )
                raise RuntimeError("uydurma geri alma")
        assert cagrilar == []
        assert _hesap(sekreter.id).status == AccountStatus.PAROLA_YENILENMELI
        with django_capture_on_commit_callbacks(execute=True) as cagrilar:
            uyelik_gecisleri.uyeligi_dusur(
                muhasip_uyeligi, drop_kind="ISTIFA", end_date=date(2026, 11, 2)
            )
        assert len(cagrilar) == 1
        _askida(muhasip, "UYELIK_DUSTU")
        assert OTURUM.kilit_bekliyor() is False and OTURUM.acik_mi() is True
        assert APIClient().get("/api/v1/oab/terms/").status_code == 200


@pytest.mark.django_db(transaction=True)
def test_kendi_dusmesini_yazan_sekreter_yanitini_alir_sonraki_istek_423() -> None:
    """Gerçek işlemle uçtan: askı commit edilince kilit hemen değil, yanıttan sonraki ilk istekte
    uygulanır; düşme ucunun yanıtı (çözülen kişi adı dahil) verilir."""
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.SEKRETER)
    hesap = _ac(AccountRole.SEKRETER, uyelik)
    istemci = APIClient()
    with _oturumda(hesap):
        yanit = istemci.post(
            f"/api/v1/oab/memberships/{uyelik.pk}/drop/",
            {"drop_kind": "ISTIFA", "end_date": "2026-11-02"},
            format="json",
        )
        assert yanit.status_code == 200, yanit.content
        assert (yanit.json()["status"], yanit.json()["person_name"]) == (
            MembershipStatus.DUSTU,
            uyelik.person.full_name,
        )
        assert _hesap(hesap.id).status == AccountStatus.ASKIDA
        sonraki = istemci.get("/api/v1/oab/terms/")
        assert sonraki.status_code == 423
        assert OTURUM.acik_mi() is False


@pytest.mark.django_db(transaction=True)
def test_uyelik_askisi_yalniz_islemin_icinde_yazilir() -> None:
    hesap = hesap_ac(AccountRole.MUHASIP)
    with pytest.raises(RuntimeError):
        hesaplar.uyelik_askisi(hesap, "UYELIK_DUSTU")
    with pytest.raises(ValueError), transaction.atomic():
        hesaplar.uyelik_askisi(hesap, "HATALI_DENEME")
    assert _hesap(hesap.id).status == AccountStatus.PAROLA_YENILENMELI


def test_gecerli_bagli_askidaki_hesap_askidan_cikar() -> None:
    """Bağ geçerliyse (ör. elle yazılmış eski askı) askıdan çıkarma açıktır (F1b davranışı)."""
    hesap = hesap_ac(AccountRole.MUHASIP)
    with transaction.atomic():
        hesaplar.uyelik_askisi(hesap, "GOREV_BOLUMU")
    assert hesaplar.bag_gecersizlik_nedeni(_hesap(hesap.id)) is None
    # Bağ geçerli: F1b'nin askı iletileri (askıdan çıkarılınca giriş açılır, önce askıdan çıkarın).
    satir = hesaplar.kullanici_satiri(hesap.id)
    assert satir is not None
    assert satir["giris"]["neden"] == hesaplar._LOGIN_SUSPENDED_MESSAGE
    assert satir["eylemler"]["parola_sifirla"]["neden"] == hesaplar._SUSPENDED_RESET_MESSAGE
    hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    assert _hesap(hesap.id).status == AccountStatus.PAROLA_YENILENMELI


def test_gorev_bolumu_askisi_dusmede_uyelik_dustu_olur() -> None:
    """Görev değişimiyle askıdaki hesabın üyeliği sonra düşerse askının nedeni `UYELIK_DUSTU`'ya
    çevrilir (yeni `HESAP` satırı; öneri ve Kullanıcılar etiketi bugünkü olayı söyler); düşmeyle
    askıdaki hesap aynı nedenle yeniden yazılmaz."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(donem, {MembershipRole.MUHASIP: uyeler[0]}, gun=GOREV_GUNU)
    hesap = _ac(AccountRole.MUHASIP, uyeler[0])
    o.yk_gorev_bolumu(donem, {MembershipRole.MUHASIP: uyeler[1]}, gun=date(2026, 10, 25))
    _askida(hesap, "GOREV_BOLUMU")
    son = _son()
    uyelik_gecisleri.uyeligi_dusur(uyeler[0], drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    _askida(hesap, "UYELIK_DUSTU")
    (iz,) = _hesap_izi(hesap, son)
    assert (iz.action, iz.values["suspend_reason"]) == (
        AuditAction.HESAP,
        ["GOREV_BOLUMU", "UYELIK_DUSTU"],
    )
    kapat = [o_ for o_ in hesap_baglari.hesap_onerileri() if o_["tur"] == "HESAP_KAPAT"]
    assert kapat == [
        {"tur": "HESAP_KAPAT", "hesap": str(hesap.id), "rol": "muhasip", "neden": "UYELIK_DUSTU"}
    ]
    son = _son()
    with transaction.atomic():
        assert hesaplar.uyelik_askisi(_hesap(hesap.id), "GOREV_BOLUMU") is None
    assert _hesap_izi(hesap, son) == []


# ============================================================ hesap önerileri ve seçim


def test_hesap_onerileri_kisisiz_ve_yalniz_program_yoneticisine() -> None:
    donem = o.donem()
    muhasip = _gorevli(donem, MembershipRole.MUHASIP)
    sekreter = _gorevli(donem, MembershipRole.SEKRETER)
    o.secilmis(donem)  # görevsiz asıl hesap almaz
    veli = o.secilmis(donem, organ="DK", seat_group="VELI")
    hesap = _ac(AccountRole.MUHASIP, muhasip)

    assert hesap_baglari.hesap_onerileri() == [
        {"tur": "HESAP_AC", "rol": "sekreter", "uyelik": sekreter.pk, "kisi": sekreter.person_id},
        {"tur": "HESAP_AC", "rol": "denetleme_kurulu", "uyelik": veli.pk, "kisi": veli.person_id},
    ]
    uyelik_gecisleri.uyeligi_dusur(muhasip, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
    oneriler = hesap_baglari.hesap_onerileri()
    assert oneriler[0] == {
        "tur": "HESAP_KAPAT",
        "hesap": str(hesap.id),
        "rol": "muhasip",
        "neden": "UYELIK_DUSTU",
    }
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    assert [o_["tur"] for o_ in hesap_baglari.hesap_onerileri()] == ["HESAP_AC", "HESAP_AC"]
    with o.rol_olarak(AccountRole.BASKAN), pytest.raises(RolYetkisiz):
        hesap_baglari.hesap_onerileri()


def test_gorev_ayni_uyeye_donunce_kapanis_onerilmez_askidan_cikarilir() -> None:
    """Muhasiplik A'dan B'ye geçer (A'nın hesabı `ASKIDA (GOREV_BOLUMU)`, kapanış önerilir), sonra
    A'ya döner: bağ yeniden geçerlidir. Askı kendiliğinden kalkmaz; öneri listesinde A'nın hesabı için
    kapanış ve muhasibe yeni hesap yoktur, kişisiz `HESAP_ASKIDAN_CIKAR` kalemi vardır; askıdan
    çıkarılınca kalem düşer."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    o.yk_gorev_bolumu(donem, {MembershipRole.MUHASIP: uyeler[0]}, gun=GOREV_GUNU)
    hesap = _ac(AccountRole.MUHASIP, uyeler[0])
    o.yk_gorev_bolumu(donem, {MembershipRole.MUHASIP: uyeler[1]}, gun=date(2026, 10, 25))
    _askida(hesap, "GOREV_BOLUMU")
    kapanis = {
        "tur": "HESAP_KAPAT",
        "hesap": str(hesap.id),
        "rol": "muhasip",
        "neden": "GOREV_BOLUMU",
    }
    assert kapanis in hesap_baglari.hesap_onerileri()

    o.yk_gorev_bolumu(donem, {MembershipRole.MUHASIP: uyeler[0]}, gun=date(2026, 10, 28))
    _askida(hesap, "GOREV_BOLUMU")
    assert hesaplar.bag_gecersizlik_nedeni(_hesap(hesap.id)) is None
    oneriler = hesap_baglari.hesap_onerileri()
    assert [o_ for o_ in oneriler if o_["tur"] == "HESAP_KAPAT"] == []
    assert [o_ for o_ in oneriler if o_["rol"] == "muhasip"] == [
        {"tur": "HESAP_ASKIDAN_CIKAR", "hesap": str(hesap.id), "rol": "muhasip"}
    ]
    hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    assert _hesap(hesap.id).status == AccountStatus.PAROLA_YENILENMELI
    assert [o_ for o_ in hesap_baglari.hesap_onerileri() if o_["rol"] == "muhasip"] == []


def test_askidan_cikar_onerisi_kaydi_tutmayan_satira_yapilmaz() -> None:
    """Bağı geçerli askıdaki hesabın kaydı program dışından değiştirildiyse (askıdan çıkarma onu
    reddederdi) öneri yoktur; satır kaydı tutarken kalem kişisiz kodlardır (ad, tanıtıcı yok)."""
    hesap = hesap_ac(AccountRole.MUHASIP)
    with transaction.atomic():
        hesaplar.uyelik_askisi(hesap, "GOREV_BOLUMU")
    askidan = [o_ for o_ in hesap_baglari.hesap_onerileri() if o_.get("hesap") == str(hesap.id)]
    assert askidan == [{"tur": "HESAP_ASKIDAN_CIKAR", "hesap": str(hesap.id), "rol": "muhasip"}]
    ham_guncelle(hesap.id, login_name="program-disi")
    assert [o_ for o_ in hesap_baglari.hesap_onerileri() if o_.get("hesap") == str(hesap.id)] == []


def test_secenekler_ve_hesap_acma_ucu_uyelik_secimi() -> None:
    """Kullanıcılar uçları: "Yeni hesap" penceresi organ rolünde hesap açılabilecek üyelikleri (kişi
    ve üyelik) verir; açma ucu üyeliği ve isteğe bağlı kişiyi alır; satır bağı taşır."""
    istemci = APIClient()
    # Açık dönem yok: organ rolünde hesap açılabilecek üye yok, rol açılamaz (rol düzeyindeki neden).
    roller = {r["rol"]: r for r in istemci.get(f"{API}options/").json()["roller"]}
    for rol in sorted(hesaplar.ORGAN_ROLLERI):
        assert (roller[rol]["acilabilir"], roller[rol]["neden"], roller[rol]["uyelikler"]) == (
            False,
            hesaplar._NO_ELIGIBLE_MEMBERSHIP_MESSAGE,
            [],
        ), rol
    assert (roller["mudur"]["acilabilir"], roller["yonetici"]["acilabilir"]) == (True, True)
    donem = o.donem()
    uyelik = _gorevli(donem, MembershipRole.MUHASIP)
    roller = {r["rol"]: r for r in istemci.get(f"{API}options/").json()["roller"]}
    assert (roller["muhasip"]["acilabilir"], roller["muhasip"]["neden"]) == (True, None)
    assert roller["muhasip"]["uyelik_gerekli"] is True
    assert roller["muhasip"]["uyelikler"] == [
        {
            "uyelik": uyelik.pk,
            "kisi": uyelik.person_id,
            "ad_soyad": uyelik.person.full_name,
            "organ": "YK",
            "gorev": "MUHASIP",
            "gorev_etiketi": "Muhasip",
            "donem": donem.pk,
        }
    ]
    # Görev bölümü yapılmamış rol (görevli üye yok) açılamaz.
    assert (roller["sekreter"]["acilabilir"], roller["sekreter"]["uyelikler"]) == (False, [])
    assert roller["sekreter"]["neden"] == hesaplar._NO_ELIGIBLE_MEMBERSHIP_MESSAGE
    assert (roller["mudur"]["uyelik_gerekli"], roller["mudur"]["uyelikler"]) == (False, [])
    govde = {
        "rol": "muhasip",
        "tanitici": "muhasip",
        "ad_soyad": "Uydurma Muhasip",
        "gecici_parola": GECICI_PAROLA,
    }
    eksik = istemci.post(API, govde, format="json")
    assert eksik.status_code == 400
    assert eksik.json()["message"] == hesaplar._BOND_REQUIRED_MESSAGE
    yanlis = istemci.post(API, {**govde, "uyelik": uyelik.pk, "kisi": o.kisi().pk}, format="json")
    assert yanlis.json()["message"] == hesaplar._BOND_PERSON_MESSAGE
    yanit = istemci.post(
        API, {**govde, "uyelik": uyelik.pk, "kisi": uyelik.person_id}, format="json"
    )
    assert yanit.status_code == 201, yanit.content
    assert yanit.json()["hesap"]["uyelik_bagi"] == {
        "kisi": uyelik.person_id,
        "uyelik": uyelik.pk,
        "donem": donem.pk,
        "gecerli": True,
    }
    roller = {r["rol"]: r for r in istemci.get(f"{API}options/").json()["roller"]}
    # Sınır nedeni bağ nedeninden önce gelir (hesap açmanın sırası).
    assert (roller["muhasip"]["neden"], roller["muhasip"]["uyelikler"]) == (
        hesaplar._SINGLE_ROLE_MESSAGE,
        [],
    )
    yonetici = next(s for s in istemci.get(API).json()["hesaplar"] if s["id"] == TEST_HESAP_ID)
    assert yonetici["uyelik_bagi"] is None


def test_fabrika_organ_hesabini_uyelige_bagli_acar() -> None:
    """F1b fabrikaları organ rolünde üyelikle kurulur (plan F1c 7. adım): her organ rolünün hesabı
    kurala uyan bir üyeliğe bağlıdır; bağ geçerlidir."""
    for rol in sorted(hesaplar.ORGAN_ROLLERI):
        hesap = hesap_ac(rol, ad="Uydurma Hesap")
        assert hesap.membership_id is not None, rol
        assert hesaplar.bag_gecersizlik_nedeni(hesap) is None, rol
    # Görevi taşıyan üye bağlıysa fabrika onu verir: hesap açma rolün sınırıyla reddeder.
    muhasip = Account.objects.get(role=AccountRole.MUHASIP)
    assert hesap_uyeligi(AccountRole.MUHASIP) == muhasip.membership_id
