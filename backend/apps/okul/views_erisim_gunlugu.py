"""Erişim günlüğünün okuma ucu (plan F1b-2 "Erişim günlüğü okuma ucu"; tasarım §4.6.4, §4.4.2).

* `GET access-log/` `?baslangic=yyyy-aa-gg&bitis=yyyy-aa-gg&tur=<tür>&hesap=<kimlik>&sayfa=N` →
  `{satirlar, toplam, sayfa, sayfa_sayisi, sayfa_boyutu, turler, hesaplar}`
  (`erisim_gunlugu.liste`): en yeni önce, sayfalı; gün Europe/Istanbul'a göredir, iki uç dahildir.
  Bütün süzgeçler isteğe bağlıdır; boş değer verilmemiş sayılır, bilinmeyen anahtar yok sayılır.
  Satır kişisizdir: okuyan hesap rol etiketi (sıra no'suz) ve tanıtıcıyla anılır, ad-soyad yoktur.

Program yöneticisi ve Denetleme Kuruluna açıktır: rol kapısı (`rol_izinleri.KURALLAR`, matrisin
"Erişim günlüğü" satırı) ve servisin okuma denetimi birlikte. Yalnız açık oturumda (kilitliyken
kilit kapısı 423 verir). OKUMA İZ BIRAKMAZ: ne denetim izine ne erişim günlüğüne satır yazılır.

RET KODLARI: biçimsiz süzgeç ya da ters tarih aralığı 400 `validation_error` (Türkçe ileti; sözlük
§1 "Erişim günlüğü (F1b)"); rol 403 `rol_yetkisiz`. 400'ün iletisi süzgecin alanına bağlıdır
(`fields`: `baslangic`, `bitis`, `tur`, `hesap`, `sayfa`): takvimin ucundaki gün ve ters aralık da
(`erisim_gunlugu.tarih_suzgeci_hatalari`; ters aralıkta `bitis`) — ekran iletiyi o alanın altına
yazar.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.okul import erisim_gunlugu
from apps.okul.models import AccessKind
from apps.okul.views_oturum import guvenlik_hatalari


class ErisimGunluguSorgusu(serializers.Serializer[dict[str, Any]]):
    """Okuma ekranının süzgeçleri (hepsi isteğe bağlı)."""

    baslangic = serializers.DateField(
        required=False,
        error_messages={
            "invalid": erisim_gunlugu.TARIH_MESAJI,
            "datetime": erisim_gunlugu.TARIH_MESAJI,
        },
    )
    bitis = serializers.DateField(
        required=False,
        error_messages={
            "invalid": erisim_gunlugu.TARIH_MESAJI,
            "datetime": erisim_gunlugu.TARIH_MESAJI,
        },
    )
    tur = serializers.ChoiceField(
        choices=AccessKind.values,
        required=False,
        error_messages={"invalid_choice": erisim_gunlugu.TUR_MESAJI},
    )
    hesap = serializers.UUIDField(
        required=False, error_messages={"invalid": erisim_gunlugu.HESAP_MESAJI}
    )
    sayfa = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        max_value=erisim_gunlugu.AZAMI_SAYFA,
        error_messages={
            "invalid": erisim_gunlugu.SAYFA_MESAJI,
            "max_string_length": erisim_gunlugu.SAYFA_MESAJI,
            "min_value": erisim_gunlugu.SAYFA_MESAJI,
            "max_value": erisim_gunlugu.SAYFA_MESAJI,
        },
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Takvimin uçları ve ters aralık alan adıyla reddedilir (modül başlığı "RET KODLARI")."""
        hatalar = erisim_gunlugu.tarih_suzgeci_hatalari(attrs.get("baslangic"), attrs.get("bitis"))
        if hatalar:
            raise serializers.ValidationError({alan: [ileti] for alan, ileti in hatalar.items()})
        return attrs


class ErisimGunluguView(APIView):
    """`GET /api/v1/access-log/` — erişim günlüğünün bir sayfası (modül başlığı)."""

    def get(self, request: Request) -> Response:
        veri = {ad: deger for ad, deger in request.query_params.items() if deger != ""}
        req = ErisimGunluguSorgusu(data=veri)
        req.is_valid(raise_exception=True)
        with guvenlik_hatalari():
            return Response(erisim_gunlugu.liste(**req.validated_data))
