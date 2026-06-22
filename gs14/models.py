from django.db import models
from django.contrib.auth.models import User
import os
from django.utils.text import slugify
from django.utils import timezone
import uuid

def get_upload_path(instance, filename):
    """Генерация пути для загрузки файлов"""
    ext = os.path.splitext(filename)[1].lower()
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    name = slugify(os.path.splitext(filename)[0]) or 'image'
    new_filename = f"{name}_{timestamp}_{unique_id}{ext}"
    return os.path.join('controls/', new_filename)

class Control(models.Model):
    serial_number = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='Серийный номер',
        db_index=True
    )
    
    # Владелец модели (контролер, который создал)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='controls',
        verbose_name='Владелец',
        null=True,
        blank=True
    )
    
    serial_photo = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото серийного номера'
    )
    
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Описание'
    )
    
    title1 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид внутри'
    )
    image1 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида внутри'
    )

    title2 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид платы'
    )
    image2 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида платы'
    )

    title3 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид спереди'
    )
    image3 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида спереди'
    )

    title4 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид справа'
    )
    image4 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида справа'
    )

    title5 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид слева'
    )
    image5 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида слева'
    )

    title6 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид сзади'
    )
    image6 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида сзади'
    )

    title7 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Комплектность'
    )
    image7 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото комплектности'
    )

    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='Дата обновления'
    )

    # Статус объекта
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершен'),
        ('closed', 'Закрыт'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Статус'
    )
    
    # Дата завершения проверки
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершения'
    )
    
    # Кто закрыл объект
    closed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_controls',
        verbose_name='Закрыл'
    )
    
    class Meta:
        verbose_name = 'GS14'
        verbose_name_plural = 'GS14'
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_controls", "Может просматривать все объекты"),
            ("can_edit_all_controls", "Может редактировать все объекты"),
            ("can_delete_all_controls", "Может удалять все объекты"),
        ]
    
    def is_completed(self):
        """Проверка, заполнены ли все фото"""
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
        for field in image_fields:
            if not getattr(self, field):
                return False
        return True
    
    def check_and_update_status(self):
        """Проверка и обновление статуса"""
        if self.is_completed() and self.status != 'closed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            return True
        return False
    
    def can_edit(self, user=None):
        """
        Проверка, может ли пользователь редактировать объект
        Если user не передан, используем текущего пользователя из request
        """
        from django.contrib.auth.models import AnonymousUser
        
        # Если пользователь не передан, возвращаем False
        if user is None or isinstance(user, AnonymousUser):
            return False
        
        # Суперпользователь всегда может редактировать
        if user.is_superuser:
            return True
        
        # Контролер может редактировать только свои объекты в статусе draft или in_progress
        if user.groups.filter(name='Контролер').exists():
            if self.owner != user:
                return False
            return self.status in ['draft', 'in_progress']
        
        return False
    
    def is_editable(self):
        """Проверка, можно ли редактировать объект (без проверки пользователя)"""
        return self.status in ['draft', 'in_progress']
    
    def __str__(self):
        return f"{self.serial_number} - {self.title1 or 'Без названия'}"