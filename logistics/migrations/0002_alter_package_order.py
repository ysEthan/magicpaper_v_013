# Generated by Django 4.2.16 on 2024-12-30 17:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trade', '0001_initial'),
        ('logistics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='order',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='package', to='trade.order', verbose_name='订单'),
        ),
    ]