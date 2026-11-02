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
bağlar. Okuma ekranı (rol: yönetici, DK) 2. adımdadır.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import date, datetime, time
from typing import Final

from django.apps import apps as django_apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone

from apps.okul import denetim_izi, masaustu_kanca
from apps.okul.models import AccessKind, AccessLog, AccountRole
from apps.okul.oturum import IZ_KIP_KILIDI, sistem_olarak, yazar
from shared import crypto

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
