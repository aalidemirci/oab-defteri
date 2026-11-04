"""Hesap servisleri — açma, kapama, parola sıfırlama, askıdan çıkarma, iki depo karşılaştırması.

Tasarım §4.4.1, §4.4.5, §4.6.1; plan F1b-1 ("Hesap açma, kapama, parola sıfırlama
ve askıdan çıkarma servisleri 1. adımdadır; uçları, Kullanıcılar ekranı ve hesap
teslim pusulası 2. adımda"). Dosya ayağı (`guvenlik.json` sarmalları ve arşivler)
`app_password`'tedir; burası veritabanı ayağını ve iki deponun SIRASINI yönetir.

**İşlemi yapan ve rolü** (`_actor`, `_yonetici_aktor`): işlemi yapan hesap (`by_hesap_id`)
açık (`ACIK`), mührü tutan ve isteğin yazarıyla aynı hesap olmalıdır; yazar yoksa ya da
`SISTEM` ise ret (hesap işlemi kullanıcı eylemidir). Hesap yönetimi — açma, kapama, parola
sıfırlama, askıdan çıkarma, sahipsiz sarmalın silinmesi — yalnız program yöneticisinindir
(tasarım §4.4.2 Kullanıcılar satırı): rol kapısının (`RolMiddleware`) ardından servis de
mühürlü satırın rolüyle yetki kapısına sorar (`rol_izinleri.Eylem.HESAP_YONETIMI`; derin
savunma, ret 403 `rol_yetkisiz`). Parola yenilenme bildiriminin kapatılması her rolde açıktır
(sahibinin kendi bildirimi). Geri yükleme kartının "Gördüm"ü yalnız Denetleme Kurulunundur
(`acknowledge_restore`; `Eylem.GERI_YUKLEME_GORDUM`, M8 ⁵). Her servis kilit açıkken çalışır (DEK
bellekte; mühür ve şifreli ad onu ister).

SIRALAR (iki depo kuralı, §4.6.1):

* **Açma:** sarmal önce bellekte kurulur; önce veritabanı (`PAROLA_YENILENMELI`, sarmalın
  özeti, mühür), sonra sarmal (geçici parolayla). Tek aşamalıdır: yeni kimliğin önceki
  sarmalı yoktur (`app_password` modül başlığı "İKİ AŞAMALI ÖZET"). Arada kesilirse satır
  sarmalsız kalır; giriş zaten açılmaz, program yöneticisi yeniden geçici parola verir
  (`reset_password` sarmalı yeniden kurar).
* **Kapama:** önce veritabanı (`KAPALI`, `closed_at`, mühür), sonra sarmal
  `guvenlik.json`'dan ve bütün arşivlerden silinir (TK11). Arada kesilirse kilit
  açılışındaki temizlik siler (`app_password._cleanup_closed_wraps`).
* **Parola sıfırlama:** önce veritabanı (`PAROLA_YENILENMELI`, yenilenme izi, bekleyen
  özet), sonra sarmal (asıl özetle aynı işlemde; iki aşamalı özet). Ters sırada kesinti,
  program yöneticisinin bildiği geçici parolayı zorunlu değişim OLMADAN geçerli bırakırdı.
  Başarılı sıfırlamadan sonra hesabın eski sarmalı (arşivdeki dahil) programda açılmaz:
  sıfırlama, ele geçmiş bir parolayı ve özeti tutmayan sarmalı
  (`TwoStoreDifferences.digest_mismatch`) da geçersiz kılar — yalnız `guvenlik.json`'a
  yazabilen birine karşı. Satırı eski bir kopyadan geri sarılmış hesabı sıfırlama aklamaz:
  satırın izi tutmaz, sıfırlama reddedilir. Kalan hâller `app_password` modül başlığı "KALAN
  RİSKLER"dedir.
* **Askıdan çıkarma:** `Account.status = ASKIDA` ise satır, sonra dosyadaki hatalı
  deneme sayacı ve askısı (iki kaynak; plan F1b-1 "Oturum").

Dosya adımı yarıda kalırsa (ör. dosyayı başka bir program tutuyor) veritabanı adımı yerinde kalır
ve hata `GuvenlikDosyasiYazilamadi`'dır (`OSError`; uçta 400 `validation_error`; orkestratör
maddeleri F-7 ve (d0)-1): ileti neyin yapılıp neyin yapılmadığını ve çıkışı söyler —
`OPEN_WRAP_MESSAGE`, `CLOSE_WRAP_MESSAGE`, `RESET_WRAP_MESSAGE`, `UNSUSPEND_WRAP_MESSAGE` ya da
`UNSUSPEND_NOTHING_MESSAGE`, sahipsiz parola kaydının silinmesinde `ORPHAN_WRAP_MESSAGE`.

ZAMAN SÜTUNU BOZUK SATIR (orkestratör maddesi (d0)-2): satırlar `app_password.hesap_satiri` ve
`hesap_satirlari`'yla okunur; program dışından yazılmış geçersiz bir an okumayı düşürmez, o satır
kaydı değiştirilmiş sayılır (mühür ya da satırın izi tutmaz; `seal_mismatch`, Kullanıcılar'da
`kayit_tutuyor: false`). Kullanıcıya giden anlar çevrilemezse None'dır (`_yerel`).

Mührü ya da son iz kaydı tutmayan satıra hiçbir servis dokunmaz; her üç kolun reddi kendi
işleminde bir `BUTUNLUK` satırı yazar (`SISTEM`; orkestratör maddesi F-1: mühür kolu da —
`_muhur_reddi`, `AccountSealMismatch`, alan `seal`; izi tutmayan satırda alt sınıfı
`AccountRecordStale`, alan `kayit_mac`; izdeki boşlukta `AuditTrailGap`, alan `iz_boslugu`, ileti
`_GAP_MESSAGE`; C-4): yeniden
mühürlemek program dışından değiştirilmiş satırı meşrulaştırırdı (tehdit 19); eski bir kopyadan
geri konmuş satırı (mührü tutar, son iz kaydını tutmaz; kullanıcı kararı 03.11.2026 "Girişte
reddet") sıfırlamak, kapatmak, askıdan çıkarmak ya da iki depo karşılaştırmasında parola yenilemeye
çekmek onu yeni bir iz satırıyla AKLARDI. Kural hem işlemi yapana (`_actor`) hem işlem görene
(`_target`; sahipsiz parola kaydının silinmesinde kapalı hesabın satırı da, `_kaydi_butun`)
uygulanır; iki depo karşılaştırması bu satırları `seal_mismatch`'e koyar. Satırın
izi denetlenirken arada meşru bir yazım satırı değiştirdiyse (çift tıklanan işlem) yanlış alarm
yazılmaz, karar doğrulanmış GÜNCEL satırdan verilir (`app_password.satir_izini_denetle`): işlemi
yapan ve işlem gören o satırla yeniden sınanır (işlemi yapan açık değilse işlemi yapan iletisi,
işlem gören kapanmışsa kapalı hesap iletisi; kapalı hesap yeniden açılmaz). Reddedilen
hesabın çıkışı yedekten geri yüklemedir (zarfın üçüncü durumu): tek hesaplı roldeki (ör. muhasip)
satır KAPALI olmadığı için o role yeni hesap da açılamaz.

DENETİM İZİ (tasarım §4.6.2; plan F1b-1 alt commit c). Her satır yazımı iz satırıyla AYNI
işlemdedir (`apps.okul.denetim_izi`): açma, kapama ve askıdan çıkarma `HESAP`, parola
sıfırlama `PAROLA`, parola yenilenme bildiriminin kapatılması `GUNCELLE`, geri yükleme kartının
"Gördüm"ü `ISARET` (kaydı denetim izinin kendi satırı; hesap satırı değişmez). Yazar istek
başındaki bağlamdır (oturumdaki hesap); `by_hesap_id` işlemi yapan hesabın açık ve mühürlü
olduğunu doğrulamak içindir ve yazarla AYNI hesap olmalıdır (`_actor`): satırın hesabı
yazardan, `opened_by`/`closed_by`/`reset_by` `by_hesap_id`'den gelir; ikisi ayrışırsa
servis reddeder (Kullanıcılar uçlarının güvenlik ağı). İki depo sırası korunur:
satır ve iz satırı birlikte, sonra dosya. Dosyadaki sayacı ve askıyı ya da sarmalı
değiştiren adımlar (askıdan çıkarma, parola sıfırlamanın ve kapamanın dosya adımı,
sahipsiz sarmalın silinmesi) `guvenlik.json` bölümünün (`denetim_izi.HESAP_SARMALI`)
`HESAP` satırını önceki değerleriyle yazar (`app_password.sarmal_izi`; sayaç ve askı
sıfırsa sıfırlama ve kapamada satır yok); satır dosyadan ÖNCE, aynı işlemde eklenir
(`app_password.dosya_ve_iz_islemi`). Geri yüklemeden sonraki karşılaştırmanın durum
düzeltmesi programın kendi işidir: yazar `SISTEM`'dir.

KİLİT EKRANI LİSTESİ (`lock_screen_accounts`; tasarım §4.4.3, plan F1b-1 "Oturum"):
kilitliyken çalışır, DEK istemez ve kişi adı döndürmez (şifreli ad-soyad okunmaz).
Kurtarma anahtarıyla açılışın hesap listesi (`recovery_accounts`) aynı kurallarla
veritabanından çıkar: sarmalı olmayan program yöneticisi de görünür (TK10 geri yüklemesi).

KISITLAR (sert; sistem bütünlüğü, altın kural 3): açık hesaplar arasında tanıtıcı
tekil ve tek hesaplı roller (DB kısıtı; burada Türkçe iletiyle önce denetlenir),
Denetleme Kurulu en çok üç, en az bir açık program yöneticisi (son yönetici
kapatılamaz). Tanıtıcının ad-soyadı içermesi uyarıdır, engel değildir
(`hesap_kurallari.login_name_warning`; çağıran gösterir). Rolün sınırında yeri tutan bütün
hesapların kaydı ya da izi tutmuyorsa ayrı neden verilir (`_rol_acilamama_nedeni`; orkestratör
maddesi C-1). Program yöneticisinde sınır yoktur: ikinci program yöneticisi açılır (plan F1b-2;
değişimdeki anahtar yenilemesi F4'te, `IKINCI_YONETICI_BILGISI`).

KENDİ HESABI (plan F1b-2 "Kendi hesabı ve ikinci program yöneticisi"): oturumdaki hesap kendi
hesabını kapatamaz, kendi parolasını buradan sıfırlayamaz (kendi parolası Ayarlar → Güvenlik'te
eski parolayla değiştirilir), kendi teslim pusulasını basamaz. Program yöneticisi değişiminin
istisnası F4'te DEK yenilemesiyle gelir.

HESAP TESLİM PUSULASI (E63; `teslim_pusulasi`, içerik `services.hesap_teslim_pusulasi`; plan F1b-2
"E63 hesap teslim pusulası"): yalnız program yöneticisi (`_yonetici_aktor`), kendi hesabına,
kapalı hesaba ve kaydı ya da izi tutmayan hesaba basılmaz (`_target`: mühür, satır izi, iz boşluğu;
kapama ve sıfırlamayla aynı sıra ve iletiler). Dosya SAKLANMAZ: PDF bellekte çizilir, çağırana
döner; tek izi `BASIM` satırıdır (`denetim_izi.basim`: kod ve PDF'in sha256'sı; kaydın kimliği
hesap). İz yazılamazsa PDF verilmez. Erişim günlüğüne girmez: pusula kişisel veri basmaz (ad-soyad
yok; tasarım §4.6.4'ün türlerinden değildir).

KULLANICILAR EKRANININ VERİSİ (`kullanici_listesi`, `kullanici_ayrintisi`, `kullanici_satiri`,
`kullanici_secenekleri`; uçları `views_hesaplar`): yalnız program yöneticisi (yetki kapısı
`Eylem.HESAP_YONETIMI`, okumada da: hesap sahibinin adı kişisel veridir). Satırların eylemleri ve
yapılamama nedenleri burada, servislerin kurallarıyla ve iletileriyle hesaplanır; ön yüz yalnız
eşler. Kayıt durumu (mühür, satır izi, iz boşluğu) giriş ve servislerle aynı tek karardan
(`denetim_izi.hesap_izi_karari`) gelir; okuma hiçbir şey yazmaz.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, NoReturn

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.okul import denetim_izi, iz_dogrulama
from apps.okul.models import (
    MAX_AUDIT_BOARD_ACCOUNTS,
    SINGLE_ACCOUNT_ROLES,
    Account,
    AccountRole,
    AccountStatus,
    AuditAction,
    AuditTrail,
    ResetKind,
    SchoolConfig,
    SuspendReason,
)
from apps.okul.oturum import ham_an_sutunlari, hesap_ani, rol_etiketi, sistem_olarak, yazar
from apps.okul.rol_izinleri import Eylem, yetki, yetki_oturum
from apps.okul.services import app_password, hesap_kurallari, hesap_teslim_pusulasi
from apps.okul.services.app_password import AccountSealMismatch, AppPasswordError
from shared import crypto, evrak
from shared.exceptions import RolYetkisiz

logger = logging.getLogger("oab_defteri.guvenlik")

_LOCKED_MESSAGE = "Kayıtlar kilitli. Önce hesabınızla kilidi açın."
_ACTOR_MESSAGE = "İşlemi yapan hesap açık değil. Kilitleyip hesabınızla yeniden açın."
_NOT_FOUND_MESSAGE = "Hesap bulunamadı."
_CLOSED_MESSAGE = "Hesap kapalı; kapalı hesap yeniden açılmaz, yeni hesap açılır."
#: Kaydı tutmayan hesabın iletisi oturumdaki parola doğrulamasınınkiyle tek kaynaktır.
_SEAL_MESSAGE = app_password.ISLEMDE_KAYIT_MESSAGE
#: İzde boşluk (`app_password.AuditTrailGap`; orkestratör maddesi C-4): mühür iletisinin kalıbı,
#: değişen hesap kaydı değil denetim izidir.
_GAP_MESSAGE = app_password.ISLEMDE_BOSLUK_MESSAGE
#: Kendi hesabı (plan F1b-2 "Kendi hesabı ve ikinci program yöneticisi"): oturumdaki hesap kendi
#: hesabını kapatamaz, kendi parolasını Kullanıcılar'dan sıfırlayamaz.
_OWN_CLOSE_MESSAGE = "Kendi hesabınızı kapatamazsınız."
_OWN_RESET_MESSAGE = (  # noqa: S105 — kullanıcı iletisidir, parola değil
    "Kendi parolanızı buradan sıfırlayamazsınız; Ayarlar → Güvenlik'teki “Parolayı değiştir” "
    "penceresini kullanın."
)
#: Kendi hesabının teslim pusulası basılmaz (plan F1b-2 "Kendi hesabı": "kendi pusulasını basamaz").
_OWN_SLIP_MESSAGE = "Kendi hesabınızın teslim pusulasını basamazsınız."
_LOGIN_NAME_TAKEN_MESSAGE = "Bu tanıtıcı açık bir başka hesapta kullanılıyor."
_SINGLE_ROLE_MESSAGE = "Bu rolde açık bir hesap zaten var; önce onu kapatın."
_AUDIT_BOARD_LIMIT_MESSAGE = (
    f"Denetleme Kurulu için en çok {MAX_AUDIT_BOARD_ACCOUNTS} hesap açık olabilir."
)
_LAST_ADMIN_MESSAGE = "Son program yöneticisi hesabı kapatılamaz."
_ROLE_MESSAGE = "Geçerli bir rol seçin."
_SUSPENDED_RESET_MESSAGE = "Askıdaki hesabın parolası sıfırlanamaz; önce hesabı askıdan çıkarın."  # noqa: S105
# Genel Bakış'ın "Hesaplar ve Güvenlik Dosyası" kartında görünür: "sarmal" kullanıcı metnine
# girmez, kullanıcıdaki adı hesabın güvenlik dosyasındaki parola kaydıdır (sözlük §1 "Denetim izi").
_NOT_ORPHAN_MESSAGE = (
    "Bu parola kaydı artık güvenlik dosyasından silinebilecek durumda değil; Genel Bakış'ı "
    "yenileyip yeniden deneyin."
)


#: Kapamanın dosya adımı yarıda kaldı (orkestratör maddesi F-7): hesap KAPALI'dır (satır ve `HESAP`
#: satırı commit edildi), parola kaydı güvenlik dosyasında ya da eski kopyalarında kaldı; kilit
#: açılışındaki temizlik siler (`app_password._cleanup_closed_wraps`). Genel Bakış kartının
#: cümlesiyle aynı söz (sözlük §4.5 "Hesaplar ve Güvenlik Dosyası").
CLOSE_WRAP_MESSAGE = (
    "Hesap kapatıldı, ancak parola kaydının güvenlik dosyasından silinmesi tamamlanamadı "
    "(ör. dosyayı başka bir program tutuyor); program bir sonraki kilit açılışında yineler."
)
#: Sahipsiz parola kaydının silinmesinde güvenlik dosyası yazılamadı: hiçbir şey değişmedi (iz
#: satırları geri alındı; orkestratör maddesi F-7).
ORPHAN_WRAP_MESSAGE = (
    "Parola kaydı güvenlik dosyasından silinemedi (ör. dosyayı başka bir program tutuyor); "
    "hiçbir şey değişmedi. Biraz sonra yeniden deneyin."
)
#: Hesap açmanın dosya adımı yarıda kaldı (orkestratör maddesi (d0)-1; iki depo kuralı 2): satır ve
#: `HESAP` satırı commit edildi, hesap açıktır (`PAROLA_YENILENMELI`) ama parola kaydı güvenlik
#: dosyasına girmedi; giriş açılmaz, çıkış program yöneticisinin parola sıfırlamasıdır
#: (`reset_password` parola kaydını yeniden kurar; Kullanıcılar satırının giriş nedeni
#: `_LOGIN_NO_WRAP_MESSAGE`).
OPEN_WRAP_MESSAGE = (
    "Hesap açıldı, ancak parola kaydı güvenlik dosyasına yazılamadı (ör. dosyayı başka bir "
    "program tutuyor); hesabın parolasını sıfırlayın."
)
#: Parola sıfırlamanın dosya adımı yarıda kaldı (orkestratör maddesi (d0)-1): 1. işlem (durum
#: `PAROLA_YENILENMELI`, yenilenme izi ve bildirimi, `PAROLA` satırı, bekleyen özet) commit edildi;
#: 2. işlem (asıl özet, sayacın satırı) geri alındı, güvenlik dosyasındaki kayıt değişmedi. Geçici
#: parola geçerli değildir; çıkış sıfırlamayı yinelemektir.
RESET_WRAP_MESSAGE = (
    "Parola kaydı güvenlik dosyasına yazılamadı (ör. dosyayı başka bir program tutuyor); geçici "
    "parola geçerli değil. Hesabın durumu “Parola yenilenmeli”; parolayı yeniden sıfırlayın."
)
#: Askıdan çıkarmanın dosya adımı yarıda kaldı ve veritabanı askısı kaldırılmıştı (orkestratör maddesi
#: (d0)-1): satır ve `HESAP` satırı commit edildi; hatalı deneme sayacı ve askısı dosyada kaldı
#: (sayacın `guvenlik.sarmal` satırı geri alındı). Yinelenen askıdan çıkarma yalnız dosyayı siler.
UNSUSPEND_WRAP_MESSAGE = (
    "Hesabın askısı kaldırıldı, ancak hatalı parola denemelerinin kaydı güvenlik dosyasından "
    "silinemedi (ör. dosyayı başka bir program tutuyor). Hesap hâlâ askıda görünürse askıdan "
    "çıkarmayı yeniden deneyin."
)
#: Askıdan çıkarmada yalnız dosya adımı vardı (veritabanında askı yok) ve yazılamadı: hiçbir şey
#: değişmedi (sayacın `guvenlik.sarmal` satırı geri alındı; `ORPHAN_WRAP_MESSAGE`'ın kalıbı).
UNSUSPEND_NOTHING_MESSAGE = (
    "Hatalı parola denemelerinin kaydı güvenlik dosyasından silinemedi (ör. dosyayı başka bir "
    "program tutuyor); hiçbir şey değişmedi. Biraz sonra yeniden deneyin."
)


class AccountServiceError(AppPasswordError):
    """Hesap servisinin Türkçe reddi (view katmanı 400'e çevirir)."""


class GuvenlikDosyasiYazilamadi(OSError):
    """Hesap servisinin güvenlik dosyası adımı yarıda kaldı (ör. dosyayı başka bir program tutuyor);
    ileti Türkçedir ve neyin yapılıp neyin yapılmadığını söyler (orkestratör maddeleri F-7 ve
    (d0)-1): hesap açma `OPEN_WRAP_MESSAGE`, parola sıfırlama `RESET_WRAP_MESSAGE`, askıdan
    çıkarma `UNSUSPEND_WRAP_MESSAGE` ya da `UNSUSPEND_NOTHING_MESSAGE`; silme alt sınıfıdır
    (`ParolaKaydiSilinemedi`).

    İki depo kuralı 2 değişmez: önce veritabanı, sonra güvenlik dosyası; dosya adımı yarıda kalırsa
    veritabanı adımı yerinde kalır ve ileti bunu söyler. `OSError` alt sınıfıdır: dosya hatası
    olarak kalır (çağıranlar ve testler onu öyle yakalar), kök neden `__cause__`'dadır. Uçta
    `views_oturum.guvenlik_hatalari` servis retlerinin kalıbıyla 400 `validation_error`'a çevirir
    (eskiden 500); ileti iç ayrıntı (yol, işletim sistemi iletisi) ve geçici parola taşımaz.
    Yalnız DOSYA YAZIMININ `OSError`'ı çevrilir: güvenlik dosyası okunamıyorsa ya da bozuksa ret
    `app_password`'ün kendi Türkçe iletisidir (`AppPasswordError`).
    """


class ParolaKaydiSilinemedi(GuvenlikDosyasiYazilamadi):
    """Parola kaydının (sarmalın) güvenlik dosyasından silinmesi yarıda kaldı (orkestratör maddesi
    F-7); ileti Türkçedir ve neyin yapılıp neyin yapılmadığını söyler (`CLOSE_WRAP_MESSAGE`,
    `ORPHAN_WRAP_MESSAGE`).

    `OSError` alt sınıfıdır: dosya hatası olarak kalır (çağıranlar ve testler onu öyle yakalar),
    kök neden `__cause__`'dadır. Uçta `views_oturum.guvenlik_hatalari` servis retlerinin kalıbıyla
    400 `validation_error`'a çevirir (eskiden 500); ileti iç ayrıntı (yol, işletim sistemi iletisi)
    taşımaz.
    """


def _kural(dogrulayici: Callable[[str], str], deger: str) -> str:
    """`hesap_kurallari` doğrulayıcısını çağırır; ihlali bu modülün hata türüne çevirir."""
    try:
        return dogrulayici(deger)
    except hesap_kurallari.AccountRuleError as exc:
        raise AccountServiceError(str(exc)) from exc


def _sarmal_dosyada(hesap_id: object, data_key: bytes, ozet: str) -> bool:
    """Dosya hatasından sonra: verilen özetin parola kaydı güvenlik dosyasında mı? (okunamazsa hayır)

    Hesap açmanın ve parola sıfırlamanın Türkçe iletisi ("parola kaydı yazılamadı", "geçici parola
    geçerli değil") yalnız kayıt dosyaya GİRMEDİYSE doğrudur. Hata yazımdan SONRA geldiyse (kesinti
    testlerinin "süreç öldü" taklidi; gerçekte yazımdan sonra dosya hatası veren adım yoktur) kayıt
    dosyadadır ve bekleyen özetle açar: o zaman hata olduğu gibi yükselir (orkestratör maddesi
    (d0)-1; `close_account`'un "ana dosya yazıldı mı" ayrımının kalıbı).
    """
    try:
        return bool(ozet) and app_password.wrap_digests(data_key).get(str(hesap_id)) == ozet
    except AppPasswordError:
        return False


def _active_data_key() -> bytes:
    """Bellekteki DEK; kilitliyse ret (hesap servisleri kilit açıkken çalışır)."""
    dek = crypto.active_key()
    if dek is None:
        raise AccountServiceError(_LOCKED_MESSAGE)
    return dek


def _muhur_reddi(hesap: Account, data_key: bytes) -> NoReturn:
    """Mührü tutmayan hesabın (işlemi yapan ya da işlem gören) reddi: `BUTUNLUK` satırı ve 409.

    Satır kendi işlemindedir (`app_password._muhur_bozuk_izi`, alan `seal`, yazar `SISTEM`); satırın
    izi ve izdeki boşluk kollarıyla aynı muamele (orkestratör maddesi F-1; eskiden yalnız mühür kolu
    satır yazmıyordu). Çağıran bir veritabanı işleminin içinde değildir (uçlar istek boyu işlem
    açmaz; C-2): ret işlemi geri alınsa da satır kalır. Satıra dokunulmaz.
    """
    logger.warning("Hesap mührü tutmadı; hesap işlemi yapılmadı (%s).", hesap.id)
    app_password._muhur_bozuk_izi(hesap, data_key)
    raise AccountSealMismatch(_SEAL_MESSAGE)


def _actor(by_hesap_id: object, data_key: bytes) -> Account:
    """İşlemi yapan hesap: var, `ACIK`, mührü tutuyor ve yazarla aynı (rol sorulmaz).

    Yazar bağlamı istek başındaki oturum hesabıdır; işlemi yapan o hesap olmalıdır: iz
    satırının hesabı yazardan, kaydın `opened_by`/`closed_by`/`reset_by`'ı bu hesaptan gelir;
    ayrışırlarsa kayıt başkasının adına yazılmış olurdu (modül başlığı). Yazar yoksa ya da
    `SISTEM` ise ret (`RolYetkisiz`): hesap işlemi gün işi ya da sistem işi değildir (plan
    F1b-1 "by_hesap_id yazar bağlamındaki hesaba eşit olmalıdır"). Rolü soran
    `_yonetici_aktor`'dur; parola yenilenme bildiriminin kapatılması her role açık kalır.

    SIRA (kilit açılışınınki, `app_password._open_account_for_login`): önce yalnız varlık ve kimlik
    (satır var, yazarla aynı hesap), sonra mühür ve satırın izi, DURUM EN SON — doğrulanmış
    satırdan. Mührü tutmayan satırın hiçbir değerine güvenilmez: program dışından "açık değil"
    yapılmış durum da mühür reddini (`BUTUNLUK`, alan `seal`) verir, olağan ret iletisini değil
    (orkestratör maddesi F-1'in tutarlılığı; bağımsız denetim bulgusu). Meşru satırda ileti değişmez.
    """
    kim = yazar()
    if kim is None or kim.sistem_mi:
        raise RolYetkisiz
    aktor = app_password.account_by_id(by_hesap_id)
    if aktor is None:
        raise AccountServiceError(_ACTOR_MESSAGE)
    if denetim_izi.kimlik_metni_ya_da_none(Account, kim.hesap_id) != str(aktor.id):
        logger.warning("İşlemi yapan hesap yazar bağlamındaki hesap değil; işlem yapılmadı.")
        raise AccountServiceError(_ACTOR_MESSAGE)
    if not aktor.seal_matches(data_key):
        _muhur_reddi(aktor, data_key)
    # Satırın izi (`app_password` modül başlığı "SATIRIN İZİ"): eski bir kopyadan geri konmuş
    # işlemi yapanın satırı (ör. rolü düşürülmeden önceki hâli) hiçbir hesap işlemi açmaz. Dönen
    # satır kararın satırıdır (arada meşru bir yazımla değiştiyse güncel hâl): durum ondan sorulur.
    aktor = app_password.satir_izini_denetle(
        aktor, data_key, ileti=_SEAL_MESSAGE, bosluk_iletisi=_GAP_MESSAGE
    )
    if aktor.status != AccountStatus.ACIK:
        raise AccountServiceError(_ACTOR_MESSAGE)
    return aktor


def _yonetici_aktor(by_hesap_id: object, data_key: bytes) -> Account:
    """`_actor` + hesap yönetimi yetkisi (yalnız program yöneticisi; modül başlığı).

    Rol mühürlü satırdandır (`aktor.role`; açılışta doğrulanan mühre girer): yazarın rolüyle
    aynıdır, satır program dışından değiştirildiyse mühür zaten tutmaz.
    """
    aktor = _actor(by_hesap_id, data_key)
    yetki(str(aktor.role), Eylem.HESAP_YONETIMI)
    return aktor


def _target(hesap_id: object, data_key: bytes) -> Account:
    """Üzerinde işlem yapılan hesap: var, kapalı değil, mührü ve izi tutuyor (modül başlığı).

    Mührü tutmayan satır (`_muhur_reddi`, `BUTUNLUK` alan `seal`) ve izi tutmayan (eski bir
    kopyadan geri konmuş) satır sıfırlanmaz, kapatılmaz, askıdan çıkarılmaz: işlem satırı yeniden
    mühürleyip yeni bir iz satırı yazardı ve değişikliği ya da geri sarmayı AKLARDI
    (`AccountRecordStale`, `BUTUNLUK` satırı; çıkış yedekten geri yüklemedir).

    SIRA `_actor`'unkidir: varlık, mühür, satırın izi, DURUM EN SON (doğrulanmış satırdan).
    Program dışından KAPALI yapılmış satır olağan "Hesap kapalı…" iletisini değil mühür reddini
    alır (`BUTUNLUK`, alan `seal`); meşru kapalı hesabın mührü tutar, iletisi değişmez.
    """
    hesap = _kaydi_butun(hesap_id, data_key)
    if hesap.status == AccountStatus.KAPALI:
        raise AccountServiceError(_CLOSED_MESSAGE)
    return hesap


def _kaydi_butun(hesap_id: object, data_key: bytes) -> Account:
    """`_target`'ın kayıt yarısı: hesap var, mührü ve izi tutuyor; DURUM SORULMAZ.

    Tutmazsa ret `BUTUNLUK` satırıyla verilir (`_muhur_reddi`, `app_password.satir_izini_denetle`).
    Kapalı hesabın satırını da denetlemesi gereken yol (sahipsiz parola kaydının silinmesi) bunu
    doğrudan çağırır. Dönen satır kararın satırıdır (arada meşru bir yazımla değiştiyse güncel hâl).
    """
    hesap = app_password.account_by_id(hesap_id)
    if hesap is None:
        raise AccountServiceError(_NOT_FOUND_MESSAGE)
    if not hesap.seal_matches(data_key):
        _muhur_reddi(hesap, data_key)
    return app_password.satir_izini_denetle(
        hesap, data_key, ileti=_SEAL_MESSAGE, bosluk_iletisi=_GAP_MESSAGE
    )


def _kendi_hesabi_mi(aktor: Account, hesap_id: object) -> bool:
    """İşlem gören hesap işlemi yapanın (oturumdaki hesabın) kendisi mi? (kimlik kanonik biçimde)"""
    return denetim_izi.kimlik_metni_ya_da_none(Account, hesap_id) == str(aktor.id)


def _needs_password_renewal(hesap: Account) -> bool:
    """Askıdan dönen hesap geçici parolasını henüz değiştirmemişse `PAROLA_YENILENMELI` olur."""
    if hesap.password_changed_at is None:
        return True
    return hesap.reset_at is not None and hesap.password_changed_at < hesap.reset_at


def default_login_name(role: str) -> str:
    """Rolden türeyen, açık hesaplarda kullanılmayan ilk tanıtıcı (tasarım §4.4.4)."""
    alinmis = Account.objects.exclude(status=AccountStatus.KAPALI).values_list(
        "login_name", flat=True
    )
    return hesap_kurallari.default_login_name(role, alinmis)


@sensitive_variables("temp_password", "parola", "dek")
def open_account(
    *, by_hesap_id: object, role: str, tanitici: str, display_name: str, temp_password: str
) -> Account:
    """Yeni hesap açar (`PAROLA_YENILENMELI`); ilk girişte geçici parola değiştirilir.

    Önce veritabanı (mühürlü satır), sonra geçici parolalı sarmal (modül başlığı).
    Kısıt ihlali Türkçe iletiyle reddedilir. Organ bağı (üyelik) F1c'de zorunlu
    olur; bugün hesap rolle açılır (tasarım §4.4.1).

    Sarmal güvenlik dosyasına yazılamazsa (ör. dosyayı başka bir program tutuyor) satır ve `HESAP`
    satırı yerinde kalır (iki depo kuralı 2: hesap açıktır, sarmalsızdır, giriş açılmaz) ve hata
    `GuvenlikDosyasiYazilamadi` olur (ileti `OPEN_WRAP_MESSAGE`: hesap açıldı, parolasını
    sıfırlayın; uçta 400 `validation_error`; orkestratör maddesi (d0)-1).
    """
    dek = _active_data_key()
    aktor = _yonetici_aktor(by_hesap_id, dek)
    if role not in AccountRole.values:
        raise AccountServiceError(_ROLE_MESSAGE)
    login = _kural(hesap_kurallari.validate_login_name, tanitici)
    ad = _kural(hesap_kurallari.validate_display_name, display_name)
    parola = _kural(hesap_kurallari.validate_password, temp_password)
    acik = Account.objects.exclude(status=AccountStatus.KAPALI)
    if acik.filter(login_name=login).exists():
        raise AccountServiceError(_LOGIN_NAME_TAKEN_MESSAGE)
    # Rolün sınırı ve nedeni `accounts/options/` ile AYNI kuraldandır (`_rol_acilamama_nedeni`).
    # Zaman sütunu bozulmuş satır da okunur ve kaydı değiştirilmiş sayılır (`hesap_satirlari`).
    neden = _rol_acilamama_nedeni(role, app_password.hesap_satirlari(acik.filter(role=role)), dek)
    if neden is not None:
        raise AccountServiceError(neden)
    hesap = Account(
        login_name=login,
        role=role,
        display_name=ad,
        status=AccountStatus.PAROLA_YENILENMELI,
        opened_at=timezone.now(),
        opened_by=aktor,
    )
    # Sarmal önce bellekte kurulur, özeti satıra girer (tek aşamalı: yeni kimliğin önceki
    # sarmalı yoktur; `app_password` modül başlığı "İKİ AŞAMALI ÖZET").
    sarmal = app_password.new_account_wrap(dek, hesap_id=hesap.id, tanitici=login, password=parola)
    hesap.wrap_digest = app_password.wrap_digest(dek, sarmal) or ""
    try:
        with transaction.atomic():
            hesap.seal = hesap.compute_seal(dek)
            hesap.save(force_insert=True)
            denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=None)
    except IntegrityError as exc:  # yarış: DB kısıtı son sözü söyler
        raise AccountServiceError(_LOGIN_NAME_TAKEN_MESSAGE) from exc
    try:
        app_password.write_account_wrap(
            data_key=dek, hesap_id=hesap.id, tanitici=login, sarmal=sarmal
        )
    except OSError as exc:
        if _sarmal_dosyada(hesap.id, dek, hesap.wrap_digest):
            raise  # parola kaydı dosyaya girmişti: ileti yanlış olurdu (`_sarmal_dosyada`)
        logger.warning(
            "Hesap açıldı ama parola kaydı güvenlik dosyasına yazılamadı (%s).",
            hesap.login_name,
            exc_info=True,
        )
        raise GuvenlikDosyasiYazilamadi(OPEN_WRAP_MESSAGE) from exc
    logger.info("Hesap açıldı (%s, %s).", hesap.login_name, hesap.role)
    return hesap


def close_account(*, by_hesap_id: object, hesap_id: object) -> Account:
    """Hesabı kapatır; sarmalı `guvenlik.json`'dan ve bütün arşivlerden silinir (TK11).

    Önce veritabanı (`KAPALI`, `closed_at`, kapatan, mühür), sonra dosyalar. Satır
    kalır (denetim izi için; altın kural 4). Son açık program yöneticisi kapatılamaz. Oturumdaki
    hesap kendi hesabını kapatamaz (plan F1b-2 "Kendi hesabı"; program yöneticisi değişiminin
    kendi istisnası F4'te DEK yenilemesiyle gelir): bu yüzden son program yöneticisi kuralı bugün
    servis yolundan erişilmez, derin savunma olarak kalır.

    Sarmalda hatalı deneme sayacı ya da askı varsa silinirken izi düşer: dosya adımının
    işleminde, dosyadan ÖNCE `guvenlik.sarmal` satırı (`app_password.sarmal_izi`; modül
    başlığı). Ana dosya yazılamazsa o satır geri alınır, sarmalı kilit açılışındaki
    temizlik siler (o da iz yazar); sarmal ana dosyadan silinip bir arşiv kopyası
    temizlenemediyse satır kalır. İki hâlde de hesap KAPALI'dır (veritabanı adımı commit
    edilmiştir) ve hata çağırana `ParolaKaydiSilinemedi` olarak döner (`OSError`; ileti
    `CLOSE_WRAP_MESSAGE`, uçta 400 `validation_error`; orkestratör maddesi F-7).
    """
    dek = _active_data_key()
    aktor = _yonetici_aktor(by_hesap_id, dek)
    if _kendi_hesabi_mi(aktor, hesap_id):
        raise AccountServiceError(_OWN_CLOSE_MESSAGE)
    hesap = _target(hesap_id, dek)
    if (
        hesap.role == AccountRole.YONETICI
        and Account.objects.exclude(status=AccountStatus.KAPALI)
        .filter(role=AccountRole.YONETICI)
        .count()
        <= 1
    ):
        raise AccountServiceError(_LAST_ADMIN_MESSAGE)
    with transaction.atomic():
        onceki = denetim_izi.anlik(hesap)
        hesap.status = AccountStatus.KAPALI
        hesap.suspend_reason = ""
        hesap.closed_at = timezone.now()
        hesap.closed_by = aktor
        hesap.seal = hesap.compute_seal(dek)
        hesap.save(update_fields=["status", "suspend_reason", "closed_at", "closed_by", "seal"])
        denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=onceki)
    kimlik = str(hesap.id)
    arsiv_hatasi: OSError | None = None
    try:
        with app_password.dosya_ve_iz_islemi():
            app_password.sarmal_izi(kimlik, silindi=True)
            try:
                app_password.remove_account_wraps({kimlik})
            except OSError as exc:
                if kimlik in app_password.wrap_ids():
                    raise  # ana dosya yazılmadı: sarmalın satırı da geri alınır
                arsiv_hatasi = exc
    except OSError as exc:
        logger.warning(
            "Kapanan hesabın parola kaydı güvenlik dosyasından silinemedi.", exc_info=True
        )
        raise ParolaKaydiSilinemedi(CLOSE_WRAP_MESSAGE) from exc
    if arsiv_hatasi is not None:
        logger.warning(
            "Kapanan hesabın parola kaydı güvenlik dosyasının bazı eski kopyalarından silinemedi.",
            exc_info=arsiv_hatasi,
        )
        raise ParolaKaydiSilinemedi(CLOSE_WRAP_MESSAGE) from arsiv_hatasi
    logger.info("Hesap kapatıldı (%s).", hesap.login_name)
    return hesap


@sensitive_variables("temp_password", "parola", "dek")
def reset_password(*, by_hesap_id: object, hesap_id: object, temp_password: str) -> Account:
    """Hesabın parolasını geçici parolayla sıfırlar (`PAROLA_YENILENMELI`; tehdit 12).

    Önce veritabanı (durum, `reset_at`, `reset_by`, `reset_kind = SIFIRLAMA`,
    `reset_notice_pending`, mühür), sonra sarmal yeni geçici parolayla kurulur;
    hatalı deneme sayacı ve askısı sıfırlanır. Sahibi ilk girişinde parolasını
    değiştirir ve sıfırlama bildirimini görür. `ASKIDA` durumundaki hesap önce
    askıdan çıkarılır. Oturumdaki hesap kendi parolasını buradan sıfırlayamaz (plan F1b-2 "Kendi
    hesabı"): kendi parolası Ayarlar → Güvenlik'te eski parolayla değiştirilir
    (`app_password.change_password`).

    Geçici parola yalnız politika denetiminden geçer (`hesap_kurallari.validate_password`) ve
    sarmala girer; hiçbir yanıta, günlüğe, iz satırına ya da iletiye yazılmaz (plan F1b-2
    "Kullanıcılar uçları"; `sensitive_variables`).

    Sarmalda sayaç ya da askı varsa izi kalkarken düşer: sarmal yazımının işleminde,
    dosyadan ÖNCE `guvenlik.sarmal` satırı (`app_password.sarmal_izi`). İki işlemdir ve iki
    aşamalı özettir (`app_password` modül başlığı "İKİ AŞAMALI ÖZET"): (1) veritabanı satırı,
    `PAROLA` satırı ve bekleyen özet (geçici parolanın sarmalınınki; asıl özet dosyada şu an
    duran sarmalınki, yalnız meşruysa) sarmaldan ÖNCE commit edilir (modül başlığı "Parola
    sıfırlama"); (2) asıl özetin geçici parolanınkine çekilmesi (`HESAP` satırı), sayacın
    satırı ve en sonda sarmal. Sarmal yazılamazsa yalnız ikinci işlem geri alınır: satır
    `PAROLA_YENILENMELI`dir, eski parola yeni parola isteyerek açar, geçici parola açmaz; hata
    `GuvenlikDosyasiYazilamadi` olur (ileti `RESET_WRAP_MESSAGE`, uçta 400 `validation_error`;
    orkestratör maddesi (d0)-1) ve çıkış sıfırlamayı yinelemektir. Başarılı sıfırlamadan
    sonra eski sarmal (arşivdeki dahil) programda açılmaz (kalan hâller `app_password` modül
    başlığı "KALAN RİSKLER"): parola sıfırlaması özeti tutmayan sarmalın da çaresidir
    (`TwoStoreDifferences.digest_mismatch`).
    """
    dek = _active_data_key()
    aktor = _yonetici_aktor(by_hesap_id, dek)
    if _kendi_hesabi_mi(aktor, hesap_id):
        raise AccountServiceError(_OWN_RESET_MESSAGE)
    hesap = _target(hesap_id, dek)
    if hesap.status == AccountStatus.ASKIDA:
        raise AccountServiceError(_SUSPENDED_RESET_MESSAGE)
    parola = _kural(hesap_kurallari.validate_password, temp_password)
    # Geçici parolanın sarmalı önce bellekte kurulur: özeti iki aşamalı yazımın 1. adımında
    # bekleyen özet olur (`app_password` modül başlığı "İKİ AŞAMALI ÖZET").
    sarmal = app_password.new_account_wrap(
        dek, hesap_id=hesap.id, tanitici=hesap.login_name, password=parola
    )
    yeni_ozet = app_password.wrap_digest(dek, sarmal) or ""
    with app_password.dosya_kilidi():
        # (1) Satır, yenilenme izi, `PAROLA` satırı ve bekleyen özet. Asıl özet dosyada şu an
        # duran sarmalınkidir — yalnız meşruysa (kesintide eski parola açılabilir kalır).
        korunan = app_password.kept_wrap_digest(hesap, dek)
        with transaction.atomic():
            onceki = denetim_izi.anlik(hesap)
            hesap.status = AccountStatus.PAROLA_YENILENMELI
            hesap.reset_at = timezone.now()
            hesap.reset_by = aktor
            hesap.reset_kind = ResetKind.SIFIRLAMA
            hesap.reset_notice_pending = True
            ozet_alanlari = app_password.set_wrap_digests(hesap, asil=korunan, bekleyen=yeni_ozet)
            hesap.seal = hesap.compute_seal(dek)
            hesap.save(
                update_fields=[
                    "status",
                    "reset_at",
                    "reset_by",
                    "reset_kind",
                    "reset_notice_pending",
                    *ozet_alanlari,
                    "seal",
                ]
            )
            denetim_izi.kayit(AuditAction.PAROLA, hesap, onceki=onceki)
        # (2) Asıl özet (`HESAP` satırı), sayacın satırı ve en sonda sarmal. Dosya yazılamazsa
        # yalnız bu işlem geri alınır; (1) yerinde kalır ve ileti bunu söyler ((d0)-1).
        try:
            with app_password.dosya_ve_iz_islemi():
                app_password.write_wrap_digests(hesap, dek, asil=yeni_ozet, bekleyen="")
                app_password.sarmal_izi(hesap.id)
                app_password.write_account_wrap(
                    data_key=dek, hesap_id=hesap.id, tanitici=hesap.login_name, sarmal=sarmal
                )
        except OSError as exc:
            if _sarmal_dosyada(hesap.id, dek, yeni_ozet):
                raise  # geçici parolanın kaydı dosyaya girmişti: ileti yanlış olurdu
            logger.warning(
                "Parola sıfırlandı ama parola kaydı güvenlik dosyasına yazılamadı (%s).",
                hesap.login_name,
                exc_info=True,
            )
            raise GuvenlikDosyasiYazilamadi(RESET_WRAP_MESSAGE) from exc
    logger.info("Hesabın parolası sıfırlandı (%s).", hesap.login_name)
    return hesap


def unsuspend(*, by_hesap_id: object, hesap_id: object) -> Account:
    """Hesabı askıdan çıkarır: iki kaynak birlikte (plan F1b-1 "Oturum").

    `Account.status = ASKIDA` ise satır `ACIK`'a (geçici parolası değişmemişse
    `PAROLA_YENILENMELI`'ye) döner, askı nedeni silinir, mühür yenilenir (`HESAP` satırı);
    sonra dosyadaki hatalı deneme sayacı ve askısı kaldırılır (arşivlenmez). Askıda
    olmayan hesapta yalnız sayaç sıfırlanır (fikirdeş).

    Hatalı deneme askısı kilitliyken, DEK yokken dosyaya yazılır; o an iz yazılamaz
    (`app_password` modül başlığı). Askının izi kalkarken düşer (burada, parola
    sıfırlamada ve kapamada da): dosyada sayaç ya da askı varsa `guvenlik.json` bölümünün
    `HESAP` satırı önceki değerleri taşır (`hatali`, `askida`; `app_password.sarmal_izi`);
    dosya yazımından önce ve aynı işlemde yazılır.

    Dosya yazılamazsa (ör. dosyayı başka bir program tutuyor) sayacın satırı geri alınır, dosyadaki
    sayaç ve askı yerinde kalır ve hata `GuvenlikDosyasiYazilamadi` olur (uçta 400
    `validation_error`; orkestratör maddesi (d0)-1): veritabanı askısı kaldırıldıysa (satır ve
    `HESAP` satırı commit edilmiştir) ileti `UNSUSPEND_WRAP_MESSAGE`'dır — yinelemek yalnız dosyayı
    siler —, kaldırılacak veritabanı askısı yoktuysa `UNSUSPEND_NOTHING_MESSAGE` (hiçbir şey
    değişmedi).
    """
    dek = _active_data_key()
    _yonetici_aktor(by_hesap_id, dek)
    hesap = _target(hesap_id, dek)
    veritabani_askisi = hesap.status == AccountStatus.ASKIDA
    if veritabani_askisi:
        with transaction.atomic():
            onceki = denetim_izi.anlik(hesap)
            hesap.status = (
                AccountStatus.PAROLA_YENILENMELI
                if _needs_password_renewal(hesap)
                else AccountStatus.ACIK
            )
            hesap.suspend_reason = ""
            hesap.seal = hesap.compute_seal(dek)
            hesap.save(update_fields=["status", "suspend_reason", "seal"])
            denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=onceki)
    try:
        with app_password.dosya_ve_iz_islemi():
            app_password.sarmal_izi(hesap.id)
            app_password.clear_failed_attempts(hesap.id)
    except OSError as exc:
        logger.warning(
            "Hatalı deneme kaydı güvenlik dosyasından silinemedi (%s).",
            hesap.login_name,
            exc_info=True,
        )
        raise GuvenlikDosyasiYazilamadi(
            UNSUSPEND_WRAP_MESSAGE if veritabani_askisi else UNSUSPEND_NOTHING_MESSAGE
        ) from exc
    logger.info("Hesap askıdan çıkarıldı (%s).", hesap.login_name)
    return hesap


@dataclass(frozen=True)
class TeslimPusulasi:
    """Basılan hesap teslim pusulası: bellekteki PDF ve indirme adı (dosya saklanmaz).

    Ad, kararın verildiği (mührü ve izi doğrulanmış) satırın rolünden kurulur
    (`hesap_teslim_pusulasi.dosya_adi`; orkestratör maddesi F-2): rol etiketi girer, tanıtıcı ve
    ad girmez.
    """

    pdf: bytes
    dosya_adi: str


def teslim_pusulasi(*, by_hesap_id: object, hesap_id: object) -> TeslimPusulasi:
    """Hesap teslim pusulasının (E63) PDF'i; dosya saklanmaz (modül başlığı "HESAP TESLİM PUSULASI").

    Sıra kapamanınkidir: işlemi yapan (açık, mühürlü, izli program yöneticisi; yetki kapısı
    `Eylem.HESAP_YONETIMI`) → kendi hesabı değil → işlem gören (var, kapalı değil, mührü ve izi
    tutuyor; tutmuyorsa 409 `hesap_muhru_tutmadi` ve `BUTUNLUK` satırı — alan mühürde `seal`,
    satırın izinde `kayit_mac`, izdeki boşlukta `iz_boslugu`). İçerik yalnız tanıtıcıdan, rolden,
    açılış tarihinden, okul kartının antedinden ve boşta kilit süresinden kurulur
    (`hesap_teslim_pusulasi.pusula_belgesi`; ad-soyad okunmaz). PDF bellekte çizilir; sonra AYNI
    işlemde hesabın hâlâ kapalı olmadığı sorulur ve `BASIM` satırı (kod ve PDF'in sha256'sı)
    yazılır. Satır yazılamazsa PDF verilmez (iz yazılamazsa yazma yapılmaz; 409 `iz_yazilamadi`).
    Hiçbir dosyaya ve erişim günlüğüne yazmaz. Dönüş PDF ve indirme adıdır (`TeslimPusulasi`).
    """
    dek = _active_data_key()
    aktor = _yonetici_aktor(by_hesap_id, dek)
    if _kendi_hesabi_mi(aktor, hesap_id):
        raise AccountServiceError(_OWN_SLIP_MESSAGE)
    hesap = _target(hesap_id, dek)
    okul = SchoolConfig.load()
    belge = hesap_teslim_pusulasi.pusula_belgesi(
        tanitici=hesap.login_name,
        rol=hesap.role,
        acilis=hesap.opened_at,
        okul_adi=okul.school_name,
        ilce=okul.district,
        bosta_dakika=okul.idle_lock_minutes,
    )
    pdf = evrak.pdf_ciz(belge)
    with transaction.atomic():
        # Çizim sürerken hesap kapatıldıysa basılmaz (kapalı hesaba pusula yok).
        if not Account.objects.filter(pk=hesap.pk).exclude(status=AccountStatus.KAPALI).exists():
            raise AccountServiceError(_CLOSED_MESSAGE)
        denetim_izi.basim(
            model=denetim_izi.model_etiketi(Account),
            object_id=denetim_izi.kimlik_metni(Account, hesap.pk),
            kod=hesap_teslim_pusulasi.KOD,
            sha256=hashlib.sha256(pdf).hexdigest(),
        )
    logger.info("Hesap teslim pusulası basıldı (%s).", hesap.login_name)
    return TeslimPusulasi(pdf=pdf, dosya_adi=hesap_teslim_pusulasi.dosya_adi(hesap.role))


def acknowledge_reset_notice(*, hesap_id: object) -> Account:
    """Parola yenilenme bildirimini kapatır: sahibi "Gördüm" dedi (tasarım §4.4.3, tehdit 12).

    Yalnız oturumdaki hesabın KENDİ bildirimi kapanır (çağıran yazar bağlamındaki hesabı verir:
    `views_oturum._yazar_hesabi()`; istek ortasındaki kilit ya da hesap değişimi kararı
    değiştirmez — orkestratör maddesi C-5; `_actor` onu yazarla yeniden karşılaştırır);
    hesap açık ve mührü tutuyor olmalıdır (`_actor`; mührü tutmayan satıra dokunulmaz). Her
    rolde açıktır: rol sorulmaz (sahibinin kendi bildirimi; tasarım §4.4.3, tehdit 12).
    `reset_notice_pending` mühre girmez: mühür yenilenmez. Satır ve `GUNCELLE` iz satırı
    (`reset_notice_pending: [true, false]`) aynı işlemdedir; yazar istek başındaki bağlamdır
    (oturumdaki hesap). Bildirim beklemiyorsa hiçbir şey yazılmaz (fikirdeş; iz satırı yok).
    `reset_at` ve `reset_kind` kalır: sıfırlamanın ne zaman yapıldığı kayıtta durur.
    """
    dek = _active_data_key()
    hesap = _actor(hesap_id, dek)
    if not hesap.reset_notice_pending:
        return hesap
    with transaction.atomic():
        onceki = denetim_izi.anlik(hesap)
        hesap.reset_notice_pending = False
        hesap.save(update_fields=["reset_notice_pending"])
        denetim_izi.kayit(AuditAction.GUNCELLE, hesap, onceki=onceki)
    logger.info("Parola yenilenme bildirimi görüldü (%s).", hesap.login_name)
    return hesap


#: "Gördüm"ün `seq`'i son geri yüklemenin satırı değil (eski ya da olmayan; sözlük §1 "Geri yükleme
#: kartının “Gördüm”ü (F1b)").
RESTORE_CARD_STALE_MESSAGE = (
    "Bu geri yükleme kartı artık güncel değil; Genel Bakış'ı yenileyip yeniden deneyin."
)


class RestoreCardStale(Exception):
    """Geri yükleme kartının "Gördüm"ü eski ya da olmayan bir geri yüklemeyi andı → 409.

    `ValueError` DEĞİLDİR: görünümün servis hata sarmalayıcısı onu 400'e çevirmesin
    (`views_oturum.GeriYuklemeGordumView`).
    """

    def __init__(self) -> None:
        super().__init__(RESTORE_CARD_STALE_MESSAGE)


def acknowledge_restore(*, by_hesap_id: object, seq: int) -> AuditTrail | None:
    """Geri yükleme kartının "Gördüm"ü (plan F1b-2 "Gördüm."; tasarım §4.4.4, §4.4.2 M8 ⁵).

    Yalnız Denetleme Kurulu: rol istek başındaki yazardan ve işlemi yapanın mühürlü satırından iki
    kez sorulur (`Eylem.GERI_YUKLEME_GORDUM`; derin savunma). İşlemi yapan açık ve yazarla aynı
    hesaptır (`_actor`; yazar yoksa 403, işlemi yapan açık değilse ya da yazarla aynı değilse 400),
    mührü ve izi tutar (tutmazsa 409 `hesap_muhru_tutmadi`; mühürde, satır izinde ve izdeki
    boşlukta `BUTUNLUK` satırı kendi işleminde yazılır ve kalır — orkestratör maddesi F-1). Sonra TEK
    `IMMEDIATE` işlemde: `seq` doğrulanan son `GERI_YUKLEME` satırı
    değilse `RestoreCardStale` (409; eski bir geri yükleme ya da olmayan kayıt); o geri yüklemeye
    bir Denetleme Kurulu üyesi zaten "Gördüm" dediyse hiçbir şey yazılmaz (None); değilse `ISARET`
    satırı yazılır (model denetim izinin kendisi, kimlik geri yüklemenin `seq`'i; değer yok) ve
    döner. Kart o satırla herkes için kalkar (`iz_dogrulama` modül başlığı "GÖRDÜM"). Kayıt ve dosya
    değişmez.
    """
    yetki_oturum(Eylem.GERI_YUKLEME_GORDUM)
    dek = _active_data_key()
    aktor = _actor(by_hesap_id, dek)
    yetki(str(aktor.role), Eylem.GERI_YUKLEME_GORDUM)
    with transaction.atomic():
        gecerli = denetim_izi.acik_satir_dogrulayici()
        son = iz_dogrulama.son_geri_yukleme(gecerli)
        if son is None or isinstance(seq, bool) or son.seq != seq:
            raise RestoreCardStale
        if iz_dogrulama.geri_yukleme_goruldu_mu(son, gecerli):
            return None
        satir = denetim_izi.olay(
            AuditAction.ISARET,
            model=iz_dogrulama.IZ_SATIRI_MODELI,
            object_id=str(son.seq),
        )
    logger.info("Geri yükleme kartı görüldü (%s, kayıt %d).", aktor.login_name, son.seq)
    return satir


# ---------------------------------------------------------------------------
# İki depo karşılaştırması (§4.6.1 kural 4: geri yüklemeden sonraki ilk kilit açılışı)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TwoStoreDifferences:
    """`guvenlik.json` ile `Account` tablosunun farkı (kimlik listeleri, sıralı).

    * `rows_without_wrap`: açık (`KAPALI` olmayan) ama sarmalı olmayan hesaplar;
      `ACIK` olanlar karşılaştırmada `PAROLA_YENILENMELI`'ye çekilir.
    * `wraps_without_row`: satırı olmayan sarmallar;
    * `wraps_of_closed`: satırı `KAPALI` (mührü ve izi tutan) sarmallar;
    * `seal_mismatch`: mührü ya da izi (denetim izindeki son içerik MAC'li kaydı; `app_password`
      modül başlığı "SATIRIN İZİ") tutmayan satırlar — hiçbir işleme konu olmaz. İki hâl tek
      listededir (kartın listesi "Kaydı ya da denetim izi program dışından değiştirilmiş görünen
      hesaplar"dır: değişen hesap kaydı da olabilir denetim izi de); ayrımı `BUTUNLUK` satırının
      alan adı taşır (`seal`, `kayit_mac`, `iz_boslugu`);
    * `digest_mismatch`: mührü tutan, açık (`KAPALI` olmayan) ve sarmalı dosyada duran ama
      sarmalının özeti satırın asıl ya da bekleyen özetini tutmayan hesaplar (eski ya da program
      dışından konmuş parola kaydı; özeti boş satır dahil; `app_password` modül başlığı
      "SARMALIN TAZELİĞİ"). Bu hesaplar parolayla açılmaz; çaresi program yöneticisinin parola
      sıfırlamasıdır (`reset_password` özeti yeniden yazar), program yöneticisinin kendi
      hesabıysa kurtarma anahtarıyla açılış ya da başka bir program yöneticisinin sıfırlaması.

    `wraps_without_row` yalnız program yöneticisinin onayıyla silinir (`remove_orphan_wraps`).
    `wraps_of_closed`'ı ise program her kilit açılışında kendisi siler (`app_password.
    _cleanup_closed_wraps`; §4.6.1 kural 3'ün "kapalı hesabın sarmalı duruyor" denetimi):
    listede yalnız o silme tamamlanamadıysa (ör. dosyayı başka bir program tuttu) görünür ve
    onayla hemen de silinebilir. Tasarımın kural 4'ü geri yüklemeden sonra bunu da onaya
    bağlıyordu; kural 3'ün kendiliğinden temizliği her açılışta koştuğu için iki kural
    örtüşür, uygulama kural 3'ü izler (Genel Bakış kartının metni bunu söyler).
    """

    rows_without_wrap: list[str] = field(default_factory=list)
    wraps_without_row: list[str] = field(default_factory=list)
    wraps_of_closed: list[str] = field(default_factory=list)
    seal_mismatch: list[str] = field(default_factory=list)
    digest_mismatch: list[str] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not (
            self.rows_without_wrap
            or self.wraps_without_row
            or self.wraps_of_closed
            or self.seal_mismatch
            or self.digest_mismatch
        )

    @property
    def removable_wraps(self) -> list[str]:
        """Onayla silinebilecek sarmallar (satırsız + kapalı)."""
        return sorted({*self.wraps_without_row, *self.wraps_of_closed})


def two_store_differences(
    *, sarmali_yazilacak: frozenset[str] = frozenset()
) -> TwoStoreDifferences:
    """İki deponun farkını hesaplar; HİÇBİR ŞEY yazmaz (kilit açık olmalı: mühür DEK ister).

    `sarmali_yazilacak`: sarmalı çağıranın işleminin sonunda yazılacak hesaplar
    (`reconcile_two_stores`); sarmallı sayılır, özetleri de o işlemde yazılır (karşılaştırılmaz).
    Sarmalın özeti dosyadaki İLK sarmalınkidir (kilit açılışı da ilkini dener).

    Satırlar ve izleri TEK anlık görüntüde okunur (`atomic`; çağıran bir işlemdeyse kayıt noktası)
    ve her satırın izi okunan mührüne bağlıdır (`beklenen_muhur`; `satir_izi` modül başlığı adım
    5): kartlar işlem dışında çağırır, arada commit edilen meşru bir yazım satırı geçici olarak
    "kaydı ya da denetim izi program dışından değiştirilmiş görünen hesaplar"a düşürmesin.
    """
    dek = _active_data_key()
    ozetler = app_password.wrap_digests(dek)
    sarmallar = set(ozetler) | set(sarmali_yazilacak)
    sarmalsiz: list[str] = []
    satirsiz: list[str] = []
    kapali: list[str] = []
    muhursuz: list[str] = []
    ozeti_tutmayan: list[str] = []
    with transaction.atomic():
        # Zaman sütunu bozuk satır da okunur; mührü ya da izi tutmaz (`hesap_satirlari`).
        satirlar = {
            str(hesap.id): hesap for hesap in app_password.hesap_satirlari(Account.objects.all())
        }
        for hesap_id, hesap in satirlar.items():
            if not hesap.seal_matches(dek) or not denetim_izi.hesap_izi_tutuyor(
                hesap.id, veri_anahtari=dek, beklenen_muhur=hesap.seal
            ):
                # Mührü ya da izi tutmayan satır hiçbir listeye ve işleme girmez (modül başlığı).
                muhursuz.append(hesap_id)
                continue
            if hesap.status == AccountStatus.KAPALI:
                if hesap_id in sarmallar:
                    kapali.append(hesap_id)
            elif hesap_id not in sarmallar:
                sarmalsiz.append(hesap_id)
            elif hesap_id not in sarmali_yazilacak and not app_password.digest_matches(
                hesap, ozetler[hesap_id]
            ):
                ozeti_tutmayan.append(hesap_id)
    for hesap_id in sarmallar:
        if hesap_id not in satirlar:
            satirsiz.append(hesap_id)
    return TwoStoreDifferences(
        rows_without_wrap=sorted(sarmalsiz),
        wraps_without_row=sorted(satirsiz),
        wraps_of_closed=sorted(kapali),
        seal_mismatch=sorted(muhursuz),
        digest_mismatch=sorted(ozeti_tutmayan),
    )


def reconcile_two_stores(*, sarmali_yazilacak: frozenset[str] = frozenset()) -> TwoStoreDifferences:
    """Farkı hesaplar ve sarmalı olmayan `ACIK` hesapları `PAROLA_YENILENMELI` yapar.

    Geri yüklemeden sonraki ilk kilit açılışında, geri yükleme notu işlenirken koşar
    (`iz_dogrulama.yaz`, kilit açılışının işleminde). Kurtarma anahtarıyla açılışta
    açılan hesabın sarmalı aynı işlemin SONUNDA yazılır (`sarmali_yazilacak`): o hesap
    sarmallı sayılır, yeni parolasıyla açtığı oturumda parola yenilemeye çekilmez.
    Sarmalı olmayan hesabın sahibi giremez; program yöneticisi geçici parola verir
    (`reset_password` sarmalı kurar). Sarmal silmez: o, listenin Genel Bakış'ta gösterilip
    onaylanmasıyla `remove_orphan_wraps`'tadır (`POST security/integrity/orphan-wraps/`).
    Durum düzeltmesi programın kendi işidir: her hesabın satırı ve `HESAP` satırı tek
    işlemde, yazar `SISTEM` (plan F1b-1 "Denetim izi").
    """
    dek = _active_data_key()
    fark = two_store_differences(sarmali_yazilacak=sarmali_yazilacak)
    for hesap in Account.objects.filter(pk__in=fark.rows_without_wrap, status=AccountStatus.ACIK):
        with sistem_olarak(), transaction.atomic():
            onceki = denetim_izi.anlik(hesap)
            hesap.status = AccountStatus.PAROLA_YENILENMELI
            hesap.seal = hesap.compute_seal(dek)
            hesap.save(update_fields=["status", "seal"])
            denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=onceki)
        logger.info("Sarmalı olmayan hesap parola yenilemeye çekildi (%s).", hesap.login_name)
    return fark


def remove_orphan_wraps(*, by_hesap_id: object, hesap_idler: list[str]) -> list[str]:
    """Program yöneticisinin onayıyla satırsız ya da kapalı hesap sarmallarını siler.

    Yalnız güncel farkta silinebilir görünen kimlikler kabul edilir (onaydan sonra
    durum değiştiyse ret); mührü tutmayan satırın sarmalı asla silinmez. Silme
    `guvenlik.json`'dan ve bütün arşivlerden yapılır. Silinen kimlikleri döndürür.
    Yalnız program yöneticisi (§4.6.1 kural 4; `_yonetici_aktor`).

    Her silinen sarmal için `guvenlik.json` bölümünün `HESAP` satırı dosyadan ÖNCE, aynı
    işlemde yazılır (yazar onaylayan hesap; sarmalda sayaç ya da askı varsa önceki değerleri
    de, `app_password.sarmal_izi`). Ana dosya yazılamazsa işlem geri sarılır, hiçbir şey
    değişmez ve hata `ParolaKaydiSilinemedi` olur (`OSError`; ileti `ORPHAN_WRAP_MESSAGE`, uçta
    400 `validation_error`; orkestratör maddesi F-7); sarmal ana dosyadan silinmiş ama bir arşiv
    kopyası yazılamamışsa iz kalır (sarmal artık kilit açmaz), arşivin uyarısı günlüğe düşer ve
    silme başarılı döner.

    İstenen kimliğin hesap satırı kaydı değiştirilmiş görünüyorsa (farkın `seal_mismatch`'i:
    mührü, izi ya da izdeki boşluk tutmuyor) parola kaydı silinmez ve ret öteki hesap
    işlemlerindeki gibi `BUTUNLUK` satırıyla 409 olur (`_kaydi_butun`; orkestratör maddesi F-1,
    son sınama bulgusu). Satır arada düzelmişse olağan `_NOT_ORPHAN_MESSAGE` döner.
    """
    dek = _active_data_key()
    _yonetici_aktor(by_hesap_id, dek)
    istenen = {str(h) for h in hesap_idler}
    fark = two_store_differences()
    for hesap_id in sorted(istenen & set(fark.seal_mismatch)):
        _kaydi_butun(hesap_id, dek)
    if not istenen <= set(fark.removable_wraps):
        raise AccountServiceError(_NOT_ORPHAN_MESSAGE)
    if istenen:
        try:
            with app_password.dosya_ve_iz_islemi():
                for hesap_id in sorted(istenen):
                    app_password.sarmal_izi(hesap_id, silindi=True, her_zaman=True)
                try:
                    app_password.remove_account_wraps(istenen)
                except OSError:
                    if istenen & set(app_password.wrap_ids()):
                        raise
                    logger.warning(
                        "Sahipsiz sarmallar güvenlik dosyasından silindi; bazı arşiv kopyaları "
                        "temizlenemedi.",
                        exc_info=True,
                    )
        except OSError as exc:
            # Ana dosya yazılamadı: işlem geri sarıldı (iz satırları yok), sarmallar yerinde.
            logger.warning("Sahipsiz sarmallar güvenlik dosyasından silinemedi.", exc_info=True)
            raise ParolaKaydiSilinemedi(ORPHAN_WRAP_MESSAGE) from exc
        logger.info("Sahipsiz hesap sarmalları onayla silindi (%d).", len(istenen))
    return sorted(istenen)


# ---------------------------------------------------------------------------
# Kilit ekranının hesap listesi (tasarım §4.4.3; plan F1b-1 "Oturum")
# ---------------------------------------------------------------------------
#: Hatalı deneme askısının kodu (`guvenlik.json` `askida`); veritabanı askısı
#: `SuspendReason` değerini taşır. Kodlar kullanıcı metnine çıkmaz: ön yüz ikisini de
#: "askıda — program yöneticisine başvurun" diye yazar (sözlük "Hesap").
HATALI_DENEME_ASKISI = "HATALI_DENEME"
#: `ASKIDA` satırında neden boşsa (program dışı yazım) kullanılan kod.
ASKI_NEDENI_BILINMIYOR = "ASKIDA"

#: Birden çok açık hesabı olabilen rollerde etikete sıra no eklenir ("Denetleme Kurulu 2").
_ROL_SIRASI = {rol: sira for sira, rol in enumerate(AccountRole.values)}


def lock_screen_accounts() -> list[dict[str, Any]]:
    """Kilit ekranının hesap listesi; kilitliyken çalışır, DEK İSTEMEZ, kişi adı DÖNDÜRMEZ.

    Liste `guvenlik.json`'daki sarmallardan çıkar (`app_password.account_wraps`); rol,
    durum ve askı nedeni veritabanının düz sütunlarından okunur (şifreli ad-soyad
    sorguya hiç girmez). Her satır `{id, tanitici, rol, rol_etiketi, secilebilir,
    askida_nedeni}`:

    * `KAPALI` satırın sarmalı listelenmez (kapanmış hesap; sarmalı kilit açılışındaki
      temizlik siler);
    * askının iki kaynağı vardır — hatalı deneme askısı (`HATALI_DENEME`) ve
      `Account.status = ASKIDA` (`SuspendReason` değeri); ikisi de seçilemez;
    * rolü veritabanından okunamayan satır (satır yok, kimlik biçimsiz, rol
      tanınmıyor) "Hesap kaydı okunamadı" etiketiyle görünür ve seçilemez (plan
      F1b-1: "rolü veritabanından okunamayan satır açılmaz").

    Sıra: rol sırası (`AccountRole`), sonra açılış zamanı, sonra tanıtıcı; okunamayan
    satırlar sonda. Aynı rolde birden çok hesap varsa etikete açılış sırasıyla sıra no
    eklenir ("Denetleme Kurulu 2"). Mühür burada denetlenmez (DEK yok): mührü tutmayan
    satır kilit açılışında reddedilir (`hesap_muhru_tutmadi`). Durum da DOĞRULANMAMIŞ sütundan
    okunur: program dışından `KAPALI` yapılmış hesap listeden düşer, `ASKIDA` yapılmış hesap
    "askıda" görünür (ikisinde de ret iletisi ve `BUTUNLUK` satırı yoktur; hesap seçilemediği
    için kayıt denetlenmez — sözlük §1 "Hesap kaydının ve denetim izinin tutmaması").

    Açılış anı ORM dönüştürücüsü olmadan, ham metin okunur (`oturum.ham_an_sutunlari`,
    `hesap_ani`; orkestratör maddesi (d0)-2): program dışından yazılmış geçersiz tek bir an
    kilit ekranını — bütün hesapların girişini — düşürmez; okunamayan an rolünün sonuna düşer.
    """
    sarmallar = app_password.account_wraps()
    kimlikler: list[uuid.UUID] = []
    for sarmal in sarmallar:
        try:
            kimlikler.append(uuid.UUID(sarmal["id"]))
        except ValueError:
            continue
    satirlar = {
        str(satir["id"]): satir
        for satir in Account.objects.filter(pk__in=kimlikler)
        .annotate(**ham_an_sutunlari())
        .values("id", "role", "status", "suspend_reason", "ham_acilis", "login_name")
    }
    okunan: list[dict[str, Any]] = []
    okunamayan: list[dict[str, Any]] = []
    for sarmal in sarmallar:
        satir = satirlar.get(sarmal["id"])
        if satir is not None and satir["status"] == AccountStatus.KAPALI:
            continue
        if satir is None or satir["role"] not in _ROL_SIRASI:
            okunamayan.append(
                {
                    "id": sarmal["id"],
                    "tanitici": sarmal["tanitici"],
                    "rol": None,
                    "rol_etiketi": rol_etiketi(None),
                    "secilebilir": False,
                    "askida_nedeni": HATALI_DENEME_ASKISI if sarmal["askida"] else None,
                }
            )
            continue
        neden: str | None = None
        if sarmal["askida"]:
            neden = HATALI_DENEME_ASKISI
        elif satir["status"] == AccountStatus.ASKIDA:
            neden = satir["suspend_reason"] or ASKI_NEDENI_BILINMIYOR
        okunan.append(
            {
                "id": sarmal["id"],
                "tanitici": sarmal["tanitici"],
                "rol": satir["role"],
                "rol_etiketi": rol_etiketi(satir["role"]),
                "secilebilir": neden is None
                and satir["status"] in (AccountStatus.ACIK, AccountStatus.PAROLA_YENILENMELI),
                "askida_nedeni": neden,
                "_acilis": hesap_ani(satir["ham_acilis"]),
            }
        )
    okunan.sort(key=lambda h: (_ROL_SIRASI[h["rol"]], _acilis_sirasi(h["_acilis"]), h["tanitici"]))
    adet: dict[str, int] = {}
    for hesap in okunan:
        adet[hesap["rol"]] = adet.get(hesap["rol"], 0) + 1
    sira: dict[str, int] = {}
    for hesap in okunan:
        del hesap["_acilis"]
        if adet[hesap["rol"]] > 1:
            sira[hesap["rol"]] = sira.get(hesap["rol"], 0) + 1
            hesap["rol_etiketi"] = f"{hesap['rol_etiketi']} {sira[hesap['rol']]}"
    return [*okunan, *okunamayan]


def recovery_accounts() -> list[dict[str, Any]]:
    """Kurtarma anahtarıyla açılabilecek hesaplar; kilitliyken çalışır, DEK İSTEMEZ, kişi adı DÖNDÜRMEZ.

    Tasarım §4.4.3-§4.4.4, TK10: kurtarma anahtarıyla yapılan geri yüklemeden sonra
    (yeni bilgisayara taşıma, güvenlik dosyası kayıp kilidinden çıkış) `guvenlik.json`
    yalnız kurtarma bölümünü taşır; kilit ekranı listesi sarmallardan çıktığı için
    boştur (plan F1b-1 "Oturum"). "Kurtarma anahtarıyla aç + program yöneticisi
    parolası" ekranı hesabı bu listeden seçer (`GET security/recover/`).

    Liste veritabanından çıkar: `KAPALI` olmayan ve kurtarma yolunun kabul ettiği
    durumdaki (`ACIK`, `PAROLA_YENILENMELI`) program yöneticisi satırları; açılış
    sırasıyla. Her satır `{id, tanitici, rol_etiketi, sarmali_var}`; `sarmali_var`
    satırın bu bilgisayarın güvenlik dosyasında sarmalı olup olmadığıdır (yoksa
    kurtarmayla açılış sarmalı yeniden kurar). Yalnız düz sütunlar okunur (şifreli
    ad-soyad sorguya girmez); mühür açılışta denetlenir (`hesap_muhru_tutmadi`).
    """
    sarmallar = {sarmal["id"] for sarmal in app_password.account_wraps()}
    satirlar = (
        Account.objects.filter(
            role=AccountRole.YONETICI,
            status__in=(AccountStatus.ACIK, AccountStatus.PAROLA_YENILENMELI),
        )
        .order_by("opened_at", "login_name")
        .values("id", "login_name")
    )
    return [
        {
            "id": str(satir["id"]),
            "tanitici": satir["login_name"],
            "rol_etiketi": rol_etiketi(AccountRole.YONETICI.value),
            "sarmali_var": str(satir["id"]) in sarmallar,
        }
        for satir in satirlar
    ]


# ---------------------------------------------------------------------------
# Kullanıcılar ekranının verisi (plan F1b-2 "Kullanıcılar uçları"; tasarım §4.4.2, §4.4.5)
# ---------------------------------------------------------------------------
#: Hesap kaydının durumu (`_kayit_durumlari`): None tutuyor demektir.
KAYIT_MUHUR = "muhur"
KAYIT_SATIR_IZI = "satir_izi"
KAYIT_IZ_BOSLUGU = "iz_boslugu"

#: Satırın eylemleri (sunucu hesaplar, ön yüz yalnız eşler; plan F1b-2 "Sözleşme"). `pusula`
#: hesap teslim pusulasıdır (E63; `teslim_pusulasi`, uç `handover-slip/`).
EYLEM_KAPAT = "kapat"
EYLEM_ASKIDAN_CIKAR = "askidan_cikar"
EYLEM_PAROLA_SIFIRLA = "parola_sifirla"
EYLEM_PUSULA = "pusula"

#: Satırın ve eylemlerin kullanıcı metinleri (sözlük §1 "Kullanıcılar (F1b)"). Kodlar kullanıcı
#: metnine çıkmaz; ön yüz bu metinleri yazar.
_ROW_SEAL_MESSAGE = (
    "Hesap kaydı program dışından değiştirilmiş görünüyor; program bu kayda dokunmaz. "
    "Denetleme Kuruluna bildirin."
)
_ROW_GAP_MESSAGE = (
    "Denetim izinden kayıt silinmiş ya da kayıtların sırası program dışından değiştirilmiş "
    "görünüyor; program bu kayda dokunmaz. Denetleme Kuruluna bildirin."
)
_NOT_SUSPENDED_MESSAGE = "Hesap askıda değil."
_LOGIN_CLOSED_MESSAGE = "Hesap kapalı."
_LOGIN_SUSPENDED_MESSAGE = "Hesap askıda; askıdan çıkarılınca giriş açılır."
_LOGIN_NO_WRAP_MESSAGE = (
    "Parola kaydı bu bilgisayarın güvenlik dosyasında yok; parolasını sıfırlayın."  # noqa: S105
)
_LOGIN_DIGEST_MESSAGE = "Parola kaydı hesap kaydındakiyle uyuşmuyor; parolasını sıfırlayın."  # noqa: S105
#: Tek hesaplı rolde (ya da Denetleme Kurulunun sınırında) yerini tutan bütün açık hesapların kaydı
#: ya da izi tutmuyorsa (orkestratör maddesi C-1): o hesaplar kapatılamaz, role yeni hesap açılamaz.
#: Mühür, satır izi ve iz boşluğu TEK nedendir; çıkış yedekten geri yüklemedir (modül başlığı).
_ROLE_RECORD_MESSAGE = (
    "Bu roldeki hesabın kaydı ya da denetim izi program dışından değiştirilmiş görünüyor; o hesap "
    "kapatılamadığı için bu role yeni hesap açılamaz. Denetleme Kuruluna bildirin; kayıtlar sağlam "
    "bir yedekten geri yüklenebilir."
)
#: "Yeni hesap" penceresinin program yöneticisi rolündeki bilgisi (plan F1b-2 "Kendi hesabı ve
#: ikinci program yöneticisi"; tasarım §4.4.5 "MY değişti", TK12 F4'te).
IKINCI_YONETICI_BILGISI = (
    "Program yöneticisi değiştiğinde kayıtların anahtarının yenilenmesi programın sonraki bir "
    "sürümünde gelecek; bu hesap ikinci bir program yöneticisi hesabı olarak açılır."
)
#: Askı nedeninin görünen adı (kod `lock_screen_accounts`'unkiyle aynı; sözlük §1 "Kullanıcılar").
_ASKI_ETIKETLERI: dict[str, str] = {
    HATALI_DENEME_ASKISI: "Hatalı parola denemesi",
    SuspendReason.UYELIK_DUSTU.value: "Üyelik düştü",
    SuspendReason.GOREV_BOLUMU.value: "Görev bölümü",
    ASKI_NEDENI_BILINMIYOR: "Nedeni kayıtlı değil",
}


def _kayit_durumlari(hesaplar: list[Account], dek: bytes) -> dict[str, str | None]:
    """Her hesabın kaydı: mührü ve izi tutuyorsa None, tutmuyorsa nedeni (`KAYIT_*`).

    İz kararı `denetim_izi.hesap_izi_karari`'dır (giriş ve hesap servisleriyle aynı tek işlev;
    retin nedeni `satir_izi` "RET NEDENİ"); okunan mühre bağlıdır (beklenen mühür). Çağıran satırları
    ve bu kararları tek anlık görüntüde (`atomic`) okur. Hiçbir şey yazmaz: ret `BUTUNLUK` satırı
    yalnız bir işlem reddedilince düşer.
    """
    durumlar: dict[str, str | None] = {}
    for hesap in hesaplar:
        kimlik = str(hesap.id)
        if not hesap.seal_matches(dek):
            durumlar[kimlik] = KAYIT_MUHUR
            continue
        karar = denetim_izi.hesap_izi_karari(hesap.id, veri_anahtari=dek, beklenen_muhur=hesap.seal)
        if karar.tutuyor:
            durumlar[kimlik] = None
        elif karar.neden is not None and karar.neden.bosluk_mu:
            durumlar[kimlik] = KAYIT_IZ_BOSLUGU
        else:
            durumlar[kimlik] = KAYIT_SATIR_IZI
    return durumlar


def _rol_acilamama_nedeni(rol: str, acik_hesaplar: list[Account], dek: bytes) -> str | None:
    """Role yeni hesap açılamıyorsa nedeni (kullanıcı metni), açılabiliyorsa None.

    `acik_hesaplar` rolün `KAPALI` olmayan hesaplarıdır. Tek hesaplı rollerde bir, Denetleme
    Kurulunda üç açık hesap sınırdır (tasarım §4.6.1 kısıtları); program yöneticisinde sınır yoktur
    (ikinci program yöneticisi; plan F1b-2). Sınırda, yeri tutan BÜTÜN hesapların kaydı ya da izi
    tutmuyorsa ayrı neden verilir (orkestratör maddesi C-1): onlar kapatılamaz (`_target`), olağan
    "önce onu kapatın" iletisi yol göstermezdi. Hesap açma (`open_account`) ve rol seçenekleri
    (`kullanici_secenekleri`) bu tek kuralı kullanır.
    """
    if rol not in AccountRole.values:
        return _ROLE_MESSAGE
    if rol in SINGLE_ACCOUNT_ROLES:
        sinir, ileti = 1, _SINGLE_ROLE_MESSAGE
    elif rol == AccountRole.DENETLEME_KURULU:
        sinir, ileti = MAX_AUDIT_BOARD_ACCOUNTS, _AUDIT_BOARD_LIMIT_MESSAGE
    else:
        return None
    if len(acik_hesaplar) < sinir:
        return None
    durumlar = _kayit_durumlari(acik_hesaplar, dek)
    if all(durumlar[str(hesap.id)] is not None for hesap in acik_hesaplar):
        return _ROLE_RECORD_MESSAGE
    return ileti


@dataclass(frozen=True)
class _Gorunum:
    """Kullanıcılar satırlarının ortak bağlamı (satırlar ve kayıt durumları tek anlık görüntüden)."""

    oturum_id: str | None
    durumlar: dict[str, str | None]
    dosya_askilari: dict[str, bool]
    ozetler: dict[str, str | None]
    acik_yonetici: int
    hesaplar: dict[str, Account]


def _oturum_hesap_kimligi() -> str | None:
    """İsteğin yazarı olan hesap (istek başındaki görüntü; plan F1b-2 "rolün kaynağı yazar
    bağlamıdır"): istek ortasındaki kilit ya da hesap değişimi "kendi hesabı" kararını değiştirmez."""
    kim = yazar()
    if kim is None or kim.sistem_mi:
        return None
    return denetim_izi.kimlik_metni_ya_da_none(Account, kim.hesap_id)


def _gorunum(dek: bytes) -> _Gorunum:
    """Bütün hesap satırları ve kayıt durumları tek anlık görüntüde; sarmallar dosyadan."""
    try:
        ozetler = app_password.wrap_digests(dek)
    except AppPasswordError:
        ozetler = {}
    dosya_askilari = {
        str(sarmal["id"]): bool(sarmal["askida"]) for sarmal in app_password.account_wraps()
    }
    with transaction.atomic():
        hesaplar = {
            str(hesap.id): hesap for hesap in app_password.hesap_satirlari(Account.objects.all())
        }
        durumlar = _kayit_durumlari(list(hesaplar.values()), dek)
    acik_yonetici = sum(
        1
        for hesap in hesaplar.values()
        if hesap.role == AccountRole.YONETICI and hesap.status != AccountStatus.KAPALI
    )
    return _Gorunum(
        oturum_id=_oturum_hesap_kimligi(),
        durumlar=durumlar,
        dosya_askilari=dosya_askilari,
        ozetler=ozetler,
        acik_yonetici=acik_yonetici,
        hesaplar=hesaplar,
    )


def _yerel(an: Any) -> str | None:
    """Satırın anı Europe/Istanbul'da ISO metin; an yoksa ya da yerel saate çevrilemiyorsa (program
    dışından yazılmış uç değer, ör. 9999'un son saati: OverflowError) None — satır düşmez
    (orkestratör maddesi (d0)-2; `oturum.hesap_gunu`'nun kalıbı)."""
    if an is None:
        return None
    try:
        return str(timezone.localtime(an).isoformat())
    except (OverflowError, ValueError):
        return None


def _durum_etiketi(durum: str) -> str:
    try:
        return str(AccountStatus(durum).label)
    except ValueError:
        return rol_etiketi(None)  # "Hesap kaydı okunamadı"


def _kayit_iletisi(kayit: str | None) -> str | None:
    if kayit is None:
        return None
    return _ROW_GAP_MESSAGE if kayit == KAYIT_IZ_BOSLUGU else _ROW_SEAL_MESSAGE


def _eylem(neden: str | None) -> dict[str, Any]:
    return {"yapilabilir": neden is None, "neden": neden}


def _giris_engeli(
    hesap: Account, gorunum: _Gorunum, kayit_iletisi: str | None, askida_nedeni: str | None
) -> str | None:
    """Hesap bugün kilit ekranından girebilir mi? Giremiyorsa nedeni (kullanıcı metni).

    `PAROLA_YENILENMELI` girer (ilk girişte parolasını yeniler). Sıra hesap servislerininkidir
    (`_target`; kayıt önce, durum en son): kaydı ya da izi tutmuyor (mührü tutmayan satırın
    durumuna güvenilmez), kapalı, askıda, parola kaydı yok, parola kaydının özeti tutmuyor (iki
    depo kartının "Giriş yapamayan hesaplar"ı ve özeti tutmayanlar). Kilit ekranı parola kaydının
    yokluğunu ve dosyadaki askıyı mühürden önce (parola denenmeden) sorar; orada aynı hesap
    "askıda" ya da "parola kaydı yok" iletisini alabilir.
    """
    kimlik = str(hesap.id)
    if kayit_iletisi is not None:
        return kayit_iletisi
    if hesap.status == AccountStatus.KAPALI:
        return _LOGIN_CLOSED_MESSAGE
    if askida_nedeni is not None:
        return _LOGIN_SUSPENDED_MESSAGE
    if kimlik not in gorunum.ozetler:
        return _LOGIN_NO_WRAP_MESSAGE
    if not app_password.digest_matches(hesap, gorunum.ozetler[kimlik]):
        return _LOGIN_DIGEST_MESSAGE
    return None


def _kullanici_satiri(hesap: Account, gorunum: _Gorunum) -> dict[str, Any]:
    """Kullanıcılar satırı (kişisiz kodlar + kullanıcı metinleri; geçici parola YOK).

    Eylemlerin nedenleri servislerin sırasıyla ve iletileriyledir (`close_account`, `unsuspend`,
    `reset_password`, `teslim_pusulasi`): kendi hesabı → kaydı ya da izi tutmuyor → kapalı (durum
    en son, doğrulanmış satırdan; `_target`) → (kapamada) son program yöneticisi; askıdaki hesabın parolası sıfırlanmaz; askıda olmayan hesap
    askıdan çıkarılmaz; teslim pusulası askıdaki hesaba da basılır.
    Kaydı tutmayan satırda ileti, servisin reddinin ("kayda dokunulmadı") önceden söylenişidir
    ("program bu kayda dokunmaz"); kayıt kodu (`KAYIT_*`) yalnız iletiyi seçer.
    """
    kimlik = str(hesap.id)
    kayit = gorunum.durumlar.get(kimlik)
    kendi = kimlik == gorunum.oturum_id
    kapali = hesap.status == AccountStatus.KAPALI
    askida_nedeni: str | None = None
    if not kapali:
        if gorunum.dosya_askilari.get(kimlik, False):
            askida_nedeni = HATALI_DENEME_ASKISI
        elif hesap.status == AccountStatus.ASKIDA:
            askida_nedeni = hesap.suspend_reason or ASKI_NEDENI_BILINMIYOR
    kayit_iletisi = _kayit_iletisi(kayit)

    def _ortak(kendi_iletisi: str | None) -> str | None:
        if kendi and kendi_iletisi is not None:
            return kendi_iletisi
        if kayit_iletisi is not None:
            return kayit_iletisi
        return _CLOSED_MESSAGE if kapali else None

    kapat = _ortak(_OWN_CLOSE_MESSAGE)
    if kapat is None and hesap.role == AccountRole.YONETICI and gorunum.acik_yonetici <= 1:
        kapat = _LAST_ADMIN_MESSAGE
    askidan_cikar = _ortak(None)
    if askidan_cikar is None and askida_nedeni is None:
        askidan_cikar = _NOT_SUSPENDED_MESSAGE
    sifirla = _ortak(_OWN_RESET_MESSAGE)
    if sifirla is None and hesap.status == AccountStatus.ASKIDA:
        sifirla = _SUSPENDED_RESET_MESSAGE
    pusula = _ortak(_OWN_SLIP_MESSAGE)
    giris = _giris_engeli(hesap, gorunum, kayit_iletisi, askida_nedeni)

    ad = hesap.display_name
    return {
        "id": kimlik,
        "tanitici": hesap.login_name,
        "rol": hesap.role,
        # Rol etiketi sıra no'suzdur (plan F1b-2 "Sözleşme"; sıra no yalnız kilit ekranında).
        "rol_etiketi": rol_etiketi(hesap.role),
        # Çözülemeyen ad (D48) boştur; ön yüz "okunamadı" yazar (sözlük §1 "Şifreleme").
        "ad_soyad": ad if isinstance(ad, str) else None,
        "durum": hesap.status,
        "durum_etiketi": _durum_etiketi(hesap.status),
        "askida_nedeni": askida_nedeni,
        "askida_nedeni_etiketi": _ASKI_ETIKETLERI.get(askida_nedeni or ""),
        "kayit_tutuyor": kayit is None,
        "oturumdaki": kendi,
        "acilis": _yerel(hesap.opened_at),
        "kapanis": _yerel(hesap.closed_at),
        "son_giris": _yerel(hesap.last_login_at),
        "giris": {"yapabilir": giris is None, "neden": giris},
        "eylemler": {
            EYLEM_KAPAT: _eylem(kapat),
            EYLEM_ASKIDAN_CIKAR: _eylem(askidan_cikar),
            EYLEM_PAROLA_SIFIRLA: _eylem(sifirla),
            EYLEM_PUSULA: _eylem(pusula),
        },
    }


#: Liste sırası: açık (kapalı olmayan) hesaplar önce, kapalılar sonda.
_KAPALI_SONDA = {AccountStatus.KAPALI.value: 1}


#: Açılış anı okunamayan hesabın sıralama anahtarı (o hesap rolünün sonuna düşer).
_EN_ESKI_AN = datetime.min.replace(tzinfo=UTC)


def _acilis_sirasi(an: datetime | None) -> tuple[bool, datetime]:
    """Açılış anının sıralama anahtarı: okunamayan an (None; program dışından yazılmış) sonda —
    None ile anı karşılaştırmak sıralamayı (ve listeyi) düşürürdü (orkestratör maddesi (d0)-2)."""
    return (an is None, an or _EN_ESKI_AN)


def _liste_sirasi(hesap: Account) -> tuple[Any, ...]:
    """Açık hesaplar önce (rol sırası, açılış), kapalılar sonda (aynı sırayla)."""
    return (
        _KAPALI_SONDA.get(hesap.status, 0),
        _ROL_SIRASI.get(hesap.role, len(_ROL_SIRASI)),
        _acilis_sirasi(hesap.opened_at),
        hesap.login_name,
    )


def kullanici_listesi() -> list[dict[str, Any]]:
    """Kullanıcılar listesi: BÜTÜN hesaplar — giriş yapamayanlar ve kapalılar dahil (plan F1b-2).

    Yalnız program yöneticisi (rol kapısı ve yetki kapısı, `Eylem.HESAP_YONETIMI`); kilit açık
    olmalı (mühür ve ad DEK ister). Satır `_kullanici_satiri`'dır. Hiçbir şey yazmaz; okuma erişim
    günlüğüne girmez (hesap sahibinin adı tasarım §4.6.4'ün hassas okuma türlerinden değildir).
    """
    yetki_oturum(Eylem.HESAP_YONETIMI)
    gorunum = _gorunum(_active_data_key())
    return [
        _kullanici_satiri(hesap, gorunum)
        for hesap in sorted(gorunum.hesaplar.values(), key=_liste_sirasi)
    ]


def _hesap_kisaltmasi(gorunum: _Gorunum, hesap_id: object) -> dict[str, Any] | None:
    """Ayrıntıdaki ilgili hesap (açan, kapatan, sıfırlayan): kişisiz `{id, tanitici, rol_etiketi}`."""
    if hesap_id is None:
        return None
    kimlik = str(hesap_id)
    hesap = gorunum.hesaplar.get(kimlik)
    return {
        "id": kimlik,
        "tanitici": None if hesap is None else hesap.login_name,
        "rol_etiketi": None if hesap is None else rol_etiketi(hesap.role),
    }


def _tek_satir(hesap_id: object) -> tuple[Account, _Gorunum] | None:
    kimlik = denetim_izi.kimlik_metni_ya_da_none(Account, hesap_id)
    gorunum = _gorunum(_active_data_key())
    hesap = gorunum.hesaplar.get(kimlik or "")
    return None if hesap is None else (hesap, gorunum)


def kullanici_satiri(hesap_id: object) -> dict[str, Any] | None:
    """Tek hesabın Kullanıcılar satırı (hesap açmanın ve eylemlerin yanıtı); hesap yoksa None."""
    yetki_oturum(Eylem.HESAP_YONETIMI)
    bulunan = _tek_satir(hesap_id)
    return None if bulunan is None else _kullanici_satiri(*bulunan)


def kullanici_ayrintisi(hesap_id: object) -> dict[str, Any] | None:
    """Bir hesabın ayrıntısı ve son girişleri (`accounts/<id>/`); hesap yoksa None.

    Satır alanlarına ek olarak açan, kapatan, son parola değişimi, son sıfırlama (tür kodu
    `SIFIRLAMA` ya da `KURTARMA`; ön yüz sözlükteki cümleyi yazar) ve kilit ekranından son girişler
    (`iz_dogrulama.hesabin_girisleri`: yalnız o hesabın doğrulanan `GIRIS` satırları). Yalnız
    program yöneticisi; hiçbir şey yazmaz.
    """
    yetki_oturum(Eylem.HESAP_YONETIMI)
    bulunan = _tek_satir(hesap_id)
    if bulunan is None:
        return None
    hesap, gorunum = bulunan
    satir = _kullanici_satiri(hesap, gorunum)
    satir["acan"] = _hesap_kisaltmasi(gorunum, hesap.opened_by_id)
    satir["kapatan"] = _hesap_kisaltmasi(gorunum, hesap.closed_by_id)
    satir["parola_degisimi"] = _yerel(hesap.password_changed_at)
    satir["sifirlama"] = (
        None
        if hesap.reset_at is None
        else {
            "tur": hesap.reset_kind or None,
            "zaman": _yerel(hesap.reset_at),
            "yapan": _hesap_kisaltmasi(gorunum, hesap.reset_by_id),
        }
    )
    satir["son_girisler"] = iz_dogrulama.hesabin_girisleri(hesap.id)
    return satir


def kullanici_secenekleri() -> dict[str, Any]:
    """ "Yeni hesap" penceresinin seçenekleri (`accounts/options/`; plan F1b-2).

    `roller`: her rol için `{rol, rol_etiketi, acilabilir, neden, varsayilan_tanitici, bilgi}`.
    `neden` hesap açmanın vereceği iletinin AYNISIDIR (`_rol_acilamama_nedeni`; kaydı ya da izi
    tutmayan hesap için ayrı neden — orkestratör maddesi C-1). `bilgi` program yöneticisi rolünde
    ikinci program yöneticisinin bilgisidir (`IKINCI_YONETICI_BILGISI`). Rolün etiketi sıra
    no'suzdur. Yalnız program yöneticisi; hiçbir şey yazmaz.
    """
    yetki_oturum(Eylem.HESAP_YONETIMI)
    dek = _active_data_key()
    roller: list[dict[str, Any]] = []
    with transaction.atomic():
        acik = app_password.hesap_satirlari(Account.objects.exclude(status=AccountStatus.KAPALI))
        alinmis = [hesap.login_name for hesap in acik]
        for rol in AccountRole.values:
            neden = _rol_acilamama_nedeni(rol, [h for h in acik if h.role == rol], dek)
            roller.append(
                {
                    "rol": rol,
                    "rol_etiketi": rol_etiketi(rol),
                    "acilabilir": neden is None,
                    "neden": neden,
                    "varsayilan_tanitici": hesap_kurallari.default_login_name(rol, alinmis),
                    "bilgi": IKINCI_YONETICI_BILGISI if rol == AccountRole.YONETICI else None,
                }
            )
    return {"roller": roller}
