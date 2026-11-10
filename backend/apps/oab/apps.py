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
        """Açılış denetimleri (tasarım §6.3 D1, D2, D5, D7) ve `okul` kayıt defterleri.

        Denetimler hata yükseltmez, program açılır. Kancalar (plan F1c-4): birlik kişisine bağlı
        personel silinmez, birleştirmede bağ taşınır (`services.persons`); veli listesi aktarımı açık
        birlik dönemini buradan öğrenir (`services.imports`); organ rollerinin hesabı üyeliğe bu
        kurallarla bağlanır (`services.hesaplar`, plan F1c 7. adım). Kayıtlar idempotenttir.
        """
        from apps.oab.kurallar import yukleyici
        from apps.oab.services import donemler, hesap_baglari, kisiler
        from apps.okul.services import hesaplar, imports, persons

        yukleyici.ac()
        persons.register_membership_check(kisiler.personnel_linked)
        persons.register_merge_hook(kisiler.personnel_merged)
        imports.register_roster_term_provider(donemler.acik_donem_kimligi)
        hesaplar.register_account_bond_rules(hesap_baglari.KURALLAR)
