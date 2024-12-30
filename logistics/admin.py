from django.contrib import admin
from .models import Carrier, Service, Package


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name_zh', 'name_en', 'code', 'contact', 'url']
    search_fields = ['name_zh', 'name_en', 'code']
    list_per_page = 20


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['carrier', 'service_name', 'service_code', 'service_type']
    list_filter = ['carrier']
    search_fields = ['service_name', 'service_code']
    list_per_page = 20


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'tracking_no', 'carrier_name', 'service_name', 'pkg_status_code', 'shipping_fee']
    list_filter = ['pkg_status_code', 'service__carrier']
    search_fields = ['tracking_no', 'order__order_no']
    list_per_page = 20
