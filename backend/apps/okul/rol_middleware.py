"""Rol kapısı — açık oturumda rolün matriste açık olmayan `/api/` isteklerini keser (tasarım §4.4.2-§4.4.3).

`config/settings.py` MIDDLEWARE listesinde `AppLockMiddleware`'den HEMEN SONRA durur
(tasarım §4.4.3 ara katman sırası): kilitliyken (423) ve geri yükleme sonrasında (503)
istek buraya hiç gelmez. Kural tablosu `apps.okul.rol_izinleri`'dedir (uç adı + yöntem →
matris satırı → roller; yeni uç varsayılan kapalıdır).

Her `/api/` isteği sırasıyla:

1. **Hiç kesilmeyen yollar** (`HIC_KESILMEYEN_YOLLAR`: açılış sağlık denetimi `HEALTH_PATH`
   = `setup/status/` ve `security/status/`) YALNIZ okuma yöntemlerinde (GET, HEAD) geçer.
   Okuma dışı yöntemleri olağan tablodan geçer (aile dersi: muafiyet yöntemi de
   sınırlamasaydı bu yollara eklenecek bir yazma yöntemi her role açık kalırdı).
2. **Yalnız açık oturumda keser.** Rol, kilit kapısının istek başında kurduğu yazar
   bağlamından okunur (`oturum.yazar()`): denetim izinin yazarıyla aynı görüntüdür, istek
   ortasındaki kilit kararı onu değiştirmez. Yazar yoksa (kurulum, kilitli, güvenlik dosyası
   kayıpken oturumsuz) neyin açık olduğuna kilit kapısı karar vermiştir; rol kapısı
   geçirir. Yazar `SISTEM` ise reddeder: kilit kapısı istekte yalnız hesap ya da hiçbir şey
   kurar, `SISTEM` bir isteğin yazarı olamaz.
3. `rol_izinleri.izinli_mi(uç adı, yöntem, rol, istek)` doğruysa geçer. Çözülemeyen `/api/`
   yolu her rolde (program yöneticisi dahil) reddedilir: var olmayan uç ile kapalı uç ayırt
   edilmez (fail-closed). OPTIONS hiçbir rolde açık değildir.
4. **Güvenlik dosyası kayıpken** (oturum açık kalmış olabilir) kesmez: o durumda açık listeyi
   kilit kapısı tutar (`lock_middleware.KAYIP_IZINLI`; yedek listesi ve geri yükleme
   kayıp kilidinin çıkış yoludur, servis o kipte yalnız kurtarma anahtarını kabul eder).
   Karar diskten YENİDEN OKUNMAZ: kilit kapısının bu istek için verdiği karar kullanılır
   (`lock_middleware.guvenlik_dosyasi_kayip_karari`). İki okuma arasında dosya silinirse
   olağan kilitte geçmiş bir isteğin rol kapısını aşması (fail-open yarış) böylece olmaz.
5. Aksi hâlde **403** ve sabit gövde `{"code": "rol_yetkisiz", "message": …, "fields": {}}`
   (`shared.exceptions.rol_yetkisiz_govdesi`): hangi ucun istendiği yankılanmaz, ileti role
   göre değişmez; servis katmanının reddiyle (`RolYetkisiz`) aynıdır.

Boşta sayacı: kilit kapısı `X-OD-Etkinlik` başlıklı ve kendi kapısından geçen istekte sayacı
tazeler; burada reddedilen istek bu tazelemeyi geri almaz (kullanıcının tıklaması gerçek bir
etkinliktir; plan F1b-2).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from desktop.server import HEALTH_PATH
from django.http import HttpRequest, HttpResponse, JsonResponse

from apps.okul import rol_izinleri
from apps.okul.lock_middleware import API_PREFIX, OKUMA, guvenlik_dosyasi_kayip_karari
from apps.okul.oturum import yazar
from shared.exceptions import rol_yetkisiz_govdesi

#: Rol kapısında hiçbir durumda kesilmeyen yollar — yalnız okuma yöntemlerinde (tam yol).
HIC_KESILMEYEN_YOLLAR: Final[frozenset[str]] = frozenset({HEALTH_PATH, "/api/v1/security/status/"})


class RolMiddleware:
    """Açık oturumda rolün açamadığı `/api/` isteklerini 403 `rol_yetkisiz` ile reddeder."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self._get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = request.path
        if not path.startswith(API_PREFIX):
            return self._get_response(request)
        yontem = (request.method or "").upper()
        if path in HIC_KESILMEYEN_YOLLAR and yontem in OKUMA:
            return self._get_response(request)
        kim = yazar()
        if kim is None:
            return self._get_response(request)
        if not kim.sistem_mi and rol_izinleri.izinli_mi(
            rol_izinleri.uc_adi(request.path_info), yontem, kim.rol, request
        ):
            return self._get_response(request)
        if not kim.sistem_mi and guvenlik_dosyasi_kayip_karari(request):
            return self._get_response(request)
        # Gövde sabit: hangi ucun istendiği yankılanmaz.
        return JsonResponse(rol_yetkisiz_govdesi(), status=403)
