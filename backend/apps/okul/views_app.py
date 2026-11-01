"""Program uçları — `POST app/quit/`: arayüzden düzenli çıkış (tasarım §4.2 "Kapanış").

Pencerenin çarpısı programı kapatır (T6, tasarım §4.5); tepsi yoktur. Düzenli
kapanış ayrıca tek kopya kanalının `kapat` komutundan (kurucu), Linux'ta oturum
kapanışından (SIGTERM) ve bu uçtan gelir. Uç, pencere süslemesi olmayan Linux
masaüstünün çıkış yoludur (tasarım §4.5).

Çık **her oturum durumunda parolasızdır** (tasarım §4.2, §4.5; plan F1b-1 "Oturum"):
açık oturumda (her rolde), kilitliyken, kurulumda, güvenlik dosyası kayıpken ve
geri yüklemeden sonra. Aile iskeletinin görevli kipindeki parola dalı görevli kipiyle
birlikte söküldü. Kilit kapısı ve yeniden başlat kapısı bu yolu geçirir
(`lock_middleware`, `restart_gate`): kilitliyken de programdan çıkılabilmelidir.
Oturum açıksa kapanış sırasında kilitlenir (`oturum.kapanista_kilitle`, masaüstü
kabuğu çağırır; §4.2 kapanış sırası).

Başarıda 202 döner ve kapanış masaüstü kancasıyla (`masaustu_kanca.cikis_iste`)
AYRI bir iş parçacığında başlar: yanıt önce gönderilir, sonra pencere, oturum kilidi,
yönetim sunucusu ve WAL checkpoint sırasıyla kapanır (`desktop/main.py`). Kanca
yoksa (geliştirme sunucusu) 503 `cikis_kullanilamiyor`.
"""

from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.okul import masaustu_kanca, son_oturum

logger = logging.getLogger("oab_defteri.cikis")

CIKIS_KULLANILAMIYOR = (
    "Program masaüstü penceresinde çalışmıyor; bu ortamda arayüzden çıkış yapılamaz."
)


def _hata(kod: str, ileti: str, durum_kodu: int) -> Response:
    return Response({"code": kod, "message": ileti, "fields": {}}, status=durum_kodu)


class AppQuitView(APIView):
    """`POST /api/v1/app/quit/` — düzenli kapanışı başlatır (parolasız; modül başlığı)."""

    def post(self, request: Request) -> Response:
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
    """

    def get(self, request: Request) -> Response:
        return Response(son_oturum.ozet())

    def post(self, request: Request) -> Response:
        son_oturum.onayla()
        return Response(son_oturum.ozet())
