"""Organ üyeliği: kayıt, seçilme, koltuk uygunluğu, kadro ve seçilme sayacı (tasarım §5.2.2, §6.4.2,
§6.4.3; §12.A `assign_membership`, `promote_membership`, `validate_membership_composition`,
`count_prior_baskan_terms` UYARLA; plan F1c-5).

F1c'nin 5. adımı yönetim kurulu ve Denetleme Kurulu üyeliğini yazar. Görev bölümü (`gorev_bolumu`),
yedek çağrısı, düşme, iptal ve görev alma engeli (`uyelik_gecisleri`), temsilciler ve alım komisyonu
(`temsilciler`) 6. adımdadır ve buradaki denetimleri ortak yardımcılarla kullanır; divan ve genel
kurul akışı F2'de gelir.

YAZMA YOLLARI (hepsi `yazma_kapisi()` ile başlar, kural denetimini `uyum.denetle` ile yapar):

* `assign_membership`: kaydı açar. Genel kurul seçiminde kayıt o genel kurulun ADAYIDIR (`ADAY`);
  seçilen yalnız aynı kaydın `ADAY` → `SECILDI` geçişiyle olur (tek kaynak — sert; tasarım §5.2.2).
  Genel kurul dışı kanalda (öğretmenler kurulu, il/ilçe MEM görevlendirmesi) ve geçiş kurulumunda
  devralınan (`DEVRALINAN`) üyelik doğrudan `SECILDI` açılır; devralınanda aday şartı aranmaz.
* `elect_membership`: `ADAY` → `SECILDI` (genel kurulun seçim sonucu; ekranı F2'nin sihirbazındadır).
* `update_membership`: kişisiz ayrıntılar (oy, yedek sırası, dayanak notu, MEM onay no, beyan günleri,
  DK öğretmeninin başka kurumdaki görevlendirme günleri, alım komisyonunda uzmanlık işareti).
* `dk_baskanlik_denetimi`: Denetleme Kurulu başkanlık sayacı; görev bölümünde koşar (aşağıda "Seçilme
  sayacı"), uyarı özeti değişirse izini yazar.

KOLTUK UYGUNLUĞU (tasarım §5.2.2 tablosu; CLAUDE.md altın kural 3):

* Yönetim kurulu: veli (`is_parent`; veli olan öğretmen ve idareci dâhil), 18 yaşını doldurduğu
  beyan edilmiş kursiyer ya da hayırsever (`yonetim_kurulu.uye_turleri`, SERT — mevzuatın saymadığı
  kişi türü). Okul müdürü (`is_principal`) veli olsa da giremez (`okul_muduru_uye_olamaz`, SERT —
  kullanıcı kararı KE-15).
* Denetleme Kurulu: veli koltuğu veli ya da 18 yaşını doldurmuş kursiyer, hayırsever DEĞİL; öğretmen
  koltuğu öğretmen (`denetleme_kurulu.koltuklar`, SERT). Bir grubun asıl ya da yedek koltukları
  doluysa fazlası da aynı kuralla SERT'tir (md. 14/1'in bileşimi). Öğretmen koltuğuna il/ilçe MEM
  görevlendirmesiyle gelen başka okulun öğretmeninin onay no'su girilmemişse EKSİK (tamamlanacak;
  gerekçe istemez, altın kural 3).
* Bir kişi aynı dönemde aynı kurulda tek koltuk tutar (SERT — hesap bütünlüğü; kullanıcı kararı
  10.11.2026, plan F1c 5. adım notları): Denetleme Kurulunun veli ve öğretmen koltuğu ya da yönetim
  kurulunun asıl ve yedek koltuğu aynı kişide olamaz, kadro ve yeter sayı kişiyi bir sayar. Koltuk
  seçilmiş kayıttır (`SECILDI`): denetim kayıt seçilmiş açılırken ve aday seçilirken koşar. Aday
  kaydı koltuk değildir (seçilmeyen aday kaydı aday kalır; aynı kişi dönemin başka genel kurulunda
  yeniden aday olabilir, md. 13/8). Düşmüş kayıt koltuk değildir: olağanüstü genel kurul aynı dönemde
  yeni kurul seçer, görevdeki eski üyelikler düşer (`OLAGANUSTU_GK_SECIMI`, tasarım §7.1) ve eski üye
  yeniden seçilebilir; yedek çağrısı ise yeni kayıt değil, aynı kaydın `promoted_on`'udur (§7.2).
  İptal kaydı hiç olmamıştır. Kural yalnız yönetim kurulunda ve Denetleme Kurulunda uygulanır:
  temsilcide temsil türleri ayrı koltuktur (genel kurulsuz tekil kısıt `representation` ile ayırır).
* Aynı kişi aynı dönemde yönetim kurulunda ve Denetleme Kurulunda olamaz (`yk_uyesi_olamaz`, SERT —
  kullanıcı kararı A-2). Öteki kurulda aynı dönemde seçilmiş ya da seçilip düşmüş üyelik
  (`SECILDI`, `DUSTU`) engeldir; kararın lafzı dönemi ölçüt alır, görevdeki üyeliği değil. Aday
  kaydı (seçilmesi yeniden denetlenir) ve iptal edilmiş kayıt (hiç olmamış kayıt) engel değildir.
* GÖREV SEÇİMDE VERİLMEZ (md. 12/3: yönetim kurulu görevlerini "üyeleri arasından" görev bölümünde
  seçer; md. 14/1: Denetleme Kurulunun asıl üyeleri "aralarından bir başkan seçerek" görev bölümü
  yapar; tasarım §7.2). Programda açılan kayıt (`PROGRAM`) yalnız `UYE`'dir; görev 6. adımın görev
  bölümü yolundan yazılır. Görevli kayıt yalnız devralınan asıldır: geçişte görev bölümü yapılmıştır,
  dayanağı `evidence_note`'tadır (tasarım §7.9 adım 2). Yedek üyeye görev hiç verilmez: görev bölümünü
  asıl üyeler yapar, yedek çağrılınca asıl olur.
* Yönetim kurulunda başkan, başkan yardımcısı, muhasip ve sekreter görevleri tekildir
  (`yonetim_kurulu.gorevler`, SERT — hesap bütünlüğü; görevdeki seçilmiş asıllar arasında sayılır).
* Kadro SAYILARI (5+5, 3+3) yazımı engellemez: kadro okumasında uyarıdır (`kadro_uyarilari`); genel
  kurul yeter sayısının tabanını etkilemez (sabit 16, tasarım §5.2.3). Görevdeki asıllar arasında
  başkan yoksa (görev bölümü başkansız yapılmış, henüz yapılmamış ya da başkan düşmüş) kadro okumasında
  eksiktir (`kadro_uyarilari`; gerekçe istemez, yazım engellenmez; plan F1c 6. adım notları).

SEÇİLME SAYACI (md. 12/4 "en fazla dört defa seçilebilir", md. 14/3 "üç defa"; §15 B-12; D33):
yönetim kurulunda başkan ve üyeler TEK sayaçtır, asıl ve yedek her seçilme sayılır; Denetleme
Kurulunda yalnız başkanlık sayılır. Sayaç = programın kayıtları (`SECILDI` ve `DUSTU`; `ADAY` ve
`IPTAL` hariç; `source = PROGRAM`) + kişinin `external_*` beyanı. `DEVRALINAN` kayıt sayaç dışıdır:
beyan görevdeki seçimi içerir (plan F1c kararları). Beyan "bilinmiyor"sa (`None`) sayaç EKSİK'tir,
engel değildir (R5); bilinen kayıtlar sınırı zaten aşıyorsa uyarıdır. Sınırın üstündeki seçim uyarı +
gerekçedir. Yönetim kurulunda denetim programda yapılan seçilmede koşar (`SECILDI` + `PROGRAM`).
Denetleme Kurulu başkanını seçim değil görev bölümü belirler (md. 14/1): başkanlık sayacı seçim anında
koşmaz, görev bölümünde koşar (`dk_baskanlik_denetimi`; çağıran yol 6. adımın DK görev bölümüdür, M8).
Her görev bölümündeki başkan seçimi bir seçilmedir (kullanıcı kararı 10.11.2026; `dk_baskanlik_sayisi`).

GÖREV ALMA ENGELİ (md. 12/4-5, 14/7; tasarım §5.2.2): engel işaretli (`eligibility_bar = VAR`) adayın
seçimi uyarı + gerekçedir: dayanak suçsa `uyelik.suc_engeli`, başka birlik yönetimiyse
`yonetim_kurulu.tek_birlik` (yalnız yönetim kurulunda). Görevdeki üyede engel düşürme önerisidir
(`uyelik_gecisleri.oneriler`). Okulun beyan uygulaması işaretlenmediyse mevzuat uyarısı yoktur.

Olay günü (kuralın yürürlüğü) seçilme günüdür (`start_date`); adayda genel kurulun birinci
toplantısının yerel günü, o da yoksa bugünün yerel günü (`timezone.localdate()`).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any, Final

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.oab import selectors
from apps.oab.kurallar import VERI_YOK, YururlukteDegerYok, kural, yazma_kapisi
from apps.oab.kurallar.erisim import DenetimSonucu
from apps.oab.kurallar.erisim import denetle as paket_denetle
from apps.oab.models import (
    AssemblyKind,
    AssemblyStatus,
    ElectedBy,
    EligibilityBar,
    EligibilityBarBasis,
    GeneralAssembly,
    MembershipRole,
    MembershipSource,
    MembershipStatus,
    OabPerson,
    OabTerm,
    OrganMembership,
    OrganType,
    PersonKind,
    PersonStatus,
    SeatGroup,
    SeatType,
    UyelikDurumuGecersiz,
)
from apps.oab.services import donem_kilidi, iz, takvim, uyum
from apps.okul import denetim_izi, erisim_gunlugu
from apps.okul.models import AccessKind
from apps.okul.services import app_password
from shared.crypto import is_corrupt

#: Bu adımda kaydı yazılan organlar; öteki organlar sonraki adımların akışlarıyla yazılır.
YAZILAN_ORGANLAR: Final = frozenset({OrganType.YONETIM_KURULU, OrganType.DENETLEME_KURULU})

#: Organ içi görevler (yönetim kurulu md. 12/3; Denetleme Kurulu md. 14/1 "aralarından bir başkan").
ORGAN_GOREVLERI: Final[dict[str, frozenset[str]]] = {
    OrganType.YONETIM_KURULU: frozenset(
        {
            MembershipRole.BASKAN,
            MembershipRole.BASKAN_YARDIMCISI,
            MembershipRole.MUHASIP,
            MembershipRole.SEKRETER,
            MembershipRole.UYE,
        }
    ),
    OrganType.DENETLEME_KURULU: frozenset({MembershipRole.BASKAN, MembershipRole.UYE}),
}

#: Seçim kanalları: yönetim kurulunu ve Denetleme Kurulunun veli koltuğunu genel kurul, öğretmen
#: koltuklarını öğretmenler kurulu seçer; okulda yeterli öğretmen yoksa il/ilçe MEM onayıyla başka
#: okulun öğretmeni görevlendirilir (md. 12/1, 14/1; `denetleme_kurulu.koltuklar`).
SECIM_KANALLARI: Final[dict[tuple[str, str], frozenset[str]]] = {
    (OrganType.YONETIM_KURULU, ""): frozenset({ElectedBy.GENEL_KURUL}),
    (OrganType.DENETLEME_KURULU, SeatGroup.VELI): frozenset({ElectedBy.GENEL_KURUL}),
    (OrganType.DENETLEME_KURULU, SeatGroup.OGRETMEN): frozenset(
        {ElectedBy.OGRETMENLER_KURULU, ElectedBy.MEM_GOREVLENDIRME}
    ),
}

#: Seçilme sayacına giren durumlar (§15 B-12): seçilmiş ve sonradan düşmüş kayıt sayılır.
SAYAC_DURUMLARI: Final = (MembershipStatus.SECILDI, MembershipStatus.DUSTU)

#: Aynı dönemde kurulda bulunmuş sayılan durumlar (kullanıcı kararı A-2: "aynı dönemde"). Sayaçla
#: aynı küme olsa da anlamı ayrıdır: aday kaydı seçilince yeniden denetlenir, iptal kaydı hiç olmamıştır.
KURULDA_BULUNMUS: Final = (MembershipStatus.SECILDI, MembershipStatus.DUSTU)

#: Bir kişinin aynı dönemde tek koltuk tuttuğu kurullar (kullanıcı kararı 10.11.2026; hesap
#: bütünlüğü). Temsilcide farklı temsil türleri ayrı koltuktur; kural yalnız bu iki kurulda uygulanır.
TEK_KOLTUKLU_KURULLAR: Final = frozenset({OrganType.YONETIM_KURULU, OrganType.DENETLEME_KURULU})

#: Güncellemeyle değişebilen kişisiz alanlar; görev bölümü, yedek çağrısı, düşme, iptal ve görev alma
#: engeli ayrı yoldur (6. adım).
GUNCELLENEBILIR: Final = frozenset(
    {
        "votes",
        "seat_order",
        "evidence_note",
        "mem_approval_no",
        "eligibility_declared_on",
        "single_birlik_declared_on",
        "external_assignment_start",
        "external_assignment_end",
        "expertise_required",
    }
)


#: Uyarı özetine giren denetim sonuçları (O3 `rule_warnings`).
_OZETLENEN: Final = frozenset({"eksik", "uyari"})

#: Koltuk grubunun kişisi değil: kural tablosunda olmayan grup anahtarı (gözlenen bileşim).
_GRUP_DISI: Final = "GRUP_DISI"
#: Yönetim kurulu kişi türlerinin hiçbirine girmeyen kişi (`uye_turleri` listesinde yok).
_TUR_DISI: Final = "TUR_DISI"

ORGAN_BU_YOLDAN_YAZILMAZ = "Bu organın üyeliği bu kayıtla yazılmaz; yalnız yönetim kurulu ve Denetleme Kurulu üyeliği yazılır."
KISI_PASIF = "Pasif kişi organa eklenemez; önce kişi kaydını etkinleştirin."
KOLTUK_GRUBU_GEREKLI = (
    "Denetleme Kurulu üyeliğinde koltuk grubu (veli ya da öğretmen) seçilmelidir."
)
KOLTUK_GRUBU_YALNIZ_DK = "Koltuk grubu yalnız Denetleme Kurulu üyeliğinde verilir."
GOREV_ORGANDA_YOK = "Bu görev bu organda yoktur."
GOREV_SECIMDE_VERILMEZ = (
    "Görev seçimde verilmez; kurul görevlerini görev bölümünde asıl üyeleri arasından seçer."
)
GOREV_YALNIZ_ASILDA = "Görev yalnız asıl üyeye verilir; yedek üye çağrılmadan görev almaz."
KANAL_GECERSIZ = "Bu koltuğa bu seçim kanalıyla üye gelmez."
GENEL_KURUL_GEREKLI = "Genel kurulda seçilen üyenin kaydı o genel kurula bağlanır."
GENEL_KURUL_BAGI_YALNIZ_SECIMDE = "Genel kurul bağı yalnız genel kurul seçiminde verilir."
GENEL_KURUL_DONEMI_TUTMUYOR = (
    "Genel kurulun seçtiği üye, genel kurulun açtığı döneme (olağanüstü genel kurulda kendi "
    "dönemine) yazılır."
)
GENEL_KURUL_IPTAL = "İptal edilmiş genel kurula üye yazılmaz."
YEDEK_SIRASI_YALNIZ_YEDEKTE = "Yedek sırası yalnız yedek üyede verilir."
MEM_ONAYI_YALNIZ_OGRETMEN_KOLTUGUNDA = (
    "MEM onay no yalnız Denetleme Kurulunun öğretmen koltuğunda verilir."
)
AYNI_UYELIK_VAR = "Bu kişinin bu dönemde bu organda üyelik kaydı zaten var."
TEK_KOLTUK = (
    "Bu kişi bu dönemde bu kurula zaten seçilmiş; bir kişi aynı kurulda tek koltuk tutar. Kurulun "
    "üye sayısı ve yeter sayısı kişi başına sayıldığından ikinci koltuk bu hesabı bozar."
)
YALNIZ_ADAY_SECILIR = "Yalnız aday kaydı seçilmiş olarak işaretlenir."
DEGISMEZ_UYELIK = "Düşmüş ya da iptal edilmiş üyelik kaydı değiştirilemez."
GOREVLENDIRME_YALNIZ_DK_OGRETMENINDE = (
    "Başka kurumda görevlendirme günleri yalnız Denetleme Kurulunun öğretmen koltuğunda verilir."
)
GOREVLENDIRME_SIRASI = "Görevlendirmenin bitişi başlangıcından önce olamaz."
UZMANLIK_YALNIZ_ALIM_KOMISYONUNDA = "Uzmanlık işareti yalnız alım komisyonu üyeliğinde verilir."


# ---------------------------------------------------------------------------
# Kişinin koltuğa uygunluğu
# ---------------------------------------------------------------------------
def _kursiyer_yetiskin(kisi: OabPerson) -> bool:
    return bool(kisi.kind == PersonKind.KURSIYER and kisi.adult_declared)


def yk_uye_turu(kisi: OabPerson) -> str:
    """Yönetim kurulu uygunluğunda kişinin türü (`yonetim_kurulu.uye_turleri` listesiyle karşılaştırılır).

    Veli işareti türden önce gelir: veli olan öğretmen ve idareci velidir. 18 yaşını doldurduğu beyan
    edilmemiş kursiyer, veli olmayan öğretmen, idareci ve diğer kişiler listede olmayan türdür.
    """
    if kisi.is_parent:
        return str(PersonKind.VELI)
    if _kursiyer_yetiskin(kisi):
        return str(PersonKind.KURSIYER)
    if kisi.kind == PersonKind.HAYIRSEVER:
        return str(PersonKind.HAYIRSEVER)
    return _TUR_DISI


def dk_koltuguna_uygun(kisi: OabPerson, seat_group: str) -> bool:
    """Denetleme Kurulu koltuk grubuna uygun mu? Veli koltuğu veli ya da 18 yaşını doldurmuş
    kursiyer (hayırsever değil; §12.A S-8 düzeltmesi), öğretmen koltuğu öğretmen (md. 14/1)."""
    if seat_group == SeatGroup.VELI:
        return bool(kisi.is_parent) or _kursiyer_yetiskin(kisi)
    if seat_group == SeatGroup.OGRETMEN:
        return bool(kisi.kind == PersonKind.OGRETMEN)
    return False


# ---------------------------------------------------------------------------
# Seçilme sayacı (§15 B-12)
# ---------------------------------------------------------------------------
def _sayilan(kisi: OabPerson) -> QuerySet[OrganMembership]:
    return OrganMembership.objects.filter(
        person=kisi, status__in=SAYAC_DURUMLARI, source=MembershipSource.PROGRAM
    )


def yk_secilme_sayisi(kisi: OabPerson) -> int:
    """Programdaki yönetim kurulu seçilmeleri: başkan ve üye tek sayaç, asıl ve yedek her seçilme."""
    return _sayilan(kisi).filter(organ=OrganType.YONETIM_KURULU).count()


def dk_baskanlik_sayisi(kisi: OabPerson) -> int:
    """Programdaki Denetleme Kurulu başkan seçilmeleri (yalnız başkanlık sayılır; md. 14/3).

    Sayılan seçilmedir, dönem sonundaki görev değil: her görev bölümündeki başkan seçimi bir seçilmedir
    (kullanıcı kararı 10.11.2026; aynı dönemde A → B → A dönüşünde A iki kez sayılır); görevdeki
    başkanın yeniden başkan seçilmesi (A → A) yeni seçilme değildir. Seçilmeleri
    üyeliğin `chair_elections` sayısı tutar; dönem içi görev değişimi onu azaltmaz. Görevi `BASKAN`
    olup sayısı sıfır olan program kaydı (görev bölümünden geçmemiş eski kayıt) bir seçilme sayılır."""
    toplam = 0
    for role, sayi in (
        _sayilan(kisi)
        .filter(organ=OrganType.DENETLEME_KURULU)
        .values_list("role", "chair_elections")
    ):
        toplam += max(sayi, 1 if role == MembershipRole.BASKAN else 0)
    return toplam


def secilme_sayaci(kisi: OabPerson, organ: str) -> int | None:
    """Program kayıtları + programdan önceki beyan; beyan "bilinmiyor"sa `None` (eksik)."""
    if organ == OrganType.YONETIM_KURULU:
        program, beyan = yk_secilme_sayisi(kisi), kisi.external_yk_terms
    elif organ == OrganType.DENETLEME_KURULU:
        program, beyan = dk_baskanlik_sayisi(kisi), kisi.external_dk_chair_terms
    else:
        raise ValueError(ORGAN_BU_YOLDAN_YAZILMAZ)
    return None if beyan is None else program + beyan


def _sayac_gozlenen(kural_sonucu: DenetimSonucu, program: int, beyan: int | None) -> Any:
    """Sayaç gözlenen değeri: beyan bilinmiyorsa eksik, ama bilinen kayıtlar sınırı aşıyorsa sayı."""
    if beyan is not None:
        return program + beyan
    return program if kural_sonucu["durum"] == "uyari" else VERI_YOK


# ---------------------------------------------------------------------------
# Denetimler
# ---------------------------------------------------------------------------
def _olay_gunu(uyelik: OrganMembership) -> date:
    if uyelik.start_date is not None:
        return uyelik.start_date
    if uyelik.assembly is not None and uyelik.assembly.first_meeting_at is not None:
        return timezone.localdate(uyelik.assembly.first_meeting_at)
    return timezone.localdate()


def _iki_kurulda(uyelik: OrganMembership) -> bool:
    """Kişi aynı dönemde öteki kurulda bulundu mu (seçilmiş ya da seçilip düşmüş)? (kullanıcı kararı
    A-2; denetleyen ile denetlenen ayrılığı, md. 14/4: düşen yönetim kurulu üyesi kendi dönemini
    denetleyemez.)"""
    oteki = (
        OrganType.DENETLEME_KURULU
        if uyelik.organ == OrganType.YONETIM_KURULU
        else OrganType.YONETIM_KURULU
    )
    return OrganMembership.objects.filter(
        term_id=uyelik.term_id,
        person_id=uyelik.person_id,
        organ=oteki,
        status__in=KURULDA_BULUNMUS,
    ).exists()


def _ikinci_koltuk(uyelik: OrganMembership) -> bool:
    """Seçilmiş kayıt, kişinin bu dönemde bu kuruldaki ikinci seçilmiş kaydı mı? (tek koltuk; modül
    başlığı "Koltuk uygunluğu"). Aday, düşmüş ve iptal kaydı koltuk değildir."""
    if uyelik.organ not in TEK_KOLTUKLU_KURULLAR or uyelik.status != MembershipStatus.SECILDI:
        return False
    return (
        OrganMembership.objects.filter(
            term_id=uyelik.term_id,
            person_id=uyelik.person_id,
            organ=uyelik.organ,
            status=MembershipStatus.SECILDI,
        )
        .exclude(pk=uyelik.pk)
        .exists()
    )


def _gorevdeki_hucre(uyelik: OrganMembership) -> QuerySet[OrganMembership]:
    """Üyeliğin oturduğu hücrenin öteki seçilmiş üyeleri (yedekten çağrılan asıl hücresindedir)."""
    kayitlar = OrganMembership.objects.filter(
        term_id=uyelik.term_id,
        organ=uyelik.organ,
        seat_group=uyelik.seat_group,
        status=MembershipStatus.SECILDI,
    ).exclude(pk=uyelik.pk)
    if uyelik.seat_type == SeatType.ASIL or uyelik.promoted_on is not None:
        return kayitlar.filter(Q(seat_type=SeatType.ASIL) | Q(promoted_on__isnull=False))
    return kayitlar.filter(seat_type=SeatType.YEDEK, promoted_on__isnull=True)


def _dk_koltuk_gozlenen(uyelik: OrganMembership, deger: dict[str, Any]) -> Any:
    """`denetleme_kurulu.koltuklar` için gözlenen bileşim (değer kopyalanır, paket değişmez).

    Uygun koltukta tablonun kendisi döner (uygun). Kişi grubun türünde değilse tabloda olmayan grup
    eklenir, seçilmiş üye dolu hücreye oturuyorsa hücre gözlenen sayıyla yazılır: ikisi de tabloyla
    tutmaz (sert). Uygun koltukta MEM görevlendirmesinin onay no'su yoksa veri eksiktir.
    """
    if not deger:
        return VERI_YOK  # olay günündeki metin yok: `denetle` "denetlenmedi" der, satır açılmaz
    asil = uyelik.seat_type == SeatType.ASIL or uyelik.promoted_on is not None
    hucre = str(SeatType.ASIL if asil else SeatType.YEDEK)
    if not dk_koltuguna_uygun(uyelik.person, uyelik.seat_group):
        return {**deger, _GRUP_DISI: {hucre: 1}}
    if uyelik.status == MembershipStatus.SECILDI:
        dolu = _gorevdeki_hucre(uyelik).count() + 1
        if dolu > deger[uyelik.seat_group][hucre]:
            return {**deger, uyelik.seat_group: {**deger[uyelik.seat_group], hucre: dolu}}
    if uyelik.elected_by == ElectedBy.MEM_GOREVLENDIRME and not uyelik.mem_approval_no:
        return VERI_YOK
    return deger


def _uyari_ozeti(kural_id: str, sonuc: DenetimSonucu) -> dict[str, Any]:
    return {
        "kural": kural_id,
        "atif": sonuc["atif"],
        "mesaj": sonuc["mesaj"],
        "durum": sonuc["durum"],
        "paket": sonuc["paket"],
        "rev": sonuc["rev"],
    }


class _Denetim:
    """Bir üyeliğin denetim turu: sonuçları uyarı özetine (`rule_warnings`) toplar."""

    def __init__(
        self,
        uyelik: OrganMembership,
        donem: OabTerm,
        *,
        gerekce: uyum.Gerekce | None,
    ) -> None:
        self.uyelik = uyelik
        self.donem = donem
        self.gerekce = gerekce
        self.tarih = _olay_gunu(uyelik)
        self.hazirlik = uyelik.elected_by == ElectedBy.GENEL_KURUL
        self.sonuclar: dict[str, DenetimSonucu] = {}

    def kaydet(self, kural_id: str, sonuc: uyum.UyumSonucu) -> None:
        self.sonuclar[kural_id] = sonuc.sonuc

    def ortak(self) -> dict[str, Any]:
        return {
            "donem": self.donem,
            "konu": self.uyelik,
            "tarih": self.tarih,
            "gerekce": self.gerekce,
            "hazirlik_yazimi": self.hazirlik,
        }

    def ozet(self, onceki: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Bu turda denetlenen kuralların eski satırları atılır, eksik ve uyarı olanlar eklenir."""
        kalan = [satir for satir in onceki if satir.get("kural") not in self.sonuclar]
        yeni = [
            _uyari_ozeti(kural_id, sonuc)
            for kural_id, sonuc in self.sonuclar.items()
            if sonuc["durum"] in _OZETLENEN
        ]
        return [*kalan, *yeni]


def _koltuk_denetimleri(d: _Denetim) -> None:
    """Tek koltuk (sert, hesap bütünlüğü; seçilmiş kayıtta), koltuk uygunluğu (sert) ve öteki kurul
    engeli; adayda da koşar. Tek koltuk kural paketinde değildir (mevzuat oranı değil, sayımın
    bütünlüğüdür): ret atıfsız Türkçe iletiyle 400 olur, işlem geri alınır."""
    uyelik, ortak = d.uyelik, d.ortak()
    if _ikinci_koltuk(uyelik):
        raise ValueError(TEK_KOLTUK)
    if uyelik.organ == OrganType.YONETIM_KURULU:
        d.kaydet(
            "yonetim_kurulu.uye_turleri",
            uyum.denetle("yonetim_kurulu.uye_turleri", yk_uye_turu(uyelik.person), **ortak),
        )
        d.kaydet(
            "yonetim_kurulu.okul_muduru_uye_olamaz",
            uyum.denetle(
                "yonetim_kurulu.okul_muduru_uye_olamaz", not uyelik.person.is_principal, **ortak
            ),
        )
    else:
        _dk_koltuk_denetimi(d)
    d.kaydet(
        "denetleme_kurulu.yk_uyesi_olamaz",
        uyum.denetle("denetleme_kurulu.yk_uyesi_olamaz", not _iki_kurulda(uyelik), **ortak),
    )


def _dk_koltuk_denetimi(d: _Denetim) -> None:
    try:
        deger = kural("denetleme_kurulu.koltuklar", tarih=d.tarih, donem=d.donem)
    except YururlukteDegerYok:
        deger = {}
    d.kaydet(
        "denetleme_kurulu.koltuklar",
        uyum.denetle(
            "denetleme_kurulu.koltuklar", _dk_koltuk_gozlenen(d.uyelik, deger), **d.ortak()
        ),
    )


def _gorev_tekilligi(d: _Denetim) -> None:
    """Yönetim kurulunun dört görevi görevdeki seçilmiş asıllar arasında tekildir (sert, hesap
    bütünlüğü). Yedeğe görev verilmez (`_yapiyi_dogrula`); asıl süzmesi yine de savunma olarak durur."""
    uyelik = d.uyelik
    if uyelik.organ != OrganType.YONETIM_KURULU or uyelik.status != MembershipStatus.SECILDI:
        return
    try:
        deger = kural("yonetim_kurulu.gorevler", tarih=d.tarih, donem=d.donem)
    except YururlukteDegerYok:
        return
    if uyelik.role not in deger:
        return
    sayi = OrganMembership.objects.filter(
        selectors.GOREVDEKI_ASIL,
        term_id=uyelik.term_id,
        organ=OrganType.YONETIM_KURULU,
        role=uyelik.role,
        status=MembershipStatus.SECILDI,
    ).count()
    d.kaydet(
        "yonetim_kurulu.gorevler",
        uyum.denetle("yonetim_kurulu.gorevler", {**deger, uyelik.role: sayi}, **d.ortak()),
    )


def _secilme_siniri(d: _Denetim) -> None:
    """Programda yapılan yönetim kurulu seçilmesinin sayacı (modül başlığı "Seçilme sayacı").

    Denetleme Kurulunda seçim sayaca girmez: sayılan başkanlıktır, başkanı görev bölümü belirler
    (`_dk_baskanlik_siniri`).
    """
    uyelik, kisi = d.uyelik, d.uyelik.person
    if uyelik.status != MembershipStatus.SECILDI or uyelik.source != MembershipSource.PROGRAM:
        return
    if uyelik.organ == OrganType.YONETIM_KURULU:
        program, beyan = yk_secilme_sayisi(kisi), kisi.external_yk_terms
        on = paket_denetle("yonetim_kurulu.secilme_siniri", program, tarih=d.tarih, donem=d.donem)
        d.kaydet(
            "yonetim_kurulu.secilme_siniri",
            uyum.denetle(
                "yonetim_kurulu.secilme_siniri", _sayac_gozlenen(on, program, beyan), **d.ortak()
            ),
        )


def _dk_baskanlik_siniri(d: _Denetim) -> None:
    """Denetleme Kurulu başkanlık sayacı (md. 14/3): programda görev bölümünde başkan olan asıl."""
    uyelik, kisi = d.uyelik, d.uyelik.person
    if (
        uyelik.organ == OrganType.DENETLEME_KURULU
        and uyelik.role == MembershipRole.BASKAN
        and uyelik.status == MembershipStatus.SECILDI
        and uyelik.source == MembershipSource.PROGRAM
        and selectors.gorevdeki_asil_mi(uyelik)
    ):
        program, beyan = dk_baskanlik_sayisi(kisi), kisi.external_dk_chair_terms
        on = paket_denetle(
            "denetleme_kurulu.baskan_secilme_siniri", program, tarih=d.tarih, donem=d.donem
        )
        d.kaydet(
            "denetleme_kurulu.baskan_secilme_siniri",
            uyum.denetle(
                "denetleme_kurulu.baskan_secilme_siniri",
                _sayac_gozlenen(on, program, beyan),
                **d.ortak(),
            ),
        )


#: Görev alma engelinin hüküm olduğu organlar (dayanak → organlar): suç engeli yönetim kurulu, alım
#: (harcama) komisyonu (md. 12/5) ve Denetleme Kurulu (md. 14/7); başka birlik yönetimi engeli yalnız
#: yönetim kurulu (md. 12/4 2. cümle).
ENGEL_ORGANLARI: Final[dict[str, frozenset[str]]] = {
    EligibilityBarBasis.SUC_12_5_14_7: frozenset(
        {OrganType.YONETIM_KURULU, OrganType.DENETLEME_KURULU, OrganType.ALIM_KOMISYONU}
    ),
    EligibilityBarBasis.TEK_BIRLIK_12_4: frozenset({OrganType.YONETIM_KURULU}),
}


def engel_hukum_mu(uyelik: OrganMembership) -> bool:
    """İşaretli görev alma engeli bu üyeliğin organında hüküm mü? (`ENGEL_ORGANLARI`). Seçim uyarısı
    (`_engel_denetimi`) ve düşürme önerisi (`uyelik_gecisleri.oneriler`) aynı ölçüyü kullanır.

    Dayanak programın kendi okumasıdır (kullanıcıya gösterilmez, erişim günlüğüne yazılmaz)."""
    if uyelik.eligibility_bar != EligibilityBar.VAR:
        return False
    return str(uyelik.organ) in ENGEL_ORGANLARI.get(str(uyelik.eligibility_bar_basis), frozenset())


def _engel_denetimi(d: _Denetim) -> None:
    """Görev alma engeli işaretli kaydın seçimi uyarı + gerekçedir (modül başlığı "Görev alma engeli").

    Engel organda hüküm değilse (`engel_hukum_mu`) satır açılmaz.
    """
    uyelik = d.uyelik
    if not engel_hukum_mu(uyelik):
        return
    dayanak = str(uyelik.eligibility_bar_basis)
    if dayanak == EligibilityBarBasis.SUC_12_5_14_7:
        d.kaydet("uyelik.suc_engeli", uyum.denetle("uyelik.suc_engeli", False, **d.ortak()))
    elif dayanak == EligibilityBarBasis.TEK_BIRLIK_12_4:
        d.kaydet(
            "yonetim_kurulu.tek_birlik",
            uyum.denetle("yonetim_kurulu.tek_birlik", False, **d.ortak()),
        )


def _denetle_ve_ozetle(d: _Denetim, *, secim: bool = False) -> None:
    """Bütün denetimler; sert ihlal ve gerekçesiz uyarı işlemi geri alır (APIException)."""
    _koltuk_denetimleri(d)
    _gorev_tekilligi(d)
    _secilme_siniri(d)
    if secim:
        _engel_denetimi(d)
    uyelik = d.uyelik
    ozet = d.ozet(list(uyelik.rule_warnings or []))
    if ozet != (uyelik.rule_warnings or []):
        uyelik.rule_warnings = ozet
        uyelik.save(update_fields=["rule_warnings", "updated_at"])


def ozet_hesapla(
    uyelik: OrganMembership, sonuclar: Mapping[str, DenetimSonucu]
) -> list[dict[str, Any]]:
    """Başka akışın denetim sonuçlarıyla kaydın yeni uyarı özeti (O3); YAZMAZ.

    Kaydı ve izini çağıran akış yazar (görev bölümü, yedek çağrısı, düşme, temsilci; 6. adım): iz
    satırı kaydın son hâlini mühürler.
    """
    d = _Denetim(uyelik, uyelik.term, gerekce=None)
    d.sonuclar = {**d.sonuclar, **sonuclar}
    return d.ozet(list(uyelik.rule_warnings or []))


def gorev_tekilligini_denetle(uyelik: OrganMembership) -> dict[str, DenetimSonucu]:
    """Görev bölümünün yazdığı görevin tekilliği (sert, hesap bütünlüğü; `_gorev_tekilligi`); özete
    işlenecek sonuçları döner (`ozet_hesapla`)."""
    d = _Denetim(_guncel(uyelik), uyelik.term, gerekce=None)
    _gorev_tekilligi(d)
    return d.sonuclar


def koltugu_denetle(
    uyelik: OrganMembership, *, gerekce: uyum.Gerekce | None = None
) -> dict[str, DenetimSonucu]:
    """Koltuk uygunluğunu yeniden denetler (yedekten çağrılan Denetleme Kurulu üyesi asıl hücresine
    oturur: hücre doluysa sert; 6. adımın yedek çağrısı); özete işlenecek sonuçları döner."""
    d = _Denetim(_guncel(uyelik), uyelik.term, gerekce=gerekce)
    _koltuk_denetimleri(d)
    return d.sonuclar


@transaction.atomic
def dk_baskanlik_denetimi(uyelik: OrganMembership, *, gerekce: uyum.Gerekce | None = None) -> None:
    """Denetleme Kurulu başkanlık sayacını denetler (md. 14/3; uyarı + gerekçe, eksik beyan EKSİK).

    Başkanı seçim değil görev bölümü belirler (md. 14/1), denetim de oradadır: çağıran yol 6. adımın
    DK görev bölümüdür (M8, `denetleme_kurulu` rolü; plan F1c-6 "DK başkan sınırı görev bölümünde
    denetlenir"). Görevi yazılmış güncel kayıt üstünde koşar; başkan olmayan, görevde olmayan ya da
    devralınan kayıtta satır açmaz. Gerekçesiz uyarı işlemi geri alır (APIException).
    """
    yazma_kapisi()
    guncel = _guncel(uyelik)
    onceki = denetim_izi.anlik(guncel)
    d = _Denetim(guncel, guncel.term, gerekce=gerekce)
    _dk_baskanlik_siniri(d)
    ozet = d.ozet(list(guncel.rule_warnings or []))
    if ozet != (guncel.rule_warnings or []):
        guncel.rule_warnings = ozet
        guncel.save(update_fields=["rule_warnings", "updated_at"])
        denetim_izi.degisiklik(guncel, onceki=onceki)  # özet değişmediyse boş iz satırı yazılmaz


# ---------------------------------------------------------------------------
# Yapısal doğrulama
# ---------------------------------------------------------------------------
def _genel_kurul_bagi(
    *, donem: OabTerm, assembly: GeneralAssembly | None, kanal: str, source: str
) -> None:
    if source == MembershipSource.PROGRAM and kanal == ElectedBy.GENEL_KURUL:
        if assembly is None:
            raise ValueError(GENEL_KURUL_GEREKLI)
        kurul = GeneralAssembly.objects.get(pk=assembly.pk)
        if kurul.status == AssemblyStatus.IPTAL:
            raise ValueError(GENEL_KURUL_IPTAL)
        donemi = kurul.term_id if kurul.kind == AssemblyKind.OLAGANUSTU else kurul.opens_term_id
        if donemi != donem.pk:
            raise ValueError(GENEL_KURUL_DONEMI_TUTMUYOR)
    elif assembly is not None:
        raise ValueError(GENEL_KURUL_BAGI_YALNIZ_SECIMDE)


def _yapiyi_dogrula(
    *,
    organ: str,
    seat_type: str,
    seat_group: str,
    role: str,
    elected_by: str,
    source: str,
    seat_order: int | None,
    mem_approval_no: str,
) -> None:
    if organ not in YAZILAN_ORGANLAR:
        raise ValueError(ORGAN_BU_YOLDAN_YAZILMAZ)
    if organ == OrganType.DENETLEME_KURULU and seat_group not in SeatGroup.values:
        raise ValueError(KOLTUK_GRUBU_GEREKLI)
    if organ != OrganType.DENETLEME_KURULU and seat_group:
        raise ValueError(KOLTUK_GRUBU_YALNIZ_DK)
    if role not in ORGAN_GOREVLERI[organ]:
        raise ValueError(GOREV_ORGANDA_YOK)
    if role != MembershipRole.UYE:
        # Görevi kurul görev bölümünde asıl üyeleri arasından seçer (md. 12/3, 14/1; tasarım §7.2).
        # Yeni kayıtta `promoted_on` boştur: yedek kayıt çağrılmamış yedektir, görev alamaz. Görevli
        # kayıt yalnız devralınan asıldır (geçişte görev bölümü yapılmıştır; tasarım §7.9 adım 2).
        if seat_type == SeatType.YEDEK:
            raise ValueError(GOREV_YALNIZ_ASILDA)
        if source != MembershipSource.DEVRALINAN:
            raise ValueError(GOREV_SECIMDE_VERILMEZ)
    if elected_by not in SECIM_KANALLARI[(organ, seat_group)]:
        raise ValueError(KANAL_GECERSIZ)
    if seat_order is not None and seat_type != SeatType.YEDEK:
        raise ValueError(YEDEK_SIRASI_YALNIZ_YEDEKTE)
    if mem_approval_no and (organ, seat_group) != (OrganType.DENETLEME_KURULU, SeatGroup.OGRETMEN):
        raise ValueError(MEM_ONAYI_YALNIZ_OGRETMEN_KOLTUGUNDA)


def kisi_aktif(kisi: OabPerson) -> OabPerson:
    """Kişinin güncel kaydı; pasif kişi organa eklenemez (temsilci ve alım komisyonu da)."""
    guncel = OabPerson.objects.get(pk=kisi.pk)
    if guncel.status != PersonStatus.AKTIF:
        raise ValueError(KISI_PASIF)
    return guncel


_kisi_aktif = kisi_aktif


def _ayni_uyelik_var(
    *, donem: OabTerm, kisi: OabPerson, organ: str, assembly: GeneralAssembly | None
) -> bool:
    """İki kısmi tekil kısıtın servis karşılığı (iletisi Türkçe olsun diye; kısıt yine bekler)."""
    kayitlar = OrganMembership.objects.filter(term=donem, person=kisi, organ=organ).exclude(
        status=MembershipStatus.IPTAL
    )
    if assembly is not None:
        return kayitlar.filter(assembly=assembly).exists()
    return kayitlar.filter(assembly__isnull=True, representation="").exists()


# ---------------------------------------------------------------------------
# Yazma yolları
# ---------------------------------------------------------------------------
@transaction.atomic
def assign_membership(
    *,
    term: OabTerm,
    person: OabPerson,
    organ: str,
    seat_type: str,
    elected_by: str,
    seat_group: str = "",
    role: str = MembershipRole.UYE,
    assembly: GeneralAssembly | None = None,
    source: str = MembershipSource.PROGRAM,
    start_date: date | None = None,
    votes: int | None = None,
    seat_order: int | None = None,
    evidence_note: str = "",
    mem_approval_no: str = "",
    eligibility_declared_on: date | None = None,
    single_birlik_declared_on: date | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> OrganMembership:
    """Üyelik kaydı açar (`OLUSTUR`): genel kurul seçiminde aday, öteki kanallarda seçilmiş."""
    yazma_kapisi()
    app_password.require_password_set()
    donem = OabTerm.objects.select_related("rule_package").get(pk=term.pk)
    if source not in MembershipSource.values:
        raise ValueError(ORGAN_BU_YOLDAN_YAZILMAZ)
    _yapiyi_dogrula(
        organ=organ,
        seat_type=seat_type,
        seat_group=seat_group,
        role=role,
        elected_by=elected_by,
        source=source,
        seat_order=seat_order,
        mem_approval_no=mem_approval_no,
    )
    _genel_kurul_bagi(donem=donem, assembly=assembly, kanal=elected_by, source=source)
    donem_kilidi.yazma_denetimi(donem, hazirlik_yazimi=elected_by == ElectedBy.GENEL_KURUL)
    kisi = _kisi_aktif(person)
    if _ayni_uyelik_var(donem=donem, kisi=kisi, organ=organ, assembly=assembly):
        raise ValueError(AYNI_UYELIK_VAR)
    aday = source == MembershipSource.PROGRAM and elected_by == ElectedBy.GENEL_KURUL
    hesap = iz.yazar_hesabi()
    uyelik = OrganMembership.objects.create(
        term=donem,
        person=kisi,
        organ=organ,
        assembly=assembly,
        role=role,
        seat_type=seat_type,
        seat_group=seat_group,
        votes=votes,
        seat_order=seat_order,
        elected_by=elected_by,
        source=source,
        evidence_note=evidence_note,
        mem_approval_no=mem_approval_no,
        status=MembershipStatus.ADAY if aday else MembershipStatus.SECILDI,
        start_date=None if aday else (start_date or timezone.localdate()),
        eligibility_declared_on=eligibility_declared_on,
        single_birlik_declared_on=single_birlik_declared_on,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    _denetle_ve_ozetle(_Denetim(uyelik, donem, gerekce=gerekce))
    denetim_izi.degisiklik(uyelik, onceki=None)
    return uyelik


def _guncel(uyelik: OrganMembership) -> OrganMembership:
    return OrganMembership.objects.select_related("term__rule_package", "person", "assembly").get(
        pk=uyelik.pk
    )


#: Üyeliğin güncel kaydı (dönemi, kural kopyası ve kişisiyle); 6. adımın akışları da okur.
guncel_kayit = _guncel


@transaction.atomic
def elect_membership(
    uyelik: OrganMembership,
    *,
    start_date: date | None = None,
    votes: int | None = None,
    seat_order: int | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> OrganMembership:
    """Genel kurulun seçim sonucu: aday kaydı seçilmiş olur (`ADAY` → `SECILDI`, `DURUM`).

    Seçilen, aynı genel kurulun aday kaydının kendisidir (tek kaynak). Koltuk uygunluğu yeniden,
    görev tekilliği ve seçilme sayacı bu geçişte denetlenir.
    """
    yazma_kapisi()
    app_password.require_password_set()
    guncel = _guncel(uyelik)
    if guncel.status != MembershipStatus.ADAY:
        raise UyelikDurumuGecersiz(YALNIZ_ADAY_SECILIR)
    donem_kilidi.yazma_denetimi(guncel.term, hazirlik_yazimi=True)
    _kisi_aktif(guncel.person)
    if seat_order is not None and guncel.seat_type != SeatType.YEDEK:
        raise ValueError(YEDEK_SIRASI_YALNIZ_YEDEKTE)
    onceki = denetim_izi.anlik(guncel)
    guncel.status = MembershipStatus.SECILDI
    guncel.start_date = start_date or _olay_gunu(guncel)
    if votes is not None:
        guncel.votes = votes
    if seat_order is not None:
        guncel.seat_order = seat_order
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save()
    _denetle_ve_ozetle(_Denetim(guncel, guncel.term, gerekce=gerekce), secim=True)
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel


def _gorevlendirme_dogrula(
    guncel: OrganMembership, alanlar: Mapping[str, Any], degisen: list[str]
) -> None:
    """Başka kurumdaki görevlendirme günleri yalnız DK öğretmen koltuğunda; bitiş başlangıçtan önce
    olamaz (md. 14/6; dört ay önerisi `uyelik_gecisleri.oneriler`'dedir, kayıt engellenmez)."""
    adlar = {"external_assignment_start", "external_assignment_end"}
    if not adlar & set(degisen):
        return
    baslangic = alanlar.get("external_assignment_start", guncel.external_assignment_start)
    bitis = alanlar.get("external_assignment_end", guncel.external_assignment_end)
    if (baslangic or bitis) and (guncel.organ, guncel.seat_group) != (
        OrganType.DENETLEME_KURULU,
        SeatGroup.OGRETMEN,
    ):
        raise ValueError(GOREVLENDIRME_YALNIZ_DK_OGRETMENINDE)
    if baslangic and bitis and bitis < baslangic:
        raise ValueError(GOREVLENDIRME_SIRASI)


@transaction.atomic
def update_membership(uyelik: OrganMembership, **alanlar: Any) -> OrganMembership:
    """Kişisiz ayrıntıları yazar (`GUNCELLE`); yalnız değişen alan. MEM onay no koltuğu yeniden denetler."""
    yazma_kapisi()
    app_password.require_password_set()
    bilinmeyen = set(alanlar) - GUNCELLENEBILIR
    if bilinmeyen:
        raise ValueError(f"Güncellenemeyen alan: {', '.join(sorted(bilinmeyen))}")
    guncel = _guncel(uyelik)
    degisen = [ad for ad, deger in alanlar.items() if getattr(guncel, ad) != deger]
    if not degisen:
        return guncel
    if guncel.status not in (MembershipStatus.ADAY, MembershipStatus.SECILDI):
        raise UyelikDurumuGecersiz(DEGISMEZ_UYELIK)
    donem_kilidi.yazma_denetimi(
        guncel.term, hazirlik_yazimi=guncel.elected_by == ElectedBy.GENEL_KURUL
    )
    if "seat_order" in degisen and alanlar["seat_order"] is not None:
        if guncel.seat_type != SeatType.YEDEK:
            raise ValueError(YEDEK_SIRASI_YALNIZ_YEDEKTE)
    if "mem_approval_no" in degisen and alanlar["mem_approval_no"]:
        if (guncel.organ, guncel.seat_group) != (OrganType.DENETLEME_KURULU, SeatGroup.OGRETMEN):
            raise ValueError(MEM_ONAYI_YALNIZ_OGRETMEN_KOLTUGUNDA)
    _gorevlendirme_dogrula(guncel, alanlar, degisen)
    if "expertise_required" in degisen and alanlar["expertise_required"]:
        if guncel.organ != OrganType.ALIM_KOMISYONU:
            raise ValueError(UZMANLIK_YALNIZ_ALIM_KOMISYONUNDA)
    onceki = denetim_izi.anlik(guncel)
    for ad in degisen:
        setattr(guncel, ad, alanlar[ad])
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=[*degisen, "updated_at", "updated_by"])
    if "mem_approval_no" in degisen and guncel.organ == OrganType.DENETLEME_KURULU:
        d = _Denetim(guncel, guncel.term, gerekce=None)
        _dk_koltuk_denetimi(d)
        ozet = d.ozet(list(guncel.rule_warnings or []))
        if ozet != (guncel.rule_warnings or []):
            guncel.rule_warnings = ozet
            guncel.save(update_fields=["rule_warnings", "updated_at"])
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel


# ---------------------------------------------------------------------------
# Kadro (okuma)
# ---------------------------------------------------------------------------
#: Kadrosu okunan organlar (organ ekranının sekmeleri; tasarım §5.2.2 "Sayılar", §6.4.6).
KADRO_ORGANLARI: Final = frozenset(
    {OrganType.YONETIM_KURULU, OrganType.DENETLEME_KURULU, OrganType.ALIM_KOMISYONU}
)


def gorev_suresi_gozlenen(donem: OabTerm, gun: date) -> Any:
    """Görev süresi (md. 12/2, 14/2; "Dönem bitişi takvimde"): son genel kuruldan (dönemin başlangıcı)
    bu yana başlamış yıl sayısı. Süre başlangıçtan bir önceki güne kadar sayılır: yıl dönümünde süre
    dolmuştur. Dönem başlangıcı yoksa (hazırlık) eksik."""
    if donem.start_date is None:
        return VERI_YOK
    return takvim.baslamis_yil(donem.start_date, gun)


#: Başkan görevini koyan kural (atıf ve olay günündeki metin): yönetim kurulunda md. 12/3 (dört görev),
#: Denetleme Kurulunda md. 14/1 ("aralarından bir başkan seçerek" görev bölümü).
_BASKAN_KURALI: Final[dict[str, str]] = {
    OrganType.YONETIM_KURULU: "yonetim_kurulu.gorevler",
    OrganType.DENETLEME_KURULU: "denetleme_kurulu.gorev_bolumu_gun",
}
BASKAN_YOK: Final[dict[str, str]] = {
    OrganType.YONETIM_KURULU: (
        "Yönetim kurulunun görevdeki asıl üyeleri arasında başkan yok; görev bölümünde başkan "
        "seçilmelidir."
    ),
    OrganType.DENETLEME_KURULU: (
        "Denetleme Kurulunun görevdeki asıl üyeleri arasında başkan yok; görev bölümünde başkan "
        "seçilmelidir."
    ),
}


def _baskan_eksigi(donem: OabTerm, organ: str, gun: date) -> DenetimSonucu | None:
    """Görevdeki asıllar varken aralarında başkan yoksa eksik (modül başlığı "Koltuk uygunluğu"):
    başkansız görev bölümü yazılabilir, kadro okumasında tamamlanacaktır; gerekçe istemez. Atıf görevi
    koyan maddedir; metin olay gününde yoksa satır çıkmaz."""
    asillar = selectors.gorevdeki_asillar(donem, organ)
    if not asillar or any(u.role == MembershipRole.BASKAN for u in asillar):
        return None
    sonuc = paket_denetle(_BASKAN_KURALI[organ], VERI_YOK, tarih=gun, donem=donem)
    if sonuc["durum"] == "denetlenmedi":
        return None
    return DenetimSonucu(**{**sonuc, "durum": "eksik", "mesaj": BASKAN_YOK[organ]})


def kadro_uyarilari(
    donem: OabTerm, organ: str, *, tarih: date | None = None
) -> list[DenetimSonucu]:
    """Kadro okumasının uyarıları ve eksikleri: yazmaz, gerekçe istemez (tasarım §5.2.2 "Sayılar").

    Yönetim kurulu ve Denetleme Kurulunda kadro sayıları (5+5, 3+3) ve görev süresi (md. 12/2, 14/2;
    "bitiminde uyarı"); alım komisyonunda en az üç kişi (md. 18/1; organ ekranı, harcama dosyasındaki
    karşılığı F4). Sayılan yalnız seçilmiş (`SECILDI`) kayıttır; aday sayılmaz, düşen koltuk sayıma
    girmez. Asıl sayısı görevdeki asıllardır (yedekten çağrılan dahil), yedek sayısı çağrılmamış
    yedeklerdir. İki kurulda görevdeki asıllar arasında başkan yoksa eksik satırı da döner
    (`_baskan_eksigi`; durumu `eksik`).
    """
    gun = tarih or timezone.localdate()
    sayilar = selectors.kadro_sayilari(donem, organ)
    eksikler: list[DenetimSonucu] = []
    if organ in (OrganType.YONETIM_KURULU, OrganType.DENETLEME_KURULU):
        onek = "yonetim_kurulu" if organ == OrganType.YONETIM_KURULU else "denetleme_kurulu"
        sure = f"{onek}.gorev_suresi_yil"
        sonuclar = [
            paket_denetle(f"{onek}.asil_uye", sayilar[SeatType.ASIL], tarih=gun, donem=donem),
            paket_denetle(f"{onek}.yedek_uye", sayilar[SeatType.YEDEK], tarih=gun, donem=donem),
            paket_denetle(sure, gorev_suresi_gozlenen(donem, gun), tarih=gun, donem=donem),
        ]
        baskan = _baskan_eksigi(donem, organ, gun)
        if baskan is not None:
            eksikler.append(baskan)
    elif organ == OrganType.ALIM_KOMISYONU:
        sonuclar = [
            paket_denetle(
                "harcama.alim_komisyonu_en_az", sayilar[SeatType.ASIL], tarih=gun, donem=donem
            )
        ]
    else:
        raise ValueError(ORGAN_BU_YOLDAN_YAZILMAZ)
    return [*(sonuc for sonuc in sonuclar if sonuc["durum"] == "uyari"), *eksikler]


# ---------------------------------------------------------------------------
# Görev alma engelinin dayanağı (özel nitelikli alan; erişim günlüğü)
# ---------------------------------------------------------------------------
def engel_dayanagini_oku(uyelik: OrganMembership) -> str | None:
    """Dayanağı verir; dolu dayanağın okuması ÖNCE erişim günlüğüne yazılır (tasarım §4.6.4).

    Satır yazılamazsa (`ErisimGunluguYazilamadi`) değer verilmez (fail-closed). Boş dayanakta okunan
    özel nitelikli veri yoktur, satır yazılmaz. Çözülemeyen değer `None` döner, okuma yine yazılır.
    """
    guncel = OrganMembership.objects.get(pk=uyelik.pk)
    deger = guncel.eligibility_bar_basis
    if not deger:
        return None
    erisim_gunlugu.yaz(
        AccessKind.OZEL_NITELIKLI_ALAN,
        model=OrganMembership,
        object_id=guncel.pk,
        field="eligibility_bar_basis",
    )
    return None if is_corrupt(deger) else str(deger)
