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
from apps.oab.serializers import (
    OabPersonCreateSerializer,
    OabPersonFromParentSerializer,
    OabPersonFromPersonnelSerializer,
    OabPersonSerializer,
    OabPersonUpdateSerializer,
    OabTermAcilisSerializer,
    OabTermSerializer,
)
from apps.oab.services import donemler, kisiler
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
