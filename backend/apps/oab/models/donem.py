"""Kural paketi kopyası ve birlik dönemi (tasarım §5.2.1, §6.2).

Dönem, bağlandığı revizyonun dondurulmuş kopyasından okur (`RulePackage.content`): program güncellemesi
dosyayı değiştirse de bağlı dönem etkilenmez. `OabTerm.rule_package` yalnız revizyon geçişi servisiyle
(`services.kural_bagi`) ve `KAPANDI` olmayan dönemde değişir.

`archive_document` (→ `GeneratedDocument`) dönem kapanışının arşiv paketidir (E39, tasarım §8.5); alan F1c
9. adımda evrak hattıyla geldi, yazanı dönem kapanışıdır (F4).
"""

from __future__ import annotations

from typing import Any, ClassVar

from django.db import models
from django.db.models import F, Q

from apps.oab.models._base import OabBaseModel, TermStatus
from apps.okul.models import ImmutableRecord
from shared.crypto import EncryptedTextField


class _DegismezQuerySet(models.QuerySet):  # type: ignore[type-arg]  # Any davranışı korunur
    """Dondurulmuş kopyayı ORM yoluyla değiştiren toplu yazımlar hata verir."""

    def update(self, **kwargs: Any) -> int:
        raise ImmutableRecord("Kural paketi kopyası değiştirilemez (tasarım §6.2-4).")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ImmutableRecord("Kural paketi kopyası silinemez (tasarım §6.2-4).")


class RulePackage(models.Model):
    """Bir kural revizyonunun veritabanındaki dondurulmuş kopyası (tasarım §5.2.1, §6.2-4).

    İçerik yazıldıktan sonra değişmez, yeni revizyon yeni satırdır. `content_sha256` kanonik JSON
    özetidir (D7, `kurallar.yukleyici.icerik_ozeti`): `JSONField` gidiş-dönüşü baytı korumaz.
    """

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "package",
        "rev",
        "schema_version",
        "content_sha256",
        "loaded_at",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "package",
        "rev",
        "schema_version",
        "content",
        "content_sha256",
        "loaded_at",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ()

    package = models.CharField("paket", max_length=16)
    rev = models.PositiveIntegerField("revizyon")
    schema_version = models.PositiveSmallIntegerField("şema sürümü")
    content = models.JSONField("içerik")
    content_sha256 = models.CharField("içerik özeti", max_length=64)
    loaded_at = models.DateTimeField("yüklenme", auto_now_add=True)

    objects = _DegismezQuerySet.as_manager()

    class Meta:
        verbose_name = "kural paketi kopyası"
        verbose_name_plural = "kural paketi kopyaları"
        ordering = ["package", "rev"]
        constraints = [
            models.UniqueConstraint(fields=["package", "rev"], name="uq_rulepackage_package_rev"),
        ]

    def __str__(self) -> str:
        return f"{self.package}.r{self.rev}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Yalnız yeni satır yazılır; var olan kopyanın kaydı `ImmutableRecord` yükseltir."""
        if not self._state.adding:
            raise ImmutableRecord("Kural paketi kopyası değiştirilemez (tasarım §6.2-4).")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ImmutableRecord("Kural paketi kopyası silinemez (tasarım §6.2-4).")


_BASLAMIS_DURUMLAR = (TermStatus.ACIK, TermStatus.KAPANISTA, TermStatus.KAPANDI)
_BITMIS_DURUMLAR = (TermStatus.KAPANISTA, TermStatus.KAPANDI)


class OabTerm(OabBaseModel):
    """Birlik dönemi: genel kuruldan genel kurula (T3; tasarım §5.2.1).

    Yazma kuralları `services.donem_kilidi`'ndedir (O2). F1c'de açılan tek yol ilk dönemin doğrudan
    `ACIK` açılmasıdır (§7.9); `HAZIRLIK` yolu F2, gerçek kapanış F4'tedir. Tarih aralıklarının
    çakışmaması ikinci dönemi açan F2 yolunda denetlenir: ilk dönemde çakışacak başka dönem yoktur.
    """

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "school_year",
        "start_date",
        "end_date",
        "opened_by_assembly",
        "rule_package",
        "status",
        "program_start_date",
        "pre_program_income",
        "pre_program_expense",
        "transition_completed_on",
        "closed_at",
        "closed_by",
        "archive_document",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "name",
        "school_year",
        "start_date",
        "end_date",
        "opened_by_assembly",
        "rule_package",
        "status",
        "program_start_date",
        "pre_program_income",
        "pre_program_expense",
        "pre_program_evidence",
        "yk_meeting_day_rule",
        "dk_audit_plan_dates",
        "transition_completed_on",
        "cancel_reason",
        "closed_at",
        "closed_by",
        "archive_document",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)
    #: Satırın denetim izindeki dönemi kendisidir (`AuditTrail.term`).
    IZ_DONEM_ALANI: ClassVar[str] = "id"

    name = models.CharField("ad", max_length=40)
    school_year = models.ForeignKey(
        "okul.SchoolYear",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="ders yılı",
    )
    start_date = models.DateField("başlangıç", null=True, blank=True)
    end_date = models.DateField("bitiş", null=True, blank=True)
    opened_by_assembly = models.ForeignKey(
        "oab.GeneralAssembly",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="dönemi açan genel kurul",
    )
    rule_package = models.ForeignKey(
        RulePackage,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="kural paketi",
    )
    status = models.CharField(
        "durum", max_length=16, choices=TermStatus.choices, default=TermStatus.HAZIRLIK
    )
    program_start_date = models.DateField("programa başlama günü", null=True, blank=True)
    pre_program_income = models.DecimalField(
        "programdan önceki gelir", max_digits=14, decimal_places=2, null=True, blank=True
    )
    pre_program_expense = models.DecimalField(
        "programdan önceki gider", max_digits=14, decimal_places=2, null=True, blank=True
    )
    pre_program_evidence = EncryptedTextField("programdan önceki kanıt", blank=True, default="")
    yk_meeting_day_rule = models.CharField(
        "yönetim kurulu toplantı günü kuralı", max_length=64, blank=True, default=""
    )
    dk_audit_plan_dates = models.JSONField("denetim planı tarihleri", default=list, blank=True)
    #: "Geçiş kurulumu tamamlandı" işaretinin günü (tasarım §7.9 "Senaryolar"; alan tasarımda yok,
    #: en dar çözüm olarak dönemdedir — plan F1c 8. adımın kararı). Yalnız genel kurulsuz açılan
    #: dönemde konur; konunca geçiş kayıtları (dönem, devralınan üyelik, sayaç beyanı, karar defteri)
    #: kilitlenir, iptal yolu kapanır.
    transition_completed_on = models.DateField(
        "geçiş kurulumunun tamamlandığı gün", null=True, blank=True
    )
    #: `ACIK` → `IPTAL`'de zorunlu: yanlış geçiş kaydının gerekçesi (şifreli; kim `updated_by` ve iz).
    cancel_reason = EncryptedTextField("iptal gerekçesi", blank=True, default="")
    closed_at = models.DateTimeField("kapanış", null=True, blank=True)
    closed_by = models.ForeignKey(
        "okul.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="kapatan hesap",
    )
    #: Kapanan dönemin arşiv paketi (E39; tasarım §5.2.1, §8.5). Yazanı dönem kapanışıdır (F4).
    archive_document = models.ForeignKey(
        "oab.GeneratedDocument",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="arşiv paketi",
    )

    class Meta:
        verbose_name = "birlik dönemi"
        verbose_name_plural = "birlik dönemleri"
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=TermStatus.values), name="ck_oabterm_status"
            ),
            models.UniqueConstraint(
                fields=["status"],
                condition=Q(status=TermStatus.ACIK),
                name="uq_oabterm_tek_acik",
            ),
            models.UniqueConstraint(
                fields=["status"],
                condition=Q(status=TermStatus.HAZIRLIK),
                name="uq_oabterm_tek_hazirlik",
            ),
            models.CheckConstraint(
                # İptal: hazırlıktan (tarihsiz) ya da geçiş döneminden (tarihli) gelir.
                condition=Q(status=TermStatus.HAZIRLIK, start_date__isnull=True)
                | Q(status=TermStatus.IPTAL)
                | Q(status__in=_BASLAMIS_DURUMLAR, start_date__isnull=False),
                name="ck_oabterm_baslangic",
            ),
            models.CheckConstraint(
                condition=Q(transition_completed_on__isnull=True)
                | Q(opened_by_assembly__isnull=True),
                name="ck_oabterm_gecis_isareti",
            ),
            models.CheckConstraint(
                condition=Q(status__in=_BITMIS_DURUMLAR, end_date__isnull=False)
                | (~Q(status__in=_BITMIS_DURUMLAR) & Q(end_date__isnull=True)),
                name="ck_oabterm_bitis",
            ),
            models.CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(end_date__gte=F("start_date")),
                name="ck_oabterm_bitis_sirasi",
            ),
            models.CheckConstraint(
                condition=Q(program_start_date__isnull=True)
                | Q(program_start_date__gte=F("start_date")),
                name="ck_oabterm_programa_baslama",
            ),
            models.UniqueConstraint(
                fields=["name"],
                condition=~Q(status=TermStatus.IPTAL),
                name="uq_oabterm_ad_iptal_olmayan",
            ),
        ]

    def __str__(self) -> str:
        return str(self.name)

    @property
    def donem_kapali(self) -> bool:
        """Kapanmış dönem her rolde salt okurdur (`rol_izinleri.YetkiKaydi`; tasarım §5 O2)."""
        return bool(self.status == TermStatus.KAPANDI)

    @property
    def sahip_rol(self) -> str | None:
        """Dönemin sahibi olan rol yoktur (`rol_izinleri.YetkiKaydi`)."""
        return None
