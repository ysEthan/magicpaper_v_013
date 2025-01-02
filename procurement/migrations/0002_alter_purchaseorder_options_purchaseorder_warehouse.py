# Generated by Django 4.2.16 on 2025-01-02 14:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_batch'),
        ('procurement', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='purchaseorder',
            options={'ordering': ['-created_at'], 'verbose_name': '采购单', 'verbose_name_plural': '采购单'},
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='warehouse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='storage.warehouse', verbose_name='仓库'),
        ),
    ]
