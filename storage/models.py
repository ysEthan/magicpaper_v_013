from django.db import models
from django.core.validators import MinValueValidator
from gallery.models import SKU
from procurement.models import PurchaseOrderDetail

class Warehouse(models.Model):
    """仓库模型"""
    
    id = models.AutoField(
        primary_key=True,
        verbose_name='仓库ID'
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name='仓库名称'
    )
    
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='仓库地址'
    )
    
    contact = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='联系人'
    )
    
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='联系电话'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )

    class Meta:
        db_table = 'storage_warehouse'
        verbose_name = '仓库'
        verbose_name_plural = '仓库列表'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Batch(models.Model):
    """批次信息表"""
    
    id = models.AutoField(
        primary_key=True,
        verbose_name='批次ID'
    )
    
    purchase_order_detail = models.ForeignKey(
        PurchaseOrderDetail,
        on_delete=models.PROTECT,
        verbose_name='采购明细'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )

    class Meta:
        db_table = 'storage_batch'
        verbose_name = '批次信息'
        verbose_name_plural = '批次信息列表'
        ordering = ['-created_at']

    def __str__(self):
        return f"批次{self.id} - {self.purchase_order_detail.purchase_order.purchase_order_number}"

    @property
    def purchase_date(self):
        """获取采购日期"""
        return self.purchase_order_detail.purchase_order.purchase_date

    @property
    def supplier(self):
        """获取供应商"""
        return self.purchase_order_detail.purchase_order.supplier

    @property
    def cost(self):
        """获取采购成本"""
        return self.purchase_order_detail.unit_price

class Allocation(models.Model):
    """货区货位模型"""
    
    class AreaType(models.TextChoices):
        NORMAL = 'NORMAL', '普通区'
        CONSUMABLE = 'CONSUMABLE', '耗材区'
        REQUISITION = 'REQUISITION', '领用区'
    
    warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.CASCADE,
        verbose_name='所属仓库'
    )
    
    area_code = models.CharField(
        max_length=10,
        verbose_name='货区编码'
    )
    
    area_name = models.CharField(
        max_length=20,
        verbose_name='货区名称'
    )
    
    area_type = models.CharField(
        max_length=20,
        choices=AreaType.choices,
        default=AreaType.NORMAL,
        verbose_name='货区类型'
    )
    
    location_code = models.CharField(
        max_length=10,
        verbose_name='货位编码'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )

    class Meta:
        db_table = 'storage_allocation'
        verbose_name = '货区货位'
        verbose_name_plural = '货区货位列表'
        ordering = ['warehouse', 'area_code', 'location_code']
        unique_together = ['warehouse', 'area_code', 'location_code']

    def __str__(self):
        return f"{self.warehouse.name} - {self.area_name} - {self.location_code}"

class Stock(models.Model):
    """库存模型"""
    
    id = models.AutoField(
        primary_key=True,
        verbose_name='库存ID'
    )
    
    stock_num = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='库存数量'
    )
    
    warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.CASCADE,
        verbose_name='所属仓库'
    )
    
    avg_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name='平均成本'
    )
    
    sku = models.ForeignKey(
        SKU,
        on_delete=models.CASCADE,
        verbose_name='关联SKU'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )

    class Meta:
        db_table = 'storage_stock'
        verbose_name = '库存'
        verbose_name_plural = '库存列表'
        ordering = ['-updated_at']
        unique_together = ['warehouse', 'sku']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['warehouse']),
        ]

    def __str__(self):
        return f"{self.warehouse.name} - {self.sku.sku_code} - {self.stock_num}"
