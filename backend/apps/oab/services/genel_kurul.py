"""Genel kurulun durum makinesi ve hazırlık dönemi (tasarım §5.2.3, §7.1; plan F2 §1.1-1…5, §5.2,
§7 U1-U12, U19, U24; F2 4. adım).

F1c genel kurulun asgari kaydını (dönem bağı, yeter sayının anlık görüntüsü) kurdu; F2 3. adım tasarımın
alanlarını ve model düzeyindeki durum makinesini (`models.genel_kurul`) getirdi. Bu modül geçişlerin
servisidir: planlama, çağrı, ilan, birinci toplantı, yeter sayı yok, ikinci toplantının ilanı ve kendisi,
iptal. Gündem değişikliği, divan, karar ve katılım düzeltmesi 5. adımda; seçim, ibra, tutanak ve dönemin
açılması 6. adımda; müdürün ve Denetleme Kurulunun yazıları (yeni okul daveti, müdürün olağanüstü
çağrısı, md. 14/5 çağrısı) ve gelen-giden evrak bağı 7. adımdadır. Uç ve ekran 11. adımdadır.

KİM (tasarım §4.4.2 M3 ve §7.1 "Kim" sütunu; Kim matrisi daraltır, genişletemez). Her yazma önce
`Eylem.GENEL_KURUL_YAZMA` kapısından geçer (program yöneticisi ve yönetim kurulu rolleri; müdür ve
Denetleme Kurulu okur), sonra geçişin "Kim"iyle daraltılır: planlama, tarih değişikliği, ilan ve
toplantılar program yöneticisi ve sekreter; yönetim kurulunun çağrısı sekreter (YK kararı); başkanın md.
13/8 çağrısı başkan; üyelerin yazılı başvurusunu program yöneticisi kaydeder; iptal yalnız program
yöneticisi. Müdürün (md. 9/1 yeni okul, 9/6, 13/8, 25/2) ve Denetleme Kurulunun (md. 14/5) çağrısının
kendi eylemleri 7. adımda bağlanır; o güne dek bu çağıranlar hiçbir rolle kaydedilmez (`RolYetkisiz`).

KURALLAR (altın kural 1-3). Değerler kural paketindedir; kurallar kapanacak dönemin kopyasından, yeni
okulun ilk genel kurulunda hazırlık döneminin kopyasından okunur (U1). Kopya genel kurul kurallarını
taşımıyorsa (`r1`'e bağlı açık dönem) planlama yapılmaz: önce kural sürümü güncellemesi (hesap
bütünlüğü; `KuralSurumuGuncellenmeli`). Bütün genel kurul kurallarının olay günü birinci toplantının
yerel günüdür (Europe/Istanbul; U7: yeter sayı da o günün kuralıyla dondurulur). Süre ve oran sapmaları
uyarı + gerekçedir (`uyum.denetle`); girilmemiş bilgi eksiktir, gerekçe istemez. Sert olanlar yalnız
hesap bütünlüğüdür: yeter sayı ilanda okul kartındaki mevcuttan hesaplanır ve dondurulur, birinci
toplantının sonucu (yapıldı ya da yeter sayı yok) katılım sayısından programca hesaplanır, türe göre
dağılımın toplamı katılım sayısını tutar.

HAZIRLIK DÖNEMİ (U2-U5; tasarım §5.2.1, §7.8). Olağan genel kurul planlanınca yeni birlik dönemi
`HAZIRLIK` açılır, programla gelen en yeni revizyona bağlanır (`kural_bagi.acilis_bagi`) ve aynı işlemde
`opened_by_assembly` yazılır (dönem açılır, genel kurul yazılır, dönem güncellenir; bağ sonradan
yazılsaydı hazırlık dönemi geçiş dönemi sanılırdı). Ders yılı birinci toplantı gününü içeren ders
yılıdır; tanımlı değilse planlama yapılmaz (Ayarlar → Ders Yılları). Olağanüstü genel kurul dönem açmaz
(md. 13/8). Genel kurul iptal edilirse hazırlık dönemi de iptal olur. Hiç birlik dönemi olmayan okulda
olağan genel kurul yeni açılan okulun ilk genel kuruludur (kullanıcı kararı S5): okul kartında açılış
tarihi girilmiş olmalıdır, kapanacak dönem yoktur (`term` boş), çağıran okul müdürüdür (md. 9/1; çağrısı
7. adımda).

GÜNDEM TOHUMU (U19, U24). Olağan genel kurulun gündemi planlamayla aynı işlemde OYS'nin standart
şablonundan (`create_default_agenda` AYNEN) yazılır; md. 11/1-e (yetkilendirme) ve 11/1-f (öneriler)
maddeleriyle tazelenir. "Saygı duruşu ve İstiklal Marşı" teamüldür: `DIGER` türüyle durur, kural
denetimine girmez. Olağanüstü genel kurulda tohum yoktur; gündem çağrı nedeninden çağrıda girilir
(md. 9/6, U30).

ÇAĞRI. Olağanda çağıran yönetim kuruludur (yeni okulda okul müdürü); yönetim kurulu kararının bağı F3'e
dek atıfsız akış satırıdır, uyarı + gerekçe (kullanıcı kararı S1; `KARARSIZ_CAGRI_AKISI`). Olağanüstüde
çağıran ve çağrı nedeni zorunludur, çağıran `genel_kurul.olaganustu_cagiranlar` ile denetlenir; üyelerin
yazılı başvurusunda oran başvuran sayısı / elle girilen üye sayısıdır (U12;
`genel_kurul.olaganustu_basvuru_oran`), biri girilmemişse eksiktir. Başvuru yazısının gelen evrak bağı
(`call_document`) 7. adımdadır; o güne dek boştur ve eksik sayılır (gerekçe istemez, satır açılmaz).

İLAN (U7-U10). Her ilan bir `Announcement` kaydıdır; üç kanalın kanıt günleri ayrı alanlardır. 15 gün
her kanal için ayrıdır, bağlayıcı olan en geç kanalın günüdür (U9); kanalı eksik ilan
`genel_kurul.ilan_kanallari`'nda eksiktir (tamamlanacaklar). İlanın kuralları ilan kaydına (konu
`Announcement`) yazılır: ikinci toplantının ayrı ilanı birincinin satırını ezmez. Yeter sayı bu geçişte
dondurulur (`yeter_sayiyi_dondur`). İkinci toplantı birinci toplantının gününden en geç 30 gün sonra
olur; olağanüstüde de (kullanıcı kararı A-1; ileti atfı U10).

TOPLANTILAR. Birinci toplantıda katılım dondurulmuş yeter sayıdan azsa durum `YETER_SAYI_YOK`, değilse
`YAPILDI`'dır; kullanıcı seçmez. İkinci toplantıda çoğunluk aranmaz (md. 9/2; olağanüstüde de, A-1).
Gözlemci öğrenci (md. 9/5) ayrı alandır, katılım sayısına eklenmez. Açılışı okul müdürü yapar (md.
10/1-b): bilgi satırıdır.

Her yazma denetim izine düşer (izli servis kalıbı: `denetim_izi.degisiklik`). Kayıt silinmez: genel
kurul `IPTAL` olur (altın kural 4).
"""

from __future__ import annotations

import calendar
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Final

from django.db import transaction
from django.utils import timezone

from apps.oab.hatalar import KuralSurumuGuncellenmeli, YeterSayiDonduruldu
from apps.oab.kurallar import (
    VERI_YOK,
    BilinmeyenKural,
    YururlukteDegerYok,
    genel_kurul,
    kural_kaydi,
    yazma_kapisi,
)
from apps.oab.kurallar.erisim import DenetimSonucu
from apps.oab.models import (
    AgendaItem,
    AgendaItemKind,
    Announcement,
    AnnouncementKind,
    AnnouncementStatus,
    AssemblyCaller,
    AssemblyKind,
    AssemblyMeeting,
    AssemblyStatus,
    AttendanceKind,
    GeneralAssembly,
    OabTerm,
    TermStatus,
)
from apps.oab.models.genel_kurul import BASLIK_MAX, YER_MAX
from apps.oab.services import donem_kilidi, gecis, iz, kural_bagi, uyum
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AccountRole, ParentRoster, SchoolConfig
from apps.okul.oturum import yazar
from apps.okul.services import app_password
from shared.exceptions import RolYetkisiz

# ---------------------------------------------------------------------------
# İletiler (kullanıcıya görünür; sözlük §1)
# ---------------------------------------------------------------------------
OGRENCI_MEVCUDU_BOS = "Okul kartında öğrenci mevcudu girilmemiş; yeter sayı hesaplanamadı."
DONEMSIZ_GENEL_KURUL = "Genel kurulun birlik dönemi yok; yeter sayı hesaplanamadı."
IPTAL_KURULDA_DONDURULMAZ = "İptal edilmiş genel kurulun yeter sayısı dondurulmaz."
TUR_GECERSIZ = "Genel kurulun türü olağan ya da olağanüstü olmalıdır."
BIRINCI_TOPLANTI_GEREKLI = "Birinci toplantının günü ve saati girilmelidir."
YER_UZUN = f"Toplantı yeri en çok {YER_MAX} karakter olabilir."
ACIK_DONEM_YOK = "Açık birlik dönemi yok; genel kurul açık birlik döneminde planlanır."
OLAGANUSTU_ACIK_DONEMDE = (
    "Olağanüstü genel kurul açık birlik döneminde planlanır; bu okulda açık birlik dönemi yok."
)
YENI_OKUL_ACILIS_TARIHI_YOK = (
    "Birlik dönemi yok. Okul daha önce birlik dönemi açtıysa önce geçiş kurulumunda ilk dönemi açın; "
    "yeni açılan okulsa okul kartına okulun açılış tarihini girin (md. 9/1)."
)
HAZIRLIK_DONEMI_VAR = (
    "Hazırlıkta bir birlik dönemi var; aynı anda tek olağan genel kurul hazırlanır. Önceki genel "
    "kurul tamamlanmalı ya da iptal edilmelidir."
)
DERS_YILI_YOK = (
    "Birinci toplantı gününü kapsayan ders yılı tanımlı değil; Ayarlar → Ders Yılları'ndan o ders "
    "yılını ekleyip yeniden deneyin."
)
DURUM_GECERSIZ = "Genel kurul bu durumdayken bu işlem yapılmaz."
TARIH_DEGISMEZ = "Toplantı tarihi yalnız ilandan önce değiştirilir."
OLAGAN_CAGIRAN = "Olağan genel kurulu yönetim kurulu çağırır; yeni açılan okulda okul müdürü davet eder (md. 9/1)."
OLAGAN_CAGRI_ALANLARI = (
    "Olağan genel kurulun çağrısında çağrı nedeni, gündem ve başvuru sayıları girilmez; gündem "
    "planlamada yazılan tohum gündemdir."
)
CAGIRAN_GEREKLI = "Olağanüstü genel kurulu çağıran seçilmelidir (md. 9/6)."
CAGIRAN_GECERSIZ = "Çağıran tanımlı çağıranlardan biri olmalıdır."
CAGRI_NEDENI_GEREKLI = "Olağanüstü genel kurulun çağrı nedeni yazılmalıdır (md. 9/6)."
GUNDEM_GEREKLI = (
    "Olağanüstü genel kurulun gündemi çağrıda girilir; en az bir gündem maddesi yazılmalıdır "
    "(md. 9/6)."
)
GUNDEM_TURU_GECERSIZ = "Gündem maddesinin türü tanımlı türlerden biri olmalıdır."
GUNDEM_BASLIGI_GEREKLI = "Gündem maddesinin başlığı yazılmalıdır."
GUNDEM_BASLIGI_UZUN = f"Gündem maddesinin başlığı en çok {BASLIK_MAX} karakter olabilir."
BASVURU_SAYILARI_YALNIZ_UYELERDE = (
    "Başvuran ve üye sayısı yalnız üyelerin yazılı başvurusuyla yapılan çağrıda girilir."
)
SAYI_GECERSIZ = "Sayılar sıfır ya da pozitif tam sayı olmalıdır."
UYE_SAYISI_SIFIR = "Birlik üye sayısı sıfırdan büyük olmalıdır."
BASVURAN_UYEDEN_COK = "Başvuran üye sayısı birlik üye sayısından büyük olamaz."
IKINCI_TOPLANTI_SIRASI = "İkinci toplantı birinci toplantıdan sonra olmalıdır."
IKINCI_TOPLANTI_TARIHI_YOK = (
    "İkinci toplantının tarihi ilan edilmedi; önce ikinci toplantının ilanını kaydedin."
)
IKINCI_ILAN_VAR = "Bu genel kurulun ikinci toplantısı ayrıca ilan edildi."
DUYURU_GENEL_KURULUN_DEGIL = "Bu duyuru bir genel kurulun ilanı değildir."
DAGILIM_GECERSIZ = "Katılımın türe göre dağılımı yalnız tanımlı türlerin sayılarıdır."
DAGILIM_TOPLAMI = (
    "Katılımın türe göre dağılımının toplamı katılan üye sayısını tutmalıdır (hesap bütünlüğü)."
)
IPTAL_GEREKCESI_GEREKLI = "İptal gerekçesi yazılmalıdır."
HAZIRLIK_DONEMI_IPTAL_NEDENI = "Dönemi açan genel kurul iptal edildi."

#: Olağan genel kurulun yönetim kurulu kararı bağı yokluğunun akış satırı (kullanıcı kararı S1;
#: Yönetmelik maddesi değildir, atıf basılmaz; F1c'nin yedek çağrısı emsali).
KARARSIZ_CAGRI_AKISI: Final = "akis.genel_kurul_cagri_karar_bagi"
KARARSIZ_CAGRI: Final = (
    "Genel kurul çağrısı bir yönetim kurulu kararına bağlanmadı; karar defterindeki kararın bilgisi "
    "sonra eklenir (program uyarısıdır, Yönetmelik hükmü değildir)."
)
#: Olağanüstü genel kurulda ikinci toplantı kurallarının iletisine eklenen atıf (U10).
A1_ATFI: Final = (
    "Olağanüstü genel kurulda da uygulanır: kullanıcı kararı A-1 (md. 9/2'nin olağanüstüde "
    "uygulanması)."
)

#: Bilgi satırları ([B]; gerekçe istemez, saklanmaz).
MUDUR_ACILIS_BILGISI: Final = "Toplantının açılışını okul müdürü yapar (md. 10/1-b)."
OLAGANUSTU_DONEM_ACMAZ_BILGISI: Final = (
    "Olağanüstü genel kurul yeni birlik dönemi açmaz (md. 13/8)."
)
GUNDEME_BAGLILIK_BILGISI: Final = (
    "Olağanüstü genel kurulda gündeme bağlılık ilkesi geçerlidir (md. 9/6)."
)
BASVURU_YAZISI_BILGISI: Final = (
    "Üyelerin yazılı başvurusu gelen evrak kaydına bağlanmadı; bağ eksik sayılır, gerekçe istemez."
)
VELI_LISTESI_ONERISI: Final = (
    "Veli listesi aktarılmadı. Elden yazılı davetin sınıf başına adedi ve katılım cetveli için okulun "
    "şablonuyla aktarılabilir (isteğe bağlı)."
)

# ---------------------------------------------------------------------------
# Roller (modül başlığı "Kim")
# ---------------------------------------------------------------------------
_YONETICI: Final = rol_izinleri.YONETICI
_SEKRETER: Final = AccountRole.SEKRETER.value
_BASKAN: Final = AccountRole.BASKAN.value
#: Tasarım §7.1 `PLANLANDI` (oluşturma) "Kim": program yöneticisi, sekreter.
PLANLAYAN_ROLLER: Final = frozenset({_YONETICI, _SEKRETER})
#: §7.1 ilan, birinci toplantı, yeter sayı yok, ikinci toplantı "Kim": program yöneticisi, sekreter.
ILAN_VE_TOPLANTI_ROLLERI: Final = frozenset({_YONETICI, _SEKRETER})
#: §7.1 `… → IPTAL` "Kim": program yöneticisi.
IPTAL_EDEN_ROLLER: Final = frozenset({_YONETICI})
#: §7.1 çağrı "Kim"i, çağırana göre. Müdürün ve Denetleme Kurulunun çağrısı bu tabloda yoktur (7. adım).
CAGIRAN_ROLLERI: Final[Mapping[str, frozenset[str]]] = {
    AssemblyCaller.YONETIM_KURULU: frozenset({_SEKRETER}),
    AssemblyCaller.BASKAN_VEYA_MUDUR_13_8: frozenset({_BASKAN}),
    AssemblyCaller.UYE_BASVURUSU: frozenset({_YONETICI}),
}

# ---------------------------------------------------------------------------
# Kurallar, gündem tohumu, ilan kanalları
# ---------------------------------------------------------------------------
#: Genel kurul akışının okuduğu kurallar (U1: kapanacak dönemin kopyası bunları taşımalıdır).
GENEL_KURUL_KURALLARI: Final = (
    "genel_kurul.olagan_son_ay",
    "genel_kurul.yeni_okul_ay",
    "genel_kurul.ilan_en_az_gun",
    "genel_kurul.ilan_kanallari",
    "genel_kurul.ikinci_toplanti_en_gec_gun",
    "genel_kurul.ikinci_toplanti_cogunluk_aranmaz",
    "genel_kurul.olaganustu_cagiranlar",
    "genel_kurul.olaganustu_basvuru_oran",
)

#: Olağan genel kurulun tohum gündemi (U19: OYS `STANDARD_AGENDA_TEMPLATE` AYNEN, md. 11/1-e ve f ile
#: tazelenmiş; U24: saygı duruşu `DIGER`). Başlıklar sözlüğün yazımıyladır ("yönetim kurulu",
#: "Denetleme Kurulu").
TOHUM_GUNDEM: Final[tuple[tuple[str, str], ...]] = (
    (AgendaItemKind.ACILIS, "Açılış ve yoklama"),
    (AgendaItemKind.DIVAN_SECIMI, "Divan başkanı ve kâtip seçimi"),
    (AgendaItemKind.DIGER, "Saygı duruşu ve İstiklal Marşı"),
    (AgendaItemKind.YK_FAALIYET_RAPORU, "Yönetim kurulu faaliyet raporunun okunması"),
    (AgendaItemKind.DK_RAPORU, "Denetleme Kurulu raporunun okunması"),
    (AgendaItemKind.IBRA, "Yönetim kurulu ve Denetleme Kurulunun ibrası"),
    (AgendaItemKind.SECIM_YK, "Yönetim kurulu asıl ve yedek üye seçimi"),
    (AgendaItemKind.SECIM_DK, "Denetleme Kurulu asıl ve yedek üye seçimi (veli koltuğu)"),
    (AgendaItemKind.TAHMINI_BUTCE, "Tahmini bütçenin görüşülmesi"),
    (
        AgendaItemKind.YETKILENDIRME,
        "İhtiyaçların giderilmesi için yönetim kurulunun yetkilendirilmesi",
    ),
    (
        AgendaItemKind.ONERILER,
        "Eğitim ve öğretimde kalite ve başarının yükseltilmesine ilişkin öneriler",
    ),
    (AgendaItemKind.DILEK, "Dilek ve temenniler"),
    (AgendaItemKind.KAPANIS, "Kapanış"),
)

#: `genel_kurul.ilan_kanallari` belirteçleri (kural paketinin değerleri; md. 9/3).
KANAL_ELDEN_YAZILI: Final = "ELDEN_YAZILI"
KANAL_ILAN_PANOSU: Final = "ILAN_PANOSU"
KANAL_INTERNET_SAYFASI: Final = "INTERNET_SAYFASI"
#: İlan kaydının kanıt alanı tuttuğu kanallar (`Announcement`'ın üç alanı).
TUM_KANALLAR: Final = (KANAL_ELDEN_YAZILI, KANAL_ILAN_PANOSU, KANAL_INTERNET_SAYFASI)

#: Takvim yılındaki ay sayısı (takvim aritmetiği; kural değeri değildir).
_YILIN_AYLARI: Final = 12
#: Uyarı özetine giren denetim sonuçları (O3 `rule_warnings`).
_OZETLENEN: Final = frozenset({"eksik", "uyari"})
#: İptal edilebilen durumlar (tasarım §7.1 `… → IPTAL`).
_IPTAL_EDILEBILIR: Final = frozenset(
    {
        AssemblyStatus.PLANLANDI,
        AssemblyStatus.CAGRILDI,
        AssemblyStatus.ILAN_EDILDI,
        AssemblyStatus.YETER_SAYI_YOK,
    }
)
#: İlan kanıtı yazılabilen durumlar (tutanak tamamlanana dek; tamamlanınca eksik sapmaya döner, 6. adım).
_KANIT_YAZILABILIR: Final = frozenset(
    {AssemblyStatus.ILAN_EDILDI, AssemblyStatus.YETER_SAYI_YOK, AssemblyStatus.YAPILDI}
)


# ---------------------------------------------------------------------------
# Girdi ve sonuç türleri
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GundemMaddesi:
    """Çağrıda girilen gündem maddesi (olağanüstü genel kurul; md. 9/6)."""

    title: str
    kind: str = AgendaItemKind.DIGER


@dataclass(frozen=True)
class IlanKanallari:
    """Üç kanalın kanıt günleri (md. 9/3); girilmeyen kanal `None`'dur (eksik)."""

    distributed_written_on: date | None = None
    posted_board_on: date | None = None
    published_web_on: date | None = None

    def girilenler(self) -> list[str]:
        """Kanıt günü girilmiş kanalların belirteçleri (`genel_kurul.ilan_kanallari`)."""
        gunler = (self.distributed_written_on, self.posted_board_on, self.published_web_on)
        return [kanal for kanal, gun in zip(TUM_KANALLAR, gunler, strict=True) if gun is not None]

    def en_gec(self) -> date | None:
        """Bağlayıcı ilan günü: girilmiş kanalların en geç günü (U9); hiçbiri girilmediyse `None`."""
        gunler = [
            g
            for g in (self.distributed_written_on, self.posted_board_on, self.published_web_on)
            if g is not None
        ]
        return max(gunler) if gunler else None


@dataclass(frozen=True)
class Katilim:
    """Bir toplantının sayıları: katılan üye (kişi başı), türe göre dağılım, velisi katılan öğrenci
    sayısı (U16) ve gözlemci öğrenci (md. 9/5; katılım sayısına girmez)."""

    attendee_count: int
    attendance_by_kind: Mapping[str, int] = field(default_factory=dict)
    parent_students_count: int | None = None
    observer_count: int | None = None


@dataclass(frozen=True)
class GenelKurulSonucu:
    """Geçişin sonucu: güncel kayıt, bu geçişte çıkan eksik ve uyarılar (atıflı) ve bilgi satırları."""

    kurul: GeneralAssembly
    uyarilar: tuple[dict[str, Any], ...] = ()
    bilgiler: tuple[str, ...] = ()


def _ozet_satiri(kural_id: str, sonuc: DenetimSonucu) -> dict[str, Any] | None:
    if sonuc["durum"] not in _OZETLENEN:
        return None
    return {
        "kural": kural_id,
        "atif": sonuc["atif"],
        "mesaj": sonuc["mesaj"],
        "durum": sonuc["durum"],
        "paket": sonuc["paket"],
        "rev": sonuc["rev"],
    }


class _Tur:
    """Bir geçişin denetim turu: ortak denetim değişkenleri, kurulun özet satırları, dönen uyarılar."""

    def __init__(self, kurul: GeneralAssembly, gerekce: uyum.Gerekce | None) -> None:
        self.kurul = kurul
        self.donem = kural_donemi(kurul)
        self.gun = birinci_toplanti_gunu(kurul)
        self.gerekce = gerekce
        #: Kurulun kendi kurallarının özet satırları; `None` uygun (eski satırı düşürür).
        self.ozet_satirlari: dict[str, dict[str, Any] | None] = {}
        self.uyarilar: list[dict[str, Any]] = []

    def ortak(self) -> dict[str, Any]:
        """`uyum.denetle`'nin ortak değişkenleri: dönem, olay günü, gerekçe, hazırlık yazımı."""
        return {
            "donem": self.donem,
            "tarih": self.gun,
            "gerekce": self.gerekce,
            "hazirlik_yazimi": True,
        }

    def kaydet(self, kural_id: str, sonuc: uyum.UyumSonucu, *, kurulun: bool = True) -> None:
        """Sonucu dönen uyarılara, konusu kurulsa kurulun özetine işler."""
        satir = _ozet_satiri(kural_id, sonuc.sonuc)
        if kurulun:
            self.ozet_satirlari[kural_id] = satir
        if satir is not None:
            self.uyarilar.append(satir)

    def akis(self, akis_id: str, mesaj: str) -> None:
        """Atıfsız akış satırı (gerekçesi alınmış uyarı) kurulun özetine ve dönen uyarılara girer."""
        satir: dict[str, Any] = {
            "kural": akis_id,
            "atif": "",
            "mesaj": mesaj,
            "durum": "uyari",
            "paket": "",
            "rev": None,
        }
        self.ozet_satirlari[akis_id] = satir
        self.uyarilar.append(satir)

    def ozet(self) -> list[dict[str, Any]]:
        """Kurulun yeni uyarı özeti: bu turda denetlenen kuralların eski satırları atılır."""
        kalan = [
            satir
            for satir in (self.kurul.rule_warnings or [])
            if satir.get("kural") not in self.ozet_satirlari
        ]
        return [*kalan, *(s for s in self.ozet_satirlari.values() if s is not None)]


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
def _kapi() -> None:
    """Genel kurul yazma kapısı (M3, dipnot ¹: müdür genel kurulun öteki işlerinde okur)."""
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.GENEL_KURUL_YAZMA)


def _daralt(roller: frozenset[str]) -> None:
    """Geçişin "Kim"i (tasarım §7.1): kapıdan geçen rol bu geçişi yapan roller arasında olmalıdır."""
    kim = yazar()
    if kim is None or kim.sistem_mi or kim.rol not in roller:
        raise RolYetkisiz


def _baslangic(roller: frozenset[str]) -> None:
    """Her yazmanın başı (`yazma_kapisi()`'ndan sonra): ilk hesap kurulu, kapı ve "Kim"."""
    app_password.require_password_set()
    _kapi()
    _daralt(roller)


def yerel_gun(an: datetime) -> date:
    """Anın Europe/Istanbul takvim günü."""
    return timezone.localtime(an).date()


def birinci_toplanti_gunu(kurul: GeneralAssembly) -> date:
    """Genel kurul kurallarının olay günü: birinci toplantının yerel günü (modül başlığı)."""
    if kurul.first_meeting_at is None:
        raise ValueError(BIRINCI_TOPLANTI_GEREKLI)
    return yerel_gun(kurul.first_meeting_at)


def kural_donemi(kurul: GeneralAssembly) -> OabTerm:
    """Kuralların okunduğu ve uyum satırlarının yazıldığı dönem: kapanacak dönem; yeni okulun ilk genel
    kurulunda hazırlık dönemi (U1)."""
    donem = kurul.term if kurul.term_id is not None else kurul.opens_term
    if donem is None:
        raise ValueError(DONEMSIZ_GENEL_KURUL)
    return donem


def _guncel(kurul: GeneralAssembly) -> GeneralAssembly:
    """Kaydın güncel hâli; dönemi yazılabilir olmalı (kapanmış, iptal, kopyası tutmayan dönem değil)."""
    guncel: GeneralAssembly = GeneralAssembly.objects.select_related(
        "term__rule_package", "opens_term__rule_package"
    ).get(pk=kurul.pk)
    donem_kilidi.yazma_denetimi(kural_donemi(guncel), hazirlik_yazimi=True)
    return guncel


def _durum(kurul: GeneralAssembly, *durumlar: str) -> None:
    if kurul.status not in durumlar:
        raise ValueError(DURUM_GECERSIZ)


def _yer(metin: str) -> str:
    deger = " ".join(metin.split())
    if len(deger) > YER_MAX:
        raise ValueError(YER_UZUN)
    return deger


def _sayi(deger: object) -> int:
    if not isinstance(deger, int) or isinstance(deger, bool) or deger < 0:
        raise ValueError(SAYI_GECERSIZ)
    return deger


def _secimli_sayi(deger: object) -> int | None:
    return None if deger is None else _sayi(deger)


def kurallari_tasiyor_mu(donem: OabTerm, gun: date) -> bool:
    """Dönemin kopyası genel kurul akışının kurallarını taşıyor mu? (U1; olay gününde yürürlükte
    olmayan kural da taşınmış sayılır, `denetle` onu "denetlenmedi" diye döner)."""
    for kimlik in GENEL_KURUL_KURALLARI:
        try:
            kural_kaydi(kimlik, tarih=gun, donem=donem)
        except YururlukteDegerYok:
            continue
        except BilinmeyenKural:
            return False
    return True


def _kurallar_denetimi(donem: OabTerm, gun: date) -> None:
    if not kurallari_tasiyor_mu(donem, gun):
        raise KuralSurumuGuncellenmeli


def _ay_ekle(gun: date, ay: int) -> date:
    """Takvim ayı aritmetiği: ayın son günüyle sınırlı (31.08 + 2 ay = 31.10; 31.12 + 2 ay = 28.02)."""
    toplam = gun.year * _YILIN_AYLARI + gun.month - 1 + ay
    yil, ay_sirasi = divmod(toplam, _YILIN_AYLARI)
    son_gun = calendar.monthrange(yil, ay_sirasi + 1)[1]
    return date(yil, ay_sirasi + 1, min(gun.day, son_gun))


def ay_farki(baslangic: date, gun: date) -> int:
    """`gun`, `baslangic`tan itibaren kaçıncı takvim ayının içinde? (`genel_kurul.yeni_okul_ay`, birim
    `ay`): 15.09'dan 15.11 iki ay, 16.11 üç aydır. Başlangıçtan önceki gün sıfırdır."""
    fark = (gun.year - baslangic.year) * _YILIN_AYLARI + gun.month - baslangic.month
    if gun > _ay_ekle(baslangic, fark):
        fark += 1
    return max(fark, 0)


def ders_yili_ayi(baslangic: date, gun: date) -> int:
    """`gun`'ün ayı, ders yılının başladığı takvim yılından sayılarak (`genel_kurul.olagan_son_ay`, birim
    `takvim_ayi`): Ekim 10, Kasım 11, ertesi yılın Ocak'ı 13."""
    return (gun.year - baslangic.year) * _YILIN_AYLARI + gun.month


def planlama_bilgileri() -> tuple[str, ...]:
    """Planlamanın bilgi satırları ([B]; tasarım §7.1 `PLANLANDI`): okul kartındaki öğrenci mevcudu ve
    tarihi (yeter sayının girdisi, ilanda dondurulur; U7) ve veli listesi aktarılmadıysa öneri (§8.4).
    Kişisizdir, yazmaz."""
    okul = SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).first()
    bilgiler: list[str] = []
    if okul is None or okul.student_count is None or okul.student_count_as_of is None:
        bilgiler.append(
            "Okul kartında öğrenci mevcudu girilmemiş. Yeter sayı ilanda bu sayıdan hesaplanır ve "
            "dondurulur (md. 9/2); ilandan önce girilmelidir."
        )
    else:
        bilgiler.append(
            f"Okul kartındaki öğrenci mevcudu {okul.student_count} "
            f"({okul.student_count_as_of:%d.%m.%Y} tarihli). Yeter sayı ilanda bu sayıdan hesaplanır "
            "ve dondurulur (md. 9/2); güncel değilse ilandan önce okul kartından güncelleyin."
        )
    if not ParentRoster.objects.exists():
        bilgiler.append(VELI_LISTESI_ONERISI)
    return tuple(bilgiler)


def _donem_adi(yil_adi: str, gun: date) -> str:
    """Hazırlık döneminin adı; aynı adlı (iptal edilmemiş) dönem varsa genel kurulun günüyle ayrılır."""
    ad = f"{yil_adi} birlik dönemi"
    if OabTerm.objects.exclude(status=TermStatus.IPTAL).filter(name=ad).exists():
        ad = f"{ad} ({gun:%d.%m.%Y})"
    return ad


def _hazirlik_donemi_ac(gun: date) -> OabTerm:
    """Olağan genel kurulun açacağı `HAZIRLIK` dönemi (U2, U5); bağı çağıran aynı işlemde yazar (U3)."""
    yil = gecis.ders_yili_bul(gun)
    if yil is None:
        raise ValueError(DERS_YILI_YOK)
    hesap = iz.yazar_hesabi()
    donem = OabTerm.objects.create(
        name=_donem_adi(yil.name, gun),
        school_year=yil,
        rule_package=kural_bagi.acilis_bagi(),
        status=TermStatus.HAZIRLIK,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(donem, onceki=None)
    return donem


def _hazirlik_ders_yilini_esitle(kurul: GeneralAssembly, gun: date) -> None:
    """Birinci toplantı başka ders yılına taşındıysa hazırlık döneminin ders yılı ve adı izlenir (U5)."""
    hazirlik = kurul.opens_term
    if hazirlik is None:
        return
    yil = gecis.ders_yili_bul(gun)
    if yil is None:
        raise ValueError(DERS_YILI_YOK)
    if yil.pk == hazirlik.school_year_id:
        return
    onceki = denetim_izi.anlik(hazirlik)
    hazirlik.school_year = yil
    hazirlik.name = _donem_adi(yil.name, gun)
    hazirlik.updated_by_id = iz.yazar_hesabi()
    hazirlik.save(update_fields=["school_year", "name", "updated_at", "updated_by"])
    denetim_izi.degisiklik(hazirlik, onceki=onceki)


def _gundem_yaz(kurul: GeneralAssembly, maddeler: Sequence[tuple[str, str]]) -> list[AgendaItem]:
    """Gündem maddelerini sırayla yazar (1'den); her madde izlidir."""
    hesap = iz.yazar_hesabi()
    yazilanlar: list[AgendaItem] = []
    for sira, (tur, baslik) in enumerate(maddeler, start=1):
        madde = AgendaItem.objects.create(
            assembly=kurul,
            order=sira,
            kind=tur,
            title=baslik,
            created_by_id=hesap,
            updated_by_id=hesap,
        )
        denetim_izi.degisiklik(madde, onceki=None)
        yazilanlar.append(madde)
    return yazilanlar


def _cagri_gundemi(gundem: Sequence[GundemMaddesi]) -> list[tuple[str, str]]:
    if not gundem:
        raise ValueError(GUNDEM_GEREKLI)
    maddeler: list[tuple[str, str]] = []
    for madde in gundem:
        if madde.kind not in AgendaItemKind.values:
            raise ValueError(GUNDEM_TURU_GECERSIZ)
        baslik = " ".join(madde.title.split())
        if not baslik:
            raise ValueError(GUNDEM_BASLIGI_GEREKLI)
        if len(baslik) > BASLIK_MAX:
            raise ValueError(GUNDEM_BASLIGI_UZUN)
        maddeler.append((madde.kind, baslik))
    return maddeler


def _toplanti_gunu_denetimi(tur: _Tur) -> None:
    """Olağan genel kurulun toplantı günü (md. 9/1): Ekim sonu (`olagan_son_ay`; S3: birinci
    toplantının günü) ya da yeni açılan okulda açılıştan iki ay (`yeni_okul_ay`)."""
    kurul = tur.kurul
    if kurul.kind != AssemblyKind.OLAGAN:
        return
    if kurul.term_id is None:
        okul = SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).first()
        acilis = None if okul is None else okul.opened_on
        gozlenen: Any = VERI_YOK if acilis is None else ay_farki(acilis, tur.gun)
        sonuc = uyum.denetle("genel_kurul.yeni_okul_ay", gozlenen, konu=kurul, **tur.ortak())
        tur.kaydet("genel_kurul.yeni_okul_ay", sonuc)
        return
    hazirlik = kurul.opens_term
    if hazirlik is None:  # tür daraltması: olağan genel kurul hazırlık dönemini açar
        raise ValueError(DERS_YILI_YOK)
    ay = ders_yili_ayi(hazirlik.school_year.start_date, tur.gun)
    sonuc = uyum.denetle("genel_kurul.olagan_son_ay", ay, konu=kurul, **tur.ortak())
    tur.kaydet("genel_kurul.olagan_son_ay", sonuc)


def _kaydet(kurul: GeneralAssembly, onceki: denetim_izi.Anlik, alanlar: Sequence[str]) -> None:
    """Kurulun değişen alanlarını yazar ve izler (izli servis kalıbı)."""
    kurul.updated_by_id = iz.yazar_hesabi()
    kurul.save(update_fields=[*alanlar, "updated_at", "updated_by"])
    denetim_izi.degisiklik(kurul, onceki=onceki)


def _ozeti_yaz(kurul: GeneralAssembly, tur: _Tur, alanlar: Sequence[str]) -> None:
    """Geçişin alanlarını ve uyarı özetini tek yazımla yazar ve izler; önceki hâl veritabanından
    okunur (alanlar bellekteki kayıtta değiştirilmiş olur). Yazılacak bir şey yoksa yazmaz."""
    onceki = denetim_izi.anlik(GeneralAssembly.objects.get(pk=kurul.pk))
    ozet = tur.ozet()
    yazilacak = list(alanlar)
    if ozet != (kurul.rule_warnings or []):
        kurul.rule_warnings = ozet
        yazilacak.append("rule_warnings")
    if yazilacak:
        _kaydet(kurul, onceki, yazilacak)


def _sonuc(tur: _Tur, bilgiler: Sequence[str] = ()) -> GenelKurulSonucu:
    return GenelKurulSonucu(kurul=tur.kurul, uyarilar=tuple(tur.uyarilar), bilgiler=tuple(bilgiler))


# ---------------------------------------------------------------------------
# F1c'nin asgari yolu ve yeter sayının dondurulması
# ---------------------------------------------------------------------------
@transaction.atomic
def genel_kurul_olustur(
    *,
    donem: OabTerm,
    kind: AssemblyKind,
    first_meeting_at: datetime | None = None,
    opens_term: OabTerm | None = None,
) -> GeneralAssembly:
    """Genel kurul kaydı açar (`PLANLANDI`; F1c'nin asgari yolu). Hazırlık dönemi, tohum gündem ve
    planlamanın kuralları yoktur: F2'nin planlama yolu `planla`'dır; bu işlev organ ve evrak
    akışlarının (seçim, görev bölümü) genel kurul bağını kuran düşük düzey kayıttır. Kapısı genel
    kurul yazma kapısıdır."""
    yazma_kapisi()
    app_password.require_password_set()
    _kapi()
    donem = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(donem, hazirlik_yazimi=True)
    hesap = iz.yazar_hesabi()
    kurul = GeneralAssembly.objects.create(
        term=donem,
        opens_term=opens_term,
        kind=kind,
        first_meeting_at=first_meeting_at,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(kurul, onceki=None)
    return kurul


@transaction.atomic
def yeter_sayiyi_dondur(kurul: GeneralAssembly, *, tarih: date) -> GeneralAssembly:
    """Okul kartındaki mevcudu kurula kopyalar, yeter sayıyı hesaplar ve dondurur (O7, §7.1 ilan).

    İlan geçişi `tarih` olarak birinci toplantının gününü verir (U7). İptal edilmiş genel kurulda
    dondurma reddedilir; dondurulmuş yeter sayı yeniden hesaplanmaz (sert, hesap bütünlüğü).
    """
    yazma_kapisi()
    app_password.require_password_set()
    _kapi()
    guncel: GeneralAssembly = GeneralAssembly.objects.select_related(
        "term__rule_package", "opens_term__rule_package"
    ).get(pk=kurul.pk)
    # Kurallar kapanacak dönemin kopyasından okunur; yeni okulun ilk genel kurulunda kapanacak dönem
    # yoktur, hazırlık döneminin kopyasından okunur (plan F2 §7 U1; `ck_generalassembly_donem`).
    donem = guncel.term if guncel.term is not None else guncel.opens_term
    if donem is None:
        raise ValueError(DONEMSIZ_GENEL_KURUL)
    donem_kilidi.yazma_denetimi(donem, hazirlik_yazimi=True)
    if guncel.status == AssemblyStatus.IPTAL:
        raise ValueError(IPTAL_KURULDA_DONDURULMAZ)
    if guncel.quorum_required is not None:
        raise YeterSayiDonduruldu
    mevcut = SchoolConfig.objects.get(pk=SchoolConfig.SINGLETON_PK).student_count
    if mevcut is None:
        raise ValueError(OGRENCI_MEVCUDU_BOS)
    hesap = genel_kurul.genel_kurul_yeter_sayisi(mevcut, tarih=tarih, donem=donem)
    onceki = denetim_izi.anlik(guncel)
    guncel.student_count_snapshot = mevcut
    guncel.quorum_base = hesap.taban
    guncel.quorum_multiplier = hesap.carpan
    guncel.quorum_required = hesap.gerekli
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(
        update_fields=[
            "student_count_snapshot",
            "quorum_base",
            "quorum_multiplier",
            "quorum_required",
            "updated_at",
            "updated_by",
        ]
    )
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel


# ---------------------------------------------------------------------------
# PLANLANDI (oluşturma) ve tarih değişikliği
# ---------------------------------------------------------------------------
@transaction.atomic
def planla(
    *,
    kind: str,
    first_meeting_at: datetime,
    venue: str = "",
    gerekce: uyum.Gerekce | None = None,
) -> GenelKurulSonucu:
    """Genel kurulu planlar (`PLANLANDI`; modül başlığı "Hazırlık dönemi", "Gündem tohumu").

    Olağanda kapanacak dönem açık dönemdir; hazırlık dönemi açılır, bağı ve tohum gündem aynı işlemde
    yazılır; toplantı günü Ekim sonu (yeni okulda açılıştan iki ay) ile denetlenir. Olağanüstüde dönem
    açılmaz, tohum gündem yoktur. Bilgi satırları: öğrenci mevcudu ve tarihi, veli listesi önerisi.
    """
    yazma_kapisi()
    _baslangic(PLANLAYAN_ROLLER)
    if kind not in AssemblyKind.values:
        raise ValueError(TUR_GECERSIZ)
    yer = _yer(venue)
    gun = yerel_gun(first_meeting_at)
    acik: OabTerm | None = (
        OabTerm.objects.select_related("rule_package").filter(status=TermStatus.ACIK).first()
    )
    yeni_okul = acik is None
    if acik is None:
        if kind == AssemblyKind.OLAGANUSTU:
            raise ValueError(OLAGANUSTU_ACIK_DONEMDE)
        # Yeni okulun ilk genel kurulu hazırlıktaysa asıl neden odur (açık dönem yeni okulda olamaz).
        if OabTerm.objects.filter(status=TermStatus.HAZIRLIK).exists():
            raise ValueError(HAZIRLIK_DONEMI_VAR)
        if OabTerm.objects.exclude(status=TermStatus.IPTAL).exists():
            raise ValueError(ACIK_DONEM_YOK)
        okul = SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).first()
        if okul is None or okul.opened_on is None:
            raise ValueError(YENI_OKUL_ACILIS_TARIHI_YOK)
    else:
        donem_kilidi.yazma_denetimi(acik)
        _kurallar_denetimi(acik, gun)
    hazirlik: OabTerm | None = None
    if kind == AssemblyKind.OLAGAN:
        if OabTerm.objects.filter(status=TermStatus.HAZIRLIK).exists():
            raise ValueError(HAZIRLIK_DONEMI_VAR)
        hazirlik = _hazirlik_donemi_ac(gun)
        if yeni_okul:
            _kurallar_denetimi(hazirlik, gun)
    hesap = iz.yazar_hesabi()
    kurul = GeneralAssembly.objects.create(
        term=acik,
        opens_term=hazirlik,
        kind=kind,
        called_by=AssemblyCaller.MUDUR_YENI_OKUL if yeni_okul else "",
        first_meeting_at=first_meeting_at,
        venue=yer,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(kurul, onceki=None)
    if hazirlik is not None:
        onceki = denetim_izi.anlik(hazirlik)
        hazirlik.opened_by_assembly = kurul
        hazirlik.updated_by_id = hesap
        hazirlik.save(update_fields=["opened_by_assembly", "updated_at", "updated_by"])
        denetim_izi.degisiklik(hazirlik, onceki=onceki)
        _gundem_yaz(kurul, TOHUM_GUNDEM)
    kurul = _guncel(kurul)
    tur = _Tur(kurul, gerekce)
    _toplanti_gunu_denetimi(tur)
    _ozeti_yaz(kurul, tur, ())
    bilgiler = list(planlama_bilgileri())
    if kind == AssemblyKind.OLAGANUSTU:
        bilgiler.append(OLAGANUSTU_DONEM_ACMAZ_BILGISI)
    return _sonuc(tur, bilgiler)


@transaction.atomic
def toplanti_bilgisini_degistir(
    kurul: GeneralAssembly,
    *,
    first_meeting_at: datetime,
    venue: str | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> GenelKurulSonucu:
    """İlandan önce birinci toplantının zamanını (ve yerini) değiştirir; toplantı günü kuralları
    yeniden denetlenir (plan F2 §3.1 "PLANLANDI ve tarih değişiminde"), hazırlık döneminin ders yılı
    yeni güne göre izlenir (U5)."""
    yazma_kapisi()
    _baslangic(PLANLAYAN_ROLLER)
    guncel = _guncel(kurul)
    if guncel.status not in (AssemblyStatus.PLANLANDI, AssemblyStatus.CAGRILDI):
        raise ValueError(TARIH_DEGISMEZ)
    gun = yerel_gun(first_meeting_at)
    _kurallar_denetimi(kural_donemi(guncel), gun)
    _hazirlik_ders_yilini_esitle(guncel, gun)
    guncel = _guncel(guncel)
    guncel.first_meeting_at = first_meeting_at
    alanlar = ["first_meeting_at"]
    if venue is not None:
        guncel.venue = _yer(venue)
        alanlar.append("venue")
    tur = _Tur(guncel, gerekce)
    _toplanti_gunu_denetimi(tur)
    _ozeti_yaz(guncel, tur, alanlar)
    return _sonuc(tur)


# ---------------------------------------------------------------------------
# PLANLANDI → CAGRILDI
# ---------------------------------------------------------------------------
def _cagiran(kurul: GeneralAssembly, called_by: str) -> str:
    """Çağıran: olağanda kayıttan belirlidir (yönetim kurulu; yeni okulda müdür), olağanüstüde zorunlu
    ve kapalı listedir (`AssemblyCaller`)."""
    if kurul.kind == AssemblyKind.OLAGAN:
        beklenen = (
            AssemblyCaller.YONETIM_KURULU
            if kurul.term_id is not None
            else AssemblyCaller.MUDUR_YENI_OKUL
        )
        if called_by and called_by != beklenen:
            raise ValueError(OLAGAN_CAGIRAN)
        return str(beklenen)
    if not called_by:
        raise ValueError(CAGIRAN_GEREKLI)
    if called_by not in AssemblyCaller.values:
        raise ValueError(CAGIRAN_GECERSIZ)
    return called_by


@transaction.atomic
def cagir(
    kurul: GeneralAssembly,
    *,
    called_by: str = "",
    call_reason: str = "",
    gundem: Sequence[GundemMaddesi] = (),
    member_application_count: int | None = None,
    member_count_declared: int | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> GenelKurulSonucu:
    """Genel kurulu çağırır (`PLANLANDI → CAGRILDI`; modül başlığı "Çağrı")."""
    yazma_kapisi()
    app_password.require_password_set()
    _kapi()
    guncel = _guncel(kurul)
    cagiran = _cagiran(guncel, called_by)
    _daralt(CAGIRAN_ROLLERI.get(cagiran, frozenset()))
    _durum(guncel, AssemblyStatus.PLANLANDI)
    basvuran = _secimli_sayi(member_application_count)
    uye_sayisi = _secimli_sayi(member_count_declared)
    olaganustu = guncel.kind == AssemblyKind.OLAGANUSTU
    neden = call_reason.strip()
    maddeler: list[tuple[str, str]] = []
    if not olaganustu:
        if neden or gundem or basvuran is not None or uye_sayisi is not None:
            raise ValueError(OLAGAN_CAGRI_ALANLARI)
    else:
        if not neden:
            raise ValueError(CAGRI_NEDENI_GEREKLI)
        maddeler = _cagri_gundemi(gundem)
        if cagiran != AssemblyCaller.UYE_BASVURUSU and (
            basvuran is not None or uye_sayisi is not None
        ):
            raise ValueError(BASVURU_SAYILARI_YALNIZ_UYELERDE)
        if uye_sayisi == 0:
            raise ValueError(UYE_SAYISI_SIFIR)
        if basvuran is not None and uye_sayisi is not None and basvuran > uye_sayisi:
            raise ValueError(BASVURAN_UYEDEN_COK)
    tur = _Tur(guncel, gerekce)
    bilgiler: list[str] = []
    if olaganustu:
        sonuc = uyum.denetle(
            "genel_kurul.olaganustu_cagiranlar", cagiran, konu=guncel, **tur.ortak()
        )
        tur.kaydet("genel_kurul.olaganustu_cagiranlar", sonuc)
        if cagiran == AssemblyCaller.UYE_BASVURUSU:
            oran: Any = (
                VERI_YOK
                if basvuran is None or uye_sayisi is None
                else Decimal(basvuran) / Decimal(uye_sayisi)
            )
            sonuc = uyum.denetle(
                "genel_kurul.olaganustu_basvuru_oran", oran, konu=guncel, **tur.ortak()
            )
            tur.kaydet("genel_kurul.olaganustu_basvuru_oran", sonuc)
            bilgiler.append(BASVURU_YAZISI_BILGISI)
        bilgiler.append(OLAGANUSTU_DONEM_ACMAZ_BILGISI)
    elif guncel.call_decision_id is None:
        if guncel.term is None:  # tür daraltması: yönetim kurulunun çağrısı kapanacak dönemdedir
            raise ValueError(DONEMSIZ_GENEL_KURUL)
        uyum.akis_sapmasi(
            KARARSIZ_CAGRI_AKISI, KARARSIZ_CAGRI, donem=guncel.term, konu=guncel, gerekce=gerekce
        )
        tur.akis(KARARSIZ_CAGRI_AKISI, KARARSIZ_CAGRI)
    if maddeler:
        _gundem_yaz(guncel, maddeler)
    guncel.called_by = cagiran
    guncel.call_reason = neden
    guncel.member_application_count = basvuran
    guncel.member_count_declared = uye_sayisi
    guncel.status = AssemblyStatus.CAGRILDI
    _ozeti_yaz(
        guncel,
        tur,
        (
            "called_by",
            "call_reason",
            "member_application_count",
            "member_count_declared",
            "status",
        ),
    )
    return _sonuc(tur, bilgiler)


# ---------------------------------------------------------------------------
# İlan (CAGRILDI → ILAN_EDILDI; ikinci toplantının ilanı; kanal kanıtları)
# ---------------------------------------------------------------------------
def kurulun_duyurulari(kurul: GeneralAssembly) -> list[Announcement]:
    """Genel kurulun ilanları, yazılış sırasıyla: ilki birinci toplantınındır."""
    return list(
        Announcement.objects.filter(
            subject_type=denetim_izi.model_etiketi(GeneralAssembly),
            subject_id=denetim_izi.kimlik_metni(GeneralAssembly, kurul.pk),
        ).order_by("pk")
    )


def _yayimla(duyuru: Announcement) -> None:
    """Kanıt günü girilmiş taslak ilan yayımlanmış sayılır (`TASLAK → YAYIMLANDI`; izli)."""
    if duyuru.status != AnnouncementStatus.TASLAK or not (
        duyuru.distributed_written_on or duyuru.posted_board_on or duyuru.published_web_on
    ):
        return
    onceki = denetim_izi.anlik(duyuru)
    duyuru.status = AnnouncementStatus.YAYIMLANDI
    duyuru.updated_by_id = iz.yazar_hesabi()
    duyuru.save(update_fields=["status", "updated_at", "updated_by"])
    denetim_izi.degisiklik(duyuru, onceki=onceki)


def _duyuru_yaz(kurul: GeneralAssembly, kanallar: IlanKanallari) -> Announcement:
    """İlan kaydı (konu genel kurul); kanal günleri girilmişse yayımlanır."""
    hesap = iz.yazar_hesabi()
    duyuru = Announcement.objects.create(
        term=kural_donemi(kurul),
        kind=(
            AnnouncementKind.GK_CAGRISI
            if kurul.kind == AssemblyKind.OLAGAN
            else AnnouncementKind.OLAGANUSTU_GK_CAGRISI
        ),
        subject_type=denetim_izi.model_etiketi(GeneralAssembly),
        subject_id=denetim_izi.kimlik_metni(GeneralAssembly, kurul.pk),
        distributed_written_on=kanallar.distributed_written_on,
        posted_board_on=kanallar.posted_board_on,
        published_web_on=kanallar.published_web_on,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(duyuru, onceki=None)
    _yayimla(duyuru)
    return duyuru


def _ilan_denetimi(
    tur: _Tur, duyuru: Announcement, kanallar: IlanKanallari, toplanti_gunu: date
) -> None:
    """İlanın iki kuralı, konusu ilan kaydı: 15 gün (en geç kanal, U9) ve üç kanal (eksikse
    tamamlanacak)."""
    en_gec = kanallar.en_gec()
    gun_farki: Any = VERI_YOK if en_gec is None else (toplanti_gunu - en_gec).days
    sonuc = uyum.denetle("genel_kurul.ilan_en_az_gun", gun_farki, konu=duyuru, **tur.ortak())
    tur.kaydet("genel_kurul.ilan_en_az_gun", sonuc, kurulun=False)
    girilen = kanallar.girilenler()
    gozlenen: Any = girilen if len(girilen) == len(TUM_KANALLAR) else VERI_YOK
    sonuc = uyum.denetle("genel_kurul.ilan_kanallari", gozlenen, konu=duyuru, **tur.ortak())
    tur.kaydet("genel_kurul.ilan_kanallari", sonuc, kurulun=False)


def _a1(kurul: GeneralAssembly) -> str:
    return A1_ATFI if kurul.kind == AssemblyKind.OLAGANUSTU else ""


def _ikinci_toplanti_denetimi(tur: _Tur, second_meeting_at: datetime) -> None:
    """İkinci toplantı birinci toplantı gününden en geç 30 gün sonra (md. 9/2; olağanüstüde A-1)."""
    birinci = tur.kurul.first_meeting_at
    if birinci is not None and second_meeting_at <= birinci:
        raise ValueError(IKINCI_TOPLANTI_SIRASI)
    fark = (yerel_gun(second_meeting_at) - tur.gun).days
    sonuc = uyum.denetle(
        "genel_kurul.ikinci_toplanti_en_gec_gun",
        fark,
        konu=tur.kurul,
        ek_ileti=_a1(tur.kurul),
        **tur.ortak(),
    )
    tur.kaydet("genel_kurul.ikinci_toplanti_en_gec_gun", sonuc)


@transaction.atomic
def ilan_et(
    kurul: GeneralAssembly,
    *,
    kanallar: IlanKanallari | None = None,
    second_meeting_at: datetime | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> GenelKurulSonucu:
    """İlan (`CAGRILDI → ILAN_EDILDI`; modül başlığı "İlan"): yeter sayı dondurulur (U7), ilan kaydı
    yazılır, 15 gün ve kanallar denetlenir; ikinci toplantı tarihi girildiyse 30 gün denetlenir."""
    yazma_kapisi()
    _baslangic(ILAN_VE_TOPLANTI_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, AssemblyStatus.CAGRILDI)
    kanal = kanallar if kanallar is not None else IlanKanallari()
    yeter_sayiyi_dondur(guncel, tarih=birinci_toplanti_gunu(guncel))
    guncel = _guncel(guncel)
    tur = _Tur(guncel, gerekce)
    alanlar = ["announced_on", "status"]
    if second_meeting_at is not None:
        _ikinci_toplanti_denetimi(tur, second_meeting_at)
        guncel.second_meeting_at = second_meeting_at
        alanlar.append("second_meeting_at")
    duyuru = _duyuru_yaz(guncel, kanal)
    _ilan_denetimi(tur, duyuru, kanal, tur.gun)
    guncel.announced_on = kanal.en_gec()
    guncel.status = AssemblyStatus.ILAN_EDILDI
    _ozeti_yaz(guncel, tur, alanlar)
    bilgiler = (GUNDEME_BAGLILIK_BILGISI,) if guncel.kind == AssemblyKind.OLAGANUSTU else ()
    return _sonuc(tur, bilgiler)


@transaction.atomic
def ikinci_toplanti_ilani(
    kurul: GeneralAssembly,
    *,
    second_meeting_at: datetime,
    kanallar: IlanKanallari | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> GenelKurulSonucu:
    """Birinci toplantıda yeter sayı sağlanamadıktan sonra ikinci toplantının ayrı ilanı (tasarım §7.1
    `ILAN_EDILDI → YETER_SAYI_YOK`): 15 gün (ikinci toplantının gününe) ve 30 gün (birinci toplantı
    gününden) ayrı ayrı denetlenir; ikisi birlikte sağlanamıyorsa iki uyarı da görünür. Olağanüstüde
    de (A-1)."""
    yazma_kapisi()
    _baslangic(ILAN_VE_TOPLANTI_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, AssemblyStatus.YETER_SAYI_YOK)
    if len(kurulun_duyurulari(guncel)) > 1:
        raise ValueError(IKINCI_ILAN_VAR)
    kanal = kanallar if kanallar is not None else IlanKanallari()
    tur = _Tur(guncel, gerekce)
    _ikinci_toplanti_denetimi(tur, second_meeting_at)
    duyuru = _duyuru_yaz(guncel, kanal)
    _ilan_denetimi(tur, duyuru, kanal, yerel_gun(second_meeting_at))
    guncel.second_meeting_at = second_meeting_at
    guncel.second_announced_on = kanal.en_gec()
    _ozeti_yaz(guncel, tur, ("second_meeting_at", "second_announced_on"))
    return _sonuc(tur)


@transaction.atomic
def ilan_kanitlarini_yaz(
    duyuru: Announcement,
    *,
    kanallar: IlanKanallari,
    gerekce: uyum.Gerekce | None = None,
) -> GenelKurulSonucu:
    """İlanın kanal kanıt günlerini sonradan girer ya da düzeltir (tamamlanacaklar; tutanak
    tamamlanana dek). 15 gün ve kanallar yeniden denetlenir: eksik kapanır, sapma gerekçe ister."""
    yazma_kapisi()
    _baslangic(ILAN_VE_TOPLANTI_ROLLERI)
    guncel_duyuru = Announcement.objects.get(pk=duyuru.pk)
    if guncel_duyuru.subject_type != denetim_izi.model_etiketi(GeneralAssembly):
        raise ValueError(DUYURU_GENEL_KURULUN_DEGIL)
    guncel = _guncel(GeneralAssembly.objects.get(pk=int(guncel_duyuru.subject_id)))
    if guncel.status not in _KANIT_YAZILABILIR:
        raise ValueError(DURUM_GECERSIZ)
    birinci = kurulun_duyurulari(guncel)[0].pk == guncel_duyuru.pk
    if birinci:
        toplanti_gunu = birinci_toplanti_gunu(guncel)
    elif guncel.second_meeting_at is not None:
        toplanti_gunu = yerel_gun(guncel.second_meeting_at)
    else:
        raise ValueError(IKINCI_TOPLANTI_TARIHI_YOK)
    onceki = denetim_izi.anlik(guncel_duyuru)
    guncel_duyuru.distributed_written_on = kanallar.distributed_written_on
    guncel_duyuru.posted_board_on = kanallar.posted_board_on
    guncel_duyuru.published_web_on = kanallar.published_web_on
    guncel_duyuru.updated_by_id = iz.yazar_hesabi()
    guncel_duyuru.save(
        update_fields=[
            "distributed_written_on",
            "posted_board_on",
            "published_web_on",
            "updated_at",
            "updated_by",
        ]
    )
    denetim_izi.degisiklik(guncel_duyuru, onceki=onceki)
    _yayimla(guncel_duyuru)
    tur = _Tur(guncel, gerekce)
    _ilan_denetimi(tur, guncel_duyuru, kanallar, toplanti_gunu)
    if birinci:
        guncel.announced_on = kanallar.en_gec()
        _ozeti_yaz(guncel, tur, ("announced_on",))
    else:
        guncel.second_announced_on = kanallar.en_gec()
        _ozeti_yaz(guncel, tur, ("second_announced_on",))
    return _sonuc(tur)


# ---------------------------------------------------------------------------
# Toplantılar (ILAN_EDILDI → YAPILDI | YETER_SAYI_YOK; YETER_SAYI_YOK → YAPILDI)
# ---------------------------------------------------------------------------
def _katilim_dogrula(katilim: Katilim) -> dict[str, int]:
    """Sayılar sıfır ya da pozitif tam sayıdır; dağılım tanımlı türlerdir ve toplamı katılımı tutar."""
    katilan = _sayi(katilim.attendee_count)
    _secimli_sayi(katilim.parent_students_count)
    _secimli_sayi(katilim.observer_count)
    dagilim = dict(katilim.attendance_by_kind)
    for tur_adi, sayi in dagilim.items():
        if tur_adi not in AttendanceKind.values:
            raise ValueError(DAGILIM_GECERSIZ)
        _sayi(sayi)
    if dagilim and sum(dagilim.values()) != katilan:
        raise ValueError(DAGILIM_TOPLAMI)
    return dagilim


def _katilim_alanlari(
    kurul: GeneralAssembly, katilim: Katilim, dagilim: dict[str, int]
) -> list[str]:
    """Toplantının dağılım, velisi katılan öğrenci ve gözlemci sayısını kayda koyar (yazmaz)."""
    kurul.attendance_by_kind = dagilim
    kurul.parent_students_count = katilim.parent_students_count
    kurul.observer_count = katilim.observer_count
    return ["attendance_by_kind", "parent_students_count", "observer_count"]


@transaction.atomic
def birinci_toplanti(
    kurul: GeneralAssembly, *, katilim: Katilim, gerekce: uyum.Gerekce | None = None
) -> GenelKurulSonucu:
    """Birinci toplantının sonucu (modül başlığı "Toplantılar"): katılım dondurulmuş yeter sayıdan az
    değilse `YAPILDI`, azsa `YETER_SAYI_YOK` (md. 9/2; programın hesapladığı sonuç). Katılım sayısı her
    iki hâlde de yazılır. Açılışı okul müdürü yapar (md. 10/1-b; bilgi)."""
    yazma_kapisi()
    _baslangic(ILAN_VE_TOPLANTI_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, AssemblyStatus.ILAN_EDILDI)
    dagilim = _katilim_dogrula(katilim)
    if guncel.quorum_required is None:  # tür daraltması: ilandan sonra yeter sayı doludur (U7)
        raise ValueError(DURUM_GECERSIZ)
    tur = _Tur(guncel, gerekce)
    guncel.first_attendee_count = katilim.attendee_count
    alanlar = ["first_attendee_count", "status", *_katilim_alanlari(guncel, katilim, dagilim)]
    if katilim.attendee_count >= guncel.quorum_required:
        guncel.status = AssemblyStatus.YAPILDI
        guncel.held_at_meeting = AssemblyMeeting.BIRINCI
        alanlar.append("held_at_meeting")
    else:
        guncel.status = AssemblyStatus.YETER_SAYI_YOK
    _ozeti_yaz(guncel, tur, alanlar)
    return _sonuc(tur, (MUDUR_ACILIS_BILGISI,))


@transaction.atomic
def ikinci_toplanti(
    kurul: GeneralAssembly, *, katilim: Katilim, gerekce: uyum.Gerekce | None = None
) -> GenelKurulSonucu:
    """İkinci toplantı (`YETER_SAYI_YOK → YAPILDI`): çoğunluk aranmaz (md. 9/2; olağanüstüde de, A-1);
    katılım yeter sayıyla karşılaştırılmaz. Toplantının tarihi ilanda girilmiş olmalıdır."""
    yazma_kapisi()
    _baslangic(ILAN_VE_TOPLANTI_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, AssemblyStatus.YETER_SAYI_YOK)
    if guncel.second_meeting_at is None:
        raise ValueError(IKINCI_TOPLANTI_TARIHI_YOK)
    dagilim = _katilim_dogrula(katilim)
    tur = _Tur(guncel, gerekce)
    sonuc = uyum.denetle(
        "genel_kurul.ikinci_toplanti_cogunluk_aranmaz",
        True,
        konu=guncel,
        ek_ileti=_a1(guncel),
        **tur.ortak(),
    )
    tur.kaydet("genel_kurul.ikinci_toplanti_cogunluk_aranmaz", sonuc)
    guncel.second_attendee_count = katilim.attendee_count
    guncel.status = AssemblyStatus.YAPILDI
    guncel.held_at_meeting = AssemblyMeeting.IKINCI
    _ozeti_yaz(
        guncel,
        tur,
        [
            "second_attendee_count",
            "status",
            "held_at_meeting",
            *_katilim_alanlari(guncel, katilim, dagilim),
        ],
    )
    return _sonuc(tur)


# ---------------------------------------------------------------------------
# İptal
# ---------------------------------------------------------------------------
@transaction.atomic
def iptal_et(kurul: GeneralAssembly, *, cancel_reason: str) -> GeneralAssembly:
    """Genel kurulu iptal eder (`… → IPTAL`; gerekçe zorunlu, şifreli). Olağanda hazırlık dönemi de
    `IPTAL` olur (tasarım §7.1, §5.2.1). İlan ve dondurulmuş yeter sayı iz olarak kalır. Kurulun ve
    ilanlarının açık `EKSIK` satırları kapanır: girilecek veri (ilanın kanıtı, başvuru sayıları) artık
    girilmeyecek, satır dönemin tamamlanacaklarında kalıp kapanışta gerekçe istemez (O3; F1c'nin
    iptal emsali). Kapanan satır silinmez, iz olarak kalır; gerekçeli sapmalara dokunulmaz."""
    yazma_kapisi()
    _baslangic(IPTAL_EDEN_ROLLER)
    metin = cancel_reason.strip()
    if not metin:
        raise ValueError(IPTAL_GEREKCESI_GEREKLI)
    guncel = _guncel(kurul)
    if guncel.status not in _IPTAL_EDILEBILIR:
        raise ValueError(DURUM_GECERSIZ)
    # Dönem IPTAL'e dönmeden önce (yeni okulda satırlar hazırlık dönemindedir).
    uyum.iptalde_eksikleri_kapat(
        kural_donemi(guncel), [guncel, *kurulun_duyurulari(guncel)], hazirlik_yazimi=True
    )
    hazirlik = guncel.opens_term
    onceki = denetim_izi.anlik(guncel)
    guncel.status = AssemblyStatus.IPTAL
    guncel.cancel_reason = metin
    _kaydet(guncel, onceki, ("status", "cancel_reason"))
    if hazirlik is not None and hazirlik.status == TermStatus.HAZIRLIK:
        donem_kilidi.yazma_denetimi(hazirlik, hazirlik_yazimi=True)
        onceki_donem = denetim_izi.anlik(hazirlik)
        hazirlik.status = TermStatus.IPTAL
        hazirlik.cancel_reason = HAZIRLIK_DONEMI_IPTAL_NEDENI
        hazirlik.updated_by_id = iz.yazar_hesabi()
        hazirlik.save(update_fields=["status", "cancel_reason", "updated_at", "updated_by"])
        denetim_izi.degisiklik(hazirlik, onceki=onceki_donem)
    return guncel
