"""Genel kurul, gündem, tutanak ve katılım düzeltmesi (tasarım §5.2.3; plan F2 §5.1, §7).

F1c genel kurulun asgari kaydını kurdu (dönem bağı ve yeter sayının anlık görüntüsü); F2 3. adım
tasarımın alanlarını tamamladı. Durum geçişlerinin servisleri ve kural denetimleri F2'nin 4.-7.
adımlarında (`services.genel_kurul`), uçlar ve ekran 11. adımında yazıldı; burada yalnız alanlar ve
veritabanı düzeyindeki kısıtlar vardır. Göç yalnız şema değiştirir: var olan kayıtlarda yeni alanlar
boş ya da varsayılandır.

ALAN ANLAMI (plan F2 §5.1 "tuzak"): `term` kapanacak dönemdir (çağrıyı o dönemin YK'si yapar, raporlar
o döneme aittir); olağanda açılacak `HAZIRLIK` dönemi `opens_term`'dür. Kaynak modülün (tasarım
§12.A) `term`'ü başlattığı dönemdi; anlamı burada değişir. Yeni açılan okulun ilk genel kurulunda
kapanacak dönem yoktur: `term` YALNIZ `called_by = MUDUR_YENI_OKUL`'da boş olabilir ve o zaman
`opens_term` doludur (kullanıcı kararı S5 (i), 15.11.2026). Olağanüstü genel kurul dönem açmaz
(md. 13/8): `opens_term` boştur. Bir hazırlık dönemini tek genel kurul açar (kısmi tekil kısıt).

İKİ TOPLANTI TEK KAYITTA (U8): kaynak modülün `follows_failed_assembly`'si alınmaz. Birinci
toplantının zamanı ve katılımı `first_*`, çoğunluk aranmayan ikinci toplantınınki (md. 9/2;
olağanüstüde de, A-1) `second_*` alanlarındadır; genel kurulun yapıldığı toplantı
`held_at_meeting`'dir.

YETER SAYI (U7, O7): `student_count_snapshot`, `quorum_base`, `quorum_multiplier`, `quorum_required`
ilanda (`CAGRILDI → ILAN_EDILDI`) birlikte dondurulur; dondurulduktan sonra değişmez (sert — yeter sayı
hesabı): ne örnek kaydı ne toplu güncelleme onları değiştirir, katılım düzeltmesi de onlara uzanmaz.
`ILAN_EDILDI` ve sonrasındaki her durumda doludur.

DURUM MAKİNESİ (tasarım §7.1; plan F2 §1.1-1): kayıt `PLANLANDI` açılır; `PLANLANDI → CAGRILDI →
ILAN_EDILDI → YAPILDI → TUTANAK_TAMAM`, `ILAN_EDILDI → YETER_SAYI_YOK → YAPILDI`; dört durumdan
(`PLANLANDI`, `CAGRILDI`, `ILAN_EDILDI`, `YETER_SAYI_YOK`) `IPTAL`. Koruma `save()`'dedir: hangi servis
yazarsa yazsın geçiş veritabanındaki durumla denetlenir (`BoardDecision` kalıbı).

KATILIM DÜZELTMESİ (`AttendanceCorrection`): ekleme-yalnızdır; satır değişmez, silinmez. Genel kuruldaki
sayı son düzeltme satırının değeridir (yazanı `services.genel_kurul.katilim_duzelt`, F2 5. adım).
Düzeltilebilen alanlar kapalı listedir (`DUZELTILEBILIR_ALANLAR`); yeter sayının dört alanı listede
yoktur (veritabanı kısıtı).

MD. 14/5 ÇAĞRISININ İKİ BAĞI (kullanıcı kararı S6 (ii), hukuken geçersiz işlem; plan F2 §7 U13):
Denetleme Kurulunun çağrısı iki yabancı anahtardadır: genel kuruldaki `call_audit_report` ve rapordaki
`escalated_assembly`. Veritabanı kısıtı yalnız kendi satırını okur: `ck_generalassembly_dk_raporu`
genel kuruldaki bağı Denetleme Kurulunun çağrısına, `ck_auditreport_md6_cagri` rapordaki bağı md. 6
işaretine bağlar. Genel kuruldaki bağın da işaretli rapor istemesi ve iki bağın birbirini göstermesi
MODEL KATMANINDADIR (başka tabloyu okur): genel kurulun `save()`'i ve toplu güncellemesi bağlanan
raporun işaretine ve bağına bakar (`_cagri_raporu_denetimi`); raporun tarafı `models.denetim`'dedir
(çağrıya bağlı raporun işareti kaldırılmaz, rapor başka raporla çağrılmış genel kurulu göstermez). Ham
SQL bu korumayı aşar; 7. adımın servisi iki bağı aynı işlemde yazar. İptal edilmiş genel kurulu gösteren
bağ "başka genel kurul" sayılmaz: rapor yeni çağrıya bağlanabilir (bağ izli güncellemeyle taşınır, iptal
edilen kurulun bağı iz olarak kalır; 5. adımın katılım işareti emsali).

ÇAĞRIYI YAZAN ROL (`called_by_role`; plan F2 7. adım): çağrıda yazanın rolü yazılır. md. 13/8'in
çağıranı "başkan ya da müdür"dür ve tek değerdir (`BASKAN_VEYA_MUDUR_13_8`): hangisinin yazdığı bu
alandan okunur (çağrının sahipliği, E05'in imzası). md. 13/8 çağrısında yazan başkan ya da müdürdür
(veritabanı kısıtı).

İBRA OYLAMASI (md. 11/1-c; tasarım §9.6 E10 "YK ve DK ibrası ayrı oylama satırı"; F2 6. adım): ibra
genel kurulun kararıdır, sonucu oylardan hesaplanır (kullanıcı kararı S6 (iii)). Oylama kurul başına
ayrı alanlardadır (`discharge_<yk|dk>_votes_for`, `_votes_against`, `_present_count`): kabul ve ret
birlikte dolar, oy varsa ibra oylanmıştır (`EDILDI` ya da `EDILMEDI`), salonda bulunan oyların
toplamından az olamaz (veritabanı kısıtı). Sonucun oylarla tutarlılığı serviste hesaplanır (payda
toplantının katılımına bağlıdır).

ŞİFRELEME (tasarım §5.3): `call_reason`, `cancel_reason`, gündemin `notes` ve `result_text`'i,
tutanağın `unaudited_documents_note`'u ve düzeltmenin `justification`'ı şifrelidir; değer listesine
girmez, içerik MAC'indedir. Toplantı yeri ve gündem başlığı açık serbest metindir: yalnız içerik
MAC'indedir. Kişi bağları (tutanağın okuyucuları) yalnız içerik MAC'indedir.

KAYIT SİLİNMEZ (altın kural 4, O1): genel kurul `IPTAL` olur, gündem maddesi `removed_by_vote` ile
çıkarılır; bu modüldeki modellerin silme yolu kapalıdır (`SilinmezQuerySet`, `SilinmezOabModel`).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar, Final

from django.apps import apps
from django.db import models
from django.db.models import F, Q

from apps.oab.models._base import (
    AgendaItemKind,
    AgendaResult,
    AssemblyCaller,
    AssemblyKind,
    AssemblyMeeting,
    AssemblyStatus,
    AttendanceKind,
    Discharge,
    SilinmezOabModel,
    SilinmezQuerySet,
)
from apps.okul.models import AccountRole, ImmutableRecord
from shared.crypto import EncryptedTextField

#: Yeter sayının ilanda dondurulan dört alanı (modül başlığı "Yeter sayı").
DONDURULAN_ALANLAR: Final = (
    "student_count_snapshot",
    "quorum_base",
    "quorum_multiplier",
    "quorum_required",
)
YER_MAX = 200
BASLIK_MAX = 200

#: Yeter sayısı dondurulmuş olması gereken durumlar (U7: dondurma ilan geçişindedir).
_ILANDAN_SONRAKI = (
    AssemblyStatus.ILAN_EDILDI,
    AssemblyStatus.YETER_SAYI_YOK,
    AssemblyStatus.YAPILDI,
    AssemblyStatus.TUTANAK_TAMAM,
)
#: Genel kurulun yapıldığı durumlar (yapıldığı toplantı ve ibra yalnız bunlarda).
_YAPILMIS = (AssemblyStatus.YAPILDI, AssemblyStatus.TUTANAK_TAMAM)
#: Çağrısı yapılmamış ya da iptal edilmiş durumlar (çağıran alanı boş olabilir).
_CAGRISIZ = (AssemblyStatus.PLANLANDI, AssemblyStatus.IPTAL)

#: Durum makinesi (modül başlığı); listede olmayan durum son durumdur.
GENEL_KURUL_GECISLERI: Final[dict[str, frozenset[str]]] = {
    AssemblyStatus.PLANLANDI: frozenset({AssemblyStatus.CAGRILDI, AssemblyStatus.IPTAL}),
    AssemblyStatus.CAGRILDI: frozenset({AssemblyStatus.ILAN_EDILDI, AssemblyStatus.IPTAL}),
    AssemblyStatus.ILAN_EDILDI: frozenset(
        {AssemblyStatus.YAPILDI, AssemblyStatus.YETER_SAYI_YOK, AssemblyStatus.IPTAL}
    ),
    AssemblyStatus.YETER_SAYI_YOK: frozenset({AssemblyStatus.YAPILDI, AssemblyStatus.IPTAL}),
    AssemblyStatus.YAPILDI: frozenset({AssemblyStatus.TUTANAK_TAMAM}),
}

GENEL_KURUL_ACILIS_DURUMU_GECERSIZ = "Genel kurul yalnız planlandı durumunda açılır."
GENEL_KURUL_DURUM_GECISI_GECERSIZ = "Genel kurul bu duruma geçirilemez."
YETER_SAYI_DEGISMEZ = "Dondurulmuş yeter sayı değiştirilemez (md. 9/2; hesap bütünlüğü)."
KATILIM_DAGILIMI_GECERSIZ = (
    "Katılımın türe göre dağılımı yalnız tanımlı türlerin sıfır ya da daha büyük sayılarıdır."
)
DUZELTME_DEGISMEZ = "Katılım düzeltmesi değiştirilemez; yeni düzeltme satırı eklenir."
DK_RAPORU_ISARETSIZ = (
    "Denetleme Kurulunun olağanüstü genel kurul çağrısı, yönetim kurulunun md. 6'ya aykırı faaliyeti "
    "işaretlenmiş raporla açılır (md. 14/5)."
)
DK_RAPORU_BASKA_KURULDA = "Denetim raporu başka bir olağanüstü genel kurulun çağrısını gösteriyor."

#: Genel kuruldaki md. 14/5 bağının alan adları (`update_fields` ve toplu güncelleme ikisini de alır).
_CAGRI_RAPORU_ALANLARI: Final = frozenset({"call_audit_report", "call_audit_report_id"})

#: Katılım düzeltmesinin düzeltebildiği sayı alanları (modül başlığı "Katılım düzeltmesi"). Türe
#: göre dağılımın her türü ayrı alandır (`attendance_by_kind.<tür>`).
DUZELTILEBILIR_ALANLAR: Final = (
    "first_attendee_count",
    "second_attendee_count",
    "parent_students_count",
    "observer_count",
    *(f"attendance_by_kind.{tur}" for tur in AttendanceKind.values),
)


class GenelKurulKaydiGecersiz(ValueError):
    """Genel kurul kaydı modelin kuralını bozuyor (Türkçe ileti; içerik taşımaz)."""


def _cagri_raporu_denetimi(rapor: object, kurul_pkleri: list[int | None]) -> None:
    """md. 14/5 bağı (modül başlığı): rapor md. 6 işaretli olmalı, iptal edilmemiş başka genel kurulu
    göstermemeli.

    `rapor` örnek ya da birincil anahtardır; boşsa bağ yoktur. Rapor yoksa yabancı anahtar kısıtı
    reddeder. Henüz kaydedilmemiş genel kurulun anahtarı boştur: rapor bir genel kurulu gösteriyorsa
    o, bu değildir. Raporun gösterdiği genel kurul iptal edildiyse bağ serbesttir (modül başlığı).
    """
    rapor_pk = getattr(rapor, "pk", rapor)
    if rapor_pk is None:
        return
    deger = (
        apps.get_model("oab", "AuditReport")
        ._base_manager.filter(pk=rapor_pk)
        .values("md6_violation_found", "escalated_assembly_id")
        .first()
    )
    if deger is None:
        return
    if not deger["md6_violation_found"]:
        raise GenelKurulKaydiGecersiz(DK_RAPORU_ISARETSIZ)
    bag = deger["escalated_assembly_id"]
    if (
        bag is not None
        and any(pk != bag for pk in kurul_pkleri)
        and not GeneralAssembly._base_manager.filter(pk=bag, status=AssemblyStatus.IPTAL).exists()
    ):
        raise GenelKurulKaydiGecersiz(DK_RAPORU_BASKA_KURULDA)


class _GenelKurulQuerySet(SilinmezQuerySet):
    """Toplu güncelleme dondurulmuş yeter sayıyı değiştirmez, md. 14/5 bağını bozmaz; silme kapalı."""

    def update(self, **kwargs: Any) -> int:
        if (
            set(kwargs) & set(DONDURULAN_ALANLAR)
            and self.filter(quorum_required__isnull=False).exists()
        ):
            raise ImmutableRecord(YETER_SAYI_DEGISMEZ)
        for ad in _CAGRI_RAPORU_ALANLARI & set(kwargs):
            _cagri_raporu_denetimi(kwargs[ad], list(self.values_list("pk", flat=True)))
        return super().update(**kwargs)


def katilim_dagilimi_gecerli_mi(deger: object) -> bool:
    """`attendance_by_kind`: tanımlı türlerin sıfır ya da daha büyük tamsayıları (boş sözlük olur)."""
    if not isinstance(deger, Mapping):
        return False
    return all(
        tur in AttendanceKind.values
        and isinstance(sayi, int)
        and not isinstance(sayi, bool)
        and sayi >= 0
        for tur, sayi in deger.items()
    )


def _ibra_oylari_kisiti(kurul: str) -> models.CheckConstraint:
    """Bir kurulun ibra oylamasının kısıtı (`discharge_<kurul>_*`)."""
    onek = f"discharge_{kurul}"
    return models.CheckConstraint(
        condition=Q(
            **{
                f"{onek}_votes_for__isnull": True,
                f"{onek}_votes_against__isnull": True,
                f"{onek}_present_count__isnull": True,
            }
        )
        | (
            Q(
                **{
                    f"{onek}_votes_for__isnull": False,
                    f"{onek}_votes_against__isnull": False,
                    f"{onek}__in": [Discharge.EDILDI, Discharge.EDILMEDI],
                }
            )
            & (
                Q(**{f"{onek}_present_count__isnull": True})
                | Q(
                    **{
                        f"{onek}_present_count__gte": F(f"{onek}_votes_for")
                        + F(f"{onek}_votes_against")
                    }
                )
            )
        ),
        name=f"ck_generalassembly_ibra_oylari_{kurul}",
    )


class GeneralAssembly(SilinmezOabModel):
    """Genel kurul (modül başlığı); `term` kapanacak, `opens_term` olağanda açılacak dönemdir."""

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "term",
        "opens_term",
        "kind",
        "called_by",
        "called_by_role",
        "call_decision",
        "call_document",
        "call_audit_report",
        "member_application_count",
        "member_count_declared",
        "announced_on",
        "first_meeting_at",
        "second_meeting_at",
        "second_announced_on",
        "student_count_snapshot",
        "quorum_base",
        "quorum_multiplier",
        "quorum_required",
        "first_attendee_count",
        "second_attendee_count",
        "held_at_meeting",
        "attendance_by_kind",
        "parent_students_count",
        "observer_count",
        "discharge_yk",
        "discharge_dk",
        "discharge_yk_votes_for",
        "discharge_yk_votes_against",
        "discharge_yk_present_count",
        "discharge_dk_votes_for",
        "discharge_dk_votes_against",
        "discharge_dk_present_count",
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
        "called_by",
        "called_by_role",
        "call_reason",
        "call_decision",
        "call_document",
        "call_audit_report",
        "member_application_count",
        "member_count_declared",
        "announced_on",
        "venue",
        "first_meeting_at",
        "second_meeting_at",
        "second_announced_on",
        "student_count_snapshot",
        "quorum_base",
        "quorum_multiplier",
        "quorum_required",
        "first_attendee_count",
        "second_attendee_count",
        "held_at_meeting",
        "attendance_by_kind",
        "parent_students_count",
        "observer_count",
        "discharge_yk",
        "discharge_dk",
        "discharge_yk_votes_for",
        "discharge_yk_votes_against",
        "discharge_yk_present_count",
        "discharge_dk_votes_for",
        "discharge_dk_votes_against",
        "discharge_dk_present_count",
        "status",
        "rule_warnings",
        "cancel_reason",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)
    IZ_DONEM_ALANI: ClassVar[str] = "term"

    #: Kapanacak dönem; yalnız yeni açılan okulun ilk genel kurulunda boş (S5 (i)).
    term = models.ForeignKey(
        "oab.OabTerm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
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
    #: Çağıran; çağrıdan (`CAGRILDI`) itibaren zorunlu, kapalı liste (md. 9/1, 9/6).
    called_by = models.CharField(
        "çağıran", max_length=32, choices=AssemblyCaller.choices, blank=True, default=""
    )
    #: Çağrıyı yazanın rolü (modül başlığı "Çağrıyı yazan rol"); çağrıda yazılır.
    called_by_role = models.CharField(
        "çağrıyı yazan rol", max_length=24, choices=AccountRole.choices, blank=True, default=""
    )
    #: Çağrı nedeni (olağanüstüde zorunlu; serbest metin, şifreli).
    call_reason = EncryptedTextField("çağrı nedeni", blank=True, default="")
    call_decision = models.ForeignKey(
        "oab.BoardDecision",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="çağrı kararı",
    )
    #: Müdür ya da Denetleme Kurulu yazısı, üye başvurusu (gelen-giden evrak kaydı).
    call_document = models.ForeignKey(
        "oab.DocumentRecord",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="çağrı yazısı",
    )
    #: Denetleme Kurulu çağrısında md. 6 aykırılık işaretli rapor (md. 14/5).
    call_audit_report = models.ForeignKey(
        "oab.AuditReport",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="çağrıyı açan denetim raporu",
    )
    #: Üye başvurusunda başvuran sayısı (kişi listesi tutulmaz; md. 9/6).
    member_application_count = models.PositiveIntegerField(
        "başvuran üye sayısı", null=True, blank=True
    )
    #: Üye başvurusunda oranın paydası: elle girilen üye sayısı (plan F2 §7 U12).
    member_count_declared = models.PositiveIntegerField(
        "beyan edilen üye sayısı", null=True, blank=True
    )
    announced_on = models.DateField("ilan günü", null=True, blank=True)
    venue = models.CharField("toplantı yeri", max_length=YER_MAX, blank=True, default="")
    first_meeting_at = models.DateTimeField("birinci toplantı", null=True, blank=True)
    second_meeting_at = models.DateTimeField("ikinci toplantı", null=True, blank=True)
    second_announced_on = models.DateField("ikinci toplantının ilan günü", null=True, blank=True)
    student_count_snapshot = models.PositiveIntegerField("öğrenci mevcudu", null=True, blank=True)
    quorum_base = models.PositiveSmallIntegerField("yeter sayı tabanı", null=True, blank=True)
    quorum_multiplier = models.PositiveSmallIntegerField(
        "yeter sayı çarpanı", null=True, blank=True
    )
    quorum_required = models.PositiveIntegerField("toplantı yeter sayısı", null=True, blank=True)
    first_attendee_count = models.PositiveIntegerField(
        "birinci toplantıya katılan", null=True, blank=True
    )
    second_attendee_count = models.PositiveIntegerField(
        "ikinci toplantıya katılan", null=True, blank=True
    )
    held_at_meeting = models.CharField(
        "yapıldığı toplantı",
        max_length=8,
        choices=AssemblyMeeting.choices,
        blank=True,
        default="",
    )
    #: Katılımın türe göre dağılımı (`AttendanceKind` anahtarlı sayılar).
    attendance_by_kind = models.JSONField("türe göre katılım", default=dict, blank=True)
    #: Velisi katılan öğrenci sayısı (TKB E.4 §3.2 Tablo 1; kişi başı sayımdan ayrı, U16).
    parent_students_count = models.PositiveIntegerField(
        "velisi katılan öğrenci sayısı", null=True, blank=True
    )
    #: Gözlemci öğrenci (md. 9/5): oy yok, katılım sayısına hiçbir yoldan eklenmez.
    observer_count = models.PositiveIntegerField("gözlemci öğrenci", null=True, blank=True)
    discharge_yk = models.CharField(
        "yönetim kurulunun ibrası",
        max_length=12,
        choices=Discharge.choices,
        blank=True,
        default="",
    )
    discharge_dk = models.CharField(
        "Denetleme Kurulunun ibrası",
        max_length=12,
        choices=Discharge.choices,
        blank=True,
        default="",
    )
    #: İbra oylaması kurul başına ayrı satırdır (md. 11/1-c; tasarım §9.6 E10 "YK ve DK ibrası ayrı
    #: oylama satırı"): kabul, ret ve oylamada salonda bulunan. İbra sonucu bu oylardan hesaplanır
    #: (`genel_kurul.karar_cogunlugu`, kullanıcı kararı S6 (iii); servis `genel_kurul.ibra_yaz`).
    discharge_yk_votes_for = models.PositiveIntegerField(
        "yönetim kurulunun ibrasında kabul oyu", null=True, blank=True
    )
    discharge_yk_votes_against = models.PositiveIntegerField(
        "yönetim kurulunun ibrasında ret oyu", null=True, blank=True
    )
    discharge_yk_present_count = models.PositiveIntegerField(
        "yönetim kurulunun ibrasında salonda bulunan", null=True, blank=True
    )
    discharge_dk_votes_for = models.PositiveIntegerField(
        "Denetleme Kurulunun ibrasında kabul oyu", null=True, blank=True
    )
    discharge_dk_votes_against = models.PositiveIntegerField(
        "Denetleme Kurulunun ibrasında ret oyu", null=True, blank=True
    )
    discharge_dk_present_count = models.PositiveIntegerField(
        "Denetleme Kurulunun ibrasında salonda bulunan", null=True, blank=True
    )
    status = models.CharField(
        "durum", max_length=16, choices=AssemblyStatus.choices, default=AssemblyStatus.PLANLANDI
    )
    #: Kaydın güncel uyarı özeti (tasarım §5 O3).
    rule_warnings = models.JSONField("kural uyarıları", default=list, blank=True)
    #: `IPTAL`'de zorunlu gerekçe (şifreli; kim `updated_by` ve iz satırıdır).
    cancel_reason = EncryptedTextField("iptal gerekçesi", blank=True, default="")

    objects = _GenelKurulQuerySet.as_manager()

    class Meta:
        verbose_name = "genel kurul"
        verbose_name_plural = "genel kurullar"
        ordering = ["-id"]
        base_manager_name = "objects"
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
            models.CheckConstraint(
                condition=Q(called_by__in=["", *AssemblyCaller.values]),
                name="ck_generalassembly_called_by",
            ),
            models.CheckConstraint(
                condition=Q(called_by_role__in=["", *AccountRole.values]),
                name="ck_generalassembly_called_by_role",
            ),
            # md. 13/8'in çağrısını başkan ya da müdür yazar (modül başlığı "Çağrıyı yazan rol").
            models.CheckConstraint(
                condition=~Q(called_by=AssemblyCaller.BASKAN_VEYA_MUDUR_13_8)
                | Q(status__in=_CAGRISIZ)
                | Q(called_by_role__in=[AccountRole.BASKAN, AccountRole.MUDUR]),
                name="ck_generalassembly_13_8_yazan",
            ),
            models.CheckConstraint(
                condition=Q(held_at_meeting__in=["", *AssemblyMeeting.values]),
                name="ck_generalassembly_held_at_meeting",
            ),
            models.CheckConstraint(
                condition=Q(discharge_yk__in=["", *Discharge.values])
                & Q(discharge_dk__in=["", *Discharge.values]),
                name="ck_generalassembly_discharge",
            ),
            # Kapanacak dönem yalnız yeni okulun ilk genel kurulunda boştur; o zaman açılacak dönem
            # doludur (S5 (i)).
            models.CheckConstraint(
                condition=Q(term__isnull=False)
                | Q(called_by=AssemblyCaller.MUDUR_YENI_OKUL, opens_term__isnull=False),
                name="ck_generalassembly_donem",
            ),
            # Olağanüstü genel kurul dönem açmaz (md. 13/8; plan F2 §5.2).
            models.CheckConstraint(
                condition=~Q(kind=AssemblyKind.OLAGANUSTU) | Q(opens_term__isnull=True),
                name="ck_generalassembly_olaganustu_donem_acmaz",
            ),
            # Çağrıdan itibaren çağıran zorunludur (kapalı liste).
            models.CheckConstraint(
                condition=Q(status__in=_CAGRISIZ) | ~Q(called_by=""),
                name="ck_generalassembly_cagiran",
            ),
            # Olağanüstüde çağrı nedeni zorunludur.
            models.CheckConstraint(
                condition=~Q(kind=AssemblyKind.OLAGANUSTU)
                | Q(status__in=_CAGRISIZ)
                | ~Q(call_reason=""),
                name="ck_generalassembly_olaganustu_neden",
            ),
            models.CheckConstraint(
                condition=~Q(status=AssemblyStatus.IPTAL) | ~Q(cancel_reason=""),
                name="ck_generalassembly_iptal_gerekcesi",
            ),
            # Yeter sayı ilanda dondurulur (U7): ilandan sonraki her durumda doludur.
            models.CheckConstraint(
                condition=~Q(status__in=_ILANDAN_SONRAKI) | Q(quorum_required__isnull=False),
                name="ck_generalassembly_yeter_sayi_ilanda",
            ),
            # Yapıldığı toplantı yalnız ve her zaman yapılmış genel kurulda.
            models.CheckConstraint(
                condition=(Q(status__in=_YAPILMIS) & ~Q(held_at_meeting=""))
                | (~Q(status__in=_YAPILMIS) & Q(held_at_meeting="")),
                name="ck_generalassembly_yapildigi_toplanti",
            ),
            models.CheckConstraint(
                condition=~Q(held_at_meeting=AssemblyMeeting.BIRINCI)
                | Q(first_meeting_at__isnull=False, first_attendee_count__isnull=False),
                name="ck_generalassembly_birinci_toplanti",
            ),
            # İkinci toplantı birincide yeter sayı sağlanamayınca yapılır: birincinin sayımı da var.
            models.CheckConstraint(
                condition=~Q(held_at_meeting=AssemblyMeeting.IKINCI)
                | Q(
                    second_meeting_at__isnull=False,
                    second_attendee_count__isnull=False,
                    first_attendee_count__isnull=False,
                ),
                name="ck_generalassembly_ikinci_toplanti",
            ),
            models.CheckConstraint(
                condition=~Q(status=AssemblyStatus.YETER_SAYI_YOK)
                | Q(first_attendee_count__isnull=False),
                name="ck_generalassembly_yeter_sayi_yok",
            ),
            models.CheckConstraint(
                condition=Q(second_meeting_at__isnull=True)
                | Q(first_meeting_at__isnull=True)
                | Q(second_meeting_at__gt=F("first_meeting_at")),
                name="ck_generalassembly_ikinci_toplanti_sirasi",
            ),
            models.CheckConstraint(
                condition=Q(second_announced_on__isnull=True, second_attendee_count__isnull=True)
                | Q(second_meeting_at__isnull=False),
                name="ck_generalassembly_ikinci_toplanti_alanlari",
            ),
            # İbra yalnız yapılmış genel kurulda.
            models.CheckConstraint(
                condition=Q(discharge_yk="", discharge_dk="") | Q(status__in=_YAPILMIS),
                name="ck_generalassembly_ibra",
            ),
            # İbra oylaması kurul başına: kabul ve ret birlikte; oy varsa ibra oylanmıştır (edildi ya da
            # edilmedi); salonda bulunan oyların toplamından az olamaz (S6 (iii), hesap bütünlüğü).
            *(_ibra_oylari_kisiti(kurul) for kurul in ("yk", "dk")),
            # md. 14/5 raporu yalnız Denetleme Kurulunun çağrısında. Raporun md. 6 işareti başka
            # tablodadır, kısıt okuyamaz: `save()` ve toplu güncelleme denetler (modül başlığı, S6 (ii)).
            models.CheckConstraint(
                condition=Q(call_audit_report__isnull=True)
                | Q(called_by=AssemblyCaller.DENETLEME_KURULU),
                name="ck_generalassembly_dk_raporu",
            ),
            # Başvuran ve üye sayısı yalnız üyelerin yazılı başvurusunda (md. 9/6, U12).
            models.CheckConstraint(
                condition=Q(
                    member_application_count__isnull=True, member_count_declared__isnull=True
                )
                | Q(called_by=AssemblyCaller.UYE_BASVURUSU),
                name="ck_generalassembly_uye_basvurusu",
            ),
            # Bir hazırlık dönemini tek genel kurul açar.
            models.UniqueConstraint(
                fields=["opens_term"],
                condition=Q(opens_term__isnull=False),
                name="uq_generalassembly_opens_term",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} genel kurul"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Durum makinesi, dondurulmuş yeter sayı, katılım dağılımı ve md. 14/5 bağı denetlenir
        (modül başlığı)."""
        alanlar = kwargs.get("update_fields")
        if (alanlar is None or "attendance_by_kind" in alanlar) and not (
            katilim_dagilimi_gecerli_mi(self.attendance_by_kind)
        ):
            raise GenelKurulKaydiGecersiz(KATILIM_DAGILIMI_GECERSIZ)
        if alanlar is None or _CAGRI_RAPORU_ALANLARI & set(alanlar):
            _cagri_raporu_denetimi(self.call_audit_report_id, [self.pk])
        if self._state.adding:
            if self.status != AssemblyStatus.PLANLANDI:
                raise GenelKurulKaydiGecersiz(GENEL_KURUL_ACILIS_DURUMU_GECERSIZ)
        else:
            eski = (
                type(self)
                ._base_manager.filter(pk=self.pk)
                .values("status", *DONDURULAN_ALANLAR)
                .first()
            )
            if eski is not None:
                if (
                    (alanlar is None or "status" in alanlar)
                    and eski["status"] != self.status
                    and self.status
                    not in GENEL_KURUL_GECISLERI.get(str(eski["status"]), frozenset())
                ):
                    raise GenelKurulKaydiGecersiz(GENEL_KURUL_DURUM_GECISI_GECERSIZ)
                if eski["quorum_required"] is not None and any(
                    (alanlar is None or ad in alanlar) and eski[ad] != getattr(self, ad)
                    for ad in DONDURULAN_ALANLAR
                ):
                    raise ImmutableRecord(YETER_SAYI_DEGISMEZ)
        super().save(*args, **kwargs)


class AgendaItem(SilinmezOabModel):
    """Genel kurul gündem maddesi (tasarım §5.2.3; §12.A AYNEN → UYARLA).

    (genel kurul, sıra) tekildir; SQLite tekil kısıtı ertelemediği için sıra değişikliği servis
    katmanında geçici değerle iki adımda yapılır. Çıkarılan madde silinmez: `removed_by_vote` (md. 9/4);
    çıkarılan madde görüşülmez, sonucu yoktur. Kabul ya da ret sonucu oylarla birlikte yazılır (sonuç
    oylardan hesaplanır; S6 (iii) servistedir). Oylamada salonda bulunan sayı (`present_count`; F2 5.
    adım, kullanıcı kararı S2) girilmişse karar çoğunluğunun paydası odur, girilmemişse toplantının
    katılım sayısıdır; yalnız oyları girilmiş maddede bulunur.
    """

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "assembly",
        "order",
        "kind",
        "added_by_vote",
        "removed_by_vote",
        "change_votes_for",
        "change_votes_against",
        "votes_for",
        "votes_against",
        "present_count",
        "result",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "assembly",
        "order",
        "kind",
        "title",
        "notes",
        "added_by_vote",
        "removed_by_vote",
        "change_votes_for",
        "change_votes_against",
        "result_text",
        "votes_for",
        "votes_against",
        "present_count",
        "result",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("removed_by_vote", "result")
    IZ_DONEM_ALANI: ClassVar[str] = "assembly__term"

    assembly = models.ForeignKey(
        GeneralAssembly,
        on_delete=models.PROTECT,
        related_name="agenda_items",
        verbose_name="genel kurul",
    )
    order = models.PositiveSmallIntegerField("sıra")
    kind = models.CharField("tür", max_length=20, choices=AgendaItemKind.choices)
    title = models.CharField("başlık", max_length=BASLIK_MAX)
    notes = EncryptedTextField("not", blank=True, default="")
    #: md. 9/4: gündeme ekleme ve çıkarma oy çokluğuyla.
    added_by_vote = models.BooleanField("oylamayla eklendi", default=False)
    removed_by_vote = models.BooleanField("oylamayla çıkarıldı", default=False)
    change_votes_for = models.PositiveIntegerField(
        "gündem değişikliğinde kabul oyu", null=True, blank=True
    )
    change_votes_against = models.PositiveIntegerField(
        "gündem değişikliğinde ret oyu", null=True, blank=True
    )
    result_text = EncryptedTextField("sonuç metni", blank=True, default="")
    votes_for = models.PositiveIntegerField("kabul oyu", null=True, blank=True)
    votes_against = models.PositiveIntegerField("ret oyu", null=True, blank=True)
    #: Oylamada salonda bulunan üye sayısı (toplantıdan ayrılan varsa; kullanıcı kararı S2).
    present_count = models.PositiveIntegerField("oylamada salonda bulunan", null=True, blank=True)
    result = models.CharField(
        "sonuç", max_length=12, choices=AgendaResult.choices, blank=True, default=""
    )

    objects = SilinmezQuerySet.as_manager()

    class Meta:
        verbose_name = "gündem maddesi"
        verbose_name_plural = "gündem maddeleri"
        ordering = ["assembly", "order"]
        base_manager_name = "objects"
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=AgendaItemKind.values), name="ck_agendaitem_kind"
            ),
            models.CheckConstraint(
                condition=Q(result__in=["", *AgendaResult.values]), name="ck_agendaitem_result"
            ),
            # Gündem değişikliğinin oyları yalnız oylamayla eklenen ya da çıkarılan maddede.
            models.CheckConstraint(
                condition=Q(change_votes_for__isnull=True, change_votes_against__isnull=True)
                | Q(added_by_vote=True)
                | Q(removed_by_vote=True),
                name="ck_agendaitem_degisiklik_oylari",
            ),
            # Çıkarılan madde görüşülmez.
            models.CheckConstraint(
                condition=Q(removed_by_vote=False) | Q(result=""),
                name="ck_agendaitem_cikarilan_sonucsuz",
            ),
            # Kabul ve ret oylardan hesaplanır: oylar yazılıdır.
            models.CheckConstraint(
                condition=~Q(result__in=(AgendaResult.KABUL, AgendaResult.RET))
                | Q(votes_for__isnull=False, votes_against__isnull=False),
                name="ck_agendaitem_sonuc_oylari",
            ),
            # Salondaki sayı yalnız oyları girilmiş maddede ve oyların toplamından az değil.
            models.CheckConstraint(
                condition=Q(present_count__isnull=True)
                | Q(
                    votes_for__isnull=False,
                    votes_against__isnull=False,
                    present_count__gte=F("votes_for") + F("votes_against"),
                ),
                name="ck_agendaitem_salondaki_sayi",
            ),
            models.UniqueConstraint(fields=["assembly", "order"], name="uq_agendaitem_sira"),
        ]

    def __str__(self) -> str:
        return f"{self.order}. gündem maddesi"


class AssemblyMinutes(SilinmezOabModel):
    """Genel kurul tutanağının yapısal alanları (tasarım §5.2.3; §12.A UYARLA).

    Bire bir genel kurula bağlıdır. Divan `OrganMembership(DIVAN)`'dan, seçilenler
    `OrganMembership(SECILDI)`'den okunur (tek kaynak, O6). Kaynak modülün serbest metin adları kişi
    kaydına bağlanır; `authorization_note` (md. 11/1-e) `AgendaItem(YETKILENDIRME).result_text`'e taşındı.
    """

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = ("assembly", "handed_to_new_yk_on")
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "assembly",
        "yk_report_reader",
        "dk_report_reader",
        "budget_presenter",
        "unaudited_documents_note",
        "handed_to_new_yk_on",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ()
    IZ_DONEM_ALANI: ClassVar[str] = "assembly__term"

    assembly = models.OneToOneField(
        GeneralAssembly,
        on_delete=models.PROTECT,
        related_name="minutes",
        verbose_name="genel kurul",
    )
    yk_report_reader = models.ForeignKey(
        "oab.OabPerson",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="yönetim kurulu faaliyet raporunu okuyan",
    )
    dk_report_reader = models.ForeignKey(
        "oab.OabPerson",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Denetleme Kurulu raporunu okuyan",
    )
    budget_presenter = models.ForeignKey(
        "oab.OabPerson",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="tahmini bütçeyi sunan",
    )
    #: İbra edilmeyen muhasebe evrakının listesi (md. 11/1-ç; şifreli).
    unaudited_documents_note = EncryptedTextField(
        "ibra edilmeyen muhasebe evrakı", blank=True, default=""
    )
    #: Yeni yönetim kuruluna teslim günü (md. 10/1-ç; F2'de yalnız tarih, U29).
    handed_to_new_yk_on = models.DateField(
        "yeni yönetim kuruluna teslim günü", null=True, blank=True
    )

    objects = SilinmezQuerySet.as_manager()

    class Meta:
        verbose_name = "genel kurul tutanağı"
        verbose_name_plural = "genel kurul tutanakları"
        ordering = ["-id"]
        base_manager_name = "objects"

    def __str__(self) -> str:
        return "Genel kurul tutanağı"


class _EklemeYalnizQuerySet(SilinmezQuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ImmutableRecord(DUZELTME_DEGISMEZ)


class AttendanceCorrection(SilinmezOabModel):
    """Genel kurul katılım sayısının gerekçeli düzeltmesi (tasarım §5.2.3; YENİ; modül başlığı).

    Ekleme-yalnızdır: yazıldıktan sonra değişmez, silinmez. Birinci toplantının katılımı birinci,
    ikinci toplantınınki ikinci toplantıya yazılır; dondurulmuş yeter sayı düzeltilemez (kısıt).
    """

    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = (
        "assembly",
        "meeting",
        "field",
        "old_value",
        "new_value",
        "corrected_by",
        "corrected_at",
    )
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "assembly",
        "meeting",
        "field",
        "old_value",
        "new_value",
        "justification",
        "corrected_by",
        "corrected_at",
    )
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ()
    IZ_DONEM_ALANI: ClassVar[str] = "assembly__term"

    assembly = models.ForeignKey(
        GeneralAssembly,
        on_delete=models.PROTECT,
        related_name="attendance_corrections",
        verbose_name="genel kurul",
    )
    meeting = models.CharField("toplantı", max_length=8, choices=AssemblyMeeting.choices)
    #: Düzeltilen sayı alanı (`DUZELTILEBILIR_ALANLAR`).
    field = models.CharField("düzeltilen alan", max_length=48)
    old_value = models.PositiveIntegerField("önceki değer", null=True, blank=True)
    new_value = models.PositiveIntegerField("yeni değer")
    justification = EncryptedTextField("gerekçe")
    corrected_by = models.ForeignKey(
        "okul.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="düzelten hesap",
    )
    corrected_at = models.DateTimeField("düzeltme anı")

    objects = _EklemeYalnizQuerySet.as_manager()

    class Meta:
        verbose_name = "katılım düzeltmesi"
        verbose_name_plural = "katılım düzeltmeleri"
        ordering = ["assembly", "corrected_at", "id"]
        base_manager_name = "objects"
        constraints = [
            models.CheckConstraint(
                condition=Q(meeting__in=AssemblyMeeting.values),
                name="ck_attendancecorrection_meeting",
            ),
            # Dondurulmuş yeter sayı düzeltilemez: alan kapalı listededir.
            models.CheckConstraint(
                condition=Q(field__in=DUZELTILEBILIR_ALANLAR),
                name="ck_attendancecorrection_field",
            ),
            # Toplantıya ait sayı kendi toplantısına yazılır.
            models.CheckConstraint(
                condition=~Q(field="first_attendee_count") | Q(meeting=AssemblyMeeting.BIRINCI),
                name="ck_attendancecorrection_birinci",
            ),
            models.CheckConstraint(
                condition=~Q(field="second_attendee_count") | Q(meeting=AssemblyMeeting.IKINCI),
                name="ck_attendancecorrection_ikinci",
            ),
            models.CheckConstraint(
                condition=Q(old_value__isnull=True) | ~Q(old_value=F("new_value")),
                name="ck_attendancecorrection_degisiklik",
            ),
            models.CheckConstraint(
                condition=~Q(justification=""), name="ck_attendancecorrection_gerekce"
            ),
        ]

    def __str__(self) -> str:
        return "Katılım düzeltmesi"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Yalnız yeni satır yazılır (ekleme-yalnız)."""
        if not self._state.adding:
            raise ImmutableRecord(DUZELTME_DEGISMEZ)
        super().save(*args, **kwargs)
