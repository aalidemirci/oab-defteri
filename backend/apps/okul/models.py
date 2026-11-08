"""`okul` modelleri — kurum künyesi, ders yılı/dönemler, kapalı günler, personel sicili, içe aktarma.

Aile iskeletinden alındı (iskelet bunu atalarının `apps/okul/models.py`
kalıbından türetip sadeleştirmişti). OAB'deki yeri ve değişecek alanları OAB
tasarımının §5.1 ve §12.B'sindedir (okul kartının OAB alanları F1b 4. adımda girdi,
kütüphane saatleri ve kısa ad aynı adımda düştü; öğrenci sicili, şube kataloğu ve hazırlık
sınıfı bayrağı F1b 5. adımda düştü — tasarım §5.1 ALMA, T5):

- `SchoolConfig`: okul kartı — kurum künyesi, kademeler, öğrenci mevcudu, yerleşim türü,
  kantin ve personel çalıştırma biçimi, kampüs, açılış tarihi, demirbaş onayı (sınıf yorumu).

- `ParentRoster`: veli listesi (T5; F1b 5. adım) — bir satır bir öğrenci: şifreli veli adı,
  adın kör indeksi, öğrencinin sınıfı (düz metin), aktarım partisi (sınıf yorumu).
- `Personnel`: aile kalıbı + `is_active` + şifreli ad-soyad + `member_kind` +
  ayrılış tarihi. Unvan ve branş YOKTUR (tasarım §8.4; branş, küçük okulda
  öğretmeni kişiye bağlar).
- AYRILIŞ HAVUZU (aile iskeletinin kararı; OAB'de tasarım §5.1 `Personnel`): `Personnel`
  `leave_candidate_since` + `leave_candidate_run` taşır. e-Okul
  aktarımında listede bulunmayan AKTİF kişi havuza girer, durumu aktif kalır;
  karar yöneticinindir (`services.persons`). Havuzdaki kişi DB kısıtıyla
  aktiftir: ayrılış havuz alanlarını aynı kayıtta temizler.
- `Holiday`: aile iskeletinden AYNEN (tasarım §5.1) — `SCHOOL_BREAK` türüyle
  ("öğrenciye kapalı gün"); kapalı gün aritmetiğinin veri kaynağıdır
  (`shared.working_days`; OAB'de iş günü hesabı, tasarım §5.1).
- Koşullu UniqueConstraint'ler SQLite partial index ile çalışır (ailede kanıtlı).
- Güvenlik çekirdeği (tasarım §4.6, F1b-1): `Account`, `AuditKey`, `AuditTrail` ve
  `AccessLog` (erişim günlüğü; zincir dışı, değer tutmaz, 2 yıl saklanır).
- `Attachment` (tasarım §5.2.8, TK22; plan F1b-3 "Sapma"): dosya deposundaki ekin satırı. Tasarım
  onu OAB modelleri arasında sayar; `apps/oab` F1c'de doğar, bağımlılık yönü oab'den okula kalır.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, ClassVar

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Length
from django.db.models.lookups import Exact
from django.utils import timezone

from apps.okul.name_match import name_key
from shared import kanonik
from shared.crypto import (
    EncryptedCharField,
    EncryptedTextField,
    account_seal_key,
    blind_index,
    is_corrupt,
)
from shared.models import BaseModel


class SchoolLevel(models.TextChoices):
    """Okulun kademesi (tasarım §3.5, §5.1 `levels`) — `SchoolConfig.levels`'in değer kümesi.

    OAB'de kademe kural paketinin koşuluna (kesişimle, tasarım §6.1), kursiyer türünün
    görünürlüğüne (md. 4/1-ğ, 7/1) ve temsilci kurullarına girer (tasarım §5.1). Birden çok
    kademeli kurum birden çok değer seçer; "karma" ayrı değer değildir, yaygın eğitim
    seçeneği yoktur (tasarım §3.5). Sıra kanoniktir: `levels` bu sırayla saklanır. Kademe
    sınıf seviyelerini KISITLAMAZ (1-12 okul içi sabit kalır).
    """

    OKUL_ONCESI = "OKUL_ONCESI", "Okul öncesi"
    ILKOKUL = "ILKOKUL", "İlkokul"
    ORTAOKUL = "ORTAOKUL", "Ortaokul"
    ORTAOGRETIM = "ORTAOGRETIM", "Ortaöğretim (lise)"


class SettlementType(models.TextChoices):
    """Okulun bulunduğu yerleşimin türü (tasarım §5.1 `settlement_type`).

    Kantin gelirinin pay dağılımı buna göre yapılır: büyükşehir statüsünde olmayan il
    merkezinde ilçe payı yoktur, pay il millî eğitim müdürlüğüne gider (md. 17/1-a-2; oranlar
    kural paketinde, F1c). Değer adları kural paketinin `okul.yerlesim_turu` koşuludur (tasarım §6.1).
    """

    BUYUKSEHIR = "BUYUKSEHIR", "Büyükşehir statüsündeki il"
    IL_MERKEZI_BUYUKSEHIR_DEGIL = (
        "IL_MERKEZI_BUYUKSEHIR_DEGIL",
        "Büyükşehir statüsünde olmayan il merkezi",
    )
    DIGER = "DIGER", "Büyükşehir statüsünde olmayan ilde, il merkezi dışında"


class CanteenMode(models.TextChoices):
    """Kantin ve benzeri yerlerin işletme biçimi (tasarım §5.1 `canteen_mode`).

    Arz bedeli kiraya verilen yerde kiracıdan (md. 17/1-a-1), birlikçe işletilen yerde
    birlikten (md. 17/1-b-1) hesaplanır; birlikçe işletmede vergi mükellefiyeti doğarsa
    Vergi Usul Kanunu hükümleri uygulanır (md. 23/3; okul kartında bilgi bandı).
    """

    KIRAYA_VERILIYOR = "KIRAYA_VERILIYOR", "Kiraya veriliyor"
    BIRLIKCE_ISLETILIYOR = "BIRLIKCE_ISLETILIYOR", "Birlikçe işletiliyor"
    KANTIN_YOK = "KANTIN_YOK", "Kantin ve benzeri yer yok"


class StaffingMode(models.TextChoices):
    """Birliğin personel çalıştırma biçimi (tasarım §5.1 `staffing_mode`; K3).

    Personel modülü (sürüm 2) yalnız doğrudan işverende açılır; birliğin istihdam ettiği
    personel için kıdem tazminatı karşılığı ayrılır (md. 6/1-d). Hizmet alımı harcama
    zincirinden geçer (tasarım §7.4).
    """

    DOGRUDAN_ISVEREN = "DOGRUDAN_ISVEREN", "Birlik doğrudan işveren"
    HIZMET_ALIMI = "HIZMET_ALIMI", "Hizmet alımıyla"
    CALISTIRMIYOR = "CALISTIRMIYOR", "Personel çalıştırmıyor"


#: Öğrenci mevcudunun üst sınırı (yazım denetimi; mevzuat hükmü değildir).
STUDENT_COUNT_MAX = 99999
#: Kurum kodunun hane sayısı (MEB kurum kodu; kullanıcı bilgisi, plan F1b-4 kararları).
INSTITUTION_CODE_LENGTH = 6
#: Veri sorumlusu metninin üst sınırı (karakter; ad, adres ve iletişim bir paragrafa sığar —
#: yazım denetimi, mevzuat hükmü değildir).
DATA_CONTROLLER_TEXT_MAX = 500


#: Boşta kilit süresi (dakika; tasarım TK14, §15 M-3): varsayılan 10, ayar 3-30. Alanın
#: kendi varsayılanıdır; oturum katmanı satır yokken de bunu kullanır (aile iskeletinin
#: 3 dk'lık varsayılanına sessiz düşüş yoktur, tasarım §13 D11).
IDLE_LOCK_MINUTES_DEFAULT = 10
IDLE_LOCK_MINUTES_MIN = 3
IDLE_LOCK_MINUTES_MAX = 30


class SchoolConfig(BaseModel):
    """Kurum bilgisi — TEK satır (singleton, pk=1).

    Kurulum sihirbazı doldurur; evrak antedi (okul adı/ilçe/müdür) buradan
    çözülür. `setup_completed` sihirbaz kapısıdır.

    `app_password_hash` (aile kalıbı; tasarım §4.4.4): adı tarihsel — içeriği
    parolanın özeti DEĞİLDİR; veri anahtarının (DEK) tek yönlü parmak izini
    tutar (`shared.crypto.key_fingerprint`). Parola/tuz/sarmal `guvenlik.json`
    dosyasındadır; DB ile güvenlik dosyasının eşleşmesi bu damgayla denetlenir
    ve alan şifreleme geçişi bu alanla AYNI işlemde damgalanır.

    OKUL KARTI (sihirbazın 2. adımı ve Ayarlar → Okul Bilgileri; tasarım §5.1 "`SchoolConfig`'e
    eklenen OAB alanları", plan F1b-4 kararları). Hiçbiri kişisel veri değildir, şifrelenmez:

    - `school_name`, `province`, `district` (resmî yazı anteti), `principal_name` (isteğe bağlı).
    - `institution_code`: MEB kurum kodu, boş ya da altı rakam (yazım denetimi; mevzuat değil).
    - `levels`: kademeler — `SchoolLevel` değerlerinin tekrarsız listesi, `SchoolLevel`
      sırasıyla (serileştirici normalleştirir). SQLite'ta JSON listesine DB kısıtı yazılamaz:
      doğrulama serileştiricide ve `services.setup.missing_school_fields`'tadır.
    - `student_count` + `student_count_as_of`: öğrenci mevcudu ve sayının alındığı gün; genel
      kurul yeter sayısı (md. 9/2, 9/6) ve kantin kirasının yeniden tespiti (md. 21/3). İkisi
      birlikte dolu ya da birlikte boştur (DB kısıtı).
    - `settlement_type`: yerleşim türü, pay dağılımı (md. 17/1-a-2).
    - `canteen_mode`: kantin işletme biçimi, arz bedeli (md. 17/1-a-1, 17/1-b-1) ve md. 23/3.
    - `staffing_mode`: personel çalıştırma biçimi (K3; kıdem karşılığı md. 6/1-d).
    - `in_campus`: okul eğitim kampüsünde (md. 2/1; kampüs yönetimine temsilci md. 13/7).
    - `opened_on`: yeni açılan okulun açılış tarihi; ilk genel kurul bundan sayılır (md. 9/1).
      Çoğu okulda boştur, boşaltılabilir.
    - `demirbas_onayi` + `demirbas_no` (Bilgi ve Sistem Güvenliği Yönergesi 11/8, 11/23:
      program yalnız kurum demirbaşı bilgisayara kurulur).
    - `data_controller_text`: veri sorumlusu ve iletişim bilgisi (serbest metin, isteğe bağlı;
      tasarım §5.1, E04; KVKK md. 10/1-a "veri sorumlusunun kimliği"). Personel ve veli listesi
      aktarım ekranlarının aydınlatma metni buradan dolar; boşken ekran uyarır, aktarımı
      engellemez (plan "F1b-5 uygulama kararları"). Kurulumun zorunlu alanı DEĞİLDİR
      (`services.setup.missing_school_fields`).

    Enum alanlarında boş değer "henüz seçilmedi"dir (kurulum tamamlanamaz). Bir kez girilen
    zorunlu alan sonradan boşaltılamaz (serileştirici; aile kuralı, tasarım §5.1).

    `idle_lock_minutes`: oturumun boşta kilit süresi (dakika; tasarım TK14, plan F1b-1
    "Oturum"). Ayarlar → Güvenlik'te program yöneticisi değiştirir (uç
    `security/idle-lock/`, servis `services.setup.set_idle_lock_minutes`; her rol okur,
    yalnız program yöneticisi yazar). Oturum katmanı değeri süreç içinde önbelleğe alır; satır
    kaydedilince önbellek boşalır (`apps.okul.oturum.bosta_suresi_onbellegini_bosalt`).

    `yol_haritasi`: Genel Bakış'taki "Başlangıç Yol Haritası" kartının
    KULLANICININ İŞARETLEDİĞİ maddeleri (`{"isaretler": {madde: "gg-aa-yyyy"
    ISO tarih}, "gizli": bool}`; biçim `services.setup` tek kaynağındadır).
    Tarayıcı depolaması yerine burada durur: yönetim yüzeyi her açılışta
    RASTGELE portta dinler, köken (origin) değiştiği için `localStorage`
    açılışlar arasında taşınmaz; pencere profili de silinebilir önbellektedir.
    Kişisel veri İÇERMEZ (madde anahtarı + tarih).

    DENETİM İZİ (tasarım §4.6.2, §5.1 "her değişiklik denetim izine düşer"): her yazma
    servisi (`services.setup`, ilk hesabın parmak izi `app_password.enable`) iz satırı
    yazar (`apps.okul.denetim_izi`). `IZ_DEGER_ALANLARI` önce/sonra değeri satıra giren
    kişisiz alanlardır (sayı, kod, durum, numara, tarih; kademeler kod listesi); okul adı,
    il, ilçe ve veri sorumlusu serbest metindir, müdür adı kişi adıdır, parmak izi güvenlik
    öğesidir, yol haritası JSON'dur: satıra yalnız adları girer. İçerik MAC'i kimlik dışındaki bütün
    alanları kapsar (`IZ_OZET_ALANLARI`; KVKK silme kümesinde alan yok).
    """

    SINGLETON_PK = 1

    #: Denetim izinde önce/sonra değeri yazılabilen kişisiz alanlar (tasarım §4.6.2, §5 O4).
    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
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
        "setup_completed",
        "idle_lock_minutes",
        "deleted_at",
    )
    #: Durum alanları (`denetim_izi.degisiklik`: değişimleri ayrı `DURUM` satırıdır, §4.6.2
    #: kural 3). Bugünkü yazımlar türü açıkça verir (kurulumun tamamlanması `DURUM`).
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("setup_completed", "deleted_at")
    #: İçerik MAC'ine giren alanlar (kimlik hariç; tasarım §4.6.2 "kaydın özeti").
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "updated_at",
        "deleted_at",
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
        "data_controller_text",
        "yol_haritasi",
        "setup_completed",
        "app_password_hash",
        "idle_lock_minutes",
    )

    school_name = models.CharField("okul adı", max_length=255, blank=True, default="")
    province = models.CharField("il", max_length=64, blank=True, default="")
    district = models.CharField("ilçe", max_length=64, blank=True, default="")
    principal_name = models.CharField("müdür adı", max_length=128, blank=True, default="")
    institution_code = models.CharField(
        "kurum kodu", max_length=INSTITUTION_CODE_LENGTH, blank=True, default=""
    )
    levels = models.JSONField("kademeler", default=list, blank=True)
    student_count = models.PositiveIntegerField(
        "öğrenci mevcudu",
        null=True,
        blank=True,
        validators=[MaxValueValidator(STUDENT_COUNT_MAX)],
    )
    student_count_as_of = models.DateField("mevcudun tarihi", null=True, blank=True)
    settlement_type = models.CharField(
        "yerleşim türü", max_length=32, choices=SettlementType.choices, blank=True, default=""
    )
    canteen_mode = models.CharField(
        "kantin işletme biçimi",
        max_length=32,
        choices=CanteenMode.choices,
        blank=True,
        default="",
    )
    staffing_mode = models.CharField(
        "personel çalıştırma biçimi",
        max_length=32,
        choices=StaffingMode.choices,
        blank=True,
        default="",
    )
    in_campus = models.BooleanField("eğitim kampüsünde", default=False)
    opened_on = models.DateField("okulun açılış tarihi", null=True, blank=True)
    demirbas_onayi = models.BooleanField("bilgisayar okul demirbaşıdır", default=False)
    demirbas_no = models.CharField(
        "bilgisayarın demirbaş no'su", max_length=64, blank=True, default=""
    )
    data_controller_text = models.CharField(
        "veri sorumlusu", max_length=DATA_CONTROLLER_TEXT_MAX, blank=True, default=""
    )
    yol_haritasi = models.JSONField("başlangıç yol haritası işaretleri", default=dict, blank=True)
    setup_completed = models.BooleanField("kurulum tamamlandı", default=False)
    app_password_hash = models.CharField(
        "veri anahtarı parmak izi", max_length=255, blank=True, default=""
    )
    idle_lock_minutes = models.PositiveSmallIntegerField(
        "boşta kilit süresi (dakika)",
        default=IDLE_LOCK_MINUTES_DEFAULT,
        validators=[
            MinValueValidator(IDLE_LOCK_MINUTES_MIN),
            MaxValueValidator(IDLE_LOCK_MINUTES_MAX),
        ],
    )

    class Meta:
        verbose_name = "kurum yapılandırması"
        verbose_name_plural = "kurum yapılandırması"
        constraints = [
            # Enum alanlarında boş = sihirbazda henüz seçilmedi (kurulum tamamlanamaz).
            models.CheckConstraint(
                condition=models.Q(settlement_type__in=[*SettlementType.values, ""]),
                name="ck_schoolconfig_settlement_type",
            ),
            models.CheckConstraint(
                condition=models.Q(canteen_mode__in=[*CanteenMode.values, ""]),
                name="ck_schoolconfig_canteen_mode",
            ),
            models.CheckConstraint(
                condition=models.Q(staffing_mode__in=[*StaffingMode.values, ""]),
                name="ck_schoolconfig_staffing_mode",
            ),
            # Mevcut tarihsiz, tarih mevcutsuz anlamsızdır: ikisi birlikte dolu ya da boş.
            models.CheckConstraint(
                condition=(
                    models.Q(student_count__isnull=True, student_count_as_of__isnull=True)
                    | models.Q(student_count__isnull=False, student_count_as_of__isnull=False)
                ),
                name="ck_schoolconfig_student_count_pair",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(student_count__isnull=True)
                    | models.Q(student_count__lte=STUDENT_COUNT_MAX)
                ),
                name="ck_schoolconfig_student_count_max",
            ),
            # Kurum kodu boş ya da altı hane (rakam denetimi serileştiricide).
            models.CheckConstraint(
                condition=(
                    models.Q(institution_code="")
                    | models.Q(Exact(Length("institution_code"), INSTITUTION_CODE_LENGTH))
                ),
                name="ck_schoolconfig_institution_code",
            ),
            # Aralık doğrulayıcılarla aynı; program dışından yazılan değer de reddedilir.
            models.CheckConstraint(
                condition=models.Q(
                    idle_lock_minutes__gte=IDLE_LOCK_MINUTES_MIN,
                    idle_lock_minutes__lte=IDLE_LOCK_MINUTES_MAX,
                ),
                name="ck_schoolconfig_idle_lock_minutes",
            ),
        ]

    def __str__(self) -> str:
        return self.school_name or "Kurulmamış okul"

    @classmethod
    def load(cls) -> SchoolConfig:
        """Singleton satırı döndürür; yoksa KAYDEDİLMEMİŞ varsayılan (okuma yazmaz)."""
        instance: SchoolConfig | None = cls.objects.filter(pk=cls.SINGLETON_PK).first()
        return instance if instance is not None else cls(pk=None)


class SchoolYear(BaseModel):
    """Ders yılı (örn. '2026-2027'). Tek-aktif kuralı hem serviste hem DB kısıtında.

    DENETİM İZİ (tasarım §4.6.2; plan F1b-1 alt commit c): her yazma servisi
    (`services.school_year`) iz satırı yazar. Ad elle yazılan metindir (biçimi
    denetlenmez): satıra yalnız alan adı girer; tarihler ve aktiflik değerleriyle.
    Aktifleştirme ve yumuşak silme durum geçişidir (`DURUM`).
    """

    #: Denetim izinde önce/sonra değeri yazılabilen kişisiz alanlar (tasarım §4.6.2).
    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "start_date",
        "end_date",
        "is_active",
        "deleted_at",
    )
    #: İçerik MAC'ine giren alanlar (kimlik hariç bütün alanlar).
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "updated_at",
        "deleted_at",
        "name",
        "start_date",
        "end_date",
        "is_active",
    )
    #: Durum alanları: değişimleri ayrı `DURUM` satırıdır (§4.6.2 kural 3).
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("is_active", "deleted_at")

    name = models.CharField("ad", max_length=32)
    start_date = models.DateField("başlangıç")
    end_date = models.DateField("bitiş")
    is_active = models.BooleanField("aktif", default=False)

    class Meta:
        verbose_name = "ders yılı"
        verbose_name_plural = "ders yılları"
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_schoolyear_name_alive",
            ),
            # Savunma hattı: aktif yıl değişimi serviste "önce eskisini kapat"
            # sırasıyla yapılır; kısıt yarış/hata durumunda ikinci aktifi keser.
            models.UniqueConstraint(
                fields=["is_active"],
                condition=models.Q(is_active=True, deleted_at__isnull=True),
                name="uq_schoolyear_single_active",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class SchoolTerm(BaseModel):
    """Ders yılının iki dönemi — dönem bazlı raporlar ve tarih → dönem çözümü buna bağlanır.

    DENETİM İZİ: `services.terms` her dönemin oluşturulmasını ve tarih değişikliğini
    izler; bütün alanlar kişisizdir (ders yılı kimliği, sıra, tarihler).
    """

    #: Denetim izinde önce/sonra değeri yazılabilen kişisiz alanlar (tasarım §4.6.2).
    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "school_year",
        "sequence",
        "start_date",
        "end_date",
        "deleted_at",
    )
    #: İçerik MAC'ine giren alanlar (kimlik hariç bütün alanlar).
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "updated_at",
        "deleted_at",
        "school_year",
        "sequence",
        "start_date",
        "end_date",
    )
    #: Durum alanları: değişimleri ayrı `DURUM` satırıdır (§4.6.2 kural 3).
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("deleted_at",)

    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name="terms",
        verbose_name="ders yılı",
    )
    sequence = models.PositiveSmallIntegerField("dönem", choices=((1, "1. dönem"), (2, "2. dönem")))
    start_date = models.DateField("başlangıç")
    end_date = models.DateField("bitiş")

    class Meta:
        verbose_name = "ders dönemi"
        verbose_name_plural = "ders dönemleri"
        ordering = ["school_year", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["school_year", "sequence"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_schoolterm_year_sequence_alive",
            ),
            models.CheckConstraint(
                condition=models.Q(sequence__in=(1, 2)),
                name="ck_schoolterm_sequence",
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="ck_schoolterm_date_order",
            ),
        ]
        indexes = [
            models.Index(fields=["school_year", "start_date"], name="schoolterm_year_start_idx"),
        ]

    @property
    def name(self) -> str:
        return f"{self.sequence}. dönem"

    def __str__(self) -> str:
        return f"{self.school_year.name} · {self.name}"


class HolidayKind(models.TextChoices):
    """Kapalı gün türü — ailenin `HolidayKind`'ı + `SCHOOL_BREAK` (tasarım §5.1 `Holiday`).

    Kapalı gün aritmetiğinde türler İKİ ayrı kurala ayrılır; dayanakları farklıdır
    (`shared.working_days` modül yorumu):

    - `OFFICIAL`, `RELIGIOUS`, `OTHER` her zaman kapalıdır (hafta sonu gibi).
    - `SCHOOL_BREAK` ("öğrenciye kapalı gün": ara tatil, yarıyıl) hesaba girip
      girmeyeceğini çağıran seçer
      (`include_school_breaks`). Ayrı türle tutulur ki yarıyıl tatili resmî
      tatilden ayrılabilsin (tasarım §5.1: `SCHOOL_BREAK` yarıyıl tatilini tanır).
    """

    OFFICIAL = "OFFICIAL", "Resmî tatil"
    RELIGIOUS = "RELIGIOUS", "Dini bayram"
    SCHOOL_BREAK = "SCHOOL_BREAK", "Öğrenciye kapalı gün"
    OTHER = "OTHER", "İdari izin / diğer"


class Holiday(BaseModel):
    """Kapalı gün aralığı (aile iskeletinden AYNEN; tasarım §5.1).

    Ders yılına BAĞLANMAZ (aile kalıbı): kapalı gün sorusu tarih kapsamasıyla
    cevaplanır. Tek günlük kayıtta başlangıç ve bitiş aynı gündür.

    `is_estimated`: hicri takvime bağlı dini bayramlar Diyanet takvimi
    kesinleşmeden önce TAHMİNİDİR (2027 ve sonrası); arayüz "tahmini" rozetiyle
    gösterir. Yalnız tohumlama yazar; elle girilen kayıt kesin tarih sayılır.

    DENETİM İZİ: `services.calendar` tohumlamayı, elle eklemeyi ve yumuşak silmeyi
    (`DURUM`, `deleted_at`) izler. Ad serbest metindir (elle girilen "idari izin"
    gerekçesi kişi adı taşıyabilir): satıra yalnız alan adı girer.
    """

    #: Denetim izinde önce/sonra değeri yazılabilen kişisiz alanlar (tasarım §4.6.2).
    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "start_date",
        "end_date",
        "kind",
        "is_estimated",
        "deleted_at",
    )
    #: İçerik MAC'ine giren alanlar (kimlik hariç bütün alanlar).
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "updated_at",
        "deleted_at",
        "name",
        "start_date",
        "end_date",
        "kind",
        "is_estimated",
    )
    #: Durum alanları: değişimleri ayrı `DURUM` satırıdır (§4.6.2 kural 3).
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("deleted_at",)

    name = models.CharField("ad", max_length=128)
    start_date = models.DateField("başlangıç", db_index=True)
    end_date = models.DateField("bitiş")
    kind = models.CharField(
        "tür", max_length=16, choices=HolidayKind.choices, default=HolidayKind.OFFICIAL
    )
    is_estimated = models.BooleanField("tahmini", default=False)

    class Meta:
        verbose_name = "kapalı gün"
        verbose_name_plural = "kapalı günler"
        ordering = ["start_date", "end_date", "pk"]
        constraints = [
            # Tohumlama fikirdeşliğinin DB sigortası: aynı (ad, başlangıç) canlı satır tekil.
            models.UniqueConstraint(
                fields=["name", "start_date"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_holiday_name_start_alive",
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="ck_holiday_date_order",
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=HolidayKind.values),
                name="ck_holiday_kind",
            ),
            # "Tahmini" yalnız hicri takvime bağlı dini bayramda anlamlıdır.
            models.CheckConstraint(
                condition=models.Q(is_estimated=False) | models.Q(kind=HolidayKind.RELIGIOUS),
                name="ck_holiday_estimated_religious",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.start_date})"


class MemberKind(models.TextChoices):
    """Personelin görev türü (sözlük: ekran adı "Görev türü"; "öğretmen" · "yönetici" ·
    "diğer personel").

    Tasarım §5.1 `Personnel.member_kind` (öğretmen · yönetici · diğer); değerler tasarımın
    Türkçe büyük harf ASCII kuralına uyar (§5 O8; plan "F1b-5 uygulama kararları"). Ekranda
    "üye türü" denmez: diğer personel birliğin üyesi değildir (OAB Yön. md. 4/1-e). Şifrelenmez
    (tasarım §5.3). Unvanın yerini ALMAZ: e-Okul'daki "Görevi" metni yalnız bu değerlerden
    birini seçmek için aktarım sırasında geçici okunur, saklanmaz (tasarım §8.4).
    """

    OGRETMEN = "OGRETMEN", "öğretmen"
    YONETICI = "YONETICI", "yönetici"
    DIGER = "DIGER", "diğer personel"


class Personnel(BaseModel):
    """Okul personeli — login'siz sicil kaydı (tasarım §5.1).

    Ayrılışta `is_active=False` + `left_at` yazılır (`services.persons`
    ayrılış yolu); kayıt SİLİNMEZ. Bağsız ayrılan personelin silinmesi dönem
    kapanışının işidir (tasarım §5.4). e-Okul listesinde bulunmayan aktif kişi
    önce ayrılış havuzuna girer (`leave_candidate_since`). Ad-soyad ŞİFRELİDİR (§5.3) — ada
    dayalı arama, sıralama ve eşleştirme Python katmanında yapılır. Unvan ve
    branş YOKTUR (§8.4).

    DENETİM İZİ (tasarım §4.6.2): `Personnel` KVKK silme kümesindedir (§5.4: bağsız
    ayrılan personel dönem kapanışında silinir), bu yüzden `values` BOŞTUR
    (`IZ_DEGER_ALANLARI = ()`): satıra yalnız değişen alanların adları girer. Silme
    kümesindeki kişi alanları (ad, soyad) içerik MAC'ine de GİRMEZ (`IZ_MAC_DISI_ALANLARI`;
    tasarım §5 O4, §4.6.2 "KVKK gereği boşaltılan ya da silinen alanlar"): satır silindikten
    sonra iz satırları kalır, İA'ya erişen biri bilinen öteki alanlarla (zaman damgaları
    satırın anına yakındır, görev türü ve durum dar bir uzaydır) aday ad-soyad sözlüğünü
    deneyerek silinen kişiyi geri bulabilirdi — silme anlamsızlaşırdı. İçerik MAC'i kalan
    alanları kapsar. Dürüst sınır: ad-soyad sütununa program dışından yazılan değer ya da
    başka satırdan taşınmış şifreli token içerik MAC'inde görünmez. Ayrılış ve havuz alanları
    durum geçişidir (`DURUM`).
    """

    #: Denetim izinde değeri yazılabilen alan YOK (KVKK silme kümesi; tasarım §4.6.2).
    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = ()
    #: İçerik MAC'ine giren alanlar: kimlik ve KVKK silme kümesindeki kişi alanları hariç.
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "updated_at",
        "deleted_at",
        "member_kind",
        "is_active",
        "left_at",
        "leave_candidate_since",
        "leave_candidate_run",
    )
    #: İçerik MAC'inin DIŞINDAKİ alanlar: silinen kişi verisi (tasarım §5 O4; belge dizesi).
    IZ_MAC_DISI_ALANLARI: ClassVar[tuple[str, ...]] = ("first_name", "last_name")
    #: Durum alanları: ayrılış ve ayrılış havuzu (§4.6.2 kural 3; ayrı `DURUM` satırı).
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = (
        "is_active",
        "left_at",
        "leave_candidate_since",
        "leave_candidate_run",
        "deleted_at",
    )

    first_name = EncryptedCharField("ad", max_length=100)
    last_name = EncryptedCharField("soyad", max_length=100)
    member_kind = models.CharField(
        "görev türü", max_length=16, choices=MemberKind.choices, default=MemberKind.OGRETMEN
    )
    is_active = models.BooleanField("aktif", default=True)
    left_at = models.DateField("ayrılış tarihi", null=True, blank=True)
    leave_candidate_since = models.DateField("ayrılış havuzuna giriş tarihi", null=True, blank=True)
    leave_candidate_run = models.ForeignKey(
        "ImportRun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="havuza ekleyen aktarım",
    )

    class Meta:
        verbose_name = "personel"
        verbose_name_plural = "personel"
        # Şifreli alanda DB sıralaması anlamsızdır (token sırası) — kayıt sırası
        # kararlı olsun diye pk; ad sıralaması selector'da Python ile yapılır.
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(member_kind__in=MemberKind.values),
                name="ck_personnel_member_kind",
            ),
            # Ayrılış havuzunda yalnız AKTİF kişi bekler (ayrılış havuzu temizler).
            models.CheckConstraint(
                condition=models.Q(leave_candidate_since__isnull=True) | models.Q(is_active=True),
                name="ck_personnel_leave_candidate_active",
            ),
        ]

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_full_name(self) -> str:
        """Aile kalıbındaki `get_full_name` eşi — evrak şablonları bu adı çağırır."""
        return self.full_name


class ImportSourceType(models.TextChoices):
    """İçe aktarma kaynak türü (dosya ve pano yapıştırma AYNI türdedir; tasarım §5.1 `ImportRun`).

    Değerler tasarımın Türkçe büyük harf ASCII kuralına uyar (§5 O8; plan "F1b-5 uygulama
    kararları"). `VELI` veli listesinin aktarımıdır (`excel_veli`, `services.imports`; satırları
    `ParentRoster`).
    """

    PERSONEL = "PERSONEL", "Personel"
    VELI = "VELI", "Veli listesi"


class ImportStatus(models.TextChoices):
    RUNNING = "RUNNING", "Çalışıyor"
    COMPLETED = "COMPLETED", "Tamamlandı"
    FAILED = "FAILED", "Başarısız"
    PREVIEWED = "PREVIEWED", "Önizlendi"


class ImportRun(BaseModel):
    """Her toplu içe aktarma için bir kayıt (geçmiş izi + idempotency uyarısı).

    Aile kalıbı: aynı dosyanın yeniden COMMIT'i ENGELLENMEZ — `already_imported`
    yalnız UYARIDIR (güncelleme meşru). Kısıt bozulmasın diye yeniden commit
    MEVCUT COMPLETED satırı günceller (yeni satır açmaz).

    DENETİM İZİ (`services.imports`): koşunun açılışı `OLUSTUR`, kapanışı ve yeniden
    açılışı `DURUM` (durum, zamanlar ve sonuç raporu koşunun geçişidir). Dosya adı serbest
    metindir (kişi adı taşıyabilir), rapor iç içe JSON'dur: satıra yalnız adları girer;
    tür, içerik özeti (sha256), durum ve zamanlar değerleriyle.
    """

    #: Denetim izinde önce/sonra değeri yazılabilen kişisiz alanlar (tasarım §4.6.2).
    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "source_type",
        "file_hash",
        "status",
        "started_at",
        "finished_at",
        "deleted_at",
    )
    #: İçerik MAC'ine giren alanlar (kimlik hariç bütün alanlar; rapor JSON'uyla).
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "updated_at",
        "deleted_at",
        "source_type",
        "file_name",
        "file_hash",
        "status",
        "started_at",
        "finished_at",
        "report",
    )
    #: Durum alanları: koşunun yaşam döngüsü (açılış, kapanış, sonuç raporu).
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = (
        "status",
        "started_at",
        "finished_at",
        "report",
        "deleted_at",
    )

    source_type = models.CharField(
        "kaynak türü", max_length=16, choices=ImportSourceType.choices, db_index=True
    )
    file_name = models.CharField("dosya adı", max_length=255, blank=True, default="")
    file_hash = models.CharField("içerik özeti (SHA256)", max_length=64, db_index=True)
    status = models.CharField(
        "durum", max_length=16, choices=ImportStatus.choices, default=ImportStatus.RUNNING
    )
    started_at = models.DateTimeField("başlangıç", default=timezone.now)
    finished_at = models.DateTimeField("bitiş", null=True, blank=True)
    report = models.JSONField("rapor", default=dict, blank=True)

    class Meta:
        verbose_name = "içe aktarma koşusu"
        verbose_name_plural = "içe aktarma koşuları"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["source_type", "file_hash"], name="okul_importrun_hash_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_type", "file_hash"],
                condition=models.Q(deleted_at__isnull=True, status="COMPLETED"),
                name="uq_importrun_completed_per_hash",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_source_type_display()} — {self.file_name or self.file_hash[:12]}"


# ---------------------------------------------------------------------------
# Veli listesi (T5; tasarım §5.1 `ParentRoster`, §8.4)
# ---------------------------------------------------------------------------
#: Veli adı-soyadının üst sınırı (karakter; şifreli sütunun düz metni).
PARENT_NAME_MAX = 200
#: Öğrencinin sınıfının üst sınırı (normalleştirilmiş yazım: "10-A", "Hazırlık-B", "Anasınıfı-A",
#: "5 Yaş-A"; en uzunu "Anasınıfı-ABCD", 14 karakter).
STUDENT_CLASS_MAX = 16


def parent_name_blind_index(full_name: object) -> str:
    """Velinin adının kör indeksi (tasarım §5.1 `name_index`, §5.3); boş ad → ''.

    Yazımda (`ParentRoster.save`) ve aramada (`selectors.parent_roster_by_name`) AYNI yol:
    `name_match.name_key` katlaması (Türkçe harf ASCII'ye, küçük harf, tek boşluk) +
    `crypto.blind_index`. Metin olmayan değer (çözülemeyen alan işareti) boş anahtar verir.
    Anahtar bellekte değilse `KeyMissingError` (fail-closed).
    """
    return blind_index(name_key(full_name) if isinstance(full_name, str) else "")


class ParentRoster(models.Model):
    """Veli listesinin bir satırı — bir satır BİR ÖĞRENCİDİR (tasarım §5.1, §8.4; T5).

    İki çocuklu veli iki satırdır (TKB Tablo 1 "velisi katılan öğrenci sayısı"); satırlar
    birleştirilmez. Yalnız iki veri alanı vardır: velinin adı-soyadı (ŞİFRELİ) ve öğrencinin
    sınıfı (DÜZ METİN, yazımı `excel_veli.sinif_metni` ile normalleştirilir: "10-A", okul öncesi
    "Anasınıfı-A" ya da "5 Yaş-A"). Öğrencinin
    adı, numarası, T.C. kimlik no, telefon ve adres alınmaz. Kaynak dosyadaki satır sırası
    tutulmaz: satırlar sınıf ve çözülmüş ad sırasıyla yazılır (`services.imports`).

    F1b'DE OLMAYAN ALANLAR (plan "F1b-5 uygulama kararları"; hedef modeli olmayan alan
    uydurulmaz): birlik dönemi bağı (`term` → `OabTerm`) F1c'de, katılım işaretleri
    (`attended_assembly` → `GeneralAssembly`, `attended_meeting`) F2'de göçle eklenir. O güne
    dek "dönem içindeki önceki parti" kuralı (tasarım §8.4 (1)) bütün canlı liste üzerinde
    çalışır. Başka hiçbir model buna yabancı anahtar vermez (silinebilirlik).

    KÖR İNDEKS (`name_index`) YALNIZ `save()` İLE YAZILIR: `QuerySet.update(full_name=…)`,
    `bulk_update` ve `bulk_create` `save()`'i atlar, indeks boş ya da eski adda kalır. Veli
    listesi toplu yazılmaz (koruma testi: `test_veli_listesi.py::test_veli_adi_toplu_yazilmaz`;
    denetçinin kendi sınaması `test_toplu_yazim_denetcisi_ihlali_yakalar`).
    İndeksin işi adaydan kişi kaydına geçiş ve yeniden aktarımda aynı velinin bulunmasıdır
    (tasarım §5.3; F1c).

    SİLME KVKK silmesidir (tasarım §5.4, §8.4: dönem kapanışında; program yöneticisi onayla elle
    de siler): satır katı silinir, yumuşak silme yoktur. Program elle silmeyi zamana bağlamaz
    (genel kurulun yapılıp yapılmadığı denetlenmez); aydınlatma metnindeki "genel kuruldan sonra
    daha önce de silinebilir" cümlesi okulun saklama beyanıdır, programın kısıtı değildir. Aktarımda dosyadaki sınıfların eski satırları
    yerine geçerken ve "Veli listesini sil"de silinir; ikisi de denetim izine kişisiz
    `KVKK_SILME` satırıdır (`services.imports`; elle silme `services.imports.delete_parent_roster`).

    DENETİM İZİ: satır başına iz YAZILMAZ ve model izin listesi TAŞIMAZ (`denetim_izi`
    yazıcısı onu yazamaz): tasarım §4.6.2 "veli listesinin hiçbir alanı ne açık ne şifreli
    olarak satıra girmez", "veli listesi modelinin tamamı MAC'e girmez". Aktarım kişisiz parti
    satırıyla yazılır — koşunun (`ImportRun`) `OLUSTUR` ve `DURUM` satırları; satırlar
    `import_run` ile o partiye bağlıdır (plan "F1b-5 uygulama kararları": erişim günlüğüne
    yazılmaz). Dürüst sınır: satırın içerik MAC'i olmadığı için program dışından yapılan
    değişiklik kayıt bütünlüğü denetiminde görünmez.
    """

    import_run = models.ForeignKey(
        ImportRun,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="aktarım partisi",
    )
    full_name = EncryptedCharField("veli adı-soyadı", max_length=PARENT_NAME_MAX)
    name_index = models.CharField(
        "veli adı kör indeksi", max_length=64, blank=True, default="", editable=False
    )
    student_class = models.CharField("öğrencinin sınıfı", max_length=STUDENT_CLASS_MAX)
    created_at = models.DateTimeField("oluşturulma", auto_now_add=True)

    class Meta:
        verbose_name = "veli listesi satırı"
        verbose_name_plural = "veli listesi"
        # Ad şifreli → DB'de ona sıralanamaz; kullanıcıya gösterilen sıra Python'dadır.
        ordering = ["student_class", "pk"]
        indexes = [
            models.Index(fields=["student_class"], name="okul_parentroster_class_idx"),
            models.Index(fields=["name_index"], name="okul_parentroster_name_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(student_class=""),
                name="ck_parentroster_student_class",
            ),
        ]

    def __str__(self) -> str:
        return f"Veli listesi satırı ({self.student_class})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Adın kör indeksini günceller, sonra kaydeder.

        `update_fields` verilmişse ve ad içinde yoksa indeks yeniden hesaplanmaz (anahtar
        gerekmez). Ad içindeyse indeks alanı da `update_fields`'e eklenir. Ad çözülemiyorsa
        (`CorruptField`, tasarım §13 D48) indeks yeniden HESAPLANMAZ: işaretin indeksi
        anlamsızdır ve eşleşmeye sahte bir değer sokardı; kayıtlı indeks olduğu gibi kalır.
        """
        update_fields = kwargs.get("update_fields")
        if (update_fields is None or "full_name" in update_fields) and not is_corrupt(
            self.full_name
        ):
            self.name_index = parent_name_blind_index(self.full_name)
            if update_fields is not None and "name_index" not in update_fields:
                kwargs["update_fields"] = [*update_fields, "name_index"]
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Hesaplar ve iz anahtarı (tasarım §4.6; F1b-1)
# ---------------------------------------------------------------------------
class DeletionNotAllowed(RuntimeError):
    """Satırı silinmeyen modelde silme denendi (altın kural 4; tasarım §4.6)."""


class _NoDeleteQuerySet(models.QuerySet):  # type: ignore[type-arg]  # Any davranışı korunur
    """Toplu silmeyi reddeden queryset (hesap ve iz anahtarı satırları silinmez)."""

    def delete(self) -> tuple[int, dict[str, int]]:
        raise DeletionNotAllowed("Bu kayıtlar silinmez (tasarım §4.6).")


class AccountRole(models.TextChoices):
    """Hesap rolleri (tasarım §2.3.1 rol kodları, §4.4.1; etiketler sözlük §1).

    `yonetici` etiketi sözlüğün tam adıdır; kilit ekranındaki kısa etiket
    ("Program yöneticisi") oturum katmanındadır (plan F1b-1 "Oturum").
    """

    YONETICI = "yonetici", "Program yöneticisi (OAB'den sorumlu müdür yardımcısı)"
    BASKAN = "baskan", "Başkan"
    BASKAN_YARDIMCISI = "baskan_yardimcisi", "Başkan yardımcısı"
    MUHASIP = "muhasip", "Muhasip"
    SEKRETER = "sekreter", "Sekreter"
    DENETLEME_KURULU = "denetleme_kurulu", "Denetleme Kurulu"
    MUDUR = "mudur", "Okul müdürü"


#: Aynı anda tek açık (KAPALI olmayan) hesabı olabilen roller (tasarım §4.6.1 kısıtları).
SINGLE_ACCOUNT_ROLES: tuple[str, ...] = (
    AccountRole.BASKAN.value,
    AccountRole.BASKAN_YARDIMCISI.value,
    AccountRole.MUHASIP.value,
    AccountRole.SEKRETER.value,
    AccountRole.MUDUR.value,
)
#: Denetleme Kurulu hesabı üst sınırı (asıl üyeler: 1 veli + 2 öğretmen, md. 14/1).
MAX_AUDIT_BOARD_ACCOUNTS = 3


class AccountStatus(models.TextChoices):
    """Hesap durumu (tasarım §4.6.1). `KAPALI` geri dönmez."""

    PAROLA_YENILENMELI = "PAROLA_YENILENMELI", "Parola yenilenmeli"
    ACIK = "ACIK", "Açık"
    ASKIDA = "ASKIDA", "Askıda"
    KAPALI = "KAPALI", "Kapalı"


class SuspendReason(models.TextChoices):
    """`ASKIDA` durumunun nedeni; hatalı deneme askısı `guvenlik.json`'dadır (§4.4.4)."""

    UYELIK_DUSTU = "UYELIK_DUSTU", "Üyelik düştü"
    GOREV_BOLUMU = "GOREV_BOLUMU", "Görev bölümü"


class ResetKind(models.TextChoices):
    """Parolanın neden yenilendiği (sahibine ilk girişte bildirilir; tasarım §4.3 tehdit 12)."""

    SIFIRLAMA = "SIFIRLAMA", "Parola sıfırlandı"
    KURTARMA = "KURTARMA", "Kurtarma anahtarıyla yenilendi"


class Account(models.Model):
    """Kişisel hesap: bir kişi + bir rol (tasarım §4.4.1, §4.6.1; T1).

    `guvenlik.json`'daki `hesaplar[]` ile İKİ DEPO kuralına bağlıdır: `id` sarmalın
    `id`'si, `login_name` sarmalın `tanitici`'sidir; rol, ad-soyad, durum ve tarihler
    yalnız burada durur (§4.4.4). Kural ve sıralar `services.app_password` ve
    `services.hesaplar` modül başlıklarındadır.

    MÜHÜR (`seal`): `HMAC(HKDF(DEK, "od-hesap-muhru/v1"), kanonik(id, login_name,
    role, status, person, membership, term, opened_at, closed_at, wrap_digest,
    wrap_digest_pending))` (`shared.kanonik.hesap_muhru`). Kilit açılışında seçilen
    hesabın mührü DEK belleğe alınmadan doğrulanır; tutmazsa giriş reddedilir ve satıra
    DOKUNULMAZ (yeniden mühürlemek program dışından değiştirilmiş rolü meşrulaştırırdı;
    §4.3 tehdit 19). `person`, `membership` ve `term` alanları hedef modelleriyle F1c'de
    gelir; mühür onları bugünden `null` olarak taşır, alanlar eklenince var olan
    mühürler değişmez.

    SARMAL ÖZETİ (kullanıcı kararı 03.11.2026 "tazelik kapatılır"; `app_password` modül
    başlığı "SARMALIN TAZELİĞİ"): `wrap_digest` hesabın `guvenlik.json`'daki GÜNCEL parola
    kaydının (sarmalın) DEK'li özetidir, `wrap_digest_pending` iki aşamalı yazımın bekleyen
    özeti (kesinti hâli). Parolayla açılan sarmalın özeti ikisinden birini tutmalıdır; ikisi de
    boşsa hesap parolayla açılmaz (fail-closed). İki alan mühre girer: satırdaki özet tek başına
    eski değerle değiştirilemez.

    SATIRIN İZİ (kullanıcı kararı 03.11.2026 "Girişte reddet"; `services.satir_izi`): mühür satırın
    bir zamanlar program tarafından yazıldığını kanıtlar, bugünkü hâli olduğunu kanıtlamaz. Satır
    denetim izindeki SON içerik MAC'li kaydını da tutmalıdır (`IZ_OZET_ALANLARI` üzerinden); eski bir
    kopyadan geri konmuş satır giriş, oturum işlemi, kurtarma ve hesap işlemi açmaz. Bu yüzden her
    yazım satırla aynı işlemde iz satırı yazar (aşağıda "DENETİM İZİ") ve `IZ_OZET_ALANLARI`'nı ya
    da var olan satırların bu alanlardaki değerini değiştiren her değişiklik (F4'ün DEK yenilemesi
    dahil) `KAPALI` olanlar DAHİL BÜTÜN satırların izini aynı işlemde yeniden kurmalıdır — her
    satırı önce eski hâliyle son kaydına karşı doğrulayıp yalnız tutanlara; yoksa açık satırların
    girişi reddedilir, `KAPALI` satırlar iki depo kartında yanlış alarm verir. Bu adımın bugün yeri
    yoktur, küme o tasarlanmadan değişmez (`satir_izi.HESAP_OZET_ALANLARI` yorumu; kullanıcı kararı
    bekler).

    KISITLAR (sert; sistem bütünlüğü): açık (`KAPALI` olmayan) hesaplar arasında
    `login_name` tekil · başkan, başkan yardımcısı, muhasip, sekreter ve okul müdürü
    için tek açık hesap (DB kısıtı) · Denetleme Kurulu için en çok üç ve en az bir
    açık program yöneticisi (servis katmanı, `services.hesaplar`). SATIR SİLİNMEZ:
    `delete()` ve toplu silme `DeletionNotAllowed` yükseltir (TK11; altın kural 4).
    `BaseModel`'den türemez: yumuşak silme ve `updated_at` bu modele uymaz.

    DENETİM İZİ (tasarım §4.6.2; plan F1b-1 alt commit c): her yazma (`app_password`,
    `services.hesaplar`) satırla AYNI işlemde iz satırı yazar (`HESAP`, `PAROLA`,
    `KURTARMA`, `GIRIS`; parola yenilenme bildiriminin kapatılması `GUNCELLE`). Önce/sonra değeri satıra giren alanlar yalnız durum, rol, kod
    ve tarihlerdir (`IZ_DEGER_ALANLARI`): ad-soyad şifreli kişi verisidir, tanıtıcı
    kişinin adını içerebilir (program yalnız uyarır), mühür ve hesap bağları değer
    taşımaz — satıra yalnız adları girer. İçerik MAC'i kimlik dışındaki bütün alanları
    çözülmüş değerleriyle kapsar (`IZ_OZET_ALANLARI`): şifreli sütuna yazılmış düz metin
    ya da başka satırdan taşınmış ad token'ı burada görünür (denetim GA-9).
    """

    #: Denetim izinde önce/sonra değeri yazılabilen kişisiz alanlar (tasarım §4.6.2).
    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "role",
        "status",
        "suspend_reason",
        "opened_at",
        "closed_at",
        "password_changed_at",
        "reset_at",
        "reset_kind",
        "reset_notice_pending",
        "last_login_at",
    )
    #: İçerik MAC'ine giren alanlar (kimlik hariç; ad-soyad çözülmüş değeriyle).
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "login_name",
        "role",
        "display_name",
        "status",
        "suspend_reason",
        "opened_at",
        "opened_by",
        "closed_at",
        "closed_by",
        "password_changed_at",
        "reset_at",
        "reset_by",
        "reset_kind",
        "reset_notice_pending",
        "last_login_at",
        "wrap_digest",
        "wrap_digest_pending",
        "seal",
    )

    id = models.UUIDField("kimlik", primary_key=True, default=uuid.uuid4, editable=False)
    login_name = models.CharField("tanıtıcı", max_length=32)
    role = models.CharField("rol", max_length=24, choices=AccountRole.choices)
    display_name = EncryptedCharField("hesap sahibinin adı-soyadı", max_length=150)
    status = models.CharField(
        "durum",
        max_length=24,
        choices=AccountStatus.choices,
        default=AccountStatus.PAROLA_YENILENMELI,
    )
    suspend_reason = models.CharField(
        "askı nedeni", max_length=16, choices=SuspendReason.choices, blank=True, default=""
    )
    opened_at = models.DateTimeField("açılış", default=timezone.now)
    opened_by = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="açan hesap",
    )
    closed_at = models.DateTimeField("kapanış", null=True, blank=True)
    closed_by = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="kapatan hesap",
    )
    password_changed_at = models.DateTimeField("parola değişimi", null=True, blank=True)
    reset_at = models.DateTimeField("parola yenilenme anı", null=True, blank=True)
    reset_by = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="parolayı sıfırlayan hesap",
    )
    reset_kind = models.CharField(
        "parola yenilenme türü", max_length=16, choices=ResetKind.choices, blank=True, default=""
    )
    reset_notice_pending = models.BooleanField("yenilenme bildirimi bekliyor", default=False)
    last_login_at = models.DateTimeField("son giriş", null=True, blank=True)
    wrap_digest = models.CharField("parola kaydının özeti", max_length=64, blank=True, default="")
    wrap_digest_pending = models.CharField(
        "parola kaydının bekleyen özeti", max_length=64, blank=True, default=""
    )
    seal = models.CharField("mühür", max_length=64, blank=True, default="")

    objects = _NoDeleteQuerySet.as_manager()

    class Meta:
        verbose_name = "hesap"
        verbose_name_plural = "hesaplar"
        ordering = ["opened_at", "login_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["login_name"],
                condition=~models.Q(status="KAPALI"),
                name="uq_account_login_name_open",
            ),
            models.UniqueConstraint(
                fields=["role"],
                condition=models.Q(role__in=SINGLE_ACCOUNT_ROLES) & ~models.Q(status="KAPALI"),
                name="uq_account_single_role_open",
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=AccountRole.values), name="ck_account_role"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=AccountStatus.values), name="ck_account_status"
            ),
            models.CheckConstraint(
                condition=models.Q(suspend_reason__in=[*SuspendReason.values, ""]),
                name="ck_account_suspend_reason",
            ),
            models.CheckConstraint(
                condition=models.Q(reset_kind__in=[*ResetKind.values, ""]),
                name="ck_account_reset_kind",
            ),
            # Askı nedeni yalnız ASKIDA durumunda dolu olur.
            models.CheckConstraint(
                condition=models.Q(status="ASKIDA") | models.Q(suspend_reason=""),
                name="ck_account_suspend_reason_status",
            ),
            # Kapanış anı yalnız KAPALI durumda, KAPALI durumda da daima dolu.
            models.CheckConstraint(
                condition=(models.Q(status="KAPALI") & models.Q(closed_at__isnull=False))
                | (~models.Q(status="KAPALI") & models.Q(closed_at__isnull=True)),
                name="ck_account_closed_at_status",
            ),
        ]

    def __str__(self) -> str:
        # Ad-soyad şifreli ve kişisel veridir: temsil tanıtıcı ve roldür.
        return f"{self.login_name} ({self.get_role_display()})"

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        raise DeletionNotAllowed("Hesap kaydı silinmez; hesap kapatılır (tasarım §4.6.1).")

    def seal_fields(self) -> dict[str, Any]:
        """Mühre giren alanlar (`shared.kanonik.HESAP_MUHRU_ALANLARI`).

        `person`, `membership` ve `term` F1c'ye dek `None`dır (sınıf belge dizesi).
        """
        return {
            "id": self.id,
            "login_name": self.login_name,
            "role": self.role,
            "status": self.status,
            "person": None,
            "membership": None,
            "term": None,
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "wrap_digest": self.wrap_digest,
            "wrap_digest_pending": self.wrap_digest_pending,
        }

    def compute_seal(self, data_key: bytes) -> str:
        """Bu satırın verilen DEK'le mührü (DEK belleğe yüklenmeden de hesaplanır)."""
        return kanonik.hesap_muhru(account_seal_key(data_key), self.seal_fields())

    def seal_matches(self, data_key: bytes) -> bool:
        """Kayıtlı mühür verilen DEK'le hesaplanana eşit mi? (sabit sürede karşılaştırılır)

        Mühre giren bir alan kanonik biçime giremiyorsa (program dışından metin sütununa yazılmış
        ikili değer) mühür tutmuyor sayılır: hata yükseltip denetimi yarıda kesmez (ORM'siz
        okuyucuyla aynı; `geri_yukleme_yetkisi`).
        """
        if not self.seal:
            return False
        try:
            beklenen = self.compute_seal(data_key)
        except kanonik.KanonikHata:
            return False
        return kanonik.esit(self.seal, beklenen)

    @property
    def display_name_text(self) -> str | None:
        """Ad-soyadın okunabilir hâli; çözülemiyorsa None (ekranda "okunamadı", plan F1b-1)."""
        deger = self.display_name
        return None if is_corrupt(deger) else str(deger)


class AuditKey(models.Model):
    """Denetim izinin iz anahtarı (İA; tasarım §4.6.3).

    İA kurulumda ayrı üretilen 32 rastgele bayttır, DEK'ten TÜREMEZ; DEK'le şifreli
    (Fernet) olarak burada durur: veritabanıyla birlikte yedeğe girer, geri yükleme
    hangi yoldan yapılırsa yapılsın zincir doğrulanabilir. `key` alanı base64
    kodlu anahtarın şifreli hâlidir. DEK yenilemesinde (F4) yeni İA eklenir, eskiler
    yeni DEK'le yeniden şifrelenir ve `retired_at` alır. Açık kipteki her iz satırının
    `key_ref`'i o satırı mühürleyen anahtarın kimliğidir (`AuditTrail`). Satır silinmez.

    İA kişisel veri değildir (§4.6.5): şifreli alanı Güvenlik ekranındaki
    "şifrelenen alanlar" listesine girmez (`ENCRYPTED_FIELDS_ARE_PERSONAL`).
    """

    #: `app_password.protected_field_labels` bu modelin şifreli alanlarını listelemez.
    ENCRYPTED_FIELDS_ARE_PERSONAL = False

    key = EncryptedTextField("iz anahtarı")
    valid_from_seq = models.PositiveBigIntegerField("geçerli ilk iz sırası", unique=True)
    created_at = models.DateTimeField("oluşturulma", default=timezone.now)
    retired_at = models.DateTimeField("emeklilik", null=True, blank=True)

    objects = _NoDeleteQuerySet.as_manager()

    class Meta:
        verbose_name = "iz anahtarı"
        verbose_name_plural = "iz anahtarları"
        ordering = ["valid_from_seq"]

    def __str__(self) -> str:
        return f"İz anahtarı ({self.valid_from_seq}. satırdan)"

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        raise DeletionNotAllowed("İz anahtarı silinmez (tasarım §4.6.3).")


# ---------------------------------------------------------------------------
# Denetim izi (tasarım §4.6.2-§4.6.3; TK16; plan F1b-1 alt commit c)
# ---------------------------------------------------------------------------
class ImmutableRecord(RuntimeError):
    """Ekleme-yalnız modelde güncelleme ya da silme denendi (tasarım §4.6.2 yazma kuralı 2).

    Erişim günlüğü (`AccessLog`, §4.6.4) de aynı hatayı verir: satırı değiştirilemez, saklama
    süresi dolmadan silinemez, toplu eklenemez (satırı tek tek yazıcı yazar).
    """


class _AppendOnlyQuerySet(models.QuerySet):  # type: ignore[type-arg]  # Any davranışı korunur
    """Toplu güncellemeyi ve silmeyi reddeden queryset (denetim izi ekleme-yalnızdır)."""

    def update(self, **kwargs: Any) -> int:
        raise ImmutableRecord("Denetim izi satırı değiştirilemez (tasarım §4.6.2).")

    def bulk_update(self, objs: Any, fields: Any, batch_size: int | None = None) -> int:
        raise ImmutableRecord("Denetim izi satırı değiştirilemez (tasarım §4.6.2).")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ImmutableRecord("Denetim izi satırı silinemez (tasarım §4.6.2).")


class AuditActor(models.TextChoices):
    """Yazmanın aktörü: hesap ya da kullanıcı eylemi olmadan programın kendi işi."""

    HESAP = "HESAP", "Hesap"
    SISTEM = "SISTEM", "Program"


class AuditAction(models.TextChoices):
    """İz satırının türü — KAPALI KÜME (tasarım §4.6.2); yeni tür göçle eklenir.

    Küme `test_denetim_izi.py`'deki anlık görüntüyle sabittir. Kilitliyken yalnız
    `YEDEK`, `GOC`, `GUN_ISI` ve `BUTUNLUK` yazılabilir (§4.6.3, kilitli kip). Etiketler
    iç belge içindir; kullanıcıya görünen adları denetim modülü (F4) sözlükten verir.
    """

    OLUSTUR = "OLUSTUR", "Oluşturma"
    GUNCELLE = "GUNCELLE", "Güncelleme"
    DURUM = "DURUM", "Durum değişikliği"
    TERS_KAYIT = "TERS_KAYIT", "Ters kayıt"
    ISARET = "ISARET", "İşaret"
    BASIM = "BASIM", "Basım"
    KVKK_SILME = "KVKK_SILME", "Kişisel veri silme"
    GIRIS = "GIRIS", "Giriş"
    KILIT = "KILIT", "Kilit"
    HESAP = "HESAP", "Hesap işlemi"
    PAROLA = "PAROLA", "Parola"
    KURTARMA = "KURTARMA", "Kurtarma anahtarı"
    YEDEK = "YEDEK", "Yedek"
    GOC = "GOC", "Şema göçü"
    GERI_YUKLEME = "GERI_YUKLEME", "Geri yükleme"
    DEK_YENILEME = "DEK_YENILEME", "Veri anahtarı yenileme"
    BUTUNLUK = "BUTUNLUK", "Bütünlük denetimi"
    GUN_ISI = "GUN_ISI", "Gün işi"


class AuditLabel(models.TextChoices):
    """İz satırının etiketi (tasarım §4.6.2); boş değer etiketsizdir. F1b'de kullanılmaz."""

    GECIS = "GECIS", "Geçiş kurulumu"
    KISA_YOL = "KISA_YOL", "Genel karar kapsamında kısa yol"
    KAPALI_DONEM = "KAPALI_DONEM", "Kapanmış döneme beyaz listedeki yazma"


class AuditKeyMode(models.TextChoices):
    """Satırın hangi anahtarla mühürlendiği (tasarım §4.6.3)."""

    ACIK = "ACIK", "İz anahtarı"
    KILITLI = "KILITLI", "Kilitli kip anahtarı"


#: Kilitliyken yazılabilen kişisiz sistem olayları — KAPALI KÜME (tasarım §4.6.3): yedek
#: alındı ya da döndürüldü, şema göçü uygulandı, gün işi DEK istediği için ertelendi,
#: bütünlük denetiminin bulgusu. Kilitli kip satırı yalnız `SISTEM`'indir; yazıcı ve
#: veritabanı kısıtı (`ck_audittrail_locked_closed_set`) birlikte zorlar.
KILITLI_KIP_TURLERI: tuple[str, ...] = (
    AuditAction.YEDEK.value,
    AuditAction.GOC.value,
    AuditAction.GUN_ISI.value,
    AuditAction.BUTUNLUK.value,
)


class AuditTrail(models.Model):
    """Denetim izi — ekleme-yalnız, HMAC zincirli, kişisel veri taşımayan kayıt (tasarım §4.6.2).

    Tek yazarı `apps.okul.denetim_izi`'dir (açık çağrı; sinyal ya da `save()` kancası
    YOK: toplu güncelleme ve yumuşak silme sinyali atlardı). Kurallar orada ve
    tasarımdadır; burada şema ve ekleme-yalnızlık:

    * `seq` birincil anahtardır ve yazıcı tarafından, işlemin İÇİNDE veritabanındaki son
      satırdan +1 olarak verilir (MAC `seq`'i kapsar; önce bilinmelidir). Geri alınan
      işlemin satırı kalmaz, sıra boşluk bırakmaz.
    * `at` UTC saklanır (USE_TZ); kanonik biçim UTC `Z`'dir, ekranlar Europe/Istanbul gösterir.
    * `term` (→ OabTerm) ve `compliance_item` (→ ComplianceItem) sütunları hedef
      modelleriyle F1c'de gelir; kanonik biçim onları bugünden `null` olarak taşır
      (`shared.kanonik.IZ_SATIRI_ALANLARI`): sütunlar eklenince var olan MAC'ler değişmez.
    * `values` yalnız modelin izinli kişisiz alanlarının `[önce, sonra]` değerlerini,
      kanonik ilkel biçimde (`kanonik.duz`) taşır; `changed_fields` yalnız alan adlarıdır.
    * `key_ref` metindir: açık kipte `AuditKey` kimliği, kilitli kipte `"<çapa seq>:<adım>"`;
      `iz-durumu.json` yokken yazılan mühürsüz kilitli satırda boş (`apps.okul.iz_durumu`).
    * Kilitli kip satırı yalnız `KILITLI_KIP_TURLERI`'ndeki bir `SISTEM` olayıdır ve içerik
      MAC'i taşımaz (iki veritabanı kısıtı).
    * `record_mac` ve `prev_mac` boş dize olabilir (içerik MAC'i olmayan olay; ilk satır).

    EKLEME-YALNIZ (yazma kuralı 2): var olan satırda `save()`, `delete()`, toplu
    `update()`/`delete()` `ImmutableRecord` yükseltir; ayrıca SQLite tetikleyicileri
    (`BEFORE UPDATE`, `BEFORE DELETE` → `RAISE(ABORT)`, `0001_initial`) program içi kazayı
    veritabanında keser. Program dışındaki değişikliği zincir yakalar. Tetikleyicileri
    kapatan bir üretim yolu YOKTUR; testlerin `flush`'ı kök `conftest.py`'dedir.
    """

    seq = models.PositiveBigIntegerField("sıra", primary_key=True)
    at = models.DateTimeField("zaman")
    actor = models.CharField("aktör", max_length=8, choices=AuditActor.choices)
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="hesap",
    )
    role = models.CharField("rol", max_length=24, blank=True, default="")
    action = models.CharField("tür", max_length=16, choices=AuditAction.choices)
    model = models.CharField("model", max_length=64)
    object_id = models.CharField("kayıt kimliği", max_length=64)
    changed_fields = models.JSONField("değişen alanlar", default=list, blank=True)
    values = models.JSONField("değerler", default=dict, blank=True)
    record_mac = models.CharField("içerik MAC'i", max_length=64, blank=True, default="")
    label = models.CharField(
        "etiket", max_length=16, choices=AuditLabel.choices, blank=True, default=""
    )
    key_mode = models.CharField("anahtar kipi", max_length=8, choices=AuditKeyMode.choices)
    key_ref = models.CharField("anahtar başvurusu", max_length=64)
    prev_mac = models.CharField("önceki MAC", max_length=64, blank=True, default="")
    mac = models.CharField("MAC", max_length=64)

    objects = _AppendOnlyQuerySet.as_manager()

    class Meta:
        verbose_name = "denetim izi satırı"
        verbose_name_plural = "denetim izi"
        ordering = ["seq"]
        indexes = [
            models.Index(fields=["model", "object_id", "seq"], name="okul_audittrail_kayit_idx"),
            models.Index(fields=["action", "account", "seq"], name="okul_audittrail_tur_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(action__in=AuditAction.values), name="ck_audittrail_action"
            ),
            models.CheckConstraint(
                condition=models.Q(actor__in=AuditActor.values), name="ck_audittrail_actor"
            ),
            models.CheckConstraint(
                condition=models.Q(key_mode__in=AuditKeyMode.values),
                name="ck_audittrail_key_mode",
            ),
            models.CheckConstraint(
                condition=models.Q(label__in=[*AuditLabel.values, ""]),
                name="ck_audittrail_label",
            ),
            # Hesap satırında hesap ve rol dolu; SISTEM satırında ikisi de boş.
            models.CheckConstraint(
                condition=(models.Q(actor="HESAP", account__isnull=False) & ~models.Q(role=""))
                | models.Q(actor="SISTEM", account__isnull=True, role=""),
                name="ck_audittrail_actor_account",
            ),
            # Kilitli kip satırı içerik MAC'i taşımaz (hiçbir veri değişikliğini meşrulaştıramaz).
            models.CheckConstraint(
                condition=models.Q(key_mode="ACIK") | models.Q(record_mac=""),
                name="ck_audittrail_locked_no_record_mac",
            ),
            # Kilitli kip satırı yalnız kapalı kümedeki SISTEM olayıdır (tasarım §4.6.3).
            models.CheckConstraint(
                condition=models.Q(key_mode="ACIK")
                | models.Q(actor="SISTEM", action__in=KILITLI_KIP_TURLERI),
                name="ck_audittrail_locked_closed_set",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.seq}. {self.action} {self.model} {self.object_id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Yalnız YENİ satır yazılır; var olan satırın kaydı `ImmutableRecord` yükseltir."""
        if not self._state.adding:
            raise ImmutableRecord("Denetim izi satırı değiştirilemez (tasarım §4.6.2).")
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        raise ImmutableRecord("Denetim izi satırı silinemez (tasarım §4.6.2).")


# ---------------------------------------------------------------------------
# Erişim günlüğü (tasarım §4.6.4; plan F1b-1 alt commit d)
# ---------------------------------------------------------------------------
class AccessKind(models.TextChoices):
    """Hassas okumanın ya da kişisel veri içeren çıktının türü — KAPALI KÜME (tasarım §4.6.4).

    Küme `test_erisim_gunlugu.py`'deki anlık görüntüyle sabittir; yeni tür göçle eklenir (DB
    kısıtı da aynı kümedir). Etiketler iç belge içindir; kullanıcıya görünen adları okuma
    ucunun `apps.okul.erisim_gunlugu.TUR_ADLARI`'ndadır (sözlük §1 "Erişim günlüğü (F1b)").
    """

    MASKESIZ_TCKN = "MASKESIZ_TCKN", "Maskesiz T.C. kimlik no"
    KISI_DOKUMU = "KISI_DOKUMU", "Kişi dökümü"
    #: Adlı E07 (davet teslim çizelgesi) ve E08 (katılım cetveli).
    VELI_LISTESI_CIKTISI = "VELI_LISTESI_CIKTISI", "Veli listesi çıktısı"
    KISISEL_DISA_AKTARIM = "KISISEL_DISA_AKTARIM", "Kişisel veri dışa aktarımı"
    IHLAL_DOKUMU = "IHLAL_DOKUMU", "İhlal dökümü"
    OZEL_NITELIKLI_EK = "OZEL_NITELIKLI_EK", "Özel nitelikli ek"
    #: Kantin isteklisinin katılım engeli dayanağı, organ üyesinin görev alma engeli dayanağı.
    OZEL_NITELIKLI_ALAN = "OZEL_NITELIKLI_ALAN", "Özel nitelikli alan"


class _AccessLogQuerySet(models.QuerySet):  # type: ignore[type-arg]  # Any davranışı korunur
    """Erişim günlüğünün queryset'i: toplu ekleme, güncelleme ve silme reddedilir (`AccessLog`).

    Toplu ekleme `save()`'i ve yazıcının biçim denetimini atlardı; yazıcı satırı tek tek
    `create` ile yazar. Tek silme yolu `_saklama_disini_sil`'dir; onu yalnız saklama süresini
    hesaplayan silme servisi çağırır (`apps.okul.erisim_gunlugu.suresi_dolanlari_sil`; tek
    çağıranı ve tek yazarı `test_erisim_gunlugu.py`'nin kaynak taraması sınar).
    """

    def bulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> list[Any]:
        raise ImmutableRecord(
            "Erişim günlüğüne toplu yazılmaz; satırı yalnız yazıcı yazar (tasarım §4.6.4)."
        )

    def update(self, **kwargs: Any) -> int:
        raise ImmutableRecord("Erişim günlüğü satırı değiştirilemez (tasarım §4.6.4).")

    def bulk_update(self, objs: Any, fields: Any, batch_size: int | None = None) -> int:
        raise ImmutableRecord("Erişim günlüğü satırı değiştirilemez (tasarım §4.6.4).")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ImmutableRecord(
            "Erişim günlüğü satırı yalnız saklama süresi dolunca silinir (tasarım §4.6.4)."
        )

    def _saklama_disini_sil(self, sinir: datetime) -> int:
        """`at`'i `sinir`'den ÖNCE olan satırları siler; silinen satır sayısını döndürür.

        Sınırı saklama süresinden silme servisi hesaplar; burada süre bilinmez (tek kaynak
        `erisim_gunlugu.SAKLAMA_SURESI_YIL`). Satırın ilişkisi olmadığı için silme tek
        `DELETE … WHERE at < ?` ifadesidir.
        """
        eskiler = self.filter(at__lt=sinir)
        return super(_AccessLogQuerySet, eskiler).delete()[0]


class AccessLog(models.Model):
    """Erişim günlüğü — hassas okumanın ve kişisel veri içeren çıktının kaydı (tasarım §4.6.4).

    KVKK md. 12 güvenlik tedbiridir (OYS'nin "okuma ≠ yönetme ≠ hassas detay" ayrımı). Tek
    yazarı `apps.okul.erisim_gunlugu.yaz`'dır; okuyan hesap ve rol yazar bağlamından gelir.

    * **Zincir dışıdır**: denetim izine bağlı değildir, satır mühürlenmez; süresi dolunca
      silinir (2 yıl, `erisim_gunlugu.SAKLAMA_SURESI_YIL`; §15 B-9 DOĞRULANMADI) ve silmenin
      kendisi denetim izine `KVKK_SILME` satırı olarak düşer. Arşiv paketine girmez (§8.5).
    * **Şifresizdir ve değer tutmaz**: kişisel veri olarak yalnız okuyan hesabın bağı ve
      okunan kaydın kimliği (takma ad düzeyinde) durur; okunan değer, ad, serbest metin
      hiçbir sütuna girmez. `model` uygulama etiketli model adı (`okul.Personnel`), `object_id`
      kimliğin metni, `field` modelin alan adıdır; çıktıda belgenin sha256'sı ve satır sayısı.

    KORUMA — SATIR DEĞİŞMEZ, YALNIZ SÜRESİ DOLUNCA SİLİNİR:

    * Model: var olan satırda `save()` ve `delete()`, queryset'te `bulk_create()`, `update()`,
      `bulk_update()` ve `delete()` `ImmutableRecord` yükseltir. Tek silme yolu queryset'in
      `_saklama_disini_sil`'idir; onu yalnız silme servisi çağırır.
    * Veritabanı: `BEFORE UPDATE` tetikleyicisi (`RAISE(ABORT)`, `0001_initial`) model
      yöntemlerini atlayan program içi güncellemeyi de (`_base_manager`, ham SQL) keser.
    * DELETE için tetikleyici YOKTUR, bilerek: koşulsuz bir tetikleyici meşru silmeyi (saklama
      süresinin dolması) de keserdi; "yalnız süresi dolan satır" koşulunu tetikleyiciye yazmak
      saklama süresini ve gün sınırını (Europe/Istanbul, 29 Şubat) SQL'de ikinci kez
      tanımlamak olurdu — süre DOĞRULANMADI'dır, değişirse iki tanım ayrışırdı. Program içi
      yazımı ve silmeyi model yöntemleri ile iki test tutar: kaynak taraması
      (`tests/test_erisim_gunlugu.py`: kökü `AccessLog` olan her yazım ve silme zinciri —
      `_base_manager` ve kurucu dahil — yalnız yazıcıda ve silme servisinde durur; takma adla
      ya da dizeyle başvuru yoktur) ve uçların tablo karşılaştırması
      (`tests/test_izsiz_yazim.py`: uç erişim günlüğüne yalnız EKLER; sildiği ya da değiştirdiği
      satır ucu düşürür). Program dışından silme zincir dışı bir tabloda görünmez; tasarımın
      kabul ettiği sınırdır (§4.6.4 "zincir dışıdır").
    """

    at = models.DateTimeField("zaman", default=timezone.now)
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="okuyan hesap",
    )
    role = models.CharField("rol", max_length=24)
    kind = models.CharField("tür", max_length=24, choices=AccessKind.choices)
    model = models.CharField("model", max_length=64, blank=True, default="")
    object_id = models.CharField("kayıt kimliği", max_length=64, blank=True, default="")
    field = models.CharField("alan", max_length=64, blank=True, default="")
    document_sha256 = models.CharField("belgenin sha256'sı", max_length=64, blank=True, default="")
    row_count = models.PositiveIntegerField("satır sayısı", null=True, blank=True)

    objects = _AccessLogQuerySet.as_manager()

    class Meta:
        verbose_name = "erişim günlüğü satırı"
        verbose_name_plural = "erişim günlüğü"
        ordering = ["at", "id"]
        indexes = [models.Index(fields=["at"], name="okul_accesslog_at_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind__in=AccessKind.values), name="ck_accesslog_kind"
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=AccountRole.values), name="ck_accesslog_role"
            ),
            # Çıktının özeti ve satır sayısı birliktedir; özet 64 onaltılık hanedir (biçimini
            # yazıcı denetler, SQLite `max_length`'i zorlamaz).
            models.CheckConstraint(
                condition=models.Q(document_sha256="", row_count__isnull=True)
                | models.Q(
                    Exact(Length("document_sha256"), 64),
                    row_count__isnull=False,
                ),
                name="ck_accesslog_document",
            ),
            # Kayıt kimliği yalnız bir modelle, alan adı yalnız bir kayıt kimliğiyle.
            models.CheckConstraint(
                condition=models.Q(object_id="") | ~models.Q(model=""),
                name="ck_accesslog_object_model",
            ),
            models.CheckConstraint(
                condition=models.Q(field="") | ~models.Q(object_id=""),
                name="ck_accesslog_field_object",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind} {self.model} {self.object_id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Yalnız YENİ satır yazılır; var olan satırın kaydı `ImmutableRecord` yükseltir."""
        if not self._state.adding:
            raise ImmutableRecord("Erişim günlüğü satırı değiştirilemez (tasarım §4.6.4).")
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        raise ImmutableRecord(
            "Erişim günlüğü satırı yalnız saklama süresi dolunca silinir (tasarım §4.6.4)."
        )


# ---------------------------------------------------------------------------
# Dosya deposu (tasarım TK22, §4.4.7, §5.2.8; plan F1b-3 "Dosya deposu")
# ---------------------------------------------------------------------------
class AttachmentSensitivity(models.TextChoices):
    """Ekin hassasiyeti (tasarım §5.2.8); özel nitelikli ekin okunması erişim günlüğüne düşer."""

    NORMAL = "NORMAL", "Normal"
    OZEL_NITELIKLI = "OZEL_NITELIKLI", "Özel nitelikli"


class Attachment(models.Model):
    """Dosya deposundaki bir ekin satırı (tasarım §5.2.8, §4.4.4 "Dosya anahtarı", §5.3 "Dosyalar").

    Dosya `dosyalar/<stored_name>`'de dosya başına rastgele anahtarla AES-256-GCM şifreli durur;
    kabı `shared.dosya_sifreleme`, yazım sırası ve okuma `services.dosya_deposu`'ndadır (tek yazarı
    odur). F1b'de ek ucu ve ekranı yoktur; ilk sahip F1c'de `GeneratedDocument`'tır (plan F1b-3).

    ALANLAR:

    * `stored_name`: `uuid4().hex` (32 küçük onaltılık hane, uzantısız). `UUIDField` DEĞİLDİR:
      ORM ile ham SQL aynı metni görmeli; AAD ve dosya adı bu metnin ASCII baytlarıdır.
    * `original_name`: kullanıcının verdiği dosya adı; kişi adı taşıyabilir, şifrelidir (§5.3).
    * `key_wrap`: dosya anahtarının sarmalı, base64(nonce 12 ‖ şifreli anahtar 32 ‖ etiket 16) =
      80 karakterlik metin. DEK yenilemesi (TK12, F4) dosyaya dokunmadan bunu yeniler.
    * `sha256`, `size`: AÇIK içeriğin özeti ve boyu (OYS `file_storage.py` AYNEN); manifesto onları
      bu açık sütunlardan DEK'siz alır (plan F1b-3 "Kap ve manifesto").
    * `mime`: imza baytından belirlenen tür (kullanıcının sözü değil). Boyu OYS'deki gibi 100'dür:
      F1c'nin DOCX ve XLSX adları 64'e sığmaz.
    * `owner_type`, `owner_id`: genel bağ (§5.2.10). `owner_type` kayıtlı bir model etiketidir
      (`okul.SchoolYear` biçimi; küme `services.dosya_deposu`'nda, F1b'de boş); `contenttypes`
      kimlikleri kurulumdan kuruluma değişeceği için kullanılmaz. `owner_id`
      `denetim_izi.kimlik_metni` biçimindedir.
    * `uploaded_by`: yazan hesap; `SISTEM` yazarında boştur.
    * `retention_until`, `purged_at`: KVKK saklama sınırı ve imha anı; imhanın kendisi F4-F6'dadır.

    SİLİNMEZ (tasarım §5 O1; altın kural 4): `delete()` ve toplu silme `DeletionNotAllowed`
    yükseltir; `_base_manager` da `objects`'tir (`base_manager_name`), düz yöneticiden silinemez.
    `_raw_delete` bu yolla kapanmaz; onu izsiz yazım ve tek yazar taramaları yakalar.
    `BaseModel`'in yumuşak silmesi ve `updated_at`'i alınmaz. Depo tek yazımlıdır: KVKK
    imhasında dosya silinir, satır `purged_at` ile kalır; `key_wrap` ve `original_name` boşalır
    (anahtar imhası). Canlı satırda ikisi doludur, imhalı satırda ikisi boştur (veritabanı kısıtı).

    DENETİM İZİ (tasarım §4.6.2; plan F1b-3 "Dosya deposu"): her yazma satırla AYNI işlemde iz satırı
    yazar. İçerik MAC'i `IZ_OZET_ALANLARI`'nı kapsar. `original_name` ve `key_wrap` MAC DIŞIDIR
    (`IZ_MAC_DISI_ALANLARI`; §4.6.2 "imha edilen dosya"): imhada boşalırlar, MAC'te kalsalardı
    anahtara erişen biri dar uzaylı dosya adını aday sözlüğüyle geri bulabilirdi; `key_wrap` DEK
    yenilemesinde de değişir ve kendini AES-GCM etiketiyle doğrular. Değeri satıra girenler kişisiz
    alanlardır (`IZ_DEGER_ALANLARI`); özet değere girmez. İmha `purged_at` üzerinden durum geçişidir
    (`IZ_DURUM_ALANLARI`).
    """

    #: Denetim izinde önce/sonra değeri yazılabilen kişisiz alanlar (tasarım §4.6.2).
    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "mime",
        "size",
        "sensitivity",
        "retention_until",
        "owner_type",
        "owner_id",
        "uploaded_at",
        "purged_at",
    )
    #: İçerik MAC'ine giren alanlar (plan F1b-3 "Dosya deposu"; kimlik hariç).
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "stored_name",
        "sha256",
        "mime",
        "size",
        "sensitivity",
        "retention_until",
        "owner_type",
        "owner_id",
        "uploaded_by",
        "uploaded_at",
        "purged_at",
    )
    #: İçerik MAC'inin DIŞINDAKİ alanlar: imhada boşalanlar (tasarım §4.6.2; belge dizesi).
    IZ_MAC_DISI_ALANLARI: ClassVar[tuple[str, ...]] = ("original_name", "key_wrap")
    #: Durum alanı: imha (§4.6.2 kural 3; ayrı `DURUM` satırı).
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("purged_at",)

    stored_name = models.CharField("depo adı", max_length=32, unique=True)
    original_name = EncryptedCharField("özgün dosya adı", max_length=255, blank=True, default="")
    key_wrap = models.CharField("dosya anahtarı sarmalı", max_length=80, blank=True, default="")
    sha256 = models.CharField("açık içeriğin sha256'sı", max_length=64)
    mime = models.CharField("tür", max_length=100)
    size = models.PositiveBigIntegerField("açık boyut (bayt)")
    sensitivity = models.CharField(
        "hassasiyet",
        max_length=16,
        choices=AttachmentSensitivity.choices,
        default=AttachmentSensitivity.NORMAL,
    )
    retention_until = models.DateField("saklama sınırı", null=True, blank=True)
    owner_type = models.CharField("sahip kaydın modeli", max_length=64)
    owner_id = models.CharField("sahip kaydın kimliği", max_length=64)
    uploaded_by = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="yükleyen hesap",
    )
    uploaded_at = models.DateTimeField("yükleme anı", default=timezone.now)
    purged_at = models.DateTimeField("imha anı", null=True, blank=True)

    objects = _NoDeleteQuerySet.as_manager()

    class Meta:
        verbose_name = "ek"
        verbose_name_plural = "ekler"
        ordering = ["uploaded_at", "id"]
        base_manager_name = "objects"
        indexes = [
            models.Index(fields=["owner_type", "owner_id"], name="okul_attachment_sahip_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(sensitivity__in=AttachmentSensitivity.values),
                name="ck_attachment_sensitivity",
            ),
            # Canlı satırda sarmal ve ad dolu, imhalı satırda ikisi de boş (belge dizesi).
            models.CheckConstraint(
                condition=models.Q(purged_at__isnull=False, key_wrap="", original_name="")
                | (
                    models.Q(purged_at__isnull=True)
                    & ~models.Q(key_wrap="")
                    & ~models.Q(original_name="")
                ),
                name="ck_attachment_purged_fields",
            ),
            # Biçimleri servis ve okuyucular denetler; SQLite `max_length`'i zorlamaz.
            models.CheckConstraint(
                condition=models.Q(Exact(Length("stored_name"), 32)),
                name="ck_attachment_stored_name",
            ),
            models.CheckConstraint(
                condition=models.Q(Exact(Length("sha256"), 64)), name="ck_attachment_sha256"
            ),
            # Boş dosya eklenemez (`shared.dosya_sifreleme.tur_belirle`).
            models.CheckConstraint(condition=models.Q(size__gt=0), name="ck_attachment_size"),
            # Sahipsiz ek yoktur (§5.2.10 genel bağ).
            models.CheckConstraint(
                condition=~models.Q(owner_type="") & ~models.Q(owner_id=""),
                name="ck_attachment_owner",
            ),
        ]

    def __str__(self) -> str:
        # Özgün ad şifreli ve kişi adı taşıyabilir: temsil depo adıdır.
        return f"Ek {self.stored_name}"

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        raise DeletionNotAllowed(
            "Ek kaydı silinmez; imhada `purged_at` ile kalır (tasarım §4.4.7)."
        )
