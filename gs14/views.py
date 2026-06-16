# views.py
from django.shortcuts import redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.views.generic import ListView, DetailView
from formtools.wizard.views import SessionWizardView
from .forms import SerialNumberForm, MainInfoForm
from .models import Control
import os
import time
import threading
from django.conf import settings

# Константы для имен шагов
FORM_SERIAL = '0'
FORM_MAIN = '1'

class MyWizard(SessionWizardView):
    # Список форм в порядке следования
    form_list = [SerialNumberForm, MainInfoForm]
    
    # Временное хранилище для файлов
    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'wizard_temp'),
        base_url='/media/wizard_temp/'
    )
    
    # Условия показа шагов
    condition_dict = {
        FORM_MAIN: True
    }

    def get_template_names(self):
        """Явно указываем шаблоны для каждого шага"""
        if self.steps.current == FORM_SERIAL:
            return ['forms/wizard_0.html']
        elif self.steps.current == FORM_MAIN:
            return ['forms/wizard_1.html']
        return ['forms/wizard_base.html']

    def get_form_initial(self, step):
        """
        Передача начальных данных для формы второго шага
        """
        initial = super().get_form_initial(step)
        
        if step == FORM_MAIN:
            # Получаем серийный номер из первого шага
            cleaned_serial_data = self.get_cleaned_data_for_step(FORM_SERIAL)
            serial = cleaned_serial_data.get('serial_number') if cleaned_serial_data else None

            if serial:
                try:
                    # Ищем объект в базе
                    instance = Control.objects.get(serial_number=serial)
                    # Подставляем существующие данные
                    initial.update({
                        'description': instance.description or '',
                        'title1': instance.title1 or '',
                        'image1': instance.image1,
                    })
                    messages.info(self.request, f'Найден объект с номером {serial}. Вы можете изменить данные ниже.')
                except Control.DoesNotExist:
                    messages.warning(self.request, f'Объект с номером {serial} не найден. Пожалуйста, заполните все поля.')
        
        return initial

    def get_form(self, step=None, data=None, files=None):
        """
        Кастомизация формы на втором шаге
        """
        form = super().get_form(step, data, files)
        
        if step == FORM_MAIN:
            # Получаем серийный номер
            cleaned_serial_data = self.get_cleaned_data_for_step(FORM_SERIAL)
            serial = cleaned_serial_data.get('serial_number') if cleaned_serial_data else None

            if serial:
                try:
                    # Проверяем существование объекта
                    Control.objects.get(serial_number=serial)
                    # Если объект существует, делаем все поля НЕ обязательными
                    for field in form.fields.values():
                        field.required = False
                except Control.DoesNotExist:
                    # Если объект новый - поля остаются обязательными
                    pass
        
        return form

    def get_context_data(self, form, **kwargs):
        """
        Передача дополнительных данных в шаблон
        """
        context = super().get_context_data(form, **kwargs)
        
        # Получаем серийный номер из первого шага
        cleaned_data = self.get_cleaned_data_for_step(FORM_SERIAL)
        
        if cleaned_data:
            serial_number = cleaned_data.get('serial_number')
            context['serial_number'] = serial_number
            
            # Проверяем существует ли объект в базе
            if serial_number:
                context['object_exists'] = Control.objects.filter(serial_number=serial_number).exists()
            else:
                context['object_exists'] = False
        else:
            # Пробуем получить из storage (альтернативный способ)
            if FORM_SERIAL in self.storage.data:
                serial_number = self.storage.data[FORM_SERIAL].get('serial_number')
                context['serial_number'] = serial_number
                context['object_exists'] = Control.objects.filter(serial_number=serial_number).exists() if serial_number else False
            else:
                context['serial_number'] = None
                context['object_exists'] = False
        
        return context

    def delete_temp_file_later(self, file_path):
        """
        Отложенное удаление временного файла
        """
        def delete_file():
            time.sleep(1)  # Даем время Django завершить работу с файлом
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Временный файл удален: {file_path}")
            except Exception as e:
                print(f"Не удалось удалить файл {file_path}: {e}")
        
        thread = threading.Thread(target=delete_file)
        thread.daemon = True
        thread.start()

    def done(self, form_list, form_dict, **kwargs):
        """
        Сохранение данных в базу
        """
        # Получаем данные из всех форм
        serial_form_data = form_dict[FORM_SERIAL].cleaned_data
        main_form_data = form_dict[FORM_MAIN].cleaned_data
        serial = serial_form_data.get('serial_number')

        # Получаем загруженный файл
        uploaded_image = main_form_data.get('image1')
        
        # Сохраняем путь к временному файлу
        temp_file_path = None
        if uploaded_image and hasattr(uploaded_image, 'path'):
            temp_file_path = uploaded_image.path

        # Получаем существующий объект (если есть)
        try:
            existing_obj = Control.objects.get(serial_number=serial)
            created = False
        except Control.DoesNotExist:
            existing_obj = None
            created = True
        
        # Подготовка данных для сохранения
        defaults = {
            'description': main_form_data.get('description', '') or '',
            'title1': main_form_data.get('title1', '') or '',
            'image1': uploaded_image if uploaded_image else (existing_obj.image1 if existing_obj else None),
        }
        
        # Создаем или обновляем объект
        obj, created = Control.objects.update_or_create(
            serial_number=serial,
            defaults=defaults
        )
        
        # Удаляем временный файл
        if temp_file_path and os.path.exists(temp_file_path):
            self.delete_temp_file_later(temp_file_path)

        # Сообщения пользователю
        if created:
            messages.success(self.request, f'Новый объект с серийным номером {serial} успешно создан.')
        else:
            messages.success(self.request, f'Данные для объекта с серийным номером {serial} успешно обновлены.')
        
        # Перенаправляем на список объектов
        return redirect('control_list')


class ControlListView(ListView):
    """
    Список всех объектов Control
    """
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
    """
    Детальная страница объекта Control
    """
    model = Control
    template_name = 'controls/control_detail.html'
    context_object_name = 'control'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Объект {self.object.serial_number}'
        return context