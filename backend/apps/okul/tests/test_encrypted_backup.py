"""Şifreli yedeğin programca kaydedilmesi (tasarım §4.4.7, §16 R6; plan F1b-3).

Kullanıcı kararları 04.11.2026 "Şifreli yedeği program kaydeder", 05.11.2026 "Yedek alınırken bozuk
olan ek eksik sayılır" ve "Şifreli yedek yazılmadan önce her ek bir kez okunur". Yol kullanıcının
seçtiği yerdir: `usb` fixtürü onun yerine geçer, program dizinlerinin dışındadır. Uçtan uca geri
yükleme `test_tam_yedek.py`'dedir. Adlar ve içerikler uydurmadır.
"""

from __future__ import annotations

import errno
import logging
import os
import shutil
import sqlite3
import stat
from collections.abc import Callable, Iterator
from contextlib import closing
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from desktop import backup_crypto
from desktop.backup_crypto import (
    KAPSAM_TAM,
    KAPSAM_YEREL,
    MAGIC,
    BackupCryptoError,
    Manifesto,
    ManifestoGirdisi,
    baslik_oku,
    decrypt_bytes,
    dosya_bolumunu_oku,
    kap_basligini_oku,
    muhurlu_bolumu_ac,
    usable_recovery_header,
)
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import Attachment, AttachmentSensitivity, AuditTrail, SchoolYear
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password, dis_yedek, dosya_deposu, encrypted_backup
from apps.okul.services import school_year as school_year_service
from apps.okul.tests.geri_yukleme_ortak import OZGUN_AD, PDF, PNG
from conftest import KURULUM_IZI, TEST_DEK, TEST_HESAP_ID, oturumu_ac_test, varsayilan_yazar
from shared import bakim, crypto
from shared import dosya_sifreleme as ds

pytestmark = pytest.mark.django_db

URL = "/api/v1/backups/encrypted/"
AD = "oab-defteri-yedek-2026-11-06-101530.odbak"
#: Yamalanan görüntü (mühürlü bölüme girer; test veritabanı işlemde açıktır).
GORUNTU = b"SQLite format 3\0uydurma-kayit-icerigi"
#: Serbest adın ve seçilen yolun içinde durur: hiçbir satırda ve iletide geçmemelidir.
UYDURMA_KISI = "Uydurgul"


class _Olduruldu(BaseException):
    """Süreci kesen hata: `Exception`'dan türemez, hiçbir `except` yakalamaz."""


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def usb(tmp_path: Path) -> Path:
    """Kullanıcının seçtiği yer: program dizinlerinin dışında, adı uydurma kişi taşır."""
    yol = tmp_path / f"{UYDURMA_KISI}-usb"
    yol.mkdir()
    return yol


@pytest.fixture
def goruntu(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Görüntüyü sabitler; verilen eklerin manifestosunu kurar (`Attachment` ya da hazır girdi)."""

    def kur(*ekler: Attachment | ManifestoGirdisi) -> None:
        girdiler = tuple(
            ek
            if isinstance(ek, ManifestoGirdisi)
            else ManifestoGirdisi(ek.stored_name, ek.size, ek.sha256)
            for ek in ekler
        )
        monkeypatch.setattr(
            encrypted_backup,
            "goruntu_ve_manifesto",
            lambda _yol: (GORUNTU, Manifesto(KAPSAM_YEREL, girdiler)),
        )

    kur()
    return kur


@pytest.fixture
def sahip(monkeypatch: pytest.MonkeyPatch) -> Iterator[SchoolYear]:
    """Geçici sahip kümesi (`SchoolYear`; F1b'de küme boştur)."""
    monkeypatch.setattr(dosya_deposu, "_SAHIP_ETIKETLERI", set())
    dosya_deposu.sahip_kaydet(SchoolYear)
    yield school_year_service.create_school_year(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), activate=True
    )


def _ek(sahip: SchoolYear, acik: bytes = PDF) -> Attachment:
    return dosya_deposu.yaz(
        acik,
        original_name=OZGUN_AD,
        sensitivity=AttachmentSensitivity.NORMAL,
        owner=sahip,
        yazar=varsayilan_yazar(),
        kisi_listesi=False,
    )


def _kaydet(client: APIClient, hedef: Path | str) -> Any:
    return client.post(URL, {"hedef": str(hedef)}, format="json")


def _yedek_satirlari() -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(seq__gt=KURULUM_IZI, action="YEDEK").order_by("seq"))


def _adlar(dizin: Path) -> list[str]:
    return sorted(yol.name for yol in dizin.iterdir())


def _iz_yok_dosya_yok(dizin: Path) -> None:
    """Yedek verilmedi: seçilen yer boş, satır yok, hatırlatma sıfırlanmadı."""
    assert _adlar(dizin) == []
    assert _yedek_satirlari() == []
    assert not dis_yedek.dosya_yolu().exists()


def _bit_cevir(yol: Path, konum: int) -> None:
    baytlar = bytearray(yol.read_bytes())
    baytlar[konum] ^= 1
    yol.write_bytes(baytlar)


def _sayac_bos() -> None:
    assert bakim.UZUN_ISLER.sayi == 0
    assert bakim.KAPI.ucusta == 0
    assert not encrypted_backup._TEK_IS.locked()


# ============================================================ önerilen ad


def test_onerilen_ad_program_desenindedir_saat_yerel_saattir(
    client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tasarım §2.3.1: dosya adı saatlidir, adı sunucu önerir."""
    monkeypatch.setattr(timezone, "now", lambda: datetime(2026, 11, 6, 7, 15, 30, tzinfo=UTC))
    yanit = client.get(URL)
    assert yanit.status_code == 200
    assert yanit.json() == {"onerilen_ad": AD}
    assert denetim_izi.program_yedegi_mi(AD)


# ============================================================ kaydetme


def test_tam_yedek_secilen_yere_kaydedilir_satir_kisisiz_ozet_tasir(
    client: APIClient, usb: Path, goruntu: Callable[..., None]
) -> None:
    hedef = usb / AD

    yanit = _kaydet(client, hedef)

    assert yanit.status_code == 200
    icerik = hedef.read_bytes()
    assert yanit.json() == {
        "ad": AD,
        "boyut": len(icerik),
        "ek_sayisi": 0,
        "eksik": 0,
        "denetlendi": True,
    }
    assert yanit["Content-Type"] == "application/json"
    assert _adlar(usb) == [AD]  # geçici dosya kalmaz
    assert icerik.startswith(MAGIC)
    assert kap_basligini_oku(hedef).kapsam == KAPSAM_TAM
    assert decrypt_bytes(icerik, TEST_DEK).veritabani == GORUNTU
    assert kap_basligini_oku(hedef).kurtarma_basligi == usable_recovery_header(
        app_password.state_path().parent
    )
    if os.name == "posix":
        assert stat.S_IMODE(hedef.stat().st_mode) == backup_crypto.YEDEK_DOSYA_KIPI
    # Kullanıcının istediği yedek oturumdaki hesabın `YEDEK` satırıdır (tasarım §4.6.3).
    (satir,) = _yedek_satirlari()
    assert (satir.model, satir.object_id, satir.key_mode) == (
        denetim_izi.YEDEK_DOSYASI,
        AD,
        "ACIK",
    )
    assert str(satir.account_id) == TEST_HESAP_ID
    assert satir.values == {
        "kapsam": [None, "tam"],
        "dosya_sayisi": [None, 0],
        "boyut": [None, len(icerik)],
        "eksik": [None, 0],
    }
    assert dis_yedek.durum().son_indirme is not None
    _sayac_bos()


def test_veritabani_gorunumu_sifreli_yazilir_acik_icerik_dosyada_yoktur(
    client: APIClient, usb: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gerçek görüntü: kaynak dosya tabanlı SQLite (test veritabanı işlemde açıktır)."""
    kaynak = tmp_path / "kaynak.sqlite3"
    gizli = "ogrenci-kisisel-verisi"
    with closing(sqlite3.connect(kaynak)) as baglanti:
        baglanti.execute("CREATE TABLE kayit (deger TEXT)")
        baglanti.execute("INSERT INTO kayit VALUES (?)", (gizli,))
        baglanti.commit()
    monkeypatch.setattr(
        encrypted_backup, "settings", SimpleNamespace(DATABASES={"default": {"NAME": kaynak}})
    )

    assert _kaydet(client, usb / AD).status_code == 200

    icerik = (usb / AD).read_bytes()
    assert gizli.encode() not in icerik
    acilan = decrypt_bytes(icerik, TEST_DEK).veritabani
    assert acilan.startswith(b"SQLite format 3") and gizli.encode() in acilan


def test_ekler_sifreli_baytlariyla_aynen_kopyalanir(
    client: APIClient, usb: Path, goruntu: Callable[..., None], sahip: SchoolYear
) -> None:
    """Plan "Kap ve manifesto": ek ikinci kez şifrelenmez, açık içerik diske düşmez."""
    birinci, ikinci = _ek(sahip, PDF), _ek(sahip, PNG)
    goruntu(birinci, ikinci)
    depo = dosya_deposu.depo_dizini()

    yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 200
    assert (yanit.json()["ek_sayisi"], yanit.json()["eksik"]) == (2, 0)
    (satir,) = _yedek_satirlari()
    assert satir.values["dosya_sayisi"] == [None, 2]
    icerik = (usb / AD).read_bytes()
    assert PDF not in icerik and PNG not in icerik
    with (usb / AD).open("rb") as akis:
        baslik = baslik_oku(akis, len(icerik))
        manifesto = muhurlu_bolumu_ac(akis, baslik, TEST_DEK).manifesto
        assert manifesto.kapsam == KAPSAM_TAM
        for bolum in dosya_bolumunu_oku(akis, manifesto):
            assert b"".join(bolum.parcalar()) == (depo / bolum.girdi.ad).read_bytes()


def test_sira_on_okuma_yazim_denetim_satir_asil_ad_hatirlatma(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kullanıcı kararı 04.11.2026: satır denetimden sonra, hatırlatma asıl addan sonradır."""
    hedef = usb / AD
    sira: list[tuple[str, bool]] = []

    def izle(sahibi: Any, ad: str, etiket: str) -> None:
        asil = getattr(sahibi, ad)

        def sar(*a: Any, **k: Any) -> Any:
            sira.append((etiket, hedef.exists()))
            return asil(*a, **k)

        monkeypatch.setattr(sahibi, ad, sar)

    for ad, etiket in (
        ("_yer_denetle", "yer"),
        ("_ekleri_on_oku", "on_okuma"),
        ("tam_yedek_yaz", "yazim"),
        ("_yazilani_denetle", "denetim"),
        ("_satiri_yaz", "satir"),
    ):
        izle(encrypted_backup, ad, etiket)
    izle(encrypted_backup, "_asil_adi_ver", "asil_ad")
    izle(dis_yedek, "indirme_kaydet", "hatirlatma")

    assert _kaydet(client, hedef).status_code == 200

    assert sira == [
        ("yer", False),
        ("on_okuma", False),
        ("yazim", False),
        ("denetim", False),
        ("satir", False),
        ("asil_ad", False),
        ("hatirlatma", True),
    ]


def test_gecici_ad_programa_ozgudur_kullanicinin_adindan_turemez(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    gorulen: list[Path] = []
    asil = backup_crypto.tam_yedek_yaz

    def sar(target: Path, *a: Any, **k: Any) -> Manifesto:
        gorulen.append(target)
        sonuc = asil(target, *a, **k)
        if os.name == "posix":
            assert stat.S_IMODE(target.stat().st_mode) == backup_crypto.YEDEK_DOSYA_KIPI
        return sonuc

    monkeypatch.setattr(encrypted_backup, "tam_yedek_yaz", sar)

    assert _kaydet(client, usb / f"{UYDURMA_KISI} yedegi.odbak").status_code == 200

    (gecici,) = gorulen
    assert gecici.parent == usb
    assert gecici.name.startswith(f"{encrypted_backup.AD_ONEKI}-")
    assert gecici.name.endswith(encrypted_backup.GECICI_EK)
    assert UYDURMA_KISI not in gecici.name


def test_tahmini_boy_yedegin_boyundan_kucuk_degildir(
    client: APIClient, usb: Path, goruntu: Callable[..., None], sahip: SchoolYear
) -> None:
    ek = _ek(sahip)
    goruntu(ek)

    assert _kaydet(client, usb / AD).status_code == 200

    girdi = ManifestoGirdisi(ek.stored_name, ek.size, ek.sha256)
    assert encrypted_backup._tahmini_boy(GORUNTU, [girdi]) >= (usb / AD).stat().st_size
    # Tahmin depodaki kapları da sayar: büyük ek pay içinde kaybolmaz.
    buyuk = ManifestoGirdisi("a" * 32, 10 * 1024 * 1024, "0" * 64)
    assert encrypted_backup._tahmini_boy(GORUNTU, [buyuk]) > buyuk.sifreli_boy + len(GORUNTU)


# ============================================================ iptal ve yol denetimi


@pytest.mark.parametrize("govde", [{}, {"hedef": ""}])
def test_iptalde_hicbir_sey_yazilmaz(
    client: APIClient, usb: Path, monkeypatch: pytest.MonkeyPatch, govde: dict[str, str]
) -> None:
    """Kullanıcı kararı 04.11.2026: yol gelmezse görüntü bile alınmaz."""

    def alinmamali(_yol: Path) -> None:
        raise AssertionError("görüntü alınmamalıydı")

    monkeypatch.setattr(encrypted_backup, "goruntu_ve_manifesto", alinmamali)

    yanit = client.post(URL, govde, format="json")

    assert yanit.status_code == 400
    assert yanit.json()["message"] == encrypted_backup.YER_SECILMEDI
    _iz_yok_dosya_yok(usb)


def _goreli(_usb: Path) -> str:
    return AD


def _ust_dizin_adimi(usb: Path) -> str:
    (usb / "alt").mkdir()
    return f"{usb}/alt/../{AD}"


def _ust_dizin_yok(usb: Path) -> str:
    return str(usb / "olmayan" / AD)


def _ust_dizin_dosya(usb: Path) -> str:
    (usb / "dosya").write_bytes(b"x")
    return str(usb / "dosya" / AD)


def _veri_dizini(_usb: Path) -> str:
    return str(app_password.state_path().parent / AD)


def _veri_dizininin_alti(_usb: Path) -> str:
    alt = app_password.state_path().parent / "alt"
    alt.mkdir()
    return str(alt / AD)


def _yedek_dizini(_usb: Path) -> str:
    return str(app_password.backup_dir() / AD)


def _dosya_deposu(_usb: Path) -> str:
    return str(ds.dizin_kur(dosya_deposu.depo_dizini()) / AD)


def _baga_gizlenmis_veri_dizini(usb: Path) -> str:
    (usb / "bag").symlink_to(app_password.state_path().parent, target_is_directory=True)
    return str(usb / "bag" / AD)


def _uzantisiz(usb: Path) -> str:
    return str(usb / "yedek")


def _baska_uzanti(usb: Path) -> str:
    return str(usb / "yedek.odbak.zip")


def _buyuk_harfli_uzanti(usb: Path) -> str:
    return str(usb / "YEDEK.ODBAK")


def _yalniz_uzanti(usb: Path) -> str:
    return str(usb / ".odbak")


def _hedef_dizin(usb: Path) -> str:
    (usb / AD).mkdir()
    return str(usb / AD)


def _hedef_sembolik_bag(usb: Path) -> str:
    (usb / "baska.dosya").write_bytes(b"dokunulmamali")
    (usb / AD).symlink_to(usb / "baska.dosya")
    return str(usb / AD)


def _hedef_kirik_bag(usb: Path) -> str:
    (usb / AD).symlink_to(usb / "yok.dosya")
    return str(usb / AD)


def _hedef_fifo(usb: Path) -> str:
    os.mkfifo(usb / AD)
    return str(usb / AD)


@pytest.mark.parametrize(
    ("kur", "ileti"),
    [
        (_goreli, encrypted_backup.YER_KULLANILAMIYOR),
        (_ust_dizin_adimi, encrypted_backup.YER_KULLANILAMIYOR),
        (_ust_dizin_yok, encrypted_backup.YER_KULLANILAMIYOR),
        (_ust_dizin_dosya, encrypted_backup.YER_KULLANILAMIYOR),
        (_uzantisiz, encrypted_backup.UZANTI_DEGISMIS),
        (_baska_uzanti, encrypted_backup.UZANTI_DEGISMIS),
        (_buyuk_harfli_uzanti, encrypted_backup.UZANTI_DEGISMIS),
        (_yalniz_uzanti, encrypted_backup.UZANTI_DEGISMIS),
        (_veri_dizini, encrypted_backup.PROGRAM_KLASORU),
        (_veri_dizininin_alti, encrypted_backup.PROGRAM_KLASORU),
        (_yedek_dizini, encrypted_backup.PROGRAM_KLASORU),
        (_dosya_deposu, encrypted_backup.PROGRAM_KLASORU),
        pytest.param(
            _baga_gizlenmis_veri_dizini,
            encrypted_backup.PROGRAM_KLASORU,
            marks=pytest.mark.skipif(os.name != "posix", reason="sembolik bağ"),
        ),
        (_hedef_dizin, encrypted_backup.DOSYA_DEGIL),
        pytest.param(
            _hedef_sembolik_bag,
            encrypted_backup.DOSYA_DEGIL,
            marks=pytest.mark.skipif(os.name != "posix", reason="sembolik bağ"),
        ),
        pytest.param(
            _hedef_kirik_bag,
            encrypted_backup.DOSYA_DEGIL,
            marks=pytest.mark.skipif(os.name != "posix", reason="sembolik bağ"),
        ),
        pytest.param(
            _hedef_fifo,
            encrypted_backup.DOSYA_DEGIL,
            marks=pytest.mark.skipif(os.name != "posix", reason="FIFO"),
        ),
    ],
)
def test_sunucu_yola_guvenmez(
    client: APIClient,
    usb: Path,
    monkeypatch: pytest.MonkeyPatch,
    kur: Callable[[Path], str],
    ileti: str,
) -> None:
    """Plan F1b-3: reddedilen yolda görüntü alınmaz, hiçbir yere bir şey yazılmaz."""

    def alinmamali(_yol: Path) -> None:
        raise AssertionError("görüntü alınmamalıydı")

    monkeypatch.setattr(encrypted_backup, "goruntu_ve_manifesto", alinmamali)
    hedef = kur(usb)
    once = _adlar(usb)
    veri = app_password.state_path().parent
    veri_once = _adlar(veri)
    yedekler_once = _adlar(app_password.backup_dir())

    yanit = _kaydet(client, hedef)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ileti
    assert str(usb) not in yanit.content.decode("utf-8")
    assert _adlar(usb) == once
    assert _adlar(veri) == veri_once
    assert _adlar(app_password.backup_dir()) == yedekler_once
    assert _yedek_satirlari() == []
    _sayac_bos()


@pytest.mark.skipif(os.name != "posix", reason="sembolik bağ")
@pytest.mark.parametrize("alt", ["", "alt"], ids=["kok", "alt_dizin"])
@pytest.mark.parametrize(
    "kok_bul",
    [lambda: app_password.state_path().parent, app_password.backup_dir, dosya_deposu.depo_dizini],
    ids=["veri", "yedek", "depo"],
)
def test_program_klasorunun_baska_yazimi_da_reddedilir(
    usb: Path, monkeypatch: pytest.MonkeyPatch, kok_bul: Callable[[], Path], alt: str
) -> None:
    r"""Windows'ta `resolve` `\\?\C:\...` önekini korur, metin karşılaştırması yazımı görmez.

    Docker'da o yazımın yerini çözülmemiş sembolik bağ tutar: yol metinde dışarıdadır, dosya
    kimliği içeridedir.
    """
    kok = kok_bul()
    (kok / alt).mkdir(parents=True, exist_ok=True)
    baska_yazim = usb / "baska-yazim"
    baska_yazim.symlink_to(kok, target_is_directory=True)
    monkeypatch.setattr(Path, "resolve", lambda self, strict=False: self)

    with pytest.raises(encrypted_backup.EncryptedBackupError) as hata:
        encrypted_backup._hedef_denetle(str(baska_yazim / alt / AD))

    assert str(hata.value) == encrypted_backup.PROGRAM_KLASORU


def test_dosya_kimligi_baska_dizini_ve_olmayan_koku_icinde_saymaz(
    usb: Path, tmp_path: Path
) -> None:
    """Kök henüz yoksa (dosya deposu ilk ekle doğar) denetim düşmez, o aday atlanır."""
    kok = tmp_path / "program"
    kok.mkdir()
    komsu = tmp_path / "program-komsu"
    komsu.mkdir()

    assert not encrypted_backup._icinde_mi(komsu, kok)
    assert not encrypted_backup._icinde_mi(usb, tmp_path / "olmayan-kok")


def test_sembolik_bag_izlenmez_gosterdigi_dosya_degismez(client: APIClient, usb: Path) -> None:
    if os.name != "posix":
        pytest.skip("sembolik bağ")
    hedef = _hedef_sembolik_bag(usb)

    assert _kaydet(client, hedef).status_code == 400

    assert (usb / "baska.dosya").read_bytes() == b"dokunulmamali"
    assert (usb / AD).is_symlink()


def test_nul_bayti_tasiyan_yol_reddedilir(usb: Path) -> None:
    with pytest.raises(encrypted_backup.EncryptedBackupError, match="kullanılamıyor"):
        encrypted_backup.sifreli_yedegi_kaydet(f"{usb}/{AD}\0.odbak")


def test_hedefteki_duzenli_dosya_yenisi_denetimden_gecince_degisir(
    client: APIClient, usb: Path, goruntu: Callable[..., None]
) -> None:
    """Pencere üzerine yazmayı kullanıcıya sormuştur; eski dosya sona kadar yerinde durur."""
    (usb / AD).write_bytes(b"eski yedek")

    assert _kaydet(client, usb / AD).status_code == 200

    assert (usb / AD).read_bytes().startswith(MAGIC)
    assert _adlar(usb) == [AD]


def test_hedefteki_dosya_denetim_duserse_yerinde_kalir(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    (usb / AD).write_bytes(b"eski yedek")
    _yazimdan_sonra(monkeypatch, lambda gecici: _bit_cevir(gecici, 50))

    assert _kaydet(client, usb / AD).status_code == 400

    assert (usb / AD).read_bytes() == b"eski yedek"
    assert _adlar(usb) == [AD]


# ============================================================ denetim


def _yazimdan_sonra(monkeypatch: pytest.MonkeyPatch, boz: Callable[[Path], None]) -> None:
    """Yazılan dosyayı denetimden hemen önce diskte değiştirir."""
    asil = backup_crypto.tam_yedek_yaz

    def sar(target: Path, *a: Any, **k: Any) -> Manifesto:
        sonuc = asil(target, *a, **k)
        boz(target)
        return sonuc

    monkeypatch.setattr(encrypted_backup, "tam_yedek_yaz", sar)


def _muhurlu_bolumde_bit(yol: Path) -> None:
    _bit_cevir(yol, len(kap_basligini_oku(yol).aad) + 3)


def _baslikta_bit(yol: Path) -> None:
    _bit_cevir(yol, len(MAGIC) + 2)


def _ek_govdesinde_bit(yol: Path) -> None:
    # Dosya bölümü: bitiş işaretinden hemen önceki bayt son ekin etiketindedir.
    _bit_cevir(yol, yol.stat().st_size - len(backup_crypto.DOSYA_BOLUMU_SONU) - 1)


def _ek_gorunmeden_kesik(yol: Path) -> None:
    with yol.open("r+b") as dosya:
        dosya.truncate(yol.stat().st_size - 1)


def _fazla_bayt(yol: Path) -> None:
    with yol.open("ab") as dosya:
        dosya.write(b"\0")


@pytest.mark.parametrize(
    "boz",
    [_muhurlu_bolumde_bit, _baslikta_bit, _ek_govdesinde_bit, _ek_gorunmeden_kesik, _fazla_bayt],
)
def test_denetim_duserse_dosya_kalmaz_satir_yazilmaz(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    sahip: SchoolYear,
    monkeypatch: pytest.MonkeyPatch,
    boz: Callable[[Path], None],
) -> None:
    """Denetim diskteki dosyadandır, bellekteki kopyadan değil: sonradan değişen bayt yakalanır."""
    goruntu(_ek(sahip))
    _yazimdan_sonra(monkeypatch, boz)

    yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == encrypted_backup.DENETIM_DUSTU
    _iz_yok_dosya_yok(usb)
    _sayac_bos()


def test_baska_veritabani_ya_da_manifesto_yazilmissa_denetim_duser(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    sahip: SchoolYear,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Geçerli mühürlü ama istenen içerik olmayan dosya da denetimden geçmez."""
    ek = _ek(sahip)
    goruntu(ek)
    asil = backup_crypto.tam_yedek_yaz

    def baska_veritabani(target: Path, _db: bytes, *a: Any, **k: Any) -> Manifesto:
        return asil(target, b"SQLite format 3\0baska", *a, **k)

    monkeypatch.setattr(encrypted_backup, "tam_yedek_yaz", baska_veritabani)
    assert _kaydet(client, usb / AD).json()["message"] == encrypted_backup.DENETIM_DUSTU
    _iz_yok_dosya_yok(usb)

    def baska_manifesto(target: Path, db: bytes, *a: Any, **k: Any) -> Manifesto:
        yazilan = asil(target, db, *a, **k)
        fazla = ManifestoGirdisi("b" * 32, 1, "0" * 64, eksik=True)
        return Manifesto(KAPSAM_TAM, (*yazilan.dosyalar, fazla))

    monkeypatch.setattr(encrypted_backup, "tam_yedek_yaz", baska_manifesto)
    assert _kaydet(client, usb / AD).json()["message"] == encrypted_backup.DENETIM_DUSTU
    _iz_yok_dosya_yok(usb)


def test_denetim_kapsami_tam_olmayan_kabi_reddeder(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Yazıcı yanlışlıkla yerel kap yazarsa denetim düşer (tam yedek sözü verilmiştir)."""

    def yerel_kap(target: Path, db: bytes, _g: Any, _d: Path, anahtar: Any, **k: Any) -> Manifesto:
        target.write_bytes(backup_crypto.encrypt_bytes(db, anahtar, **k))
        return Manifesto(KAPSAM_TAM)

    monkeypatch.setattr(encrypted_backup, "tam_yedek_yaz", yerel_kap)

    assert _kaydet(client, usb / AD).json()["message"] == encrypted_backup.DENETIM_DUSTU
    _iz_yok_dosya_yok(usb)


@pytest.mark.skipif(not hasattr(os, "posix_fadvise"), reason="POSIX")
def test_denetim_onbellegi_birakip_aygittan_okur(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dosya yeni yazılmıştır, sayfaları önbellektedir: bırakılmazsa denetim aygıtı görmez."""
    olaylar: list[Any] = []
    asil_baslik = baslik_oku

    def birak(fd: int, konum: int, boy: int, tavsiye: int) -> None:
        ad = Path(f"/proc/self/fd/{fd}").resolve().name
        olaylar.append(("birak", ad.endswith(encrypted_backup.GECICI_EK), konum, boy, tavsiye))

    def baslik(*a: Any, **k: Any) -> Any:
        olaylar.append("oku")
        return asil_baslik(*a, **k)

    monkeypatch.setattr(os, "posix_fadvise", birak)
    monkeypatch.setattr(encrypted_backup, "baslik_oku", baslik)

    assert _kaydet(client, usb / AD).status_code == 200

    assert olaylar == [("birak", True, 0, 0, os.POSIX_FADV_DONTNEED), "oku"]


def _birakilamaz(yama: pytest.MonkeyPatch) -> None:
    def birakilamadi(*_a: object) -> None:
        raise OSError(errno.EINVAL, "desteklenmiyor", "/gizli/yol")

    yama.setattr(os, "posix_fadvise", birakilamadi, raising=False)


def _windows_gibi(yama: pytest.MonkeyPatch) -> None:
    yama.delattr(os, "posix_fadvise", raising=False)


@pytest.mark.parametrize("kur", [_birakilamaz, _windows_gibi], ids=["hata", "yok"])
def test_onbellek_birakilamazsa_denetim_yine_kosar(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    kur: Callable[[pytest.MonkeyPatch], None],
) -> None:
    """Bırakma bir iyileştirmedir, koşul değildir; denetim sonra bozuk baytı yine yakalar."""
    kur(monkeypatch)

    with caplog.at_level(logging.DEBUG):
        assert _kaydet(client, usb / AD).status_code == 200
    assert "/gizli/yol" not in caplog.text

    _yazimdan_sonra(monkeypatch, _muhurlu_bolumde_bit)
    assert _kaydet(client, usb / "ikinci.odbak").json()["message"] == encrypted_backup.DENETIM_DUSTU


def test_satir_yazilamazsa_dosya_kalmaz_hatirlatma_sifirlanmaz(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """İzsiz yedek yoktur (tasarım §4.6.3)."""

    def yazilamadi(*_a: object, **_k: object) -> None:
        raise denetim_izi.IzYazilamadi("deneme")

    monkeypatch.setattr(denetim_izi, "olay", yazilamadi)

    yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 409
    assert yanit.json()["code"] == "iz_yazilamadi"
    _iz_yok_dosya_yok(usb)
    _sayac_bos()


def test_asil_ad_verilemezse_satir_kalir_hatirlatma_sifirlanmaz_gecici_silinir(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    gercek = os.replace

    def verilemedi(kaynak: Path, hedef: Path) -> None:
        # Yalnız yedeğin geçici dosyası düşer: `dis-yedek.json` yazılabilir kalır, aşağıdaki
        # "hatırlatma sıfırlanmaz" iddiası kod sıfırlamaya kalksa gerçekten düşer.
        if str(kaynak).endswith(encrypted_backup.GECICI_EK):
            raise PermissionError(errno.EACCES, "erişim engellendi", str(hedef))
        gercek(kaynak, hedef)

    monkeypatch.setattr(os, "replace", verilemedi)

    with caplog.at_level(logging.DEBUG):
        yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == encrypted_backup.ASIL_AD_VERILEMEDI
    assert str(usb) not in yanit.content.decode("utf-8")
    assert UYDURMA_KISI not in caplog.text
    assert len(_yedek_satirlari()) == 1
    assert not dis_yedek.dosya_yolu().exists()
    assert _adlar(usb) == []
    _sayac_bos()


def test_dizin_esitlenemezse_yedek_gecerlidir(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dosya asıl adını almıştır: hatırlatma sıfırlanır, yol günlüğe gitmez."""

    def esitlenemedi(dizin: Path) -> None:
        raise OSError(errno.EINVAL, "desteklenmiyor", str(dizin))

    monkeypatch.setattr(ds, "dizini_esitle", esitlenemedi)

    assert _kaydet(client, usb / AD).status_code == 200

    assert dis_yedek.dosya_yolu().exists()


def test_gecici_dosya_silinemezse_asil_ileti_kalir(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _yazimdan_sonra(monkeypatch, _muhurlu_bolumde_bit)
    asil_unlink = Path.unlink

    def silinemez(yol: Path, *a: Any, **k: Any) -> None:
        if yol.parent == usb:
            raise PermissionError(errno.EACCES, "erişim engellendi", str(yol))
        asil_unlink(yol, *a, **k)

    monkeypatch.setattr(Path, "unlink", silinemez)

    with caplog.at_level(logging.DEBUG):
        yanit = _kaydet(client, usb / AD)

    assert yanit.json()["message"] == encrypted_backup.DENETIM_DUSTU
    assert UYDURMA_KISI not in caplog.text


# ============================================================ ön okuma


def _depodan_sil(depo: Path, ad: str, _yama: pytest.MonkeyPatch) -> None:
    (depo / ad).unlink()


def _boyu_bozuk(depo: Path, ad: str, _yama: pytest.MonkeyPatch) -> None:
    with (depo / ad).open("ab") as dosya:
        dosya.write(b"x")


def _bit_donmus(depo: Path, ad: str, _yama: pytest.MonkeyPatch) -> None:
    _bit_cevir(depo / ad, -1)


def _disk_hatasi(_depo: Path, ad: str, yama: pytest.MonkeyPatch) -> None:
    """Dosya açılır, okunurken kötü sektöre takılır; hata tam yolu taşır."""
    asil = ds.kabi_oku

    def oku(yol: Path) -> bytes:
        if yol.name == ad:
            raise OSError(errno.EIO, "giriş çıkış hatası", str(yol))
        return asil(yol)

    yama.setattr(ds, "kabi_oku", oku)


@pytest.mark.parametrize("boz", [_depodan_sil, _boyu_bozuk, _bit_donmus, _disk_hatasi])
def test_okunamayan_ya_da_bozuk_ek_eksik_sayilir_yedek_alinir(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    sahip: SchoolYear,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    boz: Callable[[Path, str, pytest.MonkeyPatch], None],
) -> None:
    """Yedeksiz kalmak eksik ekli yedekten ağırdır (plan "Kap ve manifesto").

    Okunamayan ve boyu tutmayan ek 05.11.2026 kararlarıdır; `_bit_donmus` kolu 06.11.2026 kararıdır
    (`encrypted_backup` başlığı, 4. adım).
    """
    saglam, bozuk = _ek(sahip, PDF), _ek(sahip, PNG)
    goruntu(saglam, bozuk)
    boz(dosya_deposu.depo_dizini(), bozuk.stored_name, monkeypatch)

    with caplog.at_level(logging.DEBUG):
        yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 200
    veri = yanit.json()
    assert (veri["ek_sayisi"], veri["eksik"], veri["denetlendi"]) == (1, 1, True)
    (satir,) = _yedek_satirlari()
    assert satir.values["eksik"] == [None, 1]
    assert satir.values["dosya_sayisi"] == [None, 1]
    manifesto = decrypt_bytes((usb / AD).read_bytes(), TEST_DEK).manifesto
    assert {girdi.ad: girdi.eksik for girdi in manifesto.dosyalar} == {
        saglam.stored_name: False,
        bozuk.stored_name: True,
    }
    assert [girdi.ad for girdi in manifesto.tasinanlar] == [saglam.stored_name]
    # Yalnız sayı: depo adı ve yol günlüğe girmez.
    assert bozuk.stored_name not in caplog.text
    assert str(dosya_deposu.depo_dizini()) not in caplog.text


def test_ozeti_tutmayan_ve_satiri_olmayan_ek_eksik_sayilir(
    client: APIClient, usb: Path, goruntu: Callable[..., None], sahip: SchoolYear
) -> None:
    ek = _ek(sahip)
    satirsiz = ds.dosya_hazirla(PDF, sarmal_anahtari=b"\x11" * 32)
    ds.depoya_yaz(dosya_deposu.depo_dizini(), satirsiz.stored_name, satirsiz.kap)
    goruntu(
        ManifestoGirdisi(ek.stored_name, ek.size, "0" * 64),
        ManifestoGirdisi(satirsiz.stored_name, satirsiz.size, satirsiz.sha256),
    )

    yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 200
    assert (yanit.json()["ek_sayisi"], yanit.json()["eksik"]) == (0, 2)


def test_her_ek_yazimdan_once_bir_kez_okunur(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    sahip: SchoolYear,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ön okuma depoyu bir kez okur; denetim yazılan dosyadan yapılır, depoya dönmez."""
    birinci, ikinci = _ek(sahip, PDF), _ek(sahip, PNG)
    goruntu(birinci, ikinci)
    okunanlar: list[str] = []
    yazimda: list[list[str]] = []
    asil_oku, asil_yaz = ds.kabi_oku, backup_crypto.tam_yedek_yaz

    def oku(yol: Path) -> bytes:
        okunanlar.append(yol.name)
        return asil_oku(yol)

    def yaz(*a: Any, **k: Any) -> Manifesto:
        yazimda.append(sorted(okunanlar))
        return asil_yaz(*a, **k)

    monkeypatch.setattr(ds, "kabi_oku", oku)
    monkeypatch.setattr(encrypted_backup, "tam_yedek_yaz", yaz)

    assert _kaydet(client, usb / AD).status_code == 200

    assert sorted(okunanlar) == sorted([birinci.stored_name, ikinci.stored_name])
    assert yazimda == [sorted(okunanlar)]


def _kopyada_disk_hatasi(_hedef: Any, kaynak: Path, _boy: int) -> None:
    raise OSError(errno.EIO, "giriş çıkış hatası", str(kaynak))


def _kopyada_degisti(_hedef: Any, _kaynak: Path, _boy: int) -> None:
    raise BackupCryptoError("Ek dosyası yedek alınırken değişti; yedek yazılmadı.")


@pytest.mark.parametrize(
    ("kopya", "ileti"),
    [
        (_kopyada_disk_hatasi, encrypted_backup.YAZILAMADI),
        (_kopyada_degisti, "Ek dosyası yedek alınırken değişti; yedek yazılmadı."),
    ],
)
def test_on_okumadan_sonra_okuma_duserse_yedek_duser_ileti_yol_tasimaz(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    sahip: SchoolYear,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    kopya: Callable[..., None],
    ileti: str,
) -> None:
    goruntu(_ek(sahip))
    monkeypatch.setattr(backup_crypto, "_ek_govdesini_kopyala", kopya)

    with caplog.at_level(logging.DEBUG):
        yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ileti
    assert str(dosya_deposu.depo_dizini()) not in yanit.content.decode("utf-8")
    assert str(dosya_deposu.depo_dizini()) not in caplog.text
    _iz_yok_dosya_yok(usb)
    _sayac_bos()


# ============================================================ boş yer ve FAT32


def test_disk_dolu_yazmadan_once_soylenir(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    sorulan: list[Path] = []

    def bos_yer(yol: Path) -> SimpleNamespace:
        sorulan.append(Path(yol))
        return SimpleNamespace(free=10)

    monkeypatch.setattr(shutil, "disk_usage", bos_yer)

    def yazilmamali(*_a: object, **_k: object) -> None:
        raise AssertionError("yazılmamalıydı")

    monkeypatch.setattr(encrypted_backup, "tam_yedek_yaz", yazilmamali)

    yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == encrypted_backup.YER_YOK
    assert sorulan == [usb]
    _iz_yok_dosya_yok(usb)


def _yazim_hatasi(monkeypatch: pytest.MonkeyPatch, hata: OSError) -> None:
    """Yazım yarıda düşer: gerçek yazıcı geçici dosyasını açmış, hedef hatası gelmiştir."""
    monkeypatch.setattr(backup_crypto, "_diske_indir", lambda _akis: (_ for _ in ()).throw(hata))


@pytest.mark.parametrize(
    ("hata", "ileti"),
    [
        (OSError(errno.ENOSPC, "yer yok", "/uydurma/yol"), encrypted_backup.YER_YOK),
        (OSError(errno.EDQUOT, "kota doldu", "/uydurma/yol"), encrypted_backup.YER_YOK),
        (OSError(errno.EFBIG, "dosya çok büyük", "/uydurma/yol"), encrypted_backup.FAT_SINIRI),
        (OSError(errno.EIO, "giriş çıkış", "/uydurma/yol"), encrypted_backup.YAZILAMADI),
        (PermissionError(errno.EACCES, "izin yok", "/uydurma/yol"), encrypted_backup.YAZILAMADI),
    ],
)
def test_yazim_hatasi_turkce_iletiye_cevrilir_dosya_kalmaz(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    hata: OSError,
    ileti: str,
) -> None:
    _yazim_hatasi(monkeypatch, hata)

    with caplog.at_level(logging.DEBUG):
        yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == ileti
    assert "/uydurma/yol" not in yanit.content.decode("utf-8")
    assert "/uydurma/yol" not in caplog.text
    _iz_yok_dosya_yok(usb)
    _sayac_bos()


@pytest.mark.parametrize(
    ("winerror", "ileti"),
    [
        (112, encrypted_backup.YER_YOK),
        (39, encrypted_backup.YER_YOK),
        (223, encrypted_backup.FAT_SINIRI),
        (5, encrypted_backup.YAZILAMADI),
    ],
)
def test_windows_hata_kodlari_da_cevrilir(winerror: int, ileti: str) -> None:
    hata = OSError(errno.EINVAL, "uydurma")
    hata.winerror = winerror  # type: ignore[attr-defined]
    assert encrypted_backup._yazim_iletisi(hata) == ileti


def _buyuk_yedek(monkeypatch: pytest.MonkeyPatch, boy: int, tur: str | None) -> None:
    monkeypatch.setattr(encrypted_backup, "_tahmini_boy", lambda *_a: boy)
    monkeypatch.setattr(encrypted_backup, "dosya_sistemi_turu", lambda _yol: tur)
    monkeypatch.setattr(shutil, "disk_usage", lambda _yol: SimpleNamespace(free=2**40))


@pytest.mark.parametrize("tur", ["vfat", "msdos", "FAT32", "FAT"])
def test_fat32_sinirini_asan_yedek_yazmadan_once_reddedilir(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
    tur: str,
) -> None:
    _buyuk_yedek(monkeypatch, 2**32, tur)

    def yazilmamali(*_a: object, **_k: object) -> None:
        raise AssertionError("yazılmamalıydı")

    monkeypatch.setattr(encrypted_backup, "tam_yedek_yaz", yazilmamali)

    yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == encrypted_backup.FAT_SINIRI
    _iz_yok_dosya_yok(usb)


@pytest.mark.parametrize(
    ("boy", "tur"),
    [(2**32 - 1, "vfat"), (2**32, "ntfs"), (2**32, "exfat"), (2**32, None)],
    ids=["sinirda", "ntfs", "exfat", "tur_okunamadi"],
)
def test_fat32_olmayan_ya_da_siniri_asmayan_yedek_yazilir(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
    boy: int,
    tur: str | None,
) -> None:
    """Tür okunamazsa yazım denenir; sınır aşılırsa `EFBIG` iletiye çevrilir (üstteki test)."""
    _buyuk_yedek(monkeypatch, boy, tur)

    assert _kaydet(client, usb / AD).status_code == 200


def test_bos_yer_okunamazsa_yazim_denenir(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    def okunamadi(yol: Path) -> None:
        raise OSError(errno.EIO, "okunamadı", str(yol))

    monkeypatch.setattr(shutil, "disk_usage", okunamadi)

    assert _kaydet(client, usb / AD).status_code == 200


# ============================================================ serbest ad ve kişisel veri


@pytest.mark.parametrize(
    "serbest",
    [
        f"{UYDURMA_KISI} Masalcıoğlu yedeği.odbak",
        f"oab-defteri-yedek-2026-11-06-101530-{UYDURMA_KISI}.odbak",
        f"{UYDURMA_KISI}-oab-defteri-yedek-2026-11-06-101530.odbak",
        f"oab-defteri-yedek-2026-11-06-101530.odbak-{UYDURMA_KISI}.odbak",
        "oab-defteri-yedek-٢٠٢٦-11-06-101530.odbak",
        "OAB-DEFTERI-YEDEK-2026-11-06-101530.odbak",
        # Programın başka bir adı da bu satırın kimliği olmaz: bu yedek günlük yedek değildir.
        "gunluk-2026-11-06.odbak",
    ],
)
def test_serbest_ad_satira_gunluge_yanita_girmez_kimlik_programindir(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    caplog: pytest.LogCaptureFixture,
    serbest: str,
) -> None:
    """R1: ad serbest metindir; dosya kullanıcının adıyla durur, kimlik programın adıdır."""
    with caplog.at_level(logging.DEBUG):
        yanit = _kaydet(client, usb / serbest)

    assert yanit.status_code == 200
    assert (usb / serbest).is_file()
    (satir,) = _yedek_satirlari()
    assert encrypted_backup._PROGRAM_ADI.fullmatch(satir.object_id)
    assert yanit.json()["ad"] == satir.object_id
    assert satir.object_id != serbest
    govde = yanit.content.decode("utf-8")
    assert serbest not in govde and serbest not in caplog.text
    assert serbest not in str(AuditTrail.objects.values().get(pk=satir.pk))


def test_yol_hicbir_satira_gunluge_yanita_girmez(
    client: APIClient,
    usb: Path,
    goruntu: Callable[..., None],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG):
        yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 200
    assert UYDURMA_KISI not in yanit.content.decode("utf-8")
    assert UYDURMA_KISI not in caplog.text
    assert UYDURMA_KISI not in str(list(AuditTrail.objects.values()))
    # Programın adı kimlik olarak kalır (Denetleme Kurulu satırı dosyayla eşler).
    (satir,) = _yedek_satirlari()
    assert satir.object_id == AD


# ============================================================ uzun iş


def test_ikinci_yedek_409_alir(
    client: APIClient, usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Aynı anda ikincisi beklemez: birinci sürerken gelen istek 409 `yedek_suruyor` alır."""
    ikinciler: list[Any] = []

    def goruntu_al(_yol: Path) -> tuple[bytes, Manifesto]:
        ikinciler.append(_kaydet(client, usb / "ikinci.odbak"))
        return GORUNTU, Manifesto(KAPSAM_YEREL)

    monkeypatch.setattr(encrypted_backup, "goruntu_ve_manifesto", goruntu_al)

    assert _kaydet(client, usb / AD).status_code == 200

    (ikinci,) = ikinciler
    assert ikinci.status_code == 409
    assert ikinci.json()["code"] == "yedek_suruyor"
    assert ikinci.json()["message"] == encrypted_backup.YEDEK_ALINIYOR
    assert _adlar(usb) == [AD]
    _sayac_bos()


def test_bakim_surerken_baslamaz(
    client: APIClient, usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def alinmamali(_yol: Path) -> None:
        raise AssertionError("görüntü alınmamalıydı")

    monkeypatch.setattr(encrypted_backup, "goruntu_ve_manifesto", alinmamali)
    assert bakim.KAPI.bakima_al(bekleme_sn=0)

    yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 409
    assert yanit.json()["code"] == "bakim_suruyor"
    assert yanit.json()["message"] == encrypted_backup.BAKIM_SURUYOR
    _iz_yok_dosya_yok(usb)
    _sayac_bos()


def test_is_suresince_sayac_ve_kapi_tutulur_sonra_birakilir(
    client: APIClient, usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gorulen: list[tuple[int, int, bool]] = []

    def goruntu_al(_yol: Path) -> tuple[bytes, Manifesto]:
        gorulen.append(
            (bakim.UZUN_ISLER.sayi, bakim.KAPI.ucusta, encrypted_backup._TEK_IS.locked())
        )
        return GORUNTU, Manifesto(KAPSAM_YEREL)

    monkeypatch.setattr(encrypted_backup, "goruntu_ve_manifesto", goruntu_al)

    assert _kaydet(client, usb / AD).status_code == 200

    assert gorulen == [(1, 1, True)]
    _sayac_bos()


def _patlayan(hata: BaseException) -> Callable[..., None]:
    def patla(*_a: object, **_k: object) -> None:
        raise hata

    return patla


@pytest.mark.parametrize(
    "hata",
    [
        OSError(errno.EIO, "uydurma"),
        BackupCryptoError("uydurma"),
        denetim_izi.IzYazilamadi("uydurma"),
        RuntimeError("uydurma"),
        _Olduruldu(),
    ],
    ids=["os", "kap", "iz", "beklenmedik", "base_exception"],
)
@pytest.mark.parametrize("yer", ["tam_yedek_yaz", "_yazilani_denetle", "_satiri_yaz"])
def test_sayac_her_cikista_duser_gecici_dosya_kalmaz(
    usb: Path,
    goruntu: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
    yer: str,
    hata: BaseException,
) -> None:
    """Sayaç sızarsa kilit hiç gelmez, her çarpı 60 sn bekler; geçici dosya da kalmamalıdır."""
    monkeypatch.setattr(encrypted_backup, yer, _patlayan(hata))

    with pytest.raises(BaseException):  # noqa: B017, PT011 — tür parametrede
        encrypted_backup.sifreli_yedegi_kaydet(str(usb / AD))

    _sayac_bos()
    _iz_yok_dosya_yok(usb)


def test_on_okumada_kesilirse_de_sayac_duser(
    usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(encrypted_backup, "_ekleri_on_oku", _patlayan(_Olduruldu()))

    with pytest.raises(_Olduruldu):
        encrypted_backup.sifreli_yedegi_kaydet(str(usb / AD))

    _sayac_bos()
    assert _adlar(usb) == []


def test_kilit_denetimi_sayacin_icindedir(
    usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Denetimle sayaç arasında kilit kararı verilemez: denetim anında sayaç artmıştır."""
    gorulen: list[int] = []
    asil = app_password.is_locked

    def izle() -> bool:
        gorulen.append(bakim.UZUN_ISLER.sayi)
        return asil()

    monkeypatch.setattr(app_password, "is_locked", izle)

    encrypted_backup.sifreli_yedegi_kaydet(str(usb / AD))

    assert gorulen == [1]


def test_is_surerken_elle_kilit_ertelenir_dek_dusmez(
    client: APIClient, usb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tasarım §4.4.3 (denetim UY-1): kilit işin sonuna kalır, satır oturumun hesabıyla yazılır."""

    def goruntu_al(_yol: Path) -> tuple[bytes, Manifesto]:
        OTURUM.kilitle(neden="elle")
        return GORUNTU, Manifesto(KAPSAM_YEREL)

    monkeypatch.setattr(encrypted_backup, "goruntu_ve_manifesto", goruntu_al)

    assert _kaydet(client, usb / AD).status_code == 200

    (satir,) = _yedek_satirlari()
    assert str(satir.account_id) == TEST_HESAP_ID
    assert OTURUM.kilit_bekliyor()


# ============================================================ kilit, rol, güvenlik dosyası


def test_kilitliyken_servis_reddeder(usb: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_password, "is_locked", lambda: True)

    with pytest.raises(encrypted_backup.EncryptedBackupError, match="kilidi açın"):
        encrypted_backup.sifreli_yedegi_kaydet(str(usb / AD))
    with pytest.raises(encrypted_backup.EncryptedBackupError, match="kilidi açın"):
        encrypted_backup.onerilen_ad()
    _iz_yok_dosya_yok(usb)
    _sayac_bos()


def test_guvenlik_yetenegi_oneriyi_ve_kaydi_birlikte_kapsar() -> None:
    """Ön yüz düğmeyi yetenekten açar: iki istek de yeteneğin içindedir (plan F1b-2 "Yetenekler")."""
    guvenlik = rol_izinleri.YETENEKLER["guvenlik"]
    assert {("encrypted-backup-download", "GET"), ("encrypted-backup-download", "POST")} <= guvenlik


def test_kilitliyken_uclar_kapalidir(client: APIClient, kilitli: Path, usb: Path) -> None:
    assert client.get(URL).status_code == 423
    assert _kaydet(client, usb / AD).status_code == 423
    assert _adlar(usb) == []


@pytest.mark.parametrize("rol", ["mudur", "muhasip", "denetleme_kurulu"])
def test_uclar_yalniz_program_yoneticisine_aciktir(client: APIClient, usb: Path, rol: str) -> None:
    oturumu_ac_test("0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e30", tanitici=rol, rol=rol)

    assert client.get(URL).status_code == 403
    assert _kaydet(client, usb / AD).status_code == 403
    assert _adlar(usb) == []


@pytest.mark.parametrize("durum", ["yok", "bozuk", "arsiv_var"])
def test_guvenlik_dosyasi_okunamiyorsa_yedek_verilmez(
    durum: str, usb: Path, goruntu: Callable[..., None]
) -> None:
    """Başlıksız yedek üretilmez (plan F1b-3 "Kap ve manifesto"): arşiv kopyasına da düşülmez;
    iz satırı yazılmaz, dış yedek hatırlatması sıfırlanmaz."""
    guvenlik = app_password.state_path()
    saglam = guvenlik.read_bytes()
    if durum == "yok":
        guvenlik.unlink()
    else:
        guvenlik.write_bytes(b"{bozuk")
    if durum == "arsiv_var":
        guvenlik.with_name("guvenlik-arsiv-2026-11-01-101010.json").write_bytes(saglam)

    with pytest.raises(encrypted_backup.EncryptedBackupError, match="Güvenlik dosyası okunamıyor"):
        encrypted_backup.sifreli_yedegi_kaydet(str(usb / AD))

    _iz_yok_dosya_yok(usb)
    _sayac_bos()


def test_veri_anahtari_bellekte_degilse_yazilmaz(
    client: APIClient, usb: Path, goruntu: Callable[..., None], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(crypto, "active_key", lambda: None)

    yanit = _kaydet(client, usb / AD)

    assert yanit.status_code == 409
    assert yanit.json()["code"] == "parola_gerekli"
    _iz_yok_dosya_yok(usb)
