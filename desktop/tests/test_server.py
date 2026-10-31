"""Gömülü sunucu testleri (tasarım §4.1 — 127.0.0.1 + boş port, erişim logu YOK).

Dosyanın sonundaki koruma testleri "yalnız 127.0.0.1" değişmezini kilitler (§13 D2).
"""

from __future__ import annotations

import ast
import socket
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

import pytest

from desktop.errors import ServerStartError
from desktop.server import DEFAULT_HOST, BackgroundServer, check_health, find_free_port


class _SahteSunucu:
    """waitress sunucusu yerine geçen kayıt tutucu (gerçek soket açmaz)."""

    def __init__(self, effective_port: int | str = 54321) -> None:
        self.effective_port = effective_port
        self.effective_host = "127.0.0.1"
        self.calisti = False
        self.kapandi = False

    def run(self) -> None:
        self.calisti = True

    def close(self) -> None:
        self.kapandi = True


def test_bos_port_bulunur_ve_baglanabilir() -> None:
    port = find_free_port()

    assert 1024 < port < 65536
    with socket.socket() as s:  # port gerçekten serbest olmalı
        s.bind(("127.0.0.1", port))


def test_sunucu_sabit_port_kullanmaz() -> None:
    """Sabit port YOK: başka bir program 8000'i tutuyorsa açılış patlamamalı."""
    cagri: dict[str, Any] = {}

    def fabrika(app: object, **kwargs: Any) -> _SahteSunucu:
        cagri.update(kwargs)
        return _SahteSunucu(effective_port=54321)

    sunucu = BackgroundServer(lambda environ, start_response: [], server_factory=fabrika)
    sunucu.start()
    try:
        assert cagri["port"] == 0  # işletim sistemi boş port seçsin
        assert cagri["host"] == "127.0.0.1"
        assert sunucu.port == 54321
        assert sunucu.base_url == "http://127.0.0.1:54321"
    finally:
        sunucu.stop()


def test_port_tam_sayiya_cevrilir() -> None:
    """waitress `effective_port`'u METİN döndürür; `%d` biçimlemesi patlamasın."""
    sunucu = BackgroundServer(
        lambda environ, start_response: [],
        server_factory=lambda app, **kwargs: _SahteSunucu(effective_port="54321"),
    )
    sunucu.start()
    try:
        assert sunucu.port == 54321
        assert isinstance(sunucu.port, int)
        assert sunucu.base_url == "http://127.0.0.1:54321"
    finally:
        sunucu.stop()


def test_sunucu_arka_plan_thread_inde_kosar_ve_durdurulur() -> None:
    sahte = _SahteSunucu()

    sunucu = BackgroundServer(
        lambda environ, start_response: [],
        server_factory=lambda app, **kwargs: sahte,
    )
    sunucu.start()
    sunucu.wait_until_started(timeout=2.0)

    assert sahte.calisti
    assert sunucu.thread is not None and sunucu.thread.daemon

    sunucu.stop()
    assert sahte.kapandi
    assert sunucu.thread is None


def test_sunucu_ayaga_kalkmazsa_turkce_hata(monkeypatch: pytest.MonkeyPatch) -> None:
    def patla(app: object, **kwargs: Any) -> _SahteSunucu:
        raise OSError("adres kullanımda")

    sunucu = BackgroundServer(lambda environ, start_response: [], server_factory=patla)

    with pytest.raises(ServerStartError) as hata:
        sunucu.start()

    assert "başlat" in str(hata.value).lower()


def test_gercek_waitress_yalniz_yerel_arayuzde_dinler() -> None:
    """Bütünleşik denetim: gerçek waitress + boş port + 127.0.0.1 bağlanması."""
    waitress = pytest.importorskip("waitress")
    assert waitress

    def uygulama(environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"tamam"]

    sunucu = BackgroundServer(uygulama)
    sunucu.start()
    try:
        sunucu.wait_until_ready(timeout=10.0)
        assert sunucu.port != 0
        assert isinstance(sunucu.port, int)
        with urllib.request.urlopen(sunucu.base_url + "/", timeout=5) as yanit:  # noqa: S310
            assert yanit.status == 200
            assert yanit.read() == b"tamam"
    finally:
        sunucu.stop()


def test_saglik_denetimi_belirtecsiz_istegin_reddini_dogrular() -> None:
    """`--autotest`: belirteçsiz istek 403 DÖNMELİ, belirteçli istek 200."""
    pytest.importorskip("waitress")
    gorulen: list[str] = []

    def uygulama(environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        gorulen.append(environ.get("QUERY_STRING", ""))
        if "gizli" in environ.get("QUERY_STRING", ""):
            start_response("200 OK", [("Content-Type", "application/json")])
            return [b'{"setup_completed": false}']
        start_response("403 Forbidden", [("Content-Type", "application/json")])
        return [b'{"code": "forbidden"}']

    sunucu = BackgroundServer(uygulama)
    sunucu.start()
    try:
        sunucu.wait_until_ready(timeout=10.0)
        check_health(sunucu.base_url, "gizli", path="/api/v1/setup/status/", timeout=5.0)
    finally:
        sunucu.stop()

    assert len(gorulen) == 2  # biri belirteçsiz (403 beklenir), biri belirteçli


def test_saglik_denetimi_korumasiz_sunucuyu_reddeder() -> None:
    """Belirteçsiz istek 200 dönüyorsa koruma çalışmıyordur → açılış durur."""
    pytest.importorskip("waitress")

    def uygulama(environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        start_response("200 OK", [("Content-Type", "application/json")])
        return [b"{}"]

    sunucu = BackgroundServer(uygulama)
    sunucu.start()
    try:
        sunucu.wait_until_ready(timeout=10.0)
        with pytest.raises(ServerStartError) as hata:
            check_health(sunucu.base_url, "gizli", path="/api/v1/setup/status/", timeout=5.0)
    finally:
        sunucu.stop()

    assert "koruma" in str(hata.value).lower()


def test_saglik_denetimi_sunucu_hatasini_yakalar() -> None:
    pytest.importorskip("waitress")

    def uygulama(environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        if "gizli" in environ.get("QUERY_STRING", ""):
            start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
            return [b"patladi"]
        start_response("403 Forbidden", [("Content-Type", "application/json")])
        return [b"{}"]

    sunucu = BackgroundServer(uygulama)
    sunucu.start()
    try:
        sunucu.wait_until_ready(timeout=10.0)
        with pytest.raises(ServerStartError):
            check_health(sunucu.base_url, "gizli", path="/api/v1/setup/status/", timeout=5.0)
    finally:
        sunucu.stop()


def test_ulasilamayan_sunucu_turkce_hata_verir() -> None:
    kapali_port = find_free_port()

    with pytest.raises(ServerStartError):
        check_health(f"http://127.0.0.1:{kapali_port}", "gizli", timeout=1.0)


def test_urlopen_hata_kodunu_yutmaz() -> None:
    """Yardımcı: 403 bir istisna değil, sonuç olarak dönmeli."""
    with pytest.raises(urllib.error.URLError):
        urllib.request.urlopen("http://127.0.0.1:1/", timeout=1)


# ------------------------------------------------------ koruma testleri (§4.1, §13 D2)
#
# "Yalnız 127.0.0.1" değişmezi: yönetim sunucusu başka host kabul etmez, `main.py`
# host vermez ve tüm arayüz adresi (`0.0.0.0`) hiçbir üretim kaynağında geçmez (tek
# muafiyet `window.py`'deki WebView2 sürüm damgası). Aile iskeletinde bu testler ağ
# kataloğu testlerindeydi; katalogla birlikte silinmesinler diye buraya taşındı.

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
DESKTOP_DIR = REPO_ROOT / "desktop"

# Testler tüm arayüz adresini bilerek yazar (reddedildiğini sınamak için); ruff S104
# uyarısı tek yerde susturulur.
TUM_ARAYUZ = "0.0.0.0"  # noqa: S104


def _bos_uygulama(
    environ: dict[str, Any], start_response: Callable[..., Any]
) -> Iterable[bytes]:
    start_response("200 OK", [("Content-Length", "0")])
    return [b""]


@pytest.mark.parametrize("host", [TUM_ARAYUZ, "", "localhost", "192.168.1.5", "::"])
def test_yonetim_sunucusu_yalniz_varsayilan_hostu_kabul_eder(host: str) -> None:
    assert DEFAULT_HOST == "127.0.0.1"

    with pytest.raises(ValueError, match="127.0.0.1"):
        BackgroundServer(_bos_uygulama, host=host)


def test_yonetim_sunucusu_varsayilan_hostla_kurulur() -> None:
    sunucu = BackgroundServer(_bos_uygulama, host=DEFAULT_HOST)

    assert sunucu.base_url.startswith("http://127.0.0.1:")


def test_main_yonetim_sunucusunu_host_vermeden_kurar() -> None:
    agac = ast.parse((DESKTOP_DIR / "main.py").read_text(encoding="utf-8"))
    cagrilar = [
        dugum
        for dugum in ast.walk(agac)
        if isinstance(dugum, ast.Call)
        and isinstance(dugum.func, ast.Name)
        and dugum.func.id == "BackgroundServer"
    ]

    assert cagrilar, "main.py yönetim sunucusunu kurmuyor (desen değişti mi)"
    for cagri in cagrilar:
        assert not any(k.arg == "host" for k in cagri.keywords)
        assert len(cagri.args) == 1  # yalnız uygulama; host konumsal da verilmez


# Taranan üretim kaynakları: masaüstü kabuğu, paket giriş noktası ve backend (ayarlar,
# uygulamalar, ortak modüller). Testler kapsam dışıdır (bu dosya adresi bilerek yazar).
_TARANAN_KOKLER = (
    DESKTOP_DIR,
    REPO_ROOT / "packaging" / "pyinstaller",
    BACKEND_DIR / "config",
    BACKEND_DIR / "apps",
    BACKEND_DIR / "shared",
)
# Bilinçli istisna: `window.py`'deki "0.0.0.0" bir IP değil, kaldırılmış WebView2
# çalışma zamanının bıraktığı sürüm damgasıdır. Muafiyet ATAMA adıyla verilir;
# aynı dosyaya eklenecek başka bir kullanım yine yakalanır.
_MUAF_ATAMALAR = {("desktop/window.py", "_EMPTY_VERSIONS")}


def _uretim_kaynaklari() -> Iterator[Path]:
    for kok in _TARANAN_KOKLER:
        for dosya in sorted(kok.rglob("*.py")):
            parcalar = dosya.relative_to(REPO_ROOT).parts
            if "tests" in parcalar or "migrations" in parcalar:
                continue
            yield dosya


def _tum_arayuz_metinleri(goreli: str, kaynak: str) -> list[int]:
    """Kaynakta "0.0.0.0" içeren metin sabitlerinin (belge dizeleri dahil) satırları."""
    agac = ast.parse(kaynak)
    muaf: set[int] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Assign | ast.AnnAssign) and dugum.value is not None:
            hedefler = dugum.targets if isinstance(dugum, ast.Assign) else [dugum.target]
            if any(isinstance(h, ast.Name) and (goreli, h.id) in _MUAF_ATAMALAR for h in hedefler):
                muaf.update(id(alt) for alt in ast.walk(dugum.value))
    return sorted(
        dugum.lineno
        for dugum in ast.walk(agac)
        if isinstance(dugum, ast.Constant)
        and isinstance(dugum.value, str)
        and TUM_ARAYUZ in dugum.value
        and id(dugum) not in muaf
    )


def test_tum_arayuz_adresi_hicbir_uretim_kaynaginda_gecmez() -> None:
    bulunan: list[str] = []
    for dosya in _uretim_kaynaklari():
        goreli = dosya.relative_to(REPO_ROOT).as_posix()
        kaynak = dosya.read_text(encoding="utf-8")
        bulunan.extend(f"{goreli}:{no}" for no in _tum_arayuz_metinleri(goreli, kaynak))

    assert bulunan == []


def test_yonetim_sunucusu_kaynaginda_tum_arayuz_adresi_hic_gecmez() -> None:
    """`server.py`'de yorum dahil hiçbir yerde geçmez (ham metin taraması)."""
    assert TUM_ARAYUZ not in (DESKTOP_DIR / "server.py").read_text(encoding="utf-8")


def test_tum_arayuz_taramasi_muafiyet_disini_yakalar() -> None:
    """Tarayıcının kendisi: muaf atama geçer; başka ad, dosya ya da belge dizesi yakalanır."""
    kaynak = '"""0.0.0.0 belgede"""\nX = "0.0.0.0"\n_EMPTY_VERSIONS = {"", "0.0.0.0"}\n'

    assert _tum_arayuz_metinleri("desktop/window.py", kaynak) == [1, 2]
    assert _tum_arayuz_metinleri("desktop/main.py", kaynak) == [1, 2, 3]


def test_diger_tum_arayuz_bicimleri_uretim_kaynaginda_yok() -> None:
    """IPv6 `::`, boş host ve `INADDR_ANY` de tüm arayüzlere bağlanır."""
    bulunan: list[str] = []
    for dosya in _uretim_kaynaklari():
        for dugum in ast.walk(ast.parse(dosya.read_text(encoding="utf-8"))):
            if isinstance(dugum, ast.Constant) and dugum.value in {"::", "::0"}:
                bulunan.append(f"{dosya.name}:{dugum.lineno}")
            if isinstance(dugum, ast.Attribute) and dugum.attr in {"INADDR_ANY", "IN6ADDR_ANY"}:
                bulunan.append(f"{dosya.name}:{dugum.lineno}")
            if isinstance(dugum, ast.keyword) and dugum.arg == "host":
                if isinstance(dugum.value, ast.Constant) and dugum.value.value == "":
                    bulunan.append(f"{dosya.name}:{dugum.value.lineno}")

    assert bulunan == []
