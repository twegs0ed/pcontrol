from django.apps import AppConfig


class UnifiedProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unified_products'
    verbose_name = 'Управление изделиями'
    
    def ready(self):
        import unified_products.signals