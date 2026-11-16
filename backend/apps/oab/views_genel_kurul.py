"""Genel kurul, gelen-giden evrak, genel kurul evrakı ve yıllık iş takvimi uçları (plan F2 §6.1, §6.2;
11. adımın arka yüzü — ekranları 11b'de).

F1c'nin organ, görev bölümü ve evrak uçlarının kalıbıdır: görünüm gövdeyi doğrular, servisi çağırır,
yanıtı kurar; iş mantığı, durum makinesi, kural denetimi ve rol daraltması servistedir (`genel_kurul`,
`gelen_giden_evrak`, `genel_kurul_evraki`, `denetim`). Rol kapısı iki katmandır (F1b-2): uç katmanı
`rol_izinleri.KURALLAR` (adıyla), servis katmanı `Eylem` kapısı. Servisin Türkçe `ValueError`'ı 400 olur;
gerekçe gereken uyarıda 400 `gerekce_gerekli` (altın kural 3: uç gerekçeyi `gerekce` alanında alır).

KİŞİSEL VERİ (altın kural 5). Yanıtlar kişisizdir; yalnız ekranın gösterdiği birlik kişisi adları (divan,
adaylar, seçilenler, tutanağın okuyanları) üyelik ve kişi kaydından çözülür (`OrganMembershipSerializer`
kalıbı; bozuk alan `null`). T.C. kimlik numarası hiçbir yanıtta yoktur. Gerekçe metinleri (katılım
düzeltmesinin gerekçesi, uyum satırlarının gerekçesi) dönmez. Veli adı yalnız katılım işaretleri
penceresinin okumasında (erişim günlüğüne yazılır) ve veli adlı çıktının dosyasında vardır; ikisi de
yalnız program yöneticisine açıktır ve önbelleğe alınmaz (`no-store`).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.oab import selectors
from apps.oab.hatalar import EvrakDosyasiAcilamadi, EvrakDosyasiYazilamadi
from apps.oab.kurallar import KuralPaketiKullanilamaz
from apps.oab.models import (
    AgendaItem,
    AgendaItemKind,
    Announcement,
    AssemblyKind,
    AssemblyMeeting,
    AssemblyMinutes,
    AssemblyStatus,
    BookKind,
    DocumentDirection,
    DocumentFormat,
    DocumentRecord,
    GeneralAssembly,
    GeneratedDocument,
    OabTerm,
    OfficialBook,
    OrganType,
    TermStatus,
)
from apps.oab.serializers import IptalSerializer, OabTermSerializer, OrganMembershipSerializer
from apps.oab.serializers_genel_kurul import (
    TUTANAK_ALANLARI,
    AdaySerializer,
    AdliEvrakSerializer,
    CagriSerializer,
    CagriYazisiSerializer,
    DivanSerializer,
    DkCagrisiSerializer,
    DosyaSerializer,
    EvrakDefteriSerializer,
    EvrakKaydiSerializer,
    EvrakUretimSerializer,
    GerekceMixin,
    GidenKayitSerializer,
    GundemCikarSerializer,
    GundemEkleSerializer,
    GundemSirasiSerializer,
    IbraSerializer,
    IkinciIlanSerializer,
    IlanSerializer,
    KanitSerializer,
    KararSonucuSerializer,
    KatilimDuzeltmeSerializer,
    KatilimIsaretiSerializer,
    KatilimSayilariSerializer,
    MudurCagrisiSerializer,
    PlanlaSerializer,
    SecimBicimiSerializer,
    SecimSerializer,
    ToplantiBilgisiSerializer,
    ToplantiSorgusuSerializer,
    TutanakBilgisiSerializer,
)
from apps.oab.services import (
    denetim,
    gelen_giden_evrak,
    genel_kurul,
    genel_kurul_evraki,
    uyum,
)
from apps.oab.views import _donemler, _hizmet_hatalari
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import Attachment
from apps.okul.oturum import yazar
from apps.okul.permissions import RequiresAdminPassword
from apps.okul.services import dosya_deposu
from shared import dosya_sifreleme
from shared.crypto import is_corrupt
from shared.exceptions import RolYetkisiz

#: Kullanıcı ekinin sahibi olan kayıtlar ve okuma satırları (indirme ucu; tasarım §4.4.2 "Okuma").
_EK_SAHIPLERI: dict[str, rol_izinleri.Satir] = {
    denetim_izi.model_etiketi(AgendaItem): rol_izinleri.Satir.M3,
    denetim_izi.model_etiketi(Announcement): rol_izinleri.Satir.M3,
    denetim_izi.model_etiketi(DocumentRecord): rol_izinleri.Satir.M10,
}
#: İndirilen ekin dosya adının kökü (sözlük §3 "Kaydedilen dosya adı": belge adı + kapsam + tarih).
#: Özgün ad kişi adı taşıyabilir (`Attachment.original_name`, şifreli): yalnız ekin üst bilgisinde
#: (`_ek` → `ad`) ve ekranda görünür, dosya adına girmez (`dosya_deposu.indirme_yaniti`; sözlük §5).
_EK_DOSYA_ADI_KOKLERI: dict[str, str] = {
    AgendaItemKind.YK_FAALIYET_RAPORU: "Genel-Kurul-Eki-Faaliyet-Raporu-ve-Kesin-Hesap",
    AgendaItemKind.TAHMINI_BUTCE: "Genel-Kurul-Eki-Tahmini-Bütçe",
    AgendaItemKind.DK_RAPORU: "Genel-Kurul-Eki-Denetleme-Kurulu-Raporu",
}
_GENEL_KURUL_EKI_KOKU = "Genel-Kurul-Dosya-Eki"
_ILAN_KANITI_KOKU = "İlan-Kanıtı"
_EVRAK_EKI_KOKU = "Gelen-Giden-Evrak-Eki"
#: Kullanıcı ekinin türünden uzantı (kabul edilen türler PDF, JPEG, PNG; `dosya_sifreleme`).
_EK_UZANTILARI: dict[str, str] = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
}
#: Gelen-giden evrak listesinin süzgeç iletileri (sözlük "Genel kurul uçları (F2)"); yönünki servisindir.
DEFTER_GECERSIZ = "Defter geçersiz."
YIL_GECERSIZ = "Yıl geçersiz."


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
def _gerekce(veri: dict[str, Any]) -> uyum.Gerekce | None:
    metin = str(veri.pop("gerekce", "")).strip()
    kok = str(veri.pop("kok_neden", "")).strip()
    return uyum.Gerekce(metin=metin, kok_neden=kok) if metin or kok else None


def _metin(deger: object) -> str | None:
    """Şifreli serbest metin: çözülemezse `null` (bozuk alan)."""
    return None if is_corrupt(deger) else str(deger or "")


def _an(deger: Any) -> str | None:
    return None if deger is None else timezone.localtime(deger).isoformat()


def _gun(deger: Any) -> str | None:
    return None if deger is None else deger.isoformat()


@contextmanager
def _ek_yazma_hatalari() -> Iterator[None]:
    """Kullanıcı ekinin yazımı: geri yükleme sürerken 409, öteki ret (tür, boyut, ad) 400."""
    try:
        yield
    except dosya_deposu.DepoBakimda as exc:
        raise EvrakDosyasiYazilamadi(str(exc)) from exc
    except (dosya_deposu.DosyaDeposuHatasi, dosya_sifreleme.DosyaSifrelemeHatasi) as exc:
        raise serializers.ValidationError(str(exc)) from exc


@contextmanager
def _evrak_yazma_hatalari() -> Iterator[None]:
    """Evrak üretiminde dosya deposunun ret ve bakım hataları 409 (`views._depo_yazma_hatalari`)."""
    try:
        yield
    except (dosya_deposu.DosyaDeposuHatasi, dosya_sifreleme.DosyaSifrelemeHatasi) as exc:
        raise EvrakDosyasiYazilamadi(str(exc)) from exc


def _kurullar() -> QuerySet[GeneralAssembly]:
    return GeneralAssembly.objects.select_related("term__rule_package", "opens_term__rule_package")


def _kurul(pk: int) -> GeneralAssembly:
    kurul: GeneralAssembly = get_object_or_404(_kurullar(), pk=pk)
    return kurul


def _madde(pk: int) -> AgendaItem:
    madde: AgendaItem = get_object_or_404(AgendaItem.objects.all(), pk=pk)
    return madde


def _ekler(sahip: Any) -> list[dict[str, Any]]:
    """Kaydın kullanıcı ekleri (kişisiz üst bilgi; ad kaydın kendisinde görünür, dosya deposu başlığı)."""
    satirlar = Attachment.objects.filter(
        owner_type=denetim_izi.model_etiketi(type(sahip)),
        owner_id=denetim_izi.kimlik_metni(type(sahip), sahip.pk),
        purged_at__isnull=True,
    ).order_by("uploaded_at", "id")
    return [_ek(ek) for ek in satirlar]


def _ek(ek: Attachment) -> dict[str, Any]:
    return {
        "id": ek.pk,
        "ad": None if is_corrupt(ek.original_name) else str(ek.original_name),
        "tur": ek.mime,
        "boyut": ek.size,
        "yukleme_zamani": _an(ek.uploaded_at),
    }


def _uyarilar(satirlar: Any) -> list[dict[str, Any]]:
    """Geçişin eksik ve uyarı satırları (atıflı, kişisiz; `genel_kurul._ozet_satiri`)."""
    return [dict(satir) for satir in satirlar]


# ---------------------------------------------------------------------------
# Genel kurulun yanıtı
# ---------------------------------------------------------------------------
def _kurul_ozeti(kurul: GeneralAssembly) -> dict[str, Any]:
    """Listenin satırı: kişisiz, serbest metin yok."""
    return {
        "id": kurul.pk,
        "kind": kurul.kind,
        "status": kurul.status,
        "term": kurul.term_id,
        "opens_term": kurul.opens_term_id,
        "called_by": kurul.called_by,
        "called_by_role": kurul.called_by_role,
        "first_meeting_at": _an(kurul.first_meeting_at),
        "second_meeting_at": _an(kurul.second_meeting_at),
        "venue": kurul.venue,
        "held_at_meeting": kurul.held_at_meeting,
        "quorum_required": kurul.quorum_required,
    }


def _gundem_maddesi(madde: AgendaItem) -> dict[str, Any]:
    return {
        "id": madde.pk,
        "order": madde.order,
        "kind": madde.kind,
        "title": madde.title,
        "notes": _metin(madde.notes),
        "added_by_vote": madde.added_by_vote,
        "removed_by_vote": madde.removed_by_vote,
        "change_votes_for": madde.change_votes_for,
        "change_votes_against": madde.change_votes_against,
        "result": madde.result,
        "result_text": _metin(madde.result_text),
        "votes_for": madde.votes_for,
        "votes_against": madde.votes_against,
        "present_count": madde.present_count,
        "dosya_eki_belgesi": genel_kurul.DOSYA_EKI_BELGELERI.get(str(madde.kind), ""),
        "ekler": _ekler(madde) if madde.kind in genel_kurul.DOSYA_EKI_BELGELERI else [],
    }


def _duyuru(duyuru: Announcement) -> dict[str, Any]:
    return {
        "id": duyuru.pk,
        "kind": duyuru.kind,
        "status": duyuru.status,
        "distributed_written_on": _gun(duyuru.distributed_written_on),
        "posted_board_on": _gun(duyuru.posted_board_on),
        "removed_board_on": _gun(duyuru.removed_board_on),
        "published_web_on": _gun(duyuru.published_web_on),
        "ekler": _ekler(duyuru),
    }


def _kisi(kisi: Any) -> dict[str, Any] | None:
    if kisi is None:
        return None
    return {"id": kisi.pk, "ad": None if is_corrupt(kisi.full_name) else kisi.full_name}


def _tutanak(kurul: GeneralAssembly) -> dict[str, Any] | None:
    tutanak: AssemblyMinutes | None = (
        AssemblyMinutes.objects.filter(assembly=kurul)
        .select_related("yk_report_reader", "dk_report_reader", "budget_presenter")
        .first()
    )
    if tutanak is None:
        return None
    return {
        "yk_report_reader": _kisi(tutanak.yk_report_reader),
        "dk_report_reader": _kisi(tutanak.dk_report_reader),
        "budget_presenter": _kisi(tutanak.budget_presenter),
        "unaudited_documents_note": _metin(tutanak.unaudited_documents_note),
        "handed_to_new_yk_on": _gun(tutanak.handed_to_new_yk_on),
    }


def _duzeltmeler(kurul: GeneralAssembly) -> list[dict[str, Any]]:
    """Katılım düzeltmeleri (ekleme-yalnız): gerekçe metni ve düzelten hesap dönmez."""
    return [
        {
            "id": d.pk,
            "meeting": d.meeting,
            "field": d.field,
            "old_value": d.old_value,
            "new_value": d.new_value,
            "corrected_at": _an(d.corrected_at),
        }
        for d in genel_kurul.katilim_duzeltmeleri(kurul)
    ]


def _kurul_bilgileri(kurul: GeneralAssembly) -> list[str]:
    """Durumun bilgi satırları ([B]; tasarım §7.1): planlamada mevcut ve veli listesi önerisi, ilanda
    müdürün açılışı (md. 10/1-b), olağanüstüde gündeme bağlılık (md. 9/6)."""
    bilgiler: list[str] = []
    if kurul.status == AssemblyStatus.PLANLANDI:
        bilgiler += genel_kurul.planlama_bilgileri()
    if kurul.status in (AssemblyStatus.ILAN_EDILDI, AssemblyStatus.YETER_SAYI_YOK):
        bilgiler.append(genel_kurul.MUDUR_ACILIS_BILGISI)
    if kurul.kind == AssemblyKind.OLAGANUSTU and kurul.status != AssemblyStatus.IPTAL:
        bilgiler.append(genel_kurul.GUNDEME_BAGLILIK_BILGISI)
    return bilgiler


def _kurul_ayrintisi(kurul: GeneralAssembly) -> dict[str, Any]:
    """Genel kurulun ayrıntısı (sihirbazın bütün adımları): kayıt, gündem, ilanlar, divan, adaylar ve
    seçilenler, tutanak, katılım düzeltmeleri, katılım işaretlerinin sayıları (öneri; U33)."""
    kurul = GeneralAssembly.objects.get(pk=kurul.pk)
    uyelikler = selectors.membership_all().filter(assembly=kurul)
    return {
        **_kurul_ozeti(kurul),
        "call_reason": _metin(kurul.call_reason),
        "call_decision": kurul.call_decision_id,
        "call_document": kurul.call_document_id,
        "call_audit_report": kurul.call_audit_report_id,
        "cagri_sahibi": genel_kurul.cagri_sahibi(kurul),
        "member_application_count": kurul.member_application_count,
        "member_count_declared": kurul.member_count_declared,
        "announced_on": _gun(kurul.announced_on),
        "second_announced_on": _gun(kurul.second_announced_on),
        "student_count_snapshot": kurul.student_count_snapshot,
        "quorum_base": kurul.quorum_base,
        "quorum_multiplier": kurul.quorum_multiplier,
        "first_attendee_count": kurul.first_attendee_count,
        "second_attendee_count": kurul.second_attendee_count,
        "attendance_by_kind": kurul.attendance_by_kind,
        "parent_students_count": kurul.parent_students_count,
        "observer_count": kurul.observer_count,
        "discharge_yk": kurul.discharge_yk,
        "discharge_dk": kurul.discharge_dk,
        "discharge_yk_votes_for": kurul.discharge_yk_votes_for,
        "discharge_yk_votes_against": kurul.discharge_yk_votes_against,
        "discharge_yk_present_count": kurul.discharge_yk_present_count,
        "discharge_dk_votes_for": kurul.discharge_dk_votes_for,
        "discharge_dk_votes_against": kurul.discharge_dk_votes_against,
        "discharge_dk_present_count": kurul.discharge_dk_present_count,
        "cancel_reason": _metin(kurul.cancel_reason),
        "rule_warnings": list(kurul.rule_warnings or []),
        "gundem": [
            _gundem_maddesi(m) for m in AgendaItem.objects.filter(assembly=kurul).order_by("order")
        ],
        "ilanlar": [_duyuru(d) for d in genel_kurul.kurulun_duyurulari(kurul)],
        # Yalnız iptal edilmemiş divan (`kurulun_divani`): düzeltilen divanın kayıtları silinmez,
        # `IPTAL` olur; ekran divanın yeniden seçilmesini bu listeden anlar.
        "divan": OrganMembershipSerializer(genel_kurul.kurulun_divani(kurul), many=True).data,
        "adaylar": OrganMembershipSerializer(
            uyelikler.filter(
                organ__in=(OrganType.YONETIM_KURULU, OrganType.DENETLEME_KURULU)
            ).order_by("organ", "seat_type", "pk"),
            many=True,
        ).data,
        "tutanak": _tutanak(kurul),
        "katilim_duzeltmeleri": _duzeltmeler(kurul),
        "katilim_isareti_sayilari": {
            toplanti: genel_kurul.katilim_isareti_sayisi(kurul, toplanti)
            for toplanti in AssemblyMeeting.values
        },
        "bilgiler": _kurul_bilgileri(kurul),
        "oturum": _oturumun_eylemleri(kurul),
    }


def _oturumun_eylemleri(kurul: GeneralAssembly) -> dict[str, Any]:
    """Oturumdaki rolün bu kayıtta yazabildikleri (ekranın çağrı penceresi ve belge kartları; plan F2
    11b): çağıranlar ve uçları, üretebileceği belgeler. Ön yüz rol adıyla dallanmaz, bunu okur; kapı
    yine yazmanın kendisindedir. Kişisizdir, yazmaz."""
    return {
        "cagiranlar": genel_kurul.oturumun_cagiranlari(kurul),
        "uretilebilir_belgeler": [
            kod for kod in genel_kurul_evraki.KODLAR if genel_kurul_evraki.uretebilir_mi(kod, kurul)
        ],
    }


def _sonuc(sonuc: genel_kurul.GenelKurulSonucu, durum: int = status.HTTP_200_OK) -> Response:
    """Geçişin yanıtı: güncel ayrıntı, bu geçişin uyarıları ve bilgi satırları."""
    return Response(
        {
            "genel_kurul": _kurul_ayrintisi(sonuc.kurul),
            "uyarilar": _uyarilar(sonuc.uyarilar),
            "bilgiler": list(sonuc.bilgiler),
        },
        status=durum,
    )


def _madde_sonucu(sonuc: Any) -> Response:
    """Gündem ve seçim yazımlarının yanıtı (`GundemSonucu`, `SecimSonucu`)."""
    madde = AgendaItem.objects.get(pk=sonuc.madde.pk)
    return Response(
        {
            "madde": _gundem_maddesi(madde),
            "genel_kurul": _kurul_ayrintisi(madde.assembly),
            "uyarilar": _uyarilar(sonuc.uyarilar),
            "bilgiler": list(sonuc.bilgiler),
        }
    )


def _kurul_yaniti(kurul: GeneralAssembly) -> Response:
    return Response({"genel_kurul": _kurul_ayrintisi(kurul), "uyarilar": [], "bilgiler": []})


def _acik_donem() -> OabTerm | None:
    donem: OabTerm | None = (
        OabTerm.objects.select_related("rule_package").filter(status=TermStatus.ACIK).first()
    )
    return donem


# ---------------------------------------------------------------------------
# Genel kurul: liste, planlama, ayrıntı, toplantı bilgisi
# ---------------------------------------------------------------------------
class AssemblyListView(APIView):
    """Genel kurullar (en yeni üstte) ve planlama (`genel_kurul.planla`).

    Okuma kişisizdir; planlamanın bilgi satırları (öğrenci mevcudu ve tarihi, veli listesi önerisi) ve
    açık dönemin kural sürümünün genel kurul kurallarını taşıyıp taşımadığı (U1: taşımıyorsa sihirbaz
    kural sürümü güncellemesine götürür) yanındadır."""

    def get(self, request: Request) -> Response:
        acik = _acik_donem()
        guncellenmeli = False
        if acik is not None:
            try:
                guncellenmeli = not genel_kurul.kurallari_tasiyor_mu(acik, timezone.localdate())
            except KuralPaketiKullanilamaz:
                guncellenmeli = True
        return Response(
            {
                "kayitlar": [_kurul_ozeti(k) for k in _kurullar().order_by("-pk")],
                "acik_donem": None if acik is None else acik.pk,
                "kural_surumu_guncellenmeli": guncellenmeli,
                "planlama_bilgileri": list(genel_kurul.planlama_bilgileri()),
            }
        )

    def post(self, request: Request) -> Response:
        govde = PlanlaSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.planla(**veri, gerekce=gerekce)
        return _sonuc(sonuc, status.HTTP_201_CREATED)


class AssemblyDetailView(APIView):
    """Genel kurulun ayrıntısı; ilandan önce toplantı zamanı ve yeri (PATCH; çağrının sahibi müdürse
    müdür düzenler — `genel_kurul._duzenleme_kapisi`)."""

    def get(self, request: Request, pk: int) -> Response:
        return Response(_kurul_ayrintisi(_kurul(pk)))

    def patch(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = ToplantiBilgisiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.toplanti_bilgisini_degistir(
                kurul,
                first_meeting_at=veri["first_meeting_at"],
                venue=veri.get("venue"),
                gerekce=gerekce,
            )
        return _sonuc(sonuc)


# ---------------------------------------------------------------------------
# Çağrı (PLANLANDI → CAGRILDI): yönetim kurulu, başkan, üye başvurusu; müdür (¹); Denetleme Kurulu (⁵)
# ---------------------------------------------------------------------------
def _gundem(veri: dict[str, Any]) -> list[genel_kurul.GundemMaddesi]:
    return [genel_kurul.GundemMaddesi(title=m["title"], kind=m["kind"]) for m in veri.pop("gundem")]


class AssemblyCallView(APIView):
    """Çağrı: yönetim kurulu (sekreter; S1: karar bağı F3'e dek uyarı + gerekçe), başkanın md. 13/8
    çağrısı, üyelerin yazılı başvurusu (program yöneticisi; başvuran ve üye sayısı, gelen evrak bağı).
    Rol çağırana göre serviste daraltılır (`genel_kurul.CAGIRAN_ROLLERI`)."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = CagriSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        gundem = _gundem(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.cagir(kurul, **veri, gundem=gundem, gerekce=gerekce)
        return _sonuc(sonuc)


class AssemblyPrincipalCallView(APIView):
    """Müdürün yazısı (¹; sahiplikli): yeni açılan okulda genel kurul daveti (md. 9/1) ya da olağanüstü
    çağrı (md. 9/6, 13/8, 25/2). Yazı evrak defterine programca giden evrak olarak işlenir (⁷); defter
    kayıtlı değilse bilgi satırı döner."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = MudurCagrisiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        gundem = _gundem(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.cagir(kurul, **veri, gundem=gundem, gerekce=gerekce)
        return _sonuc(sonuc)


class AssemblyAuditBoardCallView(APIView):
    """Denetleme Kurulunun md. 14/5 çağrısı (⁵): çağrı yalnız md. 6 aykırılık işaretli denetim raporuyla
    açılır (S6 (ii), sert — hukuken geçersiz işlem; `irregularity_found` tek başına açmaz). Rapor kayıtlı
    olandan seçilir ya da aynı istekte, aynı işlemde yazılır (U13); çağrı reddedilirse rapor da yazılmaz."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = DkCagrisiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        gundem = _gundem(veri)
        rapor_bilgisi = veri.pop("rapor")
        with _hizmet_hatalari(), transaction.atomic():
            rapor = veri.pop("call_audit_report")
            if rapor_bilgisi is not None:
                rapor = denetim.denetim_raporu_yaz(**rapor_bilgisi)
            sonuc = genel_kurul.cagir(
                kurul,
                called_by="DENETLEME_KURULU",
                call_audit_report=rapor,
                gundem=gundem,
                gerekce=gerekce,
                **veri,
            )
        return _sonuc(sonuc)


class AssemblyCallDocumentView(APIView):
    """Çağrı yazısının evrak kaydı bağı: üyelerin başvurusunun gelen evrak kaydı ya da Denetleme Kurulunun
    yazısının kaydı (program yöneticisi; `genel_kurul.cagri_yazisini_bagla`)."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = CagriYazisiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            sonuc = genel_kurul.cagri_yazisini_bagla(kurul, kayit=govde.validated_data["kayit"])
        return _sonuc(sonuc)


# ---------------------------------------------------------------------------
# İlan ve davet
# ---------------------------------------------------------------------------
def _kanallar(veri: dict[str, Any] | None) -> genel_kurul.IlanKanallari | None:
    if veri is None:
        return None
    return genel_kurul.IlanKanallari(**veri)


class AssemblyAnnouncementView(APIView):
    """İlan (`CAGRILDI → ILAN_EDILDI`): yeter sayı dondurulur (U7), 15 gün ve üç kanal denetlenir;
    ikinci toplantının tarihi girildiyse 30 gün."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = IlanSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.ilan_et(
                kurul,
                kanallar=_kanallar(veri["kanallar"]),
                second_meeting_at=veri["second_meeting_at"],
                gerekce=gerekce,
            )
        return _sonuc(sonuc)


class AssemblySecondAnnouncementView(APIView):
    """İkinci toplantının ayrı ilanı (birinci toplantıda yeter sayı sağlanamadıktan sonra)."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = IkinciIlanSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.ikinci_toplanti_ilani(
                kurul,
                second_meeting_at=veri["second_meeting_at"],
                kanallar=_kanallar(veri["kanallar"]),
                gerekce=gerekce,
            )
        return _sonuc(sonuc)


def _duyuru_kaydi(pk: int) -> Announcement:
    duyuru: Announcement = get_object_or_404(Announcement.objects.all(), pk=pk)
    return duyuru


class AnnouncementEvidenceView(APIView):
    """İlanın kanal kanıt günlerinin sonradan girilmesi ya da düzeltilmesi (tutanak tamamlanana dek)."""

    def put(self, request: Request, pk: int) -> Response:
        duyuru = _duyuru_kaydi(pk)
        govde = KanitSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.ilan_kanitlarini_yaz(
                duyuru, kanallar=genel_kurul.IlanKanallari(**veri), gerekce=gerekce
            )
        return _sonuc(sonuc)


class AnnouncementAttachmentsView(APIView):
    """İlanın kanıt dosyası (ilan panosunun fotoğrafı, internet sayfasının görüntüsü, teslim kaydı;
    PDF, JPEG, PNG). Veli adı taşıyan çizelge eklenmez (R9)."""

    def post(self, request: Request, pk: int) -> Response:
        duyuru = _duyuru_kaydi(pk)
        govde = DosyaSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        dosya = govde.validated_data["file"]
        with _hizmet_hatalari(), _ek_yazma_hatalari():
            ek = genel_kurul.ilan_kanitina_ek_ekle(duyuru, dosya.read(), dosya_adi=dosya.name or "")
        return Response(_ek(ek), status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Toplantılar, iptal, katılım düzeltmesi ve işareti
# ---------------------------------------------------------------------------
def _katilim(veri: dict[str, Any]) -> genel_kurul.Katilim:
    return genel_kurul.Katilim(
        attendee_count=veri["attendee_count"],
        attendance_by_kind=veri["attendance_by_kind"],
        parent_students_count=veri["parent_students_count"],
        observer_count=veri["observer_count"],
    )


class AssemblyFirstMeetingView(APIView):
    """Birinci toplantı: yapıldı ya da yeter sayı yok programca hesaplanır (md. 9/2); açılışı okul
    müdürü yapar (md. 10/1-b; bilgi satırı)."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = KatilimSayilariSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.birinci_toplanti(kurul, katilim=_katilim(veri), gerekce=gerekce)
        return _sonuc(sonuc)


class AssemblySecondMeetingView(APIView):
    """İkinci toplantı (çoğunluk aranmaz, md. 9/2; olağanüstüde de, A-1)."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = KatilimSayilariSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.ikinci_toplanti(kurul, katilim=_katilim(veri), gerekce=gerekce)
        return _sonuc(sonuc)


class AssemblyCancelView(APIView):
    """İptal (gerekçe zorunlu, şifreli; olağanda hazırlık dönemi de iptal olur; program yöneticisi)."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = IptalSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            kurul = genel_kurul.iptal_et(kurul, cancel_reason=govde.validated_data["cancel_reason"])
        return _kurul_yaniti(kurul)


class AssemblyAttendanceCorrectionsView(APIView):
    """Katılım düzeltmesi (ekleme-yalnız; dondurulmuş yeter sayı düzeltilemez — sert)."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = KatilimDuzeltmeSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.katilim_duzelt(kurul, **veri, gerekce=gerekce)
        return _sonuc(sonuc, status.HTTP_201_CREATED)


class AssemblyAttendanceMarksView(APIView):
    """Katılım işaretleri penceresi (U33; R9, ¹⁰): yalnız program yöneticisi. Okuma veli adlarını sınıf
    başına verir ve erişim günlüğüne yazılır; yanıt önbelleğe alınmaz. Yazma işaret sayısını (öneri)
    döner, ad dönmez."""

    permission_classes = [RequiresAdminPassword]

    def get(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        sorgu = ToplantiSorgusuSerializer(data=request.query_params)
        sorgu.is_valid(raise_exception=True)
        with _hizmet_hatalari(), transaction.atomic():
            liste = genel_kurul.katilim_isaretleri(kurul, toplanti=sorgu.validated_data["toplanti"])
        yanit = Response({"toplanti": sorgu.validated_data["toplanti"], "siniflar": liste})
        yanit["Cache-Control"] = "no-store"
        return yanit

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = KatilimIsaretiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            sayi = genel_kurul.katilim_isaretle(kurul, **dict(govde.validated_data))
        return Response({"toplanti": govde.validated_data["toplanti"], "isaret_sayisi": sayi})


# ---------------------------------------------------------------------------
# Gündem, karar, seçim, ibra, dosya ekleri
# ---------------------------------------------------------------------------
class AssemblyAgendaView(APIView):
    """Toplantıda gündeme oylamayla madde (md. 9/4); olağanüstüde gündeme bağlılık uyarısı (B-13)."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = GundemEkleSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.gundeme_madde_ekle(kurul, **veri, gerekce=gerekce)
        return _madde_sonucu(sonuc)


class AssemblyAgendaOrderView(APIView):
    """Gündemin sırası (ilandan önce ya da toplantıda; çağrının sahibi müdürse ilandan önce müdür)."""

    def put(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = GundemSirasiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            sonuc = genel_kurul.gundem_sirasini_degistir(kurul, sira=govde.validated_data["sira"])
        return _sonuc(sonuc)


class AgendaItemRemovalView(APIView):
    """Gündemden oylamayla çıkarma (md. 9/4; madde silinmez)."""

    def post(self, request: Request, pk: int) -> Response:
        madde = _madde(pk)
        govde = GundemCikarSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.gundemden_madde_cikar(madde, **veri, gerekce=gerekce)
        return _madde_sonucu(sonuc)


class AgendaItemResultView(APIView):
    """Gündem maddesinin sonucu: oylanan maddede sonuç oylardan hesaplanır (S2, S6 (iii) sert)."""

    def post(self, request: Request, pk: int) -> Response:
        madde = _madde(pk)
        govde = KararSonucuSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            sonuc = genel_kurul.karar_sonucu_yaz(madde, **dict(govde.validated_data))
        return _madde_sonucu(sonuc)


class AgendaItemElectionView(APIView):
    """Seçim maddesinin sonucu (U26, U27): seçilen aynı genel kurulun aday kaydıdır (S6 (i), sert)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        madde = _madde(pk)
        govde = SecimSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        adaylar = [genel_kurul.AdayOyu(**dict(a)) for a in veri.pop("adaylar")]
        with _hizmet_hatalari():
            sonuc = genel_kurul.secim_sonucu_yaz(madde, adaylar=adaylar, **veri, gerekce=gerekce)
        return _madde_sonucu(sonuc)


class AgendaItemElectionFormView(APIView):
    """Seçimin biçimi (liste hâlinde, açık oy; `genel_kurul.secim_bicimi`)."""

    def put(self, request: Request, pk: int) -> Response:
        madde = _madde(pk)
        govde = SecimBicimiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.secim_bicimini_yaz(madde, **veri, gerekce=gerekce)
        return _madde_sonucu(sonuc)


class AgendaItemElectionCancelView(APIView):
    """Yanlış girilen seçim sonucunun iptali (gerekçe zorunlu; sonra yeniden girilir)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        madde = _madde(pk)
        govde = IptalSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            genel_kurul.secimi_iptal_et(madde, cancel_reason=govde.validated_data["cancel_reason"])
        return _kurul_yaniti(GeneralAssembly.objects.get(pk=madde.assembly_id))


class AgendaItemDischargeView(APIView):
    """İbra (md. 11/1-c, ç): yönetim kurulu ve Denetleme Kurulu ayrı oylanır; sonuç oylardan."""

    def post(self, request: Request, pk: int) -> Response:
        madde = _madde(pk)
        govde = IbraSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        oylamalar = {
            kurul: None if veri[kurul] is None else genel_kurul.IbraOylamasi(**dict(veri[kurul]))
            for kurul in ("yk", "dk")
        }
        with _hizmet_hatalari():
            sonuc = genel_kurul.ibra_yaz(
                madde,
                yk=oylamalar["yk"],
                dk=oylamalar["dk"],
                discharge_yk=veri["discharge_yk"],
                discharge_dk=veri["discharge_dk"],
                unaudited_documents_note=veri["unaudited_documents_note"],
            )
        return _sonuc(sonuc)


class _DosyaEkiView(APIView):
    """Genel kurulun dosya eki (U23): gündem maddesinin eki (PDF, JPEG, PNG)."""

    def post(self, request: Request, pk: int) -> Response:
        madde = _madde(pk)
        govde = DosyaSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        dosya = govde.validated_data["file"]
        self.madde_denetimi(madde)
        with _hizmet_hatalari(), _ek_yazma_hatalari():
            ek = genel_kurul.dosya_eki_ekle(madde, dosya.read(), dosya_adi=dosya.name or "")
        return Response(_ek(ek), status=status.HTTP_201_CREATED)

    def madde_denetimi(self, madde: AgendaItem) -> None:
        raise NotImplementedError


class AgendaItemAttachmentsView(_DosyaEkiView):
    """Yönetim kurulu faaliyet raporu ve kesin hesap (E34) ve tahmini bütçe (E28): yönetim kurulu rolleri
    ve program yöneticisi. Denetleme Kurulunun raporu bu uçtan eklenmez (kendi ucu, ⁵)."""

    def madde_denetimi(self, madde: AgendaItem) -> None:
        if madde.kind == genel_kurul.DK_DOSYA_EKI_MADDESI:
            raise RolYetkisiz


class AgendaItemAuditBoardAttachmentView(_DosyaEkiView):
    """Denetleme Kurulunun nihai raporu (E33; md. 14/4): yalnız Denetleme Kurulu (⁵)."""

    def madde_denetimi(self, madde: AgendaItem) -> None:
        if madde.kind != genel_kurul.DK_DOSYA_EKI_MADDESI:
            raise RolYetkisiz


# ---------------------------------------------------------------------------
# Divan, adaylar, tutanak, dönem geçişi
# ---------------------------------------------------------------------------
class AssemblyPresidingBoardView(APIView):
    """Divan başkanı ve kâtip (md. 10/1-c; U25); kişi türü uyarı + gerekçe."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = DivanSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul.divan_sec(kurul, **veri, gerekce=gerekce)
        return _sonuc(sonuc, status.HTTP_201_CREATED)


class AssemblyPresidingBoardCancelView(APIView):
    """Yanlış girilen divanın iptali (iki kayıt birlikte; gerekçe zorunlu)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = IptalSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            genel_kurul.divani_iptal_et(kurul, cancel_reason=govde.validated_data["cancel_reason"])
        return _kurul_yaniti(kurul)


class AssemblyCandidatesView(APIView):
    """Aday kaydı (U26; planlamadan toplantının sonuna dek, salondan adaylık dahil)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = AdaySerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            uyelik = genel_kurul.aday_kaydet(kurul, **veri, gerekce=gerekce)
        return Response(
            OrganMembershipSerializer(selectors.membership_all().get(pk=uyelik.pk)).data,
            status=status.HTTP_201_CREATED,
        )


class AssemblyMinutesView(APIView):
    """Tutanağın kişi bağları ve teslim günü (kısmi yazım; md. 10/1-ç teslim günü, U29)."""

    permission_classes = [RequiresAdminPassword]

    def patch(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = TutanakBilgisiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        alanlar = {
            ad: govde.validated_data[ad] for ad in TUTANAK_ALANLARI if ad in govde.validated_data
        }
        with _hizmet_hatalari():
            genel_kurul.tutanak_bilgilerini_yaz(kurul, **alanlar)
        return _kurul_yaniti(kurul)


class AssemblyMinutesCompleteView(APIView):
    """Tutanağın tamamlanması (`YAPILDI → TUTANAK_TAMAM`; açık eksikler gerekçeyle sapmaya döner, O3).
    Dönem kendiliğinden açılmaz: geçişi program yöneticisi onaylar (U32)."""

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = GerekceMixin(data=request.data)
        govde.is_valid(raise_exception=True)
        gerekce = _gerekce(dict(govde.validated_data))
        with _hizmet_hatalari():
            sonuc = genel_kurul.tutanagi_tamamla(kurul, gerekce=gerekce)
        return _sonuc(sonuc)


def _donem_gecisi(gecis: genel_kurul.DonemGecisi) -> dict[str, Any]:
    return {
        "genel_kurul": gecis.kurul.pk,
        "yeni_donem": OabTermSerializer(OabTerm.objects.get(pk=gecis.yeni_donem.pk)).data,
        "baslangic": gecis.baslangic.isoformat(),
        "kapanacak": None
        if gecis.kapanacak is None
        else OabTermSerializer(OabTerm.objects.get(pk=gecis.kapanacak.pk)).data,
        "kapanacak_bitis": _gun(gecis.kapanacak_bitis),
        "engeller": list(gecis.engeller),
    }


class AssemblyTermTransitionView(APIView):
    """Dönem geçişinin önizlemesi (yazmaz, kişisiz) ve onayı (U32; yalnız program yöneticisi, M1):
    hazırlık dönemi `ACIK`, kapanacak dönem `KAPANISTA`; aralık çakışması sert (hesap bütünlüğü)."""

    permission_classes = [RequiresAdminPassword]

    def get(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        with _hizmet_hatalari():
            gecis = genel_kurul.donem_gecisi_onizlemesi(kurul)
        return Response(_donem_gecisi(gecis))

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        with _hizmet_hatalari():
            gecis = genel_kurul.donem_gecisini_onayla(kurul)
        return Response(_donem_gecisi(gecis))


# ---------------------------------------------------------------------------
# Genel kurul evrakı (E05-E13, E64; E04 üretilmez): katalog, liste, üretim, adlı çıktı
# ---------------------------------------------------------------------------
_BELGE_ADLARI = genel_kurul_evraki.BELGE_ADLARI


def evrak_satiri(kayit: GeneratedDocument) -> dict[str, Any]:
    """Genel kurul evrakının kaydı: veli adlı kayıtta yalnız tür, tarih ve satır sayısı (dosyası yok)."""
    return {
        "id": kayit.pk,
        "kod": kayit.doc_type,
        "ad": _BELGE_ADLARI.get(str(kayit.doc_type), str(kayit.doc_type)),
        "kip": kayit.variant,
        "toplanti": kayit.meeting,
        "surum": kayit.version,
        "durum": kayit.status,
        "uretim_zamani": _an(kayit.generated_at),
        "bicimler": [] if kayit.personal_list else kayit.formats,
        "kisi_listesi": kayit.personal_list,
        "satir_sayisi": kayit.row_count if kayit.personal_list else None,
    }


class AssemblyDocumentCatalogView(APIView):
    """Genel kurul evrakının kataloğu ve E12'nin muhatap önerileri (il ve ilçe millî eğitim müdürlüğü;
    varsayılan ilçe). E04 katalogda durur, üretilmez (nedeni yanında)."""

    def get(self, request: Request) -> Response:
        return Response(
            {
                "belgeler": genel_kurul_evraki.katalog(),
                "muhatap_onerileri": genel_kurul_evraki.muhatap_onerileri(),
                "varsayilan_muhatap": genel_kurul_evraki.VARSAYILAN_MUHATAP,
            }
        )


class AssemblyDocumentListView(APIView):
    """Genel kurulun geçerli evrakı (kod, kip ve toplantı başına; veli adlı kayıtlar dosyasız)."""

    def get(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        return Response([evrak_satiri(k) for k in genel_kurul_evraki.evrak_listesi(kurul)])


def _muhatap(veri: dict[str, Any]) -> genel_kurul_evraki.Muhatap | None:
    """E12'nin muhatabı: basımda düzenlenen (`muhatap_idare` verildiyse) ya da seçilen il/ilçe millî
    eğitim müdürlüğünün önerisi; ikisi de yoksa servisin varsayılanı (ilçe)."""
    if veri["muhatap_idare"] is not None:
        return genel_kurul_evraki.Muhatap(idare=veri["muhatap_idare"], birim=veri["muhatap_birim"])
    if veri["muhatap_secimi"]:
        return genel_kurul_evraki.muhatap_sec(veri["muhatap_secimi"])
    return None


def _uretim_yaniti(uretim: genel_kurul_evraki.Uretim) -> Response:
    return Response(
        {"evrak": evrak_satiri(uretim.kayit), "uyarilar": list(uretim.uyarilar)},
        status=status.HTTP_201_CREATED,
    )


class AssemblyDocumentView(APIView):
    """Genel kurul belgesinin üretimi (yeni sürüm, PDF ve Word saklanır). Üreten rol belgeye göre
    serviste daraltılır (tasarım §9.6 "Üreten"; E05 çağırana göre). E04 ve konusu genel kurul olmayan
    kod bu yoldan üretilmez (400)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int, kod: str) -> Response:
        kurul = _kurul(pk)
        govde = EvrakUretimSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        with _hizmet_hatalari(), _evrak_yazma_hatalari():
            if kod.upper() not in genel_kurul_evraki.GENEL_KURUL_KODLARI:
                raise ValueError(genel_kurul_evraki.KOD_GECERSIZ)
            muhatap = _muhatap(veri)
            uretim = genel_kurul_evraki.uret(
                kod.upper(), kurul, kip=veri["kip"], toplanti=veri["toplanti"], muhatap=muhatap
            )
        return _uretim_yaniti(uretim)


class AssemblyE05AuditBoardView(APIView):
    """Denetleme Kurulunun çağrı yazısı (E05, md. 14/5 kolu; ⁵): yalnız Denetleme Kurulu, çağrının
    sahiplikli eylemiyle (`genel_kurul_evraki._e05_yetkisi`)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        kurul = _kurul(pk)
        govde = EvrakUretimSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari(), _evrak_yazma_hatalari():
            uretim = genel_kurul_evraki.uret(
                genel_kurul_evraki.E05, kurul, toplanti=govde.validated_data["toplanti"]
            )
        return _uretim_yaniti(uretim)


#: Veli adlı çıktının yoldaki biçimi → kaydın biçimi.
_ADLI_BICIMLER = {
    "pdf": DocumentFormat.PDF,
    "docx": DocumentFormat.DOCX,
    "xlsx": DocumentFormat.XLSX,
}


class AssemblyNamedDocumentView(APIView):
    """Veli adlı E07 (sınıf teslim çizelgesi) ve E08 (katılım cetveli): tek istekte üretilir ve verilir
    (U15; R9, ¹⁰ — yalnız program yöneticisi). Dosya saklanmaz; evrak kaydı (dosyasız), basım izi ve
    erişim günlüğü satırı aynı işlemde yazılır; yanıt önbelleğe alınmaz (`no-store`)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int, kod: str) -> Any:
        kurul = _kurul(pk)
        govde = AdliEvrakSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            cikti = genel_kurul_evraki.adli_uret_ve_ver(
                kod.upper(),
                kurul,
                bicim=_ADLI_BICIMLER[govde.validated_data["bicim"]],
                toplanti=govde.validated_data["toplanti"],
            )
        return genel_kurul_evraki.indirme_yaniti(
            cikti.icerik, dosya_adi=cikti.dosya_adi, mime=cikti.mime
        )


class E14DocumentView(APIView):
    """Yıllık iş takviminin basımı (E14; konusu birlik dönemi; program yöneticisi). Hazırlıktaki
    dönemin takvimi yazılmaz (409 `donem_yazilamaz`)."""

    def post(self, request: Request, pk: int) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        with _hizmet_hatalari(), _evrak_yazma_hatalari():
            uretim = genel_kurul_evraki.uret(genel_kurul_evraki.E14, donem)
        return _uretim_yaniti(uretim)


class TermAnnualCalendarView(APIView):
    """Yıllık iş takviminin verisi (Genel Bakış → Yıllık İş Takvimi; M9: her rol okur): E14'ün süre
    kuralı satırları (kural kimliği ve atıfla) ve okul planı satırları. Kişisiz, yazmaz. Kural paketi
    yüklenemezse okuma açık kalır: satırlar boş gelir (D1; `views._kadro_uyarilari` emsali)."""

    def get(self, request: Request, pk: int) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        try:
            return Response(genel_kurul_evraki.yillik_is_takvimi(donem))
        except KuralPaketiKullanilamaz:
            return Response(
                {
                    "donem": donem.pk,
                    "bolumler": list(genel_kurul_evraki.E14_BOLUMLER),
                    "kural_satirlari": [],
                    "plan_satirlari": [],
                    "uyarilar": [],
                }
            )


# ---------------------------------------------------------------------------
# Gelen-giden evrak (M10; ⁷): defter, kayıt, ek; E12'nin kaydı
# ---------------------------------------------------------------------------
def _defter(defter: OfficialBook) -> dict[str, Any]:
    bugun = timezone.localdate()
    return {
        "id": defter.pk,
        "status": defter.status,
        "certified_by": defter.certified_by,
        "certified_on": _gun(defter.certified_on),
        "certification_no": defter.certification_no,
        "page_count": defter.page_count,
        "opened_on": _gun(defter.opened_on),
        "last_no_before_program": defter.last_no_before_program,
        "siradaki_no": gelen_giden_evrak.beklenen_kayit_no(defter, bugun.year),
    }


def _evrak_kaydi(kayit: DocumentRecord) -> dict[str, Any]:
    return {
        "id": kayit.pk,
        "book": kayit.book_id,
        "direction": kayit.direction,
        "year": kayit.year,
        "record_no": kayit.record_no,
        "date": _gun(kayit.date),
        "counterparty": _metin(kayit.counterparty),
        "subject": _metin(kayit.subject),
        "external_ref": kayit.external_ref,
        "generated_document": kayit.generated_document_id,
        "term": kayit.term_id,
        "ekler": _ekler(kayit),
    }


def _evrak_kaydi_yaniti(sonuc: gelen_giden_evrak.EvrakKaydiSonucu) -> Response:
    kayit = DocumentRecord.objects.get(pk=sonuc.kayit.pk)
    return Response(
        {"kayit": _evrak_kaydi(kayit), "uyarilar": _uyarilar(sonuc.uyarilar)},
        status=status.HTTP_201_CREATED,
    )


class DocumentBookListView(APIView):
    """Gelen-giden evrak defterleri (defter seçimi; kullanımdaki en yenisi varsayılandır) ve kaydı."""

    def get(self, request: Request) -> Response:
        defterler = OfficialBook.objects.filter(kind=BookKind.GELEN_GIDEN_EVRAK_DEFTERI).order_by(
            "-pk"
        )
        varsayilan = gelen_giden_evrak.evrak_defteri()
        return Response(
            {
                "defterler": [_defter(d) for d in defterler],
                "varsayilan": None if varsayilan is None else varsayilan.pk,
            }
        )

    def post(self, request: Request) -> Response:
        govde = EvrakDefteriSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            defter = gelen_giden_evrak.evrak_defteri_olustur(**dict(govde.validated_data))
        return Response(_defter(defter), status=status.HTTP_201_CREATED)


class DocumentRecordListView(APIView):
    """Gelen ve giden kayıtlar (`?book=&year=&direction=`; defter ve yıl sırasıyla) ve elle kayıt
    (numara tekilliği sert, sıra atlama uyarı + gerekçe). Müdürün yazısı ve E12 kendi yollarındadır."""

    def get(self, request: Request) -> Response:
        params = request.query_params
        kayitlar = DocumentRecord.objects.all()
        for anahtar, alan, ileti in (
            ("book", "book_id", DEFTER_GECERSIZ),
            ("year", "year", YIL_GECERSIZ),
        ):
            ham = params.get(anahtar, "").strip()
            if ham:
                # `str.isdigit` tek başına yetmez: "²" gibi rakamlar onu doğru yapar, `int` çeviremez
                # (`denetim_izi.acik_ref_coz` kalıbı).
                if not (ham.isascii() and ham.isdigit()):
                    raise serializers.ValidationError({anahtar: [ileti]})
                kayitlar = kayitlar.filter(**{alan: int(ham)})
        yon = params.get("direction", "").strip()
        if yon:
            if yon not in DocumentDirection.values:
                raise serializers.ValidationError({"direction": [gelen_giden_evrak.YON_GECERSIZ]})
            kayitlar = kayitlar.filter(direction=yon)
        return Response([_evrak_kaydi(k) for k in kayitlar.order_by("book", "-year", "-record_no")])

    def post(self, request: Request) -> Response:
        govde = EvrakKaydiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = gelen_giden_evrak.evrak_kaydet(**veri, gerekce=gerekce)
        return _evrak_kaydi_yaniti(sonuc)


class DocumentRecordAttachmentsView(APIView):
    """Evrak kaydının eki (taranmış evrak; PDF, JPEG, PNG)."""

    def post(self, request: Request, pk: int) -> Response:
        kayit = get_object_or_404(DocumentRecord.objects.all(), pk=pk)
        govde = DosyaSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        dosya = govde.validated_data["file"]
        with _hizmet_hatalari(), _ek_yazma_hatalari():
            ek = gelen_giden_evrak.evrak_kaydina_ek_ekle(
                kayit, dosya.read(), dosya_adi=dosya.name or ""
            )
        return Response(_ek(ek), status=status.HTTP_201_CREATED)


class DocumentOutgoingRecordView(APIView):
    """Programın ürettiği giden yazının (E12) evrak kaydı: GET öneri (yazmaz), POST kullanıcının onayıyla
    kayıt (plan F2 §7 U20; E12 kendiliğinden kaydedilmez). Bir yazı bir kez kaydedilir."""

    def get(self, request: Request, pk: int) -> Response:
        kayit = get_object_or_404(GeneratedDocument.objects.all(), pk=pk)
        with _hizmet_hatalari():
            return Response(genel_kurul_evraki.giden_kayit_onerisi(kayit))

    def post(self, request: Request, pk: int) -> Response:
        kayit = get_object_or_404(GeneratedDocument.objects.all(), pk=pk)
        govde = GidenKayitSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = genel_kurul_evraki.giden_kaydet(kayit, **veri, gerekce=gerekce)
        return _evrak_kaydi_yaniti(sonuc)


# ---------------------------------------------------------------------------
# Kullanıcı eklerinin indirilmesi
# ---------------------------------------------------------------------------
def _ek_indirme_adi(ek: Attachment) -> str:
    """İndirilen ekin dosya adı: sahibin belgesi ya da türü + kapsam + yükleme günü (sözlük §3):
    'Genel-Kurul-Eki-Tahmini-Bütçe_05.10.2026.pdf', 'İlan-Kanıtı_05.10.2026.jpg',
    'Gelen-Giden-Evrak-Eki-2026-14_05.10.2026.pdf'. Özgün ad kullanılmaz (kişi adı taşıyabilir)."""
    sahip = str(ek.owner_type)
    kok = _ILAN_KANITI_KOKU
    if sahip == denetim_izi.model_etiketi(AgendaItem):
        tur = AgendaItem.objects.filter(pk=int(ek.owner_id)).values_list("kind", flat=True).first()
        kok = _EK_DOSYA_ADI_KOKLERI.get(str(tur), _GENEL_KURUL_EKI_KOKU)
    elif sahip == denetim_izi.model_etiketi(DocumentRecord):
        kayit = (
            DocumentRecord.objects.filter(pk=int(ek.owner_id)).values("year", "record_no").first()
        )
        kok = (
            _EVRAK_EKI_KOKU
            if kayit is None
            else f"{_EVRAK_EKI_KOKU}-{kayit['year']}-{kayit['record_no']}"
        )
    ad = f"{kok}_{timezone.localtime(ek.uploaded_at):%d.%m.%Y}"
    uzanti = _EK_UZANTILARI.get(str(ek.mime))
    return f"{ad}.{uzanti}" if uzanti else ad


class AttachmentDownloadView(APIView):
    """Genel kurulun dosya eki, ilanın kanıtı ya da evrak kaydının eki: sahibin satırını okuyan rol
    indirir. Başka sahibin eki (üretilen evrak dahil; o basım yolundadır) 404. HEAD dosya vermez (405)."""

    def get(self, request: Request, pk: int) -> Any:
        ek = get_object_or_404(Attachment.objects.filter(purged_at__isnull=True), pk=pk)
        satir = _EK_SAHIPLERI.get(str(ek.owner_type))
        if satir is None:
            raise Http404
        kim = yazar()
        if kim is None or kim.sistem_mi or kim.rol not in rol_izinleri.okuyabilen_roller(satir):
            raise RolYetkisiz
        try:
            return dosya_deposu.indirme_yaniti(ek, dosya_adi=_ek_indirme_adi(ek))
        except (dosya_deposu.DosyaDeposuHatasi, dosya_sifreleme.DosyaSifrelemeHatasi) as exc:
            raise EvrakDosyasiAcilamadi(str(exc)) from exc

    def head(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.http_method_not_allowed(request, *args, **kwargs)


__all__ = [
    "AgendaItemAttachmentsView",
    "AgendaItemAuditBoardAttachmentView",
    "AgendaItemDischargeView",
    "AgendaItemElectionCancelView",
    "AgendaItemElectionFormView",
    "AgendaItemElectionView",
    "AgendaItemRemovalView",
    "AgendaItemResultView",
    "AnnouncementAttachmentsView",
    "AnnouncementEvidenceView",
    "AssemblyAgendaOrderView",
    "AssemblyAgendaView",
    "AssemblyAttendanceCorrectionsView",
    "AssemblyAttendanceMarksView",
    "AssemblyAuditBoardCallView",
    "AssemblyCallDocumentView",
    "AssemblyCallView",
    "AssemblyCancelView",
    "AssemblyCandidatesView",
    "AssemblyDetailView",
    "AssemblyDocumentCatalogView",
    "AssemblyDocumentListView",
    "AssemblyDocumentView",
    "AssemblyE05AuditBoardView",
    "AssemblyFirstMeetingView",
    "AssemblyListView",
    "AssemblyMinutesCompleteView",
    "AssemblyMinutesView",
    "AssemblyNamedDocumentView",
    "AssemblyPresidingBoardCancelView",
    "AssemblyPresidingBoardView",
    "AssemblyPrincipalCallView",
    "AssemblySecondAnnouncementView",
    "AssemblySecondMeetingView",
    "AssemblyTermTransitionView",
    "AttachmentDownloadView",
    "DocumentBookListView",
    "DocumentOutgoingRecordView",
    "DocumentRecordAttachmentsView",
    "DocumentRecordListView",
    "E14DocumentView",
    "TermAnnualCalendarView",
    "evrak_satiri",
]
