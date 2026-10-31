"""Sistem tepsisi testleri (tasarım §4.4 tepsi kip matrisi — §5.10-13, §4.5, UY-7).

pystray Docker imajında yoktur: sahte modülle sınanır. Linux Qt kurulumu ve
SIGTERM köprüsünün testleri `test_qt_kurulum.py`'ye taşındı (§13 D1).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from desktop import tray as tray_mod
from desktop.tray import (
    KIP_MATRISI,
    MENU_QUIT,
    MENU_SHOW,
    NullTray,
    PystrayTray,
    TrayActions,
    kip_sutunu,
    komutu_calistir,
    menu_durumu,
    menu_entries,
    start_tray,
)


class _Sayac:
    def __init__(self) -> None:
        self.goster = 0
        self.cik = 0

    def eylemler(self) -> TrayActions:
        def goster() -> None:
            self.goster += 1

        def cik() -> None:
            self.cik += 1

        return TrayActions(show=goster, quit=cik)


# ------------------------------------------------------------------ menü (F0)


def test_kip_bilgisi_verilmezse_menu_yalniz_ac_ve_cik() -> None:
    """Kip sağlayıcısı yoksa (ör. Django kurulmadan) kilitli sütunu: yalnız aç ve Çık."""
    sayac = _Sayac()

    assert [metin for metin, _ in menu_entries(sayac.eylemler())] == ["Pencereyi aç", "Çık"]
    assert (MENU_SHOW, MENU_QUIT) == ("Pencereyi aç", "Çık")


# ------------------------------------------------------------ Windows: pystray


class _SahtePystray:
    """pystray modülünün kullandığımız yüzeyi."""

    def __init__(self, *, patlasin: bool = False) -> None:
        self.ikonlar: list[Any] = []
        self._patlasin = patlasin
        disari = self

        class MenuItem:
            """pystray: metin, `enabled` ve `visible` çağrılabilir olabilir (öğeyle çağrılır)."""

            def __init__(
                self,
                text: Any,
                action: Callable[[], None],
                default: bool = False,
                enabled: Any = True,
                visible: Any = True,
            ) -> None:
                self._text, self.action, self.default = text, action, default
                self._enabled, self._visible = enabled, visible

            def _deger(self, alan: Any) -> Any:
                return alan(self) if callable(alan) else alan

            @property
            def text(self) -> str:
                return str(self._deger(self._text))

            @property
            def enabled(self) -> bool:
                return bool(self._deger(self._enabled))

            @property
            def visible(self) -> bool:
                return bool(self._deger(self._visible))

        class Menu:
            def __init__(self, *items: MenuItem) -> None:
                self.items = items

        class Icon:
            def __init__(self, name: str, icon: Image.Image, title: str, menu: Menu) -> None:
                self.name, self.icon, self.title, self.menu = name, icon, title, menu
                self.run_detached_cagri = 0
                self.stop_cagri = 0
                disari.ikonlar.append(self)

            def run_detached(self) -> None:
                if disari._patlasin:
                    raise OSError("Shell_NotifyIcon başarısız")
                self.run_detached_cagri += 1

            def stop(self) -> None:
                self.stop_cagri += 1

            def update_menu(self) -> None:
                self.guncelleme += 1

            guncelleme = 0

            def gorunenler(self) -> list[Any]:
                return [oge for oge in self.menu.items if oge.visible]

        self.MenuItem, self.Menu, self.Icon = MenuItem, Menu, Icon


def test_windows_tepsisi_run_detached_ile_kurulur() -> None:
    sahte = _SahtePystray()
    sayac = _Sayac()
    tepsi = PystrayTray(sayac.eylemler(), pystray_module=sahte)

    assert tepsi.start() is True
    assert tepsi.available is True
    (ikon,) = sahte.ikonlar
    assert ikon.run_detached_cagri == 1
    assert ikon.title == "OAB Defteri"
    assert [(i.text, i.default) for i in ikon.gorunenler()] == [
        ("Pencereyi aç", True),  # simgeye tıklama pencereyi açar
        ("Çık", False),
    ]

    ikon.gorunenler()[0].action()
    ikon.gorunenler()[1].action()
    assert (sayac.goster, sayac.cik) == (1, 1)


def test_windows_tepsisi_cikista_icon_stop_cagirir() -> None:
    """run_detached daemon OLMAYAN iş parçacığı açar: stop atlanırsa süreç asılı kalır."""
    sahte = _SahtePystray()
    tepsi = PystrayTray(_Sayac().eylemler(), pystray_module=sahte)
    tepsi.start()

    tepsi.stop()
    tepsi.stop()  # ikinci çağrı etkisiz

    assert sahte.ikonlar[0].stop_cagri == 1
    assert tepsi.available is False


def test_windows_tepsisi_kurulamazsa_program_surer(od_gunlugu: list[logging.LogRecord]) -> None:
    tepsi = PystrayTray(_Sayac().eylemler(), pystray_module=_SahtePystray(patlasin=True))

    assert tepsi.start() is False
    assert tepsi.available is False
    assert any("tepsi" in k.getMessage() for k in od_gunlugu)
    tepsi.stop()  # kurulmamış tepside de güvenli


def test_tepsi_komutu_hatasi_tepsiyi_dusurmez(od_gunlugu: list[logging.LogRecord]) -> None:
    def patla() -> None:
        raise RuntimeError("pencere yok")

    sahte = _SahtePystray()
    PystrayTray(TrayActions(show=patla, quit=patla), pystray_module=sahte).start()

    sahte.ikonlar[0].menu.items[0].action()  # hata yükseltmez

    assert any("Tepsi komutu başarısız" in k.getMessage() for k in od_gunlugu)


def test_pystray_modulu_yoksa_tepsisiz() -> None:
    """Geliştirme ortamında pystray kurulu değil: gerçek içe aktarma denenir, düşer."""
    tepsi = PystrayTray(_Sayac().eylemler())

    assert tepsi.start() is False


# ---------------------------------------------------------------- platform seçimi


def test_platforma_gore_tepsi_secilir(monkeypatch: pytest.MonkeyPatch) -> None:
    baslatilan: list[str] = []

    def kaydeden(ad: str) -> Callable[[object], bool]:
        def start(_self: object) -> bool:
            baslatilan.append(ad)
            return True

        return start

    monkeypatch.setattr(PystrayTray, "start", kaydeden("pystray"))
    eylemler = _Sayac().eylemler()

    assert isinstance(start_tray(eylemler, platform="win32"), PystrayTray)
    # Linux'ta tepsi yok; Qt kurulumu ve SIGTERM köprüsü `qt_kurulum`'dadır (§13 D1).
    assert isinstance(start_tray(eylemler, platform="linux"), NullTray)
    assert isinstance(start_tray(eylemler, platform="darwin"), NullTray)
    assert baslatilan == ["pystray"]


def test_tepsi_kurulamasa_da_nesne_doner_ve_durdurulabilir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(PystrayTray, "start", lambda self: False)

    tepsi = start_tray(_Sayac().eylemler(), platform="win32")

    assert tepsi.available is False
    tepsi.stop()


def test_null_tepsi() -> None:
    tepsi = NullTray()
    assert tepsi.available is False
    tepsi.stop()


def test_tepsi_ikonu_varsayilan_olarak_paket_yolundan_cozulur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alinan: list[Path | None] = []

    def kaydet(self: PystrayTray) -> bool:
        alinan.append(self._icon_path)
        return True

    monkeypatch.setattr(PystrayTray, "start", kaydet)
    monkeypatch.setattr(tray_mod, "app_icon_path", lambda: Path("/paket/oab-defteri.ico"))

    start_tray(_Sayac().eylemler(), platform="win32")

    assert alinan == [Path("/paket/oab-defteri.ico")]


def test_tepsi_geri_cagrisi_pystray_ve_qt_ile_uyumlu() -> None:
    """pystray `co_argcount`'a bakıp argümansız çağırır; Qt `triggered(bool)` değer verir."""
    cagri: list[int] = []
    sarili = tray_mod._guarded("deneme", lambda: cagri.append(1))

    assert sarili.__code__.co_argcount == 0
    sarili()
    sarili(False)
    assert cagri == [1, 1]


# ------------------------------------------------ kip matrisi (§4.4, §5.10-13)


class _Masa:
    """Tepsinin bütün hedeflerini kaydeden taklit masaüstü (kip değiştirilebilir)."""

    def __init__(self, kip: str = "yonetici", *, katalog_acik: bool = False) -> None:
        self.kip = kip
        self.acik = katalog_acik
        self.cagrilar: list[str] = []

    def _kaydet(self, ad: str) -> Callable[[], None]:
        def kaydet() -> None:
            self.cagrilar.append(ad)

        return kaydet

    def eylemler(self) -> TrayActions:
        return TrayActions(
            show=self._kaydet("pencere"),
            quit=self._kaydet("cik"),
            kip=lambda: self.kip,
            quit_gorevli=self._kaydet("cik-parola-spa"),
            katalog_satiri=lambda: (
                "Ağ Kataloğu: açık — http://192.168.10.5:8765/"
                if self.acik
                else "Ağ Kataloğu: kapalı"
            ),
            katalog_acik=lambda: self.acik,
            katalog_ac=self._kaydet("katalog-ac"),
            katalog_kapat=self._kaydet("katalog-kapat"),
            katalog_goster=self._kaydet("katalog-tarayici"),
            gorevli_kipine_gec=self._kaydet("gorevli"),
            kilitle=self._kaydet("kilitle"),
        )


def _gorunen(masa: _Masa) -> list[tuple[str, bool]]:
    return [(o.metin, o.etkin) for o in menu_durumu(masa.eylemler()) if o.gorunur]


def test_kip_matrisi_tasarim_tablosuyla_birebir() -> None:
    """§4.4 tablosu anlık görüntüsü: değişiklik bilinçli yapılır."""
    assert {kod: sorted(sutunlar) for kod, sutunlar in KIP_MATRISI.items()} == {
        "pencere": ["gorevli", "kilitli", "yonetici"],
        "katalog_durum": ["gorevli", "kilitli", "yonetici"],
        "katalog_ac_kapa": ["yonetici"],
        "gorevli": ["yonetici"],
        "kilitle": ["gorevli", "yonetici"],
        "cik": ["gorevli", "kilitli", "yonetici"],
    }


def test_yonetici_kipinde_butun_komutlar() -> None:
    masa = _Masa("yonetici", katalog_acik=True)

    assert _gorunen(masa) == [
        ("Pencereyi aç", True),
        ("Ağ Kataloğu: açık — http://192.168.10.5:8765/", True),  # tıklanınca tarayıcıda açılır
        ("Ağ Kataloğunu kapat", True),
        ("Görevli kipine geç", True),
        ("Kilitle", True),
        ("Çık", True),
    ]


def test_yonetici_kipinde_katalog_kapaliyken_ac_komutu() -> None:
    masa = _Masa("yonetici", katalog_acik=False)

    gorunen = _gorunen(masa)

    assert ("Ağ Kataloğunu aç", True) in gorunen
    assert ("Ağ Kataloğu: kapalı", False) in gorunen  # adres yok: tıklanmaz


def test_gorevli_kipinde_ayar_degistiren_komut_yok_katalog_yalniz_bilgi() -> None:
    masa = _Masa("gorevli", katalog_acik=True)

    assert _gorunen(masa) == [
        ("Pencereyi aç", True),
        ("Ağ Kataloğu: açık — http://192.168.10.5:8765/", False),  # bilgi
        ("Kilitle", True),
        ("Çık", True),
    ]


@pytest.mark.parametrize(
    "kip", ["kilitli", "kurulum", "guvenlik_dosyasi_kayip", "yeniden_baslat", "bilinmeyen"]
)
def test_kilitli_sutunu(kip: str) -> None:
    masa = _Masa(kip, katalog_acik=True)

    assert _gorunen(masa) == [
        ("Pencereyi aç", True),
        ("Ağ Kataloğu: açık — http://192.168.10.5:8765/", False),
        ("Çık", True),
    ]
    assert kip_sutunu(kip) == "kilitli"


def test_gorevli_kipinde_ayar_degistiren_komut_eski_menuden_de_reddedilir() -> None:
    """§5.10-13: menü yönetici kipinde kuruldu, kip sonra görevliye indi; komut reddedilir."""
    masa = _Masa("yonetici", katalog_acik=False)
    eylemler = masa.eylemler()
    menu_durumu(eylemler)  # menü yönetici kipinde çizildi
    masa.kip = "gorevli"

    for kod in ("katalog_ac_kapa", "gorevli"):
        assert komutu_calistir(eylemler, kod) is False
    assert komutu_calistir(eylemler, "katalog_durum") is False  # yalnız bilgi

    assert masa.cagrilar == []


def test_kilitliyken_kilitle_ve_ayar_komutlari_reddedilir() -> None:
    masa = _Masa("kilitli")
    eylemler = masa.eylemler()

    for kod in ("katalog_ac_kapa", "gorevli", "kilitle", "katalog_durum", "bilinmeyen"):
        assert komutu_calistir(eylemler, kod) is False
    assert masa.cagrilar == []


def test_cik_goreli_kipte_parolayi_spada_ister_digerlerinde_dogrudan() -> None:
    """§4.2-4: yönetici ve kilitli doğrudan; görevli pencere + SPA'da yönetici parolası."""
    masa = _Masa("gorevli")
    eylemler = masa.eylemler()

    komutu_calistir(eylemler, "cik")
    masa.kip = "yonetici"
    komutu_calistir(eylemler, "cik")
    masa.kip = "kilitli"
    komutu_calistir(eylemler, "cik")

    assert masa.cagrilar == ["cik-parola-spa", "cik", "cik"]


def test_yonetici_komutlari_hedeflerine_gider() -> None:
    masa = _Masa("yonetici", katalog_acik=True)
    eylemler = masa.eylemler()

    for kod in ("pencere", "katalog_durum", "katalog_ac_kapa", "gorevli", "kilitle"):
        assert komutu_calistir(eylemler, kod) is True
    masa.acik = False
    komutu_calistir(eylemler, "katalog_ac_kapa")

    assert masa.cagrilar == [
        "pencere",
        "katalog-tarayici",
        "katalog-kapat",
        "gorevli",
        "kilitle",
        "katalog-ac",
    ]


def test_kip_okunamazsa_kilitli_sayilir() -> None:
    def patla() -> str:
        raise RuntimeError("veritabanı meşgul")

    eylemler = TrayActions(show=lambda: None, quit=lambda: None, kip=patla, kilitle=lambda: None)

    assert [o.kod for o in menu_durumu(eylemler) if o.gorunur] == ["pencere", "cik"]
    assert komutu_calistir(eylemler, "kilitle") is False


def test_windows_tepsisi_menuyu_kip_degisince_yeniden_kurar() -> None:
    """pystray Win32 menüyü bir kez kurar: değişiklik `update_menu` ile yansır."""
    sahte = _SahtePystray()
    masa = _Masa("yonetici")
    tepsi = PystrayTray(masa.eylemler(), pystray_module=sahte, yenileme_sn=3600)
    tepsi.start()
    (ikon,) = sahte.ikonlar
    try:
        assert [i.text for i in ikon.gorunenler()] == [
            "Pencereyi aç",
            "Ağ Kataloğu: kapalı",
            "Ağ Kataloğunu aç",
            "Görevli kipine geç",
            "Kilitle",
            "Çık",
        ]

        assert tepsi.yenile() is False  # değişiklik yok: menü yeniden kurulmaz
        masa.kip = "gorevli"
        assert tepsi.yenile() is True
        assert ikon.guncelleme == 1
        assert [i.text for i in ikon.gorunenler()] == [
            "Pencereyi aç",
            "Ağ Kataloğu: kapalı",
            "Kilitle",
            "Çık",
        ]
        assert [i.enabled for i in ikon.gorunenler()] == [True, False, True, True]

        # Görevli kipinde Çık menüden seçilince parola SPA'da istenir.
        ikon.gorunenler()[-1].action()
        assert masa.cagrilar == ["cik-parola-spa"]
    finally:
        tepsi.stop()


def test_windows_tepsisi_yenileme_is_parcacigi_od_tepsi_ve_cikista_durur() -> None:
    import threading

    sahte = _SahtePystray()
    masa = _Masa("yonetici")
    tepsi = PystrayTray(masa.eylemler(), pystray_module=sahte, yenileme_sn=0.01)
    tepsi.start()
    adlar = {t.name for t in threading.enumerate()}
    masa.kip = "kilitli"

    import time

    son = time.monotonic() + 5
    while sahte.ikonlar[0].guncelleme == 0 and time.monotonic() < son:
        time.sleep(0.01)
    tepsi.stop()

    assert "od-tepsi" in adlar
    assert sahte.ikonlar[0].guncelleme >= 1
    assert "od-tepsi" not in {t.name for t in threading.enumerate()}


def test_ayar_acik_ama_katalog_acilamadiysa_tepsi_kapat_sunar() -> None:
    """F5 düzeltmesi: "Güvenlik duvarı izni yok" durumunda da ayar kapatılabilmeli.

    Durum satırı adres olmadığı için tıklanmaz (`katalog_acik` yanlış); aç/kapa
    ise `katalog_kapatilabilir`'e bakar ve "kapat"ı çalıştırır.
    """
    masa = _Masa("yonetici", katalog_acik=False)
    eylemler = masa.eylemler()
    eylemler = TrayActions(**{**eylemler.__dict__, "katalog_kapatilabilir": lambda: True})

    gorunen = [(o.metin, o.etkin) for o in menu_durumu(eylemler) if o.gorunur]

    assert ("Ağ Kataloğunu kapat", True) in gorunen
    assert ("Ağ Kataloğu: kapalı", False) in gorunen
    assert komutu_calistir(eylemler, "katalog_ac_kapa") is True
    assert masa.cagrilar == ["katalog-kapat"]


def _tasinabilir(masa: _Masa, *, kapatilabilir: bool) -> TrayActions:
    """KB-2: Pardus taşınabilir arşivinin tepsi hedefleri (katalog sunulmaz)."""
    eylemler = masa.eylemler()
    return TrayActions(
        **{
            **eylemler.__dict__,
            "katalog_satiri": lambda: "Ağ Kataloğu: taşınabilir sürümde sunulmaz",
            "katalog_kapatilabilir": lambda: kapatilabilir,
            "katalog_sunulur": lambda: False,
        }
    )


def test_tasinabilir_arsivde_tepsi_ac_sunmaz_ve_eski_menuden_de_reddeder() -> None:
    """KB-2 (28.09.2026): "Ağ Kataloğunu aç" görünmez; tıklansa da denetçiye gitmez."""
    masa = _Masa("yonetici", katalog_acik=False)
    eylemler = _tasinabilir(masa, kapatilabilir=False)

    gorunen = [(o.metin, o.etkin) for o in menu_durumu(eylemler) if o.gorunur]

    assert gorunen == [
        ("Pencereyi aç", True),
        ("Ağ Kataloğu: taşınabilir sürümde sunulmaz", False),
        ("Görevli kipine geç", True),
        ("Kilitle", True),
        ("Çık", True),
    ]
    assert komutu_calistir(eylemler, "katalog_ac_kapa") is False
    assert masa.cagrilar == []


def test_tasinabilir_arsivde_acik_kalmis_ayar_tepsiden_kapatilir() -> None:
    masa = _Masa("yonetici", katalog_acik=False)
    eylemler = _tasinabilir(masa, kapatilabilir=True)

    gorunen = [(o.metin, o.etkin) for o in menu_durumu(eylemler) if o.gorunur]

    assert ("Ağ Kataloğunu kapat", True) in gorunen
    assert ("Ağ Kataloğunu aç", True) not in gorunen
    assert komutu_calistir(eylemler, "katalog_ac_kapa") is True
    assert masa.cagrilar == ["katalog-kapat"]


def test_katalog_sunulur_okunamazsa_ac_sunulmaz() -> None:
    """Denetçi zaten reddeder; tepsi okunamayan durumda "aç" göstermez (fail-closed)."""
    masa = _Masa("yonetici", katalog_acik=False)

    def patla() -> bool:
        raise RuntimeError("okunamadı")

    eylemler = TrayActions(**{**masa.eylemler().__dict__, "katalog_sunulur": patla})

    assert "Ağ Kataloğunu aç" not in [o.metin for o in menu_durumu(eylemler) if o.gorunur]
    assert komutu_calistir(eylemler, "katalog_ac_kapa") is False
    assert masa.cagrilar == []


def test_katalog_sunulursa_tepsi_davranisi_degismez() -> None:
    masa = _Masa("yonetici", katalog_acik=False)
    eylemler = TrayActions(**{**masa.eylemler().__dict__, "katalog_sunulur": lambda: True})

    assert ("Ağ Kataloğunu aç", True) in [
        (o.metin, o.etkin) for o in menu_durumu(eylemler) if o.gorunur
    ]
    assert komutu_calistir(eylemler, "katalog_ac_kapa") is True
    assert masa.cagrilar == ["katalog-ac"]
