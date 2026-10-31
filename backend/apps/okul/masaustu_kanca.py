"""Masaüstü kancaları — backend ile masaüstü kabuğu arasındaki TEK kanal (T16).

Program tek süreçtir: Django (yönetim API'si) ve masaüstü kabuğunun iş
parçacıkları (`od-gunluk`, `od-kanal`) aynı süreçte koşar. Backend masaüstüne
bir HTTP ucuyla değil, masaüstü kabuğunun açılışta buraya KAYDETTİĞİ nesnelerle
ulaşır (tasarım §4.1). Böylece ikinci bir durum kaynağı ya da tanımsız bir
kontrol kanalı doğmaz:

* **Çıkış** (`POST app/quit/`, `views_app.py`): düzenli kapanışı başlatan
  çağrılabilir; masaüstünde pencere denetçisinin `request_quit` yoludur
  (pencerenin çarpısı, tek kopya kanalı ve kurucunun kapatma olayıyla aynı yol).
* **Gün değişimi işleri** (T9): backend'deki bir işin masaüstünün `od-gunluk`
  kapısına girmesi için buraya kaydolması yeter; kapı açılışta bu listeyi okur.
  Masaüstü modüllerini backend'den içe aktarmak gerekmez.

Geri yükleme ile gün işlerinin dışlaşması bu kanaldan değil, ortak bakım
kapısından (`shared/bakim.py`) geçer.

Kanca yoksa (geliştirme sunucusu, testler) işlevler "yok" der; çağıran uç bunu
kullanıcıya Türkçe iletiyle bildirir (ör. 503). Kayıt süreç içidir ve
açılışta bir kez yapılır; `_reset_for_tests` yalnız testler içindir.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass

GunlukIs = Callable[[], bool | None]


@dataclass(frozen=True)
class GunlukIsKaydi:
    """Gün değişimi kapısına backend'den kaydolan iş (T9)."""

    ad: str
    calistir: GunlukIs


_kilit = threading.Lock()
_cikis: Callable[[], None] | None = None
_gunluk_isler: dict[str, GunlukIsKaydi] = {}


def kaydet(*, cikis: Callable[[], None] | None = None) -> None:
    """Masaüstü kabuğu açılışta kancalarını kaydeder (verilmeyen kanca değişmez)."""
    global _cikis
    with _kilit:
        if cikis is not None:
            _cikis = cikis


def kaldir() -> None:
    """Kapanışta kancaları bırakır: kapanan sunucuya istek yönlendirilmez."""
    global _cikis
    with _kilit:
        _cikis = None


def cikis_iste() -> bool:
    """Düzenli kapanışı başlatır; kanca yoksa `False` (masaüstü dışında çalışıyor).

    Kanca ENGELLEMEZ: kapanış ayrı bir iş parçacığında sürer, bu çağrıyı yapan
    HTTP isteği yanıtını gönderebilir.
    """
    with _kilit:
        cikis = _cikis
    if cikis is None:
        return False
    cikis()
    return True


def gunluk_is_kaydet(ad: str, calistir: GunlukIs) -> None:
    """Gün değişimi kapısına iş kaydeder (T9). Aynı adla ikinci kayıt öncekinin yerine geçer.

    İş günde bir kez, kapının `od-gunluk` iş parçacığında koşar. `True` ya da
    `None` dönerse o günün işi yapılmış sayılır; `False` dönerse ya da istisna
    yükseltirse bir saat sonra yeniden denenir. İş kendi veritabanı
    bağlantısını `finally` içinde kapatmakla yükümlü değildir: kapı her işten
    sonra iş parçacığının bağlantılarını kapatır.
    """
    if not ad or not ad.isascii():
        raise ValueError("Gün değişimi işinin adı ASCII ve boş olmayan bir dize olmalı.")
    with _kilit:
        _gunluk_isler[ad] = GunlukIsKaydi(ad=ad, calistir=calistir)


def gunluk_isler() -> tuple[GunlukIsKaydi, ...]:
    """Kayıtlı gün değişimi işleri (kayıt sırasıyla)."""
    with _kilit:
        return tuple(_gunluk_isler.values())


def _reset_for_tests() -> None:
    """Yalnız testler için: kayıt süreç içi olduğundan testler arasında sızar."""
    global _cikis
    with _kilit:
        _cikis = None
        _gunluk_isler.clear()
