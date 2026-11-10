"""Resmî defter, kurul toplantısı, katılım ve karar (tasarım §5.2.4, §5.2.8; plan F1c kararları).

F1c bu modelleri EKRANSIZ kurar (plan "F1c uygulama kararları": F2-F3 modellerine bağımlılık): görev
bölümü kaydı toplantı ve karar taslağı üretir, yedek çağrısı karar bağı taşır. Alanlar tasarımdaki
gibi tamdır; F1c'de yazılan karar türleri yalnız `GOREV_BOLUMU` ve `YEDEK_CAGIRMA`'dır, defter yalnız
karar defteridir. Toplantı ve karar yeter sayısı, deftere işleme ve sakat karar akışı F3'tedir.

Program karar defterinin yerine geçmez (CLAUDE.md "Konum"): karar defterine kararlar el ile yazılır,
defter noter tasdiklidir (md. 13/5, 23/2). `BoardDecision` defterdeki kararın programdaki karşılığıdır;
kararın varsayılanı `TASLAK`'tır.

Şifreli alanlar serbest metindir (tasarım §5.3): toplantı gündemi, karar metni ve muhalefet şerhi.
Hiçbiri KVKK boşaltma kümesinde değildir (birlik kaydıdır, §5.4); içerik MAC'indedir, değer listesine
girmez. Toplantı katılımında özrün nedeni tutulmaz (sağlık verisi olabilir).
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models
from django.db.models import Q

from apps.oab.models._base import (
    BookCertifier,
    BookKind,
    BookStatus,
    DecisionKind,
    DecisionStatus,
    MeetingKind,
    MeetingStatus,
    OabBaseModel,
    OrganType,
)
from apps.okul.models import Attachment
from shared.crypto import EncryptedTextField

#: Toplantısı tutulan organlar (tasarım §5.2.4 `BoardMeeting.organ`).
KURUL_ORGANLARI = (OrganType.YONETIM_KURULU, OrganType.DENETLEME_KURULU)

#: Sertifika no ve yer adlarının üst sınırı (karakter).
KISA_METIN_MAX = 64
YER_MAX = 128


class OfficialBook(OabBaseModel):
    """Resmî defter (tasarım §5.2.8). Dönemsizdir, devredilir; kilidi kendi durumudur (O2)."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "kind",
        "certified_by",
        "certified_on",
        "certification_no",
        "page_count",
        "lines_per_page",
        "last_no_before_program",
        "last_page_before_program",
        "opened_on",
        "closed_on",
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

    kind = models.CharField("tür", max_length=32, choices=BookKind.choices)
    certified_by = models.CharField(
        "tasdik eden makam", max_length=12, choices=BookCertifier.choices, blank=True, default=""
    )
    certified_on = models.DateField("tasdik günü", null=True, blank=True)
    certification_no = models.CharField(
        "tasdik no", max_length=KISA_METIN_MAX, blank=True, default=""
    )
    page_count = models.PositiveIntegerField("sayfa sayısı", null=True, blank=True)
    #: Gelir-gider defterinde sayfa başına satır (E17 baskısı ve toplu işaret; F3).
    lines_per_page = models.PositiveSmallIntegerField("sayfa başına satır", null=True, blank=True)
    #: Geçiş kurulumunda defterdeki son sıra no ve sayfa (§7.9 adım 4).
    last_no_before_program = models.PositiveIntegerField(
        "programdan önceki son sıra no", null=True, blank=True
    )
    last_page_before_program = models.PositiveIntegerField(
        "programdan önceki son sayfa", null=True, blank=True
    )
    opened_on = models.DateField("açılış günü", null=True, blank=True)
    closed_on = models.DateField("kapanış günü", null=True, blank=True)
    status = models.CharField(
        "durum", max_length=12, choices=BookStatus.choices, default=BookStatus.KULLANIMDA
    )

    class Meta:
        verbose_name = "resmî defter"
        verbose_name_plural = "resmî defterler"
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=BookKind.values), name="ck_officialbook_kind"
            ),
            models.CheckConstraint(
                condition=Q(certified_by__in=["", *BookCertifier.values]),
                name="ck_officialbook_certified_by",
            ),
            models.CheckConstraint(
                condition=Q(status__in=BookStatus.values), name="ck_officialbook_status"
            ),
            models.CheckConstraint(
                condition=Q(closed_on__isnull=True)
                | Q(opened_on__isnull=True)
                | Q(closed_on__gte=models.F("opened_on")),
                name="ck_officialbook_kapanis_sirasi",
            ),
        ]

    def __str__(self) -> str:
        return str(self.get_kind_display())


class BoardMeeting(OabBaseModel):
    """Yönetim kurulu ya da Denetleme Kurulu toplantısı (tasarım §5.2.4)."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "term",
        "organ",
        "meeting_no",
        "kind",
        "scheduled_at",
        "held_at",
        "status",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "term",
        "organ",
        "meeting_no",
        "kind",
        "scheduled_at",
        "held_at",
        "place",
        "agenda",
        "status",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)
    IZ_DONEM_ALANI: ClassVar[str] = "term"

    term = models.ForeignKey(
        "oab.OabTerm",
        on_delete=models.PROTECT,
        related_name="board_meetings",
        verbose_name="birlik dönemi",
    )
    organ = models.CharField("organ", max_length=16, choices=OrganType.choices)
    #: Dönem ve organ içinde sıra.
    meeting_no = models.PositiveIntegerField("toplantı no")
    kind = models.CharField("tür", max_length=16, choices=MeetingKind.choices)
    scheduled_at = models.DateTimeField("planlanan zaman", null=True, blank=True)
    held_at = models.DateTimeField("yapıldığı zaman", null=True, blank=True)
    place = models.CharField("yer", max_length=YER_MAX, blank=True, default="")
    agenda = EncryptedTextField("gündem", blank=True, default="")
    status = models.CharField(
        "durum", max_length=16, choices=MeetingStatus.choices, default=MeetingStatus.PLANLANDI
    )

    class Meta:
        verbose_name = "kurul toplantısı"
        verbose_name_plural = "kurul toplantıları"
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(organ__in=KURUL_ORGANLARI), name="ck_boardmeeting_organ"
            ),
            models.CheckConstraint(
                condition=Q(kind__in=MeetingKind.values), name="ck_boardmeeting_kind"
            ),
            models.CheckConstraint(
                condition=Q(status__in=MeetingStatus.values), name="ck_boardmeeting_status"
            ),
            # Yapılmış (ya da yeter sayısı sağlanamamış) toplantının zamanı vardır.
            models.CheckConstraint(
                condition=~Q(status__in=(MeetingStatus.YAPILDI, MeetingStatus.YETER_SAYI_YOK))
                | Q(held_at__isnull=False),
                name="ck_boardmeeting_yapildi_zamani",
            ),
            models.UniqueConstraint(
                fields=["term", "organ", "meeting_no"], name="uq_boardmeeting_donem_organ_no"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_organ_display()} toplantısı {self.meeting_no}"


class BoardMeetingAttendance(OabBaseModel):
    """Bir üyenin bir toplantıdaki katılımı (tasarım §5.2.4; OYS AYNEN). Özrün nedeni tutulmaz."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = ("meeting", "membership", "present", "excused")
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "meeting",
        "membership",
        "present",
        "excused",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ()
    #: Dönemi toplantısındandır (`AuditTrail.term`).
    IZ_DONEM_ALANI: ClassVar[str] = "meeting__term"

    meeting = models.ForeignKey(
        BoardMeeting,
        on_delete=models.PROTECT,
        related_name="attendances",
        verbose_name="toplantı",
    )
    membership = models.ForeignKey(
        "oab.OrganMembership",
        on_delete=models.PROTECT,
        related_name="attendances",
        verbose_name="üyelik",
    )
    present = models.BooleanField("katıldı")
    #: Katılmayanda anlamlıdır: yalnız özürsüz devamsızlık sayılır (md. 13/6; F3).
    excused = models.BooleanField("özürlü", default=False)

    class Meta:
        verbose_name = "toplantı katılımı"
        verbose_name_plural = "toplantı katılımları"
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "membership"], name="uq_boardmeetingattendance_uyelik"
            ),
            models.CheckConstraint(
                condition=Q(present=False) | Q(excused=False),
                name="ck_boardmeetingattendance_ozur",
            ),
        ]

    def __str__(self) -> str:
        return "katıldı" if self.present else ("özürlü" if self.excused else "özürsüz")


class BoardDecision(OabBaseModel):
    """Kurul kararının programdaki karşılığı (tasarım §5.2.4; OYS `is_draft` → `status`)."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "meeting",
        "kind",
        "votes_for",
        "votes_against",
        "status",
        "book",
        "decision_no",
        "page_no",
        "decision_date",
        "entered_by",
        "entered_at",
        "page_photo",
        "amends",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "meeting",
        "kind",
        "text",
        "votes_for",
        "votes_against",
        "dissent",
        "status",
        "book",
        "decision_no",
        "page_no",
        "decision_date",
        "entered_by",
        "entered_at",
        "page_photo",
        "amends",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)
    #: Dönemi toplantısındandır (`AuditTrail.term`).
    IZ_DONEM_ALANI: ClassVar[str] = "meeting__term"

    meeting = models.ForeignKey(
        BoardMeeting,
        on_delete=models.PROTECT,
        related_name="decisions",
        verbose_name="toplantı",
    )
    kind = models.CharField("tür", max_length=16, choices=DecisionKind.choices)
    text = EncryptedTextField("karar metni", blank=True, default="")
    votes_for = models.PositiveSmallIntegerField("kabul oyu", null=True, blank=True)
    votes_against = models.PositiveSmallIntegerField("ret oyu", null=True, blank=True)
    dissent = EncryptedTextField("muhalefet şerhi", blank=True, default="")
    status = models.CharField(
        "durum", max_length=16, choices=DecisionStatus.choices, default=DecisionStatus.TASLAK
    )
    book = models.ForeignKey(
        OfficialBook,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="decisions",
        verbose_name="karar defteri",
    )
    decision_no = models.PositiveIntegerField("defter sıra no", null=True, blank=True)
    page_no = models.PositiveIntegerField("defter sayfası", null=True, blank=True)
    decision_date = models.DateField("karar günü", null=True, blank=True)
    entered_by = models.ForeignKey(
        "okul.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="deftere işleyen hesap",
    )
    entered_at = models.DateTimeField("deftere işlenme zamanı", null=True, blank=True)
    page_photo = models.ForeignKey(
        Attachment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="defter sayfasının fotoğrafı",
    )
    amends = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="düzelttiği karar",
    )

    class Meta:
        verbose_name = "kurul kararı"
        verbose_name_plural = "kurul kararları"
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=DecisionKind.values), name="ck_boarddecision_kind"
            ),
            models.CheckConstraint(
                condition=Q(status__in=DecisionStatus.values), name="ck_boarddecision_status"
            ),
            # (defter, sıra no) tekil — sert (tasarım §5.2.4).
            models.UniqueConstraint(
                fields=["book", "decision_no"],
                condition=Q(book__isnull=False, decision_no__isnull=False),
                name="uq_boarddecision_defter_sira",
            ),
            # Defterde yazılı kararın defteri, sıra no'su ve sayfası vardır.
            models.CheckConstraint(
                condition=~Q(
                    status__in=(DecisionStatus.DEFTERE_ISLENDI, DecisionStatus.DEFTERDE_SAKAT)
                )
                | Q(book__isnull=False, decision_no__isnull=False, page_no__isnull=False),
                name="ck_boarddecision_defter_bilgisi",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} kararı"
