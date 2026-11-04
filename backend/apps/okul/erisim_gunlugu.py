"""Erişim günlüğü: yazıcı ve saklama süresinin silmesi (tasarım §4.6.4; plan F1b-1 (d)).

Hassas okumanın ve kişisel veri içeren çıktının kaydıdır (KVKK md. 12 güvenlik tedbiri;
model `AccessLog`). ZİNCİR DIŞIDIR (denetim izine bağlı değildir, mühürlenmez), şifresizdir,
okunan değeri tutmaz; süresi dolunca silinir ve silmenin kendisi denetim izine düşer.

YAZICI (`yaz`) — TEK giriş noktası (kaynakta kökü `AccessLog` olan her yazım zinciri yalnız
burada, silme zinciri yalnız `suresi_dolanlari_sil`'de durur; `test_erisim_gunlugu.py`):

* Okuyan hesap ve rol yazar bağlamından gelir (`oturum.yazar()`; istek başında ara katman
  kurar). Bağlam yoksa ya da yazar `SISTEM`'se ret: günlük bir HESABIN okumasının kaydıdır,
  programın kendi işi okuma sayılmaz.
* Tür kapalı kümedendir (`AccessKind`). `model`, `object_id`, `field` kimlik biçimindedir:
  kayıtlı bir modelin sınıfı, o modelin kimliği olabilen değer (alanın `to_python`'undan
  geçer; tireli UUID ya da ondalık sayı metnine iner), modelin somut alanının adı. Serbest
  metin ve değer kabul edilmez; okunan değer hiçbir sütuna girmez.
* Çıktıda belgenin sha256'sı (64 küçük onaltılık hane) ve satır sayısı BİRLİKTE verilir.
  Alan düzeyindeki türler (maskesiz T.C. kimlik no, özel nitelikli alan) alan adı ister;
  tanımı gereği çıktı olan türler (veli listesi çıktısı, kişisel veri dışa aktarımı) çıktı
  özeti ister; maskesiz T.C. kimlik no hiçbir dosyaya girmediği için (§5.3) çıktı özeti
  taşıyamaz. Anı yazıcı koyar.
* KULLANIM: hassas okuma ya da çıktı satır YAZILDIKTAN sonra verilir; yazılamazsa (ret,
  veritabanı hatası) verilmez (fail-closed). Çağıranın işlemindeyse onunla birlikte geri
  alınır.

SİLME (`suresi_dolanlari_sil`; gün işi `gun_isi`, kayıt `gun_isini_kaydet`):

* Saklama süresi `SAKLAMA_SURESI_YIL` takvim yılıdır, SABİTTİR (§15 B-9 DOĞRULANMADI;
  mevzuat hükmü değil programın varsayılanı olduğu için kural paketine girmez — plan F1b-1).
  Satır, gününün yıl dönümü BİTTİKTEN sonraki ilk gün işinde silinir (`saklama_siniri`).
* Tek `IMMEDIATE` işlemde süresi dolan satırlar silinir ve denetim izine `KVKK_SILME` satırı
  yazılır (`denetim_izi.kvkk_silme`: model `okul.AccessLog`, alan adları, adet, silinen en
  yeni satırın günü, tetik `GUN_ISI`; değer ve kişi yok). Silinecek satır yoksa iz satırı da
  yoktur. Yazar `SISTEM`'dir.
* DEK ya da İA bellekte değilse (kilitli) hiçbir şey okunmaz ve yazılmaz;
  `IzAnahtariBellekteDegil` (`KeyMissingError`) yükselir. Gün kapısının sarmalayıcısı bunu
  "ertelendi" sayar ve `GUN_ISI` satırını yazar (`masaustu_kanca._sistem_adina`); iş kilit
  açılışının sinyaliyle (`masaustu_kanca.ertelenen_gun_islerini_dene`) ve saatlik denemeyle
  yeniden koşar (TK19, tasarım §4.4.3 sırası).
* Kilit, oturumun kilitlenmesi ve kilit açılışıyla aynı yöndedir: `IZ_KIP_KILIDI` →
  veritabanı. Anahtarların bellekte olup olmadığı o kilidin altında okunur; `KILIT` satırı,
  çapa ve anahtarların düşmesi bu işin ortasına girmez.

ENVANTER (02.11.2026). Bugün kodda tasarımın hassas okuma türlerinden birine AÇIKÇA uyan yol
yoktur; yazıcı bu yüzden hiçbir uca bağlı değildir. Kişisel veriye dokunan bugünkü yollar:
öğrenci ve personel listesi ve ayrıntısı, ayrılış havuzu (olağan okuma; tasarımın "okuma ≠
hassas detay" ayrımında okuma), içe aktarma önizlemesi (kullanıcının yüklediği dosyanın
işlenmesi; programın verisinin çıktısı değildir), boş şablonlar ve kurtarma anahtarı belgesi
(kişisel veri yok), şifreli yedek indirme (bütün veritabanı, şifreli; tasarımda "Güvenlik"
satırındadır, izi denetim izinde `YEDEK` satırıdır — erişim günlüğü türlerinde yoktur).
T.C. kimlik no (K9, F3), veli listesi ve adlı E07/E08 (F2), kişi dökümü ve ihlal dökümü,
özel nitelikli alan ve ek (F1c-F5) henüz yoktur; o okumaları getiren adımlar bu yazıcıya
bağlar.

OKUMA (`liste`; ucu `GET access-log/`, `views_erisim_gunlugu`; plan F1b-2 "Erişim günlüğü okuma
ucu"; tasarım §4.6.4 "Okuyan: yonetici ve DK"):

* Yalnız program yöneticisi ve Denetleme Kurulu: rol kapısının (matrisin "Erişim günlüğü"
  satırı, `rol_izinleri.Satir.ERISIM_GUNLUGU`) ardından servis de yazarın rolünü aynı satırın
  okuyabilen rolleriyle sınar (derin savunma; satırın Y hücresi olmadığı için eylem değildir).
  Yazar yoksa ya da `SISTEM` ise ret (`RolYetkisiz`).
* Süzgeçler: tarih aralığı (iki uç dahil; gün Europe/Istanbul'a göredir: başlangıç gününün
  00.00'ından bitiş gününün ertesi 00.00'ına dek), tür (`AccessKind`), okuyan hesap. Sayfalıdır
  (`SAYFA_BOYUTU`), en yeni önce gelir.
* KİŞİSİZDİR: okuyan hesap rol etiketi (sıra no'suz, satırdaki rolden) ve tanıtıcıyla anılır;
  ad-soyad (şifreli `display_name`) okunmaz. Okunan kaydın kimliği satırda olduğu gibidir (model,
  kimlik, alan adı; değer yoktur — yazıcı tutmaz). Tanıtıcı yalnız açık hesaplar arasında tekil
  olduğundan hesabın açılış ve kapanış günü de verilir (`acilis`, `kapanis`; Europe/Istanbul günü,
  yyyy-aa-gg; açık hesapta `kapanis` None): kapanan hesapla aynı tanıtıcıyı alan yeni hesap
  satırlarda ve hesap seçeneklerinde ayrılır (orkestratör maddesi F-3; `iz_dogrulama` kartlarındaki
  hesap özetiyle aynı karar).
* OKUMA İZ BIRAKMAZ: ne denetim izine ne erişim günlüğüne satır yazar (günlüğü okumak tasarımın
  hassas okuma türlerinden değildir; §4.6.4). DEK istemez (tablo şifresizdir); uç yalnız açık
  oturumdadır (kilit kapısı).
* Türlerin görünen adları `TUR_ADLARI`'ndadır (sözlük §1 "Erişim günlüğü (F1b)"); özel nitelikli
  türlerde KVKK md. 6/1'in sözü ("özel nitelikli kişisel veri") kullanılır.
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Mapping
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Final

from django.apps import apps as django_apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone

from apps.okul import denetim_izi, masaustu_kanca, rol_izinleri
from apps.okul.models import AccessKind, AccessLog, Account, AccountRole
from apps.okul.oturum import (
    IZ_KIP_KILIDI,
    ham_an_sutunlari,
    hesap_ani,
    hesap_gunu,
    rol_etiketi,
    sistem_olarak,
    yazar,
)
from shared import crypto
from shared.exceptions import RolYetkisiz

logger = logging.getLogger("oab_defteri.okul")

#: Erişim günlüğünün saklama süresi (takvim yılı) — tasarım §4.6.4, §15 B-9: öneri,
#: DOĞRULANMADI. Mevzuat hükmü değil programın varsayılanıdır; kural paketine GİRMEZ (plan
#: F1b-1 "Erişim günlüğü"). Değişirse yalnız burası değişir (`AccessLog` belge dizesi).
SAKLAMA_SURESI_YIL: Final = 2

#: Gün değişimi kapısındaki işin adı (ASCII); ertelemenin `GUN_ISI` satırının kimliği de budur.
SILME_ISI: Final = "erisim-gunlugu-silme"

#: KVKK silmesinin tetiği (`denetim_izi.KVKK_SILME_TETIKLERI`).
_TETIK: Final = "GUN_ISI"

#: Alan düzeyindeki okumalar: okunan alanın adı zorunludur.
_ALAN_ISTEYEN: Final = frozenset({AccessKind.MASKESIZ_TCKN, AccessKind.OZEL_NITELIKLI_ALAN})
#: Tanımı gereği çıktı olan türler: belgenin sha256'sı ve satır sayısı zorunludur.
_CIKTI_OLAN: Final = frozenset({AccessKind.VELI_LISTESI_CIKTISI, AccessKind.KISISEL_DISA_AKTARIM})
#: Hiçbir dosyaya girmeyen okuma (T.C. kimlik no; tasarım §5.3): çıktı özeti taşıyamaz.
_CIKTISIZ: Final = frozenset({AccessKind.MASKESIZ_TCKN})

_SHA256: Final = re.compile(r"[0-9a-f]{64}")
#: `object_id` sütununun sınırı (`AccessLog.object_id`).
_KIMLIK_SINIRI: Final = 64


class ErisimGunluguYazilamadi(RuntimeError):
    """Erişim günlüğü satırı yazılamadı (ret); hassas okuma ve çıktı verilmez (modül başlığı)."""


# ---------------------------------------------------------------------------
# Yazıcı
# ---------------------------------------------------------------------------
def _model_kimligi(
    model: type[models.Model] | None, object_id: object, field: str
) -> tuple[str, str, str]:
    """(model etiketi, kimlik metni, alan adı); kimlik biçiminde değilse ret."""
    if model is None:
        if object_id is not None or field:
            raise ErisimGunluguYazilamadi("Kayıt kimliği ve alan adı yalnız bir modelle verilir.")
        return "", "", ""
    if not (isinstance(model, type) and issubclass(model, models.Model)):
        raise ErisimGunluguYazilamadi("Model, kayıtlı bir modelin sınıfıdır.")
    etiket = denetim_izi.model_etiketi(model)
    try:
        kayitli = django_apps.get_model(etiket) is model
    except (LookupError, ValueError):
        kayitli = False
    if not kayitli:
        raise ErisimGunluguYazilamadi("Model, kayıtlı bir modelin sınıfıdır.")
    kimlik = ""
    if object_id is not None:
        aday = (
            None
            if isinstance(object_id, bool)
            else denetim_izi.kimlik_metni_ya_da_none(model, object_id)
        )
        if aday is None or len(aday) > _KIMLIK_SINIRI:
            raise ErisimGunluguYazilamadi(f"Kayıt kimliği {etiket} modelinin kimliği olmalıdır.")
        kimlik = aday
    if field:
        if not kimlik:
            raise ErisimGunluguYazilamadi("Alan adı yalnız bir kayıt kimliğiyle verilir.")
        try:
            alan = model._meta.get_field(field)
        except FieldDoesNotExist:
            alan = None
        if alan is None or not getattr(alan, "concrete", False) or alan.name != field:
            raise ErisimGunluguYazilamadi(f"Alan adı {etiket} modelinin bir alanı olmalıdır.")
    return etiket, kimlik, field


def _cikti_ozeti(document_sha256: str, row_count: int | None) -> tuple[str, int | None]:
    """(sha256, satır sayısı): ikisi birlikte ya da hiçbiri; biçimsizse ret."""
    if document_sha256 == "" and row_count is None:
        return "", None
    if not isinstance(document_sha256, str) or _SHA256.fullmatch(document_sha256) is None:
        raise ErisimGunluguYazilamadi(
            "Çıktının özeti 64 küçük onaltılık haneli sha256'dır ve satır sayısıyla verilir."
        )
    if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 0:
        raise ErisimGunluguYazilamadi("Çıktının satır sayısı negatif olmayan bir tamsayıdır.")
    return document_sha256, row_count


def yaz(
    kind: str,
    *,
    model: type[models.Model] | None = None,
    object_id: object = None,
    field: str = "",
    document_sha256: str = "",
    row_count: int | None = None,
) -> AccessLog:
    """Hassas okumanın ya da kişisel veri içeren çıktının satırı (kurallar modül başlığında).

    Okuyan hesap ve rol yazar bağlamındandır; ret `ErisimGunluguYazilamadi`'dır. Satırı
    döndürür.
    """
    kim = yazar()
    if kim is None:
        raise ErisimGunluguYazilamadi("Yazar bağlamı olmayan okuma kaydedilemez.")
    if kim.sistem_mi:
        raise ErisimGunluguYazilamadi(
            "Erişim günlüğü okuyan hesabın kaydıdır; program adına yazılmaz."
        )
    if kim.rol not in AccountRole.values:
        raise ErisimGunluguYazilamadi("Okuyan hesabın rolü bilinmiyor.")
    try:
        hesap_id = uuid.UUID(str(kim.hesap_id))
    except ValueError as exc:
        raise ErisimGunluguYazilamadi("Okuyan hesabın kimliği biçimsiz.") from exc
    if not isinstance(kind, str) or kind not in AccessKind.values:
        raise ErisimGunluguYazilamadi("Bilinmeyen erişim günlüğü türü.")
    tur = AccessKind(kind)
    etiket, kimlik, alan = _model_kimligi(model, object_id, field)
    ozet, sayi = _cikti_ozeti(document_sha256, row_count)
    if tur in _ALAN_ISTEYEN and not alan:
        raise ErisimGunluguYazilamadi("Bu tür okunan alanın adını ister.")
    if tur in _CIKTI_OLAN and not ozet:
        raise ErisimGunluguYazilamadi("Bu tür çıktının özetini ve satır sayısını ister.")
    if tur in _CIKTISIZ and ozet:
        raise ErisimGunluguYazilamadi("Maskesiz T.C. kimlik no hiçbir dosyaya girmez.")
    return AccessLog.objects.create(
        at=timezone.now(),
        account_id=hesap_id,
        role=kim.rol,
        kind=tur.value,
        model=etiket,
        object_id=kimlik,
        field=alan,
        document_sha256=ozet,
        row_count=sayi,
    )


# ---------------------------------------------------------------------------
# Saklama süresinin silmesi
# ---------------------------------------------------------------------------
def saklama_siniri(bugun: date) -> date:
    """`bugun`'kü silmenin sınırı: günü bundan ÖNCE olan satırın süresi dolmuştur.

    Satırın yıl dönümü, gününün `SAKLAMA_SURESI_YIL` takvim yılı sonraki karşılığıdır;
    29 Şubat'ın karşılığı olmayan yılda 28 Şubat'tır. Satır yıl dönümü günü durur, ertesi
    günkü işte silinir: süre hiçbir satırda kısalmaz. Sınır bu yüzden iki yıl önceki aynı
    gündür; `bugun` 29 Şubat'sa ve iki yıl önce o gün yoksa 1 Mart'tır (28 Şubat'ın satırı
    yıl dönümünü dün bitirdi).
    """
    try:
        return bugun.replace(year=bugun.year - SAKLAMA_SURESI_YIL)
    except ValueError:  # 29 Şubat; iki yıl önce artık yıl değil
        return date(bugun.year - SAKLAMA_SURESI_YIL, 3, 1)


def suresi_dolanlari_sil(*, bugun: date | None = None) -> int:
    """Saklama süresi dolan satırları siler ve `KVKK_SILME` satırını yazar; silinen sayı.

    Kurallar modül başlığında ("SİLME"). `bugun` verilmezse yerel gündür (Europe/Istanbul);
    bugünden SONRAKİ bir gün verilemez (süresi dolmamış satır silinmesin). Kilitliyse
    `denetim_izi.IzAnahtariBellekteDegil`.
    """
    simdi = timezone.localdate()
    gun = simdi if bugun is None else bugun
    if gun > simdi:
        raise ValueError("Silme günü bugünden sonra olamaz: süresi dolmamış satır silinmez.")
    sinir = timezone.make_aware(datetime.combine(saklama_siniri(gun), time.min))
    with IZ_KIP_KILIDI, sistem_olarak():
        if not crypto.is_unlocked() or crypto.active_audit_key() is None:
            raise denetim_izi.IzAnahtariBellekteDegil(
                "Kayıtlar kilitli; erişim günlüğünün silmesi ertelendi."
            )
        with transaction.atomic():
            en_yeni = AccessLog.objects.filter(at__lt=sinir).aggregate(an=Max("at"))["an"]
            if en_yeni is None:
                return 0
            adet = AccessLog.objects.all()._saklama_disini_sil(sinir)
            denetim_izi.kvkk_silme(
                AccessLog, adet=adet, en_yeni=timezone.localdate(en_yeni), tetik=_TETIK
            )
    logger.info("Erişim günlüğünün saklama süresi dolan %d satırı silindi.", adet)
    return adet


def gun_isi() -> bool:
    """Gün değişimi kapısının işi: süresi dolanları siler (silinecek yoksa da gün tamamdır)."""
    suresi_dolanlari_sil()
    return True


def gun_isini_kaydet() -> None:
    """Silme işini masaüstünün gün kapısına kaydeder (`OkulConfig.ready`; `masaustu_kanca`).

    Kapı listeyi açılışta okur (`desktop.gunluk.GunDegisimiKapisi.backend_islerini_ekle`);
    iş `SISTEM` adına ve ertelemeyle sarılır (`masaustu_kanca._sistem_adina`).
    """
    masaustu_kanca.gunluk_is_kaydet(SILME_ISI, gun_isi)


# ---------------------------------------------------------------------------
# Okuma ekranı (modül başlığı "OKUMA")
# ---------------------------------------------------------------------------
#: Bir sayfadaki satır sayısı.
SAYFA_BOYUTU: Final = 50
#: Sayfa numarasının üst sınırı (biçimsiz büyük sayı SQLite'ın OFFSET sınırını aşmasın).
AZAMI_SAYFA: Final = 1_000_000

#: Türlerin görünen adları (sözlük §1 "Erişim günlüğü (F1b)"). Özel nitelikli türlerde KVKK
#: md. 6/1'in sözü: "… özel nitelikli kişisel veridir." Kişi dökümü KVKK md. 11 başvurusunun,
#: ihlal dökümü KVKK md. 12/5 bildiriminin yardımıdır (tasarım §8.6); veli listesi çıktısı adlı davet
#: teslim çizelgesi (E07) ve katılım cetvelidir (E08).
TUR_ADLARI: Final[Mapping[str, str]] = {
    AccessKind.MASKESIZ_TCKN.value: "Maskesiz T.C. kimlik numarası",
    AccessKind.KISI_DOKUMU.value: "Kişi dökümü",
    AccessKind.VELI_LISTESI_CIKTISI.value: "Veli listesi çıktısı",
    AccessKind.KISISEL_DISA_AKTARIM.value: "Kişisel veri içeren dışa aktarım",
    AccessKind.IHLAL_DOKUMU.value: "İhlal dökümü",
    AccessKind.OZEL_NITELIKLI_EK.value: "Özel nitelikli kişisel veri içeren ek",
    AccessKind.OZEL_NITELIKLI_ALAN.value: "Özel nitelikli kişisel veri alanı",
}
#: Kapalı kümede olmayan tür (program dışından yazılmış satır; DB kısıtı da reddeder).
BILINMEYEN_TUR_ADI: Final = "Bilinmeyen tür"

#: Süzgeçlerin iletileri (sözlük §1 "Erişim günlüğü (F1b)"; uç da bunları verir).
TARIH_SIRASI_MESAJI: Final = "Bitiş tarihi başlangıç tarihinden önce olamaz."
TARIH_MESAJI: Final = "Tarih geçersiz."
TUR_MESAJI: Final = "Geçerli bir tür seçin."
HESAP_MESAJI: Final = "Geçerli bir hesap seçin."
SAYFA_MESAJI: Final = "Sayfa numarası geçersiz."


def _okuma_yetkisi() -> None:
    """Yazarın rolü erişim günlüğünü okuyabilir mi? (matrisin satırı; modül başlığı "OKUMA")"""
    kim = yazar()
    if kim is None or kim.sistem_mi:
        raise RolYetkisiz
    if kim.rol not in rol_izinleri.okuyabilen_roller(rol_izinleri.Satir.ERISIM_GUNLUGU):
        raise RolYetkisiz


def _gun_basi(gun: date) -> datetime:
    """Günün yerel (Europe/Istanbul) başlangıcı, saat dilimli."""
    return timezone.make_aware(datetime.combine(gun, time.min))


def _aralik(baslangic: date | None, bitis: date | None) -> tuple[datetime | None, datetime | None]:
    """Süzgecin UTC sınırları: başlangıç gününün 00.00'ı (dahil) ve bitiş gününün ertesi 00.00'ı
    (hariç), Europe/Istanbul'a göre.

    Takvimin uçlarında sınır kurulamaz: 9999-12-31'in ertesi günü yoktur, 0001-01-01'in yerel
    00.00'ı UTC'de 1. yıldan öncedir (`OverflowError`). Bu `ValueError` değildir, uçta 500 olurdu;
    tarih geçersiz sayılır (`TARIH_MESAJI`, 400; bağımsız denetim bulgusu).
    """
    try:
        alt = None if baslangic is None else _gun_basi(baslangic).astimezone(UTC)
        ust = None if bitis is None else _gun_basi(bitis + timedelta(days=1)).astimezone(UTC)
    except OverflowError as exc:
        raise ValueError(TARIH_MESAJI) from exc
    return alt, ust


def tarih_suzgeci_hatalari(baslangic: date | None, bitis: date | None) -> dict[str, str]:
    """Tarih süzgeçlerinin alan hataları: `{alan adı: ileti}`; yoksa boş sözlük.

    `liste`'nin iki tarih denetimi (takvimin uçları, ters aralık) burada ALAN ADIYLA verilir: uç
    400'ü alana bağlar, ekran iletiyi o alanın altına yazar (F1b-2 (d3); eskiden ret alansızdı ve
    takvimin ucundaki günün hangi alanda olduğu ekranda bilinmiyordu). Başlangıç gününün yerel
    00.00'ı ya da bitiş gününün ertesi 00.00'ı kurulamıyorsa (`_aralik`) o alan `TARIH_MESAJI`
    alır; ikisi de kurulabiliyor ve bitiş başlangıçtan önceyse bitiş `TARIH_SIRASI_MESAJI` alır.
    `liste` aynı denetimleri kendisi de yapar (derin savunma); yalnız okur.
    """
    hatalar: dict[str, str] = {}
    if baslangic is not None:
        try:
            _aralik(baslangic, None)
        except ValueError:
            hatalar["baslangic"] = TARIH_MESAJI
    if bitis is not None:
        try:
            _aralik(None, bitis)
        except ValueError:
            hatalar["bitis"] = TARIH_MESAJI
    if not hatalar and baslangic is not None and bitis is not None and bitis < baslangic:
        hatalar["bitis"] = TARIH_SIRASI_MESAJI
    return hatalar


def _rol_sirasi(rol: str) -> int:
    try:
        return list(AccountRole.values).index(rol)
    except ValueError:
        return len(AccountRole.values)


def _hesap_ozetleri(kimlikler: set[Any]) -> dict[str, dict[str, Any]]:
    """Okuyan hesapların kişisiz özeti: kimlik → {id, tanitici, rol_etiketi, acilis, kapanis};
    ad-soyad okunmaz.

    Açılış ve kapanış günü aynı tanıtıcıyı taşıyan hesapları ayırır (orkestratör maddesi F-3):
    tanıtıcı yalnız AÇIK hesaplar arasında tekildir, kapanan "muhasip"in yerine açılan yeni hesap da
    "muhasip" olabilir; günlükte ikisi ayrı hesaptır.

    İki an ORM dönüştürücüsü olmadan, ham metin okunur (`oturum.ham_an_sutunlari`, `hesap_ani`):
    program dışından yazılmış geçersiz tek bir an ekranı düşürmez, o gün None olur (bağımsız
    denetim bulgusu). Açılış ANI yanıta girmeyen `_acilis_an`'da kalır: seçeneklerin sırası gün
    değil andır (aynı gün kapatılıp yeniden açılan tanıtıcı da açılış sırasıyla gelir).
    """
    ozetler: dict[str, dict[str, Any]] = {}
    sorgu = Account.objects.filter(pk__in=kimlikler).annotate(**ham_an_sutunlari())
    for satir in sorgu.values("id", "login_name", "role", "ham_acilis", "ham_kapanis"):
        kimlik = str(satir["id"])
        acilis = hesap_ani(satir["ham_acilis"])
        ozetler[kimlik] = {
            "id": kimlik,
            "tanitici": satir["login_name"],
            "rol_etiketi": rol_etiketi(satir["role"]),
            "acilis": hesap_gunu(acilis),
            "kapanis": hesap_gunu(hesap_ani(satir["ham_kapanis"])),
            "_rol": satir["role"],
            "_acilis_an": acilis,
        }
    return ozetler


#: Açılış anı okunamayan hesap aynı tanıtıcının seçeneklerinde sona düşer (sıralama anahtarı).
_EN_ESKI_AN: Final = datetime.min.replace(tzinfo=UTC)


def _secenek_sirasi(ozet: Mapping[str, Any]) -> tuple[Any, ...]:
    """Hesap seçeneklerinin sırası: rol sırası, tanıtıcı, açılış ANI (okunamayan sonda), kimlik."""
    an = ozet["_acilis_an"]
    return (
        _rol_sirasi(ozet["_rol"]),
        ozet["tanitici"],
        an is None,
        an or _EN_ESKI_AN,
        ozet["id"],
    )


def _satir_ozeti(satir: AccessLog, hesaplar: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    kimlik = str(satir.account_id)
    hesap = hesaplar.get(kimlik)
    return {
        "id": satir.pk,
        "zaman": timezone.localtime(satir.at).isoformat(),
        "hesap": {
            "id": kimlik,
            "tanitici": None if hesap is None else hesap["tanitici"],
            # Okuma anındaki rol (satırın kendi sütunu; hesabın rolü açılıştan sonra değişmez).
            "rol_etiketi": rol_etiketi(satir.role),
            "acilis": None if hesap is None else hesap["acilis"],
            "kapanis": None if hesap is None else hesap["kapanis"],
        },
        "tur": satir.kind,
        "tur_adi": TUR_ADLARI.get(satir.kind, BILINMEYEN_TUR_ADI),
        "model": satir.model or None,
        "kayit": satir.object_id or None,
        "alan": satir.field or None,
        "belge_ozeti": satir.document_sha256 or None,
        "satir_sayisi": satir.row_count,
    }


def liste(
    *,
    baslangic: date | None = None,
    bitis: date | None = None,
    tur: str | None = None,
    hesap: object = None,
    sayfa: int = 1,
) -> dict[str, Any]:
    """Okuma ekranının bir sayfası (modül başlığı "OKUMA"); yalnız okur, iz bırakmaz.

    Yanıt: `satirlar` (en yeni önce; `{id, zaman, hesap: {id, tanitici, rol_etiketi, acilis,
    kapanis}, tur, tur_adi, model, kayit, alan, belge_ozeti, satir_sayisi}`), `toplam` (süzgece
    uyan satır), `sayfa`, `sayfa_sayisi` (en az 1), `sayfa_boyutu`; süzgeç seçenekleri `turler`
    (kapalı küme, görünen adıyla) ve `hesaplar` (günlükte satırı olan hesaplar `{id, tanitici,
    rol_etiketi, acilis, kapanis}`; rol sırasıyla, aynı tanıtıcıda açılış sırasıyla). `acilis` ve
    `kapanis` hesabın Europe/Istanbul günüdür (yyyy-aa-gg; açık hesapta `kapanis` None): aynı
    tanıtıcıyı alan eski ve yeni hesap ayrılır (orkestratör maddesi F-3). Sayfa son sayfadan
    büyükse `satirlar` boştur. Bitiş başlangıçtan önceyse `ValueError`.
    """
    _okuma_yetkisi()
    if baslangic is not None and bitis is not None and bitis < baslangic:
        raise ValueError(TARIH_SIRASI_MESAJI)
    if isinstance(sayfa, bool) or not isinstance(sayfa, int) or not 1 <= sayfa <= AZAMI_SAYFA:
        raise ValueError(SAYFA_MESAJI)
    alt, ust = _aralik(baslangic, bitis)
    sorgu = AccessLog.objects.all()
    if alt is not None:
        sorgu = sorgu.filter(at__gte=alt)
    if ust is not None:
        sorgu = sorgu.filter(at__lt=ust)
    if tur is not None:
        sorgu = sorgu.filter(kind=tur)
    if hesap is not None:
        sorgu = sorgu.filter(account_id=hesap)
    toplam = sorgu.count()
    bas = (sayfa - 1) * SAYFA_BOYUTU
    satirlar = list(sorgu.order_by("-at", "-id")[bas : bas + SAYFA_BOYUTU])
    okuyanlar = set(AccessLog.objects.order_by().values_list("account_id", flat=True).distinct())
    hesaplar = _hesap_ozetleri(okuyanlar)
    return {
        "satirlar": [_satir_ozeti(satir, hesaplar) for satir in satirlar],
        "toplam": toplam,
        "sayfa": sayfa,
        "sayfa_sayisi": max(1, -(-toplam // SAYFA_BOYUTU)),
        "sayfa_boyutu": SAYFA_BOYUTU,
        "turler": [{"tur": tur_, "tur_adi": TUR_ADLARI[tur_]} for tur_ in AccessKind.values],
        "hesaplar": [
            {ad: deger for ad, deger in ozet.items() if not ad.startswith("_")}
            for ozet in sorted(hesaplar.values(), key=_secenek_sirasi)
        ],
    }
