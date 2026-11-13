"""Linux paketine GÖMÜLMEYEN, hedef sistemden alınan kütüphaneler (TEK kaynak).

SAHA BULGUSU (Pardus 25.2 = Debian 13, XFCE + x11, Intel HD 4600, Mesa 25.0.7;
12.11.2026, paket 9b35c17): program pencere açılmadan "qt.glx: qglx_findConfig: Failed
to finding matching FBConfig … Could not initialize GLX" ile çöktü. Kurulum, `--autotest`
ve üç duman kipi geçiyordu; hiçbiri pencere açmaz.

KÖK NEDEN: paket bilerek `python:3.12-bullseye`'da derlenir (glibc 2.31 = Pardus 21
tabanı; `docker-build.sh`). PyInstaller ikili bağımlılık çözümlemesinde bullseye'ın
`libstdc++.so.6`, `libgbm.so.1`, `libexpat.so.1`, `libz.so.1`, `libzstd.so.1` … kopyalarını
`_internal`'a gömer; çalışma anında önyükleyici `_internal`'ı kitaplık arama yoluna
koyar. Grafik sürücüsü (Mesa) ise SİSTEMDEN yüklenir ve aynı adlı (SONAME) kütüphaneleri
sürecin önceden yüklediği gömülü kopyalardan alır. Mesa 25'in sürücüsü (`libgallium`,
`libLLVM-19`, `libz3`) GLIBCXX_3.4.29-3.4.32 ve CXXABI_1.3.13-1.3.15 ister, bullseye'ın
gcc-10 `libstdc++`'ı 3.4.28'de kalır; `libEGL_mesa` bullseye'ın Mesa 20.3 `libgbm`'inde
olmayan `gbm_bo_create_with_modifiers2`'yi, Wayland oturumunda Wayland 1.18'de olmayan
`wl_proxy_marshal_flags` (1.20) ve `wl_display_create_queue_with_name` (1.23) işlevlerini
ister. Kanıt: temiz debian:13 kabında Mesa sürücüleri `LD_LIBRARY_PATH=<_internal> ldd -r`
ile bu satırları verir (12.11.2026). Sahada sistemin libstdc++ + libgbm + libexpat + libz +
libzstd'si birlikte öne alınınca (LD_PRELOAD) pencere tam çizildi.

KURAL: sürecin İÇİNE sistemden yüklenen grafik sürücüsüyle paylaşılan kütüphaneler pakete
girmez; hedef sistemin (sürücüyle aynı yaştaki) kopyası kullanılır. Hepsi SONAME sürümünü
korur ve geriye uyumludur: Pardus 21'de (Debian 11) sistemdeki kopya gömülenle AYNI
sürümdür, Pardus 23/25'te daha yenidir. Her öğenin Debian paketi `.deb` Depends'ine girer
(`build.sh`, ad Debian 11, 12 ve 13'te aynı — `apt-cache show` ile 12.11.2026'da
denetlendi; 64 bit zaman geçişinde adı değişen paket yoktur).

BİLİNÇLİ OLARAK DIŞLANMAYANLAR (aşırıya kaçmamak için):

* libX11/xcb ailesinin geneli (`libX11`, `libXext`, `libXau`, `libXdmcp`,
  `libxcb-randr/shm/xfixes/render/shape/xkb/icccm/image/keysyms/render-util/cursor/util` …):
  Qt'nin xcb eklentisi ve QtWebEngine bunlara bağlanır. Sahada bunlar gömülüyken pencere
  çizildi; debian:13'te Mesa 25 sürücüleri `ldd -r` ile gömülü bullseye kopyalarında eksik
  sembol bulmadı. X protokol bağlayıcıları yalnız ekleme yaparak büyür (SONAME 1.x'ten beri
  aynı). Yalnız sürücünün X sunucusuyla DRI/GLX bağını kuran parçalar (aşağıda) sistemden
  alınır: onlar sürücüyle birlikte gelir ve sürücüyle birlikte değişir.
* `libssl.so.1.1`, `libcrypto.so.1.1`, `libffi.so.7`: Python'un kendi bağımlılıklarıdır,
  grafik yığınıyla SONAME paylaşmazlar (Debian 13 Mesa'sı `libffi.so.8` ister) ve Pardus 25'te
  `libssl1.1` yoktur — gömülü kalmak ZORUNDADIR.
* `liblzma.so.5`, `libbsd.so.0`, `libmd.so.0`: sürücünün dolaylı bağımlılıklarıdır ama
  `ldd -r` debian:13'te gömülü kopyalarda eksik sembol bulmadı; grafik yığınına özgü değiller.
* `libatomic.so.1`: GCC çalışma kitaplığıdır ama Mesa ona bağlanmaz (debian:13 `ldd`).
* PyInstaller'ın paketlediği, adı karma ekli kopyalar (`libzstd-44be1190.so.1.5.7`,
  `libxcb-ad31f5a3.so.1.1.0` …): tekerleklerin auditwheel ile yeniden adlandırdığı özel
  kopyalardır, SONAME'leri farklıdır, sistemdekiyle çakışmaz; desenler bunları eşlemez.

PyInstaller 6.11.1'in kendi varsayılan dışlama listesiyle (`PyInstaller/depend/dylib.py`,
`_unix_excludes`) ÇAKIŞANLAR: glvnd ailesi (`libE?(Open)?GLX?(ESv1_CM|ESv2)?(dispatch)?\\.so`),
`libdrm\\.so` ve `libxcb-dri.*\\.so` (ayrıca `libxcb\\.so` — bu listede yok, zaten gömülmez).
Bunlar burada YİNE sayılır: Depends'e ve derleme sonrası denetime girsinler, PyInstaller
sürümü değişip listesini daraltırsa kural bizde kalsın.

Kullanım (yalnız standart kitaplık):
    spec (yalnız Linux, Analysis'ten SONRA):  `sistemden_suz(a.binaries)`
    build.sh Depends eki:                      `python sistem_kutuphaneleri.py depends`
    build.sh derleme sonrası denetim:          `python sistem_kutuphaneleri.py denetle --paket DIZIN`
    kurulum provası (sistem_denetimi.sh):      `SISTEMDEN_ERE` (eşitliği kapı testi sınar —
                                               packaging/tests/test_sistem_kutuphaneleri.py)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class SistemKutuphanesi:
    """Pakete gömülmeyen, hedef sistemden alınan bir kütüphane (ya da aile)."""

    #: Dosya adının (SONAME) deseni; Python `re` ile POSIX ERE'nin ORTAK alt kümesiyle
    #: yazılır (`\\d` yok), çünkü aynı ifade kurulum provasında (sistem_denetimi.sh)
    #: `grep -E` ile koşar.
    desen: str
    #: Debian paketi (Debian 11, 12, 13'te aynı ad) → `.deb` Depends. None: Depends'e
    #: girmez; gerekçede hangi paketle geldiği yazar.
    paket: str | None
    gerekce: str


SISTEMDEN_ALINANLAR: tuple[SistemKutuphanesi, ...] = (
    # --- C++ çalışma kütüphanesi ---------------------------------------------------
    SistemKutuphanesi(
        r"libstdc\+\+\.so\.6",
        "libstdc++6",
        "Mesa 25 sürücüsü (libgallium, libLLVM-19, libz3) GLIBCXX_3.4.29-3.4.32 ve "
        "CXXABI_1.3.13-1.3.15 ister; bullseye'ın gcc-10 kopyası GLIBCXX_3.4.28'de kalır. "
        "Sürece yüklenen her sistem C++ kitaplığı en yeni libstdc++'ı bekler.",
    ),
    SistemKutuphanesi(
        r"libgcc_s\.so\.1",
        "libgcc-s1",
        "libstdc++ ile aynı GCC derlemesinden gelir (istisna yayılımı, unwinder); Debian'da "
        "libstdc++6 aynı sürümde libgcc-s1'e bağlıdır. Yeni libstdc++ eski libgcc_s ile "
        "eşlenmez.",
    ),
    # --- Mesa: GBM, DRM, glvnd, sürücü kitaplıkları --------------------------------
    SistemKutuphanesi(
        r"libgbm\.so\.1",
        "libgbm1",
        "Mesa'nın kendi parçasıdır, sürücüyle aynı sürümde olmalı: libEGL_mesa (Mesa 25) "
        "bullseye'ın 20.3.5 kopyasında olmayan gbm_bo_create_with_modifiers2'yi ister; "
        "arka ucu (gbm/dri_gbm.so) sürücüyle gelir. QtWebEngine'in istediği "
        "gbm_bo_get_fd_for_plane için Debian 11'in libgbm1'i yeterlidir (PySide6 6.8.x tavanı, "
        "requirements-paketleme.txt).",
    ),
    SistemKutuphanesi(
        r"libdrm\.so\.2",
        "libdrm2",
        "Çekirdek DRM arayüzü, sürücüyle aynı yaşta olmalı. PyInstaller varsayılanı da dışlar.",
    ),
    SistemKutuphanesi(
        r"libdrm_[a-z0-9]+\.so\.[0-9]+",
        None,
        "Donanıma özgü DRM yardımcıları (intel, amdgpu, nouveau, radeon …) yalnız sürücü "
        "yükler; sürücü paketiyle (libgl1-mesa-dri) gelir, programın hiçbir dosyası bunlara "
        "bağlanmaz.",
    ),
    SistemKutuphanesi(
        r"libglapi\.so\.0",
        None,
        "Mesa'nın GL dağıtım tablosu; Debian 11/12'de libglapi-mesa sürücüyle gelir, Debian "
        "13'te (Mesa 25) ayrı paket yoktur. Depends'e adı yazılamaz.",
    ),
    SistemKutuphanesi(
        r"lib(E?(Open)?GLX?(ESv1_CM|ESv2)?(dispatch)?)\.so\.[0-9]+",
        None,
        "glvnd yükleyicisi (libGL, libEGL, libGLX, libOpenGL, libGLESv2, libGLdispatch): "
        "sürücü üreticisini çalışma anında seçer. PyInstaller varsayılanı da dışlar; libgl1 ve "
        "libegl1 Depends'tedir (build.sh DEPENDS_QT), ötekiler onların bağımlılığıyla gelir.",
    ),
    SistemKutuphanesi(
        r"lib(GLX|EGL)_mesa\.so\.0",
        None,
        "Mesa'nın glvnd üretici kitaplıkları; sürücünün kendisidir (libglx-mesa0, "
        "libegl-mesa0 — libgl1/libegl1 üzerinden gelir).",
    ),
    # --- Wayland -------------------------------------------------------------------
    SistemKutuphanesi(
        r"libwayland-client\.so\.0",
        "libwayland-client0",
        "libEGL_mesa (Mesa 25) Wayland 1.18'de (bullseye) olmayan wl_proxy_marshal_flags "
        "(1.20) ve wl_display_create_queue_with_name (1.23) işlevlerini ister; Wayland "
        "oturumunda (Pardus 25 GNOME) gömülü kopya sürücüyü kırar. YAN ETKİ (denetim bulgusu "
        "13.11.2026): Qt'nin Wayland platform eklentisi de wl_proxy_marshal_flags ister; gömülü "
        "kopyayla çalışamazdı, sistem kopyasıyla libwayland-cursor0 ve libwayland-egl1 kurulu "
        "her makinede eksiksiz bağlanır ve Wayland oturumunda Qt onu xcb'den önce yükler. "
        "Pencere yolu bu yüzden çalışma zamanı kancasında sınanmış xcb'ye sabitlenir "
        "(packaging/pyinstaller/rthook_od.py).",
    ),
    SistemKutuphanesi(
        r"libwayland-server\.so\.0",
        "libwayland-server0",
        "libgbm ve libEGL_mesa'nın bağımlılığıdır; client ile aynı kaynaktan (wayland) gelir, "
        "ikisi aynı sürümde kalmalı.",
    ),
    # --- X sunucusu ile sürücü arasındaki DRI/GLX bağı ------------------------------
    SistemKutuphanesi(
        r"libX11-xcb\.so\.1",
        "libx11-xcb1",
        "Sürücünün Xlib bağlantısından xcb bağlantısını aldığı köprü (GLX/EGL x11).",
    ),
    SistemKutuphanesi(
        r"libxcb-glx\.so\.0",
        "libxcb-glx0",
        "GLX protokolü; yalnız libGLX_mesa kullanır (saha hatası GLX yolunda).",
    ),
    SistemKutuphanesi(
        r"libxcb-present\.so\.0",
        "libxcb-present0",
        "DRI3/Present ekran sunumu; sürücü kullanır.",
    ),
    SistemKutuphanesi(
        r"libxcb-sync\.so\.1",
        "libxcb-sync1",
        "Sürücünün X sunucusuyla çizim eşitlemesi (DRI3 fence).",
    ),
    SistemKutuphanesi(
        r"libxcb-dri2\.so\.0",
        "libxcb-dri2-0",
        "DRI2 protokolü; PyInstaller varsayılanı da dışlar (ABI'si sık değişir).",
    ),
    SistemKutuphanesi(
        r"libxcb-dri3\.so\.0",
        "libxcb-dri3-0",
        "DRI3 protokolü; PyInstaller varsayılanı da dışlar (ABI'si sık değişir).",
    ),
    SistemKutuphanesi(
        r"libxshmfence\.so\.1",
        "libxshmfence1",
        "Sürücü ile X sunucusu arasında paylaşımlı bellek çiti (DRI3).",
    ),
    # --- Sürücünün süreçle paylaştığı sıkıştırma ve XML kitaplıkları ---------------
    SistemKutuphanesi(
        r"libexpat\.so\.1",
        "libexpat1",
        "Mesa sürücü yapılandırmasını (driconf XML) expat ile okur; saha deneyinde (12.11.2026) "
        "pencere ancak sistemin libexpat'ı da öne alınınca çizildi.",
    ),
    SistemKutuphanesi(
        r"libz\.so\.1",
        "zlib1g",
        "Sürücü, libLLVM ve libelf zlib'e bağlanır; saha deneyinde gerekli kümenin parçası.",
    ),
    SistemKutuphanesi(
        r"libzstd\.so\.1",
        "libzstd1",
        "Sürücünün gölgelendirici önbelleği ve libLLVM/libelf zstd'ye bağlanır; saha "
        "deneyinde gerekli kümenin parçası.",
    ),
)

#: Bütün desenler tek ifadede; dosya adının TAMAMI eşleşir, sondaki ek sürüm
#: (`libstdc++.so.6.0.28`) de kapsanır. sistem_denetimi.sh `SISTEMDEN_ERE` ile AYNI olmalı.
SISTEMDEN_ERE = "^(" + "|".join(k.desen for k in SISTEMDEN_ALINANLAR) + r")(\.[0-9]+)*$"
_DESEN = re.compile(SISTEMDEN_ERE)


def sistemden_mi(yol: str | os.PathLike[str]) -> bool:
    """Paket içi yol ya da dosya adı sistemden alınması gereken bir kütüphane mi?"""
    return _DESEN.match(PurePosixPath(str(yol).replace("\\", "/")).name) is not None


def sistemden_suz(
    toc: Sequence[tuple[str, str, str]],
) -> tuple[list[tuple[str, str, str]], list[str]]:
    """spec için (yalnız Linux): sistemden alınacak kütüphaneleri PyInstaller TOC'undan
    ayıklar → (kalan, atılan hedef adları)."""
    kalan: list[tuple[str, str, str]] = []
    atilan: list[str] = []
    for oge in toc:
        if sistemden_mi(oge[0]):
            atilan.append(oge[0])
        else:
            kalan.append(oge)
    return kalan, atilan


def depends_paketleri() -> list[str]:
    """`.deb` Depends'ine eklenecek Debian paketleri (sırası korunur, tekil)."""
    return list(dict.fromkeys(k.paket for k in SISTEMDEN_ALINANLAR if k.paket))


def paket_denetimi(paket_dizini: Path) -> list[str]:
    """Paketin DİSKTEKİ hâlinde sistemden alınması gereken kütüphane (dosya ya da sembolik
    bağ) kalmış mı? Kalan her biri hata satırıdır."""
    bulunan: list[str] = []
    for kok, _dizinler, dosyalar in os.walk(paket_dizini):
        for ad in dosyalar:
            if sistemden_mi(ad):
                bulunan.append((Path(kok) / ad).relative_to(paket_dizini).as_posix())
    return [
        f"sistemden alınması gereken kütüphane pakette: {yol} — spec `sistemden_suz` "
        "süzgeci (packaging/linux/sistem_kutuphaneleri.py)"
        for yol in sorted(bulunan)
    ]


def _yaz(metin: str) -> None:
    """Konsolun kodlayamadığı harfi kaçışa çevirerek yazar (lisanslar.yaz ile aynı)."""
    kodlama = getattr(sys.stdout, "encoding", None) or "utf-8"
    print(metin.encode(kodlama, "backslashreplace").decode(kodlama))


def main(argv: Sequence[str] | None = None) -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    alt = ayristirici.add_subparsers(dest="komut", required=True)
    alt.add_parser("depends", help="Depends'e eklenecek Debian paketlerini virgülle basar")
    denetle = alt.add_parser("denetle", help="paket dizininde sistemden alınacak kütüphane arar")
    denetle.add_argument("--paket", type=Path, required=True)
    args = ayristirici.parse_args(argv)

    if args.komut == "depends":
        print(", ".join(depends_paketleri()))
        return 0
    paket_dizini: Path = args.paket
    if not paket_dizini.is_dir():
        _yaz(f"HATA: paket dizini yok: {paket_dizini}")
        return 2
    hatalar = paket_denetimi(paket_dizini)
    if hatalar:
        _yaz("HATA: sistem kütüphanesi denetimi başarısız:")
        for hata in hatalar:
            _yaz(f"  - {hata}")
        return 1
    _yaz(
        f"Sistem kütüphanesi denetimi başarılı: {len(SISTEMDEN_ALINANLAR)} kuralın hiçbiri "
        "pakette dosya bulmadı."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
