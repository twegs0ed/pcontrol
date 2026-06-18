from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.urls import reverse_lazy
from django.http import JsonResponse
from .forms import ControlForm
from .models import Control
import os
import logging

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
        """Проверка существования объекта перед созданием"""
        serial_number = request.POST.get('serial_number')
        
        if serial_number:
            # Проверяем, существует ли объект с таким серийным номером
            try:
                existing_obj = Control.objects.get(serial_number=serial_number)
                messages.warning(
                    request, 
                    f'Объект с серийным номером {serial_number} уже существует. '
                    f'Вы будете перенаправлены на страницу редактирования.'
                )
                return redirect('control_edit', serial_number=serial_number)
            except Control.DoesNotExist:
                # Объект не найден, продолжаем создание
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
        # Получаем объект до сохранения
        obj = form.instance
        
        # Проверяем чекбоксы удаления
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
        for field in image_fields:
            delete_key = f'delete_{field}'
            if self.request.POST.get(delete_key):
                # Удаляем изображение
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
    """Проверка существования серийного номера и перенаправление"""
    def post(self, request):
        serial_number = request.POST.get('serial_number', '').strip()
        
        if not serial_number:
            messages.error(request, 'Введите серийный номер')
            return redirect('control_create')
        
        try:
            # Проверяем существование объекта
            obj = Control.objects.get(serial_number=serial_number)
            messages.info(request, f'Объект с серийным номером {serial_number} найден. Переход к редактированию.')
            return redirect('control_edit', serial_number=serial_number)
        except Control.DoesNotExist:
            # Объект не найден, создаем новый
            messages.success(request, f'Создан новый объект с серийным номером {serial_number}.')
            # Создаем новый объект
            obj = Control.objects.create(serial_number=serial_number)
            return redirect('control_edit', serial_number=serial_number)