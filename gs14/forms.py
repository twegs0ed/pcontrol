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
            'image1': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image2': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image3': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image4': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image5': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image6': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image7': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Делаем поля необязательными при редактировании
        if self.instance and self.instance.pk:
            for field in self.fields.values():
                field.required = False