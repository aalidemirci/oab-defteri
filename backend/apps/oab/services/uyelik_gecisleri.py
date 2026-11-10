"""Üyeliğin geçişleri: yedek çağrısı, düşme, iptal, görev alma engeli ve öneriler (tasarım §5.2.2, §7.2;
plan F1c 6. adım).

YEDEK ÇAĞRISI (`yedek_cagir`): yedek yeni kayıt değildir; aynı kaydın `promoted_on`'u yazılır, `seat_type`
seçildiği koltuk olarak kalır (plan F1c kararları). Yönetim kurulunda çağrı günü kurulun görev bölümü
süresini başlatır (md. 12/3; `gorev_bolumu.kurulun_olustugu_gun`).

* Yönetim kurulu (md. 13/6; uç kuralı: sekreter, YK kararıyla): yedekler aldıkları oy sırasıyla çağrılır
  (`yonetim_kurulu.yedek_cagirma`); sıradakinin atlanması uyarı + gerekçedir, bekleyen yedeklerden
  birinin sırası girilmemişse sıra tamamlanacaktır. md. 13/6 satırı yalnız sıradan doğar. Karar bağı
  (`promoted_by_decision`) bağlanırken karar yedek çağırma kararı, toplantısı bu dönemin yönetim kurulu
  toplantısıdır ve karar kabul edilmiş olmalıdır (sert, hesap bütünlüğü; tasarım §7.2 "Notlar"). Karar
  bağı yoksa F3'e dek uyarı + gerekçedir (tasarım §7.2; plan F1c kararları): bu bir Yönetmelik hükmü
  değildir, md. 13/6 satırına yazılmaz; atıfsız akış satırıdır (`uyum.akis_sapmasi`).
* Denetleme Kurulu (md. 14/6; uç kuralı: program yöneticisi, üyelik kaydı): yönetim kurulu kararı
  gerekmez, karar bağı verilmez. Çağrılan yedek kendi koltuk grubunun asıl hücresine oturur: hücre
  doluysa koltuk kuralı serttir (önce görevden ayrılanın üyeliği düşürülür).

DÜŞME (`uyeligi_dusur`): yalnız seçilmiş üyelik düşer (aday iptal edilir); düşme türü zorunludur, serbest
gerekçe isteğe bağlı ve şifrelidir. Öğrencisi ayrılan velinin (ya da eğitimini tamamlayan kursiyerin)
yönetim kurulu üyeliği, kurulun görevdeki asıl sayısı toplantı yeter sayısının altına düşecekse
olağanüstü genel kurula kadar sürer (md. 7/2; `uyelik.ayrilan_veli_devam`): düşürme önerilmez, ertelenir
(`ertele=True` → `retained_until_assembly`); ertelemeden düşürmek uyarı + gerekçedir. Devamsızlıkla
düşmenin önerisi F3'tedir. Düşen üyeliğe bağlı hesap aynı işlemde askıya alınır (`UYELIK_DUSTU`;
`hesap_baglari.hesaplari_esitle`, tasarım §4.4.5; F1c 7. adım); ertelenen üyelik seçilmiş kalır,
hesabı askıya alınmaz. İptal edilen (yanlış kayıt) seçilmiş üyeliğin hesabı da aynı nedenle askıya
alınır: bağ artık geçerli bir koltuğa dayanmaz.

İPTAL (`uyeligi_iptal_et`): yanlış kayıt `IPTAL` olur (aday ya da seçilmiş); gerekçe zorunludur (sert,
O1), kim `updated_by` ve iz satırıdır. İptal kaydı hiç olmamış sayılır (tekil kısıt, sayaç, tek koltuk).

GÖREV ALMA ENGELİ (`engel_yaz`): `eligibility_bar` hüküm alanıdır; `VAR`'da dayanak (şifreli, özel
nitelikli) ve tespit günü zorunludur. Engel işaretli adayın seçimi uyarı + gerekçedir
(`uyelikler.elect_membership`); görevdeki üyede düşürme önerisidir (tespit günüyle, düşme türü
`DIGER`; tür suçu ele vermez). Öneri ve hatırlatmalar saklanmaz, kayıttan hesaplanır (`oneriler`).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any, Final

from django.db import transaction
from django.utils import timezone

from apps.oab import selectors
from apps.oab.kurallar import VERI_YOK, YururlukteDegerYok, kural, yazma_kapisi
from apps.oab.kurallar.erisim import atifli_metin
from apps.oab.kurallar.erisim import denetle as paket_denetle
from apps.oab.models import (
    BoardDecision,
    DecisionKind,
    DropKind,
    ElectedBy,
    EligibilityBar,
    EligibilityBarBasis,
    MembershipRole,
    MembershipStatus,
    OrganMembership,
    OrganType,
    PersonKind,
    SeatGroup,
    SeatType,
    UyelikDurumuGecersiz,
)
from apps.oab.services import (
    donem_kilidi,
    hesap_baglari,
    iz,
    takvim,
    temsilciler,
    uyelikler,
    uyum,
)
from apps.okul import denetim_izi
from apps.okul.services import app_password

#: Yedeği çağrılan kurullar (md. 13/6, 14/6).
YEDEKLI_KURULLAR: Final = frozenset({OrganType.YONETIM_KURULU, OrganType.DENETLEME_KURULU})

YEDEK_ORGAN_TUTMUYOR = "Bu çağrı bu kurulun yedeği için yapılır."
YALNIZ_BEKLEYEN_YEDEK = "Yalnız seçilmiş ve çağrılmamış yedek üye asıl üyeliğe çağrılır."
CAGRI_SECIMDEN_ONCE = "Yedeğin çağrı günü seçildiği günden önce olamaz."
DK_YEDEGI_KARARSIZ = (
    "Denetleme Kurulunun yedeği yönetim kurulu kararıyla çağrılmaz (md. 14/6); karar bağı verilmez."
)
KARAR_YEDEK_CAGIRMA_DEGIL = "Bağlanan karar yedek çağırma kararı olmalıdır."
KARAR_YK_TOPLANTISI_DEGIL = "Yedek çağırma kararı yönetim kurulu toplantısının kararı olmalıdır."
KARAR_DONEMI_TUTMUYOR = "Yedek çağırma kararı yedeğin birlik döneminin kararı olmalıdır."
#: Karar bağı yokluğunun akış satırı (Yönetmelik maddesi değildir; tasarım §7.2, plan F1c kararları).
KARARSIZ_CAGRI_AKISI = "akis.yedek_cagrisi_karar_bagi"
KARARSIZ_CAGRI = (
    "Yedek çağrısı bir yönetim kurulu kararına bağlanmadı; karar defterindeki kararın bilgisi sonra "
    "eklenir (program uyarısıdır, Yönetmelik hükmü değildir)."
)
DUSME_TURU_GEREKLI = "Düşme türü seçilmelidir."
YALNIZ_SECILMIS_DUSER = "Yalnız seçilmiş üyelik düşer; aday kaydı yanlışsa iptal edilir."
DUSME_SECIMDEN_ONCE = "Düşme günü seçilme gününden önce olamaz."
ERTELEME_KOSULU_YOK = (
    "Erteleme yalnız öğrencisi ayrılan velinin ya da kursiyerin yönetim kurulu üyeliğinde, kurulun "
    "üye sayısı toplantı yeter sayısının altına düşecekken yapılır (md. 7/2)."
)
IPTAL_GEREKCESI_GEREKLI = "İptal gerekçesi yazılmalıdır."
YALNIZ_ADAY_YA_DA_SECILMIS_IPTAL = "Yalnız aday ya da seçilmiş üyelik iptal edilir."
ENGEL_DAYANAGI_GEREKLI = "Görev alma engelinin dayanağı ve tespit günü girilmelidir."
ENGEL_YOKSA_DAYANAK_YOK = "Engel yoksa dayanak ve tespit günü girilmez."
ENGEL_DEGISMEZ = "Düşmüş ya da iptal edilmiş üyeliğin görev alma engeli değiştirilemez."

#: Öneri ve hatırlatma metinleri (kişisiz; engelin dayanağını ele vermez, tasarım §4.4.2 ¹¹).
ENGEL_DUSURME_ONERISI = (
    "Görev alma engeli işaretli: üyeliğin engelin tespit günüyle ({gun}) ve “Diğer” düşme türüyle "
    "düşürülmesi önerilir."
)
SUC_BEYANI_HATIRLATMASI = (
    "Okulun görev alma engeli beyanı uygulaması bu üyelikte işaretlenmedi (okul uygulamasıdır, "
    "mevzuat uyarısı değildir)."
)
TEK_BIRLIK_BEYANI_HATIRLATMASI = (
    "Okulun tek birlik yönetimi beyanı uygulaması bu üyelikte işaretlenmedi (okul uygulamasıdır, "
    "mevzuat uyarısı değildir)."
)


@dataclass(frozen=True)
class Oneri:
    """Kayıttan hesaplanan öneri ya da hatırlatma (saklanmaz; gerekçe istemez)."""

    tur: str
    metin: str
    gun: date | None = None
    drop_kind: str = ""


def _ozeti_isle(guncel: OrganMembership, sonuclar: Mapping[str, Any]) -> None:
    """Denetim sonuçlarını uyarı özetine yazar; izini çağıran (aynı işlemde, son hâlle) yazar."""
    ozet = uyelikler.ozet_hesapla(guncel, sonuclar)
    if ozet != (guncel.rule_warnings or []):
        guncel.rule_warnings = ozet
        guncel.save(update_fields=["rule_warnings", "updated_at"])


def _baslangic(uyelik: OrganMembership) -> OrganMembership:
    """Güncel kayıt; ilk hesap kurulu ve dönem yazılabilir olmalı (kural kullanan servis ayrıca
    `yazma_kapisi()` ile başlar)."""
    app_password.require_password_set()
    guncel = uyelikler.guncel_kayit(uyelik)
    donem_kilidi.yazma_denetimi(
        guncel.term, hazirlik_yazimi=guncel.elected_by == ElectedBy.GENEL_KURUL
    )
    return guncel


# ---------------------------------------------------------------------------
# Yedek çağrısı (md. 13/6, 14/6)
# ---------------------------------------------------------------------------
def _karar_dogrula(guncel: OrganMembership, karar: BoardDecision) -> BoardDecision:
    bagli = BoardDecision.objects.select_related("meeting").get(pk=karar.pk)
    if bagli.kind != DecisionKind.YEDEK_CAGIRMA:
        raise ValueError(KARAR_YEDEK_CAGIRMA_DEGIL)
    if bagli.meeting.organ != OrganType.YONETIM_KURULU:
        raise ValueError(KARAR_YK_TOPLANTISI_DEGIL)
    if bagli.meeting.term_id != guncel.term_id:
        raise ValueError(KARAR_DONEMI_TUTMUYOR)
    if bagli.status not in temsilciler.BAGLANABILIR_KARAR_DURUMLARI:
        raise ValueError(temsilciler.KARAR_KABUL_EDILMEMIS)
    return bagli


def _oy_sirasinda_mi(guncel: OrganMembership) -> bool | None:
    """Çağrılan, bekleyen yedekler arasında oy sırasının ilki mi? Bir sıra girilmemişse `None`."""
    bekleyenler = selectors.bekleyen_yedekler(guncel.term, guncel.organ)
    if any(y.seat_order is None for y in bekleyenler):
        return None
    ilk = min(y.seat_order for y in bekleyenler if y.seat_order is not None)
    return guncel.seat_order == ilk


def _yk_cagri_denetimi(
    guncel: OrganMembership,
    karar: BoardDecision | None,
    *,
    gun: date,
    gerekce: uyum.Gerekce | None,
) -> uyum.UyumSonucu:
    """Oy sırası (md. 13/6 satırı; sıra çağrıdan ÖNCEKİ bekleyen yedeklere bakar), sonra karar bağı
    (atıfsız akış satırı; modül başlığı). İki denetim sırayla koşar; aynı gerekçe ikisine de yazılır."""
    sirada = _oy_sirasinda_mi(guncel)
    gozlenen: Any
    if sirada is None:
        gozlenen = VERI_YOK
    elif sirada:
        gozlenen = ["OY_SIRASI"]
    else:
        gozlenen = ["SIRA_DISI"]
    sonuc = uyum.denetle(
        "yonetim_kurulu.yedek_cagirma",
        gozlenen,
        donem=guncel.term,
        konu=guncel,
        tarih=gun,
        gerekce=gerekce,
    )
    if karar is None:
        uyum.akis_sapmasi(
            KARARSIZ_CAGRI_AKISI, KARARSIZ_CAGRI, donem=guncel.term, konu=guncel, gerekce=gerekce
        )
    return sonuc


@transaction.atomic
def yedek_cagir(
    uyelik: OrganMembership,
    *,
    organ: str,
    promoted_on: date | None = None,
    karar: BoardDecision | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> OrganMembership:
    """Yedeği asıl üyeliğe çağırır (`GUNCELLE`; modül başlığı "Yedek çağrısı")."""
    yazma_kapisi()
    guncel = _baslangic(uyelik)
    if organ not in YEDEKLI_KURULLAR or guncel.organ != organ:
        raise ValueError(YEDEK_ORGAN_TUTMUYOR)
    if (
        guncel.status != MembershipStatus.SECILDI
        or guncel.seat_type != SeatType.YEDEK
        or guncel.promoted_on is not None
    ):
        raise ValueError(YALNIZ_BEKLEYEN_YEDEK)
    gun = promoted_on or timezone.localdate()
    if guncel.start_date is not None and gun < guncel.start_date:
        raise ValueError(CAGRI_SECIMDEN_ONCE)
    if organ == OrganType.DENETLEME_KURULU and karar is not None:
        raise ValueError(DK_YEDEGI_KARARSIZ)
    bagli = None if karar is None else _karar_dogrula(guncel, karar)
    sira_sonucu = None
    if organ == OrganType.YONETIM_KURULU:
        sira_sonucu = _yk_cagri_denetimi(guncel, bagli, gun=gun, gerekce=gerekce)
    onceki = denetim_izi.anlik(guncel)
    guncel.promoted_on = gun
    guncel.promoted_by_decision = bagli
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=["promoted_on", "promoted_by_decision", "updated_at", "updated_by"])
    if sira_sonucu is not None:
        _ozeti_isle(guncel, {"yonetim_kurulu.yedek_cagirma": sira_sonucu.sonuc})
    else:
        _ozeti_isle(guncel, uyelikler.koltugu_denetle(guncel, gerekce=gerekce))
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel


# ---------------------------------------------------------------------------
# Düşme (md. 7/2, 12/5, 13/6, 14/6-7)
# ---------------------------------------------------------------------------
def _md72_kapsaminda(guncel: OrganMembership, drop_kind: str) -> bool:
    """Öğrencisi ayrılan velinin ya da kursiyerin yönetim kurulu üyeliği mi? (md. 7/2 2. cümle)."""
    return (
        drop_kind == DropKind.OGRENCI_AYRILDI
        and guncel.organ == OrganType.YONETIM_KURULU
        and uyelikler.yk_uye_turu(guncel.person) in (PersonKind.VELI, PersonKind.KURSIYER)
    )


def _uyelik_surer_mi(guncel: OrganMembership, gun: date) -> bool:
    """Düşerse kurulun görevdeki asıl sayısı toplantı yeter sayısının altına iner mi? (md. 7/2)."""
    esik = int(kural("yonetim_kurulu.toplanti_yeter_sayi", tarih=gun, donem=guncel.term))
    kalan = {
        u.person_id
        for u in selectors.gorevdeki_asillar(guncel.term, OrganType.YONETIM_KURULU)
        if u.pk != guncel.pk
    }
    return len(kalan) < esik


def _yk_baskani_mi(guncel: OrganMembership) -> bool:
    """Yönetim kurulu başkanlık kaydı mı? Başkanlık düşer ya da iptal olursa başkanın kendiliğinden
    üye olduğu üç komisyonun satırları aynı işlemde kapanır (tasarım §6.4.4, E03)."""
    return guncel.organ == OrganType.YONETIM_KURULU and guncel.role == MembershipRole.BASKAN


@transaction.atomic
def uyeligi_dusur(
    uyelik: OrganMembership,
    *,
    drop_kind: str,
    end_date: date | None = None,
    dropped_reason: str = "",
    ertele: bool = False,
    gerekce: uyum.Gerekce | None = None,
) -> OrganMembership:
    """Seçilmiş üyeliği düşürür (`DURUM`) ya da md. 7/2'de olağanüstü genel kurula erteler."""
    yazma_kapisi()
    if not drop_kind or drop_kind not in DropKind.values:
        raise ValueError(DUSME_TURU_GEREKLI)
    guncel = _baslangic(uyelik)
    if guncel.status != MembershipStatus.SECILDI:
        raise UyelikDurumuGecersiz(YALNIZ_SECILMIS_DUSER)
    gun = end_date or timezone.localdate()
    if guncel.start_date is not None and gun < guncel.start_date:
        raise ValueError(DUSME_SECIMDEN_ONCE)
    kapsamda = _md72_kapsaminda(guncel, drop_kind)
    surer = kapsamda and _uyelik_surer_mi(guncel, gun)
    if ertele and not surer:
        raise ValueError(ERTELEME_KOSULU_YOK)
    sonuclar = {}
    if kapsamda:
        sonuclar["uyelik.ayrilan_veli_devam"] = uyum.denetle(
            "uyelik.ayrilan_veli_devam",
            ertele or not surer,
            donem=guncel.term,
            konu=guncel,
            tarih=gun,
            gerekce=gerekce,
        ).sonuc
    onceki = denetim_izi.anlik(guncel)
    if ertele:
        guncel.retained_until_assembly = True
        alanlar = ["retained_until_assembly"]
    else:
        guncel.status = MembershipStatus.DUSTU
        guncel.drop_kind = drop_kind
        guncel.end_date = gun
        guncel.dropped_reason = dropped_reason
        alanlar = ["status", "drop_kind", "end_date", "dropped_reason"]
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=[*alanlar, "updated_at", "updated_by"])
    if sonuclar:
        _ozeti_isle(guncel, sonuclar)
    denetim_izi.degisiklik(guncel, onceki=onceki)
    if not ertele:
        hesap_baglari.hesaplari_esitle(guncel)
    if not ertele and _yk_baskani_mi(guncel):
        temsilciler.baskan_satirlarini_kapat(guncel.term, guncel.person_id, gun=gun)
    return guncel


# ---------------------------------------------------------------------------
# İptal (O1)
# ---------------------------------------------------------------------------
@transaction.atomic
def uyeligi_iptal_et(uyelik: OrganMembership, *, cancel_reason: str) -> OrganMembership:
    """Yanlış kaydı iptal eder (`DURUM`); gerekçe zorunlu, kim `updated_by` ve iz satırıdır."""
    metin = cancel_reason.strip()
    if not metin:
        raise ValueError(IPTAL_GEREKCESI_GEREKLI)
    guncel = _baslangic(uyelik)
    if guncel.status not in (MembershipStatus.ADAY, MembershipStatus.SECILDI):
        raise UyelikDurumuGecersiz(YALNIZ_ADAY_YA_DA_SECILMIS_IPTAL)
    onceki = denetim_izi.anlik(guncel)
    baskan = _yk_baskani_mi(guncel)
    guncel.status = MembershipStatus.IPTAL
    guncel.cancel_reason = metin
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=["status", "cancel_reason", "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel, onceki=onceki)
    hesap_baglari.hesaplari_esitle(guncel)
    if baskan:
        temsilciler.baskan_satirlarini_kapat(
            guncel.term, guncel.person_id, gun=timezone.localdate(), iptal=True
        )
    return guncel


# ---------------------------------------------------------------------------
# Görev alma engeli (md. 12/4-5, 14/7)
# ---------------------------------------------------------------------------
@transaction.atomic
def engel_yaz(
    uyelik: OrganMembership,
    *,
    eligibility_bar: str,
    eligibility_bar_basis: str = "",
    eligibility_bar_found_on: date | None = None,
) -> OrganMembership:
    """Görev alma engelini yazar (`GUNCELLE`); dayanak şifrelidir, iz satırına yalnız adı girer."""
    if eligibility_bar == EligibilityBar.VAR:
        if (
            eligibility_bar_basis not in EligibilityBarBasis.values
            or eligibility_bar_found_on is None
        ):
            raise ValueError(ENGEL_DAYANAGI_GEREKLI)
    elif eligibility_bar == EligibilityBar.YOK:
        if eligibility_bar_basis or eligibility_bar_found_on is not None:
            raise ValueError(ENGEL_YOKSA_DAYANAK_YOK)
    else:
        raise ValueError(ENGEL_DAYANAGI_GEREKLI)
    guncel = _baslangic(uyelik)
    if guncel.status not in (MembershipStatus.ADAY, MembershipStatus.SECILDI):
        raise UyelikDurumuGecersiz(ENGEL_DEGISMEZ)
    yeni = {
        "eligibility_bar": eligibility_bar,
        "eligibility_bar_basis": eligibility_bar_basis,
        "eligibility_bar_found_on": eligibility_bar_found_on,
    }
    degisen = [ad for ad, deger in yeni.items() if getattr(guncel, ad) != deger]
    if not degisen:
        return guncel
    onceki = denetim_izi.anlik(guncel)
    for ad in degisen:
        setattr(guncel, ad, yeni[ad])
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=[*degisen, "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel


# ---------------------------------------------------------------------------
# Öneriler ve hatırlatmalar (kayıttan hesaplanır, saklanmaz)
# ---------------------------------------------------------------------------
def _gorevlendirme_onerisi(uyelik: OrganMembership) -> Oneri | None:
    """DK öğretmeninin başka kurumdaki görevlendirmesi dört aydan uzunsa yerine yedeği çağrılır (md.
    14/6; `denetleme_kurulu.ogretmen_gorevlendirme_ay`). Bitiş girilmemişse öneri yoktur."""
    baslangic, bitis = uyelik.external_assignment_start, uyelik.external_assignment_end
    if (
        uyelik.organ != OrganType.DENETLEME_KURULU
        or uyelik.seat_group != SeatGroup.OGRETMEN
        or baslangic is None
        or bitis is None
    ):
        return None
    sonuc = paket_denetle(
        "denetleme_kurulu.ogretmen_gorevlendirme_ay",
        takvim.baslamis_ay(baslangic, bitis),
        tarih=baslangic,
        donem=uyelik.term,
    )
    if sonuc["durum"] != "uyari":
        return None
    return Oneri(tur="YEDEK_CAGRISI", metin=atifli_metin(sonuc), gun=baslangic)


def oneriler(uyelik: OrganMembership) -> list[Oneri]:
    """Görevdeki (seçilmiş) üyeliğin önerileri ve okul uygulaması hatırlatmaları (yazmaz).

    Engel: düşürme önerisi, tespit günüyle (`DIGER`). Dört ay: yedek çağrısı önerisi. Beyan günü
    girilmemişse okul uygulaması hatırlatması (mevzuat uyarısı değildir, gerekçe istemez).
    """
    if uyelik.status != MembershipStatus.SECILDI:
        return []
    sonuc: list[Oneri] = []
    if uyelikler.engel_hukum_mu(uyelik) and uyelik.eligibility_bar_found_on:
        gun = uyelik.eligibility_bar_found_on
        sonuc.append(
            Oneri(
                tur="DUSURME",
                metin=ENGEL_DUSURME_ONERISI.format(gun=gun.strftime("%d.%m.%Y")),
                gun=gun,
                drop_kind=DropKind.DIGER,
            )
        )
    if uyelik.term_id is not None and selectors.gorevdeki_asil_mi(uyelik):
        try:
            gorevlendirme = _gorevlendirme_onerisi(uyelik)
        except YururlukteDegerYok:
            gorevlendirme = None
        if gorevlendirme is not None:
            sonuc.append(gorevlendirme)
    if uyelik.organ in YEDEKLI_KURULLAR and uyelik.eligibility_declared_on is None:
        sonuc.append(Oneri(tur="HATIRLATMA", metin=SUC_BEYANI_HATIRLATMASI))
    if uyelik.organ == OrganType.YONETIM_KURULU and uyelik.single_birlik_declared_on is None:
        sonuc.append(Oneri(tur="HATIRLATMA", metin=TEK_BIRLIK_BEYANI_HATIRLATMASI))
    return sonuc
