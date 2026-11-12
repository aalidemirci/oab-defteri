"""Üretilen evrak kaydı ve evrak hattının depoyla bağı (tasarım §5.2.8, §9.1-2; plan F1c 9. adım).

Sabitlenenler: (1) satır silinmez, içeriği değişmez, durumu yalnız `GECERLI` → `YERINI_ALDI`; (2)
yeniden üretim yeni sürüm satırıdır, önceki satır yerini bırakır (iz: `DURUM` + `OLUSTUR`); (3)
kapanmış dönemde de yazılır (`KAPALI_DONEM` etiketi), iptal edilmiş dönemde yazılmaz; kural paketi
dönemin kopyasıdır; kapanmış dönemde içerik değişmez (yeni sürüm geçerli satırın özetiyle aynıdır)
ve veli adı taşıyan belge yazılmaz; hazırlıktaki döneme yalnız hazırlık bayrağıyla yazılır; (4) yeniden basım kayıtlı JSON'dan çizilir ve aynı özeti verir, kayıt bozuksa
basılmaz; (5) veli adı taşıyan belgenin içeriği ve dosyası saklanmaz (R9); (6) üretilen evrak dosya
deposunun sahibidir: PDF ve DOCX alır, kayıt türü adı Türkçedir, indirme yanıtı bellektendir; (7) Word
ve PDF çıktıları kayıtlı içerikten de aynı metin akışını verir. Adlar UYDURMADIR.
"""

from __future__ import annotations

import io
import re
from datetime import date
from typing import Any

import pytest
from django.db import IntegrityError, transaction
from pypdf import PdfReader

from apps.oab.hatalar import (
    DonemKapali,
    DonemYazilamaz,
    EvrakIcerigiSaklanmaz,
    EvrakIcerigiTutmuyor,
)
from apps.oab.models import (
    DocumentStatus,
    EvrakKaydiGecersiz,
    GeneratedDocument,
    OabTerm,
    TermStatus,
)
from apps.oab.services import donemler
from apps.oab.services import evrak as evrak_servisi
from apps.okul import denetim_izi
from apps.okul.models import AuditAction, AuditLabel, AuditTrail, ImmutableRecord, SchoolYear
from apps.okul.oturum import yazar
from apps.okul.services import dosya_deposu
from apps.okul.services.geri_yukleme_ekleri import tur_adi
from shared import docx as cizici
from shared import dosya_sifreleme as ds
from shared import evrak

pytestmark = pytest.mark.django_db

GUN = date(2026, 10, 10)
UYDURMA_AD, UYDURMA_SOYAD = "Uydurnur", "Örnekkaya"


def _donem() -> OabTerm:
    yil = SchoolYear.objects.create(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), is_active=True
    )
    return donemler.create_term(name="2026-2027 birlik dönemi", school_year=yil, start_date=GUN)


def _belge(kod: str = "E01", ek: str = "") -> evrak.Belge:
    """Gerçek uzunlukta değil, hattın bütün blok türlerini taşıyan uydurma karar taslağı."""
    return evrak.Belge(
        kod=kod,
        antet=evrak.birlik_anteti(okul_adi="Örnek Ortaokulu", ilce="Örnek İlçe"),
        bloklar=(
            evrak.Baslik("yönetim kurulu görev bölümü", alt=evrak.TASLAK_IBARESI),
            evrak.AltBaslik("A. Toplantı"),
            evrak.Paragraf(f"Kurul toplandı.{ek}"),
            evrak.Tablo(
                basliklar=("Sıra", "Ad ve soyadı", "Görev", "Koltuk", "Dönem"),
                satirlar=(("1", evrak.ad_soyad(UYDURMA_AD, UYDURMA_SOYAD), "Başkan", "Veli", "1"),),
                oranlar=(1, 5, 3, 2, 2),
            ),
            evrak.KonumCumlesi(evrak.KDT),
            evrak.Imza(sahipler=(evrak.ImzaSahibi(evrak.ad_soyad("ayşe", "örnek"), "Başkan"),)),
            evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
        ),
    )


def _kaydet(donem: OabTerm, **alanlar: Any) -> GeneratedDocument:
    varsayilan: dict[str, Any] = {"konu": donem, "bicimler": ("DOCX", "PDF"), "donem": donem}
    return evrak_servisi.kaydet(alanlar.pop("belge", _belge()), **{**varsayilan, **alanlar})


def _akis(yanit: Any) -> Any:
    return yanit.streaming_content


def _kapat(donem: OabTerm) -> OabTerm:
    """Sentetik kapanış (gerçek kapanış F4)."""
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.KAPANDI, end_date=date(2027, 10, 1)
    )
    return OabTerm.objects.get(pk=donem.pk)


# ============================================================ model


def test_kayit_silinmez_icerigi_degismez_durumu_geri_donmez() -> None:
    kayit = _kaydet(_donem())
    with pytest.raises(ImmutableRecord):
        kayit.delete()
    with pytest.raises(ImmutableRecord):
        GeneratedDocument.objects.filter(pk=kayit.pk).delete()
    with pytest.raises(ImmutableRecord):
        GeneratedDocument._base_manager.all().delete()
    kayit.content_sha256 = "0" * 64
    with pytest.raises(ImmutableRecord):
        kayit.save()
    with pytest.raises(ImmutableRecord):
        kayit.save(update_fields=["content_sha256"])
    kayit = GeneratedDocument.objects.get(pk=kayit.pk)
    kayit.status = DocumentStatus.YERINI_ALDI
    kayit.save(update_fields=["status"])
    kayit.status = DocumentStatus.GECERLI
    with pytest.raises(EvrakKaydiGecersiz, match="bu yöne"):
        kayit.save(update_fields=["status"])


@pytest.mark.parametrize(
    ("alanlar", "ileti"),
    [
        ({"doc_type": "E1"}, "kodu"),
        ({"doc_type": "DUMAN"}, "kodu"),
        ({"formats": []}, "biçim"),
        ({"formats": ["PDF", "DOCX"]}, "biçim"),
        ({"formats": ["ODT"]}, "biçim"),
        ({"status": DocumentStatus.YERINI_ALDI}, "geçerli durumda"),
    ],
)
def test_yeni_kayit_model_kuralina_uyar(alanlar: dict[str, Any], ileti: str) -> None:
    temel: dict[str, Any] = {
        "doc_type": "E01",
        "subject_type": "oab.OabTerm",
        "subject_id": "1",
        "version": 1,
        "formats": ["PDF"],
        "content_sha256": "0" * 64,
        "content_json": "{}",
        "generated_at": "2026-11-10T09:00:00Z",
    }
    with pytest.raises(EvrakKaydiGecersiz, match=ileti):
        GeneratedDocument(**{**temel, **alanlar}).save()


@pytest.mark.parametrize(
    ("alanlar", "kisit"),
    [
        ({"personal_list": True}, "ck_generateddocument_icerik"),
        ({"content_json": ""}, "ck_generateddocument_icerik"),
        ({"content_sha256": "0" * 63}, "ck_generateddocument_sha256"),
        ({"version": 0}, "ck_generateddocument_version"),
        ({"subject_id": ""}, "ck_generateddocument_konu"),
    ],
)
def test_veritabani_kisitlari(alanlar: dict[str, Any], kisit: str) -> None:
    temel: dict[str, Any] = {
        "doc_type": "E01",
        "subject_type": "oab.OabTerm",
        "subject_id": "1",
        "version": 1,
        "formats": ["PDF"],
        "content_sha256": "0" * 64,
        "content_json": "{}",
        "generated_at": "2026-11-10T09:00:00Z",
    }
    with transaction.atomic(), pytest.raises(IntegrityError, match=kisit):
        GeneratedDocument.objects.create(**{**temel, **alanlar})


def test_ayni_konuda_tek_gecerli_kayit_ve_surum_tekil() -> None:
    kayit = _kaydet(_donem())
    temel: dict[str, Any] = {
        "doc_type": kayit.doc_type,
        "subject_type": kayit.subject_type,
        "subject_id": kayit.subject_id,
        "formats": ["PDF"],
        "content_sha256": "0" * 64,
        "content_json": "{}",
        "generated_at": "2026-11-10T09:00:00Z",
    }
    with transaction.atomic(), pytest.raises(IntegrityError, match=r"subject_id$"):
        GeneratedDocument.objects.create(version=2, **temel)
    with (
        transaction.atomic(),
        pytest.raises(IntegrityError, match=r"subject_id, oab_generateddocument.version$"),
    ):
        # Model yeni satırı yalnız geçerli açar; sürüm kısıtı ham yazımla sınanır.
        GeneratedDocument.objects.bulk_create(
            [GeneratedDocument(version=1, status=DocumentStatus.YERINI_ALDI, **temel)]
        )


# ============================================================ kayıt servisi


def test_kayit_icerigi_ozeti_ve_baglari() -> None:
    donem = _donem()
    belge = _belge()
    kayit = _kaydet(donem, belge=belge, satir_sayisi=1)
    assert (kayit.doc_type, kayit.version, kayit.status) == ("E01", 1, DocumentStatus.GECERLI)
    assert (kayit.subject_type, kayit.subject_id) == ("oab.OabTerm", str(donem.pk))
    assert kayit.formats == ["DOCX", "PDF"] and kayit.row_count == 1
    assert kayit.rule_package_id == donem.rule_package_id and kayit.term_id == donem.pk
    assert kayit.content_json == evrak.kanonik_json(belge)
    assert kayit.content_sha256 == evrak.icerik_ozeti(belge)
    assert kayit.generated_by_id == kayit.created_by_id is not None
    (satir,) = AuditTrail.objects.filter(model="oab.GeneratedDocument")
    assert satir.action == AuditAction.OLUSTUR and str(satir.term_id) == str(donem.pk)
    # Değerler kişisizdir: içerik JSON'u şifrelidir ve değere girmez.
    assert "content_json" not in satir.values and satir.values["doc_type"] == [None, "E01"]
    assert UYDURMA_SOYAD.upper() not in str(satir.values)
    assert denetim_izi.kaydi_dogrula(GeneratedDocument, kayit.pk) is True


def test_yeniden_uretim_yeni_surumdur_onceki_yerini_birakir() -> None:
    donem = _donem()
    ilk = _kaydet(donem)
    ikinci = _kaydet(donem, belge=_belge(ek=" İkinci okuma."))
    ilk.refresh_from_db()
    assert (ilk.version, ilk.status) == (1, DocumentStatus.YERINI_ALDI)
    assert (ikinci.version, ikinci.status) == (2, DocumentStatus.GECERLI)
    assert ilk.content_sha256 != ikinci.content_sha256
    eylemler = list(
        AuditTrail.objects.filter(model="oab.GeneratedDocument")
        .order_by("seq")
        .values_list("action", "object_id")
    )
    assert eylemler == [
        (AuditAction.OLUSTUR, str(ilk.pk)),
        (AuditAction.DURUM, str(ilk.pk)),
        (AuditAction.OLUSTUR, str(ikinci.pk)),
    ]
    # Başka evrak kodu ayrı zincirdir.
    assert _kaydet(donem, belge=_belge(kod="E03")).version == 1
    assert denetim_izi.zinciri_dogrula() == []


def test_kapanmis_donemde_yazilir_ve_etiketlenir_iptal_doneme_yazilmaz() -> None:
    donem = _donem()
    _kaydet(donem)
    kapali = _kapat(donem)
    kayit = _kaydet(kapali)
    assert kayit.version == 2
    etiketler = set(
        AuditTrail.objects.filter(model="oab.GeneratedDocument", seq__gt=1).values_list(
            "label", flat=True
        )
    )
    assert AuditLabel.KAPALI_DONEM in etiketler
    OabTerm.objects.filter(pk=donem.pk).update(status=TermStatus.IPTAL, end_date=None)
    with pytest.raises(DonemYazilamaz):
        _kaydet(OabTerm.objects.get(pk=donem.pk))


def _iz_sayisi() -> int:
    return AuditTrail.objects.filter(model="oab.GeneratedDocument").count()


def test_kapanmis_donemde_icerik_degismez_yeniden_basim_ayni_ozeti_verir() -> None:
    """Kapanmış dönemde yeni sürüm yalnız geçerli satırın özetiyle aynı içerikle yazılır (tasarım
    §5.2.8: "aynı content_sha256'yı vermelidir"; O2: metin kilitli); farklı içerik `DonemKapali`
    alır, satır, durum ve iz değişmez. Önceki geçerli satırı olmayan ilk kayıt kabul edilir (E39
    arşiv paketi kapanmış dönemden üretilir, §7.8)."""
    donem = _donem()
    ilk = _kaydet(donem)
    kapali = _kapat(donem)
    iz_once = _iz_sayisi()
    with pytest.raises(DonemKapali):
        _kaydet(kapali, belge=_belge(ek=" Sonradan eklenen cümle."))
    ilk.refresh_from_db()
    assert ilk.status == DocumentStatus.GECERLI
    assert GeneratedDocument.objects.count() == 1 and _iz_sayisi() == iz_once
    # Aynı içerik yeniden basımdır: yeni sürüm, `KAPALI_DONEM` etiketli.
    assert _kaydet(kapali).content_sha256 == ilk.content_sha256
    # Önceki satırı olmayan evrakın ilk kaydı kapanmış dönemde de yazılır.
    assert _kaydet(kapali, belge=_belge(kod="E39")).version == 1


def test_veli_adi_tasiyan_belge_kapanmis_doneme_yazilmaz() -> None:
    """Veli adı taşıyan belge beyaz listede değildir (tasarım §5 O2 "veli adı taşıyan belge hariç",
    §5.2.8): kapanmış dönemde aynı içerikle de yazılmaz; önceki satır geçerli kalır, iz düşmez."""
    donem = _donem()
    belge = _belge(kod="E07")
    ilk = _kaydet(donem, belge=belge, kisi_listesi=True, satir_sayisi=24)
    kapali = _kapat(donem)
    iz_once = _iz_sayisi()
    with pytest.raises(DonemKapali):
        _kaydet(kapali, belge=belge, kisi_listesi=True, satir_sayisi=24)
    ilk.refresh_from_db()
    assert ilk.status == DocumentStatus.GECERLI
    assert GeneratedDocument.objects.count() == 1 and _iz_sayisi() == iz_once
    # Önceki satırı olmayan veli adlı belge de kapanmış döneme yazılmaz.
    with pytest.raises(DonemKapali):
        _kaydet(kapali, belge=_belge(kod="E08"), kisi_listesi=True)
    assert GeneratedDocument.objects.count() == 1


def test_hazirlik_donemine_yalniz_hazirlik_bayragiyla_yazilir() -> None:
    """Hazırlıktaki döneme yalnız genel kurul hazırlığının evrakı yazılır (tasarım §5 O2; plan 9. adım
    notu): bayraksız kayıt `DonemYazilamaz` alır ve satır yazılmaz; bayrakla geçerli ilk sürüm
    yazılır, izi `KAPALI_DONEM` etiketi taşımaz."""
    donem = _donem()
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.HAZIRLIK, start_date=None, end_date=None, program_start_date=None
    )
    hazirlik = OabTerm.objects.get(pk=donem.pk)
    with pytest.raises(DonemYazilamaz):
        _kaydet(hazirlik)
    assert not GeneratedDocument.objects.exists()
    kayit = evrak_servisi.kaydet(
        _belge(), konu=hazirlik, bicimler=("PDF",), donem=hazirlik, hazirlik_yazimi=True
    )
    assert (kayit.status, kayit.version) == (DocumentStatus.GECERLI, 1)
    (satir,) = AuditTrail.objects.filter(model="oab.GeneratedDocument")
    assert satir.label == ""


def test_kod_ve_konu_ve_bicim_denetlenir() -> None:
    donem = _donem()
    with pytest.raises(EvrakKaydiGecersiz, match="kodu"):
        evrak_servisi.kaydet(evrak.ornek_belge(), konu=donem, bicimler=("PDF",))
    with pytest.raises(EvrakKaydiGecersiz, match="kaydedilmiş"):
        evrak_servisi.kaydet(_belge(), konu=SchoolYear(name="x"), bicimler=("PDF",))
    with pytest.raises(EvrakKaydiGecersiz, match="biçim"):
        evrak_servisi.kaydet(_belge(), konu=donem, bicimler=())
    with pytest.raises(EvrakKaydiGecersiz, match="biçim"):
        evrak_servisi.kaydet(_belge(), konu=donem, bicimler=("ODT",))
    assert not GeneratedDocument.objects.exists()


# ============================================================ yeniden basım


def test_yeniden_basim_kayitli_jsondan_ayni_ozeti_verir() -> None:
    """Kapanmış dönemin belgesi program, şablon ya da ana veri değişse de aynı özeti verir (§6.2-6):
    çizim yalnız kayıtlı JSON'dan yapılır; iki çizici kayıtlı içerikten de aynı metin akışını verir."""
    donem = _donem()
    belge = _belge()
    kayit = _kaydet(donem, belge=belge)
    _kapat(donem)
    yeniden = evrak_servisi.yeniden_ciz(kayit)
    assert yeniden == belge
    assert evrak.icerik_ozeti(yeniden) == kayit.content_sha256
    beklenen = re.sub(r"\s+", "", "".join(evrak.metin_akisi(yeniden)))
    word = cizici.govde_metin_akisi(cizici.ac(evrak.docx_ciz(yeniden)))
    pdf = "\n".join(
        s.extract_text() or "" for s in PdfReader(io.BytesIO(evrak.pdf_ciz(yeniden))).pages
    )
    pdf = re.sub(r"OAB Defteri · \S+ · Sayfa \d+\s*/\s*\d+", "", pdf)
    assert re.sub(r"\s+", "", "".join(word)) == beklenen == re.sub(r"\s+", "", pdf)


@pytest.mark.parametrize(
    "bozma",
    [
        lambda metin: metin.replace('"kod":"E01"', '"kod":"E02"'),
        lambda metin: metin.replace('{"antet"', '{ "antet"'),
        lambda metin: metin[:-1],
    ],
    ids=["icerik_degisti", "kanonik_degil", "json_bozuk"],
)
def test_bozulmus_kayit_yeniden_basilmaz(bozma: Any) -> None:
    """Program dışından değiştirilmiş içerik basılmaz: özet tutmaz ya da kanonik çözüm reddeder.
    İçerik ve özet birlikte değiştirilirse biçimce geçerli içerik çözülür ama kaydın içerik MAC'i
    tutmaz (değişiklik denetim izinde görünür; `kaydi_dogrula`)."""
    kayit = _kaydet(_donem())
    yeni = bozma(kayit.content_json)
    GeneratedDocument.objects.filter(pk=kayit.pk).update(content_json=yeni)
    with pytest.raises(EvrakIcerigiTutmuyor):
        evrak_servisi.yeniden_ciz(kayit)
    # Özet de bozulmuş içeriğe uydurulsa kanonik denetim yine reddeder (ikinci ve üçüncü kol).
    GeneratedDocument.objects.filter(pk=kayit.pk).update(content_sha256=evrak.metin_ozeti(yeni))
    if '"kod":"E02"' in yeni:
        assert evrak_servisi.yeniden_ciz(kayit).kod == "E02"
        assert denetim_izi.kaydi_dogrula(GeneratedDocument, kayit.pk) is False
    else:
        with pytest.raises(EvrakIcerigiTutmuyor):
            evrak_servisi.yeniden_ciz(kayit)


def test_veli_adi_tasiyan_belgenin_icerigi_ve_dosyasi_saklanmaz() -> None:
    """R9: içerik JSON'u boş, özet ve satır sayısı kalır; yeniden basılmaz; depoya ek yazılmaz."""
    donem = _donem()
    belge = _belge(kod="E07")
    kayit = _kaydet(donem, belge=belge, kisi_listesi=True, satir_sayisi=24)
    assert (kayit.content_json, kayit.personal_list, kayit.row_count) == ("", True, 24)
    assert kayit.content_sha256 == evrak.icerik_ozeti(belge)
    with pytest.raises(EvrakIcerigiSaklanmaz):
        evrak_servisi.yeniden_ciz(kayit)
    with pytest.raises(dosya_deposu.KisiListesiSaklanmaz):
        evrak_servisi.dosya_ekle(kayit, evrak.pdf_ciz(belge), bicim="PDF", dosya_adi="liste.pdf")
    # Bayrak unutulsa da sahibin işareti okunur.
    with pytest.raises(dosya_deposu.KisiListesiSaklanmaz):
        dosya_deposu.yaz(
            evrak.pdf_ciz(belge),
            original_name="liste.pdf",
            sensitivity="NORMAL",
            owner=kayit,
            yazar=yazar(),
            kisi_listesi=False,
        )
    assert kayit.ekler().count() == 0


# ============================================================ dosya deposu bağı


def test_uretilen_evrak_depoya_pdf_ve_docx_olarak_yazilir_ve_okunur() -> None:
    """İlk ek sahibi üretilen evraktır (plan F1b-3, F1c 9. adım): PDF ve DOCX kabul edilir, kayıt
    türü adı Türkçedir, ek bellekten verilir; kaydında olmayan biçim ve yerini almış kayıt reddedilir."""
    donem = _donem()
    belge = _belge()
    kayit = _kaydet(donem, belge=belge)
    pdf, docx = evrak.pdf_ciz(belge), evrak.docx_ciz(belge)
    pdf_eki = evrak_servisi.dosya_ekle(kayit, pdf, bicim="PDF", dosya_adi="Gorev-Bolumu.pdf")
    docx_eki = evrak_servisi.dosya_ekle(kayit, docx, bicim="DOCX", dosya_adi="Gorev-Bolumu.docx")
    assert (pdf_eki.mime, docx_eki.mime) == (ds.PDF.mime, ds.DOCX.mime)
    assert list(kayit.ekler()) == [pdf_eki, docx_eki]
    assert dosya_deposu.oku(docx_eki) == docx
    assert tur_adi(pdf_eki.owner_type) == "üretilen evrak"
    assert str(GeneratedDocument._meta.verbose_name) == "üretilen evrak"

    yanit = dosya_deposu.indirme_yaniti(pdf_eki, dosya_adi="Görev-Bölümü.pdf")
    assert yanit["Cache-Control"] == "no-store" and yanit["Content-Type"] == ds.PDF.mime
    assert "attachment" in yanit["Content-Disposition"]
    assert b"".join(_akis(yanit)) == pdf

    with pytest.raises(ds.TurHatasi):
        evrak_servisi.dosya_ekle(kayit, docx, bicim="PDF", dosya_adi="yanlis.pdf")
    yalniz_pdf = _kaydet(donem, belge=_belge(kod="E03"), bicimler=("PDF",))
    with pytest.raises(EvrakKaydiGecersiz, match="kaydında yok"):
        evrak_servisi.dosya_ekle(yalniz_pdf, docx, bicim="DOCX", dosya_adi="x.docx")
    _kaydet(donem, belge=_belge(ek=" Yeni."))
    with pytest.raises(EvrakKaydiGecersiz, match="Yerini yeni sürüme"):
        evrak_servisi.dosya_ekle(kayit, pdf, bicim="PDF", dosya_adi="eski.pdf")
