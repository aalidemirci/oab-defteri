"""Oturum durum makinesi (tasarım §4.1, §4.4.3, TK14; plan F1b-1 "Oturum") — birim testleri.

Varsayılan test ortamı (kök `conftest.py`): ilk hesap kurulu + oturum program
yöneticisi hesabıyla açık. Saat taklit edilir (`SahteSaat`). Bu dosyada kurulum
TAMAMLANMIŞ başlanır (`kurulum_tamamlanmis`, otomatik): kurulum bitene kadar boşta
süre oturumu kilitlemez (tasarım §13 D15); o davranış `TestKurulumSurerken`
sınıfındadır. Uç düzeyindeki davranış `test_oturum_uclari.py`'de, kilit kapısının
açık listeleri `test_kilit_koruma.py`'dedir.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import pytest
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from apps.okul import iz_dogrulama, masaustu_kanca
from apps.okul import oturum as oturum_modulu
from apps.okul.lock_middleware import AppLockMiddleware
from apps.okul.models import Account, AuditTrail, SchoolConfig
from apps.okul.oturum import (
    ACIK,
    ERTELENDI,
    GUVENLIK_DOSYASI_KAYIP,
    KILITLENDI,
    KILITLI,
    KURULUM,
    OTURUM,
    SISTEM,
    ZATEN_KILITLI,
    OturumDurumu,
    OturumHesabi,
    UcustakiIstekler,
    UykuyuSayanSaat,
    Yazar,
    bosta_suresi_dk,
    kapanista_kilitle,
    rol_etiketi,
    sistem_olarak,
    uykuyu_sayan_monoton_kaynak,
    yazar,
    yazar_olarak,
)
from apps.okul.services import app_password, live_restore
from apps.okul.tests.hesap_ortak import GECICI_PAROLA, YENI_PAROLA, hesap_ac
from apps.okul.tests.oturum_ortak import SahteSaat, kurulum_durumunu_yaz, oturum_saatini_kur
from conftest import (
    TEST_DEK,
    TEST_HESAP_ID,
    TEST_IA,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
    TEST_TANITICI,
    oturumu_ac_test,
)
from shared import bakim, crypto

pytestmark = pytest.mark.django_db

BOSTA = 10 * 60
YONETICI = OturumHesabi(id=TEST_HESAP_ID, tanitici=TEST_TANITICI, rol="yonetici")


@pytest.fixture(autouse=True)
def kurulum_tamamlanmis(db: None) -> None:
    """Boşta kilit testleri kurulumu tamamlanmış ortamda koşar (modül başlığı)."""
    kurulum_durumunu_yaz(tamam=True)


@pytest.fixture
def saat() -> SahteSaat:
    """Süreç içi oturumun saati sahtesiyle değişir; açık oturum korunur."""
    saat = SahteSaat()
    oturum_saatini_kur(saat)
    return saat


def _bekle(kosul: Callable[[], bool], *, sure: float = 5.0) -> bool:
    """Başka iş parçacığının durumu değiştirmesini bekler (koşul gerçekleşince True)."""
    son = time.monotonic() + sure
    while time.monotonic() < son:
        if kosul():
            return True
        time.sleep(0.01)
    return kosul()


# ============================================================ durumlar


class TestDurumlar:
    def test_varsayilan_ortamda_oturum_program_yoneticisiyle_aciktir(self) -> None:
        assert OTURUM.durum() == ACIK
        assert OTURUM.hesap() == YONETICI
        assert crypto.is_unlocked() is True

    def test_hesap_kurulmadan_kurulum(self, parolasiz: None) -> None:
        assert OTURUM.durum() == KURULUM
        assert OTURUM.hesap() is None

    def test_kilitliyken_kilitli(self, kilitli: None) -> None:
        assert OTURUM.durum() == KILITLI
        assert OTURUM.hesap_id() is None

    def test_guvenlik_dosyasi_kayipken_kayip(self, parmak_izi_yazili: str) -> None:
        app_password.state_path().unlink()
        assert OTURUM.durum() == GUVENLIK_DOSYASI_KAYIP

    def test_durum_dizeleri_sabittir(self) -> None:
        """Ön yüz bu dizeleri okur (`security/session/` `durum`)."""
        assert (KURULUM, KILITLI, ACIK, GUVENLIK_DOSYASI_KAYIP) == (
            "kurulum",
            "kilitli",
            "acik",
            "guvenlik_dosyasi_kayip",
        )

    def test_modul_tekili_tek_nesnedir(self) -> None:
        assert oturum_modulu.OTURUM is OTURUM
        assert isinstance(OTURUM, OturumDurumu)


def test_rol_etiketleri_kisa_ve_kodsuzdur() -> None:
    """Kilit ekranı ve üst çubuk: `yonetici` kısa etiketle; rol kodu kullanıcıya çıkmaz."""
    assert rol_etiketi("yonetici") == "Program yöneticisi"
    assert rol_etiketi("denetleme_kurulu") == "Denetleme Kurulu"
    assert rol_etiketi("muhasip") == "Muhasip"
    assert rol_etiketi("boyle_bir_rol") == "Hesap kaydı okunamadı"
    assert rol_etiketi(None) == "Hesap kaydı okunamadı"


# ============================================================ açılış yalnız açık çağrıyla


class TestAcilis:
    def test_anahtar_yuklemek_oturum_acmaz(self, kilitli: None) -> None:
        """Ailenin kip katmanı açılışı anahtar döneminden çıkarıyordu; OAB'de çıkarmaz."""
        crypto.load_key(TEST_DEK, audit_key=TEST_IA)

        assert OTURUM.durum() == KILITLI
        assert OTURUM.hesap() is None
        assert app_password.is_locked() is True

    def test_ac_dek_ve_iz_anahtarini_hesapla_birlikte_yukler(self, kilitli: None) -> None:
        assert crypto.is_unlocked() is False

        OTURUM.ac(YONETICI, veri_anahtari=TEST_DEK, iz_anahtari=TEST_IA)

        assert OTURUM.hesap() == YONETICI
        assert crypto.active_key() == TEST_DEK
        assert crypto.active_audit_key() == TEST_IA

    def test_kilit_acma_oturumu_o_hesapla_acar(
        self, kilitli: None, yonetici_hesabi: Account
    ) -> None:
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

        assert OTURUM.durum() == ACIK
        assert OTURUM.hesap() == YONETICI

    def test_kurtarma_anahtariyla_acilis_oturumu_acar(
        self, kilitli: None, yonetici_hesabi: Account
    ) -> None:
        app_password.unlock_with_recovery(
            recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=YENI_PAROLA
        )

        assert OTURUM.hesap() == YONETICI
        assert crypto.active_audit_key() == TEST_IA

    def test_ilk_hesap_kurulumu_oturumu_acar(self, parolasiz: None) -> None:
        app_password.enable(tanitici="yonetici", display_name="Örnek Kuran", password=YENI_PAROLA)

        hesap = OTURUM.hesap()
        assert hesap is not None
        assert (hesap.tanitici, hesap.rol) == ("yonetici", "yonetici")
        assert hesap.id == str(Account.objects.get().id)
        assert crypto.active_audit_key() is not None

    def test_acik_oturumda_dusen_giris_acik_oturumu_kapatmaz(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Açık oturumdayken yapılan ve işlemi düşen bir giriş, kendisinden önce süren oturumun
        anahtarlarına ve nesline dokunmaz (aynı DEK ve İA; bağımsız denetim bulgusu). Oturum
        yokken düşen giriş ise kendi yüklediği anahtarları düşürür (`test_denetim_izi`)."""

        def dustu(*_a: object, **_k: object) -> None:
            raise DatabaseError("database is locked")

        monkeypatch.setattr(iz_dogrulama, "yaz", dustu)
        once = crypto.key_epoch()
        with pytest.raises(DatabaseError):
            app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

        assert OTURUM.hesap() == YONETICI
        assert crypto.is_unlocked() is True
        assert crypto.key_epoch() > once  # anahtarlar (aynısı) yeniden yüklendi, düşmedi

    def test_reddedilen_kilit_acma_oturum_acmaz(
        self, kilitli: None, yonetici_hesabi: Account
    ) -> None:
        with pytest.raises(app_password.WrongPassword):
            app_password.unlock(hesap_id=TEST_HESAP_ID, password="Yanlis-Parola-9")

        assert OTURUM.durum() == KILITLI
        assert crypto.is_unlocked() is False

    def test_acikken_baska_hesapla_acilis_oturumu_o_hesaba_gecirir(
        self, yonetici_hesabi: Account
    ) -> None:
        """Parolayla kanıtlanmış "Kilitle + aç": DEK aynıdır, oturum yeni hesabındır."""
        muhasip = hesap_ac()

        app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)

        hesap = OTURUM.hesap()
        assert hesap is not None and (hesap.id, hesap.rol) == (str(muhasip.id), "muhasip")
        assert crypto.active_key() == TEST_DEK

    def test_parola_degisimi_oturumu_yeniden_acmaz(
        self, yonetici_hesabi: Account, saat: SahteSaat
    ) -> None:
        """Ailede parola değişimi "yeni açılış" sayılıyordu; burada oturum ve sayaç aynen kalır."""
        saat.ilerlet(300)
        donem = crypto.key_epoch()

        app_password.change_password(
            hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
        )

        assert crypto.key_epoch() == donem
        assert OTURUM.hesap() == YONETICI
        assert OTURUM.ozet()["bosta_kalan_sn"] == BOSTA - 300

    def test_kilit_acilisi_bosta_sayacini_sifirdan_baslatir(
        self, yonetici_hesabi: Account, saat: SahteSaat
    ) -> None:
        """Boşta kilitten sonra parolayla açılan oturum eski sayaçtan devam etseydi ilk
        istekte yeniden kilitlenirdi (`OturumDurumu.ac`: taze parola kanıtı)."""
        saat.ilerlet(BOSTA + 1)
        assert OTURUM.durum() == KILITLI

        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

        assert OTURUM.ozet()["bosta_kalan_sn"] == BOSTA
        saat.ilerlet(BOSTA - 1)
        assert OTURUM.durum() == ACIK
        saat.ilerlet(1)
        assert OTURUM.durum() == KILITLI

    def test_dek_oturum_disinda_duserse_oturum_kapanmis_sayilir(self) -> None:
        crypto.unload_key()

        assert OTURUM.acik_mi() is False
        assert OTURUM.durum() == KILITLI


# ============================================================ Kilitle


class TestKilitle:
    def test_kilitle_dek_ve_iz_anahtarini_dusurur(self) -> None:
        assert OTURUM.kilitle() == KILITLENDI

        assert OTURUM.durum() == KILITLI
        assert crypto.is_unlocked() is False
        assert crypto.active_audit_key() is None
        assert app_password.is_locked() is True

    def test_kilitliyken_kilitle_etkisizdir(self, kilitli: None) -> None:
        assert OTURUM.kilitle() == ZATEN_KILITLI

    def test_servis_kilidi_hemen_kapatir(self) -> None:
        """`app_password.lock` beklemez, ertelemez (geri yükleme sonrası, testler)."""
        with bakim.UZUN_ISLER.is_():
            app_password.lock()
            assert crypto.is_unlocked() is False
        assert OTURUM.hesap() is None


# ============================================================ boşta kilit


class TestBostaKilit:
    def test_bosta_sure_dolmadan_oturum_acik_kalir(self, saat: SahteSaat) -> None:
        saat.ilerlet(BOSTA - 1)
        assert OTURUM.durum() == ACIK
        assert OTURUM.ozet()["bosta_kalan_sn"] == 1

    def test_bosta_sure_dolunca_kilitlenir_ve_dek_duser(self, saat: SahteSaat) -> None:
        saat.ilerlet(BOSTA)  # sınır anı kilit sayılır (fail-closed)

        assert OTURUM.durum() == KILITLI
        assert crypto.is_unlocked() is False
        assert crypto.active_audit_key() is None

    def test_etkinlik_boşta_sayacini_tazeler(self, saat: SahteSaat) -> None:
        for _ in range(5):
            saat.ilerlet(BOSTA - 60)
            OTURUM.degerlendir()
            OTURUM.etkinlik()
        assert OTURUM.durum() == ACIK

    def test_suresi_dolmus_oturum_etkinlikle_dirilmez(self, saat: SahteSaat) -> None:
        saat.ilerlet(BOSTA + 1)

        OTURUM.etkinlik()  # değerlendirmeden önce gelse de sayacı tazelemez

        assert OTURUM.durum() == KILITLI

    def test_varsayilan_bosta_suresi_on_dakikadir(self) -> None:
        assert SchoolConfig.load().idle_lock_minutes == 10
        assert bosta_suresi_dk() == 10
        assert OTURUM.ozet()["bosta_dk"] == 10

    def test_ayar_satiri_yoksa_alanin_varsayilani_gecer(self) -> None:
        """Tasarım §13 D11: aile iskeletinin 3 dakikasına sessiz düşüş yoktur."""
        satirlar: Any = SchoolConfig.all_objects.all()
        satirlar.hard_delete()
        oturum_modulu.bosta_suresi_onbellegini_bosalt()

        assert bosta_suresi_dk() == 10

    def test_bosta_sure_ayardan_okunur_kaydedince_onbellek_bosalir(self, saat: SahteSaat) -> None:
        assert bosta_suresi_dk() == 10  # önbelleğe alındı
        config = SchoolConfig.load()
        config.idle_lock_minutes = 3
        config.save(update_fields=["idle_lock_minutes", "updated_at"])  # post_save boşaltır

        assert bosta_suresi_dk() == 3
        saat.ilerlet(3 * 60)
        assert OTURUM.durum() == KILITLI

    def test_ayar_sicak_yolda_onbellektedir(self, saat: SahteSaat) -> None:
        okumalar: list[int] = []

        def bosta_dk() -> int:
            okumalar.append(1)
            return 10

        OTURUM._bosta_dk = bosta_dk
        for _ in range(17):  # alt sınırın (3 dk) altında ayar hiç okunmaz
            saat.ilerlet(10)
            OTURUM.degerlendir()
            OTURUM.etkinlik()
        assert okumalar == []

    def test_aralik_disi_deger_sinira_cekilir(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        class _Sahte:
            def values_list(self, *_a: object, **_k: object) -> _Sahte:
                return self

            def first(self) -> int:
                return 99

        caplog.set_level(logging.WARNING, logger="oab_defteri.okul")
        monkeypatch.setattr(SchoolConfig.objects, "filter", lambda **_k: _Sahte())
        oturum_modulu.bosta_suresi_onbellegini_bosalt()

        assert bosta_suresi_dk() == 30
        assert "aralık dışında" in caplog.text

    def test_veritabani_okunamazsa_alan_varsayilani_onbellege_alinmaz(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = SchoolConfig.load()
        config.idle_lock_minutes = 5
        config.save(update_fields=["idle_lock_minutes", "updated_at"])

        def patlat(**_k: object) -> None:
            raise DatabaseError("disk I/O error")

        with monkeypatch.context() as yama:
            yama.setattr(SchoolConfig.objects, "filter", patlat)
            assert bosta_suresi_dk() == 10
        assert bosta_suresi_dk() == 5  # önbelleğe alınmamıştı: yeniden okundu


# ============================================================ kurulum sürerken (D15)


class TestKurulumSurerken:
    """Kurulum bitene kadar boşta süre oturumu kilitlemez (tasarım §13 D15)."""

    @pytest.fixture(autouse=True)
    def kurulum_suruyor(self, kurulum_tamamlanmis: None) -> None:
        kurulum_durumunu_yaz(tamam=False)

    def test_bosta_sure_kilitlemez(self, saat: SahteSaat) -> None:
        for _ in range(5):
            saat.ilerlet(BOSTA + 1)
            assert OTURUM.durum() == ACIK
        assert crypto.is_unlocked() is True

    def test_ozet_kalan_sureyi_bos_verir(self, saat: SahteSaat) -> None:
        """Geri sayım gösterilmez: süre işlemiyor."""
        saat.ilerlet(40)
        ozet = OTURUM.ozet()
        assert ozet["durum"] == ACIK
        assert ozet["bosta_kalan_sn"] is None
        assert ozet["kurulum_tamam"] is False
        assert ozet["bosta_dk"] == 10

    def test_elle_kilitle_calisir(self) -> None:
        assert OTURUM.kilitle() == KILITLENDI
        assert OTURUM.durum() == KILITLI

    def test_kurulum_tamamlaninca_sure_islemeye_baslar(self, saat: SahteSaat) -> None:
        saat.ilerlet(BOSTA + 30)
        assert OTURUM.durum() == ACIK  # sayaç yeniden başladı
        kurulum_durumunu_yaz(tamam=True)
        saat.ilerlet(BOSTA)
        assert OTURUM.durum() == KILITLI

    def test_kurulum_bilgisi_yalniz_sure_dolarken_sorulur(self, saat: SahteSaat) -> None:
        """Sıcak yol hafif kalır: süre dolmadıkça veritabanına sorulmaz."""
        sorgular: list[float] = []

        def kurulum_tamam() -> bool:
            sorgular.append(saat())
            return False

        OTURUM._kurulum_tamam = kurulum_tamam
        for _ in range(BOSTA // 30 - 1):
            saat.ilerlet(30)
            OTURUM.degerlendir()
        assert sorgular == []
        saat.ilerlet(30)  # süre doldu: bir kez sorulur, sayaç yeniden başlar
        OTURUM.degerlendir()
        assert len(sorgular) == 1
        for _ in range(BOSTA // 30 - 1):
            saat.ilerlet(30)
            OTURUM.degerlendir()
        assert len(sorgular) == 1
        assert OTURUM.acik_mi() is True

    def test_ozet_kurulum_bitince_veritabanina_gitmez(self, saat: SahteSaat) -> None:
        """Ön yüz oturum özetini kısa aralıkla yoklar: sorgu TÜKENMELİDİR."""
        bitti = False
        sorgular: list[float] = []

        def kurulum_tamam() -> bool:
            sorgular.append(saat())
            return bitti

        OTURUM._kurulum_tamam = kurulum_tamam
        for _ in range(5):
            saat.ilerlet(15)
            assert OTURUM.ozet()["bosta_kalan_sn"] is None
        assert len(sorgular) == 5

        bitti = True
        sorgular.clear()
        for _ in range(5):
            saat.ilerlet(15)
            assert OTURUM.ozet()["bosta_kalan_sn"] is not None
        assert len(sorgular) == 1

    def test_veritabani_okunamazsa_kurulum_tamam_sayilir(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fail-closed: kurulum bilgisi okunamazsa boşta süre işler."""

        def patlat(*_a: object, **_k: object) -> None:
            raise DatabaseError("disk I/O error")

        monkeypatch.setattr(SchoolConfig.objects, "filter", patlat)
        assert oturum_modulu.kurulum_tamamlandi_mi() is True
        assert oturum_modulu.kurulum_durumu() is None  # yanıt bilinmiyor

    def test_veritabani_hatasinin_yaniti_onbellege_alinmaz(
        self, saat: SahteSaat, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Tek bir geçici hata o anki kararda fail-closed'dur ama D15'i süreç sonuna dek
        kapatmaz: kurtarma anahtarı ekrandayken boşta kilit devreye girmemeli (TB19)."""

        def patlat(*_a: object, **_k: object) -> None:
            raise DatabaseError("database is locked")

        with monkeypatch.context() as yama:
            yama.setattr(SchoolConfig.objects, "filter", patlat)
            assert OTURUM.ozet()["kurulum_tamam"] is True  # o anki karar: süre işler

        assert OTURUM.ozet()["kurulum_tamam"] is False  # önbelleğe alınmamıştı
        saat.ilerlet(BOSTA + 1)
        assert OTURUM.durum() == ACIK
        assert crypto.is_unlocked() is True

    def test_kurulum_bilgisi_veritabanindan_okunur(self) -> None:
        assert oturum_modulu.kurulum_tamamlandi_mi() is False
        kurulum_durumunu_yaz(tamam=True)
        assert oturum_modulu.kurulum_tamamlandi_mi() is True
        satirlar: Any = SchoolConfig.all_objects.all()
        satirlar.hard_delete()  # satır yok: kurulum sürüyor
        assert oturum_modulu.kurulum_tamamlandi_mi() is False


def test_sureyi_yeniden_baslat_bosta_sayacini_sifirlar(saat: SahteSaat) -> None:
    saat.ilerlet(BOSTA - 10)
    OTURUM.sureyi_yeniden_baslat()
    assert OTURUM.ozet()["bosta_kalan_sn"] == BOSTA


# ============================================================ uzun iş (UY-1)


class TestUzunIs:
    def test_uzun_is_surerken_bosta_kilit_yok(self, saat: SahteSaat) -> None:
        """Tasarım §10.6: uzun iş sürerken boşta süre dolsa da DEK işin ortasında silinmez."""
        with bakim.UZUN_ISLER.is_():
            saat.ilerlet(BOSTA + 5)
            assert OTURUM.durum() == ACIK
            assert crypto.is_unlocked() is True
            ozet = OTURUM.ozet()
            assert ozet["kilit_bekliyor"] is True
            assert ozet["bosta_kalan_sn"] is None  # ekranda "İşlem bitince kilitlenecek"
            OTURUM.etkinlik()  # süresi dolmuş oturum etkinlikle dirilmez
        assert bakim.UZUN_ISLER.sayi == 0
        # İş bitti: ilk istekte kilit uygulanır.
        assert OTURUM.durum() == KILITLI
        assert crypto.is_unlocked() is False

    def test_uzun_is_surerken_elle_kilit_ertelenir(self) -> None:
        with bakim.UZUN_ISLER.is_():
            assert OTURUM.kilitle() == ERTELENDI
            assert OTURUM.kilitle() == ERTELENDI  # fikirdeş
            assert OTURUM.durum() == ACIK
            assert OTURUM.kilit_bekliyor() is True
        assert OTURUM.durum() == KILITLI

    def test_ic_ice_uzun_islerde_son_is_bitene_dek_ertelenir(self) -> None:
        with bakim.UZUN_ISLER.is_():
            with bakim.UZUN_ISLER.is_():
                OTURUM.kilitle()
            assert bakim.UZUN_ISLER.sayi == 1
            assert OTURUM.durum() == ACIK
        assert OTURUM.durum() == KILITLI

    def test_kapanis_kilidi_ertelenmez(self) -> None:
        with bakim.UZUN_ISLER.is_():
            assert kapanista_kilitle() is True
            assert crypto.is_unlocked() is False

    def test_kilit_acilisi_bekleyen_kilidi_kaldirir(self) -> None:
        with bakim.UZUN_ISLER.is_():
            OTURUM.kilitle()
            oturumu_ac_test()  # parolayla yeniden açılış (taze kanıt)
            assert OTURUM.kilit_bekliyor() is False
        assert OTURUM.durum() == ACIK

    def test_sayac_istisnada_da_duser(self) -> None:
        with pytest.raises(RuntimeError), bakim.UZUN_ISLER.is_():
            raise RuntimeError("iş yarıda kaldı")
        assert bakim.UZUN_ISLER.sayi == 0

    def test_canli_geri_yukleme_uzun_is_sayacini_kullanir(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gorulen: list[int] = []

        def sahte(**_k: object) -> dict[str, Any]:
            gorulen.append(bakim.UZUN_ISLER.sayi)
            return {}

        monkeypatch.setattr(live_restore, "_restore", sahte)
        live_restore.restore_and_require_restart(name="x.odbak", password=TEST_PAROLA)
        assert gorulen == [1]
        assert bakim.UZUN_ISLER.sayi == 0


# ============================================================ uçuştaki istekler


def _ucusta_tut() -> tuple[threading.Thread, threading.Event]:
    """Uçuşta bir istek başlatır; döndürülen olay set edilene dek istek bitmez."""
    basladi = threading.Event()
    birak = threading.Event()

    def istek() -> None:
        with OTURUM.istek():
            basladi.set()
            birak.wait(10)

    is_parcacigi = threading.Thread(target=istek, daemon=True)
    is_parcacigi.start()
    assert basladi.wait(5)
    return is_parcacigi, birak


@pytest.fixture
def kilit_izi_bellekte(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, Yazar]]:
    """`KILIT` satırını veritabanı yerine belleğe yazar (kilitleyen başka iş parçacığıysa).

    Testin veritabanı işlemi test boyunca açıktır; başka bir iş parçacığının bağlantısı o
    sürede SQLite'a yazamaz (yazma kilidi, `busy_timeout` 5 sn). Kilidin iz satırı
    `test_denetim_izi.py`'de aynı iş parçacığında sınanır; burada yalnız çağrı görülür.
    """
    gorulen: list[tuple[str, Yazar]] = []
    monkeypatch.setattr(OTURUM, "_kilit_izi", lambda hesap, kim: gorulen.append((hesap.id, kim)))
    return gorulen


class TestUcustakiIstekler:
    def test_kilitle_ucustaki_istegin_bitmesini_bekler(
        self, kilit_izi_bellekte: list[tuple[str, Yazar]]
    ) -> None:
        istek, birak = _ucusta_tut()
        sonuc: list[str] = []
        kilitleyen = threading.Thread(target=lambda: sonuc.append(OTURUM.kilitle()), daemon=True)
        kilitleyen.start()

        # Kilit kararı verildi: yeni istekler için oturum kapalı, ama DEK uçuştaki istek
        # bitene dek bellekte (işin ortasında silinmez).
        assert _bekle(lambda: not OTURUM.acik_mi())
        assert crypto.is_unlocked() is True
        assert OTURUM.durum() == KILITLI
        assert sonuc == []

        birak.set()
        istek.join(5)
        kilitleyen.join(5)
        assert sonuc == [KILITLENDI]
        assert crypto.is_unlocked() is False
        # İz satırı istek bittikten sonra, elle Kilitle olduğu için hesabın adına.
        assert kilit_izi_bellekte == [(TEST_HESAP_ID, Yazar.hesaptan(YONETICI))]

    def test_bekleme_sinirlidir_sure_dolunca_yine_kilitlenir(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.WARNING, logger="oab_defteri.okul")
        istek, birak = _ucusta_tut()
        try:
            assert OTURUM.kilitle(bekleme_sn=0.05) == KILITLENDI
            assert crypto.is_unlocked() is False
            assert "bitmedi" in caplog.text
        finally:
            birak.set()
            istek.join(5)

    def test_kilitleyen_istek_kendini_beklemez(self) -> None:
        baslangic = time.monotonic()
        with OTURUM.istek():
            assert OTURUM.kilitle(bekleme_sn=5) == KILITLENDI
        assert time.monotonic() - baslangic < 2

    def test_bekleme_sirasinda_acilan_oturum_dusurulmez(
        self, kilit_izi_bellekte: list[tuple[str, Yazar]]
    ) -> None:
        """Kilit uçuştakileri beklerken açılan (yeni hesaplı) oturum, kilidin sonunda düşmez;
        uygulanmayan kilit için `KILIT` satırı ve çapa da YAZILMAZ: iz açık bir oturumu
        kilitlenmiş göstermez (hesap değiştirmenin olağan yolu gibi)."""
        istek, birak = _ucusta_tut()
        kilitleyen = threading.Thread(target=OTURUM.kilitle, daemon=True)
        kilitleyen.start()
        assert _bekle(lambda: not OTURUM.acik_mi())

        oturumu_ac_test("0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", tanitici="muhasip", rol="muhasip")
        birak.set()
        istek.join(5)
        kilitleyen.join(5)

        hesap = OTURUM.hesap()
        assert hesap is not None and hesap.rol == "muhasip"
        assert crypto.is_unlocked() is True
        assert kilit_izi_bellekte == []

    def test_ayni_hesapla_yeniden_giriste_de_kilit_satiri_yazilmaz(
        self, kilit_izi_bellekte: list[tuple[str, Yazar]]
    ) -> None:
        """Yavaş bir istek uçuştayken kilit ekranından AYNI hesapla yeniden giriş: iz
        `GIRIS(A) … KILIT(A)` sırasıyla açık oturumu kilitli göstermez."""
        istek, birak = _ucusta_tut()
        kilitleyen = threading.Thread(target=OTURUM.kilitle, daemon=True)
        kilitleyen.start()
        assert _bekle(lambda: not OTURUM.acik_mi())

        oturumu_ac_test()
        birak.set()
        istek.join(5)
        kilitleyen.join(5)

        assert OTURUM.hesap_id() == TEST_HESAP_ID
        assert kilit_izi_bellekte == []

    def test_bekleme_sirasinda_servis_kapatirsa_kilit_satiri_yazilmaz_zaten_kilitli(
        self, kilit_izi_bellekte: list[tuple[str, Yazar]], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Oturum servis içinden kapatıldıysa (geri yükleme, güvenlik dosyasının sıfırlanması)
        bu yeniden giriş DEĞİLDİR: satır yazılmaz, yanıt `zaten_kilitli`, günlük doğrusunu
        söyler (bağımsız denetim bulgusu: "oturum yeniden açıldı" yazıyordu)."""
        caplog.set_level(logging.INFO, logger="oab_defteri.okul")
        istek, birak = _ucusta_tut()
        sonuc: list[str] = []
        kilitleyen = threading.Thread(target=lambda: sonuc.append(OTURUM.kilitle()), daemon=True)
        kilitleyen.start()
        assert _bekle(lambda: not OTURUM.acik_mi())

        OTURUM.kapat()
        birak.set()
        istek.join(5)
        kilitleyen.join(5)

        assert sonuc == [ZATEN_KILITLI]
        assert kilit_izi_bellekte == []
        assert "servis içinden kapatıldı" in caplog.text
        assert "yeniden açıldı" not in caplog.text

    def test_bekleyen_kilit_sirasinda_dusen_giris_kilidi_ve_ucustaki_isi_bozmaz(
        self,
        kilit_izi_bellekte: list[tuple[str, Yazar]],
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Bağımsız denetim bulgusu: uzun bir yazma uçuştayken Kilitle'ye basılır, kilit
        ekranından yapılan giriş işlemini kuramayıp düşer ("database is locked"). Düşen giriş
        `OTURUM.kapat()` ile DEK'i uçuştaki yazmanın ortasında düşürüyor, nesli değiştirip
        bekleyen kilidin `KILIT` satırını ve çapasını iptal ediyordu. Artık kendisinden önce süren
        oturuma dokunmaz: DEK uçuştaki iş bitene dek bellektedir, kilidin satırı yazılır."""
        caplog.set_level(logging.INFO, logger="oab_defteri.okul")

        def kilitli_vt(*_a: object, **_k: object) -> None:
            raise DatabaseError("database is locked")

        istek, birak = _ucusta_tut()
        sonuc: list[str] = []
        kilitleyen = threading.Thread(target=lambda: sonuc.append(OTURUM.kilitle()), daemon=True)
        kilitleyen.start()
        assert _bekle(lambda: not OTURUM.acik_mi())

        monkeypatch.setattr(iz_dogrulama, "yaz", kilitli_vt)
        with pytest.raises(DatabaseError):
            app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
        # Uçuştaki iş sürüyor: DEK düşmedi, kilit hâlâ bekliyor.
        assert crypto.is_unlocked() is True
        assert sonuc == [] and kilit_izi_bellekte == []

        birak.set()
        istek.join(5)
        kilitleyen.join(5)

        assert sonuc == [KILITLENDI]
        assert kilit_izi_bellekte == [(TEST_HESAP_ID, Yazar.hesaptan(YONETICI))]
        assert crypto.is_unlocked() is False
        assert "yeniden açıldı" not in caplog.text

    def test_sayac_istek_bitince_duser(self) -> None:
        sayac = UcustakiIstekler()
        with sayac.istek():
            assert sayac.sayi == 1
            with pytest.raises(RuntimeError), sayac.istek():
                raise RuntimeError("görünümde hata")
            assert sayac.sayi == 1
        assert sayac.sayi == 0
        assert sayac.bosalmasini_bekle(bekleme_sn=0.01) is True


# ============================================================ yazar bağlamı (TK16)


def _yazari_yakala(gorulen: list[Yazar | None]) -> Callable[[HttpRequest], HttpResponse]:
    def gorunum(_request: HttpRequest) -> HttpResponse:
        gorulen.append(yazar())
        return HttpResponse("tamam")

    return gorunum


class TestYazar:
    def test_baglam_yoksa_yazar_yok(self) -> None:
        # Varsayılan test ortamı oturumdaki hesabın bağlamıyla koşar (kök conftest).
        assert yazar() == Yazar(hesap_id=TEST_HESAP_ID, rol="yonetici")
        with yazar_olarak(None):
            assert yazar() is None

    def test_sistem_ve_ic_ice_baglam(self) -> None:
        hesap_yazari = Yazar.hesaptan(
            OturumHesabi(
                id="0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", tanitici="muhasip", rol="muhasip"
            )
        )
        dis = yazar()
        with yazar_olarak(hesap_yazari):
            assert yazar() == hesap_yazari
            with sistem_olarak():
                kim = yazar()
                assert kim is SISTEM and kim.sistem_mi
            assert yazar() == hesap_yazari
        assert yazar() == dis
        assert hesap_yazari.sistem_mi is False

    def test_ara_katman_oturum_hesabini_istek_boyunca_yazar_yapar(self) -> None:
        gorulen: list[Yazar | None] = []
        katman = AppLockMiddleware(_yazari_yakala(gorulen))

        with yazar_olarak(None):
            katman(RequestFactory().get("/api/v1/school-years/"))
            assert yazar() is None  # bağlam istekten sızmaz

        assert gorulen == [Yazar(hesap_id=TEST_HESAP_ID, rol="yonetici")]

    def test_kilitliyken_izinli_istekte_yazar_yok(self, kilitli: None) -> None:
        gorulen: list[Yazar | None] = []
        katman = AppLockMiddleware(_yazari_yakala(gorulen))

        katman(RequestFactory().get("/api/v1/setup/status/"))

        assert gorulen == [None]

    def test_ara_katman_istegi_ucusta_sayar(self) -> None:
        sayilar: list[int] = []

        def gorunum(_request: HttpRequest) -> HttpResponse:
            sayilar.append(oturum_modulu.UCUSTA.sayi)
            return HttpResponse("tamam")

        AppLockMiddleware(gorunum)(RequestFactory().get("/api/v1/school-years/"))

        assert sayilar == [1]
        assert oturum_modulu.UCUSTA.sayi == 0


# ============================================================ düzenli kapanış (§4.2)


class TestKapanis:
    def test_kapanis_kilidi_masaustu_kancasina_kayitlidir(self) -> None:
        """`OkulConfig.ready` kaydeder; masaüstü oturum modülünü içe aktarmaz."""
        assert masaustu_kanca.kapanista_kilitle() is True
        assert crypto.is_unlocked() is False
        assert OTURUM.durum() == KILITLI

    def test_kilitliyken_kapanis_kilidi_bir_sey_yapmaz(self, kilitli: None) -> None:
        assert masaustu_kanca.kapanista_kilitle() is False

    def test_kayit_kaldirilinca_kanca_yok_der(self) -> None:
        try:
            masaustu_kanca.kapanis_kilidi_kaydet(None)
            assert masaustu_kanca.kapanista_kilitle() is False
            assert crypto.is_unlocked() is True
        finally:
            masaustu_kanca.kapanis_kilidi_kaydet(kapanista_kilitle)

    def test_kapanis_suren_elle_kilidin_satirini_ve_capasini_bekler(
        self, kilit_izi_bellekte: list[tuple[str, Yazar]]
    ) -> None:
        """Bağımsız denetim bulgusu: elle kilit uçuştaki isteği beklerken pencere kapatılınca
        kapanış kilidi HEMEN dönüyordu; masaüstü sunucuyu durdurup temiz kapanış işaretini
        yazıyor, bekleyen kilit (daemon iş parçacığı) süreçle ölüyor, `KILIT` satırı ve çapa hiç
        yazılmıyordu. Kapanış artık süren kilidin bitmesini bekler."""
        istek, birak = _ucusta_tut()
        kilitleyen = threading.Thread(target=OTURUM.kilitle, daemon=True)
        kilitleyen.start()
        assert _bekle(lambda: not OTURUM.acik_mi())
        sonuc: list[bool] = []
        kapanis = threading.Thread(target=lambda: sonuc.append(kapanista_kilitle()), daemon=True)
        kapanis.start()

        time.sleep(0.2)
        assert sonuc == [] and kilit_izi_bellekte == []  # kapanış süren kilidi bekliyor

        birak.set()
        istek.join(5)
        kilitleyen.join(5)
        kapanis.join(5)

        assert sonuc == [False]  # kilidi elle kilit uyguladı
        assert kilit_izi_bellekte == [(TEST_HESAP_ID, Yazar.hesaptan(YONETICI))]
        assert crypto.is_unlocked() is False

    def test_kapanis_suren_kilit_acilisini_bekler_acilan_oturumu_kilitler(
        self,
        kilitli: None,
        kilit_izi_bellekte: list[tuple[str, Yazar]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Bağımsız denetim bulgusu: kilit açılışı sürerken kapanış kilidi oturum kapalı diye
        hemen dönüyor, açılış ondan SONRA oturumu açıyordu: süreç oturum açık ve çapasız
        bitiyordu. Kapanış artık uçuştaki istekleri (süren açılış) bekler ve açılan oturumu da
        kilitler (`KILIT` satırı ve çapa)."""
        asil = iz_dogrulama.hazirla
        icerde = threading.Event()

        def yavas(anahtar: Any) -> Any:
            icerde.set()
            time.sleep(0.3)
            return asil(anahtar)

        monkeypatch.setattr(iz_dogrulama, "hazirla", yavas)
        sonuc: list[bool] = []

        def kapanis() -> None:
            assert icerde.wait(5)
            sonuc.append(kapanista_kilitle())

        kapanan = threading.Thread(target=kapanis, daemon=True)
        kapanan.start()
        with OTURUM.istek():  # kilit açılışı uçuştaki bir istektir (ara katman sayar)
            app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
        kapanan.join(10)

        assert sonuc == [True]
        assert OTURUM.acik_mi() is False and crypto.is_unlocked() is False
        assert kilit_izi_bellekte == [(TEST_HESAP_ID, SISTEM)]

    def test_kapanis_suresi_dolunca_bu_arada_acilan_oturumu_beklemeden_kilitler(
        self,
        kilitli: None,
        kilit_izi_bellekte: list[tuple[str, Yazar]],
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Bağımsız denetim bulgusu: oturum kapalıyken uzun bir istek (büyük dışa aktarım)
        uçuştayken kilit açılışı biter. Kapanış uzun isteği beklerken açılan oturumu görmüyor,
        süre dolunca oturum AÇIK ve `KILIT` satırsız dönüyordu; masaüstü temiz kapanış işaretini
        yazdığı için "Son Oturumu Kontrol Edin" kartı da çıkmıyordu. Süre dolunca açık oturum
        artık beklemeden kilitlenir (fail-closed)."""
        caplog.set_level(logging.WARNING, logger="oab_defteri.okul")
        asil = iz_dogrulama.hazirla
        icerde = threading.Event()

        def yavas(anahtar: Any) -> Any:
            icerde.set()  # açılış kapanış işaretini geçti, oturumu henüz açmadı
            time.sleep(0.2)
            return asil(anahtar)

        monkeypatch.setattr(iz_dogrulama, "hazirla", yavas)
        uzun, birak = _ucusta_tut()
        sonuc: list[bool] = []

        def kapanis() -> None:
            assert icerde.wait(5)
            sonuc.append(OTURUM.kapanis_kilidi(bekleme_sn=2.0))

        kapanan = threading.Thread(target=kapanis, daemon=True)
        kapanan.start()
        try:
            with OTURUM.istek():  # kilit açılışı uçuştaki bir istektir (ara katman sayar)
                app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
            assert OTURUM.acik_mi() is True  # açılış bitti, uzun istek sürüyor
            kapanan.join(10)

            assert sonuc == [True]
            assert OTURUM.acik_mi() is False and crypto.is_unlocked() is False
            assert kilit_izi_bellekte == [(TEST_HESAP_ID, SISTEM)]
            assert "bitmedi" in caplog.text
        finally:
            birak.set()
            uzun.join(5)

    def test_kapanis_once_ucustakileri_sonra_oturumu_okur_arada_acilan_kacmaz(
        self, kilitli: None
    ) -> None:
        """Bağımsız denetim bulgusu (dar yarış): kapanış oturumu kapalı okuyup bıraktıktan
        sonra, uçuştaki sayıyı okumadan önce bir kilit açılışı oturumu açıp biterse kapanış
        açık oturumla dönüyordu. Artık önce uçuştaki istekler, SONRA oturum okunur; yarışın en
        kötü anı, açılışın uçuştaki sayı okunurken bitmesidir."""
        gorulen: list[tuple[str, Yazar]] = []
        oturum: OturumDurumu

        class _AcilisYarisi(UcustakiIstekler):
            """Uçuştaki istekler İLK kez okunurken bir kilit açılışı oturumu açıp biter."""

            def __init__(self) -> None:
                super().__init__()
                self.acildi = False

            def _yaris(self) -> None:
                if not self.acildi:
                    self.acildi = True
                    oturum.ac(YONETICI, veri_anahtari=TEST_DEK, iz_anahtari=TEST_IA)

            @property
            def sayi(self) -> int:
                self._yaris()
                return super().sayi

            def bosalmasini_bekle(self, *, bekleme_sn: float) -> bool:
                self._yaris()
                return super().bosalmasini_bekle(bekleme_sn=bekleme_sn)

        sayac = _AcilisYarisi()
        oturum = OturumDurumu(
            ucusta=sayac,
            kilit_izi=lambda hesap, kim: gorulen.append((hesap.id, kim)),
            hesap_kurulu=lambda: True,
            dosya_kayip=lambda: False,
        )
        baslangic = time.monotonic()

        assert oturum.kapanis_kilidi(bekleme_sn=5.0) is True

        assert sayac.acildi is True
        assert oturum.acik_mi() is False and crypto.is_unlocked() is False
        assert gorulen == [(TEST_HESAP_ID, SISTEM)]
        assert time.monotonic() - baslangic < 2  # beklemeden: uçuşta istek yoktu

    def test_kapanis_basladiktan_sonra_kilit_acilisi_hicbir_sey_yazmadan_reddedilir(
        self, kilitli: None
    ) -> None:
        """Kapanış işareti tek yönlüdür: sonra gelen kilit açılışı oturum açmaz, iz yazmaz."""
        assert kapanista_kilitle() is False
        once = AuditTrail.objects.count()

        with pytest.raises(app_password.ProgramClosing, match="Program kapanıyor"):
            app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

        assert OTURUM.acik_mi() is False and crypto.is_unlocked() is False
        assert AuditTrail.objects.count() == once

    def test_masaustu_kancalarinin_sifirlanmasi_kapanis_kilidini_dusurmez(self) -> None:
        masaustu_kanca._reset_for_tests()
        masaustu_kanca.kaldir()
        assert masaustu_kanca.kapanista_kilitle() is True


# ============================================================ saat: uyku da süredir


class _IkiKaynak:
    """`UykuyuSayanSaat`'in iki kaynağını (monoton + duvar) elle ilerleten taklit."""

    def __init__(self) -> None:
        self.monoton = 5_000.0
        self.duvar = 1_790_000_000.0  # 2026 civarı bir Unix zamanı

    def saat(self) -> UykuyuSayanSaat:
        return UykuyuSayanSaat(monoton=lambda: self.monoton, duvar=lambda: self.duvar)


def test_varsayilan_saat_uykuyu_sayan_saattir() -> None:
    """Denetim bulgusu: `time.monotonic` Linux'ta askıya alınan süreyi saymaz."""
    assert isinstance(OturumDurumu()._saat, UykuyuSayanSaat)
    OTURUM._reset_for_tests()
    assert isinstance(OTURUM._saat, UykuyuSayanSaat)


@pytest.mark.skipif(not hasattr(time, "CLOCK_BOOTTIME"), reason="yalnız Linux")
def test_linuxta_monoton_kaynak_boottime_dir() -> None:
    """Linux'ta (Pardus) monoton kaynak CLOCK_BOOTTIME'dır: uykuyu da sayar."""
    kaynak = uykuyu_sayan_monoton_kaynak()
    assert kaynak is not time.monotonic
    assert abs(kaynak() - time.clock_gettime(time.CLOCK_BOOTTIME)) < 1.0


def test_uyku_suresi_duvar_saatinden_sayilir() -> None:
    """Monoton kaynak uykuda durur (CLOCK_MONOTONIC), duvar saati uyanışta ileri geçer."""
    k = _IkiKaynak()
    saat = k.saat()
    once = saat()
    k.duvar += 8 * 3600  # gece boyunca uyku; monoton kaynak hiç ilerlemedi
    assert saat() - once == 8 * 3600


def test_duvar_saati_geri_alinsa_sure_uzamaz_ve_saat_azalmaz() -> None:
    k = _IkiKaynak()
    saat = k.saat()
    once = saat()
    k.duvar -= 3600  # saat bir saat geri alındı
    k.monoton += 10
    ara = saat()
    assert ara - once == 10  # yalnız monoton ilerleme
    k.monoton += 5
    k.duvar += 5
    assert saat() - ara == 5  # geri alınan saat sonraki adımlarda borç yaratmaz


def test_duvar_saati_ileri_sicrarsa_sure_erken_dolar() -> None:
    """Fail-closed: ileri sıçrama oturumu kısaltır, asla uzatmaz."""
    k = _IkiKaynak()
    saat = k.saat()
    once = saat()
    k.monoton += 1
    k.duvar += 120
    assert saat() - once == 120


def test_uykudan_uyaninca_oturum_kilitlenir_ve_dek_duser() -> None:
    """Denetçi senaryosu: boşta sayacında 2 dk kalmışken makine uyutulur, sabah uyanır.
    Uyanıştan sonraki ilk dokunuş (etkinlik) oturumu dirilterek UZATAMAZ."""
    k = _IkiKaynak()
    oturum_saatini_kur(k.saat())
    k.monoton += 8 * 60
    k.duvar += 8 * 60
    assert OTURUM.ozet()["bosta_kalan_sn"] == BOSTA - 8 * 60

    k.duvar += 10 * 3600  # uyku: yalnız duvar saati ilerler
    OTURUM.etkinlik()

    assert OTURUM.durum() == KILITLI
    assert crypto.is_unlocked() is False
