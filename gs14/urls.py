# gs14/urls.py
from django.urls import path
from . import views

app_name = 'gs14'

urlpatterns = [
    # Список объектов
    path('', views.ControlListView.as_view(), name='control_list'),
    
    # Создание объекта
    path('create/', views.ControlCreateView.as_view(), name='control_create'),
    
    # Сканирование серийного номера
    path('scan-serial/', views.ScanSerialView.as_view(), name='scan_serial'),
    
    # Проверка серийного номера
    path('check-serial/', views.CheckSerialView.as_view(), name='check_serial'),
    
    # AJAX-эндпоинты
    path('ajax-save-image/<int:pk>/<str:field_name>/', views.ajax_save_image, name='ajax_save_image'),
    path('ajax-save-title/<int:pk>/<str:field_name>/', views.ajax_save_title, name='ajax_save_title'),
    path('ajax-check-completed/<int:pk>/', views.ajax_check_completed, name='ajax_check_completed'),
    
    # Детальный просмотр
    path('<int:pk>/', views.ControlDetailView.as_view(), name='control_detail'),
    
    # Редактирование (через serial_number)
    path('edit/<str:serial_number>/', views.ControlUpdateView.as_view(), name='control_edit'),
    
    # Удаление (через pk)
    path('delete/<int:pk>/', views.ControlDeleteView.as_view(), name='control_delete'),
    
    # Закрытие (через pk)
    path('close/<int:pk>/', views.ControlCloseView.as_view(), name='control_close'),
]