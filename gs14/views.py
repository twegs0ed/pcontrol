# gs14/views.py
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import models
from django.utils import timezone
from .forms import ControlForm
from .models import Control
import os, sys
import logging
import re
from PIL import Image, ImageEnhance
import pytesseract
import tempfile
import time


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


logger = logging.getLogger(__name__)

# Указываем путь к Tesseract
if sys.platform == 'win32':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
elif sys.platform == 'linux':  # Linux
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
elif sys.platform == 'darwin':  # macOS
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'


# === ДЕКОРАТОРЫ ДЛЯ ПРОВЕРКИ ПРАВ ===

def controller_required(view_func):
    """Декоратор для проверки, что пользователь в группе Контролер"""
    def wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if not request.user.groups.filter(name='Контролер').exists():
            messages.error(request, 'У вас нет прав для выполнения этого действия')
            return redirect('gs14:control_list')
        return view_func(request, *args, **kwargs)
    return wrapped


def auditor_required(view_func):
    """Декоратор для проверки, что пользователь в группе Аудитор"""
    def wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if not request.user.groups.filter(name='Аудитор').exists():
            messages.error(request, 'У вас нет прав для выполнения этого действия')
            return redirect('gs14:control_list')
        return view_func(request, *args, **kwargs)
    return wrapped


class ControlListView(LoginRequiredMixin, ListView):
    """Список объектов Control с учетом прав"""
    model = Control
    template_name = 'common/list.html'
    context_object_name = 'controls'
    ordering = ['-created_at']
    paginate_by = 10
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Фильтр по статусу
        status_filter = self.request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        # Поиск
        search_query = self.request.GET.get('search')
        if search_query:
            qs = qs.filter(
                models.Q(serial_number__icontains=search_query) |
                models.Q(title1__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        
        # Суперпользователь видит все
        if self.request.user.is_superuser:
            return qs
        
        # Аудитор видит все
        if self.request.user.groups.filter(name='Аудитор').exists():
            return qs
        
        # Контролер видит только свои
        if self.request.user.groups.filter(name='Контролер').exists():
            return qs.filter(owner=self.request.user)
        
        return qs.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список объектов GS14'
        context['total_count'] = self.get_queryset().count()
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        context['app_name'] = 'GS14'
        context['app_icon'] = 'fa-microchip'
        context['namespace'] = 'gs14'
        context['primary_color'] = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        context['header_color'] = 'bg-primary'
        context['scan_url'] = '/gs14/scan-serial/'
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Добавляем can_edit для каждого объекта
        user = self.request.user
        for control in context['controls']:
            control.can_edit = control.can_edit(user)
        
        return context


class ControlDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница объекта Control"""
    model = Control
    template_name = 'common/detail.html'
    context_object_name = 'control'
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        if self.request.user.is_superuser:
            return qs
        if self.request.user.groups.filter(name='Аудитор').exists():
            return qs
        if self.request.user.groups.filter(name='Контролер').exists():
            return qs.filter(owner=self.request.user)
        return qs.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Объект {self.object.serial_number}'
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        context['can_edit'] = self.object.can_edit(self.request.user)
        context['app_name'] = 'GS14'
        context['namespace'] = 'gs14'
        context['header_color'] = 'bg-primary'
        return context


class ControlCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание нового объекта"""
    model = Control
    form_class = ControlForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('gs14:control_list')
    
    def test_func(self):
        return self.request.user.is_superuser or \
               self.request.user.groups.filter(name='Контролер').exists()
    
    def get_form_kwargs(self):
        """Передаем параметры в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['is_create'] = True
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        context['is_superuser'] = self.request.user.is_superuser
        context['app_name'] = 'GS14'
        context['namespace'] = 'gs14'
        context['header_color'] = 'bg-primary'
        context['scan_url'] = '/gs14/scan-serial/'
        return context
    
    def post(self, request, *args, **kwargs):
        """Проверка существования объекта перед созданием"""
        serial_number = request.POST.get('serial_number')
        
        if serial_number:
            try:
                existing_obj = Control.objects.get(serial_number=serial_number)
                messages.warning(
                    request, 
                    f'Объект с серийным номером {serial_number} уже существует. '
                    f'Вы будете перенаправлены на страницу редактирования.'
                )
                return redirect('gs14:control_edit', serial_number=serial_number)
            except Control.DoesNotExist:
                pass
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f'Объект с серийным номером {form.instance.serial_number} успешно создан.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при создании объекта. Проверьте данные.')
        return super().form_invalid(form)


class ControlUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование объекта"""
    model = Control
    form_class = ControlForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('gs14:control_list')
    
    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        
        if not obj.can_edit(user):
            if user.groups.filter(name='Контролер').exists():
                if obj.status == 'draft':
                    messages.warning(
                        self.request, 
                        'Объект в статусе "Черновик". Необходимо заполнить все поля.'
                    )
                elif obj.status == 'completed':
                    messages.warning(
                        self.request, 
                        'Объект завершен. Редактирование недоступно.'
                    )
                elif obj.status == 'closed':
                    messages.warning(
                        self.request, 
                        'Объект закрыт. Редактирование недоступно.'
                    )
            return False
        
        return True
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_create'] = False
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_object(self, queryset=None):
        return get_object_or_404(Control, serial_number=self.kwargs['serial_number'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = False
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        context['is_superuser'] = self.request.user.is_superuser
        context['app_name'] = 'GS14'
        context['namespace'] = 'gs14'
        context['header_color'] = 'bg-primary'
        context['scan_url'] = '/gs14/scan-serial/'
        
        # Добавляем информацию о статусе объекта
        obj = self.get_object()
        context['is_completed'] = obj.is_completed()
        context['is_closed'] = obj.status == 'closed'
        context['can_edit'] = obj.can_edit(self.request.user)
        return context
    
    def form_valid(self, form):
        obj = form.instance
        
        # Если пользователь не суперпользователь, сохраняем старый серийный номер
        if not self.request.user.is_superuser:
            original_obj = Control.objects.get(pk=obj.pk)
            obj.serial_number = original_obj.serial_number
        
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
        for field in image_fields:
            delete_key = f'delete_{field}'
            if self.request.POST.get(delete_key):
                if getattr(obj, field):
                    try:
                        old_path = getattr(obj, field).path
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            logger.info(f"Удалено изображение: {old_path}")
                    except Exception as e:
                        logger.warning(f"Не удалось удалить изображение: {e}")
                    setattr(obj, field, None)
        
        obj.save()
        
        # Проверяем статус после сохранения
        if obj.is_completed() and obj.status != 'closed':
            obj.status = 'completed'
            obj.completed_at = timezone.now()
            obj.save()
            messages.success(
                self.request, 
                f'✅ Все фото загружены! Объект {obj.serial_number} завершен. Редактирование закрыто.'
            )
            return redirect('gs14:control_list')  # Переход на список
        else:
            # Если не все фото загружены, обновляем статус на "В процессе"
            if obj.status == 'draft':
                obj.status = 'in_progress'
                obj.save()
            messages.success(
                self.request, 
                f'📝 Объект {obj.serial_number} успешно обновлен. Продолжите заполнение.'
            )
            return redirect('gs14:control_edit', serial_number=obj.serial_number) 
    


class ControlDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Удаление объекта"""
    template_name = 'common/confirm_delete.html'
    
    def test_func(self):
        # Только суперпользователь может удалять
        return self.request.user.is_superuser
    
    def get(self, request, pk):
        control = get_object_or_404(Control, pk=pk)
        context = {
            'control': control,
            'app_name': 'GS14',
            'namespace': 'gs14',
        }
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        try:
            control = get_object_or_404(Control, pk=pk)
            serial = control.serial_number
            
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
            return redirect('gs14:control_list')
            
        except Control.DoesNotExist:
            messages.error(request, f'Объект с ID {pk} не найден')
            return redirect('gs14:control_list')
            
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            logger.error(f"Ошибка удаления объекта {pk}: {e}")
            return redirect('gs14:control_list')


class ControlCloseView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Закрытие объекта"""
    template_name = 'common/confirm_close.html'
    
    def test_func(self):
        obj = get_object_or_404(Control, pk=self.kwargs['pk'])
        return obj.can_edit(self.request.user)
    
    def get(self, request, pk):
        control = get_object_or_404(Control, pk=pk)
        context = {
            'control': control,
            'app_name': 'GS14',
            'namespace': 'gs14',
        }
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        try:
            control = get_object_or_404(Control, pk=pk)
            
            if not control.can_edit(request.user):
                messages.error(request, 'У вас нет прав на закрытие этого объекта')
                return redirect('gs14:control_detail', pk=control.pk)
            
            if control.is_completed():
                control.status = 'closed'
                control.completed_at = timezone.now()
                control.closed_by = request.user
                control.save()
                messages.success(request, f'Объект {control.serial_number} успешно закрыт!')
            else:
                messages.error(request, 'Невозможно закрыть объект: не все фото загружены')
            
            return redirect('gs14:control_detail', pk=control.pk)
            
        except Control.DoesNotExist:
            messages.error(request, f'Объект с ID {pk} не найден')
            return redirect('gs14:control_list')
        except Exception as e:
            messages.error(request, f'Ошибка при закрытии: {str(e)}')
            return redirect('gs14:control_list')


class CheckSerialView(LoginRequiredMixin, View):
    """Проверка существования серийного номера и создание модели"""
    
    def post(self, request):
        serial_number = request.POST.get('serial_number', '').strip()
        
        if not serial_number:
            messages.error(request, 'Введите серийный номер')
            return redirect('gs14:control_create')
        
        try:
            # Проверяем, существует ли объект
            obj = Control.objects.get(serial_number=serial_number)
            
            # Проверяем права доступа к объекту
            if not request.user.is_superuser:
                if request.user.groups.filter(name='Контролер').exists() and obj.owner != request.user:
                    messages.error(request, 'У вас нет доступа к этому объекту')
                    return redirect('gs14:control_list')
            
            messages.info(request, f'Объект с серийным номером {serial_number} найден. Переход к редактированию.')
            return redirect('gs14:control_edit', serial_number=serial_number)
            
        except Control.DoesNotExist:
            # Проверяем, может ли пользователь создавать
            if not request.user.is_superuser and not request.user.groups.filter(name='Контролер').exists():
                messages.error(request, 'У вас нет прав для создания объектов')
                return redirect('gs14:control_list')
            
            # СОЗДАЕМ НОВЫЙ ОБЪЕКТ ТОЛЬКО ЗДЕСЬ, ПОСЛЕ НАЖАТИЯ КНОПКИ "ВВОД"
            obj = Control.objects.create(serial_number=serial_number, owner=request.user)
            messages.success(request, f'Создан новый объект с серийным номером {serial_number}.')
            return redirect('gs14:control_edit', serial_number=serial_number)


class ScanSerialView(LoginRequiredMixin, View):
    """Сканирование серийного номера с фото с сохранением в модель"""
    
    def post(self, request):
        try:
            if 'scan_image' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'Файл не выбран'
                }, status=400)
            
            file = request.FILES['scan_image']
            
            if file.size > 10 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': 'Файл слишком большой (максимум 10MB)'
                }, status=400)
            
            # Получаем серийный номер из запроса
            serial_number = request.POST.get('serial_number', '').strip()
            
            # Сохраняем файл во временное место для распознавания
            import tempfile
            import os
            import time
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f'scan_{int(time.time())}.jpg')
            
            with open(temp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Сбрасываем указатель файла для повторного использования
            file.seek(0)
            
            # Пытаемся найти или создать объект
            control = None
            is_new = False
            
            if serial_number:
                try:
                    control = Control.objects.get(serial_number=serial_number)
                    logger.info(f"Найден объект: {serial_number}")
                except Control.DoesNotExist:
                    # Создаем новый объект
                    control = Control.objects.create(
                        serial_number=serial_number,
                        owner=request.user,
                        status='draft'
                    )
                    is_new = True
                    logger.info(f"Создан новый объект: {serial_number}")
            else:
                # Создаем временный объект
                import uuid
                temp_serial = f"TEMP_{uuid.uuid4().hex[:8]}"
                control = Control.objects.create(
                    serial_number=temp_serial,
                    owner=request.user,
                    status='draft'
                )
                is_new = True
                logger.info(f"Создан временный объект: {temp_serial}")
            
            # Сохраняем фото в модель
            try:
                # Открываем файл заново для сохранения
                with open(temp_path, 'rb') as f:
                    from django.core.files import File
                    control.serial_photo.save(
                        f'serial_photo_{control.serial_number}_{int(time.time())}.jpg',
                        File(f),
                        save=True
                    )
                logger.info(f"Фото сохранено для объекта {control.serial_number}")
            except Exception as e:
                logger.error(f"Ошибка сохранения фото: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка сохранения фото: {str(e)}',
                    'serial_number': control.serial_number,
                    'photo_saved': False
                }, status=500)
            
            # Теперь пытаемся распознать серийный номер
            detected_serial = None
            try:
                import pytesseract
                from PIL import Image
                import re
                import sys
                
                # Настраиваем Tesseract
                if sys.platform == 'win32':
                    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                    if not os.path.exists(tesseract_path):
                        tesseract_path = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                    if os.path.exists(tesseract_path):
                        pytesseract.pytesseract.tesseract_cmd = tesseract_path
                
                # Открываем изображение для распознавания
                image = Image.open(temp_path)
                image = image.convert('L')
                image = image.point(lambda p: 255 if p > 128 else 0)
                
                width, height = image.size
                image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
                
                config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
                text = pytesseract.image_to_string(image, lang='eng', config=config)
                text = re.sub(r'[^0-9]', '', text)
                
                # Ищем серийный номер
                match = re.search(r'\d{7}', text)
                if match:
                    detected_serial = match.group(0)
                else:
                    match = re.search(r'\d{6,8}', text)
                    if match:
                        detected_serial = match.group(0)
                    else:
                        match = re.search(r'\d{5,}', text)
                        if match:
                            detected_serial = match.group(0)
                
                if detected_serial:
                    logger.info(f"Распознан серийный номер: {detected_serial}")
                    
                    # Если это новый объект или номер изменился
                    if detected_serial != control.serial_number:
                        # Проверяем, что такой номер не занят
                        if not Control.objects.filter(serial_number=detected_serial).exclude(pk=control.pk).exists():
                            control.serial_number = detected_serial
                            control.save()
                            logger.info(f"Серийный номер обновлен на {detected_serial}")
                        else:
                            logger.warning(f"Номер {detected_serial} уже занят")
                            
            except Exception as e:
                logger.error(f"Ошибка распознавания: {e}")
            
            # Удаляем временный файл
            try:
                os.remove(temp_path)
            except:
                pass
            
            # Формируем ответ
            if detected_serial and detected_serial != control.serial_number:
                return JsonResponse({
                    'success': True,
                    'serial_number': detected_serial,
                    'photo_saved': True,
                    'message': f'Фото сохранено, номер обновлен на {detected_serial}'
                })
            elif detected_serial:
                return JsonResponse({
                    'success': True,
                    'serial_number': detected_serial,
                    'photo_saved': True,
                    'message': f'Фото сохранено, номер {detected_serial}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'serial_number': control.serial_number,
                    'photo_saved': True,
                    'error': 'Фото сохранено, но не удалось распознать серийный номер'
                })
                
        except Exception as e:
            logger.error(f"Общая ошибка: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Ошибка: {str(e)}'
            }, status=500)
        













@require_http_methods(["POST"])
def ajax_save_image(request, pk, field_name):
    """
    AJAX-сохранение изображения для конкретного поля
    """
    try:
        control = get_object_or_404(Control, pk=pk)
        
        # Проверка прав
        if not control.can_edit(request.user):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на редактирование этого объекта'
            }, status=403)
        
        # Проверка, что поле существует
        if field_name not in ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'serial_photo']:
            return JsonResponse({
                'success': False,
                'error': f'Поле {field_name} не существует'
            }, status=400)
        
        # Проверка, что файл передан
        if field_name not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': f'Файл для поля {field_name} не передан'
            }, status=400)
        
        # Сохраняем файл
        file = request.FILES[field_name]
        setattr(control, field_name, file)
        control.save()
        
        # Проверяем, завершен ли объект
        is_completed = control.is_completed()
        if is_completed and control.status != 'closed':
            control.status = 'completed'
            control.completed_at = timezone.now()
            control.save()
        
        # Формируем ответ
        response_data = {
            'success': True,
            'message': f'Изображение для поля {field_name} успешно загружено',
            'image_url': getattr(control, field_name).url if getattr(control, field_name) else None,
            'is_completed': is_completed,
            'status': control.status,
            'status_display': control.get_status_display()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении изображения: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def ajax_save_title(request, pk, field_name):
    """
    AJAX-сохранение заголовка для конкретного поля
    """
    try:
        control = get_object_or_404(Control, pk=pk)
        
        # Проверка прав
        if not control.can_edit(request.user):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на редактирование этого объекта'
            }, status=403)
        
        # Проверка, что поле существует
        if field_name not in ['title1', 'title2', 'title3', 'title4', 'title5', 'title6', 'title7', 'description']:
            return JsonResponse({
                'success': False,
                'error': f'Поле {field_name} не существует'
            }, status=400)
        
        # Получаем значение
        data = json.loads(request.body)
        value = data.get('value', '')
        
        setattr(control, field_name, value)
        control.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Заголовок для поля {field_name} сохранен',
            'value': value
        })
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении заголовка: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def ajax_check_completed(request, pk):
    """
    Проверка, завершен ли объект
    """
    try:
        control = get_object_or_404(Control, pk=pk)
        
        is_completed = control.is_completed()
        
        if is_completed and control.status != 'closed':
            control.status = 'completed'
            control.completed_at = timezone.now()
            control.save()
        
        return JsonResponse({
            'success': True,
            'is_completed': is_completed,
            'status': control.status,
            'status_display': control.get_status_display(),
            'message': 'Объект завершен!' if is_completed else 'Не все фото загружены'
        })
        
    except Exception as e:
        logger.error(f"Ошибка при проверке завершенности: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
