"""`oab` uçlarının serileştiricileri."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.oab.models import OabTerm
from apps.oab.services import donem_kilidi
from apps.okul.models import SchoolYear


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
