from django.urls import path
from . import views

app_name = 'storage'

urlpatterns = [
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/sync/', views.stock_sync, name='stock_sync'),
] 