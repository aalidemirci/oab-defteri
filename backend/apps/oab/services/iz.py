"""Yazar bağlamından `created_by`/`updated_by` kimliği (tasarım §5 O4)."""

from __future__ import annotations

import uuid

from apps.okul.oturum import yazar
from shared.exceptions import RolYetkisiz


def yazar_hesabi() -> uuid.UUID | None:
    """Yazarın hesap kimliği; `SISTEM` yazarında None (gün işi ve sistem işinin hesabı yoktur)."""
    kim = yazar()
    if kim is None or kim.hesap_id is None:
        return None
    return uuid.UUID(str(kim.hesap_id))


def hesap_zorunlu() -> uuid.UUID:
    """Yazar bir hesap olmalıdır (gerekçe ve yarım metin hesabın işidir); değilse ret."""
    kimlik = yazar_hesabi()
    if kimlik is None:
        raise RolYetkisiz
    return kimlik
