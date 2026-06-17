from django.forms import ClearableFileInput

class CameraFileInput(ClearableFileInput):
    """
    Виджет для загрузки файлов с поддержкой камеры на мобильных устройствах
    """
    template_name = 'widgets/camera_file_input.html'
    
    class Media:
        css = {
            'all': ('css/camera_widget.css',)
        }
        js = ('js/camera_widget.js',)