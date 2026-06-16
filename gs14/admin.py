# admin.py
from django.contrib import admin
from .models import Control

@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'title1', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['serial_number', 'title1', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('serial_number', 'title1', 'description')
        }),
        ('Медиа', {
            'fields': ('image1',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )