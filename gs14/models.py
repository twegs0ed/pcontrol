# models.py
from django.db import models
from webcampicture.fields import WebcamPictureField

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
    
    # Вид внутри
    title1 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид внутри'
    )
    image1 = WebcamPictureField(
        upload_to='controls/',
        blank=True,
        null=True,
        verbose_name='Фото вида внутри'
    )

    # Вид платы
    title2 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид платы'
    )
    image2 = WebcamPictureField(
        upload_to='controls/',
        blank=True,
        null=True,
        verbose_name='Фото вида платы'
    )

    # Вид спереди
    title3 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид спереди'
    )
    image3 = WebcamPictureField(
        upload_to='controls/',
        blank=True,
        null=True,
        verbose_name='Фото вида спереди'
    )

    # Вид справа
    title4 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид справа'
    )
    image4 = WebcamPictureField(
        upload_to='controls/',
        blank=True,
        null=True,
        verbose_name='Фото вида справа'
    )

    # Вид слева
    title5 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид слева'
    )
    image5 = WebcamPictureField(
        upload_to='controls/',
        blank=True,
        null=True,
        verbose_name='Фото вида слева'
    )

    # Вид сзади
    title6 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Вид сзади'
    )
    image6 = WebcamPictureField(
        upload_to='controls/',
        blank=True,
        null=True,
        verbose_name='Фото вида сзади'
    )

    # Комплектность - ИСПРАВЛЕНО: теперь title7 и image7
    title7 = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Комплектность'
    )
    image7 = WebcamPictureField(
        upload_to='controls/',
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
    
    def __str__(self):
        return f"{self.serial_number} - {self.title1 or 'Без названия'}"