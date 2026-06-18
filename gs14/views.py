from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .forms import ControlForm
from .models import Control
import os
import logging
import re
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import tempfile
import time
import cv2
import numpy as np
from django.conf import settings


if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:  # Linux/Mac
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

logger = logging.getLogger(__name__)

class ControlListView(ListView):
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
    model = Control
    template_name = 'controls/control_detail.html'
    context_object_name = 'control'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Объект {self.object.serial_number}'
        return context


class ControlCreateView(CreateView):
    model = Control
    form_class = ControlForm
    template_name = 'controls/control_form.html'
    success_url = reverse_lazy('gs14_control_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        return context
    
    def post(self, request, *args, **kwargs):
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
        messages.success(self.request, f'Объект с серийным номером {form.instance.serial_number} успешно создан.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при создании объекта. Проверьте данные.')
        return super().form_invalid(form)


class ControlUpdateView(UpdateView):
    model = Control
    form_class = ControlForm
    template_name = 'controls/control_form.html'
    success_url = reverse_lazy('gs14_control_list')
    
    def get_object(self, queryset=None):
        return get_object_or_404(Control, serial_number=self.kwargs['serial_number'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = False
        return context
    
    def form_valid(self, form):
        obj = form.instance
        
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


class ControlDeleteView(View):
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


class CheckSerialView(View):
    def post(self, request):
        serial_number = request.POST.get('serial_number', '').strip()
        
        if not serial_number:
            messages.error(request, 'Введите серийный номер')
            return redirect('control_create')
        
        try:
            obj = Control.objects.get(serial_number=serial_number)
            messages.info(request, f'Объект с серийным номером {serial_number} найден. Переход к редактированию.')
            return redirect('control_edit', serial_number=serial_number)
        except Control.DoesNotExist:
            messages.success(request, f'Создан новый объект с серийным номером {serial_number}.')
            obj = Control.objects.create(serial_number=serial_number)
            return redirect('control_edit', serial_number=serial_number)


'''class ScanSerialView(View):
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
            
            # Сохраняем временный файл
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f'scan_{int(time.time())}.jpg')
            
            with open(temp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            try:
                # Открываем изображение
                image = Image.open(temp_path)
                
                # === УЛУЧШЕННАЯ ОБРАБОТКА ИЗОБРАЖЕНИЯ ===
                
                # 1. Конвертируем в черно-белое
                image = image.convert('L')
                
                # 2. Увеличиваем контраст
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.5)
                
                # 3. Увеличиваем резкость
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(2.0)
                
                # 4. Увеличиваем яркость
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(1.3)
                
                # 5. Применяем фильтр для улучшения краев
                image = image.filter(ImageFilter.SHARPEN)
                image = image.filter(ImageFilter.SHARPEN)
                
                # 6. Увеличиваем размер для лучшего распознавания
                width, height = image.size
                if width < 1500:
                    new_size = (width * 3, height * 3)
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                
                # 7. Применяем пороговую обработку (бинаризация)
                # Используем адаптивный порог для лучшего разделения цифр
                img_array = np.array(image)
                
                # Применяем адаптивный порог
                binary = cv2.adaptiveThreshold(
                    img_array, 
                    255, 
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 
                    11, 
                    2
                )
                
                # Удаляем шум
                kernel = np.ones((2, 2), np.uint8)
                binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
                binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
                
                # Сохраняем обработанное изображение для отладки
                debug_path = os.path.join(temp_dir, f'debug_{int(time.time())}.jpg')
                cv2.imwrite(debug_path, binary)
                logger.info(f"Отладочное изображение сохранено: {debug_path}")
                
                # Конвертируем обратно в PIL для Tesseract
                processed_image = Image.fromarray(binary)
                
                # === РАСПОЗНАВАНИЕ ===
                
                # Вариант 1: Только цифры
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
                text1 = pytesseract.image_to_string(processed_image, lang='eng', config=custom_config)
                
                # Вариант 2: Цифры и буквы (для случаев, когда буквы могут быть)
                custom_config2 = r'--oem 3 --psm 6'
                text2 = pytesseract.image_to_string(processed_image, lang='rus+eng', config=custom_config2)
                
                # Вариант 3: Только цифры, но с другим PSM
                custom_config3 = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
                text3 = pytesseract.image_to_string(processed_image, lang='eng', config=custom_config3)
                
                # Комбинируем результаты
                all_text = text1 + " " + text2 + " " + text3
                
                # Удаляем все не цифры
                all_text = re.sub(r'[^0-9]', '', all_text)
                
                logger.info(f"Распознанный текст после очистки: {all_text}")
                
                # === ПОИСК СЕРИЙНОГО НОМЕРА ===
                serial_number = None
                found_numbers = []
                
                # Ищем все последовательности цифр длиной 5-10
                matches = re.findall(r'\d{5,10}', all_text)
                for match in matches:
                    found_numbers.append(match)
                    logger.info(f"Найдена последовательность: {match}")
                
                # Сначала ищем ровно 7 цифр
                for num in found_numbers:
                    if len(num) == 7:
                        serial_number = num
                        logger.info(f"Найден 7-значный номер: {serial_number}")
                        break
                
                # Если 7 не найдено, ищем 6-8
                if not serial_number:
                    for num in found_numbers:
                        if 6 <= len(num) <= 8:
                            serial_number = num
                            logger.info(f"Найден {len(num)}-значный номер: {serial_number}")
                            break
                
                # Если ничего не найдено, берем первую последовательность
                if not serial_number and found_numbers:
                    serial_number = found_numbers[0]
                    logger.info(f"Найден первый номер: {serial_number}")
                
                # Удаляем временные файлы
                try:
                    os.remove(temp_path)
                    if os.path.exists(debug_path):
                        os.remove(debug_path)
                except:
                    pass
                
                if serial_number:
                    return JsonResponse({
                        'success': True,
                        'serial_number': serial_number
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Не удалось найти серийный номер. Попробуйте сделать фото с лучшим освещением.'
                    })
                    
            except Exception as e:
                logger.error(f"Ошибка обработки изображения: {e}")
                try:
                    os.remove(temp_path)
                except:
                    pass
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка обработки: {str(e)}'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Ошибка сканирования: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Ошибка сканирования: {str(e)}'
            }, status=500)'''




class ScanSerialView(View):
    """Сканирование серийного номера с фото (самый простой вариант)"""
    
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
            
            # Сохраняем временный файл
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f'scan_{int(time.time())}.jpg')
            
            with open(temp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Сохраняем фото в медиа
            photo_name = f"serial_{int(time.time())}.jpg"
            full_dir = os.path.join(settings.MEDIA_ROOT, 'controls', 'serial_photos')
            
            if not os.path.exists(full_dir):
                os.makedirs(full_dir)
            
            full_path = os.path.join(full_dir, photo_name)
            
            import shutil
            shutil.copy2(temp_path, full_path)
            logger.info(f"Фото сохранено: {full_path}")
            
            try:
                # Открываем изображение
                image = Image.open(temp_path)
                
                # Простая обработка
                image = image.convert('L')  # Черно-белое
                image = image.point(lambda p: 255 if p > 128 else 0)  # Бинаризация
                
                # Распознавание через Tesseract
                config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
                text = pytesseract.image_to_string(image, lang='eng', config=config)
                
                # Удаляем все не цифры
                text = re.sub(r'[^0-9]', '', text)
                
                logger.info(f"Распознанный текст: {text}")
                
                # Ищем 7 цифр подряд
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
                
                # Удаляем временный файл
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                if serial_number:
                    # Проверяем существование объекта
                    existing_obj = Control.objects.filter(serial_number=serial_number).first()
                    
                    if existing_obj:
                        if full_path and os.path.exists(full_path):
                            with open(full_path, 'rb') as f:
                                existing_obj.serial_photo.save(photo_name, ContentFile(f.read()), save=True)
                                logger.info(f"Фото добавлено к объекту {serial_number}")
                    else:
                        obj = Control.objects.create(serial_number=serial_number)
                        if full_path and os.path.exists(full_path):
                            with open(full_path, 'rb') as f:
                                obj.serial_photo.save(photo_name, ContentFile(f.read()), save=True)
                                logger.info(f"Создан новый объект {serial_number}")
                    
                    return JsonResponse({
                        'success': True,
                        'serial_number': serial_number
                    })
                else:
                    if full_path and os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                            logger.info(f"Удалено фото без номера")
                        except:
                            pass
                    
                    return JsonResponse({
                        'success': False,
                        'error': 'Не удалось найти 7 цифр серийного номера. Попробуйте другое фото.'
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