"""Hesaplı güvenlik çekirdeği (tasarım §4.3, §4.4.3-§4.4.4; şema 2) — uçtan uca davranış testleri.

Varsayılan test ortamı `backend/conftest.py`'dedir: **ilk hesap kurulu + kilit
açık + oturumda o hesap** (sabit `TEST_DEK`, `TEST_HESAP_ID`, `TEST_PAROLA`,
`TEST_KURTARMA_ANAHTARI`). Kilit açan testler `yonetici_hesabi` fixtürüyle
`Account` satırını ve iz anahtarını kurar (iki depo kuralı DB ister). Hesap
servisleri ve iki depo halleri `test_hesaplar.py`'dedir.

Şifreleme iddiaları ORM'e güvenmez, ham SQL ile sütunu okur
(`connection.cursor()`); aksi hâlde şifreli alan kendini çözer ve test yalan
söylerdi.

F1 kod kapısının üç güvenlik maddesi burada AYRI testlerle kanıtlanır:
* "kilitliyken `Student.save()` hata verir" → `TestFailClosed`,
* "guvenlik.json silinince fail-closed" → `TestGuvenlikDosyasiKayip`,
* "hesap yokken kişi yazan uç 409" → `test_kisi_yazan_uclar.py`.
"""

from __future__ import annotations

import base64
import json
import sqlite3
import time
import uuid
from datetime import timedelta
from io import StringIO
from pathlib import Path
from typing import Any, cast
from unittest import mock

import pytest
from desktop.backup_crypto import (
    config_path,
    decrypt_bytes,
    encrypt_bytes,
    ensure_public_config,
    private_key_from_data_key,
    recovery_metadata,
)
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, connections, transaction
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul import selectors
from apps.okul.models import (
    Account,
    AccountRole,
    AccountStatus,
    AuditKey,
    Personnel,
    ResetKind,
    SchoolConfig,
    Student,
)
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    UCUNCU_PAROLA,
    YENI_PAROLA,
    arsivler,
    durum,
    durum_yaz,
    ham_guncelle,
    hesap_ac,
    muhurle,
    sarmal,
)
from conftest import (
    TEST_DEK,
    TEST_HESAP_ID,
    TEST_IA,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
    TEST_TANITICI,
)
from shared import crypto

OGRENCI_AD = "EMRE CAN"
OGRENCI_SOYAD = "YILMAZ"
KURAN_AD = "Örnek Müdür Yardımcısı"

#: Üretimdeki gecikme dizisi, kök `conftest`'in her testte yaptığı yamadan (`(0.0,)`)
#: ÖNCE, içe aktarmada alınır. Gecikme testi yamayı beklenen değerin kendisiyle
#: yineleseydi üretimdeki sabit hiç sınanmamış olurdu.
_GERCEK_GECIKMELER = app_password.FAILURE_DELAYS


class _SurecOldu(BaseException):
    """Sürecin işlem ortasında ölmesi: `except Exception` yakalamaz, geri alma koşmaz."""


def ogrenci_olustur(**fazlasi: Any) -> Student:
    veri: dict[str, Any] = {
        "first_name": OGRENCI_AD,
        "last_name": OGRENCI_SOYAD,
        "student_number": "101",
        "class_level": 10,
        "class_section": "A",
    }
    veri.update(fazlasi)
    return cast("Student", Student.objects.create(**veri))


def ham_satir(student_id: int) -> tuple[str, str]:
    """ORM'i BYPASS ederek ad-soyad sütunlarını olduğu gibi okur (şifre çözülmez)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT first_name, last_name FROM okul_student WHERE id = %s",
            [student_id],
        )
        satir = cursor.fetchone()
    return (str(satir[0]), str(satir[1]))


def parolasiz_yap() -> None:
    """Test gövdesinde (kişi yazıldıktan SONRA) hesapsız duruma geçer."""
    app_password.lock()
    app_password.state_path().unlink(missing_ok=True)
    config_path(app_password.state_path().parent).unlink(missing_ok=True)


def baska_kurulumun_durumu(parola: str) -> dict[str, Any]:
    """Aynı hesap ve parolayla sarılmış ama BAŞKA bir DEK taşıyan geçerli güvenlik dosyası."""
    return app_password._build_state(
        crypto.new_data_key(),
        hesap_id=TEST_HESAP_ID,
        tanitici=TEST_TANITICI,
        password=parola,
        recovery_key=app_password.generate_recovery_key(),
    )


def ac(password: str = TEST_PAROLA, **fazlasi: Any) -> Account:
    return app_password.unlock(hesap_id=TEST_HESAP_ID, password=password, **fazlasi)


def kur(password: str = YENI_PAROLA, tanitici: str = "yonetici") -> str:
    return app_password.enable(tanitici=tanitici, display_name=KURAN_AD, password=password)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def kayip(parmak_izi_yazili: str) -> Path:
    """Güvenlik dosyası kayıp: DB'de parmak izi var, `guvenlik.json` yok, kilitli.

    Silinen dosyanın içeriği döndürülen yolun yanında `.yedek` olarak saklanır
    (geri koyma senaryosu için).
    """
    yol = app_password.state_path()
    yedek = yol.with_name("guvenlik.json.yedek")
    yedek.write_bytes(yol.read_bytes())
    yol.unlink()
    app_password.lock()
    return yedek


# ---------------------------------------------------------------------------
# İlk program yöneticisi hesabı (yalnız ilk kurulumda)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestEnable:
    def test_ilk_kurulumda_hesap_iz_anahtari_ve_parmak_izi_yazilir(self, parolasiz: Path) -> None:
        kurtarma = kur()

        assert len(kurtarma.split("-")) == 8
        veri = durum()
        assert veri["surum"] == 2 and veri["gecis"] is None
        assert [h["tanitici"] for h in veri["hesaplar"]] == ["yonetici"]
        assert veri["kurtarma"]["no"] == 1
        assert veri["kurtarma"]["tarih"] == timezone.localdate().isoformat()
        assert veri["kurtarma"]["dogrulandi"] is None
        assert "parola" not in veri  # şema 1'in tek parola bölümü yok
        assert crypto.is_unlocked() is True
        parmak = crypto.active_fingerprint()
        assert parmak is not None and SchoolConfig.load().app_password_hash == parmak
        assert config_path(parolasiz).is_file()  # yedek açık anahtarı da yazıldı

        hesap = Account.objects.get()
        assert str(hesap.id) == veri["hesaplar"][0]["id"]
        assert hesap.role == AccountRole.YONETICI and hesap.status == AccountStatus.ACIK
        assert hesap.display_name == KURAN_AD
        assert hesap.password_changed_at is not None
        dek = crypto.active_key()
        assert dek is not None and hesap.seal_matches(dek)
        assert OTURUM.hesap_id() == str(hesap.id)

    def test_iz_anahtari_ayri_uretilir_ve_dek_ile_sifreli_durur(self, parolasiz: Path) -> None:
        """Tasarım §4.6.3: İA DEK'ten TÜREMEZ; DEK'le şifreli olarak `AuditKey`'de durur."""
        kur()
        anahtar = AuditKey.objects.get()
        assert anahtar.valid_from_seq == 1 and anahtar.retired_at is None
        ia = crypto.active_audit_key()
        dek = crypto.active_key()
        assert ia is not None and dek is not None and len(ia) == 32
        assert ia != dek
        assert ia != crypto.derive_subkey(dek, info=b"od-denetim-izi/v1")
        assert base64.b64decode(anahtar.key) == ia
        with connection.cursor() as cursor:
            cursor.execute('SELECT "key" FROM okul_auditkey')
            (ham,) = cursor.fetchone()
        assert str(ham).startswith("gAAAA")

    def test_hesap_sahibinin_adi_sifreli_yazilir(self, parolasiz: Path) -> None:
        kur()
        with connection.cursor() as cursor:
            cursor.execute("SELECT display_name FROM okul_account")
            (ham,) = cursor.fetchone()
        assert str(ham).startswith("gAAAA") and "Örnek" not in str(ham)

    def test_kurulumdan_sonra_kisi_adi_sifreli_yazilir(self, parolasiz: Path) -> None:
        kur()
        ogrenci = ogrenci_olustur()

        ad, soyad = ham_satir(ogrenci.pk)
        assert OGRENCI_AD not in ad and OGRENCI_SOYAD not in soyad
        assert ad.startswith("gAAAA")
        tazelenmis = Student.objects.get(pk=ogrenci.pk)
        assert tazelenmis.full_name == f"{OGRENCI_AD} {OGRENCI_SOYAD}"

    def test_personel_adi_da_sifrelenir(self) -> None:
        kisi = Personnel.objects.create(first_name="AYŞE", last_name="ÖĞRETMEN")
        with connection.cursor() as cursor:
            cursor.execute("SELECT first_name FROM okul_personnel WHERE id = %s", [kisi.pk])
            (ad,) = cursor.fetchone()
        assert str(ad).startswith("gAAAA")

    def test_kurulum_oncesi_yedek_alinir(
        self, parolasiz: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        etiketler: list[str] = []
        monkeypatch.setattr(app_password, "take_transition_backup", etiketler.append)
        kur()
        assert etiketler == ["acilis"]

    def test_dosya_tabanli_veritabaninda_gercek_kopya_alinir(self, tmp_path: Path) -> None:
        """Kopyalama mantığının kendisi (gerçek dosya + gerçek SQLite yedek API'si)."""
        veri_anahtari = b"k" * 32
        ensure_public_config(app_password._data_dir(), veri_anahtari, replace=True)
        kaynak = tmp_path / "db.sqlite3"
        with sqlite3.connect(kaynak) as baglanti:
            baglanti.execute("CREATE TABLE deneme (ad TEXT)")
            baglanti.execute("INSERT INTO deneme VALUES ('EMRE')")
        with mock.patch.object(app_password, "database_file", return_value=kaynak):
            hedef = app_password.take_transition_backup("acilis")
        assert hedef is not None
        assert hedef.name.startswith("pre-parola-acilis-")
        geri_yuklenen = tmp_path / "geri-yuklenen.sqlite3"
        geri_yuklenen.write_bytes(decrypt_bytes(hedef.read_bytes(), veri_anahtari))
        with sqlite3.connect(geri_yuklenen) as kopya:
            assert kopya.execute("SELECT ad FROM deneme").fetchone() == ("EMRE",)

    def test_ikinci_kez_kurulamaz(self) -> None:
        with pytest.raises(app_password.AppPasswordError, match="zaten kurulu"):
            kur()

    def test_politikaya_uymayan_parola_reddedilir(self, parolasiz: Path) -> None:
        with pytest.raises(app_password.AppPasswordError, match="en az 8"):
            kur(password="Kisa-1")
        with pytest.raises(app_password.AppPasswordError, match="eksik: simge"):
            kur(password="Uzunparola12")
        assert app_password.read_state() is None

    def test_gecersiz_taniticiyla_kurulmaz(self, parolasiz: Path) -> None:
        with pytest.raises(app_password.AppPasswordError, match="Tanıtıcı"):
            kur(tanitici="1 yonetici")
        assert app_password.read_state() is None

    @pytest.mark.hesapsiz  # kişi tabloları dolu ama hesap ve parmak izi yok
    def test_ogrenci_varken_reddedilir(self) -> None:
        ogrenci_olustur()
        parolasiz_yap()
        with pytest.raises(app_password.AppPasswordError, match="diğer personel ya da hesap"):
            kur()
        assert app_password.read_state() is None

    @pytest.mark.hesapsiz  # kişi tabloları dolu ama hesap ve parmak izi yok
    def test_personel_varken_reddedilir(self) -> None:
        Personnel.objects.create(first_name="AYŞE", last_name="KAYA")
        parolasiz_yap()
        with pytest.raises(app_password.AppPasswordError, match="diğer personel ya da hesap"):
            kur()

    @pytest.mark.hesapsiz  # kişi tabloları dolu ama hesap ve parmak izi yok
    def test_silinmis_ogrenci_varken_de_reddedilir(self) -> None:
        """Yumuşak silinmiş kişinin adı da kişisel veridir (`all_objects`)."""
        ogrenci_olustur().delete()
        assert not Student.objects.exists()
        parolasiz_yap()
        with pytest.raises(app_password.AppPasswordError, match="diğer personel ya da hesap"):
            kur()

    def test_guvenlik_dosyasi_kayipken_reddedilir(self, kayip: Path) -> None:
        """Tehdit 8 (§4.3): parmak izi doluyken yeni anahtar eski kayıtları okunamaz bırakırdı."""
        with pytest.raises(app_password.AppPasswordError, match="guvenlik.json"):
            kur()
        assert app_password.read_state() is None

    def test_basarisiz_yedekte_dosyalar_geri_alinir(
        self, parolasiz: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def yedek_alinamadi(label: str) -> None:
            raise app_password.AppPasswordError("yedek alınamadı")

        monkeypatch.setattr(app_password, "take_transition_backup", yedek_alinamadi)
        with pytest.raises(app_password.AppPasswordError):
            kur()
        assert app_password.read_state() is None
        assert not config_path(parolasiz).exists()
        assert SchoolConfig.load().app_password_hash == ""

    def test_veritabani_islemi_duserse_hicbiri_kalmaz(
        self, parolasiz: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Tek veritabanı işlemi: hesap, iz anahtarı ve parmak izi birlikte yazılır ya da hiçbiri."""

        def patla(value: str) -> None:
            raise RuntimeError("kesinti")

        monkeypatch.setattr(app_password, "_write_fingerprint", patla)
        with pytest.raises(RuntimeError):
            kur()
        assert not Account.objects.exists() and not AuditKey.objects.exists()
        assert app_password.read_state() is None
        assert crypto.is_unlocked() is False

    def test_veritabani_isleminde_kesilen_kurulum_damgali_dosya_birakir(
        self, parolasiz: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Plan F1b-1: önce `gecis: "KURULUM"` damgalı dosya, sonra tek veritabanı işlemi.

        Gerçek `enable` ara adımda (süreç ölümü) kesilir: damgalı dosya kalır, parmak izi
        ve tablolar boştur. Durum sorgusu bunu yarım kurulum diye arşivler, kurulum
        yeniden yapılır. Dosya damgasız yazılsaydı kesinti tanınmaz, program açılamazdı.
        """

        def oldur(value: str) -> None:
            raise _SurecOldu

        with monkeypatch.context() as yama:
            yama.setattr(app_password, "_write_fingerprint", oldur)
            with pytest.raises(_SurecOldu):
                kur()
        crypto.unload_key()  # süreç ölseydi bellek de giderdi

        assert durum()["gecis"] == app_password.TRANSITION_SETUP
        assert SchoolConfig.load().app_password_hash == ""
        assert not Account.objects.exists() and not AuditKey.objects.exists()

        ozet = app_password.status()

        assert ozet["password_set"] is False and ozet["transition_pending"] is False
        assert app_password.read_state() is None and len(arsivler()) == 1
        kur()
        assert Account.objects.count() == 1

    def test_damga_kaldirilamazsa_kurulum_tamamlanir_ve_oturum_acilir(
        self, parolasiz: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """(3) adımı yazılamazsa DEK oturumsuz bellekte kalmaz: oturum açılır, kurtarma
        anahtarı döner; damgayı ilk durum sorgusu kaldırır (veritabanı işlemi bitmişti)."""
        gercek = app_password._write_state

        def damgasiz_yazim_duser(data: dict[str, Any]) -> None:
            if data.get("gecis") is None:
                raise OSError("dosya kilitli")
            gercek(data)

        with monkeypatch.context() as yama:
            yama.setattr(app_password, "_write_state", damgasiz_yazim_duser)
            kurtarma = kur()

        assert len(kurtarma.split("-")) == 8
        assert OTURUM.hesap_id() == str(Account.objects.get().id)
        assert crypto.is_unlocked() is True
        assert durum()["gecis"] == app_password.TRANSITION_SETUP
        assert app_password.status()["transition_pending"] is False
        assert durum()["gecis"] is None and arsivler() == []

    def test_cift_gonderimde_ikinci_istek_ilk_kurulumu_ezmez(
        self, parolasiz: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sihirbazda çift tıklama (sunucu çok iş parçacıklı): ikinci istek ön koşulları
        geçip Argon2id'deyken birincisi tamamlanır. Ön koşullar kilit altında yeniden
        sorulduğu için ikinci istek "zaten kurulu" ile döner; birincinin dosyasını ezmez,
        silmez, oturumun DEK'ini değiştirmez."""
        gercek = app_password._build_state
        ilk_ayar: list[bytes] = []

        def araya_giren(*args: Any, **kwargs: Any) -> dict[str, Any]:
            ikinci = gercek(*args, **kwargs)
            if not ilk_ayar:  # birinci istek ikincinin Argon2id'si sürerken tamamlanır
                monkeypatch.setattr(app_password, "_build_state", gercek)
                kur(password=YENI_PAROLA)
                ilk_ayar.append(config_path(parolasiz).read_bytes())
            return ikinci

        monkeypatch.setattr(app_password, "_build_state", araya_giren)

        with pytest.raises(app_password.AppPasswordError, match="zaten kurulu"):
            kur(password=UCUNCU_PAROLA)

        hesap = Account.objects.get()
        dek = crypto.active_key()
        assert dek is not None and hesap.seal_matches(dek)
        assert [h["id"] for h in durum()["hesaplar"]] == [str(hesap.id)]
        assert SchoolConfig.load().app_password_hash == crypto.key_fingerprint(dek)
        assert config_path(parolasiz).read_bytes() == ilk_ayar[0]
        assert OTURUM.hesap_id() == str(hesap.id) and AuditKey.objects.count() == 1
        app_password.lock()
        app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)

    def test_geri_alma_yalniz_kendi_yazdigi_dosyayi_siler(
        self, parolasiz: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Veritabanı işlemi düşerken diskteki dosya artık bu kurulumun değilse silinmez."""
        yabanci = app_password._build_state(
            crypto.new_data_key(),
            hesap_id=uuid.uuid4(),
            tanitici="yonetici",
            password=YENI_PAROLA,
            recovery_key=app_password.generate_recovery_key(),
        )

        def araya_yazip_patla(value: str) -> None:
            app_password._write_state(yabanci)  # başka bir yazıcı dosyayı değiştirdi
            raise RuntimeError("kesinti")

        monkeypatch.setattr(app_password, "_write_fingerprint", araya_yazip_patla)
        with pytest.raises(RuntimeError):
            kur()

        assert durum() == yabanci
        assert crypto.is_unlocked() is False and not Account.objects.exists()


# ---------------------------------------------------------------------------
# Yarım kalan kurulum (plan F1b-1: dosya önce, sonra tek DB işlemi, sonra damga)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestYarimKurulum:
    def _kurulum_damgali_dosya(self) -> dict[str, Any]:
        veri = app_password._build_state(
            crypto.new_data_key(),
            hesap_id=uuid.uuid4(),
            tanitici="yonetici",
            password=YENI_PAROLA,
            recovery_key=app_password.generate_recovery_key(),
            gecis=app_password.TRANSITION_SETUP,
        )
        durum_yaz(veri)
        return veri

    def test_kesilen_kurulum_kuruluma_doner(self, parolasiz: Path) -> None:
        """Dosya yazıldı, DB işlemi kesildi: parmak izi boş, tablolar boş → arşiv + kurulum."""
        self._kurulum_damgali_dosya()
        ensure_public_config(parolasiz, b"z" * 32, replace=True)

        ozet = app_password.status()

        assert ozet["password_set"] is False and ozet["transition_pending"] is False
        assert app_password.read_state() is None
        assert len(arsivler()) == 1
        assert not config_path(parolasiz).exists()  # yedek anahtarı da arşivlendi
        kur()  # kurulum yeniden yapılabilir
        assert Account.objects.count() == 1

    def test_kurulum_yeniden_baslatilinca_yarim_dosya_cozulur(self, parolasiz: Path) -> None:
        self._kurulum_damgali_dosya()
        kur()
        assert durum()["gecis"] is None
        assert len(arsivler()) == 1

    def test_islem_tamamlanmissa_yalniz_damga_kalkar(self, yonetici_hesabi: Account) -> None:
        veri = durum()
        veri["gecis"] = app_password.TRANSITION_SETUP
        durum_yaz(veri)

        assert app_password.status()["transition_pending"] is False
        assert durum()["gecis"] is None
        assert arsivler() == []

    @pytest.mark.hesapsiz  # veritabanı boş: hesap ve parmak izi yok
    def test_damgasiz_dosya_bos_veritabaninda_arsivlenmez(self) -> None:
        """Veritabanı silinip boş açıldıysa dosya, hesap parolasıyla geri yüklemenin anahtarıdır."""
        assert SchoolConfig.load().app_password_hash == ""
        app_password.status()
        assert app_password.read_state() is not None
        assert arsivler() == []

    def test_parmak_izi_bos_ama_hesap_varsa_dokunulmaz(self, yonetici_hesabi: Account) -> None:
        SchoolConfig.objects.update(app_password_hash="")
        veri = durum()
        veri["gecis"] = app_password.TRANSITION_SETUP
        durum_yaz(veri)

        app_password.status()

        assert durum()["gecis"] == app_password.TRANSITION_SETUP
        assert arsivler() == []


# ---------------------------------------------------------------------------
# Fail-closed yazma (F1 kod kapısı: kilitliyken Student.save() hata verir)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestFailClosed:
    def test_kilitliyken_student_save_hata_verir(self, kilitli: Path) -> None:
        with pytest.raises(crypto.KeyMissingError), transaction.atomic():
            Student(first_name=OGRENCI_AD, last_name=OGRENCI_SOYAD).save()
        assert not Student.all_objects.exists()

    def test_kilitliyken_mevcut_kaydi_kaydetmek_hata_verir(self, yonetici_hesabi: Account) -> None:
        """Kilitliyken okunan token düz metin gibi geri yazılamaz (anahtar yok)."""
        ogrenci = ogrenci_olustur()
        app_password.lock()
        kilitli_okunan = Student.objects.get(pk=ogrenci.pk)
        assert kilitli_okunan.first_name.startswith("gAAAA")  # okuma patlamaz
        with pytest.raises(crypto.KeyMissingError), transaction.atomic():
            kilitli_okunan.save()
        ac()
        assert Student.objects.get(pk=ogrenci.pk).first_name == OGRENCI_AD

    def test_hesapsizken_student_save_hata_verir(self, parolasiz: Path) -> None:
        with pytest.raises(crypto.KeyMissingError), transaction.atomic():
            Student.objects.create(first_name=OGRENCI_AD, last_name=OGRENCI_SOYAD)
        assert not Student.all_objects.exists()

    def test_bos_ad_anahtarsiz_yazilabilir(self, kilitli: Path) -> None:
        """Boş dize şifrelenmez: "veri yok" hâli DB'de de boş görünür."""
        ogrenci = Student.objects.create(first_name="", last_name="")
        assert ham_satir(ogrenci.pk) == ("", "")


# ---------------------------------------------------------------------------
# Durum sorgusu (fail-closed): dosya VAR ya da parmak izi dolu
# ---------------------------------------------------------------------------
class TestPasswordSetState:
    def test_varsayilan_ortamda_kurulu_ve_acik(self) -> None:
        """DB istemez: dosya varken parmak izine bakılmaz (her istekte çağrılır)."""
        assert app_password.is_password_set() is True
        assert app_password.security_file_missing() is False
        assert app_password.is_locked() is False

    @pytest.mark.django_db
    def test_hesapsiz_ortamda_kurulu_degil(self, parolasiz: Path) -> None:
        assert app_password.is_password_set() is False
        assert app_password.security_file_missing() is False
        assert app_password.is_locked() is False
        ozet = app_password.status()
        assert ozet["password_set"] is False and ozet["security_file_missing"] is False
        assert ozet["account_count"] == 0 and ozet["recovery_key_no"] is None

    @pytest.mark.django_db
    def test_dosya_silinip_parmak_izi_kalinca_kurulu_sayilir(self, kayip: Path) -> None:
        assert app_password.is_password_set() is True
        assert app_password.security_file_missing() is True
        assert app_password.is_locked() is True
        ozet = app_password.status()
        assert ozet["password_set"] is True
        assert ozet["locked"] is True
        assert ozet["security_file_missing"] is True

    def test_durum_ozeti_sema_2_alanlarini_tasir_kisi_adi_tasimaz(self) -> None:
        ozet = app_password.status()
        assert ozet["account_count"] == 1
        assert ozet["recovery_key_no"] == 1
        assert ozet["recovery_key_date"] == timezone.localdate().isoformat()
        assert ozet["corrupt_field_count"] == 0
        assert ozet["transition"] == "" and ozet["transition_pending"] is False
        assert TEST_TANITICI not in json.dumps(ozet)  # tanıtıcı bile durumda yok

    @pytest.mark.django_db
    def test_require_password_set(self, parolasiz: Path) -> None:
        with pytest.raises(app_password.PasswordRequired) as hata:
            app_password.require_password_set()
        # 409 çevirisi tek sınıftan yapılır: PasswordRequired bir KeyMissingError'dır.
        assert isinstance(hata.value, crypto.KeyMissingError)
        assert "program yöneticisi hesabını kurun" in str(hata.value)

    def test_require_password_set_kuruluyken_gecer(self) -> None:
        app_password.require_password_set()


# ---------------------------------------------------------------------------
# Kilit açma / kilitleme (iki depo kuralı 1)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestUnlock:
    def test_dogru_parola_acar(self, yonetici_hesabi: Account) -> None:
        ogrenci = ogrenci_olustur()
        app_password.lock()
        assert app_password.is_locked() is True
        assert OTURUM.hesap_id() is None
        # Kilitliyken okuma çöp (token) döner — patlamaz.
        assert Student.objects.get(pk=ogrenci.pk).first_name.startswith("gAAAA")

        hesap = ac()

        assert app_password.is_locked() is False
        assert str(hesap.id) == TEST_HESAP_ID
        assert OTURUM.hesap_id() == TEST_HESAP_ID
        assert crypto.active_audit_key() == TEST_IA
        assert Student.objects.get(pk=ogrenci.pk).first_name == OGRENCI_AD
        assert Account.objects.get(pk=TEST_HESAP_ID).last_login_at is not None

    def test_yanlis_parola_reddedilir(self, yonetici_hesabi: Account, kilitli: Path) -> None:
        with pytest.raises(app_password.WrongPassword, match="Parola hatalı") as hata:
            ac("Yanlis-Parola-1")
        assert hata.value.code == "parola_yanlis"
        assert app_password.is_locked() is True
        assert sarmal(TEST_HESAP_ID)["hatali"] == 1

    def test_kilit_acma_bayat_yedekleme_json_u_onarir(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        """Çapraz-DEK geri yükleme artığı gibi UYUMSUZ bir yedekleme.json kilidi
        kalıcı kilitlememeli: DEK parmak izine ve mühre karşı kanıtlandıktan sonra
        otorite dosya değil anahtardır (replace=True)."""
        yol = config_path(kilitli)
        ensure_public_config(kilitli, b"x" * 32, replace=True)  # yabancı anahtar
        yabanci = yol.read_bytes()

        ac()

        assert app_password.is_locked() is False
        assert yol.read_bytes() != yabanci

    def test_hatali_deneme_gecikmesi_hesap_basinadir(
        self, yonetici_hesabi: Account, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Gecikme dosyadaki `hatali`dan türer (0/0/1/2/4, sonra 4); hesaplar ayrı sayılır.

        Üretimdeki dizi kullanılır (`_GERCEK_GECIKMELER`); kök `conftest`'in yaması geri alınır.
        """
        muhasip = hesap_ac()
        app_password.lock()
        monkeypatch.setattr(app_password, "FAILURE_DELAYS", _GERCEK_GECIKMELER)
        beklemeler: list[float] = []
        monkeypatch.setattr(time, "sleep", beklemeler.append)

        for _ in range(6):
            with pytest.raises(app_password.WrongPassword):
                ac("Yanlis-Parola-1")
        assert beklemeler == [1.0, 2.0, 4.0, 4.0]
        assert sarmal(TEST_HESAP_ID)["hatali"] == 6

        beklemeler.clear()
        with pytest.raises(app_password.WrongPassword):
            app_password.unlock(hesap_id=muhasip.id, password="Yanlis-Parola-1")
        assert beklemeler == []  # öteki hesabın sayacı ayrı
        assert sarmal(muhasip.id)["hatali"] == 1

        ac()  # doğru parola sayacı sıfırlar
        assert sarmal(TEST_HESAP_ID)["hatali"] == 0

    def test_onuncu_hatada_organ_hesabi_askiya_alinir(self, yonetici_hesabi: Account) -> None:
        """§15 M-12: eşik sabit sayıyla yazılır (sabitin kendisiyle saymak onu sınamazdı)."""
        muhasip = hesap_ac()
        app_password.lock()
        for _ in range(9):
            with pytest.raises(app_password.WrongPassword):
                app_password.unlock(hesap_id=muhasip.id, password="Yanlis-Parola-1")
        assert sarmal(muhasip.id)["askida"] is False
        with pytest.raises(app_password.AccountSuspended, match="askıya alındı") as hata:
            app_password.unlock(hesap_id=muhasip.id, password="Yanlis-Parola-1")
        assert hata.value.code == "hesap_askida"
        assert sarmal(muhasip.id)["askida"] is True
        # Askıdaki hesap doğru parolayla da açılmaz.
        with pytest.raises(app_password.AccountSuspended):
            app_password.unlock(
                hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA
            )

    def test_program_yoneticisinde_aski_yoktur(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        """Kendi kendine hizmet reddi olurdu; kurtarma anahtarı yolu kalır (§15 M-12)."""
        for _ in range(12):
            with pytest.raises(app_password.WrongPassword):
                ac("Yanlis-Parola-1")
        assert sarmal(TEST_HESAP_ID)["askida"] is False
        ac()

    def test_gecikme_dizisi_ve_aski_esigi_tasarimdakidir(self) -> None:
        """Plan F1b-1, TK15, §15 M-12: 0/0/1/2/4 sn (sonra 4); 10. hatada askı."""
        assert _GERCEK_GECIKMELER == (0.0, 0.0, 1.0, 2.0, 4.0)
        assert app_password.SUSPEND_AFTER_FAILURES == 10

    def test_hesap_kurulu_degilken_acilamaz(self, parolasiz: Path) -> None:
        with pytest.raises(app_password.AppPasswordError, match="kurulmadı"):
            ac()

    def test_guvenlik_dosyasi_kayipken_acilamaz(self, kayip: Path) -> None:
        with pytest.raises(app_password.AppPasswordError, match="bulunamadı"):
            ac()

    def test_sema_1_dosyasiyla_acilamaz(self, yonetici_hesabi: Account, kilitli: Path) -> None:
        durum_yaz({"surum": 1, "kdf": {}, "parola": {"salt": "eA==", "sarmal": "eA=="}})
        with pytest.raises(app_password.AppPasswordError, match="okunamıyor"):
            ac()

    def test_baska_veritabaninin_guvenlik_dosyasi_reddedilir(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        """Parmak izi uyuşmazlığı → sessiz bozulma yerine açık ret, DEK yüklenmez."""
        SchoolConfig.objects.update(app_password_hash="v1:" + "0" * 64)
        with pytest.raises(app_password.TwoStoreMismatch, match="ait değil") as hata:
            ac()
        assert hata.value.code == "iki_depo_tutarsiz"
        assert crypto.is_unlocked() is False

    def test_sarmali_olmayan_hesap_reddedilir(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(app_password.TwoStoreMismatch):
            app_password.unlock(hesap_id=uuid.uuid4(), password=TEST_PAROLA)

    def test_iz_anahtari_cozulemezse_giris_acilmaz(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        """İz yazılamazsa yazma yapılamaz: hesap bütünlüğü, sert engel (plan F1b-1)."""
        with connection.cursor() as cursor:
            cursor.execute('UPDATE okul_auditkey SET "key" = %s', ["gAAAAbozuk"])
        with pytest.raises(app_password.AuditKeyUnreadable) as hata:
            ac()
        assert hata.value.code == "iki_depo_tutarsiz"
        assert crypto.is_unlocked() is False

    def test_etkin_iz_anahtari_yoksa_giris_acilmaz(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        AuditKey.objects.update(retired_at=timezone.now())
        with pytest.raises(app_password.AuditKeyUnreadable):
            ac()

    def test_askidaki_hesap_durumu_girisi_kapatir(self, yonetici_hesabi: Account) -> None:
        muhasip = hesap_ac()
        muhurle(muhasip, status=AccountStatus.ASKIDA, suspend_reason="UYELIK_DUSTU")
        app_password.lock()
        with pytest.raises(app_password.AccountSuspended, match="program yöneticisine"):
            app_password.unlock(
                hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA
            )

    def test_gecici_parola_yeni_parola_ister(self, yonetici_hesabi: Account) -> None:
        """Geçici parola oturum açmaz: kilit açma yeni parolayı birlikte ister (409)."""
        muhasip = hesap_ac()
        app_password.lock()

        with pytest.raises(app_password.PasswordRenewalRequired) as hata:
            app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA)
        assert hata.value.code == "parola_yenilenmeli" and hata.value.status_code == 409
        assert crypto.is_unlocked() is False
        with pytest.raises(app_password.AppPasswordError, match="aynı olamaz"):
            app_password.unlock(
                hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=GECICI_PAROLA
            )

        app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)

        tazelenmis = Account.objects.get(pk=muhasip.id)
        assert tazelenmis.status == AccountStatus.ACIK
        assert tazelenmis.password_changed_at is not None
        assert tazelenmis.seal_matches(TEST_DEK)
        app_password.lock()
        with pytest.raises(app_password.WrongPassword):
            app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA)
        app_password.unlock(hesap_id=muhasip.id, password=YENI_PAROLA)

    def test_180_gunu_dolan_parola_yenilenir(self, yonetici_hesabi: Account, kilitli: Path) -> None:
        Account.objects.filter(pk=TEST_HESAP_ID).update(
            password_changed_at=timezone.now() - timedelta(days=181)
        )
        with pytest.raises(app_password.PasswordRenewalRequired):
            ac()
        ac(new_password=YENI_PAROLA)
        assert Account.objects.get(pk=TEST_HESAP_ID).seal_matches(TEST_DEK)

    def test_179_gunluk_parola_yenileme_istemez(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        Account.objects.filter(pk=TEST_HESAP_ID).update(
            password_changed_at=timezone.now() - timedelta(days=179)
        )
        ac()

    def test_kilitleme_oturumu_ve_iz_anahtarini_dusurur(self) -> None:
        app_password.lock()
        assert crypto.is_unlocked() is False
        assert crypto.active_audit_key() is None
        assert OTURUM.hesap_id() is None


# ---------------------------------------------------------------------------
# Parola doğrulama (kurtarma anahtarı yenileme; F4'te DEK işlemleri): yalnız oturumdaki hesap
# ---------------------------------------------------------------------------
class TestVerifyPassword:
    def test_dogru_parola_gecer(self) -> None:
        app_password.verify_password(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    def test_yanlis_parola_reddedilir_ve_gecikme_uygulanir(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(app_password, "FAILURE_DELAYS", (0.0, 0.5))
        beklemeler: list[float] = []
        monkeypatch.setattr(time, "sleep", beklemeler.append)
        for _ in range(2):
            with pytest.raises(app_password.AppPasswordError, match="^Parola hatalı.$"):
                app_password.verify_password(hesap_id=TEST_HESAP_ID, password="Yanlis-Parola-1")
        assert beklemeler == [0.5]
        assert crypto.is_unlocked() is True  # doğrulama kilidi etkilemez

    def test_baska_hesabin_parolasi_ve_kimligi_gecmez(self) -> None:
        """Yenilemede ve DEK işlemlerinde başka hesabın parolası geçmez (plan F1b-1)."""
        baska = str(uuid.uuid4())
        app_password.write_account_wrap(
            data_key=TEST_DEK, hesap_id=baska, tanitici="muhasip", password=YENI_PAROLA
        )
        with pytest.raises(app_password.AppPasswordError, match="oturumdaki hesap"):
            app_password.verify_password(hesap_id=baska, password=YENI_PAROLA)
        with pytest.raises(app_password.WrongPassword):
            app_password.verify_password(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA)

    def test_baska_kurulumun_dosyasiyla_dogrulanmaz(self) -> None:
        """Parolası bilinen yabancı bir guvenlik.json konursa sarmal açılır ama
        DEK yüklü anahtarla eşleşmez → "Parola hatalı."."""
        durum_yaz(baska_kurulumun_durumu(TEST_PAROLA))
        with pytest.raises(app_password.AppPasswordError, match="^Parola hatalı.$"):
            app_password.verify_password(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    def test_kilitliyken_dogrulanamaz(self, kilitli: Path) -> None:
        with pytest.raises(app_password.AppPasswordError, match="kilitli"):
            app_password.verify_password(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    @pytest.mark.django_db
    def test_guvenlik_dosyasi_kayipken_dogrulanamaz(self, kayip: Path) -> None:
        with pytest.raises(app_password.AppPasswordError, match="bulunamadı"):
            app_password.verify_password(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


# ---------------------------------------------------------------------------
# Kurtarma anahtarı
# ---------------------------------------------------------------------------

#: Normalleştirme örnek tablosu — ön yüzde AYNI tablo sınanır
#: (`frontend/src/modules/guvenlik/KurtarmaAnahtariPaneli.test.tsx`,
#: "normalleştirme örnek tablosu"). Biri değişirse öteki de değişmeli.
NORMALLESTIRME_ORNEKLERI: list[tuple[str, str]] = [
    (" test-kurt ", "TESTKURT"),
    ("o0i1b8", "OOIIBB"),
    ("abci-ABCI-ABCİ-ABCı", "ABCIABCIABCIABCI"),
    ("TARİ tarı Tari", "TARITARITARI"),
    ("ŞAKA-12", "AKAI2"),
]


@pytest.mark.parametrize(("yazim", "beklenen"), NORMALLESTIRME_ORNEKLERI)
def test_kurtarma_anahtari_normallestirme_ornek_tablosu(yazim: str, beklenen: str) -> None:
    assert app_password.normalize_recovery_key(yazim) == beklenen


def kurtar(anahtar: str = TEST_KURTARMA_ANAHTARI, **fazlasi: Any) -> Account:
    secenekler: dict[str, Any] = {"hesap_id": TEST_HESAP_ID, "new_password": YENI_PAROLA}
    secenekler.update(fazlasi)
    return app_password.unlock_with_recovery(recovery_key=anahtar, **secenekler)


@pytest.mark.django_db
class TestRecovery:
    def test_kurtarma_anahtariyla_acilir_ve_parola_yenilenir(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        hesap = kurtar()

        assert app_password.is_locked() is False
        assert OTURUM.hesap_id() == TEST_HESAP_ID
        assert hesap.reset_kind == ResetKind.KURTARMA
        assert hesap.reset_notice_pending is True and hesap.reset_at is not None
        assert hesap.reset_by is None
        assert Account.objects.get(pk=TEST_HESAP_ID).seal_matches(TEST_DEK)
        # Eski parola artık geçersiz, yenisi geçerli; kurtarma sarmalı değişmedi.
        app_password.lock()
        with pytest.raises(app_password.WrongPassword):
            ac()
        ac(YENI_PAROLA)
        assert durum()["kurtarma"]["no"] == 1

    def test_kurtarma_anahtari_bicimden_bagimsiz_kabul_edilir(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        kurtar(TEST_KURTARMA_ANAHTARI.replace("-", " ").lower())
        assert app_password.is_locked() is False

    def test_turkce_klavyede_buyuk_harfle_yazilan_anahtar_kabul_edilir(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        """Türkçe klavyede Shift/CapsLock + i noktalı "İ" (U+0130) üretir."""
        turkce = TEST_KURTARMA_ANAHTARI.replace("I", "İ")
        assert "İ" in turkce
        kurtar(turkce)
        assert app_password.is_locked() is False

    def test_yanlis_kurtarma_anahtari_reddedilir(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        with pytest.raises(app_password.AppPasswordError, match="Kurtarma anahtarı hatalı"):
            kurtar("AAAA-BBBB-CCCC-DDDD-EEEE-FFFF-GGGG-HHHH")
        assert crypto.is_unlocked() is False

    def test_kurtarma_anahtari_parola_degisince_gecerli_kalir(
        self, yonetici_hesabi: Account
    ) -> None:
        """Zarf şifreleme: hesap sarmalı değişir, kurtarma sarmalı DEĞİŞMEZ."""
        app_password.change_password(
            hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
        )
        app_password.lock()
        kurtar(new_password=UCUNCU_PAROLA)
        assert app_password.is_locked() is False

    def test_kurtarma_yalniz_program_yoneticisi_icin(self, yonetici_hesabi: Account) -> None:
        """Başka rolün hesabı kurtarma anahtarıyla açılmaz (tasarım §4.4.3)."""
        muhasip = hesap_ac()
        app_password.lock()
        with pytest.raises(app_password.AppPasswordError, match="program yöneticisi"):
            kurtar(hesap_id=muhasip.id)
        with pytest.raises(app_password.AppPasswordError, match="program yöneticisi"):
            kurtar(hesap_id=uuid.uuid4())
        assert crypto.is_unlocked() is False

    def test_hesap_taniticisiyla_da_secilir(self, yonetici_hesabi: Account) -> None:
        """Kurtarmayla geri yüklemeden sonra kilit ekranı listesi boştur; kullanıcı
        tanıtıcıyı yazabilir (Türkçe klavyedeki büyük harfle de)."""
        muhasip = hesap_ac()
        app_password.lock()
        with pytest.raises(app_password.AppPasswordError, match="program yöneticisi"):
            kurtar(hesap_id=muhasip.login_name)
        with pytest.raises(app_password.AppPasswordError, match="program yöneticisi"):
            kurtar(hesap_id="boyle-bir-hesap-yok")

        hesap = kurtar(hesap_id=" YONETİCİ ")

        assert str(hesap.id) == TEST_HESAP_ID
        assert OTURUM.hesap_id() == TEST_HESAP_ID

    def test_kapali_yonetici_hesabi_kurtarilamaz(self, yonetici_hesabi: Account) -> None:
        ikinci = hesap_ac(AccountRole.YONETICI, ad="Örnek İkinci Yönetici")
        muhurle(ikinci, status=AccountStatus.KAPALI, closed_at=timezone.now())
        app_password.lock()
        with pytest.raises(app_password.AppPasswordError, match="program yöneticisi"):
            kurtar(hesap_id=ikinci.id)

    def test_kurtarma_sayaci_ve_askiyi_temizler(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        veri = durum()
        veri["hesaplar"][0].update(hatali=7, askida=True)
        durum_yaz(veri)
        kurtar()
        assert sarmal(TEST_HESAP_ID)["hatali"] == 0
        assert sarmal(TEST_HESAP_ID)["askida"] is False

    def test_sarmali_olmayan_yoneticiye_sarmal_kurulur(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        """Kurtarma anahtarıyla geri yüklemeden sonra `hesaplar` boştur (TK10)."""
        veri = durum()
        veri["hesaplar"] = []
        durum_yaz(veri)

        kurtar()

        assert sarmal(TEST_HESAP_ID)["tanitici"] == TEST_TANITICI
        app_password.lock()
        ac(YENI_PAROLA)

    def test_muhru_tutmayan_yonetici_kurtarilamaz(
        self, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        ham_guncelle(TEST_HESAP_ID, login_name="baska-ad")
        with pytest.raises(app_password.AccountSealMismatch):
            kurtar()
        assert crypto.is_unlocked() is False


# ---------------------------------------------------------------------------
# Parola değiştirme (yalnız açık oturumda, oturumdaki hesap)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestChangePassword:
    def degistir(self, mevcut: str = TEST_PAROLA, yeni: str = YENI_PAROLA) -> None:
        app_password.change_password(
            hesap_id=TEST_HESAP_ID, current_password=mevcut, new_password=yeni
        )

    def test_veri_yeniden_sifrelenmez_ama_okunur_kalir(self, yonetici_hesabi: Account) -> None:
        ogrenci = ogrenci_olustur()
        onceki_token, _ = ham_satir(ogrenci.pk)
        epoch = crypto.key_epoch()

        self.degistir()

        sonraki_token, _ = ham_satir(ogrenci.pk)
        assert sonraki_token == onceki_token  # DEK değişmedi, satırlara dokunulmadı
        assert crypto.key_epoch() == epoch  # oturum değişmedi
        app_password.lock()
        ac(YENI_PAROLA)
        assert Student.objects.get(pk=ogrenci.pk).first_name == OGRENCI_AD

    def test_kor_indeks_parola_degisiminden_sonra_ayni_kalir(
        self, yonetici_hesabi: Account
    ) -> None:
        """Kör indeks (§5.3) anahtarı DEK'ten türer; parola değişimi indeksi bozmaz."""
        onceki = crypto.blind_index("101")
        self.degistir()
        app_password.lock()
        ac(YENI_PAROLA)
        assert crypto.blind_index("101") == onceki

    def test_degisim_ani_yazilir_ve_arsiv_kopyasi_alinir(self, yonetici_hesabi: Account) -> None:
        once = Account.objects.get(pk=TEST_HESAP_ID).password_changed_at
        self.degistir()
        sonra = Account.objects.get(pk=TEST_HESAP_ID).password_changed_at
        assert once is not None and sonra is not None and sonra > once
        assert len(arsivler()) == 1  # sarmal değişimi yapısal yazımdır

    def test_yanlis_mevcut_parola_reddedilir(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(app_password.WrongPassword, match="Parola hatalı"):
            self.degistir(mevcut="Yanlis-Parola-1")

    def test_eskisiyle_ayni_olamaz(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(app_password.AppPasswordError, match="aynı olamaz"):
            self.degistir(yeni=TEST_PAROLA)

    def test_kilitliyken_degistirilemez(self, yonetici_hesabi: Account, kilitli: Path) -> None:
        """Ailede kilitliyken de açıktı ve ikinci bir kilit açma yoluydu (plan F1b-1)."""
        with pytest.raises(app_password.AppPasswordError, match="kilitli"):
            self.degistir()

    def test_baska_hesabin_parolasi_degistirilemez(self, yonetici_hesabi: Account) -> None:
        muhasip = hesap_ac()
        with pytest.raises(app_password.AppPasswordError, match="oturumdaki hesap"):
            app_password.change_password(
                hesap_id=muhasip.id, current_password=GECICI_PAROLA, new_password=YENI_PAROLA
            )


# ---------------------------------------------------------------------------
# Arşiv politikası (plan F1b-1): yalnız yapısal yazım arşivlenir
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_hatali_deneme_sayaci_arsivlenmez(yonetici_hesabi: Account, kilitli: Path) -> None:
    for _ in range(3):
        with pytest.raises(app_password.WrongPassword):
            ac("Yanlis-Parola-1")
    ac()
    assert arsivler() == []


# ---------------------------------------------------------------------------
# Eşleştirme / arama davranışı (ad şifreli — selector'lar Python'da)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestLookupBehaviour:
    def test_ad_filtresi_orm_ile_CALISMAZ(self) -> None:
        """Şifreli alanda DB filtresi daima boş döner — yeni ad sorgusu ORM'e yazılmaz."""
        ogrenci_olustur()
        assert Student.objects.filter(first_name=OGRENCI_AD).first() is None

    def test_ad_aramasi_selector_uzerinden_bozulmaz(self) -> None:
        ogrenci = ogrenci_olustur()
        bulunan = selectors.student_list(search="yilmaz")
        assert [o.pk for o in bulunan] == [ogrenci.pk]

    def test_personel_ad_siralamasi_python_tarafinda(self) -> None:
        Personnel.objects.create(first_name="ZEYNEP", last_name="ÇELİK")
        Personnel.objects.create(first_name="AHMET", last_name="AK")
        sirali = selectors.personnel_sorted()
        assert [p.first_name for p in sirali] == ["AHMET", "ZEYNEP"]


# ---------------------------------------------------------------------------
# API + kilit kapısı
# ---------------------------------------------------------------------------
class TestSecurityApi:
    def test_durum_ucu(self, client: APIClient) -> None:
        resp = client.get("/api/v1/security/status/")
        assert resp.status_code == 200
        veri = resp.json()
        assert veri["password_set"] is True
        assert veri["locked"] is False
        assert veri["security_file_missing"] is False
        assert "ad" in veri["protected_fields"]
        assert veri["account_count"] == 1 and veri["recovery_key_no"] == 1

    @pytest.mark.django_db
    def test_hesapsiz_durum_ucu(self, client: APIClient, parolasiz: Path) -> None:
        veri = client.get("/api/v1/security/status/").json()
        assert veri["password_set"] is False
        assert veri["locked"] is False
        assert veri["security_file_missing"] is False

    @pytest.mark.django_db
    def test_kurma_kilitleme_acma_akisi(self, client: APIClient, parolasiz: Path) -> None:
        resp = client.post(
            "/api/v1/security/enable/",
            {"ad_soyad": KURAN_AD, "parola": YENI_PAROLA},
            format="json",
        )
        assert resp.status_code == 201, resp.json()
        assert len(resp.json()["recovery_key"].split("-")) == 8
        assert resp.json()["login_name_warning"] is None
        hesap_id = str(Account.objects.get().id)

        assert client.post("/api/v1/security/lock/").json()["durum"] == "kilitli"
        resp = client.post(
            "/api/v1/security/unlock/",
            {"hesap": hesap_id, "parola": "Yanlis-Parola-1"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "parola_yanlis"
        assert resp.json()["message"] == "Parola hatalı."

        resp = client.post(
            "/api/v1/security/unlock/",
            {"hesap": hesap_id, "parola": YENI_PAROLA},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["durum"] == "acik"
        assert resp.json()["hesap"]["tanitici"] == "yonetici"
        assert KURAN_AD not in resp.content.decode("utf-8")  # yanıtta kişi adı yok

    @pytest.mark.django_db
    def test_parola_uclarda_kirpilmaz(self, client: APIClient, parolasiz: Path) -> None:
        """Plan F1b-1: parola kırpılmaz (aile kurulumda kırpıp açılışta kırpmıyordu: sonu
        boşluklu parola kurulup açılamazdı). Uçlar gövdeyi olduğu gibi servise verir."""
        kenari_bosluklu = client.post(
            "/api/v1/security/enable/",
            {"ad_soyad": KURAN_AD, "parola": " " + YENI_PAROLA},
            format="json",
        )
        assert kenari_bosluklu.status_code == 400
        assert "başında ya da sonunda" in kenari_bosluklu.json()["message"]
        assert app_password.read_state() is None

        kurulum = client.post(
            "/api/v1/security/enable/", {"ad_soyad": KURAN_AD, "parola": YENI_PAROLA}, format="json"
        )
        assert kurulum.status_code == 201
        kurtarma = kurulum.json()["recovery_key"]
        hesap_id = str(Account.objects.get().id)
        degisim = "/api/v1/security/change-password/"

        yeni_bosluklu = client.post(
            degisim, {"parola": YENI_PAROLA, "yeni_parola": UCUNCU_PAROLA + " "}, format="json"
        )
        assert yeni_bosluklu.status_code == 400
        assert "başında ya da sonunda" in yeni_bosluklu.json()["message"]
        simdiki_bosluklu = client.post(
            degisim, {"parola": YENI_PAROLA + " ", "yeni_parola": UCUNCU_PAROLA}, format="json"
        )
        assert simdiki_bosluklu.status_code == 400
        assert simdiki_bosluklu.json()["code"] == "parola_yanlis"

        client.post("/api/v1/security/lock/")
        acma = client.post(
            "/api/v1/security/unlock/",
            {"hesap": hesap_id, "parola": YENI_PAROLA + " "},
            format="json",
        )
        assert acma.status_code == 400 and acma.json()["code"] == "parola_yanlis"
        kurtarma_bosluklu = client.post(
            "/api/v1/security/recover/",
            {"hesap": hesap_id, "kurtarma_anahtari": kurtarma, "yeni_parola": UCUNCU_PAROLA + " "},
            format="json",
        )
        assert kurtarma_bosluklu.status_code == 400
        assert "başında ya da sonunda" in kurtarma_bosluklu.json()["message"]
        acma = client.post(
            "/api/v1/security/unlock/", {"hesap": hesap_id, "parola": YENI_PAROLA}, format="json"
        )
        assert acma.status_code == 200

    @pytest.mark.django_db
    def test_kurulum_yaniti_taniticidaki_adi_uyarir(
        self, client: APIClient, parolasiz: Path
    ) -> None:
        resp = client.post(
            "/api/v1/security/enable/",
            {"tanitici": "ayse.kaya", "ad_soyad": "Ayşe Kaya", "parola": YENI_PAROLA},
            format="json",
        )
        assert resp.status_code == 201
        assert "adını içeriyor" in resp.json()["login_name_warning"]

    @pytest.mark.django_db
    def test_kilit_acma_ret_kodlari(self, client: APIClient, yonetici_hesabi: Account) -> None:
        muhasip = hesap_ac()
        client.post("/api/v1/security/lock/")
        yenilenmeli = client.post(
            "/api/v1/security/unlock/",
            {"hesap": str(muhasip.id), "parola": GECICI_PAROLA},
            format="json",
        )
        assert yenilenmeli.status_code == 409
        assert yenilenmeli.json()["code"] == "parola_yenilenmeli"
        ham_guncelle(TEST_HESAP_ID, login_name="baska-ad")
        muhur = client.post(
            "/api/v1/security/unlock/",
            {"hesap": TEST_HESAP_ID, "parola": TEST_PAROLA},
            format="json",
        )
        assert muhur.status_code == 409 and muhur.json()["code"] == "hesap_muhru_tutmadi"
        tutarsiz = client.post(
            "/api/v1/security/unlock/",
            {"hesap": str(uuid.uuid4()), "parola": TEST_PAROLA},
            format="json",
        )
        assert tutarsiz.status_code == 409 and tutarsiz.json()["code"] == "iki_depo_tutarsiz"
        veri = durum()
        for hesap in veri["hesaplar"]:
            hesap["askida"] = True
        durum_yaz(veri)
        askida = client.post(
            "/api/v1/security/unlock/",
            {"hesap": str(muhasip.id), "parola": GECICI_PAROLA},
            format="json",
        )
        assert askida.status_code == 403 and askida.json()["code"] == "hesap_askida"
        for resp in (yenilenmeli, muhur, tutarsiz, askida):
            assert resp.json()["code"] not in resp.json()["message"]  # iç kod yüzeye çıkmaz

    @pytest.mark.django_db
    def test_kurulu_hesap_yeniden_kurulamaz(self, client: APIClient) -> None:
        """Açık oturumda ilk hesap ucu hiçbir role açık değildir (rol kapısı, 403); servisin
        ön koşulu da reddeder (derin savunma)."""
        resp = client.post(
            "/api/v1/security/enable/",
            {"ad_soyad": KURAN_AD, "parola": YENI_PAROLA},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.json()["code"] == "rol_yetkisiz"
        with pytest.raises(app_password.AppPasswordError, match="zaten kurulu"):
            app_password.enable(tanitici="yonetici-2", display_name=KURAN_AD, password=YENI_PAROLA)

    @pytest.mark.django_db
    def test_kurtarma_ucu(self, client: APIClient, yonetici_hesabi: Account, kilitli: Path) -> None:
        resp = client.post(
            "/api/v1/security/recover/",
            {
                "hesap": TEST_HESAP_ID,
                "kurtarma_anahtari": TEST_KURTARMA_ANAHTARI,
                "yeni_parola": YENI_PAROLA,
            },
            format="json",
        )
        assert resp.status_code == 200, resp.json()
        assert resp.json()["durum"] == "acik"
        assert resp.json()["hesap"]["id"] == TEST_HESAP_ID

    def test_kaldirma_ucu_yoktur(self, client: APIClient) -> None:
        """`security/disable/` aile iskeletinde söküldü; yol ne adla ne adresle çözülür."""
        with pytest.raises(NoReverseMatch):
            reverse("security-disable")
        resp = client.post("/api/v1/security/disable/", {"password": TEST_PAROLA}, format="json")
        # Açık oturumda çözülemeyen `/api/` yolu rol kapısında 403'tür (fail-closed).
        assert resp.status_code == 403
        assert resp.json()["code"] == "rol_yetkisiz"

    @pytest.mark.django_db
    def test_parola_degistirme_ucu(self, client: APIClient, yonetici_hesabi: Account) -> None:
        resp = client.post(
            "/api/v1/security/change-password/",
            {"parola": TEST_PAROLA, "yeni_parola": YENI_PAROLA},
            format="json",
        )
        assert resp.status_code == 200, resp.json()
        client.post("/api/v1/security/lock/")
        resp = client.post(
            "/api/v1/security/unlock/",
            {"hesap": TEST_HESAP_ID, "parola": YENI_PAROLA},
            format="json",
        )
        assert resp.status_code == 200


@pytest.mark.django_db
class TestLockMiddleware:
    """Kilit kapısı (`apps.okul.lock_middleware`) — settings'te bağlı."""

    def test_kilitliyken_veri_uclari_423_doner(self, client: APIClient, kilitli: Path) -> None:
        resp = client.get("/api/v1/students/")
        assert resp.status_code == 423
        assert resp.json()["code"] == "locked"
        # Tasarım §12.B, §13 D50: her kullanıcı kendi hesabıyla açar.
        assert resp.json()["message"] == (
            "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın (parolanızı unuttuysanız "
            "program yöneticisine başvurun)."
        )

    def test_kilitliyken_acilis_saglik_ucu_calisir(self, client: APIClient, kilitli: Path) -> None:
        """`desktop/server.py` açılışta bu ucu çağırır; 423 dönseydi program AÇILMAZDI."""
        assert client.get("/api/v1/setup/status/").status_code == 200
        # Kurulum sihirbazının YAZMA uçları yine kapalı.
        assert client.post("/api/v1/setup/complete/").status_code == 423

    def test_kilitliyken_guvenlik_uclari_calisir(
        self, client: APIClient, yonetici_hesabi: Account, kilitli: Path
    ) -> None:
        assert client.get("/api/v1/security/status/").status_code == 200
        resp = client.post(
            "/api/v1/security/unlock/",
            {"hesap": TEST_HESAP_ID, "parola": TEST_PAROLA},
            format="json",
        )
        assert resp.status_code == 200
        # Kilit açıldıktan sonra veri uçları normale döner.
        assert client.get("/api/v1/students/").status_code == 200

    def test_hesapsiz_kipte_kapi_gecirir(self, client: APIClient, parolasiz: Path) -> None:
        """Kurulum durumunda okuma açıktır; kişi yazma izin sınıfıyla 409 alır."""
        assert client.get("/api/v1/students/").status_code == 200


def _kurtarma_baslikli_yedek(icerik_yolu: Path, baslik_kaynagi: Path) -> Path:
    """Başlığında `baslik_kaynagi`'nın TK10 izdüşümünü taşıyan şifreli yedek yazar."""
    with sqlite3.connect(icerik_yolu) as baglanti:
        baglanti.execute("CREATE TABLE kayit (deger TEXT)")
    yedek = app_password.backup_dir() / "gunluk-2026-09-21.odbak"
    yedek.parent.mkdir(parents=True, exist_ok=True)
    gecici = icerik_yolu.with_name("baslik-kaynagi")
    gecici.mkdir(exist_ok=True)
    (gecici / "guvenlik.json").write_bytes(baslik_kaynagi.read_bytes())
    yedek.write_bytes(
        encrypt_bytes(
            icerik_yolu.read_bytes(),
            private_key_from_data_key(TEST_DEK).public_key(),
            recovery_header=recovery_metadata(gecici),
        )
    )
    return yedek


# ---------------------------------------------------------------------------
# Güvenlik dosyası kayıp kilidi (F1 kod kapısı: guvenlik.json silinince fail-closed)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestGuvenlikDosyasiKayip:
    def test_guvenlik_json_silinince_fail_closed(self, client: APIClient, kayip: Path) -> None:
        """Kilitliyken dosya silinir: program kuruluma DÖNMEZ; veri uçları 423
        `guvenlik_dosyasi_kayip`, kişi yazma 423 (409 değil), yeni hesap kurulamaz."""
        resp = client.get("/api/v1/students/")
        assert resp.status_code == 423
        assert resp.json() == {
            "code": "guvenlik_dosyasi_kayip",
            "message": (
                "Güvenlik dosyası (guvenlik.json) bulunamadı ya da okunamıyor. Kayıtlar "
                "açılamaz. Dosyanın sağlam bir kopyasını veri klasörüne geri koyun ya da "
                "bir yedekten geri yükleyin."
            ),
            "fields": {},
        }
        yazma = client.post(
            "/api/v1/students/", {"first_name": "A", "last_name": "B"}, format="json"
        )
        assert yazma.status_code == 423
        kurma = client.post(
            "/api/v1/security/enable/",
            {"ad_soyad": KURAN_AD, "parola": YENI_PAROLA},
            format="json",
        )
        assert kurma.status_code == 423
        assert app_password.read_state() is None

    def test_acik_kalan_yollar(self, client: APIClient, kayip: Path) -> None:
        assert client.get("/api/v1/setup/status/").status_code == 200
        ozet = client.get("/api/v1/security/status/")
        assert ozet.status_code == 200
        assert ozet.json()["security_file_missing"] is True
        assert ozet.json()["password_set"] is True
        assert client.get("/api/v1/backups/").status_code == 200
        # Oturum özeti salt okurdur; kayıp kilidinde de yanıt verir.
        oturum = client.get("/api/v1/security/session/")
        assert oturum.status_code == 200
        assert oturum.json()["durum"] == "guvenlik_dosyasi_kayip"

    def test_kilit_acma_ve_diger_guvenlik_uclari_kapali(
        self, client: APIClient, kayip: Path
    ) -> None:
        for yol in (
            "/api/v1/security/unlock/",
            "/api/v1/security/recover/",
            "/api/v1/security/change-password/",
        ):
            resp = client.post(yol, {"password": TEST_PAROLA}, format="json")
            assert resp.status_code == 423, yol
            assert resp.json()["code"] == "guvenlik_dosyasi_kayip"
        assert client.get("/api/v1/updates/latest/").status_code == 423

    def test_anahtar_bellekteyken_dosya_kaybolsa_da_kapi_kapanir(
        self, client: APIClient, parmak_izi_yazili: str
    ) -> None:
        app_password.state_path().unlink()
        assert crypto.is_unlocked() is True
        resp = client.get("/api/v1/students/")
        assert resp.status_code == 423
        assert resp.json()["code"] == "guvenlik_dosyasi_kayip"

    def test_dosya_geri_konunca_olagan_kilide_doner(
        self, client: APIClient, kayip: Path, yonetici_hesabi: Account
    ) -> None:
        app_password.state_path().write_bytes(kayip.read_bytes())
        resp = client.get("/api/v1/students/")
        assert resp.status_code == 423
        assert resp.json()["code"] == "locked"
        acma = client.post(
            "/api/v1/security/unlock/",
            {"hesap": TEST_HESAP_ID, "parola": TEST_PAROLA},
            format="json",
        )
        assert acma.status_code == 200
        assert client.get("/api/v1/students/").status_code == 200

    def test_yedekten_geri_yukleme_ile_kayip_kilitten_cikilir(
        self,
        client: APIClient,
        kayip: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Çıkış yolu gerçekten çalışır: geri yükleme ucu kayıp kilidinde açıktır ve
        `guvenlik.json`'u yedeğin başlığından YALNIZ kurtarma bölümüyle yazar (TK10)."""
        yedek = _kurtarma_baslikli_yedek(tmp_path / "yedek-icerik.sqlite3", kayip)
        hedef_db = tmp_path / "canli" / "db.sqlite3"
        monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(hedef_db))
        # Test veritabanı bellek içidir; takas öncesi kapatma onu yok ederdi.
        monkeypatch.setattr(connections, "close_all", lambda: None)

        liste = client.get("/api/v1/backups/")
        assert [s["name"] for s in liste.json()["backups"]] == [yedek.name]
        parolali = client.post(
            "/api/v1/backups/restore/",
            {"name": yedek.name, "hesap": TEST_TANITICI, "password": TEST_PAROLA},
            format="json",
        )
        # Oturum yokken parola yolu reddedilir (başlıkta hesap sarmalı da yoktur, TK10).
        assert parolali.status_code == 400
        assert "kurtarma anahtarıyla" in parolali.json()["message"]
        resp = client.post(
            "/api/v1/backups/restore/",
            {"name": yedek.name, "recovery_key": TEST_KURTARMA_ANAHTARI},
            format="json",
        )

        assert resp.status_code == 200, resp.json()
        assert resp.json()["state_written"] is True
        yazilan = durum()
        assert yazilan["hesaplar"] == []
        assert yazilan["kurtarma"]["no"] == 1 and yazilan["kurtarma"]["dogrulandi"]
        assert app_password._unwrap_with_recovery(yazilan, TEST_KURTARMA_ANAHTARI) == TEST_DEK


# Dosya SİLİNMEZ ama kullanılamaz hâle gelir (boşaltılır, bozulur, bölümü eksik
# kalır, şema 1 kalır). Kural `desktop.backup_crypto.is_usable_security_state` —
# yedek başlığının kuralıyla aynı.
_KULLANILAMAZ_GUVENLIK = {
    "bos": b"",
    "bozuk_json": b"{bozuk",
    "sozluk_degil": b"[]",
    "bolumler_eksik": b'{"surum": 2, "kdf": {}, "hesaplar": [], "gecis": null}',
    "sema_1": b'{"surum": 1, "kdf": {}, "parola": {"salt": "eA==", "sarmal": "eA=="}}',
}


@pytest.mark.django_db
@pytest.mark.parametrize("icerik", _KULLANILAMAZ_GUVENLIK.values(), ids=_KULLANILAMAZ_GUVENLIK)
class TestKullanilamazGuvenlikDosyasi:
    """Denetçi bulgusu: boş/bozuk guvenlik.json'da durum ucu 500, kilit ve kayıp ekranı
    görünmüyor, geri yükleme 423 ile kapalıydı. Artık kayıp kilidiyle aynı sınıftır."""

    @pytest.fixture
    def bozuk(self, parmak_izi_yazili: str, icerik: bytes) -> bytes:
        """Kilitliyken dosyanın içi bozulur; sağlam içerik döndürülür (geri koyma için)."""
        yol = app_password.state_path()
        saglam = yol.read_bytes()
        yol.write_bytes(icerik)
        app_password.lock()
        return saglam

    def test_durum_ucu_500_degil_kayip_bildirir(self, client: APIClient, bozuk: bytes) -> None:
        resp = client.get("/api/v1/security/status/")

        assert resp.status_code == 200, resp.content
        veri = resp.json()
        assert veri["security_file_missing"] is True
        assert veri["password_set"] is True
        assert veri["transition_pending"] is False
        assert app_password.security_file_missing() is True
        assert OTURUM.durum() == "guvenlik_dosyasi_kayip"

    def test_kayip_kilidi_uygulanir_cikis_yollari_acik(
        self, client: APIClient, bozuk: bytes
    ) -> None:
        veri = client.get("/api/v1/students/")
        assert veri.status_code == 423
        assert veri.json()["code"] == "guvenlik_dosyasi_kayip"
        kurma = client.post(
            "/api/v1/security/enable/",
            {"ad_soyad": KURAN_AD, "parola": YENI_PAROLA},
            format="json",
        )
        assert kurma.status_code == 423
        assert client.get("/api/v1/backups/").status_code == 200
        eksik = client.post("/api/v1/backups/restore/", {}, format="json")
        assert eksik.status_code == 400  # görünüme ulaştı: doğrulama reddi, 423 değil

    def test_saglam_dosya_geri_konunca_olagan_kilide_doner(
        self, client: APIClient, bozuk: bytes
    ) -> None:
        app_password.state_path().write_bytes(bozuk)

        assert client.get("/api/v1/security/status/").json()["security_file_missing"] is False
        assert client.get("/api/v1/students/").json()["code"] == "locked"

    def test_yedekten_geri_yukleme_bozuk_dosyayi_arsivleyip_basligi_yazar(
        self,
        client: APIClient,
        bozuk: bytes,
        icerik: bytes,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        saglam = tmp_path / "saglam-guvenlik.json"
        saglam.write_bytes(bozuk)
        yedek = _kurtarma_baslikli_yedek(tmp_path / "yedek-icerik.sqlite3", saglam)
        monkeypatch.setitem(
            settings.DATABASES["default"], "NAME", str(tmp_path / "canli" / "db.sqlite3")
        )
        monkeypatch.setattr(connections, "close_all", lambda: None)

        resp = client.post(
            "/api/v1/backups/restore/",
            {"name": yedek.name, "recovery_key": TEST_KURTARMA_ANAHTARI},
            format="json",
        )

        assert resp.status_code == 200, resp.json()
        assert resp.json()["state_written"] is True
        assert durum()["hesaplar"] == []
        # Bozuk dosya silinmez, arşivlenir.
        assert [a.read_bytes() for a in arsivler()] == [icerik]


def test_parmak_izi_yokken_bozuk_dosya_da_kayip_sayilir_ve_db_istemez() -> None:
    """Fail-closed: dosyanın neyi koruduğu bilinemez; kural parmak izinden bağımsızdır.
    Dosya varken karar yalnız dosyadan verilir (DB'ye gidilmez — bu test DB istemez;
    `security_file_missing` her API isteğinde çağrılır)."""
    app_password.state_path().write_bytes(b"")
    app_password.lock()

    assert app_password.security_file_missing() is True


@pytest.mark.django_db
@pytest.mark.hesapsiz  # sıfırlama koşulu: parmak izi ve şifreli tablolar boş
def test_parmak_izi_yokken_bozuk_dosya_durum_ozetinde_kayip_ve_sifirlanabilir() -> None:
    """Durum özeti kayıp hâlinde sıfırlama yolunun koşullarını da sorar (DB'ye gider:
    parmak izi + şifreli tablolar). Parmak izi boş ve kişi yokken yol açıktır."""
    app_password.state_path().write_bytes(b"")
    app_password.lock()

    ozet = app_password.status()
    assert ozet["security_file_missing"] is True
    assert ozet["password_set"] is True
    assert ozet["reset_available"] is True


def test_bozuk_dosya_iletisi_olmayan_otomatik_kopyayi_anmaz() -> None:
    """Eski ileti "veri klasöründeki yedeğinizden geri alın" diyordu; öyle bir kopya yok."""
    app_password.state_path().write_text("bu json değil", encoding="utf-8")

    with pytest.raises(app_password.AppPasswordError) as hata:
        app_password.read_state()

    assert "yedeğinizden" not in str(hata.value)
    assert "bir yedekten geri yükleyin" in str(hata.value)


def test_aileden_kalan_gecis_araclari_yoktur() -> None:
    """Düz metin şifreleme geçişi ve görev devri kalktı (plan F1b-1; tasarım §13 D29)."""
    for ad in (
        "disable",
        "_run_decrypt_pass",
        "_rewrite_rows",
        "resume_pending",
        "TRANSITION_ENCRYPTING",
        "TRANSITION_DONE",
        "start_handover",
        "handover_info",
        "_unwrap_with_password",
    ):
        assert not hasattr(app_password, ad), ad
    for ad in ("plaintext_writes", "writes_encrypted"):
        assert not hasattr(crypto, ad), ad


# ---------------------------------------------------------------------------
# Konsol kurtarma aracı
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestManagementCommand:
    """`manage.py app_password …` — arayüz açılamadığında destek elinin yolu."""

    def _kosu(self, *args: str, **secenekler: Any) -> str:
        cikti = StringIO()
        call_command("app_password", *args, stdout=cikti, **secenekler)
        return cikti.getvalue()

    def test_durum_ozet_basar(self) -> None:
        cikti = self._kosu("status")
        assert "Hesap kurulu     : evet" in cikti
        assert "Hesap sayısı     : 1" in cikti
        assert "1 numaralı" in cikti
        assert "ad" in cikti

    def test_durum_kayip_dosyayi_bildirir(self, kayip: Path) -> None:
        cikti = self._kosu("status")
        assert "KAYIP" in cikti
        assert "guvenlik.json" in cikti

    def test_kur(self, parolasiz: Path) -> None:
        cikti = self._kosu("enable", ad=KURAN_AD, password=YENI_PAROLA)
        assert "KURTARMA ANAHTARI" in cikti
        assert app_password.is_password_set() is True
        assert Account.objects.get().login_name == "yonetici"

    @pytest.mark.parametrize("islem", ["disable", "resume"])
    def test_kaldirilan_komutlar_yoktur(self, islem: str) -> None:
        with pytest.raises(CommandError):
            self._kosu(islem, password=TEST_PAROLA)

    def test_kurtar_yeni_parola_belirler(self, yonetici_hesabi: Account, kilitli: Path) -> None:
        self._kosu(
            "recover",
            hesap=TEST_TANITICI,
            recovery_key=TEST_KURTARMA_ANAHTARI,
            new_password=YENI_PAROLA,
        )
        assert app_password.is_locked() is False

    def test_kurtarmada_bilinmeyen_tanitici_command_error(self, kilitli: Path) -> None:
        with pytest.raises(CommandError, match="bulunamadı"):
            self._kosu(
                "recover",
                hesap="yok-boyle",
                recovery_key=TEST_KURTARMA_ANAHTARI,
                new_password=YENI_PAROLA,
            )

    def test_politika_ihlali_command_error_verir(self, parolasiz: Path) -> None:
        with pytest.raises(CommandError, match="en az 8"):
            self._kosu("enable", ad=KURAN_AD, password="Kisa-1")


def test_varsayilan_ortamin_guvenlik_dosyasi_sema_2_dir() -> None:
    """conftest sözleşmesi: geçerli, tek hesaplı şema 2 durum dosyası (DB istemez)."""
    veri = json.loads(app_password.state_path().read_text(encoding="utf-8"))
    assert veri["surum"] == 2 and veri["gecis"] is None
    assert [h["id"] for h in veri["hesaplar"]] == [TEST_HESAP_ID]
    assert app_password._unwrap_with_account(veri, TEST_TANITICI, TEST_PAROLA) == TEST_DEK
    assert crypto.active_fingerprint() == crypto.key_fingerprint(TEST_DEK)
    assert OTURUM.hesap_id() == TEST_HESAP_ID
