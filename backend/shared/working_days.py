"""Kapalı gün aritmetiği — takvime bağlı süre hesaplarının ortak çekirdeği (tasarım §5.1).

Aile iskeletinden AYNEN alındı (tasarım §12.B; `SCHOOL_BREAK` ve `next_open_day`
iskeletin kendi uyarlamasıdır). Modül yalnız
takvim aritmetiğidir: bir gün kapalı mı, kapalıysa izleyen ilk açık gün hangisi.
Bir sürenin nasıl sayılacağı (gün mü, iş günü mü, son gün kayar mı) bu modülün
işi DEĞİLDİR; süreyi koyan kural paketinin maddesi söyler (CLAUDE.md §2 altın
kural 1-2). OAB'de bu çekirdeğe dayanacak iş günü süreleri tasarım §5.1
(`Holiday` satırı) ve kural paketinin süre kurallarındadır (§6.4.5, §6.4.9); bugün
`is_closed_day` ile `next_open_day`'i üretim kodunda çağıran yoktur.

İKİ AYRI KAPALI GÜN KURALI (bu ayrım kullanıcı metnine de yansır):

1. **Hafta sonu, resmî tatil, dini bayram, idari izin — her zaman kapalı.**
   İdari izin (`OTHER`) de aynı DAVRANIŞA (her zaman kapalı) bağlandı; günün
   hukuki niteliği hakkında program hüküm koymaz. Bu, programın kuralıdır, mevzuat
   dayanağı değildir: kullanıcı metninde mevzuat gereği diye sunulmaz
   (tasarım §3.3).
2. **Öğrenciye kapalı gün (ara tatil, yarıyıl — `SCHOOL_BREAK`) — bayrakla.**
   Hesaba girip girmeyeceğini çağıran, yani süreyi koyan kural seçer
   (`include_school_breaks`). Bu günlerin hukuki niteliği hakkında program hüküm
   koymaz (dayanağı korpusta yok; CLAUDE.md §2 altın kural 1).

Katman: çekirdek (`*_in` işlevleri) ORM'sizdir, kapalı dönemleri parametre alır ve
saf birim testiyle sınanır. Sözleşme işlevleri (`is_closed_day`, `next_open_day`)
dönem verilmezse `apps.okul.services.calendar.closed_periods_from` ile DB'den okur;
içe aktarma TEMBELDİR — `shared` açılışta `apps`'e bağlanmaz.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

# 5=Cumartesi, 6=Pazar (`date.weekday()`).
_WEEKEND = frozenset({5, 6})
_ONE_DAY = timedelta(days=1)


@dataclass(frozen=True, slots=True)
class ClosedPeriod:
    """Kapsayıcı kapalı dönem [start, end]; `school_break` → öğrenciye kapalı gün."""

    start: date
    end: date
    school_break: bool = False

    def covers(self, day: date) -> bool:
        return self.start <= day <= self.end


def is_weekend(day: date) -> bool:
    return day.weekday() in _WEEKEND


def _applicable(
    periods: Iterable[ClosedPeriod], *, include_school_breaks: bool
) -> list[ClosedPeriod]:
    """Kurala giren dönemler: öğrenciye kapalı günler yalnız bayrak açıkken."""
    return [p for p in periods if include_school_breaks or not p.school_break]


def is_closed_day_in(
    day: date, periods: Iterable[ClosedPeriod], *, include_school_breaks: bool
) -> bool:
    """Saf çekirdek: `day` hafta sonu mu ya da kurala giren bir dönemin içinde mi?"""
    if is_weekend(day):
        return True
    return any(
        p.covers(day) for p in _applicable(periods, include_school_breaks=include_school_breaks)
    )


def next_open_day_in(
    day: date, periods: Iterable[ClosedPeriod], *, include_school_breaks: bool = True
) -> date:
    """Saf çekirdek: `day` açıksa kendisi, değilse izleyen ilk açık gün.

    Kapalı aralıklar gün gün değil, kapsayan dönemlerin en geç bitişinin ertesine
    atlanarak geçilir. Dönem kümesi sonlu olduğundan döngü biter: her adım tarihi
    ileri taşır ve son dönemin bitişinden sonra yalnız hafta sonları kalır.
    """
    applicable = _applicable(periods, include_school_breaks=include_school_breaks)
    current = day
    while True:
        if is_weekend(current):
            current += _ONE_DAY
            continue
        covering = [p.end for p in applicable if p.covers(current)]
        if not covering:
            return current
        current = max(covering) + _ONE_DAY


def _periods_from_db(day: date) -> list[ClosedPeriod]:
    # Tembel içe aktarma: bkz. modül yorumu (katman).
    from apps.okul.services.calendar import closed_periods_from

    return closed_periods_from(day)


def is_closed_day(
    day: date,
    *,
    include_school_breaks: bool,
    periods: Iterable[ClosedPeriod] | None = None,
) -> bool:
    """`day` kapalı gün mü? Hafta sonu + resmî/dini tatil + idari izin daima;
    öğrenciye kapalı gün yalnız `include_school_breaks` ile.

    `periods` verilmezse canlı kapalı gün kayıtları DB'den okunur.
    """
    source = _periods_from_db(day) if periods is None else periods
    return is_closed_day_in(day, source, include_school_breaks=include_school_breaks)


def next_open_day(
    day: date,
    *,
    include_school_breaks: bool = True,
    periods: Iterable[ClosedPeriod] | None = None,
) -> date:
    """`day` açıksa kendisi; değilse izleyen ilk açık gün.

    `periods` verilmezse canlı kapalı gün kayıtları DB'den okunur.
    """
    source = _periods_from_db(day) if periods is None else periods
    return next_open_day_in(day, source, include_school_breaks=include_school_breaks)
