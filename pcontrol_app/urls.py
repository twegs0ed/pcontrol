# pcontrol_app/urls.py
from django.urls import path
from . import views

app_name = 'pcontrol'

urlpatterns = [
    # Главная страница
    path('', views.MainPageView.as_view(), name='index'),
    
    # Сканирование
    path('scan-serial/', views.ScanSerialView.as_view(), name='scan_serial'),
    
    # AJAX
    path('check-serial-ajax/', views.CheckSerialAjaxView.as_view(), name='check_serial_ajax'),
    
    # Страницы
    path('access-denied/<str:serial_number>/', views.AccessDeniedView.as_view(), name='access_denied'),
]