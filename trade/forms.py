from django import forms
from django.db.models import Max
from .models import Order, Shop
from django.utils import timezone

class OrderForm(forms.ModelForm):
    order_type = forms.ChoiceField(
        label='订单类型',
        choices=[
            ('influencer', '达人订单'),
            ('offline', '线下订单'),
            ('employee', '员工自购'),
        ],
        help_text='订单来源类型'
    )

    class Meta:
        model = Order
        fields = [
            'order_type', 'order_no', 'platform_order_no', 'shop',
            'recipient_name', 'recipient_phone', 'recipient_email',
            'recipient_country', 'recipient_state', 'recipient_city',
            'recipient_address', 'recipient_postcode',
            'paid_amount', 'freight',
            'system_remark', 'cs_remark', 'buyer_remark'
        ]
        widgets = {
            'system_remark': forms.TextInput(attrs={'class': 'form-control'}),
            'cs_remark': forms.TextInput(attrs={'class': 'form-control'}),
            'buyer_remark': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置店铺默认值
        if not self.instance.pk:  # 只在创建新订单时设置默认值
            self.initial['shop'] = 1
            # 设置默认订单类型为达人订单并生成订单号
            self.initial['order_type'] = 'influencer'
            self.initial['order_no'] = self.generate_order_no('influencer')

    def generate_order_no(self, order_type):
        """生成订单号"""
        today = timezone.now().strftime('%Y%m%d')
        prefix_map = {
            'platform': 'PL',
            'influencer': 'IN',
            'offline': 'OF',
            'employee': 'EM'
        }
        prefix = prefix_map.get(order_type, 'X')
        
        # 查找今天最大的订单号
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timezone.timedelta(days=1)
        latest_order = Order.objects.filter(
            created_at__gte=today_start,
            created_at__lt=today_end,
            order_no__startswith=f"{prefix}{today}"
        ).order_by('-order_no').first()
        
        if latest_order:
            # 提取序号并加1
            seq = int(latest_order.order_no[-4:]) + 1
        else:
            seq = 1
            
        # 生成新的订单号
        return f"{prefix}{today}{seq:04d}" 