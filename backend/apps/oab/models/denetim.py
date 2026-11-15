"""Denetleme Kurulu raporunun asgari kaydı (tasarım §5.2.4 `AuditReport`; plan F2 §7 U13).

F2 yalnız Denetleme Kurulunun md. 14/5 olağanüstü genel kurul çağrısını açan kısmı kurar: dönem, tür,
rapor günü, iki işaret, çağrılan genel kurul ve durum. Ekran yoktur; rapor içeriği (kontrol listesi,
bulgular), ara raporun yönetim kuruluna, nihai raporun genel kurula sunuluşu ve E32, E33 üretimi F4'te
gelir (OYS `AuditReport` UYARLA'sı orada tamamlanır; F1c'nin asgari `GeneralAssembly` kalıbı).

İKİ İŞARET (denetim MB-10): `irregularity_found` raporun usulsüzlük bayrağıdır; md. 14/5'in yolunu
açmaz ("usulsüzlük veya uygunsuzluk" müdürün md. 27/3 yoludur). Olağanüstü genel kurul çağrısı ve
`escalated_assembly` bağı yalnız `md6_violation_found` doğruyken vardır: md. 14/5 Denetleme Kuruluna
çağrıyı yönetim kurulunun md. 6'da sayılan görev ve yetkilere aykırı faaliyetinde verir (kullanıcı kararı
S6 (ii), hukuken geçersiz işlem).

İKİ BAĞ, İKİ KATMAN: çağrı iki yabancı anahtardadır, rapordaki `escalated_assembly` ve genel kuruldaki
`call_audit_report` (`models.genel_kurul` başlığı "md. 14/5 çağrısının iki bağı"). Veritabanı kısıtı
(`ck_auditreport_md6_cagri`) yalnız bu tablodaki bağı işarete bağlar. Genel kuruldaki bağın işareti ve
iki bağın birbirini göstermesi model katmanındadır: genel kurul tarafı `models.genel_kurul`'da; bu
tarafta `save()` ve toplu güncelleme çağrıya bağlı raporun işaretinin kaldırılmasını ve başka raporla
çağrılmış genel kurula bağlanmayı reddeder. Ham SQL bu korumayı aşar. İptal edilmiş genel kurulu gösteren
bağ yeni çağrıya taşınabilir (`models.genel_kurul` başlığı; denetim izli güncellemeyle, servis yazar).

Kayıt silinmez (altın kural 4).
"""

from __future__ import annotations

from typing import Any, ClassVar, Final

from django.apps import apps
from django.db import models
from django.db.models import Q

from apps.oab.models._base import (
    AuditReportKind,
    AuditReportStatus,
    SilinmezOabModel,
    SilinmezQuerySet,
)

MD6_ISARETI_KALDIRILAMAZ = (
    "Olağanüstü genel kurul çağrısına bağlı raporun md. 6 işareti kaldırılamaz (md. 14/5)."
)
GENEL_KURUL_BASKA_RAPORLA = "Bu olağanüstü genel kurul başka bir denetim raporuyla çağrılmış."

#: Rapordaki md. 14/5 bağının alan adları (`update_fields` ve toplu güncelleme ikisini de alır).
_CAGRI_ALANLARI: Final = frozenset({"escalated_assembly", "escalated_assembly_id"})


class DenetimRaporuKaydiGecersiz(ValueError):
    """Denetim raporu kaydı modelin kuralını bozuyor (Türkçe ileti; içerik taşımaz)."""


def _genel_kurul_modeli() -> Any:
    return apps.get_model("oab", "GeneralAssembly")


def _isaret_kaldirma_denetimi(rapor_pkleri: list[int]) -> None:
    """Genel kurulun `call_audit_report`'u gösterdiği raporun md. 6 işareti kaldırılmaz."""
    if (
        rapor_pkleri
        and _genel_kurul_modeli()
        ._base_manager.filter(call_audit_report_id__in=rapor_pkleri)
        .exists()
    ):
        raise DenetimRaporuKaydiGecersiz(MD6_ISARETI_KALDIRILAMAZ)


def _cagri_bagi_denetimi(kurul: object, rapor_pkleri: list[int | None]) -> None:
    """Rapordaki bağın gösterdiği genel kurul başka bir raporla çağrılmamış olmalı (modül başlığı).

    Genel kuruldaki bağ boş olabilir: 7. adımın servisi iki bağı aynı işlemde, sırayla yazar.
    """
    kurul_pk = getattr(kurul, "pk", kurul)
    if kurul_pk is None:
        return
    bag = (
        _genel_kurul_modeli()
        ._base_manager.filter(pk=kurul_pk)
        .values_list("call_audit_report_id", flat=True)
        .first()
    )
    if bag is not None and any(pk != bag for pk in rapor_pkleri):
        raise DenetimRaporuKaydiGecersiz(GENEL_KURUL_BASKA_RAPORLA)


class _DenetimRaporuQuerySet(SilinmezQuerySet):
    """Toplu güncelleme md. 14/5 bağını bozmaz (modül başlığı); silme kapalıdır."""

    def update(self, **kwargs: Any) -> int:
        if "md6_violation_found" in kwargs and kwargs["md6_violation_found"] is False:
            _isaret_kaldirma_denetimi(list(self.values_list("pk", flat=True)))
        for ad in _CAGRI_ALANLARI & set(kwargs):
            _cagri_bagi_denetimi(kwargs[ad], list(self.values_list("pk", flat=True)))
        return super().update(**kwargs)


class AuditReport(SilinmezOabModel):
    """Denetleme Kurulu raporu (asgari; modül başlığı)."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "term",
        "kind",
        "report_date",
        "irregularity_found",
        "md6_violation_found",
        "escalated_assembly",
        "status",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "term",
        "kind",
        "report_date",
        "irregularity_found",
        "md6_violation_found",
        "escalated_assembly",
        "status",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)
    IZ_DONEM_ALANI: ClassVar[str] = "term"

    term = models.ForeignKey(
        "oab.OabTerm",
        on_delete=models.PROTECT,
        related_name="audit_reports",
        verbose_name="birlik dönemi",
    )
    kind = models.CharField("tür", max_length=8, choices=AuditReportKind.choices)
    report_date = models.DateField("rapor günü")
    #: Raporun usulsüzlük bayrağı; md. 14/5 yolunu açmaz (modül başlığı).
    irregularity_found = models.BooleanField("usulsüzlük tespit edildi", default=False)
    #: Denetleme Kurulunun açık işareti: yönetim kurulunun md. 6'ya aykırı faaliyeti tespit edildi.
    md6_violation_found = models.BooleanField(
        "md. 6'ya aykırı faaliyet tespit edildi", default=False
    )
    #: md. 14/5 olağanüstü genel kurul çağrısı.
    escalated_assembly = models.ForeignKey(
        "oab.GeneralAssembly",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="çağrılan olağanüstü genel kurul",
    )
    status = models.CharField(
        "durum",
        max_length=12,
        choices=AuditReportStatus.choices,
        default=AuditReportStatus.TASLAK,
    )

    objects = _DenetimRaporuQuerySet.as_manager()

    class Meta:
        verbose_name = "denetim raporu"
        verbose_name_plural = "denetim raporları"
        ordering = ["-report_date", "-id"]
        base_manager_name = "objects"
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=AuditReportKind.values), name="ck_auditreport_kind"
            ),
            models.CheckConstraint(
                condition=Q(status__in=AuditReportStatus.values), name="ck_auditreport_status"
            ),
            # md. 14/5 çağrısı yalnız md. 6 aykırılık işaretiyle (S6 (ii)); genel kuruldaki bağ
            # model katmanındadır (modül başlığı).
            models.CheckConstraint(
                condition=Q(escalated_assembly__isnull=True) | Q(md6_violation_found=True),
                name="ck_auditreport_md6_cagri",
            ),
        ]

    def __str__(self) -> str:
        return str(self.get_kind_display())

    def save(self, *args: Any, **kwargs: Any) -> None:
        """md. 14/5 bağının bu tarafı denetlenir (modül başlığı "İki bağ, iki katman")."""
        alanlar = kwargs.get("update_fields")
        if (
            (alanlar is None or "md6_violation_found" in alanlar)
            and not self.md6_violation_found
            and self.pk is not None
        ):
            _isaret_kaldirma_denetimi([self.pk])
        if alanlar is None or _CAGRI_ALANLARI & set(alanlar):
            _cagri_bagi_denetimi(self.escalated_assembly_id, [self.pk])
        super().save(*args, **kwargs)
