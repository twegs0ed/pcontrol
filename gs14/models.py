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
    
    class Meta:
        verbose_name = 'Контроль'
        verbose_name_plural = 'Контроли'
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_controls", "Может просматривать все объекты"),
            ("can_edit_all_controls", "Может редактировать все объекты"),
            ("can_delete_all_controls", "Может удалять все объекты"),
        ]
    
    def __str__(self):
        return f"{self.serial_number} - {self.title1 or 'Без названия'}"