"""Duyuru (tasarım §5.2.7 `Announcement`; plan F2 §5.1).

Model tasarımdaki alanlarıyla tamdır; F2'de genel kurul çağrıları (`GK_CAGRISI`,
`OLAGANUSTU_GK_CAGRISI`) yazılır, öteki türler geldikleri fazdadır. Üç kanalın kanıt günleri
(`distributed_written_on` elden yazılı, `posted_board_on` ilan panosu, `published_web_on` internet
sayfası; md. 9/3) ayrı alanlardır: 15 günlük süre her kanal için ayrıdır (plan F2 §7 U9). Konu genel
bağdır (`subject_type`, `subject_id`: genel kurul, bütçe, ders dönemi, tespit süreci; üretilen evrakın
biçimi). Kanıt dosyaları `Attachment`'a genel bağla bağlanır (`ekler()`; dosya deposunun sahip kaydı ve
yazma yolu 7. adımda).

İçerikte kişi adı yoktur (altın kural 5): içeriği üretilen evraktır (`content` → `GeneratedDocument`),
modelin serbest metin alanı yoktur. Web metni HTML dosyasıdır; program yayımlamaz.

DURUM MAKİNESİ: `TASLAK` → `YAYIMLANDI` → `KALDIRILDI`; kayıt taslak açılır, koruma `save()`'dedir.
Kayıt silinmez (altın kural 4).
"""

from __future__ import annotations

from typing import Any, ClassVar, Final

from django.db import models
from django.db.models import F, Q

from apps.oab.models._base import (
    AnnouncementKind,
    AnnouncementStatus,
    SilinmezOabModel,
    SilinmezQuerySet,
)
from apps.okul.models import Attachment

DUYURU_GECISLERI: Final[dict[str, frozenset[str]]] = {
    AnnouncementStatus.TASLAK: frozenset({AnnouncementStatus.YAYIMLANDI}),
    AnnouncementStatus.YAYIMLANDI: frozenset({AnnouncementStatus.KALDIRILDI}),
}
DUYURU_ACILIS_DURUMU_GECERSIZ = "Duyuru yalnız taslak olarak açılır."
DUYURU_DURUM_GECISI_GECERSIZ = "Duyuru bu duruma geçirilemez."


class DuyuruKaydiGecersiz(ValueError):
    """Duyuru kaydı modelin kuralını bozuyor (Türkçe ileti; içerik taşımaz)."""


class Announcement(SilinmezOabModel):
    """Duyuru (modül başlığı)."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "term",
        "kind",
        "subject_type",
        "subject_id",
        "school_term",
        "distributed_written_on",
        "posted_board_on",
        "removed_board_on",
        "published_web_on",
        "content",
        "status",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        *IZ_DEGER_ALANLARI,
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)
    IZ_DONEM_ALANI: ClassVar[str] = "term"

    term = models.ForeignKey(
        "oab.OabTerm",
        on_delete=models.PROTECT,
        related_name="announcements",
        verbose_name="birlik dönemi",
    )
    kind = models.CharField("tür", max_length=24, choices=AnnouncementKind.choices)
    #: Konunun model etiketi ve kimlik metni (`GeneratedDocument` biçimi); konusuz duyuruda boş.
    subject_type = models.CharField("konu kaydın modeli", max_length=64, blank=True, default="")
    subject_id = models.CharField("konu kaydın kimliği", max_length=64, blank=True, default="")
    school_term = models.ForeignKey(
        "okul.SchoolTerm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="ders dönemi",
    )
    distributed_written_on = models.DateField("elden yazılı bildirim günü", null=True, blank=True)
    posted_board_on = models.DateField("ilan panosuna asılma günü", null=True, blank=True)
    removed_board_on = models.DateField("ilan panosundan kaldırılma günü", null=True, blank=True)
    published_web_on = models.DateField("internet sayfasında yayım günü", null=True, blank=True)
    content = models.ForeignKey(
        "oab.GeneratedDocument",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="içerik (üretilen evrak)",
    )
    status = models.CharField(
        "durum",
        max_length=12,
        choices=AnnouncementStatus.choices,
        default=AnnouncementStatus.TASLAK,
    )

    objects = SilinmezQuerySet.as_manager()

    class Meta:
        verbose_name = "duyuru"
        verbose_name_plural = "duyurular"
        ordering = ["-id"]
        base_manager_name = "objects"
        indexes = [
            models.Index(fields=["subject_type", "subject_id", "kind"], name="oab_duyuru_konu_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=AnnouncementKind.values), name="ck_announcement_kind"
            ),
            models.CheckConstraint(
                condition=Q(status__in=AnnouncementStatus.values), name="ck_announcement_status"
            ),
            # Konu iki alanıyla birlikte dolu ya da birlikte boş.
            models.CheckConstraint(
                condition=Q(subject_type="", subject_id="")
                | (~Q(subject_type="") & ~Q(subject_id="")),
                name="ck_announcement_konu",
            ),
            # Panodan kaldırma asılmadan olmaz ve asılmadan önce olamaz.
            models.CheckConstraint(
                condition=Q(removed_board_on__isnull=True)
                | Q(posted_board_on__isnull=False, removed_board_on__gte=F("posted_board_on")),
                name="ck_announcement_pano_sirasi",
            ),
        ]

    def __str__(self) -> str:
        return str(self.get_kind_display())

    def ekler(self) -> models.QuerySet[Attachment]:
        """Bu duyuruya bağlı kanıt dosyaları (`evidence`; genel bağ, modül başlığı)."""
        return Attachment.objects.filter(
            owner_type=self._meta.label, owner_id=str(self.pk)
        ).order_by("uploaded_at", "id")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Durum makinesini veritabanındaki duruma karşı denetler, sonra kaydeder (modül başlığı)."""
        if self._state.adding:
            if self.status != AnnouncementStatus.TASLAK:
                raise DuyuruKaydiGecersiz(DUYURU_ACILIS_DURUMU_GECERSIZ)
        else:
            alanlar = kwargs.get("update_fields")
            if alanlar is None or "status" in alanlar:
                eski = (
                    type(self)
                    ._base_manager.filter(pk=self.pk)
                    .values_list("status", flat=True)
                    .first()
                )
                if (
                    eski is not None
                    and eski != self.status
                    and self.status not in DUYURU_GECISLERI.get(str(eski), frozenset())
                ):
                    raise DuyuruKaydiGecersiz(DUYURU_DURUM_GECISI_GECERSIZ)
        super().save(*args, **kwargs)
