from django.db import models
from django.utils import timezone
from gallery.models import SKU


class Supplier(models.Model):
    """供应商信息表"""
    name = models.CharField('供应商名称', max_length=100)
    contact_info = models.CharField('联系方式', max_length=100)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '供应商'
        verbose_name_plural = verbose_name


class PurchaseOrder(models.Model):
    """采购单主表"""
    class Status(models.IntegerChoices):
        DRAFT = 0, '草稿'
        PENDING_ORDER = 1, '待下单'
        PENDING_PAYMENT = 2, '待支付'
        PENDING_STORAGE = 3, '待入库'
        STORED = 4, '已入库'
        CANCELLED = 5, '已取消'

    purchase_order_number = models.CharField('采购单号', max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, verbose_name='供应商')
    warehouse = models.ForeignKey('storage.Warehouse', on_delete=models.PROTECT, null=True, blank=True, verbose_name='仓库')
    purchase_date = models.DateField('采购日期')
    status = models.IntegerField('采购状态', choices=Status.choices, default=Status.DRAFT)
    expected_delivery_date = models.DateField('预计到货日期')
    total_amount = models.DecimalField('总金额', max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return self.purchase_order_number

    class Meta:
        verbose_name = '采购单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']


class PurchaseOrderDetail(models.Model):
    """采购单明细表"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, verbose_name='采购单')
    product = models.ForeignKey(SKU, on_delete=models.PROTECT, verbose_name='产品')
    quantity = models.DecimalField('采购数量', max_digits=10, decimal_places=2)
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    amount = models.DecimalField('金额', max_digits=10, decimal_places=2)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def save(self, *args, **kwargs):
        # 计算金额
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # 更新采购单总金额
        total = self.purchase_order.purchaseorderdetail_set.aggregate(
            total=models.Sum('amount'))['total'] or 0
        self.purchase_order.total_amount = total
        self.purchase_order.save()

    def __str__(self):
        return f"{self.purchase_order.purchase_order_number} - {self.product.name}"

    class Meta:
        verbose_name = '采购单明细'
        verbose_name_plural = verbose_name
