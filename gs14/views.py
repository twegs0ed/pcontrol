from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import models
from .forms import ControlForm
from .models import Control
import os, sys
import logging
import re
from PIL import Image, ImageEnhance
import pytesseract
import tempfile
import time

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
            return redirect('gs14_control_list')
        return view_func(request, *args, **kwargs)
    return wrapped

def auditor_required(view_func):
    """Декоратор для проверки, что пользователь в группе Аудитор"""
    def wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if not request.user.groups.filter(name='Аудитор').exists():
            messages.error(request, 'У вас нет прав для выполнения этого действия')
            return redirect('gs14_control_list')
        return view_func(request, *args, **kwargs)
    return wrapped


class ControlListView(LoginRequiredMixin, ListView):
    """Список объектов Control с учетом прав"""
    model = Control
    template_name = 'controls/control_list.html'
    context_object_name = 'controls'
    ordering = ['-created_at']
    paginate_by = 10
    
    def get_queryset(self):
        qs = super().get_queryset()
        
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
        context['title'] = 'Список объектов Control'
        context['total_count'] = self.get_queryset().count()
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        return context


class ControlDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница объекта Control"""
    model = Control
    template_name = 'controls/control_detail.html'
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
        context['can_edit'] = self.request.user.is_superuser or \
                              (self.request.user.groups.filter(name='Контролер').exists() and 
                               self.object.owner == self.request.user)
        return context


class ControlCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание нового объекта"""
    model = Control
    form_class = ControlForm
    template_name = 'controls/control_form.html'
    success_url = reverse_lazy('gs14_control_list')
    
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
                return redirect('control_edit', serial_number=serial_number)
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
    template_name = 'controls/control_form.html'
    success_url = reverse_lazy('gs14_control_list')
    
    def test_func(self):
        obj = self.get_object()
        if self.request.user.is_superuser:
            return True
        if self.request.user.groups.filter(name='Контролер').exists():
            return obj.owner == self.request.user
        return False
    
    def get_form_kwargs(self):
        """Передаем параметры в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['is_create'] = False
        kwargs['user'] = self.request.user  # Передаем пользователя
        return kwargs
    
    def get_object(self, queryset=None):
        return get_object_or_404(Control, serial_number=self.kwargs['serial_number'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = False
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        context['can_edit'] = self.request.user.is_superuser or \
                              (self.request.user.groups.filter(name='Контролер').exists() and 
                               self.object.owner == self.request.user)
        context['is_superuser'] = self.request.user.is_superuser  # Добавляем для шаблона
        return context
    
    def form_valid(self, form):
        obj = form.instance
        
        # Если пользователь не суперпользователь, сохраняем старый серийный номер
        if not self.request.user.is_superuser:
            # Получаем оригинальный объект из базы
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
        
        messages.success(self.request, f'Объект с серийным номером {obj.serial_number} успешно обновлен.')
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при обновлении объекта. Проверьте данные.')
        return super().form_invalid(form)


class ControlDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Удаление объекта"""
    
    def test_func(self):
        # Только суперпользователь может удалять
        return self.request.user.is_superuser
    
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
            return redirect('gs14_control_list')
            
        except Control.DoesNotExist:
            messages.error(request, f'Объект с ID {pk} не найден')
            return redirect('gs14_control_list')
            
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            logger.error(f"Ошибка удаления объекта {pk}: {e}")
            return redirect('gs14_control_list')


class CheckSerialView(LoginRequiredMixin, View):
    """Проверка существования серийного номера"""
    
    def post(self, request):
        serial_number = request.POST.get('serial_number', '').strip()
        
        if not serial_number:
            messages.error(request, 'Введите серийный номер')
            return redirect('control_create')
        
        try:
            obj = Control.objects.get(serial_number=serial_number)
            
            # Проверяем права доступа к объекту
            if not request.user.is_superuser:
                if request.user.groups.filter(name='Контролер').exists() and obj.owner != request.user:
                    messages.error(request, 'У вас нет доступа к этому объекту')
                    return redirect('gs14_control_list')
            
            messages.info(request, f'Объект с серийным номером {serial_number} найден. Переход к редактированию.')
            return redirect('control_edit', serial_number=serial_number)
        except Control.DoesNotExist:
            # Проверяем, может ли пользователь создавать
            if not request.user.is_superuser and not request.user.groups.filter(name='Контролер').exists():
                messages.error(request, 'У вас нет прав для создания объектов')
                return redirect('gs14_control_list')
            
            messages.success(request, f'Создан новый объект с серийным номером {serial_number}.')
            obj = Control.objects.create(serial_number=serial_number, owner=request.user)
            return redirect('control_edit', serial_number=serial_number)


class ScanSerialView(LoginRequiredMixin, View):
    """Сканирование серийного номера с фото"""
    
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
            
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f'scan_{int(time.time())}.jpg')
            
            with open(temp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            photo_name = f"serial_{int(time.time())}.jpg"
            full_dir = os.path.join(settings.MEDIA_ROOT, 'controls', 'serial_photos')
            
            if not os.path.exists(full_dir):
                os.makedirs(full_dir)
            
            full_path = os.path.join(full_dir, photo_name)
            
            import shutil
            shutil.copy2(temp_path, full_path)
            
            try:
                image = Image.open(temp_path)
                image = image.convert('L')
                image = image.point(lambda p: 255 if p > 128 else 0)
                
                config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
                text = pytesseract.image_to_string(image, lang='eng', config=config)
                text = re.sub(r'[^0-9]', '', text)
                
                serial_number = None
                match = re.search(r'\d{7}', text)
                if match:
                    serial_number = match.group(0)
                else:
                    match = re.search(r'\d{6,8}', text)
                    if match:
                        serial_number = match.group(0)
                    else:
                        match = re.search(r'\d{5,}', text)
                        if match:
                            serial_number = match.group(0)
                
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                if serial_number:
                    existing_obj = Control.objects.filter(serial_number=serial_number).first()
                    
                    if existing_obj:
                        # Проверяем права на объект
                        if not request.user.is_superuser and not request.user.groups.filter(name='Контролер').exists():
                            if full_path and os.path.exists(full_path):
                                try:
                                    os.remove(full_path)
                                except:
                                    pass
                            return JsonResponse({
                                'success': False,
                                'error': 'У вас нет прав для работы с этим объектом'
                            }, status=403)
                        
                        if full_path and os.path.exists(full_path):
                            with open(full_path, 'rb') as f:
                                existing_obj.serial_photo.save(photo_name, ContentFile(f.read()), save=True)
                    else:
                        # Создаем новый объект
                        if not request.user.is_superuser and not request.user.groups.filter(name='Контролер').exists():
                            if full_path and os.path.exists(full_path):
                                try:
                                    os.remove(full_path)
                                except:
                                    pass
                            return JsonResponse({
                                'success': False,
                                'error': 'У вас нет прав для создания объектов'
                            }, status=403)
                        
                        obj = Control.objects.create(serial_number=serial_number, owner=request.user)
                        if full_path and os.path.exists(full_path):
                            with open(full_path, 'rb') as f:
                                obj.serial_photo.save(photo_name, ContentFile(f.read()), save=True)
                    
                    return JsonResponse({
                        'success': True,
                        'serial_number': serial_number
                    })
                else:
                    if full_path and os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                        except:
                            pass
                    
                    return JsonResponse({
                        'success': False,
                        'error': 'Не удалось найти 7 цифр серийного номера'
                    })
                    
            except Exception as e:
                logger.error(f"Ошибка: {e}")
                try:
                    os.remove(temp_path)
                except:
                    pass
                if full_path and os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except:
                        pass
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка: {str(e)}'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Ошибка: {str(e)}'
            }, status=500)