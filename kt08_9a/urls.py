# kt08_9a/urls.py
from django.urls import path
from . import views

app_name = 'kt08_9a'

urlpatterns = [
    # Список объектов
    path('', views. KT08_9aListView.as_view(), name='control_list'),
    
    # Создание объекта
    path('create/', views.KT08_9aCreateView.as_view(), name='control_create'),
    
    # Сканирование серийного номера
    path('scan-serial/', views.KT08_9aScanSerialView.as_view(), name='scan_serial'),
    
    # Проверка серийного номера
    path('check-serial/', views.KT08_9aCheckSerialView.as_view(), name='check_serial'),
    
    # AJAX-эндпоинты
    path('ajax-save-image/<int:pk>/<str:field_name>/', views.ajax_save_image, name='ajax_save_image'),
    path('ajax-save-title/<int:pk>/<str:field_name>/', views.ajax_save_title, name='ajax_save_title'),
    path('ajax-check-completed/<int:pk>/', views.ajax_check_completed, name='ajax_check_completed'),
    path('ajax-delete-image/<int:pk>/<str:field_name>/', views.ajax_delete_image, name='ajax_delete_image'),
    
    # Детальный просмотр
    path('<int:pk>/', views.KT08_9aDetailView.as_view(), name='control_detail'),
    
    # Редактирование (через serial_number)
    path('edit/<str:serial_number>/', views.KT08_9aUpdateView.as_view(), name='control_edit'),
    
    # Удаление (через pk)
    path('delete/<int:pk>/', views.KT08_9aDeleteView.as_view(), name='control_delete'),
    
    # Закрытие (через pk)
    path('close/<int:pk>/', views.KT08_9aCloseView.as_view(), name='control_close'),
]