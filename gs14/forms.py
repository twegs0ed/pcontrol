from django import forms
from .models import Control

class ControlForm(forms.ModelForm):
    class Meta:
        model = Control
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
            # Title поля
            'title1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title3': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title4': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title5': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title6': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'title7': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            # Image поля
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
        # Получаем параметр is_create
        is_create = kwargs.pop('is_create', False)
        # Получаем пользователя для проверки прав
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Настройка всех текстовых полей (title1-title7)
        text_fields = ['title1', 'title2', 'title3', 'title4', 'title5', 'title6', 'title7']
        for field_name in text_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': 'Введите заголовок'
                })
        
        # Настройка всех полей изображений (image1-image7)
        image_fields = ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']
        for field_name in image_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'accept': 'image/*',
                    'capture': 'environment',
                    'style': 'padding: 10px;'
                })
        
        # === ПРИ СОЗДАНИИ: все поля кроме serial_number - неактивны ===
        if is_create:
            # Список полей, которые должны остаться активными
            active_fields = ['serial_number']
            
            # Делаем все поля неактивными, кроме указанных
            for field_name in self.fields:
                if field_name not in active_fields:
                    self.fields[field_name].widget.attrs['disabled'] = 'disabled'
                    self.fields[field_name].widget.attrs['class'] = 'form-control disabled-field'
                    self.fields[field_name].required = False
                    # Добавляем подсказку
                    self.fields[field_name].help_text = 'Будет доступно после создания объекта'
        
        # === ПРИ РЕДАКТИРОВАНИИ: проверяем права на серийный номер ===
        if self.instance and self.instance.pk and not is_create:
            # Делаем все поля активными
            for field in self.fields.values():
                field.required = False
            
            # Если пользователь НЕ суперпользователь - блокируем поле serial_number
            if user and not user.is_superuser:
                self.fields['serial_number'].widget.attrs['readonly'] = True
                self.fields['serial_number'].widget.attrs['class'] = 'form-control bg-light'
                self.fields['serial_number'].help_text = 'Только администратор может изменить серийный номер'
                self.fields['serial_number'].required = False