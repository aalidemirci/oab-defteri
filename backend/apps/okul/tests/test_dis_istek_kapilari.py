"""Program ağ servisi sunmaz; dış istek TEK kapıdan çıkar (tasarım §4.1, T11).

Program ağ servisi sunmaz: yönetim sunucusu yalnız 127.0.0.1'de, rastgele portta ve
oturum belirteciyle dinler; hiçbir port okul ağına açılmaz. Dış istek yalnız
kullanıcının başlattığı güncelleme denetiminden çıkar — "Şimdi denetle" düğmesiyle,
GitHub'dan (kullanıcı kararı 27.09.2026). Aile iskeletinin ikinci kapısı (ISBN künye
sorgusu) OAB'de yoktur. **Açılışta ağ yok, telemetri yok.** Bu dosya kuralı KAYNAK düzeyinde kilitler; açılış
zincirinin kendisi `desktop/tests/test_acilista_dis_istek.py`'de gerçek süreçte ve
ağ çağrıları tuzaklanmış hâlde koşar.

1. **Ağ istemcisi kullanan modüller kapalı bir listedir.** Backend ve masaüstü
   kaynağında (testler hariç) `urllib.request`, `http.client`, `socket`, `ssl`,
   `requests`, `webbrowser` … import eden her modül aşağıdaki listede ve
   gerekçesiyle durur. Yeni bir modül ağ istemcisi import ederse test düşer:
   ekleyen, bunun bir dış istek kapısı olup olmadığına bilinçli karar verir.
2. **Güncelleme modülünün istek atan işlevlerini** yalnız güncelleme uçları çağırır
   (`apps/okul/views.py`). Masaüstü kabuğu (açılış, gün değişimi kapısı) güncelleme
   modülünü hiç import etmez.

Tarama `ast` iledir: yorumdaki "socket" sözcüğü sayılmaz, import ağacı sayılır.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

#: Ağ istemcisi sayılan modüller (kök adıyla ya da tam adla).
AG_ISTEMCILERI = frozenset(
    {
        "socket",
        "ssl",
        "socketserver",
        "http.client",
        "http.server",
        "urllib.request",
        "requests",
        "httpx",
        "aiohttp",
        "ftplib",
        "smtplib",
        "telnetlib",
        "xmlrpc.client",
        "webbrowser",
    }
)

#: Ağ istemcisi import etmesine izin verilen modüller ve gerekçeleri (depo köküne göre).
IZINLI: dict[str, str] = {
    "backend/apps/okul/services/updates.py": (
        "Kapı 1: güncelleme denetimi — yalnız 'Şimdi denetle' düğmesiyle (GitHub)"
    ),
    "desktop/server.py": "Yönetim sunucusu ve 127.0.0.1 sağlık denetimi (dışarı çıkmaz)",
    "desktop/instance_channel.py": "Tek kopya kanalı (yerel soket / adlı olay)",
}

#: `updates` modülünü import edebilen modüller ve kullanabilecekleri adlar.
GUNCELLEME_KULLANICILARI: dict[str, frozenset[str] | None] = {
    # None: güncelleme uçları — modülün tamamı (düğmenin arkası).
    "backend/apps/okul/views.py": None,
}


def _depo_koku() -> Path:
    """Yerelde `depo/backend/...`; konteynerde backend `/app`, depo `/repo`."""
    yerel = Path(__file__).resolve().parents[4]
    for kok in (yerel, Path("/repo")):
        if (kok / "desktop").is_dir() and (kok / "backend").is_dir():
            return kok
    pytest.fail(f"Depo kökü bulunamadı ({yerel} ya da /repo).")


def _kaynaklar() -> list[Path]:
    kok = _depo_koku()
    dosyalar: list[Path] = []
    for dizin in (kok / "backend", kok / "desktop"):
        for yol in dizin.rglob("*.py"):
            parcalar = set(yol.relative_to(kok).parts)
            if parcalar & {"tests", "migrations", "node_modules", "__pycache__"}:
                continue
            if yol.name in {"conftest.py"} or yol.name.startswith("test_"):
                continue
            dosyalar.append(yol)
    assert len(dosyalar) > 50, "tarama kaynakları bulamadı (yanlış yeşil)"
    return dosyalar


def _importlar(agac: ast.AST) -> set[str]:
    """Kaynağın import ettiği modüllerin tam adları (`from x import y` → x ve x.y)."""
    adlar: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Import):
            adlar.update(ad.name for ad in dugum.names)
        elif isinstance(dugum, ast.ImportFrom) and dugum.module and dugum.level == 0:
            adlar.add(dugum.module)
            adlar.update(f"{dugum.module}.{ad.name}" for ad in dugum.names)
    return adlar


def _ag_istemcisi_mi(ad: str) -> bool:
    return ad in AG_ISTEMCILERI or ad.split(".")[0] in {k for k in AG_ISTEMCILERI if "." not in k}


def _goreli(yol: Path) -> str:
    return yol.relative_to(_depo_koku()).as_posix()


def test_ag_istemcisi_import_eden_moduller_kapali_listededir() -> None:
    bulunan: dict[str, set[str]] = {}
    for yol in _kaynaklar():
        agac = ast.parse(yol.read_text(encoding="utf-8"))
        ag = {ad for ad in _importlar(agac) if _ag_istemcisi_mi(ad)}
        if ag:
            bulunan[_goreli(yol)] = ag

    izinsiz = {yol: sorted(ad) for yol, ad in bulunan.items() if yol not in IZINLI}
    assert izinsiz == {}, (
        "Ağ istemcisi import eden yeni modül: dış istek yalnız kullanıcının başlattığı "
        f"güncelleme denetiminden çıkar (tasarım §4.1). {izinsiz}"
    )
    # Liste bayatlamasın: izinli her modül gerçekten ağ istemcisi kullanıyor.
    assert set(IZINLI) == set(bulunan), sorted(set(IZINLI) ^ set(bulunan))


def _updates_kullanimi(agac: ast.AST) -> tuple[bool, set[str]]:
    """(modül `updates`'i import ediyor mu, `updates.` üzerinden/`from … import` edilen adlar)."""
    import_eder = False
    adlar: set[str] = set()
    takma: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.ImportFrom) and dugum.module == "apps.okul.services":
            for ad in dugum.names:
                if ad.name == "updates":
                    import_eder = True
                    takma.add(ad.asname or ad.name)
        elif isinstance(dugum, ast.ImportFrom) and dugum.module == "apps.okul.services.updates":
            import_eder = True
            adlar.update(ad.name for ad in dugum.names)
        elif isinstance(dugum, ast.Import):
            if any(ad.name == "apps.okul.services.updates" for ad in dugum.names):
                import_eder = True
    for dugum in ast.walk(agac):
        if (
            isinstance(dugum, ast.Attribute)
            and isinstance(dugum.value, ast.Name)
            and dugum.value.id in takma
        ):
            adlar.add(dugum.attr)
    return import_eder, adlar


def test_guncelleme_denetimini_yalniz_guncelleme_uclari_cagirir() -> None:
    """Açılış, gün değişimi kapısı ya da belge üreticisi denetim BAŞLATMAZ."""
    kullananlar: dict[str, set[str]] = {}
    for yol in _kaynaklar():
        goreli = _goreli(yol)
        if goreli == "backend/apps/okul/services/updates.py":
            continue
        import_eder, adlar = _updates_kullanimi(ast.parse(yol.read_text(encoding="utf-8")))
        if import_eder:
            kullananlar[goreli] = adlar

    assert set(kullananlar) == set(GUNCELLEME_KULLANICILARI), sorted(kullananlar)
    for goreli, adlar in kullananlar.items():
        izinli = GUNCELLEME_KULLANICILARI[goreli]
        if izinli is None:
            continue
        assert adlar <= izinli, f"{goreli}: {sorted(adlar - izinli)}"


def test_masaustu_kabugu_guncelleme_modulunu_import_etmez() -> None:
    """Açılış zinciri ve `od-gunluk` (gün değişimi kapısı) masaüstündedir: dış istek kapısı
    orada yok."""
    kok = _depo_koku()
    for yol in (kok / "desktop").glob("*.py"):
        adlar = _importlar(ast.parse(yol.read_text(encoding="utf-8")))
        yasak = {
            ad
            for ad in adlar
            if ad.startswith("apps.okul.services.updates") or ad == "apps.okul.services.updates"
        }
        assert not yasak, f"{yol.name}: {sorted(yasak)}"
