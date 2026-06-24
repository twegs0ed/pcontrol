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
from django.utils import timezone
from .forms import KT08_9aForm
from .models import KT08_9a
import os
import sys
import logging
import re
from PIL import Image, ImageEnhance
import pytesseract
import tempfile
import time
from django.urls import reverse


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json



logger = logging.getLogger(__name__)

# Путь к Tesseract
if sys.platform == 'win32':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
elif sys.platform == 'linux':
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
elif sys.platform == 'darwin':
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'


class KT08_9aListView(LoginRequiredMixin, ListView):
    """Список объектов KT08_9a с учетом прав"""
    model = KT08_9a
    template_name = 'common/list.html'  # ИЗМЕНЕНО
    context_object_name = 'controls'
    ordering = ['-created_at']
    paginate_by = 10
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Фильтр по статусу (ДОБАВЛЕНО)
        status_filter = self.request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        # Поиск (ДОБАВЛЕНО)
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
        context['title'] = 'Список объектов KT08_9a'
        context['total_count'] = self.get_queryset().count()
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        context['app_name'] = 'KT08_9a'
        context['app_icon'] = 'fa-microchip'
        context['namespace'] = 'kt08_9a'
        context['primary_color'] = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)'
        context['header_color'] = 'bg-success'
        context['app_badge'] = True
        context['scan_url'] = '/kt08_9a/control/scan-serial/'
        
        # Передаем текущие фильтры в контекст (ДОБАВЛЕНО)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Добавляем can_edit для каждого объекта
        user = self.request.user
        for control in context['controls']:
            control.can_edit = control.can_edit(user)
        
        return context


class KT08_9aDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница объекта KT08_9a"""
    model = KT08_9a
    template_name = 'common/detail.html'  # ИЗМЕНЕНО
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
        context['app_name'] = 'KT08_9a'
        context['namespace'] = 'kt08_9a'  # ДОБАВЛЕНО
        context['header_color'] = 'bg-success'  # ДОБАВЛЕНО
        return context


class KT08_9aCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание нового объекта KT08_9a"""
    model = KT08_9a
    form_class = KT08_9aForm
    template_name = 'common/form.html'  # ИЗМЕНЕНО
    success_url = reverse_lazy('kt08_9a:control_list')
    
    def test_func(self):
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
        context['namespace'] = 'kt08_9a'
        context['header_color'] = 'bg-success'
        context['scan_url'] = '/kt08_9a/scan-serial/'  # <-- ДОБАВЛЕНО (без /control/)
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
                return redirect('kt08_9a:control_edit', serial_number=serial_number)
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
    """Редактирование объекта KT08_9a"""
    model = KT08_9a
    form_class = KT08_9aForm
    template_name = 'common/form.html'  # ИЗМЕНЕНО
    success_url = reverse_lazy('kt08_9a:control_list')
    
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
                else:
                    messages.warning(
                        self.request, 
                        f'Редактирование недоступно. Статус: {obj.status}'
                    )
            else:
                messages.warning(
                    self.request, 
                    'У вас нет прав для редактирования этого объекта.'
                )
            return False
        
        return True
    
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
        context['namespace'] = 'kt08_9a'
        context['header_color'] = 'bg-success'
        context['scan_url'] = '/kt08_9a/scan-serial/'  # <-- ДОБАВЛЕНО (без /control/)
        context['can_edit'] = self.object.can_edit(self.request.user)
        return context
    
    def form_valid(self, form):
        obj = form.instance
        
        # Если пользователь не суперпользователь, сохраняем старый серийный номер
        if not self.request.user.is_superuser:
            original_obj = KT08_9a.objects.get(pk=obj.pk)
            obj.serial_number = original_obj.serial_number
        
        # Обработка удаления serial_photo
        if self.request.POST.get('delete_serial_photo'):
            if obj.serial_photo:
                try:
                    old_path = obj.serial_photo.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
                        logger.info(f"Удалено фото серийного номера: {old_path}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить фото серийного номера: {e}")
                obj.serial_photo = None
        
        # Обработка загрузки нового serial_photo
        # Файл уже сохранен в объекте через form.save()
        # Но нужно убедиться, что он сохранился
        if 'serial_photo' in self.request.FILES:
            # Django автоматически сохранит файл при сохранении объекта
            # Но мы можем добавить логирование
            logger.info(f"Загружено новое фото серийного номера для {obj.serial_number}")
        
        # Обработка удаления image1-image7
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
        
        # Сохраняем объект
        obj.save()
        
        # Проверяем статус после сохранения
        if obj.is_completed() and obj.status != 'closed':
            obj.status = 'completed'
            obj.completed_at = timezone.now()
            obj.save()
            messages.success(
                self.request, 
                f'✅ Все фото загружены! Объект KT08_9a {obj.serial_number} завершен.'
            )
            return redirect('kt08_9a:control_list')  # Переход на список
        else:
            if obj.status == 'draft':
                obj.status = 'in_progress'
                obj.save()
            messages.success(
                self.request, 
                f'📝 Объект KT08_9a {obj.serial_number} успешно обновлен. Продолжите заполнение.'
            )
            return redirect('kt08_9a:control_edit', serial_number=obj.serial_number)  # Остаемся на редактировании


class KT08_9aDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Удаление объекта KT08_9a"""
    template_name = 'common/confirm_delete.html'  # ДОБАВЛЕНО
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get(self, request, pk):
        obj = get_object_or_404(KT08_9a, pk=pk)
        context = {
            'control': obj,
            'app_name': 'KT08_9a',
            'namespace': 'kt08_9a',
        }
        return render(request, self.template_name, context)
    
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
                            logger.info(f"Удалено изображение: {old_path}")
                    except Exception as e:
                        logger.warning(f"Не удалось удалить изображение: {e}")
            
            obj.delete()
            
            messages.success(
                request, 
                f'Объект KT08_9a с серийным номером {serial} успешно удален.'
            )
            return redirect('kt08_9a:control_list')
            
        except KT08_9a.DoesNotExist:
            messages.error(request, f'Объект с ID {pk} не найден')
            return redirect('kt08_9a:control_list')
            
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            logger.error(f"Ошибка удаления объекта {pk}: {e}")
            return redirect('kt08_9a:control_list')


class KT08_9aCloseView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Закрытие объекта KT08_9a"""
    template_name = 'common/confirm_close.html'  # ДОБАВЛЕНО
    
    def test_func(self):
        obj = get_object_or_404(KT08_9a, pk=self.kwargs['pk'])
        return obj.can_edit(self.request.user)
    
    def get(self, request, pk):
        obj = get_object_or_404(KT08_9a, pk=pk)
        context = {
            'control': obj,
            'app_name': 'KT08_9a',
            'namespace': 'kt08_9a',
        }
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        try:
            obj = get_object_or_404(KT08_9a, pk=pk)
            
            if not obj.can_edit(request.user):
                messages.error(request, 'У вас нет прав на закрытие этого объекта')
                return redirect('kt08_9a:control_detail', pk=obj.pk)
            
            if obj.is_completed():
                obj.status = 'closed'
                obj.completed_at = timezone.now()
                obj.closed_by = request.user
                obj.save()
                messages.success(request, f'Объект KT08_9a {obj.serial_number} успешно закрыт!')
            else:
                messages.error(request, 'Невозможно закрыть объект: не все фото загружены')
            
            return redirect('kt08_9a:control_detail', pk=obj.pk)
            
        except KT08_9a.DoesNotExist:
            messages.error(request, f'Объект с ID {pk} не найден')
            return redirect('kt08_9a:control_list')
        except Exception as e:
            messages.error(request, f'Ошибка при закрытии: {str(e)}')
            return redirect('kt08_9a:control_list')


class KT08_9aCheckSerialView(LoginRequiredMixin, View):
    """Проверка и создание объекта с серийным номером"""
    
    def post(self, request):
            # ОТЛАДКА: выводим все POST данные
        print("=== CHECK_SERIAL POST DATA ===")
        for key, value in request.POST.items():
            if key == 'scanned_photo_base64':
                print(f"{key}: {value[:100] if value else 'EMPTY'}... (length: {len(value) if value else 0})")
            else:
                print(f"{key}: {value}")
        print("=== FILES ===")
        for key, value in request.FILES.items():
            print(f"{key}: {value.name if value else 'None'}")
        serial_number = request.POST.get('serial_number', '').strip()
        
        if not serial_number:
            messages.error(request, 'Введите серийный номер')
            return redirect('kt08_9a:control_create')
        
        try:
            # Проверяем, существует ли объект
            obj = KT08_9a.objects.get(serial_number=serial_number)
            
            # Проверяем права доступа к объекту
            if not request.user.is_superuser:
                if request.user.groups.filter(name='Контролер').exists() and obj.owner != request.user:
                    messages.error(request, 'У вас нет доступа к этому объекту')
                    return redirect('kt08_9a:control_list')
            
            messages.info(request, f'Объект с серийным номером {serial_number} найден. Переход к редактированию.')
            return redirect('kt08_9a:control_edit', serial_number=serial_number)
            
        except KT08_9a.DoesNotExist:
            # Проверяем, может ли пользователь создавать
            if not request.user.is_superuser and not request.user.groups.filter(name='Контролер').exists():
                messages.error(request, 'У вас нет прав для создания объектов')
                return redirect('kt08_9a:control_list')
            
            # СОЗДАЕМ НОВЫЙ ОБЪЕКТ
            obj = KT08_9a.objects.create(
                serial_number=serial_number,
                owner=request.user,
                status='draft'
            )
            
            # СОХРАНЯЕМ ФОТО СЕРИЙНОГО НОМЕРА
            photo_saved = False
            
            # 1. Проверяем, есть ли файл в request.FILES
            if 'serial_photo' in request.FILES:
                try:
                    obj.serial_photo = request.FILES['serial_photo']
                    obj.save()
                    photo_saved = True
                    messages.success(request, f'✅ Создан объект с серийным номером {serial_number} и фото.')
                except Exception as e:
                    logger.error(f"Ошибка сохранения фото: {e}")
            
            # 2. Проверяем скрытое поле с base64 (от сканирования)
            elif 'scanned_photo_base64' in request.POST:
                import base64
                from django.core.files.base import ContentFile
                from django.core.files import File
                import os
                
                try:
                    photo_data = request.POST.get('scanned_photo_base64', '')
                    print(f"DEBUG: photo_data length: {len(photo_data)}")  # Для отладки
                    print(f"DEBUG: photo_data starts with: {photo_data[:50] if photo_data else 'EMPTY'}")
                    
                    if photo_data and photo_data != 'null' and photo_data != '' and len(photo_data) > 100:
                        # Проверяем, есть ли префикс data:image
                        if ';base64,' in photo_data:
                            # Разделяем на формат и данные
                            format_part, imgstr = photo_data.split(';base64,')
                            # Извлекаем расширение из формата
                            ext = 'jpg'
                            if '/' in format_part:
                                ext = format_part.split('/')[-1]
                                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                                    ext = 'jpg'
                            
                            # Декодируем base64
                            try:
                                image_data = base64.b64decode(imgstr)
                                if image_data and len(image_data) > 1000:  # Проверяем, что данные есть
                                    # Создаем файл
                                    filename = f'serial_photo_{serial_number}.{ext}'
                                    obj.serial_photo.save(
                                        filename,
                                        ContentFile(image_data),
                                        save=True
                                    )
                                    photo_saved = True
                                    print(f"DEBUG: Photo saved successfully! Size: {len(image_data)} bytes")
                                    messages.success(request, f'✅ Создан объект с серийным номером {serial_number} и фото из сканирования.')
                                else:
                                    print(f"DEBUG: Image data too small or empty: {len(image_data) if image_data else 0}")
                            except Exception as e:
                                print(f"DEBUG: Base64 decode error: {e}")
                                logger.error(f"Ошибка декодирования base64: {e}")
                        else:
                            # Возможно, данные без префикса
                            try:
                                image_data = base64.b64decode(photo_data)
                                if image_data and len(image_data) > 1000:
                                    obj.serial_photo.save(
                                        f'serial_photo_{serial_number}.jpg',
                                        ContentFile(image_data),
                                        save=True
                                    )
                                    photo_saved = True
                                    messages.success(request, f'✅ Создан объект с серийным номером {serial_number} и фото из сканирования.')
                            except Exception as e:
                                print(f"DEBUG: Direct decode error: {e}")
                    else:
                        print(f"DEBUG: Photo data invalid or too short: {len(photo_data) if photo_data else 0}")
                        
                except Exception as e:
                    print(f"DEBUG: General error: {e}")
                    logger.error(f"Ошибка сохранения фото из base64: {e}")
            
            # 3. Если есть файл в сессии (старый способ)
            elif 'temp_serial_photo' in request.session:
                import base64
                from django.core.files.base import ContentFile
                try:
                    photo_data = request.session.pop('temp_serial_photo')
                    if photo_data and len(photo_data) > 100:
                        # Проверяем формат
                        if ';base64,' in photo_data:
                            format_part, imgstr = photo_data.split(';base64,')
                            ext = 'jpg'
                            if '/' in format_part:
                                ext = format_part.split('/')[-1]
                            image_data = base64.b64decode(imgstr)
                            if image_data and len(image_data) > 1000:
                                obj.serial_photo.save(
                                    f'serial_photo_{serial_number}.{ext}',
                                    ContentFile(image_data),
                                    save=True
                                )
                                photo_saved = True
                                messages.success(request, f'✅ Создан объект с серийным номером {serial_number} и фото из сессии.')
                except Exception as e:
                    logger.error(f"Ошибка сохранения фото из сессии: {e}")
            
            if not photo_saved:
                messages.success(request, f'✅ Создан объект с серийным номером {serial_number}. (Фото не сохранено)')
                print("DEBUG: Photo NOT saved!")
            
            return redirect('kt08_9a:control_edit', serial_number=serial_number)


class KT08_9aScanSerialView(LoginRequiredMixin, View):
    """Сканирование серийного номера - ТОЛЬКО распознавание, без создания объекта"""
    
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
            
            # Сохраняем файл во временное место для распознавания
            import tempfile
            import os
            import time
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f'scan_{int(time.time())}.jpg')
            
            with open(temp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Сбрасываем указатель файла
            file.seek(0)
            
            # Пытаемся распознать серийный номер
            detected_serial = None
            try:
                import pytesseract
                from PIL import Image, ImageEnhance, ImageFilter
                import re
                import sys
                
                # Настраиваем Tesseract
                if sys.platform == 'win32':
                    tesseract_paths = [
                        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                    ]
                    for path in tesseract_paths:
                        if os.path.exists(path):
                            pytesseract.pytesseract.tesseract_cmd = path
                            break
                
                # Открываем изображение и улучшаем его
                image = Image.open(temp_path)
                
                # Конвертируем в оттенки серого
                image = image.convert('L')
                
                # Увеличиваем контрастность
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)
                
                # Применяем пороговую обработку (бинаризация)
                threshold = 128
                image = image.point(lambda p: 255 if p > threshold else 0)
                
                # Увеличиваем размер для лучшего распознавания
                width, height = image.size
                image = image.resize((width * 3, height * 3), Image.Resampling.LANCZOS)
                
                # Применяем фильтр для улучшения
                image = image.filter(ImageFilter.SHARPEN)
                
                # Пробуем разные конфигурации Tesseract
                configs = [
                    r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789',
                    r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789',
                    r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789',
                    r'--oem 3 --psm 13 -c tessedit_char_whitelist=0123456789',
                ]
                
                all_texts = []
                for config in configs:
                    try:
                        text = pytesseract.image_to_string(image, lang='eng', config=config)
                        text = re.sub(r'[^0-9]', '', text)
                        if text:
                            all_texts.append(text)
                            logger.info(f"Распознано с config {config}: {text}")
                    except Exception as e:
                        logger.warning(f"Ошибка с config {config}: {e}")
                
                # Ищем серийный номер (7 цифр)
                patterns = [
                    r'\d{7}',      # ровно 7 цифр
                    r'\d{6,8}',    # 6-8 цифр
                ]
                
                for text in all_texts:
                    for pattern in patterns:
                        match = re.search(pattern, text)
                        if match:
                            detected_serial = match.group(0)
                            logger.info(f"Найден серийный номер: {detected_serial}")
                            break
                    if detected_serial:
                        break
                        
            except Exception as e:
                logger.error(f"Ошибка распознавания: {e}")
            
            # Кодируем фото в base64 для отправки в форму
            import base64
            photo_base64 = None
            try:
                with open(temp_path, 'rb') as f:
                    photo_base64 = base64.b64encode(f.read()).decode('utf-8')
                    logger.info(f"Фото закодировано в base64, длина: {len(photo_base64)}")
            except Exception as e:
                logger.error(f"Ошибка кодирования фото: {e}")
            
            # Удаляем временный файл
            try:
                os.remove(temp_path)
            except:
                pass
            
            # Возвращаем результат распознавания с фото
            if detected_serial:
                from .models import KT08_9a
                exists = KT08_9a.objects.filter(serial_number=detected_serial).exists()
                
                return JsonResponse({
                    'success': True,
                    'serial_number': detected_serial,
                    'exists': exists,
                    'photo_base64': photo_base64,
                    'message': f'Распознан номер: {detected_serial}' + (' (уже существует)' if exists else '')
                })
            else:
                # Даже если номер не распознан, возвращаем фото для ручного ввода
                return JsonResponse({
                    'success': False,
                    'photo_base64': photo_base64,
                    'error': 'Не удалось распознать серийный номер на изображении. Введите номер вручную.'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Общая ошибка: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Ошибка: {str(e)}'
            }, status=500)


class KT08_9aChangeStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Изменение статуса объекта KT08_9a (только для администратора)"""
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def post(self, request, pk):
        try:
            obj = get_object_or_404(KT08_9a, pk=pk)
            new_status = request.POST.get('new_status')
            
            if new_status in dict(KT08_9a.STATUS_CHOICES):
                obj.status = new_status
                if new_status == 'completed':
                    obj.completed_at = timezone.now()
                obj.save()
                messages.success(
                    request, 
                    f'Статус объекта KT08_9a {obj.serial_number} изменен на "{obj.get_status_display()}".'
                )
            else:
                messages.error(request, 'Неверный статус')
            
            return redirect('kt08_9a:control_edit', serial_number=obj.serial_number)
            
        except KT08_9a.DoesNotExist:
            messages.error(request, 'Объект не найден')
            return redirect('kt08_9a:control_list')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
            return redirect('kt08_9a:control_list')
        










@require_http_methods(["POST"])
def ajax_save_image(request, pk, field_name):
    """
    AJAX-сохранение изображения для конкретного поля
    """
    try:
        from .models import KT08_9a  # Или ваша модель
        control = get_object_or_404(KT08_9a, pk=pk)
        
        # Проверка прав
        if not control.can_edit(request.user):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на редактирование этого объекта'
            }, status=403)
        
        # Проверка, что поле существует
        valid_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'serial_photo']
        if field_name not in valid_fields:
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
        
        # Если все фото загружены - меняем статус и готовим редирект
        redirect_url = None
        if is_completed and control.status != 'closed':
            control.status = 'completed'
            control.completed_at = timezone.now()
            control.save()
            
            # Готовим URL для редиректа на список
            redirect_url = reverse('kt08_9a:control_list')
        
        # Формируем ответ
        response_data = {
            'success': True,
            'message': f'Изображение для поля {field_name} успешно загружено',
            'image_url': getattr(control, field_name).url if getattr(control, field_name) else None,
            'is_completed': is_completed,
            'status': control.status,
            'status_display': control.get_status_display(),
            'redirect_url': redirect_url,  # Добавляем URL для редиректа
            'redirect_message': '✅ Все фото загружены! Объект завершен. Перенаправление на список...'
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
        from .models import KT08_9a
        control = get_object_or_404(KT08_9a, pk=pk)
        
        # Проверка прав
        if not control.can_edit(request.user):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на редактирование этого объекта'
            }, status=403)
        
        # Проверка, что поле существует
        valid_fields = ['title1', 'title2', 'title3', 'title4', 'title5', 'title6', 'title7', 'description']
        if field_name not in valid_fields:
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
        from .models import KT08_9a
        from django.urls import reverse
        
        control = get_object_or_404(KT08_9a, pk=pk)
        
        is_completed = control.is_completed()
        
        redirect_url = None
        if is_completed and control.status != 'closed':
            control.status = 'completed'
            control.completed_at = timezone.now()
            control.save()
            redirect_url = reverse('kt08_9a:control_list')
        
        return JsonResponse({
            'success': True,
            'is_completed': is_completed,
            'status': control.status,
            'status_display': control.get_status_display(),
            'redirect_url': redirect_url,
            'message': 'Объект завершен!' if is_completed else 'Не все фото загружены'
        })
        
    except Exception as e:
        logger.error(f"Ошибка при проверке завершенности: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def ajax_delete_image(request, pk, field_name):
    """
    AJAX-удаление изображения
    """
    try:
        from .models import KT08_9a
        control = get_object_or_404(KT08_9a, pk=pk)
        
        # Проверка прав
        if not control.can_edit(request.user):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на редактирование этого объекта'
            }, status=403)
        
        # Проверка, что поле существует
        valid_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'serial_photo']
        if field_name not in valid_fields:
            return JsonResponse({
                'success': False,
                'error': f'Поле {field_name} не существует'
            }, status=400)
        
        # Удаляем файл
        current_file = getattr(control, field_name)
        if current_file:
            current_file.delete(save=False)
            setattr(control, field_name, None)
            control.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Изображение для поля {field_name} удалено'
        })
        
    except Exception as e:
        logger.error(f"Ошибка при удалении изображения: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)