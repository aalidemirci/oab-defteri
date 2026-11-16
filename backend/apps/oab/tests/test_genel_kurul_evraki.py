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
from datetime import date, timedelta
from pathlib import Path

import pytest
from django.db.models import Model
from django.http import Http404

from apps.oab.hatalar import DonemYazilamaz, EvrakIcerigiSaklanmaz
from apps.oab.kurallar import kural, yukleyici
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
    """İçerikler 9. ve 10. adımlardadır: 9. adımda E05-E08 ve E64'ün kurucuları (adlı kipte E07 ve
    E08) yazıldı; E04 ve E09-E14 10. adımdadır, kurucusu olmayan kod üretilmez; F1c'nin kodları bu
    yoldan üretilmez."""
    gko.acik_donem()
    kurul_ = gko.planla()
    assert set(gke.KURUCULAR) == {"E05", "E06", "E07", "E08", "E64"}
    assert set(gke.ADLI_KURUCULAR) == {"E07", "E08"}
    for kod in ("E09", "E10", "E11", "E13"):
        with pytest.raises(ValueError, match=gke.KOD_GECERSIZ):
            gke.uret(kod, kurul_)
    assert kurul_.term is not None
    with pytest.raises(ValueError, match=gke.KOD_GECERSIZ):
        gke.uret("E14", kurul_.term)
    with pytest.raises(ValueError, match=gke.KOD_GECERSIZ):
        gke.uret("E04", SchoolConfig.load())
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


# ============================================================ Genel kurul evrakı I (9. adım)


def test_cagrisiz_ve_toplantisiz_belge_uretilmez() -> None:
    """E05, E06 ve E07 genel kurul çağrılmadan üretilmez (imza ve üreten çağırana göredir); ikinci
    toplantının belgesi (E05 ve E06 ilanı, E64 tespiti; U34) birinci toplantıda yeter sayı
    sağlanamadıktan sonra üretilir; E64 toplantının katılımı girilmeden üretilmez. Ret hiçbir kayıt
    yazmaz."""
    gko.acik_donem()
    kurul = gko.planla()
    with o.rol_olarak(AccountRole.SEKRETER):
        for kod, kip, toplanti in (
            ("E05", "", _BIRINCI),
            ("E06", "", _BIRINCI),
            ("E07", DocumentVariant.KISISIZ, ""),
        ):
            with pytest.raises(ValueError, match=gke.CAGRI_YOK):
                gke.uret(kod, kurul, kip=kip, toplanti=toplanti)
    kurul = ortak.ilanli(gko.olagan_cagir(kurul))
    for kod in ("E05", "E06"):
        with pytest.raises(ValueError, match=gke.IKINCI_TOPLANTI_ACILMADI):
            gke.uret(kod, kurul, toplanti=_IKINCI)
    for toplanti in (_BIRINCI, _IKINCI):
        with pytest.raises(ValueError, match=gke.TOPLANTI_YAPILMADI):
            gke.uret("E64", kurul, toplanti=toplanti)
    kurul = ortak.birinci_toplantida_yapilmis(kurul)
    for kod in ("E05", "E06"):
        with pytest.raises(ValueError, match=gke.IKINCI_TOPLANTI_ACILMADI):
            gke.uret(kod, kurul, toplanti=_IKINCI)
    with pytest.raises(ValueError, match=gke.TOPLANTI_YAPILMADI):
        gke.uret("E64", kurul, toplanti=_IKINCI)
    assert not GeneratedDocument.objects.exists()


def test_e64_birinci_toplantinin_dagilimi_ikinci_toplantidan_sonra_bos_basilir() -> None:
    """İkinci toplantının sayıları birinci toplantının türe göre dağılımının ve gözlemci sayısının
    üzerine yazılır (`genel_kurul.ikinci_toplanti`; plan F2 4. adım notu). En dar seçim (yeni model
    alanı açılmadı): birinci toplantının E64'ü ikinci toplantıdan önce üretildiyse dağılımı taşır ve
    ikinci toplantının E64'ünden sonra da geçerli kalır (U34); ikinci toplantıdan sonra üretilirse
    katılan sayısı birinci toplantınınkidir (`first_attendee_count`), dağılım ve gözlemci "………" ve
    basım uyarısıdır. Önceki sürüm silinmez (yerini alır, içeriği kalır)."""
    kurul = ortak.ilanli(ortak.kurulum(gke.KOL_YK))
    kurul = ortak.birinci_toplantida_yetersiz(kurul)
    with o.rol_olarak(AccountRole.SEKRETER):
        once = gke.uret("E64", kurul, toplanti=_BIRINCI)
    belge = evrak_servisi.yeniden_ciz(once.kayit)
    dagilim = next(
        b
        for b in belge.bloklar
        if isinstance(b, evrak.Tablo) and b.basliklar == gke.DAGILIM_BASLIKLARI
    )
    assert dagilim.satirlar[:2] == (("Veli ve kursiyer", "7"), ("Öğretmen", "3"))
    assert once.uyarilar == ()

    kurul = ortak.ikinci_toplantida_yapilmis(kurul)
    ikinci = gke.uret("E64", kurul, toplanti=_IKINCI).kayit
    sonra = gke.uret("E64", kurul, toplanti=_BIRINCI)
    assert gke.UYARI_BIRINCI_DAGILIM_YOK in sonra.uyarilar
    belge = evrak_servisi.yeniden_ciz(sonra.kayit)
    satirlar = {
        s[0]: s[1]
        for b in belge.bloklar
        if isinstance(b, evrak.Tablo) and b.basliklar[0] == "Konu"
        for s in b.satirlar
    }
    assert satirlar[gke.SATIR_KATILAN] == "10"
    assert satirlar[gke.SATIR_GOZLEMCI] == gke.BOS_YER
    dagilim = next(
        b
        for b in belge.bloklar
        if isinstance(b, evrak.Tablo) and b.basliklar == gke.DAGILIM_BASLIKLARI
    )
    assert {s[1] for s in dagilim.satirlar} == {gke.BOS_YER}
    durumlar = dict(GeneratedDocument.objects.values_list("pk", "status"))
    assert durumlar[once.kayit.pk] == DocumentStatus.YERINI_ALDI
    assert durumlar[ikinci.pk] == durumlar[sonra.kayit.pk] == DocumentStatus.GECERLI
    assert GeneratedDocument.objects.get(pk=once.kayit.pk).content_json


#: İlan süresi uyarısının kalıbı (herhangi bir gün sayısıyla; `UYARI_ILAN_SURESI`).
_ILAN_SURESI_KALIBI = re.compile(
    re.escape(gke.UYARI_ILAN_SURESI)
    .replace(re.escape("{kalan}"), "-?[0-9]+")
    .replace(re.escape("{en_az}"), "[0-9]+")
)


def test_e05_ilan_suresinden_az_gun_kala_basim_uyarisi(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tasarım §9.6 E05 "14 gün kala basımda uyarı" (md. 9/3; `genel_kurul.ilan_en_az_gun`, kodda sabit
    yok): toplantıya ilan süresinden az gün kaldıysa (toplantı günü dahil) üretimin yanıtında uyarı,
    kalan gün sayısıyla; süre tamsa (sınır günü) ya da toplantı geçtiyse HİÇBİR ilan süresi uyarısı
    yok. Uyarı belgeye basılmaz."""
    from django.utils import timezone

    kurul = ortak.kurulum(gke.KOL_YK)
    en_az = int(kural("genel_kurul.ilan_en_az_gun"))
    birinci = gko.BIRINCI_GUN
    for kalan, uyari in ((en_az - 1, True), (en_az, False), (0, True), (-1, False)):
        gun = birinci - timedelta(days=kalan)
        monkeypatch.setattr(timezone, "localdate", lambda *_a, _g=gun, **_k: _g)
        with o.rol_olarak(AccountRole.SEKRETER):
            sonuc = gke.uret("E05", kurul, toplanti=_BIRINCI)
        bulunan = [u for u in sonuc.uyarilar if _ILAN_SURESI_KALIBI.fullmatch(u)]
        beklenen = [gke.UYARI_ILAN_SURESI.format(kalan=kalan, en_az=en_az)] if uyari else []
        assert bulunan == beklenen, kalan
        akis = " ".join(evrak.metin_akisi(evrak_servisi.yeniden_ciz(sonuc.kayit)))
        assert not _ILAN_SURESI_KALIBI.search(akis)


def test_e05_ikinci_toplanti_ilaninin_kaniti_ayri_ilandan() -> None:
    """İkinci toplantı ilk ilanda yoksa ayrı ilan edilir (`genel_kurul.ikinci_toplanti_ilani`); ikinci
    toplantının E05'i duyuru kanıtını bu ilandan alır, giriş cümlesi ikinci toplantınındır ve ikinci
    toplantının kuralı (md. 9/2) yeniden basılmaz. Ayrı ilan yoksa kanıt birinci ilanınkidir, uyarıyla."""
    from apps.oab.services import genel_kurul as gk

    kurul = ortak.ilanli(ortak.kurulum(gke.KOL_YK), ikinci_gun=False)
    kurul = ortak.birinci_toplantida_yetersiz(kurul)
    ikinci_ilan = date(2026, 10, 22)
    gk.ikinci_toplanti_ilani(
        kurul,
        second_meeting_at=gko.an(gko.IKINCI_GUN + timedelta(days=2)),
        kanallar=gko.kanallar(ikinci_ilan),
    )
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E05", kurul, toplanti=_IKINCI)
    belge = evrak_servisi.yeniden_ciz(sonuc.kayit)
    akis = " ".join(evrak.metin_akisi(belge))
    assert gke.IKINCI_DAVET_GIRISI.format(tur="olağan") in akis
    assert "07.11.2026 10:00" in akis and "22.10.2026" in akis and "05.10.2026" not in akis
    assert gke.SATIR_BIRINCI not in akis
    assert gke.IKINCI_TOPLANTI_CUMLESI.split("{")[0] not in akis
    assert gke.UYARI_IKINCI_ILAN_YOK not in sonuc.uyarilar


def test_yeni_okulda_yapilamadi_imzasi_acilisi_yapan_mudur() -> None:
    """Kullanıcı kararı S5 (ii): yeni açılan okulun ilk genel kurulunda (yönetim kurulu yok) E64'ün
    "sağlanamadı" imzası ve E08'in parafının "yapılamadıysa" kolu "Okul Müdürü (açılışı yapan)"dır,
    "Görüldü" bloğu yoktur; E05 müdürün yazısıdır (okul antedi), E06 ve E07 "Okul Müdürlüğü". Toplantıdan
    önce basılan cetvelde sonuç belli değildir: parafın iki kolu koşuluyla basılır. E64 kişisizdir
    (KE-21): imzada yalnız unvan."""
    kurul = ortak.ilanli(ortak.kurulum(gke.KOL_MUDUR_9_1))
    assert kurul.term_id is None
    with o.rol_olarak(AccountRole.SEKRETER):
        cetvel = gke.uret("E08", kurul, kip=DocumentVariant.KISISIZ).kayit
    kurul = ortak.birinci_toplantida_yetersiz(kurul)
    with o.rol_olarak(AccountRole.SEKRETER):
        tespit = gke.uret("E64", kurul, toplanti=_BIRINCI).kayit
    for kayit, beklenen in (
        (
            cetvel,
            {
                ("", gke.PARAF_YAPILDIYSA.format(unvan=gke.UNVAN_DIVAN_BASKANI)),
                ("", gke.PARAF_YAPILDIYSA.format(unvan=gke.UNVAN_KATIP)),
                ("", gke.PARAF_YAPILAMADIYSA.format(unvan=gke.UNVAN_ACILISI_YAPAN)),
            },
        ),
        (tespit, {("", gke.UNVAN_ACILISI_YAPAN)}),
    ):
        belge = evrak_servisi.yeniden_ciz(kayit)
        sahipler = {
            (s.ad, s.gorev) for b in belge.bloklar if isinstance(b, evrak.Imza) for s in b.sahipler
        }
        assert sahipler == beklenen, kayit.doc_type
        assert "örüldü" not in " ".join(evrak.metin_akisi(belge))
    assert {k.term_id for k in (cetvel, tespit)} == {kurul.opens_term_id}


def test_e05_olaganustu_cagri_nedeni_basvuru_ve_gundeme_baglilik() -> None:
    """Tasarım §9.6 E05: olağanüstüde çağıran ve neden basılı, gündem nedene bağlı (md. 9/6 "gündeme
    bağlılık ilkesi geçerlidir"); üyelerin başvurusunda başvuran ve üye sayısı (U12); başvuru yazısının
    evrak kaydı bağlı değilse "………" ve uyarı. Yeter sayı ilanla dondurulur: ilandan önce "………"."""
    kurul = ortak.kurulum(gke.KOL_YUZDE_10)
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E05", kurul, toplanti=_BIRINCI)
    belge = evrak_servisi.yeniden_ciz(sonuc.kayit)
    bilgi = {
        s[0]: s[1]
        for b in belge.bloklar
        if isinstance(b, evrak.Tablo) and b.basliklar[0] == "Konu"
        for s in b.satirlar
    }
    assert bilgi[gke.SATIR_TUR] == "Olağanüstü genel kurul"
    assert bilgi[gke.SATIR_CAGRI_NEDENI] == gko.OLAGANUSTU_NEDEN
    assert bilgi[gke.SATIR_BASVURU] == "10 / 100"
    assert bilgi[gke.SATIR_EVRAK] == gke.BOS_YER
    assert bilgi[gke.SATIR_YETER_SAYI] == gke.BOS_YER
    assert gke.SATIR_KARAR not in bilgi
    for uyari in (gke.UYARI_EVRAK_KAYDI_YOK, gke.UYARI_YETER_SAYI_YOK, gke.UYARI_ILAN_YOK):
        assert uyari in sonuc.uyarilar
    akis = " ".join(evrak.metin_akisi(belge))
    assert gke.GUNDEME_BAGLILIK in akis
    gundem = [m.title for m in gko.OLAGANUSTU_GUNDEM]
    assert all(baslik in akis for baslik in gundem)


def _imzalar(belge: evrak.Belge) -> list[tuple[str, str]]:
    return [(s.ad, s.gorev) for b in belge.bloklar if isinstance(b, evrak.Imza) for s in b.sahipler]


def _bilgi_satirlari(belge: evrak.Belge) -> dict[str, str]:
    return {
        s[0]: s[1]
        for b in belge.bloklar
        if isinstance(b, evrak.Tablo) and b.basliklar[0] == "Konu"
        for s in b.satirlar
    }


def _dagilim(belge: evrak.Belge) -> tuple[tuple[str, ...], ...]:
    return next(
        b.satirlar
        for b in belge.bloklar
        if isinstance(b, evrak.Tablo) and b.basliklar == gke.DAGILIM_BASLIKLARI
    )


def test_e05_imzacisi_cagri_gunundeki_gorevlidir() -> None:
    """E05 geçmiş bir olayın (çağrının) belgesidir: imzacı bugünkü görevli değil, çağrı günü görevde
    olandır (`selectors.gundeki_asillar`; en geç birinci toplantıdan bir gün önce). Olağanüstü genel
    kurulun seçimi eski yönetim kurulunu toplantı günü düşürür (U27); seçimden sonra yeniden üretilen
    E05 çağrıyı imzalayan eski başkanı basar, "görev boş" uyarısı yoktur."""
    from apps.oab import selectors

    kurul = ortak.ilanli(ortak.kurulum(gke.KOL_BASKAN_13_8))
    donem = kurul.term
    assert donem is not None
    (baskan,) = [u for u in selectors.gorevdeki_asillar(donem, "YK") if u.role == "BASKAN"]
    eski_ad = evrak.ad_soyad(str(baskan.person.first_name), str(baskan.person.last_name))
    kurul = ortak.birinci_toplantida_yapilmis(kurul)
    gko.secim(kurul, "SECIM_YK", [gko.aday(kurul) for _ in range(5)])
    assert baskan.pk not in {u.pk for u in selectors.gorevdeki_asillar(donem, "YK")}
    with o.rol_olarak(AccountRole.BASKAN):
        sonuc = gke.uret("E05", kurul, toplanti=_BIRINCI)
    belge = evrak_servisi.yeniden_ciz(sonuc.kayit)
    assert _imzalar(belge) == [
        (eski_ad, gke.UNVAN_BIRLIK_BASKANI),
        (ortak.MUDUR_IMZASI, gke.UNVAN_GORULDU_E05),
    ]
    assert not [u for u in sonuc.uyarilar if u.endswith("görevi boş.")]


def test_e05_yonetim_kurulu_karari_bagliyken_basilir() -> None:
    """Çağrının dayanak satırı dolu kolda: yönetim kurulunun çağrı kararı "gg.aa.yyyy · N" (S1 (a);
    defter sıra no'su girilmemişse "………"); bağlıyken eksik uyarısı yok, evrak kaydı satırı yok."""
    from apps.oab.models import DecisionKind, MeetingKind
    from apps.oab.services import kurullar

    # Yönetim kurulunun kararı (karar bağı servisi F3'tedir; bağ testin kurgusu, ORM).
    kurul = ortak.ilanli(ortak.kurulum(gke.KOL_YK))
    assert kurul.term is not None
    toplanti = kurullar.toplanti_olustur(donem=kurul.term, organ="YK", kind=MeetingKind.AYLIK)
    karar = kurullar.karar_taslagi_olustur(
        toplanti, kind=DecisionKind.YEDEK_CAGIRMA, decision_date=date(2026, 9, 28)
    )
    kurul.call_decision = karar
    kurul.save(update_fields=["call_decision"])
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E05", kurul, toplanti=_BIRINCI)
    bilgi = _bilgi_satirlari(evrak_servisi.yeniden_ciz(sonuc.kayit))
    assert bilgi[gke.SATIR_KARAR] == gke.KARAR_DEGERI.format(tarih="28.09.2026", no=gke.BOS_YER)
    assert gke.UYARI_KARAR_YOK not in sonuc.uyarilar
    assert gke.SATIR_EVRAK not in bilgi


def test_e05_denetleme_kurulu_raporunun_gunu_basilir() -> None:
    """Denetleme Kurulunun çağrısında (md. 14/5) E05 bağlı raporun gününü basar."""
    dk_kurulu = ortak.kurulum(gke.KOL_DK_14_5)
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        sonuc = gke.uret("E05", dk_kurulu, toplanti=_BIRINCI)
    assert _bilgi_satirlari(evrak_servisi.yeniden_ciz(sonuc.kayit))[gke.SATIR_DK_RAPORU] == (
        "30.09.2026"
    )


def test_e05_basvuru_yazisinin_evrak_kaydi_basilir() -> None:
    """Üyelerin başvurusunun gelen evrak kaydı bağlanınca (U12) E05'in evrak kaydı satırı "yyyy/N"dir
    ve eksik uyarısı yoktur."""
    from apps.oab.services import gelen_giden_evrak
    from apps.oab.services import genel_kurul as gk

    kurul = ortak.kurulum(gke.KOL_YUZDE_10)
    if gelen_giden_evrak.evrak_defteri() is None:
        gelen_giden_evrak.evrak_defteri_olustur()
    yazi = gelen_giden_evrak.evrak_kaydet(
        direction="GELEN",
        tarih=date(2026, 9, 25),
        counterparty="Uydurma başvuran üyeler",
        subject="Olağanüstü genel kurul başvurusu",
    ).kayit
    kurul = gk.cagri_yazisini_bagla(kurul, kayit=yazi).kurul
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E05", kurul, toplanti=_BIRINCI)
    bilgi = _bilgi_satirlari(evrak_servisi.yeniden_ciz(sonuc.kayit))
    assert bilgi[gke.SATIR_EVRAK] == gke.EVRAK_DEGERI.format(yil=yazi.year, no=yazi.record_no)
    assert gke.UYARI_EVRAK_KAYDI_YOK not in sonuc.uyarilar


def test_e64_ikinci_toplantinin_icerigi() -> None:
    """İkinci toplantının E64'ü (md. 9/2 "çoğunluk aranmaz"): alt satır ve sonuç çoğunluk aranmaz,
    katılan ikinci toplantınınki (`second_attendee_count`), dağılım ve gözlemci ikinci toplantınınki,
    ikinci toplantının günü; ikinci toplantı satırı yok; Divan Başkanı + Kâtip, yalnız unvan, "Görüldü"
    yok (KE-21)."""
    kurul = ortak.ilanli(ortak.kurulum(gke.KOL_YK))
    kurul = ortak.ikinci_toplantida_yapilmis(ortak.birinci_toplantida_yetersiz(kurul))
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E64", kurul, toplanti=_IKINCI)
    belge = evrak_servisi.yeniden_ciz(sonuc.kayit)
    assert belge.bloklar[0] == evrak.Baslik(
        gke.BELGE_ADLARI["E64"], alt=f"Olağan genel kurul{gke.ALT_AYRAC}{gke.ALT_COGUNLUK_ARANMAZ}"
    )
    bilgi = _bilgi_satirlari(belge)
    assert bilgi[gke.SATIR_TOPLANTI] == "İkinci toplantı"
    assert bilgi[gke.SATIR_GUN_YER] == f"05.11.2026 10:00 · {ortak.YER}"
    assert bilgi[gke.SATIR_KATILAN] == "20"
    assert bilgi[gke.SATIR_GOZLEMCI] == "2"
    assert bilgi[gke.SATIR_SONUC] == gke.SONUC_COGUNLUK_ARANMAZ
    assert gke.SATIR_IKINCI not in bilgi and gke.SATIR_KATILAN_DUZELTILMIS not in bilgi
    assert _dagilim(belge) == (
        ("Veli ve kursiyer", "15"),
        ("Öğretmen", "4"),
        ("İdareci", "0"),
        ("Hayırsever", "1"),
        ("Diğer", "0"),
    )
    assert _imzalar(belge) == [("", gke.UNVAN_DIVAN_BASKANI), ("", gke.UNVAN_KATIP)]
    assert "örüldü" not in " ".join(evrak.metin_akisi(belge))
    assert sonuc.uyarilar == ()


@pytest.mark.parametrize("yon", ["yukari", "asagi"])
def test_e64_katilim_duzeltmesinden_sonra_tespit_toplantidaki_sayidir(yon: str) -> None:
    """Katılım düzeltmesi genel kurulun durumunu değiştirmez (tasarım §5.2.3): yeter sayının öbür
    yanına geçen düzeltmeden sonra da E64 toplantıdaki tespiti belgeler — katılan toplantıda girilen
    sayıdır (`genel_kurul.ilk_girilen_deger`), sonuç onunla tutarlıdır; düzeltilmiş sayı ayrı satırda
    ve basım uyarısıyla. Düzeltme yoksa satır ve uyarı yok."""
    from apps.oab.services import genel_kurul as gk

    if yon == "yukari":
        kurul = gk.birinci_toplanti(gko.ilanli_olagan(), katilim=gko.katilim(10)).kurul
        ilk, yeni, sonuc_metni = 10, 70, gke.SONUC_SAGLANAMADI
    else:
        kurul = gko.yapilmis_olagan()
        ilk, yeni, sonuc_metni = 70, 60, gke.SONUC_SAGLANDI
    with o.rol_olarak(AccountRole.SEKRETER):
        once = gke.uret("E64", kurul, toplanti=_BIRINCI)
    assert gke.UYARI_KATILIM_DUZELTILDI not in once.uyarilar
    assert gke.SATIR_KATILAN_DUZELTILMIS not in _bilgi_satirlari(
        evrak_servisi.yeniden_ciz(once.kayit)
    )
    gk.katilim_duzelt(
        kurul,
        toplanti=_BIRINCI,
        degerler={"first_attendee_count": yeni},
        justification="Uydurma: cetvel yeniden sayıldı.",
        gerekce=gko.GEREKCE,
    )
    kurul = GeneralAssembly.objects.get(pk=kurul.pk)
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E64", kurul, toplanti=_BIRINCI)
    bilgi = _bilgi_satirlari(evrak_servisi.yeniden_ciz(sonuc.kayit))
    assert bilgi[gke.SATIR_KATILAN] == str(ilk)
    assert bilgi[gke.SATIR_KATILAN_DUZELTILMIS] == str(yeni)
    assert bilgi[gke.SATIR_SONUC] == sonuc_metni
    assert gke.UYARI_KATILIM_DUZELTILDI in sonuc.uyarilar


def test_veli_adi_ad_soyad_bicimindedir() -> None:
    """Adlı E07 ve E08'de veli adı personelinki gibi "Ad SOYAD"dır (F1c `gorev_evraki._ad`): veli
    listesi adı tek alanda tutar (T5), son sözcük soyadı sayılır; üç ya da daha çok sözcüklü adda bu
    bölme tahmindir ve basım uyarısı verilir (`gorev_evraki._mudur_adi`'nin kalıbı)."""
    kurul = ortak.ilanli(ortak.kurulum(gke.KOL_YK))
    gko.veli_aktar([("ayşe nur ırmakçı", "5-A"), ("İSMAİL ÖRNEKOĞLU", "5-B")], ad="ikinci.xlsx")
    for kurucu in (gke.e07_adli_belgesi, gke.e08_adli_belgesi):
        icerik = kurucu(kurul, "")
        akis = " ".join(evrak.metin_akisi(icerik.belge))
        assert "Ayşe Nur IRMAKÇI" in akis and "İsmail ÖRNEKOĞLU" in akis, kurucu.__name__
        assert "ayşe nur" not in akis and "İSMAİL ÖRNEKOĞLU" not in akis
        assert gke.UYARI_VELI_SOYADI in icerik.uyarilar
    gko.veli_aktar([("Kemal Uydurmacı", "5-A")], ad="ucuncu.xlsx")
    assert gke.UYARI_VELI_SOYADI not in gke.e08_adli_belgesi(kurul, "").uyarilar


def test_veli_listesi_yokken_davet_ve_cetvel_bos_basilir() -> None:
    """Veli listesi aktarılmamışsa (F1c boş alan kalıbı) davetin sınıf adet tablosu "………", cetvelin
    veli bölümü sınıfsız ve `BOS_VELI_SATIRI` boş satırlıdır; ikisinde de basım uyarısı."""
    kurul = gko.ilanli_olagan()
    with o.rol_olarak(AccountRole.SEKRETER):
        davet = gke.uret("E07", kurul, kip=DocumentVariant.KISISIZ)
        cetvel = gke.uret("E08", kurul, kip=DocumentVariant.KISISIZ)
    assert gke.UYARI_VELI_LISTESI_YOK in davet.uyarilar
    assert gke.UYARI_VELI_LISTESI_YOK in cetvel.uyarilar
    bloklar = evrak_servisi.yeniden_ciz(davet.kayit).bloklar
    adet = bloklar[bloklar.index(evrak.AltBaslik(gke.E07_ADET_BOLUMU)) + 1]
    assert isinstance(adet, evrak.Tablo)
    assert adet.satirlar == ((gke.BOS_YER, gke.BOS_YER, "", ""),)
    bloklar = evrak_servisi.yeniden_ciz(cetvel.kayit).bloklar
    veli = bloklar[bloklar.index(evrak.AltBaslik(gke.VELI_BOLUMU_SINIFSIZ)) + 1]
    assert isinstance(veli, evrak.Tablo)
    assert len(veli.satirlar) == gke.BOS_VELI_SATIRI
    assert all(s[1:] == ("", "", "") for s in veli.satirlar)
    assert _adli_davette_veli_listesi_yok(kurul)


def _adli_davette_veli_listesi_yok(kurul: GeneralAssembly) -> bool:
    """Adlı E07'nin veli listesi yok uyarısı (sınıf bölümü "………")."""
    icerik = gke.e07_adli_belgesi(kurul, "")
    return (
        gke.UYARI_VELI_LISTESI_YOK in icerik.uyarilar
        and evrak.AltBaslik(gke.SINIF_BOLUMU.format(sinif=gke.BOS_YER)) in icerik.belge.bloklar
    )


def test_e64_dagilimi_ve_gozlemcisi_girilmemisse_bos_basilir() -> None:
    """Toplantının türe göre dağılımı ve gözlemci sayısı girilmemişse E64'te "………" ve basım uyarısı."""
    from apps.oab.services import genel_kurul as gk

    kurul = gk.birinci_toplanti(gko.ilanli_olagan(), katilim=gko.katilim(10)).kurul
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E64", kurul, toplanti=_BIRINCI)
    belge = evrak_servisi.yeniden_ciz(sonuc.kayit)
    assert gke.UYARI_DAGILIM_YOK in sonuc.uyarilar and gke.UYARI_GOZLEMCI_YOK in sonuc.uyarilar
    assert {s[1] for s in _dagilim(belge)} == {gke.BOS_YER}
    assert _bilgi_satirlari(belge)[gke.SATIR_GOZLEMCI] == gke.BOS_YER


def test_e05_eksik_alanlar_bos_ve_uyarili() -> None:
    """E05'in boş alan kalıbı: yer girilmemiş, ikinci toplantının günü girilmemiş ve bir kanalın kanıt
    günü eksikse yerleri "………" ve basım uyarısı; ilan günü girilmiş kanallardandır."""
    from apps.oab.services import genel_kurul as gk

    kurul = gko.cagrilmis_olagan()
    kurul = gk.ilan_et(
        kurul,
        kanallar=gk.IlanKanallari(
            distributed_written_on=gko.ILAN_GUNU,
            posted_board_on=gko.ILAN_GUNU,
            published_web_on=None,
        ),
    ).kurul
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E05", kurul, toplanti=_BIRINCI)
    belge = evrak_servisi.yeniden_ciz(sonuc.kayit)
    bilgi = _bilgi_satirlari(belge)
    assert bilgi[gke.SATIR_YER] == gke.BOS_YER and gke.UYARI_YER_YOK in sonuc.uyarilar
    assert bilgi[gke.SATIR_IKINCI] == gke.BOS_YER and gke.UYARI_IKINCI_TARIH_YOK in sonuc.uyarilar
    assert gke.UYARI_KANIT_EKSIK in sonuc.uyarilar
    kanit = next(
        b
        for b in belge.bloklar
        if isinstance(b, evrak.Tablo) and b.basliklar == gke.KANIT_BASLIKLARI
    )
    assert kanit.satirlar[2] == (gke.KANAL_INTERNET, gke.BOS_YER, "")
    assert kanit.satirlar[3] == (gke.KANIT_ILAN_GUNU, "05.10.2026", "")


def test_e05_ikinci_toplantinin_ayri_ilani_yoksa_uyari() -> None:
    """İkinci toplantının günü ilk ilanda verildiyse ayrı ilanı yoktur: ikinci toplantının E05'inde
    duyuru kanıtı birinci ilanınkidir, basım uyarısıyla."""
    ikinci = ortak.birinci_toplantida_yetersiz(ortak.ilanli(ortak.kurulum(gke.KOL_DK_14_5)))
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        sonuc = gke.uret("E05", ikinci, toplanti=_IKINCI)
    assert gke.UYARI_IKINCI_ILAN_YOK in sonuc.uyarilar


def test_bozuk_cagri_nedeni_ve_bos_gundem_bos_basilir() -> None:
    """Çağrı nedeni program dışından bozulmuşsa (çözülemeyen şifreli değer) ve çağrının gündemi
    okunamıyorsa (program dışından yazım taklidi) E05'te "………" ve basım uyarısı."""
    from django.db import connection

    kurul = ortak.kurulum(gke.KOL_YUZDE_10)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE oab_generalassembly SET call_reason = %s WHERE id = %s",
            ["UYDURMA HAM", kurul.pk],
        )
        cursor.execute(
            "UPDATE oab_agendaitem SET added_by_vote = %s WHERE assembly_id = %s",
            [True, kurul.pk],
        )
    kurul = GeneralAssembly.objects.get(pk=kurul.pk)
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret("E05", kurul, toplanti=_BIRINCI)
    belge = evrak_servisi.yeniden_ciz(sonuc.kayit)
    assert _bilgi_satirlari(belge)[gke.SATIR_CAGRI_NEDENI] == gke.BOS_YER
    assert gke.UYARI_NEDEN_OKUNAMADI in sonuc.uyarilar
    gundem = next(
        b
        for b in belge.bloklar
        if isinstance(b, evrak.Tablo) and b.basliklar == gke.GUNDEM_BASLIKLARI
    )
    assert gundem.satirlar == ((gke.BOS_YER, gke.BOS_YER),)
    assert gke.UYARI_GUNDEM_YOK in sonuc.uyarilar


@pytest.mark.parametrize("kod", ["E05", "E06", "E07", "E08"])
def test_iptal_edilmis_genel_kurulun_belgesi_uyariyla_basilir(kod: str) -> None:
    """İptal edilmiş genel kurulun belgesi iptalden önceki kayıtla basılır; basım uyarısıyla."""
    from apps.oab.services import genel_kurul as gk

    kurul = ortak.ilanli(ortak.kurulum(gke.KOL_YK))
    kurul = gk.iptal_et(kurul, cancel_reason="Uydurma gerekçe: toplantı ertelendi.")
    kip = DocumentVariant.KISISIZ if kod in gke.KIPLI_KODLAR else ""
    toplanti = _BIRINCI if kod in gke.TOPLANTILI_KODLAR else ""
    with o.rol_olarak(AccountRole.SEKRETER):
        sonuc = gke.uret(kod, kurul, kip=kip, toplanti=toplanti)
    assert gke.UYARI_IPTAL in sonuc.uyarilar
    assert gke.UYARI_IPTAL not in " ".join(
        evrak.metin_akisi(evrak_servisi.yeniden_ciz(sonuc.kayit))
    )


# ============================================================ sözlük


def _genel_kurul_evraki_i_metinleri() -> list[str]:
    """9. adımın kullanıcıya görünen sabit metinleri (yer tutucular sözlükteki biçimiyle). Onaylı veli
    aydınlatma metninin cümleleri ön yüz sözlüğü testindedir (`test_on_yuz_sozlugu`)."""
    g = gke
    return [
        *g.TUR_BASLIKLARI.values(),
        *g.TOPLANTI_ADLARI.values(),
        g.CAGIRAN_YK_OLAGAN,
        g.CAGIRAN_YK_OLAGANUSTU,
        *g.CAGIRAN_METINLERI.values(),
        *dict.fromkeys(g.KURUM_ADLARI.values()),
        g.DAVET_GIRISI.format(tur="<tür>"),
        g.IKINCI_DAVET_GIRISI.format(tur="<tür>"),
        g.ILAN_CUMLESI.format(gun="N"),
        g.IKINCI_TOPLANTI_CUMLESI.format(gun="N"),
        g.GUNDEME_BAGLILIK,
        g.SATIR_TUR,
        g.SATIR_CAGIRAN,
        g.SATIR_CAGRI_NEDENI,
        g.SATIR_KARAR,
        g.KARAR_DEGERI.format(tarih="gg.aa.yyyy", no="N"),
        g.SATIR_BASVURU,
        g.BASVURU_DEGERI.format(basvuran="N", uye="N"),
        g.SATIR_DK_RAPORU,
        g.SATIR_EVRAK,
        g.EVRAK_DEGERI.format(yil="yyyy", no="N"),
        g.SATIR_YER,
        g.SATIR_BIRINCI,
        g.SATIR_IKINCI,
        g.SATIR_YETER_SAYI,
        g.YETER_SAYI_DEGERI.format(sayi="N", taban="N", carpan="N"),
        g.GUNDEM_BOLUMU,
        *g.GUNDEM_BASLIKLARI,
        g.KANIT_BOLUMU,
        *g.KANIT_BASLIKLARI,
        g.KANAL_ELDEN,
        g.KANAL_PANO,
        g.KANAL_INTERNET,
        g.KANIT_ILAN_GUNU,
        g.SAYIN_VELI,
        g.E07_AYDINLATMA_BASLIGI,
        g.E07_TAM_METIN_YERI,
        g.E07_ADET_BOLUMU,
        *g.ADET_BASLIKLARI,
        g.TOPLAM,
        g.E07_CIZELGE_ALT,
        g.E07_CIZELGE_GIRISI,
        g.SINIF_BOLUMU.format(sinif="<sınıf>"),
        *g.CIZELGE_BASLIKLARI,
        g.E08_GIRIS,
        g.VELI_BOLUMU.format(sinif="<sınıf>"),
        g.VELI_BOLUMU_SINIFSIZ,
        *g.VELI_BASLIKLARI,
        g.PERSONEL_BOLUMU,
        *g.PERSONEL_BASLIKLARI,
        *g.PERSONEL_GOREVLERI.values(),
        g.DIGER_BOLUMU,
        *g.DIGER_BASLIKLARI,
        g.GOZLEMCI_BOLUMU,
        *g.GOZLEMCI_BASLIKLARI,
        g.E64_GIRIS.format(tur="<tür>"),
        g.ALT_SAGLANDI,
        g.ALT_SAGLANAMADI,
        g.ALT_COGUNLUK_ARANMAZ,
        g.SATIR_TOPLANTI,
        g.SATIR_GUN_YER,
        g.GUN_YER_DEGERI.format(an="gg.aa.yyyy SS:dd", yer="<yer>"),
        g.SATIR_MEVCUT,
        g.SATIR_KATILAN,
        g.SATIR_GOZLEMCI,
        g.SATIR_SONUC,
        g.SONUC_SAGLANDI,
        g.SONUC_SAGLANAMADI,
        g.SONUC_COGUNLUK_ARANMAZ,
        g.DAGILIM_BOLUMU,
        *g.DAGILIM_BASLIKLARI,
        g.UNVAN_YK_ADINA_BASKAN,
        g.UNVAN_BIRLIK_BASKANI,
        g.UNVAN_SEKRETER,
        g.UNVAN_OKUL_MUDURU,
        g.UNVAN_GORULDU_E05,
        g.UNVAN_GORULDU,
        g.UNVAN_ACILISI_YAPAN,
        g.UNVAN_DIVAN_BASKANI,
        g.UNVAN_KATIP,
        g.UNVAN_DK_BASKANI,
        g.UNVAN_DK_UYESI,
        g.UNVAN_REHBER,
        g.PARAF_YAPILDIYSA.format(unvan="<unvan>"),
        g.PARAF_YAPILAMADIYSA.format(unvan="<unvan>"),
        g.SATIR_KATILAN_DUZELTILMIS,
        g.CAGRI_YOK,
        g.IKINCI_TOPLANTI_ACILMADI,
        g.TOPLANTI_YAPILMADI,
        g.UYARI_YER_YOK,
        g.UYARI_IKINCI_TARIH_YOK,
        g.UYARI_YETER_SAYI_YOK,
        g.UYARI_KARAR_YOK,
        g.UYARI_EVRAK_KAYDI_YOK,
        g.UYARI_NEDEN_OKUNAMADI,
        g.UYARI_GUNDEM_YOK,
        g.UYARI_ILAN_YOK,
        g.UYARI_KANIT_EKSIK,
        g.UYARI_IKINCI_ILAN_YOK,
        g.UYARI_ILAN_SURESI.format(kalan="N", en_az="N"),
        g.UYARI_YUZDE_10,
        g.UYARI_IPTAL,
        g.UYARI_VELI_LISTESI_YOK,
        g.UYARI_VERI_SORUMLUSU_YOK,
        g.UYARI_DAGILIM_YOK,
        g.UYARI_GOZLEMCI_YOK,
        g.UYARI_BIRINCI_DAGILIM_YOK,
        g.UYARI_KATILIM_DUZELTILDI,
        g.UYARI_VELI_SOYADI,
    ]


def test_genel_kurul_evraki_i_metinleri_sozlukte_yazilidir() -> None:
    """9. adımın belge başlıkları, bölümleri, satırları, unvanları, iletileri ve basım uyarıları
    sözlükte (sözlük §1 "Genel kurul evrakı (F2)"); katılımın türleri (`AttendanceKind`) de."""
    from apps.oab.models import AttendanceKind

    sozluk = _depo_dosyasi("docs/sozluk.md")
    metinler = [*_genel_kurul_evraki_i_metinleri(), *(str(t.label) for t in AttendanceKind)]
    assert [m for m in dict.fromkeys(metinler) if f'**"{m}"**' not in sozluk] == []


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
