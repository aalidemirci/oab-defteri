"""`shared.pdf` — WeasyPrint'in tek kapısı (19.09.2026 çöküş tanısı).

Sabitlenen dört şey: (1) basımlar süreç genelinde SIRAYLA koşar — eşzamanlı basım
Pango/fontconfig katmanında yerel belleği bozuyordu; (2) yazı tipi yapılandırması
belgeler arasında PAYLAŞILIR; (3) uygulama kodunda WeasyPrint'e bu kapı dışından
gidilmez — yeni bir PDF yolu kilidi sessizce atlayamasın; (4) WeasyPrint yalnız
`data:` ve paket içi `file:` kaynağı okur, belgedeki `http(s)` adresi ağ tuzağını
tetiklemez (tasarım §4.1, §13 D47).
"""

from __future__ import annotations

import re
import socket
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from shared import pdf

BACKEND = Path(__file__).resolve().parents[2]


def test_gercek_pdf_uretir_ve_yazi_tipi_yapilandirmasini_paylasir() -> None:
    ilk = pdf.html_to_pdf("<p>Türkçe metin: ĞÜŞİÖÇ ığüşiöç</p>")
    yapilandirma = pdf._font_config
    ikinci = pdf.html_to_pdf("<p>İkinci belge</p>")

    assert ilk.startswith(b"%PDF-") and ikinci.startswith(b"%PDF-")
    assert yapilandirma is not None
    assert pdf._font_config is yapilandirma, "her belgede yeni FontConfiguration kuruldu"


def test_ayni_anda_en_fazla_bir_basim(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dört iş parçacığı aynı anda basar; WeasyPrint'e aynı anda tek çağrı düşer."""
    import weasyprint

    kilit = threading.Lock()
    durum = {"etkin": 0, "en_cok": 0, "cagri": 0}

    class SahteHTML:
        def __init__(self, string: str, **_kwargs: Any) -> None:
            self.string = string

        def write_pdf(self, **_kwargs: Any) -> bytes:
            with kilit:
                durum["etkin"] += 1
                durum["cagri"] += 1
                durum["en_cok"] = max(durum["en_cok"], durum["etkin"])
            time.sleep(0.02)  # çakışma penceresi: kilitsiz kodda mutlaka örtüşür
            with kilit:
                durum["etkin"] -= 1
            return b"%PDF-sahte"

    monkeypatch.setattr(weasyprint, "HTML", SahteHTML)
    monkeypatch.setattr(pdf, "_font_config", object())  # gerçek fontconfig kurulmasın

    def isci() -> None:
        for _ in range(3):
            assert pdf.html_to_pdf("<p>x</p>") == b"%PDF-sahte"

    ipler = [threading.Thread(target=isci) for _ in range(4)]
    for ip in ipler:
        ip.start()
    for ip in ipler:
        ip.join()

    assert durum["cagri"] == 12
    assert durum["en_cok"] == 1, "iki PDF aynı anda basıldı — kilit atlanmış"


# WeasyPrint'e doğrudan giden kod kalıpları (yorum/belge dizesi değil, çağrı).
_YASAK = (
    re.compile(r"\bwrite_pdf\s*\("),
    re.compile(r"^\s*(from\s+weasyprint\b|import\s+weasyprint\b)", re.MULTILINE),
)


def test_weasyprint_yalniz_shared_pdf_kapisindan() -> None:
    """Uygulama kodunda WeasyPrint çağrısı yalnız `shared/pdf.py`de olabilir.

    Testler kapsam dışıdır (tek iş parçacığında koşar, sahte PDF üretir).
    """
    ihlaller: list[str] = []
    for kok in ("apps", "shared", "config"):
        for yol in sorted((BACKEND / kok).rglob("*.py")):
            goreli = yol.relative_to(BACKEND).as_posix()
            if "/tests/" in f"/{goreli}" or goreli == "shared/pdf.py":
                continue
            metin = yol.read_text(encoding="utf-8")
            for desen in _YASAK:
                for eslesme in desen.finditer(metin):
                    satir = metin.count("\n", 0, eslesme.start()) + 1
                    ihlaller.append(f"{goreli}:{satir}")
    assert ihlaller == [], (
        "WeasyPrint'e shared.pdf.html_to_pdf dışından gidiliyor (eşzamanlı basım "
        f"kilidini atlar — 19.09.2026 çöküşü): {ihlaller}"
    )


# --------------------------------------------------------------------------- #
# Ağsız kaynak okuyucu (url_fetcher) — tasarım §4.1, §13 D47
# --------------------------------------------------------------------------- #

#: TEST-NET-2 (RFC 5737): hiçbir gerçek sunucuya ait değildir.
_DIS_ADRES = "198.51.100.7"


@pytest.fixture
def ag_tuzagi(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    """Ad çözümü ve bağlantı denemesini kaydeder ve düşürür; kayıt boş kalmalıdır."""
    denemeler: list[str] = []

    def tuzak(*args: Any, **_kwargs: Any) -> Any:
        denemeler.append(repr(args[:2]))
        raise OSError("ağ tuzağı: dış istek denendi")

    monkeypatch.setattr(socket, "getaddrinfo", tuzak)
    monkeypatch.setattr(socket, "create_connection", tuzak)
    monkeypatch.setattr(socket.socket, "connect", tuzak)
    yield denemeler


def test_url_fetcher_ag_tuzagi(ag_tuzagi: list[str]) -> None:
    """Belgedeki ve CSS'teki `http(s)` adresleri çizilmez; tek bağlantı denenmez."""
    html = (
        f'<link rel="stylesheet" href="https://{_DIS_ADRES}/s.css">'
        f'<style>@import url("http://{_DIS_ADRES}/i.css");'
        f"p {{ background: url(http://{_DIS_ADRES}/b.png) }}</style>"
        f'<p>Türkçe metin</p><img src="http://{_DIS_ADRES}/x.png">'
        '<img src="file://sunucu/paylasim/x.png">'
    )

    belge = pdf.html_to_pdf(html)

    assert belge.startswith(b"%PDF-")
    assert ag_tuzagi == []


def test_okuyucu_yalniz_data_ve_paket_ici_dosyayi_acar(
    ag_tuzagi: list[str], tmp_path: Path
) -> None:
    okuyucu = pdf.url_okuyucu()

    yanit = okuyucu.fetch("data:text/plain;base64,T0FC")
    assert yanit.read() == b"OAB"
    yanit.close()
    sablon = pdf.PAKET_KOKU / "templates" / "documents" / "base.html"
    yanit = okuyucu.fetch(sablon.as_uri())
    assert yanit.read().lstrip().startswith(b"<")
    yanit.close()

    disari = tmp_path / "paket-disi.css"
    disari.write_text("p {}", encoding="utf-8")
    for adres in (
        f"http://{_DIS_ADRES}/x.png",
        f"https://{_DIS_ADRES}/x.png",
        f"ftp://{_DIS_ADRES}/x.png",
        "file://sunucu/paylasim/x.png",
        disari.as_uri(),
        pdf.PAKET_KOKU.as_uri() + "/../../etc/passwd",
    ):
        with pytest.raises(pdf.DisKaynakReddi):
            okuyucu.fetch(adres)
    assert ag_tuzagi == []
