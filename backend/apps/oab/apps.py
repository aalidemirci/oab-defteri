"""Okul-aile birliği uygulaması (plan F1c; tasarım §5.2).

Bağımlılık yönü `oab`'den `okul`'adır: `okul` ve `shared` bu uygulamayı Python düzeyinde içe
aktarmaz, `okul`'dan `oab`'ye giden yabancı anahtarlar dizeyle verilir (plan "F1c adımları"; bekçisi
`apps/oab/tests/test_iskelet.py`).
"""

from __future__ import annotations

from django.apps import AppConfig


class OabConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.oab"
    verbose_name = "Okul-aile birliği"

    def ready(self) -> None:
        """Açılış denetimleri (tasarım §6.3 D1, D2, D5, D7): hata yükseltmez, program açılır."""
        from apps.oab.kurallar import yukleyici

        yukleyici.ac()
