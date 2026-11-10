"""`oab` uçlarının serileştiricileri."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.oab.models import (
    BoardDecision,
    DropKind,
    ElectedBy,
    EligibilityBar,
    EligibilityBarBasis,
    GeneralAssembly,
    MembershipRole,
    OabPerson,
    OabTerm,
    OrganMembership,
    OrganType,
    PersonKind,
    PersonStatus,
    Representation,
    SeatGroup,
    SeatType,
)
from apps.oab.models.kisi import KISI_ADI_MAX
from apps.oab.models.uyelik import MEM_ONAY_NO_MAX
from apps.oab.services import donem_kilidi
from apps.okul.models import PARENT_NAME_MAX, Personnel, SchoolYear
from apps.okul.serializers import CorruptFieldsMixin
from shared.crypto import has_corrupt


class OabTermSerializer(serializers.ModelSerializer[OabTerm]):
    """Birlik dönemi: kural sürümü salt okunur satırıyla (plan F1c kararları)."""

    kural_paketi = serializers.SerializerMethodField()
    kural_kopyasi_tutuyor = serializers.SerializerMethodField()

    class Meta:
        model = OabTerm
        fields = [
            "id",
            "name",
            "school_year",
            "start_date",
            "end_date",
            "status",
            "program_start_date",
            "opened_by_assembly",
            "kural_paketi",
            "kural_kopyasi_tutuyor",
        ]

    def get_kural_paketi(self, donem: OabTerm) -> dict[str, Any]:
        return {"paket": donem.rule_package.package, "rev": donem.rule_package.rev}

    def get_kural_kopyasi_tutuyor(self, donem: OabTerm) -> bool:
        return donem_kilidi.kural_kopyasi_tutuyor(donem)


class OabTermAcilisSerializer(serializers.Serializer[dict[str, Any]]):
    """İlk birlik döneminin açılışı (tasarım §7.9 adım 1)."""

    name = serializers.CharField(max_length=40, trim_whitespace=True)
    school_year = serializers.PrimaryKeyRelatedField(queryset=SchoolYear.objects.all())
    start_date = serializers.DateField()
    program_start_date = serializers.DateField(required=False, allow_null=True)


# ---------------------------------------------------------------------------
# Birlik kişileri (tasarım §5.2.2; plan F1c-4)
# ---------------------------------------------------------------------------
#: Programdan önceki seçilme sayısının üst sınırı (alan `PositiveSmallIntegerField`).
_SAYAC_UST = 32767


class OabPersonSerializer(CorruptFieldsMixin, serializers.ModelSerializer[OabPerson]):
    """Birlik kişisi (okuma). T.C. kimlik no ve telefon yoktur (K9; tasarım §5.2.2).

    Çözülemeyen ad `null` gelir, kayıtta `bozuk_alanlar` durur (D48). Kör indeks dönmez.
    """

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = OabPerson
        fields = [
            "id",
            "kind",
            "first_name",
            "last_name",
            "full_name",
            "is_parent",
            "adult_declared",
            "is_principal",
            "personnel",
            "external_yk_terms",
            "external_dk_chair_terms",
            "status",
        ]
        read_only_fields = fields


def _ad_alani() -> serializers.CharField:
    return serializers.CharField(max_length=KISI_ADI_MAX, trim_whitespace=True)


def _sayac_alani() -> serializers.IntegerField:
    """Programdan önceki seçilme sayısı; boş "bilinmiyor"dur."""
    return serializers.IntegerField(
        min_value=0, max_value=_SAYAC_UST, required=False, allow_null=True
    )


class _AyniKisiDegilMixin(serializers.Serializer[dict[str, Any]]):
    """ "Olası aynı kişi" sorusunun onayı (tasarım §13 D30)."""

    ayni_kisi_degil = serializers.BooleanField(required=False, default=False)


class OabPersonCreateSerializer(_AyniKisiDegilMixin):
    """Elle kişi kaydı. Veli işareti verilmezse türden gelir; müdür işareti okul kartından."""

    kind = serializers.ChoiceField(choices=PersonKind.choices)
    first_name = _ad_alani()
    last_name = _ad_alani()
    is_parent = serializers.BooleanField(required=False)
    adult_declared = serializers.BooleanField(required=False, default=False)
    external_yk_terms = _sayac_alani()
    external_dk_chair_terms = _sayac_alani()


class OabPersonUpdateSerializer(_AyniKisiDegilMixin):
    """Kişi güncellemesi (PATCH): yalnız gönderilen alanlar değişir; personel bağı değişmez."""

    kind = serializers.ChoiceField(choices=PersonKind.choices, required=False)
    first_name = serializers.CharField(
        max_length=KISI_ADI_MAX, trim_whitespace=True, required=False
    )
    last_name = serializers.CharField(max_length=KISI_ADI_MAX, trim_whitespace=True, required=False)
    is_parent = serializers.BooleanField(required=False)
    adult_declared = serializers.BooleanField(required=False)
    is_principal = serializers.BooleanField(required=False)
    external_yk_terms = _sayac_alani()
    external_dk_chair_terms = _sayac_alani()
    status = serializers.ChoiceField(choices=PersonStatus.choices, required=False)


class OabPersonFromPersonnelSerializer(_AyniKisiDegilMixin):
    """Personelden kopya: hangi personel."""

    personnel = serializers.PrimaryKeyRelatedField(queryset=Personnel.objects.all())


class OabPersonFromParentSerializer(_AyniKisiDegilMixin):
    """Veli listesinden kopya: velinin adı (kör indeksle aranır; liste dökülmez)."""

    full_name = serializers.CharField(max_length=PARENT_NAME_MAX, trim_whitespace=True)


# ---------------------------------------------------------------------------
# Organ üyelikleri (tasarım §5.2.2; plan F1c-5)
# ---------------------------------------------------------------------------
#: Bu adımda kaydı yazılan organlar (`services.uyelikler.YAZILAN_ORGANLAR`).
_YAZILAN_ORGANLAR = [
    (OrganType.YONETIM_KURULU.value, OrganType.YONETIM_KURULU.label),
    (OrganType.DENETLEME_KURULU.value, OrganType.DENETLEME_KURULU.label),
]
#: Yedek sırasının üst sınırı (alan `PositiveSmallIntegerField`).
_SIRA_UST = 32767
#: Serbest metinlerin üst sınırı (dayanak notu ve gerekçe; şifreli sütun TEXT'tir).
_NOT_UST = 1000
#: Kök neden alanının sınırı (`ComplianceJustification.root_cause`).
_KOK_NEDEN_UST = 64


class OrganMembershipSerializer(CorruptFieldsMixin, serializers.ModelSerializer[OrganMembership]):
    """Organ üyeliği (kadro okuması). Kişi adı çözülmüş gelir (bozuksa `null`).

    Kadroya GİRMEZ (plan F1c-5): görev alma engelinin dayanağı (özel nitelikli; okuması ayrı uçtadır ve
    erişim günlüğüne yazılır), düşme gerekçesi (KVKK boşaltma kümesi) ve uyarı özeti (uyarılar uyum
    satırlarındadır).
    """

    person_name = serializers.SerializerMethodField()

    class Meta:
        model = OrganMembership
        fields = [
            "id",
            "term",
            "person",
            "person_name",
            "organ",
            "assembly",
            "role",
            "seat_type",
            "seat_group",
            "votes",
            "seat_order",
            "elected_by",
            "source",
            "evidence_note",
            "representation",
            "representative_decision",
            "mem_approval_no",
            "external_assignment_start",
            "external_assignment_end",
            "status",
            "start_date",
            "end_date",
            "promoted_on",
            "promoted_by_decision",
            "drop_kind",
            "eligibility_declared_on",
            "single_birlik_declared_on",
            "expertise_required",
            "eligibility_bar",
            "eligibility_bar_found_on",
            "retained_until_assembly",
        ]
        read_only_fields = fields

    def get_person_name(self, uyelik: OrganMembership) -> str | None:
        kisi = uyelik.person
        return None if has_corrupt(kisi) else kisi.full_name


def _istege_bagli_gun() -> serializers.DateField:
    return serializers.DateField(required=False, allow_null=True)


class _GerekceMixin(serializers.Serializer[dict[str, Any]]):
    """Uyarı gerektiren kaydın gerekçesi (altın kural 3); kök neden toplu gerekçeyi bağlar."""

    gerekce = serializers.CharField(
        max_length=_NOT_UST, required=False, allow_blank=True, default=""
    )
    kok_neden = serializers.CharField(
        max_length=_KOK_NEDEN_UST, required=False, allow_blank=True, default=""
    )


class OrganMembershipCreateSerializer(_GerekceMixin):
    """Üyelik kaydı: genel kurul seçiminde aday (genel kurul bağıyla), öteki kanallarda seçilmiş."""

    term = serializers.PrimaryKeyRelatedField(queryset=OabTerm.objects.all())
    person = serializers.PrimaryKeyRelatedField(queryset=OabPerson.objects.all())
    organ = serializers.ChoiceField(choices=_YAZILAN_ORGANLAR)
    seat_type = serializers.ChoiceField(choices=SeatType.choices)
    seat_group = serializers.ChoiceField(
        choices=SeatGroup.choices, required=False, allow_blank=True, default=""
    )
    role = serializers.ChoiceField(
        choices=MembershipRole.choices, required=False, default=MembershipRole.UYE
    )
    elected_by = serializers.ChoiceField(choices=ElectedBy.choices)
    assembly = serializers.PrimaryKeyRelatedField(
        queryset=GeneralAssembly.objects.all(), required=False, allow_null=True, default=None
    )
    start_date = _istege_bagli_gun()
    votes = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    seat_order = serializers.IntegerField(
        min_value=1, max_value=_SIRA_UST, required=False, allow_null=True
    )
    evidence_note = serializers.CharField(
        max_length=_NOT_UST, required=False, allow_blank=True, default=""
    )
    mem_approval_no = serializers.CharField(
        max_length=MEM_ONAY_NO_MAX, required=False, allow_blank=True, default=""
    )
    eligibility_declared_on = _istege_bagli_gun()
    single_birlik_declared_on = _istege_bagli_gun()


class OrganMembershipUpdateSerializer(serializers.Serializer[dict[str, Any]]):
    """Üyelik güncellemesi (PATCH): kişisiz ayrıntılar; görev, durum ve koltuk ayrı akışlardadır."""

    votes = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    seat_order = serializers.IntegerField(
        min_value=1, max_value=_SIRA_UST, required=False, allow_null=True
    )
    evidence_note = serializers.CharField(max_length=_NOT_UST, required=False, allow_blank=True)
    mem_approval_no = serializers.CharField(
        max_length=MEM_ONAY_NO_MAX, required=False, allow_blank=True
    )
    eligibility_declared_on = _istege_bagli_gun()
    single_birlik_declared_on = _istege_bagli_gun()
    #: Denetleme Kurulu öğretmeninin başka kurumdaki görevlendirmesi (md. 14/6; F1c 6. adım).
    external_assignment_start = _istege_bagli_gun()
    external_assignment_end = _istege_bagli_gun()
    #: Alım komisyonunda YK üyesi olmayan üye için "uzmanlık gerektiren iş" (md. 18/1).
    expertise_required = serializers.BooleanField(required=False)


# ---------------------------------------------------------------------------
# Görev bölümü, yedek çağrısı, düşme, iptal, engel, temsilciler (plan F1c 6. adım)
# ---------------------------------------------------------------------------
#: Karar metninin üst sınırı (şifreli sütun TEXT'tir; taslak metni evrak hattında üretilir).
_KARAR_METNI_UST = 4000
#: Toplantı yerinin üst sınırı (`BoardMeeting.place`).
_YER_UST = 128


def _uyelik_alani(**kwargs: Any) -> serializers.PrimaryKeyRelatedField[OrganMembership]:
    return serializers.PrimaryKeyRelatedField(queryset=OrganMembership.objects.all(), **kwargs)


class KatilimSerializer(serializers.Serializer[dict[str, Any]]):
    """Görev bölümü toplantısında bir üyenin katılımı (katıldı · özürlü · özürsüz; neden tutulmaz)."""

    membership = _uyelik_alani()
    present = serializers.BooleanField()
    excused = serializers.BooleanField(required=False, default=False)


class _GorevBolumuMixin(_GerekceMixin):
    held_at = serializers.DateTimeField()
    place = serializers.CharField(max_length=_YER_UST, required=False, allow_blank=True, default="")
    text = serializers.CharField(
        max_length=_KARAR_METNI_UST, required=False, allow_blank=True, default=""
    )
    katilim = KatilimSerializer(many=True)


class YkGorevBolumuSerializer(_GorevBolumuMixin):
    """Yönetim kurulunun görev bölümü (md. 12/3): verilen görevler; en az biri."""

    baskan = _uyelik_alani(required=False, allow_null=True, default=None)
    baskan_yardimcisi = _uyelik_alani(required=False, allow_null=True, default=None)
    muhasip = _uyelik_alani(required=False, allow_null=True, default=None)
    sekreter = _uyelik_alani(required=False, allow_null=True, default=None)


class DkGorevBolumuSerializer(_GorevBolumuMixin):
    """Denetleme Kurulunun görev bölümü (md. 14/1) ve denetim planı tarihleri (dönem ayarı)."""

    baskan = _uyelik_alani()
    denetim_plani = serializers.ListField(
        child=serializers.DateField(), required=False, allow_null=True, default=None
    )


class YkYedekCagrisiSerializer(_GerekceMixin):
    """Yönetim kurulu yedeğinin çağrısı (md. 13/6): çağrı günü ve yedek çağırma kararı bağı."""

    promoted_on = _istege_bagli_gun()
    promoted_by_decision = serializers.PrimaryKeyRelatedField(
        queryset=BoardDecision.objects.all(), required=False, allow_null=True, default=None
    )


class DkYedekCagrisiSerializer(serializers.Serializer[dict[str, Any]]):
    """Denetleme Kurulu yedeğinin çağrısı (md. 14/6): yalnız çağrı günü (karar bağı yoktur)."""

    promoted_on = _istege_bagli_gun()


class DusmeSerializer(_GerekceMixin):
    """Üyeliğin düşmesi: tür zorunlu; serbest gerekçe isteğe bağlı (şifreli; KVKK boşaltma)."""

    drop_kind = serializers.ChoiceField(choices=DropKind.choices)
    end_date = _istege_bagli_gun()
    dropped_reason = serializers.CharField(
        max_length=_NOT_UST, required=False, allow_blank=True, default=""
    )
    #: md. 7/2: düşürme yerine olağanüstü genel kurula kadar erteleme.
    ertele = serializers.BooleanField(required=False, default=False)


class IptalSerializer(serializers.Serializer[dict[str, Any]]):
    """Yanlış üyelik kaydının iptali: gerekçe zorunlu (O1)."""

    cancel_reason = serializers.CharField(max_length=_NOT_UST, trim_whitespace=True)


class EngelSerializer(serializers.Serializer[dict[str, Any]]):
    """Görev alma engeli (hüküm alanı) ve dayanağı (özel nitelikli, şifreli) ile tespit günü."""

    eligibility_bar = serializers.ChoiceField(choices=EligibilityBar.choices)
    eligibility_bar_basis = serializers.ChoiceField(
        choices=EligibilityBarBasis.choices, required=False, allow_blank=True, default=""
    )
    eligibility_bar_found_on = _istege_bagli_gun()


class TemsilciCreateSerializer(_GerekceMixin):
    """Temsilci kaydı (tasarım "Temsil türleri"); karar bağı E03'ün karar no'sudur."""

    term = serializers.PrimaryKeyRelatedField(queryset=OabTerm.objects.all())
    person = serializers.PrimaryKeyRelatedField(queryset=OabPerson.objects.all())
    representation = serializers.ChoiceField(choices=Representation.choices)
    seat_type = serializers.ChoiceField(
        choices=SeatType.choices, required=False, default=SeatType.ASIL
    )
    start_date = _istege_bagli_gun()
    representative_decision = serializers.PrimaryKeyRelatedField(
        queryset=BoardDecision.objects.all(), required=False, allow_null=True, default=None
    )


class AlimKomisyonuCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Alım komisyonu üyesi (md. 18/1); uzmanlık işareti YK üyesi olmayan üye içindir."""

    term = serializers.PrimaryKeyRelatedField(queryset=OabTerm.objects.all())
    person = serializers.PrimaryKeyRelatedField(queryset=OabPerson.objects.all())
    expertise_required = serializers.BooleanField(required=False, default=False)
    start_date = _istege_bagli_gun()
