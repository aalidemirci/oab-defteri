"""Görevli kipinin izin listesi (aile iskeletinden; tasarım §4.4) — fail-closed.

Görevli kipinde bir API isteği yalnız buradaki bir kurala uyarsa geçer; geri
kalan HER şey `kip_middleware` tarafından 403 `kip_yetkisiz` ile kesilir. Yeni
bir uç bu listeye kendiliğinden girmez (varsayılan kapalı): görevlinin o işe
gerçekten ihtiyacı varsa bilinçli olarak eklenir ve anlık görüntü testi
(`tests/test_kip_koruma.py`) aynı değişiklikte güncellenir. Testi yeşile
çekmek için listeye uç eklemek kusurdur.

Kural düzeyi: **uç + yöntem (+ parametre)**.

* Uç, Django URL adıyla tutulur (`resolve(path).view_name`; ad alanlı
  include'larda `ad_alani:ad` biçimi). Yol değil ad tutulur: yol dönüştürücü
  içerebilir, ad değişmez.
* Yöntem büyük harfli HTTP yöntemidir. HEAD ve OPTIONS ayrıca yazılmadıkça
  kapalıdır.
* Parametre kuralı: isteği alıp geçip geçmeyeceğini söyleyen bir denetçi.
  Denetçi yanlış dönerse istek kesilir. İki biçimi vardır:
  - `yalniz_sorgu(...)`: GET ucunun sorgu dizesinde YALNIZ sayılan anahtarlar
    bulunabilir (bilinmeyen anahtar da kesilir, fail-closed);
  - `govdede_yok(...)`: gövdede (ve sorgu dizesinde) sayılan anahtarların
    HİÇBİRİ bulunamaz. Gövde JSON değilse (ya da okunamıyorsa) istek kesilir:
    denetçinin okuyamadığı bir gövde görünüme ulaşmamalıdır. Boş gövde geçer
    (görünüm doğrulamayla reddeder). **Karakter kümesi yalnız UTF-8'dir**:
    denetçi baytları `json.loads` ile okur (UTF-8/16/32 kendiliğinden sezilir),
    DRF ise gövdeyi `Content-Type`'taki `charset` ile çözer; `charset=utf-7`
    gönderen bir istemci bir anahtarı denetçiye başka, görünüme başka
    gösterebilirdi. `charset` UTF-8 dışında bir şeyse istek kesilir.
  Anahtarın DEĞERİNE bakılmaz, VARLIĞINA bakılır.
  Aile iskeletinde bu denetçiler kütüphane masası uçlarını daraltıyordu; uçlar
  sökülünce (F1a-2) mekanizma kaldı, OAB'nin rol izinleri F1b'de onu kullanır
  (tasarım §12.B `rol_izinleri.py`).

`setup/status/` (masaüstü sağlık denetimi), `security/status/` ve
`security/mode/` ara katmanda HİÇBİR durumda kesilmez (§4.4) — yalnız GET/HEAD;
başka yöntemler bu listeden geçer. Listede yine de açıkça yer alırlar ki izin
listesi görevlinin gördüğü yüzeyin tam tarifi olsun.

Uç URL ADIYLA eşleştiği için `/api/` altındaki adların TEKİL olması şarttır
(uygulamaların URL'leri aynı düz ad uzayındadır): izin listesindeki bir adı
taşıyan ikinci bir desen görevli kipinde sessizce açılırdı. Teklik
`tests/test_kip_koruma.py`'de sabitlenir.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

from django.http import HttpRequest

ParametreDenetcisi = Callable[[HttpRequest], bool]

#: Parametre denetçili uçların kabul ettiği tek gövde biçimi.
JSON_ICERIK = "application/json"
#: Gövdenin kabul edilen tek karakter kümesi (adı büyük/küçük harf ve tire farkı gözetmeden).
UTF8_ADLARI = frozenset({"utf-8", "utf8"})


def utf8_mi(charset: str | None) -> bool:
    """`Content-Type`'taki `charset` yok ya da UTF-8 mi? (Başkası → fail-closed.)"""
    if charset is None:
        return True
    return charset.strip().strip('"').lower().replace("_", "-") in UTF8_ADLARI


@dataclass(frozen=True)
class SorguSiniri:
    """GET ucunda sorgu dizesinde bulunabilecek anahtarlar (başkası → 403)."""

    izinli: frozenset[str]

    def __call__(self, request: HttpRequest) -> bool:
        return set(request.GET.keys()) <= self.izinli


@dataclass(frozen=True)
class GovdeYasagi:
    """Gövdede ve sorgu dizesinde bulunamayacak anahtarlar (varlık yeter → 403)."""

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


@dataclass(frozen=True)
class IzinKurali:
    """Görevli kipinde açık bir uç + yöntem (+ isteğe bağlı parametre denetçisi)."""

    uc: str
    yontem: str
    parametre: ParametreDenetcisi | None = None
    # Kuralın neden açık olduğu (kod okuru için; kullanıcıya gösterilmez).
    gerekce: str = ""


IZIN_LISTESI: tuple[IzinKurali, ...] = (
    IzinKurali("setup-status", "GET", gerekce="masaüstü sağlık denetimi ve kurulum kapısı"),
    IzinKurali("security-status", "GET", gerekce="kilit ekranı durum sorgusu"),
    IzinKurali("security-lock", "POST", gerekce="Kilitle her kipte parolasızdır (§4.4)"),
    IzinKurali("security-mode", "GET", gerekce="kip göstergesi"),
    IzinKurali(
        "security-mode-admin",
        "POST",
        gerekce="yönetici kipine geçiş; gövdede yönetici parolası",
    ),
    IzinKurali(
        "app-quit",
        "POST",
        gerekce=(
            "Çık (tasarım §4.2); parolasız istek görünümde 403 alır, gövdede yönetici "
            "parolası gerekir — kaza önleyicidir, güvenlik sınırı değildir"
        ),
    ),
)

_KURALLAR: dict[tuple[str, str], IzinKurali] = {
    (kural.uc, kural.yontem): kural for kural in IZIN_LISTESI
}


def izinli_mi(
    uc: str | None,
    yontem: str,
    request: HttpRequest,
    *,
    kurallar: tuple[IzinKurali, ...] | None = None,
) -> bool:
    """Görevli kipinde bu istek geçer mi? Adsız ya da bilinmeyen uç → hayır.

    `kurallar` yalnız testler içindir (parametre denetçisi mekanizmasını sınamak).
    """
    if not uc:
        return False
    tablo = _KURALLAR if kurallar is None else {(k.uc, k.yontem): k for k in kurallar}
    kural = tablo.get((uc, yontem.upper()))
    if kural is None:
        return False
    return kural.parametre is None or kural.parametre(request)
