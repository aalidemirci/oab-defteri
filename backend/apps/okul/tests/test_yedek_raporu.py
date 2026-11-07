"""Yedek Raporu (plan F1b-3 "Yedek raporu bu adımda, tam döküm"; tasarım §4.4.7, §9.7).

Kanıtlanan maddeler:

* rapor bu bilgisayardaki yedekleri türlerine göre sayar: adet, en eski ve en yeni tarih, saklama
  kuralı; saklama rakamları rotasyon sabitlerinden gelir;
* her yedeği açan kurtarma anahtarının no'su ve tarihi başlıktan, kurtarma anahtarı olmadan okunur;
  okunamayan dosya "Okunamadı" diye sayılır, rapor düşmez;
* kenara alınmış önceki veritabanları sayılır, `-wal`/`-shm` eşleri sayılmaz;
* son şifreli yedeğin tarihi, denetlendiği ve kaç ek taşıdığı; ad verilemeyen yedeğin satırı yedek
  sayılmaz;
* hatırlatma süresi ve "USB bellekteki yedek programın dışındadır" cümlesi;
* tek sayfa, kişisiz: kişi adı, yol ve elle adlandırılmış dosyanın adı yoktur;
* basım `BASIM` satırıdır (kod ve PDF'in sha256'sı); satır yazılamazsa PDF verilmez;
* yalnız program yöneticisi basar, kilitliyken kapalıdır; dosya saklanmaz.

Adlar uydurmadır.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import patch
from urllib.parse import unquote

import pytest
from desktop import backup as yedek_mod
from desktop.backup import DEFAULT_KEEP_DAYS, DEFAULT_KEEP_PRE_MIGRATE, ROTASYON_KUMESI
from desktop.backup_crypto import KAPSAM_YEREL, Manifesto, ManifestoGirdisi
from desktop.tests.kap_ortak import durum_basligi, kap_kur
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from pypdf import PdfReader
from rest_framework.test import APIClient

from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AccountRole, AuditAction, AuditTrail, SchoolConfig
from apps.okul.oturum import Yazar, yazar_olarak
from apps.okul.services import app_password, dis_yedek, yedek_raporu
from conftest import KURULUM_IZI, TEST_DEK, TEST_HESAP_ID, oturumu_ac_test, varsayilan_yazar
from shared.exceptions import RolYetkisiz

pytestmark = pytest.mark.django_db

URL = "/api/v1/backups/report/"
GORUNTU = b"SQLite format 3\0uydurma-kayit-icerigi"
#: Dosya adında, okul kartında ve müdür alanında durur: raporda geçmemelidir.
UYDURMA_KISI = "Uydurgul Masalcioglu"
UYDURMA_KISI_KISA = "Uydurgul"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def yedekler() -> Iterator[Path]:
    dizin = app_password.backup_dir()
    dizin.mkdir(parents=True, exist_ok=True)
    yield dizin


@pytest.fixture
def veri_dizini() -> Path:
    return app_password.state_path().parent


def _yedek(dizin: Path, ad: str, *, no: int = 1, tarih: str = "2026-11-01") -> Path:
    durum = dict(app_password.read_state() or {})
    durum["kurtarma"] = {**durum["kurtarma"], "no": no, "tarih": tarih}
    yol = dizin / ad
    yol.write_bytes(kap_kur(GORUNTU, TEST_DEK, baslik=durum_basligi(durum)))
    return yol


def _baglam() -> dict[str, Any]:
    return yedek_raporu._baglam()  # noqa: SLF001


def _tur(baglam: dict[str, Any], ad: str) -> Any:
    return next(satir for satir in baglam["turler"] if satir.ad == ad)


def _bas(client: APIClient) -> Any:
    return client.post(URL)


def _pdf(yanit: Any) -> bytes:
    assert yanit.status_code == 200, yanit.content[:300]
    return b"".join(yanit.streaming_content)


def _metin(pdf: bytes) -> str:
    return "\n".join(sayfa.extract_text() or "" for sayfa in PdfReader(BytesIO(pdf)).pages)


def _tek_satir(pdf: bytes) -> str:
    return " ".join(_metin(pdf).split())


def _basim_satirlari() -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(seq__gt=KURULUM_IZI, action=AuditAction.BASIM))


def _yedek_satiri(
    *, an: datetime, dosya_sayisi: int = 3, eksik: int = 0, kapsam: str = "tam"
) -> None:
    """Kaydedilen yedeğin `YEDEK` satırı (`encrypted_backup._satiri_yaz` ile aynı değerler).

    İz satırı değiştirilemez: geçmişteki an yazıcının saatiyle kurulur.
    """
    degerler = {
        "kapsam": (None, kapsam),
        "dosya_sayisi": (None, dosya_sayisi),
        "boyut": (None, 2048),
        "eksik": (None, eksik),
    }
    with (
        patch("apps.okul.denetim_izi.timezone.now", return_value=an),
        yazar_olarak(varsayilan_yazar()),
        transaction.atomic(),
    ):
        denetim_izi.olay(
            AuditAction.YEDEK,
            model=denetim_izi.YEDEK_DOSYASI,
            object_id="oab-defteri-yedek-2026-11-05-101530.odbak",
            changed_fields=sorted(degerler),
            values=degerler,
        )


# ------------------------------------------------------------------ içerik: türler


def test_yedekler_turlerine_gore_sayilir(yedekler: Path) -> None:
    for ad in (
        "gunluk-2026-10-25.odbak",
        "gunluk-2026-11-06.odbak",
        "gunluk-2026-11-01.odbak",
        "pre-migrate-0.2.0-2026-10-30.odbak",
        "pre-parola-acilis-2026-10-20-101530.odbak",
    ):
        _yedek(yedekler, ad)

    baglam = _baglam()

    gunluk = _tur(baglam, "Günlük yedek")
    assert (gunluk.adet, gunluk.en_eski, gunluk.en_yeni) == (3, "25.10.2026", "06.11.2026")
    goc = _tur(baglam, "Güncelleme öncesi yedek")
    assert (goc.adet, goc.en_eski, goc.en_yeni) == (1, "30.10.2026", "30.10.2026")
    assert _tur(baglam, "Kurulum yedeği").adet == 1


def test_bos_dizinde_adli_turler_sifirla_basilir(yedekler: Path) -> None:
    baglam = _baglam()

    gunluk = _tur(baglam, "Günlük yedek")
    assert (gunluk.adet, gunluk.en_eski, gunluk.en_yeni) == (0, "", "")
    assert baglam["anahtarlar"] == []


def test_saklama_kurali_rotasyon_sabitlerinden_gelir(
    yedekler: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rakam metne elle yazılmaz: sabit değişirse rapor da değişir."""
    baglam = _baglam()
    assert _tur(baglam, "Günlük yedek").saklama == f"{DEFAULT_KEEP_DAYS} gün"
    assert (
        _tur(baglam, "Güncelleme öncesi yedek").saklama == f"Son {DEFAULT_KEEP_PRE_MIGRATE} yedek"
    )

    monkeypatch.setattr(yedek_raporu, "DEFAULT_KEEP_DAYS", 21)
    monkeypatch.setattr(yedek_raporu, "DEFAULT_KEEP_PRE_MIGRATE", 7)
    baglam = _baglam()
    assert _tur(baglam, "Kurulum yedeği").saklama == "21 gün"
    assert _tur(baglam, yedek_raporu.ONCEKI_VERITABANI).saklama == "21 gün"
    assert _tur(baglam, "Güncelleme öncesi yedek").saklama == "Son 7 yedek"


def test_rapor_rotasyonun_sabitlerini_kullanir() -> None:
    assert DEFAULT_KEEP_DAYS == yedek_mod.DEFAULT_KEEP_DAYS == 14
    assert DEFAULT_KEEP_PRE_MIGRATE == yedek_mod.DEFAULT_KEEP_PRE_MIGRATE == 5


def test_adlandirilmamis_turler_oteki_yedek_satirinda_sayilir(yedekler: Path) -> None:
    """Rotasyonun yedek dizinindeki her öneki ya adlıdır ya da "Öteki yedek"te sayılır."""
    adsizlar = {
        kural.onek
        for kural in ROTASYON_KUMESI
        if not kural.veri_dizininde and kural.onek not in yedek_raporu.TUR_ADLARI
    }
    assert adsizlar == {"pre-anonim", "pre-kapanis", "pre-dek-yenileme"}
    _yedek(yedekler, "pre-kapanis-2026-11-01.odbak")
    _yedek(yedekler, "pre-anonim-2026-11-03-101530.odbak")

    oteki = _tur(_baglam(), yedek_raporu.OTEKI_YEDEK)

    assert (oteki.adet, oteki.en_eski, oteki.en_yeni) == (2, "01.11.2026", "03.11.2026")
    assert oteki.saklama == f"{DEFAULT_KEEP_DAYS} gün"


def test_oteki_yedek_yoksa_satiri_basilmaz(yedekler: Path) -> None:
    assert yedek_raporu.OTEKI_YEDEK not in {satir.ad for satir in _baglam()["turler"]}


def test_elle_adlandirilmis_dosya_yalniz_sayilir(yedekler: Path) -> None:
    _yedek(yedekler, f"{UYDURMA_KISI_KISA}-yedegi.odbak")
    # Tarihi geçersiz program adı da program yedeği sayılmaz.
    _yedek(yedekler, "gunluk-2026-13-45.odbak")

    baglam = _baglam()

    elle = _tur(baglam, yedek_raporu.ELLE_KONMUS_YEDEK)
    assert (elle.adet, elle.en_eski, elle.en_yeni) == (2, "", "")
    assert elle.saklama == yedek_raporu.PROGRAM_SILMEZ
    assert UYDURMA_KISI_KISA not in repr(baglam)


def test_yedek_olmayan_dosyalar_ve_dizinler_sayilmaz(yedekler: Path) -> None:
    (yedekler / "gunluk-2026-11-01.odbak.tmp").write_bytes(b"yarim")
    (yedekler / "not.txt").write_text("uydurma", encoding="utf-8")
    (yedekler / "gunluk-2026-11-02.odbak").mkdir()
    baska = yedekler.parent / "baska.odbak"
    _yedek(yedekler.parent, baska.name)
    (yedekler / "gunluk-2026-11-03.odbak").symlink_to(baska)

    baglam = _baglam()

    assert _tur(baglam, "Günlük yedek").adet == 0
    assert baglam["anahtarlar"] == []


def test_onceki_veritabanlari_eslerini_saymadan_sayilir(yedekler: Path, veri_dizini: Path) -> None:
    for ad in (
        "db-onceki-2026-11-01-101530.sqlite3",
        "db-onceki-2026-11-01-101530.sqlite3-wal",
        "db-onceki-2026-11-01-101530.sqlite3-shm",
        "db-onceki-2026-11-04-090000.sqlite3",
        "db-onceki-elle.sqlite3",
    ):
        (veri_dizini / ad).write_bytes(b"x")

    onceki = _tur(_baglam(), yedek_raporu.ONCEKI_VERITABANI)

    assert (onceki.adet, onceki.en_eski, onceki.en_yeni) == (2, "01.11.2026", "04.11.2026")
    assert onceki.saklama == f"{DEFAULT_KEEP_DAYS} gün"


def test_dizin_okunamazsa_rapor_dusmez(
    yedekler: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def patlar(_yol: Any) -> Any:
        raise PermissionError(13, "erişim reddedildi", f"/home/{UYDURMA_KISI_KISA}/yedekler")

    monkeypatch.setattr("apps.okul.services.yedek_raporu.os.scandir", patlar)

    with caplog.at_level(logging.DEBUG):
        baglam = _baglam()

    assert _tur(baglam, "Günlük yedek").adet == 0
    assert UYDURMA_KISI_KISA not in caplog.text


# ---------------------------------------------------------------- içerik: anahtarlar


def test_her_yedegi_acan_anahtar_basliktan_okunur(yedekler: Path) -> None:
    """Kurtarma anahtarı istenmez; en yeni anahtar üsttedir, bir anahtar tek satırdır."""
    _yedek(yedekler, "gunluk-2026-11-01.odbak", no=2, tarih="2026-10-30")
    _yedek(yedekler, "gunluk-2026-11-02.odbak", no=2, tarih="2026-10-30")
    _yedek(yedekler, "gunluk-2026-11-03.odbak", no=3, tarih="2026-11-02")

    assert _baglam()["anahtarlar"] == [
        yedek_raporu.AnahtarSatiri("3", "02.11.2026", 1),
        yedek_raporu.AnahtarSatiri("2", "30.10.2026", 2),
    ]


@pytest.mark.parametrize(
    "icerik",
    [
        pytest.param(b"yedek degil", id="kap_degil"),
        pytest.param(b"ODBAK\x02" + b"\0" * 80, id="deneme_kabi"),
        pytest.param(b"", id="bos"),
    ],
)
def test_okunamayan_dosya_okunamadi_diye_sayilir_rapor_dusmez(
    yedekler: Path, client: APIClient, icerik: bytes
) -> None:
    _yedek(yedekler, "gunluk-2026-11-02.odbak", no=2, tarih="2026-10-30")
    (yedekler / "gunluk-2026-11-01.odbak").write_bytes(icerik)

    assert _baglam()["anahtarlar"] == [
        yedek_raporu.AnahtarSatiri("2", "30.10.2026", 1),
        yedek_raporu.AnahtarSatiri(yedek_raporu.OKUNAMADI, "", 1),
    ]
    assert "Okunamadı" in _metin(_pdf(_bas(client)))


def test_okuma_hatasi_veren_dosya_okunamadi_sayilir(
    yedekler: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _yedek(yedekler, "gunluk-2026-11-01.odbak")

    def patlar(_yol: Path) -> Any:
        raise PermissionError(13, "erişim reddedildi", f"/home/{UYDURMA_KISI_KISA}/yedek.odbak")

    monkeypatch.setattr("apps.okul.services.live_restore.read_embedded_recovery_metadata", patlar)

    with caplog.at_level(logging.DEBUG):
        anahtarlar = _baglam()["anahtarlar"]

    assert anahtarlar == [yedek_raporu.AnahtarSatiri(yedek_raporu.OKUNAMADI, "", 1)]
    assert UYDURMA_KISI_KISA not in caplog.text


def test_anahtar_satirlari_sayfa_butcesi_icin_sinirlidir(yedekler: Path) -> None:
    sinir = yedek_raporu.ANAHTAR_SATIRI_SINIRI
    for no in range(1, sinir + 4):
        _yedek(yedekler, f"gunluk-2026-10-{no:02}.odbak", no=no)

    satirlar = _baglam()["anahtarlar"]

    assert len(satirlar) == sinir + 1
    assert satirlar[0].no == str(sinir + 3)
    assert satirlar[-1] == yedek_raporu.AnahtarSatiri(yedek_raporu.OTEKI_ANAHTARLAR, "", 3)


# ------------------------------------------------------ içerik: son şifreli yedek


def test_hic_yedek_kaydedilmediyse_soyler(client: APIClient) -> None:
    assert yedek_raporu.HIC_ALINMADI in _tek_satir(_pdf(_bas(client)))


def test_son_sifreli_yedegin_tarihi_ve_ek_sayisi(client: APIClient) -> None:
    an = timezone.localtime().replace(microsecond=0) - timedelta(days=1)
    _yedek_satiri(an=an - timedelta(seconds=2), dosya_sayisi=7, eksik=2)
    dis_yedek.indirme_kaydet(an)

    son = _baglam()["son_yedek"]
    assert son == yedek_raporu.SonSifreliYedek(tarih=f"{an:%d.%m.%Y}", ek_sayisi=7, eksik=2)

    metin = _tek_satir(_pdf(_bas(client)))
    assert f"{an:%d.%m.%Y}" in metin
    assert yedek_raporu.DENETLENDI in metin
    assert "7; 2 ek yedek alınırken bulunamadı ya da bozuktu" in metin


def test_dort_haneli_ek_sayisi_noktayla_ayrilir(client: APIClient) -> None:
    """Sözlük §3 (RYUE md. 16/7): evrakta dört ve daha çok haneli sayı üçlü gruplanır."""
    an = timezone.localtime().replace(microsecond=0)
    _yedek_satiri(an=an - timedelta(seconds=2), dosya_sayisi=1200, eksik=1035)
    dis_yedek.indirme_kaydet(an)

    son = _baglam()["son_yedek"]
    assert (son.ek_sayisi, son.eksik) == (1200, 1035)  # alanlar sayı kalır, biçim metindedir

    metin = _tek_satir(_pdf(_bas(client)))
    assert "1.200; 1.035 ek yedek alınırken bulunamadı ya da bozuktu" in metin


def test_eksik_yoksa_sifir_basilmaz() -> None:
    """Şablon `eksik`'i sayı olarak sınar: metne çevrilseydi "0" doğru sayılırdı."""
    an = timezone.localtime().replace(microsecond=0)
    _yedek_satiri(an=an - timedelta(seconds=2), dosya_sayisi=1200, eksik=0)
    dis_yedek.indirme_kaydet(an)

    html = render_to_string(yedek_raporu.TEMPLATE_NAME, _baglam())

    assert "1.200" in html
    assert "yedek alınırken bulunamadı" not in html


def test_tablolardaki_adetler_de_noktayla_ayrilir() -> None:
    baglam = {
        **_baglam(),
        "turler": [yedek_raporu.TurSatiri("Günlük yedek", 1200, "", "", "14 gün")],
        "anahtarlar": [yedek_raporu.AnahtarSatiri("3", "", 1035)],
    }

    html = render_to_string(yedek_raporu.TEMPLATE_NAME, baglam)

    assert '<td class="sayi">1.200</td>' in html
    assert '<td class="sayi">1.035</td>' in html


@pytest.mark.parametrize(
    ("sayi", "metin"),
    [(None, ""), (0, "0"), (999, "999"), (1000, "1.000"), (1234567, "1.234.567")],
)
def test_binlikli(sayi: int | None, metin: str) -> None:
    assert yedek_raporu._binlikli(sayi) == metin


def test_son_yedegin_tarihi_yerel_gundur() -> None:
    """Saat dilimi `Europe/Istanbul`: gece birdeki yedek UTC'de bir önceki gündedir."""
    dis_yedek.indirme_kaydet(timezone.make_aware(datetime(2026, 11, 6, 1, 0)))

    assert _baglam()["son_yedek"].tarih == "06.11.2026"


def test_kayit_saniyeye_kirpildigi_icin_satir_ondan_az_sonra_gorunebilir() -> None:
    """Tarih saniyeye kırpılı yazılır: 10:15:30,7'deki satır 10:15:30 kaydının satırıdır."""
    an = timezone.localtime().replace(microsecond=0)
    _yedek_satiri(an=an + timedelta(milliseconds=700), dosya_sayisi=4)
    dis_yedek.indirme_kaydet(an)

    assert _baglam()["son_yedek"].ek_sayisi == 4


def test_ad_verilemeyen_yedegin_satiri_yedek_sayilmaz() -> None:
    """Asıl ad verilemezse satır kalır, kayıt yazılmaz: rapor son sağlam yedeği söyler."""
    an = timezone.localtime().replace(microsecond=0) - timedelta(days=2)
    _yedek_satiri(an=an - timedelta(seconds=2), dosya_sayisi=4)
    dis_yedek.indirme_kaydet(an)
    _yedek_satiri(an=an + timedelta(days=1), dosya_sayisi=9)

    son = _baglam()["son_yedek"]

    assert son.tarih == f"{an:%d.%m.%Y}"
    assert son.ek_sayisi == 4


def test_hic_ad_verilmediyse_satir_yedek_sayilmaz() -> None:
    _yedek_satiri(an=timezone.localtime(), dosya_sayisi=9)

    assert _baglam()["son_yedek"] is None


def test_yerel_yedegin_satiri_son_sifreli_yedek_sayilmaz() -> None:
    an = timezone.localtime().replace(microsecond=0)
    _yedek_satiri(an=an - timedelta(seconds=3), dosya_sayisi=5)
    _yedek_satiri(an=an - timedelta(seconds=1), dosya_sayisi=0, kapsam="yerel")
    dis_yedek.indirme_kaydet(an)

    assert _baglam()["son_yedek"].ek_sayisi == 5


def test_eski_veritabani_donmusse_ek_sayisi_bilinmiyor_der(client: APIClient) -> None:
    """Kayıt bu bilgisayarın dosyasındadır, satır veritabanında: geri yükleme satırı götürür.
    Daha eski bir yedeğin satırı bu yedeğin sayısı diye basılmaz."""
    an = timezone.localtime().replace(microsecond=0)
    _yedek_satiri(an=an - timedelta(days=20), dosya_sayisi=9)
    dis_yedek.indirme_kaydet(an)

    son = _baglam()["son_yedek"]
    assert son == yedek_raporu.SonSifreliYedek(tarih=f"{an:%d.%m.%Y}", ek_sayisi=None, eksik=None)
    assert yedek_raporu.EK_SAYISI_BILINMIYOR in _tek_satir(_pdf(_bas(client)))


def test_gercek_kayit_raporda_gorunur(
    client: APIClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Uçtan uca: `POST backups/encrypted/` raporun okuduğu satırı ve kaydı yazar."""
    from apps.okul.services import encrypted_backup

    girdi = ManifestoGirdisi("a" * 32, 10, "b" * 64)  # depoda yok: `eksik` sayılır
    monkeypatch.setattr(
        encrypted_backup,
        "goruntu_ve_manifesto",
        lambda _yol: (GORUNTU, Manifesto(KAPSAM_YEREL, (girdi,))),
    )
    usb = tmp_path / "usb"
    usb.mkdir()
    yanit = client.post(
        "/api/v1/backups/encrypted/",
        {"hedef": str(usb / "oab-defteri-yedek-2026-11-06-101530.odbak")},
        format="json",
    )
    assert yanit.status_code == 200, yanit.content

    son = _baglam()["son_yedek"]

    assert son == yedek_raporu.SonSifreliYedek(
        tarih=f"{timezone.localdate():%d.%m.%Y}", ek_sayisi=0, eksik=1
    )


# -------------------------------------------------------------- belge ve kişisizlik


def test_rapor_metni_plandaki_maddeleri_tasir(client: APIClient, yedekler: Path) -> None:
    _yedek(yedekler, "gunluk-2026-11-01.odbak", no=2, tarih="2026-10-30")
    gun = dis_yedek.hatirlatma_suresini_ayarla
    with yazar_olarak(varsayilan_yazar()):
        gun(45)

    metin = _tek_satir(_pdf(_bas(client)))

    assert "YEDEK RAPORU" in metin
    assert "BU BİLGİSAYARDAKİ YEDEKLER" in metin
    assert "Günlük yedek" in metin
    assert "Anahtar no" in metin
    assert "2 30.10.2026 1" in metin
    assert yedek_raporu.ONCEKI_VERITABANI in metin
    assert "SON ŞİFRELİ YEDEK" in metin
    assert "45 gün" in metin
    assert "USB bellekteki yedek programın dışındadır." in metin


def test_rapor_tek_sayfadir_en_uzun_dokumde_bile(client: APIClient, yedekler: Path) -> None:
    """Sayfa bütçesi gerçek uzunlukta uydurma verilerle (tasarım §9.1-4): bütün türler dolu, anahtar
    tablosu sınırda, okul adı uzun."""
    okul = SchoolConfig.load()
    okul.school_name = "Uydurma Şehit Öğretmen Çok Uzun Adlı Mesleki ve Teknik Anadolu Lisesi"
    okul.district = "Uydurmaköy"
    okul.save()
    for no in range(1, 15):
        _yedek(yedekler, f"gunluk-2026-10-{no:02}.odbak", no=no)
    _yedek(yedekler, "pre-migrate-0.2.0-2026-10-30.odbak")
    _yedek(yedekler, "pre-parola-acilis-2026-10-20-101530.odbak")
    _yedek(yedekler, "pre-kapanis-2026-11-01.odbak")
    _yedek(yedekler, f"{UYDURMA_KISI_KISA}.odbak")
    (yedekler / "gunluk-2026-11-01.odbak").write_bytes(b"bozuk")
    an = timezone.localtime().replace(microsecond=0)
    _yedek_satiri(an=an - timedelta(seconds=1), dosya_sayisi=1200, eksik=35)
    dis_yedek.indirme_kaydet(an)

    pdf = _pdf(_bas(client))

    assert len(PdfReader(BytesIO(pdf)).pages) == 1


def test_rapor_kisisizdir(client: APIClient, yedekler: Path) -> None:
    """Kişi adı, yol ve elle adlandırılmış dosyanın adı basılmaz (plan: "kişisiz PDF")."""
    okul = SchoolConfig.load()
    okul.principal_name = UYDURMA_KISI
    okul.save()
    _yedek(yedekler, f"{UYDURMA_KISI_KISA}-yedegi.odbak")
    _yedek(yedekler, "pre-migrate-Uydurgul-Masalcioglu-2020-01-01.odbak")

    metin = _metin(_pdf(_bas(client)))

    assert UYDURMA_KISI_KISA not in metin
    assert "Masalcioglu" not in metin
    assert "Deneme" not in metin
    assert str(yedekler) not in metin
    assert "odbak" not in metin


def test_yanit_pdf_no_store_ve_ek(client: APIClient) -> None:
    yanit = _bas(client)
    assert _pdf(yanit).startswith(b"%PDF")

    assert yanit["Content-Type"] == "application/pdf"
    assert yanit["Cache-Control"] == "no-store"
    assert f"{timezone.localdate():%d.%m.%Y}" in unquote(yanit["Content-Disposition"])
    assert "Yedek-Raporu_" in unquote(yanit["Content-Disposition"])


def test_dosya_adi_belge_adindan_kurulur() -> None:
    assert yedek_raporu.dosya_adi(date(2026, 11, 6)) == "Yedek-Raporu_06.11.2026.pdf"


def test_dosyasi_saklanmaz(client: APIClient, yedekler: Path, veri_dizini: Path) -> None:
    onceki = sorted(yol.name for yol in veri_dizini.rglob("*"))

    _pdf(_bas(client))

    assert sorted(yol.name for yol in veri_dizini.rglob("*")) == onceki


# ----------------------------------------------------------------- basım izi ve yetki


def test_basim_basim_satiridir_kod_ve_pdfin_ozeti(client: APIClient) -> None:
    pdf = _pdf(_bas(client))

    satir = _basim_satirlari()[-1]
    assert satir.model == denetim_izi.YEDEK_RAPORU
    assert satir.object_id == yedek_raporu.KIMLIK
    assert satir.values == {
        "kod": [None, yedek_raporu.KOD],
        "sha256": [None, hashlib.sha256(pdf).hexdigest()],
    }
    assert satir.changed_fields == []


def test_her_basim_ayri_satirdir(client: APIClient) -> None:
    _pdf(_bas(client))
    _pdf(_bas(client))

    assert len(_basim_satirlari()) == 2


def test_basim_kodu_e_kodu_degildir_ve_baska_ad_kabul_edilmez() -> None:
    """Tasarım §9.7: program belgesi E-kodu almaz; kod kümesi yine kapalıdır."""
    assert yedek_raporu.KOD == "YEDEK-RAPORU"
    with yazar_olarak(varsayilan_yazar()), transaction.atomic():
        for kod in ("YEDEK-RAPORU-2", "YEDEK", "yedek-raporu", UYDURMA_KISI):
            with pytest.raises(denetim_izi.IzYazilamadi):
                denetim_izi.basim(
                    model=denetim_izi.YEDEK_RAPORU,
                    object_id=yedek_raporu.KIMLIK,
                    kod=kod,
                    sha256="0" * 64,
                )


def test_satir_yazilamazsa_pdf_verilmez(client: APIClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def patlar(**_: Any) -> Any:
        raise denetim_izi.IzYazilamadi("uydurma")

    monkeypatch.setattr(denetim_izi, "basim", patlar)

    yanit = _bas(client)

    assert yanit.status_code == 409
    assert yanit.json()["code"] == "iz_yazilamadi"
    assert not yanit.headers.get("Content-Disposition")


@pytest.mark.parametrize("rol", [rol.value for rol in AccountRole if rol != AccountRole.YONETICI])
def test_yalniz_program_yoneticisi_basar(client: APIClient, rol: str) -> None:
    oturumu_ac_test("0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e30", tanitici="uydurma", rol=rol)
    son = denetim_izi.zincir_basi()

    yanit = _bas(client)

    assert yanit.status_code == 403
    assert yanit.json()["code"] == "rol_yetkisiz"
    assert denetim_izi.zincir_basi() == son


def test_yetenek_ve_rol_kapisi_ucu_yalniz_guvenlik_satirina_baglar() -> None:
    assert ("backup-report", "POST") in rol_izinleri.YETENEKLER["guvenlik"]


def test_servis_de_yetkiyi_sorar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rol kapısının ardından servis de sorar: ret PDF çizilmeden verilir."""
    cizildi: list[str] = []

    def ciz(html: str) -> bytes:
        cizildi.append(html)
        return b""

    monkeypatch.setattr(yedek_raporu, "html_to_pdf", ciz)
    muhasip = Yazar(hesap_id=TEST_HESAP_ID, rol=AccountRole.MUHASIP.value)

    with yazar_olarak(muhasip), pytest.raises(RolYetkisiz):
        yedek_raporu.yedek_raporu()

    assert cizildi == []


@pytest.mark.usefixtures("kilitli")
def test_kilitliyken_kapalidir(client: APIClient) -> None:
    yanit = _bas(client)

    assert yanit.status_code == 423
    assert yanit.json()["code"] == "locked"


def test_gunluge_yol_ve_ad_dusmez(
    client: APIClient, yedekler: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _yedek(yedekler, f"{UYDURMA_KISI_KISA}-yedegi.odbak")
    (yedekler / f"{UYDURMA_KISI_KISA}-bozuk.odbak").write_bytes(b"bozuk")

    with caplog.at_level(logging.DEBUG):
        _pdf(_bas(client))

    assert UYDURMA_KISI_KISA not in caplog.text
    assert str(yedekler) not in caplog.text
