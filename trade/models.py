from django.db import models
from django.utils.translation import gettext_lazy as _

class Shop(models.Model):
    PLATFORM_CHOICES = (
        ('SHOPIFY', 'Shopify'),
        ('AMAZON', 'Amazon'),
        ('EBAY', 'eBay'),
        ('WALMART', 'Walmart'),
        ('OTHER', '其他'),
    )

    id = models.AutoField('ID', primary_key=True)
    name = models.CharField('店铺名称', max_length=100)
    code = models.CharField('店铺编码', max_length=50, unique=True)
    platform = models.CharField('平台', max_length=20, choices=PLATFORM_CHOICES)
    is_active = models.BooleanField('启用状态', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '店铺'
        verbose_name_plural = '店铺'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', _('待处理')
        PROCESSING = 'processing', _('处理中')
        SHIPPED = 'shipped', _('已发货')
        COMPLETED = 'completed', _('已完成')
        CANCELLED = 'cancelled', _('已取消')
    
    order_no = models.CharField(max_length=64, unique=True)
    platform_order_no = models.CharField(max_length=64)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=32,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    recipient_country = models.CharField(max_length=64)
    recipient_state = models.CharField(max_length=64)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)
    recipient_email = models.EmailField()
    recipient_city = models.CharField(max_length=50)
    recipient_address = models.CharField(max_length=100)
    system_remark = models.TextField('系统备注', blank=True, default='')
    cs_remark = models.TextField('客服备注', blank=True, default='')
    buyer_remark = models.TextField('买家备注', blank=True, default='')

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = '订单'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_no}"

    def get_sku_stats(self):
        """获取SKU统计信息"""
        sku_count = self.cart_set.count()  # SKU种类数
        total_qty = sum(cart.qty for cart in self.cart_set.all())  # SKU总数量
        return {
            'sku_count': sku_count,
            'total_qty': total_qty
        }

class Cart(models.Model):
    id = models.AutoField('ID', primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        verbose_name='订单'
    )
    sku = models.ForeignKey(
        'gallery.SKU',
        on_delete=models.PROTECT,
        verbose_name='SKU'
    )
    qty = models.IntegerField(
        '数量',
        default=1
    )
    price = models.DecimalField(
        '售价',
        max_digits=10,
        decimal_places=2
    )
    cost = models.DecimalField(
        '成本',
        max_digits=10,
        decimal_places=2
    )
    discount = models.DecimalField(
        '折扣',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    actual_price = models.DecimalField(
        '实际售价',
        max_digits=10,
        decimal_places=2
    )
    is_out_of_stock = models.BooleanField(
        '缺货状态',
        default=False
    )
    created_at = models.DateTimeField(
        '创建时间',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        '更新时间',
        auto_now=True
    )

    class Meta:
        verbose_name = '购物车'
        verbose_name_plural = '购物车'
        ordering = ['-created_at']

    def __str__(self):
        return f"订单 {self.order.order_no} - {self.sku.sku_code}"
