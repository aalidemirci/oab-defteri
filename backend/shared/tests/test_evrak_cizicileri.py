"""Evrak hattının F2 ekleri (plan F2 §4.2, 8. adım): RYUE resmî yazı bloğu, ek bölümü, sayfa sonu,
Excel çizicisi ve tek dosyalık web sayfası.

Sabitlenenler: (1) resmî yazının başı RYUE md. 10-14'e uyar — antet okul kartından (md. 10/3),
"Sayı:" ve tarih aynı satırda, tarih yazı alanının sağında (md. 11/2, 12/1), "Konu:" bir alt satırda
ve yazı alanının yarısını geçmez (md. 13/1), yan başlıklar yazı alanının solundan başlar (md. 11/2) ve
iki noktaları aynı hizadadır (md. 15/3), muhatap büyük harfle ve birim parantez içinde alt satırda
(md. 14/2, 14/5; kullanıcı kararı S11 (a)); (2) "Ek:" imza bölümünden sonra (md. 18/1; programda imza
bloğunun hemen ardından), tek ekte yanında, birden çok ekte altında numaralı (md. 18/2); (3) sayfa
sonu sonraki bloğu yeni sayfaya iter, metin taşımaz; (4) yeni bloklar iki çizicide aynı metin akışını
verir, punto alt sınırı (9) korunur, kayıtlı JSON'dan aynı modele döner; (5) Excel çıktısı aynı metin
akışını verir (resmî yazıyı reddeder), A4 ve altlık ayarlıdır, yazı tipi Times New Roman ve 9
puntodan küçük değildir, değerler metindir; (6) web sayfası tek dosyadır,
hiçbir dış kaynak (bağlantı, betik, görsel, `url(...)`, `@import`) taşımaz, metni kaçışlıdır ve
gövdesinin metni modelinkine eşittir; (7) resmî yazının metin paragrafı 1,25 cm içeriden, iki yana
yaslı ve aralıksızdır (md. 16/4), imza bölümünde tek imza sağ yarıda, iki imzada üst unvan sağdadır
(md. 17/1, 17/11; plan F2 10. adım), TFB konum cümlesi tasarım §9.2'nin metnidir.

Adlar UYDURMADIR.
"""

from __future__ import annotations

import io
import re
import zipfile
from html.parser import HTMLParser
from typing import Any

import pytest

from shared import docx as cizici
from shared import evrak
from shared import xlsx as excel
from shared.letterhead import MEM_IL, MEM_ILCE, mem_muhatabi
from shared.tests.test_evrak import _ALTLIK, _bosluksuz, _pdf_metni, pdf_yazi_boyutlari

ORNEKLER = {
    "duman": evrak.ornek_belge,
    "resmi_yazi": evrak.ornek_resmi_yazi,
    "sayfali": evrak.ornek_sayfali_belge,
}
#: Excel çizicisinin örnekleri: resmî yazı Excel'e çizilmez (`test_xlsx_resmi_yaziyi_reddeder`).
EXCEL_ORNEKLERI = sorted(ad for ad in ORNEKLER if ad != "resmi_yazi")


@pytest.fixture(scope="module")
def resmi() -> evrak.Belge:
    return evrak.ornek_resmi_yazi()


@pytest.fixture(scope="module")
def resmi_pdf(resmi: evrak.Belge) -> bytes:
    return evrak.pdf_ciz(resmi)


@pytest.fixture(scope="module")
def resmi_docx(resmi: evrak.Belge) -> bytes:
    return evrak.docx_ciz(resmi)


def _resmi(**alanlar: Any) -> evrak.ResmiYazi:
    varsayilan = {
        "sayi": "………",
        "tarih": "01.11.2026",
        "konu": "Uydurma Konu",
        "muhatap": "örnek ilçe kaymakamlığına",
    }
    return evrak.ResmiYazi(**{**varsayilan, **alanlar})


def _imza() -> evrak.Imza:
    return evrak.Imza(sahipler=(evrak.ImzaSahibi("Ayşe ÖRNEK", "Okul Müdürü"),))


def _antet() -> evrak.Antet:
    return evrak.okul_anteti(okul_adi="Örnek Ortaokulu", ilce="Örnek İlçe")


# ============================================================ resmî yazı bloğu (RYUE md. 10-14)


def test_resmi_yazi_basi_metin_akisinda_ryue_sirasiyla(resmi: evrak.Belge) -> None:
    """Antet (md. 10/3: T.C., kaymakamlık, okulun müdürlüğü) → "Sayı", ":", sayı, tarih → "Konu", ":",
    konu → muhatap (iki satır) → metin → imza → ek. Yan başlığın iki noktası ızgarada kendi
    sütunundadır (md. 15/3)."""
    akis = evrak.metin_akisi(resmi)
    assert akis[:3] == ["T.C.", "ÖRNEK İLÇE KAYMAKAMLIĞI", "Örnek Ortaokulu Müdürlüğü"]
    assert akis[3:12] == [
        "Sayı",
        ":",
        "………",
        "01.11.2026",
        "Konu",
        ":",
        "Genel Kurulda İbra Edilmeyen Yönetim Kurulu",
        "ÖRNEK İLÇE KAYMAKAMLIĞINA",
        "(İlçe Millî Eğitim Müdürlüğü)",
    ]
    assert akis[-3:] == [
        "Ek:",
        "1- Teslim tutanağı (1 sayfa)",
        "2- Genel kurul tutanağı örneği (2 sayfa)",
    ]
    # Ekler imza bölümünden sonradır (md. 18/1).
    assert akis.index("Okul Müdürü") < akis.index("Ek:")


def test_resmi_yazi_word_akisi_ve_pdf_esdegerligi(
    resmi: evrak.Belge, resmi_pdf: bytes, resmi_docx: bytes
) -> None:
    """Yeni bloklar iki çizicide aynı metin akışını verir (tek içerik, iki çizici; tasarım §9.1)."""
    word = cizici.govde_metin_akisi(cizici.ac(resmi_docx))
    assert word == evrak.metin_akisi(resmi)
    pdf_metni = _pdf_metni(resmi_pdf)
    assert _ALTLIK.search(pdf_metni)
    assert _bosluksuz(_ALTLIK.sub("", pdf_metni)) == _bosluksuz(evrak.metin_akisi(resmi))


def test_resmi_yazi_word_izgarasi(resmi_docx: bytes) -> None:
    """Word'de "Sayı" ve tarih aynı satırdadır, tarih sağa yaslıdır (md. 12/1); yan başlıklar sola
    yaslıdır, iki noktaları iki satırda aynı sütundadır (aynı hiza, md. 15/3); konu sütunu yazı
    alanının yarısında biter (md. 13/1); ızgara çerçevesizdir. Muhatap ortalıdır."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    d = cizici.ac(resmi_docx)
    izgara = d.tables[0]
    sayi, konu = izgara.rows
    assert [h.text for h in sayi.cells] == ["Sayı", ":", "………", "01.11.2026"]
    assert [h.text for h in konu.cells] == [
        "Konu",
        ":",
        "Genel Kurulda İbra Edilmeyen Yönetim Kurulu",
        "",
    ]
    sol, sag = WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT
    for satir in (sayi, konu):
        assert [h.paragraphs[0].alignment for h in satir.cells] == [sol, sol, sol, sag]
    genislikler = [h.width.cm for h in sayi.cells]
    assert [h.width.cm for h in konu.cells] == genislikler
    assert sum(genislikler[:3]) == pytest.approx(cizici.YAZI_ALANI_CM / 2, abs=0.01)
    assert sum(genislikler) == pytest.approx(cizici.YAZI_ALANI_CM, abs=0.01)
    assert izgara.style is None or "Grid" not in izgara.style.name
    muhatap = [p for p in d.paragraphs if p.text == "ÖRNEK İLÇE KAYMAKAMLIĞINA"]
    assert len(muhatap) == 1 and muhatap[0].alignment == WD_ALIGN_PARAGRAPH.CENTER


def test_resmi_yazi_pdf_sayi_ve_tarih_ayni_satirda(resmi_pdf: bytes) -> None:
    """PDF'in düzen kipindeki metninde (pypdf `layout`): "Sayı:" ile tarih aynı satırdadır, tarih
    satırın sağ yarısında ve sonundadır (md. 12/1); "Konu:" bir alt satırdadır, iki nokta "Sayı:"nınkiyle
    aynı hizadadır (md. 15/3; düzen kipinin bir karakterlik payıyla); uzun konunun devamı yan başlığın
    altını boş bırakır (md. 13/1); muhatap konudan sonra, ortadadır (md. 14/1)."""
    from pypdf import PdfReader

    metin = PdfReader(io.BytesIO(resmi_pdf)).pages[0].extract_text(extraction_mode="layout")
    satirlar = metin.splitlines()
    genislik = max(len(s.rstrip()) for s in satirlar)
    (sayi,) = [s for s in satirlar if re.search(r"Sayı\s*:", s)]
    assert sayi.rstrip().endswith("01.11.2026")
    assert sayi.index("01.11.2026") > genislik / 2 > sayi.index("Sayı")
    sira = satirlar.index(sayi)
    konu, devam = satirlar[sira + 1], satirlar[sira + 2]
    assert re.match(r"\s*Konu\s*:\s*Genel Kurulda", konu)
    assert konu.index("Konu") == sayi.index("Sayı")
    assert abs(konu.index(":") - sayi.index(":")) <= 1
    assert devam.strip() == "Kurulu" and len(devam) - len(devam.lstrip()) > konu.index(":")
    (muhatap,) = [s for s in satirlar if "ÖRNEK İLÇE KAYMAKAMLIĞINA" in s]
    assert satirlar.index(muhatap) > sira + 2
    assert muhatap.index("ÖRNEK") > genislik / 4


def test_resmi_yazi_word_yan_basliklar_yazi_alaninin_solundan(resmi_docx: bytes) -> None:
    """Md. 11/2: "Sayı:" yazı alanının solundan başlanarak yazılır ("Konu:" altında, md. 13/1). Word'de
    ızgara sola hizalı ve girintisizdir (`w:tblInd` 0), hücrelerin sol ve sağ iç boşluğu sıfırdır
    (`w:tblCellMar`; hücrede `w:tcMar` yok), yan başlık paragrafında girinti yoktur: "Sayı" ve "Konu"
    yazı alanının sol kenarından başlar, tarih sağ kenarda biter (md. 12/1). Öğeler şemanın sırasıyla
    yazılır (Word onarım istemesin). "Ek:" de girintisizdir (md. 18/1)."""
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn

    d = cizici.ac(resmi_docx)
    izgara = d.tables[0]
    assert izgara.alignment == WD_TABLE_ALIGNMENT.LEFT
    tblpr = izgara._tbl.tblPr
    girinti = tblpr.find(qn("w:tblInd"))
    assert girinti is not None and girinti.get(qn("w:w")) == "0"
    bosluk = tblpr.find(qn("w:tblCellMar"))
    assert bosluk is not None
    for kenar in ("w:left", "w:right"):
        oge = bosluk.find(qn(kenar))
        assert oge is not None and oge.get(qn("w:w")) == "0", kenar
    for satir in izgara.rows:
        for hucre in satir.cells:
            assert hucre._tc.tcPr is None or hucre._tc.tcPr.find(qn("w:tcMar")) is None
        bicim = satir.cells[0].paragraphs[0].paragraph_format
        assert not bicim.left_indent and not bicim.first_line_indent
    adlar = [oge.tag.rsplit("}", 1)[-1] for oge in tblpr]
    assert adlar.index("tblInd") < adlar.index("tblCellMar")
    for once, sonra in (("jc", "tblInd"), ("tblInd", "tblLayout"), ("tblCellMar", "tblLook")):
        if once in adlar and sonra in adlar:
            assert adlar.index(once) < adlar.index(sonra), (once, sonra)
    (ek,) = [p for p in d.paragraphs if p.text == "Ek:"]
    assert not ek.paragraph_format.left_indent and not ek.paragraph_format.first_line_indent


def _pdf_parca_konumlari(veri: bytes) -> list[tuple[str, float]]:
    """İlk sayfadaki metin parçalarının (metin, x) çiftleri, nokta biriminde. Konum, pypdf'in metin
    ziyaretçisindeki metin matrisinin (`tm`) dönüşüm matrisiyle (`cm`) çarpımıdır."""
    from pypdf import PdfReader

    parcalar: list[tuple[str, float]] = []

    def ziyaretci(metin: str, cm: Any, tm: Any, _tip: Any, _boyut: float) -> None:
        if metin.strip():
            parcalar.append((metin.strip(), tm[4] * cm[0] + tm[5] * cm[2] + cm[4]))

    PdfReader(io.BytesIO(veri)).pages[0].extract_text(visitor_text=ziyaretci)
    return parcalar


def test_resmi_yazi_pdf_yan_basliklar_yazi_alaninin_solundan(resmi_pdf: bytes) -> None:
    """Md. 11/2: PDF'te "Sayı" ve "Konu" satırları yazı alanının sol kenarından (sayfanın sol kenar
    boşluğu, 1,8 cm) başlar; "Ek:" de oradadır (md. 18/1). Uzun konunun devamı değer sütununun
    başındadır: yan başlık ve iki nokta sütunlarının (`RYUE_SUTUNLARI`) sağında (md. 13/1). pypdf aynı
    satırın parçalarını birleştirir; iki noktaların hizası düzen kipi testindedir (md. 15/3)."""
    parcalar = _pdf_parca_konumlari(resmi_pdf)
    pt_cm = 72 / 2.54
    sol = cizici.KENAR_CM["left"] * pt_cm

    def x(bas: str) -> float:
        (deger,) = [px for metin, px in parcalar if metin.startswith(bas)]
        return deger

    for bas in ("Sayı", "Konu", "Ek:"):
        assert x(bas) == pytest.approx(sol, abs=0.5), (bas, x(bas), sol)
    deger_sutunu = sol + sum(evrak.RYUE_SUTUNLARI[:2]) / 100 * cizici.YAZI_ALANI_CM * pt_cm
    (devam,) = [px for metin, px in parcalar if metin == "Kurulu"]
    assert devam == pytest.approx(deger_sutunu, abs=0.5)


def test_resmi_yazi_punto_alt_siniri(resmi_pdf: bytes, resmi_docx: bytes) -> None:
    """Resmî yazının bütün metni (sayı, konu, muhatap, ek) 12 puntodur; 9'un altında metin yoktur."""
    parcalar = pdf_yazi_boyutlari(resmi_pdf)
    kucukler = [(m, b) for _s, m, b in parcalar if b < cizici.EN_KUCUK_PUNTO]
    assert kucukler == []
    # pypdf satırın parçalarını birleştirir: "Sayı" ve "Konu" parçası iki noktayı ve değeri de taşır.
    for bas in ("Sayı", "Konu", "ÖRNEK İLÇE KAYMAKAMLIĞINA", "(İlçe", "Ek:", "1- ", "2- "):
        boyutlar = {b for _s, m, b in parcalar if m.startswith(bas)}
        assert boyutlar == {float(evrak.GOVDE_PUNTO)}, (bas, boyutlar)
    d = cizici.ac(resmi_docx)
    for tablo in d.tables:
        for satir in tablo.rows:
            for hucre in satir.cells:
                for p in hucre.paragraphs:
                    for run in p.runs:
                        assert run.font.size is None or run.font.size.pt >= cizici.EN_KUCUK_PUNTO


def test_muhatap_buyuk_harf_ve_birim_parantezde() -> None:
    """Md. 14/2: idarenin adı büyük harfle (Türkçe harf kuralıyla) saklanır; birim parantezsiz
    saklanır, alt satırda parantez içinde basılır."""
    blok = _resmi(muhatap="ığdır valiliğine", birim="İl Millî Eğitim Müdürlüğü")
    assert blok.muhatap == "IĞDIR VALİLİĞİNE"
    assert evrak.muhatap_satirlari(blok) == ("IĞDIR VALİLİĞİNE", "(İl Millî Eğitim Müdürlüğü)")
    assert evrak.muhatap_satirlari(_resmi()) == ("ÖRNEK İLÇE KAYMAKAMLIĞINA",)


@pytest.mark.parametrize(
    ("birim", "il", "ilce", "beklenen"),
    [
        (MEM_ILCE, "İzmir", "Çiğli", ("ÇİĞLİ KAYMAKAMLIĞINA", "İlçe Millî Eğitim Müdürlüğü")),
        (MEM_IL, "İzmir", "Çiğli", ("İZMİR VALİLİĞİNE", "İl Millî Eğitim Müdürlüğü")),
        (MEM_ILCE, "İzmir", "", ("…………… KAYMAKAMLIĞINA", "İlçe Millî Eğitim Müdürlüğü")),
        (MEM_IL, None, "Çiğli", ("…………… VALİLİĞİNE", "İl Millî Eğitim Müdürlüğü")),
    ],
)
def test_mem_muhatabi_s11_a(
    birim: str, il: str | None, ilce: str | None, beklenen: tuple[str, str]
) -> None:
    """Kullanıcı kararı S11 (a): RYUE md. 14/5 ana kuralı iki hâlde de — ilçe millî eğitim
    müdürlüğüne kaymakamlık, il millî eğitim müdürlüğüne valilik üzerinden; ad boşsa yer tutucu."""
    assert mem_muhatabi(birim, il=il, ilce=ilce) == beklenen


def test_mem_muhatabi_bilinmeyen_birimi_reddeder() -> None:
    with pytest.raises(ValueError, match="il ya da ilçe"):
        mem_muhatabi("Okul Müdürlüğü", il="İzmir", ilce="Çiğli")


@pytest.mark.parametrize(
    "alanlar",
    [
        {"sayi": " "},
        {"tarih": ""},
        {"konu": ""},
        {"muhatap": "  "},
        {"konu": "Uydurma Konu."},
        {"konu": "………"},
        *(
            {"konu": f"Uydurma Konu{isaret}"}
            for isaret in (")", "]", '"', "'", "’", "”", "»", "-", "—", "–", "/", "\\", "(", "!")
        ),
    ],
)
def test_resmi_yazi_eksik_ya_da_noktalamali_alani_reddeder(alanlar: dict[str, str]) -> None:
    """Md. 11/1: sayı zorunludur (bilinmiyorsa "………"); md. 13/1: konunun sonunda "herhangi bir
    noktalama işareti" yok — ayraçlar, tırnaklar, kesme, kısa ve uzun çizgi, eğik çizgi dahil. Konu
    yer tutucu olamaz ("…" de noktalamadır; plan F2 §7 U20 yer tutucuyu sayıya verir)."""
    with pytest.raises(ValueError):
        _resmi(**alanlar)


def test_resmi_yazi_belgenin_ilk_blogudur() -> None:
    """Md. 11/2: "Sayı:" başlığın (antedin) hemen altındadır; başka blok önüne geçemez."""
    with pytest.raises(ValueError, match="ilk bloğu"):
        evrak.Belge(kod="E12", antet=_antet(), bloklar=(evrak.Paragraf("Metin."), _resmi()))
    evrak.Belge(kod="E12", antet=_antet(), bloklar=(_resmi(), evrak.Paragraf("Metin.")))


# ============================================================ ek bölümü (RYUE md. 18)


def test_ek_satirlari_tek_ve_cok_ek() -> None:
    """Md. 18/2: tek ekte ibare "Ek:"in sağında; birden çok ekte altında numaralı."""
    assert evrak.ek_satirlari(evrak.Ekler(("Teslim tutanağı",))) == ("Ek: Teslim tutanağı",)
    assert evrak.ek_satirlari(evrak.Ekler(("A", "B"))) == ("Ek:", "1- A", "2- B")
    with pytest.raises(ValueError):
        evrak.Ekler(())
    with pytest.raises(ValueError):
        evrak.Ekler(("A", " "))


def test_ek_bolumu_imzadan_sonra_ve_tektir() -> None:
    """Md. 18/1: "Ek:" imza bölümünden sonra; programın sözleşmesi olarak imza bloğunun hemen
    ardından (aralarına başka blok girmez). Belgenin tek ek bölümü olur. Dipnot ekten sonra gelebilir
    (belgenin en sonu)."""
    ekler = evrak.Ekler(("Teslim tutanağı",))
    with pytest.raises(ValueError, match="imza bölümünden"):
        evrak.Belge(kod="E12", antet=_antet(), bloklar=(evrak.Paragraf("Metin."), ekler))
    with pytest.raises(ValueError, match="tek ek"):
        evrak.Belge(kod="E12", antet=_antet(), bloklar=(_imza(), ekler, _imza(), ekler))
    evrak.Belge(
        kod="E12",
        antet=_antet(),
        bloklar=(_imza(), ekler, evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)),
    )


# ============================================================ sayfa sonu (E08'in sınıf sayfaları)


@pytest.mark.parametrize("bloklar", ["ilk", "son", "art_arda"])
def test_sayfa_sonu_ilk_son_ya_da_art_arda_olamaz(bloklar: str) -> None:
    p = evrak.Paragraf("Metin.")
    s = evrak.SayfaSonu()
    diziler: dict[str, tuple[evrak.Blok, ...]] = {
        "ilk": (s, p),
        "son": (p, s),
        "art_arda": (p, s, s, p),
    }
    dizi = diziler[bloklar]
    with pytest.raises(ValueError, match="Sayfa sonu"):
        evrak.Belge(kod="E08", antet=_antet(), bloklar=dizi)


def test_sayfa_sonu_pdf_de_sonraki_sinifi_yeni_sayfaya_iter() -> None:
    """Sınıf başına sayfa (plan F2 §7 U16): 5-B ikinci sayfadadır; metin akışı iki çizicide aynıdır."""
    from pypdf import PdfReader

    belge = evrak.ornek_sayfali_belge()
    pdf = evrak.pdf_ciz(belge)
    sayfalar = [s.extract_text() or "" for s in PdfReader(io.BytesIO(pdf)).pages]
    assert len(sayfalar) == 2
    assert "Sınıf: 5-A" in sayfalar[0] and "5-B" not in sayfalar[0]
    assert "Sınıf: 5-B" in sayfalar[1]
    assert _bosluksuz(_ALTLIK.sub("", "\n".join(sayfalar))) == _bosluksuz(evrak.metin_akisi(belge))


def test_sayfa_sonu_word_de_sayfa_sonu_karakteridir() -> None:
    belge = evrak.ornek_sayfali_belge()
    veri = evrak.docx_ciz(belge)
    with zipfile.ZipFile(io.BytesIO(veri)) as arsiv:
        govde = arsiv.read("word/document.xml").decode("utf-8")
    assert govde.count('w:type="page"') == 1
    assert cizici.govde_metin_akisi(cizici.ac(veri)) == evrak.metin_akisi(belge)


@pytest.mark.parametrize("ad", ["resmi_yazi", "sayfali"])
def test_yeni_bloklar_kanonik_jsondan_ayni_modele_doner(ad: str) -> None:
    """Yeniden basım kayıtlı JSON'dan çizilir (tasarım §9.1-2): yeni bloklar da aynı özeti verir."""
    belge = ORNEKLER[ad]()
    json_metni = evrak.kanonik_json(belge)
    assert evrak.belge_coz(json_metni) == belge
    assert evrak.icerik_ozeti(evrak.belge_coz(json_metni)) == evrak.icerik_ozeti(belge)


def test_ekler_jsonda_metin_listesi_olmali(resmi: evrak.Belge) -> None:
    bozuk = evrak.kanonik_json(resmi).replace('"ekler":["Teslim', '"ekler":[1,"Teslim')
    with pytest.raises(evrak.BelgeCozulemedi):
        evrak.belge_coz(bozuk)


# ============================================================ Excel çizicisi


@pytest.mark.parametrize("ad", EXCEL_ORNEKLERI)
def test_xlsx_metin_akisi_modelle_ayni(ad: str) -> None:
    """Excel çıktısı aynı içerik modelinden çizilir: hücreler satır satır okununca modelin metin
    akışı çıkar (tek içerik; altlık hücrede değildir)."""
    belge = ORNEKLER[ad]()
    assert excel.metin_akisi(evrak.xlsx_ciz(belge)) == evrak.metin_akisi(belge)


def test_xlsx_sayfa_ayari_altlik_ve_sayfa_sonu() -> None:
    """A4 dikey, sayfa genişliğine sığdırılmış; altlık "OAB Defteri · <kod> · Sayfa &P/&N"; sınıf
    başına elle sayfa sonu; sayfa adı belgenin kodu."""
    kitap = excel.ac(evrak.xlsx_ciz(evrak.ornek_sayfali_belge()))
    sayfa = kitap.active
    assert sayfa.title == "DUMAN"
    assert str(sayfa.page_setup.paperSize) == str(sayfa.PAPERSIZE_A4)
    assert sayfa.page_setup.orientation == "portrait"
    assert sayfa.sheet_properties.pageSetUpPr.fitToPage is True
    assert sayfa.oddFooter.center.text == "OAB Defteri · DUMAN · Sayfa &P/&N"
    kesmeler = [kesme.id for kesme in sayfa.row_breaks.brk]
    assert len(kesmeler) == 1
    # Kesmeden sonraki ilk dolu satır ikinci sınıfın başlığıdır.
    sonraki = next(
        sayfa.cell(row=satir, column=1).value
        for satir in range(kesmeler[0] + 1, sayfa.max_row + 1)
        if sayfa.cell(row=satir, column=1).value
    )
    assert sonraki == "Sınıf: 5-B"


@pytest.mark.parametrize("ad", EXCEL_ORNEKLERI)
def test_xlsx_yazi_tipi_punto_ve_metin_degerler(ad: str) -> None:
    """Yazı tipi Times New Roman; 9 puntodan küçük metin yok (RYUE md. 7/1); dipnot ve konum cümlesi
    9, gövde 12, 5 sütunlu tablo 10; bütün değerler metin (sayıya çevrilmez)."""
    belge = ORNEKLER[ad]()
    sayfa = excel.ac(evrak.xlsx_ciz(belge)).active
    dolu = [h for satir in sayfa.iter_rows() for h in satir if h.value is not None]
    assert dolu
    assert {h.font.name for h in dolu} == {excel.YAZI_TIPI}
    assert min(h.font.size for h in dolu) >= excel.EN_KUCUK_PUNTO
    assert all(isinstance(h.value, str) for h in dolu)
    for blok in belge.bloklar:
        if isinstance(blok, evrak.Dipnot):
            assert {h.font.size for h in dolu if h.value == blok.metin} == {excel.DIPNOT_PUNTO}
        if isinstance(blok, evrak.Tablo):
            # Başlık hücresinin puntosu tablonun sütun sayısındandır (aynı adlı başlık iki tabloda olabilir).
            punto = evrak.tablo_punto(len(blok.basliklar))
            assert punto in {h.font.size for h in dolu if h.value == blok.basliklar[1]}


def test_xlsx_resmi_yaziyi_reddeder() -> None:
    """Resmî yazı Excel'e çizilmez: RYUE başının ızgarası (iki satır boşluklar, yan başlık ve iki nokta
    sütunu, konunun yazı alanının yarısında bitmesi) Excel sayfasının tablo ızgarasıyla birlikte
    korunamaz. F2'de Excel'i olan E08 ve E14 resmî yazı değildir; E12'nin biçimleri Word ve PDF'tir."""
    with pytest.raises(ValueError, match="Resmî yazı Excel'e çizilmez"):
        evrak.xlsx_ciz(evrak.ornek_resmi_yazi())


def test_xlsx_dokuz_puntodan_kucuk_yaziyi_reddeder() -> None:
    kitap = excel.Kitap("DUMAN", (100.0,))
    with pytest.raises(ValueError, match="9 puntodan"):
        kitap.paragraf("Uydurma.", punto=8)


# ============================================================ tek dosyalık web sayfası (E06)


class _Ayristirici(HTMLParser):
    """Web sayfasının etiketleri, öznitelikleri, biçemi ve gövde metni."""

    def __init__(self) -> None:
        super().__init__()
        self.etiketler: list[str] = []
        self.oznitelikler: list[tuple[str, str | None]] = []
        self.bicem: list[str] = []
        self.govde: list[str] = []
        self._yer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.etiketler.append(tag)
        self.oznitelikler += attrs
        if tag not in ("meta", "col", "hr", "br", "link", "img"):
            self._yer.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self._yer and self._yer[-1] == tag:
            self._yer.pop()

    def handle_data(self, data: str) -> None:
        if "style" in self._yer:
            self.bicem.append(data)
        elif "body" in self._yer and data.strip():
            self.govde.append(data)


def _ayristir(sayfa: str) -> _Ayristirici:
    a = _Ayristirici()
    a.feed(sayfa)
    a.close()
    return a


@pytest.mark.parametrize("ad", sorted(ORNEKLER))
def test_web_sayfasi_dis_kaynaksiz_tek_dosya(ad: str) -> None:
    """Tasarım §9.6 E06: "html tek dosya, dış bağlantısız". Sayfada bağlantı, betik, görsel, çerçeve,
    nesne ya da form yoktur; hiçbir öznitelik bir kaynağa (src, href, srcset, action, data, poster)
    işaret etmez; biçemde `url(` ve `@import` yoktur; sayfada adres şeması geçmez."""
    sayfa = evrak.web_html_ciz(ORNEKLER[ad]())
    a = _ayristir(sayfa)
    yasak_etiketler = {"link", "script", "img", "iframe", "object", "embed", "source", "video",
                       "audio", "form", "base", "picture", "svg"}  # fmt: skip
    assert set(a.etiketler) & yasak_etiketler == set()
    kaynaklar = {"src", "href", "srcset", "action", "data", "poster", "xlink:href", "formaction"}
    assert [ad_ for ad_, _ in a.oznitelikler if ad_ in kaynaklar] == []
    assert all(not ad_.startswith("on") for ad_, _ in a.oznitelikler)
    bicem = "".join(a.bicem)
    assert bicem and "url(" not in bicem and "@import" not in bicem
    assert not re.search(r"(https?|ftp|file|data):|//", sayfa)
    assert sayfa.startswith("<!DOCTYPE html>") and '<html lang="tr">' in sayfa
    assert '<meta charset="utf-8">' in sayfa
    assert "text-transform" not in sayfa


@pytest.mark.parametrize("ad", sorted(ORNEKLER))
def test_web_sayfasi_metni_modelle_ayni(ad: str) -> None:
    """Gövdenin metni modelin metin akışıdır (içerik eşdeğerliği); başlık yalnız `<title>`'da da durur."""
    belge = ORNEKLER[ad]()
    a = _ayristir(evrak.web_html_ciz(belge))
    assert _bosluksuz(a.govde) == _bosluksuz(evrak.metin_akisi(belge))


def test_web_sayfasi_metni_kacislidir() -> None:
    """Kayıttan gelen metin HTML olarak yorumlanmaz: `<script>` metni etikete dönüşmez."""
    belge = evrak.Belge(
        kod="E06",
        antet=_antet(),
        bloklar=(
            evrak.Baslik("genel kurul duyurusu"),
            evrak.Paragraf('Yer: <script>alert("x")</script> & "salon"'),
        ),
    )
    sayfa = evrak.web_html_ciz(belge)
    a = _ayristir(sayfa)
    assert "script" not in a.etiketler
    assert "&lt;script&gt;" in sayfa and "&amp;" in sayfa
    assert "<title>GENEL KURUL DUYURUSU</title>" in sayfa


# ============================================================ resmî yazının metni ve imzası (10. adım)


def test_metin_paragrafi_word_de_ilk_satir_girintili_ve_araliksiz(resmi_docx: bytes) -> None:
    """RYUE md. 16/4: paragrafa 1,25 cm içeriden başlanır, metin iki yana hizalanır, paragraflar
    arasında satır boşluğu bırakılmaz."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    belge = cizici.ac(resmi_docx)
    paragraflar = [
        p for p in belge.paragraphs if p.text.startswith(("Türkçe örnek", "Bilgileriniz"))
    ]
    assert len(paragraflar) == 2
    for p in paragraflar:
        bicim = p.paragraph_format
        assert bicim.first_line_indent is not None
        assert round(bicim.first_line_indent.cm, 2) == evrak.METIN_GIRINTISI_CM
        assert bicim.space_before == 0 and bicim.space_after == 0
        assert p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY


def test_metin_paragrafi_pdf_ve_web_sayfasinda_girintili(resmi: evrak.Belge) -> None:
    """PDF şablonu ve web sayfası aynı girintiyi çizer (1,25 cm, aralıksız)."""
    html = evrak.html_ciz(resmi)
    assert html.count('class="para-girintili"') == 2
    sayfa = evrak.web_html_ciz(resmi)
    assert sayfa.count('class="govde girintili"') == 2
    assert ".girintili{text-indent:1.25cm;margin:0}" in sayfa


@pytest.mark.parametrize("sayi", [1, 2])
def test_resmi_imza_tek_imza_sagda_iki_imzada_ust_unvan_sagda(sayi: int) -> None:
    """RYUE md. 17/1: tek imza yazı alanının en sağında ortalanır (sağ yarı hücre); md. 17/11: iki
    imzada üst unvan sağdadır (kurucu sahipleri soldan sağa verir). Word'de sol hücre tek imzada boştur;
    metin akışı iki çizicide aynıdır."""
    sahipler = (
        evrak.ImzaSahibi("Ayşe ÖRNEK", "Yönetim Kurulu adına Birlik Başkanı"),
        evrak.ImzaSahibi("İsmail DENEME", "Okul Müdürü"),
    )[-sayi:]
    imza = evrak.ResmiImza(sahipler=sahipler)
    sol, sag = evrak.resmi_imza_hucreleri(imza)
    assert sag == sahipler[-1] and (sol is None) is (sayi == 1)
    belge = evrak.Belge(
        kod="E12",
        antet=_antet(),
        bloklar=(_resmi(), evrak.MetinParagrafi("Arz ederim."), imza, evrak.Ekler(("Ek",))),
    )
    veri = evrak.docx_ciz(belge)
    tablo = cizici.ac(veri).tables[-1]
    hucreler = tablo.rows[0].cells
    assert len(hucreler) == 2 and "Okul Müdürü" in hucreler[1].text
    assert (hucreler[0].text.strip() == "") is (sayi == 1)
    assert cizici.govde_metin_akisi(cizici.ac(veri)) == evrak.metin_akisi(belge)
    pdf_metni = _pdf_metni(evrak.pdf_ciz(belge))
    assert _bosluksuz(_ALTLIK.sub("", pdf_metni)) == _bosluksuz(evrak.metin_akisi(belge))
    assert evrak.belge_coz(evrak.kanonik_json(belge)) == belge


@pytest.mark.parametrize("sayi", [0, 3])
def test_resmi_imza_bir_ya_da_iki_imza_tasir(sayi: int) -> None:
    """İkiden çok imza md. 17/11'in ikinci cümlesinin sıralamasıdır (onu gerektiren belgenin fazında);
    imzasız imza bölümü olmaz."""
    with pytest.raises(ValueError, match="bir ya da iki imza"):
        evrak.ResmiImza(sahipler=tuple(evrak.ImzaSahibi("A B", "Unvan") for _ in range(sayi)))


def test_tfb_tasarimdaki_metindir() -> None:
    """Tasarım §9.2 TFB (md. 23/5) BİREBİR; konum cümlesi kalıbıyla imzanın hemen üstünde durur."""
    belge = evrak.Belge(
        kod="E13",
        antet=_antet(),
        bloklar=(evrak.KonumCumlesi(evrak.TFB), _imza()),
    )
    assert evrak.metin_akisi(belge)[3:4] == [evrak.TFB]
    assert evrak.TFB.endswith("TEFBİS kaydının yerine geçmez.")
