"""Çözülemeyen şifreli alan uçtan uca (tasarım TK8 (3), §13 D48; plan F1b-1 "Denetim izi").

Program dışından SQLite'ta şifreli sütuna düz metin yazılır ya da başka bir DEK'in
token'ı taşınır: kilit açıkken alan `CorruptField` olarak okunur, API'de `null` gelir
ve kayıtta `bozuk_alanlar` listesi durur; arama ve eşleme kaydı dışarıda bırakır;
kayıt yeniden kaydedilince ham değer aynen kalır (işaret şifrelenip meşru veriye
dönmez); güvenlik durumu bozuk alan sayısını bildirir. Alan birimi testleri
(`test_from_db_value_kati_kip`) `shared/tests/test_crypto.py`'dedir.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.db import connection
from rest_framework.test import APIClient

from apps.okul import name_match, selectors
from apps.okul.models import Personnel, Student
from apps.okul.serializers import PersonnelSerializer, StudentSerializer
from apps.okul.services import app_password
from conftest import oturumu_ac_test
from shared import crypto

pytestmark = pytest.mark.django_db


def _ham_yaz(tablo: str, pk: int, **alanlar: str) -> None:
    """Program dışından yazım taklidi: şifreli sütuna ham değer (ORM'siz)."""
    atamalar = ", ".join(f"{ad} = %s" for ad in alanlar)
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {tablo} SET {atamalar} WHERE id = %s",  # noqa: S608 — test, sabit adlar
            [*alanlar.values(), pk],
        )


def _ham_oku(tablo: str, pk: int, alan: str) -> str:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {alan} FROM {tablo} WHERE id = %s", [pk])  # noqa: S608
        (deger,) = cursor.fetchone()
    return str(deger)


@pytest.fixture
def bozuk_personel() -> Personnel:
    kisi = Personnel.objects.create(first_name="AYŞE", last_name="KAYA")
    _ham_yaz("okul_personnel", kisi.pk, first_name="AYŞE")  # düz metin sızdı
    okunan: Personnel = Personnel.objects.get(pk=kisi.pk)
    return okunan


def test_duz_metin_okunmaz_isaret_doner(bozuk_personel: Personnel) -> None:
    assert crypto.is_corrupt(bozuk_personel.first_name)
    assert bozuk_personel.last_name == "KAYA"
    assert crypto.corrupt_fields_of(bozuk_personel) == ["first_name"]
    assert "AYŞE" not in bozuk_personel.full_name  # işaret ad birleştirmede boş kalır


def test_baska_dekin_tokeni_okunmaz() -> None:
    kisi = Personnel.objects.create(first_name="ALİ", last_name="CAN")
    crypto.load_key(b"\x07" * 32)
    yabanci = Personnel._meta.get_field("first_name").get_prep_value("VELİ")
    app_password.lock()
    oturumu_ac_test()
    _ham_yaz("okul_personnel", kisi.pk, first_name=str(yabanci))
    assert crypto.is_corrupt(Personnel.objects.get(pk=kisi.pk).first_name)


def test_kaydedilince_ham_deger_aynen_kalir(bozuk_personel: Personnel) -> None:
    bozuk_personel.member_kind = "STAFF"
    bozuk_personel.save()  # update_fields'siz tam kayıt
    assert _ham_oku("okul_personnel", bozuk_personel.pk, "first_name") == "AYŞE"
    bozuk_personel.full_clean()  # temizleme işareti "" yapmaz
    assert crypto.is_corrupt(bozuk_personel.first_name)


def test_ogrenci_kor_indeksi_bozuk_okul_nodan_hesaplanmaz() -> None:
    ogrenci = Student.objects.create(first_name="EMRE", last_name="CAN", student_number="101")
    indeks = ogrenci.student_number_index
    _ham_yaz("okul_student", ogrenci.pk, student_number="101")  # düz metin
    okunan = Student.objects.get(pk=ogrenci.pk)
    assert crypto.is_corrupt(okunan.student_number)
    okunan.save()
    assert Student.objects.get(pk=ogrenci.pk).student_number_index == indeks
    assert _ham_oku("okul_student", ogrenci.pk, "student_number") == "101"


def test_api_alani_null_verir_ve_bozuk_alanlari_listeler(bozuk_personel: Personnel) -> None:
    veri: dict[str, Any] = dict(PersonnelSerializer(bozuk_personel).data)
    assert veri["first_name"] is None and veri["full_name"] is None
    assert veri["last_name"] == "KAYA"
    assert veri["bozuk_alanlar"] == ["first_name"]

    saglam = Personnel.objects.create(first_name="ZEYNEP", last_name="AK")
    assert PersonnelSerializer(saglam).data["bozuk_alanlar"] == []

    yanit = APIClient().get(f"/api/v1/personnel/{bozuk_personel.pk}/")
    assert yanit.status_code == 200
    assert yanit.json()["first_name"] is None and "AYŞE" not in yanit.content.decode()


def test_ogrenci_serializeri_da_isaretler() -> None:
    ogrenci = Student.objects.create(first_name="EMRE", last_name="CAN", student_number="7")
    _ham_yaz("okul_student", ogrenci.pk, student_number="7")
    veri = StudentSerializer(Student.objects.get(pk=ogrenci.pk)).data
    assert veri["student_number"] is None and veri["full_name"] == "EMRE CAN"
    assert veri["bozuk_alanlar"] == ["student_number"]


def test_arama_ve_siralama_bozuk_kaydi_disarida_birakir(bozuk_personel: Personnel) -> None:
    Personnel.objects.create(first_name="AHMET", last_name="KAYA")
    bulunan = selectors.personnel_list(search="kaya")
    assert [p.first_name for p in bulunan] == ["AHMET"]  # bozuk kayıt sağlam soyadıyla bulunmaz
    assert len(selectors.personnel_sorted()) == 2  # listede durur, sıralama patlamaz

    ogrenci = Student.objects.create(first_name="EMRE", last_name="CAN", student_number="9")
    _ham_yaz("okul_student", ogrenci.pk, first_name="EMRE")
    assert selectors.student_list(search="can") == []
    assert selectors.student_list(search="9") == []


def test_olasi_ayni_kisi_bozuk_kaydi_onermez(bozuk_personel: Personnel) -> None:
    from django.utils import timezone

    bozuk_personel.leave_candidate_since = timezone.localdate()
    bozuk_personel.save(update_fields=["leave_candidate_since"])
    Personnel.objects.create(first_name="AYŞE", last_name="KAYA")  # aynı adla yeni kayıt
    havuz = selectors.leave_pool_personnel()
    assert selectors.leave_pool_similar_personnel(havuz) == {}


def test_ad_eslestirme_metin_olmayan_girdide_eslesmez() -> None:
    isaret = crypto.CorruptField("AYŞE")
    assert (
        name_match.match_reason(first_a=isaret, full_a="KAYA", first_b="AYŞE", full_b="AYŞE KAYA")  # type: ignore[arg-type]
        is None
    )
    assert name_match.name_key(isaret) == ""  # type: ignore[arg-type]


def test_durum_bozuk_alan_sayisini_bildirir(bozuk_personel: Personnel) -> None:
    durum = app_password.status()
    assert durum["corrupt_field_count"] == 1
    assert crypto.corrupt_reads() == [("okul.Personnel", str(bozuk_personel.pk), "first_name")]
