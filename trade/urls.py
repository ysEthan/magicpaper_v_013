from django.urls import path
from . import views

app_name = 'trade'

urlpatterns = [
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/edit/', views.OrderUpdateView.as_view(), name='order_edit'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('orders/sync/', views.sync_orders, name='order_sync'),
    path('generate-order-no/', views.generate_order_no, name='generate_order_no'),
] 