"""Temiz makinede geri yükleme provası (aile iskeletinden; OAB'de tasarım §14 F1b kapısı:
şifreli yedek geri yüklenir).

Bilgisayar değişir, disk bozulur, program yeniden kurulur: okulun elinde kalan,
kullanıcının indirip USB belleğe aldığı şifreli yedektir. Prova GERÇEK süreçlerle
koşar (`desktop.main`, gerçek göç, gerçek şifreleme, gerçek yedek kapsayıcısı):

1. **Eski bilgisayar** (`hazirla`): yönetici parolası + doğrulanmış kurtarma anahtarı,
   uydurma kişi kayıtları; dış yedek USB'ye.
2. **Temiz bilgisayar**: boş veri dizininde `--geri-yukle` (parola ya da kurtarma
   anahtarıyla) → güvenlik dosyası yedeğin başlığından yazılır → program açılır
   (`--autotest`: damga, bütünlük, günlük yedek, göç, sunucu) → kilit AYNI parolayla /
   AYNI anahtarla açılır → kişi kayıtları birebir aynıdır.
3. **Daha yeni sürümün yedeği eski programda açılmaz**: geri yükleme sürüm damgasını
   siler; veritabanının göç kaydı eski programı 4 koduyla durdurur.
4. **Sihirbazı başka parolayla doldurulmuş yeni bilgisayar** (aile iskeletinin düzeltmesi):
   kurucunun sonunda açılan programda parola kurulmuşsa geri yükleme yabancı güvenlik
   dosyasını ve boş veritabanını kenara alır; veri yine birebir aynıdır.

Aile iskeletinin verilmiş kart defteri sınamaları kütüphane uygulamasıyla söküldü
(F1a-2).
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from desktop.errors import EXIT_OK, EXIT_SCHEMA_TOO_NEW
from desktop.tests.alt_surec import betik, gunluk, program

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def eski_bilgisayar(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, Any]]:
    """Eski bilgisayar: gerçek göç + parola + veri + USB'deki dış yedek (modülde bir kez)."""
    kok = tmp_path_factory.mktemp("eski-bilgisayar")
    usb = tmp_path_factory.mktemp("usb-bellek")
    sonuc = betik("hazirla", "--data-dir", str(kok), "--usb", str(usb))
    sonuc["kok"] = kok
    sonuc["usb"] = usb
    assert Path(sonuc["yedek"]).is_file()
    yield sonuc


def _geri_yukle(hedef: Path, yedek: str, *sir: str) -> None:
    sonuc = program("--geri-yukle", yedek, *sir, "--evet", "--data-dir", str(hedef))
    assert sonuc.returncode == EXIT_OK, (sonuc.stdout[-2000:], sonuc.stderr[-2000:])


def _acilis(hedef: Path) -> None:
    sonuc = program("--autotest", "--data-dir", str(hedef))
    assert sonuc.returncode == EXIT_OK, (sonuc.stderr[-2000:], gunluk(hedef)[-3000:])


def test_temiz_makinede_parolayla_geri_yukleme_ayni_veriyi_verir(
    eski_bilgisayar: dict[str, Any], tmp_path: Path
) -> None:
    yeni = tmp_path / "yeni-bilgisayar"

    _geri_yukle(yeni, eski_bilgisayar["yedek"], "--parola", eski_bilgisayar["parola"])

    # Güvenlik dosyası ve yedek anahtarı yedeğin başlığından yeniden kuruldu; damga
    # silindi (yedeğin sürümü bilinmez), ilk açılış yeniden yazar.
    assert (yeni / "data" / "guvenlik.json").is_file()
    assert (yeni / "data" / "yedekleme.json").is_file()
    assert not (yeni / "data" / "surum.json").exists()

    _acilis(yeni)
    assert (yeni / "data" / "surum.json").is_file()
    # Açılış yeni bilgisayarın ilk günlük yedeğini aldı (şifreli, başlıklı).
    assert list((yeni / "backups").glob("gunluk-*.odbak"))

    dogrulama = betik("dogrula", "--data-dir", str(yeni), "--parola", eski_bilgisayar["parola"])
    assert dogrulama["ozet"] == eski_bilgisayar["beklenen"]
    assert dogrulama["ozet"]["ogrenciler"], "kişi kayıtları taşınmadı"
    assert dogrulama["durum"]["recovery_key_confirmed"] is True
    assert dogrulama["durum"]["locked"] is False


def test_sihirbazda_baska_parola_kurulmus_yeni_bilgisayara_geri_yukleme(
    eski_bilgisayar: dict[str, Any], tmp_path: Path
) -> None:
    """Kurucunun "programı çalıştır" kutusu (Inno `postinstall`, varsayılan işaretli) programı
    açar; kullanıcı sihirbazda BAŞKA bir parola kurabilir. Yeni bilgisayarda yabancı bir
    güvenlik dosyası, yedek anahtarı, geçiş yedeği ve boş veritabanı oluşur. Eski yedeğin
    geri yüklenmesi yine aynı veriyi verir: yabancı güvenlik dosyası "guvenlik-arsiv"
    adıyla, boş veritabanı "db-onceki" adıyla kenara alınır, güvenlik dosyası ve yedek
    anahtarı yedeğin başlığından yazılır (aile iskeletinin düzeltmesi)."""
    yeni = tmp_path / "sihirbazi-doldurulmus"
    betik("sihirbaz", "--data-dir", str(yeni), "--parola", "Sihirbaz-Baska-Parola-3")
    yabanci = (yeni / "data" / "guvenlik.json").read_bytes()
    yabanci_anahtar = (yeni / "data" / "yedekleme.json").read_bytes()

    _geri_yukle(yeni, eski_bilgisayar["yedek"], "--parola", eski_bilgisayar["parola"])

    arsivler = list((yeni / "data").glob("guvenlik-arsiv-*.json"))
    assert [yol.read_bytes() for yol in arsivler] == [yabanci]
    assert (yeni / "data" / "guvenlik.json").read_bytes() != yabanci
    assert (yeni / "data" / "yedekleme.json").read_bytes() != yabanci_anahtar
    assert list((yeni / "data").glob("db-onceki-*.sqlite3")), "boş veritabanı kenara alınmadı"
    _acilis(yeni)
    dogrulama = betik("dogrula", "--data-dir", str(yeni), "--parola", eski_bilgisayar["parola"])
    assert dogrulama["ozet"] == eski_bilgisayar["beklenen"]
    assert dogrulama["durum"]["recovery_key_confirmed"] is True


def test_temiz_makinede_kurtarma_anahtariyla_acilir_ve_parola_yenilenir(
    eski_bilgisayar: dict[str, Any], tmp_path: Path
) -> None:
    yeni = tmp_path / "yeni-bilgisayar"

    _geri_yukle(yeni, eski_bilgisayar["yedek"], "--kurtarma-anahtari", eski_bilgisayar["kurtarma"])
    _acilis(yeni)

    kurtarma = betik("dogrula", "--data-dir", str(yeni), "--kurtarma", eski_bilgisayar["kurtarma"])
    assert kurtarma["ozet"] == eski_bilgisayar["beklenen"]
    # Kurtarma anahtarıyla açılış yeni parola belirler; sonraki açılış onunla yapılır.
    yeni_parola = betik("dogrula", "--data-dir", str(yeni), "--parola", "Prova-Yeni-Parola-2")
    assert yeni_parola["ozet"] == eski_bilgisayar["beklenen"]


def test_yeni_surumun_yedegi_eski_programda_acilmaz(
    eski_bilgisayar: dict[str, Any], tmp_path: Path
) -> None:
    """Geri yükleme damgayı siler; veritabanının göç kaydı eski programı durdurur (kod 4)."""
    kaynak = tmp_path / "kaynak"
    shutil.copytree(eski_bilgisayar["kok"], kaynak)
    usb = tmp_path / "usb"
    gelecek = betik(
        "gelecek-yedek",
        "--data-dir",
        str(kaynak),
        "--parola",
        eski_bilgisayar["parola"],
        "--usb",
        str(usb),
    )
    hedef = tmp_path / "eski-program"
    _geri_yukle(hedef, gelecek["yedek"], "--parola", eski_bilgisayar["parola"])
    assert not (hedef / "data" / "surum.json").exists()

    sonuc = program("--autotest", "--data-dir", str(hedef))

    assert sonuc.returncode == EXIT_SCHEMA_TOO_NEW
    kayit = gunluk(hedef)
    assert "Program sürümü eski" in kayit
    assert "tanımadığı değişiklikler" in kayit
    assert "okul.9999_gelecek_surum" in kayit
    # Göç ve damga yazılmadı: veri, onu yazan sürüme dokunulmadan kalır.
    assert not (hedef / "data" / "surum.json").exists()
    assert not list((hedef / "backups").glob("pre-migrate-*"))
