# Generated by Django 4.2.16 on 2024-12-30 16:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gallery', '0002_alter_sku_suppliers_list_alter_spu_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='店铺名称')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='店铺编码')),
                ('platform', models.CharField(choices=[('SHOPIFY', 'Shopify'), ('AMAZON', 'Amazon'), ('EBAY', 'eBay'), ('WALMART', 'Walmart'), ('OTHER', '其他')], max_length=20, verbose_name='平台')),
                ('is_active', models.BooleanField(default=True, verbose_name='启用状态')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '店铺',
                'verbose_name_plural': '店铺',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_no', models.CharField(max_length=64, unique=True)),
                ('platform_order_no', models.CharField(max_length=64)),
                ('status', models.CharField(choices=[('pending', '待处理'), ('processing', '处理中'), ('shipped', '已发货'), ('completed', '已完成'), ('cancelled', '已取消')], default='pending', max_length=32)),
                ('recipient_country', models.CharField(max_length=64)),
                ('recipient_state', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('paid_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('freight', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('recipient_name', models.CharField(max_length=100)),
                ('recipient_phone', models.CharField(max_length=20)),
                ('recipient_email', models.EmailField(max_length=254)),
                ('recipient_city', models.CharField(max_length=50)),
                ('recipient_address', models.CharField(max_length=100)),
                ('system_remark', models.TextField(blank=True, default='', verbose_name='系统备注')),
                ('cs_remark', models.TextField(blank=True, default='', verbose_name='客服备注')),
                ('buyer_remark', models.TextField(blank=True, default='', verbose_name='买家备注')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trade.shop')),
            ],
            options={
                'verbose_name': '订单',
                'verbose_name_plural': '订单',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('qty', models.IntegerField(default=1, verbose_name='数量')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='售价')),
                ('cost', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='成本')),
                ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='折扣')),
                ('actual_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='实际售价')),
                ('is_out_of_stock', models.BooleanField(default=False, verbose_name='缺货状态')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trade.order', verbose_name='订单')),
                ('sku', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='gallery.sku', verbose_name='SKU')),
            ],
            options={
                'verbose_name': '购物车',
                'verbose_name_plural': '购物车',
                'ordering': ['-created_at'],
            },
        ),
    ]
