from django import template

register = template.Library()

@register.filter
def get_field(form, field_name):
    """Получить поле из формы по имени"""
    try:
        if form and hasattr(form, 'fields') and field_name in form.fields:
            return form[field_name]
    except Exception as e:
        print(f"Ошибка в get_field: {e}")
    return None

@register.filter
def get_attr(obj, attr_name):
    """Получить атрибут объекта по имени"""
    try:
        if obj and hasattr(obj, attr_name):
            return getattr(obj, attr_name)
    except Exception as e:
        print(f"Ошибка в get_attr: {e}")
    return None