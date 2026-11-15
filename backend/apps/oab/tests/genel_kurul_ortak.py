"""Genel kurul akışı testlerinin ortak kurulumu (F2 4. adım; `gk`, `ak` ve akış testleri).

Kapanacak dönem geçiş kurulumuyla 2025-2026 ders yılında açılır; olağan genel kurul 2026-2027 ders
yılının Ekim'inde toplanır (hazırlık döneminin ders yılı birinci toplantının günüdür, U5). Saatler
Europe/Istanbul'dadır. Okul kartındaki öğrenci mevcudu 120: yeter sayı 16 × 4 = 64. Kişi ve hesap
adları UYDURMADIR.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from io import BytesIO

from django.utils import timezone
from openpyxl import Workbook

from apps.oab.models import AgendaItem, AssemblyCaller, AssemblyKind, GeneralAssembly, OabTerm
from apps.oab.services import donemler, uyum
from apps.oab.services import genel_kurul as gk
from apps.oab.tests import uyelik_ortak as o
from apps.okul.models import AccountRole, SchoolConfig, SchoolYear
from apps.okul.services import imports as import_service
from apps.okul.services.templates import PARENT_TEMPLATE_HEADERS

#: Kapanacak dönemin başı (geçiş kurulumu).
DONEM_BASI = date(2025, 11, 3)
#: Okul kartındaki mevcudun alındığı gün.
MEVCUT_GUNU = date(2026, 9, 15)
#: Olağan genel kurulun birinci toplantısı (Ekim sonundan önce).
BIRINCI_GUN = date(2026, 10, 20)
#: Birinci toplantıdan 15 gün önce (üç kanalın ilan günü).
ILAN_GUNU = date(2026, 10, 5)

GEREKCE = uyum.Gerekce(metin="Uydurma gerekçe: okul idaresinin yazısıyla kayda geçti.")
#: Olağan çağrının yönetim kurulu kararı bağı akış satırının gerekçesi (kullanıcı kararı S1).
KARAR_GEREKCESI = uyum.Gerekce(
    metin="Uydurma gerekçe: yönetim kurulu kararı defterde; bilgisi sonra girilecek."
)
#: Olağanüstü genel kurulun uydurma çağrı nedeni ve gündemi.
OLAGANUSTU_NEDEN = "Uydurma neden: yönetim kurulunda boşalan koltuklar."
OLAGANUSTU_GUNDEM = (
    gk.GundemMaddesi(title="Açılış ve yoklama", kind="ACILIS"),
    gk.GundemMaddesi(title="Yönetim kurulu asıl ve yedek üye seçimi", kind="SECIM_YK"),
)


def an(gun: date, saat: int = 10, dakika: int = 0) -> datetime:
    """Europe/Istanbul'da yerel an."""
    return datetime(
        gun.year, gun.month, gun.day, saat, dakika, tzinfo=timezone.get_current_timezone()
    )


def ders_yillari() -> tuple[SchoolYear, SchoolYear]:
    """2025-2026 (kapanacak dönem) ve 2026-2027 (genel kurul ve hazırlık dönemi) ders yılları."""
    once = SchoolYear.objects.create(
        name="2025-2026", start_date=date(2025, 9, 8), end_date=date(2026, 6, 26)
    )
    sonra = SchoolYear.objects.create(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), is_active=True
    )
    return once, sonra


def mevcut(sayi: int | None = 120) -> None:
    """Okul kartındaki öğrenci mevcudu (yeter sayının girdisi)."""
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK,
        defaults={
            "student_count": sayi,
            "student_count_as_of": None if sayi is None else MEVCUT_GUNU,
        },
    )


def acik_donem(ogrenci: int | None = 120) -> OabTerm:
    """Kapanacak (açık) birlik dönemi ve okul kartının mevcudu."""
    once, _ = ders_yillari()
    mevcut(ogrenci)
    return donemler.create_term(
        name="2025-2026 birlik dönemi", school_year=once, start_date=DONEM_BASI
    )


def planla(
    kind: str = AssemblyKind.OLAGAN,
    birinci: datetime | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> GeneralAssembly:
    """Program yöneticisinin planlaması (varsayılan yazar)."""
    return gk.planla(kind=kind, first_meeting_at=birinci or an(BIRINCI_GUN), gerekce=gerekce).kurul


def olagan_cagir(kurul: GeneralAssembly) -> GeneralAssembly:
    """Olağan genel kurulu yönetim kurulu adına sekreter çağırır (karar bağı gerekçesiyle)."""
    with o.rol_olarak(AccountRole.SEKRETER):
        return gk.cagir(kurul, gerekce=KARAR_GEREKCESI).kurul


def olaganustu_cagir(kurul: GeneralAssembly) -> GeneralAssembly:
    """Olağanüstü genel kurulu yönetim kurulu adına sekreter çağırır."""
    with o.rol_olarak(AccountRole.SEKRETER):
        return gk.cagir(
            kurul,
            called_by=AssemblyCaller.YONETIM_KURULU,
            call_reason=OLAGANUSTU_NEDEN,
            gundem=OLAGANUSTU_GUNDEM,
        ).kurul


def kanallar(gun: date = ILAN_GUNU) -> gk.IlanKanallari:
    """Üç kanalın da aynı gün kanıtı."""
    return gk.IlanKanallari(distributed_written_on=gun, posted_board_on=gun, published_web_on=gun)


def cagrilmis_olagan(birinci: datetime | None = None) -> GeneralAssembly:
    """Açık dönem, planlanmış ve çağrılmış olağan genel kurul."""
    acik_donem()
    return olagan_cagir(planla(birinci=birinci))


def ilanli_olagan(second_meeting_at: datetime | None = None) -> GeneralAssembly:
    """İlan edilmiş olağan genel kurul (15 gün, üç kanal; yeter sayı 64)."""
    kurul = cagrilmis_olagan()
    return gk.ilan_et(kurul, kanallar=kanallar(), second_meeting_at=second_meeting_at).kurul


def katilim(
    sayi: int,
    *,
    dagilim: Mapping[str, int] | None = None,
    velisi_katilan: int | None = None,
    gozlemci: int | None = None,
) -> gk.Katilim:
    """Toplantının sayıları (gözlemci katılım sayısına girmez, md. 9/5)."""
    return gk.Katilim(
        attendee_count=sayi,
        attendance_by_kind=dict(dagilim or {}),
        parent_students_count=velisi_katilan,
        observer_count=gozlemci,
    )


# ---------------------------------------------------------------------------
# 5. adım: yapılmış genel kurul, gündem maddesi, veli listesi
# ---------------------------------------------------------------------------
#: Birinci toplantının katılımı (yeter sayı 64'ün üstünde: genel kurul birinci toplantıda yapılır).
KATILAN = 70


def yapilmis_olagan(katilan: int = KATILAN) -> GeneralAssembly:
    """Birinci toplantıda yapılmış olağan genel kurul (`YAPILDI`; katılım `katilan`)."""
    kurul = ilanli_olagan()
    return gk.birinci_toplanti(kurul, katilim=katilim(katilan)).kurul


def yapilmis_olaganustu(katilan: int = KATILAN) -> GeneralAssembly:
    """Birinci toplantıda yapılmış olağanüstü genel kurul (çağrı gündemi `OLAGANUSTU_GUNDEM`)."""
    acik_donem()
    kurul = olaganustu_cagir(planla(kind=AssemblyKind.OLAGANUSTU))
    gk.ilan_et(kurul, kanallar=kanallar())
    return gk.birinci_toplanti(kurul, katilim=katilim(katilan)).kurul


def madde(kurul: GeneralAssembly, kind: str) -> AgendaItem:
    """Genel kurulun verilen türdeki (ilk) gündem maddesi."""
    bulunan: AgendaItem | None = (
        AgendaItem.objects.filter(assembly=kurul, kind=kind).order_by("order").first()
    )
    assert bulunan is not None, kind
    return bulunan


def gundem(kurul: GeneralAssembly) -> list[tuple[int, str]]:
    """Gündemin (sıra, başlık) listesi."""
    return list(
        AgendaItem.objects.filter(assembly=kurul).order_by("order").values_list("order", "title")
    )


def veli_aktar(satirlar: Sequence[tuple[str, str]], ad: str = "veli-listesi.xlsx") -> None:
    """Okulun şablonuyla veli listesi aktarımı (veli adı, öğrencinin sınıfı); adlar UYDURMADIR."""
    import_service.commit_parents_file(file_bytes=veli_xlsx(satirlar), file_name=ad)


def veli_xlsx(satirlar: Sequence[tuple[str, str]]) -> bytes:
    kitap = Workbook()
    sayfa = kitap.active
    assert sayfa is not None
    sayfa.append(list(PARENT_TEMPLATE_HEADERS))
    for satir in satirlar:
        sayfa.append(list(satir))
    tampon = BytesIO()
    kitap.save(tampon)
    return tampon.getvalue()
