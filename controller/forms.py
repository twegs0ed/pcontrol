from django import forms
from .models import ControlRecord


class ControlRecordForm(forms.ModelForm):
    class Meta:
        model = ControlRecord
        fields = ['worker', 'batch_size', 'shift_photo', 'notes']
        widgets = {
            'worker': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ФИО рабочего',
            }),
            'batch_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'id': 'id_batch_size',
            }),
            'shift_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Примечания...',
            }),
        }
