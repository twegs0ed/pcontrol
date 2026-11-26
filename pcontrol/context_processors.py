from django.contrib.auth.models import Permission


def menu_context(request):
    """Context processor для меню"""
    user = request.user
    
    return {
        'can_create_category': user.is_authenticated and (
            user.is_superuser or 
            user.has_perm('unified_products.add_category')
        ),
    }
