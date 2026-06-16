# urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import MyWizard, ControlListView, ControlDetailView
from .forms import SerialNumberForm, MainInfoForm

# Список форм
form_list = [SerialNumberForm, MainInfoForm]

# Условия показа шагов
condition_dict = {
    '1': lambda wizard: True
}

urlpatterns = [
    # Wizard форма
    path('wizard/', MyWizard.as_view(form_list, condition_dict=condition_dict), name='my_wizard'),
    
    # Список объектов
    path('controls/', ControlListView.as_view(), name='control_list'),
    
    # Детальная страница объекта
    path('control/<int:pk>/', ControlDetailView.as_view(), name='control_detail'),
    
    # Редактирование объекта
    path('control/edit/<str:serial_number>/', MyWizard.as_view(form_list, condition_dict=condition_dict), name='control_edit'),
]

# Добавляем URL для медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)