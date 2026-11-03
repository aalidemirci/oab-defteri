"""Denetim izi yazıcısı — TEK yazar (tasarım §4.6.2-§4.6.3, TK16; plan F1b-1 alt commit c).

Her yazma servisi veri satırını yazdığı İŞLEMİN İÇİNDE buraya açıkça çağrı yapar;
yazıcı satırı aynı işleme ekler, biri yazılamazsa ikisi de geri alınır (yazma kuralı
1). Django sinyali ya da `save()` kancası KULLANILMAZ: toplu `update()`, yumuşak silme
querysetleri ve `bulk_*` sinyali atlardı. Toplu yazım kayıt başına satır yazar (önce
kayıtlar okunur, her birinin önceki hâli alınır). İzsiz yazımı iki test yakalar
(`tests/test_izsiz_yazim.py`): yazma uçlarının hepsini süren çalışma anı testi ve
servislerdeki ORM yazma çağrılarının kaynak taraması; muafiyetler orada ADIYLA ve
gerekçesiyle yazılıdır (plan F1b-1: kişi silme ve birleştirme 5. adımda yeniden yazılır).

Giriş noktaları: `degisiklik` (okul çekirdeğinin kayıtları; tür modelin durum
alanlarından seçilir: `OLUSTUR`, `GUNCELLE`, `DURUM`), `kayit` (türü çağıranın verdiği
kayıt yazımı: hesap olayları), `olay` (kayıt yazımı olmayan olay: kilit, mühür bulgusu,
`guvenlik.json` bölümü, yedek, dosyadaki ayar), `kvkk_silme` (KVKK silmesi: model, alan
adları, adet, tetik; değer yok — bugün erişim günlüğünün saklama süresi dolan satırları).

KURALLAR (her biri bu modülde zorlanır):

* **İşlem içinde.** `connection.in_atomic_block` doğru değilse yazmaz (`IzYazilamadi`).
  Ayarlardaki `transaction_mode = "IMMEDIATE"` yalnız atomik bloklara uygulanır; zincirin
  sonunu okumak ile satırı eklemek arasına başka bir yazar ancak böyle giremez.
* **Zincirin sonu her seferinde veritabanından, işlemin içinde okunur.** Bellekte son
  MAC TUTULMAZ: içe aktarma önizlemesi işlemini `set_rollback` ile geri sarar; bellekte
  kalan bir "son MAC" geri alınmış satıra bağlanır, zincir kopardı. `seq` son satırın
  +1'idir; geri alınan satır boşluk bırakmaz.
* **Yazar bağlamı zorunludur.** Yazar `oturum.yazar()`'dır: istek başında ara katmanın
  kurduğu bağlam (oturum istek sürerken değişse de o isteğin yazarı açılıştaki hesaptır),
  gün işinde ve sistem işinde açıkça verilen `SISTEM` (`oturum.sistem_olarak`), kilit
  açılışında, ilk hesapta ve kurtarmayla açılışta o hesap (plan F1b-1). Bağlam yoksa
  yazmaz.
* **Kaydın özeti (R1).** Satır kişisel veri taşımaz: kayıt kimliği, değişen alan ADLARI,
  modelin izinli kişisiz alanlarının `[önce, sonra]` değeri (`IZ_DEGER_ALANLARI`, modelde)
  ve içerik MAC'i. İzin listesi dışındaki alanın değeri `values`'a giremez (yazıcı
  reddeder). `guvenlik.json`'daki bölümler (kurtarma anahtarı, hesap sarmalı), yedek
  dosyası ve dış yedek ayarı veritabanı modeli değildir; izinli alanları burada,
  `DOSYA_NESNELERI`'ndedir. KVKK silme kümesindeki modellerin (`Student`, `Personnel`)
  izin listesi boştur.
* **İçerik MAC'i** (`record_mac`) kaydın YAZMADAN SONRAKİ hâlinden, veritabanından taze
  okunarak hesaplanır: `HMAC(HKDF(İA, "od-kayit-ozeti/v1"), kanonik(model, object_id,
  özet alanlarının çözülmüş değerleri))` (`shared.kanonik.kayit_mac`; alanlar
  `IZ_OZET_ALANLARI`, modelde). KVKK silme kümesindeki kişi alanları (öğrenci ve personelin
  adı, soyadı, okul no'su) içerik MAC'ine GİRMEZ (`IZ_MAC_DISI_ALANLARI`; tasarım §5 O4):
  silinen kişiyi MAC'ten sözlükle geri bulmak mümkün olmasın. Çözülemeyen şifreli alan (`CorruptField`, D48) hata
  vermez, düz metne de çevrilmez: `kanonik.bozuk_alan` temsiliyle girer. Kilitli kip
  satırı içerik MAC'i taşımaz.
* **Zincir:** `mac = HMAC(HKDF(İA, "od-denetim-izi/v1"), kanonik(satır) ‖ prev_mac)`
  (`kanonik.iz_mac`). Açık kipte `key_ref` satırı mühürleyen `AuditKey`'in kimliğidir;
  bellekteki İA'nın o kayıt olduğu oturum başına bir kez doğrulanır.

ÖZET ALANLARI VE ŞEMA DEĞİŞİMİ. İçerik MAC'i modelin açık listesindeki alanları kapsar
(`IZ_OZET_ALANLARI`); yeni bir sütun listeye eklenirse var olan kayıtların yeniden
hesaplanan MAC'i son iz satırındakini tutmaz. Listeye alan ekleyen değişiklik, ilk kilit
açılışında koşan veri göçüyle her kayda yeni MAC'li bir satır yazmalıdır (tasarım §4.1
"veri göçü ilk kilit açılışında"); listeler bu yüzden modelde, göçle birlikte değişir. `Account`
için bu kural GİRİŞİ bağlar (kullanıcı kararı 03.11.2026 "Girişte reddet"; `hesap_izi_tutuyor`,
`services.satir_izi`): hesap satırı son içerik MAC'li iz satırını tutmazsa giriş, oturum işlemi ve
hesap işlemi reddedilir. `Account` için "ilk kilit açılışında veri göçü" yolu KAPALIDIR: satırın
izi kilit açılışında, DEK belleğe alınmadan ve her veri göçünden ÖNCE denetlenir; şema göçü
kilitliyken iz yazamaz. `Account.IZ_OZET_ALANLARI`'nı ya da var olan satırların bu alanlardaki
değerini değiştiren her değişiklik (F4'ün DEK yenilemesindeki mühür, özet ve ad-soyad yeniden
yazımı dahil) `KAPALI` olanlar DAHİL BÜTÜN hesap satırlarının izini aynı işlemde yeniden kurmalıdır
(her satıra yeni hâlinin içerik MAC'ini taşıyan, o sırada yürürlükteki iz anahtarıyla mühürlü bir
iz satırı), ama YALNIZ satırı önce ESKİ alan kümesiyle ve eski anahtarla son içerik MAC'li kaydına
karşı doğrulayıp tutanlara (doğrulamasız yeniden kurma geri sarılmış satırı aklar). Yoksa açık
satırların girişi reddedilir, `KAPALI` satırlar iki depo kartında "kaydı program dışından
değiştirilmiş görünen hesaplar" listesine düşer ve sarmallarının temizliği durur. Böyle bir adım
tasarlanmadan küme değiştirilmez (kullanıcı kararı bekler; F1c'nin `person`/`membership`/`term`
alanları buna girer). Program sahaya çıkana dek deneme kurulumları silinip yeniden kurulur
(kullanıcı kararı 03.11.2026).

TEK YAZARIN ORM'SİZ EŞİ: geri yüklemenin özet onarımı (`services.ozet_onarimi`) takastan önce,
oturumu olmayan `.tmp` veritabanında yazar; değiştirdiği hesap satırlarının iz satırını
`services.satir_izi.hesap_satirlarini_izle` ekler. Biçim bu modülün `_ekle`'siyle BİREBİRDİR
(`SISTEM`, açık kip, etkin `AuditKey`, `kanonik.kayit_mac` ve `kanonik.iz_mac`; sütunlar Django'nun
yazdığı biçimde); eşitliği `test_satir_izi.py` sınar, izsiz yazım taraması ilkeller listesinde
adıyla tanır.

KİLİTLİ KİP (`key_mode = KILITLI`, §4.6.3: `YEDEK`, `GOC`, `GUN_ISI`, `BUTUNLUK`) bu
modülün ikinci giriş noktasıdır (`kilitli_olay`). Çekirdek (`_ekle`) mührü dışarıdan
alır (`AcikAnahtar` ya da `KilitliMuhur`), zinciri ve satırı aynı kuralla kurar; kilitli
mühürde yalnız kapalı kümedeki `SISTEM` olayı yazılır, içerik MAC'i yoktur. Çapa,
`iz-durumu.json` ve tohumun ilerletilmesi `apps.okul.iz_durumu`'dadır; tohumun dosyada
satırdan ÖNCE ilerlemesi mührün `kaydetmeden_once` kancasıyla sağlanır (plan F1b-1).
Kilitli satırın anahtarı veritabanından da türetilebilir: `key_ref = "<çapa seq>:<adım>"`
satırı, çapanın `seq` satırının `mac`'i ve o satırı mühürleyen İA `tohum₀`'ı verir
(`kilitli_zincir_anahtarlari`). Zincir doğrulaması böylece `iz-durumu.json` silinmiş ya da
yenilenmiş olsa da eski kilitli satırları doğrular; dosyayı okuyan biri (İA'sız) hiçbir
satırı mühürleyemez. Doğrulama satırın türünü ve kipini de denetler (`satir_kurali_tutuyor`):
mühürsüz ya da kilitli kip anahtarıyla yazılmış bir satır yalnız kapalı kümedeki kişisiz
`SISTEM` olayı olabilir; kartlar yalnız açık kipte mühürlü satırları okur
(`acik_satir_dogrulayici`).

İz yazılamazsa yazma yapılamaz (hesap bütünlüğü; plan F1b-1): yazıcının her reddi
istisnadır ve çağıranın işlemini geri sardırır. Anahtar bellekte değilse (oturum istek
ortasında kilitlendi) ret `KeyMissingError` ailesindendir: uç 409 döner.
"""

from __future__ import annotations

import base64
import hmac
import logging
import re
import threading
import uuid
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Final

from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import DatabaseError, connection, models, transaction
from django.db.models import QuerySet
from django.db.models.functions import Cast
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.okul.models import (
    KILITLI_KIP_TURLERI,
    Account,
    AuditAction,
    AuditActor,
    AuditKey,
    AuditKeyMode,
    AuditLabel,
    AuditTrail,
)
from apps.okul.oturum import Yazar, yazar, yazar_olarak
from apps.okul.services import satir_izi
from shared import crypto, kanonik

logger = logging.getLogger("oab_defteri.okul")

#: İz anahtarının uzunluğu (bayt); DEK'ten türemez, kurulumda ayrı üretilir (§4.6.3).
IZ_ANAHTARI_BAYT: Final = 32

#: Veritabanı modeli olmayan izli nesneler ve izinli kişisiz alanları:
#:
#: * `guvenlik.json` bölümleri — kurtarma anahtarının kimliği (no, üretim günü; TK10) ve
#:   hesap sarmalının hatalı deneme sayacı ile askısı (§15 M-12). Tuz ve sarmal ASLA
#:   satıra girmez.
#: * Şifreli yedek dosyası (`YEDEK`; kimliği dosyanın adıdır, ad zaman damgasıdır).
#:   Kullanıcının istediği yedek açık kipte, açılıştaki günlük ve göç öncesi yedekler
#:   kilitli kipte yazılır (tasarım §4.6.3). Yalnız programın ürettiği ad kimlik olur
#:   (`yedek_kimligi`); elle konmuş ya da yeniden adlandırılmış dosyanın adı satıra girmez.
#: * Dış yedek hatırlatmasının süresi (`dis-yedek.json`, tasarım §16 R6; gün sayısı).
#: * Şema göçü (`GOC`; kimliği programın sürümü, değeri uygulanan göçlerin adları).
#: * Ertelenen gün işi (`GUN_ISI`; kimliği işin ASCII adı).
#: * Kilit açılışındaki kendiliğinden doğrulama (`BUTUNLUK`; bulgu kodları, düzey, çapanın
#:   sırası, kilitli satır sayıları, bulgulu satırların sıraları — hepsi sayı ya da iç kod).
#: * Geri yükleme (`GERI_YUKLEME`; kimliği kenara alınan veritabanının adı; yol, kurtarma
#:   anahtarı no'su, parolayla açan hesabın kimliği, uygulama içi geri yüklemede oturumdaki
#:   hesabın kimliği, kenara alınanın sha256'sı ve zincir başı). Tanıtıcı satıra girmez:
#:   kişinin adını içerebilir (program yalnız uyarır).
#:
#: `zaman`: satırın anı (`at`) yazıldığı andır. Sistem olayı yazılamayıp beklemişse (geri
#: yükleme notunda ya da düşen bir kilitli yazımdan sonra bellekte; `iz_durumu`) ilk kilit
#: açılışında yazılır; olayın KENDİ anı o zaman `zaman` değeridir (UTC; saat dilimsiz an
#: girmez). Geri yüklemenin anı da böyledir.
KURTARMA_ANAHTARI: Final = "guvenlik.kurtarma"
HESAP_SARMALI: Final = "guvenlik.sarmal"
YEDEK_DOSYASI: Final = "yedek.dosya"
DIS_YEDEK_AYARI: Final = "dis_yedek.ayar"
SEMA_GOCU: Final = "sema.goc"
GUN_ISI_ERTELEME: Final = "gun_isi.erteleme"
IZ_DOGRULAMASI: Final = "denetim_izi.dogrulama"
GERI_YUKLEME_KAYDI: Final = "yedek.geri_yukleme"
DOSYA_NESNELERI: Final[Mapping[str, tuple[str, ...]]] = {
    KURTARMA_ANAHTARI: ("no", "tarih"),
    HESAP_SARMALI: ("hatali", "askida"),
    YEDEK_DOSYASI: ("zaman",),
    DIS_YEDEK_AYARI: ("hatirlatma_gun",),
    SEMA_GOCU: ("gocler", "zaman"),
    GUN_ISI_ERTELEME: ("zaman",),
    IZ_DOGRULAMASI: (
        "bulgular",
        "duzey",
        "capa_seq",
        "adim",
        "kilitli_satir",
        "bulgu_satirlari",
        "zaman",
    ),
    GERI_YUKLEME_KAYDI: (
        # Geri yüklemenin anı (nottan; satırın kendi anı ilk kilit açılışınındır).
        "zaman",
        "yedek",
        "yol",
        "kurtarma_no",
        "hesap",
        "oturum_hesap",
        "onceki_sha256",
        "onceki_seq",
        "onceki_mac",
    ),
}

#: Programın ürettiği yedek adları — BİREBİR biçimleriyle (`desktop/backup.py`,
#: `services/encrypted_backup.py`): günlük `gunluk-<gün>`, göç öncesi
#: `pre-migrate-<sürüm>-<gün>`, saklama tetiği öncesi `pre-anonim-<gün>-<saat>[-<sıra>]`,
#: indirilen `oab-defteri-yedek-<gün>-<saat>`. Önekten sonra serbest harf KABUL EDİLMEZ:
#: kullanıcı programın önekini koruyup dosyaya bir ad ekleyebilir ("oab-defteri-yedek-…-
#: Uydurma.odbak"); o ad serbest metindir, kişi adı içerebilir (R1). Sürüm yalnız
#: `x.y.z[-alpha|beta|rc|dev[.n]]` biçimindedir; uymayan sürümlü ad da satıra girmez
#: (fail-closed: ad düşer, olay kalır).
_GUN = r"\d{4}-\d{2}-\d{2}"
_PROGRAM_YEDEGI: Final = re.compile(
    rf"^(?:gunluk-{_GUN}"
    rf"|pre-migrate-\d{{1,4}}\.\d{{1,4}}\.\d{{1,4}}(?:-(?:alpha|beta|rc|dev)(?:\.\d{{1,4}})?)?-{_GUN}"
    rf"|pre-anonim-{_GUN}-\d{{6}}(?:-\d{{1,4}})?"
    rf"|oab-defteri-yedek-{_GUN}-\d{{6}})\.odbak$"
)


def program_yedegi_mi(ad: object) -> bool:
    """Ad programın ürettiği bir yedek adı mı? (`_PROGRAM_YEDEGI`; yol ayırıcısı ya da boşluk yok)"""
    return isinstance(ad, str) and _PROGRAM_YEDEGI.match(ad) is not None


def yedek_kimligi(ad: object) -> str:
    """`YEDEK` satırının kimliği: programın ürettiği ad, değilse BOŞ (adı kayda geçmez; R1).

    Rotasyon tarihi adın herhangi bir yerinde arar (`desktop/backup.py`): yedek klasörüne
    elle konmuş "gunluk-2026-10-01 <ad>.odbak" da silinir; silinen dosyanın adı satıra
    girmez, olay kalır. Geri yükleme notunda bekleyen olay da aynı kuraldan geçer.
    """
    return ad if isinstance(ad, str) and program_yedegi_mi(ad) else ""


#: Her yazımda değişen ama kendi başına anlamı olmayan alan (`BaseModel.updated_at`):
#: `degisiklik` onu satırların ilkine ekler; yalnız o değiştiyse tek `GUNCELLE` satırıdır.
_GUNCELLENME_ALANI: Final = "updated_at"

#: Yazmadan önceki hâlin (alan adı → değer) bellekteki biçimi. Şifreli alanların çözülmüş
#: değerini taşır: YALNIZ bellekte tutulur, hiçbir yere yazılmaz.
Anlik = dict[str, Any]


class IzYazilamadi(RuntimeError):
    """İz satırı yazılamadı; çağıranın yazması da yapılmaz (tasarım §4.6.2 yazma kuralı 1)."""


class IzAnahtariOkunamadi(IzYazilamadi):
    """Etkin iz anahtarı yok ya da verilen DEK'le çözülemiyor (kilit açılışı reddeder)."""


class IzAnahtariBellekteDegil(crypto.KeyMissingError, IzYazilamadi):
    """DEK ya da İA bellekte değil (oturum kilitli): uç 409 döner, işlem geri alınır."""

    def __init__(self, message: str = "Kayıtlar kilitli; iz yazılamaz.") -> None:
        super().__init__(message)


@dataclass(frozen=True)
class AcikAnahtar:
    """Açık kipte satırı mühürleyen iz anahtarı (İA) ve onun `AuditKey` kimliği."""

    ia: bytes = field(repr=False)
    kayit_id: int


@dataclass(frozen=True)
class KilitliMuhur:
    """Kilitli kipte bir satırı mühürleyen anahtar adımı (tasarım §4.6.3; `iz_durumu` kurar).

    `zincir_anahtari` k'ıncı tohumdan türeyen anahtardır (`HKDF(tohumₖ,
    "od-iz-kilitli-mac/v1")`) ya da mühürsüz satırda sırsız `kanonik.MUHURSUZ_ANAHTAR`.
    `key_ref` `"<çapa seq>:<k>"`, mühürsüz satırda boştur. `kaydetmeden_once` satırın MAC'i
    hesaplandıktan sonra, satır eklenmeden HEMEN ÖNCE çağrılır: tohum dosyada ilerler, eski
    tohum silinir; satır ondan SONRA yazılır (plan F1b-1). Kanca hata verirse satır yazılmaz.
    """

    zincir_anahtari: bytes = field(repr=False)
    key_ref: str
    kaydetmeden_once: Callable[[], None] | None = field(default=None, repr=False)


# ---------------------------------------------------------------------------
# İz anahtarı
# ---------------------------------------------------------------------------
def _etkin_kayit() -> tuple[int, str] | None:
    """Etkin (emekli olmamış, en yeni) iz anahtarı: (kimlik, ham şifreli token).

    Ham sütun okunur (`Cast` alanın `from_db_value`'sunu atlar): bellekte başka bir
    anahtar yüklüyken de yalnız verilen DEK denenir.
    """
    kayit = (
        AuditKey.objects.filter(retired_at__isnull=True)
        .order_by("-valid_from_seq")
        .values_list("pk", Cast("key", output_field=models.TextField()))
        .first()
    )
    if kayit is None:
        return None
    return int(kayit[0]), str(kayit[1] or "")


def _token_coz(veri_anahtari: bytes, token: str) -> bytes:
    """`AuditKey.key` token'ını DEK'le çözer; 32 baytlık İA değilse `IzAnahtariOkunamadi`."""
    try:
        anahtar = base64.b64decode(crypto.decrypt_with(veri_anahtari, token), validate=True)
    except Exception as exc:  # noqa: BLE001 — InvalidToken, biçim ve base64 hataları aynı ret
        raise IzAnahtariOkunamadi("İz anahtarı bu veri anahtarıyla çözülemedi.") from exc
    if len(anahtar) != IZ_ANAHTARI_BAYT:
        raise IzAnahtariOkunamadi("İz anahtarı beklenen uzunlukta değil.")
    return anahtar


def anahtari_coz(veri_anahtari: bytes) -> AcikAnahtar:
    """Etkin İA'yı verilen DEK'le çözer (DEK belleğe alınmadan; kilit açılışı, §4.6.3).

    İA yoksa ya da çözülemezse `IzAnahtariOkunamadi`: iz yazılamazsa yazma yapılamaz,
    kilit açılışı bunu `iki_depo_tutarsiz` ile reddeder (`app_password`).
    """
    kayit = _etkin_kayit()
    if kayit is None or not kayit[1]:
        raise IzAnahtariOkunamadi("Etkin iz anahtarı yok.")
    return AcikAnahtar(ia=_token_coz(veri_anahtari, kayit[1]), kayit_id=kayit[0])


_dogrulama_kilidi = threading.Lock()
#: Bellekteki İA'nın etkin `AuditKey` olduğu en son hangi anahtar yüklemesinde (`key_epoch`)
#: ve hangi kayıt için doğrulandı. Her `load_key`/`unload_key` sayacı artırır: yeni oturum
#: yeniden doğrular. Anahtarın kendisi burada TUTULMAZ.
_dogrulanan: tuple[int, int] | None = None


def _bellekteki_anahtar() -> AcikAnahtar:
    """Oturumun İA'sı ve kaydı; bellekteki İA'nın etkin kayıt olduğu doğrulanır.

    DEK ya da İA yoksa `IzAnahtariBellekteDegil`. Bellekteki İA etkin kaydın çözülmüş
    anahtarı değilse `IzYazilamadi`: satırın `key_ref`'i yalan söylemesin (doğrulayıcı o
    kaydın anahtarıyla doğrular). Doğrulama anahtar yüklemesi başına bir kez yapılır.
    """
    global _dogrulanan
    ia = crypto.active_audit_key()
    dek = crypto.active_key()
    if ia is None or dek is None:
        raise IzAnahtariBellekteDegil()
    donem = crypto.key_epoch()
    kayit = _etkin_kayit()
    if kayit is None or not kayit[1]:
        raise IzYazilamadi("Etkin iz anahtarı yok; iz yazılamaz.")
    with _dogrulama_kilidi:
        dogrulandi = _dogrulanan == (donem, kayit[0])
    if not dogrulandi:
        if not hmac.compare_digest(_token_coz(dek, kayit[1]), ia):
            raise IzYazilamadi("Bellekteki iz anahtarı veritabanındaki etkin anahtar değil.")
        with _dogrulama_kilidi:
            _dogrulanan = (donem, kayit[0])
    return AcikAnahtar(ia=ia, kayit_id=kayit[0])


# ---------------------------------------------------------------------------
# Kaydın alanları
# ---------------------------------------------------------------------------
def model_etiketi(model: type[models.Model]) -> str:
    """İz satırının `model` sütunu: uygulama etiketli model adı (`okul.Account`)."""
    return str(model._meta.label)


def _izli_alanlar(model: type[models.Model]) -> tuple[models.Field[Any, Any], ...]:
    """Kaydın kimlik dışındaki somut alanları (model sırasıyla)."""
    return tuple(alan for alan in model._meta.fields if alan.concrete and not alan.primary_key)


def _alan_degeri(nesne: models.Model, alan: models.Field[Any, Any]) -> Any:
    """Alanın özet ve karşılaştırma değeri: yabancı anahtar kimliğin METNİ, bozuk alan temsil."""
    deger = getattr(nesne, alan.attname)
    if isinstance(deger, crypto.CorruptField):
        return kanonik.bozuk_alan(deger.raw)
    if alan.is_relation:
        return None if deger is None else str(deger)
    return deger


def kimlik_metni(model: type[models.Model], pk: Any) -> str:
    """İz satırının `object_id`'si: kimliğin alan türüne göre metni (UUID tireli, sayı ondalık).

    Aynı kayıt hangi biçimde verilirse verilsin (`"6f1c…"`, tiresiz onaltılık, UUID) tek
    metne iner: içerik MAC'i ve "kaydın son iz satırı" araması buna bağlıdır.
    """
    alan = model._meta.pk
    assert alan is not None  # her modelin birincil anahtarı vardır
    return str(alan.to_python(pk))


def kimlik_metni_ya_da_none(model: type[models.Model], pk: Any) -> str | None:
    """`kimlik_metni`; değer boşsa ya da o modelin kimliği olamıyorsa (dosyadan okunmuş
    biçimsiz değer) None — hata yükseltmez."""
    if pk is None or pk == "":
        return None
    try:
        return kimlik_metni(model, pk)
    except (ValidationError, TypeError, ValueError):
        return None


def _taze(model: type[models.Model], pk: Any) -> models.Model:
    """Kaydı veritabanından yeniden okur (yumuşak silinmiş dahil; `_base_manager`)."""
    return model._base_manager.get(pk=pk)


def _degerler(nesne: models.Model) -> Anlik:
    return {alan.name: _alan_degeri(nesne, alan) for alan in _izli_alanlar(type(nesne))}


def anlik(nesne: models.Model) -> Anlik:
    """Kaydın yazmadan ÖNCEKİ hâli — veritabanından taze okunur, yalnız bellekte tutulur.

    Servis bunu değişikliği yapmadan önce, aynı işlemin içinde alır; `kayit` yazmadan
    sonraki hâlle karşılaştırıp değişen alanları ve izinli değerleri çıkarır. Bellekteki
    örneğin kaydedilmemiş değişiklikleri karşılaştırmayı yanıltmasın diye örnek değil
    satır okunur. Şifreli alanların çözülmüş değerini taşır; hiçbir yere yazılmaz.
    """
    return _degerler(_taze(type(nesne), nesne.pk))


def _izinli_degerler(model_adi: str) -> tuple[str, ...]:
    """Model ya da dosya nesnesinin `values`'a girebilen alanları (yoksa boş: değer yazılmaz)."""
    if model_adi in DOSYA_NESNELERI:
        return DOSYA_NESNELERI[model_adi]
    try:
        model = django_apps.get_model(model_adi)
    except (LookupError, ValueError):
        return ()
    return tuple(getattr(model, "IZ_DEGER_ALANLARI", ()))


def _izli_model(model: type[models.Model]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Modelin izin listeleri (değer, özet); tanımsızsa yazmaz (programlama hatası)."""
    degerler = getattr(model, "IZ_DEGER_ALANLARI", None)
    ozet = getattr(model, "IZ_OZET_ALANLARI", None)
    if degerler is None or ozet is None:
        raise IzYazilamadi(
            f"{model_etiketi(model)} denetim izi listelerini tanımlamıyor "
            "(IZ_DEGER_ALANLARI, IZ_OZET_ALANLARI)."
        )
    return tuple(degerler), tuple(ozet)


def _durum_alanlari(model: type[models.Model]) -> tuple[str, ...]:
    """Modelin durum alanları (`IZ_DURUM_ALANLARI`); `degisiklik` için tanımsızsa yazmaz."""
    alanlar = getattr(model, "IZ_DURUM_ALANLARI", None)
    if alanlar is None:
        raise IzYazilamadi(
            f"{model_etiketi(model)} durum alanlarını tanımlamıyor (IZ_DURUM_ALANLARI)."
        )
    return tuple(alanlar)


def kayit_mac_hesapla(
    model: type[models.Model], pk: Any, *, anahtar: AcikAnahtar | None = None
) -> str:
    """Kaydın BUGÜNKÜ değerinden içerik MAC'i (veritabanından taze okunur; DEK bellekte olmalı).

    Yazıcı yazmadan sonra, kayıt bütünlüğü denetimi bugün aynı işlevi çağırır: ikisi aynı
    yoldan hesaplanır (tasarım §4.6.2 "içerik MAC'i").
    """
    if not crypto.is_unlocked():
        raise IzAnahtariBellekteDegil()
    _, ozet_alanlari = _izli_model(model)
    acik = anahtar if anahtar is not None else _bellekteki_anahtar()
    degerler = _degerler(_taze(model, pk))
    ozet = {ad: degerler[ad] for ad in ozet_alanlari}
    return kanonik.kayit_mac(
        crypto.record_summary_key(acik.ia), model_etiketi(model), kimlik_metni(model, pk), ozet
    )


# ---------------------------------------------------------------------------
# Yazma
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _Yazim:
    """Bir kaydın yazımının iz satırına girecek özeti (yazmadan sonraki hâlden)."""

    etiket: str
    kimlik: str
    #: Değişen alan adları (model sırasıyla); yeni kayıtta kimlik dışındaki bütün alanlar.
    degisen: list[str]
    #: İzinli alanların `[önce, sonra]` değerleri, kanonik ilkel biçimde.
    degerler: dict[str, list[Any]]
    record_mac: str
    anahtar: AcikAnahtar


def _yazim(nesne: models.Model, *, onceki: Anlik | None, anahtar: AcikAnahtar | None) -> _Yazim:
    """Yazımın özeti: kayıt veritabanından yeniden okunur, önceki hâlle karşılaştırılır."""
    model = type(nesne)
    deger_alanlari, ozet_alanlari = _izli_model(model)
    if not crypto.is_unlocked():
        raise IzAnahtariBellekteDegil()
    acik = anahtar if anahtar is not None else _bellekteki_anahtar()
    sonra = _degerler(_taze(model, nesne.pk))
    if onceki is None:
        degisen = list(sonra)
    else:
        degisen = [ad for ad, deger in sonra.items() if onceki.get(ad) != deger]
    once = onceki or {}
    etiket = model_etiketi(model)
    kimlik = kimlik_metni(model, nesne.pk)
    return _Yazim(
        etiket=etiket,
        kimlik=kimlik,
        degisen=degisen,
        degerler={
            ad: [kanonik.duz(once.get(ad)), kanonik.duz(sonra[ad])]
            for ad in degisen
            if ad in deger_alanlari
        },
        record_mac=kanonik.kayit_mac(
            crypto.record_summary_key(acik.ia),
            etiket,
            kimlik,
            {ad: sonra[ad] for ad in ozet_alanlari},
        ),
        anahtar=acik,
    )


def _yazim_satiri(eylem: str, yazim: _Yazim, alanlar: Sequence[str], label: str) -> AuditTrail:
    """Yazımın bir satırı: yalnız `alanlar`ın adları ve (izinliyse) değerleri."""
    return _ekle(
        eylem,
        model=yazim.etiket,
        object_id=yazim.kimlik,
        changed_fields=list(alanlar),
        values={ad: yazim.degerler[ad] for ad in alanlar if ad in yazim.degerler},
        record_mac=yazim.record_mac,
        label=label,
        anahtar=yazim.anahtar,
    )


def kayit(
    eylem: str,
    nesne: models.Model,
    *,
    onceki: Anlik | None,
    label: str = "",
    anahtar: AcikAnahtar | None = None,
) -> AuditTrail:
    """Bir kaydın yazımını izler: değişen alanlar, izinli değerler, içerik MAC'i (açık kip).

    `onceki` `anlik(nesne)`'nin yazmadan önceki sonucudur; `None` kaydın bu işlemde
    oluşturulduğunu söyler (değişen alanlar kimlik dışındaki bütün alanlar, değerler
    `[None, sonra]`). Kayıt veritabanından yeniden okunur: MAC bellekteki örneğin değil,
    yazılmış satırın özetidir. `anahtar` verilmezse oturumun İA'sı kullanılır (kilit
    açılışı oturum açılmadan önce yazdığı için kendi çözdüğünü verir). Türü çağıran
    verir (hesap olayları); okul çekirdeğinin kayıtları türü modelden seçen
    `degisiklik`'i kullanır.
    """
    yazim = _yazim(nesne, onceki=onceki, anahtar=anahtar)
    return _yazim_satiri(eylem, yazim, yazim.degisen, label)


def degisiklik(
    nesne: models.Model,
    *,
    onceki: Anlik | None,
    label: str = "",
    anahtar: AcikAnahtar | None = None,
) -> list[AuditTrail]:
    """Okul çekirdeğinin kayıt yazımını izler; türü modelin durum alanlarından seçer.

    * `onceki` `None` → tek `OLUSTUR` satırı (kayıt bu işlemde oluşturuldu).
    * Değişen alanlar modelin durum alanlarına (`IZ_DURUM_ALANLARI`: ayrılış, aktiflik,
      havuz, yumuşak silme, koşu durumu) göre ayrılır. "Her durum geçişi ayrı satırdır"
      (tasarım §4.6.2 kural 3): veri alanları değiştiyse `GUNCELLE`, durum alanları
      değiştiyse `DURUM` satırı; ikisi birden değiştiyse İKİ satır (önce `GUNCELLE`).
      `updated_at` ilk satıra girer; yalnız o değiştiyse tek `GUNCELLE` satırıdır.

    İki satır aynı yazımın iki yüzüdür: içerik MAC'leri aynıdır (yazmadan sonraki hâl).
    Yumuşak silme böylece `deleted_at`'li bir `DURUM` satırıdır.
    """
    durum_alanlari = _durum_alanlari(type(nesne))
    yazim = _yazim(nesne, onceki=onceki, anahtar=anahtar)
    if onceki is None:
        return [_yazim_satiri(AuditAction.OLUSTUR, yazim, yazim.degisen, label)]
    durum = [ad for ad in yazim.degisen if ad in durum_alanlari]
    veri = [ad for ad in yazim.degisen if ad not in durum_alanlari]
    if durum and all(ad == _GUNCELLENME_ALANI for ad in veri):
        return [_yazim_satiri(AuditAction.DURUM, yazim, yazim.degisen, label)]
    satirlar = [_yazim_satiri(AuditAction.GUNCELLE, yazim, veri, label)]
    if durum:
        satirlar.append(_yazim_satiri(AuditAction.DURUM, yazim, durum, label))
    return satirlar


def olay(
    eylem: str,
    *,
    model: str,
    object_id: str,
    changed_fields: Iterable[str] = (),
    values: Mapping[str, Sequence[Any]] | None = None,
    label: str = "",
    anahtar: AcikAnahtar | None = None,
) -> AuditTrail:
    """Kayıt yazımı olmayan olay (açık kip): kilit, mühür bulgusu, `guvenlik.json` bölümü,
    yedek dosyası, dosyadaki ayar (`DOSYA_NESNELERI`).

    İçerik MAC'i taşımaz. `values` yalnız `model`'in izinli alanlarını taşıyabilir
    (veritabanı modelinde `IZ_DEGER_ALANLARI`, dosya nesnesinde `DOSYA_NESNELERI`);
    değerler kanonik ilkel biçime çevrilir.
    """
    degerler = izinli_degerler(model, values)
    acik = anahtar if anahtar is not None else _bellekteki_anahtar()
    return _ekle(
        eylem,
        model=model,
        object_id=object_id,
        changed_fields=list(changed_fields),
        values=degerler,
        record_mac="",
        label=label,
        anahtar=acik,
    )


def izinli_degerler(model: str, values: Mapping[str, Sequence[Any]] | None) -> dict[str, list[Any]]:
    """`values`'ı denetler ve kanonik ilkel biçime çevirir: yalnız izinli alanların çiftleri.

    İzin listesi dışındaki alan ya da `[önce, sonra]` olmayan değer `IzYazilamadi`'dır.
    Kilitli kipin geri yükleme notunda bekleyen olayları da yazılmadan önce buradan geçer.
    """
    izinli = _izinli_degerler(model)
    degerler: dict[str, list[Any]] = {}
    for ad, cift in (values or {}).items():
        if ad not in izinli:
            raise IzYazilamadi(f"{model} için {ad} alanının değeri denetim izine yazılamaz.")
        if isinstance(cift, str | bytes) or len(cift) != 2:
            raise IzYazilamadi("Denetim izi değeri [önce, sonra] çiftidir.")
        try:
            degerler[ad] = [kanonik.duz(cift[0]), kanonik.duz(cift[1])]
        except kanonik.KanonikHata as exc:
            raise IzYazilamadi(f"{model} için {ad} alanının değeri kanonik biçime girmez.") from exc
    return degerler


def kilitli_olay(
    eylem: str,
    *,
    model: str,
    object_id: str,
    muhur: KilitliMuhur,
    changed_fields: Iterable[str] = (),
    values: Mapping[str, Sequence[Any]] | None = None,
) -> AuditTrail:
    """Kilitli kip olayı (tasarım §4.6.3): kapalı kümedeki kişisiz `SISTEM` olayı.

    Mührü `apps.okul.iz_durumu` kurar (çapa ve tohum ya da mühürsüz satır); çağıranın
    işleminde ve `SISTEM` yazar bağlamında yazılır. İçerik MAC'i yoktur; kapalı küme dışı tür
    ya da hesap yazarı `IzYazilamadi`'dır (veritabanı kısıtı da reddeder).
    """
    return _ekle(
        eylem,
        model=model,
        object_id=object_id,
        changed_fields=list(changed_fields),
        values=izinli_degerler(model, values),
        record_mac="",
        label="",
        anahtar=muhur,
    )


#: `KVKK_SILME` satırının değerleri (tasarım §4.6.2 kural 4: "model, alan adları, adet, tetik;
#: değer yok"; §4.6.4: "silinen satır sayısı ve en yeni tarih"). Hepsi kişisizdir: silinen
#: kayıt SAYISI, silinenlerin en yenisinin GÜNÜ (an değil) ve silmeyi başlatan tetik.
KVKK_SILME_DEGERLERI: Final = ("adet", "en_yeni", "tetik")
#: Silmenin tetikleri — KAPALI KÜME. Bugün yalnız gün işi (erişim günlüğünün saklama süresi);
#: dönem kapanışının silmeleri (F4) ve kişi silme (5. adım) kendi tetikleriyle gelir.
KVKK_SILME_TETIKLERI: Final = ("GUN_ISI",)


def kvkk_silme(
    model: type[models.Model],
    *,
    adet: int,
    en_yeni: date,
    tetik: str,
    alanlar: Sequence[str] | None = None,
) -> AuditTrail:
    """KVKK silmesinin satırı (açık kip; tasarım §4.6.2 kural 4): değer YOK.

    Silmeyle AYNI işlemde çağrılır (yazma kuralı 1). `model` silinen kayıtların modelidir;
    `alanlar` silinen ya da boşaltılan alanların ADLARIDIR (`None`: bütün satır — kimlik
    dışındaki bütün alanlar). `values` yalnız `KVKK_SILME_DEGERLERI`'ni taşır: adet (pozitif
    tamsayı), en yeni silinen kaydın günü (saatsiz tarih) ve kapalı kümeden tetik. Toplu
    silmede tek bir kaydın kimliği yoktur: `object_id` boştur (silinen kayıtların kimlikleri
    satıra girmez). İçerik MAC'i yoktur: silinen kaydın özeti kalsaydı olasılık uzayı dar
    değer anahtarla yeniden bulunabilirdi (§4.6.2 "MAC dışı alanlar").
    """
    etiket = model_etiketi(model)
    try:
        kayitli = django_apps.get_model(etiket) is model
    except (LookupError, ValueError):
        kayitli = False
    if not kayitli:
        raise IzYazilamadi("KVKK silmesinin modeli kayıtlı bir model olmalıdır.")
    adlar = [alan.name for alan in _izli_alanlar(model)]
    secilen = adlar if alanlar is None else list(alanlar)
    if not secilen or not set(secilen) <= set(adlar) or len(set(secilen)) != len(secilen):
        raise IzYazilamadi(f"KVKK silmesinin alanları {etiket} modelinin alan adlarıdır.")
    if isinstance(adet, bool) or not isinstance(adet, int) or adet < 1:
        raise IzYazilamadi("KVKK silmesinin adedi pozitif bir tamsayıdır.")
    if isinstance(en_yeni, datetime) or not isinstance(en_yeni, date):
        raise IzYazilamadi("KVKK silmesinin en yeni kaydı saatsiz bir tarihtir.")
    if tetik not in KVKK_SILME_TETIKLERI:
        raise IzYazilamadi(f"Bilinmeyen KVKK silmesi tetiği: {tetik}")
    return _ekle(
        AuditAction.KVKK_SILME,
        model=etiket,
        object_id="",
        changed_fields=secilen,
        values={
            "adet": [None, adet],
            "en_yeni": [None, kanonik.duz(en_yeni)],
            "tetik": [None, tetik],
        },
        record_mac="",
        label="",
        anahtar=_bellekteki_anahtar(),
    )


def kilit_olayi(*, hesap_id: str, kim: Yazar) -> AuditTrail:
    """Oturumun kilitlenmesi: `KILIT` satırı, kendi işleminde, oturumun açık anahtarıyla.

    Oturum katmanı uçuştaki istekler bittikten sonra, DEK ve İA düşmeden önce çağırır
    (`oturum.OturumDurumu._kilidi_ize_yaz`); yazarı nedenden o seçer (elle ve arayüzdeki
    Çık'ın kapanışı: hesap; boşta ve öteki kapanışlar: `SISTEM`). Kaydın kimliği kilitlenen
    hesaptır.
    """
    with yazar_olarak(kim), transaction.atomic():
        return olay(AuditAction.KILIT, model=model_etiketi(Account), object_id=hesap_id)


def _ekle(
    eylem: str,
    *,
    model: str,
    object_id: str,
    changed_fields: list[str],
    values: dict[str, list[Any]],
    record_mac: str,
    label: str,
    anahtar: AcikAnahtar | KilitliMuhur,
) -> AuditTrail:
    """Çekirdek: yazar ve işlem denetimi, zincirin sonu, `seq`, MAC, ekleme (iki kip)."""
    if eylem not in AuditAction.values:
        raise IzYazilamadi(f"Bilinmeyen iz satırı türü: {eylem}")
    if label not in (*AuditLabel.values, ""):
        raise IzYazilamadi(f"Bilinmeyen iz satırı etiketi: {label}")
    if not all(isinstance(ad, str) for ad in changed_fields):
        raise IzYazilamadi("Değişen alanlar yalnız alan adlarıdır.")
    kim = yazar()
    if kim is None:
        raise IzYazilamadi("Yazar bağlamı olmayan yazma reddedilir (tasarım §4.6.2).")
    if not connection.in_atomic_block:
        raise IzYazilamadi("İz satırı veri satırıyla aynı işlemde yazılır; işlem dışında yazılmaz.")
    kancasi: Callable[[], None] | None = None
    if isinstance(anahtar, KilitliMuhur):
        # Kilitli kip (§4.6.3): yalnız kapalı kümedeki kişisiz SISTEM olayı, içerik MAC'siz.
        if eylem not in KILITLI_KIP_TURLERI:
            raise IzYazilamadi(f"Kilitliyken {eylem} yazılmaz (tasarım §4.6.3 kapalı küme).")
        if not kim.sistem_mi or record_mac:
            raise IzYazilamadi("Kilitli kip satırı yalnız SISTEM'in içerik MAC'siz olayıdır.")
        key_mode, key_ref = AuditKeyMode.KILITLI, anahtar.key_ref
        zincir_anahtari = anahtar.zincir_anahtari
        kancasi = anahtar.kaydetmeden_once
    else:
        key_mode, key_ref = AuditKeyMode.ACIK, str(anahtar.kayit_id)
        zincir_anahtari = crypto.audit_chain_key(anahtar.ia)
    hesap_id = None if kim.hesap_id is None else str(uuid.UUID(str(kim.hesap_id)))
    son = AuditTrail.objects.order_by("-seq").values_list("seq", "mac").first()
    seq = 1 if son is None else int(son[0]) + 1
    prev_mac = "" if son is None else str(son[1])
    satir = AuditTrail(
        seq=seq,
        at=timezone.now(),
        actor=AuditActor.SISTEM if hesap_id is None else AuditActor.HESAP,
        account_id=hesap_id,
        role="" if hesap_id is None else (kim.rol or ""),
        action=eylem,
        model=model,
        object_id=object_id,
        changed_fields=list(changed_fields),
        values=values,
        record_mac=record_mac,
        label=label,
        key_mode=key_mode,
        key_ref=key_ref,
        prev_mac=prev_mac,
    )
    satir.mac = kanonik.iz_mac(zincir_anahtari, satir_alanlari(satir), prev_mac)
    if kancasi is not None:
        # Kilitli kip: tohum dosyada satırdan ÖNCE ilerler (plan F1b-1; `KilitliMuhur`).
        kancasi()
    satir.save()
    return satir


def satir_alanlari(satir: AuditTrail) -> dict[str, Any]:
    """Satırın zincir MAC'inin kapsadığı alanlar (`kanonik.IZ_SATIRI_ALANLARI`).

    Yazımda ve doğrulamada aynı işlev kullanılır. `term` ve `compliance_item` F1c'ye dek
    `None`dır (sütunları yoktur; `AuditTrail` belge dizesi).
    """
    return {
        "seq": satir.seq,
        "at": satir.at,
        "actor": satir.actor,
        "account": _hesap_metni(satir.account_id),
        "role": satir.role,
        "action": satir.action,
        "model": satir.model,
        "object_id": satir.object_id,
        "term": None,
        "changed_fields": satir.changed_fields,
        "values": satir.values,
        "record_mac": satir.record_mac,
        "compliance_item": None,
        "label": satir.label,
        "key_mode": satir.key_mode,
        "key_ref": satir.key_ref,
    }


def _hesap_metni(deger: object) -> str | None:
    """Satırın hesap kimliğinin kanonik metni; UUID değilse `KanonikHata` (MAC tutmaz)."""
    if deger is None:
        return None
    try:
        return str(deger if isinstance(deger, uuid.UUID) else uuid.UUID(str(deger)))
    except ValueError as exc:
        raise kanonik.KanonikHata("Denetim izi satırının hesap kimliği UUID değil.") from exc


def _uuid_mu(deger: object) -> bool:
    try:
        _hesap_metni(deger)
    except kanonik.KanonikHata:
        return False
    return deger is not None


# ---------------------------------------------------------------------------
# Satırların okunması (doğrulama ve kartlar)
# ---------------------------------------------------------------------------
def satirlari_oku(sorgu: QuerySet[AuditTrail], *, adet: int | None = None) -> Iterator[AuditTrail]:
    """Sorgunun satırları; değeri yüzünden düşebilen sütun dönüşümleri OLMADAN (sırasıyla).

    Django hesap kimliğini (`account_id`) hedef UUID alanının, anı (`at`) tarih alanının
    dönüştürücüsüyle okur: program dışından yazılmış biçimsiz TEK bir değer (`"zzz"`; CHECK
    kısıtları bunu engellemez) satırı modele yüklerken hata yükseltir ve bütün sorguyu —
    kilit açılışındaki doğrulamayı da, Genel Bakış kartlarını da — düşürürdü. Bu iki sütun ham
    metin olarak okunur ve burada çevrilir; çevrilemeyen değer ham metin olarak kalır: satır
    kuralını (`satir_kurali_tutuyor`) ve MAC'ini (`mac_tutuyor`) tutmaz, bulgusu
    `satir_kurali` olur, karta çıkmaz. `adet` verilirse ilk `adet` satır okunur.
    """
    ham = sorgu.defer("account", "at").annotate(
        ham_hesap=Cast("account", output_field=models.TextField()),
        ham_an=Cast("at", output_field=models.TextField()),
    )
    if adet is not None:
        ham = ham[:adet]
    for satir in ham.iterator():
        satir.account_id = _ham_hesap(satir.ham_hesap)
        satir.at = _ham_an(satir.ham_an)
        yield satir


def _ham_hesap(ham: object) -> Any:
    """Ham hesap kimliği → `uuid.UUID`; boşsa None, biçimsizse ham metin (kural tutmaz)."""
    if ham is None:
        return None
    try:
        return uuid.UUID(str(ham))
    except ValueError:
        return str(ham)


def _ham_an(ham: object) -> Any:
    """Ham an → saat dilimli zaman (Django'nun SQLite dönüşümüyle aynı: saf değer bağlantının
    saat dilimindedir); çözülemezse ham metin (kural ve MAC tutmaz)."""
    if ham is None:
        return None
    metin = str(ham)
    try:
        an = parse_datetime(metin)
    except ValueError:
        return metin
    if an is None:
        return metin
    if timezone.is_naive(an):
        an = timezone.make_aware(an, connection.timezone)
    return an


# ---------------------------------------------------------------------------
# Doğrulama (kilit açılışı, DK'nin kayıt bütünlüğü denetimi, testler)
# ---------------------------------------------------------------------------
#: Zincir bulgularının kodları (iç kod; kullanıcı metnine çıkmaz).
SIRA_BOSLUGU: Final = "sira_boslugu"
ZINCIR_KOPUK: Final = "zincir_kopuk"
MAC_TUTMADI: Final = "mac_tutmadi"
ANAHTAR_YOK: Final = "anahtar_yok"
#: Mühürsüz kilitli satır (`iz-durumu.json` yokken yazıldı; zincire bağlı ama sırsız anahtarla).
MUHURSUZ: Final = "muhursuz"
#: Satır türünün ve kipinin kuralına uymuyor (`satir_kurali_tutuyor`): geçersiz kip, tür,
#: aktör ya da etiket; hesap/rol aktörle tutarsız; kilitli kipte kapalı küme dışı tür, hesap
#: yazarı ya da içerik MAC'i. Veritabanı kısıtları aynı kuralı zorlar, ama program DIŞINDAN
#: (kısıtlar kapatılarak — `PRAGMA ignore_check_constraints`) eklenen satırı ancak bu görür.
SATIR_KURALI: Final = "satir_kurali"

#: Satırın metin sütunları (`satir_kurali_tutuyor`: metin olmayan değer kuralı çiğner).
_METIN_SUTUNLARI: Final = (
    "actor",
    "role",
    "action",
    "model",
    "object_id",
    "record_mac",
    "label",
    "key_mode",
    "key_ref",
    "prev_mac",
    "mac",
)

#: Kilitli kip satırının zincir anahtarını veren işlev (varsayılanı veritabanından türetir).
KilitliAnahtar = Callable[[AuditTrail], bytes | None]

#: Bir çapadan türetilecek en çok adım: program dışından yazılmış bir `key_ref`
#: ("1:999999999") doğrulamayı dakikalarca SHA-256 döngüsünde tutmasın.
AZAMI_ADIM: Final = 100_000


# ---------------------------------------------------------------------------
# Kilitli kipin anahtarları (tasarım §4.6.3; modül başlığı "KİLİTLİ KİP")
# ---------------------------------------------------------------------------
def kilitli_ref(capa_seq: int, adim: int) -> str:
    """Kilitli kip satırının `key_ref`'i: `"<çapa seq>:<adım>"`."""
    return f"{capa_seq}:{adim}"


def kilitli_ref_coz(key_ref: object) -> tuple[int, int] | None:
    """`"<çapa seq>:<adım>"` → (çapa seq, adım); biçimsizse, metin değilse ya da sınır dışındaysa
    None."""
    if not isinstance(key_ref, str):
        return None
    parcalar = key_ref.split(":")
    if len(parcalar) != 2 or not all(p.isascii() and p.isdigit() for p in parcalar):
        return None
    capa_seq, adim = int(parcalar[0]), int(parcalar[1])
    if capa_seq < 1 or adim > AZAMI_ADIM:
        return None
    return capa_seq, adim


def acik_ref_coz(key_ref: object) -> int | None:
    """Açık kip `key_ref`'i → `AuditKey` kimliği; yalnız ASCII ondalık rakamsa, değilse None.

    `str.isdigit` tek başına yetmez: "²" ya da başka yazıların rakamları onu doğru yapar
    ama `int()` onları çeviremez. Program dışından yazılmış böyle bir başvuru doğrulamayı
    istisnayla yarıda kesmez, satırın bulgusu `anahtar_yok` olur (`kilitli_ref_coz` gibi).
    Metin olmayan değer de (ikili `b"1"`; `bytes.isdigit` doğrudur) başvuru değildir.
    """
    if not isinstance(key_ref, str) or not key_ref or not (key_ref.isascii() and key_ref.isdigit()):
        return None
    return int(key_ref)


def satir_kurali_tutuyor(satir: AuditTrail) -> bool:
    """Satır türünün ve kipinin kuralına uyuyor mu? (bulgu kodu `satir_kurali`)

    Veritabanı kısıtlarının (`AuditTrail.Meta.constraints`) ve yazıcının (`_ekle`) zorladığı
    kuralın doğrulamadaki eşi: kip `ACIK` ya da `KILITLI`; tür, aktör, etiket kapalı kümeden;
    `HESAP` satırında hesap ve rol dolu, `SISTEM` satırında ikisi de boş; kilitli kip satırı
    yalnız kapalı kümedeki (`KILITLI_KIP_TURLERI`) içerik MAC'siz bir `SISTEM` olayıdır.
    Tasarım §4.6.3'ün kalan riski ("dosyayı okuyan kişi o andan sonraki kilitli satırları
    taklit edebilir; bu satırlar veri değiştirmez") bu kurala dayanır: kural zorlanmasaydı
    herkesin bildiği mühürsüz anahtarla sahte bir `GIRIS` ya da `GERI_YUKLEME` satırı geçerli
    sayılırdı. Hesap kimliği UUID, an saat dilimli zaman olmalıdır (program dışından yazılmış
    biçimsiz değer; `satirlari_oku` onu ham metin olarak bırakır). Sıra tamsayı, metin
    sütunları metin olmalıdır: program yalnız metin yazar; SQLite metin sütununa program
    dışından yazılmış ikili değeri (BLOB) çevirmeden saklar.
    """
    if isinstance(satir.seq, bool) or not isinstance(satir.seq, int):
        return False
    if not all(isinstance(getattr(satir, ad), str) for ad in _METIN_SUTUNLARI):
        return False
    if satir.key_mode not in AuditKeyMode.values:
        return False
    if satir.action not in AuditAction.values or satir.actor not in AuditActor.values:
        return False
    if satir.label not in (*AuditLabel.values, ""):
        return False
    if not isinstance(satir.at, datetime):
        return False
    if satir.actor == AuditActor.HESAP:
        if not _uuid_mu(satir.account_id) or not satir.role:
            return False
    elif satir.account_id is not None or satir.role:
        return False
    if satir.key_mode == AuditKeyMode.KILITLI:
        return (
            satir.action in KILITLI_KIP_TURLERI
            and satir.actor == AuditActor.SISTEM
            and not satir.record_mac
        )
    return True


def kilitli_tohum(ia: bytes, capa_seq: int, capa_mac: str) -> bytes:
    """`tohum₀ = HKDF(İA, "od-iz-kilitli/v1", tuz = seq ‖ mac)` (tasarım §4.6.3)."""
    return crypto.audit_locked_seed(ia, kanonik.capa_baytlari(capa_seq, capa_mac))


def sirayi_muhurleyen_ia(seq: int) -> bytes | None:
    """`seq` satırını mühürleyen iz anahtarı: `valid_from_seq`'i ona eşit ya da küçük en yeni İA.

    Çapanın mührü ve kilitli kip tohumu çapanın satırını mühürleyen İA'yla hesaplanır (DEK
    yenilemesinden önceki çapalar eski İA'yla doğrulanır; F4). Bellekteki DEK'le çözülür;
    DEK yoksa `IzAnahtariBellekteDegil`, kayıt yoksa ya da çözülemezse None.
    """
    dek = crypto.active_key()
    if dek is None:
        raise IzAnahtariBellekteDegil()
    token = (
        AuditKey.objects.filter(valid_from_seq__lte=seq)
        .order_by("-valid_from_seq")
        .values_list(Cast("key", output_field=models.TextField()), flat=True)
        .first()
    )
    if not token:
        return None
    try:
        return _token_coz(dek, str(token))
    except IzAnahtariOkunamadi:
        return None


def _capa_tohumu(capa_seq: int) -> bytes | None:
    """Veritabanındaki çapa satırından `tohum₀`; satır ya da İA yoksa None."""
    mac = AuditTrail.objects.filter(seq=capa_seq).values_list("mac", flat=True).first()
    if mac is None:
        return None
    ia = sirayi_muhurleyen_ia(capa_seq)
    if ia is None:
        return None
    try:
        return kilitli_tohum(ia, capa_seq, str(mac))
    except kanonik.KanonikHata:
        return None


def kilitli_zincir_anahtarlari() -> KilitliAnahtar:
    """Kilitli kip satırının zincir anahtarı, yalnız veritabanından ve bellekteki DEK'ten.

    `key_ref = "<çapa seq>:<k>"`: çapanın satırının `mac`'i ve onu mühürleyen İA `tohum₀`'ı
    verir, `k` kez ileri alınır, `HKDF(tohumₖ, "od-iz-kilitli-mac/v1")`. Mühürsüz satır
    (`key_ref` boş) sırsız anahtarla zincire bağlıdır (`kanonik.MUHURSUZ_ANAHTAR`); onu
    `zinciri_dogrula` ayrıca `muhursuz` bulgusuyla gösterir. Biçimsiz `key_ref` ya da
    bulunamayan çapa satırı None'dır (`anahtar_yok`). Tohumlar çağrı boyunca önbellektedir.
    """
    tohumlar: dict[int, list[bytes] | None] = {}

    def coz(satir: AuditTrail) -> bytes | None:
        if satir.key_ref == "":
            return kanonik.MUHURSUZ_ANAHTAR
        ref = kilitli_ref_coz(satir.key_ref)
        if ref is None:
            return None
        capa_seq, adim = ref
        if capa_seq not in tohumlar:
            ilk = _capa_tohumu(capa_seq)
            tohumlar[capa_seq] = None if ilk is None else [ilk]
        liste = tohumlar[capa_seq]
        if liste is None:
            return None
        while len(liste) <= adim:
            liste.append(kanonik.ileri_tohum(liste[-1]))
        return crypto.audit_locked_mac_key(liste[adim])

    return coz


@dataclass(frozen=True)
class ZincirBulgusu:
    """Zincir doğrulamasının bir bulgusu: hangi satır, hangi tür (iç kod)."""

    seq: int
    kod: str


def _acik_zincir_anahtarlari() -> Callable[[AuditTrail], bytes | None]:
    """Açık kip satırının zincir anahtarı: `key_ref`'teki `AuditKey`, bellekteki DEK'le."""
    dek = crypto.active_key()
    if dek is None:
        raise IzAnahtariBellekteDegil()
    onbellek: dict[str, tuple[bytes, int] | None] = {}

    def coz(satir: AuditTrail) -> bytes | None:
        if satir.key_ref not in onbellek:
            onbellek[satir.key_ref] = None
            kayit_id = acik_ref_coz(satir.key_ref)
            if kayit_id is not None:
                kayit = (
                    AuditKey.objects.filter(pk=kayit_id)
                    .values_list(Cast("key", output_field=models.TextField()), "valid_from_seq")
                    .first()
                )
                if kayit is not None and kayit[0]:
                    try:
                        ia = _token_coz(dek, str(kayit[0]))
                    except IzAnahtariOkunamadi:
                        ia = None
                    if ia is not None:
                        onbellek[satir.key_ref] = (crypto.audit_chain_key(ia), int(kayit[1]))
        bulunan = onbellek[satir.key_ref]
        if bulunan is None or satir.seq < bulunan[1]:
            return None
        return bulunan[0]

    return coz


def zinciri_dogrula(
    *,
    ilk: int | None = None,
    son: int | None = None,
    kilitli_anahtar: KilitliAnahtar | None = None,
) -> list[ZincirBulgusu]:
    """`[ilk, son]` aralığındaki satırların zincirini doğrular; bulguları döndürür.

    Her satırda: sıra boşluksuz mu, `prev_mac` bir önceki satırın `mac`'i mi (aralığın ilk
    satırında aralık dışındaki önceki satır okunur; `seq = 1` ise `prev_mac` boştur), MAC
    satırın alanlarından ve anahtarından yeniden hesaplanınca tutuyor mu. Açık kip
    satırının anahtarı `key_ref`'teki iz anahtarıdır (bellekteki DEK'le çözülür; DEK
    yoksa `IzAnahtariBellekteDegil`). Kilitli kip satırının anahtarını `kilitli_anahtar`
    verir (verilmezse veritabanından türetilir, `kilitli_zincir_anahtarlari`); anahtar
    bulunamazsa bulgu `anahtar_yok`'tur. Mühürsüz kilitli satır zincire bağlı olsa da
    `muhursuz` bulgusudur. Kipi ne `ACIK` ne `KILITLI` olan satır kilitli SAYILMAZ: anahtarı
    yoktur (`anahtar_yok`). Her satırın türü ve kipi kuralına uymalıdır (`satir_kurali`;
    `satir_kurali_tutuyor`): MAC'i tutan satır da kuralı çiğniyorsa bulgudur. Satırlar
    sütun dönüşümü düşmeden okunur (`satirlari_oku`): biçimsiz bir hesap kimliği ya da an
    doğrulamayı yarıda kesmez, o satırın bulgusu olur. Metin sütununa yazılmış ikili değer
    (`mac`, `prev_mac` BLOB'u) de öyle: hiçbir mühre eşit değildir (`kanonik.esit`). Bir
    satırın denetimi bunlar dışında beklenmeyen bir hata verirse (program dışından yazılmış
    başka bir biçim) o satırın bulgusu `satir_kurali` olur ve denetim sürer: önceki ve sonraki
    satırların bulguları kaybolmaz. Veritabanı hatası ve bellekte olmayan anahtar yükselir.
    """
    acik_anahtar = _acik_zincir_anahtarlari()
    if kilitli_anahtar is None:
        kilitli_anahtar = kilitli_zincir_anahtarlari()
    sorgu = AuditTrail.objects.order_by("seq")
    if ilk is not None:
        sorgu = sorgu.filter(seq__gte=ilk)
    if son is not None:
        sorgu = sorgu.filter(seq__lte=son)
    bulgular: list[ZincirBulgusu] = []
    onceki: tuple[int, str] | None = None
    for satir in satirlari_oku(sorgu):
        try:
            bulgular.extend(_satirin_bulgulari(satir, onceki, acik_anahtar, kilitli_anahtar))
        except (DatabaseError, crypto.KeyMissingError):
            raise
        except Exception:  # noqa: BLE001 — biçimsiz satır doğrulamayı kesmez, bulgusu olur
            logger.warning(
                "Denetim izinin bir satırı denetlenirken beklenmeyen hata; satır kuralı "
                "bulgusu sayıldı.",
                exc_info=True,
            )
            bulgular.append(ZincirBulgusu(satir.seq, SATIR_KURALI))
        onceki = (satir.seq, satir.mac)
    return bulgular


def _satirin_bulgulari(
    satir: AuditTrail,
    onceki: tuple[int, str] | None,
    acik_anahtar: Callable[[AuditTrail], bytes | None],
    kilitli_anahtar: KilitliAnahtar,
) -> list[ZincirBulgusu]:
    """Bir satırın zincir bulguları (`zinciri_dogrula`); `onceki` bir önceki satırın (seq, mac)."""
    bulgular: list[ZincirBulgusu] = []
    beklenen: str | None
    if onceki is not None:
        if satir.seq != onceki[0] + 1:
            bulgular.append(ZincirBulgusu(satir.seq, SIRA_BOSLUGU))
        beklenen = onceki[1]
    elif satir.seq == 1:
        beklenen = ""
    else:
        ust = AuditTrail.objects.filter(seq=satir.seq - 1).values_list("mac", flat=True).first()
        if ust is None:
            bulgular.append(ZincirBulgusu(satir.seq, SIRA_BOSLUGU))
        beklenen = ust
    if beklenen is not None and not kanonik.esit(satir.prev_mac, beklenen):
        bulgular.append(ZincirBulgusu(satir.seq, ZINCIR_KOPUK))
    anahtar: bytes | None = None
    if satir.key_mode == AuditKeyMode.ACIK:
        anahtar = acik_anahtar(satir)
    elif satir.key_mode == AuditKeyMode.KILITLI:
        anahtar = kilitli_anahtar(satir)
        if satir.key_ref == "":
            bulgular.append(ZincirBulgusu(satir.seq, MUHURSUZ))
    if not satir_kurali_tutuyor(satir):
        bulgular.append(ZincirBulgusu(satir.seq, SATIR_KURALI))
    if anahtar is None:
        bulgular.append(ZincirBulgusu(satir.seq, ANAHTAR_YOK))
    elif not mac_tutuyor(anahtar, satir):
        bulgular.append(ZincirBulgusu(satir.seq, MAC_TUTMADI))
    return bulgular


def mac_tutuyor(anahtar: bytes, satir: AuditTrail) -> bool:
    """Satırın MAC'i alanlarından yeniden hesaplanınca tutuyor mu? Biçimi bozuk satır tutmaz."""
    try:
        beklenen = kanonik.iz_mac(anahtar, satir_alanlari(satir), satir.prev_mac)
    except kanonik.KanonikHata:
        return False
    return kanonik.esit(satir.mac, beklenen)


def acik_satir_dogrulayici() -> Callable[[AuditTrail], bool]:
    """Kartların okuduğu satırın süzgeci: açık kipte mi, kuralına uyuyor mu, MAC'i tutuyor mu?

    Genel Bakış kartları ("Son Girişler", bütünlük, geri yükleme) ve parola yenilenme
    bildirimi yalnız İA ile mühürlenmiş satırlardan beslenir: kilitli kip satırı ya da
    sırsız anahtarla (mühürsüz) eklenmiş satır sahte bir giriş, bulgu ya da geri yükleme
    gösteremez. Satırın kendi MAC'i, `key_ref`'teki iz anahtarıyla doğrulanır (bellekteki
    DEK'le; DEK yoksa `IzAnahtariBellekteDegil`); zincir bağı (3). denetimin işidir. Süzgeç
    çağrı boyunca anahtarları önbellekte tutar. Program dışından yazılmış biçimsiz bir satır
    (metin sütununda ikili değer…) kartı düşürmez: süzgeçten geçmez, atlanır (beklenmeyen bir
    hata da öyle; `zinciri_dogrula` onu bulgu olarak gösterir). Veritabanı hatası ve bellekte
    olmayan anahtar yükselir.
    """
    acik_anahtar = _acik_zincir_anahtarlari()

    def gecerli(satir: AuditTrail) -> bool:
        try:
            if satir.key_mode != AuditKeyMode.ACIK or not satir_kurali_tutuyor(satir):
                return False
            anahtar = acik_anahtar(satir)
            return anahtar is not None and mac_tutuyor(anahtar, satir)
        except (DatabaseError, crypto.KeyMissingError):
            raise
        except Exception:  # noqa: BLE001 — biçimsiz satır kartı düşürmez, süzgeçten geçmez
            logger.warning(
                "Denetim izinin bir satırı kart için denetlenirken beklenmeyen hata; satır "
                "atlandı.",
                exc_info=True,
            )
            return False

    return gecerli


def son_satirlari_dogrula(
    adet: int = 200, *, kilitli_anahtar: KilitliAnahtar | None = None
) -> list[ZincirBulgusu]:
    """Son `adet` satırın zinciri (kilit açılışındaki kendiliğinden doğrulama, §4.6.3 (3))."""
    bas = zincir_basi()
    if bas is None:
        return []
    return zinciri_dogrula(ilk=max(1, bas[0] - adet + 1), kilitli_anahtar=kilitli_anahtar)


def zincir_basi() -> tuple[int, str] | None:
    """Zincirin son satırı: (`seq`, `mac`); iz boşsa None (kâğıt çapasının kaynağı, §4.6.3)."""
    son = AuditTrail.objects.order_by("-seq").values_list("seq", "mac").first()
    return None if son is None else (int(son[0]), str(son[1]))


def kaydi_dogrula(model: type[models.Model], pk: Any) -> bool | None:
    """Kayıt bütünlüğü: bugünkü değerden içerik MAC'i, o kaydın son MAC'li iz satırına eşit mi?

    Program dışından yapılan değişiklik, şifreli sütuna yazılmış düz metin ve bir satırdan
    ötekine taşınmış Fernet token'ı burada görünür (tasarım §4.6.2; denetim GA-9). Kaydın
    içerik MAC'li iz satırı yoksa None. Doğrulama, satırı mühürleyen iz anahtarıyla yapılır.
    Denetleme Kurulunun (DK modülü, F4) ve testlerin denetimidir; hesap satırının GİRİŞTEKİ katı
    eşi `hesap_izi_tutuyor`'dur (iz satırı yoksa False, okunan satırların zincir MAC'i de doğrulanır).
    """
    son = (
        AuditTrail.objects.filter(model=model_etiketi(model), object_id=kimlik_metni(model, pk))
        .exclude(record_mac="")
        .order_by("-seq")
        .values_list("record_mac", "key_ref")
        .first()
    )
    if son is None:
        return None
    dek = crypto.active_key()
    if dek is None:
        raise IzAnahtariBellekteDegil()
    kayit_id = acik_ref_coz(str(son[1]))
    token = (
        AuditKey.objects.filter(pk=kayit_id)
        .values_list(Cast("key", output_field=models.TextField()), flat=True)
        .first()
        if kayit_id is not None
        else None
    )
    if not token or kayit_id is None:
        return False
    try:
        ia = _token_coz(dek, str(token))
    except IzAnahtariOkunamadi:
        return False
    anahtar = AcikAnahtar(ia=ia, kayit_id=kayit_id)
    try:
        guncel = kayit_mac_hesapla(model, pk, anahtar=anahtar)
    except ObjectDoesNotExist:
        return False
    return kanonik.esit(str(son[0]), guncel)


def hesap_izi_tutuyor(
    hesap_id: Any, *, veri_anahtari: bytes, beklenen_muhur: str | None = None
) -> bool:
    """Hesap satırı denetim izindeki son içerik MAC'li kaydını tutuyor mu? (kullanıcı kararı
    03.11.2026 "Girişte reddet"; `app_password` modül başlığı "SATIRIN İZİ")

    `kaydi_dogrula`'nın hesap satırı için GİRİŞTE kullanılan katı eşidir: karar ORM'siz tek
    işlevdedir (`services.satir_izi.hesap_izi_tutuyor`; geri yüklemenin parola yolu da onu
    çağırır), burada Django'nun bağlantısı verilir — açık bir işlemin içindeyse işlemin
    gördüğünü görür, değilse okumalar tek bir okuma işleminde (tek anlık görüntü) yapılır. DEK
    açıkça verilir: kilit açılışında henüz belleğe alınmamıştır (aday DEK, tasarım §4.6.3).
    `beklenen_muhur`: çağıranın ORM'le okuyup kararı verdiği satırın mührü; ham okumadaki mühür
    ona eşit değilse False (`satir_izi` modül başlığı adım 5). `kaydi_dogrula`'dan farkı: içerik
    MAC'li iz satırı yoksa None değil False'tur (fail-closed) ve okunan her iz satırının sırasının
    türü ve kendi zincir MAC'i de doğrulanır (son satırın `record_mac`'ini boşaltmak, `key_ref`'ini
    değiştirmek ya da eski bir satırın sırasını BLOB'a çevirmek denetimi eski bir satıra
    kaydırmasın).
    """
    connection.ensure_connection()
    return satir_izi.hesap_izi_tutuyor(
        connection.connection, hesap_id, veri_anahtari, beklenen_muhur=beklenen_muhur
    )


def _reset_for_tests() -> None:
    """Yalnız testler için: anahtar doğrulama önbelleği testler arasında sızmasın."""
    global _dogrulanan
    with _dogrulama_kilidi:
        _dogrulanan = None
