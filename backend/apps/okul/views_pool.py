"""Ayrılış havuzu uçları (tasarım §5.1 `Personnel`, §13 D30) — İNCE görünümler.

Aile iskeletinin kullanıcı kararı (22.09.2026): e-Okul aktarımı kimseyi ayırmaz ve silmez;
listede bulunmayan aktif kişi ayrılış havuzuna girer, karar burada verilir.

- `GET leave-pool/` — havuzdaki öğretmen ve diğer personel, TR sıralı, adlarla
  (yönetim yüzeyi). `?summary=true` yalnız sayıyı döner (Genel Bakış kartı; kişisel veri
  yok). Kişi YAZMAZ.
- `POST leave-pool/resolve/` — toplu karar: `{personnel: {leave, keep}}`. Kişi yazar →
  `RequiresAdminPassword` (parola kurulmadan 409 `parola_gerekli`).

Havuz yalnız personeli taşır: öğrenci sicili F1b 5. adımda söküldü (tasarım §5.1 ALMA);
veli listesi havuz kullanmaz, sınıf bazında yerine konur (tasarım §8.4).

Karar program yöneticisinin işidir: havuz (özet dahil) ve karar yalnız program
yöneticisine açıktır (tasarım §8.1 A7; `rol_izinleri.KURALLAR`, plan F1b-2).
"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.okul import selectors
from apps.okul.permissions import RequiresAdminPassword
from apps.okul.serializers import LeavePoolPersonnelSerializer, LeavePoolResolveSerializer
from apps.okul.services import persons as persons_service

_TRUE_VALUES = frozenset({"true", "1"})


class LeavePoolView(APIView):
    """`GET leave-pool/` — ayrılış kararı bekleyen kişiler (ya da `?summary=true` sayılar)."""

    def get(self, request: Request) -> Response:
        if request.query_params.get("summary", "").strip().lower() in _TRUE_VALUES:
            return Response(selectors.leave_pool_counts())
        personel = selectors.leave_pool_personnel()
        benzerler = selectors.leave_pool_similar_personnel(personel)
        return Response(
            {
                "personnel_count": len(personel),
                "personnel": LeavePoolPersonnelSerializer(
                    personel, many=True, context={"similar": benzerler}
                ).data,
            }
        )


class LeavePoolResolveView(APIView):
    """`POST leave-pool/resolve/` — "Ayrıldı olarak işaretle" / "Aktif kalsın" (tek işlem).

    Yanıt: uygulanan sayılar + havuzda kalan sayılar. Seçilen kişi artık havuzda
    değilse hiçbir karar uygulanmaz (400, liste yenilenmeli).
    """

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request) -> Response:
        req = LeavePoolResolveSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        personel = req.validated_data.get("personnel") or {}
        sonuc = persons_service.resolve_leave_pool(
            personnel=persons_service.PoolDecision(
                leave=tuple(personel.get("leave", ())), keep=tuple(personel.get("keep", ()))
            ),
        )
        return Response({**sonuc, **selectors.leave_pool_counts()})
