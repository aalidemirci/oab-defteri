# F1b-5 — öğrenci sicili, şube kataloğu ve hazırlık sınıfı bayrağı düşer (tasarım §5.1: `Student`
# ve `ClassSection` ALMA; T5: e-Okul'dan öğrenci alınmaz, veli listesi okulun şablonundan gelir).
# Plan "F1b-5 uygulama kararları (08.11.2026)": düz göç — gerçek öğrenci verisi aktarılmış bir
# kurulum yoktur (kullanıcı); açılıştaki göç olayı iz olarak yeter. Tabloların satırları şifreli
# kişi verisi taşıyabildiği için ters yön verisiz tablo kurar (eski satırlar geri gelmez).
# Göçler F1b sonunda tek `0001_initial`'a iner (plan F1b-1 "Eski veri").

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("okul", "0013_okul_karti_oab_alanlari"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Student",
        ),
        migrations.DeleteModel(
            name="ClassSection",
        ),
        migrations.RemoveField(
            model_name="schoolconfig",
            name="has_prep_class",
        ),
    ]
