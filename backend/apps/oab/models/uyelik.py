"""Organ üyeliği (tasarım §5.2.2 `OrganMembership`; OYS `OrganMembership` UYARLA; plan F1c-5).

Bir kişinin bir birlik döneminde bir organdaki koltuğu: yönetim kurulu, Denetleme Kurulu, divan, alım
komisyonu ya da birlik temsilciliği. Koltuk uygunluğu, kadro sayımı ve seçilme sayacı
`services.uyelikler`'dedir; kurul bileşimleri ve sayılar kural paketindedir (altın kural 2).

OYS'den çıkanlar: şifreli beyan notu ve uygunluk beyanı bayrağı (yalnız tarih kalır, envanter S-20;
D41), model başına `compliance_warnings` / `compliance_justification` (uyum satırına taşındı, O3;
kaydın güncel uyarı özeti `rule_warnings`), `kvkk_special_category`, `status_changed_at` (seçilme günü
`start_date`, bitiş `end_date`, yedekten çağrı `promoted_on`), iki harfli `organ` sınırı ve yumuşak
silmeli tek tekil kısıt.

İKİ KISMİ TEKİL KISIT (tasarım §5.2.2; plan F1c kararları), ikisi de `IPTAL` OLMAYAN kayıtlarda:
genel kurul bağı doluyken (dönem, organ, kişi, genel kurul); boşken (dönem, organ, kişi, temsil türü).
SQLite tekil dizinde NULL'ları ayrı saydığından tek kısıt genel kurul dışı seçimlerde etkisiz kalırdı
(denetim UY-10). Temsil türü öteki organlarda boş dizedir, `NULL` değildir: aynı veli iki kurulda
temsilci olabilir, başkan kendiliğinden üye olduğu komisyonlarda ayrı satır alır.

DURUM MAKİNESİ (OYS kusurunun düzeltmesi): kayıt `ADAY` ya da `SECILDI` açılır; geçişler `ADAY` →
`SECILDI` · `IPTAL`, `SECILDI` → `DUSTU` · `IPTAL`'dir. `DUSTU` ve `IPTAL` geri dönmez, `ADAY`
düşürülmez. Koruma `save()`'dedir: hangi servis yazarsa yazsın geçiş veritabanındaki durumla denetlenir.
`seat_type` seçildiği koltuktur, değişmez; yedekten çağrıyı `promoted_on` gösterir.

DENETİM İZİ (tasarım §4.6.2, §5 O4): değer listesi kişisiz alanlardır (organ, görev, koltuk, oy, durum,
kaynak, tarihler, engel var/yok, MEM onay no, karar bağları). Kişi bağı ve şifreli `evidence_note`
yalnız içerik MAC'indedir. KVKK boşaltma kümesindeki iki alan (`dropped_reason`,
`eligibility_bar_basis`; §5.4, dönem kapanışında boşaltılır) ne değer listesine ne içerik MAC'ine girer.
"""

from __future__ import annotations

from typing import Any, ClassVar, Final

from django.db import models
from django.db.models import Q

from apps.oab.models._base import (
    DropKind,
    ElectedBy,
    EligibilityBar,
    EligibilityBarBasis,
    MembershipRole,
    MembershipSource,
    MembershipStatus,
    OabBaseModel,
    OrganType,
    Representation,
    SeatGroup,
    SeatType,
)
from shared.crypto import EncryptedCharField, EncryptedTextField

#: Kaydın açılabildiği durumlar: genel kurul adayı ya da genel kurul dışı kanalda seçilmiş üye.
ACILIS_DURUMLARI: Final = frozenset({MembershipStatus.ADAY, MembershipStatus.SECILDI})

#: İzinli durum geçişleri; `DUSTU` ve `IPTAL` son durumdur.
IZINLI_GECISLER: Final[dict[str, frozenset[str]]] = {
    MembershipStatus.ADAY: frozenset({MembershipStatus.SECILDI, MembershipStatus.IPTAL}),
    MembershipStatus.SECILDI: frozenset({MembershipStatus.DUSTU, MembershipStatus.IPTAL}),
    MembershipStatus.DUSTU: frozenset(),
    MembershipStatus.IPTAL: frozenset(),
}

DURUM_GECISI_GECERSIZ = "Üyelik kaydı bu duruma geçirilemez."
ACILIS_DURUMU_GECERSIZ = "Üyelik kaydı yalnız aday ya da seçilmiş olarak açılır."

#: MEM onay no'sunun üst sınırı (karakter; il/ilçe yazısının sayısı).
MEM_ONAY_NO_MAX = 64


class UyelikDurumuGecersiz(ValueError):
    """İzinli olmayan durum geçişi (durum makinesi; modül başlığı)."""


class OrganMembership(OabBaseModel):
    """Bir kişinin bir dönemde bir organdaki koltuğu (tasarım §5.2.2)."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "term",
        "organ",
        "assembly",
        "role",
        "seat_type",
        "seat_group",
        "votes",
        "seat_order",
        "elected_by",
        "source",
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
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "term",
        "person",
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
        "rule_warnings",
    )
    #: KVKK boşaltma kümesi (tasarım §5.4): dönem kapanışında boşaltılır; MAC'e girmez (O4).
    IZ_MAC_DISI_ALANLARI: ClassVar[tuple[str, ...]] = ("dropped_reason", "eligibility_bar_basis")
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)
    IZ_DONEM_ALANI: ClassVar[str] = "term"

    term = models.ForeignKey(
        "oab.OabTerm",
        on_delete=models.PROTECT,
        related_name="memberships",
        verbose_name="birlik dönemi",
    )
    person = models.ForeignKey(
        "oab.OabPerson",
        on_delete=models.PROTECT,
        related_name="memberships",
        verbose_name="birlik kişisi",
    )
    organ = models.CharField("organ", max_length=16, choices=OrganType.choices)
    #: Seçildiği genel kurul: divanda ve genel kurul seçiminde zorunlu, öteki kanallarda boş.
    assembly = models.ForeignKey(
        "oab.GeneralAssembly",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="memberships",
        verbose_name="genel kurul",
    )
    role = models.CharField(
        "görev", max_length=20, choices=MembershipRole.choices, default=MembershipRole.UYE
    )
    seat_type = models.CharField("koltuk", max_length=8, choices=SeatType.choices)
    #: Denetleme Kurulunda koltuk grubu; öteki organlarda boş dize.
    seat_group = models.CharField(
        "koltuk grubu", max_length=8, choices=SeatGroup.choices, blank=True, default=""
    )
    votes = models.PositiveIntegerField("aldığı oy", null=True, blank=True)
    #: Yedek sırası (aldığı oy sırası; md. 13/6).
    seat_order = models.PositiveSmallIntegerField("yedek sırası", null=True, blank=True)
    elected_by = models.CharField("seçim kanalı", max_length=20, choices=ElectedBy.choices)
    source = models.CharField(
        "kaynak",
        max_length=12,
        choices=MembershipSource.choices,
        default=MembershipSource.PROGRAM,
    )
    #: Devralınan üyelikte seçildiği genel kurulun tarihi ve görev bölümü kararının defter sıra no'su.
    evidence_note = EncryptedTextField("dayanak notu", blank=True, default="")
    #: Temsilcide temsil türü; öteki organlarda boş dize (`NULL` değil; plan F1c kararları).
    representation = models.CharField(
        "temsil türü", max_length=32, choices=Representation.choices, blank=True, default=""
    )
    representative_decision = models.ForeignKey(
        "oab.BoardDecision",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="temsilci görevlendirme kararı",
    )
    #: Denetleme Kurulu öğretmen koltuğunda başka okulun öğretmeni için il/ilçe MEM onay no'su.
    mem_approval_no = models.CharField(
        "MEM onay no", max_length=MEM_ONAY_NO_MAX, blank=True, default=""
    )
    external_assignment_start = models.DateField(
        "başka kurumda görevlendirme başlangıcı", null=True, blank=True
    )
    external_assignment_end = models.DateField(
        "başka kurumda görevlendirme bitişi", null=True, blank=True
    )
    status = models.CharField(
        "durum", max_length=8, choices=MembershipStatus.choices, default=MembershipStatus.ADAY
    )
    start_date = models.DateField("başlangıç", null=True, blank=True)
    end_date = models.DateField("bitiş", null=True, blank=True)
    promoted_on = models.DateField("yedekten çağrı günü", null=True, blank=True)
    promoted_by_decision = models.ForeignKey(
        "oab.BoardDecision",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="yedek çağırma kararı",
    )
    drop_kind = models.CharField(
        "düşme türü", max_length=24, choices=DropKind.choices, blank=True, default=""
    )
    dropped_reason = EncryptedTextField("düşme gerekçesi", blank=True, default="")
    #: Okulun suç engeli beyanı uygulamasının tarihi (beyan okulun yöntemidir; içerik tutulmaz).
    eligibility_declared_on = models.DateField("suç engeli beyanı günü", null=True, blank=True)
    single_birlik_declared_on = models.DateField("tek birlik beyanı günü", null=True, blank=True)
    expertise_required = models.BooleanField("uzmanlık gerektiren iş", default=False)
    eligibility_bar = models.CharField(
        "görev alma engeli",
        max_length=4,
        choices=EligibilityBar.choices,
        default=EligibilityBar.YOK,
    )
    #: Özel nitelikli (KVKK md. 6/1): şifreli; okuması erişim günlüğüne yazılır.
    eligibility_bar_basis = EncryptedCharField(
        "görev alma engelinin dayanağı",
        max_length=32,
        choices=EligibilityBarBasis.choices,
        blank=True,
        default="",
    )
    eligibility_bar_found_on = models.DateField("engelin tespit günü", null=True, blank=True)
    #: md. 7/2 istisnası: öğrencisi ayrılan velinin üyeliği olağanüstü genel kurula kadar sürer.
    retained_until_assembly = models.BooleanField("olağanüstü genel kurula kadar", default=False)
    #: Kaydın güncel uyarı özeti (O3): kural kimliği, atıf, ileti, durum, paket ve revizyon.
    rule_warnings = models.JSONField("kural uyarıları", default=list, blank=True)

    class Meta:
        verbose_name = "organ üyeliği"
        verbose_name_plural = "organ üyelikleri"
        # Kişi adı şifrelidir; kullanıcıya gösterilen sıra seçicidedir (Python'da).
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(organ__in=OrganType.values), name="ck_organmembership_organ"
            ),
            models.CheckConstraint(
                condition=Q(role__in=MembershipRole.values), name="ck_organmembership_role"
            ),
            models.CheckConstraint(
                condition=Q(seat_type__in=SeatType.values), name="ck_organmembership_seat_type"
            ),
            models.CheckConstraint(
                condition=Q(elected_by__in=ElectedBy.values),
                name="ck_organmembership_elected_by",
            ),
            models.CheckConstraint(
                condition=Q(source__in=MembershipSource.values), name="ck_organmembership_source"
            ),
            models.CheckConstraint(
                condition=Q(status__in=MembershipStatus.values), name="ck_organmembership_status"
            ),
            models.CheckConstraint(
                condition=Q(eligibility_bar__in=EligibilityBar.values),
                name="ck_organmembership_eligibility_bar",
            ),
            models.CheckConstraint(
                condition=Q(drop_kind__in=["", *DropKind.values]),
                name="ck_organmembership_drop_kind",
            ),
            # Düşme türü yalnız ve her zaman düşmüş üyelikte (düşmede zorunlu).
            models.CheckConstraint(
                condition=Q(status=MembershipStatus.DUSTU, drop_kind__in=DropKind.values)
                | (~Q(status=MembershipStatus.DUSTU) & Q(drop_kind="")),
                name="ck_organmembership_dusme_turu",
            ),
            # Koltuk grubu yalnız ve her zaman Denetleme Kurulunda.
            models.CheckConstraint(
                condition=Q(organ=OrganType.DENETLEME_KURULU, seat_group__in=SeatGroup.values)
                | (~Q(organ=OrganType.DENETLEME_KURULU) & Q(seat_group="")),
                name="ck_organmembership_seat_group",
            ),
            # Temsil türü yalnız ve her zaman temsilcide; öteki organlarda boş dize.
            models.CheckConstraint(
                condition=Q(organ=OrganType.TEMSILCI, representation__in=Representation.values)
                | (~Q(organ=OrganType.TEMSILCI) & Q(representation="")),
                name="ck_organmembership_representation",
            ),
            # Divan genel kurulun organıdır: genel kurul bağı zorunlu.
            models.CheckConstraint(
                condition=~Q(organ=OrganType.DIVAN) | Q(assembly__isnull=False),
                name="ck_organmembership_divan_genel_kurul",
            ),
            models.CheckConstraint(
                condition=Q(end_date__isnull=True)
                | Q(start_date__isnull=True)
                | Q(end_date__gte=models.F("start_date")),
                name="ck_organmembership_bitis_sirasi",
            ),
            # İki kısmi tekil kısıt, ikisi de `IPTAL` olmayanlarda (modül başlığı).
            models.UniqueConstraint(
                fields=["term", "organ", "person", "assembly"],
                condition=Q(assembly__isnull=False) & ~Q(status=MembershipStatus.IPTAL),
                name="uq_organmembership_genel_kurullu",
            ),
            models.UniqueConstraint(
                fields=["term", "organ", "person", "representation"],
                condition=Q(assembly__isnull=True) & ~Q(status=MembershipStatus.IPTAL),
                name="uq_organmembership_genel_kurulsuz",
            ),
        ]
        indexes = [
            models.Index(fields=["term", "organ", "status"], name="oab_uyelik_kadro_idx"),
            models.Index(fields=["person", "organ"], name="oab_uyelik_kisi_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_organ_display()} üyeliği"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Durum makinesini veritabanındaki duruma karşı denetler, sonra kaydeder (modül başlığı)."""
        if self._state.adding:
            if self.status not in ACILIS_DURUMLARI:
                raise UyelikDurumuGecersiz(ACILIS_DURUMU_GECERSIZ)
        else:
            update_fields = kwargs.get("update_fields")
            if update_fields is None or "status" in update_fields:
                eski = (
                    type(self)
                    ._base_manager.filter(pk=self.pk)
                    .values_list("status", flat=True)
                    .first()
                )
                if (
                    eski is not None
                    and eski != self.status
                    and self.status not in IZINLI_GECISLER.get(str(eski), frozenset())
                ):
                    raise UyelikDurumuGecersiz(DURUM_GECISI_GECERSIZ)
        super().save(*args, **kwargs)
