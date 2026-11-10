"""`oab` uçlarının serileştiricileri."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.oab.models import OabPerson, OabTerm, PersonKind, PersonStatus
from apps.oab.models.kisi import KISI_ADI_MAX
from apps.oab.services import donem_kilidi
from apps.okul.models import PARENT_NAME_MAX, Personnel, SchoolYear
from apps.okul.serializers import CorruptFieldsMixin


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
