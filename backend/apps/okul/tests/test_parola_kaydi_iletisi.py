"""Program dışından değiştirilmiş görünen parola kaydının İLETİLERİ (orkestratör maddesi (d0)-3).

Bağsız parola kaydı (`turetim` etiketi yok; `UnboundWrap`) ve özeti hesap kaydındakini tutmayan
parola kaydı (eski kaydın geri konması; `WrapDigestMismatch`) iki yerde reddedilir:

* KİLİT EKRANINDA (`unlock`) ileti değişmez — `UNBOUND_WRAP_MESSAGE` ("…; giriş açılmadı. Denetleme
  Kuruluna bildirin. Program yöneticisinin hesabıysa “Parolamı unuttum” yolundan…"; kullanıcı
  kararı 03.11.2026); kurtarma anahtarıyla açılış bu hâlin çıkışıdır ve iletileri de değişmez.
* AÇIK OTURUMDA (parola doğrulama, parola değiştirme, kurtarma anahtarının yenilenmesi;
  `_check_session_password`) kişi zaten oturumdadır: ileti `ISLEMDE_PAROLA_KAYDI_MESSAGE` ("…;
  işlem yapılmadı. Denetleme Kuruluna bildirin."). Kod, durum ve yan etkiler kilit ekranınınkidir
  (sayaç artmaz, oturum sürer; eski kayıtta `BUTUNLUK` satırı).

Adlar ve parolalar uydurmadır.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.okul.models import AuditAction, AuditTrail
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password
from apps.okul.tests.hesap_ortak import (
    UCUNCU_PAROLA,
    YENI_PAROLA,
    arsivler,
    durum,
    durum_yaz,
    ham_guncelle,
)
from conftest import TEST_HESAP_ID, TEST_KURTARMA_ANAHTARI, TEST_PAROLA

pytestmark = pytest.mark.django_db

#: İki hâl: bağsız parola kaydı ve özeti tutmayan (eski) parola kaydı.
HALLER = ("bagsiz", "eski")
#: Açık oturumdaki üç parola doğrulaması.
ISLEMLER = ("dogrulama", "degistirme", "kurtarma_yenileme")
#: Hâlin hatası, kodu ve HTTP durumu (kilit ekranınınkiyle aynı; değişmez).
BEKLENEN: dict[str, tuple[type[app_password.UnlockRefused], str, int]] = {
    "bagsiz": (app_password.UnboundWrap, "iki_depo_tutarsiz", 409),
    "eski": (app_password.WrapDigestMismatch, "hesap_muhru_tutmadi", 409),
}


def _son_seq() -> int:
    return int(AuditTrail.objects.order_by("-seq").values_list("seq", flat=True).first() or 0)


def _arsivdeki_sarmal(hesap_id: object, parola: str) -> dict[str, Any]:
    kdf_durumu = durum()
    for arsiv in arsivler():
        for bolum in json.loads(arsiv.read_text(encoding="utf-8")).get("hesaplar", []):
            if (
                bolum.get("id") == str(hesap_id)
                and app_password._try_unwrap_account(bolum, kdf_durumu, parola) is not None
            ):
                return dict(bolum)
    raise AssertionError("arşivde o parolanın sarmalı yok")


def _parola_kaydini_boz(hal: str) -> str:
    """Program yöneticisinin parola kaydını program dışından değiştirir; kaydı açan parolayı döndürür.

    `bagsiz`: etiket silinir (anahtar değişmez, doğru parola yine `TEST_PAROLA`). `eski`: parola
    değiştirilir, arşivdeki eski kayıt geri konur (eski parola `TEST_PAROLA` onu açar, özet tutmaz).
    """
    veri = durum()
    if hal == "bagsiz":
        for bolum in veri["hesaplar"]:
            if bolum["id"] == TEST_HESAP_ID:
                bolum.pop(app_password.WRAP_DERIVATION_FIELD)
        durum_yaz(veri)
        return TEST_PAROLA
    app_password.change_password(
        hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
    )
    eski = _arsivdeki_sarmal(TEST_HESAP_ID, TEST_PAROLA)
    veri = durum()
    veri["hesaplar"] = [dict(eski) if h["id"] == eski["id"] else h for h in veri["hesaplar"]]
    durum_yaz(veri)
    return TEST_PAROLA


def _islem(islem: str, parola: str) -> None:
    if islem == "dogrulama":
        app_password.verify_password(hesap_id=TEST_HESAP_ID, password=parola)
    elif islem == "degistirme":
        app_password.change_password(
            hesap_id=TEST_HESAP_ID, current_password=parola, new_password=UCUNCU_PAROLA
        )
    else:
        app_password.renew_recovery_key(hesap_id=TEST_HESAP_ID, password=parola)


# ============================================================ açık oturum: kendi iletisi


@pytest.mark.parametrize("islem", ISLEMLER)
@pytest.mark.parametrize("hal", HALLER)
def test_acik_oturumda_parola_kaydi_iletisi_oturumunkidir(hal: str, islem: str) -> None:
    """Açık oturumdaki parola doğrulaması kilit ekranının iletisini ("giriş açılmadı", "Parolamı
    unuttum") VERMEZ: kişi zaten oturumdadır. İleti `ISLEMDE_PAROLA_KAYDI_MESSAGE`; kod, durum ve
    yan etkiler değişmez (sayaç artmaz, kurtarma bölümü aynı kalır, oturum sürer; eski kayıtta
    `BUTUNLUK` satırı düşer, bağsızda düşmez — DEK açılmadan reddedilir)."""
    parola = _parola_kaydini_boz(hal)
    kurtarma = durum()["kurtarma"]
    son = _son_seq()
    hata_turu, kod, http = BEKLENEN[hal]

    with pytest.raises(hata_turu) as hata:
        _islem(islem, parola)

    assert type(hata.value) is hata_turu
    assert (hata.value.code, hata.value.status_code) == (kod, http)
    assert str(hata.value) == app_password.ISLEMDE_PAROLA_KAYDI_MESSAGE
    assert "giriş açılmadı" not in str(hata.value) and "Parolamı unuttum" not in str(hata.value)
    assert app_password.wrap_failure_state(TEST_HESAP_ID) == (0, False)
    assert durum()["kurtarma"] == kurtarma
    assert OTURUM.hesap_id() == TEST_HESAP_ID
    yeni = list(AuditTrail.objects.filter(seq__gt=son).values_list("action", "changed_fields"))
    assert yeni == ([] if hal == "bagsiz" else [(AuditAction.BUTUNLUK, ["wrap_digest"])])


@pytest.mark.parametrize("hal", HALLER)
def test_parola_degistirme_ve_kurtarma_yenileme_uclari_oturum_iletisini_verir(hal: str) -> None:
    """Uçlar servisin iletisini ve kodunu taşır: Ayarlar → Güvenlik'in "Parolayı değiştir" ve
    kurtarma anahtarının yenilenmesi."""
    parola = _parola_kaydini_boz(hal)
    _, kod, http = BEKLENEN[hal]
    istemci = APIClient()

    degistirme = istemci.post(
        "/api/v1/security/change-password/",
        {"parola": parola, "yeni_parola": UCUNCU_PAROLA},
        format="json",
    )
    yenileme = istemci.post(
        "/api/v1/security/recovery-key/renew/", {"password": parola}, format="json"
    )

    for yanit in (degistirme, yenileme):
        assert yanit.status_code == http, yanit.content
        assert yanit.json()["code"] == kod
        assert yanit.json()["message"] == app_password.ISLEMDE_PAROLA_KAYDI_MESSAGE
        assert "recovery_key" not in yanit.json()
    assert OTURUM.hesap_id() == TEST_HESAP_ID


# ============================================================ kilit ekranı ve kurtarma: değişmez


@pytest.mark.parametrize("hal", HALLER)
def test_kilit_ekraninin_ve_kurtarmanin_iletisi_degismez(hal: str) -> None:
    """Kilit ekranı kullanıcı kararının iletisini (03.11.2026) korur: "giriş açılmadı", Denetleme
    Kuruluna bildirim, program yöneticisi için "Parolamı unuttum", öteki hesaplar için program
    yöneticisinin sıfırlaması — servis ve uç. Kurtarma anahtarıyla açılış bu hâlin çıkışıdır ve
    açar (parola kaydını bağlı biçimde yeniden kurar)."""
    parola = _parola_kaydini_boz(hal)
    hata_turu, kod, http = BEKLENEN[hal]
    app_password.lock()

    with pytest.raises(hata_turu) as hata:
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=parola)
    yanit = APIClient().post(
        "/api/v1/security/unlock/", {"hesap": TEST_HESAP_ID, "parola": parola}, format="json"
    )

    assert str(hata.value) == app_password.UNBOUND_WRAP_MESSAGE
    assert app_password.UNBOUND_WRAP_MESSAGE != app_password.ISLEMDE_PAROLA_KAYDI_MESSAGE
    assert (yanit.status_code, yanit.json()["code"]) == (http, kod)
    assert yanit.json()["message"] == app_password.UNBOUND_WRAP_MESSAGE
    assert OTURUM.hesap_id() is None

    hesap = app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=UCUNCU_PAROLA
    )
    assert str(hesap.id) == TEST_HESAP_ID == OTURUM.hesap_id()
    sarmal = app_password._find_wrap(durum(), TEST_HESAP_ID)
    assert sarmal is not None and app_password.wrap_is_bound(sarmal)


def test_kurtarma_anahtariyla_acilisin_kayit_iletisi_kilit_ekraninindir() -> None:
    """Kurtarma anahtarıyla açılış kilitliyken yapılır: kaydı tutmayan hesabın iletisi kilit
    ekranınınkidir ("giriş açılmadı"), açık oturumun karşılığı ("kayda dokunulmadı") değil."""
    ham_guncelle(TEST_HESAP_ID, login_name="baska-tanitici")  # program dışından değişiklik
    app_password.lock()

    with pytest.raises(app_password.AccountSealMismatch) as hata:
        app_password.unlock_with_recovery(
            recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=UCUNCU_PAROLA
        )

    assert str(hata.value) == app_password._SEAL_MISMATCH_MESSAGE
    assert str(hata.value) != app_password.ISLEMDE_KAYIT_MESSAGE
    assert OTURUM.hesap_id() is None


def test_oturum_iletisi_sozlukte_yazilidir() -> None:
    """Kullanıcıya görünen her metin sözlüktedir (§1 "Hesap (F1b)")."""
    for kok in (Path(__file__).resolve().parents[4], Path("/repo")):
        yol = kok / "docs" / "sozluk.md"
        if yol.is_file():
            sozluk = yol.read_text(encoding="utf-8")
            break
    else:
        pytest.fail("docs/sozluk.md bulunamadı.")
    for ileti in (app_password.ISLEMDE_PAROLA_KAYDI_MESSAGE, app_password.UNBOUND_WRAP_MESSAGE):
        assert f'**"{ileti}"**' in sozluk
