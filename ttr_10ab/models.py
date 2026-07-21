from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.utils import timezone
import os
from django.utils.text import slugify
import uuid


def get_upload_path(instance, filename):
    """Генерация пути для загрузки файлов"""
    ext = os.path.splitext(filename)[1].lower()
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    name = slugify(os.path.splitext(filename)[0]) or 'image'
    new_filename = f"{name}_{timestamp}_{unique_id}{ext}"
    return os.path.join('ttr_10ab/', new_filename)


class TTR10AB(models.Model):
    """Модель для объектов TTR-10AB"""
    
    # === Основная информация ===
    serial_number = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='Серийный номер',
        db_index=True
    )
    serial_photo = models.ImageField(
        upload_to='serial_photos/',
        blank=True,
        null=True,
        verbose_name="Фото серийного номера"
    )
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ttr_10ab_controls',
        verbose_name='Владелец',
        null=True,
        blank=True
    )
    
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Описание'
    )
    
    # === Статус ===
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
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершения'
    )
    
    closed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_ttr_10ab',
        verbose_name='Закрыл'
    )
    
    is_sample = models.BooleanField(
        default=False,
        verbose_name='Образец (только для администратора)',
        help_text='Отметьте, чтобы сделать эту модель образцом'
    )
    
    # === Группа 1: Механизм вид сверху ===
    title1 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Механизм вид сверху'
    )
    image1 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото механизма вид сверху'
    )

    # === Группа 2: Механизм вид справа ===
    title2 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Механизм вид справа'
    )
    image2 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото механизма вид справа'
    )

    # === Группа 3: Механизм вид слева ===
    title3 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Механизм вид слева'
    )
    image3 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото механизма вид слева'
    )

    # === Группа 4: Турникет вид сверху ===
    title4 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Турникет вид сверху'
    )
    image4 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото турникета вид сверху'
    )

    # === Группа 5: Турникет вид слева ===
    title5 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Турникет вид слева'
    )
    image5 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото турникета вид слева'
    )

    # === Группа 6: Турникет вид справа ===
    title6 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Турникет вид справа'
    )
    image6 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото турникета вид справа'
    )

    # === Группа 7: Турникет вид сзади ===
    title7 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Турникет вид сзади'
    )
    image7 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото турникета вид сзади'
    )

    # === Группа 8: Комплектность ===
    title8 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Комплектность'
    )
    image8 = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото комплектности'
    )

    # === Системная информация ===
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'TTR-10AB'
        verbose_name_plural = 'TTR-10AB'
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_ttr_10ab", "Может просматривать все объекты TTR-10AB"),
            ("can_edit_all_ttr_10ab", "Может редактировать все объекты TTR-10AB"),
            ("can_delete_all_ttr_10ab", "Может удалять все объекты TTR-10AB"),
        ]
    
    def __str__(self):
        return f"{self.serial_number} - {self.title1 or 'Без названия'}"
    
    # === Методы для работы со статусом ===
    
    def is_completed(self):
        """Проверка, заполнены ли все фото (8 полей)"""
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'image8']
        for field in image_fields:
            if not getattr(self, field):
                return False
        return True
    
    def get_filled_count(self):
        """Возвращает количество загруженных фото"""
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'image8']
        count = 0
        for field in image_fields:
            if getattr(self, field):
                count += 1
        return count
    
    def check_and_update_status(self):
        """Проверка и обновление статуса"""
        if self.is_completed() and self.status != 'closed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            return True
        return False
    
    # === Методы для проверки прав ===
    
    def can_edit(self, user=None):
        """
        Проверка, может ли пользователь редактировать объект
        """
        from django.contrib.auth.models import AnonymousUser
        
        # Если пользователь не передан или аноним
        if user is None or isinstance(user, AnonymousUser):
            return False
        
        # Суперпользователь всегда может редактировать
        if user.is_superuser:
            return True
        
        # Если пользователь является владельцем объекта - разрешаем
        # НЕЗАВИСИМО ОТ ГРУППЫ!
        if self.owner == user:
            return self.status in ['draft', 'in_progress']
        
        # Проверяем группу Контролер (для редактирования чужих объектов)
        if user.groups.filter(name='Контролер').exists():
            # Контролер может редактировать только если он владелец
            # (уже проверено выше) или если объект без владельца
            if self.owner is None:
                return self.status in ['draft', 'in_progress']
            return False
        
        return False
    
    def can_delete(self, user=None):
        """Проверка, может ли пользователь удалить объект"""
        if user is None:
            return False
        
        if isinstance(user, AnonymousUser):
            return False
        
        return user.is_superuser
    
    def can_view(self, user=None):
        """Проверка, может ли пользователь просматривать объект"""
        if user is None:
            return False
        
        if isinstance(user, AnonymousUser):
            return False
        
        if user.is_superuser:
            return True
        
        if user.groups.filter(name='Аудитор').exists():
            return True
        
        if user.groups.filter(name='Контролер').exists():
            return self.owner == user
        
        return False
    
    # === Методы для работы с изображениями ===
    
    def get_all_images(self):
        """Возвращает список всех загруженных изображений"""
        images = []
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'image8']
        title_fields = ['title1', 'title2', 'title3', 'title4', 'title5', 'title6', 'title7', 'title8']
        for field, title_field in zip(image_fields, title_fields):
            image = getattr(self, field)
            if image:
                images.append({
                    'field': field,
                    'title': getattr(self, title_field) or field.replace('image', 'Группа '),
                    'url': image.url,
                    'path': image.path
                })
        return images
    
    def get_image_count(self):
        """Возвращает количество загруженных изображений"""
        return self.get_filled_count()
    
    def delete_all_images(self):
        """Удаляет все изображения объекта"""
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'image8']
        for field in image_fields:
            image = getattr(self, field)
            if image:
                try:
                    if os.path.exists(image.path):
                        os.remove(image.path)
                except Exception as e:
                    print(f"Ошибка удаления {field}: {e}")
                setattr(self, field, None)
        self.save()