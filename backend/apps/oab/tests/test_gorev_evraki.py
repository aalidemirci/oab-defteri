"""E01, E02, E03'ün uçları, rolleri, basım izi ve basım uyarıları (plan F1c 10. adım).

Sabitlenenler: (1) E01 ve E03'ü yalnız sekreter ve program yöneticisi, E02'yi yalnız Denetleme Kurulu
üretir (tasarım §9.6 "Üreten"; uç ve servis kapısı); başkan ve başkan yardımcısı okur ve basar; (2)
basım her okur rolde `BASIM` satırı yazar (kod ve dosyanın sha256'sı; kaydın kimliği belgenin konusu),
erişim günlüğüne girmez; HEAD basmaz; dosya okunamazsa bayt ve iz yoktur; (3) liste dönemin geçerli
kayıtlarıdır; (4) basım uyarıları: geçişte görev bölümü toplantısı yoksa A bölümü boş, görev ve
koltuk boşsa "………", denetim planı ve müdürün adı yoksa; E01'in görev tablosu ve imzaları kurulun
koltuk sayısını aşmaz; uyarılar belgeye basılmaz; (5) karar deftere işlenince sıra no ve sayfa
basılır, iptal edilen karar basılmaz; (6) yazı alanında 9 puntodan küçük metin yok; (7) kapanmış
dönemde yeni sürüm yalnız aynı içerikle yazılır, kurallar dönemin son günüyle okunur; (8) dosya deposu
yazılamazsa kayıt da yazılmaz; (9) yedekten çağrılan asıl çağrı günüyle, olağanüstü genel kurulla
yenilenen kurulda o genel kurulun günü; (10) teslim alan müdürün adı müdür kişi kaydının ayrık
alanlarından. Adlar UYDURMADIR.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import quote

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.oab.models import (
    AssemblyKind,
    BoardDecision,
    DecisionKind,
    DecisionStatus,
    DocumentStatus,
    GeneratedDocument,
    MembershipRole,
    OabTerm,
    SeatGroup,
    TermStatus,
)
from apps.oab.services import evrak as evrak_servisi
from apps.oab.services import genel_kurul as genel_kurul_servisi
from apps.oab.services import (
    gorev_evraki,
    kisiler,
    kurullar,
    uyelik_gecisleri,
    uyelikler,
    uyum,
)
from apps.oab.tests import uyelik_ortak as o
from apps.oab.tests.kurallar import gorev_evraki_ortak as ge_ortak
from apps.okul.models import AccessLog, AccountRole, AuditAction, AuditTrail
from apps.okul.oturum import Yazar, yazar_olarak
from apps.okul.services import dosya_deposu
from conftest import TEST_HESAP_ID
from shared import docx as cizici
from shared import evrak
from shared.exceptions import RolYetkisiz
from shared.tests.test_evrak import pdf_yazi_boyutlari

pytestmark = pytest.mark.django_db

URETEN: dict[str, set[AccountRole]] = {
    "E01": {AccountRole.YONETICI, AccountRole.SEKRETER},
    "E02": {AccountRole.DENETLEME_KURULU},
    "E03": {AccountRole.YONETICI, AccountRole.SEKRETER},
}


def _yol(kod: str, donem: OabTerm) -> str:
    return f"/api/v1/oab/terms/{donem.pk}/documents/{kod.lower()}/"


def _post(kod: str, donem: OabTerm, rol: AccountRole = AccountRole.YONETICI) -> Any:
    if rol == AccountRole.YONETICI:
        return APIClient().post(_yol(kod, donem), {}, format="json")
    with o.rol_olarak(rol):
        return APIClient().post(_yol(kod, donem), {}, format="json")


def _uret(kod: str, donem: OabTerm) -> tuple[GeneratedDocument, list[str]]:
    rol = AccountRole.DENETLEME_KURULU if kod == "E02" else AccountRole.YONETICI
    yanit = _post(kod, donem, rol)
    assert yanit.status_code == 201, yanit.content
    return GeneratedDocument.objects.get(pk=yanit.json()["evrak"]["id"]), yanit.json()["uyarilar"]


def _tablolar(belge: evrak.Belge) -> list[evrak.Tablo]:
    return [b for b in belge.bloklar if isinstance(b, evrak.Tablo)]


def _imza_sahipleri(belge: evrak.Belge) -> list[evrak.ImzaSahibi]:
    return [s for b in belge.bloklar if isinstance(b, evrak.Imza) for s in b.sahipler]


def _ad(uyelik: Any) -> str:
    return evrak.ad_soyad(uyelik.person.first_name, uyelik.person.last_name)


def _basimlar() -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(action=AuditAction.BASIM).order_by("seq"))


# ============================================================ üretim ve roller


@pytest.mark.parametrize("kod", ["E01", "E02", "E03"])
def test_uretim_yalniz_ureten_rollerde(kod: str) -> None:
    """Tasarım §9.6 "Üreten" (uç kuralı): öteki her rol 403 alır, kayıt yazılmaz."""
    donem = o.donem()
    for rol in AccountRole:
        once = GeneratedDocument.objects.count()
        yanit = _post(kod, donem, rol)
        if rol in URETEN[kod]:
            assert yanit.status_code == 201, (rol, yanit.content)
            assert GeneratedDocument.objects.count() == once + 1
        else:
            assert yanit.status_code == 403, (rol, yanit.status_code)
            assert GeneratedDocument.objects.count() == once


@pytest.mark.parametrize(
    ("kod", "rol"),
    [
        ("E01", AccountRole.BASKAN),
        ("E03", AccountRole.BASKAN_YARDIMCISI),
        ("E02", AccountRole.YONETICI),
        ("E02", AccountRole.SEKRETER),
    ],
)
def test_servis_kapisi_uc_kuralindan_bagimsiz(kod: str, rol: AccountRole) -> None:
    """Servis de üreten rolü sorar (savunma derinliği; fail-closed): uç kuralı olmadan çağrılsa da
    başkan, başkan yardımcısı ve Denetleme Kurulu dışındaki roller E02'yi üretemez."""
    donem = o.donem()
    with yazar_olarak(Yazar(hesap_id=TEST_HESAP_ID, rol=rol.value)), pytest.raises(RolYetkisiz):
        gorev_evraki.uret(kod, donem)
    assert not GeneratedDocument.objects.exists()


def test_uretim_yaniti_ve_liste() -> None:
    """Yanıt evrak kaydının özeti ve basım uyarılarıdır; liste dönemin geçerli kayıtlarıdır (yeniden
    üretim yeni sürümdür, önceki kayıt listede yok)."""
    donem = o.donem()
    ilk = _post("E01", donem).json()
    assert ilk["evrak"]["kod"] == "E01" and ilk["evrak"]["surum"] == 1
    assert ilk["evrak"]["ad"] == gorev_evraki.BELGE_ADLARI["E01"]
    assert sorted(ilk["evrak"]["bicimler"]) == ["DOCX", "PDF"]
    ikinci = _post("E01", donem).json()
    _post("E03", donem)
    liste = APIClient().get(f"/api/v1/oab/terms/{donem.pk}/documents/").json()
    assert [(s["kod"], s["surum"]) for s in liste] == [("E01", 2), ("E03", 1)]
    assert liste[0]["id"] == ikinci["evrak"]["id"]
    assert liste[0]["durum"] == DocumentStatus.GECERLI


# ============================================================ basım


@pytest.mark.parametrize(
    "rol",
    [
        AccountRole.BASKAN,
        AccountRole.BASKAN_YARDIMCISI,
        AccountRole.MUHASIP,
        AccountRole.DENETLEME_KURULU,
        AccountRole.MUDUR,
    ],
)
def test_basim_okuma_rolunde_de_iz_yazar(rol: AccountRole) -> None:
    """Tasarım §4.4.2 "Okuma": evrak çıktısı okumanın kapsamındadır, `BASIM` satırı okuma rolünde de
    yazılır (kod, dosyanın sha256'sı; kaydın kimliği belgenin konusu, birlik dönemi). Erişim
    günlüğüne yazılmaz. Yanıt ek olarak, önbelleğe alınmadan; dosya adı belge + tarih."""
    donem = o.donem()
    e01, _ = _uret("E01", donem)
    e02, _ = _uret("E02", donem)
    gunluk = AccessLog.objects.count()
    with o.rol_olarak(rol) as hesap:
        for kayit, bicim in ((e01, "pdf"), (e01, "docx"), (e02, "pdf")):
            yanit: Any = APIClient().get(f"/api/v1/oab/documents/{kayit.pk}/{bicim}/")
            assert yanit.status_code == 200, (rol, kayit.doc_type, bicim)
            assert yanit["Cache-Control"] == "no-store"
            assert "attachment" in yanit["Content-Disposition"]
            ek = next(e for e in kayit.ekler() if e.mime == yanit["Content-Type"])
            assert b"".join(yanit.streaming_content) == dosya_deposu.oku(ek)
    satirlar = _basimlar()
    assert [(s.values["kod"][1], s.account_id) for s in satirlar] == [
        ("E01", hesap.id),
        ("E01", hesap.id),
        ("E02", hesap.id),
    ]
    assert {(s.model, s.object_id) for s in satirlar} == {("oab.OabTerm", str(donem.pk))}
    assert satirlar[0].values["sha256"][1] == next(e.sha256 for e in e01.ekler() if "pdf" in e.mime)
    assert AccessLog.objects.count() == gunluk


def test_basim_dosya_adi_belge_ve_tarih() -> None:
    """Sözlük §3 "Kaydedilen dosya adı": belge + üretim günü; kişi adı ve dönem adı yok."""
    donem = o.donem()
    kayit, _ = _uret("E03", donem)
    yanit = APIClient().get(f"/api/v1/oab/documents/{kayit.pk}/docx/")
    gun = timezone.localdate(kayit.generated_at)
    beklenen = gorev_evraki.dosya_adi("E03", gun, "DOCX")
    assert beklenen == f"Temsilci-Görevlendirme-Çizelgesi_{gun:%d.%m.%Y}.docx"
    assert quote(beklenen) in yanit["Content-Disposition"]


def test_basim_head_405_ve_iz_yok() -> None:
    """HEAD dosya vermez; basım izi de yazmaz (basım yalnız GET'tir)."""
    kayit, _ = _uret("E01", o.donem())
    yanit = APIClient().head(f"/api/v1/oab/documents/{kayit.pk}/pdf/")
    assert yanit.status_code == 405
    assert _basimlar() == []


def test_basim_bilinmeyen_bicim_ve_baska_evrak_404() -> None:
    """Biçim `pdf` ya da `docx`tır; bu uç yalnız E01-E03'ü basar (öteki evrakın kendi ucu vardır)."""
    donem = o.donem()
    kayit, _ = _uret("E01", donem)
    assert APIClient().get(f"/api/v1/oab/documents/{kayit.pk}/xlsx/").status_code == 404
    baska = evrak_servisi.kaydet(
        evrak.Belge(kod="E05", antet=evrak.okul_anteti(okul_adi="Örnek", ilce=None)),
        konu=donem,
        bicimler=("PDF",),
        donem=donem,
    )
    assert APIClient().get(f"/api/v1/oab/documents/{baska.pk}/pdf/").status_code == 404
    assert _basimlar() == []


def test_dosyasi_okunamayan_evrak_basilmaz_iz_yazilmaz() -> None:
    """Dosya deposundan silinmiş ek: 409 `evrak_dosyasi_acilamadi` (deponun iletisi), bayt ve
    `BASIM` satırı yok."""
    kayit, _ = _uret("E01", o.donem())
    ek = next(e for e in kayit.ekler() if "pdf" in e.mime)
    (dosya_deposu.depo_dizini() / ek.stored_name).unlink()
    yanit = APIClient().get(f"/api/v1/oab/documents/{kayit.pk}/pdf/")
    assert yanit.status_code == 409
    assert yanit.json()["code"] == "evrak_dosyasi_acilamadi"
    assert yanit.json()["message"] == str(dosya_deposu.EkDosyasiYok())
    assert _basimlar() == []


def test_dosya_yazilamazsa_kayit_yazilmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Geri yükleme sürerken (`DepoBakimda`) evrak kaydı da yazılmaz: 409 `evrak_dosyasi_yazilamadi`."""
    donem = o.donem()

    def bakimda(*_a: Any, **_k: Any) -> Any:
        raise dosya_deposu.DepoBakimda()

    monkeypatch.setattr(dosya_deposu, "yaz", bakimda)
    yanit = _post("E01", donem)
    assert yanit.status_code == 409
    assert yanit.json()["code"] == "evrak_dosyasi_yazilamadi"
    assert yanit.json()["message"] == str(dosya_deposu.DepoBakimda())
    assert not GeneratedDocument.objects.exists()


# ============================================================ basım uyarıları ve boş alanlar


def test_geciste_toplanti_yoksa_a_bolumu_bos_ve_uyari() -> None:
    """Geçişte devralınan kurulun görev bölümü toplantısı programda yoktur: A bölümü "………", basım
    uyarısı; devralınan görevler basılır, boş görevler "………" ve uyarı (plan F1c-10)."""
    ge_ortak.okul_karti()
    donem = o.donem()
    o.devralinan(donem, o.kisi(), role=MembershipRole.BASKAN)
    o.devralinan(donem, o.kisi(), role=MembershipRole.MUHASIP)
    for _ in range(3):
        o.devralinan(donem, o.kisi())
    kayit, uyarilar = _uret("E01", donem)
    assert uyarilar == [
        gorev_evraki.UYARI_TOPLANTI_YOK,
        gorev_evraki.UYARI_GOREV_BOS.format(gorev="Başkan yardımcısı"),
        gorev_evraki.UYARI_GOREV_BOS.format(gorev="Sekreter"),
        gorev_evraki.UYARI_KOLTUK_BOS,
    ]
    belge = evrak_servisi.yeniden_ciz(kayit)
    tablolar = [b for b in belge.bloklar if isinstance(b, evrak.Tablo)]
    assert {s[1] for s in tablolar[0].satirlar} == {gorev_evraki.BOS}
    gorev = tablolar[1]
    # Beş koltuk dolu: boş görevlerin ayrı "………" satırı yok (koltuk sayısını aşmaz).
    assert [s[0] for s in gorev.satirlar] == ["Başkan", "Muhasip", "Üye", "Üye", "Üye"]
    assert gorev_evraki.BOS not in {s[1] for s in gorev.satirlar}
    assert len(_imza_sahipleri(belge)) == 5
    for uyari in uyarilar:
        assert uyari not in " ".join(evrak.metin_akisi(belge))


def test_gorev_bolumunden_once_tablo_ve_imza_koltuk_sayisinca() -> None:
    """Md. 12/1, tasarım §9.6 E01 "YK asıl 5 üye": görev bölümü yapılmamış beş asılda tablo ve imza
    beş satırdır (hepsi "Üye"); dört görevin boşluğu yalnız uyarıdır, ayrı "………" satırı ve imzası
    açılmaz."""
    ge_ortak.okul_karti()
    donem = o.donem()
    asillar = [o.secilmis(donem) for _ in range(5)]
    belge, uyarilar = gorev_evraki.e01_belgesi(donem)
    gorev = _tablolar(belge)[1]
    assert [s[0] for s in gorev.satirlar] == ["Üye"] * 5
    assert [s[1] for s in gorev.satirlar] == [_ad(u) for u in asillar]
    imzalar = _imza_sahipleri(belge)
    assert [(i.ad, i.gorev) for i in imzalar] == [(_ad(u), "Üye") for u in asillar]
    for gorev_adi in ("Başkan", "Başkan yardımcısı", "Muhasip", "Sekreter"):
        assert gorev_evraki.UYARI_GOREV_BOS.format(gorev=gorev_adi) in uyarilar


def test_bos_kurulda_uyarilar() -> None:
    """Kurul ve plan girilmemişken de basılır: yerler "………", uyarılar yanıtta (E02 planı, E03'te
    müdürün adı ve imzacı görevler)."""
    ge_ortak.okul_karti(principal_name="")
    donem = o.donem()
    _, e02 = _uret("E02", donem)
    assert gorev_evraki.UYARI_PLAN_YOK in e02 and gorev_evraki.UYARI_KOLTUK_BOS in e02
    assert gorev_evraki.UYARI_GOREV_BOS.format(gorev="Başkan") in e02
    _, e03 = _uret("E03", donem)
    assert gorev_evraki.UYARI_MUDUR_ADI_YOK in e03
    assert gorev_evraki.UYARI_GOREV_BOS.format(gorev="Sekreter") in e03
    kayit, e01 = _uret("E01", donem)
    assert gorev_evraki.UYARI_KOLTUK_BOS in e01
    belge = evrak_servisi.yeniden_ciz(kayit)
    yedek = [b for b in belge.bloklar if isinstance(b, evrak.Tablo)][2]
    assert yedek.satirlar == ((gorev_evraki.BOS, gorev_evraki.BOS, ""),) * 5


def test_deftere_islenen_kararin_sira_no_ve_sayfasi_basilir() -> None:
    """Karar `TASLAK` iken "………"; deftere işlenince (F3 akışı; burada ORM'le) sıra no ve sayfa."""
    kurulum = ge_ortak.tam_kurulum()
    karar = BoardDecision.objects.get(
        meeting__term=kurulum.donem, meeting__organ="YK", meeting__status="YAPILDI"
    )
    BoardDecision.objects.filter(pk=karar.pk).update(status=DecisionStatus.KABUL_EDILDI)
    karar.refresh_from_db()
    defter = kurullar.karar_defteri_olustur(last_no_before_program=41, last_page_before_program=12)
    karar.status = DecisionStatus.DEFTERE_ISLENDI
    karar.book, karar.decision_no, karar.page_no = defter, 42, 13
    karar.save()
    belge, _ = gorev_evraki.e01_belgesi(kurulum.donem)
    toplanti = next(b for b in belge.bloklar if isinstance(b, evrak.Tablo))
    assert {s[0]: s[1] for s in toplanti.satirlar}[gorev_evraki.KARAR_DEFTERI] == "42 / 13"
    # Aynı toplantıda sonradan açılıp iptal edilen görev bölümü kararı basılmaz.
    iptal = kurullar.karar_taslagi_olustur(karar.meeting, kind=DecisionKind.GOREV_BOLUMU)
    assert iptal.pk > karar.pk
    kurullar.karar_durumu_yaz(iptal, DecisionStatus.IPTAL)
    belge, _ = gorev_evraki.e01_belgesi(kurulum.donem)
    toplanti = next(b for b in belge.bloklar if isinstance(b, evrak.Tablo))
    assert {s[0]: s[1] for s in toplanti.satirlar}[gorev_evraki.KARAR_DEFTERI] == "42 / 13"


def test_dk_veli_koltugundaki_kursiyer() -> None:
    """E02: veli koltuğundaki kursiyer "Kursiyer" (md. 14/1), asıl satırında "Asıl"."""
    donem = o.donem()
    kursiyer = o.kisi(kind="KURSIYER", is_parent=False, adult_declared=True)
    o.secilmis(donem, kursiyer, organ="DK", seat_group=SeatGroup.VELI)
    belge, _ = gorev_evraki.e02_belgesi(donem)
    uyeler = [b for b in belge.bloklar if isinstance(b, evrak.Tablo)][1]
    assert uyeler.satirlar[0][0] == "Kursiyer — genel kurul seçimi"
    assert uyeler.satirlar[0][2] == "Asıl"


def test_dk_yedekten_cagrilan_asil_cagri_gunuyle() -> None:
    """E02 (md. 14/6): öğretmen asıl düşer, öğretmen yedeği çağrılır. Çağrılanın satırı "Asıl
    (yedekten çağrıldı: gg.aa.yyyy)"; "Yedek" satırları yalnız bekleyen yedeklerdir, çağrılan orada
    yok; çağrılmamış asıllar "Asıl" kalır."""
    kurulum = ge_ortak.tam_kurulum()
    dusen, cagrilan = kurulum.dk_asillar[1], kurulum.dk_yedekler[1]
    uyelik_gecisleri.uyeligi_dusur(
        dusen, drop_kind="BASKA_KURUMDA_GOREV", end_date=date(2026, 11, 1)
    )
    uyelik_gecisleri.yedek_cagir(cagrilan, organ="DK", promoted_on=date(2026, 11, 2))
    belge, _ = gorev_evraki.e02_belgesi(kurulum.donem)
    satirlar = _tablolar(belge)[1].satirlar
    durumlar = {s[1]: s[2] for s in satirlar if s[1] != gorev_evraki.BOS}
    assert durumlar[_ad(cagrilan)] == gorev_evraki.YEDEKTEN_CAGRILDI.format(gun="02.11.2026")
    assert durumlar[_ad(cagrilan)] == "Asıl (yedekten çağrıldı: 02.11.2026)"
    assert _ad(dusen) not in durumlar
    for asil in (kurulum.dk_asillar[0], kurulum.dk_asillar[2]):
        assert durumlar[_ad(asil)] == "Asıl"
    yedekler = {s[1] for s in satirlar if s[2] == gorev_evraki.YEDEK and s[1] != gorev_evraki.BOS}
    assert yedekler == {_ad(kurulum.dk_yedekler[0]), _ad(kurulum.dk_yedekler[2])}
    assert (_ad(cagrilan), "Üye") in [(i.ad, i.gorev) for i in _imza_sahipleri(belge)]


def test_yk_baskani_duser_yedek_cagrilir_e01() -> None:
    """E01 (md. 13/6): başkan düşer, birinci yedek çağrılır (karar bağı F3'e dek yok: gerekçeyle).
    Yeni görev bölümüne dek tablo ve imza beş satırdır (başkanın boş satırı açılmaz, çağrılan "Üye");
    yedek tablosunda çağrılanın "Çağrılma tarihi" çağrı günüdür, ötekilerinde boş."""
    kurulum = ge_ortak.tam_kurulum()
    baskan, cagrilan = kurulum.yk_asillar[0], kurulum.yk_yedekler[0]
    uyelik_gecisleri.uyeligi_dusur(baskan, drop_kind="ISTIFA", end_date=date(2026, 11, 1))
    uyelik_gecisleri.yedek_cagir(
        cagrilan,
        organ="YK",
        promoted_on=date(2026, 11, 2),
        gerekce=uyum.Gerekce(metin="Uydurma: karar defteri ekranı F3'te."),
    )
    belge, uyarilar = gorev_evraki.e01_belgesi(kurulum.donem)
    assert gorev_evraki.UYARI_GOREV_BOS.format(gorev="Başkan") in uyarilar
    _, gorev, yedek, *_ = _tablolar(belge)
    assert [s[0] for s in gorev.satirlar] == [
        "Başkan yardımcısı",
        "Muhasip",
        "Sekreter",
        "Üye",
        "Üye",
    ]
    assert _ad(cagrilan) in {s[1] for s in gorev.satirlar}
    assert len(_imza_sahipleri(belge)) == 5
    cagrilar = {s[1]: s[2] for s in yedek.satirlar}
    assert cagrilar[_ad(cagrilan)] == "02.11.2026"
    assert [cagrilar[_ad(u)] for u in kurulum.yk_yedekler[1:]] == [""] * 4


def test_olaganustu_genel_kurulla_yenilenen_kurulda_o_gunun_tarihi() -> None:
    """E01 A bölümü: olağanüstü genel kurul (md. 13/8) yönetim kurulunun bir koltuğunu yenilediyse
    "Genel kurul (seçim) tarihi" o genel kurulun günüdür (dönemin başı değil)."""
    kurulum = ge_ortak.tam_kurulum()
    kurul = genel_kurul_servisi.genel_kurul_olustur(
        donem=kurulum.donem,
        kind=AssemblyKind.OLAGANUSTU,
        first_meeting_at=datetime(2026, 11, 5, 7, 0, tzinfo=UTC),
    )
    uyelik_gecisleri.uyeligi_dusur(
        kurulum.yk_asillar[4], drop_kind="OLAGANUSTU_GK_SECIMI", end_date=date(2026, 11, 5)
    )
    aday = o.yk_adayi(kurulum.donem, o.kisi(external_yk_terms=0), kurul)
    uyelikler.elect_membership(aday, start_date=date(2026, 11, 5))
    belge, _ = gorev_evraki.e01_belgesi(kurulum.donem)
    toplanti = {s[0]: s[1] for s in _tablolar(belge)[0].satirlar}
    assert toplanti[gorev_evraki.GENEL_KURUL_SECIM_TARIHI] == "05.11.2026"


# ============================================================ teslim alan müdürün adı


def _teslim_alan(belge: evrak.Belge) -> str:
    (mudur,) = [i for i in _imza_sahipleri(belge) if i.gorev == gorev_evraki.UNVAN_TESLIM_ALAN]
    return mudur.ad


def test_mudur_adi_kisi_kaydinin_ayrik_alanlarindan() -> None:
    """RYUE md. 17/2 (soyadı büyük harfle): iki sözcüklü soyadlı müdürün adı okul kartında tek
    alandır; okul müdürü kişi kaydı (`is_principal`, ad ve soyad ayrı) varsa imza bloğu ondan
    basılır, uyarı yok."""
    ge_ortak.okul_karti(principal_name="Ayşe Yılmaz Kaya")
    donem = o.donem()
    mudur = o.kisi(kind="IDARECI", is_parent=False, first_name="Ayşe", last_name="Yılmaz Kaya")
    assert mudur.is_principal
    belge, uyarilar = gorev_evraki.e03_belgesi(donem)
    assert _teslim_alan(belge) == "Ayşe YILMAZ KAYA"
    assert gorev_evraki.UYARI_MUDUR_SOYADI not in uyarilar


def test_mudur_kaydi_yoksa_son_sozcuk_soyadi_ve_uyari() -> None:
    """Müdür kişi kaydı yoksa (ya da kaydın adı okul kartındakiyle tutmuyorsa) son sözcük soyadı
    sayılır; üç ya da daha çok sözcükte bölme tahmindir: basım uyarısı. İki sözcükte uyarı yok."""
    ge_ortak.okul_karti(principal_name="Ayşe Yılmaz Kaya")
    donem = o.donem()
    belge, uyarilar = gorev_evraki.e03_belgesi(donem)
    assert _teslim_alan(belge) == "Ayşe Yılmaz KAYA"
    assert gorev_evraki.UYARI_MUDUR_SOYADI in uyarilar
    assert gorev_evraki.UYARI_MUDUR_SOYADI not in " ".join(evrak.metin_akisi(belge))
    # İşaret kartla çelişen kişide kalmışsa o ad basılmaz: kart değişti, kayıt eski müdürün.
    o.kisi(kind="IDARECI", is_parent=False, first_name="Ayşe", last_name="Yılmaz Kaya")
    ge_ortak.okul_karti()  # "Gülten Uydurmaca"
    belge, uyarilar = gorev_evraki.e03_belgesi(donem)
    assert _teslim_alan(belge) == "Gülten UYDURMACA"
    assert gorev_evraki.UYARI_MUDUR_SOYADI not in uyarilar


# ============================================================ biçim ve dönem


@pytest.mark.parametrize("kod", ["E01", "E02", "E03"])
def test_punto_alt_siniri(kod: str) -> None:
    """RYUE md. 7/1 (kullanıcı kararı 11.11.2026): yazı alanında 9 puntodan küçük metin yok; dipnot
    9, altlık 12; Word'de de."""
    kurulum = ge_ortak.tam_kurulum(uzun=True)
    belge, _ = gorev_evraki.KURUCULAR[kod](kurulum.donem)
    parcalar = pdf_yazi_boyutlari(evrak.pdf_ciz(belge))
    assert parcalar
    assert [(m, b) for _s, m, b in parcalar if b < cizici.EN_KUCUK_PUNTO] == []
    assert {b for _s, m, b in parcalar if m == evrak.KISISEL_VERI_DIPNOTU} == {
        float(cizici.DIPNOT_PUNTO)
    }
    assert {b for _s, m, b in parcalar if m.startswith("OAB Defteri ·")} == {
        float(cizici.ALTLIK_PUNTO)
    }
    d = cizici.ac(evrak.docx_ciz(belge))
    boyutlar = [
        r.font.size.pt
        for p in d.paragraphs
        for r in p.runs
        if r.text.strip() and r.font.size is not None
    ]
    assert boyutlar and min(boyutlar) >= cizici.EN_KUCUK_PUNTO


#: Kapanmış dönemin son günü: temsilcilerin günü (20.10.2026) ile bugün arasında, geçmişte.
SON_GUN = date(2026, 10, 31)


def test_kapanmis_donemde_ayni_icerik_yazilir_farkli_icerik_yazilmaz() -> None:
    """O2 beyaz listesi (tasarım §5.2.8): kapanmış dönemde yeni sürüm yalnız geçerli kaydın içeriğiyle
    yazılır; veri değişmişse 409 `donem_kapali`, kayıt yazılmaz."""
    kurulum = ge_ortak.tam_kurulum()
    ilk, _ = _uret("E03", kurulum.donem)
    # Bitiş günü geçmişte: olay günü dönemin son günüdür (`_olay_gunu`).
    OabTerm.objects.filter(pk=kurulum.donem.pk).update(status=TermStatus.KAPANDI, end_date=SON_GUN)
    ikinci, _ = _uret("E03", kurulum.donem)
    assert ikinci.content_sha256 == ilk.content_sha256 and ikinci.version == 2
    OabTerm.objects.filter(pk=kurulum.donem.pk).update(status=TermStatus.ACIK, end_date=None)
    kisiler.update_person(kurulum.yk_asillar[0].person, first_name="Yenad", ayni_kisi_degil=True)
    OabTerm.objects.filter(pk=kurulum.donem.pk).update(status=TermStatus.KAPANDI, end_date=SON_GUN)
    yanit = _post("E03", kurulum.donem)
    assert yanit.status_code == 409 and yanit.json()["code"] == "donem_kapali"
    assert GeneratedDocument.objects.filter(doc_type="E03").count() == 2


def _asil_uye_yururlugu_biter(donem: OabTerm, bitis: date) -> None:
    """Dönemin kural kopyasında (bellekte; kayıt değişmez) `yonetim_kurulu.asil_uye` yürürlüğü
    `bitis`te sona erer: o günden sonraki olay gününde değer yoktur."""
    for kayit in donem.rule_package.content["kurallar"]:
        if kayit["id"] == "yonetim_kurulu.asil_uye":
            kayit["yururluk"]["bitis"] = f"{bitis:%d.%m.%Y}"


def test_kapanmis_donemde_kurallar_donemin_son_gunuyle_okunur() -> None:
    """Kapanmış dönemde olay günü dönemin son günüdür, bugün değil (yeniden üretim aynı değeri
    okusun): asıl üye sayısının yürürlüğü son günde sürüyor, bugün bitmiş. Kapanmış dönemde katılan
    satırının paydası 5'tir; açık dönemde (olay günü bugün) değer yoktur, payda "………"."""
    kurulum = ge_ortak.tam_kurulum()
    assert timezone.localdate() > SON_GUN
    OabTerm.objects.filter(pk=kurulum.donem.pk).update(status=TermStatus.KAPANDI, end_date=SON_GUN)
    for durum, beklenen in (
        (TermStatus.KAPANDI, "4/5"),
        (TermStatus.ACIK, f"4/{gorev_evraki.BOS}"),
    ):
        if durum == TermStatus.ACIK:
            OabTerm.objects.filter(pk=kurulum.donem.pk).update(status=durum, end_date=None)
        donem = OabTerm.objects.select_related("rule_package").get(pk=kurulum.donem.pk)
        _asil_uye_yururlugu_biter(donem, SON_GUN)
        belge, _ = gorev_evraki.KURUCULAR["E01"](donem)
        toplanti = {s[0]: s[1] for s in _tablolar(belge)[0].satirlar}
        assert toplanti[gorev_evraki.KATILAN] == beklenen, durum
