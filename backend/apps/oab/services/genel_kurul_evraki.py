"""Genel kurul evrakı: E04-E14 ve E64 — üretim, veli adlı çıktı ve basım (plan F2 §4, 8.-10. adım).

`gorev_evraki`'nin kalıbıdır (`KODLAR`, `BELGE_ADLARI`, `URETEN_ROLLER`, kurucular, `uret`, `bas`).
İskelet 8. adımdadır; içerik kurucuları 9. adımda E05, E06, E07, E08 ve E64 için ("Genel kurul evrakı
I"), 10. adımda E09-E14 için yazıldı ("Genel kurul evrakı II"). E04'ün kurucusu dört alt metnin
kullanıcı onayından sonra yazılır (plan F2 §9 S8 (i), §10.1 "E04 10. adımın son işi"). Kurucusu
olmayan kod üretilmez (`KOD_GECERSIZ`).

GENEL KURUL EVRAKI I (plan F2 §4.1, §7 U14-U18, U34; tasarım §9.3, §9.6):

- E05 — çağrı ve gündem (dosya nüshası; duyuru kanıtıyla), toplantı başına (U34). Çağırana göre
  "kol"dur (`cagri_kolu`: yönetim kurulu · başkanın md. 13/8 çağrısı · müdürün md. 9/1, 9/6, 13/8,
  25/2 çağrısı · Denetleme Kurulu md. 14/5 · üyelerin başvurusu): üreten rol ve imza ona göredir
  (MB-3, tasarım §9.3 "Çağıran ve imzacı", "Görüldü"). Müdürün kollarında belge müdürün yazısıdır:
  yalnız müdürün hesabından, çağrının sahiplikli eylemiyle üretilir (¹), antedi okulundur (§9.1-8),
  "Görüldü" bloğu yoktur; öteki kollarda müdür "Görüldü — Okul Müdürü (md. 27/1)" bloğundadır.
  Yönetim kurulunun çağrı kararı bağlı değilse karar tarihi ve sayısı "………" (kullanıcı kararı S1
  (a)); üyelerin başvurusunda imza birlik başkanınındır (KE-11 varsayılanı, S8). İmzacı bugünkü
  görevli değil, çağrı günü görevde olandır (`_cagri_imza_gunu`: en geç birinci toplantıdan bir gün
  önce; `selectors.gundeki_asillar`). Duyuru kanıtında görev unvanı sütunu elle doldurulur (ilan
  kaydı yapanı tutmaz; ad yazılmaz). Toplantıya ilan süresinden az gün kala basımda uyarı
  (`genel_kurul.ilan_en_az_gun`; tasarım §9.6 E05).
- E06 — duyuru (ilan panosu ve internet sayfası), toplantı başına; kişisizdir (tasarım §9.1-5):
  çağrı nedeni de basılmaz (serbest metindir, ad taşıyabilir). İmza çağırana göre kurum adıdır (U17).
  PDF saklanır, web sayfası kayıtlı içerikten çizilir (U18).
- E07 — kişisiz kip: üyelere elden yazılı davet ("Sayın Veli"), kısa aydınlatma paragrafı (KM-6;
  kullanıcının 08.11.2026'da onayladığı veli metninin cümleleri BİREBİR ve tam metnin yeri) ve sınıf
  başına davet adedi; imza çağırana göre kurum adı (U17, S5 (ii)). Adlı kip: sınıf teslim çizelgesi
  (veli adları "Ad SOYAD": tek alandan son sözcük soyadı, üç ve daha çok sözcükte basım uyarısı;
  sınıf başına sayfa, teslim eden sınıf rehber öğretmeni); yalnız `adli_uret_ve_ver`.
- E08 — katılım cetveli. Sınıf başına ayrı sayfa (M-13 a), sınıf sonunda listede olmayan veliler
  için boş satır (U16), öğretmenler ve idareciler, diğer katılanlar, gözlemci öğrenciler (boş satırlı;
  ad alınmaz, T5). T.C. kimlik no ve telefon sütunu yoktur. Sayfa parafı: genel kurul yapıldıysa Divan
  Başkanı + Kâtip, yapılamadıysa Birlik Başkanı + Sekreter (yeni okulda açılışı yapan okul müdürü, S5
  (ii)). Cetvel toplantıdan önce basılır; genel kurul yapılmadıkça sonuç belli değildir ve iki kolun
  unvanları koşuluyla, adsız basılır ("Divan Başkanı — toplantı yapıldıysa" ...). Kişisiz kip (boş
  satırlı) hiçbir ad taşımaz, parafta da (U14); adlı kip veli ve personel adlarıyla, yalnız
  `adli_uret_ve_ver`.
- E64 — yeter sayı tespit tutanağı, toplantı başına (U34); kişisizdir (KE-21; tasarım §9.6 "yalnız
  sayılar"): dondurulmuş yeter sayı, mevcut, katılan, türe göre dağılım, gözlemci; imza bloklarında
  yalnız unvan, kişisel veri dipnotu yok. Sağlandıysa Divan Başkanı + Kâtip; sağlanamadıysa Birlik
  Başkanı + Sekreter + "Görüldü — Okul Müdürü" (KE-10); müdürün çağırdığı genel kurulda "Görüldü"
  yoktur (tasarım §9.3 "Görüldü (müdür çağırmadıysa)"), yeni okulda açılışı yapan okul müdürü (S5
  (ii)); ikinci toplantıda "çoğunluk aranmaz" satırı. Katılan toplantıda girilen sayıdır (sonuç ondan
  hesaplandı); sonradan düzeltildiyse düzeltilmiş sayı ayrı satır ve basım uyarısıdır. İkinci
  toplantının sayıları birincinin türe göre dağılımının ve gözlemci sayısının üzerine yazılır
  (`genel_kurul.ikinci_toplanti`): birinci toplantının tutanağı ikinci toplantı kaydedildikten sonra
  üretilirse bu satırlar "………" ve basım uyarısıdır (sayı `first_attendee_count`'tan basılır; yeni
  model alanı açılmadı).

GENEL KURUL EVRAKI II (plan F2 §4.1, §7 U20-U22; tasarım §9.1-§9.3, §9.6):

- E09 — yönetim kurulu ve Denetleme Kurulu (veli koltuğu) aday listeleri: bu genel kurulun aday
  kayıtları (aday kalan, seçilen, sonradan düşen; iptal edilen yanlış giriş hariç), kişi türü ve
  yönetim kurulunda md. 12/4 sayacı (bu genel kurulun seçilmesi hariç). Öğretmen koltukları bilgi
  satırıdır, sayılar kural paketinden. Olağanüstü genel kurul Denetleme Kuruluna seçim yapmaz (S10):
  B bölümü basılmaz. İmza Divan Başkanı + Kâtip.
- E10 — toplantı tutanağı, yalnız yapılmış genel kurulda: toplantı, açılış ve divan, gündemin
  sonuçları (oylarla; çıkarılan madde de), gündem değişikliğinin oylaması ayrı tabloda, ibra kurul
  başına ayrı oylama satırı, seçilenler (E09 ve E13 ile aynı kayıtlar), teslim günü. Tahmini bütçe
  yalnız "görüşüldü" ve ekin adı (U22). İmza divan + "Görüldü — Okul Müdürü (md. 27/1)"; müdürün
  çağırdığı genel kurulda "Görüldü" yok (tasarım §9.3; E64 ile aynı). Tarih yapıldığı gün.
- E11 — ibra edilmeyen muhasebe evrakının teslim tutanağı; E12 — il/ilçe millî eğitim müdürlüğüne
  resmî yazı: yalnız yönetim kurulunun hesapları ibra edilmediğinde (S4 (a)). E11 evrakı tutanağın
  notundan tek tek listeler; divan teslim eder, teslim alan kurullar adına birer üye teslim alır
  (adları elle; seçilen yeni kurul ya da görevdeki kurul — olağanüstü genel kurul Denetleme Kuruluna
  seçim yapmaz, S10 (a); `TESLIM_ALANLAR`). E12 RYUE biçimindedir (okul antedi, "Sayı:" yer tutucu, tarih üretim günü, konu, muhatap
  S11 (a) önerisi ya da basımda düzenlenen muhatap — boşsa yer tutucu ve uyarı, girintili metin
  md. 16/4, imza bölümü md. 17/1, 17/11, ek E11 md. 18); taslağı program yöneticisi hazırlar
  (KE-19), müdür rolü üretmez; okul dışına gittiği için kişisel veri dipnotu basılmaz.
- E13 — sonuç bildirimi (okul müdürlüğüne): sonuç, seçilenler, tarihli sonraki işler (görev
  bölümlerinin son günü kural paketinden); konum cümlesi TFB imzanın hemen üstünde; "Yönetmelik
  gereği" denmez (MB-11). İmza yeni başkan + yeni sekreter (görev bölümünden önce "………", U21) ve
  "Teslim alan: Okul Müdürü".
- E14 — yıllık iş takvimi (konusu birlik dönemi; kişisiz, imzasız): süre kuralı satırları kural
  kimliği ve atıf taşır (sözlük §2 istisna 3), okul planı satırları (ders yılı, dönemin yönetim
  kurulu toplantı günü ve denetim planı) ayrı bölümdedir.

Kişisel veri dipnotu (tasarım §9.1-5) yalnız kişi adı taşıyan iç belgelerdedir (E05, adlı E07 ve E08,
E09, E10, E13); E12 okul dışına giden resmî yazıdır, dipnot taşımaz; E11 E12'nin ekidir (il/ilçe millî
eğitim müdürlüğüne gider), "okul dışına verilmez" dipnotu onda da basılmaz (10. adımın kararı, kullanıcı
onayına sunuldu). Konum cümlesi F2'de yalnız
E13'tedir (TFB); karar taslağı cümlesi (KDT) ve taslak ibaresi hiçbir F2 belgesinde yoktur. Belgede
üretim günü yoktur (resmî yazının tarihi hariç): aynı veriden yeniden üretim aynı içerik özetini
verir. Boş alan "………"dır, basım
uyarısı üretimin yanıtındadır, belgeye basılmaz (F1c kalıbı, `gorev_evraki`).

KONU VE DÖNEM (plan F2 §4.2). Genel kurul belgelerinin (E05-E13, E64) konusu genel kuruldur
(`GeneralAssembly`); dönemi `assembly.term`'dür, yeni okulun ilk genel kurulunda hazırlık dönemi
(`opens_term`; `genel_kurul.kural_donemi`). Bu belgeler hazırlık dönemine de yazılır
(`hazirlik_yazimi=True`; dönem kilidi `donem_kilidi.yazma_denetimi`). E04'ün konusu okul kartıdır
(dönemsiz), E14'ünkü birlik dönemidir; E14 genel kurul belgesi değildir, hazırlıktaki döneme
yazılmaz (`DonemYazilamaz`).

KİP VE TOPLANTI (plan F2 §7 U14, U34). E07 ve E08 iki kiplidir: kişisiz kip (`KISISIZ`: davet ve
sınıf başına adet; boş satırlı cetvel) `uret` ile üretilir ve saklanır; adlı kip (`ADLI`: teslim
çizelgesi; veli adlı cetvel) yalnız `adli_uret_ve_ver` ile, saklanmadan verilir. E05, E06 ve E64
toplantı başınadır (`BIRINCI`, `IKINCI`). Öteki belgeler kip ve toplantı almaz. Aynı konunun aynı
kodlu belgeleri kip ve toplantı başına ayrı geçerli satırdır (`evrak_servisi.kaydet`).

BİÇİMLER (tasarım §9.5; plan F2 §7 U18). Word ve PDF dosya deposunda saklanır (`dosya_ekle`); Excel
(E08, E14) ve web sayfası (E06) saklanmaz, kayıtlı içerikten (`content_json`) istendikçe çizilir.

ÜRETİM (`uret`). Sıra `gorev_evraki.uret`'inki: yazma kapısı → ilk hesap → rol (genel kurul
belgelerinde `Eylem.GENEL_KURUL_YAZMA` ve tasarım §9.6'nın "Üreten"i, `URETEN_ROLLER`; E05'te
çağırana göre: müdürün ve Denetleme Kurulunun çağrısında çağrının sahiplikli eylemi, öteki kollarda
`E05_URETENLER`) → içerik → çizim (işlem dışında) → TEK işlemde evrak kaydı ve saklanan dosyalar.

VELİ ADLI ÇIKTI (`adli_uret_ve_ver`; plan F2 §7 U15, R9; tasarım §5.2.8, §4.6.4). Hesap teslim
pusulasının (E63) kalıbıyla tek istekte üretilir ve verilir. Kapı `Eylem.KISISEL_VERI_CIKTISI`'dır
(dipnot ¹⁰: yalnız program yöneticisi). Belge bellekte çizilir; sonra AYNI işlemde (1) evrak kaydı
`kaydet(kisi_listesi=True, satir_sayisi=N, kip=ADLI)` — içerik JSON'u saklanmaz, yalnız özeti, satır
sayısı ve tarih kalır; kapanmış döneme yazılmaz (O2), (2) `BASIM` izi (kod ve dosyanın sha256'sı) ve
(3) erişim günlüğünün `VELI_LISTESI_CIKTISI` satırı (dosyanın sha256'sı ve satır sayısı; ad
yok) yazılır. Biri yazılamazsa dosya verilmez. `dosya_ekle` çağrılmaz: dosya hiçbir yerde saklanmaz;
arşiv paketine girmez (F4). Yanıtın `Cache-Control: no-store`'u ucundur (11. adım; `indirme_yaniti`
hazırdır). Günlüğe, hataya ve ize kişi adı yazılmaz: kayıt yalnız kodu ve satır sayısını söyler.

BASIM (`bas`). Kaydedilmiş belgeyi okur roller basar (tasarım §9.6; `OKUMA_SATIRLARI`): genel kurul
belgelerini M3'ü, E14'ü M9'u, E04'ü M1'i okuyan roller. Saklanan biçim dosya deposundan, saklanmayan
biçim kayıtlı içerikten çizilir (`evrak_servisi.yeniden_ciz`); sonra AYNI istekte `BASIM` satırı
yazılır, yazılamazsa dosya verilmez. Veli adlı belge yeniden basılmaz (dosyası ve içeriği yoktur:
404). `gorev_evraki.bas`'ın F1c davranışı değişmez.

Bütün sabit metinler sözlüğe girer (sözlük §1 "Genel kurul evrakı (F2)").
"""

from __future__ import annotations

import calendar
import hashlib
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Final

from django.db import models, transaction
from django.http import FileResponse, Http404
from django.utils import timezone

from apps.oab import selectors
from apps.oab.kurallar import YururlukteDegerYok, kural, kural_kaydi, yazma_kapisi
from apps.oab.kurallar.erisim import atif_metni
from apps.oab.models import (
    AgendaItem,
    AgendaItemKind,
    AgendaResult,
    Announcement,
    AssemblyCaller,
    AssemblyKind,
    AssemblyMeeting,
    AssemblyMinutes,
    AssemblyStatus,
    AttendanceKind,
    Discharge,
    DocumentFormat,
    DocumentStatus,
    DocumentVariant,
    GeneralAssembly,
    GeneratedDocument,
    MembershipRole,
    MembershipStatus,
    OabTerm,
    OrganMembership,
    OrganType,
    PersonKind,
    SeatGroup,
    SeatType,
)
from apps.oab.services import evrak as evrak_servisi
from apps.oab.services import gelen_giden_evrak, genel_kurul, uyelikler, uyum
from apps.oab.services.gorev_evraki import (
    BOS,
    KONU_BILGI,
    UNVAN_TESLIM_ALAN,
    UYARI_AD_OKUNAMADI,
    UYARI_GOREV_BOS,
    _ad,
    _an,
    _gun,
    _mudur_adi,
    _olay_gunu,
    _Uyarilar,
)
from apps.okul import denetim_izi, erisim_gunlugu, excel_veli, normalize, rol_izinleri
from apps.okul.models import (
    AccessKind,
    AccountRole,
    CanteenMode,
    MemberKind,
    ParentRoster,
    Personnel,
    SchoolConfig,
    SchoolTerm,
)
from apps.okul.oturum import yazar
from apps.okul.selectors import personnel_sorted
from apps.okul.services import app_password, dosya_deposu
from shared import evrak
from shared.crypto import is_corrupt
from shared.exceptions import RolYetkisiz
from shared.letterhead import MEM_IL, MEM_ILCE, mem_muhatabi

logger = logging.getLogger(__name__)

E04: Final = "E04"
E05: Final = "E05"
E06: Final = "E06"
E07: Final = "E07"
E08: Final = "E08"
E09: Final = "E09"
E10: Final = "E10"
E11: Final = "E11"
E12: Final = "E12"
E13: Final = "E13"
E14: Final = "E14"
E64: Final = "E64"
KODLAR: Final = (E04, E05, E06, E07, E08, E09, E10, E11, E12, E13, E14, E64)
#: Konusu genel kurul olan belgeler (modül başlığı "Konu ve dönem").
GENEL_KURUL_KODLARI: Final = frozenset({E05, E06, E07, E08, E09, E10, E11, E12, E13, E64})
#: İki kipli belgeler (U14) ve toplantı başına belgeler (U34).
KIPLI_KODLAR: Final = frozenset({E07, E08})
TOPLANTILI_KODLAR: Final = frozenset({E05, E06, E64})
#: Basımda düzenlenen muhatabı olan resmî yazılar (plan F2 §7 U20).
MUHATAPLI_KODLAR: Final = frozenset({E12})
#: Veli adlı kipin belgeleri (R9).
ADLI_KODLAR: Final = (E07, E08)

#: Belge adları (tasarım §9.5 kataloğu; kısaltmalar açık yazılır, sözlük §3 "Kısaltma").
BELGE_ADLARI: Final[dict[str, str]] = {
    E04: "Kişisel veri aydınlatma metni",
    E05: "Genel kurul toplantı çağrısı ve gündemi",
    E06: "Genel kurul duyurusu",
    E07: "Üyelere elden yazılı davet ve sınıf teslim çizelgesi",
    E08: "Genel kurul katılım cetveli",
    E09: "Yönetim kurulu ve Denetleme Kurulu (veli koltuğu) aday listeleri",
    E10: "Genel kurul toplantı tutanağı",
    E11: "İbra edilmeyen muhasebe evrakının teslim tutanağı",
    E12: "İbra edilmediğine dair il/ilçe millî eğitim müdürlüğüne resmî yazı",
    E13: "Genel kurul sonuç bildirimi",
    E14: "Yıllık iş takvimi",
    E64: "Genel kurul yeter sayı tespit tutanağı",
}
#: Kaydedilen dosyanın adının belge kısmı (sözlük §3 "Kaydedilen dosya adı"; ad + kapsam + tarih).
DOSYA_ADI_KOKLERI: Final[dict[str, str]] = {
    E04: "Kişisel-Veri-Aydınlatma-Metni",
    E05: "Genel-Kurul-Çağrısı-ve-Gündemi",
    E06: "Genel-Kurul-Duyurusu",
    E07: "Genel-Kurul-Daveti",
    E08: "Genel-Kurul-Katılım-Cetveli",
    E09: "Genel-Kurul-Aday-Listeleri",
    E10: "Genel-Kurul-Toplantı-Tutanağı",
    E11: "İbra-Edilmeyen-Evrak-Teslim-Tutanağı",
    E12: "İbra-Edilmediğine-Dair-Resmî-Yazı",
    E13: "Genel-Kurul-Sonuç-Bildirimi",
    E14: "Yıllık-İş-Takvimi",
    E64: "Genel-Kurul-Yeter-Sayı-Tespit-Tutanağı",
}
#: Veli adlı kipin dosya adı kökleri (kişisiz kipten ayırt edilsin).
ADLI_DOSYA_ADI_KOKLERI: Final[dict[str, str]] = {
    E07: "Genel-Kurul-Daveti-Sınıf-Teslim-Çizelgesi",
    E08: "Genel-Kurul-Katılım-Cetveli-Veli-Adlı",
}
#: Toplantının dosya adındaki kapsamı.
TOPLANTI_KAPSAMLARI: Final[dict[str, str]] = {
    AssemblyMeeting.BIRINCI: "Birinci-Toplantı",
    AssemblyMeeting.IKINCI: "İkinci-Toplantı",
}

_DOCX_PDF: Final = (DocumentFormat.PDF, DocumentFormat.DOCX)
#: Belgelerin biçimleri (tasarım §9.5 "Biçim").
BICIMLER: Final[dict[str, tuple[str, ...]]] = {
    E04: _DOCX_PDF,
    E05: _DOCX_PDF,
    E06: (DocumentFormat.PDF, DocumentFormat.HTML),
    E07: _DOCX_PDF,
    E08: (DocumentFormat.PDF, DocumentFormat.DOCX, DocumentFormat.XLSX),
    E09: _DOCX_PDF,
    E10: _DOCX_PDF,
    E11: _DOCX_PDF,
    E12: _DOCX_PDF,
    E13: _DOCX_PDF,
    E14: (DocumentFormat.PDF, DocumentFormat.XLSX),
    E64: _DOCX_PDF,
}
#: Veli adlı kipin biçimleri (tasarım §9.5; plan F2 §4.1: adlı E08 docx+pdf ve xlsx).
ADLI_BICIMLER: Final[dict[str, tuple[str, ...]]] = {
    E07: _DOCX_PDF,
    E08: (DocumentFormat.PDF, DocumentFormat.DOCX, DocumentFormat.XLSX),
}
#: Dosya deposunda saklanan biçimler; ötekiler kayıtlı içerikten çizilir (U18).
SAKLANAN_BICIMLER: Final = frozenset(_DOCX_PDF)
UZANTILAR: Final[dict[str, str]] = {
    DocumentFormat.PDF: "pdf",
    DocumentFormat.DOCX: "docx",
    DocumentFormat.XLSX: "xlsx",
    DocumentFormat.HTML: "html",
}
#: Verilen dosyanın türü (saklanan biçimlerde dosya deposunun türüyle aynı).
MIME_TURLERI: Final[dict[str, str]] = {
    **evrak_servisi.BICIM_TURLERI,
    DocumentFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    DocumentFormat.HTML: "text/html; charset=utf-8",
}

_YONETICI: Final = AccountRole.YONETICI.value
_SEKRETER: Final = AccountRole.SEKRETER.value
#: Üreten roller (tasarım §9.6 "Üreten"; plan F2 §4.1). E05'in satırı yönetim kurulunun çağrısınındır;
#: E05 çağırana göre üretilir (`E05_URETENLER`, `_e05_yetkisi`). E07 ve E08'in adlı kipi
#: `KISISEL_VERI_CIKTISI` ile yalnız program yöneticisinindir (U14).
URETEN_ROLLER: Final[dict[str, frozenset[str]]] = {
    E04: frozenset({_YONETICI}),
    **{
        kod: frozenset({_YONETICI, _SEKRETER})
        for kod in (E05, E06, E07, E08, E09, E10, E11, E13, E64)
    },
    E12: frozenset({_YONETICI}),
    E14: frozenset({_YONETICI}),
}
#: Basımın okuma satırı (tasarım §4.4.2 "Okuma"; plan F2 §6.1): genel kurul M3, yıllık iş takvimi M9
#: (Genel Bakış), aydınlatma metni M1 (okul kartı; her rol okur).
OKUMA_SATIRLARI: Final[dict[str, rol_izinleri.Satir]] = {
    E04: rol_izinleri.Satir.M1,
    **{kod: rol_izinleri.Satir.M3 for kod in GENEL_KURUL_KODLARI},
    E14: rol_izinleri.Satir.M9,
}

KOD_GECERSIZ: Final = "Bu evrak bu yoldan üretilmez."
KONU_GECERSIZ: Final = "Bu evrak bu kayıt için üretilmez."
KIP_GECERSIZ: Final = "Bu evrakın kipi geçersiz."
TOPLANTI_GECERSIZ: Final = "Bu evrakın toplantısı geçersiz."
BICIM_GECERSIZ: Final = "Bu evrak bu biçimde verilmez."


# ---------------------------------------------------------------------------
# Kurucular (9. ve 10. adımlarda dolar)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Muhatap:
    """Resmî yazının (E12) basımda düzenlenen muhatabı (plan F2 §7 U20, kullanıcı kararı S11 (a)):
    idarenin adı (büyük harfe çizici çevirir, RYUE md. 14/2) ve parantez içindeki birim (md. 14/5).
    Verilmezse muhatap okul kartından önerilir (`letterhead.mem_muhatabi`)."""

    idare: str
    birim: str = ""


@dataclass(frozen=True)
class Secim:
    """Üretimin kipi ve toplantısı (modül başlığı "Kip ve toplantı"); resmî yazıda (E12) basımda
    düzenlenen muhatap."""

    kip: str = ""
    toplanti: str = ""
    muhatap: Muhatap | None = None


@dataclass(frozen=True)
class AdliIcerik:
    """Veli adlı belgenin içeriği: model, satır sayısı (veli satırı) ve basım uyarıları."""

    belge: evrak.Belge
    satir_sayisi: int
    uyarilar: tuple[str, ...] = ()


#: Kişisiz kurucu: konu ve seçim → (içerik modeli, basım uyarıları).
Kurucu = Callable[[models.Model, Secim], tuple[evrak.Belge, tuple[str, ...]]]
#: Veli adlı kurucu: genel kurul ve toplantı → içerik.
AdliKurucu = Callable[[GeneralAssembly, str], AdliIcerik]


# ---------------------------------------------------------------------------
# Genel kurul evrakı I — sabitler (sözlük §1 "Genel kurul evrakı (F2)")
# ---------------------------------------------------------------------------
#: Çağrının kolları (modül başlığı "Genel kurul evrakı I"; tasarım §9.6 E05 "İmza").
KOL_YK: Final = "yk"
KOL_BASKAN_13_8: Final = "baskan_13_8"
KOL_MUDUR_9_1: Final = "mudur_9_1"
KOL_MUDUR_9_6: Final = "mudur_9_6"
KOL_MUDUR_13_8: Final = "mudur_13_8"
KOL_MUDUR_25_2: Final = "mudur_25_2"
KOL_DK_14_5: Final = "dk_14_5"
KOL_YUZDE_10: Final = "yuzde_10"
KOLLAR: Final = (
    KOL_YK,
    KOL_BASKAN_13_8,
    KOL_MUDUR_9_1,
    KOL_MUDUR_9_6,
    KOL_MUDUR_13_8,
    KOL_MUDUR_25_2,
    KOL_DK_14_5,
    KOL_YUZDE_10,
)
#: Müdürün yazısı olan kollar (tasarım §9.3 "Çağıran ve imzacı"; ¹, M-5, M-11).
MUDUR_KOLLARI: Final = frozenset({KOL_MUDUR_9_1, KOL_MUDUR_9_6, KOL_MUDUR_13_8, KOL_MUDUR_25_2})
_BASKAN: Final = AccountRole.BASKAN.value
#: E05'i üreten roller, çağrının sahibi olmayan kollarda (tasarım §9.6 E05 "Üreten", MB-3): yönetim
#: kurulunun çağrısında sekreter ve program yöneticisi, başkanın md. 13/8 çağrısında başkan. Üyelerin
#: başvurusunda çağrıyı kaydeden program yöneticisi ve yönetim kurulunun sekreteri (KE-11: çağrıyı
#: yönetim kurulu başkanı yapar). Müdürün ve Denetleme Kurulunun kollarında çağrının sahiplikli eylemi
#: geçer (`genel_kurul.cagri_yazisi_eylemi`).
E05_URETENLER: Final[dict[str, frozenset[str]]] = {
    KOL_YK: frozenset({_YONETICI, _SEKRETER}),
    KOL_BASKAN_13_8: frozenset({_BASKAN}),
    KOL_YUZDE_10: frozenset({_YONETICI, _SEKRETER}),
}

#: Genel kurulun türü: cümle içinde ve başlığın alt satırında.
TUR_ADLARI: Final[dict[str, str]] = {
    AssemblyKind.OLAGAN: "olağan",
    AssemblyKind.OLAGANUSTU: "olağanüstü",
}
TUR_BASLIKLARI: Final[dict[str, str]] = {
    AssemblyKind.OLAGAN: "Olağan genel kurul",
    AssemblyKind.OLAGANUSTU: "Olağanüstü genel kurul",
}
TOPLANTI_ADLARI: Final[dict[str, str]] = {
    AssemblyMeeting.BIRINCI: "Birinci toplantı",
    AssemblyMeeting.IKINCI: "İkinci toplantı",
}
#: Başlığın alt satırında türden sonraki parçanın ayracı.
ALT_AYRAC: Final = " — "

#: E05'in "Çağıran" satırı (md. 9/1, 9/6, 13/8, 14/5, 25/2; md. 25/2 çağrıyı kendi metninde saymaz,
#: yetki md. 9/6'daki 2023 ek ibaresindendir).
CAGIRAN_YK_OLAGAN: Final = "Yönetim kurulu (md. 9/1)"
CAGIRAN_YK_OLAGANUSTU: Final = "Yönetim kurulu (md. 9/6)"
CAGIRAN_METINLERI: Final[dict[str, str]] = {
    KOL_BASKAN_13_8: "Birlik başkanı (md. 13/8)",
    KOL_MUDUR_9_1: "Okul müdürü, yeni açılan okul (md. 9/1)",
    KOL_MUDUR_9_6: "Okul müdürü (md. 9/6)",
    KOL_MUDUR_13_8: "Okul müdürü (md. 13/8)",
    KOL_MUDUR_25_2: "Okul müdürü (md. 9/6, 25/2)",
    KOL_DK_14_5: "Denetleme Kurulu (md. 9/6, 14/5)",
    KOL_YUZDE_10: "Birlik üyelerinin yazılı başvurusu (md. 9/6)",
}
#: Duyurunun ve davetin kişisiz imzası, çağırana göre (plan F2 §7 U17; yeni okul S5 (ii)). Başkanın md.
#: 13/8 çağrısında ve üyelerin başvurusunda (KE-11: çağrıyı yönetim kurulu başkanı yapar) unvandır.
_KURUM_YK: Final = "Okul-Aile Birliği Yönetim Kurulu"
_KURUM_MUDURLUK: Final = "Okul Müdürlüğü"
_KURUM_DK: Final = "Okul-Aile Birliği Denetleme Kurulu"
_KURUM_BASKAN: Final = "Okul-Aile Birliği Başkanı"
KURUM_ADLARI: Final[dict[str, str]] = {
    KOL_YK: _KURUM_YK,
    KOL_BASKAN_13_8: _KURUM_BASKAN,
    KOL_MUDUR_9_1: _KURUM_MUDURLUK,
    KOL_MUDUR_9_6: _KURUM_MUDURLUK,
    KOL_MUDUR_13_8: _KURUM_MUDURLUK,
    KOL_MUDUR_25_2: _KURUM_MUDURLUK,
    KOL_DK_14_5: _KURUM_DK,
    KOL_YUZDE_10: _KURUM_BASKAN,
}

#: Davetin ve duyurunun giriş cümlesi (md. 9/1 "Genel kurul, birliğin üyelerinden meydana gelir", 9/3).
DAVET_GIRISI: Final = (
    "Okul-Aile Birliğinin {tur} genel kurul toplantısı aşağıda belirtilen yer ve zamanda, "
    "belirtilen gündemle yapılacaktır; birliğin üyeleri genel kurula davetlidir (Millî Eğitim "
    "Bakanlığı Okul-Aile Birliği Yönetmeliği (Yönetmelik) md. 9/1, 9/3)."
)
#: İkinci toplantının ayrı ilanında giriş cümlesi (md. 9/2, 9/3; olağanüstüde de, A-1).
IKINCI_DAVET_GIRISI: Final = (
    "Okul-Aile Birliğinin {tur} genel kurulunun birinci toplantısında toplantı yeter sayısı "
    "sağlanamamıştır; ikinci toplantı aşağıda belirtilen yer ve zamanda, belirtilen gündemle "
    "çoğunluk aranmaksızın yapılacaktır (Millî Eğitim Bakanlığı Okul-Aile Birliği Yönetmeliği "
    "(Yönetmelik) md. 9/2, 9/3)."
)
#: md. 9/3'ün lafzı; gün sayısı kural paketinden (`genel_kurul.ilan_en_az_gun`).
ILAN_CUMLESI: Final = (
    "Toplantının yeri, zamanı ve gündemi en az {gun} gün önceden üyelere elden yazılı olarak "
    "bildirilir, okul ilan panosu ile okulun internet sayfasında duyurulur (md. 9/3)."
)
#: md. 9/2'nin son cümlesi; gün sayısı kural paketinden (`genel_kurul.ikinci_toplanti_en_gec_gun`).
IKINCI_TOPLANTI_CUMLESI: Final = (
    "Genel kurul birinci toplantıda toplanamazsa ikinci toplantı en geç {gun} gün içinde çoğunluk "
    "aranmaksızın yapılır; kararlar katılanların çoğunluğu ile alınır (md. 9/2)."
)
GUNDEME_BAGLILIK: Final = "Gündeme bağlılık ilkesi geçerlidir (md. 9/6)."

SATIR_TUR: Final = "Genel kurulun türü"
SATIR_CAGIRAN: Final = "Çağıran"
SATIR_CAGRI_NEDENI: Final = "Çağrı nedeni"
SATIR_KARAR: Final = "Yönetim kurulunun çağrı kararı: tarih ve sayı"
KARAR_DEGERI: Final = "{tarih} · {no}"
SATIR_BASVURU: Final = "Başvuran üye sayısı ve birlik üye sayısı (md. 9/6)"
BASVURU_DEGERI: Final = "{basvuran} / {uye}"
SATIR_DK_RAPORU: Final = "Denetleme Kurulunun raporunun günü (md. 14/5)"
SATIR_EVRAK: Final = "Çağrı yazısının evrak kaydı: yıl ve kayıt no"
EVRAK_DEGERI: Final = "{yil}/{no}"
SATIR_YER: Final = "Toplantının yeri"
SATIR_BIRINCI: Final = "Birinci toplantı: gün ve saat"
SATIR_IKINCI: Final = "İkinci toplantı: gün ve saat"
SATIR_YETER_SAYI: Final = "Toplantı yeter sayısı (md. 9/2)"
YETER_SAYI_DEGERI: Final = (
    "{sayi} (yönetim ve denetleme kurullarının asıl ve yedek üye sayısı {taban} × {carpan})"
)
GUNDEM_BOLUMU: Final = "Gündem"
GUNDEM_BASLIKLARI: Final = ("Sıra", "Gündem maddesi")
KANIT_BOLUMU: Final = "Duyuru kanıtı (md. 9/3)"
#: Kanıtın görev unvanı sütunu elle doldurulur (tasarım §9.6 E05 "görev unvanıyla (ad yok)"): ilan
#: kaydı (`Announcement`, tasarım §5.2.7) bildireni, asanı ve yayımlayanı tutmaz.
KANIT_BASLIKLARI: Final = ("Kanal", "Gün", "Yapanın görev unvanı (ad yazılmaz)")
KANAL_ELDEN: Final = (
    "Üyelere elden yazılı bildirim (üyelere elden yazılı davet ve sınıf teslim çizelgesi)"
)
KANAL_PANO: Final = "Okul ilan panosu"
KANAL_INTERNET: Final = "Okulun internet sayfası"
KANIT_ILAN_GUNU: Final = "İlan günü (en geç kanalın günü)"

#: E07: davet mektubu ve kısa aydınlatma paragrafı (KM-6; tasarım §9.1-5).
SAYIN_VELI: Final = "Sayın Veli,"
E07_AYDINLATMA_BASLIGI: Final = "Kişisel verileriniz hakkında kısa bilgi"
#: Kullanıcının 08.11.2026'da onayladığı veli listesi aydınlatma metninin cümleleri, BİREBİR (tek harf
#: değiştirilmez; ön yüzdeki karşılığı `kisiler/metinler.ts`, birebirliği testte sınanır).
VELI_AYDINLATMA_AMACI: Final = (
    "Amaç: Genel kurul toplantısının daveti, katılım cetveli ve toplantı yeter sayısının sayımı "
    "(OAB Yönetmeliği md. 9/2, 9/3, 10/1-a); birlik organlarına aday olan velinin kaydı. Yalnız "
    "veli adı-soyadı ve öğrencinin sınıfı tutulur; telefon, adres, T.C. kimlik no ve öğrencinin "
    "adı tutulmaz."
)
AYDINLATMA_VERI_SORUMLUSU_ETIKETI: Final = "Veri sorumlusu:"
AYDINLATMA_HAKLARINIZ: Final = (
    "Haklarınız: KVKK md. 11'deki haklarınızı (verinizin işlenip işlenmediğini öğrenme, bilgi "
    "isteme, düzeltilmesini ya da silinmesini isteme ve ötekiler) veri sorumlusuna başvurarak "
    "kullanabilirsiniz."
)
#: Tam metnin (E04) yeri: onaylı veli metninin girişi "genel kurul davetinde kısa paragrafı ve tam
#: metnin okunacağı yer (okul panosu, okul sitesi) yer alır" der. Bu cümle yenidir (kullanıcıya sorulacak).
E07_TAM_METIN_YERI: Final = (
    "Aydınlatma metninin tamamı (Kişisel veri aydınlatma metni) okul ilan panosunda ve okulun "
    "internet sayfasındadır."
)
E07_ADET_BOLUMU: Final = "Sınıf başına davet adedi ve teslim"
ADET_BASLIKLARI: Final = (
    "Sınıf",
    "Davet adedi",
    "Teslim eden sınıf rehber öğretmeni",
    "Teslim günü ve imza",
)
TOPLAM: Final = "Toplam"
#: E07'nin adlı kipi: sınıf teslim çizelgesi (S9: teslim eden sınıf rehber öğretmeni).
E07_CIZELGE_ALT: Final = "Sınıf teslim çizelgesi"
E07_CIZELGE_GIRISI: Final = (
    "Genel kurulun yazılı daveti (md. 9/3) sınıf rehber öğretmeni eliyle velilere teslim edilir; "
    "teslim bu çizelgeye işlenir."
)
SINIF_BOLUMU: Final = "Sınıf: {sinif}"
CIZELGE_BASLIKLARI: Final = ("Sıra", "Velinin adı ve soyadı", "Teslim günü", "Açıklama")

#: E08: katılım cetveli (md. 10/1-a; U16; M-13 a).
E08_GIRIS: Final = (
    "Genel kurula katılan üyeler toplantı katılım cetvelini imzalar (Millî Eğitim Bakanlığı "
    "Okul-Aile Birliği Yönetmeliği (Yönetmelik) md. 10/1-a). Aynı veli birden çok çocuğu için bir "
    "kez imzalar. Gözlemci öğrenciler (md. 9/5) ayrı bölümde imzalar ve katılım sayısına eklenmez."
)
VELI_BOLUMU: Final = "Veliler — sınıf: {sinif}"
VELI_BOLUMU_SINIFSIZ: Final = "Veliler"
VELI_BASLIKLARI: Final = ("Sıra", "Velinin adı ve soyadı", "Öğrencinin sınıfı", "İmza")
PERSONEL_BOLUMU: Final = "Öğretmenler ve idareciler"
PERSONEL_BASLIKLARI: Final = ("Sıra", "Adı ve soyadı", "Görevi", "İmza")
#: Personelin görev türünün cetveldeki adı (katılım dağılımının adlarıyla aynı, `AttendanceKind`).
PERSONEL_GOREVLERI: Final[dict[str, str]] = {
    MemberKind.OGRETMEN: str(AttendanceKind.OGRETMEN.label),
    MemberKind.YONETICI: str(AttendanceKind.IDARECI.label),
}
DIGER_BOLUMU: Final = "Diğer katılanlar"
DIGER_BASLIKLARI: Final = ("Sıra", "Adı ve soyadı", "Katılım türü", "İmza")
GOZLEMCI_BOLUMU: Final = "Gözlemci öğrenciler (md. 9/5; katılım sayısına eklenmez)"
GOZLEMCI_BASLIKLARI: Final = ("Sıra", "Kurul ya da sınıf seviyesi", "İmza")
#: Boş satır sayıları (düzen kararı, kural değildir): her bölümün sonunda listede olmayanlar için
#: (U16: ör. ikinci ebeveyn, md. 4/1-f), veli listesi yokken veli bölümünde ve gözlemci bölümünde.
EK_BOS_SATIR: Final = 5
BOS_VELI_SATIRI: Final = 40
GOZLEMCI_SATIRI: Final = 10

#: E64: yeter sayı tespit tutanağı (md. 9/2, 9/5; KE-10, KE-21).
E64_GIRIS: Final = (
    "Okul-Aile Birliğinin {tur} genel kurul toplantısının yeter sayısı aşağıdaki sayılarla tespit "
    "edilmiştir (Millî Eğitim Bakanlığı Okul-Aile Birliği Yönetmeliği (Yönetmelik) md. 9/2, 9/5)."
)
ALT_SAGLANDI: Final = "Toplantı yeter sayısı sağlandı"
ALT_SAGLANAMADI: Final = "Toplantı yeter sayısı sağlanamadı"
ALT_COGUNLUK_ARANMAZ: Final = "Çoğunluk aranmaz"
SATIR_TOPLANTI: Final = "Toplantı"
SATIR_GUN_YER: Final = "Toplantının günü, saati ve yeri"
GUN_YER_DEGERI: Final = "{an} · {yer}"
SATIR_MEVCUT: Final = "Öğrenci mevcudu (yeter sayının girdisi)"
SATIR_KATILAN: Final = "Katılım cetvelini imzalayan üye sayısı (md. 10/1-a)"
SATIR_KATILAN_DUZELTILMIS: Final = "Katılım sayısının toplantıdan sonra düzeltilmiş değeri"
SATIR_GOZLEMCI: Final = "Gözlemci öğrenci sayısı (md. 9/5; katılım sayısına eklenmez)"
SATIR_SONUC: Final = "Sonuç"
SONUC_SAGLANDI: Final = (
    "Toplantı yeter sayısı sağlandı; genel kurul birinci toplantıda toplandı (md. 9/2)."
)
SONUC_SAGLANAMADI: Final = (
    "Toplantı yeter sayısı sağlanamadı; ikinci toplantı çoğunluk aranmaksızın yapılır (md. 9/2)."
)
SONUC_COGUNLUK_ARANMAZ: Final = (
    "İkinci toplantıda çoğunluk aranmaz; genel kurul katılan üyelerle toplandı (md. 9/2)."
)
DAGILIM_BOLUMU: Final = "Katılımın türe göre dağılımı"
DAGILIM_BASLIKLARI: Final = ("Katılım türü", "Sayı")

#: İmza bloklarının unvanları (tasarım §9.3, §9.6; KE-10, S5 (ii)).
UNVAN_YK_ADINA_BASKAN: Final = "Yönetim Kurulu adına Birlik Başkanı"
UNVAN_BIRLIK_BASKANI: Final = "Birlik Başkanı"
UNVAN_SEKRETER: Final = "Sekreter"
UNVAN_OKUL_MUDURU: Final = "Okul Müdürü"
UNVAN_GORULDU_E05: Final = "Görüldü — Okul Müdürü (md. 27/1)"
UNVAN_GORULDU: Final = "Görüldü — Okul Müdürü"
UNVAN_ACILISI_YAPAN: Final = "Okul Müdürü (açılışı yapan)"
UNVAN_DIVAN_BASKANI: Final = "Divan Başkanı"
UNVAN_KATIP: Final = "Kâtip"
UNVAN_DK_BASKANI: Final = "Denetleme Kurulu Başkanı"
UNVAN_DK_UYESI: Final = "Denetleme Kurulu Üyesi"
UNVAN_REHBER: Final = "Teslim eden: Sınıf rehber öğretmeni"
#: Sonucu belli olmayan toplantının cetvelinde parafın iki kolu (tasarım §9.6 E08; `_paraf`).
PARAF_YAPILDIYSA: Final = "{unvan} — toplantı yapıldıysa"
PARAF_YAPILAMADIYSA: Final = "{unvan} — toplantı yapılamadıysa"

#: Boş alanın yeri (tasarım §9.3 "blok ……… kalır"; `gorev_evraki.BOS` ile aynı).
BOS_YER: Final = BOS

#: Üretimin iletileri (belge üretilmez).
CAGRI_YOK: Final = "Genel kurul çağrılmadan bu evrak üretilmez."
IKINCI_TOPLANTI_ACILMADI: Final = (
    "İkinci toplantının belgesi birinci toplantıda yeter sayı sağlanamadıktan sonra üretilir."
)
TOPLANTI_YAPILMADI: Final = (
    "Bu toplantının katılımı girilmeden yeter sayı tespit tutanağı üretilmez."
)

#: Basım uyarıları (üretimin yanıtında; belgeye basılmaz).
UYARI_YER_YOK: Final = "Toplantının yeri girilmemiş; yeri ……… basıldı."
UYARI_IKINCI_TARIH_YOK: Final = "İkinci toplantının günü girilmemiş; yeri ……… basıldı."
UYARI_YETER_SAYI_YOK: Final = (
    "Toplantı yeter sayısı ilanla dondurulur; yeter sayının yeri ……… basıldı."
)
UYARI_KARAR_YOK: Final = (
    "Yönetim kurulunun çağrı kararı bağlı değil; karar tarihi ve sayısı ……… basıldı."
)
UYARI_EVRAK_KAYDI_YOK: Final = "Çağrı yazısının evrak kaydı yok; yeri ……… basıldı."
UYARI_NEDEN_OKUNAMADI: Final = "Çağrı nedeni okunamadı; yeri ……… basıldı."
UYARI_GUNDEM_YOK: Final = "Gündem maddesi yok; gündem satırı ……… basıldı."
UYARI_ILAN_YOK: Final = "İlan kaydı yok; duyuru kanıtının günleri ……… basıldı."
UYARI_KANIT_EKSIK: Final = "Duyuru kanıtının günü girilmemiş kanal var; günü ……… basıldı."
UYARI_IKINCI_ILAN_YOK: Final = (
    "İkinci toplantının ayrı ilanı kayıtlı değil; duyuru kanıtı birinci ilanınkidir."
)
UYARI_ILAN_SURESI: Final = (
    "Toplantıya {kalan} gün kaldı; toplantının yeri, zamanı ve gündemi en az {en_az} gün önceden "
    "bildirilir (md. 9/3)."
)
UYARI_YUZDE_10: Final = (
    "Üyelerin başvurusu üzerine çağrı birlik başkanının imzasıyla basıldı; başkan çağırmazsa "
    "çağrıyı okul müdürü yapar."
)
UYARI_IPTAL: Final = "Genel kurul iptal edildi; belge iptalden önceki kayıtla basıldı."
UYARI_VELI_LISTESI_YOK: Final = "Veli listesi aktarılmamış; sınıf satırları ……… basıldı."
UYARI_VERI_SORUMLUSU_YOK: Final = (
    "Okul bilgilerinde veri sorumlusu girilmemiş; aydınlatma paragrafında yeri ……… basıldı."
)
UYARI_DAGILIM_YOK: Final = "Katılımın türe göre dağılımı girilmemiş; dağılım ……… basıldı."
UYARI_GOZLEMCI_YOK: Final = "Gözlemci öğrenci sayısı girilmemiş; yeri ……… basıldı."
UYARI_KATILIM_DUZELTILDI: Final = (
    "Katılım sayısı toplantıdan sonra düzeltildi; tespit toplantıda girilen sayıyla, düzeltilmiş "
    "sayı ayrı satırda basıldı."
)
UYARI_VELI_SOYADI: Final = (
    "Velinin adı veli listesinde tek alanda; son sözcük soyadı sayıldı. Soyadı birden çok sözcükse "
    "belgeyi denetleyin."
)
UYARI_BIRINCI_DAGILIM_YOK: Final = (
    "İkinci toplantının sayıları kaydedildiği için birinci toplantının türe göre dağılımı ve "
    "gözlemci sayısı programda yok; bu satırlar ……… basıldı."
)


# ---------------------------------------------------------------------------
# Genel kurul evrakı I — ortak yardımcılar
# ---------------------------------------------------------------------------
def _genel_kurul(konu: models.Model) -> GeneralAssembly:
    if not isinstance(konu, GeneralAssembly):
        raise ValueError(KONU_GECERSIZ)
    return konu


def cagri_kolu(kurul: GeneralAssembly) -> str:
    """Çağrının kolu (modül başlığı "Genel kurul evrakı I"): çağıran (`called_by`) ve md. 13/8'de
    çağrıyı yazanın rolü (`called_by_role`). Yeni açılan okulun davetçisi olağanüstü genel kurulda
    müdürün md. 9/6 çağrısıdır (`genel_kurul.mudur_yazisi_konusu`). Çağrılmamış genel kurulda
    `CAGRI_YOK`."""
    cagiran = str(kurul.called_by)
    if cagiran == AssemblyCaller.YONETIM_KURULU:
        return KOL_YK
    if cagiran == AssemblyCaller.BASKAN_VEYA_MUDUR_13_8:
        return KOL_MUDUR_13_8 if kurul.called_by_role == AccountRole.MUDUR else KOL_BASKAN_13_8
    if cagiran == AssemblyCaller.MUDUR_YENI_OKUL:
        return KOL_MUDUR_9_1 if kurul.kind == AssemblyKind.OLAGAN else KOL_MUDUR_9_6
    if cagiran == AssemblyCaller.OKUL_MUDURU:
        return KOL_MUDUR_9_6
    if cagiran == AssemblyCaller.MUDUR_25_2:
        return KOL_MUDUR_25_2
    if cagiran == AssemblyCaller.DENETLEME_KURULU:
        return KOL_DK_14_5
    if cagiran == AssemblyCaller.UYE_BASVURUSU:
        return KOL_YUZDE_10
    raise ValueError(CAGRI_YOK)


def _antet(kol: str | None = None) -> evrak.Antet:
    """Müdürün yazısı okul antedini, öteki belgeler birlik antedini taşır (tasarım §9.1-8)."""
    okul = SchoolConfig.load()
    if kol in MUDUR_KOLLARI:
        return evrak.okul_anteti(okul_adi=okul.school_name, ilce=okul.district)
    return evrak.birlik_anteti(okul_adi=okul.school_name, ilce=okul.district)


def _baslik(kod: str, kurul: GeneralAssembly, ek: str = "") -> evrak.Baslik:
    """Belgenin adı; alt satırda genel kurulun türü ve (varsa) toplantı ya da kip."""
    alt = TUR_BASLIKLARI[str(kurul.kind)]
    return evrak.Baslik(BELGE_ADLARI[kod], alt=f"{alt}{ALT_AYRAC}{ek}" if ek else alt)


def _toplanti_ani(kurul: GeneralAssembly, toplanti: str) -> datetime | None:
    return kurul.second_meeting_at if toplanti == AssemblyMeeting.IKINCI else kurul.first_meeting_at


def _ikinci_toplanti_denetimi(kurul: GeneralAssembly, toplanti: str) -> None:
    """İkinci toplantının belgesi birinci toplantıda yeter sayı sağlanamadıktan sonra üretilir."""
    if toplanti == AssemblyMeeting.IKINCI and (
        kurul.first_attendee_count is None or kurul.held_at_meeting == AssemblyMeeting.BIRINCI
    ):
        raise ValueError(IKINCI_TOPLANTI_ACILMADI)


def _kural_yeri(kurul: GeneralAssembly) -> tuple[date, OabTerm] | None:
    """Genel kurul kurallarının olay günü ve dönemi: birinci toplantı günü ve genel kurulun kural
    dönemi (U1, U7); toplantı anı yoksa `None`."""
    if kurul.first_meeting_at is None:
        return None
    return genel_kurul.yerel_gun(kurul.first_meeting_at), genel_kurul.kural_donemi(kurul)


def _ilan_en_az_gun(kurul: GeneralAssembly) -> int | None:
    """md. 9/3'ün gün sayısı (`genel_kurul.ilan_en_az_gun`); yürürlükte değer yoksa `None`."""
    yer = _kural_yeri(kurul)
    if yer is None:
        return None
    try:
        return int(kural("genel_kurul.ilan_en_az_gun", *yer))
    except YururlukteDegerYok:
        return None


def _ikinci_toplanti_en_gec_gun(kurul: GeneralAssembly) -> int | None:
    """md. 9/2'nin gün sayısı (`genel_kurul.ikinci_toplanti_en_gec_gun`); yürürlükte değer yoksa
    `None`."""
    yer = _kural_yeri(kurul)
    if yer is None:
        return None
    try:
        return int(kural("genel_kurul.ikinci_toplanti_en_gec_gun", *yer))
    except YururlukteDegerYok:
        return None


def _sayi(sayi: int | None) -> str:
    return BOS if sayi is None else str(sayi)


def _yer(kurul: GeneralAssembly, uyarilar: _Uyarilar) -> str:
    yer = " ".join(str(kurul.venue).split())
    if not yer:
        uyarilar.ekle(UYARI_YER_YOK)
        return BOS
    return yer


def _zaman_satirlari(
    kurul: GeneralAssembly, toplanti: str, uyarilar: _Uyarilar
) -> list[tuple[str, str]]:
    """Yer ve toplantıların günü; ikinci toplantının ayrı ilanında yalnız ikinci toplantı (U8)."""
    satirlar = [(SATIR_YER, _yer(kurul, uyarilar))]
    if toplanti != AssemblyMeeting.IKINCI:
        satirlar.append((SATIR_BIRINCI, _an(kurul.first_meeting_at)))
    if kurul.second_meeting_at is None:
        uyarilar.ekle(UYARI_IKINCI_TARIH_YOK)
    satirlar.append((SATIR_IKINCI, _an(kurul.second_meeting_at)))
    return satirlar


def _davet_girisi(kurul: GeneralAssembly, toplanti: str) -> evrak.Paragraf:
    kalip = IKINCI_DAVET_GIRISI if toplanti == AssemblyMeeting.IKINCI else DAVET_GIRISI
    return evrak.Paragraf(kalip.format(tur=TUR_ADLARI[str(kurul.kind)]))


def _gundem(kurul: GeneralAssembly, uyarilar: _Uyarilar) -> evrak.Tablo:
    """Çağrının gündemi: toplantıda oylamayla eklenen maddeler hariç, sırasıyla (md. 9/3, 9/4)."""
    maddeler = AgendaItem.objects.filter(assembly=kurul, added_by_vote=False).order_by(
        "order", "pk"
    )
    satirlar = tuple((str(sira), str(m.title)) for sira, m in enumerate(maddeler, start=1))
    if not satirlar:
        uyarilar.ekle(UYARI_GUNDEM_YOK)
        satirlar = ((BOS, BOS),)
    return evrak.Tablo(basliklar=GUNDEM_BASLIKLARI, satirlar=satirlar, oranlar=(1, 9))


def _toplanti_paragraflari(kurul: GeneralAssembly, toplanti: str) -> list[evrak.Blok]:
    """İkinci toplantının kuralı (birinci toplantının ilanında; md. 9/2) ve gündeme bağlılık (md. 9/6)."""
    bloklar: list[evrak.Blok] = []
    if toplanti != AssemblyMeeting.IKINCI:
        gun = _ikinci_toplanti_en_gec_gun(kurul)
        bloklar.append(evrak.Paragraf(IKINCI_TOPLANTI_CUMLESI.format(gun=_sayi(gun))))
    if kurul.kind == AssemblyKind.OLAGANUSTU:
        bloklar.append(evrak.Paragraf(GUNDEME_BAGLILIK))
    return bloklar


def _yeter_sayi(kurul: GeneralAssembly, uyarilar: _Uyarilar) -> str:
    """Dondurulmuş yeter sayı (U7; değerler ilanda kural paketinden dondurulmuştur)."""
    if kurul.quorum_required is None:
        uyarilar.ekle(UYARI_YETER_SAYI_YOK)
        return BOS
    return YETER_SAYI_DEGERI.format(
        sayi=kurul.quorum_required,
        taban=_sayi(kurul.quorum_base),
        carpan=_sayi(kurul.quorum_multiplier),
    )


def _kurum_imzasi(kol: str) -> evrak.Imza:
    """Duyurunun ve davetin kişisiz imzası (U17)."""
    return evrak.Imza(sahipler=(evrak.ImzaSahibi("", KURUM_ADLARI[kol]),))


def _cagri_imza_gunu(kurul: GeneralAssembly) -> date:
    """Çağrının imzacısının görevde olduğu gün: bugün, ama en geç birinci toplantıdan bir gün önce.
    Çağrı toplantıdan önce imzalanır; çağrı günü ayrı kaydedilmez. Toplantıdan sonra yeniden üretilen
    E05 imzacıyı toplantının değişikliklerinden önceki görevliden okur (olağanüstü genel kurulun
    seçimi eski yönetim kurulunu toplantı günü düşürür, `genel_kurul._olaganustu_eski_yk_dusur`)."""
    bugun = timezone.localdate()
    if kurul.first_meeting_at is None:
        return bugun
    return min(bugun, genel_kurul.yerel_gun(kurul.first_meeting_at) - timedelta(days=1))


def _kurulun_asillari(kurul: GeneralAssembly, organ: str) -> list[OrganMembership]:
    """Kapanacak dönemin kurulunda çağrı günü görevde olan asıllar (`selectors.gundeki_asillar`)."""
    if kurul.term is None:
        return []
    return selectors.gundeki_asillar(kurul.term, organ, _cagri_imza_gunu(kurul))


def _yk_gorevlisi(kurul: GeneralAssembly, role: str) -> OrganMembership | None:
    """Kapanacak dönemin yönetim kurulunda çağrı günü görevdeki görevli (başkan, sekreter)."""
    return next(
        (u for u in _kurulun_asillari(kurul, OrganType.YONETIM_KURULU) if u.role == role), None
    )


def _gorevli_adi(kurul: GeneralAssembly, role: str, unvan: str, uyarilar: _Uyarilar) -> str:
    uyelik = _yk_gorevlisi(kurul, role)
    if uyelik is None:
        uyarilar.ekle(UYARI_GOREV_BOS.format(gorev=unvan))
        return BOS
    return _ad(uyelik.person, uyarilar)


def _divan_imzalari(
    kurul: GeneralAssembly, uyarilar: _Uyarilar, *, adli: bool = True
) -> list[evrak.ImzaSahibi]:
    """Divan Başkanı ve Kâtip (md. 10/1-c); kişisiz kipte ad basılmaz."""
    divan = genel_kurul.kurulun_divani(kurul)
    sahipler: list[evrak.ImzaSahibi] = []
    for role, unvan in (
        (MembershipRole.BASKAN, UNVAN_DIVAN_BASKANI),
        (MembershipRole.KATIP, UNVAN_KATIP),
    ):
        uyelik = next((u for u in divan if u.role == role), None)
        if not adli:
            ad = ""
        elif uyelik is None:
            uyarilar.ekle(UYARI_GOREV_BOS.format(gorev=unvan))
            ad = BOS
        else:
            ad = _ad(uyelik.person, uyarilar)
        sahipler.append(evrak.ImzaSahibi(ad, unvan))
    return sahipler


def _yapilamadi_unvanlari(kurul: GeneralAssembly, *, gorulmus: bool) -> list[str]:
    """Toplantı yapılamadıysa imzacıların unvanları: Birlik Başkanı + Sekreter (+ "Görüldü — Okul
    Müdürü"; KE-10); yeni okulda açılışı yapan okul müdürü, "Görüldü" bloğu yok (S5 (ii)). Kişisiz
    belgede (E64) ve sonucu belli olmayan cetvelde (E08) ad basılmaz."""
    if kurul.term is None:
        return [UNVAN_ACILISI_YAPAN]
    unvanlar = [UNVAN_BIRLIK_BASKANI, UNVAN_SEKRETER]
    if gorulmus:
        unvanlar.append(UNVAN_GORULDU)
    return unvanlar


def _veli_siniflari(kurul: GeneralAssembly) -> list[tuple[str, list[ParentRoster]]]:
    """Genel kurulun veli listesi sınıf başına, sınıf ve ad sırasıyla (Türk alfabesi)."""
    satirlar = sorted(
        genel_kurul.kurulun_veli_satirlari(kurul),
        key=lambda s: (
            excel_veli.sinif_sira_anahtari(s.student_class),
            normalize.tr_sort_key("" if is_corrupt(s.full_name) else str(s.full_name)),
            s.pk,
        ),
    )
    siniflar: dict[str, list[ParentRoster]] = {}
    for satir in satirlar:
        siniflar.setdefault(str(satir.student_class), []).append(satir)
    return list(siniflar.items())


def _veli_adi(satir: ParentRoster, uyarilar: _Uyarilar) -> str:
    """Velinin adı "Ad SOYAD" biçiminde (personel ve birlik kişileri gibi; F1c `gorev_evraki._ad`).
    Veli listesi adı tek alanda tutar (T5): son sözcük soyadı sayılır; üç ya da daha çok sözcüklü adda
    bu bölme tahmindir, basım uyarısı verilir (`gorev_evraki._mudur_adi`'nin kalıbı)."""
    if is_corrupt(satir.full_name):
        uyarilar.ekle(UYARI_AD_OKUNAMADI)
        return BOS
    ad = " ".join(str(satir.full_name).split())
    if not ad:
        return BOS
    adlar, _, soyad = ad.rpartition(" ")
    if len(ad.split()) >= 3:
        uyarilar.ekle(UYARI_VELI_SOYADI)
    return evrak.ad_soyad(adlar, soyad) if adlar else evrak.ad_soyad(soyad, "")


def _personel() -> list[Personnel]:
    """Genel kurula katılan öğretmen ve idareciler (md. 7/1; `Personnel`), ada göre."""
    return personnel_sorted(
        Personnel.objects.filter(
            is_active=True, member_kind__in=(MemberKind.OGRETMEN, MemberKind.YONETICI)
        )
    )


def _bos_satirlar(bas: int, adet: int, sutun: int, sinif: str = "") -> list[tuple[str, ...]]:
    """`bas` numaralı satırdan başlayan `adet` boş satır (sınıf sütunu varsa dolu)."""
    satirlar: list[tuple[str, ...]] = []
    for sira in range(bas, bas + adet):
        hucreler = [str(sira)] + [""] * (sutun - 1)
        if sinif:
            hucreler[2] = sinif
        satirlar.append(tuple(hucreler))
    return satirlar


# ---------------------------------------------------------------------------
# E05 — genel kurul toplantı çağrısı ve gündemi
# ---------------------------------------------------------------------------
def _cagiran_metni(kurul: GeneralAssembly, kol: str) -> str:
    if kol == KOL_YK:
        return CAGIRAN_YK_OLAGAN if kurul.kind == AssemblyKind.OLAGAN else CAGIRAN_YK_OLAGANUSTU
    return CAGIRAN_METINLERI[kol]


def _cagri_nedeni(kurul: GeneralAssembly, uyarilar: _Uyarilar) -> str:
    if is_corrupt(kurul.call_reason):
        uyarilar.ekle(UYARI_NEDEN_OKUNAMADI)
        return BOS
    return " ".join(str(kurul.call_reason).split()) or BOS


def _cagri_bagi_satirlari(
    kurul: GeneralAssembly, kol: str, uyarilar: _Uyarilar
) -> list[tuple[str, str]]:
    """Çağrının dayanağı: yönetim kurulu kararı (S1 (a)), başvuru sayıları (U12), Denetleme Kurulunun
    raporu (md. 14/5) ve çağrı yazısının evrak kaydı (müdürün yazısında ⁷)."""
    satirlar: list[tuple[str, str]] = []
    if kol == KOL_YK:
        karar = kurul.call_decision
        if karar is None:
            uyarilar.ekle(UYARI_KARAR_YOK)
            satirlar.append((SATIR_KARAR, BOS))
        else:
            no = BOS if karar.decision_no is None else str(karar.decision_no)
            satirlar.append(
                (SATIR_KARAR, KARAR_DEGERI.format(tarih=_gun(karar.decision_date), no=no))
            )
    if kol == KOL_YUZDE_10:
        satirlar.append(
            (
                SATIR_BASVURU,
                BASVURU_DEGERI.format(
                    basvuran=_sayi(kurul.member_application_count),
                    uye=_sayi(kurul.member_count_declared),
                ),
            )
        )
    if kol == KOL_DK_14_5:
        rapor = kurul.call_audit_report
        satirlar.append((SATIR_DK_RAPORU, BOS if rapor is None else _gun(rapor.report_date)))
    if kol in MUDUR_KOLLARI or kol in (KOL_DK_14_5, KOL_YUZDE_10):
        yazi = kurul.call_document
        if yazi is None:
            uyarilar.ekle(UYARI_EVRAK_KAYDI_YOK)
            satirlar.append((SATIR_EVRAK, BOS))
        else:
            satirlar.append((SATIR_EVRAK, EVRAK_DEGERI.format(yil=yazi.year, no=yazi.record_no)))
    return satirlar


def _ilan(kurul: GeneralAssembly, toplanti: str, uyarilar: _Uyarilar) -> Announcement | None:
    """Toplantının ilanı: birinci toplantıda ilk ilan; ikinci toplantıda ayrı ilanı, yoksa ilk ilan."""
    duyurular = genel_kurul.kurulun_duyurulari(kurul)
    if not duyurular:
        uyarilar.ekle(UYARI_ILAN_YOK)
        return None
    if toplanti == AssemblyMeeting.IKINCI:
        if len(duyurular) > 1:
            return duyurular[1]
        uyarilar.ekle(UYARI_IKINCI_ILAN_YOK)
    return duyurular[0]


def _kanit_tablosu(kurul: GeneralAssembly, toplanti: str, uyarilar: _Uyarilar) -> evrak.Tablo:
    """Duyuru kanıtı (tasarım §9.6 E05): üç kanalın günü ve bağlayıcı ilan günü (U9); görev unvanı
    sütunu elle doldurulur (`KANIT_BASLIKLARI`); kişi adı yok."""
    duyuru = _ilan(kurul, toplanti, uyarilar)
    gunler = (
        (None, None, None)
        if duyuru is None
        else (duyuru.distributed_written_on, duyuru.posted_board_on, duyuru.published_web_on)
    )
    if duyuru is not None and None in gunler:
        uyarilar.ekle(UYARI_KANIT_EKSIK)
    girilmis = [g for g in gunler if g is not None]
    satirlar = (
        *(
            (kanal, _gun(gun), "")
            for kanal, gun in zip((KANAL_ELDEN, KANAL_PANO, KANAL_INTERNET), gunler, strict=True)
        ),
        (KANIT_ILAN_GUNU, _gun(max(girilmis) if girilmis else None), ""),
    )
    return evrak.Tablo(basliklar=KANIT_BASLIKLARI, satirlar=satirlar, oranlar=(5, 2, 4))


def _ilan_suresi_uyarisi(
    kurul: GeneralAssembly, toplanti: str, en_az: int | None, uyarilar: _Uyarilar
) -> None:
    """Toplantıya ilan süresinden az gün kala basımda uyarı (tasarım §9.6 E05; md. 9/3)."""
    an = _toplanti_ani(kurul, toplanti)
    if an is None or en_az is None:
        return
    kalan = (genel_kurul.yerel_gun(an) - timezone.localdate()).days
    if 0 <= kalan < en_az:
        uyarilar.ekle(UYARI_ILAN_SURESI.format(kalan=kalan, en_az=en_az))


def _e05_imzasi(kurul: GeneralAssembly, kol: str, uyarilar: _Uyarilar) -> evrak.Imza:
    """Çağırana göre imza (tasarım §9.3, §9.6 E05; MB-3): müdürün kollarında Okul Müdürü ("Görüldü"
    yok); öteki kollarda çağıran ve "Görüldü — Okul Müdürü (md. 27/1)"."""
    if kol in MUDUR_KOLLARI:
        return evrak.Imza(sahipler=(evrak.ImzaSahibi(_mudur_adi(uyarilar), UNVAN_OKUL_MUDURU),))
    sahipler: list[evrak.ImzaSahibi]
    if kol == KOL_YK:
        sahipler = [
            evrak.ImzaSahibi(
                _gorevli_adi(kurul, MembershipRole.BASKAN, UNVAN_BIRLIK_BASKANI, uyarilar),
                UNVAN_YK_ADINA_BASKAN,
            ),
            evrak.ImzaSahibi(
                _gorevli_adi(kurul, MembershipRole.SEKRETER, UNVAN_SEKRETER, uyarilar),
                UNVAN_SEKRETER,
            ),
        ]
    elif kol == KOL_DK_14_5:
        asillar = sorted(
            _kurulun_asillari(kurul, OrganType.DENETLEME_KURULU),
            key=lambda u: u.role != MembershipRole.BASKAN,
        )
        sahipler = [
            evrak.ImzaSahibi(
                _ad(u.person, uyarilar),
                UNVAN_DK_BASKANI if u.role == MembershipRole.BASKAN else UNVAN_DK_UYESI,
            )
            for u in asillar
        ]
        if not sahipler:
            uyarilar.ekle(UYARI_GOREV_BOS.format(gorev=UNVAN_DK_UYESI))
            sahipler = [evrak.ImzaSahibi(BOS, UNVAN_DK_UYESI)]
    else:  # başkanın md. 13/8 çağrısı; üyelerin başvurusunda çağrıyı başkan yapar (KE-11)
        if kol == KOL_YUZDE_10:
            uyarilar.ekle(UYARI_YUZDE_10)
        sahipler = [
            evrak.ImzaSahibi(
                _gorevli_adi(kurul, MembershipRole.BASKAN, UNVAN_BIRLIK_BASKANI, uyarilar),
                UNVAN_BIRLIK_BASKANI,
            )
        ]
    sahipler.append(evrak.ImzaSahibi(_mudur_adi(uyarilar), UNVAN_GORULDU_E05))
    return evrak.Imza(sahipler=tuple(sahipler))


def e05_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E05'in içerik modeli ve basım uyarıları (modül başlığı "Genel kurul evrakı I")."""
    kurul = _genel_kurul(konu)
    kol = cagri_kolu(kurul)
    toplanti = secim.toplanti
    _ikinci_toplanti_denetimi(kurul, toplanti)
    uyarilar = _Uyarilar()
    if kurul.status == AssemblyStatus.IPTAL:
        uyarilar.ekle(UYARI_IPTAL)
    bilgi: list[tuple[str, str]] = [
        (SATIR_TUR, TUR_BASLIKLARI[str(kurul.kind)]),
        (SATIR_CAGIRAN, _cagiran_metni(kurul, kol)),
    ]
    if kurul.kind == AssemblyKind.OLAGANUSTU:
        bilgi.append((SATIR_CAGRI_NEDENI, _cagri_nedeni(kurul, uyarilar)))
    bilgi += _cagri_bagi_satirlari(kurul, kol, uyarilar)
    bilgi += _zaman_satirlari(kurul, toplanti, uyarilar)
    bilgi.append((SATIR_YETER_SAYI, _yeter_sayi(kurul, uyarilar)))
    en_az = _ilan_en_az_gun(kurul)
    gundem = _gundem(kurul, uyarilar)
    kanit = _kanit_tablosu(kurul, toplanti, uyarilar)
    imza = _e05_imzasi(kurul, kol, uyarilar)
    _ilan_suresi_uyarisi(kurul, toplanti, en_az, uyarilar)
    belge = evrak.Belge(
        kod=E05,
        antet=_antet(kol),
        bloklar=(
            _baslik(E05, kurul, TOPLANTI_ADLARI[toplanti]),
            _davet_girisi(kurul, toplanti),
            evrak.Paragraf(ILAN_CUMLESI.format(gun=_sayi(en_az))),
            evrak.Tablo(basliklar=KONU_BILGI, satirlar=tuple(bilgi), oranlar=(2, 3)),
            evrak.AltBaslik(GUNDEM_BOLUMU),
            gundem,
            *_toplanti_paragraflari(kurul, toplanti),
            evrak.AltBaslik(KANIT_BOLUMU),
            kanit,
            imza,
            evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
        ),
    )
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# E06 — genel kurul duyurusu (kişisiz)
# ---------------------------------------------------------------------------
def e06_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E06'nın içerik modeli: kişi adı yok, çağrı nedeni de yok (tasarım §9.1-5); imza çağırana göre
    kurum adı (U17)."""
    kurul = _genel_kurul(konu)
    kol = cagri_kolu(kurul)
    toplanti = secim.toplanti
    _ikinci_toplanti_denetimi(kurul, toplanti)
    uyarilar = _Uyarilar()
    if kurul.status == AssemblyStatus.IPTAL:
        uyarilar.ekle(UYARI_IPTAL)
    bilgi = _zaman_satirlari(kurul, toplanti, uyarilar)
    belge = evrak.Belge(
        kod=E06,
        antet=_antet(kol),
        bloklar=(
            _baslik(E06, kurul, TOPLANTI_ADLARI[toplanti]),
            _davet_girisi(kurul, toplanti),
            evrak.Tablo(basliklar=KONU_BILGI, satirlar=tuple(bilgi), oranlar=(2, 3)),
            evrak.AltBaslik(GUNDEM_BOLUMU),
            _gundem(kurul, uyarilar),
            *_toplanti_paragraflari(kurul, toplanti),
            _kurum_imzasi(kol),
        ),
    )
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# E07 — üyelere elden yazılı davet (kişisiz kip) ve sınıf teslim çizelgesi (adlı kip)
# ---------------------------------------------------------------------------
def _aydinlatma(uyarilar: _Uyarilar) -> list[evrak.Blok]:
    """Kısa aydınlatma paragrafı (KM-6; tasarım §9.1-5): onaylı veli metninin amaç, veri sorumlusu ve
    haklar cümleleri ile tam metnin yeri."""
    veri_sorumlusu = " ".join(str(SchoolConfig.load().data_controller_text or "").split())
    if not veri_sorumlusu:
        uyarilar.ekle(UYARI_VERI_SORUMLUSU_YOK)
        veri_sorumlusu = BOS
    return [
        evrak.AltBaslik(E07_AYDINLATMA_BASLIGI),
        evrak.Paragraf(VELI_AYDINLATMA_AMACI),
        evrak.Paragraf(f"{AYDINLATMA_VERI_SORUMLUSU_ETIKETI} {veri_sorumlusu}"),
        evrak.Paragraf(AYDINLATMA_HAKLARINIZ),
        evrak.Paragraf(E07_TAM_METIN_YERI),
    ]


def e07_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E07'nin kişisiz kipi: davet mektubu ("Sayın Veli"), kısa aydınlatma paragrafı ve sınıf başına
    davet adedi (sınıf ve sayı; ad yok). İmza çağırana göre kurum adı (U17, S5 (ii))."""
    kurul = _genel_kurul(konu)
    kol = cagri_kolu(kurul)
    birinci = AssemblyMeeting.BIRINCI
    uyarilar = _Uyarilar()
    if kurul.status == AssemblyStatus.IPTAL:
        uyarilar.ekle(UYARI_IPTAL)
    siniflar = _veli_siniflari(kurul)
    adetler: list[tuple[str, str, str, str]] = [
        (sinif, str(len(satirlar)), "", "") for sinif, satirlar in siniflar
    ]
    if adetler:
        adetler.append((TOPLAM, str(sum(len(s) for _, s in siniflar)), "", ""))
    else:
        uyarilar.ekle(UYARI_VELI_LISTESI_YOK)
        adetler.append((BOS, BOS, "", ""))
    bilgi = _zaman_satirlari(kurul, birinci, uyarilar)
    belge = evrak.Belge(
        kod=E07,
        antet=_antet(kol),
        bloklar=(
            _baslik(E07, kurul),
            evrak.Paragraf(SAYIN_VELI),
            _davet_girisi(kurul, birinci),
            evrak.Tablo(basliklar=KONU_BILGI, satirlar=tuple(bilgi), oranlar=(2, 3)),
            evrak.AltBaslik(GUNDEM_BOLUMU),
            _gundem(kurul, uyarilar),
            *_toplanti_paragraflari(kurul, birinci),
            *_aydinlatma(uyarilar),
            _kurum_imzasi(kol),
            evrak.SayfaSonu(),
            evrak.AltBaslik(E07_ADET_BOLUMU),
            evrak.Tablo(basliklar=ADET_BASLIKLARI, satirlar=tuple(adetler), oranlar=(2, 2, 5, 4)),
        ),
    )
    return belge, tuple(uyarilar.liste)


def e07_adli_belgesi(kurul: GeneralAssembly, toplanti: str) -> AdliIcerik:
    """E07'nin adlı kipi: sınıf teslim çizelgesi (veli adları; sınıf başına sayfa, teslim eden sınıf
    rehber öğretmeni). Satır sayısı veli satırıdır. Yalnız `adli_uret_ve_ver` çağırır."""
    kol = cagri_kolu(kurul)
    uyarilar = _Uyarilar()
    bloklar: list[evrak.Blok] = [
        _baslik(E07, kurul, E07_CIZELGE_ALT),
        evrak.Paragraf(E07_CIZELGE_GIRISI),
    ]
    siniflar = _veli_siniflari(kurul)
    satir_sayisi = sum(len(satirlar) for _, satirlar in siniflar)
    bolumler: list[tuple[str, tuple[tuple[str, ...], ...]]] = [
        (
            SINIF_BOLUMU.format(sinif=sinif),
            tuple(
                (str(sira), _veli_adi(satir, uyarilar), "", "")
                for sira, satir in enumerate(satirlar, start=1)
            ),
        )
        for sinif, satirlar in siniflar
    ]
    if not bolumler:
        uyarilar.ekle(UYARI_VELI_LISTESI_YOK)
        bolumler.append((SINIF_BOLUMU.format(sinif=BOS), ((BOS, BOS, "", ""),)))
    for sira, (baslik, satirlar) in enumerate(bolumler):
        if sira:
            bloklar.append(evrak.SayfaSonu())
        bloklar += [
            evrak.AltBaslik(baslik),
            evrak.Tablo(basliklar=CIZELGE_BASLIKLARI, satirlar=satirlar, oranlar=(1, 6, 3, 4)),
            evrak.Imza(sahipler=(evrak.ImzaSahibi("", UNVAN_REHBER),)),
        ]
    bloklar.append(evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU))
    belge = evrak.Belge(kod=E07, antet=_antet(kol), bloklar=tuple(bloklar))
    return AdliIcerik(belge=belge, satir_sayisi=satir_sayisi, uyarilar=tuple(uyarilar.liste))


# ---------------------------------------------------------------------------
# E08 — genel kurul katılım cetveli (boş satırlı kip ve adlı kip)
# ---------------------------------------------------------------------------
def _paraf(kurul: GeneralAssembly, uyarilar: _Uyarilar, *, adli: bool) -> evrak.Imza:
    """Sayfa parafı (tasarım §9.6 E08): genel kurul yapıldıysa Divan Başkanı + Kâtip, yapılamadıysa
    Birlik Başkanı + Sekreter (yeni okulda açılışı yapan okul müdürü, S5 (ii)). Boş satırlı kipte ad
    basılmaz (U14). Cetvel toplantıdan önce basılır (tasarım §7.1 ilan satırı); genel kurul yapılmadan
    (toplantıdan önce ya da birinci toplantıda yeter sayı sağlanamayınca) toplantının sonucu belli
    değildir: iki kolun unvanları koşuluyla, adsız basılır (`PARAF_YAPILDIYSA`,
    `PARAF_YAPILAMADIYSA`)."""
    if kurul.held_at_meeting:
        return evrak.Imza(sahipler=tuple(_divan_imzalari(kurul, uyarilar, adli=adli)))
    return evrak.Imza(
        sahipler=(
            *(
                evrak.ImzaSahibi("", PARAF_YAPILDIYSA.format(unvan=unvan))
                for unvan in (UNVAN_DIVAN_BASKANI, UNVAN_KATIP)
            ),
            *(
                evrak.ImzaSahibi("", PARAF_YAPILAMADIYSA.format(unvan=unvan))
                for unvan in _yapilamadi_unvanlari(kurul, gorulmus=False)
            ),
        )
    )


def _e08(kurul: GeneralAssembly, *, adli: bool) -> tuple[evrak.Belge, tuple[str, ...], int]:
    """E08'in iki kipinin ortak kurucusu: (belge, basım uyarıları, veli satırı sayısı)."""
    uyarilar = _Uyarilar()
    if kurul.status == AssemblyStatus.IPTAL:
        uyarilar.ekle(UYARI_IPTAL)
    paraf = _paraf(kurul, uyarilar, adli=adli)
    bolumler: list[tuple[str, tuple[str, ...], tuple[int, ...], list[tuple[str, ...]]]] = []
    veli_sayisi = 0
    veli_oranlari = (1, 6, 2, 4)
    for sinif, satirlar in _veli_siniflari(kurul):
        tablo: list[tuple[str, ...]] = [
            (str(sira), _veli_adi(satir, uyarilar) if adli else "", sinif, "")
            for sira, satir in enumerate(satirlar, start=1)
        ]
        tablo += _bos_satirlar(len(satirlar) + 1, EK_BOS_SATIR, len(VELI_BASLIKLARI), sinif)
        veli_sayisi += len(satirlar)
        bolumler.append((VELI_BOLUMU.format(sinif=sinif), VELI_BASLIKLARI, veli_oranlari, tablo))
    if not bolumler:
        uyarilar.ekle(UYARI_VELI_LISTESI_YOK)
        bolumler.append(
            (
                VELI_BOLUMU_SINIFSIZ,
                VELI_BASLIKLARI,
                veli_oranlari,
                _bos_satirlar(1, BOS_VELI_SATIRI, len(VELI_BASLIKLARI)),
            )
        )
    personel = _personel()
    personel_tablosu: list[tuple[str, ...]] = []
    if adli:
        for sira, kisi in enumerate(personel, start=1):
            if is_corrupt(kisi.first_name) or is_corrupt(kisi.last_name):
                uyarilar.ekle(UYARI_AD_OKUNAMADI)
                ad = BOS
            else:
                ad = evrak.ad_soyad(str(kisi.first_name), str(kisi.last_name))
            personel_tablosu.append((str(sira), ad, PERSONEL_GOREVLERI[str(kisi.member_kind)], ""))
    else:
        personel_tablosu = _bos_satirlar(1, len(personel), len(PERSONEL_BASLIKLARI))
    personel_tablosu += _bos_satirlar(
        len(personel_tablosu) + 1, EK_BOS_SATIR, len(PERSONEL_BASLIKLARI)
    )
    bolumler += [
        (PERSONEL_BOLUMU, PERSONEL_BASLIKLARI, (1, 6, 3, 4), personel_tablosu),
        (
            DIGER_BOLUMU,
            DIGER_BASLIKLARI,
            (1, 6, 3, 4),
            _bos_satirlar(1, EK_BOS_SATIR, len(DIGER_BASLIKLARI)),
        ),
        (
            GOZLEMCI_BOLUMU,
            GOZLEMCI_BASLIKLARI,
            (1, 8, 4),
            _bos_satirlar(1, GOZLEMCI_SATIRI, len(GOZLEMCI_BASLIKLARI)),
        ),
    ]
    bloklar: list[evrak.Blok] = [
        _baslik(E08, kurul),
        evrak.Tablo(
            basliklar=KONU_BILGI,
            satirlar=tuple(_zaman_satirlari(kurul, AssemblyMeeting.BIRINCI, uyarilar)),
            oranlar=(2, 3),
        ),
        evrak.Paragraf(E08_GIRIS),
    ]
    for sira, (baslik, basliklar, oranlar, bolum_satirlari) in enumerate(bolumler):
        if sira:
            bloklar.append(evrak.SayfaSonu())
        bloklar += [
            evrak.AltBaslik(baslik),
            evrak.Tablo(basliklar=basliklar, satirlar=tuple(bolum_satirlari), oranlar=oranlar),
            paraf,
        ]
    if adli:
        bloklar.append(evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU))
    belge = evrak.Belge(kod=E08, antet=_antet(), bloklar=tuple(bloklar))
    return belge, tuple(uyarilar.liste), veli_sayisi


def e08_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E08'in boş satırlı kipi: hiçbir ad taşımaz (veli, personel, parafta da; U14); saklanır."""
    belge, uyarilar, _ = _e08(_genel_kurul(konu), adli=False)
    return belge, uyarilar


def e08_adli_belgesi(kurul: GeneralAssembly, toplanti: str) -> AdliIcerik:
    """E08'in adlı kipi: veli ve personel adlarıyla; yalnız `adli_uret_ve_ver` çağırır (R9). Toplantı
    almaz (8. adımın en dar seçimi): parafı genel kurulun durumundandır (`_paraf`)."""
    belge, uyarilar, satir_sayisi = _e08(kurul, adli=True)
    return AdliIcerik(belge=belge, satir_sayisi=satir_sayisi, uyarilar=uyarilar)


# ---------------------------------------------------------------------------
# E64 — genel kurul yeter sayı tespit tutanağı (kişisiz; KE-21)
# ---------------------------------------------------------------------------
def _dagilim_satirlari(
    kurul: GeneralAssembly, kayipli: bool, uyarilar: _Uyarilar
) -> tuple[tuple[str, str], ...]:
    """Katılımın türe göre dağılımı (`AttendanceKind` sırasıyla); girilmemişse ya da birinci
    toplantınınki ikinci toplantının sayılarıyla değiştirildiyse "………" (modül başlığı)."""
    dagilim = dict(kurul.attendance_by_kind or {})
    if kayipli or not dagilim:
        if not kayipli:
            uyarilar.ekle(UYARI_DAGILIM_YOK)
        return tuple((str(tur.label), BOS) for tur in AttendanceKind)
    return tuple((str(tur.label), str(dagilim.get(tur.value, 0))) for tur in AttendanceKind)


def e64_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E64'ün içerik modeli (modül başlığı): toplantının sayıları ve sonucu; imza sonuca göre, adsız
    (KE-21)."""
    kurul = _genel_kurul(konu)
    toplanti = secim.toplanti
    ikinci = toplanti == AssemblyMeeting.IKINCI
    katilan = kurul.second_attendee_count if ikinci else kurul.first_attendee_count
    if (
        katilan is None
        or kurul.quorum_required is None
        or (ikinci and kurul.held_at_meeting != AssemblyMeeting.IKINCI)
    ):
        raise ValueError(TOPLANTI_YAPILMADI)
    uyarilar = _Uyarilar()
    # Tespit toplantıdakidir: sonuç (`held_at_meeting`) toplantıda girilen sayıdan hesaplandı. Sonradan
    # düzeltilen sayı ayrı satırdadır, uyarıyla (`katilim_duzelt` durumu değiştirmez; tasarım §5.2.3).
    alan = "second_attendee_count" if ikinci else "first_attendee_count"
    toplantidaki = genel_kurul.ilk_girilen_deger(kurul, alan)
    toplantidaki = katilan if toplantidaki is None else toplantidaki
    saglandi = ikinci or kurul.held_at_meeting == AssemblyMeeting.BIRINCI
    # Birinci toplantının dağılımı ve gözlemcisi ikinci toplantının kaydıyla değişir (modül başlığı).
    kayipli = not ikinci and kurul.second_attendee_count is not None
    if kayipli:
        uyarilar.ekle(UYARI_BIRINCI_DAGILIM_YOK)
        gozlemci = BOS
    elif kurul.observer_count is None:
        uyarilar.ekle(UYARI_GOZLEMCI_YOK)
        gozlemci = BOS
    else:
        gozlemci = str(kurul.observer_count)
    if ikinci:
        alt, sonuc = ALT_COGUNLUK_ARANMAZ, SONUC_COGUNLUK_ARANMAZ
    elif saglandi:
        alt, sonuc = ALT_SAGLANDI, SONUC_SAGLANDI
    else:
        alt, sonuc = ALT_SAGLANAMADI, SONUC_SAGLANAMADI
    bilgi: list[tuple[str, str]] = [
        (SATIR_TUR, TUR_BASLIKLARI[str(kurul.kind)]),
        (SATIR_TOPLANTI, TOPLANTI_ADLARI[toplanti]),
        (
            SATIR_GUN_YER,
            GUN_YER_DEGERI.format(
                an=_an(_toplanti_ani(kurul, toplanti)), yer=_yer(kurul, uyarilar)
            ),
        ),
        (SATIR_MEVCUT, _sayi(kurul.student_count_snapshot)),
        (SATIR_YETER_SAYI, _yeter_sayi(kurul, uyarilar)),
        (SATIR_KATILAN, str(toplantidaki)),
    ]
    if toplantidaki != katilan:
        uyarilar.ekle(UYARI_KATILIM_DUZELTILDI)
        bilgi.append((SATIR_KATILAN_DUZELTILMIS, str(katilan)))
    bilgi += [(SATIR_GOZLEMCI, gozlemci), (SATIR_SONUC, sonuc)]
    if not saglandi:
        if kurul.second_meeting_at is None:
            uyarilar.ekle(UYARI_IKINCI_TARIH_YOK)
        bilgi.append((SATIR_IKINCI, _an(kurul.second_meeting_at)))
    # Kişisiz (KE-21): imzalarda yalnız unvan. Müdürün çağırdığı genel kurulda "Görüldü" yok (tasarım
    # §9.3 müdür blokları: "Görüldü (müdür çağırmadıysa)"; yeni okulda S5 (ii)).
    if saglandi:
        imza = evrak.Imza(sahipler=tuple(_divan_imzalari(kurul, uyarilar, adli=False)))
    else:
        gorulmus = cagri_kolu(kurul) not in MUDUR_KOLLARI
        imza = evrak.Imza(
            sahipler=tuple(
                evrak.ImzaSahibi("", unvan)
                for unvan in _yapilamadi_unvanlari(kurul, gorulmus=gorulmus)
            )
        )
    belge = evrak.Belge(
        kod=E64,
        antet=_antet(),
        bloklar=(
            _baslik(E64, kurul, alt),
            evrak.Paragraf(E64_GIRIS.format(tur=TUR_ADLARI[str(kurul.kind)])),
            evrak.Tablo(basliklar=KONU_BILGI, satirlar=tuple(bilgi), oranlar=(2, 3)),
            evrak.AltBaslik(DAGILIM_BOLUMU),
            evrak.Tablo(
                basliklar=DAGILIM_BASLIKLARI,
                satirlar=_dagilim_satirlari(kurul, kayipli, uyarilar),
                oranlar=(3, 1),
            ),
            imza,
        ),
    )
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# Genel kurul evrakı II — sabitler (sözlük §1 "Genel kurul evrakı (F2)")
# ---------------------------------------------------------------------------
#: Genel kurulun yapıldığı durumlar (tutanak, teslim tutanağı, resmî yazı ve sonuç bildirimi).
_YAPILMIS: Final = (AssemblyStatus.YAPILDI, AssemblyStatus.TUTANAK_TAMAM)
GENEL_KURUL_YAPILMADI: Final = "Genel kurul yapılmadan bu evrak üretilmez."
IBRA_EDILMEDIKCE_URETILMEZ: Final = (
    "Yönetim kurulunun hesapları ibra edilmedikçe bu evrak üretilmez (md. 11/1-ç)."
)
MUHATAP_GECERSIZ: Final = "Bu evrakın muhatabı yoktur."

#: Koltuk ve organ adları (gorev_evraki ile aynı).
ASIL: Final = "Asıl"
YEDEK: Final = "Yedek"
KOLTUK_ADLARI: Final[dict[str, str]] = {SeatType.ASIL: ASIL, SeatType.YEDEK: YEDEK}

#: E09: aday listeleri (md. 10/1-d, 11/1-a, b, 12/1, 12/4; tasarım §9.3 "Aday listeleri").
E09_GIRIS: Final = (
    "Yönetim kurulunun üyeleri ile Denetleme Kurulunun veli koltuğundaki üyesi genel kurulca asıl ve "
    "yedek olarak liste hâlinde, açık oyla seçilir (Millî Eğitim Bakanlığı Okul-Aile Birliği "
    "Yönetmeliği (Yönetmelik) md. 10/1-d, 11/1-a, b)."
)
YK_ADAY_BOLUMU: Final = "A. Yönetim kurulu adayları (md. 11/1-a, 12/1)"
DK_ADAY_BOLUMU: Final = "B. Denetleme Kurulu veli koltuğu adayları (md. 11/1-b, 14/1)"
YK_ADAY_BASLIKLARI: Final = (
    "Sıra",
    "Adı ve soyadı",
    "Asıl ya da yedek",
    "Kişi türü",
    "Önceki seçilme sayısı (md. 12/4)",
)
DK_ADAY_BASLIKLARI: Final = ("Sıra", "Adı ve soyadı", "Asıl ya da yedek", "Kişi türü")
#: Denetleme Kurulunun öğretmen koltukları genel kurulun oylamasına girmez (tasarım §9.3; md. 11/1-b,
#: 14/1); sayılar kural paketinden (`denetleme_kurulu.koltuklar`).
DK_OGRETMEN_BILGISI: Final = (
    "Denetleme Kurulunun {asil} asıl ve {yedek} yedek öğretmen üyesi öğretmenler kurulunca seçilir; "
    "genel kurulun oylamasına girmez (md. 11/1-b, 14/1)."
)

#: E10: genel kurul toplantı tutanağı (md. 9/2-6, 10/1, 11/1; GNL-OAB-FR-004; OYS `tutanak.html`).
E10_GIRIS: Final = (
    "Okul-Aile Birliğinin {tur} genel kurulu aşağıdaki bilgilerle toplanmış ve gündem maddelerini "
    "görüşmüştür (Millî Eğitim Bakanlığı Okul-Aile Birliği Yönetmeliği (Yönetmelik) md. 10/1, 11/1)."
)
E10_BOLUMLER: Final = (
    "A. Toplantı",
    "B. Açılış ve divan (md. 10/1-b, c)",
    "C. Gündem maddeleri ve sonuçları (md. 9/4, 11/1)",
    "D. İbra (md. 11/1-c, ç)",
    "E. Seçim sonuçları (md. 10/1-d, 11/1-a, b)",
    "F. Kapanış (md. 10/1-ç)",
)
SATIR_ILAN: Final = "İlan günü (md. 9/3)"
SATIR_BIRINCI_SONUCU: Final = "Birinci toplantı"
BIRINCI_SONUCU_DEGERI: Final = "{an} · toplantı yeter sayısı sağlanamadı ({katilan} katılan)"
COGUNLUK_ARANMAZ_DEGERI: Final = "İkinci toplantıda çoğunluk aranmaz (md. 9/2)"
SATIR_ACILIS: Final = "Açılış"
ACILIS_DEGERI: Final = "Toplantının açılışını okul müdürü yaptı (md. 10/1-b)."
SONUC_BASLIKLARI: Final = ("Sıra", "Gündem maddesi", "Sonuç")
SONUC_KABUL: Final = "Kabul edildi ({oylar})"
SONUC_RET: Final = "Reddedildi ({oylar})"
SONUC_GORUSULDU: Final = "Görüşüldü"
SONUC_CIKARILDI: Final = "Gündemden çıkarıldı (md. 9/4)"
SONUC_IBRA: Final = "Görüşüldü; ibra oylaması D bölümündedir"
#: İki kurulun ibrası da "görüşülmedi" (`genel_kurul.ibra_yaz` maddenin sonucunu boş bırakır; sonuç
#: kurulun `discharge_yk` ve `discharge_dk` alanlarındadır).
SONUC_IBRA_GORUSULMEDI: Final = "Görüşülmedi; ibra satırları D bölümündedir"
SONUC_SECIM: Final = "Görüşüldü; seçim sonuçları E bölümündedir"
#: Tahmini bütçe F2'de yalnız "görüşüldü" ve ekin adıdır, tutar basılmaz (plan F2 §7 U22; md. 11/1-d
#: "görüşmek"). Oyla girilmiş sonuç da (kabul ya da ret) E10'da ve E13'te böyle basılır: iki belge aynı
#: kayıttan aynı sonucu verir (tasarım §9.1-3).
SONUC_BUTCE: Final = "Görüşüldü; ek: Tahmini bütçe"
SONUC_METNI: Final = "{sonuc} · {metin}"
OYLAR_DEGERI: Final = "kabul {kabul}, ret {ret}"
SALONDAKI_DEGERI: Final = "; oylamada salonda bulunan {salon}"
GUNDEM_DEGISIKLIGI_BOLUMU: Final = "Gündem değişikliği (md. 9/4)"
DEGISIKLIK_BASLIKLARI: Final = ("Gündem maddesi", "Değişiklik", "Oylama")
DEGISIKLIK_EKLENDI: Final = "Gündeme eklendi"
DEGISIKLIK_CIKARILDI: Final = "Gündemden çıkarıldı"
GUNDEM_DEGISMEDI: Final = "Duyurulan gündemde değişiklik yapılmadı (md. 9/4)."
SATIR_YK_RAPORU: Final = "Yönetim kurulu faaliyet raporunu okuyan"
SATIR_DK_RAPORU_OKUYAN: Final = "Denetleme Kurulu raporunu okuyan"
SATIR_BUTCEYI_SUNAN: Final = "Tahmini bütçeyi sunan"
IBRA_BASLIKLARI: Final = ("Kurul", "Sonuç", "Kabul", "Ret", "Oylamada salonda bulunan")
KURUL_YK: Final = "Yönetim kurulu"
KURUL_DK: Final = "Denetleme Kurulu"
#: Md. 11/1-ç'nin teslim aldığı kurullar, genel kurulun türüne ve gündemde (çıkarılmamış) seçim maddesi
#: olup olmadığına göre (yönetim kurulu seçildi mi, Denetleme Kurulu seçildi mi): olağanüstü genel kurul
#: Denetleme Kuruluna seçim yapmaz (kullanıcı kararı S10 (a)), teslim görevdeki kurula yapılır;
#: yönetim kurulu seçilmediyse görevdeki yönetim kuruluna.
TESLIM_ALANLAR: Final[Mapping[tuple[bool, bool], str]] = {
    (True, True): "seçilen yeni yönetim kuruluna ve yeni Denetleme Kuruluna",
    (True, False): "seçilen yeni yönetim kuruluna ve görevdeki Denetleme Kuruluna",
    (False, True): "görevdeki yönetim kuruluna ve seçilen yeni Denetleme Kuruluna",
    (False, False): "görevdeki yönetim kuruluna ve Denetleme Kuruluna",
}
IBRA_EDILMEDI_PARAGRAFI: Final = (
    "Yönetim kurulunun hesapları ibra edilmedi; diğer gündem maddeleri görüşüldü. Divan ibra "
    "edilmeyen muhasebe evrakını tutanak altına alarak {teslim_alan} teslim etti (md. 11/1-ç; ibra "
    "edilmeyen muhasebe evrakının teslim tutanağı ektedir)."
)
SECIM_YK_ALT: Final = "Yönetim kurulu (md. 11/1-a)"
SECIM_DK_ALT: Final = "Denetleme Kurulu veli koltuğu (md. 11/1-b)"
SECIM_BASLIKLARI: Final = ("Sıra", "Adı ve soyadı", "Asıl ya da yedek", "Aldığı oy", "Yedek sırası")
SATIR_TESLIM: Final = "Tutanak ve belgelerin yeni yönetim kuruluna teslim günü (md. 10/1-ç)"

#: E11: ibra edilmeyen muhasebe evrakının teslim tutanağı (md. 11/1-ç; GNL-OAB-FR-005 B satır 9).
E11_GIRIS: Final = (
    "Okul-Aile Birliğinin {gun} günü yapılan {tur} genel kurul toplantısında yönetim kurulunun "
    "hesapları ibra edilmemiştir. Divan, ibra edilmeyen muhasebe evrakını aşağıda tutanak altına "
    "almış ve {teslim_alan} teslim etmiştir (Millî Eğitim Bakanlığı Okul-Aile Birliği Yönetmeliği "
    "(Yönetmelik) md. 11/1-ç)."
)
SATIR_YK_IBRA_OYLARI: Final = "Yönetim kurulunun ibra oylaması (md. 11/1-c)"
E11_LISTE_BOLUMU: Final = "İbra edilmeyen muhasebe evrakı"
E11_LISTE_BASLIKLARI: Final = ("Sıra", "Evrak")
UNVAN_TESLIM_ALAN_YK: Final = "Teslim alan: Yeni Yönetim Kurulu adına üye"
UNVAN_TESLIM_ALAN_GOREVDEKI_YK: Final = "Teslim alan: Yönetim Kurulu adına üye"
UNVAN_TESLIM_ALAN_YENI_DK: Final = "Teslim alan: Yeni Denetleme Kurulu adına üye"
UNVAN_TESLIM_ALAN_DK: Final = "Teslim alan: Denetleme Kurulu adına üye"

#: E12: il/ilçe millî eğitim müdürlüğüne resmî yazı (md. 11/1-ç; RYUE md. 11-18; plan F2 §7 U20, U21).
E12_KONU: Final = "Genel Kurulda Hesapların İbra Edilmemesi"
E12_METIN: Final = (
    "Okulumuz Okul-Aile Birliğinin {gun} tarihinde yapılan {tur} genel kurul toplantısında yönetim "
    "kurulunun hesapları ibra edilmemiştir.",
    "Millî Eğitim Bakanlığı Okul-Aile Birliği Yönetmeliğinin 11 inci maddesinin birinci fıkrasının "
    "(ç) bendi uyarınca divan, ibra edilmeyen muhasebe evrakını tutanak altına alarak {teslim_alan} "
    "teslim etmiş olup teslim tutanağı ekte sunulmuştur.",
    "Bilgilerinizi arz ederim.",
)
#: Basımda boşaltılan muhatabın yeri (8. adımın notu; `letterhead.mem_muhatabi`'nin yer tutucusu).
MUHATAP_YERI: Final = "……………"

#: E13: genel kurul sonuç bildirimi (okul müdürlüğüne; GNL-OAB-FR-005 A, C). Bildirim okul
#: uygulamasıdır: belgede "Yönetmelik gereği" denmez, giriş atıf taşımaz (MB-11; tasarım §9.5 E13).
E13_GIRIS: Final = (
    "Okul-Aile Birliğinin {gun} günü yapılan {tur} genel kurul toplantısının sonucu ve sonraki işler "
    "aşağıda bilgilerinize sunulmuştur."
)
E13_BOLUMLER: Final = (
    "A. Genel kurulun sonucu",
    "B. Seçilen yönetim kurulu (md. 11/1-a)",
    "C. Seçilen Denetleme Kurulu veli üyesi (md. 11/1-b)",
    "D. Sonraki işler",
)
SATIR_YK_IBRASI: Final = "Yönetim kurulunun ibrası (md. 11/1-c)"
SATIR_DK_IBRASI: Final = "Denetleme Kurulunun ibrası (md. 11/1-c)"
SATIR_BUTCE: Final = "Tahmini bütçe (md. 11/1-d)"
UYE_BASLIKLARI: Final = ("Sıra", "Adı ve soyadı", "Asıl ya da yedek", "Görevi")
SONRAKI_BASLIKLARI: Final = ("İş", "Son gün", "Dayanak")
IS_YK_GOREV_BOLUMU: Final = "Yönetim kurulunun görev bölümü"
IS_DK_GOREV_BOLUMU: Final = "Denetleme Kurulunun görev bölümü"
IS_BANKA: Final = "Bankaya müşterek imza yetkililerinin (başkan ve muhasip) bildirimi"
IS_TEFBIS: Final = (
    "TEFBİS'e yeni yönetimin, banka hesap bilgilerinin ve tahmini bütçenin girişi (okul idaresi)"
)
#: İl/ilçe millî eğitim müdürlüğüne yazının işi (md. 11/1-ç), yönetim kurulunun seçilip seçilmediğine
#: göre (`genel_kurul.secilen_kurullar`; teslim alanlarla aynı kaynak): seçimsiz olağanüstü genel kurulda
#: yeni yönetim kurulu yoktur, yazıyı görevdeki yönetim kurulu ve okul yönetimi yazar.
IS_MEM_YAZILARI: Final[Mapping[bool, str]] = {
    True: (
        "Hesaplar ibra edilmediği için il/ilçe millî eğitim müdürlüğüne resmî yazı (yeni yönetim "
        "kurulu ve okul yönetimi)"
    ),
    False: (
        "Hesaplar ibra edilmediği için il/ilçe millî eğitim müdürlüğüne resmî yazı (görevdeki "
        "yönetim kurulu ve okul yönetimi)"
    ),
}
#: Yönetim kurulunu seçen genel kurulun satırı (geriye dönük ad).
IS_MEM_YAZISI: Final = IS_MEM_YAZILARI[True]
SON_GUN_DEGERI: Final = "en geç {gun}"
GOREV_BOLUMUNDEN_SONRA: Final = "Yönetim kurulunun görev bölümünden sonra"
GENEL_KURULDAN_SONRA: Final = "Genel kuruldan sonra"
DAYANAK_BANKA: Final = "md. 18/2"
DAYANAK_TEFBIS: Final = "md. 23/5"
DAYANAK_MEM_YAZISI: Final = "md. 11/1-ç"

#: E14: yıllık iş takvimi (kural paketinin süre kuralları, ders yılı, birlik döneminin ayarları;
#: GNL-OAB-RH-001 Bölüm 6). Satırlar kural kimliği ve atıf taşır (sözlük §2 istisna 3).
E14_GIRIS: Final = (
    "Bu takvim kural paketinin süre kurallarından, ders yılından ve birlik döneminin ayarlarından "
    "hazırlanmıştır. Süre kuralı satırları kuralın kimliğini ve dayanağını taşır; okul planı satırları "
    "birlik döneminin ve ders yılının ayarlarındandır, kural değildir."
)
E14_BOLUMLER: Final = ("A. Süre kuralları", "B. Okul planı")
KURAL_BASLIKLARI: Final = ("Tarih", "İş", "Kural", "Dayanak")
PLAN_BASLIKLARI: Final = ("Tarih", "İş", "Kaynak")
IS_ILAN: Final = "Olağan genel kurulun yeri, zamanı ve gündeminin bildirilmesi ve duyurulması"
IS_OLAGAN_GK: Final = "Olağan genel kurulun birinci toplantısı"
IS_IKINCI_TOPLANTI: Final = (
    "Birinci toplantıda yeter sayı sağlanamazsa ikinci toplantı (çoğunluk aranmaz)"
)
IS_ARZ_SOZLESME: Final = "Kantin arz bedelinin ödenmesi (kiracı; sözleşmedeki son gün)"
IS_ARZ_YONETMELIK: Final = "Kantin arz bedelinin ödenmesinin Yönetmelikteki son günü"
ILAN_GORELI: Final = "toplantı gününden en az {gun} gün önce"
IKINCI_GORELI: Final = "birinci toplantıdan sonra en geç {gun} gün içinde"
ARZ_GUNU: Final = "üçer aylık dönemlerde, dönemi takip eden ayın {gun}. günü"
IS_DERS_YILI_BASI: Final = "Ders yılının başlangıcı"
IS_DERS_YILI_SONU: Final = "Ders yılının sonu"
IS_DERS_DONEMI: Final = "{sira}. ders dönemi"
DONEM_ARALIGI: Final = "{bas} – {son}"
IS_YK_TOPLANTISI: Final = "Yönetim kurulunun aylık toplantısı (md. 13/3)"
IS_DK_DENETIMI: Final = "Denetleme Kurulunun {sira}. ara denetimi (md. 14/4)"
KAYNAK_DERS_YILI: Final = "Ders yılı (Ayarlar)"
KAYNAK_DONEM: Final = "Birlik döneminin ayarı"
#: E14'ün süre kuralları ve satırın işi (kural kimliği basılır; sözlük §2 istisna 3).
_GK_ILAN: Final = "genel_kurul.ilan_en_az_gun"
_GK_SON_AY: Final = "genel_kurul.olagan_son_ay"
_GK_IKINCI: Final = "genel_kurul.ikinci_toplanti_en_gec_gun"
_YK_GOREV_BOLUMU: Final = "yonetim_kurulu.gorev_bolumu_gun"
_DK_GOREV_BOLUMU: Final = "denetleme_kurulu.gorev_bolumu_gun"
_ARZ_SOZLESME: Final = "arz_bedeli.sozlesme_vade_gunu"
_ARZ_YONETMELIK: Final = "arz_bedeli.yonetmelik_vade_gunu"
E14_KURALLARI: Final = (
    _YK_GOREV_BOLUMU,
    _DK_GOREV_BOLUMU,
    _GK_ILAN,
    _GK_SON_AY,
    _GK_IKINCI,
    _ARZ_SOZLESME,
    _ARZ_YONETMELIK,
)

#: Basım uyarıları (belgeye basılmaz).
UYARI_ADAY_YOK: Final = "Aday kaydı yok; aday satırı ……… basıldı."
UYARI_SAYAC_BILINMIYOR: Final = (
    "Bir adayın programdan önceki seçilme sayısı bilinmiyor; yeri ……… basıldı."
)
UYARI_SONUC_YOK: Final = "Sonucu girilmemiş gündem maddesi var; sonucun yeri ……… basıldı."
UYARI_SONUC_METNI_OKUNAMADI: Final = "Bir gündem maddesinin sonuç metni okunamadı; basılmadı."
UYARI_IBRA_YOK: Final = "İbra sonucu girilmemiş; yeri ……… basıldı."
UYARI_SECIM_YOK: Final = "Seçim sonucu girilmemiş; seçilenlerin satırı ……… basıldı."
UYARI_TUTANAK_BILGISI_YOK: Final = "Tutanak bilgisi girilmemiş; yeri ……… basıldı."
UYARI_EVRAK_LISTESI_YOK: Final = (
    "İbra edilmeyen muhasebe evrakının listesi girilmemiş; listenin yeri ……… basıldı."
)
UYARI_EVRAK_LISTESI_OKUNAMADI: Final = (
    "İbra edilmeyen muhasebe evrakının listesi okunamadı; listenin yeri ……… basıldı."
)
UYARI_SAYI: Final = "Yazının sayısı okulun resmî yazışma sisteminde verilir; yeri ……… basıldı."
UYARI_MUHATAP_BOS: Final = "Muhatap boş bırakıldı; muhatabın yeri …………… basıldı."
UYARI_MUHATAP_ILCE_YOK: Final = (
    "Okul bilgilerinde ilçe girilmemiş; muhatapta ilçenin yeri …………… basıldı."
)
UYARI_YENI_BASKAN_YOK: Final = (
    "Yeni yönetim kurulunun görev bölümü yapılmadı; başkanın adının yeri ……… basıldı. Görev "
    "bölümünden sonra belgeyi yeniden üretin."
)
UYARI_YENI_SEKRETER_YOK: Final = (
    "Yeni yönetim kurulunun görev bölümü yapılmadı; sekreterin adının yeri ……… basıldı. Görev "
    "bölümünden sonra belgeyi yeniden üretin."
)
UYARI_DONEM_BASLANGICI_YOK: Final = (
    "Birlik döneminin başlangıcı yok; görev bölümü satırlarının tarihi ……… basıldı."
)
UYARI_KURAL_DEGERI_YOK: Final = "Bir kuralın bu güne değeri yok; satırın tarihi ……… basıldı."
UYARI_YK_TOPLANTISI_YOK: Final = (
    "Birlik döneminde yönetim kurulunun toplantı günü girilmemiş; yeri ……… basıldı."
)
UYARI_DENETIM_PLANI_YOK: Final = (
    "Birlik döneminde Denetleme Kurulunun denetim planı girilmemiş; yeri ……… basıldı."
)
UYARI_KANTIN_BICIMI_YOK: Final = (
    "Okul bilgilerinde kantin işletme biçimi girilmemiş; arz bedeli satırları basılmadı."
)


# ---------------------------------------------------------------------------
# Genel kurul evrakı II — ortak yardımcılar
# ---------------------------------------------------------------------------
def _yapilmis_kurul(konu: models.Model) -> GeneralAssembly:
    """Yapılmış genel kurul (tutanağın ve sonrasının belgeleri); yapılmadıysa üretilmez."""
    kurul = _genel_kurul(konu)
    if kurul.status not in _YAPILMIS or not kurul.held_at_meeting:
        raise ValueError(GENEL_KURUL_YAPILMADI)
    return kurul


def _ibra_edilmemis_kurul(konu: models.Model) -> GeneralAssembly:
    """E11 ve E12'nin açılma koşulu (kullanıcı kararı S4 (a)): yönetim kurulunun hesapları ibra
    edilmedi. Denetleme Kurulunun ibra edilmemesi yalnız tutanağa yazılır (E10)."""
    kurul = _yapilmis_kurul(konu)
    if kurul.discharge_yk != Discharge.EDILMEDI:
        raise ValueError(IBRA_EDILMEDIKCE_URETILMEZ)
    return kurul


def _yapildigi_an(kurul: GeneralAssembly) -> datetime | None:
    return _toplanti_ani(kurul, str(kurul.held_at_meeting))


def _yapildigi_gun(kurul: GeneralAssembly) -> date | None:
    """Genel kurulun yapıldığı toplantının yerel günü (plan F2 §7 U6; `selectors.genel_kurul_gunu`)."""
    return selectors.genel_kurul_gunu(kurul)


def _katilan(kurul: GeneralAssembly) -> int | None:
    """Yapıldığı toplantının katılımı (son düzeltmeyle; kararlar bu sayıyla denetlenir)."""
    if kurul.held_at_meeting == AssemblyMeeting.IKINCI:
        return kurul.second_attendee_count
    return kurul.first_attendee_count


def _gun_yer(kurul: GeneralAssembly, uyarilar: _Uyarilar) -> str:
    return GUN_YER_DEGERI.format(an=_an(_yapildigi_an(kurul)), yer=_yer(kurul, uyarilar))


def _oylar(kabul: int | None, ret: int | None, salon: int | None = None) -> str:
    """Oylamanın sayıları ("kabul N, ret N; oylamada salonda bulunan N")."""
    metin = OYLAR_DEGERI.format(kabul=_sayi(kabul), ret=_sayi(ret))
    if salon is not None:
        metin += SALONDAKI_DEGERI.format(salon=salon)
    return metin


def _kurul_secilenleri(kurul: GeneralAssembly, organ: str) -> list[OrganMembership]:
    """Genel kurulun seçtikleri (tek kaynak, O6; tasarım §9.1-3): bu genel kurulun bu kuruldaki
    seçilmiş kayıtları — sonradan düşen de seçilmiştir; iptal edilen (yanlış giriş) ve seçilmeyen aday
    girmez. Asıl önce, yedek sırasıyla (`selectors.memberships_sorted`)."""
    return selectors.memberships_sorted(
        OrganMembership.objects.filter(
            assembly=kurul,
            organ=organ,
            status__in=(MembershipStatus.SECILDI, MembershipStatus.DUSTU),
        ).select_related("person")
    )


def _kurul_adaylari(kurul: GeneralAssembly, organ: str) -> list[OrganMembership]:
    """Genel kurulun aday kayıtları (E09): aday kalan, seçilen ve sonradan düşen; iptal edilen (yanlış
    giriş) girmez. Aday listesi ile seçim sonucu aynı kayıtlardır (tasarım §9.6 E09)."""
    return selectors.memberships_sorted(
        OrganMembership.objects.filter(assembly=kurul, organ=organ)
        .exclude(status=MembershipStatus.IPTAL)
        .select_related("person")
    )


def _yeni_gorevli(kurul: GeneralAssembly, role: str) -> OrganMembership | None:
    """Genel kurulun seçtiği yönetim kurulunda görev bölümüyle görev alan (yeni başkan, yeni sekreter;
    plan F2 §7 U21). Görev bölümünden önce `None`."""
    return next(
        (
            u
            for u in _kurul_secilenleri(kurul, OrganType.YONETIM_KURULU)
            if u.status == MembershipStatus.SECILDI and u.role == role
        ),
        None,
    )


def _gundem_turleri(kurul: GeneralAssembly) -> set[str]:
    """Gündemde kalan maddelerin türleri (oylamayla çıkarılan madde sayılmaz; md. 9/4)."""
    return genel_kurul.gundem_turleri(kurul)


def _secilen_kurullar(kurul: GeneralAssembly, turler: set[str]) -> tuple[bool, bool]:
    """Bu genel kurul yönetim kurulunu ve Denetleme Kurulunu (veli koltuğu) seçer mi (tek kaynak:
    `genel_kurul.secilen_kurullar`; olağanüstü genel kurul Denetleme Kuruluna seçim yapmaz, S10 (a))."""
    return genel_kurul.secilen_kurullar(kurul, turler)


def _teslim_alan(kurul: GeneralAssembly) -> str:
    """Md. 11/1-ç'de evrakı teslim alan kurullar (`TESLIM_ALANLAR`; seçilen yeni ya da görevdeki)."""
    return TESLIM_ALANLAR[_secilen_kurullar(kurul, _gundem_turleri(kurul))]


def _yeni_gorevli_adi(kurul: GeneralAssembly, role: str, uyari: str, uyarilar: _Uyarilar) -> str:
    uyelik = _yeni_gorevli(kurul, role)
    if uyelik is None:
        uyarilar.ekle(uyari)
        return BOS
    return _ad(uyelik.person, uyarilar)


def _imzaci_gorevli_adi(
    kurul: GeneralAssembly, role: str, unvan: str, uyari: str, uyarilar: _Uyarilar
) -> str:
    """E12 ve E13'ün başkanı ve sekreteri. Bu genel kurul yönetim kurulunu seçtiyse yeni kurulun
    görevlisi (plan F2 §7 U21; görev bölümünden önce "………" ve `uyari`); seçmediyse (seçim maddesi
    olmayan olağanüstü genel kurul ya da gündemden çıkarılan seçim) genel kurulun günü görevde olan
    yönetim kurulunun görevlisi (`selectors.gundeki_asillar`; yoksa "………" ve görev boş uyarısı)."""
    if _secilen_kurullar(kurul, _gundem_turleri(kurul))[0]:
        return _yeni_gorevli_adi(kurul, role, uyari, uyarilar)
    gun = _yapildigi_gun(kurul)
    asillar = (
        []
        if kurul.term is None or gun is None
        else selectors.gundeki_asillar(kurul.term, OrganType.YONETIM_KURULU, gun)
    )
    uyelik = next((u for u in asillar if u.role == role), None)
    if uyelik is None:
        uyarilar.ekle(UYARI_GOREV_BOS.format(gorev=unvan))
        return BOS
    return _ad(uyelik.person, uyarilar)


def _dk_ogretmen_bilgisi(kurul: GeneralAssembly) -> evrak.Paragraf:
    """Denetleme Kurulunun öğretmen koltukları bilgi satırı; sayılar kural paketinden."""
    yer = _kural_yeri(kurul)
    asil, yedek = BOS, BOS
    if yer is not None:
        try:
            koltuklar = kural("denetleme_kurulu.koltuklar", *yer)
            ogretmen = koltuklar[SeatGroup.OGRETMEN]
            asil, yedek = str(ogretmen[SeatType.ASIL]), str(ogretmen[SeatType.YEDEK])
        except YururlukteDegerYok:
            pass
    return evrak.Paragraf(DK_OGRETMEN_BILGISI.format(asil=asil, yedek=yedek))


def _sure_son_gunu(kural_id: str, baslangic: date, donem: OabTerm) -> tuple[date, str] | None:
    """Süre kuralının son günü ve atfı: başlangıç + kural değeri (gün; pano ile aynı hesap, plan
    F1c görev bölümü süresi). Yürürlükte değer yoksa `None`."""
    try:
        kayit = kural_kaydi(kural_id, tarih=baslangic, donem=donem)
    except YururlukteDegerYok:
        return None
    return baslangic + timedelta(days=int(kayit["deger"])), atif_metni(kayit)


# ---------------------------------------------------------------------------
# E09 — yönetim kurulu ve Denetleme Kurulu (veli koltuğu) aday listeleri
# ---------------------------------------------------------------------------
def _onceki_secilme(kurul: GeneralAssembly, uyelik: OrganMembership, uyarilar: _Uyarilar) -> str:
    """Adayın programdan önceki ve programdaki yönetim kurulu seçilmeleri (md. 12/4): bu genel
    kuruldan önceki seçilmeler; bu genel kurulun ve sonraki genel kurulların seçilmeleri sayılmaz
    (`uyelikler.yk_secilme_sayaci_once`; eski genel kurulun yeniden üretilen listesi aynı sayıyı
    basar). Beyan bilinmiyorsa "………" ve uyarı."""
    sayi = uyelikler.yk_secilme_sayaci_once(
        uyelik.person, selectors.genel_kurul_gunu(kurul), haric_kurul=kurul
    )
    if sayi is None:
        uyarilar.ekle(UYARI_SAYAC_BILINMIYOR)
        return BOS
    return str(sayi)


def _aday_satirlari(
    kurul: GeneralAssembly, organ: str, uyarilar: _Uyarilar, *, sayacli: bool
) -> tuple[tuple[str, ...], ...]:
    satirlar: list[tuple[str, ...]] = []
    for sira, uyelik in enumerate(_kurul_adaylari(kurul, organ), start=1):
        hucreler = [
            str(sira),
            _ad(uyelik.person, uyarilar),
            KOLTUK_ADLARI.get(str(uyelik.seat_type), BOS),
            str(PersonKind(uyelik.person.kind).label),
        ]
        if sayacli:
            hucreler.append(_onceki_secilme(kurul, uyelik, uyarilar))
        satirlar.append(tuple(hucreler))
    if not satirlar:
        uyarilar.ekle(UYARI_ADAY_YOK)
        satirlar.append((BOS,) * (5 if sayacli else 4))
    return tuple(satirlar)


def e09_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E09'un içerik modeli (tasarım §9.3, §9.6 E09; OYS `aday_listeleri.html` UYARLA): yönetim kurulu
    adayları (kişi türü ve md. 12/4 sayacıyla) ve Denetleme Kurulunun veli koltuğu adayları; öğretmen
    koltukları yalnız bilgi satırıdır (genel kurulun oylamasına girmez). Olağanüstü genel kurul
    Denetleme Kuruluna seçim yapmaz (kullanıcı kararı S10 (a)): B bölümü basılmaz. İmza Divan Başkanı
    + Kâtip; aday adları kişisel veridir (dipnot)."""
    kurul = _genel_kurul(konu)
    uyarilar = _Uyarilar()
    if kurul.status == AssemblyStatus.IPTAL:
        uyarilar.ekle(UYARI_IPTAL)
    toplanti = str(kurul.held_at_meeting or AssemblyMeeting.BIRINCI)
    bilgi = [
        (SATIR_TUR, TUR_BASLIKLARI[str(kurul.kind)]),
        (
            SATIR_GUN_YER,
            GUN_YER_DEGERI.format(
                an=_an(_toplanti_ani(kurul, toplanti)), yer=_yer(kurul, uyarilar)
            ),
        ),
    ]
    bloklar: list[evrak.Blok] = [
        _baslik(E09, kurul),
        evrak.Paragraf(E09_GIRIS),
        evrak.Tablo(basliklar=KONU_BILGI, satirlar=tuple(bilgi), oranlar=(2, 3)),
        evrak.AltBaslik(YK_ADAY_BOLUMU),
        evrak.Tablo(
            basliklar=YK_ADAY_BASLIKLARI,
            satirlar=_aday_satirlari(kurul, OrganType.YONETIM_KURULU, uyarilar, sayacli=True),
            oranlar=(1, 6, 3, 3, 3),
        ),
    ]
    if kurul.kind == AssemblyKind.OLAGAN:
        bloklar += [
            evrak.AltBaslik(DK_ADAY_BOLUMU),
            evrak.Tablo(
                basliklar=DK_ADAY_BASLIKLARI,
                satirlar=_aday_satirlari(
                    kurul, OrganType.DENETLEME_KURULU, uyarilar, sayacli=False
                ),
                oranlar=(1, 6, 3, 3),
            ),
            _dk_ogretmen_bilgisi(kurul),
        ]
    bloklar += [
        evrak.Imza(sahipler=tuple(_divan_imzalari(kurul, uyarilar))),
        evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
    ]
    belge = evrak.Belge(kod=E09, antet=_antet(), bloklar=tuple(bloklar))
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# E10 — genel kurul toplantı tutanağı
# ---------------------------------------------------------------------------
def _toplanti_bilgisi(
    kurul: GeneralAssembly, kol: str, uyarilar: _Uyarilar
) -> list[tuple[str, str]]:
    """A bölümü: tür, çağıran (olağanüstüde neden), yapıldığı toplantı, gün ve yer, ilan, yeter sayı
    (ikinci toplantıda "çoğunluk aranmaz"), katılan ve gözlemci."""
    ikinci = kurul.held_at_meeting == AssemblyMeeting.IKINCI
    bilgi: list[tuple[str, str]] = [
        (SATIR_TUR, TUR_BASLIKLARI[str(kurul.kind)]),
        (SATIR_CAGIRAN, _cagiran_metni(kurul, kol)),
    ]
    if kurul.kind == AssemblyKind.OLAGANUSTU:
        bilgi.append((SATIR_CAGRI_NEDENI, _cagri_nedeni(kurul, uyarilar)))
    bilgi += [
        (SATIR_TOPLANTI, TOPLANTI_ADLARI[str(kurul.held_at_meeting)]),
        (SATIR_GUN_YER, _gun_yer(kurul, uyarilar)),
        (SATIR_ILAN, _gun(kurul.announced_on)),
    ]
    if ikinci:
        ilk = genel_kurul.ilk_girilen_deger(kurul, "first_attendee_count")
        ilk = kurul.first_attendee_count if ilk is None else ilk
        bilgi.append(
            (
                SATIR_BIRINCI_SONUCU,
                BIRINCI_SONUCU_DEGERI.format(an=_an(kurul.first_meeting_at), katilan=_sayi(ilk)),
            )
        )
        bilgi.append((SATIR_YETER_SAYI, COGUNLUK_ARANMAZ_DEGERI))
    else:
        bilgi.append((SATIR_YETER_SAYI, _yeter_sayi(kurul, uyarilar)))
    if kurul.observer_count is None:
        uyarilar.ekle(UYARI_GOZLEMCI_YOK)
    bilgi += [
        (SATIR_KATILAN, _sayi(_katilan(kurul))),
        (SATIR_GOZLEMCI, _sayi(kurul.observer_count)),
    ]
    return bilgi


def _divan_bilgisi(kurul: GeneralAssembly, uyarilar: _Uyarilar) -> list[tuple[str, str]]:
    """B bölümü: açılış (md. 10/1-b) ve divan (md. 10/1-c); adlar divan kayıtlarından."""
    satirlar = [(SATIR_ACILIS, ACILIS_DEGERI)]
    satirlar += [(sahip.gorev, sahip.ad) for sahip in _divan_imzalari(kurul, uyarilar)]
    return satirlar


def _ibra_sonucu(kurul: GeneralAssembly) -> str | None:
    """İbra maddesinin sonucu kurulun ibra alanlarından (`discharge_yk`, `discharge_dk`; maddenin
    `result`'u iki kurul da "görüşülmedi" olunca boştur, `genel_kurul.ibra_yaz`). Girilmemişse `None`."""
    sonuclar = {str(kurul.discharge_yk), str(kurul.discharge_dk)}
    if "" in sonuclar:
        return None
    return SONUC_IBRA_GORUSULMEDI if sonuclar == {Discharge.GORUSULMEDI} else SONUC_IBRA


def _sonuc_metni(madde: AgendaItem, kurul: GeneralAssembly, uyarilar: _Uyarilar) -> str:
    """Gündem maddesinin sonucu (md. 9/2, 9/4, 11/1): kabul ve ret oylarıyla; ibra ve seçim kendi
    bölümlerinde (ibra kurulun ibra alanlarından); tahmini bütçe yalnız "görüşüldü" ve ekin adı (U22;
    oyla girilmiş sonuç da — E13 ile aynı). Sonuç metni (serbest, şifreli) sonuna eklenir."""
    if madde.removed_by_vote:
        return SONUC_CIKARILDI
    tur = str(madde.kind)
    if tur == AgendaItemKind.IBRA:
        ibra = _ibra_sonucu(kurul)
        if ibra is None:
            uyarilar.ekle(UYARI_IBRA_YOK)
            return BOS
        sonuc = ibra
    elif not madde.result:
        uyarilar.ekle(UYARI_SONUC_YOK)
        return BOS
    elif tur in (AgendaItemKind.SECIM_YK, AgendaItemKind.SECIM_DK):
        sonuc = SONUC_SECIM
    elif tur == AgendaItemKind.TAHMINI_BUTCE:
        sonuc = SONUC_BUTCE
    elif madde.result == AgendaResult.KABUL:
        sonuc = SONUC_KABUL.format(
            oylar=_oylar(madde.votes_for, madde.votes_against, madde.present_count)
        )
    elif madde.result == AgendaResult.RET:
        sonuc = SONUC_RET.format(
            oylar=_oylar(madde.votes_for, madde.votes_against, madde.present_count)
        )
    else:
        sonuc = SONUC_GORUSULDU
    if is_corrupt(madde.result_text):
        uyarilar.ekle(UYARI_SONUC_METNI_OKUNAMADI)
        return sonuc
    metin = " ".join(str(madde.result_text).split())
    return SONUC_METNI.format(sonuc=sonuc, metin=metin) if metin else sonuc


def _gundem_sonuclari(kurul: GeneralAssembly, uyarilar: _Uyarilar) -> list[evrak.Blok]:
    """C bölümü: gündem maddeleri (oylamayla eklenen ve çıkarılan dahil) ve sonuçları, raporları
    okuyanlar ve bütçeyi sunan; gündem değişikliğinin oylaması ayrı tablodadır (md. 9/4; tasarım §9.6
    E10)."""
    maddeler = list(AgendaItem.objects.filter(assembly=kurul).order_by("order", "pk"))
    satirlar = tuple(
        (str(m.order), str(m.title), _sonuc_metni(m, kurul, uyarilar)) for m in maddeler
    ) or ((BOS, BOS, BOS),)
    if not maddeler:
        uyarilar.ekle(UYARI_GUNDEM_YOK)
    bloklar: list[evrak.Blok] = [
        evrak.Tablo(basliklar=SONUC_BASLIKLARI, satirlar=satirlar, oranlar=(1, 5, 6))
    ]
    okuyanlar = _okuyan_satirlari(
        kurul, {str(m.kind) for m in maddeler if not m.removed_by_vote}, uyarilar
    )
    if okuyanlar:
        bloklar.append(evrak.Tablo(basliklar=KONU_BILGI, satirlar=tuple(okuyanlar), oranlar=(2, 3)))
    degisiklikler = tuple(
        (
            str(m.title),
            DEGISIKLIK_EKLENDI if m.added_by_vote else DEGISIKLIK_CIKARILDI,
            _oylar(m.change_votes_for, m.change_votes_against),
        )
        for m in maddeler
        if m.added_by_vote or m.removed_by_vote
    )
    bloklar.append(evrak.AltBaslik(GUNDEM_DEGISIKLIGI_BOLUMU))
    if degisiklikler:
        bloklar.append(
            evrak.Tablo(basliklar=DEGISIKLIK_BASLIKLARI, satirlar=degisiklikler, oranlar=(5, 3, 4))
        )
    else:
        bloklar.append(evrak.Paragraf(GUNDEM_DEGISMEDI))
    return bloklar


def _okuyan_satirlari(
    kurul: GeneralAssembly, turler: set[str], uyarilar: _Uyarilar
) -> list[tuple[str, str]]:
    """Raporları okuyanlar ve tahmini bütçeyi sunan (tutanak kaydı; gündemde kalan maddesi olanlar,
    oylamayla çıkarılan sayılmaz)."""
    tutanak = AssemblyMinutes.objects.filter(assembly=kurul).first()
    satirlar: list[tuple[str, str]] = []
    for tur, satir, alan in (
        (AgendaItemKind.YK_FAALIYET_RAPORU, SATIR_YK_RAPORU, "yk_report_reader"),
        (AgendaItemKind.DK_RAPORU, SATIR_DK_RAPORU_OKUYAN, "dk_report_reader"),
        (AgendaItemKind.TAHMINI_BUTCE, SATIR_BUTCEYI_SUNAN, "budget_presenter"),
    ):
        if tur not in turler:
            continue
        kisi = None if tutanak is None else getattr(tutanak, alan)
        if kisi is None:
            uyarilar.ekle(UYARI_TUTANAK_BILGISI_YOK)
        satirlar.append((satir, _ad(kisi, uyarilar)))
    return satirlar


def _ibra_bolumu(kurul: GeneralAssembly, uyarilar: _Uyarilar) -> list[evrak.Blok]:
    """D bölümü (md. 11/1-c, ç; tasarım §9.6 E10 "YK ve DK ibrası ayrı oylama satırı"): sonuç ve
    oylar kurul başına; yönetim kurulunun hesapları ibra edilmediyse yan akışın paragrafı (S4 (a))."""
    satirlar: list[tuple[str, str, str, str, str]] = []
    for ad, onek in ((KURUL_YK, "discharge_yk"), (KURUL_DK, "discharge_dk")):
        sonuc = str(getattr(kurul, onek))
        if not sonuc:
            uyarilar.ekle(UYARI_IBRA_YOK)
            satirlar.append((ad, BOS, "", "", ""))
            continue
        kabul = getattr(kurul, f"{onek}_votes_for")
        ret = getattr(kurul, f"{onek}_votes_against")
        salon = getattr(kurul, f"{onek}_present_count")
        satirlar.append(
            (
                ad,
                str(Discharge(sonuc).label),
                "" if kabul is None else str(kabul),
                "" if ret is None else str(ret),
                "" if salon is None else str(salon),
            )
        )
    bloklar: list[evrak.Blok] = [
        evrak.Tablo(basliklar=IBRA_BASLIKLARI, satirlar=tuple(satirlar), oranlar=(3, 3, 2, 2, 3))
    ]
    if kurul.discharge_yk == Discharge.EDILMEDI:
        bloklar.append(
            evrak.Paragraf(IBRA_EDILMEDI_PARAGRAFI.format(teslim_alan=_teslim_alan(kurul)))
        )
    return bloklar


def _secilen_satirlari(
    kurul: GeneralAssembly, organ: str, uyarilar: _Uyarilar
) -> tuple[tuple[str, ...], ...]:
    satirlar = tuple(
        (
            str(sira),
            _ad(u.person, uyarilar),
            KOLTUK_ADLARI.get(str(u.seat_type), BOS),
            "" if u.votes is None else str(u.votes),
            "" if u.seat_order is None else str(u.seat_order),
        )
        for sira, u in enumerate(_kurul_secilenleri(kurul, organ), start=1)
    )
    if not satirlar:
        uyarilar.ekle(UYARI_SECIM_YOK)
        return ((BOS, BOS, BOS, "", ""),)
    return satirlar


def _secim_bolumu(
    kurul: GeneralAssembly, turler: set[str], uyarilar: _Uyarilar
) -> list[evrak.Blok]:
    """E bölümü: seçim maddesi olan kurulların seçilenleri (asıl ve yedek, oy, yedek sırası; md.
    10/1-d, 13/6); Denetleme Kurulunda öğretmen koltukları bilgi satırıdır."""
    bloklar: list[evrak.Blok] = []
    if AgendaItemKind.SECIM_YK in turler:
        bloklar += [
            evrak.Paragraf(SECIM_YK_ALT),
            evrak.Tablo(
                basliklar=SECIM_BASLIKLARI,
                satirlar=_secilen_satirlari(kurul, OrganType.YONETIM_KURULU, uyarilar),
                oranlar=(1, 6, 3, 2, 2),
            ),
        ]
    if AgendaItemKind.SECIM_DK in turler and kurul.kind == AssemblyKind.OLAGAN:
        bloklar += [
            evrak.Paragraf(SECIM_DK_ALT),
            evrak.Tablo(
                basliklar=SECIM_BASLIKLARI,
                satirlar=_secilen_satirlari(kurul, OrganType.DENETLEME_KURULU, uyarilar),
                oranlar=(1, 6, 3, 2, 2),
            ),
            _dk_ogretmen_bilgisi(kurul),
        ]
    return bloklar


def e10_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E10'un içerik modeli (tasarım §9.6 E10; GNL-OAB-FR-004; OYS `tutanak.html` UYARLA): toplantı,
    açılış ve divan, gündem maddelerinin sonuçları ve gündem değişikliğinin oylaması (md. 9/4), ibra
    (kurul başına ayrı oylama satırı), seçim sonuçları, kapanış (teslim günü). Seçilenler üyelik
    kayıtlarından (tek kaynak; E09 ve E13 ile aynı kayıtlar). İmza Divan Başkanı + Kâtip ve "Görüldü —
    Okul Müdürü (md. 27/1)"; müdürün çağırdığı genel kurulda "Görüldü" yoktur (tasarım §9.3 "Görüldü
    (müdür çağırmadıysa)"; E64 ile aynı). Tarih genel kurulun yapıldığı gündür."""
    kurul = _yapilmis_kurul(konu)
    kol = cagri_kolu(kurul)
    uyarilar = _Uyarilar()
    turler = _gundem_turleri(kurul)
    bloklar: list[evrak.Blok] = [
        _baslik(E10, kurul),
        evrak.Paragraf(E10_GIRIS.format(tur=TUR_ADLARI[str(kurul.kind)])),
        evrak.AltBaslik(E10_BOLUMLER[0]),
        evrak.Tablo(
            basliklar=KONU_BILGI,
            satirlar=tuple(_toplanti_bilgisi(kurul, kol, uyarilar)),
            oranlar=(2, 3),
        ),
        evrak.AltBaslik(E10_BOLUMLER[1]),
        evrak.Tablo(
            basliklar=KONU_BILGI, satirlar=tuple(_divan_bilgisi(kurul, uyarilar)), oranlar=(2, 3)
        ),
        evrak.AltBaslik(E10_BOLUMLER[2]),
        *_gundem_sonuclari(kurul, uyarilar),
    ]
    if AgendaItemKind.IBRA in turler:
        bloklar += [evrak.AltBaslik(E10_BOLUMLER[3]), *_ibra_bolumu(kurul, uyarilar)]
    secimler = _secim_bolumu(kurul, turler, uyarilar)
    if secimler:
        bloklar += [evrak.AltBaslik(E10_BOLUMLER[4]), *secimler]
    tutanak = AssemblyMinutes.objects.filter(assembly=kurul).first()
    teslim = None if tutanak is None else tutanak.handed_to_new_yk_on
    if teslim is None:
        uyarilar.ekle(UYARI_TUTANAK_BILGISI_YOK)
    bloklar += [
        evrak.AltBaslik(E10_BOLUMLER[5]),
        evrak.Tablo(basliklar=KONU_BILGI, satirlar=((SATIR_TESLIM, _gun(teslim)),), oranlar=(2, 3)),
    ]
    sahipler = _divan_imzalari(kurul, uyarilar)
    if kol not in MUDUR_KOLLARI:
        sahipler.append(evrak.ImzaSahibi(_mudur_adi(uyarilar), UNVAN_GORULDU_E05))
    bloklar += [
        evrak.Imza(sahipler=tuple(sahipler), tarih=_gun(_yapildigi_gun(kurul))),
        evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
    ]
    belge = evrak.Belge(kod=E10, antet=_antet(), bloklar=tuple(bloklar))
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# E11 — ibra edilmeyen muhasebe evrakının teslim tutanağı (divan)
# ---------------------------------------------------------------------------
def _evrak_listesi_satirlari(
    kurul: GeneralAssembly, uyarilar: _Uyarilar
) -> tuple[tuple[str, str], ...]:
    """İbra edilmeyen muhasebe evrakı tek tek (tasarım §9.6 E11): tutanağın şifreli notunun her dolu
    satırı bir evraktır (`AssemblyMinutes.unaudited_documents_note`)."""
    tutanak = AssemblyMinutes.objects.filter(assembly=kurul).first()
    if tutanak is not None and is_corrupt(tutanak.unaudited_documents_note):
        uyarilar.ekle(UYARI_EVRAK_LISTESI_OKUNAMADI)
        return ((BOS, BOS),)
    metin = "" if tutanak is None else str(tutanak.unaudited_documents_note)
    kalemler = [" ".join(satir.split()) for satir in metin.splitlines() if satir.strip()]
    if not kalemler:
        uyarilar.ekle(UYARI_EVRAK_LISTESI_YOK)
        return ((BOS, BOS),)
    return tuple((str(sira), kalem) for sira, kalem in enumerate(kalemler, start=1))


def e11_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E11'in içerik modeli (tasarım §9.6 E11; md. 11/1-ç): yalnız yönetim kurulunun hesapları ibra
    edilmediğinde üretilir (kullanıcı kararı S4 (a)). Evrak tek tek listelenir, tarih genel kurulun
    yapıldığı gündür. Divan (Divan Başkanı + Kâtip) teslim eder; teslim alan yönetim kurulu ve
    Denetleme Kurulu adına birer üyedir (adları elle yazılır). Kurul bu genel kurulda seçildiyse yeni
    kurul, seçilmediyse görevdeki kuruldur: olağanüstü genel kurul Denetleme Kuruluna seçim yapmaz
    (S10 (a)); seçim maddesi gündemde yoksa yönetim kurulu da görevdekidir (`TESLIM_ALANLAR`; giriş
    cümlesi ve unvanlar aynı kaynaktan). E12'nin ekidir, okul dışına gider: kişisel veri dipnotu
    ("okul dışına verilmez") basılmaz."""
    kurul = _ibra_edilmemis_kurul(konu)
    uyarilar = _Uyarilar()
    bilgi = [
        (SATIR_TUR, TUR_BASLIKLARI[str(kurul.kind)]),
        (SATIR_GUN_YER, _gun_yer(kurul, uyarilar)),
        (
            SATIR_YK_IBRA_OYLARI,
            _oylar(
                kurul.discharge_yk_votes_for,
                kurul.discharge_yk_votes_against,
                kurul.discharge_yk_present_count,
            ),
        ),
    ]
    yeni_yk, yeni_dk = _secilen_kurullar(kurul, _gundem_turleri(kurul))
    sahipler = [
        *_divan_imzalari(kurul, uyarilar),
        evrak.ImzaSahibi("", UNVAN_TESLIM_ALAN_YK if yeni_yk else UNVAN_TESLIM_ALAN_GOREVDEKI_YK),
        evrak.ImzaSahibi("", UNVAN_TESLIM_ALAN_YENI_DK if yeni_dk else UNVAN_TESLIM_ALAN_DK),
    ]
    belge = evrak.Belge(
        kod=E11,
        antet=_antet(),
        bloklar=(
            _baslik(E11, kurul),
            evrak.Paragraf(
                E11_GIRIS.format(
                    gun=_gun(_yapildigi_gun(kurul)),
                    tur=TUR_ADLARI[str(kurul.kind)],
                    teslim_alan=TESLIM_ALANLAR[(yeni_yk, yeni_dk)],
                )
            ),
            evrak.Tablo(basliklar=KONU_BILGI, satirlar=tuple(bilgi), oranlar=(2, 3)),
            evrak.AltBaslik(E11_LISTE_BOLUMU),
            evrak.Tablo(
                basliklar=E11_LISTE_BASLIKLARI,
                satirlar=_evrak_listesi_satirlari(kurul, uyarilar),
                oranlar=(1, 9),
            ),
            evrak.Imza(sahipler=tuple(sahipler), tarih=_gun(_yapildigi_gun(kurul))),
        ),
    )
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# E12 — ibra edilmediğine dair il/ilçe millî eğitim müdürlüğüne resmî yazı (RYUE)
# ---------------------------------------------------------------------------
def _muhatap(secim: Secim, uyarilar: _Uyarilar) -> tuple[str, str]:
    """Muhatap (plan F2 §7 U20; kullanıcı kararı S11 (a)): verilmediyse okul kartından ilçe millî
    eğitim müdürlüğüne kaymakamlık üzerinden öneri (`letterhead.mem_muhatabi`); basımda düzenlenen
    muhatap boşaltıldıysa yer tutucu ve uyarı (altın kural 3: sert engel değil)."""
    if secim.muhatap is None:
        okul = SchoolConfig.load()
        if not str(okul.district or "").strip():
            uyarilar.ekle(UYARI_MUHATAP_ILCE_YOK)
        return mem_muhatabi(MEM_ILCE, il=okul.province, ilce=okul.district)
    idare = " ".join(secim.muhatap.idare.split())
    if not idare:
        uyarilar.ekle(UYARI_MUHATAP_BOS)
        idare = MUHATAP_YERI
    return idare, " ".join(secim.muhatap.birim.split())


def e12_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E12'nin içerik modeli (tasarım §9.3 "Okul idaresinin resmî yazıları", §9.6 E12; RYUE md. 10-18):
    okul antedi (md. 10/3), "Sayı:" yer tutucu ve tarih aynı satırda (md. 11, 12; U20: sayı okulun
    yazışma sisteminde verilir), konu (md. 13/1), muhatap (md. 14; S11 (a), basımda düzenlenir),
    girintili metin paragrafları (md. 16/4; üst makama "arz ederim", md. 16/12), imza bölümü (md. 17):
    Yönetim Kurulu adına Birlik Başkanı (yeni; görev bölümünden önce "………", U21) solda, Okul Müdürü
    (üst unvan) sağda (md. 17/11); ek E11 (md. 18). Taslağı program yöneticisi hazırlar, kâğıdı müdür
    imzalar (KE-19). Tarih üretim günüdür. Yazı okul dışına gider: kişisel veri dipnotu basılmaz."""
    kurul = _ibra_edilmemis_kurul(konu)
    uyarilar = _Uyarilar()
    uyarilar.ekle(UYARI_SAYI)
    muhatap, birim = _muhatap(secim, uyarilar)
    tur = TUR_ADLARI[str(kurul.kind)]
    gun = _gun(_yapildigi_gun(kurul))
    baskan = _imzaci_gorevli_adi(
        kurul, MembershipRole.BASKAN, UNVAN_BIRLIK_BASKANI, UYARI_YENI_BASKAN_YOK, uyarilar
    )
    teslim_alan = _teslim_alan(kurul)
    okul = SchoolConfig.load()
    belge = evrak.Belge(
        kod=E12,
        antet=evrak.okul_anteti(okul_adi=okul.school_name, ilce=okul.district),
        bloklar=(
            evrak.ResmiYazi(
                sayi=BOS,
                tarih=_gun(timezone.localdate()),
                konu=E12_KONU,
                muhatap=muhatap,
                birim=birim,
            ),
            *(
                evrak.MetinParagrafi(metin.format(gun=gun, tur=tur, teslim_alan=teslim_alan))
                for metin in E12_METIN
            ),
            evrak.ResmiImza(
                sahipler=(
                    evrak.ImzaSahibi(baskan, UNVAN_YK_ADINA_BASKAN),
                    evrak.ImzaSahibi(_mudur_adi(uyarilar), UNVAN_OKUL_MUDURU),
                )
            ),
            evrak.Ekler((BELGE_ADLARI[E11],)),
        ),
    )
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# E13 — genel kurul sonuç bildirimi (okul müdürlüğüne)
# ---------------------------------------------------------------------------
def _sonuc_bilgisi(
    kurul: GeneralAssembly, turler: set[str], uyarilar: _Uyarilar
) -> list[tuple[str, str]]:
    bilgi = [
        (SATIR_TUR, TUR_BASLIKLARI[str(kurul.kind)]),
        (SATIR_GUN_YER, _gun_yer(kurul, uyarilar)),
        (SATIR_KATILAN, _sayi(_katilan(kurul))),
    ]
    if AgendaItemKind.IBRA in turler:
        for satir, sonuc in (
            (SATIR_YK_IBRASI, kurul.discharge_yk),
            (SATIR_DK_IBRASI, kurul.discharge_dk),
        ):
            if not sonuc:
                uyarilar.ekle(UYARI_IBRA_YOK)
            bilgi.append((satir, str(Discharge(sonuc).label) if sonuc else BOS))
    if AgendaItemKind.TAHMINI_BUTCE in turler:
        butce = (
            AgendaItem.objects.filter(
                assembly=kurul, kind=AgendaItemKind.TAHMINI_BUTCE, removed_by_vote=False
            )
            .order_by("order")
            .first()
        )
        # Oyla girilmiş sonuç da "görüşüldü"dür (U22; E10'un `_sonuc_metni` ile aynı).
        gorusuldu = butce is not None and bool(butce.result)
        if not gorusuldu:
            uyarilar.ekle(UYARI_SONUC_YOK)
        bilgi.append((SATIR_BUTCE, SONUC_BUTCE if gorusuldu else BOS))
    return bilgi


def _uye_satirlari(
    kurul: GeneralAssembly, organ: str, uyarilar: _Uyarilar
) -> tuple[tuple[str, ...], ...]:
    satirlar = tuple(
        (
            str(sira),
            _ad(u.person, uyarilar),
            KOLTUK_ADLARI.get(str(u.seat_type), BOS),
            str(MembershipRole(u.role).label) if u.role else "",
        )
        for sira, u in enumerate(_kurul_secilenleri(kurul, organ), start=1)
    )
    if not satirlar:
        uyarilar.ekle(UYARI_SECIM_YOK)
        return ((BOS, BOS, BOS, ""),)
    return satirlar


def _sonraki_isler(
    kurul: GeneralAssembly, turler: set[str], uyarilar: _Uyarilar
) -> tuple[tuple[str, str, str], ...]:
    """D bölümü (tasarım §9.6 E13 "sonraki adımlar tarihli"): görev bölümlerinin son günü kural
    paketinden (başlangıç genel kurulun yapıldığı gün; md. 12/3, 14/1), banka imza yetkisi (md. 18/2),
    TEFBİS girişi (md. 23/5; süre kural değildir), ibra edilmediyse il/ilçe millî eğitim müdürlüğüne
    yazı (md. 11/1-ç)."""
    gun = _yapildigi_gun(kurul)
    donem = genel_kurul.secim_donemi(kurul)
    satirlar: list[tuple[str, str, str]] = []
    gorev_bolumleri = []
    if AgendaItemKind.SECIM_YK in turler:
        gorev_bolumleri.append((IS_YK_GOREV_BOLUMU, _YK_GOREV_BOLUMU))
    if AgendaItemKind.SECIM_DK in turler and kurul.kind == AssemblyKind.OLAGAN:
        gorev_bolumleri.append((IS_DK_GOREV_BOLUMU, _DK_GOREV_BOLUMU))
    for is_, kural_id in gorev_bolumleri:
        sure = None if gun is None else _sure_son_gunu(kural_id, gun, donem)
        if sure is None:
            uyarilar.ekle(UYARI_KURAL_DEGERI_YOK)
            satirlar.append((is_, BOS, BOS))
        else:
            satirlar.append((is_, SON_GUN_DEGERI.format(gun=_gun(sure[0])), sure[1]))
    if AgendaItemKind.SECIM_YK in turler:
        satirlar.append((IS_BANKA, GOREV_BOLUMUNDEN_SONRA, DAYANAK_BANKA))
    satirlar.append((IS_TEFBIS, GENEL_KURULDAN_SONRA, DAYANAK_TEFBIS))
    if kurul.discharge_yk == Discharge.EDILMEDI:
        yeni_yk = _secilen_kurullar(kurul, turler)[0]
        satirlar.append((IS_MEM_YAZILARI[yeni_yk], GENEL_KURULDAN_SONRA, DAYANAK_MEM_YAZISI))
    return tuple(satirlar)


def e13_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E13'ün içerik modeli (tasarım §9.6 E13; GNL-OAB-FR-005 A, C): genel kurulun sonucu (ibra,
    tahmini bütçe yalnız "görüşüldü", U22), seçilenler (E10 ile aynı kayıtlar), tarihli sonraki işler;
    konum cümlesi TFB imzanın hemen üstünde (tasarım §9.2). İmza Birlik Başkanı (yeni) + Sekreter (yeni;
    görev bölümünden önce "………", U21) ve "Teslim alan: Okul Müdürü" (tasarım §9.3). Bildirim okul
    uygulamasıdır: "Yönetmelik gereği" denmez (MB-11)."""
    kurul = _yapilmis_kurul(konu)
    uyarilar = _Uyarilar()
    turler = _gundem_turleri(kurul)
    bloklar: list[evrak.Blok] = [
        _baslik(E13, kurul),
        evrak.Paragraf(
            E13_GIRIS.format(gun=_gun(_yapildigi_gun(kurul)), tur=TUR_ADLARI[str(kurul.kind)])
        ),
        evrak.AltBaslik(E13_BOLUMLER[0]),
        evrak.Tablo(
            basliklar=KONU_BILGI,
            satirlar=tuple(_sonuc_bilgisi(kurul, turler, uyarilar)),
            oranlar=(2, 3),
        ),
    ]
    if AgendaItemKind.SECIM_YK in turler:
        bloklar += [
            evrak.AltBaslik(E13_BOLUMLER[1]),
            evrak.Tablo(
                basliklar=UYE_BASLIKLARI,
                satirlar=_uye_satirlari(kurul, OrganType.YONETIM_KURULU, uyarilar),
                oranlar=(1, 6, 3, 3),
            ),
        ]
    if AgendaItemKind.SECIM_DK in turler and kurul.kind == AssemblyKind.OLAGAN:
        bloklar += [
            evrak.AltBaslik(E13_BOLUMLER[2]),
            evrak.Tablo(
                basliklar=UYE_BASLIKLARI,
                satirlar=_uye_satirlari(kurul, OrganType.DENETLEME_KURULU, uyarilar),
                oranlar=(1, 6, 3, 3),
            ),
        ]
    baskan = _imzaci_gorevli_adi(
        kurul, MembershipRole.BASKAN, UNVAN_BIRLIK_BASKANI, UYARI_YENI_BASKAN_YOK, uyarilar
    )
    sekreter = _imzaci_gorevli_adi(
        kurul, MembershipRole.SEKRETER, UNVAN_SEKRETER, UYARI_YENI_SEKRETER_YOK, uyarilar
    )
    bloklar += [
        evrak.AltBaslik(E13_BOLUMLER[3]),
        evrak.Tablo(
            basliklar=SONRAKI_BASLIKLARI,
            satirlar=_sonraki_isler(kurul, turler, uyarilar),
            oranlar=(6, 3, 2),
        ),
        evrak.KonumCumlesi(evrak.TFB),
        evrak.Imza(
            sahipler=(
                evrak.ImzaSahibi(baskan, UNVAN_BIRLIK_BASKANI),
                evrak.ImzaSahibi(sekreter, UNVAN_SEKRETER),
                evrak.ImzaSahibi(_mudur_adi(uyarilar), UNVAN_TESLIM_ALAN),
            )
        ),
        evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
    ]
    belge = evrak.Belge(kod=E13, antet=_antet(), bloklar=tuple(bloklar))
    return belge, tuple(uyarilar.liste)


# ---------------------------------------------------------------------------
# E14 — yıllık iş takvimi (kişisiz)
# ---------------------------------------------------------------------------
def _donem(konu: models.Model) -> OabTerm:
    if not isinstance(konu, OabTerm):
        raise ValueError(KONU_GECERSIZ)
    return konu


def _sonraki_olagan(donem: OabTerm) -> GeneralAssembly | None:
    """Dönemi kapatacak olağan genel kurul (`term` kapanacak dönemdir; iptal edilen sayılmaz)."""
    kurul: GeneralAssembly | None = (
        GeneralAssembly.objects.filter(term=donem, kind=AssemblyKind.OLAGAN)
        .exclude(status=AssemblyStatus.IPTAL)
        .order_by("-pk")
        .first()
    )
    return kurul


def _kural_satiri(
    kural_id: str,
    is_: str,
    gun: date,
    donem: OabTerm,
    tarih: Callable[[int], str],
    uyarilar: _Uyarilar,
) -> tuple[str, str, str, str]:
    """Süre kuralının satırı: tarih (kural değerinden), iş, kural kimliği ve atıf (sözlük §2 istisna
    3). Olay gününde değer yoksa tarih "………" ve uyarı; kimlik yine basılır."""
    try:
        kayit = kural_kaydi(kural_id, tarih=gun, donem=donem)
    except YururlukteDegerYok:
        uyarilar.ekle(UYARI_KURAL_DEGERI_YOK)
        return BOS, is_, kural_id, BOS
    return tarih(int(kayit["deger"])), is_, kural_id, atif_metni(kayit)


def _son_gun(gun: date) -> str:
    return SON_GUN_DEGERI.format(gun=_gun(gun))


def _sonrasi(baslangic: date) -> Callable[[int], str]:
    """Başlangıçtan kural değeri kadar gün sonrasının son günü ("en geç gg.aa.yyyy")."""

    def tarih(gun: int) -> str:
        return _son_gun(baslangic + timedelta(days=gun))

    return tarih


def _oncesi(bitis: date) -> Callable[[int], str]:
    """Bitişten kural değeri kadar gün öncesinin son günü ("en geç gg.aa.yyyy")."""

    def tarih(gun: int) -> str:
        return _son_gun(bitis - timedelta(days=gun))

    return tarih


def _kalip(metin: str) -> Callable[[int], str]:
    """Tarihsiz satırın göreli metni; kural değeri `{gun}` yerine yazılır."""

    def tarih(gun: int) -> str:
        return metin.format(gun=gun)

    return tarih


def _ay_sonu(yil: int) -> Callable[[int], str]:
    """`yil` yılında kural değerindeki ayın son günü ("en geç gg.aa.yyyy")."""

    def tarih(ay: int) -> str:
        return _son_gun(date(yil, ay, calendar.monthrange(yil, ay)[1]))

    return tarih


def _bos_tarih(_deger: int) -> str:
    return BOS


def _kural_satirlari(donem: OabTerm, uyarilar: _Uyarilar) -> tuple[tuple[str, str, str, str], ...]:
    """A bölümü: görev bölümleri (dönemin başlangıcından), dönemi kapatacak olağan genel kurulun son
    ayı (ders yılının bitiş yılında; md. 9/1), ilanı ve ikinci toplantısı (planlanmışsa birinci
    toplantının gününden tarihli, değilse göreli), kantin varsa arz bedelinin son günleri: kiraya
    vermede sözleşmedeki (EK-2 md. 7) ve Yönetmelikteki (md. 17/1-a-1), birlikçe işletmede yalnız
    Yönetmelikteki (md. 17/1-b-1; hangisinin basılacağı kuralın `kosul`'undan). Değerler kural
    paketindendir (D8)."""
    bugun = _olay_gunu(donem)
    satirlar: list[tuple[str, str, str, str]] = []
    baslangic = donem.start_date
    if baslangic is None:
        uyarilar.ekle(UYARI_DONEM_BASLANGICI_YOK)
    for kural_id, is_ in (
        (_YK_GOREV_BOLUMU, IS_YK_GOREV_BOLUMU),
        (_DK_GOREV_BOLUMU, IS_DK_GOREV_BOLUMU),
    ):
        if baslangic is None:
            satirlar.append(_kural_satiri(kural_id, is_, bugun, donem, _bos_tarih, uyarilar))
        else:
            satirlar.append(
                _kural_satiri(kural_id, is_, baslangic, donem, _sonrasi(baslangic), uyarilar)
            )
    kurul = _sonraki_olagan(donem)
    birinci = (
        None
        if kurul is None or kurul.first_meeting_at is None
        else genel_kurul.yerel_gun(kurul.first_meeting_at)
    )
    ilan = _kalip(ILAN_GORELI) if birinci is None else _oncesi(birinci)
    ikinci = _kalip(IKINCI_GORELI) if birinci is None else _sonrasi(birinci)
    bitis_yili = donem.school_year.end_date.year
    satirlar += [
        _kural_satiri(_GK_ILAN, IS_ILAN, bugun, donem, ilan, uyarilar),
        _kural_satiri(_GK_SON_AY, IS_OLAGAN_GK, bugun, donem, _ay_sonu(bitis_yili), uyarilar),
        _kural_satiri(_GK_IKINCI, IS_IKINCI_TOPLANTI, bugun, donem, ikinci, uyarilar),
    ]
    kantin = str(SchoolConfig.load().canteen_mode or "")
    if not kantin:
        uyarilar.ekle(UYARI_KANTIN_BICIMI_YOK)
    elif kantin != CanteenMode.KANTIN_YOK:
        for kural_id, is_ in (
            (_ARZ_SOZLESME, IS_ARZ_SOZLESME),
            (_ARZ_YONETMELIK, IS_ARZ_YONETMELIK),
        ):
            if _kantin_kosulu_tutar(kural_id, kantin, bugun, donem):
                satirlar.append(
                    _kural_satiri(kural_id, is_, bugun, donem, _kalip(ARZ_GUNU), uyarilar)
                )
    return tuple(satirlar)


def _kantin_kosulu_tutar(kural_id: str, kantin: str, gun: date, donem: OabTerm) -> bool:
    """Arz bedeli kuralının okulun kantin işletme biçimine uygulanıp uygulanmadığı kural paketinin
    `kosul` alanından okunur (D8; tasarım §6.1): sözleşmedeki son gün (EK-2 md. 7) yalnız kiraya
    vermededir; Yönetmelikteki son gün (md. 17/1-a-1, b-1) koşulsuzdur, birlikçe işletmede arz
    bedelini birlik öder. Olay gününde değeri olmayan kuralın satırı `_kural_satiri`'nin uyarısıyla
    basılır."""
    try:
        kayit = kural_kaydi(kural_id, tarih=gun, donem=donem)
    except YururlukteDegerYok:
        return True
    izinli = kayit.get("kosul", {}).get("okul.kantin")
    return izinli is None or kantin in izinli


def _plan_satirlari(donem: OabTerm, uyarilar: _Uyarilar) -> tuple[tuple[str, str, str], ...]:
    """B bölümü (okul planı; kural değildir): ders yılı ve ders dönemleri, yönetim kurulunun aylık
    toplantı günü (dönem ayarı; md. 13/3) ve Denetleme Kurulunun denetim planı (dönem ayarı; md.
    14/4)."""
    yil = donem.school_year
    satirlar: list[tuple[str, str, str]] = [
        (_gun(yil.start_date), IS_DERS_YILI_BASI, KAYNAK_DERS_YILI)
    ]
    for ders_donemi in SchoolTerm.objects.filter(school_year=yil).order_by("sequence"):
        satirlar.append(
            (
                DONEM_ARALIGI.format(
                    bas=_gun(ders_donemi.start_date), son=_gun(ders_donemi.end_date)
                ),
                IS_DERS_DONEMI.format(sira=ders_donemi.sequence),
                KAYNAK_DERS_YILI,
            )
        )
    toplanti = " ".join(str(donem.yk_meeting_day_rule or "").split())
    if not toplanti:
        uyarilar.ekle(UYARI_YK_TOPLANTISI_YOK)
    satirlar.append((toplanti or BOS, IS_YK_TOPLANTISI, KAYNAK_DONEM))
    plan = sorted(date.fromisoformat(str(gun_)) for gun_ in donem.dk_audit_plan_dates or [])
    if not plan:
        uyarilar.ekle(UYARI_DENETIM_PLANI_YOK)
        satirlar.append((BOS, IS_DK_DENETIMI.format(sira=1), KAYNAK_DONEM))
    satirlar += [
        (_gun(gun_), IS_DK_DENETIMI.format(sira=sira), KAYNAK_DONEM)
        for sira, gun_ in enumerate(plan, start=1)
    ]
    satirlar.append((_gun(yil.end_date), IS_DERS_YILI_SONU, KAYNAK_DERS_YILI))
    return tuple(satirlar)


def e14_belgesi(konu: models.Model, secim: Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
    """E14'ün içerik modeli (tasarım §7.10, §9.6 E14; GNL-OAB-RH-001 Bölüm 6): kişisiz, imzasız. Süre
    kuralı satırları kural kimliği ve atıf taşır; okul planı satırları ayrı bölümdedir ve kural
    değildir. Rehberin "öneri" satırları (kural paketinde ve programın kayıtlarında karşılığı olmayan
    takvim önerileri) basılmaz. PDF saklanır, Excel kayıtlı içerikten çizilir (U18). Hazırlıktaki
    dönemin takvimi yazılmaz (`DonemYazilamaz`; 8. adımın kararı)."""
    donem = _donem(konu)
    uyarilar = _Uyarilar()
    belge = evrak.Belge(
        kod=E14,
        antet=_antet(),
        bloklar=(
            evrak.Baslik(BELGE_ADLARI[E14], alt=str(donem.name)),
            evrak.Paragraf(E14_GIRIS),
            evrak.AltBaslik(E14_BOLUMLER[0]),
            evrak.Tablo(
                basliklar=KURAL_BASLIKLARI,
                satirlar=_kural_satirlari(donem, uyarilar),
                oranlar=(4, 6, 5, 2),
            ),
            evrak.AltBaslik(E14_BOLUMLER[1]),
            evrak.Tablo(
                basliklar=PLAN_BASLIKLARI,
                satirlar=_plan_satirlari(donem, uyarilar),
                oranlar=(4, 7, 4),
            ),
        ),
    )
    return belge, tuple(uyarilar.liste)


#: Kodun kişisiz içerik kurucusu (E05-E08, E64 9. adımda; E09-E14 10. adımda; E04 metinlerin
#: onayından sonra, plan F2 §9 S8 (i)).
KURUCULAR: dict[str, Kurucu] = {
    E05: e05_belgesi,
    E06: e06_belgesi,
    E07: e07_belgesi,
    E08: e08_belgesi,
    E09: e09_belgesi,
    E10: e10_belgesi,
    E11: e11_belgesi,
    E12: e12_belgesi,
    E13: e13_belgesi,
    E14: e14_belgesi,
    E64: e64_belgesi,
}
#: Veli adlı kipin içerik kurucusu (E07 ve E08).
ADLI_KURUCULAR: dict[str, AdliKurucu] = {
    E07: e07_adli_belgesi,
    E08: e08_adli_belgesi,
}


# ---------------------------------------------------------------------------
# Ortak yardımcılar
# ---------------------------------------------------------------------------
def _konu_turu(kod: str) -> type[models.Model]:
    if kod in GENEL_KURUL_KODLARI:
        return GeneralAssembly
    if kod == E14:
        return OabTerm
    return SchoolConfig


def _konu_ve_donem(kod: str, konu: models.Model) -> tuple[models.Model, OabTerm | None]:
    """Konunun güncel kaydı ve evrakın dönemi (modül başlığı "Konu ve dönem")."""
    tur = _konu_turu(kod)
    if not isinstance(konu, tur) or konu.pk is None:
        raise ValueError(KONU_GECERSIZ)
    if tur is GeneralAssembly:
        kurul = GeneralAssembly.objects.select_related(
            "term__rule_package", "opens_term__rule_package"
        ).get(pk=konu.pk)
        return kurul, genel_kurul.kural_donemi(kurul)
    if tur is OabTerm:
        donem = OabTerm.objects.select_related("rule_package").get(pk=konu.pk)
        return donem, donem
    return SchoolConfig.load(), None


def _secim_denetimi(kod: str, secim: Secim, *, adli: bool = False) -> None:
    """Kip ve toplantı koda uymalı (modül başlığı "Kip ve toplantı"); muhatap yalnız resmî yazıda."""
    if kod in KIPLI_KODLAR:
        beklenen = DocumentVariant.ADLI if adli else DocumentVariant.KISISIZ
        if secim.kip != beklenen:
            raise ValueError(KIP_GECERSIZ)
    elif secim.kip:
        raise ValueError(KIP_GECERSIZ)
    if kod in TOPLANTILI_KODLAR:
        if secim.toplanti not in AssemblyMeeting.values:
            raise ValueError(TOPLANTI_GECERSIZ)
    elif secim.toplanti:
        raise ValueError(TOPLANTI_GECERSIZ)
    if secim.muhatap is not None and kod not in MUHATAPLI_KODLAR:
        raise ValueError(MUHATAP_GECERSIZ)


def _cizim(belge: evrak.Belge, bicim: str) -> bytes:
    """Biçimin çizicisi (tek içerik, dört çizici)."""
    if bicim == DocumentFormat.PDF:
        return evrak.pdf_ciz(belge)
    if bicim == DocumentFormat.DOCX:
        return evrak.docx_ciz(belge)
    if bicim == DocumentFormat.XLSX:
        return evrak.xlsx_ciz(belge)
    if bicim == DocumentFormat.HTML:
        return evrak.web_html_ciz(belge).encode("utf-8")
    raise ValueError(BICIM_GECERSIZ)


def dosya_adi(kod: str, gun: date, bicim: str, *, toplanti: str = "", adli: bool = False) -> str:
    """Kaydedilen dosyanın adı: belge + kapsam (toplantı) + tarih (sözlük §3). Kişi adı, dönem adı ve
    sınıf taşımaz: 'Genel-Kurul-Duyurusu-İkinci-Toplantı_20.11.2026.pdf'."""
    kok = ADLI_DOSYA_ADI_KOKLERI[kod] if adli else DOSYA_ADI_KOKLERI[kod]
    if toplanti:
        kok = f"{kok}-{TOPLANTI_KAPSAMLARI[toplanti]}"
    return f"{kok}_{gun:%d.%m.%Y}.{UZANTILAR[bicim]}"


def indirme_yaniti(icerik: bytes, *, dosya_adi: str, mime: str) -> FileResponse:
    """Bellekteki dosyanın indirme yanıtı: ek olarak, önbelleğe alınmadan (`no-store`; R9). Türkçe
    harfli ad Content-Disposition'a Django'nun kodlamasıyla girer (E63'ün kalıbı)."""
    from io import BytesIO

    yanit = FileResponse(BytesIO(icerik), as_attachment=True, filename=dosya_adi, content_type=mime)
    yanit["Cache-Control"] = "no-store"
    return yanit


def _rol_daraltmasi(roller: frozenset[str]) -> None:
    kim = yazar()
    if kim is None or kim.sistem_mi or kim.rol not in roller:
        raise RolYetkisiz


def _e05_yetkisi(konu: models.Model) -> None:
    """E05'in üreten rolü çağırana göredir (tasarım §9.6 E05, MB-3): müdürün ve Denetleme Kurulunun
    çağrısında çağrının sahiplikli eylemi (yalnız müdürün ya da Denetleme Kurulunun hesabı; ¹, ⁵),
    öteki kollarda genel kurul yazma kapısı ve `E05_URETENLER`. Çağrılmamış genel kurulda
    `CAGRI_YOK`."""
    if not isinstance(konu, GeneralAssembly) or konu.pk is None:
        raise ValueError(KONU_GECERSIZ)
    kurul = GeneralAssembly.objects.get(pk=konu.pk)
    kol = cagri_kolu(kurul)
    if genel_kurul.cagri_sahibi(kurul) is not None:
        rol_izinleri.yetki_oturum(
            genel_kurul.cagri_yazisi_eylemi(kurul), genel_kurul.cagri_yetki_kaydi(kurul)
        )
        return
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.GENEL_KURUL_YAZMA)
    _rol_daraltmasi(E05_URETENLER[kol])


def _uretim_yetkisi(kod: str, konu: models.Model) -> None:
    """Üreten rol (modül başlığı "Üretim"): E05'te çağırana göre (`_e05_yetkisi`); öteki genel kurul
    belgelerinde genel kurul yazma kapısı, sonra tasarım §9.6'nın "Üreten"i (`URETEN_ROLLER`)."""
    if kod == E05:
        _e05_yetkisi(konu)
        return
    if kod in GENEL_KURUL_KODLARI:
        rol_izinleri.yetki_oturum(rol_izinleri.Eylem.GENEL_KURUL_YAZMA)
    _rol_daraltmasi(URETEN_ROLLER[kod])


# ---------------------------------------------------------------------------
# Üretim (kişisiz)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Uretim:
    """Üretimin sonucu: evrak kaydı ve basım uyarıları (belgeye basılmaz)."""

    kayit: GeneratedDocument
    uyarilar: tuple[str, ...]


def uret(
    kod: str,
    konu: models.Model,
    *,
    kip: str = "",
    toplanti: str = "",
    muhatap: Muhatap | None = None,
) -> Uretim:
    """Evrakı üretir ve kaydeder (modül başlığı "Üretim"); yeni sürümün kaydını döner. `muhatap`
    yalnız resmî yazının (E12) basımda düzenlenen muhatabıdır (plan F2 §7 U20)."""
    if kod not in KURUCULAR:
        raise ValueError(KOD_GECERSIZ)
    secim = Secim(kip=kip, toplanti=toplanti, muhatap=muhatap)
    _secim_denetimi(kod, secim)
    yazma_kapisi()
    app_password.require_password_set()
    _uretim_yetkisi(kod, konu)
    guncel, donem = _konu_ve_donem(kod, konu)
    belge, uyarilar = KURUCULAR[kod](guncel, secim)
    if belge.kod != kod:
        raise ValueError(KOD_GECERSIZ)
    saklananlar = [bicim for bicim in BICIMLER[kod] if bicim in SAKLANAN_BICIMLER]
    cizimler = {bicim: _cizim(belge, bicim) for bicim in saklananlar}
    gun = timezone.localdate()
    with transaction.atomic():
        kayit = evrak_servisi.kaydet(
            belge,
            konu=guncel,
            bicimler=BICIMLER[kod],
            donem=donem,
            hazirlik_yazimi=kod in GENEL_KURUL_KODLARI,
            kip=secim.kip,
            toplanti=secim.toplanti,
        )
        for bicim in saklananlar:
            evrak_servisi.dosya_ekle(
                kayit,
                cizimler[bicim],
                bicim=bicim,
                dosya_adi=dosya_adi(kod, gun, bicim, toplanti=secim.toplanti),
            )
    return Uretim(kayit=kayit, uyarilar=uyarilar)


# ---------------------------------------------------------------------------
# Veli adlı çıktı (R9; U15)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AdliCikti:
    """Veli adlı çıktının sonucu: verilecek bayt, dosya adı ve türü; kayıt ve basım uyarıları. Bayt
    hiçbir yerde saklanmaz (modül başlığı "Veli adlı çıktı")."""

    icerik: bytes
    dosya_adi: str
    mime: str
    kayit: GeneratedDocument
    uyarilar: tuple[str, ...]


def adli_uret_ve_ver(
    kod: str, kurul: GeneralAssembly, *, bicim: str, toplanti: str = ""
) -> AdliCikti:
    """Veli adlı belgeyi tek istekte üretir ve verir (modül başlığı "Veli adlı çıktı")."""
    if kod not in ADLI_KURUCULAR:
        raise ValueError(KOD_GECERSIZ)
    if bicim not in ADLI_BICIMLER[kod]:
        raise ValueError(BICIM_GECERSIZ)
    secim = Secim(kip=DocumentVariant.ADLI, toplanti=toplanti)
    _secim_denetimi(kod, secim, adli=True)
    yazma_kapisi()
    app_password.require_password_set()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.KISISEL_VERI_CIKTISI)
    guncel, donem = _konu_ve_donem(kod, kurul)
    if not isinstance(guncel, GeneralAssembly):  # adlı kipin kodları genel kurul belgesidir
        raise ValueError(KONU_GECERSIZ)
    icerik = ADLI_KURUCULAR[kod](guncel, secim.toplanti)
    if icerik.belge.kod != kod or icerik.satir_sayisi < 0:
        raise ValueError(KOD_GECERSIZ)
    dosya = _cizim(icerik.belge, bicim)
    ozet = hashlib.sha256(dosya).hexdigest()
    with transaction.atomic():
        kayit = evrak_servisi.kaydet(
            icerik.belge,
            konu=guncel,
            bicimler=(bicim,),
            donem=donem,
            kisi_listesi=True,
            satir_sayisi=icerik.satir_sayisi,
            hazirlik_yazimi=True,
            kip=secim.kip,
            toplanti=secim.toplanti,
        )
        denetim_izi.basim(
            model=str(kayit.subject_type), object_id=str(kayit.subject_id), kod=kod, sha256=ozet
        )
        erisim_gunlugu.yaz(
            AccessKind.VELI_LISTESI_CIKTISI,
            model=GeneralAssembly,
            object_id=guncel.pk,
            document_sha256=ozet,
            row_count=icerik.satir_sayisi,
        )
    # Kişi adı yazılmaz: kod ve satır sayısı yeter (modül başlığı).
    logger.info("Veli adlı evrak verildi (%s, %s satır).", kod, icerik.satir_sayisi)
    return AdliCikti(
        icerik=dosya,
        dosya_adi=dosya_adi(kod, timezone.localdate(), bicim, toplanti=secim.toplanti, adli=True),
        mime=MIME_TURLERI[bicim],
        kayit=kayit,
        uyarilar=icerik.uyarilar,
    )


# ---------------------------------------------------------------------------
# Liste ve basım
# ---------------------------------------------------------------------------
def evrak_listesi(konu: models.Model) -> list[GeneratedDocument]:
    """Konunun geçerli genel kurul evrakı kayıtları (kod, kip ve toplantı sırasıyla); veli adlı
    kayıtlar dahil (yalnız tür, tarih ve satır sayısıyla; dosyaları yoktur)."""
    return list(
        GeneratedDocument.objects.filter(
            subject_type=denetim_izi.model_etiketi(type(konu)),
            subject_id=denetim_izi.kimlik_metni(type(konu), konu.pk),
            doc_type__in=KODLAR,
            status=DocumentStatus.GECERLI,
        ).order_by("doc_type", "variant", "meeting", "-version")
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

    Kod bu belgelerden biri değilse, biçim kayıtta yoksa, kayıt veli adı taşıyorsa ya da saklanan
    dosya eklenmemişse 404. Kayıtlı içerik tutmuyorsa (`EvrakIcerigiTutmuyor`) ya da dosya
    okunamazsa bayt verilmez, iz yazılmaz.
    """
    kod = str(kayit.doc_type)
    if kod not in KODLAR or bicim not in kayit.formats or kayit.personal_list:
        raise Http404
    _okuma_yetkisi(kod)
    ad = dosya_adi(kod, timezone.localdate(kayit.generated_at), bicim, toplanti=str(kayit.meeting))
    if bicim in SAKLANAN_BICIMLER:
        ek = kayit.ekler().filter(mime=evrak_servisi.BICIM_TURLERI[bicim]).last()
        if ek is None:
            raise Http404
        yanit = dosya_deposu.indirme_yaniti(ek, dosya_adi=ad)
        ozet = str(ek.sha256)
    else:
        icerik = _cizim(evrak_servisi.yeniden_ciz(kayit), bicim)
        yanit = indirme_yaniti(icerik, dosya_adi=ad, mime=MIME_TURLERI[bicim])
        ozet = hashlib.sha256(icerik).hexdigest()
    with transaction.atomic():
        denetim_izi.basim(
            model=str(kayit.subject_type), object_id=str(kayit.subject_id), kod=kod, sha256=ozet
        )
    return yanit


def bicim_coz(metin: str, bicimler: Mapping[str, str] = UZANTILAR) -> str:
    """Yoldaki biçim ('pdf', 'docx', 'xlsx', 'html') → kaydın biçimi; tanınmazsa 404."""
    for bicim, uzanti in bicimler.items():
        if metin == uzanti:
            return bicim
    raise Http404


# ---------------------------------------------------------------------------
# Uçların okumaları (plan F2 11. adım: katalog, muhatap önerisi, yıllık iş takvimi, E12'nin evrak kaydı)
# ---------------------------------------------------------------------------
#: E04 üretilmez: dört alt metnin kullanıcı onayı beklenir (plan F2 §9 S8 (i), 10. adımın notu).
URETILEMEZ_NEDENLERI: Final[dict[str, str]] = {
    E04: "Kişisel veri aydınlatma metninin dört alt metni onay bekliyor; belge bu sürümde üretilmez.",
}
#: Belgenin konusu (katalog; modül başlığı "Konu ve dönem").
KONU_GENEL_KURUL: Final = "genel_kurul"
KONU_DONEM: Final = "donem"
KONU_OKUL: Final = "okul"
#: E12'nin muhatap seçenekleri (plan F2 §7 U20, kullanıcı kararı S11 (a); varsayılan ilçe).
MUHATAP_BIRIMLERI: Final[dict[str, str]] = {"ILCE": MEM_ILCE, "IL": MEM_IL}
VARSAYILAN_MUHATAP: Final = "ILCE"
MUHATAP_SECIMI_GECERSIZ: Final = "Muhatap il ya da ilçe millî eğitim müdürlüğü olmalıdır."


def katalog() -> list[dict[str, object]]:
    """Genel kurul evrakının kataloğu (tasarım §9.5): kod, ad, konu, biçimler, kip ve toplantı
    seçenekleri, üreten roller ve üretilebilirlik. Kurucusu olmayan kod (E04) katalogda durur ama
    üretilmez; nedeni yanındadır. Kişisizdir, yazmaz."""
    satirlar: list[dict[str, object]] = []
    for kod in KODLAR:
        tur = _konu_turu(kod)
        konu = (
            KONU_GENEL_KURUL
            if tur is GeneralAssembly
            else KONU_DONEM
            if tur is OabTerm
            else KONU_OKUL
        )
        uretilebilir = kod in KURUCULAR
        satirlar.append(
            {
                "kod": kod,
                "ad": BELGE_ADLARI[kod],
                "konu": konu,
                "bicimler": list(BICIMLER[kod]),
                "kipler": [DocumentVariant.KISISIZ, DocumentVariant.ADLI]
                if kod in KIPLI_KODLAR
                else [],
                "adli_bicimler": list(ADLI_BICIMLER.get(kod, ())),
                "toplantili": kod in TOPLANTILI_KODLAR,
                "muhatapli": kod in MUHATAPLI_KODLAR,
                "ureten_roller": sorted(URETEN_ROLLER[kod]),
                "okuma_satiri": OKUMA_SATIRLARI[kod].value,
                "uretilebilir": uretilebilir,
                "uretilemez_nedeni": ""
                if uretilebilir
                else URETILEMEZ_NEDENLERI.get(kod, KOD_GECERSIZ),
            }
        )
    return satirlar


def muhatap_onerileri() -> dict[str, dict[str, str]]:
    """E12'nin muhatap önerileri (il ve ilçe millî eğitim müdürlüğü; okul kartından). Basımda
    düzenlenir; varsayılan ilçedir."""
    okul = SchoolConfig.load()
    sonuc: dict[str, dict[str, str]] = {}
    for anahtar, birim in MUHATAP_BIRIMLERI.items():
        idare, alt = mem_muhatabi(birim, il=okul.province, ilce=okul.district)
        sonuc[anahtar] = {"idare": idare, "birim": alt}
    return sonuc


def muhatap_sec(anahtar: str) -> Muhatap:
    """Seçilen il ya da ilçe millî eğitim müdürlüğünün önerilen muhatabı."""
    if anahtar not in MUHATAP_BIRIMLERI:
        raise ValueError(MUHATAP_SECIMI_GECERSIZ)
    oneri = muhatap_onerileri()[anahtar]
    return Muhatap(idare=oneri["idare"], birim=oneri["birim"])


def yillik_is_takvimi(donem: OabTerm) -> dict[str, object]:
    """Yıllık iş takviminin verisi (Genel Bakış → Yıllık İş Takvimi; M9: her rol okur): E14'ün iki
    bölümünün satırları ve basım uyarıları, aynı kaynaktan (`_kural_satirlari`, `_plan_satirlari`).
    Kişisizdir, okuma yazmaz; hazırlıktaki dönemin de takvimi okunur (basımı yazılmaz)."""
    guncel = OabTerm.objects.select_related("rule_package", "school_year").get(pk=donem.pk)
    uyarilar = _Uyarilar()
    kural_satirlari = [
        {"tarih": tarih, "is": is_, "kural": kural_id, "atif": atif}
        for tarih, is_, kural_id, atif in _kural_satirlari(guncel, uyarilar)
    ]
    plan_satirlari = [
        {"tarih": tarih, "is": is_, "kaynak": kaynak}
        for tarih, is_, kaynak in _plan_satirlari(guncel, uyarilar)
    ]
    return {
        "donem": guncel.pk,
        "bolumler": list(E14_BOLUMLER),
        "kural_satirlari": kural_satirlari,
        "plan_satirlari": plan_satirlari,
        "uyarilar": list(uyarilar.liste),
    }


#: E12'nin evrak kaydı önerisi: giden yazının konusu (RYUE md. 13/1, belgedekiyle aynı).
GIDEN_KONU: Final = E12_KONU


def _resmi_yazi(kayit: GeneratedDocument) -> evrak.ResmiYazi | None:
    belge = evrak_servisi.yeniden_ciz(kayit)
    return next((b for b in belge.bloklar if isinstance(b, evrak.ResmiYazi)), None)


def giden_kayit_onerisi(kayit: GeneratedDocument) -> dict[str, object]:
    """Programın ürettiği giden yazının (E12) gelen-giden evrak kaydı önerisi (plan F2 §7 U20, 10.
    adımın notu: kendiliğinden kaydedilmez, önerilir; kullanıcı onaylayınca `giden_kaydet`). Yazmaz.
    Karşı taraf belgedeki muhataptır (kişi değil, idaredir), konu belgenin konusudur, tarih belgenin
    tarihidir; numara kullanımdaki defterin o yılda sıradaki numarasıdır. Kayıtlıysa kaydın yılı ve
    numarası döner. Defter kayıtlı değilse öneri numarasızdır (`defter` boş)."""
    if str(kayit.doc_type) not in gelen_giden_evrak.GIDEN_KAYDEDILEN_KODLAR:
        raise ValueError(gelen_giden_evrak.URETILEN_EVRAK_GECERSIZ)
    _okuma_yetkisi(str(kayit.doc_type))
    yazi = _resmi_yazi(kayit)
    try:
        gun = (
            datetime.strptime(yazi.tarih, "%d.%m.%Y").date()
            if yazi is not None
            else timezone.localdate()
        )
    except ValueError:
        gun = timezone.localdate()
    karsi_taraf = "" if yazi is None else yazi.muhatap + (f" ({yazi.birim})" if yazi.birim else "")
    onceki = gelen_giden_evrak.giden_kaydi(kayit)
    defter = gelen_giden_evrak.evrak_defteri()
    return {
        "evrak": kayit.pk,
        "kod": str(kayit.doc_type),
        "kayitli": None
        if onceki is None
        else {"id": onceki.pk, "yil": onceki.year, "kayit_no": onceki.record_no},
        "direction": "GIDEN",
        "tarih": gun.isoformat(),
        "counterparty": karsi_taraf,
        "subject": GIDEN_KONU,
        "defter": None if defter is None else defter.pk,
        "onerilen_no": None
        if defter is None
        else gelen_giden_evrak.beklenen_kayit_no(defter, gun.year),
        "gecerli": kayit.status == DocumentStatus.GECERLI,
    }


def giden_kaydet(
    kayit: GeneratedDocument,
    *,
    tarih: date,
    counterparty: str,
    subject: str,
    external_ref: str = "",
    record_no: int | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> gelen_giden_evrak.EvrakKaydiSonucu:
    """Önerinin kullanıcı onayıyla kaydı: giden evrak, yazının üretilen evrak bağıyla
    (`gelen_giden_evrak.evrak_kaydet`; kapısı `Eylem.EVRAK_KAYDI`, M10)."""
    return gelen_giden_evrak.evrak_kaydet(
        direction="GIDEN",
        tarih=tarih,
        counterparty=counterparty,
        subject=subject,
        external_ref=external_ref,
        record_no=record_no,
        generated_document=kayit,
        gerekce=gerekce,
    )
