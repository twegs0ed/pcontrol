from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def get_control_upload_path(instance, filename):
    import os
    from django.utils.text import slugify
    import uuid
    from django.utils import timezone as django_timezone

    ext = os.path.splitext(filename)[1].lower()
    timestamp = django_timezone.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    name = slugify(os.path.splitext(filename)[0]) or 'photo'
    new_filename = f"{name}_{timestamp}_{unique_id}{ext}"

    return os.path.join('controls', new_filename)


class ControlRecord(models.Model):
    controller = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='control_records',
        verbose_name='Контролер'
    )
    worker = models.CharField(
        max_length=200,
        verbose_name='ФИО рабочего'
    )
    batch_size = models.PositiveIntegerField(
        verbose_name='Количество предъявленных деталей',
        default=100
    )
    rejected_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество забракованных деталей',
        help_text='Автоматически рассчитывается'
    )
    control_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время контроля'
    )
    shift_photo = models.ImageField(
        upload_to=get_control_upload_path,
        blank=True,
        null=True,
        verbose_name='Фото сменного задания'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания'
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
        verbose_name = 'Запись контроля детали'
        verbose_name_plural = 'Записи контроля деталей'
        ordering = ['-control_date']

    def __str__(self):
        return f"{self.controller.get_full_name() or self.controller.username} - {self.worker} ({self.control_date.strftime('%d.%m.%Y %H:%M')})"

    def calculate_rejected(self):
        rejected = 0
        for group in self.groups.all():
            for dim in group.dimensions.all():
                if dim.is_acceptable is False:
                    rejected += 1
                    break
        self.rejected_count = rejected
        self.save(update_fields=['rejected_count'])
        return rejected

    def get_min_dimensions(self):
        return max(5, int(self.batch_size * 0.05))

    def get_total_dimensions(self):
        return self.groups.aggregate(
            total=models.Count('dimensions')
        )['total'] or 0

    @property
    def all_dimensions(self):
        """Возвращает все размеры через группы (для обратной совместимости)."""
        dims = []
        for group in self.groups.prefetch_related('dimensions').all():
            dims.extend(list(group.dimensions.all()))
        return dims


class DimensionGroup(models.Model):
    control_record = models.ForeignKey(
        ControlRecord,
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='Запись контроля'
    )
    group_number = models.PositiveIntegerField(
        verbose_name='Номер группы'
    )

    class Meta:
        verbose_name = 'Группа измерений'
        verbose_name_plural = 'Группы измерений'
        ordering = ['group_number']
        unique_together = [('control_record', 'group_number')]

    def __str__(self):
        return f"Группа {self.group_number} - Деталь {self.control_record.worker}"


class DimensionRecord(models.Model):
    group = models.ForeignKey(
        DimensionGroup,
        on_delete=models.CASCADE,
        related_name='dimensions',
        verbose_name='Группа измерений'
    )
    detail_number = models.PositiveIntegerField(
        verbose_name='Номер детали'
    )
    dimension_number = models.PositiveIntegerField(
        verbose_name='Номер размера'
    )
    value = models.CharField(
        max_length=50,
        verbose_name='Значение размера'
    )
    tolerance = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Допуск'
    )
    is_acceptable = models.BooleanField(
        default=True,
        verbose_name='Принимаемый'
    )

    class Meta:
        verbose_name = 'Измеренный размер'
        verbose_name_plural = 'Измеренные размеры'
        ordering = ['detail_number', 'dimension_number']
        unique_together = [('group', 'dimension_number')]

    def __str__(self):
        return f"Деталь {self.detail_number}, размер {self.dimension_number}: {self.value}"
