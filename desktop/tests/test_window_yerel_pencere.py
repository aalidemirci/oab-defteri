"""Köprünün Linux'taki pencere yolu: önce masaüstünün penceresi, olmazsa Qt (saha bulgusu K-P3).

`desktop/window.py` başlığı "Linux'ta pencere masaüstünündür". Masaüstü penceresinin (zenity/kdialog)
kendisi `test_yerel_pencere.py`'de sınanır; burada köprünün ona verdiği seçenekler, Qt penceresine
düşüş, uzantı ve yeniden açma kuralının bu yolda da çalışması, ikinci çağrının iptali ve ön yüze
bildirilmesi, sayfanın dosya kutusunun aynı pencereyle açılması, arka uca bağlananlar, kapanışta açık
pencerenin sonlandırılması ve Windows yolunun değişmemesi sınanır (bağımsız denetim 13.11.2026).
"""

from __future__ import annotations

import base64
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import desktop.window as window_mod
from desktop.dis_surec import TemizOrtamTarayicisi
from desktop.window import (
    DOSYA_PENCERESI_ACIK_OLAYI,
    KAYDETME_SUZGECI,
    PENCERE_METINLERI,
    PencereKoprusu,
    open_window,
    yukleme_suzgecleri,
)
from desktop.yerel_pencere import YerelDosyaPenceresi

_ICERIK = b"%PDF-1.7 uydurma"


def _b64() -> str:
    return base64.b64encode(_ICERIK).decode("ascii")


class _Sabitler:
    OPEN_DIALOG = 10  # pywebview 5.3.2 `webview/__init__.py`
    SAVE_DIALOG = 30


class _QtPenceresi:
    """pywebview penceresi: `create_file_dialog` (Qt kolu) yalnız düşüşte çağrılmalı."""

    def __init__(self, *sonuclar: Any) -> None:
        self._sonuclar = list(sonuclar)
        self.anahtarlar: list[dict[str, Any]] = []
        self.turler: list[int] = []
        self.betikler: list[str] = []
        self.betik_geldi = threading.Event()

    def evaluate_js(self, betik: str) -> None:
        self.betikler.append(betik)
        self.betik_geldi.set()

    def create_file_dialog(self, tur: int, **anahtarlar: Any) -> Any:
        self.turler.append(tur)
        self.anahtarlar.append(anahtarlar)
        return self._sonuclar.pop(0) if self._sonuclar else None


class _SahteYerel:
    """`YerelDosyaPenceresi.ac`'ın yerine geçer; sıradaki dönüşü verir."""

    def __init__(self, *sonuclar: str | None, bekle: threading.Event | None = None) -> None:
        self._sonuclar = list(sonuclar)
        self._bekle = bekle
        self.acildi = threading.Event()
        self.cagrilar: list[dict[str, Any]] = []

    def ac(self, **secenekler: Any) -> str | None:
        self.cagrilar.append(secenekler)
        self.acildi.set()
        if self._bekle is not None:
            self._bekle.wait(5)
        return self._sonuclar.pop(0) if self._sonuclar else ""


def _kopru(
    yerel: _SahteYerel, qt: _QtPenceresi | None = None, platform: str = "linux"
) -> PencereKoprusu:
    kopru = PencereKoprusu(platform=platform, webview=_Sabitler, yerel_pencere=yerel)
    kopru.bind_window(qt if qt is not None else _QtPenceresi())
    return kopru


# ------------------------------------------------------------ seçenekler


def test_kaydetme_yeri_masaustu_penceresinde_sorulur() -> None:
    yerel = _SahteYerel("/media/uydurma/USB/yedek.odbak")
    qt = _QtPenceresi()

    yol = _kopru(yerel, qt).kaydetme_yeri_sor("oab-defteri-yedek-2026-11-13-101530.odbak")

    assert yol == "/media/uydurma/USB/yedek.odbak"
    assert yerel.cagrilar == [
        {
            "kaydet": True,
            "baslik": PENCERE_METINLERI["global.saveFile"],
            "klasor": str(Path.home()),
            "ad": "oab-defteri-yedek-2026-11-13-101530.odbak",
            "suzgecler": KAYDETME_SUZGECI,
        }
    ]
    assert qt.turler == []


def test_yedek_dosyasi_masaustunun_ac_penceresinde_secilir() -> None:
    yerel = _SahteYerel("/media/uydurma/USB/yedek.odbak")

    assert _kopru(yerel).yedek_dosyasi_sor() == "/media/uydurma/USB/yedek.odbak"

    (secenekler,) = yerel.cagrilar
    assert secenekler["kaydet"] is False
    assert secenekler["baslik"] == PENCERE_METINLERI["linux.openFile"] == "Dosya aç"
    assert secenekler["suzgecler"] == KAYDETME_SUZGECI


def test_dosya_kaydinda_tur_suzgeci_ve_onerilen_ad_verilir(tmp_path: Path) -> None:
    hedef = tmp_path / "Yedek-Raporu_13.11.2026.pdf"
    yerel = _SahteYerel(str(hedef))

    assert _kopru(yerel).dosya_kaydet(_b64(), "/baska/Yedek-Raporu_13.11.2026.pdf") == "kaydedildi"

    assert hedef.read_bytes() == _ICERIK
    (secenekler,) = yerel.cagrilar
    assert secenekler["ad"] == "Yedek-Raporu_13.11.2026.pdf"
    assert secenekler["suzgecler"] == ("PDF belgesi (*.pdf)",)


# -------------------------------------------------------------- dönüşler


def test_masaustu_penceresinde_iptal_qtye_dusmez(tmp_path: Path) -> None:
    yerel = _SahteYerel("")
    qt = _QtPenceresi(str(tmp_path / "a.pdf"))

    assert _kopru(yerel, qt).dosya_kaydet(_b64(), "a.pdf") == "iptal"

    assert qt.turler == []
    assert not list(tmp_path.iterdir())


def test_masaustu_penceresi_acilamazsa_qt_penceresi_ayni_seceneklerle_acilir(
    tmp_path: Path,
) -> None:
    yerel = _SahteYerel(None)
    qt = _QtPenceresi((str(tmp_path / "yedek.odbak"),))

    yol = _kopru(yerel, qt).kaydetme_yeri_sor("yedek.odbak")

    assert yol == str(tmp_path / "yedek.odbak")
    assert qt.turler == [_Sabitler.SAVE_DIALOG]
    assert qt.anahtarlar == [
        {
            "directory": str(Path.home()),
            "save_filename": "yedek.odbak",
            "file_types": KAYDETME_SUZGECI,
        }
    ]


def test_qtye_dusulen_ac_penceresi_tek_dosya_icindir() -> None:
    qt = _QtPenceresi(None)

    _kopru(_SahteYerel(None), qt).yedek_dosyasi_sor()

    assert qt.turler == [_Sabitler.OPEN_DIALOG]
    assert qt.anahtarlar[0]["allow_multiple"] is False


def test_masaustu_penceresinin_secimi_son_klasor_olur(tmp_path: Path) -> None:
    usb = tmp_path / "usb"
    usb.mkdir()
    yerel = _SahteYerel(str(usb / "yedek.odbak"), "")
    kopru = _kopru(yerel)

    kopru.kaydetme_yeri_sor("yedek.odbak")
    kopru.yedek_dosyasi_sor()

    assert [secenekler["klasor"] for secenekler in yerel.cagrilar] == [str(Path.home()), str(usb)]


def test_kurtarma_belgesi_masaustu_penceresinde_de_ev_klasorunde_acilir(tmp_path: Path) -> None:
    usb = tmp_path / "usb"
    usb.mkdir()
    yerel = _SahteYerel(str(usb / "yedek.odbak"), str(tmp_path / "anahtar.pdf"))
    kopru = _kopru(yerel)

    kopru.kaydetme_yeri_sor("yedek.odbak")
    kopru.dosya_kaydet(_b64(), "anahtar.pdf", True)

    assert yerel.cagrilar[1]["klasor"] == str(Path.home())


# ------------------------------------------------- uzantı ve yeniden açma kuralı


def test_zenity_yolunda_uzanti_eklenir(tmp_path: Path) -> None:
    """GTK'nın penceresi de uzantı eklemez: "rapor" yazılırsa "rapor.pdf" yazılır."""
    yerel = _SahteYerel(str(tmp_path / "rapor"))

    assert _kopru(yerel).dosya_kaydet(_b64(), "Yedek-Raporu.pdf") == "kaydedildi"

    assert [yol.name for yol in tmp_path.iterdir()] == ["rapor.pdf"]


def test_zenity_yolunda_uzanti_eklenen_ad_varsa_pencere_o_adla_yeniden_acilir(
    tmp_path: Path,
) -> None:
    """Pencere "rapor"u sordu, "rapor.pdf"yi değil: ikinci açılışta üzerine yazmayı zenity sorar."""
    var_olan = tmp_path / "rapor.pdf"
    var_olan.write_bytes(b"eski")
    yerel = _SahteYerel(str(tmp_path / "rapor"), str(var_olan))

    assert _kopru(yerel).dosya_kaydet(_b64(), "Yedek-Raporu.pdf") == "kaydedildi"

    assert [(s["klasor"], s["ad"]) for s in yerel.cagrilar] == [
        (str(Path.home()), "Yedek-Raporu.pdf"),
        (str(tmp_path), "rapor.pdf"),
    ]
    assert var_olan.read_bytes() == _ICERIK


def test_zenity_yolunda_yeniden_acilan_pencere_iptal_edilirse_dosya_kalir(tmp_path: Path) -> None:
    var_olan = tmp_path / "rapor.pdf"
    var_olan.write_bytes(b"eski")
    yerel = _SahteYerel(str(tmp_path / "rapor"), "")

    assert _kopru(yerel).dosya_kaydet(_b64(), "Yedek-Raporu.pdf") == "iptal"

    assert var_olan.read_bytes() == b"eski"


# ---------------------------------------------------- aynı anda tek pencere


@pytest.mark.parametrize(
    ("ikinci", "iptal"),
    [
        (lambda kopru: kopru.kaydetme_yeri_sor("yedek.odbak"), ""),
        (lambda kopru: kopru.yedek_dosyasi_sor(), ""),
        (lambda kopru: kopru.dosya_kaydet(_b64(), "belge.pdf"), "iptal"),
    ],
    ids=["kaydetme_yeri", "yedek_dosyasi", "dosya_kaydet"],
)
def test_pencere_acikken_ikinci_cagri_beklemeden_iptal_doner(
    tmp_path: Path, ikinci: Any, iptal: str
) -> None:
    """Dış süreç ana pencereye bağlı değildir: ikinci düğme ikinci pencere açmaz, beklemez."""
    birak = threading.Event()
    yerel = _SahteYerel(str(tmp_path / "ilk.pdf"), bekle=birak)
    kopru = _kopru(yerel)
    ilk: list[str] = []
    is_parcacigi = threading.Thread(
        target=lambda: ilk.append(kopru.dosya_kaydet(_b64(), "ilk.pdf"))
    )
    is_parcacigi.start()
    assert yerel.acildi.wait(5)

    try:
        assert ikinci(kopru) == iptal
        assert len(yerel.cagrilar) == 1
        assert kopru._yukleme_dosyasi_sec([".xlsx"]) == []
        assert len(yerel.cagrilar) == 1
    finally:
        birak.set()
        is_parcacigi.join(5)

    assert ilk == ["kaydedildi"]
    # Pencere kapandıktan sonra yeni çağrı yine açılır.
    yerel.acildi.clear()
    kopru.yedek_dosyasi_sor()
    assert len(yerel.cagrilar) == 2


def test_ikinci_cagrinin_iptali_on_yuze_bildirilir(tmp_path: Path) -> None:
    """Bağımsız denetim 13.11.2026: iptal sessizdi; dış pencere ana pencerenin arkasında kalabilir."""
    birak = threading.Event()
    yerel = _SahteYerel(str(tmp_path / "ilk.pdf"), bekle=birak)
    qt = _QtPenceresi()
    kopru = _kopru(yerel, qt)
    is_parcacigi = threading.Thread(target=lambda: kopru.dosya_kaydet(_b64(), "ilk.pdf"))
    is_parcacigi.start()
    assert yerel.acildi.wait(5)

    try:
        assert kopru.dosya_kaydet(_b64(), "ikinci.pdf") == "iptal"
        assert qt.betik_geldi.wait(5)
    finally:
        birak.set()
        is_parcacigi.join(5)

    assert qt.betikler == [f"window.dispatchEvent(new CustomEvent('{DOSYA_PENCERESI_ACIK_OLAYI}'))"]
    assert DOSYA_PENCERESI_ACIK_OLAYI == "od:dosya-penceresi-acik"


def test_ilk_pencere_bildirim_yollamaz(tmp_path: Path) -> None:
    qt = _QtPenceresi()

    _kopru(_SahteYerel(str(tmp_path / "a.pdf")), qt).dosya_kaydet(_b64(), "a.pdf")

    assert not qt.betik_geldi.wait(0.2)


def test_bildirim_gonderilemese_de_iptal_doner(tmp_path: Path) -> None:
    class _Patlayan(_QtPenceresi):
        def evaluate_js(self, betik: str) -> None:
            super().evaluate_js(betik)
            raise RuntimeError("sayfa yok")

    birak = threading.Event()
    yerel = _SahteYerel(str(tmp_path / "ilk.pdf"), bekle=birak)
    qt = _Patlayan()
    kopru = _kopru(yerel, qt)
    is_parcacigi = threading.Thread(target=lambda: kopru.dosya_kaydet(_b64(), "ilk.pdf"))
    is_parcacigi.start()
    assert yerel.acildi.wait(5)
    try:
        assert kopru.kaydetme_yeri_sor("a.odbak") == ""
        assert qt.betik_geldi.wait(5)
    finally:
        birak.set()
        is_parcacigi.join(5)


def test_pencere_hata_verirse_kilit_birakilir(tmp_path: Path) -> None:
    class _Patlayan(_SahteYerel):
        def ac(self, **secenekler: Any) -> str | None:
            super().ac(**secenekler)
            raise RuntimeError("beklenmedik")

    yerel = _Patlayan()
    kopru = _kopru(yerel)

    assert kopru.kaydetme_yeri_sor("a.odbak") == ""
    assert kopru.kaydetme_yeri_sor("a.odbak") == ""
    assert len(yerel.cagrilar) == 2


# --------------------------------------------------- sayfanın dosya kutusu


#: Kişiler'deki iki kutunun `accept` değeri (`frontend/src/modules/kisiler/AktarimPaneli.tsx`).
_KISILER_KABUL = [
    ".xls",
    ".xlsx",
    ".csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
]


def test_kutunun_uzantilari_uygun_dosyalar_suzgecidir() -> None:
    assert yukleme_suzgecleri(_KISILER_KABUL) == (
        "Uygun dosyalar (*.xls;*.xlsx;*.csv)",
        "Tüm dosyalar (*.*)",
    )


@pytest.mark.parametrize(
    ("kabul", "beklenen"),
    [
        ([], ("Tüm dosyalar (*.*)",)),
        (["text/csv"], ("Tüm dosyalar (*.*)",)),
        ([" .ODBAK ", ".odbak"], ("Uygun dosyalar (*.odbak)", "Tüm dosyalar (*.*)")),
        ([".tar.gz", ".x;y", "."], ("Tüm dosyalar (*.*)",)),
    ],
    ids=["bos", "yalniz_mime", "buyuk_harf_tekrar", "bicimsiz"],
)
def test_kutunun_suzgeci_bicimsiz_degerleri_atlar(kabul: list[str], beklenen: Any) -> None:
    assert yukleme_suzgecleri(kabul) == beklenen


def test_dosya_kutusu_masaustunun_ac_penceresinde_son_klasorde_acilir(tmp_path: Path) -> None:
    usb = tmp_path / "usb"
    usb.mkdir()
    yerel = _SahteYerel(str(usb / "yedek.odbak"), str(usb / "personel.XLS"))
    kopru = _kopru(yerel)
    kopru.kaydetme_yeri_sor("yedek.odbak")

    assert kopru._yukleme_dosyasi_sec(_KISILER_KABUL) == [str(usb / "personel.XLS")]

    assert yerel.cagrilar[1] == {
        "kaydet": False,
        "baslik": "Dosya aç",
        "klasor": str(usb),
        "ad": "",
        "suzgecler": ("Uygun dosyalar (*.xls;*.xlsx;*.csv)", "Tüm dosyalar (*.*)"),
    }


def test_dosya_kutusunun_secimi_son_klasor_olur(tmp_path: Path) -> None:
    usb = tmp_path / "usb"
    usb.mkdir()
    yerel = _SahteYerel(str(usb / "veli.xlsx"), "")
    kopru = _kopru(yerel)

    kopru._yukleme_dosyasi_sec([".xlsx"])
    kopru.yedek_dosyasi_sor()

    assert yerel.cagrilar[1]["klasor"] == str(usb)


def test_dosya_kutusunda_iptal_bos_listedir_son_klasor_degismez() -> None:
    yerel = _SahteYerel("", "")
    kopru = _kopru(yerel)

    assert kopru._yukleme_dosyasi_sec([".xlsx"]) == []
    kopru._yukleme_dosyasi_sec([".xlsx"])

    assert yerel.cagrilar[1]["klasor"] == str(Path.home())


def test_masaustu_penceresi_acilamazsa_dosya_kutusu_qtye_duser() -> None:
    assert _kopru(_SahteYerel(None))._yukleme_dosyasi_sec([".xlsx"]) is None


def test_dosya_kutusu_kilidi_birakir(tmp_path: Path) -> None:
    yerel = _SahteYerel(str(tmp_path / "a.xlsx"), str(tmp_path / "b.odbak"))
    kopru = _kopru(yerel)

    kopru._yukleme_dosyasi_sec([".xlsx"])

    assert kopru.yedek_dosyasi_sor() == str(tmp_path / "b.odbak")


def test_dosya_kutusu_acikken_kopru_penceresi_iptal_doner(tmp_path: Path) -> None:
    birak = threading.Event()
    yerel = _SahteYerel(str(tmp_path / "a.xlsx"), bekle=birak)
    kopru = _kopru(yerel)
    sonuc: list[Any] = []
    is_parcacigi = threading.Thread(target=lambda: sonuc.append(kopru._yukleme_dosyasi_sec([])))
    is_parcacigi.start()
    assert yerel.acildi.wait(5)
    try:
        assert kopru.yedek_dosyasi_sor() == ""
    finally:
        birak.set()
        is_parcacigi.join(5)

    assert sonuc == [[str(tmp_path / "a.xlsx")]]


def test_windowsta_dosya_kutusu_koprude_acilmaz() -> None:
    yerel = _SahteYerel("/olmamali")

    assert _kopru(yerel, platform="win32")._yukleme_dosyasi_sec([".xlsx"]) is None
    assert yerel.cagrilar == []


def test_dosya_kutusu_on_yuze_acilmaz() -> None:
    """pywebview `js_api`'nin `_` ile başlamayan özniteliklerini ön yüze açar."""
    acik = [ad for ad in dir(PencereKoprusu) if not ad.startswith("_")]

    assert not [ad for ad in acik if "yukleme" in ad or "bildir" in ad]


# ------------------------------------------------------------- Windows değişmez


def test_windowsta_masaustu_penceresi_kullanilmaz() -> None:
    """Windows'ta pencereyi WinForms açar; yerel pencere verilse de yok sayılır, kilit yoktur."""
    yerel = _SahteYerel("/olmamali")
    qt = _QtPenceresi("C:\\Yedekler\\yedek.odbak")

    yol = _kopru(yerel, qt, platform="win32").kaydetme_yeri_sor("yedek.odbak")

    assert yol == "C:\\Yedekler\\yedek.odbak"
    assert yerel.cagrilar == []


# ---------------------------------------------------------------- open_window


class _Olay:
    def __iadd__(self, _isleyici: Any) -> _Olay:
        return self


class _SahteSayfa:
    """pywebview `BrowserView.WebPage`: `chooseFiles` sınıfa konur."""


class _TabanSayfa:
    """`QWebEnginePage`: kip numaralandırması ve Qt'nin varsayılan `chooseFiles`'ı."""

    class FileSelectionMode:
        FileSelectOpen = "tek"
        FileSelectOpenMultiple = "coklu"

    @staticmethod
    def chooseFiles(sayfa: Any, kip: Any, eski: Any, kabul: Any) -> list[str]:  # noqa: N802
        return ["qt-varsayilani"]


class _EskiAcici:
    def open(self, url: str, new: int = 0, autoraise: bool = True) -> bool:
        return True


def _sahte_arka_uc() -> SimpleNamespace:
    """`webview.platforms.qt`'nin kullandığımız yüzeyi."""
    return SimpleNamespace(
        webbrowser=_EskiAcici(),
        QWebPage=_TabanSayfa,
        BrowserView=SimpleNamespace(WebPage=type("WebPage", (_SahteSayfa,), {})),
        QtCore=SimpleNamespace(),
    )


class _SahteWebview:
    OPEN_DIALOG = 10
    SAVE_DIALOG = 30

    def __init__(self) -> None:
        self.settings: dict[str, Any] = {}
        self.pencereler: list[dict[str, Any]] = []
        self.start_aninda: list[str] = []
        self.arka_uc = _sahte_arka_uc()
        self.ilk_initialize = self.initialize

    def initialize(self, gui: str | None = None) -> Any:
        return self.arka_uc

    def create_window(self, title: str, url: str, **kwargs: Any) -> Any:
        self.pencereler.append(kwargs)
        return SimpleNamespace(events=SimpleNamespace(shown=_Olay()))

    def start(self, **kwargs: Any) -> None:
        # pywebview 5.3.2 `start`: `guilib = initialize(gui)` (modülün adıyla), sonra pencereler.
        self.initialize(kwargs.get("gui"))
        kopru = self.pencereler[0]["js_api"]
        self.start_aninda.append(type(kopru._yerel_pencere).__name__)


def test_linuxta_kopru_masaustu_penceresiyle_kurulur_kapanista_kapatilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kapatilan: list[YerelDosyaPenceresi] = []
    monkeypatch.setattr(YerelDosyaPenceresi, "kapat", lambda self: kapatilan.append(self))
    sahte = _SahteWebview()

    open_window("http://127.0.0.1:1/", webview=sahte, platform="linux", storage_path=tmp_path)

    kopru = sahte.pencereler[0]["js_api"]
    assert sahte.start_aninda == ["YerelDosyaPenceresi"]
    assert kapatilan == [kopru._yerel_pencere]


def test_linuxta_arka_uc_yuklenince_baglanti_acicisi_ve_dosya_kutusu_baglanir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Eşzamanlı (bağımsız denetim 13.11.2026): `start` arka ucu yüklediğinde ikisi de yerindedir;
    ayrı iş parçacığı, `webbrowser` kaydı ve `xdg-settings` yoktur."""
    monkeypatch.setattr(YerelDosyaPenceresi, "kapat", lambda self: None)

    def is_parcacigi_yok(*_a: Any, **_k: Any) -> Any:
        pytest.fail("pencere açılırken iş parçacığı başlatıldı (eski kayıt yarışı)")

    monkeypatch.setattr(
        window_mod,
        "threading",
        SimpleNamespace(Lock=threading.Lock, Event=threading.Event, Thread=is_parcacigi_yok),
    )
    sahte = _SahteWebview()
    arka_uc = sahte.arka_uc
    eski_acici = arka_uc.webbrowser

    open_window("http://127.0.0.1:1/", webview=sahte, platform="linux", storage_path=tmp_path)

    assert isinstance(arka_uc.webbrowser, TemizOrtamTarayicisi)
    assert arka_uc.webbrowser._yedek == eski_acici.open
    assert callable(arka_uc.BrowserView.WebPage.chooseFiles)
    assert "chooseFiles" not in vars(_SahteSayfa)


def test_linuxta_dosya_kutusu_kopruye_baglanir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sayfanın tek dosyalık kutusu köprünün `_yukleme_dosyasi_sec`'ine, öteki kipler Qt'ye gider."""
    monkeypatch.setattr(YerelDosyaPenceresi, "kapat", lambda self: None)
    monkeypatch.setattr(
        window_mod,
        "yukleme_penceresini_bagla",
        lambda arka_uc, sec: setattr(arka_uc, "secici", sec),
    )
    sahte = _SahteWebview()

    open_window("http://127.0.0.1:1/", webview=sahte, platform="linux", storage_path=tmp_path)

    kopru = sahte.pencereler[0]["js_api"]
    assert sahte.arka_uc.secici == kopru._yukleme_dosyasi_sec


def test_baglama_hatasi_pencereyi_durdurmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, od_gunlugu: list[Any]
) -> None:
    monkeypatch.setattr(YerelDosyaPenceresi, "kapat", lambda self: None)
    sahte = _SahteWebview()
    sahte.arka_uc = SimpleNamespace()  # yüzeyi olmayan arka uç

    open_window("http://127.0.0.1:1/", webview=sahte, platform="linux", storage_path=tmp_path)

    assert sahte.start_aninda == ["YerelDosyaPenceresi"]
    assert "AttributeError" in " ".join(kayit.getMessage() for kayit in od_gunlugu)


def test_pencere_dongusu_hata_verse_de_masaustu_penceresi_kapatilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kapatilan: list[object] = []
    monkeypatch.setattr(YerelDosyaPenceresi, "kapat", lambda self: kapatilan.append(self))
    sahte = _SahteWebview()

    def patla(**_kwargs: Any) -> None:
        raise RuntimeError("döngü düştü")

    sahte.start = patla  # type: ignore[method-assign]

    with pytest.raises(RuntimeError):
        open_window("http://127.0.0.1:1/", webview=sahte, platform="linux", storage_path=tmp_path)

    assert len(kapatilan) == 1


def test_windowsta_kopru_masaustu_penceresi_ve_tarayici_kurmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bağımsız denetimin M26'sı (13.11.2026): Windows'ta masaüstü penceresi hiç kurulmaz, arka uca
    hiçbir şey bağlanmaz. Eşzamanlıdır: iş parçacığındaki hatanın testi düşürmemesi sorunu yoktur."""
    kurulan: list[object] = []

    class _Kaydeden(YerelDosyaPenceresi):
        def __init__(self, **anahtarlar: Any) -> None:
            kurulan.append(self)
            super().__init__(**anahtarlar)

    monkeypatch.setattr(window_mod, "YerelDosyaPenceresi", _Kaydeden)
    sahte = _SahteWebview()
    eski_acici = sahte.arka_uc.webbrowser

    open_window("http://127.0.0.1:1/", webview=sahte, platform="win32", storage_path=tmp_path)

    assert kurulan == []
    assert sahte.pencereler[0]["js_api"]._yerel_pencere is None
    assert sahte.initialize == sahte.ilk_initialize
    assert sahte.arka_uc.webbrowser is eski_acici
    assert "chooseFiles" not in vars(sahte.arka_uc.BrowserView.WebPage)
