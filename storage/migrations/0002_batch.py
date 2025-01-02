# Generated by Django 4.2.16 on 2025-01-02 12:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0001_initial'),
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='批次ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('purchase_order_detail', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='procurement.purchaseorderdetail', verbose_name='采购明细')),
            ],
            options={
                'verbose_name': '批次信息',
                'verbose_name_plural': '批次信息列表',
                'db_table': 'storage_batch',
                'ordering': ['-created_at'],
            },
        ),
    ]