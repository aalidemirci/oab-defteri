"""Geçiş kurulumu, organ kısmı (tasarım §7.9 adım 1-4 ve "Senaryolar"; plan F1c-8 ve "8. adımın kararı").

Program bir okula çoğu zaman dönemin ortasında girer. Geçiş kurulumu programdan önce başlamış dönemi ve
görevdeki kurulu kuralları delmeden programa alır. Yalnız ilk dönemde açılır; sihirbazda başlar
(`okul.services.setup` adım anahtarı `birlik_donemi`, atlanabilir), atlanırsa Genel Bakış yol
haritasından sürer (`yol_haritasi_durumu`; ekranlar F1c'nin 11. ve 12. adımında). Kaydı `yonetici`
yazar (`Eylem.BIRLIK_DONEMI_YAZMA`, M1; dayanağı §7.9). Mali kısım (adım 5-8) F3, kantin ve servisin
süren sözleşmeleri F5 ve F6'dadır.

ADIMLAR:

1. **İlk birlik dönemi** (`ilk_donemi_ac`): dönem doğrudan `ACIK` açılır, `opened_by_assembly` boştur
   (`donemler.create_term`). Ders yılı dönem başını (son olağan genel kurulun günü) kapsayan yıldır;
   yoksa ret: sihirbaz o geçmiş yılı etkin olmadan açar (`okul.services.school_year`), sonra bu adımı
   yineler. Programa başlama günü verilmezse bugündür; dönem başından önce olamaz (sert). Son genel
   kurulun üzerinden bir yıl geçmişse dönem yine açılır, görev süresi uyarısı döner
   (`yonetim_kurulu.gorev_suresi_yil`, `denetleme_kurulu.gorev_suresi_yil`; md. 12/2, 14/2): uyarı kadro
   okumasının uyarısıdır, yazmaz ve gerekçe istemez (`uyelikler.kadro_uyarilari` ile aynı ölçü).
2. **Görevdeki kurul** (`devralinan_ekle`, `devralinan_temsilci_ekle`): her üye `source = DEVRALINAN`
   üyeliktir, aday şartı aranmaz; koltuk uygunluğu (kişi türü, müdür yasağı, aynı kişi iki kurulda,
   tek koltuk, görev tekilliği) yine serttir (`uyelikler.assign_membership`). Seçilme günü verilmezse
   dönem başıdır (görevdeki kurulu son olağan genel kurul seçti). Görevli devralınan kayıt hesap açmaya
   yeter (`hesap_baglari`; hesabı `yonetici` açar, E63 basılır, tasarım §4.4.5).
3. **Programdan önceki seçilme sayıları** (`sayac_beyani`): görevdeki ve aday olacak kişiler için toplu
   beyan; her alanda sayı ya da "bilinmiyor" (`None`). "Bilinmiyor" denen her kişi ve kural için uyum
   satırı `SAPMA` olur ve hepsi TEK gerekçeye bağlanır (kök neden `sayac_kok_nedeni`; R5, O3): sonraki
   beyanlarda ve F2'nin seçimlerinde aynı kök nedenle yeniden sorulmaz. Beyan görevdeki seçimi içerir,
   `DEVRALINAN` üyelik sayıma ayrıca girmez; beyanın kendisi sınırla karşılaştırılır (kullanıcı
   kararı 12.11.2026): görevdeki devralınan yönetim kurulu üyesinde md. 12/4, Denetleme Kurulu
   başkanında md. 14/3 sınırı aşılırsa üyelikte uyarı + gerekçe (`uyelikler.sayaci_yeniden_denetle`).
   Sayı girilince kişinin açık satırı kapanır; dönemin üyeliklerindeki sayaç denetimi yeniden koşar:
   uygunsa açık satır kapanır, sınır aşılıyorsa uyarı + gerekçe, program kaydında beyan bilinmiyorsa
   açık eksik satırı toplu gerekçeye bağlanır (devralınan kayıtta "bilinmiyor" satır açmaz).
4. **Karar defteri** (`karar_defteri_kaydet`): programdan önceki son sıra no ve sayfa zorunludur; tasdik
   kuralla denetlenir (`kurullar.tasdik_denetimi`, `yonetim_kurulu.karar_defteri_noter_tasdiki`,
   md. 23/2; plan F1c 8. adım notları): tasdik bilgisi (makam ve gün) yoksa ya da makam noter değilse
   (il/ilçe millî eğitim müdürlüğü tasdiki karar defterine yetmez; tasarım `OfficialBook` "yanlış
   makamla kullanım") uyarı + gerekçe, konu defter, gerekçe defter başına bir (kök neden defterin
   kimliği, O3). Gelir-gider defteri F3'tedir.

İPTAL VE DÜZELTME (plan F1c 8. adımın kararı; altın kural 4): geçiş kaydında alan değişmez.

* Dönem `ACIK` → `IPTAL` (`donemi_iptal_et`; gerekçe şifreli `cancel_reason`): dönemin aday ya da seçilmiş
  üyeliği kalmamalıdır (önce üyelikler iptal edilir: bağlı hesaplar aynı işlemde askıya alınır);
  karar defterinin açık tasdik satırı bu döneme bağlıysa önce defter kaydı iptal edilir (defter
  dönemsizdir, satırı dönemlidir: dönemle birlikte iptal edilen dönemde kalır, yeni dönemde görünmez
  ve kapanamazdı); dönemin veli satırları dönemsiz kalır, sonraki ilk dönem onları bağlar.
* Devralınan üyelik `IPTAL` (`devralinan_iptal_et` → `uyelik_gecisleri.uyeligi_iptal_et`).
* Karar defteri `KULLANIMDA` → `IPTAL` (`karar_defterini_iptal_et`; gerekçe şifreli).
* Sayaç beyanı yeni beyanla gerekçeli düzeltilir: verilmiş sayı değişirse ya da "bilinmiyor"a dönerse
  düzeltme gerekçesi zorunludur; gerekçe kapanmış bir akış satırında (`DUZELTME_AKISI`) durur, kişinin
  iz satırı ona bağlanır. "Bilinmiyor"dan sayıya geçiş düzeltme değil, bilginin girilmesidir.

Hepsi "Geçiş kurulumu tamamlandı" işaretine (`gecisi_tamamla`; `OabTerm.transition_completed_on`) kadar
açıktır, sonra kilitlidir (`GecisKapali`, 409; `donem_kilidi.gecis_yazma_denetimi`). İşaret eksik adım
bırakılsa da konabilir: geçiş atlanabilir, eksik adım pano yol haritasında görünür.

İZ: geçişin bütün yazmaları `label = GECIS`'tir (tasarım §4.6.2, §7.9; `denetim_izi.etiketle`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Final

from django.db import transaction
from django.utils import timezone

from apps.oab.hatalar import KisiPasif
from apps.oab.kurallar import yazma_kapisi
from apps.oab.kurallar.erisim import denetle as paket_denetle
from apps.oab.models import (
    BookKind,
    BookStatus,
    ComplianceItem,
    ElectedBy,
    MembershipRole,
    MembershipSource,
    MembershipStatus,
    OabPerson,
    OabTerm,
    OfficialBook,
    OrganMembership,
    OrganType,
    PersonStatus,
    SeatType,
    TermStatus,
)
from apps.oab.services import (
    donem_kilidi,
    donemler,
    iz,
    kisiler,
    kurullar,
    temsilciler,
    uyelik_gecisleri,
    uyelikler,
    uyum,
)
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AuditLabel, SchoolYear
from apps.okul.services import app_password

#: Sayaç beyanının gerekçeli düzeltmesi (akış satırı; yazıldığı anda kapanır).
DUZELTME_AKISI: Final = "akis.gecis_sayac_beyani_duzeltmesi"
DUZELTME_MESAJI: Final = (
    "Programdan önceki seçilme sayısı beyanı geçiş kurulumunda düzeltildi (program kaydıdır)."
)
#: "Bilinmiyor" beyanının uyum satırı iletisi (alan → ileti).
BILINMIYOR_MESAJI: Final[dict[str, str]] = {
    "external_yk_terms": (
        "Programdan önceki yönetim kurulu seçilme sayısı bilinmiyor; seçilme sınırı bu kişi için "
        "denetlenemiyor."
    ),
    "external_dk_chair_terms": (
        "Programdan önceki Denetleme Kurulu başkanlığı sayısı bilinmiyor; başkanlık sınırı bu kişi "
        "için denetlenemiyor."
    ),
}

#: Son genel kuruldan bu yana süresi sayılan kurullar (md. 12/2, 14/2; senaryo "bir yıl geçmişse").
GOREV_SURESI_KURALLARI: Final = (
    "yonetim_kurulu.gorev_suresi_yil",
    "denetleme_kurulu.gorev_suresi_yil",
)

#: Yol haritasının durumu ve açık adımları (kişisiz anahtarlar; `yol_haritasi_durumu`).
DURUM_BASLAMADI: Final = "BASLAMADI"
DURUM_SURUYOR: Final = "SURUYOR"
DURUM_TAMAMLANDI: Final = "TAMAMLANDI"
DURUM_GEREKMIYOR: Final = "GEREKMIYOR"
ADIM_DONEM: Final = "donem"
ADIM_KURUL: Final = "kurul"
ADIM_SAYAC: Final = "sayac_beyani"
ADIM_KARAR_DEFTERI: Final = "karar_defteri"
ADIM_TAMAMLA: Final = "tamamla"

DERS_YILI_YOK = (
    "Dönem başını kapsayan ders yılı tanımlı değil; o ders yılını (etkin olmadan) ekleyip yeniden "
    "deneyin."
)
DERS_YILI_KAPSAMIYOR = "Seçilen ders yılı dönem başını kapsamıyor."
GECIS_DONEMI_YOK = "Geçiş kurulumunun birlik dönemi açılmadı."
SAYAC_DEGERI_GECERSIZ = "Seçilme sayısı sıfır ya da pozitif tam sayı ya da “bilinmiyor” olmalıdır."
AYNI_KISI_IKI_KEZ = "Bir kişi beyanda bir kez yer alır."
DUZELTME_GEREKCESI_GEREKLI = "Verilmiş beyanın düzeltmesi için gerekçe yazılmalıdır."
DEFTER_BILGISI_GEREKLI = (
    "Karar defterinin programdan önceki son sıra no'su ve sayfası girilmelidir."
)
KARAR_DEFTERI_VAR = (
    "Kullanımdaki karar defteri zaten kayıtlı; yanlışsa önce iptal edip yeniden girin."
)
DEFTER_GECIS_KAYDI_DEGIL = "Yalnız geçiş kurulumunda girilen kullanımdaki defter iptal edilir."
IPTAL_GEREKCESI_GEREKLI = "İptal gerekçesi yazılmalıdır."
DONEMIN_UYELIKLERI_VAR = "Dönemde aday ya da seçilmiş üyelik var; dönem iptal edilmeden önce bu üyelikler iptal edilmelidir."
DONEMIN_DEFTERI_VAR = (
    "Karar defterinin tasdik gerekçesi bu döneme bağlı; dönem iptal edilmeden önce karar defteri "
    "kaydı iptal edilmelidir."
)
DEVRALINAN_DEGIL = "Bu yoldan yalnız devralınan üyelik iptal edilir."


class _Yok:
    """Beyanda verilmemiş alanın işareti ("bilinmiyor" `None`'dan ayrı)."""

    def __repr__(self) -> str:
        return "YOK"


#: Alan beyanda yok: kişinin o alanı değişmez.
YOK: Final = _Yok()


@dataclass(frozen=True)
class SayacBeyani:
    """Bir kişinin beyanı: sayı, "bilinmiyor" (`None`) ya da verilmedi (`YOK`)."""

    kisi: OabPerson
    yk: int | None | _Yok = YOK
    dk_baskanlik: int | None | _Yok = YOK

    def alanlar(self) -> dict[str, int | None]:
        verilen: dict[str, Any] = {
            "external_yk_terms": self.yk,
            "external_dk_chair_terms": self.dk_baskanlik,
        }
        return {ad: deger for ad, deger in verilen.items() if not isinstance(deger, _Yok)}


@dataclass(frozen=True)
class DonemAcilisi:
    """İlk dönemin açılışı ve (kaydedilmeyen) görev süresi uyarıları."""

    donem: OabTerm
    uyarilar: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class SayacBeyaniSonucu:
    """Beyanın açtığı ya da açık tuttuğu "bilinmiyor" satırları ve düzeltme kayıtları."""

    bilinmeyenler: list[ComplianceItem] = field(default_factory=list)
    duzeltmeler: list[ComplianceItem] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
def _yetki() -> None:
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.BIRLIK_DONEMI_YAZMA)


def gecis_donemi() -> OabTerm | None:
    """Geçiş kurulumunun dönemi: genel kurulsuz açılmış, iptal edilmemiş dönem (yoksa `None`)."""
    donem: OabTerm | None = (
        OabTerm.objects.select_related("rule_package")
        .filter(opened_by_assembly__isnull=True)
        .exclude(status=TermStatus.IPTAL)
        .order_by("pk")
        .first()
    )
    return donem


def _acik_gecis(donem: OabTerm | None) -> OabTerm:
    """Yazılacak geçiş dönemi: verilmezse geçiş dönemi; geçişe açık değilse `GecisKapali`."""
    hedef = donem if donem is not None else gecis_donemi()
    if hedef is None:
        raise ValueError(GECIS_DONEMI_YOK)
    return donem_kilidi.gecis_yazma_denetimi(hedef)


def sayac_kok_nedeni(donem: OabTerm) -> str:
    """Programdan önceki seçilme sayılarının "bilinmiyor" beyanının toplu gerekçe kök nedeni (§5 O3).

    F2'nin seçimleri ve sonraki beyanlar aynı kök nedenle bağlanır, gerekçe yeniden sorulmaz. Dönemin
    kimliğini taşır: iptal edilen geçişin gerekçesi yeni geçişe bağlanmaz."""
    return f"gecis.sayac_beyani:{donem.pk}"


def ders_yili_bul(gun: date) -> SchoolYear | None:
    """Günü kapsayan (silinmemiş) ders yılı; yoksa `None`."""
    yil: SchoolYear | None = (
        SchoolYear.objects.filter(start_date__lte=gun, end_date__gte=gun).order_by("pk").first()
    )
    return yil


def gorev_suresi_uyarilari(donem: OabTerm, *, tarih: date | None = None) -> list[dict[str, Any]]:
    """Son genel kuruldan (dönem başı) bu yana görev süresi doldu mu (md. 12/2, 14/2)? Kayıt yazmaz.

    Her uyarı kural kimliğini (`kural`) ve denetim sonucunu (ileti, atıf, paket) taşır."""
    gun = tarih or timezone.localdate()
    gozlenen = uyelikler.gorev_suresi_gozlenen(donem, gun)
    uyarilar: list[dict[str, Any]] = []
    for kural_id in GOREV_SURESI_KURALLARI:
        sonuc = paket_denetle(kural_id, gozlenen, tarih=gun, donem=donem)
        if sonuc["durum"] == "uyari":
            uyarilar.append({"kural": kural_id, **sonuc})
    return uyarilar


# ---------------------------------------------------------------------------
# 1. İlk birlik dönemi
# ---------------------------------------------------------------------------
@transaction.atomic
def ilk_donemi_ac(
    *,
    start_date: date,
    program_start_date: date | None = None,
    school_year: SchoolYear | None = None,
    name: str = "",
) -> DonemAcilisi:
    """Geçiş kurulumunun 1. adımı (modül başlığı). Satırlar `GECIS` etiketlidir (`create_term`)."""
    yazma_kapisi()
    _yetki()
    yil = school_year if school_year is not None else ders_yili_bul(start_date)
    if yil is None:
        raise ValueError(DERS_YILI_YOK)
    if not yil.start_date <= start_date <= yil.end_date:
        raise ValueError(DERS_YILI_KAPSAMIYOR)
    donem = donemler.create_term(
        name=name.strip() or f"{yil.name} birlik dönemi",
        school_year=yil,
        start_date=start_date,
        program_start_date=(
            program_start_date if program_start_date is not None else timezone.localdate()
        ),
    )
    return DonemAcilisi(donem=donem, uyarilar=gorev_suresi_uyarilari(donem))


@transaction.atomic
def donemi_iptal_et(donem: OabTerm, *, cancel_reason: str) -> OabTerm:
    """Yanlış girilmiş geçiş dönemi `ACIK` → `IPTAL` (`DURUM`; modül başlığı "İptal ve düzeltme")."""
    _yetki()
    metin = cancel_reason.strip()
    if not metin:
        raise ValueError(IPTAL_GEREKCESI_GEREKLI)
    guncel = donem_kilidi.gecis_yazma_denetimi(donem)
    if (
        OrganMembership.objects.filter(term=guncel)
        .filter(status__in=(MembershipStatus.ADAY, MembershipStatus.SECILDI))
        .exists()
    ):
        raise ValueError(DONEMIN_UYELIKLERI_VAR)
    if ComplianceItem.objects.filter(
        term=guncel, rule_id=kurullar.TASDIK_KURALI, resolved_at__isnull=True
    ).exists():
        raise ValueError(DONEMIN_DEFTERI_VAR)
    with denetim_izi.etiketle(AuditLabel.GECIS):
        onceki = denetim_izi.anlik(guncel)
        guncel.status = TermStatus.IPTAL
        guncel.cancel_reason = metin
        guncel.updated_by_id = iz.yazar_hesabi()
        guncel.save(update_fields=["status", "cancel_reason", "updated_at", "updated_by"])
        denetim_izi.degisiklik(guncel, onceki=onceki)
        donemler.veli_listesini_coz(guncel)
    return guncel


# ---------------------------------------------------------------------------
# 2. Görevdeki kurul
# ---------------------------------------------------------------------------
@transaction.atomic
def devralinan_ekle(
    *,
    person: OabPerson,
    organ: str,
    seat_type: str = SeatType.ASIL,
    elected_by: str = ElectedBy.GENEL_KURUL,
    seat_group: str = "",
    role: str = MembershipRole.UYE,
    start_date: date | None = None,
    term: OabTerm | None = None,
    **alanlar: Any,
) -> OrganMembership:
    """Görevdeki yönetim kurulu ya da Denetleme Kurulu üyesi (`DEVRALINAN`; modül başlığı, adım 2)."""
    yazma_kapisi()
    _yetki()
    donem = _acik_gecis(term)
    return uyelikler.assign_membership(
        term=donem,
        person=person,
        organ=organ,
        seat_type=seat_type,
        elected_by=elected_by,
        seat_group=seat_group,
        role=role,
        source=MembershipSource.DEVRALINAN,
        start_date=start_date or donem.start_date,
        **alanlar,
    )


@transaction.atomic
def devralinan_temsilci_ekle(
    *,
    person: OabPerson,
    representation: str,
    seat_type: str = SeatType.ASIL,
    start_date: date | None = None,
    evidence_note: str = "",
    term: OabTerm | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> OrganMembership:
    """Görevdeki birlik temsilcisi (`DEVRALINAN`; tasarım §7.9 adım 2 "temsilciler")."""
    yazma_kapisi()
    _yetki()
    donem = _acik_gecis(term)
    return temsilciler.temsilci_ekle(
        term=donem,
        person=person,
        representation=representation,
        seat_type=seat_type,
        start_date=start_date or donem.start_date,
        source=MembershipSource.DEVRALINAN,
        evidence_note=evidence_note,
        gerekce=gerekce,
    )


@transaction.atomic
def devralinan_iptal_et(uyelik: OrganMembership, *, cancel_reason: str) -> OrganMembership:
    """Yanlış girilmiş devralınan üyelik `IPTAL` (gerekçe şifreli; bağlı hesap aynı işlemde askıda)."""
    _yetki()
    guncel = OrganMembership.objects.select_related("term").get(pk=uyelik.pk)
    if guncel.source != MembershipSource.DEVRALINAN:
        raise ValueError(DEVRALINAN_DEGIL)
    donem_kilidi.gecis_yazma_denetimi(guncel.term)
    return uyelik_gecisleri.uyeligi_iptal_et(guncel, cancel_reason=cancel_reason)


# ---------------------------------------------------------------------------
# 3. Programdan önceki seçilme sayıları
# ---------------------------------------------------------------------------
def _sayac_degeri_gecerli(deger: object) -> bool:
    if deger is None:
        return True
    return isinstance(deger, int) and not isinstance(deger, bool) and deger >= 0


#: Sayaç kuralı → kişinin alanı (`kisiler.SAYAC_KURALLARI`'nın tersi).
_KURALIN_ALANI: Final[dict[str, str]] = {
    kural: alan for alan, kural in kisiler.SAYAC_KURALLARI.items()
}


@transaction.atomic
def sayac_beyani(
    beyanlar: list[SayacBeyani],
    *,
    gerekce: str = "",
    duzeltme_gerekcesi: str = "",
    term: OabTerm | None = None,
) -> SayacBeyaniSonucu:
    """Toplu sayaç beyanı (modül başlığı, adım 3). `gerekce`: "bilinmiyor" beyanının ve beyanla doğan
    sınır uyarısının gerekçesi (toplu); `duzeltme_gerekcesi`: verilmiş beyanın düzeltmesi."""
    yazma_kapisi()
    app_password.require_password_set()
    _yetki()
    donem = _acik_gecis(term)
    kimlikler = [beyan.kisi.pk for beyan in beyanlar]
    if len(set(kimlikler)) != len(kimlikler):
        raise ValueError(AYNI_KISI_IKI_KEZ)
    for beyan in beyanlar:
        if not all(_sayac_degeri_gecerli(deger) for deger in beyan.alanlar().values()):
            raise ValueError(SAYAC_DEGERI_GECERSIZ)
    gun = timezone.localdate()
    toplu = uyum.Gerekce(metin=gerekce, kok_neden=sayac_kok_nedeni(donem))
    duzeltme = uyum.Gerekce(
        metin=duzeltme_gerekcesi, kok_neden=f"gecis.sayac_duzeltmesi:{uuid.uuid4().hex}"
    )
    sonuc = SayacBeyaniSonucu()
    with denetim_izi.etiketle(AuditLabel.GECIS):
        for beyan in beyanlar:
            _kisinin_beyani(beyan, donem, gun=gun, toplu=toplu, duzeltme=duzeltme, sonuc=sonuc)
    return sonuc


def _kisinin_beyani(
    beyan: SayacBeyani,
    donem: OabTerm,
    *,
    gun: date,
    toplu: uyum.Gerekce,
    duzeltme: uyum.Gerekce,
    sonuc: SayacBeyaniSonucu,
) -> None:
    kisi = OabPerson.objects.get(pk=beyan.kisi.pk)
    if kisi.status != PersonStatus.AKTIF:
        raise KisiPasif
    alanlar = beyan.alanlar()
    degisen = [ad for ad, deger in alanlar.items() if getattr(kisi, ad) != deger]
    duzeltilen = [ad for ad in degisen if getattr(kisi, ad) is not None]
    bag: ComplianceItem | None = None
    if duzeltilen:
        if not duzeltme.metin.strip():
            raise ValueError(DUZELTME_GEREKCESI_GEREKLI)
        bag = uyum.duzeltme_kaydi(
            DUZELTME_AKISI, DUZELTME_MESAJI, donem=donem, konu=kisi, gerekce=duzeltme
        )
        sonuc.duzeltmeler.append(bag)
    if degisen:
        onceki = denetim_izi.anlik(kisi)
        for ad in degisen:
            setattr(kisi, ad, alanlar[ad])
        kisi.updated_by_id = iz.yazar_hesabi()
        kisi.save(update_fields=[*degisen, "updated_at", "updated_by"])
        denetim_izi.degisiklik(kisi, onceki=onceki, compliance_item=None if bag is None else bag.pk)
    for ad, deger in alanlar.items():
        kural_id = kisiler.SAYAC_KURALLARI[ad]
        if deger is None:
            satir = uyum.bilinmeyen_beyan_sapmasi(
                kural_id,
                donem=donem,
                konu=kisi,
                mesaj=BILINMIYOR_MESAJI[ad],
                gerekce=toplu,
                tarih=gun,
            )
            if satir is not None:
                sonuc.bilinmeyenler.append(satir)
        else:
            uyum.acik_satiri_kapat(kural_id, donem=donem, konu=kisi)
    _uyelikleri_yeniden_denetle(kisi, donem, alanlar=alanlar, gun=gun, toplu=toplu)


def _uyelikleri_yeniden_denetle(
    kisi: OabPerson,
    donem: OabTerm,
    *,
    alanlar: dict[str, int | None],
    gun: date,
    toplu: uyum.Gerekce,
) -> None:
    """Dönemin seçilmiş ve düşmüş üyeliklerinde sayaç denetimi yeniden koşar (modül başlığı, adım 3;
    düşmüş kayıtta yalnız açık sayaç satırı, `uyelikler.sayaci_yeniden_denetle`): uygunsa açık satır
    kapanır, sınır aşılıyorsa uyarı + gerekçe (beyanın gerekçesi, kök nedensiz: kişiye özgüdür; gerekçe
    yoksa `GerekceGerekli`, beyan geri alınır), program kaydında beyan "bilinmiyor"sa açık eksik satırı
    toplu gerekçeye bağlanır. Görevdeki devralınan kayıt sayıma girmez, beyanı sınırla karşılaştırılır;
    "bilinmiyor" beyanında satır açılmaz (kişinin satırı yeter)."""
    uyelikler_ = OrganMembership.objects.filter(
        term=donem,
        person=kisi,
        status__in=(MembershipStatus.SECILDI, MembershipStatus.DUSTU),
        organ__in=(OrganType.YONETIM_KURULU, OrganType.DENETLEME_KURULU),
    ).order_by("pk")
    for uyelik in uyelikler_:
        kisiye_ozgu = uyum.Gerekce(metin=toplu.metin) if toplu.metin.strip() else None
        sonuclar = uyelikler.sayaci_yeniden_denetle(uyelik, gerekce=kisiye_ozgu)
        for kural_id, denetim in sonuclar.items():
            alan = _KURALIN_ALANI.get(kural_id)
            if alan in alanlar and alanlar[alan] is None and denetim["durum"] == "eksik":
                uyum.bilinmeyen_beyan_sapmasi(
                    kural_id,
                    donem=donem,
                    konu=uyelik,
                    mesaj=BILINMIYOR_MESAJI[alan],
                    gerekce=toplu,
                    tarih=gun,
                )


# ---------------------------------------------------------------------------
# 4. Karar defteri
# ---------------------------------------------------------------------------
@transaction.atomic
def karar_defteri_kaydet(
    *,
    last_no_before_program: int | None,
    last_page_before_program: int | None,
    certified_by: str = "",
    certified_on: date | None = None,
    certification_no: str = "",
    page_count: int | None = None,
    opened_on: date | None = None,
    gerekce: str = "",
    term: OabTerm | None = None,
) -> OfficialBook:
    """Karar defterinin geçiş kaydı (modül başlığı, adım 4): son sıra no ve sayfa; tasdik bilgisi yoksa
    ya da makam noter değilse defter başına bir gerekçe (`kurullar.tasdik_denetimi`, md. 23/2)."""
    yazma_kapisi()
    _yetki()
    donem = _acik_gecis(term)
    if last_no_before_program is None or last_page_before_program is None:
        raise ValueError(DEFTER_BILGISI_GEREKLI)
    if (
        OfficialBook.objects.filter(kind=BookKind.KARAR_DEFTERI)
        .exclude(status=BookStatus.IPTAL)
        .exists()
    ):
        raise ValueError(KARAR_DEFTERI_VAR)
    with denetim_izi.etiketle(AuditLabel.GECIS):
        defter = kurullar.karar_defteri_olustur(
            certified_by=certified_by,
            certified_on=certified_on,
            certification_no=certification_no,
            page_count=page_count,
            last_no_before_program=last_no_before_program,
            last_page_before_program=last_page_before_program,
            opened_on=opened_on,
        )
        kurullar.tasdik_denetimi(defter, donem=donem, gerekce=gerekce)
    return defter


@transaction.atomic
def karar_defterini_iptal_et(defter: OfficialBook, *, cancel_reason: str) -> OfficialBook:
    """Yanlış girilmiş karar defteri kaydı `KULLANIMDA` → `IPTAL` (`DURUM`); açık tasdik satırı kapanır."""
    _yetki()
    metin = cancel_reason.strip()
    if not metin:
        raise ValueError(IPTAL_GEREKCESI_GEREKLI)
    donem = _acik_gecis(None)
    guncel = OfficialBook.objects.get(pk=defter.pk)
    if guncel.status != BookStatus.KULLANIMDA or guncel.last_no_before_program is None:
        raise ValueError(DEFTER_GECIS_KAYDI_DEGIL)
    with denetim_izi.etiketle(AuditLabel.GECIS):
        onceki = denetim_izi.anlik(guncel)
        guncel.status = BookStatus.IPTAL
        guncel.cancel_reason = metin
        guncel.updated_by_id = iz.yazar_hesabi()
        guncel.save(update_fields=["status", "cancel_reason", "updated_at", "updated_by"])
        denetim_izi.degisiklik(guncel, onceki=onceki)
        uyum.acik_satiri_kapat(kurullar.TASDIK_KURALI, donem=donem, konu=guncel)
    return guncel


# ---------------------------------------------------------------------------
# "Geçiş kurulumu tamamlandı" işareti ve yol haritası
# ---------------------------------------------------------------------------
@transaction.atomic
def gecisi_tamamla(term: OabTerm | None = None) -> OabTerm:
    """İşareti koyar (`GUNCELLE`, `transition_completed_on` bugün); geçiş kayıtları kilitlenir."""
    _yetki()
    guncel = _acik_gecis(term)
    with denetim_izi.etiketle(AuditLabel.GECIS):
        onceki = denetim_izi.anlik(guncel)
        guncel.transition_completed_on = timezone.localdate()
        guncel.updated_by_id = iz.yazar_hesabi()
        guncel.save(update_fields=["transition_completed_on", "updated_at", "updated_by"])
        denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel


def _sayac_beyani_eksik(donem: OabTerm) -> bool:
    """Devralınan yönetim kurulu üyesinde ya da Denetleme Kurulu başkanında beyan verilmemiş mi
    (sayı yok, "bilinmiyor" satırı da yok)? Kişinin şifreli alanları okunmaz (yalnız kimlik ve sayaç)."""
    gorevliler = OrganMembership.objects.filter(
        term=donem, source=MembershipSource.DEVRALINAN, status=MembershipStatus.SECILDI
    ).values_list(
        "organ", "role", "person_id", "person__external_yk_terms", "person__external_dk_chair_terms"
    )
    for organ, role, kisi_id, yk, dk in gorevliler:
        if organ == OrganType.YONETIM_KURULU:
            alan, deger = "external_yk_terms", yk
        elif organ == OrganType.DENETLEME_KURULU and role == MembershipRole.BASKAN:
            alan, deger = "external_dk_chair_terms", dk
        else:
            continue
        if deger is not None:
            continue
        bilinmiyor = ComplianceItem.objects.filter(
            term=donem,
            subject_type=denetim_izi.model_etiketi(OabPerson),
            subject_id=denetim_izi.kimlik_metni(OabPerson, kisi_id),
            rule_id=kisiler.SAYAC_KURALLARI[alan],
            resolved_at__isnull=True,
        ).exists()
        if not bilinmiyor:
            return True
    return False


def yol_haritasi_durumu() -> dict[str, Any]:
    """Geçiş kurulumunun Genel Bakış yol haritasındaki durumu (kişisiz: durum ve açık adım anahtarları).

    `GEREKMIYOR`: dönem genel kurulla açılmış (F2'nin yolu; yeni okul geçişi atlar). `BASLAMADI`: dönem
    yok (geçiş atlanmış ya da başlamamış; madde açık kalır). `SURUYOR`: geçiş dönemi açık, işaret yok;
    açık adımlar sırasıyla döner. `TAMAMLANDI`: işaret konmuş. `okul.services.setup` kayıt defterinden
    okur (`register_transition_status`).
    """
    canli = OabTerm.objects.exclude(status=TermStatus.IPTAL)
    gecis_satiri = (
        canli.filter(opened_by_assembly__isnull=True)
        .order_by("pk")
        .values("pk", "status", "transition_completed_on")
        .first()
    )
    if gecis_satiri is None:
        if canli.filter(opened_by_assembly__isnull=False).exists():
            return {"state": DURUM_GEREKMIYOR, "open_steps": []}
        return {"state": DURUM_BASLAMADI, "open_steps": [ADIM_DONEM]}
    if (
        gecis_satiri["transition_completed_on"] is not None
        or gecis_satiri["status"] != TermStatus.ACIK
    ):
        return {"state": DURUM_TAMAMLANDI, "open_steps": []}
    donem = OabTerm(pk=gecis_satiri["pk"])  # yalnız kimlikle süzülür; şifreli alan okunmaz
    adimlar: list[str] = []
    if not OrganMembership.objects.filter(
        term=donem, source=MembershipSource.DEVRALINAN, status=MembershipStatus.SECILDI
    ).exists():
        adimlar.append(ADIM_KURUL)
    if _sayac_beyani_eksik(donem):
        adimlar.append(ADIM_SAYAC)
    if (
        not OfficialBook.objects.filter(kind=BookKind.KARAR_DEFTERI)
        .exclude(status=BookStatus.IPTAL)
        .exists()
    ):
        adimlar.append(ADIM_KARAR_DEFTERI)
    adimlar.append(ADIM_TAMAMLA)
    return {"state": DURUM_SURUYOR, "open_steps": adimlar}
