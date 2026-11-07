"""Pencere katmanı testleri — WebView2 tespiti + MSHTML düşüşünün ENGELLİ olması."""

from __future__ import annotations

import base64
import logging
import os
import re
import stat
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from desktop.errors import WebViewUnavailableError
from desktop.window import (
    GENEL_SUZGEC,
    KAYDETME_SUZGECI,
    TUR_SUZGECLERI,
    WINDOW_TITLE,
    PencereKoprusu,
    gui_backend_for,
    open_window,
    require_window_runtime,
    set_windows_titlebar_theme,
    set_windows_window_icon,
    webview2_installed,
)


class _SahteWebview:
    """pywebview modülü yerine geçen kayıt tutucu."""

    def __init__(self) -> None:
        self.settings: dict[str, Any] = {"ALLOW_DOWNLOADS": False}
        self.pencereler: list[dict[str, Any]] = []
        self.start_kwargs: dict[str, Any] = {}

    def create_window(self, title: str, url: str, **kwargs: Any) -> object:
        self.pencereler.append({"title": title, "url": url, **kwargs})
        return object()

    def start(self, **kwargs: Any) -> None:
        self.start_kwargs = kwargs


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
        ("oab-defteri-kurulum.exe", "Tüm dosyalar (*.*)"),
        ("uzantisiz", "Tüm dosyalar (*.*)"),
    ],
    ids=["pdf", "buyuk_harf", "xlsx", "kurulum", "uzantisiz"],
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
