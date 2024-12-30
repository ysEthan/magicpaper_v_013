from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, SPU
from .forms import CategoryForm, SPUForm
from django.db import models

@login_required
def category_list(request):
    categories = Category.objects.filter(status=1).order_by('rank_id', 'id')
    
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(
            models.Q(category_name_zh__icontains=search_query) |
            models.Q(category_name_en__icontains=search_query)
        )
    
    return render(request, 'gallery/category_list.html', {
        'categories': categories,
        'search_query': search_query,
        'active_menu': 'gallery_category'
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

@login_required
def spu_list(request):
    spus = SPU.objects.select_related('brand', 'category', 'poc').filter(status=True)
    
    search_query = request.GET.get('search', '')
    if search_query:
        spus = spus.filter(
            models.Q(spu_code__icontains=search_query) |
            models.Q(spu_name__icontains=search_query)
        )
    
    return render(request, 'gallery/spu_list.html', {
        'spus': spus,
        'search_query': search_query,
        'active_menu': 'gallery_spu'
    })

@login_required
def spu_add(request):
    if request.method == 'POST':
        form = SPUForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'SPU添加成功！')
            return redirect('gallery:spu_list')
        else:
            messages.error(request, '请检查输入是否正确')
    else:
        form = SPUForm()
    
    return render(request, 'gallery/spu_form.html', {
        'form': form,
        'title': '添加SPU',
        'active_menu': 'gallery_spu'
    })

@login_required
def spu_edit(request, pk):
    spu = get_object_or_404(SPU, pk=pk)
    if request.method == 'POST':
        form = SPUForm(request.POST, instance=spu)
        if form.is_valid():
            form.save()
            messages.success(request, 'SPU更新成功！')
            return redirect('gallery:spu_list')
        else:
            messages.error(request, '请检查输入是否正确')
    else:
        form = SPUForm(instance=spu)
    
    return render(request, 'gallery/spu_form.html', {
        'form': form,
        'title': '编辑SPU',
        'active_menu': 'gallery_spu'
    })

@login_required
def spu_delete(request, pk):
    spu = get_object_or_404(SPU, pk=pk)
    
    if request.method == 'POST':
        try:
            # 检查是否有关联的SKU
            if hasattr(spu, 'skus') and spu.skus.exists():
                messages.error(request, '无法删除：该SPU下存在SKU')
                return redirect('gallery:spu_list')
            
            spu.delete()
            messages.success(request, 'SPU删除成功！')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
        return redirect('gallery:spu_list')
    
    return render(request, 'gallery/spu_delete.html', {
        'spu': spu,
        'active_menu': 'gallery_spu'
    })
