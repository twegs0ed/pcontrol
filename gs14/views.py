# views.py
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.views.generic import ListView, DetailView
from django.views import View
from formtools.wizard.views import SessionWizardView
from .forms import SerialNumberForm, MainInfoForm
from .models import Control
import os
import time
import threading
import logging
from django.conf import settings
from django.db import transaction
import gc
import atexit

logger = logging.getLogger(__name__)

# Константы для имен шагов
FORM_SERIAL = '0'
FORM_MAIN = '1'

class MyWizard(SessionWizardView):
    form_list = [SerialNumberForm, MainInfoForm]
    
    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'wizard_temp'),
        base_url='/media/wizard_temp/'
    )
    
    condition_dict = {
        FORM_MAIN: True
    }
    
    serial_from_url = None
    is_edit_mode = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'wizard_temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self._clean_old_temp_files(temp_dir)
    
    def _clean_old_temp_files(self, temp_dir):
        """Очистка старых временных файлов"""
        try:
            current_time = time.time()
            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                if os.path.isfile(filepath):
                    if current_time - os.path.getmtime(filepath) > 3600:
                        os.remove(filepath)
                        logger.info(f"Удален старый временный файл: {filepath}")
        except Exception as e:
            logger.error(f"Ошибка очистки временных файлов: {e}")

    def dispatch(self, request, *args, **kwargs):
        """Перехватываем параметры URL перед обработкой запроса"""
        self.serial_from_url = kwargs.get('serial_number', None)
        
        if self.serial_from_url:
            self.is_edit_mode = True
            try:
                Control.objects.get(serial_number=self.serial_from_url)
                messages.info(request, f'Редактирование объекта с серийным номером {self.serial_from_url}')
            except Control.DoesNotExist:
                messages.error(request, f'Объект с серийным номером {self.serial_from_url} не найден')
                return redirect('gs14_control_list')
        else:
            self.is_edit_mode = False
        
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Обработка GET запроса с переходом на второй шаг при редактировании"""
        if 'cancel' in request.GET:
            self.storage.reset()
            messages.info(request, 'Операция отменена')
            return redirect('gs14_control_list')
        
        # Если это режим редактирования, сразу переходим на второй шаг
        if self.is_edit_mode and self.serial_from_url:
            if self.steps.current == FORM_SERIAL:
                self.storage.data[FORM_SERIAL] = {
                    'serial_number': self.serial_from_url
                }
                self.storage.current_step = FORM_MAIN
        
        return super().get(request, *args, **kwargs)

    def get_template_names(self):
        """Явно указываем шаблоны для каждого шага"""
        if self.steps.current == FORM_SERIAL:
            return ['forms/wizard_0.html']
        elif self.steps.current == FORM_MAIN:
            return ['forms/wizard_1.html']
        return ['forms/wizard_base.html']

    def get_form_initial(self, step):
        """Передача начальных данных для форм"""
        initial = super().get_form_initial(step)
        
        if step == FORM_SERIAL:
            if self.is_edit_mode and self.serial_from_url:
                initial['serial_number'] = self.serial_from_url
                
        elif step == FORM_MAIN:
            serial = self.serial_from_url
            if not serial:
                cleaned_serial_data = self.get_cleaned_data_for_step(FORM_SERIAL)
                serial = cleaned_serial_data.get('serial_number') if cleaned_serial_data else None
            
            if serial:
                try:
                    instance = Control.objects.get(serial_number=serial)
                    # Передаем ТОЛЬКО текстовые поля
                    initial.update({
                        'description': instance.description or '',
                        'title1': instance.title1 or '',
                        'title2': instance.title2 or '',
                        'title3': instance.title3 or '',
                        'title4': instance.title4 or '',
                        'title5': instance.title5 or '',
                        'title6': instance.title6 or '',
                        'title7': instance.title7 or '',
                    })
                    # НЕ передаем image поля в initial
                except Control.DoesNotExist:
                    pass
        
        return initial

    def get_form(self, step=None, data=None, files=None):
        """Кастомизация формы"""
        form = super().get_form(step, data, files)
        
        if step == FORM_SERIAL:
            if self.is_edit_mode and self.serial_from_url:
                if not data:
                    form.initial['serial_number'] = self.serial_from_url
                
                form.fields['serial_number'].widget.attrs['readonly'] = True
                form.fields['serial_number'].widget.attrs['class'] = 'form-control readonly-field'
                form.fields['serial_number'].help_text = '⚠️ Серийный номер нельзя изменить при редактировании'
                form.fields['serial_number'].required = False
        
        if step == FORM_MAIN:
            serial = self.serial_from_url
            if not serial:
                cleaned_serial_data = self.get_cleaned_data_for_step(FORM_SERIAL)
                serial = cleaned_serial_data.get('serial_number') if cleaned_serial_data else None
            
            if serial:
                try:
                    Control.objects.get(serial_number=serial)
                    # Делаем все поля необязательными
                    for field in form.fields.values():
                        field.required = False
                    
                    # Добавляем подсказки для всех полей
                    for field_name in form.fields:
                        if field_name.startswith('title'):
                            form.fields[field_name].help_text = "Необязательно - оставьте пустым для сохранения текущего значения"
                        elif field_name.startswith('image'):
                            form.fields[field_name].help_text = "Необязательно - оставьте пустым для сохранения текущего изображения"
                        elif field_name == 'description':
                            form.fields[field_name].help_text = "Необязательно - оставьте пустым для сохранения текущего значения"
                except Control.DoesNotExist:
                    pass
        
        return form

    def get_context_data(self, form, **kwargs):
        """Передача дополнительных данных в шаблон"""
        context = super().get_context_data(form, **kwargs)
        
        context['is_edit_mode'] = self.is_edit_mode
        context['serial_from_url'] = self.serial_from_url
        
        serial = self.serial_from_url
        if not serial:
            cleaned_data = self.get_cleaned_data_for_step(FORM_SERIAL)
            if cleaned_data:
                serial = cleaned_data.get('serial_number')
        
        context['serial_number'] = serial
        
        if serial:
            context['object_exists'] = Control.objects.filter(serial_number=serial).exists()
            
            # Добавляем информацию о существующих изображениях
            if self.is_edit_mode:
                try:
                    obj = Control.objects.get(serial_number=serial)
                    context['current_images'] = {
                        'image1': obj.image1.url if obj.image1 else None,
                        'image2': obj.image2.url if obj.image2 else None,
                        'image3': obj.image3.url if obj.image3 else None,
                        'image4': obj.image4.url if obj.image4 else None,
                        'image5': obj.image5.url if obj.image5 else None,
                        'image6': obj.image6.url if obj.image6 else None,
                        'image7': obj.image7.url if obj.image7 else None,
                    }
                    # Добавляем флаги существования изображений
                    context['has_images'] = {
                        'image1': bool(obj.image1),
                        'image2': bool(obj.image2),
                        'image3': bool(obj.image3),
                        'image4': bool(obj.image4),
                        'image5': bool(obj.image5),
                        'image6': bool(obj.image6),
                        'image7': bool(obj.image7),
                    }
                except Control.DoesNotExist:
                    pass
        else:
            context['object_exists'] = False
        
        return context

    def process_step(self, form):
        """Дополнительная валидация на шаге"""
        if self.steps.current == FORM_SERIAL:
            cleaned_data = form.cleaned_data
            serial = cleaned_data.get('serial_number')
            
            if self.is_edit_mode and serial and serial != self.serial_from_url:
                form.add_error(
                    'serial_number', 
                    'При редактировании нельзя изменить серийный номер'
                )
        
        if self.steps.current == FORM_MAIN:
            # Проверка всех загруженных изображений
            image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
            for field_name in image_fields:
                image = form.cleaned_data.get(field_name)
                if image:
                    if image.size > 5 * 1024 * 1024:
                        form.add_error(field_name, 'Размер файла не должен превышать 5MB')
                    
                    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                    ext = os.path.splitext(image.name)[1].lower()
                    if ext not in valid_extensions:
                        form.add_error(field_name, 'Разрешены только изображения: JPG, PNG, GIF')
        
        return super().process_step(form)

    def delete_temp_file_later(self, file_path):
        """Отложенное удаление временного файла"""
        def delete_file():
            time.sleep(2)
            try:
                if os.path.exists(file_path):
                    gc.collect()
                    os.remove(file_path)
                    logger.info(f"Временный файл удален: {file_path}")
            except Exception as e:
                logger.error(f"Не удалось удалить файл {file_path}: {e}")
                atexit.register(lambda: self._safe_delete(file_path))
        
        thread = threading.Thread(target=delete_file, daemon=True)
        thread.start()

    def _safe_delete(self, file_path):
        """Запасной метод удаления"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

    def done(self, form_list, form_dict, **kwargs):
        """Сохранение данных в базу"""
        try:
            serial_form_data = form_dict[FORM_SERIAL].cleaned_data
            main_form_data = form_dict[FORM_MAIN].cleaned_data
            
            serial = self.serial_from_url if self.is_edit_mode else serial_form_data.get('serial_number')
            
            if not serial:
                messages.error(self.request, 'Серийный номер обязателен')
                return redirect('gs14_control_list')
            
            with transaction.atomic():
                existing_obj = Control.objects.filter(serial_number=serial).first()
                
                # Список всех полей
                text_fields = ['description', 'title1', 'title2', 'title3', 'title4', 'title5', 'title6', 'title7']
                image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
                
                # Подготовка данных для обновления
                update_data = {}
                
                # Текстовые поля - обновляем только если есть значение
                for field in text_fields:
                    value = main_form_data.get(field)
                    if value is not None:
                        update_data[field] = value.strip() if value else ''
                
                # Поля изображений
                for field in image_fields:
                    uploaded_file = main_form_data.get(field)
                    if uploaded_file:
                        # Если загружено новое изображение
                        if existing_obj and getattr(existing_obj, field):
                            try:
                                old_path = getattr(existing_obj, field).path
                                if os.path.exists(old_path):
                                    os.remove(old_path)
                                    logger.info(f"Удалено старое изображение: {old_path}")
                            except Exception as e:
                                logger.warning(f"Не удалось удалить старое изображение: {e}")
                        update_data[field] = uploaded_file
                    elif existing_obj:
                        # Сохраняем существующее изображение
                        update_data[field] = getattr(existing_obj, field)
                    else:
                        update_data[field] = None
                
                # Создаем или обновляем объект
                obj, created = Control.objects.update_or_create(
                    serial_number=serial,
                    defaults=update_data
                )
                
                # Удаляем временные файлы
                for field in image_fields:
                    uploaded_file = main_form_data.get(field)
                    if uploaded_file and hasattr(uploaded_file, 'path'):
                        temp_file_path = uploaded_file.path
                        if os.path.exists(temp_file_path):
                            self.delete_temp_file_later(temp_file_path)
                
                if created:
                    messages.success(self.request, f'Новый объект с серийным номером {serial} успешно создан.')
                else:
                    messages.success(self.request, f'Данные для объекта с серийным номером {serial} успешно обновлены.')
                
                return redirect('gs14_control_list')
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных: {e}")
            messages.error(self.request, f'Произошла ошибка при сохранении данных: {str(e)}')
            return redirect('gs14_control_list')


class ControlListView(ListView):
    """Список всех объектов Control"""
    model = Control
    template_name = 'controls/control_list.html'
    context_object_name = 'controls'
    ordering = ['-created_at']
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список объектов Control'
        context['total_count'] = Control.objects.count()
        return context


class ControlDetailView(DetailView):
    """Детальная страница объекта Control"""
    model = Control
    template_name = 'controls/control_detail.html'
    context_object_name = 'control'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Объект {self.object.serial_number}'
        return context


class ControlDeleteView(View):
    """Удаление объекта через POST запрос"""
    def post(self, request, pk):
        try:
            control = get_object_or_404(Control, pk=pk)
            serial = control.serial_number
            
            # Удаляем все изображения
            image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
            for field in image_fields:
                if getattr(control, field):
                    try:
                        old_path = getattr(control, field).path
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            logger.info(f"Удалено изображение: {old_path}")
                    except Exception as e:
                        logger.warning(f"Не удалось удалить изображение: {e}")
            
            control.delete()
            
            messages.success(request, f'Объект с серийным номером {serial} успешно удален.')
            return redirect('gs14_control_list')
            
        except Control.DoesNotExist:
            messages.error(request, f'Объект с ID {pk} не найден')
            return redirect('gs14_control_list')
            
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            logger.error(f"Ошибка удаления объекта {pk}: {e}")
            return redirect('gs14_control_list')