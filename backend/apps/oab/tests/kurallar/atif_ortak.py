"""Atıf kilidinin korpus denetimleri: D3 (çapa) ve D4 (fıkra, bent) (tasarım §6.3).

Yalnız testte koşar: korpus dağıtılmaz. Metin biçimleri `docs/mevzuat/` dosyalarından çıkarılmıştır:

- Numaralı fıkra `(n)` satır başındadır, ilki `MADDE N – (1)` satırında olabilir.
- Bent `a)` satır başındadır ve yalnız kendi fıkrasının penceresinde aranır (OKY 25/1-a ile 25/2-a).
- Alt bent `1)` bent satırının içinde akar (OAB Yön. md. 17).
- Paragraf sayımında `###` başlığı sayılmaz (EK-2 md. 7'nin sonu); bent satırları ve küçük harfle
  süren satır kendinden önceki paragrafa aittir (4857 md. 17 "feshedilmiş sayılır.").
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

_CAPA = re.compile(r'<a id="([^"]+)"></a>')
_FIKRA = re.compile(
    r"^(?:MADDE\s+\d+(?:/[A-Z])?\s*[–-]\s*)?\((\d+)\)", re.MULTILINE | re.IGNORECASE
)
_BENT = re.compile(r"^([a-zçğıöşü])\)", re.MULTILINE)
_ALT_BENT = re.compile(r"(?<![\w.(])(\d+)\)\s")
_SERH_ACILIS = "(Mülga"
_YD = "yürütmesi durdurulan"
_IPTAL = re.compile(r"iptal (?:bent|ibare)")
_YENIDEN = "(Yeniden Düzenleme:"


def korpus_kokleri(depo_dosyasi: Path) -> Path:
    """Depo kökündeki `docs/mevzuat` (yerelde depo kökü, konteynerde `/repo`)."""
    for kok in (depo_dosyasi.resolve().parents[5], Path("/repo")):
        aday = kok / "docs" / "mevzuat"
        if aday.is_dir():
            return aday
    raise FileNotFoundError("docs/mevzuat bulunamadı.")


def _frontmatter(metin: str) -> dict[str, str]:
    if not metin.startswith("---"):
        return {}
    alanlar: dict[str, str] = {}
    for satir in metin.split("---", 2)[1].splitlines():
        anahtar, ayrac, deger = satir.partition(":")
        if ayrac:
            alanlar[anahtar.strip()] = deger.strip().strip('"')
    return alanlar


def d3_capa_hatalari(madde: Mapping[str, Any], kural: Mapping[str, Any], kok: Path) -> list[str]:
    """Tek bir atfın D3 denetimi; boş liste geçti demektir."""
    dosya_adi, _, capa = str(madde["capa"]).partition("#")
    if ".." in dosya_adi or dosya_adi.startswith("/"):
        return [f"{dosya_adi}: korpus dışına çıkan yol"]
    if dosya_adi.startswith("bilgi/"):
        return [f"{dosya_adi}: bilgi/ altındaki metin kural dayanağı olamaz"]
    if Path(dosya_adi).name.startswith(".draft-"):
        return [f"{dosya_adi}: doğrulanmamış taslak dayanak olamaz"]
    yol = kok / dosya_adi
    if not yol.is_file():
        return [f"{dosya_adi}: korpusta yok"]
    metin = yol.read_text(encoding="utf-8")
    hatalar: list[str] = []
    alanlar = _frontmatter(metin)
    if "denetim rehberi" in alanlar.get("belge-turu", "").lower():
        hatalar.append(f"{dosya_adi}: denetim rehberi kural dayanağı olamaz")
    if capa not in _CAPA.findall(metin):
        hatalar.append(f"{dosya_adi}#{capa}: çapa yok")
    if alanlar.get("yururlukte") == "false" and kural["yururluk"]["bitis"] is None:
        hatalar.append(f"{dosya_adi}: yürürlükten kalkmış metin, yururluk.bitis boş olamaz")
    return hatalar


def madde_govdesi(metin: str, capa: str) -> str | None:
    """Çapadan bir sonraki çapaya kadar olan gövde (başlık satırları atılır); çapa yoksa `None`."""
    eslesmeler = list(_CAPA.finditer(metin))
    for sira, eslesme in enumerate(eslesmeler):
        if eslesme.group(1) != capa:
            continue
        son = eslesmeler[sira + 1].start() if sira + 1 < len(eslesmeler) else len(metin)
        satirlar = metin[eslesme.end() : son].splitlines()
        return "\n".join(s for s in satirlar if not s.lstrip().startswith("#")).strip()
    return None


def _pencere(metin: str, eslesmeler: list[re.Match[str]], ad: str) -> str | None:
    """Adı `ad` olan işaretten bir sonraki işarete kadarki metin, işaretle birlikte."""
    for sira, eslesme in enumerate(eslesmeler):
        if eslesme.group(1) == ad:
            son = eslesmeler[sira + 1].start() if sira + 1 < len(eslesmeler) else len(metin)
            return metin[eslesme.start() : son]
    return None


def paragraflar(govde: str) -> list[str]:
    """Paragraf bloklarını sayar; bent satırı ve küçük harfle süren blok öncekine eklenir."""
    sonuc: list[str] = []
    for blok in re.split(r"\n\s*\n", govde):
        temiz = blok.strip()
        if not temiz:
            continue
        devam = _BENT.match(temiz) is not None or temiz[0].islower()
        if devam and sonuc:
            sonuc[-1] += "\n" + temiz
        else:
            sonuc.append(temiz)
    return sonuc


def _isaretsiz(pencere: str, isaret: re.Pattern[str]) -> str:
    """Pencerenin başındaki işaret (`(10)`, `a)`, `1)`) atılmış metin."""
    return isaret.sub("", pencere, count=1).strip()


def _serh_hatalari(metin: str, etiket: str) -> list[str]:
    """Atıf yapılan birim mülga, yürütmesi durdurulmuş ya da düzeltilmemiş iptal mi?"""
    hatalar: list[str] = []
    if metin.startswith(_SERH_ACILIS):
        hatalar.append(f"{etiket}: mülga hükme atıf")
    if _YD in metin:
        hatalar.append(f"{etiket}: yürütmesi durdurulan hükme atıf")
    iptal = _IPTAL.search(metin)
    if iptal is not None and _YENIDEN not in metin[iptal.end() :]:
        hatalar.append(f"{etiket}: iptal edilmiş hükme atıf")
    return hatalar


def d4_fikra_hatalari(madde: Mapping[str, Any], kok: Path) -> list[str]:
    """Tek bir atfın D4 denetimi; boş liste geçti demektir."""
    dosya_adi, _, capa = str(madde["capa"]).partition("#")
    yol = kok / dosya_adi
    govde = madde_govdesi(yol.read_text(encoding="utf-8"), capa) if yol.is_file() else None
    if govde is None:
        return [f"{madde['capa']}: gövde bulunamadı"]
    etiket = str(madde["capa"])
    fikra = madde.get("fikra")
    if madde.get("fikra_bicimi", "numarali") == "paragraf":
        birimler = paragraflar(govde)
        if fikra is None:
            if len(birimler) > 1:
                return [f"{etiket}: çok paragraflı maddede fıkra boş olamaz"]
            return _serh_hatalari(govde, etiket)
        sira = int(str(fikra)) - 1
        if not 0 <= sira < len(birimler):
            return [f"{etiket}: {fikra}. paragraf yok"]
        pencere = birimler[sira]
        fikra_metni = pencere
    else:
        isaretler = list(_FIKRA.finditer(govde))
        if fikra is None:
            if len(isaretler) > 1:
                return [f"{etiket}: çok fıkralı maddede fıkra boş olamaz"]
            return _serh_hatalari(govde, etiket)
        bulunan = _pencere(govde, isaretler, str(fikra))
        if bulunan is None:
            return [f"{etiket}: ({fikra}) fıkrası yok"]
        pencere = bulunan
        fikra_metni = _isaretsiz(pencere, _FIKRA)
    if "bent" not in madde:
        return _serh_hatalari(fikra_metni, f"{etiket} ({fikra})")
    bent_pencere = _pencere(pencere, list(_BENT.finditer(pencere)), str(madde["bent"]))
    if bent_pencere is None:
        return [f"{etiket} ({fikra}): {madde['bent']}) bendi yok"]
    bent_metni = _isaretsiz(bent_pencere, _BENT)
    if "alt_bent" not in madde:
        return _serh_hatalari(bent_metni, f"{etiket} ({fikra})-{madde['bent']}")
    alt = _pencere(bent_pencere, list(_ALT_BENT.finditer(bent_pencere)), str(madde["alt_bent"]))
    if alt is None:
        return [f"{etiket} ({fikra})-{madde['bent']}: {madde['alt_bent']}) alt bendi yok"]
    return _serh_hatalari(_isaretsiz(alt, _ALT_BENT), f"{etiket} alt bent {madde['alt_bent']}")


def butun_maddeler(kural: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    yield kural["madde"]
    yield from kural.get("ek_madde", ())
