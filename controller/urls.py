from django.urls import path
from . import views

app_name = 'controller'

urlpatterns = [
    path('', views.control_list, name='control_list'),
    path('create/', views.control_create, name='control_create'),
    path('<int:pk>/', views.control_detail, name='control_detail'),
    path('<int:pk>/edit/', views.control_edit, name='control_edit'),
    path('<int:pk>/delete/', views.control_delete, name='control_delete'),
]
