# unified_products/models.py
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
    
    # Определяем папку
    if hasattr(instance, 'product') and instance.product and instance.product.category:
        folder = f'products/{instance.product.category.id}'
    else:
        folder = 'products'
    
    return os.path.join(folder, new_filename)


class Category(models.Model):
    """
    Таблица категорий изделий
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название категории'
    )
    prefix = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Префикс серийного номера',
        help_text='Первые цифры серийного номера, например: 123, 4567'
    )
    image_count = models.PositiveIntegerField(
        default=7,
        verbose_name='Количество изображений',
        help_text='Количество фотографий, которые нужно загрузить для изделия'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
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
        verbose_name = 'Категория изделия'
        verbose_name_plural = 'Категории изделий'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (префикс: {self.prefix})"
    
    def get_image_fields(self):
        """Возвращает список названий полей для изображений"""
        return [f'image_{i}' for i in range(1, self.image_count + 1)]
    
    def get_title_fields(self):
        """Возвращает список названий полей для заголовков"""
        return [f'title_{i}' for i in range(1, self.image_count + 1)]


class Product(models.Model):
    """
    Основная таблица изделий
    """
    # === Связи ===
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='Категория'
    )
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='unified_products',
        verbose_name='Владелец',
        null=True,
        blank=True
    )
    
    closed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_unified_products',
        verbose_name='Закрыл'
    )
    
    # === Основная информация ===
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Серийный номер',
        db_index=True
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
    
    # === Образец ===
    is_sample = models.BooleanField(
        default=False,
        verbose_name='Образец',
        help_text='Отметьте, чтобы сделать этот объект образцом (только для администратора)'
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
        verbose_name = 'Изделие'
        verbose_name_plural = 'Изделия'
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_products", "Может просматривать все изделия"),
            ("can_edit_all_products", "Может редактировать все изделия"),
            ("can_delete_all_products", "Может удалять все изделия"),
        ]

    def __str__(self):
        return f"{self.serial_number} - {self.category.name}"

    def is_completed(self):
        """Проверка, заполнены ли все фото"""
        images = self.images.all()
        required_count = self.category.image_count
        filled_count = images.filter(image__isnull=False).exclude(image='').count()
        return filled_count >= required_count
    
    def get_filled_count(self):
        """Возвращает количество загруженных фото"""
        return self.images.filter(image__isnull=False).exclude(image='').count()
    
    def get_total_required(self):
        """Возвращает общее количество требуемых фото"""
        return self.category.image_count
    
    def get_progress_percent(self):
        """Возвращает процент заполнения"""
        total = self.get_total_required()
        if total == 0:
            return 0
        filled = self.get_filled_count()
        return int((filled / total) * 100)
    
    def check_and_update_status(self):
        """Проверка и обновление статуса"""
        if self.is_completed() and self.status != 'closed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save(update_fields=['status', 'completed_at'])
            return True
        return False
    
    def can_edit(self, user=None):
        """Проверка, может ли пользователь редактировать объект"""
        if user is None or isinstance(user, AnonymousUser):
            return False
        
        if user.is_superuser:
            return True
        
        if self.owner == user:
            return self.status in ['draft', 'in_progress']
        
        if user.groups.filter(name='Контролер').exists():
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
        if user is None or isinstance(user, AnonymousUser):
            return False
        
        if user.is_superuser:
            return True
        
        if user.groups.filter(name='Аудитор').exists():
            return True
        
        if user.groups.filter(name='Контролер').exists():
            return self.owner == user
        
        return False
    def get_absolute_url(self):
        """Возвращает URL для просмотра объекта"""
        from django.urls import reverse
        return reverse('unified_products:product_detail', kwargs={'pk': self.pk})
    
    def get_edit_url(self):
        """Возвращает URL для редактирования объекта"""
        from django.urls import reverse
        return reverse('unified_products:product_edit', kwargs={'serial_number': self.serial_number})


class ProductImage(models.Model):
    """
    Таблица изображений изделия
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Изделие'
    )
    field_index = models.PositiveIntegerField(
        verbose_name='Номер поля'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Заголовок'
    )
    image = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name='Изображение'
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
        verbose_name = 'Изображение изделия'
        verbose_name_plural = 'Изображения изделий'
        ordering = ['product', 'field_index']
        unique_together = ['product', 'field_index']

    def __str__(self):
        return f"{self.product.serial_number} - поле {self.field_index}"