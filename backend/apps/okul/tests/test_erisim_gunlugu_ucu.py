"""Erişim günlüğünün okuma ucu (plan F1b-2 "Erişim günlüğü okuma ucu"; tasarım §4.6.4, §4.4.2).

`GET access-log/`, program yöneticisi ve Denetleme Kurulu: süzgeçler tarih aralığı (Europe/Istanbul
günü, iki uç dahil), tür ve hesap; sayfalı, en yeni önce; ad-soyad yok (hesap rol etiketi ve
tanıtıcıyla); okuma iz bırakmaz (ne denetim izi ne erişim günlüğü satırı). Türlerin görünen adları
sözlüktedir; özel nitelikli türlerde KVKK md. 6/1'in sözü kullanılır.

Adlar ve numaralar uydurmadır; gerçek kişi değildir.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul import erisim_gunlugu, rol_izinleri
from apps.okul.models import (
    AccessKind,
    AccessLog,
    Account,
    AccountRole,
    AccountStatus,
    AuditTrail,
    Student,
)
from apps.okul.oturum import SISTEM, Yazar, yazar_olarak
from apps.okul.services import hesaplar
from apps.okul.tests.hesap_ortak import ham_guncelle, hesap_ac, muhurle
from conftest import TEST_HESAP_ID, TEST_TANITICI, oturumu_ac_test
from shared.exceptions import RolYetkisiz

pytestmark = pytest.mark.django_db

YOL = "/api/v1/access-log/"
#: Uydurma ad-soyadlar (yanıtta aranır; hiçbir yerde görünmemeli).
MUHASIP_ADI = "Uydurcan Hayalgüloğlu"
DK_ADI = "Örnekay Düşlemeli"
OZET = "cd" * 32


def yerel(
    yil: int, ay: int, gun: int, saat: int = 12, dakika: int = 0, saniye: int = 0
) -> datetime:
    """Europe/Istanbul'da verilen an (saat dilimli)."""
    return timezone.make_aware(datetime(yil, ay, gun, saat, dakika, saniye))


def satir(an: datetime, **alanlar: Any) -> AccessLog:
    """Verilen anlı satır (yazıcı anı kendisi koyar; geçmiş satır taklidi doğrudan yazılır)."""
    varsayilan: dict[str, Any] = {
        "account_id": TEST_HESAP_ID,
        "role": "yonetici",
        "kind": AccessKind.KISI_DOKUMU,
        "model": "okul.Student",
        "object_id": "7",
    }
    return AccessLog.objects.create(at=an, **{**varsayilan, **alanlar})


def _oku(**sorgu: Any) -> Any:
    return APIClient().get(YOL, sorgu)


def _gun(an: Any) -> str | None:
    """Hesabın Europe/Istanbul günü, yyyy-aa-gg (hesap özetinin `acilis`/`kapanis` biçimi; F-3)."""
    return None if an is None else f"{timezone.localtime(an):%Y-%m-%d}"


def _muhasip() -> Account:
    return muhurle(hesap_ac(AccountRole.MUHASIP, ad=MUHASIP_ADI), status=AccountStatus.ACIK)


def _dk() -> Account:
    return muhurle(
        hesap_ac(AccountRole.DENETLEME_KURULU, ad=DK_ADI, tanitici="dk-1"),
        status=AccountStatus.ACIK,
    )


# ============================================================ rol


@pytest.mark.parametrize("rol", rol_izinleri.ROLLER)
def test_yalniz_program_yoneticisi_ve_denetleme_kurulu_okur(rol: str) -> None:
    """Matrisin "Erişim günlüğü" satırı: program yöneticisi ve DK okur, öteki roller "—"."""
    satir(yerel(2026, 11, 1))
    oturumu_ac_test("0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", tanitici=rol, rol=rol)

    yanit = _oku()

    if rol in ("yonetici", "denetleme_kurulu"):
        assert yanit.status_code == 200, yanit.content
        assert yanit.json()["toplam"] == 1
    else:
        assert yanit.status_code == 403
        assert yanit.json()["code"] == "rol_yetkisiz"
    assert APIClient().head(YOL).status_code == yanit.status_code


@pytest.mark.parametrize(
    "kim",
    [
        None,
        SISTEM,
        Yazar(hesap_id=TEST_HESAP_ID, rol="muhasip"),
        Yazar(hesap_id=TEST_HESAP_ID, rol="mudur"),
    ],
    ids=["yazarsiz", "sistem", "muhasip", "mudur"],
)
def test_servis_de_rolu_sorar(kim: Yazar | None) -> None:
    """Derin savunma: rol kapısının ardından servis de yazarın rolünü matrisin satırıyla sınar."""
    with yazar_olarak(kim), pytest.raises(RolYetkisiz):
        erisim_gunlugu.liste()


def test_servis_program_yoneticisi_ve_dk_yazariyla_okur() -> None:
    for rol in ("yonetici", "denetleme_kurulu"):
        with yazar_olarak(Yazar(hesap_id=TEST_HESAP_ID, rol=rol)):
            assert erisim_gunlugu.liste()["toplam"] == 0


# ============================================================ satırlar, sıra, sayfa


def test_en_yeni_once_ve_sayfali() -> None:
    bas = yerel(2026, 10, 1)
    for i in range(erisim_gunlugu.SAYFA_BOYUTU * 2 + 20):
        satir(bas + timedelta(minutes=i), object_id=str(i))

    ilk = _oku().json()
    ucuncu = _oku(sayfa=3).json()
    fazla = _oku(sayfa=4).json()

    toplam = erisim_gunlugu.SAYFA_BOYUTU * 2 + 20
    assert (ilk["toplam"], ilk["sayfa"], ilk["sayfa_sayisi"]) == (toplam, 1, 3)
    assert ilk["sayfa_boyutu"] == erisim_gunlugu.SAYFA_BOYUTU
    assert [s["kayit"] for s in ilk["satirlar"]] == [
        str(i) for i in range(toplam - 1, toplam - 1 - erisim_gunlugu.SAYFA_BOYUTU, -1)
    ]
    assert [s["kayit"] for s in ucuncu["satirlar"]] == [str(i) for i in range(19, -1, -1)]
    assert fazla["satirlar"] == [] and fazla["sayfa"] == 4 and fazla["sayfa_sayisi"] == 3
    zamanlar = [s["zaman"] for s in ilk["satirlar"]]
    assert zamanlar == sorted(zamanlar, reverse=True)


def test_ayni_anda_yazilan_satirlar_yeniden_eskiye_kimlikle_siralanir() -> None:
    an = yerel(2026, 11, 1)
    once = satir(an, object_id="1")
    sonra = satir(an, object_id="2")
    assert [s["id"] for s in _oku().json()["satirlar"]] == [sonra.pk, once.pk]


def test_bos_gunluk_tek_bos_sayfadir() -> None:
    govde = _oku().json()
    assert (govde["satirlar"], govde["toplam"], govde["sayfa"], govde["sayfa_sayisi"]) == (
        [],
        0,
        1,
        1,
    )
    assert govde["hesaplar"] == []


def test_satir_kisisizdir_hesap_rol_etiketi_ve_taniticiyla_anilir() -> None:
    """Ad-soyad yok; okuyan hesap rol etiketi (sıra no'suz, satırdaki rol) ve tanıtıcıyla; okunan
    kaydın kimliği ve alanı, çıktının özeti ve satır sayısı olduğu gibi."""
    muhasip = _muhasip()
    dk = _dk()
    with yazar_olarak(Yazar(hesap_id=str(dk.id), rol="denetleme_kurulu")):
        erisim_gunlugu.yaz(
            AccessKind.OZEL_NITELIKLI_ALAN, model=Student, object_id=7, field="first_name"
        )
    satir(
        yerel(2026, 10, 1),
        account_id=str(muhasip.id),
        role="muhasip",
        kind=AccessKind.KISISEL_DISA_AKTARIM,
        model="",
        object_id="",
        document_sha256=OZET,
        row_count=12,
    )

    yanit = _oku()

    metin = yanit.content.decode("utf-8")
    for ad in (MUHASIP_ADI, DK_ADI, *MUHASIP_ADI.split(), *DK_ADI.split()):
        assert ad not in metin, ad
    yeni, eski = yanit.json()["satirlar"]
    assert yeni["hesap"] == {
        "id": str(dk.id),
        "tanitici": "dk-1",
        "rol_etiketi": "Denetleme Kurulu",
        "acilis": _gun(dk.opened_at),
        "kapanis": None,
    }
    assert (yeni["tur"], yeni["tur_adi"]) == (
        "OZEL_NITELIKLI_ALAN",
        "Özel nitelikli kişisel veri alanı",
    )
    assert (yeni["model"], yeni["kayit"], yeni["alan"]) == ("okul.Student", "7", "first_name")
    assert (yeni["belge_ozeti"], yeni["satir_sayisi"]) == (None, None)
    assert eski["hesap"] == {
        "id": str(muhasip.id),
        "tanitici": "muhasip",
        "rol_etiketi": "Muhasip",
        "acilis": _gun(muhasip.opened_at),
        "kapanis": None,
    }
    assert (eski["model"], eski["kayit"], eski["alan"]) == (None, None, None)
    assert (eski["belge_ozeti"], eski["satir_sayisi"]) == (OZET, 12)
    assert eski["zaman"] == "2026-10-01T12:00:00+03:00"
    assert set(yeni) == {
        "id",
        "zaman",
        "hesap",
        "tur",
        "tur_adi",
        "model",
        "kayit",
        "alan",
        "belge_ozeti",
        "satir_sayisi",
    }


def test_secenekler_turler_ve_gunlukte_satiri_olan_hesaplar() -> None:
    """Süzgeç seçenekleri: kapalı tür kümesi görünen adlarıyla; günlükte satırı olan hesaplar (rol
    sırasıyla, kişisiz). Süzgeç seçenekleri sayfaya ve süzgece bağlı değildir."""
    muhasip = _muhasip()
    dk = _dk()
    satir(yerel(2026, 10, 1), account_id=str(dk.id), role="denetleme_kurulu")
    satir(yerel(2026, 10, 2), account_id=str(muhasip.id), role="muhasip")
    satir(yerel(2026, 10, 3))

    govde = _oku(tur=AccessKind.IHLAL_DOKUMU).json()

    assert govde["toplam"] == 0
    assert govde["turler"] == [
        {"tur": tur, "tur_adi": erisim_gunlugu.TUR_ADLARI[tur]} for tur in AccessKind.values
    ]
    yonetici = Account.objects.get(pk=TEST_HESAP_ID)
    assert govde["hesaplar"] == [
        {
            "id": TEST_HESAP_ID,
            "tanitici": TEST_TANITICI,
            "rol_etiketi": "Program yöneticisi",
            "acilis": _gun(yonetici.opened_at),
            "kapanis": None,
        },
        {
            "id": str(muhasip.id),
            "tanitici": "muhasip",
            "rol_etiketi": "Muhasip",
            "acilis": _gun(muhasip.opened_at),
            "kapanis": None,
        },
        {
            "id": str(dk.id),
            "tanitici": "dk-1",
            "rol_etiketi": "Denetleme Kurulu",
            "acilis": _gun(dk.opened_at),
            "kapanis": None,
        },
    ]


#: Kimlik sırası açılış sırasının TERSİ (eski hesabın kimliği büyük): seçeneklerin sırası kimliğe
#: kalsaydı yeni hesap önce gelirdi (F-3 testi her koşuda aynı sonucu verir).
ESKI_KIMLIK = uuid.UUID("ffffffff-ffff-4fff-bfff-ffffffffffff")
YENI_KIMLIK = uuid.UUID("00000000-0000-4000-8000-000000000001")


def kimlikleri_sabitle(monkeypatch: pytest.MonkeyPatch, *kimlikler: uuid.UUID) -> None:
    """Sonraki hesap açılışlarına sırayla bu kimlikleri verir (sonra rastgele `uuid4`)."""
    kalan = iter(kimlikler)
    monkeypatch.setattr(
        Account._meta.get_field("id"), "_get_default", lambda: next(kalan, None) or uuid.uuid4()
    )


#: F-3'ün iki kolu: eski hesabın açılış ve kapanış anı, yeni hesabın açılış anı (UTC) ve üç an için
#: beklenen Europe/Istanbul günleri.
F3_KOLLARI: dict[str, tuple[datetime, datetime, datetime, tuple[str, str, str]]] = {
    # Eski hesap geçen yıl açılmış, geçen ay kapanmış; anlar UTC'de gece yarısından önce,
    # Europe/Istanbul'da ertesi gündür (gün yerel gündür).
    "farkli_gun": (
        datetime(2025, 8, 31, 21, 30, tzinfo=UTC),
        datetime(2026, 10, 14, 22, 15, tzinfo=UTC),
        datetime(2026, 10, 15, 6, 0, tzinfo=UTC),
        ("2025-09-01", "2026-10-15", "2026-10-15"),
    ),
    # Yanlış kişiye açılan hesap aynı gün kapatılıp aynı tanıtıcıyla yeniden açılır: üç an aynı
    # yerel gündedir, seçeneklerin sırasını gün değil an verir.
    "ayni_gun": (
        datetime(2026, 10, 15, 5, 0, tzinfo=UTC),
        datetime(2026, 10, 15, 6, 0, tzinfo=UTC),
        datetime(2026, 10, 15, 7, 0, tzinfo=UTC),
        ("2026-10-15", "2026-10-15", "2026-10-15"),
    ),
}


@pytest.mark.parametrize("kol", list(F3_KOLLARI))
def test_ayni_taniticili_eski_ve_yeni_hesap_acilis_ve_kapanisla_ayrilir(
    kol: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Orkestratör maddesi F-3: tanıtıcı yalnız açık hesaplar arasında tekildir; kapanan "muhasip"
    hesabının yerine açılan yeni hesap da "muhasip"tir. Satırların hesap özeti ve hesap seçenekleri
    ikisini açılış ve kapanış günüyle (Europe/Istanbul günü, yyyy-aa-gg; açık hesapta kapanış yok)
    ayırır; seçeneklerde aynı tanıtıcı açılış ANI sırasıyladır — aynı gün kapatılıp yeniden açılan
    hesapta da. Kimlik sırası bilerek açılış sırasının tersine kurulur: sıra kimliğe ya da güne
    kalırsa test her koşuda düşer. Ad-soyad yine yoktur."""
    eski_acilis, eski_kapanis, yeni_acilis, gunler = F3_KOLLARI[kol]
    eski_acilis_gunu, eski_kapanis_gunu, yeni_acilis_gunu = gunler
    kimlikleri_sabitle(monkeypatch, ESKI_KIMLIK, YENI_KIMLIK)
    eski = _muhasip()
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=eski.id)
    eski = muhurle(Account.objects.get(pk=eski.id), opened_at=eski_acilis, closed_at=eski_kapanis)
    yeni = muhurle(
        hesap_ac(AccountRole.MUHASIP, ad="Uydurmaca Yenigelen"),
        status=AccountStatus.ACIK,
        opened_at=yeni_acilis,
    )
    assert (eski.id, yeni.id) == (ESKI_KIMLIK, YENI_KIMLIK)
    assert eski.login_name == yeni.login_name == "muhasip"
    satir(yerel(2026, 10, 1), account_id=str(eski.id), role="muhasip")
    satir(yerel(2026, 10, 20), account_id=str(yeni.id), role="muhasip")

    govde = _oku().json()

    son, ilk = govde["satirlar"]
    assert son["hesap"] == {
        "id": str(yeni.id),
        "tanitici": "muhasip",
        "rol_etiketi": "Muhasip",
        "acilis": yeni_acilis_gunu,
        "kapanis": None,
    }
    assert ilk["hesap"] == {
        "id": str(eski.id),
        "tanitici": "muhasip",
        "rol_etiketi": "Muhasip",
        "acilis": eski_acilis_gunu,
        "kapanis": eski_kapanis_gunu,
    }
    assert [(h["id"], h["acilis"], h["kapanis"]) for h in govde["hesaplar"]] == [
        (str(eski.id), eski_acilis_gunu, eski_kapanis_gunu),
        (str(yeni.id), yeni_acilis_gunu, None),
    ]
    metin = json.dumps(govde, ensure_ascii=False)
    assert MUHASIP_ADI not in metin and "Uydurmaca Yenigelen" not in metin


@pytest.mark.parametrize(
    "bozuk", ["2026-02-30 10:00:00.000000", "9999-12-31 23:59:59.000000", "zzz"]
)
def test_hesabin_bozuk_acilis_ani_ekrani_dusurmez(bozuk: str) -> None:
    """Bağımsız denetim bulgusu (F-3'ün gerilemesi): hesabın açılış ve kapanış anı program dışından
    biçime uyan ama geçersiz (30 Şubat), yerel güne çevrilemeyen (9999'un son saati) ya da biçimsiz
    bir değerle yazılmışsa uç yine 200 döner; o hesabın günleri None'dır (kaydın söylemediği),
    öteki hesaplar etkilenmez. Eskiden ORM'nin tarih dönüştürücüsü ValueError yükseltiyor, uç 400
    ve İngilizce bir iç ileti veriyordu. Hesap kapalıdır: iki an da doludur (veritabanı kısıtı
    kapanışı yalnız kapalı hesapta kabul eder)."""
    muhasip = _muhasip()
    dk = _dk()
    satir(yerel(2026, 10, 1), account_id=str(muhasip.id), role="muhasip")
    satir(yerel(2026, 10, 2), account_id=str(dk.id), role="denetleme_kurulu")
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id)
    ham_guncelle(muhasip.id, opened_at=bozuk, closed_at=bozuk)

    yanit = _oku()

    assert yanit.status_code == 200, yanit.content
    govde = yanit.json()
    secenekler = {h["id"]: h for h in govde["hesaplar"]}
    assert (secenekler[str(muhasip.id)]["acilis"], secenekler[str(muhasip.id)]["kapanis"]) == (
        None,
        None,
    )
    assert secenekler[str(muhasip.id)]["tanitici"] == "muhasip"
    assert secenekler[str(dk.id)]["acilis"] == _gun(dk.opened_at)
    ozetler = {s["hesap"]["id"]: s["hesap"] for s in govde["satirlar"]}
    assert (ozetler[str(muhasip.id)]["acilis"], ozetler[str(muhasip.id)]["kapanis"]) == (None, None)
    assert ozetler[str(dk.id)]["acilis"] == _gun(dk.opened_at)
    # Okunamayan an seçeneklerin rol sırasını bozmaz (muhasip, sonra Denetleme Kurulu).
    assert [h["id"] for h in govde["hesaplar"]][-2:] == [str(muhasip.id), str(dk.id)]


# ============================================================ süzgeçler


def test_tarih_araligi_europe_istanbul_gunudur_iki_uc_dahil() -> None:
    """Başlangıç gününün yerel 00.00'ından bitiş gününün ertesi 00.00'ına dek. Yerel 01.11 00.30
    UTC'de 31.10'dur: yine de 01.11'in satırıdır."""
    for an, ad in (
        (yerel(2026, 10, 31, 23, 59, 59), "dun"),
        (yerel(2026, 11, 1, 0, 0, 0), "gece_yarisi"),
        (yerel(2026, 11, 1, 0, 30), "utc_onceki_gun"),
        (yerel(2026, 11, 1, 23, 59, 59), "gun_sonu"),
        (yerel(2026, 11, 2, 0, 0, 0), "yarin"),
    ):
        satir(an, object_id=ad)

    tek_gun = _oku(baslangic="2026-11-01", bitis="2026-11-01").json()
    yalniz_baslangic = _oku(baslangic="2026-11-01").json()
    yalniz_bitis = _oku(bitis="2026-11-01").json()

    assert [s["kayit"] for s in tek_gun["satirlar"]] == [
        "gun_sonu",
        "utc_onceki_gun",
        "gece_yarisi",
    ]
    assert tek_gun["toplam"] == 3
    assert {s["kayit"] for s in yalniz_baslangic["satirlar"]} == {
        "gece_yarisi",
        "utc_onceki_gun",
        "gun_sonu",
        "yarin",
    }
    assert {s["kayit"] for s in yalniz_bitis["satirlar"]} == {
        "dun",
        "gece_yarisi",
        "utc_onceki_gun",
        "gun_sonu",
    }


def test_tur_ve_hesap_suzgeci_birlikte_uygulanir() -> None:
    muhasip = _muhasip()
    satir(yerel(2026, 10, 1), kind=AccessKind.KISI_DOKUMU, object_id="a")
    satir(
        yerel(2026, 10, 2),
        account_id=str(muhasip.id),
        role="muhasip",
        kind=AccessKind.KISI_DOKUMU,
        object_id="b",
    )
    satir(
        yerel(2026, 10, 3),
        account_id=str(muhasip.id),
        role="muhasip",
        kind=AccessKind.IHLAL_DOKUMU,
        object_id="c",
    )

    def kayitlar(**sorgu: Any) -> list[str]:
        return [s["kayit"] for s in _oku(**sorgu).json()["satirlar"]]

    assert kayitlar(tur=AccessKind.KISI_DOKUMU) == ["b", "a"]
    assert kayitlar(hesap=str(muhasip.id)) == ["c", "b"]
    assert kayitlar(hesap=str(muhasip.id), tur=AccessKind.KISI_DOKUMU) == ["b"]
    assert kayitlar(hesap="9f8e7d6c-5b4a-4c3d-8e2f-1a0b9c8d7e6f") == []
    # Boş değer verilmemiş sayılır; bilinmeyen anahtar yok sayılır.
    assert kayitlar(tur="", hesap="", baslangic="", bilinmeyen="x") == ["c", "b", "a"]


@pytest.mark.parametrize(
    ("sorgu", "ileti"),
    [
        ({"baslangic": "01.11.2026"}, erisim_gunlugu.TARIH_MESAJI),
        ({"bitis": "2026-13-01"}, erisim_gunlugu.TARIH_MESAJI),
        # Takvimin uçları (bağımsız denetim bulgusu): sınır kurulamaz, 500 değil 400.
        ({"bitis": "9999-12-31"}, erisim_gunlugu.TARIH_MESAJI),
        ({"baslangic": "0001-01-01"}, erisim_gunlugu.TARIH_MESAJI),
        ({"baslangic": "2026-11-02", "bitis": "2026-11-01"}, erisim_gunlugu.TARIH_SIRASI_MESAJI),
        ({"tur": "BILINMEYEN"}, erisim_gunlugu.TUR_MESAJI),
        ({"hesap": "muhasip"}, erisim_gunlugu.HESAP_MESAJI),
        ({"sayfa": "0"}, erisim_gunlugu.SAYFA_MESAJI),
        ({"sayfa": "iki"}, erisim_gunlugu.SAYFA_MESAJI),
        ({"sayfa": str(erisim_gunlugu.AZAMI_SAYFA + 1)}, erisim_gunlugu.SAYFA_MESAJI),
        ({"sayfa": "9" * 40}, erisim_gunlugu.SAYFA_MESAJI),
    ],
)
def test_bicimsiz_suzgec_400_ve_turkce_ileti(sorgu: dict[str, str], ileti: str) -> None:
    yanit = _oku(**sorgu)
    assert yanit.status_code == 400, yanit.content
    assert yanit.json()["message"] == ileti


@pytest.mark.parametrize(
    ("sorgu", "alan", "ileti"),
    [
        ({"baslangic": "01.11.2026"}, "baslangic", erisim_gunlugu.TARIH_MESAJI),
        ({"bitis": "2026-13-01"}, "bitis", erisim_gunlugu.TARIH_MESAJI),
        # Takvimin uçları: ekran iletiyi o alanın altına yazar (F1b-2 (d3); eskiden alansızdı).
        ({"bitis": "9999-12-31"}, "bitis", erisim_gunlugu.TARIH_MESAJI),
        ({"baslangic": "0001-01-01"}, "baslangic", erisim_gunlugu.TARIH_MESAJI),
        (
            {"baslangic": "0001-01-01", "bitis": "2026-11-01"},
            "baslangic",
            erisim_gunlugu.TARIH_MESAJI,
        ),
        # Ters aralık bitiş alanınındır.
        (
            {"baslangic": "2026-11-02", "bitis": "2026-11-01"},
            "bitis",
            erisim_gunlugu.TARIH_SIRASI_MESAJI,
        ),
        ({"tur": "BILINMEYEN"}, "tur", erisim_gunlugu.TUR_MESAJI),
        ({"hesap": "muhasip"}, "hesap", erisim_gunlugu.HESAP_MESAJI),
        ({"sayfa": "0"}, "sayfa", erisim_gunlugu.SAYFA_MESAJI),
    ],
)
def test_bicimsiz_suzgecin_iletisi_alanina_baglidir(
    sorgu: dict[str, str], alan: str, ileti: str
) -> None:
    yanit = _oku(**sorgu)
    assert yanit.status_code == 400, yanit.content
    assert yanit.json()["code"] == "validation_error"
    assert yanit.json()["fields"] == {alan: [ileti]}


def test_tarih_suzgeci_hatalari_alan_adiyla_ve_yalniz_okuyarak() -> None:
    hatalar = erisim_gunlugu.tarih_suzgeci_hatalari
    assert hatalar(None, None) == {}
    assert hatalar(date(2026, 11, 1), date(2026, 11, 1)) == {}
    assert hatalar(date.min + timedelta(days=1), date.max - timedelta(days=1)) == {}
    assert hatalar(date.min, None) == {"baslangic": erisim_gunlugu.TARIH_MESAJI}
    assert hatalar(None, date.max) == {"bitis": erisim_gunlugu.TARIH_MESAJI}
    assert hatalar(date.min, date.max) == {
        "baslangic": erisim_gunlugu.TARIH_MESAJI,
        "bitis": erisim_gunlugu.TARIH_MESAJI,
    }
    assert hatalar(date(2026, 11, 2), date(2026, 11, 1)) == {
        "bitis": erisim_gunlugu.TARIH_SIRASI_MESAJI
    }


def test_servis_ters_aralik_ve_bicimsiz_sayfayi_reddeder() -> None:
    with pytest.raises(ValueError, match="Bitiş tarihi"):
        erisim_gunlugu.liste(baslangic=date(2026, 11, 2), bitis=date(2026, 11, 1))
    for sayfa in (0, -1, erisim_gunlugu.AZAMI_SAYFA + 1, True):
        with pytest.raises(ValueError, match="Sayfa"):
            erisim_gunlugu.liste(sayfa=sayfa)
    # Takvimin uçlarında sınır kurulamaz (`OverflowError` değil, Türkçe `ValueError`); bir gün
    # içeride kalan uçlar geçerlidir.
    with pytest.raises(ValueError, match="Tarih geçersiz"):
        erisim_gunlugu.liste(bitis=date.max)
    with pytest.raises(ValueError, match="Tarih geçersiz"):
        erisim_gunlugu.liste(baslangic=date.min)
    assert erisim_gunlugu.liste(bitis=date.max - timedelta(days=1))["toplam"] == 0
    assert erisim_gunlugu.liste(baslangic=date.min + timedelta(days=1))["toplam"] == 0


# ============================================================ okuma iz bırakmaz


def test_okuma_iz_birakmaz() -> None:
    """Plan F1b-2: "Okuma iz bırakmaz" — ne denetim izine ne erişim günlüğüne satır yazılır."""
    satir(yerel(2026, 10, 1))
    iz_once = AuditTrail.objects.count()
    gunluk_once = list(AccessLog.objects.order_by("id").values())

    for sorgu in ({}, {"tur": AccessKind.KISI_DOKUMU}, {"sayfa": "2"}):
        assert _oku(**sorgu).status_code == 200
    assert APIClient().head(YOL).status_code == 200

    assert AuditTrail.objects.count() == iz_once
    assert list(AccessLog.objects.order_by("id").values()) == gunluk_once


# ============================================================ türlerin görünen adları


def _sozluk() -> str:
    """`docs/sozluk.md` (yerelde depo kökü, konteynerde `/repo`)."""
    for kok in (Path(__file__).resolve().parents[4], Path("/repo")):
        yol = kok / "docs" / "sozluk.md"
        if yol.is_file():
            return yol.read_text(encoding="utf-8")
    pytest.fail("docs/sozluk.md bulunamadı.")


def _kvkk() -> str:
    for kok in (Path(__file__).resolve().parents[4], Path("/repo")):
        yol = kok / "docs" / "mevzuat" / "6698-kvkk.md"
        if yol.is_file():
            return yol.read_text(encoding="utf-8")
    pytest.fail("docs/mevzuat/6698-kvkk.md bulunamadı.")


def test_turlerin_gorunen_adlari_kapali_kumeyi_kapsar() -> None:
    assert set(erisim_gunlugu.TUR_ADLARI) == set(AccessKind.values)
    assert len(set(erisim_gunlugu.TUR_ADLARI.values())) == len(AccessKind.values)
    for ad in erisim_gunlugu.TUR_ADLARI.values():
        assert not re.search(r"[A-Z]{2,}_", ad), ad  # tür kodu kullanıcı metnine çıkmaz


def test_ozel_nitelikli_turler_kvkk_6_1_in_sozunu_kullanir() -> None:
    """Plan F1b-2: "Özel nitelikli türlerde KVKK md. 6/1'in sözü kullanılır." Söz korpustaki md.
    6/1'den doğrulanır: "… özel nitelikli kişisel veridir."."""
    kvkk = _kvkk()
    madde = kvkk[kvkk.index('<a id="madde-6">') : kvkk.index('<a id="madde-7">')]
    birinci_fikra = madde[madde.index("(1)") : madde.index("(2)")]
    assert "özel nitelikli kişisel veridir" in birinci_fikra
    for tur in (AccessKind.OZEL_NITELIKLI_EK, AccessKind.OZEL_NITELIKLI_ALAN):
        assert "özel nitelikli kişisel veri" in erisim_gunlugu.TUR_ADLARI[tur].lower(), tur


def test_erisim_gunlugu_metinleri_sozlukte_yazilidir() -> None:
    """Kullanıcıya görünen her metin sözlüğe girer (sözlük §1 "Erişim günlüğü (F1b)")."""
    sozluk = _sozluk()
    for ileti in (
        *erisim_gunlugu.TUR_ADLARI.values(),
        erisim_gunlugu.BILINMEYEN_TUR_ADI,
        erisim_gunlugu.TARIH_MESAJI,
        erisim_gunlugu.TARIH_SIRASI_MESAJI,
        erisim_gunlugu.TUR_MESAJI,
        erisim_gunlugu.HESAP_MESAJI,
        erisim_gunlugu.SAYFA_MESAJI,
    ):
        assert f'**"{ileti}"**' in sozluk, ileti


def test_yanit_json_anahtarlari_turkcedir() -> None:
    satir(yerel(2026, 10, 1))
    govde = json.loads(_oku().content)
    assert set(govde) == {
        "satirlar",
        "toplam",
        "sayfa",
        "sayfa_sayisi",
        "sayfa_boyutu",
        "turler",
        "hesaplar",
    }
