"""Genel Bakış'ın pano kalemleri (tasarım §7.10 "Pano ve takvim"; plan F1c 12. adım "pano kabuğu").

KAYNAKLAR: kalemler SAKLANMAZ; her okumada (açılış, gün değişimi, ilgili kayıt yazıldıktan sonraki okuma)
kaynak kayıtlardan hesaplanır (tek kaynak, O6). Hesap okuma işidir: veritabanına hiçbir şey yazmaz,
kilitliyken de yazmaz (§4.6.3; uç kilitliyken 423 döner, hesap hiç koşmaz). Kalem gerekçe istemez:
vadesi geçen kuralın gerekçesi kendi akışındaki kapatıcı geçişte istenir (O3), kalem kayıt kapanınca
kendiliğinden düşer.

KİŞİSİZ: kalemde kişi adı, kişi ya da üyelik kimliği yoktur; yalnız kod, gün, kural paketinin kişisiz
iletisi, madde atfı ve götürdüğü ekran (rota + sekme). Kişi ancak kalemin götürdüğü ekranda, rolün okuma
yetkisi içinde görünür (§7.10; ailenin "bildirimde kişi adı yok" ilkesi, §12.A). Kullanıcı metni
(başlık, açıklama) ön yüzün sözlüğe bağlı metinleridir (`modules/pano/metinler.ts`); burada yalnız kural
paketinin iletisi döner.

F1c KALEMLERİ (§7.10 "Fazlar": pano kabuğu; F3-F6 kaynakları kalem üretmez, yer tutucu da çıkmaz; F2'nin
kalemleri aşağıda "F2 KALEMLERİ"nde):

* `YK_GOREV_BOLUMU` — yönetim kurulunun görev bölümü süresi (md. 12/3; `yonetim_kurulu.gorev_bolumu_gun`):
  kurulun bugünkü bileşimi oluştuktan sonra görev bölümü yapılmadıysa son gün başlangıç + kural değeri;
* `DK_GOREV_BOLUMU` — Denetleme Kurulunun görev bölümü (md. 14/1; `denetleme_kurulu.gorev_bolumu_gun`);
  başlangıç kurulu seçen genel kuruldur (`gorev_bolumu.dk_secen_genel_kurul_gunu`). İki kalemde de
  başlangıç ve "yapıldı mı" yazmadaki süre denetimiyle aynı kaynaktır
  (`gorev_bolumu.bekleyen_sure_baslangici`). Başlangıç programa başlama gününden önceyse kurul
  programdan önce oluşmuştur (devralınan kurul): geçmiş geriye dönük işletilmez (§7.9 "Ne olmaz"),
  kalem çıkmaz;
* `GECIS_ADIMI` — geçiş kurulumunun açık adımları (`gecis.yol_haritasi_durumu`; §7.9, §7.10);
* `KURAL_SURUMU` — kural sürümü güncellemesi (F2 2. adım; tasarım §7.10 "Kurulum yol haritası … kural sürümü
  seçimi", §6.2-5; plan F2 §6.3, §7 U2): programla açık dönemden daha yeni revizyon geldi
  (`kural_bagi.guncelleme_onerisi`); `ek` yalnız iki sürümü taşır (paket kimliği ve revizyon). Kalem geçiş
  yapılınca kendiliğinden düşer;
* `YEDEK_CAGRISI` — yönetim kurulunda görevdeki asıl sayısı kural paketindeki asıl üye sayısının altında
  ve çağrılmamış yedek varken (md. 13/6; ileti `yonetim_kurulu.asil_uye`'nin), Denetleme Kurulunda
  öğretmen üyenin başka kurumdaki görevlendirmesi kural süresini aştıysa
  (`uyelik_gecisleri.oneriler`, `denetleme_kurulu.ogretmen_gorevlendirme_ay`); aynı ileti ve atfı
  taşıyan öneriler tek kalemdir, `ek.sayi` kaç üyede olduğunu söyler (kişisiz sayım, §7.10);
* `KADRO` — kadro okumasının uyarı ve eksikleri (`uyelikler.kadro_uyarilari`: kadro sayıları, görev
  süresi, başkan eksiği); yedek çağrısı önerisine dönen asıl sayısı iletisi ayrıca yazılmaz;
* `HESAP_ONERISI` — program yöneticisinin hesap önerileri (`hesap_baglari.hesap_onerileri`; kişisiz
  kodlar: öneri türü, rol, neden; hesap ve üyelik kimliği dönmez); aynı tür, rol ve nedenli öneriler
  tek kalemdir, `ek.sayi` kaç öneri olduğunu söyler (ör. Denetleme Kurulunun üç asılına hesap
  açılmadıysa tek kalem, `sayi` 3; ilk görülme sırası korunur);
* `YARIM_TASLAK` — oturumdaki hesabın yarım kalan gerekçe metni (§7 "Yarım kalan metin"): yalnız kutunun
  bağlamı (metin okunmaz, şifresi çözülmez); bilinmeyen bağlam kalem üretmez (götüreceği ekran yok);
* `tamamlanacaklar` — açık dönemin açık `ComplianceItem(EKSIK)` satırları (O3), rolün görünümüyle; açık
  dönem yokken yeni açılan okulun ilk genel kurulunun hazırlık dönemindekiler (ilk genel kurulun kuralları
  ve satırları o dönemdedir, `genel_kurul.kural_donemi`; ilanın eksik kanalı, gündemin girilmemiş verisi)
  (`uyum.uyum_satiri_gorunumu`: görev alma engelinin kimliğini ve atfını yalnız program yöneticisi ve
  yönetim kurulu rolleri görür; kullanıcı kararı 10.11.2026);
* `bilgiler` — kural kopyası doğrulanamayan dönem (D7: kurallı kalemler çıkmaz, uç 503 vermez) ve açık
  birlik dönemi olmaması (hiç açılmadı ya da son dönem iptal edildi).

F2 KALEMLERİ ("genel kurul süreleri"; tasarım §7.10 "Fazlar", plan F2 §6.3 ve 12. adım). Kaynakları genel
kurul kayıtları, kural paketi ve `ComplianceItem(TAKVIM)` satırlarıdır; süreler ve sınırlar kural
paketinden okunur (D8; genel kurul kurallarının olay günü birinci toplantının günüdür, toplantı yoksa
bugün). Genel kurul kalemi genel kurulun ekranına götürür (`ek.kurul`: genel kurulun kimliği; kişi
kimliği değildir). Okunan genel kurullar açık dönemin genel kurulları ve yeni açılan okulun hazırlıktaki
ilk genel kuruludur; iptal edilen genel kurul kalem üretmez.

* `GK_OLAGAN` — olağan genel kurul (md. 9/1; `genel_kurul.olagan_son_ay`, S3: sınır birinci toplantının
  günüdür). Açık dönemin ders yılından sonraki ders yılı başladığı hâlde açık dönemin olağan genel kurulu
  planlanmadıysa `PLANLANMADI`: son gün, sınırdaki bir toplantının ilanının son günüdür (sınır −
  `genel_kurul.ilan_en_az_gun`; `ek.son_gun` toplantının son günü). Bu son gün iki kuraldan çıktığı için
  kalemin atfı ikisini birlikte taşır ("md. 9/1, 9/3"); ilan süresinin atfı ayrıca `ek.ilan_atif`'tedir
  (cümledeki "en az N gün önce ilan edilir"in dayanağı, md. 9/3); planlanmış ve henüz birinci toplantısı
  yapılmamış genel kurulun birinci toplantısı sınırı aşıyorsa `SINIRI_ASIYOR` (son gün sınırdır). Ders
  yılı tanımlı değilse kalem çıkmaz;
* `GK_YENI_OKUL` — yeni açılan okulun ilk genel kurulu (md. 9/1; `genel_kurul.yeni_okul_ay`): okul
  kartında açılış günü var ve birlik dönemi hiç açılmadıysa; aynı iki durumla (sınır açılış günü + kural
  değeri);
* `GK_ILAN` — ilan (md. 9/3; `genel_kurul.ilan_en_az_gun`, `genel_kurul.ilan_kanallari`): ilan edilmemiş
  genel kurulda (`PLANLANDI`, `CAGRILDI`) `ILAN_BEKLIYOR`, son gün birinci toplantı − kural değeri; ilanı
  yapılmış ve kanıtı hâlâ yazılabilen genel kurulda kanıt günü girilmemiş kanal varsa ilan başına
  `KANIT_EKSIK` (`ek.eksik` kanal belirteçleri, `ek.toplanti` ilanın toplantısı; son gün o toplantı −
  kural değeri; ikinci toplantının günü girilmemişse ikinci ilanın kalemi çıkmaz). Eksik kanal ayrıca
  "tamamlanacaklar"dadır (O3; satır genel kurulun ekranına götürür; yeni açılan okulda satır hazırlık
  dönemindedir, aşağıda "tamamlanacaklar");
* `GK_IKINCI_TOPLANTI` — birinci toplantıda yeter sayı sağlanamadı (`YETER_SAYI_YOK`): son gün birinci
  toplantı + `genel_kurul.ikinci_toplanti_en_gec_gun` (md. 9/2). md. 9/2 olağan genel kurulu düzenler;
  olağanüstü genel kurulda süre kullanıcı kararı A-1 ile uygulanır: atıf bunu söyler
  ("md. 9/2; kullanıcı kararı A-1 …", `ek.olaganustu` 1; plan F2 §7 U10, tasarım §6.1 "kullanıcı kararı
  atıfla görünür"). Tarihi ilk ilanda olmayan ikinci toplantının ilan süresinin atfı `ek.ilan_atif`'tedir;
* `MUDUR_YAZISI` — müdürün bekleyen yazısı (tasarım §7.10 mudur satırı "yeni okulda ve olağanüstüde
  E05"): yeni açılan okulun planlanmış ilk genel kurulunda çağrı (davet) kaydedilmedi
  (`YENI_OKUL_DAVETI`) ya da çağrının sahibi müdür olduğu hâlde çağrı yazısı (E05) üretilmedi
  (`CAGRI_YAZISI`); son gün ilanın son günüdür (çağrı ilandan önce gelir): birinci toplantı −
  `genel_kurul.ilan_en_az_gun`. Bu son gün iki kuraldan çıktığı için atıf ikisini birlikte taşır
  (yeni okulda "md. 9/1, 9/3", olağanüstüde "md. 9/6, 9/3"); ilan süresinin atfı ayrıca
  `ek.ilan_atif`'tedir (`GK_OLAGAN`'daki gibi). Çağıranı henüz belli olmayan planlanmış olağanüstü genel
  kurul müdüre kalem üretmez (en dar seçim);
* `IBRA_BILDIRIMI`, `TEFBIS_GIRISI` — açık ya da kapanıştaki dönemin yapılmamış (`done_on` boş) takvim
  satırları: ibra edilmedi bildirimi (md. 11/1-ç) ve okul idaresinin TEFBİS girişleri (md. 23/5; program
  TEFBİS'in yerine geçmez). İleti satırın kişisiz iletisidir. Kalem **süresizdir** (`vade` boş, gecikmez):
  iki yükümlülükte de mevzuatta süre yoktur (md. 11/1-ç "resmî yazıyla bildirilir", md. 23/5 "TEFBİS'e
  kaydeder"; TEFBİS'in "genel kuruldan hemen sonra"sı yalnız rehberde, tasarım §5.2.7 ve §7.1 [B]).
  Satırın `due_date`'i (genel kurulun yapıldığı gün; 6. adımın açık sorusu) yalnız sıralamadır, son gün
  diye gösterilmez. `ek.satir` takvim satırının kimliğidir (kişi kimliği değildir): satırın işini yapan rol
  "yapıldı" işaretini bu kalemden yazar (`uyum.takvim_satiri_yapildi`; tasarım §7.10 "kalemin kapanması:
  … `done_on` … alınca"); işaretlenen satır düşer. `ek.salt_okur`: satırın kendi döneminin kural kopyası
  tutmuyor (D7; uç işareti `donem_salt_okur` ile reddeder, karar aynı işlevden), ön yüz düğmeyi gizler.
  İbra edilmedi bildirimi yalnız genel kurulun güncel yönetim kurulu ibrası hâlâ "ibra edilmedi" iken
  görünür: tutanaktan sonraki katılım düzeltmesi sonucu "ibra edildi"ye çevirirse satır silinmez ve
  yapıldı sayılmaz (altın kural 4), yalnız panoda gizlenir; sonuç yeniden "ibra edilmedi" olursa aynı
  satır yeniden görünür (`genel_kurul._ibrayi_yeniden_yaz` yapılmamış satır varken yenisini yazmaz);
* `DONEM_ONAYI` — tutanağı tamamlanmış olağan genel kurulun hazırlık dönemi hâlâ onay bekliyor (plan F2
  §7 U32; süresiz; `ek.baslangic` dönemin başlangıcı, genel kurulun yapıldığı gün);
* `VERI_SORUMLUSU` — "tamamlanacaklar"da: okul kartında veri sorumlusu girilmediyse kişisel veri
  aydınlatma metni (E04) üretilmez (tasarım §9.6 E04; §7.10 "Kurulum yol haritası … `data_controller_text`").
  Okul Bilgileri'ne götürür; dönemden bağımsızdır.

Görev bölümü süresinin başlangıcı genel kurulun yapıldığı gündür (birinci ya da ikinci toplantı; U6):
`gorev_bolumu.bekleyen_sure_baslangici` bunu okur, kalem değişmez. Yeni açılan okulda (okul kartında açılış
günü var, geçiş kurulumu başlamadı) geçiş kurulumunun "İlk birlik dönemi girilmedi" adımı kalem olmaz: ilk
dönem ilk genel kurulla açılır (S5 (iii)); yerine `GK_YENI_OKUL` çıkar. "Kapanış bekleyen dönem" F4'tedir.

ROL BAŞINA GÖRÜNÜM (§7.10 tablosu ve §4.4.2; `KALEM_ROLLERI`): program yöneticisi bütün listeyi görür;
sekreter yönetim kurulunun görev bölümü süresini, yedek çağrısı önerisini ve kadrosunu; başkan ve başkan
yardımcısı yönetim kurulunun görev bölümü süresini; Denetleme Kurulu kendi görev bölümü süresini ve
kadrosunu. Geçiş adımları, kural sürümü güncellemesi, hesap önerileri ve Denetleme Kurulunun yedek
çağrısı (yedeği program yöneticisi çağırır, md. 14/6) yalnız program yöneticisinindir. F2 (plan §6.3
"Roller"): olağan genel kurul program yöneticisinde, sekreterde, başkanda, başkan yardımcısında ve müdürde
(md. 27/1 "zamanında yapılması"); ilan ve ikinci toplantı müdür dışındaki bu rollerde; yeni okulun ilk
genel kurulu program yöneticisinde ve müdürde; müdürün bekleyen yazısı yalnız müdürde; ibra edilmedi
bildirimi program yöneticisinde ve sekreterde; TEFBİS girişleri, dönem onayı ve veri sorumlusu yalnız
program yöneticisinde. Tamamlanacaklar (veri sorumlusu satırı dışında), bilgiler ve kendi yarım taslağı
her roldedir (M2 ve M1'i her rol okur; Organlar ekranının kadro okuması
aynı satırları aynı süzmeyle verir).
Veli rollerinde (başkan, başkan yardımcısı, muhasip, sekreter) varsayılan görünüm "bu ay sizden
beklenenler"dir (`gorunum: "ay"`), ötekilerde "bu hafta yapılacaklar" (`"hafta"`); ön yüz rol adıyla
dallanmaz, görünümü buradan okur.
"""

from __future__ import annotations

import calendar
from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any, Final

from django.db.models import Q
from django.utils import timezone

from apps.oab import selectors
from apps.oab.kurallar import (
    BilinmeyenKural,
    KuralPaketiKullanilamaz,
    YururlukteDegerYok,
    kural,
    kural_kaydi,
)
from apps.oab.kurallar.erisim import atif_metni
from apps.oab.kurallar.erisim import denetle as paket_denetle
from apps.oab.models import (
    AgendaItem,
    Announcement,
    AssemblyCaller,
    AssemblyKind,
    AssemblyStatus,
    BoardMeeting,
    ComplianceItem,
    ComplianceKind,
    ComplianceObligation,
    Discharge,
    DocumentStatus,
    DraftText,
    GeneralAssembly,
    GeneratedDocument,
    OabPerson,
    OabTerm,
    OfficialBook,
    OrganMembership,
    OrganType,
    SeatType,
    TermStatus,
)
from apps.oab.services import (
    donem_kilidi,
    gecis,
    genel_kurul,
    gorev_bolumu,
    hesap_baglari,
    kural_bagi,
    takvim,
    uyelik_gecisleri,
    uyelikler,
    uyum,
)
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AccountRole, SchoolConfig, SchoolYear

# ---------------------------------------------------------------------------
# Kalem kodları ve rolleri (modül başlığı "Rol başına görünüm")
# ---------------------------------------------------------------------------
YK_GOREV_BOLUMU: Final = "YK_GOREV_BOLUMU"
DK_GOREV_BOLUMU: Final = "DK_GOREV_BOLUMU"
GECIS_ADIMI: Final = "GECIS_ADIMI"
KURAL_SURUMU: Final = "KURAL_SURUMU"
YEDEK_CAGRISI_YK: Final = "YEDEK_CAGRISI_YK"
YEDEK_CAGRISI_DK: Final = "YEDEK_CAGRISI_DK"
KADRO_YK: Final = "KADRO_YK"
KADRO_DK: Final = "KADRO_DK"
HESAP_ONERISI: Final = "HESAP_ONERISI"
YARIM_TASLAK: Final = "YARIM_TASLAK"
# F2 (modül başlığı "F2 kalemleri").
GK_OLAGAN: Final = "GK_OLAGAN"
GK_YENI_OKUL: Final = "GK_YENI_OKUL"
GK_ILAN: Final = "GK_ILAN"
GK_IKINCI_TOPLANTI: Final = "GK_IKINCI_TOPLANTI"
MUDUR_YAZISI: Final = "MUDUR_YAZISI"
IBRA_BILDIRIMI: Final = "IBRA_BILDIRIMI"
TEFBIS_GIRISI: Final = "TEFBIS_GIRISI"
DONEM_ONAYI: Final = "DONEM_ONAYI"
#: Kalemin durumu (`ek.durum`): genel kurul planlanmadı ya da birinci toplantı sınırı aşıyor; ilan
#: bekliyor ya da ilanın kanıtı eksik; müdürün bekleyen yazısının türü (`ek.tur`).
PLANLANMADI: Final = "PLANLANMADI"
SINIRI_ASIYOR: Final = "SINIRI_ASIYOR"
ILAN_BEKLIYOR: Final = "ILAN_BEKLIYOR"
KANIT_EKSIK: Final = "KANIT_EKSIK"
YENI_OKUL_DAVETI: Final = "YENI_OKUL_DAVETI"
CAGRI_YAZISI: Final = "CAGRI_YAZISI"
#: İlanın toplantısı (`ek.toplanti`; `AssemblyMeeting` değerleri).
BIRINCI: Final = "BIRINCI"
IKINCI: Final = "IKINCI"
#: Yanıttaki kod (iki kurulun yedek çağrısı ve kadrosu aynı başlıkla, `ek.organ` ile ayrılır).
_YANIT_KODU: Final[dict[str, str]] = {
    YEDEK_CAGRISI_YK: "YEDEK_CAGRISI",
    YEDEK_CAGRISI_DK: "YEDEK_CAGRISI",
    KADRO_YK: "KADRO",
    KADRO_DK: "KADRO",
}
#: Tamamlanacak satırının kodu (O3 "eksik").
EKSIK: Final = "EKSIK"
#: Okul kartının tamamlanacak satırı: veri sorumlusu girilmedi (E04 üretilmez).
VERI_SORUMLUSU: Final = "VERI_SORUMLUSU"
#: Bilgi kodları.
KURAL_KOPYASI_DOGRULANAMADI: Final = "KURAL_KOPYASI_DOGRULANAMADI"
DONEM_YOK: Final = "DONEM_YOK"

_YONETICI: Final = rol_izinleri.YONETICI
_SEKRETER: Final = AccountRole.SEKRETER.value
_BASKAN: Final = AccountRole.BASKAN.value
_BASKAN_YARDIMCISI: Final = AccountRole.BASKAN_YARDIMCISI.value
_DK: Final = rol_izinleri.DENETLEME_KURULU
_MUDUR: Final = AccountRole.MUDUR.value
#: Genel kurul sürelerini gören roller (plan F2 §6.3; tasarım §7.10 sekreter, başkan ve başkan
#: yardımcısı satırları "genel kurul süreleri").
_GK_SURE_ROLLERI: Final = frozenset({_YONETICI, _SEKRETER, _BASKAN, _BASKAN_YARDIMCISI})

#: Kalemi gören roller (tasarım §7.10 "Rol başına görünüm"; program yöneticisi "bütün liste").
KALEM_ROLLERI: Final[dict[str, frozenset[str]]] = {
    YK_GOREV_BOLUMU: frozenset({_YONETICI, _BASKAN, _BASKAN_YARDIMCISI, _SEKRETER}),
    DK_GOREV_BOLUMU: frozenset({_YONETICI, _DK}),
    GECIS_ADIMI: frozenset({_YONETICI}),
    KURAL_SURUMU: frozenset({_YONETICI}),
    YEDEK_CAGRISI_YK: frozenset({_YONETICI, _SEKRETER}),
    YEDEK_CAGRISI_DK: frozenset({_YONETICI}),
    KADRO_YK: frozenset({_YONETICI, _SEKRETER}),
    KADRO_DK: frozenset({_YONETICI, _DK}),
    HESAP_ONERISI: frozenset({_YONETICI}),
    GK_OLAGAN: _GK_SURE_ROLLERI | {_MUDUR},
    GK_YENI_OKUL: frozenset({_YONETICI, _MUDUR}),
    GK_ILAN: _GK_SURE_ROLLERI,
    GK_IKINCI_TOPLANTI: _GK_SURE_ROLLERI,
    MUDUR_YAZISI: frozenset({_MUDUR}),
    IBRA_BILDIRIMI: frozenset({_YONETICI, _SEKRETER}),
    TEFBIS_GIRISI: frozenset({_YONETICI}),
    DONEM_ONAYI: frozenset({_YONETICI}),
}
#: Varsayılan görünümü "bu ay sizden beklenenler" olan veli rolleri (§7.10 "Teslim yolu").
AYLIK_GORUNUM_ROLLERI: Final = rol_izinleri.YK_ROLLERI

#: Yarım metin kutusunun bağlamı → götürdüğü ekran (rota, sekme). Bağlamlar ön yüzün kutularıdır
#: (`useUyariGerekce(baglam)`; F1c 11. adım); bu listede olmayan bağlam kalem üretmez. Yedek çağrısı
#: ve düşme pencereleri iki kurulda da açıldığı için bağlamları kurulludur (`.yk` / `.dk`): kalem
#: taslağın yazıldığı kurulun sekmesine götürür.
TASLAK_EKRANLARI: Final[dict[str, tuple[str, str]]] = {
    "gecis.devralinan": ("/birlik-donemi/gecis-kurulumu", ""),
    "gecis.karar_defteri": ("/birlik-donemi/gecis-kurulumu", ""),
    "gecis.sayac_beyani": ("/birlik-donemi/gecis-kurulumu", ""),
    "organlar.yk_gorev_bolumu": ("/organlar", "yk"),
    "organlar.yedek_cagrisi.yk": ("/organlar", "yk"),
    "organlar.yedek_cagrisi.dk": ("/organlar", "dk"),
    "organlar.dusme.yk": ("/organlar", "yk"),
    "organlar.dusme.dk": ("/organlar", "dk"),
    "organlar.dk_gorev_bolumu": ("/organlar", "dk"),
    "organlar.ogretmen_uye": ("/organlar", "dk"),
    "temsilciler.temsilci": ("/temsilciler", ""),
}

#: Kurulun Organlar sekmesi.
_ORGAN_SEKMESI: Final[dict[str, str]] = {
    OrganType.YONETIM_KURULU.value: "yk",
    OrganType.DENETLEME_KURULU.value: "dk",
    OrganType.ALIM_KOMISYONU.value: "alim",
}
_ORGANLAR: Final = "/organlar"
_TEMSILCILER: Final = "/temsilciler"
_BIRLIK_DONEMI: Final = "/birlik-donemi"
_GECIS_KURULUMU: Final = "/birlik-donemi/gecis-kurulumu"
_KULLANICILAR: Final = "/kullanicilar"
_GENEL_KURUL: Final = "/genel-kurul"
_AYARLAR: Final = "/ayarlar"
_OKUL_BILGILERI_SEKMESI: Final = "okul"

#: Birinci toplantısı henüz yapılmamış genel kurul (Ekim sonu ve açılıştan iki ay sınırı birinci
#: toplantının günüdür, S3).
_TOPLANMAMIS: Final = frozenset(
    {AssemblyStatus.PLANLANDI, AssemblyStatus.CAGRILDI, AssemblyStatus.ILAN_EDILDI}
)
#: İlanı yapılmamış genel kurul.
_ILAN_ONCESI: Final = frozenset({AssemblyStatus.PLANLANDI, AssemblyStatus.CAGRILDI})
#: İlanın kanıt günlerinin hâlâ yazılabildiği durumlar (`genel_kurul.ilan_kanitlarini_yaz`'ın kapısı;
#: tutanak tamamlanınca eksik kanal sapmaya döner).
_KANIT_YAZILABILIR: Final = frozenset(
    {AssemblyStatus.ILAN_EDILDI, AssemblyStatus.YETER_SAYI_YOK, AssemblyStatus.YAPILDI}
)
#: Takvim satırının yükümlülüğü → kalemin kodu (F2'nin satırları; öteki fazların yükümlülükleri
#: kendi fazlarında eklenir).
_TAKVIM_KODLARI: Final[dict[str, str]] = {
    ComplianceObligation.IBRA_EDILMEDI_BILDIRIMI: IBRA_BILDIRIMI,
    ComplianceObligation.TEFBIS_YONETIM_BILGISI: TEFBIS_GIRISI,
    ComplianceObligation.TEFBIS_BANKA_BILGISI: TEFBIS_GIRISI,
    ComplianceObligation.TEFBIS_BUTCE_GIRISI: TEFBIS_GIRISI,
}
#: Çağrı yazısının evrak kodu (genel kurul evrakı kataloğu; `genel_kurul_evraki.E05`).
_CAGRI_YAZISI_KODU: Final = "E05"

#: Yönetmelik maddesi atfının öneki (`erisim.atif_metni`; birleşik atıf için).
_MADDE_ONEKI: Final = "md. "
#: Olağanüstü genel kurulda ikinci toplantı süresinin atfına eklenen kullanıcı kararı (plan F2 §7 U10;
#: md. 9/2 olağan genel kurulu düzenler, olağanüstüde uygulanması kullanıcı kararı A-1'dir).
A1_ATIF_EKI: Final = "kullanıcı kararı A-1 (md. 9/2'nin olağanüstü genel kurulda uygulanması)"

#: Paket ya da dönem kopyası okunamayınca kurallı kalem çıkmaz (D1, D7); okuma açık kalır.
_KURAL_OKUNAMADI: Final = (KuralPaketiKullanilamaz, YururlukteDegerYok, BilinmeyenKural)


def bugun() -> date:
    """Kalemlerin günü (Europe/Istanbul); testler gün değişimini bununla sabitler."""
    return timezone.localdate()


def _kalem(
    kod: str,
    *,
    rota: str,
    sekme: str = "",
    vade: date | None = None,
    gun: date | None = None,
    metin: str = "",
    atif: str = "",
    **ek: Any,
) -> dict[str, Any]:
    return {
        "kod": _YANIT_KODU.get(kod, kod),
        "vade": None if vade is None else vade.isoformat(),
        "gecikti": vade is not None and gun is not None and gun > vade,
        "rota": rota,
        "sekme": sekme,
        "metin": metin,
        "atif": atif,
        "ek": ek,
    }


# ---------------------------------------------------------------------------
# Kurallı kalemler (kural paketinden; D7'de çıkmaz)
# ---------------------------------------------------------------------------
_SURE_KURALLARI: Final[dict[str, tuple[str, str]]] = {
    OrganType.YONETIM_KURULU.value: (YK_GOREV_BOLUMU, "yonetim_kurulu.gorev_bolumu_gun"),
    OrganType.DENETLEME_KURULU.value: (DK_GOREV_BOLUMU, "denetleme_kurulu.gorev_bolumu_gun"),
}


def _gorev_bolumu_kalemi(donem: OabTerm, organ: str, gun: date) -> dict[str, Any] | None:
    """Görev bölümü süresi (modül başlığı): son gün = başlangıç + kural değeri (gün; yorum KE-12)."""
    kod, kural_id = _SURE_KURALLARI[organ]
    baslangic = gorev_bolumu.bekleyen_sure_baslangici(donem, organ, gun)
    program_basi = donem.program_start_date or donem.start_date
    if baslangic is None or (program_basi is not None and baslangic < program_basi):
        return None
    kayit = kural_kaydi(kural_id, tarih=baslangic, donem=donem)
    vade = baslangic + timedelta(days=int(kayit["deger"]))
    return _kalem(
        kod,
        rota=_ORGANLAR,
        sekme=_ORGAN_SEKMESI[organ],
        vade=vade,
        gun=gun,
        atif=atif_metni(kayit),
    )


def _yk_yedek_ve_kadro(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Yönetim kurulunun yedek çağrısı önerisi ve kadro kalemleri (modül başlığı)."""
    sonuclar: list[tuple[str, dict[str, Any]]] = []
    organ = OrganType.YONETIM_KURULU.value
    sayilar = selectors.kadro_sayilari(donem, organ)
    yedek_iletisi = ""
    if sayilar[SeatType.ASIL] < int(
        kural("yonetim_kurulu.asil_uye", gun, donem)
    ) and selectors.bekleyen_yedekler(donem, organ):
        sonuc = paket_denetle(
            "yonetim_kurulu.asil_uye", sayilar[SeatType.ASIL], tarih=gun, donem=donem
        )
        if sonuc["durum"] == "uyari":
            yedek_iletisi = sonuc["mesaj"]
            cagri = kural_kaydi("yonetim_kurulu.yedek_cagirma", tarih=gun, donem=donem)
            sonuclar.append(
                (
                    YEDEK_CAGRISI_YK,
                    _kalem(
                        YEDEK_CAGRISI_YK,
                        rota=_ORGANLAR,
                        sekme="yk",
                        metin=yedek_iletisi,
                        atif=atif_metni(cagri),
                        organ=organ,
                    ),
                )
            )
    for sonuc in uyelikler.kadro_uyarilari(donem, organ, tarih=gun):
        if sonuc["mesaj"] == yedek_iletisi:
            continue
        sonuclar.append(
            (
                KADRO_YK,
                _kalem(
                    KADRO_YK,
                    rota=_ORGANLAR,
                    sekme="yk",
                    metin=sonuc["mesaj"],
                    atif=sonuc["atif"],
                    organ=organ,
                    durum=sonuc["durum"],
                ),
            )
        )
    return sonuclar


def _dk_yedek_cagrilari(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Denetleme Kurulunun yedek çağrısı önerisi: öğretmen üyenin görevlendirmesi kural süresini aştı.
    Aynı ileti ve atıf tek kalemdir; `sayi` kaç üyede olduğudur (kişisiz; ilk görülme sırası)."""
    organ = OrganType.DENETLEME_KURULU.value
    gruplar: dict[tuple[str, str], int] = {}
    for uyelik in selectors.gorevdeki_asillar(donem, organ):
        sonuc = uyelik_gecisleri.gorevlendirme_denetimi(uyelik)
        if sonuc is not None:
            anahtar = (str(sonuc["mesaj"]), str(sonuc["atif"]))
            gruplar[anahtar] = gruplar.get(anahtar, 0) + 1
    return [
        (
            YEDEK_CAGRISI_DK,
            _kalem(
                YEDEK_CAGRISI_DK,
                rota=_ORGANLAR,
                sekme="dk",
                metin=metin,
                atif=atif,
                organ=organ,
                sayi=sayi,
            ),
        )
        for (metin, atif), sayi in gruplar.items()
    ]


def _dk_kadro(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Denetleme Kurulunun kadro kalemleri."""
    organ = OrganType.DENETLEME_KURULU.value
    return [
        (
            KADRO_DK,
            _kalem(
                KADRO_DK,
                rota=_ORGANLAR,
                sekme="dk",
                metin=sonuc["mesaj"],
                atif=sonuc["atif"],
                organ=organ,
                durum=sonuc["durum"],
            ),
        )
        for sonuc in uyelikler.kadro_uyarilari(donem, organ, tarih=gun)
    ]


def _gorev_bolumu_kalemleri(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    sonuclar: list[tuple[str, dict[str, Any]]] = []
    for organ, (kod, _) in _SURE_KURALLARI.items():
        kalem = _gorev_bolumu_kalemi(donem, organ, gun)
        if kalem is not None:
            sonuclar.append((kod, kalem))
    return sonuclar


def _kuralli_kalemler(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Kural paketinden okunan kalemler. Her kaynak ayrı okunur: paket ya da dönem kopyası okunamazsa
    (D1, D7) ya da kuralın olay gününde yürürlükte değeri yoksa o kaynağın kalemi çıkmaz; öteki
    kaynaklar ve kuralsız kalemler çalışır (okuma açık kalır, uç 503 vermez)."""
    sonuclar: list[tuple[str, dict[str, Any]]] = []
    for kaynak in (_gorev_bolumu_kalemleri, _yk_yedek_ve_kadro, _dk_yedek_cagrilari, _dk_kadro):
        try:
            sonuclar.extend(kaynak(donem, gun))
        except _KURAL_OKUNAMADI:
            continue
    return sonuclar


# ---------------------------------------------------------------------------
# F2: genel kurul süreleri (modül başlığı "F2 kalemleri"; kurallı, D7'de o kaynağın kalemi çıkmaz)
# ---------------------------------------------------------------------------
def _ayin_son_gunu(yil_basi: date, ay: int) -> date:
    """Ders yılının başladığı takvim yılından sayılan `ay`ın son günü (`genel_kurul.olagan_son_ay`,
    birim `takvim_ayi`: Ekim 10, ertesi yılın Ocak'ı 13; `genel_kurul.ders_yili_ayi`'nin tersi)."""
    yil = yil_basi.year + (ay - 1) // takvim.YILDAKI_AY
    ay_sirasi = (ay - 1) % takvim.YILDAKI_AY + 1
    return date(yil, ay_sirasi, calendar.monthrange(yil, ay_sirasi)[1])


def _birlesik_atif(*atiflar: str) -> str:
    """Bir sonucun birden çok kuraldan çıktığı kalemin atfı: Yönetmelik maddeleri tek "md."yle
    ("md. 9/1, 9/3"), öteki atıflar noktalı virgülle; yinelenen atıf bir kez."""
    tekil = [a for a in dict.fromkeys(atiflar) if a]
    if tekil and all(a.startswith(_MADDE_ONEKI) for a in tekil):
        return _MADDE_ONEKI + ", ".join(a.removeprefix(_MADDE_ONEKI) for a in tekil)
    return "; ".join(tekil)


def _gk_kalemi(
    kod: str, kurul: GeneralAssembly | None, *, vade: date | None, gun: date, atif: str, **ek: Any
) -> dict[str, Any]:
    """Genel kurul kalemi: genel kurulun ekranına götürür (varsa `ek.kurul` ile ayrıntısına)."""
    if kurul is not None:
        ek["kurul"] = kurul.pk
    return _kalem(kod, rota=_GENEL_KURUL, vade=vade, gun=gun, atif=atif, **ek)


def _olagan_genel_kurul_kalemi(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Olağan genel kurul planlanmadı ya da birinci toplantı sınırı aşıyor (modül başlığı `GK_OLAGAN`)."""
    kurul: GeneralAssembly | None = (
        GeneralAssembly.objects.select_related("opens_term__school_year")
        .filter(term=donem, kind=AssemblyKind.OLAGAN)
        .exclude(status=AssemblyStatus.IPTAL)
        .order_by("-pk")
        .first()
    )
    if kurul is not None:
        if (
            kurul.status not in _TOPLANMAMIS
            or kurul.first_meeting_at is None
            or kurul.opens_term is None
        ):
            return []
        birinci = genel_kurul.birinci_toplanti_gunu(kurul)
        kayit = kural_kaydi("genel_kurul.olagan_son_ay", tarih=birinci, donem=donem)
        son_gun = _ayin_son_gunu(kurul.opens_term.school_year.start_date, int(kayit["deger"]))
        if birinci <= son_gun:
            return []
        return [
            (
                GK_OLAGAN,
                _gk_kalemi(
                    GK_OLAGAN,
                    kurul,
                    vade=son_gun,
                    gun=gun,
                    atif=atif_metni(kayit),
                    durum=SINIRI_ASIYOR,
                    son_gun=son_gun.isoformat(),
                ),
            )
        ]
    # Açık dönemin ders yılından sonra başlamış ders yılı: bu yılın olağan genel kurulu (U5).
    yil: SchoolYear | None = (
        SchoolYear.objects.filter(start_date__lte=gun, start_date__gt=donem.school_year.start_date)
        .order_by("-start_date")
        .first()
    )
    if yil is None:
        return []
    kayit = kural_kaydi("genel_kurul.olagan_son_ay", tarih=gun, donem=donem)
    son_gun = _ayin_son_gunu(yil.start_date, int(kayit["deger"]))
    ilan = kural_kaydi("genel_kurul.ilan_en_az_gun", tarih=gun, donem=donem)
    ilan_gun = int(ilan["deger"])
    return [
        (
            GK_OLAGAN,
            _gk_kalemi(
                GK_OLAGAN,
                None,
                vade=son_gun - timedelta(days=ilan_gun),
                gun=gun,
                atif=_birlesik_atif(atif_metni(kayit), atif_metni(ilan)),
                durum=PLANLANMADI,
                son_gun=son_gun.isoformat(),
                ilan_gun=ilan_gun,
                ilan_atif=atif_metni(ilan),
            ),
        )
    ]


def _acilis_gunu() -> date | None:
    """Okul kartındaki açılış günü (yeni açılan okul; md. 9/1); okul kartı yoksa `None`."""
    gunu: date | None = (
        SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK)
        .values_list("opened_on", flat=True)
        .first()
    )
    return gunu


def _yeni_okul_kalemi(gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Yeni açılan okulun ilk genel kurulu (modül başlığı `GK_YENI_OKUL`)."""
    acilis = _acilis_gunu()
    if (
        acilis is None
        or OabTerm.objects.filter(
            status__in=(TermStatus.ACIK, TermStatus.KAPANISTA, TermStatus.KAPANDI)
        ).exists()
    ):
        return []
    kurul: GeneralAssembly | None = (
        GeneralAssembly.objects.select_related("opens_term__rule_package")
        .filter(term__isnull=True, kind=AssemblyKind.OLAGAN)
        .exclude(status=AssemblyStatus.IPTAL)
        .order_by("-pk")
        .first()
    )
    if kurul is not None:
        if (
            kurul.status not in _TOPLANMAMIS
            or kurul.first_meeting_at is None
            or kurul.opens_term is None
        ):
            return []
        birinci = genel_kurul.birinci_toplanti_gunu(kurul)
        kayit = kural_kaydi("genel_kurul.yeni_okul_ay", tarih=birinci, donem=kurul.opens_term)
        son_gun = takvim.ay_ekle(acilis, int(kayit["deger"]))
        if birinci <= son_gun:
            return []
        return [
            (
                GK_YENI_OKUL,
                _gk_kalemi(
                    GK_YENI_OKUL,
                    kurul,
                    vade=son_gun,
                    gun=gun,
                    atif=atif_metni(kayit),
                    durum=SINIRI_ASIYOR,
                    son_gun=son_gun.isoformat(),
                ),
            )
        ]
    # Dönemsiz okuma: dağıtılan en yeni kural sürümü (hazırlık dönemi planlamada ona bağlanır, U2).
    kayit = kural_kaydi("genel_kurul.yeni_okul_ay", tarih=gun)
    son_gun = takvim.ay_ekle(acilis, int(kayit["deger"]))
    ilan = kural_kaydi("genel_kurul.ilan_en_az_gun", tarih=gun)
    ilan_gun = int(ilan["deger"])
    return [
        (
            GK_YENI_OKUL,
            _gk_kalemi(
                GK_YENI_OKUL,
                None,
                vade=son_gun - timedelta(days=ilan_gun),
                gun=gun,
                atif=_birlesik_atif(atif_metni(kayit), atif_metni(ilan)),
                durum=PLANLANMADI,
                son_gun=son_gun.isoformat(),
                ilan_gun=ilan_gun,
                ilan_atif=atif_metni(ilan),
            ),
        )
    ]


def _suren_genel_kurullar() -> list[GeneralAssembly]:
    """Kalem üretebilen genel kurullar (modül başlığı): açık dönemin ve yeni açılan okulun hazırlıktaki
    ilk genel kurulu; iptal edilen çıkar. Tutanağı tamamlanmış genel kurul yalnız dönem onayı için
    okunur."""
    return list(
        GeneralAssembly.objects.select_related("term__rule_package", "opens_term__rule_package")
        .filter(
            Q(term__status=TermStatus.ACIK)
            | Q(term__isnull=True, opens_term__status=TermStatus.HAZIRLIK)
        )
        .exclude(status=AssemblyStatus.IPTAL)
        .order_by("pk")
    )


def _ilan_kalemleri(kurul: GeneralAssembly, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """İlanın son günü ve eksik kanal kanıtı (modül başlığı `GK_ILAN`)."""
    if kurul.first_meeting_at is None:
        return []
    donem = genel_kurul.kural_donemi(kurul)
    birinci = genel_kurul.birinci_toplanti_gunu(kurul)
    kayit = kural_kaydi("genel_kurul.ilan_en_az_gun", tarih=birinci, donem=donem)
    ilan_gun = int(kayit["deger"])
    atif = atif_metni(kayit)
    if kurul.status in _ILAN_ONCESI:
        return [
            (
                GK_ILAN,
                _gk_kalemi(
                    GK_ILAN,
                    kurul,
                    vade=birinci - timedelta(days=ilan_gun),
                    gun=gun,
                    atif=atif,
                    durum=ILAN_BEKLIYOR,
                    toplanti=BIRINCI,
                    ilan_gun=ilan_gun,
                ),
            )
        ]
    if kurul.status not in _KANIT_YAZILABILIR:
        return []
    gerekli = [str(k) for k in kural("genel_kurul.ilan_kanallari", birinci, donem)]
    sonuclar: list[tuple[str, dict[str, Any]]] = []
    for sira, duyuru in enumerate(genel_kurul.kurulun_duyurulari(kurul)):
        toplanti_gunu = (
            birinci
            if sira == 0
            else (
                None
                if kurul.second_meeting_at is None
                else genel_kurul.yerel_gun(kurul.second_meeting_at)
            )
        )
        if toplanti_gunu is None:
            continue
        girilen = genel_kurul.IlanKanallari(
            distributed_written_on=duyuru.distributed_written_on,
            posted_board_on=duyuru.posted_board_on,
            published_web_on=duyuru.published_web_on,
        ).girilenler()
        eksik = [k for k in gerekli if k not in girilen]
        if not eksik:
            continue
        sonuclar.append(
            (
                GK_ILAN,
                _gk_kalemi(
                    GK_ILAN,
                    kurul,
                    vade=toplanti_gunu - timedelta(days=ilan_gun),
                    gun=gun,
                    atif=atif,
                    durum=KANIT_EKSIK,
                    toplanti=BIRINCI if sira == 0 else IKINCI,
                    eksik=",".join(eksik),
                ),
            )
        )
    return sonuclar


def _ikinci_toplanti_kalemi(kurul: GeneralAssembly, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Yeter sayı sağlanamadı: ikinci toplantının son günü (modül başlığı `GK_IKINCI_TOPLANTI`)."""
    if kurul.status != AssemblyStatus.YETER_SAYI_YOK or kurul.first_meeting_at is None:
        return []
    donem = genel_kurul.kural_donemi(kurul)
    birinci = genel_kurul.birinci_toplanti_gunu(kurul)
    kayit = kural_kaydi("genel_kurul.ikinci_toplanti_en_gec_gun", tarih=birinci, donem=donem)
    sure_gun = int(kayit["deger"])
    ilan = kural_kaydi("genel_kurul.ilan_en_az_gun", tarih=birinci, donem=donem)
    olaganustu = kurul.kind == AssemblyKind.OLAGANUSTU
    atif = atif_metni(kayit)
    return [
        (
            GK_IKINCI_TOPLANTI,
            _gk_kalemi(
                GK_IKINCI_TOPLANTI,
                kurul,
                vade=birinci + timedelta(days=sure_gun),
                gun=gun,
                atif=f"{atif}; {A1_ATIF_EKI}" if olaganustu else atif,
                sure_gun=sure_gun,
                ilan_gun=int(ilan["deger"]),
                ilan_atif=atif_metni(ilan),
                tarihli=int(kurul.second_meeting_at is not None),
                olaganustu=int(olaganustu),
            ),
        )
    ]


def _cagri_yazisi_uretildi(kurul: GeneralAssembly) -> bool:
    """Genel kurulun geçerli çağrı yazısı (E05) var mı (yalnız varlığı okunur)."""
    return GeneratedDocument.objects.filter(
        doc_type=_CAGRI_YAZISI_KODU,
        subject_type=denetim_izi.model_etiketi(GeneralAssembly),
        subject_id=denetim_izi.kimlik_metni(GeneralAssembly, kurul.pk),
        status=DocumentStatus.GECERLI,
    ).exists()


def _mudur_yazisi_kalemi(kurul: GeneralAssembly, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Müdürün bekleyen yazısı (modül başlığı `MUDUR_YAZISI`)."""
    if kurul.first_meeting_at is None:
        return []
    if (
        kurul.status == AssemblyStatus.PLANLANDI
        and kurul.called_by == AssemblyCaller.MUDUR_YENI_OKUL
    ):
        tur = YENI_OKUL_DAVETI
    elif (
        kurul.status == AssemblyStatus.CAGRILDI
        and genel_kurul.cagri_sahibi(kurul) == _MUDUR
        and not _cagri_yazisi_uretildi(kurul)
    ):
        tur = CAGRI_YAZISI
    else:
        return []
    donem = genel_kurul.kural_donemi(kurul)
    birinci = genel_kurul.birinci_toplanti_gunu(kurul)
    ilan = kural_kaydi("genel_kurul.ilan_en_az_gun", tarih=birinci, donem=donem)
    ilan_gun = int(ilan["deger"])
    if kurul.kind == AssemblyKind.OLAGAN:
        dayanak = kural_kaydi("genel_kurul.yeni_okul_ay", tarih=birinci, donem=donem)
    else:
        dayanak = kural_kaydi("genel_kurul.olaganustu_cagiranlar", tarih=birinci, donem=donem)
    return [
        (
            MUDUR_YAZISI,
            _gk_kalemi(
                MUDUR_YAZISI,
                kurul,
                vade=birinci - timedelta(days=ilan_gun),
                gun=gun,
                atif=_birlesik_atif(atif_metni(dayanak), atif_metni(ilan)),
                tur=tur,
                ilan_gun=ilan_gun,
                ilan_atif=atif_metni(ilan),
            ),
        )
    ]


def _donem_onayi_kalemi(kurul: GeneralAssembly, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Yeni birlik döneminin açılışı onay bekliyor (U32; süresiz, kuralsız)."""
    hazirlik = kurul.opens_term
    if (
        kurul.status != AssemblyStatus.TUTANAK_TAMAM
        or hazirlik is None
        or hazirlik.status != TermStatus.HAZIRLIK
    ):
        return []
    baslangic = selectors.genel_kurul_gunu(kurul)
    return [
        (
            DONEM_ONAYI,
            _gk_kalemi(
                DONEM_ONAYI,
                kurul,
                vade=None,
                gun=gun,
                atif="",
                baslangic="" if baslangic is None else baslangic.isoformat(),
            ),
        )
    ]


def _genel_kurul_kalemleri(donem: OabTerm | None, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """F2 kalemleri. Her kaynak (ve her genel kurulun her kaynağı) ayrı okunur: kural okunamazsa (D1,
    D7, olay gününde değer yok, kopyada kural yok) yalnız o kalem düşer."""
    sonuclar: list[tuple[str, dict[str, Any]]] = []
    if donem is not None:
        try:
            sonuclar.extend(_olagan_genel_kurul_kalemi(donem, gun))
        except _KURAL_OKUNAMADI:
            pass
    try:
        sonuclar.extend(_yeni_okul_kalemi(gun))
    except _KURAL_OKUNAMADI:
        pass
    for kurul in _suren_genel_kurullar():
        for kaynak in (
            _ilan_kalemleri,
            _ikinci_toplanti_kalemi,
            _mudur_yazisi_kalemi,
            _donem_onayi_kalemi,
        ):
            try:
                sonuclar.extend(kaynak(kurul, gun))
            except _KURAL_OKUNAMADI:
                continue
    return sonuclar


def _ibrasi_edilmis_kurullar(satirlar: list[ComplianceItem], kurul_turu: str) -> set[int]:
    """İbra edilmedi bildirimi satırlarının genel kurullarından güncel yönetim kurulu ibrası artık
    "ibra edilmedi" olmayanlar (tutanaktan sonraki katılım düzeltmesi; modül başlığı `IBRA_BILDIRIMI`)."""
    kimlikler = _sayilar(
        s.subject_id
        for s in satirlar
        if s.obligation == ComplianceObligation.IBRA_EDILMEDI_BILDIRIMI
        and s.subject_type == kurul_turu
    )
    if not kimlikler:
        return set()
    return set(
        GeneralAssembly.objects.filter(pk__in=kimlikler)
        .exclude(discharge_yk=Discharge.EDILMEDI)
        .values_list("pk", flat=True)
    )


def _takvim_kalemleri() -> list[tuple[str, dict[str, Any]]]:
    """Açık ya da kapanıştaki dönemin yapılmamış takvim satırları (`IBRA_BILDIRIMI`, `TEFBIS_GIRISI`).
    İleti satırın kişisiz iletisidir (madde atfı içinde); konu genel kurulsa genel kurula götürür. Kalem
    süresizdir (modül başlığı: mevzuatta süre yok); satırın `due_date`'i yalnız sıralamadır. İbra
    edilmedi bildirimi, genel kurulun güncel yönetim kurulu ibrası "ibra edilmedi" değilse çıkmaz (satır
    silinmez; modül başlığı). `ek.salt_okur` satırın kendi dönemine göredir (açık ya da kapanıştaki)."""
    kurul_turu = denetim_izi.model_etiketi(GeneralAssembly)
    satirlar = list(
        ComplianceItem.objects.select_related("term__rule_package")
        .filter(
            kind=ComplianceKind.TAKVIM,
            done_on__isnull=True,
            obligation__in=list(_TAKVIM_KODLARI),
            term__status__in=(TermStatus.ACIK, TermStatus.KAPANISTA),
        )
        .order_by("due_date", "pk")
    )
    ibrasi_edilmis = _ibrasi_edilmis_kurullar(satirlar, kurul_turu)
    sonuclar: list[tuple[str, dict[str, Any]]] = []
    for satir in satirlar:
        kod = _TAKVIM_KODLARI[satir.obligation]
        ek: dict[str, Any] = {
            "yukumluluk": str(satir.obligation),
            "satir": satir.pk,
            # Satırın kendi döneminin kural kopyası tutmuyorsa (D7) uç "yapıldı" işaretini
            # `donem_salt_okur` ile reddeder; karar aynı işlevden (`donem_kilidi.kural_kopyasi_tutuyor`).
            "salt_okur": not donem_kilidi.kural_kopyasi_tutuyor(satir.term),
        }
        if satir.subject_type == kurul_turu and satir.subject_id.isdigit():
            ek["kurul"] = int(satir.subject_id)
            if (
                satir.obligation == ComplianceObligation.IBRA_EDILMEDI_BILDIRIMI
                and ek["kurul"] in ibrasi_edilmis
            ):
                continue
        sonuclar.append(
            (
                kod,
                _kalem(kod, rota=_GENEL_KURUL, metin=satir.message, **ek),
            )
        )
    return sonuclar


# ---------------------------------------------------------------------------
# Kuralsız kalemler
# ---------------------------------------------------------------------------
def _gecis_kalemleri() -> list[dict[str, Any]]:
    """Geçiş kurulumunun açık adımları (sırasıyla; kişisiz adım anahtarları). Yeni açılan okulda geçiş
    başlamadıysa adım kalemi yoktur: ilk dönem ilk genel kurulla açılır (S5 (iii); `GK_YENI_OKUL`)."""
    durum = gecis.yol_haritasi_durumu()
    if durum["state"] == gecis.DURUM_BASLAMADI and _acilis_gunu() is not None:
        return []
    return [_kalem(GECIS_ADIMI, rota=_GECIS_KURULUMU, adim=adim) for adim in durum["open_steps"]]


def _kural_surumu_kalemi() -> dict[str, Any] | None:
    """Kural sürümü güncellemesi önerisi (kişisiz; götürdüğü ekran Birlik Dönemi)."""
    oneri = kural_bagi.guncelleme_onerisi()
    if oneri is None:
        return None
    return _kalem(
        KURAL_SURUMU,
        rota=_BIRLIK_DONEMI,
        bagli_paket=oneri["bagli"]["paket"],
        bagli_rev=oneri["bagli"]["rev"],
        yeni_paket=oneri["en_yeni"]["paket"],
        yeni_rev=oneri["en_yeni"]["rev"],
    )


def _hesap_kalemleri() -> list[dict[str, Any]]:
    """Program yöneticisinin hesap önerileri: yalnız tür, rol, neden ve sayı (kimlik dönmez). Aynı tür,
    rol ve nedenli öneriler tek kalemdir (ilk görülme sırası; aynı adlı bağlantılar yinelenmez)."""
    gruplar: dict[tuple[str, str, str], int] = {}
    for oneri in hesap_baglari.hesap_onerileri():
        anahtar = (str(oneri["tur"]), str(oneri["rol"]), str(oneri.get("neden", "")))
        gruplar[anahtar] = gruplar.get(anahtar, 0) + 1
    return [
        _kalem(HESAP_ONERISI, rota=_KULLANICILAR, tur=tur, rol=rol, neden=neden, sayi=sayi)
        for (tur, rol, neden), sayi in gruplar.items()
    ]


def _taslak_kalemi(hesap_id: str | None) -> dict[str, Any] | None:
    """Oturumdaki hesabın yarım metni: yalnız bağlam okunur (şifreli metin çözülmez)."""
    if hesap_id is None:
        return None
    baglam = DraftText.objects.filter(account_id=hesap_id).values_list("context", flat=True).first()
    if baglam is None or baglam not in TASLAK_EKRANLARI:
        return None
    rota, sekme = TASLAK_EKRANLARI[baglam]
    return _kalem(YARIM_TASLAK, rota=rota, sekme=sekme, baglam=baglam)


# ---------------------------------------------------------------------------
# Tamamlanacaklar (ComplianceItem EKSIK)
# ---------------------------------------------------------------------------
def _sayilar(kimlikler: Iterable[str]) -> list[int]:
    return [int(k) for k in kimlikler if k.isdigit()]


def _konu_organlari(satirlar: list[ComplianceItem]) -> dict[str, dict[str, str]]:
    """Üyelik ve toplantı konulu satırların kurulu (kimlik → organ; ekranın sekmesi için)."""
    uyelik = denetim_izi.model_etiketi(OrganMembership)
    toplanti = denetim_izi.model_etiketi(BoardMeeting)
    uyelikler_ = OrganMembership.objects.filter(
        pk__in=_sayilar(s.subject_id for s in satirlar if s.subject_type == uyelik)
    ).values_list("pk", "organ")
    toplantilar = BoardMeeting.objects.filter(
        pk__in=_sayilar(s.subject_id for s in satirlar if s.subject_type == toplanti)
    ).values_list("pk", "organ")
    return {
        uyelik: {str(pk): str(organ) for pk, organ in uyelikler_},
        toplanti: {str(pk): str(organ) for pk, organ in toplantilar},
    }


def _konu_kurullari(satirlar: list[ComplianceItem]) -> dict[tuple[str, str], int]:
    """Genel kurul, ilanı ve gündem maddesi konulu satırların genel kurulu ((tür, kimlik) → genel kurul
    kimliği; satır genel kurulun ekranına götürür, F2 12. adım)."""
    kurul_turu = denetim_izi.model_etiketi(GeneralAssembly)
    duyuru_turu = denetim_izi.model_etiketi(Announcement)
    madde_turu = denetim_izi.model_etiketi(AgendaItem)
    sonuc: dict[tuple[str, str], int] = {
        (kurul_turu, s.subject_id): int(s.subject_id)
        for s in satirlar
        if s.subject_type == kurul_turu and s.subject_id.isdigit()
    }
    duyurular = Announcement.objects.filter(
        pk__in=_sayilar(s.subject_id for s in satirlar if s.subject_type == duyuru_turu),
        subject_type=kurul_turu,
    ).values_list("pk", "subject_id")
    for pk, konu in duyurular:
        if str(konu).isdigit():
            sonuc[(duyuru_turu, str(pk))] = int(konu)
    maddeler = AgendaItem.objects.filter(
        pk__in=_sayilar(s.subject_id for s in satirlar if s.subject_type == madde_turu)
    ).values_list("pk", "assembly_id")
    for pk, kurul_id in maddeler:
        sonuc[(madde_turu, str(pk))] = int(kurul_id)
    return sonuc


def _eksik_ekrani(satir: ComplianceItem, organlar: dict[str, dict[str, str]]) -> tuple[str, str]:
    """Satırın götürdüğü ekran: konusunun ekranı (organ sekmesi, temsilciler, kişiler, geçiş)."""
    if satir.rule_id.startswith("temsilci."):
        return _TEMSILCILER, ""
    organ = organlar.get(satir.subject_type, {}).get(satir.subject_id)
    if organ is not None:
        if organ == OrganType.TEMSILCI:
            return _TEMSILCILER, ""
        return _ORGANLAR, _ORGAN_SEKMESI.get(organ, "")
    if satir.subject_type == denetim_izi.model_etiketi(OabPerson):
        return "/kisiler", "birlik"
    if satir.subject_type == denetim_izi.model_etiketi(OfficialBook):
        return _GECIS_KURULUMU, ""
    return _BIRLIK_DONEMI, ""


def _uyum_atfi(kural_id: str, donem: OabTerm, gun: date) -> str:
    try:
        return atif_metni(kural_kaydi(kural_id, tarih=gun, donem=donem))
    except _KURAL_OKUNAMADI:
        return ""


def _tamamlanacaklar(donem: OabTerm, rol: str | None, gun: date) -> list[dict[str, Any]]:
    satirlar = list(
        ComplianceItem.objects.filter(
            term=donem, kind=ComplianceKind.EKSIK, resolved_at__isnull=True
        ).order_by("pk")
    )
    organlar = _konu_organlari(satirlar)
    kurullar = _konu_kurullari(satirlar)
    sonuc: list[dict[str, Any]] = []
    for satir in satirlar:
        gorunum = uyum.uyum_satiri_gorunumu(satir, rol)
        kurul = kurullar.get((satir.subject_type, satir.subject_id))
        ek: dict[str, Any] = {}
        if kurul is not None:
            rota, sekme = _GENEL_KURUL, ""
            ek["kurul"] = kurul
        else:
            rota, sekme = _eksik_ekrani(satir, organlar)
        sonuc.append(
            _kalem(
                EKSIK,
                rota=rota,
                sekme=sekme,
                metin=str(gorunum["message"]),
                atif=_uyum_atfi(str(gorunum["rule_id"]), donem, gun),
                **ek,
            )
        )
    return sonuc


def _okul_karti_tamamlanacaklari(rol: str | None) -> list[dict[str, Any]]:
    """Okul kartının tamamlanacakları (yalnız program yöneticisi; okul kartını o yazar): veri sorumlusu
    girilmediyse E04 üretilmez (modül başlığı `VERI_SORUMLUSU`). Dönemden bağımsızdır."""
    if rol != _YONETICI:
        return []
    metin = (
        SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK)
        .values_list("data_controller_text", flat=True)
        .first()
    )
    if metin and metin.strip():
        return []
    return [_kalem(VERI_SORUMLUSU, rota=_AYARLAR, sekme=_OKUL_BILGILERI_SEKMESI)]


# ---------------------------------------------------------------------------
# Bilgiler ve toplu okuma
# ---------------------------------------------------------------------------
def _acik_donem() -> OabTerm | None:
    donem: OabTerm | None = (
        OabTerm.objects.select_related("rule_package").filter(status=TermStatus.ACIK).first()
    )
    return donem


def _yeni_okulun_hazirlik_donemi() -> OabTerm | None:
    """Yeni açılan okulun ilk genel kurulunun hazırlık dönemi (iptal edilmemiş, dönemsiz genel kurulun
    açacağı `HAZIRLIK` dönem): ilk genel kurulun kuralları ve uyum satırları bu dönemdedir
    (`genel_kurul.kural_donemi`). Açık dönem yokken "tamamlanacaklar" buradan okunur (modül başlığı)."""
    kurul: GeneralAssembly | None = (
        GeneralAssembly.objects.select_related("opens_term__rule_package")
        .filter(term__isnull=True, opens_term__status=TermStatus.HAZIRLIK)
        .exclude(status=AssemblyStatus.IPTAL)
        .order_by("-pk")
        .first()
    )
    return None if kurul is None else kurul.opens_term


def _bilgiler(donem: OabTerm | None) -> list[dict[str, Any]]:
    if donem is None:
        son = OabTerm.objects.order_by("-pk").values_list("status", flat=True).first()
        return [
            _kalem(
                DONEM_YOK,
                rota=_BIRLIK_DONEMI,
                son_durum=str(son) if son == TermStatus.IPTAL else "",
            )
        ]
    if not donem_kilidi.kural_kopyasi_tutuyor(donem):
        return [_kalem(KURAL_KOPYASI_DOGRULANAMADI, rota=_BIRLIK_DONEMI)]
    return []


def kalemler(rol: str | None, hesap_id: str | None, *, gun: date | None = None) -> dict[str, Any]:
    """Oturumdaki rolün pano kalemleri (modül başlığı). Yazmaz; rolü bilinmeyen oturum yalnız rol
    süzmesi gerekmeyen kalemleri (bilgiler, tamamlanacaklar, kendi taslağı) görür.

    Dönüş: `{bugun, gorunum, bilgiler, isler, tamamlanacaklar}`. `isler` vadeli kalemler önde (son güne
    göre), vadesizler ardından; tamamlanacaklar satır sırasıyla.
    """
    gun = gun or bugun()
    donem = _acik_donem()
    eksik_donemi = donem if donem is not None else _yeni_okulun_hazirlik_donemi()
    adaylar: list[tuple[str, dict[str, Any]]] = []
    if donem is not None:
        adaylar.extend(_kuralli_kalemler(donem, gun))
    adaylar.extend(_genel_kurul_kalemleri(donem, gun))
    adaylar.extend(_takvim_kalemleri())
    if rol == _YONETICI:
        adaylar.extend((GECIS_ADIMI, k) for k in _gecis_kalemleri())
        kural_surumu = _kural_surumu_kalemi()
        if kural_surumu is not None:
            adaylar.append((KURAL_SURUMU, kural_surumu))
        adaylar.extend((HESAP_ONERISI, k) for k in _hesap_kalemleri())
    isler = [k for kod, k in adaylar if rol is not None and rol in KALEM_ROLLERI[kod]]
    taslak = _taslak_kalemi(hesap_id)
    if taslak is not None:
        isler.append(taslak)
    isler.sort(key=lambda k: (k["vade"] is None, k["vade"] or ""))
    return {
        "bugun": gun.isoformat(),
        "gorunum": "ay" if rol in AYLIK_GORUNUM_ROLLERI else "hafta",
        "bilgiler": _bilgiler(donem),
        "isler": isler,
        "tamamlanacaklar": (
            ([] if eksik_donemi is None else _tamamlanacaklar(eksik_donemi, rol, gun))
            + _okul_karti_tamamlanacaklari(rol)
        ),
    }
