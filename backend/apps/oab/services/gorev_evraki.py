"""Görev bölümü ve temsilci evrakı: E01, E02, E03 (tasarım §9.5-9.6; plan F1c 10. adım).

İçerik modeli (`shared.evrak.Belge`) burada BİR KEZ kurulur; Word ve PDF evrak hattının iki
çizicisidir (tek içerik, iki çizici; tasarım §9.1-1). Genel setin karşılıkları GNL-OAB-FR-006, 011
ve 022'dir; bölüm ve alanları şablondan, farkları tasarımdan ve plan kararlarından gelir (aşağıda
"Alınmayanlar"; pilot eşdeğerlik testi `test_evrak_kurallari.test_ilk_uc_evrak_pilot_esdegerligi`).

E01 — YÖNETİM KURULU GÖREV BÖLÜMÜ, İMZA YETKİSİ VE TEMSİLCİ KARAR TASLAĞI (md. 12/3, 13/4-5, 18/2).
Karar taslağıdır: başlıkta taslak ibaresi, imza bloklarının hemen üstünde KDT (tasarım §9.2). A.
Toplantı (görev bölümü toplantısı, `BoardMeeting(GOREV_BOLUMU)`; karar `TASLAK` iken karar defteri
sıra no ve sayfası "………"; geçişte toplantı yoksa bölüm boş basılır, basım uyarısı) · B. Görev
dağılımı ("kaçıncı dönem" seçilme sayacından, `uyelikler.secilme_sayaci`; "Beyan (okul uygulaması)"
sütunu okulun beyan günleridir, Yönetmelik maddesine bağlanmaz, KM-8) ve yedekler oy sırasıyla · C.
İmza yetkisi ve banka (müşterek imza: başkan + muhasip, yokluğunda başkan yardımcısı, md. 18/2; banka
satırları ve bankaya bildirim "………", model F3'tedir) · D. Çalışma düzeni ve birlik temsilcileri
(temsilciler E03'ün tek kaynağından, `temsilciler.temsilci_cizelgesi`: iki belgede aynı kişiler).
İmza: yönetim kurulunun görevdeki asıl üyeleri, görev unvanlarıyla.

E02 — DENETLEME KURULU GÖREV BÖLÜMÜ TUTANAĞI VE DENETİM PLANI (md. 14/1-4). Tutanaktır, karar taslağı
değildir: KDT ve taslak ibaresi yoktur. A. Toplantı (kurulu seçen genel kurulun günü,
`gorev_bolumu.dk_secen_genel_kurul_gunu`) · B. Üyeler ve görev bölümü (veli ya da kursiyer koltuğu
genel kurul seçimi, öğretmen koltukları öğretmenler kurulu seçimi ya da görevlendirme, ayrı
satırlarda; başkanın "kaçıncı başkanlık"ı sayaçtan) · C. Denetim planı (dönemin denetim planı
tarihleri, `OabTerm.dk_audit_plan_dates`; ara raporlar yönetim kuruluna, nihai rapor genel kurula,
md. 14/4). İmza: Denetleme Kurulunun görevdeki asıl üyeleri ve "Bilgi: Birlik Başkanı". Müdür bloğu
yoktur (tasarım §9.3, MB-15).

E03 — BİRLİK TEMSİLCİLERİNİN KURUL VE KOMİSYONLARA GÖREVLENDİRME ÇİZELGESİ. Karar taslağıdır (KDT,
taslak ibaresi). Satırlar YALNIZ temsilciler çizelgesindendir (tasarım §9.6 E03 satırı ve §6.4.4;
`temsilci_cizelgesi` tek kaynaktır: kademe, kantin ve kampüs koşulları, başkanın kendiliğinden üye
olduğu komisyonlar, pay dağıtım komisyonu yalnız seçildiyse). Yönetim kurulu kararı
`representative_decision`'dan okunur, boşsa "………". Rehberlik ve psikolojik danışma hizmetleri
yürütme komisyonu satırı görünürse, komisyonun öteki üyelerini öğretmenler kurulunun belirlediği
notu basılır (RPD Yön. md. 16/5; çizelgenin notu). İmza: Sekreter + Birlik Başkanı; "Teslim alan:
Okul Müdürü" (tasarım §9.3).

ALINMAYANLAR (plan F1c-10; genel setten): "katılanların çoğunluğu" (md. 13/3 karar yeter sayısını üç
der); "son iş günü" (md. 18/5 "her ayın sonunda"); beyanın Yönetmeliğe bağlanması; FR-011'in "Okul
Müdürü (görüldü)" satırı; FR-022'nin Öğretmenler Kurulu, genel kurul gözlemcileri ve alım komisyonu
satırları; form kodları. Kurum kodu basılmaz (plan F1c kararları). Genel kural: uyarı kutusu resmî
evraka basılmaz (tasarım §9.1-6); kural uyarıları kayıtta ve uyum satırlarındadır.

BOŞ ALAN. Görev ya da koltuk boşsa, kişinin adı okunamıyorsa ya da bilgi girilmemişse yerine "………"
basılır; basım uyarısı üretimin yanıtındadır (`Uretim.uyarilar`; tasarım §9.3 "görev boşsa basımda
uyarı verilir"). Uyarılar belgeye basılmaz. E01'in görev tablosu ve imzaları kurulun asıl koltuk
sayısını aşmaz: koltuklar doluyken boş görev yalnız uyarıdır, ayrı "………" satırı açılmaz.

ÜRETİM (`uret`). Üreten: E01 ve E03 yalnız sekreter ve program yöneticisi (tasarım §9.6 "Üreten";
uç kuralı ve servis kapısı), E02 yalnız Denetleme Kurulu (`Eylem.DK_GOREV_BOLUMU_YAZMA`, M8 ⁵). Sıra:
kural paketi kapısı → ilk hesap → rol → içerik (veriden) → iki çizim (işlem dışında) → TEK işlemde
evrak kaydı (`evrak_servisi.kaydet`; konu birlik dönemi; dönem kilidi O2 orada) ve iki dosya
(`evrak_servisi.dosya_ekle`; PDF ve Word). Kapanmış dönemde yeni sürüm yalnız aynı içerikle yazılır
(kaydın kuralı). Belgede üretim günü yoktur: yeniden üretim aynı veriden aynı içerik özetini verir.

BASIM (`bas`). Kaydedilmiş belgeyi her okur rol basar (tasarım §9.6, §4.4.2 "Okuma"): E01 ve E03'ü M2'yi,
E02'yi M8'i okuyan roller; başkan ve başkan yardımcısı okur ve basar, oluşturmaz. Dosya deposundan
okunur (`dosya_deposu.indirme_yaniti`; özet satırla doğrulanır), sonra AYNI istekte `BASIM` satırı
yazılır (kod ve dosyanın sha256'sı; kaydın kimliği belgenin konusu, birlik dönemi); satır
yazılamazsa dosya verilmez. Okuma rolünde de yazılır. Erişim günlüğüne girmez: belge veli adı
taşımaz, §4.6.4'ün türlerinden değildir.

Bütün sabit metinler sözlüğe girer (sözlük §1 "Görev bölümü ve temsilci evrakı (F1c)").
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Final

from django.db import transaction
from django.http import FileResponse, Http404
from django.utils import timezone

from apps.oab import selectors
from apps.oab.kurallar import YururlukteDegerYok, kural, yazma_kapisi
from apps.oab.models import (
    AssemblyKind,
    BoardDecision,
    BoardMeeting,
    DecisionKind,
    DecisionStatus,
    DocumentFormat,
    DocumentStatus,
    ElectedBy,
    GeneratedDocument,
    MeetingKind,
    MeetingStatus,
    MembershipRole,
    OabPerson,
    OabTerm,
    OrganMembership,
    OrganType,
    PersonKind,
    PersonStatus,
    Representation,
    SeatGroup,
    SeatType,
)
from apps.oab.services import evrak as evrak_servisi
from apps.oab.services import gorev_bolumu, temsilciler, uyelikler
from apps.okul import denetim_izi, name_match, rol_izinleri
from apps.okul.models import AccountRole, SchoolConfig
from apps.okul.oturum import yazar
from apps.okul.services import app_password, dosya_deposu
from shared import evrak
from shared.crypto import is_corrupt
from shared.exceptions import RolYetkisiz

E01: Final = "E01"
E02: Final = "E02"
E03: Final = "E03"
KODLAR: Final = (E01, E02, E03)

#: Belge adları (sözlük §2 "Belge adları"; katalogdaki kısaltmalar açık yazılır).
BELGE_ADLARI: Final[dict[str, str]] = {
    E01: "Yönetim kurulu görev bölümü, imza yetkisi ve temsilci karar taslağı",
    E02: "Denetleme Kurulu görev bölümü tutanağı ve denetim planı",
    E03: "Birlik temsilcilerinin kurul ve komisyonlara görevlendirme çizelgesi",
}
#: Kaydedilen dosyanın adının belge kısmı (sözlük §3 "Kaydedilen dosya adı"; ad + tarih).
DOSYA_ADI_KOKLERI: Final[dict[str, str]] = {
    E01: "Yönetim-Kurulu-Görev-Bölümü-Karar-Taslağı",
    E02: "Denetleme-Kurulu-Görev-Bölümü-Tutanağı",
    E03: "Temsilci-Görevlendirme-Çizelgesi",
}
#: Belgelerin biçimleri (tasarım §9.5: docx+pdf); dosya uzantıları.
BICIMLER: Final = (DocumentFormat.PDF, DocumentFormat.DOCX)
UZANTILAR: Final[dict[str, str]] = {DocumentFormat.PDF: "pdf", DocumentFormat.DOCX: "docx"}

#: Boş alanın yeri (tasarım §9.3 "blok ……… kalır").
BOS: Final = "………"

# ---------------------------------------------------------------------------
# Sabit metinler (sözlük §1 "Görev bölümü ve temsilci evrakı (F1c)")
# ---------------------------------------------------------------------------
E01_GIRIS: Final = (
    "Millî Eğitim Bakanlığı Okul-Aile Birliği Yönetmeliğinin (Yönetmelik) md. 12/3 hükmü gereği "
    "yönetim kurulu, üyeleri arasından bir başkan, bir başkan yardımcısı, bir muhasip ve bir "
    "sekreter seçerek görev ve iş bölümü yapar. Birliğin banka hesabındaki paralar birlik başkanı ve "
    "muhasip üyenin müşterek imzasıyla çekilir; birlik başkanının bulunmadığı durumlarda başkan "
    "yardımcısı yetkilidir (md. 18/2)."
)
E02_GIRIS: Final = (
    "Millî Eğitim Bakanlığı Okul-Aile Birliği Yönetmeliğinin (Yönetmelik) md. 14/1 hükmü gereği "
    "Denetleme Kurulu, genel kurulca seçilen bir veli ya da on sekiz yaşını doldurmuş bir kursiyer "
    "ile öğretmenler kurulunca seçilen iki öğretmenden oluşur; asıl üyeler aralarından bir başkan "
    "seçerek görev ve iş bölümü yapar. Kurul yılda en az iki defa yönetim kurulunun faaliyetlerini "
    "inceler; ara raporlarını yönetim kuruluna, nihai raporunu genel kurula sunar (md. 14/4)."
)

E01_BOLUMLER: Final = (
    "A. Toplantı",
    "B. Görev dağılımı (md. 12/3) ve beyanlar",
    "C. İmza yetkisi ve banka (md. 18/2)",
    "D. Çalışma düzeni ve birlik temsilcileri (md. 13/3-4, 18/5)",
)
E02_BOLUMLER: Final = (
    "A. Toplantı",
    "B. Üyeler ve görev bölümü (md. 14/1)",
    "C. Denetim planı (md. 14/4)",
)
E03_BOLUMLER: Final = ("A. Görevlendirme çizelgesi",)

#: İki sütunlu bilgi tablolarının başlıkları.
KONU_BILGI: Final = ("Konu", "Bilgi")
KONU_KARAR: Final = ("Konu", "Karar")

GENEL_KURUL_SECIM_TARIHI: Final = "Genel kurul (seçim) tarihi"
GENEL_KURUL_TARIHI: Final = "Genel kurul tarihi"
TOPLANTI: Final = "Görev bölümü toplantısı: tarih, saat ve yer"
KATILAN: Final = "Katılan asıl üye sayısı"
KARAR_DEFTERI: Final = "Karar defteri sıra no ve sayfası"

E01_GOREV_BASLIKLARI: Final = (
    "Görev",
    "Adı ve soyadı",
    "Kaçıncı dönem (md. 12/4)",
    "Beyan (okul uygulaması)",
    "İmza",
)
E01_YEDEK_BASLIKLARI: Final = ("Yedek sırası (md. 13/6)", "Adı ve soyadı", "Çağrılma tarihi")
#: Beyan hücresi: okulun suç engeli ve tek birlik beyanı uygulamasının günleri (tasarım §5.2.2).
BEYAN: Final = "Suç engeli: {suc} · Tek birlik: {tek}"

BANKA_HESABI: Final = "Birlik banka hesabı: banka, şube, Uluslararası Banka Hesap Numarası (IBAN)"
MUSTEREK_IMZA: Final = "Müşterek imza yetkilileri"
MUSTEREK_IMZA_DEGERI: Final = (
    "Birlik Başkanı {baskan} ve Muhasip {muhasip}; birlik başkanının bulunmadığı durumlarda "
    "Başkan Yardımcısı {yardimci}"
)
BANKAYA_BILDIRIM: Final = "Bankaya bildirim tarihi ve belgesi"

AYLIK_TOPLANTI: Final = "Aylık toplantı günü (md. 13/3)"
AYLIK_BILDIRIM: Final = "Okul müdürüne aylık yazılı bildirim (md. 18/5)"
#: Md. 18/5'in lafzı (bildirimin konusu dahil; korpus metniyle birebir).
AYLIK_BILDIRIM_DEGERI: Final = (
    "Birlik başkanı elde edilen gelirler, alınan bağışlar ve yönetim kurulu kararlarıyla yapılan "
    "harcamalara ilişkin bilgileri okul müdürüne her ayın sonunda yazılı olarak bildirir."
)
KOORDINASYON: Final = "Koordinasyon (md. 13/4)"
KOORDINASYON_DEGERI: Final = (
    "Gelir-gider işlemlerini muhasip, yazışmaları sekreter yürütür; harcamalar ile iş ve işlemlere "
    "ilişkin yazışmalar okul müdürü ile koordineli yapılır."
)
TEMSILCI_BASLIKLARI: Final = ("Kurul ya da komisyon", "Birlik temsilcisi")

E02_UYE_BASLIKLARI: Final = (
    "Seçim kanalı",
    "Adı ve soyadı",
    "Asıl ya da yedek",
    "Görevi",
    "Kaçıncı başkanlık (md. 14/3)",
    "İmza",
)
#: Koltuk grubunun satırdaki adı (veli koltuğunda kursiyer de olabilir, md. 14/1).
VELI_KOLTUGU: Final = "Veli"
KURSIYER_KOLTUGU: Final = "Kursiyer"
VELI_YA_DA_KURSIYER: Final = "Veli ya da kursiyer"
OGRETMEN_KOLTUGU: Final = "Öğretmen"
#: Seçim kanalının satırdaki adı.
KANALLAR: Final[dict[str, str]] = {
    ElectedBy.GENEL_KURUL: "genel kurul seçimi",
    ElectedBy.OGRETMENLER_KURULU: "öğretmenler kurulu seçimi",
    ElectedBy.MEM_GOREVLENDIRME: "il/ilçe millî eğitim müdürü onayıyla görevlendirme",
}
ASIL: Final = "Asıl"
YEDEK: Final = "Yedek"
YEDEKTEN_CAGRILDI: Final = "Asıl (yedekten çağrıldı: {gun})"

E02_PLAN_BASLIKLARI: Final = ("Denetim", "Planlanan tarih", "Rapor")
ARA_DENETIM: Final = "{sira}. ara denetim"
ARA_RAPOR: Final = "Ara rapor, bilgi ve gereği için yönetim kuruluna sunulur."
NIHAI_RAPOR: Final = "Nihai rapor"
NIHAI_RAPOR_DEGERI: Final = (
    "Yönetim kurulunun faaliyet dönemine ilişkin nihai rapor genel kurula sunulur."
)

E03_BASLIKLARI: Final = (
    "Sıra",
    "Kurul ya da komisyon",
    "Görevlendirilen",
    "Asıl ya da yedek",
    "Yönetim kurulu kararı: sıra no ve tarih",
)
KARAR_NO_TARIH: Final = "{no} · {tarih}"
BASKAN_SIFATIYLA: Final = "Birlik başkanı sıfatıyla"
#: Rehberlik komisyonunun notu (RPD Yön. md. 16/5; kuralın yorumu, tasarım §6.4.4): çizelgenin
#: satırı not taşıyınca basılır. Yönetmeliğin adı açık yazılır (sözlük §3 "Kısaltma").
RPD_NOTU: Final = (
    "Rehberlik ve psikolojik danışma hizmetleri yürütme komisyonunun diğer üyeleri her ders yılı "
    "başında öğretmenler kurulunda belirlenir (Millî Eğitim Bakanlığı Rehberlik ve Psikolojik "
    "Danışma Hizmetleri Yönetmeliği md. 16/5); yönetim kurulu kararı bu satırda öneri ve bilgi "
    "niteliğindedir."
)

#: İmza bloklarının unvanları.
UNVAN_DK_BASKANI: Final = "Denetleme Kurulu Başkanı"
UNVAN_BILGI_BASKAN: Final = "Bilgi: Birlik Başkanı"
UNVAN_SEKRETER: Final = "Sekreter"
UNVAN_BIRLIK_BASKANI: Final = "Birlik Başkanı"
UNVAN_TESLIM_ALAN: Final = "Teslim alan: Okul Müdürü"
#: Bir imza satırındaki en çok imza (yönetim kurulunun beş asıl üyesi tek satırda; fazlası alt satıra).
IMZA_SATIRI: Final = 5

# Basım uyarıları (üretimin yanıtında; belgeye basılmaz).
UYARI_TOPLANTI_YOK: Final = "Görev bölümü toplantısı kayıtlı değil; toplantı bölümü boş basıldı."
UYARI_GOREV_BOS: Final = "{gorev} görevi boş."
UYARI_KOLTUK_BOS: Final = "Kurulda boş koltuk var; satırı ……… basıldı."
UYARI_AD_OKUNAMADI: Final = "Bir kişinin adı okunamadı; adın yeri ……… basıldı."
UYARI_PLAN_YOK: Final = "Denetim planı tarihi girilmemiş; plan satırı ……… basıldı."
UYARI_MUDUR_ADI_YOK: Final = "Okul müdürünün adı okul bilgilerinde yok; adın yeri ……… basıldı."
UYARI_MUDUR_SOYADI: Final = (
    "Okul müdürünün adı okul bilgilerinde tek alanda; son sözcük soyadı sayıldı. Soyadı birden çok "
    "sözcükse imza bloğunu denetleyin."
)

KOD_GECERSIZ: Final = "Bu evrak bu yoldan üretilmez."

#: Yönetim kurulunun dört görevi, belgedeki sırasıyla (md. 12/3; görevler `gorev_bolumu`'ndadır).
GOREV_SIRASI: Final = (
    MembershipRole.BASKAN,
    MembershipRole.BASKAN_YARDIMCISI,
    MembershipRole.MUHASIP,
    MembershipRole.SEKRETER,
)
#: Üreten roller (tasarım §9.6 "Üreten"; E02'nin kapısı `Eylem.DK_GOREV_BOLUMU_YAZMA`).
URETEN_ROLLER: Final[dict[str, frozenset[str]]] = {
    E01: frozenset({AccountRole.YONETICI.value, AccountRole.SEKRETER.value}),
    E03: frozenset({AccountRole.YONETICI.value, AccountRole.SEKRETER.value}),
}
#: Basımın okuma satırı (tasarım §4.4.2 "Okuma"; §9.6 "Kaydedilmiş belgeyi her okur rol basabilir").
OKUMA_SATIRLARI: Final[dict[str, rol_izinleri.Satir]] = {
    E01: rol_izinleri.Satir.M2,
    E02: rol_izinleri.Satir.M8,
    E03: rol_izinleri.Satir.M2,
}


# ---------------------------------------------------------------------------
# Ortak yardımcılar
# ---------------------------------------------------------------------------
class _Uyarilar:
    """Basım uyarıları: sıralı, tekrarsız."""

    def __init__(self) -> None:
        self.liste: list[str] = []

    def ekle(self, metin: str) -> None:
        if metin not in self.liste:
            self.liste.append(metin)


def _gun(gun: date | None) -> str:
    """Tarih, RYUE md. 12/1 biçiminde (gg.aa.yyyy); yoksa "………"."""
    return BOS if gun is None else f"{gun:%d.%m.%Y}"


def _an(an: datetime | None) -> str:
    """An, Europe/Istanbul gün ve saatiyle (gg.aa.yyyy SS:dd); yoksa "………"."""
    if an is None:
        return BOS
    yerel = timezone.localtime(an) if timezone.is_aware(an) else an
    return f"{yerel:%d.%m.%Y %H:%M}"


def _ad(kisi: OabPerson | None, uyarilar: _Uyarilar) -> str:
    """Kişinin adı "Ad SOYAD" biçiminde (RYUE md. 17/2); kişi yoksa ya da adı okunamıyorsa "………"."""
    if kisi is None:
        return BOS
    if is_corrupt(kisi.first_name) or is_corrupt(kisi.last_name):
        uyarilar.ekle(UYARI_AD_OKUNAMADI)
        return BOS
    return evrak.ad_soyad(str(kisi.first_name), str(kisi.last_name))


def _olay_gunu(donem: OabTerm) -> date:
    """Kuralların ve çizelgenin günü: bugün; kapanmış dönemde dönemin son günü (yeniden üretim
    aynı değeri okusun)."""
    bugun = timezone.localdate()
    if donem.end_date is not None and donem.end_date < bugun:
        return donem.end_date
    return bugun


def _antet() -> evrak.Antet:
    okul = SchoolConfig.load()
    return evrak.birlik_anteti(okul_adi=okul.school_name, ilce=okul.district)


def _imzalar(sahipler: Sequence[evrak.ImzaSahibi], tarih: str = "") -> list[evrak.Imza]:
    """İmza blokları, satır başına en çok `IMZA_SATIRI` imza; tarih ilk satırdadır."""
    return [
        evrak.Imza(
            sahipler=tuple(sahipler[bas : bas + IMZA_SATIRI]), tarih=tarih if bas == 0 else ""
        )
        for bas in range(0, len(sahipler), IMZA_SATIRI)
    ]


def _gorev_bolumu_toplantisi(donem: OabTerm, organ: str) -> BoardMeeting | None:
    """Kurulun en son yapılmış görev bölümü toplantısı."""
    return (
        BoardMeeting.objects.filter(
            term=donem, organ=organ, kind=MeetingKind.GOREV_BOLUMU, status=MeetingStatus.YAPILDI
        )
        .order_by("-held_at", "-pk")
        .first()
    )


def _gorev_bolumu_karari(toplanti: BoardMeeting | None) -> BoardDecision | None:
    if toplanti is None:
        return None
    return (
        toplanti.decisions.filter(kind=DecisionKind.GOREV_BOLUMU)
        .exclude(status=DecisionStatus.IPTAL)
        .order_by("-pk")
        .first()
    )


def _karar_defteri(karar: BoardDecision | None) -> str:
    """Karar defteri sıra no ve sayfası: yalnız deftere işlenmiş kararda; taslakta "………"."""
    if karar is None or karar.status != DecisionStatus.DEFTERE_ISLENDI or karar.decision_no is None:
        return BOS
    sayfa = BOS if karar.page_no is None else str(karar.page_no)
    return f"{karar.decision_no} / {sayfa}"


def _secen_genel_kurul_gunu(donem: OabTerm, organ: str) -> date | None:
    """Kurulu seçen genel kurulun günü: olağanüstü genel kurulla yenilenen kurulda o günün, öteki
    hâllerde dönemi açan genel kurulun günü (`gorev_bolumu.dk_secen_genel_kurul_gunu` kalıbı)."""
    if organ == OrganType.DENETLEME_KURULU:
        return gorev_bolumu.dk_secen_genel_kurul_gunu(donem)
    gunler = [
        timezone.localdate(uyelik.assembly.first_meeting_at)
        for uyelik in selectors.gorevdeki_asillar(donem, organ)
        if uyelik.assembly is not None
        and uyelik.assembly.kind == AssemblyKind.OLAGANUSTU
        and uyelik.assembly.first_meeting_at is not None
    ]
    return max(gunler) if gunler else donem.start_date


def _toplanti_satirlari(
    donem: OabTerm,
    organ: str,
    toplanti: BoardMeeting | None,
    asil_sayisi: int | None,
    uyarilar: _Uyarilar,
    *,
    genel_kurul: str,
) -> list[tuple[str, str]]:
    """A bölümü. Toplantı kayıtlı değilse (geçiş) bölüm boş basılır, basım uyarısı verilir."""
    if toplanti is None:
        uyarilar.ekle(UYARI_TOPLANTI_YOK)
        return [(genel_kurul, BOS), (TOPLANTI, BOS), (KATILAN, BOS)]
    katilan = toplanti.attendances.filter(present=True).count()
    payda = BOS if asil_sayisi is None else str(asil_sayisi)
    yer = toplanti.place.strip() or BOS
    return [
        (genel_kurul, _gun(_secen_genel_kurul_gunu(donem, organ))),
        (TOPLANTI, f"{_an(toplanti.held_at)} · {yer}"),
        (KATILAN, f"{katilan}/{payda}"),
    ]


def _gorevli(asillar: Iterable[OrganMembership], role: str) -> OrganMembership | None:
    return next((uyelik for uyelik in asillar if uyelik.role == role), None)


def _sayac(kisi: OabPerson, organ: str) -> str:
    """Seçilme sayacı (program kayıtları + programdan önceki beyan); beyan bilinmiyorsa "………"."""
    sayi = uyelikler.secilme_sayaci(kisi, organ)
    return BOS if sayi is None else str(sayi)


def _yk_baskani(donem: OabTerm) -> OrganMembership | None:
    return _gorevli(
        selectors.gorevdeki_asillar(donem, OrganType.YONETIM_KURULU), MembershipRole.BASKAN
    )


def _temsilci_satirlari(
    satirlar: Iterable[temsilciler.TemsilciSatiri], uyarilar: _Uyarilar
) -> list[tuple[str, str]]:
    """E01'in temsilci tablosu: çizelgenin her satırı, temsilci başına bir satır (E03 ile aynı kişiler)."""
    tablo: list[tuple[str, str]] = []
    for satir in satirlar:
        if not satir.uyeler:
            tablo.append((satir.ad, BOS))
        for uyelik in satir.uyeler:
            koltuk = ASIL if uyelik.seat_type == SeatType.ASIL else YEDEK
            tablo.append((satir.ad, f"{_ad(uyelik.person, uyarilar)} ({koltuk})"))
    return tablo


# ---------------------------------------------------------------------------
# E01
# ---------------------------------------------------------------------------
def _yk_kadrosu(donem: OabTerm, gun: date) -> tuple[int | None, int | None]:
    """Kural paketinden asıl ve yedek üye sayısı (md. 12/1); olay gününde değer yoksa `None`."""
    try:
        return (
            int(kural("yonetim_kurulu.asil_uye", gun, donem)),
            int(kural("yonetim_kurulu.yedek_uye", gun, donem)),
        )
    except YururlukteDegerYok:
        return None, None


def _beyan(uyelik: OrganMembership) -> str:
    return BEYAN.format(
        suc=_gun(uyelik.eligibility_declared_on), tek=_gun(uyelik.single_birlik_declared_on)
    )


def e01_belgesi(donem: OabTerm) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E01'in içerik modeli ve basım uyarıları (modül başlığı)."""
    uyarilar = _Uyarilar()
    gun = _olay_gunu(donem)
    asil_sayisi, yedek_sayisi = _yk_kadrosu(donem, gun)
    organ = OrganType.YONETIM_KURULU
    asillar = selectors.gorevdeki_asillar(donem, organ)
    toplanti = _gorev_bolumu_toplantisi(donem, organ)
    karar = _gorev_bolumu_karari(toplanti)

    toplanti_satirlari = _toplanti_satirlari(
        donem, organ, toplanti, asil_sayisi, uyarilar, genel_kurul=GENEL_KURUL_SECIM_TARIHI
    )
    toplanti_satirlari.append((KARAR_DEFTERI, BOS if toplanti is None else _karar_defteri(karar)))

    gorev_satirlari: list[tuple[str, str, str, str, str]] = []
    imzalar: list[evrak.ImzaSahibi] = []

    def satir_ekle(etiket: str, uyelik: OrganMembership | None) -> None:
        if uyelik is None:
            gorev_satirlari.append((etiket, BOS, "", "", ""))
            imzalar.append(evrak.ImzaSahibi(BOS, etiket))
            return
        ad = _ad(uyelik.person, uyarilar)
        sayac = _sayac(uyelik.person, organ)
        gorev_satirlari.append((etiket, ad, sayac, _beyan(uyelik), ""))
        imzalar.append(evrak.ImzaSahibi(ad, etiket))

    # Satır ve imza sayısı kurulun koltuk sayısıdır (md. 12/1; E02'nin koltuk mantığı): boş görevin
    # "………" satırı yalnız boş bir koltuğu temsil eder. Koltuklar doluyken görev boşsa (görev bölümünden
    # önce, geçişte ya da görevlinin düşüp yedeğin çağrıldığı kurulda) uyarı verilir, asıl "Üye"
    # satırında imzalar; ayrı boş imza açılmaz. Kural paketinde değer yoksa kadro görevdekilerdir.
    bos_koltuk = max((len(asillar) if asil_sayisi is None else asil_sayisi) - len(asillar), 0)
    for role in GOREV_SIRASI:
        etiket = str(MembershipRole(role).label)
        gorevli = [u for u in asillar if u.role == role]
        if not gorevli:
            uyarilar.ekle(UYARI_GOREV_BOS.format(gorev=etiket))
            if bos_koltuk > 0:
                satir_ekle(etiket, None)
                bos_koltuk -= 1
        for uyelik in gorevli:
            satir_ekle(etiket, uyelik)
    uye_etiketi = str(MembershipRole.UYE.label)
    for uyelik in (u for u in asillar if u.role not in GOREV_SIRASI):
        satir_ekle(uye_etiketi, uyelik)
    if asil_sayisi is not None and len(asillar) < asil_sayisi:
        uyarilar.ekle(UYARI_KOLTUK_BOS)
    for _ in range(bos_koltuk):
        satir_ekle(uye_etiketi, None)

    yedek_satirlari: list[tuple[str, str, str]] = []
    yedekler = selectors.elected_roster(donem, organ)["yedek"]
    for uyelik in yedekler:
        sira = BOS if uyelik.seat_order is None else str(uyelik.seat_order)
        cagri = "" if uyelik.promoted_on is None else _gun(uyelik.promoted_on)
        yedek_satirlari.append((sira, _ad(uyelik.person, uyarilar), cagri))
    if yedek_sayisi is not None and len(yedekler) < yedek_sayisi:
        uyarilar.ekle(UYARI_KOLTUK_BOS)
        yedek_satirlari += [(BOS, BOS, "")] * (yedek_sayisi - len(yedekler))

    baskan = _gorevli(asillar, MembershipRole.BASKAN)
    muhasip = _gorevli(asillar, MembershipRole.MUHASIP)
    yardimci = _gorevli(asillar, MembershipRole.BASKAN_YARDIMCISI)
    imza_yetkisi = MUSTEREK_IMZA_DEGERI.format(
        baskan=_ad(baskan.person if baskan else None, uyarilar),
        muhasip=_ad(muhasip.person if muhasip else None, uyarilar),
        yardimci=_ad(yardimci.person if yardimci else None, uyarilar),
    )
    temsilci_satirlari = _temsilci_satirlari(
        temsilciler.temsilci_cizelgesi(donem, tarih=gun), uyarilar
    )
    imza_tarihi = "" if toplanti is None or toplanti.held_at is None else _an(toplanti.held_at)[:10]

    belge = evrak.Belge(
        kod=E01,
        antet=_antet(),
        bloklar=(
            evrak.Baslik(BELGE_ADLARI[E01], alt=evrak.TASLAK_IBARESI),
            evrak.Paragraf(E01_GIRIS),
            evrak.AltBaslik(E01_BOLUMLER[0]),
            evrak.Tablo(basliklar=KONU_BILGI, satirlar=tuple(toplanti_satirlari), oranlar=(2, 3)),
            evrak.AltBaslik(E01_BOLUMLER[1]),
            evrak.Tablo(
                basliklar=E01_GOREV_BASLIKLARI,
                satirlar=tuple(gorev_satirlari),
                oranlar=(3, 5, 2, 4, 3),
            ),
            evrak.Tablo(
                basliklar=E01_YEDEK_BASLIKLARI,
                satirlar=tuple(yedek_satirlari),
                oranlar=(2, 5, 3),
            ),
            evrak.AltBaslik(E01_BOLUMLER[2]),
            evrak.Tablo(
                basliklar=KONU_BILGI,
                satirlar=(
                    (BANKA_HESABI, BOS),
                    (MUSTEREK_IMZA, imza_yetkisi),
                    (BANKAYA_BILDIRIM, BOS),
                ),
                oranlar=(2, 3),
            ),
            evrak.AltBaslik(E01_BOLUMLER[3]),
            evrak.Tablo(
                basliklar=KONU_KARAR,
                satirlar=(
                    (AYLIK_TOPLANTI, donem.yk_meeting_day_rule.strip() or BOS),
                    (AYLIK_BILDIRIM, AYLIK_BILDIRIM_DEGERI),
                    (KOORDINASYON, KOORDINASYON_DEGERI),
                ),
                oranlar=(2, 3),
            ),
            evrak.Tablo(
                basliklar=TEMSILCI_BASLIKLARI,
                satirlar=tuple(temsilci_satirlari),
                oranlar=(3, 2),
            ),
            evrak.KonumCumlesi(evrak.KDT),
            *_imzalar(imzalar, imza_tarihi),
            evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
        ),
    )
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# E02
# ---------------------------------------------------------------------------
_KOLTUK_GRUPLARI: Final = (SeatGroup.VELI, SeatGroup.OGRETMEN)


def _dk_koltuklari(donem: OabTerm, gun: date) -> dict[str, dict[str, int]] | None:
    """Kural paketinden koltuk grupları (md. 14/1); olay gününde değer yoksa `None`."""
    try:
        deger: dict[str, dict[str, int]] = kural("denetleme_kurulu.koltuklar", gun, donem)
    except YururlukteDegerYok:
        return None
    return deger


def _grup_adi(uyelik: OrganMembership | None, grup: str) -> str:
    if grup == SeatGroup.OGRETMEN:
        return OGRETMEN_KOLTUGU
    if uyelik is None:
        return VELI_YA_DA_KURSIYER
    return KURSIYER_KOLTUGU if uyelik.person.kind == PersonKind.KURSIYER else VELI_KOLTUGU


def _kanal(uyelik: OrganMembership | None, grup: str) -> str:
    if uyelik is None:
        kanal = KANALLAR[
            ElectedBy.GENEL_KURUL if grup == SeatGroup.VELI else ElectedBy.OGRETMENLER_KURULU
        ]
    else:
        kanal = KANALLAR.get(str(uyelik.elected_by), str(uyelik.get_elected_by_display()))
    return f"{_grup_adi(uyelik, grup)} — {kanal}"


def e02_belgesi(donem: OabTerm) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E02'nin içerik modeli ve basım uyarıları (modül başlığı)."""
    uyarilar = _Uyarilar()
    gun = _olay_gunu(donem)
    organ = OrganType.DENETLEME_KURULU
    koltuklar = _dk_koltuklari(donem, gun)
    asil_sayisi = None if koltuklar is None else sum(koltuklar[g][SeatType.ASIL] for g in koltuklar)
    asillar = selectors.gorevdeki_asillar(donem, organ)
    yedekler = selectors.bekleyen_yedekler(donem, organ)
    toplanti = _gorev_bolumu_toplantisi(donem, organ)
    toplanti_satirlari = _toplanti_satirlari(
        donem, organ, toplanti, asil_sayisi, uyarilar, genel_kurul=GENEL_KURUL_TARIHI
    )

    baskan = _gorevli(asillar, MembershipRole.BASKAN)
    if baskan is None:
        uyarilar.ekle(UYARI_GOREV_BOS.format(gorev=str(MembershipRole.BASKAN.label)))

    uye_satirlari: list[tuple[str, str, str, str, str, str]] = []
    # Başkan seçilmemişse ayrı başkan bloğu yoktur: asıllar üye olarak imzalar (uyarı yukarıda).
    imza_baskan: list[evrak.ImzaSahibi] = []
    imza_uyeler: list[evrak.ImzaSahibi] = []
    for koltuk, kayitlar in ((SeatType.ASIL, asillar), (SeatType.YEDEK, yedekler)):
        for grup in _KOLTUK_GRUPLARI:
            gruptakiler = [u for u in kayitlar if u.seat_group == grup]
            for uyelik in gruptakiler:
                ad = _ad(uyelik.person, uyarilar)
                if koltuk == SeatType.YEDEK:
                    durum, gorev, baskanlik = YEDEK, "", ""
                else:
                    durum = (
                        ASIL
                        if uyelik.promoted_on is None
                        else YEDEKTEN_CAGRILDI.format(gun=_gun(uyelik.promoted_on))
                    )
                    gorev = str(MembershipRole(uyelik.role).label)
                    baskanlik = ""
                    if uyelik.role == MembershipRole.BASKAN:
                        baskanlik = _sayac(uyelik.person, organ)
                        imza_baskan = [evrak.ImzaSahibi(ad, UNVAN_DK_BASKANI)]
                    else:
                        imza_uyeler.append(evrak.ImzaSahibi(ad, gorev))
                uye_satirlari.append((_kanal(uyelik, grup), ad, durum, gorev, baskanlik, ""))
            beklenen = None if koltuklar is None else koltuklar[grup][koltuk]
            if beklenen is not None and len(gruptakiler) < beklenen:
                uyarilar.ekle(UYARI_KOLTUK_BOS)
                etiket = ASIL if koltuk == SeatType.ASIL else YEDEK
                for _ in range(beklenen - len(gruptakiler)):
                    uye_satirlari.append((_kanal(None, grup), BOS, etiket, "", "", ""))
                    if koltuk == SeatType.ASIL:
                        imza_uyeler.append(evrak.ImzaSahibi(BOS, str(MembershipRole.UYE.label)))

    plan = [date.fromisoformat(str(gun_)) for gun_ in donem.dk_audit_plan_dates or []]
    plan_satirlari = [
        (ARA_DENETIM.format(sira=sira), _gun(planlanan), ARA_RAPOR)
        for sira, planlanan in enumerate(sorted(plan), start=1)
    ]
    if not plan_satirlari:
        uyarilar.ekle(UYARI_PLAN_YOK)
        plan_satirlari.append((ARA_DENETIM.format(sira=1), BOS, ARA_RAPOR))
    plan_satirlari.append((NIHAI_RAPOR, BOS, NIHAI_RAPOR_DEGERI))

    yk_baskani = _yk_baskani(donem)
    if yk_baskani is None:
        uyarilar.ekle(UYARI_GOREV_BOS.format(gorev=UNVAN_BIRLIK_BASKANI))
    imza_tarihi = "" if toplanti is None or toplanti.held_at is None else _an(toplanti.held_at)[:10]
    belge = evrak.Belge(
        kod=E02,
        antet=_antet(),
        bloklar=(
            evrak.Baslik(BELGE_ADLARI[E02]),
            evrak.Paragraf(E02_GIRIS),
            evrak.AltBaslik(E02_BOLUMLER[0]),
            evrak.Tablo(basliklar=KONU_BILGI, satirlar=tuple(toplanti_satirlari), oranlar=(2, 3)),
            evrak.AltBaslik(E02_BOLUMLER[1]),
            evrak.Tablo(
                basliklar=E02_UYE_BASLIKLARI,
                satirlar=tuple(uye_satirlari),
                oranlar=(5, 5, 3, 2, 3, 3),
            ),
            evrak.AltBaslik(E02_BOLUMLER[2]),
            evrak.Tablo(
                basliklar=E02_PLAN_BASLIKLARI, satirlar=tuple(plan_satirlari), oranlar=(2, 2, 5)
            ),
            # Denetleme Kurulunun asıl üyeleri ve bilgi için birlik başkanı aynı imza satırında.
            *_imzalar(
                [
                    *imza_baskan,
                    *imza_uyeler,
                    evrak.ImzaSahibi(
                        _ad(yk_baskani.person if yk_baskani else None, uyarilar),
                        UNVAN_BILGI_BASKAN,
                    ),
                ],
                imza_tarihi,
            ),
            evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
        ),
    )
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# E03
# ---------------------------------------------------------------------------
def _karar_hucresi(uyelik: OrganMembership) -> str:
    """Yönetim kurulu kararı (sıra no ve tarih); kendiliğinden ve görevlendirme kanalı adıyla."""
    if uyelik.elected_by == ElectedBy.KENDILIGINDEN:
        return BASKAN_SIFATIYLA
    if uyelik.elected_by != ElectedBy.YK_KARARI:
        return KANALLAR.get(str(uyelik.elected_by), str(uyelik.get_elected_by_display()))
    karar = uyelik.representative_decision
    if karar is None:
        return BOS
    no = BOS if karar.decision_no is None else str(karar.decision_no)
    return KARAR_NO_TARIH.format(no=no, tarih=_gun(karar.decision_date))


def _mudur_kaydi(kart_adi: str) -> OabPerson | None:
    """Okul kartındaki adla eşleşen tek okul müdürü kişi kaydı (`is_principal`; ad ve soyad ayrı
    alanlarda). Etkin olmalı, adı okunabilmeli ve `name_key`'i kartın adınınkiyle aynı olmalı: işaret
    yanlış kişide kalmışsa kartla çelişen ad basılmaz. Birden çok eşleşme ya da hiç eşleşme yoksa `None`."""
    anahtar = name_match.name_key(kart_adi)
    eslesenler = [
        kisi
        for kisi in OabPerson.objects.filter(is_principal=True, status=PersonStatus.AKTIF)
        if not is_corrupt(kisi.first_name)
        and not is_corrupt(kisi.last_name)
        and name_match.name_key(f"{kisi.first_name} {kisi.last_name}") == anahtar
    ]
    return eslesenler[0] if len(eslesenler) == 1 else None


def _mudur_adi(uyarilar: _Uyarilar) -> str:
    """Okul müdürünün adı "Ad SOYAD" (RYUE md. 17/2). Önce okul müdürü kişi kaydının ayrık ad ve soyad
    alanlarından (`_mudur_kaydi`); kayıt yoksa okul kartının tek alanından, son sözcük soyadı sayılarak.
    Üç ya da daha çok sözcüklü adda bu bölme tahmindir: basım uyarısı verilir."""
    ad = " ".join(str(SchoolConfig.load().principal_name or "").split())
    if not ad:
        uyarilar.ekle(UYARI_MUDUR_ADI_YOK)
        return BOS
    kayit = _mudur_kaydi(ad)
    if kayit is not None:
        return _ad(kayit, uyarilar)
    adlar, _, soyad = ad.rpartition(" ")
    if len(ad.split()) >= 3:
        uyarilar.ekle(UYARI_MUDUR_SOYADI)
    return evrak.ad_soyad(adlar, soyad) if adlar else evrak.ad_soyad(soyad, "")


def e03_belgesi(donem: OabTerm) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E03'ün içerik modeli ve basım uyarıları (modül başlığı); satırlar yalnız çizelgedendir."""
    uyarilar = _Uyarilar()
    gun = _olay_gunu(donem)
    cizelge = temsilciler.temsilci_cizelgesi(donem, tarih=gun)
    satirlar: list[tuple[str, str, str, str, str]] = []
    for sira, satir in enumerate(cizelge, start=1):
        if not satir.uyeler:
            satirlar.append((str(sira), satir.ad, BOS, "", BOS))
        for ilk, uyelik in enumerate(satir.uyeler):
            koltuk = ASIL if uyelik.seat_type == SeatType.ASIL else YEDEK
            satirlar.append(
                (
                    str(sira) if ilk == 0 else "",
                    satir.ad if ilk == 0 else "",
                    _ad(uyelik.person, uyarilar),
                    koltuk,
                    _karar_hucresi(uyelik),
                )
            )
    notlar = [
        evrak.Paragraf(RPD_NOTU)
        for satir in cizelge
        if satir.representation == Representation.RPD_YURUTME_KOMISYONU and satir.notlar
    ]
    asillar = selectors.gorevdeki_asillar(donem, OrganType.YONETIM_KURULU)
    sekreter = _gorevli(asillar, MembershipRole.SEKRETER)
    baskan = _gorevli(asillar, MembershipRole.BASKAN)
    for gorevli, etiket in ((sekreter, MembershipRole.SEKRETER), (baskan, MembershipRole.BASKAN)):
        if gorevli is None:
            uyarilar.ekle(UYARI_GOREV_BOS.format(gorev=str(MembershipRole(etiket).label)))
    belge = evrak.Belge(
        kod=E03,
        antet=_antet(),
        bloklar=(
            evrak.Baslik(BELGE_ADLARI[E03], alt=evrak.TASLAK_IBARESI),
            evrak.AltBaslik(E03_BOLUMLER[0]),
            evrak.Tablo(
                basliklar=E03_BASLIKLARI, satirlar=tuple(satirlar), oranlar=(2, 6, 5, 3, 4)
            ),
            *notlar,
            evrak.KonumCumlesi(evrak.KDT),
            # Sekreter, Birlik Başkanı ve teslim alan Okul Müdürü aynı imza satırında (genel setin
            # düzeni; müdür bloğu tasarım §9.3 "Teslim alan").
            evrak.Imza(
                sahipler=(
                    evrak.ImzaSahibi(
                        _ad(sekreter.person if sekreter else None, uyarilar), UNVAN_SEKRETER
                    ),
                    evrak.ImzaSahibi(
                        _ad(baskan.person if baskan else None, uyarilar), UNVAN_BIRLIK_BASKANI
                    ),
                    evrak.ImzaSahibi(_mudur_adi(uyarilar), UNVAN_TESLIM_ALAN),
                ),
            ),
            evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
        ),
    )
    return belge, tuple(uyarilar.liste)


#: Kodun içerik kurucusu.
KURUCULAR: Final[dict[str, Callable[[OabTerm], tuple[evrak.Belge, tuple[str, ...]]]]] = {
    E01: e01_belgesi,
    E02: e02_belgesi,
    E03: e03_belgesi,
}


# ---------------------------------------------------------------------------
# Üretim, liste ve basım
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Uretim:
    """Üretimin sonucu: evrak kaydı ve basım uyarıları (belgeye basılmaz)."""

    kayit: GeneratedDocument
    uyarilar: tuple[str, ...]


def dosya_adi(kod: str, gun: date, bicim: str) -> str:
    """Kaydedilen dosyanın adı: belge + tarih (sözlük §3): 'Temsilci-Görevlendirme-Çizelgesi_
    11.11.2026.pdf'. Kişi adı ve dönem adı taşımaz."""
    return f"{DOSYA_ADI_KOKLERI[kod]}_{gun:%d.%m.%Y}.{UZANTILAR[bicim]}"


def _uretim_yetkisi(kod: str) -> None:
    """Üreten rol (modül başlığı "Üretim"). E02 Denetleme Kurulunun görev bölümü eylemidir; kayıt
    verilmez: kapanmış dönemin kuralı evrak kaydının dönem kilidindedir (O2 beyaz listesi)."""
    if kod == E02:
        rol_izinleri.yetki_oturum(rol_izinleri.Eylem.DK_GOREV_BOLUMU_YAZMA)
        return
    kim = yazar()
    if kim is None or kim.sistem_mi or kim.rol not in URETEN_ROLLER[kod]:
        raise RolYetkisiz


def uret(kod: str, term: OabTerm) -> Uretim:
    """Evrakı üretir ve kaydeder (modül başlığı "Üretim"); yeni sürümün kaydını döner."""
    if kod not in KURUCULAR:
        raise ValueError(KOD_GECERSIZ)
    yazma_kapisi()
    app_password.require_password_set()
    _uretim_yetkisi(kod)
    donem = OabTerm.objects.select_related("rule_package").get(pk=term.pk)
    belge, uyarilar = KURUCULAR[kod](donem)
    cizimler = {
        DocumentFormat.PDF: evrak.pdf_ciz(belge),
        DocumentFormat.DOCX: evrak.docx_ciz(belge),
    }
    gun = timezone.localdate()
    with transaction.atomic():
        kayit = evrak_servisi.kaydet(belge, konu=donem, bicimler=BICIMLER, donem=donem)
        for bicim in BICIMLER:
            evrak_servisi.dosya_ekle(
                kayit, cizimler[bicim], bicim=bicim, dosya_adi=dosya_adi(kod, gun, bicim)
            )
    return Uretim(kayit=kayit, uyarilar=uyarilar)


def evrak_listesi(donem: OabTerm) -> list[GeneratedDocument]:
    """Dönemin geçerli E01, E02 ve E03 kayıtları (kod sırasıyla)."""
    return list(
        GeneratedDocument.objects.filter(
            term=donem, doc_type__in=KODLAR, status=DocumentStatus.GECERLI
        ).order_by("doc_type", "-version")
    )


def _okuma_yetkisi(kod: str) -> None:
    """Basan rol belgenin satırını okuyabilmeli (tasarım §4.4.2 "Okuma"); yoksa 403."""
    kim = yazar()
    if (
        kim is None
        or kim.sistem_mi
        or kim.rol not in rol_izinleri.okuyabilen_roller(OKUMA_SATIRLARI[kod])
    ):
        raise RolYetkisiz


def bas(kayit: GeneratedDocument, bicim: str) -> FileResponse:
    """Kaydın dosyasını verir ve `BASIM` satırını yazar (modül başlığı "Basım").

    Kod bu üç belgeden biri değilse, biçim kayıtta yoksa ya da dosya eklenmemişse 404. Dosya
    okunamazsa (`dosya_deposu` hataları) bayt verilmez, iz yazılmaz.
    """
    if kayit.doc_type not in KODLAR or bicim not in kayit.formats:
        raise Http404
    _okuma_yetkisi(str(kayit.doc_type))
    ek = kayit.ekler().filter(mime=evrak_servisi.BICIM_TURLERI[bicim]).last()
    if ek is None:
        raise Http404
    yanit = dosya_deposu.indirme_yaniti(
        ek,
        dosya_adi=dosya_adi(str(kayit.doc_type), timezone.localdate(kayit.generated_at), bicim),
    )
    with transaction.atomic():
        denetim_izi.basim(
            model=str(kayit.subject_type),
            object_id=str(kayit.subject_id),
            kod=str(kayit.doc_type),
            sha256=str(ek.sha256),
        )
    return yanit


def bicim_coz(metin: str) -> str:
    """Yoldaki biçim ('pdf', 'docx') → kaydın biçimi; tanınmazsa 404."""
    for bicim, uzanti in UZANTILAR.items():
        if metin == uzanti:
            return bicim
    raise Http404
