# kt08_9a/forms.py
from django import forms
from .models import KT08_9a

class KT08_9aForm(forms.ModelForm):
    class Meta:
        model = KT08_9a
        fields = '__all__'
        exclude = ['created_at', 'updated_at', 'owner', 'serial_photo']
        widgets = {
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите серийный номер',
                'autofocus': True,
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
            'image1': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image2': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image3': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image4': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image5': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image6': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
            'image7': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'padding: 10px;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        is_create = kwargs.pop('is_create', False)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Настройка текстовых полей
        text_fields = ['title1', 'title2', 'title3', 'title4', 'title5', 'title6', 'title7']
        for field_name in text_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': 'Введите заголовок'
                })
        
        # Настройка полей изображений
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
        for field_name in image_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'accept': 'image/*',
                    'capture': 'environment',
                    'style': 'padding: 10px;'
                })
        
        # При создании: только serial_number активен
        if is_create:
            for field_name in self.fields:
                if field_name != 'serial_number':
                    self.fields[field_name].widget.attrs['disabled'] = 'disabled'
                    self.fields[field_name].widget.attrs['class'] = 'form-control disabled-field'
                    self.fields[field_name].required = False
                    self.fields[field_name].help_text = 'Будет доступно после создания объекта'
        
        # При редактировании
        if self.instance and self.instance.pk and not is_create:
            for field in self.fields.values():
                field.required = False
            
            if user and not user.is_superuser:
                self.fields['serial_number'].widget.attrs['readonly'] = True
                self.fields['serial_number'].widget.attrs['class'] = 'form-control bg-light'
                self.fields['serial_number'].help_text = 'Только администратор может изменить серийный номер'
                self.fields['serial_number'].required = False