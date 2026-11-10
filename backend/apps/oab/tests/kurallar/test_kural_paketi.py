"""Kural paketi testleri (`kp`, tasarım §10.1 ve §10.2): D1-D8, atıf kilidi, değer tablosu, erişim.

Değer tablosu (`DEGER_TABLOSU`) korpustan ve tasarım §6.4'ten **elle** yazılmıştır, pakete bakmaz:
paketle karşılaştırılan ikinci kayıttır. Dönem bağı ve sapma-gerekçe testleri dosyanın sonundadır
(F1c'nin 3. adımı); kapanış testleri sentetik dönemle kurulur, gerçek kapanış F4'tedir.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from string import Formatter
from types import ModuleType, SimpleNamespace
from typing import Any

import jsonschema
import pytest
from django.db import connection

from apps.oab.hatalar import (
    DonemKapali,
    GerekceGerekli,
    KuralSert,
    RevizyonOnayiGerekli,
)
from apps.oab.kurallar import (
    BilinmeyenKural,
    KuralPaketiKullanilamaz,
    OlayTarihiGerekli,
    YururlukteDegerYok,
    bilgi_notu,
    denetimler,
    denetle,
    erisim,
    kural,
    yazma_kapisi,
)
from apps.oab.kurallar import genel_kurul as genel_kurul_hesabi
from apps.oab.kurallar import yukleyici as yk
from apps.oab.kurallar.dogrulayici import SemaHatasi, sema_hatalari
from apps.oab.models import (
    AssemblyKind,
    ComplianceItem,
    ComplianceJustification,
    ComplianceKind,
    GeneralAssembly,
    OabTerm,
    RulePackage,
    TermStatus,
)
from apps.oab.services import donem_kilidi, donemler, genel_kurul, kural_bagi, uyum
from apps.oab.tests.kurallar import atif_ortak, faz_ortak, isaret_ortak
from apps.okul import denetim_izi
from apps.okul.models import (
    AuditAction,
    AuditTrail,
    CanteenMode,
    SchoolConfig,
    SchoolLevel,
    SchoolYear,
    SettlementType,
    StaffingMode,
)

DOSYA = "OAB-2023.12.r1.json"
SEMA: dict[str, Any] = json.loads((yk.PAKETLER_DIZINI / yk.SEMA_ADI).read_text(encoding="utf-8"))
R1: dict[str, Any] = json.loads((yk.PAKETLER_DIZINI / DOSYA).read_text(encoding="utf-8"))
KURALLAR: dict[str, dict[str, Any]] = {k["id"]: k for k in R1["kurallar"]}
KORPUS = atif_ortak.korpus_kokleri(Path(__file__))
Y = "meb-okul-aile-birligi-yonetmeligi.md"
#: Tasarım §15.1 ve §15.1b'nin kullanıcı kararı kimlikleri (elle yazıldı).
KULLANICI_KARARLARI = frozenset(
    {"A-1", "KE-1", "M-5", "M-6", "B-13", "A-2", "KE-5", "KE-15", "D1", "D2", "D3", "D4", "D5"}
)

_KISA_DOSYA = {
    "Y": (Y, "madde-", False),
    "E2": (
        "meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md",
        "genel-sartlar-madde-",
        True,
    ),
    "OKY": ("ortaogretim-kurumlari-yonetmeligi.md", "madde-", False),
    "OOIKY": ("meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md", "madde-", False),
    "SEY": ("meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md", "madde-", False),
    "RPD": ("meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md", "madde-", False),
    "OSAY": ("okul-servis-araclari-yonetmeligi.md", "madde-", False),
    "UE": ("okul-servisi-calistirma-usul-esaslari.md", "madde-", False),
    "G2020": ("okul-kantinlerinde-gida-ve-hijyen-denetimi-genelgesi-2020-8.md", "bolum-a-1-", True),
    "K5510": ("5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md", "madde-", True),
}


def _madde(kisa: str) -> dict[str, str]:
    """ "Y 17/1-a-1" → paketteki `madde` nesnesi; genelge bölümü "G2020 a" diye yazılır."""
    dosya_kisa, konum = kisa.split()
    dosya, onek, paragraf = _KISA_DOSYA[dosya_kisa]
    no, _, zincir = konum.partition("/")
    sonuc = {"capa": f"{dosya}#{onek}{no}"}
    if zincir:
        for ad, deger in zip(("fikra", "bent", "alt_bent"), zincir.split("-"), strict=False):
            sonuc[ad] = deger
    if paragraf:
        sonuc["fikra_bicimi"] = "paragraf"
    return sonuc


@dataclass(frozen=True)
class B:
    """Değer tablosunun satırı; alan adları kısaltılmadı, sıra paketle aynı."""

    deger: Any
    birim: str
    karsilastirma: str
    sert_gerekcesi: str | None
    dayanak_turu: str
    atif: tuple[str, ...]
    yururluk: str
    davranis_fazi: str = "F1c"
    kosul: dict[str, list[str]] | None = None
    karar: str | None = None
    eksik_veri: str = "tamamlanacak"


HB, HD, HG, KK = "hesap_butunlugu", "hesaplanan_deger", "hukuki_gecersizlik", "kullanici_karari"
_2012, _2023 = "09.02.2012", "01.12.2023"
_LISE = {"okul.kademe": ["ORTAOGRETIM"]}
_KIRA = {"okul.kantin": ["KIRAYA_VERILIYOR"]}
_ISLETME = {"okul.kantin": ["BIRLIKCE_ISLETILIYOR"]}
_YK_KOLTUK = ("Y 12/1", "Y 11/1-a")
_DK_KOLTUK = ("Y 14/1", "Y 11/1-b")

# Satır başına bir kural: tablo paketle yan yana okunur, biçimleyici bölmesin.
# fmt: off
DEGER_TABLOSU: dict[str, B] = {
    # §6.4.1 Genel kurul (Y:137-150)
    "genel_kurul.olagan_son_ay": B(10, "takvim_ayi", "en_cok", None, "lafiz", ("Y 9/1",), _2012, "F2"),
    "genel_kurul.ilan_en_az_gun": B(15, "gun", "en_az", None, "lafiz", ("Y 9/3", "Y 9/6"), _2012, "F2"),
    "genel_kurul.yeter_sayi_taban": B(16, "kisi", "parametre", HB, "yorum", ("Y 9/2", "Y 12/1", "Y 14/1"), _2012),
    "genel_kurul.yeter_sayi_carpan": B(4, "adet", "carpan", HB, "lafiz", ("Y 9/2", "Y 9/6"), _2012),
    "genel_kurul.kucuk_okul_carpan": B(2, "adet", "carpan", HB, "lafiz", ("Y 9/2", "Y 9/6"), _2012),
    "genel_kurul.kucuk_okul_esik": B(100, "ogrenci", "kucuktur", HB, "lafiz", ("Y 9/2", "Y 9/6"), _2012),
    "genel_kurul.ikinci_toplanti_en_gec_gun": B(30, "gun", "en_cok", None, "yorum", ("Y 9/2",), _2012, "F2"),
    "genel_kurul.ikinci_toplanti_cogunluk_aranmaz": B(True, "mantiksal", "esit", HB, "lafiz", ("Y 9/2",), _2012, "F2"),
    "genel_kurul.divan_uye_turleri": B(["VELI", "KURSIYER"], "liste", "liste_icinde", None, "lafiz", ("Y 10/1-c",), _2023, "F2"),
    # §6.4.2 Yönetim kurulu ve ortak üyelik (Y:113-116, 186-210, 396)
    "yonetim_kurulu.asil_uye": B(5, "kisi", "esit", None, "lafiz", _YK_KOLTUK, _2012),
    "yonetim_kurulu.yedek_uye": B(5, "kisi", "esit", None, "lafiz", _YK_KOLTUK, _2012),
    "yonetim_kurulu.uye_turleri": B(["VELI", "KURSIYER", "HAYIRSEVER"], "liste", "liste_icinde", HG, "lafiz", ("Y 12/1",), _2023),
    "yonetim_kurulu.okul_muduru_uye_olamaz": B(True, "mantiksal", "esit", KK, "kullanici_karari", ("Y 12/1", "Y 27/2", "Y 27/3"), _2023, karar="KE-15"),
    "yonetim_kurulu.gorev_suresi_yil": B(1, "yil", "esit", None, "lafiz", ("Y 12/2",), _2012),
    "yonetim_kurulu.gorev_bolumu_gun": B(7, "gun", "en_cok", None, "yorum", ("Y 12/3",), _2012),
    "yonetim_kurulu.gorevler": B({"BASKAN": 1, "BASKAN_YARDIMCISI": 1, "MUHASIP": 1, "SEKRETER": 1}, "tablo", "tablo", HB, "lafiz", ("Y 12/3",), _2012),
    "yonetim_kurulu.secilme_siniri": B(4, "adet", "en_cok", None, "lafiz", ("Y 12/4",), _2023),
    "yonetim_kurulu.tek_birlik": B(True, "mantiksal", "esit", None, "lafiz", ("Y 12/4",), _2012),
    "uyelik.suc_engeli": B(True, "mantiksal", "esit", None, "lafiz", ("Y 12/5", "Y 14/7"), _2023),
    "uyelik.ayrilan_veli_devam": B(True, "mantiksal", "esit", None, "lafiz", ("Y 7/2",), _2023),
    "yonetim_kurulu.yedek_cagirma": B(["OY_SIRASI"], "liste", "parametre", None, "lafiz", ("Y 13/6",), _2012),
    "yonetim_kurulu.toplanti_yeter_sayi": B(4, "kisi", "en_az", HB, "lafiz", ("Y 13/3",), _2012, "F3"),
    "yonetim_kurulu.karar_yeter_sayi": B(3, "kisi", "en_az", HB, "lafiz", ("Y 13/3",), _2012, "F3"),
    "yonetim_kurulu.devamsizlik_siniri": B(3, "adet", "kucuktur", None, "lafiz", ("Y 13/6",), _2012, "F3"),
    "yonetim_kurulu.karar_defteri_noter_tasdiki": B(["NOTER"], "liste", "liste_icinde", None, "lafiz", ("Y 23/2",), _2012, eksik_veri="sapma"),
    # §6.4.3 Denetleme Kurulu (Y:224-237)
    "denetleme_kurulu.asil_uye": B(3, "kisi", "esit", None, "lafiz", _DK_KOLTUK, _2012),
    "denetleme_kurulu.yedek_uye": B(3, "kisi", "esit", None, "lafiz", _DK_KOLTUK, _2012),
    "denetleme_kurulu.koltuklar": B({"VELI": {"ASIL": 1, "YEDEK": 1}, "OGRETMEN": {"ASIL": 2, "YEDEK": 2}}, "tablo", "tablo", HG, "lafiz", _DK_KOLTUK, _2023),
    "denetleme_kurulu.gorev_bolumu_gun": B(7, "gun", "en_cok", None, "yorum", ("Y 14/1",), _2012),
    "denetleme_kurulu.gorev_suresi_yil": B(1, "yil", "esit", None, "lafiz", ("Y 14/2",), _2012),
    "denetleme_kurulu.baskan_secilme_siniri": B(3, "adet", "en_cok", None, "lafiz", ("Y 14/3",), _2012),
    "denetleme_kurulu.yk_uyesi_olamaz": B(True, "mantiksal", "esit", KK, "kullanici_karari", ("Y 14/4",), _2023, karar="A-2"),
    "denetleme_kurulu.ogretmen_gorevlendirme_ay": B(4, "ay", "en_cok", None, "lafiz", ("Y 14/6",), _2012),
    # §6.4.4 Birlik temsilcileri
    "temsilci.odul_disiplin_kurulu": B({"ASIL": 1, "YEDEK": 1}, "kisi", "esit", None, "lafiz", ("OKY 185/1-ç", "OKY 186/1"), "07.09.2013", kosul=_LISE),
    "temsilci.davranis_degerlendirme_kurulu": B(1, "kisi", "esit", None, "lafiz", ("OOIKY 57/2-c",), "26.07.2014", kosul={"okul.kademe": ["ORTAOKUL"]}),
    "temsilci.sosyal_etkinlikler_kurulu": B(1, "kisi", "esit", None, "lafiz", ("SEY 6/1",), "08.06.2017"),
    "temsilci.kontenjan_komisyonu": B(1, "kisi", "esit", None, "lafiz", ("OKY 25/1-a",), "13.09.2014", kosul=_LISE),
    "temsilci.rpd_yurutme_komisyonu": B(1, "kisi", "esit", None, "yorum", ("RPD 16/2-e", "RPD 16/5"), "14.08.2020"),
    "temsilci.tasimaci_tespit_komisyonu": B(["BASKAN"], "liste", "liste_icinde", None, "lafiz", ("OSAY 3/1-m", "UE 3/1-e"), "25.10.2017"),
    "temsilci.muhammen_bedel_komisyonu": B(["BASKAN"], "liste", "liste_icinde", None, "lafiz", ("Y 19/1",), _2023),
    "temsilci.kiralama_ihale_komisyonu": B(["BASKAN"], "liste", "liste_icinde", None, "lafiz", ("Y 20/3",), _2012),
    "temsilci.pay_dagitim_komisyonu": B(2, "kisi", "parametre", None, "yorum", ("Y 17/1-b-3",), _2012),
    "temsilci.kantin_denetim_komisyonu": B(1, "kisi", "esit", None, "lafiz", ("G2020 a", "G2020 b"), "10.11.2020", kosul={"okul.kantin": ["KIRAYA_VERILIYOR", "BIRLIKCE_ISLETILIYOR"]}),
    # §6.4.5 Gelir, bağış, makbuz (Y:265, 269)
    "bagis.elden_yatirma_is_gunu": B(5, "is_gunu", "en_cok", None, "yorum", ("Y 16/3",), _2012, "F3"),
    "makbuz.cilt_yaprak": B({"asil": 50, "kocan": 50}, "adet", "esit", None, "lafiz", ("Y 16/5",), _2012, "F3"),
    # §6.4.6 Harcama (Y:287)
    "harcama.alim_komisyonu_en_az": B(3, "kisi", "en_az", None, "lafiz", ("Y 18/1",), _2012),
    "harcama.alim_komisyonu_uyeleri": B(["YK_UYESI", "BIRLIK_UYESI"], "liste", "liste_icinde", None, "lafiz", ("Y 18/1",), _2012, "F4"),
    # §6.4.7 Kantin: arz bedeli ve pay (Y:280-282; EK-2 md. 7)
    "arz_bedeli.kira_oran": B("0.03", "oran", "parametre", HD, "lafiz", ("Y 17/1-a-1", "E2 7/1"), _2012, "F3", kosul=_KIRA),
    "arz_bedeli.isletme_oran": B("0.01", "oran", "parametre", HD, "lafiz", ("Y 17/1-b-1",), _2012, "F5", kosul=_ISLETME),
    "arz_bedeli.sozlesme_vade_gunu": B(10, "ayin_gunu", "en_cok", None, "lafiz", ("E2 7/1",), _2023, "F3", kosul=_KIRA),
    "arz_bedeli.yonetmelik_vade_gunu": B(20, "ayin_gunu", "en_cok", None, "lafiz", ("Y 17/1-a-1", "Y 17/1-b-1"), _2012, "F3"),
    "pay_dagitimi.genel": B({"birlik": "0.80", "ilce": "0.10", "il": "0.10"}, "oran", "tablo", HD, "lafiz", ("Y 17/1-a-2", "Y 17/1-b-2", "E2 7/2"), _2012, "F3", kosul={"okul.yerlesim_turu": ["BUYUKSEHIR", "DIGER"]}),
    "pay_dagitimi.il_merkezi": B({"birlik": "0.80", "ilce": "0.00", "il": "0.20"}, "oran", "tablo", HD, "yorum", ("Y 17/1-a-2", "Y 17/1-b-2"), _2012, "F3", kosul={"okul.yerlesim_turu": ["IL_MERKEZI_BUYUKSEHIR_DEGIL"]}),
    # §6.4.8 Kantin (Y:398)
    "kantin.isletmede_vergi_uyarisi": B(True, "mantiksal", "esit", None, "lafiz", ("Y 23/3",), _2012, kosul=_ISLETME),
    # §6.4.10 Personel (5510:60, 43; Y:72)
    "personel.sgk_saklama_yil": B(10, "yil", "parametre", HD, "yorum", ("K5510 86/2", "K5510 12/1", "Y 5/1"), "16.06.2006", "F8", kosul={"okul.personel": ["DOGRUDAN_ISVEREN"]}),
}
# fmt: on


def _deger_parametreleri(kimlikler: list[str]) -> list[Any]:
    return [pytest.param(kid, id=kid, marks=pytest.mark.kural_deger(kid)) for kid in kimlikler]


def _kopya() -> dict[str, Any]:
    return deepcopy(R1)


def _bul(icerik: dict[str, Any], kid: str) -> dict[str, Any]:
    return next(k for k in icerik["kurallar"] if k["id"] == kid)


def _d1(icerik: Any) -> list[str]:
    return denetimler.d1_sema(icerik, SEMA)


def _paket_dizini(hedef: Path, *icerikler: dict[str, Any], sema: Any = None) -> Path:
    """Şema, revizyon dosyaları ve doğru özetli MANIFEST taşıyan sentetik paket dizini."""
    hedef.mkdir(parents=True, exist_ok=True)
    sema_ham = (
        (yk.PAKETLER_DIZINI / yk.SEMA_ADI).read_bytes()
        if sema is None
        else json.dumps(sema).encode("utf-8")
    )
    (hedef / yk.SEMA_ADI).write_bytes(sema_ham)
    satirlar = []
    for icerik in icerikler:
        ad = f"{icerik['paket']}.r{icerik['rev']}.json"
        ham = json.dumps(icerik, ensure_ascii=False).encode("utf-8")
        (hedef / ad).write_bytes(ham)
        satirlar.append({"dosya": ad, "sha256": hashlib.sha256(ham).hexdigest()})
    manifest = {
        "surum": 1,
        "sema_sha256": hashlib.sha256(sema_ham).hexdigest(),
        "paketler": satirlar,
    }
    (hedef / yk.MANIFEST_ADI).write_text(json.dumps(manifest), "utf-8")
    return hedef


# ======================================================================= sayım


def test_r1_kural_sayimi() -> None:
    """Tasarım §6.4.11: r1 = 55 kural; 17 sert, 38 uyarı; 37 davranışı F1c, 18'i sonra."""
    kurallar = R1["kurallar"]
    assert len(kurallar) == 55 == len(KURALLAR)
    assert sum(k["tur"] == "sert" for k in kurallar) == 17
    assert sum(k["tur"] == "uyari" for k in kurallar) == 38
    assert sum(k["davranis_fazi"] == "F1c" for k in kurallar) == 37
    fazlar = [k["davranis_fazi"] for k in kurallar if k["davranis_fazi"] != "F1c"]
    assert {f: fazlar.count(f) for f in set(fazlar)} == {
        "F2": 5,
        "F3": 10,
        "F4": 1,
        "F5": 1,
        "F8": 1,
    }
    assert {k["giris"] for k in kurallar} == {"F1c"}


# ======================================================================= değer tablosu


def test_deger_tablosu_paketin_butun_kimliklerini_kapsar() -> None:
    assert set(DEGER_TABLOSU) == set(KURALLAR)


@pytest.mark.parametrize("kid", _deger_parametreleri(sorted(DEGER_TABLOSU)))
def test_deger_tablosu(kid: str) -> None:
    """Tasarım §10.1 çift kayıt: paket elle yazılmış tabloyla birebir aynı."""
    b = DEGER_TABLOSU[kid]
    k = KURALLAR[kid]
    assert k["deger"] == b.deger and type(k["deger"]) is type(b.deger)
    assert (k["birim"], k["karsilastirma"]) == (b.birim, b.karsilastirma)
    assert k["tur"] == ("sert" if b.sert_gerekcesi else "uyari")
    assert k.get("sert_gerekcesi") == b.sert_gerekcesi
    assert k["dayanak_turu"] == b.dayanak_turu
    assert [k["madde"], *k.get("ek_madde", [])] == [_madde(a) for a in b.atif]
    assert k["yururluk"] == {"baslangic": b.yururluk, "bitis": None}
    assert (k["giris"], k["davranis_fazi"]) == ("F1c", b.davranis_fazi)
    assert k.get("kosul") == b.kosul
    assert (k.get("karar") or {}).get("kimlik") == b.karar
    assert k["eksik_veri"] == b.eksik_veri and k["toplu_gerekce"] is True


# ======================================================================= D1


def test_sema_gecerli() -> None:
    jsonschema.Draft202012Validator.check_schema(SEMA)
    assert not list(jsonschema.Draft202012Validator(SEMA).iter_errors(R1))
    assert _d1(R1) == []


def _boz(degistir: Any) -> dict[str, Any]:
    icerik = _kopya()
    degistir(icerik)
    return icerik


def _kural0(icerik: dict[str, Any]) -> dict[str, Any]:
    return _bul(icerik, "genel_kurul.ilan_en_az_gun")


def _sil(sozluk: dict[str, Any], ad: str) -> None:
    del sozluk[ad]


_BOZUK_ORNEKLER = {
    "zorunlu_ust_alan_yok": lambda i: _sil(i, "korpus_teyit"),
    "tanimsiz_ust_alan": lambda i: i.update(fazla=1),
    "paket_bicimi": lambda i: i.update(paket="OAB-2023"),
    "rev_sifir": lambda i: i.update(rev=0),
    "sema_surumu": lambda i: i.update(sema_surumu=2),
    "bos_kurallar": lambda i: i.update(kurallar=[]),
    "kural_alani_yok": lambda i: _sil(_kural0(i), "giris"),
    "kural_fazla_alan": lambda i: _kural0(i).update(fazla=True),
    "birim_disi": lambda i: _kural0(i).update(birim="saat"),
    "karsilastirma_disi": lambda i: _kural0(i).update(karsilastirma="yaklasik"),
    "tur_disi": lambda i: _kural0(i).update(tur="bilgi"),
    "deger_serbest_metin": lambda i: _kural0(i).update(deger="on bes"),
    "deger_null": lambda i: _kural0(i).update(deger=None),
    "deger_bos_liste": lambda i: _kural0(i).update(deger=[]),
    "deger_liste_yinelenen": lambda i: _kural0(i).update(deger=["VELI", "VELI"]),
    "deger_liste_kucuk_harf": lambda i: _kural0(i).update(deger=["veli"]),
    "oran_tamsayi": lambda i: _bul(i, "arz_bedeli.kira_oran").update(deger=3),
    "oran_tablo_tamsayi": lambda i: _bul(i, "pay_dagitimi.genel").update(deger={"birlik": 1}),
    "kimlik_alan_disi": lambda i: _kural0(i).update(id="kulup.ad"),
    "kimlik_iki_nokta": lambda i: _kural0(i).update(id="genel_kurul.a.b"),
    "kimlik_buyuk_harf": lambda i: _kural0(i).update(id="genel_kurul.Ilan"),
    "capa_bicimi": lambda i: _kural0(i)["madde"].update(capa="madde-9"),
    "bent_fikrasiz": lambda i: _kural0(i).update(madde={"capa": f"{Y}#madde-9", "bent": "a"}),
    "alt_bent_bentsiz": lambda i: _kural0(i).update(
        madde={"capa": f"{Y}#madde-9", "fikra": "1", "alt_bent": "1"}
    ),
    "fikra_bicimi_disi": lambda i: _kural0(i)["madde"].update(fikra_bicimi="serbest"),
    "tarih_bicimi": lambda i: _kural0(i)["yururluk"].update(baslangic="2012-02-09"),
    "bitis_alani_yok": lambda i: _sil(_kural0(i)["yururluk"], "bitis"),
    "faz_disi": lambda i: _kural0(i).update(giris="F9"),
    "eksik_veri_disi": lambda i: _kural0(i).update(eksik_veri="yok"),
    "toplu_gerekce_metin": lambda i: _kural0(i).update(toplu_gerekce="evet"),
    "kosul_anahtari_disi": lambda i: _kural0(i).update(kosul={"okul.tur": ["A"]}),
    "kosul_degeri_disi": lambda i: _kural0(i).update(kosul={"okul.kantin": ["KIRALIK"]}),
    "kosul_bos": lambda i: _kural0(i).update(kosul={"okul.kantin": []}),
    "kosul_yinelenen": lambda i: _kural0(i).update(
        kosul={"okul.kantin": ["KANTIN_YOK", "KANTIN_YOK"]}
    ),
    "uyaride_metin_yok": lambda i: _sil(_kural0(i), "uyari_metni"),
    "uyarida_sert_gerekcesi": lambda i: _kural0(i).update(sert_gerekcesi="hesap_butunlugu"),
    "lafizda_yorum": lambda i: _kural0(i).update(yorum="not"),
    "lafizda_karar": lambda i: _kural0(i).update(karar={"kimlik": "A-2", "tarih": "31.10.2026"}),
    "karar_kimlik_bicimi": lambda i: _bul(i, "denetleme_kurulu.yk_uyesi_olamaz")["karar"].update(
        kimlik="a2"
    ),
    "degisiklik_turu_disi": lambda i: i["degisiklikler"][0].update(tur="silme"),
}


@pytest.mark.parametrize("ad", sorted(_BOZUK_ORNEKLER))
def test_kucuk_dogrulayici_jsonschema_ile_ayni_sonucu_verir(ad: str) -> None:
    """Plan F1c kararları: açılıştaki doğrulayıcı `jsonschema`'nın verdiği sonucu verir."""
    icerik = _boz(_BOZUK_ORNEKLER[ad])
    jsonschema_hatali = bool(list(jsonschema.Draft202012Validator(SEMA).iter_errors(icerik)))
    assert jsonschema_hatali is True
    assert bool(sema_hatalari(icerik, SEMA)) is jsonschema_hatali


@pytest.mark.parametrize(
    "ornek",
    [1, 1.0, True, None, "0.03", [], {}, {"a": 1}, {"a": {"b": "0.1"}}, ["A", "A"], ["A"]],
)
def test_kucuk_dogrulayici_deger_tanimini_jsonschema_gibi_okur(ornek: Any) -> None:
    sema = {**SEMA, "$ref": "#/$defs/deger"}
    for anahtar in ("type", "additionalProperties", "required", "properties"):
        sema.pop(anahtar)
    beklenen = bool(list(jsonschema.Draft202012Validator(sema).iter_errors(ornek)))
    assert bool(sema_hatalari(ornek, sema)) is beklenen


@pytest.mark.parametrize(
    "sema",
    [{"oneOf": []}, {"format": "date"}, {"$ref": "http://dis/kaynak"}, {"type": "tamsayi"}],
)
def test_dogrulayici_tanimadigi_semayi_reddeder(sema: dict[str, Any]) -> None:
    """Şemaya eklenen yeni anahtar sessizce denetimsiz kalmaz."""
    with pytest.raises(SemaHatasi):
        sema_hatalari({"a": 1}, sema)


def test_jsonschema_uretim_bagimliligi_degil() -> None:
    backend = Path(yk.__file__).resolve().parents[3]
    assert "jsonschema" not in (backend / "requirements.txt").read_text(encoding="utf-8")
    for yol in (backend / "apps" / "oab" / "kurallar").glob("*.py"):
        assert "import jsonschema" not in yol.read_text(encoding="utf-8"), yol


def test_ondalik_dize_kayan_nokta_yok() -> None:
    assert denetimler._kayan_noktalar(R1, "$") == []
    for kid, deger in (
        ("arz_bedeli.kira_oran", 0.03),
        ("pay_dagitimi.genel", {"birlik": 0.8, "ilce": 0.1, "il": 0.1}),
    ):
        icerik = _kopya()
        _bul(icerik, kid)["deger"] = deger
        assert _d1(icerik)
    # `1.0` şemada tamsayı sayılır; kayan nokta denetimi yine yakalar.
    icerik = _kopya()
    _kural0(icerik)["deger"] = 15.0
    assert any("kayan nokta" in satir for satir in _d1(icerik))


def test_sert_kuralda_gerekce_zorunlu() -> None:
    icerik = _kopya()
    del _bul(icerik, "genel_kurul.yeter_sayi_taban")["sert_gerekcesi"]
    assert _d1(icerik)
    assert {k["sert_gerekcesi"] for k in R1["kurallar"] if k["tur"] == "sert"} == {HB, HD, HG, KK}


def test_kullanici_karari_kuralinda_karar_zorunlu() -> None:
    icerik = _kopya()
    del _bul(icerik, "denetleme_kurulu.yk_uyesi_olamaz")["karar"]
    assert _d1(icerik)


def test_yorum_kuralinda_yorum_zorunlu() -> None:
    icerik = _kopya()
    del _bul(icerik, "yonetim_kurulu.gorev_bolumu_gun")["yorum"]
    assert _d1(icerik)


def test_davranis_fazi_giristen_once_olamaz() -> None:
    icerik = _kopya()
    k = _kural0(icerik)
    k["giris"], k["davranis_fazi"] = "F3", "F2"
    assert any("davranis_fazi" in satir for satir in _d1(icerik))


def test_takvimde_olmayan_tarih_reddedilir() -> None:
    icerik = _kopya()
    _kural0(icerik)["yururluk"]["baslangic"] = "31.02.2012"
    assert any("takvimde olmayan" in satir for satir in _d1(icerik))


def test_tanimsiz_yer_tutucu_reddedilir() -> None:
    icerik = _kopya()
    _kural0(icerik)["uyari_metni"] = "En az {sinir} gün."
    assert any("yer tutucu" in satir for satir in _d1(icerik))


def test_kosul_anahtar_ve_degerleri_sozlukte() -> None:
    sozluk = SEMA["$defs"]["kosul"]["properties"]
    assert set(sozluk) == {
        "okul.kademe",
        "okul.yerlesim_turu",
        "okul.kantin",
        "okul.personel",
        "etkinlik.duzenleyen",
        "personel.sozlesme_turu",
    }
    for k in R1["kurallar"]:
        for anahtar, degerler in k.get("kosul", {}).items():
            assert set(degerler) <= set(sozluk[anahtar]["items"]["enum"]), k["id"]


@pytest.mark.parametrize(
    ("anahtar", "enum"),
    [
        ("okul.kademe", SchoolLevel),
        ("okul.yerlesim_turu", SettlementType),
        ("okul.kantin", CanteenMode),
        ("okul.personel", StaffingMode),
    ],
)
def test_kosul_degerleri_okul_karti_enumlariyla_ayni(anahtar: str, enum: Any) -> None:
    assert set(SEMA["$defs"]["kosul"]["properties"][anahtar]["items"]["enum"]) == set(enum.values)


# ======================================================================= D2


def test_kimlik_bicimi_ve_tekillik() -> None:
    assert denetimler.d2_kimlik(R1) == []
    icerik = _kopya()
    icerik["kurallar"].append(deepcopy(_kural0(icerik)))
    assert any("aynı aralıkla" in satir for satir in denetimler.d2_kimlik(icerik))


def _ikinci_kayit(icerik: dict[str, Any], baslangic: str, deger: Any = 20) -> dict[str, Any]:
    kayit = deepcopy(_kural0(icerik))
    kayit["yururluk"] = {"baslangic": baslangic, "bitis": None}
    kayit["deger"] = deger
    icerik["kurallar"].append(kayit)
    return kayit


def test_yururluk_araliklari_cakismaz() -> None:
    icerik = _kopya()
    _ikinci_kayit(icerik, "01.01.2025")
    assert any("çakışıyor" in s for s in denetimler.d2_kimlik(icerik))
    _kural0(icerik)["yururluk"]["bitis"] = "31.12.2024"
    assert not any("çakışıyor" in s for s in denetimler.d2_kimlik(icerik))
    _kural0(icerik)["yururluk"]["bitis"] = "01.01.2025"
    assert any("çakışıyor" in s for s in denetimler.d2_kimlik(icerik))


def _r2(degistir: Any, *beyan: tuple[str, str]) -> dict[str, Any]:
    icerik = _kopya()
    icerik["rev"] = 2
    degistir(icerik)
    icerik["degisiklikler"] = [{"id": kid, "tur": tur} for kid, tur in beyan]
    return icerik


def test_yayimlanmis_kimlik_silinmemis() -> None:
    def sil(icerik: dict[str, Any]) -> None:
        icerik["kurallar"] = [k for k in icerik["kurallar"] if k["id"] != "makbuz.cilt_yaprak"]

    assert any("silinmiş" in s for s in denetimler.d2_kimlik(_r2(sil), R1))


def test_duzeltme_kaydi_ayni_araligin_yerini_alir() -> None:
    """Tasarım §6.2-3a: aynı aralıkla düzeltme çakışma sayılmaz, beyansızı reddedilir."""

    def duzelt(icerik: dict[str, Any]) -> None:
        _kural0(icerik)["deger"] = 16

    kid = "genel_kurul.ilan_en_az_gun"
    assert denetimler.d2_kimlik(_r2(duzelt, (kid, "duzeltme")), R1) == []
    assert any("beyanı tutmuyor" in s for s in denetimler.d2_kimlik(_r2(duzelt), R1))
    assert any(
        "beyanı tutmuyor" in s for s in denetimler.d2_kimlik(_r2(duzelt, (kid, "ekleme")), R1)
    )


def test_degisiklikler_onceki_revizyonla_tutarli() -> None:
    kid = "genel_kurul.ilan_en_az_gun"

    def deger_degisti(icerik: dict[str, Any]) -> None:
        _kural0(icerik)["yururluk"]["bitis"] = "31.12.2024"
        _ikinci_kayit(icerik, "01.01.2025")

    def bitti(icerik: dict[str, Any]) -> None:
        _kural0(icerik)["yururluk"]["bitis"] = "31.12.2024"

    def eklendi(icerik: dict[str, Any]) -> None:
        yeni = deepcopy(_kural0(icerik))
        yeni["id"] = "genel_kurul.yeni_kural"
        icerik["kurallar"].append(yeni)

    assert denetimler.d2_kimlik(_r2(deger_degisti, (kid, "deger_degisikligi")), R1) == []
    assert denetimler.d2_kimlik(_r2(bitti, (kid, "bitis")), R1) == []
    assert denetimler.d2_kimlik(_r2(eklendi, ("genel_kurul.yeni_kural", "ekleme")), R1) == []
    # Değişiklik yokken beyan ve revizyon atlama.
    assert any(
        "beyanı tutmuyor" in s
        for s in denetimler.d2_kimlik(_r2(lambda _: None, (kid, "bitis")), R1)
    )
    atlayan = _r2(lambda _: None)
    atlayan["rev"] = 3
    assert any("bir fazlası" in s for s in denetimler.d2_kimlik(atlayan, R1))
    # r1'de bütün kimlikler `ekleme` beyan edilir; pakette olmayan kimlik beyan edilemez.
    eksik_beyan = _kopya()
    eksik_beyan["degisiklikler"].pop()
    assert denetimler.d2_kimlik(eksik_beyan)
    yabanci = _kopya()
    yabanci["degisiklikler"].append({"id": "kantin.yok", "tur": "ekleme"})
    assert any("olmayan kimlik" in s for s in denetimler.d2_kimlik(yabanci))


# ======================================================================= D3


@pytest.mark.parametrize("kid", _deger_parametreleri(sorted(KURALLAR)))
def test_atif_kilidi(kid: str) -> None:
    k = KURALLAR[kid]
    for madde in atif_ortak.butun_maddeler(k):
        assert atif_ortak.d3_capa_hatalari(madde, k, KORPUS) == [], madde


def _atif_kurali() -> dict[str, Any]:
    return deepcopy(_kural0(R1))


def test_bozuk_capa_yakalanir() -> None:
    hatalar = atif_ortak.d3_capa_hatalari({"capa": f"{Y}#madde-99"}, _atif_kurali(), KORPUS)
    assert any("çapa yok" in satir for satir in hatalar)
    assert atif_ortak.d3_capa_hatalari({"capa": "yok.md#madde-1"}, _atif_kurali(), KORPUS)


def test_bilgi_dizini_atfi_reddedilir(tmp_path: Path) -> None:
    (tmp_path / "bilgi").mkdir()
    (tmp_path / "bilgi" / "ozelge.md").write_text('<a id="madde-1"></a>\n', "utf-8")
    hatalar = atif_ortak.d3_capa_hatalari(
        {"capa": "bilgi/ozelge.md#madde-1"}, _atif_kurali(), tmp_path
    )
    assert any("bilgi/" in satir for satir in hatalar)


def test_draft_dosya_atfi_reddedilir(tmp_path: Path) -> None:
    (tmp_path / ".draft-x.md").write_text('<a id="madde-1"></a>\n', "utf-8")
    hatalar = atif_ortak.d3_capa_hatalari({"capa": ".draft-x.md#madde-1"}, _atif_kurali(), tmp_path)
    assert any("taslak" in satir for satir in hatalar)


def test_denetim_rehberi_atfi_reddedilir(tmp_path: Path) -> None:
    (tmp_path / "r.md").write_text(
        '---\nbelge-turu: "denetim rehberi"\n---\n<a id="m"></a>\n', "utf-8"
    )
    assert any(
        "denetim rehberi" in s
        for s in atif_ortak.d3_capa_hatalari({"capa": "r.md#m"}, _atif_kurali(), tmp_path)
    )


def test_yururlukten_kalkmis_metinde_bitis_zorunlu(tmp_path: Path) -> None:
    (tmp_path / "m.md").write_text('---\nyururlukte: false\n---\n<a id="m"></a>\n', "utf-8")
    kural_ = _atif_kurali()
    assert atif_ortak.d3_capa_hatalari({"capa": "m.md#m"}, kural_, tmp_path)
    kural_["yururluk"]["bitis"] = "31.12.2024"
    assert atif_ortak.d3_capa_hatalari({"capa": "m.md#m"}, kural_, tmp_path) == []


def test_kullanici_karari_kimligi_listede() -> None:
    kararlar = {k["karar"]["kimlik"] for k in R1["kurallar"] if "karar" in k}
    assert kararlar == {"A-2", "KE-15"}
    assert kararlar <= KULLANICI_KARARLARI
    assert "X-9" not in KULLANICI_KARARLARI


# ======================================================================= D4


@pytest.mark.parametrize("kid", sorted(KURALLAR), ids=str)
def test_fikra_bent_kilidi(kid: str) -> None:
    for madde in atif_ortak.butun_maddeler(KURALLAR[kid]):
        assert atif_ortak.d4_fikra_hatalari(madde, KORPUS) == [], madde


def test_cok_fikrali_maddede_fikra_zorunlu() -> None:
    hatalar = atif_ortak.d4_fikra_hatalari({"capa": f"{Y}#madde-9"}, KORPUS)
    assert any("fıkra boş olamaz" in satir for satir in hatalar)
    assert atif_ortak.d4_fikra_hatalari({"capa": f"{Y}#madde-9", "fikra": "7"}, KORPUS)
    ek2 = _madde("E2 7")
    assert any("fıkra boş olamaz" in s for s in atif_ortak.d4_fikra_hatalari(ek2, KORPUS))


def test_paragraf_bicimli_fikra() -> None:
    assert atif_ortak.d4_fikra_hatalari(_madde("E2 7/1"), KORPUS) == []
    assert atif_ortak.d4_fikra_hatalari(_madde("E2 7/5"), KORPUS) == []
    # Başlık satırı (`###`) sayılmaz: 6. paragraf yoktur.
    assert any("paragraf yok" in s for s in atif_ortak.d4_fikra_hatalari(_madde("E2 7/6"), KORPUS))
    dosya = "4857-is-kanunu.md"
    md17 = (KORPUS / dosya).read_text("utf-8")
    govde = atif_ortak.madde_govdesi(md17, "madde-17")
    assert govde is not None
    bolumler = atif_ortak.paragraflar(govde)
    # Bent satırları ve "feshedilmiş sayılır." ikinci paragraftadır.
    assert "İş sözleşmeleri;" in bolumler[1] and "feshedilmiş sayılır." in bolumler[1]
    for ad, fikra in (("madde-17", "2"), ("madde-17", "3"), ("madde-53", "4")):
        assert (
            atif_ortak.d4_fikra_hatalari(
                {"capa": f"{dosya}#{ad}", "fikra": fikra, "fikra_bicimi": "paragraf"}, KORPUS
            )
            == []
        )
    assert (
        atif_ortak.d4_fikra_hatalari(
            {"capa": f"{dosya}#madde-17", "fikra": "2", "bent": "d", "fikra_bicimi": "paragraf"},
            KORPUS,
        )
        == []
    )


def test_mulga_fikraya_atif_yakalanir() -> None:
    hatalar = atif_ortak.d4_fikra_hatalari({"capa": f"{Y}#madde-20", "fikra": "10"}, KORPUS)
    assert any("mülga" in satir for satir in hatalar)


def _sentetik(tmp_path: Path, govde: str) -> Path:
    (tmp_path / "s.md").write_text(
        f'<a id="madde-1"></a>\n{govde}\n<a id="madde-2"></a>\n', "utf-8"
    )
    return tmp_path


def test_mulga_bende_atif_yakalanir(tmp_path: Path) -> None:
    kok = _sentetik(tmp_path, "MADDE 1 – (1) Giriş;\n\na) (Mülga:RG-1/1/2020-1)\n\nb) Yürürlükte.")
    hatalar = atif_ortak.d4_fikra_hatalari({"capa": "s.md#madde-1", "fikra": "1", "bent": "a"}, kok)
    assert any("mülga" in satir for satir in hatalar)
    assert (
        atif_ortak.d4_fikra_hatalari({"capa": "s.md#madde-1", "fikra": "1", "bent": "b"}, kok) == []
    )


def test_bent_kendi_fikrasinda_aranir(tmp_path: Path) -> None:
    kok = _sentetik(tmp_path, "MADDE 1 – (1) Giriş;\n\na) Birinci.\n\n(2) İkinci fıkra.")
    assert (
        atif_ortak.d4_fikra_hatalari({"capa": "s.md#madde-1", "fikra": "1", "bent": "a"}, kok) == []
    )
    assert atif_ortak.d4_fikra_hatalari({"capa": "s.md#madde-1", "fikra": "2", "bent": "a"}, kok)


def test_alt_bent_satir_icinde_aranir() -> None:
    temel = {"capa": f"{Y}#madde-17", "fikra": "1", "bent": "b"}
    assert atif_ortak.d4_fikra_hatalari({**temel, "alt_bent": "3"}, KORPUS) == []
    assert atif_ortak.d4_fikra_hatalari({**temel, "alt_bent": "9"}, KORPUS)


OSAY = "okul-servis-araclari-yonetmeligi.md#madde-5"


def test_yd_bende_atif_yakalanir() -> None:
    hatalar = atif_ortak.d4_fikra_hatalari({"capa": OSAY, "fikra": "2", "bent": "b"}, KORPUS)
    assert any("yürütmesi durdurulan" in satir for satir in hatalar)


def test_yd_ibareye_atif_yakalanir() -> None:
    dosya = _KISA_DOSYA["E2"][0]
    hatalar = atif_ortak.d4_fikra_hatalari(
        {"capa": f"{dosya}#ozel-sartlar-madde-1", "fikra": "1", "fikra_bicimi": "paragraf"}, KORPUS
    )
    assert any("yürütmesi durdurulan" in satir for satir in hatalar)


def test_yeniden_duzenlenen_iptal_bent_gecer(tmp_path: Path) -> None:
    assert atif_ortak.d4_fikra_hatalari({"capa": OSAY, "fikra": "2", "bent": "d"}, KORPUS) == []
    kok = _sentetik(tmp_path, "MADDE 1 – (1) Giriş;\n\na) (Danıştay kararı ile iptal bent) Eski.")
    hatalar = atif_ortak.d4_fikra_hatalari({"capa": "s.md#madde-1", "fikra": "1", "bent": "a"}, kok)
    assert any("iptal" in satir for satir in hatalar)


# ======================================================================= D5


def test_yeter_sayi_tabani_bilesimle_tutarli() -> None:
    assert denetimler.d5_tutarlilik(R1) == []
    icerik = _kopya()
    _bul(icerik, "genel_kurul.yeter_sayi_taban")["deger"] = 15
    assert any("yeter_sayi_taban" in s for s in denetimler.d5_tutarlilik(icerik))
    icerik = _kopya()
    _bul(icerik, "yonetim_kurulu.asil_uye")["deger"] = 6
    assert any("yeter_sayi_taban" in s for s in denetimler.d5_tutarlilik(icerik))


def test_koltuklar_bilesimle_tutarli() -> None:
    icerik = _kopya()
    _bul(icerik, "denetleme_kurulu.koltuklar")["deger"]["OGRETMEN"]["ASIL"] = 3
    assert any("koltuklar" in s for s in denetimler.d5_tutarlilik(icerik))


def test_pay_tablolari_toplami_bir() -> None:
    icerik = _kopya()
    _bul(icerik, "pay_dagitimi.genel")["deger"]["il"] = "0.11"
    assert any("pay_dagitimi.genel" in s for s in denetimler.d5_tutarlilik(icerik))


def test_arz_vadeleri_sirali() -> None:
    icerik = _kopya()
    _bul(icerik, "arz_bedeli.sozlesme_vade_gunu")["deger"] = 20
    assert any("vade" in s for s in denetimler.d5_tutarlilik(icerik))


def test_yeter_sayi_carpani_kucuk_okul_carpanindan_buyuk() -> None:
    icerik = _kopya()
    _bul(icerik, "genel_kurul.yeter_sayi_carpan")["deger"] = 2
    assert any("carpan" in s for s in denetimler.d5_tutarlilik(icerik))


def test_ek3_azami_toplami_25() -> None:
    """EK-3 kuralı F6'da gelir; o güne dek denetim atlanır, gelince dişlidir."""
    assert "servis.ek3_kriter_azami_puan" not in KURALLAR
    icerik = _kopya()
    yeni = deepcopy(_kural0(icerik))
    yeni["id"] = "servis.ek3_kriter_azami_puan"
    yeni["deger"] = {"a": 5, "b": 5, "c": 5, "d": 5, "e": 5}
    icerik["kurallar"].append(yeni)
    assert denetimler.d5_tutarlilik(icerik) == []
    yeni["deger"]["e"] = 6
    assert any("25" in s for s in denetimler.d5_tutarlilik(icerik))


# ======================================================================= D6


def test_isaretler_pyproject_markers_listesinde(pytestconfig: pytest.Config) -> None:
    """Tasarım §6.3 D6: iki işaret kayıtlıdır; kayıtsız işaret toplama hatasıdır."""
    kayitli = {satir.split(":", 1)[0] for satir in pytestconfig.getini("markers")}
    assert {"kural_deger", "kural_davranis"} <= kayitli
    assert pytestconfig.getini("strict_markers") is True


def _kural_isaretleri() -> dict[str, set[str]]:
    return isaret_ortak.kural_isaretleri(isaret_ortak.kural_test_modulleri())


def _backend() -> Path:
    return Path(yk.__file__).resolve().parents[3]


def test_koddaki_kural_cagrilari_pakette() -> None:
    kimlikler, okunamayan = isaret_ortak.koddaki_kural_cagrilari(
        [_backend() / "apps", _backend() / "shared"]
    )
    assert okunamayan == []
    assert kimlikler  # okul kartı bilgisi bugünden çağırır
    assert kimlikler <= set(KURALLAR), kimlikler - set(KURALLAR)


def test_kural_cagrisi_taramasi_kimligi_okur() -> None:
    kaynak = (
        'SABIT = "bagis.a"\n'
        'x = kural("genel_kurul.b")\n'
        'y = erisim.denetle("harcama.c", 3)\n'
        "z = bilgi_notu(SABIT)\n"
        "t = kural(degisken)\n"
    )
    kimlikler, sabitsiz = isaret_ortak.kural_cagrilari(kaynak)
    assert kimlikler == {"bagis.a", "genel_kurul.b", "harcama.c"}
    assert sabitsiz == [5]


def test_her_kuralin_deger_testi_var() -> None:
    isaretler = _kural_isaretleri()
    assert isaretler["kural_deger"] == set(KURALLAR)
    assert isaretler["kural_davranis"] <= set(KURALLAR)


def test_davranis_fazi_gelen_kuralin_davranis_testi_var() -> None:
    fazlar = {k["id"]: k["davranis_fazi"] for k in R1["kurallar"]}
    gelenler = faz_ortak.fazi_gelenler(fazlar)
    assert gelenler <= _kural_isaretleri()["kural_davranis"]


@pytest.mark.parametrize(
    ("gecerli", "beklenen"),
    [
        ("F1b", {"F1b_kurali"}),
        ("F1c", {"F1b_kurali", "F1c_kurali"}),
        ("F8+", {"F1b_kurali", "F1c_kurali", "F2_kurali", "F8+_kurali"}),
    ],
)
def test_fazi_gelenler_gecerli_faza_esit_ya_da_kucuk_olanlardir(
    gecerli: str, beklenen: set[str]
) -> None:
    """Tasarım §6.3 D6: `davranis_fazi` geçerli faza eşit ya da küçük olan kural istenir."""
    fazlar = {"F1b_kurali": "F1b", "F1c_kurali": "F1c", "F2_kurali": "F2", "F8+_kurali": "F8+"}
    assert faz_ortak.fazi_gelenler(fazlar, gecerli=gecerli) == beklenen


def test_bilinmeyen_faz_yazim_hatasidir() -> None:
    """Yanlış yazılmış faz "henüz gelmedi" sayılıp testi sessizce kapatmaz."""
    with pytest.raises(ValueError, match="F9"):
        faz_ortak.fazi_gelenler({"kural": "F9"})


def test_gecerli_faz_sirada_tanimlidir() -> None:
    assert faz_ortak.GECERLI_FAZ in faz_ortak.FAZ_SIRASI
    assert len(set(faz_ortak.FAZ_SIRASI)) == len(faz_ortak.FAZ_SIRASI)


def test_f1c_kurallarinin_davranis_testi_tamam() -> None:
    """F1c'nin 6. adımının "Bitti" ölçütü (plan F1c-6): geçerli faz F1c olunca istenen 36 kuralın
    hepsinin davranış testi vardır. `GECERLI_FAZ` evrakla birlikte 10. adımda F1c olur; o gün
    `test_davranis_fazi_gelen_kuralin_davranis_testi_var` bu kümeyi kendiliğinden ister. 8. adımda
    karar defterinin noter tasdiki kurala bağlandı (36 → 37; plan F1c 8. adım notları)."""
    fazlar = {k["id"]: k["davranis_fazi"] for k in R1["kurallar"]}
    gelenler = faz_ortak.fazi_gelenler(fazlar, gecerli="F1c")
    assert len(gelenler) == 37
    assert gelenler - _kural_isaretleri()["kural_davranis"] == set()


def test_davranis_kolu_eksik_isarette_dislidir() -> None:
    """Davranış kolu dişlidir: işareti olmayan bir F1c kuralı kümeden düşünce eksik görünür."""
    fazlar = {k["id"]: k["davranis_fazi"] for k in R1["kurallar"]}
    gelenler = faz_ortak.fazi_gelenler(fazlar, gecerli="F1c")
    isaretli = _kural_isaretleri()["kural_davranis"] - {"temsilci.pay_dagitim_komisyonu"}
    assert gelenler - isaretli == {"temsilci.pay_dagitim_komisyonu"}


def _sahte_modul() -> ModuleType:
    modul = ModuleType("sahte")

    @pytest.mark.kural_davranis("a.b")
    def test_bir() -> None: ...

    @pytest.mark.parametrize(
        "x", [pytest.param("c", marks=pytest.mark.kural_deger("c.d")), pytest.param("e")]
    )
    def test_iki(x: str) -> None: ...

    def test_uc() -> None: ...

    vars(modul).update(test_bir=test_bir, test_iki=test_iki, test_uc=test_uc)
    return modul


def test_isaret_taramasi_parametre_isaretlerini_gorur() -> None:
    assert isaret_ortak.modul_isaretleri(_sahte_modul()) == {
        ("kural_davranis", "a.b"),
        ("kural_deger", "c.d"),
    }


def test_kimliksiz_isaret_yazim_hatasidir() -> None:
    modul = ModuleType("sahte")

    @pytest.mark.kural_deger()
    def test_bos() -> None: ...

    vars(modul).update(test_bos=test_bos)
    with pytest.raises(ValueError, match="tek bir kural kimliği"):
        isaret_ortak.modul_isaretleri(modul)


# ======================================================================= D7


def test_dagitilan_paket_ozeti() -> None:
    manifest = json.loads((yk.PAKETLER_DIZINI / yk.MANIFEST_ADI).read_text("utf-8"))
    ham = (yk.PAKETLER_DIZINI / DOSYA).read_bytes()
    assert manifest["paketler"] == [{"dosya": DOSYA, "sha256": hashlib.sha256(ham).hexdigest()}]
    sema_ham = (yk.PAKETLER_DIZINI / yk.SEMA_ADI).read_bytes()
    assert manifest["sema_sha256"] == hashlib.sha256(sema_ham).hexdigest()
    assert yk.yukle().yuklendi is True


def test_ozeti_tutmayan_paket_yuklenmez(tmp_path: Path) -> None:
    dizin = _paket_dizini(tmp_path, _kopya())
    (dizin / DOSYA).write_bytes((dizin / DOSYA).read_bytes() + b" ")
    durum = yk.yukle(dizin)
    assert durum.yuklendi is False and durum.en_yeni is None
    assert any("D7" in satir for satir in durum.hatalar)


def test_ozeti_tutmayan_sema_yuklenmez(tmp_path: Path) -> None:
    """Şema da MANIFEST kapsamındadır: gevşetilmiş şema D1'i sessizce açamaz."""
    dizin = _paket_dizini(tmp_path, _kopya())
    (dizin / yk.SEMA_ADI).write_bytes((dizin / yk.SEMA_ADI).read_bytes() + b" ")
    durum = yk.yukle(dizin)
    assert durum.yuklendi is False
    assert any(yk.SEMA_ADI in satir and "D7" in satir for satir in durum.hatalar)


def test_sema_ozeti_olmayan_manifest_yuklenmez(tmp_path: Path) -> None:
    dizin = _paket_dizini(tmp_path, _kopya())
    manifest = json.loads((dizin / yk.MANIFEST_ADI).read_text("utf-8"))
    del manifest["sema_sha256"]
    (dizin / yk.MANIFEST_ADI).write_text(json.dumps(manifest), "utf-8")
    assert yk.yukle(dizin).yuklendi is False


def test_manifestte_olmayan_paket_yuklenmez(tmp_path: Path) -> None:
    dizin = _paket_dizini(tmp_path, _kopya())
    (dizin / "OAB-2023.12.r2.json").write_text("{}", "utf-8")
    assert yk.yukle(dizin).yuklendi is False


def test_dosya_adi_icerikle_tutmali(tmp_path: Path) -> None:
    dizin = _paket_dizini(tmp_path, _kopya())
    (dizin / DOSYA).rename(dizin / "OAB-2023.12.r5.json")
    manifest = json.loads((dizin / yk.MANIFEST_ADI).read_text("utf-8"))
    manifest["paketler"][0]["dosya"] = "OAB-2023.12.r5.json"
    (dizin / yk.MANIFEST_ADI).write_text(json.dumps(manifest), "utf-8")
    assert any("dosya adı" in s for s in yk.yukle(dizin).hatalar)


@pytest.mark.parametrize(
    ("ham", "ileti"),
    [(b'{"a": 1, "a": 2}', "Yinelenen"), (b'{"a": NaN}', "olmayan sayı")],
)
def test_kati_json(ham: bytes, ileti: str) -> None:
    with pytest.raises(ValueError, match=ileti):
        yk.json_coz(ham)


def test_kanonik_icerik_ozeti_anahtar_sirasindan_bagimsiz() -> None:
    """`content_sha256` kanonik JSON'un özetidir: `JSONField` gidiş-dönüşü baytı korumaz."""
    ters = dict(reversed(list(R1.items())))
    assert yk.icerik_ozeti(ters) == yk.icerik_ozeti(R1)
    degisik = _kopya()
    degisik["rev"] = 2
    assert yk.icerik_ozeti(degisik) != yk.icerik_ozeti(R1)


def test_acilista_bozuk_revizyon_butun_paketi_kapatir(tmp_path: Path) -> None:
    """Herhangi bir revizyon denetimden geçemezse yazma kapalı (fail-closed)."""
    bozuk = _kopya()
    bozuk["rev"] = 2
    bozuk["degisiklikler"] = []
    _bul(bozuk, "genel_kurul.yeter_sayi_taban")["deger"] = 15
    durum = yk.yukle(_paket_dizini(tmp_path, _kopya(), bozuk))
    assert durum.yuklendi is False
    assert any("(D2)" in s for s in durum.hatalar) and any("(D5)" in s for s in durum.hatalar)


def test_semaya_uyup_d5te_patlayan_deger_programi_dusurmez(tmp_path: Path) -> None:
    """`koltuklar.deger=5` şemadan geçer, D5 okurken `AttributeError` verir: durum "yüklenemedi"."""
    bozuk = _kopya()
    _bul(bozuk, "denetleme_kurulu.koltuklar")["deger"] = 5
    assert _d1(bozuk) == []
    durum = yk.yukle(_paket_dizini(tmp_path, bozuk))
    assert durum.yuklendi is False and durum.en_yeni is None
    assert any("AttributeError" in satir for satir in durum.hatalar)


@pytest.mark.parametrize(
    "sema",
    [
        pytest.param([], id="dizi"),
        pytest.param({"properties": {"paket": {"pattern": "("}}}, id="bozuk_pattern"),
    ],
)
def test_bozuk_sema_programi_dusurmez(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sema: Any
) -> None:
    """Özeti tutan ama okunamayan şema: açılış hata yükseltmez, durum "yüklenemedi"."""
    monkeypatch.setattr(yk._Onbellek, "durum", None)
    durum = yk.ac(_paket_dizini(tmp_path, _kopya(), sema=sema))
    assert durum.yuklendi is False
    assert durum.hatalar and "okunamadı" in durum.hatalar[0]


def test_en_yeni_revizyon_okunur(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    r2 = _r2(lambda i: _kural0(i).update(deger=16), ("genel_kurul.ilan_en_az_gun", "duzeltme"))
    monkeypatch.setattr(yk._Onbellek, "durum", yk.yukle(_paket_dizini(tmp_path, _kopya(), r2)))
    assert kural("genel_kurul.ilan_en_az_gun") == 16
    assert denetle("genel_kurul.ilan_en_az_gun", 20)["rev"] == 2


def test_gercek_acilis_ac_islevi_durumu_yeniler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(yk._Onbellek, "durum", None)
    with caplog.at_level("ERROR"):
        assert yk.ac(tmp_path).yuklendi is False
    assert "Kural paketi denetimi" in caplog.text
    assert yk.ac().yuklendi is True
    assert yk.durum().en_yeni is not None


# ======================================================================= D8


def _d8_sayilari() -> tuple[set[int], set[str]]:
    return isaret_ortak.paket_sayilari(R1["kurallar"])


def test_sabit_taramasi() -> None:
    tamsayilar, ondaliklar = _d8_sayilari()
    assert {4, 15, 16} <= tamsayilar and {"0.03", "0.80"} <= ondaliklar
    oab = _backend() / "apps" / "oab"
    assert isaret_ortak.oab_sabit_bulgulari(oab, tamsayilar, ondaliklar, izinli=set()) == []


def test_sabit_taramasi_kaliplari_yakalar() -> None:
    tamsayilar, ondaliklar = _d8_sayilari()
    kaynak = (
        'a = Decimal("0.03")\n'
        'b = "0.80"\n'
        "c = timedelta(days=15)\n"
        "d = taban * 4\n"
        "e = timedelta(days=9)\n"
        "f = x * 9\n"
    )
    assert isaret_ortak.sabit_bulgulari(kaynak, tamsayilar, ondaliklar) == [
        (1, '"0.03"'),
        (2, '"0.80"'),
        (3, "timedelta(days=15)"),
        (4, "* 4"),
    ]


def test_sabit_taramasi_izin_listesine_uyar(tmp_path: Path) -> None:
    (tmp_path / "servis.py").write_text("c = x * 4\n", "utf-8")
    tamsayilar, ondaliklar = _d8_sayilari()
    assert isaret_ortak.oab_sabit_bulgulari(tmp_path, tamsayilar, ondaliklar, set())
    assert (
        isaret_ortak.oab_sabit_bulgulari(tmp_path, tamsayilar, ondaliklar, {("servis.py", "* 4")})
        == []
    )


# ======================================================================= erişim


@pytest.fixture
def bozuk_paket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(yk._Onbellek, "durum", yk.yukle(tmp_path))


@pytest.mark.usefixtures("bozuk_paket")
def test_paket_yuklenemezse_yazma_kapali_okuma_acik() -> None:
    """D1: kural kullanan yazma durur, okuma (durum sorgusu) açık kalır."""
    for cagri in (
        lambda: kural("genel_kurul.ilan_en_az_gun"),
        lambda: denetle("genel_kurul.ilan_en_az_gun", 20),
        lambda: bilgi_notu("kantin.isletmede_vergi_uyarisi"),
    ):
        with pytest.raises(KuralPaketiKullanilamaz):
            cagri()
    with pytest.raises(KuralPaketiKullanilamaz):
        yazma_kapisi()
    assert yk.durum().yuklendi is False and yk.durum().hatalar


def _donem(icerik: dict[str, Any] | None = None) -> Any:
    return SimpleNamespace(rule_package=SimpleNamespace(content=icerik or _kopya()))


@pytest.mark.usefixtures("bozuk_paket")
def test_paket_yuklenemezse_donem_kopyasi_okunur() -> None:
    """Tasarım §6.2-4, D1 "okuma açık": dağıtılan dosya bozulsa da bağlı dönem kopyasıyla okunur."""
    gun = date(2026, 11, 9)
    kid = "genel_kurul.ilan_en_az_gun"
    donem = _donem()
    assert kural(kid, gun, donem) == 15
    sonuc = denetle(kid, 14, tarih=gun, donem=donem)
    assert (sonuc["durum"], sonuc["paket"], sonuc["rev"]) == ("uyari", "OAB-2023.12", 1)
    bilgi = bilgi_notu(
        "kantin.isletmede_vergi_uyarisi",
        tarih=gun,
        donem=donem,
        okul={"okul.kantin": "BIRLIKCE_ISLETILIYOR"},
    )
    assert bilgi is not None and bilgi["atif"] == "md. 23/3"


def test_yazma_kapisi_paket_yuklendiyse_aciktir() -> None:
    yazma_kapisi()


def test_bilinmeyen_kimlikte_yazma_kapali() -> None:
    with pytest.raises(BilinmeyenKural):
        kural("genel_kurul.yok")
    with pytest.raises(BilinmeyenKural):
        denetle("genel_kurul.yok", 1)
    assert BilinmeyenKural.status_code == 500
    assert KuralPaketiKullanilamaz.status_code == 503


def test_yururluk_disi_olayda_denetim_yok_bilgi_notu() -> None:
    once = date(2023, 11, 30)
    kid = "yonetim_kurulu.secilme_siniri"
    sonuc = denetle(kid, 9, tarih=once)
    assert sonuc["durum"] == "denetlenmedi"
    assert sonuc["mesaj"] == erisim.DENETLENMEDI_NOTU
    with pytest.raises(YururlukteDegerYok):
        kural(kid, tarih=once)
    # Değerin bugünkü hâliyle yürürlüğe girdiği gün denetlenir (sınırın iki yanı).
    assert denetle(kid, 9, tarih=date(2023, 12, 1))["durum"] == "uyari"


def _bitisli_paket(**alanlar: Any) -> dict[str, Any]:
    """İlan kuralı 31.12.2024'te biten sentetik içerik: yanlış gün hemen görünür."""
    icerik = _kopya()
    _kural0(icerik)["yururluk"]["bitis"] = "31.12.2024"
    _kural0(icerik).update(alanlar)
    return icerik


@pytest.mark.parametrize(
    "cagri",
    [
        pytest.param(lambda d: kural("genel_kurul.ilan_en_az_gun", donem=d), id="kural"),
        pytest.param(lambda d: denetle("genel_kurul.ilan_en_az_gun", 20, donem=d), id="denetle"),
        pytest.param(lambda d: bilgi_notu("kantin.isletmede_vergi_uyarisi", donem=d), id="bilgi"),
    ],
)
def test_donem_verilince_olay_tarihi_zorunlu(cagri: Any) -> None:
    """Tasarım §6.1 "Olay tarihi": dönem kuralı işlem anıyla sessizce hesaplanmaz."""
    with pytest.raises(OlayTarihiGerekli):
        cagri(_donem())


def test_donem_tarihsiz_cagrida_bilinmeyen_kimlik_once_gelir() -> None:
    with pytest.raises(BilinmeyenKural):
        kural("genel_kurul.yok", donem=_donem())


def test_tarihsiz_donemsiz_okuma_bugunu_kullanir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    icerik = _bitisli_paket()
    monkeypatch.setattr(yk._Onbellek, "durum", yk.yukle(_paket_dizini(tmp_path, icerik)))
    kid = "genel_kurul.ilan_en_az_gun"
    monkeypatch.setattr("django.utils.timezone.localdate", lambda: date(2024, 12, 31))
    assert kural(kid) == 15
    monkeypatch.setattr("django.utils.timezone.localdate", lambda: date(2025, 1, 1))
    with pytest.raises(YururlukteDegerYok):
        kural(kid)


def test_kuralin_olay_tarihi_alani_okunur() -> None:
    """`olay_tarihi` olayın adıdır; günü çağıran `olaylar` ile verir, kural o güne bakar."""
    icerik = _bitisli_paket(olay_tarihi="duyuru_gunu")
    assert _d1(icerik) == []
    donem = _donem(icerik)
    kid = "genel_kurul.ilan_en_az_gun"
    assert kural(kid, donem=donem, olaylar={"duyuru_gunu": date(2024, 12, 31)}) == 15
    with pytest.raises(YururlukteDegerYok):
        kural(kid, donem=donem, olaylar={"duyuru_gunu": date(2025, 1, 1)})
    sonuc = denetle(kid, 20, donem=donem, olaylar={"duyuru_gunu": date(2025, 1, 1)})
    assert sonuc["durum"] == "denetlenmedi"
    # Verilen tarih önceliklidir; olayın günü bilinmiyorsa dönemde hata, bugüne düşmez.
    assert kural(kid, date(2024, 1, 1), donem, olaylar={"duyuru_gunu": date(2025, 1, 1)}) == 15
    with pytest.raises(OlayTarihiGerekli):
        kural(kid, donem=donem, olaylar={"baska_gun": date(2024, 1, 1)})


def test_yururluk_bitisi_dahildir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    icerik = _kopya()
    _kural0(icerik)["yururluk"]["bitis"] = "31.12.2024"
    r2 = deepcopy(icerik)
    r2["rev"] = 1
    monkeypatch.setattr(yk._Onbellek, "durum", yk.yukle(_paket_dizini(tmp_path, r2)))
    kid = "genel_kurul.ilan_en_az_gun"
    assert kural(kid, tarih=date(2024, 12, 31)) == 15
    assert denetle(kid, 20, tarih=date(2025, 1, 1))["durum"] == "denetlenmedi"


def test_kullanici_karari_atfi_yonetmelik_geregi_demez() -> None:
    a2 = denetle("denetleme_kurulu.yk_uyesi_olamaz", False)
    assert a2["atif"] == "kullanıcı kararı A-2 (gerekçe md. 14/4)"
    ke15 = denetle("yonetim_kurulu.okul_muduru_uye_olamaz", False)
    assert ke15["atif"] == "kullanıcı kararı KE-15 (gerekçe md. 12/1, 27/2-3)"
    for sonuc in (a2, ke15):
        assert sonuc["dayanak_turu"] == "kullanici_karari"
        assert "Yönetmelik gereği" not in f"{sonuc['mesaj']} {sonuc['atif']}"


@pytest.mark.parametrize(
    ("kid", "beklenen"),
    [
        ("genel_kurul.ilan_en_az_gun", "md. 9/3"),
        ("genel_kurul.divan_uye_turleri", "md. 10/1-c"),
        ("temsilci.pay_dagitim_komisyonu", "md. 17/1-b-3"),
        ("temsilci.odul_disiplin_kurulu", "OKY md. 185/1-ç"),
        ("temsilci.davranis_degerlendirme_kurulu", "OÖİKY md. 57/2-c"),
        ("temsilci.sosyal_etkinlikler_kurulu", "SEY md. 6/1"),
        ("temsilci.rpd_yurutme_komisyonu", "RPD md. 16/2-e"),
        ("temsilci.tasimaci_tespit_komisyonu", "OSAY md. 3/1-m"),
        ("arz_bedeli.sozlesme_vade_gunu", "EK-2 md. 7/1. paragraf"),
        ("personel.sgk_saklama_yil", "5510 md. 86/2. paragraf"),
        ("temsilci.kantin_denetim_komisyonu", "G.2020/8 A-1/a"),
    ],
)
def test_atif_metni(kid: str, beklenen: str) -> None:
    assert erisim.atif_metni(KURALLAR[kid]) == beklenen


def test_her_atif_dosyasinin_kisa_adi_var() -> None:
    for k in R1["kurallar"]:
        for madde in atif_ortak.butun_maddeler(k):
            assert madde["capa"].split("#")[0] in erisim._KISA_ADLAR, k["id"]


@pytest.mark.parametrize(
    ("kid", "gozlenen", "durum"),
    [
        ("genel_kurul.ilan_en_az_gun", 15, "uygun"),
        ("genel_kurul.ilan_en_az_gun", 14, "uyari"),
        ("genel_kurul.ikinci_toplanti_en_gec_gun", 30, "uygun"),
        ("genel_kurul.ikinci_toplanti_en_gec_gun", 31, "uyari"),
        ("denetleme_kurulu.ogretmen_gorevlendirme_ay", 4, "uygun"),
        ("denetleme_kurulu.ogretmen_gorevlendirme_ay", 5, "uyari"),
        ("yonetim_kurulu.devamsizlik_siniri", 2, "uygun"),
        ("yonetim_kurulu.devamsizlik_siniri", 3, "uyari"),
        ("yonetim_kurulu.toplanti_yeter_sayi", 4, "uygun"),
        ("yonetim_kurulu.toplanti_yeter_sayi", 3, "sert"),
        ("yonetim_kurulu.asil_uye", 5, "uygun"),
        ("yonetim_kurulu.asil_uye", 4, "uyari"),
        ("yonetim_kurulu.uye_turleri", "VELI", "uygun"),
        ("yonetim_kurulu.uye_turleri", "OGRETMEN", "sert"),
    ],
)
def test_denetle_sinirin_iki_yani(kid: str, gozlenen: Any, durum: str) -> None:
    assert denetle(kid, gozlenen)["durum"] == durum


def test_denetle_mesaji_yer_tutucuyu_doldurur() -> None:
    sonuc = denetle("genel_kurul.ilan_en_az_gun", 14)
    assert sonuc == {
        "durum": "uyari",
        "mesaj": "Duyuru ile toplantı arasında 14 gün var; en az 15 gün olmalı.",
        "atif": "md. 9/3",
        "dayanak_turu": "lafiz",
        "paket": "OAB-2023.12",
        "rev": 1,
    }


def test_denetle_ondalik_dizeyle_kiyaslar() -> None:
    assert (
        denetle("arz_bedeli.kira_oran", Decimal("0.03"), okul={"okul.kantin": "KIRAYA_VERILIYOR"})[
            "durum"
        ]
        == "uygun"
    )
    assert (
        denetle("arz_bedeli.kira_oran", Decimal("0.04"), okul={"okul.kantin": "KIRAYA_VERILIYOR"})[
            "durum"
        ]
        == "sert"
    )
    with pytest.raises(TypeError):
        denetle("arz_bedeli.kira_oran", 0.03, okul={"okul.kantin": "KIRAYA_VERILIYOR"})


def test_liste_gozlenen_alt_kume_olarak_kiyaslanir() -> None:
    assert denetle("yonetim_kurulu.uye_turleri", ["VELI", "KURSIYER"])["durum"] == "uygun"
    assert denetle("yonetim_kurulu.uye_turleri", ["VELI", "IDARECI"])["durum"] == "sert"


def test_eksik_veri_gerekce_istemeden_eksik_doner() -> None:
    sonuc = denetle("genel_kurul.ilan_en_az_gun")
    assert sonuc["durum"] == "eksik" and sonuc["mesaj"] == erisim.EKSIK_NOTU


def test_eksik_veri_sapma_kuralinda_bastan_sapmadir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    icerik = _kopya()
    _kural0(icerik)["eksik_veri"] = "sapma"
    monkeypatch.setattr(yk._Onbellek, "durum", yk.yukle(_paket_dizini(tmp_path, icerik)))
    assert denetle("genel_kurul.ilan_en_az_gun")["durum"] == "uyari"


def test_kosul_saglanmazsa_kural_uygulanmaz() -> None:
    kid = "temsilci.kontenjan_komisyonu"
    assert denetle(kid, 0, okul={"okul.kademe": ["ORTAOKUL"]}) == {
        "durum": "uygun",
        "mesaj": "",
        "atif": "OKY md. 25/1-a",
        "dayanak_turu": "lafiz",
        "paket": "OAB-2023.12",
        "rev": 1,
    }
    # Karma okul: kesişim boş değilse uygulanır.
    assert denetle(kid, 0, okul={"okul.kademe": ["ORTAOKUL", "ORTAOGRETIM"]})["durum"] == "uyari"


@pytest.mark.parametrize("okul", [None, {}, {"okul.kademe": []}])
def test_okul_kartinda_kosul_girilmemisse_eksik(okul: Any) -> None:
    assert denetle("temsilci.kontenjan_komisyonu", 1, okul=okul)["durum"] == "eksik"


def test_donem_kopyasindan_okunur() -> None:
    """Dönem kendi kopyasıyla hesaplanır; dağıtılan paket değişse de etkilenmez (§6.2-4)."""
    kopya = _kopya()
    _kural0(kopya)["deger"] = 21
    donem = _donem(kopya)
    kid = "genel_kurul.ilan_en_az_gun"
    gun = date(2026, 11, 9)
    assert kural(kid, gun, donem) == 21
    assert kural(kid) == 15
    assert denetle(kid, 20, tarih=gun, donem=donem)["durum"] == "uyari"


def test_kural_kopya_doner() -> None:
    deger = kural("yonetim_kurulu.uye_turleri")
    deger.append("OGRETMEN")
    assert "OGRETMEN" not in kural("yonetim_kurulu.uye_turleri")


#: Ekran metni kendi atfını yazmaz (§6.1: atıf `madde`den eklenir); özelge ve sirküler dayanak olamaz.
_METINDE_ATIF = re.compile(
    r"\bmd\.|\bmadde\b|\bfıkra|\bözelge|\bsirküler|\bsayılı\b|Yönetmelik gereği", re.IGNORECASE
)
_METINDE_KISI_VERISI = re.compile(
    r"T\.\s?C\.|kimlik n|\btelefon|\badres|\bsuç|\bhüküm giy|\b\d{11}\b", re.IGNORECASE
)
#: Yönetmelik maddesinin kendi sözü: atıf değil, hükmün içeriği (korpus testi sınar).
_METNIN_KENDI_ATFI = {
    "kantin.isletmede_vergi_uyarisi": ("madde-23", "213 sayılı Vergi Usul Kanunu")
}


def _ekran_metni_bulgulari(metin: str) -> list[str]:
    bulgular = [e.group() for e in _METINDE_ATIF.finditer(metin)]
    bulgular += [e.group() for e in _METINDE_KISI_VERISI.finditer(metin)]
    yer_tutucular = {ad for _, ad, _, _ in Formatter().parse(metin) if ad is not None}
    return bulgular + sorted(yer_tutucular - denetimler.YER_TUTUCULAR)


@pytest.mark.parametrize("kid", sorted(KURALLAR))
def test_uyari_metinlerinde_yonetmelik_disi_atif_ve_kisi_verisi_yok(kid: str) -> None:
    """Ekrana çıkan metin (`uyari_metni`, sert kuralda `aciklama`) atıf ve kişi verisi taşımaz.

    `suc_engeli` metni suçu ele vermez (KVKK md. 6/1; tasarım §6.4.2).
    """
    k = KURALLAR[kid]
    bulgular = _ekran_metni_bulgulari(k.get("uyari_metni", k["aciklama"]))
    beklenen = ["sayılı"] if kid in _METNIN_KENDI_ATFI else []
    assert bulgular == beklenen


def test_metnin_kendi_atfi_yonetmelik_maddesinin_sozudur() -> None:
    for kid, (capa, ibare) in _METNIN_KENDI_ATFI.items():
        govde = atif_ortak.madde_govdesi((KORPUS / Y).read_text("utf-8"), capa)
        assert govde is not None and ibare in " ".join(govde.split()), kid
        assert ibare in KURALLAR[kid]["uyari_metni"]


@pytest.mark.parametrize(
    "metin",
    [
        "Süre md. 9/3 gereği en az on beş gündür.",
        "Bu ödeme madde hükmüne aykırı.",
        "İdarenin özelgesine göre muaftır.",
        "Sirküler uyarınca yapılır.",
        "5018 sayılı Kanun uygulanır.",
        "Yönetmelik gereği olamaz.",
        "Kişinin T.C. numarası eksik.",
        "Kimlik no girilmedi.",
        "12345678901 numaralı kişi.",
        "Bu kişinin suç kaydı var.",
        "{ad} görev alamaz.",
    ],
)
def test_ekran_metni_taramasi_yakalar(metin: str) -> None:
    assert _ekran_metni_bulgulari(metin)


# ============================================================ dönem bağı (§6.2; sentetik r2, r3)

GUN = date(2026, 10, 1)
IZIN_KURALI = "genel_kurul.ilan_en_az_gun"
CARPAN_KURALI = "genel_kurul.yeter_sayi_carpan"
ESIK_KURALI = "genel_kurul.kucuk_okul_esik"
YENI_KURAL = "genel_kurul.yeni_bilgi"
PAKET = "OAB-2023.12"


def _dagit(monkeypatch: pytest.MonkeyPatch, *icerikler: dict[str, Any]) -> None:
    """Sentetik revizyonları programla gelmiş gibi gösterir (`monkeypatch` geri alır)."""
    monkeypatch.setattr(
        yk._Onbellek,
        "durum",
        yk.PaketDurumu(paketler=tuple(yk.Paket.sozlukten(icerik) for icerik in icerikler)),
    )


def _rev(rev: int, *degisiklikler: tuple[str, str]) -> dict[str, Any]:
    kopya = deepcopy(R1)
    kopya["rev"] = rev
    kopya["degisiklikler"] = [{"id": kid, "tur": tur} for kid, tur in degisiklikler]
    return kopya


def _kayit_al(icerik: dict[str, Any], kid: str) -> dict[str, Any]:
    return next(k for k in icerik["kurallar"] if k["id"] == kid)


def _ekleme_revizyonu(rev: int = 2) -> dict[str, Any]:
    kopya = _rev(rev, ("genel_kurul.yeni_bilgi", "ekleme"))
    yeni = deepcopy(_kayit_al(kopya, IZIN_KURALI))
    yeni["id"] = "genel_kurul.yeni_bilgi"
    kopya["kurallar"].append(yeni)
    return kopya


def _duzeltme_revizyonu(rev: int = 2, *, carpan: int = 3, gun: int = 14) -> dict[str, Any]:
    """Değeri baştan yanlış yazılmış kurallar: aynı yürürlük aralığı, yeni değer (§6.2-3a)."""
    kopya = _rev(rev, (CARPAN_KURALI, "duzeltme"), (IZIN_KURALI, "duzeltme"))
    _kayit_al(kopya, CARPAN_KURALI)["deger"] = carpan
    _kayit_al(kopya, IZIN_KURALI)["deger"] = gun
    return kopya


def _deger_degisikligi_revizyonu(
    rev: int = 2, *, kid: str = IZIN_KURALI, deger: int = 20
) -> dict[str, Any]:
    """Değer 01.01.2027'de değişir: eski kaydın bitişi dolar, yeni kayıt eklenir (§6.2-3)."""
    kopya = _rev(rev, (kid, "deger_degisikligi"))
    eski = _kayit_al(kopya, kid)
    yeni = deepcopy(eski)
    eski["yururluk"]["bitis"] = "31.12.2026"
    yeni["deger"] = deger
    yeni["yururluk"] = {"baslangic": "01.01.2027", "bitis": None}
    kopya["kurallar"].append(yeni)
    return kopya


def _ilk_donem() -> OabTerm:
    yil = SchoolYear.objects.create(
        name="2026-2027",
        start_date=date(2026, 9, 7),
        end_date=date(2027, 6, 25),
        is_active=True,
    )
    return donemler.create_term(name="2026-2027 birlik dönemi", school_year=yil, start_date=GUN)


def _kapat(donem: OabTerm) -> OabTerm:
    """Sentetik kapanış: gerçek kapanış F4'tedir (plan F1c-3 "Testler")."""
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.KAPANDI, end_date=date(2027, 10, 1)
    )
    return OabTerm.objects.get(pk=donem.pk)


def _kurul(donem: OabTerm, mevcut: int = 120) -> GeneralAssembly:
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK,
        defaults={"student_count": mevcut, "student_count_as_of": GUN},
    )
    return genel_kurul.genel_kurul_olustur(donem=donem, kind=AssemblyKind.OLAGAN)


def _bag(donem: OabTerm) -> tuple[str, int]:
    donem = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    return str(donem.rule_package.package), int(donem.rule_package.rev)


def test_sentetik_revizyonlar_d2_den_gecer() -> None:
    assert denetimler.d2_kimlik(_ekleme_revizyonu(), R1) == []
    assert denetimler.d2_kimlik(_duzeltme_revizyonu(), R1) == []
    assert denetimler.d2_kimlik(_deger_degisikligi_revizyonu(), R1) == []


@pytest.mark.django_db
def test_kapanmis_donem_yeni_revizyonla_ayni_sonuc(monkeypatch: pytest.MonkeyPatch) -> None:
    donem = _kapat(_ilk_donem())
    _dagit(monkeypatch, R1, _duzeltme_revizyonu())
    assert kural(CARPAN_KURALI, tarih=GUN) == 3  # program yeni revizyonu taşıyor
    assert kural(CARPAN_KURALI, tarih=GUN, donem=donem) == 4
    assert genel_kurul_hesabi.genel_kurul_yeter_sayisi(120, tarih=GUN, donem=donem).gerekli == 64


@pytest.mark.django_db
def test_kapanmis_donemde_revizyon_gecisi_sert(monkeypatch: pytest.MonkeyPatch) -> None:
    donem = _kapat(_ilk_donem())
    _dagit(monkeypatch, R1, _ekleme_revizyonu())
    with pytest.raises(DonemKapali):
        kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=2)
    assert _bag(donem) == ("OAB-2023.12", 1)


@pytest.mark.django_db
def test_acik_donem_gecisi_fark_listesi_ve_denetim_izi(monkeypatch: pytest.MonkeyPatch) -> None:
    donem = _ilk_donem()
    r2 = _ekleme_revizyonu()
    _dagit(monkeypatch, R1, r2)
    fark = kural_bagi.revizyon_farki(donem, paket="OAB-2023.12", rev=2)
    assert fark.eklenen == ("genel_kurul.yeni_bilgi",)
    assert (fark.biten, fark.deger_degisen, fark.duzeltilen, fark.cikarilan) == ((), (), (), ())
    assert fark.kayitlar == ()
    assert _bag(donem) == ("OAB-2023.12", 1)  # fark kayıt yazmaz

    kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=2)
    assert _bag(donem) == ("OAB-2023.12", 2)
    guncelleme = AuditTrail.objects.get(model="oab.OabTerm", action=AuditAction.GUNCELLE)
    assert guncelleme.term_id == donem.pk
    assert guncelleme.account_id is not None
    assert "rule_package" in guncelleme.changed_fields
    olay = AuditTrail.objects.get(model="kural.revizyon_gecisi", object_id=str(donem.pk))
    assert olay.values == {"paket": ["OAB-2023.12", "OAB-2023.12"], "rev": [1, 2]}
    assert olay.term_id == donem.pk


@pytest.mark.django_db
def test_acik_donem_gecisi_geri_alinir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Geçiş dönem kapanana kadar geri alınabilir (§6.2-5)."""
    donem = _ilk_donem()
    _dagit(monkeypatch, R1, _ekleme_revizyonu())
    kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=2)
    fark = kural_bagi.revizyon_farki(donem, paket="OAB-2023.12", rev=1)
    assert fark.cikarilan == ("genel_kurul.yeni_bilgi",)
    kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=1)
    assert _bag(donem) == ("OAB-2023.12", 1)
    with pytest.raises(ValueError, match="zaten"):
        kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=1)


@pytest.mark.django_db
def test_olmayan_revizyona_gecilmez() -> None:
    donem = _ilk_donem()
    with pytest.raises(ValueError, match="programda yok"):
        kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=7)


@pytest.mark.django_db
def test_eski_degerli_olay_eski_degerle_hesaplanir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Değer değişince değişiklikten önceki olaylar eski değerle kalır (§6.2-3)."""
    donem = _ilk_donem()
    r2 = _deger_degisikligi_revizyonu()
    _dagit(monkeypatch, R1, r2)
    kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=2)
    donem = OabTerm.objects.get(pk=donem.pk)
    assert kural(IZIN_KURALI, tarih=date(2026, 12, 31), donem=donem) == 15
    assert kural(IZIN_KURALI, tarih=date(2027, 1, 1), donem=donem) == 20


@pytest.mark.django_db
def test_ekleme_revizyonu_hesap_degistirmez(monkeypatch: pytest.MonkeyPatch) -> None:
    donem = _ilk_donem()
    kurul = genel_kurul.yeter_sayiyi_dondur(_kurul(donem), tarih=GUN)
    _dagit(monkeypatch, R1, _ekleme_revizyonu())
    fark = kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=2)
    assert fark.kayitlar == ()
    assert (
        genel_kurul_hesabi.genel_kurul_yeter_sayisi(
            120, tarih=GUN, donem=OabTerm.objects.get(pk=donem.pk)
        ).gerekli
        == 64
    )
    assert GeneralAssembly.objects.get(pk=kurul.pk).quorum_required == 64


@pytest.mark.django_db
def test_duzeltme_revizyonunda_hesabi_degisecek_kayitlar_listelenir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    GeneralAssembly.objects.filter(pk=kurul.pk).update(
        first_meeting_at=datetime(2026, 10, 20, tzinfo=UTC)
    )
    genel_kurul.yeter_sayiyi_dondur(kurul, tarih=GUN)
    satir = uyum.denetle(
        IZIN_KURALI,
        3,
        donem=donem,
        konu=kurul,
        tarih=GUN,
        gerekce=uyum.Gerekce(metin="Uydurma gerekçe"),
    ).satir
    assert satir is not None
    _dagit(monkeypatch, R1, _duzeltme_revizyonu())
    fark = kural_bagi.revizyon_farki(donem, paket="OAB-2023.12", rev=2)
    assert fark.duzeltilen == (IZIN_KURALI, CARPAN_KURALI)
    assert {(k.model, k.kayit_id, k.kural_id) for k in fark.kayitlar} == {
        ("oab.ComplianceItem", str(satir.pk), IZIN_KURALI),
        ("oab.GeneralAssembly", str(kurul.pk), CARPAN_KURALI),
    }
    with pytest.raises(RevizyonOnayiGerekli):
        kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=2)
    assert _bag(donem) == ("OAB-2023.12", 1)
    kural_bagi.revizyon_gecisi(donem, paket="OAB-2023.12", rev=2, onay=True)
    assert _bag(donem) == ("OAB-2023.12", 2)


def _atlamali_revizyonlar() -> tuple[dict[str, Any], dict[str, Any]]:
    """r2 kuralı bitirir, r3 aynı aralıkta değeri düzeltir; ikisi de ardışık olarak D2'den geçer."""
    r2 = _rev(2, (IZIN_KURALI, "bitis"))
    _kayit_al(r2, IZIN_KURALI)["yururluk"]["bitis"] = "31.12.2026"
    r3 = deepcopy(r2)
    r3["rev"] = 3
    r3["degisiklikler"] = [{"id": IZIN_KURALI, "tur": "duzeltme"}]
    _kayit_al(r3, IZIN_KURALI)["deger"] = 14
    return r2, r3


@pytest.mark.django_db
def test_atlamali_geciste_duzeltme_bitis_sayilmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    r2, r3 = _atlamali_revizyonlar()
    assert denetimler.d2_kimlik(r2, R1) == []
    assert denetimler.d2_kimlik(r3, r2) == []
    donem = _ilk_donem()
    satir = uyum.denetle(
        IZIN_KURALI,
        3,
        donem=donem,
        konu=_kurul(donem),
        tarih=GUN,
        gerekce=uyum.Gerekce(metin="Uydurma gerekçe"),
    ).satir
    assert satir is not None
    _dagit(monkeypatch, R1, r2, r3)
    fark = kural_bagi.revizyon_farki(donem, paket=PAKET, rev=3)
    assert (fark.deger_degisen, fark.biten) == ((IZIN_KURALI,), ())
    assert [(k.model, k.kayit_id) for k in fark.kayitlar] == [("oab.ComplianceItem", str(satir.pk))]
    with pytest.raises(RevizyonOnayiGerekli):
        kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=3)
    assert _bag(donem) == (PAKET, 1)


def test_tek_revizyonda_bitis_kiliginda_deger_degisikligi_yakalanir() -> None:
    r2 = _rev(2, (IZIN_KURALI, "bitis"))
    _kayit_al(r2, IZIN_KURALI)["yururluk"]["bitis"] = "31.12.2026"
    _kayit_al(r2, IZIN_KURALI)["deger"] = 14
    assert any("beyanı tutmuyor" in s for s in denetimler.d2_kimlik(r2, R1))


def _dondurulmus_kurul(donem: OabTerm, ilk_toplanti: datetime | None) -> GeneralAssembly:
    kurul = _kurul(donem)
    GeneralAssembly.objects.filter(pk=kurul.pk).update(first_meeting_at=ilk_toplanti)
    return genel_kurul.yeter_sayiyi_dondur(kurul, tarih=GUN)


@pytest.mark.django_db
def test_tarihsiz_dondurulmus_kurul_duzeltmede_listelenir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    donem = _ilk_donem()
    kurul = _dondurulmus_kurul(donem, None)
    _dagit(monkeypatch, R1, _duzeltme_revizyonu())
    fark = kural_bagi.revizyon_farki(donem, paket=PAKET, rev=2)
    assert [(k.model, k.kayit_id, k.kural_id) for k in fark.kayitlar] == [
        ("oab.GeneralAssembly", str(kurul.pk), CARPAN_KURALI)
    ]
    with pytest.raises(RevizyonOnayiGerekli):
        kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=2)


@pytest.mark.django_db
def test_hedefte_yururlukte_deger_yoksa_kurul_listelenir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Eşik düzeltilir, çarpan toplantıdan önce biter: fark çökmez, kurul onaya düşer (§6.1)."""
    r2 = _rev(2, (ESIK_KURALI, "duzeltme"), (CARPAN_KURALI, "bitis"))
    _kayit_al(r2, ESIK_KURALI)["deger"] = 90
    _kayit_al(r2, CARPAN_KURALI)["yururluk"]["bitis"] = "31.12.2026"
    donem = _ilk_donem()
    kurul = _dondurulmus_kurul(donem, datetime(2027, 3, 1, 9, 0, tzinfo=UTC))
    _dagit(monkeypatch, R1, r2)
    fark = kural_bagi.revizyon_farki(donem, paket=PAKET, rev=2)
    assert [(k.model, k.kayit_id, k.kural_id) for k in fark.kayitlar] == [
        ("oab.GeneralAssembly", str(kurul.pk), ESIK_KURALI)
    ]


@pytest.mark.django_db
def test_deger_degisikliginde_acik_satir_listelenir_onay_ister(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    donem = _ilk_donem()
    satir = uyum.denetle(IZIN_KURALI, donem=donem, konu=_kurul(donem), tarih=GUN).satir
    assert satir is not None
    _dagit(monkeypatch, R1, _deger_degisikligi_revizyonu())
    fark = kural_bagi.revizyon_farki(donem, paket=PAKET, rev=2)
    assert fark.deger_degisen == (IZIN_KURALI,)
    assert [(k.model, k.kayit_id) for k in fark.kayitlar] == [("oab.ComplianceItem", str(satir.pk))]
    with pytest.raises(RevizyonOnayiGerekli):
        kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=2)
    assert _bag(donem) == (PAKET, 1)


def _r2de_acik_eksik(
    monkeypatch: pytest.MonkeyPatch, r2: dict[str, Any] | None = None, kurul_sayisi: int = 1
) -> tuple[OabTerm, list[ComplianceItem]]:
    """Dönem r2'ye geçer, r1'de olmayan kural için açık `EKSIK` satırları yazılır."""
    donem = _ilk_donem()
    kurullar = [_kurul(donem) for _ in range(kurul_sayisi)]
    _dagit(monkeypatch, R1, r2 or _ekleme_revizyonu())
    kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=2)
    satirlar = [
        uyum.denetle(YENI_KURAL, donem=donem, konu=kurul, tarih=GUN).satir for kurul in kurullar
    ]
    return donem, [s for s in satirlar if s is not None]


@pytest.mark.django_db
def test_geri_almada_cikarilan_kuralin_satiri_listelenir(monkeypatch: pytest.MonkeyPatch) -> None:
    donem, (satir,) = _r2de_acik_eksik(monkeypatch)
    fark = kural_bagi.revizyon_farki(donem, paket=PAKET, rev=1)
    assert fark.cikarilan == (YENI_KURAL,)
    assert [(k.model, k.kayit_id) for k in fark.kayitlar] == [("oab.ComplianceItem", str(satir.pk))]
    with pytest.raises(RevizyonOnayiGerekli):
        kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=1)
    assert _bag(donem) == (PAKET, 2)


@pytest.mark.django_db
def test_geri_alinan_revizyonun_eksigi_kapanista_sapmaya_doner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§6.2-5, O3: kural bağlı revizyonda yoksa bayrak satırın yazıldığı revizyondan okunur."""
    donem, (satir,) = _r2de_acik_eksik(monkeypatch)
    kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=1, onay=True)
    uyum.kapanis_gecisi(
        donem, gerekceler={YENI_KURAL: uyum.Gerekce(metin="Uydurma gerekçe")}, tarih=GUN
    )
    satir.refresh_from_db()
    assert (satir.kind, satir.rev) == (ComplianceKind.SAPMA, 2)
    assert satir.justification_group is not None


@pytest.mark.django_db
def test_geri_alinan_kuralin_kapali_toplu_bayragi_satirin_revizyonundan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r2 = _ekleme_revizyonu()
    _kayit_al(r2, YENI_KURAL)["toplu_gerekce"] = False
    donem, satirlar = _r2de_acik_eksik(monkeypatch, r2, kurul_sayisi=2)
    kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=1, onay=True)
    with pytest.raises(GerekceGerekli):
        uyum.kapanis_gecisi(donem, gerekceler={YENI_KURAL: uyum.Gerekce(metin="Tek")}, tarih=GUN)
    assert {ComplianceItem.objects.get(pk=s.pk).kind for s in satirlar} == {ComplianceKind.EKSIK}


@pytest.mark.django_db
def test_fark_listesi_yalniz_kendi_donemine_bakar(monkeypatch: pytest.MonkeyPatch) -> None:
    eski = _ilk_donem()
    kurul = _dondurulmus_kurul(eski, datetime(2026, 10, 20, tzinfo=UTC))
    uyum.denetle(IZIN_KURALI, donem=eski, konu=kurul, tarih=GUN)
    OabTerm.objects.filter(pk=eski.pk).update(status=TermStatus.IPTAL, start_date=None)
    yeni = donemler.create_term(name="ikinci", school_year=eski.school_year, start_date=GUN)
    _dagit(monkeypatch, R1, _duzeltme_revizyonu())
    fark = kural_bagi.revizyon_farki(yeni, paket=PAKET, rev=2)
    assert fark.duzeltilen == (IZIN_KURALI, CARPAN_KURALI)
    assert fark.kayitlar == ()


@pytest.mark.django_db
def test_etkilenen_kurulun_gunu_istanbul_gunudur(monkeypatch: pytest.MonkeyPatch) -> None:
    """31.12.2026 21:30 UTC, İstanbul'da 01.01.2027 00:30'dur: yeni değerle hesaplanır."""
    donem = _ilk_donem()
    kurul = _dondurulmus_kurul(donem, datetime(2026, 12, 31, 21, 30, tzinfo=UTC))
    assert kurul.quorum_required == 64
    _dagit(monkeypatch, R1, _deger_degisikligi_revizyonu(kid=CARPAN_KURALI, deger=3))
    fark = kural_bagi.revizyon_farki(donem, paket=PAKET, rev=2)
    assert [(k.model, k.kayit_id, k.kural_id) for k in fark.kayitlar] == [
        ("oab.GeneralAssembly", str(kurul.pk), CARPAN_KURALI)
    ]


@pytest.mark.django_db
def test_geri_alma_dagitimda_olmayan_revizyonu_kopyadan_okur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    donem = _ilk_donem()
    r2 = _ekleme_revizyonu()
    _dagit(monkeypatch, R1, r2)
    kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=2)
    _dagit(monkeypatch, r2)
    assert kural_bagi.revizyon_farki(donem, paket=PAKET, rev=1).cikarilan == (YENI_KURAL,)
    kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=1)
    assert _bag(donem) == (PAKET, 1)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE oab_rulepackage SET content = json_set(content, '$.kurallar[0].deger', 11) "
        "WHERE id = %s",
        "UPDATE oab_rulepackage SET content = json_set(content, '$.bozuk', 1.5) WHERE id = %s",
    ],
    ids=["deger", "kayan-nokta"],
)
def test_bozuk_kopyaya_gecilmez_donem_saglam_kopyasinda_kalir(
    monkeypatch: pytest.MonkeyPatch, sql: str
) -> None:
    """D7, §6.2-5: bozukluk geçiş anında bilinir; dönem salt okura düşmez."""
    donem = _ilk_donem()
    r2 = _ekleme_revizyonu()
    _dagit(monkeypatch, R1, r2)
    kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=2)
    kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=1)
    hedef = RulePackage.objects.get(package=PAKET, rev=2)
    with connection.cursor() as cursor:
        cursor.execute(sql, [hedef.pk])
    izler = AuditTrail.objects.filter(model="kural.revizyon_gecisi").count()
    with pytest.raises(ValueError, match="bozuk"):
        kural_bagi.revizyon_gecisi(donem, paket=PAKET, rev=2)
    with pytest.raises(ValueError, match="bozuk"):
        kural_bagi.revizyon_farki(donem, paket=PAKET, rev=2)
    with pytest.raises(ValueError, match="tutmuyor"):
        kural_bagi.kopya_dondur(yk.Paket.sozlukten(r2))
    assert _bag(donem) == (PAKET, 1)
    assert AuditTrail.objects.filter(model="kural.revizyon_gecisi").count() == izler
    donem_kilidi.yazma_denetimi(OabTerm.objects.get(pk=donem.pk))


@pytest.mark.django_db
def test_donem_kopyasi_ozeti() -> None:
    """D7 dönem kolu: dondurulmuş kopyanın kanonik özeti."""
    donem = _ilk_donem()
    kopya = donem.rule_package
    assert kopya.content_sha256 == yk.icerik_ozeti(kopya.content) == yk.icerik_ozeti(R1)
    assert donem_kilidi.kural_kopyasi_tutuyor(donem)
    bozuk = deepcopy(R1)
    bozuk["kurallar"][0]["deger"] = 11
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE oab_rulepackage SET content = %s WHERE id = %s",
            [json.dumps(bozuk, ensure_ascii=False), kopya.pk],
        )
    assert not donem_kilidi.kural_kopyasi_tutuyor(OabTerm.objects.get(pk=donem.pk))


# ============================================================ uyum hattı (§5 O3, §6.1)


@pytest.mark.django_db
def test_hesaplanan_degerde_fiili_fark_kaydedilir_uyari() -> None:
    """D1, KE-23: hesaplanan değer serttir, gerçek değer kaydedilir, fark uyarı + gerekçe olur."""
    donem = _ilk_donem()
    ozellik = {"okul.kantin": "KIRAYA_VERILIYOR"}
    with pytest.raises(KuralSert):
        uyum.denetle(
            "arz_bedeli.kira_oran",
            Decimal("0.05"),
            donem=donem,
            konu=donem,
            tarih=GUN,
            okul=ozellik,
        )
    with pytest.raises(GerekceGerekli):
        uyum.denetle(
            "arz_bedeli.kira_oran",
            Decimal("0.05"),
            donem=donem,
            konu=donem,
            tarih=GUN,
            okul=ozellik,
            fiili_kayit=True,
        )
    sonuc = uyum.denetle(
        "arz_bedeli.kira_oran",
        Decimal("0.05"),
        donem=donem,
        konu=donem,
        tarih=GUN,
        okul=ozellik,
        fiili_kayit=True,
        gerekce=uyum.Gerekce(metin="Uydurma gerekçe"),
    )
    assert sonuc.sonuc["durum"] == "uyari"
    assert sonuc.satir is not None and sonuc.satir.kind == ComplianceKind.SAPMA
    assert sonuc.satir.rule_id == "arz_bedeli.kira_oran"


@pytest.mark.django_db
def test_hesaplanan_olmayan_sert_kural_fiili_kayitla_gecmez() -> None:
    donem = _ilk_donem()
    with pytest.raises(KuralSert):
        uyum.denetle(
            "denetleme_kurulu.yk_uyesi_olamaz",
            False,
            donem=donem,
            konu=donem,
            tarih=GUN,
            fiili_kayit=True,
            gerekce=uyum.Gerekce(metin="Uydurma gerekçe"),
        )


@pytest.mark.django_db
def test_uyari_gerekcesiz_reddedilir_gerekceyle_kaydedilir() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    with pytest.raises(GerekceGerekli):
        uyum.denetle(IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN)
    assert not ComplianceItem.objects.exists()
    sonuc = uyum.denetle(
        IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN, gerekce=uyum.Gerekce(metin="Uydurma")
    )
    assert sonuc.satir is not None
    satir = sonuc.satir
    assert (satir.kind, satir.rule_package, satir.rev) == (ComplianceKind.SAPMA, "OAB-2023.12", 1)
    assert satir.justification_group is not None
    iz = AuditTrail.objects.get(model="oab.ComplianceItem", object_id=str(satir.pk))
    assert iz.compliance_item_id == satir.pk
    assert iz.term_id == donem.pk
    assert iz.values["rule_id"] == [None, IZIN_KURALI]
    assert iz.values["rev"] == [None, 1]
    assert denetim_izi.kaydi_dogrula(ComplianceItem, satir.pk) is True


@pytest.mark.django_db
def test_gerekce_alinmis_sapma_ayni_degerle_yeniden_sorulmaz() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    uyum.denetle(
        IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN, gerekce=uyum.Gerekce(metin="Uydurma")
    )
    izler = AuditTrail.objects.count()
    sonuc = uyum.denetle(IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN)
    assert sonuc.satir is not None
    assert ComplianceItem.objects.count() == 1
    assert AuditTrail.objects.count() == izler


@pytest.mark.django_db
def test_sapan_deger_degisince_yeni_gerekce_istenir_ileti_ve_iz_guncellenir() -> None:
    """O3, O4: açık sapmanın değeri başka sapan değere dönerse yeni sapma gerekçesiz geçmez."""
    donem = _ilk_donem()
    kurul = _kurul(donem)
    satir = uyum.denetle(
        IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN, gerekce=uyum.Gerekce(metin="Birinci")
    ).satir
    assert satir is not None
    with pytest.raises(GerekceGerekli):
        uyum.denetle(IZIN_KURALI, 4, donem=donem, konu=kurul, tarih=GUN)
    satir.refresh_from_db()
    assert "3 gün" in satir.message
    izler = AuditTrail.objects.filter(model="oab.ComplianceItem", object_id=str(satir.pk)).count()
    uyum.denetle(
        IZIN_KURALI, 4, donem=donem, konu=kurul, tarih=GUN, gerekce=uyum.Gerekce(metin="İkinci")
    )
    satir.refresh_from_db()
    assert ComplianceItem.objects.count() == 1
    assert "4 gün" in satir.message
    assert satir.justification_group is not None and satir.justification_group.text == "İkinci"
    assert (
        AuditTrail.objects.filter(model="oab.ComplianceItem", object_id=str(satir.pk)).count()
        == izler + 1
    )
    assert denetim_izi.kaydi_dogrula(ComplianceItem, satir.pk) is True


@pytest.mark.django_db
def test_kayit_duzeltilince_sapma_kapanir() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    uyum.denetle(
        IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN, gerekce=uyum.Gerekce(metin="Uydurma")
    )
    uyum.denetle(IZIN_KURALI, 15, donem=donem, konu=kurul, tarih=GUN)
    satir = ComplianceItem.objects.get()
    assert satir.kind == ComplianceKind.SAPMA
    assert satir.resolved_at is not None


@pytest.mark.django_db
def test_eksik_veri_gerekce_istemez() -> None:
    """R5: eksik gerekçesiz yazılır; bilgi girilince kapanır."""
    donem = _ilk_donem()
    kurul = _kurul(donem)
    sonuc = uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    assert sonuc.sonuc["durum"] == "eksik"
    assert sonuc.satir is not None
    assert (sonuc.satir.kind, sonuc.satir.justification_group) == (ComplianceKind.EKSIK, None)
    # İkinci denetim yeni satır açmaz; bilgi girilince kapanır, satır silinmez.
    uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    assert ComplianceItem.objects.count() == 1
    uyum.denetle(IZIN_KURALI, 15, donem=donem, konu=kurul, tarih=GUN)
    assert ComplianceItem.objects.get().resolved_at is not None


@pytest.mark.django_db
def test_eksik_bilgi_sapan_degerle_gelince_sapmaya_doner() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    with pytest.raises(GerekceGerekli):
        uyum.denetle(IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN)
    assert ComplianceItem.objects.get().kind == ComplianceKind.EKSIK
    uyum.denetle(
        IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN, gerekce=uyum.Gerekce(metin="Uydurma")
    )
    satir = ComplianceItem.objects.get()
    assert satir.kind == ComplianceKind.SAPMA
    assert satir.justification_group is not None


@pytest.mark.django_db
def test_eksik_veri_sapma_olan_kuralda_eksiklik_bastan_sapmadir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r2 = _rev(2, (IZIN_KURALI, "duzeltme"))
    _kayit_al(r2, IZIN_KURALI)["eksik_veri"] = "sapma"
    _dagit(monkeypatch, r2)
    donem = _ilk_donem()
    kurul = _kurul(donem)
    with pytest.raises(GerekceGerekli):
        uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN)


@pytest.mark.django_db
def test_denetlenmedi_satir_acmaz_bilgi_notu_doner() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    sonuc = uyum.denetle(
        "genel_kurul.ilan_en_az_gun", 3, donem=donem, konu=kurul, tarih=date(2000, 1, 1)
    )
    assert sonuc.sonuc["durum"] == "denetlenmedi"
    assert sonuc.satir is None
    assert not ComplianceItem.objects.exists()


@pytest.mark.django_db
def test_kapanis_gecisinde_eksik_sapmaya_doner() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    with pytest.raises(GerekceGerekli):
        uyum.kapanis_gecisi(donem, konu=kurul, gerekceler={}, tarih=GUN)
    assert ComplianceItem.objects.get().kind == ComplianceKind.EKSIK
    cevrilen = uyum.kapanis_gecisi(
        donem,
        konu=kurul,
        gerekceler={IZIN_KURALI: uyum.Gerekce(metin="Uydurma gerekçe")},
        tarih=GUN,
    )
    assert [s.pk for s in cevrilen] == [ComplianceItem.objects.get().pk]
    satir = ComplianceItem.objects.get()
    assert satir.kind == ComplianceKind.SAPMA
    assert satir.justification_group is not None
    durum = AuditTrail.objects.filter(
        model="oab.ComplianceItem", object_id=str(satir.pk), action=AuditAction.DURUM
    )
    assert durum.count() == 1
    assert durum.get().compliance_item_id == satir.pk
    assert durum.get().values["kind"] == ["EKSIK", "SAPMA"]


@pytest.mark.django_db
def test_toplu_gerekce_bir_gerekce_cok_kayit() -> None:
    """Aynı kural ve kök neden için tek gerekçe; bağlanan her satır denetim izine yazılır."""
    donem = _ilk_donem()
    birinci, ikinci = _kurul(donem), _kurul(donem)
    for kurul, metin in ((birinci, "Uydurma toplu gerekçe"), (ikinci, "")):
        uyum.denetle(
            IZIN_KURALI,
            3,
            donem=donem,
            konu=kurul,
            tarih=GUN,
            gerekce=uyum.Gerekce(metin=metin, kok_neden="ilan-kaniti:1"),
        )
    gerekce = ComplianceJustification.objects.get()
    assert gerekce.root_cause == "ilan-kaniti:1"
    assert gerekce.text == "Uydurma toplu gerekçe"
    assert gerekce.items.count() == 2
    assert AuditTrail.objects.filter(model="oab.ComplianceItem").count() == 2
    assert AuditTrail.objects.filter(model="oab.ComplianceJustification").count() == 1


@pytest.mark.django_db
def test_toplu_gerekce_kapali_kuralda_tek_tek(monkeypatch: pytest.MonkeyPatch) -> None:
    r2 = _rev(2, (IZIN_KURALI, "duzeltme"))
    _kayit_al(r2, IZIN_KURALI)["toplu_gerekce"] = False
    _dagit(monkeypatch, r2)
    donem = _ilk_donem()
    birinci, ikinci = _kurul(donem), _kurul(donem)
    uyum.denetle(
        IZIN_KURALI,
        3,
        donem=donem,
        konu=birinci,
        tarih=GUN,
        gerekce=uyum.Gerekce(metin="Birinci", kok_neden="ilan-kaniti:1"),
    )
    with pytest.raises(GerekceGerekli):
        uyum.denetle(
            IZIN_KURALI,
            3,
            donem=donem,
            konu=ikinci,
            tarih=GUN,
            gerekce=uyum.Gerekce(metin="", kok_neden="ilan-kaniti:1"),
        )
    uyum.denetle(
        IZIN_KURALI,
        3,
        donem=donem,
        konu=ikinci,
        tarih=GUN,
        gerekce=uyum.Gerekce(metin="İkinci", kok_neden="ilan-kaniti:1"),
    )
    assert ComplianceJustification.objects.count() == 2
    assert set(ComplianceJustification.objects.values_list("root_cause", flat=True)) == {""}


@pytest.mark.django_db
def test_toplu_gerekce_kapali_kuralda_kapanis_tek_tek(monkeypatch: pytest.MonkeyPatch) -> None:
    """O3: tek metin her satıra çoğaltılmaz; kök neden yok sayılır, her kayıt kendi metnini alır."""
    r2 = _rev(2, (IZIN_KURALI, "duzeltme"))
    _kayit_al(r2, IZIN_KURALI)["toplu_gerekce"] = False
    _dagit(monkeypatch, r2)
    donem = _ilk_donem()
    kurullar = (_kurul(donem), _kurul(donem))
    for kurul in kurullar:
        uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    with pytest.raises(GerekceGerekli, match="kendi gerekçesini"):
        uyum.kapanis_gecisi(
            donem,
            gerekceler={IZIN_KURALI: uyum.Gerekce(metin="Tek", kok_neden="ilan-kaniti:1")},
            tarih=GUN,
        )
    assert set(ComplianceItem.objects.values_list("kind", flat=True)) == {ComplianceKind.EKSIK}
    assert not ComplianceJustification.objects.exists()
    for kurul, metin in zip(kurullar, ("Birinci", "İkinci"), strict=True):
        uyum.kapanis_gecisi(
            donem,
            konu=kurul,
            gerekceler={IZIN_KURALI: uyum.Gerekce(metin=metin, kok_neden="ilan-kaniti:1")},
            tarih=GUN,
        )
    assert set(ComplianceItem.objects.values_list("kind", flat=True)) == {ComplianceKind.SAPMA}
    assert {g.text for g in ComplianceJustification.objects.all()} == {"Birinci", "İkinci"}
    assert set(ComplianceJustification.objects.values_list("root_cause", flat=True)) == {""}


@pytest.mark.django_db
def test_toplu_gerekce_acik_kuralda_kapanis_tek_gerekceyle_gecer() -> None:
    donem = _ilk_donem()
    for kurul in (_kurul(donem), _kurul(donem)):
        uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    cevrilen = uyum.kapanis_gecisi(
        donem,
        gerekceler={IZIN_KURALI: uyum.Gerekce(metin="Uydurma", kok_neden="ilan-kaniti:1")},
        tarih=GUN,
    )
    assert len(cevrilen) == 2
    assert ComplianceJustification.objects.get().items.count() == 2


@pytest.mark.django_db
def test_kapanis_gecisi_yalniz_verilen_kaydin_eksigini_cevirir() -> None:
    donem = _ilk_donem()
    birinci, ikinci = _kurul(donem), _kurul(donem)
    satir_a = uyum.denetle(IZIN_KURALI, donem=donem, konu=birinci, tarih=GUN).satir
    satir_b = uyum.denetle(IZIN_KURALI, donem=donem, konu=ikinci, tarih=GUN).satir
    assert satir_a is not None and satir_b is not None
    uyum.kapanis_gecisi(
        donem, konu=birinci, gerekceler={IZIN_KURALI: uyum.Gerekce(metin="Uydurma")}, tarih=GUN
    )
    satir_a.refresh_from_db()
    satir_b.refresh_from_db()
    assert (satir_a.kind, satir_b.kind) == (ComplianceKind.SAPMA, ComplianceKind.EKSIK)


@pytest.mark.django_db
def test_kapanmis_eksik_kapanista_yeniden_cevrilmez() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    uyum.denetle(IZIN_KURALI, 15, donem=donem, konu=kurul, tarih=GUN)
    assert uyum.kapanis_gecisi(donem, gerekceler={}, tarih=GUN) == []
    assert ComplianceItem.objects.get().kind == ComplianceKind.EKSIK


@pytest.mark.django_db
def test_kapanan_sapmadan_sonra_yeni_sapma_yeni_satir_acar() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    gerekce = uyum.Gerekce(metin="Uydurma")
    uyum.denetle(IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN, gerekce=gerekce)
    uyum.denetle(IZIN_KURALI, 15, donem=donem, konu=kurul, tarih=GUN)
    uyum.denetle(IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN, gerekce=gerekce)
    assert ComplianceItem.objects.count() == 2
    assert ComplianceItem.objects.filter(resolved_at__isnull=True).count() == 1


@pytest.mark.django_db
def test_denetlenmedi_acik_satira_dokunmaz() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN)
    sonuc = uyum.denetle(IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=date(2000, 1, 1))
    assert sonuc.sonuc["durum"] == "denetlenmedi"
    satir = ComplianceItem.objects.get()
    assert (satir.kind, satir.resolved_at) == (ComplianceKind.EKSIK, None)


@pytest.mark.django_db
def test_kok_neden_baska_kuralin_gerekcesine_baglanmaz() -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    uyum.denetle(
        IZIN_KURALI,
        3,
        donem=donem,
        konu=kurul,
        tarih=GUN,
        gerekce=uyum.Gerekce(metin="Uydurma", kok_neden="ortak"),
    )
    with pytest.raises(GerekceGerekli):
        uyum.denetle(
            "genel_kurul.olagan_son_ay",
            11,
            donem=donem,
            konu=kurul,
            tarih=GUN,
            gerekce=uyum.Gerekce(metin="", kok_neden="ortak"),
        )
    assert ComplianceItem.objects.count() == 1


@pytest.mark.django_db
def test_eksikten_donen_sapma_ileti_paket_ve_revizyonu_gunceller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    donem = _ilk_donem()
    kurul = _kurul(donem)
    satir = uyum.denetle(IZIN_KURALI, donem=donem, konu=kurul, tarih=GUN).satir
    assert satir is not None
    assert (satir.message, satir.rule_package, satir.rev) == (erisim.EKSIK_NOTU, PAKET, 1)
    r2 = _rev(2)
    r2["paket"] = "OAB-2099.01"
    _dagit(monkeypatch, R1, r2)
    kural_bagi.revizyon_gecisi(donem, paket="OAB-2099.01", rev=2)
    uyum.denetle(
        IZIN_KURALI, 3, donem=donem, konu=kurul, tarih=GUN, gerekce=uyum.Gerekce(metin="Uydurma")
    )
    satir.refresh_from_db()
    assert satir.kind == ComplianceKind.SAPMA
    assert "3 gün" in satir.message
    assert (satir.rule_package, satir.rev) == ("OAB-2099.01", 2)
