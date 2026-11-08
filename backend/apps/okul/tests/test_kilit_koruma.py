"""Kilit kapısının açık listeleri, ara katman sırası ve boşta kilit uçtan uca (tasarım §4.3, §4.4.3).

Plan F1b-1 "Oturum": kilitliyken açık kalan uçlar bir AÇIK listededir (yol + yöntem;
`lock_middleware.KILITLI_IZINLI`); ailedeki gibi bütün `security/` ön eki muaf değildir.
Uç listesi ELLE TUTULMAZ: URL desenleri çalışma anında dolaşılır
(`apps/okul/tests/api_gezgini.py`; dönüştürücüler örnek değerle doldurulur). Eklenen
her yeni uç bu teste kendiliğinden girer ve listeye bilinçli eklenmedikçe kilitliyken
kapalıdır. Rol kapısı (`RolMiddleware`, 403 `rol_yetkisiz`) kilit kapısından sonra durur;
onun dolaşan testi `test_rol_koruma.py`'dedir.

Boşta kilit uçtan uca: `X-OD-Etkinlik` başlığı olmayan periyodik istekler oturumu canlı
tutmaz, başlıklılar tutar; süre dolunca oturum kilitlenir (423) ve DEK bellekten düşer
(ailede görevli kipine inilir, DEK kalırdı).
"""

from __future__ import annotations

import json

import pytest
from desktop.server import HEALTH_PATH
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.test import Client, RequestFactory
from django.urls import Resolver404, resolve

from apps.okul.lock_middleware import KAYIP_IZINLI, KILITLI_IZINLI, OKUMA, AppLockMiddleware
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password
from apps.okul.tests.api_gezgini import SAGLIK_YOLU, api_desenleri
from apps.okul.tests.oturum_ortak import SahteSaat, kurulum_durumunu_yaz, oturum_saatini_kur
from shared import crypto

pytestmark = pytest.mark.django_db

YONTEMLER = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
ETKINLIK = {"X-OD-Etkinlik": "1"}
VERI_UCU = "/api/v1/school-years/"
OTURUM_UCU = "/api/v1/security/session/"
BOSTA = 10 * 60


def _gecti(_request: HttpRequest) -> HttpResponse:
    return HttpResponse("gecti")


def _yalniz_kilit_kapisi(yontem: str, yol: str) -> HttpResponse:
    """Yalnız kilit kapısından geçirir; görünüm KOŞMAZ (yan etkisiz)."""
    return AppLockMiddleware(_gecti)(RequestFactory().generic(yontem, yol))


def _api_yollari() -> list[str]:
    return [ornek for _, ornek in api_desenleri()]


def _kod(yanit: HttpResponse) -> str | None:
    if yanit.status_code != 423:
        return None
    govde: dict[str, str] = json.loads(yanit.content)
    return govde["code"]


# ============================================================ yapı


def test_ara_katman_sirasi_tasarimdaki_gibidir() -> None:
    """Tasarım §4.4.3: belirteç → no-store → güvenlik → whitenoise → common → RestartRequired
    (503) → AppLock (423) → RolMiddleware (403 `rol_yetkisiz`). Kip kapısı söküldü."""
    zincir = [m for m in settings.MIDDLEWARE if m != "desktop.session_guard.SessionTokenMiddleware"]
    assert zincir == [
        "apps.okul.onbellek_middleware.ApiNoStoreMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.middleware.common.CommonMiddleware",
        "apps.okul.restart_gate.RestartRequiredMiddleware",
        "apps.okul.lock_middleware.AppLockMiddleware",
        "apps.okul.rol_middleware.RolMiddleware",
    ]
    if "desktop.session_guard.SessionTokenMiddleware" in settings.MIDDLEWARE:
        assert settings.MIDDLEWARE[0] == "desktop.session_guard.SessionTokenMiddleware"


def test_kilitli_acik_listesi_anlik_goruntuyle_sabittir() -> None:
    """Listeye uç eklemek bilinçli bir karardır: bu anlık görüntü de güncellenir."""
    assert {yol: sorted(yontemler) for yol, yontemler in KILITLI_IZINLI.items()} == {
        HEALTH_PATH: ["GET", "HEAD"],
        "/api/v1/security/status/": ["GET", "HEAD"],
        "/api/v1/security/session/": ["GET", "HEAD"],
        "/api/v1/security/accounts/": ["GET", "HEAD"],
        "/api/v1/security/unlock/": ["POST"],
        # Kurtarma listesi (GET) + kurtarma anahtarıyla açılış (POST).
        "/api/v1/security/recover/": ["GET", "HEAD", "POST"],
        "/api/v1/app/quit/": ["POST"],
    }


def test_kayip_acik_listesi_anlik_goruntuyle_sabittir() -> None:
    assert {yol: sorted(yontemler) for yol, yontemler in KAYIP_IZINLI.items()} == {
        HEALTH_PATH: ["GET", "HEAD"],
        "/api/v1/security/status/": ["GET", "HEAD"],
        "/api/v1/security/session/": ["GET", "HEAD"],
        "/api/v1/security/state/reset/": ["POST"],
        "/api/v1/backups/": ["GET", "HEAD"],
        "/api/v1/backups/inspect/": ["POST"],
        "/api/v1/backups/restore/": ["POST"],
        "/api/v1/app/quit/": ["POST"],
    }


def test_acik_listelerdeki_her_yol_gercek_bir_uctur() -> None:
    """Bayat kural kalmasın: yeniden adlandırılan uç listede sessizce ölü kalmaz."""
    yollar = set(_api_yollari())
    for yol in (*KILITLI_IZINLI, *KAYIP_IZINLI):
        assert yol in yollar, yol
        try:
            resolve(yol)
        except Resolver404:  # pragma: no cover — iddia mesajı için
            pytest.fail(f"çözülemeyen yol: {yol}")
    assert HEALTH_PATH == SAGLIK_YOLU
    assert frozenset({"GET", "HEAD"}) == OKUMA


def test_dolasma_butun_api_yuzeyini_goruyor() -> None:
    """Boş liste yanlış yeşil verirdi; oturum uçları ve sağlık yolu listede olmalı."""
    yollar = _api_yollari()
    assert len(yollar) >= 30
    assert {OTURUM_UCU, "/api/v1/security/accounts/", HEALTH_PATH} <= set(yollar)
    assert not [y for y in yollar if y.startswith("/api/v1/security/mode/")]


# ============================================================ kilitli


def test_kilitliyken_acik_liste_disindaki_her_uc_her_yontemde_423(kilitli: None) -> None:
    kesilmeyen: list[str] = []
    denenen = 0
    for yol in _api_yollari():
        for yontem in YONTEMLER:
            yanit = _yalniz_kilit_kapisi(yontem, yol)
            if yontem in KILITLI_IZINLI.get(yol, frozenset()):
                assert yanit.content == b"gecti", f"{yontem} {yol} kesildi"
                continue
            denenen += 1
            if _kod(yanit) != "locked":
                kesilmeyen.append(f"{yontem} {yol} → {yanit.status_code}")
    assert denenen > 200
    assert kesilmeyen == []


def test_kilitliyken_guvenlik_on_ekinin_yalniz_acik_listedekileri_gecer(kilitli: None) -> None:
    """Ailede bütün `security/` ön eki kilitten muaftı; artık her güvenlik ucu tek tek
    sayılır. Tam zincirle (görünümler dahil): listede olmayan her güvenlik ucu 423."""
    client = Client()
    guvenlik = [y for y in _api_yollari() if y.startswith("/api/v1/security/")]
    assert len(guvenlik) >= 10
    for yol in guvenlik:
        for yontem in ("GET", "POST", "PUT", "DELETE"):
            if yontem in KILITLI_IZINLI.get(yol, frozenset()):
                continue
            yanit = client.generic(yontem, yol)
            assert yanit.status_code == 423, f"{yontem} {yol} → {yanit.status_code}"
            assert yanit.json()["code"] == "locked"


def test_kendi_parolasini_degistirme_kilitliyken_kapalidir(kilitli: None) -> None:
    """Plan F1b-1: yalnız açık oturumda (ailede kilitliyken de açıktı, ikinci bir kilit
    açma yoluydu)."""
    yanit = Client().post(
        "/api/v1/security/change-password/",
        {"parola": "Test-Yonetici-Parolasi-1", "yeni_parola": "Yeni-Parola-2!"},
        content_type="application/json",
    )
    assert yanit.status_code == 423
    assert yanit.json()["code"] == "locked"


def test_kilitliyken_red_govdesi_sabittir_ve_ucu_yankilamaz(kilitli: None) -> None:
    yanit = Client().get("/api/v1/personnel/")

    assert yanit.json() == {
        "code": "locked",
        "message": (
            "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın (parolanızı unuttuysanız "
            "program yöneticisine başvurun)."
        ),
        "fields": {},
    }


def test_api_disi_yollar_kesilmez(kilitli: None) -> None:
    """SPA ve statik dosyalar kilit kapısının konusu değildir (kilit ekranı yüklenebilmeli)."""
    assert _yalniz_kilit_kapisi("GET", "/kisiler").content == b"gecti"


# ============================================================ güvenlik dosyası kayıp


def test_kayipken_acik_liste_disindaki_her_uc_her_yontemde_423(parmak_izi_yazili: str) -> None:
    app_password.state_path().unlink()
    kesilmeyen: list[str] = []
    for yol in _api_yollari():
        for yontem in YONTEMLER:
            yanit = _yalniz_kilit_kapisi(yontem, yol)
            if yontem in KAYIP_IZINLI.get(yol, frozenset()):
                assert yanit.content == b"gecti", f"{yontem} {yol} kesildi"
                continue
            if _kod(yanit) != "guvenlik_dosyasi_kayip":
                kesilmeyen.append(f"{yontem} {yol} → {yanit.status_code}")
    assert kesilmeyen == []


# ============================================================ açık oturum ve kurulum


def test_acik_oturumda_kilit_kapisi_hicbir_ucu_kesmez() -> None:
    for yol in _api_yollari():
        for yontem in YONTEMLER:
            assert _yalniz_kilit_kapisi(yontem, yol).content == b"gecti", f"{yontem} {yol}"


def test_hesap_kurulmadan_kilit_kapisi_gecirir(parolasiz: None) -> None:
    """Kurulum durumunda kişi yazmayı izin sınıfı keser (409), kilit kapısı değil."""
    for yol in _api_yollari():
        assert _yalniz_kilit_kapisi("GET", yol).content == b"gecti", yol


@pytest.mark.parametrize(
    "ortam",
    [
        "acik",
        "kilitli",
        # `parolasiz` burada istenerek yüklenir: varsayılan hesabın satırı ve parmak izi
        # kurulmasın, yoksa durum "kurulum" değil "güvenlik dosyası kayıp" olurdu.
        pytest.param("parolasiz", marks=pytest.mark.hesapsiz),
        "kayip",
    ],
)
def test_saglik_yolu_her_durumda_acik(ortam: str, request: pytest.FixtureRequest) -> None:
    if ortam == "kayip":
        request.getfixturevalue("parmak_izi_yazili")
        app_password.state_path().unlink()
    elif ortam != "acik":
        request.getfixturevalue(ortam)

    for yontem in OKUMA:
        assert _yalniz_kilit_kapisi(yontem, HEALTH_PATH).content == b"gecti"
    # Tam zincirde de açılış sağlık denetimi yanıt alır.
    assert Client().get(HEALTH_PATH).status_code == 200


# ============================================================ boşta kilit uçtan uca (§4.4.3)


@pytest.fixture
def saat() -> SahteSaat:
    """Boşta kilit testleri kurulumu TAMAMLANMIŞ ortamda koşar (D15 ayrı testte)."""
    kurulum_durumunu_yaz(tamam=True)
    saat = SahteSaat()
    oturum_saatini_kur(saat)
    return saat


def _durum(client: Client) -> str:
    durum: str = client.get(OTURUM_UCU).json()["durum"]
    return durum


def test_basliksiz_periyodik_istekler_oturumu_canli_tutmaz(saat: SahteSaat) -> None:
    client = Client()
    assert _durum(client) == "acik"
    for _ in range(BOSTA // 30):  # 30 sn'de bir durum ve pano sorguları, 10 dk boyunca
        saat.ilerlet(30)
        client.get(OTURUM_UCU)
        client.get(HEALTH_PATH)
        client.get("/api/v1/security/status/")
        client.get(VERI_UCU)

    assert _durum(client) == "kilitli"
    assert crypto.is_unlocked() is False
    yanit = client.get(VERI_UCU)
    assert yanit.status_code == 423
    assert yanit.json()["code"] == "locked"


def test_basliksiz_ama_sure_dolmadan_veri_ucu_calisir(saat: SahteSaat) -> None:
    saat.ilerlet(BOSTA - 60)
    assert Client().get(VERI_UCU).status_code == 200


def test_etkinlik_basligi_oturumu_canli_tutar(saat: SahteSaat) -> None:
    client = Client()
    for _ in range(30):  # 30 dk boyunca dakikada bir kullanıcı eylemi (mutlak süre yok)
        saat.ilerlet(60)
        assert client.get(VERI_UCU, headers=ETKINLIK).status_code == 200
    assert _durum(client) == "acik"


def test_bosta_sure_dolduktan_sonra_gelen_etkinlik_dirilmez(saat: SahteSaat) -> None:
    client = Client()
    saat.ilerlet(BOSTA + 1)

    yanit = client.get(VERI_UCU, headers=ETKINLIK)

    assert yanit.status_code == 423
    assert _durum(client) == "kilitli"


def test_reddedilen_istek_etkinligi_tazelemez(saat: SahteSaat, parmak_izi_yazili: str) -> None:
    """Kayıp kilidinde 423 alan başlıklı istek boşta sayacını tazelemez."""
    yol = app_password.state_path()
    yedek = yol.read_bytes()
    yol.unlink()
    saat.ilerlet(BOSTA - 60)
    assert Client().get(VERI_UCU, headers=ETKINLIK).status_code == 423
    yol.write_bytes(yedek)
    saat.ilerlet(61)

    assert _durum(Client()) == "kilitli"


def test_kurulum_surerken_basliksiz_istekler_oturumu_kilitlemez(saat: SahteSaat) -> None:
    """Sihirbazda kurtarma anahtarı ekrandayken süre dolup kilitlenmez (§13 D15)."""
    kurulum_durumunu_yaz(tamam=False)
    client = Client()
    for _ in range(40):  # 40 dk boyunca yalnız başlıksız durum sorguları
        saat.ilerlet(60)
        client.get(OTURUM_UCU)
        assert client.get(VERI_UCU).status_code == 200
    ozet = client.get(OTURUM_UCU).json()
    assert ozet["durum"] == "acik"
    assert ozet["bosta_kalan_sn"] is None  # geri sayım gösterilmez

    kurulum_durumunu_yaz(tamam=True)
    saat.ilerlet(BOSTA)
    assert client.get(VERI_UCU).status_code == 423
    assert OTURUM.acik_mi() is False
