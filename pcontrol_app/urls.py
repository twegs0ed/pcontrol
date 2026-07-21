# pcontrol_app/urls.py
from django.urls import path
from . import views

app_name = 'pcontrol'

urlpatterns = [
    path('', views.MainPageView.as_view(), name='index'),
    path('', views.MainPageView.as_view(), name='main_page'),
    path('unknown/<str:serial_number>/', views.UnknownSerialView.as_view(), name='unknown'),
    path('access-denied/<str:serial_number>/', views.AccessDeniedView.as_view(), name='access_denied'),
    path('object-detail/<str:serial_number>/', views.ObjectDetailView.as_view(), name='object_detail'),
    path('check-serial-ajax/', views.CheckSerialAjaxView.as_view(), name='check_serial_ajax'),  
]