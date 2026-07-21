# pcontrol_app/admin.py
from django.contrib import admin
from .models import Application, ProductPrefix, SearchHistory


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['app_name', 'app_label', 'is_active', 'prefix_count']
    list_filter = ['is_active']
    search_fields = ['app_name', 'app_label']
    
    def prefix_count(self, obj):
        return obj.productprefix_set.count()
    prefix_count.short_description = 'Префиксов'


@admin.register(ProductPrefix)
class ProductPrefixAdmin(admin.ModelAdmin):
    list_display = [
        'prefix', 
        'product_name', 
        'get_app_name', 
        'get_model_name_display',
        'use_unified_system', 
        'get_category_name',
        'is_active'
    ]
    list_filter = ['app', 'model_name', 'is_active', 'use_unified_system']
    search_fields = ['prefix', 'product_name', 'model_name']
    ordering = ['prefix']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('prefix', 'product_name', 'is_active')
        }),
        ('Старая система (приложение)', {
            'fields': ('app', 'model_name', 'edit_url_name', 'list_url_name', 'detail_url_name'),
            'classes': ('collapse',),
            'description': 'Настройки для работы со старыми приложениями'
        }),
        ('Новая система (unified_products)', {
            'fields': ('category', 'use_unified_system'),
            'classes': ('collapse',),
            'description': 'Настройки для работы с новой единой системой'
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def get_app_name(self, obj):
        return obj.app.app_name if obj.app else '-'
    get_app_name.short_description = 'Приложение'
    get_app_name.admin_order_field = 'app__app_name'
    
    def get_model_name_display(self, obj):
        if obj.use_unified_system and obj.category:
            return f"{obj.model_name} ⭐"
        return obj.model_name
    get_model_name_display.short_description = 'Модель'
    
    def get_category_name(self, obj):
        if obj.category:
            return obj.category.name
        return '-'
    get_category_name.short_description = 'Категория (новая)'
    get_category_name.admin_order_field = 'category__name'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('app', 'category')


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'serial_number', 'found', 'app_label', 'created_at']
    list_filter = ['found', 'app_label', 'created_at']
    search_fields = ['serial_number', 'user__username']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False