"""Evrak hattının ilk kanıtı (F1a-3; T2, tasarım §9.1, §10 `ev::test_docx_pdf_icerik_esdegerligi`).

Sabitlenenler: (1) aynı içerik modelinden çizilen Word ve PDF'in kanonik metin
akışı modelinkine EŞİTTİR — gövde blokları belge sırasıyla, tablo hücreleri satır
satır; altlık ve sayfa numarası karşılaştırmaya girmez (UY-18); (2) Word çıktısında
`w:caps` yoktur, belge dili `tr-TR`'dir; (3) içerik özeti modelin kanonik JSON'undan
çıkar ve kararlıdır; (4) python-docx'e uygulama kodunda yalnız `shared/docx.py`
kapısından gidilir.
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from shared import docx as cizici
from shared import evrak
from shared.text import tr_upper

BACKEND = Path(__file__).resolve().parents[2]

#: PDF altlığı ("OAB Defteri · DUMAN · Sayfa 1/1") — her sayfada tekrar eder.
_ALTLIK = re.compile(r"OAB Defteri · \S+ · Sayfa \d+\s*/\s*\d+")


def _bosluksuz(parcalar: list[str] | str) -> str:
    metin = "".join(parcalar) if isinstance(parcalar, list) else parcalar
    return re.sub(r"\s+", "", metin)


def _pdf_metni(veri: bytes) -> str:
    from pypdf import PdfReader

    okuyucu = PdfReader(io.BytesIO(veri))
    return "\n".join(sayfa.extract_text() or "" for sayfa in okuyucu.pages)


@pytest.fixture(scope="module")
def belge() -> evrak.Belge:
    return evrak.ornek_belge()


@pytest.fixture(scope="module")
def docx_bayt(belge: evrak.Belge) -> bytes:
    return evrak.docx_ciz(belge)


def test_word_govde_akisi_modelle_ayni(belge: evrak.Belge, docx_bayt: bytes) -> None:
    akis = cizici.govde_metin_akisi(cizici.ac(docx_bayt))
    assert akis == evrak.metin_akisi(belge)


def test_pdf_ve_word_icerik_esdegerligi(belge: evrak.Belge, docx_bayt: bytes) -> None:
    """İki çıktıdan aynı kanonik metin akışı çıkar (boşluk ve satır sonu normalleştirilir)."""
    pdf_metni = _pdf_metni(evrak.pdf_ciz(belge))
    assert _ALTLIK.search(pdf_metni), "PDF altlığı 'OAB Defteri · <kod> · Sayfa n/m' değil"
    pdf_govde = _ALTLIK.sub("", pdf_metni)
    word_govde = cizici.govde_metin_akisi(cizici.ac(docx_bayt))

    beklenen = _bosluksuz(evrak.metin_akisi(belge))
    assert _bosluksuz(pdf_govde) == beklenen
    assert _bosluksuz(word_govde) == beklenen
    assert evrak.TURKCE_ORNEK.replace(" ", "") in beklenen


def test_word_ciktisinda_caps_yok_ve_dil_turkce(docx_bayt: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(docx_bayt)) as arsiv:
        govde = arsiv.read("word/document.xml").decode("utf-8")
        stiller = arsiv.read("word/styles.xml").decode("utf-8")
    assert "<w:caps" not in govde and "<w:smallCaps" not in govde
    varsayilan = re.search(r"<w:docDefaults>.*?</w:docDefaults>", stiller, re.DOTALL)
    assert varsayilan is not None
    assert f'w:val="{cizici.DIL}"' in varsayilan.group()
    assert "<w:caps" not in varsayilan.group()


def test_word_altligi_sayfa_alanlarini_tasir(docx_bayt: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(docx_bayt)) as arsiv:
        altliklar = [
            arsiv.read(ad).decode("utf-8")
            for ad in arsiv.namelist()
            if ad.startswith("word/footer")
        ]
    birlesik = "".join(altliklar)
    assert "OAB Defteri · DUMAN · Sayfa " in birlesik
    assert " PAGE " in birlesik and " NUMPAGES " in birlesik


def test_word_a4_ve_yazi_tipi(docx_bayt: bytes) -> None:
    d = cizici.ac(docx_bayt)
    bolum = d.sections[0]
    assert bolum.page_width is not None and bolum.page_height is not None
    assert round(bolum.page_width.mm) == 210 and round(bolum.page_height.mm) == 297
    normal = d.styles["Normal"]
    assert normal.font.name == cizici.YAZI_TIPI
    assert normal.font.size.pt == cizici.GOVDE_PUNTO


def test_icerik_ozeti_kanonik_jsondan_ve_kararli(belge: evrak.Belge) -> None:
    assert evrak.icerik_ozeti(belge) == evrak.icerik_ozeti(evrak.ornek_belge())
    assert re.fullmatch(r"[0-9a-f]{64}", evrak.icerik_ozeti(belge))
    degisik = replace(belge, kod="E01")
    assert evrak.icerik_ozeti(degisik) != evrak.icerik_ozeti(belge)
    # JSON Türkçe harfleri kaçışsız taşır (okunur) ve anahtarları sıralıdır.
    json_metni = evrak.kanonik_json(belge)
    assert evrak.TURKCE_ORNEK in json_metni
    assert json_metni.index('"antet"') < json_metni.index('"bloklar"') < json_metni.index('"kod"')


def test_word_baytlari_ozeti_belirlemez(belge: evrak.Belge) -> None:
    """Özet docx zip baytından değil modelden çıkar: iki çizim aynı özeti verir."""
    evrak.docx_ciz(belge)
    evrak.docx_ciz(belge)
    assert evrak.icerik_ozeti(belge) == evrak.icerik_ozeti(evrak.ornek_belge())


def test_baslik_turkce_buyuk_harfle_saklanir() -> None:
    assert (
        evrak.Baslik("işçi izin listesi").metin
        == tr_upper("işçi izin listesi")
        == "İŞÇİ İZİN LİSTESİ"
    )


def test_konum_cumlesi_imzanin_hemen_ustunde_olmali() -> None:
    antet = evrak.Antet(
        tc="T.C.", authority="ÖRNEK KAYMAKAMLIĞI", unit_line="Örnek Okulu Müdürlüğü"
    )
    imza = evrak.Imza(sahipler=(evrak.ImzaSahibi("Ad SOYAD", "Birlik Başkanı"),))
    evrak.Belge(kod="E01", antet=antet, bloklar=(evrak.KonumCumlesi("x"), imza))
    with pytest.raises(ValueError, match="imza bloğunun hemen üstünde"):
        evrak.Belge(
            kod="E01", antet=antet, bloklar=(evrak.KonumCumlesi("x"), evrak.Paragraf("y"), imza)
        )
    with pytest.raises(ValueError, match="imza bloğunun hemen üstünde"):
        evrak.Belge(kod="E01", antet=antet, bloklar=(evrak.KonumCumlesi("x"),))


def test_tablo_satiri_baslik_sayisina_uymali() -> None:
    with pytest.raises(ValueError):
        evrak.Tablo(basliklar=("a", "b"), satirlar=(("1",),))


# python-docx'e doğrudan giden kod kalıpları (yorum/belge dizesi değil, içe aktarma).
_YASAK = re.compile(r"^\s*(from\s+docx\b|import\s+docx\b)", re.MULTILINE)


def test_python_docx_yalniz_shared_docx_kapisindan() -> None:
    """Uygulama kodunda python-docx içe aktarması yalnız `shared/docx.py`'de olabilir.

    Biçim kararları (dil, `w:caps` yokluğu, yazı tipi, A4) tek yerde sabitlensin;
    yeni bir Word yolu onları sessizce atlamasın. Testler kapsam dışıdır.
    """
    ihlaller: list[str] = []
    for kok in ("apps", "shared", "config"):
        for yol in sorted((BACKEND / kok).rglob("*.py")):
            goreli = yol.relative_to(BACKEND).as_posix()
            if "/tests/" in f"/{goreli}" or goreli == "shared/docx.py":
                continue
            metin = yol.read_text(encoding="utf-8")
            for eslesme in _YASAK.finditer(metin):
                ihlaller.append(f"{goreli}:{metin.count(chr(10), 0, eslesme.start()) + 1}")
    assert ihlaller == [], f"python-docx'e shared.docx dışından gidiliyor: {ihlaller}"
