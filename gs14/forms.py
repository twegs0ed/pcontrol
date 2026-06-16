# forms.py
from django import forms
from .models import Control

class SerialNumberForm(forms.Form):
    serial_number = forms.CharField(
        max_length=100, 
        label='Серийный номер',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите серийный номер',
            'autofocus': True,
            'id': 'id_serial_number'
        }),
        help_text='Введите уникальный серийный номер устройства'
    )

class MainInfoForm(forms.ModelForm):
    class Meta:
        model = Control
        fields = ['description', 'title1', 'image1']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Введите описание объекта...',
                'id': 'id_description'
            }),
            'title1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок',
                'id': 'id_title1'
            }),
            'image1': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_image1'
            }),
        }
        labels = {
            'description': 'Описание',
            'title1': 'Заголовок',
            'image1': 'Изображение',
        }
        help_texts = {
            'description': 'Подробное описание объекта (до 500 символов)',
            'title1': 'Краткий заголовок объекта',
            'image1': 'Загрузите изображение в формате JPG, PNG или GIF',
        }