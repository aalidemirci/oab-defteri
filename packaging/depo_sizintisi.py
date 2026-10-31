"""Depoya kişisel veri girmediğini doğrula — `veri_sizintisi.py`'nin depo eşi.

`veri_sizintisi.py` DAĞITIM PAKETİNİ denetler; bu betik aynı soruyu depo için
sorar: git'in izlediği dosyalar arasında öğrenci/personel/veli verisi ya da
birliğin mali kaydı taşıyabilecek bir şey var mı? `.gitignore` bunu ÖNLER ama
denetlemez — `git add -f` ile zorlanan, listede olmayan bir uzantıyla giren
(`.csv`) ya da bir markdown'a yapıştırılmış gerçek bir numara sessizce depoya
girer ve bir kez girdiyse `.gitignore` onu geçmişten çıkarmaz.

Dört denetim var:

1. **Yol/uzantı** — veri dosyası biçimleri (doldurulmuş evrak `.docx`/`.ods`
   ve programın yedeği `.odbak` dahil) ve gerçek verinin yaşadığı dizinler.
   Sentetik test fixture'ları ve programın evrak şablonları AÇIK LİSTEYLE
   muaftır; joker kullanılmaz, çünkü `veri/*.xls` deseni o klasöre bırakılan
   GERÇEK bir e-Okul ihracını da muaf tutardı (`.gitignore` içindeki aynı
   gerekçe).
2. **T.C. kimlik numarası** — 11 haneli her sayı değil, TCKN'nin kendi
   sağlama kuralına UYAN sayılar aranır. Çıplak `\\d{11}` deseni bu depoda
   GitHub Actions koşu numaralarını (ör. 33257833345) yakalıyordu; sağlama
   kuralı yanlış pozitifleri ~%99 eler.
3. **IBAN** — `TR` + 24 hane (dörtlü gruplar arasında boşluk olabilir), ISO
   13616 mod-97 sağlamasına UYANLAR (tasarım §4.3 tehdit 17, §13 D9). Banka
   hesap özeti, ödeme talimatı ya da bir belgeye yapıştırılmış hesap numarası
   bu yolla yakalanır; birliğin kurumsal IBAN'ı kişisel veri olmasa da depoya
   girmez (gerçek kayıt, sentetik değil).
4. **Yasaklı adlar** — depo DIŞINDAKİ, `.gitignore`'lu `.od-yasakli-adlar.txt`
   dosyasındaki gerçek adlar (ör. taşımacı firma) katlanmış metinde aranır
   (tasarım §13 D42). Adların kendisi depoya hiçbir biçimde girmez; dosya
   yoksa tarama atlanır ve kapı UYARIYLA geçer. CI'da liste depo sırrından iş
   başında bu dosyaya yazılır (sırrın tanımı yayın işidir, altın kural 8).

Çıktı KİŞİSEL VERİ İÇERMEZ: bulgu satırında yalnız dosya yolu ve satır numarası
yazılır, eşleşen sayı ya da adın kendisi asla basılmaz (veri_sizintisi.py'deki
aynı ilke — hata çıktısı da sızıntı kanalıdır).

Kullanım (dosya listesi NUL ayraçlıdır; `git ls-files -z` çıktısı):

    git ls-files -z > liste
    python packaging/depo_sizintisi.py --kok . --liste liste
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import NamedTuple

#: Kişisel veri taşıyan dosya biçimleri. e-Okul ihraçları BÜYÜK harfli `.XLS`
#: iner; karşılaştırma casefold ile yapılır. `.docx`/`.ods`: doldurulmuş ya da
#: imzalı evrak (karar örneği, katılım cetveli); programın şablonları F1a-3'ten
#: itibaren `MUAF_YOLLAR`'a ADIYLA yazılır (tasarım §13 D9). Küme paket kapısının
#: `veri_sizintisi.YASAK_UZANTILAR` kümesiyle AYNIDIR (eşitliği test sınar).
RISKLI_UZANTILAR = frozenset(
    {
        ".xls",
        ".xlsx",
        ".xlsm",
        ".csv",
        ".sqlite",
        ".sqlite3",
        ".db",
        ".odbak",
        ".docx",
        ".ods",
    }
)

#: Gerçek verinin yaşadığı dizinler (`.gitignore` ile aynı liste).
RISKLI_DIZIN_ONEKLERI = ("backend/data/", "data/raw/", "media/")

#: Sentetik fixture'lar ve programın şablonları — adları TEK TEK yazılır (joker
#: YOK; docstring'e bakın).
MUAF_YOLLAR = frozenset(
    {
        "backend/apps/okul/tests/veri/eokul_personel_listesi.xls",
    }
)

#: İçerik taramalarından (TCKN, IBAN, yasaklı ad) muaf dosyalar: üretilmiş
#: kilit/özet dosyaları uzun rakam dizileri taşır ve elle yazılmadıkları için
#: kişisel veri kanalı değildirler.
ICERIK_MUAF_YOLLAR = frozenset({"frontend/package-lock.json", "coverage.xml"})

#: Metin sayılmayan uzantılar — içerik taraması yalnız metinde anlamlıdır.
IKILI_UZANTILAR = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".pdf",
        ".zip",
        ".gz",
        ".xls",
        ".xlsx",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".exe",
        ".dll",
        ".deb",
    }
)

#: 1 MB üstü metin dosyası taranmaz (üretilmiş dosyalar; maliyet/fayda).
AZAMI_TARAMA_BAYTI = 1_048_576

#: Depo kökündeki yasaklı adlar listesi (`.gitignore`'da; tasarım §13 D42).
YASAKLI_ADLAR_DOSYASI = ".od-yasakli-adlar.txt"

_ONBIR_HANE = re.compile(r"(?<!\d)\d{11}(?!\d)")
#: TR IBAN'ı: ülke kodu + 2 denetim hanesi + 5 banka kodu + 1 ayrılmış hane + 16
#: hesap hanesi = "TR" + 24 hane. Bankalar dörtlü gruplarla yazar; her haneden
#: önce tek boşluğa izin verilir. Öncesinde harf/rakam, sonrasında rakam olamaz.
_IBAN = re.compile(r"(?<![0-9A-Za-z])TR(?: ?\d){24}(?!\d)", re.IGNORECASE)
#: Türkçe katlama: "İ", "I" ve "ı" üçü de "i" olur (kimlik kalıntısı taramasıyla
#: aynı kural); ardından casefold. Büyük harfle yazılmış ad da yakalanır.
_TR_KATLAMA = str.maketrans({"İ": "i", "I": "i", "ı": "i", "̇": None})


class Bulgular(NamedTuple):
    """Denetim sonucu; konumlar 'yol:satır' biçimindedir (değerler DEĞİL)."""

    riskli: list[str]
    tckn: list[str]
    iban: list[str]
    yasakli_ad: list[str]


def tckn_gecerli_mi(deger: str) -> bool:
    """T.C. kimlik numarası sağlama kuralı (MERNİS): rastgele sayıyı eler.

    Kural: 11 hane · ilk hane 0 olamaz · 10. hane
    ``((tek basamaklar toplamı × 7) − çift basamaklar toplamı) mod 10`` ·
    11. hane ilk on basamağın toplamının mod 10'u.
    """
    if len(deger) != 11 or not deger.isdigit() or deger[0] == "0":
        return False
    hane = [int(k) for k in deger]
    tek = hane[0] + hane[2] + hane[4] + hane[6] + hane[8]
    cift = hane[1] + hane[3] + hane[5] + hane[7]
    if (tek * 7 - cift) % 10 != hane[9]:
        return False
    return sum(hane[:10]) % 10 == hane[10]


def iban_gecerli_mi(deger: str) -> bool:
    """TR IBAN'ı ISO 13616 mod-97 sağlamasına uyuyor mu?

    Boşluklar atılır; ilk dört karakter (ülke kodu + denetim haneleri) sona alınır,
    harfler sayıya çevrilir (A=10 … Z=35) ve elde edilen sayının 97'ye bölümünden
    kalan 1 olmalıdır. Rastgele 24 hanenin ~%99'u elenir.
    """
    yalin = deger.replace(" ", "").upper()
    if len(yalin) != 26 or not yalin.startswith("TR") or not yalin[2:].isdigit():
        return False
    dizi = yalin[4:] + yalin[:4]
    return int("".join(str(int(k, 36)) for k in dizi)) % 97 == 1


def katla(metin: str) -> str:
    """Türkçe katlama + casefold + boşluk düzleme (yasaklı ad araması için)."""
    return " ".join(metin.translate(_TR_KATLAMA).casefold().split())


def yasakli_adlari_oku(dosya: Path) -> list[str] | None:
    """Listedeki adlar KATLANMIŞ olarak; dosya yoksa None.

    Satır başına bir ad; boş satırlar ve `#` ile başlayan satırlar yok sayılır.
    """
    if not dosya.is_file():
        return None
    adlar: list[str] = []
    for satir in dosya.read_text(encoding="utf-8-sig").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#"):
            adlar.append(katla(satir))
    return adlar


def yol_riskli_mi(goreli_yol: str) -> bool:
    """Dosya yolu, biçimi ya da bulunduğu dizin yüzünden riskli mi?"""
    if goreli_yol in MUAF_YOLLAR:
        return False
    if goreli_yol.startswith(RISKLI_DIZIN_ONEKLERI):
        return True
    return Path(goreli_yol).suffix.casefold() in RISKLI_UZANTILAR


def metin_satirlari(kok: Path, goreli_yol: str) -> list[str]:
    """İçerik taramasına girecek satırlar; muaf, ikili, büyük ya da okunamayan dosyada boş."""
    if goreli_yol in ICERIK_MUAF_YOLLAR:
        return []
    if Path(goreli_yol).suffix.casefold() in IKILI_UZANTILAR:
        return []
    tam_yol = kok / goreli_yol
    try:
        if not tam_yol.is_file() or tam_yol.stat().st_size > AZAMI_TARAMA_BAYTI:
            return []
        icerik = tam_yol.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # Okunamayan ya da metin olmayan dosya: yol denetimi zaten kapsıyor.
        return []
    return icerik.splitlines()


def tckn_satirlari(kok: Path, goreli_yol: str) -> list[int]:
    """Dosyada TCKN sağlamasına uyan sayıların SATIR numaraları (değerler DEĞİL)."""
    return [
        no
        for no, satir in enumerate(metin_satirlari(kok, goreli_yol), start=1)
        if any(tckn_gecerli_mi(m.group()) for m in _ONBIR_HANE.finditer(satir))
    ]


def denetle(kok: Path, yollar: Iterable[str], yasakli_adlar: Sequence[str] = ()) -> Bulgular:
    """Riskli yollar ile TCKN, IBAN ve yasaklı ad bulgularının konumları.

    `yasakli_adlar` KATLANMIŞ adlardır (`yasakli_adlari_oku`).
    """
    bulgular = Bulgular([], [], [], [])
    for goreli_yol in sorted(set(yollar)):
        if not goreli_yol:
            continue
        if yol_riskli_mi(goreli_yol):
            bulgular.riskli.append(goreli_yol)
            continue  # dosyayı ayrıca içerik için açmaya gerek yok
        for no, satir in enumerate(metin_satirlari(kok, goreli_yol), start=1):
            konum = f"{goreli_yol}:{no}"
            if any(tckn_gecerli_mi(m.group()) for m in _ONBIR_HANE.finditer(satir)):
                bulgular.tckn.append(konum)
            if any(iban_gecerli_mi(m.group()) for m in _IBAN.finditer(satir)):
                bulgular.iban.append(konum)
            if yasakli_adlar:
                katli = katla(satir)
                if any(ad in katli for ad in yasakli_adlar):
                    bulgular.yasakli_ad.append(konum)
    return bulgular


def liste_oku(liste_yolu: Path) -> list[str]:
    """`git ls-files -z` çıktısını okur (NUL ayraçlı)."""
    ham = liste_yolu.read_bytes().decode("utf-8", errors="surrogateescape")
    return [parca for parca in ham.split("\0") if parca]


def argumanlari_ayristir(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Depoya kişisel veri girmediğini denetler (git izlenen dosyalar)."
    )
    parser.add_argument("--kok", type=Path, default=Path("."), help="Depo kökü")
    parser.add_argument(
        "--liste",
        type=Path,
        required=True,
        help="`git ls-files -z` çıktısını taşıyan dosya (konteynerde git yoktur)",
    )
    parser.add_argument(
        "--yasakli-adlar",
        type=Path,
        default=None,
        help=f"Yasaklı adlar listesi (varsayılan: <kök>/{YASAKLI_ADLAR_DOSYASI})",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = argumanlari_ayristir(argv)
    kok: Path = args.kok
    if not kok.is_dir():
        print(f"HATA: depo kökü bulunamadı: {kok}")
        return 2
    if not args.liste.is_file():
        print(f"HATA: dosya listesi bulunamadı: {args.liste}")
        return 2

    yollar = liste_oku(args.liste)
    if not yollar:
        print("HATA: dosya listesi boş — `git ls-files -z` çıktısı üretilemedi.")
        return 2

    adlar_dosyasi: Path = args.yasakli_adlar or kok / YASAKLI_ADLAR_DOSYASI
    adlar = yasakli_adlari_oku(adlar_dosyasi)
    if adlar is None:
        print(
            f"UYARI: yasaklı ad taraması atlandı — {adlar_dosyasi.name} yok "
            "(depo dışındaki liste; tasarım §13 D42)."
        )
    elif not adlar:
        print(f"UYARI: yasaklı ad listesi boş ({adlar_dosyasi.name}).")

    bulgular = denetle(kok, yollar, adlar or ())
    if any(bulgular):
        print("HATA: depoda kişisel veri olabilecek içerik bulundu:")
        for yol in bulgular.riskli:
            print(f"  - veri dosyası: {yol}")
        # Yalnız konum; eşleşen sayı ya da ad BASILMAZ.
        for konum in bulgular.tckn:
            print(f"  - T.C. kimlik numarası olabilecek sayı: {konum}")
        for konum in bulgular.iban:
            print(f"  - IBAN olabilecek değer: {konum}")
        for konum in bulgular.yasakli_ad:
            print(f"  - yasaklı listedeki bir ad: {konum}")
        print(
            "\nSentetik bir örnek ya da programın bir şablonunu eklediyseniz "
            "packaging/depo_sizintisi.py içindeki MUAF_YOLLAR listesine ADIYLA yazın "
            "(joker kullanmayın)."
        )
        return 1

    print(f"Depo veri denetimi başarılı: {len(yollar)} izlenen dosyada bulgu yok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
