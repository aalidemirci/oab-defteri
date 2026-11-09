"""`oab` görünümleri."""

from __future__ import annotations

from typing import Any

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.oab.kurallar import KuralPaketiKullanilamaz, atifli_metin, bilgi_notu
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
