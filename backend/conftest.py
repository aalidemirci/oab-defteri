"""Backend test altyapısı — varsayılan güvenlik ortamı (tasarım §4.4.4, §5.3; şema 2).

İlk program yöneticisi hesabı zorunludur ve şifreli alan anahtarsız yazmaz
(fail-closed, tasarım §5.3). Bu yüzden her test, gerçek programın olağan çalışma
hâlinde başlar: **ilk hesap kurulu + kilit açık + oturumda o hesap**.

OTOMATİK FİXTÜR `guvenlik_ortami` (her teste uygulanır, DB İSTEMEZ):

* Ucuz Argon2 profili (`crypto.DEFAULT_KDF` = t=1, 8 KiB, p=1). Yalnız maliyet
  parametresidir; algoritma, zarf yapısı ve dosya biçimi üretimdekiyle aynıdır.
* Geçici `OD_SECURITY_DIR` (güvenlik dosyası + `yedekleme.json`) ve
  `OD_BACKUP_DIR`; testin kendi `tmp_path`'inden AYRI dizinlerdir.
* Sabit test DEK'i (`TEST_DEK`) için GEÇERLİ bir şema 2 `guvenlik.json`: tek
  hesap sarmalı (`TEST_HESAP_ID`, tanıtıcı `TEST_TANITICI`, parola `TEST_PAROLA`),
  kurtarma bölümü (no 1, anahtar `TEST_KURTARMA_ANAHTARI`), `gecis: null`; buna
  eşlik eden `yedekleme.json` (yedek açık anahtarı).
* Oturum `TEST_HESAP_ID` (program yöneticisi) hesabıyla AÇIKTIR (`oturum.OTURUM`;
  DEK ve iz anahtarı `TEST_IA` bellekte). Test sonunda kilitlenir.
* Kademeli yanlış parola gecikmesi sıfırlanır ve `FAILURE_DELAYS=(0.0,)`
  (gerçek `sleep` yok; davranışı ayrı test kendisi kurar).
* Süreç içi bozuk okuma kaydı (`crypto.corrupt_reads`), "yeniden başlat" kapısı
  (`restart_gate`), oturum nesnesi (saat, boşta süre önbelleği, kurulum bilgisi) ve
  uzun iş sayacı sıfırlanır; ortak bakım kapısı (`shared.bakim.KAPI`) test sonunda
  yeniden açılır.

İKİ DEPO KURALI yüzünden kilit açma veritabanı ister (`Account` satırı, mühür, iz
anahtarı). Varsayılan ortam DB'ye YAZMAZ: "dosya var, satır yok" hâlidir. Kilit
açan, parola değiştiren ya da hesap servisi çağıran testler `yonetici_hesabi`
fixtürünü ister: `TEST_HESAP_ID`'nin mühürlü `Account` satırı, `TEST_IA`'lı
`AuditKey` ve parmak izi yazılır (DB gerekir).

EK FİXTÜRLER (testin istemesi gerekir):

* `parolasiz` — güvenlik dosyası ve `yedekleme.json` YOK, anahtar YOK: hesap hiç
  kurulmamış ilk açılış ("kurulum" durumu). Kişi yazan uçlar 409 döner,
  `Student.save()` `KeyMissingError` yükseltir.
* `kilitli` — güvenlik dosyası VAR, anahtar YOK (program kilitli). Açmak için
  `app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)` (+ `yonetici_hesabi`).
* `parmak_izi_yazili` — DB'ye `TEST_DEK`'in parmak izini yazar (DB gerekir);
  "güvenlik dosyası kayıp" senaryosu bunun üstüne dosyayı siler.
* `yonetici_hesabi` — yukarıda; `Account` satırını döndürür.

Oturumu doğrudan açan yardımcı `oturumu_ac_test`'tir (kilit ekranısız; Argon2 ve
veritabanı istemez).
"""

from __future__ import annotations

import base64
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

# Sabit test anahtarları (32 bayt). Gerçek bir sır DEĞİLDİR; yalnız testlerde.
TEST_DEK = bytes(range(32))
TEST_IA = bytes(range(64, 96))
TEST_PAROLA = "Test-Yonetici-Parolasi-1"
TEST_KURTARMA_ANAHTARI = "TEST-KURT-ARMA-ANAH-TARI-ABCD-EFGH-JKLM"
#: Varsayılan ortamın ilk program yöneticisi hesabı (uydurma ad; gerçek kişi değildir).
TEST_HESAP_ID = "6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60"
TEST_TANITICI = "yonetici"
TEST_HESAP_ADI = "Örnek Yönetici"

_UCUZ_KDF: dict[str, int] = {"time_cost": 1, "memory_cost": 8, "parallelism": 1}

# Durum dosyası içeriği oturum boyunca bir kez üretilir (Argon2 ucuz olsa da
# her teste tuz/sarmal üretmek gereksiz). Yalnız okunur; her test kendi
# dizinine yazar.
_durum_onbellegi: dict[str, Any] = {}


def _test_durumu() -> dict[str, Any]:
    """`TEST_DEK`'i `TEST_PAROLA` (hesap) ve `TEST_KURTARMA_ANAHTARI` ile saran şema 2 durumu."""
    if not _durum_onbellegi:
        from apps.okul.services import app_password
        from shared import crypto

        onceki = crypto.DEFAULT_KDF
        crypto.DEFAULT_KDF = crypto.KdfParams.from_dict(_UCUZ_KDF)
        try:
            durum = app_password._build_state(
                TEST_DEK,
                hesap_id=TEST_HESAP_ID,
                tanitici=TEST_TANITICI,
                password=TEST_PAROLA,
                recovery_key=TEST_KURTARMA_ANAHTARI,
            )
        finally:
            crypto.DEFAULT_KDF = onceki
        _durum_onbellegi.update(durum)
    kopya: dict[str, Any] = json.loads(json.dumps(_durum_onbellegi))  # derin kopya
    return kopya


def _oturum_sifirla() -> None:
    """Oturum nesnesini ve uzun iş sayacını sıfırlar (süreç içi; testler arasında sızar)."""
    from apps.okul.oturum import OTURUM
    from shared import bakim

    OTURUM._reset_for_tests()
    bakim.UZUN_ISLER._reset_for_tests()


def oturumu_ac_test(
    hesap_id: str = TEST_HESAP_ID, *, tanitici: str = TEST_TANITICI, rol: str = "yonetici"
) -> None:
    """Oturumu kilit ekranısız açar: DEK ve iz anahtarı yüklenir, hesap oturuma girer."""
    from apps.okul.oturum import OTURUM, OturumHesabi

    OTURUM.ac(
        OturumHesabi(id=str(hesap_id), tanitici=tanitici, rol=rol),
        veri_anahtari=TEST_DEK,
        iz_anahtari=TEST_IA,
    )


@pytest.fixture(autouse=True)
def guvenlik_ortami(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """Varsayılan test ortamı: ilk hesap kurulu + kilit açık (modül başlığına bakın).

    Güvenlik dizininin yolunu döndürür (`guvenlik.json` ve `yedekleme.json` orada).
    """
    from desktop.backup_crypto import ensure_public_config

    from apps.okul import restart_gate
    from apps.okul.services import app_password
    from shared import bakim, crypto

    guvenlik_dizini = tmp_path_factory.mktemp("od-guvenlik")
    yedek_dizini = tmp_path_factory.mktemp("od-yedek")
    monkeypatch.setenv(app_password.ENV_SECURITY_DIR, str(guvenlik_dizini))
    monkeypatch.setenv(app_password.ENV_BACKUP_DIR, str(yedek_dizini))
    monkeypatch.setattr(crypto, "DEFAULT_KDF", crypto.KdfParams.from_dict(_UCUZ_KDF))
    monkeypatch.setattr(app_password, "FAILURE_DELAYS", (0.0,))

    (guvenlik_dizini / app_password.STATE_FILE_NAME).write_text(
        json.dumps(_test_durumu(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ensure_public_config(guvenlik_dizini, TEST_DEK, replace=True)
    app_password._reset_failures()
    crypto._reset_corrupt_reads_for_tests()
    restart_gate._reset_for_tests()
    _oturum_sifirla()
    oturumu_ac_test()
    yield guvenlik_dizini
    app_password.lock()
    app_password._reset_failures()
    crypto._reset_corrupt_reads_for_tests()
    restart_gate._reset_for_tests()
    _oturum_sifirla()
    # Başarılı canlı geri yükleme bakım kapısını süreç boyunca kapalı bırakır (§13 D3).
    bakim.KAPI.bakimdan_cik()


@pytest.fixture
def parolasiz(guvenlik_ortami: Path) -> Path:
    """Hesap hiç kurulmamış ilk açılış: güvenlik dosyası ve yedek anahtarı yok, anahtar yok."""
    from desktop.backup_crypto import config_path

    from apps.okul.services import app_password

    app_password.lock()
    app_password.state_path().unlink(missing_ok=True)
    config_path(guvenlik_ortami).unlink(missing_ok=True)
    return guvenlik_ortami


@pytest.fixture
def kilitli(guvenlik_ortami: Path) -> Path:
    """Program kilitli: güvenlik dosyası var, anahtar bellekte değil."""
    from apps.okul.services import app_password

    app_password.lock()
    return guvenlik_ortami


@pytest.fixture
def parmak_izi_yazili(guvenlik_ortami: Path, db: None) -> str:
    """DB'ye `TEST_DEK`'in parmak izini yazar; parmak izini döndürür."""
    from apps.okul.models import SchoolConfig
    from shared import crypto

    parmak = crypto.key_fingerprint(TEST_DEK)
    config, _ = SchoolConfig.objects.get_or_create(pk=SchoolConfig.SINGLETON_PK)
    config.app_password_hash = parmak
    config.save(update_fields=["app_password_hash", "updated_at"])
    return parmak


@pytest.fixture
def yonetici_hesabi(parmak_izi_yazili: str) -> Any:
    """`TEST_HESAP_ID`'nin mühürlü `Account` satırı + `TEST_IA`'lı `AuditKey` (DB gerekir).

    Şifreli ad DEK ister: kilitli bir testte de çağrılabilsin diye anahtar geçici
    olarak yüklenir ve önceki hâl (kilitli ya da açık) korunur.
    """
    from django.utils import timezone

    from apps.okul.models import Account, AccountRole, AccountStatus, AuditKey
    from shared import crypto

    kilitliydi = not crypto.is_unlocked()
    if kilitliydi:
        crypto.load_key(TEST_DEK, audit_key=TEST_IA)
    try:
        simdi = timezone.now()
        hesap = Account(
            id=TEST_HESAP_ID,
            login_name=TEST_TANITICI,
            role=AccountRole.YONETICI,
            display_name=TEST_HESAP_ADI,
            status=AccountStatus.ACIK,
            opened_at=simdi,
            password_changed_at=simdi,
        )
        hesap.seal = hesap.compute_seal(TEST_DEK)
        hesap.save(force_insert=True)
        AuditKey.objects.create(
            key=base64.b64encode(TEST_IA).decode("ascii"), valid_from_seq=1, created_at=simdi
        )
    finally:
        if kilitliydi:
            crypto.unload_key()
    return Account.objects.get(pk=TEST_HESAP_ID)
