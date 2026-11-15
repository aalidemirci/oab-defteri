"""Ön yüzün kaydettiği her uzantının kaydetme penceresinde süzgeci var (saha bulgusu K-yeni-3).

Pardus 25'te (13.11.2026) Word evrakı (E01 .docx) kaydedilirken pencere "Tüm dosyalar | *" gösterdi:
`desktop/window.py` `TUR_SUZGECLERI`'nde yalnız .pdf ve .xlsx vardı. Ön yüz dosyaları `saveBlob` ile
köprünün `dosya_kaydet`'ine verir (`frontend/src/lib/download.ts`); şifreli yedek ayrı yoldan
(`kaydetme_yeri_sor`, `KAYDETME_SUZGECI`) kaydedilir. Bu test ön yüz kaynağını tarar: her `saveBlob`
çağrısının önerdiği adın uzantısı çözülür ve `TUR_SUZGECLERI`'nde aranır. Yeni bir kaydetme yeri yeni
bir uzantı getirirse ya da adın biçimi tarayıcının tanımadığı bir biçimse test düşer.

Adın çözümü: çağrıdaki ikinci argümanın metni; içindeki uzantılı metin (`"….xlsx"`, `` `…${…}.exe` ``),
`dosyaAdi([...], "pdf")` çağrısı ve argümandaki adların bir düzey tanımı (`const AD = "….xlsx"`,
`function adı(...) { ... }`; tanımdaki `bicim: EvrakBicimi` gibi bir parametre türünün dizgi
birleşimi; `etiketler.template` gibi bir özelliğin dosyadaki `template: AD` değerleri). Sunucunun
verdiği ad (`Content-Disposition`, `installer_name`) aynı uzantıyı taşır: ön yüzün yedek adı onunla
aynı kalıptadır (`docs/sozluk.md` §3 "Dosya adları"; kurulum dosyası `INSTALLER_PATTERN` `.exe`).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from desktop.window import KAYDETME_SUZGECI, TUR_SUZGECLERI

DEPO = Path(__file__).resolve().parents[2]
ON_YUZ = DEPO / "frontend" / "src"

_UZANTILI_METIN = re.compile(r"""\.([A-Za-z0-9]{2,5})["'`]""")
_DOSYA_ADI_CAGRISI = re.compile(r"""dosyaAdi\(\s*\[[\s\S]*?\]\s*,\s*["']([A-Za-z0-9]+)["']\s*\)""")
_TUR_PARAMETRESI = re.compile(r"\b\w+\s*:\s*([A-Z]\w*)")
#: Çözülen adlar: büyük harfli sabitler ve adı "Adi" ile biten işlevler (`kurtarmaBelgesiDosyaAdi`).
_AD = re.compile(r"\b(?:[A-Z][A-Z0-9_]+|[a-z]\w*Adi)\b")
_BIRLESIM = re.compile(r"""(?:export\s+)?type\s+\w+\s*=\s*(?:["'][a-z0-9]+["']\s*\|?\s*)+;""")
_OZELLIK = re.compile(r"\.(\w+)\b")


def _kaynaklar() -> dict[Path, str]:
    dosyalar = {}
    for yol in ON_YUZ.rglob("*"):
        if yol.suffix not in {".ts", ".tsx"} or ".test." in yol.name:
            continue
        dosyalar[yol] = yol.read_text(encoding="utf-8")
    assert len(dosyalar) > 50, "ön yüz kaynağı bulunamadı (yanlış yeşil)"
    return dosyalar


def _argumanlar(metin: str, acilis: int) -> list[str]:
    """`acilis`'teki `(`'tan başlayan çağrının üst düzey argümanları (metin olarak)."""
    derinlik = 0
    parca: list[str] = []
    argumanlar: list[str] = []
    for karakter in metin[acilis:]:
        if karakter in "([{":
            derinlik += 1
            if derinlik == 1:
                continue
        elif karakter in ")]}":
            derinlik -= 1
            if derinlik == 0:
                argumanlar.append("".join(parca))
                return argumanlar
        elif karakter == "," and derinlik == 1:
            argumanlar.append("".join(parca))
            parca = []
            continue
        parca.append(karakter)
    raise AssertionError("kapanmayan çağrı")


def _tanim(ad: str, kaynaklar: dict[Path, str]) -> str | None:
    """`ad`'ın ön yüzdeki tanımı: sabit, işlev ya da tür birleşimi (yoksa `None`)."""
    desenler = (
        rf"""(?:export\s+)?const\s+{ad}\b[^=]*=\s*([^;\n]+)""",
        rf"""(?:export\s+)?(?:async\s+)?function\s+{ad}\s*\(([\s\S]*?)\n\}}""",
        rf"""(?:export\s+)?type\s+{ad}\s*=\s*([^;]+);""",
    )
    for metin in kaynaklar.values():
        for desen in desenler:
            eslesme = re.search(desen, metin)
            if eslesme:
                return eslesme.group(0)
    return None


def _uzantilar(
    ifade: str, kaynaklar: dict[Path, str], dosya: str, *, derinlik: int = 2
) -> set[str]:
    bulunan = {f".{u.lower()}" for u in _UZANTILI_METIN.findall(ifade)}
    bulunan |= {f".{u.lower()}" for u in _DOSYA_ADI_CAGRISI.findall(ifade)}
    if derinlik == 0:
        return bulunan
    # `dosyaAdi([...], bicim)`: parametrenin türü dizgi birleşimidir (`EvrakBicimi = "pdf" | "docx"`).
    if re.search(r"dosyaAdi\([\s\S]*?,\s*[a-z]\w*\s*,?\s*\)", ifade):
        for tur in _TUR_PARAMETRESI.findall(ifade):
            tanim = _tanim(tur, kaynaklar)
            if tanim and _BIRLESIM.fullmatch(tanim.strip()):
                bulunan |= {f".{u}" for u in re.findall(r"""["']([a-z0-9]+)["']""", tanim)}
    for ad in set(_AD.findall(ifade)) - {"dosyaAdi"}:
        tanim = _tanim(ad, kaynaklar)
        if tanim is not None and tanim != ifade:
            bulunan |= _uzantilar(tanim, kaynaklar, dosya, derinlik=derinlik - 1)
    # `etiketler.template`: aynı dosyadaki `template: AD` değerleri.
    for ozellik in _OZELLIK.findall(ifade):
        for deger in re.findall(rf"\b{ozellik}\s*:\s*(\w+)", dosya):
            tanim = _tanim(deger, kaynaklar)
            if tanim is not None:
                bulunan |= _uzantilar(tanim, kaynaklar, dosya, derinlik=derinlik - 1)
    return bulunan


def _kaydetme_yerleri() -> dict[str, set[str]]:
    """`saveBlob` çağrısı → önerdiği adların uzantıları (`dosya:satır` anahtarıyla)."""
    kaynaklar = _kaynaklar()
    yerler: dict[str, set[str]] = {}
    for yol, metin in kaynaklar.items():
        for eslesme in re.finditer(r"\bsaveBlob\(", metin):
            if re.search(r"function\s+$", metin[: eslesme.start()]):
                continue  # tanımın kendisi
            argumanlar = _argumanlar(metin, eslesme.end() - 1)
            assert len(argumanlar) >= 2, f"{yol.name}: saveBlob adsız çağrılmış"
            satir = metin.count("\n", 0, eslesme.start()) + 1
            yerler[f"{yol.relative_to(DEPO).as_posix()}:{satir}"] = _uzantilar(
                argumanlar[1], kaynaklar, metin
            )
    return yerler


def test_on_yuzun_kaydettigi_her_uzantinin_suzgeci_var() -> None:
    yerler = _kaydetme_yerleri()

    cozulemeyen = [yer for yer, uzantilar in yerler.items() if not uzantilar]
    suzgecsiz = {yer: sorted(uzantilar - set(TUR_SUZGECLERI)) for yer, uzantilar in yerler.items()}

    assert cozulemeyen == [], "önerilen adın uzantısı çözülemedi; tarayıcıya biçimi ekleyin"
    assert {yer: u for yer, u in suzgecsiz.items() if u} == {}


def test_tarama_bilinen_kaydetme_yerlerini_gorur() -> None:
    """Yanlış yeşile karşı: bilinen yerler ve uzantılar taramada görünür (13.11.2026 durumu)."""
    yerler = _kaydetme_yerleri()
    butun = set().union(*yerler.values())

    assert len(yerler) >= 8
    assert {".pdf", ".docx", ".xlsx", ".exe"} <= butun
    evrak = [u for yer, u in yerler.items() if yer.startswith("frontend/src/modules/evrak/")]
    assert evrak == [{".pdf", ".docx"}]


def test_suzgec_uzantisi_anahtarla_aynidir_aciklama_turkcedir() -> None:
    """pywebview süzgeç açıklamasında yalnız harf, rakam ve boşluk kabul eder (`util.parse_file_type`)."""
    for uzanti, (suzgec,) in TUR_SUZGECLERI.items():
        aciklama, desen = re.fullmatch(r"(.+) \((\*\.\w+)\)", suzgec).groups()  # type: ignore[union-attr]
        assert desen == f"*{uzanti}"
        assert re.fullmatch(r"[\w ]+", aciklama)


def test_sifreli_yedek_ayri_suzgecle_kaydedilir() -> None:
    assert KAYDETME_SUZGECI == ("OAB Defteri yedeği (*.odbak)",)
    assert ".odbak" not in TUR_SUZGECLERI


@pytest.mark.parametrize(
    ("ifade", "beklenen"),
    [
        ('"sablon-veli-listesi.xlsx"', {".xlsx"}),
        ("`oab-defteri-${surum}.exe`", {".exe"}),
        ('ad ?? dosyaAdi([KOK, formatDate(bugun)], "pdf")', {".pdf"}),
        ("adsizBirSey", set()),
    ],
    ids=["dizgi", "sablon_dizgi", "dosya_adi", "cozulemeyen"],
)
def test_tarayici_ad_bicimlerini_cozer(ifade: str, beklenen: set[str]) -> None:
    assert _uzantilar(ifade, {}, "", derinlik=0) == beklenen
