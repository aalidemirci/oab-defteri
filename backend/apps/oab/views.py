"""`oab` görünümleri."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.oab import models as oab_modelleri
from apps.oab import selectors
from apps.oab.hatalar import EvrakDosyasiAcilamadi, EvrakDosyasiYazilamadi
from apps.oab.kurallar import (
    BilinmeyenKural,
    KuralPaketiKullanilamaz,
    YururlukteDegerYok,
    atifli_metin,
    bilgi_notu,
    kural_kaydi,
)
from apps.oab.kurallar.erisim import atif_metni
from apps.oab.models import (
    BoardDecision,
    BookKind,
    BookStatus,
    ComplianceItem,
    MembershipRole,
    OfficialBook,
    OrganMembership,
    OrganType,
    SeatType,
    TermStatus,
)
from apps.oab.serializers import (
    AlimKomisyonuCreateSerializer,
    BaglanabilirKararSerializer,
    DevralinanSerializer,
    DkGorevBolumuSerializer,
    DkYedekCagrisiSerializer,
    DusmeSerializer,
    EngelSerializer,
    IptalSerializer,
    KararDefteriGecisSerializer,
    KararDefteriSerializer,
    OabPersonCreateSerializer,
    OabPersonFromParentSerializer,
    OabPersonFromPersonnelSerializer,
    OabPersonSerializer,
    OabPersonUpdateSerializer,
    OabTermAcilisSerializer,
    OabTermSerializer,
    OrganMembershipCreateSerializer,
    OrganMembershipSerializer,
    OrganMembershipUpdateSerializer,
    SayacBeyaniSerializer,
    TemsilciCreateSerializer,
    ToplantiGunuSerializer,
    YarimMetinSerializer,
    YkGorevBolumuSerializer,
    YkYedekCagrisiSerializer,
)
from apps.oab.services import (
    donemler,
    gecis,
    gorev_bolumu,
    gorev_evraki,
    kisiler,
    kurullar,
    temsilciler,
    uyelik_gecisleri,
    uyelikler,
    uyum,
    yarim_metin,
)
from apps.okul import denetim_izi
from apps.okul.models import CanteenMode
from apps.okul.oturum import yazar
from apps.okul.permissions import RequiresAdminPassword
from apps.okul.services import dosya_deposu
from shared import dosya_sifreleme

#: Boolean sorgu parametresinin "açık" değerleri (`okul` uçlarıyla aynı).
TRUE_VALUES = frozenset({"true", "1"})

KANTIN_VERGI_KURALI = "kantin.isletmede_vergi_uyarisi"


def _kantin_isletme_bilgisi() -> dict[str, Any] | None:
    """Hangi kantin biçiminde hangi md. 23/3 bilgisinin görüneceği.

    Seçim form kaydedilmeden değişebildiği için bütün biçimler için sorulur; koşulu değerlendiren
    ön yüz değil pakettir. Paket yüklenemediyse okuma açık kalır: bilgi çıkmaz, ekran çalışır.
    """
    try:
        notlar = {
            mod: bilgi_notu(KANTIN_VERGI_KURALI, okul={"okul.kantin": mod})
            for mod in CanteenMode.values
        }
    except KuralPaketiKullanilamaz:
        return None
    gecerli = {mod: not_ for mod, not_ in notlar.items() if not_ is not None}
    if not gecerli:
        return None
    ilk = next(iter(gecerli.values()))
    return {
        "modlar": list(gecerli),
        "metin": atifli_metin(ilk),
        "paket": ilk["paket"],
        "rev": ilk["rev"],
    }


class OkulKartiBilgileriView(APIView):
    """Okul kartında kural paketinden gelen bilgiler (`okul` uygulaması `oab`'yi içe aktarmaz)."""

    def get(self, request: Request) -> Response:
        return Response({"kantin_isletme_bilgisi": _kantin_isletme_bilgisi()})


@contextmanager
def _hizmet_hatalari() -> Iterator[None]:
    """Servis `ValueError`'larını sözleşmeli 400'e çevirir (Türkçe ileti korunur)."""
    try:
        yield
    except ValueError as exc:
        raise serializers.ValidationError(str(exc)) from exc


def _donemler() -> Any:
    return oab_modelleri.OabTerm.objects.select_related("rule_package")


class TermListCreateView(APIView):
    """Birlik dönemleri: liste ve ilk dönemin açılışı (M1; tasarım §4.4.2, §7.9 adım 1: geçiş
    kurulumu, `gecis.ilk_donemi_ac`; programa başlama günü verilmezse bugündür)."""

    def get(self, request: Request) -> Response:
        return Response(OabTermSerializer(_donemler(), many=True).data)

    def post(self, request: Request) -> Response:
        govde = OabTermAcilisSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            acilis = gecis.ilk_donemi_ac(**dict(govde.validated_data))
        # Görev süresi uyarısı (md. 12/2, 14/2) kaydedilmez, gerekçe istemez: açılış yanıtında döner.
        return Response(
            {
                **OabTermSerializer(acilis.donem).data,
                "uyarilar": [_kadro_satiri(sonuc) for sonuc in acilis.uyarilar],
            },
            status=status.HTTP_201_CREATED,
        )


class TermDetailView(APIView):
    """Birlik döneminin ayrıntısı; kural sürümü salt okunur satırıyla."""

    def get(self, request: Request, pk: int) -> Response:
        return Response(OabTermSerializer(get_object_or_404(_donemler(), pk=pk)).data)


class TermMeetingDayView(APIView):
    """Yönetim kurulunun aylık toplantı günü kuralı (dönem ayarı; E01'in D bölümünün ilk satırı).

    Serbest metindir, program kural koymaz (md. 13/3 yalnız "ayda bir toplanır" der; günü kurul
    belirler). Rolü uç kuralı daraltır: E01'i üretenler (program yöneticisi ve sekreter).
    """

    def put(self, request: Request, pk: int) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        govde = ToplantiGunuSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            donem = donemler.toplanti_gunu_yaz(donem, govde.validated_data["yk_meeting_day_rule"])
        return Response(OabTermSerializer(donem).data)


class TermLinkableDecisionsView(APIView):
    """Dönemin bağlanabilecek yönetim kurulu kararları: kabul edilmiş ya da deftere işlenmiş (tasarım
    §7.2 "Notlar"; temsilcinin ve yedek çağrısının karar bağı). Kişisizdir; karar metni dönmez. F1c'de
    kararlar taslaktır (kabul ve deftere işleme F3), liste o zamana dek boş gelir."""

    def get(self, request: Request, pk: int) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        kararlar = (
            BoardDecision.objects.filter(
                meeting__term=donem,
                meeting__organ=OrganType.YONETIM_KURULU,
                status__in=temsilciler.BAGLANABILIR_KARAR_DURUMLARI,
            )
            .select_related("meeting")
            .order_by("decision_no", "pk")
        )
        return Response(BaglanabilirKararSerializer(kararlar, many=True).data)


class TermCancelView(APIView):
    """Yanlış girilmiş geçiş döneminin iptali (`ACIK` → `IPTAL`; gerekçe şifreli; §7.9 "Senaryolar").

    "Geçiş kurulumu tamamlandı" işaretinden sonra 409 `gecis_kapali`; yalnız program yöneticisi (M1).
    """

    def post(self, request: Request, pk: int) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        govde = IptalSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            donem = gecis.donemi_iptal_et(
                donem, cancel_reason=govde.validated_data["cancel_reason"]
            )
        return Response(OabTermSerializer(donem).data)


# ---------------------------------------------------------------------------
# Birlik kişileri (M2; tasarım §5.2.2; plan F1c-4). Kişi yazan uçlar ilk hesap kapısını taşır
# (`RequiresAdminPassword`: hesap kurulmadan 409 `parola_gerekli`).
# ---------------------------------------------------------------------------
class PersonListCreateView(APIView):
    """Birlik kişileri: liste (ad araması ve sıralaması Python'da) ve elle kayıt."""

    permission_classes = [RequiresAdminPassword]

    def get(self, request: Request) -> Response:
        params = request.query_params
        kisiler_ = selectors.person_list(
            search=params.get("search", ""),
            only_active=params.get("only_active", "").strip().lower() in TRUE_VALUES,
        )
        return Response(OabPersonSerializer(kisiler_, many=True).data)

    def post(self, request: Request) -> Response:
        govde = OabPersonCreateSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            kisi = kisiler.create_person(**dict(govde.validated_data))
        return Response(OabPersonSerializer(kisi).data, status=status.HTTP_201_CREATED)


class PersonDetailView(APIView):
    """Birlik kişisinin ayrıntısı ve güncellemesi (PATCH; silme yoktur, kayıt `PASIF` olur)."""

    permission_classes = [RequiresAdminPassword]

    def get(self, request: Request, pk: int) -> Response:
        return Response(OabPersonSerializer(get_object_or_404(selectors.person_all(), pk=pk)).data)

    def patch(self, request: Request, pk: int) -> Response:
        kisi = get_object_or_404(selectors.person_all(), pk=pk)
        govde = OabPersonUpdateSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            kisi = kisiler.update_person(kisi, **dict(govde.validated_data))
        return Response(OabPersonSerializer(kisi).data)


class PersonFromPersonnelView(APIView):
    """Personelden birlik kişisi (görev türü `YONETICI` → `IDARECI`; personel bağı kurulur)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request) -> Response:
        govde = OabPersonFromPersonnelSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            kisi = kisiler.copy_from_personnel(
                govde.validated_data["personnel"],
                ayni_kisi_degil=govde.validated_data["ayni_kisi_degil"],
            )
        return Response(OabPersonSerializer(kisi).data, status=status.HTTP_201_CREATED)


class PersonFromParentView(APIView):
    """Veli listesinden birlik kişisi (tasarım §8.4 (3)); yalnız program yöneticisi (rol kuralı)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request) -> Response:
        govde = OabPersonFromParentSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            kisi = kisiler.copy_from_parent(
                govde.validated_data["full_name"],
                ayni_kisi_degil=govde.validated_data["ayni_kisi_degil"],
            )
        return Response(OabPersonSerializer(kisi).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Organ üyelikleri (M2; tasarım §5.2.2; plan F1c-5). Yazan uçlar ilk hesap kapısını taşır (üyelik kişi
# kaydına bağlıdır, dayanak notu şifrelidir). Ekranı Organlar'dır (F1c 11. adım).
# ---------------------------------------------------------------------------
#: Kadro okumasının organları (organ ekranının sekmeleri: yönetim kurulu, Denetleme Kurulu, alım
#: komisyonu); liste okumasında temsilciler de (6. adım).
_KADRO_ORGANLARI = frozenset(o.value for o in uyelikler.KADRO_ORGANLARI)
_LISTE_ORGANLARI = _KADRO_ORGANLARI | {OrganType.TEMSILCI.value}
ORGAN_GECERSIZ = "Organ yönetim kurulu, Denetleme Kurulu, alım komisyonu ya da temsilci olmalıdır."
DONEM_GEREKLI = "Birlik dönemi seçilmelidir."


def _gerekce(veri: dict[str, Any]) -> uyum.Gerekce | None:
    metin = str(veri.pop("gerekce", "")).strip()
    kok = str(veri.pop("kok_neden", "")).strip()
    return uyum.Gerekce(metin=metin, kok_neden=kok) if metin or kok else None


def _organ(deger: str, izinli: frozenset[str] = _KADRO_ORGANLARI) -> str:
    if deger not in izinli:
        raise serializers.ValidationError({"organ": [ORGAN_GECERSIZ]})
    return deger


def _donem_parametresi(request: Request) -> Any:
    ham = request.query_params.get("term", "").strip()
    if not ham.isdigit():
        raise serializers.ValidationError({"term": [DONEM_GEREKLI]})
    return get_object_or_404(_donemler(), pk=int(ham))


class MembershipListCreateView(APIView):
    """Bir dönem ve organın üyelikleri (`?term=&organ=`; sıra Python'da) ve üyelik kaydı."""

    permission_classes = [RequiresAdminPassword]

    def get(self, request: Request) -> Response:
        donem = _donem_parametresi(request)
        organ = _organ(request.query_params.get("organ", "").strip(), _LISTE_ORGANLARI)
        uyeler = selectors.membership_list(donem, organ)
        return Response(OrganMembershipSerializer(uyeler, many=True).data)

    def post(self, request: Request) -> Response:
        govde = OrganMembershipCreateSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            uyelik = uyelikler.assign_membership(**veri, gerekce=gerekce)
        return Response(OrganMembershipSerializer(uyelik).data, status=status.HTTP_201_CREATED)


class MembershipDetailView(APIView):
    """Üyeliğin ayrıntısı ve kişisiz ayrıntılarının güncellemesi (PATCH; silme yoktur)."""

    permission_classes = [RequiresAdminPassword]

    def get(self, request: Request, pk: int) -> Response:
        uyelik = get_object_or_404(selectors.membership_all(), pk=pk)
        return Response(OrganMembershipSerializer(uyelik).data)

    def patch(self, request: Request, pk: int) -> Response:
        uyelik = get_object_or_404(selectors.membership_all(), pk=pk)
        govde = OrganMembershipUpdateSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            uyelik = uyelikler.update_membership(uyelik, **dict(govde.validated_data))
        return Response(OrganMembershipSerializer(selectors.membership_all().get(pk=pk)).data)


class MembershipEligibilityBasisView(APIView):
    """Görev alma engelinin dayanağı: özel nitelikli alan, okuması erişim günlüğüne yazılır.

    PUT engeli yazar (6. adım); yanıt dayanağı geri okumaz (okuma ayrı ve günlüklüdür).
    """

    permission_classes = [RequiresAdminPassword]

    def put(self, request: Request, pk: int) -> Response:
        uyelik = get_object_or_404(selectors.membership_all(), pk=pk)
        govde = EngelSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            uyelik = uyelik_gecisleri.engel_yaz(uyelik, **dict(govde.validated_data))
        return Response(
            {
                "eligibility_bar": uyelik.eligibility_bar,
                "eligibility_bar_found_on": uyelik.eligibility_bar_found_on,
            }
        )

    def get(self, request: Request, pk: int) -> Response:
        uyelik = get_object_or_404(selectors.membership_all(), pk=pk)
        dayanak = uyelikler.engel_dayanagini_oku(uyelik)
        return Response(
            {
                "eligibility_bar": uyelik.eligibility_bar,
                "eligibility_bar_basis": dayanak,
                "eligibility_bar_found_on": uyelik.eligibility_bar_found_on,
            }
        )


def _kadro_satiri(sonuc: Any) -> dict[str, Any]:
    return {"metin": atifli_metin(sonuc), "atif": sonuc["atif"], "durum": sonuc["durum"]}


def _oneriler(uyeler: list[Any]) -> list[dict[str, Any]]:
    """Görevdeki üyelerin önerileri ve hatırlatmaları (kişisiz metin; saklanmaz). Paket
    yüklenemezse okuma açık kalır: öneri çıkmaz, kadro çalışır."""
    try:
        return [
            {
                "uyelik": uyelik.pk,
                "tur": oneri.tur,
                "metin": oneri.metin,
                "gun": oneri.gun,
                "drop_kind": oneri.drop_kind,
            }
            for uyelik in uyeler
            for oneri in uyelik_gecisleri.oneriler(uyelik)
        ]
    except KuralPaketiKullanilamaz:
        return []


def _kadro_uyarilari(donem: Any, organ: str) -> list[dict[str, Any]]:
    """Kadro sayılarının uyarıları; paket ya da dönem kopyası okunamazsa boş (okuma açık kalır, D1, D7)."""
    try:
        return [_kadro_satiri(sonuc) for sonuc in uyelikler.kadro_uyarilari(donem, organ)]
    except KuralPaketiKullanilamaz:
        return []


def _uyelik_uyum_satirlari(donem: Any, organ: str) -> list[dict[str, Any]]:
    """Organın üyeliklerinin açık uyum satırları (eksik, sapma), oturumdaki rolün görünümüyle.

    Görev alma engeli satırını (kural kimliği ve atfı dayanağı ele verir) yalnız program yöneticisi ve
    yönetim kurulu rolleri olduğu gibi görür; Denetleme Kurulu ve müdür atıfsız genel adı görür
    (`uyum.uyum_satiri_gorunumu`; kullanıcı kararı 10.11.2026, tasarım §4.4.2 ¹¹). Gerekçe metni hiçbir
    rolde dönmez. Akış satırının atfı yoktur (Yönetmelik hükmü değildir).
    """
    kimlikler = [
        str(pk)
        for pk in OrganMembership.objects.filter(term=donem, organ=organ).values_list(
            "pk", flat=True
        )
    ]
    satirlar = ComplianceItem.objects.filter(
        term=donem,
        subject_type=denetim_izi.model_etiketi(OrganMembership),
        subject_id__in=kimlikler,
        resolved_at__isnull=True,
    ).order_by("pk")
    kim = yazar()
    rol = None if kim is None else kim.rol
    sonuc: list[dict[str, Any]] = []
    for satir in satirlar:
        gorunum = uyum.uyum_satiri_gorunumu(satir, rol)
        sonuc.append(
            {
                "id": satir.pk,
                "uyelik": int(satir.subject_id),
                "tur": satir.kind,
                "metin": gorunum["message"],
                "atif": _uyum_atfi(str(gorunum["rule_id"]), donem),
                "gerekceli": satir.justification_group_id is not None,
            }
        )
    return sonuc


def _secilme_sayaclari(organ: str, uyeler: list[Any]) -> list[dict[str, Any]]:
    """Görevdeki üyelerin seçilme sayaçları (md. 12/4, 14/3): programın kayıtları ve programdan önceki
    beyan; beyan "bilinmiyor"sa `beyan` boştur. Yönetim kurulunda başkan ve üye tek sayaçtır, Denetleme
    Kurulunda yalnız başkanlık sayılır (`uyelikler`). Alım komisyonunda sayaç yoktur."""
    if organ == OrganType.YONETIM_KURULU:
        sayac, beyan_alani = uyelikler.yk_secilme_sayisi, "external_yk_terms"
    elif organ == OrganType.DENETLEME_KURULU:
        sayac, beyan_alani = uyelikler.dk_baskanlik_sayisi, "external_dk_chair_terms"
    else:
        return []
    return [
        {
            "uyelik": uyelik.pk,
            "program": sayac(uyelik.person),
            "beyan": getattr(uyelik.person, beyan_alani),
        }
        for uyelik in uyeler
    ]


class OrganRosterView(APIView):
    """Görevdeki kadro: görevdeki asıllar, çağrılmamış yedekler, kadro sayıları ve uyarıları.

    Sayılan yalnız seçilmiş kayıttır; uyarı yazmaz, gerekçe istemez (sayılar uyarıdır). Üyeliklerin açık
    uyum satırları role göre süzülür (`_uyelik_uyum_satirlari`); seçilme sayaçları görevdeki asıllar ve
    çağrılmamış yedekler içindir (F1c 11. adım: Organlar ekranı).
    """

    def get(self, request: Request, pk: int, organ: str) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        organ = _organ(organ)
        sayilar = selectors.kadro_sayilari(donem, organ)
        asillar = selectors.gorevdeki_asillar(donem, organ)
        yedekler = selectors.bekleyen_yedekler(donem, organ)
        return Response(
            {
                "organ": organ,
                "gorevdeki_asillar": OrganMembershipSerializer(asillar, many=True).data,
                "bekleyen_yedekler": OrganMembershipSerializer(yedekler, many=True).data,
                "kadro": {"asil": sayilar[SeatType.ASIL], "yedek": sayilar[SeatType.YEDEK]},
                "kadro_uyarilari": _kadro_uyarilari(donem, organ),
                "oneriler": _oneriler(asillar),
                "uyum_satirlari": _uyelik_uyum_satirlari(donem, organ),
                "secilme_sayaclari": _secilme_sayaclari(organ, [*asillar, *yedekler]),
            }
        )


# ---------------------------------------------------------------------------
# Görev bölümü, yedek çağrısı, düşme, iptal, temsilciler, alım komisyonu (F1c 6. adım; ekranları
# Organlar ve Temsilciler, 11. adım). Rol daraltmaları uç kuralındadır (`rol_izinleri`; tasarım §7.2
# "Kim").
# ---------------------------------------------------------------------------
_YK_GOREV_ALANLARI: dict[str, str] = {
    "baskan": MembershipRole.BASKAN,
    "baskan_yardimcisi": MembershipRole.BASKAN_YARDIMCISI,
    "muhasip": MembershipRole.MUHASIP,
    "sekreter": MembershipRole.SEKRETER,
}


def _katilim(satirlar: list[dict[str, Any]]) -> list[gorev_bolumu.KatilimSatiri]:
    return [
        gorev_bolumu.KatilimSatiri(
            uyelik=satir["membership"], present=satir["present"], excused=satir["excused"]
        )
        for satir in satirlar
    ]


def _gorev_bolumu_yaniti(sonuc: gorev_bolumu.GorevBolumu) -> dict[str, Any]:
    return {
        "toplanti": sonuc.toplanti.pk,
        "karar": sonuc.karar.pk,
        "karar_durumu": sonuc.karar.status,
        "uyelikler": OrganMembershipSerializer(
            [selectors.membership_all().get(pk=u.pk) for u in sonuc.uyelikler], many=True
        ).data,
    }


class YkDutyAssignmentView(APIView):
    """Yönetim kurulunun görev bölümü (md. 12/3): toplantı, katılım, görevler, `TASLAK` karar."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        govde = YkGorevBolumuSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        gorevler = {
            role: veri.pop(alan) for alan, role in _YK_GOREV_ALANLARI.items() if veri.get(alan)
        }
        with _hizmet_hatalari():
            sonuc = gorev_bolumu.yk_gorev_bolumu(
                term=donem,
                held_at=veri["held_at"],
                gorevler=gorevler,
                katilim=_katilim(veri["katilim"]),
                place=veri["place"],
                text=veri["text"],
                gerekce=gerekce,
            )
        return Response(_gorev_bolumu_yaniti(sonuc), status=status.HTTP_201_CREATED)


class DkDutyAssignmentView(APIView):
    """Denetleme Kurulunun görev bölümü ve denetim planı (md. 14/1; yalnız Denetleme Kurulu, M8)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        govde = DkGorevBolumuSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            sonuc = gorev_bolumu.dk_gorev_bolumu(
                term=donem,
                held_at=veri["held_at"],
                baskan=veri["baskan"],
                katilim=_katilim(veri["katilim"]),
                denetim_plani=veri["denetim_plani"],
                place=veri["place"],
                text=veri["text"],
                gerekce=gerekce,
            )
        return Response(_gorev_bolumu_yaniti(sonuc), status=status.HTTP_201_CREATED)


class MembershipSubstituteCallYkView(APIView):
    """Yönetim kurulu yedeğinin asıl üyeliğe çağrısı (md. 13/6; sekreter, YK kararıyla)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        uyelik = get_object_or_404(selectors.membership_all(), pk=pk)
        govde = YkYedekCagrisiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            uyelik_gecisleri.yedek_cagir(
                uyelik,
                organ=OrganType.YONETIM_KURULU,
                promoted_on=veri["promoted_on"],
                karar=veri["promoted_by_decision"],
                gerekce=gerekce,
            )
        return Response(OrganMembershipSerializer(selectors.membership_all().get(pk=pk)).data)


class MembershipSubstituteCallDkView(APIView):
    """Denetleme Kurulu yedeğinin asıl üyeliğe çağrısı (md. 14/6; program yöneticisi, karar yok)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        uyelik = get_object_or_404(selectors.membership_all(), pk=pk)
        govde = DkYedekCagrisiSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            uyelik_gecisleri.yedek_cagir(
                uyelik,
                organ=OrganType.DENETLEME_KURULU,
                promoted_on=govde.validated_data["promoted_on"],
            )
        return Response(OrganMembershipSerializer(selectors.membership_all().get(pk=pk)).data)


class MembershipDropView(APIView):
    """Üyeliğin düşmesi (tür zorunlu) ya da md. 7/2'de olağanüstü genel kurula ertelenmesi."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        uyelik = get_object_or_404(selectors.membership_all(), pk=pk)
        govde = DusmeSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            uyelik_gecisleri.uyeligi_dusur(uyelik, **veri, gerekce=gerekce)
        return Response(OrganMembershipSerializer(selectors.membership_all().get(pk=pk)).data)


class MembershipCancelView(APIView):
    """Yanlış üyelik kaydının iptali (gerekçe zorunlu; kim iz satırındadır)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        uyelik = get_object_or_404(selectors.membership_all(), pk=pk)
        govde = IptalSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            uyelik_gecisleri.uyeligi_iptal_et(
                uyelik, cancel_reason=govde.validated_data["cancel_reason"]
            )
        return Response(OrganMembershipSerializer(selectors.membership_all().get(pk=pk)).data)


def _cizelge_satiri(satir: temsilciler.TemsilciSatiri) -> dict[str, Any]:
    return {
        "representation": satir.representation,
        "ad": satir.ad,
        "kural": satir.kural,
        "durum": satir.durum,
        "metin": satir.metin,
        "notlar": satir.notlar,
        "uyeler": OrganMembershipSerializer(satir.uyeler, many=True).data,
    }


class RepresentativeListCreateView(APIView):
    """Temsilciler çizelgesi (`?term=`; tasarım §6.4.4, E03'ün kaynağı) ve temsilci kaydı."""

    permission_classes = [RequiresAdminPassword]

    def get(self, request: Request) -> Response:
        donem = _donem_parametresi(request)
        try:
            satirlar = temsilciler.temsilci_cizelgesi(donem)
        except KuralPaketiKullanilamaz:
            satirlar = []
        return Response([_cizelge_satiri(satir) for satir in satirlar])

    def post(self, request: Request) -> Response:
        govde = TemsilciCreateSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        with _hizmet_hatalari():
            uyelik = temsilciler.temsilci_ekle(**veri, gerekce=gerekce)
        return Response(
            OrganMembershipSerializer(selectors.membership_all().get(pk=uyelik.pk)).data,
            status=status.HTTP_201_CREATED,
        )


class PurchaseCommitteeCreateView(APIView):
    """Alım komisyonu üyesi (md. 18/1); kadrosu organ kadrosu ucundadır (`ALIM_KOMISYONU`)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request) -> Response:
        govde = AlimKomisyonuCreateSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            uyelik = temsilciler.alim_komisyonu_uyesi_ekle(**dict(govde.validated_data))
        return Response(
            OrganMembershipSerializer(selectors.membership_all().get(pk=uyelik.pk)).data,
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# E01, E02, E03 (F1c 10. adım; düğmeleri Organlar ve Temsilciler'de, 11. adım). Üretim uç kuralıyla ve
# serviste daraltılır
# (tasarım §9.6 "Üreten"); basım her okur role açıktır, `BASIM` satırı okuma rolünde de yazılır.
# ---------------------------------------------------------------------------
def _evrak_satiri(kayit: oab_modelleri.GeneratedDocument) -> dict[str, Any]:
    return {
        "id": kayit.pk,
        "kod": kayit.doc_type,
        "ad": gorev_evraki.BELGE_ADLARI[str(kayit.doc_type)],
        "surum": kayit.version,
        "durum": kayit.status,
        "uretim_zamani": kayit.generated_at.isoformat(),
        "bicimler": kayit.formats,
    }


@contextmanager
def _depo_yazma_hatalari() -> Iterator[None]:
    """Dosya deposunun ret ve bakım hataları 409'dur (ileti deponundur; kayıt geri alınır)."""
    try:
        yield
    except (dosya_deposu.DosyaDeposuHatasi, dosya_sifreleme.DosyaSifrelemeHatasi) as exc:
        raise EvrakDosyasiYazilamadi(str(exc)) from exc


class TermDocumentListView(APIView):
    """Dönemin geçerli görev bölümü ve temsilci evrakı (E01-E03): kayıt, sürüm, biçimler."""

    def get(self, request: Request, pk: int) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        return Response([_evrak_satiri(k) for k in gorev_evraki.evrak_listesi(donem)])


class _EvrakUretimView(APIView):
    """Evrakın üretimi: yeni sürüm kaydı, PDF ve Word dosyası; yanıtta basım uyarıları."""

    permission_classes = [RequiresAdminPassword]
    kod: str = ""

    def post(self, request: Request, pk: int) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        with _hizmet_hatalari(), _depo_yazma_hatalari():
            uretim = gorev_evraki.uret(self.kod, donem)
        return Response(
            {"evrak": _evrak_satiri(uretim.kayit), "uyarilar": list(uretim.uyarilar)},
            status=status.HTTP_201_CREATED,
        )


class E01DocumentView(_EvrakUretimView):
    """Yönetim kurulu görev bölümü, imza yetkisi ve temsilci karar taslağı (sekreter, yonetici)."""

    kod = gorev_evraki.E01


class E02DocumentView(_EvrakUretimView):
    """Denetleme Kurulu görev bölümü tutanağı ve denetim planı (yalnız Denetleme Kurulu, M8 ⁵)."""

    kod = gorev_evraki.E02


class E03DocumentView(_EvrakUretimView):
    """Birlik temsilcilerinin görevlendirme çizelgesi (sekreter, yonetici)."""

    kod = gorev_evraki.E03


class DocumentDownloadView(APIView):
    """Kaydedilmiş evrakın dosyası (`pdf` ya da `docx`) ve `BASIM` satırı (okuma rolünde de).

    HEAD dosya vermez, basım izi de yazmaz: 405 (basım yalnız GET'tir).
    """

    def get(self, request: Request, pk: int, bicim: str) -> Any:
        kayit = get_object_or_404(oab_modelleri.GeneratedDocument.objects.all(), pk=pk)
        try:
            return gorev_evraki.bas(kayit, gorev_evraki.bicim_coz(bicim))
        except (dosya_deposu.DosyaDeposuHatasi, dosya_sifreleme.DosyaSifrelemeHatasi) as exc:
            raise EvrakDosyasiAcilamadi(str(exc)) from exc

    def head(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.http_method_not_allowed(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Geçiş kurulumu (tasarım §7.9 adım 1-4; plan F1c 8. adım; ekranı Birlik Dönemi → Geçiş Kurulumu). Kaydı
# yalnız program yöneticisi yazar (M1, `Eylem.BIRLIK_DONEMI_YAZMA`); okuma her role açıktır. İşaretten
# sonra her yazma 409 `gecis_kapali`. Devralınan üyeliğin iptali genel iptal ucundadır
# (`MembershipCancelView`; servis devralınan kaydı yalnız program yöneticisine açar).
# ---------------------------------------------------------------------------
#: Geçiş ekranında gösterilen uyum satırlarının kuralları: seçilme sayacının "bilinmiyor" beyanı ve
#: karar defterinin noter tasdiki (kişisiz ileti; konu kişi, üyelik ya da defter kimliğidir).
_GECIS_UYUM_KURALLARI = frozenset({*kisiler.SAYAC_KURALLARI.values(), kurullar.TASDIK_KURALI})
TEMSIL_GEREKLI = "Temsil edilen kurul ya da komisyon seçilmelidir."
#: Sayaç kuralı → beyan ucunun alanı (`TransitionElectionCountsView`: `yk`, `dk_baskanlik`).
_SAYAC_ALANLARI = {
    kisiler.SAYAC_KURALLARI["external_yk_terms"]: "yk",
    kisiler.SAYAC_KURALLARI["external_dk_chair_terms"]: "dk_baskanlik",
}


def _karar_defteri() -> OfficialBook | None:
    defter: OfficialBook | None = (
        OfficialBook.objects.filter(kind=BookKind.KARAR_DEFTERI)
        .exclude(status=BookStatus.IPTAL)
        .order_by("pk")
        .first()
    )
    return defter


def _uyum_atfi(kural_id: str, donem: Any) -> str:
    """Satırın madde atfı (dönem kopyasından); okunamazsa boş (satırın iletisi yine gösterilir)."""
    try:
        return atif_metni(kural_kaydi(kural_id, tarih=timezone.localdate(), donem=donem))
    except (BilinmeyenKural, YururlukteDegerYok, KuralPaketiKullanilamaz):
        return ""


def _gecis_uyum_satirlari(donem: Any) -> list[dict[str, Any]]:
    """Geçiş döneminin açık sayaç ve tasdik satırları (eksik, sapma); ileti kişisizdir."""
    satirlar = ComplianceItem.objects.filter(
        term=donem, rule_id__in=_GECIS_UYUM_KURALLARI, resolved_at__isnull=True
    ).order_by("pk")
    return [
        {
            "id": satir.pk,
            "tur": satir.kind,
            "konu_turu": satir.subject_type,
            "konu": satir.subject_id,
            "metin": satir.message,
            "atif": _uyum_atfi(satir.rule_id, donem),
            "gerekceli": satir.justification_group_id is not None,
            # Sayaç satırının beyan alanı (ekran beyan tablosunda "Bilinmiyor"u gösterir); öteki satırda boş.
            "sayac_alani": _SAYAC_ALANLARI.get(satir.rule_id, ""),
        }
        for satir in satirlar
    ]


def _gorev_suresi(donem: Any) -> list[dict[str, Any]]:
    """Görev süresi uyarıları (kaydedilmez; md. 12/2, 14/2). Paket ya da kopya okunamazsa boş."""
    try:
        return [_kadro_satiri(sonuc) for sonuc in gecis.gorev_suresi_uyarilari(donem)]
    except KuralPaketiKullanilamaz:
        return []


class TransitionView(APIView):
    """Geçiş kurulumunun durumu: açık adımlar, geçiş dönemi, karar defteri, uyum satırları.

    Kişisizdir (adlar üyelik ve kişi uçlarından okunur). Görev süresi uyarısı ve uyum satırları
    yalnız geçiş dönemi açıkken hesaplanır.
    """

    def get(self, request: Request) -> Response:
        donem = gecis.gecis_donemi()
        defter = _karar_defteri()
        acik = donem is not None and donem.status == TermStatus.ACIK
        return Response(
            {
                **gecis.yol_haritasi_durumu(),
                "donem": None if donem is None else OabTermSerializer(donem).data,
                "karar_defteri": None if defter is None else KararDefteriSerializer(defter).data,
                "gorev_suresi_uyarilari": _gorev_suresi(donem) if acik else [],
                "uyum_satirlari": _gecis_uyum_satirlari(donem) if acik else [],
            }
        )


class TransitionInheritedView(APIView):
    """Görevdeki kurulun üyesi ya da temsilci (`DEVRALINAN`; §7.9 adım 2). Koltuk uygunluğu serttir."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request) -> Response:
        govde = DevralinanSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = dict(govde.validated_data)
        gerekce = _gerekce(veri)
        organ = veri.pop("organ")
        temsil = veri.pop("representation")
        if organ == OrganType.TEMSILCI and not temsil:
            raise serializers.ValidationError({"representation": [TEMSIL_GEREKLI]})
        with _hizmet_hatalari():
            if organ == OrganType.TEMSILCI:
                uyelik = gecis.devralinan_temsilci_ekle(
                    person=veri["person"],
                    representation=temsil,
                    seat_type=veri["seat_type"],
                    start_date=veri.get("start_date"),
                    evidence_note=veri["evidence_note"],
                    gerekce=gerekce,
                )
            else:
                uyelik = gecis.devralinan_ekle(organ=organ, **veri, gerekce=gerekce)
        return Response(
            OrganMembershipSerializer(selectors.membership_all().get(pk=uyelik.pk)).data,
            status=status.HTTP_201_CREATED,
        )


class TransitionElectionCountsView(APIView):
    """Programdan önceki seçilme sayılarının toplu beyanı (§7.9 adım 3); "bilinmiyor" tek gerekçeyle."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request) -> Response:
        govde = SayacBeyaniSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        veri = govde.validated_data
        beyanlar = [
            gecis.SayacBeyani(
                kisi=satir["person"],
                yk=satir.get("yk", gecis.YOK),
                dk_baskanlik=satir.get("dk_baskanlik", gecis.YOK),
            )
            for satir in veri["beyanlar"]
        ]
        with _hizmet_hatalari():
            sonuc = gecis.sayac_beyani(
                beyanlar,
                gerekce=veri["gerekce"],
                duzeltme_gerekcesi=veri["duzeltme_gerekcesi"],
            )
        kimlikler = [beyan.kisi.pk for beyan in beyanlar]
        return Response(
            {
                "kisiler": OabPersonSerializer(
                    selectors.person_all().filter(pk__in=kimlikler), many=True
                ).data,
                "bilinmeyen_sayisi": len(sonuc.bilinmeyenler),
            }
        )


class TransitionDecisionBookView(APIView):
    """Karar defterinin geçiş kaydı (§7.9 adım 4): son sıra no ve sayfa; tasdik yoksa gerekçe."""

    def post(self, request: Request) -> Response:
        govde = KararDefteriGecisSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            defter = gecis.karar_defteri_kaydet(**dict(govde.validated_data))
        return Response(KararDefteriSerializer(defter).data, status=status.HTTP_201_CREATED)


class TransitionDecisionBookCancelView(APIView):
    """Yanlış girilmiş karar defteri kaydının iptali (gerekçe şifreli; açık tasdik satırı kapanır)."""

    def post(self, request: Request, pk: int) -> Response:
        defter = get_object_or_404(OfficialBook.objects.filter(kind=BookKind.KARAR_DEFTERI), pk=pk)
        govde = IptalSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            defter = gecis.karar_defterini_iptal_et(
                defter, cancel_reason=govde.validated_data["cancel_reason"]
            )
        return Response(KararDefteriSerializer(defter).data)


class TransitionCompleteView(APIView):
    """ "Geçiş kurulumu tamamlandı" işareti: geçiş kayıtları kilitlenir (sonra 409 `gecis_kapali`)."""

    def post(self, request: Request) -> Response:
        with _hizmet_hatalari():
            donem = gecis.gecisi_tamamla()
        return Response(OabTermSerializer(donem).data)


# ---------------------------------------------------------------------------
# Gerekçe kutusunun yarım metni (tasarım §7 "Yarım kalan metin"; plan F1c 3. adım notları "yarım metin
# kaydının ucu 11. adımda"). Oturumdaki hesabın tek, şifreli kaydıdır; ekran yazarken kısa aralıklarla
# yazar, kayıt yapılınca ya da vazgeçilince siler. Denetim izine satır yazmaz (`yarim_metin`). Panodaki
# "yarım kalan taslak" kalemi F1c'nin 12. adımındadır.
# ---------------------------------------------------------------------------
class DraftTextView(APIView):
    """Oturumdaki hesabın yarım metni: okuma, yazma (boş metin siler) ve bağlama göre silme."""

    def get(self, request: Request) -> Response:
        kayit = yarim_metin.oku()
        if kayit is None or not isinstance(kayit.text, str):
            return Response(status=status.HTTP_204_NO_CONTENT)  # yarım metin yok
        return Response(
            {
                "metin": kayit.text,
                "baglam": kayit.context,
                "guncelleme": kayit.updated_at.isoformat(),
            }
        )

    def put(self, request: Request) -> Response:
        govde = YarimMetinSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        yarim_metin.kaydet(govde.validated_data["metin"], baglam=govde.validated_data["baglam"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request) -> Response:
        # `?baglam=` (kişisiz kutu adı, ör. `gecis.karar_defteri`): yalnız o kutunun metni silinir.
        yarim_metin.temizle(str(request.query_params.get("baglam", "")))
        return Response(status=status.HTTP_204_NO_CONTENT)
