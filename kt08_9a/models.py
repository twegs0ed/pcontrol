# kt08_9a/models.py
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
    return os.path.join('kt08_9a/', new_filename)

class KT08_9a(models.Model):
    serial_number = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='Серийный номер',
        db_index=True
    )
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='kt08_9a_controls',
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
    
    # Группа 1: Вид внутри сзади
    title1 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид внутри сзади'
    )
    image1 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида внутри сзади'
    )

    # Группа 2: Крышка внутри
    title2 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Крышка внутри'
    )
    image2 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото крышки внутри'
    )

    # Группа 3: Вид внутри сверху
    title3 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид внутри сверху'
    )
    image3 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида внутри сверху'
    )

    # Группа 4: Вид сзади
    title4 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид сзади'
    )
    image4 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида сзади'
    )

    # Группа 5: Вид справа
    title5 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид справа'
    )
    image5 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида справа'
    )

    # Группа 6: Вид спереди
    title6 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид спереди'
    )
    image6 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида спереди'
    )

    # Группа 7: Вид слева
    title7 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид слева'
    )
    image7 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото вида слева'
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
        verbose_name = 'KT08_9a'
        verbose_name_plural = 'KT08_9a'
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_kt08_9a", "Может просматривать все объекты KT08_9a"),
            ("can_edit_all_kt08_9a", "Может редактировать все объекты KT08_9a"),
            ("can_delete_all_kt08_9a", "Может удалять все объекты KT08_9a"),
        ]
    
    def __str__(self):
        return f"{self.serial_number} - {self.title1 or 'Без названия'}"