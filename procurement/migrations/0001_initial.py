# Generated by Django 4.2.16 on 2025-01-02 12:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gallery', '0002_alter_sku_suppliers_list_alter_spu_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_order_number', models.CharField(max_length=50, unique=True, verbose_name='采购单号')),
                ('purchase_date', models.DateField(verbose_name='采购日期')),
                ('status', models.IntegerField(choices=[(0, '草稿'), (1, '待下单'), (2, '待支付'), (3, '待入库'), (4, '已入库'), (5, '已取消')], default=0, verbose_name='采购状态')),
                ('expected_delivery_date', models.DateField(verbose_name='预计到货日期')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='总金额')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '采购单',
                'verbose_name_plural': '采购单',
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='供应商名称')),
                ('contact_info', models.CharField(max_length=100, verbose_name='联系方式')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '供应商',
                'verbose_name_plural': '供应商',
            },
        ),
        migrations.CreateModel(
            name='PurchaseOrderDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='采购数量')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='单价')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='金额')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='gallery.sku', verbose_name='产品')),
                ('purchase_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='procurement.purchaseorder', verbose_name='采购单')),
            ],
            options={
                'verbose_name': '采购单明细',
                'verbose_name_plural': '采购单明细',
            },
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='procurement.supplier', verbose_name='供应商'),
        ),
    ]