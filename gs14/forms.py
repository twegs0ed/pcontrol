from django import forms
from .models import Control

class ControlForm(forms.ModelForm):
    class Meta:
        model = Control
        fields = '__all__'
        exclude = ['created_at', 'updated_at']
        widgets = {
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите серийный номер',
            }),
            'serial_photo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Введите описание объекта...'
            }),
            'title1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title3': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title4': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title5': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title6': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title7': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'image1': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image2': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image3': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image4': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image5': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image6': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image7': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка текстовых полей
        text_fields = ['title1', 'title2', 'title3', 'title4', 'title5', 'title6', 'title7']
        for field_name in text_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': 'Введите заголовок'
                })
        
        # Настройка полей изображений с поддержкой камеры
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'serial_photo']
        for field_name in image_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'accept': 'image/*',
                    'capture': 'environment',
                    'style': 'padding: 10px;'
                })
        
        # Делаем поля необязательными при редактировании
        if self.instance and self.instance.pk:
            for field in self.fields.values():
                field.required = False