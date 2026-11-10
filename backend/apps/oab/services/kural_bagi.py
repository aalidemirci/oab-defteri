"""Kural paketi kopyası, dönem bağı ve revizyon geçişi (tasarım §6.2).

Dönem açılışta programla gelen en yeni revizyona bağlanır; bağ bir `RulePackage` satırıdır. Yeni
revizyon geldiğinde açık dönem kendiliğinden geçmez: `revizyon_farki` eklenen, biten, değeri değişen ve
düzeltilen kuralları ve hesabı ya da uyarısı değişecek kayıtları verir, `revizyon_gecisi` onayla uygular.
Geçiş `KAPANDI` olmayan dönemde yapılır ve dönem kapanana kadar eski revizyona geri alınabilir.

Ekranı F1c'de yoktur (plan F1c kararları): kural sürümü Ayarlar'da salt okunur satırdır, fark ekranı
ilk `r2` ile gelir.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

from django.db import transaction
from django.utils import timezone

from apps.oab.hatalar import RevizyonOnayiGerekli
from apps.oab.kurallar import (
    KuralPaketiKullanilamaz,
    YururlukteDegerYok,
    genel_kurul,
    yazma_kapisi,
    yukleyici,
)
from apps.oab.kurallar.denetimler import degisim_turu
from apps.oab.kurallar.yukleyici import Paket, icerik_ozeti
from apps.oab.models import ComplianceItem, GeneralAssembly, OabTerm, RulePackage
from apps.oab.services import donem_kilidi, iz
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AuditAction

_YETER_SAYI_KURALLARI: Final = frozenset(
    {
        "genel_kurul.yeter_sayi_taban",
        "genel_kurul.yeter_sayi_carpan",
        "genel_kurul.kucuk_okul_carpan",
        "genel_kurul.kucuk_okul_esik",
    }
)


def kopya_dondur(paket: Paket) -> RulePackage:
    """Dağıtılan revizyonun dondurulmuş kopyası; satır varsa yeniden yazılmaz, içeriği denetlenir."""
    ozet = icerik_ozeti(paket.icerik)
    mevcut: RulePackage | None = RulePackage.objects.filter(
        package=paket.kimlik, rev=paket.rev
    ).first()
    if mevcut is not None:
        if mevcut.content_sha256 != ozet or not donem_kilidi.kopya_tutuyor(mevcut):
            raise ValueError("Aynı revizyonun içeriği önceki kopyayla tutmuyor.")
        return mevcut
    kopya = RulePackage.objects.create(
        package=paket.kimlik,
        rev=paket.rev,
        schema_version=paket.icerik["sema_surumu"],
        content=paket.icerik,
        content_sha256=ozet,
    )
    denetim_izi.degisiklik(kopya, onceki=None)
    return kopya


def en_yeni_kopya() -> RulePackage:
    """Programla gelen en yeni revizyonun kopyası (`yazma_kapisi` geçilmiş olmalı)."""
    paket = yukleyici.durum().en_yeni
    if paket is None:
        raise KuralPaketiKullanilamaz
    return kopya_dondur(paket)


@dataclass(frozen=True)
class EtkilenenKayit:
    """Geçişte hesabı ya da uyarısı değişecek kayıt (§6.2-5)."""

    model: str
    kayit_id: str
    kural_id: str


@dataclass(frozen=True)
class RevizyonFarki:
    """Dönemin bağlı revizyonu ile hedef revizyon arasındaki fark (§6.2-5)."""

    eski_paket: str
    eski_rev: int
    yeni_paket: str
    yeni_rev: int
    eklenen: tuple[str, ...]
    cikarilan: tuple[str, ...]
    biten: tuple[str, ...]
    deger_degisen: tuple[str, ...]
    duzeltilen: tuple[str, ...]
    kayitlar: tuple[EtkilenenKayit, ...]


@dataclass(frozen=True)
class KopyaBagi:
    """Hedef revizyonun içeriğini `kural(..., donem=...)` için dönem bağı gibi gösterir."""

    rule_package: Any


@dataclass(frozen=True)
class _Icerik:
    content: Mapping[str, Any]


def _kimliklere_gore(icerik: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    gruplar: dict[str, list[dict[str, Any]]] = {}
    for kayit in icerik["kurallar"]:
        gruplar.setdefault(kayit["id"], []).append(kayit)
    return gruplar


def _degisenler(once: Mapping[str, Any], sonra: Mapping[str, Any]) -> dict[str, list[str]]:
    eski = _kimliklere_gore(once)
    yeni = _kimliklere_gore(sonra)
    turler: dict[str, list[str]] = {
        "ekleme": sorted(yeni.keys() - eski.keys()),
        "cikarma": sorted(eski.keys() - yeni.keys()),
        "bitis": [],
        "deger_degisikligi": [],
        "duzeltme": [],
    }
    for kid in sorted(eski.keys() & yeni.keys()):
        tur = degisim_turu(eski[kid], yeni[kid])
        if tur is None:
            continue
        # Sınıflanamayan fark değer değişikliğidir: geri almada kayıt sayısı azalır, atlamalı
        # geçişte bitiş ile düzeltme üst üste biner (ikisi de onay ister, §6.2-5).
        turler["deger_degisikligi" if tur == "tanimsiz" else tur].append(kid)
    return turler


def _etkilenen_kayitlar(
    donem: OabTerm, hedef: Mapping[str, Any], degisen: set[str]
) -> tuple[EtkilenenKayit, ...]:
    kayitlar = [
        EtkilenenKayit("oab.ComplianceItem", str(satir.pk), satir.rule_id)
        for satir in ComplianceItem.objects.filter(term=donem, rule_id__in=degisen).order_by("pk")
    ]
    hedef_bag = KopyaBagi(rule_package=_Icerik(content=hedef))
    etkileyen = sorted(degisen & _YETER_SAYI_KURALLARI)
    if etkileyen:
        for gk in GeneralAssembly.objects.filter(
            term=donem, quorum_required__isnull=False
        ).order_by("pk"):
            if gk.student_count_snapshot is None:  # veritabanı kısıtı gereği olmaz; tür daraltması
                continue
            # Hesabı yapılamayan kurul atlanmaz, onaya düşmek için listelenir (§6.2-5).
            if gk.first_meeting_at is None:
                kayitlar.append(EtkilenenKayit("oab.GeneralAssembly", str(gk.pk), etkileyen[0]))
                continue
            try:
                yeni = genel_kurul.genel_kurul_yeter_sayisi(
                    gk.student_count_snapshot,
                    tarih=timezone.localtime(gk.first_meeting_at).date(),
                    donem=hedef_bag,
                )
            except YururlukteDegerYok:
                kayitlar.append(EtkilenenKayit("oab.GeneralAssembly", str(gk.pk), etkileyen[0]))
                continue
            if yeni.gerekli != gk.quorum_required:
                kayitlar.append(EtkilenenKayit("oab.GeneralAssembly", str(gk.pk), etkileyen[0]))
    return tuple(kayitlar)


def _fark(donem: OabTerm, hedef: Mapping[str, Any]) -> RevizyonFarki:
    baglanan = donem.rule_package
    turler = _degisenler(baglanan.content, hedef)
    degisen = {*turler["deger_degisikligi"], *turler["duzeltme"], *turler["cikarma"]}
    return RevizyonFarki(
        eski_paket=str(baglanan.package),
        eski_rev=int(baglanan.rev),
        yeni_paket=str(hedef["paket"]),
        yeni_rev=int(hedef["rev"]),
        eklenen=tuple(turler["ekleme"]),
        cikarilan=tuple(turler["cikarma"]),
        biten=tuple(turler["bitis"]),
        deger_degisen=tuple(turler["deger_degisikligi"]),
        duzeltilen=tuple(turler["duzeltme"]),
        kayitlar=_etkilenen_kayitlar(donem, hedef, degisen),
    )


def _hedef_icerik(
    paket: str, rev: int
) -> tuple[Mapping[str, Any], RulePackage | None, Paket | None]:
    """Hedef revizyon: dağıtılan dosya ya da önceden dondurulmuş kopya (geri alma)."""
    kopya = RulePackage.objects.filter(package=paket, rev=rev).first()
    dagitilan = next(
        (p for p in yukleyici.durum().paketler if (p.kimlik, p.rev) == (paket, rev)),
        None,
    )
    if kopya is not None:
        if not donem_kilidi.kopya_tutuyor(kopya):
            raise ValueError("İstenen kural sürümünün kopyası bozuk; geçiş yapılmadı.")
        return kopya.content, kopya, dagitilan
    if dagitilan is None:
        raise ValueError("İstenen kural sürümü bu programda yok.")
    return dagitilan.icerik, None, dagitilan


def revizyon_farki(donem: OabTerm, *, paket: str, rev: int) -> RevizyonFarki:
    """Geçişin farkı; kayıt yazmaz."""
    guncel = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    return _fark(guncel, _hedef_icerik(paket, rev)[0])


@transaction.atomic
def revizyon_gecisi(donem: OabTerm, *, paket: str, rev: int, onay: bool = False) -> RevizyonFarki:
    """Dönemi hedef revizyona geçirir (§6.2-5, 6). Kapanmış dönemde sert engeldir.

    Hesabı ya da uyarısı değişecek kayıt varsa `onay` ister. Denetim izine dönem satırının
    `GUNCELLE` izi (`rule_package`) ve paket-revizyonun `[eski, yeni]` çiftini taşıyan olay yazılır.
    """
    yazma_kapisi()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.KURAL_SURUMU_SECIMI)
    guncel = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(guncel)
    icerik, kopya, dagitilan = _hedef_icerik(paket, rev)
    if (str(guncel.rule_package.package), int(guncel.rule_package.rev)) == (paket, rev):
        raise ValueError("Dönem zaten bu kural sürümünde.")
    fark = _fark(guncel, icerik)
    if fark.kayitlar and not onay:
        raise RevizyonOnayiGerekli
    if kopya is None:
        assert dagitilan is not None  # `_hedef_icerik` ikisinden birini verir
        kopya = kopya_dondur(dagitilan)
    onceki = denetim_izi.anlik(guncel)
    guncel.rule_package = kopya
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=["rule_package", "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel, onceki=onceki)
    denetim_izi.olay(
        AuditAction.GUNCELLE,
        model=denetim_izi.KURAL_REVIZYON_GECISI,
        object_id=str(guncel.pk),
        changed_fields=["rule_package"],
        values={
            "paket": [fark.eski_paket, fark.yeni_paket],
            "rev": [fark.eski_rev, fark.yeni_rev],
        },
        term=guncel.pk,
    )
    return fark
