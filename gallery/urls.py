from django.urls import path
from . import views

app_name = 'gallery'

urlpatterns = [
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('spu/', views.spu_list, name='spu_list'),
    path('spu/add/', views.spu_add, name='spu_add'),
    path('spu/<int:pk>/edit/', views.spu_edit, name='spu_edit'),
    path('spu/<int:pk>/delete/', views.spu_delete, name='spu_delete'),
    path('sku/', views.sku_list, name='sku_list'),
    path('sku/add/', views.sku_add, name='sku_add'),
    path('sku/<int:pk>/edit/', views.sku_edit, name='sku_edit'),
    path('sku/<int:pk>/delete/', views.sku_delete, name='sku_delete'),
    path('sku/sync/', views.sku_sync, name='sku_sync'),
] 