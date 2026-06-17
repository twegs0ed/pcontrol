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
            'fields': ('serial_number', 'description')
        }),
        ('Изображения', {
            'fields': (
                ('title1', 'image1'),
                ('title2', 'image2'),
                ('title3', 'image3'),
                ('title4', 'image4'),
                ('title5', 'image5'),
                ('title6', 'image6'),
                ('title7', 'image7'),
            )
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )