"""Uyum hattı (tasarım §5 O3, §6.1): uygun, eksik, sapma.

Kayıt yazan servis kuralı `uyum.denetle("<kimlik>", gözlenen, ...)` ile sorar; adı bilinçli olarak aynıdır,
D6'nın statik taraması kimliği böyle görür (paket erişimi `paket_denetle` diye içe alınır).

* **Uygun:** açık `EKSIK` ya da `SAPMA` satırı varsa kapanır (`resolved_at`).
* **Eksik:** kayıt gerekçesiz yazılır, `EKSIK` satırı açılır (gerekçe istemez, R5).
* **Uyarı:** gerekçesiz geçmez. Açık `EKSIK` varsa satır `SAPMA`'ya döner, yoksa yeni `SAPMA` açılır.
  Açık `SAPMA`'nın iletisi aynıysa yeniden sorulmaz; ileti değiştiyse yeni gerekçe istenir.
* **Sert:** kaydedilmez. İstisna `hesaplanan_deger`: programın hesapladığı değerden farklı gerçek değer
  (`fiili_kayit=True`) kaydedilir, fark aynı kural kimliğiyle uyarı + gerekçe olur (D1, KE-23).
* **Denetlenmedi:** olay tarihindeki metin korpusta yok; satır açılmaz, bilgi notu döner (MA-12).

Toplu gerekçe: aynı kural ve kök neden için tek `ComplianceJustification` birden çok satıra bağlanır;
`toplu_gerekce: false` olan kuralda kök neden yok sayılır, her kayıt kendi gerekçesini ister.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from django.db import models, transaction
from django.utils import timezone

from apps.oab.hatalar import GerekceGerekli, KuralSert
from apps.oab.kurallar import (
    VERI_YOK,
    BilinmeyenKural,
    YururlukteDegerYok,
    atifli_metin,
    kural_kaydi,
    yazma_kapisi,
)
from apps.oab.kurallar.erisim import DenetimSonucu, DonemBagi
from apps.oab.kurallar.erisim import denetle as paket_denetle
from apps.oab.models import (
    ComplianceItem,
    ComplianceJustification,
    ComplianceKind,
    OabTerm,
    RulePackage,
)
from apps.oab.services import donem_kilidi, iz, kural_bagi
from apps.okul import denetim_izi

_ACIK_TURLER = (ComplianceKind.SAPMA, ComplianceKind.EKSIK)


@dataclass(frozen=True)
class Gerekce:
    """Kullanıcının gerekçesi; `kok_neden` boşsa bu kayda özeldir."""

    metin: str = ""
    kok_neden: str = ""
    sablon: str = ""


@dataclass(frozen=True)
class UyumSonucu:
    """Paket denetiminin sonucu ve açılan ya da açık kalan uyum satırı."""

    sonuc: DenetimSonucu
    satir: ComplianceItem | None = field(default=None)


def _toplu_acik(
    kural_id: str, *, donem: DonemBagi, tarih: date | None, olaylar: Mapping[str, date] | None
) -> bool:
    try:
        return bool(
            kural_kaydi(kural_id, tarih=tarih, donem=donem, olaylar=olaylar)["toplu_gerekce"]
        )
    except YururlukteDegerYok:
        return True


def _kapanis_toplu_acik(satir: ComplianceItem, *, donem: OabTerm, tarih: date) -> bool:
    try:
        return _toplu_acik(satir.rule_id, donem=donem, tarih=tarih, olaylar=None)
    except BilinmeyenKural:
        if satir.rev is None:  # eksik satırı revizyonla yazılır; tür daraltması
            raise
        # Kural dönemin bağlı revizyonunda yok (geri alınmış geçiş): bayrak satırın revizyonundan okunur.
        kopya = RulePackage.objects.get(package=satir.rule_package, rev=satir.rev)
        return _toplu_acik(
            satir.rule_id, donem=kural_bagi.KopyaBagi(rule_package=kopya), tarih=tarih, olaylar=None
        )


def _gerekce_bagla(
    kural_id: str, gerekce: Gerekce | None, *, toplu_acik: bool, uyari: str
) -> ComplianceJustification:
    """Gerekçe satırı: toplu gerekçede var olan satıra bağlanır, yoksa yenisi yazılır."""
    metin = "" if gerekce is None else gerekce.metin.strip()
    kok = "" if gerekce is None or not toplu_acik else gerekce.kok_neden.strip()
    if kok:
        mevcut = ComplianceJustification.objects.filter(rule_id=kural_id, root_cause=kok).first()
        if mevcut is not None:
            return mevcut
    if not metin:
        raise GerekceGerekli(detail=f"Bu kayıt için gerekçe yazılmalıdır. {uyari}".strip())
    hesap = iz.hesap_zorunlu()
    satir = ComplianceJustification.objects.create(
        rule_id=kural_id,
        root_cause=kok,
        text=metin,
        template="" if gerekce is None else gerekce.sablon,
        justified_by_id=hesap,
        justified_at=timezone.now(),
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(satir, onceki=None)
    return satir


def _acik_satir(donem: OabTerm, konu: models.Model, kural_id: str) -> ComplianceItem | None:
    return ComplianceItem.objects.filter(
        term=donem,
        subject_type=denetim_izi.model_etiketi(type(konu)),
        subject_id=denetim_izi.kimlik_metni(type(konu), konu.pk),
        rule_id=kural_id,
        resolved_at__isnull=True,
        kind__in=_ACIK_TURLER,
    ).first()


def _satir_yaz(
    donem: OabTerm,
    konu: models.Model,
    kural_id: str,
    sonuc: DenetimSonucu,
    *,
    tur: ComplianceKind,
    gerekce: ComplianceJustification | None = None,
    label: str = "",
) -> ComplianceItem:
    hesap = iz.yazar_hesabi()
    satir = ComplianceItem.objects.create(
        term=donem,
        kind=tur,
        subject_type=denetim_izi.model_etiketi(type(konu)),
        subject_id=denetim_izi.kimlik_metni(type(konu), konu.pk),
        rule_id=kural_id,
        rule_package=sonuc["paket"],
        rev=sonuc["rev"],
        message=sonuc["mesaj"],
        justification_group=gerekce,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(satir, onceki=None, label=label, compliance_item=satir.pk)
    return satir


def _kapat(satir: ComplianceItem, *, label: str = "") -> None:
    onceki = denetim_izi.anlik(satir)
    satir.resolved_at = timezone.now()
    satir.updated_by_id = iz.yazar_hesabi()
    satir.save(update_fields=["resolved_at", "updated_at", "updated_by"])
    denetim_izi.degisiklik(satir, onceki=onceki, label=label, compliance_item=satir.pk)


def _sapmaya_cevir(satir: ComplianceItem, gerekce: ComplianceJustification, *, sonuc: Any) -> None:
    onceki = denetim_izi.anlik(satir)
    satir.kind = ComplianceKind.SAPMA
    satir.justification_group = gerekce
    if sonuc is not None:
        satir.message = sonuc["mesaj"]
        satir.rule_package = sonuc["paket"]
        satir.rev = sonuc["rev"]
    satir.updated_by_id = iz.yazar_hesabi()
    satir.save(
        update_fields=[
            "kind",
            "justification_group",
            "message",
            "rule_package",
            "rev",
            "updated_at",
            "updated_by",
        ]
    )
    denetim_izi.degisiklik(satir, onceki=onceki, compliance_item=satir.pk)


def _sert_gerekcesi(
    kural_id: str, *, donem: OabTerm, tarih: date | None, olaylar: Mapping[str, date] | None
) -> str | None:
    try:
        return kural_kaydi(kural_id, tarih=tarih, donem=donem, olaylar=olaylar).get(
            "sert_gerekcesi"
        )
    except YururlukteDegerYok:
        return None


@transaction.atomic
def denetle(
    kural_id: str,
    gozlenen: Any = VERI_YOK,
    *,
    donem: OabTerm,
    konu: models.Model,
    tarih: date | None = None,
    okul: Mapping[str, Any] | None = None,
    olaylar: Mapping[str, date] | None = None,
    gerekce: Gerekce | None = None,
    fiili_kayit: bool = False,
    hazirlik_yazimi: bool = False,
) -> UyumSonucu:
    """Kaydın kurala uyumunu denetler, sonuca göre uyum satırını yazar (modül başlığı)."""
    yazma_kapisi()
    donem = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(donem, hazirlik_yazimi=hazirlik_yazimi)
    sonuc = paket_denetle(kural_id, gozlenen, tarih=tarih, donem=donem, okul=okul, olaylar=olaylar)
    durum = sonuc["durum"]
    acik = _acik_satir(donem, konu, kural_id)
    if durum == "denetlenmedi":
        return UyumSonucu(sonuc)
    if durum == "uygun":
        if acik is not None:
            _kapat(acik)
        return UyumSonucu(sonuc)
    if durum == "eksik":
        if acik is not None:
            return UyumSonucu(sonuc, acik)
        return UyumSonucu(sonuc, _satir_yaz(donem, konu, kural_id, sonuc, tur=ComplianceKind.EKSIK))
    if durum == "sert":
        if not (
            fiili_kayit
            and _sert_gerekcesi(kural_id, donem=donem, tarih=tarih, olaylar=olaylar)
            == "hesaplanan_deger"
        ):
            raise KuralSert(detail=atifli_metin(sonuc))
        sonuc = DenetimSonucu(**{**sonuc, "durum": "uyari"})
    if acik is not None and acik.kind == ComplianceKind.SAPMA and acik.message == sonuc["mesaj"]:
        return UyumSonucu(sonuc, acik)  # aynı sapmanın gerekçesi alınmış, yeniden sorulmaz
    toplu = _toplu_acik(kural_id, donem=donem, tarih=tarih, olaylar=olaylar)
    bagli = _gerekce_bagla(kural_id, gerekce, toplu_acik=toplu, uyari=atifli_metin(sonuc))
    if acik is not None:
        _sapmaya_cevir(acik, bagli, sonuc=sonuc)
        return UyumSonucu(sonuc, acik)
    return UyumSonucu(
        sonuc, _satir_yaz(donem, konu, kural_id, sonuc, tur=ComplianceKind.SAPMA, gerekce=bagli)
    )


@transaction.atomic
def kapanis_gecisi(
    donem: OabTerm,
    *,
    gerekceler: Mapping[str, Gerekce],
    tarih: date,
    konu: models.Model | None = None,
) -> list[ComplianceItem]:
    """Kapatıcı geçişte hâlâ açık `EKSIK` satırları `SAPMA`'ya çevirir (O3).

    `konu` verilmezse dönemin bütün eksikleri (dönem kapanışı). `tarih` kapanış olayının günüdür
    (toplu gerekçe bayrağı o günkü kayıttan okunur). Gerekçesi eksik kural varsa hiçbir satır değişmez.
    `toplu_gerekce: false` olan kuralda birden çok satır çevrilecekse de değişmez: çağıran bu kuralları
    `konu` ile kayıt kayıt geçirir (F4'ün dönem kapanışı kayıt başına metin toplar).
    """
    yazma_kapisi()
    donem = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(donem)
    satirlar = ComplianceItem.objects.filter(
        term=donem, kind=ComplianceKind.EKSIK, resolved_at__isnull=True
    )
    if konu is not None:
        satirlar = satirlar.filter(
            subject_type=denetim_izi.model_etiketi(type(konu)),
            subject_id=denetim_izi.kimlik_metni(type(konu), konu.pk),
        )
    cevrilenler = list(satirlar.order_by("pk"))
    eksik_kurallar = sorted({s.rule_id for s in cevrilenler} - set(gerekceler))
    if eksik_kurallar:
        raise GerekceGerekli
    toplu_bayragi = {s.pk: _kapanis_toplu_acik(s, donem=donem, tarih=tarih) for s in cevrilenler}
    sayilar = Counter(s.rule_id for s in cevrilenler)
    if any(sayilar[s.rule_id] > 1 and not toplu_bayragi[s.pk] for s in cevrilenler):
        raise GerekceGerekli(
            detail="Bu kuralda her kayıt kendi gerekçesini ister; kayıtlar tek tek gerekçelendirilmelidir."
        )
    for satir in cevrilenler:
        bagli = _gerekce_bagla(
            satir.rule_id,
            gerekceler[satir.rule_id],
            toplu_acik=toplu_bayragi[satir.pk],
            uyari=satir.message,
        )
        _sapmaya_cevir(satir, bagli, sonuc=None)
    return cevrilenler


@transaction.atomic
def eksik_kapat(satir: ComplianceItem, *, beyaz_liste: bool = False) -> ComplianceItem:
    """Bilgi girilince `EKSIK` satırı kapanır; kapanmış dönemde yalnız işaretin kapattığı satır (O2)."""
    guncel = ComplianceItem.objects.select_related("term__rule_package").get(pk=satir.pk)
    if guncel.kind != ComplianceKind.EKSIK:
        raise ValueError("Yalnız eksik satırı bilgi girilince kapanır.")
    label = donem_kilidi.yazma_denetimi(guncel.term, beyaz_liste=beyaz_liste)
    if guncel.resolved_at is None:
        _kapat(guncel, label=label)
    return guncel
