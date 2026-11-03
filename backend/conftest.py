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
* Yazar bağlamı (TK16) o hesaptır (`VARSAYILAN_YAZAR`): test, oturumdaki hesabın
  isteği gibi koşar. Üretimde bağlamı istek başında ara katman kurar
  (`lock_middleware`); servisi doğrudan çağıran test de aynı yazarla yazar. Bağlamsız
  yazmayı sınayan test `yazar_olarak(None)` ile bağlamı kaldırır.
* Kademeli yanlış parola gecikmesi sıfırlanır ve `FAILURE_DELAYS=(0.0,)`
  (gerçek `sleep` yok; davranışı ayrı test kendisi kurar).
* Süreç içi bozuk okuma kaydı (`crypto.corrupt_reads`), "yeniden başlat" kapısı
  (`restart_gate`), oturum nesnesi (saat, boşta süre önbelleği, kurulum bilgisi),
  denetim izi yazıcısının anahtar doğrulama önbelleği ve uzun iş sayacı sıfırlanır;
  ortak bakım kapısı (`shared.bakim.KAPI`) test sonunda yeniden açılır.

OTOMATİK FİXTÜR `varsayilan_hesap` (yalnız VERİTABANI kullanan testte): İKİ DEPO KURALI
ve denetim izi veritabanı ister. Her yazma iz satırı yazar; satırın hesabı `Account`'a
bağlıdır (PROTECT) ve mührü `AuditKey`'deki İA'dır. Bu yüzden veritabanı kullanan her
testte `yonetici_hesabi` kurulur: `TEST_HESAP_ID`'nin mühürlü `Account` satırı,
`TEST_IA`'lı `AuditKey`, parmak izi ve hesabın `HESAP` iz satırı (`enable` gibi: zincir bu
satırla, `seq = 1`'den başlar). İz satırı zorunludur: hesap satırı denetim izindeki son içerik
MAC'li kaydını tutmazsa giriş, oturum işlemi ve hesap işlemi reddedilir (kullanıcı kararı
03.11.2026 "Girişte reddet"; `app_password` modül başlığı "SATIRIN İZİ"). Hesabı ve iz anahtarı
OLMAYAN veritabanı isteyen test ya `parolasiz`'ı
ister (hiç kurulmamış ilk açılış) ya da `@pytest.mark.hesapsiz` işaretini taşır (ör.
"güvenlik dosyasını sıfırla" koşulu şifreli tabloların boş olmasını ister). Yazıcının ve
kilitli kipin ZİNCİR BAŞINI sınayan test (ilk satırın `prev_mac`'i boş, sıra 1'den) ise
`@pytest.mark.bos_zincir` taşır: hesap ve iz anahtarı kurulur, hesabın iz satırı yazılmaz —
o testte hesabın girişi ve hesap işlemleri satır izi yüzünden reddedilir. DB kullanmayan test
veritabanına dokunmaz: güvenlik dosyası var, satır yok.

DENETİM İZİ VE `flush` (`iz_tetikleyicili_flush`, oturum boyu): `AuditTrail`'in `BEFORE
DELETE` tetikleyicisi `transaction=True` testlerinin sonundaki `flush`'ı (`DELETE FROM`)
keserdi. Yalnız test sürecinde SQLite arka ucunun `execute_sql_flush`'ı sarılır: aynı
işlemde tetikleyiciler `sqlite_master`'daki tanımlarıyla düşürülür, tablolar boşaltılır,
tanımlar AYNEN yeniden kurulur. Üretimde tetikleyicileri kapatan bir yol yoktur; göçün
kurduğu tanım test sonunda da yerindedir (`test_denetim_izi.py` sınar).

EK FİXTÜRLER (testin istemesi gerekir):

* `parolasiz` — güvenlik dosyası ve `yedekleme.json` YOK, anahtar YOK: hesap hiç
  kurulmamış ilk açılış ("kurulum" durumu). Kişi yazan uçlar 409 döner,
  `Student.save()` `KeyMissingError` yükseltir. Veritabanında hesap kurulmaz.
* `kilitli` — güvenlik dosyası VAR, anahtar YOK (program kilitli). Açmak için
  `app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)`.
* `parmak_izi_yazili` — DB'ye `TEST_DEK`'in parmak izini yazar (DB gerekir);
  "güvenlik dosyası kayıp" senaryosu bunun üstüne dosyayı siler.
* `yonetici_hesabi` — yukarıda; `Account` satırını döndürür (veritabanı kullanan
  testte zaten kuruludur; aynı satırı verir).

Oturumu doğrudan açan yardımcı `oturumu_ac_test`'tir (kilit ekranısız; Argon2 ve
veritabanı istemez).
"""

from __future__ import annotations

import base64
import json
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from django.db.backends.sqlite3.operations import DatabaseOperations

# Sabit test anahtarları (32 bayt). Gerçek bir sır DEĞİLDİR; yalnız testlerde.
TEST_DEK = bytes(range(32))
TEST_IA = bytes(range(64, 96))
TEST_PAROLA = "Test-Yonetici-Parolasi-1"
TEST_KURTARMA_ANAHTARI = "TEST-KURT-ARMA-ANAH-TARI-ABCD-EFGH-JKLM"
#: Varsayılan ortamın ilk program yöneticisi hesabı (uydurma ad; gerçek kişi değildir).
TEST_HESAP_ID = "6f1c2a3b-4d5e-4f60-8a71-0b2c3d4e5f60"
TEST_TANITICI = "yonetici"
TEST_HESAP_ADI = "Örnek Yönetici"
#: Varsayılan yazar bağlamının rolü (`VARSAYILAN_YAZAR`; modül başlığı).
TEST_ROL = "yonetici"

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


def varsayilan_yazar() -> Any:
    """Varsayılan ortamın yazar bağlamı: oturumdaki program yöneticisi (modül başlığı)."""
    from apps.okul.oturum import Yazar

    return Yazar(hesap_id=TEST_HESAP_ID, rol=TEST_ROL)


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

    from apps.okul import denetim_izi, iz_durumu, restart_gate
    from apps.okul.oturum import yazar_olarak
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
    denetim_izi._reset_for_tests()
    iz_durumu._reset_for_tests()
    _oturum_sifirla()
    oturumu_ac_test()
    with yazar_olarak(varsayilan_yazar()):
        yield guvenlik_dizini
    app_password.lock()
    app_password._reset_failures()
    crypto._reset_corrupt_reads_for_tests()
    restart_gate._reset_for_tests()
    denetim_izi._reset_for_tests()
    iz_durumu._reset_for_tests()
    _oturum_sifirla()
    # Başarılı canlı geri yükleme bakım kapısını süreç boyunca kapalı bırakır (§13 D3).
    bakim.KAPI.bakimdan_cik()


def _veritabani_kullanir(request: pytest.FixtureRequest) -> bool:
    """Test veritabanı kullanıyor mu? (`django_db` işareti ya da `db`/`transactional_db`)"""
    return (
        request.node.get_closest_marker("django_db") is not None
        or "_django_db_helper" in request.fixturenames
    )


@pytest.fixture(autouse=True)
def varsayilan_hesap(request: pytest.FixtureRequest, guvenlik_ortami: Path) -> None:
    """Veritabanı kullanan testte program yöneticisinin satırı ve iz anahtarı (modül başlığı).

    `parolasiz` isteyen ya da `hesapsiz` işaretli testte kurulmaz; `bos_zincir` işaretli testte
    hesabın iz satırı yazılmaz.
    """
    if not _veritabani_kullanir(request):
        return
    if "parolasiz" in request.fixturenames or request.node.get_closest_marker("hesapsiz"):
        return
    request.getfixturevalue("yonetici_hesabi")


#: Varsayılan ortamın yazdığı iz satırı sayısı (`yonetici_hesabi`: hesabın `HESAP` satırı). Testin
#: kendi yazdığı ilk satırın sırası `KURULUM_IZI + 1`'dir (`bos_zincir` işaretli testte 1).
KURULUM_IZI = 1


@pytest.fixture(autouse=True, scope="session")
def iz_tetikleyicili_flush() -> Iterator[None]:
    """`transaction=True` testlerinin `flush`'ı denetim izinin tetikleyicisine takılmasın.

    Yalnız test süreci (modül başlığı "DENETİM İZİ VE flush"): aynı işlemde
    `okul_audittrail`'in tetikleyicileri `sqlite_master`'daki tanımlarıyla düşürülür,
    tablolar boşaltılır, tanımlar AYNEN yeniden kurulur. Tabloda satır yokken de aynı
    yol koşar (tanım değişmez).
    """
    from django.db import transaction
    from django.db.backends.sqlite3.operations import DatabaseOperations

    asil = DatabaseOperations.execute_sql_flush

    def tetikleyicileri_koruyarak(self: DatabaseOperations, sql_list: list[str]) -> None:
        with transaction.atomic(using=self.connection.alias):
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' "
                    "AND tbl_name = 'okul_audittrail' ORDER BY name"
                )
                tetikleyiciler = [(str(ad), str(sql)) for ad, sql in cursor.fetchall()]
                for ad, _ in tetikleyiciler:
                    cursor.execute(f'DROP TRIGGER "{ad}"')
            asil(self, sql_list)
            with self.connection.cursor() as cursor:
                for _, sql in tetikleyiciler:
                    cursor.execute(sql)

    with pytest.MonkeyPatch.context() as yama:
        yama.setattr(DatabaseOperations, "execute_sql_flush", tetikleyicileri_koruyarak)
        yield


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
def kilitli(request: pytest.FixtureRequest, guvenlik_ortami: Path) -> Path:
    """Program kilitli: güvenlik dosyası var, anahtar bellekte değil.

    Veritabanı kullanan testte kilitlenme düzenli kilit gibi önce çapayı yazar
    (`iz_durumu.capa_yaz`): zincir varsayılan hesabın iz satırıyla başlar ve çapasız zincir ilk
    kilit açılışında "çapa yok" bulgusu (`BUTUNLUK` satırı) olurdu.
    """
    from apps.okul import iz_durumu
    from apps.okul.services import app_password

    if _veritabani_kullanir(request) and not request.node.get_closest_marker("hesapsiz"):
        iz_durumu.capa_yaz()
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
def yonetici_hesabi(request: pytest.FixtureRequest, parmak_izi_yazili: str) -> Any:
    """`TEST_HESAP_ID`'nin mühürlü `Account` satırı + `TEST_IA`'lı `AuditKey` (DB gerekir).

    Satır güvenlik dosyasındaki sarmalın özetini taşır (`wrap_digest`; kullanıcı kararı
    03.11.2026 "tazelik kapatılır"): satır ve sarmal ayrı kurulur, özet de kurulur.

    Şifreli ad DEK ister: kilitli bir testte de çağrılabilsin diye anahtar geçici
    olarak yüklenir ve önceki hâl (kilitli ya da açık) korunur. Satır, ilk hesabın
    (`app_password.enable`) yazdığı gibi `HESAP` iz satırıyla aynı işlemde yazılır: zincir
    bu satırla başlar (modül başlığı); `bos_zincir` işaretli testte iz satırı yazılmaz.
    """
    from django.db import transaction
    from django.utils import timezone

    from apps.okul import denetim_izi
    from apps.okul.models import Account, AccountRole, AccountStatus, AuditAction, AuditKey
    from apps.okul.oturum import Yazar, yazar_olarak
    from apps.okul.services import app_password
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
        sarmal = app_password._find_wrap(app_password.read_state() or {}, TEST_HESAP_ID)
        hesap.wrap_digest = (app_password.wrap_digest(TEST_DEK, sarmal) or "") if sarmal else ""
        hesap.seal = hesap.compute_seal(TEST_DEK)
        with (
            yazar_olarak(Yazar(hesap_id=TEST_HESAP_ID, rol=TEST_ROL)),
            transaction.atomic(),
        ):
            hesap.save(force_insert=True)
            anahtar = AuditKey.objects.create(
                key=base64.b64encode(TEST_IA).decode("ascii"), valid_from_seq=1, created_at=simdi
            )
            if request.node.get_closest_marker("bos_zincir") is None:
                denetim_izi.kayit(
                    AuditAction.HESAP,
                    hesap,
                    onceki=None,
                    anahtar=denetim_izi.AcikAnahtar(ia=TEST_IA, kayit_id=anahtar.pk),
                )
    finally:
        if kilitliydi:
            crypto.unload_key()
    return Account.objects.get(pk=TEST_HESAP_ID)
