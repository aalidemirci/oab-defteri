"""DRF izin sınıfları — kişi yazan uçların ilk hesap kapısı (tasarım §5.3).

Rol izni bu sınıfın işi değildir: açık oturumda rol kapısı (`RolMiddleware`, tasarım §4.4.2)
görünümden önce keser. Tasarım §12.B'deki "`RequiresAdminPassword` → rol izinleri" satırı
böyle okunur (plan F1b-2): rol işi `RolMiddleware`'e geçti, bu sınıf kurulum durumunun 409
kapısı olarak kaldı — rol kapısı yalnız açık oturumda çalıştığı için kurulumdaki 409'u
başka hiçbir şey vermez. Buradaki izin sınıfı kimlik sormaz, **programın durumunu** sorar: ilk program
yöneticisi hesabı kurulmadan kişi yazan bir uç (öğrenci/personel oluşturma, güncelleme,
silme, içe aktarma önizleme ve uygulama) çalışmaz, **409 `parola_gerekli`**
döner. Okuma yöntemleri serbesttir.

Neden 403 değil 409? İstek yetkisiz değildir; programın durumu işlemle
çelişir ("önce program yöneticisi hesabını kurun"). Arayüz bu kodu tanır ve kullanıcıyı kurulum
sihirbazının ilk adımına yönlendirir.

Savunma derinliği: izin sınıfı unutulsa bile şifreli alan anahtarsız yazmaz
(`shared.crypto.KeyMissingError` → yine 409). Koruma testi
(`tests/test_kisi_yazan_uclar.py`) URL desenlerini dolaşır ve bu sınıfı taşıyan
uçları açık bir listeyle karşılaştırır. Yeni bir kişi uç eklenince bu sınıf
takılır ve listeye eklenir.
"""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from apps.okul.services import app_password


class RequiresAdminPassword(BasePermission):
    """Yazma yöntemlerinde (POST/PUT/PATCH/DELETE) ilk hesap kurulu olmalı (rol: `RolMiddleware`)."""

    def has_permission(self, request: Request, view: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        # Kurulu değilse `PasswordRequired` → od_exception_handler → 409 parola_gerekli.
        app_password.require_password_set()
        return True
