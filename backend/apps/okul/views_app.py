"""Program uçları — `POST app/quit/`: arayüzden düzenli çıkış (tasarım §4.2 "Kapanış").

Pencerenin çarpısı programı kapatır (T6, tasarım §4.5); tepsi yoktur. Düzenli
kapanış ayrıca tek kopya kanalının `kapat` komutundan (kurucu), Linux'ta oturum
kapanışından (SIGTERM) ve bu uçtan gelir. Uç, pencere süslemesi olmayan Linux
masaüstünün çıkış yoludur (tasarım §4.5).

Kip kuralı (aile iskeletinden; tasarım §4.2 Çık'ı her oturum durumunda parolasız
ister — kip F1b'nin 1. adımında oturuma döner):

| Durum | Çık |
|---|---|
| yönetici kipi | parolasız |
| görevli kipi | gövdede yönetici parolası; parolasız istek **403** `cikis_parolasi_gerekli`, yanlış parola 400 "Parola hatalı." (+ kademeli gecikme) |
| kilitli, kurulum, güvenlik dosyası kayıp, yeniden başlat gerekli | parolasız |

Bu koruma **kaza önleyicidir, güvenlik sınırı değildir**: Görev
Yöneticisi süreci her durumda kapatabilir. Görevli kipinin izin listesinde uç
yalnız `POST` olarak durur (`kip_izinleri`); parolayı bu görünüm denetler.
Kilit kapısı ve yeniden başlat kapısı bu yolu geçirir (`lock_middleware`,
`restart_gate`): kilitliyken de programdan çıkılabilmelidir.

Başarıda 202 döner ve kapanış masaüstü kancasıyla (`masaustu_kanca.cikis_iste`)
AYRI bir iş parçacığında başlar: yanıt önce gönderilir, sonra pencere, yönetim
sunucusu ve WAL checkpoint sırasıyla kapanır (`desktop/main.py`). Kanca yoksa
(geliştirme sunucusu) 503 `cikis_kullanilamiyor`.

Parola hiçbir yanıtta, günlükte ya da hata iletisinde yankılanmaz.
"""

from __future__ import annotations

import logging
from typing import Any

from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.okul import masaustu_kanca, restart_gate, son_oturum
from apps.okul.kip import GOREVLI, KIP
from apps.okul.services import app_password

logger = logging.getLogger("oab_defteri.cikis")

CIKIS_PAROLASI_GEREKLI = "Görevli kipinde programdan çıkmak için yönetici parolasını girin."
CIKIS_KULLANILAMIYOR = (
    "Program masaüstü penceresinde çalışmıyor; bu ortamda arayüzden çıkış yapılamaz."
)


class CikisSerializer(serializers.Serializer[dict[str, Any]]):
    password = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)


def _hata(kod: str, ileti: str, durum_kodu: int) -> Response:
    return Response({"code": kod, "message": ileti, "fields": {}}, status=durum_kodu)


class AppQuitView(APIView):
    """`POST /api/v1/app/quit/` — düzenli kapanışı başlatır (kip kuralı modül başlığında)."""

    def post(self, request: Request) -> Response:
        # Geri yüklemeden sonra kip durumu bayattır; çıkış her durumda parolasızdır.
        if not restart_gate.restart_required() and KIP.durum() == GOREVLI:
            req = CikisSerializer(data=request.data)
            req.is_valid(raise_exception=True)
            parola = str(req.validated_data.get("password") or "")
            if not parola:
                return _hata(
                    "cikis_parolasi_gerekli", CIKIS_PAROLASI_GEREKLI, status.HTTP_403_FORBIDDEN
                )
            try:
                app_password.verify_password(parola)
            except app_password.AppPasswordError as exc:
                raise serializers.ValidationError(str(exc)) from exc
        if not masaustu_kanca.cikis_iste():
            return _hata(
                "cikis_kullanilamiyor", CIKIS_KULLANILAMIYOR, status.HTTP_503_SERVICE_UNAVAILABLE
            )
        logger.info("Arayüzden çıkış istendi; program düzenli kapanıyor.")
        return Response({"durum": "kapaniyor"}, status=status.HTTP_202_ACCEPTED)


class SonOturumView(APIView):
    """`GET/POST /api/v1/dashboard/last-session/` — son oturum kartı (T15, §13 D4).

    GET kişisiz özeti döndürür (`unexpected_shutdown`, `process_started_at`); POST
    kartı bu oturum için kapatır ("Kontrol ettim") ve güncel özeti döndürür.
    Görevli kipinin izin listesinde değildir (varsayılan kapalı, `kip_izinleri`).
    """

    def get(self, request: Request) -> Response:
        return Response(son_oturum.ozet())

    def post(self, request: Request) -> Response:
        son_oturum.onayla()
        return Response(son_oturum.ozet())
