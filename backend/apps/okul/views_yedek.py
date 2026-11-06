"""Dış yedek hatırlatması (aile iskeletinden; tasarım §16 R6, §4.3 tehdit 18) ve Yedek Raporu uçları.

| Uç | Ad | İş |
|---|---|---|
| `GET backups/external/` | `backup-external-reminder` | Son şifreli yedeğin tarihi, hatırlatma süresi, Genel Bakış kartının gösterilip gösterilmeyeceği ve son denemenin özeti (`son_deneme`; yoksa `null`; kişisel veri yok) |
| `PUT backups/external/` | `backup-external-reminder` | `{reminder_days}` — hatırlatma süresi (7-90 gün) |
| `POST backups/report/` | `backup-report` | Yedek Raporu'nun PDF'i (`yedek_raporu`; plan F1b-3) |

Tarih yedek kaydedilince kendiliğinden yazılır (`encrypted_backup.sifreli_yedegi_kaydet`);
burada elle "aldım" işareti YOKTUR — kart yalnız programın gördüğü olayı söyler.
Kilitliyken kilit kapısı keser (iki yol da kilit muafiyeti taşımaz); okuma ve
yazma yalnız program yöneticisine açıktır (tasarım §4.4.2 Güvenlik satırı;
`rol_izinleri.KURALLAR`).
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from django.http import FileResponse
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.okul.services import dis_yedek, yedek_raporu


class DisYedekAyariSerializer(serializers.Serializer[dict[str, Any]]):
    reminder_days = serializers.IntegerField(
        min_value=dis_yedek.EN_AZ_HATIRLATMA_GUN,
        max_value=dis_yedek.EN_COK_HATIRLATMA_GUN,
        error_messages={
            "min_value": dis_yedek.SURE_ARALIK_MESAJI,
            "max_value": dis_yedek.SURE_ARALIK_MESAJI,
            "invalid": dis_yedek.SURE_ARALIK_MESAJI,
            "required": dis_yedek.SURE_ARALIK_MESAJI,
            "null": dis_yedek.SURE_ARALIK_MESAJI,
        },
    )


class DisYedekView(APIView):
    """`GET`/`PUT backups/external/` — dış yedek hatırlatmasının durumu ve süresi."""

    def get(self, request: Request) -> Response:
        return Response(dis_yedek.durum().as_dict())

    def put(self, request: Request) -> Response:
        req = DisYedekAyariSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        try:
            sonuc = dis_yedek.hatirlatma_suresini_ayarla(req.validated_data["reminder_days"])
        except ValueError as exc:  # pragma: no cover — serializer aynı aralığı denetler
            raise serializers.ValidationError({"reminder_days": [str(exc)]}) from exc
        return Response(sonuc.as_dict())


class YedekRaporuView(APIView):
    """`POST backups/report/` — Yedek Raporu (`yedek_raporu`; plan F1b-3).

    Gövde yoktur. PDF bellekten, ek olarak verilir; önbelleğe alınmaz ve saklanmaz. Basımın izi
    `BASIM` satırıdır: POST bu yüzdendir. Satır yazılamazsa yanıt 409 `iz_yazilamadi`'dır.
    """

    def post(self, request: Request) -> FileResponse:
        rapor = yedek_raporu.yedek_raporu()
        yanit = FileResponse(
            BytesIO(rapor.pdf),
            as_attachment=True,
            filename=rapor.dosya_adi,
            content_type="application/pdf",
        )
        yanit["Cache-Control"] = "no-store"
        return yanit
