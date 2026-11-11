"""`oab` servislerinin ret türleri: `{code, message, fields}` gövdesiyle dönerler.

`APIException` oldukları için servis zincirinden görünüme kadar yutulmaz; DRF işlemi geri alır.
İleti Türkçedir, iç ayrıntı (kural kimliği, model adı) taşımaz; atıf kullanıcıya gösterilir.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import APIException


class DonemKapali(APIException):
    """Kapanmış dönemin kaydına beyaz liste dışı yazma (sert; tasarım §5 O2)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "donem_kapali"
    default_detail = "Bu birlik dönemi kapanmıştır; kayıt yazılamaz."


class DonemYazilamaz(APIException):
    """Dönem bu yazmaya açık değil: hazırlıktaki döneme genel kurul hazırlığı dışında yazma."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "donem_yazilamaz"
    default_detail = "Bu birlik dönemine bu kayıt yazılamaz."


class DonemSaltOkur(APIException):
    """Dönemin kural kopyası özetini tutmuyor (D7): dönem salt okur açılır."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "donem_salt_okur"
    default_detail = (
        "Bu birlik döneminin kural kopyası doğrulanamadığı için dönem salt okunur açıldı. "
        "Yedekten geri yükleme için program yöneticisine başvurun."
    )


class GecisKapali(APIException):
    """Geçiş kurulumunun kaydı yazılamaz: "Geçiş kurulumu tamamlandı" işareti konmuş ya da geçiş
    dönemi açık değil (tasarım §7.9 "Senaryolar"; plan F1c 8. adımın kararı)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "gecis_kapali"
    default_detail = (
        "Geçiş kurulumu tamamlandı; geçiş kayıtları artık eklenemez, düzeltilemez ve iptal "
        "edilemez."
    )


class GerekceGerekli(APIException):
    """Uyarı gerektiren kayıt gerekçesiz geçmez (altın kural 3): 400 `gerekce_gerekli`."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "gerekce_gerekli"
    default_detail = "Bu kayıt için gerekçe yazılmalıdır."


class KuralSert(APIException):
    """Sert kural: kural dışı değer ya da işlem kaydedilmez (altın kural 3)."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "kural_sert"
    default_detail = "Bu kayıt kurala aykırı olduğu için yapılmadı."


class RevizyonOnayiGerekli(APIException):
    """Geçiş kayıtların hesabını ya da uyarısını değiştiriyor: liste görülüp onaylanmalı (§6.2-3a)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "revizyon_onayi_gerekli"
    default_detail = (
        "Bu kural sürümü bazı kayıtların hesabını ya da uyarısını değiştiriyor; onay gerekli."
    )


class YeterSayiDonduruldu(APIException):
    """Yeter sayı ilan anında dondurulur, elle değiştirilemez (sert; tasarım §5.2.3)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "yeter_sayi_donduruldu"
    default_detail = "Bu genel kurulun yeter sayısı dondurulmuştur; değiştirilemez."


class OlasiAyniKisi(APIException):
    """Aynı ad kör indeksiyle başka birlik kişisi var: "olası aynı kişi" (tasarım §13 D30).

    Engel değil, soru: kullanıcı aynı kişi olmadığını onaylayınca (`ayni_kisi_degil`) kayıt yazılır.
    İleti adı yankılamaz.
    """

    status_code = status.HTTP_409_CONFLICT
    default_code = "olasi_ayni_kisi"
    default_detail = (
        "Bu adla kayıtlı bir birlik kişisi var; aynı kişi olabilir. Aynı kişi değilse "
        "onaylayarak yeniden kaydedin."
    )


class KisiPasif(APIException):
    """Pasif kişi kaydının alanları değişmez; yalnız yeniden etkinleştirilir (tasarım §5 O2)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "kisi_pasif"
    default_detail = "Pasif kişi kaydı değiştirilemez; önce kaydı etkinleştirin."


class EvrakIcerigiSaklanmaz(APIException):
    """Veli adı taşıyan belge (R9) yeniden basılmaz: içeriği ve dosyası saklanmaz (tasarım §9.1-2)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "evrak_icerigi_saklanmaz"
    default_detail = (
        "Bu belge veli adı taşıdığı için program içeriğini saklamaz; yeniden basılamaz, yeniden "
        "üretilir."
    )


class EvrakIcerigiTutmuyor(APIException):
    """Kayıtlı içerik JSON'u çözülemedi ya da kayıtlı özeti tutmuyor: belge basılmaz (§6.2-6)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "evrak_icerigi_tutmuyor"
    default_detail = (
        "Kayıtlı evrak içeriği doğrulanamadı; belge yeniden basılmadı. Kayıt program dışından "
        "değiştirilmiş olabilir; Denetleme Kuruluna bildirin."
    )


class EvrakDosyasiYazilamadi(APIException):
    """Üretilen evrakın dosyası depoya yazılamadı (ör. geri yükleme sürüyor): kayıt da yazılmaz.

    İleti dosya deposunun iletisidir (sözlük §1 "Ek ve dosya deposu"); özgün ad taşımaz.
    """

    status_code = status.HTTP_409_CONFLICT
    default_code = "evrak_dosyasi_yazilamadi"
    default_detail = "Geri yükleme sürüyor; dosya yazılmadı. Biraz sonra yeniden deneyin."


class EvrakDosyasiAcilamadi(APIException):
    """Üretilen evrakın dosyası açılamadı (yok, bozuk ya da özeti tutmuyor): bayt verilmez, basım
    izi yazılmaz. İleti dosya deposunun iletisidir (sözlük §1 "Ek ve dosya deposu")."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "evrak_dosyasi_acilamadi"
    default_detail = "Dosya yok: bu ekin dosyası imha edilmiş ya da depoda bulunamadı."
