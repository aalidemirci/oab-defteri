"""Oturum uçları (`views_oturum`; tasarım §4.4.3, TK14; plan F1b-1 "Oturum") — uçtan uca.

İstekler tam ara katman zincirinden geçer (yeniden başlat → kilit ve oturum). Varsayılan
ortam `backend/conftest.py`'dedir: oturum program yöneticisi hesabıyla açık. Kilit
açan testler `yonetici_hesabi` fixtürüyle `Account` satırını ve iz anahtarını kurar.
Hesap adları uydurmadır; hiçbir yanıtta ad-soyad yoktur (kilit ekranı kişi adı
göstermez, tasarım §4.4.3).
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from desktop.tests.kap_ortak import durum_basligi, kap_kur
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul.models import Account, AccountRole, AccountStatus, SchoolConfig, SuspendReason
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password, backup_restore, hesaplar
from apps.okul.services import setup as setup_service
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    UCUNCU_PAROLA,
    YENI_PAROLA,
    durum,
    durum_yaz,
    hesap_ac,
    muhurle,
)
from conftest import (
    TEST_DEK,
    TEST_HESAP_ADI,
    TEST_HESAP_ID,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
    TEST_TANITICI,
)
from shared import bakim, crypto

pytestmark = pytest.mark.django_db

OTURUM_UCU = "/api/v1/security/session/"
HESAPLAR_UCU = "/api/v1/security/accounts/"
ACMA_UCU = "/api/v1/security/unlock/"
KILITLE_UCU = "/api/v1/security/lock/"
KURTARMA_UCU = "/api/v1/security/recover/"
PAROLA_UCU = "/api/v1/security/change-password/"
BOSTA_KILIT_UCU = "/api/v1/security/idle-lock/"
VERI_UCU = "/api/v1/school-years/"
MUHASIP_ADI = "Örnek Muhasip"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _govde(yanit: Any) -> dict[str, Any]:
    veri: dict[str, Any] = yanit.json()
    return veri


def _liste(yanit: Any) -> list[dict[str, Any]]:
    veri: list[dict[str, Any]] = yanit.json()
    return veri


def _ac(client: APIClient, hesap: object, parola: str, yeni: str | None = None) -> Any:
    govde: dict[str, Any] = {"hesap": str(hesap), "parola": parola}
    if yeni is not None:
        govde["yeni_parola"] = yeni
    return client.post(ACMA_UCU, govde, format="json")


# ============================================================ oturum özeti


def test_oturum_ozetinin_anahtarlari_sabittir(client: APIClient) -> None:
    """Ön yüz `security/session/` yanıtını bu anahtarlarla okur (alt commit b)."""
    veri = _govde(client.get(OTURUM_UCU))

    assert sorted(veri) == [
        "bosta_dk",
        "bosta_kalan_sn",
        "durum",
        "hesap",
        "kilit_bekliyor",
        "kurulum_tamam",
        "yukleme_siniri_mb",
    ]
    assert veri["durum"] == "acik"
    assert veri["hesap"] == {
        "id": TEST_HESAP_ID,
        "tanitici": TEST_TANITICI,
        "rol": "yonetici",
        "rol_etiketi": "Program yöneticisi",
        # Ön yüz süzmesinin tek kaynağı (plan F1b-2; `rol_izinleri.YETENEKLER`).
        "yetenekler": [
            "ayrilis_havuzu",
            "birlik_donemi_yazma",
            "birlik_kisi_yazma",
            "bosta_sure_yazma",
            "butunluk_denetim",
            "ders_yili_yazma",
            "eokul_aktarimi",
            "erisim_gunlugu",
            "guncelleme",
            "guvenlik",
            "iki_depo",
            "kapali_gun_yazma",
            "karar_taslagi_uretme",
            "kisi_yazma",
            "kullanicilar",
            "kurulum_tamamlama",
            "okul_karti_yazma",
            "organ_yazma",
            "son_oturum_onay",
            "temsilci_yazma",
            "veli_listesi",
            "yol_haritasi",
        ],
    }
    assert veri["bosta_dk"] == 10
    assert veri["kilit_bekliyor"] is False


def test_oturum_ozeti_kisi_adi_tasimaz(client: APIClient, yonetici_hesabi: Account) -> None:
    assert TEST_HESAP_ADI not in client.get(OTURUM_UCU).content.decode("utf-8")


def test_kilitliyken_oturum_ozeti_yanit_verir(client: APIClient, kilitli: None) -> None:
    yanit = client.get(OTURUM_UCU)

    assert yanit.status_code == 200
    assert _govde(yanit)["durum"] == "kilitli"
    assert _govde(yanit)["hesap"] is None
    assert _govde(yanit)["bosta_kalan_sn"] is None


def test_oturum_ozeti_yukleme_sinirini_ayardan_verir(client: APIClient, settings: Any) -> None:
    """Ekran sınırı aşan düz dosyayı göndermez; değer ayardan gelir (kullanıcı kararı 05.11.2026)."""
    settings.MAX_UPLOAD_SIZE_MB = 7

    assert _govde(client.get(OTURUM_UCU))["yukleme_siniri_mb"] == 7


def test_hesap_kurulmadan_oturum_ozeti_kurulum_der(client: APIClient, parolasiz: None) -> None:
    veri = _govde(client.get(OTURUM_UCU))
    assert (veri["durum"], veri["hesap"], veri["kurulum_tamam"]) == ("kurulum", None, False)


def test_kip_uclari_kaldirildi(client: APIClient) -> None:
    """Görevli kipi ve uçları söküldü (tasarım §12.B): ne adla ne adresle çözülür."""
    for ad in ("security-mode", "security-mode-staff", "security-mode-admin"):
        with pytest.raises(NoReverseMatch):
            reverse(ad)
    # Açık oturumda çözülemeyen `/api/` yolu rol kapısında 403'tür (var olmayan uç ile kapalı
    # uç ayırt edilmez; `test_rol_koruma.py`).
    for yanit in (
        client.get("/api/v1/security/mode/"),
        client.post("/api/v1/security/mode/admin/", {}, format="json"),
    ):
        assert yanit.status_code == 403
        assert yanit.json()["code"] == "rol_yetkisiz"


# ============================================================ kilit ekranının hesap listesi


def test_hesap_listesi_tanitici_ve_rol_etiketi_verir(
    client: APIClient, yonetici_hesabi: Account
) -> None:
    yanit = client.get(HESAPLAR_UCU)

    assert yanit.status_code == 200
    assert _liste(yanit) == [
        {
            "id": TEST_HESAP_ID,
            "tanitici": TEST_TANITICI,
            "rol": "yonetici",
            "rol_etiketi": "Program yöneticisi",
            "secilebilir": True,
            "askida_nedeni": None,
        }
    ]


def test_hesap_listesi_kilitliyken_acik_ve_kisi_adi_tasimaz(
    client: APIClient, yonetici_hesabi: Account
) -> None:
    hesap_ac(ad=MUHASIP_ADI)
    app_password.lock()

    yanit = client.get(HESAPLAR_UCU)

    assert yanit.status_code == 200
    metin = yanit.content.decode("utf-8")
    assert TEST_HESAP_ADI not in metin and MUHASIP_ADI not in metin
    assert {anahtar for h in _liste(yanit) for anahtar in h} == {
        "id",
        "tanitici",
        "rol",
        "rol_etiketi",
        "secilebilir",
        "askida_nedeni",
    }
    # Parola yenilenmeli hesap seçilebilir: kilit açma yeni parolayı birlikte ister.
    muhasip = next(h for h in _liste(yanit) if h["rol"] == "muhasip")
    assert (muhasip["rol_etiketi"], muhasip["secilebilir"]) == ("Muhasip", True)


def test_hesap_listesi_rol_sirasiyla_ve_ayni_rolde_sira_noyla(
    client: APIClient, yonetici_hesabi: Account
) -> None:
    hesap_ac(AccountRole.DENETLEME_KURULU, tanitici="dk-1", ad="Örnek Denetçi Bir")
    hesap_ac(AccountRole.DENETLEME_KURULU, tanitici="dk-2", ad="Örnek Denetçi İki")
    hesap_ac(AccountRole.MUHASIP)

    satirlar = _liste(client.get(HESAPLAR_UCU))

    assert [(h["tanitici"], h["rol_etiketi"]) for h in satirlar] == [
        (TEST_TANITICI, "Program yöneticisi"),
        ("muhasip", "Muhasip"),
        ("dk-1", "Denetleme Kurulu 1"),
        ("dk-2", "Denetleme Kurulu 2"),
    ]


def test_iki_kaynaktan_askidaki_hesap_secilemez(
    client: APIClient, yonetici_hesabi: Account
) -> None:
    """Hatalı deneme askısı (`guvenlik.json`) ve `Account.status = ASKIDA` (plan F1b-1)."""
    muhasip = hesap_ac()
    sekreter = hesap_ac(AccountRole.SEKRETER, ad="Örnek Sekreter")
    veri = durum()
    for sarmal in veri["hesaplar"]:
        if sarmal["id"] == str(muhasip.id):
            sarmal["askida"] = True
    durum_yaz(veri)
    muhurle(sekreter, status=AccountStatus.ASKIDA, suspend_reason=SuspendReason.UYELIK_DUSTU)

    satirlar = {h["rol"]: h for h in _liste(client.get(HESAPLAR_UCU))}

    assert (satirlar["muhasip"]["secilebilir"], satirlar["muhasip"]["askida_nedeni"]) == (
        False,
        hesaplar.HATALI_DENEME_ASKISI,
    )
    assert (satirlar["sekreter"]["secilebilir"], satirlar["sekreter"]["askida_nedeni"]) == (
        False,
        "UYELIK_DUSTU",
    )
    assert satirlar["yonetici"]["secilebilir"] is True


def test_kapali_hesabin_kalan_sarmali_listelenmez(
    client: APIClient, yonetici_hesabi: Account
) -> None:
    muhasip = hesap_ac()
    muhurle(muhasip, status=AccountStatus.KAPALI, closed_at=timezone.now())  # sarmal duruyor

    kimlikler = [h["id"] for h in _liste(client.get(HESAPLAR_UCU))]

    assert str(muhasip.id) not in kimlikler


def test_rolu_okunamayan_sarmal_secilemez(client: APIClient, yonetici_hesabi: Account) -> None:
    """Plan F1b-1: "rolü veritabanından okunamayan satır açılmaz"."""
    veri = durum()
    sahte = dict(veri["hesaplar"][0])
    satirsiz = str(uuid.uuid4())
    veri["hesaplar"].append({**sahte, "id": satirsiz, "tanitici": "eski-hesap"})
    veri["hesaplar"].append({**sahte, "id": "bicimsiz", "tanitici": "bozuk"})
    durum_yaz(veri)

    satirlar = _liste(client.get(HESAPLAR_UCU))

    assert [(h["id"], h["rol"], h["rol_etiketi"], h["secilebilir"]) for h in satirlar[1:]] == [
        (satirsiz, None, "Hesap kaydı okunamadı", False),
        ("bicimsiz", None, "Hesap kaydı okunamadı", False),
    ]


def test_guvenlik_dosyasi_yoksa_liste_bostur(yonetici_hesabi: Account) -> None:
    app_password.state_path().unlink()
    assert hesaplar.lock_screen_accounts() == []
    assert app_password.account_wraps() == []


# ============================================================ kilit açma


def test_kilit_acma_secilen_hesapla_oturum_acar(
    client: APIClient, yonetici_hesabi: Account
) -> None:
    muhasip = hesap_ac(ad=MUHASIP_ADI)
    client.post(KILITLE_UCU)

    yenilenmeli = _ac(client, muhasip.id, GECICI_PAROLA)
    assert yenilenmeli.status_code == 409
    assert _govde(yenilenmeli)["code"] == "parola_yenilenmeli"
    assert "parola_yenilenmeli" not in _govde(yenilenmeli)["message"]
    assert client.get(VERI_UCU).status_code == 423  # oturum açılmadı

    yanit = _ac(client, muhasip.id, GECICI_PAROLA, YENI_PAROLA)

    assert yanit.status_code == 200, yanit.content
    assert _govde(yanit)["durum"] == "acik"
    assert _govde(yanit)["hesap"]["id"] == str(muhasip.id)
    assert _govde(yanit)["hesap"]["rol_etiketi"] == "Muhasip"
    assert MUHASIP_ADI not in yanit.content.decode("utf-8")
    assert client.get(VERI_UCU).status_code == 200


def test_yanlis_parola_400_ve_iletide_kod_yok(client: APIClient, yonetici_hesabi: Account) -> None:
    client.post(KILITLE_UCU)

    yanit = _ac(client, TEST_HESAP_ID, "Yanlis-Parola-9")

    assert yanit.status_code == 400
    assert _govde(yanit) == {"code": "parola_yanlis", "message": "Parola hatalı.", "fields": {}}
    assert "Yanlis-Parola-9" not in yanit.content.decode("utf-8")
    assert OTURUM.acik_mi() is False


def test_eski_govde_anahtarlari_kabul_edilmez(client: APIClient, kilitli: None) -> None:
    """Oturum sözleşmesi Türkçe anahtarlıdır (`hesap`, `parola`)."""
    yanit = client.post(
        ACMA_UCU, {"hesap_id": TEST_HESAP_ID, "password": TEST_PAROLA}, format="json"
    )
    assert yanit.status_code == 400
    assert set(_govde(yanit)["fields"]) == {"hesap", "parola"}


# ============================================================ Kilitle


def test_kilitle_oturumu_kapatir_ve_dek_duser(client: APIClient) -> None:
    yanit = client.post(KILITLE_UCU)

    assert yanit.status_code == 200
    assert (_govde(yanit)["sonuc"], _govde(yanit)["durum"]) == ("kilitlendi", "kilitli")
    assert crypto.is_unlocked() is False
    assert client.get(VERI_UCU).status_code == 423


def test_kilitliyken_kilitle_kilit_kapisinda_423(client: APIClient, kilitli: None) -> None:
    yanit = client.post(KILITLE_UCU)
    assert yanit.status_code == 423
    assert _govde(yanit)["code"] == "locked"


def test_uzun_is_surerken_kilitle_ertelenir(client: APIClient) -> None:
    with bakim.UZUN_ISLER.is_():
        yanit = client.post(KILITLE_UCU)
        assert yanit.status_code == 200
        assert _govde(yanit)["sonuc"] == "ertelendi"
        assert _govde(yanit)["durum"] == "acik"
        assert _govde(yanit)["kilit_bekliyor"] is True
        assert client.get(VERI_UCU).status_code == 200  # iş sürerken oturum açık
    # İş bitti: ilk istekte kilit uygulanır.
    assert client.get(VERI_UCU).status_code == 423
    assert crypto.is_unlocked() is False


# ============================================================ kurtarma anahtarıyla açılış


def test_kurtarma_ucu_program_yoneticisinin_oturumunu_acar(
    client: APIClient, yonetici_hesabi: Account, kilitli: None
) -> None:
    yanit = client.post(
        KURTARMA_UCU,
        {
            "kurtarma_anahtari": TEST_KURTARMA_ANAHTARI,
            "hesap": TEST_HESAP_ID,
            "yeni_parola": YENI_PAROLA,
        },
        format="json",
    )

    assert yanit.status_code == 200, yanit.content
    assert _govde(yanit)["hesap"]["id"] == TEST_HESAP_ID
    assert TEST_KURTARMA_ANAHTARI not in yanit.content.decode("utf-8")


def test_kurtarma_ucu_baska_rolu_acmaz(client: APIClient, yonetici_hesabi: Account) -> None:
    muhasip = hesap_ac()
    app_password.lock()

    yanit = client.post(
        KURTARMA_UCU,
        {
            "kurtarma_anahtari": TEST_KURTARMA_ANAHTARI,
            "hesap": str(muhasip.id),
            "yeni_parola": YENI_PAROLA,
        },
        format="json",
    )

    assert yanit.status_code == 400
    assert "program yöneticisi" in _govde(yanit)["message"]
    assert OTURUM.acik_mi() is False


def test_kurtarma_listesi_yalniz_program_yoneticilerini_verir(
    client: APIClient, yonetici_hesabi: Account
) -> None:
    """`GET security/recover/`: kilitliyken açık; tanıtıcı + rol etiketi, kişi adı yok."""
    hesap_ac(ad=MUHASIP_ADI)
    ikinci = hesap_ac(AccountRole.YONETICI, ad="Örnek İkinci Yönetici")
    kapali = hesap_ac(AccountRole.YONETICI, tanitici="eski-yonetici", ad="Örnek Eski Yönetici")
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=kapali.id)
    app_password.lock()

    yanit = client.get(KURTARMA_UCU)

    assert yanit.status_code == 200
    assert _liste(yanit) == [
        {
            "id": TEST_HESAP_ID,
            "tanitici": TEST_TANITICI,
            "rol_etiketi": "Program yöneticisi",
            "sarmali_var": True,
        },
        {
            "id": str(ikinci.id),
            "tanitici": "yonetici-2",
            "rol_etiketi": "Program yöneticisi",
            "sarmali_var": True,
        },
    ]
    metin = yanit.content.decode("utf-8")
    assert TEST_HESAP_ADI not in metin and "Örnek İkinci" not in metin


def test_kurtarma_ucu_taniticiyi_da_kabul_eder(
    client: APIClient, yonetici_hesabi: Account, kilitli: None
) -> None:
    yanit = client.post(
        KURTARMA_UCU,
        {
            "kurtarma_anahtari": TEST_KURTARMA_ANAHTARI,
            "hesap": TEST_TANITICI,
            "yeni_parola": YENI_PAROLA,
        },
        format="json",
    )

    assert yanit.status_code == 200, yanit.content
    assert _govde(yanit)["hesap"]["id"] == TEST_HESAP_ID


def test_kurtarmayla_geri_yuklemeden_sonra_program_yoneticisi_arayuzden_acar(
    client: APIClient, yonetici_hesabi: Account, tmp_path: Path
) -> None:
    """TK10, tasarım §4.4.4: yeni bilgisayara taşıma ya da kayıp kilidinden çıkış.

    Yedek kurtarma anahtarıyla geri yüklenir; `guvenlik.json` yalnız kurtarma bölümünü
    taşır (`hesaplar` boş). Program yeniden açılınca kilit ekranı listesi boştur;
    kurtarma listesi program yöneticisini verir, kurtarma ucu onu açar ve sarmalı kurar.
    """
    hesap_ac(ad=MUHASIP_ADI)
    kaynak = tmp_path / "kaynak.sqlite3"
    with closing(sqlite3.connect(kaynak)) as baglanti:
        baglanti.execute("CREATE TABLE kayit (deger TEXT)")
        baglanti.commit()
    yedek = tmp_path / "tasima.odbak"
    yedek.write_bytes(
        kap_kur(kaynak.read_bytes(), TEST_DEK, baslik=durum_basligi(app_password.read_state()))
    )
    app_password.lock()
    app_password.state_path().unlink()  # yeni bilgisayar: güvenlik dosyası yok

    sonuc = backup_restore.restore_database(
        yedek, tmp_path / "hedef" / "db.sqlite3", recovery_key=TEST_KURTARMA_ANAHTARI
    )

    assert sonuc.state_written is True
    assert _govde(client.get(OTURUM_UCU))["durum"] == "kilitli"
    assert _liste(client.get(HESAPLAR_UCU)) == []
    kurtarilabilir = _liste(client.get(KURTARMA_UCU))
    assert kurtarilabilir == [
        {
            "id": TEST_HESAP_ID,
            "tanitici": TEST_TANITICI,
            "rol_etiketi": "Program yöneticisi",
            "sarmali_var": False,
        }
    ]

    yanit = client.post(
        KURTARMA_UCU,
        {
            "kurtarma_anahtari": TEST_KURTARMA_ANAHTARI,
            "hesap": kurtarilabilir[0]["id"],
            "yeni_parola": YENI_PAROLA,
        },
        format="json",
    )

    assert yanit.status_code == 200, yanit.content
    assert _govde(yanit)["hesap"]["id"] == TEST_HESAP_ID
    client.post(KILITLE_UCU)
    assert [h["id"] for h in _liste(client.get(HESAPLAR_UCU))] == [TEST_HESAP_ID]
    assert _liste(client.get(KURTARMA_UCU))[0]["sarmali_var"] is True
    assert _ac(client, TEST_HESAP_ID, YENI_PAROLA).status_code == 200


# ============================================================ kendi parolasını değiştirme


def test_parola_degistirme_acik_oturumda_kendi_parolasiyla(
    client: APIClient, yonetici_hesabi: Account
) -> None:
    yanit = client.post(
        PAROLA_UCU, {"parola": TEST_PAROLA, "yeni_parola": YENI_PAROLA}, format="json"
    )

    assert yanit.status_code == 200, yanit.content
    assert _govde(yanit)["hesap"]["id"] == TEST_HESAP_ID  # oturum aynı hesapta sürer
    client.post(KILITLE_UCU)
    assert _ac(client, TEST_HESAP_ID, YENI_PAROLA).status_code == 200


def test_parola_degistirmede_baska_hesabin_parolasi_gecmez(
    client: APIClient, yonetici_hesabi: Account
) -> None:
    """Plan F1b-1: parola oturumdaki hesabınkine karşı doğrulanır."""
    muhasip = hesap_ac()
    assert _ac(client, muhasip.id, GECICI_PAROLA, YENI_PAROLA).status_code == 200

    yanit = client.post(
        PAROLA_UCU, {"parola": TEST_PAROLA, "yeni_parola": UCUNCU_PAROLA}, format="json"
    )

    assert yanit.status_code == 400
    assert _govde(yanit)["code"] == "parola_yanlis"
    yanit = client.post(
        PAROLA_UCU, {"parola": YENI_PAROLA, "yeni_parola": UCUNCU_PAROLA}, format="json"
    )
    assert yanit.status_code == 200
    assert _govde(yanit)["hesap"]["id"] == str(muhasip.id)


def test_parola_degistirme_servisi_oturum_olmadan_reddeder(
    yonetici_hesabi: Account, kilitli: None
) -> None:
    with pytest.raises(app_password.AppPasswordError, match="kilitli"):
        app_password.change_password(
            hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
        )


# ============================================================ boşta kilit süresi (TK14, §13 D11)


def test_bosta_kilit_suresi_varsayilani_10_dakikadir(client: APIClient) -> None:
    """Satır yokken alanın kendi varsayılanı; oturum özetindeki `bosta_dk` ile aynı kaynak."""
    yanit = client.get(BOSTA_KILIT_UCU)

    assert yanit.status_code == 200
    assert _govde(yanit) == {"dakika": 10}
    assert _govde(client.get(OTURUM_UCU))["bosta_dk"] == 10


def test_bosta_kilit_suresi_yazilir_ve_oturum_hemen_uygular(client: APIClient) -> None:
    """Kayıt oturumun önbelleğini boşaltır: yeni süre yeniden başlatmadan geçerlidir."""
    assert _govde(client.get(OTURUM_UCU))["bosta_dk"] == 10  # önbelleğe alınır

    yanit = client.put(BOSTA_KILIT_UCU, {"dakika": 3}, format="json")

    assert yanit.status_code == 200, yanit.content
    assert _govde(yanit) == {"dakika": 3}
    assert SchoolConfig.load().idle_lock_minutes == 3
    assert _govde(client.get(BOSTA_KILIT_UCU)) == {"dakika": 3}
    assert _govde(client.get(OTURUM_UCU))["bosta_dk"] == 3
    assert client.put(BOSTA_KILIT_UCU, {"dakika": 30}, format="json").status_code == 200
    assert _govde(client.get(OTURUM_UCU))["bosta_dk"] == 30


@pytest.mark.parametrize("deger", [2, 31, 0, -5, 1000])
def test_bosta_kilit_suresi_aralik_disinda_reddedilir(client: APIClient, deger: int) -> None:
    yanit = client.put(BOSTA_KILIT_UCU, {"dakika": deger}, format="json")

    assert yanit.status_code == 400
    assert _govde(yanit)["message"] == "Boşta kilit süresi 3 ile 30 dakika arasında olmalıdır."
    assert SchoolConfig.load().idle_lock_minutes == 10


@pytest.mark.parametrize("deger", ["on", "", True, 7.5, [5]])
def test_bosta_kilit_suresi_tam_sayi_ister(client: APIClient, deger: object) -> None:
    yanit = client.put(BOSTA_KILIT_UCU, {"dakika": deger}, format="json")

    assert yanit.status_code == 400
    assert _govde(yanit)["message"] == "Boşta kilit süresi tam sayı (dakika) olmalıdır."
    assert SchoolConfig.load().idle_lock_minutes == 10


@pytest.mark.parametrize("govde", [{}, {"dakika": None}], ids=["alansiz", "bos_deger"])
def test_bosta_kilit_suresi_degersiz_reddedilir(client: APIClient, govde: dict[str, Any]) -> None:
    """Alan adı olmadan anlamsız ret alanın altında durur (`fields`; ön yüz formu gösterir)."""
    yanit = client.put(BOSTA_KILIT_UCU, govde, format="json")

    assert yanit.status_code == 400
    assert _govde(yanit)["fields"]["dakika"] == ["Boşta kilit süresini dakika olarak girin."]
    assert SchoolConfig.load().idle_lock_minutes == 10


def test_bosta_kilit_suresi_kilitliyken_423(client: APIClient, kilitli: None) -> None:
    """Kilit ekranının açık listesinde değildir: kilitliyken ne okunur ne yazılır."""
    for yanit in (
        client.get(BOSTA_KILIT_UCU),
        client.put(BOSTA_KILIT_UCU, {"dakika": 5}, format="json"),
    ):
        assert yanit.status_code == 423
        assert _govde(yanit)["code"] == "locked"
    assert SchoolConfig.load().idle_lock_minutes == 10


def test_bosta_kilit_suresi_hesap_kurulmadan_yazilmaz(client: APIClient, parolasiz: None) -> None:
    """Kurulum durumunda kilit kapısı geçirir; servis açık oturum ister (savunma derinliği)."""
    assert _govde(client.get(BOSTA_KILIT_UCU)) == {"dakika": 10}

    yanit = client.put(BOSTA_KILIT_UCU, {"dakika": 5}, format="json")

    assert yanit.status_code == 400
    assert _govde(yanit)["message"] == "Boşta kilit süresi yalnız açık oturumda değiştirilir."
    assert SchoolConfig.load().idle_lock_minutes == 10


def test_bosta_kilit_suresi_servisi_aralik_disini_ve_bool_u_reddeder() -> None:
    """Uç dışı çağrı da veritabanı kısıtına (500) düşmeden Türkçe iletiyle reddedilir."""
    for deger in (2, 31, True):
        with pytest.raises(setup_service.IdleLockError, match="3 ile 30 dakika"):
            setup_service.set_idle_lock_minutes(dakika=deger)


# ============================================================ ilk hesap (Türkçe gövde)


def test_ilk_hesap_ucu_turkce_govde_ister_ve_oturumu_acar(
    client: APIClient, parolasiz: None
) -> None:
    eski = client.post(
        "/api/v1/security/enable/",
        {"display_name": "Örnek Kuran", "password": YENI_PAROLA},
        format="json",
    )
    assert eski.status_code == 400

    yanit = client.post(
        "/api/v1/security/enable/",
        {"ad_soyad": "Örnek Kuran", "parola": YENI_PAROLA},
        format="json",
    )

    assert yanit.status_code == 201, yanit.content
    hesap = OTURUM.hesap()
    assert hesap is not None and hesap.id == str(Account.objects.get().id)
    assert _govde(client.get(OTURUM_UCU))["durum"] == "acik"
