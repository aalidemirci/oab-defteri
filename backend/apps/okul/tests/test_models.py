"""`okul` modelleri — kısıtlar, singleton, şifreli kişi alanları (aile iskeletinden alındı).

Aile test kalıbından uyarlandı: TCKN/veli/tatil testleri kalktı. Öğrenci sicili, şube kataloğu
ve hazırlık sınıfı bayrağı (seviye kümesi) F1b 5. adımda göç 0014 ile düştü (tasarım §5.1
ALMA); okul no kör indeksinin model sınamaları onlarla gitti, kör indeksin kendisi
`test_kor_indeks.py`'de `shared.crypto` düzeyinde sınanır. Personelde unvan/branş yok, üye türü
ve ayrılış tarihi var; ad-soyad DB'de token'dır.
"""

from __future__ import annotations

from datetime import date

import pytest
from django.apps import apps as django_apps
from django.db import IntegrityError, connection

from apps.okul.models import (
    CanteenMode,
    MemberKind,
    Personnel,
    SchoolConfig,
    SchoolLevel,
    SchoolYear,
    SettlementType,
    StaffingMode,
)


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


class TestOgrenciTarafiYok:
    """Tasarım §5.1 ALMA, T5: öğrenci sicili, şube kataloğu ve hazırlık bayrağı göç 0014 ile düştü."""

    def test_ogrenci_ve_sube_modelleri_yoktur(self) -> None:
        for ad in ("Student", "ClassSection"):
            with pytest.raises(LookupError):
                django_apps.get_model("okul", ad)

    def test_okul_kartinda_hazirlik_bayragi_yoktur(self) -> None:
        alanlar = {alan.name for alan in SchoolConfig._meta.get_fields()}
        assert "has_prep_class" not in alanlar
        assert "has_prep_class" not in SchoolConfig.IZ_DEGER_ALANLARI
        assert "has_prep_class" not in SchoolConfig.IZ_OZET_ALANLARI
        assert not hasattr(SchoolConfig(), "grade_levels")


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

    def test_ad_soyad_db_de_duz_metin_durmaz(self) -> None:
        """F1 kod kapısı: ad-soyad sütunu ham SQL ile okununca token'dır, ad değil (§5.3)."""
        kisi = Personnel.objects.create(first_name="ÖRNEKAD", last_name="ÖRNEKSOYAD")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT first_name, last_name FROM okul_personnel WHERE id = %s", [kisi.pk]
            )
            ham_ad, ham_soyad = cursor.fetchone()
        for ham, duz in ((ham_ad, "ÖRNEKAD"), (ham_soyad, "ÖRNEKSOYAD")):
            assert duz not in ham
            assert ham.startswith("gAAAA")  # Fernet token'ı
        assert Personnel.objects.get(pk=kisi.pk).full_name == "ÖRNEKAD ÖRNEKSOYAD"

    def test_full_name(self) -> None:
        assert Personnel(first_name="EMRE CAN", last_name="YILMAZ").full_name == "EMRE CAN YILMAZ"

    def test_korunan_alan_listesi_ad_ve_soyadi_icerir(self) -> None:
        """Güvenlik ekranının "korunan alanlar" listesi koddan okunur (şifreli alanlar)."""
        from apps.okul.services import app_password

        etiketler = app_password.protected_field_labels()
        assert {"ad", "soyad"} <= set(etiketler)
        # Öğrenci sicili söküldü: okul numarası korunan alanlar arasında yoktur.
        assert "okul no" not in etiketler

    def test_ayrilis_tarihi_alani_var(self) -> None:
        kisi = Personnel.objects.create(first_name="A", last_name="B")
        assert kisi.left_at is None
