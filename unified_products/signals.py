# unified_products/signals.py
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Category, Product, ProductImage
import os
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Product)
def create_product_images(sender, instance, created, **kwargs):
    """Создает изображения для нового продукта"""
    if created:
        logger.info(f"Создание изображений для продукта {instance.serial_number}")
        for i in range(1, instance.category.image_count + 1):
            ProductImage.objects.create(
                product=instance,
                field_index=i
            )
        logger.info(f"Создано {instance.category.image_count} изображений")


@receiver(pre_save, sender=Product)
def ensure_only_one_sample(sender, instance, **kwargs):
    """
    Гарантирует, что только один объект может быть образцом в каждой категории
    """
    if instance.is_sample:
        # Если текущий объект становится образцом
        # Снимаем отметку "образец" со всех других объектов в этой категории
        Product.objects.filter(
            category=instance.category,
            is_sample=True
        ).exclude(pk=instance.pk).update(is_sample=False)
        logger.info(f"Объект {instance.serial_number} установлен как образец в категории {instance.category.name}")


@receiver(pre_delete, sender=Product)
def delete_product_images(sender, instance, **kwargs):
    """Удаляет файлы изображений при удалении продукта"""
    for image in instance.images.all():
        if image.image and os.path.exists(image.image.path):
            try:
                os.remove(image.image.path)
                logger.info(f"Удалено изображение: {image.image.path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить изображение: {e}")


@receiver(pre_delete, sender=Category)
def delete_category_files(sender, instance, **kwargs):
    """Удаляет файлы при удалении категории"""
    for product in instance.products.all():
        for image in product.images.all():
            if image.image and os.path.exists(image.image.path):
                try:
                    os.remove(image.image.path)
                except:
                    pass


@receiver(post_save, sender=Category)
def update_product_images_on_category_change(sender, instance, **kwargs):
    """
    Обновляет количество изображений у продуктов при изменении категории
    """
    # Проверяем, изменилось ли количество изображений
    if hasattr(instance, '_image_count_old'):
        old_count = instance._image_count_old
        new_count = instance.image_count
        
        if old_count != new_count:
            logger.info(f"Изменение количества изображений: {old_count} -> {new_count}")
            
            # Обновляем продукты
            for product in instance.products.all():
                current_count = ProductImage.objects.filter(product=product).count()
                
                if current_count < new_count:
                    # Добавляем недостающие поля
                    for i in range(current_count + 1, new_count + 1):
                        ProductImage.objects.create(
                            product=product,
                            field_index=i
                        )
                    logger.info(f"Добавлено {new_count - current_count} полей для {product.serial_number}")
                elif current_count > new_count:
                    # Удаляем лишние поля
                    ProductImage.objects.filter(
                        product=product,
                        field_index__gt=new_count
                    ).delete()
                    logger.info(f"Удалено {current_count - new_count} полей для {product.serial_number}")