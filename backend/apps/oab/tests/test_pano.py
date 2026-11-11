"""Genel Bakış'ın pano kalemleri (tasarım §7.10; plan F1c 12. adım "pano kabuğu").

Sınananlar: rol başına görünüm (§7.10 tablosu, her rolde), kalemin götürdüğü ekran, gün değişimi
(gün `pano.bugun` ile sabitlenir; günün Europe/Istanbul günü olduğu ayrıca), kalemin kaynak kayıt
kapanınca düşmesi, kişi adı taraması (uydurma adlarla yanıt gövdesinde ad yok), aynı önerilerin
kişisiz sayımla tek kaleme toplanması, hesaplamanın hiçbir şey yazmaması (sorgu sayacı) ve
kilitliyken uçtan yazma olmaması (423, tablolar değişmez), D7'de ucun 503 değil bilgiyle dönmesi, tek
kaynağın kuralı okunamayınca ötekilerin çalışması. Adlar ve tarihler UYDURMADIR.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from typing import Any

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.oab.kurallar import VERI_YOK, YururlukteDegerYok
from apps.oab.models import (
    ComplianceItem,
    ComplianceKind,
    DraftText,
    OabPerson,
    OabTerm,
    OfficialBook,
    OrganMembership,
    SeatGroup,
    SeatType,
    TermStatus,
)
from apps.oab.services import gecis, kisiler, kurullar, pano, temsilciler, uyelikler, uyum
from apps.oab.tests import uyelik_ortak as o
from apps.okul import denetim_izi, iz_durumu
from apps.okul.models import AccountRole, AuditTrail
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


@pytest.fixture(autouse=True)
def gunu_sabitle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pano, "bugun", lambda: GUN)


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
        assert not {"YK_GOREV_BOLUMU", "DK_GOREV_BOLUMU", "KADRO", "YEDEK_CAGRISI"} & set(
            _kodlar(veri)
        ), rol
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
