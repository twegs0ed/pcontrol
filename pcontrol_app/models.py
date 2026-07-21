# pcontrol_app/models.py
from django.db import models
from django.apps import apps

class Application(models.Model):
    """Модель для хранения списка приложений"""
    app_label = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Метка приложения'
    )
    app_name = models.CharField(
        max_length=100,
        verbose_name='Название приложения'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )
    
    class Meta:
        verbose_name = 'Приложение'
        verbose_name_plural = 'Приложения'
        ordering = ['app_name']
    
    def __str__(self):
        return self.app_name

class ProductPrefix(models.Model):
    """Модель для хранения префиксов серийных номеров"""
    
    prefix = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Префикс серийного номера',
        help_text='Первые цифры серийного номера, например: 123, 4567'
    )
    product_name = models.CharField(
        max_length=100,
        verbose_name='Название изделия',
        help_text='Например: GS14, KT08_9a'
    )
    app = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        verbose_name='Приложение'
    )
    model_name = models.CharField(
        max_length=50,
        verbose_name='Модель',
        help_text='Название модели в приложении (Control, KT08_9a)'
    )
    edit_url_name = models.CharField(
        max_length=100,
        verbose_name='Имя URL для редактирования',
        help_text='Например: control_edit или kt08_9a_edit',
        default='edit'
    )
    list_url_name = models.CharField(
        max_length=100,
        verbose_name='Имя URL для списка',
        help_text='Например: gs14_control_list или kt08_9a_list',
        default='list'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    detail_url_name = models.CharField(
        max_length=100,
        verbose_name='Имя URL для просмотра',
        help_text='Например: detail или control_detail',
        default='detail',
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = 'Префикс изделия'
        verbose_name_plural = 'Префиксы изделий'
        ordering = ['prefix']
        unique_together = ['prefix', 'app', 'model_name']
    
    def __str__(self):
        return f"{self.prefix} → {self.product_name}"
    
    def get_model(self):
        """Получить модель по app_label и model_name"""
        try:
            return apps.get_model(self.app.app_label, self.model_name)
        except LookupError:
            return None
    
    def get_edit_url(self, serial_number):
        """Получить URL для редактирования"""
        try:
            from django.urls import reverse
            return reverse(f'{self.app.app_label}:{self.edit_url_name}', kwargs={'serial_number': serial_number})
        except:
            return None
    
    def get_list_url(self):
        """Получить URL для списка"""
        try:
            from django.urls import reverse
            return reverse(f'{self.app.app_label}:{self.list_url_name}')
        except:
            return None
    def get_detail_url(self, serial_number):
            """Получить URL для детального просмотра"""
            try:
                from django.urls import reverse
                detail_url_name = getattr(self, 'detail_url_name', 'detail')
                return reverse(
                    f'{self.app.app_label}:{detail_url_name}', 
                    kwargs={'serial_number': serial_number}
                )
            except Exception as e:
                logger.warning(f"Не удалось получить detail_url: {e}")
                return None
