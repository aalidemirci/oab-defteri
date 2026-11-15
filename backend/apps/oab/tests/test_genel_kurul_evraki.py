"""Genel kurul evrakı hattının iskeleti (`services.genel_kurul_evraki`; plan F2 §4.2, 8. adım).

Belgelerin içerikleri 9. ve 10. adımlardadır; burada hat deneme kurucularıyla sınanır
(`genel_kurul_evraki_ortak`): kodlar ve biçimler tasarım §9.5 kataloğuyla aynı; kurucusu olmayan kod
üretilmez; konu, kip ve toplantı denetimi (U14, U34); üreten roller (tasarım §9.6); Word ve PDF
saklanır, Excel ve web sayfası saklanmaz, kayıtlı içerikten çizilir (U18); basım `BASIM` izi yazar ve
`no-store`dur; veli adlı çıktı (U15, R9) tek istekte verilir, erişim günlüğü yazılamazsa verilmez,
günlüğe ad yazmaz, yeniden basılmaz; yazma ve parola kapıları ile kurucuların tutarlılık denetimi;
yeni okulun ilk genel kurulunda evrakın hazırlık dönemine yazılması. Veli adlı belgenin saklanmadığı
kapı testi `kurallar/test_evrak_kurallari.py::test_veli_adli_belge_saklanmaz`'dadır, dipnot ¹⁰'un
gerçek servis testi `apps/okul/tests/test_yetki_kapisi.py`'dedir.

Adlar UYDURMADIR.
"""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest
from django.db.models import Model
from django.http import Http404

from apps.oab.hatalar import DonemYazilamaz, EvrakIcerigiSaklanmaz
from apps.oab.kurallar import yukleyici
from apps.oab.kurallar.hatalar import KuralPaketiKullanilamaz
from apps.oab.models import (
    AssemblyCaller,
    AssemblyMeeting,
    DocumentFormat,
    DocumentStatus,
    DocumentVariant,
    GeneralAssembly,
    GeneratedDocument,
    TermStatus,
)
from apps.oab.services import evrak as evrak_servisi
from apps.oab.services import genel_kurul_evraki as gke
from apps.oab.tests import genel_kurul_evraki_ortak as ortak
from apps.oab.tests import genel_kurul_ortak as gko
from apps.oab.tests import uyelik_ortak as o
from apps.okul import erisim_gunlugu
from apps.okul.erisim_gunlugu import ErisimGunluguYazilamadi
from apps.okul.models import AccessLog, AccountRole, AuditAction, AuditTrail, SchoolConfig
from apps.okul.services import app_password
from shared import evrak
from shared.exceptions import RolYetkisiz

pytestmark = pytest.mark.django_db

TASARIM = "docs/tasarim/2026-10-31-genel-tasarim.md"


def _depo_dosyasi(goreli: str) -> str:
    """Depo kökündeki dosya (yerelde depo kökü, konteynerde `/repo`)."""
    for kok in (Path(__file__).resolve().parents[4], Path("/repo")):
        yol = kok / goreli
        if yol.is_file():
            return yol.read_text(encoding="utf-8")
    pytest.fail(f"{goreli} bulunamadı.")


_KATALOG_SATIRI = re.compile(r"^\| (E\d{2}) \|(.*)\|$", re.MULTILINE)
_BIRINCI = AssemblyMeeting.BIRINCI
_IKINCI = AssemblyMeeting.IKINCI


@pytest.fixture
def kurul(monkeypatch: pytest.MonkeyPatch) -> GeneralAssembly:
    ortak.kuruculari_kur(monkeypatch)
    return gko.ilanli_olagan()


@pytest.fixture
def yeni_okul_kurulu(monkeypatch: pytest.MonkeyPatch) -> GeneralAssembly:
    """Yeni açılan okulun ilk olağan genel kurulu: `term` boş, açılacak dönem hazırlıkta (S5 (i))."""
    ortak.kuruculari_kur(monkeypatch)
    gko.ders_yillari()
    gko.mevcut()
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(opened_on=date(2026, 9, 7))
    kurul_ = gko.planla()
    assert (kurul_.term_id, kurul_.called_by) == (None, AssemblyCaller.MUDUR_YENI_OKUL)
    assert kurul_.opens_term is not None and kurul_.opens_term.status == TermStatus.HAZIRLIK
    return kurul_


def _basimlar() -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(action=AuditAction.BASIM).order_by("seq"))


def _hicbir_sey_yazilmadi() -> None:
    """Reddedilen üretimden geriye evrak kaydı, `BASIM` satırı ve erişim günlüğü satırı kalmaz."""
    assert not GeneratedDocument.objects.exists()
    assert _basimlar() == [] and not AccessLog.objects.exists()


# ============================================================ katalog


def test_kodlar_bicimler_ve_adlar_katalogla_ayni() -> None:
    """Tasarım §9.5: F2'nin on iki belgesi (E04-E14, E64) ve biçim sütunları; her kodun adı, dosya adı
    kökü, üreteni ve okuma satırı vardır. Kip ve toplantı kümeleri plan F2 §7 U14 ve U34'tedir."""
    metin = _depo_dosyasi(TASARIM)
    bolum = metin[metin.index("\n### 9.5 ") : metin.index("\n### 9.6 ")]
    katalog = {kod: kalan.split("|") for kod, kalan in _KATALOG_SATIRI.findall(bolum)}
    f2 = {kod for kod, sutunlar in katalog.items() if sutunlar[-1].split()[0] == "F2"}
    assert set(gke.KODLAR) == f2
    harita = {"docx+pdf": {"DOCX", "PDF"}, "pdf": {"PDF"}, "html": {"HTML"}, "xlsx": {"XLSX"}}
    for kod in gke.KODLAR:
        beklenen: set[str] = set()
        for parca in katalog[kod][-2].split(","):
            beklenen |= harita[parca.strip()]
        assert set(gke.BICIMLER[kod]) == beklenen, kod
    for sozluk in (gke.BELGE_ADLARI, gke.DOSYA_ADI_KOKLERI, gke.URETEN_ROLLER, gke.OKUMA_SATIRLARI):
        assert set(sozluk) == set(gke.KODLAR)
    assert set(gke.ADLI_KODLAR) == set(gke.KIPLI_KODLAR) == {"E07", "E08"}
    assert gke.TOPLANTILI_KODLAR == {"E05", "E06", "E64"}
    assert set(gke.ADLI_BICIMLER["E08"]) == set(gke.BICIMLER["E08"])


def test_icerik_kurucusu_yokken_uretilmez() -> None:
    """İçerikler 9. ve 10. adımlardadır: kurucusu olmayan kod üretilmez; F1c'nin kodları bu yoldan
    üretilmez."""
    gko.acik_donem()
    kurul_ = gko.planla()
    assert gke.KURUCULAR == {} and gke.ADLI_KURUCULAR == {}
    with pytest.raises(ValueError, match=gke.KOD_GECERSIZ):
        gke.uret("E06", kurul_, toplanti=_BIRINCI)
    with pytest.raises(ValueError, match=gke.KOD_GECERSIZ):
        gke.adli_uret_ve_ver("E07", kurul_, bicim=DocumentFormat.PDF)
    with pytest.raises(ValueError, match=gke.KOD_GECERSIZ):
        gke.uret("E01", kurul_)
    assert not GeneratedDocument.objects.exists()


# ============================================================ kişisiz üretim


def test_uret_kayit_donem_kip_toplanti_ve_saklanan_dosyalar(kurul: GeneralAssembly) -> None:
    """Konu genel kurul, dönem `assembly.term`; toplantı satıra yazılır; yalnız Word ve PDF saklanır
    (E06'da yalnız PDF; web sayfası saklanmaz, U18)."""
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E06", kurul, toplanti=_BIRINCI)
    kayit = sonuc.kayit
    assert sonuc.uyarilar == ("Deneme uyarısı.",)
    assert (kayit.doc_type, kayit.subject_type, kayit.subject_id) == (
        "E06",
        "oab.GeneralAssembly",
        str(kurul.pk),
    )
    assert (kayit.variant, kayit.meeting, kayit.term_id) == ("", _BIRINCI, kurul.term_id)
    assert kayit.formats == ["HTML", "PDF"]
    assert kayit.personal_list is False and kayit.content_json
    assert [ek.mime for ek in kayit.ekler()] == ["application/pdf"]

    with o.rol_olarak(AccountRole.SEKRETER):
        e08 = gke.uret("E08", kurul, kip=DocumentVariant.KISISIZ).kayit
    assert e08.formats == ["DOCX", "PDF", "XLSX"] and e08.variant == DocumentVariant.KISISIZ
    assert sorted(ek.mime for ek in e08.ekler()) == sorted(
        evrak_servisi.BICIM_TURLERI[b] for b in (DocumentFormat.PDF, DocumentFormat.DOCX)
    )


def test_ayni_kodun_toplantilari_ve_kipleri_birbirinin_yerini_almaz(kurul: GeneralAssembly) -> None:
    """Plan F2 §7 U34: ikinci toplantının ilanı birincinin yerini almaz; aynı toplantının yeniden
    üretimi alır (sürüm kod ve konu başınadır)."""
    birinci = gke.uret("E06", kurul, toplanti=_BIRINCI).kayit
    ikinci = gke.uret("E06", kurul, toplanti=_IKINCI).kayit
    yeni = gke.uret("E06", kurul, toplanti=_BIRINCI).kayit
    durum = dict(GeneratedDocument.objects.values_list("pk", "status"))
    assert durum[birinci.pk] == DocumentStatus.YERINI_ALDI
    assert durum[ikinci.pk] == durum[yeni.pk] == DocumentStatus.GECERLI
    assert (birinci.version, ikinci.version, yeni.version) == (1, 2, 3)
    assert [k.pk for k in gke.evrak_listesi(kurul)] == [yeni.pk, ikinci.pk]


@pytest.mark.parametrize(
    ("kod", "kip", "toplanti"),
    [
        ("E06", "", ""),
        ("E06", "", "UCUNCU"),
        ("E06", DocumentVariant.KISISIZ, _BIRINCI),
        ("E07", "", ""),
        ("E07", DocumentVariant.ADLI, ""),
        ("E08", DocumentVariant.KISISIZ, _BIRINCI),
        ("E10", "", _BIRINCI),
    ],
)
def test_uret_kip_ve_toplanti_koda_uymali(
    kurul: GeneralAssembly, kod: str, kip: str, toplanti: str
) -> None:
    """E05, E06, E64 toplantı ister (U34); E07 ve E08 kişisiz kipi ister, adlı kip bu yoldan
    üretilmez (U14, U15); öteki belgeler kip ve toplantı almaz."""
    with pytest.raises(ValueError):
        gke.uret(kod, kurul, kip=kip, toplanti=toplanti)
    assert not GeneratedDocument.objects.exists()


def test_uret_konu_turu_koda_uymali(kurul: GeneralAssembly) -> None:
    """Genel kurul belgesinin konusu genel kuruldur; E14'ünkü birlik dönemi, E04'ünkü okul kartı."""
    donem = kurul.term
    assert donem is not None
    with pytest.raises(ValueError, match=gke.KONU_GECERSIZ):
        gke.uret("E10", donem)
    with pytest.raises(ValueError, match=gke.KONU_GECERSIZ):
        gke.uret("E14", kurul)
    e14 = gke.uret("E14", donem).kayit
    assert (e14.subject_type, e14.term_id, e14.formats) == (
        "oab.OabTerm",
        donem.pk,
        ["PDF", "XLSX"],
    )
    e04 = gke.uret("E04", SchoolConfig.load()).kayit
    assert (e04.subject_type, e04.term_id) == ("okul.SchoolConfig", None)


@pytest.mark.parametrize(
    ("kod", "rol"),
    [
        ("E06", AccountRole.MUHASIP),
        ("E06", AccountRole.BASKAN),
        ("E06", AccountRole.DENETLEME_KURULU),
        ("E06", AccountRole.MUDUR),
        ("E12", AccountRole.SEKRETER),
        ("E14", AccountRole.SEKRETER),
        ("E04", AccountRole.SEKRETER),
    ],
)
def test_uret_yalniz_ureten_roller(kurul: GeneralAssembly, kod: str, rol: AccountRole) -> None:
    """Tasarım §9.6 "Üreten" (plan F2 §4.1): genel kurul belgeleri sekreter ve program yöneticisi; E12,
    E14 ve E04 yalnız program yöneticisi. Öteki roller `RolYetkisiz`; kayıt yazılmaz."""
    konular: dict[str, Model] = {"E04": SchoolConfig.load()}
    if kurul.term is not None:
        konular["E14"] = kurul.term
    konu = konular.get(kod, kurul)
    toplanti = _BIRINCI if kod in gke.TOPLANTILI_KODLAR else ""
    with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
        gke.uret(kod, konu, toplanti=toplanti)
    assert not GeneratedDocument.objects.exists()


def test_uret_kurucu_baska_kodlu_belge_dondururse_kaydetmez(
    kurul: GeneralAssembly, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kurucunun döndürdüğü belgenin kodu istenen kod olmalı (9. ve 10. adımın kurucularına karşı
    koruma): değilse `KOD_GECERSIZ`, kayıt ve dosya yazılmaz."""
    monkeypatch.setitem(gke.KURUCULAR, "E06", ortak.kisisiz_kurucu("E05"))
    with pytest.raises(ValueError, match=gke.KOD_GECERSIZ):
        gke.uret("E06", kurul, toplanti=_BIRINCI)
    _hicbir_sey_yazilmadi()


# ============================================================ kapılar (D1, parola)


def _paketi_boz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(yukleyici._Onbellek, "durum", yukleyici.PaketDurumu(hatalar=("bozuk",)))


def _parolayi_kaldir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_password, "is_password_set", lambda: False)


@pytest.mark.parametrize(
    ("kapat", "hata"),
    [(_paketi_boz, KuralPaketiKullanilamaz), (_parolayi_kaldir, app_password.PasswordRequired)],
    ids=["kural_paketi_yuklenemez", "parola_kurulmamis"],
)
@pytest.mark.parametrize("yol", ["kisisiz", "adli"])
def test_kapilar_kapaliyken_uretilmez_ve_verilmez(
    kurul: GeneralAssembly,
    monkeypatch: pytest.MonkeyPatch,
    kapat: Callable[[pytest.MonkeyPatch], None],
    hata: type[Exception],
    yol: str,
) -> None:
    """Yazma kapısı (D1: kural paketi yüklenemezse yazma kapalı) ve parola kapısı: kişisiz üretim de
    veli adlı çıktı da (R9) reddedilir; evrak kaydı, `BASIM` satırı ve erişim günlüğü yazılmaz,
    dosya verilmez."""
    kapat(monkeypatch)
    with pytest.raises(hata):
        if yol == "kisisiz":
            gke.uret("E06", kurul, toplanti=_BIRINCI)
        else:
            gke.adli_uret_ve_ver("E08", kurul, bicim=DocumentFormat.XLSX)
    _hicbir_sey_yazilmadi()


# ============================================================ hazırlık dönemi (yeni okul)


def test_yeni_okul_kurulunun_evraki_hazirlik_donemine_yazilir(
    yeni_okul_kurulu: GeneralAssembly,
) -> None:
    """Plan F2 §4.2: yeni okulun ilk genel kurulunda evrakın dönemi açılacak dönemdir (`opens_term`,
    hazırlıkta); genel kurul belgeleri hazırlık dönemine `hazirlik_yazimi=True` ile yazılır. Kişisiz
    üretim de veli adlı çıktı da geçer ve kayıt hazırlık dönemine bağlanır."""
    hazirlik_pk = yeni_okul_kurulu.opens_term_id
    duyuru = gke.uret("E06", yeni_okul_kurulu, toplanti=_BIRINCI).kayit
    cetvel = gke.uret("E08", yeni_okul_kurulu, kip=DocumentVariant.KISISIZ).kayit
    adli = gke.adli_uret_ve_ver("E08", yeni_okul_kurulu, bicim=DocumentFormat.PDF).kayit
    assert [k.term_id for k in (duyuru, cetvel, adli)] == [hazirlik_pk] * 3
    assert adli.personal_list is True and AccessLog.objects.count() == 1


def test_hazirliktaki_donemin_yillik_is_takvimi_uretilmez(
    yeni_okul_kurulu: GeneralAssembly,
) -> None:
    """E14'ün konusu birlik dönemidir, genel kurul belgesi değildir: hazırlık dönemine yazma yalnız
    genel kurul belgelerinindir (`hazirlik_yazimi`; modül başlığı "Konu ve dönem"). Hazırlıktaki
    dönemin yıllık iş takvimi `DonemYazilamaz` ile reddedilir; kayıt yazılmaz."""
    hazirlik = yeni_okul_kurulu.opens_term
    assert hazirlik is not None
    with pytest.raises(DonemYazilamaz):
        gke.uret("E14", hazirlik)
    _hicbir_sey_yazilmadi()


# ============================================================ basım


def test_bas_saklanan_bicimi_depodan_saklanmayani_icerikten_verir(kurul: GeneralAssembly) -> None:
    """Plan F2 §7 U18: PDF dosya deposundan, web sayfası kayıtlı içerikten çizilir; ikisi de `BASIM`
    satırı yazar (kod ve verilen baytın sha256'sı), yanıt `no-store` ve ektir. Okuma rolü (Denetleme
    Kurulu, M3 "O") de basar."""
    kayit = gke.uret("E06", kurul, toplanti=_IKINCI).kayit
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        pdf = gke.bas(kayit, DocumentFormat.PDF)
        html = gke.bas(kayit, DocumentFormat.HTML)
    pdf_bayt = pdf.getvalue()
    html_bayt = html.getvalue()
    beklenen = evrak.web_html_ciz(evrak_servisi.yeniden_ciz(kayit)).encode("utf-8")
    assert html_bayt == beklenen and b"<!DOCTYPE html>" in html_bayt
    assert html["Content-Type"] == "text/html; charset=utf-8"
    for yanit in (pdf, html):
        assert yanit["Cache-Control"] == "no-store"
        assert "attachment" in yanit["Content-Disposition"]
    assert "Genel-Kurul-Duyurusu-%C4%B0kinci-Toplant%C4%B1_" in html["Content-Disposition"]
    satirlar = _basimlar()
    assert [s.values for s in satirlar] == [
        {"kod": [None, "E06"], "sha256": [None, hashlib.sha256(pdf_bayt).hexdigest()]},
        {"kod": [None, "E06"], "sha256": [None, hashlib.sha256(html_bayt).hexdigest()]},
    ]
    assert {(s.model, s.object_id, s.role) for s in satirlar} == {
        ("oab.GeneralAssembly", str(kurul.pk), "denetleme_kurulu")
    }


def test_bas_kayitta_olmayan_bicim_404(kurul: GeneralAssembly) -> None:
    kayit = gke.uret("E06", kurul, toplanti=_BIRINCI).kayit
    with pytest.raises(Http404):
        gke.bas(kayit, DocumentFormat.DOCX)
    assert _basimlar() == []


def test_bas_xlsx_kayitli_icerikten(kurul: GeneralAssembly) -> None:
    from shared import xlsx

    kayit = gke.uret("E08", kurul, kip=DocumentVariant.KISISIZ).kayit
    yanit = gke.bas(kayit, DocumentFormat.XLSX)
    bayt = yanit.getvalue()
    assert xlsx.metin_akisi(bayt) == evrak.metin_akisi(evrak_servisi.yeniden_ciz(kayit))
    assert yanit["Content-Type"] == gke.MIME_TURLERI[DocumentFormat.XLSX]


def test_bas_yazar_bagi_yoksa_403(kurul: GeneralAssembly) -> None:
    """Basan rol belgenin satırını okuyabilmeli (tasarım §4.4.2 "Okuma"); yazar bağlamı yoksa ret,
    iz yazılmaz."""
    from apps.okul.oturum import yazar_olarak

    kayit = gke.uret("E64", kurul, toplanti=_BIRINCI).kayit
    with yazar_olarak(None), pytest.raises(RolYetkisiz):
        gke.bas(kayit, DocumentFormat.PDF)
    assert _basimlar() == []


# ============================================================ veli adlı çıktı (U15, R9)


def test_adli_cikti_verilir_dosya_adi_ve_tur(kurul: GeneralAssembly) -> None:
    """Adlı E08 Excel'i de verilir (tasarım §9.5); dosya adı kişisiz kipinkinden ayrıdır, veli adı
    taşımaz; dönen bayt veli adlarını taşır (yalnız verilen dosyada)."""
    from shared import xlsx

    cikti = gke.adli_uret_ve_ver("E08", kurul, bicim=DocumentFormat.XLSX)
    assert cikti.mime == gke.MIME_TURLERI[DocumentFormat.XLSX]
    assert cikti.dosya_adi.startswith("Genel-Kurul-Katılım-Cetveli-Veli-Adlı_")
    assert cikti.dosya_adi.endswith(".xlsx")
    akis = xlsx.metin_akisi(cikti.icerik)
    assert all(veli in akis for veli, _ in ortak.VELILER)
    assert cikti.kayit.variant == DocumentVariant.ADLI and cikti.kayit.formats == ["XLSX"]


@pytest.mark.parametrize("bicim", [DocumentFormat.XLSX, DocumentFormat.HTML])
def test_adli_e07_bicim_denetimi(kurul: GeneralAssembly, bicim: str) -> None:
    with pytest.raises(ValueError, match=gke.BICIM_GECERSIZ):
        gke.adli_uret_ve_ver("E07", kurul, bicim=bicim)
    assert not GeneratedDocument.objects.exists()


def test_adli_cikti_erisim_gunlugu_yazilamazsa_verilmez(
    kurul: GeneralAssembly, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Aynı işlem: erişim günlüğü satırı yazılamazsa dosya verilmez; evrak kaydı ve `BASIM` satırı da
    geri alınır (tasarım §4.6.4 "satır yazılamazsa çıktı verilmez")."""

    def reddet(*_a: object, **_k: object) -> None:
        raise ErisimGunluguYazilamadi("Uydurma ret.")

    monkeypatch.setattr(erisim_gunlugu, "yaz", reddet)
    with pytest.raises(ErisimGunluguYazilamadi):
        gke.adli_uret_ve_ver("E07", kurul, bicim=DocumentFormat.PDF)
    assert not GeneratedDocument.objects.exists()
    assert _basimlar() == [] and not AccessLog.objects.exists()


def test_adli_kayit_yeniden_basilmaz(kurul: GeneralAssembly) -> None:
    """Veli adlı belgenin dosyası ve içeriği yoktur (R9): basım 404, yeniden çizim reddedilir.
    Saklanmayan biçimde (adlı E08'in Excel'i) 404'ü veren kaydın veli adı taşımasıdır: koruma
    olmasa basım kayıtlı içerikten çizmeye kalkardı. Basım reddinde `BASIM` satırı yazılmaz."""
    kayit = gke.adli_uret_ve_ver("E07", kurul, bicim=DocumentFormat.PDF).kayit
    excel = gke.adli_uret_ve_ver("E08", kurul, bicim=DocumentFormat.XLSX).kayit
    once = len(_basimlar())
    with pytest.raises(Http404):
        gke.bas(kayit, DocumentFormat.PDF)
    with pytest.raises(Http404):
        gke.bas(excel, DocumentFormat.XLSX)
    assert len(_basimlar()) == once
    for adli in (kayit, excel):
        with pytest.raises(EvrakIcerigiSaklanmaz):
            evrak_servisi.yeniden_ciz(adli)


@pytest.mark.parametrize("kod", ["E07", "E08"])
def test_adli_cikti_toplanti_almaz(kurul: GeneralAssembly, kod: str) -> None:
    """Plan F2 §7 U34: E07 ve E08 toplantı başına değildir; adlı kipe de toplantı verilmez."""
    with pytest.raises(ValueError, match=gke.TOPLANTI_GECERSIZ):
        gke.adli_uret_ve_ver(kod, kurul, bicim=DocumentFormat.PDF, toplanti=_BIRINCI)
    _hicbir_sey_yazilmadi()


@pytest.mark.parametrize(
    ("donen_kod", "satir_sayisi"), [("E08", 1), ("E07", -1)], ids=["baska_kod", "eksi_satir"]
)
def test_adli_kurucu_tutarsiz_icerik_dondururse_verilmez(
    kurul: GeneralAssembly, monkeypatch: pytest.MonkeyPatch, donen_kod: str, satir_sayisi: int
) -> None:
    """Veli adlı kurucunun içeriği tutarlı olmalı (9. adımın kurucularına karşı koruma): belgenin kodu
    istenen kod, satır sayısı eksi değil. Değilse `KOD_GECERSIZ`; kayıt, iz ve günlük yazılmaz, dosya
    verilmez."""
    gercek = ortak.adli_kurucu(donen_kod)

    def tutarsiz(kurul_: GeneralAssembly, toplanti: str) -> gke.AdliIcerik:
        icerik = gercek(kurul_, toplanti)
        return gke.AdliIcerik(belge=icerik.belge, satir_sayisi=satir_sayisi)

    monkeypatch.setitem(gke.ADLI_KURUCULAR, "E07", tutarsiz)
    with pytest.raises(ValueError, match=gke.KOD_GECERSIZ):
        gke.adli_uret_ve_ver("E07", kurul, bicim=DocumentFormat.PDF)
    _hicbir_sey_yazilmadi()


def test_adli_cikti_gunluge_ve_ize_ad_yazmaz(
    kurul: GeneralAssembly, caplog: pytest.LogCaptureFixture
) -> None:
    """KVKK: günlük kaydı yalnız kodu ve satır sayısını söyler; iz satırlarında ve erişim günlüğünde
    veli adı yoktur."""
    with caplog.at_level(logging.INFO):
        gke.adli_uret_ve_ver("E08", kurul, bicim=DocumentFormat.DOCX)
    metin = caplog.text + "".join(
        f"{s.values}{s.changed_fields}{s.object_id}" for s in AuditTrail.objects.all()
    )
    metin += "".join(f"{a.model}{a.object_id}{a.field}" for a in AccessLog.objects.all())
    assert "Veli adlı evrak verildi (E08, 2 satır)." in caplog.text
    for veli, _ in ortak.VELILER:
        for parca in veli.split():
            assert parca not in metin, parca


# ============================================================ sözlük


def test_genel_kurul_evraki_metinleri_sozlukte_yazilidir() -> None:
    """Kullanıcıya görünen her metin sözlüğe girer (sözlük §1 "Genel kurul evrakı (F2) — evrak
    hattı"): belge adları, dosya adı kökleri (kişisiz ve veli adlı kip, toplantı kapsamı), resmî yazının
    yan başlıkları, muhatap önerisi ve üretimin iletileri."""
    from shared.letterhead import MEM_IL, MEM_ILCE

    sozluk = _depo_dosyasi("docs/sozluk.md")
    metinler = [
        *gke.BELGE_ADLARI.values(),
        *gke.TOPLANTI_KAPSAMLARI.values(),
        evrak.SAYI_ETIKETI,
        evrak.KONU_ETIKETI,
        evrak.EK_ETIKETI,
        f"({MEM_ILCE})",
        f"({MEM_IL})",
        gke.KOD_GECERSIZ,
        gke.KONU_GECERSIZ,
        gke.KIP_GECERSIZ,
        gke.TOPLANTI_GECERSIZ,
        gke.BICIM_GECERSIZ,
    ]
    assert [m for m in metinler if f'**"{m}"**' not in sozluk] == []
    for kok in (*gke.DOSYA_ADI_KOKLERI.values(), *gke.ADLI_DOSYA_ADI_KOKLERI.values()):
        assert f"`{kok}_gg.aa.yyyy.pdf`" in sozluk, kok
    ornek = gke.dosya_adi("E06", date(2026, 11, 20), DocumentFormat.HTML, toplanti=_IKINCI)
    assert f"`{ornek}`" in sozluk
