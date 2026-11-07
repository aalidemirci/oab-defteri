"""Dış yedek hatırlatması (tasarım §16 R6) — servis ve `backups/external/` ucu.

Kanıtlanan maddeler:

* şifreli yedeğin kaydedilmesi (`POST backups/encrypted/`) son yedeğin tarihini veri
  dizinindeki `dis-yedek.json`'a yazar; veritabanına YAZMAZ (geri yükleme geri sarmaz);
* hiç kayıt yokken hatırlatma parola kurulumundan 7 gün sonra, kayıt varken son
  kayıttan `hatirlatma_gun` (varsayılan 30) gün sonra başlar;
* süre 7-90 gün arasında ayarlanır; aralık dışı 400; bozuk dosya "hiç kayıt yok" sayılır;
* uç kilitliyken 423 (rol izni `rol_izinleri.KURALLAR`'da); yanıtta kişisel veri yok;
* son şifreli yedek denemesi `dis-yedek.json`'da durur, uçtan döner, hatırlatmaya dokunmaz; yazımı
  hata yükseltmez, okuması biçimi tutmayan alanı `null` yapar (kullanıcı kararı 06.11.2026);
* dosya bir anlık okunamazsa son deneme ve süre ayarı onun üstüne yazmaz, hatırlatma alanları kalır;
  yazanlar aynı kilidi tutar; tarih aralığını taşan damga ve yazılamayacak kayıt okunamamış sayılır.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul.services import app_password, backup_restore, dis_yedek

URL = "/api/v1/backups/external/"
RAPOR_URL = "/api/v1/backups/report/"
#: Biçimi geçerli, yerel saate çevrilemeyen damgalar: tarih aralığının iki ucu (`OverflowError`).
TASAN_DAMGALAR = [
    "0001-01-01T00:00:00+03:00",
    "0001-01-01T00:00:00+14:00",
    "9999-12-31T23:59:59-12:00",
    "9999-12-31T23:59:59-14:00",
]
#: Yerel saate çevrilir, okumadan geçer; raporun bir saniyelik payı tarih aralığını taşırır.
SON_SANIYE_DAMGALARI = ["9999-12-31T23:59:59+03:00", "9999-12-31T20:59:59+00:00"]

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _kurulum_tarihini_yaz(gun: date) -> None:
    """Güvenlik dosyasının oluşturma damgasını geriye alır (parola `gun` günü kurulmuş)."""
    durum = app_password.read_state()
    assert durum is not None
    an = timezone.make_aware(datetime(gun.year, gun.month, gun.day, 9, 0))
    durum["olusturma"] = an.isoformat(timespec="seconds")
    app_password._write_state(durum)  # noqa: SLF001


def test_parola_kurulur_kurulmaz_hatirlatma_yok() -> None:
    bugun = timezone.localdate()
    _kurulum_tarihini_yaz(bugun)

    ozet = dis_yedek.durum(bugun)

    assert ozet.son_indirme is None
    assert ozet.hatirlatma_gun == dis_yedek.VARSAYILAN_HATIRLATMA_GUN == 30
    assert ozet.gecen_gun == 0
    assert ozet.hatirlat is False


def test_hic_indirme_yoksa_parola_kurulumundan_yedi_gun_sonra_hatirlatir() -> None:
    bugun = date(2026, 9, 27)
    _kurulum_tarihini_yaz(bugun - timedelta(days=6))
    assert dis_yedek.durum(bugun).hatirlat is False

    _kurulum_tarihini_yaz(bugun - timedelta(days=7))
    ozet = dis_yedek.durum(bugun)
    assert ozet.hatirlat is True
    assert ozet.gecen_gun == 7
    assert ozet.son_indirme is None


def test_kurtarmayla_tasinan_kurulumda_kart_hemen_cikar() -> None:
    """Yeni bilgisayara kurtarma anahtarıyla geri yüklenen kurulum (TK10): yedek başlığı
    `olusturma` taşımaz; damga kurtarma anahtarının üretim günüdür, yani eski bir tarih
    (`backup_restore._creation_stamp`). Yeni diskte henüz dış kopya yoktur."""
    baslik = {
        "surum": 2,
        "kdf": {},
        "kurtarma": {"no": 3, "tarih": "2026-09-01", "salt": "dHV6", "sarmal": "s"},
    }
    yazilan = backup_restore._state_from_header(baslik)
    assert yazilan["olusturma"].startswith("2026-09-01T00:00:00")
    app_password._write_state(yazilan)

    ozet = dis_yedek.durum(date(2026, 11, 1))

    assert ozet.hatirlat is True and ozet.gecen_gun == 61
    # Kurtarma bölümünde tarih yoksa geri yükleme anı yazılır.
    tarihsiz = backup_restore._state_from_header({"surum": 2, "kdf": {}, "kurtarma": {}})
    assert datetime.fromisoformat(tarihsiz["olusturma"]).date() == timezone.localdate()


def test_indirme_saati_sifirlar_ve_sure_dolunca_hatirlatir() -> None:
    _kurulum_tarihini_yaz(date(2026, 1, 1))
    indirme = timezone.make_aware(datetime(2026, 9, 1, 14, 30))
    dis_yedek.indirme_kaydet(indirme)

    assert dis_yedek.durum(date(2026, 9, 30)).hatirlat is False  # 29 gün
    ozet = dis_yedek.durum(date(2026, 10, 1))  # 30 gün
    assert ozet.hatirlat is True
    assert ozet.gecen_gun == 30
    assert ozet.son_indirme is not None and ozet.son_indirme.startswith("2026-09-01T14:30")


def test_sifreli_yedek_kaydi_tarihi_veri_dizinine_yazar(
    client: APIClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Görüntünün kaynağı dosya tabanlı bir SQLite olmalıdır (test DB'si değil).
    kaynak = tmp_path / "db.sqlite3"
    with closing(sqlite3.connect(kaynak)) as baglanti:
        baglanti.execute("CREATE TABLE deneme (deger TEXT)")
        baglanti.commit()
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", kaynak)
    yol = dis_yedek.dosya_yolu()
    assert not yol.exists()

    usb = tmp_path / "usb"
    usb.mkdir()
    hedef = usb / "oab-defteri-yedek-2026-11-06-101530.odbak"
    yanit = client.post("/api/v1/backups/encrypted/", {"hedef": str(hedef)}, format="json")

    assert yanit.status_code == 200
    kayit = json.loads(yol.read_text(encoding="utf-8"))
    assert kayit["son_indirme"].startswith(timezone.localdate().isoformat())
    assert kayit["hatirlatma_gun"] == 30
    # Dosya güvenlik dosyasının yanındadır (veritabanında değil — geri yükleme geri sarmaz).
    assert yol.parent == app_password.state_path().parent
    ozet = client.get(URL).json()
    assert ozet["days_since"] == 0
    assert ozet["remind"] is False


def test_hatirlatma_suresi_ayarlanir_ve_aralik_disi_reddedilir(client: APIClient) -> None:
    yanit = client.put(URL, {"reminder_days": 60}, format="json")

    assert yanit.status_code == 200
    assert yanit.json()["reminder_days"] == 60
    assert dis_yedek.durum().hatirlatma_gun == 60
    # İndirme kaydı süreyi korur.
    dis_yedek.indirme_kaydet()
    assert dis_yedek.durum().hatirlatma_gun == 60

    for gecersiz in (6, 91, "otuz", None):
        ret = client.put(URL, {"reminder_days": gecersiz}, format="json")
        assert ret.status_code == 400, gecersiz
        assert "7 ile 90 gün" in json.dumps(ret.json(), ensure_ascii=False)
    assert dis_yedek.durum().hatirlatma_gun == 60


def test_bozuk_dosya_hic_indirme_yok_sayilir_ve_yazim_onarir() -> None:
    dis_yedek.dosya_yolu().write_text("{bozuk", encoding="utf-8")

    assert dis_yedek.durum().son_indirme is None
    dis_yedek.indirme_kaydet()
    assert dis_yedek.durum().son_indirme is not None


def test_yazilamayan_dosya_indirmeyi_durdurmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    def patla(_veri: dict[str, Any]) -> None:
        raise OSError("disk dolu")

    monkeypatch.setattr(dis_yedek, "_yaz", patla)

    dis_yedek.indirme_kaydet()  # hata yükseltmez


def test_yanit_kisisel_veri_tasimaz(client: APIClient) -> None:
    govde = client.get(URL).json()

    assert set(govde) == {
        "last_download",
        "reminder_days",
        "days_since",
        "remind",
        "min_reminder_days",
        "max_reminder_days",
        "son_deneme",
    }
    assert govde["son_deneme"] is None


# ---------------------------------------------------------------------------
# Son deneme (kullanıcı kararı 06.11.2026 "Son şifreli yedek denemesi saklanır")
# ---------------------------------------------------------------------------
def _ham_kayit() -> dict[str, Any]:
    kayit: dict[str, Any] = json.loads(dis_yedek.dosya_yolu().read_text(encoding="utf-8"))
    return kayit


def _kaydi_yaz(veri: Any) -> None:
    dis_yedek.dosya_yolu().parent.mkdir(parents=True, exist_ok=True)
    dis_yedek.dosya_yolu().write_text(json.dumps(veri), encoding="utf-8")


def test_basarili_deneme_uctan_doner_an_yerel_saattedir(client: APIClient) -> None:
    dis_yedek.deneme_basarili(boyut=13_107_200, ek_sayisi=3, eksik=1)

    deneme = client.get(URL).json()["son_deneme"]

    assert set(deneme) == {"an", "sonuc", "boyut", "ek_sayisi", "eksik", "ileti"}
    assert deneme["sonuc"] == "basarili"
    assert (deneme["boyut"], deneme["ek_sayisi"], deneme["eksik"]) == (13_107_200, 3, 1)
    assert deneme["ileti"] is None
    assert deneme["an"] == datetime.fromisoformat(deneme["an"]).isoformat(timespec="seconds")
    assert datetime.fromisoformat(deneme["an"]).utcoffset() == timedelta(hours=3)


def test_basarisiz_deneme_iletiyi_tasir_sayi_tasimaz(client: APIClient) -> None:
    dis_yedek.deneme_basarisiz("Seçilen yerde yeterli boş yer yok; şifreli yedek alınmadı.")

    deneme = client.get(URL).json()["son_deneme"]

    assert deneme["sonuc"] == "basarisiz"
    assert deneme["ileti"] == "Seçilen yerde yeterli boş yer yok; şifreli yedek alınmadı."
    assert (deneme["boyut"], deneme["ek_sayisi"], deneme["eksik"]) == (None, None, None)


def test_son_deneme_oncekini_ezer() -> None:
    dis_yedek.deneme_basarisiz("Şifreli yedek oluşturulamadı.")
    dis_yedek.deneme_basarili(boyut=1, ek_sayisi=0, eksik=0)

    ozet = dis_yedek.durum().son_deneme

    assert ozet is not None
    assert ozet["sonuc"] == "basarili"
    assert ozet["ileti"] is None


def test_deneme_hatirlatma_alanlarina_dokunmaz() -> None:
    an = timezone.make_aware(datetime(2026, 10, 1, 9, 0))
    dis_yedek.indirme_kaydet(an)
    dis_yedek.hatirlatma_suresini_ayarla(14)
    once = _ham_kayit()

    dis_yedek.deneme_basarisiz("Şifreli yedek oluşturulamadı.")
    dis_yedek.deneme_basarili(boyut=1, ek_sayisi=0, eksik=0)

    sonra = _ham_kayit()
    assert sonra["son_indirme"] == once["son_indirme"]
    assert sonra["hatirlatma_gun"] == once["hatirlatma_gun"] == 14


def test_hatirlatma_yazimlari_son_denemeyi_silmez() -> None:
    dis_yedek.deneme_basarili(boyut=7, ek_sayisi=2, eksik=0)

    dis_yedek.indirme_kaydet()
    dis_yedek.hatirlatma_suresini_ayarla(14)

    ozet = dis_yedek.durum().son_deneme
    assert ozet is not None
    assert ozet["boyut"] == 7


def test_hic_kayit_yoksa_ve_kurulum_yoksa_da_son_deneme_doner(parolasiz: Path) -> None:
    dis_yedek.deneme_basarisiz("Şifreli yedek oluşturulamadı.")

    ozet = dis_yedek.durum().son_deneme

    assert ozet is not None
    assert ozet["sonuc"] == "basarisiz"


def test_tarihli_kayitta_da_son_deneme_doner() -> None:
    dis_yedek.indirme_kaydet()
    dis_yedek.deneme_basarili(boyut=7, ek_sayisi=2, eksik=0)

    assert dis_yedek.durum().son_deneme is not None


@pytest.mark.parametrize(
    "hata", [OSError("/uydurma/yol"), ValueError("/uydurma/yol")], ids=["os", "beklenmedik"]
)
def test_deneme_yazilamazsa_hata_yukselmez_gunluge_yol_gitmez(
    hata: Exception, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def yazilamadi(_veri: dict[str, Any]) -> None:
        raise hata

    monkeypatch.setattr(dis_yedek, "_yaz", yazilamadi)

    with caplog.at_level(logging.DEBUG):
        dis_yedek.deneme_basarisiz("Şifreli yedek oluşturulamadı.")
        dis_yedek.deneme_basarili(boyut=1, ek_sayisi=0, eksik=0)

    assert type(hata).__name__ in caplog.text
    assert "/uydurma/yol" not in caplog.text
    assert not dis_yedek._kilit.locked()


@pytest.mark.parametrize(
    "ham",
    [
        None,
        "basarili",
        [],
        {},
        {"an": "2026-11-06T10:00:00+03:00"},
        {"sonuc": "basarili"},
        {"an": "dun", "sonuc": "basarili"},
        {"an": 5, "sonuc": "basarili"},
        {"an": "2026-11-06T10:00:00+03:00", "sonuc": "yarim"},
        {"an": "2026-11-06T10:00:00+03:00", "sonuc": ["basarili"]},
        *[{"an": damga, "sonuc": "basarisiz", "ileti": "x"} for damga in TASAN_DAMGALAR],
    ],
    ids=[
        "bos",
        "metin",
        "liste",
        "alansiz",
        "sonucsuz",
        "zamansiz",
        "zaman_bozuk",
        "zaman_sayi",
        "sonuc_bilinmiyor",
        "sonuc_liste",
        *[f"zaman_tasiyor_{sira}" for sira in range(len(TASAN_DAMGALAR))],
    ],
)
def test_zamani_ya_da_sonucu_okunamayan_deneme_yok_sayilir(ham: Any, client: APIClient) -> None:
    _kaydi_yaz({"surum": 1, "son_deneme": ham})

    assert client.get(URL).json()["son_deneme"] is None


@pytest.mark.parametrize(
    ("alan", "deger"),
    [
        ("boyut", "12"),
        ("boyut", -1),
        ("boyut", True),
        ("boyut", 1.5),
        ("ek_sayisi", "3"),
        ("eksik", {"sayi": 1}),
        ("ileti", 7),
        ("ileti", ""),
        ("ileti", ["metin"]),
    ],
)
def test_bicimi_tutmayan_alan_null_doner_oteki_alanlar_kalir(
    alan: str, deger: Any, client: APIClient
) -> None:
    saglam = {
        "an": "2026-11-06T10:00:00+03:00",
        "sonuc": "basarili",
        "boyut": 10,
        "ek_sayisi": 2,
        "eksik": 1,
        "ileti": "uydurma",
    }
    _kaydi_yaz({"surum": 1, "son_deneme": {**saglam, alan: deger}})

    deneme = client.get(URL).json()["son_deneme"]

    assert deneme == {**saglam, alan: None}


def test_bozuk_dosyada_son_deneme_yoktur(client: APIClient) -> None:
    dis_yedek.dosya_yolu().parent.mkdir(parents=True, exist_ok=True)
    dis_yedek.dosya_yolu().write_text("{bozuk", encoding="utf-8")

    assert client.get(URL).json()["son_deneme"] is None


@pytest.mark.parametrize(
    "damga", ["2026-11-06T07:00:00+00:00", "2026-11-06T10:00:00"], ids=["utc", "dilimsiz"]
)
def test_damga_yerel_saate_cevrilir(damga: str, client: APIClient) -> None:
    _kaydi_yaz({"surum": 1, "son_indirme": damga, "son_deneme": {"an": damga, "sonuc": "basarili"}})

    govde = client.get(URL).json()

    assert govde["last_download"] == "2026-11-06T10:00:00+03:00"
    assert govde["son_deneme"]["an"] == "2026-11-06T10:00:00+03:00"


@pytest.mark.parametrize("damga", TASAN_DAMGALAR)
def test_tasan_son_indirme_hic_kayit_yok_sayilir(damga: str, client: APIClient) -> None:
    _kaydi_yaz({"surum": 1, "son_indirme": damga})

    assert client.get(URL).json()["last_download"] is None


def test_tasan_damga_ayar_ucunu_ve_raporu_dusurmez(client: APIClient) -> None:
    """`durum()`'u bu iki uç da okur; ayar ucunda süre yazıldıktan sonra okunur."""
    damga = TASAN_DAMGALAR[0]
    _kaydi_yaz({"surum": 1, "son_indirme": damga, "son_deneme": {"an": damga, "sonuc": "basarili"}})

    ayar = client.put(URL, {"reminder_days": 14}, format="json")

    assert ayar.status_code == 200
    assert ayar.json()["reminder_days"] == 14
    assert client.post(RAPOR_URL).status_code == 200


@pytest.mark.parametrize("damga", SON_SANIYE_DAMGALARI)
def test_tarih_araliginin_son_saniyesi_raporu_dusurmez(damga: str, client: APIClient) -> None:
    _kaydi_yaz({"surum": 1, "son_indirme": damga})

    assert client.get(URL).json()["last_download"] is not None
    assert client.post(RAPOR_URL).status_code == 200


def test_tasan_kurulum_damgasi_gun_sayisi_vermez() -> None:
    durum = app_password.read_state()
    assert durum is not None
    durum["olusturma"] = TASAN_DAMGALAR[0]
    app_password._write_state(durum)  # noqa: SLF001

    ozet = dis_yedek.durum()

    assert ozet.gecen_gun is None
    assert ozet.hatirlat is False


@pytest.mark.parametrize("derinlik", [5_000, 200_000], ids=["yazilamayan", "okunamayan"])
def test_derin_ic_ice_kayit_hic_kayit_yok_sayilir_yazim_onarir(
    derinlik: int, client: APIClient
) -> None:
    """Okuma yaklaşık on bin katta düşer, girintili yazım bin katta: ikisi de bozuk kayıttır."""
    dosya = dis_yedek.dosya_yolu()
    dosya.parent.mkdir(parents=True, exist_ok=True)
    dosya.write_text('{"son_deneme": ' + "[" * derinlik + "]" * derinlik + "}", encoding="utf-8")

    assert client.get(URL).json()["son_deneme"] is None
    dis_yedek.indirme_kaydet()  # hata yükseltmez

    assert dis_yedek.durum().son_indirme is not None


def test_utf8e_cevrilemeyen_kayit_hic_kayit_yok_sayilir(client: APIClient) -> None:
    """Tek vekil karakter JSON'dan okunur, ama ne yanıta çizilir ne dosyaya yazılabilir."""
    an = "2026-11-06T10:00:00+03:00"
    _kaydi_yaz({"surum": 1, "son_deneme": {"an": an, "sonuc": "basarisiz", "ileti": "yarım\ud83d"}})

    assert client.get(URL).json()["son_deneme"] is None
    dis_yedek.indirme_kaydet()  # hata yükseltmez

    assert dis_yedek.durum().son_indirme is not None


def _bir_kez_okunamasin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Başka bir süreç dosyayı bir anlık tutar (Windows'ta antivirüs): okuma düşer, sonra geçer."""
    dosya = dis_yedek.dosya_yolu()
    asil = Path.read_text
    hatalar = [PermissionError("/uydurma/yol")]

    def oku(yol: Path, *args: Any, **kwargs: Any) -> str:
        if yol == dosya and hatalar:
            raise hatalar.pop()
        return asil(yol, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", oku)


def _dolu_kayit() -> dict[str, Any]:
    dis_yedek.indirme_kaydet(timezone.make_aware(datetime(2026, 10, 1, 9, 0)))
    dis_yedek.hatirlatma_suresini_ayarla(14)
    dis_yedek.deneme_basarili(boyut=7, ek_sayisi=2, eksik=0)
    return _ham_kayit()


def test_okunamayan_dosyada_deneme_hatirlatma_alanlarini_silmez(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    once = _dolu_kayit()
    _bir_kez_okunamasin(monkeypatch)

    with caplog.at_level(logging.DEBUG):
        dis_yedek.deneme_basarisiz("Şifreli yedek oluşturulamadı.")  # hata yükseltmez

    assert _ham_kayit() == once
    assert "PermissionError" in caplog.text
    assert "/uydurma/yol" not in caplog.text


def test_okunamayan_dosyada_sure_ayari_oteki_alanlari_silmez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    once = _dolu_kayit()
    _bir_kez_okunamasin(monkeypatch)

    with pytest.raises(PermissionError):
        dis_yedek.hatirlatma_suresini_ayarla(60)

    assert _ham_kayit() == once


def test_okunamayan_dosyada_durum_hic_kayit_yok_sayar(monkeypatch: pytest.MonkeyPatch) -> None:
    _dolu_kayit()
    _bir_kez_okunamasin(monkeypatch)

    assert dis_yedek.durum().son_indirme is None  # hata yükseltmez
    assert dis_yedek.durum().son_indirme is not None  # kayıt yerindedir


def test_okunamayan_dosyada_yedegin_tarihi_yine_yazilir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hatırlatma başarıda sıfırlanır: yedek yerindedir, dosyanın okunamaması tarihi engellemez."""
    _dolu_kayit()
    an = timezone.make_aware(datetime(2026, 11, 2, 9, 0))
    _bir_kez_okunamasin(monkeypatch)

    dis_yedek.indirme_kaydet(an)

    son = dis_yedek.durum().son_indirme
    assert son is not None and son.startswith("2026-11-02T09:00")


def test_deneme_yazimi_dosya_kilidini_bekler() -> None:
    """Ayar yazımıyla aynı anda oku-yaz yapılmaz: alanlar ezilir, sabit `.tmp` adı çakışır."""
    yazici = threading.Thread(
        target=dis_yedek.deneme_basarisiz, args=("Şifreli yedek oluşturulamadı.",)
    )

    with dis_yedek._kilit:
        yazici.start()
        yazici.join(0.3)
        assert yazici.is_alive()
        assert not dis_yedek.dosya_yolu().exists()

    yazici.join(5)
    assert not yazici.is_alive()
    assert dis_yedek.dosya_yolu().exists()


def test_parola_kurulmamissa_hatirlatma_yok(parolasiz: Path, client: APIClient) -> None:
    ozet = client.get(URL).json()

    assert ozet["remind"] is False
    assert ozet["days_since"] is None


def test_kilitliyken_kapali(kilitli: Path, client: APIClient) -> None:
    yanit = client.get(URL)

    assert yanit.status_code == 423
    assert yanit.json()["code"] == "locked"
