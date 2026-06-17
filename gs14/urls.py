# urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import MyWizard, ControlListView, ControlDetailView, ControlDeleteView
from .forms import SerialNumberForm, MainInfoForm

form_list = [SerialNumberForm, MainInfoForm]

condition_dict = {
    '1': True
}

urlpatterns = [
    path('control/create/', MyWizard.as_view(form_list, condition_dict=condition_dict), name='control_create'),
    path('control/edit/<str:serial_number>/', MyWizard.as_view(form_list, condition_dict=condition_dict), name='control_edit'),
    path('control/delete/<int:pk>/', ControlDeleteView.as_view(), name='control_delete'),
    path('controls/', ControlListView.as_view(), name='gs14_control_list'),
    path('control/<int:pk>/', ControlDetailView.as_view(), name='control_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)