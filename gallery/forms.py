from django import forms
from .models import Category, SPU

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