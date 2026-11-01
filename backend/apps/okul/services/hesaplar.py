"""Hesap servisleri — açma, kapama, parola sıfırlama, askıdan çıkarma, iki depo karşılaştırması.

Tasarım §4.4.1, §4.4.5, §4.6.1; plan F1b-1 ("Hesap açma, kapama, parola sıfırlama
ve askıdan çıkarma servisleri 1. adımdadır; uçları, Kullanıcılar ekranı ve hesap
teslim pusulası 2. adımda"). Dosya ayağı (`guvenlik.json` sarmalları ve arşivler)
`app_password`'tedir; burası veritabanı ayağını ve iki deponun SIRASINI yönetir.

**Rol denetimi 2. adımda (tasarım §4.4.2):** bu servisler işlemi yapan hesabı
(`by_hesap_id`) yalnız açık (`ACIK`) ve mührü tutan bir hesap olarak doğrular;
kimin hangi işi yapabileceği (`yonetici`) rol matrisinin işidir. Her servis kilit
açıkken çalışır (DEK bellekte; mühür ve şifreli ad onu ister).

SIRALAR (iki depo kuralı, §4.6.1):

* **Açma:** önce veritabanı (`PAROLA_YENILENMELI`, mühür), sonra sarmal (geçici
  parolayla). Arada kesilirse satır sarmalsız kalır; giriş zaten açılmaz, program
  yöneticisi yeniden geçici parola verir (`reset_password` sarmalı yeniden kurar).
* **Kapama:** önce veritabanı (`KAPALI`, `closed_at`, mühür), sonra sarmal
  `guvenlik.json`'dan ve bütün arşivlerden silinir (TK11). Arada kesilirse kilit
  açılışındaki temizlik siler (`app_password._cleanup_closed_wraps`).
* **Parola sıfırlama:** önce veritabanı (`PAROLA_YENILENMELI`, yenilenme izi),
  sonra sarmal. Ters sırada kesinti, program yöneticisinin bildiği geçici parolayı
  zorunlu değişim OLMADAN geçerli bırakırdı.
* **Askıdan çıkarma:** `Account.status = ASKIDA` ise satır, sonra dosyadaki hatalı
  deneme sayacı ve askısı (iki kaynak; plan F1b-1 "Oturum").

Mührü tutmayan satıra hiçbir servis dokunmaz (`AccountSealMismatch`): yeniden
mühürlemek program dışından değiştirilmiş satırı meşrulaştırırdı (tehdit 19).

KİLİT EKRANI LİSTESİ (`lock_screen_accounts`; tasarım §4.4.3, plan F1b-1 "Oturum"):
kilitliyken çalışır, DEK istemez ve kişi adı döndürmez (şifreli ad-soyad okunmaz).
Kurtarma anahtarıyla açılışın hesap listesi (`recovery_accounts`) aynı kurallarla
veritabanından çıkar: sarmalı olmayan program yöneticisi de görünür (TK10 geri yüklemesi).

KISITLAR (sert; sistem bütünlüğü, altın kural 3): açık hesaplar arasında tanıtıcı
tekil ve tek hesaplı roller (DB kısıtı; burada Türkçe iletiyle önce denetlenir),
Denetleme Kurulu en çok üç, en az bir açık program yöneticisi (son yönetici
kapatılamaz). Tanıtıcının ad-soyadı içermesi uyarıdır, engel değildir
(`hesap_kurallari.login_name_warning`; çağıran gösterir).
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.okul.models import (
    MAX_AUDIT_BOARD_ACCOUNTS,
    SINGLE_ACCOUNT_ROLES,
    Account,
    AccountRole,
    AccountStatus,
    ResetKind,
)
from apps.okul.oturum import rol_etiketi
from apps.okul.services import app_password, hesap_kurallari
from apps.okul.services.app_password import AccountSealMismatch, AppPasswordError
from shared import crypto

logger = logging.getLogger("oab_defteri.guvenlik")

_LOCKED_MESSAGE = "Kayıtlar kilitli. Önce hesabınızla kilidi açın."
_ACTOR_MESSAGE = "İşlemi yapan hesap açık değil. Kilitleyip hesabınızla yeniden açın."
_NOT_FOUND_MESSAGE = "Hesap bulunamadı."
_CLOSED_MESSAGE = "Hesap kapalı; kapalı hesap yeniden açılmaz, yeni hesap açılır."
_SEAL_MESSAGE = (
    "Hesap kaydı program dışından değiştirilmiş görünüyor; kayda dokunulmadı. "
    "Denetleme Kuruluna bildirin."
)
_LOGIN_NAME_TAKEN_MESSAGE = "Bu tanıtıcı açık bir başka hesapta kullanılıyor."
_SINGLE_ROLE_MESSAGE = "Bu rolde açık bir hesap zaten var; önce onu kapatın."
_AUDIT_BOARD_LIMIT_MESSAGE = (
    f"Denetleme Kurulu için en çok {MAX_AUDIT_BOARD_ACCOUNTS} hesap açık olabilir."
)
_LAST_ADMIN_MESSAGE = "Son program yöneticisi hesabı kapatılamaz."
_ROLE_MESSAGE = "Geçerli bir rol seçin."
_SUSPENDED_RESET_MESSAGE = "Askıdaki hesabın parolası sıfırlanamaz; önce hesabı askıdan çıkarın."  # noqa: S105
_NOT_ORPHAN_MESSAGE = (
    "Silinmek istenen sarmal artık sahipsiz değil; listeyi yenileyip yeniden deneyin."
)


class AccountServiceError(AppPasswordError):
    """Hesap servisinin Türkçe reddi (view katmanı 400'e çevirir)."""


def _kural(dogrulayici: Callable[[str], str], deger: str) -> str:
    """`hesap_kurallari` doğrulayıcısını çağırır; ihlali bu modülün hata türüne çevirir."""
    try:
        return dogrulayici(deger)
    except hesap_kurallari.AccountRuleError as exc:
        raise AccountServiceError(str(exc)) from exc


def _active_data_key() -> bytes:
    """Bellekteki DEK; kilitliyse ret (hesap servisleri kilit açıkken çalışır)."""
    dek = crypto.active_key()
    if dek is None:
        raise AccountServiceError(_LOCKED_MESSAGE)
    return dek


def _actor(by_hesap_id: object, data_key: bytes) -> Account:
    """İşlemi yapan hesap: var, `ACIK` ve mührü tutuyor. Rol denetimi 2. adımda (§4.4.2)."""
    aktor = app_password.account_by_id(by_hesap_id)
    if aktor is None or aktor.status != AccountStatus.ACIK:
        raise AccountServiceError(_ACTOR_MESSAGE)
    if not aktor.seal_matches(data_key):
        raise AccountSealMismatch(_SEAL_MESSAGE)
    return aktor


def _target(hesap_id: object, data_key: bytes) -> Account:
    """Üzerinde işlem yapılan hesap: var, kapalı değil, mührü tutuyor."""
    hesap = app_password.account_by_id(hesap_id)
    if hesap is None:
        raise AccountServiceError(_NOT_FOUND_MESSAGE)
    if hesap.status == AccountStatus.KAPALI:
        raise AccountServiceError(_CLOSED_MESSAGE)
    if not hesap.seal_matches(data_key):
        logger.warning("Hesap mührü tutmadı; hesap işlemi yapılmadı (%s).", hesap.id)
        raise AccountSealMismatch(_SEAL_MESSAGE)
    return hesap


def _needs_password_renewal(hesap: Account) -> bool:
    """Askıdan dönen hesap geçici parolasını henüz değiştirmemişse `PAROLA_YENILENMELI` olur."""
    if hesap.password_changed_at is None:
        return True
    return hesap.reset_at is not None and hesap.password_changed_at < hesap.reset_at


def default_login_name(role: str) -> str:
    """Rolden türeyen, açık hesaplarda kullanılmayan ilk tanıtıcı (tasarım §4.4.4)."""
    alinmis = Account.objects.exclude(status=AccountStatus.KAPALI).values_list(
        "login_name", flat=True
    )
    return hesap_kurallari.default_login_name(role, alinmis)


@sensitive_variables("temp_password", "parola", "dek")
def open_account(
    *, by_hesap_id: object, role: str, tanitici: str, display_name: str, temp_password: str
) -> Account:
    """Yeni hesap açar (`PAROLA_YENILENMELI`); ilk girişte geçici parola değiştirilir.

    Önce veritabanı (mühürlü satır), sonra geçici parolalı sarmal (modül başlığı).
    Kısıt ihlali Türkçe iletiyle reddedilir. Organ bağı (üyelik) F1c'de zorunlu
    olur; bugün hesap rolle açılır (tasarım §4.4.1).
    """
    dek = _active_data_key()
    aktor = _actor(by_hesap_id, dek)
    if role not in AccountRole.values:
        raise AccountServiceError(_ROLE_MESSAGE)
    login = _kural(hesap_kurallari.validate_login_name, tanitici)
    ad = _kural(hesap_kurallari.validate_display_name, display_name)
    parola = _kural(hesap_kurallari.validate_password, temp_password)
    acik = Account.objects.exclude(status=AccountStatus.KAPALI)
    if acik.filter(login_name=login).exists():
        raise AccountServiceError(_LOGIN_NAME_TAKEN_MESSAGE)
    if role in SINGLE_ACCOUNT_ROLES and acik.filter(role=role).exists():
        raise AccountServiceError(_SINGLE_ROLE_MESSAGE)
    if (
        role == AccountRole.DENETLEME_KURULU
        and acik.filter(role=role).count() >= MAX_AUDIT_BOARD_ACCOUNTS
    ):
        raise AccountServiceError(_AUDIT_BOARD_LIMIT_MESSAGE)
    try:
        with transaction.atomic():
            hesap = Account(
                login_name=login,
                role=role,
                display_name=ad,
                status=AccountStatus.PAROLA_YENILENMELI,
                opened_at=timezone.now(),
                opened_by=aktor,
            )
            hesap.seal = hesap.compute_seal(dek)
            hesap.save(force_insert=True)
    except IntegrityError as exc:  # yarış: DB kısıtı son sözü söyler
        raise AccountServiceError(_LOGIN_NAME_TAKEN_MESSAGE) from exc
    app_password.write_account_wrap(
        data_key=dek, hesap_id=hesap.id, tanitici=login, password=parola
    )
    logger.info("Hesap açıldı (%s, %s).", hesap.login_name, hesap.role)
    return hesap


def close_account(*, by_hesap_id: object, hesap_id: object) -> Account:
    """Hesabı kapatır; sarmalı `guvenlik.json`'dan ve bütün arşivlerden silinir (TK11).

    Önce veritabanı (`KAPALI`, `closed_at`, kapatan, mühür), sonra dosyalar. Satır
    kalır (denetim izi için; altın kural 4). Son açık program yöneticisi kapatılamaz.
    """
    dek = _active_data_key()
    aktor = _actor(by_hesap_id, dek)
    hesap = _target(hesap_id, dek)
    if (
        hesap.role == AccountRole.YONETICI
        and Account.objects.exclude(status=AccountStatus.KAPALI)
        .filter(role=AccountRole.YONETICI)
        .count()
        <= 1
    ):
        raise AccountServiceError(_LAST_ADMIN_MESSAGE)
    with transaction.atomic():
        hesap.status = AccountStatus.KAPALI
        hesap.suspend_reason = ""
        hesap.closed_at = timezone.now()
        hesap.closed_by = aktor
        hesap.seal = hesap.compute_seal(dek)
        hesap.save(update_fields=["status", "suspend_reason", "closed_at", "closed_by", "seal"])
    app_password.remove_account_wraps({str(hesap.id)})
    logger.info("Hesap kapatıldı (%s).", hesap.login_name)
    return hesap


@sensitive_variables("temp_password", "parola", "dek")
def reset_password(*, by_hesap_id: object, hesap_id: object, temp_password: str) -> Account:
    """Hesabın parolasını geçici parolayla sıfırlar (`PAROLA_YENILENMELI`; tehdit 12).

    Önce veritabanı (durum, `reset_at`, `reset_by`, `reset_kind = SIFIRLAMA`,
    `reset_notice_pending`, mühür), sonra sarmal yeni geçici parolayla kurulur;
    hatalı deneme sayacı ve askısı sıfırlanır. Sahibi ilk girişinde parolasını
    değiştirir ve sıfırlama bildirimini görür. `ASKIDA` durumundaki hesap önce
    askıdan çıkarılır.
    """
    dek = _active_data_key()
    aktor = _actor(by_hesap_id, dek)
    hesap = _target(hesap_id, dek)
    if hesap.status == AccountStatus.ASKIDA:
        raise AccountServiceError(_SUSPENDED_RESET_MESSAGE)
    parola = _kural(hesap_kurallari.validate_password, temp_password)
    with transaction.atomic():
        hesap.status = AccountStatus.PAROLA_YENILENMELI
        hesap.reset_at = timezone.now()
        hesap.reset_by = aktor
        hesap.reset_kind = ResetKind.SIFIRLAMA
        hesap.reset_notice_pending = True
        hesap.seal = hesap.compute_seal(dek)
        hesap.save(
            update_fields=[
                "status",
                "reset_at",
                "reset_by",
                "reset_kind",
                "reset_notice_pending",
                "seal",
            ]
        )
    app_password.write_account_wrap(
        data_key=dek, hesap_id=hesap.id, tanitici=hesap.login_name, password=parola
    )
    logger.info("Hesabın parolası sıfırlandı (%s).", hesap.login_name)
    return hesap


def unsuspend(*, by_hesap_id: object, hesap_id: object) -> Account:
    """Hesabı askıdan çıkarır: iki kaynak birlikte (plan F1b-1 "Oturum").

    `Account.status = ASKIDA` ise satır `ACIK`'a (geçici parolası değişmemişse
    `PAROLA_YENILENMELI`'ye) döner, askı nedeni silinir, mühür yenilenir; sonra
    dosyadaki hatalı deneme sayacı ve askısı kaldırılır (arşivlenmez). Askıda olmayan
    hesapta yalnız sayaç sıfırlanır (fikirdeş).
    """
    dek = _active_data_key()
    _actor(by_hesap_id, dek)
    hesap = _target(hesap_id, dek)
    if hesap.status == AccountStatus.ASKIDA:
        with transaction.atomic():
            hesap.status = (
                AccountStatus.PAROLA_YENILENMELI
                if _needs_password_renewal(hesap)
                else AccountStatus.ACIK
            )
            hesap.suspend_reason = ""
            hesap.seal = hesap.compute_seal(dek)
            hesap.save(update_fields=["status", "suspend_reason", "seal"])
    app_password.clear_failed_attempts(hesap.id)
    logger.info("Hesap askıdan çıkarıldı (%s).", hesap.login_name)
    return hesap


# ---------------------------------------------------------------------------
# İki depo karşılaştırması (§4.6.1 kural 4: geri yüklemeden sonraki ilk kilit açılışı)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TwoStoreDifferences:
    """`guvenlik.json` ile `Account` tablosunun farkı (kimlik listeleri, sıralı).

    * `rows_without_wrap`: açık (`KAPALI` olmayan) ama sarmalı olmayan hesaplar;
      `ACIK` olanlar karşılaştırmada `PAROLA_YENILENMELI`'ye çekilir.
    * `wraps_without_row`: satırı olmayan sarmallar;
    * `wraps_of_closed`: satırı `KAPALI` (mührü tutan) sarmallar;
    * `seal_mismatch`: mührü tutmayan satırlar — hiçbir işleme konu olmaz.

    İlk iki sarmal listesi yalnız program yöneticisinin onayıyla silinir
    (`remove_orphan_wraps`).
    """

    rows_without_wrap: list[str] = field(default_factory=list)
    wraps_without_row: list[str] = field(default_factory=list)
    wraps_of_closed: list[str] = field(default_factory=list)
    seal_mismatch: list[str] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not (
            self.rows_without_wrap
            or self.wraps_without_row
            or self.wraps_of_closed
            or self.seal_mismatch
        )

    @property
    def removable_wraps(self) -> list[str]:
        """Onayla silinebilecek sarmallar (satırsız + kapalı)."""
        return sorted({*self.wraps_without_row, *self.wraps_of_closed})


def two_store_differences() -> TwoStoreDifferences:
    """İki deponun farkını hesaplar; HİÇBİR ŞEY yazmaz (kilit açık olmalı: mühür DEK ister)."""
    dek = _active_data_key()
    sarmallar = set(app_password.wrap_ids())
    satirlar = {str(hesap.id): hesap for hesap in Account.objects.all()}
    sarmalsiz: list[str] = []
    satirsiz: list[str] = []
    kapali: list[str] = []
    muhursuz: list[str] = []
    for hesap_id, hesap in satirlar.items():
        if not hesap.seal_matches(dek):
            muhursuz.append(hesap_id)
            continue
        if hesap.status == AccountStatus.KAPALI:
            if hesap_id in sarmallar:
                kapali.append(hesap_id)
        elif hesap_id not in sarmallar:
            sarmalsiz.append(hesap_id)
    for hesap_id in sarmallar:
        if hesap_id not in satirlar:
            satirsiz.append(hesap_id)
    return TwoStoreDifferences(
        rows_without_wrap=sorted(sarmalsiz),
        wraps_without_row=sorted(satirsiz),
        wraps_of_closed=sorted(kapali),
        seal_mismatch=sorted(muhursuz),
    )


def reconcile_two_stores() -> TwoStoreDifferences:
    """Farkı hesaplar ve sarmalı olmayan `ACIK` hesapları `PAROLA_YENILENMELI` yapar.

    Geri yüklemeden sonraki ilk kilit açılışında koşar (çağıran oturum katmanıdır;
    geri yükleme notu alt commit (c)'de). Sarmalı olmayan hesabın sahibi giremez;
    program yöneticisi geçici parola verir (`reset_password` sarmalı kurar). Sarmal
    silmez: o, listenin gösterilip onaylanmasıyla `remove_orphan_wraps`'tadır.
    """
    dek = _active_data_key()
    fark = two_store_differences()
    for hesap in Account.objects.filter(pk__in=fark.rows_without_wrap, status=AccountStatus.ACIK):
        hesap.status = AccountStatus.PAROLA_YENILENMELI
        hesap.seal = hesap.compute_seal(dek)
        hesap.save(update_fields=["status", "seal"])
        logger.info("Sarmalı olmayan hesap parola yenilemeye çekildi (%s).", hesap.login_name)
    return fark


def remove_orphan_wraps(*, by_hesap_id: object, hesap_idler: list[str]) -> list[str]:
    """Program yöneticisinin onayıyla satırsız ya da kapalı hesap sarmallarını siler.

    Yalnız güncel farkta silinebilir görünen kimlikler kabul edilir (onaydan sonra
    durum değiştiyse ret); mührü tutmayan satırın sarmalı asla silinmez. Silme
    `guvenlik.json`'dan ve bütün arşivlerden yapılır. Silinen kimlikleri döndürür.
    Rol denetimi (yalnız program yöneticisi) 2. adımdadır (§4.4.2).
    """
    dek = _active_data_key()
    _actor(by_hesap_id, dek)
    istenen = {str(h) for h in hesap_idler}
    silinebilir = set(two_store_differences().removable_wraps)
    if not istenen <= silinebilir:
        raise AccountServiceError(_NOT_ORPHAN_MESSAGE)
    if istenen:
        app_password.remove_account_wraps(istenen)
        logger.info("Sahipsiz hesap sarmalları onayla silindi (%d).", len(istenen))
    return sorted(istenen)


# ---------------------------------------------------------------------------
# Kilit ekranının hesap listesi (tasarım §4.4.3; plan F1b-1 "Oturum")
# ---------------------------------------------------------------------------
#: Hatalı deneme askısının kodu (`guvenlik.json` `askida`); veritabanı askısı
#: `SuspendReason` değerini taşır. Kodlar kullanıcı metnine çıkmaz: ön yüz ikisini de
#: "askıda — program yöneticisine başvurun" diye yazar (sözlük "Hesap").
HATALI_DENEME_ASKISI = "HATALI_DENEME"
#: `ASKIDA` satırında neden boşsa (program dışı yazım) kullanılan kod.
ASKI_NEDENI_BILINMIYOR = "ASKIDA"

#: Birden çok açık hesabı olabilen rollerde etikete sıra no eklenir ("Denetleme Kurulu 2").
_ROL_SIRASI = {rol: sira for sira, rol in enumerate(AccountRole.values)}


def lock_screen_accounts() -> list[dict[str, Any]]:
    """Kilit ekranının hesap listesi; kilitliyken çalışır, DEK İSTEMEZ, kişi adı DÖNDÜRMEZ.

    Liste `guvenlik.json`'daki sarmallardan çıkar (`app_password.account_wraps`); rol,
    durum ve askı nedeni veritabanının düz sütunlarından okunur (şifreli ad-soyad
    sorguya hiç girmez). Her satır `{id, tanitici, rol, rol_etiketi, secilebilir,
    askida_nedeni}`:

    * `KAPALI` satırın sarmalı listelenmez (kapanmış hesap; sarmalı kilit açılışındaki
      temizlik siler);
    * askının iki kaynağı vardır — hatalı deneme askısı (`HATALI_DENEME`) ve
      `Account.status = ASKIDA` (`SuspendReason` değeri); ikisi de seçilemez;
    * rolü veritabanından okunamayan satır (satır yok, kimlik biçimsiz, rol
      tanınmıyor) "Hesap kaydı okunamadı" etiketiyle görünür ve seçilemez (plan
      F1b-1: "rolü veritabanından okunamayan satır açılmaz").

    Sıra: rol sırası (`AccountRole`), sonra açılış zamanı, sonra tanıtıcı; okunamayan
    satırlar sonda. Aynı rolde birden çok hesap varsa etikete açılış sırasıyla sıra no
    eklenir ("Denetleme Kurulu 2"). Mühür burada denetlenmez (DEK yok): mührü tutmayan
    satır kilit açılışında reddedilir (`hesap_muhru_tutmadi`).
    """
    sarmallar = app_password.account_wraps()
    kimlikler: list[uuid.UUID] = []
    for sarmal in sarmallar:
        try:
            kimlikler.append(uuid.UUID(sarmal["id"]))
        except ValueError:
            continue
    satirlar = {
        str(satir["id"]): satir
        for satir in Account.objects.filter(pk__in=kimlikler).values(
            "id", "role", "status", "suspend_reason", "opened_at", "login_name"
        )
    }
    okunan: list[dict[str, Any]] = []
    okunamayan: list[dict[str, Any]] = []
    for sarmal in sarmallar:
        satir = satirlar.get(sarmal["id"])
        if satir is not None and satir["status"] == AccountStatus.KAPALI:
            continue
        if satir is None or satir["role"] not in _ROL_SIRASI:
            okunamayan.append(
                {
                    "id": sarmal["id"],
                    "tanitici": sarmal["tanitici"],
                    "rol": None,
                    "rol_etiketi": rol_etiketi(None),
                    "secilebilir": False,
                    "askida_nedeni": HATALI_DENEME_ASKISI if sarmal["askida"] else None,
                }
            )
            continue
        neden: str | None = None
        if sarmal["askida"]:
            neden = HATALI_DENEME_ASKISI
        elif satir["status"] == AccountStatus.ASKIDA:
            neden = satir["suspend_reason"] or ASKI_NEDENI_BILINMIYOR
        okunan.append(
            {
                "id": sarmal["id"],
                "tanitici": sarmal["tanitici"],
                "rol": satir["role"],
                "rol_etiketi": rol_etiketi(satir["role"]),
                "secilebilir": neden is None
                and satir["status"] in (AccountStatus.ACIK, AccountStatus.PAROLA_YENILENMELI),
                "askida_nedeni": neden,
                "_acilis": satir["opened_at"],
            }
        )
    okunan.sort(key=lambda h: (_ROL_SIRASI[h["rol"]], h["_acilis"], h["tanitici"]))
    adet: dict[str, int] = {}
    for hesap in okunan:
        adet[hesap["rol"]] = adet.get(hesap["rol"], 0) + 1
    sira: dict[str, int] = {}
    for hesap in okunan:
        del hesap["_acilis"]
        if adet[hesap["rol"]] > 1:
            sira[hesap["rol"]] = sira.get(hesap["rol"], 0) + 1
            hesap["rol_etiketi"] = f"{hesap['rol_etiketi']} {sira[hesap['rol']]}"
    return [*okunan, *okunamayan]


def recovery_accounts() -> list[dict[str, Any]]:
    """Kurtarma anahtarıyla açılabilecek hesaplar; kilitliyken çalışır, DEK İSTEMEZ, kişi adı DÖNDÜRMEZ.

    Tasarım §4.4.3-§4.4.4, TK10: kurtarma anahtarıyla yapılan geri yüklemeden sonra
    (yeni bilgisayara taşıma, güvenlik dosyası kayıp kilidinden çıkış) `guvenlik.json`
    yalnız kurtarma bölümünü taşır; kilit ekranı listesi sarmallardan çıktığı için
    boştur (plan F1b-1 "Oturum"). "Kurtarma anahtarıyla aç + program yöneticisi
    parolası" ekranı hesabı bu listeden seçer (`GET security/recover/`).

    Liste veritabanından çıkar: `KAPALI` olmayan ve kurtarma yolunun kabul ettiği
    durumdaki (`ACIK`, `PAROLA_YENILENMELI`) program yöneticisi satırları; açılış
    sırasıyla. Her satır `{id, tanitici, rol_etiketi, sarmali_var}`; `sarmali_var`
    satırın bu bilgisayarın güvenlik dosyasında sarmalı olup olmadığıdır (yoksa
    kurtarmayla açılış sarmalı yeniden kurar). Yalnız düz sütunlar okunur (şifreli
    ad-soyad sorguya girmez); mühür açılışta denetlenir (`hesap_muhru_tutmadi`).
    """
    sarmallar = {sarmal["id"] for sarmal in app_password.account_wraps()}
    satirlar = (
        Account.objects.filter(
            role=AccountRole.YONETICI,
            status__in=(AccountStatus.ACIK, AccountStatus.PAROLA_YENILENMELI),
        )
        .order_by("opened_at", "login_name")
        .values("id", "login_name")
    )
    return [
        {
            "id": str(satir["id"]),
            "tanitici": satir["login_name"],
            "rol_etiketi": rol_etiketi(AccountRole.YONETICI.value),
            "sarmali_var": str(satir["id"]) in sarmallar,
        }
        for satir in satirlar
    ]
