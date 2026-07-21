# pcontrol_app/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.apps import apps
from django.http import JsonResponse
from django.utils import timezone
import logging
import re
import base64
import tempfile
import os
from PIL import Image, ImageEnhance
import pytesseract
import sys

from .models import ProductPrefix, Application
from unified_products.models import Category, Product

logger = logging.getLogger(__name__)

# Путь к Tesseract
if sys.platform == 'win32':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
elif sys.platform == 'linux':
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
elif sys.platform == 'darwin':
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'


class MainPageView(LoginRequiredMixin, View):
    """Главная страница с формой поиска серийного номера"""
    
    login_url = '/login/'
    redirect_field_name = 'next'
    
    def get(self, request):
        # Получаем активные категории для примеров
        categories = Category.objects.filter(is_active=True)
        
        # Статистика
        total_products = Product.objects.count()
        total_completed = Product.objects.filter(status='completed').count()
        total_in_progress = Product.objects.filter(status='in_progress').count()
        
        return render(request, 'pcontrol/index.html', {
            'categories': categories,
            'total_products': total_products,
            'total_completed': total_completed,
            'total_in_progress': total_in_progress,
        })
    
    def post(self, request):
        serial_number = request.POST.get('serial_number', '').strip()
        
        if not serial_number:
            messages.error(request, 'Введите серийный номер')
            return redirect('pcontrol:index')
        
        # Ищем категорию по префиксу
        category = None
        categories = Category.objects.filter(is_active=True)
        for cat in categories:
            if serial_number.startswith(cat.prefix):
                category = cat
                break
        
        if category:
            return self.process_with_category(request, serial_number, category)
        else:
            messages.error(request, f'Не найдена категория для серийного номера {serial_number}')
            return redirect('pcontrol:index')
    
    def process_with_category(self, request, serial_number, category):
        """Обработка найденной категории"""
        try:
            # Пытаемся найти объект
            try:
                obj = Product.objects.get(serial_number=serial_number)
                owner = getattr(obj, 'owner', None)
                
                # Проверка владельца
                if owner and owner != request.user:
                    owner_full_name = owner.get_full_name() or owner.username
                    if owner.groups.filter(name='Контролер').exists():
                        messages.error(
                            request,
                            f'⛔ ДОСТУП ЗАПРЕЩЕН! Объект с серийным номером {serial_number} '
                            f'уже проверяется контролером {owner_full_name}.'
                        )
                        return render(request, 'pcontrol/access_denied.html', {
                            'serial_number': serial_number,
                            'owner_name': owner_full_name,
                            'product_name': category.name,
                        })
                    else:
                        messages.info(
                            request,
                            f'ℹ️ Объект с серийным номером {serial_number} найден. '
                            f'Владелец: {owner_full_name}'
                        )
                        return redirect('unified_products:product_detail', pk=obj.pk)
                
                # Если объект принадлежит текущему пользователю
                messages.info(
                    request, 
                    f'ℹ️ Объект {category.name} с серийным номером {serial_number} найден.'
                )
                
                # Проверяем статус
                if obj.status in ['completed', 'closed']:
                    return redirect('unified_products:product_detail', pk=obj.pk)
                
                return redirect('unified_products:product_edit', serial_number=serial_number)
                
            except Product.DoesNotExist:
                # Объект не найден - создаем новый
                return self.create_and_redirect(request, serial_number, category)
                    
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}")
            messages.error(request, f'❌ Ошибка: {str(e)}')
            return redirect('pcontrol:index')
    
    def create_and_redirect(self, request, serial_number, category):
        """Создать объект и перенаправить на редактирование"""
        try:
            # Проверяем права
            if not request.user.is_superuser and not request.user.groups.filter(name='Контролер').exists():
                messages.error(request, 'У вас нет прав для создания объектов')
                return redirect('pcontrol:index')
            
            # Создаем объект
            obj = Product.objects.create(
                serial_number=serial_number,
                category=category,
                owner=request.user,
                status='draft'
            )
            
            messages.success(
                request, 
                f'✅ Создан новый объект "{category.name}" с серийным номером {serial_number}'
            )
            
            return redirect('unified_products:product_edit', serial_number=serial_number)
            
        except Exception as e:
            logger.error(f"Ошибка создания объекта: {e}")
            messages.error(request, f'❌ Ошибка создания объекта: {str(e)}')
            return redirect('pcontrol:index')


class CheckSerialAjaxView(LoginRequiredMixin, View):
    """AJAX проверка серийного номера"""
    
    login_url = '/login/'
    redirect_field_name = 'next'
    
    def get(self, request):
        serial_number = request.GET.get('serial', '').strip()
        
        if not serial_number:
            return JsonResponse({
                'success': False,
                'error': 'Введите серийный номер'
            })
        
        # Ищем категорию по префиксу
        category = None
        categories = Category.objects.filter(is_active=True)
        for cat in categories:
            if serial_number.startswith(cat.prefix):
                category = cat
                break
        
        if not category:
            return JsonResponse({
                'success': False,
                'error': 'Категория для этого номера не найдена',
                'found': False
            })
        
        try:
            obj = Product.objects.get(serial_number=serial_number)
            owner = getattr(obj, 'owner', None)
            status = getattr(obj, 'status', None)
            is_completed = status in ['completed', 'closed'] if status else False
            progress = obj.get_progress_percent() if hasattr(obj, 'get_progress_percent') else 0
            
            # ===== ОБЪЕКТ ЗАВЕРШЕН =====
            if is_completed:
                owner_name = owner.get_full_name() or owner.username if owner else 'Неизвестно'
                return JsonResponse({
                    'success': True,
                    'found': True,
                    'blocked': True,
                    'is_completed': True,
                    'status': status,
                    'category_name': category.name,
                    'owner_name': owner_name,
                    'message': f'Объект завершен (статус: {status})'
                })
            
            # ===== ОБЪЕКТ ПРИНАДЛЕЖИТ ТЕКУЩЕМУ ПОЛЬЗОВАТЕЛЮ =====
            if owner and owner == request.user:
                return JsonResponse({
                    'success': True,
                    'found': True,
                    'blocked': False,
                    'can_edit': True,
                    'owner': owner.get_full_name() or owner.username,
                    'category_name': category.name,
                    'is_completed': False,
                    'status': status,
                    'progress': progress,
                    'message': 'Объект принадлежит вам'
                })
            
            # ===== ОБЪЕКТ ПРИНАДЛЕЖИТ ДРУГОМУ ПОЛЬЗОВАТЕЛЮ =====
            if owner and owner != request.user:
                owner_full_name = owner.get_full_name() or owner.username
                is_controller = owner.groups.filter(name='Контролер').exists()
                
                if is_controller:
                    return JsonResponse({
                        'success': True,
                        'found': True,
                        'blocked': True,
                        'is_completed': False,
                        'owner_name': owner_full_name,
                        'category_name': category.name,
                        'message': f'Объект занят контролером {owner_full_name}'
                    })
                else:
                    return JsonResponse({
                        'success': True,
                        'found': True,
                        'blocked': False,
                        'can_edit': False,
                        'owner': owner_full_name,
                        'category_name': category.name,
                        'is_completed': False,
                        'message': f'Объект принадлежит {owner_full_name}'
                    })
            
            # ===== ОБЪЕКТ БЕЗ ВЛАДЕЛЬЦА =====
            can_edit = request.user.is_superuser or request.user.groups.filter(name='Контролер').exists()
            return JsonResponse({
                'success': True,
                'found': True,
                'blocked': False,
                'can_edit': can_edit,
                'owner': None,
                'category_name': category.name,
                'is_completed': False,
                'status': status,
                'progress': progress,
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': True,
                'found': False,
                'category_name': category.name,
                'message': 'Объект не найден, будет создан новый'
            })
        except Exception as e:
            logger.error(f"Ошибка проверки: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class ScanSerialView(LoginRequiredMixin, View):
    """Сканирование серийного номера с камеры"""
    
    login_url = '/login/'
    redirect_field_name = 'next'
    
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
            
            # Сохраняем во временный файл
            temp_path = tempfile.mktemp(suffix='.jpg')
            with open(temp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Распознаем серийный номер
            detected_serial = None
            try:
                image = Image.open(temp_path)
                image = image.convert('L')
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)
                image = image.point(lambda p: 255 if p > 128 else 0)
                width, height = image.size
                image = image.resize((width * 3, height * 3), Image.Resampling.LANCZOS)
                
                configs = [
                    r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789',
                    r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789',
                    r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789',
                ]
                
                for config in configs:
                    text = pytesseract.image_to_string(image, lang='eng', config=config)
                    text = re.sub(r'[^0-9]', '', text)
                    if text:
                        match = re.search(r'\d{6,8}', text)
                        if match:
                            detected_serial = match.group(0)
                            break
            except Exception as e:
                logger.error(f"Ошибка распознавания: {e}")
            
            # Кодируем фото в base64
            with open(temp_path, 'rb') as f:
                photo_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # Удаляем временный файл
            try:
                os.remove(temp_path)
            except:
                pass
            
            if detected_serial:
                # Определяем категорию по префиксу
                category = None
                categories = Category.objects.filter(is_active=True)
                for cat in categories:
                    if detected_serial.startswith(cat.prefix):
                        category = cat
                        break
                
                return JsonResponse({
                    'success': True,
                    'serial_number': detected_serial,
                    'photo_base64': photo_base64,
                    'category_id': category.id if category else None,
                    'category_name': category.name if category else None,
                    'message': f'Распознан номер: {detected_serial}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'photo_base64': photo_base64,
                    'error': 'Не удалось распознать серийный номер'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Ошибка сканирования: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class AccessDeniedView(LoginRequiredMixin, View):
    """Страница с информацией о запрете доступа"""
    
    login_url = '/login/'
    redirect_field_name = 'next'
    
    def get(self, request, serial_number):
        owner_name = 'Неизвестный контролер'
        product_name = 'Изделие'
        
        try:
            product = Product.objects.get(serial_number=serial_number)
            owner = getattr(product, 'owner', None)
            if owner:
                owner_name = owner.get_full_name() or owner.username
                product_name = product.category.name if product.category else 'Изделие'
        except Product.DoesNotExist:
            pass
        
        return render(request, 'pcontrol/access_denied.html', {
            'serial_number': serial_number,
            'owner_name': owner_name,
            'product_name': product_name,
        })