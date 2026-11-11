"""Hesap ↔ üyelik bağının kuralları (tasarım §4.4.1, §4.4.5, §4.6.1; plan F1c 7. adım).

Organ rollerinin (dört YK görevi ve Denetleme Kurulu) `okul.Account` satırı bir organ üyeliğine
bağlıdır (`person`, `membership`, `term`; kişi ve dönem üyelikten türer). Kurallar burada durur, `okul`
onları kayıt defterinden alır (`okul.services.hesaplar.register_account_bond_rules`; `AppConfig.ready`):
`okul` `oab`'yi içe aktarmaz (plan "F1c adımları").

HESAP AÇMA (`bagla`; tasarım §4.4.1 "Organ rolleri organ üyeliğine bağlanır"):

* üyelik rolün kurulundadır: dört YK görevinde yönetim kurulu, `denetleme_kurulu`'nda Denetleme
  Kurulu;
* üyelik seçilmiştir (`SECILDI`); geçiş kurulumunda devralınan üyelik (`DEVRALINAN`, §7.9) de
  seçilmiş açılır ve hesap açmaya yeter (aday, düşmüş ve iptal edilmiş kayıt hesap almaz);
* üye görevdeki asıldır (asıl koltuk ya da yedekten çağrılmış): yedekler ve YK'nin görevsiz asılları
  v1'de hesap almaz (§15 M-7); Denetleme Kurulu hesabı "DK asıl üyeleri"nindir (§4.4.1 rol tablosu);
* dönemi açıktır (`ACIK`): hesaplar dönemliktir, eski dönemin hesabı hesap geçişindedir (F4);
* yönetim kurulunda üyeliğin görevi hesabın rolüdür: görev görev bölümünde verilir (md. 12/3; ya da
  devralınan görevli kayıtta). Denetleme Kurulunda görev aranmaz: kurul kendi görev bölümünü (başkan
  seçimi, md. 14/1) bu hesapla yazar (M8).

Aynı üyeliğe bağlı tek açık hesap, rolün açık hesap sınırı ve hesap açmanın öteki kuralları `okul`'dadır
(`hesaplar.open_account`).

GEÇERSİZLİK VE ASKI (`gecersizlik_nedeni`, `hesaplari_esitle`; tasarım §4.4.5 "Üyelik düştü, görev
değişti"): bağlı üyelik seçilmiş değilse (düştü, iptal edildi) ya da kurulu, kişisi, dönemi tutmuyorsa
neden `UYELIK_DUSTU`, yönetim kurulunda görevi hesabın rolü değilse `GOREV_BOLUMU`'dur. Üyeliği yazan
servisler — düşme ve iptal (`uyelik_gecisleri`), görev bölümü (`gorev_bolumu._gorevleri_dagit`) —
kaydı yazdıktan sonra AYNI işlemde `hesaplari_esitle`'yi çağırır; geçersizleşen her açık hesap
`ASKIDA` olur (`hesaplar.uyelik_askisi`; iz satırının yazarı kaydı yazan hesaptır). md. 7/2'de
olağanüstü genel kurula ertelenen üyelik seçilmiş kalır: hesap askıya alınmaz. Dönemin kapanışı askı
nedeni değildir (yeni dönemin görev bölümü ve hesap geçişi F4).

HESAP ÖNERİLERİ (`hesap_onerileri`; tasarım §4.4.5, §8 Genel Bakış "hesap önerileri"): program
yöneticisinin listesi, kişisiz kodlar ve kimlikler. Kalemler saklanmaz, her okumada kayıtlardan
hesaplanır: üyelik ya da görev nedeniyle askıdaki ve bağı bugün geçersiz hesabın kapanışı (sarmalın
silinmesi kapamayla gelir, TK11), bağı yeniden geçerli olmuş askıdaki hesabın askıdan çıkarılması
(askı kendiliğinden kalkmaz, §4.4.5) ve açık dönemde hesabı olmayan görevli (dört YK görevi ve
Denetleme Kurulunun görevdeki asılları) için yeni hesap. Ekranı (Kullanıcılar, 11. adım) ve Genel
Bakış kalemi (12. adım) geldi.
"""

from __future__ import annotations

from typing import Any, Final

from apps.oab import selectors
from apps.oab.models import (
    MembershipRole,
    MembershipStatus,
    OabTerm,
    OrganMembership,
    OrganType,
    TermStatus,
)
from apps.okul.models import Account, AccountRole, AccountStatus, SuspendReason
from apps.okul.rol_izinleri import Eylem, yetki_oturum
from apps.okul.services import app_password, hesaplar
from apps.okul.services.hesaplar import HesapBagi, HesapBagiKurallari, HesapBagiReddi
from shared.crypto import has_corrupt

#: Yönetim kurulu rolünün görevi (md. 12/3; tasarım §4.4.1).
ROL_GOREVLERI: Final[dict[str, str]] = {
    AccountRole.BASKAN.value: MembershipRole.BASKAN.value,
    AccountRole.BASKAN_YARDIMCISI.value: MembershipRole.BASKAN_YARDIMCISI.value,
    AccountRole.MUHASIP.value: MembershipRole.MUHASIP.value,
    AccountRole.SEKRETER.value: MembershipRole.SEKRETER.value,
}
#: Görevin hesap rolü (`ROL_GOREVLERI`'nin tersi).
GOREV_ROLLERI: Final[dict[str, str]] = {gorev: rol for rol, gorev in ROL_GOREVLERI.items()}

UYELIK_YOK = "Üyelik kaydı bulunamadı."
ORGAN_TUTMUYOR = "Seçilen üyelik bu rolün kurulunda değil."
SECILMIS_DEGIL = (
    "Hesap yalnız seçilmiş üyeye açılır; aday, düşmüş ya da iptal edilmiş üyelik hesap almaz."
)
GOREVDEKI_ASIL_DEGIL = "Çağrılmamış yedek üye hesap almaz."
DONEM_ACIK_DEGIL = "Hesap yalnız açık birlik dönemindeki üyeliğe açılır."
GOREV_TUTMUYOR = (
    "Yönetim kurulunda hesap, görev bölümünde bu görevi alan üyeye açılır; seçilen üyenin görevi "
    "bu rol değil."
)

#: Hesap önerisi türleri (kişisiz kodlar; ekran metni sözlükte ve `pano/metinler.ts`'te).
ONERI_KAPAT: Final = "HESAP_KAPAT"
ONERI_ASKIDAN_CIKAR: Final = "HESAP_ASKIDAN_CIKAR"
ONERI_AC: Final = "HESAP_AC"


def _rolun_kurulu(rol: str) -> str:
    return (
        OrganType.DENETLEME_KURULU
        if rol == AccountRole.DENETLEME_KURULU
        else OrganType.YONETIM_KURULU
    )


def _acilis_engeli(rol: str, uyelik: OrganMembership) -> str | None:
    """Üyeliğe bu rolde hesap açılamıyorsa nedeni (modül başlığı "HESAP AÇMA"), açılabiliyorsa None."""
    if uyelik.organ != _rolun_kurulu(rol):
        return ORGAN_TUTMUYOR
    if uyelik.status != MembershipStatus.SECILDI:
        return SECILMIS_DEGIL
    if not selectors.gorevdeki_asil_mi(uyelik):
        return GOREVDEKI_ASIL_DEGIL
    if uyelik.term.status != TermStatus.ACIK:
        return DONEM_ACIK_DEGIL
    gorev = ROL_GOREVLERI.get(rol)
    if gorev is not None and uyelik.role != gorev:
        return GOREV_TUTMUYOR
    return None


def _uyelik(kimlik: object) -> OrganMembership | None:
    if isinstance(kimlik, bool):
        return None
    try:
        pk = int(str(kimlik))
    except (TypeError, ValueError):
        return None
    return OrganMembership.objects.select_related("term", "person").filter(pk=pk).first()


def bagla(rol: str, uyelik_kimligi: object) -> HesapBagi:
    """Hesap açmanın bağı: kurala uyan üyelik → (kişi, üyelik, dönem); uymazsa `HesapBagiReddi`."""
    uyelik = _uyelik(uyelik_kimligi)
    if uyelik is None:
        raise HesapBagiReddi(UYELIK_YOK)
    engel = _acilis_engeli(rol, uyelik)
    if engel is not None:
        raise HesapBagiReddi(engel)
    return HesapBagi(person_id=uyelik.person_id, membership_id=uyelik.pk, term_id=uyelik.term_id)


def gecersizlik_nedeni(hesap: Account) -> str | None:
    """Organ rolündeki hesabın bağı bugün geçersizse askı nedeni, geçerliyse None (modül başlığı)."""
    uyelik = _uyelik(hesap.membership_id) if hesap.membership_id is not None else None
    if (
        uyelik is None
        or uyelik.person_id != hesap.person_id
        or uyelik.term_id != hesap.term_id
        or uyelik.organ != _rolun_kurulu(hesap.role)
        or uyelik.status != MembershipStatus.SECILDI
        or not selectors.gorevdeki_asil_mi(uyelik)
    ):
        return SuspendReason.UYELIK_DUSTU.value
    gorev = ROL_GOREVLERI.get(hesap.role)
    if gorev is not None and uyelik.role != gorev:
        return SuspendReason.GOREV_BOLUMU.value
    return None


def hesaplari_esitle(uyelik: OrganMembership) -> list[Account]:
    """Üyeliğe bağlı açık hesaplardan bağı geçersizleşenleri AYNI işlemde askıya alır (modül başlığı).

    Üyeliği yazan servis kaydı yazdıktan sonra, kendi işleminin içinde çağırır; askı yazılamazsa kayıt
    da geri alınır. Askıya alınan hesapları döndürür.

    Sıra "durum en son"dur (`hesaplar.uyelik_askisi`): üyeliğe bağlı BÜTÜN satırlar (kapalı dahil)
    askıya verilir; önce satırın mührü ve izi doğrulanır (tutmayan satırda `BUTUNLUK` satırı), durum
    ve askı nedeni ancak doğrulanmış satırdan okunur. Program dışından `KAPALI` ya da `ASKIDA`
    yapılmış satır bu yüzden süzgeçte sessizce düşmez.
    """
    askiya_alinan: list[Account] = []
    bagli = app_password.hesap_satirlari(
        Account.objects.filter(membership_id=uyelik.pk).order_by("opened_at", "pk")
    )
    for hesap in bagli:
        askida = hesaplar.uyelik_askisi(hesap)
        if askida is not None:
            askiya_alinan.append(askida)
    return askiya_alinan


def _acik_donem() -> OabTerm | None:
    donem: OabTerm | None = OabTerm.objects.filter(status=TermStatus.ACIK).first()
    return donem


def _bagli_uyelikler() -> set[int]:
    """Açık (kapalı olmayan) bir hesaba bağlı üyeliklerin kimlikleri."""
    return set(
        Account.objects.exclude(status=AccountStatus.KAPALI)
        .filter(membership__isnull=False)
        .values_list("membership_id", flat=True)
    )


def _gorevli_adaylar(donem: OabTerm) -> list[tuple[str, OrganMembership]]:
    """Açık dönemde hesap alabilecek görevliler: (rol, üyelik), kurul ve kadro sırasıyla."""
    adaylar: list[tuple[str, OrganMembership]] = []
    for uyelik in selectors.gorevdeki_asillar(donem, OrganType.YONETIM_KURULU):
        rol = GOREV_ROLLERI.get(uyelik.role)
        if rol is not None:
            adaylar.append((rol, uyelik))
    adaylar.extend(
        (AccountRole.DENETLEME_KURULU.value, uyelik)
        for uyelik in selectors.gorevdeki_asillar(donem, OrganType.DENETLEME_KURULU)
    )
    return adaylar


def uygun_uyelikler(rol: str) -> list[dict[str, Any]]:
    """Rolün hesap açılabilecek üyelikleri ("Yeni hesap" penceresinde kişi ve üyelik seçimi).

    Açık dönemin görevdeki asılları arasından, kurala uyan (`_acilis_engeli`) ve açık hesaba bağlı
    olmayan üyelikler; kadro sırasıyla. Satır: `{uyelik, kisi, ad_soyad, organ, gorev, gorev_etiketi,
    donem}`. Çözülemeyen ad boştur (ekranda "okunamadı"). Okuma yalnız program yöneticisinindir
    (çağıran `hesaplar.kullanici_secenekleri` yetki kapısından geçer); hiçbir şey yazmaz.
    """
    donem = _acik_donem()
    if donem is None or rol not in hesaplar.ORGAN_ROLLERI:
        return []
    bagli = _bagli_uyelikler()
    satirlar: list[dict[str, Any]] = []
    for aday_rolu, uyelik in _gorevli_adaylar(donem):
        if aday_rolu != rol or uyelik.pk in bagli or _acilis_engeli(rol, uyelik) is not None:
            continue
        kisi = uyelik.person
        satirlar.append(
            {
                "uyelik": uyelik.pk,
                "kisi": uyelik.person_id,
                "ad_soyad": None if has_corrupt(kisi) else kisi.full_name,
                "organ": uyelik.organ,
                "gorev": uyelik.role,
                "gorev_etiketi": str(MembershipRole(uyelik.role).label),
                "donem": uyelik.term_id,
            }
        )
    return satirlar


def hesap_onerileri() -> list[dict[str, Any]]:
    """Program yöneticisinin hesap önerileri (modül başlığı; kişisiz kodlar ve kimlikler).

    * `{tur: "HESAP_KAPAT", hesap, rol, neden}`: üyelik düştüğü ya da görev değiştiği için askıdaki
      ve bağı BUGÜN geçersiz hesap (neden bugünkü geçersizlik: `UYELIK_DUSTU` · `GOREV_BOLUMU`).
    * `{tur: "HESAP_ASKIDAN_CIKAR", hesap, rol}`: üyelik ya da görev nedeniyle askıdaki ama bağı
      yeniden geçerli olmuş hesap (ör. görev aynı üyeye döndü). Askı kendiliğinden kalkmaz (tasarım
      §4.4.5; askıdan çıkarma program yöneticisinin elle eylemidir, Kullanıcılar satırı).
    * `{tur: "HESAP_AC", rol, uyelik, kisi}`: açık dönemde görevli (dört YK görevi ve Denetleme
      Kurulunun görevdeki asılları) olup açık hesaba bağlı olmayan üyelik; kurul ve kadro sırasıyla.

    Askıdaki hesapların kalemleri (kapanış ve askıdan çıkarma) açılış sırasıyladır ve yalnız kaydı ve
    izi tutan satırdan çıkar (`hesaplar.kaydi_tutan_satirlar`): tutmayan satıra servisler dokunmaz,
    öneri de yapılmaz (Kullanıcılar satırı kaydın durumunu söyler). Bağın kararı askıdan çıkarmanın
    ve parola sıfırlamanınkiyle aynı işlevdir (`hesaplar.bag_gecersizlik_nedeni`).

    Yalnız program yöneticisi (yetki kapısı `Eylem.HESAP_YONETIMI`); hiçbir şey yazmaz.
    """
    yetki_oturum(Eylem.HESAP_YONETIMI)
    oneriler: list[dict[str, Any]] = []
    for hesap in hesaplar.kaydi_tutan_satirlar(
        Account.objects.filter(
            status=AccountStatus.ASKIDA, suspend_reason__in=SuspendReason.values
        ).order_by("opened_at", "pk")
    ):
        # Neden bugünkü geçersizliktir; bağı yeniden geçerli olmuş askı kapanış değil askıdan
        # çıkarma önerisidir.
        neden = hesaplar.bag_gecersizlik_nedeni(hesap)
        if neden is not None:
            oneriler.append(
                {"tur": ONERI_KAPAT, "hesap": str(hesap.id), "rol": hesap.role, "neden": neden}
            )
        else:
            oneriler.append({"tur": ONERI_ASKIDAN_CIKAR, "hesap": str(hesap.id), "rol": hesap.role})
    donem = _acik_donem()
    if donem is not None:
        bagli = _bagli_uyelikler()
        oneriler.extend(
            {"tur": ONERI_AC, "rol": rol, "uyelik": uyelik.pk, "kisi": uyelik.person_id}
            for rol, uyelik in _gorevli_adaylar(donem)
            if uyelik.pk not in bagli
        )
    return oneriler


#: `okul`'un kayıt defterine verilen kurallar (`AppConfig.ready`).
KURALLAR: Final = HesapBagiKurallari(
    bagla=bagla,
    gecersizlik_nedeni=gecersizlik_nedeni,
    uygun_uyelikler=uygun_uyelikler,
)
