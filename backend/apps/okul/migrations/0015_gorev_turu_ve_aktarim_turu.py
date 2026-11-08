# F1b-5 — personelin görev türü üçlü olur, aktarım türleri tasarımın adlarını alır (tasarım §5.1
# `Personnel.member_kind`: öğretmen · yönetici · diğer; `ImportRun`: PERSONEL · VELI; §5 O8 Türkçe
# büyük harf ASCII; plan "F1b-5 uygulama kararları (08.11.2026)").
#
# Var olan değerler çevrilir: görev türünde TEACHER → OGRETMEN, STAFF → DIGER; aktarım türünde
# PERSONNEL → PERSONEL. Eski STUDENTS koşuları BİLEREK çevrilmez (models.ImportSourceType).
# Ters yön: OGRETMEN → TEACHER, DIGER → STAFF; eski kümede yönetici olmadığı için YONETICI →
# TEACHER (eski sınıflama müdürü ve müdür yardımcısını öğretmen sayıyordu); PERSONEL →
# PERSONNEL; VELI koşusu eski kümede yoktur, olduğu gibi kalır (o güne dek yazanı yoktur).
# Görev türünün veritabanı kısıtı çeviriden önce düşer, sonra yeni kümeyle kurulur.
# Göçler F1b sonunda tek `0001_initial`'a iner (plan F1b-1 "Eski veri").

from typing import Any

from django.db import migrations, models

_GOREV_ILERI = {"TEACHER": "OGRETMEN", "STAFF": "DIGER"}
_GOREV_GERI = {"OGRETMEN": "TEACHER", "YONETICI": "TEACHER", "DIGER": "STAFF"}
_AKTARIM_ILERI = {"PERSONNEL": "PERSONEL"}
_AKTARIM_GERI = {"PERSONEL": "PERSONNEL"}


def _cevir(apps: Any, gorev: dict[str, str], aktarim: dict[str, str]) -> None:
    # `update()` şifreli ad alanlarına dokunmaz (anahtar gerekmez; göç kilitliyken koşar).
    personel = apps.get_model("okul", "Personnel")
    for eski, yeni in gorev.items():
        personel._base_manager.filter(member_kind=eski).update(member_kind=yeni)
    kosu = apps.get_model("okul", "ImportRun")
    for eski, yeni in aktarim.items():
        kosu._base_manager.filter(source_type=eski).update(source_type=yeni)


def ileri(apps: Any, schema_editor: Any) -> None:
    _cevir(apps, _GOREV_ILERI, _AKTARIM_ILERI)


def geri(apps: Any, schema_editor: Any) -> None:
    _cevir(apps, _GOREV_GERI, _AKTARIM_GERI)


class Migration(migrations.Migration):
    dependencies = [
        ("okul", "0014_ogrenci_ve_sube_sokumu"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="personnel",
            name="ck_personnel_member_kind",
        ),
        migrations.AlterField(
            model_name="personnel",
            name="member_kind",
            field=models.CharField(
                choices=[
                    ("OGRETMEN", "öğretmen"),
                    ("YONETICI", "yönetici"),
                    ("DIGER", "diğer personel"),
                ],
                default="OGRETMEN",
                max_length=16,
                verbose_name="görev türü",
            ),
        ),
        migrations.AlterField(
            model_name="importrun",
            name="source_type",
            field=models.CharField(
                choices=[("PERSONEL", "Personel"), ("VELI", "Veli listesi")],
                db_index=True,
                max_length=16,
                verbose_name="kaynak türü",
            ),
        ),
        migrations.RunPython(ileri, geri),
        migrations.AddConstraint(
            model_name="personnel",
            constraint=models.CheckConstraint(
                condition=models.Q(("member_kind__in", ["OGRETMEN", "YONETICI", "DIGER"])),
                name="ck_personnel_member_kind",
            ),
        ),
    ]
