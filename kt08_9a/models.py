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
    return os.path.join('kt08_9a/', new_filename)


class KT08_9a(models.Model):
    """Модель для объектов KT08_9a"""
    
    # === Основная информация ===
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
        related_name='closed_kt08_9a',
        verbose_name='Закрыл'
    )
    
    # === Группа 1: Вид внутри сзади ===
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

    # === Группа 2: Крышка внутри ===
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

    # === Группа 3: Вид внутри сверху ===
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

    # === Группа 4: Вид сзади ===
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

    # === Группа 5: Вид справа ===
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

    # === Группа 6: Вид спереди ===
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

    # === Группа 7: Вид слева ===
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
    
    # === Методы для работы со статусом ===
    
    def is_completed(self):
        """Проверка, заполнены ли все фото"""
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
        for field in image_fields:
            if not getattr(self, field):
                return False
        return True
    
    def get_filled_count(self):
        """Возвращает количество загруженных фото"""
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
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
        
        Аргументы:
            user: Объект пользователя Django
        
        Возвращает:
            bool: True если пользователь может редактировать, иначе False
        """
        # Если пользователь не передан
        if user is None:
            return False
        
        # Анонимный пользователь не может редактировать
        if isinstance(user, AnonymousUser):
            return False
        
        # Суперпользователь всегда может редактировать
        if user.is_superuser:
            return True
        
        # Проверяем, что пользователь в группе "Контролер"
        is_controller = user.groups.filter(name='Контролер').exists()
        
        # Если не контролер и не суперпользователь
        if not is_controller:
            return False
        
        # Проверяем, что пользователь - владелец объекта
        if self.owner != user:
            return False
        
        # Разрешаем редактирование только для статусов draft и in_progress
        if self.status not in ['draft', 'in_progress']:
            return False
        
        return True
    
    def can_delete(self, user=None):
        """
        Проверка, может ли пользователь удалить объект
        
        Аргументы:
            user: Объект пользователя Django
        
        Возвращает:
            bool: True если пользователь может удалить, иначе False
        """
        if user is None:
            return False
        
        if isinstance(user, AnonymousUser):
            return False
        
        # Только суперпользователь может удалять
        return user.is_superuser
    
    def can_view(self, user=None):
        """
        Проверка, может ли пользователь просматривать объект
        
        Аргументы:
            user: Объект пользователя Django
        
        Возвращает:
            bool: True если пользователь может просматривать, иначе False
        """
        if user is None:
            return False
        
        if isinstance(user, AnonymousUser):
            return False
        
        # Суперпользователь и аудитор видят все
        if user.is_superuser:
            return True
        
        if user.groups.filter(name='Аудитор').exists():
            return True
        
        # Контролер видит только свои объекты
        if user.groups.filter(name='Контролер').exists():
            return self.owner == user
        
        return False
    
    # === Методы для работы с изображениями ===
    
    def get_all_images(self):
        """Возвращает список всех загруженных изображений"""
        images = []
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
        for field in image_fields:
            image = getattr(self, field)
            if image:
                images.append({
                    'field': field,
                    'title': getattr(self, field.replace('image', 'title')),
                    'url': image.url,
                    'path': image.path
                })
        return images
    
    def get_image_count(self):
        """Возвращает количество загруженных изображений"""
        return self.get_filled_count()
    
    def delete_all_images(self):
        """Удаляет все изображения объекта"""
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
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