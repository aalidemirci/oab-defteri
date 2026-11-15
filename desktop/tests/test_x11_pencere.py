"""Dış dosya penceresini ana pencereye bağlama testleri (saha bulgusu K-yeni-2, Pardus 25, 13.11.2026).

`desktop/x11_pencere.py` başlığı. Pencere arama, bağlama, öne getirme, süre ve süreç sonu, X11 yokken
sessizlik ve ana pencerenin kimliğinin Qt'den alınışı sahte X11 ve sahte Qt sınıflarıyla sınanır. Gerçek
`WM_TRANSIENT_FOR` ve yığın sırası debian:13 (zenity 4.1.90) ve debian:12 (zenity 3.44) kaplarında Xvfb +
xfwm4 + gerçek Qt penceresiyle gösterildi (modül başlığı).
"""

from __future__ import annotations

import ast
import ctypes
import threading
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from desktop import x11_pencere
from desktop.x11_pencere import (
    DisPencereBaglayici,
    Xlib,
    _XEvent,
    ana_pencereyi_bagla,
)

_ANA = 0x400007
_DIS = 0x600004


class _SahteX11:
    """`X11Arayuzu`: pencere `bul_sonra` aramadan sonra görünür."""

    def __init__(self, *, bul_sonra: int = 0, patla: Exception | None = None) -> None:
        self._kalan = bul_sonra
        self._patla = patla
        self.aramalar: list[int] = []
        self.gecici: list[tuple[int, int]] = []
        self.one_getirilen: list[int] = []

    def pencere_bul(self, pid: int) -> int | None:
        self.aramalar.append(pid)
        if self._patla is not None:
            raise self._patla
        if self._kalan > 0:
            self._kalan -= 1
            return None
        return _DIS

    def gecici_yap(self, pencere: int, ana: int) -> None:
        self.gecici.append((pencere, ana))

    def one_getir(self, pencere: int) -> None:
        self.one_getirilen.append(pencere)


class _Saat:
    def __init__(self) -> None:
        self.simdi = 0.0

    def __call__(self) -> float:
        return self.simdi

    def bekle(self, sure: float) -> None:
        self.simdi += sure


def _baglayici(x11: _SahteX11 | None, saat: _Saat | None = None, **ek: Any) -> DisPencereBaglayici:
    saat = saat or _Saat()
    return DisPencereBaglayici(x11_yukle=lambda: x11, bekle=saat.bekle, saat=saat, **ek)


def _izle_bekle(baglayici: DisPencereBaglayici, pid: int, suruyor: Any = lambda: True) -> None:
    is_parcacigi = baglayici.izle(pid, suruyor)
    assert is_parcacigi is not None
    is_parcacigi.join(5)


def test_dis_pencere_bulununca_ana_pencereye_gecici_yapilir() -> None:
    x11 = _SahteX11(bul_sonra=3)
    baglayici = _baglayici(x11)
    baglayici.ana_pencere(_ANA)

    _izle_bekle(baglayici, 4242)

    assert x11.aramalar == [4242] * 4
    assert x11.gecici == [(_DIS, _ANA)]


def test_ana_pencere_kimligi_yoksa_aranmaz_kutuphane_yuklenmez() -> None:
    yuklenen: list[bool] = []

    def yukle() -> None:
        yuklenen.append(True)

    baglayici = DisPencereBaglayici(x11_yukle=yukle)

    assert baglayici.izle(1, lambda: True) is None
    assert yuklenen == []


def test_x11_yoksa_sessizce_gecilir() -> None:
    baglayici = _baglayici(None)
    baglayici.ana_pencere(_ANA)

    assert baglayici.izle(1, lambda: True) is None
    assert baglayici.one_getir() is False


def test_surec_biterse_arama_durur() -> None:
    x11 = _SahteX11(bul_sonra=100)
    baglayici = _baglayici(x11)
    baglayici.ana_pencere(_ANA)
    sayac = iter([True, True, False])

    _izle_bekle(baglayici, 7, lambda: next(sayac))

    assert len(x11.aramalar) == 2
    assert x11.gecici == []


def test_sure_dolunca_arama_durur(od_gunlugu: list[Any]) -> None:
    x11 = _SahteX11(bul_sonra=10_000)
    baglayici = _baglayici(x11, arama_sn=1.0, aralik_sn=0.1)
    baglayici.ana_pencere(_ANA)

    _izle_bekle(baglayici, 7)

    assert 10 <= len(x11.aramalar) <= 12
    assert x11.gecici == []
    assert "bulunamadı" in " ".join(k.getMessage() for k in od_gunlugu)


def test_x11_hatasi_yalniz_turuyle_gunluge_duser(od_gunlugu: list[Any]) -> None:
    baglayici = _baglayici(_SahteX11(patla=OSError("/home/uydurma/gizli")))
    baglayici.ana_pencere(_ANA)

    _izle_bekle(baglayici, 7)

    metin = " ".join(k.getMessage() for k in od_gunlugu)
    assert "OSError" in metin
    assert "uydurma" not in metin


def test_ikinci_cagrida_bagli_pencere_one_getirilir() -> None:
    x11 = _SahteX11()
    baglayici = _baglayici(x11)
    baglayici.ana_pencere(_ANA)
    _izle_bekle(baglayici, 7)

    assert baglayici.one_getir() is True
    assert x11.one_getirilen == [_DIS]


def test_surec_bitince_pencere_unutulur() -> None:
    x11 = _SahteX11()
    baglayici = _baglayici(x11)
    baglayici.ana_pencere(_ANA)
    _izle_bekle(baglayici, 7)

    baglayici.birak(7)

    assert baglayici.one_getir() is False
    assert x11.one_getirilen == []


def test_kimlik_sifirsa_ana_pencere_yok_sayilir() -> None:
    baglayici = _baglayici(_SahteX11())
    baglayici.ana_pencere(0)

    assert baglayici.ana_pencere_kimligi is None


def test_kutuphane_bir_kez_yuklenir() -> None:
    yuklenen: list[int] = []
    x11 = _SahteX11()

    def yukle() -> _SahteX11:
        yuklenen.append(1)
        return x11

    saat = _Saat()
    baglayici = DisPencereBaglayici(x11_yukle=yukle, bekle=saat.bekle, saat=saat)
    baglayici.ana_pencere(_ANA)
    _izle_bekle(baglayici, 1)
    _izle_bekle(baglayici, 2)

    assert yuklenen == [1]


# ----------------------------------------------------------------- Xlib yükleyicisi


def test_display_yoksa_kutuphane_yuklenmez(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wayland ya da ekransız oturum: X11 yolu hiç denenmez."""
    monkeypatch.setattr(ctypes, "CDLL", lambda *_a: pytest.fail("kütüphane yüklenmemeli"))

    assert Xlib.yukle(ortam={"WAYLAND_DISPLAY": "wayland-0"}) is None


def test_kutuphane_yuklenemezse_none_doner(monkeypatch: pytest.MonkeyPatch) -> None:
    def yuklenemez(ad: str) -> Any:
        assert ad == "libX11.so.6"  # sürecin yüklediği Xlib, tam yol değil (modül başlığı)
        raise OSError("yok")

    monkeypatch.setattr(ctypes, "CDLL", yuklenemez)

    assert Xlib.yukle(ortam={"DISPLAY": ":0"}) is None


# ------------------------------------------- Xlib katmanı (sahte libX11, bağımsız denetim 14.11.2026)
#
# `Xlib` çağrıları ve argümanları kaydeden sahte bir kütüphaneyle sınanır: atom türü, pid eşlemesi,
# her yolda XFree / XSync / eski hata işleyicisi / XCloseDisplay sırası ve istemci iletisinin
# değerleri. Gerçek X sunucusundaki davranış modül başlığındaki kap sınamasındadır.

_EKRAN = 0xD15
_KOK = 0x1EE
_ONCEKI_ISLEYICI = 0xE51
_XA_STRING = 31
_XA_ATOM = 4


class _Islev:
    """Sahte kütüphanenin bir işlevi: `argtypes`/`restype` atanabilir, çağrı kaydedilir."""

    def __init__(self, kutuphane: _SahteKutuphane, ad: str) -> None:
        self._kutuphane = kutuphane
        self._ad = ad
        self.argtypes: Any = None
        self.restype: Any = None

    def __call__(self, *argumanlar: Any) -> Any:
        return self._kutuphane.cagrildi(self._ad, argumanlar)


def _deger(arguman: Any) -> Any:
    """ctypes nesnesinin Python değeri (kayıtlar karşılaştırılabilsin)."""
    if isinstance(arguman, ctypes.c_void_p):
        return arguman.value
    return arguman


class _SahteKutuphane:
    """`libX11.so.6`'nın `Xlib`'in kullandığı yüzü; özellikler `(pencere, ad) → (tür, biçim, değerler)`."""

    def __init__(
        self,
        ozellikler: dict[tuple[int, str], tuple[int, int, list[int]]] | None = None,
        *,
        ekran: int = _EKRAN,
        patlayan: str | None = None,
    ) -> None:
        self.ozellikler = ozellikler or {}
        self.ekran = ekran
        self.patlayan = patlayan
        self.cagrilar: list[tuple[str, tuple[Any, ...]]] = []
        self.olaylar: list[dict[str, Any]] = []
        self._atomlar: dict[str, int] = {}
        self._diziler: list[Any] = []
        self.verilen_veriler: list[int] = []
        self.islevler: dict[str, _Islev] = {}

    def __getattr__(self, ad: str) -> _Islev:
        if ad.startswith("X"):
            islevler: dict[str, _Islev] = self.__dict__["islevler"]
            if ad not in islevler:
                islevler[ad] = _Islev(self, ad)
            return islevler[ad]
        raise AttributeError(ad)

    def atom(self, ad: str) -> int:
        return self._atomlar.setdefault(ad, 100 + len(self._atomlar))

    def adlar(self) -> list[str]:
        return [ad for ad, _ in self.cagrilar]

    def cagrildi(self, ad: str, argumanlar: tuple[Any, ...]) -> Any:
        self.cagrilar.append((ad, tuple(_deger(a) for a in argumanlar)))
        if ad == self.patlayan:
            raise OSError("sahte X hatası")
        if ad == "XOpenDisplay":
            return self.ekran
        if ad == "XSetErrorHandler":
            return _ONCEKI_ISLEYICI
        if ad == "XDefaultRootWindow":
            return _KOK
        if ad == "XInternAtom":
            return self.atom(argumanlar[1].decode("ascii"))
        if ad == "XGetWindowProperty":
            return self._ozellik_ver(argumanlar)
        if ad == "XSendEvent":
            ileti = argumanlar[4]._obj.xclient
            self.olaylar.append(
                {
                    "type": ileti.type,
                    "send_event": ileti.send_event,
                    "window": ileti.window,
                    "message_type": ileti.message_type,
                    "format": ileti.format,
                    "data": list(ileti.data),
                }
            )
        return 0

    def _ozellik_ver(self, argumanlar: tuple[Any, ...]) -> int:
        pencere, atom, istenen_tur = argumanlar[1], argumanlar[2], argumanlar[6]
        ad = next(a for a, kimlik in self._atomlar.items() if kimlik == atom)
        kayit = self.ozellikler.get((pencere, ad))
        gercek_tur, bicim, adet, _kalan, veri = (a._obj for a in argumanlar[7:12])
        if kayit is None:
            gercek_tur.value, bicim.value, adet.value, veri.value = 0, 0, 0, None
            return 0
        tur, bicim_degeri, degerler = kayit
        dizi = (ctypes.c_ulong * max(len(degerler), 1))(*degerler)
        self._diziler.append(dizi)
        gercek_tur.value = tur
        bicim.value = bicim_degeri
        adet.value = len(degerler)
        veri.value = ctypes.addressof(dizi)
        self.verilen_veriler.append(ctypes.addressof(dizi))
        assert istenen_tur in (x11_pencere._XA_WINDOW, x11_pencere._XA_CARDINAL)
        return 0


def _istemci_listesi(**pidler: Any) -> dict[tuple[int, str], tuple[int, int, list[int]]]:
    """Kökün `_NET_CLIENT_LIST`'i ve pencerelerin `_NET_WM_PID`'leri (`p<kimlik>=pid`)."""
    pencereler = [int(ad[1:]) for ad in pidler]
    ozellikler: dict[tuple[int, str], tuple[int, int, list[int]]] = {
        (_KOK, "_NET_CLIENT_LIST"): (x11_pencere._XA_WINDOW, 32, pencereler)
    }
    for ad, pid in pidler.items():
        if pid is not None:
            ozellikler[(int(ad[1:]), "_NET_WM_PID")] = pid
    return ozellikler


def _baglanti_cercevesi(kutuphane: _SahteKutuphane) -> None:
    """Her işlem: bağlan, hatayı yutan işleyiciyi kur, … , XSync, eski işleyici, bağlantıyı kapat."""
    cagrilar = kutuphane.cagrilar
    yutan = ctypes.cast(x11_pencere._YUTAN_ISLEYICI, ctypes.c_void_p).value
    assert cagrilar[0] == ("XOpenDisplay", (None,))
    assert cagrilar[1] == ("XSetErrorHandler", (yutan,))
    assert cagrilar[-3:] == [
        ("XSync", (_EKRAN, 0)),
        ("XSetErrorHandler", (_ONCEKI_ISLEYICI,)),
        ("XCloseDisplay", (_EKRAN,)),
    ]
    assert kutuphane.adlar().count("XOpenDisplay") == 1
    assert kutuphane.adlar().count("XCloseDisplay") == 1


def test_xlib_pid_eslesen_son_pencereyi_bulur() -> None:
    kart = x11_pencere._XA_CARDINAL
    kutuphane = _SahteKutuphane(
        _istemci_listesi(
            p11=(kart, 32, [100]),
            p12=(kart, 32, [200]),
            p13=None,  # `_NET_WM_PID` yazmayan pencere
            p14=(_XA_STRING, 8, [200]),  # yanlış türde özellik eşleşmez
            p15=(kart, 32, [200]),
            p16=(_XA_ATOM, 32, [200]),  # 32 bitlik ama yanlış türde özellik de eşleşmez
        )
    )
    xlib = Xlib(kutuphane)

    assert xlib.pencere_bul(200) == 15
    assert xlib.pencere_bul(100) == 11
    assert xlib.pencere_bul(300) is None


def test_xlib_pencere_listesini_ve_pidi_dogru_turle_ister() -> None:
    kutuphane = _SahteKutuphane(_istemci_listesi(p11=(x11_pencere._XA_CARDINAL, 32, [7])))

    Xlib(kutuphane).pencere_bul(7)

    istekler = [a for ad, a in kutuphane.cagrilar if ad == "XGetWindowProperty"]
    assert [(a[1], a[2], a[5], a[6]) for a in istekler] == [
        (_KOK, kutuphane.atom("_NET_CLIENT_LIST"), 0, x11_pencere._XA_WINDOW),
        (11, kutuphane.atom("_NET_WM_PID"), 0, x11_pencere._XA_CARDINAL),
    ]


def test_xlib_her_ozellik_verisini_serbest_birakir() -> None:
    """Pencere 0,1 sn'de bir aranır: XFree'siz her arama belleği sızdırırdı."""
    kart = x11_pencere._XA_CARDINAL
    kutuphane = _SahteKutuphane(
        _istemci_listesi(p11=(kart, 32, [1]), p12=(_XA_STRING, 8, [2]), p13=None)
    )

    Xlib(kutuphane).pencere_bul(9)

    serbest = [a[0] for ad, a in kutuphane.cagrilar if ad == "XFree"]
    assert len(kutuphane.verilen_veriler) == 3
    assert sorted(serbest) == sorted(kutuphane.verilen_veriler)


@pytest.mark.parametrize("islem", ["pencere_bul", "gecici_yap", "one_getir"])
def test_xlib_her_islem_baglantisini_acar_ve_kapatir(islem: str) -> None:
    kutuphane = _SahteKutuphane(_istemci_listesi())
    xlib = Xlib(kutuphane)

    islemler: dict[str, Callable[[], object]] = {
        "pencere_bul": lambda: xlib.pencere_bul(1),
        "gecici_yap": lambda: xlib.gecici_yap(_DIS, _ANA),
        "one_getir": lambda: xlib.one_getir(_DIS),
    }
    islemler[islem]()

    _baglanti_cercevesi(kutuphane)


def test_xlib_hata_olsa_da_isleyici_geri_konur_baglanti_kapanir() -> None:
    kutuphane = _SahteKutuphane(patlayan="XSetTransientForHint")

    with pytest.raises(OSError, match="sahte"):
        Xlib(kutuphane).gecici_yap(_DIS, _ANA)

    _baglanti_cercevesi(kutuphane)


def test_xlib_ekrana_baglanilamazsa_oserror_isleyiciye_dokunulmaz() -> None:
    kutuphane = _SahteKutuphane(ekran=0)

    with pytest.raises(OSError):
        Xlib(kutuphane).pencere_bul(1)

    assert kutuphane.adlar() == ["XOpenDisplay"]


def test_xlib_gecici_yap_transient_yazar_gorev_cubugundan_dusurur() -> None:
    kutuphane = _SahteKutuphane()

    Xlib(kutuphane).gecici_yap(_DIS, _ANA)

    assert ("XSetTransientForHint", (_EKRAN, _DIS, _ANA)) in kutuphane.cagrilar
    gonderilen = [a for ad, a in kutuphane.cagrilar if ad == "XSendEvent"]
    assert [a[:4] for a in gonderilen] == [(_EKRAN, _KOK, 0, (1 << 20) | (1 << 19))]
    assert kutuphane.olaylar == [
        {
            "type": 33,  # ClientMessage
            "send_event": 1,
            "window": _DIS,
            "message_type": kutuphane.atom("_NET_WM_STATE"),
            "format": 32,
            # EWMH: eylem (1 = ekle), özellik 1, özellik 2, kaynak (2 = kullanıcı adına)
            "data": [1, kutuphane.atom("_NET_WM_STATE_SKIP_TASKBAR"), 0, 2, 0],
        }
    ]


def test_xlib_one_getir_etkin_pencere_iletisi_sonra_raise() -> None:
    kutuphane = _SahteKutuphane()

    Xlib(kutuphane).one_getir(_DIS)

    assert kutuphane.olaylar == [
        {
            "type": 33,
            "send_event": 1,
            "window": _DIS,
            "message_type": kutuphane.atom("_NET_ACTIVE_WINDOW"),
            "format": 32,
            "data": [2, 0, 0, 0, 0],
        }
    ]
    adlar = kutuphane.adlar()
    assert ("XRaiseWindow", (_EKRAN, _DIS)) in kutuphane.cagrilar
    assert adlar.index("XSendEvent") < adlar.index("XRaiseWindow")


def test_xlib_imzalari_kurulur() -> None:
    """Argüman türleri kurulmazsa ctypes 64 bitte `Window`/`long`'u `int`e kırpardı."""
    kutuphane = _SahteKutuphane()
    Xlib(kutuphane)
    islevler = kutuphane.islevler

    assert islevler["XOpenDisplay"].restype is ctypes.c_void_p
    assert len(islevler["XGetWindowProperty"].argtypes) == 12
    assert islevler["XSendEvent"].argtypes[3] is ctypes.c_long
    assert islevler["XSetTransientForHint"].argtypes == [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
    ]
    assert islevler["XSetErrorHandler"].restype is ctypes.c_void_p


def test_istemci_iletisi_xlibin_olay_boyundadir() -> None:
    """`XEvent` 24 `long`'luk birliktir; kısa yapı `XSendEvent`'te yığını taşırırdı."""
    assert ctypes.sizeof(_XEvent) == 24 * ctypes.sizeof(ctypes.c_long)


def test_modul_ldconfig_calistirmaz() -> None:
    """`ctypes.util.find_library` Linux'ta `ldconfig`'i dış süreçle çalıştırır (modül başlığı)."""
    agac = ast.parse(Path(x11_pencere.__file__).read_text(encoding="utf-8"))
    adlar = {d.attr for d in ast.walk(agac) if isinstance(d, ast.Attribute)}
    aktarilan = {a.name for d in ast.walk(agac) if isinstance(d, ast.Import) for a in d.names}

    assert "find_library" not in adlar
    assert "ctypes.util" not in aktarilan


# ------------------------------------------------------- ana pencerenin X kimliği


class _Pencere:
    def __init__(self, kimlik: int) -> None:
        self._kimlik = kimlik

    def winId(self) -> int:  # noqa: N802 — Qt adı
        return self._kimlik


def _arka_uc(platform: str) -> SimpleNamespace:
    gosterilen: list[Any] = []

    class BrowserView:
        def showEvent(self, olay: Any) -> None:  # noqa: N802 — Qt adı
            gosterilen.append(olay)

    return SimpleNamespace(
        BrowserView=BrowserView,
        QApplication=SimpleNamespace(platformName=lambda: platform),
        gosterilen=gosterilen,
    )


def test_pencere_gosterilirken_x_kimligi_alinir_asil_olay_kosar() -> None:
    arka_uc = _arka_uc("xcb")
    baglayici = DisPencereBaglayici(x11_yukle=lambda: None)
    ana_pencereyi_bagla(arka_uc, baglayici)

    arka_uc.BrowserView.showEvent(_Pencere(_ANA), "olay")

    assert baglayici.ana_pencere_kimligi == _ANA
    assert arka_uc.gosterilen == ["olay"]


def test_waylandda_kimlik_alinmaz() -> None:
    arka_uc = _arka_uc("wayland")
    baglayici = DisPencereBaglayici(x11_yukle=lambda: None)
    ana_pencereyi_bagla(arka_uc, baglayici)

    arka_uc.BrowserView.showEvent(_Pencere(_ANA), "olay")

    assert baglayici.ana_pencere_kimligi is None
    assert arka_uc.gosterilen == ["olay"]


def test_kimlik_okunamazsa_pencere_yine_gosterilir(od_gunlugu: list[Any]) -> None:
    class _Bozuk:
        def winId(self) -> int:  # noqa: N802
            raise RuntimeError("yok")

    arka_uc = _arka_uc("xcb")
    baglayici = DisPencereBaglayici(x11_yukle=lambda: None)
    ana_pencereyi_bagla(arka_uc, baglayici)

    arka_uc.BrowserView.showEvent(_Bozuk(), "olay")

    assert arka_uc.gosterilen == ["olay"]
    assert "RuntimeError" in " ".join(k.getMessage() for k in od_gunlugu)


def test_ikinci_baglama_yeniden_sarmaz() -> None:
    arka_uc = _arka_uc("xcb")
    baglayici = DisPencereBaglayici(x11_yukle=lambda: None)
    ana_pencereyi_bagla(arka_uc, baglayici)
    ilk = arka_uc.BrowserView.showEvent

    ana_pencereyi_bagla(arka_uc, baglayici)

    assert arka_uc.BrowserView.showEvent is ilk


def test_is_parcacigi_baslatilamazsa_sessizce_gecilir(
    monkeypatch: pytest.MonkeyPatch, od_gunlugu: list[Any]
) -> None:
    """Kaynak tükenmesi (`can't start new thread`): hata dosya penceresine taşmaz (modül başlığı)."""
    x11 = _SahteX11()
    baglayici = _baglayici(x11)
    baglayici.ana_pencere(_ANA)

    def baslamaz(_self: threading.Thread) -> None:
        raise RuntimeError("can't start new thread")

    monkeypatch.setattr(threading.Thread, "start", baslamaz)

    assert baglayici.izle(7, lambda: True) is None
    assert x11.aramalar == []
    assert "RuntimeError" in " ".join(k.getMessage() for k in od_gunlugu)


def test_arama_ayri_is_parcaciginda_kosar() -> None:
    """`izle` çağıranı (köprünün iş parçacığı) bekletmez: pencere bulunana dek dönmüş olur."""
    birak = threading.Event()
    bulundu = threading.Event()

    class _Yavas(_SahteX11):
        def pencere_bul(self, pid: int) -> int | None:
            birak.wait(5)
            bulundu.set()
            return _DIS

    baglayici = _baglayici(_Yavas())
    baglayici.ana_pencere(_ANA)
    is_parcacigi = baglayici.izle(1, lambda: True)

    assert is_parcacigi is not None and is_parcacigi.daemon
    assert not bulundu.is_set()
    birak.set()
    is_parcacigi.join(5)
    assert bulundu.is_set()
