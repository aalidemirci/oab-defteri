"""Okul çekirdeği uygulama tanımı.

`ready()` bu sürecin başlangıcını işaretler (T15, tasarım §13 D4): beklenmedik
kapanıştan sonra panodaki "son oturumdaki kayıtları kontrol edin" kartı
(`apps.okul.son_oturum`) bu damgayı "son oturum"un üst sınırı sayar.
"""

from __future__ import annotations

from django.apps import AppConfig


class OkulConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.okul"
    verbose_name = "Okul çekirdeği"

    def ready(self) -> None:
        from apps.okul import son_oturum

        # T15: bu oturumun başlangıcı — "son oturumdaki kayıtlar" bundan öncekilerdir.
        son_oturum.mark_process_start()
