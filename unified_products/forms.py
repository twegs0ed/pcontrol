from django import forms
from .models import Category, Product, ProductImage


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'prefix', 'image_count', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название категории'
            }),
            'prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Префикс серийного номера'
            }),
            'image_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['serial_number', 'category', 'description', 'serial_photo']
        widgets = {
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите серийный номер',
                'autofocus': True,
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите описание...'
            }),
            'serial_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        is_create = kwargs.pop('is_create', False)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Ограничиваем категории только активными
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        
        if is_create:
            self.fields['serial_number'].widget.attrs['autofocus'] = True
        
        if self.instance and self.instance.pk and not is_create:
            if user and not user.is_superuser:
                self.fields['serial_number'].widget.attrs['readonly'] = True
                self.fields['serial_number'].widget.attrs['class'] = 'form-control bg-light'
                self.fields['serial_number'].help_text = 'Только администратор может изменить серийный номер'


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['title', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }




