from django import forms
from django.core.exceptions import ValidationError
from .models import Category, SPU, SKU
import json

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name_en', 'category_name_zh', 'description', 
                 'image', 'parent', 'rank_id', 'level', 'is_last_level', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        } 

class SPUForm(forms.ModelForm):
    class Meta:
        model = SPU
        fields = ['spu_code', 'spu_name', 'product_type', 'spu_remark', 
                 'sales_channel', 'brand', 'poc', 'category', 'status']
        widgets = {
            'spu_code': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'spu_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'product_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'sales_channel': forms.TextInput(attrs={'class': 'form-control'}),
            'spu_remark': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'poc': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        } 

class SKUForm(forms.ModelForm):
    class Meta:
        model = SKU
        fields = ['sku_code', 'sku_name', 'spu', 'material', 'color', 
                 'plating_process', 'surface_treatment', 'weight', 
                 'length', 'width', 'height', 'other_dimensions', 
                 'suppliers_list', 'img_url', 'status']
        widgets = {
            'sku_code': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'sku_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'spu': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'material': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'plating_process': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'surface_treatment': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'length': forms.NumberInput(attrs={'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control'}),
            'other_dimensions': forms.TextInput(attrs={'class': 'form-control'}),
            'suppliers_list': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': '请输入供应商列表，默认为空数组 []'
            }),
            'img_url': forms.URLInput(attrs={'class': 'form-control'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        error_messages = {
            'sku_code': {
                'required': 'SKU编码不能为空',
                'unique': '该SKU编码已存在'
            },
            'sku_name': {
                'required': 'SKU名称不能为空'
            },
            'spu': {
                'required': '请选择或创建SPU'
            },
            'material': {
                'required': '请选择材质'
            },
            'color': {
                'required': '请选择颜色'
            },
            'plating_process': {
                'required': '请选择电镀工艺'
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置suppliers_list为非必填
        self.fields['suppliers_list'].required = False
        # 设置spu字段为非必填，因为在新建SPU时会后续设置
        self.fields['spu'].required = False
        # 为suppliers_list字段设置默认值
        if not self.instance.pk and not self.initial.get('suppliers_list'):
            self.initial['suppliers_list'] = '[]'

    def clean_suppliers_list(self):
        suppliers_list = self.cleaned_data.get('suppliers_list')
        if not suppliers_list or suppliers_list.strip() == '':
            return '[]'
        try:
            suppliers_data = json.loads(suppliers_list)
            if not isinstance(suppliers_data, list):
                raise ValidationError('供应商列表必须是JSON数组格式')
            return suppliers_list
        except json.JSONDecodeError:
            raise ValidationError('供应商列表格式不正确，请输入有效的JSON数组')

    def clean(self):
        cleaned_data = super().clean()
        # 检查SPU相关字段
        spu_selection = self.data.get('spu_selection')
        if spu_selection == 'create':
            # 验证新建SPU所需的字段
            spu_name = self.data.get('spu_name')
            product_type = self.data.get('product_type')
            category = self.data.get('category')
            if not spu_name:
                self.add_error(None, '新建SPU时，SPU名称不能为空')
            if not product_type:
                self.add_error(None, '新建SPU时，产品类型不能为空')
            if not category:
                self.add_error(None, '新建SPU时，必须选择类目')
            # 如果是新建SPU，则不需要验证spu字段
            if 'spu' in self._errors:
                del self._errors['spu']
        elif spu_selection == 'reference' and not cleaned_data.get('spu'):
            self.add_error('spu', '引用现有SPU时，必须选择一个SPU')
        
        return cleaned_data 