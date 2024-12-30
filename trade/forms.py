from django import forms
from .models import Order, Shop

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_no', 'platform_order_no', 'shop', 'order_type', 'status',
            'recipient_country', 'recipient_state', 'recipient_city', 'recipient_address',
            'recipient_name', 'recipient_phone', 'recipient_email',
            'paid_amount', 'freight',
            'system_remark', 'cs_remark', 'buyer_remark'
        ]
        widgets = {
            'order_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'shop': forms.Select(attrs={'class': 'form-select'}),
            'system_remark': forms.Textarea(attrs={'rows': 3}),
            'cs_remark': forms.Textarea(attrs={'rows': 3}),
            'buyer_remark': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置字段是否必填
        self.fields['recipient_email'].required = False
        self.fields['system_remark'].required = False
        self.fields['cs_remark'].required = False
        self.fields['buyer_remark'].required = False
        
        # 添加字段的帮助文本
        self.fields['order_type'].help_text = '选择订单的来源类型'
        
        # 设置初始值
        if not self.instance.pk:  # 如果是新建订单
            self.fields['status'].initial = Order.OrderStatus.PENDING
            self.fields['order_type'].initial = Order.OrderType.PLATFORM 