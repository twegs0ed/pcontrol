from django.contrib import admin
from .models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']  # Редактирование прямо в списке
    list_filter = ['is_active']  # Фильтр по активности
    search_fields = ['title']  # Поиск по названию
    ordering = ['order']  # Сортировка в админке