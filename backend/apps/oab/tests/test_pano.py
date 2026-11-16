"""Genel Bakış'ın pano kalemleri (tasarım §7.10; plan F1c 12. adım "pano kabuğu").

Sınananlar: rol başına görünüm (§7.10 tablosu, her rolde), kalemin götürdüğü ekran, gün değişimi
(gün `pano.bugun` ile sabitlenir; günün Europe/Istanbul günü olduğu ayrıca), kalemin kaynak kayıt
kapanınca düşmesi, kişi adı taraması (uydurma adlarla yanıt gövdesinde ad yok), aynı önerilerin
kişisiz sayımla tek kaleme toplanması, hesaplamanın hiçbir şey yazmaması (sorgu sayacı) ve
kilitliyken uçtan yazma olmaması (423, tablolar değişmez), D7'de ucun 503 değil bilgiyle dönmesi, tek
kaynağın kuralı okunamayınca ötekilerin çalışması. Adlar ve tarihler UYDURMADIR.

F2 (plan §6.3, 12. adım "genel kurul süreleri"): olağan genel kurul (planlanmadı, birinci toplantı
sınırı aşıyor), yeni açılan okulun ilk genel kurulu, ilanın son günü ve eksik kanal kanıtı, ikinci
toplantının son günü, görev bölümü süresinin genel kurulun yapıldığı günden (ikinci toplantı) işlemesi,
müdürün bekleyen yazısı, ibra edilmedi bildirimi ve TEFBİS takvim satırları, dönem onayı, veri
sorumlusunun tamamlanacağı; her kalemde yetkili ve yetkisiz roller, sınır günleri (tam son gün, bir gün
önce ve sonra; Europe/Istanbul gece yarısı), kişi adı taraması ve yazmazlık. Süreler kural paketinden
okunarak beklenir (testte sabit süre yazılmaz; yalnız uydurma takvim günleri).
"""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.oab.kurallar import VERI_YOK, YururlukteDegerYok, kural
from apps.oab.kurallar import yukleyici as yk
from apps.oab.models import (
    AssemblyKind,
    ComplianceItem,
    ComplianceKind,
    DraftText,
    GeneralAssembly,
    OabPerson,
    OabTerm,
    OfficialBook,
    OrganMembership,
    RulePackage,
    SeatGroup,
    SeatType,
    TermStatus,
)
from apps.oab.services import (
    donem_kilidi,
    gecis,
    kisiler,
    kural_bagi,
    kurullar,
    pano,
    takvim,
    temsilciler,
    uyelikler,
    uyum,
)
from apps.oab.services import genel_kurul as gk
from apps.oab.services import genel_kurul_evraki as gke
from apps.oab.tests import genel_kurul_evraki_ortak as gke_ortak
from apps.oab.tests import genel_kurul_ortak as gko
from apps.oab.tests import uyelik_ortak as o
from apps.oab.tests.kurallar import paket_ortak
from apps.okul import denetim_izi, iz_durumu
from apps.okul.models import AccountRole, AuditTrail, SchoolConfig
from apps.okul.services import app_password

pytestmark = pytest.mark.django_db

UC = "/api/v1/oab/dashboard/"
#: Kurulların görevdeki asılları `SECIM_GUNU`'nde (15.10.2026) seçilmiş, dönem 10.10.2026'da açılmış:
#: yönetim kurulunun görev bölümü süresi 22.10'da, Denetleme Kurulununki 17.10'da biter (7 gün, KE-12).
GUN = date(2026, 10, 20)
YK_SON_GUN = "2026-10-22"
DK_SON_GUN = "2026-10-17"

ROLLER = (
    AccountRole.YONETICI,
    AccountRole.BASKAN,
    AccountRole.BASKAN_YARDIMCISI,
    AccountRole.MUHASIP,
    AccountRole.SEKRETER,
    AccountRole.DENETLEME_KURULU,
    AccountRole.MUDUR,
)

#: Gerçek gün işlevi (fixture'dan önce saklanır; Europe/Istanbul sınaması bununla koşar).
_GERCEK_BUGUN = pano.bugun


#: Okul kartının uydurma veri sorumlusu: girilmişken program yöneticisinin "tamamlanacaklar"ında
#: okul kartı satırı çıkmaz (F2 12. adım; boş hâli `test_f2_veri_sorumlusu_tamamlanacak`).
VERI_SORUMLUSU = "Uydurma Ortaokulu Müdürlüğü, Örnek Mah. No: 1"


@pytest.fixture(autouse=True)
def gunu_sabitle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pano, "bugun", lambda: GUN)


@pytest.fixture(autouse=True)
def veri_sorumlusu_girili() -> None:
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK, defaults={"data_controller_text": VERI_SORUMLUSU}
    )


def _pano(rol: AccountRole | None = None) -> dict[str, Any]:
    if rol is None or rol == AccountRole.YONETICI:
        yanit = APIClient().get(UC)
    else:
        with o.rol_olarak(rol):
            yanit = APIClient().get(UC)
    assert yanit.status_code == 200, yanit.content
    veri: dict[str, Any] = yanit.json()
    return veri


def _kodlar(veri: dict[str, Any]) -> list[str]:
    return [k["kod"] for k in veri["isler"]]


def _kurullar() -> OabTerm:
    """Açık dönem, beş asıllı yönetim kurulu ve üç asıllı Denetleme Kurulu (yedeksiz, görevsiz)."""
    donem = o.donem()
    o.yk_kurulu(donem)
    o.dk_kurulu(donem)
    return donem


def test_rol_basina_gorunum() -> None:
    """Tasarım §7.10 "Rol başına görünüm": program yöneticisi bütün listeyi; sekreter yönetim kurulunun
    görev bölümü süresini ve kadrosunu; başkan ve başkan yardımcısı görev bölümü süresini; Denetleme
    Kurulu kendi görev bölümü süresini ve kadrosunu görür; muhasip ve müdürün F1c'de kalemi yoktur.
    Geçiş adımları ve hesap önerileri yalnız program yöneticisinde. Veli rollerinde görünüm "ay"."""
    _kurullar()
    beklenen = {
        AccountRole.YONETICI: {
            "YK_GOREV_BOLUMU",
            "DK_GOREV_BOLUMU",
            "KADRO",
            "GECIS_ADIMI",
            "HESAP_ONERISI",
        },
        AccountRole.BASKAN: {"YK_GOREV_BOLUMU"},
        AccountRole.BASKAN_YARDIMCISI: {"YK_GOREV_BOLUMU"},
        AccountRole.MUHASIP: set(),
        AccountRole.SEKRETER: {"YK_GOREV_BOLUMU", "KADRO"},
        AccountRole.DENETLEME_KURULU: {"DK_GOREV_BOLUMU", "KADRO"},
        AccountRole.MUDUR: set(),
    }
    for rol in ROLLER:
        veri = _pano(rol)
        assert set(_kodlar(veri)) == beklenen[rol], rol
        assert veri["bugun"] == GUN.isoformat()
        assert veri["gorunum"] == ("ay" if rol in pano.AYLIK_GORUNUM_ROLLERI else "hafta"), rol
        assert veri["bilgiler"] == [], rol

    # İki kurulun kadro kalemi aynı koddadır: kurul `ek.organ` ile ayrılır (program yöneticisi ikisini).
    def kadro_kurullari(rol: AccountRole) -> set[str]:
        return {k["ek"]["organ"] for k in _pano(rol)["isler"] if k["kod"] == "KADRO"}

    assert kadro_kurullari(AccountRole.YONETICI) == {"YK", "DK"}
    assert kadro_kurullari(AccountRole.SEKRETER) == {"YK"}
    assert kadro_kurullari(AccountRole.DENETLEME_KURULU) == {"DK"}


def test_gorev_bolumu_suresi_vade_ekran_ve_atif() -> None:
    """Son gün başlangıç + kural değeridir; vadeli kalemler önde, sonra vadesizler. Kalem kendi kurulunun
    sekmesine götürür, atfı kural paketindendir."""
    _kurullar()
    isler = _pano()["isler"]
    yk, dk = (
        next(k for k in isler if k["kod"] == kod) for kod in ("YK_GOREV_BOLUMU", "DK_GOREV_BOLUMU")
    )
    assert (yk["vade"], yk["gecikti"], yk["rota"], yk["sekme"]) == (
        YK_SON_GUN,
        False,
        "/organlar",
        "yk",
    )
    assert yk["atif"] == "md. 12/3"
    assert (dk["vade"], dk["gecikti"], dk["sekme"]) == (DK_SON_GUN, True, "dk")
    assert dk["atif"] == "md. 14/1"
    # Vadeliler son güne göre önde (Denetleme Kurulununki daha erken), vadesizler ardından.
    assert [k["vade"] for k in isler[:2]] == [DK_SON_GUN, YK_SON_GUN]
    assert all(k["vade"] is None for k in isler[2:])


def test_gun_degisimi(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kalem her okumada o günle hesaplanır: son gün bugünse gecikmemiştir, ertesi gün gecikmiştir."""
    _kurullar()
    for gun, gecikti in ((date(2026, 10, 22), False), (date(2026, 10, 23), True)):
        monkeypatch.setattr(pano, "bugun", lambda gun=gun: gun)
        veri = _pano(AccountRole.SEKRETER)
        (yk,) = [k for k in veri["isler"] if k["kod"] == "YK_GOREV_BOLUMU"]
        assert veri["bugun"] == gun.isoformat()
        assert (yk["vade"], yk["gecikti"]) == (YK_SON_GUN, gecikti)


def test_gorev_bolumu_yapilinca_kalem_duser() -> None:
    """Kalem saklanmaz: görev bölümü yazılınca sonraki okumada çıkmaz (§7.10 "Kalemin kapanması")."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    assert "YK_GOREV_BOLUMU" in _kodlar(_pano(AccountRole.BASKAN))
    with o.rol_olarak(AccountRole.SEKRETER):
        o.yk_gorev_bolumu(donem, {"BASKAN": uyeler[0]}, gun=date(2026, 10, 18))
    assert "YK_GOREV_BOLUMU" not in _kodlar(_pano(AccountRole.BASKAN))
    assert ComplianceItem.objects.filter(rule_id="yonetim_kurulu.gorev_bolumu_gun").count() == 0


def test_dk_gorev_bolumu_yapilinca_kalem_duser() -> None:
    """Denetleme Kurulunda da kalem saklanmaz: görev bölümü yazılınca sonraki okumada ne Denetleme
    Kurulunda ne program yöneticisinde çıkar (§7.10 "Kalemin kapanması"; md. 14/1)."""
    donem = o.donem()
    dk = o.dk_kurulu(donem)
    for rol in (AccountRole.DENETLEME_KURULU, AccountRole.YONETICI):
        assert "DK_GOREV_BOLUMU" in _kodlar(_pano(rol)), rol
    # 16.10.2026 görev bölümü süresinin içindedir (son gün 17.10): gerekçe istenmez.
    o.dk_gorev_bolumu(donem, dk[0], gun=date(2026, 10, 16))
    for rol in (AccountRole.DENETLEME_KURULU, AccountRole.YONETICI):
        assert "DK_GOREV_BOLUMU" not in _kodlar(_pano(rol)), rol
    assert ComplianceItem.objects.filter(rule_id="denetleme_kurulu.gorev_bolumu_gun").count() == 0


def test_programdan_once_olusmus_kurulda_sure_kalemi_yok() -> None:
    """Kurul programa başlama gününden önce oluşmuşsa (devralınan kurul) görev bölümü programdan önce
    yapılmıştır; geçmiş geriye dönük işletilmez (§7.9 "Ne olmaz"), süre kalemi çıkmaz."""
    donem = _kurullar()
    OabTerm.objects.filter(pk=donem.pk).update(program_start_date=date(2026, 10, 16))
    kodlar = _kodlar(_pano())
    assert "YK_GOREV_BOLUMU" not in kodlar and "DK_GOREV_BOLUMU" not in kodlar


def test_yedek_cagrisi_onerisi() -> None:
    """Yönetim kurulunda asıl eksik ve çağrılmamış yedek varken öneri sekreter ve program yöneticisinde
    (md. 13/6), aynı ileti kadro kalemi olarak yinelenmez; başkan görmez. Denetleme Kurulunda öğretmenin
    dört aydan uzun görevlendirmesi yalnız program yöneticisine öneridir (yedeği o çağırır, md. 14/6)."""
    donem = o.donem()
    o.yk_kurulu(donem, asil=4, yedek=1)
    for rol in (AccountRole.YONETICI, AccountRole.SEKRETER):
        isler = _pano(rol)["isler"]
        (oneri,) = [k for k in isler if k["kod"] == "YEDEK_CAGRISI"]
        assert (oneri["ek"]["organ"], oneri["atif"], oneri["sekme"]) == ("YK", "md. 13/6", "yk")
        assert "4" in oneri["metin"]
        assert all(k["metin"] != oneri["metin"] for k in isler if k["kod"] == "KADRO"), rol
    assert "YEDEK_CAGRISI" not in _kodlar(_pano(AccountRole.BASKAN))

    uyelikler.update_membership(
        o.dk_ogretmeni(donem, o.ogretmen()),
        external_assignment_start=date(2026, 10, 16),
        external_assignment_end=date(2027, 3, 30),
    )
    dk_onerileri = [
        k for k in _pano()["isler"] if k["kod"] == "YEDEK_CAGRISI" and k["ek"]["organ"] == "DK"
    ]
    assert len(dk_onerileri) == 1 and dk_onerileri[0]["atif"] == "md. 14/6"
    assert dk_onerileri[0]["ek"]["sayi"] == 1
    for rol in (AccountRole.SEKRETER, AccountRole.DENETLEME_KURULU):
        assert all(
            k["ek"].get("organ") != "DK" or k["kod"] != "YEDEK_CAGRISI" for k in _pano(rol)["isler"]
        )


def test_gecis_adimlari_ve_hesap_onerileri_kisisiz() -> None:
    """Geçiş kurulumunun açık adımları ve hesap önerileri yalnız program yöneticisinde; hesap önerisi
    yalnız tür, rol ve neden taşır (hesap, üyelik, kişi kimliği dönmez)."""
    _kurullar()
    isler = _pano()["isler"]
    adimlar = [k["ek"]["adim"] for k in isler if k["kod"] == "GECIS_ADIMI"]
    assert adimlar == gecis.yol_haritasi_durumu()["open_steps"] and adimlar[-1] == "tamamla"
    assert all(
        k["rota"] == "/birlik-donemi/gecis-kurulumu" for k in isler if k["kod"] == "GECIS_ADIMI"
    )
    hesap = [k for k in isler if k["kod"] == "HESAP_ONERISI"]
    assert hesap and {k["ek"]["tur"] for k in hesap} == {"HESAP_AC"}
    assert all(
        set(k["ek"]) == {"tur", "rol", "neden", "sayi"} and k["rota"] == "/kullanicilar"
        for k in hesap
    )


def test_kural_surumu_guncellemesi_yalniz_yoneticide_gecisle_duser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan F2 2. adım, §6.3 ve §7 U2; tasarım §7.10 (yol haritası: kural sürümü seçimi): programla açık
    dönemden daha yeni revizyon geldiyse program yöneticisine kişisiz kalem çıkar (yalnız iki sürüm;
    götürdüğü ekran Birlik Dönemi); öteki rollerde yoktur; geçiş yapılınca kendiliğinden düşer."""
    monkeypatch.setattr(
        yk._Onbellek,
        "durum",
        yk.PaketDurumu(paketler=(yk.Paket.sozlukten(paket_ortak.oku(paket_ortak.DOSYALAR[0])),)),
    )
    donem = o.donem()
    monkeypatch.setattr(
        yk._Onbellek,
        "durum",
        yk.PaketDurumu(paketler=tuple(yk.Paket.sozlukten(i) for i in paket_ortak.REVIZYONLAR)),
    )
    kalemler = [k for k in _pano()["isler"] if k["kod"] == "KURAL_SURUMU"]
    assert len(kalemler) == 1
    (kalem,) = kalemler
    assert (kalem["rota"], kalem["sekme"], kalem["vade"], kalem["metin"]) == (
        "/birlik-donemi",
        "",
        None,
        "",
    )
    assert kalem["ek"] == {
        "bagli_paket": paket_ortak.PAKET,
        "bagli_rev": 1,
        "yeni_paket": paket_ortak.PAKET,
        "yeni_rev": paket_ortak.EN_YENI_REV,
    }
    for rol in ROLLER[1:]:
        assert "KURAL_SURUMU" not in _kodlar(_pano(rol)), rol
    kural_bagi.revizyon_gecisi(donem, paket=paket_ortak.PAKET, rev=paket_ortak.EN_YENI_REV)
    assert "KURAL_SURUMU" not in _kodlar(_pano())


def test_ayni_oneriler_kisisiz_sayimla_tek_kalem() -> None:
    """Aynı tür, rol ve nedenli hesap önerileri tek kalemdir (sayı ile); Denetleme Kurulunda aynı
    iletili yedek çağrısı önerileri de (kaç üyede olduğu sayıyla). Kimlik ve ad eklenmez (§7.10)."""
    donem = _kurullar()
    hesap = [k for k in _pano()["isler"] if k["kod"] == "HESAP_ONERISI"]
    # Görev bölümü yapılmamış yönetim kurulunda hesap alacak görev yoktur; Denetleme Kurulunun üç
    # asılının hiçbirinin hesabı yoktur.
    assert [(k["ek"]["tur"], k["ek"]["rol"], k["ek"]["sayi"]) for k in hesap] == [
        ("HESAP_AC", "denetleme_kurulu", 3)
    ]
    _, ogretmen1, ogretmen2 = OrganMembership.objects.filter(term=donem, organ="DK").order_by("pk")
    for uyelik in (ogretmen1, ogretmen2):
        uyelikler.update_membership(
            uyelik,
            external_assignment_start=date(2026, 10, 16),
            external_assignment_end=date(2027, 3, 30),
        )
    (dk_yedek,) = [
        k for k in _pano()["isler"] if k["kod"] == "YEDEK_CAGRISI" and k["ek"]["organ"] == "DK"
    ]
    assert (dk_yedek["ek"]["sayi"], dk_yedek["atif"]) == (2, "md. 14/6")


def _eksik(donem: OabTerm, uyelik: OrganMembership, kural_id: str) -> ComplianceItem:
    sonuc = uyum.denetle(kural_id, VERI_YOK, donem=donem, konu=uyelik, tarih=o.SECIM_GUNU)
    assert sonuc.satir is not None and sonuc.satir.kind == "EKSIK"
    return sonuc.satir


def test_tamamlanacaklar_rol_gorunumu_ve_ekrani() -> None:
    """Açık `EKSIK` satırları her rolde "tamamlanacaklar"dadır; görev alma engeli satırının iletisini ve
    atfını yalnız program yöneticisi ve yönetim kurulu rolleri görür (kullanıcı kararı 10.11.2026).
    Satır konusunun ekranına götürür; kapanan satır düşer."""
    donem = o.donem()
    yk = o.secilmis(donem)
    dk, *_ = o.dk_kurulu(donem)
    engel = _eksik(donem, yk, "uyelik.suc_engeli")
    _eksik(donem, dk, "denetleme_kurulu.baskan_secilme_siniri")
    # Aynı dönemde gerekçeli açık SAPMA satırı (başka üyelikte): eksik değildir, listeye girmez (O3).
    sapma = uyum.bilinmeyen_beyan_sapmasi(
        "uyelik.suc_engeli",
        donem=donem,
        konu=o.secilmis(donem),
        mesaj="Uydurma beyan.",
        gerekce=uyum.Gerekce(metin="Uydurma gerekçe."),
        tarih=o.SECIM_GUNU,
    )
    assert sapma is not None
    assert (sapma.kind, sapma.resolved_at) == (ComplianceKind.SAPMA, None)
    for rol in ROLLER:
        satirlar = _pano(rol)["tamamlanacaklar"]
        assert [(s["kod"], s["rota"], s["sekme"]) for s in satirlar] == [
            ("EKSIK", "/organlar", "yk"),
            ("EKSIK", "/organlar", "dk"),
        ], rol
        if uyum.engel_dayanagini_okur_mu(rol.value):
            assert satirlar[0]["metin"] == engel.message and satirlar[0]["atif"], rol
        else:
            assert satirlar[0]["metin"] == uyum.ENGEL_GENEL_METNI and satirlar[0]["atif"] == "", rol
    uyum.eksik_kapat(engel)
    assert len(_pano()["tamamlanacaklar"]) == 1


def test_yarim_taslak_yalniz_kendi_hesabinda_ve_metinsiz() -> None:
    """Yarım metin kalemi oturumdaki hesabındır; metin dönmez, kutunun ekranına götürür. Bilinmeyen
    bağlam kalem üretmez."""
    o.donem()
    metin = "Uydurnur Taslakkaya görev bölümüne katılamadı."
    with o.rol_olarak(AccountRole.SEKRETER):
        yanit = APIClient().put(
            "/api/v1/oab/drafts/",
            {"metin": metin, "baglam": "organlar.yk_gorev_bolumu"},
            format="json",
        )
        assert yanit.status_code == 204, yanit.content
    veri = _pano(AccountRole.SEKRETER)
    (taslak,) = [k for k in veri["isler"] if k["kod"] == "YARIM_TASLAK"]
    assert (taslak["rota"], taslak["sekme"], taslak["ek"]) == (
        "/organlar",
        "yk",
        {"baglam": "organlar.yk_gorev_bolumu"},
    )
    assert "Taslakkaya" not in json.dumps(veri, ensure_ascii=False)
    for rol in (AccountRole.YONETICI, AccountRole.BASKAN):
        assert "YARIM_TASLAK" not in _kodlar(_pano(rol)), rol
    DraftText.objects.update(context="bilinmeyen.kutu")
    assert "YARIM_TASLAK" not in _kodlar(_pano(AccountRole.SEKRETER))


@pytest.mark.parametrize(
    ("baglam", "sekme"),
    [
        ("organlar.yedek_cagrisi.yk", "yk"),
        ("organlar.yedek_cagrisi.dk", "dk"),
        ("organlar.dusme.yk", "yk"),
        ("organlar.dusme.dk", "dk"),
    ],
)
def test_yedek_ve_dusme_taslagi_kendi_kurulunun_sekmesine(baglam: str, sekme: str) -> None:
    """Yedek çağrısı ve düşme pencereleri iki kurulda da açılır: bağlam kurulludur, kalem taslağın
    yazıldığı kurulun sekmesine götürür (program yöneticisinin Denetleme Kurulu yedek çağrısı
    taslağı Yönetim Kurulu sekmesine değil)."""
    o.donem()
    yanit = APIClient().put(
        "/api/v1/oab/drafts/", {"metin": "Uydurma.", "baglam": baglam}, format="json"
    )
    assert yanit.status_code == 204, yanit.content
    (taslak,) = [k for k in _pano()["isler"] if k["kod"] == "YARIM_TASLAK"]
    assert (taslak["rota"], taslak["sekme"], taslak["ek"]) == (
        "/organlar",
        sekme,
        {"baglam": baglam},
    )


def test_kisi_adi_taramasi_bos() -> None:
    """Pano kişisizdir: uydurma adlı kişilerle her rolün yanıtında ad ve soyad geçmez."""
    donem = o.donem()
    adlar = []
    for i in range(4):
        kisi = o.kisi(first_name=f"Uydurnur{i} Panokaya", last_name="Kalemoğlu")
        adlar.extend([kisi.first_name, "Kalemoğlu"])
        o.secilmis(donem, kisi)
    yedek = o.kisi(first_name="Yedekbey Panokaya", last_name="Kalemoğlu")
    o.secilmis(donem, yedek, seat_type=SeatType.YEDEK, seat_order=1)
    dk = o.secilmis(
        donem,
        o.kisi(first_name="Denetnur Panokaya", last_name="Kalemoğlu"),
        organ="DK",
        seat_group=SeatGroup.VELI,
    )
    _eksik(donem, dk, "denetleme_kurulu.baskan_secilme_siniri")
    desen = re.compile("Panokaya|Kalemoğlu|Uydurnur|Yedekbey|Denetnur", re.IGNORECASE)
    for rol in ROLLER:
        govde = json.dumps(_pano(rol), ensure_ascii=False)
        assert not desen.search(govde), (rol, desen.search(govde))


_YAZAN = re.compile(r"^\s*(INSERT|UPDATE|DELETE|REPLACE)\b", re.IGNORECASE)


def test_hesap_hicbir_sey_yazmaz() -> None:
    """Okuma işidir: bütün kaynaklar doluyken (iki yedek çağrısı dâhil) her rolün okumasında
    veritabanına yazan sorgu yoktur."""
    donem = o.donem()
    o.yk_kurulu(donem, asil=4, yedek=1)
    dk = o.dk_kurulu(donem)
    uyelikler.update_membership(
        dk[1],
        external_assignment_start=date(2026, 10, 16),
        external_assignment_end=date(2027, 3, 30),
    )
    uye = OrganMembership.objects.filter(term=donem, organ="YK").first()
    assert uye is not None
    _eksik(donem, uye, "uyelik.suc_engeli")
    APIClient().put(
        "/api/v1/oab/drafts/", {"metin": "Uydurma.", "baglam": "gecis.devralinan"}, format="json"
    )
    # Kaynaklar gerçekten dolu: iki kurulun yedek çağrısı, görev bölümü, kadro, geçiş, hesap, taslak.
    yonetici = _pano()
    assert {k["ek"].get("organ") for k in yonetici["isler"] if k["kod"] == "YEDEK_CAGRISI"} == {
        "YK",
        "DK",
    }
    assert {
        "YK_GOREV_BOLUMU",
        "DK_GOREV_BOLUMU",
        "KADRO",
        "GECIS_ADIMI",
        "HESAP_ONERISI",
        "YARIM_TASLAK",
    } <= set(_kodlar(yonetici))
    assert yonetici["tamamlanacaklar"]
    assert "YEDEK_CAGRISI" in _kodlar(_pano(AccountRole.SEKRETER))
    for rol in ROLLER:
        with o.rol_olarak(rol), CaptureQueriesContext(connection) as sorgular:
            yanit = APIClient().get(UC)
        assert yanit.status_code == 200, yanit.content
        yazanlar = [s["sql"] for s in sorgular.captured_queries if _YAZAN.match(s["sql"])]
        assert yazanlar == [], (rol, yazanlar)


def test_kilitliyken_423_ve_yazma_yok() -> None:
    """Kilitliyken uç 423 döner; denetim izi, uyum satırları ve yarım metin tablosu değişmez."""
    donem = _kurullar()
    uye = OrganMembership.objects.filter(term=donem, organ="YK").first()
    assert uye is not None
    _eksik(donem, uye, "uyelik.suc_engeli")
    APIClient().put(
        "/api/v1/oab/drafts/", {"metin": "Uydurma.", "baglam": "gecis.devralinan"}, format="json"
    )
    iz_durumu.capa_yaz()
    app_password.lock()
    once = (AuditTrail.objects.count(), ComplianceItem.objects.count(), DraftText.objects.count())
    with CaptureQueriesContext(connection) as sorgular:
        yanit = APIClient().get(UC)
    assert yanit.status_code == 423, yanit.content
    assert [s["sql"] for s in sorgular.captured_queries if _YAZAN.match(s["sql"])] == []
    sonra = (AuditTrail.objects.count(), ComplianceItem.objects.count(), DraftText.objects.count())
    assert sonra == once


def test_d7_bilgi_doner_kuralli_kalem_cikmaz() -> None:
    """Kural kopyası doğrulanamayan dönemde (D7) uç 503 değil 200 döner: bilgi kalemi çıkar, kurallı
    kalemler (süre, kadro, yedek) çıkmaz; kuralsız kalemler (geçiş, hesap, tamamlanacaklar) çalışır."""
    donem = _kurullar()
    uye = OrganMembership.objects.filter(term=donem, organ="YK").first()
    assert uye is not None
    _eksik(donem, uye, "uyelik.suc_engeli")
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE oab_rulepackage SET content_sha256 = %s WHERE id = %s",
            ["0" * 64, donem.rule_package_id],
        )
    for rol in ROLLER:
        veri = _pano(rol)
        assert [b["kod"] for b in veri["bilgiler"]] == ["KURAL_KOPYASI_DOGRULANAMADI"], rol
        assert not (
            {"YK_GOREV_BOLUMU", "DK_GOREV_BOLUMU", "KADRO", "YEDEK_CAGRISI"} | _GK_KODLARI
        ) & set(_kodlar(veri)), rol
        assert len(veri["tamamlanacaklar"]) == 1 and veri["tamamlanacaklar"][0]["atif"] == ""
    kodlar = set(_kodlar(_pano()))
    assert {"GECIS_ADIMI", "HESAP_ONERISI"} <= kodlar


def test_donem_yok_ve_iptal_bilgisi() -> None:
    """Açık birlik dönemi yokken bilgi kalemi çıkar (son dönem iptal edildiyse bunu söyler); program
    yöneticisinde geçişin ilk adımı açık kalır. Organ kalemi ve tamamlanacak yoktur."""
    veri = _pano()
    assert veri["bilgiler"] == [
        {
            "kod": "DONEM_YOK",
            "vade": None,
            "gecikti": False,
            "rota": "/birlik-donemi",
            "sekme": "",
            "metin": "",
            "atif": "",
            "ek": {"son_durum": ""},
        }
    ]
    assert [k["ek"]["adim"] for k in veri["isler"]] == ["donem"]
    assert _pano(AccountRole.SEKRETER)["isler"] == []
    donem = o.donem()
    gecis.donemi_iptal_et(donem, cancel_reason="Uydurma iptal gerekçesi.")
    assert OabTerm.objects.get(pk=donem.pk).status == TermStatus.IPTAL
    for rol in ROLLER:
        veri = _pano(rol)
        assert veri["bilgiler"][0]["ek"] == {"son_durum": "IPTAL"}, rol
        assert veri["tamamlanacaklar"] == [], rol


def test_kadro_uyarilari_kaynakla_ayni() -> None:
    """Kadro kalemleri kadro okumasının uyarılarıdır (tek kaynak, `uyelikler.kadro_uyarilari`)."""
    donem = _kurullar()
    beklenen = [s["mesaj"] for s in uyelikler.kadro_uyarilari(donem, "YK", tarih=GUN)]
    kadro = [k["metin"] for k in _pano(AccountRole.SEKRETER)["isler"] if k["kod"] == "KADRO"]
    assert kadro == beklenen and beklenen


def test_tek_kaynagin_kurali_okunamazsa_oteki_kaynaklar_calisir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bir kaynağın kuralı olay gününde okunamazsa yalnız o kaynağın kalemi düşer; yedek çağrısı ve
    kadro kalemleri çıkar (`_kuralli_kalemler`: her kaynak ayrı okunur)."""
    donem = o.donem()
    o.yk_kurulu(donem, asil=4, yedek=1)
    o.dk_kurulu(donem)
    assert {"YK_GOREV_BOLUMU", "KADRO", "YEDEK_CAGRISI"} <= set(_kodlar(_pano()))

    def _okunamaz(*_a: Any, **_k: Any) -> None:
        raise YururlukteDegerYok("Uydurma: olay gününde yürürlükte değer yok.")

    # Görev bölümü süresi kaynakların ilkidir: hatası sonrakileri kesmemeli.
    monkeypatch.setattr(pano, "_gorev_bolumu_kalemi", _okunamaz)
    kodlar = set(_kodlar(_pano()))
    assert not {"YK_GOREV_BOLUMU", "DK_GOREV_BOLUMU"} & kodlar
    assert {"KADRO", "YEDEK_CAGRISI"} <= kodlar


def test_gun_europe_istanbul_gunudur(monkeypatch: pytest.MonkeyPatch) -> None:
    """UTC 19.10.2026 21:30, Europe/Istanbul'da 20.10.2026 00:30'dur: kalemlerin günü yerel gündür
    (UTC günü bir gün geride kalırdı ve son günü dün olan kalem gecikmemiş görünürdü)."""
    monkeypatch.setattr(pano, "bugun", _GERCEK_BUGUN)
    monkeypatch.setattr(
        "django.utils.timezone.now", lambda: datetime(2026, 10, 19, 21, 30, tzinfo=UTC)
    )
    assert pano.bugun() == date(2026, 10, 20)
    assert pano.kalemler(None, None)["bugun"] == "2026-10-20"


def _eksik_satiri(donem: OabTerm, kural_id: str, konu_turu: str, konu_kimligi: str) -> None:
    """Ekran eşlemesi için doğrudan açık EKSIK satırı (yalnız kural ve konu okunur; uydurma)."""
    ComplianceItem.objects.create(
        term=donem,
        kind=ComplianceKind.EKSIK,
        subject_type=konu_turu,
        subject_id=konu_kimligi,
        rule_id=kural_id,
        message="Uydurma eksik iletisi.",
    )


@pytest.mark.parametrize(
    ("durum", "beklenen"),
    [
        ("temsilci_kurali", ("/temsilciler", "")),
        ("temsilci_uyeligi", ("/temsilciler", "")),
        ("kisi", ("/kisiler", "birlik")),
        ("defter", ("/birlik-donemi/gecis-kurulumu", "")),
        ("donem", ("/birlik-donemi", "")),
    ],
)
def test_tamamlanacak_satirinin_ekrani(durum: str, beklenen: tuple[str, str]) -> None:
    """Tamamlanacak satırı konusunun ekranına götürür (§7.10 "tek tıkla ilgili ekrana"): temsilci
    kuralı ve temsilci üyeliği Temsilciler'e, kişi Birlik Kişileri'ne, defter Geçiş Kurulumu'na,
    öteki (dönem konulu) Birlik Dönemi'ne."""
    donem = o.donem()
    donem_turu = denetim_izi.model_etiketi(OabTerm)
    if durum == "temsilci_kurali":
        _eksik_satiri(donem, "temsilci.kantin_denetim_komisyonu", donem_turu, str(donem.pk))
    elif durum == "temsilci_uyeligi":
        temsilci = temsilciler.temsilci_ekle(
            term=donem,
            person=o.kisi(),
            representation="SOSYAL_ETKINLIKLER_KURULU",
            start_date=date(2026, 10, 20),
        )
        _eksik_satiri(
            donem,
            "uyelik.suc_engeli",
            denetim_izi.model_etiketi(OrganMembership),
            str(temsilci.pk),
        )
    elif durum == "kisi":
        kural_id = next(iter(kisiler.SAYAC_KURALLARI.values()))
        _eksik_satiri(donem, kural_id, denetim_izi.model_etiketi(OabPerson), str(o.kisi().pk))
    elif durum == "defter":
        _eksik_satiri(donem, kurullar.TASDIK_KURALI, denetim_izi.model_etiketi(OfficialBook), "1")
    else:
        _eksik_satiri(donem, "yonetim_kurulu.asil_uye", donem_turu, str(donem.pk))
    (satir,) = _pano()["tamamlanacaklar"]
    assert (satir["rota"], satir["sekme"]) == beklenen


# ---------------------------------------------------------------------------
# F2: genel kurul süreleri (plan §6.3, 12. adım)
# ---------------------------------------------------------------------------
#: Genel kurulun ilan ve ikinci toplantı kalemlerini gören roller (plan §6.3 "Roller").
GK_SURE_ROLLERI = {
    AccountRole.YONETICI,
    AccountRole.SEKRETER,
    AccountRole.BASKAN,
    AccountRole.BASKAN_YARDIMCISI,
}


def _gun(monkeypatch: pytest.MonkeyPatch, gun: date) -> None:
    monkeypatch.setattr(pano, "bugun", lambda gun=gun: gun)


def _isler(veri: dict[str, Any], kod: str) -> list[dict[str, Any]]:
    return [k for k in veri["isler"] if k["kod"] == kod]


def _goren_roller(kod: str) -> set[AccountRole]:
    return {rol for rol in ROLLER if kod in _kodlar(_pano(rol))}


def _ilan_gunu() -> int:
    return int(kural("genel_kurul.ilan_en_az_gun"))


def test_f2_olagan_genel_kurul_planlanmadi_sinir_gunleri_ve_roller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Açık dönemin ders yılından sonraki ders yılı başladı, olağan genel kurul planlanmadı (md. 9/1):
    son gün Ekim sonundaki bir toplantının ilanının son günüdür (`olagan_son_ay` − `ilan_en_az_gun`);
    tam son gün gecikmemiş, ertesi gün gecikmiştir. Yeni ders yılı başlamadan kalem yoktur. Kalem
    program yöneticisinde, sekreterde, başkanda, başkan yardımcısında ve müdürde (md. 27/1)."""
    gko.acik_donem()
    son_gun = date(2026, 10, 31)
    vade = son_gun - timedelta(days=_ilan_gunu())
    for gun, gecikti in (
        (vade - timedelta(days=1), False),
        (vade, False),
        (vade + timedelta(days=1), True),
    ):
        _gun(monkeypatch, gun)
        (kalem,) = _isler(_pano(), "GK_OLAGAN")
        assert (kalem["vade"], kalem["gecikti"], kalem["rota"], kalem["sekme"]) == (
            vade.isoformat(),
            gecikti,
            "/genel-kurul",
            "",
        ), gun
        # Son gün iki kuraldan çıkar: Ekim sonu (md. 9/1) ve ilan süresi (md. 9/3).
        assert kalem["atif"] == "md. 9/1, 9/3"
        assert kalem["ek"] == {
            "durum": "PLANLANMADI",
            "son_gun": son_gun.isoformat(),
            "ilan_gun": _ilan_gunu(),
            "ilan_atif": "md. 9/3",
        }
    assert _goren_roller("GK_OLAGAN") == GK_SURE_ROLLERI | {AccountRole.MUDUR}
    # 2026-2027 ders yılı 07.09.2026'da başlar: bir gün önce bu yılın genel kurulu sorulmaz.
    _gun(monkeypatch, date(2026, 9, 6))
    assert "GK_OLAGAN" not in _kodlar(_pano())
    _gun(monkeypatch, date(2026, 9, 7))
    assert "GK_OLAGAN" in _kodlar(_pano())


def test_f2_birinci_toplanti_siniri_asiyor_europe_istanbul_gece_yarisi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Planlanmış olağan genel kurulun birinci toplantısı Ekim sonunu aşıyorsa kalem genel kurula
    götürür, son gün sınırdır (S3). Gün Europe/Istanbul günüdür: 01.11.2026 00:30 UTC'de 31.10.2026
    21:30'dur ama sınırı aşar; 31.10.2026 23:30 aşmaz. İlanın son günü de yerel günden sayılır."""
    gko.acik_donem()
    _gun(monkeypatch, date(2026, 10, 1))
    kurul = gko.planla(birinci=gko.an(date(2026, 11, 1), 0, 30), gerekce=gko.GEREKCE)
    veri = _pano()
    (kalem,) = _isler(veri, "GK_OLAGAN")
    assert (kalem["vade"], kalem["gecikti"], kalem["atif"]) == ("2026-10-31", False, "md. 9/1")
    assert kalem["ek"] == {"durum": "SINIRI_ASIYOR", "son_gun": "2026-10-31", "kurul": kurul.pk}
    (ilan,) = _isler(veri, "GK_ILAN")
    assert ilan["vade"] == (date(2026, 11, 1) - timedelta(days=_ilan_gunu())).isoformat()
    _gun(monkeypatch, date(2026, 11, 1))
    assert _isler(_pano(), "GK_OLAGAN")[0]["gecikti"] is True
    gk.toplanti_bilgisini_degistir(kurul, first_meeting_at=gko.an(date(2026, 10, 31), 23, 30))
    # Planlanmış ve sınırın içindeki genel kurulda "planlanmadı" kalemi de yoktur.
    assert _goren_roller("GK_OLAGAN") == set()


def test_f2_ilan_son_gunu_ve_eksik_kanal_kaniti(monkeypatch: pytest.MonkeyPatch) -> None:
    """İlan edilmemiş genel kurulda son gün birinci toplantı − `ilan_en_az_gun` (md. 9/3); ilandan
    sonra kanıt günü girilmemiş kanal ilan başına kalemdir (aynı son günle) ve tamamlanacak satırı
    genel kurulun ekranına götürür; kanıt girilince ikisi de düşer. Müdür, muhasip ve Denetleme
    Kurulu görmez."""
    gko.acik_donem()
    kurul = gko.planla()
    vade = gko.BIRINCI_GUN - timedelta(days=_ilan_gunu())
    for gun, gecikti in (
        (vade - timedelta(days=1), False),
        (vade, False),
        (vade + timedelta(days=1), True),
    ):
        _gun(monkeypatch, gun)
        (kalem,) = _isler(_pano(), "GK_ILAN")
        assert (kalem["vade"], kalem["gecikti"], kalem["atif"]) == (
            vade.isoformat(),
            gecikti,
            "md. 9/3",
        )
        assert kalem["ek"] == {
            "durum": "ILAN_BEKLIYOR",
            "toplanti": "BIRINCI",
            "ilan_gun": _ilan_gunu(),
            "kurul": kurul.pk,
        }
    assert _goren_roller("GK_ILAN") == GK_SURE_ROLLERI
    kurul = gko.olagan_cagir(kurul)
    assert _isler(_pano(), "GK_ILAN")[0]["ek"]["durum"] == "ILAN_BEKLIYOR"
    gk.ilan_et(
        kurul,
        kanallar=gk.IlanKanallari(
            distributed_written_on=gko.ILAN_GUNU, posted_board_on=gko.ILAN_GUNU
        ),
    )
    _gun(monkeypatch, gko.ILAN_GUNU + timedelta(days=1))
    veri = _pano()
    (kalem,) = _isler(veri, "GK_ILAN")
    assert (kalem["vade"], kalem["gecikti"]) == (vade.isoformat(), True)
    assert kalem["ek"] == {
        "durum": "KANIT_EKSIK",
        "toplanti": "BIRINCI",
        "eksik": "INTERNET_SAYFASI",
        "kurul": kurul.pk,
    }
    genel_kurul_satirlari = [s for s in veri["tamamlanacaklar"] if s["rota"] == "/genel-kurul"]
    assert len(genel_kurul_satirlari) == 1
    assert (genel_kurul_satirlari[0]["sekme"], genel_kurul_satirlari[0]["ek"]) == (
        "",
        {"kurul": kurul.pk},
    )
    assert _goren_roller("GK_ILAN") == GK_SURE_ROLLERI
    gk.ilan_kanitlarini_yaz(gk.kurulun_duyurulari(kurul)[0], kanallar=gko.kanallar())
    veri = _pano()
    assert "GK_ILAN" not in _kodlar(veri)
    assert all(s["rota"] != "/genel-kurul" for s in veri["tamamlanacaklar"])


def test_f2_ikinci_toplantinin_son_gunu(monkeypatch: pytest.MonkeyPatch) -> None:
    """Birinci toplantıda yeter sayı sağlanamadı: son gün birinci toplantı +
    `ikinci_toplanti_en_gec_gun` (md. 9/2); ikinci toplantı yapılınca düşer."""
    kurul = gko.ilanli_olagan()
    gk.birinci_toplanti(kurul, katilim=gko.katilim(gko.BIRINCIDE_KATILAN))
    sure = int(kural("genel_kurul.ikinci_toplanti_en_gec_gun"))
    vade = gko.BIRINCI_GUN + timedelta(days=sure)
    for gun, gecikti in (
        (vade - timedelta(days=1), False),
        (vade, False),
        (vade + timedelta(days=1), True),
    ):
        _gun(monkeypatch, gun)
        (kalem,) = _isler(_pano(), "GK_IKINCI_TOPLANTI")
        assert (kalem["vade"], kalem["gecikti"], kalem["atif"], kalem["rota"]) == (
            vade.isoformat(),
            gecikti,
            "md. 9/2",
            "/genel-kurul",
        )
        assert kalem["ek"] == {
            "kurul": kurul.pk,
            "sure_gun": sure,
            "ilan_gun": _ilan_gunu(),
            "ilan_atif": "md. 9/3",
            "tarihli": 0,
            "olaganustu": 0,
        }
    assert _goren_roller("GK_IKINCI_TOPLANTI") == GK_SURE_ROLLERI
    _gun(monkeypatch, date(2026, 10, 22))
    gk.ikinci_toplanti_ilani(
        kurul, second_meeting_at=gko.an(gko.IKINCI_GUN), kanallar=gko.kanallar(date(2026, 10, 21))
    )
    veri = _pano()
    assert _isler(veri, "GK_IKINCI_TOPLANTI")[0]["ek"]["tarihli"] == 1
    assert "GK_ILAN" not in _kodlar(veri)  # iki ilanın da üç kanalı girildi
    gk.ikinci_toplanti(kurul, katilim=gko.katilim(gko.IKINCIDE_KATILAN))
    assert not {"GK_IKINCI_TOPLANTI", "GK_ILAN"} & set(_kodlar(_pano()))


def test_f2_donem_onayi_gorev_bolumu_ikinci_toplanti_gununden_ve_tefbis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tutanağı tamamlanmış olağan genel kurulun hazırlık dönemi onay bekler (U32; yalnız program
    yöneticisi, süresiz). Onaydan sonra görev bölümü süresi genel kurulun yapıldığı günden (ikinci
    toplantı; U6) işler; okul idaresinin üç TEFBİS girişi (md. 23/5) yalnız program yöneticisinde,
    süresiz (mevzuatta süre yok: md. 23/5; "genel kuruldan hemen sonra" yalnız rehberde, tasarım §5.2.7):
    son gün ve gecikme gösterilmez."""
    kurul = gko.ikinci_toplantida_yapilmis_olagan()
    gko.kurullari_sec(kurul)
    gk.ibra_yaz(gko.madde(kurul, "IBRA"), yk=gko.IBRA_EDILDI, dk=gko.IBRA_EDILDI)
    gk.tutanagi_tamamla(kurul)
    _gun(monkeypatch, gko.IKINCI_GUN + timedelta(days=1))
    (onay,) = _isler(_pano(), "DONEM_ONAYI")
    assert (onay["vade"], onay["gecikti"], onay["rota"], onay["atif"]) == (
        None,
        False,
        "/genel-kurul",
        "",
    )
    assert onay["ek"] == {"kurul": kurul.pk, "baslangic": gko.IKINCI_GUN.isoformat()}
    assert _goren_roller("DONEM_ONAYI") == {AccountRole.YONETICI}
    assert "GK_OLAGAN" not in _kodlar(_pano())
    gk.donem_gecisini_onayla(kurul)
    veri = _pano()
    assert "DONEM_ONAYI" not in _kodlar(veri)
    gorev = int(kural("yonetim_kurulu.gorev_bolumu_gun"))
    (yk_kalemi,) = _isler(veri, "YK_GOREV_BOLUMU")
    assert yk_kalemi["vade"] == (gko.IKINCI_GUN + timedelta(days=gorev)).isoformat()
    tefbis = _isler(veri, "TEFBIS_GIRISI")
    assert {k["ek"]["yukumluluk"] for k in tefbis} == {
        "TEFBIS_YONETIM_BILGISI",
        "TEFBIS_BANKA_BILGISI",
        "TEFBIS_BUTCE_GIRISI",
    }
    assert all(
        (k["vade"], k["rota"], k["ek"]["kurul"], k["gecikti"], k["atif"])
        == (None, "/genel-kurul", kurul.pk, False, "")
        for k in tefbis
    )
    assert all(isinstance(k["ek"]["satir"], int) for k in tefbis)
    assert all("TEFBİS" in k["metin"] and "md. 23/5" in k["metin"] for k in tefbis)
    assert _goren_roller("TEFBIS_GIRISI") == {AccountRole.YONETICI}
    # Yeni dönemin ders yılı bu yılınkidir: bu yılın genel kurulu yapıldı, kalem yok.
    assert "GK_OLAGAN" not in _kodlar(veri)


def test_f2_ibra_edilmedi_bildirimi_kapanistaki_donemde_de(monkeypatch: pytest.MonkeyPatch) -> None:
    """Yönetim kurulu ibra edilmedi: il/ilçe MEM'e bildirimin takvim satırı (md. 11/1-ç) program
    yöneticisinde ve sekreterde; ileti satırın kişisiz iletisidir. Kalem süresizdir (md. 11/1-ç süre
    koymaz): genel kurulun ertesi günü de "süresi doldu" olmaz. Dönem geçişinden sonra satır kapanıştaki
    dönemdedir, kalem sürer."""
    kurul = gko.yapilmis_olagan()
    gko.kurullari_sec(kurul)
    gk.ibra_yaz(gko.madde(kurul, "IBRA"), yk=gko.IBRA_EDILMEDI, dk=gko.IBRA_EDILDI)
    gk.tutanagi_tamamla(kurul)
    (satir,) = ComplianceItem.objects.filter(
        kind=ComplianceKind.TAKVIM, obligation="IBRA_EDILMEDI_BILDIRIMI"
    )
    for gun in (gko.BIRINCI_GUN, gko.BIRINCI_GUN + timedelta(days=1), date(2027, 3, 1)):
        _gun(monkeypatch, gun)
        (kalem,) = _isler(_pano(AccountRole.SEKRETER), "IBRA_BILDIRIMI")
        assert (kalem["vade"], kalem["gecikti"], kalem["rota"], kalem["atif"]) == (
            None,
            False,
            "/genel-kurul",
            "",
        )
        assert kalem["metin"] == gk.ibra_bildirimi_mesaji(kurul)
        assert kalem["ek"] == {
            "yukumluluk": "IBRA_EDILMEDI_BILDIRIMI",
            "satir": satir.pk,
            "salt_okur": False,
            "kurul": kurul.pk,
        }
    assert _goren_roller("IBRA_BILDIRIMI") == {AccountRole.YONETICI, AccountRole.SEKRETER}
    gk.donem_gecisini_onayla(kurul)
    assert kurul.term_id is not None
    assert OabTerm.objects.get(pk=kurul.term_id).status == TermStatus.KAPANISTA
    assert _goren_roller("IBRA_BILDIRIMI") == {AccountRole.YONETICI, AccountRole.SEKRETER}


def test_f2_yeni_okulun_ilk_genel_kurulu_ve_mudurun_daveti(monkeypatch: pytest.MonkeyPatch) -> None:
    """Yeni açılan okul (okul kartında açılış günü, birlik dönemi yok): ilk genel kurul açılıştan
    `yeni_okul_ay` içinde (md. 9/1). Planlanmadıysa son gün sınırdaki toplantının ilanının son günü;
    geçiş kurulumunun "ilk birlik dönemi" kalemi çıkmaz (S5 (iii)). Planlanınca müdürün daveti bekler
    (yalnız müdür); sınır günü aşılmaz, ertesi gün aşar; davetten sonra çağrı yazısı bekler."""
    gko.ders_yillari()
    gko.mevcut()
    acilis = date(2026, 9, 15)
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(opened_on=acilis)
    son_gun = takvim.ay_ekle(acilis, int(kural("genel_kurul.yeni_okul_ay")))
    vade = son_gun - timedelta(days=_ilan_gunu())
    for gun, gecikti in ((vade, False), (vade + timedelta(days=1), True)):
        _gun(monkeypatch, gun)
        veri = _pano()
        (kalem,) = _isler(veri, "GK_YENI_OKUL")
        assert (kalem["vade"], kalem["gecikti"], kalem["atif"], kalem["rota"]) == (
            vade.isoformat(),
            gecikti,
            "md. 9/1, 9/3",
            "/genel-kurul",
        )
        assert kalem["ek"] == {
            "durum": "PLANLANMADI",
            "son_gun": son_gun.isoformat(),
            "ilan_gun": _ilan_gunu(),
            "ilan_atif": "md. 9/3",
        }
        assert "GECIS_ADIMI" not in _kodlar(veri)
    assert _goren_roller("GK_YENI_OKUL") == {AccountRole.YONETICI, AccountRole.MUDUR}
    _gun(monkeypatch, date(2026, 10, 1))
    kurul = gko.planla(birinci=gko.an(son_gun))
    assert "GK_YENI_OKUL" not in _kodlar(_pano())
    (davet,) = _isler(_pano(AccountRole.MUDUR), "MUDUR_YAZISI")
    # Son gün birinci toplantı − ilan süresi: atıf iki kuralı birlikte taşır (md. 9/1, 9/3).
    assert (davet["vade"], davet["atif"], davet["ek"]) == (
        (son_gun - timedelta(days=_ilan_gunu())).isoformat(),
        "md. 9/1, 9/3",
        {
            "tur": "YENI_OKUL_DAVETI",
            "kurul": kurul.pk,
            "ilan_gun": _ilan_gunu(),
            "ilan_atif": "md. 9/3",
        },
    )
    assert _goren_roller("MUDUR_YAZISI") == {AccountRole.MUDUR}
    assert _goren_roller("GK_ILAN") == GK_SURE_ROLLERI
    gk.toplanti_bilgisini_degistir(
        kurul, first_meeting_at=gko.an(son_gun + timedelta(days=1)), gerekce=gko.GEREKCE
    )
    (kalem,) = _isler(_pano(AccountRole.MUDUR), "GK_YENI_OKUL")
    assert kalem["ek"] == {
        "durum": "SINIRI_ASIYOR",
        "son_gun": son_gun.isoformat(),
        "kurul": kurul.pk,
    }
    with o.rol_olarak(AccountRole.MUDUR):
        gk.cagir(kurul)
    (yazi,) = _isler(_pano(AccountRole.MUDUR), "MUDUR_YAZISI")
    assert yazi["ek"]["tur"] == "CAGRI_YAZISI"


def test_f2_mudurun_olaganustu_cagrisinin_yazisi_uretilince_duser() -> None:
    """Müdürün olağanüstü çağrısı (md. 9/6) kaydedildi, çağrı yazısı üretilmedi: yalnız müdüre kalem
    (son gün ilanın son günü: dayanak md. 9/6, 9/3); yazı üretilince düşer. Çağıranı belli olmayan
    planlanmış olağanüstü genel kurul müdüre kalem üretmez."""
    kurul = gke_ortak.kurulum(gke.KOL_MUDUR_9_6)
    (kalem,) = _isler(_pano(AccountRole.MUDUR), "MUDUR_YAZISI")
    assert (kalem["atif"], kalem["ek"]) == (
        "md. 9/6, 9/3",
        {
            "tur": "CAGRI_YAZISI",
            "kurul": kurul.pk,
            "ilan_gun": _ilan_gunu(),
            "ilan_atif": "md. 9/3",
        },
    )
    assert _goren_roller("MUDUR_YAZISI") == {AccountRole.MUDUR}
    with o.rol_olarak(AccountRole.MUDUR):
        gke.uret("E05", kurul, toplanti="BIRINCI")
    assert "MUDUR_YAZISI" not in _kodlar(_pano(AccountRole.MUDUR))
    gko.planla(kind=AssemblyKind.OLAGANUSTU)
    assert "MUDUR_YAZISI" not in _kodlar(_pano(AccountRole.MUDUR))


def test_f2_veri_sorumlusu_tamamlanacak() -> None:
    """Okul kartında veri sorumlusu girilmediyse kişisel veri aydınlatma metni üretilmez (tasarım §9.6
    E04): yalnız program yöneticisinin "tamamlanacaklar"ında, birlik dönemi olmasa da; Okul
    Bilgileri'ne götürür. Girilince düşer."""
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(data_controller_text="  ")
    (satir,) = _pano()["tamamlanacaklar"]
    assert (satir["kod"], satir["rota"], satir["sekme"], satir["metin"]) == (
        "VERI_SORUMLUSU",
        "/ayarlar",
        "okul",
        "",
    )
    for rol in ROLLER[1:]:
        assert _pano(rol)["tamamlanacaklar"] == [], rol
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(
        data_controller_text=VERI_SORUMLUSU
    )
    assert _pano()["tamamlanacaklar"] == []


def _f2_kaynaklari_dolu() -> None:
    """Uydurma adlı kişilerle F2 kalemlerinin çoğu: ibra edilmedi bildirimi ve dönem onayı bekleyen
    olağan genel kurul (aday ve veli adları uydurma), planlanmış olağanüstü genel kurul (ilanın son
    günü)."""
    kurul = gko.yapilmis_olagan()
    gko.veli_aktar([("Velinur PANOKAYA", "5-A"), ("Velibey KALEMOĞLU", "6-B")])
    yk = [
        gko.aday(kurul, kisi=o.kisi(first_name=f"Adaynur{i}", last_name="Panokaya"))
        for i in range(5)
    ]
    dk = [gko.aday(kurul, organ="DK", kisi=o.kisi(first_name="Denetnur", last_name="Kalemoğlu"))]
    gko.secim(kurul, "SECIM_YK", yk)
    gko.secim(kurul, "SECIM_DK", dk)
    gk.ibra_yaz(gko.madde(kurul, "IBRA"), yk=gko.IBRA_EDILMEDI, dk=gko.IBRA_EDILDI)
    gk.tutanagi_tamamla(kurul)
    gko.planla(kind=AssemblyKind.OLAGANUSTU, birinci=gko.an(date(2026, 11, 20)))


def test_f2_kisi_adi_taramasi_bos(monkeypatch: pytest.MonkeyPatch) -> None:
    """F2 kalemleri kişisizdir: aday ve veli adları hiçbir rolün yanıtında geçmez."""
    _gun(monkeypatch, date(2026, 10, 21))
    _f2_kaynaklari_dolu()
    assert {"IBRA_BILDIRIMI", "DONEM_ONAYI", "GK_ILAN"} <= set(_kodlar(_pano()))
    desen = re.compile("Panokaya|Kalemoğlu|Velinur|Velibey|Adaynur|Denetnur", re.IGNORECASE)
    for rol in ROLLER:
        govde = json.dumps(_pano(rol), ensure_ascii=False)
        assert not desen.search(govde), (rol, desen.search(govde))


def test_f2_okuma_yazmaz_iz_dusmez(monkeypatch: pytest.MonkeyPatch) -> None:
    """F2 kaynakları doluyken (takvim satırı, dönem onayı, ilan, veri sorumlusu) her rolün okuması
    veritabanına yazmaz ve denetim izine satır düşmez."""
    _gun(monkeypatch, date(2026, 10, 21))
    _f2_kaynaklari_dolu()
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(data_controller_text="")
    yonetici = _pano()
    assert {"IBRA_BILDIRIMI", "DONEM_ONAYI", "GK_ILAN"} <= set(_kodlar(yonetici))
    assert any(s["kod"] == "VERI_SORUMLUSU" for s in yonetici["tamamlanacaklar"])
    for rol in ROLLER:
        # Rolün hesabı (testin kurgusu) kendi iz satırını yazar: sayım hesap kurulduktan sonradır.
        with o.rol_olarak(rol):
            once = (AuditTrail.objects.count(), ComplianceItem.objects.count())
            with CaptureQueriesContext(connection) as sorgular:
                yanit = APIClient().get(UC)
            sonra = (AuditTrail.objects.count(), ComplianceItem.objects.count())
        assert yanit.status_code == 200, yanit.content
        yazanlar = [s["sql"] for s in sorgular.captured_queries if _YAZAN.match(s["sql"])]
        assert yazanlar == [], (rol, yazanlar)
        assert sonra == once, rol


def test_f2_bir_genel_kurul_kaynaginin_kurali_okunamazsa_otekiler_calisir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """İlan kaynağının kuralı okunamazsa (D7 benzeri) yalnız ilan kalemi düşer; ikinci toplantı
    kalemi çıkar."""
    kurul = gko.ilanli_olagan()
    gk.ilan_kanitlarini_yaz(
        gk.kurulun_duyurulari(kurul)[0],
        kanallar=gk.IlanKanallari(distributed_written_on=gko.ILAN_GUNU),
    )
    gk.birinci_toplanti(kurul, katilim=gko.katilim(gko.BIRINCIDE_KATILAN))
    assert {"GK_ILAN", "GK_IKINCI_TOPLANTI"} <= set(_kodlar(_pano()))

    def _okunamaz(*_a: Any, **_k: Any) -> None:
        raise YururlukteDegerYok("Uydurma: olay gününde yürürlükte değer yok.")

    monkeypatch.setattr(pano, "_ilan_kalemleri", _okunamaz)
    kodlar = set(_kodlar(_pano()))
    assert "GK_ILAN" not in kodlar and "GK_IKINCI_TOPLANTI" in kodlar


# ---------------------------------------------------------------------------
# F2 12. adımın denetim bulguları: takvim satırının "Yapıldı" işareti, A-1 atfı, yeni okulun
# tamamlanacakları, gerçek D7, gündem maddesi ve ikinci ilan kalemleri
# ---------------------------------------------------------------------------
def _yapildi(satir_id: int, gun: str, rol: AccountRole | None = None) -> Any:
    yol = f"/api/v1/oab/compliance-items/{satir_id}/done/"
    if rol is None or rol == AccountRole.YONETICI:
        return APIClient().post(yol, {"done_on": gun}, format="json")
    with o.rol_olarak(rol):
        return APIClient().post(yol, {"done_on": gun}, format="json")


def test_f2_takvim_kalemi_yapildi_isaretiyle_duser(monkeypatch: pytest.MonkeyPatch) -> None:
    """Takvim satırının "Yapıldı" işareti (tasarım §7.10 "kalemin kapanması: … `done_on` … alınca"):
    satırın işini yapan rol yazar (plan F2 §6.3 "Roller"). İbra edilmedi bildirimini yeni yönetim kurulu
    ve okul yönetimi yapar (md. 11/1-ç): program yöneticisi ve sekreter (md. 13/4); TEFBİS'e kaydı okul
    idaresi yapar (md. 23/5): yalnız program yöneticisi, sekreter TEFBİS satırını işaretleyemez. Öteki
    roller hiçbirini işaretleyemez. İşaret izlidir, satır silinmez; kalem düşer. Gelecek gün, ikinci
    işaret ve takvim olmayan satır reddedilir. Kapanıştaki dönemin ibra bildirimi de işaretlenir."""
    kurul = gko.yapilmis_olagan()
    gko.kurullari_sec(kurul)
    gk.ibra_yaz(gko.madde(kurul, "IBRA"), yk=gko.IBRA_EDILMEDI, dk=gko.IBRA_EDILDI)
    gk.tutanagi_tamamla(kurul)
    gk.donem_gecisini_onayla(kurul)
    veri = _pano()
    (ibra,) = _isler(veri, "IBRA_BILDIRIMI")
    tefbis = _isler(veri, "TEFBIS_GIRISI")
    assert len(tefbis) == 3
    bugun = timezone.localdate()
    ibra_satiri = ibra["ek"]["satir"]
    for rol in ROLLER:
        if rol in (AccountRole.YONETICI, AccountRole.SEKRETER):
            continue
        assert _yapildi(ibra_satiri, bugun.isoformat(), rol).status_code == 403, rol
        assert _yapildi(tefbis[0]["ek"]["satir"], bugun.isoformat(), rol).status_code == 403, rol
    sekreter_tefbis = _yapildi(tefbis[0]["ek"]["satir"], bugun.isoformat(), AccountRole.SEKRETER)
    assert sekreter_tefbis.status_code == 403, sekreter_tefbis.content
    gelecek = _yapildi(ibra_satiri, (bugun + timedelta(days=1)).isoformat(), AccountRole.SEKRETER)
    assert gelecek.status_code == 400, gelecek.content
    assert (
        ComplianceItem.objects.filter(kind=ComplianceKind.TAKVIM).exclude(done_on=None).count() == 0
    )
    once = AuditTrail.objects.count()
    yanit = _yapildi(ibra_satiri, gko.IKINCI_GUN.isoformat(), AccountRole.SEKRETER)
    assert yanit.status_code == 200, yanit.content
    assert yanit.json() == {"id": ibra_satiri, "done_on": gko.IKINCI_GUN.isoformat()}
    assert AuditTrail.objects.count() > once
    satir = ComplianceItem.objects.get(pk=ibra_satiri)
    assert (satir.done_on, satir.term.status) == (gko.IKINCI_GUN, TermStatus.KAPANISTA)
    assert _yapildi(ibra_satiri, bugun.isoformat()).status_code == 400  # ikinci işaret
    for rol in (AccountRole.YONETICI, AccountRole.SEKRETER):
        assert "IBRA_BILDIRIMI" not in _kodlar(_pano(rol)), rol
    for kalem in tefbis:
        assert _yapildi(kalem["ek"]["satir"], bugun.isoformat()).status_code == 200
    assert "TEFBIS_GIRISI" not in _kodlar(_pano())
    assert ComplianceItem.objects.filter(kind=ComplianceKind.TAKVIM, done_on=None).count() == 0
    eksik = ComplianceItem.objects.exclude(kind=ComplianceKind.TAKVIM).first()
    if eksik is not None:
        assert _yapildi(eksik.pk, bugun.isoformat()).status_code == 404


def test_f2_olaganustu_genel_kurulda_ikinci_toplanti_a1_atfi() -> None:
    """md. 9/2 olağan genel kurulu düzenler; olağanüstü genel kurulda 30 gün kullanıcı kararı A-1 ile
    uygulanır (plan F2 §7 U10): kalemin atfı bunu söyler, Yönetmelik hükmü gibi yalnız "md. 9/2"
    basılmaz. Olağan genel kurulda atıf yalnız "md. 9/2"dir (`test_f2_ikinci_toplantinin_son_gunu`)."""
    gko.acik_donem()
    kurul = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    gk.ilan_et(kurul, kanallar=gko.kanallar())
    gk.birinci_toplanti(kurul, katilim=gko.katilim(gko.BIRINCIDE_KATILAN))
    (kalem,) = _isler(_pano(), "GK_IKINCI_TOPLANTI")
    assert kalem["atif"] == f"md. 9/2; {pano.A1_ATIF_EKI}"
    assert "kullanıcı kararı A-1" in kalem["atif"]
    assert (kalem["ek"]["olaganustu"], kalem["ek"]["ilan_atif"]) == (1, "md. 9/3")


def test_f2_yeni_okulda_ilanin_eksik_kanali_tamamlanacaklarda() -> None:
    """Yeni açılan okulun ilk genel kurulunun satırları hazırlık dönemindedir (`kural_donemi`): açık
    dönem yokken ilanın kanıtı eksik kanalı "tamamlanacaklar"da çıkar ve genel kurulun ekranına götürür
    (O3; modül başlığı `GK_ILAN`). Kanıt girilince düşer."""
    gko.ders_yillari()
    gko.mevcut()
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(opened_on=date(2026, 9, 15))
    kurul = gko.planla(birinci=gko.an(date(2026, 11, 10)))
    with o.rol_olarak(AccountRole.MUDUR):
        kurul = gk.cagir(kurul).kurul
    gk.ilan_et(
        kurul,
        kanallar=gk.IlanKanallari(
            distributed_written_on=date(2026, 10, 20), posted_board_on=date(2026, 10, 20)
        ),
    )
    assert not OabTerm.objects.filter(status=TermStatus.ACIK).exists()
    veri = _pano()
    assert [b["kod"] for b in veri["bilgiler"]] == ["DONEM_YOK"]
    (ilan,) = _isler(veri, "GK_ILAN")
    assert ilan["ek"]["durum"] == "KANIT_EKSIK"
    satirlar = [s for s in veri["tamamlanacaklar"] if s["rota"] == "/genel-kurul"]
    assert satirlar, veri["tamamlanacaklar"]
    assert all((s["sekme"], s["ek"]) == ("", {"kurul": kurul.pk}) for s in satirlar)
    assert any(s["atif"] == "md. 9/3" for s in satirlar)
    gk.ilan_kanitlarini_yaz(gk.kurulun_duyurulari(kurul)[0], kanallar=gko.kanallar())
    veri = _pano()
    assert "GK_ILAN" not in _kodlar(veri)
    assert all(s["atif"] != "md. 9/3" for s in veri["tamamlanacaklar"])


def _kopyayi_boz(donem: OabTerm) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE oab_rulepackage SET content_sha256 = %s WHERE id = %s",
            ["0" * 64, donem.rule_package_id],
        )


_GK_KODLARI = {"GK_OLAGAN", "GK_YENI_OKUL", "GK_ILAN", "GK_IKINCI_TOPLANTI", "MUDUR_YAZISI"}


def test_f2_gercek_d7_genel_kurul_kalemleri_duser_takvim_calisir() -> None:
    """Gerçek D7 (dönemin kural kopyası doğrulanamıyor): açık dönemin ders yılından sonraki ders yılı
    başlamış ve olağan genel kurul planlanmış. Uç her rolde 200 döner, bilgi KURAL_KOPYASI_DOGRULANAMADI;
    genel kurul kalemleri (olağan genel kurul, ilan, ikinci toplantı, müdürün yazısı) çıkmaz; kuralsız
    takvim kalemi (TEFBİS) çalışır."""
    donem = gko.acik_donem()
    gko.planla()
    uyum.takvim_satiri_yaz(
        "TEFBIS_BANKA_BILGISI",
        donem=donem,
        due_date=date(2026, 10, 1),
        mesaj="Uydurma takvim iletisi (md. 23/5).",
        responsible_role=AccountRole.YONETICI.value,
    )
    assert {"GK_ILAN", "TEFBIS_GIRISI"} <= set(_kodlar(_pano()))
    _kopyayi_boz(donem)
    for rol in ROLLER:
        veri = _pano(rol)
        assert [b["kod"] for b in veri["bilgiler"]] == ["KURAL_KOPYASI_DOGRULANAMADI"], rol
        assert not _GK_KODLARI & set(_kodlar(veri)), rol
    (tefbis,) = _isler(_pano(), "TEFBIS_GIRISI")
    # Dönem salt okurdur: "Yapıldı" işareti 409 (ön yüz düğmeyi çizmez).
    yanit = _yapildi(tefbis["ek"]["satir"], date(2026, 10, 1).isoformat())
    assert (yanit.status_code, yanit.json()["code"]) == (409, "donem_salt_okur"), yanit.content


def test_f2_gercek_d7_planlanmadi_kalemi_duser(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gerçek D7, olağan genel kurul planlanmamış: "planlanmadı" kaynağının kuralı okunamaz, kalem
    düşer, uç 200 döner."""
    donem = gko.acik_donem()
    assert "GK_OLAGAN" in _kodlar(_pano())
    _kopyayi_boz(donem)
    for rol in ROLLER:
        assert not _GK_KODLARI & set(_kodlar(_pano(rol))), rol


def test_f2_gercek_d7_yeni_okulun_hazirlik_donemi() -> None:
    """Yeni açılan okulda ilk genel kurulun hazırlık döneminin kopyası doğrulanamıyor: sınırı aşan
    ilk genel kurulun kalemi ve ilan kalemi çıkmaz, uç 200 döner; tamamlanacakların atfı boş kalır."""
    gko.ders_yillari()
    gko.mevcut()
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(opened_on=date(2026, 9, 15))
    son_gun = takvim.ay_ekle(date(2026, 9, 15), int(kural("genel_kurul.yeni_okul_ay")))
    kurul = gko.planla(birinci=gko.an(son_gun + timedelta(days=1)), gerekce=gko.GEREKCE)
    assert {"GK_YENI_OKUL", "GK_ILAN"} <= set(_kodlar(_pano()))
    assert kurul.opens_term is not None
    _kopyayi_boz(kurul.opens_term)
    for rol in ROLLER:
        veri = _pano(rol)
        assert not _GK_KODLARI & set(_kodlar(veri)), rol
        assert all(s["atif"] == "" for s in veri["tamamlanacaklar"] if s["kod"] == "EKSIK"), rol


def test_f2_gundem_maddesinin_eksigi_genel_kurula_goturur() -> None:
    """Seçimin biçimi girilmeden kaydedilen seçim (md. 10/1-d; `genel_kurul.secim_bicimi` VERI_YOK)
    gündem maddesi konulu eksik satırıdır: "tamamlanacaklar"da genel kurulun ekranına götürür (`ek.kurul`),
    Birlik Dönemi'ne düşmez."""
    kurul = gko.yapilmis_olagan()
    yk = [gko.aday(kurul) for _ in range(5)]
    gko.secim(kurul, "SECIM_YK", yk, liste=None, acik_oy=None)
    madde = gko.madde(kurul, "SECIM_YK")
    satir = ComplianceItem.objects.get(
        kind=ComplianceKind.EKSIK,
        rule_id="genel_kurul.secim_bicimi",
        subject_type=denetim_izi.model_etiketi(type(madde)),
        subject_id=str(madde.pk),
        resolved_at=None,
    )
    tamamlanacaklar = _pano()["tamamlanacaklar"]
    (kalem,) = [s for s in tamamlanacaklar if s["metin"] == satir.message]
    assert (kalem["rota"], kalem["sekme"], kalem["ek"]) == ("/genel-kurul", "", {"kurul": kurul.pk})


def test_f2_ikinci_ilanin_eksik_kanali(monkeypatch: pytest.MonkeyPatch) -> None:
    """İkinci toplantının ilanında kanıt günü girilmemiş kanal: ilk ilanın kanıtı tamken yalnız ikinci
    ilan için tek kalem çıkar (`toplanti` IKINCI); son gün ikinci toplantı − `ilan_en_az_gun` (md. 9/3);
    tam son gün gecikmemiş, ertesi gün gecikmiş. Kanıt girilince düşer."""
    kurul = gko.ilanli_olagan()
    gk.birinci_toplanti(kurul, katilim=gko.katilim(gko.BIRINCIDE_KATILAN))
    _gun(monkeypatch, date(2026, 10, 21))
    gk.ikinci_toplanti_ilani(
        kurul,
        second_meeting_at=gko.an(gko.IKINCI_GUN),
        kanallar=gk.IlanKanallari(distributed_written_on=date(2026, 10, 21)),
    )
    vade = gko.IKINCI_GUN - timedelta(days=_ilan_gunu())
    for gun, gecikti in ((vade, False), (vade + timedelta(days=1), True)):
        _gun(monkeypatch, gun)
        (kalem,) = _isler(_pano(), "GK_ILAN")
        assert (kalem["vade"], kalem["gecikti"], kalem["atif"], kalem["rota"]) == (
            vade.isoformat(),
            gecikti,
            "md. 9/3",
            "/genel-kurul",
        )
        assert kalem["ek"] == {
            "durum": "KANIT_EKSIK",
            "toplanti": "IKINCI",
            "eksik": "ILAN_PANOSU,INTERNET_SAYFASI",
            "kurul": kurul.pk,
        }
    assert _goren_roller("GK_ILAN") == GK_SURE_ROLLERI
    gk.ilan_kanitlarini_yaz(
        gk.kurulun_duyurulari(kurul)[1], kanallar=gko.kanallar(date(2026, 10, 21))
    )
    assert "GK_ILAN" not in _kodlar(_pano())


# ---------------------------------------------------------------------------
# F2 12. adımın bağımsız denetimi (Y1, Y2, Y4): tutanaktan sonra değişen ibra, yapıldığı günün alt
# sınırı, kapanmış dönemde işaret
# ---------------------------------------------------------------------------
#: Salondaki sayısı girilmemiş yönetim kurulu ibrası: payda katılımdır (S6 (iii)); 36 kabul oyu 70
#: katılımda "edildi", 72 katılımda "edilmedi"dir (`genel_kurul.karar_cogunlugu`).
_IBRA_OYLARI = gk.IbraOylamasi(votes_for=36, votes_against=30)


def _katilimi_duzelt(kurul: Any, sayi: int) -> None:
    gk.katilim_duzelt(
        kurul,
        toplanti="BIRINCI",
        degerler={"first_attendee_count": sayi},
        justification="Uydurma: sayım hatası.",
        gerekce=gko.GEREKCE,
    )


def _ibra_satirlari() -> list[ComplianceItem]:
    return list(
        ComplianceItem.objects.filter(
            kind=ComplianceKind.TAKVIM, obligation="IBRA_EDILMEDI_BILDIRIMI"
        ).order_by("pk")
    )


def _yk_ibrasi(kurul: Any) -> str:
    return str(GeneralAssembly.objects.get(pk=kurul.pk).discharge_yk)


def test_f2_tutanaktan_sonra_ibra_iki_yonlu_degisir_tek_satir() -> None:
    """Tutanaktan sonra katılım düzeltilip yönetim kurulunun ibrası değişirse (düzeltme
    `TUTANAK_TAMAM`'da da yapılır): "edilmedi → edildi"de bildirim satırı silinmez, yapıldı sayılmaz
    (uydurma gün yazılmaz), yalnız panoda gizlenir; "edildi → edilmedi"de yapılmamış satır varken
    yenisi yazılmaz, aynı satır yeniden görünür (md. 11/1-ç; altın kural 4)."""
    kurul = gko.yapilmis_olagan(72)
    gk.ibra_yaz(gko.madde(kurul, "IBRA"), yk=_IBRA_OYLARI, dk=gko.IBRA_EDILDI)
    gk.tutanagi_tamamla(kurul)
    (satir,) = _ibra_satirlari()
    (kalem,) = _isler(_pano(), "IBRA_BILDIRIMI")
    assert kalem["ek"]["satir"] == satir.pk
    # Edilmedi → edildi: satır yerinde ve yapılmamış, kalem yok.
    _katilimi_duzelt(kurul, 70)
    assert _yk_ibrasi(kurul) == "EDILDI"
    assert [(s.pk, s.done_on) for s in _ibra_satirlari()] == [(satir.pk, None)]
    for rol in (AccountRole.YONETICI, AccountRole.SEKRETER):
        assert "IBRA_BILDIRIMI" not in _kodlar(_pano(rol)), rol
    # Edildi → edilmedi: yeni satır yazılmaz, aynı satır yeniden görünür.
    _katilimi_duzelt(kurul, 72)
    assert _yk_ibrasi(kurul) == "EDILMEDI"
    assert [(s.pk, s.done_on) for s in _ibra_satirlari()] == [(satir.pk, None)]
    (kalem,) = _isler(_pano(AccountRole.SEKRETER), "IBRA_BILDIRIMI")
    assert kalem["ek"]["satir"] == satir.pk


def test_f2_tutanakta_ibra_edilmis_kurul_iki_kez_edilmedi_olursa_tek_satir() -> None:
    """Tutanakta "ibra edildi": satır yoktur. Düzeltmeyle "edilmedi" bir satır yazar; "edildi"ye
    dönüşte kalem gizlenir, yeniden "edilmedi" ikinci satır yazmaz."""
    kurul = gko.yapilmis_olagan()
    gk.ibra_yaz(gko.madde(kurul, "IBRA"), yk=_IBRA_OYLARI, dk=gko.IBRA_EDILDI)
    gk.tutanagi_tamamla(kurul)
    assert _ibra_satirlari() == []
    assert "IBRA_BILDIRIMI" not in _kodlar(_pano())
    _katilimi_duzelt(kurul, 72)
    assert _yk_ibrasi(kurul) == "EDILMEDI"
    (satir,) = _ibra_satirlari()
    assert [k["ek"]["satir"] for k in _isler(_pano(), "IBRA_BILDIRIMI")] == [satir.pk]
    _katilimi_duzelt(kurul, 70)
    assert _yk_ibrasi(kurul) == "EDILDI"
    assert "IBRA_BILDIRIMI" not in _kodlar(_pano())
    _katilimi_duzelt(kurul, 72)
    assert [s.pk for s in _ibra_satirlari()] == [satir.pk]
    assert [k["ek"]["satir"] for k in _isler(_pano(), "IBRA_BILDIRIMI")] == [satir.pk]


def test_f2_yapildigi_gun_genel_kurul_gununden_once_olamaz() -> None:
    """Takvim satırının son günü yükümlülüğün doğduğu gündür (genel kurulun yapıldığı gün): iş ondan
    önce yapılmış olamaz. Daha önceki gün sert retle reddedilir (işaret bir kez konur, düzeltme yolu
    yoktur), satır değişmez, iz düşmez; tam o gün kabul edilir."""
    kurul = gko.yapilmis_olagan()
    gk.ibra_yaz(gko.madde(kurul, "IBRA"), yk=gko.IBRA_EDILMEDI, dk=gko.IBRA_EDILDI)
    gk.tutanagi_tamamla(kurul)
    (satir,) = _ibra_satirlari()
    assert satir.due_date == gko.BIRINCI_GUN
    ileti = uyum.TAKVIM_GUNU_GENEL_KURULDAN_ONCE.format(gun=gko.BIRINCI_GUN)
    assert "(20.10.2026)" in ileti
    once = AuditTrail.objects.count()
    for gun in (date(1900, 1, 1), gko.BIRINCI_GUN - timedelta(days=1)):
        yanit = _yapildi(satir.pk, gun.isoformat())
        assert yanit.status_code == 400, (gun, yanit.content)
        assert ileti in json.dumps(yanit.json(), ensure_ascii=False), yanit.content
    assert ComplianceItem.objects.get(pk=satir.pk).done_on is None
    assert AuditTrail.objects.count() == once
    yanit = _yapildi(satir.pk, gko.BIRINCI_GUN.isoformat())
    assert yanit.status_code == 200, yanit.content
    assert ComplianceItem.objects.get(pk=satir.pk).done_on == gko.BIRINCI_GUN


def test_f2_yapildigi_gunun_alt_siniri_yalniz_genel_kuruldan_dogan_satirda() -> None:
    """Alt sınır (`due_date`'ten önce olamaz) yalnız konusu genel kurul olan satırdadır: orada
    `due_date` genel kurulun yapıldığı gündür. Konusu genel kurul olmayan takvim satırının `due_date`'i
    gerçek son gündür (öteki fazların yükümlülükleri, ör. defter tasdiki): son günden önce yapılmış
    işaretlenir. Uydurma satırlar."""
    donem = gko.acik_donem()
    kurul = gko.planla()
    bugun = timezone.localdate()
    son_gunlu = uyum.takvim_satiri_yaz(
        "DEFTER_TASDIK",
        donem=donem,
        due_date=bugun,
        mesaj="Uydurma takvim iletisi (son günlü yükümlülük).",
        responsible_role=AccountRole.YONETICI.value,
    )
    once = bugun - timedelta(days=30)
    yanit = _yapildi(son_gunlu.pk, once.isoformat())
    assert yanit.status_code == 200, yanit.content
    assert ComplianceItem.objects.get(pk=son_gunlu.pk).done_on == once
    kurul_konulu = uyum.takvim_satiri_yaz(
        "TEFBIS_BANKA_BILGISI",
        donem=donem,
        due_date=bugun,
        mesaj="Uydurma takvim iletisi (md. 23/5).",
        responsible_role=AccountRole.YONETICI.value,
        konu=kurul,
    )
    ileti = uyum.TAKVIM_GUNU_GENEL_KURULDAN_ONCE.format(gun=bugun)
    yanit = _yapildi(kurul_konulu.pk, (bugun - timedelta(days=1)).isoformat())
    assert yanit.status_code == 400, yanit.content
    assert ileti in json.dumps(yanit.json(), ensure_ascii=False), yanit.content
    assert ComplianceItem.objects.get(pk=kurul_konulu.pk).done_on is None


def _kapanista_ve_acik_donem() -> tuple[ComplianceItem, OabTerm, OabTerm]:
    """İbra edilmedi bildirimi kapanıştaki dönemde, yeni dönem açık (dönem geçişi onaylandı). İki dönem
    aynı revizyonun kopyasına bağlı açılır; açık dönem aynı içerikli uydurma bir revizyona (kural
    sürümü güncellemesi gibi) bağlanır ki iki dönemin kopyası ayrı ayrı bozulabilsin."""
    kurul = gko.yapilmis_olagan()
    gko.kurullari_sec(kurul)
    gk.ibra_yaz(gko.madde(kurul, "IBRA"), yk=gko.IBRA_EDILMEDI, dk=gko.IBRA_EDILDI)
    gk.tutanagi_tamamla(kurul)
    gk.donem_gecisini_onayla(kurul)
    kurul = GeneralAssembly.objects.get(pk=kurul.pk)
    assert kurul.term_id is not None and kurul.opens_term_id is not None
    kapanista = OabTerm.objects.get(pk=kurul.term_id)
    gercek = kapanista.rule_package
    ayri = RulePackage.objects.create(
        package=gercek.package,
        rev=gercek.rev + 100,
        schema_version=gercek.schema_version,
        content=gercek.content,
        content_sha256=gercek.content_sha256,
    )
    OabTerm.objects.filter(pk=kurul.opens_term_id).update(rule_package=ayri)
    acik = OabTerm.objects.get(pk=kurul.opens_term_id)
    assert (kapanista.status, acik.status) == (TermStatus.KAPANISTA, TermStatus.ACIK)
    assert donem_kilidi.kural_kopyasi_tutuyor(acik)
    (satir,) = _ibra_satirlari()
    assert satir.term_id == kapanista.pk
    return satir, kapanista, acik


def test_f2_takvim_kaleminin_salt_okuru_satirin_donemine_gore_acik_donem_d7() -> None:
    """Açık dönemin kopyası doğrulanamıyor (D7), kapanıştaki dönemin kopyası tutuyor: kapanıştaki
    dönemin satırının kalemi `salt_okur` false (düğme çizilir) ve uç işareti kabul eder; kararın
    kaynağı tektir (`donem_kilidi.kural_kopyasi_tutuyor`)."""
    satir, _kapanista, acik = _kapanista_ve_acik_donem()
    _kopyayi_boz(acik)
    veri = _pano(AccountRole.SEKRETER)
    assert [b["kod"] for b in veri["bilgiler"]] == ["KURAL_KOPYASI_DOGRULANAMADI"]
    (kalem,) = _isler(veri, "IBRA_BILDIRIMI")
    assert (kalem["ek"]["satir"], kalem["ek"]["salt_okur"]) == (satir.pk, False)
    yanit = _yapildi(satir.pk, gko.IKINCI_GUN.isoformat(), AccountRole.SEKRETER)
    assert yanit.status_code == 200, yanit.content


def test_f2_takvim_kaleminin_salt_okuru_satirin_donemine_gore_kapanistaki_d7() -> None:
    """Kapanıştaki dönemin kopyası doğrulanamıyor (D7), açık dönemin kopyası tutuyor: panoda bant
    yoktur ama kapanıştaki dönemin satırının kalemi `salt_okur` true (düğme çizilmez); uç işareti
    409 `donem_salt_okur` ile reddeder, satır değişmez."""
    satir, kapanista, _acik = _kapanista_ve_acik_donem()
    _kopyayi_boz(kapanista)
    veri = _pano(AccountRole.SEKRETER)
    assert veri["bilgiler"] == []
    (kalem,) = _isler(veri, "IBRA_BILDIRIMI")
    assert (kalem["ek"]["satir"], kalem["ek"]["salt_okur"]) == (satir.pk, True)
    yanit = _yapildi(satir.pk, gko.IKINCI_GUN.isoformat(), AccountRole.SEKRETER)
    assert (yanit.status_code, yanit.json()["code"]) == (409, "donem_salt_okur"), yanit.content
    assert ComplianceItem.objects.get(pk=satir.pk).done_on is None


def test_f2_kapanmis_donemde_yapildi_isareti_409() -> None:
    """Kapanmış dönemin takvim satırı işaretlenmez: 409 `donem_kapali` (tasarım §5 O2; işaret beyaz
    listede değildir), satır değişmez, iz düşmez. Kalem de çıkmaz (yalnız açık ve kapanıştaki dönem)."""
    donem = gko.acik_donem()
    satir = uyum.takvim_satiri_yaz(
        "TEFBIS_BANKA_BILGISI",
        donem=donem,
        due_date=date(2026, 10, 1),
        mesaj="Uydurma takvim iletisi (md. 23/5).",
        responsible_role=AccountRole.YONETICI.value,
    )
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.KAPANDI, end_date=date(2027, 10, 1)
    )
    assert "TEFBIS_GIRISI" not in _kodlar(_pano())
    once = AuditTrail.objects.count()
    yanit = _yapildi(satir.pk, date(2026, 10, 2).isoformat())
    assert (yanit.status_code, yanit.json()["code"]) == (409, "donem_kapali"), yanit.content
    assert ComplianceItem.objects.get(pk=satir.pk).done_on is None
    assert AuditTrail.objects.count() == once
