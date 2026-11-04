"""Parola kaydının (sarmalın) tazeliği — kullanıcı kararı 03.11.2026 "Tazelik kapatılır".

Hesabın mühürlü `Account` satırı `guvenlik.json`'daki GÜNCEL sarmalın DEK'li özetini taşır
(`wrap_digest`; iki aşamalı yazımın ara hâli `wrap_digest_pending`) ve iki alan hesap mührüne
girer (`app_password` modül başlığı "SARMALIN TAZELİĞİ", "İKİ AŞAMALI ÖZET"). Bu dosya:

* oturumdaki parola doğrulamasının kolunu (parola doğrulama, parola değiştirme, kurtarma
  anahtarının yenilenmesi): oturum açıkken dosyaya eski sarmal konursa eski parola geçmez;
* özeti boş ve özeti program dışından eski değere çevrilmiş satırı (fail-closed; mühür);
* iki depo farkının `digest_mismatch` listesini ve parola sıfırlamasıyla çıkışı;
* KESİNTİYİ: her yazıcı (kilit açılışında yenileme, parola değiştirme, kurtarma anahtarıyla
  açılış, parola sıfırlama) × her adım (dosya yazılamadı; dosya yazıldı, ikinci işlem commit
  olmadı) — hesap `guvenlik.json`'da o an duran sarmalın parolasıyla açılır; başarılı bitişten
  sonra eski sarmal açılmaz; bekleyen özet penceresi (kalan risk) ve ilk açılışın düzeltmesi;
* GERİ YÜKLEME ONARIMINI (`ozet_onarimi`; ORM'in yazdığı gerçek veritabanı dosyalarıyla):
  (i) yedekten sonra parolası değişen muhasip, (ii) geri yüklemeden önce `guvenlik.json`'a
  konan eski sarmal, (iii) yedekten sonra parolasını değiştiren program yöneticisi, (iv) güncel
  veritabanı yokken parola yolu reddi ve kurtarma anahtarı yolu, (v) kurtarma anahtarıyla geri
  yükleme (güncel `guvenlik.json` ile ve başlıktan);
* BAĞIMSIZ DENETİMİN BULGULARINI (dosyanın sonu): çapa ikamesi (bayat çapa özet vermez), çift
  geri yükleme (çapada olmayan hesabın özeti boşalır), kapanan hesap (çapada `KAPALI` → boşalır),
  mührü bozuk çapa satırı (taşınmaz; K-a: dosyadakini tutmayan özetler boşaltılır, geri
  yüklemeden önce konan yedek günü sarmalı kalan risk olarak sabitlenir), taşıma dalı, onarım yazılamazsa
  geri yükleme, kilitte özet/durum sırası, korunan asıl özetin meşruluğu (`_kept_digest`) ve
  zehirli arşiv / kapalı hesap temizliğinin hatası (sarmal yazımından sonra düşen adım yok).

Kilit açılışının kolu (eski sarmal eski parolayla açılmaz) `test_sarmal_kimligi.py`'de, geri
yükleme yetkisinin kolu (konsol, masaüstü kipi, uygulama içi) `test_geri_yukleme_yetkisi.py`'de.
Adlar, parolalar ve kimlikler uydurmadır.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul.models import Account, AccountRole, AccountStatus, AuditAction, AuditTrail
from apps.okul.oturum import OTURUM, Yazar, yazar_olarak
from apps.okul.services import (
    app_password,
    backup_restore,
    geri_yukleme_notu,
    geri_yukleme_yetkisi,
    hesaplar,
    ozet_onarimi,
)
from apps.okul.tests.geri_yukleme_ortak import geri_yukle as _geri_yukle
from apps.okul.tests.geri_yukleme_ortak import goruntu as _goruntu
from apps.okul.tests.geri_yukleme_ortak import hesap_satiri_oku as _hesap_satiri
from apps.okul.tests.geri_yukleme_ortak import programa_al as _programa_al
from apps.okul.tests.geri_yukleme_ortak import sifreli_yedek as _kapsayici
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
    hesap_ac,
    muhurle,
)
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_KURTARMA_ANAHTARI, TEST_PAROLA
from shared import crypto

pytestmark = pytest.mark.django_db

#: Kesintiden sonra açılış tamamlanırken verilen (uydurma) parola.
_SONRAKI_PAROLA = "Kesinti-Sonrasi-7!"


def _muhasip() -> Account:
    """Açık (`ACIK`) uydurma muhasip; parolası `GECICI_PAROLA`, sarmalı ve özeti programın."""
    return muhurle(hesap_ac(), status=AccountStatus.ACIK, password_changed_at=timezone.now())


def _sarmal(hesap_id: object) -> dict[str, Any]:
    sarmal = app_password._find_wrap(durum(), hesap_id)
    assert sarmal is not None
    return dict(sarmal)


def _geri_koy(eski: dict[str, Any]) -> None:
    """Metin düzenleyici taklidi (kod gerekmez): aynı kimliğin sarmalını verilenle değiştirir."""
    veri = durum()
    veri["hesaplar"] = [dict(eski) if h["id"] == eski["id"] else h for h in veri["hesaplar"]]
    durum_yaz(veri)


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


def _son_seq() -> int:
    return int(AuditTrail.objects.order_by("-seq").values_list("seq", flat=True).first() or 0)


def _ham(hesap_id: object) -> dict[str, Any]:
    """Satırın değişmemesi gereken sütunları (ORM'siz)."""
    sutunlar = (
        "status",
        "seal",
        "wrap_digest",
        "wrap_digest_pending",
        "reset_notice_pending",
        "last_login_at",
        "password_changed_at",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT {', '.join(sutunlar)} FROM okul_account WHERE id = %s",  # noqa: S608
            [str(hesap_id).replace("-", "")],
        )
        satir = cursor.fetchone()
    assert satir is not None
    return dict(zip(sutunlar, satir, strict=True))


def _butunluk_satiri(hesap_id: object) -> None:
    satir = AuditTrail.objects.order_by("-seq").first()
    assert satir is not None
    assert (satir.action, satir.model, satir.object_id) == (
        AuditAction.BUTUNLUK,
        "okul.Account",
        str(hesap_id),
    )
    assert satir.changed_fields == ["wrap_digest"]
    assert satir.actor == "SISTEM"


def _acilir(hesap_id: object, parola: str) -> Account:
    """Hesap bu parolayla açılır: sarmal, mühür ve özet denetimi geçer. Yenileme istenirse (satır
    `PAROLA_YENILENMELI`) yeni parolayla tamamlanır — meşru kullanıcı kilitlenmemiştir."""
    try:
        return app_password.unlock(hesap_id=hesap_id, password=parola)
    except app_password.PasswordRenewalRequired:
        return app_password.unlock(hesap_id=hesap_id, password=parola, new_password=_SONRAKI_PAROLA)


def _acilmaz(hesap_id: object, parola: str) -> None:
    """Eski sarmal: parola onu açar ama özet tutmaz — oturum açılmaz, `BUTUNLUK` satırı düşer."""
    with pytest.raises(app_password.WrapDigestMismatch) as hata:
        app_password.unlock(hesap_id=hesap_id, password=parola, new_password=_SONRAKI_PAROLA)
    assert (hata.value.code, hata.value.status_code) == ("hesap_muhru_tutmadi", 409)
    assert str(hata.value) == app_password.WRAP_DIGEST_MISMATCH_MESSAGE
    assert OTURUM.hesap_id() is None and crypto.is_unlocked() is False
    _butunluk_satiri(hesap_id)


# ============================================================ oturumdaki parola doğrulaması


@pytest.mark.parametrize("islem", ["dogrulama", "degistirme", "kurtarma_yenileme"])
def test_oturumda_eski_sarmal_geri_konunca_eski_parola_gecmez(islem: str) -> None:
    """Program yöneticisi parolasını değiştirir; oturum açıkken arşivdeki eski sarmal
    `guvenlik.json`'a geri konur. Eski parola o sarmalı açar ve DEK bellektekiyle aynıdır, ama
    özet tutmaz: parola doğrulaması, parola değiştirme ve kurtarma anahtarının yenilenmesi
    reddedilir (`WrapDigestMismatch`), `BUTUNLUK` satırı düşer, satır, kurtarma bölümü ve sayaç
    değişmez, oturum sürer."""
    app_password.change_password(
        hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
    )
    _geri_koy(_arsivdeki_sarmal(TEST_HESAP_ID, TEST_PAROLA))
    once = _ham(TEST_HESAP_ID)
    kurtarma = durum()["kurtarma"]
    son = _son_seq()

    with pytest.raises(app_password.WrapDigestMismatch):
        if islem == "dogrulama":
            app_password.verify_password(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
        elif islem == "degistirme":
            app_password.change_password(
                hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=UCUNCU_PAROLA
            )
        else:
            app_password.renew_recovery_key(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    assert _ham(TEST_HESAP_ID) == once
    assert durum()["kurtarma"] == kurtarma
    assert app_password.wrap_failure_state(TEST_HESAP_ID) == (0, False)
    assert list(AuditTrail.objects.filter(seq__gt=son).values_list("action", flat=True)) == [
        AuditAction.BUTUNLUK
    ]
    _butunluk_satiri(TEST_HESAP_ID)
    assert OTURUM.hesap_id() == TEST_HESAP_ID  # oturum sürer
    # Yanlış parola hâlâ yanlış parola sayılır (özet denetimi parolanın yerini tutmaz).
    with pytest.raises(app_password.WrongPassword):
        app_password.verify_password(hesap_id=TEST_HESAP_ID, password="Yanlis-Parola-1")


# ============================================================ özeti boş ve özeti değiştirilmiş satır


def test_ozeti_bos_satir_parolayla_acilmaz_sifirlamayla_cikar() -> None:
    """Özeti boş satır fail-closed'dır: doğru parola, sağlam mühür ama özet yok → giriş açılmaz.
    Satır iki depo farkının `digest_mismatch` listesinde görünür; program yöneticisinin parola
    sıfırlaması özeti yeniden yazar, liste boşalır, muhasip geçici parolasıyla açar."""
    muhasip = muhurle(_muhasip(), wrap_digest="", wrap_digest_pending="")
    assert muhasip.seal_matches(TEST_DEK)
    fark = hesaplar.two_store_differences()
    assert fark.digest_mismatch == [str(muhasip.id)] and not fark.empty
    yanit = APIClient().get("/api/v1/security/integrity/two-store/")
    assert yanit.status_code == 200
    kart = yanit.json()["iki_depo"]
    assert kart["fark_var"] is True
    assert [h["id"] for h in kart["ozeti_tutmayan_hesaplar"]] == [str(muhasip.id)]
    app_password.lock()
    _acilmaz(muhasip.id, GECICI_PAROLA)

    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    assert hesaplar.two_store_differences().digest_mismatch == []
    app_password.lock()
    assert _acilir(muhasip.id, UCUNCU_PAROLA).id == muhasip.id


def test_ozet_program_disindan_eski_degere_cevrilirse_muhur_tutmaz() -> None:
    """Özet mühre girer: satırdaki özeti eski sarmalınkine (ham SQL, mühür yenilenmeden) çevirip
    eski sarmalı geri koyan biri açamaz — mühür tutmaz (`AccountSealMismatch`). Özet mühürde
    olmasaydı özet tek başına eski değerle değiştirilebilirdi."""
    muhasip = _muhasip()
    eski_ozet = muhasip.wrap_digest
    app_password.lock()
    app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA)
    with yazar_olarak(Yazar(hesap_id=str(muhasip.id), rol=AccountRole.MUHASIP)):
        app_password.change_password(
            hesap_id=muhasip.id, current_password=GECICI_PAROLA, new_password=YENI_PAROLA
        )
    app_password.lock()
    _geri_koy(_arsivdeki_sarmal(muhasip.id, GECICI_PAROLA))
    ham_guncelle(muhasip.id, wrap_digest=eski_ozet)

    with pytest.raises(app_password.AccountSealMismatch) as hata:
        app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA)
    assert not isinstance(hata.value, app_password.WrapDigestMismatch)
    assert OTURUM.hesap_id() is None


def test_bagsiz_ve_eski_sarmal_ayni_iletiyi_verir() -> None:
    """Zarf kararı (kullanıcı kararı 03.11.2026): iki hâl tek iletidir; ileti Denetleme Kuruluna
    bildirimi ve çıkışı ("Parolamı unuttum" yolu, program yöneticisinin sıfırlaması) söyler."""
    assert app_password.WRAP_DIGEST_MISMATCH_MESSAGE == app_password.UNBOUND_WRAP_MESSAGE
    ileti = app_password.UNBOUND_WRAP_MESSAGE
    assert "Denetleme Kuruluna bildirin" in ileti
    assert "“Parolamı unuttum”" in ileti and "kurtarma anahtarıyla" in ileti
    assert "program yöneticisi sıfırlar" in ileti


# ============================================================ kesinti: her yazıcı × her adım


#: Yazıcılar: kilit açılışında yenileme, parola değiştirme, kurtarma anahtarıyla açılış, sıfırlama.
YAZICILAR = ("kilit_yenileme", "parola_degistirme", "kurtarma", "sifirlama")


def _yazici(ad: str) -> tuple[str, str, str, Callable[[], object]]:
    """(hesap kimliği, eski parola, yeni parola, yazımı başlatan işlev). Ortam kurulur: kilit
    açılışı ve kurtarma için program kilitli, parola değiştirme ve sıfırlama için oturum açık."""
    if ad == "kilit_yenileme":
        muhasip = hesap_ac()  # PAROLA_YENILENMELI, geçici parola
        app_password.lock()
        kimlik = str(muhasip.id)
        return (
            kimlik,
            GECICI_PAROLA,
            YENI_PAROLA,
            lambda: app_password.unlock(
                hesap_id=kimlik, password=GECICI_PAROLA, new_password=YENI_PAROLA
            ),
        )
    if ad == "parola_degistirme":
        return (
            TEST_HESAP_ID,
            TEST_PAROLA,
            YENI_PAROLA,
            lambda: app_password.change_password(
                hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
            ),
        )
    if ad == "kurtarma":
        app_password.lock()
        return (
            TEST_HESAP_ID,
            TEST_PAROLA,
            YENI_PAROLA,
            lambda: app_password.unlock_with_recovery(
                recovery_key=TEST_KURTARMA_ANAHTARI,
                hesap_id=TEST_HESAP_ID,
                new_password=YENI_PAROLA,
            ),
        )
    muhasip = _muhasip()
    kimlik = str(muhasip.id)
    return (
        kimlik,
        GECICI_PAROLA,
        UCUNCU_PAROLA,
        lambda: hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=UCUNCU_PAROLA
        ),
    )


@pytest.mark.parametrize("yazici", YAZICILAR)
def test_basarili_yazimdan_sonra_eski_sarmal_acilmaz(yazici: str) -> None:
    """Yazım başarıyla bitince satırda bekleyen özet kalmaz; arşivdeki eski sarmal (eski ya da
    geçici parolası bilinen) geri konunca açılmaz. Yeni sarmal açar."""
    hesap_id, eski, yeni, calistir = _yazici(yazici)
    calistir()
    satir = Account.objects.get(pk=hesap_id)
    assert satir.wrap_digest_pending == "" and satir.seal_matches(TEST_DEK)
    assert satir.wrap_digest == app_password.wrap_digest(TEST_DEK, _sarmal(hesap_id))
    app_password.lock()
    guncel = _sarmal(hesap_id)
    _geri_koy(_arsivdeki_sarmal(hesap_id, eski))
    _acilmaz(hesap_id, eski)
    _geri_koy(guncel)
    assert str(_acilir(hesap_id, yeni).id) == hesap_id


@pytest.mark.parametrize("yazici", YAZICILAR)
def test_dosya_yazilamazsa_eski_parola_acar_yeni_acmaz(
    yazici: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kesinti 1. adımdan (bekleyen özet commit edildi) sonra, dosya yazımında: dosyada eski sarmal
    durur ve asıl özet onundur — eski parola açar (meşru kullanıcı kilitlenmez); yeni sarmal
    dosyaya hiç girmedi."""
    hesap_id, eski, yeni, calistir = _yazici(yazici)

    def yazilamadi(_durum: dict[str, Any], _yeni: dict[str, Any]) -> None:
        raise OSError("disk dolu")

    with monkeypatch.context() as yama:
        yama.setattr(app_password, "_replace_wrap", yazilamadi)
        with pytest.raises(OSError) as hata:
            calistir()
    _dosya_hatasi(hata.value, "disk dolu", sifirlama=yazici == "sifirlama")

    satir = Account.objects.get(pk=hesap_id)
    assert satir.wrap_digest_pending != "" and satir.seal_matches(TEST_DEK)
    assert satir.wrap_digest == app_password.wrap_digest(TEST_DEK, _sarmal(hesap_id))
    app_password.lock()
    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=hesap_id, password=yeni)
    assert str(_acilir(hesap_id, eski).id) == hesap_id
    # İlk açılış bekleyen özeti temizledi (ya da açılıştaki yenileme kendi yazımını bitirdi).
    assert Account.objects.get(pk=hesap_id).wrap_digest_pending == ""


def _yazip_dusur(yazici: str, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str, str]:
    """Yazıcıyı dosya yazımıyla 2. adımın commit'i arasında düşürür (sarmal yazılır, işlem düşer)."""
    hesap_id, eski, yeni, calistir = _yazici(yazici)
    gercek = app_password._replace_wrap

    def yazip_dus(durum_: dict[str, Any], yeni_: dict[str, Any]) -> None:
        gercek(durum_, yeni_)
        raise OSError("süreç öldü")

    with monkeypatch.context() as yama:
        yama.setattr(app_password, "_replace_wrap", yazip_dus)
        with pytest.raises(OSError, match="süreç öldü"):
            calistir()
    satir = Account.objects.get(pk=hesap_id)
    assert satir.wrap_digest_pending == app_password.wrap_digest(TEST_DEK, _sarmal(hesap_id))
    assert satir.wrap_digest == app_password.wrap_digest(
        TEST_DEK, _arsivdeki_sarmal(hesap_id, eski)
    )
    app_password.lock()
    return hesap_id, eski, yeni


@pytest.mark.parametrize("yazici", YAZICILAR)
def test_dosya_yazilip_commit_olmazsa_yeni_parola_acar_ilk_acilis_duzeltir(
    yazici: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kesinti dosya yazımıyla 2. adımın commit'i arasında: dosyada yeni sarmal durur ve bekleyen
    özet onundur — yeni parola açar (meşru kullanıcı kilitlenmez). İlk açılış bekleyeni asıla
    çeker; ondan sonra arşivdeki eski sarmal açılmaz."""
    hesap_id, eski, yeni = _yazip_dusur(yazici, monkeypatch)
    assert str(_acilir(hesap_id, yeni).id) == hesap_id
    satir = Account.objects.get(pk=hesap_id)
    assert satir.wrap_digest_pending == "" and satir.seal_matches(TEST_DEK)
    app_password.lock()
    _geri_koy(_arsivdeki_sarmal(hesap_id, eski))
    _acilmaz(hesap_id, eski)


@pytest.mark.parametrize("yazici", YAZICILAR)
def test_bekleyen_ozet_penceresi_kalan_risktir(
    yazici: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """KALAN RİSK (bekleyen özet penceresi; `app_password` modül başlığı "KALAN RİSKLER" (a)):
    yalnız dosya yazımıyla 2. adımın commit'i arasında kesilen yazımdan sonra, ilk kilit açılışına
    dek asıl özet ESKİ sarmalınkidir. O pencerede arşivdeki eski sarmalı geri koyan biri eski
    parolayla açar; açılış "asılla tutan sarmal varken bekleyen temizlenir" kuralıyla eski sarmalı
    asıl bırakır, yeni sarmal artık açmaz (parola sıfırlaması çıkıştır). Kesintisiz yazımda pencere
    yoktur (`test_basarili_yazimdan_sonra_eski_sarmal_acilmaz`). Bu test riski sabitler: kapanırsa
    ret testine döner."""
    hesap_id, eski, yeni = _yazip_dusur(yazici, monkeypatch)
    yeni_sarmal = _sarmal(hesap_id)
    _geri_koy(_arsivdeki_sarmal(hesap_id, eski))
    assert str(_acilir(hesap_id, eski).id) == hesap_id
    satir = Account.objects.get(pk=hesap_id)
    assert satir.wrap_digest_pending == ""
    app_password.lock()
    if yazici in ("kilit_yenileme", "sifirlama"):
        # Açılış yenileme istedi ve yeni parolayla tamamlandı: dosyada artık o sarmal durur.
        return
    _geri_koy(yeni_sarmal)
    _acilmaz(hesap_id, yeni)


@pytest.mark.parametrize("yazici", YAZICILAR)
def test_bekleyen_ozet_yazilamazsa_hicbir_sey_degismez(
    yazici: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kesinti 1. adımda (bekleyen özetin işlemi düştü): dosya, sarmal ve satırın özetleri
    değişmez; eski parola açar."""
    hesap_id, eski, yeni, calistir = _yazici(yazici)
    once_satir = Account.objects.filter(pk=hesap_id).values(
        "wrap_digest", "wrap_digest_pending", "seal"
    )[0]
    once_sarmal = _sarmal(hesap_id)
    gercek = Account.save

    def kesinti(satir: Account, *args: Any, **kwargs: Any) -> None:
        alanlar = kwargs.get("update_fields") or ()
        if "wrap_digest_pending" in alanlar and satir.wrap_digest_pending:
            raise OSError("veritabanı kilitli")
        gercek(satir, *args, **kwargs)

    with monkeypatch.context() as yama:
        yama.setattr(Account, "save", kesinti)
        with pytest.raises(OSError, match="veritabanı kilitli"):
            calistir()

    assert (
        Account.objects.filter(pk=hesap_id).values("wrap_digest", "wrap_digest_pending", "seal")[0]
        == once_satir
    )
    assert _sarmal(hesap_id) == once_sarmal
    app_password.lock()
    assert str(_acilir(hesap_id, eski).id) == hesap_id
    del yeni


# ============================================================ geri yükleme onarımı


def _muhasip_parolasini_degistirir(muhasip: Account) -> None:
    app_password.lock()
    app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA)
    with yazar_olarak(Yazar(hesap_id=str(muhasip.id), rol=AccountRole.MUHASIP)):
        app_password.change_password(
            hesap_id=muhasip.id, current_password=GECICI_PAROLA, new_password=YENI_PAROLA
        )
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("sir", ["parola", "kurtarma"])
def test_onarim_yedekten_sonra_parolasi_degisen_hesap_yeni_parolasiyla_girer(
    sir: str, tmp_path: Path
) -> None:
    """(i) ve (v, güncel dosya): yedek alınır; muhasip parolasını değiştirir; program yöneticisi
    parolasıyla (ya da kurtarma anahtarıyla) geri yükler. Geri yüklenen satır yedek gününün
    özetini taşırdı: onarım onu güncel dosyadaki sarmala çeker (çapa tutuyor). Muhasip YENİ
    parolasıyla girer; eski sarmalı geri konunca açılmaz."""
    muhasip = _muhasip()
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    _muhasip_parolasini_degistirir(muhasip)
    guncel = _goruntu(tmp_path / "guncel.sqlite3")

    if sir == "parola":
        db = _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)
    else:
        db = _geri_yukle(tmp_path, yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)

    satir = _hesap_satiri(db, muhasip.id)
    ozet = app_password.wrap_digest(TEST_DEK, _sarmal(muhasip.id))
    assert satir[geri_yukleme_yetkisi.SIRA_OZET] == ozet
    assert satir[geri_yukleme_yetkisi.SIRA_BEKLEYEN] == ""
    assert geri_yukleme_yetkisi.muhurlu_satir_mi(satir, TEST_DEK)
    _programa_al(db)
    app_password.lock()
    assert _acilir(muhasip.id, YENI_PAROLA).id == muhasip.id
    app_password.lock()
    _geri_koy(_arsivdeki_sarmal(muhasip.id, GECICI_PAROLA))
    _acilmaz(muhasip.id, GECICI_PAROLA)


@pytest.mark.django_db(transaction=True)
def test_onarim_geri_yuklemeden_once_konan_eski_sarmali_aklamaz(tmp_path: Path) -> None:
    """(ii): yedek alınır (muhasibin sarmalı W1); muhasip parolasını değiştirir (W2); biri
    geri yüklemeden ÖNCE `guvenlik.json`'a W1'i koyar; program yöneticisi geri yükler. Çapa
    (önceki veritabanı) W2'nin özetini söyler: W1 aklanmaz, geri yüklenen satıra çapanın özeti
    geçer. Yedekteki satır W1'in özetini taşıdığı için onarımsız (ya da yalnız dosyaya bakan
    onarımla) W1 eski parolayla açılırdı."""
    muhasip = _muhasip()
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    _muhasip_parolasini_degistirir(muhasip)
    guncel = _goruntu(tmp_path / "guncel.sqlite3")
    cikista = Account.objects.get(pk=muhasip.id)
    _geri_koy(_arsivdeki_sarmal(muhasip.id, GECICI_PAROLA))

    db = _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)

    satir = _hesap_satiri(db, muhasip.id)
    assert satir[geri_yukleme_yetkisi.SIRA_OZET] == cikista.wrap_digest
    assert satir[geri_yukleme_yetkisi.SIRA_BEKLEYEN] == cikista.wrap_digest_pending == ""
    assert geri_yukleme_yetkisi.muhurlu_satir_mi(satir, TEST_DEK)
    _programa_al(db)
    app_password.lock()
    _acilmaz(muhasip.id, GECICI_PAROLA)


@pytest.mark.django_db(transaction=True)
def test_onarim_yedekten_sonra_parolasini_degistiren_yonetici_gunceliyle_geri_yukler(
    tmp_path: Path,
) -> None:
    """(iii): program yöneticisi yedekten sonra parolasını değiştirir; güncel parolasıyla geri
    yükler (güncel veritabanı okunur, özet tutar). Geri yüklenen satırı onarılır: güncel
    parolasıyla girer, eski sarmalı açılmaz."""
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    app_password.change_password(
        hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
    )
    guncel = _goruntu(tmp_path / "guncel.sqlite3")

    db = _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=YENI_PAROLA)

    satir = _hesap_satiri(db, TEST_HESAP_ID)
    assert satir[geri_yukleme_yetkisi.SIRA_OZET] == app_password.wrap_digest(
        TEST_DEK, _sarmal(TEST_HESAP_ID)
    )
    _programa_al(db)
    app_password.lock()
    assert str(_acilir(TEST_HESAP_ID, YENI_PAROLA).id) == TEST_HESAP_ID
    app_password.lock()
    _geri_koy(_arsivdeki_sarmal(TEST_HESAP_ID, TEST_PAROLA))
    _acilmaz(TEST_HESAP_ID, TEST_PAROLA)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("guncel_hali", ["yok", "bozuk"])
def test_dususte_yedekten_sonra_degisen_yonetici_parolasi_reddedilir_kurtarma_acik(
    guncel_hali: str, tmp_path: Path
) -> None:
    """(iv): güncel veritabanı yok ya da bozuk (görüntüye düşüş) ve program yöneticisi
    parolasını yedekten sonra değiştirmiş: görüntüdeki satır yedek gününün özetini taşır, parola
    yolu reddedilir (`RET_OZET`; ileti kurtarma anahtarı yolunu anar), hiçbir dosya değişmez.
    Kurtarma anahtarı yolu açıktır: geri yükler; çapa okunamadığı için K-a uygulanır — güncel
    `guvenlik.json`'daki sarmal (yeni parolanınki) yedek gününün özetini tutmadığı için İKİ ÖZET
    BOŞALTILIR (fail-closed) ve onarım `SISTEM` `HESAP` satırıyla izlenir; ne yeni parola ne
    arşivden geri konan yedek günü sarmalı açar, program yöneticisi kurtarma anahtarıyla açar.
    (b3'te yedekteki özet kalıyordu: arşivden geri konan yedek günü sarmalı açardı.)"""
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    yedekteki = Account.objects.get(pk=TEST_HESAP_ID).wrap_digest
    app_password.change_password(
        hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
    )
    guncel = None if guncel_hali == "yok" else b"SQLite format 3\x00 bozuk"
    guvenlik = app_password.state_path().read_bytes()

    with pytest.raises(backup_restore.GeriYuklemeYetkisiz) as ret:
        _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=YENI_PAROLA)
    assert ret.value.kod == geri_yukleme_yetkisi.RET_OZET
    assert str(ret.value) == geri_yukleme_yetkisi.ILETI_OZET
    assert "kurtarma anahtarıyla" in str(ret.value)
    db = tmp_path / "canli" / "db.sqlite3"
    assert (db.read_bytes() if db.exists() else None) == guncel
    assert app_password.state_path().read_bytes() == guvenlik

    db = _geri_yukle(tmp_path, yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)
    satir = _hesap_satiri(db, TEST_HESAP_ID)
    assert yedekteki != ""
    assert (satir[geri_yukleme_yetkisi.SIRA_OZET], satir[geri_yukleme_yetkisi.SIRA_BEKLEYEN]) == (
        "",
        "",
    )
    assert geri_yukleme_yetkisi.muhurlu_satir_mi(satir, TEST_DEK)
    _programa_al(db)
    app_password.lock()
    with pytest.raises(app_password.WrapDigestMismatch):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA)
    yeni_sarmal = _sarmal(TEST_HESAP_ID)
    _geri_koy(_arsivdeki_sarmal(TEST_HESAP_ID, TEST_PAROLA))
    with pytest.raises(app_password.WrapDigestMismatch):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    _geri_koy(yeni_sarmal)
    hesap = app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=UCUNCU_PAROLA
    )
    assert str(hesap.id) == TEST_HESAP_ID == OTURUM.hesap_id()


@pytest.mark.django_db(transaction=True)
def test_kurtarma_anahtariyla_baslikli_geri_yuklemede_capanin_ozetleri_gecer(
    tmp_path: Path,
) -> None:
    """(v, başlıktan): güvenlik dosyası kayıp; kurtarma anahtarıyla geri yükleme dosyayı yalnız
    kurtarma bölümüyle yazar (onarılacak sarmal yok). Çapa okunur: yedekten sonra parolası değişen
    muhasibin geri yüklenen satırına önceki veritabanının özeti geçer — yedek günündeki sarmal
    (arşivden geri konsa) açılmaz. Ardından program yöneticisi kurtarma anahtarıyla açar: iki depo
    karşılaştırması, sarmalı işlemin sonunda yazılacak hesabın (dosyada henüz sarmalı yok) özetini
    karşılaştırmaz (`sarmali_yazilacak`)."""
    muhasip = _muhasip()
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    _muhasip_parolasini_degistirir(muhasip)
    cikista = Account.objects.get(pk=muhasip.id)
    guncel = _goruntu(tmp_path / "guncel.sqlite3")
    w1 = _arsivdeki_sarmal(muhasip.id, GECICI_PAROLA)
    kapsayici = _kapsayici(yedek)
    app_password.lock()
    app_password.state_path().unlink()

    db = _geri_yukle(
        tmp_path, yedek, guncel, kapsayici=kapsayici, recovery_key=TEST_KURTARMA_ANAHTARI
    )

    assert durum()["hesaplar"] == []
    satir = _hesap_satiri(db, muhasip.id)
    assert satir[geri_yukleme_yetkisi.SIRA_OZET] == cikista.wrap_digest
    assert not geri_yukleme_yetkisi.ozet_tutuyor_mu(satir, app_password.wrap_digest(TEST_DEK, w1))
    assert geri_yukleme_yetkisi.muhurlu_satir_mi(satir, TEST_DEK)

    _programa_al(db)
    hesap = app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=UCUNCU_PAROLA
    )
    assert str(hesap.id) == TEST_HESAP_ID == OTURUM.hesap_id()
    fark = hesaplar.two_store_differences()
    assert fark.digest_mismatch == [] and fark.rows_without_wrap == [str(muhasip.id)]


@pytest.mark.django_db(transaction=True)
def test_onarim_muhru_tutmayan_satira_dokunmaz_ve_dosya_degismeden_kalir(tmp_path: Path) -> None:
    """Onarım yalnız iki tarafta da mührü tutan satırı yazar: geri yüklenecek satırın mührü
    program dışından bozulmuşsa ona dokunulmaz (yeniden mühürlemek değiştirilmiş satırı
    meşrulaştırırdı). Çapa (önceki veritabanı) salt okunur açılır, baytları değişmez."""
    muhasip = _muhasip()
    ham_guncelle(muhasip.id, role=AccountRole.YONETICI)  # mühür artık tutmaz
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    muhurle(
        Account.objects.get(pk=muhasip.id), role=AccountRole.MUHASIP
    )  # programın düzeltmesi taklidi
    _muhasip_parolasini_degistirir(muhasip)
    guncel = _goruntu(tmp_path / "guncel.sqlite3")
    once = _hesap_satiri(tmp_path / "yedek.sqlite3", muhasip.id)
    gecici = tmp_path / "onarilacak.sqlite3"
    gecici.write_bytes(yedek)
    onceki = tmp_path / "onceki.sqlite3"
    onceki.write_bytes(guncel)

    sonuc = ozet_onarimi.ozetleri_onar(
        onceki_db=onceki,
        yeni_db=gecici,
        dek=TEST_DEK,
        sarmal_ozetleri={str(muhasip.id): app_password.wrap_digest(TEST_DEK, _sarmal(muhasip.id))},
    )

    assert str(muhasip.id) not in sonuc.tasinan + sonuc.capadan
    assert _hesap_satiri(gecici, muhasip.id) == once
    assert onceki.read_bytes() == guncel
    assert not gecici.with_name(gecici.name + "-wal").exists()


def test_onarim_modulu_orm_ve_django_ice_aktarmaz() -> None:
    """Onarım konsol geri yüklemesinde Django kurulmadan da koşar (modül başlığı)."""
    import ast

    kaynak = Path(ozet_onarimi.__file__).read_text(encoding="utf-8")
    izinli = {
        "__future__",
        "logging",
        "sqlite3",
        "collections.abc",
        "contextlib",
        "dataclasses",
        "datetime",
        "pathlib",
        "typing",
    }
    for dugum in ast.walk(ast.parse(kaynak)):
        if isinstance(dugum, ast.Import):
            assert {ad.name for ad in dugum.names} <= izinli
        elif isinstance(dugum, ast.ImportFrom):
            if dugum.module == "shared":
                assert {ad.name for ad in dugum.names} <= {"crypto", "kanonik", "sqlite_adres"}
            elif dugum.module == "apps.okul.services":
                assert {ad.name for ad in dugum.names} <= {"geri_yukleme_yetkisi", "satir_izi"}
            else:
                assert dugum.module in izinli, dugum.module


# ============================================================ bağımsız denetimin bulguları (b3)


def _muhasip_yeniden_degistirir(muhasip_id: object, eski: str, yeni: str) -> None:
    """Muhasip kendi oturumunda parolasını `eski`den `yeni`ye değiştirir; program yöneticisi döner."""
    app_password.lock()
    app_password.unlock(hesap_id=muhasip_id, password=eski)
    with yazar_olarak(Yazar(hesap_id=str(muhasip_id), rol=AccountRole.MUHASIP)):
        app_password.change_password(hesap_id=muhasip_id, current_password=eski, new_password=yeni)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


def _sirla_geri_yukle(tmp_path: Path, yedek: bytes, guncel: bytes, sir: str) -> Path:
    """Program yöneticisinin parolasıyla ya da kurtarma anahtarıyla (güncel dosya) geri yükler."""
    if sir == "parola":
        return _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)
    return _geri_yukle(tmp_path, yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)


def _yazilamadi(_durum: dict[str, Any], _yeni: dict[str, Any]) -> None:
    raise OSError("dosya salt okunur")


def _dosya_hatasi(hata: BaseException, neden: str, *, sifirlama: bool) -> None:
    """Dosya yazımının hatası çağırana dosya hatası olarak döner. Parola sıfırlaması onu Türkçe
    iletili `GuvenlikDosyasiYazilamadi`ya çevirir (kök neden `__cause__`'da; orkestratör maddesi
    (d0)-1: 1. adım yerinde, geçici parola geçerli değil); öteki yazıcılarda hata olduğu gibidir."""
    assert isinstance(hata, hesaplar.GuvenlikDosyasiYazilamadi) is sifirlama
    if sifirlama:
        assert str(hata) == hesaplar.RESET_WRAP_MESSAGE
        assert hata.__cause__ is not None
        hata = hata.__cause__
    assert neden in str(hata)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("sir", ["parola", "kurtarma"])
def test_capa_ikamesi_eski_ozeti_taze_yedege_tasimaz(
    sir: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Çapa ikamesi (bağımsız denetim bulgusu; Senaryo 1): program yöneticisi muhasibin parolasını
    sıfırlar ve hemen veritabanının düz kopyasını alır (kopyada muhasibin asıl özeti geçici
    parolanın sarmalınındır). Muhasip geçici parolayla girip parolasını yeniler; TAZE yedek alınır.
    Program kapalıyken `db.sqlite3` eski kopyayla değiştirilir, arşivdeki geçici parola sarmalı
    `guvenlik.json`'a konur ve taze yedek geri yüklenir. Eski kopya taze yedeğin zincir başını
    içermez: çapa BAYATTIR, özet taşınmaz. Dosyadaki (geri konmuş) sarmal geri yüklenen satırın
    özetini tutmadığı için iki özet BOŞALTILIR (K-a, fail-closed); geçici parola açmaz. (Çapa
    tazelik denetimi olmadan geçici parolanın özeti taze yedeğe aklanırdı.)"""
    muhasip = _muhasip()
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    eski_kopya = _goruntu(tmp_path / "eski-kopya.sqlite3")
    app_password.lock()
    app_password.unlock(hesap_id=muhasip.id, password=UCUNCU_PAROLA, new_password=YENI_PAROLA)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    taze = Account.objects.get(pk=muhasip.id)
    taze_yedek = _goruntu(tmp_path / "taze-yedek.sqlite3")
    _geri_koy(_arsivdeki_sarmal(muhasip.id, UCUNCU_PAROLA))

    db = _sirla_geri_yukle(tmp_path, taze_yedek, eski_kopya, sir)

    assert "bayat çapa" in caplog.text
    satir = _hesap_satiri(db, muhasip.id)
    assert taze.wrap_digest != ""
    assert (satir[geri_yukleme_yetkisi.SIRA_OZET], satir[geri_yukleme_yetkisi.SIRA_BEKLEYEN]) == (
        "",
        "",
    )
    assert geri_yukleme_yetkisi.muhurlu_satir_mi(satir, TEST_DEK)
    _programa_al(db)
    app_password.lock()
    _acilmaz(muhasip.id, UCUNCU_PAROLA)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("sir", ["parola", "kurtarma"])
def test_cift_geri_yuklemede_capada_olmayan_hesabin_ozeti_bosalir(sir: str, tmp_path: Path) -> None:
    """Çift geri yükleme (bağımsız denetim bulgusu): B1 muhasip yokken, B2 muhasip geçici parolayla
    açıldıktan sonra alınır; muhasip parolasını yeniler. Önce B1, ardından (kilit açmadan) B2 geri
    yüklenir. İkinci geri yüklemenin çapası B1'den yazılmış eski veritabanıdır: muhasip orada
    yoktur ve çapa B2'nin zincir başını içermez. Onarım muhasibin İKİ ÖZETİNİ BOŞALTIR: ne yeni
    parola ne arşivden geri konan geçici parola açar; program yöneticisinin sıfırlaması çıkıştır.
    (Boşaltılmasaydı B2'nin geçici parola özeti kalır, arşivdeki o sarmal açardı — Senaryo 1.)"""
    b1 = _goruntu(tmp_path / "b1.sqlite3")
    muhasip = hesap_ac()
    b2 = _goruntu(tmp_path / "b2.sqlite3")
    app_password.lock()
    app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    guncel = _goruntu(tmp_path / "guncel.sqlite3")

    db = _sirla_geri_yukle(tmp_path, b1, guncel, sir)
    db = _sirla_geri_yukle(tmp_path, b2, db.read_bytes(), sir)

    satir = _hesap_satiri(db, muhasip.id)
    assert (satir[geri_yukleme_yetkisi.SIRA_OZET], satir[geri_yukleme_yetkisi.SIRA_BEKLEYEN]) == (
        "",
        "",
    )
    assert geri_yukleme_yetkisi.muhurlu_satir_mi(satir, TEST_DEK)
    _programa_al(db)
    app_password.lock()
    _acilmaz(muhasip.id, YENI_PAROLA)
    _geri_koy(_arsivdeki_sarmal(muhasip.id, GECICI_PAROLA))
    _acilmaz(muhasip.id, GECICI_PAROLA)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    app_password.lock()
    assert _acilir(muhasip.id, UCUNCU_PAROLA).id == muhasip.id


@pytest.mark.django_db(transaction=True)
def test_kapanan_hesabin_saklanan_sarmali_kapanistan_onceki_yedekle_acilmaz(tmp_path: Path) -> None:
    """TK11 (bağımsız denetim bulgusu): açık muhasip sarmalının bir kopyasını saklar; yedek alınır;
    hesap kapatılır (sarmal dosyadan ve arşivlerden silinir). Kapanıştan önceki yedek geri yüklenince
    satır `ACIK` döner; çapada satır `KAPALI` olduğu için iki özet BOŞALTILIR: saklanan kopya
    `guvenlik.json`'a konsa da eski parolayla açılmaz. (Boşaltılmasaydı kapanıştaki son özet o
    kopyayı tutardı.)"""
    muhasip = _muhasip()
    saklanan = _sarmal(muhasip.id)
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id)
    assert app_password._find_wrap(durum(), muhasip.id) is None
    guncel = _goruntu(tmp_path / "guncel.sqlite3")

    db = _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)

    satir = _hesap_satiri(db, muhasip.id)
    assert geri_yukleme_yetkisi.satirdan_muhur_alanlari(satir)["status"] == AccountStatus.ACIK
    assert (satir[geri_yukleme_yetkisi.SIRA_OZET], satir[geri_yukleme_yetkisi.SIRA_BEKLEYEN]) == (
        "",
        "",
    )
    assert geri_yukleme_yetkisi.muhurlu_satir_mi(satir, TEST_DEK)
    _programa_al(db)
    veri = durum()
    veri["hesaplar"].append(saklanan)
    durum_yaz(veri)
    app_password.lock()
    _acilmaz(muhasip.id, GECICI_PAROLA)


def test_kapali_durum_sabiti_modeldekiyle_ayni() -> None:
    assert ozet_onarimi.DURUM_KAPALI == AccountStatus.KAPALI.value


def _muhru_bozuk_capa(
    tmp_path: Path,
) -> tuple[Account, dict[str, Any], dict[str, Any], bytes, bytes]:
    """Muhasip W1 (geçici) → W2 → W3 geçer; yedek W2 günündendir. Güncel veritabanında muhasibin
    özeti program dışından W1'inkine çevrilir (çapa satırının mührü bozulur). (muhasip, W1, W2,
    yedek, güncel) döner."""
    muhasip = _muhasip()
    w1 = _sarmal(muhasip.id)
    _muhasip_yeniden_degistirir(muhasip.id, GECICI_PAROLA, YENI_PAROLA)
    w2 = _sarmal(muhasip.id)
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    _muhasip_yeniden_degistirir(muhasip.id, YENI_PAROLA, UCUNCU_PAROLA)
    ham_guncelle(muhasip.id, wrap_digest=app_password.wrap_digest(TEST_DEK, w1))
    guncel = _goruntu(tmp_path / "guncel.sqlite3")
    return muhasip, w1, w2, yedek, guncel


@pytest.mark.django_db(transaction=True)
def test_capadaki_muhru_bozuk_satirin_ozeti_tasinmaz_bosaltilir(tmp_path: Path) -> None:
    """Çapa satırının mühür şartı ve K-a (orkestratör kararı, b4): çapadaki satırın mührü bozuksa
    çapa o hesap için KULLANILAMAZ; özet taşınmaz. Dosyada W1 (geri konmuş) durur ve geri yüklenen
    satırın (W2 günü) özetini tutmaz: iki özet BOŞALTILIR (fail-closed), onarım `SISTEM` `HESAP`
    satırıyla izlenir. W1 açılmaz; geri yüklemeden SONRA arşivden geri konan W2 de açılmaz (b3'te
    açıyordu: kapanan kalan risk). Çıkış program yöneticisinin parola sıfırlamasıdır."""
    muhasip, w1, w2, yedek, guncel = _muhru_bozuk_capa(tmp_path)
    _geri_koy(w1)

    db = _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)

    satir = _hesap_satiri(db, muhasip.id)
    assert (satir[geri_yukleme_yetkisi.SIRA_OZET], satir[geri_yukleme_yetkisi.SIRA_BEKLEYEN]) == (
        "",
        "",
    )
    assert geri_yukleme_yetkisi.muhurlu_satir_mi(satir, TEST_DEK)
    _programa_al(db)
    app_password.lock()
    _acilmaz(muhasip.id, GECICI_PAROLA)
    _geri_koy(w2)
    _acilmaz(muhasip.id, YENI_PAROLA)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    app_password.lock()
    assert _acilir(muhasip.id, UCUNCU_PAROLA).id == muhasip.id


@pytest.mark.django_db(transaction=True)
def test_bilinen_sinir_geri_yuklemeden_once_konan_yedek_gunu_sarmali_acar(tmp_path: Path) -> None:
    """KALAN RİSK (K-a; `app_password` modül başlığı "KALAN RİSKLER" (c)): çapa kullanılamazken
    (burada çapadaki satırın mührü bozuk) yedek günündeki sarmal (W2) geri yüklemeden ÖNCE
    `guvenlik.json`'a konursa geri yüklenen satırın özetini tutar, özetler kalır ve o günün
    parolası açar. Görünürlüğü geri yükleme kartıdır. Test riski sabitler: kapanırsa ret testine
    döner."""
    muhasip, _w1, w2, yedek, guncel = _muhru_bozuk_capa(tmp_path)
    _geri_koy(w2)

    db = _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)

    satir = _hesap_satiri(db, muhasip.id)
    assert satir[geri_yukleme_yetkisi.SIRA_OZET] == app_password.wrap_digest(TEST_DEK, w2)
    _programa_al(db)
    app_password.lock()
    assert _acilir(muhasip.id, YENI_PAROLA).id == muhasip.id  # kalan risk


@pytest.mark.django_db(transaction=True)
def test_capada_bekleyeni_tutan_sarmal_asil_olur_eski_sarmal_acilmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Taşıma dalı: muhasibin parola değişimi dosyayı yazıp düşmüştür (çapada asıl özet eski W1'in,
    bekleyen yeni W2'nin; dosyada W2). Geri yüklemede dosyadaki sarmal çapanın BEKLEYEN özetini
    tutar: geri yüklenen satırın asıl özeti W2'ninki olur, bekleyen boşalır; W1 geri konsa açılmaz.
    (Taşınmasaydı çapanın iki özeti aynen geçer, W1 asıl kalırdı.)"""
    muhasip = _muhasip()
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    app_password.lock()
    app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA)
    gercek = app_password._replace_wrap

    def yazip_dus(durum_: dict[str, Any], yeni_: dict[str, Any]) -> None:
        gercek(durum_, yeni_)
        raise OSError("süreç öldü")

    with monkeypatch.context() as yama:
        yama.setattr(app_password, "_replace_wrap", yazip_dus)
        with (
            yazar_olarak(Yazar(hesap_id=str(muhasip.id), rol=AccountRole.MUHASIP)),
            pytest.raises(OSError, match="süreç öldü"),
        ):
            app_password.change_password(
                hesap_id=muhasip.id, current_password=GECICI_PAROLA, new_password=YENI_PAROLA
            )
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    capadaki = Account.objects.get(pk=muhasip.id)
    assert capadaki.wrap_digest_pending == app_password.wrap_digest(TEST_DEK, _sarmal(muhasip.id))
    guncel = _goruntu(tmp_path / "guncel.sqlite3")

    db = _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)

    satir = _hesap_satiri(db, muhasip.id)
    assert (satir[geri_yukleme_yetkisi.SIRA_OZET], satir[geri_yukleme_yetkisi.SIRA_BEKLEYEN]) == (
        capadaki.wrap_digest_pending,
        "",
    )
    _programa_al(db)
    app_password.lock()
    _geri_koy(_arsivdeki_sarmal(muhasip.id, GECICI_PAROLA))
    _acilmaz(muhasip.id, GECICI_PAROLA)


@pytest.mark.django_db(transaction=True)
def test_onarim_yazilamazsa_geri_yukleme_hicbir_dosyaya_dokunmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Onarımın yazıcı bağlantısı hata verirse geri yükleme yarıda kalır (`OnarimYazilamadi` →
    `BackupRestoreError`): canlı veritabanı, `guvenlik.json` ve geri yükleme notu değişmez, önceki
    veritabanı kenara alınmaz, `.tmp` kalmaz. (Hata yutulsaydı yedek günündeki özet takasla
    canlıya geçerdi.)"""
    muhasip = _muhasip()
    yedek = _goruntu(tmp_path / "yedek.sqlite3")
    _muhasip_parolasini_degistirir(muhasip)  # onarım yazmalı (taşınan)
    guncel = _goruntu(tmp_path / "guncel.sqlite3")
    guvenlik = app_password.state_path().read_bytes()
    gercek = sqlite3.connect

    def yazici_duser(adres: Any, *args: Any, **kwargs: Any) -> sqlite3.Connection:
        if not kwargs.get("uri"):
            raise sqlite3.OperationalError("disk I/O error")
        return cast("sqlite3.Connection", gercek(adres, *args, **kwargs))

    sahte = type("SahteSqlite", (), {"connect": staticmethod(yazici_duser), "Error": sqlite3.Error})
    monkeypatch.setattr(ozet_onarimi, "sqlite3", sahte)

    with pytest.raises(backup_restore.BackupRestoreError):
        _geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)

    canli = tmp_path / "canli"
    assert (canli / "db.sqlite3").read_bytes() == guncel
    # Salt okunur okumanın boş `-wal`/`-shm`'i bilinen bedeldir (`geri_yukleme_yetkisi` başlığı);
    # kenara alınmış veritabanı ve `.tmp` kalmaz.
    assert {p.name for p in canli.iterdir()} <= {"db.sqlite3", "db.sqlite3-wal", "db.sqlite3-shm"}
    assert app_password.state_path().read_bytes() == guvenlik
    assert not geri_yukleme_notu.var_mi(app_password.state_path().parent)


def test_askidaki_hesapta_ozet_durumdan_once_denetlenir() -> None:
    """Kilit açılışında sıra mühür → ÖZET → durum (`_open_account_for_login`): askıdaki (`ASKIDA`)
    hesabın eski sarmalı geri konunca ret özetinkidir ve `BUTUNLUK` satırı düşer — program dışı
    değişiklik durumun arkasına saklanmaz. Güncel sarmal askı iletisini alır."""
    muhasip = _muhasip()
    _muhasip_yeniden_degistirir(muhasip.id, GECICI_PAROLA, YENI_PAROLA)
    muhurle(Account.objects.get(pk=muhasip.id), status=AccountStatus.ASKIDA)
    guncel = _sarmal(muhasip.id)
    app_password.lock()
    _geri_koy(_arsivdeki_sarmal(muhasip.id, GECICI_PAROLA))
    _acilmaz(muhasip.id, GECICI_PAROLA)
    _geri_koy(guncel)
    with pytest.raises(app_password.AccountSuspended):
        app_password.unlock(hesap_id=muhasip.id, password=YENI_PAROLA)


def test_baska_kimligin_sarmali_yazilmaz() -> None:
    """`write_account_wrap` önceden kurulmuş sarmalı yalnız kendi kimliğine yazar: başka hesabın
    sarmalını program yöneticisinin yerine koyan çağrı `ValueError` alır, dosya değişmez."""
    muhasip = _muhasip()
    sarmal = app_password.new_account_wrap(
        TEST_DEK, hesap_id=muhasip.id, tanitici=muhasip.login_name, password=UCUNCU_PAROLA
    )
    once = app_password.state_path().read_bytes()
    with pytest.raises(ValueError, match="kimliği"):
        app_password.write_account_wrap(
            data_key=TEST_DEK, hesap_id=TEST_HESAP_ID, tanitici="yonetici", sarmal=sarmal
        )
    assert app_password.state_path().read_bytes() == once


@pytest.mark.parametrize("yazici", ["sifirlama", "kurtarma"])
def test_kesintide_dosyaya_konmus_eski_sarmal_asil_ozet_olmaz(
    yazici: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Korunan asıl özetin meşruluk koşulu (`_kept_digest`; bağımsız denetim bulgusu): hesabın eski
    sarmalı arşivden geri konmuşken dosya yazılamazsa (salt okunur dosya, başka programda açık —
    kod gerekmez) sıfırlamanın ya da kurtarmanın 1. adımı ESKİ sarmalın özetini asıl yazmaz;
    satırınki kalır, eski parola açmaz."""
    calistir: Callable[[], object]
    if yazici == "sifirlama":
        muhasip = _muhasip()
        _muhasip_yeniden_degistirir(muhasip.id, GECICI_PAROLA, YENI_PAROLA)
        kimlik, eski = str(muhasip.id), GECICI_PAROLA

        def calistir() -> object:
            return hesaplar.reset_password(
                by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=UCUNCU_PAROLA
            )
    else:
        app_password.change_password(
            hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
        )
        app_password.lock()
        kimlik, eski = TEST_HESAP_ID, TEST_PAROLA

        def calistir() -> object:
            return app_password.unlock_with_recovery(
                recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=kimlik, new_password=UCUNCU_PAROLA
            )

    asil = Account.objects.get(pk=kimlik).wrap_digest
    _geri_koy(_arsivdeki_sarmal(kimlik, eski))
    with monkeypatch.context() as yama:
        yama.setattr(app_password, "_replace_wrap", _yazilamadi)
        with pytest.raises(OSError) as hata:
            calistir()
    _dosya_hatasi(hata.value, "salt okunur", sifirlama=yazici == "sifirlama")

    assert Account.objects.get(pk=kimlik).wrap_digest == asil
    app_password.lock()
    _acilmaz(kimlik, eski)


def test_kesintide_dosyadaki_bekleyen_sarmal_korunur(monkeypatch: pytest.MonkeyPatch) -> None:
    """Meşru bekleyen sarmal dalı (`_kept_digest`): muhasibin parola değişimi dosyayı yazıp düşer
    (asıl eski W1, bekleyen yeni W2, dosyada W2); ilk açılıştan önce yapılan sıfırlamanın 2. adımı
    da düşerse korunan asıl özet dosyadaki (bekleyenle tutan) W2'ninkidir: yeni parola açar (meşru
    kullanıcı kilitlenmez), W1 geri konsa açmaz."""
    muhasip = _muhasip()
    kimlik = str(muhasip.id)
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA)
    gercek = app_password._replace_wrap

    def yazip_dus(durum_: dict[str, Any], yeni_: dict[str, Any]) -> None:
        gercek(durum_, yeni_)
        raise OSError("süreç öldü")

    with monkeypatch.context() as yama:
        yama.setattr(app_password, "_replace_wrap", yazip_dus)
        with (
            yazar_olarak(Yazar(hesap_id=kimlik, rol=AccountRole.MUHASIP)),
            pytest.raises(OSError, match="süreç öldü"),
        ):
            app_password.change_password(
                hesap_id=kimlik, current_password=GECICI_PAROLA, new_password=YENI_PAROLA
            )
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    with monkeypatch.context() as yama:
        yama.setattr(app_password, "_replace_wrap", _yazilamadi)
        with pytest.raises(hesaplar.GuvenlikDosyasiYazilamadi) as hata:
            hesaplar.reset_password(
                by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=UCUNCU_PAROLA
            )
    _dosya_hatasi(hata.value, "salt okunur", sifirlama=True)
    w2 = _sarmal(kimlik)
    assert Account.objects.get(pk=kimlik).wrap_digest == app_password.wrap_digest(TEST_DEK, w2)
    app_password.lock()
    _geri_koy(_arsivdeki_sarmal(kimlik, GECICI_PAROLA))
    _acilmaz(kimlik, GECICI_PAROLA)
    _geri_koy(w2)
    assert str(_acilir(kimlik, YENI_PAROLA).id) == kimlik


def _zehirli_arsiv() -> Path:
    """Derin iç içe JSON taşıyan arşiv (`json.loads` `RecursionError`; metin düzenleyiciyle
    üretilebilir, kod gerekmez)."""
    yol = app_password.state_path().with_name("guvenlik-arsiv-zz.json")
    yol.write_text("[" * 100_000 + "]" * 100_000, encoding="utf-8")
    return yol


def _yazim_izi_tam(hesap_id: str, yazici: str, son: int) -> None:
    """Yazım tamamlandı: oturum açık, yazımın satırı ve `GIRIS` izde, özet dosyadakinin."""
    assert OTURUM.hesap_id() == hesap_id
    eylemler = list(AuditTrail.objects.filter(seq__gt=son).values_list("action", flat=True))
    beklenen = AuditAction.KURTARMA if yazici == "kurtarma" else AuditAction.PAROLA
    assert beklenen in eylemler and eylemler[-1] == AuditAction.GIRIS
    satir = Account.objects.get(pk=hesap_id)
    assert satir.wrap_digest == app_password.wrap_digest(TEST_DEK, _sarmal(hesap_id))
    assert satir.wrap_digest_pending == ""
    if yazici == "kurtarma":
        assert satir.reset_notice_pending is True


@pytest.mark.parametrize("yazici", ["kurtarma", "kilit_yenileme"])
def test_zehirli_arsiv_kurtarmayi_ve_yenilemeyi_izsiz_birakmaz(yazici: str) -> None:
    """Zehirli arşiv (bağımsız denetim bulgusu): sarmal yazımından SONRA koşan kapalı hesap
    temizliği arşivleri okur. Derin iç içe JSON okunamayan arşiv sayılır ve atlanır: kurtarma
    anahtarıyla açılış ve kilit açılışında yenileme tamamlanır, `KURTARMA`/`PAROLA` satırı ve
    bildirim yeni parolayla birlikte vardır. Zehir dururken kilit açılışı da açılır (hizmet reddi
    yok)."""
    hesap_id, _eski, yeni, calistir = _yazici(yazici)
    _zehirli_arsiv()
    son = _son_seq()
    calistir()
    _yazim_izi_tam(hesap_id, yazici, son)
    app_password.lock()
    assert str(app_password.unlock(hesap_id=hesap_id, password=yeni).id) == hesap_id


def test_kapali_hesap_temizligi_dusse_de_giris_ve_izi_surer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kapalı hesap temizliği HİÇBİR hatayla girişi düşürmez (yalnız dosya hatası değil): sarmal
    yazımından sonra commit dışında düşebilecek adım kalmaz. Beklenmeyen bir hata günlüğe düşer;
    kurtarma anahtarıyla açılışın `KURTARMA` satırı, bildirimi ve yeni sarmalı birlikte kalır."""
    hesap_id, _eski, yeni, calistir = _yazici("kurtarma")

    def bozuk() -> set[str]:
        raise RuntimeError("beklenmeyen")

    monkeypatch.setattr(app_password, "_archived_wrap_ids", bozuk)
    son = _son_seq()
    calistir()
    _yazim_izi_tam(hesap_id, "kurtarma", son)
    app_password.lock()
    assert str(app_password.unlock(hesap_id=hesap_id, password=yeni).id) == hesap_id


def test_zehirli_arsiv_kapali_hesap_temizligini_durdurmaz() -> None:
    """Okunamayan (derin iç içe) arşiv atlanır, temizliği durdurmaz: kapanmanın arşiv adımı yarıda
    kalmış hesabın sarmalı öteki arşivden yine silinir (TK11). Arşiv okuması `RecursionError`'ı
    yakalamasaydı temizlik bütünüyle düşer, sarmal arşivde kalırdı."""
    muhasip = _muhasip()
    sarmal = _sarmal(muhasip.id)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id)
    kalinti = arsiv_yaz("kalinti", {"surum": 2, "hesaplar": [sarmal]})
    zehir = _zehirli_arsiv()
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert arsivdeki_kimlikler(kalinti) == []
    assert zehir.exists()
