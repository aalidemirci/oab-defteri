"""Aç penceresinde seçilen yedek: yol kaynağı, USB kopması, başlık okuma (plan F1b-3).

Kullanıcı kararları 06.11.2026 "Yedek dosyası yüklenmez, programın Aç penceresiyle seçilir" ve
"Elden seçilen yedeğin başlığını sunucu okur". Kanıtlananlar:

* `POST backups/restore/` üçüncü kaynak `yol` alır; kaynak yalnız okunur, adı kayda geçer, yolu geçmez;
* geçersiz yol tek sabit iletiyle reddedilir, ileti ve günlük yolu yankılamaz, bakıma girilmez;
* çekirdek kaynağı bir kez açar, baştan sona bir kez okur, takas başlayınca bir daha okumaz; bellek
  çıkarılırsa hedefe dokunulmaz, kapı açılır, geçici dosya kalmaz, yanıt 400'dür;
* `POST backups/inspect/` listenin satırını verir, her dosyada hata yerine `null` döner, dosyanın
  tamamını okumaz; kapıları geri yüklemeyle aynıdır;
* UTF-8 olmayan dosya adı ne listeyi ne başlık okumasını düşürür; ad gösterimde `?`'lidir.

Geri yükleme testleri `test_live_restore.py`'nin ortamını kullanır: `django_db` yoktur, hedef geçici
bir dosyadır. Yollar ve adlar uydurmadır; Türkçe karakter ve boşluk bilerek vardır.
"""

from __future__ import annotations

import errno
import io
import json
import logging
import os
import pathlib
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from desktop.backup_crypto import (
    DENEME_MAGIC,
    MAGIC,
    YEDEK_OKUNAMADI,
    kap_basligini_oku,
)
from desktop.tests.kap_ortak import durum_basligi, kap_kur
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.okul import restart_gate
from apps.okul.oturum import yazar_olarak
from apps.okul.services import app_password, backup_restore, geri_yukleme_notu, live_restore
from apps.okul.services.geri_yukleme_ekleri import EkYerlesimi
from apps.okul.tests.geri_yukleme_ortak import (
    HesapSatiri,
    OrnekEk,
    depoya_koy,
    ekli_sqlite,
    ornek_ek,
    tam_yedek_kur,
    yetkili_sqlite,
)
from conftest import (
    TEST_DEK,
    TEST_HESAP_ID,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
    TEST_TANITICI,
    oturumu_ac_test,
)
from shared import bakim, crypto
from shared import dosya_sifreleme as ds

GERI_YUKLE_URL = "/api/v1/backups/restore/"
BASLIK_URL = "/api/v1/backups/inspect/"
LISTE_URL = "/api/v1/backups/"
#: Yolun içinde durur: yanıtta, günlükte ve notta geçmemelidir.
UYDURMA_KISI = "Uydurgül Masalcıoğlu"
PROGRAM_ADI = "oab-defteri-yedek-2026-11-06-101530.odbak"
SERBEST_AD = f"{UYDURMA_KISI} yedeği ğüşıöç.odbak"
#: Eski arşivden ISO-8859-9 adla kopyalanmış dosyanın baytları ve ekranda görünen adı.
UTF8_OLMAYAN_AD = b"yede\xf0im.odbak"
UTF8_OLMAYAN_ADIN_GOSTERIMI = "yede?im.odbak"
ILETI = live_restore.SECILEN_YEDEK_ACILAMADI
#: Kaynak üçünden tam olarak biri değilse (`BackupRestoreRequestSerializer`).
KAYNAK_ILETISI = "Yedek klasöründen bir dosya seçin YA DA elinizdeki yedek dosyasını seçin."


@pytest.fixture(autouse=True)
def ortam(
    guvenlik_ortami: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[dict[str, Path]]:
    """Veri dizini conftest'inki; hedef veritabanı ve dosya deposu geçici; kapı temiz."""
    db = tmp_path / "canli" / "db.sqlite3"
    db.parent.mkdir()
    depo = tmp_path / "canli" / "dosyalar"
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(db))
    monkeypatch.setattr(settings, "DOSYA_DEPOSU_DIR", str(depo), raising=False)
    yield {"veri": guvenlik_ortami, "db": db, "depo": depo}


@pytest.fixture
def usb(tmp_path: Path) -> Path:
    """Takılı bellek: program dizinlerinin dışında, adında boşluk ve Türkçe karakter var."""
    yol = tmp_path / f"{UYDURMA_KISI} USB Bellek"
    yol.mkdir()
    return yol


@pytest.fixture
def kapi(monkeypatch: pytest.MonkeyPatch) -> bakim.BakimKapisi:
    yeni = bakim.BakimKapisi()
    monkeypatch.setattr(bakim, "KAPI", yeni)
    return yeni


def _sqlite(dizin: Path, isaret: str) -> bytes:
    return yetkili_sqlite(
        dizin / f"kaynak-{isaret}.sqlite3",
        dek=TEST_DEK,
        hesaplar=[HesapSatiri(TEST_HESAP_ID, TEST_TANITICI)],
        isaret=isaret,
    )


def _yerel_yedek(hedef: Path, tmp_path: Path, isaret: str = "yeni") -> bytes:
    """Bu kurulumun DEK'iyle yerel kapsamlı yedek; dosyanın baytlarını döndürür."""
    baytlar = cast(
        "bytes",
        kap_kur(
            _sqlite(tmp_path, isaret),
            TEST_DEK,
            baslik=durum_basligi(app_password.read_state() or {}),
        ),
    )
    hedef.write_bytes(baytlar)
    return baytlar


def _tam_yedek(hedef: Path, tmp_path: Path) -> tuple[OrnekEk, OrnekEk]:
    """İki ekli tam yedek (gerçek yazıcı)."""
    birinci, ikinci = ornek_ek(owner_id="3"), ornek_ek(b"%PDF-1.7\nikinci ek\n", owner_id="9")
    kaynak = ds.dizin_kur(tmp_path / "kaynak-depo")
    depoya_koy(kaynak, birinci, ikinci)
    goruntu = ekli_sqlite(
        tmp_path / "goruntu.sqlite3",
        (birinci, ikinci),
        hesaplar=[HesapSatiri(TEST_HESAP_ID, TEST_TANITICI)],
        isaret="yeni",
    )
    tam_yedek_kur(hedef, goruntu, (birinci, ikinci), kaynak)
    return birinci, ikinci


def _json_gonder(url: str, govde: dict[str, Any]) -> Any:
    """Ham JSON: istemcinin çevirici adımı vekil karakteri kodlayamazdı, tarayıcı `\\ud83d` yollar."""
    return APIClient().post(url, json.dumps(govde), content_type="application/json")


def _geri_yukle(yol: Path | str, **alanlar: Any) -> Any:
    return _json_gonder(GERI_YUKLE_URL, {"yol": str(yol), "password": TEST_PAROLA, **alanlar})


def _baslik(yol: Path | str) -> Any:
    return _json_gonder(BASLIK_URL, {"yol": str(yol)})


def _dosya_izi(yol: Path) -> tuple[bytes, int, str]:
    """Baytlar, değişme zamanı, ad; `Path.open`'ı izleyen sahteye takılmaz."""
    with io.open(yol, "rb") as dosya:  # noqa: UP020 — bilerek `Path.open` değil
        return dosya.read(), yol.stat().st_mtime_ns, yol.name


def _artiklar(ortam: dict[str, Path]) -> list[str]:
    """Geri yüklemenin geçici dosyaları: `.yeni.tmp` ve hazırlık dizinleri."""
    bulunan = [yol.name for yol in ortam["db"].parent.glob("*.tmp*")]
    if ortam["depo"].is_dir():
        bulunan += [yol.name for yol in ortam["depo"].glob(f"{ds.HAZIRLIK_ONEKI}*")]
    return bulunan


# ---------------------------------------------------------------------------
# Yoldan geri yükleme
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bicim", ["json", "multipart"])
def test_yoldan_geri_yukleme_kapiyi_kurar_kaynaga_dokunmaz(
    bicim: str, tmp_path: Path, ortam: dict[str, Path], usb: Path
) -> None:
    ortam["db"].write_bytes(_sqlite(tmp_path, "eski"))
    kaynak = usb / SERBEST_AD
    _yerel_yedek(kaynak, tmp_path)
    once = _dosya_izi(kaynak)

    yanit = APIClient().post(
        GERI_YUKLE_URL, {"yol": str(kaynak), "password": TEST_PAROLA}, format=bicim
    )

    assert yanit.status_code == 200, yanit.json()
    assert yanit.json()["restart_required"] is True
    assert restart_gate.restart_required() is True
    assert _dosya_izi(kaynak) == once
    assert sorted(yol.name for yol in usb.iterdir()) == [SERBEST_AD]
    assert str(usb) not in yanit.content.decode("utf-8")
    # Bu kolda gövde küçüktür: yükleme işleyicisi çalışmaz, yedek dizinine geçici dosya inmez.
    assert list(app_password.backup_dir().glob(f"{live_restore.YUKLEME_ONEKI}*")) == []


def test_yol_kurtarma_anahtariyla_da_gecer(
    tmp_path: Path, ortam: dict[str, Path], usb: Path
) -> None:
    ortam["db"].write_bytes(_sqlite(tmp_path, "eski"))
    kaynak = usb / PROGRAM_ADI
    _yerel_yedek(kaynak, tmp_path)

    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {"yol": str(kaynak), "recovery_key": TEST_KURTARMA_ANAHTARI},
        format="json",
    )

    assert yanit.status_code == 200, yanit.json()


def test_yanlis_parolada_kaynak_ve_hedef_yerinde_kalir(
    tmp_path: Path, ortam: dict[str, Path], usb: Path, kapi: bakim.BakimKapisi
) -> None:
    eski = _sqlite(tmp_path, "eski")
    ortam["db"].write_bytes(eski)
    kaynak = usb / PROGRAM_ADI
    _yerel_yedek(kaynak, tmp_path)
    once = _dosya_izi(kaynak)

    yanit = _geri_yukle(kaynak, password="Yanlis-Parola-9")

    assert yanit.status_code == 400
    assert _dosya_izi(kaynak) == once
    assert ortam["db"].read_bytes() == eski
    assert kapi.bakimda is False
    assert restart_gate.restart_required() is False


def test_ikinci_onayda_ayni_yol_yeniden_gelir_kaynak_silinmez(
    tmp_path: Path, ortam: dict[str, Path], usb: Path
) -> None:
    """Onay durumsuzdur: ilk ret kaynağa dokunmaz, aynı yol bayrakla yeniden gelir."""
    saglam, bozuk = ornek_ek(owner_id="3"), ornek_ek(owner_id="9")
    depo = ds.dizin_kur(tmp_path / "bozuk-depo")
    depoya_koy(depo, saglam, bozuk)
    baytlar = bytearray((depo / bozuk.ad).read_bytes())
    baytlar[-1] ^= 1
    (depo / bozuk.ad).write_bytes(baytlar)
    goruntu = ekli_sqlite(
        tmp_path / "bozuk.sqlite3",
        (saglam, bozuk),
        hesaplar=[HesapSatiri(TEST_HESAP_ID, TEST_TANITICI)],
        isaret="yeni",
    )
    kaynak = usb / SERBEST_AD
    tam_yedek_kur(kaynak, goruntu, (saglam, bozuk), depo)
    ortam["db"].write_bytes(_sqlite(tmp_path, "eski"))
    once = _dosya_izi(kaynak)

    ilk = _geri_yukle(kaynak)
    ikinci = _geri_yukle(kaynak, ekler_olmadan_surdur=True)

    assert ilk.status_code == 409
    assert ilk.json()["code"] == "ek_onayi_gerekli"
    assert ikinci.status_code == 200, ikinci.json()
    assert ikinci.json()["dosya_raporu"]["onayla_suruldu"] == 1
    assert _dosya_izi(kaynak) == once


@pytest.mark.parametrize(
    ("ad", "beklenen"),
    [(PROGRAM_ADI, PROGRAM_ADI), (SERBEST_AD, None)],
    ids=["program_adi", "serbest_ad"],
)
def test_kayda_yalniz_programin_adi_gecer_yol_gecmez(
    ad: str,
    beklenen: str | None,
    tmp_path: Path,
    ortam: dict[str, Path],
    usb: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    ortam["db"].write_bytes(_sqlite(tmp_path, "eski"))
    kaynak = usb / ad
    _yerel_yedek(kaynak, tmp_path)

    with caplog.at_level(logging.DEBUG):
        assert _geri_yukle(kaynak).status_code == 200

    not_dosyasi = ortam["veri"] / geri_yukleme_notu.DOSYA_ADI
    metin = not_dosyasi.read_text(encoding="utf-8")
    (kayit,) = json.loads(metin)["geri_yuklemeler"]
    assert kayit["yedek"] == beklenen
    assert str(usb) not in metin
    assert UYDURMA_KISI not in metin
    assert UYDURMA_KISI not in caplog.text


# ---------------------------------------------------------------------------
# Kaynak: tam olarak biri
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "alanlar",
    [
        {},
        {"yol": ""},
        {"name": "gunluk.odbak", "yol": "/uydurma/yedek.odbak"},
    ],
    ids=["hicbiri", "bos_yol", "ad_ve_yol"],
)
def test_kaynak_tam_olarak_biri_olmali(
    alanlar: dict[str, str], ortam: dict[str, Path], kapi: bakim.BakimKapisi
) -> None:
    ortam["db"].write_bytes(b"onceki")

    yanit = APIClient().post(GERI_YUKLE_URL, {**alanlar, "password": TEST_PAROLA}, format="json")

    assert yanit.status_code == 400
    assert yanit.json()["message"] == KAYNAK_ILETISI
    assert ortam["db"].read_bytes() == b"onceki"
    assert kapi.bakimda is False


def test_dosya_ve_yol_birlikte_verilemez(ortam: dict[str, Path], usb: Path) -> None:
    kaynak = usb / PROGRAM_ADI
    kaynak.write_bytes(b"uydurma")

    yanit = APIClient().post(
        GERI_YUKLE_URL,
        {
            "file": SimpleUploadedFile("elden.odbak", b"uydurma"),
            "yol": str(kaynak),
            "password": TEST_PAROLA,
        },
        format="multipart",
    )

    assert yanit.status_code == 400
    assert yanit.json()["message"] == KAYNAK_ILETISI
    assert kaynak.read_bytes() == b"uydurma"


# ---------------------------------------------------------------------------
# Yolun denetimi: iki uç da aynı işlevden geçer
# ---------------------------------------------------------------------------
def _nul(usb: Path) -> str:
    return f"{usb}/yedek\0.odbak"


def _goreli(_usb: Path) -> str:
    return f"{UYDURMA_KISI}/yedek.odbak"


def _yok(usb: Path) -> str:
    return str(usb / "olmayan.odbak")


def _ust_yok(usb: Path) -> str:
    return str(usb / "cikarilmis" / "yedek.odbak")


def _dizin(usb: Path) -> str:
    dizin = usb / "klasor.odbak"
    dizin.mkdir()
    return str(dizin)


def _fifo(usb: Path) -> str:
    yol = usb / "boru.odbak"
    os.mkfifo(yol)
    return str(yol)


def _aygit(_usb: Path) -> str:
    return "/dev/null"


def _vekil_karakter(usb: Path) -> str:
    return f"{usb}/yedek\ud83d.odbak"


def _bosluktan_ibaret(_usb: Path) -> str:
    return "   "


GECERSIZ_YOLLAR = [
    pytest.param(_nul, id="nul"),
    pytest.param(_goreli, id="goreli"),
    pytest.param(_yok, id="bulunamayan"),
    pytest.param(_ust_yok, id="ust_dizin_yok"),
    pytest.param(_dizin, id="dizin"),
    pytest.param(
        _fifo, id="fifo", marks=pytest.mark.skipif(os.name != "posix", reason="FIFO yalnız POSIX")
    ),
    pytest.param(
        _aygit, id="aygit", marks=pytest.mark.skipif(os.name != "posix", reason="POSIX aygıtı")
    ),
    pytest.param(_vekil_karakter, id="vekil_karakter"),
    pytest.param(_bosluktan_ibaret, id="bosluk"),
]


def _yanitta_yol_yok(yanit: Any, *parcalar: str) -> None:
    metin = yanit.content.decode("utf-8")
    assert all(parca not in metin for parca in parcalar), metin


@pytest.mark.parametrize("kur", GECERSIZ_YOLLAR)
def test_gecersiz_yolda_geri_yukleme_sabit_iletiyle_reddedilir(
    kur: Callable[[Path], str],
    ortam: dict[str, Path],
    usb: Path,
    kapi: bakim.BakimKapisi,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    ortam["db"].write_bytes(b"onceki")
    bakima_alma: list[Any] = []
    monkeypatch.setattr(kapi, "bakima_al", lambda **anahtarlar: bakima_alma.append(anahtarlar))

    with caplog.at_level(logging.DEBUG):
        yanit = _geri_yukle(kur(usb))

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ILETI
    _yanitta_yol_yok(yanit, str(usb), UYDURMA_KISI)
    assert UYDURMA_KISI not in caplog.text
    assert bakima_alma == []
    assert ortam["db"].read_bytes() == b"onceki"
    assert restart_gate.restart_required() is False


@pytest.mark.parametrize("kur", GECERSIZ_YOLLAR)
def test_gecersiz_yolda_baslik_ayni_sabit_iletiyle_reddedilir(
    kur: Callable[[Path], str], usb: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        yanit = _baslik(kur(usb))

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ILETI
    _yanitta_yol_yok(yanit, str(usb), UYDURMA_KISI)
    assert UYDURMA_KISI not in caplog.text


def test_goreli_yol_var_olan_dosyayi_gosterse_de_reddedilir(
    tmp_path: Path, usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sunucunun çalışma dizini kullanıcının seçtiği yer değildir."""
    _yerel_yedek(usb / PROGRAM_ADI, tmp_path)
    monkeypatch.chdir(usb)

    yanit = _baslik(PROGRAM_ADI)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ILETI


def test_okunamayan_dosyada_gunluge_yalniz_hatanin_turu_yazilir(
    usb: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    kaynak = usb / PROGRAM_ADI
    kaynak.write_bytes(b"uydurma")

    def izin_yok(yol: Any, *_a: Any, **_k: Any) -> int:
        raise PermissionError(errno.EACCES, "Erişim engellendi", str(yol))

    monkeypatch.setattr(os, "open", izin_yok)

    with caplog.at_level(logging.DEBUG):
        yanit = _baslik(kaynak)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ILETI
    assert "PermissionError" in caplog.text
    assert UYDURMA_KISI not in caplog.text
    _yanitta_yol_yok(yanit, UYDURMA_KISI)


def test_yol_alani_metin_degilse_ayni_ileti_doner() -> None:
    yanit = _json_gonder(BASLIK_URL, {"yol": ["/uydurma/yedek.odbak"]})

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ILETI


@pytest.mark.skipif(os.name != "posix", reason="sembolik bağ")
def test_sembolik_bag_izlenir_kaynak_yine_okunur(tmp_path: Path, usb: Path) -> None:
    """Pardus'ta bellek bağla gösterilebilir: kaynak yalnız okunur, bağı kullanıcı seçmiştir."""
    asil = usb / PROGRAM_ADI
    _yerel_yedek(asil, tmp_path)
    bag = usb / "bag.odbak"
    bag.symlink_to(asil)

    govde = _baslik(bag).json()

    assert govde["name"] == "bag.odbak"
    assert govde["kapsam"] == "yerel"


# ---------------------------------------------------------------------------
# Yetki kapıları: yol kaynağı öteki kaynaklarla aynı
# ---------------------------------------------------------------------------
def test_yol_kaynaginda_rol_yetkisi_gecerlidir(
    tmp_path: Path, ortam: dict[str, Path], usb: Path, kapi: bakim.BakimKapisi
) -> None:
    ortam["db"].write_bytes(b"onceki")
    kaynak = usb / PROGRAM_ADI
    _yerel_yedek(kaynak, tmp_path)
    oturumu_ac_test(tanitici="muhasip", rol="muhasip")

    yanit = _geri_yukle(kaynak)

    assert yanit.status_code == 403
    assert yanit.json()["code"] == "rol_yetkisiz"
    assert ortam["db"].read_bytes() == b"onceki"
    assert kapi.bakimda is False


def test_yol_kaynaginda_parola_oturum_ister(
    tmp_path: Path, ortam: dict[str, Path], usb: Path, kapi: bakim.BakimKapisi
) -> None:
    kaynak = usb / PROGRAM_ADI
    _yerel_yedek(kaynak, tmp_path)

    with yazar_olarak(None), pytest.raises(live_restore.LiveRestoreError) as hata:
        live_restore.restore_and_require_restart(yol=str(kaynak), password=TEST_PAROLA)

    assert str(hata.value) == live_restore.PAROLA_YOLU_OTURUM_ISTER
    assert kapi.bakimda is False


# ---------------------------------------------------------------------------
# Kaynak USB'de: ne zaman, kaç kez okunur; bellek çıkarılırsa
# ---------------------------------------------------------------------------
class _IzlenenAkis:
    """Gerçek dosyanın önüne geçer, okunan baytları sayar; `sinir`'e varınca kesilir.

    `hata` doğruysa sınırı geçen okuma `OSError` verir (bellek çıkarıldı), değilse dosya orada
    bitmiş gibi davranır (kısalan dosya). `kapanis_hatasi` kapatırken `OSError` verir.
    """

    def __init__(
        self,
        gercek: Any,
        *,
        sinir: int | None = None,
        hata: bool = True,
        kapanis_hatasi: bool = False,
        okumadan_once: Callable[[], None] = lambda: None,
    ) -> None:
        self._gercek = gercek
        self._sinir = sinir
        self._hata = hata
        self._kapanis_hatasi = kapanis_hatasi
        self._okumadan_once = okumadan_once
        self.okunan = 0

    def read(self, boy: int = -1) -> bytes:
        self._okumadan_once()
        if self._sinir is not None:
            konum = self._gercek.tell()
            if self._hata and (boy < 0 or konum + boy > self._sinir):
                raise OSError(errno.EIO, "Girdi/çıktı hatası", f"/media/{UYDURMA_KISI}/yedek")
            if not self._hata:
                boy = max(0, min(boy, self._sinir - konum))
        parca = cast("bytes", self._gercek.read(boy))
        self.okunan += len(parca)
        return parca

    def seek(self, konum: int, nereden: int = 0) -> int:
        return cast("int", self._gercek.seek(konum, nereden))

    def tell(self) -> int:
        return cast("int", self._gercek.tell())

    def fileno(self) -> int:
        return cast("int", self._gercek.fileno())

    def __enter__(self) -> _IzlenenAkis:
        return self

    def __exit__(self, *_hata: object) -> None:
        self.close()

    def close(self) -> None:
        self._gercek.close()
        if self._kapanis_hatasi:
            raise OSError(errno.EIO, "Girdi/çıktı hatası", f"/media/{UYDURMA_KISI}/yedek")


def _izle(monkeypatch: pytest.MonkeyPatch, kaynak: Path, **secenekler: Any) -> list[_IzlenenAkis]:
    """`kaynak`'ın her açılışını izlenen akışla sarar; açılan akışları sırayla döndürür."""
    acilanlar: list[_IzlenenAkis] = []
    asil = pathlib.Path.open

    def ac(self: Path, *args: Any, **kwargs: Any) -> Any:
        gercek = asil(self, *args, **kwargs)
        if self != kaynak:
            return gercek
        akis = _IzlenenAkis(gercek, **secenekler)
        acilanlar.append(akis)
        return akis

    monkeypatch.setattr(pathlib.Path, "open", ac)
    return acilanlar


def test_cekirdek_kaynagi_bir_kez_acar_bastan_sona_bir_kez_okur(
    tmp_path: Path, ortam: dict[str, Path], usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ortam["db"].write_bytes(_sqlite(tmp_path, "eski"))
    kaynak = usb / PROGRAM_ADI
    _tam_yedek(kaynak, tmp_path)
    acilanlar = _izle(monkeypatch, kaynak)

    yanit = _geri_yukle(kaynak)

    assert yanit.status_code == 200, yanit.json()
    (akis,) = acilanlar
    # `_kabi_tani`'nın imza okuması geri sarılır; öteki her bayt bir kez okunur.
    assert akis.okunan == kaynak.stat().st_size + len(backup_restore.SQLITE_MAGIC)


def test_ilk_kalici_degisiklikten_sonra_kaynak_bir_daha_okunmaz(
    tmp_path: Path, ortam: dict[str, Path], usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ortam["db"].write_bytes(_sqlite(tmp_path, "eski"))
    kaynak = usb / PROGRAM_ADI
    _tam_yedek(kaynak, tmp_path)
    yerlesim = {"basladi": False}

    def okuma_izni() -> None:
        assert not yerlesim["basladi"], "yerleşim başladıktan sonra kaynaktan okundu"

    acilanlar = _izle(monkeypatch, kaynak, okumadan_once=okuma_izni)
    asil_yerlesim = EkYerlesimi.yerine_koy

    def yerine_koy(self: EkYerlesimi) -> None:  # depoya ilk taşıma; takas bundan da sonradır
        yerlesim["basladi"] = True
        asil_yerlesim(self)

    monkeypatch.setattr(EkYerlesimi, "yerine_koy", yerine_koy)

    yanit = _geri_yukle(kaynak)

    assert yanit.status_code == 200, yanit.json()
    assert yerlesim["basladi"] is True
    assert len(acilanlar) == 1


def _kesme_noktalari(kaynak: Path) -> dict[str, int]:
    baslik = kap_basligini_oku(kaynak)
    bolum = baslik.dosya_bolumu_konumu
    return {
        "baslik": 20,
        "muhurlu_bolum": len(baslik.aad) + 5,
        "ek_basi": bolum + 3,
        "ek_govdesi": bolum + 40 + 3,
        "son_isaret": kaynak.stat().st_size - 3,
    }


def _degismedi(
    ortam: dict[str, Path],
    kapi: bakim.BakimKapisi,
    kaynak: Path,
    once: tuple[bytes, int, str],
    eski: bytes,
) -> None:
    assert ortam["db"].read_bytes() == eski
    assert kapi.bakimda is False
    assert restart_gate.restart_required() is False
    assert crypto.is_unlocked() is True
    assert _artiklar(ortam) == []
    assert list(ortam["depo"].glob("[0-9a-f]*")) == []
    assert _dosya_izi(kaynak) == once


@pytest.mark.parametrize(
    "nokta", ["baslik", "muhurlu_bolum", "ek_basi", "ek_govdesi", "son_isaret"]
)
def test_bellek_cikarilirsa_hedefe_dokunulmaz_sabit_ileti_gider(
    nokta: str,
    tmp_path: Path,
    ortam: dict[str, Path],
    usb: Path,
    kapi: bakim.BakimKapisi,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    eski = _sqlite(tmp_path, "eski")
    ortam["db"].write_bytes(eski)
    kaynak = usb / PROGRAM_ADI
    _tam_yedek(kaynak, tmp_path)
    once = _dosya_izi(kaynak)
    _izle(monkeypatch, kaynak, sinir=_kesme_noktalari(kaynak)[nokta])

    with caplog.at_level(logging.DEBUG):
        yanit = _geri_yukle(kaynak)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == YEDEK_OKUNAMADI
    assert UYDURMA_KISI not in caplog.text
    _degismedi(ortam, kapi, kaynak, once, eski)


@pytest.mark.parametrize(
    ("nokta", "ileti"),
    [
        ("baslik", "Dosya geçerli bir OAB Defteri yedeği değil."),
        ("muhurlu_bolum", YEDEK_OKUNAMADI),
        ("ek_basi", "Yedeğin ekleri taşıyan bölümü bozuk ya da eksik; bu yedek geri yüklenemez."),
        (
            "ek_govdesi",
            "Yedeğin ekleri taşıyan bölümü bozuk ya da eksik; bu yedek geri yüklenemez.",
        ),
        (
            "son_isaret",
            "Yedeğin ekleri taşıyan bölümü bozuk ya da eksik; bu yedek geri yüklenemez.",
        ),
    ],
)
def test_okuma_ortasinda_kisalan_dosya_hedefe_dokunmaz(
    nokta: str,
    ileti: str,
    tmp_path: Path,
    ortam: dict[str, Path],
    usb: Path,
    kapi: bakim.BakimKapisi,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eski = _sqlite(tmp_path, "eski")
    ortam["db"].write_bytes(eski)
    kaynak = usb / PROGRAM_ADI
    _tam_yedek(kaynak, tmp_path)
    once = _dosya_izi(kaynak)
    _izle(monkeypatch, kaynak, sinir=_kesme_noktalari(kaynak)[nokta], hata=False)

    yanit = _geri_yukle(kaynak)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ileti
    _degismedi(ortam, kapi, kaynak, once, eski)


def test_bellek_geri_takilinca_ayni_yol_yeniden_denenebilir(
    tmp_path: Path, ortam: dict[str, Path], usb: Path, kapi: bakim.BakimKapisi
) -> None:
    ortam["db"].write_bytes(_sqlite(tmp_path, "eski"))
    kaynak = usb / PROGRAM_ADI
    _tam_yedek(kaynak, tmp_path)
    with pytest.MonkeyPatch.context() as yama:
        _izle(yama, kaynak, sinir=_kesme_noktalari(kaynak)["ek_govdesi"])
        assert _geri_yukle(kaynak).status_code == 400

    yanit = _geri_yukle(kaynak)

    assert yanit.status_code == 200, yanit.json()
    assert yanit.json()["dosya_raporu"]["yerine_konan"] == 2


def test_hedefe_yazim_hatasi_kaynak_hatasi_sanilmaz(
    tmp_path: Path, ortam: dict[str, Path], usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Disk doluysa ileti diski söyler: yalnız kaynağın okuma hatası `YEDEK_OKUNAMADI` olur."""
    eski = _sqlite(tmp_path, "eski")
    ortam["db"].write_bytes(eski)
    kaynak = usb / PROGRAM_ADI
    _tam_yedek(kaynak, tmp_path)

    def dolu(_yol: Path, parcalar: Any) -> None:
        next(iter(parcalar))
        raise OSError(errno.ENOSPC, "Aygıtta yer yok")

    monkeypatch.setattr(ds, "akisla_yaz", dolu)

    yanit = _geri_yukle(kaynak)

    assert yanit.status_code == 400
    assert "Geri yükleme yazılamadı" in yanit.json()["message"]
    assert ortam["db"].read_bytes() == eski


def test_kaynak_kapatilamazsa_yapilmis_takas_basarili_sayilir(
    tmp_path: Path,
    ortam: dict[str, Path],
    usb: Path,
    kapi: bakim.BakimKapisi,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Takastan sonra çekirdekten hata çıkamaz: çıksaydı kapı açılır, DEK eski veride kalırdı."""
    ortam["db"].write_bytes(_sqlite(tmp_path, "eski"))
    kaynak = usb / PROGRAM_ADI
    _tam_yedek(kaynak, tmp_path)
    _izle(monkeypatch, kaynak, kapanis_hatasi=True)

    yanit = _geri_yukle(kaynak)

    assert yanit.status_code == 200, yanit.json()
    assert restart_gate.restart_required() is True
    assert kapi.bakimda is True


# ---------------------------------------------------------------------------
# `POST backups/inspect/`
# ---------------------------------------------------------------------------
def test_baslik_listedeki_satirin_aynisini_verir(tmp_path: Path, usb: Path) -> None:
    yedek_dizini = app_password.backup_dir()
    yedek_dizini.mkdir(parents=True, exist_ok=True)
    listede = yedek_dizini / PROGRAM_ADI
    _tam_yedek(listede, tmp_path)
    elde = usb / PROGRAM_ADI
    elde.write_bytes(listede.read_bytes())
    os.utime(elde, ns=(listede.stat().st_atime_ns, listede.stat().st_mtime_ns))

    yanit = _baslik(elde)

    assert yanit.status_code == 200, yanit.json()
    (satir,) = APIClient().get(LISTE_URL).json()["backups"]
    assert yanit.json() == satir
    assert set(yanit.json()) == {"name", "size", "modified_at", "kurtarma", "kapsam"}
    assert yanit.json()["kapsam"] == "tam"
    assert yanit.json()["kurtarma"]["no"] == 1


def test_baslik_yerel_yedegi_tanir_name_dosya_adidir_yol_yanitta_yok(
    tmp_path: Path, usb: Path, caplog: pytest.LogCaptureFixture
) -> None:
    kaynak = usb / SERBEST_AD
    baytlar = _yerel_yedek(kaynak, tmp_path)

    with caplog.at_level(logging.DEBUG):
        yanit = _baslik(kaynak)

    govde = yanit.json()
    assert yanit.status_code == 200, govde
    assert govde["name"] == SERBEST_AD
    assert govde["size"] == len(baytlar)
    assert govde["kapsam"] == "yerel"
    assert str(usb) not in yanit.content.decode("utf-8")
    assert UYDURMA_KISI not in caplog.text


def _bos(hedef: Path, _tmp: Path) -> None:
    hedef.write_bytes(b"")


def _cok_kisa(hedef: Path, _tmp: Path) -> None:
    hedef.write_bytes(MAGIC)


def _ikili(hedef: Path, _tmp: Path) -> None:
    hedef.write_bytes(bytes(range(256)) * 64)


def _deneme_surumu(hedef: Path, _tmp: Path) -> None:
    hedef.write_bytes(DENEME_MAGIC + bytes(200))


def _duz_sqlite(hedef: Path, tmp: Path) -> None:
    hedef.write_bytes(_sqlite(tmp, "duz"))


def _cok_buyuk_seyrek(hedef: Path, _tmp: Path) -> None:
    with hedef.open("wb") as dosya:
        dosya.truncate(5 * 1024 * 1024 * 1024)


def _kesik_kap(hedef: Path, tmp: Path) -> None:
    _yerel_yedek(hedef, tmp)
    with hedef.open("r+b") as dosya:
        dosya.truncate(hedef.stat().st_size - 1)


def _bozuk_baslik_uzunlugu(hedef: Path, _tmp: Path) -> None:
    hedef.write_bytes(MAGIC + bytes(44) + (2**32 - 1).to_bytes(4, "big") + bytes(64))


@pytest.mark.parametrize(
    "kur",
    [
        _bos,
        _cok_kisa,
        _ikili,
        _deneme_surumu,
        _duz_sqlite,
        _cok_buyuk_seyrek,
        _kesik_kap,
        _bozuk_baslik_uzunlugu,
    ],
)
def test_baslik_okunamayan_dosyada_hata_degil_null_doner(
    kur: Callable[[Path, Path], None], tmp_path: Path, usb: Path
) -> None:
    kaynak = usb / "yedek değil.odbak"
    kur(kaynak, tmp_path)

    yanit = _baslik(kaynak)

    assert yanit.status_code == 200, yanit.json()
    assert yanit.json()["kapsam"] is None
    assert yanit.json()["kurtarma"] is None
    assert yanit.json()["size"] == kaynak.stat().st_size


@pytest.mark.parametrize(
    "ham",
    [
        b"",
        b"\xff\xfe",
        b"[" * 200_000,
        b'{"surum": 2}',
        b'{"surum": 2, "kdf": {}, "kurtarma": {"salt": 1, "sarmal": 2}}',
    ],
    ids=["bos", "utf8_degil", "derin_json", "eksik_bolum", "tur_bozuk"],
)
def test_kurtarma_bolumu_kullanilamayan_yedekte_kapsam_yine_okunur(
    ham: bytes, tmp_path: Path, usb: Path
) -> None:
    kaynak = usb / "bozuk-baslik.odbak"
    kaynak.write_bytes(kap_kur(_sqlite(tmp_path, "yeni"), TEST_DEK, baslik=ham))

    govde = _baslik(kaynak).json()

    assert govde["kurtarma"] is None
    assert govde["kapsam"] == "yerel"


def test_baslik_yalniz_dosyanin_basini_okur(
    tmp_path: Path, usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kapsam ve anahtar kimliği şifreli bölüme varmadan okunur; USB'de saniyeler sürmez."""
    kaynak = usb / PROGRAM_ADI
    _tam_yedek(kaynak, tmp_path)
    baslik = kap_basligini_oku(kaynak)
    acilanlar = _izle(monkeypatch, kaynak)

    assert _baslik(kaynak).status_code == 200

    assert len(acilanlar) == 2  # anahtar kimliği ve kapsam
    assert all(akis.okunan == len(baslik.aad) for akis in acilanlar)


def test_okuma_hatasi_veren_dosyada_baslik_null_doner(
    tmp_path: Path, usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kaynak = usb / PROGRAM_ADI
    _yerel_yedek(kaynak, tmp_path)
    _izle(monkeypatch, kaynak, sinir=0)

    yanit = _baslik(kaynak)

    assert yanit.status_code == 200, yanit.json()
    assert yanit.json()["kapsam"] is None
    assert yanit.json()["kurtarma"] is None


def _utf8_olmayan_adli_yedek(dizin: Path, tmp_path: Path) -> Path:
    """Python adı vekil karakterle okur; bu karakter yanıt çizilirken kodlanamaz."""
    yol = Path(os.fsdecode(os.fsencode(dizin) + b"/" + UTF8_OLMAYAN_AD))
    _yerel_yedek(yol, tmp_path)
    return yol


@pytest.mark.skipif(os.name != "posix", reason="Ad baytları yalnız POSIX'te serbesttir")
def test_utf8_olmayan_ad_listeyi_dusurmez(tmp_path: Path) -> None:
    dizin = app_password.backup_dir()
    dizin.mkdir(parents=True, exist_ok=True)
    _yerel_yedek(dizin / PROGRAM_ADI, tmp_path)
    _utf8_olmayan_adli_yedek(dizin, tmp_path)

    yanit = APIClient().get(LISTE_URL)

    assert yanit.status_code == 200
    adlar = {satir["name"] for satir in yanit.json()["backups"]}
    assert adlar == {PROGRAM_ADI, UTF8_OLMAYAN_ADIN_GOSTERIMI}


@pytest.mark.skipif(os.name != "posix", reason="Ad baytları yalnız POSIX'te serbesttir")
def test_utf8_olmayan_yedek_dizini_listeyi_dusurmez(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dizin = Path(os.fsdecode(os.fsencode(tmp_path) + b"/" + UTF8_OLMAYAN_AD))
    dizin.mkdir()
    monkeypatch.setattr(app_password, "backup_dir", lambda: dizin)

    yanit = APIClient().get(LISTE_URL)

    assert yanit.status_code == 200
    assert yanit.json()["backup_dir"].endswith(f"/{UTF8_OLMAYAN_ADIN_GOSTERIMI}")


@pytest.mark.skipif(os.name != "posix", reason="Ad baytları yalnız POSIX'te serbesttir")
def test_utf8_olmayan_adin_satiri_gosterim_icindir_listeden_secilemez(tmp_path: Path) -> None:
    """Kalan sınır: `?`'li ad dosyaya geri dönmez; kullanıcı dosyanın adını değiştirir."""
    dizin = app_password.backup_dir()
    dizin.mkdir(parents=True, exist_ok=True)
    _utf8_olmayan_adli_yedek(dizin, tmp_path)

    yanit = _json_gonder(
        GERI_YUKLE_URL, {"name": UTF8_OLMAYAN_ADIN_GOSTERIMI, "password": TEST_PAROLA}
    )

    assert yanit.status_code == 400
    assert yanit.json()["message"] == (
        f"Yedek klasöründe böyle bir dosya yok: {UTF8_OLMAYAN_ADIN_GOSTERIMI}"
    )


@pytest.mark.skipif(os.name != "posix", reason="Ad baytları yalnız POSIX'te serbesttir")
def test_utf8_olmayan_adin_basligi_okunur(tmp_path: Path, usb: Path) -> None:
    yanit = _baslik(_utf8_olmayan_adli_yedek(usb, tmp_path))

    assert yanit.status_code == 200
    assert yanit.json()["name"] == UTF8_OLMAYAN_ADIN_GOSTERIMI
    assert yanit.json()["kapsam"] == "yerel"


def test_tutulamayan_zaman_satiri_dusurmez() -> None:
    bilgi = cast("os.stat_result", SimpleNamespace(st_mtime=1e20))

    assert live_restore._degisme_ani(bilgi) is None


def test_yol_sorgu_dizesinden_okunmaz(tmp_path: Path, usb: Path) -> None:
    kaynak = usb / PROGRAM_ADI
    _yerel_yedek(kaynak, tmp_path)

    yanit = APIClient().post(f"{BASLIK_URL}?yol={kaynak}", {}, format="json")

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ILETI


def test_baslik_dosyaya_dokunmaz(tmp_path: Path, usb: Path) -> None:
    kaynak = usb / PROGRAM_ADI
    _yerel_yedek(kaynak, tmp_path)
    once = _dosya_izi(kaynak)

    assert _baslik(kaynak).status_code == 200

    assert _dosya_izi(kaynak) == once
    assert sorted(yol.name for yol in usb.iterdir()) == [PROGRAM_ADI]


# ------------------------------------------------------------------ uçların kapıları
def test_baslik_ucu_kilitliyken_kapalidir(kilitli: Path, usb: Path) -> None:
    yanit = _baslik(usb / PROGRAM_ADI)

    assert yanit.status_code == 423
    assert yanit.json()["code"] == "locked"


@pytest.mark.parametrize("rol", ["muhasip", "sekreter", "baskan", "denetleme_kurulu", "mudur"])
def test_baslik_ucu_yalniz_program_yoneticisine_aciktir(
    rol: str, tmp_path: Path, usb: Path
) -> None:
    kaynak = usb / PROGRAM_ADI
    _yerel_yedek(kaynak, tmp_path)
    oturumu_ac_test(tanitici=rol, rol=rol)

    yanit = _baslik(kaynak)

    assert yanit.status_code == 403
    assert yanit.json()["code"] == "rol_yetkisiz"


@pytest.mark.django_db
@pytest.mark.parametrize("oturum", ["yok", "acik_kalmis_organ"], ids=["oturumsuz", "organ"])
def test_baslik_ucu_kayip_kilidinde_aciktir(
    oturum: str, parmak_izi_yazili: str, tmp_path: Path, usb: Path
) -> None:
    """Güvenlik dosyası kayıp ekranı yedeği listedeki gibi tanır; rol kapısı o kipte kesmez."""
    kaynak = usb / PROGRAM_ADI
    _yerel_yedek(kaynak, tmp_path)
    if oturum == "yok":
        app_password.lock()
    else:
        oturumu_ac_test(tanitici="muhasip", rol="muhasip")
    app_password.state_path().unlink()

    yanit = _baslik(kaynak)

    assert yanit.status_code == 200, yanit.json()
    assert yanit.json()["kapsam"] == "yerel"


def test_baslik_ucu_yeniden_baslat_kapisinda_kesilir(usb: Path) -> None:
    restart_gate.mark_restart_required()

    assert _baslik(usb / PROGRAM_ADI).status_code == 503


def test_baslik_ucu_get_kabul_etmez() -> None:
    """Yol gövdede gider: uçta okuma yöntemi yoktur, adres yol taşıyamaz."""
    assert APIClient().get(BASLIK_URL).status_code == 403
