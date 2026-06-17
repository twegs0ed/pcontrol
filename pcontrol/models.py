from django.db import models
from django.core.cache import cache

class MenuItem(models.Model):
    title = models.CharField(
        max_length=100,
        verbose_name='Название пункта меню'
    )
    url = models.CharField(
        max_length=200,
        verbose_name='URL-адрес',
        help_text='Можно указать полный URL или путь (например, /about/)'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок отображения',
        help_text='Чем меньше число, тем выше в меню'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Показывать ли пункт в меню'
    )
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Очищаем кэш при сохранении любого пункта
        cache.delete('active_menu_items')

    class Meta:
        ordering = ['order']  # Сортировка по полю order
        verbose_name = 'Пункт меню'
        verbose_name_plural = 'Пункты меню'

    def __str__(self):
        return self.title