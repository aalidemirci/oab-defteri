"""Okul kartının eksiksiz, UYDURMA test verisi (F1b 4. adım; tasarım §5.1, plan F1b-4 kararları).

Kurulumu tamamlayan testler okul kartını buradan doldurur: zorunlu alanlar
(`services.setup.missing_school_fields`) değişince tek yer güncellenir. Ad ve kod uydurmadır;
gerçek bir okula ya da kişiye ait değildir.

- `TAM_OKUL_KARTI`: servis alanları (`setup.update_school_config(fields=…)`; tarihler `date`).
- `okul_karti_govdesi()`: aynı veri `PUT setup/school-config/` gövdesi olarak (tarihler ISO).
- `okul_kartini_dogrudan_yaz()`: hesapsız ortamda ORM ile (servis iz ister, tasarım §4.6.3).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from apps.okul.models import (
    CanteenMode,
    SchoolConfig,
    SchoolLevel,
    SettlementType,
    StaffingMode,
)

#: Eksiksiz okul kartı (servis biçimi). Müdür adı, kampüs ve açılış tarihi isteğe bağlıdır.
TAM_OKUL_KARTI: dict[str, Any] = {
    "school_name": "Örnek Anadolu Lisesi",
    "province": "Örnek İl",
    "district": "Örnek İlçe",
    "institution_code": "999001",
    "levels": [SchoolLevel.ORTAOGRETIM.value],
    "student_count": 1234,
    "student_count_as_of": date(2026, 10, 1),
    "settlement_type": SettlementType.BUYUKSEHIR.value,
    "canteen_mode": CanteenMode.KIRAYA_VERILIYOR.value,
    "staffing_mode": StaffingMode.HIZMET_ALIMI.value,
    "demirbas_onayi": True,
    "demirbas_no": "BLG-2026-017",
}


def okul_karti(**degisiklik: Any) -> dict[str, Any]:
    """`TAM_OKUL_KARTI`'nın değiştirilmiş kopyası (servis biçimi)."""
    return {**TAM_OKUL_KARTI, **degisiklik}


def okul_karti_govdesi(**degisiklik: Any) -> dict[str, Any]:
    """`PUT setup/school-config/` gövdesi: tarihler ISO metni (`YYYY-MM-DD`)."""
    return {
        ad: deger.isoformat() if isinstance(deger, date) else deger
        for ad, deger in okul_karti(**degisiklik).items()
    }


def okul_kartini_dogrudan_yaz(**degisiklik: Any) -> SchoolConfig:
    """Okul kartını ORM ile yazar (iz satırı yazılmaz; hesapsız ortamın test verisi)."""
    config: SchoolConfig
    config, _ = SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK, defaults=okul_karti(**degisiklik)
    )
    return config
