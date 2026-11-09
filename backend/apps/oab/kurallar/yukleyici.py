"""Dağıtılan kural paketlerini okur ve açılış denetimlerini koşar (tasarım §6.1-6.3; D1, D2, D5, D7).

Paketler salt okunurdur, programla gelir. `MANIFEST.json` her revizyon dosyasının ve şema dosyasının
**bayt** SHA-256'sını taşır (D7 "sürüm bildirimi"). Dönemin dondurulmuş kopyası ise kanonik JSON'un özetiyle tutulur
(`icerik_ozeti`, plan F1c kararları): `JSONField` gidiş-dönüşü baytı korumaz.

`yukle` hiçbir koşulda hata yükseltmez: sonuç `PaketDurumu`'dur. Herhangi bir revizyon denetimden geçemezse
hiçbir paket kullanılmaz (fail-closed): yeni bağlama ve yazma kapalı, dönem kopyasından okuma açıktır (`erisim`).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from apps.oab.kurallar import denetimler
from shared import kanonik

logger = logging.getLogger(__name__)

PAKETLER_DIZINI: Final = Path(__file__).resolve().parent / "paketler"
MANIFEST_ADI: Final = "MANIFEST.json"
SEMA_ADI: Final = "kural-paketi.schema.json"
_PAKET_DOSYASI: Final = re.compile(r"^(OAB-\d{4}\.\d{2})\.r(\d+)\.json$")


@dataclass(frozen=True)
class Paket:
    """Tek bir revizyon; `kayitlar` kimliği yürürlük aralıklarına çevirir."""

    kimlik: str
    rev: int
    icerik: Mapping[str, Any]
    kayitlar: Mapping[str, tuple[Mapping[str, Any], ...]] = field(repr=False)

    @classmethod
    def sozlukten(cls, icerik: Mapping[str, Any]) -> Paket:
        gruplar: dict[str, list[Mapping[str, Any]]] = {}
        for kural in icerik["kurallar"]:
            gruplar.setdefault(kural["id"], []).append(kural)
        return cls(
            kimlik=icerik["paket"],
            rev=icerik["rev"],
            icerik=icerik,
            kayitlar={kid: tuple(kayit) for kid, kayit in gruplar.items()},
        )


@dataclass(frozen=True)
class PaketDurumu:
    """Açılış denetimlerinin sonucu. `hatalar` doluysa `paketler` boştur."""

    paketler: tuple[Paket, ...] = ()
    hatalar: tuple[str, ...] = ()

    @property
    def yuklendi(self) -> bool:
        return bool(self.paketler) and not self.hatalar

    @property
    def en_yeni(self) -> Paket | None:
        return self.paketler[-1] if self.yuklendi else None


def icerik_ozeti(icerik: Mapping[str, Any]) -> str:
    """Dönem kopyasının özeti: kanonik JSON'un SHA-256'sı (`RulePackage.content_sha256`, D7)."""
    return hashlib.sha256(kanonik.kodla(icerik)).hexdigest()


def _yinelenen_anahtari_reddet(ciftler: list[tuple[str, Any]]) -> dict[str, Any]:
    sonuc: dict[str, Any] = {}
    for anahtar, deger in ciftler:
        if anahtar in sonuc:
            raise ValueError(f"Yinelenen anahtar: {anahtar}")
        sonuc[anahtar] = deger
    return sonuc


def _nan_reddet(ad: str) -> None:
    raise ValueError(f"JSON'da olmayan sayı: {ad}")


def json_coz(ham: bytes) -> Any:
    """Katı JSON: yinelenen anahtar ve `NaN` paketi bozuk sayar."""
    return json.loads(
        ham.decode("utf-8"),
        object_pairs_hook=_yinelenen_anahtari_reddet,
        parse_constant=_nan_reddet,
    )


def _manifest_oku(dizin: Path) -> tuple[dict[str, str], str]:
    """Revizyon dosyalarının özetleri ve şema dosyasının özeti."""
    manifest = json_coz((dizin / MANIFEST_ADI).read_bytes())
    if not isinstance(manifest, dict) or not isinstance(manifest.get("paketler"), list):
        raise ValueError("MANIFEST.json biçimi bozuk.")
    return {satir["dosya"]: satir["sha256"] for satir in manifest["paketler"]}, manifest[
        "sema_sha256"
    ]


def _ad_parcalari(ad: str) -> tuple[str, int]:
    """`OAB-2023.12.r1.json` → `("OAB-2023.12", 1)`; revizyonların sırası da budur."""
    eslesme = _PAKET_DOSYASI.match(ad)
    if eslesme is None:
        raise ValueError(f"Paket dosyası adı bozuk: {ad}")
    return eslesme.group(1), int(eslesme.group(2))


def _sirali_dosyalar(dizin: Path, manifest: Mapping[str, str]) -> list[str]:
    diskteki = {ad.name for ad in dizin.iterdir() if _PAKET_DOSYASI.match(ad.name)}
    if diskteki != manifest.keys():
        raise ValueError(f"MANIFEST.json dizinle tutmuyor: {sorted(diskteki ^ manifest.keys())}")
    return sorted(manifest, key=_ad_parcalari)


def _denetle(dizin: Path) -> tuple[list[Paket], list[str]]:
    manifest, sema_ozeti = _manifest_oku(dizin)
    dosyalar = _sirali_dosyalar(dizin, manifest)
    if not dosyalar:
        return [], ["Dağıtılmış kural paketi yok."]
    sema_ham = (dizin / SEMA_ADI).read_bytes()
    if hashlib.sha256(sema_ham).hexdigest() != sema_ozeti:
        return [], [f"{SEMA_ADI}: dosya özeti MANIFEST.json ile tutmuyor (D7)."]
    sema = json_coz(sema_ham)
    paketler: list[Paket] = []
    hatalar: list[str] = []
    onceki: Mapping[str, Any] | None = None
    for ad in dosyalar:
        ham = (dizin / ad).read_bytes()
        if hashlib.sha256(ham).hexdigest() != manifest[ad]:
            hatalar.append(f"{ad}: dosya özeti MANIFEST.json ile tutmuyor (D7).")
            continue
        icerik = json_coz(ham)
        yapi = denetimler.d1_sema(icerik, sema)
        if yapi:
            hatalar += [f"{ad} (D1) {satir}" for satir in yapi]
            continue
        if (icerik["paket"], icerik["rev"]) != _ad_parcalari(ad):
            hatalar.append(f"{ad}: dosya adı içerikle tutmuyor.")
        hatalar += [f"{ad} (D2) {satir}" for satir in denetimler.d2_kimlik(icerik, onceki)]
        hatalar += [f"{ad} (D5) {satir}" for satir in denetimler.d5_tutarlilik(icerik)]
        paketler.append(Paket.sozlukten(icerik))
        onceki = icerik
    return paketler, hatalar


def yukle(dizin: Path = PAKETLER_DIZINI) -> PaketDurumu:
    """Paketleri okur, D1-D2-D5-D7'yi koşar. Hata yükseltmez; sonuç `PaketDurumu`'dur.

    Geniş `except` bilinçlidir: bozuk dosya denetimlerin ortasında her türden hata çıkarabilir
    (şemaya uyan ama D5'in okuyamadığı değer, bozuk `pattern`) ve program yine açılmalıdır (D1).
    """
    try:
        paketler, hatalar = _denetle(dizin)
    except Exception as exc:
        return PaketDurumu(hatalar=(f"Kural paketi okunamadı ({type(exc).__name__}): {exc}",))
    if hatalar:
        return PaketDurumu(hatalar=tuple(hatalar))
    return PaketDurumu(paketler=tuple(paketler))


class _Onbellek:
    durum: PaketDurumu | None = None


def durum() -> PaketDurumu:
    """Süreç içinde bir kez yüklenen paket durumu."""
    return _Onbellek.durum if _Onbellek.durum is not None else ac()


def ac(dizin: Path = PAKETLER_DIZINI) -> PaketDurumu:
    """Açılış: paketleri yeniden yükler; hatayı günlüğe yazar (program yine açılır, okuma açık)."""
    _Onbellek.durum = yukle(dizin)
    for satir in _Onbellek.durum.hatalar:
        logger.error("Kural paketi denetimi: %s", satir)
    return _Onbellek.durum
