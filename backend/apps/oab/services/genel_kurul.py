"""Genel kurulun durum makinesi ve hazırlık dönemi (tasarım §5.2.3, §7.1; plan F2 §1.1-1…5, §5.2,
§7 U1-U12, U19, U24; F2 4. adım).

F1c genel kurulun asgari kaydını (dönem bağı, yeter sayının anlık görüntüsü) kurdu; F2 3. adım tasarımın
alanlarını ve model düzeyindeki durum makinesini (`models.genel_kurul`) getirdi. Bu modül geçişlerin
servisidir: planlama, çağrı, ilan, birinci toplantı, yeter sayı yok, ikinci toplantının ilanı ve kendisi,
iptal (4. adım); gündem değişikliği, gündeme bağlılık, karar sonucu, divan, katılım düzeltmesi ve katılım
işareti (5. adım); aday ve seçim, ibra ve "ibra edilmedi" yan akışı, tutanağın tamamlanması ve dönem
geçişinin onayı (6. adım); müdürün ve Denetleme Kurulunun çağrısı (yeni okul daveti, müdürün olağanüstü
çağrısı, md. 14/5 çağrısı), çağrı yazısının gelen-giden evrak bağı ve ilan kanıtının eki (7. adım). Uç
ve ekran 11. adımdadır.

KİM (tasarım §4.4.2 M3 ve §7.1 "Kim" sütunu; Kim matrisi daraltır, genişletemez). Her yazma önce
`Eylem.GENEL_KURUL_YAZMA` kapısından geçer (program yöneticisi ve yönetim kurulu rolleri; müdür ve
Denetleme Kurulu okur), sonra geçişin "Kim"iyle daraltılır: planlama, tarih değişikliği, ilan ve
toplantılar program yöneticisi ve sekreter; yönetim kurulunun çağrısı sekreter (YK kararı); başkanın md.
13/8 çağrısı başkan; üyelerin yazılı başvurusunu program yöneticisi kaydeder; iptal yalnız program
yöneticisi. Gündem, karar, divan ve katılım düzeltmesi tutanağın işidir (§7.1 `YAPILDI →
TUTANAK_TAMAM` "Kim"): program yöneticisi ve sekreter; aday kaydı, seçim, ibra ve tutanağın
tamamlanması da. Dönem geçişini yalnız program yöneticisi onaylar (U32; M1, `Eylem.BIRLIK_DONEMI_YAZMA`).
Katılım işareti veli adını gösterir (R9, dipnot ¹⁰; U33): yalnız program yöneticisi, kişisel veri içeren
çıktı kapısıyla.

MÜDÜR VE DENETLEME KURULU (K2; tasarım §4.4.2 ¹, ⁵, ⁷; §7.1 çağrı satırları; §15 M-5, M-6, M-11; F2 7.
adım). Müdür genel kurulun öteki işlerinde okurdur, yalnız kendi yazısını yazar: yeni açılan okulda
genel kurul daveti (md. 9/1; `Eylem.GENEL_KURUL_YENI_OKUL_DAVETI`) ve olağanüstü genel kurul çağrısı
(md. 9/6, 13/8, 25/2; `Eylem.OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR`). md. 13/8'in çağıranı "başkan ya da
müdür"dür: başkanın hesabından yönetim kurulu kapısıyla, müdürün hesabından müdürün eylemiyle yazılır;
hangisinin yazdığı kayıttadır (`called_by_role`, çağrıda yazanın rolü). Program yöneticisi müdürün yazısının taslağını hazırlamaz (M-11): müdürün çağıranları müdürün hesabı
dışında kaydedilmez. Denetleme Kurulu yalnız denetim modülüne yazar; md. 14/5 çağrısı oradandır
(`Eylem.DK_GENEL_KURUL_YAZMA`): çağrı yalnız md. 6 aykırılık işaretli, aynı dönemin, başka genel kurulu
çağırmamış denetim raporuyla açılır (kullanıcı kararı S6 (ii), sert — hukuken geçersiz işlem); iki bağ
(`call_audit_report`, raporun `escalated_assembly`'si) aynı işlemde yazılır. Müdür ya da Denetleme Kurulu
çağırsa da planlama, ilan ve toplantılar program yöneticisi ve sekreterdedir (§7.1 "Kim").
SAHİPLİK (plan F1b-2 "kayıt sahipliği rol düzeyindedir"; tasarım §4.4.2 "müdür yalnız kendi yazısını
düzenler"): çağrının yazısı çağıranındır (`cagri_sahibi`; md. 13/8'de müdür yazdıysa müdürün). Müdürün ya
da Denetleme Kurulunun çağırdığı genel kurulda çağrıdaki toplantı zamanı, yeri ve gündem sırası ilandan
önce (`CAGRILDI`) yalnız yazının sahibince, çağrının eylemiyle düzenlenir (`_duzenleme_kapisi`); başka rol
değiştirmez. Toplantıdaki gündem değişikliği genel kurulun kararıdır (md. 9/4).
EVRAK DEFTERİ (⁷): müdürün yazısı gelen-giden evrak defterine program tarafından giden evrak olarak
işlenir ve çağrı yazısı bağı (`call_document`) olur (`gelen_giden_evrak.mudur_yazisini_isle`); defter
kaydedilmemişse işlenmez, bilgi satırı döner. Konusu çağıranla genel kurulun türünden seçilir
(`mudur_yazisi_konusu`). Denetleme Kurulunun yazısını program işlemez (DK evrak kaydı yazmaz, M10):
yetkili rolün kaydettiği evrak kaydı çağrıda ya da sonra (`cagri_yazisini_bagla`) bağlanır (tasarım
§5.2.3 `call_document`, plan F2 §1.1-11); bağ girilmemişse bilgi satırı döner. Bağı iptal edilmiş genel
kurulu gösteren evrak kaydı ve denetim raporu yeni çağrıya bağlanabilir (iptal edilen kurulun bağı iz
olarak kalır).

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
`genel_kurul.olaganustu_basvuru_oran`), biri girilmemişse eksiktir. Başvuru yazısı gelen evrak olarak
kaydedilir, kişi listesi tutulmaz (U12): çağrı yazısı bağı (`call_document`) `DocumentRecord(GELEN)`'dir;
çağrıda ya da sonra (`cagri_yazisini_bagla`) girilir, girilmemişse akış eksiğidir (`BASVURU_YAZISI_AKISI`;
gerekçe istemez, bağ girilince kapanır, tutanak tamamlanırken hâlâ açıksa gerekçeyle sapmaya döner).

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

GÜNDEM VE KARAR (md. 9/2, 9/4, 9/6; 5. adım). Gündeme ekleme ve çıkarma toplantıda oylanır: oylama
satırı yoksa ya da kabul retten fazla değilse uyarı + gerekçe (`genel_kurul.gundem_degisikligi`;
kullanıcı kararı S2: md. 9/4'te kabul > ret); çıkarılan madde silinmez (`removed_by_vote`). Sıra
değişikliği uyarı üretmez (MA-16); SQLite tekil kısıtı ertelemediği için geçici sırayla iki adımda
yazılır. Olağanüstü genel kurulda toplantıda eklenen madde çağrı gündemi dışındadır: uyarı + gerekçe
(`genel_kurul.olaganustu_gundeme_baglilik`; B-13). Karar sonucu oylardan hesaplanır
(`genel_kurul.karar_cogunlugu`, sert — hesap bütünlüğü; S2 (a): kabul oyu paydanın yarısından fazla,
payda oylamada salonda bulunan sayı ya da toplantının katılımı); oylarla çelişen sonuç kaydedilmez
(kullanıcı kararı S6 (iii)).

DİVAN (md. 10/1-c; U25). Ayrı servistir (`divan_sec`); kayıt `OrganMembership(DIVAN)`, genel kurulun
kendi dönemine (yeni okulda hazırlık dönemine) seçilmiş açılır, aday kaydı aranmaz. Kişi türü
(`genel_kurul.divan_uye_turleri`: veli ya da 18 yaşını doldurmuş kursiyer; veli olan öğretmen veli
sayılır, MA-11) uyarı + gerekçedir.

KATILIM DÜZELTMESİ VE İŞARETİ. Toplantıda girilen sayılar yalnız gerekçeli düzeltme satırıyla değişir
(`AttendanceCorrection`, ekleme-yalnız); dondurulmuş yeter sayı düzeltilemez (sert). Düzeltme birinci
toplantıda yeter sayının sağlanıp sağlanmadığını değiştirirse uyarı + gerekçedir (akış satırı; durum
değişmez). Veli listesinin katılım işareti (`ParentRoster.attended_*`) yalnız sayım yardımıdır: işaret
sayısı öneridir, katılım sayısı işaretten hesaplanmaz; işaret tutanak tamamlanana dek yazılır, adlar
yalnız işaret penceresinin okumasında çözülür ve okuma erişim günlüğüne düşer (U33). Yeniden aktarımda
işaretler satırlarıyla düşer (S12 (a); `okul.services.imports`).

SEÇİM (md. 10/1-d, 11/1-a, b, 12/4, 13/8; U26, U27; 6. adım). Aday kaydı planlamadan toplantının sonuna
dek açılır (`aday_kaydet`; salondan adaylık); olağanda açılacak (hazırlık) döneme, olağanüstüde genel
kurulun kendi dönemine yazılır. Seçilen yalnız aynı genel kurulun aday kaydından olur (kullanıcı kararı
S6 (i), sert — hesap bütünlüğü). Koltuk uygunluğu, tek koltuk, aynı dönemde iki kurul ve okul müdürü
engeli F1c'nin sert kurallarıdır (`uyelikler`); seçimde denetlenen tek seçilme sınırı md. 12/4'tür,
md. 14/3 Denetleme Kurulunun görev bölümünde kalır. Seçimin biçimi `genel_kurul.secim_bicimi` (uyarı +
gerekçe). Olağanüstü genel kurulda yönetim kurulu seçilince görevdeki eski üyelikler düşer (U27);
olağanüstü genel kurul Denetleme Kuruluna seçim yapmaz (kullanıcı kararı S10 (a)).

İBRA VE TUTANAK (md. 11/1-c, ç; S4 (a); U32). İbra kurul başına ayrıdır; yönetim kurulunun hesapları
ibra edilmezse ibra edilmeyen muhasebe evrakı tutanağa yazılır, tutanak tamamlanınca il/ilçe MEM
bildirimi takvime girer. `TUTANAK_TAMAM` kapatıcı geçiştir: açık eksikler gerekçeyle sapmaya döner
(O3). Olağanda dönem bu geçişte değişmez; program yöneticisinin onayıyla hazırlık dönemi `ACIK`
(başlangıç genel kurulun yapıldığı gün, U6), kapanacak dönem `KAPANISTA` (bir önceki gün biter) olur,
aralık çakışması serttir (U4), okul idaresinin TEFBİS girişleri takvime girer (md. 23/5).

GÜN KAYNAĞI (U6). Genel kurulun yapıldığı gün `genel_kurul_gunu`'dür (`selectors.genel_kurul_gunu`:
birinci ya da ikinci toplantı); divanın ve seçilenlerin günü, yeni dönemin başlangıcı ve görev bölümü
süresi buradan okunur. Kuralların olay günü yine birinci toplantınındır (U7).

Her yazma denetim izine düşer (izli servis kalıbı: `denetim_izi.degisiklik`). Kayıt silinmez: genel
kurul `IPTAL` olur (altın kural 4).
"""

from __future__ import annotations

import calendar
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Final

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from apps.oab import selectors
from apps.oab.hatalar import (
    GerekceGerekli,
    KuralSert,
    KuralSurumuGuncellenmeli,
    YeterSayiDonduruldu,
)
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
    AgendaResult,
    Announcement,
    AnnouncementKind,
    AnnouncementStatus,
    AssemblyCaller,
    AssemblyKind,
    AssemblyMeeting,
    AssemblyMinutes,
    AssemblyStatus,
    AttendanceCorrection,
    AttendanceKind,
    AuditReport,
    ComplianceItem,
    ComplianceKind,
    ComplianceObligation,
    Discharge,
    DocumentDirection,
    DocumentRecord,
    DropKind,
    ElectedBy,
    GeneralAssembly,
    MembershipRole,
    MembershipStatus,
    OabPerson,
    OabTerm,
    OrganMembership,
    OrganType,
    SeatType,
    TermStatus,
)
from apps.oab.models.genel_kurul import (
    BASLIK_MAX,
    DK_RAPORU_BASKA_KURULDA,
    DK_RAPORU_ISARETSIZ,
    DONDURULAN_ALANLAR,
    DUZELTILEBILIR_ALANLAR,
    YER_MAX,
)
from apps.oab.services import (
    donem_kilidi,
    donemler,
    gecis,
    gelen_giden_evrak,
    iz,
    kural_bagi,
    uyelik_gecisleri,
    uyelikler,
    uyum,
)
from apps.okul import denetim_izi, erisim_gunlugu, excel_veli, normalize, rol_izinleri
from apps.okul.models import (
    AccessKind,
    AccountRole,
    Attachment,
    AttachmentSensitivity,
    AuditAction,
    ParentRoster,
    SchoolConfig,
)
from apps.okul.oturum import yazar
from apps.okul.services import app_password, dosya_deposu
from shared.crypto import is_corrupt
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
DK_RAPORU_GEREKLI = (
    "Denetleme Kurulunun olağanüstü genel kurul çağrısı, yönetim kurulunun md. 6'ya aykırı faaliyeti "
    "işaretlenmiş denetim raporuyla açılır (md. 14/5); rapor seçilmelidir."
)
DK_RAPORU_DONEMI = "Denetim raporu genel kurulun birlik dönemine ait olmalıdır."
DENETIM_RAPORU_YALNIZ_DK = "Denetim raporu yalnız Denetleme Kurulunun çağrısına bağlanır."
CAGRI_YAZISI_YALNIZ_BASVURUDA = (
    "Çağrı yazısı bağı yalnız üyelerin yazılı başvurusunda ve Denetleme Kurulunun çağrısında girilir; "
    "müdürün yazısını program işler."
)
CAGRI_YAZISI_GELEN_OLMALI = "Üyelerin yazılı başvurusu gelen evrak kaydıdır (md. 9/6)."
CAGRI_YAZISI_DONEMI = "Çağrı yazısının evrak kaydı genel kurulun birlik dönemine ait olmalıdır."
CAGRI_YAZISI_BASKA_KURULDA = "Bu evrak kaydı başka bir genel kurulun çağrı yazısı."
CAGRI_YAZISI_BAGLI = "Bu genel kurulun çağrı yazısı bağlı."
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
# Gündem ve karar (5. adım).
OYLAR_BIRLIKTE = "Kabul ve ret oyları birlikte girilir."
OYLAR_KATILANI_ASAR = (
    "Kabul ve ret oylarının toplamı oylamaya katılabilecek üye sayısını aşamaz (hesap bütünlüğü)."
)
EKLEME_SIRASI_GECERSIZ = (
    "Eklenecek maddenin sırası 1 ile gündemin son sırasının bir fazlası arasında olmalıdır."
)
MADDE_CIKARILMIS = "Bu gündem maddesi oylamayla çıkarıldı; görüşülmez."
EKLENEN_CIKARILMAZ = (
    "Oylamayla eklenen madde ayrıca çıkarılamaz; ekleme oylamasının sonucunu kayda geçirin."
)
SONUCLU_MADDE_CIKARILMAZ = "Sonucu girilmiş gündem maddesi çıkarılamaz."
SIRA_GECERSIZ = "Yeni sıra gündemin bütün maddelerini birer kez içermelidir."
SONUC_GECERSIZ = "Sonuç kabul, ret ya da görüşüldü olmalıdır."
SONUC_KENDI_YOLUNDA = "İbra ve seçim maddelerinin sonucu kendi adımında girilir."
GORUSULDU_OYSUZ = "Görüşüldü sonucunda oy girilmez."
OYLAR_GEREKLI = (
    "Oylanan maddede kabul ve ret oyları girilmelidir; oylanmayan madde görüşüldü diye kaydedilir."
)
SALONDAKI_KATILANDAN_COK = (
    "Oylamada salonda bulunan sayı toplantıya katılan üye sayısından büyük olamaz (hesap "
    "bütünlüğü)."
)
KARAR_OYLARLA_CELISIYOR = (
    "Genel kurul kararları katılanların çoğunluğuyla alınır ve sonuç oylardan hesaplanır; girilen "
    "sonuç oylarla çelişiyor"
)
# Divan (5. adım).
DIVAN_AYNI_KISI = "Divan başkanı ve kâtip ayrı kişilerdir (md. 10/1-c)."
DIVAN_SECILDI = "Bu genel kurulun divanı seçildi."
# Katılım düzeltmesi ve işareti (5. adım).
TOPLANTI_GECERSIZ = "Toplantı birinci ya da ikinci toplantı olmalıdır."
DUZELTME_GEREKCESI_GEREKLI = "Katılım düzeltmesinin gerekçesi yazılmalıdır."
DUZELTME_BOS = "Düzeltilecek en az bir sayı girilmelidir."
DUZELTME_ALANI_GECERSIZ = (
    "Düzeltilen sayı katılım sayısı, türe göre dağılım, velisi katılan öğrenci ya da gözlemci "
    "sayısı olmalıdır."
)
DUZELTME_TOPLANTISI = "Bu sayı seçilen toplantının sayısı değil."
DUZELTME_DEGISMIYOR = "Düzeltilen sayı önceki değerle aynı."
IKINCI_TOPLANTI_YAPILMADI = "İkinci toplantı yapılmadı; ikinci toplantının sayısı düzeltilemez."
DUZELTME_OYLARIN_ALTINDA = (
    "Katılım sayısı, gündem maddelerine ve ibraya girilmiş oyların, oylamada salonda bulunan sayının "
    "ya da gündem değişikliği oylarının toplamının altına düzeltilemez (hesap bütünlüğü)."
)
#: Katılım düzeltmesi yönetim kurulunun ibra sonucunu değiştirince bilgi satırı (md. 11/1-ç; S4 (a)).
IBRA_YAN_AKISI_GOZDEN_GECIR: Final = (
    'Yönetim kurulunun ibra sonucu değişti: "ibra edilmedi" yan akışı (ibra edilmeyen muhasebe '
    "evrakının listesi, il/ilçe millî eğitim müdürlüğüne bildirim; md. 11/1-ç) gözden geçirilmelidir."
)
ISARET_CAKISIYOR = "Aynı satır hem işaretlenip hem işareti kaldırılamaz."
ISARET_SATIRI_YOK = "Satır bu genel kurulun veli listesinde yok."
ISARET_BASKA_KURULDA = "Bu satır başka bir genel kurulun katılım işaretini taşıyor."
ISARET_YOK = "Bu satırda bu toplantının katılım işareti yok."

#: Katılım düzeltmesi birinci toplantıda yeter sayının sağlanıp sağlanmadığını değiştirince yazılan
#: akış satırı (tasarım §5.2.3 "uyarı + gerekçe"; kural paketinde değeri yoktur, atıf basılmaz).
DUZELTME_YETER_SAYI_AKISI: Final = "akis.genel_kurul_katilim_duzeltmesi"
DUZELTME_YETER_SAYI: Final = (
    "Düzeltme, birinci toplantıda yeter sayının sağlanıp sağlanmadığını değiştiriyor; genel "
    "kurulun durumu değişmez, düzeltme gerekçesiyle kayda geçer (program uyarısıdır)."
)
#: Katılım düzeltmesi, salondaki sayısı girilmemiş oylanmış maddenin oylardan hesaplanan sonucunu
#: değiştirince yazılan akış satırı (plan F2 §5.1 "sonucu değiştiren düzeltme uyarı + gerekçe");
#: sonuç kullanıcı kararı S6 (iii) gereği yeni paydayla yeniden hesaplanır. Atıf basılmaz.
DUZELTME_KARAR_AKISI: Final = "akis.genel_kurul_karar_duzeltmesi"
DUZELTME_KARAR: Final = (
    "Düzeltme, oylamaya katılabilecek üye sayısını değiştirdiği için oylardan hesaplanan karar "
    "sonucunu değiştiriyor; sonuç yeni sayıyla yeniden hesaplanır, düzeltme gerekçesiyle kayda geçer "
    "(program uyarısıdır)."
)
#: Sıra değişikliğinin bilgi satırı (md. 9/4 birinci cümle; MA-16: kural değildir).
SIRA_BILGISI: Final = "Genel kurul gündem maddelerini sırasıyla görüşür (md. 9/4)."

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
#: Müdür yazısının evrak defterine işlenmesinin bilgi satırları (⁷).
MUDUR_YAZISI_ISLENDI: Final = (
    "Müdürün yazısı gelen-giden evrak defterine giden evrak olarak işlendi ({yil}/{no})."
)
MUDUR_YAZISI_DEFTERSIZ: Final = (
    "Gelen-giden evrak defteri kaydedilmediği için müdürün yazısı evrak defterine işlenmedi."
)
#: Denetleme Kurulunun yazısının evrak bağı girilmediğinde (modül başlığı "Evrak defteri").
DK_YAZISI_BAGSIZ: Final = (
    "Denetleme Kurulunun çağrı yazısı gelen-giden evrak defterine kaydedilince çağrıya bağlanır."
)
#: Üyelerin yazılı başvurusunun gelen evrak bağının akış eksiği (U12; atıf basılmaz, gerekçe istemez).
BASVURU_YAZISI_AKISI: Final = "akis.genel_kurul_basvuru_yazisi"
BASVURU_YAZISI_EKSIK: Final = (
    "Üyelerin yazılı başvurusu gelen evrak kaydına bağlanmadı; başvuru yazısı gelen evrak olarak "
    "kaydedilip bağlanınca eksik kapanır (program hatırlatmasıdır)."
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
#: §7.1 `YAPILDI → TUTANAK_TAMAM` "Kim" (gündem değişikliği, karar, divan, katılım düzeltmesi) ve
#: ilandan önceki gündem düzeni (planlama "Kim"i): program yöneticisi, sekreter.
TUTANAK_ROLLERI: Final = frozenset({_YONETICI, _SEKRETER})
#: Katılım işareti (U33; R9, dipnot ¹⁰): yalnız program yöneticisi.
ISARET_ROLLERI: Final = frozenset({_YONETICI})
_MUDUR: Final = AccountRole.MUDUR.value
_DENETLEME_KURULU: Final = AccountRole.DENETLEME_KURULU.value
#: §7.1 çağrı "Kim"i, genel kurul yazma kapısından geçen çağıranlar. Müdürün ve Denetleme Kurulunun
#: çağrısı kendi eylemleriyle yazılır (`_cagri_kapisi`); md. 13/8'in müdür kolu da.
CAGIRAN_ROLLERI: Final[Mapping[str, frozenset[str]]] = {
    AssemblyCaller.YONETIM_KURULU: frozenset({_SEKRETER}),
    AssemblyCaller.BASKAN_VEYA_MUDUR_13_8: frozenset({_BASKAN}),
    AssemblyCaller.UYE_BASVURUSU: frozenset({_YONETICI}),
}
#: Yalnız müdürün yazabildiği çağıranlar (md. 9/1 yeni okul, 9/6, 25/2; ¹, M-5).
MUDUR_CAGIRANLARI: Final = frozenset(
    {AssemblyCaller.OKUL_MUDURU, AssemblyCaller.MUDUR_25_2, AssemblyCaller.MUDUR_YENI_OKUL}
)
#: Müdürün yazısının eylemleri (¹; sahiplikli): yazısı evrak defterine programca işlenir (⁷).
_MUDUR_EYLEMLERI: Final = frozenset(
    {
        rol_izinleri.Eylem.GENEL_KURUL_YENI_OKUL_DAVETI,
        rol_izinleri.Eylem.OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR,
    }
)
#: Müdürün yazısının programca evrak kaydında konu (kişisiz; ⁷). md. 25/2 çağrıyı kendi metninde
#: saymaz, yetki md. 9/6'daki 2023 ek ibaresindendir (plan F2 §3.2).
MUDUR_YAZISI_KONUSU: Final[Mapping[str, str]] = {
    AssemblyCaller.MUDUR_YENI_OKUL: "Genel kurul toplantı çağrısı (yeni açılan okul; md. 9/1)",
    AssemblyCaller.OKUL_MUDURU: "Olağanüstü genel kurul toplantı çağrısı (md. 9/6)",
    AssemblyCaller.BASKAN_VEYA_MUDUR_13_8: "Olağanüstü genel kurul toplantı çağrısı (md. 13/8)",
    AssemblyCaller.MUDUR_25_2: "Olağanüstü genel kurul toplantı çağrısı (md. 9/6, 25/2)",
}


def mudur_yazisi_konusu(kind: str, cagiran: str) -> str:
    """Müdürün yazısının evrak kaydındaki konusu: çağırana ve genel kurulun türüne göre. Yeni açılan
    okulun daveti (md. 9/1) olağan genel kuruldur; olağanüstü genel kurulda `MUDUR_YENI_OKUL` listede
    olmayan çağırandır (uyarı + gerekçe, plan F2 §3.2), yazı müdürün olağanüstü çağrısıdır (md. 9/6)."""
    if cagiran == AssemblyCaller.MUDUR_YENI_OKUL and kind == AssemblyKind.OLAGANUSTU:
        return MUDUR_YAZISI_KONUSU[AssemblyCaller.OKUL_MUDURU]
    return MUDUR_YAZISI_KONUSU[cagiran]


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
#: Gündem sırasının değiştiği durumlar: ilandan önce (planlama, çağrı) ve toplantıda (md. 9/4).
_SIRA_DEGISEBILIR: Final = (
    AssemblyStatus.PLANLANDI,
    AssemblyStatus.CAGRILDI,
    AssemblyStatus.YAPILDI,
)
#: Sonucu bu yoldan girilmeyen gündem maddeleri: ibra ve seçim (6. adım).
_KENDI_YOLUNDA: Final = frozenset(
    {AgendaItemKind.IBRA, AgendaItemKind.SECIM_YK, AgendaItemKind.SECIM_DK}
)
#: Katılım sayılarının düzeltildiği durumlar: toplantıda sayılar girildikten sonra.
_DUZELTILEBILIR_DURUMLAR: Final = (
    AssemblyStatus.YETER_SAYI_YOK,
    AssemblyStatus.YAPILDI,
    AssemblyStatus.TUTANAK_TAMAM,
)
#: Türe göre dağılımın düzeltme alanı öneki (`DUZELTILEBILIR_ALANLAR`).
_DAGILIM_ONEKI: Final = "attendance_by_kind."
#: İlan kanıtı yazılabilen durumlar (tutanak tamamlanana dek; tamamlanınca eksik sapmaya döner:
#: `tutanagi_tamamla`).
_KANIT_YAZILABILIR: Final = frozenset(
    {AssemblyStatus.ILAN_EDILDI, AssemblyStatus.YETER_SAYI_YOK, AssemblyStatus.YAPILDI}
)

#: Katılım işaretinin yazılabildiği durumlar (U33: tutanak tamamlanana dek; `_isaret_toplantisi`).
_ISARET_YAZILABILIR: Final = frozenset(
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

    def akis(self, akis_id: str, mesaj: str, *, kurulun: bool = True) -> None:
        """Atıfsız akış satırı (gerekçesi alınmış uyarı) dönen uyarılara, konusu kurulsa kurulun
        özetine girer."""
        satir: dict[str, Any] = {
            "kural": akis_id,
            "atif": "",
            "mesaj": mesaj,
            "durum": "uyari",
            "paket": "",
            "rev": None,
        }
        if kurulun:
            self.ozet_satirlari[akis_id] = satir
        self.uyarilar.append(satir)

    def akis_eksik(self, akis_id: str, mesaj: str) -> None:
        """Atıfsız akış eksiği (gerekçe istemez) dönen uyarılara ve kurulun özetine girer."""
        satir: dict[str, Any] = {
            "kural": akis_id,
            "atif": "",
            "mesaj": mesaj,
            "durum": "eksik",
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


def _gundem_maddesi(madde: GundemMaddesi) -> tuple[str, str]:
    """Gündem maddesinin türü ve boşlukları sadeleşmiş başlığı (türü tanımlı, başlığı dolu ve sınırda)."""
    if madde.kind not in AgendaItemKind.values:
        raise ValueError(GUNDEM_TURU_GECERSIZ)
    baslik = " ".join(madde.title.split())
    if not baslik:
        raise ValueError(GUNDEM_BASLIGI_GEREKLI)
    if len(baslik) > BASLIK_MAX:
        raise ValueError(GUNDEM_BASLIGI_UZUN)
    return madde.kind, baslik


def _cagri_gundemi(gundem: Sequence[GundemMaddesi]) -> list[tuple[str, str]]:
    if not gundem:
        raise ValueError(GUNDEM_GEREKLI)
    return [_gundem_maddesi(madde) for madde in gundem]


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
    _duzenleme_kapisi(kurul, PLANLAYAN_ROLLER)
    guncel = _guncel(kurul)
    if guncel.status not in (AssemblyStatus.PLANLANDI, AssemblyStatus.CAGRILDI):
        raise ValueError(TARIH_DEGISMEZ)
    _cagri_sahipligi(guncel)
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
@dataclass(frozen=True)
class CagriKaydi:
    """Yetki kapısının sorduğu kayıt (`rol_izinleri.YetkiKaydi`): genel kurulun çağrısı."""

    donem_kapali: bool
    sahip_rol: str | None


def cagri_sahibi(kurul: GeneralAssembly) -> str | None:
    """Çağrı yazısının sahibi olan rol (modül başlığı "Sahiplik"): müdürün çağıranlarında ve müdürün
    yazdığı md. 13/8 çağrısında (`called_by_role`) müdür, Denetleme Kurulunun çağrısında Denetleme Kurulu.
    Öteki çağıranlarda (yönetim kurulu, üye başvurusu, başkanın md. 13/8 çağrısı) sahip rol yoktur:
    `None`."""
    if kurul.called_by in MUDUR_CAGIRANLARI or (
        kurul.called_by == AssemblyCaller.BASKAN_VEYA_MUDUR_13_8 and kurul.called_by_role == _MUDUR
    ):
        return _MUDUR
    if kurul.called_by == AssemblyCaller.DENETLEME_KURULU:
        return _DENETLEME_KURULU
    return None


def _cagri_kaydi(kurul: GeneralAssembly) -> CagriKaydi:
    donem = kural_donemi(kurul)
    return CagriKaydi(donem_kapali=donem.donem_kapali, sahip_rol=cagri_sahibi(kurul))


def _cagri_eylemi(kurul: GeneralAssembly, cagiran: str, rol: str | None) -> rol_izinleri.Eylem:
    """Çağrının eylemi (modül başlığı "Müdür ve Denetleme Kurulu"): müdürün yazısı müdürün eylemiyle,
    Denetleme Kurulunun çağrısı denetim modülünün eylemiyle, ötekiler genel kurul yazma kapısıyla."""
    if cagiran == AssemblyCaller.DENETLEME_KURULU:
        return rol_izinleri.Eylem.DK_GENEL_KURUL_YAZMA
    if cagiran == AssemblyCaller.MUDUR_YENI_OKUL and kurul.kind == AssemblyKind.OLAGAN:
        return rol_izinleri.Eylem.GENEL_KURUL_YENI_OKUL_DAVETI
    if cagiran in MUDUR_CAGIRANLARI or (
        cagiran == AssemblyCaller.BASKAN_VEYA_MUDUR_13_8 and rol == _MUDUR
    ):
        return rol_izinleri.Eylem.OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR
    return rol_izinleri.Eylem.GENEL_KURUL_YAZMA


def cagri_yetki_kaydi(kurul: GeneralAssembly) -> CagriKaydi:
    """Çağrı yazısının yetki kaydı (dönem kilidi ve sahip rol): çağrı yazısını, yani E05'i çağıranın
    eylemiyle üreten evrak servisi okur (`genel_kurul_evraki`; plan F2 9. adım)."""
    return _cagri_kaydi(kurul)


def cagri_yazisi_eylemi(kurul: GeneralAssembly) -> rol_izinleri.Eylem:
    """Kaydedilmiş çağrının eylemi (`called_by`, `called_by_role`; modül başlığı "Müdür ve
    Denetleme Kurulu"): müdürün yazısı müdürün eylemi, Denetleme Kurulunun çağrısı denetim modülünün
    eylemi, ötekiler genel kurul yazma kapısı. Evrak servisi E05'in üretim kapısında okur."""
    return _cagri_eylemi(kurul, str(kurul.called_by), str(kurul.called_by_role) or None)


def _cagri_kapisi(kurul: GeneralAssembly, cagiran: str) -> rol_izinleri.Eylem:
    """Çağrının rol kapısı: eylem ve (genel kurul yazma kapısında) çağrının "Kim"i; sahiplikli eylemde
    kayıt da sorulur. Geçen eylem döner."""
    kim = yazar()
    eylem = _cagri_eylemi(kurul, cagiran, None if kim is None else kim.rol)
    if eylem is rol_izinleri.Eylem.GENEL_KURUL_YENI_OKUL_DAVETI:
        rol_izinleri.yetki_oturum(
            rol_izinleri.Eylem.GENEL_KURUL_YENI_OKUL_DAVETI, _cagri_kaydi(kurul)
        )
    elif eylem is rol_izinleri.Eylem.OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR:
        rol_izinleri.yetki_oturum(
            rol_izinleri.Eylem.OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR, _cagri_kaydi(kurul)
        )
    elif eylem is rol_izinleri.Eylem.DK_GENEL_KURUL_YAZMA:
        rol_izinleri.yetki_oturum(rol_izinleri.Eylem.DK_GENEL_KURUL_YAZMA, _cagri_kaydi(kurul))
    else:
        _kapi()
        _daralt(CAGIRAN_ROLLERI.get(cagiran, frozenset()))
    return eylem


def _cagri_sahipligi(kurul: GeneralAssembly) -> None:
    """Çağrılmış genel kurulda çağrı yazısının (toplantı zamanı, gündem) sahibi müdür ya da Denetleme
    Kuruluysa ilandan önce başka rolce değiştirilmez (modül başlığı "Sahiplik")."""
    if kurul.status != AssemblyStatus.CAGRILDI:
        return
    sahip = cagri_sahibi(kurul)
    kim = yazar()
    if sahip is not None and (kim is None or kim.rol != sahip):
        raise RolYetkisiz


def _duzenleme_kapisi(kurul: GeneralAssembly, roller: frozenset[str]) -> None:
    """Çağrı yazısının alanlarını (toplantı zamanı ve yeri, gündem sırası) düzenleyen yazmanın başı
    (modül başlığı "Sahiplik"; tasarım §4.4.2 "müdür yalnız kendi yazısını düzenler"). Çağrılmış genel
    kurulda yazının sahibi müdür ya da Denetleme Kuruluysa kapı çağrının eylemidir (sahiplikli: yalnız
    sahip rol geçer); öteki hâllerde genel kurul yazma kapısı ve geçişin "Kim"i (`roller`)."""
    kayit = GeneralAssembly.objects.get(pk=kurul.pk)
    sahip = cagri_sahibi(kayit) if kayit.status == AssemblyStatus.CAGRILDI else None
    if sahip is None:
        _baslangic(roller)
        return
    app_password.require_password_set()
    rol_izinleri.yetki_oturum(
        _cagri_eylemi(kayit, kayit.called_by, kayit.called_by_role), _cagri_kaydi(kayit)
    )


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


#: Çağrı yazısının evrak bağı girilen çağıranlar (modül başlığı "Çağrı", "Evrak defteri"): üyelerin
#: başvurusu (U12) ve Denetleme Kurulunun yazısı (tasarım §5.2.3, plan F2 §1.1-11). Müdürün yazısını
#: program işler (⁷).
YAZI_BAGLANAN_CAGIRANLAR: Final = frozenset(
    {AssemblyCaller.UYE_BASVURUSU, AssemblyCaller.DENETLEME_KURULU}
)


def _cagri_yazisi_denetimi(
    kurul: GeneralAssembly, cagiran: str, kayit: DocumentRecord
) -> DocumentRecord:
    """Çağrı yazısının evrak kaydı: genel kurulun döneminde, iptal edilmemiş başka genel kurulun çağrı
    yazısı değil (tek kaynak); üyelerin başvurusunda gelen evrak (U12). Denetleme Kurulunun yazısında
    yön denetlenmez: kaynaklar yazının gelen mi giden mi kaydedileceğini söylemez (altın kural 1)."""
    guncel = DocumentRecord.objects.get(pk=kayit.pk)
    if cagiran == AssemblyCaller.UYE_BASVURUSU and guncel.direction != DocumentDirection.GELEN:
        raise ValueError(CAGRI_YAZISI_GELEN_OLMALI)
    if guncel.term_id != kurul.term_id:
        raise ValueError(CAGRI_YAZISI_DONEMI)
    if (
        GeneralAssembly.objects.filter(call_document=guncel)
        .exclude(pk=kurul.pk)
        .exclude(status=AssemblyStatus.IPTAL)
        .exists()
    ):
        raise ValueError(CAGRI_YAZISI_BASKA_KURULDA)
    return guncel


def _dk_raporu_denetimi(kurul: GeneralAssembly, rapor: AuditReport | None) -> AuditReport:
    """md. 14/5 çağrısının raporu: md. 6 aykırılık işaretli, genel kurulun döneminde, iptal edilmemiş
    başka genel kurulu çağırmamış (kullanıcı kararı S6 (ii), sert; `models.genel_kurul` "md. 14/5
    çağrısının iki bağı"). İptal edilen genel kurulun raporu yeni çağrıya bağlanır."""
    if rapor is None:
        raise ValueError(DK_RAPORU_GEREKLI)
    guncel = AuditReport.objects.get(pk=rapor.pk)
    if not guncel.md6_violation_found:
        raise ValueError(DK_RAPORU_ISARETSIZ)
    if guncel.term_id != kurul.term_id:
        raise ValueError(DK_RAPORU_DONEMI)
    if (
        guncel.escalated_assembly_id is not None
        and guncel.escalated_assembly_id != kurul.pk
        and not GeneralAssembly.objects.filter(
            pk=guncel.escalated_assembly_id, status=AssemblyStatus.IPTAL
        ).exists()
    ):
        raise ValueError(DK_RAPORU_BASKA_KURULDA)
    return guncel


@transaction.atomic
def cagir(
    kurul: GeneralAssembly,
    *,
    called_by: str = "",
    call_reason: str = "",
    gundem: Sequence[GundemMaddesi] = (),
    member_application_count: int | None = None,
    member_count_declared: int | None = None,
    call_document: DocumentRecord | None = None,
    call_audit_report: AuditReport | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> GenelKurulSonucu:
    """Genel kurulu çağırır (`PLANLANDI → CAGRILDI`; modül başlığı "Çağrı", "Müdür ve Denetleme
    Kurulu"). Rol kapısı çağırana göredir; müdürün yazısı evrak defterine işlenir (⁷), Denetleme
    Kurulunun çağrısı işaretli raporla iki bağı yazar, üyelerin başvurusunun gelen evrak bağı burada ya
    da sonra girilir."""
    yazma_kapisi()
    app_password.require_password_set()
    cagiran = _cagiran(GeneralAssembly.objects.get(pk=kurul.pk), called_by)
    eylem = _cagri_kapisi(GeneralAssembly.objects.get(pk=kurul.pk), cagiran)
    guncel = _guncel(kurul)
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
    if call_document is not None and cagiran not in YAZI_BAGLANAN_CAGIRANLAR:
        raise ValueError(CAGRI_YAZISI_YALNIZ_BASVURUDA)
    if call_audit_report is not None and cagiran != AssemblyCaller.DENETLEME_KURULU:
        raise ValueError(DENETIM_RAPORU_YALNIZ_DK)
    rapor = (
        _dk_raporu_denetimi(guncel, call_audit_report)
        if cagiran == AssemblyCaller.DENETLEME_KURULU
        else None
    )
    bagli_yazi = (
        None if call_document is None else _cagri_yazisi_denetimi(guncel, cagiran, call_document)
    )
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
            if bagli_yazi is None:
                uyum.akis_eksigi(
                    BASVURU_YAZISI_AKISI, BASVURU_YAZISI_EKSIK, donem=tur.donem, konu=guncel
                )
                tur.akis_eksik(BASVURU_YAZISI_AKISI, BASVURU_YAZISI_EKSIK)
        bilgiler.append(OLAGANUSTU_DONEM_ACMAZ_BILGISI)
    elif cagiran == AssemblyCaller.YONETIM_KURULU and guncel.call_decision_id is None:
        if guncel.term is None:  # tür daraltması: yönetim kurulunun çağrısı kapanacak dönemdedir
            raise ValueError(DONEMSIZ_GENEL_KURUL)
        uyum.akis_sapmasi(
            KARARSIZ_CAGRI_AKISI, KARARSIZ_CAGRI, donem=guncel.term, konu=guncel, gerekce=gerekce
        )
        tur.akis(KARARSIZ_CAGRI_AKISI, KARARSIZ_CAGRI)
    if maddeler:
        _gundem_yaz(guncel, maddeler)
    yazi = bagli_yazi
    if cagiran == AssemblyCaller.DENETLEME_KURULU and yazi is None:
        bilgiler.append(DK_YAZISI_BAGSIZ)
    if eylem in _MUDUR_EYLEMLERI:
        yazi = gelen_giden_evrak.mudur_yazisini_isle(
            donem=tur.donem, subject=mudur_yazisi_konusu(guncel.kind, cagiran)
        )
        bilgiler.append(
            MUDUR_YAZISI_DEFTERSIZ
            if yazi is None
            else MUDUR_YAZISI_ISLENDI.format(yil=yazi.year, no=yazi.record_no)
        )
    kim = yazar()
    guncel.called_by = cagiran
    guncel.called_by_role = (None if kim is None else kim.rol) or ""
    guncel.call_reason = neden
    guncel.member_application_count = basvuran
    guncel.member_count_declared = uye_sayisi
    guncel.call_document = yazi
    guncel.call_audit_report = rapor
    guncel.status = AssemblyStatus.CAGRILDI
    _ozeti_yaz(
        guncel,
        tur,
        (
            "called_by",
            "called_by_role",
            "call_reason",
            "member_application_count",
            "member_count_declared",
            "call_document",
            "call_audit_report",
            "status",
        ),
    )
    if rapor is not None:
        onceki = denetim_izi.anlik(rapor)
        rapor.escalated_assembly = guncel
        rapor.updated_by_id = iz.yazar_hesabi()
        rapor.save(update_fields=["escalated_assembly", "updated_at", "updated_by"])
        denetim_izi.degisiklik(rapor, onceki=onceki)
    return _sonuc(tur, bilgiler)


@transaction.atomic
def cagri_yazisini_bagla(kurul: GeneralAssembly, *, kayit: DocumentRecord) -> GenelKurulSonucu:
    """Çağrı yazısının evrak kaydını bağlar (modül başlığı "Çağrı", "Evrak defteri"): üyelerin yazılı
    başvurusunun gelen evrak kaydı (U12; akış eksiği kapanır) ya da Denetleme Kurulunun yazısının kaydı
    (tasarım §5.2.3). Bağı program yöneticisi girer (başvuruyu kaydeden, §7.1 "Kim"; DK evrak kaydı
    yazmaz, M10); bağ tutanak tamamlanana dek girilir, bir kez girilir."""
    _baslangic(CAGIRAN_ROLLERI[AssemblyCaller.UYE_BASVURUSU])
    guncel = _guncel(kurul)
    if guncel.called_by not in YAZI_BAGLANAN_CAGIRANLAR:
        raise ValueError(CAGRI_YAZISI_YALNIZ_BASVURUDA)
    _durum(guncel, AssemblyStatus.CAGRILDI, *_KANIT_YAZILABILIR)
    if guncel.call_document_id is not None:
        raise ValueError(CAGRI_YAZISI_BAGLI)
    yazi = _cagri_yazisi_denetimi(guncel, guncel.called_by, kayit)
    tur = _Tur(guncel, None)
    if guncel.called_by == AssemblyCaller.UYE_BASVURUSU:
        uyum.acik_satiri_kapat(BASVURU_YAZISI_AKISI, donem=tur.donem, konu=guncel)
        tur.ozet_satirlari[BASVURU_YAZISI_AKISI] = None
    guncel.call_document = yazi
    _ozeti_yaz(guncel, tur, ("call_document",))
    return _sonuc(tur)


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


def ilan_kanitina_ek_ekle(duyuru: Announcement, icerik: bytes, *, dosya_adi: str) -> Attachment:
    """İlanın kanıt dosyasını (ilan panosunun fotoğrafı, internet sayfasının görüntüsü, elden yazılı
    davetin teslim kaydı) dosya deposuna yazar; sahip ilan kaydıdır (`Announcement.ekler()`; kullanıcı
    eki kümesi PDF, JPEG, PNG). İlan ve toplantının "Kim"i; kanıt yazılabilen durumlarda (tutanak
    tamamlanana dek). Veli adı taşıyan çizelge buraya eklenmez: adlı çıktı saklanmaz (R9)."""
    _baslangic(ILAN_VE_TOPLANTI_ROLLERI)
    guncel_duyuru = Announcement.objects.get(pk=duyuru.pk)
    if guncel_duyuru.subject_type != denetim_izi.model_etiketi(GeneralAssembly):
        raise ValueError(DUYURU_GENEL_KURULUN_DEGIL)
    guncel = _guncel(GeneralAssembly.objects.get(pk=int(guncel_duyuru.subject_id)))
    if guncel.status not in _KANIT_YAZILABILIR:
        raise ValueError(DURUM_GECERSIZ)
    return dosya_deposu.yaz(
        icerik,
        original_name=dosya_adi,
        sensitivity=AttachmentSensitivity.NORMAL,
        owner=guncel_duyuru,
        yazar=yazar(),
        kisi_listesi=False,
    )


# ---------------------------------------------------------------------------
# Genel kurulun dosya ekleri (plan F2 §1.2, §7 U22, U23; kullanıcı kararı S13 (a); 11. adım)
# ---------------------------------------------------------------------------
#: Dosya eki alan gündem maddeleri ve ekin belgesi: yönetim kurulu faaliyet raporu ve kesin hesap (E34)
#: ve tahmini bütçe (E28) yönetim kurulu rollerinin ve program yöneticisinin, Denetleme Kurulunun nihai
#: raporu (E33; md. 14/4) Denetleme Kurulunun ekidir. Üretimleri F4'tedir; F2'de genel kurula sunulan
#: belge dosya olarak eklenir. Ekin sahibi gündem maddesidir (kayıt türü başına ayrı bağ; şema
#: değişmez).
DOSYA_EKI_BELGELERI: Final[Mapping[str, str]] = {
    AgendaItemKind.YK_FAALIYET_RAPORU: "E34",
    AgendaItemKind.TAHMINI_BUTCE: "E28",
    AgendaItemKind.DK_RAPORU: "E33",
}
#: Denetleme Kurulunun eki (M8 ⁵, `Eylem.DK_GENEL_KURUL_YAZMA`).
DK_DOSYA_EKI_MADDESI: Final = AgendaItemKind.DK_RAPORU
#: Dosya ekinin yazıldığı durumlar: planlamadan toplantının sonuna dek (tutanak tamamlanınca kapanır).
_EK_YAZILABILIR: Final = frozenset(
    {
        AssemblyStatus.PLANLANDI,
        AssemblyStatus.CAGRILDI,
        AssemblyStatus.ILAN_EDILDI,
        AssemblyStatus.YETER_SAYI_YOK,
        AssemblyStatus.YAPILDI,
    }
)
DOSYA_EKI_MADDESI_DEGIL = (
    "Dosya eki yalnız yönetim kurulu faaliyet raporu, Denetleme Kurulu raporu ve tahmini bütçe "
    "maddelerine eklenir."
)


def dosya_eki_ekle(madde: AgendaItem, icerik: bytes, *, dosya_adi: str) -> Attachment:
    """Genel kurula sunulan belgeyi gündem maddesinin dosya eki olarak yazar (U23; kullanıcı eki kümesi
    PDF, JPEG, PNG). Faaliyet raporu ve tahmini bütçe: genel kurul yazma kapısı (program yöneticisi ve
    yönetim kurulu rolleri; md. 13/4 gelir-gider işlemlerini muhasibe verir); Denetleme Kurulunun
    raporu: yalnız Denetleme Kurulu (⁵). Planlamadan toplantının sonuna dek; çıkarılan maddeye eklenmez.
    Ek silinmez (altın kural 4)."""
    app_password.require_password_set()
    guncel_madde = AgendaItem.objects.get(pk=madde.pk)
    if guncel_madde.kind not in DOSYA_EKI_BELGELERI:
        raise ValueError(DOSYA_EKI_MADDESI_DEGIL)
    kurul = GeneralAssembly.objects.select_related(
        "term__rule_package", "opens_term__rule_package"
    ).get(pk=guncel_madde.assembly_id)
    if guncel_madde.kind == DK_DOSYA_EKI_MADDESI:
        rol_izinleri.yetki_oturum(rol_izinleri.Eylem.DK_GENEL_KURUL_YAZMA, kural_donemi(kurul))
    else:
        _kapi()
    guncel = _guncel(kurul)
    if guncel.status not in _EK_YAZILABILIR:
        raise ValueError(DURUM_GECERSIZ)
    if guncel_madde.removed_by_vote:
        raise ValueError(MADDE_CIKARILMIS)
    return dosya_deposu.yaz(
        icerik,
        original_name=dosya_adi,
        sensitivity=AttachmentSensitivity.NORMAL,
        owner=guncel_madde,
        yazar=yazar(),
        kisi_listesi=False,
    )


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


# ---------------------------------------------------------------------------
# Gündem değişikliği (md. 9/4), gündeme bağlılık (md. 9/6), karar (md. 9/2, 9/6)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GundemSonucu:
    """Gündem yazımının sonucu: güncel madde, bu yazımda çıkan uyarılar (atıflı) ve bilgi satırları."""

    madde: AgendaItem
    uyarilar: tuple[dict[str, Any], ...] = ()
    bilgiler: tuple[str, ...] = ()


def _toplanti_katilani(kurul: GeneralAssembly) -> int:
    """Genel kurulun yapıldığı toplantının katılım sayısı (son düzeltme satırının değeri)."""
    sayi = (
        kurul.second_attendee_count
        if kurul.held_at_meeting == AssemblyMeeting.IKINCI
        else kurul.first_attendee_count
    )
    if sayi is None:  # tür daraltması: yapılmış genel kurulun toplantısının katılımı doludur
        raise ValueError(DURUM_GECERSIZ)
    return sayi


def genel_kurul_gunu(kurul: GeneralAssembly) -> date:
    """Genel kurulun yapıldığı toplantının yerel günü (`selectors.genel_kurul_gunu`, plan F2 §7 U6):
    divanın ve seçilenlerin günü, yeni dönemin başlangıcı. Gün yoksa `DURUM_GECERSIZ`."""
    gun = selectors.genel_kurul_gunu(kurul)
    if gun is None:  # tür daraltması: yapılmış genel kurulun toplantı anı doludur
        raise ValueError(DURUM_GECERSIZ)
    return gun


def _madde_ve_kurul(madde: AgendaItem) -> tuple[AgendaItem, GeneralAssembly]:
    """Maddenin ve genel kurulunun güncel hâli; dönem yazılabilir olmalı."""
    guncel: AgendaItem = AgendaItem.objects.get(pk=madde.pk)
    return guncel, _guncel(guncel.assembly)


def _degisiklik_oylari(
    kurul: GeneralAssembly, kabul: object, ret: object
) -> tuple[int | None, int | None]:
    """Gündem değişikliğinin oyları: ikisi birlikte girilir; toplamı katılımı aşamaz (hesap
    bütünlüğü). Girilmemişse oylama satırı yoktur (kural uyarısı; tutanak olduğu gibi girilir)."""
    if (kabul is None) != (ret is None):
        raise ValueError(OYLAR_BIRLIKTE)
    if kabul is None or ret is None:
        return None, None
    kabul_sayisi, ret_sayisi = _sayi(kabul), _sayi(ret)
    if kabul_sayisi + ret_sayisi > _toplanti_katilani(kurul):
        raise ValueError(OYLAR_KATILANI_ASAR)
    return kabul_sayisi, ret_sayisi


def _gundem_degisikligi_denetimi(tur: _Tur, madde: AgendaItem) -> None:
    """md. 9/4: ekleme ve çıkarma oylanır, oy çokluğu aranır (kullanıcı kararı S2: kabul > ret).
    Oylama satırı yoksa ya da kabul retten fazla değilse uyarı + gerekçe; konu maddedir."""
    kabul, ret = madde.change_votes_for, madde.change_votes_against
    oy_coklugu = kabul is not None and ret is not None and kabul > ret
    sonuc = uyum.denetle("genel_kurul.gundem_degisikligi", oy_coklugu, konu=madde, **tur.ortak())
    tur.kaydet("genel_kurul.gundem_degisikligi", sonuc, kurulun=False)


def _gundeme_baglilik_denetimi(tur: _Tur, madde: AgendaItem) -> None:
    """md. 9/6 "gündeme bağlılık ilkesi geçerlidir" (kullanıcı kararı B-13: sert değil): olağanüstü
    genel kurulda toplantıda eklenen madde çağrı gündeminde değildir; uyarı + gerekçe."""
    if tur.kurul.kind != AssemblyKind.OLAGANUSTU:
        return
    # Gözlenen: madde çağrının gündemine bağlı mı? Toplantıda eklenen madde çağrıda yoktu.
    sonuc = uyum.denetle(
        "genel_kurul.olaganustu_gundeme_baglilik", False, konu=madde, **tur.ortak()
    )
    tur.kaydet("genel_kurul.olaganustu_gundeme_baglilik", sonuc, kurulun=False)


def _yer_ac(maddeler: Sequence[AgendaItem], sira: int) -> None:
    """`sira` ve sonrasındaki maddeleri birer kaydırır (büyükten küçüğe: tekil kısıt çakışmaz)."""
    hesap = iz.yazar_hesabi()
    for madde in sorted(maddeler, key=lambda m: m.order, reverse=True):
        if madde.order < sira:
            continue
        onceki = denetim_izi.anlik(madde)
        madde.order += 1
        madde.updated_by_id = hesap
        madde.save(update_fields=["order", "updated_at", "updated_by"])
        denetim_izi.degisiklik(madde, onceki=onceki)


def _sirala(sirali: Sequence[AgendaItem]) -> None:
    """Maddeleri verilen sırayla 1'den numaralar. SQLite tekil kısıtı (genel kurul, sıra) ertelemediği
    için yeri değişen maddeler önce kullanılmayan geçici sıralara, sonra yerlerine yazılır (tasarım
    §5.2.3). Her madde tek iz satırıyla izlenir: önceki hâl → son hâl."""
    degisen = [m for yeni, m in enumerate(sirali, start=1) if m.order != yeni]
    if not degisen:
        return
    oncekiler = {m.pk: denetim_izi.anlik(m) for m in degisen}
    gecici = max(m.order for m in sirali) + 1
    for adim, madde in enumerate(degisen):
        madde.order = gecici + adim
        madde.save(update_fields=["order"])
    hesap = iz.yazar_hesabi()
    for yeni, madde in enumerate(sirali, start=1):
        if madde.pk not in oncekiler:
            continue
        madde.order = yeni
        madde.updated_by_id = hesap
        madde.save(update_fields=["order", "updated_at", "updated_by"])
        denetim_izi.degisiklik(madde, onceki=oncekiler[madde.pk])


@transaction.atomic
def gundeme_madde_ekle(
    kurul: GeneralAssembly,
    *,
    title: str,
    kind: str = AgendaItemKind.DIGER,
    sira: int | None = None,
    change_votes_for: int | None = None,
    change_votes_against: int | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> GundemSonucu:
    """Toplantıda gündeme oylamayla madde ekler (md. 9/4; `added_by_vote`). Oylama satırı yoksa ya da
    oy çokluğu yoksa uyarı + gerekçe (`genel_kurul.gundem_degisikligi`); olağanüstü genel kurulda
    eklenen madde çağrı gündemi dışındadır, uyarı + gerekçe (`genel_kurul.olaganustu_gundeme_baglilik`,
    B-13). `sira` verilmezse madde sona eklenir; verilirse o sıradaki ve sonraki maddeler kayar."""
    yazma_kapisi()
    _baslangic(TUTANAK_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, AssemblyStatus.YAPILDI)
    tur_adi, baslik = _gundem_maddesi(GundemMaddesi(title=title, kind=kind))
    kabul, ret = _degisiklik_oylari(guncel, change_votes_for, change_votes_against)
    maddeler = list(AgendaItem.objects.filter(assembly=guncel).order_by("order"))
    son_sira = maddeler[-1].order if maddeler else 0
    yeni_sira = son_sira + 1 if sira is None else sira
    if (
        not isinstance(yeni_sira, int)
        or isinstance(yeni_sira, bool)
        or not 1 <= yeni_sira <= son_sira + 1
    ):
        raise ValueError(EKLEME_SIRASI_GECERSIZ)
    _yer_ac(maddeler, yeni_sira)
    hesap = iz.yazar_hesabi()
    madde = AgendaItem.objects.create(
        assembly=guncel,
        order=yeni_sira,
        kind=tur_adi,
        title=baslik,
        added_by_vote=True,
        change_votes_for=kabul,
        change_votes_against=ret,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    tur = _Tur(guncel, gerekce)
    _gundem_degisikligi_denetimi(tur, madde)
    _gundeme_baglilik_denetimi(tur, madde)
    denetim_izi.degisiklik(madde, onceki=None)
    return GundemSonucu(madde=madde, uyarilar=tuple(tur.uyarilar))


@transaction.atomic
def gundemden_madde_cikar(
    madde: AgendaItem,
    *,
    change_votes_for: int | None = None,
    change_votes_against: int | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> GundemSonucu:
    """Toplantıda gündemden oylamayla madde çıkarır (md. 9/4): madde silinmez, `removed_by_vote` olur
    ve görüşülmez. Oylama satırı yoksa ya da oy çokluğu yoksa uyarı + gerekçe."""
    yazma_kapisi()
    _baslangic(TUTANAK_ROLLERI)
    guncel_madde, kurul = _madde_ve_kurul(madde)
    _durum(kurul, AssemblyStatus.YAPILDI)
    if guncel_madde.removed_by_vote:
        raise ValueError(MADDE_CIKARILMIS)
    if guncel_madde.added_by_vote:
        raise ValueError(EKLENEN_CIKARILMAZ)
    if guncel_madde.result:
        raise ValueError(SONUCLU_MADDE_CIKARILMAZ)
    kabul, ret = _degisiklik_oylari(kurul, change_votes_for, change_votes_against)
    onceki = denetim_izi.anlik(guncel_madde)
    guncel_madde.removed_by_vote = True
    guncel_madde.change_votes_for = kabul
    guncel_madde.change_votes_against = ret
    guncel_madde.updated_by_id = iz.yazar_hesabi()
    guncel_madde.save(
        update_fields=[
            "removed_by_vote",
            "change_votes_for",
            "change_votes_against",
            "updated_at",
            "updated_by",
        ]
    )
    tur = _Tur(kurul, gerekce)
    _gundem_degisikligi_denetimi(tur, guncel_madde)
    denetim_izi.degisiklik(guncel_madde, onceki=onceki)
    return GundemSonucu(madde=guncel_madde, uyarilar=tuple(tur.uyarilar))


@transaction.atomic
def gundem_sirasini_degistir(kurul: GeneralAssembly, *, sira: Sequence[int]) -> GenelKurulSonucu:
    """Gündemin sırasını değiştirir: `sira` maddelerin kimlikleridir, yeni sırayla, hepsi bir kez
    (çıkarılan maddeler de yerini korur). Sıra değişikliği md. 9/4'ün ekleme ve çıkarması değildir,
    uyarı üretmez (MA-16); gündem ilandan önce (planlama ve çağrı) ve toplantıda değiştirilir.
    Kural okumaz."""
    _duzenleme_kapisi(kurul, TUTANAK_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, *_SIRA_DEGISEBILIR)
    _cagri_sahipligi(guncel)
    maddeler = {m.pk: m for m in AgendaItem.objects.filter(assembly=guncel)}
    kimlikler = list(sira)
    if len(set(kimlikler)) != len(kimlikler) or set(kimlikler) != set(maddeler):
        raise ValueError(SIRA_GECERSIZ)
    _sirala([maddeler[pk] for pk in kimlikler])
    return GenelKurulSonucu(kurul=guncel, bilgiler=(SIRA_BILGISI,))


@dataclass(frozen=True)
class _Oylama:
    """Bir oylamanın denetlenmiş sayıları ve çoğunluk hesabı (`genel_kurul.karar_cogunlugu`)."""

    kabul: int
    ret: int
    salondaki: int | None
    cogunluk: bool
    atif: str


def _oylama(kurul: GeneralAssembly, kabul: object, ret: object, salondaki: object) -> _Oylama:
    """Oylamanın sonucu (md. 9/2 "katılanların çoğunluğu"; kullanıcı kararı S2 (a), S6 (iii); sert —
    hesap bütünlüğü): payda oylamada salonda bulunan sayıdır, girilmemişse toplantının katılım sayısı;
    salondaki katılımı, kabul ve ret toplamı paydayı aşamaz. Kabul oyu paydanın yarısından fazlaysa
    çoğunluk vardır (eşitlikte yoktur). Gündem maddesinin kararı ve ibra aynı hesabı kullanır."""
    kabul_sayisi, ret_sayisi = _sayi(kabul), _sayi(ret)
    katilan = _toplanti_katilani(kurul)
    salondaki_sayisi = _secimli_sayi(salondaki)
    payda = katilan if salondaki_sayisi is None else salondaki_sayisi
    if payda > katilan:
        raise ValueError(SALONDAKI_KATILANDAN_COK)
    if kabul_sayisi + ret_sayisi > payda:
        raise ValueError(OYLAR_KATILANI_ASAR)
    sonuc = genel_kurul.karar_cogunlugu(
        kabul_sayisi, payda, tarih=birinci_toplanti_gunu(kurul), donem=kural_donemi(kurul)
    )
    return _Oylama(
        kabul=kabul_sayisi,
        ret=ret_sayisi,
        salondaki=salondaki_sayisi,
        cogunluk=sonuc["durum"] == "uygun",
        atif=str(sonuc["atif"]),
    )


@transaction.atomic
def karar_sonucu_yaz(
    madde: AgendaItem,
    *,
    result: str | None = None,
    votes_for: int | None = None,
    votes_against: int | None = None,
    present_count: int | None = None,
    result_text: str = "",
) -> GundemSonucu:
    """Gündem maddesinin sonucunu yazar (md. 9/2, 9/6; kullanıcı kararı S6 (iii)).

    Oylanan maddenin sonucu oylardan HESAPLANIR (`genel_kurul.karar_cogunlugu`, sert — hesap
    bütünlüğü): kabul oyu paydanın yarısından fazlaysa kabul, değilse ret (eşitlikte karar
    alınmamıştır; S2 (a)). Payda oylamada salonda bulunan sayıdır, girilmemişse toplantının katılım
    sayısıdır. `result` verilirse hesapla karşılaştırılır: oylarla çelişen sonuç (ör. çoğunluk yokken
    "kabul") kaydedilmez (`KuralSert`). Oylanmayan madde "görüşüldü"dür (raporlar, tahmini bütçe,
    dilekler; oy girilmez). İbra ve seçim maddelerinin sonucu kendi yolundadır (6. adım).
    """
    yazma_kapisi()
    _baslangic(TUTANAK_ROLLERI)
    guncel_madde, kurul = _madde_ve_kurul(madde)
    _durum(kurul, AssemblyStatus.YAPILDI)
    if guncel_madde.removed_by_vote:
        raise ValueError(MADDE_CIKARILMIS)
    if guncel_madde.kind in _KENDI_YOLUNDA:
        raise ValueError(SONUC_KENDI_YOLUNDA)
    if result is not None and result not in AgendaResult.values:
        raise ValueError(SONUC_GECERSIZ)
    oylar_girildi = any(v is not None for v in (votes_for, votes_against, present_count))
    kabul: int | None = None
    ret: int | None = None
    salondaki: int | None = None
    if result == AgendaResult.GORUSULDU:
        if oylar_girildi:
            raise ValueError(GORUSULDU_OYSUZ)
        hesaplanan = str(AgendaResult.GORUSULDU)
    else:
        if votes_for is None or votes_against is None:
            raise ValueError(OYLAR_GEREKLI)
        oylama = _oylama(kurul, votes_for, votes_against, present_count)
        kabul, ret, salondaki = oylama.kabul, oylama.ret, oylama.salondaki
        hesaplanan = str(AgendaResult.KABUL if oylama.cogunluk else AgendaResult.RET)
        if result is not None and result != hesaplanan:
            raise KuralSert(detail=f"{KARAR_OYLARLA_CELISIYOR} ({oylama.atif}).")
    onceki = denetim_izi.anlik(guncel_madde)
    guncel_madde.result = hesaplanan
    guncel_madde.votes_for = kabul
    guncel_madde.votes_against = ret
    guncel_madde.present_count = salondaki
    guncel_madde.result_text = result_text.strip()
    guncel_madde.updated_by_id = iz.yazar_hesabi()
    guncel_madde.save(
        update_fields=[
            "result",
            "votes_for",
            "votes_against",
            "present_count",
            "result_text",
            "updated_at",
            "updated_by",
        ]
    )
    denetim_izi.degisiklik(guncel_madde, onceki=onceki)
    return GundemSonucu(madde=guncel_madde)


# ---------------------------------------------------------------------------
# Divan (md. 10/1-c; U25)
# ---------------------------------------------------------------------------
def kurulun_divani(kurul: GeneralAssembly) -> list[OrganMembership]:
    """Genel kurulun iptal edilmemiş divan kayıtları (başkan önce)."""
    return sorted(
        OrganMembership.objects.filter(assembly=kurul, organ=OrganType.DIVAN).exclude(
            status=MembershipStatus.IPTAL
        ),
        key=lambda u: (u.role != MembershipRole.BASKAN, u.pk),
    )


def _divan_uyesi(tur: _Tur, kisi: OabPerson, rol: str, gun: date) -> OrganMembership:
    """Divanın bir kaydı: genel kurulun kendi dönemine, seçilmiş açılır (aday kaydı aranmaz, U25);
    kişi türü `genel_kurul.divan_uye_turleri` ile denetlenir (uyarı + gerekçe; konu üyelik)."""
    hesap = iz.yazar_hesabi()
    uyelik = OrganMembership.objects.create(
        term=tur.donem,
        person=kisi,
        organ=OrganType.DIVAN,
        assembly=tur.kurul,
        role=rol,
        seat_type=SeatType.ASIL,
        elected_by=ElectedBy.GENEL_KURUL,
        status=MembershipStatus.SECILDI,
        start_date=gun,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    # Veli işareti türden önce gelir (MA-11): veli olan öğretmen ve idareci velidir; 18 yaşını
    # doldurduğu beyan edilmiş kursiyer kursiyerdir; öteki kişiler listede olmayan türdür.
    sonuc = uyum.denetle(
        "genel_kurul.divan_uye_turleri",
        uyelikler.yk_uye_turu(kisi),
        konu=uyelik,
        **tur.ortak(),
    )
    tur.kaydet("genel_kurul.divan_uye_turleri", sonuc, kurulun=False)
    satir = _ozet_satiri("genel_kurul.divan_uye_turleri", sonuc.sonuc)
    if satir is not None:
        uyelik.rule_warnings = [satir]
        uyelik.save(update_fields=["rule_warnings"])
    denetim_izi.degisiklik(uyelik, onceki=None)
    return uyelik


@transaction.atomic
def divan_sec(
    kurul: GeneralAssembly,
    *,
    baskan: OabPerson,
    katip: OabPerson,
    gerekce: uyum.Gerekce | None = None,
) -> GenelKurulSonucu:
    """Divan başkanını ve kâtibi kaydeder (md. 10/1-c; U25): genel kurulun yapıldığı toplantıda, açık
    oyla, veliler ya da 18 yaşını doldurmuş kursiyerler arasından. Kayıt `OrganMembership(DIVAN)`'dır,
    kişiler birlik kişisidir (adlar şifreli, `OabPerson`). Kişi türü uyarıdır (gerekçeyle kaydedilir);
    başkan ve kâtip ayrı kişidir; bir genel kurulun tek divanı vardır."""
    yazma_kapisi()
    _baslangic(TUTANAK_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, AssemblyStatus.YAPILDI)
    if baskan.pk == katip.pk:
        raise ValueError(DIVAN_AYNI_KISI)
    if kurulun_divani(guncel):
        raise ValueError(DIVAN_SECILDI)
    baskan_kaydi = uyelikler.kisi_aktif(baskan)
    katip_kaydi = uyelikler.kisi_aktif(katip)
    tur = _Tur(guncel, gerekce)
    gun = genel_kurul_gunu(guncel)
    _divan_uyesi(tur, baskan_kaydi, MembershipRole.BASKAN, gun)
    _divan_uyesi(tur, katip_kaydi, MembershipRole.KATIP, gun)
    return _sonuc(tur)


# ---------------------------------------------------------------------------
# Katılım düzeltmesi (tasarım §5.2.3 `AttendanceCorrection`)
# ---------------------------------------------------------------------------
def katilim_duzeltmeleri(kurul: GeneralAssembly) -> list[AttendanceCorrection]:
    """Genel kurulun katılım düzeltmeleri, yazılış sırasıyla (ekleme-yalnız; tutanak ve evrak okur)."""
    return list(AttendanceCorrection.objects.filter(assembly=kurul).order_by("corrected_at", "pk"))


def ilk_girilen_deger(kurul: GeneralAssembly, alan: str) -> int | None:
    """Düzeltilmiş sayının toplantıda girilen (ilk) değeri: ilk düzeltme satırının önceki değeri;
    düzeltme yoksa kayıttaki değer. Kayıttaki değer son düzeltme satırının değeridir."""
    if alan not in DUZELTILEBILIR_ALANLAR:
        raise ValueError(DUZELTME_ALANI_GECERSIZ)
    ilk = (
        AttendanceCorrection.objects.filter(assembly=kurul, field=alan)
        .order_by("corrected_at", "pk")
        .first()
    )
    if ilk is not None:
        onceki: int | None = ilk.old_value
        return onceki
    if alan.startswith(_DAGILIM_ONEKI):
        deger = (kurul.attendance_by_kind or {}).get(alan.removeprefix(_DAGILIM_ONEKI))
        return None if deger is None else int(deger)
    sayi: int | None = getattr(kurul, alan)
    return sayi


def _dagilimin_toplantisi(kurul: GeneralAssembly) -> str:
    """Türe göre dağılım, velisi katılan öğrenci ve gözlemci son yapılan toplantının sayılarıdır:
    ikinci toplantı yapıldıysa ikincinin (4. adım: ikinci toplantı birincinin üzerine yazar)."""
    return str(
        AssemblyMeeting.IKINCI
        if kurul.second_attendee_count is not None
        else AssemblyMeeting.BIRINCI
    )


def _alanin_toplantisi(kurul: GeneralAssembly, alan: str) -> str:
    if alan == "first_attendee_count":
        return str(AssemblyMeeting.BIRINCI)
    if alan == "second_attendee_count":
        return str(AssemblyMeeting.IKINCI)
    return _dagilimin_toplantisi(kurul)


def _yeter_sayi_sonucu_degisir(kurul: GeneralAssembly, eski: int | None, yeni: int) -> bool:
    """Birinci toplantının katılımı dondurulmuş yeter sayının bir yanından öbür yanına geçiyor mu?"""
    gerekli = kurul.quorum_required
    if gerekli is None or eski is None:  # tür daraltması: ilandan sonra ikisi de doludur
        return False
    return (eski >= gerekli) != (yeni >= gerekli)


def _paydasi_degisen_kararlar(kurul: GeneralAssembly, katilan: int) -> list[tuple[AgendaItem, str]]:
    """Katılım düzeltmesinin gündem maddelerine etkisi (kullanıcı kararı S6 (iii); hesap bütünlüğü).

    Düzeltilen sayı genel kurulun yapıldığı toplantının katılımıysa oylamaya katılabilecek üye sayısı
    da değişir: girilmiş oyların, oylamada salonda bulunan sayının ve gündem değişikliği oylarının
    toplamı yeni katılımı aşamaz (sert; `karar_sonucu_yaz` ve `_degisiklik_oylari` ile aynı sınır).
    Salondaki sayısı girilmemiş oylanmış maddenin paydası katılımdır: sonucu yeni paydayla yeniden
    hesaplanır (`genel_kurul.karar_cogunlugu`). Sonucu değişen maddeler yeni sonuçlarıyla döner
    (yazmaz)."""
    degisenler: list[tuple[AgendaItem, str]] = []
    tarih, donem = birinci_toplanti_gunu(kurul), kural_donemi(kurul)
    for madde in AgendaItem.objects.filter(assembly=kurul).order_by("order"):
        if madde.change_votes_for is not None and madde.change_votes_against is not None:
            if madde.change_votes_for + madde.change_votes_against > katilan:
                raise ValueError(DUZELTME_OYLARIN_ALTINDA)
        if madde.votes_for is None or madde.votes_against is None:
            continue
        if max(madde.present_count or 0, madde.votes_for + madde.votes_against) > katilan:
            raise ValueError(DUZELTME_OYLARIN_ALTINDA)
        if (
            madde.present_count is not None
            or madde.kind in _KENDI_YOLUNDA
            or madde.result not in (AgendaResult.KABUL, AgendaResult.RET)
        ):
            continue
        sonuc = genel_kurul.karar_cogunlugu(madde.votes_for, katilan, tarih=tarih, donem=donem)
        hesaplanan = str(AgendaResult.KABUL if sonuc["durum"] == "uygun" else AgendaResult.RET)
        if hesaplanan != madde.result:
            degisenler.append((madde, hesaplanan))
    return degisenler


def _paydasi_degisen_ibralar(kurul: GeneralAssembly, katilan: int) -> dict[str, str]:
    """Katılım düzeltmesinin ibraya etkisi (`_paydasi_degisen_kararlar`'ın ibra kolu; kullanıcı kararı
    S6 (iii)): ibra oylarının ve salondaki sayının toplamı yeni katılımı aşamaz (sert); salondaki sayısı
    girilmemiş ibranın sonucu yeni paydayla yeniden hesaplanır. Sonucu değişen kurulların ibra alanı ve
    yeni sonucu döner (yazmaz)."""
    degisenler: dict[str, str] = {}
    tarih, donem = birinci_toplanti_gunu(kurul), kural_donemi(kurul)
    for sonuc_alani, kabul_alani, ret_alani, salondaki_alani in _IBRA_ALANLARI.values():
        kabul, ret = getattr(kurul, kabul_alani), getattr(kurul, ret_alani)
        salondaki = getattr(kurul, salondaki_alani)
        if kabul is None or ret is None:
            continue
        if max(salondaki or 0, kabul + ret) > katilan:
            raise ValueError(DUZELTME_OYLARIN_ALTINDA)
        if salondaki is not None:
            continue
        sonuc = genel_kurul.karar_cogunlugu(kabul, katilan, tarih=tarih, donem=donem)
        hesaplanan = str(Discharge.EDILDI if sonuc["durum"] == "uygun" else Discharge.EDILMEDI)
        if hesaplanan != getattr(kurul, sonuc_alani):
            degisenler[sonuc_alani] = hesaplanan
    return degisenler


def _karar_sonucunu_yeniden_yaz(madde: AgendaItem, sonuc: str, satir: int) -> str:
    """Düzeltmenin değiştirdiği karar sonucunu yazar (izli; iz satırı akış satırına bağlı) ve bilgi
    satırını döner."""
    onceki = denetim_izi.anlik(madde)
    eski = AgendaResult(madde.result).label
    madde.result = sonuc
    madde.updated_by_id = iz.yazar_hesabi()
    madde.save(update_fields=["result", "updated_at", "updated_by"])
    denetim_izi.degisiklik(madde, onceki=onceki, compliance_item=satir)
    return (
        f"{madde.order}. {madde.title}: sonuç oylardan yeniden hesaplandı "
        f"({eski} → {AgendaResult(sonuc).label})."
    )


def _ibrayi_yeniden_yaz(tur: _Tur, kurul: GeneralAssembly, ibralar: Mapping[str, str]) -> list[str]:
    """Düzeltmenin değiştirdiği ibra sonuçlarını kurula işler (kayıt düzeltmenin yazımıyla, izli) ve
    bilgi satırlarını döner. Yönetim kurulunun ibrası değişirse yan akış gözden geçirilir (md. 11/1-ç);
    tutanak tamamlanmışsa ve yeni sonuç "ibra edilmedi"yse il/ilçe MEM bildirimi takvime girer (tutanağın
    tamamlanmasındaki satır, S4 (a))."""
    bilgiler: list[str] = []
    for alan, yeni in ibralar.items():
        kurul_adi = alan.removeprefix("discharge_")
        eski = Discharge(getattr(kurul, alan)).label
        setattr(kurul, alan, yeni)
        bilgiler.append(
            f"İbra ({_IBRA_KURUL_ADI[kurul_adi]}): sonuç oylardan yeniden hesaplandı "
            f"({eski} → {Discharge(yeni).label})."
        )
    if "discharge_yk" in ibralar:
        bilgiler.append(IBRA_YAN_AKISI_GOZDEN_GECIR)
        if (
            kurul.status == AssemblyStatus.TUTANAK_TAMAM
            and ibralar["discharge_yk"] == Discharge.EDILMEDI
        ):
            uyum.takvim_satiri_yaz(
                ComplianceObligation.IBRA_EDILMEDI_BILDIRIMI,
                donem=tur.donem,
                due_date=genel_kurul_gunu(kurul),
                mesaj=ibra_bildirimi_mesaji(kurul),
                responsible_role=_YONETICI,
                konu=kurul,
                hazirlik_yazimi=True,
            )
    return bilgiler


@transaction.atomic
def katilim_duzelt(
    kurul: GeneralAssembly,
    *,
    toplanti: str,
    degerler: Mapping[str, int],
    justification: str,
    gerekce: uyum.Gerekce | None = None,
) -> GenelKurulSonucu:
    """Toplantıda girilen katılım sayılarını gerekçeyle düzeltir (tasarım §5.2.3, §7.1).

    Her değişen sayı bir `AttendanceCorrection` satırıdır (ekleme-yalnız: satır değişmez, silinmez);
    genel kuruldaki sayı son satırın değeridir. Gerekçe zorunludur ve şifrelidir. Dondurulmuş yeter
    sayı düzeltilemez (sert — hesap bütünlüğü; `YeterSayiDonduruldu`). Birden çok sayı tek işlemde
    düzeltilir: türe göre dağılımın toplamı yine katılım sayısını tutmalıdır (hesap bütünlüğü).
    Düzeltme birinci toplantıda yeter sayının sağlanıp sağlanmadığını değiştiriyorsa uyarı +
    gerekçedir (akış satırı); genel kurulun durumu hiçbir düzeltmede değişmez.

    Genel kurulun yapıldığı toplantının katılımı düzeltilirse gündem maddeleri aynı işlemde yeniden
    denetlenir (`_paydasi_degisen_kararlar`): oy toplamları yeni katılımı aşamaz (sert — hesap
    bütünlüğü); salondaki sayısı girilmemiş maddenin sonucu yeni paydayla yeniden hesaplanıp yazılır
    (kullanıcı kararı S6 (iii): oylarla çelişen sonuç kayıtta durmaz) ve sonucu değiştiren düzeltme
    uyarı + gerekçedir (plan F2 §5.1; akış satırı, konusu katılım sayısının düzeltme satırı). İbra
    oylaması da aynı denetimden geçer (`_paydasi_degisen_ibralar`): sonucu değişen ibra yeniden yazılır,
    yönetim kurulunun ibrası değişirse yan akış bilgi satırıyla gözden geçirilir."""
    yazma_kapisi()
    _baslangic(TUTANAK_ROLLERI)
    metin = justification.strip()
    if not metin:
        raise ValueError(DUZELTME_GEREKCESI_GEREKLI)
    guncel = _guncel(kurul)
    _durum(guncel, *_DUZELTILEBILIR_DURUMLAR)
    if toplanti not in AssemblyMeeting.values:
        raise ValueError(TOPLANTI_GECERSIZ)
    if not degerler:
        raise ValueError(DUZELTME_BOS)
    onceki_kurul = denetim_izi.anlik(guncel)
    yapildi = guncel.status in (AssemblyStatus.YAPILDI, AssemblyStatus.TUTANAK_TAMAM)
    eski_payda = _toplanti_katilani(guncel) if yapildi else None
    dagilim = dict(guncel.attendance_by_kind or {})
    degisenler: list[tuple[str, int | None, int]] = []
    alanlar: set[str] = set()
    for alan, deger in degerler.items():
        if alan in DONDURULAN_ALANLAR:
            raise YeterSayiDonduruldu
        if alan not in DUZELTILEBILIR_ALANLAR:
            raise ValueError(DUZELTME_ALANI_GECERSIZ)
        yeni = _sayi(deger)
        if alan == "second_attendee_count" and guncel.second_attendee_count is None:
            raise ValueError(IKINCI_TOPLANTI_YAPILMADI)
        if toplanti != _alanin_toplantisi(guncel, alan):
            raise ValueError(DUZELTME_TOPLANTISI)
        eski: int | None
        if alan.startswith(_DAGILIM_ONEKI):
            tur_adi = alan.removeprefix(_DAGILIM_ONEKI)
            eski = dagilim.get(tur_adi)
            dagilim[tur_adi] = yeni
            alanlar.add("attendance_by_kind")
        else:
            eski = getattr(guncel, alan)
            setattr(guncel, alan, yeni)
            alanlar.add(alan)
        if eski == yeni:
            raise ValueError(DUZELTME_DEGISMIYOR)
        degisenler.append((alan, eski, yeni))
    guncel.attendance_by_kind = dagilim
    katilan = (
        guncel.second_attendee_count
        if _dagilimin_toplantisi(guncel) == AssemblyMeeting.IKINCI
        else guncel.first_attendee_count
    )
    if dagilim and sum(dagilim.values()) != katilan:
        raise ValueError(DAGILIM_TOPLAMI)
    yeni_payda = _toplanti_katilani(guncel) if yapildi else None
    payda_alani = (
        "second_attendee_count"
        if guncel.held_at_meeting == AssemblyMeeting.IKINCI
        else "first_attendee_count"
    )
    kararlar: list[tuple[AgendaItem, str]] = []
    ibralar: dict[str, str] = {}
    if yeni_payda is not None and yeni_payda != eski_payda:
        kararlar = _paydasi_degisen_kararlar(guncel, yeni_payda)
        ibralar = _paydasi_degisen_ibralar(guncel, yeni_payda)
    tur = _Tur(guncel, gerekce)
    hesap = iz.yazar_hesabi()
    an = timezone.now()
    bilgiler: list[str] = []
    for alan, eski, yeni in degisenler:
        duzeltme = AttendanceCorrection.objects.create(
            assembly=guncel,
            meeting=toplanti,
            field=alan,
            old_value=eski,
            new_value=yeni,
            justification=metin,
            corrected_by_id=hesap,
            corrected_at=an,
            created_by_id=hesap,
            updated_by_id=hesap,
        )
        bag = None
        if alan == "first_attendee_count" and _yeter_sayi_sonucu_degisir(guncel, eski, yeni):
            satir = uyum.akis_sapmasi(
                DUZELTME_YETER_SAYI_AKISI,
                DUZELTME_YETER_SAYI,
                donem=tur.donem,
                konu=duzeltme,
                gerekce=gerekce,
                hazirlik_yazimi=True,
            )
            tur.akis(DUZELTME_YETER_SAYI_AKISI, DUZELTME_YETER_SAYI, kurulun=False)
            bag = satir.pk
        if alan == payda_alani and (kararlar or ibralar):
            karar_satiri = uyum.akis_sapmasi(
                DUZELTME_KARAR_AKISI,
                DUZELTME_KARAR,
                donem=tur.donem,
                konu=duzeltme,
                gerekce=gerekce,
                hazirlik_yazimi=True,
            )
            tur.akis(DUZELTME_KARAR_AKISI, DUZELTME_KARAR, kurulun=False)
            bilgiler.extend(
                _karar_sonucunu_yeniden_yaz(madde, sonuc, karar_satiri.pk)
                for madde, sonuc in kararlar
            )
            bilgiler.extend(_ibrayi_yeniden_yaz(tur, guncel, ibralar))
            alanlar.update(ibralar.keys())
            bag = karar_satiri.pk if bag is None else bag
        denetim_izi.degisiklik(duzeltme, onceki=None, compliance_item=bag)
    guncel.updated_by_id = hesap
    guncel.save(update_fields=[*sorted(alanlar), "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel, onceki=onceki_kurul)
    return _sonuc(tur, bilgiler)


# ---------------------------------------------------------------------------
# Katılım işareti (`ParentRoster.attended_*`; plan F2 §7 U33, S12)
# ---------------------------------------------------------------------------
def _isaret_kapisi() -> None:
    """Katılım işareti veli adını gösterir (R9, dipnot ¹⁰): yalnız program yöneticisi; kişisel veri
    içeren çıktı kapısı ve genel kurul yazma kapısı."""
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.KISISEL_VERI_CIKTISI)
    _kapi()
    _daralt(ISARET_ROLLERI)


def _isaret_toplantisi(kurul: GeneralAssembly, toplanti: str) -> None:
    """İşaret yapılmakta ya da yapılmış toplantıya, tutanak tamamlanana dek konur: birinci toplantı
    ilandan sonra; ikinci toplantı birincide yeter sayı sağlanamadıysa ve tarihi ilan edildiyse."""
    if toplanti not in AssemblyMeeting.values:
        raise ValueError(TOPLANTI_GECERSIZ)
    if toplanti == AssemblyMeeting.BIRINCI:
        _durum(
            kurul,
            AssemblyStatus.ILAN_EDILDI,
            AssemblyStatus.YETER_SAYI_YOK,
            AssemblyStatus.YAPILDI,
        )
        return
    _durum(kurul, AssemblyStatus.YETER_SAYI_YOK, AssemblyStatus.YAPILDI)
    if kurul.second_meeting_at is None or kurul.held_at_meeting == AssemblyMeeting.BIRINCI:
        raise ValueError(DURUM_GECERSIZ)


def _isareti_engelleyen_kurullar(kurul: GeneralAssembly, kurul_kimlikleri: set[int]) -> set[int]:
    """Satırlarındaki işaret başka bir genel kurulda işaretlemeyi engelleyen genel kurullar: işareti
    hâlâ yazılabilen (ilan edilmiş, yeter sayısı sağlanamamış ya da yapılmış) öteki kurullar. İptal
    edilmiş ya da tutanağı tamamlanmış kurulun işareti bitmiş bir sayım yardımıdır (U33: işaret
    yalnız `TUTANAK_TAMAM`'a dek yazılır; sayılar kurulda dondurulmuştur), yeni işaretle üzerine
    yazılır."""
    adaylar = kurul_kimlikleri - {kurul.pk}
    if not adaylar:
        return set()
    return set(
        GeneralAssembly.objects.filter(pk__in=adaylar, status__in=_ISARET_YAZILABILIR).values_list(
            "pk", flat=True
        )
    )


def _veli_satirlari(kurul: GeneralAssembly) -> QuerySet[ParentRoster]:
    """Genel kurulun veli listesi: kapanacak dönemin satırları; yeni okulun ilk genel kurulunda
    dönemsiz satırlar (ilk dönem açılınca bağlanırlar)."""
    if kurul.term_id is None:
        return ParentRoster.objects.filter(term__isnull=True)
    return ParentRoster.objects.filter(term_id=kurul.term_id)


def kurulun_veli_satirlari(kurul: GeneralAssembly) -> QuerySet[ParentRoster]:
    """Genel kurulun veli listesi (`_veli_satirlari`): elden yazılı davetin sınıf adetleri ve veli
    adlı çıktılar (E07, E08; `genel_kurul_evraki`) buradan okur. Okuma yazmaz."""
    return _veli_satirlari(kurul)


def katilim_isareti_sayisi(kurul: GeneralAssembly, toplanti: str) -> int:
    """Toplantının işaret sayısı (kişisiz): katılım sayısına ÖNERİdir, hesaplanmaz (U33)."""
    return ParentRoster.objects.filter(
        attended_assembly_id=kurul.pk, attended_meeting=toplanti
    ).count()


def katilim_isaretleri(kurul: GeneralAssembly, *, toplanti: str) -> list[dict[str, Any]]:
    """Katılım işaretleri penceresinin listesi (U33): sınıf başına veli satırları, veli adı ve bu
    toplantının işareti; `oteki_toplanti` aynı kurulun öteki toplantısının işaretidir (işaretlenirse
    bu toplantıya taşınır), `baska_isaret` işaretlemeyi engelleyen başka kurulun işaretidir
    (`_isareti_engelleyen_kurullar`). Ad yalnız burada çözülür; okuma erişim günlüğüne yazılır
    (kişisel veri içeren çıktı, `VELI_LISTESI_CIKTISI`: listenin sha256'sı ve satır sayısı; ad
    günlüğe girmez). Günlük satırı yazılamazsa liste verilmez. Yalnız program yöneticisi."""
    _isaret_kapisi()
    guncel = _guncel(kurul)
    _isaret_toplantisi(guncel, toplanti)
    satirlar = sorted(
        _veli_satirlari(guncel),
        key=lambda s: (
            excel_veli.sinif_sira_anahtari(s.student_class),
            normalize.tr_sort_key("" if is_corrupt(s.full_name) else s.full_name),
            s.pk,
        ),
    )
    engelleyen = _isareti_engelleyen_kurullar(
        guncel, {s.attended_assembly_id for s in satirlar if s.attended_assembly_id is not None}
    )
    siniflar: dict[str, list[dict[str, Any]]] = {}
    for satir in satirlar:
        bu_kurul = satir.attended_assembly_id == guncel.pk
        siniflar.setdefault(satir.student_class, []).append(
            {
                "id": satir.pk,
                "veli": None if is_corrupt(satir.full_name) else str(satir.full_name),
                "isaretli": bu_kurul and satir.attended_meeting == toplanti,
                "oteki_toplanti": bu_kurul and satir.attended_meeting != toplanti,
                "baska_isaret": satir.attended_assembly_id in engelleyen,
            }
        )
    liste = [{"sinif": sinif, "satirlar": ogeler} for sinif, ogeler in siniflar.items()]
    ozet = hashlib.sha256(
        json.dumps(liste, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    erisim_gunlugu.yaz(
        AccessKind.VELI_LISTESI_CIKTISI,
        model=GeneralAssembly,
        object_id=guncel.pk,
        document_sha256=ozet,
        row_count=len(satirlar),
    )
    return liste


@transaction.atomic
def katilim_isaretle(
    kurul: GeneralAssembly,
    *,
    toplanti: str,
    isaretle: Sequence[int] = (),
    kaldir: Sequence[int] = (),
) -> int:
    """Veli satırlarına toplantının katılım işaretini koyar ya da kaldırır (U33); toplantının işaret
    sayısını döner (öneri). İşaret sayım yardımıdır: genel kuruldaki katılım sayısı elle girilir,
    işaretten hesaplanmaz. İşareti hâlâ yazılabilen başka genel kurulun işaretini taşıyan satır
    işaretlenmez; iptal edilmiş ya da tutanağı tamamlanmış kurulun işaretinin üzerine yazılır. Satır
    tek işaret taşır: aynı kurulun öteki toplantısında işaretli satır işaretlenince işaret bu
    toplantıya taşınır (öteki toplantının sayısı kurulda dondurulmuştur). Denetim izine
    kişisiz `ISARET` satırı düşer (satır kimliği, ad, sınıf ve sayı yok; veli listesinin hiçbir
    alanı ize girmez, tasarım §4.6.2). Kural okumaz. Yalnız program yöneticisi."""
    app_password.require_password_set()
    _isaret_kapisi()
    guncel = _guncel(kurul)
    _isaret_toplantisi(guncel, toplanti)
    eklenecek, kaldirilacak = set(isaretle), set(kaldir)
    if eklenecek & kaldirilacak:
        raise ValueError(ISARET_CAKISIYOR)
    istenen = eklenecek | kaldirilacak
    if not istenen:
        return katilim_isareti_sayisi(guncel, toplanti)
    durumlar = {
        pk: (kurul_pk, gorusme)
        for pk, kurul_pk, gorusme in _veli_satirlari(guncel)
        .filter(pk__in=istenen)
        .values_list("pk", "attended_assembly_id", "attended_meeting")
    }
    if set(durumlar) != istenen:
        raise ValueError(ISARET_SATIRI_YOK)
    engelleyen = _isareti_engelleyen_kurullar(
        guncel, {durumlar[pk][0] for pk in eklenecek if durumlar[pk][0] is not None}
    )
    if any(durumlar[pk][0] in engelleyen for pk in eklenecek):
        raise ValueError(ISARET_BASKA_KURULDA)
    if any(durumlar[pk] != (guncel.pk, toplanti) for pk in kaldirilacak):
        raise ValueError(ISARET_YOK)
    if eklenecek:
        ParentRoster.objects.filter(pk__in=eklenecek).update(
            attended_assembly=guncel, attended_meeting=toplanti
        )
    if kaldirilacak:
        ParentRoster.objects.filter(pk__in=kaldirilacak).update(
            attended_assembly=None, attended_meeting=""
        )
    denetim_izi.olay(
        AuditAction.ISARET,
        model=denetim_izi.model_etiketi(ParentRoster),
        object_id="",
        changed_fields=["attended_assembly", "attended_meeting"],
        term=kural_donemi(guncel).pk,
    )
    return katilim_isareti_sayisi(guncel, toplanti)


# ---------------------------------------------------------------------------
# 6. adım: aday ve seçim (md. 10/1-d, 11/1-a, b, 12/4, 13/8; plan F2 §7 U26, U27, S6 (i), S10)
# ---------------------------------------------------------------------------
#: Aday kaydı ve seçim "Kim"i: ilandan önce planlamanın, toplantıda tutanağın rolleri (tasarım §7.1
#: `PLANLANDI` ve `YAPILDI → TUTANAK_TAMAM`): program yöneticisi, sekreter.
SECIM_ROLLERI: Final = frozenset({_YONETICI, _SEKRETER})
#: Seçim maddesinin kurulu (gündem türü → organ).
SECIM_ORGANLARI: Final[Mapping[str, str]] = {
    AgendaItemKind.SECIM_YK: OrganType.YONETIM_KURULU,
    AgendaItemKind.SECIM_DK: OrganType.DENETLEME_KURULU,
}
#: Aday kaydının açıldığı durumlar: planlamadan toplantının sonuna dek (U26: salondan adaylık).
_ADAY_KAYDI_ACIK: Final = (
    AssemblyStatus.PLANLANDI,
    AssemblyStatus.CAGRILDI,
    AssemblyStatus.ILAN_EDILDI,
    AssemblyStatus.YETER_SAYI_YOK,
    AssemblyStatus.YAPILDI,
)
#: `genel_kurul.secim_bicimi` belirteçleri (kural paketinin değerleri; md. 10/1-d, 11/1-a, b).
SECIM_LISTE: Final = "LISTE"
SECIM_ACIK_OY: Final = "ACIK_OY"
#: Yönetim kurulu seçilme sayacının kuralı (U26: bilinmeyen beyanın toplu gerekçesi).
_YK_SAYAC_KURALI: Final = "yonetim_kurulu.secilme_siniri"

ADAY_ORGANI = (
    "Genel kurulda yalnız yönetim kurulu ve Denetleme Kurulunun veli koltuğu için aday kaydedilir "
    "(md. 11/1-a, b)."
)
SECIM_MADDESI_DEGIL = "Bu gündem maddesi seçim maddesi değil."
SECIM_SONUCU_GIRILDI = (
    "Bu seçimin sonucu girildi; yanlış girilen sonuç seçimin gerekçeli iptaliyle düzeltilir "
    "(seçilenlerin kayıtları iptal olur, sonuç yeniden girilir)."
)
SECIM_SONUCU_YOK = "Bu seçimin sonucu girilmedi."
SECIM_BICIMI_GECERSIZ = (
    "Seçimin biçimi girilirken liste hâlinde ve açık oyla yapılıp yapılmadığı ikisi birlikte "
    "işaretlenir."
)
ADAY_TEKRAR = "Bir adayın sonucu bir kez girilir."
SECILEN_ADAYDAN = (
    "Seçilen yalnız bu genel kurulun bu kurula aday kaydından olur (tek kaynak; hesap bütünlüğü)."
)
OY_KATILANDAN_COK = "Bir adayın oyu toplantıya katılan üye sayısını aşamaz (hesap bütünlüğü)."
YEDEK_SIRASI_YALNIZ_SECILEN_YEDEKTE = "Yedek sırası yalnız seçilen yedek üyeye verilir."
YEDEK_SIRASI_GECERSIZ = "Yedek sırası 1 ya da daha büyük tam sayı olmalıdır."
YEDEK_SIRASI_TEKRAR = (
    "Seçilen yedeklerin sırası birbirinden farklı olmalıdır (md. 13/6; hesap bütünlüğü)."
)
OLAGANUSTU_DK_SECIMI_YOK = (
    "Olağanüstü genel kurul Denetleme Kuruluna seçim yapmaz: md. 13/8 olağanüstü genel kurulun "
    "seçtiği kurul olarak yalnız yönetim kurulunu sayar (kullanıcı kararı S10)."
)
ESIT_OYLU_YEDEK_BILGISI: Final = (
    "Eşit oy alan ya da oyu girilmeyen yedeklerin sırası programca hesaplanmaz; sıra elle girilir "
    "(md. 13/6 yedekleri aldıkları oy sırasıyla çağırır, eşitlikte yöntem vermez)."
)


@dataclass(frozen=True)
class AdayOyu:
    """Seçimde bir adayın sonucu: aldığı oy, seçilip seçilmediği ve (eşit oyda) elle yedek sırası."""

    uyelik: OrganMembership
    votes: int | None = None
    secildi: bool = False
    seat_order: int | None = None


@dataclass(frozen=True)
class SecimSonucu:
    """Seçimin sonucu: seçim maddesi, seçilenler, olağanüstü seçimde düşen eski üyelikler, uyarılar
    (atıflı) ve bilgi satırları."""

    madde: AgendaItem
    secilenler: tuple[OrganMembership, ...] = ()
    dusenler: tuple[OrganMembership, ...] = ()
    uyarilar: tuple[dict[str, Any], ...] = ()
    bilgiler: tuple[str, ...] = ()


def secim_donemi(kurul: GeneralAssembly) -> OabTerm:
    """Adayların ve seçilenlerin dönemi: olağanda açılacak (hazırlık) dönem, olağanüstüde genel
    kurulun kendi dönemi (tasarım §7.1 notları; md. 13/8; `uyelikler._genel_kurul_bagi`)."""
    donem = kurul.term if kurul.kind == AssemblyKind.OLAGANUSTU else kurul.opens_term
    if donem is None:  # tür daraltması: olağan genel kurul hazırlık dönemini açar
        raise ValueError(DONEMSIZ_GENEL_KURUL)
    return donem


@transaction.atomic
def aday_kaydet(
    kurul: GeneralAssembly,
    *,
    person: OabPerson,
    organ: str,
    seat_type: str,
    seat_group: str = "",
    gerekce: uyum.Gerekce | None = None,
) -> OrganMembership:
    """Genel kurulun asıl ya da yedek listesine aday kaydeder (U26; `ADAY`). Kayıt planlamadan
    toplantının sonuna dek açılır (salondan adaylık; mevzuat aday başvurusunu düzenlemez). Kişi ve
    koltuk uygunluğu, tek koltuk, iki kurul ve müdür engeli F1c'nin kayıt yolunda denetlenir
    (`uyelikler.assign_membership`; sert olanlar CLAUDE.md altın kural 3). Denetleme Kurulunda yalnız
    veli koltuğu (öğretmen koltuğu genel kurul oylamasına girmez, md. 14/1); olağanüstü genel kurul
    Denetleme Kuruluna seçim yapmaz (kullanıcı kararı S10)."""
    yazma_kapisi()
    _baslangic(SECIM_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, *_ADAY_KAYDI_ACIK)
    if organ not in SECIM_ORGANLARI.values():
        raise ValueError(ADAY_ORGANI)
    if guncel.kind == AssemblyKind.OLAGANUSTU and organ == OrganType.DENETLEME_KURULU:
        raise ValueError(OLAGANUSTU_DK_SECIMI_YOK)
    return uyelikler.assign_membership(
        term=secim_donemi(guncel),
        person=person,
        organ=organ,
        seat_type=seat_type,
        seat_group=seat_group,
        elected_by=ElectedBy.GENEL_KURUL,
        assembly=guncel,
        gerekce=gerekce,
    )


def _aday_kayitlari(
    kurul: GeneralAssembly, organ: str, adaylar: Sequence[AdayOyu], katilan: int
) -> list[tuple[OrganMembership, AdayOyu]]:
    """Seçimin aday kayıtları: her biri bu genel kurulun bu kuruldaki `ADAY` kaydıdır (S6 (i), sert —
    hesap bütünlüğü); oy katılımı aşamaz; yedek sırası yalnız seçilen yedekte."""
    kimlikler = [aday.uyelik.pk for aday in adaylar]
    if len(set(kimlikler)) != len(kimlikler):
        raise ValueError(ADAY_TEKRAR)
    kayitlar: list[tuple[OrganMembership, AdayOyu]] = []
    for aday in adaylar:
        uyelik = uyelikler.guncel_kayit(aday.uyelik)
        if (
            uyelik.assembly_id != kurul.pk
            or uyelik.organ != organ
            or uyelik.status != MembershipStatus.ADAY
        ):
            raise ValueError(SECILEN_ADAYDAN)
        oy = _secimli_sayi(aday.votes)
        if oy is not None and oy > katilan:
            raise ValueError(OY_KATILANDAN_COK)
        if aday.seat_order is not None:
            if not aday.secildi or uyelik.seat_type != SeatType.YEDEK:
                raise ValueError(YEDEK_SIRASI_YALNIZ_SECILEN_YEDEKTE)
            if _sayi(aday.seat_order) < 1:
                raise ValueError(YEDEK_SIRASI_GECERSIZ)
        kayitlar.append((uyelik, aday))
    return kayitlar


def _yedek_siralari(
    kayitlar: Sequence[tuple[OrganMembership, AdayOyu]],
) -> tuple[dict[int, int], bool]:
    """Seçilen yedeklerin sırası (U26; md. 13/6 "aldıkları oy sırasına göre"): oydan hesaplanır, eşit
    oyda program sıra hesaplamaz (sıra boş kalır, elle girilir); elle girilen sıra hesaplananın yerine
    geçer. Sıralar birbirinden farklıdır (hesap bütünlüğü). İkinci değer: eşit oylu ya da oysuz yedek
    sırasız kaldı mı?"""
    yedekler = [(u, a) for u, a in kayitlar if a.secildi and u.seat_type == SeatType.YEDEK]
    oylar = [(u, a.votes) for u, a in yedekler if a.votes is not None]
    siralar: dict[int, int] = {}
    sira = 1
    for oy in sorted({o for _, o in oylar}, reverse=True):
        grup = [u for u, o in oylar if o == oy]
        if len(grup) == 1:
            siralar[grup[0].pk] = sira
        sira += len(grup)
    siralar.update({u.pk: a.seat_order for u, a in yedekler if a.seat_order is not None})
    if len(set(siralar.values())) != len(siralar):
        raise ValueError(YEDEK_SIRASI_TEKRAR)
    return siralar, any(u.pk not in siralar for u, _ in yedekler)


def _secim_bicimi_denetimi(
    tur: _Tur, madde: AgendaItem, liste: bool | None, acik_oy: bool | None
) -> None:
    """md. 10/1-d "asıl ve yedek olarak liste hâlinde oylanarak", 11/1-a, b "açık oylamayla"
    (`genel_kurul.secim_bicimi`, uyarı): gözlenen seçimin yapılış biçimidir; girilmediyse eksik
    (tamamlanacak: `secim_bicimini_yaz` ile tutanak tamamlanana dek girilir, girilince eksik kapanır;
    tutanak tamamlanırken hâlâ eksikse gerekçe ister). Konu seçim maddesidir. Gözlenen değer ayrı
    alanda saklanmaz: sapma ya da eksik uyum satırıdır, satır yoksa seçim liste hâlinde ve açık oyla
    yapılmıştır (plan F2 6. adım kararı)."""
    gozlenen: Any = (
        VERI_YOK
        if liste is None or acik_oy is None
        else [belirtec for belirtec, var in ((SECIM_LISTE, liste), (SECIM_ACIK_OY, acik_oy)) if var]
    )
    sonuc = uyum.denetle("genel_kurul.secim_bicimi", gozlenen, konu=madde, **tur.ortak())
    tur.kaydet("genel_kurul.secim_bicimi", sonuc, kurulun=False)


def _olaganustu_eski_yk_dusur(kurul: GeneralAssembly, gun: date) -> list[OrganMembership]:
    """U27 (md. 13/8 "olağanüstü genel kurul tarafından seçilen yönetim kurulu"): görevdeki eski yönetim
    kurulu üyelikleri (asıl ve yedek, md. 7/2'de ertelenen dahil) seçilenlerin kaydından önce aynı
    işlemde `DUSTU (OLAGANUSTU_GK_SECIMI)` olur; bağlı hesaplar askıya alınır, başkanın temsilci
    satırları kapanır (`uyelik_gecisleri.uyeligi_dusur`). Denetleme Kurulu kolu yoktur (S10)."""
    eskiler = (
        OrganMembership.objects.filter(
            term_id=kurul.term_id,
            organ=OrganType.YONETIM_KURULU,
            status=MembershipStatus.SECILDI,
        )
        .exclude(assembly=kurul)
        .order_by("pk")
    )
    return [
        uyelik_gecisleri.uyeligi_dusur(
            uyelik, drop_kind=DropKind.OLAGANUSTU_GK_SECIMI, end_date=gun
        )
        for uyelik in eskiler
    ]


def _bilinmeyen_beyani_bagla(secilen: OrganMembership, gun: date) -> None:
    """U26: seçilen yönetim kurulu üyesinin programdan önceki seçilme sayısı geçiş kurulumunda
    "bilinmiyor" diye beyan edildiyse sayacın eksik satırı geçişin toplu gerekçesine bağlanır
    (`gecis.sayac_kok_nedeni`; gerekçe yeniden sorulmaz). Beyan hiç verilmediyse eksik kalır."""
    if secilen.organ != OrganType.YONETIM_KURULU or secilen.person.external_yk_terms is not None:
        return
    gecis_donemi = gecis.gecis_donemi()
    if gecis_donemi is None:
        return
    kok = gecis.sayac_kok_nedeni(gecis_donemi)
    beyan_edildi = ComplianceItem.objects.filter(
        subject_type=denetim_izi.model_etiketi(OabPerson),
        subject_id=denetim_izi.kimlik_metni(OabPerson, secilen.person_id),
        rule_id=_YK_SAYAC_KURALI,
        kind=ComplianceKind.SAPMA,
        justification_group__root_cause=kok,
    ).exists()
    eksik = ComplianceItem.objects.filter(
        subject_type=denetim_izi.model_etiketi(OrganMembership),
        subject_id=denetim_izi.kimlik_metni(OrganMembership, secilen.pk),
        rule_id=_YK_SAYAC_KURALI,
        kind=ComplianceKind.EKSIK,
        resolved_at__isnull=True,
    ).exists()
    if not (beyan_edildi and eksik):
        return
    uyum.bilinmeyen_beyan_sapmasi(
        _YK_SAYAC_KURALI,
        donem=secilen.term,
        konu=secilen,
        mesaj=gecis.BILINMIYOR_MESAJI["external_yk_terms"],
        gerekce=uyum.Gerekce(kok_neden=kok),
        tarih=gun,
        hazirlik_yazimi=True,
    )


@transaction.atomic
def secim_sonucu_yaz(
    madde: AgendaItem,
    *,
    adaylar: Sequence[AdayOyu],
    liste: bool | None = None,
    acik_oy: bool | None = None,
    result_text: str = "",
    gerekce: uyum.Gerekce | None = None,
) -> SecimSonucu:
    """Seçim maddesinin sonucu (md. 10/1-d, 11/1-a, b; U26). Sonuç `karar_sonucu_yaz`'dan girilmez.

    Seçilen, aynı genel kurulun aday kaydının kendisidir (S6 (i), sert — hesap bütünlüğü): her aday
    `ADAY` → `SECILDI` olur (`uyelikler.elect_membership`; seçilme günü genel kurulun yapıldığı gün,
    U6). Koltuk uygunluğu, tek koltuk, iki kurul ve müdür engeli yeniden, seçilme sınırı yalnız
    yönetim kurulunda (md. 12/4) denetlenir; Denetleme Kurulunun başkanlık sayacı (md. 14/3) seçimde
    koşmaz, görev bölümündedir. Oy aday başınadır; seçilmeyen adayın oyu da yazılır, kaydı aday kalır.
    Yedek sırası oydan hesaplanır, eşit oyda elle girilir (`_yedek_siralari`). Seçimin biçimi (liste
    hâlinde, açık oy) `genel_kurul.secim_bicimi` ile denetlenir (uyarı + gerekçe; girilmediyse eksik,
    `secim_bicimini_yaz` ile sonradan girilir).

    Olağanüstü genel kurulda yönetim kurulu seçilince görevdeki eski üyelikler önce düşer (U27);
    Denetleme Kuruluna seçim yapılmaz (S10). Madde "görüşüldü" olur; sonucu bir kez girilir, yanlış
    girilen sonuç `secimi_iptal_et` ile iptal edilip yeniden girilir."""
    yazma_kapisi()
    _baslangic(SECIM_ROLLERI)
    guncel_madde, kurul = _madde_ve_kurul(madde)
    _durum(kurul, AssemblyStatus.YAPILDI)
    organ = SECIM_ORGANLARI.get(str(guncel_madde.kind))
    if organ is None:
        raise ValueError(SECIM_MADDESI_DEGIL)
    if guncel_madde.removed_by_vote:
        raise ValueError(MADDE_CIKARILMIS)
    if guncel_madde.result:
        raise ValueError(SECIM_SONUCU_GIRILDI)
    if kurul.kind == AssemblyKind.OLAGANUSTU and organ == OrganType.DENETLEME_KURULU:
        raise ValueError(OLAGANUSTU_DK_SECIMI_YOK)
    gun = genel_kurul_gunu(kurul)
    kayitlar = _aday_kayitlari(kurul, organ, adaylar, _toplanti_katilani(kurul))
    siralar, sirasiz = _yedek_siralari(kayitlar)
    tur = _Tur(kurul, gerekce)
    _secim_bicimi_denetimi(tur, guncel_madde, liste, acik_oy)
    secilecekler = sorted(
        ((u, a) for u, a in kayitlar if a.secildi),
        key=lambda kayit: (kayit[0].seat_type != SeatType.ASIL, kayit[0].pk),
    )
    dusenler: list[OrganMembership] = []
    if secilecekler and kurul.kind == AssemblyKind.OLAGANUSTU:
        dusenler = _olaganustu_eski_yk_dusur(kurul, gun)
    secilenler: list[OrganMembership] = []
    uyarilar = list(tur.uyarilar)
    for uyelik, aday in secilecekler:
        secilen = uyelikler.elect_membership(
            uyelik,
            start_date=gun,
            votes=aday.votes,
            seat_order=siralar.get(uyelik.pk),
            gerekce=gerekce,
        )
        _bilinmeyen_beyani_bagla(secilen, gun)
        secilenler.append(secilen)
        uyarilar.extend(s for s in (secilen.rule_warnings or []) if s.get("durum") == "uyari")
    for uyelik, aday in kayitlar:
        if not aday.secildi and aday.votes is not None:
            uyelikler.update_membership(uyelik, votes=aday.votes)
    onceki = denetim_izi.anlik(guncel_madde)
    guncel_madde.result = AgendaResult.GORUSULDU
    guncel_madde.result_text = result_text.strip()
    guncel_madde.updated_by_id = iz.yazar_hesabi()
    guncel_madde.save(update_fields=["result", "result_text", "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel_madde, onceki=onceki)
    return SecimSonucu(
        madde=guncel_madde,
        secilenler=tuple(secilenler),
        dusenler=tuple(dusenler),
        uyarilar=tuple(uyarilar),
        bilgiler=(ESIT_OYLU_YEDEK_BILGISI,) if sirasiz else (),
    )


@transaction.atomic
def secim_bicimini_yaz(
    madde: AgendaItem,
    *,
    liste: bool,
    acik_oy: bool,
    gerekce: uyum.Gerekce | None = None,
) -> SecimSonucu:
    """Seçimin biçimini (liste hâlinde, açık oy) sonucu girilmiş seçim maddesine sonradan girer ya da
    düzeltir (tamamlanacaklar; tutanak tamamlanana dek; `ilan_kanitlarini_yaz` emsali, tasarım O3).
    `genel_kurul.secim_bicimi` yeniden denetlenir: liste hâlinde ve açık oyla yapılan seçimde eksik
    satırı (ya da önceki sapma) kapanır; sapma uyarı + gerekçedir, gerekçesiz ret hiçbir şey yazmaz.
    Seçilenler değişmez."""
    yazma_kapisi()
    _baslangic(SECIM_ROLLERI)
    guncel_madde, kurul = _madde_ve_kurul(madde)
    _durum(kurul, AssemblyStatus.YAPILDI)
    if str(guncel_madde.kind) not in SECIM_ORGANLARI:
        raise ValueError(SECIM_MADDESI_DEGIL)
    if guncel_madde.removed_by_vote:
        raise ValueError(MADDE_CIKARILMIS)
    if not guncel_madde.result:
        raise ValueError(SECIM_SONUCU_YOK)
    if not isinstance(liste, bool) or not isinstance(acik_oy, bool):
        raise ValueError(SECIM_BICIMI_GECERSIZ)
    tur = _Tur(kurul, gerekce)
    _secim_bicimi_denetimi(tur, guncel_madde, liste, acik_oy)
    return SecimSonucu(madde=guncel_madde, uyarilar=tuple(tur.uyarilar))


GENEL_KURUL_ADAYI_IPTALI: Final = (
    "Seçimin sonucu girildikten sonra genel kurulun aday kaydı iptal edilmez; yanlış girilen sonuç "
    "Genel Kurul'da seçimin iptaliyle düzeltilir (tek kaynak; hesap bütünlüğü)."
)


def aday_iptali_denetimi(uyelik: OrganMembership) -> None:
    """F1c'nin genel üyelik iptalinde genel kurulun aday kaydı (plan F2 §10.2, en dar seçenek;
    `uyelik_gecisleri.uyeligi_iptal_et` çağırır, işlemi odur): adayı kaydeden roller (§7.1 "Kim",
    `SECIM_ROLLERI`), aday kaydının açık olduğu durumlarda (`_ADAY_KAYDI_ACIK`) ve o kurulun seçim
    sonucu girilmeden iptal eder. Sonuç girildiyse seçilmeyen adayın oyu da sonucun parçasıdır: önce
    seçimin iptali (`secimi_iptal_et`). Yazmaz."""
    if uyelik.assembly_id is None:
        return  # genel kurula bağlı olmayan kayıt bu denetimin konusu değildir
    _daralt(SECIM_ROLLERI)
    kurul = GeneralAssembly.objects.get(pk=uyelik.assembly_id)
    _durum(kurul, *_ADAY_KAYDI_ACIK)
    turler = [tur for tur, organ in SECIM_ORGANLARI.items() if organ == uyelik.organ]
    if AgendaItem.objects.filter(assembly=kurul, kind__in=turler).exclude(result="").exists():
        raise ValueError(GENEL_KURUL_ADAYI_IPTALI)


@transaction.atomic
def secimi_iptal_et(madde: AgendaItem, *, cancel_reason: str) -> list[OrganMembership]:
    """Yanlış girilen seçim sonucunu düzeltir (divanın düzeltilmesi emsali, `divani_iptal_et`; en dar
    yol): bu genel kurulun bu kurula seçilmiş kayıtları gerekçeyle `IPTAL` olur (altın kural 4;
    `uyelik_gecisleri.uyeligi_iptal_et`, gerekçe zorunlu ve şifreli), iptal edilen kayıtların açık
    eksik satırları kapanır (`uyum.iptalde_eksikleri_kapat`), maddenin sonucu boşalır (izli). Seçilmemiş
    adaylar aday kalır; seçilmiş kaydı iptal edilen kişi yeniden aday kaydedilir, sonuç
    `secim_sonucu_yaz` ile yeniden girilir. Olağanüstü seçimde düşen eski yönetim kurulu üyelikleri
    (U27) bu iptalle geri gelmez. Yalnız tutanak tamamlanmadan."""
    yazma_kapisi()
    _baslangic(SECIM_ROLLERI)
    metin = cancel_reason.strip()
    if not metin:
        raise ValueError(uyelik_gecisleri.IPTAL_GEREKCESI_GEREKLI)
    guncel_madde, kurul = _madde_ve_kurul(madde)
    _durum(kurul, AssemblyStatus.YAPILDI)
    organ = SECIM_ORGANLARI.get(str(guncel_madde.kind))
    if organ is None:
        raise ValueError(SECIM_MADDESI_DEGIL)
    if not guncel_madde.result:
        raise ValueError(SECIM_SONUCU_YOK)
    secilenler = OrganMembership.objects.filter(
        assembly=kurul, organ=organ, status=MembershipStatus.SECILDI
    ).order_by("pk")
    iptaller = [
        uyelik_gecisleri.uyeligi_iptal_et(uyelik, cancel_reason=metin, genel_kurul_yolu=True)
        for uyelik in secilenler
    ]
    if iptaller:
        uyum.iptalde_eksikleri_kapat(secim_donemi(kurul), iptaller, hazirlik_yazimi=True)
    onceki = denetim_izi.anlik(guncel_madde)
    guncel_madde.result = ""
    guncel_madde.result_text = ""
    guncel_madde.updated_by_id = iz.yazar_hesabi()
    guncel_madde.save(update_fields=["result", "result_text", "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel_madde, onceki=onceki)
    return iptaller


# ---------------------------------------------------------------------------
# 6. adım: ibra ve "ibra edilmedi" yan akışı (md. 11/1-c, ç; plan F2 §9 S4)
# ---------------------------------------------------------------------------
IBRA_MADDESI_DEGIL = "Bu gündem maddesi ibra maddesi değil."
IBRA_SONUCU_GECERSIZ = "İbra sonucu ibra edildi, ibra edilmedi ya da görüşülmedi olmalıdır."
IBRA_OYLARI_GEREKLI = (
    "İbra genel kurulun kararıdır, sonucu oylardan hesaplanır: ibra edildi ya da edilmedi sonucu kabul "
    "ve ret oylarıyla girilir; oylanmayan ibra görüşülmedi diye kaydedilir (md. 11/1-c, 9/2)."
)
IBRA_GORUSULMEDI_OYSUZ = "Görüşülmedi sonucunda ibra oyu girilmez."
EVRAK_NOTU_YALNIZ_IBRA_EDILMEDIGINDE = (
    "İbra edilmeyen muhasebe evrakı yalnız yönetim kurulunun hesapları ibra edilmediğinde yazılır "
    "(md. 11/1-ç)."
)
IBRA_EDILMEDI_BILGISI: Final = (
    "Hesaplar ibra edilmedi: diğer gündem maddeleri görüşülür; divan ibra edilmeyen muhasebe "
    "evrakını tutanak altına alarak yönetim kuruluna ve Denetleme Kuruluna teslim eder "
    "(md. 11/1-ç). Tutanak tamamlanınca il/ilçe millî eğitim müdürlüğüne bildirim takvime girer."
)
#: İl/ilçe millî eğitim müdürlüğüne bildirimin takvim satırı (md. 11/1-ç: "yeni yönetim kurulu ve okul
#: yönetimi tarafından"). Yönetim kurulunu seçmeyen (seçimsiz) olağanüstü genel kurulda yeni yönetim
#: kurulu yoktur: bildirimi görevdeki yönetim kurulu yapar (`secilen_kurullar`; teslim alan kurullarla
#: aynı kaynak, `genel_kurul_evraki.TESLIM_ALANLAR`; 10. adımın 11. adıma bıraktığı düzeltme).
IBRA_BILDIRIMI_MESAJLARI: Final[Mapping[bool, str]] = {
    True: (
        "Hesaplar ibra edilmedi: yeni yönetim kurulu ve okul yönetimi il/ilçe millî eğitim "
        "müdürlüğüne resmî yazıyla bildirir (md. 11/1-ç)."
    ),
    False: (
        "Hesaplar ibra edilmedi: görevdeki yönetim kurulu ve okul yönetimi il/ilçe millî eğitim "
        "müdürlüğüne resmî yazıyla bildirir (md. 11/1-ç)."
    ),
}
#: Yönetim kurulunu seçen genel kurulun bildirimi (geriye dönük ad).
IBRA_BILDIRIMI_MESAJI: Final = IBRA_BILDIRIMI_MESAJLARI[True]


def gundem_turleri(kurul: GeneralAssembly) -> set[str]:
    """Gündemde kalan maddelerin türleri (oylamayla çıkarılan madde sayılmaz; md. 9/4)."""
    return {
        str(tur)
        for tur in AgendaItem.objects.filter(assembly=kurul, removed_by_vote=False).values_list(
            "kind", flat=True
        )
    }


def secilen_kurullar(kurul: GeneralAssembly, turler: set[str] | None = None) -> tuple[bool, bool]:
    """Bu genel kurul yönetim kurulunu ve Denetleme Kurulunu (veli koltuğu) seçer mi: gündemde kalan
    seçim maddesi; olağanüstü genel kurul Denetleme Kuruluna seçim yapmaz (kullanıcı kararı S10 (a)).
    Teslim alan kurulların (md. 11/1-ç; E10, E11, E12) ve il/ilçe millî eğitim müdürlüğüne bildirimin
    (E13, takvim satırı) tek kaynağıdır."""
    kalan = gundem_turleri(kurul) if turler is None else turler
    return (
        AgendaItemKind.SECIM_YK in kalan,
        AgendaItemKind.SECIM_DK in kalan and kurul.kind == AssemblyKind.OLAGAN,
    )


def ibra_bildirimi_mesaji(kurul: GeneralAssembly) -> str:
    """İbra edilmedi bildiriminin takvim satırı, yönetim kurulunun seçilip seçilmediğine göre."""
    return IBRA_BILDIRIMI_MESAJLARI[secilen_kurullar(kurul)[0]]


def _tutanak(kurul: GeneralAssembly) -> AssemblyMinutes:
    """Genel kurulun tutanak kaydı (1:1); yoksa açılır (izli)."""
    tutanak: AssemblyMinutes | None = AssemblyMinutes.objects.filter(assembly=kurul).first()
    if tutanak is not None:
        return tutanak
    hesap = iz.yazar_hesabi()
    yeni = AssemblyMinutes.objects.create(assembly=kurul, created_by_id=hesap, updated_by_id=hesap)
    denetim_izi.degisiklik(yeni, onceki=None)
    return yeni


def _tutanagi_yaz(tutanak: AssemblyMinutes, alanlar: Mapping[str, Any]) -> AssemblyMinutes:
    """Tutanağın değişen alanlarını yazar ve izler; değişen yoksa yazmaz."""
    degisen = [ad for ad, deger in alanlar.items() if getattr(tutanak, ad) != deger]
    if not degisen:
        return tutanak
    onceki = denetim_izi.anlik(tutanak)
    for ad in degisen:
        setattr(tutanak, ad, alanlar[ad])
    tutanak.updated_by_id = iz.yazar_hesabi()
    tutanak.save(update_fields=[*degisen, "updated_at", "updated_by"])
    denetim_izi.degisiklik(tutanak, onceki=onceki)
    return tutanak


@dataclass(frozen=True)
class IbraOylamasi:
    """Bir kurulun ibra oylaması (md. 11/1-c; tasarım §9.6 E10 "YK ve DK ibrası ayrı oylama satırı"):
    kabul ve ret oyu, oylamada salonda bulunan (girilmezse payda toplantının katılımıdır, S2)."""

    votes_for: int
    votes_against: int
    present_count: int | None = None


#: Kurul başına ibra alanları (sonuç, kabul, ret, salondaki).
_IBRA_ALANLARI: Final[Mapping[str, tuple[str, str, str, str]]] = {
    kurul: (
        f"discharge_{kurul}",
        f"discharge_{kurul}_votes_for",
        f"discharge_{kurul}_votes_against",
        f"discharge_{kurul}_present_count",
    )
    for kurul in ("yk", "dk")
}
_IBRA_KURUL_ADI: Final[Mapping[str, str]] = {"yk": "yönetim kurulu", "dk": "Denetleme Kurulu"}


def _ibra_sonucu(
    kurul: GeneralAssembly, oylama: IbraOylamasi | None, verilen: str | None
) -> tuple[str, int | None, int | None, int | None]:
    """Bir kurulun ibra sonucu ve oyları (md. 11/1-c, 9/2; kullanıcı kararı S6 (iii), sert — hesap
    bütünlüğü). Oylama verilmediyse ibra görüşülmemiştir; verildiyse sonuç oylardan hesaplanır
    (`_oylama`): çoğunluk varsa ibra edildi, yoksa edilmedi. `verilen` (tutanağın yazdığı sonuç)
    hesapla karşılaştırılır: oylarla çelişen sonuç kaydedilmez (`KuralSert`)."""
    if verilen is not None and verilen not in Discharge.values:
        raise ValueError(IBRA_SONUCU_GECERSIZ)
    if oylama is None:
        if verilen not in (None, Discharge.GORUSULMEDI):
            raise ValueError(IBRA_OYLARI_GEREKLI)
        return str(Discharge.GORUSULMEDI), None, None, None
    if verilen == Discharge.GORUSULMEDI:
        raise ValueError(IBRA_GORUSULMEDI_OYSUZ)
    sonuc = _oylama(kurul, oylama.votes_for, oylama.votes_against, oylama.present_count)
    hesaplanan = str(Discharge.EDILDI if sonuc.cogunluk else Discharge.EDILMEDI)
    if verilen is not None and verilen != hesaplanan:
        raise KuralSert(detail=f"{KARAR_OYLARLA_CELISIYOR} ({sonuc.atif}).")
    return hesaplanan, sonuc.kabul, sonuc.ret, sonuc.salondaki


@transaction.atomic
def ibra_yaz(
    madde: AgendaItem,
    *,
    yk: IbraOylamasi | None,
    dk: IbraOylamasi | None,
    discharge_yk: str | None = None,
    discharge_dk: str | None = None,
    unaudited_documents_note: str = "",
) -> GenelKurulSonucu:
    """İbra maddesinin sonucu (md. 11/1-c "yönetim ve denetleme kurulu faaliyet raporlarını görüşmek
    ve ibra etmek"): yönetim kurulu ve Denetleme Kurulu ayrı oylanır (`yk`, `dk`; tasarım §9.6 E10
    "ayrı oylama satırı"). İbra genel kurulun kararıdır: sonuç oylardan HESAPLANIR
    (`genel_kurul.karar_cogunlugu`, kullanıcı kararı S6 (iii), sert — hesap bütünlüğü; payda S2). Oylama
    verilmeyen kurulun ibrası görüşülmemiştir. `discharge_yk`, `discharge_dk` verilirse hesapla
    karşılaştırılır; oylarla çelişen sonuç kaydedilmez. Sonuç `karar_sonucu_yaz`'dan girilmez.

    Yönetim kurulunun hesapları ibra edilmezse yan akış açılır (kullanıcı kararı S4 (a)): ibra
    edilmeyen muhasebe evrakının listesi tutanağa yazılır (`AssemblyMinutes.unaudited_documents_note`,
    şifreli) ve tutanak tamamlanınca il/ilçe MEM bildirimi takvime girer; Denetleme Kurulunun ibra
    edilmemesi yalnız tutanağa yazılır. Tutanak tamamlanana dek düzeltilir (izli; her çağrı iki kurulun
    oylamasını birlikte yazar)."""
    yazma_kapisi()
    _baslangic(TUTANAK_ROLLERI)
    guncel_madde, kurul = _madde_ve_kurul(madde)
    _durum(kurul, AssemblyStatus.YAPILDI)
    if guncel_madde.kind != AgendaItemKind.IBRA:
        raise ValueError(IBRA_MADDESI_DEGIL)
    if guncel_madde.removed_by_vote:
        raise ValueError(MADDE_CIKARILMIS)
    sonuclar = {
        "yk": _ibra_sonucu(kurul, yk, discharge_yk),
        "dk": _ibra_sonucu(kurul, dk, discharge_dk),
    }
    yk_sonucu = sonuclar["yk"][0]
    not_metni = unaudited_documents_note.strip()
    if not_metni and yk_sonucu != Discharge.EDILMEDI:
        raise ValueError(EVRAK_NOTU_YALNIZ_IBRA_EDILMEDIGINDE)
    alanlar = {
        ad: deger
        for kurul_adi, degerler in sonuclar.items()
        for ad, deger in zip(_IBRA_ALANLARI[kurul_adi], degerler, strict=True)
    }
    degisen = [ad for ad, deger in alanlar.items() if getattr(kurul, ad) != deger]
    if degisen:
        onceki = denetim_izi.anlik(kurul)
        for ad in degisen:
            setattr(kurul, ad, alanlar[ad])
        _kaydet(kurul, onceki, degisen)
    mevcut = AssemblyMinutes.objects.filter(assembly=kurul).first()
    if not_metni or (mevcut is not None and mevcut.unaudited_documents_note):
        _tutanagi_yaz(_tutanak(kurul), {"unaudited_documents_note": not_metni})
    gorusuldu = {s[0] for s in sonuclar.values()} != {Discharge.GORUSULMEDI}
    sonuc = str(AgendaResult.GORUSULDU) if gorusuldu else ""
    if guncel_madde.result != sonuc:
        onceki_madde = denetim_izi.anlik(guncel_madde)
        guncel_madde.result = sonuc
        guncel_madde.updated_by_id = iz.yazar_hesabi()
        guncel_madde.save(update_fields=["result", "updated_at", "updated_by"])
        denetim_izi.degisiklik(guncel_madde, onceki=onceki_madde)
    bilgiler = (IBRA_EDILMEDI_BILGISI,) if yk_sonucu == Discharge.EDILMEDI else ()
    return GenelKurulSonucu(kurul=_guncel(kurul), bilgiler=bilgiler)


class _Verilmedi(Enum):
    """Kısmi yazımda "alan verilmedi" belirteci (`None` alanı boşaltır)."""

    VERILMEDI = "VERILMEDI"


#: `tutanak_bilgilerini_yaz`'da verilmeyen alan yazılmaz.
VERILMEDI: Final = _Verilmedi.VERILMEDI
TUTANAK_BILGISI_BOS = "Yazılacak tutanak bilgisi verilmedi."
TUTANAK_TAMAM_YALNIZ_TESLIM = (
    "Tutanak tamamlandıktan sonra yalnız yeni yönetim kuruluna teslim günü yazılır; raporları okuyanlar "
    "ve bütçeyi sunan tutanakla birlikte girilir."
)


@transaction.atomic
def tutanak_bilgilerini_yaz(
    kurul: GeneralAssembly,
    *,
    yk_report_reader: OabPerson | None | _Verilmedi = VERILMEDI,
    dk_report_reader: OabPerson | None | _Verilmedi = VERILMEDI,
    budget_presenter: OabPerson | None | _Verilmedi = VERILMEDI,
    handed_to_new_yk_on: date | None | _Verilmedi = VERILMEDI,
) -> AssemblyMinutes:
    """Tutanağın kişi bağları ve teslim günü (tasarım §5.2.3 `AssemblyMinutes`): raporları okuyanlar ve
    tahmini bütçeyi sunan birlik kişisidir (serbest metin ad yok); yeni yönetim kuruluna teslim günü
    md. 10/1-ç (F2'de yalnız tarih, U29). Kısmi yazımdır: yalnız verilen alan yazılır, `None` alanı
    boşaltır. Pasif kişi yeni bağlanamaz; tutanakta zaten bağlı kişi sonradan pasifleşse de bağ
    yeniden verilince korunur (kayıt toplantıdaki durumu yazar). Kişi bağları tutanak tamamlanana dek
    (`YAPILDI`) yazılır; teslim günü tutanak tamamlandıktan sonra da yazılır ve düzeltilir (tasarım §7.1
    `TUTANAK_TAMAM` sonrası "tutanak ve belgeler yeni YK'ye teslim", §7.8 sıra; dönem kilidi
    denetlenir). Divan ve seçilenler üyelik kayıtlarından okunur (tek kaynak, O6)."""
    yazma_kapisi()
    _baslangic(TUTANAK_ROLLERI)
    guncel = _guncel(kurul)
    kisiler = {
        "yk_report_reader": yk_report_reader,
        "dk_report_reader": dk_report_reader,
        "budget_presenter": budget_presenter,
    }
    verilen = {ad: kisi for ad, kisi in kisiler.items() if not isinstance(kisi, _Verilmedi)}
    if verilen and guncel.status == AssemblyStatus.TUTANAK_TAMAM:
        raise ValueError(TUTANAK_TAMAM_YALNIZ_TESLIM)
    _durum(guncel, AssemblyStatus.YAPILDI, AssemblyStatus.TUTANAK_TAMAM)
    mevcut = AssemblyMinutes.objects.filter(assembly=guncel).first()
    alanlar: dict[str, Any] = {}
    for ad, kisi in verilen.items():
        alan = f"{ad}_id"
        if kisi is None:
            alanlar[alan] = None
        elif mevcut is not None and getattr(mevcut, alan) == kisi.pk:
            alanlar[alan] = kisi.pk  # bağ değişmiyor: aktiflik yeni bağda sorulur
        else:
            alanlar[alan] = uyelikler.kisi_aktif(kisi).pk
    if not isinstance(handed_to_new_yk_on, _Verilmedi):
        alanlar["handed_to_new_yk_on"] = handed_to_new_yk_on
    if not alanlar:
        raise ValueError(TUTANAK_BILGISI_BOS)
    return _tutanagi_yaz(_tutanak(guncel), alanlar)


# ---------------------------------------------------------------------------
# 6. adım: yanlış seçilen divanın düzeltilmesi (5. adımın açık bıraktığı nokta)
# ---------------------------------------------------------------------------
DIVAN_YOK = "Bu genel kurulun divanı seçilmedi."


@transaction.atomic
def divani_iptal_et(kurul: GeneralAssembly, *, cancel_reason: str) -> list[OrganMembership]:
    """Yanlış girilen divanı düzeltir (en dar yol): iki kayıt da gerekçeyle `IPTAL` olur (altın kural
    4; `uyelik_gecisleri.uyeligi_iptal_et`, gerekçe zorunlu ve şifreli), sonra `divan_sec` yeniden
    yazılır. Yalnız tutanak tamamlanmadan; divan birlikte düzelir (başkan ve kâtip aynı açık oylamanın
    sonucudur, md. 10/1-c)."""
    yazma_kapisi()
    _baslangic(TUTANAK_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, AssemblyStatus.YAPILDI)
    divan = kurulun_divani(guncel)
    if not divan:
        raise ValueError(DIVAN_YOK)
    return [
        uyelik_gecisleri.uyeligi_iptal_et(
            uyelik, cancel_reason=cancel_reason, genel_kurul_yolu=True
        )
        for uyelik in divan
    ]


# ---------------------------------------------------------------------------
# 6. adım: YAPILDI → TUTANAK_TAMAM (tasarım §7.1; plan F2 §5.2, §7 U32)
# ---------------------------------------------------------------------------
TUTANAK_EKSIGI: Final = (
    "Tutanak tamamlanırken hâlâ eksik bilgi var; tamamlanınca bu bilgi girilemez, sapma olarak "
    "gerekçesiyle kayda geçer"
)
DONEM_ONAYI_BEKLIYOR: Final = (
    "Yeni birlik döneminin açılması program yöneticisinin onayını bekliyor (dönemin başlangıcı "
    "genel kurulun yapıldığı gün: {gun:%d.%m.%Y})."
)


def _acik_eksikler(donem: OabTerm, konular: Sequence[Any]) -> list[tuple[Any, ComplianceItem]]:
    """Konuların açık `EKSIK` satırları (konu, satır), konu sırasıyla."""
    eksikler: list[tuple[Any, ComplianceItem]] = []
    for konu in konular:
        satirlar = ComplianceItem.objects.filter(
            term=donem,
            kind=ComplianceKind.EKSIK,
            resolved_at__isnull=True,
            subject_type=denetim_izi.model_etiketi(type(konu)),
            subject_id=denetim_izi.kimlik_metni(type(konu), konu.pk),
        ).order_by("pk")
        eksikler.extend((konu, satir) for satir in satirlar)
    return eksikler


@transaction.atomic
def tutanagi_tamamla(
    kurul: GeneralAssembly, *, gerekce: uyum.Gerekce | None = None
) -> GenelKurulSonucu:
    """Tutanağı tamamlar (`YAPILDI → TUTANAK_TAMAM`; tasarım §7.1 "Kim": sekreter, program yöneticisi).

    Kapatıcı geçiştir (O3): genel kurulun, ilanlarının ve gündem maddelerinin hâlâ açık eksikleri
    (ör. kanıt günü girilmemiş ilan kanalı — `genel_kurul.ilan_kanallari`'nın konusu ilan kaydıdır —,
    girilmemiş seçim biçimi) sapmaya döner ve gerekçe ister (`uyum.kapanis_gecisi`); gerekçesiz ret
    hiçbir şey yazmaz. Yönetim kurulunun hesapları ibra edilmediyse il/ilçe MEM bildirimi takvime
    girer (`ComplianceItem(TAKVIM, IBRA_EDILMEDI_BILDIRIMI)`, md. 11/1-ç; S4 (a)). Dönem değişmez:
    olağan genel kurulda dönem geçişini program yöneticisi ayrıca onaylar (U32;
    `donem_gecisini_onayla`)."""
    yazma_kapisi()
    _baslangic(TUTANAK_ROLLERI)
    guncel = _guncel(kurul)
    _durum(guncel, AssemblyStatus.YAPILDI)
    donem = kural_donemi(guncel)
    konular: list[Any] = [
        guncel,
        *kurulun_duyurulari(guncel),
        *AgendaItem.objects.filter(assembly=guncel).order_by("order"),
    ]
    eksikler = _acik_eksikler(donem, konular)
    if eksikler:
        if gerekce is None or not (gerekce.metin.strip() or gerekce.kok_neden.strip()):
            iletiler = "; ".join(dict.fromkeys(satir.message for _, satir in eksikler))
            raise GerekceGerekli(detail=f"{TUTANAK_EKSIGI}: {iletiler}")
        gun = birinci_toplanti_gunu(guncel)
        for konu in dict.fromkeys(konu for konu, _ in eksikler):
            kurallar = {satir.rule_id for k, satir in eksikler if k is konu}
            uyum.kapanis_gecisi(
                donem,
                gerekceler=dict.fromkeys(kurallar, gerekce),
                tarih=gun,
                konu=konu,
                hazirlik_yazimi=True,
            )
    yapildigi_gun = genel_kurul_gunu(guncel)
    if guncel.discharge_yk == Discharge.EDILMEDI:
        uyum.takvim_satiri_yaz(
            ComplianceObligation.IBRA_EDILMEDI_BILDIRIMI,
            donem=donem,
            due_date=yapildigi_gun,
            mesaj=ibra_bildirimi_mesaji(guncel),
            responsible_role=_YONETICI,
            konu=guncel,
            hazirlik_yazimi=True,
        )
    onceki = denetim_izi.anlik(guncel)
    guncel.status = AssemblyStatus.TUTANAK_TAMAM
    _kaydet(guncel, onceki, ("status",))
    bilgiler: tuple[str, ...] = ()
    if guncel.opens_term_id is not None:
        bilgiler = (DONEM_ONAYI_BEKLIYOR.format(gun=yapildigi_gun),)
    return GenelKurulSonucu(kurul=_guncel(guncel), bilgiler=bilgiler)


# ---------------------------------------------------------------------------
# 6. adım: dönem geçişi önerisi ve onayı (tasarım §5.2.1, §7.1, §7.8; plan F2 §5.2, §7 U4, U32)
# ---------------------------------------------------------------------------
DONEM_ACMAZ = (
    "Bu genel kurul birlik dönemi açmaz; dönem geçişi olağan genel kurulun hazırlık dönemindedir "
    "(md. 13/8)."
)
TUTANAK_TAMAMLANMADI = "Dönem geçişi genel kurulun tutanağı tamamlandıktan sonra onaylanır."
DONEM_HAZIRLIKTA_DEGIL = "Bu genel kurulun açtığı dönem hazırlıkta değil; dönem geçişi onaylandı ya da dönem iptal edildi."
KAPANACAK_ACIK_DEGIL = (
    "Kapanacak birlik dönemi açık değil; dönem geçişi yapılamaz (hesap bütünlüğü)."
)
DONEM_CAKISIYOR = (
    "Yeni birlik döneminin başlangıcı ({gun:%d.%m.%Y}) başka bir dönemin tarih aralığıyla "
    "çakışıyor; birlik dönemlerinin aralıkları çakışmaz (hesap bütünlüğü)."
)
#: Okul idaresinin genel kuruldan sonraki TEFBİS girişleri (tasarım §7.1 `TUTANAK_TAMAM` sonrası,
#: §5.2.7; md. 23/5). Süre kural değildir ("genel kuruldan hemen sonra" yalnız rehberde, RH-001): son
#: gün yeni dönemin başlangıcıdır, yükümlülüğün doğduğu gün (plan F2 6. adım kararı).
TEFBIS_TAKVIMI: Final[tuple[tuple[str, str], ...]] = (
    (
        ComplianceObligation.TEFBIS_YONETIM_BILGISI,
        "Okul idaresi birliğin kayıtlarını TEFBİS'e girer (md. 23/5): genel kuruldan sonra yeni "
        "yönetimin bilgisi girilir.",
    ),
    (
        ComplianceObligation.TEFBIS_BANKA_BILGISI,
        "Okul idaresi birliğin kayıtlarını TEFBİS'e girer (md. 23/5): genel kuruldan sonra banka "
        "hesap bilgileri girilir.",
    ),
    (
        ComplianceObligation.TEFBIS_BUTCE_GIRISI,
        "Okul idaresi birliğin kayıtlarını TEFBİS'e girer (md. 23/5): genel kuruldan sonra tahmini "
        "bütçe girilir.",
    ),
)


@dataclass(frozen=True)
class DonemGecisi:
    """Dönem geçişinin önizlemesi ya da sonucu (kişisiz): açılacak dönem ve başlangıcı, kapanacak
    dönem ve bitişi, geçişi engelleyen hesap bütünlüğü iletileri."""

    kurul: GeneralAssembly
    yeni_donem: OabTerm
    baslangic: date
    kapanacak: OabTerm | None
    kapanacak_bitis: date | None
    engeller: tuple[str, ...] = ()


def _cakisma_var(yeni: OabTerm, kapanacak: OabTerm | None, gun: date) -> bool:
    """Yeni dönemin aralığı [gun, …) başka bir başlamış dönemle çakışır mı? (U4; tasarım §5.2.1
    "dönem aralıkları çakışmaz"). Kapanacak dönem `gun`'den bir önceki gün biter: başlangıcı `gun`'den
    önce olmalıdır. Öteki başlamış dönemler (`KAPANISTA`, `KAPANDI`) `gun`'den önce bitmiş olmalıdır."""
    if kapanacak is not None and (kapanacak.start_date is None or kapanacak.start_date >= gun):
        return True
    haric = [yeni.pk] if kapanacak is None else [yeni.pk, kapanacak.pk]
    digerleri = OabTerm.objects.exclude(status__in=(TermStatus.IPTAL, TermStatus.HAZIRLIK)).exclude(
        pk__in=haric
    )
    return any(d.end_date is None or d.end_date >= gun for d in digerleri)


def donem_gecisi_onizlemesi(kurul: GeneralAssembly) -> DonemGecisi:
    """Dönem geçişinin önerisi (U32; yazmaz, kişisiz): tutanak tamamlanınca sistem geçişi önerir,
    denetimler ve çakışma bu anda görünür. Başlangıç genel kurulun yapıldığı gündür (birinci ya da
    ikinci toplantı, U6); kapanacak dönem bir önceki gün biter."""
    guncel: GeneralAssembly = GeneralAssembly.objects.select_related(
        "term", "opens_term__rule_package"
    ).get(pk=kurul.pk)
    if guncel.kind != AssemblyKind.OLAGAN or guncel.opens_term is None:
        raise ValueError(DONEM_ACMAZ)
    yeni = guncel.opens_term
    kapanacak = guncel.term
    gun = genel_kurul_gunu(guncel)
    engeller: list[str] = []
    if guncel.status != AssemblyStatus.TUTANAK_TAMAM:
        engeller.append(TUTANAK_TAMAMLANMADI)
    if yeni.status != TermStatus.HAZIRLIK:
        engeller.append(DONEM_HAZIRLIKTA_DEGIL)
    elif kapanacak is not None and kapanacak.status != TermStatus.ACIK:
        engeller.append(KAPANACAK_ACIK_DEGIL)
    elif _cakisma_var(yeni, kapanacak, gun):
        engeller.append(DONEM_CAKISIYOR.format(gun=gun))
    return DonemGecisi(
        kurul=guncel,
        yeni_donem=yeni,
        baslangic=gun,
        kapanacak=kapanacak,
        kapanacak_bitis=None if kapanacak is None else gun - timedelta(days=1),
        engeller=tuple(engeller),
    )


@transaction.atomic
def donem_gecisini_onayla(kurul: GeneralAssembly) -> DonemGecisi:
    """Dönem geçişini onaylar (U32; tasarım §7.1, §7.8 "sistem; yonetici onaylar"): yalnız program
    yöneticisi (M1, `Eylem.BIRLIK_DONEMI_YAZMA`). Tek işlemde: kapanacak dönem `ACIK → KAPANISTA`
    (bitiş genel kurulun yapıldığı günden bir önceki gün), hazırlık dönemi `HAZIRLIK → ACIK`
    (başlangıç genel kurulun yapıldığı gün); aralık çakışması sert (hesap bütünlüğü). Kural bağı
    değişmez (U2). Yeni açılan okulun ilk genel kurulunda dönemsiz veli satırları döneme bağlanır.
    Okul idaresinin TEFBİS girişleri yeni dönemin takvimine girer (md. 23/5). Her yazım izlidir, iz
    satırı onaylayan hesabındır. Kapanış (`KAPANISTA → KAPANDI`) F4'tedir."""
    yazma_kapisi()
    app_password.require_password_set()
    _kapi()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.BIRLIK_DONEMI_YAZMA)
    onizleme = donem_gecisi_onizlemesi(kurul)
    if onizleme.engeller:
        raise ValueError(onizleme.engeller[0])
    gun = onizleme.baslangic
    hesap = iz.yazar_hesabi()
    kapanacak: OabTerm | None = None
    if onizleme.kapanacak is not None:
        kapanacak = OabTerm.objects.select_related("rule_package").get(pk=onizleme.kapanacak.pk)
        donem_kilidi.yazma_denetimi(kapanacak)
        onceki = denetim_izi.anlik(kapanacak)
        kapanacak.status = TermStatus.KAPANISTA
        kapanacak.end_date = onizleme.kapanacak_bitis
        kapanacak.updated_by_id = hesap
        kapanacak.save(update_fields=["status", "end_date", "updated_at", "updated_by"])
        denetim_izi.degisiklik(kapanacak, onceki=onceki)
    yeni = OabTerm.objects.select_related("rule_package").get(pk=onizleme.yeni_donem.pk)
    donem_kilidi.yazma_denetimi(yeni, hazirlik_yazimi=True)
    onceki_yeni = denetim_izi.anlik(yeni)
    yeni.status = TermStatus.ACIK
    yeni.start_date = gun
    yeni.updated_by_id = hesap
    yeni.save(update_fields=["status", "start_date", "updated_at", "updated_by"])
    denetim_izi.degisiklik(yeni, onceki=onceki_yeni)
    if kapanacak is None:
        donemler.ilk_donemin_veli_listesini_bagla(yeni)
    for yukumluluk, mesaj in TEFBIS_TAKVIMI:
        uyum.takvim_satiri_yaz(
            yukumluluk,
            donem=yeni,
            due_date=gun,
            mesaj=mesaj,
            responsible_role=_YONETICI,
            konu=onizleme.kurul,
        )
    return DonemGecisi(
        kurul=onizleme.kurul,
        yeni_donem=yeni,
        baslangic=gun,
        kapanacak=kapanacak,
        kapanacak_bitis=onizleme.kapanacak_bitis,
    )
