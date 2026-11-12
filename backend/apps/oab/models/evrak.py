"""Üretilen evrak kaydı (tasarım §5.2.8 `GeneratedDocument`, §9.1-2 "Evrak izi"; plan F1c 9. adım).

Her üretim bir satırdır: evrak kodu, konu (genel bağ), dönem, kural paketi, üreten hesap ve zaman,
içerik JSON'u (`content_json`, şifreli; `shared.evrak.kanonik_json`) ve onun kanonik özeti
(`content_sha256`; docx zip baytı değil). Yeniden basım kayıtlı JSON'dan çizilir ve aynı özeti verir
(`shared.evrak.belge_coz`; tasarım §6.2-6). Aynı konunun aynı evrakının yeniden üretimi yeni sürüm
satırıdır, önceki satır `YERINI_ALDI` olur ve silinmez; kapanmış dönemde de yazılabilir (O2 beyaz
listesi). Yazma kuralları `services.evrak`'tadır.

DOSYALAR (`files` → `Attachment`): ekler genel bağla bu satıra bağlanır (`Attachment.owner_type`
`oab.GeneratedDocument`, `owner_id` satırın kimliği; tasarım §5.2.10). Ayrı bir çoka-çok alanı
yoktur: tek yazar dosya deposudur (`apps.okul.services.dosya_deposu`), model bu bağı `ekler()` ile
okur. Bu model dosya deposunun ilk sahibidir (plan F1b-3; `apps.oab.apps` kaydeder) ve DOCX türünü
yalnız o alır.

VELİ ADI TAŞIYAN BELGE (R9; `personal_list`): program dosyasını ve içerik JSON'unu saklamaz —
`content_json` boştur (veritabanı kısıtı), dosya deposu bu sahibe ek yazmaz; satırda tür, tarih, satır
sayısı ve özet durur. Hesap teslim pusulasının (E63) dosyası saklanmaz, yalnız içerik JSON'u.

DEĞİŞMEZLİK (altın kural 4): satır silinmez (`ImmutableRecord`); yazıldıktan sonra yalnız durum
(`GECERLI` → `YERINI_ALDI`) ve ıslak imza işareti (`wet_signed_on`) değişir, öteki alanlar değişmez
(`save` `update_fields` ister ve yalnız bu alanlara izin verir).
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import Exact

from apps.oab.models._base import DocumentFormat, DocumentStatus, OabBaseModel
from apps.okul.models import Attachment, ImmutableRecord
from shared.crypto import EncryptedTextField

#: Evrak kataloğu kodu (tasarım §9.5: E01…E79); denetim izinin `BASIM` deseniyle aynı biçim.
EVRAK_KODU = re.compile(r"E\d{2}")
#: Yazıldıktan sonra değişebilen alanlar (modül başlığı "DEĞİŞMEZLİK").
DEGISEBILEN_ALANLAR: frozenset[str] = frozenset(
    {"status", "wet_signed_on", "updated_at", "updated_by"}
)
#: Durum geçişleri: geçerli kayıt yeniden üretimle yerini bırakır; geri dönüş yok.
DURUM_GECISLERI: dict[str, frozenset[str]] = {
    DocumentStatus.GECERLI: frozenset({DocumentStatus.YERINI_ALDI}),
    DocumentStatus.YERINI_ALDI: frozenset(),
}


class EvrakKaydiGecersiz(ValueError):
    """Üretilen evrak kaydı modelin kuralını bozuyor (Türkçe ileti; içerik taşımaz)."""


class _SilinmezQuerySet(models.QuerySet):  # type: ignore[type-arg]  # Any davranışı korunur
    def delete(self) -> tuple[int, dict[str, int]]:
        raise ImmutableRecord("Üretilen evrak kaydı silinmez (tasarım §5.2.8).")


class GeneratedDocument(OabBaseModel):
    """Programın ürettiği bir evrakın kaydı (modül başlığı)."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "doc_type",
        "subject_type",
        "subject_id",
        "term",
        "version",
        "formats",
        "content_sha256",
        "personal_list",
        "row_count",
        "rule_package",
        "generated_at",
        "generated_by",
        "wet_signed_on",
        "status",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "doc_type",
        "subject_type",
        "subject_id",
        "term",
        "version",
        "formats",
        "content_sha256",
        "content_json",
        "personal_list",
        "row_count",
        "rule_package",
        "generated_at",
        "generated_by",
        "wet_signed_on",
        "status",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)
    IZ_DONEM_ALANI: ClassVar[str] = "term"

    doc_type = models.CharField("evrak kodu", max_length=8)
    #: Konunun model etiketi (`okul.Account` biçimi) ve kimlik metni (`denetim_izi.kimlik_metni`).
    subject_type = models.CharField("konu kaydın modeli", max_length=64)
    subject_id = models.CharField("konu kaydın kimliği", max_length=64)
    term = models.ForeignKey(
        "oab.OabTerm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="generated_documents",
        verbose_name="birlik dönemi",
    )
    version = models.PositiveIntegerField("sürüm")
    #: Üretilen biçimler (`DocumentFormat` değerleri, sıralı ve tekrarsız).
    formats = models.JSONField("biçimler", default=list)
    content_sha256 = models.CharField("içerik özeti", max_length=64)
    content_json = EncryptedTextField("içerik", blank=True, default="")
    #: Veli adı taşıyan belge (R9): içerik ve dosya saklanmaz.
    personal_list = models.BooleanField("veli adı taşır", default=False)
    row_count = models.PositiveIntegerField("satır sayısı", null=True, blank=True)
    rule_package = models.ForeignKey(
        "oab.RulePackage",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="kural paketi",
    )
    generated_at = models.DateTimeField("üretim anı")
    generated_by = models.ForeignKey(
        "okul.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="üreten hesap",
    )
    wet_signed_on = models.DateField("ıslak imza günü", null=True, blank=True)
    status = models.CharField(
        "durum", max_length=16, choices=DocumentStatus.choices, default=DocumentStatus.GECERLI
    )

    objects = _SilinmezQuerySet.as_manager()

    class Meta:
        verbose_name = "üretilen evrak"
        verbose_name_plural = "üretilen evrak"
        ordering = ["-id"]
        base_manager_name = "objects"
        indexes = [
            models.Index(
                fields=["subject_type", "subject_id", "doc_type"], name="oab_gendoc_konu_idx"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=DocumentStatus.values), name="ck_generateddocument_status"
            ),
            models.CheckConstraint(
                condition=Q(version__gte=1), name="ck_generateddocument_version"
            ),
            models.CheckConstraint(
                condition=Q(Exact(Length("content_sha256"), 64)),
                name="ck_generateddocument_sha256",
            ),
            models.CheckConstraint(
                condition=~Q(subject_type="") & ~Q(subject_id=""),
                name="ck_generateddocument_konu",
            ),
            # Veli adı taşıyan belgenin içeriği saklanmaz (R9); ötekinin içeriği vardır.
            models.CheckConstraint(
                condition=Q(personal_list=True, content_json="")
                | (Q(personal_list=False) & ~Q(content_json="")),
                name="ck_generateddocument_icerik",
            ),
            models.UniqueConstraint(
                fields=["doc_type", "subject_type", "subject_id", "version"],
                name="uq_generateddocument_surum",
            ),
            # Aynı konunun aynı evrakında tek geçerli kayıt (yeniden üretim öncekinin yerini alır).
            models.UniqueConstraint(
                fields=["doc_type", "subject_type", "subject_id"],
                condition=Q(status=DocumentStatus.GECERLI),
                name="uq_generateddocument_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.doc_type} sürüm {self.version}"

    def ekler(self) -> models.QuerySet[Attachment]:
        """Bu kayda bağlı ekler (`files`; modül başlığı "DOSYALAR")."""
        return Attachment.objects.filter(
            owner_type=self._meta.label, owner_id=str(self.pk)
        ).order_by("uploaded_at", "id")

    def _ilk_kayit_denetimi(self) -> None:
        if not (isinstance(self.doc_type, str) and EVRAK_KODU.fullmatch(self.doc_type)):
            raise EvrakKaydiGecersiz("Evrak kodu biçimsiz.")
        if self.status != DocumentStatus.GECERLI:
            raise EvrakKaydiGecersiz("Üretilen evrak geçerli durumda açılır.")
        bicimler = self.formats
        if (
            not isinstance(bicimler, list)
            or not bicimler
            or not set(bicimler) <= set(DocumentFormat.values)
            or bicimler != sorted(set(bicimler))
        ):
            raise EvrakKaydiGecersiz("Evrakın biçim listesi geçersiz.")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Yeni satır kurala uymalı; var olan satırda yalnız `DEGISEBILEN_ALANLAR` yazılır."""
        if self._state.adding:
            self._ilk_kayit_denetimi()
        else:
            alanlar = kwargs.get("update_fields")
            if alanlar is None or not set(alanlar) <= DEGISEBILEN_ALANLAR:
                raise ImmutableRecord(
                    "Üretilen evrakın içeriği değişmez; yeniden üretim yeni sürüm satırıdır."
                )
            if "status" in alanlar:
                eski = (
                    type(self)
                    ._base_manager.filter(pk=self.pk)
                    .values_list("status", flat=True)
                    .first()
                )
                if (
                    eski is not None
                    and eski != self.status
                    and self.status not in DURUM_GECISLERI.get(str(eski), frozenset())
                ):
                    raise EvrakKaydiGecersiz("Üretilen evrakın durumu bu yöne değişmez.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ImmutableRecord("Üretilen evrak kaydı silinmez (tasarım §5.2.8).")
