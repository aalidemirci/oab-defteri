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
from apps.oab.kurallar import KuralPaketiKullanilamaz, atifli_metin, bilgi_notu
from apps.oab.serializers import OabTermAcilisSerializer, OabTermSerializer
from apps.oab.services import donemler
from apps.okul.models import CanteenMode

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
