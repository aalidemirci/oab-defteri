"""Yönetim kurulu ve Denetleme Kurulu görev bölümü (tasarım §7.2; md. 12/3, 14/1; plan F1c 6. adım).

GÖREV SEÇİMDE VERİLMEZ (plan F1c 5. adım notları): kurul görevlerini görev bölümünde, görevdeki asıl
üyeleri arasından seçer (seçilmiş asıl ya da yedekten çağrılan; `selectors.gorevdeki_asil_mi`). Yedeğe
görev verilmez. Bir görev bölümü kaydı:

* `BoardMeeting(GOREV_BOLUMU)` açar: toplantının günü ve yeri, görevdeki her asılın katılım satırı
  (katıldı · özürlü · özürsüz; özrün nedeni tutulmaz), sonra `YAPILDI` (`kurullar.toplanti_yapildi`);
* görevleri yazar: verilen her görevin önceki sahibi `UYE` olur (dönem içi görev değişimi), yeni sahibi
  görevi alır; yönetim kurulunda dört görev görevdeki asıllar arasında tekildir (sert, hesap bütünlüğü;
  `yonetim_kurulu.gorevler`), Denetleme Kurulunda başkan tektir (aynı sayım);
* `TASLAK` görev bölümü kararı üretir (E01 ve E02'nin kaynağı; program karar defterinin yerine geçmez);
* süreyi denetler (uyarı + gerekçe; uyum satırının konusu görev bölümü toplantısıdır):
  - yönetim kurulu: seçimden ya da yedek çağrısından sonra bir hafta (`yonetim_kurulu.gorev_bolumu_gun`,
    md. 12/3). Süre kurulun bugünkü bileşiminin oluştuğu günden sayılır: görevdeki asılların en geç
    seçilme ya da yedekten çağrı günü (`start_date`, `promoted_on`);
  - Denetleme Kurulu: genel kuruldan sonraki ilk hafta (`denetleme_kurulu.gorev_bolumu_gun`, md. 14/1).
    Süre kurulu seçen genel kurulun gününden sayılır (kullanıcı kararı 10.11.2026): görevdeki veli
    koltuğunun bağlı olduğu genel kurul olağanüstüyse (md. 13/8; kurulu dönem içinde yeniler) o genel
    kurulun günü, değilse dönemi açan genel kurulun günü (`OabTerm.start_date`; birinci ya da ikinci
    toplantı). Süre yalnız o genel kuruldan sonraki ilk görev bölümünde denetlenir: yedek çağrısı
    (md. 14/6) süreyi yeniden başlatmaz;
  - kurulun bugünkü bileşimi oluştuktan sonra yapılmış görev bölümü varsa sonraki görev değişimi süreye
    bağlı değildir (md. 12/3 ve 14/1 yalnız seçimden ya da genel kuruldan ve yönetim kurulunda yedek
    çağrısından sonraki görev bölümüne süre koyar).
  Görev bölümü, görevdeki asılların seçilme ya da yedekten çağrı gününden önce olamaz (sert, tarih
  sırası; iki kurulda da).

YÖNETİM KURULU: kaydı ve karar taslağını sekreter yazar (uç kuralı; tasarım §7.2). Başkan atanınca
başkanın kendiliğinden üye olduğu üç komisyonun temsilci satırları açılır; başkanlığı bırakan önceki
başkanın satırları düşer, başka bir göreve geçmiş olsa da (`temsilciler.baskan_temsilciliklerini_esitle`;
E03). Başkanlığı düşmeyle ya da iptalle biten kişinin satırları o geçişte düşer
(`uyelik_gecisleri.uyeligi_dusur`, `uyeligi_iptal_et`). Görev değişiminde önceki görev sahibinin
hesabının askısı hesap ↔ üyelik bağıyla gelir (F1c 7. adım).

DENETLEME KURULU: başkan seçimi, görev bölümü tutanağı ve denetim planı yalnız Denetleme Kurulunundur
(`Eylem.DK_GOREV_BOLUMU_YAZMA`, M8 ⁵; YK rolleri ve program yöneticisi yazmaz). Başkanlık sayacı burada
koşar (`uyelikler.dk_baskanlik_denetimi`, md. 14/3). Başkan olmayan üye görev bölümünde başkan
seçilince üyeliğin `chair_elections` sayısı bir artar (kullanıcı kararı 10.11.2026: her başkanlık seçimi
bir seçilmedir; aynı dönemde A → B → A dönüşünde A iki kez sayılır). Görevdeki başkanın yeni görev
bölümünde yeniden başkan seçilmesi (A → A) sayılmaz: dönem içinde başka bir görev için yapılan görev
bölümü süren başkanlığı sınıra yaklaştırmaz (plan F1c 6. adım notları). Sayı azalmaz: dönem içi görev değişiminde önceki başkanın seçilmesi sayaçtan düşmez (md. 14/3
"seçilebilir"; sayılan seçilmedir). Denetim planı tarihleri dönem ayarıdır (`OabTerm.dk_audit_plan_dates`;
E02, E14); "yılda en az iki inceleme" kuralı F4'tedir.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Final

from django.db import transaction
from django.utils import timezone

from apps.oab import selectors
from apps.oab.kurallar import VERI_YOK, yazma_kapisi
from apps.oab.models import (
    AssemblyKind,
    BoardDecision,
    BoardMeeting,
    DecisionKind,
    MeetingKind,
    MeetingStatus,
    MembershipRole,
    MembershipStatus,
    OabTerm,
    OrganMembership,
    OrganType,
    SeatGroup,
)
from apps.oab.services import donem_kilidi, iz, kurullar, temsilciler, uyelikler, uyum
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.services import app_password

#: Yönetim kurulunun görev bölümünde seçilen dört görev (md. 12/3).
YK_GOREVLERI: Final = frozenset(
    {
        MembershipRole.BASKAN,
        MembershipRole.BASKAN_YARDIMCISI,
        MembershipRole.MUHASIP,
        MembershipRole.SEKRETER,
    }
)

GOREV_YOK = "Görev bölümünde en az bir görev verilmelidir."
GOREV_GECERSIZ = "Bu görev yönetim kurulunun görev bölümünde verilmez."
AYNI_UYEYE_IKI_GOREV = "Bir üyeye görev bölümünde tek görev verilir."
UYELIK_KURULDA_DEGIL = "Görev yalnız bu dönemin bu kurulundaki seçilmiş üyeye verilir."
KATILIM_TEKRAR = "Bir üyenin katılım satırı bir kez girilir."
GOREV_BOLUMU_SECIMDEN_ONCE = (
    "Görev bölümü, kurulun bugünkü üyelerinin seçildiği ya da yedekten çağrıldığı günden önce "
    "olamaz."
)
GOREV_BOLUMU_DONEMDEN_ONCE = (
    "Görev bölümü birlik döneminin başından ya da kurulu seçen genel kuruldan önce olamaz."
)
PLAN_DONEM_DISI = "Denetim planı tarihleri birlik döneminin başından önce olamaz."
DK_BASKAN_TEKIL = "Denetleme Kurulunun görevdeki asılları arasında tek başkan olur."


@dataclass(frozen=True)
class KatilimSatiri:
    """Görev bölümü toplantısında bir üyenin katılımı (özrün nedeni tutulmaz)."""

    uyelik: OrganMembership
    present: bool
    excused: bool = False


@dataclass(frozen=True)
class GorevBolumu:
    """Görev bölümü kaydının ürettikleri."""

    toplanti: BoardMeeting
    karar: BoardDecision
    uyelikler: tuple[OrganMembership, ...]


# ---------------------------------------------------------------------------
# Ortak adımlar
# ---------------------------------------------------------------------------
def _kurul_uyesi(uyelik: OrganMembership, donem: OabTerm, organ: str) -> OrganMembership:
    """Görev verilecek üyelik: bu dönemin bu kurulunda seçilmiş görevdeki asıl."""
    guncel = uyelikler.guncel_kayit(uyelik)
    if (
        guncel.term_id != donem.pk
        or guncel.organ != organ
        or guncel.status != MembershipStatus.SECILDI
    ):
        raise ValueError(UYELIK_KURULDA_DEGIL)
    if not selectors.gorevdeki_asil_mi(guncel):
        raise ValueError(uyelikler.GOREV_YALNIZ_ASILDA)
    return guncel


def _gun(held_at: datetime) -> date:
    return timezone.localdate(held_at) if timezone.is_aware(held_at) else held_at.date()


def kurulun_olustugu_gun(donem: OabTerm, organ: str) -> date | None:
    """Kurulun bugünkü bileşiminin oluştuğu gün: görevdeki asılların en geç seçilme ya da yedekten
    çağrı günü (modül başlığı; yönetim kurulunda süre buradan sayılır, iki kurulda da görev bölümü bu
    günden önce olamaz). Gün bilinmiyorsa `None`."""
    gunler = [
        uyelik.promoted_on or uyelik.start_date
        for uyelik in selectors.gorevdeki_asillar(donem, organ)
    ]
    bilinen = [gun for gun in gunler if gun is not None]
    return max(bilinen) if bilinen else None


def dk_secen_genel_kurul_gunu(donem: OabTerm) -> date | None:
    """Denetleme Kurulunu seçen genel kurulun günü (md. 14/1 "genel kuruldan sonraki ilk hafta";
    kullanıcı kararı 10.11.2026; modül başlığı).

    Görevdeki veli koltuğunun (genel kurul seçer) bağlı olduğu genel kurul olağanüstüyse kurulu dönem
    içinde yenilemiştir (md. 13/8): onun günü. Öteki hâllerde (olağan genel kurul, devralınan ya da boş
    veli koltuğu) dönemi açan genel kurulun günü (`OabTerm.start_date`; birinci ya da ikinci toplantı,
    tasarım §7.1). Olağanüstü genel kurulun günü F1c'de birinci toplantının yerel günüdür; ikinci
    toplantı alanı F2'de gelince o toplantının günü olur. Bilinmiyorsa `None` (eksik)."""
    gunler = [
        timezone.localdate(uyelik.assembly.first_meeting_at)
        for uyelik in selectors.gorevdeki_asillar(donem, OrganType.DENETLEME_KURULU)
        if uyelik.seat_group == SeatGroup.VELI
        and uyelik.assembly is not None
        and uyelik.assembly.kind == AssemblyKind.OLAGANUSTU
        and uyelik.assembly.first_meeting_at is not None
    ]
    return max(gunler) if gunler else donem.start_date


def _sure_referansi(donem: OabTerm, organ: str, olustugu: date | None) -> date | None:
    """Sürenin başladığı gün (modül başlığı): yönetim kurulunda kurulun bugünkü bileşiminin oluştuğu
    gün (md. 12/3: seçim ya da yedek çağrısı), Denetleme Kurulunda kurulu seçen genel kurulun günü
    (md. 14/1: "genel kuruldan sonraki ilk hafta"; `dk_secen_genel_kurul_gunu`). Bilinmiyorsa `None`
    (eksik)."""
    if organ == OrganType.DENETLEME_KURULU:
        return dk_secen_genel_kurul_gunu(donem)
    return olustugu


def _onceki_gorev_bolumu_var(donem: OabTerm, organ: str, referans: date | None, gun: date) -> bool:
    """Referans gününde ya da sonra, bu görev bölümünün gününde ya da önce yapılmış (`YAPILDI`) görev
    bölümü var mı? Varsa yeni kayıt dönem içi görev değişimidir, süreye bağlı değildir (modül başlığı).
    Referans yoksa dönemdeki her önceki görev bölümü sayılır."""
    for held_at in BoardMeeting.objects.filter(
        term=donem,
        organ=organ,
        kind=MeetingKind.GOREV_BOLUMU,
        status=MeetingStatus.YAPILDI,
    ).values_list("held_at", flat=True):
        if held_at is None or _gun(held_at) > gun:
            continue
        if referans is None or _gun(held_at) >= referans:
            return True
    return False


def _sure_gozlenen(donem: OabTerm, organ: str, gun: date) -> Any | None:
    """Süre kuralının gözleneni (gün farkı ya da eksik); süre bu görev bölümüne bağlı değilse `None`
    (çağıran kuralı denetlemez, satır açılmaz). Tarih sırası sert denetlenir."""
    olustugu = kurulun_olustugu_gun(donem, organ)
    if olustugu is not None and gun < olustugu:
        raise ValueError(GOREV_BOLUMU_SECIMDEN_ONCE)
    referans = _sure_referansi(donem, organ, olustugu)
    if _onceki_gorev_bolumu_var(donem, organ, referans, gun):
        return None
    if referans is None:
        return VERI_YOK
    fark = (gun - referans).days
    if fark < 0:
        raise ValueError(GOREV_BOLUMU_DONEMDEN_ONCE)
    return fark


def _toplanti_ve_katilim(
    donem: OabTerm,
    organ: str,
    *,
    held_at: datetime,
    place: str,
    katilim: Sequence[KatilimSatiri],
) -> BoardMeeting:
    """Görev bölümü toplantısı: katılım satırları, sonra `YAPILDI` (her görevdeki asıl girilmeli)."""
    gorulen: set[int] = set()
    for satir in katilim:
        if satir.uyelik.pk in gorulen:
            raise ValueError(KATILIM_TEKRAR)
        gorulen.add(satir.uyelik.pk)
    toplanti = kurullar.toplanti_olustur(
        donem=donem, organ=organ, kind=MeetingKind.GOREV_BOLUMU, scheduled_at=held_at, place=place
    )
    for satir in katilim:
        kurullar.katilim_yaz(toplanti, satir.uyelik, present=satir.present, excused=satir.excused)
    return kurullar.toplanti_yapildi(toplanti, held_at=held_at)


def _gorev_yaz(
    uyelik: OrganMembership,
    role: str,
    izler: dict[int, tuple[OrganMembership, Any]],
    *,
    baskan_secildi: bool = False,
) -> OrganMembership:
    """Görevi yazar; aynıysa yazmaz. İz satırı denetimden sonra yazılır (`izler`: ilk anlık).

    `baskan_secildi`: Denetleme Kurulunda başkan olmayan üye başkan seçilince `chair_elections` sayısı
    bir artar; görevdeki başkanın yeniden seçilmesi (A → A) artırmaz (modül başlığı; azalmaz, görev
    değişimi sayıyı silmez)."""
    yeni_baskanlik = baskan_secildi and uyelik.role != MembershipRole.BASKAN
    alanlar: list[str] = []
    if uyelik.role != role:
        alanlar.append("role")
    if yeni_baskanlik:
        alanlar.append("chair_elections")
    if not alanlar:
        return uyelik
    izler.setdefault(uyelik.pk, (uyelik, denetim_izi.anlik(uyelik)))
    uyelik.role = role
    if yeni_baskanlik:
        uyelik.chair_elections += 1
    uyelik.updated_by_id = iz.yazar_hesabi()
    uyelik.save(update_fields=[*alanlar, "updated_at", "updated_by"])
    return uyelik


def _gorevleri_dagit(
    donem: OabTerm, organ: str, atamalar: Mapping[str, OrganMembership]
) -> list[OrganMembership]:
    """Önce verilen görevlerin önceki sahipleri `UYE` olur, sonra yeni sahipler görevi alır; tekillik
    yazımdan sonra her yeni sahipte sayılır, iz satırları en son yazılır (`GUNCELLE`; içerik MAC'i
    kaydın son hâlidir). Yeni göreve geçen önceki sahip ara adımda `UYE` yazılmaz (gereksiz iz)."""
    yeniler = {uyelik.pk for uyelik in atamalar.values()}
    izler: dict[int, tuple[OrganMembership, Any]] = {}
    for role in atamalar:
        for eski in selectors.gorevdeki_asillar(donem, organ):
            if eski.role == role and eski.pk not in yeniler:
                _gorev_yaz(eski, MembershipRole.UYE, izler)
    yazilanlar = [
        _gorev_yaz(
            uyelik,
            role,
            izler,
            baskan_secildi=(organ == OrganType.DENETLEME_KURULU and role == MembershipRole.BASKAN),
        )
        for role, uyelik in atamalar.items()
    ]
    for uyelik in yazilanlar:
        guncel = uyelikler.guncel_kayit(uyelik)
        ozet = uyelikler.ozet_hesapla(guncel, uyelikler.gorev_tekilligini_denetle(guncel))
        if ozet != (guncel.rule_warnings or []):
            izler.setdefault(guncel.pk, (guncel, denetim_izi.anlik(guncel)))
            guncel.rule_warnings = ozet
            guncel.save(update_fields=["rule_warnings", "updated_at"])
    for _, (uyelik, onceki) in sorted(izler.items()):
        denetim_izi.degisiklik(uyelikler.guncel_kayit(uyelik), onceki=onceki)
    return [uyelikler.guncel_kayit(u) for u in yazilanlar]


def _gorevdeki_baskan(donem: OabTerm) -> OrganMembership | None:
    """Yönetim kurulunun görevdeki başkanı (görev tekil; yoksa `None`)."""
    for uyelik in selectors.gorevdeki_asillar(donem, OrganType.YONETIM_KURULU):
        if uyelik.role == MembershipRole.BASKAN:
            return uyelik
    return None


def _baslangic(donem: OabTerm) -> OabTerm:
    app_password.require_password_set()
    guncel = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(guncel)
    return guncel


def _atamalari_dogrula(
    donem: OabTerm, organ: str, gorevler: Mapping[str, OrganMembership], izinli: Iterable[str]
) -> dict[str, OrganMembership]:
    if not gorevler:
        raise ValueError(GOREV_YOK)
    izinli_kume = set(izinli)
    atamalar: dict[str, OrganMembership] = {}
    for role, uyelik in gorevler.items():
        if role not in izinli_kume:
            raise ValueError(GOREV_GECERSIZ)
        atamalar[str(role)] = _kurul_uyesi(uyelik, donem, organ)
    if len({u.pk for u in atamalar.values()}) != len(atamalar):
        raise ValueError(AYNI_UYEYE_IKI_GOREV)
    return atamalar


# ---------------------------------------------------------------------------
# Yönetim kurulu (md. 12/3)
# ---------------------------------------------------------------------------
@transaction.atomic
def yk_gorev_bolumu(
    *,
    term: OabTerm,
    held_at: datetime,
    gorevler: Mapping[str, OrganMembership],
    katilim: Sequence[KatilimSatiri],
    place: str = "",
    text: str = "",
    gerekce: uyum.Gerekce | None = None,
) -> GorevBolumu:
    """Yönetim kurulunun görev bölümü (modül başlığı). Gerekçesiz süre uyarısı işlemi geri alır."""
    yazma_kapisi()
    donem = _baslangic(term)
    atamalar = _atamalari_dogrula(donem, OrganType.YONETIM_KURULU, gorevler, YK_GOREVLERI)
    gun = _gun(held_at)
    gozlenen = _sure_gozlenen(donem, OrganType.YONETIM_KURULU, gun)
    onceki_baskan = _gorevdeki_baskan(donem)
    toplanti = _toplanti_ve_katilim(
        donem, OrganType.YONETIM_KURULU, held_at=held_at, place=place, katilim=katilim
    )
    yazilanlar = _gorevleri_dagit(donem, OrganType.YONETIM_KURULU, atamalar)
    karar = kurullar.karar_taslagi_olustur(
        toplanti, kind=DecisionKind.GOREV_BOLUMU, text=text, decision_date=gun
    )
    if gozlenen is not None:
        uyum.denetle(
            "yonetim_kurulu.gorev_bolumu_gun",
            gozlenen,
            donem=donem,
            konu=toplanti,
            tarih=gun,
            gerekce=gerekce,
        )
    # Başkanlığı bırakan yalnız önceki başkandır, başka göreve geçmiş olsa da (modül başlığı): başka
    # görevi bırakanın elle girilmiş temsilci satırına dokunulmaz.
    birakanlar: set[int] = set()
    if (
        onceki_baskan is not None
        and uyelikler.guncel_kayit(onceki_baskan).role != MembershipRole.BASKAN
    ):
        birakanlar.add(onceki_baskan.person_id)
    baskan = atamalar.get(MembershipRole.BASKAN)
    if baskan is not None or birakanlar:
        temsilciler.baskan_temsilciliklerini_esitle(
            donem,
            None if baskan is None else uyelikler.guncel_kayit(baskan),
            gun=gun,
            birakanlar=birakanlar,
        )
    return GorevBolumu(toplanti, karar, tuple(yazilanlar))


# ---------------------------------------------------------------------------
# Denetleme Kurulu (md. 14/1, 14/3)
# ---------------------------------------------------------------------------
def _plan_yaz(donem: OabTerm, plan: Sequence[date]) -> None:
    """Denetim planı tarihleri (dönem ayarı): sıralı ve tekrarsız; dönem başından önce olamaz."""
    gunler = sorted(set(plan))
    if donem.start_date is not None and any(gun < donem.start_date for gun in gunler):
        raise ValueError(PLAN_DONEM_DISI)
    yeni = [gun.isoformat() for gun in gunler]
    if yeni == list(donem.dk_audit_plan_dates or []):
        return
    onceki = denetim_izi.anlik(donem)
    donem.dk_audit_plan_dates = yeni
    donem.updated_by_id = iz.yazar_hesabi()
    donem.save(update_fields=["dk_audit_plan_dates", "updated_at", "updated_by"])
    denetim_izi.degisiklik(donem, onceki=onceki)


@transaction.atomic
def dk_gorev_bolumu(
    *,
    term: OabTerm,
    held_at: datetime,
    baskan: OrganMembership,
    katilim: Sequence[KatilimSatiri],
    denetim_plani: Sequence[date] | None = None,
    place: str = "",
    text: str = "",
    gerekce: uyum.Gerekce | None = None,
) -> GorevBolumu:
    """Denetleme Kurulunun görev bölümü ve denetim planı (modül başlığı; yalnız Denetleme Kurulu)."""
    yazma_kapisi()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.DK_GOREV_BOLUMU_YAZMA, term)
    donem = _baslangic(term)
    atamalar = _atamalari_dogrula(
        donem, OrganType.DENETLEME_KURULU, {MembershipRole.BASKAN: baskan}, {MembershipRole.BASKAN}
    )
    gun = _gun(held_at)
    gozlenen = _sure_gozlenen(donem, OrganType.DENETLEME_KURULU, gun)
    toplanti = _toplanti_ve_katilim(
        donem, OrganType.DENETLEME_KURULU, held_at=held_at, place=place, katilim=katilim
    )
    yazilanlar = _gorevleri_dagit(donem, OrganType.DENETLEME_KURULU, atamalar)
    # Başkan tekilliği (hesap bütünlüğü; md. 14/1 "bir başkan"): önceki başkan üye oldu, sayım teyittir.
    baskanlar = [
        u
        for u in selectors.gorevdeki_asillar(donem, OrganType.DENETLEME_KURULU)
        if u.role == MembershipRole.BASKAN
    ]
    if len(baskanlar) != 1:
        raise ValueError(DK_BASKAN_TEKIL)
    karar = kurullar.karar_taslagi_olustur(
        toplanti, kind=DecisionKind.GOREV_BOLUMU, text=text, decision_date=gun
    )
    if gozlenen is not None:
        uyum.denetle(
            "denetleme_kurulu.gorev_bolumu_gun",
            gozlenen,
            donem=donem,
            konu=toplanti,
            tarih=gun,
            gerekce=gerekce,
        )
    uyelikler.dk_baskanlik_denetimi(yazilanlar[0], gerekce=gerekce)
    if denetim_plani is not None:
        _plan_yaz(donem, denetim_plani)
    return GorevBolumu(toplanti, karar, tuple(yazilanlar))
