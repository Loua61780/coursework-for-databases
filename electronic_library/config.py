import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///library.db')
    
    # Параметры резервного копирования
    BACKUP_PATH = os.getenv('BACKUP_PATH', 'backups/')
    REMOTE_HOST = os.getenv('REMOTE_HOST', '')
    REMOTE_USER = os.getenv('REMOTE_USER', '')
    REMOTE_PASSWORD = os.getenv('REMOTE_PASSWORD', '')
    REMOTE_PATH = os.getenv('REMOTE_PATH', '/backups/')
    
    # Настройки экспорта
    EXPORT_PATH = os.getenv('EXPORT_PATH', 'exports/')
    
    # Ключ шифрования для Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Роли пользователей
    USER_ROLES = {
        'admin': 'Администратор',
        'librarian': 'Библиотекарь',
        'user': 'Пользователь'
    }