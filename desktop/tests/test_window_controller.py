"""Pencere denetçisi testleri — çarpı = çık, onay sorulmaz (T6; tasarım §4.2, §4.5).

pywebview Docker imajında yoktur: pencere ve olayları sahtedir. Sahte olay,
pywebview 5.3.2'nin `Event.set()` sözleşmesini taklit eder (işleyicilerden biri
`False` dönerse kapanma iptal). "Exe açılır, çarpıyla kapanır, çıkış kodu doğru"
F1a kapısında elle doğrulanır (packaging/windows/NOTLAR.md).

Uzun iş sürerken kapanış (plan F1b-3 "Uzun iş, çarpı, temiz kapanış"): sayaç gerçek
`shared.bakim.UzunIsSayaci`'dır; 60 sn'nin testleri saati ve sayacı sahte verir, gerçek süre
beklenmez. Sahte pencere `destroy`'da gerçek motorun yaptığını yapar: `closing` olayını kaldırır.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from desktop import window as window_mod
from desktop.window import (
    KAPANIS_BEKLEME_SN,
    KAPANIS_BEKLIYOR_OLAYI,
    WindowController,
    open_window,
)

#: Testin beklediği şeyin üst sınırı; olağan koşuda hiç dolmaz.
SINIR_SN = 5.0
BACKEND_DIZINI = Path(__file__).resolve().parents[2] / "backend"


@pytest.fixture
def sayac(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Gerçek uzun iş sayacının yeni bir örneği (süreç içi `UZUN_ISLER`'e dokunulmaz).

    Masaüstü testlerinde backend `sys.path`'te değildir; dizin yalnız bu testte eklenir.
    """
    monkeypatch.syspath_prepend(str(BACKEND_DIZINI))
    from shared.bakim import UzunIsSayaci

    return UzunIsSayaci()


class _SahteOlay:
    """pywebview `Event`: `+=` ile işleyici eklenir; `set()` iptal edildiyse `True` döner."""

    def __init__(self) -> None:
        self.isleyiciler: list[Callable[[], Any]] = []

    def __iadd__(self, isleyici: Callable[[], Any]) -> _SahteOlay:
        self.isleyiciler.append(isleyici)
        return self

    def set(self) -> bool:
        donenler = [isleyici() for isleyici in self.isleyiciler]
        return any(deger is False for deger in donenler)


class _SahtePencere:
    _YONTEMLER = frozenset({"hide", "show", "minimize", "restore", "maximize", "destroy"})

    def __init__(self) -> None:
        self.events = SimpleNamespace(
            closing=_SahteOlay(),
            shown=_SahteOlay(),
            minimized=_SahteOlay(),
            maximized=_SahteOlay(),
            restored=_SahteOlay(),
        )
        self.cagrilar: list[str] = []
        self.native: Any = None
        self.patlayan: str | None = None
        self.betikler: list[str] = []
        #: Gerçek motorda `destroy` `closing`'i kaldırır; burada testin isteğiyle.
        self.destroy_closing_kaldirir = False
        self.closing_sonuclari: list[bool] = []
        self.kapandi = threading.Event()
        self.bildirildi = threading.Event()

    def __getattr__(self, ad: str) -> Callable[[], None]:
        if ad not in self._YONTEMLER:
            raise AttributeError(ad)

        def yontem() -> None:
            if ad == self.patlayan:
                raise RuntimeError("pencere motoru meşgul")
            self.cagrilar.append(ad)
            if ad == "destroy":
                if self.destroy_closing_kaldirir:
                    self.closing_sonuclari.append(self.carpiya_bas())
                self.kapandi.set()

        return yontem

    def evaluate_js(self, betik: str) -> None:
        if self.patlayan == "evaluate_js":
            raise RuntimeError("sayfa yanıt vermiyor")
        self.betikler.append(betik)
        self.bildirildi.set()

    def carpiya_bas(self) -> bool:
        """`True` = pencere kapandı, `False` = kapanma iptal edildi."""
        return not self.events.closing.set()


class _SahteWebview:
    def __init__(self, pencere: _SahtePencere) -> None:
        self.settings: dict[str, Any] = {}
        self.pencere = pencere
        self.start_kwargs: dict[str, Any] | None = None

    def create_window(self, title: str, url: str, **kwargs: Any) -> _SahtePencere:
        return self.pencere

    def start(self, **kwargs: Any) -> None:
        self.start_kwargs = kwargs


class _SahteSayac:
    """Süresi saatle ölçülen sayaç: her bekleme sahte saati ilerletir, gerçek süre geçmez."""

    def __init__(self, saat: _SahteSaat, *, sayi: int = 1) -> None:
        self._saat = saat
        self.sayi = sayi
        self.sureler: list[float] = []

    def sifirlanmasini_bekle(self, sure: float) -> bool:
        self.sureler.append(sure)
        self._saat.simdi += sure
        return self.sayi == 0


class _SahteSaat:
    def __init__(self) -> None:
        self.simdi = 1000.0

    def __call__(self) -> float:
        return self.simdi


class _OkunamayanSayac:
    @property
    def sayi(self) -> int:
        raise RuntimeError("sayaç okunamadı")

    def sifirlanmasini_bekle(self, sure: float) -> bool:
        raise RuntimeError("sayaç okunamadı")


def _bagli(
    *, gosterildi: bool = True, platform: str = "linux", **ayarlar: Any
) -> tuple[WindowController, _SahtePencere]:
    denetci = WindowController(platform=platform, **ayarlar)
    pencere = _SahtePencere()
    pencere.destroy_closing_kaldirir = bool(ayarlar)
    denetci.bind(pencere)
    if gosterildi:
        pencere.events.shown.set()
    return denetci, pencere


# ------------------------------------------------------------------ çarpı


@pytest.mark.parametrize("platform", ["linux", "win32"])
def test_carpi_programi_kapatir_onay_sormaz(platform: str) -> None:
    """T6: kapanma iptal edilmez; pencere gizlenmez, küçültülmez (tepsi yok)."""
    denetci, pencere = _bagli(platform=platform)

    assert pencere.carpiya_bas() is True
    assert pencere.cagrilar == []  # pencereyi kullanıcı kapatıyor: ikinci destroy yok
    assert denetci.quitting is True


def test_carpidan_sonra_gelen_komutlar_etkisiz() -> None:
    denetci, pencere = _bagli()
    pencere.carpiya_bas()

    denetci.show()
    denetci.request_quit()

    assert pencere.cagrilar == []


def test_sayac_verilmezse_ya_da_sifirsa_carpi_bekletmez(sayac: Any) -> None:
    """Uzun iş yokken davranış T6'dır: kapanma iptal edilmez, pencere gizlenmez."""
    for ayar in ({}, {"sayac": sayac}):
        denetci, pencere = _bagli(**ayar)

        assert pencere.carpiya_bas() is True
        assert pencere.cagrilar == []
        assert denetci.quitting is True


def test_tepsi_ve_arayuze_cikis_olayi_yolu_yok() -> None:
    """T6: tepsi, gizleme ve görevli kipinde arayüze `od:cik-iste` olayı sökülmüştür."""
    denetci = WindowController(platform="linux")

    assert not hasattr(denetci, "tray_available")
    assert not hasattr(denetci, "ask_quit_in_spa")
    assert not hasattr(WindowController, "SPA_QUIT_EVENT")


# ------------------------------------------------------------------ Çık


def test_cik_pencereyi_kapatir() -> None:
    denetci, pencere = _bagli()

    denetci.request_quit()

    assert pencere.cagrilar == ["destroy"]
    assert pencere.carpiya_bas() is True  # destroy'un tetiklediği closing geçer
    assert denetci.quitting is True


def test_cik_iki_kez_gelse_de_pencere_bir_kez_kapatilir() -> None:
    denetci, pencere = _bagli()

    denetci.request_quit()
    denetci.request_quit()  # tepsiden Çık + kurucunun kapatma olayı

    assert pencere.cagrilar == ["destroy"]


def test_pencere_gosterilmeden_gelen_cik_gosterilince_uygulanir() -> None:
    """Kapatma olayı açılış sırasında gelebilir; pywebview API'si `shown`'ı bekler."""
    denetci, pencere = _bagli(gosterildi=False)

    denetci.request_quit()
    assert pencere.cagrilar == []

    pencere.events.shown.set()
    assert pencere.cagrilar == ["destroy"]


def test_kapatma_hatasi_yutulur() -> None:
    denetci, pencere = _bagli()
    pencere.patlayan = "destroy"

    denetci.request_quit()  # hata yükseltmez

    assert denetci.quitting is True


# ---------------------------------------------------------- Pencereyi aç


def test_pencereyi_ac_pencereyi_one_getirir() -> None:
    """İkinci açılış (`goster` komutu) çalışan pencereyi öne getirir."""
    denetci, pencere = _bagli()

    denetci.show()

    assert pencere.cagrilar == ["show"]


def test_pencereyi_ac_kucultulmus_pencereyi_eski_boyutuna_dondurur() -> None:
    denetci, pencere = _bagli()
    pencere.events.minimized.set()
    denetci.show()  # normal boyuttan küçültülmüş → restore

    pencere.events.maximized.set()
    pencere.events.minimized.set()
    denetci.show()  # büyütülmüşken küçültülmüş → maximize (restore normal boyuta düşürürdü)

    pencere.events.restored.set()
    denetci.show()  # küçültülmemiş → yalnız show

    assert pencere.cagrilar == ["show", "restore", "show", "maximize", "show"]


def test_pencereyi_ac_cikista_ya_da_pencere_yokken_etkisiz() -> None:
    WindowController(platform="linux").show()  # bağlanmamış
    denetci, pencere = _bagli()
    denetci.request_quit()

    denetci.show()

    assert pencere.cagrilar == ["destroy"]


def test_pencereyi_ac_hatasi_yutulur() -> None:
    denetci, pencere = _bagli()
    pencere.patlayan = "show"

    denetci.show()  # hata yükseltmez


# ------------------------------------------------------------ open_window


def test_denetci_pencereye_start_tan_once_baglanir(tmp_path: Path) -> None:
    sahte = _SahteWebview(_SahtePencere())
    denetci = WindowController(platform="linux")

    open_window(
        "http://127.0.0.1:1/",
        webview=sahte,
        platform="linux",
        storage_path=tmp_path,
        controller=denetci,
    )

    assert sahte.start_kwargs is not None and sahte.start_kwargs["gui"] == "qt"
    assert sahte.pencere.events.closing.isleyiciler == [denetci.on_closing]
    # Qt kolu kaydetme ve Aç pencerelerinin başlığını pywebview'ın metinlerinden alır (sözlük:
    # Türkçe). Anahtarlar pywebview 5.3.2 `localization.py`'den; yanlış anahtar sessizce İngilizce
    # başlık bırakırdı.
    assert sahte.start_kwargs["localization"] == {
        "global.saveFile": "Farklı kaydet",
        "linux.openFile": "Dosya aç",
    }


def test_cik_acilista_istendiyse_pencere_hic_baslatilmaz(tmp_path: Path) -> None:
    sahte = _SahteWebview(_SahtePencere())
    denetci = WindowController(platform="linux")
    denetci.request_quit()

    open_window(
        "http://127.0.0.1:1/",
        webview=sahte,
        platform="linux",
        storage_path=tmp_path,
        controller=denetci,
    )

    assert sahte.start_kwargs is None


# ------------------------------------------ Windows oturum kapanışı (FormClosing)


class _NetOlayi:
    def __init__(self) -> None:
        self.isleyiciler: list[Callable[[Any, Any], None]] = []

    def __iadd__(self, isleyici: Callable[[Any, Any], None]) -> _NetOlayi:
        self.isleyiciler.append(isleyici)
        return self


def test_windows_oturum_kapanisinda_is_yoksa_iptal_yok_ve_ek_isleyici_baglanmaz(
    sayac: Any,
) -> None:
    """§4.5: uzun iş yokken kapanma iptal edilmez; iptali geri alan .NET işleyicisi yoktur."""
    denetci = WindowController(platform="win32", sayac=sayac)
    pencere = _SahtePencere()
    pencere.native = SimpleNamespace(FormClosing=_NetOlayi())
    denetci.bind(pencere)
    pencere.events.shown.set()

    assert pencere.carpiya_bas() is True  # WindowsShutDown da UserClosing da iptal edilmez
    assert pencere.native.FormClosing.isleyiciler == []
    assert not hasattr(window_mod, "install_session_end_passthrough")


def test_windows_oturum_kapanisinda_uzun_is_kapanisi_bir_kez_erteler(sayac: Any) -> None:
    """Plan "Sorulmadı, tasarım cevaplıyor": `closing` nedeni taşımaz, oturum kapanışında da
    kapanış bir kez ertelenir, iş bitince pencere kendisi kapanır."""
    denetci = WindowController(platform="win32", sayac=sayac)
    pencere = _SahtePencere()
    pencere.destroy_closing_kaldirir = True
    pencere.native = SimpleNamespace(FormClosing=_NetOlayi())
    denetci.bind(pencere)
    pencere.events.shown.set()

    with sayac.is_():
        assert pencere.carpiya_bas() is False  # WindowsShutDown ertelendi
        assert pencere.bildirildi.wait(SINIR_SN)
    assert pencere.kapandi.wait(SINIR_SN)

    assert pencere.cagrilar.count("destroy") == 1
    assert pencere.native.FormClosing.isleyiciler == []


# ------------------------------------------------------ uzun iş sürerken kapanış


def test_is_surerken_carpi_kapanisi_bekler(sayac: Any) -> None:
    """§4.2: iş sürerken çarpı kapanmayı iptal eder, pencereyi gösterir, ön yüze olayı yollar; iş
    bitmeden pencere kapanmaz, iş bitince kendiliğinden ve bir kez kapanır."""
    denetci, pencere = _bagli(sayac=sayac)

    with sayac.is_():
        assert pencere.carpiya_bas() is False
        assert pencere.bildirildi.wait(SINIR_SN)
        assert not pencere.kapandi.wait(0.1)
        assert "destroy" not in pencere.cagrilar
        assert denetci.quitting is True

    assert pencere.kapandi.wait(SINIR_SN)
    assert pencere.cagrilar == ["show", "destroy"]
    assert pencere.betikler == [
        f"window.dispatchEvent(new CustomEvent('{KAPANIS_BEKLIYOR_OLAYI}'))"
    ]
    assert KAPANIS_BEKLIYOR_OLAYI == "od:kapanis-bekliyor"
    assert pencere.closing_sonuclari == [True]  # destroy'un tetiklediği closing iptal edilmez


def test_kapanma_isleyicisi_pencere_motorunu_cagirmaz(sayac: Any) -> None:
    """İşleyici pencere iş parçacığında eşzamanlı koşar: içinden `destroy` ya da `evaluate_js`
    pencereyi kilitlerdi. İşi yardımcı iş parçacığı yapar (modül başlığı)."""
    _, pencere = _bagli(sayac=sayac)
    cagiranlar: list[str] = []
    ana = threading.current_thread()
    gercek = pencere.evaluate_js

    def izleyen(betik: str) -> None:
        cagiranlar.append(threading.current_thread().name)
        gercek(betik)

    pencere.evaluate_js = izleyen  # type: ignore[method-assign]

    with sayac.is_():
        pencere.carpiya_bas()
        assert pencere.bildirildi.wait(SINIR_SN)
    assert pencere.kapandi.wait(SINIR_SN)

    assert cagiranlar and ana.name not in cagiranlar


@pytest.mark.parametrize(
    "istek",
    [
        pytest.param(lambda d, p: p.carpiya_bas(), id="ikinci_carpi"),
        pytest.param(lambda d, p: d.request_quit(), id="cik_kurucu_kanal_sigterm"),
    ],
)
def test_bekleme_sirasinda_gelen_kapatma_istegi_beklemeye_katilir(
    istek: Callable[[WindowController, _SahtePencere], Any],
    sayac: Any,
) -> None:
    """İkinci çarpı, Çık, kurucunun kapatma olayı, kanal ve SIGTERM aynı yoldan gelir: yeni bekleme
    başlamaz, pencere erken kapanmaz, kapanış bir kez yapılır."""
    _, pencere = _bagli(sayac=sayac)
    denetci = pencere.events.closing.isleyiciler[0].__self__

    with sayac.is_():
        assert pencere.carpiya_bas() is False
        assert pencere.bildirildi.wait(SINIR_SN)
        istek(denetci, pencere)
        istek(denetci, pencere)
        assert "destroy" not in pencere.cagrilar
    assert pencere.kapandi.wait(SINIR_SN)

    assert pencere.cagrilar.count("destroy") == 1
    assert len(pencere.betikler) == 1


def test_ikinci_carpi_kapanmayi_yine_iptal_eder(sayac: Any) -> None:
    _, pencere = _bagli(sayac=sayac)

    with sayac.is_():
        assert pencere.carpiya_bas() is False
        assert pencere.carpiya_bas() is False
    assert pencere.kapandi.wait(SINIR_SN)


def test_cik_is_surerken_beklemeyi_baslatir(sayac: Any) -> None:
    """Arayüzdeki Çık, kurucu, kanal ve SIGTERM `request_quit`'ten gelir; SIGTERM köprüsü Qt iş
    parçacığındadır, çağrı beklemez."""
    denetci, pencere = _bagli(sayac=sayac)

    with sayac.is_():
        denetci.request_quit()
        assert pencere.bildirildi.wait(SINIR_SN)
        assert "destroy" not in pencere.cagrilar
    assert pencere.kapandi.wait(SINIR_SN)

    assert pencere.cagrilar.count("destroy") == 1
    assert pencere.closing_sonuclari == [True]


def test_pencere_gosterilmeden_gelen_cik_is_surerken_gosterilince_bekler(sayac: Any) -> None:
    denetci, pencere = _bagli(gosterildi=False, sayac=sayac)

    with sayac.is_():
        denetci.request_quit()
        assert pencere.cagrilar == []
        pencere.events.shown.set()
        assert pencere.bildirildi.wait(SINIR_SN)
        assert "destroy" not in pencere.cagrilar
    assert pencere.kapandi.wait(SINIR_SN)


def test_altmis_saniye_dolunca_kapanis_bir_kez_yapilir(
    od_gunlugu: list[logging.LogRecord],
) -> None:
    """60 sn sınırı T6'yı korur: iş bitmese de pencere kapanır; gerçek süre beklenmez."""
    saat = _SahteSaat()
    sayac = _SahteSayac(saat)
    _, pencere = _bagli(sayac=sayac, saat=saat)

    assert pencere.carpiya_bas() is False
    assert pencere.kapandi.wait(SINIR_SN)

    assert KAPANIS_BEKLEME_SN == 60.0
    assert sum(sayac.sureler) == pytest.approx(KAPANIS_BEKLEME_SN)
    assert pencere.cagrilar.count("destroy") == 1
    assert pencere.closing_sonuclari == [True]
    assert any("60 sn içinde bitmedi" in kayit.getMessage() for kayit in od_gunlugu)


def test_bekleme_suresi_ve_saat_enjekte_edilebilir() -> None:
    saat = _SahteSaat()
    sayac = _SahteSayac(saat)
    _, pencere = _bagli(sayac=sayac, saat=saat, bekleme_sn=2.5)

    pencere.carpiya_bas()
    assert pencere.kapandi.wait(SINIR_SN)

    assert sum(sayac.sureler) == pytest.approx(2.5)


def test_is_erken_biterse_sure_dolmadan_kapanir() -> None:
    saat = _SahteSaat()
    sayac = _SahteSayac(saat)
    gercek = sayac.sifirlanmasini_bekle

    def uc_kezde_biter(sure: float) -> bool:
        if len(sayac.sureler) == 2:
            sayac.sayi = 0
        return gercek(sure)

    sayac.sifirlanmasini_bekle = uc_kezde_biter  # type: ignore[method-assign]
    _, pencere = _bagli(sayac=sayac, saat=saat)

    pencere.carpiya_bas()
    assert pencere.kapandi.wait(SINIR_SN)

    assert len(sayac.sureler) == 3


def test_sayac_okunamazsa_carpi_bekletmez(od_gunlugu: list[logging.LogRecord]) -> None:
    """Sayaç okunamazsa kapanış takılmaz (T6); işareti `write_marker_if_idle` kendisi okur."""
    denetci, pencere = _bagli(sayac=_OkunamayanSayac())

    assert pencere.carpiya_bas() is True

    assert denetci.quitting is True
    assert any("okunamadı" in kayit.getMessage() for kayit in od_gunlugu)


def test_cik_sayac_okunamazsa_pencereyi_kapatir() -> None:
    denetci, pencere = _bagli(sayac=_OkunamayanSayac())

    denetci.request_quit()

    assert pencere.cagrilar == ["destroy"]


def test_bekleme_sayac_hatasinda_da_kapanisi_yapar() -> None:
    """Sayaç bekleme sırasında düşerse pencere açık kalmaz."""
    sayac = _SahteSayac(_SahteSaat())

    def patlar(sure: float) -> bool:
        raise RuntimeError("sayaç bozuldu")

    sayac.sifirlanmasini_bekle = patlar  # type: ignore[method-assign]
    _, pencere = _bagli(sayac=sayac)

    assert pencere.carpiya_bas() is False
    assert pencere.kapandi.wait(SINIR_SN)
    assert pencere.cagrilar.count("destroy") == 1


@pytest.mark.parametrize("patlayan", ["show", "evaluate_js"])
def test_bildirim_hatasi_kapanisi_bozmaz(patlayan: str, sayac: Any) -> None:
    _, pencere = _bagli(sayac=sayac)
    pencere.patlayan = patlayan

    with sayac.is_():
        assert pencere.carpiya_bas() is False
    assert pencere.kapandi.wait(SINIR_SN)


def test_takilan_bildirim_altmis_saniyeyi_uzatmaz(sayac: Any) -> None:
    """`evaluate_js` sonucu süresiz bekleyebilir (pywebview): bildirim ayrı iş parçacığındadır,
    sayaç sıfıra inince pencere yine kapanır."""
    _, pencere = _bagli(sayac=sayac)
    takildi = threading.Event()
    birak = threading.Event()

    def takilan(betik: str) -> None:
        takildi.set()
        birak.wait(SINIR_SN * 2)

    pencere.evaluate_js = takilan  # type: ignore[method-assign]

    try:
        with sayac.is_():
            pencere.carpiya_bas()
            assert takildi.wait(SINIR_SN)
        assert pencere.kapandi.wait(SINIR_SN)
    finally:
        birak.set()


def test_bekleme_kucultulmus_pencereyi_gosterir(sayac: Any) -> None:
    _, pencere = _bagli(sayac=sayac)
    pencere.events.minimized.set()

    with sayac.is_():
        pencere.carpiya_bas()
        assert pencere.bildirildi.wait(SINIR_SN)
    assert pencere.kapandi.wait(SINIR_SN)

    assert pencere.cagrilar == ["show", "restore", "destroy"]


def test_yardimci_is_parcaciklari_sureci_tutmaz(sayac: Any) -> None:
    """Kapanış ve bildirim iş parçacıkları süreç sonunu beklemez (daemon)."""
    _, pencere = _bagli(sayac=sayac)

    with sayac.is_():
        pencere.carpiya_bas()
        adlar = {i.name: i.daemon for i in threading.enumerate() if i.name.startswith("od-kapanis")}
        assert pencere.bildirildi.wait(SINIR_SN)
    assert pencere.kapandi.wait(SINIR_SN)

    assert adlar and all(adlar.values())
