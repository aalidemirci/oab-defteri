"""Linux'ta kaydetme ve Aç pencereleri testleri: zenity/kdialog dış süreçte (saha bulgusu K-P3).

Seçenekler üç Debian'ın zenity ve kdialog'unda kaplarda denendi (`desktop/yerel_pencere.py` başlığı);
burada argümanlar, dönüş kodlarının eşlemesi, Qt penceresine düşüş, temiz ortam ve kapanışta açık
pencerenin sonlandırılması sahte süreçle sınanır; sayfanın dosya kutusunun Qt'ye bağlanışı
(`chooseFiles`, iç içe olay döngüsü) sahte Qt çekirdeğiyle sınanır. Gerçek zenity'nin bu argümanlarla açıldığı,
seçimi verdiği ve iptali bildirdiği debian:11/12/13 kaplarında Xvfb altında gösterildi; masaüstündeki
gerçek pencere (Türkçe, kenar çubuğunda USB bellek) Pardus'ta kullanıcıda denenir.
"""

from __future__ import annotations

import subprocess
import threading
from types import SimpleNamespace
from typing import Any, cast

import pytest

from desktop import yerel_pencere
from desktop.yerel_pencere import (
    YerelDosyaPenceresi,
    kdialog_argv,
    qt_dongusunde_bekleyici,
    suzgec_parcalari,
    yukleme_isleyicisi,
    yukleme_penceresini_bagla,
    zenity_argv,
    zenity_ortami,
)


class _SahteSurec:
    """`subprocess.Popen`'ın kullandığımız yüzeyi."""

    pid = 4242

    def __init__(self, kod: int, cikti: bytes = b"", bekle: threading.Event | None = None) -> None:
        self.returncode: int | None = None
        self._kod = kod
        self._cikti = cikti
        self._bekle = bekle
        self.sonlandirildi = False

    def communicate(self, timeout: float | None = None) -> tuple[bytes, None]:
        if self._bekle is not None:
            self._bekle.wait(5)
        self.returncode = -15 if self.sonlandirildi else self._kod
        return self._cikti, None

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.sonlandirildi = True
        if self._bekle is not None:
            self._bekle.set()

    def kill(self) -> None:
        self.terminate()


class _Baslatici:
    """Araç adına göre sıradaki süreci verir; `--version` sorusuna `surum` döner."""

    def __init__(self, *surecler: _SahteSurec | Exception, surum: bytes = b"4.1.90\n") -> None:
        self._surecler = list(surecler)
        self.surum = surum
        self.cagrilar: list[tuple[list[str], dict[str, Any]]] = []
        self.surum_sorulari = 0

    def __call__(self, argv: list[str], **anahtarlar: Any) -> _SahteSurec:
        if argv[-1] == "--version":
            self.surum_sorulari += 1
            return _SahteSurec(0, self.surum)
        self.cagrilar.append((argv, anahtarlar))
        sonraki = self._surecler.pop(0)
        if isinstance(sonraki, Exception):
            raise sonraki
        return sonraki


def _bulucu(*kurulu: str) -> Any:
    return lambda ad: f"/usr/bin/{ad}" if ad in kurulu else None


def _pencere(baslatici: _Baslatici, *kurulu: str) -> YerelDosyaPenceresi:
    return YerelDosyaPenceresi(bul=_bulucu(*kurulu), baslat=cast(Any, baslatici))


def _kaydet(pencere: YerelDosyaPenceresi, **ek: Any) -> str | None:
    secenekler: dict[str, Any] = {
        "kaydet": True,
        "baslik": "Farklı kaydet",
        "klasor": "/home/uydurma",
        "ad": "Yedek-Raporu_07.11.2026.pdf",
        "suzgecler": ("PDF belgesi (*.pdf)",),
    }
    secenekler.update(ek)
    return pencere.ac(**secenekler)


# ------------------------------------------------------------------ argümanlar


@pytest.mark.parametrize(
    ("suzgec", "beklenen"),
    [
        ("PDF belgesi (*.pdf)", ("PDF belgesi", ["*.pdf", "*.PDF"])),
        ("Excel dosyası (*.xlsx)", ("Excel dosyası", ["*.xlsx", "*.XLSX"])),
        ("OAB Defteri yedeği (*.odbak)", ("OAB Defteri yedeği", ["*.odbak", "*.ODBAK"])),
        ("Tüm dosyalar (*.*)", ("Tüm dosyalar", ["*"])),
        ("Resimler (*.png;*.jpg)", ("Resimler", ["*.png", "*.PNG", "*.jpg", "*.JPG"])),
    ],
    ids=["pdf", "xlsx", "yedek", "tum_dosyalar", "coklu"],
)
def test_pywebview_suzgeci_parcalarina_ayrilir(suzgec: str, beklenen: Any) -> None:
    assert suzgec_parcalari(suzgec) == beklenen


def test_zenity_kaydetme_argumanlari_surum_3te_uzerine_yazmayi_sorar() -> None:
    """zenity 3.32/3.44 (Debian 11/12): soru yalnız `--confirm-overwrite` ile açılır."""
    argv = zenity_argv(
        "/usr/bin/zenity",
        kaydet=True,
        baslik="Farklı kaydet",
        klasor="/media/uydurma/USB BELLEK",
        ad="oab-defteri-yedek.odbak",
        suzgecler=("OAB Defteri yedeği (*.odbak)",),
        ana_surum=3,
    )

    assert argv == [
        "/usr/bin/zenity",
        "--file-selection",
        "--title=Farklı kaydet",
        "--save",
        "--filename=/media/uydurma/USB BELLEK/oab-defteri-yedek.odbak",
        "--confirm-overwrite",
        "--file-filter=OAB Defteri yedeği | *.odbak *.ODBAK",
    ]


def test_zenity_4te_kaldirilacak_secenek_verilmez() -> None:
    """zenity 4.1.90 (Debian 13, Pardus 25): "DEPRECATED; does nothing"; GTK4 soruyu kendisi sorar."""
    argv = zenity_argv(
        "zenity",
        kaydet=True,
        baslik="Farklı kaydet",
        klasor="/home/uydurma",
        ad="a.pdf",
        suzgecler=(),
        ana_surum=4,
    )

    assert "--confirm-overwrite" not in argv


def test_zenity_surumu_okunamazsa_soru_secenegi_verilir() -> None:
    """Tanınmazsa pencere 255'le düşer ve Qt penceresine geçilir; o da sorar (modül başlığı)."""
    argv = zenity_argv(
        "zenity", kaydet=True, baslik="B", klasor="/k", ad="a.pdf", suzgecler=(), ana_surum=None
    )

    assert "--confirm-overwrite" in argv


def test_zenity_ac_penceresi_klasorde_acilir_attach_kullanilmaz() -> None:
    argv = zenity_argv(
        "zenity",
        kaydet=False,
        baslik="Dosya aç",
        klasor="/media/uydurma/USB",
        ad="",
        suzgecler=("OAB Defteri yedeği (*.odbak)",),
        ana_surum=3,
    )

    assert argv == [
        "zenity",
        "--file-selection",
        "--title=Dosya aç",
        "--filename=/media/uydurma/USB/",
        "--file-filter=OAB Defteri yedeği | *.odbak *.ODBAK",
    ]
    assert not [parca for parca in argv if parca.startswith(("--attach", "--save", "--confirm"))]


def test_kdialog_argumanlari_belgelenen_bicimdedir() -> None:
    kaydet = kdialog_argv(
        "/usr/bin/kdialog",
        kaydet=True,
        baslik="Farklı kaydet",
        klasor="/home/uydurma",
        ad="Rapor.xlsx",
        suzgecler=("Excel dosyası (*.xlsx)",),
    )
    ac = kdialog_argv(
        "/usr/bin/kdialog",
        kaydet=False,
        baslik="Dosya aç",
        klasor="/home/uydurma",
        ad="",
        suzgecler=("OAB Defteri yedeği (*.odbak)",),
    )

    assert kaydet == [
        "/usr/bin/kdialog",
        "--title",
        "Farklı kaydet",
        "--getsavefilename",
        "/home/uydurma/Rapor.xlsx",
        "*.xlsx *.XLSX|Excel dosyası",
    ]
    assert ac == [
        "/usr/bin/kdialog",
        "--title",
        "Dosya aç",
        "--getopenfilename",
        "/home/uydurma/",
        "*.odbak *.ODBAK|OAB Defteri yedeği",
    ]


# --------------------------------------------------------------- dönüş kodları


def test_secilen_yol_dondurulur_satir_sonu_atilir() -> None:
    baslatici = _Baslatici(_SahteSurec(0, "/media/uydurma/USB/Rapor şubat.pdf\n".encode()))

    assert _kaydet(_pencere(baslatici, "zenity")) == "/media/uydurma/USB/Rapor şubat.pdf"


def test_yolun_sonundaki_bosluk_korunur() -> None:
    baslatici = _Baslatici(_SahteSurec(0, b"/home/uydurma/rapor .pdf \n"))

    assert _kaydet(_pencere(baslatici, "zenity")) == "/home/uydurma/rapor .pdf "


def test_utf8_olmayan_ad_kayipsiz_cozulur() -> None:
    """Dosya sistemi adı bayttır: `os.fsdecode` geri dönüşü kayıpsız tutar."""
    import os

    ham = b"/home/uydurma/eski-\xfd.pdf"
    baslatici = _Baslatici(_SahteSurec(0, ham + b"\n"))

    assert os.fsencode(_kaydet(_pencere(baslatici, "zenity")) or "") == ham


@pytest.mark.parametrize("arac", ["zenity", "kdialog"])
def test_iptal_bos_metin_doner_qtye_dusulmez(arac: str) -> None:
    baslatici = _Baslatici(_SahteSurec(1))

    assert _kaydet(_pencere(baslatici, arac)) == ""
    assert len(baslatici.cagrilar) == 1


def test_bos_secim_iptal_sayilir() -> None:
    assert _kaydet(_pencere(_Baslatici(_SahteSurec(0, b"")), "zenity")) == ""


@pytest.mark.parametrize(
    "kod", [255, 127, 5, -11], ids=["tanimsiz_secenek", "cokme", "sure", "sinyal"]
)
def test_beklenmeyen_kodda_kdialoga_sonra_qtye_dusulur(kod: int) -> None:
    baslatici = _Baslatici(_SahteSurec(kod), _SahteSurec(kod))

    assert _kaydet(_pencere(baslatici, "zenity", "kdialog")) is None
    assert [argv[0] for argv, _ in baslatici.cagrilar] == ["/usr/bin/zenity", "/usr/bin/kdialog"]


def test_zenity_coker_kdialog_secerse_kdialogun_secimi_doner() -> None:
    baslatici = _Baslatici(_SahteSurec(127), _SahteSurec(0, b"/home/uydurma/a.pdf\n"))

    assert _kaydet(_pencere(baslatici, "zenity", "kdialog")) == "/home/uydurma/a.pdf"


def test_zenity_yoksa_kdialog_kullanilir() -> None:
    baslatici = _Baslatici(_SahteSurec(0, b"/home/uydurma/a.pdf\n"))

    assert _kaydet(_pencere(baslatici, "kdialog")) == "/home/uydurma/a.pdf"
    assert baslatici.cagrilar[0][0][0] == "/usr/bin/kdialog"


def test_ikisi_de_yoksa_qtye_dusulur() -> None:
    baslatici = _Baslatici()

    assert _kaydet(_pencere(baslatici)) is None
    assert baslatici.cagrilar == []


def test_baslatilamazsa_qtye_dusulur(od_gunlugu: list[Any]) -> None:
    baslatici = _Baslatici(PermissionError("izin yok"))

    assert _kaydet(_pencere(baslatici, "zenity")) is None
    assert "PermissionError" in " ".join(kayit.getMessage() for kayit in od_gunlugu)


def test_secilen_yol_gunluge_yazilmaz(od_gunlugu: list[Any]) -> None:
    baslatici = _Baslatici(_SahteSurec(255), _SahteSurec(0, b"/home/Uydurgul/gizli.pdf\n"))

    _kaydet(_pencere(baslatici, "zenity", "kdialog"))

    metin = " ".join(kayit.getMessage() for kayit in od_gunlugu)
    assert "Uydurgul" not in metin and "gizli" not in metin


# ----------------------------------------------------------- ortam ve sürüm


def test_pencere_temiz_ortamla_acilir(monkeypatch: pytest.MonkeyPatch) -> None:
    """K-P2: paketin `LD_LIBRARY_PATH`'iyle zenity çöker; süreç `temiz_ortam()` ile başlar."""
    monkeypatch.setattr(yerel_pencere, "temiz_ortam", lambda: {"TEMIZ": "1"})
    baslatici = _Baslatici(_SahteSurec(1))

    _kaydet(_pencere(baslatici, "zenity"))

    ((_, anahtarlar),) = baslatici.cagrilar
    # zenity'de GTK4'ün masaüstü portalı da kapatılır (N-1, K-yeni-2; modül başlığı "Portal").
    assert anahtarlar["env"] == {"TEMIZ": "1", "GDK_DEBUG": "no-portals"}
    assert anahtarlar["stdout"] is subprocess.PIPE
    assert anahtarlar["stdin"] is subprocess.DEVNULL


def test_kdialogun_ortamina_portal_degiskeni_eklenmez(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(yerel_pencere, "temiz_ortam", lambda: {"TEMIZ": "1"})
    baslatici = _Baslatici(_SahteSurec(1))

    _kaydet(_pencere(baslatici, "kdialog"))

    ((_, anahtarlar),) = baslatici.cagrilar
    assert anahtarlar["env"] == {"TEMIZ": "1"}


@pytest.mark.parametrize(
    ("onceki", "beklenen"),
    [
        (None, "no-portals"),
        ("", "no-portals"),
        ("misc", "misc,no-portals"),
        ("no-portals", "no-portals"),
        ("misc,no-portals,", "misc,no-portals,"),
    ],
    ids=["yok", "bos", "baska_deger", "zaten_var", "zaten_var_dokunulmaz"],
)
def test_zenity_ortaminda_portal_kapanir_kullanicinin_degerleri_korunur(
    onceki: str | None, beklenen: str
) -> None:
    """Pardus 25'te (debian:13 kabında portal + xfwm4 ile ölçüldü) zenity 4 kaydetme penceresini
    `xdg-desktop-portal-gtk`'ya çizdiriyor, klasör kayboluyordu (N-1); pencere de portalın
    sürecinde olduğu için ana pencereye bağlanamıyordu (K-yeni-2)."""
    ortam = {"LANG": "tr_TR.UTF-8"}
    if onceki is not None:
        ortam["GDK_DEBUG"] = onceki

    zenity_ortami(ortam)

    assert ortam == {"LANG": "tr_TR.UTF-8", "GDK_DEBUG": beklenen}


def test_windowsta_ortam_none_kalir_portal_degiskeni_eklenmez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(yerel_pencere, "temiz_ortam", lambda: None)
    baslatici = _Baslatici(_SahteSurec(1))

    _kaydet(_pencere(baslatici, "zenity"))

    assert baslatici.cagrilar[0][1]["env"] is None


def test_son_klasor_kaydetmede_tam_yolla_verilir_portal_yolu_degismez() -> None:
    """N-1: klasör zenity'ye yine `--filename=<klasör>/<ad>` ile gider; klasörü zenity 4.1.90'da
    `gtk_file_chooser_set_file` kurar, portal kapalıyken uyar (debian:13 kabında ekran görüntüsüyle)."""
    argv = zenity_argv(
        "zenity",
        kaydet=True,
        baslik="Farklı kaydet",
        klasor="/media/uydurma/USB/Yedekler",
        ad="Rapor_07.11.2026.pdf",
        suzgecler=(),
        ana_surum=4,
    )

    assert "--filename=/media/uydurma/USB/Yedekler/Rapor_07.11.2026.pdf" in argv


# ------------------------------------------------- ana pencereye bağlama (K-yeni-2)


class _SahteBaglayici:
    def __init__(self) -> None:
        self.izlenen: list[tuple[int, bool]] = []
        self.birakilan: list[int] = []
        self.one_getirme = 0

    def izle(self, pid: int, suruyor: Any) -> None:
        self.izlenen.append((pid, suruyor()))

    def birak(self, pid: int) -> None:
        self.birakilan.append(pid)

    def one_getir(self) -> bool:
        self.one_getirme += 1
        return True


def _bagli_pencere(baslatici: _Baslatici, baglayici: _SahteBaglayici) -> YerelDosyaPenceresi:
    return YerelDosyaPenceresi(
        bul=_bulucu("zenity"), baslat=cast(Any, baslatici), baglayici=cast(Any, baglayici)
    )


def test_acilan_pencere_baglayiciya_verilir_kapaninca_birakilir() -> None:
    baglayici = _SahteBaglayici()
    pencere = _bagli_pencere(_Baslatici(_SahteSurec(0, b"/a.pdf\n")), baglayici)

    assert _kaydet(pencere) == "/a.pdf"

    # Süreç açıkken izlenir (`poll` henüz `None`), biter bitmez bırakılır.
    assert baglayici.izlenen == [(4242, True)]
    assert baglayici.birakilan == [4242]


def test_baglama_is_parcacigi_baslamasa_da_pencere_sonucu_doner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bağımsız denetim 14.11.2026: `izle` iş parçacığını başlatamazsa (`RuntimeError`) hata pencereye
    taşmaz; süreç beklenir, sonucu döner, açık süreçlerden çıkarılır (zenity yetim kalmaz)."""
    from desktop.x11_pencere import DisPencereBaglayici

    baglayici = DisPencereBaglayici(x11_yukle=lambda: cast(Any, object()))
    baglayici.ana_pencere(0x400007)

    def baslamaz(_self: threading.Thread) -> None:
        raise RuntimeError("can't start new thread")

    monkeypatch.setattr(threading.Thread, "start", baslamaz)
    pencere = YerelDosyaPenceresi(
        bul=_bulucu("zenity"),
        baslat=cast(Any, _Baslatici(_SahteSurec(0, b"/a.pdf\n"))),
        baglayici=baglayici,
    )

    assert _kaydet(pencere) == "/a.pdf"
    assert pencere._surecler == set()


def test_one_getir_baglayiciya_gider() -> None:
    baglayici = _SahteBaglayici()
    pencere = _bagli_pencere(_Baslatici(), baglayici)

    pencere.one_getir()

    assert baglayici.one_getirme == 1


def test_baglayicisiz_pencere_one_getirmede_bir_sey_yapmaz() -> None:
    _pencere(_Baslatici(), "zenity").one_getir()


@pytest.mark.parametrize(
    ("surum", "soru_var"),
    [(b"3.32.0\n", True), (b"3.44.0\n", True), (b"4.1.90\n", False), (b"bozuk", True)],
    ids=["debian11", "debian12", "debian13", "okunamaz"],
)
def test_uzerine_yazma_sorusu_kurulu_zenitynin_surumune_gore(surum: bytes, soru_var: bool) -> None:
    baslatici = _Baslatici(_SahteSurec(1), _SahteSurec(1), surum=surum)
    pencere = _pencere(baslatici, "zenity")

    _kaydet(pencere)
    _kaydet(pencere)

    assert ("--confirm-overwrite" in baslatici.cagrilar[0][0]) is soru_var
    assert baslatici.surum_sorulari == 1  # süreç başına bir kez


# --------------------------------------------------------------------- kapanış


def test_kapanista_acik_pencere_sonlandirilir_iptal_sayilir() -> None:
    """Köprünün iş parçacığı gündelik iş parçacığıdır: açık pencere süreci ayakta tutmasın."""
    bekle = threading.Event()
    surec = _SahteSurec(0, b"/home/uydurma/a.pdf\n", bekle=bekle)
    pencere = _pencere(_Baslatici(surec), "zenity")
    sonuc: list[str | None] = []
    is_parcacigi = threading.Thread(target=lambda: sonuc.append(_kaydet(pencere)))
    is_parcacigi.start()
    for _ in range(100):
        if pencere._surecler:
            break
        threading.Event().wait(0.01)

    pencere.kapat()
    is_parcacigi.join(5)

    assert surec.sonlandirildi is True
    assert sonuc == [""]


def test_kapandiktan_sonra_pencere_acilmaz() -> None:
    baslatici = _Baslatici(_SahteSurec(0, b"/a.pdf\n"))
    pencere = _pencere(baslatici, "zenity")

    pencere.kapat()

    assert _kaydet(pencere) == ""
    assert baslatici.cagrilar == []


def test_tek_arac_kdialogken_kapanista_sonlandirilan_pencere_iptal_sayilir() -> None:
    """Bağımsız denetimin M13'ü (13.11.2026): sonlandırılan kdialog -15 döner; kapanış denetimi
    olmasa `None` dönüp kapanmakta olan programda Qt penceresi açılmaya kalkardı."""
    bekle = threading.Event()
    surec = _SahteSurec(0, b"/home/uydurma/a.pdf\n", bekle=bekle)
    pencere = _pencere(_Baslatici(surec), "kdialog")
    sonuc: list[str | None] = []
    is_parcacigi = threading.Thread(target=lambda: sonuc.append(_kaydet(pencere)))
    is_parcacigi.start()
    for _ in range(100):
        if pencere._surecler:
            break
        threading.Event().wait(0.01)

    pencere.kapat()
    is_parcacigi.join(5)

    assert surec.sonlandirildi is True
    assert sonuc == [""]


# ------------------------------------------------------- sayfanın dosya kutusu


class _Kip:
    FileSelectOpen = "tek"
    FileSelectOpenMultiple = "coklu"


class _Taban:
    """Qt'nin varsayılan `chooseFiles`'ı."""

    def __init__(self) -> None:
        self.cagrilar: list[tuple[Any, ...]] = []

    def __call__(self, sayfa: Any, kip: Any, eski: Any, kabul: Any) -> list[str]:
        self.cagrilar.append((sayfa, kip, eski, kabul))
        return ["/qt/secimi.xlsx"]


def _esanli(is_: Any) -> tuple[bool, Any]:
    return True, is_()


def _isleyici(sec: Any, taban: _Taban, bekle: Any = _esanli) -> Any:
    return yukleme_isleyicisi(sec, taban=taban, tek_secim=_Kip.FileSelectOpen, bekle=bekle)


def test_tek_dosyalik_kutu_masaustu_penceresine_gider() -> None:
    sorulan: list[list[str]] = []
    taban = _Taban()

    def sec(kabul: list[str]) -> list[str]:
        sorulan.append(kabul)
        return ["/media/uydurma/USB/personel.XLS"]

    yollar = _isleyici(sec, taban)("sayfa", _Kip.FileSelectOpen, [], [".xls", "text/csv"])

    assert yollar == ["/media/uydurma/USB/personel.XLS"]
    assert sorulan == [[".xls", "text/csv"]]
    assert taban.cagrilar == []


def test_masaustu_penceresi_acilamazsa_qtnin_varsayilani_acilir() -> None:
    taban = _Taban()

    yollar = _isleyici(lambda kabul: None, taban)("sayfa", _Kip.FileSelectOpen, ["e"], [".xls"])

    assert yollar == ["/qt/secimi.xlsx"]
    assert taban.cagrilar == [("sayfa", _Kip.FileSelectOpen, ["e"], [".xls"])]


def test_kutuda_iptal_bos_listedir() -> None:
    taban = _Taban()

    assert _isleyici(lambda kabul: [], taban)("sayfa", _Kip.FileSelectOpen, [], []) == []
    assert taban.cagrilar == []


def test_bekleme_bitmezse_kutu_iptal_sayilir() -> None:
    """Hata ya da program kapanışı: Qt penceresi açılmaz, boş liste döner."""
    taban = _Taban()
    isleyici = _isleyici(lambda kabul: ["/a"], taban, bekle=lambda is_: (False, None))

    assert isleyici("sayfa", _Kip.FileSelectOpen, [], []) == []
    assert taban.cagrilar == []


def test_baska_kipler_qtde_kalir() -> None:
    taban = _Taban()

    yollar = _isleyici(pytest.fail, taban)("sayfa", _Kip.FileSelectOpenMultiple, [], [])

    assert yollar == ["/qt/secimi.xlsx"]


class _Zamanlayici:
    def __init__(self) -> None:
        self.geri_cagrilar: list[Any] = []
        self.timeout = SimpleNamespace(connect=self.geri_cagrilar.append)
        self.aralik: int | None = None
        self.durdu = False

    def start(self, aralik: int) -> None:
        self.aralik = aralik

    def stop(self) -> None:
        self.durdu = True


class _QtCekirdegi:
    """`QtCore`'un `QEventLoop` ve `QTimer`'ı: döngü zamanlayıcıyı `quit`'e dek döndürür."""

    def __init__(self, *, erken_cik: bool = False) -> None:
        self.erken_cik = erken_cik
        self.zamanlayicilar: list[_Zamanlayici] = []
        self.donguler = 0
        self.dongu_is_parcacigi: list[str] = []

    def QTimer(self) -> _Zamanlayici:  # noqa: N802 — Qt adı
        self.zamanlayicilar.append(_Zamanlayici())
        return self.zamanlayicilar[-1]

    def QEventLoop(self) -> Any:  # noqa: N802 — Qt adı
        cekirdek = self

        class _Dongu:
            def __init__(self) -> None:
                self.cikti = False

            def quit(self) -> None:
                self.cikti = True

            def exec(self) -> int:
                cekirdek.donguler += 1
                cekirdek.dongu_is_parcacigi.append(threading.current_thread().name)
                if cekirdek.erken_cik:
                    return 0  # Qt'nin çıkışı bütün döngüleri bitirir
                for _ in range(500):
                    for geri_cagri in cekirdek.zamanlayicilar[-1].geri_cagrilar:
                        geri_cagri()
                    if self.cikti:
                        return 0
                    threading.Event().wait(0.01)
                raise AssertionError("döngü bitmedi")

        return _Dongu()


def test_bekleyici_isi_ayri_is_parcaciginda_dongu_ana_is_parcaciginda_doner() -> None:
    cekirdek = _QtCekirdegi()
    birak = threading.Event()
    is_parcacigi: list[str] = []

    def is_() -> str:
        is_parcacigi.append(threading.current_thread().name)
        birak.wait(5)
        return "/media/uydurma/USB/veli.xlsx"

    threading.Timer(0.05, birak.set).start()
    sonuc = qt_dongusunde_bekleyici(cekirdek)(is_)

    assert sonuc == (True, "/media/uydurma/USB/veli.xlsx")
    assert cekirdek.donguler == 1
    assert cekirdek.dongu_is_parcacigi == [threading.current_thread().name]
    assert is_parcacigi == ["od-dosya-kutusu"]
    assert cekirdek.zamanlayicilar[0].aralik == yerel_pencere.BEKLEME_ARALIGI_MS
    assert cekirdek.zamanlayicilar[0].durdu is True


def test_bekleyici_isin_none_donusunu_iletir() -> None:
    """`None` masaüstü penceresinin açılamadığıdır (Qt'ye düşülür), iptal değildir."""
    assert qt_dongusunde_bekleyici(_QtCekirdegi())(lambda: None) == (True, None)


def test_bekleyicide_is_hatasi_iptal_sayilir(od_gunlugu: list[Any]) -> None:
    def patla() -> str:
        raise RuntimeError("/home/Uydurgul/gizli.xlsx")

    assert qt_dongusunde_bekleyici(_QtCekirdegi())(patla) == (False, None)
    metin = " ".join(kayit.getMessage() for kayit in od_gunlugu)
    assert "RuntimeError" in metin and "Uydurgul" not in metin


def test_program_kapanirken_dongu_biterse_kutu_iptal_sayilir() -> None:
    birak = threading.Event()
    cekirdek = _QtCekirdegi(erken_cik=True)

    try:
        sonuc = qt_dongusunde_bekleyici(cekirdek)(lambda: birak.wait(5) and ["/a"])
    finally:
        birak.set()

    assert sonuc == (False, None)
    assert cekirdek.zamanlayicilar[0].durdu is True


def test_dosya_kutusu_sayfa_sinifina_baglanir() -> None:
    class _Sayfa:
        pass

    class _QWebPage:
        FileSelectionMode = _Kip

        @staticmethod
        def chooseFiles(*_a: Any) -> list[str]:  # noqa: N802 — Qt adı
            return ["/qt"]

    arka_uc = SimpleNamespace(
        QWebPage=_QWebPage, BrowserView=SimpleNamespace(WebPage=_Sayfa), QtCore=_QtCekirdegi()
    )

    yukleme_penceresini_bagla(arka_uc, lambda kabul: ["/media/uydurma/USB/a.xlsx"])

    sayfa: Any = _Sayfa()
    assert sayfa.chooseFiles(_Kip.FileSelectOpen, [], [".xlsx"]) == ["/media/uydurma/USB/a.xlsx"]
    assert sayfa.chooseFiles(_Kip.FileSelectOpenMultiple, [], []) == ["/qt"]
