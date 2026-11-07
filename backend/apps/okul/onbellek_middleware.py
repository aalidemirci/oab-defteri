"""API yanıtları önbelleğe yazılmaz (KVKK; tasarım §4.3 tehdit 24, §4.4.3 ara katman sırası).

Masaüstü penceresi (WebView2) sunucunun yanıtlarını kendi disk önbelleğine
(`cache/webview/EBWebView/Default/Cache`) düz metin yazıyordu: Windows sınamasında (07.11.2026)
hesap listesi ve öğrenci listesi adlarla birlikte orada bulundu. Veritabanında şifreli duran alan
çözülmüş hâliyle önbellekte kalıyordu.

Her `/api/` yanıtına `Cache-Control: no-store` konur. Görünümün kendi koyduğu başlık korunur,
`no-store` ona eklenir (`patch_cache_control`). Kapıların kendi yanıtları da (503, 423, 403) bu
katmandan geçer: katman listede güvenlik ve kilit kapılarından önce durur. Yalnız oturum belirteci
daha dıştadır; onun 403'ü sabit gövdedir, kişi verisi taşımaz. Arayüzün kendi dosyaları kişi verisi
taşımaz, kapsam dışıdır (`index.html`: kökte WhiteNoise, derin bağlantıda `config/urls.py`'deki `spa`
görünümü; `/assets/`: WhiteNoise).

Windows'ta (WebView2) sayfa önbelleği ayrıca her açılışta silinir (`desktop/window.py`
`pencere_onbellegini_temizle`): önceki sürümlerin yazdıkları da gider. Pardus'ta (Qt WebEngine) sayfa
önbelleği profil dizininin dışındadır ve açılışta silinmez; orada yeni yanıtları yalnız bu katman korur.
"""

from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_cache_control

from apps.okul.lock_middleware import API_PREFIX


class ApiNoStoreMiddleware:
    """`/api/` yanıtlarına `Cache-Control: no-store` ekler (modül başlığı)."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self._get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        yanit = self._get_response(request)
        if request.path.startswith(API_PREFIX):
            patch_cache_control(yanit, no_store=True)
        return yanit
