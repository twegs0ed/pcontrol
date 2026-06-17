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
                'placeholder': 'Введите описание объекта...',
                'id': 'id_description'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Общие атрибуты для всех текстовых полей
        common_widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите заголовок'
        })
        
        # Применяем ко всем текстовым полям
        text_fields = ['title1', 'title2', 'title3', 'title4', 'title5', 'title6', 'title7']
        for field_name in text_fields:
            self.fields[field_name].widget = common_widget
        
        # Для полей изображений добавляем классы
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
        for field_name in image_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'accept': 'image/*'
                })