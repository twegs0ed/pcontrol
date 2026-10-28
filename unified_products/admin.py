# unified_products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ['field_index', 'title', 'image', 'image_preview']
    readonly_fields = ['field_index', 'image_preview']
    ordering = ['field_index']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; border-radius: 4px;"/>',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Превью'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'prefix', 'image_count', 'is_active', 'product_count', 'sample_link']
    list_filter = ['is_active']
    search_fields = ['name', 'prefix']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'prefix', 'image_count', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:unified_products_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    product_count.short_description = 'Изделий'
    
    def sample_link(self, obj):
        try:
            sample = obj.products.filter(is_sample=True).first()
            if sample:
                url = reverse('admin:unified_products_product_change', args=[sample.id])
                return format_html('<a href="{}">Образец: {}</a>', url, sample.serial_number)
            return 'Не установлен'
        except:
            return 'Ошибка'
    sample_link.short_description = 'Образец'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'category', 'owner', 'status', 'is_sample_display', 'progress_display', 'created_at']
    list_filter = ['category', 'status', 'owner', 'is_sample']
    search_fields = ['serial_number', 'description']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('serial_number', 'category', 'owner', 'status', 'description')
        }),
        ('Фото серийного номера', {
            'fields': ('serial_photo',)
        }),
        ('Образец', {
            'fields': ('is_sample',),
            'description': 'Только для администратора. Отметьте, чтобы сделать этот объект образцом.'
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at', 'completed_at', 'closed_by'),
            'classes': ('collapse',)
        }),
    )
    
    def is_sample_display(self, obj):
        if obj.is_sample:
            return format_html('<span class="badge bg-warning text-dark">⭐ Образец</span>', '')
        return '-'
    is_sample_display.short_description = 'Образец'
    
    def progress_display(self, obj):
        filled = obj.get_filled_count()
        required = obj.get_total_required()
        percent = obj.get_progress_percent()
        color = 'green' if filled >= required else 'orange'
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color, filled, required, int(percent)
        )
    progress_display.short_description = 'Прогресс'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name='Аудитор').exists():
            return qs
        if request.user.groups.filter(name='Контролер').exists():
            return qs.filter(owner=request.user)
        return qs.none()
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.owner != request.user:
            return False
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'field_index', 'title', 'has_image']
    list_filter = ['product__category']
    search_fields = ['product__serial_number', 'title']
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.short_description = 'Есть изображение'
    has_image.boolean = True