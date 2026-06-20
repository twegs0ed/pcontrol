# kt08_9a/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.KT08_9aListView.as_view(), name='kt08_9a_list'),
    path('create/', views.KT08_9aCreateView.as_view(), name='kt08_9a_create'),
    path('edit/<str:serial_number>/', views.KT08_9aUpdateView.as_view(), name='kt08_9a_edit'),
    path('delete/<int:pk>/', views.KT08_9aDeleteView.as_view(), name='kt08_9a_delete'),
    path('detail/<int:pk>/', views.KT08_9aDetailView.as_view(), name='kt08_9a_detail'),
    path('check-serial/', views.KT08_9aCheckSerialView.as_view(), name='kt08_9a_check_serial'),
    path('scan-serial/', views.KT08_9aScanSerialView.as_view(), name='kt08_9a_scan_serial'),
]