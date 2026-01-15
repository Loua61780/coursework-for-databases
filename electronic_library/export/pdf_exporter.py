from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
from typing import List, Dict, Any
from config import Config

class PDFExporter:
    """Экспорт данных в PDF формат"""
    
    @staticmethod
    def export_sales_report_pdf(data: Dict[str, Any], file_path: str = None) -> str:
        """Экспорт отчета по продажам в PDF"""
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(Config.EXPORT_PATH, f'sales_report_{timestamp}.pdf')
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            alignment=1
        )
        
        elements.append(Paragraph("Отчет по продажам электронной библиотеки", title_style))
        elements.append(Spacer(1, 12))
        
        # Период отчета
        period_text = f"Период: {data['period']['start']} - {data['period']['end']}"
        elements.append(Paragraph(period_text, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Сводная информация
        summary = data['summary']
        summary_data = [
            ['Показатель', 'Значение'],
            ['Всего заказов', summary['total_orders']],
            ['Общая выручка', f"{summary['total_revenue']:.2f} руб."],
            ['Средний чек', f"{summary['average_order_value']:.2f} руб."]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Ежедневные данные
        elements.append(Paragraph("Ежедневная статистика:", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        daily_data = data['daily_data']
        if daily_data:
            table_data = [['Дата', 'Заказов', 'Выручка', 'Товаров продано']]
            
            for day in daily_data:
                table_data.append([
                    day['date'],
                    day['orders_count'],
                    f"{day['total_revenue']:.2f} руб.",
                    day['items_sold']
                ])
            
            daily_table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1.5*inch])
            daily_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            
            elements.append(daily_table)
        
        # Подпись и дата
        elements.append(Spacer(1, 30))
        date_text = f"Отчет сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        elements.append(Paragraph(date_text, styles['Italic']))
        
        # Генерация PDF
        doc.build(elements)
        return file_path
    
    @staticmethod
    def export_inventory_report_pdf(publications_data: List[Dict[str, Any]], file_path: str = None) -> str:
        """Экспорт отчета по инвентарю в PDF"""
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(Config.EXPORT_PATH, f'inventory_report_{timestamp}.pdf')
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            alignment=1
        )
        
        elements.append(Paragraph("Отчет по инвентарю электронной библиотеки", title_style))
        elements.append(Spacer(1, 12))
        
        # Сводная информация
        total_publications = len(publications_data)
        total_value = sum(p['price'] * p['stock_quantity'] for p in publications_data)
        low_stock = sum(1 for p in publications_data if p['stock_quantity'] < 5)
        
        summary_data = [
            ['Показатель', 'Значение'],
            ['Всего изданий', total_publications],
            ['Общая стоимость запасов', f"{total_value:.2f} руб."],
            ['Издания с низким запасом (<5)', low_stock]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Таблица изданий
        elements.append(Paragraph("Список изданий:", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        if publications_data:
            table_data = [['Название', 'ISBN', 'Цена', 'На складе', 'Стоимость запасов']]
            
            for pub in publications_data:
                stock_value = pub['price'] * pub['stock_quantity']
                table_data.append([
                    pub['title'][:30] + '...' if len(pub['title']) > 30 else pub['title'],
                    pub['isbn'] or '-',
                    f"{pub['price']:.2f} руб.",
                    pub['stock_quantity'],
                    f"{stock_value:.2f} руб."
                ])
            
            inventory_table = Table(table_data, colWidths=[2*inch, 1.2*inch, 1*inch, 0.8*inch, 1.2*inch])
            inventory_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke])
            ]))
            
            elements.append(inventory_table)
        
        # Подпись и дата
        elements.append(Spacer(1, 30))
        date_text = f"Отчет сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        elements.append(Paragraph(date_text, styles['Italic']))
        
        # Генерация PDF
        doc.build(elements)
        return file_path