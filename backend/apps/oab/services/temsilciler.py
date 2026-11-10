"""Birlik temsilcileri ve alım komisyonu (tasarım §5.2.2 "Temsil türleri", §6.4.4, §6.4.6; plan F1c 6.
adım).

Temsilci, birliğin kurul ve komisyonlardaki üyesidir (`OrganMembership`, organ `TEMSILCI`); temsil türü
ayrı koltuktur: aynı veli iki kurulda temsilci olabilir, başkan kendiliğinden üye olduğu komisyonlarda
ayrı satır alır (genel kurulsuz tekil kısıt `representation` ile ayırır). Kayıt genel kurul dışı
kanaldır, seçilmiş (`SECILDI`) açılır: kurul temsilcilerini yönetim kurulu kararı belirler
(`YK_KARARI`; kararın bağı `representative_decision`, E03'ün karar no'su; F1c'de boş kalabilir; bağlanan
karar kabul edilmiş olmalıdır, tasarım §7.2 "Notlar"), başkanın kendiliğinden üye olduğu komisyonlar
`KENDILIGINDEN`'dir. Pay dağıtım komisyonu üyeliği il/ilçe millî eğitim müdürlüğünce kurulan, mülki amirin
onayladığı komisyona seçilmedir (md. 17/1-b-3); kendiliğinden değildir, kanalı `MEM_GOREVLENDIRME`'dir.

KURALLAR (uyarı + gerekçe; hiçbiri yazımı engellemez):

* Kurul temsilcisi sayıları (`temsilci.odul_disiplin_kurulu` 1 asıl + 1 yedek, davranış, sosyal
  etkinlikler, kontenjan, RPD 1): kademe koşulu kural paketindedir (`okul.kademe`; karma okulda iki
  kademenin satırları birlikte). Fazla temsilci yazımda uyarı + gerekçedir; eksik temsilci
  tamamlanacaktır (çizelgede, gerekçe istemez). Sayı satırının konusu birlik dönemidir.
* Başkanın kendiliğinden üye olduğu taşımacıyı tespit, muhammen bedel ve kiralama ihale komisyonları:
  temsilci görevdeki yönetim kurulu başkanı değilse uyarı + gerekçe (`liste_icinde`, konu üyelik).
  Görev bölümü başkanı atayınca bu üç satır kendiliğinden açılır, başkanlığı bırakan önceki başkanın
  satırları düşer (`baskan_temsilciliklerini_esitle`); başkanlık kaydı düşer ya da iptal edilirse
  satırlar aynı işlemde düşer ya da iptal olur (`baskan_satirlarini_kapat`).
* Pay dağıtım komisyonu (md. 17/1-b-3) yalnız kayıttır: pakette `karsilastirma: parametre`, servis
  `denetle` çağırmaz; satır yalnız başkan seçildiyse çizelgede görünür, sayı uyarısı üretilmez (plan F1c
  2. adım notları).
* Kantin denetim komisyonu (Genelge 2020/8 A-1/a-b; `temsilci.kantin_denetim_komisyonu`): temsilci
  görevdeki asıl yönetim kurulu üyesi ve velidir; değilse ya da satır birden çoksa uyarı + gerekçe;
  satır yoksa tamamlanacak. Kantini olmayan okulda kural sessizdir, satır kayıt olarak açılabilir.
* Kampüs yönetimi (md. 13/7) kayıt satırıdır, kuralı yoktur; çizelgede okul kampüsteyse görünür.

ALIM KOMİSYONU (md. 18/1): üyelik `ALIM_KOMISYONU` organıdır (komisyonun tek kaynağı, O6); en az üç
kişi organ ekranının kadro uyarısıdır (`uyelikler.kadro_uyarilari`), harcama dosyasındaki karşılığı ve
üyelerin YK üyesi ya da uzmanlık işaretli olması (`harcama.alim_komisyonu_uyeleri`) F4'tedir.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Final

from django.db import transaction
from django.utils import timezone

from apps.oab import selectors
from apps.oab.kurallar import VERI_YOK, YururlukteDegerYok, kural_kaydi, yazma_kapisi
from apps.oab.kurallar.erisim import DenetimSonucu, atifli_metin
from apps.oab.kurallar.erisim import denetle as paket_denetle
from apps.oab.models import (
    BoardDecision,
    DecisionStatus,
    DropKind,
    ElectedBy,
    MembershipRole,
    MembershipStatus,
    OabPerson,
    OabTerm,
    OrganMembership,
    OrganType,
    Representation,
    SeatType,
)
from apps.oab.services import donem_kilidi, iz, uyelikler, uyum
from apps.okul import denetim_izi
from apps.okul.models import SchoolConfig
from apps.okul.services import app_password

#: Temsil türünün kuralı (tasarım §6.4.4); kampüs yönetimi ve "diğer" kuralsızdır.
TEMSIL_KURALLARI: Final[dict[str, str]] = {
    Representation.ODUL_DISIPLIN_KURULU: "temsilci.odul_disiplin_kurulu",
    Representation.DAVRANIS_DEGERLENDIRME_KURULU: "temsilci.davranis_degerlendirme_kurulu",
    Representation.SOSYAL_ETKINLIKLER_KURULU: "temsilci.sosyal_etkinlikler_kurulu",
    Representation.KONTENJAN_KOMISYONU: "temsilci.kontenjan_komisyonu",
    Representation.RPD_YURUTME_KOMISYONU: "temsilci.rpd_yurutme_komisyonu",
    Representation.TASIMACI_TESPIT_KOMISYONU: "temsilci.tasimaci_tespit_komisyonu",
    Representation.MUHAMMEN_BEDEL_KOMISYONU: "temsilci.muhammen_bedel_komisyonu",
    Representation.KIRALAMA_IHALE_KOMISYONU: "temsilci.kiralama_ihale_komisyonu",
    Representation.PAY_DAGITIM_KOMISYONU: "temsilci.pay_dagitim_komisyonu",
    Representation.KANTIN_DENETIM_KOMISYONU: "temsilci.kantin_denetim_komisyonu",
}

#: Başkanın kendiliğinden üye olduğu komisyonlar (doğrudan üyelik, seçim yok; E03 "başkanın adı
#: kendiliğinden"). Görev bölümü başkanı atayınca bu satırlar açılır.
BASKANIN_KOMISYONLARI: Final = (
    Representation.TASIMACI_TESPIT_KOMISYONU,
    Representation.MUHAMMEN_BEDEL_KOMISYONU,
    Representation.KIRALAMA_IHALE_KOMISYONU,
)
#: Başkanın seçildiyse girdiği komisyon (yalnız kayıt; "seçildiyse"): üyelik il/ilçe millî eğitim
#: müdürlüğünce kurulan, mülki amirin onayladığı komisyona seçilmedir (md. 17/1-b-3); kendiliğinden
#: değildir.
YALNIZ_KAYIT: Final = frozenset({Representation.PAY_DAGITIM_KOMISYONU})
#: Kendiliğinden (başkan sıfatıyla) üyelik kanalı; öteki temsilcileri yönetim kurulu kararı belirler.
KENDILIGINDEN_TEMSILLER: Final = frozenset(BASKANIN_KOMISYONLARI)

TEMSIL_TURU_GEREKLI = "Temsil türü seçilmelidir."
KOLTUK_GECERSIZ = "Koltuk asıl ya da yedek olmalıdır."
AYNI_TEMSIL_VAR = "Bu kişinin bu dönemde bu kurul ya da komisyonda temsilci kaydı zaten var."
KARAR_YK_DEGIL = (
    "Temsilci görevlendirme kararı bu dönemin yönetim kurulu toplantısının kararı olmalıdır."
)
AYNI_KOMISYON_UYESI_VAR = "Bu kişinin bu dönemde alım komisyonunda kaydı zaten var."
#: Bağlanan karar kabul edilmiş olmalıdır (tasarım §7.2 "Notlar"; sert, hesap bütünlüğü).
KARAR_KABUL_EDILMEMIS = (
    "Bağlanacak karar kabul edilmiş olmalı; taslak, iptal edilmiş, reddedilmiş ya da defterde sakat "
    "karar bağlanamaz."
)
#: Bağlanabilen kararın durumları (`DEFTERE_ISLENDI`, `KABUL_EDILDI`'nin ardılıdır).
BAGLANABILIR_KARAR_DURUMLARI: Final = frozenset(
    {DecisionStatus.KABUL_EDILDI, DecisionStatus.DEFTERE_ISLENDI}
)
#: Başkanlık kaydı iptal edilince kendiliğinden satırların iptal gerekçesi (kişisiz).
BASKANLIK_IPTAL_GEREKCESI = (
    "Başkanlık kaydı iptal edildi; başkan sıfatıyla açılan satır da iptal edildi."
)


def okul_baglami() -> dict[str, Any]:
    """Kural koşullarının okul kartındaki değerleri (`okul.kademe`, `okul.kantin`; tasarım §6.1)."""
    okul = SchoolConfig.load()
    return {"okul.kademe": list(okul.levels or []), "okul.kantin": okul.canteen_mode}


def _kosul(kural_id: str, *, donem: OabTerm, gun: date, okul: dict[str, Any]) -> bool | None:
    """Kuralın koşulu sağlanıyor mu? Okul kartında değer girilmemişse `None` (eksik; R5).

    `erisim.denetle`'nin koşul okumasıyla aynıdır; çizelge satırın görünürlüğü için ayrıca sorar.
    """
    try:
        kayit = kural_kaydi(kural_id, tarih=gun, donem=donem)
    except YururlukteDegerYok:
        return False
    for anahtar, izinli in kayit.get("kosul", {}).items():
        secili = okul.get(anahtar)
        if not secili:
            return None
        degerler = secili if isinstance(secili, list | tuple | set) else [secili]
        if not set(degerler) & set(izinli):
            return False
    return True


def _secilmis_temsilciler(donem: OabTerm, representation: str) -> list[OrganMembership]:
    return selectors.memberships_sorted(
        OrganMembership.objects.filter(
            term=donem,
            organ=OrganType.TEMSILCI,
            representation=representation,
            status=MembershipStatus.SECILDI,
        ).select_related("person")
    )


def _yk_gorevi(donem: OabTerm, kisi_id: int) -> str:
    """Kişinin bu dönemde görevdeki asıl yönetim kurulu üyeliğindeki görevi; üye değilse `YOK`."""
    for uyelik in selectors.gorevdeki_asillar(donem, OrganType.YONETIM_KURULU):
        if uyelik.person_id == kisi_id:
            return str(uyelik.role)
    return "YOK"


# ---------------------------------------------------------------------------
# Gözlenen değerler (yazımda ve çizelgede aynı hesap)
# ---------------------------------------------------------------------------
def _sayi_gozlenen(donem: OabTerm, representation: str, deger: Any) -> tuple[Any, str]:
    """Sayı kuralının gözleneni ve yönü: `fazla`, `tam` ya da `eksik` (eksik gerekçe istemez)."""
    satirlar = _secilmis_temsilciler(donem, representation)
    if isinstance(deger, dict):
        sayilar = {koltuk: sum(1 for u in satirlar if u.seat_type == koltuk) for koltuk in deger}
        if any(sayilar[k] > deger[k] for k in deger):
            return sayilar, "fazla"
        return (sayilar, "tam") if sayilar == deger else (VERI_YOK, "eksik")
    sayi = len({u.person_id for u in satirlar})
    if sayi > deger:
        return sayi, "fazla"
    return (sayi, "tam") if sayi == deger else (VERI_YOK, "eksik")


def _kantin_gozlenen(donem: OabTerm) -> Any:
    """Kantin denetim temsilcisi: görevdeki asıl yönetim kurulu üyesi ve veli tek kişi (tasarım §6.4.4).

    Satır yoksa eksik; birden çoksa satır sayısı; tek satır uygunsa 1, değilse 0 (uyarı)."""
    satirlar = _secilmis_temsilciler(donem, Representation.KANTIN_DENETIM_KOMISYONU)
    if not satirlar:
        return VERI_YOK
    if len(satirlar) > 1:
        return len(satirlar)
    temsilci = satirlar[0]
    uygun = _yk_gorevi(donem, temsilci.person_id) != "YOK" and temsilci.person.is_parent
    return 1 if uygun else 0


def _baskan_gozlenen(donem: OabTerm, satirlar: Iterable[OrganMembership]) -> Any:
    gorevler = [_yk_gorevi(donem, u.person_id) for u in satirlar]
    return gorevler or VERI_YOK


# ---------------------------------------------------------------------------
# Yazımdaki denetimler (kimlikler çağrıda açık yazılır: D6'nın statik taraması)
# ---------------------------------------------------------------------------
_Denetci = Callable[..., uyum.UyumSonucu]

_SAYI_DENETCILERI: Final[dict[str, _Denetci]] = {
    Representation.ODUL_DISIPLIN_KURULU: lambda g, **k: uyum.denetle(
        "temsilci.odul_disiplin_kurulu", g, **k
    ),
    Representation.DAVRANIS_DEGERLENDIRME_KURULU: lambda g, **k: uyum.denetle(
        "temsilci.davranis_degerlendirme_kurulu", g, **k
    ),
    Representation.SOSYAL_ETKINLIKLER_KURULU: lambda g, **k: uyum.denetle(
        "temsilci.sosyal_etkinlikler_kurulu", g, **k
    ),
    Representation.KONTENJAN_KOMISYONU: lambda g, **k: uyum.denetle(
        "temsilci.kontenjan_komisyonu", g, **k
    ),
    Representation.RPD_YURUTME_KOMISYONU: lambda g, **k: uyum.denetle(
        "temsilci.rpd_yurutme_komisyonu", g, **k
    ),
}
_BASKAN_DENETCILERI: Final[dict[str, _Denetci]] = {
    Representation.TASIMACI_TESPIT_KOMISYONU: lambda g, **k: uyum.denetle(
        "temsilci.tasimaci_tespit_komisyonu", g, **k
    ),
    Representation.MUHAMMEN_BEDEL_KOMISYONU: lambda g, **k: uyum.denetle(
        "temsilci.muhammen_bedel_komisyonu", g, **k
    ),
    Representation.KIRALAMA_IHALE_KOMISYONU: lambda g, **k: uyum.denetle(
        "temsilci.kiralama_ihale_komisyonu", g, **k
    ),
}


def _temsil_denetimi(
    uyelik: OrganMembership, donem: OabTerm, *, gerekce: uyum.Gerekce | None
) -> None:
    """Yazılan temsilci satırının kuralı (modül başlığı "Kurallar")."""
    temsil = str(uyelik.representation)
    gun = uyelik.start_date or timezone.localdate()
    ortak: dict[str, Any] = {
        "donem": donem,
        "tarih": gun,
        "okul": okul_baglami(),
        "gerekce": gerekce,
    }
    if temsil in _SAYI_DENETCILERI:
        try:
            deger = kural_kaydi(TEMSIL_KURALLARI[temsil], tarih=gun, donem=donem)["deger"]
        except YururlukteDegerYok:
            return
        gozlenen, yon = _sayi_gozlenen(donem, temsil, deger)
        if yon != "eksik":
            _SAYI_DENETCILERI[temsil](gozlenen, konu=donem, **ortak)
    elif temsil in _BASKAN_DENETCILERI:
        sonuc = _BASKAN_DENETCILERI[temsil](
            _yk_gorevi(donem, uyelik.person_id), konu=uyelik, **ortak
        )
        ozet = uyelikler.ozet_hesapla(uyelik, {TEMSIL_KURALLARI[temsil]: sonuc.sonuc})
        if ozet != (uyelik.rule_warnings or []):
            uyelik.rule_warnings = ozet
            uyelik.save(update_fields=["rule_warnings", "updated_at"])
    elif temsil == Representation.KANTIN_DENETIM_KOMISYONU:
        uyum.denetle(
            "temsilci.kantin_denetim_komisyonu", _kantin_gozlenen(donem), konu=donem, **ortak
        )
    # Pay dağıtım komisyonu yalnız kayıttır (denetle çağrılmaz); kampüs yönetimi ve "diğer" kuralsız.


# ---------------------------------------------------------------------------
# Yazma yolları
# ---------------------------------------------------------------------------
def _baslangic(term: OabTerm) -> OabTerm:
    """Güncel dönem; ilk hesap kurulu ve dönem yazılabilir olmalı (kural kullanan servis ayrıca
    `yazma_kapisi()` ile başlar)."""
    app_password.require_password_set()
    donem = OabTerm.objects.select_related("rule_package").get(pk=term.pk)
    donem_kilidi.yazma_denetimi(donem)
    return donem


def _ayni_satir_var(donem: OabTerm, kisi: OabPerson, organ: str, representation: str) -> bool:
    return (
        OrganMembership.objects.filter(
            term=donem,
            person=kisi,
            organ=organ,
            representation=representation,
            assembly__isnull=True,
        )
        .exclude(status=MembershipStatus.IPTAL)
        .exists()
    )


def _olustur(
    donem: OabTerm,
    kisi: OabPerson,
    *,
    organ: str,
    representation: str,
    seat_type: str,
    elected_by: str,
    start_date: date,
    representative_decision: BoardDecision | None = None,
    expertise_required: bool = False,
) -> OrganMembership:
    hesap = iz.yazar_hesabi()
    uyelik = OrganMembership.objects.create(
        term=donem,
        person=kisi,
        organ=organ,
        role=MembershipRole.UYE,
        seat_type=seat_type,
        representation=representation,
        representative_decision=representative_decision,
        elected_by=elected_by,
        status=MembershipStatus.SECILDI,
        start_date=start_date,
        expertise_required=expertise_required,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    # İz satırını çağıran, kuralın uyarı özetinden SONRA yazar (içerik MAC'i son hâlidir).
    return uyelik


def _karar_dogrula(donem: OabTerm, karar: BoardDecision | None) -> BoardDecision | None:
    if karar is None:
        return None
    guncel = BoardDecision.objects.select_related("meeting").get(pk=karar.pk)
    if guncel.meeting.organ != OrganType.YONETIM_KURULU or guncel.meeting.term_id != donem.pk:
        raise ValueError(KARAR_YK_DEGIL)
    if guncel.status not in BAGLANABILIR_KARAR_DURUMLARI:
        raise ValueError(KARAR_KABUL_EDILMEMIS)
    return guncel


def _kanal(representation: str) -> str:
    """Temsilci satırının seçim kanalı (modül başlığı): başkanın kendiliğinden üyeliği, pay dağıtım
    komisyonuna seçilme, öteki temsilcilerde yönetim kurulu kararı."""
    if representation in KENDILIGINDEN_TEMSILLER:
        return str(ElectedBy.KENDILIGINDEN)
    if representation in YALNIZ_KAYIT:
        return str(ElectedBy.MEM_GOREVLENDIRME)
    return str(ElectedBy.YK_KARARI)


@transaction.atomic
def temsilci_ekle(
    *,
    term: OabTerm,
    person: OabPerson,
    representation: str,
    seat_type: str = SeatType.ASIL,
    start_date: date | None = None,
    representative_decision: BoardDecision | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> OrganMembership:
    """Temsilci kaydı (`OLUSTUR`): seçilmiş açılır; kuralı uyarı + gerekçedir (modül başlığı)."""
    yazma_kapisi()
    donem = _baslangic(term)
    if representation not in Representation.values:
        raise ValueError(TEMSIL_TURU_GEREKLI)
    if seat_type not in SeatType.values:
        raise ValueError(KOLTUK_GECERSIZ)
    kisi = uyelikler.kisi_aktif(person)
    karar = _karar_dogrula(donem, representative_decision)
    if _ayni_satir_var(donem, kisi, OrganType.TEMSILCI, representation):
        raise ValueError(AYNI_TEMSIL_VAR)
    uyelik = _olustur(
        donem,
        kisi,
        organ=OrganType.TEMSILCI,
        representation=representation,
        seat_type=seat_type,
        elected_by=_kanal(representation),
        start_date=start_date or timezone.localdate(),
        representative_decision=karar,
    )
    _temsil_denetimi(uyelik, donem, gerekce=gerekce)
    denetim_izi.degisiklik(uyelik, onceki=None)
    return uyelik


def _dusur(uyelik: OrganMembership, *, gun: date) -> None:
    """Başkanlığı biten kişinin kendiliğinden üyeliği düşer (`DIGER`; gün başkanlığın bittiği gündür:
    görev bölümü ya da başkanlık kaydının düşme günü)."""
    onceki = denetim_izi.anlik(uyelik)
    uyelik.status = MembershipStatus.DUSTU
    uyelik.drop_kind = DropKind.DIGER
    uyelik.end_date = max(gun, uyelik.start_date) if uyelik.start_date else gun
    uyelik.updated_by_id = iz.yazar_hesabi()
    uyelik.save(update_fields=["status", "drop_kind", "end_date", "updated_at", "updated_by"])
    denetim_izi.degisiklik(uyelik, onceki=onceki)


def _iptal_et(uyelik: OrganMembership) -> None:
    """İptal edilen başkanlık kaydının kendiliğinden satırı da iptal olur (hiç olmamış sayılır)."""
    onceki = denetim_izi.anlik(uyelik)
    uyelik.status = MembershipStatus.IPTAL
    uyelik.cancel_reason = BASKANLIK_IPTAL_GEREKCESI
    uyelik.updated_by_id = iz.yazar_hesabi()
    uyelik.save(update_fields=["status", "cancel_reason", "updated_at", "updated_by"])
    denetim_izi.degisiklik(uyelik, onceki=onceki)


def _baskanin_satirlari(donem: OabTerm, kisi_id: int) -> list[OrganMembership]:
    return list(
        OrganMembership.objects.filter(
            term=donem,
            person_id=kisi_id,
            organ=OrganType.TEMSILCI,
            representation__in=BASKANIN_KOMISYONLARI,
            elected_by=ElectedBy.KENDILIGINDEN,
            status=MembershipStatus.SECILDI,
        ).order_by("pk")
    )


def baskan_satirlarini_kapat(
    donem: OabTerm, kisi_id: int, *, gun: date, iptal: bool = False
) -> list[OrganMembership]:
    """Başkanlık kaydı düşen (`DIGER`, düşme günüyle) ya da iptal edilen (`IPTAL`) kişinin üç
    komisyondaki kendiliğinden satırları (modül başlığı). Çağıran üyelik geçişidir (işlemi ve kapıları
    onundur)."""
    satirlar = _baskanin_satirlari(donem, kisi_id)
    for satir in satirlar:
        if iptal:
            _iptal_et(satir)
        else:
            _dusur(satir, gun=gun)
    return satirlar


def baskan_temsilciliklerini_esitle(
    donem: OabTerm,
    baskan: OrganMembership | None,
    *,
    gun: date,
    birakanlar: Iterable[int] = (),
) -> list[OrganMembership]:
    """Görev bölümünün başkanı, kendiliğinden üye olduğu üç komisyona yazılır (E03); başkanlığı bırakan
    önceki başkanın bu satırları düşer (başkan atanmadıysa yalnız düşme). Başkanın aynı dönemde düşmüş
    satırı varsa yenisi açılmaz (tekil kısıt); çizelge satırı eksik gösterir. Çağıran görev bölümüdür
    (işlemi ve kapıları onundur)."""
    birakan_kume = set(birakanlar) - ({baskan.person_id} if baskan is not None else set())
    acilanlar: list[OrganMembership] = []
    for temsil in BASKANIN_KOMISYONLARI:
        for satir in _secilmis_temsilciler(donem, temsil):
            if satir.person_id in birakan_kume:
                _dusur(satir, gun=gun)
        if baskan is None or _ayni_satir_var(donem, baskan.person, OrganType.TEMSILCI, temsil):
            continue
        uyelik = _olustur(
            donem,
            baskan.person,
            organ=OrganType.TEMSILCI,
            representation=temsil,
            seat_type=SeatType.ASIL,
            elected_by=ElectedBy.KENDILIGINDEN,
            start_date=gun,
        )
        _temsil_denetimi(uyelik, donem, gerekce=None)
        denetim_izi.degisiklik(uyelik, onceki=None)
        acilanlar.append(uyelik)
    return acilanlar


@transaction.atomic
def alim_komisyonu_uyesi_ekle(
    *,
    term: OabTerm,
    person: OabPerson,
    expertise_required: bool = False,
    start_date: date | None = None,
) -> OrganMembership:
    """Alım komisyonu üyesi (`OLUSTUR`; yönetim kurulu kararıyla, seçilmiş). En az üç kişi kadro
    uyarısıdır; yazım engellenmez (modül başlığı "Alım komisyonu")."""
    donem = _baslangic(term)
    kisi = uyelikler.kisi_aktif(person)
    if _ayni_satir_var(donem, kisi, OrganType.ALIM_KOMISYONU, ""):
        raise ValueError(AYNI_KOMISYON_UYESI_VAR)
    uyelik = _olustur(
        donem,
        kisi,
        organ=OrganType.ALIM_KOMISYONU,
        representation="",
        seat_type=SeatType.ASIL,
        elected_by=ElectedBy.YK_KARARI,
        start_date=start_date or timezone.localdate(),
        expertise_required=expertise_required,
    )
    denetim_izi.degisiklik(uyelik, onceki=None)
    return uyelik


# ---------------------------------------------------------------------------
# Temsilciler çizelgesi (okuma; E03'ün tek kaynağı)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TemsilciSatiri:
    """Çizelgenin bir satırı: temsil türü, kuralı, temsilcileri ve durumu (yazmaz, gerekçe istemez)."""

    representation: str
    ad: str
    kural: str | None
    uyeler: list[OrganMembership]
    durum: str | None = None
    metin: str = ""
    notlar: list[str] = field(default_factory=list)


def _satir_sonucu(
    donem: OabTerm, temsil: str, uyeler: list[OrganMembership], *, gun: date, okul: dict[str, Any]
) -> DenetimSonucu | None:
    kural_id = TEMSIL_KURALLARI.get(temsil)
    if kural_id is None or temsil in YALNIZ_KAYIT:
        return None
    if temsil in BASKANIN_KOMISYONLARI:
        gozlenen = _baskan_gozlenen(donem, uyeler)
    elif temsil == Representation.KANTIN_DENETIM_KOMISYONU:
        gozlenen = _kantin_gozlenen(donem)
    else:
        try:
            deger = kural_kaydi(kural_id, tarih=gun, donem=donem)["deger"]
        except YururlukteDegerYok:
            return None
        gozlenen, _ = _sayi_gozlenen(donem, temsil, deger)
    return paket_denetle(kural_id, gozlenen, tarih=gun, donem=donem, okul=okul)


def _gorunur(
    donem: OabTerm,
    temsil: str,
    uyeler: list[OrganMembership],
    *,
    gun: date,
    okul: dict[str, Any],
    kampuste: bool,
) -> bool:
    if uyeler:
        return True
    if temsil in YALNIZ_KAYIT or temsil == Representation.DIGER:
        return False
    if temsil == Representation.KAMPUS_YONETIMI:
        return kampuste
    kural_id = TEMSIL_KURALLARI.get(temsil)
    if kural_id is None:
        return False
    return _kosul(kural_id, donem=donem, gun=gun, okul=okul) is not False


def temsilci_cizelgesi(donem: OabTerm, *, tarih: date | None = None) -> list[TemsilciSatiri]:
    """Temsilciler çizelgesi (tasarım §6.4.4, E03): satırlar kademe ve kantin koşulundan, kampüs
    satırı okul kartından; pay dağıtım komisyonu ve "diğer" yalnız kayıt varsa. RPD satırı komisyonun
    öteki üyelerini öğretmenler kurulunun belirlediğini not eder (RPD 16/5; kuralın yorumu)."""
    gun = tarih or timezone.localdate()
    okul = okul_baglami()
    kampuste = bool(SchoolConfig.load().in_campus)
    satirlar: list[TemsilciSatiri] = []
    for temsil in Representation:
        uyeler = _secilmis_temsilciler(donem, temsil)
        if not _gorunur(donem, temsil, uyeler, gun=gun, okul=okul, kampuste=kampuste):
            continue
        sonuc = _satir_sonucu(donem, temsil, uyeler, gun=gun, okul=okul)
        notlar: list[str] = []
        kural_id = TEMSIL_KURALLARI.get(temsil)
        if temsil == Representation.RPD_YURUTME_KOMISYONU and kural_id is not None:
            try:
                yorum = kural_kaydi(kural_id, tarih=gun, donem=donem).get("yorum")
            except YururlukteDegerYok:
                yorum = None
            if yorum:
                notlar.append(str(yorum))
        durum = None if sonuc is None else sonuc["durum"]
        metin = atifli_metin(sonuc) if sonuc is not None and durum in ("uyari", "eksik") else ""
        satirlar.append(
            TemsilciSatiri(
                representation=str(temsil),
                ad=str(temsil.label),
                kural=kural_id,
                uyeler=uyeler,
                durum=durum,
                metin=metin,
                notlar=notlar,
            )
        )
    return satirlar
