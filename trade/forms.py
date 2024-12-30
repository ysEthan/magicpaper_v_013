from django import forms
from django.db.models import Max
from .models import Order, Shop

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_no', 'platform_order_no', 'shop', 'order_type',
            'recipient_country', 'recipient_state', 'recipient_city', 'recipient_address',
            'recipient_name', 'recipient_phone', 'recipient_email', 'recipient_postcode',
            'paid_amount', 'freight',
            'system_remark', 'cs_remark', 'buyer_remark'
        ]
        widgets = {
            'order_type': forms.Select(attrs={'class': 'form-select'}),
            'shop': forms.Select(attrs={'class': 'form-select'}),
            'system_remark': forms.TextInput(attrs={'class': 'form-control'}),
            'cs_remark': forms.TextInput(attrs={'class': 'form-control'}),
            'buyer_remark': forms.TextInput(attrs={'class': 'form-control'}),
            'order_no': forms.TextInput(attrs={'readonly': 'readonly'}),
            'platform_order_no': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置字段是否必填
        self.fields['recipient_email'].required = False
        self.fields['recipient_postcode'].required = False  # 邮编设为非必填
        self.fields['system_remark'].required = False
        self.fields['cs_remark'].required = False
        self.fields['buyer_remark'].required = False
        
        # 添加字段的帮助文本
        self.fields['order_type'].help_text = '选择订单的来源类型'
        
        # 从选项中移除平台订单类型
        choices = [choice for choice in Order.OrderType.choices if choice[0] != Order.OrderType.PLATFORM]
        self.fields['order_type'].choices = choices
        
        # 设置初始值
        if not self.instance.pk:  # 如果是新建订单
            # 生成初始订单号
            initial_order_no = self.generate_order_no(Order.OrderType.INFLUENCER)
            self.fields['order_no'].initial = initial_order_no
            self.fields['platform_order_no'].initial = initial_order_no  # 平台订单号与订单号保持一致
            self.fields['order_type'].initial = Order.OrderType.INFLUENCER  # 将默认值改为达人订单

    def save(self, commit=True):
        instance = super().save(commit=False)
        # 设置订单状态为待处理
        instance.status = Order.OrderStatus.PENDING
        if commit:
            instance.save()
        return instance

    def generate_order_no(self, order_type):
        """根据订单类型生成订单号"""
        from datetime import datetime
        
        # 获取当前日期作为前缀
        date_prefix = datetime.now().strftime('%Y%m%d')
        
        # 根据订单类型设置不同的类型前缀
        type_prefix = {
            Order.OrderType.INFLUENCER: 'DR',  # 达人订单
            Order.OrderType.OFFLINE: 'OF',     # 线下订单
            Order.OrderType.EMPLOYEE: 'EP',    # 员工自购
        }.get(order_type, 'XX')
        
        # 查询当天最大的订单号
        prefix = f"{type_prefix}{date_prefix}"
        max_order = Order.objects.filter(
            order_no__startswith=prefix
        ).aggregate(Max('order_no'))['order_no__max']
        
        # 如果当天没有订单，从1开始；否则递增
        if not max_order:
            sequence = '001'
        else:
            last_sequence = int(max_order[-3:])
            sequence = f"{last_sequence + 1:03d}"
            
        return f"{prefix}{sequence}" 