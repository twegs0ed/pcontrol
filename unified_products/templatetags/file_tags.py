from django import template
import os

register = template.Library()

@register.simple_tag
def get_file_type(file):
    """Определяет тип файла: image или video"""
    if not file:
        return 'unknown'
    # FieldFile не имеет content_type, определяем по расширению
    if hasattr(file, 'name') and file.name:
        ext = os.path.splitext(file.name)[1].lower()
        if ext in ('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.m4v', '.mpg', '.wmv'):
            return 'video'
        elif ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.tiff'):
            return 'image'
    # Если нет имени, фоллбэк на расширение URL
    if hasattr(file, 'url') and file.url:
        ext = os.path.splitext(file.url)[1].lower()
        if ext in ('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.m4v', '.mpg', '.wmv'):
            return 'video'
    # По умолчанию считаем изображением
    return 'image'