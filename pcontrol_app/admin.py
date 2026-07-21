# pcontrol_app/admin.py
from django.contrib import admin
from .models import ProductPrefix, Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['app_name', 'app_label', 'is_active']
    search_fields = ['app_name', 'app_label']
    list_filter = ['is_active']

@admin.register(ProductPrefix)
class ProductPrefixAdmin(admin.ModelAdmin):
    list_display = ['prefix', 'product_name', 'get_app_name', 'model_name', 'is_active']
    list_filter = ['app', 'model_name', 'is_active']
    search_fields = ['prefix', 'product_name']
    ordering = ['prefix']
    
    def get_app_name(self, obj):
        return obj.app.app_name if obj.app else '-'
    get_app_name.short_description = 'Приложение'
    get_app_name.admin_order_field = 'app__app_name'