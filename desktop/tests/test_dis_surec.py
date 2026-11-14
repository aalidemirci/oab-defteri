"""Dış süreçlerin temiz ortamı testleri (saha bulgusu K-P2, Pardus 25, 12.11.2026).

PyInstaller'ın onedir paketi süreç ortamına `LD_LIBRARY_PATH=<paket>/_internal` yazar; programın
açtığı zenity bu yolu devralıp pakete gömülü bullseye kütüphanelerine bağlanır ve çöker
(`desktop/dis_surec.py` başlığı). Burada ortamın düzeltilmesi, Windows'ta hiçbir şeyin değişmemesi
ve programdaki BÜTÜN dış süreç çağrılarının temiz ortamı vermesi (kaynak düzeyinde) sınanır.
Gerçek zenity'nin paket ortamında çöktüğü, temiz ortamla açıldığı debian:13 kabında gösterildi
(`desktop/dis_surec.py` başlığı); burada `test_gercek_alt_surec_paketin_yolunu_devralmaz` aynı
kuralı gerçek bir alt süreçle sınar. Bağımsız denetimin (13.11.2026) üç bulgusu da burada bağlıdır:
programın ve pywebview'ın değişkenleri (`QTWEBENGINE_CHROMIUM_FLAGS`'teki kamera/mikrofon bayrağı)
dış sürece geçmez; dış bağlantı açıcısı `webbrowser` kaydına girmez, kayıt yarışı yoktur; kaynak
taraması takma adla ve doğrudan içe aktarmayı da görür.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from desktop import dis_surec, yerel_pencere
from desktop.dis_surec import (
    ENV_OTURUM_BELIRTECI,
    ENV_QT_PLATFORM_KANCADAN,
    TemizOrtamTarayicisi,
    dis_tarayiciyi_bagla,
    temiz_ortam,
)

DEPO = Path(__file__).resolve().parents[2]
PAKET = "/opt/oab-defteri/_internal"


def _paket_ortami(**ek: str) -> dict[str, str]:
    """Pardus'ta paketli programın ortamı (debian:13 kabında `/proc/<pid>/environ`'dan)."""
    ortam = {
        "HOME": "/home/uydurma",
        "PATH": "/usr/bin:/bin",
        "LANG": "tr_TR.UTF-8",
        "DISPLAY": ":0",
        "LD_LIBRARY_PATH": PAKET,
        "_PYI_ARCHIVE_FILE": "/opt/oab-defteri/oab-defteri",
        "_PYI_APPLICATION_HOME_DIR": PAKET,
        "_PYI_PARENT_PROCESS_LEVEL": "1",
        "_PYI_LINUX_PROCESS_NAME": "oab-defteri",
        "QT_PLUGIN_PATH": f"{PAKET}/PySide6/Qt/plugins",
        "QML2_IMPORT_PATH": f"{PAKET}/PySide6/Qt/qml",
        "QT_API": "pyside6",
    }
    ortam.update(ek)
    return ortam


def _temiz(ortam: dict[str, str], *, donmus: bool = True) -> dict[str, str]:
    sonuc = temiz_ortam(platform="linux", ortam=ortam, donmus=donmus, paket_koku=PAKET)
    assert sonuc is not None
    return sonuc


# ------------------------------------------------------------------ ortam kuralları


def test_kutuphane_yolu_onceki_degerine_doner() -> None:
    """PyInstaller önceki değeri `LD_LIBRARY_PATH_ORIG`'de saklar (`pyi_utils_posix.c`)."""
    ortam = _paket_ortami(
        LD_LIBRARY_PATH=f"{PAKET}:/usr/local/lib/uydurma",
        LD_LIBRARY_PATH_ORIG="/usr/local/lib/uydurma",
    )

    temiz = _temiz(ortam)

    assert temiz["LD_LIBRARY_PATH"] == "/usr/local/lib/uydurma"
    assert "LD_LIBRARY_PATH_ORIG" not in temiz


def test_onceki_deger_yoksa_kutuphane_yolu_silinir() -> None:
    """Değişken açılışta yoksa önyükleyici `_ORIG` yazmaz: dış süreçte de olmamalıdır."""
    temiz = _temiz(_paket_ortami())

    assert "LD_LIBRARY_PATH" not in temiz
    assert "LD_LIBRARY_PATH_ORIG" not in temiz


def test_bos_onceki_deger_bos_olarak_korunur() -> None:
    ortam = _paket_ortami(LD_LIBRARY_PATH=f"{PAKET}:", LD_LIBRARY_PATH_ORIG="")

    assert _temiz(ortam)["LD_LIBRARY_PATH"] == ""


def test_onyukleyicinin_degiskenleri_atilir() -> None:
    temiz = _temiz(_paket_ortami())

    assert not [ad for ad in temiz if ad.startswith("_PYI_")]


def test_paketin_qt_dizinini_gosteren_degiskenler_atilir() -> None:
    """PySide6 kancası bunları paketin Qt'sine yazar; kdialog sistem Qt'siyle onları yüklerdi."""
    temiz = _temiz(_paket_ortami())

    assert "QT_PLUGIN_PATH" not in temiz
    assert "QML2_IMPORT_PATH" not in temiz


def test_paketin_disini_gosteren_qt_degiskeni_korunur() -> None:
    temiz = _temiz(_paket_ortami(QT_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/qt6/plugins"))

    assert temiz["QT_PLUGIN_PATH"] == "/usr/lib/x86_64-linux-gnu/qt6/plugins"


def test_paket_kokuyle_baslayan_baska_dizin_paketin_ici_sayilmaz() -> None:
    """`/opt/oab-defteri/_internal-eski` paketin içi değildir (yol parçası karşılaştırılır)."""
    temiz = _temiz(_paket_ortami(QT_PLUGIN_PATH=f"{PAKET}-eski/plugins"))

    assert temiz["QT_PLUGIN_PATH"] == f"{PAKET}-eski/plugins"


def test_kancanin_kurdugu_qt_platformu_dis_surece_gecmez() -> None:
    temiz = _temiz(_paket_ortami(QT_QPA_PLATFORM="xcb", **{ENV_QT_PLATFORM_KANCADAN: "1"}))

    assert "QT_QPA_PLATFORM" not in temiz
    assert ENV_QT_PLATFORM_KANCADAN not in temiz


def test_disaridan_verilen_qt_platformu_korunur() -> None:
    """İşaret yoksa değeri kullanıcı vermiştir (sahada teşhis): dış süreç de onu alır."""
    temiz = _temiz(_paket_ortami(QT_QPA_PLATFORM="wayland"))

    assert temiz["QT_QPA_PLATFORM"] == "wayland"


def test_oturum_belirteci_dis_surece_gecmez() -> None:
    temiz = _temiz(_paket_ortami(**{ENV_OTURUM_BELIRTECI: "uydurma-belirtec"}))

    assert ENV_OTURUM_BELIRTECI not in temiz


def test_oturum_belirteci_degisken_adi_oturum_koruyucusuyla_aynidir() -> None:
    """`desktop.session_guard` Django'yu içe aktarır, bu modül aktarmaz: ad iki yerde yazılıdır."""
    from desktop.session_guard import ENV_TOKEN

    assert ENV_OTURUM_BELIRTECI == ENV_TOKEN


def test_evrak_yazi_tipi_yapilandirmasi_dis_surece_gecmez() -> None:
    conf = "/home/uydurma/.cache/oab-defteri/fonts.conf"
    temiz = _temiz(_paket_ortami(FONTCONFIG_FILE=conf, OD_EVRAK_FONTCONFIG=conf))

    assert "FONTCONFIG_FILE" not in temiz


def test_kullanicinin_yazi_tipi_yapilandirmasi_korunur() -> None:
    temiz = _temiz(
        _paket_ortami(FONTCONFIG_FILE="/etc/uydurma.conf", OD_EVRAK_FONTCONFIG="/baska.conf")
    )

    assert temiz["FONTCONFIG_FILE"] == "/etc/uydurma.conf"


def test_oteki_degiskenler_aynen_gecer() -> None:
    temiz = _temiz(_paket_ortami())

    for ad in ("HOME", "PATH", "LANG", "DISPLAY"):
        assert temiz[ad] == _paket_ortami()[ad]


#: debian:13 kabında paketli programın `QtWebEngineProcess`'inin ortamında görülenler (bağımsız
#: denetim 13.11.2026) ve programın öteki değişkenleri; değerler uydurmadır.
_PROGRAMIN_DEGISKENLERI = {
    "QTWEBENGINE_CHROMIUM_FLAGS": (
        "--use-fake-ui-for-media-stream --enable-features=AutoplayIgnoreWebAudio"
    ),
    "QTWEBENGINE_REMOTE_DEBUGGING": "8228",
    "force_s3tc_enable": "true",
    "OD_DATA_DIR": "/home/uydurma/oab-veri",
    "OD_APP_HOME": "/home/uydurma/oab-veri",
    "OD_FRONTEND_DIR": f"{PAKET}/frontend/dist",
    "OD_EVRAK_FONTCONFIG": "/home/uydurma/.cache/oab-defteri/fonts.conf",
    "OD_ONCEKI_OTURUM": "1",
    "OD_RTHOOK_UYARI": "uydurma",
    "DJANGO_SETTINGS_MODULE": "config.settings",
    "PYSIDE6_OPTION_PYTHON_ENUM": "1",
    "QT_API": "pyside6",
    "QT_STYLE_OVERRIDE": "",
}


@pytest.mark.parametrize("ad", sorted(_PROGRAMIN_DEGISKENLERI))
def test_programin_ve_bilesenlerinin_degiskenleri_dis_surece_gecmez(ad: str) -> None:
    """pywebview'ın bayrağıyla açılan QtWebEngine tarayıcısı kamera/mikrofonu sormadan verirdi."""
    temiz = _temiz(_paket_ortami(**{ad: _PROGRAMIN_DEGISKENLERI[ad]}))

    assert ad not in temiz


def test_program_degiskenleri_gelistirme_ortaminda_da_atilir() -> None:
    temiz = _temiz(dict(_PROGRAMIN_DEGISKENLERI), donmus=False)

    assert temiz == {}


def test_dolu_qt_stili_kullanicinindir_korunur() -> None:
    """pywebview stil değişkenini boş yazar; dolu değer kullanıcının oturumundandır."""
    temiz = _temiz(_paket_ortami(QT_STYLE_OVERRIDE="Fusion"))

    assert temiz["QT_STYLE_OVERRIDE"] == "Fusion"


def test_masaustu_oturumunun_degiskenleri_korunur() -> None:
    """Kural izin listesi değildir: zenity ve tarayıcı oturumun değişkenleriyle açılır."""
    oturum = {
        "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
        "XDG_RUNTIME_DIR": "/run/user/1000",
        "XDG_CURRENT_DESKTOP": "XFCE",
        "XDG_SESSION_TYPE": "x11",
        "XAUTHORITY": "/home/uydurma/.Xauthority",
        "LC_ALL": "tr_TR.UTF-8",
    }

    temiz = _temiz(_paket_ortami(**oturum))

    assert {ad: temiz[ad] for ad in oturum} == oturum


def test_gelistirmede_kutuphane_yolu_kullanicinindir() -> None:
    """Donmuş değilken `LD_LIBRARY_PATH` PyInstaller'ın değildir: dokunulmaz."""
    ortam = {"LD_LIBRARY_PATH": "/usr/local/lib/uydurma", "_PYI_UYDURMA": "1"}

    temiz = _temiz(ortam, donmus=False)

    assert temiz["LD_LIBRARY_PATH"] == "/usr/local/lib/uydurma"
    assert temiz["_PYI_UYDURMA"] == "1"


def test_surec_ortami_degismez(monkeypatch: pytest.MonkeyPatch) -> None:
    """Program kendi yolunda sürer: düzeltme kopyadadır."""
    monkeypatch.setenv("LD_LIBRARY_PATH", PAKET)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    temiz = temiz_ortam(platform="linux")

    assert temiz is not None and "LD_LIBRARY_PATH" not in temiz
    assert os.environ["LD_LIBRARY_PATH"] == PAKET


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_windowsta_ortam_degismez(platform: str) -> None:
    """`None`: çağrı yeri `env=None` verir, süreç ortamı eskisi gibi devralır."""
    assert temiz_ortam(platform=platform, ortam=_paket_ortami(), donmus=True) is None


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX alt süreci")
def test_gercek_alt_surec_paketin_yolunu_devralmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LD_LIBRARY_PATH", PAKET)
    monkeypatch.delenv("LD_LIBRARY_PATH_ORIG", raising=False)
    monkeypatch.setenv("_PYI_ARCHIVE_FILE", "/opt/oab-defteri/oab-defteri")
    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--use-fake-ui-for-media-stream")
    monkeypatch.setenv("OD_DATA_DIR", "/home/uydurma/oab-veri")
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    cikti = subprocess.run(  # noqa: S603 — sabit argümanlar, kabuk yok
        ["/usr/bin/env"], env=temiz_ortam(), capture_output=True, text=True, check=True
    ).stdout

    assert "LD_LIBRARY_PATH" not in cikti and "_PYI_" not in cikti
    assert "QTWEBENGINE_" not in cikti and "OD_DATA_DIR" not in cikti


# ----------------------------------------------------------- dış bağlantı açıcısı


class _SahteSurec:
    def __init__(self) -> None:
        self.beklendi = threading.Event()

    def wait(self) -> int:
        self.beklendi.set()
        return 0


class _Baslatici:
    def __init__(self, hata: Exception | None = None) -> None:
        self.hata = hata
        self.cagrilar: list[tuple[list[str], dict[str, Any]]] = []
        self.surecler: list[_SahteSurec] = []

    def __call__(self, argv: list[str], **anahtarlar: Any) -> _SahteSurec:
        self.cagrilar.append((argv, anahtarlar))
        if self.hata is not None:
            raise self.hata
        self.surecler.append(_SahteSurec())
        return self.surecler[-1]


class _EskiAcici:
    """pywebview Qt kolunun `webbrowser` modülü: yalnız `open`'ı kullanılır."""

    def __init__(self, sonuc: bool = True) -> None:
        self.sonuc = sonuc
        self.cagrilar: list[tuple[str, int, bool]] = []

    def open(self, url: str, new: int = 0, autoraise: bool = True) -> bool:
        self.cagrilar.append((url, new, autoraise))
        return self.sonuc


def test_baglanti_xdg_opena_temiz_ortamla_verilir(monkeypatch: pytest.MonkeyPatch) -> None:
    baslatici = _Baslatici()
    monkeypatch.setattr(subprocess, "Popen", baslatici)
    monkeypatch.setattr(shutil, "which", lambda ad: f"/usr/bin/{ad}")
    monkeypatch.setattr(dis_surec, "temiz_ortam", lambda: {"TEMIZ": "1"})
    eski = _EskiAcici()

    assert TemizOrtamTarayicisi(eski.open).open("https://okulapp.org/oab-defteri/", 2) is True

    ((argv, anahtarlar),) = baslatici.cagrilar
    assert argv == ["/usr/bin/xdg-open", "https://okulapp.org/oab-defteri/"]
    assert anahtarlar["env"] == {"TEMIZ": "1"}
    assert anahtarlar["start_new_session"] is True
    assert eski.cagrilar == []


def test_xdg_open_sureci_arka_planda_beklenir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bağımsız denetim 13.11.2026: beklenmeyen `xdg-open` zombi kalıyor, ResourceWarning basıyordu."""
    baslatici = _Baslatici()
    monkeypatch.setattr(subprocess, "Popen", baslatici)
    monkeypatch.setattr(shutil, "which", lambda ad: f"/usr/bin/{ad}")

    TemizOrtamTarayicisi().open("https://okulapp.org/")

    assert baslatici.surecler[0].beklendi.wait(5)


def test_xdg_open_yoksa_pywebviewin_eski_yolu_denenir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda ad: None)
    eski = _EskiAcici(sonuc=True)

    assert TemizOrtamTarayicisi(eski.open).open("https://okulapp.org/", 2, True) is True
    assert eski.cagrilar == [("https://okulapp.org/", 2, True)]


def test_xdg_open_ve_eski_yol_yoksa_false_doner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda ad: None)

    assert TemizOrtamTarayicisi().open("https://okulapp.org/") is False


def test_baglanti_acilamazsa_false_doner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "Popen", _Baslatici(OSError("yok")))
    monkeypatch.setattr(shutil, "which", lambda ad: f"/usr/bin/{ad}")

    assert TemizOrtamTarayicisi().open("https://okulapp.org/") is False


def _arka_uc(eski: _EskiAcici | None = None) -> SimpleNamespace:
    """pywebview `webview.platforms.qt` modülünün kullandığımız yüzeyi."""
    return SimpleNamespace(webbrowser=eski if eski is not None else _EskiAcici())


def test_linuxta_arka_ucun_baglanti_acicisi_temiz_ortamlisiyla_degisir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shutil, "which", lambda ad: None)
    eski = _EskiAcici()
    arka_uc = _arka_uc(eski)

    assert dis_tarayiciyi_bagla(arka_uc, platform="linux") is True

    assert isinstance(arka_uc.webbrowser, TemizOrtamTarayicisi)
    # `NavigationHandler`'ın çağrısı: `webbrowser.open(url, 2, True)`; xdg-open yoksa eski yol.
    assert arka_uc.webbrowser.open("https://okulapp.org/", 2, True) is True
    assert eski.cagrilar == [("https://okulapp.org/", 2, True)]


def test_ikinci_baglama_aciciyi_yeniden_sarmaz() -> None:
    """`webview.initialize` birden çok çağrılabilir: yedek yine pywebview'ın eski yoludur."""
    arka_uc = _arka_uc()
    dis_tarayiciyi_bagla(arka_uc, platform="linux")
    ilk = arka_uc.webbrowser

    assert dis_tarayiciyi_bagla(arka_uc, platform="linux") is True
    assert arka_uc.webbrowser is ilk


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_windowsta_arka_ucun_baglanti_acicisina_dokunulmaz(platform: str) -> None:
    eski = _EskiAcici()
    arka_uc = _arka_uc(eski)

    assert dis_tarayiciyi_bagla(arka_uc, platform=platform) is False
    assert arka_uc.webbrowser is eski


def test_acicisi_olmayan_arka_uc_programi_durdurmaz() -> None:
    assert dis_tarayiciyi_bagla(SimpleNamespace(), platform="linux") is False


def test_baglama_esanlidir_dis_surec_acmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kayıt yarışı yok (bağımsız denetim 13.11.2026): Python'un `webbrowser` kaydı yerine arka ucun
    adı değişir; `xdg-settings` gibi bir süreç hiç başlamaz, bağlama döndüğünde açıcı yerindedir."""
    acilan: list[Any] = []
    for ad in ("Popen", "run", "check_output", "call"):
        monkeypatch.setattr(subprocess, ad, lambda *a, **k: acilan.append(a))
    arka_uc = _arka_uc()

    dis_tarayiciyi_bagla(arka_uc, platform="linux")

    assert acilan == []
    assert isinstance(arka_uc.webbrowser, TemizOrtamTarayicisi)


def test_dis_surec_modulu_webbrowseri_ice_aktarmaz() -> None:
    """Ağ istemcisi kapısının izin listesine girmez (`test_dis_istek_kapilari.py` `IZINLI`)."""
    agac = ast.parse((DEPO / "desktop" / "dis_surec.py").read_text(encoding="utf-8"))
    aktarilan = {
        ad.name for dugum in ast.walk(agac) if isinstance(dugum, ast.Import) for ad in dugum.names
    } | {dugum.module for dugum in ast.walk(agac) if isinstance(dugum, ast.ImportFrom)}

    assert "webbrowser" not in aktarilan


# ------------------------------------------- bütün dış süreçler temiz ortamla başlar

#: Programın çalışan kodu: masaüstü kabuğu, backend ve paketin giriş/kanca betikleri.
_KAYNAK_DIZINLERI = ("desktop", "backend", "packaging/pyinstaller")
_SUBPROCESS_ISLEVLERI = frozenset(
    {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
)
#: Ortam veremeyen ya da kabuk açan yollar: hiç kullanılmaz.
_YASAK_OS = frozenset(
    {"system", "popen", "posix_spawn", "posix_spawnp", "startfile"}
    | {f"exec{ek}" for ek in ("l", "le", "lp", "lpe", "v", "ve", "vp", "vpe")}
    | {f"spawn{ek}" for ek in ("l", "le", "lp", "lpe", "v", "ve", "vp", "vpe")}
)
_YASAK_ADLAR = frozenset({"QProcess", "QDesktopServices"})
#: Takma adla ya da `from … import` ile içe aktarılamayan modüller (tarama onları adıyla izler);
#: `webbrowser` hiç içe aktarılmaz (dış bağlantı `desktop.dis_surec`'ten geçer).
_ADIYLA_KALACAK = frozenset({"subprocess", "os", "webbrowser"})
#: `subprocess` işlevinin çağrılmadan değer olarak geçtiği izinli yerler (enjekte edilen başlatıcı);
#: ortamı oradaki birim testleri bağlar.
_DEGER_OLARAK_IZINLI = {
    (
        "desktop/yerel_pencere.py",
        "Popen",
    ): "test_yerel_pencere.py::test_pencere_temiz_ortamla_acilir",
}


def _calisan_kaynaklar() -> list[Path]:
    dosyalar: list[Path] = []
    for dizin in _KAYNAK_DIZINLERI:
        for yol in (DEPO / dizin).rglob("*.py"):
            parcalar = set(yol.relative_to(DEPO).parts)
            if parcalar & {"tests", "migrations", "node_modules", "__pycache__"}:
                continue
            if yol.name == "conftest.py" or yol.name.startswith("test_"):
                continue
            dosyalar.append(yol)
    assert len(dosyalar) > 50, "tarama kaynakları bulamadı (yanlış yeşil)"
    return dosyalar


def _temiz_ortam_mi(cagri: ast.Call) -> bool:
    ortam = next((k.value for k in cagri.keywords if k.arg == "env"), None)
    return (
        isinstance(ortam, ast.Call)
        and isinstance(ortam.func, ast.Name)
        and ortam.func.id == "temiz_ortam"
    )


def _ice_aktarma_bulgulari(goreli: str, dugum: ast.AST) -> list[str]:
    bulgular: list[str] = []
    if isinstance(dugum, ast.Import):
        for ad in dugum.names:
            kok = ad.name.split(".")[0]
            if kok == "webbrowser":
                bulgular.append(f"{goreli}:{dugum.lineno} import webbrowser")
            elif kok in _ADIYLA_KALACAK and ad.asname not in (None, kok):
                bulgular.append(f"{goreli}:{dugum.lineno} import {ad.name} as {ad.asname}")
    elif isinstance(dugum, ast.ImportFrom) and dugum.module is not None:
        kok = dugum.module.split(".")[0]
        if kok in {"subprocess", "webbrowser"}:
            bulgular.append(f"{goreli}:{dugum.lineno} from {dugum.module} import")
        elif kok == "os":
            for ad in dugum.names:
                if ad.name in _YASAK_OS or ad.name == "*":
                    bulgular.append(f"{goreli}:{dugum.lineno} from os import {ad.name}")
    return bulgular


def _kaynak_bulgulari(goreli: str, metin: str) -> tuple[list[str], list[str]]:
    """Tek kaynağın (temiz ortam vermeyen subprocess çağrıları, yasak yollar) — `dosya:satır`."""
    ortamsiz: list[str] = []
    yasak: list[str] = []
    agac = ast.parse(metin)
    cagrilan: set[int] = set()
    abone: set[int] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Call):
            cagrilan.add(id(dugum.func))
        elif isinstance(dugum, ast.Subscript):
            abone.add(id(dugum.value))  # `subprocess.Popen[bytes]`: tür ipucu
    for dugum in ast.walk(agac):
        yasak.extend(_ice_aktarma_bulgulari(goreli, dugum))
        if isinstance(dugum, ast.Name) and dugum.id in _YASAK_ADLAR:
            yasak.append(f"{goreli}:{dugum.lineno} {dugum.id}")
        if not isinstance(dugum, ast.Attribute):
            continue
        ad = dugum.attr
        if ad in _YASAK_ADLAR:
            yasak.append(f"{goreli}:{dugum.lineno} .{ad}")
            continue
        kok = dugum.value.id if isinstance(dugum.value, ast.Name) else None
        if kok == "os" and ad in _YASAK_OS:
            yasak.append(f"{goreli}:{dugum.lineno} os.{ad}")
        elif kok == "webbrowser":
            yasak.append(f"{goreli}:{dugum.lineno} webbrowser.{ad}")
        elif kok == "subprocess" and ad in _SUBPROCESS_ISLEVLERI:
            if id(dugum) in abone:
                continue
            if id(dugum) not in cagrilan:
                if (goreli, ad) not in _DEGER_OLARAK_IZINLI:
                    yasak.append(f"{goreli}:{dugum.lineno} subprocess.{ad} (değer olarak)")
                continue
    for dugum in ast.walk(agac):
        if (
            isinstance(dugum, ast.Call)
            and isinstance(dugum.func, ast.Attribute)
            and isinstance(dugum.func.value, ast.Name)
            and dugum.func.value.id == "subprocess"
            and dugum.func.attr in _SUBPROCESS_ISLEVLERI
            and not _temiz_ortam_mi(dugum)
        ):
            ortamsiz.append(f"{goreli}:{dugum.lineno} subprocess.{dugum.func.attr}")
    return ortamsiz, yasak


def _dis_surec_cagrilari() -> tuple[list[str], list[str]]:
    """Bütün çalışan kaynakların bulguları (`_kaynak_bulgulari`)."""
    ortamsiz: list[str] = []
    yasak: list[str] = []
    for yol in _calisan_kaynaklar():
        bulgu = _kaynak_bulgulari(yol.relative_to(DEPO).as_posix(), yol.read_text(encoding="utf-8"))
        ortamsiz.extend(bulgu[0])
        yasak.extend(bulgu[1])
    return ortamsiz, yasak


@pytest.mark.parametrize(
    "kaynak",
    [
        "from subprocess import run\nrun(['zenity'])",
        "import subprocess as sp\nsp.Popen(['zenity'])",
        "import webbrowser as wb\nwb.open('https://okulapp.org/')",
        "import webbrowser\nwebbrowser.get().open('https://okulapp.org/')",
        "from webbrowser import open as ac\nac('https://okulapp.org/')",
        "from os import execv\nexecv('/usr/bin/zenity', ['zenity'])",
        "import os as isletim\nisletim.system('zenity')",
        "from os import *",
        "from PySide6 import QtCore\nQtCore.QProcess()",
        "import subprocess\nbaslat = subprocess.Popen\nbaslat(['zenity'])",
        "import subprocess\nsubprocess.run(['zenity'])",
        "import subprocess\nsubprocess.run(['zenity'], env=None)",
    ],
    ids=[
        "from_subprocess",
        "subprocess_takma_ad",
        "webbrowser_takma_ad",
        "webbrowser_get",
        "from_webbrowser",
        "from_os_exec",
        "os_takma_ad",
        "from_os_yildiz",
        "qtcore_qprocess",
        "deger_olarak_baslatici",
        "ortamsiz_cagri",
        "baska_ortam",
    ],
)
def test_tarama_dolambacli_dis_surec_yollarini_yakalar(kaynak: str) -> None:
    """Bağımsız denetim 13.11.2026: takma ad ve doğrudan içe aktarma taramayı deliyordu."""
    ortamsiz, yasak = _kaynak_bulgulari("desktop/uydurma.py", kaynak)

    assert ortamsiz or yasak


def test_tarama_temiz_ortamli_cagriyi_ve_tur_ipucunu_gecirir() -> None:
    kaynak = (
        "import subprocess\n"
        "def f(s: subprocess.Popen[bytes]) -> None:\n"
        "    subprocess.run(['zenity'], env=temiz_ortam())\n"
        "    subprocess.PIPE, subprocess.DEVNULL\n"
    )

    assert _kaynak_bulgulari("desktop/uydurma.py", kaynak) == ([], [])


def test_butun_dis_surec_cagrilari_temiz_ortam_verir() -> None:
    """Yeni bir dış süreç `env=temiz_ortam()` vermezse düşer (modül başlığı: "Bütün dış süreçler")."""
    ortamsiz, yasak = _dis_surec_cagrilari()

    assert ortamsiz == []
    assert yasak == []


def test_tarama_dis_surec_yerlerini_gercekten_gorur() -> None:
    """Yanlış yeşile karşı: bilinen çağrı yerleri taramada görünür."""
    goruldu: set[str] = set()
    for yol in _calisan_kaynaklar():
        metin = yol.read_text(encoding="utf-8")
        if "env=temiz_ortam()" in metin:
            goruldu.add(yol.relative_to(DEPO).as_posix())

    assert {"desktop/dialogs.py", "desktop/dis_surec.py", "desktop/yerel_pencere.py"} <= goruldu


def test_yerel_pencere_sureci_subprocess_ile_baslatir() -> None:
    """`yerel_pencere` süreci enjekte edilen başlatıcıyla açar; varsayılanı `subprocess.Popen`'dır
    (ortamı vermesi `test_yerel_pencere.py`'de sınanır)."""
    pencere = yerel_pencere.YerelDosyaPenceresi()

    assert pencere._baslat is subprocess.Popen


# ------------------------------------------- yeni pencere isteği (saha bulgusu K-yeni-1)

_ANA_ADRES = "http://127.0.0.1:53817/hakkinda"


@pytest.mark.parametrize(
    ("adres", "tarayicida", "beklenen"),
    [
        ("https://polyformproject.org/licenses/noncommercial/1.0.0/", True, "tarayicida"),
        ("http://okulapp.org/oab-defteri", True, "tarayicida"),
        ("https://okulapp.org/oab-defteri", False, "ana_pencerede"),
        ("http://127.0.0.1:53817/ayarlar", True, "reddet"),
        ("http://127.0.0.1:9/baska-port", True, "reddet"),
        ("http://localhost:53817/", True, "reddet"),
        ("http://[::1]:8000/", True, "reddet"),
        ("http://127.0.0.2/", True, "reddet"),
        ("file:///etc/passwd", True, "reddet"),
        ("javascript:alert(1)", True, "reddet"),
        ("blob:http://127.0.0.1:53817/abc", True, "reddet"),
        ("data:text/html,merhaba", True, "reddet"),
        ("about:blank", True, "reddet"),
        ("", True, "reddet"),
        ("http://[bozuk/", True, "reddet"),
        ("https://okulapp.org:99999/", True, "reddet"),
        # Bağımsız denetim 14.11.2026: şemanın kendisi süzülür (adı olan http dışı adresler) ve
        # geri döngünün öteki yazılışları da yereldir.
        ("file://sunucu/paylasim/x", True, "reddet"),
        ("ftp://ornek.org/", True, "reddet"),
        ("ws://ornek.org/", True, "reddet"),
        ("http://localhost./", True, "reddet"),
        ("http://LOCALHOST:53817/", True, "reddet"),
        ("http://a.localhost:53817/", True, "reddet"),
        ("http://a.b.localhost./", True, "reddet"),
        ("http://0.0.0.0:53817/", True, "reddet"),
        ("http://[::]:53817/", True, "reddet"),
        ("http://[::ffff:127.0.0.1]:53817/", True, "reddet"),
        ("http://[::ffff:0.0.0.0]/", True, "reddet"),
        ("https://localhost.okulapp.org/", True, "tarayicida"),
        ("https://ornek-localhost/", True, "tarayicida"),
        ("http://[::ffff:8.8.8.8]/", True, "tarayicida"),
    ],
    ids=[
        "lisans",
        "http",
        "ayar_kapaliysa_ana_pencere",
        "kendi_koken",
        "geri_dongu_baska_port",
        "localhost",
        "ipv6_geri_dongu",
        "geri_dongu_agi",
        "file",
        "javascript",
        "blob",
        "data",
        "about_blank",
        "bos",
        "bicimsiz",
        "gecersiz_port",
        "file_sunuculu",
        "ftp",
        "ws",
        "localhost_noktali",
        "localhost_buyuk_harf",
        "localhost_alt_adi",
        "localhost_alt_adi_noktali",
        "belirsiz_ipv4",
        "belirsiz_ipv6",
        "ipv4_eslemli_geri_dongu",
        "ipv4_eslemli_belirsiz",
        "localhost_ile_baslayan_dis_ad",
        "localhost_ile_biten_tek_ad",
        "ipv4_eslemli_dis",
    ],
)
def test_yeni_pencere_karari(adres: str, tarayicida: bool, beklenen: str) -> None:
    assert dis_surec.yeni_pencere_karari(adres, _ANA_ADRES, tarayicida=tarayicida) == beklenen


@pytest.mark.parametrize(
    ("adres", "beklenen"),
    [
        ("http://ornek.test:8000/ayarlar", "reddet"),
        ("http://ORNEK.test:8000/", "reddet"),
        ("http://ornek.test:8001/", "tarayicida"),
        ("https://ornek.test:8000/", "tarayicida"),
        ("http://baska.test:8000/", "tarayicida"),
    ],
    ids=["ayni_koken", "ayni_koken_buyuk_harf", "baska_port", "baska_sema", "baska_ad"],
)
def test_kendi_koken_geri_dongu_olmasa_da_reddedilir(adres: str, beklenen: str) -> None:
    """Köken eşitliği tek başına sınanır: ana adres geri döngü değildir (bağımsız denetim 14.11.2026)."""
    ana = "http://ornek.test:8000/hakkinda"

    assert dis_surec.yeni_pencere_karari(adres, ana, tarayicida=True) == beklenen


class _SahteUrl:
    def __init__(self, adres: str) -> None:
        self._adres = adres

    def toString(self) -> str:  # noqa: N802 — Qt adı
        return self._adres


class _SahteProfil:
    pass


class _QtSayfasi:
    """`QWebEnginePage`'in kullandığımız yüzeyi: kurucu profili ve ebeveyni alır."""

    def __init__(self, profil: Any = None, ebeveyn: Any = None) -> None:
        self.kurulus = (profil, ebeveyn)
        self.silindi = 0

    def deleteLater(self) -> None:  # noqa: N802 — Qt adı
        self.silindi += 1


class _AnaSayfa(_QtSayfasi):
    def __init__(self) -> None:
        super().__init__()
        self._profil = _SahteProfil()
        self.yuklenen: list[Any] = []

    def profile(self) -> _SahteProfil:
        return self._profil

    def url(self) -> _SahteUrl:
        return _SahteUrl(_ANA_ADRES)

    def setUrl(self, url: Any) -> None:  # noqa: N802 — Qt adı
        self.yuklenen.append(url)


class _Kaydedici:
    def __init__(self) -> None:
        self.acilan: list[tuple[str, int, bool]] = []

    def open(self, url: str, new: int = 0, autoraise: bool = True) -> bool:
        self.acilan.append((url, new, autoraise))
        return True


def _yeni_pencere_arka_ucu(**ayarlar: Any) -> SimpleNamespace:
    return SimpleNamespace(
        QWebPage=_QtSayfasi,
        BrowserView=SimpleNamespace(WebPage=type("WebPage", (_QtSayfasi,), {})),
        webbrowser=_Kaydedici(),
        settings={"OPEN_EXTERNAL_LINKS_IN_BROWSER": True, **ayarlar},
    )


def _yeni_pencere(arka_uc: SimpleNamespace, ana: _AnaSayfa) -> Any:
    return dis_surec.yeni_pencere_isleyicisi(arka_uc)(ana, "WebBrowserTab")


def test_yeni_pencere_sayfasi_ana_sayfanin_profiliyle_kurulur() -> None:
    """K-yeni-1'in kök nedeni: pywebview'ın `NavigationHandler`'ı varsayılan profille kuruluyordu,
    Qt "Can not adopt content from a different WebEngineProfile." deyip içeriği aktarmıyordu."""
    ana = _AnaSayfa()

    sayfa = _yeni_pencere(_yeni_pencere_arka_ucu(), ana)

    assert isinstance(sayfa, _QtSayfasi)
    assert sayfa.kurulus == (ana.profile(), ana)


def test_dis_baglanti_kolun_aciciyla_tarayicida_acilir_pencere_acilmaz() -> None:
    arka_uc = _yeni_pencere_arka_ucu()
    ana = _AnaSayfa()
    sayfa = _yeni_pencere(arka_uc, ana)
    adres = "https://polyformproject.org/licenses/noncommercial/1.0.0/"

    assert sayfa.acceptNavigationRequest(_SahteUrl(adres), "LinkClicked", True) is False

    # pywebview'ın çağrısıyla aynı (`webbrowser.open(url, 2, True)`): `dis_tarayiciyi_bagla`'nın
    # koyduğu temiz ortamlı açıcı bu addadır.
    assert arka_uc.webbrowser.acilan == [(adres, 2, True)]
    assert ana.yuklenen == []
    assert sayfa.silindi == 1


def test_acici_cagri_aninda_okunur_temiz_ortamli_aciciya_gider() -> None:
    """İşleyici bağlandıktan sonra `dis_tarayiciyi_bagla` açıcıyı değiştirse de yenisi kullanılır."""
    arka_uc = _yeni_pencere_arka_ucu()
    isleyici = dis_surec.yeni_pencere_isleyicisi(arka_uc)
    yeni = _Kaydedici()
    arka_uc.webbrowser = yeni

    isleyici(_AnaSayfa(), "tab").acceptNavigationRequest(
        _SahteUrl("https://okulapp.org/"), "LinkClicked", True
    )

    assert yeni.acilan == [("https://okulapp.org/", 2, True)]


@pytest.mark.parametrize(
    "adres",
    ["http://127.0.0.1:53817/ayarlar", "file:///etc/passwd", "javascript:void(0)", ""],
    ids=["kendi_koken", "file", "javascript", "bos"],
)
def test_program_ici_ve_dis_olmayan_adres_reddedilir(adres: str, od_gunlugu: list[Any]) -> None:
    arka_uc = _yeni_pencere_arka_ucu()
    ana = _AnaSayfa()
    sayfa = _yeni_pencere(arka_uc, ana)

    assert sayfa.acceptNavigationRequest(_SahteUrl(adres), "LinkClicked", True) is False

    assert arka_uc.webbrowser.acilan == []
    assert ana.yuklenen == []
    metin = " ".join(k.getMessage() for k in od_gunlugu)
    assert "reddedildi" in metin
    assert "/etc/passwd" not in metin and "53817" not in metin


def test_ayar_kapaliysa_dis_adres_ana_pencerede_acilir() -> None:
    """pywebview'ın `OPEN_EXTERNAL_LINKS_IN_BROWSER = False` davranışı korunur."""
    arka_uc = _yeni_pencere_arka_ucu(OPEN_EXTERNAL_LINKS_IN_BROWSER=False)
    ana = _AnaSayfa()
    url = _SahteUrl("https://okulapp.org/")

    _yeni_pencere(arka_uc, ana).acceptNavigationRequest(url, "LinkClicked", True)

    assert ana.yuklenen == [url]
    assert arka_uc.webbrowser.acilan == []


def test_acici_hata_verirse_qt_yuvasindan_hata_tasmaz(od_gunlugu: list[Any]) -> None:
    class _Patlayan:
        def open(self, *_a: Any) -> bool:
            raise OSError("yok")

    arka_uc = _yeni_pencere_arka_ucu()
    arka_uc.webbrowser = _Patlayan()
    sayfa = _yeni_pencere(arka_uc, _AnaSayfa())

    assert sayfa.acceptNavigationRequest(_SahteUrl("https://okulapp.org/"), "x", True) is False
    assert sayfa.silindi == 1
    assert "OSError" in " ".join(k.getMessage() for k in od_gunlugu)


def test_her_istek_kendi_sayfasini_alir() -> None:
    """Kullanılmış sayfa yeniden verilmez: Qt her yeni pencerenin içeriğini taze sayfaya aktarır."""
    isleyici = dis_surec.yeni_pencere_isleyicisi(_yeni_pencere_arka_ucu())
    ana = _AnaSayfa()

    assert isleyici(ana, "tab") is not isleyici(ana, "tab")


def test_linuxta_yeni_pencere_istegi_sayfa_sinifina_baglanir() -> None:
    arka_uc = _yeni_pencere_arka_ucu()

    assert dis_surec.yeni_pencere_isleyicisini_bagla(arka_uc, platform="linux") is True

    sayfa = arka_uc.BrowserView.WebPage.createWindow(_AnaSayfa(), "tab")
    assert isinstance(sayfa, _QtSayfasi)


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_windowsta_yeni_pencere_istegine_dokunulmaz(platform: str) -> None:
    """Windows'ta EdgeChromium kolu `NewWindowRequested`'le açar; profil sorunu yoktur."""
    arka_uc = _yeni_pencere_arka_ucu()

    assert dis_surec.yeni_pencere_isleyicisini_bagla(arka_uc, platform=platform) is False
    assert "createWindow" not in vars(arka_uc.BrowserView.WebPage)
