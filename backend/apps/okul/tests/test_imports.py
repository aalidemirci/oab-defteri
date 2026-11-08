"""İçe aktarma servisi — personel upsert, dry-run paritesi, idempotency, FAILED izi.

Aile test kalıbından uyarlandı: TCKN/veli senaryoları kalktı. Öğrenci aktarımı (okul-no upsert,
şube tohumu) F1b 5. adımda öğrenci sicili ve şube kataloğuyla söküldü (tasarım §5.1 ALMA);
türden bağımsız sınamalar (önizleme paritesi, koşu yaşam döngüsü, uçlar) personel üzerinden
yürür. Bütün adlar uydurmadır (KVKK).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from django.db import transaction
from django.urls import NoReverseMatch, reverse
from rest_framework.test import APIClient

from apps.okul import denetim_izi
from apps.okul.excel_ortak import ParserError
from apps.okul.models import (
    ImportRun,
    ImportSourceType,
    ImportStatus,
    MemberKind,
    Personnel,
)
from apps.okul.services import imports as import_service

BASLIK = "Adı\tSoyadı\tGörevi"

#: Sentetik e-Okul ihraç örnekleri (gerçek veri DEĞİL — bkz. tests/veri/).
VERI = Path(__file__).resolve().parent / "veri"
EOKUL_PERSONEL_LISTESI = VERI / "eokul_personel_listesi.xls"


def _metin(*satirlar: str) -> str:
    return "\n".join([BASLIK, *satirlar])


@pytest.mark.django_db
class TestPreview:
    def test_dry_run_hicbir_sey_yazmaz_ama_rapor_paritesi_tam(self) -> None:
        metin = _metin("EMRE CAN\tYILMAZ\tÖğretmen", "\t\tMemur")
        onizleme = import_service.preview_personnel_text(text=metin)
        assert onizleme.dry_run is True
        assert Personnel.all_objects.count() == 0

        gercek = import_service.commit_personnel_text(text=metin)
        assert onizleme.created_personnel == gercek.created_personnel == 1
        assert [s.issue for s in onizleme.skipped] == [s.issue for s in gercek.skipped]

    def test_onizleme_kalici_iz_birakir(self) -> None:
        import_service.preview_personnel_text(text=_metin("EMRE CAN\tYILMAZ\tÖğretmen"))
        kosu = ImportRun.objects.get(status=ImportStatus.PREVIEWED)
        assert kosu.source_type == ImportSourceType.PERSONEL


@pytest.mark.django_db
class TestImportRunLifecycle:
    def test_ayni_hash_yeniden_commit_mevcut_satiri_gunceller(self) -> None:
        metin = _metin("EMRE CAN\tYILMAZ\tÖğretmen")
        import_service.commit_personnel_text(text=metin)
        import_service.commit_personnel_text(text=metin)
        assert ImportRun.objects.filter(status=ImportStatus.COMPLETED).count() == 1

    def test_parser_hatasi_failed_izi_birakir(self) -> None:
        with pytest.raises(ParserError):
            import_service.commit_personnel_text(text="Alakasız\tBaşlıklar\n1\t2")
        kayit = ImportRun.objects.get(status=ImportStatus.FAILED)
        assert "Zorunlu sütun" in kayit.report["error"]

    def test_bozuk_excel_dosyasi_turkce_hata_ve_failed_izi(self) -> None:
        with pytest.raises(ParserError, match="Dosya okunamadı. Desteklenen biçimler"):
            import_service.commit_personnel_file(file_bytes=b"PK\x03\x04 bozuk", file_name="x.xlsx")
        assert ImportRun.objects.filter(status=ImportStatus.FAILED).count() == 1

    def test_satir_sonu_farki_ayni_hashe_iner(self) -> None:
        assert import_service.text_hash("a\tb\r\nc\td") == import_service.text_hash("a\tb\nc\td")


@pytest.mark.django_db
class TestPersonnelImport:
    def test_yeni_personel_olusur_ve_ada_gore_guncellenir(self) -> None:
        rapor = import_service.commit_personnel_text(
            text="Adı\tSoyadı\tGörevi\tBranşı\nAYŞE\tÖĞRETMEN\tÖğretmen\tCoğrafya"
        )
        assert rapor.created_personnel == 1

        rapor2 = import_service.commit_personnel_text(
            text="Adı\tSoyadı\tGörevi\tBranşı\nAYŞE\tÖĞRETMEN\tMemur\tCoğrafya"
        )
        assert rapor2.updated_personnel == 1
        assert Personnel.objects.count() == 1
        kisi = Personnel.objects.first()
        assert kisi is not None and kisi.member_kind == MemberKind.DIGER

    def test_bos_hucre_mevcut_veriyi_silmez(self) -> None:
        """Görev hücresi boşsa görev türü değişmez (tanınmayan görev mevcut veriyi silmez)."""
        import_service.commit_personnel_text(text="Adı\tSoyadı\tGörevi\nAYŞE\tÖĞRETMEN\tHizmetli")
        rapor = import_service.commit_personnel_text(text="Adı\tSoyadı\tGörevi\nAYŞE\tÖĞRETMEN\t")
        kisi = Personnel.objects.first()
        assert kisi is not None and kisi.member_kind == MemberKind.DIGER
        assert rapor.unchanged_personnel == 1
        assert [u.field for u in rapor.warnings] == ["member_kind"]

    def test_bos_ad_soyad_atlanir(self) -> None:
        rapor = import_service.commit_personnel_text(text="Adı\tSoyadı\n\t")
        assert rapor.created_personnel == 0


@pytest.mark.django_db
class TestEokulDosyasi:
    """Uçtan uca: e-Okul'un DEĞİŞTİRİLMEMİŞ .xls raporu doğrudan yüklenir.

    Fixture'lar sentetiktir (`tests/veri/uret_eokul_ornekleri.py`) — yerleşim
    gerçek raporlarla aynı, adlar uydurmadır (KVKK).
    """

    def test_personel_listesi_dosyasi_aktarilir(self) -> None:
        rapor = import_service.commit_personnel_file(
            file_bytes=EOKUL_PERSONEL_LISTESI.read_bytes(), file_name="OOK01001R1_826.XLS"
        )
        assert rapor.created_personnel == 4
        assert Personnel.objects.count() == 4
        # Sayaç dipnotu ('Toplam Personel Sayısı: 4') personel olarak yazılmadı.
        assert not any("Sayısı" in p.full_name for p in Personnel.objects.all())


@pytest.mark.django_db
class TestImportApi:
    def test_onizleme_ve_aktarma_uclari(self) -> None:
        client = APIClient()
        metin = _metin("EMRE CAN\tYILMAZ\tÖğretmen")
        on = client.post("/api/v1/imports/personnel/preview/", {"text": metin}, format="multipart")
        assert on.status_code == 200 and on.json()["dry_run"] is True
        assert Personnel.all_objects.count() == 0

        yanit = client.post(
            "/api/v1/imports/personnel/commit/", {"text": metin}, format="multipart"
        )
        assert yanit.status_code == 200
        assert Personnel.objects.count() == 1

    def test_dosya_ve_metin_ayni_anda_reddedilir(self) -> None:
        yanit = APIClient().post("/api/v1/imports/personnel/preview/", {}, format="multipart")
        assert yanit.status_code == 400
        assert yanit.json()["code"] == "validation_error"

    def test_ogrenci_aktarim_uclari_yoktur(self) -> None:
        """Öğrenci aktarımı F1b 5. adımda söküldü (tasarım §5.1 ALMA, T5).

        Adsız yol açık oturumda rol kapısında kesilir (her role kapalı, 403); yol çözülseydi
        yine de ad tablosunda olmazdı.
        """
        for ad in ("import-students-preview", "import-students-commit", "template-students"):
            with pytest.raises(NoReverseMatch):
                reverse(ad)
        client = APIClient()
        yanit = client.post("/api/v1/imports/students/preview/", {"text": "x"}, format="multipart")
        assert yanit.status_code == 403
        assert not ImportRun.objects.exists()


@pytest.mark.django_db
def test_aktarim_turleri_tasarimin_adlarini_tasir_eski_ogrenci_kosusu_dogrulanir() -> None:
    """Tasarım §5.1 `ImportRun`: türler PERSONEL ve VELI. Öğrenci aktarımından kalan `STUDENTS`
    koşusu çevrilmez (göç 0015): değeri kümede olmasa da kaydı doğrulanmayı sürdürür."""
    assert ImportSourceType.values == ["PERSONEL", "VELI"]
    with transaction.atomic():
        kosu = ImportRun.objects.create(
            source_type="STUDENTS", file_hash="e" * 64, status=ImportStatus.COMPLETED
        )
        denetim_izi.degisiklik(kosu, onceki=None)

    kosu.refresh_from_db()
    assert kosu.source_type == "STUDENTS"
    assert denetim_izi.kaydi_dogrula(ImportRun, kosu.pk) is True
    assert denetim_izi.zinciri_dogrula() == []
