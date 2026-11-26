from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.views import View
from django.contrib.auth.models import User
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
import json
import logging
import os
import io
import sys
import re
from PIL import Image, ImageEnhance
import pytesseract
import tempfile
import time
import base64
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.contrib.auth.decorators import login_required

from .models import Category, Product, ProductImage
from .forms import CategoryForm, ProductForm, ProductImageForm

logger = logging.getLogger(__name__)

# Путь к Tesseract
if sys.platform == 'win32':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
elif sys.platform == 'linux':
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
elif sys.platform == 'darwin':
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'






def get_user_full_name(user):
    """Безопасное получение полного имени пользователя"""
    if not user:
        return "-"
    try:
        if user.first_name and user.last_name:
            return f"{user.last_name} {user.first_name}"
        elif user.first_name:
            return user.first_name
        elif user.last_name:
            return user.last_name
        else:
            return user.username or "-"
    except:
        return "-"


def get_username_safe(user):
    """Безопасное получение имени пользователя"""
    if not user:
        return "-"
    try:
        return user.username or "-"
    except:
        return "-"


def register_fonts():
    """Регистрация шрифтов для поддержки кириллицы в PDF"""
    try:
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/arial/arial.ttf',
            '/System/Library/Fonts/Helvetica.ttf',
            'C:/Windows/Fonts/arial.ttf',
            '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('CustomFont', path))
                return 'CustomFont'
        
        return 'Helvetica'
    except:
        return 'Helvetica'


@login_required
def export_single_product_pdf(request, pk):
    """
    Экспорт одного объекта в PDF с фотографиями
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch, cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
        from reportlab.platypus import KeepTogether
        
        product = get_object_or_404(Product, pk=pk)
        
        # Проверка прав
        if not product.can_view(request.user):
            messages.error(request, 'У вас нет прав для просмотра этого объекта')
            return redirect('unified_products:product_detail', pk=pk)
        
        FONT_NAME = register_fonts()
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            topMargin=2*cm, 
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        # Стиль заголовка
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=FONT_NAME,
            fontSize=20,
            textColor=colors.HexColor('#0d6efd'),
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=10,
            leading=24
        )
        
        # Стиль подзаголовка
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT,
            spaceAfter=8,
            spaceBefore=12,
            leading=18
        )
        
        # Стиль обычного текста
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            alignment=TA_LEFT,
            leading=14,
            spaceAfter=4
        )
        
        # Стиль для таблицы
        table_style = ParagraphStyle(
            'TableStyle',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=9,
            alignment=TA_LEFT,
            leading=12,
            spaceAfter=2
        )
        
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            alignment=TA_LEFT,
            leading=14,
            textColor=colors.whitesmoke,
            spaceAfter=2
        )
        
        elements = []
        
        # Заголовок
        elements.append(Paragraph(f'Отчет по изделию: {product.category.name} s/n {product.serial_number}', title_style))
        elements.append(Spacer(1, 12))
        
        # ===== ИНФОРМАЦИЯ =====
        elements.append(Paragraph('Основная информация', heading_style))
        elements.append(Spacer(1, 6))
        
        # Создаем данные для таблицы
        info_data = [
            ['Параметр', 'Значение'],
            ['Серийный номер', product.serial_number],
            ['Изделие', product.category.name],
            ['Ответственный контролер', get_user_full_name(product.owner)],
            ['Статус', product.get_status_display()],
            ['Дата начала проверки', timezone.localtime(product.created_at).strftime("%d.%m.%Y %H:%M")],
            ['Дата завершения проверки', timezone.localtime(product.completed_at).strftime("%d.%m.%Y %H:%M") if product.completed_at else 'Не завершена'],
            ['Закрыл', get_user_full_name(product.closed_by) if product.closed_by else '-'],
            ['Прогресс', f'{product.get_filled_count()}/{product.get_total_required()} ({product.get_progress_percent()}%)'],
            ['Описание', product.description or '-'],
        ]
        
        # Создаем таблицу
        info_table_data = []
        for row in info_data:
            info_table_data.append([
                Paragraph(row[0], table_style),
                Paragraph(str(row[1]), table_style)
            ])
        
        info_table = Table(info_table_data, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 16))
        
        # ===== ФОТОГРАФИИ =====
        elements.append(PageBreak())
        elements.append(Paragraph('Фотографии изделия', heading_style))
        elements.append(Spacer(1, 8))
        
        images = product.images.filter(image__isnull=False).exclude(image='').order_by('field_index')
        
        if images.exists():
            # Каждое изображение в отдельной строке с отступами от краев
            for idx, img in enumerate(images):
                try:
                    if img.image and hasattr(img.image, 'path') and img.image.path:
                        if os.path.exists(img.image.path) and os.path.getsize(img.image.path) > 0:
                            # Добавляем разрыв страницы перед каждым блоком (кроме первого)
                            if idx > 0:
                                elements.append(PageBreak())
                            
                            # Определяем тип файла
                            file_ext = os.path.splitext(img.image.path)[1].lower()
                            video_extensions = ('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.m4v', '.mpg', '.wmv')
                            
                            if file_ext in video_extensions:
                                # Для видео выводим сообщение
                                elements.append(Paragraph(
                                    f'<b>{img.title or f"Поле {img.field_index}"}</b>',
                                    ParagraphStyle(
                                        'ImageTitle',
                                        parent=normal_style,
                                        alignment=TA_CENTER,
                                        fontSize=10,
                                        spaceAfter=6
                                    )
                                ))
                                elements.append(Paragraph(
                                    f'<i>Видеоматериал в хорошем качестве доступен в приложении к отчету.</i>',
                                    ParagraphStyle(
                                        'VideoNotice',
                                        parent=normal_style,
                                        alignment=TA_CENTER,
                                        fontSize=9,
                                        textColor=colors.HexColor('#666666'),
                                        spaceAfter=12
                                    )
                                ))
                            else:
                                # Создаем таблицу для изображения с отступами
                                img_obj = Image(img.image.path, width=5.5*inch, height=5.5*inch, kind='proportional')
                                
                                # Заголовок
                                title = Paragraph(
                                    f'<b>{img.title or f"Поле {img.field_index}"}</b>',
                                    ParagraphStyle(
                                        'ImageTitle',
                                        parent=normal_style,
                                        alignment=TA_CENTER,
                                        fontSize=10,
                                        spaceAfter=6
                                    )
                                )
                                
                                # Ячейка с заголовком и изображением
                                cell_content = [[title], [img_obj]]
                                row_table = Table(cell_content, colWidths=[5.5*inch])
                                row_table.setStyle(TableStyle([
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                                    ('SPACEBETWEEN', (0, 0), (-1, -1), 8),
                                    ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
                                ]))
                                elements.append(row_table)
                                elements.append(Spacer(1, 12))
                except Exception as e:
                    print(f"Ошибка подготовки изображения {img.field_index}: {e}")
                    continue
        else:
            elements.append(Paragraph('Нет загруженных фотографий', normal_style))
        
        elements.append(Spacer(1, 12))
        
        # ===== ФОТО СЕРИЙНОГО НОМЕРА =====
        elements.append(PageBreak())
        elements.append(Paragraph('Фото серийного номера', heading_style))
        elements.append(Spacer(1, 6))
        
        if product.serial_photo and hasattr(product.serial_photo, 'path') and product.serial_photo.path:
            if os.path.exists(product.serial_photo.path) and os.path.getsize(product.serial_photo.path) > 0:
                try:
                    img = Image(product.serial_photo.path, width=3*inch, height=3*inch, kind='proportional')
                    elements.append(img)
                    elements.append(Spacer(1, 4))
                except Exception as e:
                    print(f"Ошибка добавления фото серийного номера: {e}")
                    elements.append(Paragraph('Не удалось загрузить фото серийного номера', normal_style))
            else:
                elements.append(Paragraph('Файл фото серийного номера отсутствует', normal_style))
        else:
            elements.append(Paragraph('Нет фото серийного номера', normal_style))
        
        # ===== ПОДПИСЬ =====
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            f'<i>Отчет сформирован: {timezone.localtime(timezone.now()).strftime("%d.%m.%Y %H:%M")}</i>',
            ParagraphStyle(
                'Footer',
                parent=normal_style,
                fontName=FONT_NAME,
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
        ))
        
        # Строим PDF
        doc.build(elements)
        buffer.seek(0)
        
        filename = f'product_{product.serial_number}_report.pdf'
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка экспорта PDF: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Ошибка при создании PDF: {str(e)}')
        return redirect('unified_products:product_detail', pk=pk)


@login_required
def export_single_product_word(request, pk):
    """
    Экспорт одного объекта в Word с фотографиями
    """
    try:
        from docx import Document
        from docx.shared import Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from PIL import Image
        import io
        
        product = get_object_or_404(Product, pk=pk)
        
        # Проверка прав
        if not product.can_view(request.user):
            messages.error(request, 'У вас нет прав для просмотра этого объекта')
            return redirect('unified_products:product_detail', pk=pk)
        
        # Создаем документ
        doc = Document()
        
        # Заголовок
        title = doc.add_heading(f'Отчет по изделию: {product.category.name} s/n {product.serial_number}', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Основная информация
        doc.add_heading('Основная информация', level=1)
        
        # Создаем таблицу с информацией
        table = doc.add_table(rows=9, cols=2)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        info = [
            ('Серийный номер:', product.serial_number),
            ('Изделие:', product.category.name),
            ('Ответственный контролер:', get_user_full_name(product.owner)),
            ('Статус:', product.get_status_display()),
            ('Дата начала проверки:', timezone.localtime(product.created_at).strftime("%d.%m.%Y %H:%M")),
            ('Дата завершения проверки:', timezone.localtime(product.completed_at).strftime("%d.%m.%Y %H:%M") if product.completed_at else 'Не завершена'),
            ('Закрыл:', get_user_full_name(product.closed_by) if product.closed_by else '-'),
            ('Описание:', product.description or '-'),
            ('Прогресс:', f'{product.get_filled_count()}/{product.get_total_required()} ({product.get_progress_percent()}%)'),
        ]
        
        for i, (label, value) in enumerate(info):
            row = table.rows[i]
            row.cells[0].text = label
            row.cells[0].paragraphs[0].runs[0].bold = True
            row.cells[1].text = str(value)
        
        doc.add_paragraph()
        
        # ===== ФОТОГРАФИИ =====
        doc.add_page_break()
        doc.add_heading('Фотографии изделия', level=1)
        
        images = product.images.filter(image__isnull=False).exclude(image='').order_by('field_index')
        
        if images.exists():
            image_added = False
            for idx, img in enumerate(images):
                title_text = img.title or f'Поле {img.field_index}'
                
                # Определяем тип файла
                file_ext = os.path.splitext(img.image.path)[1].lower() if hasattr(img.image, 'path') and img.image.path else ''
                video_extensions = ('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.m4v', '.mpg', '.wmv')
                
                # Добавляем разрыв страницы перед каждым блоком (кроме первого)
                if idx > 0:
                    doc.add_page_break()
                
                if file_ext in video_extensions:
                    # Для видео выводим сообщение
                    doc.add_heading(title_text, level=2)
                    doc.add_paragraph(
                        'Видеоматериал в хорошем качестве доступен в приложении к отчету.',
                        style='IntenseQuote'
                    )
                    image_added = True
                else:
                    # Создаем таблицу для рамки (1 колонка, 2 строки: заголовок + изображение)
                    table = doc.add_table(rows=2, cols=1)
                    table.style = 'Table Grid'
                    
                    # Ячейка с заголовком
                    cell_title = table.cell(0, 0)
                    title_para = cell_title.paragraphs[0]
                    title_run = title_para.add_run(title_text)
                    title_run.bold = True
                    
                    # Ячейка с изображением
                    cell_img = table.cell(1, 0)
                    
                    # Добавляем изображение
                    try:
                        if not img.image:
                            raise Exception("Файл не найден")
                        
                        if hasattr(img.image, 'path') and img.image.path:
                            image_path = img.image.path
                        else:
                            raise Exception("Ошибка пути файла")
                        
                        if not os.path.exists(image_path):
                            raise Exception("Файл не найден")
                        
                        if os.path.getsize(image_path) == 0:
                            raise Exception("Файл пустой")
                        
                        # Добавляем изображение в ячейку
                        from docx.shared import Inches
                        from PIL import Image as PILImage
                        pil_img = PILImage.open(image_path)
                        
                        # Конвертируем в RGB если нужно
                        if pil_img.mode in ('RGBA', 'LA', 'P'):
                            rgb_img = PILImage.new('RGB', pil_img.size, (255, 255, 255))
                            if pil_img.mode == 'P':
                                pil_img = pil_img.convert('RGBA')
                            if pil_img.mode in ('RGBA', 'LA'):
                                rgb_img.paste(pil_img, mask=pil_img.split()[-1])
                            else:
                                rgb_img.paste(pil_img)
                            pil_img = rgb_img
                        elif pil_img.mode != 'RGB':
                            pil_img = pil_img.convert('RGB')
                        
                        # Сохраняем в буфер
                        img_buffer = io.BytesIO()
                        pil_img.save(img_buffer, format='JPEG', quality=90)
                        img_buffer.seek(0)
                        
                        # Добавляем из буфера
                        cell_img.add_paragraph().add_run().add_picture(img_buffer, width=Inches(4))
                        
                        img_buffer.close()
                        
                        image_added = True
                    except Exception as e:
                        print(f"Ошибка добавления изображения: {e}")
                        import traceback
                        traceback.print_exc()
                        doc.add_paragraph(f'⚠️ Ошибка загрузки: {title_text}')
                        continue
            
            if not image_added:
                doc.add_paragraph('Не удалось добавить ни одного изображения')
        else:
            doc.add_paragraph('Нет загруженных фотографий')
        
        # ===== ФОТО СЕРИЙНОГО НОМЕРА =====
        doc.add_page_break()
        doc.add_heading('Фото серийного номера', level=1)
        if product.serial_photo:
            try:
                if product.serial_photo and hasattr(product.serial_photo, 'path') and product.serial_photo.path:
                    if os.path.exists(product.serial_photo.path) and os.path.getsize(product.serial_photo.path) > 0:
                        from docx.shared import Inches as docxInches
                        from PIL import Image as PILImage
                        pil_img = PILImage.open(product.serial_photo.path)
                        if pil_img.mode in ('RGBA', 'LA', 'P'):
                            rgb_img = PILImage.new('RGB', pil_img.size, (255, 255, 255))
                            if pil_img.mode == 'P':
                                pil_img = pil_img.convert('RGBA')
                            if pil_img.mode in ('RGBA', 'LA'):
                                rgb_img.paste(pil_img, mask=pil_img.split()[-1])
                            else:
                                rgb_img.paste(pil_img)
                            pil_img = rgb_img
                        elif pil_img.mode != 'RGB':
                            pil_img = pil_img.convert('RGB')
                        img_buffer = io.BytesIO()
                        pil_img.save(img_buffer, format='JPEG', quality=90)
                        img_buffer.seek(0)
                        doc.add_picture(img_buffer, width=docxInches(3))
                        img_buffer.close()
                    else:
                        doc.add_paragraph('Файл фото серийного номера отсутствует')
                else:
                    doc.add_paragraph('Нет фото серийного номера')
            except Exception as e:
                print(f"Ошибка добавления фото серийного номера: {e}")
                doc.add_paragraph('Не удалось загрузить фото серийного номера')
        else:
            doc.add_paragraph('Нет фото серийного номера')
        
        # Подпись
        doc.add_paragraph()
        doc.add_paragraph(f'Отчет сформирован: {timezone.localtime(timezone.now()).strftime("%d.%m.%Y %H:%M")}')
        
        # Сохраняем в буфер
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        # Формируем ответ
        filename = f'product_{product.serial_number}_report.docx'
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка экспорта Word: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Ошибка при создании Word: {str(e)}')
        return redirect('unified_products:product_detail', pk=pk)
    









# ==================== КАТЕГОРИИ ====================

class CategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список категорий"""
    model = Category
    template_name = 'unified_products/category_list.html'
    context_object_name = 'categories'
    ordering = ['name']
    
    def test_func(self):
        return self.request.user.is_superuser or \
               self.request.user.has_perm('unified_products.add_category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Категории изделий'
        context['app_name'] = 'Управление изделиями'
        context['namespace'] = 'unified_products'
        return context


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание категории"""
    model = Category
    form_class = CategoryForm
    template_name = 'unified_products/category_form.html'
    success_url = reverse_lazy('unified_products:category_list')
    
    def test_func(self):
        return self.request.user.is_superuser or \
               self.request.user.has_perm('unified_products.add_category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание категории'
        context['is_create'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Категория "{form.instance.name}" успешно создана!')
        return response


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование категории"""
    model = Category
    form_class = CategoryForm
    template_name = 'unified_products/category_form.html'
    success_url = reverse_lazy('unified_products:category_list')
    
    def test_func(self):
        return self.request.user.is_superuser or \
               self.request.user.has_perm('unified_products.change_category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование категории: {self.object.name}'
        context['is_create'] = False
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Категория "{form.instance.name}" успешно обновлена!')
        return response


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Удаление категории"""
    
    def test_func(self):
        return self.request.user.is_superuser or \
               self.request.user.has_perm('unified_products.delete_category')
    
    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        
        if Product.objects.filter(category=category).exists():
            messages.error(
                request,
                f'Нельзя удалить категорию "{category.name}", так как есть изделия, связанные с ней.'
            )
            return redirect('unified_products:category_list')
        
        category_name = category.name
        category.delete()
        messages.success(request, f'Категория "{category_name}" удалена.')
        return redirect('unified_products:category_list')


# ==================== ИЗДЕЛИЯ ====================

class ProductListView(LoginRequiredMixin, ListView):
    """Список изделий"""
    model = Product
    template_name ='unified_products/product_list.html'
    context_object_name = 'products'
    ordering = ['-created_at']
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('category', 'owner')
        
        # Фильтр по образцам
        is_sample_filter = self.request.GET.get('is_sample')
        if is_sample_filter == '1':
            qs = qs.filter(is_sample=True)
        elif is_sample_filter == '0':
            qs = qs.filter(is_sample=False)
        
        # Фильтр по категории
        category_filter = self.request.GET.get('category')
        if category_filter:
            qs = qs.filter(category_id=category_filter)
        
        # Фильтр по статусу
        status_filter = self.request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        # ===== ФИЛЬТР ПО ВЛАДЕЛЬЦУ (ПОИСК) =====
        owner_search = self.request.GET.get('owner_search', '').strip()
        if owner_search:
            # Простой поиск по username, first_name, last_name
            qs = qs.filter(
                models.Q(owner__username__icontains=owner_search) |
                models.Q(owner__first_name__icontains=owner_search) |
                models.Q(owner__last_name__icontains=owner_search)
            )
        
        # Фильтр по дате
        date_from = self.request.GET.get('date_from')
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                qs = qs.filter(created_at__date__gte=date_from_obj.date())
            except ValueError:
                pass
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                qs = qs.filter(created_at__date__lte=date_to_obj.date())
            except ValueError:
                pass
        
        # Поиск
        search_query = self.request.GET.get('search')
        if search_query:
            qs = qs.filter(
                models.Q(serial_number__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        
        # Права доступа
        user = self.request.user
        if not user.is_superuser:
            if user.groups.filter(name='Аудитор').exists():
                return qs
            elif user.groups.filter(name='Контролер').exists():
                return qs.filter(owner=user)
            else:
                return qs.none()
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        is_sample_filter = self.request.GET.get('is_sample')
        if is_sample_filter == '1':
            context['title'] = 'Образцы изделий'
            context['is_sample_view'] = True
        else:
            context['title'] = 'Список изделий'
            context['is_sample_view'] = False
        
        context['categories'] = Category.objects.filter(is_active=True)
        context['is_controller'] = self.request.user.groups.filter(name='Контролер').exists()
        context['is_auditor'] = self.request.user.groups.filter(name='Аудитор').exists()
        context['app_name'] = 'Управление изделиями'
        context['namespace'] = 'unified_products'
        
        # ===== СОХРАНЯЕМ ТЕКУЩИЕ ПАРАМЕТРЫ ФИЛЬТРОВ =====
        context['current_filters'] = {
            'category': self.request.GET.get('category', ''),
            'status': self.request.GET.get('status', ''),
            'owner_search': self.request.GET.get('owner_search', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'search': self.request.GET.get('search', ''),
            'is_sample': self.request.GET.get('is_sample', ''),
        }
        
        # Добавляем can_edit для каждого объекта
        user = self.request.user
        for product in context['products']:
            product.can_edit = product.can_edit(user)
        
        return context

class ProductDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница изделия"""
    model = Product
    template_name = 'unified_products/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('category', 'owner', 'closed_by')
        user = self.request.user
        
        if not user.is_superuser:
            if user.groups.filter(name='Аудитор').exists():
                return qs
            elif user.groups.filter(name='Контролер').exists():
                return qs.filter(owner=user)
            else:
                return qs.none()
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Изделие {self.object.serial_number}'
        context['images'] = self.object.images.all().order_by('field_index')
        context['can_edit'] = self.object.can_edit(self.request.user)
        context['app_name'] = 'Управление изделиями'
        context['namespace'] = 'unified_products'
        context['is_completed'] = self.object.is_completed()
        return context


class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание изделия"""
    model = Product
    form_class = ProductForm
    template_name = 'unified_products/product_form.html'
    
    def get_success_url(self):
        if self.object:
            return reverse('unified_products:product_edit', kwargs={'serial_number': self.object.serial_number})
        return reverse('unified_products:product_list')
    
    def test_func(self):
        return self.request.user.is_superuser or \
               self.request.user.groups.filter(name='Контролер').exists()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_create'] = True
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание изделия'
        context['is_create'] = True
        context['is_superuser'] = self.request.user.is_superuser
        context['categories'] = Category.objects.filter(is_active=True)
        context['scan_url'] = '/unified-products/scan-serial/'
        context['app_name'] = 'Управление изделиями'
        context['namespace'] = 'unified_products'
        context['header_color'] = 'bg-primary'
        
        sample = None
        category_id = self.request.GET.get('category') or self.request.POST.get('category')
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                sample = category.products.filter(is_sample=True).first()
            except Category.DoesNotExist:
                pass
        
        context['sample'] = sample
        context['categories_json'] = [
            {'id': cat.id, 'name': cat.name, 'prefix': cat.prefix}
            for cat in Category.objects.filter(is_active=True)
        ]
        
        return context
    
    def post(self, request, *args, **kwargs):
        serial_number = request.POST.get('serial_number', '').strip()
        category_id = request.POST.get('category')
        
        if serial_number:
            try:
                existing = Product.objects.get(serial_number=serial_number)
                messages.warning(
                    request,
                    f'Изделие с серийным номером {serial_number} уже существует.'
                )
                return redirect('unified_products:product_edit', serial_number=serial_number)
            except Product.DoesNotExist:
                pass
        
        if not category_id and serial_number:
            categories = Category.objects.filter(is_active=True)
            for cat in categories:
                if serial_number.startswith(cat.prefix):
                    post_data = request.POST.copy()
                    post_data['category'] = cat.id
                    request.POST = post_data
                    break
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        
        # ===== СОХРАНЯЕМ ФОТО СЕРИЙНОГО НОМЕРА =====
        # 1. Из загруженного файла
        if 'serial_photo' in self.request.FILES:
            form.instance.serial_photo = self.request.FILES['serial_photo']
            logger.info(f"Фото серийного номера загружено из файла")
        
        # 2. Из сканирования (base64)
        elif 'scanned_photo_base64' in self.request.POST:
            photo_data = self.request.POST.get('scanned_photo_base64', '')
            if photo_data and ';base64,' in photo_data:
                try:
                    import base64
                    from django.core.files.base import ContentFile
                    format_part, imgstr = photo_data.split(';base64,')
                    ext = format_part.split('/')[-1] if '/' in format_part else 'jpg'
                    image_data = base64.b64decode(imgstr)
                    if image_data and len(image_data) > 1000:
                        form.instance.serial_photo.save(
                            f'serial_photo_{form.instance.serial_number}.{ext}',
                            ContentFile(image_data),
                            save=False
                        )
                        logger.info(f"Фото серийного номера сохранено из сканирования")
                except Exception as e:
                    logger.error(f"Ошибка сохранения фото из сканирования: {e}")
        
        response = super().form_valid(form)
        
        # Копируем заголовки из образца
        sample = form.instance.category.products.filter(is_sample=True).first()
        if sample:
            self.copy_sample_titles(form.instance, sample)
        
        messages.success(
            self.request,
            f'✅ Изделие с серийным номером {form.instance.serial_number} успешно создано.'
        )
        
        return response
    
    def copy_sample_titles(self, product, sample):
        """Копирует только заголовки из образца в новый продукт"""
        try:
            for sample_image in sample.images.all():
                try:
                    product_image = ProductImage.objects.get(
                        product=product,
                        field_index=sample_image.field_index
                    )
                    if sample_image.title:
                        product_image.title = sample_image.title
                        product_image.save()
                except ProductImage.DoesNotExist:
                    pass
            
            if sample.description:
                product.description = sample.description
                product.save(update_fields=['description'])
            
            logger.info(f"Заголовки из образца скопированы в {product.serial_number}")
            
        except Exception as e:
            logger.error(f"Ошибка копирования заголовков из образца: {e}")


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование изделия"""
    model = Product
    form_class = ProductForm
    template_name = 'unified_products/product_form.html'
    
    def test_func(self):
        obj = self.get_object()
        return obj.can_edit(self.request.user)
    
    def dispatch(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            if obj.status in ['completed', 'closed']:
                if self.request.user.groups.filter(name='Контролер').exists():
                    messages.warning(
                        request,
                        f'Изделие {obj.serial_number} уже завершено. Редактирование заблокировано.'
                    )
                    return redirect('unified_products:product_detail', pk=obj.pk)
        except:
            pass
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_create'] = False
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_object(self, queryset=None):
        return get_object_or_404(Product, serial_number=self.kwargs['serial_number'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование: {self.object.serial_number}'
        context['is_create'] = False
        context['categories'] = Category.objects.filter(is_active=True)
        context['images'] = self.object.images.all().order_by('field_index')
        context['can_edit'] = self.object.can_edit(self.request.user)
        context['is_completed'] = self.object.is_completed()
        context['is_closed'] = self.object.status == 'closed'
        context['is_superuser'] = self.request.user.is_superuser
        context['scan_url'] = '/unified-products/scan-serial/'
        context['app_name'] = 'Управление изделиями'
        context['namespace'] = 'unified_products'
        context['header_color'] = 'bg-primary'
        
        sample = None
        try:
            sample = self.object.category.products.filter(is_sample=True).exclude(pk=self.object.pk).first()
        except Exception as e:
            logger.error(f"Ошибка поиска образца: {e}")
        
        context['sample'] = sample
        
        sample_images = {}
        if sample:
            for sample_img in sample.images.all():
                sample_images[sample_img.field_index] = sample_img
        
        for image in context['images']:
            image.sample_image = sample_images.get(image.field_index)
            image.has_sample_image = image.sample_image and bool(image.sample_image.image)
            if image.sample_image and not image.title:
                image.title = image.sample_image.title
        
        return context
    
    def form_valid(self, form):
        obj = form.instance
        
        # ===== ОБРАБОТКА is_sample =====
        if self.request.user.is_superuser:
            if 'is_sample' in self.request.POST:
                obj.is_sample = True
                Product.objects.filter(
                    category=obj.category,
                    is_sample=True
                ).exclude(pk=obj.pk).update(is_sample=False)
                logger.info(f"Объект {obj.serial_number} установлен как образец")
            else:
                obj.is_sample = False
        else:
            original = Product.objects.get(pk=obj.pk)
            obj.is_sample = original.is_sample
        
        # ===== БЛОКИРУЕМ ИЗМЕНЕНИЕ СЕРИЙНОГО НОМЕРА =====
        if not self.request.user.is_superuser:
            original = Product.objects.get(pk=obj.pk)
            obj.serial_number = original.serial_number
        
        # ===== ОБРАБОТКА УДАЛЕНИЯ ФОТО СЕРИЙНОГО НОМЕРА =====
        if self.request.POST.get('delete_serial_photo'):
            if obj.serial_photo:
                try:
                    if os.path.exists(obj.serial_photo.path):
                        os.remove(obj.serial_photo.path)
                        logger.info(f"Удалено фото серийного номера: {obj.serial_photo.path}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить фото серийного номера: {e}")
                obj.serial_photo = None
        
        # ===== СОХРАНЯЕМ НОВОЕ ФОТО СЕРИЙНОГО НОМЕРА =====
        if 'serial_photo' in self.request.FILES:
            obj.serial_photo = self.request.FILES['serial_photo']
            logger.info(f"Загружено новое фото серийного номера для {obj.serial_number}")
        
        # ===== СОХРАНЯЕМ ФОТО ИЗ СКАНИРОВАНИЯ =====
        if 'scanned_photo_base64' in self.request.POST:
            photo_data = self.request.POST.get('scanned_photo_base64', '')
            if photo_data and ';base64,' in photo_data:
                try:
                    import base64
                    from django.core.files.base import ContentFile
                    format_part, imgstr = photo_data.split(';base64,')
                    ext = format_part.split('/')[-1] if '/' in format_part else 'jpg'
                    image_data = base64.b64decode(imgstr)
                    if image_data and len(image_data) > 1000:
                        # Удаляем старое фото если есть
                        if obj.serial_photo:
                            try:
                                if os.path.exists(obj.serial_photo.path):
                                    os.remove(obj.serial_photo.path)
                            except:
                                pass
                        obj.serial_photo.save(
                            f'serial_photo_{obj.serial_number}.{ext}',
                            ContentFile(image_data),
                            save=False
                        )
                        logger.info(f"Фото серийного номера сохранено из сканирования")
                except Exception as e:
                    logger.error(f"Ошибка сохранения фото из сканирования: {e}")
        
        response = super().form_valid(form)
        
        # ===== ПРОВЕРЯЕМ СТАТУС =====
        if obj.is_completed() and obj.status != 'closed':
            obj.status = 'completed'
            obj.completed_at = timezone.now()
            obj.save(update_fields=['status', 'completed_at'])
            messages.success(
                self.request,
                f'✅ Все фото загружены! Изделие {obj.serial_number} завершено.'
            )
            return redirect('unified_products:product_detail', pk=obj.pk)
        else:
            if obj.status == 'draft':
                obj.status = 'in_progress'
                obj.save(update_fields=['status'])
            messages.success(
                self.request,
                f'📝 Изделие {obj.serial_number} успешно обновлено.'
            )
            return redirect('unified_products:product_edit', serial_number=obj.serial_number)


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Удаление изделия"""
    template_name = 'unified_products/confirm_delete.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return render(request, self.template_name, {
            'product': product,
            'app_name': 'Управление изделиями',
            'namespace': 'unified_products',
        })
    
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serial = product.serial_number
        product.delete()
        messages.success(request, f'Изделие {serial} успешно удалено.')
        return redirect('unified_products:product_list')


class ProductCloseView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Закрытие изделия"""
    template_name = 'unified_products/confirm_close.html'
    
    def test_func(self):
        obj = get_object_or_404(Product, pk=self.kwargs['pk'])
        return obj.can_edit(self.request.user)
    
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return render(request, self.template_name, {
            'product': product,
            'app_name': 'Управление изделиями',
            'namespace': 'unified_products',
        })
    
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        
        if product.is_completed():
            product.status = 'closed'
            product.completed_at = timezone.now()
            product.closed_by = request.user
            product.save(update_fields=['status', 'completed_at', 'closed_by'])
            messages.success(request, f'Изделие {product.serial_number} успешно закрыто!')
        else:
            messages.error(request, 'Невозможно закрыть: не все фото загружены')
        
        return redirect('unified_products:product_detail', pk=product.pk)


# ==================== СКАНИРОВАНИЕ ====================

class ScanSerialView(LoginRequiredMixin, View):
    """Сканирование серийного номера с камеры"""
    
    def post(self, request):
        print("=" * 50)
        print("ScanSerialView вызван")
        print("POST данные:", request.POST)
        print("FILES:", request.FILES)
        print("=" * 50)
        
        try:
            if 'scan_image' not in request.FILES:
                print("Ошибка: scan_image не найден в FILES")
                return JsonResponse({
                    'success': False,
                    'error': 'Файл не выбран'
                }, status=400)
            
            file = request.FILES['scan_image']
            print(f"Файл получен: {file.name}, размер: {file.size}")
            
            if file.size > 10 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': 'Файл слишком большой (максимум 10MB)'
                }, status=400)
            
            # Сохраняем во временный файл
            import tempfile
            import os
            temp_path = tempfile.mktemp(suffix='.jpg')
            print(f"Временный файл: {temp_path}")
            
            with open(temp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            print("Файл сохранен во временное хранилище")
            
            # Распознаем серийный номер
            detected_serial = None
            try:
                from PIL import Image, ImageEnhance, ImageFilter
                import pytesseract
                import re
                import sys
                from collections import Counter
                
                # Настраиваем Tesseract
                if sys.platform == 'win32':
                    tesseract_paths = [
                        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                    ]
                    for path in tesseract_paths:
                        if os.path.exists(path):
                            pytesseract.pytesseract.tesseract_cmd = path
                            print(f"Tesseract найден: {path}")
                            break
                
                image = Image.open(temp_path)
                print(f"Изображение открыто: {image.size}")
                
                image = image.convert('L')
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)
                image = image.point(lambda p: 255 if p > 128 else 0)
                width, height = image.size
                image = image.resize((width * 3, height * 3), Image.Resampling.LANCZOS)
                image = image.filter(ImageFilter.SHARPEN)
                
                configs = [
                    r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789',
                    r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789',
                    r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789',
                    r'--oem 3 --psm 13 -c tessedit_char_whitelist=0123456789',
                ]
                
                all_texts = []
                for config in configs:
                    try:
                        text = pytesseract.image_to_string(image, lang='eng', config=config)
                        text_clean = re.sub(r'[^0-9]', '', text)
                        all_texts.append(text_clean)
                        print(f"Распознано с config {config}: {text_clean}")
                    except Exception as e:
                        print(f"Ошибка с config {config}: {e}")
                
                all_found = []
                patterns = [r'\d{7}', r'\d{6,8}']
                for text in all_texts:
                    for pattern in patterns:
                        match = re.search(pattern, text)
                        if match:
                            all_found.append(match.group(0))
                            print(f"Найден серийный номер (паттерн {pattern}): {match.group(0)}")
                
                if all_found:
                    counter = Counter(all_found)
                    detected_serial = counter.most_common(1)[0][0]
                    print(f"Выбран серийный номер (самый частый): {detected_serial}")
                
                if not detected_serial:
                    print("Серийный номер не распознан с ограниченным набором")
                    
                    text_all = pytesseract.image_to_string(image, lang='eng')
                    text_all_clean = re.sub(r'[^0-9]', '', text_all)
                    print(f"Распознано без ограничений: {text_all_clean}")
                    for pattern in patterns:
                        match = re.search(pattern, text_all_clean)
                        if match:
                            detected_serial = match.group(0)
                            print(f"Найден серийный номер (без ограничений, паттерн {pattern}): {detected_serial}")
                            break
                        
            except Exception as e:
                print(f"Ошибка распознавания: {e}")
                import traceback
                traceback.print_exc()
            
            # Кодируем фото в base64
            import base64
            with open(temp_path, 'rb') as f:
                photo_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # Удаляем временный файл
            try:
                os.remove(temp_path)
                print("Временный файл удален")
            except Exception as e:
                print(f"Ошибка удаления временного файла: {e}")
            
            if detected_serial:
                # Определяем категорию по префиксу
                category = None
                categories = Category.objects.filter(is_active=True)
                for cat in categories:
                    if detected_serial.startswith(cat.prefix):
                        category = cat
                        break
                
                print(f"Определена категория: {category.name if category else 'Не найдена'}")
                
                return JsonResponse({
                    'success': True,
                    'serial_number': detected_serial,
                    'photo_base64': photo_base64,
                    'category_id': category.id if category else None,
                    'category_name': category.name if category else None,
                    'message': f'Распознан номер: {detected_serial}'
                })
            else:
                print("Серийный номер не распознан")
                return JsonResponse({
                    'success': False,
                    'photo_base64': photo_base64,
                    'error': 'Не удалось распознать серийный номер на изображении'
                }, status=400)
                
        except Exception as e:
            print(f"Общая ошибка: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Ошибка: {str(e)}'
            }, status=500)


# ==================== AJAX ====================


@require_http_methods(["POST"])
def ajax_save_image(request, pk, field_index):
    """
    AJAX-сохранение изображения
    """
    try:
        logger.info(f"ajax_save_image: pk={pk}, field_index={field_index}")
        
        product = get_object_or_404(Product, pk=pk)
        
        if not product.can_edit(request.user):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на редактирование'
            }, status=403)
        
        # Поддерживаем оба ключа: 'image' и 'file'
        uploaded_file = request.FILES.get('image') or request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({
                'success': False,
                'error': 'Файл не передан'
            }, status=400)
        
        # Получаем или создаем изображение
        image_instance, created = ProductImage.objects.get_or_create(
            product=product,
            field_index=field_index,
            defaults={'title': f'Поле {field_index}'}
        )
        
        # Сохраняем файл (изображение или видео)
        image_instance.image = uploaded_file
        image_instance.save()
        
        logger.info(f"Файл сохранен: {image_instance.image.url if image_instance.image else 'None'}, тип: {uploaded_file.content_type}")
        
        # Проверяем прогресс
        filled_count = product.get_filled_count()
        required_count = product.get_total_required()
        is_completed = filled_count >= required_count
        
        logger.info(f"Загружено: {filled_count}/{required_count}, завершен: {is_completed}")
        
        redirect_url = None
        if is_completed and product.status != 'closed':
            product.status = 'completed'
            product.completed_at = timezone.now()
            product.save(update_fields=['status', 'completed_at'])
            redirect_url = reverse('unified_products:product_list')
            logger.info(f"Объект завершен: {product.serial_number}")
        
        response_data = {
            'success': True,
            'message': 'Изображение сохранено',
            'image_url': image_instance.image.url if image_instance.image else None,
            'is_completed': is_completed,
            'status': product.status,
            'status_display': product.get_status_display(),
            'redirect_url': redirect_url,
            'progress': product.get_progress_percent(),
            'filled': filled_count,
            'total': required_count,
        }
        
        logger.info(f"Ответ: {response_data}")
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Ошибка сохранения изображения: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def ajax_save_title(request, pk, field_index):
    """AJAX-сохранение заголовка"""
    try:
        product = get_object_or_404(Product, pk=pk)
        
        if not product.can_edit(request.user):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на редактирование'
            }, status=403)
        
        data = json.loads(request.body)
        value = data.get('value', '')
        
        image_instance = ProductImage.objects.get(product=product, field_index=field_index)
        image_instance.title = value
        image_instance.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Заголовок сохранен',
            'value': value
        })
        
    except ProductImage.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Поле изображения не найдено'
        }, status=404)
    except Exception as e:
        logger.error(f"Ошибка сохранения заголовка: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def ajax_delete_image(request, pk, field_index):
    """AJAX-удаление изображения"""
    try:
        product = get_object_or_404(Product, pk=pk)
        
        if not product.can_edit(request.user):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на редактирование'
            }, status=403)
        
        image_instance = ProductImage.objects.get(product=product, field_index=field_index)
        if image_instance.image:
            image_instance.image.delete(save=False)
        image_instance.image = None
        image_instance.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Изображение удалено',
            'progress': product.get_progress_percent(),
            'filled': product.get_filled_count(),
            'total': product.get_total_required(),
        })
        
    except ProductImage.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Поле изображения не найдено'
        }, status=404)
    except Exception as e:
        logger.error(f"Ошибка удаления изображения: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def ajax_check_completed(request, pk):
    """
    Проверка завершенности
    """
    try:
        product = get_object_or_404(Product, pk=pk)
        
        filled_count = product.get_filled_count()
        required_count = product.get_total_required()
        is_completed = filled_count >= required_count
        
        redirect_url = None
        if is_completed and product.status != 'closed':
            product.status = 'completed'
            product.completed_at = timezone.now()
            product.save(update_fields=['status', 'completed_at'])
            redirect_url = reverse('unified_products:product_list')
        
        return JsonResponse({
            'success': True,
            'is_completed': is_completed,
            'status': product.status,
            'status_display': product.get_status_display(),
            'redirect_url': redirect_url,
            'progress': product.get_progress_percent(),
            'filled': filled_count,
            'total': required_count,
        })
        
    except Exception as e:
        logger.error(f"Ошибка проверки: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def ajax_search_owners(request):
    """
    AJAX-поиск владельцев для автодополнения
    """
    try:
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({
                'success': True,
                'owners': []
            })
        
        # Ищем пользователей
        owners = User.objects.filter(
            models.Q(username__icontains=query) |
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query)
        ).distinct()[:10]
        
        result = []
        for owner in owners:
            full_name = owner.get_full_name() or owner.username
            result.append({
                'id': owner.id,
                'username': owner.username,
                'full_name': full_name,
            })
        
        return JsonResponse({
            'success': True,
            'owners': result
        })
        
    except Exception as e:
        logger.error(f"Ошибка поиска владельцев: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)








