"""Kullanıcılar uçları ve F1b-2 (c1) taşınan maddeleri (plan F1b-2 "Kullanıcılar uçları", "Kendi
hesabı ve ikinci program yöneticisi", "Kapanmış hesap giremez", "Geçici parola"; orkestratör maddeleri
C-1..C-5).

* Uçlar gerçek istekle (ara katmanlar dahil) sürülür: liste (giriş yapamayanlar ve kapalılar dahil),
  seçenekler, ayrıntı ve son girişler, açma, kapama, askıdan çıkarma, parola sıfırlama; eylemleri ve
  nedenleri sunucu hesaplar.
* Kendi hesabı kapatılamaz, kendi parolası buradan sıfırlanamaz; ikinci program yöneticisi açılır.
* Kapanmış hesap giremez: elle kapanış ve üyelik düşmesi (gerçek servis: düşme aynı işlemde
  `ASKIDA (UYELIK_DUSTU)` yazar; plan F1c 7. adım).
* Geçici parola hiçbir yanıtta, günlükte, iz satırında, güvenlik dosyasında ya da iletide yok.
* C-1: kaydı ya da izi tutmayan hesap için rol seçeneklerinde ayrı neden (servisle aynı).
* C-2: uçlar istek boyu işlem açmaz; reddedilen işlemin `BUTUNLUK` satırı yanıttan sonra kalır.
* C-3: denetim izi yazılamazsa 409 `iz_yazilamadi`, sabit Türkçe ileti (eskiden 500).
* C-4: izdeki boşluk ayrı ileti ve ayrı `BUTUNLUK` alanı (`iz_boslugu`); satırın izi eskisi gibi.
* C-5: oturumdaki hesabı isteyen oturum uçları yazar bağlamından okur.
* F-1: mührü tutmayan hesabın reddi de `BUTUNLUK` satırı yazar (hesap işlemleri, oturumdaki parola
  doğrulaması, işlem içi denetimin ertelenen satırı); mühür ve iz kaydın durumundan ve rolünden
  ÖNCE sorulur (program dışından değiştirilmiş durum ya da rol de mühür reddini alır; meşru kapalı
  hesabın iletisi değişmez; Kullanıcılar satırı aynı sırayı izler).
* F-6'nın null kolu: JSON null da boş değerdir, servisin iletisini alır.
* F-5: tanıtıcıda 11 haneli sayı uyarısı; F-6: boş alan servisin iletisini alır; F-7: parola kaydı
  güvenlik dosyasından silinemezse Türkçe ileti (eskiden 500).
* (d0)-1: hesap açmada, parola sıfırlamada ve askıdan çıkarmada güvenlik dosyası yazılamazsa Türkçe
  ileti (eskiden 500); ne yazıldığı, ne geri alındığı ve iletinin dediği çıkış.

Adlar, parolalar ve numaralar uydurmadır; gerçek kişi değildir.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient

from apps.oab.models import OrganMembership
from apps.oab.services import uyelik_gecisleri
from apps.okul import denetim_izi, iz_dogrulama, rol_izinleri
from apps.okul.models import (
    Account,
    AccountRole,
    AccountStatus,
    AuditAction,
    AuditTrail,
    SchoolConfig,
    SuspendReason,
)
from apps.okul.oturum import OTURUM, Yazar, yazar_olarak
from apps.okul.services import app_password, hesap_kurallari, hesaplar, satir_izi
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    YENI_PAROLA,
    durum,
    durum_yaz,
    ham_guncelle,
    ham_satir,
    hesap_ac,
    hesap_uyeligi,
    muhurle,
    sarmal,
    sarmal_kimlikleri,
)
from apps.okul.tests.hesap_ortak import geri_sarilmis as _geri_sarilmis
from apps.okul.tests.hesap_ortak import iz_dolgusu as _dolgu
from apps.okul.tests.hesap_ortak import iz_tetikleyicisiz as _tetikleyicisiz
from apps.okul.tests.hesap_ortak import (
    izde_bosluk_sonra_yoneticiyi_tazele as _izde_bosluk_sonra_yoneticiyi_tazele,
)
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_PAROLA, oturumu_ac_test
from shared import crypto
from shared.exceptions import (
    IZ_YAZILAMADI_KODU,
    IZ_YAZILAMADI_MESAJI,
    ROL_YETKISIZ_MESAJI,
    RolYetkisiz,
    od_exception_handler,
)

pytestmark = pytest.mark.django_db

API = "/api/v1/accounts/"
#: Uydurma geçici parolalar (politikaya uyar; aranacak belirgin dizgiler).
GIZLI_GECICI = "Zarf-Icindeki-Gecici-7!"
GIZLI_SIFIRLAMA = "Zarf-Sifirlama-Parolasi-8?"
#: Var olmayan uydurma hesap kimliği.
YOK_KIMLIK = "9f8e7d6c-5b4a-4c3d-8e2f-1a0b9c8d7e6f"


def _istemci() -> APIClient:
    return APIClient()


def _satir(liste: list[dict[str, Any]], hesap_id: object) -> dict[str, Any]:
    return next(s for s in liste if s["id"] == str(hesap_id))


def _son_seq() -> int:
    bas = denetim_izi.zincir_basi()
    return 0 if bas is None else int(bas[0])


def _butunluk_satirlari(son: int) -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(seq__gt=son, action=AuditAction.BUTUNLUK))


# ============================================================ liste, ayrıntı, seçenekler


def test_liste_butun_hesaplari_eylemleriyle_tasir() -> None:
    """Liste bütün hesapları taşır — giriş yapamayanlar ve kapalılar dahil (plan F1b-2); rol etiketi
    sıra no'suzdur; eylemleri ve nedenleri sunucu servislerin iletileriyle hesaplar."""
    yeni = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")  # PAROLA_YENILENMELI
    dk1 = muhurle(
        hesap_ac(AccountRole.DENETLEME_KURULU, ad="Uydurma Denetçi Bir"),
        status=AccountStatus.ACIK,
        password_changed_at=timezone.now(),
    )
    dk2 = hesap_ac(AccountRole.DENETLEME_KURULU, ad="Uydurma Denetçi İki")
    askida = muhurle(
        hesap_ac(AccountRole.SEKRETER, ad="Uydurma Sekreter"),
        status=AccountStatus.ASKIDA,
        suspend_reason=SuspendReason.UYELIK_DUSTU,
    )
    kapali = hesap_ac(AccountRole.BASKAN, ad="Uydurma Başkan")
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=kapali.id)
    # Hatalı deneme askısı (dosyada) ve parola kaydı olmayan hesap.
    veri = durum()
    for bolum in veri["hesaplar"]:
        if bolum["id"] == str(dk1.id):
            bolum["askida"], bolum["hatali"] = True, 10
    veri["hesaplar"] = [b for b in veri["hesaplar"] if b["id"] != str(dk2.id)]
    durum_yaz(veri)

    yanit = _istemci().get(API)

    assert yanit.status_code == 200, yanit.content
    liste = yanit.json()["hesaplar"]
    assert {s["id"] for s in liste} == {
        TEST_HESAP_ID,
        str(yeni.id),
        str(dk1.id),
        str(dk2.id),
        str(askida.id),
        str(kapali.id),
    }
    assert liste[-1]["id"] == str(kapali.id)  # kapalılar sonda
    kendi = _satir(liste, TEST_HESAP_ID)
    assert kendi["oturumdaki"] is True and kendi["rol_etiketi"] == "Program yöneticisi"
    assert kendi["eylemler"]["kapat"] == {
        "yapilabilir": False,
        "neden": hesaplar._OWN_CLOSE_MESSAGE,
    }
    assert kendi["eylemler"]["parola_sifirla"]["neden"] == hesaplar._OWN_RESET_MESSAGE
    assert kendi["eylemler"]["pusula"]["neden"] == hesaplar._OWN_SLIP_MESSAGE
    assert kendi["giris"] == {"yapabilir": True, "neden": None}

    satir = _satir(liste, yeni.id)
    assert (satir["durum"], satir["durum_etiketi"], satir["ad_soyad"]) == (
        "PAROLA_YENILENMELI",
        "Parola yenilenmeli",
        "Uydurma Muhasip",
    )
    assert satir["eylemler"] == {
        "kapat": {"yapilabilir": True, "neden": None},
        "askidan_cikar": {"yapilabilir": False, "neden": hesaplar._NOT_SUSPENDED_MESSAGE},
        "parola_sifirla": {"yapilabilir": True, "neden": None},
        "pusula": {"yapilabilir": True, "neden": None},
    }
    # Aynı rolde iki hesap: etiket sıra no'suz (sıra no yalnız kilit ekranında).
    assert _satir(liste, dk1.id)["rol_etiketi"] == _satir(liste, dk2.id)["rol_etiketi"]
    assert _satir(liste, dk1.id)["rol_etiketi"] == "Denetleme Kurulu"

    hatali = _satir(liste, dk1.id)
    assert hatali["durum_etiketi"] == "Askıda"
    assert (hatali["askida_nedeni"], hatali["askida_nedeni_etiketi"]) == (
        "HATALI_DENEME",
        "Hatalı parola denemesi",
    )
    assert hatali["eylemler"]["askidan_cikar"]["yapilabilir"] is True
    assert hatali["eylemler"]["parola_sifirla"]["yapilabilir"] is True  # sıfırlama askıyı kaldırır
    assert hatali["giris"]["neden"] == hesaplar._LOGIN_SUSPENDED_MESSAGE

    assert _satir(liste, dk2.id)["giris"]["neden"] == hesaplar._LOGIN_NO_WRAP_MESSAGE

    uyelik = _satir(liste, askida.id)
    assert (uyelik["askida_nedeni"], uyelik["askida_nedeni_etiketi"]) == (
        "UYELIK_DUSTU",
        "Üyelik düştü",
    )
    assert uyelik["eylemler"]["parola_sifirla"]["neden"] == hesaplar._SUSPENDED_RESET_MESSAGE
    assert uyelik["eylemler"]["askidan_cikar"]["yapilabilir"] is True

    kapanmis = _satir(liste, kapali.id)
    assert kapanmis["giris"]["neden"] == hesaplar._LOGIN_CLOSED_MESSAGE
    assert kapanmis["kapanis"] is not None
    for eylem in kapanmis["eylemler"].values():
        assert eylem == {"yapilabilir": False, "neden": hesaplar._CLOSED_MESSAGE}
    assert GECICI_PAROLA not in yanit.content.decode("utf-8")


def test_son_program_yoneticisi_ve_ikinci_program_yoneticisi_satirda() -> None:
    """İkinci program yöneticisi açıkken onun kapatılması açıktır; açılmadan önce oturumdaki tek
    program yöneticisinin satırı kendi hesabı nedenini taşır (son yönetici kuralından önce)."""
    ikinci = hesap_ac(AccountRole.YONETICI, tanitici="yonetici-2", ad="Uydurma İkinci Yönetici")
    liste = _istemci().get(API).json()["hesaplar"]
    assert _satir(liste, ikinci.id)["eylemler"]["kapat"]["yapilabilir"] is True
    assert _satir(liste, ikinci.id)["rol_etiketi"] == "Program yöneticisi"


def test_ayrinti_son_girisleri_ve_ilgili_hesaplari_tasir() -> None:
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    app_password.lock()
    app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    yanit = _istemci().get(f"{API}{hesap.id}/")

    assert yanit.status_code == 200, yanit.content
    ayrinti = yanit.json()
    assert len(ayrinti["son_girisler"]) == 1
    assert ayrinti["acan"]["tanitici"] == "yonetici"
    assert ayrinti["kapatan"] is None and ayrinti["sifirlama"] is None
    assert ayrinti["durum"] == "ACIK" and ayrinti["parola_degisimi"] is not None
    bulunamadi = _istemci().get(f"{API}{YOK_KIMLIK}/")
    assert bulunamadi.status_code == 404
    assert bulunamadi.json()["message"] == "Hesap bulunamadı."


def test_secenekler_rolleri_nedenleri_ve_ikinci_yonetici_bilgisini_verir() -> None:
    hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    yanit = _istemci().get(f"{API}options/")
    assert yanit.status_code == 200, yanit.content
    roller = {r["rol"]: r for r in yanit.json()["roller"]}
    assert list(roller) == list(AccountRole.values)
    assert roller["muhasip"]["acilabilir"] is False
    assert roller["muhasip"]["neden"] == hesaplar._SINGLE_ROLE_MESSAGE
    assert roller["yonetici"] == {
        "rol": "yonetici",
        "rol_etiketi": "Program yöneticisi",
        "acilabilir": True,
        "neden": None,
        "varsayilan_tanitici": "yonetici-2",
        "bilgi": hesaplar.IKINCI_YONETICI_BILGISI,
        "uyelik_gerekli": False,
        "uyelikler": [],
        "organlara_yonlendir": False,
    }
    # Sınır engelinde (tek hesaplı rolde açık hesap) Organlar ekranına yönlendirilmez: çözüm hesabı
    # kapatmaktır, üye girmek değil.
    assert roller["muhasip"]["organlara_yonlendir"] is False
    assert roller["denetleme_kurulu"]["varsayilan_tanitici"] == "dk-1"
    assert all(r["bilgi"] is None for ad, r in roller.items() if ad != "yonetici")


@pytest.mark.parametrize("bozulma", ["muhur", "satir_izi", "iz_boslugu"])
def test_secenekler_kaydi_tutmayan_hesap_icin_ayri_neden_verir(bozulma: str) -> None:
    """Orkestratör maddesi C-1: tek hesaplı roldeki hesabın mührü, satır izi ya da izi (boşluk)
    tutmuyorsa o hesap kapatılamaz; rol seçeneği ayrı neden verir ve hesap açma AYNI iletiyle
    reddeder (tek kural)."""
    muhasip = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    if bozulma == "muhur":
        ham_guncelle(muhasip.id, status=AccountStatus.ACIK)
    elif bozulma == "satir_izi":
        _geri_sarilmis(muhasip)
    else:
        _izde_bosluk_sonra_yoneticiyi_tazele()

    roller = {r["rol"]: r for r in _istemci().get(f"{API}options/").json()["roller"]}

    assert roller["muhasip"]["neden"] == hesaplar._ROLE_RECORD_MESSAGE
    yanit = _istemci().post(
        API,
        {
            "rol": "muhasip",
            "tanitici": "muhasip-2",
            "ad_soyad": "Uydurma Yeni Muhasip",
            "gecici_parola": GECICI_PAROLA,
        },
        format="json",
    )
    assert yanit.status_code == 400, yanit.content
    assert yanit.json()["message"] == hesaplar._ROLE_RECORD_MESSAGE
    # Satır da kaydı tutmayan hesabın nedenini taşır (ileti nedene göre).
    satir = _satir(_istemci().get(API).json()["hesaplar"], muhasip.id)
    beklenen = hesaplar._ROW_GAP_MESSAGE if bozulma == "iz_boslugu" else hesaplar._ROW_SEAL_MESSAGE
    assert satir["kayit_tutuyor"] is False
    assert satir["eylemler"]["kapat"]["neden"] == beklenen
    assert satir["giris"]["neden"] == beklenen


def test_denetleme_kurulu_sinirinda_saglam_hesap_varsa_olagan_neden() -> None:
    """Sınırda yeri tutanlardan biri sağlamsa o kapatılabilir: olağan sınır iletisi."""
    for sira in range(3):
        hesap_ac(AccountRole.DENETLEME_KURULU, ad=f"Uydurma Denetçi {sira}")
    bozuk = Account.objects.filter(role=AccountRole.DENETLEME_KURULU).first()
    assert bozuk is not None
    ham_guncelle(bozuk.id, status=AccountStatus.ACIK)
    roller = {r["rol"]: r for r in _istemci().get(f"{API}options/").json()["roller"]}
    assert roller["denetleme_kurulu"]["neden"] == hesaplar._AUDIT_BOARD_LIMIT_MESSAGE


# ============================================================ yazma uçları


def test_hesap_acma_ucu_ve_ikinci_program_yoneticisi() -> None:
    yanit = _istemci().post(
        API,
        {
            "rol": "baskan",
            "tanitici": "baskan",
            "ad_soyad": "Uydurma Örnekkaya",
            "gecici_parola": GIZLI_GECICI,
            "uyelik": hesap_uyeligi(AccountRole.BASKAN),
        },
        format="json",
    )
    assert yanit.status_code == 201, yanit.content
    govde = yanit.json()
    assert govde["hesap"]["durum"] == "PAROLA_YENILENMELI"
    assert govde["hesap"]["tanitici"] == "baskan"
    assert (govde["uyari"], govde["bilgi"]) == (None, None)

    ikinci = _istemci().post(
        API,
        {
            "rol": "yonetici",
            "tanitici": "uydurmaca",
            "ad_soyad": "Uydurmaca Örnekoğlu",
            "gecici_parola": GIZLI_GECICI,
        },
        format="json",
    )
    assert ikinci.status_code == 201, ikinci.content
    assert ikinci.json()["bilgi"] == hesaplar.IKINCI_YONETICI_BILGISI
    # Tanıtıcı ad-soyaddaki sözcüğü içeriyor: uyarı (engel değil).
    assert ikinci.json()["uyari"] == hesap_kurallari.LOGIN_NAME_WARNING_MESSAGE
    assert Account.objects.filter(role=AccountRole.YONETICI).count() == 2


def test_kapat_askidan_cikar_sifirla_uclari() -> None:
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    hesap = muhurle(hesap, status=AccountStatus.ASKIDA, suspend_reason=SuspendReason.UYELIK_DUSTU)

    askidan = _istemci().post(f"{API}{hesap.id}/unsuspend/")
    assert askidan.status_code == 200, askidan.content
    assert askidan.json()["hesap"]["askida_nedeni"] is None

    sifirla = _istemci().post(
        f"{API}{hesap.id}/reset-password/", {"gecici_parola": GIZLI_SIFIRLAMA}, format="json"
    )
    assert sifirla.status_code == 200, sifirla.content
    assert Account.objects.get(pk=hesap.id).reset_notice_pending is True

    kapat = _istemci().post(f"{API}{hesap.id}/close/")
    assert kapat.status_code == 200, kapat.content
    assert kapat.json()["hesap"]["durum"] == "KAPALI"
    assert str(hesap.id) not in sarmal_kimlikleri()

    yok = _istemci().post(f"{API}{YOK_KIMLIK}/close/")
    assert yok.status_code == 400 and yok.json()["message"] == hesaplar._NOT_FOUND_MESSAGE


@pytest.mark.parametrize("islem", ["kapat", "sifirla"])
def test_kendi_hesabi_kapatilamaz_parolasi_buradan_sifirlanamaz(islem: str) -> None:
    """Plan F1b-2 "Kendi hesabı": servis ve uç reddeder, hiçbir şey yazılmaz (sarmal, satır, iz)."""
    once = (_son_seq(), sarmal(TEST_HESAP_ID), Account.objects.get(pk=TEST_HESAP_ID).seal)
    if islem == "kapat":
        yanit = _istemci().post(f"{API}{TEST_HESAP_ID}/close/")
        ileti = hesaplar._OWN_CLOSE_MESSAGE
    else:
        yanit = _istemci().post(
            f"{API}{TEST_HESAP_ID}/reset-password/", {"gecici_parola": YENI_PAROLA}, format="json"
        )
        ileti = hesaplar._OWN_RESET_MESSAGE
    assert yanit.status_code == 400, yanit.content
    assert yanit.json()["message"] == ileti
    assert (_son_seq(), sarmal(TEST_HESAP_ID), Account.objects.get(pk=TEST_HESAP_ID).seal) == once
    # Servis de (uçsuz) reddeder; tireli olmayan kimlik biçimi de kendi hesabıdır.
    with pytest.raises(hesaplar.AccountServiceError) as hata:
        if islem == "kapat":
            hesaplar.close_account(
                by_hesap_id=TEST_HESAP_ID, hesap_id=TEST_HESAP_ID.replace("-", "")
            )
        else:
            hesaplar.reset_password(
                by_hesap_id=TEST_HESAP_ID,
                hesap_id=TEST_HESAP_ID.replace("-", ""),
                temp_password=YENI_PAROLA,
            )
    assert str(hata.value) == ileti


def test_ikinci_program_yoneticisi_birincinin_parolasini_sifirlayabilir() -> None:
    """Kendi hesabı kuralı yalnız oturumdaki hesabı bağlar: başka bir program yöneticisinin
    parolası sıfırlanır (tasarım §4.4.5 "Yönetici parolası unutuldu: başka yonetici sıfırlar")."""
    ikinci = muhurle(
        hesap_ac(AccountRole.YONETICI, tanitici="yonetici-2", ad="Uydurma İkinci Yönetici"),
        status=AccountStatus.ACIK,
        password_changed_at=timezone.now(),
    )
    oturumu_ac_test(str(ikinci.id), tanitici="yonetici-2", rol="yonetici")
    yanit = _istemci().post(
        f"{API}{TEST_HESAP_ID}/reset-password/", {"gecici_parola": YENI_PAROLA}, format="json"
    )
    assert yanit.status_code == 200, yanit.content
    assert Account.objects.get(pk=TEST_HESAP_ID).status == AccountStatus.PAROLA_YENILENMELI


# ============================================================ kapanmış hesap giremez (§14 F1b)


def _ac_ve_gir(hesap: Account) -> None:
    """Hesap sahibi ilk girişte geçici parolasını yeniler (`ACIK`); oturum program yöneticisine
    döner."""
    app_password.lock()
    app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


@pytest.mark.parametrize("kol", ["elle_kapanis", "uyelik_dusmesi"])
def test_kapanmis_hesap_giremez(kol: str) -> None:
    """Tasarım §14 F1b kapısı "kapanmış hesap giremez" (plan F1b-2): elle kapanış ve üyelik
    düşmesi (gerçek servis, plan F1c 7. adım: `uyelik_gecisleri.uyeligi_dusur` bağlı hesabı aynı
    işlemde `ASKIDA (UYELIK_DUSTU)` yapar; askıdan çıkarılamaz) kollarında hesap Kullanıcılar
    ucundan kapatılır. Giriş açılmaz; parola kaydı (sarmal) dosyaya eski bir kopyadan geri konsa da
    açılmaz; kilit ekranında listelenmez."""
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    _ac_ve_gir(hesap)
    if kol == "uyelik_dusmesi":
        assert hesap.membership_id is not None
        uyelik = OrganMembership.objects.get(pk=hesap.membership_id)
        uyelik_gecisleri.uyeligi_dusur(uyelik, drop_kind="ISTIFA", end_date=date(2026, 11, 2))
        hesap = Account.objects.get(pk=hesap.id)
        assert (hesap.status, hesap.suspend_reason) == (
            AccountStatus.ASKIDA,
            SuspendReason.UYELIK_DUSTU,
        )
        askidan = _istemci().post(f"{API}{hesap.id}/unsuspend/")
        assert askidan.status_code == 400
        assert askidan.json()["message"] == hesaplar._BOND_INVALID_UNSUSPEND_MESSAGE
        app_password.lock()
        with pytest.raises(app_password.AccountSuspended):
            app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    saklanan = sarmal(hesap.id)

    yanit = _istemci().post(f"{API}{hesap.id}/close/")
    assert yanit.status_code == 200, yanit.content
    assert Account.objects.get(pk=hesap.id).status == AccountStatus.KAPALI

    app_password.lock()
    with pytest.raises(app_password.UnlockRefused) as hata:
        app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)
    assert hata.value.code == "iki_depo_tutarsiz"
    assert OTURUM.hesap_id() is None
    assert str(hesap.id) not in {h["id"] for h in hesaplar.lock_screen_accounts()}
    # Eski sarmal dosyaya geri konur (arşivden ya da elde tutulan kopyadan): yine açılmaz.
    veri = durum()
    veri["hesaplar"].append(saklanan)
    durum_yaz(veri)
    with pytest.raises(app_password.UnlockRefused) as hata:
        app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)
    assert hata.value.code == "iki_depo_tutarsiz"
    assert OTURUM.hesap_id() is None and not crypto.is_unlocked()
    assert str(hesap.id) not in {h["id"] for h in hesaplar.lock_screen_accounts()}


# ============================================================ geçici parola gizliliği


def test_gecici_parola_hicbir_yerde_yok(caplog: pytest.LogCaptureFixture) -> None:
    """Plan F1b-2 "Sözleşme": geçici parola hiçbir yanıtta, günlükte, iz satırında, güvenlik
    dosyasında ya da iletide yoktur; sunucu yalnız politikayı denetler (kural iletisi parolayı
    yankılamaz)."""
    caplog.set_level(logging.DEBUG)
    acma = _istemci().post(
        API,
        {
            "rol": "sekreter",
            "tanitici": "sekreter",
            "ad_soyad": "Uydurma Sekreter",
            "gecici_parola": GIZLI_GECICI,
            "uyelik": hesap_uyeligi(AccountRole.SEKRETER),
        },
        format="json",
    )
    assert acma.status_code == 201, acma.content
    kimlik = acma.json()["hesap"]["id"]
    sifirlama = _istemci().post(
        f"{API}{kimlik}/reset-password/", {"gecici_parola": GIZLI_SIFIRLAMA}, format="json"
    )
    assert sifirlama.status_code == 200, sifirlama.content
    zayif = "Kisa-1a"  # politikaya uymaz (8 karakterden kısa)
    ret = _istemci().post(f"{API}{kimlik}/reset-password/", {"gecici_parola": zayif}, format="json")
    assert ret.status_code == 400
    assert ret.json()["message"] == "Parola en az 8 karakter olmalıdır."
    with pytest.raises(hesaplar.AccountServiceError) as hata:
        hesaplar.reset_password(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=zayif)

    yanitlar = b"".join(y.content for y in (acma, sifirlama, ret))
    iz = json.dumps(list(AuditTrail.objects.values()), default=str, ensure_ascii=False).encode(
        "utf-8"
    )
    dosya = app_password.state_path().read_bytes()
    for parola in (GIZLI_GECICI, GIZLI_SIFIRLAMA, zayif):
        for yer, metin in (
            ("yanit", yanitlar),
            ("iz", iz),
            ("dosya", dosya),
            ("gunluk", caplog.text.encode("utf-8")),
            ("ileti", str(hata.value).encode("utf-8")),
        ):
            assert parola.encode("utf-8") not in metin, yer
    # Politika gerçekten denetlendi: sıfırlanan parola hesabı açar (sarmalda, düz metin yok).
    app_password.lock()
    with pytest.raises(app_password.PasswordRenewalRequired):
        app_password.unlock(hesap_id=kimlik, password=GIZLI_SIFIRLAMA)


# ============================================================ rol ve yetki kapısı


@pytest.mark.parametrize("rol", [r for r in rol_izinleri.ROLLER if r != "yonetici"])
def test_kullanicilar_yalniz_program_yoneticisine_acik(rol: str) -> None:
    """Rol kapısı: öteki her rolde liste, seçenekler ve yazmalar 403 `rol_yetkisiz`."""
    oturumu_ac_test("0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", tanitici=rol, rol=rol)
    istemci = _istemci()
    for yanit in (
        istemci.get(API),
        istemci.get(f"{API}options/"),
        istemci.get(f"{API}{TEST_HESAP_ID}/"),
        istemci.post(API, {}, format="json"),
        istemci.post(f"{API}{TEST_HESAP_ID}/close/"),
        istemci.post(f"{API}{TEST_HESAP_ID}/handover-slip/"),
    ):
        assert yanit.status_code == 403
        assert yanit.json()["code"] == "rol_yetkisiz"


def test_okuma_servisleri_de_yetki_kapisina_sorar() -> None:
    """Derin savunma: rol kapısının ardından okuma servisleri de hesap yönetimi yetkisini sorar
    (hesap sahibinin adı kişisel veridir)."""
    muhasip = Yazar(hesap_id="0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", rol="muhasip")
    for islev in (
        hesaplar.kullanici_listesi,
        hesaplar.kullanici_secenekleri,
        lambda: hesaplar.kullanici_ayrintisi(TEST_HESAP_ID),
        lambda: hesaplar.kullanici_satiri(TEST_HESAP_ID),
    ):
        with yazar_olarak(muhasip), pytest.raises(RolYetkisiz):
            islev()


# ============================================================ C-2: istek boyu işlem yok


def test_ayarlarda_istek_boyu_islem_yok() -> None:
    """Orkestratör maddesi C-2: `ATOMIC_REQUESTS` açılırsa reddin `BUTUNLUK` satırı yanıtla birlikte
    geri sarılırdı."""
    for ayar in settings.DATABASES.values():
        assert not ayar.get("ATOMIC_REQUESTS", False)


#: Program dışından kapatılmış gibi yazılan satırın kapanış anı (ham SQL; mühür yenilenmez).
HAM_KAPANIS = "2026-11-03 09:00:00.000000"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("bozulma", ["satir_izi", "muhur", "durum"])
@pytest.mark.parametrize("uc", ["acma", "kapat", "askidan_cikar", "sifirla", "pusula"])
def test_reddedilen_islem_butunluk_satirini_birakir(uc: str, bozulma: str) -> None:
    """Orkestratör maddeleri C-2 ve F-1 (otomatik commit kipinde, üretimdeki gibi): işlem gören
    hesabın satırı eski kopyaya geri sarılmıştır ya da program dışından değiştirilmiştir (mühür;
    kapama, askıdan çıkarma, sıfırlama, teslim pusulası); açmada işlemi yapanın kaydı tutmaz (izden
    ilgisiz bir satır silinmiş ve son kaydı ondan eskidir, ya da satırı program dışından
    değiştirilmiştir). Uç 409 `hesap_muhru_tutmadi` döner; reddin `BUTUNLUK` satırı yanıttan SONRA
    da kalır (alan: satırın izi `kayit_mac`, boşluk `iz_boslugu`, mühür `seal` — mühür kolu da
    yazar, F-1); satır değişmez; pusulada `BASIM` satırı da yoktur.

    `durum` kolu (bağımsız denetim bulgusu, F-1'in tutarlılığı): program dışından değiştirilen
    DURUMDUR — işlem gören KAPALI, açmada işlemi yapan askıda gösterilir. Mührü tutmayan satırın
    durumuna güvenilmez: ret olağan "Hesap kapalı…" / "İşlemi yapan hesap açık değil…" (400)
    değil, mühür reddidir (409 ve `seal` satırı)."""
    if uc == "acma":
        hedef = TEST_HESAP_ID
        if bozulma == "muhur":
            ham_guncelle(TEST_HESAP_ID, login_name="program-disi")
            ileti, alan = hesaplar._SEAL_MESSAGE, "seal"
        elif bozulma == "durum":
            ham_guncelle(
                TEST_HESAP_ID,
                status=AccountStatus.ASKIDA,
                suspend_reason=SuspendReason.UYELIK_DUSTU,
            )
            ileti, alan = hesaplar._SEAL_MESSAGE, "seal"
        else:
            dolgu = _dolgu(3)
            _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [dolgu[1]])
            ileti, alan = hesaplar._GAP_MESSAGE, app_password.IZ_BOSLUGU_ALANI
        yol, govde = (
            API,
            {
                "rol": "muhasip",
                "tanitici": "muhasip",
                "ad_soyad": "Uydurma Muhasip",
                "gecici_parola": GECICI_PAROLA,
            },
        )
    else:
        hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
        if uc == "askidan_cikar":
            hesap = muhurle(
                hesap, status=AccountStatus.ASKIDA, suspend_reason=SuspendReason.UYELIK_DUSTU
            )
        if bozulma == "muhur":
            ham_guncelle(hesap.id, login_name="program-disi")
            alan = "seal"
        elif bozulma == "durum":
            ham_guncelle(
                hesap.id, status=AccountStatus.KAPALI, suspend_reason="", closed_at=HAM_KAPANIS
            )
            alan = "seal"
        else:
            hesap = _geri_sarilmis(hesap)
            alan = app_password.KAYIT_MAC_ALANI
        hedef = str(hesap.id)
        ek = {
            "kapat": "close",
            "askidan_cikar": "unsuspend",
            "sifirla": "reset-password",
            "pusula": "handover-slip",
        }[uc]
        yol = f"{API}{hedef}/{ek}/"
        govde = {"gecici_parola": YENI_PAROLA} if uc == "sifirla" else {}
        ileti = hesaplar._SEAL_MESSAGE
    son = _son_seq()
    once = Account.objects.filter(pk=hedef).values().first()

    yanit = _istemci().post(yol, govde, format="json")

    assert yanit.status_code == 409, yanit.content
    assert (yanit.json()["code"], yanit.json()["message"]) == ("hesap_muhru_tutmadi", ileti)
    satirlar = _butunluk_satirlari(son)
    assert [(s.object_id, s.changed_fields) for s in satirlar] == [(hedef, [alan])]
    assert Account.objects.filter(pk=hedef).values().first() == once
    assert Account.objects.filter(role=AccountRole.MUHASIP).count() == (0 if uc == "acma" else 1)
    assert not AuditTrail.objects.filter(seq__gt=son, action=AuditAction.BASIM).exists()


# ============================================================ C-3: denetim izi yazılamadı


def test_iz_yazilamazsa_409_ve_sabit_ileti() -> None:
    """Orkestratör maddesi C-3: oturum içinde zincir başı program dışından bozulursa (sırası BLOB)
    yazma 409 `iz_yazilamadi` alır; ileti sabit ve Türkçedir, yazıcının iç iletisi yankılanmaz;
    hiçbir şey yazılmaz (eskiden 500)."""
    bas = _son_seq()
    _tetikleyicisiz("UPDATE okul_audittrail SET seq = CAST(seq AS BLOB) WHERE seq = %s", [bas])

    yanit = _istemci().put("/api/v1/security/idle-lock/", {"dakika": 15}, format="json")

    assert yanit.status_code == 409, yanit.content
    assert yanit.json() == {
        "code": IZ_YAZILAMADI_KODU,
        "message": IZ_YAZILAMADI_MESAJI,
        "fields": {},
    }
    assert SchoolConfig.load().idle_lock_minutes == 10


def test_iz_yazilamadi_isleyicide_ic_iletiyi_yankilamaz() -> None:
    yanit = od_exception_handler(
        denetim_izi.IzYazilamadi("okul.Deneme için gizli_alan alanının değeri yazılamaz."),
        {"view": None, "args": (), "kwargs": {}, "request": None},
    )
    assert yanit is not None and yanit.status_code == 409
    assert yanit.data == {"code": IZ_YAZILAMADI_KODU, "message": IZ_YAZILAMADI_MESAJI, "fields": {}}
    # Kilitliyken iz yazılamaması `parola_gerekli` kalır (KeyMissingError önce gelir).
    kilitli = od_exception_handler(
        denetim_izi.IzAnahtariBellekteDegil(),
        {"view": None, "args": (), "kwargs": {}, "request": None},
    )
    assert kilitli is not None and kilitli.data["code"] == "parola_gerekli"
    assert ROL_YETKISIZ_MESAJI != IZ_YAZILAMADI_MESAJI


# ============================================================ C-4: izdeki boşluk ayrı ileti


def _ilgisiz_satir_silinmis_muhasip() -> Account:
    """Açık muhasip; ardından izden İLGİSİZ bir satır silinir (muhasibin satırı değişmez);
    program kilitlidir."""
    hesap = muhurle(
        hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip"),
        status=AccountStatus.ACIK,
        password_changed_at=timezone.now(),
    )
    dolgu = _dolgu(3)
    app_password.lock()
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [dolgu[1]])
    return hesap


def test_ilgisiz_satir_silinince_iz_boslugu_iletisi_ve_alani() -> None:
    """Orkestratör maddesi C-4: izden ilgisiz bir satır silinince son kaydı ondan eski hesap
    reddedilir — ama değişen hesap kaydı değil denetim izidir: ileti iz boşluğununkidir, `BUTUNLUK`
    alanı `iz_boslugu`, neden `SILME`; kod, durum ve hatalı deneme sayılmaması aynıdır."""
    hesap = _ilgisiz_satir_silinmis_muhasip()
    son = _son_seq()

    with pytest.raises(app_password.AuditTrailGap) as hata:
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA)

    assert (hata.value.code, hata.value.status_code) == ("hesap_muhru_tutmadi", 409)
    assert str(hata.value) == app_password.IZ_BOSLUGU_MESSAGE
    assert hata.value.neden is satir_izi.IzRetNedeni.SILME
    assert [(s.object_id, s.changed_fields) for s in _butunluk_satirlari(son)] == [
        (str(hesap.id), [app_password.IZ_BOSLUGU_ALANI])
    ]
    assert app_password.wrap_failure_state(hesap.id) == (0, False)


def test_kaydirilan_kendi_satiri_kayma_nedenidir() -> None:
    """Silinen satırdan sonrakiler aşağı kaydırılır (yeniden numaralama); muhasibin KENDİ son iz
    satırı da kayar. Zincir MAC'i bugünkü sırasında tutmaz, eski sırasında tutar: neden kaymadır
    (`satir_izi` "RET NEDENİ"), ileti iz boşluğunun; satırın izi iletisi değil."""
    dolgu = _dolgu(2)
    hesap = muhurle(
        hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip"),
        status=AccountStatus.ACIK,
        password_changed_at=timezone.now(),
    )
    app_password.lock()
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [dolgu[0]])
    kalan = sorted(
        int(s) for s in AuditTrail.objects.filter(seq__gt=dolgu[0]).values_list("seq", flat=True)
    )
    for yeni, eski in enumerate(kalan, start=dolgu[0]):
        _tetikleyicisiz("UPDATE okul_audittrail SET seq = %s WHERE seq = %s", [yeni, eski])

    with pytest.raises(app_password.AuditTrailGap) as hata:
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA)

    assert hata.value.neden is satir_izi.IzRetNedeni.KAYMA
    assert str(hata.value) == app_password.IZ_BOSLUGU_MESSAGE


def test_geri_sarilmis_satir_satir_izi_iletisinde_kalir() -> None:
    """Boşluksuz geri sarma satırın izidir (`SATIR_IZI`): mühür iletisi ve `kayit_mac` alanı
    değişmez (neden karışırsa iki test birden düşer)."""
    hesap = _geri_sarilmis(
        muhurle(
            hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip"),
            status=AccountStatus.ACIK,
            password_changed_at=timezone.now(),
        )
    )
    app_password.lock()
    son = _son_seq()

    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA)

    assert not isinstance(hata.value, app_password.AuditTrailGap)
    assert hata.value.neden is satir_izi.IzRetNedeni.SATIR_IZI
    assert str(hata.value) == app_password._SEAL_MISMATCH_MESSAGE
    assert [s.changed_fields for s in _butunluk_satirlari(son)] == [[app_password.KAYIT_MAC_ALANI]]


def test_islem_icindeki_denetimin_ertelenen_satiri_boslugun_alanini_tasir() -> None:
    """Orkestratör kararı O-4'ün yolu (işlem içinden denetim, `iz_yaz=False`): izde boşluk varsa
    işlem geri alındıktan sonra yazılan `BUTUNLUK` satırının alanı da `iz_boslugu`dur."""
    hesap = _ilgisiz_satir_silinmis_muhasip()
    son = _son_seq()
    with (
        pytest.raises(app_password.AuditTrailGap),
        app_password._ertelenen_butunluk(TEST_DEK),
        transaction.atomic(),
    ):
        app_password._sealed_account(hesap.id, TEST_DEK, iz_yaz=False)
    assert [(s.object_id, s.changed_fields) for s in _butunluk_satirlari(son)] == [
        (str(hesap.id), [app_password.IZ_BOSLUGU_ALANI])
    ]


def test_islem_icindeki_muhur_denetiminin_ertelenen_satiri_muhrun_alanini_tasir() -> None:
    """Orkestratör maddesi F-1, O-4'ün yolu: işlem içinden yapılan mühür denetimi (`iz_yaz=False`)
    satırı İŞLEMİN İÇİNDE yazmaz (geri alınırdı); işlem geri alındıktan sonra `BUTUNLUK` satırı
    alan `seal` ile kendi işleminde yazılır."""
    hesap = muhurle(
        hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip"),
        status=AccountStatus.ACIK,
        password_changed_at=timezone.now(),
    )
    ham_guncelle(hesap.id, login_name="program-disi")
    son = _son_seq()
    with (
        pytest.raises(app_password.AccountSealMismatch) as hata,
        app_password._ertelenen_butunluk(TEST_DEK),
        transaction.atomic(),
    ):
        app_password._sealed_account(hesap.id, TEST_DEK, iz_yaz=False)
    assert not isinstance(hata.value, app_password.AccountRecordStale)
    assert hata.value.alan == "seal" and hata.value.ertelenen is not None
    assert [(s.object_id, s.changed_fields) for s in _butunluk_satirlari(son)] == [
        (str(hesap.id), ["seal"])
    ]


@pytest.mark.parametrize("islem", ["dogrulama", "degistirme"])
def test_oturumdaki_parola_dogrulamasinda_muhur_reddi_butunluk_yazar(islem: str) -> None:
    """Orkestratör maddesi F-1 (oturumdaki parola doğrulaması): oturum açıkken hesap satırı program
    dışından değiştirilirse doğru parola da parola doğrulamasını ve parola değiştirmeyi geçmez;
    ret 409 `hesap_muhru_tutmadi` ve `BUTUNLUK` satırıdır (`SISTEM`, alan `seal`) — satırın izi ve
    sarmal özeti kollarıyla aynı (eskiden mühür kolu satır yazmıyordu). Satır ve sarmal değişmez,
    hatalı deneme sayılmaz."""
    ham_guncelle(TEST_HESAP_ID, login_name="program-disi")
    once = (Account.objects.filter(pk=TEST_HESAP_ID).values().first(), sarmal(TEST_HESAP_ID))
    son = _son_seq()

    with pytest.raises(app_password.AccountSealMismatch) as hata:
        if islem == "dogrulama":
            app_password.verify_password(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
        else:
            app_password.change_password(
                hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
            )

    assert (hata.value.code, hata.value.status_code) == ("hesap_muhru_tutmadi", 409)
    satirlar = list(AuditTrail.objects.filter(seq__gt=son).order_by("seq"))
    assert [(s.action, s.actor, s.object_id, s.changed_fields) for s in satirlar] == [
        (AuditAction.BUTUNLUK, "SISTEM", TEST_HESAP_ID, ["seal"])
    ]
    assert (
        Account.objects.filter(pk=TEST_HESAP_ID).values().first(),
        sarmal(TEST_HESAP_ID),
    ) == once
    assert app_password.wrap_failure_state(TEST_HESAP_ID) == (0, False)


@pytest.mark.django_db(transaction=True)
def test_parola_degistirme_ucunda_muhur_reddi_satiri_kalir() -> None:
    """Orkestratör maddeleri F-1 ve C-2 (otomatik commit kipinde): kendi parolasını değiştirme ucu
    mührü tutmayan oturum hesabında 409 döner; `BUTUNLUK` satırı (alan `seal`) yanıttan sonra kalır."""
    ham_guncelle(TEST_HESAP_ID, login_name="program-disi")
    son = _son_seq()

    yanit = _istemci().post(
        "/api/v1/security/change-password/",
        {"parola": TEST_PAROLA, "yeni_parola": YENI_PAROLA},
        format="json",
    )

    assert yanit.status_code == 409, yanit.content
    assert yanit.json()["code"] == "hesap_muhru_tutmadi"
    assert [(s.object_id, s.changed_fields) for s in _butunluk_satirlari(son)] == [
        (TEST_HESAP_ID, ["seal"])
    ]


@pytest.mark.parametrize("uc", ["kapat", "askidan_cikar", "sifirla", "pusula"])
def test_mesru_kapali_hesapta_ret_kapali_hesap_iletisidir(uc: str) -> None:
    """Sıra değişikliğinin (F-1'in tutarlılığı: mühür ve iz önce, durum en son) meşru yüzü: program
    eliyle kapatılmış hesabın mührü ve izi tutar; ret eskisi gibi 400 "Hesap kapalı…"dır, `BUTUNLUK`
    satırı yazılmaz. Satırın eylemi aynı nedeni söyler."""
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    ek = {
        "kapat": "close",
        "askidan_cikar": "unsuspend",
        "sifirla": "reset-password",
        "pusula": "handover-slip",
    }[uc]
    son = _son_seq()

    yanit = _istemci().post(
        f"{API}{hesap.id}/{ek}/",
        {"gecici_parola": YENI_PAROLA} if uc == "sifirla" else {},
        format="json",
    )

    assert yanit.status_code == 400, yanit.content
    assert yanit.json()["message"] == hesaplar._CLOSED_MESSAGE
    assert _butunluk_satirlari(son) == []
    eylem = {
        "kapat": hesaplar.EYLEM_KAPAT,
        "askidan_cikar": hesaplar.EYLEM_ASKIDAN_CIKAR,
        "sifirla": hesaplar.EYLEM_PAROLA_SIFIRLA,
        "pusula": hesaplar.EYLEM_PUSULA,
    }[uc]
    satir = hesaplar.kullanici_satiri(hesap.id)
    assert satir is not None
    assert satir["eylemler"][eylem]["neden"] == hesaplar._CLOSED_MESSAGE
    assert satir["giris"]["neden"] == hesaplar._LOGIN_CLOSED_MESSAGE


def test_program_disindan_kapatilan_hesabin_satiri_kayit_iletisini_soyler() -> None:
    """Kullanıcılar satırı servisle aynı sırayı izler (`_kullanici_satiri`; kayıt önce, durum en
    son): program dışından KAPALI yapılmış satırın eylemleri ve giriş engeli "Hesap kapalı…"
    değil, kaydı tutmayan hesabın iletisidir."""
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    ham_guncelle(hesap.id, status=AccountStatus.KAPALI, closed_at=HAM_KAPANIS)

    satir = hesaplar.kullanici_satiri(hesap.id)

    assert satir is not None and satir["kayit_tutuyor"] is False
    for eylem, neden in satir["eylemler"].items():
        assert neden == {"yapilabilir": False, "neden": hesaplar._ROW_SEAL_MESSAGE}, eylem
    assert satir["giris"] == {"yapabilir": False, "neden": hesaplar._ROW_SEAL_MESSAGE}


def test_kurtarma_yenilemede_program_disindan_dusurulen_rol_muhur_reddidir() -> None:
    """F-1'in tutarlılığı (oturumdaki parola doğrulaması): kurtarma anahtarının yenilenmesi rolü
    önce mühürsüz okur. Oturumdaki program yöneticisinin rolü program dışından düşürülmüşse ret
    olağan rol reddi (403) değil mühür reddidir: 409 ve `BUTUNLUK` satırı (alan `seal`); parola
    denenmez (hatalı deneme sayılmaz), güvenlik dosyası değişmez. Meşru rol reddi ayrı testtedir
    (`test_yetki_kapisi`)."""
    ham_guncelle(TEST_HESAP_ID, role=AccountRole.MUHASIP)
    once = app_password.state_path().read_bytes()
    son = _son_seq()

    with pytest.raises(app_password.AccountSealMismatch) as hata:
        app_password.renew_recovery_key(hesap_id=TEST_HESAP_ID, password="Yanlis-Parola-9!")

    assert (hata.value.code, hata.value.status_code) == ("hesap_muhru_tutmadi", 409)
    # Kişi zaten oturumdadır: ileti kilit ekranınınki ("giriş açılmadı") değil, işleminkidir.
    assert str(hata.value) == app_password.ISLEMDE_KAYIT_MESSAGE
    assert [(s.object_id, s.changed_fields) for s in _butunluk_satirlari(son)] == [
        (TEST_HESAP_ID, ["seal"])
    ]
    assert app_password.state_path().read_bytes() == once
    assert app_password.wrap_failure_state(TEST_HESAP_ID) == (0, False)


def test_bildirim_gordumu_program_disindan_degisen_durumda_muhur_reddidir() -> None:
    """F-1'in tutarlılığı (işlemi yapan): oturumdaki hesabın durumu program dışından "açık değil"
    yapılmışsa parola yenilenme bildiriminin "Gördüm"ü olağan "İşlemi yapan hesap açık değil…"
    (400) iletisini değil mühür reddini alır: 409 ve `BUTUNLUK` satırı (alan `seal`); bayrak
    yerinde kalır."""
    ham_guncelle(TEST_HESAP_ID, status=AccountStatus.PAROLA_YENILENMELI, reset_notice_pending=True)
    son = _son_seq()

    yanit = _istemci().post("/api/v1/security/integrity/reset-notice/", {}, format="json")

    assert yanit.status_code == 409, yanit.content
    assert yanit.json()["code"] == "hesap_muhru_tutmadi"
    assert [(s.object_id, s.changed_fields) for s in _butunluk_satirlari(son)] == [
        (TEST_HESAP_ID, ["seal"])
    ]
    assert Account.objects.get(pk=TEST_HESAP_ID).reset_notice_pending is True


def test_denetim_karti_iz_boslugunu_ayri_bulgu_olarak_tasir() -> None:
    """DK ve program yöneticisi kartı (`security/integrity/audit/`): satırın `bulgular`'ı
    `iz_boslugu`dur (kartın metni `modules/butunluk`'tadır)."""
    hesap = _ilgisiz_satir_silinmis_muhasip()
    with pytest.raises(app_password.AuditTrailGap):
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA)
    # Program yöneticisinin kaydı da boşluktan eskidir; kart oturumdan bağımsız okunur.
    oturumu_ac_test()
    kartlar = _istemci().get("/api/v1/security/integrity/audit/").json()
    muhurler = [k for k in kartlar["butunluk"] if k["tur"] == "muhur"]
    assert any(
        k["hesap"]["id"] == str(hesap.id) and k["bulgular"] == ["iz_boslugu"] for k in muhurler
    )


# ============================================================ C-5: oturum uçları yazar bağlamından


@pytest.fixture
def baska_oturum(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """İstek sürerken oturum başka hesaba geçmiş gibi: `OTURUM.hesap_id()` başka kimlik verir;
    yazar bağlamı (istek başındaki görüntü) varsayılan program yöneticisidir."""
    baska = "0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f"
    monkeypatch.setattr(OTURUM, "hesap_id", lambda: baska)
    yield baska


def test_oturum_uclari_yazar_baglamindan_okur(
    baska_oturum: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Orkestratör maddesi C-5: kendi parolası, sahipsiz parola kayıtlarının silinmesi ve parola
    yenilenme bildirimi (okuma ve "Gördüm") istek başındaki yazarın hesabıyla çalışır; istek
    ortasındaki hesap değişimi kararı değiştirmez."""
    gorulen: dict[str, object] = {}

    def kaydet(ad: str, alan: str, donus: object = None) -> Any:
        def islev(*_args: Any, **kwargs: Any) -> object:
            gorulen[ad] = kwargs[alan] if alan in kwargs else _args[0]
            return donus

        return islev

    monkeypatch.setattr(app_password, "change_password", kaydet("parola", "hesap_id"))
    monkeypatch.setattr(hesaplar, "remove_orphan_wraps", kaydet("sahipsiz", "by_hesap_id", []))
    monkeypatch.setattr(hesaplar, "acknowledge_reset_notice", kaydet("gordum", "hesap_id", None))
    monkeypatch.setattr(iz_dogrulama, "yenilenme_bildirimi", kaydet("bildirim", "hesap_id"))
    istemci = _istemci()

    istemci.post(
        "/api/v1/security/change-password/",
        {"parola": TEST_PAROLA, "yeni_parola": YENI_PAROLA},
        format="json",
    )
    istemci.post(
        "/api/v1/security/integrity/orphan-wraps/", {"hesaplar": [YOK_KIMLIK]}, format="json"
    )
    istemci.get("/api/v1/security/integrity/reset-notice/")
    istemci.post("/api/v1/security/integrity/reset-notice/")

    assert gorulen == {
        "parola": TEST_HESAP_ID,
        "sahipsiz": TEST_HESAP_ID,
        "gordum": TEST_HESAP_ID,
        "bildirim": TEST_HESAP_ID,
    }
    assert baska_oturum not in gorulen.values()


# ============================================================ F-5: tanıtıcıda 11 haneli sayı


def test_hesap_acma_taniticida_kimlik_numarasina_benzer_sayiyi_uyarir() -> None:
    """Orkestratör maddesi F-5: tanıtıcıda 11 ardışık rakam (T.C. kimlik numarasına benzer) hesap
    açmayı ENGELLEMEZ; yanıtın `uyari`'sı sözlükteki iletidir (ad-soyad uyarısının yolu). Ad-soyad
    uyarısı da varsa kimlik numarası uyarısı verilir. Sayı uydurmadır, sağlaması tutmaz."""
    yanit = _istemci().post(
        API,
        {
            "rol": "sekreter",
            "tanitici": "uydurmaca-12345678901",
            "ad_soyad": "Uydurmaca Örnekoğlu",
            "gecici_parola": GIZLI_GECICI,
            "uyelik": hesap_uyeligi(AccountRole.SEKRETER),
        },
        format="json",
    )
    assert yanit.status_code == 201, yanit.content
    assert yanit.json()["uyari"] == hesap_kurallari.LOGIN_NAME_TCKN_WARNING_MESSAGE
    assert Account.objects.filter(login_name="uydurmaca-12345678901").exists()


# ============================================================ F-6: boş alanın iletisi


@pytest.mark.parametrize(
    ("alan", "ileti"),
    [
        ("rol", hesaplar._ROLE_MESSAGE),
        ("tanitici", hesap_kurallari.LOGIN_NAME_EMPTY_MESSAGE),
        ("ad_soyad", hesap_kurallari.DISPLAY_NAME_EMPTY_MESSAGE),
        ("gecici_parola", hesap_kurallari.PASSWORD_TOO_SHORT_MESSAGE),
    ],
)
@pytest.mark.parametrize("bicim", ["bos", "gonderilmedi", "null"])
def test_hesap_acmada_bos_alan_servisin_iletisini_alir(alan: str, ileti: str, bicim: str) -> None:
    """Orkestratör maddesi F-6: boş, gönderilmemiş ya da null alan DRF'nin genel iletisini ("Bu alan
    boş bırakılmamalı.") değil servisin Türkçe iletisini alır; ileti `message`'tadır, alan sözlüğü
    boştur (servis reddinin biçimi). Hiçbir şey yazılmaz. (`null` kolu bağımsız denetim bulgusudur:
    JSON null da boştur.)"""
    govde: dict[str, Any] = {
        "rol": "muhasip",
        "tanitici": "muhasip",
        "ad_soyad": "Uydurma Muhasip",
        "gecici_parola": GECICI_PAROLA,
    }
    if bicim == "bos":
        govde[alan] = ""
    elif bicim == "null":
        govde[alan] = None
    else:
        del govde[alan]
    son = _son_seq()

    yanit = _istemci().post(API, govde, format="json")

    assert yanit.status_code == 400, yanit.content
    assert yanit.json() == {"code": "validation_error", "message": ileti, "fields": {}}
    assert _son_seq() == son and not Account.objects.filter(role=AccountRole.MUHASIP).exists()


@pytest.mark.parametrize("bicim", ["bos", "gonderilmedi", "null"])
def test_parola_sifirlamada_bos_parola_servisin_iletisini_alir(bicim: str) -> None:
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    govde: dict[str, Any] = {}
    if bicim != "gonderilmedi":
        govde["gecici_parola"] = "" if bicim == "bos" else None
    yanit = _istemci().post(f"{API}{hesap.id}/reset-password/", govde, format="json")
    assert yanit.status_code == 400, yanit.content
    assert yanit.json() == {
        "code": "validation_error",
        "message": hesap_kurallari.PASSWORD_TOO_SHORT_MESSAGE,
        "fields": {},
    }


# ============================================================ F-7: parola kaydı silinemedi


def _sayacli_muhasip() -> Account:
    """Açık muhasip; güvenlik dosyasındaki sarmalında 2 hatalı deneme (silinirken izi düşsün)."""
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    veri = durum()
    for bolum in veri["hesaplar"]:
        if bolum["id"] == str(hesap.id):
            bolum["hatali"] = 2
    durum_yaz(veri)
    return hesap


@pytest.mark.parametrize("adim", ["ana_dosya", "arsiv"])
def test_kapamada_parola_kaydi_silinemezse_turkce_ileti(
    adim: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Orkestratör maddesi F-7: kapamanın dosya adımı yarıda kalırsa uç 500 değil 400
    `validation_error` ve sözlükteki ileti döner (iç ayrıntı yok). Ne yazıldı: hesap KAPALI, `HESAP`
    satırı kalır (veritabanı adımı commit edilmişti). Ne geri alındı: ana dosya yazılamadıysa
    sarmalın `guvenlik.sarmal` satırı da geri alınır, sarmal ana dosyada kalır (kilit açılışındaki
    temizlik siler); yalnız bir arşiv kopyası silinemediyse sarmal ana dosyadan gitmiştir ve satırı
    kalır."""
    hesap = _sayacli_muhasip()
    son = _son_seq()

    if adim == "ana_dosya":

        def yazilamadi(_durum: dict[str, Any]) -> None:
            raise PermissionError("C:/gizli/yol/guvenlik.json kilitli")

        monkeypatch.setattr(app_password, "_write_structural", yazilamadi)
    else:

        def arsiv_kilitli(_idler: set[str]) -> int:
            raise PermissionError("C:/gizli/yol/guvenlik-arsiv.json kilitli")

        monkeypatch.setattr(app_password, "_remove_wraps_from_archives", arsiv_kilitli)

    yanit = _istemci().post(f"{API}{hesap.id}/close/")

    assert yanit.status_code == 400, yanit.content
    assert yanit.json() == {
        "code": "validation_error",
        "message": hesaplar.CLOSE_WRAP_MESSAGE,
        "fields": {},
    }
    assert "gizli" not in yanit.content.decode("utf-8")
    assert Account.objects.get(pk=hesap.id).status == AccountStatus.KAPALI
    yeni = list(AuditTrail.objects.filter(seq__gt=son).order_by("seq"))
    assert [(s.action, s.model, s.object_id) for s in yeni][0] == (
        AuditAction.HESAP,
        "okul.Account",
        str(hesap.id),
    )
    sarmal_satirlari = [s for s in yeni if s.model == denetim_izi.HESAP_SARMALI]
    if adim == "ana_dosya":
        assert sarmal_satirlari == []
        assert str(hesap.id) in sarmal_kimlikleri()
    else:
        assert [(s.object_id, s.values) for s in sarmal_satirlari] == [
            (str(hesap.id), {"hatali": [2, None]})
        ]
        assert str(hesap.id) not in sarmal_kimlikleri()
    # Servis aynı hatayı dosya hatası olarak verir (çağıranlar `OSError` yakalar).
    assert issubclass(hesaplar.ParolaKaydiSilinemedi, OSError)


def test_sahipsiz_parola_kaydi_silinemezse_turkce_ileti(monkeypatch: pytest.MonkeyPatch) -> None:
    """Orkestratör maddesi F-7: sahipsiz parola kaydının silinmesinde ana dosya yazılamazsa uç 400
    `validation_error` ve sözlükteki ileti döner; işlem geri sarılmıştır (iz satırı yok), kayıt
    yerindedir. (Yalnız arşiv kopyası silinemezse silme başarılıdır; `test_denetim_izi`.)"""
    hayalet = "3c5d7e9f-1a2b-4c3d-8e4f-5a6b7c8d9e0f"
    app_password.write_account_wrap(
        data_key=TEST_DEK, hesap_id=hayalet, tanitici="eski-hesap", password=GECICI_PAROLA
    )
    son = _son_seq()

    def yazilamadi(_durum: dict[str, Any]) -> None:
        raise PermissionError("C:/gizli/yol/guvenlik.json kilitli")

    monkeypatch.setattr(app_password, "_write_structural", yazilamadi)

    yanit = _istemci().post(
        "/api/v1/security/integrity/orphan-wraps/", {"hesaplar": [hayalet]}, format="json"
    )

    assert yanit.status_code == 400, yanit.content
    assert yanit.json() == {
        "code": "validation_error",
        "message": hesaplar.ORPHAN_WRAP_MESSAGE,
        "fields": {},
    }
    assert _son_seq() == son
    assert hayalet in sarmal_kimlikleri()


# ============================================================ (d0)-1: güvenlik dosyası yazılamadı


@contextmanager
def _dosya_yazilamaz(monkeypatch: pytest.MonkeyPatch, islev: str) -> Iterator[None]:
    """Blok boyunca güvenlik dosyasını başka bir program tutuyor taklidi (yolu ve işletim sistemi
    iletisini taşıyan hata; yanıta sızmamalı). Yalnız bu yama geri alınır (fikstürlerinki kalır)."""

    def yazilamadi(_durum: dict[str, Any]) -> None:
        raise PermissionError("C:/gizli/yol/guvenlik.json kilitli")

    with monkeypatch.context() as yama:
        yama.setattr(app_password, islev, yazilamadi)
        yield


def _ileti_ve_sizinti(yanit: Any, ileti: str, *gizliler: str) -> None:
    assert yanit.status_code == 400, yanit.content
    assert yanit.json() == {"code": "validation_error", "message": ileti, "fields": {}}
    metin = yanit.content.decode("utf-8")
    assert "gizli" not in metin
    for gizli in gizliler:
        assert gizli not in metin


def _yeni_satirlar(son: int) -> list[tuple[str, str, str]]:
    return [
        (s.action, s.model, s.object_id)
        for s in AuditTrail.objects.filter(seq__gt=son).order_by("seq")
    ]


def test_hesap_acmada_parola_kaydi_yazilamazsa_turkce_ileti(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Orkestratör maddesi (d0)-1: hesap açmanın dosya adımı yarıda kalırsa uç 500 değil 400
    `validation_error` ve sözlükteki ileti döner (iç ayrıntı ve geçici parola yok). İki depo kuralı
    2: satır (`PAROLA_YENILENMELI`) ve `HESAP` satırı yerinde kalır, parola kaydı güvenlik dosyasında
    yoktur — Kullanıcılar satırı girişin nedenini söyler, iki depo kartında görünür; çıkış (iletinin
    dediği) parola sıfırlamasıdır: geçici parolayla açılır."""
    uyelik = hesap_uyeligi(AccountRole.MUHASIP)
    son = _son_seq()
    govde = {
        "rol": "muhasip",
        "tanitici": "muhasip",
        "ad_soyad": "Uydurma Muhasip",
        "gecici_parola": GIZLI_GECICI,
        "uyelik": uyelik,
    }

    with _dosya_yazilamaz(monkeypatch, "_write_structural"):
        yanit = _istemci().post(API, govde, format="json")

    _ileti_ve_sizinti(yanit, hesaplar.OPEN_WRAP_MESSAGE, GIZLI_GECICI)
    hesap = Account.objects.get(role=AccountRole.MUHASIP)
    assert hesap.status == AccountStatus.PAROLA_YENILENMELI
    assert _yeni_satirlar(son) == [(AuditAction.HESAP, "okul.Account", str(hesap.id))]
    assert str(hesap.id) not in sarmal_kimlikleri()

    satir = _satir(_istemci().get(API).json()["hesaplar"], hesap.id)
    assert satir["kayit_tutuyor"] is True
    assert satir["giris"] == {"yapabilir": False, "neden": hesaplar._LOGIN_NO_WRAP_MESSAGE}
    assert satir["eylemler"]["parola_sifirla"] == {"yapilabilir": True, "neden": None}
    assert hesaplar.two_store_differences().rows_without_wrap == [str(hesap.id)]

    sifirla = _istemci().post(
        f"{API}{hesap.id}/reset-password/", {"gecici_parola": GIZLI_SIFIRLAMA}, format="json"
    )
    assert sifirla.status_code == 200, sifirla.content
    app_password.lock()
    acilan = app_password.unlock(
        hesap_id=hesap.id, password=GIZLI_SIFIRLAMA, new_password="Muhasibin-Kendi-Parolasi-5!"
    )
    assert acilan.id == hesap.id


def test_hesap_acmada_dosya_yazildiktan_sonraki_hata_iletiyle_ortulmez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """İleti yalnız parola kaydı dosyaya GİRMEDİYSE doğrudur: hata yazımdan sonra gelirse (kesinti
    testlerinin "süreç öldü" taklidi) kayıt dosyadadır, hata olduğu gibi yükselir (parola
    sıfırlamanın karşılığı `test_sarmal_tazeligi._yazip_dusur`)."""
    gercek = app_password._replace_wrap

    def yazip_dus(durum_: dict[str, Any], yeni_: dict[str, Any]) -> None:
        gercek(durum_, yeni_)
        raise OSError("süreç öldü")

    with monkeypatch.context() as yama:
        yama.setattr(app_password, "_replace_wrap", yazip_dus)
        with pytest.raises(OSError, match="süreç öldü") as hata:
            hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")

    assert not isinstance(hata.value, hesaplar.GuvenlikDosyasiYazilamadi)
    hesap = Account.objects.get(role=AccountRole.MUHASIP)
    assert str(hesap.id) in sarmal_kimlikleri()


def test_parola_sifirlamada_parola_kaydi_yazilamazsa_turkce_ileti(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Orkestratör maddesi (d0)-1: sıfırlamanın dosya adımı yarıda kalırsa 400 ve sözlükteki ileti.
    Ne yazıldı: 1. işlem (durum `PAROLA_YENILENMELI`, sıfırlama izi ve bildirimi, `PAROLA` satırı).
    Ne geri alındı: 2. işlem (asıl özetin `HESAP` satırı, sayacın `guvenlik.sarmal` satırı); güvenlik
    dosyasındaki kayıt (sayaç dahil) değişmedi. Geçici parola açmaz, eski parola yeni parola
    isteyerek açar; sıfırlamayı yinelemek (iletinin dediği) geçici parolayı geçerli kılar."""
    hesap = _sayacli_muhasip()
    once = sarmal(hesap.id)
    son = _son_seq()
    with _dosya_yazilamaz(monkeypatch, "_write_structural"):
        yanit = _istemci().post(
            f"{API}{hesap.id}/reset-password/", {"gecici_parola": GIZLI_SIFIRLAMA}, format="json"
        )

    _ileti_ve_sizinti(yanit, hesaplar.RESET_WRAP_MESSAGE, GIZLI_SIFIRLAMA)
    satir = Account.objects.get(pk=hesap.id)
    assert satir.status == AccountStatus.PAROLA_YENILENMELI
    assert satir.reset_notice_pending is True and satir.reset_at is not None
    assert _yeni_satirlar(son) == [(AuditAction.PAROLA, "okul.Account", str(hesap.id))]
    assert sarmal(hesap.id) == once
    assert app_password._try_unwrap_account(sarmal(hesap.id), durum(), GIZLI_SIFIRLAMA) is None

    app_password.lock()
    with pytest.raises(app_password.PasswordRenewalRequired):
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    yine = _istemci().post(
        f"{API}{hesap.id}/reset-password/", {"gecici_parola": GIZLI_SIFIRLAMA}, format="json"
    )
    assert yine.status_code == 200, yine.content
    app_password.lock()
    acilan = app_password.unlock(
        hesap_id=hesap.id, password=GIZLI_SIFIRLAMA, new_password="Muhasibin-Kendi-Parolasi-5!"
    )
    assert acilan.id == hesap.id


def _askidaki_sekreter(*, veritabaninda: bool) -> Account:
    """Güvenlik dosyasında hatalı deneme askısı (10 deneme) olan sekreter; istenirse veritabanında
    da askıda (üyelik düştü)."""
    hesap = hesap_ac(AccountRole.SEKRETER, ad="Uydurma Sekreter")
    if veritabaninda:
        hesap = muhurle(
            hesap, status=AccountStatus.ASKIDA, suspend_reason=SuspendReason.UYELIK_DUSTU
        )
    veri = durum()
    for bolum in veri["hesaplar"]:
        if bolum["id"] == str(hesap.id):
            bolum["askida"], bolum["hatali"] = True, 10
    durum_yaz(veri)
    return hesap


def test_askidan_cikarmada_dosya_yazilamazsa_veritabani_askisi_kalkar_ileti_soyler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Orkestratör maddesi (d0)-1: veritabanında da askıdaki hesapta dosya adımı yarıda kalırsa 400
    ve sözlükteki ileti. Ne yazıldı: satır (askı kalktı) ve `HESAP` satırı. Ne geri alındı: sayacın
    `guvenlik.sarmal` satırı; dosyadaki hatalı deneme askısı kaldı — satır hâlâ askıda görünür ve
    askıdan çıkarma yapılabilir; yinelemek (iletinin dediği) yalnız dosyayı siler."""
    hesap = _askidaki_sekreter(veritabaninda=True)
    son = _son_seq()
    with _dosya_yazilamaz(monkeypatch, "_write_state"):
        yanit = _istemci().post(f"{API}{hesap.id}/unsuspend/")

    _ileti_ve_sizinti(yanit, hesaplar.UNSUSPEND_WRAP_MESSAGE)
    satir_db = Account.objects.get(pk=hesap.id)
    assert satir_db.status == AccountStatus.PAROLA_YENILENMELI and satir_db.suspend_reason == ""
    assert _yeni_satirlar(son) == [(AuditAction.HESAP, "okul.Account", str(hesap.id))]
    assert app_password.wrap_failure_state(hesap.id) == (10, True)

    satir = _satir(_istemci().get(API).json()["hesaplar"], hesap.id)
    assert satir["askida_nedeni"] == hesaplar.HATALI_DENEME_ASKISI
    assert satir["eylemler"]["askidan_cikar"] == {"yapilabilir": True, "neden": None}
    son = _son_seq()
    yine = _istemci().post(f"{API}{hesap.id}/unsuspend/")
    assert yine.status_code == 200, yine.content
    assert app_password.wrap_failure_state(hesap.id) == (0, False)
    assert _yeni_satirlar(son) == [(AuditAction.HESAP, denetim_izi.HESAP_SARMALI, str(hesap.id))]


def test_askidan_cikarmada_yalniz_dosya_askisi_varsa_hicbir_sey_degismez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Orkestratör maddesi (d0)-1: kaldırılacak veritabanı askısı yoksa ve dosya yazılamazsa hiçbir
    şey değişmez (iz satırı yok, satır ve dosyadaki askı aynı) ve ileti bunu söyler."""
    hesap = _askidaki_sekreter(veritabaninda=False)
    once = ham_satir(hesap.id)
    son = _son_seq()
    with _dosya_yazilamaz(monkeypatch, "_write_state"):
        yanit = _istemci().post(f"{API}{hesap.id}/unsuspend/")

    _ileti_ve_sizinti(yanit, hesaplar.UNSUSPEND_NOTHING_MESSAGE)
    assert _son_seq() == son
    assert ham_satir(hesap.id) == once
    assert app_password.wrap_failure_state(hesap.id) == (10, True)


def test_guvenlik_dosyasi_hatalari_dosya_hatasi_olarak_kalir() -> None:
    """Yeni hata türü dosya hatasıdır (çağıranlar `OSError` yakalar); silme hatası onun alt
    sınıfıdır ve uçta aynı yoldan çevrilir (`views_oturum.guvenlik_hatalari`)."""
    assert issubclass(hesaplar.GuvenlikDosyasiYazilamadi, OSError)
    assert issubclass(hesaplar.ParolaKaydiSilinemedi, hesaplar.GuvenlikDosyasiYazilamadi)


# ============================================================ sözlük


def _sozluk() -> str:
    """`docs/sozluk.md` (yerelde depo kökü, konteynerde `/repo`)."""
    for kok in (Path(__file__).resolve().parents[4], Path("/repo")):
        yol = kok / "docs" / "sozluk.md"
        if yol.is_file():
            return yol.read_text(encoding="utf-8")
    pytest.fail("docs/sozluk.md bulunamadı.")


def test_kullanicilar_ve_iz_iletileri_sozlukte_yazilidir() -> None:
    """Kullanıcıya görünen her metin sözlüğe girer (sözlük §1 "Kullanıcılar (F1b)", "Hesap kaydının
    ve denetim izinin tutmaması (F1b)"): servislerin iletileri, satırın nedenleri ve etiketleri."""
    sozluk = _sozluk()
    iletiler = [
        app_password._SEAL_MISMATCH_MESSAGE,
        app_password.IZ_BOSLUGU_MESSAGE,
        hesaplar._SEAL_MESSAGE,
        hesaplar._GAP_MESSAGE,
        hesaplar._OWN_CLOSE_MESSAGE,
        hesaplar._OWN_RESET_MESSAGE,
        hesaplar._OWN_SLIP_MESSAGE,
        hesaplar._CLOSED_MESSAGE,
        hesaplar._LAST_ADMIN_MESSAGE,
        hesaplar._SUSPENDED_RESET_MESSAGE,
        hesaplar._NOT_SUSPENDED_MESSAGE,
        hesaplar._ROW_SEAL_MESSAGE,
        hesaplar._ROW_GAP_MESSAGE,
        hesaplar._LOGIN_CLOSED_MESSAGE,
        hesaplar._LOGIN_SUSPENDED_MESSAGE,
        hesaplar._LOGIN_NO_WRAP_MESSAGE,
        hesaplar._LOGIN_DIGEST_MESSAGE,
        hesaplar._SINGLE_ROLE_MESSAGE,
        hesaplar._AUDIT_BOARD_LIMIT_MESSAGE,
        hesaplar._ROLE_RECORD_MESSAGE,
        hesaplar.IKINCI_YONETICI_BILGISI,
        hesaplar._NOT_FOUND_MESSAGE,
        hesaplar._LOGIN_NAME_TAKEN_MESSAGE,
        hesaplar._ROLE_MESSAGE,
        IZ_YAZILAMADI_MESAJI,
        *hesaplar._ASKI_ETIKETLERI.values(),
        *(str(etiket) for etiket in AccountStatus.labels),
        # "Yeni hesap" penceresinin (ve kurulumun) tanıtıcı ve ad-soyad iletileri (sözlük §1
        # "Hesap (F1b)"; bağımsız denetim bulgusu).
        hesap_kurallari.LOGIN_NAME_EMPTY_MESSAGE,
        hesap_kurallari.LOGIN_NAME_INVALID_MESSAGE,
        hesap_kurallari.DISPLAY_NAME_EMPTY_MESSAGE,
        hesap_kurallari.DISPLAY_NAME_TOO_LONG_MESSAGE,
        # Orkestratör maddeleri F-5 ve F-7.
        hesap_kurallari.LOGIN_NAME_WARNING_MESSAGE,
        hesap_kurallari.LOGIN_NAME_TCKN_WARNING_MESSAGE,
        hesaplar.CLOSE_WRAP_MESSAGE,
        hesaplar.ORPHAN_WRAP_MESSAGE,
        # Orkestratör maddeleri (d0)-1 ve (d0)-3.
        hesaplar.OPEN_WRAP_MESSAGE,
        hesaplar.RESET_WRAP_MESSAGE,
        hesaplar.UNSUSPEND_WRAP_MESSAGE,
        hesaplar.UNSUSPEND_NOTHING_MESSAGE,
        app_password.ISLEMDE_PAROLA_KAYDI_MESSAGE,
        # Hesap ↔ üyelik bağı (plan F1c 7. adım; bağımsız denetim bulguları).
        hesaplar._BOND_INVALID_UNSUSPEND_MESSAGE,
        hesaplar._BOND_INVALID_RESET_MESSAGE,
        hesaplar._LOGIN_BOND_INVALID_MESSAGE,
        hesaplar._NO_ELIGIBLE_MEMBERSHIP_MESSAGE,
        hesaplar._BOND_RULES_MISSING_MESSAGE,
    ]
    eksik = [ileti for ileti in iletiler if f'**"{ileti}"**' not in sozluk]
    assert eksik == []
    # Geçici parolanın politika iletileri (sözlük §1 "Parola": sunucununkiyle birebir).
    parola = [
        hesap_kurallari.PASSWORD_EDGE_SPACE_MESSAGE,
        hesap_kurallari.PASSWORD_TOO_SHORT_MESSAGE,
        hesap_kurallari.PASSWORD_TOO_LONG_MESSAGE,
    ]
    assert [ileti for ileti in parola if f'"{ileti}"' not in sozluk] == []
