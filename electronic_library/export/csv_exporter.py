import csv
import os
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from models.database_models import User, Publication, Order, OrderItem, Review
import pandas as pd
from config import Config

class CSVExporter:
    """Экспорт данных в CSV формат"""
    
    @staticmethod
    def export_to_csv(session: Session, model_class, file_path: str = None) -> str:
        """Универсальный метод экспорта в CSV"""
        objects = session.query(model_class).all()
        
        if not objects:
            raise ValueError("Нет данных для экспорта")
        
        # Получаем все атрибуты модели
        attributes = [column.name for column in model_class.__table__.columns]
        
        if not file_path:
            model_name = model_class.__name__.lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(Config.EXPORT_PATH, f'{model_name}s_{timestamp}.csv')
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Заголовки
            writer.writerow(attributes)
            
            # Данные
            for obj in objects:
                row = []
                for attr in attributes:
                    value = getattr(obj, attr)
                    if hasattr(value, 'isoformat'):  # Для datetime
                        value = value.isoformat()
                    row.append(value)
                writer.writerow(row)
        
        return file_path
    
    @staticmethod
    def export_orders_detailed(session: Session, start_date: datetime = None, end_date: datetime = None, file_path: str = None) -> str:
        """Экспорт детализированных заказов в CSV"""
        from sqlalchemy.orm import joinedload
        
        query = session.query(Order).options(joinedload(Order.items), joinedload(Order.user))
        
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)
        
        orders = query.all()
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(Config.EXPORT_PATH, f'orders_detailed_{timestamp}.csv')
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Заголовки
            headers = [
                'order_id', 'order_number', 'order_date', 'customer_email',
                'customer_name', 'total_amount', 'status', 'payment_method',
                'item_title', 'item_quantity', 'item_unit_price', 'item_total'
            ]
            writer.writerow(headers)
            
            # Данные
            for order in orders:
                for item in order.items:
                    writer.writerow([
                        order.id,
                        order.order_number,
                        order.order_date.isoformat(),
                        order.user.email,
                        f"{order.user.first_name} {order.user.last_name}",
                        order.total_amount,
                        order.status.value,
                        order.payment_method or '',
                        item.publication.title,
                        item.quantity,
                        item.unit_price,
                        item.quantity * item.unit_price
                    ])
        
        return file_path
    
    @staticmethod
    def export_publications_with_stats(session: Session, file_path: str = None) -> str:
        """Экспорт публикаций со статистикой в CSV"""
        from sqlalchemy import func
        
        publications = session.query(
            Publication.id,
            Publication.title,
            Publication.isbn,
            Publication.price,
            Publication.stock_quantity,
            func.count(Review.id).label('reviews_count'),
            func.avg(Review.rating).label('avg_rating'),
            func.sum(OrderItem.quantity).label('total_sold')
        ).outerjoin(Review).outerjoin(OrderItem).group_by(Publication.id).all()
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(Config.EXPORT_PATH, f'publications_stats_{timestamp}.csv')
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Заголовки
            headers = [
                'id', 'title', 'isbn', 'price', 'stock_quantity',
                'reviews_count', 'average_rating', 'total_sold', 'total_revenue'
            ]
            writer.writerow(headers)
            
            # Данные
            for pub in publications:
                total_revenue = (pub.total_sold or 0) * pub.price
                writer.writerow([
                    pub.id,
                    pub.title,
                    pub.isbn,
                    pub.price,
                    pub.stock_quantity,
                    pub.reviews_count,
                    round(pub.avg_rating, 2) if pub.avg_rating else 0,
                    pub.total_sold or 0,
                    total_revenue
                ])
        
        return file_path