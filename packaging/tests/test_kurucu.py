"""Windows kurucusunun (Inno) metin düzeyindeki kuralları (tasarım §4.2, §4.5 T6, TK7).

Inno betiği Docker'da derlenemez (ISCC yerelde ve CI'ın Windows koşusunda
derler); burada sabitlenenler:

* her satır kendi bölümündedir (aile iskeletinin ağ kataloğu paketi testinden
  taşındı: `#if FileExists(...)` dalındaki `Source:` satırı başka bölüme düşerse
  ISCC sürüm derlemesinde kırılır);
* `AppMutex` kullanılmaz; kapanış `OABDefteri.Kapat` olayıyla düzenlidir;
* program ağ servisi sunmaz ve tepsi yoktur: güvenlik duvarı kuralı, HKLM port
  değeri, otomatik başlatma görevi ve "tepside başlat" görevi kurucuda yoktur;
* kurulum yetkisi TK7'dir: `lowest` + `dialog` (kullanıcı başına ya da yönetici).
"""

from __future__ import annotations

import re
from pathlib import Path

PAKET = Path(__file__).resolve().parents[1]
ISS = (PAKET / "windows" / "oab-defteri.iss").read_text(encoding="utf-8")


def _iss_kod_oncesi() -> str:
    return ISS.split("\n[Code]\n", 1)[0]


def _bolumler() -> dict[str, list[str]]:
    """.iss'i bölümlere ayırır; ön işlemci (`#if/#else/#endif`) dalları ayrı değil.

    İki dalın satırları da bulunduğu bölüme sayılır: `#if FileExists(...)` doğru
    çıktığında (sürüm derlemesi WebView2 kurucusunu indirir) satır hangi başlığın
    altındaysa ISCC onu o bölümde okur.
    """
    bolumler: dict[str, list[str]] = {}
    gecerli = ""
    for satir in _iss_kod_oncesi().splitlines():
        basi = re.fullmatch(r"\[(\w+)\]", satir.strip())
        if basi:
            gecerli = basi.group(1)
            bolumler.setdefault(gecerli, [])
            continue
        bolumler.setdefault(gecerli, []).append(satir)
    return bolumler


def test_iss_her_satir_kendi_bolumunde() -> None:
    bolumler = _bolumler()
    for bolum, satirlar in bolumler.items():
        for satir in satirlar:
            s = satir.strip()
            if s.startswith("Source:"):
                assert bolum == "Files", f"`Source:` satırı [{bolum}] altında: {s}"
            if s.startswith("Root:"):
                assert bolum == "Registry", f"`Root:` satırı [{bolum}] altında: {s}"
    assert any("{#WebView2Setup}" in s for s in bolumler["Files"])


def test_kurucu_appmutex_kullanmaz() -> None:
    assert not any(satir.strip().startswith("AppMutex") for satir in ISS.splitlines())


def test_kurucu_ag_kurali_otomatik_baslatma_ve_tepsi_gorevi_tasimaz() -> None:
    """§4.1, §4.5: program ağ servisi sunmaz, tepsisi ve otomatik başlatması yoktur."""
    bolumler = _bolumler()
    assert "Registry" not in bolumler  # HKLM katalog portu değeri sökülmüştür
    assert "UninstallRun" not in bolumler  # otomatik başlatma görevi silme
    gorevler = "\n".join(bolumler["Tasks"])
    assert re.findall(r'^Name: "([^"]+)"', gorevler, flags=re.MULTILINE) == ["desktopicon"]
    for yasak in ("netsh", "schtasks", "gorev-kur.ps1", "--tepside", "KatalogPortu"):
        assert yasak not in ISS, yasak


def test_kurulum_yetkisi_tk7() -> None:
    """TK7 (§15 M-1): kurucu kullanıcı başına ve yönetici kurulumunu birlikte sunar."""
    setup = "\n".join(_bolumler()["Setup"])
    assert re.search(r"^PrivilegesRequired=lowest$", setup, flags=re.MULTILINE)
    assert re.search(r"^PrivilegesRequiredOverridesAllowed=dialog$", setup, flags=re.MULTILINE)


def test_kapanmayan_program_iletisi_tepsiyi_anlatmaz() -> None:
    """§4.2: "OAB Defteri açık. Programı kapatıp Yeniden Dene'ye basın." — tepsi yok (T6)."""
    kod = ISS.split("\n[Code]\n", 1)[1]
    assert "'OAB Defteri açık. Programı kapatıp Yeniden Dene''ye basın.'" in kod
    assert "tepsi" not in kod.casefold()
