# templatetags/form_filters.py (создайте файл)
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_field(form, field_name):
    """Получить поле формы по имени"""
    return form[field_name] if field_name in form.fields else None

@register.filter
def get_image_field(form, num):
    """Получить поле изображения по номеру"""
    field_name = f"image{num}"
    return form[field_name] if field_name in form.fields else None