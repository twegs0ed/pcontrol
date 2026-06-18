from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    ControlListView, ControlDetailView, 
    ControlCreateView, ControlUpdateView, ControlDeleteView,
    CheckSerialView, ScanSerialView
)

urlpatterns = [
    path('control/create/', ControlCreateView.as_view(), name='control_create'),
    path('control/edit/<str:serial_number>/', ControlUpdateView.as_view(), name='control_edit'),
    path('control/delete/<int:pk>/', ControlDeleteView.as_view(), name='control_delete'),
    path('control/check-serial/', CheckSerialView.as_view(), name='check_serial'),
    path('control/scan-serial/', ScanSerialView.as_view(), name='scan_serial'),
    path('controls/', ControlListView.as_view(), name='gs14_control_list'),
    path('control/<int:pk>/', ControlDetailView.as_view(), name='control_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)