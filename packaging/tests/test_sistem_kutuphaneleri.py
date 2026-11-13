"""Sistemden alınan kütüphaneler — Linux paketine gömülmez, `.deb` Depends'ine girer.

Saha bulgusu (Pardus 25.2 = Debian 13, Mesa 25.0.7; 12.11.2026, paket 9b35c17): paket
bullseye'da derlendiği için PyInstaller bullseye'ın libstdc++, libgbm, libexpat, zlib, zstd
kopyalarını gömüyordu; sistemden yüklenen Mesa 25 sürücüsü bunlara bağlanıp GLX'i açamadı
("Could not initialize GLX" → Aborted). Kurulum provası ekransız koştuğu için yakalamadı.

Kural TEK kaynaktadır (`packaging/linux/sistem_kutuphaneleri.py`); burada sabitlenenler:

* saha kümesi ve Mesa'nın DRI yolundaki kütüphaneler sistemden alınır; Python'un kendi
  bağımlılıkları (libssl1.1, libffi7), libX11/xcb ailesinin geneli ve auditwheel'in karma
  ekli özel kopyaları GÖMÜLÜ kalır;
* spec süzgeci yalnız Linux'ta, Analysis'ten SONRA uygulanır (Windows etkilenmez);
* `.deb` Depends'i, taşınabilir sürümün BENIOKU'su ve kurulum provası aynı listeyi kullanır;
  ERE ile Python `re` aynı adları eşler (sistem_denetimi.sh `grep -E` ile koşar).
"""

from __future__ import annotations

import ast
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
MODUL = REPO / "packaging" / "linux" / "sistem_kutuphaneleri.py"
SPEC = REPO / "packaging" / "pyinstaller" / "oab_defteri.spec"
BUILD_SH = REPO / "packaging" / "linux" / "build.sh"
KAP_ICI = REPO / "packaging" / "linux" / "kap-ici-test.sh"
DENETIM_SH = REPO / "packaging" / "linux" / "sistem_denetimi.sh"
BENIOKU = REPO / "packaging" / "linux" / "BENIOKU.txt"
BASH = shutil.which("bash") or "/bin/bash"


def _yukle() -> ModuleType:
    spec = importlib.util.spec_from_file_location("od_sistem_kutuphaneleri", MODUL)
    assert spec is not None and spec.loader is not None
    modul = importlib.util.module_from_spec(spec)
    sys.modules["od_sistem_kutuphaneleri"] = modul
    spec.loader.exec_module(modul)
    return modul


S: Any = _yukle()

#: Sistemden alınması gerekenler. İlk beşi saha deneyinin (LD_PRELOAD) pencereyi çizdiren
#: kümesidir; libgcc_s libstdc++ ile aynı GCC'den gelir; Wayland ikilisi debian:13'te
#: `ldd -r` ile eksik sembol verdi; ötekiler Mesa'nın DRI/GLX yolundadır ya da PyInstaller
#: varsayılanının da dışladığı grafik kütüphaneleridir.
SISTEMDEN = [
    "libstdc++.so.6",
    "libgbm.so.1",
    "libexpat.so.1",
    "libz.so.1",
    "libzstd.so.1",
    "libgcc_s.so.1",
    "libwayland-client.so.0",
    "libwayland-server.so.0",
    "libdrm.so.2",
    "libdrm_intel.so.1",
    "libdrm_amdgpu.so.1",
    "libglapi.so.0",
    "libGL.so.1",
    "libEGL.so.1",
    "libGLX.so.0",
    "libOpenGL.so.0",
    "libGLdispatch.so.0",
    "libGLESv2.so.2",
    "libGLX_mesa.so.0",
    "libEGL_mesa.so.0",
    "libX11-xcb.so.1",
    "libxcb-glx.so.0",
    "libxcb-present.so.0",
    "libxcb-sync.so.1",
    "libxcb-dri2.so.0",
    "libxcb-dri3.so.0",
    "libxshmfence.so.1",
    # Uzun sürüm eki ve paket içi yol da tanınır.
    "libstdc++.so.6.0.28",
    "PySide6/Qt/lib/libgbm.so.1",
    "_internal\\libz.so.1.2.11",
]

#: Gömülü KALMASI gerekenler (aşırıya kaçmama): Python'un bağımlılıkları (Pardus 25'te
#: libssl1.1 yok), libX11/xcb ailesinin geneli (Qt xcb eklentisi ve WebEngine bağlanır),
#: Qt'nin kendi kitaplıkları ve auditwheel'in karma ekli özel kopyaları.
GOMULU = [
    "libssl.so.1.1",
    "libcrypto.so.1.1",
    "libffi.so.7",
    "libpython3.12.so.1.0",
    "libX11.so.6",
    "libXext.so.6",
    "libXau.so.6",
    "libxcb-randr.so.0",
    "libxcb-shm.so.0",
    "libxcb-xfixes.so.0",
    "libxcb-cursor.so.0",
    "libxkbcommon.so.0",
    "liblzma.so.5",
    "libatomic.so.1",
    "libGLU.so.1",
    "libQt6Gui.so.6",
    "libQt6OpenGL.so.6",
    "libQt6EglFSDeviceIntegration.so.6",
    "libQt6WaylandClient.so.6",
    "libQt6WaylandEglClientHwIntegration.so.6",
    "libzstd-44be1190.so.1.5.7",
    "libxcb-ad31f5a3.so.1.1.0",
    "libz.so",
    "zlib.cpython-312-x86_64-linux-gnu.so",
    "libstdc++.so.6-gdb.py",
]

#: Debian paket adları — `apt-cache show` ile Debian 11 (bullseye), 12 (bookworm) ve 13
#: (trixie) kaplarında 12.11.2026'da AYNI adla bulundu (64 bit zaman geçişinde ad değişmedi).
#: `libglapi-mesa` Debian 13'te YOKTUR: listede bilinçli olarak paketsizdir.
DEBIAN_11_12_13_PAKETLER = [
    "libstdc++6",
    "libgcc-s1",
    "libgbm1",
    "libdrm2",
    "libwayland-client0",
    "libwayland-server0",
    "libx11-xcb1",
    "libxcb-glx0",
    "libxcb-present0",
    "libxcb-sync1",
    "libxcb-dri2-0",
    "libxcb-dri3-0",
    "libxshmfence1",
    "libexpat1",
    "zlib1g",
    "libzstd1",
]


# ------------------------------------------------------------------ kural


@pytest.mark.parametrize("ad", SISTEMDEN)
def test_mesa_ile_paylasilan_kutuphane_sistemden_alinir(ad: str) -> None:
    assert S.sistemden_mi(ad) is True


@pytest.mark.parametrize("ad", GOMULU)
def test_python_ve_qt_bagimliliklari_gomulu_kalir(ad: str) -> None:
    assert S.sistemden_mi(ad) is False


def test_her_kuralin_gerekcesi_var_ve_paketsizler_bilinen_kume() -> None:
    assert all(k.gerekce.strip() for k in S.SISTEMDEN_ALINANLAR)
    paketsiz = {k.desen for k in S.SISTEMDEN_ALINANLAR if k.paket is None}
    # Yalnız sürücüyle gelen, adı Debian sürümleri arasında tutarsız ya da donanıma özgü
    # kütüphaneler paketsizdir; gerekçeleri hangi paketle geldiğini söyler.
    assert paketsiz == {
        r"libdrm_[a-z0-9]+\.so\.[0-9]+",
        r"libglapi\.so\.0",
        r"lib(E?(Open)?GLX?(ESv1_CM|ESv2)?(dispatch)?)\.so\.[0-9]+",
        r"lib(GLX|EGL)_mesa\.so\.0",
    }
    # Desenler ERE ile ortak alt kümede: `\d`, `\w`, `(?` yok (sistem_denetimi.sh grep -E).
    for k in S.SISTEMDEN_ALINANLAR:
        assert not re.search(r"\\[dwsb]|\(\?", k.desen), k.desen


def test_depends_paketleri_elle_denetlenen_listeyle_ayni() -> None:
    """Bu test listeyi SABİTLER, Debian'ı denetlemez (denetim bulgusu 13.11.2026).

    Adların Debian 11/12/13'te var olduğu elle denetlendi (`apt-cache policy` ve `.deb`'in
    simulate kurulumu; 12.11.2026 ve 13.11.2026). Kalıcı kanıt CI'ın kurulum provasıdır:
    debian:11, 12 ve 13 kaplarında `.deb` `apt-get -f install` ile kurulur; Depends'teki bir ad
    o dağıtımda yoksa kurulum düşer. Bu bağ aşağıda sınanır; iki liste birlikte yanlış
    güncellenirse bu test değil, o prova yakalar.
    """
    assert S.depends_paketleri() == DEBIAN_11_12_13_PAKETLER
    is_akisi = (REPO / ".github" / "workflows" / "paketleme.yml").read_text(encoding="utf-8")
    assert re.search(r'^\s+debian: \["11", "12", "13"\]$', is_akisi, flags=re.MULTILINE)
    prova = KAP_ICI.read_text(encoding="utf-8")
    assert re.search(r"^apt_dene apt-get -f install -y -qq$", prova, flags=re.MULTILINE)


def test_sistemden_suz_toc_ogelerini_ayiklar() -> None:
    toc = [
        ("libstdc++.so.6", "/usr/lib/x86_64-linux-gnu/libstdc++.so.6", "BINARY"),
        ("libgbm.so.1", "/usr/lib/x86_64-linux-gnu/libgbm.so.1", "BINARY"),
        ("libssl.so.1.1", "/usr/lib/x86_64-linux-gnu/libssl.so.1.1", "BINARY"),
        ("PySide6/Qt/lib/libQt6Gui.so.6", "/sp/PySide6/Qt/lib/libQt6Gui.so.6", "BINARY"),
        ("pillow.libs/libzstd-44be1190.so.1.5.7", "/sp/pillow.libs/x", "BINARY"),
        ("libz.so.1", "/lib/x86_64-linux-gnu/libz.so.1", "BINARY"),
    ]
    kalan, atilan = S.sistemden_suz(toc)
    assert atilan == ["libstdc++.so.6", "libgbm.so.1", "libz.so.1"]
    assert [oge[0] for oge in kalan] == [
        "libssl.so.1.1",
        "PySide6/Qt/lib/libQt6Gui.so.6",
        "pillow.libs/libzstd-44be1190.so.1.5.7",
    ]


def test_paket_denetimi_diskte_dosyayi_ve_sembolik_bagi_bulur(tmp_path: Path) -> None:
    paket = tmp_path / "oab-defteri"
    ic = paket / "_internal"
    ic.mkdir(parents=True)
    (ic / "libssl.so.1.1").write_bytes(b"\x7fELF")
    (ic / "libQt6Gui.so.6").write_bytes(b"\x7fELF")
    assert S.paket_denetimi(paket) == []
    assert S.main(["denetle", "--paket", str(paket)]) == 0

    (ic / "libstdc++.so.6").write_bytes(b"\x7fELF")
    (ic / "PySide6" / "Qt" / "lib").mkdir(parents=True)
    (ic / "PySide6" / "Qt" / "lib" / "libgbm.so.1").symlink_to(ic / "libssl.so.1.1")
    hatalar = S.paket_denetimi(paket)
    assert len(hatalar) == 2
    assert "_internal/PySide6/Qt/lib/libgbm.so.1" in hatalar[0]
    assert "_internal/libstdc++.so.6" in hatalar[1]
    assert all("sistemden_suz" in h for h in hatalar)
    assert S.main(["denetle", "--paket", str(paket)]) == 1
    assert S.main(["denetle", "--paket", str(tmp_path / "yok")]) == 2


def test_depends_komutu_virgullu_listeyi_basar(capsys: pytest.CaptureFixture[str]) -> None:
    assert S.main(["depends"]) == 0
    assert capsys.readouterr().out.strip() == ", ".join(DEBIAN_11_12_13_PAKETLER)


# ------------------------------------------------------------------ spec


def _sistem_blogu() -> ast.If:
    agac = ast.parse(SPEC.read_text(encoding="utf-8"))
    for dugum in agac.body:
        if isinstance(dugum, ast.If) and "sistemden_suz" in ast.unparse(dugum):
            return dugum
    raise AssertionError("spec'te sistemden_suz bloğu yok")


def test_spec_suzgeci_yalniz_linuxta_analysis_sonrasi_uygular() -> None:
    blok = _sistem_blogu()
    # Yalnız Linux: koşul `not WINDOWS` (Windows paketi etkilenmez).
    assert ast.unparse(blok.test) == "not WINDOWS"
    govde = ast.unparse(blok)
    assert "a.binaries, _sistemden_ikili = _sistem.sistemden_suz(a.binaries)" in govde
    assert "a.datas, _sistemden_veri = _sistem.sistemden_suz(a.datas)" in govde
    assert "import sistem_kutuphaneleri as _sistem" in govde
    assert "REPO / 'packaging' / 'linux'" in govde  # ast.unparse tek tırnak basar
    spec = SPEC.read_text(encoding="utf-8")
    # Analysis'ten SONRA (kancaların ve ikili çözümlemenin eklediklerini görür), lisans
    # süzgeçlerinin yanında, PYZ/COLLECT'ten ÖNCE.
    assert (
        spec.index("a = Analysis(")
        < spec.index("_lisanslar.qt_gpl_suz")
        < spec.index("_sistem.sistemden_suz")
        < spec.index("pyz = PYZ(")
    )


def test_spec_suzgeci_windowsta_calismaz_linuxta_calisir() -> None:
    """Bloğu sahte `a` ile iki platformda koşturur: Windows'ta TOC'a dokunulmaz."""
    blok = _sistem_blogu()
    kod = compile(ast.Module(body=[blok], type_ignores=[]), str(SPEC), "exec")

    class _Sahte:
        pass

    for windows, beklenen in ((True, 2), (False, 1)):
        a = _Sahte()
        a.binaries = [  # type: ignore[attr-defined]
            ("libstdc++.so.6", "/x/libstdc++.so.6", "BINARY"),
            ("libssl.so.1.1", "/x/libssl.so.1.1", "BINARY"),
        ]
        a.datas = [("libgbm.so.1", "/x/libgbm.so.1", "DATA")]  # type: ignore[attr-defined]

        class _Lisans:
            @staticmethod
            def yaz(_metin: str) -> None:
                return None

        ad_alani: dict[str, Any] = {
            "WINDOWS": windows,
            "REPO": REPO,
            "sys": sys,
            "a": a,
            "_lisanslar": _Lisans,
        }
        exec(kod, ad_alani)  # noqa: S102 — depodaki spec'in kendi bloğu
        assert len(a.binaries) == beklenen  # type: ignore[attr-defined]
        assert len(a.datas) == (1 if windows else 0)  # type: ignore[attr-defined]


# ------------------------------------------------------------------ build.sh / .deb


def test_build_sh_depends_listeyi_tek_kaynaktan_her_derlemede_alir() -> None:
    betik = BUILD_SH.read_text(encoding="utf-8")
    assert (
        'DEPENDS_SISTEM="$(python "$DEPO/packaging/linux/sistem_kutuphaneleri.py" depends)"'
        in betik
    )
    # Qt'siz derlemede de girer (libstdc++/zlib/expat Qt dışındaki ikililerin de bağımlılığı).
    assert 'DEPENDS="$DEPENDS_TEMEL, $DEPENDS_SISTEM"' in betik
    assert betik.index("DEPENDS_SISTEM=") < betik.index('DEPENDS="$DEPENDS_TEMEL')


def test_build_sh_derleme_sonrasi_denetim_paketten_once_durdurur() -> None:
    betik = BUILD_SH.read_text(encoding="utf-8")
    komut = (
        'python "$DEPO/packaging/linux/sistem_kutuphaneleri.py" denetle '
        '--paket "$PAKET_KOKU/oab-defteri"'
    )
    assert komut in betik
    # `set -e` altında; PyInstaller'dan SONRA, duman testlerinden ve .deb'den ÖNCE.
    assert betik.startswith("#!/usr/bin/env bash") and "set -euo pipefail" in betik
    assert (
        betik.index("pyinstaller \\")
        < betik.index(komut)
        < betik.index('"$UYGULAMA" --bagimlilik-duman')
        < betik.index("dpkg-deb --root-owner-group")
    )


def test_depends_sablonu_tek_satir_yer_tutucu() -> None:
    """Depends tek satıra yazılır (sed ile); paket adlarında `|` ya da satır sonu olamaz."""
    sablon = (REPO / "packaging" / "linux" / "debian-control.tmpl").read_text(encoding="utf-8")
    assert "Depends: @DEPENDS@\n" in sablon
    assert all(re.fullmatch(r"[a-z0-9][a-z0-9+.-]+", p) for p in S.depends_paketleri())


# ------------------------------------------------------------------ taşınabilir sürüm


def test_benioku_gerekli_paketler_listesi_depends_ile_ayni_paketleri_sayar() -> None:
    metin = BENIOKU.read_text(encoding="utf-8")
    komutlar = " ".join(re.findall(r"sudo apt install ((?:[^\n]*\\\n)*[^\n]*)", metin)).replace(
        "\\", " "
    )
    kurulan = set(komutlar.split())
    eksik = [p for p in S.depends_paketleri() if p not in kurulan]
    assert not eksik, f"BENIOKU.txt 'GEREKLİ SİSTEM PAKETLERİ' eksik: {eksik}"
    assert "Pardus 25" in metin and "Debian 13" in metin


# ------------------------------------------------------------------ kurulum provası
#
# Denetimler `packaging/linux/sistem_denetimi.sh`'teki işlevlerdir; kap-ici-test.sh onları
# `set -euo pipefail` altında ÇIPLAK deyim olarak çağırır. Davranış (işlevin dönüşü) sahte
# paket ağacı ve PATH'e konan sahte `ldd` ile sınanır, çağrı biçimi metinle bağlanır. Denetim
# bulgusu (13.11.2026): eski satır içi bloklardaki `exit 1` `true` yapılınca testler yeşil
# kalıyordu.


def _kabuk(tmp_path: Path, komut: str, ldd: str | None = None) -> subprocess.CompletedProcess[str]:
    """sistem_denetimi.sh'i kaynak alıp `komut`u `set -euo pipefail` altında koşturur."""
    yol = "/usr/bin:/bin"
    if ldd is not None:
        sahte_dizin = tmp_path / "sahte-bin"
        sahte_dizin.mkdir(exist_ok=True)
        sahte = sahte_dizin / "ldd"
        sahte.write_text(ldd, encoding="utf-8")
        sahte.chmod(0o755)
        yol = f"{sahte_dizin}:{yol}"
    betik = f'set -euo pipefail\n. "{DENETIM_SH}"\n{komut}\necho SON\n'
    # S603: komut satırı testin KENDİSİ tarafından üretiliyor, dış girdi yok.
    return subprocess.run(  # noqa: S603
        [BASH, "-c", betik],
        capture_output=True,
        text=True,
        env={"PATH": yol, "LC_ALL": "C.UTF-8"},
        check=False,
    )


def _elf(yol: Path) -> Path:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_bytes(b"\x7fELF\x02\x01\x01")
    return yol


def test_kap_ici_ere_tek_kaynakla_ayni() -> None:
    betik = DENETIM_SH.read_text(encoding="utf-8")
    eslesme = re.search(r"^SISTEMDEN_ERE='([^']+)'$", betik, flags=re.MULTILINE)
    assert eslesme, "sistem_denetimi.sh'te SISTEMDEN_ERE yok"
    assert eslesme.group(1) == S.SISTEMDEN_ERE


def test_ere_grep_ile_python_re_ayni_adlari_eslesir(tmp_path: Path) -> None:
    """Kurulum provası deseni `grep -E` ile koşar: iki motor aynı kararı vermeli."""
    adlar = [Path(a.replace("\\", "/")).name for a in SISTEMDEN + GOMULU]
    girdi = tmp_path / "adlar.txt"
    girdi.write_text("\n".join(adlar) + "\n", encoding="utf-8")
    grep = shutil.which("grep") or "/bin/grep"
    # S603: komut ve girdi testin kendisinin; dış girdi yok.
    sonuc = subprocess.run(  # noqa: S603
        [grep, "-E", S.SISTEMDEN_ERE, str(girdi)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert sonuc.returncode == 0, sonuc.stderr
    assert sorted(sonuc.stdout.split()) == sorted(a for a in adlar if S.sistemden_mi(a))


# --- 1) Dışlanan kütüphaneler pakette yok


def test_prova_sistem_kutuphanesi_yokken_gecer(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    _elf(kok / "_internal" / "libssl.so.1.1")
    _elf(kok / "_internal" / "PySide6" / "Qt" / "lib" / "libQt6Gui.so.6")

    sonuc = _kabuk(tmp_path, f'sistemden_alinanlar_pakette_yok "{kok}"')

    assert sonuc.returncode == 0, sonuc.stderr
    assert "SON" in sonuc.stdout


def test_prova_pakette_sistem_kutuphanesi_bulunca_durur(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    _elf(kok / "_internal" / "libssl.so.1.1")
    _elf(kok / "_internal" / "libstdc++.so.6")
    lib = kok / "_internal" / "PySide6" / "Qt" / "lib"
    lib.mkdir(parents=True)
    (lib / "libgbm.so.1").symlink_to(kok / "_internal" / "libssl.so.1.1")

    sonuc = _kabuk(tmp_path, f'sistemden_alinanlar_pakette_yok "{kok}"')

    assert sonuc.returncode == 1
    assert "SON" not in sonuc.stdout  # set -e: prova burada durur
    assert "HATA" in sonuc.stderr
    assert "libstdc++.so.6" in sonuc.stderr and "libgbm.so.1" in sonuc.stderr
    assert "libssl" not in sonuc.stderr


# --- 2) Paketteki ELF'lerin bağımlılıkları çözülüyor

#: Sahte ldd: dosya adında "eksik" geçen ikili için bir "not found" satırı basar.
SAHTE_LDD_COZUM = """#!/usr/bin/env bash
nesne="${@: -1}"
echo "	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x0)"
case "$(basename "$nesne")" in
  *eksik*) echo "	libcups.so.2 => not found" ;;
esac
"""


def test_prova_elf_bagimliliklari_cozulunce_gecer(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    _elf(kok / "_internal" / "PySide6" / "Qt" / "plugins" / "platforms" / "libqxcb.so")
    # ELF olmayan .so (ör. yorum metni): adı sahte ldd'ye "eksik" dese de incelenmez.
    (kok / "_internal" / "sahte-eksik.so").write_text("ELF değil", encoding="utf-8")

    sonuc = _kabuk(tmp_path, f'paket_elfleri_cozuluyor "{kok}"', ldd=SAHTE_LDD_COZUM)

    assert sonuc.returncode == 0, sonuc.stderr
    assert "SON" in sonuc.stdout


def test_prova_pencere_yolunda_eksik_bagimlilikta_durur(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    _elf(kok / "_internal" / "PySide6" / "Qt" / "plugins" / "platforms" / "libqxcb.so")
    _elf(kok / "_internal" / "PySide6" / "Qt" / "lib" / "libQt6Gui-eksik.so.6")

    sonuc = _kabuk(tmp_path, f'paket_elfleri_cozuluyor "{kok}"', ldd=SAHTE_LDD_COZUM)

    assert sonuc.returncode == 1
    assert "SON" not in sonuc.stdout
    assert "_internal/PySide6/Qt/lib/libQt6Gui-eksik.so.6" in sonuc.stderr
    assert "libcups.so.2 => not found" in sonuc.stderr


def test_prova_istege_bagli_qt_parcasinin_eksigini_yalniz_bildirir(tmp_path: Path) -> None:
    kok = tmp_path / "oab-defteri"
    eklentiler = kok / "_internal" / "PySide6" / "Qt" / "plugins"
    _elf(eklentiler / "printsupport" / "libcupsprintersupport.so")
    # Adı sahte ldd'ye "eksik" desin diye, isteğe bağlı desene uyan bir Wayland eklentisi:
    _elf(eklentiler / "wayland-shell-integration" / "x-eksik.so")

    sonuc = _kabuk(tmp_path, f'paket_elfleri_cozuluyor "{kok}"', ldd=SAHTE_LDD_COZUM)

    assert sonuc.returncode == 0, sonuc.stderr
    assert "BİLGİ (isteğe bağlı)" in sonuc.stdout
    assert "wayland-shell-integration/x-eksik.so" in sonuc.stdout


#: debian:13 ilk koşusunda (12.11.2026) bağımlılığı Depends'te bilerek olmayan isteğe bağlı
#: Qt parçaları — ldd denetimi bunları yalnız BİLGİ olarak basar.
ISTEGE_BAGLI = [
    "_internal/PySide6/Qt/lib/libQt6WaylandClient.so.6",
    "_internal/PySide6/Qt/lib/libQt6WaylandEglClientHwIntegration.so.6",
    "_internal/PySide6/Qt/lib/libQt6WlShellIntegration.so.6",
    "_internal/PySide6/Qt/lib/libQt6Multimedia.so.6",
    "_internal/PySide6/Qt/lib/libQt6MultimediaQuick.so.6",
    "_internal/PySide6/Qt/lib/libQt6SpatialAudio.so.6",
    "_internal/PySide6/Qt/lib/libQt6TextToSpeech.so.6",
    "_internal/PySide6/Qt/plugins/platforms/libqwayland-egl.so",
    "_internal/PySide6/Qt/plugins/platforms/libqwayland-generic.so",
    "_internal/PySide6/Qt/plugins/wayland-decoration-client/libadwaita.so",
    "_internal/PySide6/Qt/plugins/wayland-graphics-integration-client/libdrm-egl-server.so",
    "_internal/PySide6/Qt/plugins/wayland-shell-integration/libxdg-shell.so",
    "_internal/PySide6/Qt/plugins/platformthemes/libqgtk3.so",
    "_internal/PySide6/Qt/plugins/printsupport/libcupsprintersupport.so",
    "_internal/PySide6/Qt/qml/QtWayland/Client/TextureSharing/libwaylandtexturesharingplugin.so",
    "_internal/PySide6/Qt/qml/QtMultimedia/libquickmultimediaplugin.so",
    "_internal/PySide6/Qt/qml/QtTextToSpeech/libtexttospeechqmlplugin.so",
]

#: Pencere yolu — eksik bağımlılığı HER ZAMAN hata olmalı.
PENCERE_YOLU = [
    "_internal/PySide6/Qt/plugins/platforms/libqxcb.so",
    "_internal/PySide6/Qt/plugins/xcbglintegrations/libqxcb-glx-integration.so",
    "_internal/PySide6/Qt/plugins/xcbglintegrations/libqxcb-egl-integration.so",
    "_internal/PySide6/Qt/lib/libQt6XcbQpa.so.6",
    "_internal/PySide6/Qt/lib/libQt6Gui.so.6",
    "_internal/PySide6/Qt/lib/libQt6WebEngineCore.so.6",
    "_internal/PySide6/Qt/lib/libQt6WebEngineWidgets.so.6",
    "_internal/PySide6/Qt/libexec/QtWebEngineProcess",
    "_internal/PySide6/QtWebEngineCore.abi3.so",
    "_internal/libpython3.12.so.1.0",
    "oab-defteri",
]


def test_kap_ici_ldd_istisnasi_yalniz_isteg_bagli_qt_parcalarini_kapsar(tmp_path: Path) -> None:
    betik = DENETIM_SH.read_text(encoding="utf-8")
    eslesme = re.search(r"^ISTEGE_BAGLI_ELF='([^']+)'$", betik, flags=re.MULTILINE)
    assert eslesme, "sistem_denetimi.sh'te ISTEGE_BAGLI_ELF yok"
    girdi = tmp_path / "yollar.txt"
    girdi.write_text("\n".join(ISTEGE_BAGLI + PENCERE_YOLU) + "\n", encoding="utf-8")
    grep = shutil.which("grep") or "/bin/grep"
    # S603: komut ve girdi testin kendisinin; dış girdi yok.
    sonuc = subprocess.run(  # noqa: S603
        [grep, "-E", eslesme.group(1), str(girdi)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert sorted(sonuc.stdout.split()) == sorted(ISTEGE_BAGLI)


def test_wayland_istisnasi_pencere_yolunun_xcbye_sabitlenmesine_dayanir() -> None:
    """Wayland eklentisi isteğe bağlı sayılabilir, çünkü paket Qt'yi xcb'ye sabitler
    (`rthook_od.py`; denetim bulgusu 13.11.2026). libwayland-client sistemden alındığından
    libwayland-cursor0 ve libwayland-egl1 kurulu her makinede eklenti YÜKLENEBİLİR olur;
    sabitleme kalkarsa Wayland oturumunda pencere sınanmamış yola geçer."""
    assert S.sistemden_mi("libwayland-client.so.0")
    kanca = (REPO / "packaging" / "pyinstaller" / "rthook_od.py").read_text(encoding="utf-8")
    assert 'QT_PLATFORM_LINUX = "xcb"' in kanca
    betik = DENETIM_SH.read_text(encoding="utf-8")
    assert "rthook_od.py" in betik and "xcb" in betik


# --- 3) Sistemin Mesa sürücüsü paketin kütüphaneleriyle eksik sembolsüz bağlanıyor

#: Sahte `ldd -r`: her nesnede sürücünün KENDİ eksiği (paket yolu olmadan da görünür); adı
#: "kirik" içeren nesnede paket yolu (LD_LIBRARY_PATH) eklenince DOĞAN eksik.
SAHTE_LDD_MESA = """#!/usr/bin/env bash
nesne="${@: -1}"
echo "	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x0)"
echo "undefined symbol: _surucunun_kendi_eksigi	($nesne)"
if [ -n "${LD_LIBRARY_PATH:-}" ]; then
  case "$(basename "$nesne")" in
    *kirik*) echo "undefined symbol: gbm_bo_create_with_modifiers2	($nesne)" ;;
  esac
fi
"""


def _mesa(tmp_path: Path, adlar: list[str]) -> str:
    ic = tmp_path / "oab-defteri" / "_internal"
    ic.mkdir(parents=True)
    nesneler = [str(_elf(tmp_path / "usr-lib" / ad)) for ad in adlar]
    yok = tmp_path / "usr-lib" / "libgallium-*.so"  # eşleşmeyen glob olduğu gibi kalır
    return f'mesa_paketle_baglaniyor "{ic}" ' + " ".join(f'"{n}"' for n in [*nesneler, yok])


def test_prova_mesa_paket_yoluyla_eksiksiz_baglaninca_gecer(tmp_path: Path) -> None:
    komut = _mesa(tmp_path, ["libGLX_mesa.so.0", "libEGL_mesa.so.0", "libgbm.so.1"])

    sonuc = _kabuk(tmp_path, komut, ldd=SAHTE_LDD_MESA)

    assert sonuc.returncode == 0, sonuc.stderr
    assert "3 Mesa nesnesi" in sonuc.stdout and "SON" in sonuc.stdout


def test_prova_paket_yoluyla_dogan_mesa_eksiginde_durur(tmp_path: Path) -> None:
    komut = _mesa(tmp_path, ["libGLX_mesa.so.0", "libEGL_mesa-kirik.so.0", "libgbm.so.1"])

    sonuc = _kabuk(tmp_path, komut, ldd=SAHTE_LDD_MESA)

    assert sonuc.returncode == 1
    assert "SON" not in sonuc.stdout
    assert "gbm_bo_create_with_modifiers2" in sonuc.stderr
    assert "libEGL_mesa-kirik.so.0" in sonuc.stderr
    # Sürücünün kendi eksiği (paket yolu olmadan da var) hata sayılmaz.
    assert "_surucunun_kendi_eksigi" not in sonuc.stderr


def test_prova_mesa_dosyalari_bulunamazsa_bosa_kosmaz(tmp_path: Path) -> None:
    komut = _mesa(tmp_path, ["libGLX_mesa.so.0", "libgbm.so.1"])

    sonuc = _kabuk(tmp_path, komut, ldd=SAHTE_LDD_MESA)

    assert sonuc.returncode == 1
    assert "SON" not in sonuc.stdout
    assert "Mesa sürücü dosyaları bulunamadı (2)" in sonuc.stderr


# --- kap-ici-test.sh çağrı biçimi


def _deyimler(metin: str) -> list[str]:
    """Ters bölüyle sürdürülen satırları tek deyimde birleştirir."""
    return re.sub(r"[ \t]*\\\n\s*", " ", metin).splitlines()


def test_kap_ici_prova_denetimleri_ciplak_deyimle_cagirir() -> None:
    """Dönüş 1 provayı durdurmalı: çağrı `set -euo pipefail` altında, `||`, `&&`, `;`, `!`,
    `if` ya da alt kabuk olmadan yapılır; denetimler dumanlardan ve --autotest'ten ÖNCE gelir."""
    prova = KAP_ICI.read_text(encoding="utf-8")
    assert "\nset -euo pipefail\n" in prova
    deyimler = _deyimler(prova)
    assert '. "$(dirname "${BASH_SOURCE[0]}")/sistem_denetimi.sh"' in deyimler
    beklenen = {
        "sistemden_alinanlar_pakette_yok": r"sistemden_alinanlar_pakette_yok /opt/oab-defteri",
        "paket_elfleri_cozuluyor": r"paket_elfleri_cozuluyor /opt/oab-defteri",
        "mesa_paketle_baglaniyor": (
            r"mesa_paketle_baglaniyor /opt/oab-defteri/_internal( /usr/lib/x86_64-linux-gnu/\S+)+"
        ),
    }
    sira: list[int] = []
    for islev, desen in beklenen.items():
        cagrilar = [i for i, d in enumerate(deyimler) if islev in d]
        assert len(cagrilar) == 1, f"{islev} tek yerde çağrılmalı: {cagrilar}"
        assert re.fullmatch(desen, deyimler[cagrilar[0]]), deyimler[cagrilar[0]]
        sira.append(cagrilar[0])
    mesa_kurulumu = next(
        i for i, d in enumerate(deyimler) if d.startswith("apt_dene") and "libgl1-mesa-dri" in d
    )
    otomatik = deyimler.index("oab-defteri --autotest")
    duman = next(i for i, d in enumerate(deyimler) if d.startswith("oab-defteri --"))
    assert sira[0] < sira[1] < mesa_kurulumu < sira[2] < duman <= otomatik
    # Satır içi eski bloklar geri gelmesin: denetim tek yerde, sınanan işlevlerde.
    assert "SISTEMDEN_ERE=" not in prova and "ISTEGE_BAGLI_ELF=" not in prova
