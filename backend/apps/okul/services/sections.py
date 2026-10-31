"""Şube kataloğu (ClassSection) yazma işlemleri.

İnce servis katmanı — doğrulama serializer'da (seviye kümesi, şube katlaması,
mükerrer denetimi), yazma burada. Toplu tohum `imports._ensure_class_sections`.

SİLME ENGELİ KAYIT DEFTERİ (aile iskeletinden). Şube silmesi yumuşak silmedir;
`PROTECT` yumuşak silmede tetiklenmez (Django'nun `on_delete` kuralı yalnız
gerçek DELETE'te çalışır). Başka bir uygulamanın şubeye bağlı açık kaydı varsa
silme gerekçeyle reddedilir; bugün kayıtlı denetim yoktur (şube kataloğu OAB'ye
alınmaz, T5 ile F1b'de sökülür — tasarım §5.1).
Bağımlılık yönü <uygulama> → okul'dur (`services.persons` kalıbı): uygulama kendi
denetimini `AppConfig.ready` içinde `register_delete_check` ile kaydeder.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.okul.models import ClassSection

type SectionDeleteCheck = Callable[[ClassSection], Iterable[str]]

_delete_checks: list[SectionDeleteCheck] = []


def register_delete_check(fn: SectionDeleteCheck) -> None:
    """Silme engeli denetimi: `fn(şube)` Türkçe gerekçe listesi döner (fikirdeş kayıt)."""
    if fn not in _delete_checks:
        _delete_checks.append(fn)


def delete_obstacles(section: ClassSection) -> list[str]:
    """Şubenin silinmesini engelleyen gerekçeler (tekilleştirilmiş, kayıt sırasıyla)."""
    gerekceler: list[str] = []
    for check in _delete_checks:
        gerekceler.extend(check(section))
    return list(dict.fromkeys(g for g in gerekceler if g))


@transaction.atomic
def create_class_section(**fields: Any) -> ClassSection:
    section: ClassSection = ClassSection.objects.create(**fields)
    return section


@transaction.atomic
def delete_class_section(section: ClassSection) -> None:
    """Şubeyi yumuşak siler; bağlı açık kaydı varsa gerekçeyle reddeder (400)."""
    gerekceler = delete_obstacles(section)
    if gerekceler:
        raise ValidationError("Şube silinemez: " + " ".join(gerekceler))
    section.delete()  # soft delete (BaseModel)
