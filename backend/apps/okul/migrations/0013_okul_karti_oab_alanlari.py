# F1b-4 — okul kartının OAB alanları (tasarım §5.1 "`SchoolConfig`'e eklenen OAB alanları"; plan
# "F1b-4 uygulama kararları (07.11.2026)"): kurum kodu, kademeler (çok değerli), öğrenci mevcudu ve
# tarihi, yerleşim türü, kantin ve personel çalıştırma biçimi, kampüs işareti, açılış tarihi. Hiçbiri
# kişisel veri değildir, şifrelenmez.
#
# Veri dönüşümü: tek değerli `kademe` doluysa `levels = [kademe]` olur (ters yönde listenin ilk
# elemanı `kademe`'ye döner). Aile iskeletinden kalan `kisa_ad` (OAB'de hiçbir çıktıda
# kullanılmıyordu) ve `kutuphane_saatleri` (okunduğu ağ kataloğu F1a-2'de söküldü) düşer. Yeni
# alanlar var olan satırda boştur: kurulum kapısı yeniden kapanmaz, yol haritası "okul kartı"
# maddesini gösterir. Göçler F1b sonunda tek `0001_initial`'a iner (plan F1b-1 "Eski veri").

from typing import Any

import django.core.validators
import django.db.models.functions.text
import django.db.models.lookups
from django.db import migrations, models


def kademeyi_listeye_cevir(apps: Any, schema_editor: Any) -> None:
    """`kademe` dolu satırda `levels = [kademe]`; boş satırda liste boş kalır."""
    SchoolConfig = apps.get_model("okul", "SchoolConfig")
    for config in SchoolConfig.objects.exclude(kademe=""):
        config.levels = [config.kademe]
        config.save(update_fields=["levels"])


def listeyi_kademeye_cevir(apps: Any, schema_editor: Any) -> None:
    """Ters yön: listenin ilk elemanı `kademe` olur (eski alan tek değer taşır)."""
    SchoolConfig = apps.get_model("okul", "SchoolConfig")
    eski_degerler = {"ILKOKUL", "ORTAOKUL", "ORTAOGRETIM"}  # eski kısıtın kümesi
    for config in SchoolConfig.objects.all():
        kademeler = config.levels if isinstance(config.levels, list) else []
        ilk = next((k for k in kademeler if k in eski_degerler), "")
        if ilk:
            config.kademe = ilk
            config.save(update_fields=["kademe"])


class Migration(migrations.Migration):

    dependencies = [
        ('okul', '0012_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolconfig',
            name='canteen_mode',
            field=models.CharField(blank=True, choices=[('KIRAYA_VERILIYOR', 'Kiraya veriliyor'), ('BIRLIKCE_ISLETILIYOR', 'Birlikçe işletiliyor'), ('KANTIN_YOK', 'Kantin ve benzeri yer yok')], default='', max_length=32, verbose_name='kantin işletme biçimi'),
        ),
        migrations.AddField(
            model_name='schoolconfig',
            name='in_campus',
            field=models.BooleanField(default=False, verbose_name='eğitim kampüsünde'),
        ),
        migrations.AddField(
            model_name='schoolconfig',
            name='institution_code',
            field=models.CharField(blank=True, default='', max_length=6, verbose_name='kurum kodu'),
        ),
        migrations.AddField(
            model_name='schoolconfig',
            name='levels',
            field=models.JSONField(blank=True, default=list, verbose_name='kademeler'),
        ),
        migrations.AddField(
            model_name='schoolconfig',
            name='opened_on',
            field=models.DateField(blank=True, null=True, verbose_name='okulun açılış tarihi'),
        ),
        migrations.AddField(
            model_name='schoolconfig',
            name='settlement_type',
            field=models.CharField(blank=True, choices=[('BUYUKSEHIR', 'Büyükşehir statüsündeki il'), ('IL_MERKEZI_BUYUKSEHIR_DEGIL', 'Büyükşehir statüsünde olmayan il merkezi'), ('DIGER', 'Büyükşehir statüsünde olmayan ilde, il merkezi dışında')], default='', max_length=32, verbose_name='yerleşim türü'),
        ),
        migrations.AddField(
            model_name='schoolconfig',
            name='staffing_mode',
            field=models.CharField(blank=True, choices=[('DOGRUDAN_ISVEREN', 'Birlik doğrudan işveren'), ('HIZMET_ALIMI', 'Hizmet alımıyla'), ('CALISTIRMIYOR', 'Personel çalıştırmıyor')], default='', max_length=32, verbose_name='personel çalıştırma biçimi'),
        ),
        migrations.AddField(
            model_name='schoolconfig',
            name='student_count',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(99999)], verbose_name='öğrenci mevcudu'),
        ),
        migrations.AddField(
            model_name='schoolconfig',
            name='student_count_as_of',
            field=models.DateField(blank=True, null=True, verbose_name='mevcudun tarihi'),
        ),
        migrations.RunPython(kademeyi_listeye_cevir, listeyi_kademeye_cevir),
        migrations.RemoveConstraint(
            model_name='schoolconfig',
            name='ck_schoolconfig_kademe',
        ),
        migrations.RemoveField(
            model_name='schoolconfig',
            name='kademe',
        ),
        migrations.RemoveField(
            model_name='schoolconfig',
            name='kisa_ad',
        ),
        migrations.RemoveField(
            model_name='schoolconfig',
            name='kutuphane_saatleri',
        ),
        migrations.AddConstraint(
            model_name='schoolconfig',
            constraint=models.CheckConstraint(condition=models.Q(('settlement_type__in', ['BUYUKSEHIR', 'IL_MERKEZI_BUYUKSEHIR_DEGIL', 'DIGER', ''])), name='ck_schoolconfig_settlement_type'),
        ),
        migrations.AddConstraint(
            model_name='schoolconfig',
            constraint=models.CheckConstraint(condition=models.Q(('canteen_mode__in', ['KIRAYA_VERILIYOR', 'BIRLIKCE_ISLETILIYOR', 'KANTIN_YOK', ''])), name='ck_schoolconfig_canteen_mode'),
        ),
        migrations.AddConstraint(
            model_name='schoolconfig',
            constraint=models.CheckConstraint(condition=models.Q(('staffing_mode__in', ['DOGRUDAN_ISVEREN', 'HIZMET_ALIMI', 'CALISTIRMIYOR', ''])), name='ck_schoolconfig_staffing_mode'),
        ),
        migrations.AddConstraint(
            model_name='schoolconfig',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('student_count__isnull', True), ('student_count_as_of__isnull', True)), models.Q(('student_count__isnull', False), ('student_count_as_of__isnull', False)), _connector='OR'), name='ck_schoolconfig_student_count_pair'),
        ),
        migrations.AddConstraint(
            model_name='schoolconfig',
            constraint=models.CheckConstraint(condition=models.Q(('student_count__isnull', True), ('student_count__lte', 99999), _connector='OR'), name='ck_schoolconfig_student_count_max'),
        ),
        migrations.AddConstraint(
            model_name='schoolconfig',
            constraint=models.CheckConstraint(condition=models.Q(('institution_code', ''), django.db.models.lookups.Exact(django.db.models.functions.text.Length('institution_code'), 6), _connector='OR'), name='ck_schoolconfig_institution_code'),
        ),
    ]
