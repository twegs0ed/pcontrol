# pcontrol_app/models.py
from django.db import models
from django.apps import apps
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Application(models.Model):
    """
    Модель для хранения списка приложений
    """
    app_label = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Метка приложения',
        help_text='Уникальный идентификатор приложения (например: gs14, kt08_9a)'
    )
    app_name = models.CharField(
        max_length=100,
        verbose_name='Название приложения',
        help_text='Отображаемое название приложения (например: GS14, KT08_9a)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно',
        help_text='Отметьте, чтобы приложение было доступно в поиске'
    )
    
    # ✅ ПРАВИЛЬНО: используем только auto_now_add
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    # ✅ ПРАВИЛЬНО: используем только auto_now
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Приложение'
        verbose_name_plural = 'Приложения'
        ordering = ['app_name']

    def __str__(self):
        return self.app_name


class ProductPrefix(models.Model):
    """
    Модель для хранения префиксов серийных номеров
    Связывает серийные номера с приложениями и моделями
    Поддерживает как старую, так и новую систему (unified_products)
    """
    
    # === Основная информация ===
    prefix = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Префикс серийного номера',
        help_text='Первые цифры серийного номера, например: 123, 4567'
    )
    product_name = models.CharField(
        max_length=100,
        verbose_name='Название изделия',
        help_text='Например: GS14, KT08_9a, TTR-10AB'
    )
    
    # === Связь с приложением (старая система) ===
    app = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        verbose_name='Приложение',
        help_text='Приложение, в котором находится модель'
    )
    model_name = models.CharField(
        max_length=50,
        verbose_name='Модель',
        help_text='Название модели в приложении (Control, KT08_9a, TTR10AB)'
    )
    
    # === URL-адреса для старой системы ===
    edit_url_name = models.CharField(
        max_length=100,
        verbose_name='Имя URL для редактирования',
        help_text='Например: control_edit или kt08_9a_edit',
        default='control_edit'
    )
    list_url_name = models.CharField(
        max_length=100,
        verbose_name='Имя URL для списка',
        help_text='Например: control_list или kt08_9a_list',
        default='control_list'
    )
    detail_url_name = models.CharField(
        max_length=100,
        verbose_name='Имя URL для просмотра',
        help_text='Например: control_detail или kt08_9a_detail',
        default='control_detail',
        blank=True,
        null=True
    )
    
    # === Связь с новой системой (unified_products) ===
    category = models.ForeignKey(
        'unified_products.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Категория (новая система)',
        help_text='Связь с категорией в unified_products. Если указана, используется новая система.'
    )
    use_unified_system = models.BooleanField(
        default=False,
        verbose_name='Использовать новую систему',
        help_text='Отметьте, чтобы использовать unified_products вместо старого приложения'
    )
    
    # === Статус ===
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Отметьте, чтобы префикс был доступен для поиска'
    )
    
    # === Системная информация ===
    # ✅ ПРАВИЛЬНО: используем только auto_now_add
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    # ✅ ПРАВИЛЬНО: используем только auto_now
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Префикс изделия'
        verbose_name_plural = 'Префиксы изделий'
        ordering = ['prefix']
        unique_together = ['prefix', 'app', 'model_name']

    def __str__(self):
        if self.use_unified_system and self.category:
            return f"{self.prefix} → {self.product_name} (новая система)"
        return f"{self.prefix} → {self.product_name}"

    def get_model(self):
        """
        Получить модель по app_label и model_name (для старой системы)
        """
        try:
            return apps.get_model(self.app.app_label, self.model_name)
        except LookupError as e:
            logger.error(f"Модель {self.app.app_label}.{self.model_name} не найдена: {e}")
            return None

    def get_edit_url(self, serial_number):
        """
        Получить URL для редактирования
        Поддерживает как старую, так и новую систему
        """
        try:
            from django.urls import reverse
            
            # === НОВАЯ СИСТЕМА ===
            if self.use_unified_system and self.category:
                return reverse('unified_products:product_edit', kwargs={'serial_number': serial_number})
            
            # === СТАРАЯ СИСТЕМА ===
            return reverse(f'{self.app.app_label}:{self.edit_url_name}', kwargs={'serial_number': serial_number})
            
        except Exception as e:
            logger.error(f"Ошибка получения URL редактирования: {e}")
            return None

    def get_list_url(self):
        """
        Получить URL для списка
        Поддерживает как старую, так и новую систему
        """
        try:
            from django.urls import reverse
            
            # === НОВАЯ СИСТЕМА ===
            if self.use_unified_system and self.category:
                return reverse('unified_products:product_list')
            
            # === СТАРАЯ СИСТЕМА ===
            return reverse(f'{self.app.app_label}:{self.list_url_name}')
            
        except Exception as e:
            logger.error(f"Ошибка получения URL списка: {e}")
            return None

    def get_detail_url(self, serial_number):
        """
        Получить URL для детального просмотра
        Поддерживает как старую, так и новую систему
        """
        try:
            from django.urls import reverse
            
            # === НОВАЯ СИСТЕМА ===
            if self.use_unified_system and self.category:
                try:
                    from unified_products.models import Product
                    product = Product.objects.get(serial_number=serial_number)
                    return reverse('unified_products:product_detail', kwargs={'pk': product.pk})
                except Product.DoesNotExist:
                    logger.warning(f"Продукт с serial_number {serial_number} не найден в unified_products")
                    return None
                except Exception as e:
                    logger.error(f"Ошибка получения продукта: {e}")
                    return None
            
            # === СТАРАЯ СИСТЕМА ===
            detail_url_name = getattr(self, 'detail_url_name', 'detail')
            return reverse(
                f'{self.app.app_label}:{detail_url_name}',
                kwargs={'serial_number': serial_number}
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения URL детального просмотра: {e}")
            return None

    def get_create_url(self):
        """
        Получить URL для создания объекта
        Поддерживает как старую, так и новую систему
        """
        try:
            from django.urls import reverse
            
            # === НОВАЯ СИСТЕМА ===
            if self.use_unified_system and self.category:
                return reverse('unified_products:product_create')
            
            # === СТАРАЯ СИСТЕМА ===
            create_url_name = getattr(self, 'create_url_name', 'control_create')
            return reverse(f'{self.app.app_label}:{create_url_name}')
            
        except Exception as e:
            logger.error(f"Ошибка получения URL создания: {e}")
            return None

    def get_object_by_serial(self, serial_number):
        """
        Получить объект по серийному номеру
        Поддерживает как старую, так и новую систему
        """
        try:
            # === НОВАЯ СИСТЕМА ===
            if self.use_unified_system and self.category:
                from unified_products.models import Product
                return Product.objects.get(serial_number=serial_number)
            
            # === СТАРАЯ СИСТЕМА ===
            model = self.get_model()
            if model:
                return model.objects.get(serial_number=serial_number)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения объекта: {e}")
            return None

    def is_owner(self, serial_number, user):
        """
        Проверить, является ли пользователь владельцем объекта
        """
        try:
            obj = self.get_object_by_serial(serial_number)
            if obj:
                owner = getattr(obj, 'owner', None)
                return owner == user
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки владельца: {e}")
            return False

    def get_status(self, serial_number):
        """
        Получить статус объекта
        """
        try:
            obj = self.get_object_by_serial(serial_number)
            if obj:
                return getattr(obj, 'status', None)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return None

    def get_owner_name(self, serial_number):
        """
        Получить имя владельца объекта
        """
        try:
            obj = self.get_object_by_serial(serial_number)
            if obj:
                owner = getattr(obj, 'owner', None)
                if owner:
                    return owner.get_full_name() or owner.username
            return None
        except Exception as e:
            logger.error(f"Ошибка получения имени владельца: {e}")
            return None

    def is_completed(self, serial_number):
        """
        Проверить, завершен ли объект
        """
        try:
            obj = self.get_object_by_serial(serial_number)
            if obj:
                status = getattr(obj, 'status', None)
                return status in ['completed', 'closed'] if status else False
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки завершенности: {e}")
            return False

    def get_app_info(self):
        """
        Получить информацию о приложении
        """
        return {
            'app_label': self.app.app_label,
            'app_name': self.app.app_name,
            'model_name': self.model_name,
            'product_name': self.product_name,
            'prefix': self.prefix,
            'use_unified': self.use_unified_system,
            'category': self.category.name if self.category else None,
        }


class SearchHistory(models.Model):
    """
    Модель для хранения истории поиска серийных номеров (опционально)
    """
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='search_history'
    )
    serial_number = models.CharField(
        max_length=100,
        verbose_name='Серийный номер'
    )
    found = models.BooleanField(
        default=False,
        verbose_name='Найден'
    )
    app_label = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Приложение'
    )
    
    # ✅ ПРАВИЛЬНО: используем только auto_now_add
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата поиска'
    )

    class Meta:
        verbose_name = 'История поиска'
        verbose_name_plural = 'История поиска'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.serial_number} - {self.created_at.strftime('%d.%m.%Y %H:%M') if self.created_at else 'Нет даты'}"