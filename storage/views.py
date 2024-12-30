from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Stock
from django.db import models
from .sync import sync_all_stock

@login_required
def stock_list(request):
    stocks = Stock.objects.select_related('warehouse', 'sku', 'sku__spu').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        stocks = stocks.filter(
            models.Q(sku__sku_code__icontains=search_query) |
            models.Q(sku__sku_name__icontains=search_query) |
            models.Q(sku__spu__spu_name__icontains=search_query) |
            models.Q(warehouse__name__icontains=search_query)
        )
    
    return render(request, 'storage/stock_list.html', {
        'stocks': stocks,
        'search_query': search_query,
        'active_menu': 'storage_stock'
    })

@login_required
def stock_sync(request):
    if request.method == 'POST':
        try:
            sync_all_stock()
            messages.success(request, '库存数据同步成功！')
        except Exception as e:
            messages.error(request, f'同步失败：{str(e)}')
    return redirect('storage:stock_list')
