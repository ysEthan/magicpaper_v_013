from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category
from .forms import CategoryForm

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'gallery/category_list.html', {
        'categories': categories,
        'active_menu': 'gallery_category'  # 用于高亮左侧菜单
    })

@login_required
def category_add(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '类目添加成功！')
            return redirect('gallery:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'gallery/category_form.html', {
        'form': form,
        'title': '添加类目',
        'active_menu': 'gallery_category'
    })

@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '类目更新成功！')
            return redirect('gallery:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'gallery/category_form.html', {
        'form': form,
        'title': '编辑类目',
        'active_menu': 'gallery_category'
    })

@login_required
def category_delete(request, pk):
    # 直接使用get_object_or_404，它会自动处理对象不存在的情况
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        # 检查是否有子类目
        if category.children.exists():
            messages.error(request, '无法删除含有子类目的分类')
            return redirect('gallery:category_list')
        
        try:
            category.delete()
            messages.success(request, '类目删除成功！')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
        return redirect('gallery:category_list')
    
    # GET请求显示确认页面
    return render(request, 'gallery/category_delete.html', {
        'category': category,
        'active_menu': 'gallery_category'
    })
