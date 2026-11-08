"""Veli listesi (`ParentRoster`) — model, aktarım, silme ve uçlar (T5; tasarım §5.1, §8.4).

Plan "F1b-5 uygulama kararları": kapının "kör indeks eşleşmesi" ve "parola kurulmadan kişi
yazan uç 409" testleri öğrenci yerine veli listesi ve personel üzerinden sınanır (409'un
dolaşan testi `test_kisi_yazan_uclar.py`'dedir). Buradakiler:

- **Kör indeks model düzeyinde:** `save()` indeksi doldurur; aramada katlanmış ad eşleşir;
  çözülemeyen addan indeks hesaplanmaz; veli adı toplu yazılmaz (kaynak taraması ve onun
  denetçisinin kendisi — öğrenci okul numarasının eski koruma testinin eşi).
- **Aktarım:** dosyadaki sınıflar yerine konur, ötekilere dokunulmaz; önizleme ile uygulama
  aynı sayıları verir (parite) ve önizleme hiçbir şey yazmaz; rapor ve yanıt ad taşımaz;
  kaynak sıra tutulmaz; kilitliyken yazım hata verir ve hiçbir şey yazmaz.
- **İz ve günlük:** aktarım kişisiz parti satırıdır, yerine geçen ve elle silinen satırlar
  kişisiz `KVKK_SILME`; uydurma veli adı ne denetim izinde ne uygulama günlüğünde geçer;
  erişim günlüğüne yazılmaz.
- **Uçlar ve rol:** yalnız program yöneticisi; özet yalnız sayı; şablon iki sütun.

Adların hepsi UYDURMADIR.
"""

from __future__ import annotations

import ast
import json
import logging
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.http import StreamingHttpResponse
from openpyxl import Workbook, load_workbook
from rest_framework.test import APIClient

from apps.okul import denetim_izi, selectors
from apps.okul.excel_ortak import MAKROLU_DOSYA_ILETISI, ParserError
from apps.okul.models import (
    AccessLog,
    AccountRole,
    AccountStatus,
    AuditTrail,
    ImportRun,
    ImportStatus,
    ParentRoster,
    parent_name_blind_index,
)
from apps.okul.services import imports as import_service
from apps.okul.services.templates import PARENT_TEMPLATE_HEADERS
from apps.okul.tests.hesap_ortak import hesap_ac, muhurle
from conftest import TEST_DEK, oturumu_ac_test
from shared import crypto

pytestmark = pytest.mark.django_db

KOK = Path(__file__).resolve().parents[3]
UYDURMA_VELI = "Pelinsu Uydurmakaya"


def _xlsx(
    satirlar: list[tuple[Any, ...]], basliklar: tuple[str, ...] = PARENT_TEMPLATE_HEADERS
) -> bytes:
    kitap = Workbook()
    sayfa = kitap.active
    assert sayfa is not None
    sayfa.append(list(basliklar))
    for satir in satirlar:
        sayfa.append(list(satir))
    tampon = BytesIO()
    kitap.save(tampon)
    return tampon.getvalue()


def _aktar(satirlar: list[tuple[Any, ...]], *, onizle: bool = False) -> Any:
    """Satırları yeni bir xlsx'le aktarır. Her çağrı dosyayı YENİDEN üretir: xlsx'in `core.xml`
    zaman damgası saniye sınırında değişebilir, iki çağrının özeti aynı olmayabilir. Aynı
    dosyanın (aynı özetin) iki kez aktarıldığı testler baytları bir kez üretir (`_aktar_bayt`)."""
    return _aktar_bayt(_xlsx(satirlar), onizle=onizle)


def _aktar_bayt(dosya: bytes, *, onizle: bool = False) -> Any:
    if onizle:
        return import_service.preview_parents_file(file_bytes=dosya, file_name="liste.xlsx")
    return import_service.commit_parents_file(file_bytes=dosya, file_name="liste.xlsx")


def _sayilar() -> dict[str, int]:
    return {s["student_class"]: s["rows"] for s in selectors.parent_roster_summary()["classes"]}


def _kosular() -> list[tuple[int, str]]:
    """Bütün aktarım koşuları (kimlik, durum): bir işlemin koşu bırakıp bırakmadığını sınar."""
    return list(ImportRun.objects.order_by("pk").values_list("pk", "status"))


def _kosu() -> ImportRun:
    kosu: ImportRun = ImportRun.objects.create(source_type="VELI", file_hash="f" * 64)
    return kosu


# ============================================================ kör indeks (model düzeyi)


class TestKorIndeks:
    def test_save_indeksi_doldurur_ad_sifreli_saklanir(self) -> None:
        satir = ParentRoster.objects.create(
            import_run=_kosu(), full_name="ÖRNEK VELİ", student_class="9-A"
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT full_name, name_index FROM okul_parentroster WHERE id = %s", [satir.pk]
            )
            ham_ad, ham_indeks = cursor.fetchone()
        assert ham_ad.startswith("gAAAA") and "ÖRNEK" not in ham_ad
        assert len(ham_indeks) == 64 and ham_indeks == parent_name_blind_index("ÖRNEK VELİ")
        assert ParentRoster.objects.get(pk=satir.pk).full_name == "ÖRNEK VELİ"

    def test_ad_degisince_update_fields_e_indeks_eklenir(self) -> None:
        satir = ParentRoster.objects.create(
            import_run=_kosu(), full_name="ÖRNEK VELİ", student_class="9-A"
        )
        satir.full_name = "DENEME VELİ"
        satir.save(update_fields=["full_name"])
        satir.refresh_from_db()
        assert satir.name_index == parent_name_blind_index("DENEME VELİ")

    def test_ad_yazilmayan_kayitta_indeks_hesaplanmaz(self) -> None:
        """`update_fields` adı içermiyorsa anahtar gerekmez, indeks değişmez."""
        satir = ParentRoster.objects.create(
            import_run=_kosu(), full_name="ÖRNEK VELİ", student_class="9-A"
        )
        indeks = satir.name_index
        crypto.unload_key()
        try:
            satir.student_class = "9-B"
            satir.save(update_fields=["student_class"])  # KeyMissingError YOK
        finally:
            crypto.load_key(TEST_DEK)
        assert ParentRoster.objects.get(pk=satir.pk).name_index == indeks

    def test_aramada_katlanmis_ad_eslesir(self) -> None:
        """Kör indeks eşleşmesi (tasarım §14 F1b kapısı): büyük-küçük harf, Türkçe harf ve
        fazla boşluk farkı eşleşmeyi bozmaz; farklı ad eşleşmez."""
        kosu = _kosu()
        bir = ParentRoster.objects.create(
            import_run=kosu, full_name="IŞIL ÇAĞLAR", student_class="9-A"
        )
        iki = ParentRoster.objects.create(
            import_run=kosu, full_name="Işıl Çağlar", student_class="6-B"
        )
        ParentRoster.objects.create(import_run=kosu, full_name="EMRE KAYA", student_class="9-A")

        # DB filtresi şifreli sütunda hiçbir şey bulamaz — arama kör indeksledir.
        assert not ParentRoster.objects.filter(full_name="IŞIL ÇAĞLAR").exists()
        for arama in ("ışıl  çağlar", "ISIL CAGLAR", " Işıl Çağlar "):
            assert {s.pk for s in selectors.parent_roster_by_name(arama)} == {bir.pk, iki.pk}
        assert not selectors.parent_roster_by_name("IŞIL ÇAĞ").exists()
        assert not selectors.parent_roster_by_name("").exists()

    def test_farkli_dek_ile_indeks_eslesmez(self) -> None:
        ParentRoster.objects.create(import_run=_kosu(), full_name="ÖRNEK VELİ", student_class="9-A")
        crypto.load_key(b"\x07" * 32)
        try:
            assert not selectors.parent_roster_by_name("ÖRNEK VELİ").exists()
        finally:
            crypto.load_key(TEST_DEK)
        assert selectors.parent_roster_by_name("ÖRNEK VELİ").exists()

    def test_kilitliyken_indeks_hesaplanamaz(self) -> None:
        crypto.unload_key()
        try:
            with pytest.raises(crypto.KeyMissingError):
                parent_name_blind_index("ÖRNEK VELİ")
        finally:
            crypto.load_key(TEST_DEK)

    def test_bozuk_addan_indeks_hesaplanmaz(self) -> None:
        """Çözülemeyen ad (tasarım §13 D48): kayıtlı indeks kalır, ham değer aynen geri yazılır."""
        satir = ParentRoster.objects.create(
            import_run=_kosu(), full_name="ÖRNEK VELİ", student_class="9-A"
        )
        indeks = satir.name_index
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE okul_parentroster SET full_name = %s WHERE id = %s",
                ["ÖRNEK VELİ", satir.pk],
            )
        okunan = ParentRoster.objects.get(pk=satir.pk)
        assert crypto.is_corrupt(okunan.full_name)
        okunan.save()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT full_name, name_index FROM okul_parentroster WHERE id = %s", [satir.pk]
            )
            assert cursor.fetchone() == ("ÖRNEK VELİ", indeks)


def _toplu_veli_adi_yazimlari(kaynak: str) -> list[int]:
    """Veli adını `save()`'i atlayarak yazan çağrıların satırları (AST ile; yorumlar sayılmaz).

    `….update(full_name=…)` (her alıcıda: personelde ad alanı `first_name`/`last_name`dir),
    argümanlarında 'full_name' geçen `bulk_update(…)` ya da `ParentRoster…bulk_create(…)`
    (indeksi hiç doldurmaz).
    """
    satirlar: list[int] = []
    for dugum in ast.walk(ast.parse(kaynak)):
        if not isinstance(dugum, ast.Call) or not isinstance(dugum.func, ast.Attribute):
            continue
        if dugum.func.attr == "update" and any(k.arg == "full_name" for k in dugum.keywords):
            satirlar.append(dugum.lineno)
        elif dugum.func.attr == "bulk_update" and "full_name" in ast.unparse(dugum):
            satirlar.append(dugum.lineno)
        elif dugum.func.attr == "bulk_create" and "ParentRoster" in ast.unparse(dugum.func.value):
            satirlar.append(dugum.lineno)
    return satirlar


def test_veli_adi_toplu_yazilmaz() -> None:
    """Koruma: `update(full_name=…)`/`bulk_*` `save()`'i atlar, kör indeks bozulur.

    Uygulama kodunda (testler ve göçler hariç) veli adını toplu yazan çağrı yoktur.
    """
    ihlaller = [
        f"{yol.relative_to(KOK)}:{satir}"
        for yol in KOK.rglob("*.py")
        if "tests" not in yol.parts and "migrations" not in yol.parts
        for satir in _toplu_veli_adi_yazimlari(yol.read_text(encoding="utf-8"))
    ]
    assert ihlaller == []


def test_toplu_yazim_denetcisi_ihlali_yakalar() -> None:
    """Denetçinin kendisi: gerçek çağrıyı yakalar, yorum/belge metnine takılmaz."""
    kaynak = (
        '"""`QuerySet.update(full_name=…)` belge metnidir."""\n'
        "ParentRoster.objects.filter(pk=1).update(full_name='X')\n"
        "ParentRoster.objects.bulk_update(rows, ['full_name'])\n"
        "ParentRoster.objects.filter(pk=1).update(student_class='9-A')\n"
        "ParentRoster.objects.bulk_create(rows)\n"
        "Holiday.objects.bulk_create(rows)\n"
    )
    assert _toplu_veli_adi_yazimlari(kaynak) == [2, 3, 5]


# ============================================================ aktarım


class TestAktarim:
    def test_ilk_aktarim_yazar_ve_sinif_sayilarini_verir(self) -> None:
        rapor = _aktar([("ÖRNEK VELİ", "9-A"), ("DENEME VELİ", "9/A"), ("UYDURMA VELİ", "10-B")])
        assert (rapor.total_rows, rapor.imported_rows, rapor.class_count) == (3, 3, 2)
        assert rapor.replaced_rows == 0 and rapor.kept_rows == 0 and rapor.kept_class_count == 0
        assert [(c.student_class, c.rows, c.replaced_rows) for c in rapor.classes] == [
            ("9-A", 2, 0),
            ("10-B", 1, 0),
        ]
        assert _sayilar() == {"9-A": 2, "10-B": 1}
        kosu = ImportRun.objects.get(source_type="VELI", status=ImportStatus.COMPLETED)
        assert set(ParentRoster.objects.values_list("import_run_id", flat=True)) == {kosu.pk}

    def test_dosyadaki_siniflar_yerine_gecer_otekiler_kalir(self) -> None:
        _aktar([("A VELİ", "9-A"), ("B VELİ", "9-A"), ("C VELİ", "10-B"), ("D VELİ", "11-C")])
        rapor = _aktar([("E VELİ", "9-A"), ("F VELİ", "12-D")])
        assert [(c.student_class, c.rows, c.replaced_rows) for c in rapor.classes] == [
            ("9-A", 1, 2),
            ("12-D", 1, 0),
        ]
        assert rapor.replaced_rows == 2
        assert (rapor.kept_class_count, rapor.kept_rows) == (2, 2)
        assert _sayilar() == {"9-A": 1, "10-B": 1, "11-C": 1, "12-D": 1}
        adlar = {s.full_name for s in ParentRoster.objects.filter(student_class="9-A")}
        assert adlar == {"E VELİ"}

    def test_iki_cocuklu_veli_iki_satirdir(self) -> None:
        _aktar([("ÖRNEK VELİ", "9-A"), ("ÖRNEK VELİ", "6-B"), ("ÖRNEK VELİ", "9-A")])
        assert ParentRoster.objects.count() == 3
        assert selectors.parent_roster_by_name("örnek veli").count() == 3

    def test_kaynak_sira_tutulmaz(self) -> None:
        """Satırlar sınıf ve ad sırasıyla yazılır (tasarım §5.1; denetim KM-11)."""
        _aktar(
            [("ZEHRA VELİ", "10-A"), ("CEM VELİ", "9-B"), ("ÇAĞLA VELİ", "9-B"), ("AYŞE", "9-A")]
        )
        yazilan = [(s.student_class, s.full_name) for s in ParentRoster.objects.order_by("pk")]
        assert yazilan == [
            ("9-A", "AYŞE"),
            ("9-B", "CEM VELİ"),
            ("9-B", "ÇAĞLA VELİ"),
            ("10-A", "ZEHRA VELİ"),
        ]

    def test_sorunlu_satir_aktarilmaz_ve_numarasiyla_bildirilir(self) -> None:
        rapor = _aktar([("ÖRNEK VELİ", "9-A"), ("", "9-A"), (UYDURMA_VELI, "sınıfsız")])
        assert (rapor.total_rows, rapor.imported_rows) == (3, 1)
        assert [(i.row_number, i.field) for i in rapor.issues] == [
            (3, "full_name"),
            (4, "student_class"),
        ]
        assert ParentRoster.objects.count() == 1

    def test_gecerli_satir_yoksa_hicbir_sinif_silinmez(self) -> None:
        _aktar([("ÖRNEK VELİ", "9-A")])
        rapor = _aktar([("", "9-A")])
        assert rapor.imported_rows == 0 and rapor.classes == []
        assert _sayilar() == {"9-A": 1}

    def test_onizleme_uygulamayla_ayni_sayilari_verir_ve_yazmaz(self) -> None:
        """Önizleme paritesi (tasarım §8.4; personel aktarımının deseni)."""
        _aktar([("A VELİ", "9-A"), ("B VELİ", "10-B")])
        # Önizleme ve uygulama AYNI baytları alır: rapor dosya özetini taşır (zamana bağlı
        # kalmasın diye dosya bir kez üretilir).
        dosya = _xlsx([("C VELİ", "9-A"), ("D VELİ", "9-A"), ("E VELİ", "11-C"), ("", "x")])
        iz_once = AuditTrail.objects.count()
        onizleme = _aktar_bayt(dosya, onizle=True)
        assert onizleme.dry_run is True
        assert _sayilar() == {"9-A": 1, "10-B": 1}  # hiçbir satır değişmedi
        # Kalıcı olan yalnız PREVIEWED koşusu ve onun OLUSTUR satırı.
        assert ImportRun.objects.filter(status=ImportStatus.PREVIEWED).count() == 1
        assert AuditTrail.objects.count() == iz_once + 1
        assert not AuditTrail.objects.filter(action="KVKK_SILME").exists()

        uygulama = _aktar_bayt(dosya)
        once, sonra = onizleme.to_dict(), uygulama.to_dict()
        for anahtar in ("dry_run", "already_imported"):
            once.pop(anahtar), sonra.pop(anahtar)
        assert once == sonra

    def test_ayni_dosya_yeniden_aktarilir_uyariyla(self) -> None:
        # Dosya bir kez üretilir: iki ayrı üretimin `core.xml` zaman damgası saniye sınırında
        # farklılaşır, özet değişir ve test zamana bağlı düşerdi.
        dosya = _xlsx([("ÖRNEK VELİ", "9-A")])
        _aktar_bayt(dosya)
        rapor = _aktar_bayt(dosya)
        assert rapor.already_imported is True and rapor.replaced_rows == 1
        assert ParentRoster.objects.count() == 1
        assert ImportRun.objects.filter(source_type="VELI", status="COMPLETED").count() == 1

    def test_csv_ve_xls_disi_bicimler_ve_makro(self) -> None:
        csv = "Velinin Adı Soyadı;Öğrencinin Sınıfı\nÖRNEK VELİ;9-A\n".encode()
        rapor = import_service.commit_parents_file(file_bytes=csv, file_name="veli.csv")
        assert rapor.imported_rows == 1
        with pytest.raises(ParserError, match="Makro"):
            import_service.commit_parents_file(file_bytes=_xlsx([]), file_name="veli.xlsm")
        kosu = ImportRun.objects.filter(source_type="VELI").order_by("-pk").first()
        assert kosu is not None and kosu.status == ImportStatus.FAILED
        assert kosu.report == {"error": MAKROLU_DOSYA_ILETISI}

    def test_yinelenen_baslik_uyarisi_turkce_alan_adiyla_raporda(self) -> None:
        """Başlık satırının uyarısı alanı Türkçe adıyla anar; iç anahtar (`student_class`) sızmaz."""
        csv = "Velinin Adı Soyadı;Öğrencinin Sınıfı;Sınıf\nÖRNEK VELİ;9-A;9-B\n".encode()
        rapor = import_service.commit_parents_file(file_bytes=csv, file_name="veli.csv")
        assert rapor.imported_rows == 1
        assert [(s.row_number, s.field, s.issue) for s in rapor.issues] == [
            (
                1,
                "header",
                "“Sınıf” sütunu da “Öğrencinin sınıfı” alanına uyuyor; ilk uyan sütun kullanıldı, "
                "bu sütun okunmadı.",
            )
        ]
        kalici = json.dumps(ImportRun.objects.get(status="COMPLETED").report, ensure_ascii=False)
        for anahtar in ("'student_class'", "'full_name'"):
            assert anahtar not in kalici

    def test_kilitliyken_yazim_hata_verir_ve_hicbir_sey_yazilmaz(self) -> None:
        _aktar([("ÖRNEK VELİ", "9-A")])
        iz_once = AuditTrail.objects.count()
        kosular_once = _kosular()
        crypto.unload_key()
        try:
            with pytest.raises(crypto.KeyMissingError):
                _aktar([("DENEME VELİ", "9-A")])
        finally:
            crypto.load_key(TEST_DEK)
        assert [s.full_name for s in ParentRoster.objects.all()] == ["ÖRNEK VELİ"]
        assert AuditTrail.objects.count() == iz_once
        # Açılan RUNNING koşusu da geri sarılır (`_ingest_parents` atomiktir).
        assert _kosular() == kosular_once

    def test_yazim_yarida_kalirsa_aktarim_butunuyle_geri_alinir(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Eski sınıf satırları silinip yeni satırların yazımı patlarsa hiçbir şey değişmez:
        eski satırlar, koşular ve denetim izi aynen kalır (`_ingest_parents` atomiktir; atomiklik
        kaldırılırsa bu test düşer)."""
        _aktar([("A VELİ", "9-A"), ("B VELİ", "10-B")])
        satirlar_once = sorted(
            ParentRoster.objects.values_list("pk", "import_run_id", "student_class", "name_index")
        )
        kosular_once = _kosular()
        iz_once = AuditTrail.objects.count()
        gercek_create = ParentRoster.objects.create
        yazilan: list[int] = []

        def patlayan_create(**alanlar: Any) -> ParentRoster:
            # İlk satır yazılır, ikincisi patlar: silme ve kısmi yazım geri sarılmalı.
            if yazilan:
                raise RuntimeError("uydurma yazım hatası")
            satir: ParentRoster = gercek_create(**alanlar)
            yazilan.append(satir.pk)
            return satir

        with monkeypatch.context() as yama:
            yama.setattr(ParentRoster.objects, "create", patlayan_create)
            with pytest.raises(RuntimeError, match="uydurma yazım hatası"):
                _aktar([("C VELİ", "9-A"), ("D VELİ", "9-A")])

        assert yazilan, "sınama yazımın ortasında patlamadı"
        assert (
            sorted(
                ParentRoster.objects.values_list(
                    "pk", "import_run_id", "student_class", "name_index"
                )
            )
            == satirlar_once
        )
        assert _kosular() == kosular_once
        assert AuditTrail.objects.count() == iz_once


# ============================================================ iz, günlük ve silme


class TestIzVeGunluk:
    def test_aktarim_kisisiz_parti_satiridir(self) -> None:
        _aktar([("A VELİ", "9-A"), ("B VELİ", "9-A")])
        bas = AuditTrail.objects.order_by("-seq").values_list("seq", flat=True).first() or 0
        _aktar([("C VELİ", "9-A")])
        yeni = list(AuditTrail.objects.filter(seq__gt=bas).order_by("seq"))
        assert [(s.action, s.model) for s in yeni] == [
            ("OLUSTUR", "okul.ImportRun"),
            ("KVKK_SILME", "okul.ParentRoster"),
            ("DURUM", "okul.ImportRun"),
        ]
        silme = yeni[1]
        assert silme.object_id == "" and silme.record_mac == ""
        assert silme.values["adet"] == [None, 2]
        assert silme.values["tetik"] == [None, denetim_izi.KVKK_TETIK_AKTARIM]
        assert set(silme.changed_fields) == {
            "import_run",
            "full_name",
            "name_index",
            "student_class",
            "created_at",
        }
        assert (
            not AuditTrail.objects.filter(model="okul.ParentRoster")
            .exclude(action="KVKK_SILME")
            .exists()
        )
        assert denetim_izi.zinciri_dogrula() == []

    def test_elle_silme_butun_listeyi_siler_kisisiz_satirla(self) -> None:
        _aktar([("A VELİ", "9-A"), ("B VELİ", "10-B"), ("C VELİ", "11-C")])
        assert import_service.delete_parent_roster() == 3
        assert not ParentRoster.objects.exists()
        satir = AuditTrail.objects.filter(action="KVKK_SILME").order_by("-seq").first()
        assert satir is not None and satir.model == "okul.ParentRoster"
        assert satir.values["adet"] == [None, 3]
        assert satir.values["tetik"] == [None, denetim_izi.KVKK_TETIK_ELLE_SILME]
        # Boş listede silme bir şey yazmaz.
        iz = AuditTrail.objects.count()
        assert import_service.delete_parent_roster() == 0
        assert AuditTrail.objects.count() == iz

    def test_veli_adi_izde_gunlukte_ve_raporda_gecmez(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.DEBUG)
        dosya_adi = "liste.xlsx"
        dosya = _xlsx([(UYDURMA_VELI, "9-A"), ("Hayal Masalcı", "10-B")])
        onizleme = import_service.preview_parents_file(file_bytes=dosya, file_name=dosya_adi)
        uygulama = import_service.commit_parents_file(file_bytes=dosya, file_name=dosya_adi)
        tokenlar = [s.full_name for s in ParentRoster.objects.all()]
        with connection.cursor() as cursor:
            cursor.execute("SELECT full_name, name_index FROM okul_parentroster")
            hamlar = [str(h) for satir in cursor.fetchall() for h in satir]
        import_service.commit_parents_file(
            file_bytes=_xlsx([("X VELİ", "9-A")]), file_name="2.xlsx"
        )
        import_service.delete_parent_roster()

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM okul_audittrail")
            iz = json.dumps([list(map(str, s)) for s in cursor.fetchall()], ensure_ascii=False)
            cursor.execute("SELECT report FROM okul_importrun")
            raporlar = " ".join(str(r[0]) for r in cursor.fetchall())
        yanitlar = json.dumps([onizleme.to_dict(), uygulama.to_dict()], ensure_ascii=False)
        gunluk = caplog.text
        assert set(tokenlar) == {UYDURMA_VELI, "Hayal Masalcı"}
        for parca in ("Pelinsu", "Uydurmakaya", "PELİNSU", "pelinsu", "Hayal", "Masalcı", *hamlar):
            assert parca not in iz, parca
            assert parca not in raporlar, parca
            assert parca not in yanitlar, parca
            assert parca not in gunluk, parca
        assert "Veli listesi aktarımı uygulandı" in gunluk
        # Erişim günlüğüne yazılmaz (plan "F1b-5 uygulama kararları").
        assert not AccessLog.objects.exists()


# ============================================================ uçlar ve rol


class TestUclar:
    def test_ozet_yalniz_sayi_tasir(self) -> None:
        _aktar([(UYDURMA_VELI, "9-A"), ("DENEME VELİ", "9-A"), ("ÖRNEK VELİ", "Hazırlık/A")])
        veri = APIClient().get("/api/v1/parent-roster/").json()
        assert veri["total_rows"] == 3 and veri["class_count"] == 2
        assert veri["classes"] == [
            {"student_class": "Hazırlık-A", "rows": 1},
            {"student_class": "9-A", "rows": 2},
        ]
        assert veri["last_import_at"] is not None
        assert "Pelinsu" not in json.dumps(veri, ensure_ascii=False)

    def test_bos_ozet(self) -> None:
        veri = APIClient().get("/api/v1/parent-roster/").json()
        assert veri == {"total_rows": 0, "class_count": 0, "last_import_at": None, "classes": []}

    def test_onizleme_ve_aktarim_ucu_dosya_ister(self) -> None:
        istemci = APIClient()
        yanit = istemci.post("/api/v1/imports/parents/preview/", {}, format="multipart")
        assert yanit.status_code == 400
        assert yanit.json()["fields"]["file"] == ["Veli listesi dosyasını seçin."]
        dosya = SimpleUploadedFile("veli.xlsx", _xlsx([(UYDURMA_VELI, "9-A")]))
        yanit = istemci.post("/api/v1/imports/parents/commit/", {"file": dosya}, format="multipart")
        assert yanit.status_code == 200, yanit.json()
        assert yanit.json()["imported_rows"] == 1
        assert "Pelinsu" not in yanit.content.decode()

    def test_taninmayan_dosya_400_turkce(self) -> None:
        dosya = SimpleUploadedFile("veli.xlsx", _xlsx([("x",)], basliklar=("Adı Soyadı",)))
        yanit = APIClient().post(
            "/api/v1/imports/parents/preview/", {"file": dosya}, format="multipart"
        )
        assert yanit.status_code == 400
        assert "Velinin Adı Soyadı" in yanit.json()["message"]

    def test_silme_ucu(self) -> None:
        _aktar([("ÖRNEK VELİ", "9-A")])
        yanit = APIClient().delete("/api/v1/parent-roster/")
        assert yanit.status_code == 200
        assert yanit.json() == {"deleted_rows": 1}
        assert not ParentRoster.objects.exists()

    def test_sablon_iki_sutunludur(self) -> None:
        yanit = APIClient().get("/api/v1/templates/parents/")
        assert yanit.status_code == 200
        assert "sablon-veli-listesi.xlsx" in yanit["Content-Disposition"]
        assert isinstance(yanit, StreamingHttpResponse)
        govde = b"".join(cast(Iterable[bytes], yanit.streaming_content))
        kitap = load_workbook(BytesIO(govde))
        sayfa = kitap.active
        assert sayfa is not None
        assert [h.value for h in sayfa[1]] == list(PARENT_TEMPLATE_HEADERS)
        assert sayfa.max_column == 2

    @pytest.mark.parametrize(
        "rol", [r for r in AccountRole if r is not AccountRole.YONETICI], ids=lambda r: r.value
    )
    def test_oteki_roller_403(self, rol: AccountRole) -> None:
        hesap = muhurle(hesap_ac(rol, ad="Uydurma Hesap"), status=AccountStatus.ACIK)
        oturumu_ac_test(str(hesap.id), tanitici=hesap.login_name, rol=rol.value)
        istemci = APIClient()
        dosya = SimpleUploadedFile("veli.xlsx", _xlsx([("ÖRNEK VELİ", "9-A")]))
        yanitlar = [
            istemci.get("/api/v1/parent-roster/"),
            istemci.delete("/api/v1/parent-roster/"),
            istemci.post("/api/v1/imports/parents/preview/", {"file": dosya}, format="multipart"),
            istemci.post("/api/v1/imports/parents/commit/", {}, format="multipart"),
            istemci.get("/api/v1/templates/parents/"),
        ]
        assert [y.status_code for y in yanitlar] == [403] * 5
        assert not ImportRun.objects.filter(source_type="VELI").exists()
