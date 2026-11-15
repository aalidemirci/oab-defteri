"""Genel kurul evrakı hattının deneme kurucuları (F2 8. adım; plan F2 §8: "hattın sınanması için en
az bir deneme kurucusu").

Belgelerin gerçek içerikleri 9. ve 10. adımlardadır; bu adımda hat (kayıt, dosya, kip, toplantı, veli
adlı çıktı, basım) deneme kurucularıyla sınanır. Kurucular yalnız testte `KURUCULAR` ve
`ADLI_KURUCULAR` sözlüklerine konur (`kuruculari_kur`). Adlar UYDURMADIR; veli adları aranacak
belirgin dizgilerdir.
"""

from __future__ import annotations

import pytest
from django.db import models

from apps.oab.models import GeneralAssembly
from apps.oab.services import genel_kurul_evraki as gke
from apps.okul.models import SchoolConfig
from shared import evrak

#: Uydurma veli adları (dosyada bulunur; kayıtta, izde, günlükte bulunmaz).
VELILER = (("Pelinsu UYDURMAKAYA", "5-A"), ("Şahinbey DENEMEOĞLU", "5-B"))
#: Deneme kişisiz belgesinin cümlesi.
DENEME_CUMLESI = "Deneme kurucusu: evrak hattı sınanıyor."


def _antet() -> evrak.Antet:
    okul = SchoolConfig.load()
    return evrak.birlik_anteti(okul_adi=okul.school_name, ilce=okul.district)


def kisisiz_kurucu(kod: str) -> gke.Kurucu:
    """Kişisiz deneme kurucusu: başlık, toplantı ve kip satırı, deneme cümlesi."""

    def kur(konu: models.Model, secim: gke.Secim) -> tuple[evrak.Belge, tuple[str, ...]]:
        bloklar: list[evrak.Blok] = [
            evrak.Baslik(gke.BELGE_ADLARI[kod]),
            evrak.Paragraf(DENEME_CUMLESI),
        ]
        if secim.toplanti:
            bloklar.append(evrak.Paragraf(f"Toplantı: {secim.toplanti}"))
        if secim.kip:
            bloklar.append(evrak.Paragraf(f"Kip: {secim.kip}"))
        return evrak.Belge(kod=kod, antet=_antet(), bloklar=tuple(bloklar)), ("Deneme uyarısı.",)

    return kur


def adli_kurucu(kod: str) -> gke.AdliKurucu:
    """Veli adlı deneme kurucusu: sınıf başına sayfa, veli adı ve sınıf; satır sayısı veli sayısı."""

    def kur(kurul: GeneralAssembly, toplanti: str) -> gke.AdliIcerik:
        bloklar: list[evrak.Blok] = [evrak.Baslik(gke.BELGE_ADLARI[kod])]
        for sira, (veli, sinif) in enumerate(VELILER):
            if sira:
                bloklar.append(evrak.SayfaSonu())
            bloklar.append(evrak.AltBaslik(f"Sınıf: {sinif}"))
            bloklar.append(
                evrak.Tablo(
                    basliklar=("Sıra", "Velinin adı ve soyadı", "Öğrencinin sınıfı", "İmza"),
                    satirlar=(("1", veli, sinif, ""),),
                )
            )
        bloklar.append(evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU))
        return gke.AdliIcerik(
            belge=evrak.Belge(kod=kod, antet=_antet(), bloklar=tuple(bloklar)),
            satir_sayisi=len(VELILER),
        )

    return kur


def kuruculari_kur(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deneme kurucularını bütün kodlara koyar (yalnız testin süresince)."""
    for kod in gke.KODLAR:
        monkeypatch.setitem(gke.KURUCULAR, kod, kisisiz_kurucu(kod))
    for kod in gke.ADLI_KODLAR:
        monkeypatch.setitem(gke.ADLI_KURUCULAR, kod, adli_kurucu(kod))
