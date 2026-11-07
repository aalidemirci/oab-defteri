"""`okul` modelleri — kısıtlar, singleton, seviye kümesi (aile iskeletinden alındı).

Aile test kalıbından uyarlandı: TCKN/veli/tatil testleri kalktı; okul içi seviye
sabiti (1-12 + hazırlık bayrağı), okul-no teklik kısıtı ve şube kataloğu eklendi.
Okul no şifreli + kör indeks (tasarım §5.3) — teklik indekste, sütun DB'de token;
personelde unvan/branş yok, üye türü ve ayrılış tarihi var.
"""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path

import pytest
from django.db import IntegrityError, connection

from apps.okul.models import (
    CanteenMode,
    ClassSection,
    MemberKind,
    Personnel,
    SchoolConfig,
    SchoolLevel,
    SchoolYear,
    SettlementType,
    StaffingMode,
    Student,
    StudentStatus,
    grade_levels_for,
    student_number_blind_index,
)
from conftest import TEST_DEK
from shared import crypto


def _toplu_okul_no_yazimlari(kaynak: str) -> list[int]:
    """Okul no'yu `save()`'i atlayarak yazan çağrıların satırları (AST ile; yorumlar sayılmaz).

    `….update(student_number=…)`, argümanlarında 'student_number' geçen
    `bulk_update(…)` ya da `Student…bulk_create(…)` (indeksi hiç doldurmaz).
    """
    satirlar: list[int] = []
    for dugum in ast.walk(ast.parse(kaynak)):
        if not isinstance(dugum, ast.Call) or not isinstance(dugum.func, ast.Attribute):
            continue
        if dugum.func.attr == "update" and any(k.arg == "student_number" for k in dugum.keywords):
            satirlar.append(dugum.lineno)
        elif dugum.func.attr == "bulk_update" and "student_number" in ast.unparse(dugum):
            satirlar.append(dugum.lineno)
        elif dugum.func.attr == "bulk_create" and "Student" in ast.unparse(dugum.func.value):
            satirlar.append(dugum.lineno)
    return satirlar


@pytest.mark.django_db
@pytest.mark.hesapsiz  # satır yokken davranış: varsayılan hesabın parmak izi satırı kurulmaz
class TestSchoolConfig:
    def test_load_kayit_yokken_kaydedilmemis_varsayilan_doner(self) -> None:
        config = SchoolConfig.load()
        assert config.pk is None
        assert config.setup_completed is False
        assert SchoolConfig.objects.count() == 0  # okuma yazmaz

    def test_load_mevcut_sati̇ri_doner(self) -> None:
        SchoolConfig.objects.create(pk=SchoolConfig.SINGLETON_PK, school_name="Örnek AL")
        assert SchoolConfig.load().school_name == "Örnek AL"

    def test_okul_kartinin_yeni_alanlari_bos_baslar(self) -> None:
        """Var olan kurulumda yeni alanlar boştur (kurulum kapısı yeniden kapanmaz)."""
        config = SchoolConfig.objects.create(pk=SchoolConfig.SINGLETON_PK)
        config.refresh_from_db()
        assert config.institution_code == ""
        assert config.levels == []
        assert (config.student_count, config.student_count_as_of) == (None, None)
        assert (config.settlement_type, config.canteen_mode, config.staffing_mode) == ("", "", "")
        assert config.in_campus is False
        assert config.opened_on is None


@pytest.mark.django_db
@pytest.mark.hesapsiz  # kısıtlar satırın kendisinde sınanır; iz anahtarı gerekmez
class TestSchoolConfigKisitlari:
    """Okul kartının DB kısıtları (F1b 4. adım): program dışından yazılan değer de reddedilir.

    `levels` için DB kısıtı yoktur (SQLite'ta JSON listesine kısıt yazılamaz; doğrulama
    serileştiricide ve `missing_school_fields`'ta)."""

    @pytest.mark.parametrize(
        ("alan", "deger"),
        [
            ("settlement_type", "KOY"),
            ("canteen_mode", "KIRALIK"),
            ("staffing_mode", "TASERON"),
            ("institution_code", "12345"),
            ("institution_code", "1"),
        ],
    )
    def test_gecersiz_deger_reddedilir(self, alan: str, deger: str) -> None:
        with pytest.raises(IntegrityError):
            SchoolConfig.objects.create(pk=SchoolConfig.SINGLETON_PK, **{alan: deger})

    @pytest.mark.parametrize(
        ("alan", "deger"),
        [
            ("settlement_type", SettlementType.IL_MERKEZI_BUYUKSEHIR_DEGIL),
            ("canteen_mode", CanteenMode.KANTIN_YOK),
            ("staffing_mode", StaffingMode.CALISTIRMIYOR),
            ("settlement_type", ""),
            ("institution_code", ""),
            ("institution_code", "999001"),
        ],
    )
    def test_gecerli_deger_ve_bos_kabul_edilir(self, alan: str, deger: str) -> None:
        SchoolConfig.objects.create(pk=SchoolConfig.SINGLETON_PK, **{alan: deger})

    @pytest.mark.parametrize(
        "alanlar",
        [{"student_count": 10}, {"student_count_as_of": date(2026, 10, 1)}],
        ids=["tarihsiz_mevcut", "mevcutsuz_tarih"],
    )
    def test_mevcut_ve_tarihi_birlikte_dolu_ya_da_bos(self, alanlar: dict[str, object]) -> None:
        with pytest.raises(IntegrityError):
            SchoolConfig.objects.create(pk=SchoolConfig.SINGLETON_PK, **alanlar)

    def test_mevcut_ust_siniri(self) -> None:
        tarih = date(2026, 10, 1)
        SchoolConfig.objects.create(
            pk=SchoolConfig.SINGLETON_PK, student_count=99999, student_count_as_of=tarih
        )
        with pytest.raises(IntegrityError):
            SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(student_count=100000)

    def test_kademe_enumu_tasarimdaki_sirayla(self) -> None:
        """Değer adları tasarım §5.1 ile birebir; sıra `levels`'in kanonik sırasıdır."""
        assert SchoolLevel.values == ["OKUL_ONCESI", "ILKOKUL", "ORTAOKUL", "ORTAOGRETIM"]
        assert SettlementType.values == ["BUYUKSEHIR", "IL_MERKEZI_BUYUKSEHIR_DEGIL", "DIGER"]
        assert CanteenMode.values == ["KIRAYA_VERILIYOR", "BIRLIKCE_ISLETILIYOR", "KANTIN_YOK"]
        assert StaffingMode.values == ["DOGRUDAN_ISVEREN", "HIZMET_ALIMI", "CALISTIRMIYOR"]


class TestGradeLevels:
    def test_varsayilan_kume_1_12(self) -> None:
        """Seviye kümesi okul içi sabittir: ders çizelgesine/okul türüne bağlı değildir."""
        assert grade_levels_for(has_prep_class=False) == tuple(range(1, 13))

    def test_hazirlik_bayragi_sifir_seviyesini_basa_ekler(self) -> None:
        assert grade_levels_for(has_prep_class=True) == (0, *range(1, 13))

    def test_kurulmamis_okulda_hazirlik_kapalidir(self) -> None:
        assert SchoolConfig().grade_levels == tuple(range(1, 13))


@pytest.mark.django_db
class TestSchoolYear:
    def test_ayni_ad_canli_kayitta_tekil(self) -> None:
        SchoolYear.objects.create(
            name="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 6, 30)
        )
        with pytest.raises(IntegrityError):
            SchoolYear.objects.create(
                name="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 6, 30)
            )

    def test_silinen_yilin_adi_yeniden_kullanilabilir(self) -> None:
        yil = SchoolYear.objects.create(
            name="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 6, 30)
        )
        yil.delete()  # soft delete
        SchoolYear.objects.create(
            name="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 6, 30)
        )

    def test_tek_aktif_yil_kisiti(self) -> None:
        SchoolYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
            is_active=True,
        )
        with pytest.raises(IntegrityError):
            SchoolYear.objects.create(
                name="2026-2027",
                start_date=date(2026, 9, 1),
                end_date=date(2027, 6, 30),
                is_active=True,
            )


@pytest.mark.django_db
class TestStudent:
    def test_ayni_okul_no_aktif_canli_kayitta_tekil(self) -> None:
        """Teklik KÖR İNDEKSTEDİR: '0101' ile '101' aynı numaradır (§5.3)."""
        Student.objects.create(first_name="A", last_name="B", student_number="101")
        with pytest.raises(IntegrityError):
            Student.objects.create(first_name="C", last_name="D", student_number="0101")

    def test_okul_no_db_de_duz_metin_durmaz(self) -> None:
        """F1 kod kapısı: okul no sütunu ham SQL ile okununca token'dır, numara değil."""
        ogrenci = Student.objects.create(first_name="A", last_name="B", student_number="4711")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT student_number, student_number_index FROM okul_student WHERE id = %s",
                [ogrenci.pk],
            )
            ham_no, ham_indeks = cursor.fetchone()
        assert ham_no != "4711" and "4711" not in ham_no
        assert ham_no.startswith("gAAAA")  # Fernet token'ı
        assert len(ham_indeks) == 64 and "4711" not in ham_indeks
        assert ham_indeks == student_number_blind_index("4711")
        assert Student.objects.get(pk=ogrenci.pk).student_number == "4711"

    def test_kor_indeks_save_ile_dolar_ve_update_fields_e_eklenir(self) -> None:
        ogrenci = Student.objects.create(first_name="A", last_name="B", student_number="101")
        assert ogrenci.student_number_index == student_number_blind_index("101")

        ogrenci.student_number = "202"
        ogrenci.save(update_fields=["student_number", "updated_at"])

        ogrenci.refresh_from_db()
        assert ogrenci.student_number_index == student_number_blind_index("202")

    def test_numara_yazilmayan_kayitta_indeks_hesaplanmaz(self) -> None:
        """`update_fields` okul no içermiyorsa indeks yeniden hesaplanmaz, anahtar gerekmez."""
        ogrenci = Student.objects.create(first_name="A", last_name="B", student_number="101")
        indeks = ogrenci.student_number_index
        crypto.unload_key()
        try:
            ogrenci.status = StudentStatus.LEFT
            ogrenci.save(update_fields=["status", "updated_at"])  # KeyMissingError YOK
        finally:
            crypto.load_key(TEST_DEK)
        assert Student.objects.get(pk=ogrenci.pk).student_number_index == indeks

    def test_kilitliyken_okul_no_yazilamaz(self) -> None:
        """Fail-closed: anahtar yokken kör indeks de hesaplanamaz (§5.3)."""
        crypto.unload_key()
        try:
            with pytest.raises(crypto.KeyMissingError):
                student_number_blind_index("101")
        finally:
            crypto.load_key(TEST_DEK)

    def test_okul_no_toplu_yazilmaz(self) -> None:
        """Koruma: `update(student_number=…)`/`bulk_update` `save()`'i atlar, indeks bozulur.

        Uygulama kodunda (testler ve göçler hariç) okul no'yu toplu yazan çağrı yoktur.
        """
        kok = Path(__file__).resolve().parents[3]
        ihlaller = [
            f"{yol.relative_to(kok)}:{satir}"
            for yol in kok.rglob("*.py")
            if "tests" not in yol.parts and "migrations" not in yol.parts
            for satir in _toplu_okul_no_yazimlari(yol.read_text(encoding="utf-8"))
        ]
        assert ihlaller == []

    def test_toplu_yazim_denetcisi_ihlali_yakalar(self) -> None:
        """Denetçinin kendisi: gerçek çağrıyı yakalar, yorum/belge metnine takılmaz."""
        kaynak = (
            '"""`QuerySet.update(student_number=…)` belge metnidir."""\n'
            "Student.objects.filter(pk=1).update(student_number='1')\n"
            "Student.objects.bulk_update(rows, ['student_number'])\n"
            "Student.objects.filter(pk=1).update(status='LEFT')\n"
            "Student.objects.bulk_create(rows)\n"
            "Holiday.objects.bulk_create(rows)\n"
        )
        assert _toplu_okul_no_yazimlari(kaynak) == [2, 3, 5]

    def test_ayrilan_ogrencinin_numarasi_yeniden_verilebilir(self) -> None:
        eski = Student.objects.create(first_name="A", last_name="B", student_number="101")
        eski.status = StudentStatus.LEFT
        eski.save(update_fields=["status"])
        Student.objects.create(first_name="C", last_name="D", student_number="101")

    def test_numarasiz_kayitlar_kisit_disi(self) -> None:
        Student.objects.create(first_name="A", last_name="B")
        Student.objects.create(first_name="C", last_name="D")  # patlamaz

    def test_class_label_bicimleri(self) -> None:
        assert (
            Student(first_name="A", last_name="B", class_level=10, class_section="A").class_label
            == "10/A"
        )
        assert (
            Student(first_name="A", last_name="B", class_level=0, class_section="B").class_label
            == "Hz/B"
        )
        assert Student(first_name="A", last_name="B").class_label == ""

    def test_full_name(self) -> None:
        assert Student(first_name="EMRE CAN", last_name="YILMAZ").full_name == "EMRE CAN YILMAZ"

    def test_korunan_alan_listesi_okul_no_yu_icerir(self) -> None:
        """Güvenlik ekranının "korunan alanlar" listesi koddan okunur (şifreli alanlar)."""
        from apps.okul.services import app_password

        etiketler = app_password.protected_field_labels()
        assert {"ad", "soyad", "okul no"} <= set(etiketler)
        assert "okul no kör indeksi" not in etiketler  # indeks şifreli alan değildir

    def test_ayrilis_tarihi_alani_var(self) -> None:
        ogrenci = Student.objects.create(first_name="A", last_name="B")
        assert ogrenci.left_at is None


@pytest.mark.django_db
class TestPersonnel:
    def test_unvan_ve_brans_alani_yoktur(self) -> None:
        """Tasarım §8.4: branş, küçük okulda öğretmeni kişiye bağlar — model onu hiç tutmaz."""
        alanlar = {alan.name for alan in Personnel._meta.get_fields()}
        assert not {"title", "branch"} & alanlar
        assert {"member_kind", "left_at", "is_active"} <= alanlar

    def test_uye_turu_varsayilan_ogretmendir(self) -> None:
        kisi = Personnel.objects.create(first_name="A", last_name="B")
        assert kisi.member_kind == MemberKind.TEACHER
        assert MemberKind.STAFF.label == "diğer personel"

    def test_gecersiz_uye_turu_db_kisitina_takilir(self) -> None:
        with pytest.raises(IntegrityError):
            Personnel.objects.create(first_name="A", last_name="B", member_kind="MUDUR")


@pytest.mark.django_db
class TestClassSection:
    def test_ayni_yil_ve_sube_tekil(self) -> None:
        yil = SchoolYear.objects.create(
            name="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 6, 30)
        )
        ClassSection.objects.create(school_year=yil, class_level=10, class_section="A")
        with pytest.raises(IntegrityError):
            ClassSection.objects.create(school_year=yil, class_level=10, class_section="A")

    def test_hazirlik_etiketi(self) -> None:
        yil = SchoolYear.objects.create(
            name="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 6, 30)
        )
        sube = ClassSection.objects.create(school_year=yil, class_level=0, class_section="A")
        assert sube.class_label == "Hz/A"
