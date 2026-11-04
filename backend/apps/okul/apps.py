"""Okul çekirdeği uygulama tanımı.

`ready()`:

* bu sürecin başlangıcını işaretler (T15, tasarım §13 D4): beklenmedik kapanıştan
  sonra panodaki "son oturumdaki kayıtları kontrol edin" kartı (`apps.okul.son_oturum`)
  bu damgayı "son oturum"un üst sınırı sayar;
* oturumun kapanış kilidini masaüstü kancasına kaydeder (tasarım §4.2 kapanış sırası:
  `od-gunluk` durur → oturum açıksa kilitlenir → yönetim sunucusu);
* erişim günlüğünün saklama süresi silmesini gün işi olarak kaydeder (tasarım §4.6.4, TK19;
  `apps.okul.erisim_gunlugu`): masaüstünün `od-gunluk` kapısı listeyi açılışta okur;
* `SchoolConfig` kaydedilince boşta kilit süresinin önbelleğini boşaltır (TK14): ayar
  değişikliği yeniden başlatma istemez.
"""

from __future__ import annotations

from django.apps import AppConfig


class OkulConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.okul"
    verbose_name = "Okul çekirdeği"

    def ready(self) -> None:
        from django.db.models.signals import post_save

        from apps.okul import erisim_gunlugu, masaustu_kanca, oturum, son_oturum
        from apps.okul.models import SchoolConfig

        # T15: bu oturumun başlangıcı — "son oturumdaki kayıtlar" bundan öncekilerdir.
        son_oturum.mark_process_start()
        masaustu_kanca.kapanis_kilidi_kaydet(oturum.kapanista_kilitle)
        erisim_gunlugu.gun_isini_kaydet()
        post_save.connect(
            oturum.bosta_suresi_onbellegini_bosalt,
            sender=SchoolConfig,
            dispatch_uid="oab_defteri.okul.bosta_suresi",
        )
