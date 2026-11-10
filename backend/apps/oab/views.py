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
from apps.oab.models import OrganType
from apps.oab.serializers import (
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
)
from apps.oab.services import donemler, kisiler, uyelikler, uyum
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
#: Kadro ve liste okumasının organları (bu adımda yazılanlar).
_KADRO_ORGANLARI = frozenset({OrganType.YONETIM_KURULU.value, OrganType.DENETLEME_KURULU.value})
ORGAN_GECERSIZ = "Organ yönetim kurulu ya da Denetleme Kurulu olmalıdır."
DONEM_GEREKLI = "Birlik dönemi seçilmelidir."


def _gerekce(veri: dict[str, Any]) -> uyum.Gerekce | None:
    metin = str(veri.pop("gerekce", "")).strip()
    kok = str(veri.pop("kok_neden", "")).strip()
    return uyum.Gerekce(metin=metin, kok_neden=kok) if metin or kok else None


def _organ(deger: str) -> str:
    if deger not in _KADRO_ORGANLARI:
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
        organ = _organ(request.query_params.get("organ", "").strip())
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
    """Görev alma engelinin dayanağı: özel nitelikli alan, okuması erişim günlüğüne yazılır."""

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


class OrganRosterView(APIView):
    """Görevdeki kadro: görevdeki asıllar, çağrılmamış yedekler, kadro sayıları ve uyarıları.

    Sayılan yalnız seçilmiş kayıttır; uyarı yazmaz, gerekçe istemez (sayılar uyarıdır).
    """

    def get(self, request: Request, pk: int, organ: str) -> Response:
        donem = get_object_or_404(_donemler(), pk=pk)
        organ = _organ(organ)
        sayilar = selectors.kadro_sayilari(donem, organ)
        return Response(
            {
                "organ": organ,
                "gorevdeki_asillar": OrganMembershipSerializer(
                    selectors.gorevdeki_asillar(donem, organ), many=True
                ).data,
                "bekleyen_yedekler": OrganMembershipSerializer(
                    selectors.bekleyen_yedekler(donem, organ), many=True
                ).data,
                "kadro": {"asil": sayilar["ASIL"], "yedek": sayilar["YEDEK"]},
                "kadro_uyarilari": [
                    _kadro_satiri(sonuc) for sonuc in uyelikler.kadro_uyarilari(donem, organ)
                ],
            }
        )
