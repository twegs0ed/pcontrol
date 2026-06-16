# models.py
from django.db import models

class Control(models.Model):
    serial_number = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='Серийный номер',
        db_index=True
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
        verbose_name='Заголовок 1'
    )
    image1 = models.ImageField(
        upload_to='controls/', 
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
        verbose_name = 'Контроль'
        verbose_name_plural = 'Контроли'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.serial_number} - {self.title1 or 'Без названия'}"