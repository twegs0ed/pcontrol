# kt08_9a/views.py
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.conf import settings
from .forms import KT08_9aForm
from .models import KT08_9a
import os
import logging
import re
from PIL import Image, ImageEnhance
import pytesseract
import tempfile
import time
import sys

logger = logging.getLogger(__name__)

# Путь к Tesseract
if sys.platform == 'win32':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
elif sys.platform == 'linux':
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
elif sys.platform == 'darwin':
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'


class KT08_9aListView(LoginRequiredMixin, ListView):
    model = KT08_9a
    template_name = 'kt08_9a/kt08_9a_list.html'
    context_object_name = 'controls'
    ordering = ['-created_at']
    paginate_by = 10
    
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
        context['title'] = 'Список объектов KT08_9a'
        context['total_count'] = self.get_queryset().count()
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        context['app_name'] = 'KT08_9a'
        context['app_icon'] = 'fa-microchip'
        return context


class KT08_9aDetailView(LoginRequiredMixin, DetailView):
    model = KT08_9a
    template_name = 'kt08_9a/kt08_9a_detail.html'
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
        context['app_name'] = 'KT08_9a'
        return context


class KT08_9aCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = KT08_9a
    form_class = KT08_9aForm
    template_name = 'kt08_9a/kt08_9a_form.html'
    success_url = reverse_lazy('kt08_9a_list')
    
    def test_func(self):
        """Проверка прав доступа: только контролеры и суперпользователи могут создавать"""
        return self.request.user.is_superuser or \
               self.request.user.groups.filter(name='Контролер').exists()
    
    def get_form_kwargs(self):
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
        context['app_name'] = 'KT08_9a'
        return context
    
    def post(self, request, *args, **kwargs):
        serial_number = request.POST.get('serial_number')
        if serial_number:
            try:
                existing_obj = KT08_9a.objects.get(serial_number=serial_number)
                messages.warning(
                    request, 
                    f'Объект KT08_9a с серийным номером {serial_number} уже существует.'
                )
                return redirect('kt08_9a_edit', serial_number=serial_number)
            except KT08_9a.DoesNotExist:
                pass
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(
            self.request, 
            f'Объект KT08_9a с серийным номером {form.instance.serial_number} успешно создан.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при создании объекта. Проверьте данные.')
        return super().form_invalid(form)


class KT08_9aUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = KT08_9a
    form_class = KT08_9aForm
    template_name = 'kt08_9a/kt08_9a_form.html'
    success_url = reverse_lazy('kt08_9a_list')
    
    def test_func(self):
        """Проверка прав доступа: только владелец, контролер или суперпользователь"""
        obj = self.get_object()
        if self.request.user.is_superuser:
            return True
        if self.request.user.groups.filter(name='Контролер').exists():
            return obj.owner == self.request.user
        return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_create'] = False
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_object(self, queryset=None):
        return get_object_or_404(KT08_9a, serial_number=self.kwargs['serial_number'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = False
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        context['is_superuser'] = self.request.user.is_superuser
        context['app_name'] = 'KT08_9a'
        return context
    
    def form_valid(self, form):
        obj = form.instance
        
        if not self.request.user.is_superuser:
            original_obj = KT08_9a.objects.get(pk=obj.pk)
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
        messages.success(
            self.request, 
            f'Объект KT08_9a с серийным номером {obj.serial_number} успешно обновлен.'
        )
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при обновлении объекта. Проверьте данные.')
        return super().form_invalid(form)


class KT08_9aDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        """Удаление доступно только суперпользователю"""
        return self.request.user.is_superuser
    
    def post(self, request, pk):
        try:
            obj = get_object_or_404(KT08_9a, pk=pk)
            serial = obj.serial_number
            
            image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
            for field in image_fields:
                if getattr(obj, field):
                    try:
                        old_path = getattr(obj, field).path
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except:
                        pass
            
            obj.delete()
            messages.success(
                request, 
                f'Объект KT08_9a с серийным номером {serial} успешно удален.'
            )
            return redirect('kt08_9a_list')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            return redirect('kt08_9a_list')


class KT08_9aCheckSerialView(LoginRequiredMixin, View):
    """Проверка существования серийного номера и создание модели"""
    
    def post(self, request):
        serial_number = request.POST.get('serial_number', '').strip()
        if not serial_number:
            messages.error(request, 'Введите серийный номер')
            return redirect('kt08_9a_create')
        
        try:
            # Проверяем, существует ли объект
            obj = KT08_9a.objects.get(serial_number=serial_number)
            
            if not request.user.is_superuser and request.user.groups.filter(name='Контролер').exists() and obj.owner != request.user:
                messages.error(request, 'У вас нет доступа к этому объекту')
                return redirect('kt08_9a_list')
            
            messages.info(request, f'Объект KT08_9a с серийным номером {serial_number} найден.')
            return redirect('kt08_9a_edit', serial_number=serial_number)
            
        except KT08_9a.DoesNotExist:
            # Проверяем, может ли пользователь создавать
            if not request.user.is_superuser and not request.user.groups.filter(name='Контролер').exists():
                messages.error(request, 'У вас нет прав для создания объектов')
                return redirect('kt08_9a_list')
            
            # СОЗДАЕМ НОВЫЙ ОБЪЕКТ ТОЛЬКО ЗДЕСЬ, ПОСЛЕ НАЖАТИЯ КНОПКИ "ВВОД"
            obj = KT08_9a.objects.create(serial_number=serial_number, owner=request.user)
            messages.success(request, f'Создан новый объект KT08_9a с серийным номером {serial_number}.')
            return redirect('kt08_9a_edit', serial_number=serial_number)


class KT08_9aScanSerialView(LoginRequiredMixin, View):
    """Сканирование серийного номера с фото - только подстановка номера в поле"""
    
    def post(self, request):
        try:
            if 'scan_image' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'Файл не выбран'}, status=400)
            
            file = request.FILES['scan_image']
            if file.size > 10 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'Файл слишком большой'}, status=400)
            
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f'scan_{int(time.time())}.jpg')
            
            with open(temp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
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
                    # ТОЛЬКО ВОЗВРАЩАЕМ НОМЕР, НЕ СОЗДАЕМ МОДЕЛЬ
                    return JsonResponse({'success': True, 'serial_number': serial_number})
                else:
                    return JsonResponse({'success': False, 'error': 'Не удалось найти серийный номер'})
            except Exception as e:
                logger.error(f"Ошибка: {e}")
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)