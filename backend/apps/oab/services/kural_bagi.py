"""Kural paketi kopyası, dönem bağı ve revizyon geçişi (tasarım §6.2).

Dönem açılışta programla gelen en yeni revizyona bağlanır; bağ bir `RulePackage` satırıdır. Yeni
revizyon geldiğinde açık dönem kendiliğinden geçmez: `revizyon_farki` eklenen, biten, değeri değişen ve
düzeltilen kuralları ve hesabı ya da uyarısı değişecek kayıtları verir, `revizyon_gecisi` onayla uygular.
Geçiş `KAPANDI` olmayan dönemde yapılır ve dönem kapanana kadar geri alınabilir: geri alma hedefi
dönemin önceki bağlarıdır (geçiş olaylarının eski sürümleri); dönem açılış bağından eskiye, hiç
bağlanmadığı revizyona indirilmez (§6.2-4, 5; `hedefler`).

Ekranı F1c'de yoktur (plan F1c kararları): kural sürümü Ayarlar'da salt okunur satırdır, fark ekranı
ilk `r2` ile gelir. F2'nin 2. adımında servis uca bağlandı (`oab-term-rule-revision`; okuma ve yazma
yalnız program yöneticisinin, `Eylem.KURAL_SURUMU_SECIMI`, Ayarlar satırı); ekranı F2'nin 11. adımındadır.

AÇILIŞ BAĞI (plan F2 §7 U2; tasarım §6.2-4 "açılışta"): ilk dönem de, genel kurulun planlanmasıyla açılan
`HAZIRLIK` dönemi de açılırken programla gelen en yeni revizyona bağlanır (`acilis_bagi`). Bağ `ACIK`'a
geçişte kendiliğinden değişmez; açık dönemden daha yeni revizyon programla gelmişse Genel Bakış'ta
program yöneticisine öneri çıkar (`guncelleme_onerisi`; pano kalemi `KURAL_SURUMU`), geçişi yönetici fark
ekranında onaylar (§6.2-5). Genel kurul kuralları kapanacak dönemin kopyasından okunduğu için (U1)
`r1`'e bağlı açık dönemin `r2`'ye geçişi genel kurul planlamasının ön koşuludur; o denetim F2'nin 4.
adımındadır.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

from django.db import transaction
from django.utils import timezone

from apps.oab.hatalar import DonemKapali, DonemSaltOkur, DonemYazilamaz, RevizyonOnayiGerekli
from apps.oab.kurallar import (
    KuralPaketiKullanilamaz,
    YururlukteDegerYok,
    genel_kurul,
    yazma_kapisi,
    yukleyici,
)
from apps.oab.kurallar.denetimler import degisim_turu
from apps.oab.kurallar.erisim import atif_metni
from apps.oab.kurallar.yukleyici import Paket, icerik_ozeti
from apps.oab.models import ComplianceItem, GeneralAssembly, OabTerm, RulePackage, TermStatus
from apps.oab.services import donem_kilidi, iz
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AuditAction, AuditTrail

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


def acilis_bagi() -> RulePackage:
    """Açılan birlik döneminin bağı (modül başlığı "Açılış bağı"; U2, §6.2-4).

    İlk dönem (`donemler.create_term`) ve genel kurulun planlanmasıyla açılan `HAZIRLIK` dönemi (F2'nin
    4. adımı) bu işlevle bağlanır: programla gelen en yeni revizyon. Dönemin durumu `ACIK`'a geçerken
    bağ yeniden kurulmaz; daha yeni revizyon yönetici onayıyla geçilir (`revizyon_gecisi`).
    """
    return en_yeni_kopya()


def _surum(paket: str, rev: int) -> dict[str, Any]:
    return {"paket": paket, "rev": rev}


def _bag(donem: OabTerm) -> tuple[str, int]:
    return str(donem.rule_package.package), int(donem.rule_package.rev)


def en_yeni_surum() -> dict[str, Any] | None:
    """Programla gelen en yeni revizyon (`{paket, rev}`); paket yüklenemediyse (D1) `None`."""
    en_yeni = yukleyici.durum().en_yeni
    return None if en_yeni is None else _surum(en_yeni.kimlik, en_yeni.rev)


def gecilebilir(donem: OabTerm) -> bool:
    """Dönem revizyon geçişine açık mı? Geçişin kapılarıyla aynı ölçü: paket yüklenmiş (D1,
    `yazma_kapisi`) ve dönem kilidi açık (kopya tutuyor; kapanmış, iptal ya da hazırlıkta değil). Fark
    ekranının onay düğmesi buna bakar; geçiş (`revizyon_gecisi`) aynı iki denetimi yeniden yapar."""
    try:
        yazma_kapisi()
        donem_kilidi.yazma_denetimi(donem)
    except (KuralPaketiKullanilamaz, DonemKapali, DonemSaltOkur, DonemYazilamaz):
        return False
    return True


def guncelleme_onerisi() -> dict[str, Any] | None:
    """Açık dönemden daha yeni revizyon programla geldi mi? (U2; tasarım §6.2-5, §7.10 yol haritası)

    Kişisizdir ve yazmaz: `{donem, bagli: {paket, rev}, en_yeni: {paket, rev}}` ya da `None`. Öneri yalnız
    `ACIK` dönem içindir (hazırlık dönemi açılışta en yeniye bağlanır, kapanmış dönem geçemez). Paket
    yüklenemediyse (D1) ya da dönemin kopyası tutmuyorsa (D7: dönem salt okurdur, geçiş de yazılamaz)
    öneri çıkmaz. Sıra yükleyicinin sırasıdır, (paket kimliği, revizyon): dönem en yeniden eskiye
    geçirilmeyi önermez (ör. daha yeni programın yedeği geri yüklendiyse).
    """
    en_yeni = yukleyici.durum().en_yeni
    if en_yeni is None:
        return None
    donem: OabTerm | None = (
        OabTerm.objects.select_related("rule_package").filter(status=TermStatus.ACIK).first()
    )
    if donem is None or not donem_kilidi.kural_kopyasi_tutuyor(donem):
        return None
    bagli = _bag(donem)
    if bagli >= (en_yeni.kimlik, en_yeni.rev):
        return None
    return {
        "donem": donem.pk,
        "bagli": _surum(*bagli),
        "en_yeni": _surum(en_yeni.kimlik, en_yeni.rev),
    }


def onceki_baglar(donem: OabTerm) -> set[tuple[str, int]]:
    """Dönemin bugünkü bağından önceki bağları: revizyon geçişi olaylarının (`kural.revizyon_gecisi`)
    eski sürümleri. İlk olayın eski sürümü açılış bağıdır; geçiş yapılmamış dönemin önceki bağı yoktur."""
    baglar: set[tuple[str, int]] = set()
    for degerler in AuditTrail.objects.filter(
        model=denetim_izi.KURAL_REVIZYON_GECISI, object_id=str(donem.pk)
    ).values_list("values", flat=True):
        baglar.add((str(degerler["paket"][0]), int(degerler["rev"][0])))
    return baglar


def _aday_surumler(donem: OabTerm) -> set[tuple[str, int]]:
    """Dönemin geçebileceği sürümler, kopyanın bütünlüğüne bakmadan (§6.2-4, 5).

    İleri: programla gelen ve dönemin bağından daha yeni revizyonlar (yükleyicinin sırası, paket kimliği
    ve revizyon). Geri alma: dönemin önceki bağları (`onceki_baglar`); dönem açılış bağından eskiye, hiç
    bağlanmadığı revizyona indirilmez. Dönemin bugünkü bağı aday değildir.
    """
    bag = _bag(donem)
    ileri = {(p.kimlik, p.rev) for p in yukleyici.durum().paketler if (p.kimlik, p.rev) > bag}
    return (ileri | onceki_baglar(donem)) - {bag}


def _hedef_okunur(paket: str, rev: int) -> bool:
    """Hedefin içeriği `_hedef_icerik`in seçim sırasıyla okunabiliyor mu (kopya varsa tutmalı)?"""
    try:
        _hedef_icerik(paket, rev)
    except ValueError:
        return False
    return True


def hedefler(donem: OabTerm) -> list[dict[str, Any]]:
    """Dönemin geçebileceği revizyonlar (`_aday_surumler`): programla gelen daha yeni revizyonlar ve
    dönemin önceki bağları (geri alma, §6.2-5); kopyası bozuk olan hedef olmaz (D7). Yükleyicinin
    sırasıyla (paket kimliği, revizyon)."""
    return [
        _surum(paket, rev)
        for paket, rev in sorted(_aday_surumler(donem))
        if _hedef_okunur(paket, rev)
    ]


def _hedef_denetimi(donem: OabTerm, paket: str, rev: int) -> None:
    """Fark ve geçiş yalnız dönemin aday sürümlerine yapılır (`_aday_surumler`); bugünkü bağ ayrıca
    denetlenir (fark boştur, geçişte "zaten bu sürümde")."""
    if (paket, rev) != _bag(donem) and (paket, rev) not in _aday_surumler(donem):
        raise ValueError(
            "Dönem bu kural sürümüne geçemez: yalnız programla gelen daha yeni sürüme ya da "
            "dönemin önceki bir sürümüne geçilir."
        )


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
            # Hesabı yapılamayan kurul atlanmaz, onaya düşmek için listelenir (§6.2-5). Gün birinci
            # toplantınındır, genel kurul ikinci toplantıda yapılsa da (plan F2 §7 U6, U7: yeter
            # sayının dondurulduğu kural günü); `genel_kurul_gunu`'ne geçmez.
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
    icerik = _hedef_icerik(paket, rev)[0]
    _hedef_denetimi(guncel, paket, rev)
    return _fark(guncel, icerik)


def _kural_satiri(kid: str, icerik: Mapping[str, Any]) -> dict[str, Any]:
    """Fark ekranının kural satırı: kimlik, açıklama ve atıf (kuralın son yürürlük kaydından). Kimlik
    ekranda gösterilmez (sözlük §2); ekran açıklamayı ve atfı yazar."""
    kayit = _kimliklere_gore(icerik)[kid][-1]
    return {"id": kid, "aciklama": str(kayit["aciklama"]), "atif": atif_metni(kayit)}


def fark_sozlugu(
    fark: RevizyonFarki, *, once: Mapping[str, Any], sonra: Mapping[str, Any]
) -> dict[str, Any]:
    """Farkın uç yanıtı (kişisiz): sürümler, kural satırları ve etkilenen kayıtlar (model, kimlik,
    kural). Çıkarılan kural eski revizyondan, ötekiler hedeften okunur; `onay_gerekli` etkilenen kayıt
    varsa doğrudur (§6.2-3a, 5)."""

    def satirlar(kimlikler: tuple[str, ...], icerik: Mapping[str, Any]) -> list[dict[str, Any]]:
        return [_kural_satiri(kid, icerik) for kid in kimlikler]

    return {
        "eski": _surum(fark.eski_paket, fark.eski_rev),
        "yeni": _surum(fark.yeni_paket, fark.yeni_rev),
        "eklenen": satirlar(fark.eklenen, sonra),
        "cikarilan": satirlar(fark.cikarilan, once),
        "biten": satirlar(fark.biten, sonra),
        "deger_degisen": satirlar(fark.deger_degisen, sonra),
        "duzeltilen": satirlar(fark.duzeltilen, sonra),
        "kayitlar": [
            {"model": k.model, "kayit_id": k.kayit_id, "kural_id": k.kural_id}
            for k in fark.kayitlar
        ],
        "onay_gerekli": bool(fark.kayitlar),
    }


def fark_gorunumu(donem: OabTerm, *, paket: str, rev: int) -> dict[str, Any]:
    """Fark ekranının okuması (`revizyon_farki` + kural satırları); kayıt yazmaz."""
    guncel = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    hedef = _hedef_icerik(paket, rev)[0]
    _hedef_denetimi(guncel, paket, rev)
    return fark_sozlugu(_fark(guncel, hedef), once=guncel.rule_package.content, sonra=hedef)


@transaction.atomic
def revizyon_gecisi(donem: OabTerm, *, paket: str, rev: int, onay: bool = False) -> RevizyonFarki:
    """Dönemi hedef revizyona geçirir (§6.2-5, 6). Kapanmış dönemde sert engeldir.

    Hedef dönemin aday sürümlerinden olmalıdır (`_aday_surumler`; değilse 400). Hesabı ya da uyarısı
    değişecek kayıt varsa `onay` ister. Denetim izine dönem satırının
    `GUNCELLE` izi (`rule_package`) ve paket-revizyonun `[eski, yeni]` çiftini taşıyan olay yazılır.
    """
    yazma_kapisi()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.KURAL_SURUMU_SECIMI)
    guncel = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(guncel)
    icerik, kopya, dagitilan = _hedef_icerik(paket, rev)
    if (str(guncel.rule_package.package), int(guncel.rule_package.rev)) == (paket, rev):
        raise ValueError("Dönem zaten bu kural sürümünde.")
    _hedef_denetimi(guncel, paket, rev)
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
