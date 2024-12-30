from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name_en', 'category_name_zh', 'description', 
                 'image', 'parent', 'rank_id', 'level', 'is_last_level', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        } 