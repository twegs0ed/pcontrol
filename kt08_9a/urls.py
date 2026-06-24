# kt08_9a/urls.py
from django.urls import path
from . import views

app_name = 'kt08_9a'

urlpatterns = [
    path('', views.KT08_9aListView.as_view(), name='control_list'),
    path('create/', views.KT08_9aCreateView.as_view(), name='control_create'),
    path('scan-serial/', views.KT08_9aScanSerialView.as_view(), name='scan_serial'),  # <-- БЕЗ /control/
    path('check-serial/', views.KT08_9aCheckSerialView.as_view(), name='check_serial'),
    path('<int:pk>/', views.KT08_9aDetailView.as_view(), name='control_detail'),
    path('edit/<str:serial_number>/', views.KT08_9aUpdateView.as_view(), name='control_edit'),
    path('delete/<int:pk>/', views.KT08_9aDeleteView.as_view(), name='control_delete'),
    path('close/<int:pk>/', views.KT08_9aCloseView.as_view(), name='control_close'),
]