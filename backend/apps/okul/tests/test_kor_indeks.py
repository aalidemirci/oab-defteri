"""Kör indeks ve şifreli kipte ad selector'ları (plan §2.4; tasarım §5.3).

Kod kapısının iki maddesi burada kanıtlanır:

- **Kör indeks eşleşmesi:** aynı (normalleştirilmiş) değer aynı indekse iner; farklı veri
  anahtarıyla (DEK) üretilen indeks eşleşmez (başka kurulumun indeksi bu kurulumda kimseyi
  bulmaz). Parola değişimi indeksi bozmaz (anahtar DEK'ten türer, parola sarmalı değişir).
  Anahtar bellekte değilse indeks hesaplanmaz (fail-closed).

  Kör indeksin tek kullanıcısı öğrenci okul numarasıydı; öğrenci sicili F1b 5. adımda
  söküldü (tasarım §5.1 ALMA). Sınama bu yüzden şimdilik `shared.crypto.blind_index`
  düzeyindedir; veli listesinin ad indeksi (`ParentRoster.name_index`, tasarım §5.1) gelince
  model ve eşleşme sınamaları ona bağlanır (sonraki alt adım).
- **Şifreli kipte ad selector'ları:** ad araması ve kullanıcıya gösterilen
  bütün sıralamalar Python'dadır ve Türk alfabesine uyar (DB filtresi şifreli
  sütunda çalışmaz, BINARY sıra 'Ç/İ/Ş'yi 'Z'den sonraya atar).

Bütün adlar ve değerler uydurmadır (KVKK).
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.okul import selectors
from apps.okul.models import Personnel
from apps.okul.services import app_password
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_PAROLA
from shared import crypto

pytestmark = pytest.mark.django_db

BASKA_DEK = bytes(range(100, 132))
#: Uydurma, normalleştirilmiş bir değer (veli listesinde katlanmış ad olacak).
ORNEK = "ornek veli adi"


# ---------------------------------------------------------------------------
# Kör indeks (shared.crypto)
# ---------------------------------------------------------------------------


def test_ayni_deger_ayni_indekse_iner_ve_degeri_tasimaz() -> None:
    indeks = crypto.blind_index(ORNEK)

    assert crypto.blind_index(ORNEK) == indeks  # belirlenimci: tam eşleşme ve teklik DB'de
    assert re.fullmatch(r"[0-9a-f]{64}", indeks)
    assert "ornek" not in indeks


def test_farkli_deger_eslesmez_ve_normallestirme_cagiranindir() -> None:
    assert crypto.blind_index(ORNEK) != crypto.blind_index("ornek veli adı")
    # İndeks yazımı katlamaz: aynı kişiye inmek için çağıran önce normalleştirir.
    assert crypto.blind_index("0123") != crypto.blind_index("123")


def test_bos_deger_bos_indeks() -> None:
    """ "Veri yok" hâli DB'de de boş görünür (kısmi teklik kısıtları buna dayanır)."""
    assert crypto.blind_index("") == ""


def test_farkli_dek_ile_uretilen_indeks_eslesmez() -> None:
    """Başka bir kurulumun (farklı DEK) indeksi bu kurulumda kimseyi bulmaz."""
    bu_kurulum = crypto.blind_index(ORNEK)

    crypto.load_key(BASKA_DEK)
    try:
        assert crypto.blind_index(ORNEK) != bu_kurulum
    finally:
        crypto.load_key(TEST_DEK)

    assert crypto.blind_index(ORNEK) == bu_kurulum


def test_kilitliyken_kor_indeks_hesaplanamaz() -> None:
    """Fail-closed: anahtar yokken kör indeks de hesaplanamaz (§5.3)."""
    crypto.unload_key()
    try:
        with pytest.raises(crypto.KeyMissingError):
            crypto.blind_index(ORNEK)
    finally:
        crypto.load_key(TEST_DEK)


def test_parola_degisimi_indeksi_bozmaz(yonetici_hesabi: Any) -> None:
    """Anahtar DEK'ten türer; parola değişimi yalnız sarmalı yeniler (§4.4.4)."""
    once = crypto.blind_index(ORNEK)

    app_password.change_password(
        hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password="Yeni-Parola-99"
    )

    assert crypto.blind_index(ORNEK) == once


# ---------------------------------------------------------------------------
# Şifreli kipte ad selector'ları
# ---------------------------------------------------------------------------


def test_ad_aramasi_python_da_turkce_katlamali() -> None:
    isil = Personnel.objects.create(first_name="IŞIL", last_name="ÇAĞLAR")
    Personnel.objects.create(first_name="EMRE", last_name="KAYA")

    # DB filtresi şifreli sütunda hiçbir şey bulamaz — arama bu yüzden Python'dadır.
    assert not Personnel.objects.filter(first_name="IŞIL").exists()
    assert [p.pk for p in selectors.personnel_list(search="isil")] == [isil.pk]
    assert [p.pk for p in selectors.personnel_list(search="çağlar")] == [isil.pk]
    assert [p.pk for p in selectors.personnel_list(search="CAGLAR")] == [isil.pk]


def test_personel_ad_sirasi_turk_alfabesiyle() -> None:
    for ad in ("DENİZ", "ÇAĞLA", "CEM", "İLKAY", "IŞIK", "ZEHRA", "ŞULE", "SELİN"):
        Personnel.objects.create(first_name=ad, last_name="ÖRNEK")

    sira = [p.first_name for p in selectors.personnel_sorted()]

    assert sira == ["CEM", "ÇAĞLA", "DENİZ", "IŞIK", "İLKAY", "SELİN", "ŞULE", "ZEHRA"]


def test_api_personel_listesi_sirali_doner() -> None:
    """Uç da aynı Python sırasını kullanır (DB'nin BINARY sırası 'Ç'yi sona atardı)."""
    Personnel.objects.create(first_name="ÜÇÜNCÜ", last_name="ÖRNEK")
    Personnel.objects.create(first_name="ÇAĞLA", last_name="ÖRNEK")
    Personnel.objects.create(first_name="CEM", last_name="ÖRNEK")

    veri = APIClient().get("/api/v1/personnel/").json()
    satirlar = veri["results"] if isinstance(veri, dict) else veri

    assert [p["first_name"] for p in satirlar] == ["CEM", "ÇAĞLA", "ÜÇÜNCÜ"]


def test_api_personel_aramasi_yalniz_adda_ve_sirali() -> None:
    Personnel.objects.create(first_name="ÇAĞLA", last_name="ÖRNEK")
    Personnel.objects.create(first_name="CANAN", last_name="ÖRNEK")
    Personnel.objects.create(first_name="DENEME", last_name="KİŞİ")

    veri = APIClient().get("/api/v1/personnel/", {"search": "ornek"}).json()
    satirlar = veri["results"] if isinstance(veri, dict) else veri

    assert [p["first_name"] for p in satirlar] == ["CANAN", "ÇAĞLA"]
