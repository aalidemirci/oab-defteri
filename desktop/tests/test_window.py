"""Pencere katmanı testleri — WebView2 tespiti + MSHTML düşüşünün ENGELLİ olması."""

from __future__ import annotations

import base64
import errno
import inspect
import logging
import os
import re
import stat
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import desktop.window as window_mod
from desktop.errors import WebViewUnavailableError
from desktop.window import (
    FORM_ONERISI_DOSYALARI,
    GENEL_SUZGEC,
    KAYDETME_SUZGECI,
    SAYFA_ONBELLEGI_DIZINI,
    TEMIZLIK_BEKLEME_SN,
    TUR_SUZGECLERI,
    WINDOW_TITLE,
    PencereKoprusu,
    form_onerisini_kapat,
    gui_backend_for,
    open_window,
    pencere_onbellegini_temizle,
    require_window_runtime,
    set_windows_titlebar_theme,
    set_windows_window_icon,
    webview2_installed,
)


class _SahteOlay:
    """pywebview `Event`: `+=` ile işleyici eklenir, `set()` hepsini koşturur."""

    def __init__(self) -> None:
        self.isleyiciler: list[Callable[[], Any]] = []

    def __iadd__(self, isleyici: Callable[[], Any]) -> _SahteOlay:
        self.isleyiciler.append(isleyici)
        return self

    def set(self) -> None:
        for isleyici in list(self.isleyiciler):
            isleyici()


class _SahtePencere:
    """pywebview penceresi: yalnız `events.shown` ve WinForms formu (`native`)."""

    def __init__(self) -> None:
        self.events = SimpleNamespace(shown=_SahteOlay())
        self.native: Any = None


class _SahteWebview:
    """pywebview modülü yerine geçen kayıt tutucu."""

    def __init__(self) -> None:
        self.settings: dict[str, Any] = {"ALLOW_DOWNLOADS": False}
        self.pencereler: list[dict[str, Any]] = []
        self.start_kwargs: dict[str, Any] = {}
        self.pencere = _SahtePencere()
        #: `start` çağrıldığında profil dizininde bulunan dosyalar (temizlik sırası için).
        self.start_aninda_dosyalar: set[Path] = set()

    def initialize(self, gui: str | None = None) -> Any:
        """Arka uç: Linux'ta `open_window` ona bağlanır (`desktop/tests/test_window_yerel_pencere.py`)."""
        return None

    def create_window(self, title: str, url: str, **kwargs: Any) -> _SahtePencere:
        self.pencereler.append({"title": title, "url": url, **kwargs})
        return self.pencere

    def start(self, **kwargs: Any) -> None:
        self.start_kwargs = kwargs
        kok = Path(kwargs["storage_path"])
        self.start_aninda_dosyalar = {yol.relative_to(kok) for yol in kok.rglob("*")}


def _kayit(bulunan: dict[tuple[str, str], str]) -> Any:
    def oku(hive: str, subkey: str, value: str) -> str | None:
        return bulunan.get((hive, value))

    return oku


# ------------------------------------------------------------------- WebView2


def test_webview2_hklm_kaydindan_bulunur() -> None:
    assert webview2_installed(registry_reader=_kayit({("HKLM", "pv"): "120.0.2210.91"}))


def test_webview2_kayit_yoksa_bulunmaz() -> None:
    assert not webview2_installed(registry_reader=_kayit({}))


def test_webview2_bos_surum_kurulu_sayilmaz() -> None:
    """Kaldırılmış runtime kaydı `pv=0.0.0.0` bırakır — kurulu DEĞİLDİR."""
    assert not webview2_installed(
        registry_reader=_kayit({("HKLM", "pv"): "0.0.0.0"})  # noqa: S104 — sürüm damgası
    )


def test_windows_disinda_webview2_aranmaz() -> None:
    require_window_runtime(platform="linux", registry_reader=_kayit({}))


def test_windows_ta_webview2_yoksa_turkce_yonlendirme() -> None:
    with pytest.raises(WebViewUnavailableError) as hata:
        require_window_runtime(platform="win32", registry_reader=_kayit({}))

    assert "WebView2" in str(hata.value)
    assert "kur" in hata.value.hint.lower()


def test_windows_ta_webview2_varsa_gecer() -> None:
    require_window_runtime(
        platform="win32", registry_reader=_kayit({("HKCU", "pv"): "120.0.2210.91"})
    )


# ------------------------------------------------------------------- pencere


def test_gui_motoru_platforma_gore_secilir() -> None:
    assert gui_backend_for("win32") == "edgechromium"
    assert gui_backend_for("linux") == "qt"
    assert gui_backend_for("darwin") == "cocoa"


def test_mshtml_asla_secilmez() -> None:
    """React 18 MSHTML'de çalışmaz; pywebview'ın sessiz düşüşü KODLA engellenir."""
    assert "mshtml" not in {gui_backend_for(p) for p in ("win32", "linux", "darwin")}


def test_pencere_turkce_baslikla_acilir(tmp_path: Path) -> None:
    sahte = _SahteWebview()

    open_window(
        "http://127.0.0.1:5051/?t=gizli",
        webview=sahte,
        platform="linux",
        storage_path=tmp_path / "webview",
    )

    assert sahte.pencereler[0]["title"] == WINDOW_TITLE
    assert WINDOW_TITLE == "OAB Defteri"
    assert sahte.pencereler[0]["url"] == "http://127.0.0.1:5051/?t=gizli"


def test_pencere_gui_motorunu_acikca_verir(tmp_path: Path) -> None:
    sahte = _SahteWebview()

    open_window("http://127.0.0.1:1/", webview=sahte, platform="win32", storage_path=tmp_path)

    assert sahte.start_kwargs["gui"] == "edgechromium"


def test_pencere_dosya_indirmelerine_izin_verir(tmp_path: Path) -> None:
    """Blob bağlantıları Excel/PDF/TXT dosyalarını masaüstünde kaydedebilmeli."""
    sahte = _SahteWebview()

    open_window("http://127.0.0.1:1/", webview=sahte, platform="win32", storage_path=tmp_path)

    assert sahte.settings["ALLOW_DOWNLOADS"] is True


class _KaydetmePenceresi:
    """`create_file_dialog` yerine geçer; pywebview 5.3.2'nin iki platformdaki dönüşünü verir."""

    def __init__(self, sonuc: Any = None, hata: Exception | None = None) -> None:
        self.sonuc = sonuc
        self.hata = hata
        self.cagrilar: list[tuple[Any, ...]] = []
        self.anahtarlar: list[dict[str, Any]] = []

    def create_file_dialog(self, *args: Any, **kwargs: Any) -> Any:
        self.cagrilar.append(args)
        self.anahtarlar.append(kwargs)
        if self.hata is not None:
            raise self.hata
        return self.sonuc


class _KaydetmeSabiti:
    OPEN_DIALOG = 10  # pywebview 5.3.2 `webview/__init__.py`
    SAVE_DIALOG = 30


def _kopru(pencere: Any) -> PencereKoprusu:
    kopru = PencereKoprusu(platform="win32", webview=_KaydetmeSabiti)
    kopru.bind_window(pencere)
    return kopru


@pytest.mark.parametrize(
    ("donus", "beklenen"),
    [
        # WinForms `dialog.FileName`: düz metin. Dizi gibi okunsa yolun ilk harfi dönerdi.
        ("C:\\Yedekler\\yedek.odbak", "C:\\Yedekler\\yedek.odbak"),
        # Qt: tek öğeli demet.
        (("/media/usb/yedek.odbak",), "/media/usb/yedek.odbak"),
        (["/media/usb/yedek.odbak"], "/media/usb/yedek.odbak"),
        # İki platformda da iptal.
        (None, ""),
        ((), ""),
    ],
    ids=["winforms", "qt", "liste", "iptal", "bos_demet"],
)
def test_kaydetme_penceresinin_donusu_tek_bicime_iner(donus: Any, beklenen: str) -> None:
    assert _kopru(_KaydetmePenceresi(donus)).kaydetme_yeri_sor("yedek.odbak") == beklenen


def test_kaydetme_penceresi_onerilen_adla_kaydetme_kipinde_acilir() -> None:
    pencere = _KaydetmePenceresi(None)

    _kopru(pencere).kaydetme_yeri_sor("oab-defteri-yedek-2026-11-06-101530.odbak")

    assert pencere.cagrilar == [(30,)]
    (anahtarlar,) = pencere.anahtarlar
    assert anahtarlar["save_filename"] == "oab-defteri-yedek-2026-11-06-101530.odbak"
    assert anahtarlar["file_types"] == KAYDETME_SUZGECI
    assert anahtarlar["directory"] == str(Path.home())


def test_onerilen_addaki_yol_ayiklanir() -> None:
    pencere = _KaydetmePenceresi(None)

    _kopru(pencere).kaydetme_yeri_sor("/baska/yer/yedek.odbak")

    assert pencere.anahtarlar[0]["save_filename"] == "yedek.odbak"


def test_kaydetme_suzgeci_pywebviewin_bicimine_uyar() -> None:
    """Desen pywebview 5.3.2 `util.parse_file_type`'tan: uymayan süzgeç `ValueError` verirdi."""
    desen = r"^([\w ]+)\((\*(?:\.(?:\w+|\*))*(?:;\*\.\w+)*)\)$"
    suzgecler = [*KAYDETME_SUZGECI, *GENEL_SUZGEC]
    suzgecler += [suzgec for grup in TUR_SUZGECLERI.values() for suzgec in grup]
    assert all(re.search(desen, suzgec) for suzgec in suzgecler)


def test_pencere_yoksa_kaydetme_yeri_bos_doner(caplog: pytest.LogCaptureFixture) -> None:
    """`--autotest` ve pencere bağlanmadan gelen çağrı: boş dönüş, ön yüz istek göndermez.

    Bu bir hata değildir, günlüğe uyarı düşmez.
    """
    kopru = PencereKoprusu(platform="linux", webview=_KaydetmeSabiti)

    with caplog.at_level(logging.DEBUG):
        assert kopru.kaydetme_yeri_sor("yedek.odbak") == ""

    assert not caplog.records


def test_kaydetme_penceresi_acilamazsa_bos_doner_yol_gunluge_gitmez(
    caplog: pytest.LogCaptureFixture,
) -> None:
    pencere = _KaydetmePenceresi(hata=RuntimeError("/home/uydurma/yedek.odbak"))

    with caplog.at_level(logging.DEBUG):
        assert _kopru(pencere).kaydetme_yeri_sor("yedek.odbak") == ""

    assert "uydurma" not in caplog.text


@pytest.mark.parametrize(
    ("donus", "beklenen"),
    [
        # WinForms `tuple(dialog.FileNames)`: kaydetmenin tersine demet verir.
        (
            ("C:\\Okul Yedekleri\\şifreli yedek ığüşöç.odbak",),
            "C:\\Okul Yedekleri\\şifreli yedek ığüşöç.odbak",
        ),
        # Qt `(self._file_name[0],)`.
        (("/media/usb/Yedek Klasörü/yedek.odbak",), "/media/usb/Yedek Klasörü/yedek.odbak"),
        # İki platformda da iptal; Qt boş seçimi `None`'a kendi çevirir.
        (None, ""),
        ((), ""),
    ],
    ids=["winforms", "qt", "iptal", "bos_demet"],
)
def test_ac_penceresinin_donusu_tek_bicime_iner(donus: Any, beklenen: str) -> None:
    assert _kopru(_KaydetmePenceresi(donus)).yedek_dosyasi_sor() == beklenen


def test_ac_penceresi_ev_dizininde_tek_dosya_icin_acilir() -> None:
    pencere = _KaydetmePenceresi(None)

    _kopru(pencere).yedek_dosyasi_sor()

    assert pencere.cagrilar == [(10,)]
    assert pencere.anahtarlar == [
        {
            "directory": str(Path.home()),
            "allow_multiple": False,
            "file_types": KAYDETME_SUZGECI,
        }
    ]


def test_pencere_yoksa_yedek_dosyasi_bos_doner(od_gunlugu: list[logging.LogRecord]) -> None:
    kopru = PencereKoprusu(platform="linux", webview=_KaydetmeSabiti)

    assert kopru.yedek_dosyasi_sor() == ""

    assert not od_gunlugu


def test_ac_penceresi_acilamazsa_bos_doner_yol_gunluge_gitmez(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    pencere = _KaydetmePenceresi(hata=RuntimeError("/home/uydurma/yedek.odbak"))

    assert _kopru(pencere).yedek_dosyasi_sor() == ""

    (kayit,) = od_gunlugu
    assert "RuntimeError" in kayit.getMessage()
    assert "uydurma" not in kayit.getMessage()


def test_secilen_yedek_yolu_gunluge_yazilmaz(od_gunlugu: list[logging.LogRecord]) -> None:
    pencere = _KaydetmePenceresi(("/home/uydurma/yedek.odbak",))

    assert _kopru(pencere).yedek_dosyasi_sor() == "/home/uydurma/yedek.odbak"

    assert not od_gunlugu


# ---------------------------------------------- dosyayı program kaydeder (07.11.2026)

_ICERIK = b"%PDF-1.7 uydurma belge, KURTARMA-UYDURMA-ANAHTAR"
_YOL_BICIMLERI: list[Callable[[Path], Any]] = [str, lambda yol: (str(yol),)]


def _b64(veri: bytes = _ICERIK) -> str:
    return base64.b64encode(veri).decode("ascii")


class _SiraliPencere(_KaydetmePenceresi):
    """Her açılışta sıradaki dönüşü verir: uzantı eklenen ad varken pencere yeniden açılır."""

    def __init__(self, *sonuclar: Any) -> None:
        super().__init__()
        self._sonuclar = list(sonuclar)

    def create_file_dialog(self, *args: Any, **kwargs: Any) -> Any:
        self.sonuc = self._sonuclar.pop(0)
        return super().create_file_dialog(*args, **kwargs)


def _acilis_klasorleri(pencere: _KaydetmePenceresi) -> list[str]:
    return [anahtarlar["directory"] for anahtarlar in pencere.anahtarlar]


@pytest.mark.parametrize("bicim", _YOL_BICIMLERI, ids=["winforms", "qt"])
def test_dosya_secilen_yere_yazilir_gecici_dosya_kalmaz(
    tmp_path: Path, bicim: Callable[[Path], Any]
) -> None:
    hedef = tmp_path / "Yedek-Raporu_07.11.2026.pdf"

    sonuc = _kopru(_KaydetmePenceresi(bicim(hedef))).dosya_kaydet(_b64(), hedef.name)

    assert sonuc == "kaydedildi"
    assert hedef.read_bytes() == _ICERIK
    assert list(tmp_path.iterdir()) == [hedef]


def test_dosya_penceresi_kaydetme_kipinde_acilir_onerilen_ad_yol_tasimaz() -> None:
    pencere = _KaydetmePenceresi(None)

    _kopru(pencere).dosya_kaydet(_b64(), "/baska/yer/Yedek-Raporu.pdf")

    assert pencere.cagrilar == [(30,)]
    (anahtarlar,) = pencere.anahtarlar
    assert anahtarlar["save_filename"] == "Yedek-Raporu.pdf"
    assert anahtarlar["directory"] == str(Path.home())


@pytest.mark.parametrize("donus", [None, ()], ids=["iptal", "bos_demet"])
def test_iptalde_hicbir_sey_yazilmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, donus: Any
) -> None:
    monkeypatch.chdir(tmp_path)

    assert _kopru(_KaydetmePenceresi(donus)).dosya_kaydet(_b64(), "belge.pdf") == "iptal"

    assert not list(tmp_path.iterdir())


def test_var_olan_dosyanin_uzerine_yazilir(tmp_path: Path) -> None:
    """Üzerine yazmayı pencere sorar; seçim geldiyse kullanıcı onaylamıştır."""
    hedef = tmp_path / "belge.pdf"
    hedef.write_bytes(b"eski")

    assert _kopru(_KaydetmePenceresi(str(hedef))).dosya_kaydet(_b64(), "belge.pdf") == "kaydedildi"

    assert hedef.read_bytes() == _ICERIK


@pytest.mark.parametrize(
    ("ad", "beklenen"),
    [
        ("Kurtarma-Anahtarı-Belgesi_07.11.2026.pdf", "PDF belgesi (*.pdf)"),
        ("BELGE.PDF", "PDF belgesi (*.pdf)"),
        ("sablon-ogrenci.xlsx", "Excel dosyası (*.xlsx)"),
        # K-yeni-3 (Pardus 25, 13.11.2026): Word evrakı ve kurulum dosyası da süzgeçlidir; Windows'ta da.
        ("Yönetim-Kurulu-Görev-Bölümü-Karar-Taslağı_13.11.2026.docx", "Word belgesi (*.docx)"),
        ("oab-defteri-1.2.0-win64-setup.exe", "Kurulum dosyası (*.exe)"),
        ("fotograf.png", "Tüm dosyalar (*.*)"),
        ("uzantisiz", "Tüm dosyalar (*.*)"),
    ],
    ids=["pdf", "buyuk_harf", "xlsx", "docx", "kurulum", "bilinmeyen", "uzantisiz"],
)
def test_tur_suzgeci_uzantiya_gore_turkcedir(ad: str, beklenen: str) -> None:
    pencere = _KaydetmePenceresi(None)

    _kopru(pencere).dosya_kaydet(_b64(), ad)

    assert pencere.anahtarlar[0]["file_types"] == (beklenen,)


@pytest.mark.parametrize(
    ("secilen", "onerilen", "beklenen"),
    [
        # Qt kolu kaydetmede süzgeç uygulamaz, uzantı eklemez (modül başlığı).
        ("rapor", "Yedek-Raporu.pdf", "rapor.pdf"),
        ("rapor.", "Yedek-Raporu.pdf", "rapor.pdf"),
        ("rapor.yedek", "Yedek-Raporu.pdf", "rapor.yedek"),
        ("rapor", "belge", "rapor"),
        # Programın adları noktalı tarihle biter: `.2026` uzantı değildir.
        (
            "Yedek-Raporu_07.11.2026",
            "Yedek-Raporu_07.11.2026.pdf",
            "Yedek-Raporu_07.11.2026.pdf",
        ),
        ("Rapor 2026.11", "Yedek-Raporu_07.11.2026.pdf", "Rapor 2026.11.pdf"),
        (
            "Rapor 07.11.2026 son",
            "Yedek-Raporu_07.11.2026.pdf",
            "Rapor 07.11.2026 son.pdf",
        ),
        ("Rapor_07.11.2026.", "Yedek-Raporu_07.11.2026.pdf", "Rapor_07.11.2026.pdf"),
    ],
    ids=[
        "silinen_uzanti",
        "sondaki_nokta",
        "yazilan_uzanti",
        "onerilende_uzanti_yok",
        "tarihle_biten",
        "rakamla_biten",
        "tarihten_sonra_soz",
        "tarih_ve_sondaki_nokta",
    ],
)
def test_uzanti_yalniz_ad_uzantisizsa_eklenir(
    tmp_path: Path, secilen: str, onerilen: str, beklenen: str
) -> None:
    pencere = _KaydetmePenceresi((str(tmp_path / secilen),))

    assert _kopru(pencere).dosya_kaydet(_b64(), onerilen) == "kaydedildi"

    assert [yol.name for yol in tmp_path.iterdir()] == [beklenen]


def test_uzanti_eklenen_ad_varsa_pencere_o_adla_yeniden_acilir(tmp_path: Path) -> None:
    """Pencere "rapor"u sordu, "rapor.pdf"yi değil: dosya kullanıcı görmeden ezilmez."""
    var_olan = tmp_path / "rapor.pdf"
    var_olan.write_bytes(b"eski")
    pencere = _SiraliPencere((str(tmp_path / "rapor"),), (str(var_olan),))

    assert _kopru(pencere).dosya_kaydet(_b64(), "Yedek-Raporu.pdf") == "kaydedildi"

    assert [anahtarlar["save_filename"] for anahtarlar in pencere.anahtarlar] == [
        "Yedek-Raporu.pdf",
        "rapor.pdf",
    ]
    assert var_olan.read_bytes() == _ICERIK


def test_tarihle_biten_adda_da_var_olan_dosya_sorulmadan_ezilmez(
    tmp_path: Path,
) -> None:
    var_olan = tmp_path / "Rapor_07.11.2026.pdf"
    var_olan.write_bytes(b"eski")
    pencere = _SiraliPencere((str(tmp_path / "Rapor_07.11.2026"),), None)

    assert _kopru(pencere).dosya_kaydet(_b64(), "Yedek-Raporu_07.11.2026.pdf") == "iptal"

    assert pencere.anahtarlar[1]["save_filename"] == "Rapor_07.11.2026.pdf"
    assert var_olan.read_bytes() == b"eski"


def test_onerilen_ad_uzantisizsa_var_olan_dosya_secilince_pencere_yeniden_acilmaz(
    tmp_path: Path,
) -> None:
    """Eklenecek uzantı yoktur: kullanıcının seçtiği ad, pencerenin sorduğu addır."""
    hedef = tmp_path / "rapor"
    hedef.write_bytes(b"eski")
    pencere = _KaydetmePenceresi((str(hedef),))

    assert _kopru(pencere).dosya_kaydet(_b64(), "belge") == "kaydedildi"

    assert len(pencere.cagrilar) == 1
    assert hedef.read_bytes() == _ICERIK


@pytest.mark.skipif(os.name != "posix", reason="sembolik bağ sınaması POSIX'tedir")
def test_uzanti_eklenen_ad_kirik_kisayolsa_sorulmadan_ezilmez(tmp_path: Path) -> None:
    """Kırık kısayol da bir addır: hedefi yok diye boş sayılmaz."""
    kisayol = tmp_path / "rapor.pdf"
    kisayol.symlink_to(tmp_path / "olmayan-hedef")
    pencere = _SiraliPencere((str(tmp_path / "rapor"),), None)

    assert _kopru(pencere).dosya_kaydet(_b64(), "Yedek-Raporu.pdf") == "iptal"

    assert [yol.name for yol in tmp_path.iterdir()] == ["rapor.pdf"]
    assert kisayol.is_symlink()


@pytest.mark.parametrize("ev_klasorunde", [False, True], ids=["olagan", "kurtarma_belgesi"])
def test_yeniden_acilan_pencere_secilen_klasorde_acilir(
    tmp_path: Path, ev_klasorunde: bool
) -> None:
    """Qt `os.path.join(directory, save_filename)` ile açar: klasör verilmeseydi kurtarma belgesi
    ev dizininde aynı adla sorulur, seçilen klasördeki çakışma görülmeden ev dizinine yazılırdı
    (bağımsız denetim 07.11.2026)."""
    usb = tmp_path / "usb"
    usb.mkdir()
    var_olan = usb / "rapor.pdf"
    var_olan.write_bytes(b"eski")
    pencere = _SiraliPencere((str(usb / "rapor"),), (str(var_olan),), None)
    kopru = _kopru(pencere)

    assert kopru.dosya_kaydet(_b64(), "Yedek-Raporu.pdf", ev_klasorunde) == "kaydedildi"

    assert _acilis_klasorleri(pencere) == [str(Path.home()), str(usb)]
    assert pencere.anahtarlar[1]["save_filename"] == "rapor.pdf"
    assert var_olan.read_bytes() == _ICERIK
    # Son klasör olağan kipte seçilen klasör olur, kurtarma belgesinde hiç değişmez.
    kopru.yedek_dosyasi_sor()
    assert _acilis_klasorleri(pencere) == [
        str(Path.home()),
        str(usb),
        str(Path.home() if ev_klasorunde else usb),
    ]


def test_yeniden_acilan_pencere_iptal_edilirse_son_klasor_degismez(tmp_path: Path) -> None:
    """İş iptalle biterse son klasör de değişmez (modül başlığı: "İptal onu değiştirmez")."""
    usb = tmp_path / "usb"
    usb.mkdir()
    (usb / "rapor.pdf").write_bytes(b"eski")
    pencere = _SiraliPencere((str(usb / "rapor"),), None, None)
    kopru = _kopru(pencere)

    assert kopru.dosya_kaydet(_b64(), "Yedek-Raporu.pdf") == "iptal"
    kopru.yedek_dosyasi_sor()

    assert _acilis_klasorleri(pencere) == [str(Path.home()), str(usb), str(Path.home())]


def test_yeniden_acilan_pencere_iptal_edilirse_var_olan_dosya_kalir(
    tmp_path: Path,
) -> None:
    var_olan = tmp_path / "rapor.pdf"
    var_olan.write_bytes(b"eski")
    pencere = _SiraliPencere((str(tmp_path / "rapor"),), None)

    assert _kopru(pencere).dosya_kaydet(_b64(), "Yedek-Raporu.pdf") == "iptal"

    assert var_olan.read_bytes() == b"eski"
    assert list(tmp_path.iterdir()) == [var_olan]


@pytest.mark.parametrize("bozuk", ["şifre", "QUJD*", None], ids=["ascii_disi", "imi", "yok"])
def test_bozuk_icerikte_pencere_acilmaz(bozuk: Any, od_gunlugu: list[logging.LogRecord]) -> None:
    pencere = _KaydetmePenceresi(None)

    assert _kopru(pencere).dosya_kaydet(bozuk, "belge.pdf") == "hata"

    assert not pencere.cagrilar
    assert len(od_gunlugu) == 1


def test_pencere_yoksa_dosya_kaydi_hata_doner(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """`--autotest` ve pencere bağlanmadan gelen çağrı: dosya yazılmadı, ön yüz bunu bilsin."""
    kopru = PencereKoprusu(platform="linux", webview=_KaydetmeSabiti)

    assert kopru.dosya_kaydet(_b64(), "belge.pdf") == "hata"

    assert not od_gunlugu


def test_pencere_acilamazsa_hata_doner_yol_gunluge_gitmez(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    pencere = _KaydetmePenceresi(hata=RuntimeError("/home/uydurma/belge.pdf"))

    assert _kopru(pencere).dosya_kaydet(_b64(), "belge.pdf") == "hata"

    (kayit,) = od_gunlugu
    assert "RuntimeError" in kayit.getMessage()
    assert "uydurma" not in kayit.getMessage()


@pytest.mark.parametrize("islev", ["fsync", "replace"])
def test_yazilamazsa_gecici_dosya_kalmaz_yol_gunluge_gitmez(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    od_gunlugu: list[logging.LogRecord],
    islev: str,
) -> None:
    hedef = tmp_path / "belge.pdf"
    hedef.write_bytes(b"eski")

    def patlat(*_args: Any) -> None:
        raise OSError(28, "No space left on device", str(hedef))

    monkeypatch.setattr(f"desktop.window.os.{islev}", patlat)

    assert _kopru(_KaydetmePenceresi(str(hedef))).dosya_kaydet(_b64(), "belge.pdf") == "hata"

    assert hedef.read_bytes() == b"eski"
    assert list(tmp_path.iterdir()) == [hedef]
    (kayit,) = od_gunlugu
    assert "OSError" in kayit.getMessage()
    assert str(tmp_path) not in kayit.getMessage()


def test_gecici_dosya_hedefle_ayni_klasordedir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`os.replace` dosya sistemleri arasında çalışmaz: geçici dosya başka yerde olsa USB'ye her
    kayıt düşer, atomiklik de giderdi. Testte iki yer aynı diskte olduğu için kaynağa bakılır."""
    hedef = tmp_path / "usb" / "belge.pdf"
    hedef.parent.mkdir()
    kaynaklar: list[Path] = []
    gercek = os.replace

    def yakala(kaynak: str, varis: Path) -> None:
        kaynaklar.append(Path(kaynak))
        gercek(kaynak, varis)

    monkeypatch.setattr("desktop.window.os.replace", yakala)

    assert _kopru(_KaydetmePenceresi(str(hedef))).dosya_kaydet(_b64(), "belge.pdf") == "kaydedildi"

    assert [kaynak.parent for kaynak in kaynaklar] == [hedef.parent]


def test_fsync_aninda_icerik_dosyadadir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Python'un tamponundaki veri `fsync`e girmez: `flush` edilmeseydi eşitleme boşa giderdi."""
    boylar: list[int] = []
    gercek = os.fsync

    def yokla(tanitici: int) -> None:
        boylar.append(os.fstat(tanitici).st_size)
        gercek(tanitici)

    monkeypatch.setattr("desktop.window.os.fsync", yokla)
    pencere = _KaydetmePenceresi(str(tmp_path / "belge.pdf"))

    assert _kopru(pencere).dosya_kaydet(_b64(), "belge.pdf") == "kaydedildi"

    assert boylar == [len(_ICERIK)]


@pytest.mark.skipif(os.name != "posix", reason="dosya kipi POSIX'tedir")
def test_kaydedilen_dosya_yalniz_kullaniciya_aciktir(tmp_path: Path) -> None:
    """Kurtarma belgesi anahtar taşır (`_atomik_yaz`)."""
    hedef = tmp_path / "belge.pdf"

    assert _kopru(_KaydetmePenceresi(str(hedef))).dosya_kaydet(_b64(), "belge.pdf") == "kaydedildi"

    assert stat.S_IMODE(hedef.stat().st_mode) == 0o600


def test_secilen_yer_kalkmissa_hata_doner(tmp_path: Path) -> None:
    """Bellek çekildi: klasör yok, yazım başlamaz."""
    hedef = tmp_path / "cekilen-bellek" / "belge.pdf"

    assert _kopru(_KaydetmePenceresi(str(hedef))).dosya_kaydet(_b64(), "belge.pdf") == "hata"


def test_kayit_yolu_ve_icerigi_gunluge_ya_da_yanita_tasimaz(
    tmp_path: Path, od_gunlugu: list[logging.LogRecord]
) -> None:
    """Dönüş yalnız durumdur; kurtarma belgesi anahtar taşır, Windows yolu hesap adını taşır."""
    pencere = _KaydetmePenceresi(str(tmp_path / "belge.pdf"))

    assert _kopru(pencere).dosya_kaydet(_b64(), "belge.pdf") == "kaydedildi"

    assert not od_gunlugu


def test_son_secilen_klasor_uc_pencerede_de_kullanilir(tmp_path: Path) -> None:
    klasor = tmp_path / "usb"
    klasor.mkdir()
    pencere = _KaydetmePenceresi(str(klasor / "belge.pdf"))
    kopru = _kopru(pencere)

    kopru.dosya_kaydet(_b64(), "belge.pdf")
    kopru.kaydetme_yeri_sor("yedek.odbak")
    kopru.yedek_dosyasi_sor()
    kopru.dosya_kaydet(_b64(), "belge.pdf")

    assert _acilis_klasorleri(pencere) == [str(Path.home()), *[str(klasor)] * 3]


@pytest.mark.parametrize(
    "sor",
    [
        lambda kopru: kopru.kaydetme_yeri_sor("yedek.odbak"),
        lambda kopru: kopru.yedek_dosyasi_sor(),
    ],
    ids=["kaydetme_yeri", "yedek_dosyasi"],
)
def test_yol_soran_pencereler_de_son_klasoru_yazar(
    tmp_path: Path, sor: Callable[[PencereKoprusu], str]
) -> None:
    pencere = _SiraliPencere((str(tmp_path / "yedek.odbak"),), None)
    kopru = _kopru(pencere)

    sor(kopru)
    kopru.dosya_kaydet(_b64(), "belge.pdf")

    assert _acilis_klasorleri(pencere) == [str(Path.home()), str(tmp_path)]


def test_iptal_son_klasoru_degistirmez(tmp_path: Path) -> None:
    pencere = _SiraliPencere(str(tmp_path / "belge.pdf"), None, None)
    kopru = _kopru(pencere)

    kopru.dosya_kaydet(_b64(), "belge.pdf")
    kopru.dosya_kaydet(_b64(), "belge.pdf")
    kopru.yedek_dosyasi_sor()

    assert _acilis_klasorleri(pencere) == [
        str(Path.home()),
        str(tmp_path),
        str(tmp_path),
    ]


def test_son_klasor_artik_yoksa_ev_dizinine_duser(tmp_path: Path) -> None:
    klasor = tmp_path / "usb"
    klasor.mkdir()
    pencere = _SiraliPencere(str(klasor / "belge.pdf"), None)
    kopru = _kopru(pencere)
    kopru.dosya_kaydet(_b64(), "belge.pdf")
    (klasor / "belge.pdf").unlink()
    klasor.rmdir()

    kopru.kaydetme_yeri_sor("yedek.odbak")

    assert _acilis_klasorleri(pencere)[-1] == str(Path.home())


def test_son_klasor_yalniz_bellektedir(tmp_path: Path) -> None:
    """Köprü yeni kurulunca (program yeniden açılınca) klasör bilinmez, diske iz düşmez."""
    hedef = tmp_path / "belge.pdf"
    _kopru(_KaydetmePenceresi(str(hedef))).dosya_kaydet(_b64(), "belge.pdf")
    pencere = _KaydetmePenceresi(None)

    _kopru(pencere).kaydetme_yeri_sor("yedek.odbak")

    assert _acilis_klasorleri(pencere) == [str(Path.home())]
    assert list(tmp_path.iterdir()) == [hedef]


def test_kurtarma_belgesi_ev_dizininde_acilir_son_klasore_dokunmaz(
    tmp_path: Path,
) -> None:
    """Kullanıcı kararı 07.11.2026 "Hep ev klasöründe": anahtar şifreli yedeğin yanına önerilmez,
    yedek de anahtarın yanına önerilmez."""
    usb = tmp_path / "usb"
    belgeler = tmp_path / "belgeler"
    usb.mkdir()
    belgeler.mkdir()
    pencere = _SiraliPencere((str(usb / "yedek.odbak"),), str(belgeler / "anahtar.pdf"), None, None)
    kopru = _kopru(pencere)

    kopru.kaydetme_yeri_sor("yedek.odbak")
    assert kopru.dosya_kaydet(_b64(), "anahtar.pdf", True) == "kaydedildi"
    kopru.kaydetme_yeri_sor("yedek.odbak")
    kopru.dosya_kaydet(_b64(), "belge.pdf")

    assert _acilis_klasorleri(pencere) == [
        str(Path.home()),
        str(Path.home()),
        str(usb),
        str(usb),
    ]
    assert (belgeler / "anahtar.pdf").read_bytes() == base64.b64decode(_b64())


@pytest.mark.parametrize("deger", [1, "true", None], ids=["sayi", "metin", "bos"])
def test_ev_klasoru_isareti_yalniz_true_ile_acilir(tmp_path: Path, deger: object) -> None:
    """Köprüye sayfadan gelen değer `True` değilse olağan kural (son klasör) geçerlidir."""
    pencere = _SiraliPencere(str(tmp_path / "belge.pdf"), None)
    kopru = _kopru(pencere)

    kopru.dosya_kaydet(_b64(), "belge.pdf")
    kopru.dosya_kaydet(_b64(), "belge.pdf", deger)  # type: ignore[arg-type]

    assert _acilis_klasorleri(pencere) == [str(Path.home()), str(tmp_path)]


def test_pencere_kaydetme_yeri_koprusunu_frontende_sunar(tmp_path: Path) -> None:
    sahte = _SahteWebview()

    open_window("http://127.0.0.1:1/", webview=sahte, platform="linux", storage_path=tmp_path)

    kopru = sahte.pencereler[0]["js_api"]
    assert callable(kopru.kaydetme_yeri_sor)
    assert callable(kopru.yedek_dosyasi_sor)
    assert callable(kopru.dosya_kaydet)
    # pywebview `js_api`'nin açık özniteliklerini dolaşır: pencere modülü ön yüze açılmamalı.
    assert "_webview" in vars(kopru)
    assert not [ad for ad in vars(kopru) if not ad.startswith("_")]


def test_pencere_baslik_cubugu_tema_koprusunu_frontende_sunar(tmp_path: Path) -> None:
    sahte = _SahteWebview()

    open_window("http://127.0.0.1:1/", webview=sahte, platform="win32", storage_path=tmp_path)

    api = sahte.pencereler[0]["js_api"]
    assert callable(api.set_titlebar_theme)
    assert api.set_titlebar_theme(True) is False


def test_windows_baslik_cubugu_koyu_tema_ozelligini_uygular() -> None:
    class _Handle:
        def ToInt64(self) -> int:
            return 2468

    class _Native:
        Handle = _Handle()

    class _Window:
        native = _Native()

    calls: list[tuple[int, int, bool]] = []

    def setter(hwnd: int, attribute: int, dark: bool) -> int:
        calls.append((hwnd, attribute, dark))
        return 0

    assert set_windows_titlebar_theme(_Window(), True, platform="win32", setter=setter)
    assert calls == [(2468, 20, True)]


def test_windows_baslik_cubugu_eski_dwm_ozelligine_geri_doner() -> None:
    class _Window:
        native = type("Native", (), {"Handle": 1357})()

    calls: list[int] = []

    def setter(_hwnd: int, attribute: int, _dark: bool) -> int:
        calls.append(attribute)
        return 1 if attribute == 20 else 0

    assert set_windows_titlebar_theme(_Window(), False, platform="win32", setter=setter)
    assert calls == [20, 19]


def test_windows_pencere_ikonu_yerel_forma_uygulanir(tmp_path: Path) -> None:
    icon_path = tmp_path / "uygulama.ico"
    icon_path.write_bytes(b"ico")

    class _Native:
        Icon: Any | None = None

    class _Window:
        native = _Native()

    loaded: list[Path] = []
    marker = object()

    def loader(path: Path) -> object:
        loaded.append(path)
        return marker

    assert set_windows_window_icon(
        _Window(),
        platform="win32",
        icon_path=icon_path,
        loader=loader,
    )
    assert loaded == [icon_path]
    assert _Window.native.Icon is marker


def test_pencere_profil_dizini_veri_alaninda(tmp_path: Path) -> None:
    """Pencere motorunun profili kurulum dizinine değil, önbelleğe yazılır."""
    sahte = _SahteWebview()
    hedef = tmp_path / "cache" / "webview"

    open_window("http://127.0.0.1:1/", webview=sahte, platform="linux", storage_path=hedef)

    assert sahte.start_kwargs["storage_path"] == str(hedef)
    assert hedef.is_dir()


def test_pywebview_kurulu_degilse_turkce_hata(tmp_path: Path) -> None:
    def bulunamadi() -> Any:
        raise ImportError("No module named 'webview'")

    with pytest.raises(WebViewUnavailableError) as hata:
        open_window(
            "http://127.0.0.1:1/",
            webview=None,
            platform="linux",
            storage_path=tmp_path,
            importer=bulunamadi,
        )

    assert "pencere" in str(hata.value).lower()


# ------------------------- pencere bileşeninin izleri (KVKK; tasarım §4.3 tehdit 24; kusur 23, 24)


class _UI:
    """Pencere iş parçacığı: bileşenin nesneleri yalnız `Invoke`un ve bileşen olayının içinde
    kullanılabilir (WebView2 dışarıdan erişimde hata verir). Sahteler bunu zorlar."""

    icinde = False


@contextmanager
def _ui_icinde() -> Iterator[None]:
    onceki, _UI.icinde = _UI.icinde, True
    try:
        yield
    finally:
        _UI.icinde = onceki


def _ui_gerekir() -> None:
    if not _UI.icinde:
        raise RuntimeError("CoreWebView2 yalnız pencere iş parçacığında kullanılabilir")


class _Ayarlar:
    """`CoreWebView2Settings`. WebView2'de `IsGeneralAutofillEnabled` açık gelir (sınamada form önerisi
    saklandı), `IsPasswordAutosaveEnabled` kapalı gelir; sahte ikisini de açık kurar ki kapatma görülsün."""

    IsGeneralAutofillEnabled: bool
    IsPasswordAutosaveEnabled: bool

    def __init__(self) -> None:
        object.__setattr__(self, "IsGeneralAutofillEnabled", True)
        object.__setattr__(self, "IsPasswordAutosaveEnabled", True)

    def __setattr__(self, ad: str, deger: Any) -> None:
        _ui_gerekir()
        object.__setattr__(self, ad, deger)


class _Core:
    def __init__(self) -> None:
        self.ayarlar = _Ayarlar()

    @property
    def Settings(self) -> _Ayarlar:  # noqa: N802 — .NET adı
        _ui_gerekir()
        return self.ayarlar


class _NetOlayi:
    """.NET olayı: pythonnet'te `+=` ile işleyici eklenir, işleyici `(gönderen, olay)` alır."""

    def __init__(self) -> None:
        self.isleyiciler: list[Callable[[Any, Any], None]] = []

    def __iadd__(self, isleyici: Callable[[Any, Any], None]) -> _NetOlayi:
        _ui_gerekir()
        self.isleyiciler.append(isleyici)
        return self

    def tetikle(self, gonderen: Any, olay: Any) -> None:
        """Bileşenin olayı pencere iş parçacığında gelir."""
        with _ui_icinde():
            for isleyici in self.isleyiciler:
                isleyici(gonderen, olay)


class _Denetim:
    """WinForms `WebView2` denetimi: bileşen hazır olunca `CoreWebView2` dolar."""

    def __init__(self, core: _Core | None = None) -> None:
        self.core = core
        self.olay = _NetOlayi()

    @property
    def CoreWebView2(self) -> _Core | None:  # noqa: N802 — .NET adı
        _ui_gerekir()
        return self.core

    @property
    def CoreWebView2InitializationCompleted(self) -> _NetOlayi:  # noqa: N802 — .NET adı
        _ui_gerekir()
        return self.olay

    @CoreWebView2InitializationCompleted.setter
    def CoreWebView2InitializationCompleted(self, deger: _NetOlayi) -> None:  # noqa: N802
        _ui_gerekir()
        self.olay = deger

    def hazir_ol(self, core: _Core, *, basarili: bool = True) -> None:
        """Bileşen başlar: `CoreWebView2` dolar, olay pencere iş parçacığında gelir."""
        self.core = core if basarili else None
        self.olay.tetikle(self, SimpleNamespace(IsSuccess=basarili))


def _form_penceresi(denetim: _Denetim) -> _SahtePencere:
    pencere = _SahtePencere()
    pencere.native = SimpleNamespace(webview=denetim)
    return pencere


def _kapali(core: _Core) -> bool:
    return not core.ayarlar.IsGeneralAutofillEnabled and not core.ayarlar.IsPasswordAutosaveEnabled


class _IsParcacigi:
    """`Invoke` yerine: işlevi pencere iş parçacığındaymış gibi koşturur, formu kaydeder."""

    def __init__(self) -> None:
        self.formlar: list[Any] = []

    def __call__(self, form: Any, islev: Callable[[], None]) -> None:
        self.formlar.append(form)
        with _ui_icinde():
            islev()


def _kayitlar(gunluk: list[logging.LogRecord]) -> list[tuple[int, str, Any]]:
    """Düzey, ileti ve yığın: uyarı DEBUG'a inse ya da yığın taşısa (yol sızar) test düşer."""
    return [(kayit.levelno, kayit.getMessage(), kayit.exc_info) for kayit in gunluk]


_KAPATILAMADI = (
    logging.WARNING,
    "Pencere bileşeninin form önerisi kapatılamadı (RuntimeError).",
    None,
)
_HESAP_YOLU = r"C:\Users\Uydurma Kisi\AppData"


def test_bilesen_hazirsa_form_onerisi_pencere_is_parcaciginda_kapanir(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    core = _Core()
    pencere = _form_penceresi(_Denetim(core))
    is_parcacigi = _IsParcacigi()

    form_onerisini_kapat(pencere, is_parcaciginda=is_parcacigi)

    assert _kapali(core)
    assert is_parcacigi.formlar == [pencere.native]
    assert not od_gunlugu


def test_bilesen_hazir_degilse_hazir_olunca_kapanir(od_gunlugu: list[logging.LogRecord]) -> None:
    denetim = _Denetim()
    form_onerisini_kapat(_form_penceresi(denetim), is_parcaciginda=_IsParcacigi())
    assert len(denetim.olay.isleyiciler) == 1

    core = _Core()
    denetim.hazir_ol(core)

    assert _kapali(core)
    assert not od_gunlugu


def test_pencere_is_parcacigi_disinda_bilesene_dokunulamaz(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """Sahtelerin sınaması: işi `Invoke`un dışında yapan kod kapatamaz, uyarı düşer.

    Denetim ya da bağlanma `Invoke`un dışına taşınsaydı yukarıdaki iki test bu yüzden düşerdi.
    """

    def disarida(_form: Any, islev: Callable[[], None]) -> None:
        islev()

    core = _Core()
    form_onerisini_kapat(_form_penceresi(_Denetim(core)), is_parcaciginda=disarida)

    assert not _kapali(core)
    assert _kayitlar(od_gunlugu) == [_KAPATILAMADI]


def test_bilesen_baslayamadiysa_ayar_denenmez(od_gunlugu: list[logging.LogRecord]) -> None:
    denetim = _Denetim()
    form_onerisini_kapat(_form_penceresi(denetim), is_parcaciginda=_IsParcacigi())

    # Başlayamayan bileşende `CoreWebView2` boştur; ona dokunulsaydı uyarı düşerdi.
    denetim.hazir_ol(_Core(), basarili=False)

    assert not od_gunlugu


def test_hazir_olayindaki_hata_disari_tasmaz(od_gunlugu: list[logging.LogRecord]) -> None:
    """Olay pencere iş parçacığında koşar; Python hatası .NET'e taşsa pencere düşebilirdi."""

    class _BozukCore(_Core):
        @property
        def Settings(self) -> _Ayarlar:  # noqa: N802 — .NET adı
            raise RuntimeError(_HESAP_YOLU)

    denetim = _Denetim()
    form_onerisini_kapat(_form_penceresi(denetim), is_parcaciginda=_IsParcacigi())

    denetim.hazir_ol(_BozukCore())

    assert _kayitlar(od_gunlugu) == [_KAPATILAMADI]


def test_form_onerisi_kapatilamazsa_pencere_durmaz_gunluge_yalniz_tur(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    def patlat(_form: Any, _islev: Callable[[], None]) -> None:
        raise RuntimeError(_HESAP_YOLU)

    form_onerisini_kapat(_form_penceresi(_Denetim(_Core())), is_parcaciginda=patlat)

    assert _kayitlar(od_gunlugu) == [_KAPATILAMADI]


def test_bilesen_bulunamazsa_uyari_duser(od_gunlugu: list[logging.LogRecord]) -> None:
    form_onerisini_kapat(_SahtePencere(), is_parcaciginda=_IsParcacigi())

    assert _kayitlar(od_gunlugu) == [
        (
            logging.WARNING,
            "Pencere bileşeninin form önerisi kapatılamadı (bileşen bulunamadı).",
            None,
        )
    ]


def test_windows_ta_form_onerisi_pencere_gosterilince_kapanir_isleyici_starttan_once_baglanir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`webview.start` pencere kapanana dek bloklar: işleyici ondan önce bağlanmalıdır."""
    monkeypatch.setattr(window_mod, "_pencere_is_parcaciginda", _IsParcacigi())
    sahte = _SahteWebview()
    core = _Core()
    sahte.pencere.native = SimpleNamespace(webview=_Denetim(core))
    asil_start = sahte.start
    gosterilmeden: list[bool] = []

    def start(**kwargs: Any) -> None:
        asil_start(**kwargs)
        gosterilmeden.append(_kapali(core))
        sahte.pencere.events.shown.set()  # pencere start sırasında gösterilir

    sahte.start = start  # type: ignore[method-assign]

    open_window("http://127.0.0.1:1/", webview=sahte, platform="win32", storage_path=tmp_path)

    assert gosterilmeden == [False]
    assert _kapali(core)


def test_windows_disinda_form_onerisi_isleyicisi_baglanmaz(tmp_path: Path) -> None:
    sahte = _SahteWebview()

    open_window("http://127.0.0.1:1/", webview=sahte, platform="linux", storage_path=tmp_path)

    assert sahte.pencere.events.shown.isleyiciler == []


#: Sınamada (07.11.2026) değerler bu veritabanında ve sayfa önbelleğinde bulundu. Elle yazılır: sabitten
#: bir ad düşerse o dosya silinmeden kalırdı, test sabitten türeseydi bunu görmezdi.
_PROFIL = Path("EBWebView", "Default")
_BEKLENEN_DOSYALAR = tuple(
    _PROFIL / ad for ad in ("Web Data-journal", "Web Data-wal", "Web Data-shm", "Web Data")
)
_SAYFA_ONBELLEGI_ICERIGI = (
    _PROFIL / "Cache" / "Cache_Data" / "data_1",
    _PROFIL / "Cache" / "Cache_Data" / "f_000001",
)


def test_silinen_ogeler_webview2_profilinin_oneri_veritabani_ve_sayfa_onbellegidir() -> None:
    assert FORM_ONERISI_DOSYALARI == _BEKLENEN_DOSYALAR
    assert SAYFA_ONBELLEGI_DIZINI == _PROFIL / "Cache"


def _yaz(profil: Path, *goreliler: Path, icerik: str = "Uydurma Okul Adi") -> None:
    for goreli in goreliler:
        (profil / goreli).parent.mkdir(parents=True, exist_ok=True)
        (profil / goreli).write_text(icerik, encoding="utf-8")


@pytest.mark.parametrize("platform", ["win32", "linux"])
def test_acilista_eski_oneriler_ve_sayfa_onbellegi_bilesen_baslamadan_silinir(
    tmp_path: Path, platform: str
) -> None:
    profil = tmp_path / "webview"
    _yaz(profil, *_BEKLENEN_DOSYALAR, *_SAYFA_ONBELLEGI_ICERIGI)
    kalacak = (
        _PROFIL / "Local Storage" / "leveldb" / "000003.log",
        _PROFIL / "Code Cache" / "js" / "index",
        _PROFIL / "Cookies",
        Path("EBWebView", "Local State"),
    )
    _yaz(profil, *kalacak, icerik="tercih")
    sahte = _SahteWebview()

    open_window("http://127.0.0.1:1/", webview=sahte, platform=platform, storage_path=profil)

    silinmesi_gereken = {*_BEKLENEN_DOSYALAR, *_SAYFA_ONBELLEGI_ICERIGI, _PROFIL / "Cache"}
    assert not silinmesi_gereken & sahte.start_aninda_dosyalar
    assert set(kalacak) <= sahte.start_aninda_dosyalar


def test_gunluk_dosyalari_ana_veritabanindan_once_silinir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ana dosya gidip günlük kalsaydı yeni veritabanına eski sayfalar uygulanabilirdi."""
    sira: list[str] = []
    asil_sil = window_mod._sil

    def kaydet(hedef: Path, *, dizin: bool) -> None:
        sira.append(hedef.name)
        asil_sil(hedef, dizin=dizin)

    monkeypatch.setattr(window_mod, "_sil", kaydet)

    pencere_onbellegini_temizle(tmp_path)

    assert sira == ["Web Data-journal", "Web Data-wal", "Web Data-shm", "Web Data", "Cache"]


class _SahteSaat:
    """`bekle` saati ilerletir; gerçek süre geçmez."""

    def __init__(self) -> None:
        self.simdi = 100.0
        self.beklemeler: list[float] = []

    def saat(self) -> float:
        return self.simdi

    def bekle(self, sure: float) -> None:
        self.beklemeler.append(sure)
        self.simdi += sure


def _kilitli(monkeypatch: pytest.MonkeyPatch, adlar: dict[str, int | None]) -> None:
    """`adlar`daki öğe verilen sayıda (`None`: hep) `PermissionError` verir, sonra gerçekten silinir."""
    asil_sil = window_mod._sil

    def sil(hedef: Path, *, dizin: bool) -> None:
        if hedef.name in adlar:
            kalan = adlar[hedef.name]
            if kalan is None or kalan > 0:
                if kalan is not None:
                    adlar[hedef.name] = kalan - 1
                raise PermissionError(13, "Kilitli", str(hedef))
        asil_sil(hedef, dizin=dizin)

    monkeypatch.setattr(window_mod, "_sil", sil)


def test_kilitli_dosya_kisa_aralarla_yeniden_denenir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, od_gunlugu: list[logging.LogRecord]
) -> None:
    """Önceki oturumun bileşen süreci programdan sonra kapanır; o sırada dosya kilitlidir."""
    _yaz(tmp_path, *_BEKLENEN_DOSYALAR)
    _kilitli(monkeypatch, {"Web Data": 2})
    zaman = _SahteSaat()

    pencere_onbellegini_temizle(tmp_path, bekle=zaman.bekle, saat=zaman.saat)

    assert zaman.beklemeler == [0.25, 0.25]
    assert not any((tmp_path / goreli).exists() for goreli in _BEKLENEN_DOSYALAR)
    assert not od_gunlugu


def test_bekleme_suresi_ve_araligi_belgedeki_gibidir() -> None:
    """Tasarım §4.3 tehdit 24 ve plan: 3 sn, 0,25 sn arayla; gerçekte uyunur (meşgul döngü yok)."""
    assert TEMIZLIK_BEKLEME_SN == 3.0
    assert window_mod._TEMIZLIK_ARALIGI_SN == 0.25
    assert inspect.signature(pencere_onbellegini_temizle).parameters["bekle"].default is time.sleep


def test_kilit_kalkmazsa_sure_dolunca_tek_uyariyla_acilis_surer_oteki_ogeler_yine_silinir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, od_gunlugu: list[logging.LogRecord]
) -> None:
    _yaz(tmp_path, *_BEKLENEN_DOSYALAR, *_SAYFA_ONBELLEGI_ICERIGI)
    _kilitli(monkeypatch, {"Web Data": None})
    zaman = _SahteSaat()

    pencere_onbellegini_temizle(tmp_path, bekle=zaman.bekle, saat=zaman.saat)

    assert sum(zaman.beklemeler) == pytest.approx(3.0)
    assert _kayitlar(od_gunlugu) == [
        (
            logging.WARNING,
            "Pencere bileşeninin eski önbelleğinden 1 öğe silinemedi (PermissionError).",
            None,
        )
    ]
    assert (tmp_path / _PROFIL / "Web Data").exists()
    # Süre dolduktan sonraki öğe de denenir ve silinir.
    assert not (tmp_path / SAYFA_ONBELLEGI_DIZINI).exists()


def test_sure_butun_ogeler_icin_ortaktir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, od_gunlugu: list[logging.LogRecord]
) -> None:
    _yaz(tmp_path, *_BEKLENEN_DOSYALAR)
    _kilitli(monkeypatch, {"Web Data-journal": None, "Web Data": None})
    zaman = _SahteSaat()

    pencere_onbellegini_temizle(tmp_path, bekle=zaman.bekle, saat=zaman.saat)

    # İkinci kilitli öğe yeniden beklemez: açılışa eklenen gecikme en çok 3 sn'dir.
    assert sum(zaman.beklemeler) == pytest.approx(3.0)
    assert [kayit.getMessage() for kayit in od_gunlugu] == [
        "Pencere bileşeninin eski önbelleğinden 2 öğe silinemedi (PermissionError)."
    ]


def test_kilit_disindaki_hata_yeniden_denenmez(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, od_gunlugu: list[logging.LogRecord]
) -> None:
    asil_sil = window_mod._sil

    def sil(hedef: Path, *, dizin: bool) -> None:
        if hedef.name == "Web Data":
            raise OSError(errno.EIO, "Giriş/çıkış hatası", str(hedef))
        asil_sil(hedef, dizin=dizin)

    monkeypatch.setattr(window_mod, "_sil", sil)
    zaman = _SahteSaat()

    pencere_onbellegini_temizle(tmp_path, bekle=zaman.bekle, saat=zaman.saat)

    assert zaman.beklemeler == []
    assert [kayit.getMessage() for kayit in od_gunlugu] == [
        "Pencere bileşeninin eski önbelleğinden 1 öğe silinemedi (OSError)."
    ]


def _isletim_sistemi_kilitli(monkeypatch: pytest.MonkeyPatch, ad: str, kez: int | None) -> None:
    """`os.unlink`'i yamalar: `shutil.rmtree`'nin kendisi hata versin (gerçek silme yolu).

    Linux'ta rmtree dosyayı `dir_fd` ile ve yalnız adıyla siler; ad bu yüzden yolun sonundan okunur.
    """
    asil = os.unlink
    kalan = [kez]

    def unlink(yol: Any, *args: Any, **kwargs: Any) -> None:
        if os.path.basename(os.fsdecode(yol)) == ad and (kalan[0] is None or kalan[0] > 0):
            if kalan[0] is not None:
                kalan[0] -= 1
            raise PermissionError(13, "Kilitli", os.fsdecode(yol))
        asil(yol, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", unlink)


def test_sayfa_onbelleginde_kilitli_dosya_yeniden_denenir_kalanlar_silinir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, od_gunlugu: list[logging.LogRecord]
) -> None:
    """rmtree kısmen silip durur; yeniden denemede kalanı siler."""
    _yaz(tmp_path, *_SAYFA_ONBELLEGI_ICERIGI)
    _isletim_sistemi_kilitli(monkeypatch, "f_000001", 2)
    zaman = _SahteSaat()

    pencere_onbellegini_temizle(tmp_path, bekle=zaman.bekle, saat=zaman.saat)

    assert zaman.beklemeler == [0.25, 0.25]
    assert not (tmp_path / SAYFA_ONBELLEGI_DIZINI).exists()
    assert not od_gunlugu


def test_sayfa_onbelleginde_kilit_kalkmazsa_uyari_duser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, od_gunlugu: list[logging.LogRecord]
) -> None:
    """rmtree'nin hatası yutulsaydı (`ignore_errors`) kalan dosya sessizce kalırdı."""
    _yaz(tmp_path, *_SAYFA_ONBELLEGI_ICERIGI)
    _isletim_sistemi_kilitli(monkeypatch, "f_000001", None)
    zaman = _SahteSaat()

    pencere_onbellegini_temizle(tmp_path, bekle=zaman.bekle, saat=zaman.saat)

    assert sum(zaman.beklemeler) == pytest.approx(3.0)
    assert [kayit.getMessage() for kayit in od_gunlugu] == [
        "Pencere bileşeninin eski önbelleğinden 1 öğe silinemedi (PermissionError)."
    ]
    assert (tmp_path / _SAYFA_ONBELLEGI_ICERIGI[1]).exists()


def test_kilit_disindaki_hata_beklenmez_acilis_surer_gunluge_yalniz_tur(
    tmp_path: Path, od_gunlugu: list[logging.LogRecord]
) -> None:
    profil = tmp_path / "webview"
    # Silinemeyen öğe: aynı adda klasör (unlink klasörü silmez; Linux'ta IsADirectoryError).
    (profil / _PROFIL / "Web Data").mkdir(parents=True)
    sahte = _SahteWebview()

    open_window("http://127.0.0.1:1/", webview=sahte, platform="linux", storage_path=profil)

    assert sahte.start_kwargs["gui"] == "qt"
    uyarilar = [kayit for kayit in od_gunlugu if kayit.levelno >= logging.WARNING]
    assert _kayitlar(uyarilar) == [
        (
            logging.WARNING,
            "Pencere bileşeninin eski önbelleğinden 1 öğe silinemedi (IsADirectoryError).",
            None,
        )
    ]
    assert str(tmp_path) not in logging.Formatter().format(uyarilar[0])


def test_profil_yoksa_temizlik_sessizdir(
    tmp_path: Path, od_gunlugu: list[logging.LogRecord]
) -> None:
    pencere_onbellegini_temizle(tmp_path / "yok")

    assert not od_gunlugu


# ------------------------------------ Qt kolunda sayfa önbelleği bellektedir (saha bulgusu N-2)


class _HttpCacheType:
    MemoryHttpCache = "bellek"
    DiskHttpCache = "disk"


class _SahteProfil:
    """`QWebEngineProfile`'in kullandığımız yüzeyi."""

    HttpCacheType = _HttpCacheType

    def __init__(self, onbellek: Path) -> None:
        self._onbellek = onbellek
        self.tur: list[str] = []

    def setHttpCacheType(self, tur: str) -> None:  # noqa: N802 — Qt adı
        self.tur.append(tur)

    def cachePath(self) -> str:  # noqa: N802 — Qt adı
        return str(self._onbellek)


def _eski_onbellek(kok: Path) -> Path:
    """Pardus'ta görülen düzen: `~/.cache/oab-defteri/QtWebEngine/pywebview/Cache/…`."""
    dizin = kok / "QtWebEngine" / "pywebview"
    (dizin / "Cache" / "Cache_Data").mkdir(parents=True)
    (dizin / "Cache" / "Cache_Data" / "f_000011").write_bytes(b"material-symbols" * 64)
    return dizin


def test_eski_qt_onbellegi_programin_onbellek_kokundeyse_silinir(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    dizin = _eski_onbellek(kok)
    (kok / "webview").mkdir()

    assert window_mod.eski_qt_onbellegini_sil(dizin, kok) is True

    assert not dizin.exists()
    assert kok.is_dir() and (kok / "webview").is_dir()


def test_onbellek_kokunun_disindaki_yol_silinmez(tmp_path: Path, od_gunlugu: list[Any]) -> None:
    kok = tmp_path / "oab-defteri"
    kok.mkdir()
    yabanci = _eski_onbellek(tmp_path / "baska-program")

    assert window_mod.eski_qt_onbellegini_sil(yabanci, kok) is False

    assert (yabanci / "Cache" / "Cache_Data" / "f_000011").is_file()
    metin = " ".join(k.getMessage() for k in od_gunlugu)
    assert "dışında" in metin and str(tmp_path) not in metin


def test_onbellek_kokunun_kendisi_silinmez(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    (kok / "data").mkdir(parents=True)

    assert window_mod.eski_qt_onbellegini_sil(kok, kok) is False
    assert window_mod.eski_qt_onbellegini_sil(kok / "QtWebEngine" / "..", kok) is False

    assert (kok / "data").is_dir()


@pytest.mark.skipif(os.name == "nt", reason="sembolik bağ POSIX'te sınanır")
def test_baglarla_koke_kacan_yol_silinmez(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    kok.mkdir()
    disari = tmp_path / "kullanici-verisi"
    disari.mkdir()
    (disari / "veri.db").write_bytes(b"x")
    (kok / "QtWebEngine").symlink_to(disari, target_is_directory=True)

    assert window_mod.eski_qt_onbellegini_sil(kok / "QtWebEngine", kok) is False

    assert (disari / "veri.db").is_file()


def test_eski_onbellek_yoksa_sessizdir(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    kok.mkdir()

    assert window_mod.eski_qt_onbellegini_sil(kok / "QtWebEngine" / "pywebview", kok) is True


def test_bos_ya_da_goreli_onbellek_yolu_silinmez(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, od_gunlugu: list[Any]
) -> None:
    """Gizli profilde `cachePath()` boştur: `Path("")` çalışma dizinine çözülürdü (denetim 14.11.2026)."""
    kok = tmp_path / "oab-defteri"
    depo = kok / "webview"
    (depo / "Local Storage").mkdir(parents=True)
    (kok / "QtWebEngine").mkdir()
    monkeypatch.chdir(depo)

    assert window_mod.eski_qt_onbellegini_sil(Path(""), kok) is False
    assert window_mod.eski_qt_onbellegini_sil(Path("Local Storage"), kok) is False
    monkeypatch.chdir(kok)
    assert window_mod.eski_qt_onbellegini_sil(Path("QtWebEngine"), kok) is False

    assert (depo / "Local Storage").is_dir() and (kok / "QtWebEngine").is_dir()
    assert "göreli" in " ".join(k.getMessage() for k in od_gunlugu)


def test_pencerenin_deposu_ve_ust_dizini_silinmez(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    depo = kok / "ic" / "webview"
    (depo / "Local Storage").mkdir(parents=True)

    assert window_mod.eski_qt_onbellegini_sil(depo, kok, korunanlar=[depo]) is False
    assert window_mod.eski_qt_onbellegini_sil(kok / "ic", kok, korunanlar=[depo]) is False
    assert window_mod.eski_qt_onbellegini_sil(depo / "..", kok, korunanlar=[depo]) is False

    assert (depo / "Local Storage").is_dir()


def test_korunanin_kardesi_silinir(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    dizin = _eski_onbellek(kok)
    depo = kok / "webview"
    depo.mkdir()

    assert window_mod.eski_qt_onbellegini_sil(dizin, kok, korunanlar=[depo]) is True

    assert not dizin.exists() and depo.is_dir()


def _sayfa_arka_ucu() -> SimpleNamespace:
    kurulan: list[tuple[Any, Any]] = []

    class WebPage:
        def __init__(self, parent: Any = None, profile: Any = None) -> None:
            kurulan.append((parent, profile))

    return SimpleNamespace(BrowserView=SimpleNamespace(WebPage=WebPage), kurulan=kurulan)


def test_sayfa_kurulurken_profilin_onbellegi_bellek_ici_olur_eskisi_silinir(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    profil = _SahteProfil(_eski_onbellek(kok))
    arka_uc = _sayfa_arka_ucu()
    window_mod.qt_onbellegini_bagla(arka_uc, kok)

    arka_uc.BrowserView.WebPage("pencere", profile=profil)

    assert profil.tur == ["bellek"]
    assert not (kok / "QtWebEngine" / "pywebview").exists()
    assert arka_uc.kurulan == [("pencere", profil)]


def test_profilin_onbellegi_pencere_deposunu_gosterirse_silinmez(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    depo = kok / "webview"
    (depo / "Local Storage").mkdir(parents=True)
    profil = _SahteProfil(depo)
    arka_uc = _sayfa_arka_ucu()
    window_mod.qt_onbellegini_bagla(arka_uc, kok, korunanlar=[depo])

    arka_uc.BrowserView.WebPage("pencere", profile=profil)

    assert profil.tur == ["bellek"]
    assert (depo / "Local Storage").is_dir()


def test_profilsiz_sayfa_aynen_kurulur(tmp_path: Path) -> None:
    arka_uc = _sayfa_arka_ucu()
    window_mod.qt_onbellegini_bagla(arka_uc, tmp_path)

    arka_uc.BrowserView.WebPage("pencere")

    assert arka_uc.kurulan == [("pencere", None)]


def test_onbellek_duzenlenemezse_sayfa_yine_kurulur(tmp_path: Path, od_gunlugu: list[Any]) -> None:
    class _Bozuk(_SahteProfil):
        def setHttpCacheType(self, tur: str) -> None:  # noqa: N802
            raise RuntimeError("profil kapandı")

    arka_uc = _sayfa_arka_ucu()
    window_mod.qt_onbellegini_bagla(arka_uc, tmp_path)
    profil = _Bozuk(tmp_path / "x")

    arka_uc.BrowserView.WebPage("pencere", profile=profil)

    assert arka_uc.kurulan == [("pencere", profil)]
    assert "RuntimeError" in " ".join(k.getMessage() for k in od_gunlugu)


def test_onbellek_baglamasi_ikinci_kez_sarmaz(tmp_path: Path) -> None:
    arka_uc = _sayfa_arka_ucu()
    window_mod.qt_onbellegini_bagla(arka_uc, tmp_path)
    ilk = arka_uc.BrowserView.WebPage.__init__

    window_mod.qt_onbellegini_bagla(arka_uc, tmp_path)

    assert arka_uc.BrowserView.WebPage.__init__ is ilk


def test_linuxta_onbellek_koku_pencere_deposunun_ust_dizinidir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`storage_path` `AppPaths.webview_storage_path`'tir (`<önbellek>/webview`): kök onun üstüdür."""
    from desktop.paths import resolve_app_paths
    from desktop.yerel_pencere import YerelDosyaPenceresi

    yollar = resolve_app_paths(platform="linux", environ={"HOME": str(tmp_path)})
    assert yollar.webview_storage_path.parent == yollar.cache

    baglanan: list[tuple[Path, tuple[Path, ...]]] = []
    monkeypatch.setattr(
        window_mod,
        "qt_onbellegini_bagla",
        lambda _a, kok, *, korunanlar: baglanan.append((kok, tuple(korunanlar))),
    )
    monkeypatch.setattr(YerelDosyaPenceresi, "kapat", lambda self: None)

    class _Webview:
        settings: dict[str, Any] = {}
        SAVE_DIALOG = 30

        def initialize(self, gui: Any = None) -> Any:
            return SimpleNamespace()

        def create_window(self, *_a: Any, **_k: Any) -> Any:
            return SimpleNamespace(events=SimpleNamespace())

        def start(self, **_k: Any) -> None:
            self.initialize()

    open_window(
        "http://127.0.0.1:1/",
        webview=_Webview(),
        platform="linux",
        storage_path=yollar.webview_storage_path,
    )

    # Pencerenin kendi deposu (oturum çerezi, taslaklar) silmeden korunur (bağımsız denetim 14.11.2026).
    assert baglanan == [(yollar.cache, (yollar.webview_storage_path,))]
