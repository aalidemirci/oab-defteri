"""Evrak hattının ilk kanıtı (F1a-3; T2, tasarım §9.1, §10 `ev::test_docx_pdf_icerik_esdegerligi`).

Sabitlenenler: (1) aynı içerik modelinden çizilen Word ve PDF'in kanonik metin
akışı modelinkine EŞİTTİR — gövde blokları belge sırasıyla, tablo hücreleri satır
satır; altlık ve sayfa numarası karşılaştırmaya girmez (UY-18); (2) Word çıktısında
`w:caps` yoktur, belge dili `tr-TR`'dir; (3) içerik özeti modelin kanonik JSON'undan
çıkar ve kararlıdır; (4) python-docx'e uygulama kodunda yalnız `shared/docx.py`
kapısından gidilir; (5) dipnot (`Dipnot`; plan F1b-2 "E63") belgenin sonunda durur, iki
çizicide gövdenin son paragrafıdır ve metin akışına girer (örnek belge onu taşır: eşdeğerlik
testleri dipnotu da sınar); (6) F1c 9. adımın blokları (tasarım §9.1-8, §9.2; plan F1c kararları
"Evrak biçimi"): bölüm başlığı (`AltBaslik`), sütun oranı iki çizicide aynı yüzde, tablo puntosu
(1-4 sütun 12, 5-7 sütun 10, ötesi ret), KDT tasarımdaki metnin aynısı, "Ad SOYAD" (RYUE md. 17/2),
okul ve birlik antedi, PDF'te Liberation Serif, kayıtlı JSON'dan geri çevirme (`belge_coz`) aynı
özeti verir, bozuk içerik reddedilir. Örnek belge bütün blok türlerini taşır: eşdeğerlik testleri
yeni blokları da sınar; (7) punto alt sınırı (RYUE md. 7/1; kullanıcı kararı 11.11.2026): yazı
alanında 9 puntodan küçük metin yoktur, altlık 12 punto — PDF'teki yazı boyutları geri okunarak ve
Word çalıştırmalarından (`test_punto_alt_siniri_*`).
"""

from __future__ import annotations

import io
import math
import re
import zipfile
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

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


def test_dipnot_belgenin_sonunda_durur() -> None:
    """Dipnottan sonra yalnız başka dipnot gelebilir; imzadan sonra iki dipnot geçerlidir."""
    antet = evrak.Antet(
        tc="T.C.", authority="ÖRNEK KAYMAKAMLIĞI", unit_line="Örnek Okulu Müdürlüğü"
    )
    imza = evrak.Imza(sahipler=(evrak.ImzaSahibi("Teslim eden", "Program yöneticisi"),))
    evrak.Belge(
        kod="E63",
        antet=antet,
        bloklar=(imza, evrak.Dipnot("birinci"), evrak.Dipnot("ikinci")),
    )
    with pytest.raises(ValueError, match="Dipnot belgenin sonunda durur"):
        evrak.Belge(kod="E63", antet=antet, bloklar=(evrak.Dipnot("x"), imza))
    with pytest.raises(ValueError, match="Dipnot belgenin sonunda durur"):
        evrak.Belge(kod="E63", antet=antet, bloklar=(evrak.Dipnot("x"), evrak.Paragraf("y")))


def test_dipnot_kanonik_bicimde_ve_akista(belge: evrak.Belge, docx_bayt: bytes) -> None:
    """Örnek belgenin son bloğu kişisel veri dipnotudur: kanonik JSON'da `dipnot` türüyle, metin
    akışının sonunda; Word'de gövdenin son paragrafı, 9 punto (PDF'teki `.dipnot` gibi; RYUE md.
    7/1, kullanıcı kararı 11.11.2026)."""
    assert isinstance(belge.bloklar[-1], evrak.Dipnot)
    assert '"tur":"dipnot"' in evrak.kanonik_json(belge)
    assert evrak.metin_akisi(belge)[-1] == evrak.KISISEL_VERI_DIPNOTU
    son = [p for p in cizici.ac(docx_bayt).paragraphs if p.text.strip()][-1]
    assert son.text == evrak.KISISEL_VERI_DIPNOTU
    boyutlar = {run.font.size for run in son.runs if run.text}
    assert {None if b is None else b.pt for b in boyutlar} == {cizici.DIPNOT_PUNTO}
    html = evrak.html_ciz(belge)
    assert html.count('class="dipnot dipnot-ilk"') == 1


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


# ============================================================ F1c 9. adım: hattın yeni blokları


def _repo_dosyasi(goreli: str) -> str:
    """Depo kökündeki dosya (yerelde depo kökü, konteynerde `/repo`)."""
    for kok in (BACKEND.parent, Path("/repo")):
        yol = kok / goreli
        if yol.is_file():
            return yol.read_text(encoding="utf-8")
    pytest.skip(f"{goreli} bulunamadı")


def test_kdt_tasarimdaki_metnin_aynisidir() -> None:
    """KDT tek sabittir ve tasarım §9.2'nin tablosundaki metinle BİREBİR aynıdır."""
    tasarim = _repo_dosyasi("docs/tasarim/2026-10-31-genel-tasarim.md")
    satir = next(s for s in tasarim.splitlines() if s.startswith("| **KDT** |"))
    assert f'"{evrak.KDT}"' in satir
    assert f'"{evrak.TASLAK_IBARESI}"' in tasarim
    assert evrak.KDT in evrak.metin_akisi(evrak.ornek_belge())


@pytest.mark.parametrize(
    ("ad", "soyad", "beklenen"),
    [
        ("ayşe", "örnek", "Ayşe ÖRNEK"),
        ("İSMAİL", "deneme", "İsmail DENEME"),
        ("  ayşe   nur ", " iğdır  kaya ", "Ayşe Nur İĞDIR KAYA"),
        ("ılgın", "işçi", "Ilgın İŞÇİ"),
        ("Zeynep", "", "Zeynep"),
    ],
)
def test_ad_soyad_ryue_17_2_bicimi(ad: str, soyad: str, beklenen: str) -> None:
    """RYUE md. 17/2: adın ilk harfi büyük diğerleri küçük, soyadı büyük; Türkçe i/ı doğru."""
    assert evrak.ad_soyad(ad, soyad) == beklenen


def test_okul_ve_birlik_anteti() -> None:
    """Birliğin belgeleri okul antedinin altına "Okul-Aile Birliği" satırını ekler (§9.1-8); kurum
    kodu antede yoktur. İki çizici satırı birim satırının hemen altında, antette çizer."""
    okul = evrak.okul_anteti(okul_adi="Örnek Ortaokulu", ilce="iğdır")
    assert (okul.tc, okul.authority, okul.unit_line, okul.alt_birim) == (
        "T.C.",
        "İĞDIR KAYMAKAMLIĞI",
        "Örnek Ortaokulu Müdürlüğü",
        "",
    )
    birlik = evrak.birlik_anteti(okul_adi="Örnek Ortaokulu", ilce="iğdır")
    assert birlik.alt_birim == "Okul-Aile Birliği" and birlik.unit_line == okul.unit_line
    belge = evrak.Belge(kod="E01", antet=birlik, bloklar=(evrak.Paragraf("x"),))
    html = evrak.html_ciz(belge)
    antet = html[html.index('<div class="letterhead">') : html.index('<div class="rule">')]
    assert antet.index("Örnek Ortaokulu Müdürlüğü") < antet.index("Okul-Aile Birliği")
    satirlar = cizici.govde_metin_akisi(cizici.ac(evrak.docx_ciz(belge)))
    assert satirlar[:4] == [
        "T.C.",
        "İĞDIR KAYMAKAMLIĞI",
        "Örnek Ortaokulu Müdürlüğü",
        "Okul-Aile Birliği",
    ]


def test_alt_baslik_harf_donusturmez_ve_sonrakine_baglidir(
    belge: evrak.Belge, docx_bayt: bytes
) -> None:
    alt = next(b for b in belge.bloklar if isinstance(b, evrak.AltBaslik))
    assert alt.metin == "A. Türkçe örnek"
    assert '"tur":"alt_baslik"' in evrak.kanonik_json(belge)
    html = evrak.html_ciz(belge)
    assert '<p class="alt-baslik">A. Türkçe örnek</p>' in html
    p = next(p for p in cizici.ac(docx_bayt).paragraphs if p.text == "A. Türkçe örnek")
    assert p.paragraph_format.keep_with_next is True
    assert all(run.bold for run in p.runs if run.text)


@pytest.mark.parametrize(("sutun", "punto"), [(1, 12), (3, 12), (4, 12), (5, 10), (6, 10), (7, 10)])
def test_tablo_puntosu_sutun_sayisindan(sutun: int, punto: int) -> None:
    """Gövde 12 punto; 5-7 sütunlu tabloda 10 (tasarım §9.1-8; plan F1c kararları)."""
    assert evrak.tablo_punto(sutun) == punto


@pytest.mark.parametrize("sutun", [0, 8])
def test_karar_olmayan_tablo_genisligi_reddedilir(sutun: int) -> None:
    with pytest.raises(ValueError):
        evrak.Tablo(basliklar=tuple(str(i) for i in range(sutun)), satirlar=())


@pytest.mark.parametrize(
    "oranlar", [(1, 2), (1, 0, 1), (1, -1, 1), (1.5, 1, 1)], ids=["eksik", "sifir", "eksi", "kesir"]
)
def test_sutun_orani_her_sutuna_bir_pozitif_tamsayi(oranlar: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError, match="sütun oranı"):
        evrak.Tablo(basliklar=("a", "b", "c"), satirlar=(), oranlar=oranlar)


def test_sutun_orani_iki_cizicide_ayni_yuzde(belge: evrak.Belge, docx_bayt: bytes) -> None:
    """Sütun genişlikleri yazı alanının yüzdesidir: PDF'te `<col>` genişliği, Word'de hücre
    genişliği aynı yüzdeden çıkar; oransız tablo eşit sütunludur. 5 sütunlu tablo iki çizicide 10
    puntodur, dar tablo gövde puntosundadır."""
    tablolar = [b for b in belge.bloklar if isinstance(b, evrak.Tablo)]
    dar, _genis = tablolar
    assert evrak.sutun_yuzdeleri(dar) == (14.29, 57.14, 28.57)
    assert evrak.sutun_yuzdeleri(evrak.Tablo(basliklar=("a", "b"), satirlar=())) == (50.0, 50.0)
    html = evrak.html_ciz(belge)
    assert '<table class="doc-table punto-12">' in html
    assert '<table class="doc-table punto-10">' in html
    for tablo in tablolar:
        cols = "".join(f'<col style="width: {y:.2f}%">' for y in evrak.sutun_yuzdeleri(tablo))
        assert f"<colgroup>{cols}</colgroup>" in html
    word = cizici.ac(docx_bayt).tables[: len(tablolar)]
    for tablo, wt in zip(tablolar, word, strict=True):
        beklenen = [round(cizici.YAZI_ALANI_CM * y / 100, 2) for y in evrak.sutun_yuzdeleri(tablo)]
        for satir in wt.rows:
            assert [round(h.width.cm, 2) for h in satir.cells] == beklenen
        assert wt.autofit is False
        boyutlar: set[float | None] = {
            None if r.font.size is None else r.font.size.pt
            for h in wt.rows[0].cells
            for r in h.paragraphs[0].runs
        }
        beklenen_boyut: set[float | None] = {None} if tablo is dar else {10.0}
        assert boyutlar == beklenen_boyut


def _kaynaklar(sayfa: Any) -> Any:
    return sayfa["/Resources"]


def test_pdf_evrak_hatti_liberation_serif_ile_dizilir(belge: evrak.Belge) -> None:
    """PDF'te yazı tipi paketli Liberation Serif'tir (tasarım §9.1-8); Türkçe örnek ve tablo bu yazı
    tipiyle dizilir, DejaVu yalnız eksik glif yedeğidir (örnekte eksik glif yok)."""
    from pypdf import PdfReader

    okuyucu = PdfReader(io.BytesIO(evrak.pdf_ciz(belge)))
    adlar = {
        str(tip.get_object()["/BaseFont"]).split("+", 1)[-1]
        for sayfa in okuyucu.pages
        for tip in _kaynaklar(sayfa)["/Font"].values()
    }
    assert adlar == {"Liberation-Serif", "Liberation-Serif-Bold"}, adlar


# ============================================================ punto alt sınırı (RYUE md. 7/1)


def pdf_yazi_boyutlari(veri: bytes) -> list[tuple[int, str, float]]:
    """PDF'teki her metin parçasının (sayfa sırası, metin, punto) üçlüsü.

    pypdf'in metin ziyaretçisiyle okunur: görünen punto `Tf` boyutunun metin matrisi (`Tm`) ve
    dönüşüm matrisi (`cm`) ile ölçeklenmişidir (dikey ölçek; WeasyPrint y eksenini çevirir, mutlak
    değer alınır). Boş parçalar atlanır. `apps.oab.tests.kurallar.test_evrak_kurallari` E63 için
    aynı yardımcıyı kullanır.
    """
    from pypdf import PdfReader

    parcalar: list[tuple[int, str, float]] = []
    for sira, sayfa in enumerate(PdfReader(io.BytesIO(veri)).pages):

        def ziyaretci(
            metin: str, cm: Any, tm: Any, _tip: Any, boyut: float, sira: int = sira
        ) -> None:
            if metin.strip():
                olcek = math.hypot(tm[2], tm[3]) * math.hypot(cm[2], cm[3])
                parcalar.append((sira, metin.strip(), round(boyut * olcek, 2)))

        sayfa.extract_text(visitor_text=ziyaretci)
    return parcalar


def _word_calistirmalari(d: Any) -> Iterator[Any]:
    """Gövdedeki bütün çalıştırmalar: paragraflar ve tablo hücreleri belge sırasıyla."""
    from docx.table import Table

    for oge in d.iter_inner_content():
        if isinstance(oge, Table):
            for satir in oge.rows:
                for hucre in satir.cells:
                    for paragraf in hucre.paragraphs:
                        yield from paragraf.runs
        else:
            yield from oge.runs


def test_punto_alt_siniri_sabitleri() -> None:
    """Çizicinin puntoları RYUE md. 7/1'in yazı alanı alt sınırının (9) altına inmez (kullanıcı kararı
    11.11.2026): konum cümlesi, dipnot, geniş tablo ve gövde; altlık 12 (md. 7/1 esası; md. 27)."""
    assert cizici.EN_KUCUK_PUNTO == 9
    assert cizici.KONUM_PUNTO == cizici.DIPNOT_PUNTO == 9
    assert min(evrak.tablo_punto(sutun) for sutun in range(1, evrak.GENIS_TABLO_EN_COK + 1)) >= 9
    assert evrak.GOVDE_PUNTO == cizici.GOVDE_PUNTO == cizici.ALTLIK_PUNTO == 12


def test_punto_alt_siniri_pdf(belge: evrak.Belge) -> None:
    """PDF'teki yazı boyutları geri okunur: yazı alanında 9 puntodan küçük metin yoktur; konum cümlesi
    ve dipnot 9, altlık 12 puntodur (RYUE md. 7/1, md. 27; kullanıcı kararı 11.11.2026). Örnek belge
    bütün blok türlerini taşır (5 sütunlu tablo, başlığın alt satırı, konum cümlesi, dipnot)."""
    parcalar = pdf_yazi_boyutlari(evrak.pdf_ciz(belge))
    assert parcalar
    kucukler = [(metin, boyut) for _s, metin, boyut in parcalar if boyut < cizici.EN_KUCUK_PUNTO]
    assert kucukler == [], kucukler
    boyutlar = {metin: boyut for _s, metin, boyut in parcalar}
    assert boyutlar[evrak.KISISEL_VERI_DIPNOTU] == cizici.DIPNOT_PUNTO
    assert {b for _s, m, b in parcalar if m in evrak.KDT} == {float(cizici.KONUM_PUNTO)}
    altlik = {b for _s, m, b in parcalar if m.startswith("OAB Defteri ·")}
    assert altlik == {float(cizici.ALTLIK_PUNTO)}, altlik


def test_punto_alt_siniri_word(docx_bayt: bytes) -> None:
    """Word'de her çalıştırma ya Normal biçeminin 12 puntosunu alır ya da en az 9 puntodur; dipnot
    9, altlık 12 punto ve 1,5 cm'lik alt boşluğun içinde (PDF'le eşdeğer)."""
    d = cizici.ac(docx_bayt)
    assert d.styles["Normal"].font.size.pt == cizici.GOVDE_PUNTO
    boyutlar = [run.font.size for run in _word_calistirmalari(d) if run.text.strip()]
    kucukler = [b.pt for b in boyutlar if b is not None and b.pt < cizici.EN_KUCUK_PUNTO]
    assert boyutlar and kucukler == [], kucukler
    for bolum in d.sections:
        assert bolum.footer_distance is not None
        assert round(bolum.footer_distance.cm, 2) == cizici.ALTLIK_UZAKLIGI_CM
        altlik = {run.font.size.pt for p in bolum.footer.paragraphs for run in p.runs}
        assert altlik == {float(cizici.ALTLIK_PUNTO)}, altlik


def test_belge_coz_kanonik_jsonu_ayni_modele_cevirir(belge: evrak.Belge) -> None:
    """Yeniden basım kayıtlı JSON'dan çizilir ve aynı özeti verir (§9.1-2): geri çevrilen model
    eşittir, kanonik JSON'u kayıtlı metnin aynısıdır."""
    metin = evrak.kanonik_json(belge)
    geri = evrak.belge_coz(metin)
    assert geri == belge and evrak.kanonik_json(geri) == metin
    assert evrak.icerik_ozeti(geri) == evrak.icerik_ozeti(belge) == evrak.metin_ozeti(metin)


_BOZMALAR: dict[str, tuple[str, str]] = {
    "kanonik_degil": ('{"antet"', '{ "antet"'),
    "fazla_alan": ('"kod":"DUMAN"', '"kod":"DUMAN","fazla":1'),
    "bilinmeyen_blok": ('"tur":"paragraf"', '"tur":"bilinmeyen"'),
    "oran_eksik": ('"oranlar":[1,4,2]', '"oranlar":[1,4]'),
    "imza_alanlari_tutmuyor": ('"tur":"imza"', '"tur":"dipnot"'),
    "baslik_kucuk_harf": ('"metin":"EVRAK HATTI DUMAN TESTİ"', '"metin":"evrak hattı duman testi"'),
    "tur_yanlis": ('"tarih":"01.11.2026"', '"tarih":1'),
}


@pytest.mark.parametrize("ad", [*_BOZMALAR, "json_bozuk", "dizi"])
def test_belge_coz_bozuk_icerigi_reddeder(belge: evrak.Belge, ad: str) -> None:
    dogru = evrak.kanonik_json(belge)
    if ad == "json_bozuk":
        metin = dogru[:-1]
    elif ad == "dizi":
        metin = "[]"
    else:
        eski, yeni = _BOZMALAR[ad]
        assert eski in dogru, ad
        metin = dogru.replace(eski, yeni, 1)
    with pytest.raises(evrak.BelgeCozulemedi):
        evrak.belge_coz(metin)
