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


class DonemKopyasiDogrulanamadi(KuralPaketiKullanilamaz):
    """Dönemin dondurulmuş kopyası kanonik özetini tutmuyor (D7): kurallar o kopyadan okunmaz.

    `KuralPaketiKullanilamaz`'ın alt türüdür: paket yokken okuması açık kalan yollar (öneriler, uyarılar,
    çizelge) bozuk kopyada da yanlış değer göstermeden boş döner; yazma zaten `donem_salt_okur`'dur
    (plan F1c 3. adım notları: kopya okuması dönemli okuma ekranıyla sertleştirildi).
    """

    default_code = "donem_kopyasi_dogrulanamadi"
    default_detail = (
        "Bu birlik döneminin kural kopyası doğrulanamadığı için kurallar okunamıyor. Yedekten geri "
        "yükleme için program yöneticisine başvurun."
    )


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
