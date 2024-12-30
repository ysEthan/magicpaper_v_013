from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
import logging
from .models import Order, Shop
from .forms import OrderForm
from . import sync

# 获取logger实例
logger = logging.getLogger(__name__)

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'trade/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-created_at']
    login_url = '/admin/login/'  # 登录页面的URL

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 搜索条件
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(order_no__icontains=search_query) |
                Q(platform_order_no__icontains=search_query) |
                Q(recipient_name__icontains=search_query)
            )
        
        # 店铺筛选
        shop_id = self.request.GET.get('shop', '')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
            
        # 状态筛选
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 添加搜索参数到上下文
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_shop'] = self.request.GET.get('shop', '')
        context['selected_status'] = self.request.GET.get('status', '')
        
        # 添加店铺列表
        context['shops'] = Shop.objects.filter(is_active=True)
        
        # 添加状态选项
        context['status_choices'] = Order.OrderStatus.choices
        
        return context

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'trade/order_form.html'
    success_url = reverse_lazy('trade:order_list')
    login_url = '/admin/login/'

    def form_valid(self, form):
        form.instance.created_at = timezone.now()
        return super().form_valid(form)

class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'trade/order_form.html'
    success_url = reverse_lazy('trade:order_list')
    login_url = '/admin/login/'

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'trade/order_detail.html'
    context_object_name = 'order'
    login_url = '/admin/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 添加额外的上下文数据
        order = self.get_object()
        context['cart_items'] = order.cart_set.all()
        return context

@require_POST
@login_required(login_url='/admin/login/')
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    try:
        order.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
@login_required(login_url='/admin/login/')
def sync_orders(request):
    """同步订单数据"""
    try:
        logger.info("开始同步订单数据")
        success, message = sync.sync_all_trade()
        if success:
            logger.info(f"订单同步成功: {message}")
            return JsonResponse({'status': 'success', 'message': message})
        else:
            logger.error(f"订单同步失败: {message}")
            return JsonResponse({'status': 'error', 'message': message}, status=500)
    except Exception as e:
        error_message = str(e)
        logger.error(f"订单同步发生异常: {error_message}")
        return JsonResponse({'status': 'error', 'message': error_message}, status=500)
