"""Kilit kapısı ve oturumun istek başı işleri (tasarım §4.3 tehdit 8, §4.4.3; plan F1b-1 "Oturum").

İlk program yöneticisi hesabı zorunludur (hesapsız kip yok). Hesap kurulu ve oturum
açılmamışken hassas alanlar zaten okunamaz (şifreli token döner) ve yazılamaz
(`KeyMissingError`), ama programın "çalışıyormuş gibi" davranıp resmî evraka
çözülememiş metin basması KABUL EDİLEMEZ. Bu ara katman iki kilidi uygular:

1. **Güvenlik dosyası kayıp** (tehdit 8): DB'de anahtar parmak izi var ama
   `guvenlik.json` yok — ya da dosya var ama kullanılamıyor (boş, bozuk, şema 1,
   sarmal bölümleri eksik; `app_password.security_file_missing`). Kilitliyken
   dosyanın silinmesi, yeniden adlandırılması ya da bozulması programı
   "hesapsız"a döndürmez ve kullanıcıyı çıkışsız bir kilit ekranında da bırakmaz;
   `423 guvenlik_dosyasi_kayip` döner. Anahtar bellekteyken dosya kaybolsa bile kapı
   kapanır: bir sonraki kilitte açılamayacak bir durumda çalışmaya devam etmek yerine
   kullanıcı sorunu hemen görür. Açık kalanlar `KAYIP_IZINLI`'dedir: durum uçları,
   "sıfırla ve kuruluma dön" (uç koşulu kendisi denetler, aksi 409), yedek listesi ve
   geri yükleme (çıkış yolu: geri yükleme `guvenlik.json`'u yedeğin kurtarma
   başlığından yeniden yazar; öteki yol dosyanın yedeğini veri klasörüne geri koymaktır
   — kapı her istekte diske bakar, dosya döndüğü anda olağan kilide geçilir) ve Çık.
2. **Kilitli** (`423 locked`): hesap kurulu, oturum açık değil (`oturum.OTURUM`). Açık
   kalanlar `KILITLI_IZINLI`'dedir: açılış sağlık denetimi (`desktop/server.py::
   HEALTH_PATH`; yanıtı kişisel veri içermez), güvenlik ve oturum durumu, kilit
   ekranının hesap listesi, kilit açma, kurtarma anahtarıyla açılış ve onun hesap
   listesi (tanıtıcı + rol etiketi; kişi adı yok) ve Çık (parolasız, çarpıyla aynı
   düzenli kapanış; T6).

İKİ LİSTE DE AÇIKTIR (yol → yöntemler, tam yol eşleşmesi). Ailede kilitliyken bütün
`security/` ön eki açıktı; artık değil: güvenlik ön ekine eklenen yeni bir uç kilitliyken
kendiliğinden kapalıdır ve URL desenlerini dolaşan test (`test_kilit_koruma.py`) bunu
sabitler. Kendi parolasını değiştirme de artık kilitliyken kapalıdır (plan F1b-1: yalnız
açık oturumda; ailede ikinci bir kilit açma yoluydu). Durum uçları yalnız okuma
yöntemlerinde açıktır (ailenin hiç kesilmeyen yollar kuralı; ileride aynı yola eklenecek
bir yazma yöntemi kilitliyken kendiliğinden açılmasın). Kurtarma anahtarı belgesi,
saklandı damgası ve anahtar yenileme kilitliyken kapalıdır: bellekteki anahtara karşı
doğrularlar, kilit açmanın yolu değildirler (açık kalsalardı ikinci bir deneme kapısı
olurlardı). `updates/` kilitliyken kapalıdır (tasarım TK4: sürüm denetimi yalnız
Ayarlar → Güncelleme'deki "Şimdi denetle" düğmesiyledir).

Hesap hiç kurulmamışsa ("kurulum" durumu) kapı bir şey yapmaz: kişi yazan uçları izin
sınıfı (`permissions.RequiresAdminPassword`, 409 `parola_gerekli`) keser.

OTURUMUN İSTEK BAŞI İŞLERİ de buradadır; ayrı bir ara katmana bölünmedi, çünkü tembel
kilit 423 kararından ÖNCE uygulanmalıdır ve iki ara katman arasındaki sıra bağımlılığı
tek yerde durur. `/api/` altındaki her istekte sırasıyla:

1. İstek uçuşta sayılır (`OTURUM.istek`): kilitleme uçuştaki isteklerin bitmesini bekler.
   Sayım kapı kararından ÖNCE başlar; böylece "kapıdan geçti ama henüz sayılmadı" anı
   yoktur ve DEK, kapıdan geçmiş bir isteğin ortasında düşmez.
2. Tembel kilit (`OTURUM.degerlendir`): uzun iş bitmişse bekleyen kilit, boşta süre
   dolmuşsa boşta kilit bu istekte uygulanır (yalnız durum yoklaması olsa da).
3. Kapı kararı (yukarıdaki iki kilit).
4. `X-OD-Etkinlik` başlıklı ve kapıdan geçen istek boşta sayacını tazeler; bu kapıda
   reddedilen istek tazelemez (rol kapısında reddedilen istek tazelemeyi geri almaz:
   tıklama gerçek bir etkinliktir). Başlığı yalnız ön yüz, kullanıcı etkileşiminden hemen
   sonra gönderir.
5. Yazar bağlamı (`oturum.yazar_olarak`): oturum açıksa hesap + rol, değilse yok. Denetim
   izi yazıcısı (`apps.okul.denetim_izi`), rol kapısı (`rol_middleware`) ve servislerin
   yetki kapısı (`rol_izinleri.yetki_oturum`) okur; istek boyunca değişmez.
6. Kapı kararı isteğe yazılır (`guvenlik_dosyasi_kayip_karari`): rol kapısı güvenlik
   dosyası kayıp kararını diskten yeniden okumaz, bu isteğin kararını kullanır.

API dışı yollar (SPA'nın kendisi, statik dosyalar) daima serbesttir — kilit ekranı
yüklenebilmelidir. **Yerel yedekleme etkilenmez**: günlük yedek bir HTTP ucu değildir;
masaüstü kabuğu onu açık yedek anahtarıyla alır (`desktop/main.py`).

`config/settings.py` MIDDLEWARE sırası (tasarım §4.4.3): belirteç → güvenlik →
whitenoise → common → `RestartRequired` (503) → **`AppLock` (423)** → `RolMiddleware`
(403 `rol_yetkisiz`; yalnız açık oturumda keser, `rol_middleware`).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Final

from desktop.server import HEALTH_PATH
from django.http import HttpRequest, HttpResponse, JsonResponse

from apps.okul.oturum import ETKINLIK_BASLIGI, OTURUM, Yazar, yazar_olarak
from apps.okul.services import app_password

API_PREFIX = "/api/"
_API = "/api/v1/"
#: Okuma yöntemleri: durum uçları yalnız bunlarda açıktır (modül başlığı).
OKUMA: frozenset[str] = frozenset({"GET", "HEAD"})
_POST: frozenset[str] = frozenset({"POST"})
_HIC: frozenset[str] = frozenset()

#: Oturum kilitliyken açık kalan uçlar (tam yol → yöntemler; modül başlığı).
KILITLI_IZINLI: Mapping[str, frozenset[str]] = {
    # Açılış sağlık denetimi; kurulum sihirbazının YAZMA uçları kapalı kalır.
    HEALTH_PATH: OKUMA,
    _API + "security/status/": OKUMA,
    _API + "security/session/": OKUMA,
    # Kilit ekranının hesap listesi (tanıtıcı + rol etiketi; kişi adı yok).
    _API + "security/accounts/": OKUMA,
    _API + "security/unlock/": _POST,
    # Kurtarma anahtarıyla açılış (POST) ve açılabilecek program yöneticisi hesapları
    # (GET; kurtarmayla geri yüklemeden sonra kilit ekranı listesi boştur, TK10).
    _API + "security/recover/": OKUMA | _POST,
    # Çık (tasarım §4.2): kilitliyken parolasız. Ön ek değildir: `app/` altına
    # ileride eklenecek bir yol kilit kapısını aşmasın.
    _API + "app/quit/": _POST,
}

#: Güvenlik dosyası kayıpken açık kalan uçlar (tam yol → yöntemler; §4.3 tehdit 8).
KAYIP_IZINLI: Mapping[str, frozenset[str]] = {
    HEALTH_PATH: OKUMA,
    _API + "security/status/": OKUMA,
    _API + "security/session/": OKUMA,
    # "Güvenlik dosyasını sıfırla ve kuruluma dön": uç kendi koşullarını denetler (aksi 409).
    _API + "security/state/reset/": _POST,
    _API + "backups/": OKUMA,
    _API + "backups/restore/": _POST,
    # Çık (tasarım §4.2): kayıp kilidinde de parolasız çıkılır.
    _API + "app/quit/": _POST,
}

_LOCKED_BODY = {
    "code": "locked",
    # Tasarım §12.B, §13 D50: her kullanıcı kendi hesabıyla açar.
    "message": (
        "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın (parolanızı unuttuysanız "
        "program yöneticisine başvurun)."
    ),
    "fields": {},
}

_SECURITY_FILE_MISSING_BODY = {
    "code": "guvenlik_dosyasi_kayip",
    "message": app_password.SECURITY_FILE_MISSING_MESSAGE,
    "fields": {},
}


#: Kilit kapısının bu istek için verdiği "güvenlik dosyası kayıp" kararı (istek özniteliği;
#: modül başlığı madde 6). Rol kapısı okur.
_KAYIP_KARARI: Final = "od_guvenlik_dosyasi_kayip"


def guvenlik_dosyasi_kayip_karari(request: HttpRequest) -> bool:
    """Kilit kapısı bu isteği güvenlik dosyası kayıp kilidinde mi geçirdi? (yoksa hayır)"""
    return getattr(request, _KAYIP_KARARI, False) is True


def izinli_mi(liste: Mapping[str, frozenset[str]], path: str, method: str) -> bool:
    """Yol + yöntem açık listede mi? (tam yol; yöntem büyük harfe çevrilir)"""
    return method.upper() in liste.get(path, _HIC)


class AppLockMiddleware:
    """Kayıp ve kilitli durumda açık listeler dışındaki API'yi 423 ile keser; oturumun istek başı."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self._get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = request.path
        if not path.startswith(API_PREFIX):
            return self._get_response(request)
        yontem = request.method or ""
        with OTURUM.istek():
            OTURUM.degerlendir()
            hesap = OTURUM.hesap()
            kayip = app_password.security_file_missing()
            setattr(request, _KAYIP_KARARI, kayip)
            # Gövdeler sabit: hangi ucun istendiği yankılanmaz.
            if kayip:
                if not izinli_mi(KAYIP_IZINLI, path, yontem):
                    return JsonResponse(_SECURITY_FILE_MISSING_BODY, status=423)
            elif (
                hesap is None
                and not izinli_mi(KILITLI_IZINLI, path, yontem)
                and app_password.is_password_set()
            ):
                return JsonResponse(_LOCKED_BODY, status=423)
            if hesap is not None and request.headers.get(ETKINLIK_BASLIGI):
                OTURUM.etkinlik()
            with yazar_olarak(Yazar.hesaptan(hesap) if hesap is not None else None):
                return self._get_response(request)
