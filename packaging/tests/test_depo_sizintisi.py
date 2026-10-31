"""`packaging/depo_sizintisi.py` — depo sızıntı kapısının davranış testleri.

Sağlamalı örnek numara ve IBAN ÇALIŞMA ANINDA üretilir, kaynağa düz yazılmaz:
aksi hâlde betik kendi test dosyasını tarayıp bulgu verirdi (kapı kendi kendini
kırardı) — ve deponun içinde gerçek biçimde duran bir numara, uydurma bile
olsa, tam olarak engellemeye çalıştığımız şeydir. Yasaklı ad testlerindeki ad
uydurmadır ve yalnız geçici dizine yazılan listede durur.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import depo_sizintisi  # noqa: E402


def _saglamali_numara(ilk_dokuz: str = "123456789") -> str:
    """TCKN sağlamasına UYAN uydurma numara üretir (son iki hane hesaplanır)."""
    hane = [int(k) for k in ilk_dokuz]
    tek = hane[0] + hane[2] + hane[4] + hane[6] + hane[8]
    cift = hane[1] + hane[3] + hane[5] + hane[7]
    onuncu = (tek * 7 - cift) % 10
    return f"{ilk_dokuz}{onuncu}{(sum(hane) + onuncu) % 10}"


def _saglamali_iban(bban: str = "0001200345678901234567") -> str:
    """mod-97 sağlamasına UYAN uydurma TR IBAN'ı (denetim haneleri hesaplanır).

    `bban`: 5 hane banka kodu + 1 ayrılmış hane + 16 hane hesap numarası.
    """
    sayi = int("".join(str(int(k, 36)) for k in bban + "TR00"))
    return f"TR{98 - sayi % 97:02d}{bban}"


def _gruplu(iban: str) -> str:
    """Bankaların yazımı: dörtlü gruplar, aralarında boşluk."""
    return " ".join(iban[i : i + 4] for i in range(0, len(iban), 4))


# --------------------------------------------------------------------------- #
# TCKN sağlaması
# --------------------------------------------------------------------------- #


def test_saglamali_numara_gecerli_sayilir() -> None:
    assert depo_sizintisi.tckn_gecerli_mi(_saglamali_numara()) is True


def test_github_kosu_numarasi_yanlis_pozitif_uretmez() -> None:
    """Çıplak `\\d{11}` deseni bu depoda koşu numaralarını yakalıyordu."""
    assert depo_sizintisi.tckn_gecerli_mi("33257833345") is False


@pytest.mark.parametrize("deger", ["0123456789", "01234567890", "1234567890", "abcdefghijk"])
def test_bicimsiz_degerler_elenir(deger: str) -> None:
    """Kısa/uzun, sıfırla başlayan ve rakam olmayan girdiler TCKN sayılmaz."""
    assert depo_sizintisi.tckn_gecerli_mi(deger) is False


# --------------------------------------------------------------------------- #
# Yol ve uzantı denetimi
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "yol",
    [
        "docs/liste.xls",
        "docs/LISTE.XLS",  # e-Okul ihraçları BÜYÜK harfli iner
        "bir/yer/ogrenciler.xlsx",
        "bir/yer/kayit.csv",
        "yedek/okul.odbak",
        "evrak/karar-ornegi.docx",  # doldurulmuş evrak (D9)
        "evrak/CETVEL.ODS",
        "backend/data/od.sqlite3",
        "backend/data/media/ek.txt",
        "media/ekran.txt",
    ],
)
def test_riskli_yollar_yakalanir(yol: str) -> None:
    assert depo_sizintisi.yol_riskli_mi(yol) is True


def test_sentetik_fixturelar_muaf() -> None:
    """Sentetik e-Okul örnekleri ADIYLA muaftır (joker kullanılmaz)."""
    for yol in depo_sizintisi.MUAF_YOLLAR:
        assert depo_sizintisi.yol_riskli_mi(yol) is False


@pytest.mark.parametrize("yol", ["backend/apps/okul/models.py", "README.md", "data/ornek.md"])
def test_masum_yollar_gecer(yol: str) -> None:
    assert depo_sizintisi.yol_riskli_mi(yol) is False


# --------------------------------------------------------------------------- #
# Uçtan uca: denetle() + main()
# --------------------------------------------------------------------------- #


def _depo_kur(tmp_path: Path, dosyalar: dict[str, str]) -> Path:
    for goreli, icerik in dosyalar.items():
        hedef = tmp_path / goreli
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(icerik, encoding="utf-8")
    return tmp_path


def test_metinde_gecen_numara_satiriyla_raporlanir(tmp_path: Path) -> None:
    numara = _saglamali_numara()
    kok = _depo_kur(tmp_path, {"docs/not.md": f"ilk satır\nöğrenci {numara} kaydı\n"})

    bulgular = depo_sizintisi.denetle(kok, ["docs/not.md"])

    assert bulgular.riskli == []
    assert bulgular.tckn == ["docs/not.md:2"]
    assert bulgular.iban == [] and bulgular.yasakli_ad == []


def test_ikili_ve_muaf_dosyalar_taranmaz(tmp_path: Path) -> None:
    numara = _saglamali_numara()
    kok = _depo_kur(
        tmp_path,
        {
            "frontend/package-lock.json": f'{{"hash": "{numara}"}}',
            "docs/kapak.pdf": f"%PDF sahte {numara}",
        },
    )

    bulgular = depo_sizintisi.denetle(kok, ["frontend/package-lock.json", "docs/kapak.pdf"])

    assert bulgular.tckn == []


def test_cikti_numaranin_kendisini_BASMAZ(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """KVKK: hata çıktısı da sızıntı kanalıdır — yalnız konum yazılır."""
    numara = _saglamali_numara()
    kok = _depo_kur(tmp_path, {"docs/not.md": f"öğrenci {numara}\n"})
    liste = tmp_path / "liste"
    liste.write_bytes(b"docs/not.md\0")

    kod = depo_sizintisi.main(["--kok", str(kok), "--liste", str(liste)])

    cikti = capsys.readouterr().out
    assert kod == 1
    assert "docs/not.md:1" in cikti
    assert numara not in cikti


def test_temiz_depo_sifir_doner(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    kok = _depo_kur(tmp_path, {"README.md": "# OAB Defteri\n"})
    liste = tmp_path / "liste"
    liste.write_bytes(b"README.md\0")

    kod = depo_sizintisi.main(["--kok", str(kok), "--liste", str(liste)])

    assert kod == 0
    assert "başarılı" in capsys.readouterr().out


def test_bos_liste_hata_verir(tmp_path: Path) -> None:
    """Liste üretilemediyse kapı SESSİZCE geçmez (fail-closed)."""
    liste = tmp_path / "liste"
    liste.write_bytes(b"")

    assert depo_sizintisi.main(["--kok", str(tmp_path), "--liste", str(liste)]) == 2


# --------------------------------------------------------------------------- #
# IBAN (TR + 24 hane, mod-97) — tasarım §13 D9
# --------------------------------------------------------------------------- #


def test_saglamali_iban_gecerli_sayilir() -> None:
    iban = _saglamali_iban()
    assert depo_sizintisi.iban_gecerli_mi(iban) is True
    assert depo_sizintisi.iban_gecerli_mi(_gruplu(iban)) is True
    assert depo_sizintisi.iban_gecerli_mi(iban.lower()) is True


def test_saglamasi_bozuk_ya_da_bicimsiz_iban_elenir() -> None:
    iban = _saglamali_iban()
    bozuk = f"TR{(int(iban[2:4]) + 1) % 100:02d}{iban[4:]}"
    assert depo_sizintisi.iban_gecerli_mi(bozuk) is False
    assert depo_sizintisi.iban_gecerli_mi(iban[:-1]) is False  # 25 karakter
    assert depo_sizintisi.iban_gecerli_mi(f"DE{iban[2:]}") is False  # yalnız TR aranır


def test_metindeki_iban_satiriyla_raporlanir(tmp_path: Path) -> None:
    """Dörtlü gruplarla yazılmış IBAN da bulunur; rastgele 24 hane bulgu değildir."""
    iban = _saglamali_iban()
    bozuk = f"TR{(int(iban[2:4]) + 1) % 100:02d}{iban[4:]}"
    kok = _depo_kur(
        tmp_path,
        {
            "docs/odeme.md": f"talimat\nalıcı hesabı: {_gruplu(iban)}\n",
            "docs/rastgele.md": f"kod {bozuk}\n",
        },
    )

    bulgular = depo_sizintisi.denetle(kok, ["docs/odeme.md", "docs/rastgele.md"])

    assert bulgular.iban == ["docs/odeme.md:2"]
    assert bulgular.tckn == []


def test_cikti_ibanin_kendisini_BASMAZ(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    iban = _saglamali_iban()
    kok = _depo_kur(tmp_path, {"docs/ozet.md": f"{iban}\n"})
    liste = tmp_path / "liste"
    liste.write_bytes(b"docs/ozet.md\0")

    kod = depo_sizintisi.main(["--kok", str(kok), "--liste", str(liste)])

    cikti = capsys.readouterr().out
    assert kod == 1
    assert "IBAN olabilecek değer: docs/ozet.md:1" in cikti
    assert iban[4:] not in cikti


# --------------------------------------------------------------------------- #
# Depo dışındaki yasaklı adlar listesi — tasarım §13 D42
# --------------------------------------------------------------------------- #

#: Uydurma ad: gerçek hiçbir firmaya ya da kişiye ait değildir.
_UYDURMA_AD = "Kuzgunkaya Örnek Taşımacılık"


def test_yasakli_ad_listesi_yoksa_tarama_atlanir_ve_kapi_gecer(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    kok = _depo_kur(tmp_path, {"README.md": f"# {_UYDURMA_AD}\n"})
    liste = tmp_path / "liste"
    liste.write_bytes(b"README.md\0")

    kod = depo_sizintisi.main(["--kok", str(kok), "--liste", str(liste)])

    cikti = capsys.readouterr().out
    assert kod == 0
    assert "yasaklı ad taraması atlandı" in cikti
    assert depo_sizintisi.YASAKLI_ADLAR_DOSYASI in cikti


def test_yasakli_ad_katlanmis_metinde_bulunur_ve_basilmaz(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Büyük harfli Türkçe yazım ("İ"/"I") ve fazladan boşluk adı gizlemez."""
    kok = _depo_kur(
        tmp_path,
        {
            "docs/servis.md": "giriş\nTaşımacı: KUZGUNKAYA   ÖRNEK TAŞIMACILIK\n",
            "docs/temiz.md": "taşımacının tespiti\n",
            depo_sizintisi.YASAKLI_ADLAR_DOSYASI: f"# yorum satırı\n\n{_UYDURMA_AD}\n",
        },
    )
    liste = tmp_path / "liste"
    liste.write_bytes(b"docs/servis.md\0docs/temiz.md\0")

    kod = depo_sizintisi.main(["--kok", str(kok), "--liste", str(liste)])

    cikti = capsys.readouterr().out
    assert kod == 1
    assert "yasaklı listedeki bir ad: docs/servis.md:2" in cikti
    assert "docs/temiz.md" not in cikti
    assert "kuzgunkaya" not in cikti.casefold()
    assert "atlandı" not in cikti


def test_yasakli_adlar_dosyasi_yorum_ve_bos_satiri_atlar(tmp_path: Path) -> None:
    dosya = tmp_path / "adlar.txt"
    dosya.write_text(f"# yorum\n\n  {_UYDURMA_AD}  \nIŞIK\n", encoding="utf-8")

    assert depo_sizintisi.yasakli_adlari_oku(dosya) == [
        "kuzgunkaya örnek taşimacilik",
        "işik",
    ]
    assert depo_sizintisi.yasakli_adlari_oku(tmp_path / "yok.txt") is None
