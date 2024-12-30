from django.shortcuts import render
from django.views.generic import ListView
from .models import Order

class OrderListView(ListView):
    model = Order
    template_name = 'trade/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        # 添加查询条件
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(order_no__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 添加额外的上下文数据
        context['search_query'] = self.request.GET.get('q', '')
        return context
