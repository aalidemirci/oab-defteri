"""Hesap satırının zaman sütunu program dışından bozulunca (orkestratör maddesi (d0)-2).

SQLite tür denetlemez: `okul_account.opened_at`'e (ya da `closed_at`, `last_login_at`…) metin
düzenleyiciyle biçime uyan ama geçersiz bir an ("2026-02-30 10:00:00"; Django'nun dönüştürücüsü
ValueError yükseltir), yerel saate çevrilemeyen bir uç an (9999'un son saati; OverflowError) ya da
biçimsiz bir değer ("zzz"; ORM None okur) yazılabilir. Eskiden tek bir değer iki depo ve "kaydı
değiştirilmiş görünen hesaplar" kartlarını ("okunamadı"), Kullanıcılar listesini, seçeneklerini ve
ayrıntısını (400, İngilizce iç ileti ya da 500), kilit ekranının hesap listesini (500: kimse
giremezdi), girişi ve hesap işlemlerini (400, İngilizce) ve oturumdaki hesabın parola yenilenme
kartını düşürüyordu. Artık:

* okumalar düşmez (`app_password.hesap_satiri`, `hesap_satirlari`; kilit ekranı ham an okur);
* o hesap KAYDI DEĞİŞTİRİLMİŞ sayılır: mührü (açılış ve kapanış anı mühre girer) ya da satırın izi
  (öteki anlar) tutmaz — Kullanıcılar'da `kayit_tutuyor: false`, iki depo farkında
  `seal_mismatch`; girişi ve hesap işlemi 409 `hesap_muhru_tutmadi` ve `BUTUNLUK` satırıyla
  reddedilir;
* kullanıcıya giden okunamayan an None'dır; öteki hesaplar etkilenmez.

Adlar ve parolalar uydurmadır.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul.models import Account, AccountRole, AccountStatus, AuditAction, AuditTrail
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password, hesaplar
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    UCUNCU_PAROLA,
    YENI_PAROLA,
    ham_guncelle,
    hesap_ac,
    muhurle,
    sarmal_kimlikleri,
)
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_PAROLA

pytestmark = pytest.mark.django_db

#: Program dışından yazılmış anlar: geçersiz (ValueError), yerel saate çevrilemeyen (OverflowError),
#: biçimsiz (ORM None okur).
BOZUK_ANLAR = ["2026-02-30 10:00:00.000000", "9999-12-31 23:59:59.000000", "zzz"]
#: Okuma sırasında ORM'yi düşüren an (yalnız bu yol `hesap_satiri`'nın ham okumasına girer).
GECERSIZ_AN = BOZUK_ANLAR[0]


def _istemci() -> APIClient:
    return APIClient(raise_request_exception=False)


def _son_seq() -> int:
    return int(AuditTrail.objects.order_by("-seq").values_list("seq", flat=True).first() or 0)


def _satir(liste: list[dict[str, Any]], hesap_id: object) -> dict[str, Any]:
    return next(s for s in liste if s["id"] == str(hesap_id))


def _acik(rol: str = AccountRole.MUHASIP, **kw: Any) -> Account:
    return muhurle(
        hesap_ac(rol, **kw), status=AccountStatus.ACIK, password_changed_at=timezone.now()
    )


def _hesaplar() -> dict[str, Account]:
    """Bozuk açılışlı açık muhasip, bozuk kapanışlı kapalı başkan, iki Denetleme Kurulu üyesi (biri
    bozuk açılışlı: aynı rolde okunamayan an sıralamayı düşürmesin)."""
    muhasip = _acik(ad="Uydurma Muhasip")
    baskan = _acik(AccountRole.BASKAN, ad="Uydurma Başkan")
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=baskan.id)
    dk1 = _acik(AccountRole.DENETLEME_KURULU, tanitici="dk-1", ad="Uydurma Denetçi Bir")
    dk2 = _acik(AccountRole.DENETLEME_KURULU, tanitici="dk-2", ad="Uydurma Denetçi İki")
    return {"muhasip": muhasip, "baskan": baskan, "dk1": dk1, "dk2": dk2}


def _boz(hesaplar_: dict[str, Account], bozuk: str) -> None:
    ham_guncelle(hesaplar_["muhasip"].id, opened_at=bozuk)
    ham_guncelle(hesaplar_["baskan"].id, closed_at=bozuk)
    ham_guncelle(hesaplar_["dk1"].id, opened_at=bozuk)


# ============================================================ Kullanıcılar


@pytest.mark.parametrize("bozuk", BOZUK_ANLAR)
def test_kullanicilar_listesi_ayrintisi_ve_secenekleri_dusmez(bozuk: str) -> None:
    """Liste, ayrıntı ve "Yeni hesap" seçenekleri 200 döner; bozuk hesaplar listede kalır, kaydı
    değiştirilmiş görünür (giriş ve eylemler kapalı, nedeni kayıt iletisi), okunamayan an None'dır;
    öteki hesaplar etkilenmez. Tek açık muhasibin kaydı tutmadığı için muhasip rolüne yeni hesap
    açılamaz (ayrı neden, C-1)."""
    h = _hesaplar()
    _boz(h, bozuk)

    liste = _istemci().get("/api/v1/accounts/")
    assert liste.status_code == 200, liste.content
    satirlar = liste.json()["hesaplar"]
    for ad, an_alani in (("muhasip", "acilis"), ("baskan", "kapanis"), ("dk1", "acilis")):
        satir = _satir(satirlar, h[ad].id)
        assert satir["kayit_tutuyor"] is False, ad
        assert satir[an_alani] is None, ad
        assert satir["giris"] == {"yapabilir": False, "neden": hesaplar._ROW_SEAL_MESSAGE}, ad
        assert {e["neden"] for e in satir["eylemler"].values()} == {hesaplar._ROW_SEAL_MESSAGE}
    for kimlik in (TEST_HESAP_ID, h["dk2"].id):
        satir = _satir(satirlar, kimlik)
        assert satir["kayit_tutuyor"] is True and satir["acilis"] is not None
    # Aynı rolde okunamayan açılış anı sona düşer (sıralama düşmez).
    dk_sirasi = [s["id"] for s in satirlar if s["rol"] == AccountRole.DENETLEME_KURULU]
    assert dk_sirasi == [str(h["dk2"].id), str(h["dk1"].id)]

    ayrinti = _istemci().get(f"/api/v1/accounts/{h['muhasip'].id}/")
    assert ayrinti.status_code == 200, ayrinti.content
    assert (ayrinti.json()["acilis"], ayrinti.json()["kayit_tutuyor"]) == (None, False)

    secenekler = _istemci().get("/api/v1/accounts/options/")
    assert secenekler.status_code == 200, secenekler.content
    muhasip_rolu = next(r for r in secenekler.json()["roller"] if r["rol"] == AccountRole.MUHASIP)
    assert (muhasip_rolu["acilabilir"], muhasip_rolu["neden"]) == (
        False,
        hesaplar._ROLE_RECORD_MESSAGE,
    )
    # Hesap açma aynı kuralla reddeder (eskiden 400, İngilizce iç ileti).
    acma = _istemci().post(
        "/api/v1/accounts/",
        {
            "rol": AccountRole.MUHASIP,
            "tanitici": "muhasip-2",
            "ad_soyad": "Uydurma Yeni Muhasip",
            "gecici_parola": UCUNCU_PAROLA,
        },
        format="json",
    )
    assert acma.status_code == 400, acma.content
    assert acma.json()["message"] == hesaplar._ROLE_RECORD_MESSAGE


def test_muhre_girmeyen_an_bozulunca_satirin_izi_tutmaz() -> None:
    """Son giriş anı mühre girmez ama satırın izine (içerik MAC'i) girer: mühür tutsa da satırın izi
    tutmaz (iz denetimi satırı ham okur). Liste düşmez; hesap işlemi `BUTUNLUK` satırıyla (alan
    `kayit_mac`) 409 alır."""
    muhasip = _acik(ad="Uydurma Muhasip")
    ham_guncelle(muhasip.id, last_login_at=GECERSIZ_AN)
    okunan = app_password.account_by_id(muhasip.id)
    assert okunan is not None and okunan.last_login_at is None
    assert okunan.seal_matches(TEST_DEK)  # mühür tutar: karar satırın izinindir

    liste = _istemci().get("/api/v1/accounts/")
    assert liste.status_code == 200, liste.content
    satir = _satir(liste.json()["hesaplar"], muhasip.id)
    assert (satir["kayit_tutuyor"], satir["son_giris"]) == (False, None)

    son = _son_seq()
    yanit = _istemci().post(
        f"/api/v1/accounts/{muhasip.id}/reset-password/",
        {"gecici_parola": UCUNCU_PAROLA},
        format="json",
    )
    assert (yanit.status_code, yanit.json()["code"]) == (409, "hesap_muhru_tutmadi")
    assert yanit.json()["message"] == hesaplar._SEAL_MESSAGE
    yeni = list(AuditTrail.objects.filter(seq__gt=son).values_list("action", "changed_fields"))
    assert yeni == [(AuditAction.BUTUNLUK, ["kayit_mac"])]


# ============================================================ kartlar


@pytest.mark.parametrize("bozuk", BOZUK_ANLAR)
def test_iki_depo_ve_kaydi_degistirilmis_kartlari_dusmez(bozuk: str) -> None:
    """İki depo kartı ve denetim kartlarının "kaydı değiştirilmiş görünen hesaplar" listesi
    okunur (`okunamayan` boş); bozuk hesaplar o listededir (mührü tutmaz: hiçbir işleme girmez),
    iki depo kartının listelerinde değildir."""
    h = _hesaplar()
    _boz(h, bozuk)
    bozuklar = {str(h[ad].id) for ad in ("muhasip", "baskan", "dk1")}

    iki_depo = _istemci().get("/api/v1/security/integrity/two-store/")
    denetim = _istemci().get("/api/v1/security/integrity/audit/")

    assert iki_depo.status_code == 200 and denetim.status_code == 200
    assert iki_depo.json()["okunamayan"] == [] and denetim.json()["okunamayan"] == []
    kart = iki_depo.json()["iki_depo"]
    listelerde = {
        satir["id"]
        for ad in ("sarmalsiz_hesaplar", "silinebilir_sarmallar", "ozeti_tutmayan_hesaplar")
        for satir in kart[ad]
    }
    assert not listelerde & bozuklar
    assert {s["id"] for s in denetim.json()["muhru_tutmayan"]} == bozuklar
    assert set(hesaplar.two_store_differences().seal_mismatch) == bozuklar


@pytest.mark.parametrize("bozuk", BOZUK_ANLAR)
def test_oturumdaki_hesabin_parola_yenilenme_karti_dusmez(bozuk: str) -> None:
    """Oturumdaki hesabın açılış anı bozulunca da parola yenilenme kartı ve bildirim ucu okunur
    (yalnız bildirimin sütunları okunur). "Gördüm" hesabın kaydını yazacağı için kayıt reddini alır:
    409 `hesap_muhru_tutmadi`, açık oturumun iletisi ve `BUTUNLUK` satırı (eskiden 400, İngilizce)."""
    muhasip = hesap_ac(AccountRole.MUHASIP)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    app_password.lock()
    app_password.unlock(hesap_id=muhasip.id, password=UCUNCU_PAROLA, new_password=YENI_PAROLA)
    assert OTURUM.hesap_id() == str(muhasip.id)
    ham_guncelle(muhasip.id, opened_at=bozuk)

    kendi = _istemci().get("/api/v1/security/integrity/")
    bildirim = _istemci().get("/api/v1/security/integrity/reset-notice/")

    assert kendi.status_code == 200 and kendi.json()["okunamayan"] == []
    assert kendi.json()["parola_yenilenme"]["tur"] == "SIFIRLAMA"
    assert bildirim.status_code == 200
    assert bildirim.json()["parola_yenilenme"]["tur"] == "SIFIRLAMA"

    son = _son_seq()
    gordum = _istemci().post("/api/v1/security/integrity/reset-notice/")
    assert (gordum.status_code, gordum.json()["code"]) == (409, "hesap_muhru_tutmadi")
    assert gordum.json()["message"] == app_password.ISLEMDE_KAYIT_MESSAGE
    yeni = list(AuditTrail.objects.filter(seq__gt=son).values_list("action", "changed_fields"))
    assert yeni == [(AuditAction.BUTUNLUK, ["seal"])]


@pytest.mark.parametrize("bozuk", BOZUK_ANLAR)
def test_sifirlama_ani_bozulunca_bildirim_ucu_dusmez(bozuk: str) -> None:
    """Sıfırlama anının KENDİSİ bozulunca (geçersiz: ValueError; yerel saate çevrilemeyen:
    OverflowError; biçimsiz: ORM None okur) iki uç da 200 döner ve bildirim `okunamayan`
    listesine girer: kartlar ucu (`GET security/integrity/`) ve bildirim ucu (`GET
    security/integrity/reset-notice/`; eskiden 500, biçimsiz anda bildirim sessizce kayboluyordu).
    Oturum açıkken bozulur (sıfırlama anı satırın izindedir; yeniden giriş kayıt reddidir)."""
    muhasip = hesap_ac(AccountRole.MUHASIP)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    app_password.lock()
    app_password.unlock(hesap_id=muhasip.id, password=UCUNCU_PAROLA, new_password=YENI_PAROLA)
    assert OTURUM.hesap_id() == str(muhasip.id)
    ham_guncelle(muhasip.id, reset_at=bozuk)

    kendi = _istemci().get("/api/v1/security/integrity/")
    bildirim = _istemci().get("/api/v1/security/integrity/reset-notice/")

    assert kendi.status_code == 200, kendi.content
    assert kendi.json()["okunamayan"] == ["parola_yenilenme"]
    assert kendi.json()["parola_yenilenme"] is None
    assert bildirim.status_code == 200, bildirim.content
    assert bildirim.json() == {"parola_yenilenme": None, "okunamayan": ["parola_yenilenme"]}


# ============================================================ kilit ekranı ve giriş


@pytest.mark.parametrize("bozuk", BOZUK_ANLAR)
def test_kilit_ekrani_listesi_dusmez_giris_kayit_reddidir(bozuk: str) -> None:
    """Kilit ekranının hesap listesi bozuk tek bir anla düşmez (eskiden 500: hiçbir hesap
    giremezdi); bozuk hesap listede kalır, okunamayan açılış anı rolünün sonuna düşer. O hesabın
    girişi kayıt reddidir (409 `hesap_muhru_tutmadi`, kilit ekranının iletisi, `BUTUNLUK` satırı
    alan `seal`; sayaç artmaz); öteki hesaplar girer."""
    h = _hesaplar()
    _boz(h, bozuk)
    app_password.lock()

    liste = _istemci().get("/api/v1/security/accounts/")
    assert liste.status_code == 200, liste.content
    kimlikler = [s["id"] for s in liste.json()]
    assert str(h["muhasip"].id) in kimlikler
    assert str(h["baskan"].id) not in kimlikler  # kapalı hesabın parola kaydı silinmiştir
    dk = [s for s in liste.json() if s["rol"] == AccountRole.DENETLEME_KURULU]
    assert [(s["id"], s["rol_etiketi"]) for s in dk] == [
        (str(h["dk2"].id), "Denetleme Kurulu 1"),
        (str(h["dk1"].id), "Denetleme Kurulu 2"),
    ]

    son = _son_seq()
    yanit = _istemci().post(
        "/api/v1/security/unlock/",
        {"hesap": str(h["muhasip"].id), "parola": GECICI_PAROLA},
        format="json",
    )
    assert (yanit.status_code, yanit.json()["code"]) == (409, "hesap_muhru_tutmadi")
    assert yanit.json()["message"] == app_password._SEAL_MISMATCH_MESSAGE
    yeni = list(AuditTrail.objects.filter(seq__gt=son).values_list("action", "changed_fields"))
    assert yeni == [(AuditAction.BUTUNLUK, ["seal"])]
    assert app_password.wrap_failure_state(h["muhasip"].id) == (0, False)
    assert OTURUM.hesap_id() is None

    assert str(app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA).id) == (
        TEST_HESAP_ID
    )


@pytest.mark.parametrize("uc", ["reset-password", "close", "unsuspend", "handover-slip"])
def test_hesap_islemi_kayit_reddidir(uc: str) -> None:
    """Zaman sütunu bozuk hesaba hesap işlemi 409 `hesap_muhru_tutmadi` ve `BUTUNLUK` satırı alır
    (eskiden 400 ve İngilizce iç ileti); satıra dokunulmaz."""
    muhasip = _acik(ad="Uydurma Muhasip")
    ham_guncelle(muhasip.id, opened_at=GECERSIZ_AN)
    son = _son_seq()

    govde = {"gecici_parola": UCUNCU_PAROLA} if uc == "reset-password" else {}
    yanit = _istemci().post(f"/api/v1/accounts/{muhasip.id}/{uc}/", govde, format="json")

    assert (yanit.status_code, yanit.json()["code"]) == (409, "hesap_muhru_tutmadi")
    assert yanit.json()["message"] == hesaplar._SEAL_MESSAGE
    yeni = list(AuditTrail.objects.filter(seq__gt=son).values_list("action", "changed_fields"))
    assert yeni == [(AuditAction.BUTUNLUK, ["seal"])]


def test_oturumdaki_hesabin_zamani_bozulunca_hesap_islemi_kayit_reddidir() -> None:
    """İşlemi yapan hesabın (oturumdaki program yöneticisi) açılış anı bozulunca da ret İngilizce
    iç ileti değil, işlemi yapanın kayıt reddidir (`hesaplar._actor`)."""
    muhasip = _acik(ad="Uydurma Muhasip")
    ham_guncelle(TEST_HESAP_ID, opened_at=GECERSIZ_AN)

    yanit = _istemci().post(f"/api/v1/accounts/{muhasip.id}/unsuspend/", {}, format="json")

    assert (yanit.status_code, yanit.json()["code"]) == (409, "hesap_muhru_tutmadi")
    assert yanit.json()["message"] == hesaplar._SEAL_MESSAGE


# ============================================================ okuyucu ve temizlik


def test_okuyucu_bozuk_olmayan_anlari_ve_satirlari_ormle_ayni_okur() -> None:
    """`hesap_satiri` olağan satırda ORM'nin kendisidir; bozuk satırda öteki anlar ORM'nin
    değeriyle aynıdır, bozuk an None'dır. `hesap_satirlari` sırayı korur, öteki satırları
    etkilenmeden okur."""
    muhasip = _acik(ad="Uydurma Muhasip")
    beklenen = Account.objects.get(pk=muhasip.id)
    ham_guncelle(muhasip.id, opened_at=GECERSIZ_AN)

    okunan = app_password.account_by_id(muhasip.id)

    assert okunan is not None
    assert okunan.opened_at is None
    for alan in app_password.HESAP_ZAMANLARI:
        if alan != "opened_at":
            assert getattr(okunan, alan) == getattr(beklenen, alan), alan
    assert okunan.login_name == beklenen.login_name and okunan.seal == beklenen.seal
    assert okunan.display_name == beklenen.display_name
    assert not okunan.seal_matches(TEST_DEK)
    assert set(app_password.HESAP_ZAMANLARI) == {
        "opened_at",
        "closed_at",
        "password_changed_at",
        "reset_at",
        "last_login_at",
    }

    hepsi = app_password.hesap_satirlari(Account.objects.order_by("login_name"))
    assert [h.login_name for h in hepsi] == sorted(h.login_name for h in hepsi)
    assert {str(h.id) for h in hepsi} == {TEST_HESAP_ID, str(muhasip.id)}
    yonetici = next(h for h in hepsi if str(h.id) == TEST_HESAP_ID)
    assert yonetici.seal_matches(TEST_DEK) and yonetici.opened_at is not None


def test_bozuk_kapali_hesap_oteki_parola_kayitlarinin_temizligini_durdurmaz() -> None:
    """Kilit açılışındaki kapalı hesap temizliği: kapanış anı bozuk kapalı hesabın parola kaydı
    silinmez (kaydı değiştirilmiş görünür), öteki kapalı hesabınki silinir (eskiden bozuk tek bir
    satır bütün temizliği durduruyordu)."""
    bozuk = _acik(AccountRole.BASKAN, ad="Uydurma Başkan")
    saglam = _acik(AccountRole.SEKRETER, ad="Uydurma Sekreter")
    for hesap in (bozuk, saglam):
        hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
        # Kapamanın dosya adımı yarıda kalmış gibi: parola kaydı güvenlik dosyasında durur.
        app_password.write_account_wrap(
            data_key=TEST_DEK, hesap_id=hesap.id, tanitici=hesap.login_name, password=GECICI_PAROLA
        )
    ham_guncelle(bozuk.id, closed_at=GECERSIZ_AN)
    app_password.lock()

    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    kalan = sarmal_kimlikleri()
    assert str(bozuk.id) in kalan
    assert str(saglam.id) not in kalan
