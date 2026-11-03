"""Hesaplar (tasarım §4.4.1, §4.4.5, §4.6.1; F1b-1) — servisler, kısıtlar, iki depo kuralı, mühür.

Varsayılan ortam `backend/conftest.py`'dedir; buradaki testler `yonetici_hesabi`
fixtürüyle program yöneticisinin satırını kurar ve servisleri onunla çağırır. Rol
denetimi (yalnız program yöneticisi) 2. adımdadır: burada işlemi yapanın açık ve
mühürlü bir hesap olması sınanır.

F1 kapısının iki testi buradadır (tasarım §10.6):
`test_iki_depo_dort_hali[giris, acma_yarida, kapama_yarida, geri_yukleme_sonrasi]` ve
`test_hesap_muhru_bozulunca_giris_reddedilir_satir_degismez`.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from typing import Any

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.okul.models import (
    MAX_AUDIT_BOARD_ACCOUNTS,
    Account,
    AccountRole,
    AccountStatus,
    AuditKey,
    AuditTrail,
    DeletionNotAllowed,
    ResetKind,
)
from apps.okul.oturum import Yazar, yazar_olarak
from apps.okul.services import app_password, hesap_kurallari, hesaplar
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    UCUNCU_PAROLA,
    YENI_PAROLA,
    arsiv_yaz,
    arsivdeki_kimlikler,
    arsivler,
    durum,
    durum_yaz,
    ham_guncelle,
    ham_satir,
    hesap_ac,
    muhurle,
    sarmal,
    sarmal_kimlikleri,
)
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_PAROLA
from shared import crypto

pytestmark = pytest.mark.django_db


def ilk_giris(hesap: Account, yeni: str = YENI_PAROLA) -> None:
    """Geçici parolayla ilk giriş (yeni parolayla); sonra program yöneticisine döner."""
    app_password.lock()
    app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA, new_password=yeni)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


def arsivlerde_yok(*hesap_idler: object) -> None:
    """Verilen hesapların sarmalı HİÇBİR arşivde yok; program yöneticisininki her arşivde var.

    Elle yazılan tek arşive bakmak yetmez: kapama, yapısal yazımın kendi arşiv kopyasını
    da alır (sarmal o kopyada da durur; TK11).
    """
    assert arsivler(), "arşiv bekleniyordu"
    for arsiv in arsivler():
        kimlikler = arsivdeki_kimlikler(arsiv)
        for hesap_id in hesap_idler:
            assert str(hesap_id) not in kimlikler, arsiv.name
        assert TEST_HESAP_ID in kimlikler, arsiv.name  # başka sarmala dokunulmaz


# ---------------------------------------------------------------------------
# Hesap açma
# ---------------------------------------------------------------------------
class TestHesapAcma:
    def test_once_satir_sonra_sarmal_parola_yenilenmeli(self, yonetici_hesabi: Account) -> None:
        hesap = hesap_ac()

        assert hesap.status == AccountStatus.PAROLA_YENILENMELI
        assert hesap.login_name == "muhasip"
        assert hesap.opened_by_id == yonetici_hesabi.id
        assert hesap.seal_matches(TEST_DEK)
        assert sarmal(hesap.id)["tanitici"] == "muhasip"
        assert sarmal(hesap.id)["hatali"] == 0 and sarmal(hesap.id)["askida"] is False
        assert Account.objects.get(pk=hesap.id).display_name == "Örnek Muhasip"

    def test_kilitliyken_hesap_acilmaz(self, yonetici_hesabi: Account) -> None:
        app_password.lock()
        with pytest.raises(hesaplar.AccountServiceError, match="kilitli"):
            hesap_ac()

    def test_islemi_yapan_acik_hesap_olmali(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(hesaplar.AccountServiceError, match="açık değil"):
            hesaplar.open_account(
                by_hesap_id=uuid.uuid4(),
                role=AccountRole.MUHASIP,
                tanitici="muhasip",
                display_name="Örnek Muhasip",
                temp_password=GECICI_PAROLA,
            )

    def test_islemi_yapan_yazar_baglamindaki_hesap_olmali(self, yonetici_hesabi: Account) -> None:
        """Satırın hesabı yazardan (istek başındaki oturum hesabı), `opened_by`/`closed_by`/
        `reset_by` `by_hesap_id`'den gelir: ikisi ayrışırsa kayıt başkasının adına yazılırdı.
        Açık ve mühürlü başka bir program yöneticisi adına yapılan her hesap işlemi reddedilir,
        hiçbir şey yazılmaz (2. adımın Kullanıcılar uçlarının güvenlik ağı)."""
        ikinci = hesap_ac(AccountRole.YONETICI, ad="Örnek İkinci Yönetici")
        muhurle(Account.objects.get(pk=ikinci.id), status=AccountStatus.ACIK)
        hedef = hesap_ac()
        once = (AuditTrail.objects.count(), ham_satir(hedef.id), sarmal(hedef.id))
        islemler: list[Callable[[], object]] = [
            lambda: hesaplar.open_account(
                by_hesap_id=ikinci.id,
                role=AccountRole.SEKRETER,
                tanitici="sekreter",
                display_name="Örnek Sekreter",
                temp_password=GECICI_PAROLA,
            ),
            lambda: hesaplar.close_account(by_hesap_id=ikinci.id, hesap_id=hedef.id),
            lambda: hesaplar.reset_password(
                by_hesap_id=ikinci.id, hesap_id=hedef.id, temp_password=YENI_PAROLA
            ),
            lambda: hesaplar.unsuspend(by_hesap_id=ikinci.id, hesap_id=hedef.id),
            lambda: hesaplar.remove_orphan_wraps(by_hesap_id=ikinci.id, hesap_idler=[]),
            lambda: hesaplar.acknowledge_reset_notice(hesap_id=ikinci.id),
        ]

        for islem in islemler:  # varsayılan yazar: oturumdaki ilk program yöneticisi
            with pytest.raises(hesaplar.AccountServiceError, match="açık değil"):
                islem()

        assert (AuditTrail.objects.count(), ham_satir(hedef.id), sarmal(hedef.id)) == once
        assert not Account.objects.filter(role=AccountRole.SEKRETER).exists()
        # Yazar o hesapsa işlem yapılır; satır da o hesabındır.
        with yazar_olarak(Yazar(hesap_id=str(ikinci.id), rol="yonetici")):
            kapali = hesaplar.close_account(by_hesap_id=ikinci.id, hesap_id=hedef.id)
        assert kapali.closed_by_id == ikinci.id
        satir = AuditTrail.objects.filter(object_id=str(hedef.id)).order_by("-seq").first()
        assert satir is not None and str(satir.account_id) == str(ikinci.id)

    def test_islemi_yapanin_muhru_tutmazsa_reddedilir(self, yonetici_hesabi: Account) -> None:
        ham_guncelle(TEST_HESAP_ID, login_name="baska-ad")
        with pytest.raises(app_password.AccountSealMismatch):
            hesap_ac()
        assert not Account.objects.filter(role=AccountRole.MUHASIP).exists()

    @pytest.mark.parametrize(
        "rol",
        [
            AccountRole.BASKAN,
            AccountRole.BASKAN_YARDIMCISI,
            AccountRole.MUHASIP,
            AccountRole.SEKRETER,
            AccountRole.MUDUR,
        ],
    )
    def test_tek_hesapli_rolde_ikinci_acik_hesap_acilmaz(
        self, yonetici_hesabi: Account, rol: str
    ) -> None:
        ilk = hesap_ac(rol, ad="Örnek Birinci")
        with pytest.raises(hesaplar.AccountServiceError, match="açık bir hesap zaten var"):
            hesap_ac(rol, tanitici="ikinci-hesap", ad="Örnek İkinci")
        hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=ilk.id)
        hesap_ac(rol, tanitici="ikinci-hesap", ad="Örnek İkinci")  # kapanınca açılır

    def test_denetleme_kurulunda_en_cok_uc_hesap(self, yonetici_hesabi: Account) -> None:
        tanitici = [
            hesap_ac(AccountRole.DENETLEME_KURULU, ad=f"Örnek Üye {i}").login_name
            for i in range(MAX_AUDIT_BOARD_ACCOUNTS)
        ]
        assert tanitici == ["dk-1", "dk-2", "dk-3"]
        with pytest.raises(hesaplar.AccountServiceError, match="en çok 3"):
            hesap_ac(AccountRole.DENETLEME_KURULU, tanitici="dk-4", ad="Örnek Üye 4")

    def test_ikinci_program_yoneticisi_acilabilir(self, yonetici_hesabi: Account) -> None:
        assert hesaplar.default_login_name(AccountRole.YONETICI) == "yonetici-2"
        ikinci = hesap_ac(AccountRole.YONETICI, ad="Örnek İkinci Yönetici")
        assert ikinci.login_name == "yonetici-2"

    def test_acik_hesaplarda_tanitici_tekildir(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(hesaplar.AccountServiceError, match="başka hesapta"):
            hesap_ac(tanitici="yonetici")

    def test_gecersiz_rol_ve_tanitici_reddedilir(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(hesaplar.AccountServiceError, match="rol"):
            hesap_ac("sayman")
        with pytest.raises(hesaplar.AccountServiceError, match="Tanıtıcı"):
            hesap_ac(tanitici="Muhasip Bey")

    def test_gecici_parola_politikaya_uymali(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(hesaplar.AccountServiceError, match="eksik"):
            hesap_ac(parola="gecicigecici")


# ---------------------------------------------------------------------------
# Hesap kapama (TK11)
# ---------------------------------------------------------------------------
class TestHesapKapama:
    def test_satir_kalir_sarmal_dosyadan_ve_arsivlerden_silinir(
        self, yonetici_hesabi: Account
    ) -> None:
        hesap = hesap_ac()
        arsiv = arsiv_yaz("2026-10-01-120000", durum())
        assert str(hesap.id) in arsivdeki_kimlikler(arsiv)
        once = len(arsivler())

        hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)

        kapali = Account.objects.get(pk=hesap.id)
        assert kapali.status == AccountStatus.KAPALI
        assert kapali.closed_at is not None and kapali.closed_by_id == yonetici_hesabi.id
        assert kapali.seal_matches(TEST_DEK)
        assert str(hesap.id) not in sarmal_kimlikleri()
        # Hesap silme yapısal yazımdır: kopya alınır, kapanan sarmal o kopyadan da silinir.
        assert len(arsivler()) == once + 1
        arsivlerde_yok(hesap.id)

    def test_yarim_yazim_artiklari_silinir(self, yonetici_hesabi: Account) -> None:
        """Kesilmiş atomik yazımın `.tmp` artığı sarmal taşıyabilir ve `*.json` desenine
        girmez (TK11): kapama da her kilit açılışı da artıkları siler."""
        hesap = hesap_ac()
        yol = app_password.state_path()
        artiklar = [
            yol.with_name(yol.name + ".tmp"),
            yol.with_name("guvenlik-arsiv-2026-10-01-120000.json.tmp"),
        ]

        def artik_yaz() -> None:
            for artik in artiklar:
                artik.write_text(json.dumps(durum(), ensure_ascii=False), encoding="utf-8")

        artik_yaz()
        app_password.lock()
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
        assert [a for a in artiklar if a.exists()] == []

        artik_yaz()
        hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
        assert [a for a in artiklar if a.exists()] == []
        assert str(hesap.id) not in sarmal_kimlikleri()

    def test_son_program_yoneticisi_kapatilamaz(
        self, yonetici_hesabi: Account, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Oturumdaki hesap kendi hesabını kapatamaz (plan F1b-2 "Kendi hesabı"): son program
        yöneticisi kuralı bugün servis yolundan erişilmez, derin savunma olarak kalır — kendi
        hesabı kuralı devre dışıyken sınanır."""
        with pytest.raises(hesaplar.AccountServiceError) as hata:
            hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=TEST_HESAP_ID)
        assert str(hata.value) == hesaplar._OWN_CLOSE_MESSAGE
        with monkeypatch.context() as yama:
            yama.setattr(hesaplar, "_kendi_hesabi_mi", lambda _aktor, _hesap_id: False)
            with pytest.raises(hesaplar.AccountServiceError, match="Son program yöneticisi"):
                hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=TEST_HESAP_ID)
        ikinci = hesap_ac(AccountRole.YONETICI, ad="Örnek İkinci Yönetici")
        hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=ikinci.id)
        assert Account.objects.get(pk=TEST_HESAP_ID).status == AccountStatus.ACIK

    def test_kapali_hesap_yeniden_kapatilmaz_ve_kapali_kalir(
        self, yonetici_hesabi: Account
    ) -> None:
        hesap = hesap_ac()
        hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
        with pytest.raises(hesaplar.AccountServiceError, match="kapalı"):
            hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
        with pytest.raises(hesaplar.AccountServiceError, match="kapalı"):
            hesaplar.reset_password(
                by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
            )

    def test_askidaki_hesap_kapatilabilir(self, yonetici_hesabi: Account) -> None:
        hesap = hesap_ac()
        muhurle(hesap, status=AccountStatus.ASKIDA, suspend_reason="UYELIK_DUSTU")
        kapali = hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
        assert kapali.suspend_reason == ""

    def test_hesap_satiri_silinmez(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(DeletionNotAllowed):
            yonetici_hesabi.delete()
        with pytest.raises(DeletionNotAllowed):
            Account.objects.all().delete()
        with pytest.raises(DeletionNotAllowed):
            AuditKey.objects.all().delete()
        with pytest.raises(DeletionNotAllowed):
            AuditKey.objects.get().delete()
        assert Account.objects.count() == 1 and AuditKey.objects.count() == 1


# ---------------------------------------------------------------------------
# Parola sıfırlama ve askıdan çıkarma
# ---------------------------------------------------------------------------
class TestSifirlamaVeAski:
    def test_sifirlama_gecici_parola_verir_ve_iz_birakir(self, yonetici_hesabi: Account) -> None:
        hesap = hesap_ac()
        ilk_giris(hesap)
        veri = durum()
        for kayit in veri["hesaplar"]:
            if kayit["id"] == str(hesap.id):
                kayit.update(hatali=10, askida=True)
        durum_yaz(veri)

        sifirlanan = hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password="Baska-Gecici-9"
        )

        assert sifirlanan.status == AccountStatus.PAROLA_YENILENMELI
        assert sifirlanan.reset_kind == ResetKind.SIFIRLAMA
        assert sifirlanan.reset_by_id == yonetici_hesabi.id
        assert sifirlanan.reset_notice_pending is True
        assert sifirlanan.seal_matches(TEST_DEK)
        assert sarmal(hesap.id)["hatali"] == 0 and sarmal(hesap.id)["askida"] is False
        app_password.lock()
        with pytest.raises(app_password.WrongPassword):
            app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)
        with pytest.raises(app_password.PasswordRenewalRequired):
            app_password.unlock(hesap_id=hesap.id, password="Baska-Gecici-9")

    def test_sarmalsiz_satira_sifirlama_sarmal_kurar(self, yonetici_hesabi: Account) -> None:
        hesap = hesap_ac()
        app_password.remove_account_wraps({str(hesap.id)})
        hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
        )
        assert str(hesap.id) in sarmal_kimlikleri()

    def test_sifirlamada_once_satir_sonra_sarmal(
        self, yonetici_hesabi: Account, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sarmal adımı kesilirse satır zaten `PAROLA_YENILENMELI`dir: eski parola zorunlu
        değişim OLMADAN oturum açmaz (ters sıra, program yöneticisinin bildiği geçici
        parolayı değişimsiz geçerli bırakırdı; hesaplar modül başlığı)."""
        hesap = hesap_ac()
        ilk_giris(hesap)  # parolası YENI_PAROLA, durumu ACIK

        def kesinti(**_: object) -> None:
            raise OSError("disk dolu")

        with monkeypatch.context() as yama:
            yama.setattr(app_password, "write_account_wrap", kesinti)
            with pytest.raises(OSError):
                hesaplar.reset_password(
                    by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password="Baska-Gecici-9"
                )

        satir = Account.objects.get(pk=hesap.id)
        assert satir.status == AccountStatus.PAROLA_YENILENMELI and satir.seal_matches(TEST_DEK)
        app_password.lock()
        with pytest.raises(app_password.WrongPassword):  # geçici parolanın sarmalı yazılmadı
            app_password.unlock(hesap_id=hesap.id, password="Baska-Gecici-9")
        with pytest.raises(app_password.PasswordRenewalRequired):
            app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)

    def test_kilit_acilisindaki_yenilemede_once_satir_ve_iz_sonra_sarmal(
        self, yonetici_hesabi: Account, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Satır yazımı kesilirse parola DEĞİŞMEZ: sarmal işlemin sonunda, satır ve `PAROLA`
        satırından sonra yazılır (`app_password._start_session`); geçici parola açmayı ve
        yenilemeyi istemeyi sürdürür, yeni parola açmaz."""
        hesap = hesap_ac()
        app_password.lock()
        gercek_kayit = Account.save

        def kesinti(satir: Account, *args: Any, **kwargs: Any) -> None:
            if "password_changed_at" in (kwargs.get("update_fields") or ()):
                raise OSError("disk dolu")
            gercek_kayit(satir, *args, **kwargs)

        with monkeypatch.context() as yama:
            yama.setattr(Account, "save", kesinti)
            with pytest.raises(OSError):
                app_password.unlock(
                    hesap_id=hesap.id, password=GECICI_PAROLA, new_password=YENI_PAROLA
                )

        assert crypto.is_unlocked() is False
        assert Account.objects.get(pk=hesap.id).status == AccountStatus.PAROLA_YENILENMELI
        with pytest.raises(app_password.WrongPassword):  # sarmal yazılmadı
            app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)
        with pytest.raises(app_password.PasswordRenewalRequired):
            app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA)
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA, new_password=UCUNCU_PAROLA)
        assert Account.objects.get(pk=hesap.id).status == AccountStatus.ACIK

    def test_kilit_acilisindaki_yenilemede_sarmal_ile_commit_arasi_kesinti(
        self, yonetici_hesabi: Account, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Süreç sarmal yazımıyla işlemin sonu arasında ölürse (taklit: sarmal yazıldıktan
        hemen sonra işlem düşer) yeni parola geçerlidir, satır `PAROLA_YENILENMELI` kalır ve
        bir sonraki girişte yenileme yeniden istenir; geçici parola artık açmaz."""
        hesap = hesap_ac()
        app_password.lock()
        gercek = app_password._replace_wrap

        def yazip_dus(*args: Any, **kwargs: Any) -> None:
            gercek(*args, **kwargs)
            raise OSError("süreç öldü")

        with monkeypatch.context() as yama:
            yama.setattr(app_password, "_replace_wrap", yazip_dus)
            with pytest.raises(OSError):
                app_password.unlock(
                    hesap_id=hesap.id, password=GECICI_PAROLA, new_password=YENI_PAROLA
                )

        assert Account.objects.get(pk=hesap.id).status == AccountStatus.PAROLA_YENILENMELI
        with pytest.raises(app_password.WrongPassword):  # sarmal yeni parolayla yazılmıştı
            app_password.unlock(
                hesap_id=hesap.id, password=GECICI_PAROLA, new_password=UCUNCU_PAROLA
            )
        with pytest.raises(app_password.PasswordRenewalRequired):
            app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)
        app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA, new_password=UCUNCU_PAROLA)
        assert Account.objects.get(pk=hesap.id).status == AccountStatus.ACIK

    def test_askida_durumdaki_hesap_once_askidan_cikar(self, yonetici_hesabi: Account) -> None:
        hesap = hesap_ac()
        ilk_giris(hesap)
        muhurle(
            Account.objects.get(pk=hesap.id),
            status=AccountStatus.ASKIDA,
            suspend_reason="GOREV_BOLUMU",
        )
        with pytest.raises(hesaplar.AccountServiceError, match="askıdan çıkarın"):
            hesaplar.reset_password(
                by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
            )

        donen = hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)

        assert donen.status == AccountStatus.ACIK and donen.suspend_reason == ""
        assert donen.seal_matches(TEST_DEK)

    def test_askidan_cikan_gecici_parolali_hesap_yenileme_ister(
        self, yonetici_hesabi: Account
    ) -> None:
        hesap = hesap_ac()
        muhurle(hesap, status=AccountStatus.ASKIDA, suspend_reason="UYELIK_DUSTU")
        donen = hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
        assert donen.status == AccountStatus.PAROLA_YENILENMELI

    def test_hatali_deneme_askisi_kaldirilir(self, yonetici_hesabi: Account) -> None:
        hesap = hesap_ac()
        veri = durum()
        for kayit in veri["hesaplar"]:
            if kayit["id"] == str(hesap.id):
                kayit.update(hatali=10, askida=True)
        durum_yaz(veri)

        hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)

        assert sarmal(hesap.id)["askida"] is False and sarmal(hesap.id)["hatali"] == 0
        assert app_password.wrap_is_suspended(hesap.id) is False


# ---------------------------------------------------------------------------
# DB kısıtları (servisi atlayan yazım da kesilir)
# ---------------------------------------------------------------------------
class TestKisitlar:
    def _satir(self, **alanlar: object) -> Account:
        hesap = Account(
            login_name=str(alanlar.pop("login_name", "deneme")),
            role=str(alanlar.pop("role", AccountRole.MUHASIP)),
            display_name="Örnek Kişi",
            **alanlar,
        )
        hesap.save(force_insert=True)
        return hesap

    def test_acik_hesaplarda_tanitici_db_de_tekil(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(IntegrityError), transaction.atomic():
            self._satir(login_name="yonetici", role=AccountRole.SEKRETER)
        self._satir(
            login_name="yonetici",
            role=AccountRole.SEKRETER,
            status=AccountStatus.KAPALI,
            closed_at=timezone.now(),
        )  # kapalı hesap tanıtıcıyı tutmaz

    def test_tek_hesapli_rol_db_de_tekil(self, yonetici_hesabi: Account) -> None:
        self._satir(login_name="muhasip-1")
        with pytest.raises(IntegrityError), transaction.atomic():
            self._satir(login_name="muhasip-2")

    def test_kapali_durum_kapanis_ani_ister(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(IntegrityError), transaction.atomic():
            self._satir(status=AccountStatus.KAPALI)

    def test_aski_nedeni_yalniz_askida(self, yonetici_hesabi: Account) -> None:
        with pytest.raises(IntegrityError), transaction.atomic():
            self._satir(suspend_reason="UYELIK_DUSTU")


# ---------------------------------------------------------------------------
# Tanıtıcı kuralları ve uyarısı
# ---------------------------------------------------------------------------
class TestTaniticiKurallari:
    @pytest.mark.parametrize(
        ("tanitici", "ad", "uyari_var"),
        [
            ("muhasip", "Ayşe Kaya", False),
            ("ayse.k", "Ayşe Kaya", True),
            ("ayse-1", "Ayşe Kaya", True),  # dört harfli sözcük sınırın içinde
            ("sukru-2", "Şükrü Öztürk", True),  # Türkçe harf katlanır
            ("ali-1", "Ali Can", False),  # üç harfli sözcük aranmaz ("ali" tanıtıcıda var)
            ("can.k", "Ali Can", False),  # "can" da üç harfli
            ("ozturk", "Şükrü Öztürk", True),
        ],
    )
    def test_ad_iceren_tanitici_uyarilir_engellenmez(
        self, tanitici: str, ad: str, uyari_var: bool
    ) -> None:
        uyari = hesap_kurallari.login_name_warning(tanitici, ad)
        assert (uyari is not None) is uyari_var

    def test_tanitici_kucuk_harfe_cevrilir(self) -> None:
        assert hesap_kurallari.validate_login_name("  MUHASİP ") == "muhasip"
        assert hesap_kurallari.validate_login_name("Iğdır") == "ığdır"

    @pytest.mark.parametrize("deger", ["", "a", "1abc", "iki sözcük", "x" * 33, "tire/yok"])
    def test_gecersiz_tanitici(self, deger: str) -> None:
        with pytest.raises(hesap_kurallari.AccountRuleError):
            hesap_kurallari.validate_login_name(deger)

    def test_varsayilan_tanitici_rolden_turer(self) -> None:
        assert hesap_kurallari.default_login_name("muhasip", []) == "muhasip"
        assert hesap_kurallari.default_login_name("muhasip", ["muhasip"]) == "muhasip-2"
        assert hesap_kurallari.default_login_name("denetleme_kurulu", ["dk-1"]) == "dk-2"
        assert hesap_kurallari.default_login_name("baskan_yardimcisi", []) == "baskan-yardimcisi"

    def test_ad_soyad_bosluklari_toplanir(self) -> None:
        assert hesap_kurallari.validate_display_name("  Örnek   Kişi ") == "Örnek Kişi"
        with pytest.raises(hesap_kurallari.AccountRuleError):
            hesap_kurallari.validate_display_name("   ")


# ---------------------------------------------------------------------------
# Parola politikası (TK15; plan F1b-1)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("parola", "parca"),
    [
        ("Kisa-1a", "en az 8"),
        ("A1-" + "a" * 126, "en çok 128"),
        (" Bosluklu-1", "başında ya da sonunda"),
        ("Bosluklu-1 ", "başında ya da sonunda"),
        ("kucukharf-1", "eksik: büyük harf."),
        ("BUYUKHARF-1", "eksik: küçük harf."),
        ("Rakamsiz-Parola", "eksik: rakam."),
        ("Simgesiz1Parola", "eksik: simge."),
        ("Bosluk Simge 1a", "eksik: simge."),  # ara boşluk serbest ama simge sayılmaz
    ],
)
def test_parola_politikasi_reddeder(parola: str, parca: str) -> None:
    with pytest.raises(hesap_kurallari.AccountRuleError, match=parca.replace(".", r"\.")):
        hesap_kurallari.validate_password(parola)


@pytest.mark.parametrize(
    "parola",
    ["Örnek-Parola-1", "çğış-ÇĞİŞ-2", "Okul aile 2026!", "A1-" + "a" * 125, "Iı1!İi2?"],
)
def test_parola_politikasi_turkce_harfleri_harf_sayar(parola: str) -> None:
    assert hesap_kurallari.validate_password(parola) == parola  # kırpılmaz, değişmez


#: ORTAK VAKA TABLOSU — ön yüzün `oturum/parolaPolitikasi.test.ts` dosyasında AYNI
#: satırlar vardır (ön denetim backend'den katı ya da gevşek olmasın). Kenar
#: karakterler: rakam yalnız onluk rakamdır (`²`, `①` değil; `٣` evet), küçük ve büyük
#: harf Unicode "Lowercase"/"Uppercase" özelliğidir (`ª` küçük, `Ⅷ` büyük), boşluk
#: Python `isspace`tir (U+00A0 ve U+001F boşluk; U+FEFF boşluk değil, simge sayılır).
_EKSIK_RAKAM = "Parola küçük harf, büyük harf, rakam ve simge içermelidir; eksik: rakam."
ORTAK_PAROLA_VAKALARI: list[tuple[str, str | None]] = [
    ("Okul-Aile\u00b2", _EKSIK_RAKAM),
    ("Okul-Aile\u2460", _EKSIK_RAKAM),
    ("Okul-Aile\u0663", None),
    ("OKUL-AILE1\u00aa", None),
    ("okul-aile1\u2167", None),
    ("\u00a0Okul-Aile1", hesap_kurallari.PASSWORD_EDGE_SPACE_MESSAGE),
    ("Okul-Aile1\u001f", hesap_kurallari.PASSWORD_EDGE_SPACE_MESSAGE),
    ("\ufeffOkulAile1", None),
]


@pytest.mark.parametrize(("parola", "ileti"), ORTAK_PAROLA_VAKALARI)
def test_parola_politikasi_ortak_vaka_tablosu(parola: str, ileti: str | None) -> None:
    if ileti is None:
        assert hesap_kurallari.validate_password(parola) == parola
        return
    with pytest.raises(hesap_kurallari.AccountRuleError) as hata:
        hesap_kurallari.validate_password(parola)
    assert str(hata.value) == ileti


# ---------------------------------------------------------------------------
# Hesap mührü (tasarım §4.6.1, §4.3 tehdit 19) — F1 kapısı
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "degisiklik",
    [
        {"role": "denetleme_kurulu"},
        {"status": "ACIK"},
        {"login_name": "baska-ad"},
    ],
    ids=["rol", "durum", "tanitici"],
)
def test_hesap_muhru_bozulunca_giris_reddedilir_satir_degismez(
    yonetici_hesabi: Account, degisiklik: dict[str, str]
) -> None:
    """Program dışından rolü, durumu ya da tanıtıcısı değişen satırla giriş açılmaz; satıra
    dokunulmaz (yeniden mühürlemek değişikliği meşrulaştırırdı)."""
    hesap = hesap_ac()  # PAROLA_YENILENMELI; "durum" hâli onu ACIK'a çevirir
    ham_guncelle(hesap.id, **degisiklik)
    once = ham_satir(hesap.id)
    app_password.lock()

    with pytest.raises(app_password.AccountSealMismatch) as hata:
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)

    assert hata.value.code == "hesap_muhru_tutmadi"
    assert crypto.is_unlocked() is False
    assert ham_satir(hesap.id) == once  # mühür, durum, son giriş aynen
    assert sarmal(hesap.id)["hatali"] == 0  # doğru parola: sayaç artmaz
    # Program yöneticisi girer; hesap işlemleri de o satıra dokunmaz.
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    with pytest.raises(app_password.AccountSealMismatch):
        hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
        )
    assert ham_satir(hesap.id) == once


def test_muhur_kanonik_alanlari_kapsar_son_girisi_kapsamaz(yonetici_hesabi: Account) -> None:
    """`last_login_at` mührün dışındadır (§4.6.1): kilit açılışı yeniden mühürlemez."""
    muhur = yonetici_hesabi.seal
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    tazelenmis = Account.objects.get(pk=TEST_HESAP_ID)
    assert tazelenmis.last_login_at is not None and tazelenmis.seal == muhur
    assert tazelenmis.seal_matches(TEST_DEK)
    # Başka bir DEK'le mühür tutmaz.
    assert not tazelenmis.seal_matches(b"\x01" * 32)


# ---------------------------------------------------------------------------
# İki depo kuralı (tasarım §4.6.1) — F1 kapısı
# ---------------------------------------------------------------------------
def _hal_giris(yonetici: Account) -> None:
    """Kural 1: sarmal açılır VE satır var, açık, mühürlü — biri eksikse giriş yok."""
    hesap = hesap_ac()
    ilk_giris(hesap)
    # (a) Satırı olmayan sarmal: parola doğru ama satır yok.
    hayalet = str(uuid.uuid4())
    app_password.write_account_wrap(
        data_key=TEST_DEK, hesap_id=hayalet, tanitici="hayalet", password=YENI_PAROLA
    )
    app_password.lock()
    with pytest.raises(app_password.TwoStoreMismatch):
        app_password.unlock(hesap_id=hayalet, password=YENI_PAROLA)
    # (b) Sarmalı olmayan satır: satır açık ve mühürlü ama sarmal yok.
    app_password.remove_account_wraps({str(hesap.id)})
    with pytest.raises(app_password.TwoStoreMismatch):
        app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)
    # (c) İkisi tutarlı: giriş açılır.
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert crypto.is_unlocked() is True


def _hal_acma_yarida(yonetici: Account, monkeypatch: pytest.MonkeyPatch) -> None:
    """Kural 2: önce satır, sonra sarmal; arada kesilirse satır sarmalsız kalır."""

    def kesinti(**_: object) -> None:
        raise OSError("disk dolu")

    with monkeypatch.context() as yama:
        yama.setattr(app_password, "write_account_wrap", kesinti)
        with pytest.raises(OSError):
            hesap_ac()
    hesap = Account.objects.get(role=AccountRole.MUHASIP)
    assert hesap.status == AccountStatus.PAROLA_YENILENMELI and hesap.seal_matches(TEST_DEK)
    assert str(hesap.id) not in sarmal_kimlikleri()
    app_password.lock()
    with pytest.raises(app_password.TwoStoreMismatch):  # giriş zaten açılmaz
        app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)
    # Program yöneticisi yeniden geçici parola verir: sarmal kurulur, giriş açılır.
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id, temp_password=GECICI_PAROLA
    )
    app_password.lock()
    app_password.unlock(hesap_id=hesap.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)


def _hal_kapama_yarida(yonetici: Account, monkeypatch: pytest.MonkeyPatch) -> None:
    """Kural 3: önce satır KAPALI, sonra sarmallar; dosya adımı kesilirse kilit açılışı siler.

    İki kesinti noktası: (a) dosya adımı hiç başlamadan (sarmal ana dosyada da durur);
    (b) ana dosya yazıldı, arşiv adımı düştü (ör. virüs tarayıcısı arşivi tutuyor):
    sarmal YALNIZ arşivlerde, yapısal yazımın az önce aldığı kopyada da kalır. Temizlik
    adayları ana dosyayla birlikte arşivlerden de toplar.
    """
    muhasip = hesap_ac()
    sekreter = hesap_ac(AccountRole.SEKRETER, ad="Örnek Sekreter")
    arsiv_yaz("2026-10-01-120000", durum())

    def kesinti(_: set[str]) -> None:
        raise OSError("dosya kilitli")

    with monkeypatch.context() as yama:  # (a)
        yama.setattr(app_password, "remove_account_wraps", kesinti)
        with pytest.raises(OSError):
            hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id)
    assert Account.objects.get(pk=muhasip.id).status == AccountStatus.KAPALI
    assert str(muhasip.id) in sarmal_kimlikleri()

    once = len(arsivler())
    with monkeypatch.context() as yama:  # (b)
        yama.setattr(app_password, "_remove_wraps_from_archives", kesinti)
        with pytest.raises(OSError):
            hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=sekreter.id)
    assert Account.objects.get(pk=sekreter.id).status == AccountStatus.KAPALI
    assert str(sekreter.id) not in sarmal_kimlikleri()
    assert len(arsivler()) == once + 1
    # Sarmal yalnız arşivlerde: elle yazılan arşivde ve kapamanın az önce aldığı kopyada.
    assert sum(str(sekreter.id) in arsivdeki_kimlikler(a) for a in arsivler()) == 2

    app_password.lock()
    with pytest.raises(app_password.TwoStoreMismatch):  # kapalı hesap girmez
        app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)

    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)  # temizlik koşar

    assert str(muhasip.id) not in sarmal_kimlikleri()
    arsivlerde_yok(muhasip.id, sekreter.id)


def _hal_geri_yukleme_sonrasi(yonetici: Account, monkeypatch: pytest.MonkeyPatch) -> None:
    """Kural 4: fark listelenir; sarmalsız açık hesap parola yenilemeye çekilir; satırsız ve
    kapalı sarmallar YALNIZ onayla silinir."""
    sarmalsiz = hesap_ac(AccountRole.SEKRETER, ad="Örnek Sekreter")
    ilk_giris(sarmalsiz)
    kapali = hesap_ac(AccountRole.MUHASIP)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=kapali.id)
    # Geri yüklenen veritabanıyla eski `guvenlik.json` arasında fark: sekreterin sarmalı
    # yok; kapanmış muhasibin ve veritabanında hiç olmayan bir hesabın sarmalı var.
    hayalet = str(uuid.uuid4())
    app_password.remove_account_wraps({str(sarmalsiz.id)})
    for hesap_id, tanitici in ((str(kapali.id), "muhasip"), (hayalet, "hayalet")):
        app_password.write_account_wrap(
            data_key=TEST_DEK, hesap_id=hesap_id, tanitici=tanitici, password=YENI_PAROLA
        )
    arsiv = arsiv_yaz("2026-10-01-120000", durum())

    fark = hesaplar.reconcile_two_stores()

    assert fark.rows_without_wrap == [str(sarmalsiz.id)]
    assert fark.wraps_without_row == [hayalet]
    assert fark.wraps_of_closed == [str(kapali.id)]
    assert fark.seal_mismatch == [] and not fark.empty
    yenilenen = Account.objects.get(pk=sarmalsiz.id)
    assert yenilenen.status == AccountStatus.PAROLA_YENILENMELI
    assert yenilenen.seal_matches(TEST_DEK)
    assert {hayalet, str(kapali.id)} <= set(sarmal_kimlikleri())  # onaysız silinmez

    with pytest.raises(hesaplar.AccountServiceError, match="silinebilecek durumda değil"):
        hesaplar.remove_orphan_wraps(by_hesap_id=TEST_HESAP_ID, hesap_idler=[TEST_HESAP_ID])
    silinen = hesaplar.remove_orphan_wraps(
        by_hesap_id=TEST_HESAP_ID, hesap_idler=fark.removable_wraps
    )

    assert silinen == sorted([hayalet, str(kapali.id)])
    assert sarmal_kimlikleri() == [TEST_HESAP_ID]
    assert arsivdeki_kimlikler(arsiv) == [TEST_HESAP_ID]
    arsivlerde_yok(hayalet, kapali.id)  # silmenin kendi aldığı kopya dahil
    assert hesaplar.two_store_differences().rows_without_wrap == [str(sarmalsiz.id)]


_IKI_DEPO_HALLERI: dict[str, Callable[..., None]] = {
    "giris": lambda yonetici, _: _hal_giris(yonetici),
    "acma_yarida": _hal_acma_yarida,
    "kapama_yarida": _hal_kapama_yarida,
    "geri_yukleme_sonrasi": _hal_geri_yukleme_sonrasi,
}


@pytest.mark.parametrize("hal", list(_IKI_DEPO_HALLERI))
def test_iki_depo_dort_hali(
    yonetici_hesabi: Account, monkeypatch: pytest.MonkeyPatch, hal: str
) -> None:
    _IKI_DEPO_HALLERI[hal](yonetici_hesabi, monkeypatch)


def test_kapali_temizligi_muhru_tutmayan_satirin_sarmalina_dokunmaz(
    yonetici_hesabi: Account,
) -> None:
    """Durumu program dışından KAPALI'ya çevrilen satır meşru bir sarmalı sildiremez."""
    hesap = hesap_ac()
    ham_guncelle(hesap.id, status="KAPALI", closed_at=timezone.now().isoformat(sep=" "))
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert str(hesap.id) in sarmal_kimlikleri()
    fark = hesaplar.two_store_differences()
    assert fark.seal_mismatch == [str(hesap.id)]
    with pytest.raises(hesaplar.AccountServiceError):
        hesaplar.remove_orphan_wraps(by_hesap_id=TEST_HESAP_ID, hesap_idler=[str(hesap.id)])


def test_bos_fark_listesi(yonetici_hesabi: Account) -> None:
    assert hesaplar.reconcile_two_stores().empty
    assert hesaplar.remove_orphan_wraps(by_hesap_id=TEST_HESAP_ID, hesap_idler=[]) == []


# ---------------------------------------------------------------------------
# Model ve kayıt defteri
# ---------------------------------------------------------------------------
def test_hesap_temsili_kisi_adi_tasimaz(yonetici_hesabi: Account) -> None:
    assert str(yonetici_hesabi) == (
        "yonetici (Program yöneticisi (OAB'den sorumlu müdür yardımcısı))"
    )
    assert "Örnek" not in str(yonetici_hesabi)


def test_korunan_alan_listesi_hesap_adini_icerir_iz_anahtarini_icermez() -> None:
    etiketler = app_password.protected_field_labels()
    assert "hesap sahibinin adı-soyadı" in etiketler
    assert "iz anahtarı" not in etiketler


def test_rol_kodlari_tasarimdaki_kumedir() -> None:
    """Tasarım §2.3.1: üç bölümün ortak adları."""
    assert AccountRole.values == [
        "yonetici",
        "baskan",
        "baskan_yardimcisi",
        "muhasip",
        "sekreter",
        "denetleme_kurulu",
        "mudur",
    ]


def test_kilit_ekraninda_sarmal_askisi_okunur() -> None:
    assert app_password.wrap_is_suspended(TEST_HESAP_ID) is False
    assert app_password.wrap_is_suspended(uuid.uuid4()) is False
