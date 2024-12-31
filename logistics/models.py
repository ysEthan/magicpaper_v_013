from django.db import models
from trade.models import Order


class Carrier(models.Model):
    """物流商模型"""
    id = models.AutoField('ID', primary_key=True)
    name_zh = models.CharField('中文名称', max_length=25)
    name_en = models.CharField('英文名称', max_length=25)
    code = models.CharField('物流商代码', max_length=10, unique=True)
    url = models.URLField('官网地址', blank=True)
    contact = models.CharField('联系电话', max_length=20, blank=True)
    key = models.IntegerField('查询代码', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '物流商'
        verbose_name_plural = '物流商'
        ordering = ['name_zh']
        db_table = 'logistics_carrier'

    def __str__(self):
        return f"{self.name_zh} ({self.name_en})"


class Service(models.Model):
    """物流服务模型"""
    id = models.AutoField('ID', primary_key=True)
    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.CASCADE,
        verbose_name='物流商'
    )
    service_name = models.CharField('服务名称', max_length=25)
    service_code = models.CharField('服务代码', max_length=10)
    service_type = models.IntegerField('服务类型')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '物流服务'
        verbose_name_plural = '物流服务'
        ordering = ['carrier', 'service_name']
        db_table = 'logistics_service'
        unique_together = ['carrier', 'service_code']  # 确保同一物流商下服务代码唯一

    def __str__(self):
        return f"{self.carrier.name_zh} - {self.service_name}"


class Package(models.Model):
    """包裹模型"""
    id = models.AutoField('ID', primary_key=True)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        verbose_name='订单',
        related_name='package'
    )
    warehouse = models.ForeignKey(
        'storage.Warehouse',
        on_delete=models.PROTECT,
        verbose_name='发货仓库',
        null=True,
        blank=True
    )
    tracking_no = models.CharField(
        '跟踪号',
        max_length=30,
        blank=True,
        null=True
    )
    pkg_status_code = models.CharField(
        '包裹状态码',
        max_length=4,
        default='0'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,  # 使用PROTECT避免误删除物流服务
        verbose_name='物流服务'
    )
    items = models.JSONField(
        '商品列表',
        help_text='包含SKU、品名、包裹尺寸、重量等信息'
    )
    shipping_fee = models.DecimalField(
        '运费',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '包裹'
        verbose_name_plural = '包裹'
        ordering = ['-created_at']
        db_table = 'logistics_package'

    def __str__(self):
        return f"包裹 {self.id} - {self.tracking_no or '未获取跟踪号'}"

    @property
    def carrier_name(self):
        """获取物流商名称"""
        return self.service.carrier.name_zh if self.service else ''

    @property
    def service_name(self):
        """获取服务名称"""
        return self.service.service_name if self.service else ''
