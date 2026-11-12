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
        kurallarla bağlanır (`services.hesaplar`, plan F1c 7. adım); kurulum durumu ve yol haritası geçiş
        kurulumunun durumunu buradan okur (`services.setup`, plan F1c 8. adım); üretilen evrak dosya
        deposunun sahibidir (PDF ve DOCX) ve okul çekirdeğinin evrakı (E63) buradan kaydedilir
        (`services.dosya_deposu`, `services.evrak_kaydi`; plan F1c 9. adım). Kayıtlar idempotenttir.
        """
        from apps.oab.kurallar import yukleyici
        from apps.oab.models import GeneratedDocument
        from apps.oab.services import donemler, evrak, gecis, hesap_baglari, kisiler
        from apps.okul.services import (
            dosya_deposu,
            evrak_kaydi,
            hesaplar,
            imports,
            persons,
            setup,
        )

        yukleyici.ac()
        persons.register_membership_check(kisiler.personnel_linked)
        persons.register_merge_hook(kisiler.personnel_merged)
        imports.register_roster_term_provider(donemler.acik_donem_kimligi)
        hesaplar.register_account_bond_rules(hesap_baglari.KURALLAR)
        setup.register_transition_status(gecis.yol_haritasi_durumu)
        dosya_deposu.sahip_kaydet(GeneratedDocument, uretilen_evrak=True)
        evrak_kaydi.register_document_recorder(evrak.okul_evraki_kaydet)
