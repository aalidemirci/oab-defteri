"""Genel kurul kuralları (`gk`, tasarım §10.3): yeter sayının hesabı ve anlık görüntüsü.

Yeter sayı 16 × 4 (mevcut ≥ 100) ya da 16 × 2 (mevcut < 100); taban kurul bileşiminden gelir, üyelik
kaydı sayılmaz; olağanüstü genel kurulda da aynıdır (tasarım §12.A S-1, S-2 düzeltmeleri). Değerler
`DEGER_TABLOSU` ile elle karşılaştırılmıştır.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from apps.oab.hatalar import YeterSayiDonduruldu
from apps.oab.kurallar import genel_kurul
from apps.oab.models import AssemblyKind, GeneralAssembly, OabTerm
from apps.oab.services import donemler
from apps.oab.services import genel_kurul as genel_kurul_servisi
from apps.okul.models import SchoolConfig, SchoolYear

GUN = date(2026, 10, 1)


def _donem() -> OabTerm:
    yil = SchoolYear.objects.create(
        name="2026-2027",
        start_date=date(2026, 9, 7),
        end_date=date(2027, 6, 25),
        is_active=True,
    )
    return donemler.create_term(name="2026-2027 birlik dönemi", school_year=yil, start_date=GUN)


def _okul_mevcudu(mevcut: int) -> None:
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK,
        defaults={"student_count": mevcut, "student_count_as_of": GUN},
    )


@pytest.mark.kural_davranis("genel_kurul.yeter_sayi_taban")
def test_taban_uyelik_kayitlarindan_bagimsiz_16() -> None:
    """Hesabın girdisinde üyelik yoktur: eksik kadroda da 64/32 (tasarım §12.A S-1 düzeltmesi)."""
    buyuk = genel_kurul.genel_kurul_yeter_sayisi(100, tarih=GUN)
    kucuk = genel_kurul.genel_kurul_yeter_sayisi(99, tarih=GUN)
    assert (buyuk.taban, buyuk.gerekli) == (16, 64)
    assert (kucuk.taban, kucuk.gerekli) == (16, 32)


@pytest.mark.kural_davranis("genel_kurul.yeter_sayi_carpan")
def test_yeter_sayi_mevcut_100_ve_ustu_64() -> None:
    for mevcut in (100, 101, 1200):
        hesap = genel_kurul.genel_kurul_yeter_sayisi(mevcut, tarih=GUN)
        assert (hesap.taban, hesap.carpan, hesap.gerekli) == (16, 4, 64)


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.yeter_sayi_carpan")
def test_olaganustu_gk_yeter_sayi_64() -> None:
    """Olağanüstü genel kurulda da aynı çarpan (md. 9/6; tasarım §12.A S-2 düzeltmesi)."""
    _okul_mevcudu(150)
    kurul = genel_kurul_servisi.genel_kurul_olustur(donem=_donem(), kind=AssemblyKind.OLAGANUSTU)
    donmus = genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert (donmus.quorum_base, donmus.quorum_multiplier, donmus.quorum_required) == (16, 4, 64)


@pytest.mark.kural_davranis("genel_kurul.kucuk_okul_carpan")
def test_yeter_sayi_mevcut_99_32() -> None:
    hesap = genel_kurul.genel_kurul_yeter_sayisi(99, tarih=GUN)
    assert (hesap.taban, hesap.carpan, hesap.gerekli) == (16, 2, 32)


@pytest.mark.kural_davranis("genel_kurul.kucuk_okul_esik")
def test_esik_99_ve_100() -> None:
    """Sınırın iki yanı: 99 → küçük okul, 100 → büyük okul."""
    assert genel_kurul.genel_kurul_yeter_sayisi(99, tarih=GUN).gerekli == 32
    assert genel_kurul.genel_kurul_yeter_sayisi(100, tarih=GUN).gerekli == 64


def test_eksi_mevcut_hatadir() -> None:
    with pytest.raises(ValueError, match="eksi"):
        genel_kurul.genel_kurul_yeter_sayisi(-1, tarih=GUN)


@pytest.mark.django_db
@pytest.mark.kural_davranis("genel_kurul.kucuk_okul_esik")
def test_mevcut_gk_kaydina_anlik_yazilir() -> None:
    """Okul kartı sonradan değişse de genel kurulun dondurulmuş hesabı değişmez (O7)."""
    _okul_mevcudu(120)
    kurul = genel_kurul_servisi.genel_kurul_olustur(
        donem=_donem(),
        kind=AssemblyKind.OLAGAN,
        first_meeting_at=datetime(2026, 10, 20, tzinfo=UTC),
    )
    donmus = genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert donmus.student_count_snapshot == 120
    assert donmus.quorum_required == 64

    _okul_mevcudu(40)
    assert GeneralAssembly.objects.get(pk=kurul.pk).student_count_snapshot == 120
    with pytest.raises(YeterSayiDonduruldu):
        genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)
    assert GeneralAssembly.objects.get(pk=kurul.pk).quorum_required == 64


@pytest.mark.django_db
def test_mevcut_girilmemisse_yeter_sayi_hesaplanmaz() -> None:
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK,
        defaults={"student_count": None, "student_count_as_of": None},
    )
    kurul = genel_kurul_servisi.genel_kurul_olustur(donem=_donem(), kind=AssemblyKind.OLAGAN)
    with pytest.raises(ValueError, match="öğrenci mevcudu"):
        genel_kurul_servisi.yeter_sayiyi_dondur(kurul, tarih=GUN)


@pytest.mark.kural_davranis("denetleme_kurulu.koltuklar")
def test_dk_ogretmen_koltugu_gk_oylamasina_girmez() -> None:
    """Denetleme Kurulunun öğretmen koltukları öğretmenler kurulunca seçilir (md. 14/1)."""
    koltuklar = genel_kurul.genel_kurul_oylamasindaki_koltuklar(tarih=GUN)
    assert koltuklar == {"YK": {"ASIL": 5, "YEDEK": 5}, "DK_VELI": {"ASIL": 1, "YEDEK": 1}}
