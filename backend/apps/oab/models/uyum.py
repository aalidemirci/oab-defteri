"""Uyum satırı, gerekçe ve yarım metin (tasarım §5 O3, §5.2.7, §7 "Yarım kalan metin").

Satır silinmez. `EKSIK` gerekçesiz yazılır; bilgi girilince `resolved_at` ile kapanır, kapatıcı geçişte
hâlâ açıksa `SAPMA`'ya döner. `SAPMA` gerekçesiz var olamaz (veritabanı kısıtı). Yazma kuralları
`services.uyum`'dadır. Kural kimliği, paket ve ileti kişisizdir ve açıktır; gerekçe metni şifrelidir
(tasarım §5.3).
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models
from django.db.models import Q

from apps.oab.models._base import ComplianceKind, ComplianceObligation, OabBaseModel
from apps.okul.models import Attachment
from shared.crypto import EncryptedTextField


class ComplianceJustification(OabBaseModel):
    """Gerekçe. Aynı kural ve kök neden için tek satır, birden çok `SAPMA`'ya bağlanır (toplu gerekçe)."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "rule_id",
        "template",
        "justified_by",
        "justified_at",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "rule_id",
        "root_cause",
        "text",
        "template",
        "justified_by",
        "justified_at",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ()

    rule_id = models.CharField("kural kimliği", max_length=64)
    root_cause = models.CharField("kök neden", max_length=64, blank=True, default="")
    text = EncryptedTextField("gerekçe")
    template = models.CharField("kalıp", max_length=64, blank=True, default="")
    justified_by = models.ForeignKey(
        "okul.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="gerekçeyi yazan hesap",
    )
    justified_at = models.DateTimeField("gerekçe zamanı")

    class Meta:
        verbose_name = "uyum gerekçesi"
        verbose_name_plural = "uyum gerekçeleri"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["rule_id", "root_cause"],
                condition=~Q(root_cause=""),
                name="uq_compliancejustification_kok_neden",
            ),
        ]

    def __str__(self) -> str:
        return str(self.rule_id)


class ComplianceItem(OabBaseModel):
    """Uyum satırı: sapma, eksik ya da takvim yükümlülüğü (tasarım §5.2.7)."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "term",
        "kind",
        "subject_type",
        "subject_id",
        "rule_id",
        "rule_package",
        "rev",
        "justification_group",
        "resolved_at",
        "obligation",
        "due_date",
        "done_on",
        "evidence",
        "responsible_role",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "term",
        "kind",
        "subject_type",
        "subject_id",
        "rule_id",
        "rule_package",
        "rev",
        "message",
        "justification_group",
        "resolved_at",
        "obligation",
        "due_date",
        "done_on",
        "evidence",
        "responsible_role",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("kind", "resolved_at")
    IZ_DONEM_ALANI: ClassVar[str] = "term"

    term = models.ForeignKey(
        "oab.OabTerm",
        on_delete=models.PROTECT,
        related_name="compliance_items",
        verbose_name="birlik dönemi",
    )
    kind = models.CharField("tür", max_length=8, choices=ComplianceKind.choices)
    # Sapma ve eksikte.
    subject_type = models.CharField("kayıt türü", max_length=64, blank=True, default="")
    subject_id = models.CharField("kayıt kimliği", max_length=64, blank=True, default="")
    rule_id = models.CharField("kural kimliği", max_length=64, blank=True, default="")
    rule_package = models.CharField("paket", max_length=16, blank=True, default="")
    rev = models.PositiveIntegerField("revizyon", null=True, blank=True)
    message = models.TextField("ileti", blank=True, default="")
    justification_group = models.ForeignKey(
        ComplianceJustification,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="items",
        verbose_name="gerekçe",
    )
    resolved_at = models.DateTimeField("kapanma", null=True, blank=True)
    # Takvimde.
    obligation = models.CharField(
        "yükümlülük", max_length=32, choices=ComplianceObligation.choices, blank=True, default=""
    )
    due_date = models.DateField("son gün", null=True, blank=True)
    done_on = models.DateField("yapıldığı gün", null=True, blank=True)
    evidence = models.ForeignKey(
        Attachment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="kanıt",
    )
    responsible_role = models.CharField("sorumlu rol", max_length=24, blank=True, default="")

    class Meta:
        verbose_name = "uyum satırı"
        verbose_name_plural = "uyum satırları"
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=ComplianceKind.values), name="ck_complianceitem_kind"
            ),
            models.CheckConstraint(
                condition=~Q(kind=ComplianceKind.SAPMA) | Q(justification_group__isnull=False),
                name="ck_complianceitem_sapma_gerekceli",
            ),
            models.CheckConstraint(
                condition=Q(kind=ComplianceKind.TAKVIM) | ~Q(rule_id=""),
                name="ck_complianceitem_kural_dolu",
            ),
            models.CheckConstraint(
                condition=~Q(kind=ComplianceKind.TAKVIM)
                | (~Q(obligation="") & Q(due_date__isnull=False)),
                name="ck_complianceitem_takvim_dolu",
            ),
            models.UniqueConstraint(
                fields=["term", "subject_type", "subject_id", "rule_id"],
                condition=Q(resolved_at__isnull=True) & ~Q(kind=ComplianceKind.TAKVIM),
                name="uq_complianceitem_acik_satir",
            ),
        ]
        indexes = [
            models.Index(fields=["term", "kind"], name="oab_uyum_donem_tur_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.rule_id or self.obligation}"


class DraftText(models.Model):
    """Hesabın gerekçe kutusundaki yarım metni: hesap başına tek, şifreli (tasarım §7).

    `TASLAK` durumu olmayan gerekçe kutusu içindir. Metin kaydedilince ya da vazgeçilince silinir.
    Kısa aralıklarla yazıldığı için iz satırı yazmaz (`services.yarim_metin`).
    """

    account = models.OneToOneField(
        "okul.Account",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="hesap",
    )
    context = models.CharField("bağlam", max_length=128, blank=True, default="")
    text = EncryptedTextField("yarım metin")
    updated_at = models.DateTimeField("güncellenme", auto_now=True)

    class Meta:
        verbose_name = "yarım metin"
        verbose_name_plural = "yarım metinler"

    def __str__(self) -> str:
        return "yarım metin"
