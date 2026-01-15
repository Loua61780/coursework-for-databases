import json
import os
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.database_models import User, Publication, Order, Review, Author, Genre, Publisher
import pandas as pd
from config import Config

class JSONExporter:
    """Экспорт данных в JSON формат"""
    
    @staticmethod
    def export_users(session: Session, file_path: str = None) -> str:
        """Экспорт пользователей в JSON"""
        users = session.query(User).all()
        data = [user.to_dict() for user in users]
        
        if not file_path:
            file_path = os.path.join(Config.EXPORT_PATH, f'users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        return file_path
    
    @staticmethod
    def export_publications(session: Session, file_path: str = None) -> str:
        """Экспорт публикаций в JSON"""
        publications = session.query(Publication).all()
        data = []
        
        for pub in publications:
            pub_data = pub.to_dict()
            pub_data['reviews_count'] = len(pub.reviews)
            pub_data['average_rating'] = sum(r.rating for r in pub.reviews) / len(pub.reviews) if pub.reviews else 0
            data.append(pub_data)
        
        if not file_path:
            file_path = os.path.join(Config.EXPORT_PATH, f'publications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        return file_path
    
    @staticmethod
    def export_orders(session: Session, start_date: datetime = None, end_date: datetime = None, file_path: str = None) -> str:
        """Экспорт заказов в JSON с фильтрацией по дате"""
        query = session.query(Order)
        
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)
        
        orders = query.all()
        data = [order.to_dict() for order in orders]
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(Config.EXPORT_PATH, f'orders_{timestamp}.json')
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        return file_path
    
    @staticmethod
    def export_sales_report(session: Session, start_date: datetime, end_date: datetime, file_path: str = None) -> str:
        """Экспорт отчета по продажам в JSON"""
        from sqlalchemy import func
        
        # Агрегированные данные по продажам
        result = session.query(
            func.date(Order.order_date).label('date'),
            func.count(Order.id).label('orders_count'),
            func.sum(Order.total_amount).label('total_revenue'),
            func.sum(func.coalesce(OrderItem.quantity, 0)).label('items_sold')
        ).join(Order.items).filter(
            Order.status.in_(['paid', 'delivered']),
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).group_by(func.date(Order.order_date)).order_by('date').all()
        
        data = []
        total_revenue = 0
        total_orders = 0
        
        for row in result:
            data.append({
                'date': row.date.isoformat(),
                'orders_count': row.orders_count,
                'total_revenue': float(row.total_revenue or 0),
                'items_sold': row.items_sold or 0
            })
            total_revenue += float(row.total_revenue or 0)
            total_orders += row.orders_count
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'average_order_value': total_revenue / total_orders if total_orders > 0 else 0
            },
            'daily_data': data
        }
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(Config.EXPORT_PATH, f'sales_report_{timestamp}.json')
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        return file_path