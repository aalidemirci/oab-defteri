# Hesap ↔ üyelik bağı (plan F1c 7. adım; tasarım §4.6.1 `Account.person`, `membership`, `term`).
# Göç grafiği `okul.0002+ -> oab.000x` (plan "F1c adımları"): yabancı anahtarlar dizeyledir, `okul`
# `oab`'yi içe aktarmaz. Boş olabilen, varsayılansız sütunlar `ALTER TABLE ADD COLUMN` ile eklenir;
# hesap tablosunda tetikleyici yoktur, denetim izinin tablosuna dokunulmaz. Kısıt yalnız `KAPALI`
# olmayan bağlı satırlarda geçerli kısmi tekil dizindir. Veri göçü yoktur (plan "F1c uygulama
# kararları": F1b deneme kurulumları F1c sürümüyle açılmaz; içerik MAC'inin yeniden kurulması F4).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oab', '0004_uyelik_iptal_ve_pay_dagitim'),
        ('okul', '0003_parentroster_term'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='membership',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='oab.organmembership', verbose_name='organ üyeliği'),
        ),
        migrations.AddField(
            model_name='account',
            name='person',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='oab.oabperson', verbose_name='birlik kişisi'),
        ),
        migrations.AddField(
            model_name='account',
            name='term',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='oab.oabterm', verbose_name='birlik dönemi'),
        ),
        migrations.AddConstraint(
            model_name='account',
            constraint=models.UniqueConstraint(condition=models.Q(('membership__isnull', False), models.Q(('status', 'KAPALI'), _negated=True)), fields=('membership',), name='uq_account_membership_open'),
        ),
    ]
