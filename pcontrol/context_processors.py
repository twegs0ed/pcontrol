from django.core.cache import cache
from .models import MenuItem

def menu_items(request):
    from django.core.cache import cache
    from urllib.parse import urlparse

    cached_menu = cache.get('active_menu_items')
    if cached_menu is not None:
        return {'menu_items': cached_menu}

    items = MenuItem.objects.filter(is_active=True)
    processed_items = []

    for item in items:
        # Если URL не начинается с http/https, добавляем текущий домен
        if not urlparse(item.url).netloc:
            item.url = request.build_absolute_uri(item.url)
        processed_items.append(item)

    cache.set('active_menu_items', processed_items, 300)
    return {'menu_items': processed_items}