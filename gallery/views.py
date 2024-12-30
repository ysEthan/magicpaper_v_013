from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, SPU, SKU, Brand
from .forms import CategoryForm, SPUForm, SKUForm
from django.db import models
from django.contrib.auth.models import User

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

@login_required
def sku_list(request):
    skus = SKU.objects.select_related('spu')
    
    search_query = request.GET.get('search', '')
    if search_query:
        skus = skus.filter(
            models.Q(sku_code__icontains=search_query) |
            models.Q(sku_name__icontains=search_query) |
            models.Q(spu__spu_name__icontains=search_query)
        )
    
    return render(request, 'gallery/sku_list.html', {
        'skus': skus,
        'search_query': search_query,
        'active_menu': 'gallery_sku'
    })

@login_required
def sku_add(request):
    spus = SPU.objects.filter(status=True)
    pocs = User.objects.filter(is_active=True)
    brands = Brand.objects.filter(status=True)
    categories = Category.objects.filter(status=True).order_by('level', 'rank_id')
    
    # 生成新的SKU编码
    last_sku = SKU.objects.order_by('-id').first()
    next_sku_id = (last_sku.id + 1) if last_sku else 1
    generated_sku_code = f'SKU{str(next_sku_id).zfill(6)}'
    
    # 生成新的SPU编码
    last_spu = SPU.objects.order_by('-id').first()
    next_spu_id = (last_spu.id + 1) if last_spu else 1
    generated_spu_code = f'SPU{str(next_spu_id).zfill(6)}'

    if request.method == 'POST':
        form = SKUForm(request.POST)
        if form.is_valid():
            try:
                spu_selection = request.POST.get('spu_selection')
                if spu_selection == 'create':
                    # 创建新的SPU
                    new_spu = SPU.objects.create(
                        spu_code=generated_spu_code,
                        spu_name=request.POST.get('spu_name'),
                        product_type=request.POST.get('product_type'),
                        sales_channel=request.POST.get('sales_channel'),
                        brand_id=request.POST.get('brand') or None,
                        poc_id=request.POST.get('poc') or None,
                        spu_remark=request.POST.get('spu_remark', ''),
                        category_id=request.POST.get('category'),
                        status=True
                    )
                    # 将新创建的SPU分配给SKU，并设置状态为True
                    sku = form.save(commit=False)
                    sku.spu = new_spu
                    sku.status = True
                    sku.save()
                    messages.success(request, f'成功创建SPU "{new_spu.spu_name}" 和 SKU "{sku.sku_name}"！')
                else:
                    # 直接保存SKU时也设置状态为True
                    sku = form.save(commit=False)
                    sku.status = True
                    sku.save()
                    messages.success(request, f'SKU "{sku.sku_name}" 添加成功！')
                
                return redirect('gallery:sku_list')
            except Exception as e:
                messages.error(request, f'保存失败：{str(e)}')
        else:
            # 显示表单级别的错误
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, error)
            # 显示字段级别的错误
            for field, errors in form.errors.items():
                if field != '__all__':  # 排除表单级别的错误
                    field_name = form.fields[field].label or field
                    messages.error(request, f'{field_name}: {errors[0]}')
    else:
        form = SKUForm(initial={'sku_code': generated_sku_code})
    
    return render(request, 'gallery/sku_form.html', {
        'form': form,
        'title': '添加SKU',
        'active_menu': 'gallery_sku',
        'spus': spus,
        'pocs': pocs,
        'brands': brands,
        'categories': categories,  # 添加类目数据到上下文
        'generated_sku_code': generated_sku_code,
        'generated_spu_code': generated_spu_code
    })

@login_required
def sku_edit(request, pk):
    sku = get_object_or_404(SKU, pk=pk)
    if request.method == 'POST':
        form = SKUForm(request.POST, instance=sku)
        if form.is_valid():
            form.save()
            messages.success(request, 'SKU更新成功！')
            return redirect('gallery:sku_list')
        else:
            messages.error(request, '请检查输入是否正确')
    else:
        form = SKUForm(instance=sku)
    
    return render(request, 'gallery/sku_form.html', {
        'form': form,
        'title': '编辑SKU',
        'active_menu': 'gallery_sku'
    })

@login_required
def sku_delete(request, pk):
    sku = get_object_or_404(SKU, pk=pk)
    
    if request.method == 'POST':
        try:
            sku.delete()
            messages.success(request, 'SKU删除成功！')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
        return redirect('gallery:sku_list')
    
    return render(request, 'gallery/sku_delete.html', {
        'sku': sku,
        'active_menu': 'gallery_sku'
    })
