"""Hesap sarmalının kimliğe bağı — kilit açılışı (kullanıcı kararı 02.11.2026: "Hesap kimliği
parola kaydına bağlanır"; tasarım §4.4.4, §4.6.1, tehdit 19 ve 21).

Sarmalın anahtarı `HKDF(Argon2id(parola, tuz), "od-hesap-sarmali/v1" ‖ kanonik kimlik)`'tir
(`shared.crypto.account_wrapping_key`). Bir hesabın parolasını bilen biri `guvenlik.json`'da
(düz metin) kendi sarmalının `id`'sini program yöneticisininkine çevirirse sarmal o kimlikle
açılmaz; tanıtıcıyı değiştirmek oturumun kimliğini değiştirmez; aynı kimliği taşıyan ikinci
sarmal ve kimliğin kanonik olmayan yazımları bağı atlatmaz. Okuyucu kimliği Argon2id'den önce
kanonik kurala sokar; biçimsiz `kdf` alanı yanlış parola sayılmaz. Bağsız (`turetim`
etiketsiz) sarmal parolayla hiç açılmaz: geri düşüş yoktur, ileti program dışı değişikliği anar
ve bildirim ister. Tazelik de bağlıdır (kullanıcı kararı 03.11.2026): aynı hesabın eski sarmalı
eski parolasıyla açılmaz — satırın sarmal özeti tutmaz (`test_eski_sarmal_eski_parolayla_acilmaz`;
`app_password` modül başlığı "SARMALIN TAZELİĞİ"; öteki kollar `test_sarmal_tazeligi.py`'de).
Geri yükleme kolu `test_geri_yukleme_yetkisi.py`'dedir, türetimin birim testleri
`shared/tests/test_crypto.py`'de.

Muhasip uydurma bir hesaptır (`hesap_ortak.hesap_ac`); parolası geçici paroladır ve satırı
`ACIK`'a çekilir (girişte yenileme istenmesin). Adlar ve kimlikler uydurmadır.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul.models import Account, AccountRole, AccountStatus, AuditAction, AuditTrail
from apps.okul.oturum import OTURUM, OturumHesabi, Yazar, yazar_olarak
from apps.okul.services import app_password, hesaplar
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    UCUNCU_PAROLA,
    YENI_PAROLA,
    arsivler,
    bagsiz_sarmal,
    durum,
    durum_yaz,
    hesap_ac,
    muhurle,
)
from conftest import TEST_HESAP_ID, TEST_KURTARMA_ANAHTARI, TEST_PAROLA, TEST_TANITICI
from shared import crypto

pytestmark = pytest.mark.django_db

#: Muhasibin KENDİ (uydurma) parolası.
MUHASIP_PAROLASI = GECICI_PAROLA
#: Muhasibin geçici parolasından sonra kendi belirlediği (uydurma) parola.
_MUHASIBIN_YENI_PAROLASI = "Muhasip-Yeni-Parola-4!"
#: Üretimdeki gecikme dizisi; kök `conftest` her testte `(0.0,)` yamasını içe aktarmadan SONRA yapar.
_GERCEK_GECIKMELER = app_password.FAILURE_DELAYS

#: Kanonik olmayan yazımlar: satırı bulan okuyucu (`uuid.UUID`) çoğunu aynı satıra çevirir. Başka
#: hesabın kimliğinin yazımıyla kullanıldıklarında BAĞIN yazım oyunuyla atlatılamadığını sınarlar
#: (gevşek okuyucuda da türetimdeki kimlik başkasınınki olurdu); KANONİK KATILIĞI ise kendi
#: kimliğinin yazımıyla kurulan testler sınar (`test_kendi_kimliginin_kanonik_olmayan_yazimi_*`).
KIMLIK_YAZIMLARI: dict[str, Callable[[str], str]] = {
    "buyuk_harf": str.upper,
    "tiresiz": lambda kimlik: kimlik.replace("-", ""),
    "bosluklu": lambda kimlik: f" {kimlik} ",
    "suslu_ayracli": lambda kimlik: f"{{{kimlik}}}",
    "urn_onekli": lambda kimlik: f"urn:uuid:{kimlik}",
}


def _muhasip() -> Account:
    """Açık (`ACIK`) uydurma muhasip hesabı; sarmalı kendi kimliğine bağlı, parolası bilinir."""
    return muhurle(hesap_ac(), status=AccountStatus.ACIK, password_changed_at=timezone.now())


def _sarmallari_yaz(donustur: Callable[[list[dict[str, Any]]], list[dict[str, Any]]]) -> None:
    """Metin düzenleyici taklidi (kod gerekmez): sarmal listesini değiştirip dosyaya yazar."""
    veri = durum()
    veri["hesaplar"] = donustur(veri["hesaplar"])
    durum_yaz(veri)


def _kimligi_degistir(eski: object, yeni: str, *, one_al: bool = False) -> None:
    """TEK sarmalın `id` alanı; `one_al` onu listenin başına taşır (kilit açılışı ilkini dener)."""

    def donustur(liste: list[dict[str, Any]]) -> list[dict[str, Any]]:
        (sarmal,) = [h for h in liste if h["id"] == str(eski)]
        sarmal["id"] = yeni
        if one_al:
            liste.remove(sarmal)
            liste.insert(0, sarmal)
        return liste

    _sarmallari_yaz(donustur)


def _reddedildi_oturum_yok() -> None:
    assert app_password.is_locked() is True
    assert OTURUM.hesap_id() is None
    assert crypto.is_unlocked() is False


def _yanlis_parola_denemeleri(
    hesap_id: object, parola: str, monkeypatch: pytest.MonkeyPatch, *, kez: int = 3
) -> list[float]:
    """`kez` kez reddedilen kilit açılışı (üretimdeki gecikme dizisiyle); beklemeleri döndürür."""
    monkeypatch.setattr(app_password, "FAILURE_DELAYS", _GERCEK_GECIKMELER)
    beklemeler: list[float] = []
    monkeypatch.setattr(time, "sleep", beklemeler.append)
    for _ in range(kez):
        with pytest.raises(app_password.WrongPassword, match="^Parola hatalı.$") as hata:
            app_password.unlock(hesap_id=hesap_id, password=parola)
        assert hata.value.code == "parola_yanlis"
    monkeypatch.setattr(time, "sleep", lambda _sn: None)
    return beklemeler


# ============================================================ kimlik değişikliği


@pytest.mark.parametrize("duzen", ["takas", "one_alinir"])
def test_sarmal_kimligi_degistirilirse_giris_reddedilir(
    duzen: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Muhasip `guvenlik.json`'da kendi sarmalının `id`'sini program yöneticisininkine çevirir —
    iki sarmalın kimliklerini takas ederek ya da kendi sarmalını program yöneticisinin
    kimliğiyle listenin başına koyarak. Kendi parolasıyla program yöneticisi olarak açamaz:
    oturum açılmaz, program yöneticisinin oturumu kurulmaz, satıra ve denetim izine dokunulmaz.
    Sonuç yanlış parolanınkiyle AYNIDIR: aynı ret, aynı gecikme dizisi, aynı sayaç. Bağ
    kaldırılsaydı (türetimden kimlik çıksaydı) oturum program yöneticisi olarak açılırdı."""
    muhasip = _muhasip()
    app_password.lock()
    assert app_password.unlock(hesap_id=muhasip.id, password=MUHASIP_PAROLASI).id == muhasip.id
    app_password.lock()
    # Karşılaştırma tabanı: program yöneticisinin kimliğine düz yanlış parola.
    taban = _yanlis_parola_denemeleri(TEST_HESAP_ID, "Yanlis-Parola-1", monkeypatch)
    taban_sayac = app_password.wrap_failure_state(TEST_HESAP_ID)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)  # sayaç sıfırlanır
    app_password.lock()

    if duzen == "takas":
        _sarmallari_yaz(
            lambda liste: [
                {
                    **h,
                    "id": {TEST_HESAP_ID: str(muhasip.id), str(muhasip.id): TEST_HESAP_ID}[h["id"]],
                }
                for h in liste
            ]
        )
    else:
        _kimligi_degistir(muhasip.id, TEST_HESAP_ID, one_al=True)
    assert [h["tanitici"] for h in durum()["hesaplar"] if h["id"] == TEST_HESAP_ID][0] == "muhasip"
    iz_sayisi = AuditTrail.objects.count()
    son_giris = Account.objects.get(pk=TEST_HESAP_ID).last_login_at

    beklemeler = _yanlis_parola_denemeleri(TEST_HESAP_ID, MUHASIP_PAROLASI, monkeypatch)

    _reddedildi_oturum_yok()
    assert beklemeler == taban == [1.0]
    assert app_password.wrap_failure_state(TEST_HESAP_ID) == taban_sayac == (3, False)
    assert AuditTrail.objects.count() == iz_sayisi
    assert Account.objects.get(pk=TEST_HESAP_ID).last_login_at == son_giris
    if duzen == "takas":
        # Program yöneticisinin sarmalı da muhasibin kimliğiyle açılmaz (iki yön de kapalı).
        for parola in (TEST_PAROLA, MUHASIP_PAROLASI):
            with pytest.raises(app_password.WrongPassword):
                app_password.unlock(hesap_id=muhasip.id, password=parola)
        _reddedildi_oturum_yok()


def test_tanitici_takasi_yetki_yukseltmez() -> None:
    """Tanıtıcı yalnız sarmalı bulmaya ve kilit ekranında göstermeye yarar. Muhasip, sarmalının
    tanıtıcısını `yonetici`, program yöneticisininkini `muhasip` yapar: kilit ekranında
    `yonetici` tanıtıcılı satır muhasibin kimliğini ve rolünü taşır; o satırla açılan oturum
    muhasibin KENDİ kimliğidir. Program yöneticisinin kimliğiyle muhasibin parolası açmaz."""
    muhasip = _muhasip()
    app_password.lock()
    takas = {TEST_TANITICI: "muhasip", "muhasip": TEST_TANITICI}
    _sarmallari_yaz(lambda liste: [{**h, "tanitici": takas[h["tanitici"]]} for h in liste])
    (satir,) = [s for s in hesaplar.lock_screen_accounts() if s["tanitici"] == TEST_TANITICI]
    assert (satir["id"], satir["rol"]) == (str(muhasip.id), "muhasip")

    hesap = app_password.unlock(hesap_id=satir["id"], password=MUHASIP_PAROLASI)

    assert hesap.id == muhasip.id
    assert OTURUM.hesap() == OturumHesabi(id=str(muhasip.id), tanitici="muhasip", rol="muhasip")
    app_password.lock()
    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=MUHASIP_PAROLASI)
    _reddedildi_oturum_yok()


# ============================================================ aynı kimlik, kanonik yazım


@pytest.mark.parametrize("yer", ["sonra", "once"])
def test_ayni_kimligi_tasiyan_iki_sarmal_bagi_atlatmaz(yer: str) -> None:
    """Muhasip kendi sarmalının KOPYASINI program yöneticisinin kimliğiyle ekler (kendi sarmalı
    da yerinde kalır). Kopya hiçbir parolayla program yöneticisi olarak açılmaz.

    * Kopya sonradaysa kilit açılışı meşru sarmalı bulur: program yöneticisi çalışmaya devam
      eder.
    * Kopya öndeyse kilit açılışı onu dener (yalnız seçilen sarmal denenir, Argon2id bir kez):
      program yöneticisinin parolası da geçmez — yetki yükselmez, hizmet reddidir. Kurtarma
      anahtarıyla açılış sarmalı yeniden kurar ve aynı kimliği taşıyan bütün kopyaları siler;
      program yöneticisi yeni parolasıyla açar. Muhasip baştan sona kendi hesabıyla açar.
    """
    muhasip = _muhasip()
    app_password.lock()

    def kopya_ekle(liste: list[dict[str, Any]]) -> list[dict[str, Any]]:
        (kendi,) = [h for h in liste if h["id"] == str(muhasip.id)]
        kopya = {**kendi, "id": TEST_HESAP_ID}
        return [*liste, kopya] if yer == "sonra" else [kopya, *liste]

    _sarmallari_yaz(kopya_ekle)
    assert [h["id"] for h in durum()["hesaplar"]].count(TEST_HESAP_ID) == 2

    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=MUHASIP_PAROLASI)
    _reddedildi_oturum_yok()
    assert app_password.unlock(hesap_id=muhasip.id, password=MUHASIP_PAROLASI).id == muhasip.id
    app_password.lock()

    if yer == "sonra":
        assert str(app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA).id) == (
            TEST_HESAP_ID
        )
        return

    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    _reddedildi_oturum_yok()
    hesap = app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=YENI_PAROLA
    )
    assert str(hesap.id) == TEST_HESAP_ID == OTURUM.hesap_id()
    assert [h["id"] for h in durum()["hesaplar"]].count(TEST_HESAP_ID) == 1
    app_password.lock()
    assert str(app_password.unlock(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA).id) == (
        TEST_HESAP_ID
    )


@pytest.mark.parametrize("yazim", sorted(KIMLIK_YAZIMLARI))
def test_kanonik_olmayan_kimlik_yazimi_bagi_atlatmaz(yazim: str) -> None:
    """Muhasip sarmalının `id`'sine program yöneticisinin kimliğinin kanonik olmayan bir yazımını
    koyar. Satırı bulan okuyucu yazımların çoğunu program yöneticisinin satırına çevirir (bağ
    olmasa yetki yükselirdi). Bu test bağın yazım oyunuyla atlatılamadığını sınar, kanonik
    katılığı değil: sarmal muhasibin kimliğine bağlıdır, okuyucu yazımı gevşek çevirse de
    türetimdeki kimlik program yöneticisininki olurdu. Meşru program yöneticisi kanonik
    kimliğiyle açmaya devam eder."""
    muhasip = _muhasip()
    app_password.lock()
    kimlik = KIMLIK_YAZIMLARI[yazim](TEST_HESAP_ID)
    _kimligi_degistir(muhasip.id, kimlik)
    satir = app_password.account_by_id(kimlik)
    if yazim != "bosluklu":
        assert satir is not None and str(satir.id) == TEST_HESAP_ID

    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=kimlik, password=MUHASIP_PAROLASI)

    _reddedildi_oturum_yok()
    assert str(app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA).id) == (
        TEST_HESAP_ID
    )


@pytest.mark.parametrize("yazim", sorted(KIMLIK_YAZIMLARI))
def test_kendi_kimliginin_kanonik_olmayan_yazimi_da_acmaz(
    yazim: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """KANONİK KATILIK: kural tek kanonik biçimdir (`crypto.canonical_account_id`) ve okuyucu
    kimliği Argon2id'den ÖNCE bu kurala sokar. Muhasibin KENDİ sarmalının `id`'si aynı kimliğin
    kanonik olmayan bir yazımına çevrilir: sarmal, aynı hesabı anlatsa da açılmaz ve türetim hiç
    koşmaz (okuyucu ham metni türetime soksaydı Argon2id koşardı; gevşek çevirseydi sarmal
    açılırdı). Böylece açılan sarmalın kimlik metni her zaman kanoniktir; kimliği metin olarak
    karşılaştıran sonraki adımlar (oturum, geri yükleme notu, iz satırı) aynı hesabı aynı
    metinle görür."""
    muhasip = _muhasip()
    app_password.lock()
    yazilan = KIMLIK_YAZIMLARI[yazim](str(muhasip.id))
    _kimligi_degistir(muhasip.id, yazilan)
    (bolum,) = [h for h in durum()["hesaplar"] if h["id"] == yazilan]

    with monkeypatch.context() as yama:
        yama.setattr(crypto, "derive_key", lambda *_a, **_k: pytest.fail("Argon2id koşmamalı"))
        assert app_password._try_unwrap_account(bolum, durum(), MUHASIP_PAROLASI) is None
        with pytest.raises(app_password.WrongPassword):
            app_password.unlock(hesap_id=yazilan, password=MUHASIP_PAROLASI)

    _reddedildi_oturum_yok()
    _kimligi_degistir(yazilan, str(muhasip.id))  # kanonik metin geri gelince yine açılır
    assert app_password.unlock(hesap_id=muhasip.id, password=MUHASIP_PAROLASI).id == muhasip.id


# ============================================================ bağsız (F1b-1 biçimli) dosya


def _bagsiz_dosya(muhasip: Account) -> None:
    """Bağsız sarmallı güvenlik dosyası taklidi (bağdan önceki deneme kurulumu ya da etiketi
    program dışından silinmiş dosya): iki sarmal da bağsız, kurtarma bölümü aynı."""
    _sarmallari_yaz(
        lambda _liste: [
            bagsiz_sarmal(TEST_HESAP_ID, TEST_TANITICI, TEST_PAROLA),
            bagsiz_sarmal(muhasip.id, "muhasip", MUHASIP_PAROLASI),
        ]
    )


def test_bagsiz_sarmal_dogru_parolayla_da_acilmaz_ve_yol_gosterir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bağsız sarmallı dosya kullanılabilir sayılır (kayıp kilidi değil; kurtarma bölümü sağlam),
    ama bağsız sarmal doğru parolayla da açılmaz. Ret Argon2id koşmadan, sayaca dokunmadan 409
    `iki_depo_tutarsiz`'dir. Program bağsız sarmal yazmadığı için sahada bu durum yalnız program
    dışı değişiklikle doğar: ileti mühür iletisinin kalıbıyla değişikliği anar, Denetleme
    Kuruluna bildirim ister ve çıkışı söyler (zarfın üçüncü durumu; kullanıcı kararı 03.11.2026:
    program yöneticisi kurtarma anahtarıyla açar, öteki hesapları o sıfırlar). Teknik olarak kurtarma anahtarıyla açılış
    ve parola sıfırlaması sarmalı bağlı biçimde yeniden kurar: program yöneticisi kurtarma
    anahtarıyla açar, muhasibin parolasını sıfırlar; muhasip geçici parolasıyla açıp parolasını
    yeniler."""
    muhasip = _muhasip()
    app_password.lock()
    _bagsiz_dosya(muhasip)
    assert app_password.security_file_missing() is False
    ileti = app_password.UNBOUND_WRAP_MESSAGE
    assert "program dışından değiştirilmiş" in ileti and "Denetleme Kuruluna bildirin" in ileti
    # Zarf kararı (kullanıcı kararı 03.11.2026): ileti çıkışı söyler — program yöneticisi
    # "Parolamı unuttum" yolundan kurtarma anahtarıyla açar, öteki hesapları o sıfırlar.
    assert "“Parolamı unuttum”" in ileti and "program yöneticisi sıfırlar" in ileti

    with monkeypatch.context() as yama:
        yama.setattr(crypto, "derive_key", lambda *_a, **_k: pytest.fail("Argon2id koşmamalı"))
        for hesap_id, parola in ((TEST_HESAP_ID, TEST_PAROLA), (muhasip.id, MUHASIP_PAROLASI)):
            with pytest.raises(app_password.UnboundWrap) as hata:
                app_password.unlock(hesap_id=hesap_id, password=parola)
            assert (hata.value.code, hata.value.status_code) == ("iki_depo_tutarsiz", 409)
            assert str(hata.value) == app_password.UNBOUND_WRAP_MESSAGE
            assert app_password.wrap_failure_state(hesap_id) == (0, False)
        yanit = APIClient().post(
            "/api/v1/security/unlock/",
            {"hesap": TEST_HESAP_ID, "parola": TEST_PAROLA},
            format="json",
        )
        assert yanit.status_code == 409
        assert yanit.json()["code"] == "iki_depo_tutarsiz"
        assert yanit.json()["message"] == app_password.UNBOUND_WRAP_MESSAGE
    _reddedildi_oturum_yok()

    hesap = app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=YENI_PAROLA
    )
    assert str(hesap.id) == TEST_HESAP_ID == OTURUM.hesap_id()
    sarmallar = {h["id"]: h for h in durum()["hesaplar"]}
    assert app_password.wrap_is_bound(sarmallar[TEST_HESAP_ID]) is True
    assert app_password.wrap_is_bound(sarmallar[str(muhasip.id)]) is False

    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    app_password.lock()
    acilan = app_password.unlock(
        hesap_id=muhasip.id, password=UCUNCU_PAROLA, new_password="Muhasip-Yeni-Parola-4!"
    )
    assert acilan.id == muhasip.id
    assert all(app_password.wrap_is_bound(h) for h in durum()["hesaplar"])


def test_etiket_turetimi_secmez() -> None:
    """`turetim` etiketi YALNIZ ret içindir: bağsız sarmala sonradan eklenen etiket onu açtırmaz
    (yanlış parolayla aynı sonuç), bağlı sarmaldan silinen etiket onu yalnız reddettirir."""
    muhasip = _muhasip()
    app_password.lock()
    _bagsiz_dosya(muhasip)
    _sarmallari_yaz(
        lambda liste: [
            {**h, app_password.WRAP_DERIVATION_FIELD: app_password.WRAP_DERIVATION} for h in liste
        ]
    )
    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert app_password.wrap_failure_state(TEST_HESAP_ID) == (1, False)
    _reddedildi_oturum_yok()


def test_etiketi_silinen_bagli_sarmal_reddedilir_dogrulama_da() -> None:
    """Bağlı sarmaldan etiket silinirse kilit açılışı da açık oturumdaki parola doğrulaması da
    `UnboundWrap` verir; etiket geri konunca sarmal yine açılır (anahtar değişmedi)."""
    veri = durum()
    etiket = veri["hesaplar"][0].pop(app_password.WRAP_DERIVATION_FIELD)
    durum_yaz(veri)
    with pytest.raises(app_password.UnboundWrap):
        app_password.verify_password(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    app_password.lock()
    with pytest.raises(app_password.UnboundWrap):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    veri["hesaplar"][0][app_password.WRAP_DERIVATION_FIELD] = etiket
    durum_yaz(veri)
    assert str(app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA).id) == (
        TEST_HESAP_ID
    )


def test_yazici_yalniz_bagli_ve_kanonik_sarmal_yazar() -> None:
    """Bütün yazıcıların ortak kapısı `_account_wrap`: `id` kanonik metindir, etiket vardır ve
    sarmal yalnız o kimlikle açılır. Kanonik olmayan kimlikle sarmal yazılmaz."""
    kimlik = uuid.uuid4()
    sarmal = app_password._account_wrap(
        bytes(32), hesap_id=kimlik, tanitici="dk-1", password=YENI_PAROLA, kdf=crypto.DEFAULT_KDF
    )
    assert sarmal["id"] == str(kimlik)
    assert sarmal[app_password.WRAP_DERIVATION_FIELD] == "od-hesap-sarmali/v1"
    durum_ = {"kdf": crypto.DEFAULT_KDF.to_dict()}
    assert app_password._try_unwrap_account(sarmal, durum_, YENI_PAROLA) == bytes(32)
    baska = {**sarmal, "id": str(uuid.uuid4())}
    assert app_password._try_unwrap_account(baska, durum_, YENI_PAROLA) is None
    for yanlis in (str(kimlik).upper(), str(kimlik).replace("-", ""), 42):
        with pytest.raises((TypeError, ValueError)):
            app_password._account_wrap(
                bytes(32),
                hesap_id=yanlis,
                tanitici="dk-1",
                password=YENI_PAROLA,
                kdf=crypto.DEFAULT_KDF,
            )


@pytest.mark.parametrize("bicimsiz", [42, None, ["x"]], ids=["sayi", "bos", "liste"])
def test_kimligi_metin_olmayan_sarmal_cokmeden_reddedilir(bicimsiz: object) -> None:
    """Dosyada `id`'si metin olmayan sarmal (elle bozulmuş) çökme değil, yanlış parola sonucudur:
    kimlik kanonik biçime çevrilemez, sarmal açılmaz."""
    veri = durum()
    veri["hesaplar"][0]["id"] = bicimsiz
    assert app_password._try_unwrap_account(veri["hesaplar"][0], veri, TEST_PAROLA) is None
    with pytest.raises(app_password.WrongPassword):
        app_password._unwrap_with_account(veri, TEST_TANITICI, TEST_PAROLA)


def test_bagsiz_sarmal_iletisi_sozlukte_yazilidir() -> None:
    """İleti sözlüğün §1 "Hesap" satırında birebir yazılıdır (kullanıcıya görünen her metin)."""
    sozluk = Path(__file__).resolve().parents[4] / "docs" / "sozluk.md"
    if not sozluk.is_file():
        sozluk = Path("/repo/docs/sozluk.md")
    assert f'**"{app_password.UNBOUND_WRAP_MESSAGE}"**' in sozluk.read_text(encoding="utf-8")


# ============================================================ okuyucunun yakaladığı hata


@pytest.mark.parametrize(
    ("alan", "deger"), [("time_cost", "uc"), ("memory_cost", None)], ids=["metin", "bos"]
)
def test_bicimsiz_kdf_yanlis_parola_sayilmaz(alan: str, deger: object) -> None:
    """Okuyucunun (`_try_unwrap_account`) yakaladığı hata YALNIZ kimliğinkidir. `kdf` alanı
    biçimsizse (`KdfParams.from_dict`'in `int(...)`'i) doğru parola "Parola hatalı." almaz:
    hata çağırana çıkar, hatalı deneme sayacı artmaz, organ hesabı onuncu denemede askıya
    düşmez. Kilit açılışı, açık oturumdaki doğrulama, geri yüklemenin parola yolu ve kurtarma
    yolu aynı davranır (bozuk dosya parola hatası gibi gösterilmez)."""
    muhasip = _muhasip()
    veri = durum()
    veri["kdf"][alan] = deger
    durum_yaz(veri)
    assert app_password.security_file_missing() is False

    def bozuk_kdf_hatasi(islem: Callable[[], object]) -> None:
        with pytest.raises((TypeError, ValueError)) as hata:
            islem()
        assert not isinstance(hata.value, app_password.AppPasswordError), hata.value

    bozuk_kdf_hatasi(
        lambda: app_password.verify_password(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    )
    app_password.lock()
    for _ in range(app_password.SUSPEND_AFTER_FAILURES):
        bozuk_kdf_hatasi(
            lambda: app_password.unlock(hesap_id=muhasip.id, password=MUHASIP_PAROLASI)
        )
    bozuk_kdf_hatasi(lambda: app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA))
    bozuk_kdf_hatasi(
        lambda: app_password._unwrap_with_account(durum(), "muhasip", MUHASIP_PAROLASI)
    )
    bozuk_kdf_hatasi(
        lambda: app_password.unlock_with_recovery(
            recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=YENI_PAROLA
        )
    )

    assert app_password.wrap_failure_state(muhasip.id) == (0, False)
    assert app_password.wrap_failure_state(TEST_HESAP_ID) == (0, False)
    _reddedildi_oturum_yok()


# ============================================================ kopya sarmalın çıkış yolları


def _kopyayi_one_koy(kaynak_id: object, hedef_id: object, *, tanitici: str) -> None:
    """`kaynak_id`'nin sarmalının kopyasını `hedef_id` kimliğiyle listenin başına koyar (metin
    düzenleyici taklidi). Kopya kaynağın kimliğine bağlıdır: hedefin hiçbir parolasıyla açılmaz."""

    def donustur(liste: list[dict[str, Any]]) -> list[dict[str, Any]]:
        (kaynak,) = [h for h in liste if h["id"] == str(kaynak_id)]
        return [{**kaynak, "id": str(hedef_id), "tanitici": tanitici}, *liste]

    _sarmallari_yaz(donustur)


def _sarmal_sayisi(hesap_id: object) -> int:
    return [h["id"] for h in durum()["hesaplar"]].count(str(hesap_id))


def test_kopya_ondeyken_parola_degistirilemez_sifirlama_kopyalari_siler() -> None:
    """Muhasibin kimliğini taşıyan bir kopya listenin başındaysa kilit açılışı da açık oturumdaki
    parola doğrulaması da yalnız onu dener: muhasip doğru parolasıyla açamaz (zorunlu yenileme
    dahil), açık oturumda parolasını da değiştiremez. Yetki yükselmez, hizmet reddidir. Program
    yöneticisinin parola sıfırlaması (`_replace_wrap`) aynı kimliği taşıyan kopyaları siler;
    muhasip geçici parolasıyla açar."""
    muhasip = _muhasip()
    app_password.lock()
    assert app_password.unlock(hesap_id=muhasip.id, password=MUHASIP_PAROLASI).id == muhasip.id
    _kopyayi_one_koy(TEST_HESAP_ID, muhasip.id, tanitici="muhasip")
    assert _sarmal_sayisi(muhasip.id) == 2

    with pytest.raises(app_password.WrongPassword):
        app_password.change_password(
            hesap_id=muhasip.id, current_password=MUHASIP_PAROLASI, new_password=YENI_PAROLA
        )
    app_password.lock()
    for yeni in (None, YENI_PAROLA):
        with pytest.raises(app_password.WrongPassword):
            app_password.unlock(hesap_id=muhasip.id, password=MUHASIP_PAROLASI, new_password=yeni)
    _reddedildi_oturum_yok()

    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    assert _sarmal_sayisi(muhasip.id) == 1
    app_password.lock()
    acilan = app_password.unlock(
        hesap_id=muhasip.id, password=UCUNCU_PAROLA, new_password=_MUHASIBIN_YENI_PAROLASI
    )
    assert acilan.id == muhasip.id


def test_program_yoneticisinin_onundeki_kopyayi_baska_program_yoneticisi_temizler() -> None:
    """Program yöneticisinin kimliğini taşıyan kopya öndeyse o hesap parolasıyla açamaz. Başka
    bir program yöneticisinin parola sıfırlaması kopyaları siler (`_target` öteki program
    yöneticisini engellemez); kurtarma anahtarıyla açılış kolu
    `test_ayni_kimligi_tasiyan_iki_sarmal_bagi_atlatmaz[once]`'tadır."""
    ikinci = muhurle(
        hesap_ac(AccountRole.YONETICI, tanitici="yonetici-2", ad="Örnek İkinci Yönetici"),
        status=AccountStatus.ACIK,
        password_changed_at=timezone.now(),
    )
    app_password.lock()
    _kopyayi_one_koy(ikinci.id, TEST_HESAP_ID, tanitici=TEST_TANITICI)
    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    _reddedildi_oturum_yok()

    assert app_password.unlock(hesap_id=ikinci.id, password=GECICI_PAROLA).id == ikinci.id
    with yazar_olarak(Yazar(hesap_id=str(ikinci.id), rol=AccountRole.YONETICI)):
        hesaplar.reset_password(
            by_hesap_id=ikinci.id, hesap_id=TEST_HESAP_ID, temp_password=UCUNCU_PAROLA
        )
    assert _sarmal_sayisi(TEST_HESAP_ID) == 1
    app_password.lock()
    acilan = app_password.unlock(
        hesap_id=TEST_HESAP_ID, password=UCUNCU_PAROLA, new_password=YENI_PAROLA
    )
    assert str(acilan.id) == TEST_HESAP_ID


def test_kanonik_olmayan_kopya_sifirlamayla_silinmez_iki_depo_onayiyla_silinir() -> None:
    """Kimliğin kanonik olmayan yazımını taşıyan kopya (`_replace_wrap` kanonik metinle
    karşılaştırır) sarmal yazımlarıyla silinmez; girişi de engellemez (`_find_wrap` kanonik
    kimlikle arar). Kilit ekranında "Hesap kaydı okunamadı" diye seçilemez görünür, iki depo
    farkında satırsız sarmal olarak listelenir ve program yöneticisinin onayıyla silinir."""
    muhasip = _muhasip()
    buyuk = str(muhasip.id).upper()
    _kopyayi_one_koy(muhasip.id, buyuk, tanitici="muhasip")
    app_password.lock()
    assert app_password.unlock(hesap_id=muhasip.id, password=MUHASIP_PAROLASI).id == muhasip.id
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    assert (_sarmal_sayisi(buyuk), _sarmal_sayisi(muhasip.id)) == (1, 1)
    (satir,) = [s for s in hesaplar.lock_screen_accounts() if s["id"] == buyuk]
    assert (satir["rol"], satir["secilebilir"], satir["rol_etiketi"]) == (
        None,
        False,
        "Hesap kaydı okunamadı",
    )
    assert buyuk in hesaplar.two_store_differences().wraps_without_row

    assert hesaplar.remove_orphan_wraps(by_hesap_id=TEST_HESAP_ID, hesap_idler=[buyuk]) == [buyuk]
    assert buyuk not in app_password.wrap_ids()
    assert _sarmal_sayisi(muhasip.id) == 1


# ============================================================ tazelik (kullanıcı kararı 03.11.2026)


def _arsivdeki_sarmal(hesap_id: object, parola: str) -> dict[str, Any]:
    """Arşiv kopyalarında bu hesabın, verilen parolayla açılan (kimliğine bağlı) sarmalı."""
    kdf_durumu = durum()
    for arsiv in arsivler():
        for bolum in json.loads(arsiv.read_text(encoding="utf-8")).get("hesaplar", []):
            if (
                bolum.get("id") == str(hesap_id)
                and app_password._try_unwrap_account(bolum, kdf_durumu, parola) is not None
            ):
                return dict(bolum)
    raise AssertionError("arşivde o parolanın sarmalı yok")


def _ham_satir(hesap_id: object) -> dict[str, Any]:
    satir = (
        Account.objects.filter(pk=str(hesap_id))
        .values(
            "status",
            "seal",
            "wrap_digest",
            "wrap_digest_pending",
            "reset_notice_pending",
            "reset_at",
            "reset_kind",
            "last_login_at",
            "password_changed_at",
        )
        .first()
    )
    assert satir is not None
    return dict(satir)


@pytest.mark.parametrize("satir_durumu", ["acik", "parola_yenilenmeli"])
def test_eski_sarmal_eski_parolayla_acilmaz(satir_durumu: str) -> None:
    """Eski "bilinen sınır" kapandı (kullanıcı kararı 03.11.2026 "Tazelik kapatılır"; `app_password`
    modül başlığı "SARMALIN TAZELİĞİ"). Veri dizinine yazabilen ve eski ya da geçici parolayı
    bilen biri arşivdeki eski sarmalı `guvenlik.json`'a geri koyar (kod gerekmez). Parola o
    sarmalı açar ama sarmalın özeti mühürlü satırın asıl ya da bekleyen özetini tutmaz: oturum
    AÇILMAZ, `BUTUNLUK` satırı (`SISTEM`, alan `wrap_digest`) düşer, satır ve parola yenilenme
    bildirimi değişmez, hatalı deneme sayacı artmaz (mühür uyuşmazlığı yoluyla aynı).

    * `acik`: program yöneticisi geçici parola verir, muhasip açıp yeniler ve bildirimi kapatır;
      geçici parolanın sarmalı arşivden geri konur — geçici parola açmaz (K2: mali kayıtları yalnız
      muhasip girer).
    * `parola_yenilenmeli`: ele geçmiş parola sıfırlanır; eski sarmal geri konur — eski parola
      (yeni parola verilse de) açmaz, `PAROLA` satırı düşmez."""
    muhasip = _muhasip()
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    app_password.lock()
    app_password.unlock(
        hesap_id=muhasip.id, password=UCUNCU_PAROLA, new_password=_MUHASIBIN_YENI_PAROLASI
    )
    with yazar_olarak(Yazar(hesap_id=str(muhasip.id), rol=AccountRole.MUHASIP)):
        hesaplar.acknowledge_reset_notice(hesap_id=muhasip.id)
    app_password.lock()
    if satir_durumu == "acik":
        bilinen = UCUNCU_PAROLA
    else:
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
        hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password="Dorduncu-Parola-5%"
        )
        app_password.lock()
        bilinen = _MUHASIBIN_YENI_PAROLASI
    eski = _arsivdeki_sarmal(muhasip.id, bilinen)
    _sarmallari_yaz(lambda liste: [eski if h["id"] == eski["id"] else h for h in liste])
    once = _ham_satir(muhasip.id)
    son_sira = AuditTrail.objects.order_by("-seq").values_list("seq", flat=True).first()

    for yeni_parola in (None, "Baska-Parola-6&"):
        with pytest.raises(app_password.WrapDigestMismatch) as hata:
            app_password.unlock(hesap_id=muhasip.id, password=bilinen, new_password=yeni_parola)
        assert (hata.value.code, hata.value.status_code) == ("hesap_muhru_tutmadi", 409)
        assert str(hata.value) == app_password.UNBOUND_WRAP_MESSAGE
        _reddedildi_oturum_yok()

    assert _ham_satir(muhasip.id) == once
    assert app_password.wrap_failure_state(muhasip.id) == (0, False)
    satirlar = list(AuditTrail.objects.filter(seq__gt=son_sira).order_by("seq"))
    assert [s.action for s in satirlar] == [AuditAction.BUTUNLUK, AuditAction.BUTUNLUK]
    for satir in satirlar:
        assert (satir.model, satir.object_id, satir.changed_fields, satir.actor) == (
            "okul.Account",
            str(muhasip.id),
            ["wrap_digest"],
            "SISTEM",
        )
    # Uç da aynı ileti ve kodla reddeder.
    yanit = APIClient().post(
        "/api/v1/security/unlock/", {"hesap": str(muhasip.id), "parola": bilinen}, format="json"
    )
    assert (yanit.status_code, yanit.json()["code"]) == (409, "hesap_muhru_tutmadi")
    assert yanit.json()["message"] == app_password.UNBOUND_WRAP_MESSAGE
