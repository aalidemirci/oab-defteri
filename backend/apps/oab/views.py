"""`oab` görünümleri."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from rest_framework import serializers, status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.oab import models as oab_modelleri
from apps.oab import selectors
from apps.oab.kurallar import KuralPaketiKullanilamaz, atifli_metin, bilgi_notu
from apps.oab.models import MembershipRole, OrganType
from apps.oab.serializers import (
    AlimKomisyonuCreateSerializer,
    DkGorevBolumuSerializer,
    DkYedekCagrisiSerializer,
    DusmeSerializer,
    EngelSerializer,
    IptalSerializer,
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
    TemsilciCreateSerializer,
    YkGorevBolumuSerializer,
    YkYedekCagrisiSerializer,
)
from apps.oab.services import (
    donemler,
    gorev_bolumu,
    kisiler,
    temsilciler,
    uyelik_gecisleri,
    uyelikler,
    uyum,
)
from apps.okul.models import CanteenMode
from apps.okul.permissions import RequiresAdminPassword

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
    """Birlik dönemleri: liste ve ilk dönemin açılışı (M1; tasarım §4.4.2, §7.9 adım 1)."""

    def get(self, request: Request) -> Response:
        return Response(OabTermSerializer(_donemler(), many=True).data)

    def post(self, request: Request) -> Response:
        govde = OabTermAcilisSerializer(data=request.data)
        govde.is_valid(raise_exception=True)
        with _hizmet_hatalari():
            donem = donemler.create_term(**dict(govde.validated_data))
        return Response(OabTermSerializer(donem).data, status=status.HTTP_201_CREATED)


class TermDetailView(APIView):
    """Birlik döneminin ayrıntısı; kural sürümü salt okunur satırıyla."""

    def get(self, request: Request, pk: int) -> Response:
        return Response(OabTermSerializer(get_object_or_404(_donemler(), pk=pk)).data)


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
# kaydına bağlıdır, dayanak notu şifrelidir). Ekranı F1c'nin 11. adımındadır.
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


class OrganRosterView(APIView):
    """Görevdeki kadro: görevdeki asıllar, çağrılmamış yedekler, kadro sayıları ve uyarıları.

    Sayılan yalnız seçilmiş kayıttır; uyarı yazmaz, gerekçe istemez (sayılar uyarıdır).
    """

    def get(self, request: Request, pk: int, organ: str) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        organ = _organ(organ)
        sayilar = selectors.kadro_sayilari(donem, organ)
        asillar = selectors.gorevdeki_asillar(donem, organ)
        return Response(
            {
                "organ": organ,
                "gorevdeki_asillar": OrganMembershipSerializer(asillar, many=True).data,
                "bekleyen_yedekler": OrganMembershipSerializer(
                    selectors.bekleyen_yedekler(donem, organ), many=True
                ).data,
                "kadro": {"asil": sayilar["ASIL"], "yedek": sayilar["YEDEK"]},
                "kadro_uyarilari": [
                    _kadro_satiri(sonuc) for sonuc in uyelikler.kadro_uyarilari(donem, organ)
                ],
                "oneriler": _oneriler(asillar),
            }
        )


# ---------------------------------------------------------------------------
# Görev bölümü, yedek çağrısı, düşme, iptal, temsilciler, alım komisyonu (F1c 6. adım; ekranları 11.
# adımda). Rol daraltmaları uç kuralındadır (`rol_izinleri`; tasarım §7.2 "Kim").
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
