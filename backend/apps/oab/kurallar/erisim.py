"""Kural paketine tek erişim: `kural`, `denetle`, `bilgi_notu` (tasarım §6.1 "Erişim").

`donem` verilirse dönemin dondurulmuş kopyasından (`donem.rule_package.content`, §6.2) okunur; dağıtılan
paket yüklenemese de kopya okunur (§6.2-4, D1 "okuma açık"). `donem` verilmezse programla gelen en yeni
revizyondan okunur: okul kartı ve sihirbaz dönem açılmadan çalışır (plan F1c kararları). Paket
yüklenemeyince bu yol kapalıdır, kural kullanan yazma servisleri de `yazma_kapisi` ile durur (`hatalar`).
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import date
from decimal import Decimal
from typing import Any, Final, Literal, TypedDict

from django.utils import timezone

from apps.oab.kurallar import yukleyici
from apps.oab.kurallar.denetimler import tarih_coz
from apps.oab.kurallar.hatalar import (
    BilinmeyenKural,
    KuralPaketiKullanilamaz,
    OlayTarihiGerekli,
    YururlukteDegerYok,
)
from apps.oab.kurallar.yukleyici import Paket

Durum = Literal["uygun", "eksik", "uyari", "sert", "denetlenmedi"]

DENETLENMEDI_NOTU: Final = "Olay tarihindeki metin korpusta yok; denetlenmedi."
EKSIK_NOTU: Final = "Bu kuralın denetleyeceği bilgi henüz girilmedi."

#: Atıfta dosyanın kısa adı (tasarım §6.4 kısaltmaları). OAB Yönetmeliği kısaltmasız yazılır.
_KISA_ADLAR: Final[Mapping[str, str]] = {
    "meb-okul-aile-birligi-yonetmeligi.md": "",
    "meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md": "EK-2",
    "ortaogretim-kurumlari-yonetmeligi.md": "OKY",
    "meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md": "OÖİKY",
    "meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md": "SEY",
    "meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md": "RPD",
    "okul-servis-araclari-yonetmeligi.md": "OSAY",
    "okul-servisi-calistirma-usul-esaslari.md": "U-E",
    "okul-kantinlerinde-gida-ve-hijyen-denetimi-genelgesi-2020-8.md": "G.2020/8",
    "5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md": "5510",
}


#: Birlik dönemi (`OabTerm`) ya da içeriği taşıyan eşdeğeri: `.rule_package.content` okunur. Protokol
#: değildir: django-stubs yabancı anahtarı tanımlayıcı olarak gördüğü için `OabTerm` ona uymaz.
type DonemBagi = Any


class DenetimSonucu(TypedDict):
    durum: Durum
    mesaj: str
    atif: str
    dayanak_turu: str
    paket: str
    rev: int


class _VeriYok:
    """`denetle`nin "gözlenen değer henüz girilmedi" işareti (`None` geçerli bir değer değil)."""


VERI_YOK: Final = _VeriYok()


def yazma_kapisi() -> None:
    """Kural kullanan her yazma servisinin başındaki kapı: paket yüklenemediyse yazma kapalı (D1).

    `kural`, `denetle` ve `bilgi_notu` okuyucudur, dönem kopyasıyla paket yüklenemese de çalışır.
    """
    if yukleyici.durum().en_yeni is None:
        raise KuralPaketiKullanilamaz


def _paket(donem: DonemBagi | None) -> Paket:
    if donem is not None:
        return Paket.sozlukten(donem.rule_package.content)
    en_yeni = yukleyici.durum().en_yeni
    if en_yeni is None:
        raise KuralPaketiKullanilamaz
    return en_yeni


def _kayitlar(paket: Paket, kural_id: str) -> tuple[Mapping[str, Any], ...]:
    kayitlar = paket.kayitlar.get(kural_id)
    if kayitlar is None:
        raise BilinmeyenKural
    return kayitlar


def _olay_gunu(
    paket: Paket,
    kural_id: str,
    tarih: date | None,
    donem: DonemBagi | None,
    olaylar: Mapping[str, date] | None,
) -> date:
    """Kuralın bakacağı gün (tasarım §6.1 "Olay tarihi", MA-12).

    Önce verilen `tarih`; yoksa kuralın `olay_tarihi` alanının adlandırdığı olayın `olaylar`daki günü.
    Bugün yalnız dönemsiz okumada (okul kartı, sihirbaz) kullanılır: dönem kuralı işlem anıyla
    hesaplanırsa geçmiş olay yanlış yürürlük aralığına düşer.
    """
    if tarih is not None:
        return tarih
    adlar = (kayit["olay_tarihi"] for kayit in _kayitlar(paket, kural_id) if "olay_tarihi" in kayit)
    gun = (olaylar or {}).get(next(adlar, ""))
    if gun is not None:
        return gun
    if donem is None:
        return timezone.localdate()
    raise OlayTarihiGerekli


def _kayit(paket: Paket, kural_id: str, tarih: date) -> Mapping[str, Any]:
    for kayit in _kayitlar(paket, kural_id):
        yururluk = kayit["yururluk"]
        bitis = yururluk["bitis"]
        if tarih_coz(yururluk["baslangic"]) <= tarih and (
            bitis is None or tarih <= tarih_coz(bitis)
        ):
            return kayit
    raise YururlukteDegerYok(f"{kural_id}: {tarih.isoformat()}")


def kural(
    kural_id: str,
    tarih: date | None = None,
    donem: DonemBagi | None = None,
    *,
    olaylar: Mapping[str, date] | None = None,
) -> Any:
    """Kuralın olay günündeki değeri; `donem` verilince olay günü zorunludur (`_olay_gunu`).

    Dönen liste ya da sözlük kopyadır: çağıran değiştirse de paket değişmez.
    """
    paket = _paket(donem)
    return deepcopy(
        _kayit(paket, kural_id, _olay_gunu(paket, kural_id, tarih, donem, olaylar))["deger"]
    )


def kural_kaydi(
    kural_id: str,
    *,
    tarih: date | None = None,
    donem: DonemBagi | None = None,
    olaylar: Mapping[str, date] | None = None,
) -> Mapping[str, Any]:
    """Kuralın olay günündeki kaydı (`toplu_gerekce`, `sert_gerekcesi` gibi şema alanları için).

    `kural` değeri, bu kayıt tümünü verir. Olay gününde yürürlükte kayıt yoksa `YururlukteDegerYok`.
    """
    paket = _paket(donem)
    return _kayit(paket, kural_id, _olay_gunu(paket, kural_id, tarih, donem, olaylar))


def _madde_ad(madde: Mapping[str, Any]) -> str:
    return str(madde["capa"]).split("#", 1)[1]


def _madde_no(ad: str) -> str | None:
    return ad.rsplit("madde-", 1)[1] if "madde-" in ad else None


def _konum(madde: Mapping[str, Any]) -> str:
    """Çapa adı ve fıkra-bent zinciri: "9/3", "17/1-a-1", "7/1. paragraf", "A-1/a"."""
    ad = _madde_ad(madde)
    no = _madde_no(ad)
    if no is None:  # genelge bölümü: `bolum-a-1-a` → `A-1/a`
        parcalar = ad.removeprefix("bolum-").split("-")
        return f"{parcalar[0].upper()}-{parcalar[1]}/{parcalar[2]}"
    if "fikra" not in madde:
        return no
    if madde.get("fikra_bicimi") == "paragraf":
        return f"{no}/{madde['fikra']}. paragraf"
    zincir = [madde["fikra"], *(madde[a] for a in ("bent", "alt_bent") if a in madde)]
    return f"{no}/{'-'.join(zincir)}"


def _tam_konum(madde: Mapping[str, Any]) -> str:
    kisa = _KISA_ADLAR.get(madde["capa"].split("#", 1)[0], "")
    konum = _konum(madde)
    if _madde_no(_madde_ad(madde)) is None:
        return f"{kisa} {konum}".strip()
    return f"{kisa} md. {konum}".strip()


def _gerekce_konumlari(kayit: Mapping[str, Any]) -> str:
    """Kullanıcı kararının gerekçe hükümleri: "md. 12/1, 27/2-3"."""
    maddeler = [kayit["madde"], *kayit.get("ek_madde", ())]
    parcalar: list[str] = []
    onceki: Mapping[str, Any] | None = None
    for madde in maddeler:
        ayni_madde = onceki is not None and onceki["capa"] == madde["capa"]
        if ayni_madde and "bent" not in madde:
            parcalar[-1] += f"-{madde['fikra']}"
        else:
            parcalar.append(_konum(madde))
        onceki = madde
    return f"md. {', '.join(parcalar)}"


def atif_metni(kayit: Mapping[str, Any]) -> str:
    """Ekrandaki atıf: "md. 9/3" ya da "kullanıcı kararı A-2 (gerekçe md. 14/4)".

    Kullanıcı kararı hiçbir yerde "Yönetmelik gereği" diye basılmaz (altın kural 1).
    """
    if kayit["dayanak_turu"] == "kullanici_karari":
        return f"kullanıcı kararı {kayit['karar']['kimlik']} (gerekçe {_gerekce_konumlari(kayit)})"
    return _tam_konum(kayit["madde"])


def atifli_metin(sonuc: DenetimSonucu) -> str:
    """Mesajın sonuna atıf: "… uygulanır (md. 23/3)." (tasarım §6.1 `uyari_metni`)."""
    return f"{sonuc['mesaj'].rstrip('.')} ({sonuc['atif']})."


def _sonuc(durum: Durum, mesaj: str, kayit: Mapping[str, Any], paket: Paket) -> DenetimSonucu:
    return DenetimSonucu(
        durum=durum,
        mesaj=mesaj,
        atif=atif_metni(kayit),
        dayanak_turu=kayit["dayanak_turu"],
        paket=paket.kimlik,
        rev=paket.rev,
    )


def _kosul_durumu(kayit: Mapping[str, Any], okul: Mapping[str, Any] | None) -> bool | None:
    """Koşul sağlanıyor mu? Okul kartında değer girilmemişse `None` (eksik; tasarım R5)."""
    for anahtar, izinli in kayit.get("kosul", {}).items():
        secili = (okul or {}).get(anahtar)
        if not secili:
            return None
        degerler = secili if isinstance(secili, list | tuple | set) else [secili]
        if not set(degerler) & set(izinli):
            return False
    return True


def _esit(gozlenen: Any, deger: Any) -> bool:
    if isinstance(deger, str):
        return Decimal(str(gozlenen)) == Decimal(deger)
    return bool(gozlenen == deger)


def _uyuyor(karsilastirma: str, gozlenen: Any, deger: Any) -> bool:
    if isinstance(gozlenen, float):
        raise TypeError("Kural değerleri kayan noktayla karşılaştırılmaz.")
    if karsilastirma == "en_az":
        return bool(gozlenen >= deger)
    if karsilastirma == "en_cok":
        return bool(gozlenen <= deger)
    if karsilastirma == "kucuktur":
        return bool(gozlenen < deger)
    if karsilastirma == "liste_icinde":
        return (
            all(oge in deger for oge in gozlenen)
            if isinstance(gozlenen, list)
            else gozlenen in deger
        )
    return _esit(gozlenen, deger)  # esit, parametre, carpan, tablo


def _sapma_mesaji(kayit: Mapping[str, Any], gozlenen: Any) -> str:
    sablon = kayit.get("uyari_metni", kayit["aciklama"])
    return str(sablon.format(deger=kayit["deger"], fark=gozlenen))


def denetle(
    kural_id: str,
    gozlenen: Any = VERI_YOK,
    *,
    tarih: date | None = None,
    donem: DonemBagi | None = None,
    okul: Mapping[str, Any] | None = None,
    olaylar: Mapping[str, date] | None = None,
) -> DenetimSonucu:
    """Gözlenen değeri kuralla karşılaştırır (tasarım §6.1).

    `okul`, koşul anahtarlarının (`okul.kantin` gibi) o okuldaki değerleridir. Koşul sağlanmıyorsa
    kural uygulanmaz: `uygun`, boş mesaj. Veri girilmemişse `eksik` (gerekçe istemez, R5);
    `eksik_veri: sapma` olan kuralda eksiklik baştan sapmadır.
    """
    paket = _paket(donem)
    try:
        kayit = _kayit(paket, kural_id, _olay_gunu(paket, kural_id, tarih, donem, olaylar))
    except YururlukteDegerYok:
        en_yeni = paket.kayitlar[kural_id][-1]
        return _sonuc("denetlenmedi", DENETLENMEDI_NOTU, en_yeni, paket)
    uygulanir = _kosul_durumu(kayit, okul)
    if uygulanir is False:
        return _sonuc("uygun", "", kayit, paket)
    tur: Durum = "sert" if kayit["tur"] == "sert" else "uyari"
    if uygulanir is None or isinstance(gozlenen, _VeriYok):
        if kayit["eksik_veri"] == "sapma":
            return _sonuc(tur, kayit.get("uyari_metni", kayit["aciklama"]), kayit, paket)
        return _sonuc("eksik", EKSIK_NOTU, kayit, paket)
    if _uyuyor(kayit["karsilastirma"], gozlenen, kayit["deger"]):
        return _sonuc("uygun", "", kayit, paket)
    return _sonuc(tur, _sapma_mesaji(kayit, gozlenen), kayit, paket)


def bilgi_notu(
    kural_id: str,
    *,
    tarih: date | None = None,
    donem: DonemBagi | None = None,
    okul: Mapping[str, Any] | None = None,
    olaylar: Mapping[str, date] | None = None,
) -> DenetimSonucu | None:
    """Karşılaştıracak değeri olmayan, koşulu tutunca görünen bilgi (md. 23/3 gibi).

    Koşul tutmuyorsa ya da okul kartında seçim yapılmamışsa `None`: uyarı da bilgi de üretilmez.
    """
    paket = _paket(donem)
    kayit = _kayit(paket, kural_id, _olay_gunu(paket, kural_id, tarih, donem, olaylar))
    if _kosul_durumu(kayit, okul) is not True:
        return None
    return _sonuc("uyari", kayit["uyari_metni"], kayit, paket)
