"""Rol izinlerinin parametre denetçileri (aile iskeletinden; tasarım §4.4.2, TK13, §12.B).

**Rol-izin matrisi F1b 2. adımda bu dosyaya gelir:** her hücre uç + yöntem (+
parametre) kuralıdır, yeni uç varsayılan kapalıdır, `RolMiddleware` (403
`rol_yetkisiz`) matrisi okur ve URL desenlerini dolaşan koruma testi onu sabitler.
1. adımda aile iskeletinin görevli kipi ve onun izin listesi (`kip_izinleri`,
`kip_middleware`) oturum düzenine dönünce söküldü; ailenin parametre denetçileri ve
uç adı çözücüsü matrisin kullanması için AYNEN buraya taşındı. Bugün hiçbir kural
bunları çağırmaz; 1. ile 2. adım tek PR'la `main`'e gider (plan F1b-1 "Sıra ve
sınır"), arada yalnız `yonetici` hesabı açılabilir.

Parametre kuralı: isteği alıp geçip geçmeyeceğini söyleyen bir denetçi. Denetçi
yanlış dönerse istek kesilir. İki biçimi vardır:

* `yalniz_sorgu(...)`: GET ucunun sorgu dizesinde YALNIZ sayılan anahtarlar
  bulunabilir (bilinmeyen anahtar da kesilir, fail-closed);
* `govdede_yok(...)`: gövdede (ve sorgu dizesinde) sayılan anahtarların HİÇBİRİ
  bulunamaz. Gövde JSON değilse (ya da okunamıyorsa) istek kesilir: denetçinin
  okuyamadığı bir gövde görünüme ulaşmamalıdır. Boş gövde geçer (görünüm
  doğrulamayla reddeder). **Karakter kümesi yalnız UTF-8'dir**: denetçi baytları
  `json.loads` ile okur (UTF-8/16/32 kendiliğinden sezilir), DRF ise gövdeyi
  `Content-Type`'taki `charset` ile çözer; `charset=utf-7` gönderen bir istemci bir
  anahtarı denetçiye başka, görünüme başka gösterebilirdi. `charset` UTF-8 dışında
  bir şeyse istek kesilir.

Anahtarın DEĞERİNE bakılmaz, VARLIĞINA bakılır.

Uçlar Django URL ADIYLA tutulacaktır (`uc_adi`; ad alanlı include'da `ad_alani:ad`):
yol dönüştürücü içerebilir, ad değişmez. Bu yüzden `/api/` altındaki adların TEKİL
olması şarttır; teklik `tests/test_rol_izinleri.py`'de sabitlenir.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

from django.http import HttpRequest
from django.urls import Resolver404, resolve

ParametreDenetcisi = Callable[[HttpRequest], bool]

#: Parametre denetçili uçların kabul ettiği tek gövde biçimi.
JSON_ICERIK = "application/json"
#: Gövdenin kabul edilen tek karakter kümesi (adı büyük/küçük harf ve tire farkı gözetmeden).
UTF8_ADLARI = frozenset({"utf-8", "utf8"})


def uc_adi(path_info: str) -> str | None:
    """Yolun Django URL adı (ad alanlı include'da `ad_alani:ad`); çözülemezse None."""
    try:
        eslesme = resolve(path_info)
    except Resolver404:
        return None
    return eslesme.view_name or None


def utf8_mi(charset: str | None) -> bool:
    """`Content-Type`'taki `charset` yok ya da UTF-8 mi? (Başkası → fail-closed.)"""
    if charset is None:
        return True
    return charset.strip().strip('"').lower().replace("_", "-") in UTF8_ADLARI


@dataclass(frozen=True)
class SorguSiniri:
    """GET ucunda sorgu dizesinde bulunabilecek anahtarlar (başkası → ret)."""

    izinli: frozenset[str]

    def __call__(self, request: HttpRequest) -> bool:
        return set(request.GET.keys()) <= self.izinli


@dataclass(frozen=True)
class GovdeYasagi:
    """Gövdede ve sorgu dizesinde bulunamayacak anahtarlar (varlık yeter → ret)."""

    yasak: frozenset[str]

    def __call__(self, request: HttpRequest) -> bool:
        if set(request.GET.keys()) & self.yasak:
            return False
        try:
            ham = request.body
        except Exception:  # okunamayan (ör. aşırı büyük) gövde: fail-closed
            return False
        if not ham.strip():
            return True
        if (request.content_type or "").lower() != JSON_ICERIK:
            return False
        if not utf8_mi((request.content_params or {}).get("charset")):
            return False
        try:
            govde = json.loads(ham)
        except (ValueError, UnicodeDecodeError):
            return False
        if not isinstance(govde, dict):
            return False
        return not (set(govde) & self.yasak)


def yalniz_sorgu(*anahtarlar: str) -> SorguSiniri:
    return SorguSiniri(frozenset(anahtarlar))


def govdede_yok(*anahtarlar: str) -> GovdeYasagi:
    return GovdeYasagi(frozenset(anahtarlar))
