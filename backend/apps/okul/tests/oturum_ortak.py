"""Oturum testlerinin ortak yardımcıları (toplanmaz: dosya adı `test_` ile başlamaz).

Aile iskeletinin kip testlerinden kalan iki yardımcı (`SahteSaat`,
`kurulum_durumunu_yaz`) ve oturumun boşta süresini sınayan testlerin kısayolları.
"""

from __future__ import annotations

from collections.abc import Callable

from apps.okul.models import SchoolConfig
from apps.okul.oturum import OTURUM


def kurulum_durumunu_yaz(*, tamam: bool) -> None:
    """`SchoolConfig.setup_completed`'ı doğrudan yazar (DB gerekir).

    Kurulum bitene kadar boşta süre oturumu kilitlemez (tasarım §13 D15); boşta kilit
    testleri (§4.4.3) kurulumu tamamlanmış ortamda koşar, kurulum sırasındaki
    davranış ayrı testlerdedir. Sihirbaz kapısı (`setup/complete/`) burada atlanır:
    oturum testleri yalnız bayrağı okur.
    """
    config, _ = SchoolConfig.objects.get_or_create(pk=SchoolConfig.SINGLETON_PK)
    config.setup_completed = tamam
    config.save(update_fields=["setup_completed", "updated_at"])


class SahteSaat:
    """Enjekte edilebilir monoton saat: `ilerlet()` ile zaman elle ilerler."""

    def __init__(self, baslangic: float = 10_000.0) -> None:
        self.simdi = baslangic

    def __call__(self) -> float:
        return self.simdi

    def ilerlet(self, saniye: float) -> None:
        self.simdi += saniye


def oturum_saatini_kur(saat: Callable[[], float]) -> None:
    """Süreç içi oturum nesnesinin saatini sahtesiyle değiştirir; açık oturum korunur.

    `_reset_for_tests` oturumu kapatır (hesap düşer); burada yalnız saat değişir ve
    boşta sayacı sahte saatin şimdisinden başlar.
    """
    with OTURUM._kilit:
        OTURUM._saat = saat
        OTURUM._son_etkinlik = saat()
