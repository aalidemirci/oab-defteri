"""`oab` salt okunur sorguları — görünümler ORM'e buradan erişir (katman disiplini).

Kişi adı ŞİFRELİDİR (tasarım §5.3): ada dokunan her arama ve kullanıcıya gösterilen her sıralama
Python'dadır (kaynak modülün `list_persons` işlevindeki `icontains` ve `order_by` şifreli adda
çalışmaz; UYARLA, tasarım §12.A). Tür ve durum düz alanlardır, süzgeçleri veritabanındadır.

Organ üyeliklerinin TEK KAYNAK listeleri (tasarım §5 O6, §12.A `organ_members`, `elected_roster`,
`candidate_roster`, `list_memberships` UYARLA): aday listesi, seçilenler, görev bölümü ve evrak aynı
seçiciden okur. Sıra yine Python'dadır: asıl önce, yedek sırası (boş önce), sonra çözülmüş ad.
"Görevdeki asıl" tek seçicidir: seçilmiş asıl ile yedekten çağrılan (`promoted_on`) yedek; `seat_type`
seçildiği koltuk olarak kalır (plan F1c kararları).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.db.models import Q, QuerySet

from apps.oab.models import (
    MembershipStatus,
    OabPerson,
    OabTerm,
    OrganMembership,
    PersonStatus,
    SeatType,
)
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


# ---------------------------------------------------------------------------
# Organ üyelikleri (tek kaynak; plan F1c-5)
# ---------------------------------------------------------------------------
_KOLTUK_SIRASI = {SeatType.ASIL: 0, SeatType.YEDEK: 1}


def _uyelik_sira_anahtari(uyelik: OrganMembership) -> tuple[Any, ...]:
    """Asıl önce; yedek sırası (boş önce, `nulls_first`, §12.A); çözülmüş ad; eşitlikte kayıt sırası."""
    sira = uyelik.seat_order
    return (
        _KOLTUK_SIRASI.get(SeatType(uyelik.seat_type), len(_KOLTUK_SIRASI)),
        sira is not None,
        sira or 0,
        *_kisi_sira_anahtari(uyelik.person),
        uyelik.pk,
    )


def memberships_sorted(rows: Iterable[OrganMembership]) -> list[OrganMembership]:
    return sorted(rows, key=_uyelik_sira_anahtari)


def _uyelikler(term: OabTerm, organ: str) -> QuerySet[OrganMembership]:
    return OrganMembership.objects.filter(term=term, organ=organ).select_related("person")


def membership_list(term: OabTerm, organ: str) -> list[OrganMembership]:
    """Bir dönem ve organdaki BÜTÜN üyelikler (aday, seçilmiş, düşmüş, iptal) — yönetim listesi."""
    return memberships_sorted(_uyelikler(term, organ))


def membership_all() -> QuerySet[OrganMembership]:
    """Bütün üyelikler (ayrıntı uçlarının tek kayıt çözümü)."""
    return OrganMembership.objects.select_related("person", "term")


def organ_members(
    term: OabTerm, organ: str, *, status: str, seat_type: str
) -> list[OrganMembership]:
    """Bir dönem, organ, durum ve koltuktaki üyeler (aday listesi `ADAY`, seçilenler `SECILDI`)."""
    return memberships_sorted(_uyelikler(term, organ).filter(status=status, seat_type=seat_type))


def elected_roster(term: OabTerm, organ: str) -> dict[str, list[OrganMembership]]:
    """Seçilenler, seçildikleri koltuğa göre (asıl ve yedek; tutanak ve B-12 dökümü)."""
    return {
        "asil": organ_members(
            term, organ, status=MembershipStatus.SECILDI, seat_type=SeatType.ASIL
        ),
        "yedek": organ_members(
            term, organ, status=MembershipStatus.SECILDI, seat_type=SeatType.YEDEK
        ),
    }


def candidate_roster(term: OabTerm, organ: str) -> dict[str, list[OrganMembership]]:
    """Adaylar, aday oldukları koltuğa göre (aday listeleri)."""
    return {
        "asil": organ_members(term, organ, status=MembershipStatus.ADAY, seat_type=SeatType.ASIL),
        "yedek": organ_members(term, organ, status=MembershipStatus.ADAY, seat_type=SeatType.YEDEK),
    }


#: Görevdeki asıl koşulu (tek tanım): seçildiği koltuk asıl ya da yedekten çağrılmış. Kayıt üstündeki
#: karşılığı `gorevdeki_asil_mi`'dir; servisler (görev tekilliği, kurul katılımı) bu ikisini kullanır.
GOREVDEKI_ASIL = Q(seat_type=SeatType.ASIL) | Q(promoted_on__isnull=False)
_BEKLEYEN_YEDEK = Q(seat_type=SeatType.YEDEK, promoted_on__isnull=True)


def gorevdeki_asil_mi(uyelik: OrganMembership) -> bool:
    """`GOREVDEKI_ASIL` koşulunun tek kayıt üstündeki karşılığı (durumuna bakmaz)."""
    return uyelik.seat_type == SeatType.ASIL or uyelik.promoted_on is not None


def gorevdeki_asillar(term: OabTerm, organ: str) -> list[OrganMembership]:
    """Görevdeki asıllar: seçilmiş asıl ve yedekten çağrılan yedek (tek seçici)."""
    return memberships_sorted(
        _uyelikler(term, organ).filter(GOREVDEKI_ASIL, status=MembershipStatus.SECILDI)
    )


def bekleyen_yedekler(term: OabTerm, organ: str) -> list[OrganMembership]:
    """Çağrılmamış seçilmiş yedekler; yedek sırasıyla."""
    return memberships_sorted(
        _uyelikler(term, organ).filter(_BEKLEYEN_YEDEK, status=MembershipStatus.SECILDI)
    )


def kadro_sayilari(term: OabTerm, organ: str) -> dict[str, int]:
    """Kadro sayımı yalnız seçilmiş kayıtları sayar (aday sayılmaz, düşen koltuk sayılmaz).

    Sayılan kişidir, kayıt değil (md. 12/1, 14/1 "beş asıl", "üç asıl" üye). Aynı kişinin aynı
    kurulda ikinci seçilmiş koltuğu yazılmaz (tek koltuk, sert; `uyelikler._ikinci_koltuk`); sayım
    yine kişiyi sayar: servis dışı yazılmış ikinci koltuk kadroyu tamamlamaz, eksik kadro uyarısı çıkar.
    """
    secilmis = OrganMembership.objects.filter(
        term=term, organ=organ, status=MembershipStatus.SECILDI
    )

    def kisi_sayisi(kosul: Q) -> int:
        return secilmis.filter(kosul).order_by().values("person").distinct().count()

    return {
        SeatType.ASIL: kisi_sayisi(GOREVDEKI_ASIL),
        SeatType.YEDEK: kisi_sayisi(_BEKLEYEN_YEDEK),
    }
