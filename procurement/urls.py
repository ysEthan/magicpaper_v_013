from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-order/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-order/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-order/<int:pk>/edit/', views.purchase_order_edit, name='purchase_order_edit'),
    path('purchase-order/<int:pk>/delete/', views.purchase_order_delete, name='purchase_order_delete'),
    path('purchase-orders/sync/', views.sync_purchase_orders, name='sync_purchase_orders'),
] 