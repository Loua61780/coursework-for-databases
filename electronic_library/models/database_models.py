from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Enum, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.sql import func
import enum
from config import Config

Base = declarative_base()

# Таблица для связи многие-ко-многим: публикации и авторы
publication_authors = Table(
    'publication_authors',
    Base.metadata,
    Column('publication_id', Integer, ForeignKey('publications.id')),
    Column('author_id', Integer, ForeignKey('authors.id'))
)

# Таблица для связи многие-ко-многим: публикации и жанры
publication_genres = Table(
    'publication_genres',
    Base.metadata,
    Column('publication_id', Integer, ForeignKey('publications.id')),
    Column('genre_id', Integer, ForeignKey('genres.id'))
)

class UserRole(enum.Enum):
    ADMIN = 'admin'
    LIBRARIAN = 'librarian'
    USER = 'user'

class OrderStatus(enum.Enum):
    PENDING = 'pending'
    PAID = 'paid'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    registration_date = Column(DateTime, default=datetime.utcnow)
    address = Column(Text)
    phone = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    
    # Связи
    orders = relationship('Order', back_populates='user', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'role': self.role.value,
            'is_active': self.is_active
        }

class Author(Base):
    """Модель автора"""
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    bio = Column(Text)
    birth_date = Column(DateTime)
    country = Column(String(100))
    
    # Связи
    publications = relationship('Publication', secondary=publication_authors, back_populates='authors')
    
    def __repr__(self):
        return f'<Author {self.full_name}>'

class Genre(Base):
    """Модель жанра"""
    __tablename__ = 'genres'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    # Связи
    publications = relationship('Publication', secondary=publication_genres, back_populates='genres')
    
    def __repr__(self):
        return f'<Genre {self.name}>'

class Publisher(Base):
    """Модель издательства"""
    __tablename__ = 'publishers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    contact_email = Column(String(255))
    website = Column(String(255))
    
    # Связи
    publications = relationship('Publication', back_populates='publisher')
    
    def __repr__(self):
        return f'<Publisher {self.name}>'

class Publication(Base):
    """Модель издания (книги)"""
    __tablename__ = 'publications'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    isbn = Column(String(20), unique=True)
    publication_year = Column(Integer)
    price = Column(Float, nullable=False)
    file_format = Column(String(10))
    file_url = Column(String(500))
    cover_image_url = Column(String(500))
    stock_quantity = Column(Integer, default=0)
    pages = Column(Integer)
    language = Column(String(50), default='Русский')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Внешние ключи
    publisher_id = Column(Integer, ForeignKey('publishers.id'))
    
    # Связи
    publisher = relationship('Publisher', back_populates='publications')
    authors = relationship('Author', secondary=publication_authors, back_populates='publications')
    genres = relationship('Genre', secondary=publication_genres, back_populates='publications')
    order_items = relationship('OrderItem', back_populates='publication')
    reviews = relationship('Review', back_populates='publication', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Publication {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'isbn': self.isbn,
            'publication_year': self.publication_year,
            'price': self.price,
            'stock_quantity': self.stock_quantity,
            'language': self.language,
            'authors': [author.full_name for author in self.authors],
            'genres': [genre.name for genre in self.genres],
            'publisher': self.publisher.name if self.publisher else None
        }

class Order(Base):
    """Модель заказа"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True)
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_method = Column(String(50))
    shipping_address = Column(Text)
    notes = Column(Text)
    
    # Внешние ключи
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Связи
    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'order_date': self.order_date.isoformat(),
            'total_amount': self.total_amount,
            'status': self.status.value,
            'user_email': self.user.email,
            'items_count': len(self.items)
        }

class OrderItem(Base):
    """Модель позиции заказа"""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    
    # Внешние ключи
    order_id = Column(Integer, ForeignKey('orders.id'))
    publication_id = Column(Integer, ForeignKey('publications.id'))
    
    # Связи
    order = relationship('Order', back_populates='items')
    publication = relationship('Publication', back_populates='order_items')
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'

class Review(Base):
    """Модель отзыва"""
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_approved = Column(Boolean, default=True)
    
    # Внешние ключи
    user_id = Column(Integer, ForeignKey('users.id'))
    publication_id = Column(Integer, ForeignKey('publications.id'))
    
    # Связи
    user = relationship('User', back_populates='reviews')
    publication = relationship('Publication', back_populates='reviews')
    
    def __repr__(self):
        return f'<Review {self.id}>'

class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self, database_url=None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Получить сессию БД"""
        return self.SessionLocal()
    
    def init_db(self):
        """Инициализация базы данных с тестовыми данными"""
        session = self.get_session()
        try:
            # Проверяем, есть ли уже данные
            if session.query(User).count() == 0:
                self._create_test_data(session)
                session.commit()
                print("База данных инициализирована с тестовыми данными")
        finally:
            session.close()
    
    def _create_test_data(self, session):
        """Создание тестовых данных"""
        from werkzeug.security import generate_password_hash
        
        # Создаем пользователей
        users = [
            User(
                email='admin@library.ru',
                password_hash=generate_password_hash('admin123'),
                first_name='Админ',
                last_name='Системный',
                role=UserRole.ADMIN
            ),
            User(
                email='librarian@library.ru',
                password_hash=generate_password_hash('lib123'),
                first_name='Мария',
                last_name='Библиотекарь',
                role=UserRole.LIBRARIAN
            ),
            User(
                email='user@example.com',
                password_hash=generate_password_hash('user123'),
                first_name='Иван',
                last_name='Петров',
                role=UserRole.USER
            )
        ]
        session.add_all(users)
        
        # Создаем жанры
        genres = [
            Genre(name='Фантастика', description='Научная фантастика и фэнтези'),
            Genre(name='Программирование', description='Книги по программированию'),
            Genre(name='Детектив', description='Детективные романы'),
            Genre(name='Классика', description='Классическая литература'),
            Genre(name='Бизнес', description='Бизнес-литература')
        ]
        session.add_all(genres)
        
        # Создаем авторов
        authors = [
            Author(full_name='Айзек Азимов', country='США'),
            Author(full_name='Роберт Мартин', country='США'),
            Author(full_name='Артур Конан Дойл', country='Великобритания'),
            Author(full_name='Лев Толстой', country='Россия'),
            Author(full_name='Стивен Кови', country='США')
        ]
        session.add_all(authors)
        
        # Создаем издательства
        publishers = [
            Publisher(name='Эксмо', contact_email='info@eksmo.ru'),
            Publisher(name='Питер', contact_email='info@piter.com'),
            Publisher(name='АСТ', contact_email='info@ast.ru'),
            Publisher(name='Манн, Иванов и Фербер', contact_email='info@mann-ivanov-ferber.ru')
        ]
        session.add_all(publishers)
        
        session.flush()  # Получаем ID созданных объектов
        
        # Создаем публикации
        publications = [
            Publication(
                title='Я, робот',
                description='Классический сборник рассказов о роботах',
                isbn='978-5-699-12345-1',
                publication_year=1950,
                price=450.0,
                stock_quantity=10,
                pages=320,
                publisher_id=publishers[0].id
            ),
            Publication(
                title='Чистый код',
                description='Руководство по написанию читаемого кода',
                isbn='978-5-4461-1234-5',
                publication_year=2008,
                price=1200.0,
                stock_quantity=5,
                pages=464,
                publisher_id=publishers[1].id
            ),
            Publication(
                title='Приключения Шерлока Холмса',
                description='Сборник детективных рассказов',
                isbn='978-5-17-123456-7',
                publication_year=1892,
                price=600.0,
                stock_quantity=8,
                pages=480,
                publisher_id=publishers[2].id
            ),
            Publication(
                title='Война и мир',
                description='Роман-эпопея Льва Толстого',
                isbn='978-5-04-123456-8',
                publication_year=1869,
                price=800.0,
                stock_quantity=3,
                pages=1225,
                publisher_id=publishers[0].id
            ),
            Publication(
                title='7 навыков высокоэффективных людей',
                description='Мощные инструменты развития личности',
                isbn='978-5-00146-123-4',
                publication_year=1989,
                price=950.0,
                stock_quantity=15,
                pages=396,
                publisher_id=publishers[3].id
            )
        ]
        session.add_all(publications)
        
        session.flush()
        
        # Связываем публикации с авторами и жанрами
        publications[0].authors = [authors[0]]
        publications[0].genres = [genres[0]]
        
        publications[1].authors = [authors[1]]
        publications[1].genres = [genres[1]]
        
        publications[2].authors = [authors[2]]
        publications[2].genres = [genres[2]]
        
        publications[3].authors = [authors[3]]
        publications[3].genres = [genres[3]]
        
        publications[4].authors = [authors[4]]
        publications[4].genres = [genres[4]]