"""Kurum yapılandırması (SchoolConfig singleton) + kurulum sihirbazı kapısı + yol haritası.

Ailenin `school_config` servisinin ikamesi (aile iskeletinden alındı). Farklar: ortam
değişkeni fallback'i YOK — tek doğruluk kaynağı DB satırıdır; `principal_name` Müdür
hesabından değil doğrudan yapılandırmadan gelir (login'siz program).
`setup_completed` yalnız `mark_setup_completed` ile değişir — sihirbaz kapısının
düz alan güncellemesiyle yanlışlıkla açılması/kapanması önlenir.

SİHİRBAZ SIRASI (tasarım §4.4.5, §5.1; plan §2.2) — adım anahtarları API'de ve ön
yüzde aynıdır (`SETUP_STEPS`):

1. `password` — ilk program yöneticisi hesabı + kurtarma anahtarı (atlanamaz;
   adım anahtarı aileden kalır). Adım ancak hesap kurulu VE anahtarın saklandığı
   doğrulanmışsa tamamdır (tasarım
   §4.4.4 `kurtarma.dogrulandi`, §4.4.5): sihirbaz iki grubu istemcide denetler, sonra
   TAM anahtarı `security/recovery-key/confirm/`'a gönderir; sunucu onu kurtarma
   sarmalına karşı doğrulayıp `guvenlik.json`'a damga yazar
   (`app_password.confirm_recovery_key`). Anahtar sunucuda saklanmaz. Damgasız
   tamamlanmış bir kurulum kilitlenmez; yol haritası ve
   Güvenlik ekranı uyarı gösterir (`recovery_key_confirmed`).
2. `school` — okul kartı (tasarım §5.1; plan F1b-4 kararları): okul adı, il, ilçe (resmî
   yazı anteti), kurum kodu, en az bir kademe, öğrenci mevcudu ve tarihi (md. 9/2, 9/6,
   21/3), yerleşim türü (md. 17/1-a-2), kantin işletme biçimi (md. 17/1-a-1, 17/1-b-1,
   23/3), personel çalıştırma biçimi (K3) ve "bu bilgisayar okul demirbaşıdır" onayı
   (Yönerge 11/8, 11/23). Müdür adı, kampüs işareti (md. 2/1, 13/7), açılış tarihi
   (md. 9/1) ve demirbaş no isteğe bağlıdır. Eksik alanlar `missing_school_fields`'tadır;
   kurulumu bu alanlar gelmeden tamamlanmış bir kurulumda kapı yeniden kapanmaz, yol
   haritasının `okul_karti` maddesi eksiği gösterir.
3. `calendar` — aktif ders yılı ve iki dönemi. Kapalı günler bu adımda girilir
   ama tamamlamanın koşulu değildir (yol haritasında ayrı maddedir).

`setup/complete/` eksik adımda Türkçe 400 (`kurulum_eksik`) döner; hangi adımın
neden eksik olduğu iletidedir (`SetupIncomplete`).

`setup_status()` masaüstü sağlık denetiminin de ucudur (`HEALTH_PATH`): hafif
kalır (birkaç sayım sorgusu) ve KİŞİSEL VERİ İÇERMEZ — yalnız bayraklar,
sayılar, okul adı ve yol haritası işaretleri.

Boşta kilit süresi (`SchoolConfig.idle_lock_minutes`) de bu tek satırdadır ama
sihirbaz alanı değildir (`UPDATABLE_FIELDS`'te yoktur): Ayarlar → Güvenlik'teki
ayrı uçtan yazılır (`set_idle_lock_minutes`).

DENETİM İZİ (tasarım §4.6.2, §5.1 "her değişiklik denetim izine düşer"; plan F1b-1 alt
commit c): her yazma servisi satırla AYNI işlemde iz satırı yazar (`_satiri_al` →
yazım → `_izle`). Satır bu işlemde oluşturulduysa `OLUSTUR`, kurulumun tamamlanması
`DURUM`, öteki yazımlar `GUNCELLE`. Değeri satıra giren alanlar modeldedir
(`SchoolConfig.IZ_DEGER_ALANLARI`): okul adı, il, ilçe ve müdür adı yalnız adlarıyla
görünür; okul kartının kod, sayı, tarih ve kademe alanları değerleriyle. Yazar istek
başındaki bağlamdır (oturumdaki hesap).
"""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.okul import denetim_izi, rol_izinleri, selectors
from apps.okul.models import (
    IDLE_LOCK_MINUTES_MAX,
    IDLE_LOCK_MINUTES_MIN,
    INSTITUTION_CODE_LENGTH,
    AuditAction,
    CanteenMode,
    SchoolConfig,
    SchoolLevel,
    SettlementType,
    StaffingMode,
)
from apps.okul.oturum import OTURUM, bosta_suresi_dk
from apps.okul.services import app_password

# Ayar/sihirbaz ekranından güncellenebilir alanlar (whitelist — başka alan yazılamaz).
UPDATABLE_FIELDS: tuple[str, ...] = (
    "school_name",
    "province",
    "district",
    "principal_name",
    "institution_code",
    "levels",
    "student_count",
    "student_count_as_of",
    "settlement_type",
    "canteen_mode",
    "staffing_mode",
    "in_campus",
    "opened_on",
    "demirbas_onayi",
    "demirbas_no",
)

# Sihirbaz adımları, sırasıyla (API ve ön yüz aynı anahtarları kullanır).
STEP_PASSWORD = "password"  # noqa: S105 — adım anahtarı, parola değil
STEP_SCHOOL = "school"
STEP_CALENDAR = "calendar"
SETUP_STEPS: tuple[str, ...] = (STEP_PASSWORD, STEP_SCHOOL, STEP_CALENDAR)


class SetupIncomplete(ValueError):
    """Kurulum tamamlanamaz: en az bir sihirbaz adımı eksik (400 `kurulum_eksik`)."""

    def __init__(self, missing: list[str], message: str) -> None:
        super().__init__(message)
        self.missing = missing


def get_school_config() -> SchoolConfig:
    """Singleton satırı; yoksa kaydedilmemiş varsayılan (okuma DB'ye yazmaz)."""
    return SchoolConfig.load()


def _satiri_al() -> tuple[SchoolConfig, denetim_izi.Anlik | None]:
    """Yazılacak tek satır ve yazmadan önceki hâli (bu işlemde oluşturulduysa None).

    Çağıranın işlemi içinde çağrılır; önceki hâl iz satırının `[önce, sonra]` değerleri
    içindir (modül başlığı "DENETİM İZİ").
    """
    config: SchoolConfig
    config, olustu = SchoolConfig.objects.get_or_create(pk=SchoolConfig.SINGLETON_PK)
    return config, None if olustu else denetim_izi.anlik(config)


def _izle(
    config: SchoolConfig, onceki: denetim_izi.Anlik | None, *, eylem: str = AuditAction.GUNCELLE
) -> None:
    """Yazımın iz satırı (aynı işlemde); satır bu işlemde oluşturulduysa `OLUSTUR`."""
    denetim_izi.kayit(AuditAction.OLUSTUR if onceki is None else eylem, config, onceki=onceki)


@transaction.atomic
def update_school_config(*, fields: dict[str, Any]) -> SchoolConfig:
    """Kurum yapılandırmasını günceller (whitelist alanları). Satır yoksa oluşturur."""
    config, onceki = _satiri_al()
    update_fields: list[str] = ["updated_at"]
    for name in UPDATABLE_FIELDS:
        if name in fields:
            setattr(config, name, fields[name])
            update_fields.append(name)
    config.save(update_fields=update_fields)
    _izle(config, onceki)
    return config


# ---------------------------------------------------------------------------
# Sihirbaz adımları
# ---------------------------------------------------------------------------
def institution_code_valid(code: object) -> bool:
    """Kurum kodu altı ASCII rakam mı? (MEB kurum kodu; yazım denetimi, mevzuat hükmü değil)."""
    return (
        isinstance(code, str)
        and len(code) == INSTITUTION_CODE_LENGTH
        and code.isascii()
        and code.isdigit()
    )


def levels_valid(levels: object) -> bool:
    """Kademeler boş olmayan, yalnız `SchoolLevel` değerlerinden oluşan bir liste mi?"""
    return (
        isinstance(levels, list)
        and bool(levels)
        and all(isinstance(deger, str) and deger in SchoolLevel.values for deger in levels)
    )


def normalize_levels(levels: list[str]) -> list[str]:
    """Kademelerin kanonik biçimi: tekrarsız, `SchoolLevel` sırasıyla (tanınmayan atılır)."""
    secilen = set(levels)
    return [deger for deger in SchoolLevel.values if deger in secilen]


def missing_school_fields(config: SchoolConfig) -> list[str]:
    """2. adımın eksik alanları — kullanıcı diliyle (sözlük), sırasıyla.

    Okul kartının zorunlu alanları (plan F1b-4 kararları "Zorunluluk"): kurum kodu altı
    rakam değilse, kademe listesi boş ya da tanınmayan değer taşıyorsa, mevcut ya da tarihi
    boşsa eksik sayılır. Müdür adı, kampüs işareti ve açılış tarihi isteğe bağlıdır.
    """
    eksik: list[str] = []
    if not config.school_name.strip():
        eksik.append("okul adı")
    if not config.province.strip():
        eksik.append("il")
    if not config.district.strip():
        eksik.append("ilçe")
    if not institution_code_valid(config.institution_code):
        eksik.append("kurum kodu")
    if not levels_valid(config.levels):
        eksik.append("kademe")
    if config.student_count is None or config.student_count_as_of is None:
        eksik.append("öğrenci mevcudu")
    if config.settlement_type not in SettlementType.values:
        eksik.append("yerleşim türü")
    if config.canteen_mode not in CanteenMode.values:
        eksik.append("kantin işletme biçimi")
    if config.staffing_mode not in StaffingMode.values:
        eksik.append("personel çalıştırma biçimi")
    if not config.demirbas_onayi:
        eksik.append("“Bu bilgisayar okul demirbaşıdır” onayı")
    return eksik


def _active_year_summary() -> dict[str, Any] | None:
    """Aktif ders yılının özeti (kişisel veri yok); yoksa None."""
    yil = selectors.active_school_year()
    if yil is None:
        return None
    siralar = set(selectors.school_terms(school_year_id=yil.pk).values_list("sequence", flat=True))
    return {
        "id": yil.pk,
        "name": yil.name,
        "start_date": yil.start_date.isoformat(),
        "end_date": yil.end_date.isoformat(),
        # İki dönem de tanımlı mı? (dönem bazlı raporlar ve tarih → dönem çözümü)
        "terms_ready": siralar == {1, 2},
    }


_HESAPLA: Any = object()  # "çağıran vermedi, burada hesapla" işareti (None geçerli bir değerdir)


def missing_setup_steps(
    *,
    config: SchoolConfig | None = None,
    active_year: Any = _HESAPLA,
    password_set: bool | None = None,
    recovery_confirmed: bool | None = None,
) -> list[str]:
    """Eksik sihirbaz adımları (`SETUP_STEPS` sırasıyla); hepsi tamamsa boş liste.

    1. adım parola kurulu değilse YA DA kurtarma anahtarı doğrulanmamışsa
    eksiktir. `setup_status` zaten okuduğu değerleri geçirir (sağlık denetimi
    ucu hafif kalsın diye aynı sorgu iki kez koşmaz); verilmeyenler burada okunur.
    """
    config = config if config is not None else get_school_config()
    if active_year is _HESAPLA:
        active_year = _active_year_summary()
    if password_set is None:
        password_set = app_password.is_password_set()
    if recovery_confirmed is None:
        recovery_confirmed = password_set and app_password.recovery_key_confirmed()
    eksik: list[str] = []
    if not password_set or not recovery_confirmed:
        eksik.append(STEP_PASSWORD)
    if missing_school_fields(config):
        eksik.append(STEP_SCHOOL)
    if active_year is None or not active_year["terms_ready"]:
        eksik.append(STEP_CALENDAR)
    return eksik


def setup_incomplete_message(missing: list[str], *, config: SchoolConfig) -> str:
    """`setup/complete/` ret iletisi: hangi adım neden eksik (Türkçe, iç kod yok)."""
    parcalar: list[str] = []
    if STEP_PASSWORD in missing:
        if app_password.is_password_set():
            parcalar.append(
                "1. adım (program yöneticisi hesabı): kurtarma anahtarı doğrulanmadı. Anahtarı "
                "sakladıktan sonra istenen iki grubunu yazarak doğrulayın; kaydedemediyseniz "
                "yenisini üretin."
            )
        else:
            parcalar.append("1. adım (program yöneticisi hesabı): hesap kurulmadı.")
    if STEP_SCHOOL in missing:
        alanlar = ", ".join(missing_school_fields(config))
        parcalar.append(f"2. adım (okul bilgileri): {alanlar} eksik.")
    if STEP_CALENDAR in missing:
        parcalar.append(
            "3. adım (ders yılı): aktif bir ders yılı ve iki dönemin tarihleri tanımlanmalı."
        )
    return "Kurulum tamamlanamadı. " + " ".join(parcalar)


@transaction.atomic
def mark_setup_completed() -> SchoolConfig:
    """Kurulum sihirbazını tamamlanmış işaretler; eksik adımda `SetupIncomplete`.

    Kapı sunucudadır: ön yüzün adım kapıları atlanarak (ör. doğrudan istekle)
    parolasız ya da demirbaş onaysız bir kurulum tamamlanamaz.
    """
    config, onceki = _satiri_al()
    eksik = missing_setup_steps(config=config)
    if eksik:
        raise SetupIncomplete(eksik, setup_incomplete_message(eksik, config=config))
    config.setup_completed = True
    config.save(update_fields=["setup_completed", "updated_at"])
    _izle(config, onceki, eylem=AuditAction.DURUM)
    return config


# ---------------------------------------------------------------------------
# Başlangıç Yol Haritası (Genel Bakış kartı)
# ---------------------------------------------------------------------------
# Kendiliğinden tespit edilen maddeler ön yüzde `setup_status` sayılarından
# okunur (personel sayısı, aktif ders yılındaki öğrenciye kapalı gün sayısı; öğrenci
# aktarımı maddesi F1b 5. adımda öğrenci tarafıyla kalktı, veli listesi dönemlik olduğu için
# madde olmaz — plan "F1b-5 uygulama kararları"). Burada yalnız KULLANICININ İŞARETLEDİĞİ maddeler tutulur: program
# bunların yapıldığını bilemez (ör. zarfın kapatılması). OAB'nin maddeleri
# F1b/F1c'de eklenir (plan §2.2; genel tasarım §7.10).
#
# Aileden gelen "parola_paylasimi" maddesi ("yönetici parolasını iki kişiyle
# paylaş") kaldırıldı: parola paylaşılmaz (BSG Yönergesi md. 7/2); kişisel
# hesaplar T1 ile F1b 1. adımda gelir. Önceden kaydedilmiş işareti bilinmeyen
# anahtar gibi yok sayılır (`_stored_roadmap` yalnız bu listedekileri okur) ve
# ilk yazmada kayıttan düşer.
ROADMAP_MANUAL_ITEMS: tuple[str, ...] = (
    "kurtarma_zarfi",  # kurtarma anahtarını müdürlükte kapalı zarfta sakla
)

_ROADMAP_MARKS = "isaretler"
_ROADMAP_HIDDEN = "gizli"


class RoadmapError(ValueError):
    """Yol haritası isteği geçersiz (Türkçe ileti; 400)."""


def _stored_roadmap(config: SchoolConfig) -> dict[str, Any]:
    """SAKLANAN işaretlerin arındırılmış hâli — bilinmeyen anahtar dışarı çıkmaz.

    Yazma yolları (işaretleme, gizleme) bunu kullanır: kullanıcının "gizle"
    tercihi `roadmap_state`'in kapısı yüzünden sessizce silinmesin.
    """
    ham: Any = config.yol_haritasi if isinstance(config.yol_haritasi, dict) else {}
    isaretler: Any = ham.get(_ROADMAP_MARKS)
    isaretler = isaretler if isinstance(isaretler, dict) else {}
    return {
        "marks": {
            madde: str(isaretler[madde])
            for madde in ROADMAP_MANUAL_ITEMS
            if isinstance(isaretler.get(madde), str) and isaretler[madde]
        },
        "hidden": bool(ham.get(_ROADMAP_HIDDEN, False)),
    }


def roadmap_state(
    config: SchoolConfig,
    *,
    recovery_confirmed: bool | None = None,
    school_info_complete: bool | None = None,
) -> dict[str, Any]:
    """Arayüzün gördüğü yol haritası durumu (saklanan işaretler + gizleme kapısı).

    Kurtarma anahtarının saklandığı doğrulanmamışsa kart GİZLİ KALAMAZ (`hidden`
    yanlış döner): "kurtarma anahtarı doğrulanmadı" uyarısı kartın içindedir ve
    Genel Bakış kartı basmazsa uyarı hiç görünmezdi — kartı geri getirecek bir
    arayüz yolu da yoktur (işaret kutuları ve gizleme düğmesi kartın içindedir).
    Bu, var olan "eksik madde varken kart gizli kalmaz" kuralının damgaya
    uygulanmasıdır; SAKLANAN tercih değişmez, damga gelince kart yine gizlenir.

    Okul kartının zorunlu alanları eksikken de kart gizli kalamaz (aynı kural, `okul_karti`
    maddesine): kurulumu okul kartının OAB alanlarından önce tamamlanmış ve kartı gizlemiş bir
    kurulumda göç 0013'ten sonra bu alanlar boştur; kurulum kapısı yeniden kapanmadığı için
    eksiği gösteren tek yer bu karttır (plan F1b-4 kararları; tasarım §7.10).

    `recovery_confirmed` ve `school_info_complete` verilmezse burada okunur; `setup_status`
    zaten bildiği için geçirir (aynı dosya ve hesap iki kez yapılmasın).
    """
    state = _stored_roadmap(config)
    dogrulandi = (
        app_password.recovery_key_confirmed() if recovery_confirmed is None else recovery_confirmed
    )
    okul_karti_tamam = (
        not missing_school_fields(config) if school_info_complete is None else school_info_complete
    )
    state["hidden"] = state["hidden"] and dogrulandi and okul_karti_tamam
    return state


def roadmap_auto_items(status: dict[str, Any]) -> dict[str, bool]:
    """Kendiliğinden tespit edilen maddeler (`setup_status` sayılarından).

    `okul_karti`: okul kartının zorunlu alanları tamam mı (`school_info_complete`). Kurulumu
    okul kartının OAB alanlarından önce tamamlanmış kurulumda bu alanlar boştur; kurulum
    kapısı yeniden kapanmaz, eksik yol haritasında görünür ve kart gizlenemez (plan F1b-4
    kararları; tasarım §7.10 "okul kartının eksik alanları").
    """
    return {
        "okul_karti": bool(status["school_info_complete"]),
        "personel_aktarimi": int(status["personnel_count"]) > 0,
        "kapali_gunler": int(status["school_break_count"]) > 0,
    }


def _save_roadmap(
    config: SchoolConfig, onceki: denetim_izi.Anlik | None, state: dict[str, Any]
) -> None:
    config.yol_haritasi = {_ROADMAP_MARKS: state["marks"], _ROADMAP_HIDDEN: state["hidden"]}
    config.save(update_fields=["yol_haritasi", "updated_at"])
    _izle(config, onceki)


@transaction.atomic
def set_roadmap_mark(item: str, *, done: bool) -> dict[str, Any]:
    """Kullanıcının işaretlediği bir maddeyi işaretler ya da işareti kaldırır."""
    if item not in ROADMAP_MANUAL_ITEMS:
        raise RoadmapError("Bu madde elle işaretlenemez.")
    config, onceki = _satiri_al()
    state = _stored_roadmap(config)
    if done:
        state["marks"][item] = timezone.localdate().isoformat()
    else:
        state["marks"].pop(item, None)
        state["hidden"] = False  # eksik madde varken kart gizli kalmaz
    _save_roadmap(config, onceki, state)
    return roadmap_state(config)


@transaction.atomic
def set_roadmap_hidden(*, hidden: bool) -> dict[str, Any]:
    """Kartı gizler/gösterir. Gizleme yalnız bütün maddeler tamamlanınca yapılır.

    Kurtarma anahtarı doğrulanmamışken gizlenemez: uyarı kartın içindedir.
    Kapı hem burada hem `roadmap_state`'tedir — eski bir kurulumda
    damgasızken kart zaten gizli kaydedilmiş olabilir.
    """
    config, onceki = _satiri_al()
    state = _stored_roadmap(config)
    if hidden:
        durum = setup_status()
        if not durum["recovery_key_confirmed"]:
            raise RoadmapError(
                "Kurtarma anahtarının saklandığı doğrulanmadan başlangıç yol haritası "
                "gizlenemez. Anahtarı Ayarlar → Güvenlik'te doğrulayın."
            )
        otomatik_eksik = [k for k, tamam in roadmap_auto_items(durum).items() if not tamam]
        elle_eksik = [m for m in ROADMAP_MANUAL_ITEMS if m not in state["marks"]]
        if otomatik_eksik or elle_eksik:
            raise RoadmapError("Başlangıç yol haritası bütün maddeler tamamlanınca gizlenebilir.")
    state["hidden"] = hidden
    _save_roadmap(config, onceki, state)
    return roadmap_state(config)


# ---------------------------------------------------------------------------
# Boşta kilit süresi (Ayarlar → Güvenlik; tasarım TK14, §13 D11; plan F1b-1 "Oturum")
# ---------------------------------------------------------------------------
IDLE_LOCK_RANGE_MESSAGE = (
    f"Boşta kilit süresi {IDLE_LOCK_MINUTES_MIN} ile {IDLE_LOCK_MINUTES_MAX} dakika "
    "arasında olmalıdır."
)
IDLE_LOCK_SESSION_MESSAGE = "Boşta kilit süresi yalnız açık oturumda değiştirilir."


class IdleLockError(ValueError):
    """Boşta kilit süresi yazılamadı; ileti kullanıcıya olduğu gibi gösterilir (400)."""


def idle_lock_minutes() -> int:
    """Oturumun UYGULADIĞI boşta kilit süresi (dakika; `oturum.bosta_suresi_dk`).

    Ayarın okunduğu tek yerdir: satır yoksa alanın varsayılanı (10), program
    dışından aralık dışına yazılmış değer sınıra çekilmiş hâliyle döner. Ekranda
    görünen süre böylece kilidin gerçekten uyguladığı süredir.
    """
    return bosta_suresi_dk()


def set_idle_lock_minutes(*, dakika: int) -> int:
    """Boşta kilit süresini yazar (3-30 dakika); yeni değeri döndürür.

    Yalnız açık oturumda (kilitliyken uç zaten 423 alır; hesap kurulmadan da ayar
    yazılmaz) ve yalnız program yöneticisi (tasarım §4.4.2 Ayarlar satırı: öteki roller
    okur): rol kapısının ardından servis de isteğin yazarının rolünü yetki kapısına sorar
    (`RolYetkisiz`, 403). Aralık doğrulayıcıları ve veritabanı kısıtı modeldedir; burada da
    denetlenir ki program dışı bir çağrı kısıt hatasına (500) düşmesin. Kayıt
    `post_save` ile oturumun önbelleğini boşaltır (`apps.okul.apps`): yeni süre bir
    sonraki istekte geçerlidir, yeniden başlatma gerekmez. Değişiklik iz satırı yazar
    (`GUNCELLE`; süre izinli kişisiz alandır, `[önce, sonra]` değeriyle).
    """
    if not OTURUM.acik_mi():
        raise IdleLockError(IDLE_LOCK_SESSION_MESSAGE)
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.BOSTA_SURE_YAZMA)
    if (
        isinstance(dakika, bool)
        or not isinstance(dakika, int)
        or not IDLE_LOCK_MINUTES_MIN <= dakika <= IDLE_LOCK_MINUTES_MAX
    ):
        raise IdleLockError(IDLE_LOCK_RANGE_MESSAGE)
    with transaction.atomic():
        config, onceki = _satiri_al()
        config.idle_lock_minutes = dakika
        config.save(update_fields=["idle_lock_minutes", "updated_at"])
        _izle(config, onceki)
    return dakika


# ---------------------------------------------------------------------------
# Durum özeti (sihirbaz + kurulum kapısı + masaüstü sağlık denetimi)
# ---------------------------------------------------------------------------
def setup_status() -> dict[str, Any]:
    """`GET setup/status/` — hafif, KİŞİSEL VERİ İÇERMEZ (modül başlığı).

    Alan kümesi hem ön yüz `SetupStatus` tipinin hem masaüstü sağlık denetiminin
    sözleşmesidir; değişirse ikisi birlikte gözden geçirilir.
    """
    config = get_school_config()
    aktif_yil = _active_year_summary()
    parola_kurulu = app_password.is_password_set()
    anahtar_dogrulandi = parola_kurulu and app_password.recovery_key_confirmed()
    okul_karti_tamam = not missing_school_fields(config)
    return {
        "setup_completed": config.setup_completed,
        "password_set": parola_kurulu,
        # Kurtarma anahtarının saklandığı doğrulandı mı? (1. adımın ikinci koşulu)
        "recovery_key_confirmed": anahtar_dogrulandi,
        "school_name": config.school_name,
        "school_info_complete": okul_karti_tamam,
        "has_active_school_year": aktif_yil is not None,
        "active_school_year": aktif_yil,
        "missing_steps": missing_setup_steps(
            config=config,
            active_year=aktif_yil,
            password_set=parola_kurulu,
            recovery_confirmed=anahtar_dogrulandi,
        ),
        "personnel_count": selectors.personnel_count(),
        "school_break_count": selectors.school_break_count(
            start=aktif_yil["start_date"] if aktif_yil else None,
            end=aktif_yil["end_date"] if aktif_yil else None,
        ),
        "roadmap": roadmap_state(
            config, recovery_confirmed=anahtar_dogrulandi, school_info_complete=okul_karti_tamam
        ),
    }


def get_letterhead_identity() -> dict[str, str]:
    """Resmî evrak antedi için kurum kimliği.

    Döner: `school_name`, `district`, `province`, `principal_name` — hepsi düz
    metin. Okul adı boşsa aile kalıbıyla 'Okul' yer tutucusu; ilçe/müdür boş
    kalabilir (antet şablonu yer tutucu basar).
    """
    config = get_school_config()
    return {
        "school_name": config.school_name.strip() or "Okul",
        "district": config.district.strip(),
        "province": config.province.strip(),
        "principal_name": config.principal_name.strip(),
    }
