"""Rol kapısı koruma testleri — aile iskeletinin `test_kip_koruma`'sının karşılığı (tasarım §12.B).

Uç listesi ELLE TUTULMAZ: URL desenleri çalışma anında dolaşılır
(`apps/okul/tests/api_gezgini.py`). Her uç × 7 yöntem × 7 rol YALNIZ rol kapısından geçirilir
(görünüm koşmaz, yan etkisi yok); beklenen sonuç kural tablosundandır (`rol_izinleri.KURALLAR`).
Eklenen her yeni uç bu teste kendiliğinden girer ve tabloya bilinçli eklenmedikçe her rolde,
program yöneticisi dahil, kapalıdır. Değişmezler: kilitliyken açık olan her (uç, yöntem) açık
oturumda her role açıktır; hiç kesilmeyen yollar yalnız okumada muaftır; çözülemeyen `/api/`
yolu 403'tür; kapı yalnız açık oturumda keser (kurulum ve güvenlik dosyası kayıp hâllerinde
neyin açık olduğuna kilit kapısı karar verir). Tam zincirde rol başına birkaç duman testi koşar
(`oturumu_ac_test(rol=...)`).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from desktop.server import HEALTH_PATH
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.test import Client, RequestFactory
from django.urls import include, path, resolve
from rest_framework.test import APIClient

from apps.okul import rol_izinleri
from apps.okul.lock_middleware import KILITLI_IZINLI, OKUMA, AppLockMiddleware
from apps.okul.models import Account, AccountRole, AccountStatus
from apps.okul.oturum import OTURUM, SISTEM, Yazar, yazar_olarak
from apps.okul.rol_izinleri import KURALLAR, ROLLER, kural_rolleri
from apps.okul.rol_middleware import HIC_KESILMEYEN_YOLLAR, RolMiddleware
from apps.okul.services import app_password
from apps.okul.tests.api_gezgini import SAGLIK_YOLU, api_desenleri
from apps.okul.tests.hesap_ortak import hesap_ac, muhurle
from apps.okul.tests.oturum_ortak import SahteSaat, kurulum_durumunu_yaz, oturum_saatini_kur
from conftest import oturumu_ac_test
from shared.exceptions import ROL_YETKISIZ_MESAJI

YONTEMLER = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
YAZMA_YONTEMLERI = ("POST", "PUT", "PATCH", "DELETE")
#: Testin uydurma hesap kimliği (rol kapısı yalnız yazarın rolüne bakar).
ORNEK_HESAP = "0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f"
RET_GOVDESI = {"code": "rol_yetkisiz", "message": ROL_YETKISIZ_MESAJI, "fields": {}}


def _gecti(_request: HttpRequest) -> HttpResponse:
    return HttpResponse("gecti")


def _yalniz_rol_kapisi(
    yontem: str, yol: str, rol: str | None, *, kayip: bool = False
) -> HttpResponse:
    """Yalnız rol kapısından geçirir; görünüm KOŞMAZ. Yazar `rol`'ün hesabıdır (None: yok)."""
    istek = RequestFactory().generic(yontem, yol)
    if kayip:
        istek.od_guvenlik_dosyasi_kayip = True  # type: ignore[attr-defined]
    kim = None if rol is None else Yazar(hesap_id=ORNEK_HESAP, rol=rol)
    with yazar_olarak(kim):
        return RolMiddleware(_gecti)(istek)


def _api_uclari() -> list[tuple[str, str]]:
    """(örnek yol, URL adı) — her `/api/` deseni için."""
    return [(ornek, resolve(ornek).view_name) for _, ornek in api_desenleri()]


def _beklenen_roller(uc: str, yontem: str) -> frozenset[str]:
    """Kural tablosundan (kapının kendi tablosundan değil): (uç, yöntem) hangi rollere açık."""
    for kural in KURALLAR:
        if kural.uc == uc and yontem in kural.yontemler:
            return kural_rolleri(kural)
    return frozenset()


def _rol_yetkisiz_mi(yanit: HttpResponse) -> bool:
    return yanit.status_code == 403 and json.loads(yanit.content) == RET_GOVDESI


# ============================================================ yapı


def test_rol_kapisi_kilit_kapisindan_hemen_sonra_durur() -> None:
    """Tasarım §4.4.3: … → RestartRequired (503) → AppLock (423) → RolMiddleware (403)."""
    zincir = list(settings.MIDDLEWARE)
    kilit = zincir.index("apps.okul.lock_middleware.AppLockMiddleware")
    assert zincir[kilit + 1] == "apps.okul.rol_middleware.RolMiddleware"
    assert zincir[-1] == "apps.okul.rol_middleware.RolMiddleware"


def test_dolasma_butun_api_yuzeyini_goruyor() -> None:
    """Boş liste yanlış yeşil verirdi; oturum, bütünlük ve sağlık yolu listede olmalı."""
    adlar = {ad for _, ad in _api_uclari()}
    assert len(adlar) >= 50
    assert {
        "security-session",
        "security-integrity",
        "security-integrity-audit",
        "security-integrity-two-store",
        "setup-status",
    } <= adlar


def test_hic_kesilmeyenler_saglik_yolu_ve_guvenlik_durumudur() -> None:
    assert HEALTH_PATH == SAGLIK_YOLU
    assert {HEALTH_PATH, "/api/v1/security/status/"} == HIC_KESILMEYEN_YOLLAR


# ============================================================ dolaşma


def test_her_rol_her_uc_her_yontem_tabloya_uyar() -> None:
    """Tasarım §4.4.2 "URL desenlerini dolaşan koruma testi": yalnız tabloda açık olan geçer."""
    yanlis: list[str] = []
    denenen = 0
    for ornek, ad in _api_uclari():
        for yontem in YONTEMLER:
            muaf = ornek in HIC_KESILMEYEN_YOLLAR and yontem in OKUMA
            acik = _beklenen_roller(ad, yontem)
            for rol in ROLLER:
                yanit = _yalniz_rol_kapisi(yontem, ornek, rol)
                denenen += 1
                if muaf or rol in acik:
                    if yanit.content != b"gecti":
                        yanlis.append(f"{rol} {yontem} {ad}: kesildi")
                elif not _rol_yetkisiz_mi(yanit):
                    yanlis.append(f"{rol} {yontem} {ad}: kesilmedi ({yanit.status_code})")
    assert denenen > 2000
    assert yanlis == []


def test_kilitliyken_acik_olan_her_uc_acik_oturumda_her_role_aciktir() -> None:
    """Değişmez (plan F1b-2): oturum açmak kilitlemekten az erişim vermez. Açık bir muhasip
    oturumunda kurtarma ucu kapalı olsaydı kullanıcı önce Kilitle'ye basıp aynı uca ulaşırdı."""
    for yol, yontemler in KILITLI_IZINLI.items():
        for yontem in yontemler:
            for rol in ROLLER:
                yanit = _yalniz_rol_kapisi(yontem, yol, rol)
                assert yanit.content == b"gecti", f"{rol} {yontem} {yol}"


def test_hic_kesilmeyenler_yalniz_okumada_muaftir() -> None:
    """Aile dersi: muafiyet yöntemi de sınırlamasaydı bu yollara eklenecek bir yazma yöntemi
    her role açık kalırdı. Okuma dışı yöntemler olağan tablodan geçer (kuralı yok → 403)."""
    for yol in HIC_KESILMEYEN_YOLLAR:
        for yontem in YONTEMLER:
            for rol in ROLLER:
                yanit = _yalniz_rol_kapisi(yontem, yol, rol)
                if yontem in OKUMA:
                    assert yanit.content == b"gecti", f"{rol} {yontem} {yol}"
                else:
                    assert _rol_yetkisiz_mi(yanit), f"{rol} {yontem} {yol}"


@pytest.mark.parametrize("rol", ROLLER)
def test_cozulemeyen_api_yolu_her_rolde_403(rol: str) -> None:
    """Var olmayan uç ile kapalı uç ayırt edilmez (fail-closed); program yöneticisi dahil."""
    assert _rol_yetkisiz_mi(_yalniz_rol_kapisi("GET", "/api/v1/boyle-bir-uc-yok/", rol))


def test_options_her_rolde_kapali_head_get_ile_ayni() -> None:
    for ornek, ad in _api_uclari():
        if ornek in HIC_KESILMEYEN_YOLLAR:
            continue
        for rol in ROLLER:
            assert _rol_yetkisiz_mi(_yalniz_rol_kapisi("OPTIONS", ornek, rol)), (rol, ad)
            get = _yalniz_rol_kapisi("GET", ornek, rol).content == b"gecti"
            head = _yalniz_rol_kapisi("HEAD", ornek, rol).content == b"gecti"
            assert get == head, (rol, ad)


def test_red_govdesi_sabittir_ve_ucu_yankilamaz() -> None:
    yanit = _yalniz_rol_kapisi("PUT", "/api/v1/setup/school-config/", "muhasip")
    assert yanit.status_code == 403
    assert json.loads(yanit.content) == {
        "code": "rol_yetkisiz",
        "message": "Bu işlem hesabınızın rolüne açık değil.",
        "fields": {},
    }
    assert b"school-config" not in yanit.content


def test_api_disi_yollar_kesilmez() -> None:
    """SPA ve statik dosyalar rol kapısının konusu değildir (ekranı ön yüz seçer)."""
    assert _yalniz_rol_kapisi("GET", "/kisiler", "mudur").content == b"gecti"


def test_bilinmeyen_rol_hicbir_yere_giremez() -> None:
    """Rol değeri tanınmıyorsa hiçbir kural eşleşmez (fail-closed)."""
    assert _rol_yetkisiz_mi(_yalniz_rol_kapisi("GET", "/api/v1/school-years/", "admin"))
    assert _yalniz_rol_kapisi("GET", HEALTH_PATH, "admin").content == b"gecti"


# ============================================================ yalnız açık oturumda


def test_yazar_yoksa_kapi_kesmez() -> None:
    """Kurulum, kilitli ya da oturumsuz kayıp: neyin açık olduğuna kilit kapısı karar verdi."""
    for ornek, _ad in _api_uclari():
        assert _yalniz_rol_kapisi("POST", ornek, None).content == b"gecti", ornek


def test_sistem_yazari_reddedilir() -> None:
    """Kilit kapısı istekte yalnız hesap ya da hiçbir şey kurar; `SISTEM` bir isteğin yazarı
    olamaz, rol kapısı onu geçirmez (kayıp kipinde de)."""
    for kayip in (False, True):
        istek = RequestFactory().get("/api/v1/school-years/")
        istek.od_guvenlik_dosyasi_kayip = kayip  # type: ignore[attr-defined]
        with yazar_olarak(SISTEM):
            assert _rol_yetkisiz_mi(RolMiddleware(_gecti)(istek))


def test_kayip_kararinda_kesmez_karari_diskten_yeniden_okumaz(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Güvenlik dosyası kayıpken açık listeyi kilit kapısı tutar; rol kapısı o isteğin kilit
    kapısındaki kararını kullanır, diske yeniden bakmaz (iki okuma arasında dosya silinirse
    olağan kilitte geçmiş bir istek rol kapısını aşmasın)."""
    yol = "/api/v1/backups/restore/"
    assert _yalniz_rol_kapisi("POST", yol, "muhasip", kayip=True).content == b"gecti"
    assert _rol_yetkisiz_mi(_yalniz_rol_kapisi("POST", yol, "muhasip"))
    monkeypatch.setattr(app_password, "security_file_missing", lambda: True)
    assert _rol_yetkisiz_mi(_yalniz_rol_kapisi("POST", yol, "muhasip"))


def test_kilit_kapisi_kayip_kararini_istege_yazar(parmak_izi_yazili: str) -> None:
    gorulen: list[bool] = []

    def gorunum(istek: HttpRequest) -> HttpResponse:
        gorulen.append(getattr(istek, "od_guvenlik_dosyasi_kayip", None) is True)
        return HttpResponse("gecti")

    AppLockMiddleware(gorunum)(RequestFactory().get("/api/v1/security/session/"))
    app_password.state_path().unlink()
    AppLockMiddleware(gorunum)(RequestFactory().get("/api/v1/security/session/"))
    assert gorulen == [False, True]


@pytest.mark.django_db
def test_kilitliyken_once_kilit_kapisi_keser(kilitli: Path) -> None:
    """Kilitliyken istek rol kapısına hiç gelmez: 423, 403 değil."""
    yanit = Client().put("/api/v1/setup/school-config/", {}, content_type="application/json")
    assert yanit.status_code == 423
    assert yanit.json()["code"] == "locked"


@pytest.mark.django_db
def test_kurulumda_rol_kapisi_devrede_degil(parolasiz: Path) -> None:
    """Kurulum durumunda (hesap yok) kişi yazan uçları izin sınıfı keser: 409 `parola_gerekli`
    korunur (tasarım §14 F1b kapısı); rol kapısı yazarsız isteği geçirir."""
    yanit = APIClient().post("/api/v1/personnel/", {}, format="json")
    assert yanit.status_code == 409
    assert yanit.json()["code"] == "parola_gerekli"
    assert APIClient().get("/api/v1/school-years/").status_code == 200


@pytest.mark.django_db
def test_kayip_kilidinde_rol_kapisi_kesmez(parmak_izi_yazili: str) -> None:
    """Muhasip oturumu açıkken güvenlik dosyası kaybolur: kayıp kilidinin çıkış yolları (yedek
    listesi, geri yükleme) rol kapısından da geçer; öteki her şey kilit kapısında 423'tür."""
    oturumu_ac_test(ORNEK_HESAP, tanitici="muhasip", rol="muhasip")
    app_password.state_path().unlink()
    client = APIClient()

    assert client.get("/api/v1/backups/").status_code == 200
    geri_yukleme = client.post("/api/v1/backups/restore/", {}, format="json")
    # Gövde eksik: görünüm doğrulamayla reddeder — kapılardan geçtiğinin kanıtı.
    assert geri_yukleme.status_code == 400, geri_yukleme.content
    veri = client.get("/api/v1/school-years/")
    assert veri.status_code == 423
    assert veri.json()["code"] == "guvenlik_dosyasi_kayip"


# ============================================================ kısıtlı roller (§14 F1b kapısı)


#: Rolün bugün yazabildiği satırlar (tasarım §14 F1b: "DK yalnız denetim modülüne, müdür yalnız
#: kendi yazılarına yazar"). Kendi hesabı ve oturum satırları her roldedir; DK'nin denetim
#: modülündeki ilk ucu geri yükleme kartının "Gördüm"üdür (M8, F1b-2 (c)); müdürün yazıları
#: sonraki fazlardadır.
#: Müdürün yazıları M3 (¹), M6 (⁴) ve müdür yazısı (⁶) satırlarındadır. M10 (gelen-giden evrak)
#: burada YOKTUR: hücresi O⁷'dir, müdürün yazısını evrak defterine program işler (yazının
#: eyleminin yan etkisi; ucu yoktur) — müdüre açılan bir M10 yazma ucu bu testi düşürür.
_KISITLI_ROLUN_SATIRLARI = {
    AccountRole.DENETLEME_KURULU.value: {
        rol_izinleri.Satir.KENDI,
        rol_izinleri.Satir.OTURUM,
        rol_izinleri.Satir.M8,
    },
    AccountRole.MUDUR.value: {
        rol_izinleri.Satir.KENDI,
        rol_izinleri.Satir.OTURUM,
        rol_izinleri.Satir.M3,
        rol_izinleri.Satir.M6,
        rol_izinleri.Satir.MUDUR_YAZISI,
    },
}


@pytest.mark.parametrize("rol", ["denetleme_kurulu", "mudur"])
def test_kisitli_roller_yalniz_kendi_satirlarina_yazar(rol: str) -> None:
    """Tasarım §14 F1b kapısı ve §4.4.2 Testler: Denetleme Kurulu yalnız denetim modülüne,
    müdür yalnız kendi yazılarına yazar (olumsuz yarı F1b'de bütün uçlarda sınanır; olumlu
    yarı uçlarıyla gelir). Bu rollere açık her yazma (POST/PUT/PATCH/DELETE) kendi satırındadır;
    öteki her uçta her yazma yöntemi rol kapısında 403'tür."""
    izinli = _KISITLI_ROLUN_SATIRLARI[rol]
    for kural in KURALLAR:
        if rol in kural_rolleri(kural) and set(kural.yontemler) & set(YAZMA_YONTEMLERI):
            assert kural.satir in izinli, (rol, kural.uc)
    acik_yazma = set()
    for ornek, ad in _api_uclari():
        for yontem in YAZMA_YONTEMLERI:
            if _yalniz_rol_kapisi(yontem, ornek, rol).content == b"gecti":
                acik_yazma.add(ad)
    # Bugün açık olanlar kendi hesabı ve oturum uçlarıdır; DK'de ek olarak denetim modülünün
    # (M8) "Gördüm"ü, görev bölümü (F1c 6. adım) ve görev bölümü tutanağı ile denetim planının
    # belgesi (E02, F1c 10. adım).
    # Gerekçe kutusunun yarım metni (F1c 11. adım) de hesabın kendi satırındadır (KENDI).
    ortak = {
        "app-quit",
        "oab-draft-text",
        "security-change-password",
        "security-integrity-reset-notice",
        "security-lock",
        "security-recover",
        "security-unlock",
    }
    ek = (
        {"security-integrity-restore-seen", "oab-dk-duty-assignment", "oab-document-e02"}
        if rol == AccountRole.DENETLEME_KURULU
        else set()
    )
    assert acik_yazma == ortak | ek


# ============================================================ tam zincir dumanları


def _oturum(rol: str, hesap_id: str = ORNEK_HESAP) -> APIClient:
    oturumu_ac_test(hesap_id, tanitici=rol, rol=rol)
    return APIClient()


@pytest.mark.django_db
def test_muhasip_okul_kartini_okur_yazamaz() -> None:
    client = _oturum("muhasip")
    assert client.get("/api/v1/school-years/").status_code == 200
    assert client.get("/api/v1/setup/school-config/").status_code == 200
    yanit = client.put("/api/v1/setup/school-config/", {}, format="json")
    assert yanit.status_code == 403
    assert yanit.json() == RET_GOVDESI
    # Kişiler: personeli her rol okur; şablon, havuz ve yazmalar yalnız program yöneticisinin.
    assert client.get("/api/v1/personnel/").status_code == 200
    assert client.get("/api/v1/templates/personnel/").status_code == 403
    assert client.post("/api/v1/personnel/", {}, format="json").status_code == 403


@pytest.mark.django_db
def test_butunluk_uclari_rol_suzmesi() -> None:
    """Kendi kartları her rol; denetim kartları program yöneticisi ve DK; iki depo kartı yalnız
    program yöneticisi (plan F1b-2 "Bütünlük ucu bölünür")."""
    beklenen = {
        "yonetici": (200, 200, 200),
        "muhasip": (200, 403, 403),
        "denetleme_kurulu": (200, 200, 403),
        "mudur": (200, 403, 403),
    }
    for rol, kodlar in beklenen.items():
        client = _oturum(rol)
        gercek = tuple(
            client.get(f"/api/v1/security/integrity/{ek}").status_code
            for ek in ("", "audit/", "two-store/")
        )
        assert gercek == kodlar, rol
    yanit = _oturum("denetleme_kurulu").post(
        "/api/v1/security/integrity/orphan-wraps/", {"hesaplar": [ORNEK_HESAP]}, format="json"
    )
    assert yanit.status_code == 403


@pytest.mark.django_db
def test_son_oturum_kartini_yonetim_kurulu_kapatir_dk_ve_mudur_kapatamaz() -> None:
    """Pano satırı M9: program yöneticisi ve YK rolleri Y, DK ve müdür O."""
    for rol, kod in (("baskan", 200), ("sekreter", 200), ("denetleme_kurulu", 403), ("mudur", 403)):
        client = _oturum(rol)
        assert client.get("/api/v1/dashboard/last-session/").status_code == 200, rol
        assert client.post("/api/v1/dashboard/last-session/").status_code == kod, rol


@pytest.mark.django_db
def test_mudur_geri_yukleyemez_yonetici_ilk_hesabi_yeniden_kuramaz() -> None:
    assert _oturum("mudur").post("/api/v1/backups/restore/", {}, format="json").status_code == 403
    yanit = _oturum("yonetici").post("/api/v1/security/enable/", {}, format="json")
    assert yanit.status_code == 403
    assert yanit.json()["code"] == "rol_yetkisiz"


@pytest.mark.django_db
def test_oturum_ozeti_rolun_yeteneklerini_tasir() -> None:
    """Ön yüz süzmesinin tek kaynağı: oturum özetindeki `hesap.yetenekler` (plan F1b-2)."""
    for rol in ROLLER:
        hesap = _oturum(rol).get("/api/v1/security/session/").json()["hesap"]
        assert hesap["rol"] == rol
        assert hesap["yetenekler"] == rol_izinleri.yetenekler(rol)
    assert "butunluk_denetim" in rol_izinleri.yetenekler("denetleme_kurulu")
    assert "iki_depo" not in rol_izinleri.yetenekler("denetleme_kurulu")


@pytest.fixture
def saat() -> Iterator[SahteSaat]:
    kurulum_durumunu_yaz(tamam=True)
    saat = SahteSaat()
    oturum_saatini_kur(saat)
    yield saat


@pytest.mark.django_db
def test_rol_reddi_etkinlik_tazelemesini_geri_almaz(saat: SahteSaat) -> None:
    """Kilit kapısı başlıklı isteği sayaca yazar; rol kapısındaki ret bunu geri almaz
    (kullanıcının tıklaması gerçek bir etkinliktir; plan F1b-2)."""
    client = _oturum("muhasip")
    bosta = 10 * 60
    saat.ilerlet(bosta - 60)
    yanit = client.put(
        "/api/v1/setup/school-config/", {}, format="json", headers={"X-OD-Etkinlik": "1"}
    )
    assert yanit.status_code == 403
    saat.ilerlet(120)
    assert client.get("/api/v1/security/session/").json()["durum"] == "acik"
    assert OTURUM.acik_mi()


# ============================================================ acknowledge_reset_notice (her rol)


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [AccountRole.MUHASIP, AccountRole.DENETLEME_KURULU])
def test_parola_bildirimini_her_rol_kapatir(rol: str) -> None:
    """Regresyon (plan F1b-2): hesap yönetimine rol denetimi gelince sahibinin kendi parola
    yenilenme bildirimini kapatması her rolde açık kalır (uç ve servis)."""
    hesap = hesap_ac(rol, ad="Örnek Hesap")
    # Meşru yazım gibi satır ve iz satırı birlikte (satırın izi tutmalı; `muhurle`).
    hesap = muhurle(
        Account.objects.get(pk=hesap.id), status=AccountStatus.ACIK, reset_notice_pending=True
    )
    client = _oturum(str(rol), str(hesap.id))

    yanit = client.post("/api/v1/security/integrity/reset-notice/", {}, format="json")

    assert yanit.status_code == 200, yanit.content
    assert Account.objects.get(pk=hesap.id).reset_notice_pending is False


# ============================================================ yeni uç varsayılan kapalı


def _ornek_gorunum(_request: HttpRequest) -> HttpResponse:
    return HttpResponse("yeni")


#: Bu modül bir URL yapılandırmasıdır da (`ROOT_URLCONF` geçersiz kılınınca): gerçek API'nin
#: yanına kurala yazılmamış yeni bir uç eklenir.
urlpatterns: list[Any] = [
    path("api/v1/", include("apps.okul.urls")),
    path("api/v1/yeni-uc/", _ornek_gorunum, name="yeni-uc"),
]


def test_yeni_uc_program_yoneticisi_icin_de_kapali(settings: Any) -> None:
    """Tabloya bilinçli eklenmeyen uç her rolde kapalıdır: `yonetici` süper kullanıcı değildir,
    yalnız Y olduğu satırda yazar (tasarım §4.4.2 "Bağlayıcılık")."""
    settings.ROOT_URLCONF = __name__
    assert resolve("/api/v1/yeni-uc/").view_name == "yeni-uc"
    for rol in ROLLER:
        for yontem in YONTEMLER:
            assert _rol_yetkisiz_mi(_yalniz_rol_kapisi(yontem, "/api/v1/yeni-uc/", rol)), rol
    # Gerçek API aynı yapılandırmada açık kalır.
    assert _yalniz_rol_kapisi("GET", "/api/v1/school-years/", "yonetici").content == b"gecti"
