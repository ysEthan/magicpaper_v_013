from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
import logging
from .models import Order, Shop, Cart
from gallery.models import SKU
from storage.models import Warehouse
from logistics.models import Service, Package
from .forms import OrderForm
from . import sync
import json

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        try:
            default_shop = Shop.objects.get(id=1)
            initial['shop'] = default_shop.id
        except Shop.DoesNotExist:
            logger.error("找不到默认店铺(ID=1)")
            initial['shop'] = None
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skus'] = SKU.objects.filter(status=True).select_related('spu')
        # 添加仓库和物流服务数据
        context['warehouses'] = Warehouse.objects.all()
        context['services'] = Service.objects.select_related('carrier').all()
        return context

    def form_valid(self, form):
        form.instance.created_at = timezone.now()
        try:
            default_shop = Shop.objects.get(id=1)
            form.instance.shop = default_shop
        except Shop.DoesNotExist:
            logger.error("找不到默认店铺(ID=1)")
            raise ValueError("找不到默认店铺，无法创建订单")
        
        # 记录所有表单数据
        logger.info("表单数据:")
        for field in form.cleaned_data:
            logger.info(f"{field}: {form.cleaned_data[field]}")
        
        # 设置platform_order_no与order_no一致
        form.instance.platform_order_no = form.instance.order_no
        
        # 设置初始支付金额为0，后续由购物车计算
        form.instance.paid_amount = 0
        response = super().form_valid(form)
        
        # 处理购物车数据
        cart_data = self.request.POST.get('cart_data')
        logger.info(f"接收到的购物车数据: {cart_data}")
        
        try:
            cart_items = json.loads(cart_data)
            logger.info(f"解析后的购物车数据: {cart_items}")
            
            # 计算订单总金额
            total_amount = 0
            
            # 准备包裹的商品信息
            package_items = []
            
            for item in cart_items:
                logger.info(f"正在创建购物车项: {item}")
                qty = int(item['qty'])
                price = float(item['price'])
                discount = float(item['discount'])
                actual_price = price * qty - discount
                total_amount += actual_price
                
                cart = Cart.objects.create(
                    order=self.object,
                    sku_id=item['sku_id'],
                    qty=qty,
                    price=price,
                    discount=discount,
                    actual_price=actual_price,
                    cost=0  # 这里可以根据需要设置成本价
                )
                
                # 获取SKU信息，添加到包裹商品列表
                sku = SKU.objects.get(id=item['sku_id'])
                package_items.append({
                    'sku_id': sku.id,
                    'sku_code': sku.sku_code,
                    'sku_name': sku.sku_name,
                    'qty': qty,
                    'weight': float(sku.weight) if sku.weight else 0,
                    'length': float(sku.length) if sku.length else 0,
                    'width': float(sku.width) if sku.width else 0,
                    'height': float(sku.height) if sku.height else 0
                })
            
            # 更新订单的支付金额（商品金额 + 用户支付运费）
            freight = float(form.cleaned_data.get('freight', 0))
            self.object.paid_amount = total_amount + freight
            self.object.save()
            
            # 创建包裹记录
            try:
                warehouse = form.cleaned_data.get('warehouse')
                service = form.cleaned_data.get('service')
                
                logger.info(f"准备创建包裹，仓库: {warehouse}, 物流服务: {service}")
                logger.info(f"POST数据: {self.request.POST}")
                
                if warehouse and service:
                    try:
                        package = Package.objects.create(
                            order=self.object,
                            warehouse=warehouse,
                            service=service,
                            tracking_no=form.cleaned_data.get('tracking_no', ''),
                            pkg_status_code=form.cleaned_data.get('pkg_status_code', '0'),
                            shipping_fee=form.cleaned_data.get('shipping_fee', 0),  # 使用物流成本
                            items=package_items
                        )
                        logger.info(f"为订单 {self.object.order_no} 创建包裹成功，包裹ID: {package.id}")
                    except Exception as e:
                        logger.error(f"创建包裹时出错: {str(e)}")
                        logger.error(f"参数: order={self.object}, service={service}, items={package_items}")
                        raise
                else:
                    logger.warning(f"订单 {self.object.order_no} 缺少仓库或物流服务信息，跳过创建包裹")
                    logger.warning(f"warehouse={warehouse}, service={service}")
            
            except Exception as e:
                logger.error(f"创建包裹记录时发生错误: {str(e)}")
                logger.exception("详细错误信息:")
                # 不抛出异常，让订单创建继续完成
            
            logger.info("购物车数据保存成功")
        except Exception as e:
            logger.error(f"保存购物车数据时发生错误: {str(e)}")
            logger.exception("详细错误信息:")
            raise  # 抛出异常，让事务回滚
                
        return response

class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'trade/order_form.html'
    success_url = reverse_lazy('trade:order_list')
    login_url = '/admin/login/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skus'] = SKU.objects.filter(status=True).select_related('spu')
        # 添加仓库和物流服务数据
        context['warehouses'] = Warehouse.objects.all()
        context['services'] = Service.objects.select_related('carrier').all()
        return context

    def form_valid(self, form):
        # 设置初始支付金额为0，后续由购物车计算
        form.instance.paid_amount = 0
        response = super().form_valid(form)
        
        # 处理购物车数据
        cart_data = self.request.POST.get('cart_data')
        if cart_data:
            try:
                # 删除原有的购物车数据
                self.object.cart_set.all().delete()
                
                # 创建新的购物车数据
                cart_items = json.loads(cart_data)
                total_amount = 0
                
                for item in cart_items:
                    qty = int(item['qty'])
                    price = float(item['price'])
                    discount = float(item['discount'])
                    actual_price = price * qty - discount
                    total_amount += actual_price
                    
                    Cart.objects.create(
                        order=self.object,
                        sku_id=item['sku_id'],
                        qty=qty,
                        price=price,
                        discount=discount,
                        actual_price=actual_price,
                        cost=0  # 这里可以根据需要设置成本价
                    )
                
                # 更新订单的支付金额（商品金额 + 用户支付运费）
                freight = float(form.cleaned_data.get('freight', 0))
                self.object.paid_amount = total_amount + freight
                self.object.save()
                
                logger.info("购物车数据更新成功")
            except Exception as e:
                logger.error(f"更新购物车数据时发生错误: {str(e)}")
                raise  # 抛出异常，让事务回滚
                
        return response

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

@require_GET
def generate_order_no(request):
    """生成订单号的API"""
    order_type = request.GET.get('order_type')
    if not order_type:
        return JsonResponse({'error': 'order_type is required'}, status=400)
        
    form = OrderForm()
    order_no = form.generate_order_no(order_type)
    return JsonResponse({
        'order_no': order_no,
        'platform_order_no': order_no  # 平台订单号与订单号保持一致
    })
