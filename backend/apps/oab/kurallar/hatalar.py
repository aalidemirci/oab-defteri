"""Kural motorunun hataları (tasarım §6.1 "Erişim", §6.3 D1).

İlk üçü işlemi durdurur (fail-closed). `APIException` oldukları için servis zincirinden görünüme
kadar yutulmadan gelir, `{code, message, fields}` gövdesiyle dönerler; ileti iç ayrıntı taşımaz
(kural kimliği günlüğe düşer).
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import APIException


class KuralPaketiKullanilamaz(APIException):
    """Paket açılış denetimlerinden geçemedi: yeni bağlama ve yazma kapalı, dönem kopyası okunur (D1)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "kural_paketi_yok"
    default_detail = "Kural paketi okunamadığı için bu işlem yapılamıyor. Programı yeniden kurun."


class BilinmeyenKural(APIException):
    """Koddaki kimlik pakette yok: programlama hatası (D6 yakalar), çalışma anında yazma kapalı."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = "bilinmeyen_kural"
    default_detail = "Bu işlemin dayandığı kural bulunamadığı için işlem yapılmadı."


class OlayTarihiGerekli(APIException):
    """Dönem kuralı olay gününe bakar (tasarım §6.1 MA-12): işlem anıyla sessizce hesaplanmaz."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = "olay_tarihi_gerekli"
    default_detail = "Bu işlemin olay tarihi belirlenemediği için işlem yapılmadı."


class YururlukteDegerYok(ValueError):
    """Olay tarihinde yürürlükte değer yok: `kural` değer veremez, `denetle` `denetlenmedi` döner."""
