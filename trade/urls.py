from django.urls import path
from . import views

app_name = 'trade'

urlpatterns = [
    path('orders/', views.OrderListView.as_view(), name='order_list'),
] 