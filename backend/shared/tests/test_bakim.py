"""Bakım kapısı testleri (tasarım §4.1, §4.2; §13 D3).

Kapı yalnız standart kütüphaneyi kullanır; testler Django'ya ve veritabanına
dokunmaz. Gün işiyle geri yüklemenin dışlaşması uçtan uca
`desktop/tests/test_gunluk.py` ve `apps/okul/tests/test_live_restore.py`'dedir.
"""

from __future__ import annotations

import threading

import pytest

from shared import bakim
from shared.bakim import BakimKapisi


def test_acik_kapida_is_baslar_ve_ucusta_sayilir() -> None:
    kapi = BakimKapisi()

    with kapi.is_() as izin:
        assert izin is True
        assert kapi.ucusta == 1

    assert kapi.ucusta == 0
    assert kapi.bakimda is False


def test_bakimdayken_yeni_is_baslamaz() -> None:
    kapi = BakimKapisi()
    assert kapi.bakima_al(bekleme_sn=0.1) is True

    with kapi.is_() as izin:
        assert izin is False
        assert kapi.ucusta == 0

    assert kapi.gir() is False


def test_bakim_ucustaki_isin_bitmesini_bekler() -> None:
    kapi = BakimKapisi()
    basladi = threading.Event()
    bitir = threading.Event()

    def is_() -> None:
        with kapi.is_():
            basladi.set()
            bitir.wait(5)

    isci = threading.Thread(target=is_)
    isci.start()
    assert basladi.wait(5)

    # Süre dolarsa `False` döner ama kapı kapalı kalır: yeni iş başlamaz.
    assert kapi.bakima_al(bekleme_sn=0.05) is False
    assert kapi.bakimda is True
    assert kapi.gir() is False

    bitir.set()
    assert kapi.bakima_al(bekleme_sn=5) is True
    isci.join(5)
    assert kapi.ucusta == 0


def test_bakimdan_cikinca_is_yeniden_baslar() -> None:
    kapi = BakimKapisi()
    kapi.bakima_al(bekleme_sn=0.1)

    kapi.bakimdan_cik()

    with kapi.is_() as izin:
        assert izin is True


def test_girisi_olmayan_cikis_reddedilir() -> None:
    with pytest.raises(RuntimeError, match="girişi olmayan"):
        BakimKapisi().cik()


def test_is_hata_verse_de_sayac_duser() -> None:
    kapi = BakimKapisi()

    with pytest.raises(ValueError), kapi.is_():
        raise ValueError("iş patladı")

    assert kapi.ucusta == 0


def test_surec_ici_tek_kapi() -> None:
    assert isinstance(bakim.KAPI, BakimKapisi)
