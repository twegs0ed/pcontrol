from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.http import HttpResponse
from django.urls import path
from .models import TTR10AB
import io
import os
from django.conf import settings
from django.utils import timezone

# Для PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Для Word
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

APP_NAME = 'TTR-10AB'


def get_user_full_name(user):
    """Возвращает полное имя пользователя"""
    if user:
        if user.first_name and user.last_name:
            return f"{user.last_name} {user.first_name}"
        elif user.first_name:
            return user.first_name
        elif user.last_name:
            return user.last_name
        else:
            return user.username
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

FONT_NAME = register_fonts()


@admin.register(TTR10AB)
class TTR10ABAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'owner', 'title1', 'image_thumbnail', 'word_export_button', 'pdf_export_button', 'created_at']
    list_filter = ['created_at', 'updated_at', 'owner']
    search_fields = ['serial_number', 'title1', 'description']
    readonly_fields = ['created_at', 'updated_at', 
                       'image1_preview', 'image2_preview', 'image3_preview', 
                       'image4_preview', 'image5_preview', 'image6_preview',
                       'image7_preview', 'image8_preview', 'serial_photo_preview']
    
    class Media:
        js = ('admin/js/image_modal.js',)
    
    def image_thumbnail(self, obj):
        if obj.image1:
            try:
                return format_html(
                    '''
                    <div style="position: relative; display: inline-block;">
                        <img src="{}" style="max-width: 60px; max-height: 60px; border-radius: 4px; object-fit: cover; cursor: pointer; border: 2px solid #ddd; transition: all 0.3s;" 
                             onclick="openImageModal('{}', '{}')"
                             onmouseover="this.style.borderColor='#0d6efd'; this.style.transform='scale(1.05)';"
                             onmouseout="this.style.borderColor='#ddd'; this.style.transform='scale(1)';"
                             title="Нажмите для увеличения" />
                        <span style="position: absolute; bottom: 0; right: 0; background: rgba(0,0,0,0.7); color: white; font-size: 10px; padding: 1px 6px; border-radius: 10px; cursor: pointer;"
                              onclick="event.stopPropagation(); openImageModal('{}', '{}')">
                            🔍
                        </span>
                    </div>
                    ''',
                    obj.image1.url,
                    obj.image1.url,
                    obj.serial_number,
                    obj.image1.url,
                    obj.serial_number
                )
            except:
                return "Ошибка загрузки"
        return "-"
    image_thumbnail.short_description = 'Фото'
    
    def image_preview(self, obj, image_field, label, title_field=None):
        try:
            image = getattr(obj, image_field)
            title = getattr(obj, title_field) if title_field else label
            if image:
                return format_html(
                    '''
                    <div style="margin: 5px 0; padding: 8px; border: 1px solid #e0e0e0; border-radius: 6px; background: #f9f9f9;">
                        <strong style="display: block; margin-bottom: 5px; font-size: 13px;">{}</strong>
                        <div style="display: inline-block; position: relative;">
                            <img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 6px; cursor: pointer; border: 2px solid #ddd; transition: all 0.3s;"
                                 onclick="openImageModal('{}', '{} - {}')"
                                 onmouseover="this.style.borderColor='#0d6efd'; this.style.boxShadow='0 4px 15px rgba(0,0,0,0.2)';"
                                 onmouseout="this.style.borderColor='#ddd'; this.style.boxShadow='none';"
                                 title="Нажмите для увеличения" />
                            <span style="position: absolute; bottom: 5px; right: 5px; background: rgba(0,0,0,0.7); color: white; font-size: 11px; padding: 2px 8px; border-radius: 12px; cursor: pointer;"
                                  onclick="event.stopPropagation(); openImageModal('{}', '{} - {}')">
                                🔍
                            </span>
                        </div>
                        <br>
                        <small style="color: #888; font-size: 10px;">Нажмите для увеличения</small>
                    </div>
                    ''',
                    title or label,
                    image.url,
                    image.url,
                    obj.serial_number,
                    title or label,
                    image.url,
                    obj.serial_number,
                    title or label
                )
            return ""
        except Exception as e:
            return ""
    
    # Методы для превью
    def image1_preview(self, obj):
        return self.image_preview(obj, 'image1', 'Механизм вид сверху', 'title1')
    image1_preview.short_description = 'Механизм вид сверху'
    
    def image2_preview(self, obj):
        return self.image_preview(obj, 'image2', 'Механизм вид справа', 'title2')
    image2_preview.short_description = 'Механизм вид справа'
    
    def image3_preview(self, obj):
        return self.image_preview(obj, 'image3', 'Механизм вид слева', 'title3')
    image3_preview.short_description = 'Механизм вид слева'
    
    def image4_preview(self, obj):
        return self.image_preview(obj, 'image4', 'Турникет вид сверху', 'title4')
    image4_preview.short_description = 'Турникет вид сверху'
    
    def image5_preview(self, obj):
        return self.image_preview(obj, 'image5', 'Турникет вид слева', 'title5')
    image5_preview.short_description = 'Турникет вид слева'
    
    def image6_preview(self, obj):
        return self.image_preview(obj, 'image6', 'Турникет вид справа', 'title6')
    image6_preview.short_description = 'Турникет вид справа'
    
    def image7_preview(self, obj):
        return self.image_preview(obj, 'image7', 'Турникет вид сзади', 'title7')
    image7_preview.short_description = 'Турникет вид сзади'
    
    def image8_preview(self, obj):
        return self.image_preview(obj, 'image8', 'Комплектность', 'title8')
    image8_preview.short_description = 'Комплектность'
    
    def serial_photo_preview(self, obj):
        try:
            if obj.serial_photo:
                return format_html(
                    '''
                    <div style="margin: 5px 0; padding: 8px; border: 2px solid #17a2b8; border-radius: 6px; background: #f0f8ff;">
                        <strong style="display: block; margin-bottom: 5px; color: #17a2b8; font-size: 13px;">Фото серийного номера</strong>
                        <div style="display: inline-block; position: relative;">
                            <img src="{}" style="max-width: 250px; max-height: 250px; border-radius: 6px; cursor: pointer; border: 3px solid #17a2b8; transition: all 0.3s;"
                                 onclick="openImageModal('{}', 'Серийный номер: {}')"
                                 onmouseover="this.style.borderColor='#0d6efd'; this.style.boxShadow='0 4px 15px rgba(0,0,0,0.3)';"
                                 onmouseout="this.style.borderColor='#17a2b8'; this.style.boxShadow='none';"
                                 title="Нажмите для увеличения" />
                            <span style="position: absolute; bottom: 5px; right: 5px; background: rgba(23, 162, 184, 0.9); color: white; font-size: 11px; padding: 2px 8px; border-radius: 12px; cursor: pointer;"
                                  onclick="event.stopPropagation(); openImageModal('{}', 'Серийный номер: {}')">
                                🔍
                            </span>
                        </div>
                        <br>
                        <small style="color: #888; font-size: 10px;">Нажмите для увеличения</small>
                    </div>
                    ''',
                    obj.serial_photo.url,
                    obj.serial_photo.url,
                    obj.serial_number,
                    obj.serial_photo.url,
                    obj.serial_number
                )
            return ""
        except Exception as e:
            return ""
    serial_photo_preview.short_description = 'Фото серийного номера'
    
    # Экспорт в Word (массовый)
    def export_word(self, request, queryset):
        if not queryset:
            self.message_user(request, 'Не выбрано ни одного объекта')
            return
        
        try:
            doc = Document()
            
            title = doc.add_heading(f'Отчет по приложению {APP_NAME}', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_paragraph(f'Дата создания отчета: {timezone.now().strftime("%d.%m.%Y %H:%M")}')
            doc.add_paragraph(f'Количество записей: {queryset.count()}')
            doc.add_paragraph()
            
            table = doc.add_table(rows=1, cols=6)
            table.style = 'Table Grid'
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            headers = ['№', 'Серийный номер', 'Контролер', 'Заголовок', 'Описание', 'Дата создания']
            for i, header in enumerate(headers):
                cell = table.cell(0, i)
                cell.text = header
                cell.paragraphs[0].runs[0].bold = True
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            for idx, obj in enumerate(queryset, 1):
                row_cells = table.add_row().cells
                row_cells[0].text = str(idx)
                row_cells[1].text = obj.serial_number
                row_cells[2].text = get_user_full_name(obj.owner)
                row_cells[3].text = obj.title1 or '-'
                row_cells[4].text = obj.description[:100] + '...' if obj.description and len(obj.description) > 100 else obj.description or '-'
                row_cells[5].text = obj.created_at.strftime("%d.%m.%Y %H:%M")
            
            doc.add_page_break()
            doc.add_heading(f'Изображения {APP_NAME}', level=1)
            
            for obj in queryset:
                doc.add_heading(f'{APP_NAME}: {obj.serial_number}', level=2)
                
                image_fields = [
                    ('image1', 'Механизм вид сверху', 'title1'),
                    ('image2', 'Механизм вид справа', 'title2'),
                    ('image3', 'Механизм вид слева', 'title3'),
                    ('image4', 'Турникет вид сверху', 'title4'),
                    ('image5', 'Турникет вид слева', 'title5'),
                    ('image6', 'Турникет вид справа', 'title6'),
                    ('image7', 'Турникет вид сзади', 'title7'),
                    ('image8', 'Комплектность', 'title8'),
                ]
                
                for field, label, title_field in image_fields:
                    try:
                        image = getattr(obj, field)
                        title_text = getattr(obj, title_field) or label
                        if image and image.path and os.path.exists(image.path):
                            doc.add_paragraph(f'{title_text}:')
                            doc.add_picture(image.path, width=Inches(3))
                            doc.add_paragraph()
                    except:
                        doc.add_paragraph(f'{title_text}: Ошибка загрузки изображения')
                
                doc.add_paragraph('-' * 50)
            
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename={APP_NAME}_report_{timezone.now().strftime("%Y%m%d_%H%M")}.docx'
            return response
            
        except Exception as e:
            self.message_user(request, f'Ошибка при создании Word отчета: {str(e)}', level='ERROR')
            return
    
    export_word.short_description = 'Экспортировать в Word'
    
    # Экспорт в PDF (массовый)
    def export_pdf(self, request, queryset):
        if not queryset:
            self.message_user(request, 'Не выбрано ни одного объекта')
            return
        
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
            
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=FONT_NAME,
                fontSize=24,
                textColor=colors.HexColor('#0d6efd'),
                alignment=TA_CENTER,
                spaceAfter=30
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=FONT_NAME,
                fontSize=14,
                textColor=colors.HexColor('#333333'),
                alignment=TA_LEFT,
                spaceAfter=12
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=FONT_NAME,
                fontSize=10,
                alignment=TA_LEFT,
                leading=14
            )
            
            table_style = ParagraphStyle(
                'TableStyle',
                parent=styles['Normal'],
                fontName=FONT_NAME,
                fontSize=9,
                alignment=TA_CENTER,
                leading=12
            )
            
            table_header_style = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontName=FONT_NAME,
                fontSize=10,
                alignment=TA_CENTER,
                leading=14,
                textColor=colors.whitesmoke
            )
            
            elements = []
            
            elements.append(Paragraph(f'Отчет по приложению {APP_NAME}', title_style))
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph(f'<b>Дата создания отчета:</b> {timezone.now().strftime("%d.%m.%Y %H:%M")}', normal_style))
            elements.append(Paragraph(f'<b>Количество записей:</b> {queryset.count()}', normal_style))
            elements.append(Spacer(1, 20))
            
            # Таблица
            data = []
            headers = ['№', 'Серийный номер', 'Контролер', 'Заголовок', 'Дата создания']
            header_row = []
            for h in headers:
                header_row.append(Paragraph(h, table_header_style))
            data.append(header_row)
            
            for idx, obj in enumerate(queryset, 1):
                row = [
                    Paragraph(str(idx), table_style),
                    Paragraph(obj.serial_number, table_style),
                    Paragraph(get_user_full_name(obj.owner), table_style),
                    Paragraph(obj.title1 or '-', table_style),
                    Paragraph(obj.created_at.strftime("%d.%m.%Y %H:%M"), table_style),
                ]
                data.append(row)
            
            col_widths = [40, 120, 100, 120, 120]
            table = Table(data, colWidths=col_widths, repeatRows=1)
            
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 30))
            
            # Изображения
            elements.append(Paragraph(f'Изображения {APP_NAME}', heading_style))
            elements.append(Spacer(1, 10))
            
            for obj in queryset:
                elements.append(Paragraph(f'<b>{APP_NAME}: {obj.serial_number}</b>', normal_style))
                elements.append(Spacer(1, 5))
                
                image_fields = [
                    ('image1', 'Механизм вид сверху', 'title1'),
                    ('image2', 'Механизм вид справа', 'title2'),
                    ('image3', 'Механизм вид слева', 'title3'),
                    ('image4', 'Турникет вид сверху', 'title4'),
                    ('image5', 'Турникет вид слева', 'title5'),
                    ('image6', 'Турникет вид справа', 'title6'),
                    ('image7', 'Турникет вид сзади', 'title7'),
                    ('image8', 'Комплектность', 'title8'),
                ]
                
                for field, label, title_field in image_fields:
                    try:
                        image = getattr(obj, field)
                        title_text = getattr(obj, title_field) or label
                        if image and image.path and os.path.exists(image.path):
                            elements.append(Paragraph(f'<i>{title_text}:</i>', normal_style))
                            img = Image(image.path, width=3*inch, height=3*inch, kind='proportional')
                            elements.append(img)
                            elements.append(Spacer(1, 5))
                    except:
                        elements.append(Paragraph(f'{title_text}: Ошибка загрузки изображения', normal_style))
                
                elements.append(Spacer(1, 10))
                elements.append(Paragraph('-' * 50, normal_style))
                elements.append(Spacer(1, 10))
            
            doc.build(elements)
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={APP_NAME}_report_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf'
            return response
            
        except Exception as e:
            self.message_user(request, f'Ошибка при создании PDF отчета: {str(e)}', level='ERROR')
            return
    
    export_pdf.short_description = 'Экспортировать в PDF'
    
    # Экспорт одного объекта в Word
    def export_single_word(self, request, obj_id):
        try:
            obj = TTR10AB.objects.get(pk=obj_id)
            
            doc = Document()
            
            title = doc.add_heading(f'{APP_NAME} - {obj.serial_number}', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_paragraph(f'Серийный номер: {obj.serial_number}')
            doc.add_paragraph(f'Контролер: {get_user_full_name(obj.owner)}')
            doc.add_paragraph(f'Описание: {obj.description or "-"}')
            doc.add_paragraph(f'Дата создания: {obj.created_at.strftime("%d.%m.%Y %H:%M")}')
            doc.add_paragraph(f'Дата обновления: {obj.updated_at.strftime("%d.%m.%Y %H:%M")}')
            doc.add_paragraph()
            
            doc.add_heading(f'Изображения {APP_NAME}', level=1)
            image_fields = [
                ('image1', 'Механизм вид сверху', 'title1'),
                ('image2', 'Механизм вид справа', 'title2'),
                ('image3', 'Механизм вид слева', 'title3'),
                ('image4', 'Турникет вид сверху', 'title4'),
                ('image5', 'Турникет вид слева', 'title5'),
                ('image6', 'Турникет вид справа', 'title6'),
                ('image7', 'Турникет вид сзади', 'title7'),
                ('image8', 'Комплектность', 'title8'),
            ]
            
            for field, label, title_field in image_fields:
                try:
                    image = getattr(obj, field)
                    title_text = getattr(obj, title_field) or label
                    if image and image.path and os.path.exists(image.path):
                        doc.add_heading(title_text, level=2)
                        doc.add_picture(image.path, width=Inches(4))
                        doc.add_paragraph()
                except:
                    doc.add_paragraph(f'{title_text}: Ошибка загрузки изображения')
            
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename={APP_NAME}_{obj.serial_number}.docx'
            return response
            
        except TTR10AB.DoesNotExist:
            return HttpResponse('Объект не найден', status=404)
        except Exception as e:
            return HttpResponse(f'Ошибка: {str(e)}', status=500)
    
    # Экспорт одного объекта в PDF
    def export_single_pdf(self, request, obj_id):
        try:
            obj = TTR10AB.objects.get(pk=obj_id)
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=FONT_NAME,
                fontSize=24,
                textColor=colors.HexColor('#0d6efd'),
                alignment=TA_CENTER,
                spaceAfter=30
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=FONT_NAME,
                fontSize=12,
                alignment=TA_LEFT,
                leading=16
            )
            
            elements = []
            
            elements.append(Paragraph(f'{APP_NAME} - {obj.serial_number}', title_style))
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph(f'<b>Серийный номер:</b> {obj.serial_number}', normal_style))
            elements.append(Paragraph(f'<b>Контролер:</b> {get_user_full_name(obj.owner)}', normal_style))
            elements.append(Paragraph(f'<b>Описание:</b> {obj.description or "-"}', normal_style))
            elements.append(Paragraph(f'<b>Дата создания:</b> {obj.created_at.strftime("%d.%m.%Y %H:%M")}', normal_style))
            elements.append(Paragraph(f'<b>Дата обновления:</b> {obj.updated_at.strftime("%d.%m.%Y %H:%M")}', normal_style))
            elements.append(Spacer(1, 20))
            
            # Добавляем изображения
            image_fields = [
                ('image1', 'Механизм вид сверху', 'title1'),
                ('image2', 'Механизм вид справа', 'title2'),
                ('image3', 'Механизм вид слева', 'title3'),
                ('image4', 'Турникет вид сверху', 'title4'),
                ('image5', 'Турникет вид слева', 'title5'),
                ('image6', 'Турникет вид справа', 'title6'),
                ('image7', 'Турникет вид сзади', 'title7'),
                ('image8', 'Комплектность', 'title8'),
            ]
            
            for field, label, title_field in image_fields:
                try:
                    image = getattr(obj, field)
                    title_text = getattr(obj, title_field) or label
                    if image and image.path and os.path.exists(image.path):
                        elements.append(Paragraph(f'<b>{title_text}:</b>', normal_style))
                        img = Image(image.path, width=4*inch, height=4*inch, kind='proportional')
                        elements.append(img)
                        elements.append(Spacer(1, 10))
                except:
                    pass
            
            doc.build(elements)
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={APP_NAME}_{obj.serial_number}.pdf'
            return response
            
        except TTR10AB.DoesNotExist:
            return HttpResponse('Объект не найден', status=404)
        except Exception as e:
            return HttpResponse(f'Ошибка: {str(e)}', status=500)
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('export-word/<int:obj_id>/', self.admin_site.admin_view(self.export_single_word), name='export_word'),
            path('export-pdf/<int:obj_id>/', self.admin_site.admin_view(self.export_single_pdf), name='export_pdf'),
        ]
        return custom_urls + urls
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions['export_word'] = (self.export_word, 'export_word', 'Экспорт в Word')
        actions['export_pdf'] = (self.export_pdf, 'export_pdf', 'Экспорт в PDF')
        return actions
    
    def word_export_button(self, obj):
        try:
            return format_html(
                '<a class="button" href="{}" style="background: #2b5a8c; color: white; padding: 3px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">📄 Word</a>',
                f'export-word/{obj.pk}/'
            )
        except:
            return '-'
    word_export_button.short_description = 'Word'
    
    def pdf_export_button(self, obj):
        try:
            return format_html(
                '<a class="button" href="{}" style="background: #dc3545; color: white; padding: 3px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">📄 PDF</a>',
                f'export-pdf/{obj.pk}/'
            )
        except:
            return '-'
    pdf_export_button.short_description = 'PDF'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Аудитор').exists():
            return qs
        if request.user.groups.filter(name='Контролер').exists():
            return qs.filter(owner=request.user)
        if request.user.is_superuser:
            return qs
        return qs.none()
    
    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Аудитор').exists():
            return False
        if request.user.groups.filter(name='Контролер').exists():
            if obj and obj.owner != request.user:
                return False
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False
    
    def has_add_permission(self, request):
        if request.user.groups.filter(name='Контролер').exists():
            return True
        if request.user.is_superuser:
            return True
        return False
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('serial_number', 'owner', 'serial_photo', 'serial_photo_preview', 'description')
        }),
        ('Изображения', {
            'fields': (
                ('title1', 'image1', 'image1_preview'),
                ('title2', 'image2', 'image2_preview'),
                ('title3', 'image3', 'image3_preview'),
                ('title4', 'image4', 'image4_preview'),
                ('title5', 'image5', 'image5_preview'),
                ('title6', 'image6', 'image6_preview'),
                ('title7', 'image7', 'image7_preview'),
                ('title8', 'image8', 'image8_preview'),
            )
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )