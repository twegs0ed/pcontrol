# pcontrol_app/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.apps import apps
from .models import ProductPrefix, Application
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class MainPageView(LoginRequiredMixin, View):
    """Главная страница с формой поиска серийного номера (только для авторизованных)"""
    
    login_url = '/login/'  # URL для перенаправления неавторизованных
    redirect_field_name = 'next'
    
    def get(self, request):
        return render(request, 'pcontrol/index.html')
    
    def post(self, request):
        serial_number = request.POST.get('serial_number', '').strip()
        
        if not serial_number:
            messages.error(request, 'Введите серийный номер')
            return redirect('pcontrol:main_page')
        
        # Ищем префикс
        matched_prefix = None
        prefixes = ProductPrefix.objects.filter(is_active=True).select_related('app').order_by('-prefix')
        
        for prefix_data in prefixes:
            if serial_number.startswith(prefix_data.prefix):
                matched_prefix = prefix_data
                break
        
        if matched_prefix:
            return self.process_with_prefix(request, serial_number, matched_prefix)
        else:
            return self.search_in_all_apps(request, serial_number)
    
    def process_with_prefix(self, request, serial_number, prefix):
        """Обработка найденного префикса"""
        try:
            model = prefix.get_model()
            if not model:
                messages.error(request, f'Модель для приложения {prefix.app.app_label} не найдена')
                return redirect('pcontrol:main_page')
            
            try:
                # Пытаемся найти объект
                obj = model.objects.get(serial_number=serial_number)
                
                # ===== ПРОВЕРКА ВЛАДЕЛЬЦА =====
                owner = getattr(obj, 'owner', None)
                
                # Если объект принадлежит другому пользователю
                if owner and owner != request.user:
                    owner_full_name = owner.get_full_name() or owner.username
                    
                    # Проверяем, является ли владелец контролером
                    is_controller = owner.groups.filter(name='Контролер').exists()
                    
                    if is_controller:
                        messages.error(
                            request,
                            f'⛔ ДОСТУП ЗАПРЕЩЕН! Объект с серийным номером {serial_number} '
                            f'уже проверяется контролером {owner_full_name}.'
                        )
                        return render(request, 'pcontrol/access_denied.html', {
                            'serial_number': serial_number,
                            'owner_name': owner_full_name,
                            'product_name': prefix.product_name,
                        })
                    else:
                        messages.info(
                            request,
                            f'ℹ️ Объект с серийным номером {serial_number} найден. '
                            f'Владелец: {owner_full_name}'
                        )
                        edit_url = prefix.get_edit_url(serial_number)
                        if edit_url:
                            return redirect(edit_url)
                        return redirect('pcontrol:main_page')
                
                # Если объект принадлежит текущему пользователю
                messages.info(
                    request, 
                    f'ℹ️ Объект {prefix.product_name} с серийным номером {serial_number} найден.'
                )
                
                edit_url = prefix.get_edit_url(serial_number)
                if edit_url:
                    return redirect(edit_url)
                else:
                    messages.error(request, f'Не удалось определить URL для редактирования {prefix.product_name}')
                    return redirect('pcontrol:main_page')
                    
            except model.DoesNotExist:
                # Объект не найден
                if not request.user.is_authenticated:
                    messages.warning(
                        request, 
                        f'⚠️ Объект с серийным номером {serial_number} не найден. '
                        f'Для создания нового объекта необходимо авторизоваться.'
                    )
                    return redirect('pcontrol:main_page')
                
                is_allowed = (
                    request.user.is_superuser or 
                    request.user.groups.filter(name='Контролер').exists()
                )
                
                if not is_allowed:
                    messages.warning(
                        request, 
                        f'⚠️ Объект с серийным номером {serial_number} не найден. '
                        f'Для создания нового объекта необходимо быть в группе "Контролер".'
                    )
                    return redirect('pcontrol:main_page')
                
                return self.create_and_redirect(request, serial_number, prefix)
                    
        except Exception as e:
            logger.error(f"Ошибка обработки префикса: {e}")
            messages.error(request, f'❌ Ошибка: {str(e)}')
            return redirect('pcontrol:main_page')
    
    def create_and_redirect(self, request, serial_number, prefix):
        """Создать объект и перенаправить на редактирование"""
        try:
            model = prefix.get_model()
            if not model:
                messages.error(request, f'Модель для приложения {prefix.app.app_label} не найдена')
                return redirect('pcontrol:main_page')
            
            existing_obj = model.objects.filter(serial_number=serial_number).first()
            if existing_obj:
                owner = getattr(existing_obj, 'owner', None)
                if owner and owner != request.user:
                    owner_full_name = owner.get_full_name() or owner.username
                    if owner.groups.filter(name='Контролер').exists():
                        return render(request, 'pcontrol/access_denied.html', {
                            'serial_number': serial_number,
                            'owner_name': owner_full_name,
                            'product_name': prefix.product_name,
                        })
                    else:
                        messages.warning(
                            request,
                            f'⚠️ Объект с серийным номером {serial_number} уже существует и принадлежит '
                            f'пользователю {owner_full_name}.'
                        )
                        edit_url = prefix.get_edit_url(serial_number)
                        if edit_url:
                            return redirect(edit_url)
                        return redirect('pcontrol:main_page')
                else:
                    messages.info(request, f'ℹ️ Объект с серийным номером {serial_number} уже существует')
                    edit_url = prefix.get_edit_url(serial_number)
                    if edit_url:
                        return redirect(edit_url)
                    return redirect('pcontrol:main_page')
            
            create_kwargs = {
                'serial_number': serial_number,
            }
            
            if hasattr(model, 'status'):
                create_kwargs['status'] = 'draft'
            
            if hasattr(model, 'owner'):
                create_kwargs['owner'] = request.user
            
            obj = model.objects.create(**create_kwargs)
            
            messages.success(
                request, 
                f'✅ Создан новый объект "{prefix.product_name}" с серийным номером {serial_number}'
            )
            
            edit_url = prefix.get_edit_url(serial_number)
            if edit_url:
                return redirect(edit_url)
            
            messages.error(request, '❌ Не удалось определить URL для редактирования')
            return redirect('pcontrol:main_page')
            
        except Exception as e:
            logger.error(f"Ошибка создания объекта: {e}")
            messages.error(request, f'❌ Ошибка создания объекта: {str(e)}')
            return redirect('pcontrol:main_page')
    
    def search_in_all_apps(self, request, serial_number):
        """Поиск во всех зарегистрированных моделях"""
        prefixes = ProductPrefix.objects.filter(is_active=True).select_related('app')
        
        models_to_check = {}
        for prefix in prefixes:
            model = prefix.get_model()
            app_label = prefix.app.app_label
            if model and app_label not in models_to_check:
                models_to_check[app_label] = {
                    'model': model,
                    'prefixes': []
                }
            if model:
                models_to_check[app_label]['prefixes'].append(prefix)
        
        for app_label, data in models_to_check.items():
            model = data['model']
            try:
                obj = model.objects.get(serial_number=serial_number)
                
                owner = getattr(obj, 'owner', None)
                
                if owner and owner != request.user:
                    owner_full_name = owner.get_full_name() or owner.username
                    
                    if owner.groups.filter(name='Контролер').exists():
                        product_name = 'Изделие'
                        for prefix in data['prefixes']:
                            if serial_number.startswith(prefix.prefix):
                                product_name = prefix.product_name
                                break
                        
                        return render(request, 'pcontrol/access_denied.html', {
                            'serial_number': serial_number,
                            'owner_name': owner_full_name,
                            'product_name': product_name,
                        })
                    else:
                        messages.info(
                            request,
                            f'ℹ️ Объект с серийным номером {serial_number} найден. '
                            f'Владелец: {owner_full_name}'
                        )
                
                messages.info(request, f'ℹ️ Объект найден в приложении {app_label}')
                
                for prefix in data['prefixes']:
                    if serial_number.startswith(prefix.prefix):
                        edit_url = prefix.get_edit_url(serial_number)
                        if edit_url:
                            return redirect(edit_url)
                
                try:
                    from django.urls import reverse
                    return redirect(f'{app_label}:edit', serial_number=serial_number)
                except:
                    messages.error(request, f'Не удалось определить URL для редактирования')
                    return redirect('pcontrol:main_page')
                    
            except model.DoesNotExist:
                continue
            except Exception as e:
                logger.error(f"Ошибка поиска в модели {app_label}: {e}")
                continue
        
        if not request.user.is_authenticated:
            messages.warning(
                request, 
                f'⚠️ Серийный номер {serial_number} не найден. '
                f'Для создания нового объекта необходимо авторизоваться.'
            )
            return redirect('pcontrol:main_page')
        
        is_allowed = (
            request.user.is_superuser or 
            request.user.groups.filter(name='Контролер').exists()
        )
        
        if not is_allowed:
            messages.warning(
                request, 
                f'⚠️ Серийный номер {serial_number} не найден. '
                f'Для создания нового объекта необходимо быть в группе "Контролер".'
            )
            return redirect('pcontrol:main_page')
        
        return redirect('pcontrol:unknown', serial_number=serial_number)


class CheckSerialAjaxView(LoginRequiredMixin, View):
    """AJAX проверка серийного номера (только для авторизованных)"""
    
    login_url = '/login/'
    redirect_field_name = 'next'
    
    def get(self, request):
        serial_number = request.GET.get('serial', '').strip()
        
        if not serial_number:
            return JsonResponse({
                'success': False,
                'error': 'Введите серийный номер'
            })
        
        # ОТЛАДКА
        print(f"\n=== AJAX ПРОВЕРКА ===")
        print(f"Пользователь: {request.user} (ID: {request.user.id})")
        print(f"Серийный номер: {serial_number}")
        
        # Ищем префикс
        matched_prefix = None
        prefixes = ProductPrefix.objects.filter(is_active=True).select_related('app').order_by('-prefix')
        
        for prefix_data in prefixes:
            if serial_number.startswith(prefix_data.prefix):
                matched_prefix = prefix_data
                break
        
        if not matched_prefix:
            return JsonResponse({
                'success': False,
                'found': False,
                'message': 'Префикс не найден в системе'
            })
        
        print(f"Найден префикс: {matched_prefix.prefix} - {matched_prefix.product_name}")
        
        # Ищем объект
        model = matched_prefix.get_model()
        if not model:
            return JsonResponse({
                'success': False,
                'found': False,
                'message': 'Модель не найдена'
            })
        
        try:
            obj = model.objects.get(serial_number=serial_number)
            owner = getattr(obj, 'owner', None)
            
            print(f"Объект найден: {obj}")
            print(f"Владелец объекта: {owner} (ID: {owner.id if owner else None})")
            print(f"Текущий пользователь: {request.user} (ID: {request.user.id})")
            print(f"Совпадают ли пользователи: {owner == request.user if owner else False}")
            
            # ===== ПРОВЕРКА СТАТУСА =====
            status = getattr(obj, 'status', None)
            is_completed = status in ['completed', 'closed'] if status else False
            
            # Если объект завершен - запрещаем редактирование
            if is_completed:
                owner_name = owner.get_full_name() or owner.username if owner else 'Неизвестно'
                return JsonResponse({
                    'success': True,
                    'found': True,
                    'blocked': True,
                    'owner_name': owner_name,
                    'product_name': matched_prefix.product_name,
                    'is_completed': True,
                    'status': status,
                    'message': f'Объект завершен (статус: {status})'
                })
            
            # ===== ПРОВЕРКА ВЛАДЕЛЬЦА =====
            # Если объект принадлежит текущему пользователю - разрешаем редактирование
            if owner and owner == request.user:
                print("=== ОБЪЕКТ ПРИНАДЛЕЖИТ ТЕКУЩЕМУ ПОЛЬЗОВАТЕЛЮ ===")
                return JsonResponse({
                    'success': True,
                    'found': True,
                    'blocked': False,
                    'can_edit': True,
                    'owner': owner.get_full_name() or owner.username,
                    'product': matched_prefix.product_name,
                    'is_completed': False,
                    'status': status,
                    'message': 'Объект принадлежит вам'
                })
            
            # Если объект принадлежит другому пользователю
            if owner and owner != request.user:
                owner_full_name = owner.get_full_name() or owner.username
                is_controller = owner.groups.filter(name='Контролер').exists()
                
                print(f"Объект принадлежит другому пользователю: {owner_full_name}")
                print(f"Владелец - контролер: {is_controller}")
                
                if is_controller:
                    return JsonResponse({
                        'success': True,
                        'found': True,
                        'blocked': True,
                        'owner_name': owner_full_name,
                        'product_name': matched_prefix.product_name,
                        'is_completed': False,
                        'message': f'Объект занят контролером {owner_full_name}'
                    })
                else:
                    return JsonResponse({
                        'success': True,
                        'found': True,
                        'blocked': False,
                        'can_edit': False,
                        'owner': owner_full_name,
                        'product': matched_prefix.product_name,
                        'is_completed': False,
                        'message': f'Объект принадлежит {owner_full_name}'
                    })
            
            # ===== ОБЪЕКТ БЕЗ ВЛАДЕЛЬЦА (свободен) =====
            print("=== ОБЪЕКТ БЕЗ ВЛАДЕЛЬЦА ===")
            can_edit = False
            if request.user.is_superuser:
                can_edit = True
            elif request.user.groups.filter(name='Контролер').exists():
                can_edit = True
            
            return JsonResponse({
                'success': True,
                'found': True,
                'blocked': False,
                'can_edit': can_edit,
                'owner': None,
                'product': matched_prefix.product_name,
                'is_completed': False,
                'status': status,
            })
            
        except model.DoesNotExist:
            print("=== ОБЪЕКТ НЕ НАЙДЕН ===")
            return JsonResponse({
                'success': True,
                'found': False,
                'product': matched_prefix.product_name,
                'message': 'Объект не найден, будет создан новый'
            })
        except Exception as e:
            print(f"ОШИБКА: {e}")
            logger.error(f"Ошибка проверки: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class AccessDeniedView(LoginRequiredMixin, View):
    """Страница с информацией о запрете доступа (только для авторизованных)"""
    
    login_url = '/login/'
    redirect_field_name = 'next'
    
    def get(self, request, serial_number):
        owner_name = 'Неизвестный контролер'
        product_name = 'Изделие'
        
        try:
            prefixes = ProductPrefix.objects.filter(is_active=True).select_related('app')
            for prefix in prefixes:
                model = prefix.get_model()
                if model:
                    try:
                        obj = model.objects.get(serial_number=serial_number)
                        owner = getattr(obj, 'owner', None)
                        if owner:
                            owner_name = owner.get_full_name() or owner.username
                            product_name = prefix.product_name
                        break
                    except:
                        continue
        except:
            pass
        
        return render(request, 'pcontrol/access_denied.html', {
            'serial_number': serial_number,
            'owner_name': owner_name,
            'product_name': product_name,
        })


class ObjectDetailView(LoginRequiredMixin, View):
    """Универсальная страница просмотра объекта (только для авторизованных)"""
    
    login_url = '/login/'
    redirect_field_name = 'next'
    
    def get(self, request, serial_number):
        owner_name = 'Неизвестный контролер'
        product_name = 'Изделие'
        fields = {}
        created_at = None
        updated_at = None
        status = None
        status_display = None
        is_completed = False
        
        # Ищем объект во всех моделях
        prefixes = ProductPrefix.objects.filter(is_active=True).select_related('app')
        
        for prefix in prefixes:
            model = prefix.get_model()
            if model:
                try:
                    obj = model.objects.get(serial_number=serial_number)
                    owner = getattr(obj, 'owner', None)
                    
                    if owner:
                        owner_name = owner.get_full_name() or owner.username
                    product_name = prefix.product_name
                    
                    # Получаем статус
                    if hasattr(obj, 'status'):
                        status = obj.status
                        status_display = obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status
                        is_completed = status in ['completed', 'closed']
                    
                    # Получаем даты
                    if hasattr(obj, 'created_at'):
                        created_at = obj.created_at
                    if hasattr(obj, 'updated_at'):
                        updated_at = obj.updated_at
                    
                    # Получаем все поля объекта для отображения
                    for field in model._meta.fields:
                        field_name = field.name
                        if field_name in ['id', 'owner', 'serial_number', 'created_at', 'updated_at']:
                            continue
                        
                        value = getattr(obj, field_name, None)
                        if value and not callable(value):
                            if isinstance(value, str) and value.strip():
                                fields[field.verbose_name] = value
                            elif not isinstance(value, str):
                                fields[field.verbose_name] = value
                    
                    break
                except:
                    continue
        
        return render(request, 'pcontrol/object_detail.html', {
            'serial_number': serial_number,
            'owner_name': owner_name,
            'product_name': product_name,
            'fields': fields,
            'created_at': created_at,
            'updated_at': updated_at,
            'status': status,
            'status_display': status_display,
            'is_completed': is_completed,
        })


class UnknownSerialView(LoginRequiredMixin, View):
    """Страница для неизвестного серийного номера (только для авторизованных)"""
    
    login_url = '/login/'
    redirect_field_name = 'next'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '⚠️ Для доступа необходимо авторизоваться.')
            return redirect('pcontrol:main_page')
        
        is_allowed = (
            request.user.is_superuser or 
            request.user.groups.filter(name='Контролер').exists()
        )
        
        if not is_allowed:
            messages.error(
                request, 
                '⛔ У вас нет прав для создания объектов. '
                'Только суперпользователи и контролеры могут создавать объекты.'
            )
            return redirect('pcontrol:main_page')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, serial_number):
        matched_prefix = None
        prefixes = ProductPrefix.objects.filter(is_active=True).select_related('app').order_by('-prefix')
        
        for prefix_data in prefixes:
            if serial_number.startswith(prefix_data.prefix):
                matched_prefix = prefix_data
                break
        
        if matched_prefix:
            return self.create_and_redirect(request, serial_number, matched_prefix)
        
        available_prefixes = ProductPrefix.objects.filter(is_active=True).select_related('app').values(
            'app__app_label',
            'app__app_name',
            'product_name', 
            'model_name',
            'prefix'
        ).distinct().order_by('app__app_name', 'product_name')
        
        available_apps = []
        for item in available_prefixes:
            available_apps.append({
                'app_label': item['app__app_label'],
                'app_name': item['app__app_name'],
                'product_name': item['product_name'],
                'model_name': item['model_name'],
                'prefix': item['prefix']
            })
        
        user_groups = [g.name for g in request.user.groups.all()]
        
        return render(request, 'pcontrol/unknown.html', {
            'serial_number': serial_number,
            'available_apps': available_apps,
            'is_admin': request.user.is_superuser,
            'is_controller': 'Контролер' in user_groups,
            'is_auditor': 'Аудитор' in user_groups,
            'has_prefix': False,
            'user_groups': user_groups,
        })
    
    def create_and_redirect(self, request, serial_number, prefix):
        try:
            model = prefix.get_model()
            if not model:
                messages.error(request, f'Модель для приложения {prefix.app.app_label} не найдена')
                return redirect('pcontrol:main_page')
            
            existing_obj = model.objects.filter(serial_number=serial_number).first()
            if existing_obj:
                owner = getattr(existing_obj, 'owner', None)
                if owner and owner != request.user:
                    owner_full_name = owner.get_full_name() or owner.username
                    if owner.groups.filter(name='Контролер').exists():
                        return render(request, 'pcontrol/access_denied.html', {
                            'serial_number': serial_number,
                            'owner_name': owner_full_name,
                            'product_name': prefix.product_name,
                        })
                    else:
                        messages.warning(
                            request,
                            f'⚠️ Объект с серийным номером {serial_number} уже существует и принадлежит '
                            f'пользователю {owner_full_name}.'
                        )
                else:
                    messages.info(request, f'ℹ️ Объект с серийным номером {serial_number} уже существует')
                
                edit_url = prefix.get_edit_url(serial_number)
                if edit_url:
                    return redirect(edit_url)
                return redirect('pcontrol:main_page')
            
            create_kwargs = {
                'serial_number': serial_number,
            }
            
            if hasattr(model, 'status'):
                create_kwargs['status'] = 'draft'
            
            if hasattr(model, 'owner'):
                create_kwargs['owner'] = request.user
            
            obj = model.objects.create(**create_kwargs)
            
            messages.success(
                request, 
                f'✅ Создан новый объект "{prefix.product_name}" с серийным номером {serial_number}'
            )
            
            edit_url = prefix.get_edit_url(serial_number)
            if edit_url:
                return redirect(edit_url)
            
            messages.error(request, '❌ Не удалось определить URL для редактирования')
            return redirect('pcontrol:main_page')
            
        except Exception as e:
            logger.error(f"Ошибка создания объекта: {e}")
            messages.error(request, f'❌ Ошибка создания объекта: {str(e)}')
            return redirect('pcontrol:main_page')
    
    def post(self, request, serial_number):
        app_label = request.POST.get('app_label')
        
        if not app_label:
            messages.error(request, '❌ Выберите тип изделия')
            return redirect('pcontrol:unknown', serial_number=serial_number)
        
        try:
            app = Application.objects.get(app_label=app_label)
            prefix = ProductPrefix.objects.filter(app=app, is_active=True).first()
            
            if not prefix:
                messages.error(request, f'❌ Приложение {app_label} не зарегистрировано')
                return redirect('pcontrol:unknown', serial_number=serial_number)
            
            return self.create_and_redirect(request, serial_number, prefix)
            
        except Application.DoesNotExist:
            messages.error(request, f'❌ Приложение "{app_label}" не найдено')
            return redirect('pcontrol:unknown', serial_number=serial_number)
        except Exception as e:
            logger.error(f"Ошибка создания объекта: {e}")
            messages.error(request, f'❌ Ошибка создания объекта: {str(e)}')
            return redirect('pcontrol:unknown', serial_number=serial_number)