# gs14/templatetags/form_filters.py
from django import template

register = template.Library()

@register.filter
def get_field(form, field_name):
    """Получить поле из формы по имени"""
    try:
        if form and hasattr(form, 'fields') and field_name in form.fields:
            return form[field_name]
    except Exception:
        pass
    return None

@register.filter
def get_attr(obj, attr_name):
    """Получить атрибут объекта по имени"""
    try:
        if obj and hasattr(obj, attr_name):
            return getattr(obj, attr_name)
    except Exception:
        pass
    return None

@register.filter
def add_str(value, arg):
    """Сложение строк"""
    try:
        return str(value) + str(arg)
    except Exception:
        return str(value)