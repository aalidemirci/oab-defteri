"""`okul` DRF serializer'ları — doğrulama + normalize burada, yazma serviste.

Elle giriş, içe aktarmayla AYNI normalize edicilerden geçer (`apps.okul.normalize`).
Hatalar Türkçedir (`{code, message, fields}` sözleşmesi). Öğrenci ve şube serileştiricileri
F1b 5. adımda öğrenci tarafıyla söküldü (tasarım §5.1 ALMA).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from django.db.models import Model
from django.utils import timezone
from rest_framework import serializers
from rest_framework.fields import empty

from apps.okul import selectors
from apps.okul.models import (
    DATA_CONTROLLER_TEXT_MAX,
    STUDENT_COUNT_MAX,
    CanteenMode,
    Holiday,
    HolidayKind,
    MemberKind,
    Personnel,
    SchoolConfig,
    SchoolLevel,
    SchoolTerm,
    SchoolYear,
    SettlementType,
    StaffingMode,
)
from apps.okul.services import calendar as calendar_service
from apps.okul.services import setup as setup_service
from shared import crypto


class _ServiseBirakanMetin(serializers.CharField):
    """`servise_birakan_metin`'in alanı: JSON `null` da boş değerdir, servise `""` gider (bağımsız
    denetim bulgusu: `allow_null` olmadan null, F-6'nın kaldırdığı "Bu alan boş bırakılmamalı."
    iletisini alıyordu). Null varsayılana da dönmez: kurulumda null tanıtıcı "Tanıtıcı boş olamaz."
    alır."""

    def run_validation(self, data: Any = empty) -> Any:
        return super().run_validation("" if data is None else data)


def servise_birakan_metin(*, kirp: bool = False, **secenekler: Any) -> serializers.CharField:
    """Boş, gönderilmemiş ya da null değeri servise bırakan metin alanı (orkestratör maddesi F-6).

    Hesap uçlarında (ilk program yöneticisi hesabı, hesap açma, parola sıfırlama) DRF'nin genel
    iletisi ("Bu alan boş bırakılmamalı.", "Bu alan zorunlu.") sözlükte yoktur ve alan adı olmadan
    anlamsızdır: boş değer servisin kurallarına gider, ret servisin Türkçe iletisidir
    (`hesap_kurallari`: "Tanıtıcı boş olamaz.", "Hesap sahibinin adı-soyadı boş olamaz.", "Parola en
    az 8 karakter olmalıdır."; rolde "Geçerli bir rol seçin.") — boşlukla doldurulmuş değerle aynı
    ileti. Aile kalıbı `views.BackupRestoreRequestSerializer`'ınkidir (`required=False,
    allow_blank=True, default=""`). Değer varsayılan olarak kırpılmaz: tanıtıcıyı ve ad-soyadı servis
    kırpar, parola hiç kırpılmaz; `kirp` yalnız kod değerleri (rol) içindir.

    Metin olmayan değer (liste, sözlük, mantıksal değer) bu kalıbın dışındadır: DRF'nin alan
    iletisini alır (ön yüz yalnız metin gönderir; açık kalan).
    """
    secenekler.setdefault("default", "")
    return _ServiseBirakanMetin(
        required=False, allow_blank=True, trim_whitespace=kirp, **secenekler
    )


#: Okul kartının iletileri — ön yüzle BİREBİR aynıdır (`frontend/src/modules/okul/okulBilgileri.ts`).
OKUL_ADI_ZORUNLU = "Okul adı zorunludur."
IL_ZORUNLU = "İl zorunludur."
ILCE_ZORUNLU = "İlçe zorunludur."
KURUM_KODU_ZORUNLU = "Kurum kodu zorunludur."
KURUM_KODU_GECERSIZ = "Kurum kodu altı haneli bir sayıdır."
KADEME_ZORUNLU = "En az bir kademe seçin."
KADEME_GECERSIZ = "Geçerli bir kademe seçin."
MEVCUT_ZORUNLU = "Öğrenci mevcudu zorunludur."
MEVCUT_GECERSIZ = "Öğrenci mevcudu 0 ile 99999 arasında bir tam sayıdır."
MEVCUT_TARIHI_ZORUNLU = "Mevcudun tarihi zorunludur."
MEVCUT_TARIHI_GELECEKTE = "Mevcudun tarihi bugünden sonra olamaz."
YERLESIM_ZORUNLU = "Yerleşim türünü seçin."
KANTIN_ZORUNLU = "Kantin işletme biçimini seçin."
PERSONEL_ZORUNLU = "Personel çalıştırma biçimini seçin."
SECENEK_GECERSIZ = "Geçerli bir seçenek seçin."
TARIH_GECERSIZ = "Geçerli bir tarih girin."
DEMIRBAS_ONAYI_ZORUNLU = "Program yalnız okul demirbaşı bilgisayara kurulur; onay zorunludur."
VERI_SORUMLUSU_UZUN = f"Veri sorumlusu en çok {DATA_CONTROLLER_TEXT_MAX} karakter olabilir."


class _Kademeler(serializers.Field):  # type: ignore[type-arg]  # değer listesi; Any davranışı
    """`levels`: `SchoolLevel` değerlerinin listesi — tekrarlar atılır, `SchoolLevel` sırasına dizilir.

    Liste olmayan değer (null dahil) ya da tanınmayan eleman `KADEME_GECERSIZ`, boş liste
    `KADEME_ZORUNLU` alır. Normalleştirme sessizdir (ön yüz de kanonik sırayla gönderir).
    """

    default_error_messages = {"invalid": KADEME_GECERSIZ, "empty": KADEME_ZORUNLU}

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("error_messages", {}).setdefault("null", KADEME_GECERSIZ)
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> list[str]:
        if not isinstance(data, list) or any(
            not isinstance(deger, str) or deger not in SchoolLevel.values for deger in data
        ):
            self.fail("invalid")
        if not data:
            self.fail("empty")
        return setup_service.normalize_levels(data)

    def to_representation(self, value: Any) -> list[str]:
        return list(value) if isinstance(value, list) else []


def _secenek(choices: Any, bos_iletisi: str) -> serializers.ChoiceField:
    """Okul kartının enum alanı: boş ve null `bos_iletisi`, tanınmayan değer `SECENEK_GECERSIZ`."""
    return serializers.ChoiceField(
        choices=choices,
        required=False,
        allow_blank=True,
        error_messages={"invalid_choice": SECENEK_GECERSIZ, "null": bos_iletisi},
    )


class SchoolConfigSerializer(serializers.ModelSerializer[SchoolConfig]):
    """Okul kartı — sihirbazın 2. adımı ve Ayarlar → Okul Bilgileri'nin ortak sözleşmesi.

    Okul adı, il, ilçe, kurum kodu, en az bir kademe, öğrenci mevcudu ve tarihi, yerleşim
    türü, kantin ve personel çalıştırma biçimi ve demirbaş onayı kurulumun ikinci adımında
    ZORUNLUDUR (`setup/complete/` kapısı: `services.setup.missing_school_fields`; plan F1b-4
    kararları). Aynı zorunluluk burada da uygulanır, ama yalnız alan gövdede VARSA: kısmi
    PUT gönderilmeyen alana dokunmaz (künyeyi silmez), gönderilen zorunlu alan ise
    boşaltılamaz (aile kuralı, tasarım §5.1). Aksi hâlde kurulum bittikten sonra Okul
    Bilgileri ekranından bir zorunlu alan sessizce geri alınabilirdi (tamamlanmış ama okul
    adımı eksik kurulum). Müdür adı, kampüs işareti, açılış tarihi ve veri sorumlusu isteğe
    bağlıdır; açılış tarihi ve veri sorumlusu boşaltılabilir (veri sorumlusu boşken aktarım
    ekranları uyarır, aktarımı engellemez; F1b 5. adım).

    Öğrenci mevcudu ile tarihi birlikte gönderilir (DB kısıtı da ikisini birlikte ister);
    biri gövdede öteki yoksa eksik olanın "zorunludur" iletisi döner. Mevcudun tarihi
    bugünden (Europe/Istanbul) sonra olamaz. Metin alanları kırpılarak kaydedilir. Kaldırılan
    `has_prep_class` (F1b 5. adımda düştü), `kademe` ve `kisa_ad` gövdede gelirse yok sayılır.

    İletiler sihirbazın istemci denetimiyle BİREBİR aynıdır
    (`frontend/src/modules/okul/okulBilgileri.ts`).
    """

    institution_code = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={"invalid": KURUM_KODU_GECERSIZ, "null": KURUM_KODU_ZORUNLU},
    )
    levels = _Kademeler(required=False)
    student_count = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=STUDENT_COUNT_MAX,
        error_messages={
            "invalid": MEVCUT_GECERSIZ,
            "min_value": MEVCUT_GECERSIZ,
            "max_value": MEVCUT_GECERSIZ,
            "max_string_length": MEVCUT_GECERSIZ,
            "null": MEVCUT_ZORUNLU,
        },
    )
    student_count_as_of = serializers.DateField(
        required=False, error_messages={"invalid": TARIH_GECERSIZ, "null": MEVCUT_TARIHI_ZORUNLU}
    )
    settlement_type = _secenek(SettlementType.choices, YERLESIM_ZORUNLU)
    canteen_mode = _secenek(CanteenMode.choices, KANTIN_ZORUNLU)
    staffing_mode = _secenek(StaffingMode.choices, PERSONEL_ZORUNLU)
    opened_on = serializers.DateField(
        required=False, allow_null=True, error_messages={"invalid": TARIH_GECERSIZ}
    )
    demirbas_no = serializers.CharField(
        max_length=64,
        required=False,
        allow_blank=True,
        error_messages={"max_length": "Bilgisayarın demirbaş no'su en çok 64 karakter olabilir."},
    )
    data_controller_text = serializers.CharField(
        max_length=DATA_CONTROLLER_TEXT_MAX,
        required=False,
        allow_blank=True,
        error_messages={"max_length": VERI_SORUMLUSU_UZUN},
    )

    class Meta:
        model = SchoolConfig
        fields = [
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
            "setup_completed",
        ]
        read_only_fields = ["setup_completed"]

    def validate_school_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError(OKUL_ADI_ZORUNLU)
        return value

    def validate_province(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError(IL_ZORUNLU)
        return value

    def validate_district(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError(ILCE_ZORUNLU)
        return value

    def validate_institution_code(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError(KURUM_KODU_ZORUNLU)
        if not setup_service.institution_code_valid(value):
            raise serializers.ValidationError(KURUM_KODU_GECERSIZ)
        return value

    def validate_student_count_as_of(self, value: date) -> date:
        if value > timezone.localdate():
            raise serializers.ValidationError(MEVCUT_TARIHI_GELECEKTE)
        return value

    def validate_settlement_type(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError(YERLESIM_ZORUNLU)
        return value

    def validate_canteen_mode(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError(KANTIN_ZORUNLU)
        return value

    def validate_staffing_mode(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError(PERSONEL_ZORUNLU)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Mevcut ile tarihi birlikte gelir: biri gövdedeyse öteki de olmalı (sınıf yorumu)."""
        sayi_var, tarih_var = "student_count" in attrs, "student_count_as_of" in attrs
        if sayi_var and not tarih_var:
            raise serializers.ValidationError({"student_count_as_of": [MEVCUT_TARIHI_ZORUNLU]})
        if tarih_var and not sayi_var:
            raise serializers.ValidationError({"student_count": [MEVCUT_ZORUNLU]})
        return attrs

    def validate_demirbas_onayi(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError(DEMIRBAS_ONAYI_ZORUNLU)
        return value


class RoadmapUpdateSerializer(serializers.Serializer[dict[str, Any]]):
    """`POST setup/roadmap/` — `{item, done}` (madde işareti) YA DA `{hidden}` (kartı gizle)."""

    item = serializers.CharField(required=False)
    done = serializers.BooleanField(required=False)
    hidden = serializers.BooleanField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        madde, isaret, gizle = ("item" in attrs), ("done" in attrs), ("hidden" in attrs)
        madde_istegi = madde and isaret and not gizle
        gizleme_istegi = gizle and not madde and not isaret
        if not (madde_istegi or gizleme_istegi):
            raise serializers.ValidationError(
                "Ya bir maddeyi (item + done) ya da kartın görünürlüğünü (hidden) gönderin."
            )
        return attrs


class RecoveryKeyRequestSerializer(serializers.Serializer[dict[str, Any]]):
    """Gövdesinde kurtarma anahtarı taşıyan güvenlik uçlarının ortak gövdesi.

    `security/recovery-key/pdf/` (kurtarma anahtarı belgesi; katalog dışı program
    belgesi, tasarım §9.7) ve `security/recovery-key/confirm/`
    (saklandığının doğrulanması) kullanır. Anahtar yalnız gövdede taşınır. Üst
    sınır bir savunmadır (anahtar 32 karakter + 7 tire); sınır aşımı iletisi
    değeri yankılamaz.
    """

    recovery_key = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        error_messages={
            "required": "Kurtarma anahtarı gönderilmedi.",
            "blank": "Kurtarma anahtarı gönderilmedi.",
            "max_length": "Kurtarma anahtarı hatalı.",
        },
    )


class RecoveryKeyPdfRequestSerializer(RecoveryKeyRequestSerializer):
    """`POST security/recovery-key/pdf/` gövdesi (`RecoveryKeyRequestSerializer`)."""


class SchoolYearSerializer(serializers.ModelSerializer[SchoolYear]):
    class Meta:
        model = SchoolYear
        fields = ["id", "name", "start_date", "end_date", "is_active"]
        read_only_fields = ["is_active"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_date": "Bitiş tarihi başlangıçtan sonra olmalıdır."}
            )
        return attrs


class SchoolTermSerializer(serializers.ModelSerializer[SchoolTerm]):
    name = serializers.CharField(read_only=True)

    class Meta:
        model = SchoolTerm
        fields = ["id", "school_year", "sequence", "name", "start_date", "end_date"]
        read_only_fields = fields


class SchoolTermConfigurationSerializer(serializers.Serializer[dict[str, Any]]):
    first_term_end = serializers.DateField()
    second_term_start = serializers.DateField()


# ---------------------------------------------------------------------------
# Kapalı günler (tasarım §5.1 `Holiday`)
# ---------------------------------------------------------------------------

# `Any` değerli: DRF stub'ı `str | _StrPromise` ister, `dict` değişmez (invariant) türdür.
_DATE_ERRORS: dict[str, Any] = {
    "invalid": "Geçerli bir tarih girin.",
    "required": "Tarih seçilmelidir.",
    "null": "Tarih seçilmelidir.",
}

_YEAR_RANGE_MESSAGE = (
    f"Yıl {calendar_service.MIN_YEAR} ile {calendar_service.MAX_YEAR} arasında olmalıdır."
)
_YEAR_ERRORS: dict[str, Any] = {
    "invalid": "Yıl dört haneli bir sayı olmalıdır.",
    "min_value": _YEAR_RANGE_MESSAGE,
    "max_value": _YEAR_RANGE_MESSAGE,
}


def _year_field(*, required: bool) -> serializers.IntegerField:
    return serializers.IntegerField(
        required=required,
        min_value=calendar_service.MIN_YEAR,
        max_value=calendar_service.MAX_YEAR,
        error_messages=_YEAR_ERRORS,
    )


class HolidaySerializer(serializers.ModelSerializer[Holiday]):
    """Kapalı gün kaydı. `is_estimated` salt okunurdur: yalnız tohumlama yazar,
    elle girilen kayıt kesin tarih sayılır.

    Teklik (ad + başlangıç) servistedir ve Türkçe reddeder; DRF'nin koşullu
    kısıttan türettiği İngilizce alan adlı doğrulayıcı `validators = []` ile kapalıdır.
    """

    name = serializers.CharField(
        max_length=128,
        error_messages={
            "blank": "Ad yazılmalıdır.",
            "required": "Ad yazılmalıdır.",
            "max_length": "Ad en çok 128 karakter olabilir.",
        },
    )
    start_date = serializers.DateField(error_messages=_DATE_ERRORS)
    end_date = serializers.DateField(error_messages=_DATE_ERRORS)
    kind = serializers.ChoiceField(
        choices=HolidayKind.choices,
        default=HolidayKind.SCHOOL_BREAK,
        error_messages={"invalid_choice": "Geçerli bir tür seçin."},
    )

    class Meta:
        model = Holiday
        fields = ["id", "name", "start_date", "end_date", "kind", "is_estimated"]
        read_only_fields = ["is_estimated"]
        validators: list[Any] = []

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end:
            if end < start:
                raise serializers.ValidationError(
                    {"end_date": "Bitiş tarihi başlangıçtan önce olamaz."}
                )
            if (end - start).days + 1 > calendar_service.MAX_SPAN_DAYS:
                raise serializers.ValidationError({"end_date": calendar_service.span_message()})
        return attrs


class HolidayListQuerySerializer(serializers.Serializer[dict[str, Any]]):
    """`GET holidays/?year=` — yıl verilmezse bütün kayıtlar."""

    year = _year_field(required=False)


class HolidaySeedRequestSerializer(serializers.Serializer[dict[str, Any]]):
    """`POST holidays/seed/` — yıl verilmezse bugünün takvim yılı (`localdate`)."""

    year = _year_field(required=False)


class CorruptFieldsMixin(serializers.Serializer[Any]):
    """Çözülemeyen şifreli alanı `null` verir, kayda `bozuk_alanlar` listesini ekler (D48).

    Kilit açıkken çözülemeyen değer `CorruptField` işaretidir (tasarım TK8 (3), §13
    D48; plan F1b-1 "API'de alan boş gelir, kayıtta bozuk_alanlar listesi durur").
    İşaret metin değildir; DRF onu boş dizeye çevirirdi, bu da "veri yok" ile
    "veri okunamadı"yı karıştırırdı. Şifreli alanlardan türeyen alanlar
    (`DERIVED_FROM`: ör. ad-soyad) kaynaklarından biri bozuksa `null` olur. Liste
    alan ADLARINI taşır, değer taşımaz; panodaki bütünlük kartı ön yüz commit'indedir.
    """

    #: Türeyen alan → şifreli kaynak alanlar.
    DERIVED_FROM: dict[str, tuple[str, ...]] = {"full_name": ("first_name", "last_name")}

    def to_representation(self, instance: Any) -> Any:
        veri = super().to_representation(instance)
        bozuk = crypto.corrupt_fields_of(instance) if isinstance(instance, Model) else []
        for alan in bozuk:
            if alan in veri:
                veri[alan] = None
        for turemis, kaynaklar in self.DERIVED_FROM.items():
            if turemis in veri and any(k in bozuk for k in kaynaklar):
                veri[turemis] = None
        veri["bozuk_alanlar"] = bozuk
        return veri


class PersonnelSerializer(CorruptFieldsMixin, serializers.ModelSerializer[Personnel]):
    """Personel sicili. Unvan ve branş YOKTUR (tasarım §8.4).

    `is_active` ve `left_at` salt okunurdur: ayrılış yalnız `personnel/<pk>/leave/`
    ayrılış yolundan ya da ayrılış havuzu kararından geçer (kancalar; kayıt
    silinmez — tasarım §5.1 `Personnel`); gövdeyle gönderilen değer yok sayılır.
    `leave_candidate_since` salt okunurdur: doluysa kişi ayrılış havuzunda karar
    bekliyor demektir (yalnız e-Okul aktarımı yazar).
    """

    full_name = serializers.CharField(read_only=True)
    member_kind = serializers.ChoiceField(
        choices=MemberKind.choices,
        default=MemberKind.OGRETMEN,
        error_messages={
            "invalid_choice": (
                "Geçerli bir görev türü seçin (öğretmen, yönetici ya da diğer personel)."
            )
        },
    )

    class Meta:
        model = Personnel
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "member_kind",
            "is_active",
            "left_at",
            "leave_candidate_since",
        ]
        read_only_fields = ["is_active", "left_at", "leave_candidate_since"]


class ImportRequestSerializer(serializers.Serializer[dict[str, Any]]):
    """İçe aktarma girdisi: dosya (e-Okul .xls / şablon .xlsx / .csv) VEYA pano metni.

    Aktarım kimseyi ayırmaz: listede olmayanlar ayrılış havuzuna
    girer, karar `leave-pool/resolve/` ile verilir. Eski personel seçeneği
    `mark_left_ids` ve öğrenci aktarımının `full_list` onayı ("Bu dosya okulun tam
    listesidir"; öğrenci tarafıyla F1b 5. adımda söküldü) KALDIRILDI; gönderilirse yok sayılır.
    """

    file = serializers.FileField(required=False)
    text = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        has_file = attrs.get("file") is not None
        has_text = bool(str(attrs.get("text", "")).strip())
        if has_file == has_text:  # ikisi birden veya hiçbiri
            raise serializers.ValidationError(
                "Dosya (file) veya yapıştırılan metin (text) alanlarından tam olarak biri gerekli."
            )
        return attrs


class ParentImportRequestSerializer(serializers.Serializer[dict[str, Any]]):
    """Veli listesi aktarımının girdisi: YALNIZ dosya (.xlsx şablon, .xls, .csv; tasarım §8.4).

    Pano yolu yoktur: veli listesi okulun doldurduğu şablondan gelir (T5); gövdede `text`
    gelirse yok sayılır.
    """

    file = serializers.FileField(
        error_messages={
            "required": "Veli listesi dosyasını seçin.",
            "null": "Veli listesi dosyasını seçin.",
            "invalid": "Veli listesi dosyasını seçin.",
            "empty": "Seçilen dosya boş.",
        }
    )


class PersonnelMergeSerializer(serializers.Serializer[dict[str, Any]]):
    """`POST personnel/<pk>/merge/` — `<pk>` (kaynak) `into_id` (hedef) kaydına birleşir."""

    into_id = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "Birleştirilecek hedef kayıt seçilmelidir.",
            "invalid": "Hedef kayıt kimliği sayısal olmalıdır.",
        },
    )


# ---------------------------------------------------------------------------
# Ayrılış havuzu (tasarım §5.1 `Personnel`, §13 D30) — AD İÇERİR: yalnız yönetim yüzeyi
# ---------------------------------------------------------------------------


def _pool_run(person: Personnel) -> dict[str, Any] | None:
    """Kişiyi havuza ekleyen aktarım: dosya adı (yapıştırılan listede boş) + gün."""
    run = selectors.leave_pool_run(person)
    if run is None:
        return None
    zaman = run.finished_at or run.started_at
    return {
        "id": run.pk,
        "file_name": run.file_name,
        "date": timezone.localdate(zaman).isoformat(),
    }


class LeavePoolPersonnelSerializer(CorruptFieldsMixin, serializers.ModelSerializer[Personnel]):
    """Havuzdaki öğretmen / diğer personel + "olası aynı kişi" adayları.

    Adaylar `context["similar"]`'dan (kimlik → `SimilarCandidate`) okunur; birleştirme
    `personnel/<id>/merge/ {into_id: aday}` ile yapılır (havuzdaki kişi kaynaktır).
    Her aday `reason` (eşleşme gerekçesi, `MatchReason` kodu), `member_kind` ve
    `created_on` (sicile eklendiği gün) taşır: ekran adayın NEDEN aday olduğunu
    yazar, onay diyaloğu iki kaydı ayırt eden bilgiyi gösterir (§13 D30).
    """

    full_name = serializers.CharField(read_only=True)
    run = serializers.SerializerMethodField()
    similar = serializers.SerializerMethodField()

    class Meta:
        model = Personnel
        fields = [
            "id",
            "full_name",
            "member_kind",
            "leave_candidate_since",
            "run",
            "similar",
        ]
        read_only_fields = fields

    def get_run(self, obj: Personnel) -> dict[str, Any] | None:
        return _pool_run(obj)

    def get_similar(self, obj: Personnel) -> list[dict[str, Any]]:
        adaylar: dict[int, list[selectors.SimilarCandidate]] = self.context.get("similar", {})
        return [
            {
                "id": aday.person.pk,
                "full_name": aday.person.full_name,
                "member_kind": aday.person.member_kind,
                "created_on": aday.created_on.isoformat(),
                "reason": str(aday.reason),
            }
            for aday in adaylar.get(obj.pk, [])
        ]


_POOL_IDS_ERRORS: dict[str, Any] = {
    "not_a_list": "Kişi kimlikleri liste olarak gönderilmelidir.",
}


def _pool_ids_field() -> serializers.ListField:
    return serializers.ListField(
        child=serializers.IntegerField(
            min_value=1, error_messages={"invalid": "Kişi kimliği sayısal olmalıdır."}
        ),
        required=False,
        default=list,
        error_messages=_POOL_IDS_ERRORS,
    )


class LeavePoolDecisionSerializer(serializers.Serializer[dict[str, Any]]):
    """Bir kişi türü için karar: `leave` (ayrıldı olarak işaretle) / `keep` (aktif kalsın)."""

    leave = _pool_ids_field()
    keep = _pool_ids_field()


class LeavePoolResolveSerializer(serializers.Serializer[dict[str, Any]]):
    """`POST leave-pool/resolve/` — `{personnel: {leave, keep}}`.

    Çakışma (aynı kişi iki listede), boş karar ve havuzda olmayan kişi
    denetimleri serviste, TEK işlemdedir (`persons.resolve_leave_pool`).
    """

    personnel = LeavePoolDecisionSerializer(required=False)
