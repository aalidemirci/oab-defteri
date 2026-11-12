"""Kantin kuralları (`kn`, tasarım §6.4.8). F1c'de paketten yalnız md. 23/3 bilgisi vardır."""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.oab.kurallar import atifli_metin, bilgi_notu
from apps.oab.kurallar import yukleyici as yk
from apps.okul.models import CanteenMode

KURAL = "kantin.isletmede_vergi_uyarisi"
#: Sözlükteki metin (docs/sozluk.md, Okul Bilgileri); paketten aynen gelmeli.
BEKLENEN_METIN = (
    "Kantin ve benzeri yerler birlikçe işletilir ve vergi mükellefiyeti doğarsa birlik hakkında "
    "213 sayılı Vergi Usul Kanunu hükümleri uygulanır (md. 23/3)."
)


@pytest.mark.kural_davranis(KURAL)
def test_birlikce_isletme_secilince_vuk_uyarisi() -> None:
    """md. 23/3: yalnız birlikçe işletmede görünür, başka biçimde bilgi üretmez."""
    sonuc = bilgi_notu(KURAL, okul={"okul.kantin": CanteenMode.BIRLIKCE_ISLETILIYOR.value})
    assert sonuc is not None
    assert sonuc["durum"] == "uyari" and sonuc["atif"] == "md. 23/3"
    assert atifli_metin(sonuc) == BEKLENEN_METIN
    for mod in (CanteenMode.KIRAYA_VERILIYOR, CanteenMode.KANTIN_YOK):
        assert bilgi_notu(KURAL, okul={"okul.kantin": mod.value}) is None
    # Okul kartında seçim henüz yapılmamışsa bilgi çıkmaz.
    assert bilgi_notu(KURAL, okul={"okul.kantin": ""}) is None


@pytest.mark.django_db
def test_okul_karti_bilgisi_pakettendir() -> None:
    """Ön yüz metni ve koşulu uçtan alır; metinde yazılı bir kopyası yoktur."""
    yanit = APIClient().get("/api/v1/oab/okul-karti-bilgileri/")
    assert yanit.status_code == 200
    assert yanit.json() == {
        "kantin_isletme_bilgisi": {
            "modlar": ["BIRLIKCE_ISLETILIYOR"],
            "metin": BEKLENEN_METIN,
            "paket": "OAB-2023.12",
            "rev": 1,
        }
    }


@pytest.mark.django_db
def test_paket_yuklenemezse_okul_karti_bilgisi_bos_doner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """Okuma açık kalır: uç hata vermez, yalnız bilgi çıkmaz (tasarım §6.3 D1)."""
    monkeypatch.setattr(yk._Onbellek, "durum", yk.yukle(tmp_path))
    yanit = APIClient().get("/api/v1/oab/okul-karti-bilgileri/")
    assert yanit.status_code == 200
    assert yanit.json() == {"kantin_isletme_bilgisi": None}
