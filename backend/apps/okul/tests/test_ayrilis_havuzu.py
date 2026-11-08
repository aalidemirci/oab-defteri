"""Ayrılış havuzu — uçlar, toplu karar, olası aynı kişi (tasarım §5.1 `Personnel`, §13 D30).

Aile iskeletinin kullanıcı kararı: e-Okul aktarımı kimseyi ayırmaz ve silmez;
listede bulunmayan aktif kişi havuza girer, karar burada verilir:

- `GET leave-pool/` havuzdaki öğretmen ve diğer personeli TR sıralı listeler; havuza giriş
  tarihi ve hangi aktarımla; `?summary=true` yalnız sayı (Genel Bakış).
- `POST leave-pool/resolve/` toplu karar: "Ayrıldı olarak işaretle" (`is_active=False` +
  tarih, kancalar; KAYIT SİLİNMEZ) ve "Aktif kalsın" (yalnız havuzdan çıkar).
  Tek işlemdir: seçilenlerden biri havuzda değilse hiçbir karar uygulanmaz.
- Karar ucu kişi yazar: parola kurulmadan 409 (rol izni `rol_izinleri.KURALLAR`'da).
- Havuzdaki personel için "olası aynı kişi" adayları (eşleşme GEREKÇESİYLE —
  §13 D30) ve havuzdan birleştirme.
- Günlüğe ad yazılmaz.

Havuz yalnız personeli taşır: öğrenci sicili F1b 5. adımda söküldü (tasarım §5.1 ALMA); yanıtta
öğrenci alanı yoktur, eski `students` kararı yok sayılır.

Bütün adlar uydurmadır (KVKK).
"""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul import name_match, selectors
from apps.okul.models import (
    ImportRun,
    ImportStatus,
    Personnel,
)
from apps.okul.services import imports as import_service
from apps.okul.services import persons

pytestmark = pytest.mark.django_db

HAVUZ_URL = "/api/v1/leave-pool/"
KARAR_URL = "/api/v1/leave-pool/resolve/"
PERSONEL_BASLIK = "Adı\tSoyadı\tGörevi\tBranşı"
SENTETIK_AD = "HAVUZSENTETİK"


@pytest.fixture(autouse=True)
def bos_kayit_defterleri(monkeypatch: pytest.MonkeyPatch) -> None:
    for ad in (
        "_obligation_checks",
        "_membership_checks",
        "_leave_hooks",
        "_merge_hooks",
        "_deletion_blocks",
    ):
        monkeypatch.setattr(persons, ad, [])


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _personel(ad: str, soyad: str) -> Personnel:
    kisi: Personnel = Personnel.objects.create(first_name=ad, last_name=soyad)
    return kisi


def _havuza(*kayitlar: Personnel) -> None:
    for kayit in kayitlar:
        persons.add_to_leave_pool(kayit, run=None)


def _karar(client: APIClient, govde: dict[str, Any]) -> Any:
    return client.post(KARAR_URL, govde, format="json")


# ---------------------------------------------------------------------------
# Havuz listesi
# ---------------------------------------------------------------------------


def test_havuz_listesi_tr_sirali_giris_ve_aktarimla(client: APIClient) -> None:
    for ad in ("ZEHRA", "ÇAĞLA", "CEM"):
        _personel(ad, "ÖRNEK")
    import_service.commit_personnel_text(text="\n".join([PERSONEL_BASLIK, "ALİ\tYENİ\t\t"]))
    kosu = ImportRun.objects.get(status=ImportStatus.COMPLETED, source_type="PERSONEL")

    yanit = client.get(HAVUZ_URL)

    assert yanit.status_code == 200
    veri = yanit.json()
    assert set(veri) == {"personnel_count", "personnel"}
    assert veri["personnel_count"] == 3
    # Türk alfabesi: C < Ç.
    assert [p["full_name"] for p in veri["personnel"]] == [
        "CEM ÖRNEK",
        "ÇAĞLA ÖRNEK",
        "ZEHRA ÖRNEK",
    ]
    bugun = timezone.localdate().isoformat()
    ilk = veri["personnel"][0]
    assert ilk["leave_candidate_since"] == bugun
    assert ilk["run"] == {"id": kosu.pk, "file_name": "", "date": bugun}
    assert set(ilk) == {
        "id",
        "full_name",
        "member_kind",
        "leave_candidate_since",
        "run",
        "similar",
        # Çözülemeyen şifreli alanların adları (tasarım §13 D48); değer taşımaz.
        "bozuk_alanlar",
    }


def test_havuz_ozeti_yalniz_sayilari_doner(client: APIClient) -> None:
    kisi = _personel(SENTETIK_AD, "ÖRNEK")
    _havuza(kisi)
    _personel("AYŞE", "KAYA")  # havuzda değil

    yanit = client.get(HAVUZ_URL, {"summary": "true"})

    assert yanit.status_code == 200
    assert yanit.json() == {"personnel_count": 1}
    assert SENTETIK_AD not in yanit.content.decode()


def test_havuz_bosken_bos_listeler(client: APIClient) -> None:
    _personel("AYŞE", "KAYA")

    veri = client.get(HAVUZ_URL).json()

    assert veri == {"personnel_count": 0, "personnel": []}


# ---------------------------------------------------------------------------
# Toplu karar
# ---------------------------------------------------------------------------


def test_toplu_karar_ayrilanlar_ayrilir_kalanlar_havuzdan_cikar_kayit_silinmez(
    client: APIClient,
) -> None:
    giden, kalan = _personel("MEHMET", "DEMİR"), _personel("ZEHRA", "ÇELİK")
    _havuza(giden, kalan)

    yanit = _karar(client, {"personnel": {"leave": [giden.pk], "keep": [kalan.pk]}})

    assert yanit.status_code == 200, yanit.json()
    assert yanit.json() == {"personnel_left": 1, "personnel_kept": 1, "personnel_count": 0}
    bugun = timezone.localdate()
    for kayit in (giden, kalan):
        kayit.refresh_from_db()
        assert kayit.deleted_at is None
        assert kayit.leave_candidate_since is None
    assert (giden.is_active, giden.left_at) == (False, bugun)
    assert (kalan.is_active, kalan.left_at) == (True, None)
    assert Personnel.all_objects.count() == 2


def test_eski_ogrenci_karari_yok_sayilir(client: APIClient) -> None:
    """Öğrenci havuzu söküldü: gövdedeki `students` alanı karar sayılmaz."""
    kisi = _personel("MEHMET", "DEMİR")
    _havuza(kisi)

    bos = _karar(client, {"students": {"leave": [kisi.pk]}})
    assert bos.status_code == 400
    assert bos.json()["message"] == persons.POOL_EMPTY_MESSAGE
    kisi.refresh_from_db()
    assert (kisi.is_active, kisi.leave_candidate_since) == (True, timezone.localdate())


def test_karar_ayrilis_kancasini_yalniz_ayrilanlar_icin_cagirir(client: APIClient) -> None:
    gelen: list[tuple[str, int]] = []
    persons.register_leave_hook(lambda kisi: gelen.append((type(kisi).__name__, kisi.pk)))
    giden, kalan = _personel("MEHMET", "DEMİR"), _personel("ZEHRA", "ÇELİK")
    _havuza(giden, kalan)

    _karar(client, {"personnel": {"leave": [giden.pk], "keep": [kalan.pk]}})

    assert gelen == [("Personnel", giden.pk)]


def test_tek_kisilik_karar_ve_yinelenen_kimlik_tekillesir(client: APIClient) -> None:
    kisi = _personel("MEHMET", "DEMİR")
    _havuza(kisi)

    yanit = _karar(client, {"personnel": {"leave": [kisi.pk, kisi.pk]}})

    assert yanit.status_code == 200
    assert yanit.json()["personnel_left"] == 1


def test_ayni_kisi_iki_listede_reddedilir(client: APIClient) -> None:
    kisi = _personel("MEHMET", "DEMİR")
    _havuza(kisi)

    yanit = _karar(client, {"personnel": {"leave": [kisi.pk], "keep": [kisi.pk]}})

    assert yanit.status_code == 400
    assert yanit.json()["message"] == persons.POOL_CONFLICT_MESSAGE
    kisi.refresh_from_db()
    assert (kisi.is_active, kisi.leave_candidate_since) == (True, timezone.localdate())


def test_havuzda_olmayan_kisi_varsa_hicbir_karar_uygulanmaz(client: APIClient) -> None:
    """Tek işlem: geçerli seçim de geri sarılır; kullanıcı listeyi yeniler."""
    havuzdaki = _personel("AYŞE", "KAYA")
    havuzda_olmayan = _personel("ZEHRA", "ÇELİK")
    ayrilmis = _personel("MEHMET", "DEMİR")
    _havuza(havuzdaki)
    persons.leave_personnel(ayrilmis)

    for govde in (
        {"personnel": {"leave": [havuzdaki.pk, havuzda_olmayan.pk]}},
        {"personnel": {"leave": [havuzdaki.pk], "keep": [ayrilmis.pk]}},
        {"personnel": {"leave": [havuzdaki.pk, 99999]}},
    ):
        yanit = _karar(client, govde)
        assert yanit.status_code == 400, govde
        assert yanit.json()["message"] == persons.POOL_STALE_MESSAGE

    havuzdaki.refresh_from_db()
    assert (havuzdaki.is_active, havuzdaki.leave_candidate_since) == (
        True,
        timezone.localdate(),
    )


def test_bos_karar_ve_bozuk_govde_reddedilir(client: APIClient) -> None:
    bos = _karar(client, {})
    assert bos.status_code == 400
    assert bos.json()["message"] == persons.POOL_EMPTY_MESSAGE

    bozuk = _karar(client, {"personnel": {"leave": ["abc"]}})
    assert bozuk.status_code == 400
    assert bozuk.json()["code"] == "validation_error"


def test_havuzdaki_kisi_aktif_olmalidir_db_kisiti() -> None:
    """Son savunma: ayrılmış kişi havuzda bekleyemez (ayrılış yolu havuzu temizler)."""
    kisi = _personel("AYŞE", "KAYA")
    persons.leave_personnel(kisi)

    with pytest.raises(IntegrityError), transaction.atomic():
        Personnel.objects.filter(pk=kisi.pk).update(leave_candidate_since=timezone.localdate())


def test_ayrilmis_kisi_servisle_havuza_eklenemez() -> None:
    kisi = _personel("AYŞE", "KAYA")
    persons.leave_personnel(kisi)

    with pytest.raises(Exception, match="zaten ayrıldı"):
        persons.add_to_leave_pool(kisi, run=None)


def test_karar_gunlukte_ad_birakmaz(client: APIClient, caplog: pytest.LogCaptureFixture) -> None:
    giden = _personel(SENTETIK_AD, "ÖRNEK")
    kalan = _personel("AYŞE", "SENTETİKKALAN")
    _havuza(giden, kalan)

    with caplog.at_level(logging.DEBUG):
        _karar(client, {"personnel": {"leave": [giden.pk], "keep": [kalan.pk]}})

    assert "Ayrılış havuzu kararı: 1 personel ayrıldı, 1 personel aktif kaldı." in caplog.text
    for iz in (SENTETIK_AD, "SENTETİKKALAN"):
        assert iz not in caplog.text


# ---------------------------------------------------------------------------
# Parola kapısı
# ---------------------------------------------------------------------------


def test_parolasizken_karar_ucu_409_liste_acik(parolasiz: Path, client: APIClient) -> None:
    yanit = _karar(client, {"personnel": {"leave": [1]}})

    assert yanit.status_code == 409
    assert yanit.json()["code"] == "parola_gerekli"
    assert client.get(HAVUZ_URL).status_code == 200


# ---------------------------------------------------------------------------
# Olası aynı kişi ve havuzdan birleştirme
# ---------------------------------------------------------------------------


def test_havuzdaki_personel_icin_olasi_ayni_kisi_ve_havuzdan_birlestirme(
    client: APIClient,
) -> None:
    """Soyadı değişimi: listede 'AYŞE BEYAZ' var, kayıttaki 'AYŞE KARA' havuza düşer."""
    eski = _personel("AYŞE", "KARA")
    _personel("ALİ", "VELİ")
    import_service.commit_personnel_text(
        text="\n".join([PERSONEL_BASLIK, "ALİ\tVELİ\t\t", "AYŞE\tBEYAZ\tÖğretmen\t"])
    )
    # Ad şifreli: DB'de aranmaz, Python'da süzülür.
    yeni = next(p for p in Personnel.objects.all() if p.full_name == "AYŞE BEYAZ")

    veri = client.get(HAVUZ_URL).json()

    # Aday satırı NEDEN aday olduğunu ve ayırt edici bilgisini taşır (§13 D30).
    assert [(p["id"], p["similar"]) for p in veri["personnel"]] == [
        (
            eski.pk,
            [
                {
                    "id": yeni.pk,
                    "full_name": "AYŞE BEYAZ",
                    "member_kind": "OGRETMEN",
                    "created_on": timezone.localdate().isoformat(),
                    "reason": "ad_ayni_soyad_farkli",
                }
            ],
        )
    ]
    birlestir = client.post(
        f"/api/v1/personnel/{eski.pk}/merge/", {"into_id": yeni.pk}, format="json"
    )
    assert birlestir.status_code == 200
    assert not Personnel.all_objects.filter(pk=eski.pk).exists()
    assert client.get(HAVUZ_URL, {"summary": "true"}).json()["personnel_count"] == 0


def test_olasi_ayni_kisi_havuza_giristen_once_acilmis_kayitlarda_aranmaz() -> None:
    """Okulda aynı adı taşıyan eski öğretmen her havuz kişisine "benzer" görünmesin."""
    eski_ayse = _personel("AYŞE", "DEMİR")
    Personnel.objects.filter(pk=eski_ayse.pk).update(
        created_at=timezone.now() - timedelta(days=400)
    )
    havuzdaki = _personel("AYŞE", "KARA")
    yeni_ayse = _personel("AYŞE", "BEYAZ")
    _havuza(havuzdaki)

    adaylar = selectors.leave_pool_similar_personnel(selectors.leave_pool_personnel())

    assert [a.person.pk for a in adaylar[havuzdaki.pk]] == [yeni_ayse.pk]


def test_aday_gerekcesi_ucta_dondurulur(client: APIClient) -> None:
    """Her aday satırı neden aday olduğunu söyler: ad eşitliği mi, yazım farkı mı (§13 D30)."""
    havuzdaki = _personel("SELİN", "ÖZTÜRK")
    ad_ayni = _personel("SELİN", "BEYAZ")
    yazim = _personel("SELİM", "ÖZTÜRK")
    _havuza(havuzdaki)

    (kisi,) = client.get(HAVUZ_URL).json()["personnel"]

    assert {a["id"]: a["reason"] for a in kisi["similar"]} == {
        ad_ayni.pk: "ad_ayni_soyad_farkli",
        yazim.pk: "yazim_farki",
    }


def test_ayni_ad_soyad_adayi_ad_ayni_soyad_farkli_diye_sunulmaz() -> None:
    """Birebir aynı ad-soyad taşıyan aday kendi gerekçesiyle gelir (yanıltmasın)."""
    havuzdaki = _personel("DENİZ", "YILDIZ")
    adas = _personel("DENİZ", "YILDIZ")
    _havuza(havuzdaki)

    adaylar = selectors.leave_pool_similar_personnel(selectors.leave_pool_personnel())

    assert [(a.person.pk, a.reason) for a in adaylar[havuzdaki.pk]] == [
        (adas.pk, name_match.MatchReason.SAME_FULL_NAME)
    ]
