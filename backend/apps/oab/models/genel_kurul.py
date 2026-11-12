"""Genel kurulun asgari kaydı (plan F1c kararları; tasarım §5.2.3).

F1c yalnız F2-F3 modellerinin dayandığı kısmı kurar: dönem bağı ve yeter sayının anlık görüntüsü. Uç ve
ekran yoktur; öteki alanlar genel kurul akışıyla F2'de gelir.
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models
from django.db.models import F, Q

from apps.oab.models._base import AssemblyKind, AssemblyStatus, OabBaseModel


class GeneralAssembly(OabBaseModel):
    """Genel kurul; `term` kapanacak dönemdir, `opens_term` olağanda açılacak `HAZIRLIK` dönemidir."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "term",
        "opens_term",
        "kind",
        "first_meeting_at",
        "student_count_snapshot",
        "quorum_base",
        "quorum_multiplier",
        "quorum_required",
        "status",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "term",
        "opens_term",
        "kind",
        "first_meeting_at",
        "student_count_snapshot",
        "quorum_base",
        "quorum_multiplier",
        "quorum_required",
        "status",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)
    IZ_DONEM_ALANI: ClassVar[str] = "term"

    term = models.ForeignKey(
        "oab.OabTerm",
        on_delete=models.PROTECT,
        related_name="assemblies",
        verbose_name="birlik dönemi",
    )
    opens_term = models.ForeignKey(
        "oab.OabTerm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="açılacak dönem",
    )
    kind = models.CharField("tür", max_length=16, choices=AssemblyKind.choices)
    first_meeting_at = models.DateTimeField("birinci toplantı", null=True, blank=True)
    student_count_snapshot = models.PositiveIntegerField("öğrenci mevcudu", null=True, blank=True)
    quorum_base = models.PositiveSmallIntegerField("yeter sayı tabanı", null=True, blank=True)
    quorum_multiplier = models.PositiveSmallIntegerField(
        "yeter sayı çarpanı", null=True, blank=True
    )
    quorum_required = models.PositiveIntegerField("toplantı yeter sayısı", null=True, blank=True)
    status = models.CharField(
        "durum", max_length=16, choices=AssemblyStatus.choices, default=AssemblyStatus.PLANLANDI
    )

    class Meta:
        verbose_name = "genel kurul"
        verbose_name_plural = "genel kurullar"
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=AssemblyKind.values), name="ck_generalassembly_kind"
            ),
            models.CheckConstraint(
                condition=Q(status__in=AssemblyStatus.values), name="ck_generalassembly_status"
            ),
            # Yeter sayı üç alandan birlikte dolar: taban × çarpan.
            models.CheckConstraint(
                condition=Q(
                    quorum_base__isnull=True,
                    quorum_multiplier__isnull=True,
                    quorum_required__isnull=True,
                    student_count_snapshot__isnull=True,
                )
                | Q(
                    quorum_base__isnull=False,
                    quorum_multiplier__isnull=False,
                    student_count_snapshot__isnull=False,
                    quorum_required=F("quorum_base") * F("quorum_multiplier"),
                ),
                name="ck_generalassembly_yeter_sayi",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} genel kurul"
