"""`okul` salt-okunur sorguları — view'lar ORM'e buradan erişir (katman disiplini).

Arama Türkçe-katlamalı yapılır: `normalize_header` (Türkçe→ASCII küçük harf) iki
tarafı da katlar. Ad-soyad ŞİFRELİDİR (tasarım §5.3): ada dokunan her arama ve
kullanıcıya gösterilen her sıralama ZORUNLU olarak Python tarafındadır — yeni
ad sorgusu ORM filtresiyle YAZILMAZ; yerel ölçek (≤2000 kayıt) bunu ucuzlatır.
Durum ve tür düz alanlardır; süzgeçleri DB tarafında kalır. (Öğrenci sicili ve şube
kataloğu seçicileri F1b 5. adımda öğrenci tarafıyla söküldü; tasarım §5.1 ALMA.)
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any

from django.db.models import QuerySet
from django.utils import timezone

from apps.okul import name_match, normalize
from apps.okul.excel_ortak import normalize_header
from apps.okul.models import (
    Holiday,
    HolidayKind,
    ImportRun,
    Personnel,
    SchoolTerm,
    SchoolYear,
)
from shared.crypto import has_corrupt


def school_years() -> QuerySet[SchoolYear]:
    return SchoolYear.objects.all()


def active_school_year() -> SchoolYear | None:
    return SchoolYear.objects.filter(is_active=True).first()


def school_terms(*, school_year_id: int) -> QuerySet[SchoolTerm]:
    return SchoolTerm.objects.filter(school_year_id=school_year_id)


def get_school_term(term_id: int) -> SchoolTerm | None:
    """Tek dönem (canlı) — yoksa None. Diğer uygulamaların dönem okuma kanalı."""
    return SchoolTerm.objects.filter(pk=term_id).select_related("school_year").first()


def _personnel_sort_key(person: Personnel) -> tuple[Any, ...]:
    """Ad-soyad Türk alfabesiyle ('C' < 'Ç', 'I' < 'İ'); eşitlikte kayıt sırası."""
    return (normalize.tr_sort_key(person.full_name), person.pk)


def personnel_sorted(
    rows: Iterable[Personnel] | None = None, *, only_active: bool = False
) -> list[Personnel]:
    """Ada göre Türk alfabesiyle sıralı personel (listeler, seçiciler).

    `rows` verilmezse canlı personelin tamamı (ya da yalnız aktifler) okunur.
    Ad şifreli olduğu için sıralama Python'dadır (DB sırası token sırasıdır).
    """
    if rows is None:
        rows = Personnel.objects.filter(is_active=True) if only_active else Personnel.objects.all()
    return sorted(rows, key=_personnel_sort_key)


def personnel_list(*, search: str = "", only_active: bool = False) -> list[Personnel]:
    """Personel listesi — ad araması ve sıralaması Python tarafında (şifreli ad).

    Unvan ve branş YOKTUR (tasarım §8.4); arama yalnız ad-soyad üzerindedir.
    """
    qs = Personnel.objects.all()
    if only_active:
        qs = qs.filter(is_active=True)
    rows: Iterable[Personnel] = qs
    if search.strip():
        needle = normalize_header(search)
        # Çözülemeyen adlı kayıt aramaya girmez (tasarım §13 D48): adın sağlam yarısı
        # yanlış kişiyi bulduruyordu.
        rows = [p for p in qs if not has_corrupt(p) and needle in normalize_header(p.full_name)]
    return personnel_sorted(rows)


def personnel_all() -> QuerySet[Personnel]:
    """Canlı personel (ayrıntı uçlarının `get_queryset`'i — tek kayıt çözümü)."""
    return Personnel.objects.all()


def get_personnel(personnel_id: int) -> Personnel | None:
    """Tek personel (canlı) — yoksa None."""
    return Personnel.objects.filter(pk=personnel_id).first()


# ---------------------------------------------------------------------------
# Ayrılış havuzu (aile iskeletinden — kişisel veri: yalnız yönetim yüzeyi, açık oturum)
# ---------------------------------------------------------------------------
def _pool_personnel_qs() -> QuerySet[Personnel]:
    return Personnel.objects.filter(is_active=True, leave_candidate_since__isnull=False)


def leave_pool_personnel() -> list[Personnel]:
    """Havuzdaki öğretmen ve diğer personel — ada göre Türk alfabesiyle (Python)."""
    return personnel_sorted(_pool_personnel_qs().select_related("leave_candidate_run"))


def leave_pool_counts() -> dict[str, int]:
    """Havuzdaki kişi sayıları (Genel Bakış kartı; kişisel veri yok)."""
    return {"personnel_count": _pool_personnel_qs().count()}


def leave_pool_run(person: Personnel) -> ImportRun | None:
    """Kişiyi havuza ekleyen aktarım (canlı değilse None — yumuşak silme ileri FK'da süzmez)."""
    run = person.leave_candidate_run
    if run is None or run.deleted_at is not None:
        return None
    return run


@dataclass(frozen=True)
class SimilarCandidate:
    """Havuzdaki kişiyle eşleşen aday + eşleşmenin GEREKÇESİ (tasarım §13 D30).

    `created_on` adayın sicile eklendiği gündür (yerel gün; UTC'den türetilmez):
    onay diyaloğunda iki kaydı ayırt eden bilgidir.
    """

    person: Personnel
    reason: name_match.MatchReason
    created_on: date


def leave_pool_similar_personnel(pool: Iterable[Personnel]) -> dict[int, list[SimilarCandidate]]:
    """Havuzdaki her personel için "olası aynı kişi" adayları (kimlik → adaylar, TR sıralı).

    Aday: aktif, havuzda OLMAYAN ve sicile kişinin havuza girdiği gün ya da sonra
    girmiş kayıt — tipik olarak aynı aktarımın yeni adla açtığı kayıt (soyadı
    değişimi). Eski kayıtlar aday sayılmaz: okulda aynı adı taşıyan başka
    öğretmenler her havuz kişisine "benzer" görünürdü. Kural aktarım
    önizlemesindekiyle aynıdır (`name_match.match_reason`) ve GEREKÇESİYLE
    birlikte taşınır: ekran adayın neden aday olduğunu yazar (§13 D30).
    """
    # Çözülemeyen adlı kayıt öneri üretmez ve aday olmaz (tasarım §13 D48).
    kisiler = [kisi for kisi in pool if not has_corrupt(kisi)]
    if not kisiler:
        return {}
    adaylar = personnel_sorted(
        aday
        for aday in Personnel.objects.filter(is_active=True, leave_candidate_since__isnull=True)
        if not has_corrupt(aday)
    )
    sonuc: dict[int, list[SimilarCandidate]] = {}
    for kisi in kisiler:
        giris = kisi.leave_candidate_since
        if giris is None:
            continue
        eslesenler: list[SimilarCandidate] = []
        for aday in adaylar:
            acilis = timezone.localdate(aday.created_at)
            if acilis < giris:
                continue
            gerekce = name_match.match_reason(
                first_a=kisi.first_name,
                full_a=kisi.full_name,
                first_b=aday.first_name,
                full_b=aday.full_name,
            )
            if gerekce is not None:
                eslesenler.append(SimilarCandidate(person=aday, reason=gerekce, created_on=acilis))
        sonuc[kisi.pk] = eslesenler
    return sonuc


def get_school_year(school_year_id: int) -> SchoolYear | None:
    """Tek ders yılı (canlı) — yoksa None."""
    return SchoolYear.objects.filter(pk=school_year_id).first()


def import_runs(*, source_type: str = "") -> QuerySet[ImportRun]:
    qs = ImportRun.objects.all()
    if source_type:
        qs = qs.filter(source_type=source_type)
    return qs


def personnel_count() -> int:
    """Canlı personel sayısı (kurulum durumu ve yol haritası; kişisel veri yok)."""
    return Personnel.objects.count()


# ---------------------------------------------------------------------------
# Kapalı günler (tasarım §5.1 `Holiday`; kişisel veri yok)
# ---------------------------------------------------------------------------


def holidays(*, year: int | None = None) -> QuerySet[Holiday]:
    """Canlı kapalı günler; `year` verilirse o takvim yılıyla KESİŞENLER (yıl sınırını
    aşan aralık iki yılda da görünür)."""
    qs = Holiday.objects.all()
    if year is not None:
        qs = qs.filter(start_date__lte=date(year, 12, 31), end_date__gte=date(year, 1, 1))
    return qs


def holidays_sorted(*, year: int | None = None) -> list[Holiday]:
    """Kullanıcıya gösterilen liste: tarih sırası, eşitlikte TR ad sırası."""
    return sorted(
        holidays(year=year),
        key=lambda h: (h.start_date, h.end_date, normalize.tr_sort_key(h.name)),
    )


def get_holiday(holiday_id: int) -> Holiday | None:
    return Holiday.objects.filter(pk=holiday_id).first()


def school_break_count(*, start: date | str | None, end: date | str | None) -> int:
    """[start, end] aralığıyla kesişen "öğrenciye kapalı gün" KAYDI sayısı.

    Yol haritasının "öğrenciye kapalı günleri girin" maddesi aktif ders yılının
    aralığıyla sorar. Aralık yoksa (aktif yıl yok) 0.
    """
    if start is None or end is None:
        return 0
    baslangic = date.fromisoformat(start) if isinstance(start, str) else start
    bitis = date.fromisoformat(end) if isinstance(end, str) else end
    return Holiday.objects.filter(
        kind=HolidayKind.SCHOOL_BREAK, start_date__lte=bitis, end_date__gte=baslangic
    ).count()
