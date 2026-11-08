# F1b-5 — veli listesi (`ParentRoster`) ve okul kartının veri sorumlusu alanı (tasarım §5.1
# `ParentRoster`, §8.4, E04; plan "F1b-5 uygulama kararları (08.11.2026)").
#
# `ParentRoster` F1b alanlarıyla kurulur: aktarım partisi, şifreli veli adı, adın kör indeksi,
# öğrencinin sınıfı. Birlik dönemi bağı (`term`) F1c'de, katılım işaretleri (`attended_*`) F2'de
# göçle eklenir. `SchoolConfig.data_controller_text` boş başlar (isteğe bağlı alan; kurulum
# kapısı yeniden kapanmaz). Çevrilecek var olan değer yoktur. Ters yön tabloyu ve sütunu düşürür
# (veli satırları ters göçte kaybolur; göç öncesi yedek masaüstü kabuğunca alınır).
# Göçler F1b sonunda tek `0001_initial`'a iner (plan F1b-1 "Eski veri").

import django.db.models.deletion
from django.db import migrations, models

import shared.crypto


class Migration(migrations.Migration):
    dependencies = [
        ("okul", "0015_gorev_turu_ve_aktarim_turu"),
    ]

    operations = [
        migrations.AddField(
            model_name="schoolconfig",
            name="data_controller_text",
            field=models.CharField(
                blank=True, default="", max_length=500, verbose_name="veri sorumlusu"
            ),
        ),
        migrations.CreateModel(
            name="ParentRoster",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "full_name",
                    shared.crypto.EncryptedCharField(
                        max_length=200, verbose_name="veli adı-soyadı"
                    ),
                ),
                (
                    "name_index",
                    models.CharField(
                        blank=True,
                        default="",
                        editable=False,
                        max_length=64,
                        verbose_name="veli adı kör indeksi",
                    ),
                ),
                (
                    "student_class",
                    models.CharField(max_length=16, verbose_name="öğrencinin sınıfı"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="oluşturulma"),
                ),
                (
                    "import_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="okul.importrun",
                        verbose_name="aktarım partisi",
                    ),
                ),
            ],
            options={
                "verbose_name": "veli listesi satırı",
                "verbose_name_plural": "veli listesi",
                "ordering": ["student_class", "pk"],
                "indexes": [
                    models.Index(fields=["student_class"], name="okul_parentroster_class_idx"),
                    models.Index(fields=["name_index"], name="okul_parentroster_name_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("student_class", ""), _negated=True),
                        name="ck_parentroster_student_class",
                    )
                ],
            },
        ),
    ]
