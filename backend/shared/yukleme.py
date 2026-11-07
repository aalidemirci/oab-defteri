"""Genel yükleme işleyicisi: yalnız bellek, sınırı aşan yükleme reddedilir (plan F1b-3).

Açık kopya kuralı (tasarım §4.4.7, §4.3 tehdit 15): içe aktarılan ham dosya sınıra kadar diske
yazılmadan bellekte okunur (gömülü sunucunun tamponu: `desktop/server.py`). Django'nun
`MemoryFileUploadHandler`'ı `FILE_UPLOAD_MAX_MEMORY_SIZE`'ı aşan isteği yalnız devre dışı bırakır:
başka işleyici yoksa dosya sessizce düşer, uçlar "dosya seçin" derdi. Burada istek Django'da
ayrıştırılmadan reddedilir (400, `{code, message, fields}`); sunucunun tampon eşiğini aşan gövde
bundan önce waitress'in sistem geçici dizinindeki dosyasına iner (Windows'ta istek süresince
adlıdır, kapanınca silinir), bu kalan risktir (plan F1b-3 "Dosya deposu"). Sınır isteğin boyuna
uygulanır, çok parçalı gövdenin birkaç yüz baytlık zarfı buna dahildir.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.files.uploadhandler import MemoryFileUploadHandler
from rest_framework.exceptions import ValidationError


class SinirliBellekIsleyicisi(MemoryFileUploadHandler):
    """Bellek işleyicisi; sınırı aşan istek `ValidationError`'dır (modül başlığı)."""

    def handle_raw_input(
        self,
        input_data: Any,
        META: dict[str, Any],  # noqa: N803 — Django'nun parametre adı
        content_length: int,
        boundary: str,
        encoding: str | None = None,
    ) -> None:
        if content_length > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            raise ValidationError(
                f"Dosya çok büyük; en çok {settings.MAX_UPLOAD_SIZE_MB} MB olabilir."
            )
        super().handle_raw_input(input_data, META, content_length, boundary, encoding)
