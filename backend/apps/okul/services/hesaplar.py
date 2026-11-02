"""Hesap servisleri — açma, kapama, parola sıfırlama, askıdan çıkarma, iki depo karşılaştırması.

Tasarım §4.4.1, §4.4.5, §4.6.1; plan F1b-1 ("Hesap açma, kapama, parola sıfırlama
ve askıdan çıkarma servisleri 1. adımdadır; uçları, Kullanıcılar ekranı ve hesap
teslim pusulası 2. adımda"). Dosya ayağı (`guvenlik.json` sarmalları ve arşivler)
`app_password`'tedir; burası veritabanı ayağını ve iki deponun SIRASINI yönetir.

**İşlemi yapan ve rolü** (`_actor`, `_yonetici_aktor`): işlemi yapan hesap (`by_hesap_id`)
açık (`ACIK`), mührü tutan ve isteğin yazarıyla aynı hesap olmalıdır; yazar yoksa ya da
`SISTEM` ise ret (hesap işlemi kullanıcı eylemidir). Hesap yönetimi — açma, kapama, parola
sıfırlama, askıdan çıkarma, sahipsiz sarmalın silinmesi — yalnız program yöneticisinindir
(tasarım §4.4.2 Kullanıcılar satırı): rol kapısının (`RolMiddleware`) ardından servis de
mühürlü satırın rolüyle yetki kapısına sorar (`rol_izinleri.Eylem.HESAP_YONETIMI`; derin
savunma, ret 403 `rol_yetkisiz`). Parola yenilenme bildiriminin kapatılması her rolde açıktır
(sahibinin kendi bildirimi). Her servis kilit açıkken çalışır (DEK bellekte; mühür ve şifreli
ad onu ister).

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

DENETİM İZİ (tasarım §4.6.2; plan F1b-1 alt commit c). Her satır yazımı iz satırıyla AYNI
işlemdedir (`apps.okul.denetim_izi`): açma, kapama ve askıdan çıkarma `HESAP`, parola
sıfırlama `PAROLA`, parola yenilenme bildiriminin kapatılması `GUNCELLE`. Yazar istek
başındaki bağlamdır (oturumdaki hesap); `by_hesap_id` işlemi yapan hesabın açık ve mühürlü
olduğunu doğrulamak içindir ve yazarla AYNI hesap olmalıdır (`_actor`): satırın hesabı
yazardan, `opened_by`/`closed_by`/`reset_by` `by_hesap_id`'den gelir; ikisi ayrışırsa
servis reddeder (Kullanıcılar uçlarının güvenlik ağı). İki depo sırası korunur:
satır ve iz satırı birlikte, sonra dosya. Dosyadaki sayacı ve askıyı ya da sarmalı
değiştiren adımlar (askıdan çıkarma, parola sıfırlamanın ve kapamanın dosya adımı,
sahipsiz sarmalın silinmesi) `guvenlik.json` bölümünün (`denetim_izi.HESAP_SARMALI`)
`HESAP` satırını önceki değerleriyle yazar (`app_password.sarmal_izi`; sayaç ve askı
sıfırsa sıfırlama ve kapamada satır yok); satır dosyadan ÖNCE, aynı işlemde eklenir
(`app_password.dosya_ve_iz_islemi`). Geri yüklemeden sonraki karşılaştırmanın durum
düzeltmesi programın kendi işidir: yazar `SISTEM`'dir.

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

from apps.okul import denetim_izi
from apps.okul.models import (
    MAX_AUDIT_BOARD_ACCOUNTS,
    SINGLE_ACCOUNT_ROLES,
    Account,
    AccountRole,
    AccountStatus,
    AuditAction,
    ResetKind,
)
from apps.okul.oturum import rol_etiketi, sistem_olarak, yazar
from apps.okul.rol_izinleri import Eylem, yetki
from apps.okul.services import app_password, hesap_kurallari
from apps.okul.services.app_password import AccountSealMismatch, AppPasswordError
from shared import crypto
from shared.exceptions import RolYetkisiz

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
# Genel Bakış'ın "Hesaplar ve Güvenlik Dosyası" kartında görünür: "sarmal" kullanıcı metnine
# girmez, kullanıcıdaki adı hesabın güvenlik dosyasındaki parola kaydıdır (sözlük §1 "Denetim izi").
_NOT_ORPHAN_MESSAGE = (
    "Bu parola kaydı artık güvenlik dosyasından silinebilecek durumda değil; Genel Bakış'ı "
    "yenileyip yeniden deneyin."
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
    """İşlemi yapan hesap: var, `ACIK`, mührü tutuyor ve yazarla aynı (rol sorulmaz).

    Yazar bağlamı istek başındaki oturum hesabıdır; işlemi yapan o hesap olmalıdır: iz
    satırının hesabı yazardan, kaydın `opened_by`/`closed_by`/`reset_by`'ı bu hesaptan gelir;
    ayrışırlarsa kayıt başkasının adına yazılmış olurdu (modül başlığı). Yazar yoksa ya da
    `SISTEM` ise ret (`RolYetkisiz`): hesap işlemi gün işi ya da sistem işi değildir (plan
    F1b-1 "by_hesap_id yazar bağlamındaki hesaba eşit olmalıdır"). Rolü soran
    `_yonetici_aktor`'dur; parola yenilenme bildiriminin kapatılması her role açık kalır.
    """
    kim = yazar()
    if kim is None or kim.sistem_mi:
        raise RolYetkisiz
    aktor = app_password.account_by_id(by_hesap_id)
    if aktor is None or aktor.status != AccountStatus.ACIK:
        raise AccountServiceError(_ACTOR_MESSAGE)
    if denetim_izi.kimlik_metni_ya_da_none(Account, kim.hesap_id) != str(aktor.id):
        logger.warning("İşlemi yapan hesap yazar bağlamındaki hesap değil; işlem yapılmadı.")
        raise AccountServiceError(_ACTOR_MESSAGE)
    if not aktor.seal_matches(data_key):
        raise AccountSealMismatch(_SEAL_MESSAGE)
    return aktor


def _yonetici_aktor(by_hesap_id: object, data_key: bytes) -> Account:
    """`_actor` + hesap yönetimi yetkisi (yalnız program yöneticisi; modül başlığı).

    Rol mühürlü satırdandır (`aktor.role`; açılışta doğrulanan mühre girer): yazarın rolüyle
    aynıdır, satır program dışından değiştirildiyse mühür zaten tutmaz.
    """
    aktor = _actor(by_hesap_id, data_key)
    yetki(str(aktor.role), Eylem.HESAP_YONETIMI)
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
    aktor = _yonetici_aktor(by_hesap_id, dek)
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
            denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=None)
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

    Sarmalda hatalı deneme sayacı ya da askı varsa silinirken izi düşer: dosya adımının
    işleminde, dosyadan ÖNCE `guvenlik.sarmal` satırı (`app_password.sarmal_izi`; modül
    başlığı). Ana dosya yazılamazsa o satır geri alınır, sarmalı kilit açılışındaki
    temizlik siler (o da iz yazar); sarmal ana dosyadan silinip bir arşiv kopyası
    temizlenemediyse satır kalır, hata yine çağırana döner.
    """
    dek = _active_data_key()
    aktor = _yonetici_aktor(by_hesap_id, dek)
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
        onceki = denetim_izi.anlik(hesap)
        hesap.status = AccountStatus.KAPALI
        hesap.suspend_reason = ""
        hesap.closed_at = timezone.now()
        hesap.closed_by = aktor
        hesap.seal = hesap.compute_seal(dek)
        hesap.save(update_fields=["status", "suspend_reason", "closed_at", "closed_by", "seal"])
        denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=onceki)
    kimlik = str(hesap.id)
    arsiv_hatasi: OSError | None = None
    with app_password.dosya_ve_iz_islemi():
        app_password.sarmal_izi(kimlik, silindi=True)
        try:
            app_password.remove_account_wraps({kimlik})
        except OSError as exc:
            if kimlik in app_password.wrap_ids():
                raise  # ana dosya yazılmadı: sarmalın satırı da geri alınır
            arsiv_hatasi = exc
    if arsiv_hatasi is not None:
        raise arsiv_hatasi
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

    Sarmalda sayaç ya da askı varsa izi kalkarken düşer: sarmal yazımının işleminde,
    dosyadan ÖNCE `guvenlik.sarmal` satırı (`app_password.sarmal_izi`). İki işlemdir:
    veritabanı satırı sarmaldan ÖNCE commit edilir (modül başlığı "Parola sıfırlama");
    sarmal yazılamazsa yalnız ikinci işlem (sayacın satırı) geri alınır.
    """
    dek = _active_data_key()
    aktor = _yonetici_aktor(by_hesap_id, dek)
    hesap = _target(hesap_id, dek)
    if hesap.status == AccountStatus.ASKIDA:
        raise AccountServiceError(_SUSPENDED_RESET_MESSAGE)
    parola = _kural(hesap_kurallari.validate_password, temp_password)
    with transaction.atomic():
        onceki = denetim_izi.anlik(hesap)
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
        denetim_izi.kayit(AuditAction.PAROLA, hesap, onceki=onceki)
    with app_password.dosya_ve_iz_islemi():
        app_password.sarmal_izi(hesap.id)
        app_password.write_account_wrap(
            data_key=dek, hesap_id=hesap.id, tanitici=hesap.login_name, password=parola
        )
    logger.info("Hesabın parolası sıfırlandı (%s).", hesap.login_name)
    return hesap


def unsuspend(*, by_hesap_id: object, hesap_id: object) -> Account:
    """Hesabı askıdan çıkarır: iki kaynak birlikte (plan F1b-1 "Oturum").

    `Account.status = ASKIDA` ise satır `ACIK`'a (geçici parolası değişmemişse
    `PAROLA_YENILENMELI`'ye) döner, askı nedeni silinir, mühür yenilenir (`HESAP` satırı);
    sonra dosyadaki hatalı deneme sayacı ve askısı kaldırılır (arşivlenmez). Askıda
    olmayan hesapta yalnız sayaç sıfırlanır (fikirdeş).

    Hatalı deneme askısı kilitliyken, DEK yokken dosyaya yazılır; o an iz yazılamaz
    (`app_password` modül başlığı). Askının izi kalkarken düşer (burada, parola
    sıfırlamada ve kapamada da): dosyada sayaç ya da askı varsa `guvenlik.json` bölümünün
    `HESAP` satırı önceki değerleri taşır (`hatali`, `askida`; `app_password.sarmal_izi`);
    dosya yazımından önce ve aynı işlemde yazılır.
    """
    dek = _active_data_key()
    _yonetici_aktor(by_hesap_id, dek)
    hesap = _target(hesap_id, dek)
    if hesap.status == AccountStatus.ASKIDA:
        with transaction.atomic():
            onceki = denetim_izi.anlik(hesap)
            hesap.status = (
                AccountStatus.PAROLA_YENILENMELI
                if _needs_password_renewal(hesap)
                else AccountStatus.ACIK
            )
            hesap.suspend_reason = ""
            hesap.seal = hesap.compute_seal(dek)
            hesap.save(update_fields=["status", "suspend_reason", "seal"])
            denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=onceki)
    with app_password.dosya_ve_iz_islemi():
        app_password.sarmal_izi(hesap.id)
        app_password.clear_failed_attempts(hesap.id)
    logger.info("Hesap askıdan çıkarıldı (%s).", hesap.login_name)
    return hesap


def acknowledge_reset_notice(*, hesap_id: object) -> Account:
    """Parola yenilenme bildirimini kapatır: sahibi "Gördüm" dedi (tasarım §4.4.3, tehdit 12).

    Yalnız oturumdaki hesabın KENDİ bildirimi kapanır (çağıran `OTURUM.hesap_id()` verir);
    hesap açık ve mührü tutuyor olmalıdır (`_actor`; mührü tutmayan satıra dokunulmaz). Her
    rolde açıktır: rol sorulmaz (sahibinin kendi bildirimi; tasarım §4.4.3, tehdit 12).
    `reset_notice_pending` mühre girmez: mühür yenilenmez. Satır ve `GUNCELLE` iz satırı
    (`reset_notice_pending: [true, false]`) aynı işlemdedir; yazar istek başındaki bağlamdır
    (oturumdaki hesap). Bildirim beklemiyorsa hiçbir şey yazılmaz (fikirdeş; iz satırı yok).
    `reset_at` ve `reset_kind` kalır: sıfırlamanın ne zaman yapıldığı kayıtta durur.
    """
    dek = _active_data_key()
    hesap = _actor(hesap_id, dek)
    if not hesap.reset_notice_pending:
        return hesap
    with transaction.atomic():
        onceki = denetim_izi.anlik(hesap)
        hesap.reset_notice_pending = False
        hesap.save(update_fields=["reset_notice_pending"])
        denetim_izi.kayit(AuditAction.GUNCELLE, hesap, onceki=onceki)
    logger.info("Parola yenilenme bildirimi görüldü (%s).", hesap.login_name)
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

    `wraps_without_row` yalnız program yöneticisinin onayıyla silinir (`remove_orphan_wraps`).
    `wraps_of_closed`'ı ise program her kilit açılışında kendisi siler (`app_password.
    _cleanup_closed_wraps`; §4.6.1 kural 3'ün "kapalı hesabın sarmalı duruyor" denetimi):
    listede yalnız o silme tamamlanamadıysa (ör. dosyayı başka bir program tuttu) görünür ve
    onayla hemen de silinebilir. Tasarımın kural 4'ü geri yüklemeden sonra bunu da onaya
    bağlıyordu; kural 3'ün kendiliğinden temizliği her açılışta koştuğu için iki kural
    örtüşür, uygulama kural 3'ü izler (Genel Bakış kartının metni bunu söyler).
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


def two_store_differences(
    *, sarmali_yazilacak: frozenset[str] = frozenset()
) -> TwoStoreDifferences:
    """İki deponun farkını hesaplar; HİÇBİR ŞEY yazmaz (kilit açık olmalı: mühür DEK ister).

    `sarmali_yazilacak`: sarmalı çağıranın işleminin sonunda yazılacak hesaplar
    (`reconcile_two_stores`); sarmallı sayılır.
    """
    dek = _active_data_key()
    sarmallar = set(app_password.wrap_ids()) | set(sarmali_yazilacak)
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


def reconcile_two_stores(*, sarmali_yazilacak: frozenset[str] = frozenset()) -> TwoStoreDifferences:
    """Farkı hesaplar ve sarmalı olmayan `ACIK` hesapları `PAROLA_YENILENMELI` yapar.

    Geri yüklemeden sonraki ilk kilit açılışında, geri yükleme notu işlenirken koşar
    (`iz_dogrulama.yaz`, kilit açılışının işleminde). Kurtarma anahtarıyla açılışta
    açılan hesabın sarmalı aynı işlemin SONUNDA yazılır (`sarmali_yazilacak`): o hesap
    sarmallı sayılır, yeni parolasıyla açtığı oturumda parola yenilemeye çekilmez.
    Sarmalı olmayan hesabın sahibi giremez; program yöneticisi geçici parola verir
    (`reset_password` sarmalı kurar). Sarmal silmez: o, listenin Genel Bakış'ta gösterilip
    onaylanmasıyla `remove_orphan_wraps`'tadır (`POST security/integrity/orphan-wraps/`).
    Durum düzeltmesi programın kendi işidir: her hesabın satırı ve `HESAP` satırı tek
    işlemde, yazar `SISTEM` (plan F1b-1 "Denetim izi").
    """
    dek = _active_data_key()
    fark = two_store_differences(sarmali_yazilacak=sarmali_yazilacak)
    for hesap in Account.objects.filter(pk__in=fark.rows_without_wrap, status=AccountStatus.ACIK):
        with sistem_olarak(), transaction.atomic():
            onceki = denetim_izi.anlik(hesap)
            hesap.status = AccountStatus.PAROLA_YENILENMELI
            hesap.seal = hesap.compute_seal(dek)
            hesap.save(update_fields=["status", "seal"])
            denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=onceki)
        logger.info("Sarmalı olmayan hesap parola yenilemeye çekildi (%s).", hesap.login_name)
    return fark


def remove_orphan_wraps(*, by_hesap_id: object, hesap_idler: list[str]) -> list[str]:
    """Program yöneticisinin onayıyla satırsız ya da kapalı hesap sarmallarını siler.

    Yalnız güncel farkta silinebilir görünen kimlikler kabul edilir (onaydan sonra
    durum değiştiyse ret); mührü tutmayan satırın sarmalı asla silinmez. Silme
    `guvenlik.json`'dan ve bütün arşivlerden yapılır. Silinen kimlikleri döndürür.
    Yalnız program yöneticisi (§4.6.1 kural 4; `_yonetici_aktor`).

    Her silinen sarmal için `guvenlik.json` bölümünün `HESAP` satırı dosyadan ÖNCE, aynı
    işlemde yazılır (yazar onaylayan hesap; sarmalda sayaç ya da askı varsa önceki değerleri
    de, `app_password.sarmal_izi`). Ana dosya yazılamazsa işlem geri sarılır;
    sarmal ana dosyadan silinmiş ama bir arşiv kopyası yazılamamışsa iz kalır (sarmal
    artık kilit açmaz), arşivin uyarısı günlüğe düşer.
    """
    dek = _active_data_key()
    _yonetici_aktor(by_hesap_id, dek)
    istenen = {str(h) for h in hesap_idler}
    silinebilir = set(two_store_differences().removable_wraps)
    if not istenen <= silinebilir:
        raise AccountServiceError(_NOT_ORPHAN_MESSAGE)
    if istenen:
        with app_password.dosya_ve_iz_islemi():
            for hesap_id in sorted(istenen):
                app_password.sarmal_izi(hesap_id, silindi=True, her_zaman=True)
            try:
                app_password.remove_account_wraps(istenen)
            except OSError:
                if istenen & set(app_password.wrap_ids()):
                    raise
                logger.warning(
                    "Sahipsiz sarmallar güvenlik dosyasından silindi; bazı arşiv kopyaları "
                    "temizlenemedi.",
                    exc_info=True,
                )
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
