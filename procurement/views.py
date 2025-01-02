from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import PurchaseOrder
from . import sync
import logging

# 获取logger实例
logger = logging.getLogger(__name__)

@login_required
def purchase_order_list(request):
    """采购单列表视图"""
    purchase_orders = PurchaseOrder.objects.all().order_by('-created_at')
    return render(request, 'procurement/purchase_order_list.html', {
        'purchase_orders': purchase_orders,
        'active_menu': 'procurement_order'
    })

@login_required
def purchase_order_create(request):
    """创建采购单"""
    if request.method == 'POST':
        # TODO: 处理表单提交
        pass
    return render(request, 'procurement/purchase_order_form.html', {
        'active_menu': 'procurement_order'
    })

@login_required
def purchase_order_edit(request, pk):
    """编辑采购单"""
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        # TODO: 处理表单提交
        pass
    return render(request, 'procurement/purchase_order_form.html', {
        'purchase_order': purchase_order,
        'active_menu': 'procurement_order'
    })

@login_required
def purchase_order_detail(request, pk):
    """采购单详情"""
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    return render(request, 'procurement/purchase_order_detail.html', {
        'purchase_order': purchase_order,
        'active_menu': 'procurement_order'
    })

@login_required
def purchase_order_delete(request, pk):
    """删除采购单"""
    if request.method == 'POST':
        purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
        purchase_order.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=405)

@require_POST
@login_required
def sync_purchase_orders(request):
    """同步采购单数据"""
    try:
        logger.info("开始同步采购单数据")
        success, message = sync.sync_all_purchase()
        if success:
            logger.info(f"采购单同步成功: {message}")
            return JsonResponse({
                'status': 'success',
                'message': message,
                'redirect_url': reverse('procurement:purchase_order_list')
            })
        else:
            logger.error(f"采购单同步失败: {message}")
            return JsonResponse({
                'status': 'error',
                'message': f"同步失败: {message}",
                'redirect_url': reverse('procurement:purchase_order_list')
            }, status=500)
    except Exception as e:
        error_message = str(e)
        logger.error(f"采购单同步发生异常: {error_message}")
        logger.exception("详细错误信息:")
        return JsonResponse({
            'status': 'error',
            'message': f"同步过程中发生错误: {error_message}",
            'redirect_url': reverse('procurement:purchase_order_list')
        }, status=500)
