"""`POST app/quit/` — arayüzden düzenli çıkış (tasarım §4.2 "Kapanış", §4.5).

Çık HER oturum durumunda parolasızdır (tasarım §4.2, §4.5; plan F1b-1 "Oturum"):
açık oturumda (her rolde), kilitliyken, kurulumda, güvenlik dosyası kayıpken ve
geri yüklemeden sonra. Aile iskeletinin görevli kipindeki parola dalı söküldü.
Kapanışın kendisi masaüstü kancasıdır (`masaustu_kanca.cikis_iste`); burada
kancanın çağrılıp çağrılmadığı sınanır. Pencere, oturum kilidi, yönetim sunucusu ve
WAL checkpoint sırası masaüstü testlerindedir (`desktop/tests/test_main.py`).
İstekler tam ara katman zincirinden geçer (yeniden başlat → kilit ve oturum).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.okul import masaustu_kanca, restart_gate
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password
from apps.okul.tests.oturum_ortak import kurulum_durumunu_yaz
from conftest import oturumu_ac_test

pytestmark = pytest.mark.django_db

CIK = "/api/v1/app/quit/"


@pytest.fixture(autouse=True)
def kancalar(db: None) -> Iterator[list[str]]:
    """Çıkış kancası yerine sayaç; test sonunda kayıt temizlenir."""
    kurulum_durumunu_yaz(tamam=True)
    cagrilar: list[str] = []
    masaustu_kanca._reset_for_tests()
    masaustu_kanca.kaydet(cikis=lambda: cagrilar.append("cik"))
    yield cagrilar
    masaustu_kanca._reset_for_tests()


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def dogrulama_cagrilari(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Parola doğrulaması çağrılırsa kaydedilir: Çık hiçbir durumda parola sormaz."""
    cagrilar: list[str] = []

    def kaydet(*, hesap_id: object = None, password: str) -> None:
        cagrilar.append(password)

    monkeypatch.setattr(app_password, "verify_password", kaydet)
    return cagrilar


def _govde(resp: Any) -> dict[str, Any]:
    veri: dict[str, Any] = resp.json()
    return veri


# ------------------------------------------------------------ parolasız durumlar


@pytest.mark.parametrize(
    "rol", ["yonetici", "baskan", "muhasip", "sekreter", "denetleme_kurulu", "mudur"]
)
def test_acik_oturumda_her_rolde_cikis_parolasizdir(
    rol: str, client: APIClient, kancalar: list[str], dogrulama_cagrilari: list[str]
) -> None:
    oturumu_ac_test("0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", tanitici="ornek", rol=rol)
    assert OTURUM.durum() == "acik"

    resp = client.post(CIK, {}, format="json")

    assert resp.status_code == 202
    assert _govde(resp) == {"durum": "kapaniyor"}
    assert kancalar == ["cik"]
    assert dogrulama_cagrilari == []  # parola sorulmadı


def test_govdede_parola_gelse_de_dogrulanmaz(
    client: APIClient, kancalar: list[str], dogrulama_cagrilari: list[str]
) -> None:
    """Ailenin görevli kipindeki parola dalı söküldü: gövde yok sayılır, yankılanmaz."""
    resp = client.post(CIK, {"password": "Yanlis-Parola-9"}, format="json")

    assert resp.status_code == 202
    assert "Yanlis-Parola-9" not in resp.content.decode("utf-8")
    assert dogrulama_cagrilari == []


def test_cikis_ucu_yalniz_post_kabul_eder(client: APIClient, kancalar: list[str]) -> None:
    for yontem in ("get", "put", "patch", "delete"):
        assert getattr(client, yontem)(CIK).status_code == 405
    assert kancalar == []


def test_kilitliyken_cikis_parolasizdir(
    kilitli: None, client: APIClient, kancalar: list[str]
) -> None:
    assert OTURUM.durum() == "kilitli"

    resp = client.post(CIK, {}, format="json")

    assert resp.status_code == 202
    assert kancalar == ["cik"]


def test_kilitliyken_cikis_disindaki_uclar_yine_423(
    kilitli: None, client: APIClient, kancalar: list[str]
) -> None:
    """Muafiyet tam yoldur: `app/` altındaki başka bir yol kilit kapısını aşamaz."""
    assert client.get("/api/v1/grade-levels/").status_code == 423
    assert client.post("/api/v1/app/quit/baska/", {}, format="json").status_code == 423


def test_parola_kurulmadan_cikis_parolasizdir(
    parolasiz: None, client: APIClient, kancalar: list[str]
) -> None:
    assert client.post(CIK, {}, format="json").status_code == 202
    assert kancalar == ["cik"]


def test_guvenlik_dosyasi_kayipken_cikis_parolasizdir(
    parmak_izi_yazili: str, client: APIClient, kancalar: list[str]
) -> None:
    app_password.state_path().unlink()
    assert client.get("/api/v1/grade-levels/").status_code == 423

    assert client.post(CIK, {}, format="json").status_code == 202
    assert kancalar == ["cik"]


def test_yeniden_baslat_gerektiginde_cikis_parolasizdir(
    client: APIClient, kancalar: list[str]
) -> None:
    """Geri yüklemeden sonra bütün API 503'tür; kapının tek çıkışı programı kapatmaktır."""
    restart_gate.mark_restart_required()

    assert client.get("/api/v1/security/session/").status_code == 503
    resp = client.post(CIK, {}, format="json")

    assert resp.status_code == 202
    assert kancalar == ["cik"]


# ------------------------------------------------------------ masaüstü dışında


def test_masaustu_kancasi_yoksa_503(client: APIClient) -> None:
    masaustu_kanca._reset_for_tests()

    resp = client.post(CIK, {}, format="json")

    assert resp.status_code == 503
    assert _govde(resp)["code"] == "cikis_kullanilamiyor"


# ------------------------------------------------------------ kanca kaydı


def test_kanca_kaydi_verilmeyeni_degistirmez_ve_kaldirilir() -> None:
    masaustu_kanca._reset_for_tests()
    cagrilar: list[str] = []

    masaustu_kanca.kaydet(cikis=lambda: cagrilar.append("bir"))
    masaustu_kanca.kaydet()  # verilmeyen kanca değişmez: çıkış kancası yerinde kalır
    assert masaustu_kanca.cikis_iste() is True
    masaustu_kanca.kaldir()

    assert masaustu_kanca.cikis_iste() is False
    assert cagrilar == ["bir"]


def test_gunluk_is_kaydi_ad_ile_tekildir() -> None:
    masaustu_kanca._reset_for_tests()

    masaustu_kanca.gunluk_is_kaydet("cok-okunanlar", lambda: True)
    masaustu_kanca.gunluk_is_kaydet("cok-okunanlar", lambda: None)
    masaustu_kanca.gunluk_is_kaydet("saklama", lambda: False)

    assert [is_.ad for is_ in masaustu_kanca.gunluk_isler()] == ["cok-okunanlar", "saklama"]
    with pytest.raises(ValueError):
        masaustu_kanca.gunluk_is_kaydet("çok-okunanlar", lambda: True)
    with pytest.raises(ValueError):
        masaustu_kanca.gunluk_is_kaydet("", lambda: True)
