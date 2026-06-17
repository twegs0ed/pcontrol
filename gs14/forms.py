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
        }),
        help_text='Введите уникальный серийный номер устройства'
    )

class MainInfoForm(forms.ModelForm):
    class Meta:
        model = Control
        fields = [
            'description', 
            'title1', 'image1', 
            'title2', 'image2', 
            'title3', 'image3', 
            'title4', 'image4',
            'title5', 'image5', 
            'title6', 'image6',
            'title7', 'image7'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Введите описание объекта...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка всех текстовых полей
        text_fields = ['title1', 'title2', 'title3', 'title4', 'title5', 'title6', 'title7']
        for field_name in text_fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'placeholder': f'Введите заголовок'
            })
        
        # Настройка всех полей для изображений с поддержкой камеры
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
        for field_name in image_fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'accept': 'image/*',  # Разрешаем только изображения
                'capture': 'environment',  # Запускаем камеру
                'style': 'padding: 10px;'
            })