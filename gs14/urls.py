# gs14/urls.py
from django.urls import path
from . import views

app_name = 'gs14'

urlpatterns = [
    # Список объектов
    path('', views.ControlListView.as_view(), name='control_list'),
    
    # Создание объекта
    path('create/', views.ControlCreateView.as_view(), name='control_create'),
    
    # Сканирование серийного номера (ДОЛЖНО БЫТЬ ДО <int:pk>)
    path('scan-serial/', views.ScanSerialView.as_view(), name='scan_serial'),
    
    # Проверка серийного номера
    path('check-serial/', views.CheckSerialView.as_view(), name='check_serial'),
    
    # Детальный просмотр (через pk) - должно быть ПОСЛЕ всех конкретных путей
    path('<int:pk>/', views.ControlDetailView.as_view(), name='control_detail'),
    
    # Редактирование (через serial_number)
    path('edit/<str:serial_number>/', views.ControlUpdateView.as_view(), name='control_edit'),
    
    # Удаление (через pk)
    path('delete/<int:pk>/', views.ControlDeleteView.as_view(), name='control_delete'),
    
    # Закрытие (через pk)
    path('close/<int:pk>/', views.ControlCloseView.as_view(), name='control_close'),
]