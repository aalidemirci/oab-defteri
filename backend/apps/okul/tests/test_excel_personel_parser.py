"""apps.okul.excel_personel — SADELEŞMİŞ personel parser testleri.

Aile şablonundan fark: e-posta ve Rol/Kapsam çiftleri YOK — personel hesabı yoktur.
Unvan ve branş SAKLANMAZ ve OKUNMAZ (tasarım §8.4). e-Okul'un "Görevi" sütunu ve şablonun
"Görev Türü" sütunu yalnız görev türüne (öğretmen · yönetici · diğer personel; plan "F1b-5
uygulama kararları") çevrilir, metni satır nesnesine girmez. Adlar uydurmadır.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook

from apps.okul import excel_personel
from apps.okul.excel_ortak import ParserError
from apps.okul.models import MemberKind

STANDARD_HEADER = ["Ad Soyad", "Görevi", "Branş"]


def make_xlsx(
    rows: list[list[object]],
    header: list[object] | None = None,
    preamble: list[list[object]] | None = None,
) -> bytes:
    """Bellekte bir .xlsx üretir (header + satırlar)."""
    wb = Workbook()
    ws = wb.active
    for pre in preamble or []:
        ws.append(pre)
    ws.append(header if header is not None else STANDARD_HEADER)
    for r in rows:
        ws.append(r)
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


def test_tur_sabitleri_model_degerleriyle_ayni() -> None:
    """Modül Django'suz kalsın diye düz metin tutar; model değerleriyle eşit olmalı."""
    assert (
        excel_personel.KIND_OGRETMEN,
        excel_personel.KIND_YONETICI,
        excel_personel.KIND_DIGER,
    ) == (MemberKind.OGRETMEN.value, MemberKind.YONETICI.value, MemberKind.DIGER.value)
    assert set(MemberKind.values) == {"OGRETMEN", "YONETICI", "DIGER"}


def test_standart_basliklar_eslenir_brans_eslenmez() -> None:
    grid = excel_personel.read_sheet(make_xlsx([]))
    mapping = excel_personel.detect_columns(grid)
    assert mapping.is_usable
    assert mapping.fields == {"full_name": 0, "role": 1}


def test_unvan_sutunu_okunmaz() -> None:
    """Tasarım §8.4 okunmayanlar: "Unvan" eşleme sözlüğünde yoktur, tür ondan çıkmaz."""
    assert not any("unvan" in kw for kws in excel_personel.COLUMN_SYNONYMS.values() for kw in kws)
    data = make_xlsx([["ALİ ÖRNEK", "Müdür", "Öğretmen"]], header=["Ad Soyad", "Unvanı", "Unvan"])
    mapping, parsed = excel_personel.parse_workbook(data)
    assert mapping.fields == {"full_name": 0}
    assert (parsed[0].member_kind, parsed[0].member_kind_unrecognized) == (None, False)


def test_fuzzy_baslik_varyasyonlari() -> None:
    header: list[object] = ["Adı Soyadı", "Görevi", "Alan", "Branşı"]
    grid = excel_personel.read_sheet(make_xlsx([], header=header))
    mapping = excel_personel.detect_columns(grid)
    assert mapping.is_usable
    assert mapping.fields == {"full_name": 0, "role": 1}


@pytest.mark.parametrize(
    ("deger", "beklenen"),
    [
        ("Öğretmen", MemberKind.OGRETMEN),
        ("ÖĞRETMEN", MemberKind.OGRETMEN),
        ("Yönetici", MemberKind.YONETICI),
        ("  YÖNETİCİ ", MemberKind.YONETICI),
        ("Diğer personel", MemberKind.DIGER),
        ("DİĞER  PERSONEL", MemberKind.DIGER),
        ("Diğer", MemberKind.DIGER),
    ],
)
def test_sablonun_gorev_turu_sutunu_uc_degeri_kabul_eder(deger: str, beklenen: str) -> None:
    header: list[object] = ["Adı", "Soyadı", "Görev Türü"]
    data = make_xlsx([["ALİ", "ÖRNEK", deger]], header=header)
    mapping, parsed = excel_personel.parse_workbook(data)
    assert mapping.fields == {"first_name": 0, "last_name": 1, "kind": 2}
    assert (parsed[0].first_name, parsed[0].last_name) == ("ALİ", "ÖRNEK")
    assert parsed[0].member_kind == beklenen
    assert parsed[0].member_kind_unrecognized is False


@pytest.mark.parametrize("deger", ["Müdür", "Memur", "öğretmenler", "", None])
def test_sablonun_taninmayan_gorev_turu_tahmin_edilmez(deger: object) -> None:
    """Şablon sütununda üç etiket dışındaki değer türe çevrilmez: denetim uyarısı düşer."""
    header: list[object] = ["Adı", "Soyadı", "Görev Türü"]
    data = make_xlsx([["ALİ", "ÖRNEK", deger]], header=header)
    _mapping, parsed = excel_personel.parse_workbook(data)
    assert (parsed[0].member_kind, parsed[0].member_kind_unrecognized) == (None, True)


def test_eski_sablonun_uye_turu_basligi_da_okunur() -> None:
    """5. adımdan önce indirilmiş şablonun "Üye Türü" başlığı görev türü sütunu sayılır."""
    header: list[object] = ["Adı", "Soyadı", "Üye Türü"]
    data = make_xlsx([["ALİ", "ÖRNEK", "Diğer personel"]], header=header)
    mapping, parsed = excel_personel.parse_workbook(data)
    assert "kind" in mapping.fields
    assert parsed[0].member_kind == MemberKind.DIGER


def test_satirda_gorev_ve_brans_metni_tutulmaz() -> None:
    header: list[object] = ["Adı", "Soyadı", "Görevi", "Branşı"]
    data = make_xlsx([["ALİ", "ÖRNEK", "Müdür", "Matematik"]], header=header)
    _mapping, parsed = excel_personel.parse_workbook(data)
    assert set(vars(parsed[0])) == {
        "row_number",
        "raw_full_name",
        "first_name",
        "last_name",
        "member_kind",
        "member_kind_unrecognized",
        "member_kind_uncertain",
    }
    assert "Müdür" not in repr(parsed[0]) and "Matematik" not in repr(parsed[0])


def test_yalniz_ad_soyad_da_yeterli_tur_bilgisi_yok() -> None:
    """Görev sütunsuz düz isim listesi kabul edilir; tür bilgisi yok, uyarı da yok."""
    _mapping, parsed = excel_personel.parse_workbook(
        make_xlsx([["ALİ ÖRNEK"]], header=["Ad Soyad"])
    )
    assert parsed[0].member_kind is None
    assert parsed[0].member_kind_unrecognized is False


def test_ad_soyad_yoksa_parser_error() -> None:
    data = make_xlsx([["Müdür", "Matematik"]], header=["Görevi", "Branş"])
    with pytest.raises(ParserError) as hata:
        excel_personel.parse_workbook(data)
    # İleti Türkçe sütun adlarını anar; iç alan anahtarı (`full_name`) sızmaz.
    assert str(hata.value) == (
        "Zorunlu sütun bulunamadı: “Adı Soyadı” (ya da ayrı “Adı” ve “Soyadı”)."
    )
    assert "full_name" not in str(hata.value)


def test_satir_ayristirma() -> None:
    rows: list[list[object]] = [
        ["ALİ ÖRNEK", "Müdür", "Matematik"],
        ["AYŞE ÖĞRETMEN", "", "Matematik"],
    ]
    _mapping, parsed = excel_personel.parse_workbook(make_xlsx(rows))
    assert len(parsed) == 2
    assert (parsed[0].first_name, parsed[0].last_name) == ("ALİ", "ÖRNEK")
    assert parsed[0].member_kind == MemberKind.YONETICI
    # Görev sütunu VAR ama hücre boş: tür çıkarılamadı → önizlemede denetim uyarısı.
    assert (parsed[1].member_kind, parsed[1].member_kind_unrecognized) == (None, True)


def test_bos_satir_atlanir() -> None:
    rows: list[list[object]] = [
        ["ALİ ÖRNEK", "Müdür", "Matematik"],
        [None, None, None],
    ]
    _mapping, parsed = excel_personel.parse_workbook(make_xlsx(rows))
    assert len(parsed) == 1


def test_preamble_atlanir() -> None:
    preamble: list[list[object]] = [["PERSONEL LİSTESİ"], []]
    grid = excel_personel.read_sheet(make_xlsx([], preamble=preamble))
    mapping = excel_personel.detect_columns(grid)
    assert mapping.header_row == 2
    assert mapping.is_usable


@pytest.mark.parametrize(
    ("gorev", "beklenen"),
    [
        # Yönetici: üç görev, Türkçe katlanmış TAM eşleşme (büyük/küçük harf, boşluk önemsiz).
        ("Müdür", "YONETICI"),
        ("MÜDÜR", "YONETICI"),
        ("müdür", "YONETICI"),
        ("Müdür Yardımcısı", "YONETICI"),
        ("MÜDÜR YARDIMCISI", "YONETICI"),
        ("müdür yardımcısı", "YONETICI"),
        ("  Müdür   Yardımcısı  ", "YONETICI"),
        ("Müdür\tYardımcısı", "YONETICI"),
        ("Müdür Başyardımcısı", "YONETICI"),
        ("MÜDÜR BAŞYARDIMCISI", "YONETICI"),
        # Tam eşleşme değil: içinde "öğretmen" yoksa diğer personel.
        ("Müdür Yrd.", "DIGER"),
        ("Okul Müdürü", "DIGER"),
        ("Müdür Yardımcısı Vekili", "DIGER"),
        # İçinde "öğretmen" geçen görev öğretmendir.
        ("Öğretmen", "OGRETMEN"),
        ("ÖĞRETMEN", "OGRETMEN"),
        ("öğretmen", "OGRETMEN"),
        ("Sözleşmeli Öğretmen(657 S.K. 4/B)", "OGRETMEN"),
        ("Ücretli Öğretmen", "OGRETMEN"),
        ("ÜCRETLİ ÖĞRETMEN", "OGRETMEN"),
        ("Rehber Öğretmen", "OGRETMEN"),
        ("Uzman Öğretmen", "OGRETMEN"),
        ("Usta Öğreticiler Öğretmeni", "OGRETMEN"),
        # Öteki her görev diğer personeldir.
        ("Psikolojik Danışman", "DIGER"),
        ("Usta Öğretici", "DIGER"),
        ("MEMUR", "DIGER"),
        ("Ambar Memuru", "DIGER"),
        ("Hizmetli", "DIGER"),
        ("Yardımcı Hizmetli", "DIGER"),
        ("Teknisyen", "DIGER"),
        ("Aşçı", "DIGER"),
        ("Şoför", "DIGER"),
        ("Sürekli İşçi", "DIGER"),
        ("Veri Hazırlama ve Kontrol İşletmeni", "DIGER"),
        ("Uzman Kaptan", "DIGER"),
        # Boş hücre: tür çıkmaz (çağıran uyarır).
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_gorev_siniflamasi(gorev: object, beklenen: str | None) -> None:
    assert excel_personel.classify_member_kind(gorev) == beklenen


@pytest.mark.parametrize(
    ("gorev", "tur"),
    [
        # Yönetici ya da öğretmen görevine benzeyip tam eşleşmeye uymayanlar: sınıflama aynı kalır
        # (kullanıcı kararı harfiyen), yalnız denetim uyarısı verilir.
        ("Okul Müdürü", "DIGER"),
        ("Müdür Yrd.", "DIGER"),
        ("MÜDÜR YRD.", "DIGER"),
        ("Müdür Yardımcısı Vekili", "DIGER"),
        ("Müdür Vekili", "DIGER"),
        ("Psikolojik Danışman", "DIGER"),
        ("Usta Öğretici", "DIGER"),
    ],
)
def test_supheli_gorev_siniflamayi_degistirmeden_denetim_ister(gorev: str, tur: str) -> None:
    assert excel_personel.classify_member_kind(gorev) == tur
    assert excel_personel.gorev_denetlenmeli(gorev) is True


@pytest.mark.parametrize(
    "gorev",
    [
        "Müdür",
        "MÜDÜR",
        "Müdür Yardımcısı",
        "  müdür   yardımcısı ",
        "Müdür Başyardımcısı",
        "Öğretmen",
        "Ücretli Öğretmen",
        "Rehber Öğretmen",
        # İçinde "öğretmen" geçen görev kesindir (kullanıcı kararı); "danışman" geçse de denetim istemez.
        "Rehber Öğretmen (Psikolojik Danışman)",
        "Usta Öğreticiler Öğretmeni",
        "Memur",
        "Hizmetli",
        "Teknisyen",
        "",
        None,
    ],
)
def test_tam_taninan_ya_da_benzemeyen_gorev_denetim_istemez(gorev: object) -> None:
    assert excel_personel.gorev_denetlenmeli(gorev) is False


def test_supheli_gorev_satirda_uyari_bayragi_tasir_tur_yine_verilir() -> None:
    rows: list[list[object]] = [
        ["ALİ ÖRNEK", "Okul Müdürü", ""],
        ["AYŞE ÖRNEK", "Müdür", ""],
        ["CEM ÖRNEK", "", ""],
    ]
    _mapping, parsed = excel_personel.parse_workbook(make_xlsx(rows))
    assert [
        (p.member_kind, p.member_kind_unrecognized, p.member_kind_uncertain) for p in parsed
    ] == [
        (MemberKind.DIGER, False, True),
        (MemberKind.YONETICI, False, False),
        (None, True, False),
    ]
    assert "Okul Müdürü" not in repr(parsed[0])


def test_sablonun_gorev_turu_sutunu_denetim_bayragi_vermez() -> None:
    """Şüpheli görev denetimi yalnız e-Okul'un "Görevi" metnindedir; şablonun üç etiketi kesindir."""
    data = make_xlsx([["ALİ", "ÖRNEK", "Yönetici"]], header=["Adı", "Soyadı", "Görev Türü"])
    _mapping, parsed = excel_personel.parse_workbook(data)
    assert (parsed[0].member_kind, parsed[0].member_kind_uncertain) == (MemberKind.YONETICI, False)


def test_yinelenen_baslik_uyarisi_turkce_alan_adiyla_yazilir() -> None:
    grid = excel_personel.read_sheet(
        make_xlsx([["ALİ ÖRNEK", "Müdür", "Öğretmen"]], header=["Ad Soyad", "Görevi", "Görev"])
    )
    mapping = excel_personel.detect_columns(grid)
    assert mapping.warnings == [
        "“Görev” sütunu da “Görevi” alanına uyuyor; ilk uyan sütun kullanıldı, bu sütun okunmadı."
    ]
