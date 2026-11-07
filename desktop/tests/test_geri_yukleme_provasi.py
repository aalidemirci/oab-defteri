"""Temiz makinede geri yükleme provası (aile iskeletinden; OAB'de tasarım §14 F1b kapısı:
şifreli yedek geri yüklenir).

Bilgisayar değişir, disk bozulur, program yeniden kurulur: okulun elinde kalan,
kullanıcının USB belleğe kaydettiği şifreli yedektir. Prova GERÇEK süreçlerle
koşar (`desktop.main`, gerçek göç, gerçek şifreleme, gerçek yedek kapsayıcısı):

1. **Eski bilgisayar** (`hazirla`): ilk program yöneticisi hesabı + doğrulanmış
   kurtarma anahtarı, uydurma kişi kayıtları, uydurma bir ek; dış (tam) yedek USB'ye.
2. **Temiz bilgisayar**: yedeğin başlığı yalnız kurtarma bölümünü taşır (tasarım
   TK10): hesap parolası yeni bilgisayarda yedeği AÇMAZ; boş veri dizininde
   `--geri-yukle` kurtarma anahtarıyla → güvenlik dosyası yalnız kurtarma bölümüyle
   yazılır → program açılır (`--autotest`: damga, bütünlük, günlük yedek, göç,
   sunucu) → kurtarma anahtarıyla açılış program yöneticisinin parolasını yeniler →
   kişi kayıtları birebir aynıdır.
3. **Aynı bilgisayar**: güncel `guvenlik.json` yerindeyken hesabın tanıtıcısı ve
   parolasıyla geri yüklenir; güvenlik dosyasına dokunulmaz.
4. **Daha yeni sürümün yedeği eski programda açılmaz**: geri yükleme sürüm damgasını
   siler; veritabanının göç kaydı eski programı 4 koduyla durdurur.
5. **Sihirbazı başka hesapla doldurulmuş yeni bilgisayar** (aile iskeletinin düzeltmesi):
   kurucunun sonunda açılan programda hesap kurulmuşsa geri yükleme yabancı güvenlik
   dosyasını ve boş veritabanını kenara alır; veri yine birebir aynıdır.
6. **Ekler dâhil** (tasarım §10.6, F1b kapısı; plan F1b-3 "Ötekiler"): temiz bilgisayarda
   tam yedekten dönen ek depoda durur ve çözülür. F1b'de ek ekleyen ekran yoktur: ek betikle
   tohumlanır, gerçek programdaki elle denetim eksiz yedekle yapılır.

Aile iskeletinin verilmiş kart defteri sınamaları kütüphane uygulamasıyla söküldü
(F1a-2).
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from desktop.errors import EXIT_OK, EXIT_RESTORE_FAILED, EXIT_SCHEMA_TOO_NEW
from desktop.tests.alt_surec import betik, gunluk, program

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def eski_bilgisayar(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, Any]]:
    """Eski bilgisayar: gerçek göç + hesap + veri + USB'deki dış yedek (modülde bir kez)."""
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


def test_temiz_makinede_hesap_parolasi_yedegi_acmaz(
    eski_bilgisayar: dict[str, Any], tmp_path: Path
) -> None:
    """TK10: yedekte hesap sarmalı yok; dönemi biten üyenin parolası eski yedeği açmaz."""
    yeni = tmp_path / "yeni-bilgisayar"

    sonuc = program(
        "--geri-yukle",
        eski_bilgisayar["yedek"],
        "--hesap",
        eski_bilgisayar["tanitici"],
        "--parola",
        eski_bilgisayar["parola"],
        "--evet",
        "--data-dir",
        str(yeni),
    )

    assert sonuc.returncode == EXIT_RESTORE_FAILED
    assert not (yeni / "data" / "db.sqlite3").exists()
    assert not (yeni / "data" / "guvenlik.json").exists()
    assert "kurtarma anahtarıyla açılır" in gunluk(yeni)


def test_temiz_makinede_kurtarma_anahtariyla_acilir_ve_parola_yenilenir(
    eski_bilgisayar: dict[str, Any], tmp_path: Path
) -> None:
    yeni = tmp_path / "yeni-bilgisayar"

    _geri_yukle(yeni, eski_bilgisayar["yedek"], "--kurtarma-anahtari", eski_bilgisayar["kurtarma"])

    # Güvenlik dosyası yedeğin başlığından YALNIZ kurtarma bölümüyle kuruldu; yedek
    # anahtarı da yazıldı; damga silindi (yedeğin sürümü bilinmez), ilk açılış yazar.
    durum = json.loads((yeni / "data" / "guvenlik.json").read_text(encoding="utf-8"))
    assert durum["hesaplar"] == []
    assert durum["kurtarma"]["no"] == 1 and durum["kurtarma"]["dogrulandi"]
    assert (yeni / "data" / "yedekleme.json").is_file()
    assert not (yeni / "data" / "surum.json").exists()

    _acilis(yeni)
    assert (yeni / "data" / "surum.json").is_file()
    # Açılış yeni bilgisayarın ilk günlük yedeğini aldı (şifreli, başlıklı).
    assert list((yeni / "backups").glob("gunluk-*.odbak"))

    kurtarma = betik("dogrula", "--data-dir", str(yeni), "--kurtarma", eski_bilgisayar["kurtarma"])
    assert kurtarma["ozet"] == eski_bilgisayar["beklenen"]
    assert kurtarma["ozet"]["ogrenciler"], "kişi kayıtları taşınmadı"
    assert kurtarma["durum"]["recovery_key_confirmed"] is True
    assert kurtarma["durum"]["locked"] is False
    # Kurtarma anahtarıyla açılış program yöneticisine yeni parola belirler; sonraki
    # açılış onunla yapılır.
    yeni_parola = betik("dogrula", "--data-dir", str(yeni), "--parola", "Prova-Yeni-Parola-2")
    assert yeni_parola["ozet"] == eski_bilgisayar["beklenen"]


def test_tam_yedek_eki_tasir_ve_temiz_makinede_ek_acilir(
    eski_bilgisayar: dict[str, Any], tmp_path: Path
) -> None:
    """Gerçek süreçlerle `sifreli_yedegi_kaydet` → `--geri-yukle` → ek depodan çözülür."""
    ozet = eski_bilgisayar["yedek_ozeti"]
    assert (ozet["ek_sayisi"], ozet["eksik"], ozet["denetlendi"]) == (1, 0, True)
    yeni = tmp_path / "yeni-bilgisayar"

    _geri_yukle(yeni, eski_bilgisayar["yedek"], "--kurtarma-anahtari", eski_bilgisayar["kurtarma"])
    _acilis(yeni)

    assert (yeni / "data" / "dosyalar" / eski_bilgisayar["ek"]).is_file()
    sonuc = betik(
        "ek-oku",
        "--data-dir",
        str(yeni),
        "--ad",
        eski_bilgisayar["ek"],
        "--kurtarma",
        eski_bilgisayar["kurtarma"],
    )
    assert sonuc == {"ayni": True, "ad": "uydurma-ek.pdf"}


def test_ayni_bilgisayarda_hesap_parolasiyla_geri_yuklenir(
    eski_bilgisayar: dict[str, Any], tmp_path: Path
) -> None:
    """Güncel `guvenlik.json` + hesabın tanıtıcısı ve parolası (aday 1); dosyaya dokunulmaz."""
    ayni = tmp_path / "ayni-bilgisayar"
    shutil.copytree(eski_bilgisayar["kok"], ayni)
    guvenlik = (ayni / "data" / "guvenlik.json").read_bytes()

    _geri_yukle(
        ayni,
        eski_bilgisayar["yedek"],
        "--hesap",
        eski_bilgisayar["tanitici"],
        "--parola",
        eski_bilgisayar["parola"],
    )

    assert (ayni / "data" / "guvenlik.json").read_bytes() == guvenlik
    assert list((ayni / "data").glob("db-onceki-*.sqlite3"))
    _acilis(ayni)
    dogrulama = betik("dogrula", "--data-dir", str(ayni), "--parola", eski_bilgisayar["parola"])
    assert dogrulama["ozet"] == eski_bilgisayar["beklenen"]


def test_sihirbazda_baska_hesap_kurulmus_yeni_bilgisayara_geri_yukleme(
    eski_bilgisayar: dict[str, Any], tmp_path: Path
) -> None:
    """Kurucunun "programı çalıştır" kutusu (Inno `postinstall`, varsayılan işaretli) programı
    açar; kullanıcı sihirbazda BAŞKA bir hesap kurabilir. Yeni bilgisayarda yabancı bir
    güvenlik dosyası, yedek anahtarı, geçiş yedeği ve boş veritabanı oluşur. Eski yedeğin
    geri yüklenmesi yine aynı veriyi verir: yabancı güvenlik dosyası "guvenlik-arsiv"
    adıyla, boş veritabanı "db-onceki" adıyla kenara alınır, güvenlik dosyası ve yedek
    anahtarı yedeğin başlığından yazılır (aile iskeletinin düzeltmesi)."""
    yeni = tmp_path / "sihirbazi-doldurulmus"
    betik("sihirbaz", "--data-dir", str(yeni), "--parola", "Sihirbaz-Baska-Parola-3")
    yabanci = (yeni / "data" / "guvenlik.json").read_bytes()
    yabanci_anahtar = (yeni / "data" / "yedekleme.json").read_bytes()

    _geri_yukle(yeni, eski_bilgisayar["yedek"], "--kurtarma-anahtari", eski_bilgisayar["kurtarma"])

    arsivler = list((yeni / "data").glob("guvenlik-arsiv-*.json"))
    assert [yol.read_bytes() for yol in arsivler] == [yabanci]
    assert (yeni / "data" / "guvenlik.json").read_bytes() != yabanci
    assert (yeni / "data" / "yedekleme.json").read_bytes() != yabanci_anahtar
    assert list((yeni / "data").glob("db-onceki-*.sqlite3")), "boş veritabanı kenara alınmadı"
    _acilis(yeni)
    dogrulama = betik("dogrula", "--data-dir", str(yeni), "--kurtarma", eski_bilgisayar["kurtarma"])
    assert dogrulama["ozet"] == eski_bilgisayar["beklenen"]
    assert dogrulama["durum"]["recovery_key_confirmed"] is True


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
    _geri_yukle(hedef, gelecek["yedek"], "--kurtarma-anahtari", eski_bilgisayar["kurtarma"])
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
