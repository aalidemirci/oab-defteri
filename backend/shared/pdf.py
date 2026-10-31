"""WeasyPrint ile PDF üretiminin TEK kapısı (aile iskeletinin 19.09.2026 çöküş tanısı).

WeasyPrint'in C katmanı (Pango, fontconfig, FreeType) aynı süreçte AYNI ANDA
iki belge dizildiğinde yerel belleği bozabiliyor. Aile iskeletinde 19.09.2026'da
paketlenmiş program toplu indirme sırasında `libpangoft2` içinde erişim ihlaliyle
kapandı (Pango NULL yazı tipi döndürdü; Python istisnası olmadığı için günlüğe iz
düşmedi). Aynı DLL'ler ve gerçek evrak şablonlarıyla Windows'ta koşulan tanıda
iki iş parçacığının eşzamanlı basımı yığın bozulmasıyla (0xC0000374) düştü,
sıralı basım hiç düşmedi. Gömülü sunucu (waitress) altı iş parçacığıyla çalışır
ve her evrak isteği ötekinden bağımsızdır: kilit yoksa çakışabilirler.

Bu modül üç şey yapar:

1. **Süreç genelinde TEK kilit** — her `write_pdf` sırayla koşar. Tek
   kullanıcılı programda bedeli, ikinci PDF işinin birincinin bitmesini
   beklemesidir (tanıda kilit süreyi uzatmadı: iş zaten Python kilidine bağlı).
2. **TEK yazı tipi yapılandırması** — `FontConfiguration` ilk kullanımda kurulur
   ve kilit altında paylaşılır. Aksi hâlde WeasyPrint her belgede fontconfig'i
   baştan kurar; Windows paketinde fontconfig önbelleği hiç yazılmadığından
   (`cache/fontconfig` boş kalıyor) bu, her belgede yazı tiplerinin yeniden
   taranması demekti. Belgede `@font-face` YOKTUR (yalnız gömülü DejaVu);
   olsaydı paylaşılan yapılandırma belgeler arasında taşırdı.
3. **Ağsız kaynak okuyucu** (`url_fetcher`; tasarım §4.1, §13 D47) — WeasyPrint
   belgedeki ya da CSS'teki bir `http(s)` adresini kendi istemcisiyle indirirdi;
   kaynak taraması (`test_dis_istek_kapilari`) kitaplığın içini görmez. Okuyucu
   yalnız `data:` ve paket içi (`backend/` altı) yerel `file:` kaynağını açar;
   öteki şemalar, ağ paylaşımına giden `file://sunucu/...` ve paket dışı dosya
   `DisKaynakReddi` yükseltir. WeasyPrint bunu yakalayıp uyarı yazar, kaynağı
   çizmeden belgeyi üretir — istek hiç çıkmaz.

Kural: WeasyPrint'e yalnız buradan gidilir. Koruma testi
`shared/tests/test_pdf.py` uygulama kodunda başka `write_pdf` çağrısına izin
vermez — yeni bir PDF yolu kilidi atlayamasın. (Paket teşhis kipi
`packaging/pyinstaller/giris.py --pdf-duman` sunucu açılmadan tek başına koşar;
kapsam dışıdır.)
"""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

_lock = threading.Lock()
_font_config: Any = None

#: Belgenin okuyabileceği yerel dosyaların kökü: `backend/` (şablonlar, statik
#: dosyalar). Paketli programda da backend kaynak dizini olarak paketlenir.
PAKET_KOKU = Path(__file__).resolve().parents[1]
_WINDOWS_SURUCU = re.compile(r"^/[A-Za-z]:")


class DisKaynakReddi(ValueError):
    """Belge, izin verilmeyen bir kaynağı (ağ ya da paket dışı dosya) istedi."""


def _yerel_yol(url: str) -> Path:
    """`file:` adresinin yerel yolu; ağ paylaşımı (`file://sunucu/...`) reddedilir."""
    parcalar = urlsplit(url)
    if parcalar.netloc not in ("", "localhost"):
        raise DisKaynakReddi("ağ paylaşımındaki dosya okunmaz")
    yol = unquote(parcalar.path)
    if _WINDOWS_SURUCU.match(yol):  # file:///C:/... → C:/...
        yol = yol[1:]
    return Path(yol)


def url_okuyucu() -> Any:
    """WeasyPrint `url_fetcher`'ı: yalnız `data:` ve `PAKET_KOKU` altındaki `file:`.

    WeasyPrint'in `URLFetcher`'ından türer (68: işlevsel okuyucu kullanımdan
    kalkıyor); izin verilen istek üst sınıfın `data:`/`file:` işleyicilerine gider,
    öteki her şey daha açılmadan reddedilir.
    """
    from weasyprint.urls import URLFetcher  # tembel import — ağır bağımlılık

    class _AgsizOkuyucu(URLFetcher):  # type: ignore[misc]
        def fetch(self, url: str, headers: Any = None) -> Any:
            sema = url.split(":", 1)[0].lower()
            if sema == "data":
                return super().fetch(url, headers)
            if sema == "file":
                yol = _yerel_yol(url).resolve()
                if yol.is_relative_to(PAKET_KOKU):
                    return super().fetch(url, headers)
                raise DisKaynakReddi("paket dışındaki dosya okunmaz")
            raise DisKaynakReddi(f"izin verilmeyen kaynak şeması: {sema}")

    return _AgsizOkuyucu(allow_redirects=False)


def html_to_pdf(html: str) -> bytes:
    """HTML'i PDF'e çevirir — kilit altında, paylaşılan yazı tipi yapılandırmasıyla."""
    from weasyprint import HTML  # tembel import — ağır bağımlılık (DLL'ler)

    global _font_config
    with _lock:
        if _font_config is None:
            from weasyprint.text.fonts import FontConfiguration

            _font_config = FontConfiguration()
        belge = HTML(string=html, url_fetcher=url_okuyucu())
        return bytes(belge.write_pdf(font_config=_font_config))
