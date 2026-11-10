"""`oab` salt okunur sorguları — görünümler ORM'e buradan erişir (katman disiplini).

Kişi adı ŞİFRELİDİR (tasarım §5.3): ada dokunan her arama ve kullanıcıya gösterilen her sıralama
Python'dadır (OYS `list_persons`'ın `icontains` ve `order_by`'ı şifreli adda çalışmaz; UYARLA).
Tür ve durum düz alanlardır, süzgeçleri veritabanındadır.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.db.models import QuerySet

from apps.oab.models import OabPerson, PersonStatus
from apps.okul import normalize
from apps.okul.excel_ortak import normalize_header
from shared.crypto import has_corrupt


def _kisi_sira_anahtari(kisi: OabPerson) -> tuple[Any, ...]:
    """Ad-soyad Türk alfabesiyle ('C' < 'Ç', 'I' < 'İ'); eşitlikte kayıt sırası."""
    return (normalize.tr_sort_key(kisi.full_name), kisi.pk)


def persons_sorted(rows: Iterable[OabPerson]) -> list[OabPerson]:
    """Ada göre Türk alfabesiyle sıralı birlik kişileri."""
    return sorted(rows, key=_kisi_sira_anahtari)


def person_list(*, search: str = "", only_active: bool = False) -> list[OabPerson]:
    """Birlik kişileri — ad araması ve sıralaması Python'da; çözülemeyen adlı kayıt aramaya girmez."""
    qs = OabPerson.objects.all()
    if only_active:
        qs = qs.filter(status=PersonStatus.AKTIF)
    rows: Iterable[OabPerson] = qs
    if search.strip():
        needle = normalize_header(search)
        rows = [k for k in qs if not has_corrupt(k) and needle in normalize_header(k.full_name)]
    return persons_sorted(rows)


def person_all() -> QuerySet[OabPerson]:
    """Bütün birlik kişileri (ayrıntı uçlarının tek kayıt çözümü)."""
    return OabPerson.objects.all()
