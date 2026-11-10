"""Kural paketinin açılışta da koşan denetimleri: D1, D2, D5 (tasarım §6.3).

Hepsi saf işlevdir: paketin sözlüğünü alır, Türkçe hata satırları döndürür; boş liste geçti demektir.
D3 ve D4 (atıf kilidi) korpusa bakar ve korpus dağıtılmaz: onlar `apps/oab/tests/kurallar/`'dadır.
D7 dosya baytına bakar, `yukleyici`'dedir.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from string import Formatter
from typing import Any

from apps.oab.kurallar.dogrulayici import sema_hatalari

#: `giris` ve `davranis_fazi`'nın sırası (tasarım §6.1); `davranis_fazi` `giris`ten önce olamaz.
FAZLAR = ("F1c", "F2", "F3", "F4", "F5", "F6", "F7", "F8")
#: `uyari_metni`nin yer tutucuları (`denetle` doldurur).
YER_TUTUCULAR = frozenset({"deger", "fark"})
_TARIH = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")


def tarih_coz(metin: str) -> date:
    """`gg.aa.yyyy` → `date`; biçim ya da takvim bozuksa `ValueError`."""
    eslesme = _TARIH.match(metin)
    if eslesme is None:
        raise ValueError(f"Tarih gg.aa.yyyy biçiminde olmalı: {metin}")
    gun, ay, yil = (int(parca) for parca in eslesme.groups())
    return date(yil, ay, gun)


def _kayan_noktalar(deger: Any, yol: str) -> list[str]:
    if isinstance(deger, float):
        return [f"{yol}: kayan nokta yasak, ondalık dize yazılır"]
    if isinstance(deger, list):
        return [h for i, ic in enumerate(deger) for h in _kayan_noktalar(ic, f"{yol}[{i}]")]
    if isinstance(deger, dict):
        return [h for ad, ic in deger.items() for h in _kayan_noktalar(ic, f"{yol}.{ad}")]
    return []


def _tarih_hatasi(metin: str, yol: str) -> list[str]:
    try:
        tarih_coz(metin)
    except ValueError:
        return [f"{yol}: takvimde olmayan tarih ({metin})"]
    return []


def _kural_anlam_hatalari(kural: Mapping[str, Any]) -> list[str]:
    kid = kural["id"]
    hatalar: list[str] = []
    if FAZLAR.index(kural["davranis_fazi"]) < FAZLAR.index(kural["giris"]):
        hatalar.append(f"{kid}: davranis_fazi giristen önce olamaz")
    yururluk = kural["yururluk"]
    hatalar += _tarih_hatasi(yururluk["baslangic"], f"{kid}.yururluk.baslangic")
    if yururluk["bitis"] is not None:
        hatalar += _tarih_hatasi(yururluk["bitis"], f"{kid}.yururluk.bitis")
    if "karar" in kural:
        hatalar += _tarih_hatasi(kural["karar"]["tarih"], f"{kid}.karar.tarih")
    if "uyari_metni" in kural:
        adlar = {ad for _, ad, _, _ in Formatter().parse(kural["uyari_metni"]) if ad is not None}
        if not adlar <= YER_TUTUCULAR:
            hatalar.append(f"{kid}: tanımsız yer tutucu {sorted(adlar - YER_TUTUCULAR)}")
    return hatalar


def d1_sema(icerik: Any, sema: Mapping[str, Any]) -> list[str]:
    """D1: şema, kayan nokta yasağı, gerçek takvim tarihi, faz sırası, yer tutucular."""
    hatalar = sema_hatalari(icerik, sema)
    hatalar += _kayan_noktalar(icerik, "$")
    if hatalar:
        return hatalar  # yapı bozuksa aşağıdaki alan okumaları anlamsızdır
    hatalar += _tarih_hatasi(icerik["korpus_teyit"], "$.korpus_teyit")
    for kural in icerik["kurallar"]:
        hatalar += _kural_anlam_hatalari(kural)
    return hatalar


def _aralik(kural: Mapping[str, Any]) -> tuple[str, str | None]:
    yururluk = kural["yururluk"]
    return yururluk["baslangic"], yururluk["bitis"]


def _kimliklere_gore(icerik: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    gruplar: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for kural in icerik["kurallar"]:
        gruplar[kural["id"]].append(kural)
    for kayitlar in gruplar.values():
        kayitlar.sort(key=lambda k: tarih_coz(k["yururluk"]["baslangic"]))
    return gruplar


def _aralik_hatalari(kid: str, kayitlar: list[dict[str, Any]]) -> list[str]:
    hatalar: list[str] = []
    for once, sonra in zip(kayitlar, kayitlar[1:], strict=False):
        bitis = once["yururluk"]["bitis"]
        if bitis is None or tarih_coz(bitis) >= tarih_coz(sonra["yururluk"]["baslangic"]):
            hatalar.append(f"{kid}: yürürlük aralıkları çakışıyor")
    for kayit in kayitlar:
        baslangic, bitis = _aralik(kayit)
        if bitis is not None and tarih_coz(bitis) < tarih_coz(baslangic):
            hatalar.append(f"{kid}: yürürlük bitişi başlangıçtan önce")
    return hatalar


def degisim_turu(once: list[dict[str, Any]], simdi: list[dict[str, Any]]) -> str | None:
    """Önceki revizyondan bu revizyona kimliğin değişiminin türü; değişmediyse `None`."""
    if once == simdi:
        return None
    if [_aralik(k) for k in once] == [_aralik(k) for k in simdi]:
        return "duzeltme"  # aynı aralığın yerini alır (tasarım §6.2-3a)
    if len(simdi) == len(once) + 1:
        return "deger_degisikligi"
    if (
        len(simdi) == len(once)
        and [k["yururluk"]["baslangic"] for k in once]
        == [k["yururluk"]["baslangic"] for k in simdi]
        and [{**k, "yururluk": None} for k in once] == [{**k, "yururluk": None} for k in simdi]
    ):
        return "bitis"  # yalnız yürürlük bitişi değişti; değer de değiştiyse bitiş sayılmaz
    return "tanimsiz"


def d2_kimlik(icerik: Mapping[str, Any], onceki: Mapping[str, Any] | None = None) -> list[str]:
    """D2: kimlik tekilliği, aralıklar, silinmeyen kimlik, `degisiklikler` beyanının doğruluğu.

    Aynı kimlik farklı yürürlük aralıklarıyla birden çok kez bulunabilir (tasarım §6.2-3); tekil
    olan kimlik ve aralık başlangıcı çiftidir. `onceki`, sıradaki bir önceki revizyondur; ilk
    revizyonda bütün kimlikler `ekleme` beyan edilir.
    """
    hatalar: list[str] = []
    gruplar = _kimliklere_gore(icerik)
    for kid, kayitlar in gruplar.items():
        baslangiclar = [k["yururluk"]["baslangic"] for k in kayitlar]
        if len(set(baslangiclar)) != len(baslangiclar):
            hatalar.append(f"{kid}: aynı aralıkla iki kayıt")
        hatalar += _aralik_hatalari(kid, kayitlar)

    once_gruplar = _kimliklere_gore(onceki) if onceki is not None else {}
    if onceki is not None:
        if icerik["paket"] == onceki["paket"] and icerik["rev"] != onceki["rev"] + 1:
            hatalar.append("Revizyon numarası önceki revizyonun bir fazlası olmalı.")
        if icerik["paket"] != onceki["paket"] and icerik["rev"] != 1:
            hatalar.append("Yeni paket kimliği 1. revizyonla başlar.")
    hatalar += [f"{kid}: yayımlanmış kimlik silinmiş" for kid in once_gruplar.keys() - gruplar]

    beyan: dict[str, list[str]] = defaultdict(list)
    for satir in icerik["degisiklikler"]:
        beyan[satir["id"]].append(satir["tur"])
    hatalar += [f"{kid}: pakette olmayan kimlik beyan edilmiş" for kid in beyan.keys() - gruplar]
    for kid, kayitlar in gruplar.items():
        once = once_gruplar.get(kid)
        tur = "ekleme" if once is None else degisim_turu(once, kayitlar)
        beklenen = [] if tur is None else [tur]
        if beyan.get(kid, []) != beklenen:
            hatalar.append(f"{kid}: degisiklikler beyanı tutmuyor (beklenen: {beklenen or 'yok'})")
    return hatalar


def _en_yeni_deger(gruplar: Mapping[str, list[dict[str, Any]]], kid: str) -> Any:
    return gruplar[kid][-1]["deger"]


def d5_tutarlilik(icerik: Mapping[str, Any]) -> list[str]:
    """D5: kuralların birbirine bağlı değerleri (tasarım §6.3).

    Yalnız en yeni kayda bakılır: eski aralıklar kendi revizyonlarında bu denetimden geçmiştir.
    Pakette henüz olmayan kuralın denetimi (EK-3, F6) o kural gelene dek atlanır.
    """
    g = _kimliklere_gore(icerik)
    hatalar: list[str] = []

    def var(*kimlikler: str) -> bool:
        return all(kid in g for kid in kimlikler)

    kurul = (
        "yonetim_kurulu.asil_uye",
        "yonetim_kurulu.yedek_uye",
        "denetleme_kurulu.asil_uye",
        "denetleme_kurulu.yedek_uye",
    )
    if var("genel_kurul.yeter_sayi_taban", *kurul):
        toplam = sum(_en_yeni_deger(g, kid) for kid in kurul)
        if _en_yeni_deger(g, "genel_kurul.yeter_sayi_taban") != toplam:
            hatalar.append(f"genel_kurul.yeter_sayi_taban kurul bileşimiyle ({toplam}) tutmuyor.")
    if var("denetleme_kurulu.koltuklar", "denetleme_kurulu.asil_uye", "denetleme_kurulu.yedek_uye"):
        koltuklar = _en_yeni_deger(g, "denetleme_kurulu.koltuklar").values()
        for tur, kid in (
            ("ASIL", "denetleme_kurulu.asil_uye"),
            ("YEDEK", "denetleme_kurulu.yedek_uye"),
        ):
            if sum(k[tur] for k in koltuklar) != _en_yeni_deger(g, kid):
                hatalar.append(f"denetleme_kurulu.koltuklar {kid} ile tutmuyor.")
    for kid, kayitlar in g.items():
        if kid.startswith("pay_dagitimi."):
            pay = kayitlar[-1]["deger"]
            if not isinstance(pay, dict) or sum(Decimal(v) for v in pay.values()) != Decimal(1):
                hatalar.append(f"{kid}: payların toplamı 1,00 olmalı.")
    if var("arz_bedeli.sozlesme_vade_gunu", "arz_bedeli.yonetmelik_vade_gunu") and _en_yeni_deger(
        g, "arz_bedeli.sozlesme_vade_gunu"
    ) >= _en_yeni_deger(g, "arz_bedeli.yonetmelik_vade_gunu"):
        hatalar.append("arz_bedeli.sozlesme_vade_gunu yönetmelik vadesinden önce olmalı.")
    if var("genel_kurul.yeter_sayi_carpan", "genel_kurul.kucuk_okul_carpan") and _en_yeni_deger(
        g, "genel_kurul.yeter_sayi_carpan"
    ) <= _en_yeni_deger(g, "genel_kurul.kucuk_okul_carpan"):
        hatalar.append("genel_kurul.yeter_sayi_carpan küçük okul çarpanından büyük olmalı.")
    if var("servis.ek3_kriter_azami_puan"):
        azami = _en_yeni_deger(g, "servis.ek3_kriter_azami_puan")
        if isinstance(azami, dict) and sum(azami.values()) != 25:
            hatalar.append("servis.ek3_kriter_azami_puan toplamı 25 olmalı.")
    return hatalar
