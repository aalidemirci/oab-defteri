"""Genel kurul, gelen-giden evrak ve genel kurul evrakı uçlarının girdi serileştiricileri (plan F2 §6.1,
11. adım).

Yalnız gövdenin biçimini denetler; kural, durum ve rol denetimi servistedir (`genel_kurul`,
`gelen_giden_evrak`, `genel_kurul_evraki`, `denetim`). Uyarı + gerekçe ilkesi (altın kural 3): gerekçe
gövdede gelir (`gerekce`, `kok_neden`), servis yalnız gerektiğinde ister. Serbest metinlerin üst
sınırları modeldedir (şifreli alanlar TEXT'tir; sınır burada konur).
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.oab.models import (
    AgendaItemKind,
    AgendaResult,
    AssemblyCaller,
    AssemblyKind,
    AssemblyMeeting,
    AuditReport,
    AuditReportKind,
    BookCertifier,
    Discharge,
    DocumentDirection,
    DocumentRecord,
    OabPerson,
    OfficialBook,
    OrganMembership,
    OrganType,
    SeatGroup,
    SeatType,
)
from apps.oab.models.genel_kurul import BASLIK_MAX, YER_MAX
from apps.oab.models.kurul import KISA_METIN_MAX
from apps.oab.services import genel_kurul_evraki

#: Serbest metinlerin üst sınırı (gerekçe, çağrı nedeni, sonuç metni; şifreli sütun TEXT'tir).
_METIN_UST = 4000
#: Gerekçe ve kök neden (ortak "uyarı + gerekçe" bileşeni; `serializers._GerekceMixin` ile aynı).
_GEREKCE_UST = 1000
_KOK_NEDEN_UST = 64
#: Sayıların üst sınırı (PositiveIntegerField).
_SAYI_UST = 2_147_483_647
#: Dış sayının üst sınırı (`DocumentRecord.external_ref`).
_DIS_SAYI_UST = 64
#: Bir istekte işaretlenebilecek satır sayısı (veli listesi satırı).
_ISARET_UST = 5000
#: Resmî yazının basımda düzenlenen muhatabının (idare ve birim) üst sınırı.
_MUHATAP_UST = 160
#: Gündemde en çok madde (sıra değişikliği gövdesi).
_GUNDEM_UST = 200
#: Seçimde en çok aday.
_ADAY_UST = 200

KANAL_ALANLARI = ("distributed_written_on", "posted_board_on", "published_web_on")
#: Tutanak bilgisinin kısmi yazımında alanlar (verilmeyen alan yazılmaz).
TUTANAK_ALANLARI = (
    "yk_report_reader",
    "dk_report_reader",
    "budget_presenter",
    "handed_to_new_yk_on",
)
#: Veli adlı çıktının biçimleri (yoldaki uzantı).
ADLI_BICIM_UZANTILARI = ("pdf", "docx", "xlsx")

CAGRI_RAPORU_TEK = (
    "Denetim raporunu ya seçin ya da yeni raporun bilgilerini girin; ikisi birden olmaz."
)
CAGRI_RAPORU_GEREKLI = (
    "Denetleme Kurulunun çağrısı denetim raporuna bağlanır: raporu seçin ya da bilgilerini girin."
)
TUTANAK_BOS = "Yazılacak tutanak bilgisi verilmedi."
ADAY_FAZLA = f"Bir seçimde en çok {_ADAY_UST} adayın sonucu girilir."


def _sayi(**kwargs: Any) -> serializers.IntegerField:
    return serializers.IntegerField(min_value=0, max_value=_SAYI_UST, **kwargs)


def _secimli_sayi() -> serializers.IntegerField:
    return _sayi(required=False, allow_null=True, default=None)


def _secimli_gun() -> serializers.DateField:
    return serializers.DateField(required=False, allow_null=True, default=None)


def _metin(ust: int = _METIN_UST) -> serializers.CharField:
    return serializers.CharField(max_length=ust, required=False, allow_blank=True, default="")


class GerekceMixin(serializers.Serializer[dict[str, Any]]):
    """Uyarı gerektiren kaydın gerekçesi (altın kural 3); kök neden toplu gerekçeyi bağlar."""

    gerekce = _metin(_GEREKCE_UST)
    kok_neden = _metin(_KOK_NEDEN_UST)


class PlanlaSerializer(GerekceMixin):
    """Genel kurulun planlanması (`genel_kurul.planla`)."""

    kind = serializers.ChoiceField(choices=AssemblyKind.choices)
    first_meeting_at = serializers.DateTimeField()
    venue = serializers.CharField(max_length=YER_MAX, required=False, allow_blank=True, default="")


class ToplantiBilgisiSerializer(GerekceMixin):
    """İlandan önce toplantı zamanı ve yeri (`genel_kurul.toplanti_bilgisini_degistir`); yer verilmezse
    değişmez."""

    first_meeting_at = serializers.DateTimeField()
    venue = serializers.CharField(max_length=YER_MAX, required=False, allow_blank=True)


class GundemMaddesiSerializer(serializers.Serializer[dict[str, Any]]):
    """Çağrıda girilen gündem maddesi (olağanüstü genel kurul; md. 9/6)."""

    title = serializers.CharField(max_length=BASLIK_MAX)
    kind = serializers.ChoiceField(
        choices=AgendaItemKind.choices, required=False, default=AgendaItemKind.DIGER
    )


class _OlaganustuCagriMixin(GerekceMixin):
    call_reason = _metin()
    gundem = GundemMaddesiSerializer(many=True, required=False, default=list)


class CagriSerializer(_OlaganustuCagriMixin):
    """Yönetim kurulunun, başkanın md. 13/8 ve üyelerin başvurusunun çağrısı (`genel_kurul.cagir`)."""

    called_by = serializers.ChoiceField(
        choices=AssemblyCaller.choices, required=False, allow_blank=True, default=""
    )
    member_application_count = _secimli_sayi()
    member_count_declared = _secimli_sayi()
    call_document = serializers.PrimaryKeyRelatedField(
        queryset=DocumentRecord.objects.all(), required=False, allow_null=True, default=None
    )


class MudurCagrisiSerializer(_OlaganustuCagriMixin):
    """Müdürün yazısı (¹): yeni okul daveti (olağanda çağıran kayıttan belirlidir) ya da olağanüstü
    çağrı (md. 9/6, 13/8, 25/2)."""

    called_by = serializers.ChoiceField(
        choices=AssemblyCaller.choices, required=False, allow_blank=True, default=""
    )


class DenetimRaporuSerializer(serializers.Serializer[dict[str, Any]]):
    """Asgari denetim raporu (U13): tür ve rapor günü zorunlu, iki işaret."""

    kind = serializers.ChoiceField(choices=AuditReportKind.choices)
    report_date = serializers.DateField()
    md6_violation_found = serializers.BooleanField()
    irregularity_found = serializers.BooleanField(required=False, default=False)


class DkCagrisiSerializer(_OlaganustuCagriMixin):
    """Denetleme Kurulunun md. 14/5 çağrısı: kayıtlı rapor ya da aynı istekte yazılan rapor (U13)."""

    call_audit_report = serializers.PrimaryKeyRelatedField(
        queryset=AuditReport.objects.all(), required=False, allow_null=True, default=None
    )
    rapor = DenetimRaporuSerializer(required=False, allow_null=True, default=None)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("call_audit_report") is not None and attrs.get("rapor") is not None:
            raise serializers.ValidationError(CAGRI_RAPORU_TEK)
        if attrs.get("call_audit_report") is None and attrs.get("rapor") is None:
            raise serializers.ValidationError(CAGRI_RAPORU_GEREKLI)
        return attrs


class CagriYazisiSerializer(serializers.Serializer[dict[str, Any]]):
    """Çağrı yazısının evrak kaydı bağı (`genel_kurul.cagri_yazisini_bagla`)."""

    kayit = serializers.PrimaryKeyRelatedField(queryset=DocumentRecord.objects.all())


class IlanKanallariSerializer(serializers.Serializer[dict[str, Any]]):
    """Üç kanalın kanıt günleri (md. 9/3); girilmeyen kanal eksiktir."""

    distributed_written_on = _secimli_gun()
    posted_board_on = _secimli_gun()
    published_web_on = _secimli_gun()


class IlanSerializer(GerekceMixin):
    """İlan (`genel_kurul.ilan_et`): kanallar ve (isteğe bağlı) ikinci toplantının tarihi."""

    kanallar = IlanKanallariSerializer(required=False, allow_null=True, default=None)
    second_meeting_at = serializers.DateTimeField(required=False, allow_null=True, default=None)


class IkinciIlanSerializer(GerekceMixin):
    """İkinci toplantının ayrı ilanı (`genel_kurul.ikinci_toplanti_ilani`)."""

    second_meeting_at = serializers.DateTimeField()
    kanallar = IlanKanallariSerializer(required=False, allow_null=True, default=None)


class KanitSerializer(IlanKanallariSerializer, GerekceMixin):
    """İlanın kanal kanıt günlerinin sonradan girilmesi (`genel_kurul.ilan_kanitlarini_yaz`)."""


class KatilimSayilariSerializer(GerekceMixin):
    """Toplantının sayıları (`genel_kurul.Katilim`); gözlemci katılım sayısına girmez (md. 9/5)."""

    attendee_count = _sayi()
    attendance_by_kind = serializers.DictField(
        child=_sayi(), required=False, default=dict, allow_empty=True
    )
    parent_students_count = _secimli_sayi()
    observer_count = _secimli_sayi()


class KatilimDuzeltmeSerializer(GerekceMixin):
    """Katılım düzeltmesi (`genel_kurul.katilim_duzelt`); düzeltmenin gerekçesi zorunludur."""

    toplanti = serializers.ChoiceField(choices=AssemblyMeeting.choices)
    degerler = serializers.DictField(child=_sayi(), allow_empty=False)
    justification = serializers.CharField(max_length=_GEREKCE_UST)


class KatilimIsaretiSerializer(serializers.Serializer[dict[str, Any]]):
    """Katılım işareti (U33): toplantı, işaretlenecek ve işareti kaldırılacak veli satırları."""

    toplanti = serializers.ChoiceField(choices=AssemblyMeeting.choices)
    isaretle = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=list,
        max_length=_ISARET_UST,
    )
    kaldir = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=list,
        max_length=_ISARET_UST,
    )


class ToplantiSorgusuSerializer(serializers.Serializer[dict[str, Any]]):
    """Katılım işaretleri penceresinin sorgusu: toplantı."""

    toplanti = serializers.ChoiceField(choices=AssemblyMeeting.choices)


class GundemEkleSerializer(GerekceMixin):
    """Toplantıda gündeme oylamayla madde (`genel_kurul.gundeme_madde_ekle`; md. 9/4)."""

    title = serializers.CharField(max_length=BASLIK_MAX)
    kind = serializers.ChoiceField(
        choices=AgendaItemKind.choices, required=False, default=AgendaItemKind.DIGER
    )
    sira = serializers.IntegerField(min_value=1, required=False, allow_null=True, default=None)
    change_votes_for = _secimli_sayi()
    change_votes_against = _secimli_sayi()


class GundemSirasiSerializer(serializers.Serializer[dict[str, Any]]):
    """Gündemin yeni sırası: maddelerin kimlikleri, hepsi bir kez."""

    sira = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False, max_length=_GUNDEM_UST
    )


class GundemCikarSerializer(GerekceMixin):
    """Gündemden oylamayla çıkarma (`genel_kurul.gundemden_madde_cikar`)."""

    change_votes_for = _secimli_sayi()
    change_votes_against = _secimli_sayi()


class KararSonucuSerializer(serializers.Serializer[dict[str, Any]]):
    """Gündem maddesinin sonucu (`genel_kurul.karar_sonucu_yaz`): oylanan maddede sonuç oylardan
    hesaplanır."""

    result = serializers.ChoiceField(
        choices=AgendaResult.choices, required=False, allow_null=True, default=None
    )
    votes_for = _secimli_sayi()
    votes_against = _secimli_sayi()
    present_count = _secimli_sayi()
    result_text = _metin()


class AdayOyuSerializer(serializers.Serializer[dict[str, Any]]):
    """Seçimde bir adayın sonucu."""

    uyelik = serializers.PrimaryKeyRelatedField(queryset=OrganMembership.objects.all())
    votes = _secimli_sayi()
    secildi = serializers.BooleanField(required=False, default=False)
    seat_order = serializers.IntegerField(
        min_value=1, required=False, allow_null=True, default=None
    )


class SecimSerializer(GerekceMixin):
    """Seçim maddesinin sonucu (`genel_kurul.secim_sonucu_yaz`)."""

    adaylar = AdayOyuSerializer(many=True)
    liste = serializers.BooleanField(required=False, allow_null=True, default=None)
    acik_oy = serializers.BooleanField(required=False, allow_null=True, default=None)
    result_text = _metin()

    def validate_adaylar(self, deger: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(deger) > _ADAY_UST:
            raise serializers.ValidationError(ADAY_FAZLA)
        return deger


class SecimBicimiSerializer(GerekceMixin):
    """Seçimin biçimi (`genel_kurul.secim_bicimini_yaz`)."""

    liste = serializers.BooleanField()
    acik_oy = serializers.BooleanField()


class IbraOylamasiSerializer(serializers.Serializer[dict[str, Any]]):
    """Bir kurulun ibra oylaması."""

    votes_for = _sayi()
    votes_against = _sayi()
    present_count = _secimli_sayi()


class IbraSerializer(serializers.Serializer[dict[str, Any]]):
    """İbra maddesinin sonucu (`genel_kurul.ibra_yaz`; YK ve DK ayrı oylama)."""

    yk = IbraOylamasiSerializer(required=False, allow_null=True, default=None)
    dk = IbraOylamasiSerializer(required=False, allow_null=True, default=None)
    discharge_yk = serializers.ChoiceField(
        choices=Discharge.choices, required=False, allow_null=True, default=None
    )
    discharge_dk = serializers.ChoiceField(
        choices=Discharge.choices, required=False, allow_null=True, default=None
    )
    unaudited_documents_note = _metin()


class DivanSerializer(GerekceMixin):
    """Divan başkanı ve kâtip (`genel_kurul.divan_sec`; birlik kişisi)."""

    baskan = serializers.PrimaryKeyRelatedField(queryset=OabPerson.objects.all())
    katip = serializers.PrimaryKeyRelatedField(queryset=OabPerson.objects.all())


class AdaySerializer(GerekceMixin):
    """Genel kurulun aday kaydı (`genel_kurul.aday_kaydet`)."""

    person = serializers.PrimaryKeyRelatedField(queryset=OabPerson.objects.all())
    organ = serializers.ChoiceField(
        choices=[
            (OrganType.YONETIM_KURULU, "Yönetim kurulu"),
            (OrganType.DENETLEME_KURULU, "Denetleme Kurulu"),
        ]
    )
    seat_type = serializers.ChoiceField(choices=SeatType.choices)
    seat_group = serializers.ChoiceField(
        choices=SeatGroup.choices, required=False, allow_blank=True, default=""
    )


class TutanakBilgisiSerializer(serializers.Serializer[dict[str, Any]]):
    """Tutanağın kişi bağları ve teslim günü (kısmi yazım: verilmeyen alan yazılmaz, `null` boşaltır)."""

    yk_report_reader = serializers.PrimaryKeyRelatedField(
        queryset=OabPerson.objects.all(), required=False, allow_null=True
    )
    dk_report_reader = serializers.PrimaryKeyRelatedField(
        queryset=OabPerson.objects.all(), required=False, allow_null=True
    )
    budget_presenter = serializers.PrimaryKeyRelatedField(
        queryset=OabPerson.objects.all(), required=False, allow_null=True
    )
    handed_to_new_yk_on = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs:
            raise serializers.ValidationError(TUTANAK_BOS)
        return attrs


class EvrakUretimSerializer(serializers.Serializer[dict[str, Any]]):
    """Genel kurul evrakının üretimi: kip (E07, E08), toplantı (E05, E06, E64) ve resmî yazının (E12)
    muhatabı — il ya da ilçe millî eğitim müdürlüğü seçimi (varsayılan ilçe) ya da basımda düzenlenen
    muhatap (`muhatap_idare` verildiyse; boş bırakılırsa yer tutucu ve uyarı)."""

    kip = serializers.CharField(max_length=8, required=False, allow_blank=True, default="")
    toplanti = serializers.CharField(max_length=8, required=False, allow_blank=True, default="")
    muhatap_secimi = serializers.ChoiceField(
        choices=list(genel_kurul_evraki.MUHATAP_BIRIMLERI),
        required=False,
        allow_blank=True,
        default="",
    )
    muhatap_idare = serializers.CharField(
        max_length=_MUHATAP_UST,
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
    )
    muhatap_birim = serializers.CharField(
        max_length=_MUHATAP_UST, required=False, allow_blank=True, default=""
    )


class AdliEvrakSerializer(serializers.Serializer[dict[str, Any]]):
    """Veli adlı çıktı: biçim ve (toplantılı belgede) toplantı."""

    bicim = serializers.ChoiceField(choices=list(ADLI_BICIM_UZANTILARI))
    toplanti = serializers.CharField(max_length=8, required=False, allow_blank=True, default="")


class DosyaSerializer(serializers.Serializer[dict[str, Any]]):
    """Kullanıcı eki (PDF, JPEG, PNG; tür ve boyut dosya deposunda denetlenir)."""

    file = serializers.FileField(
        error_messages={
            "required": "Dosyayı seçin.",
            "null": "Dosyayı seçin.",
            "invalid": "Dosyayı seçin.",
            "empty": "Seçilen dosya boş.",
        }
    )


class EvrakDefteriSerializer(serializers.Serializer[dict[str, Any]]):
    """Gelen-giden evrak defterinin kaydı (`gelen_giden_evrak.evrak_defteri_olustur`)."""

    certified_by = serializers.ChoiceField(
        choices=BookCertifier.choices, required=False, allow_blank=True, default=""
    )
    certified_on = _secimli_gun()
    certification_no = serializers.CharField(
        max_length=KISA_METIN_MAX, required=False, allow_blank=True, default=""
    )
    page_count = serializers.IntegerField(
        min_value=1, max_value=_SAYI_UST, required=False, allow_null=True, default=None
    )
    last_no_before_program = serializers.IntegerField(
        min_value=1, max_value=_SAYI_UST, required=False, allow_null=True, default=None
    )
    opened_on = _secimli_gun()


class _EvrakKaydiMixin(GerekceMixin):
    tarih = serializers.DateField()
    counterparty = _metin(_GEREKCE_UST)
    subject = _metin(_GEREKCE_UST)
    external_ref = serializers.CharField(
        max_length=_DIS_SAYI_UST, required=False, allow_blank=True, default=""
    )
    record_no = serializers.IntegerField(
        min_value=1, max_value=_SAYI_UST, required=False, allow_null=True, default=None
    )


class EvrakKaydiSerializer(_EvrakKaydiMixin):
    """Gelen ya da giden evrak kaydı (`gelen_giden_evrak.evrak_kaydet`): defter seçilmezse kullanımdaki
    defterin en yenisi."""

    direction = serializers.ChoiceField(choices=DocumentDirection.choices)
    defter = serializers.PrimaryKeyRelatedField(
        queryset=OfficialBook.objects.all(), required=False, allow_null=True, default=None
    )


class GidenKayitSerializer(_EvrakKaydiMixin):
    """Programın ürettiği giden yazının (E12) önerilen kaydının onayı (kullanıcı düzenleyebilir)."""
