from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from models.database_models import User, UserRole
from typing import Optional, Tuple
import re

class AuthManager:
    """Менеджер аутентификации и авторизации"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Валидация email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Валидация пароля"""
        if len(password) < 8:
            return False, "Пароль должен содержать не менее 8 символов"
        if not any(c.isupper() for c in password):
            return False, "Пароль должен содержать хотя бы одну заглавную букву"
        if not any(c.isdigit() for c in password):
            return False, "Пароль должен содержать хотя бы одну цифру"
        return True, "Пароль действителен"
    
    @staticmethod
    def register_user(session: Session, email: str, password: str, 
                     first_name: str, last_name: str, role: UserRole = UserRole.USER) -> Tuple[bool, str]:
        """Регистрация нового пользователя"""
        
        # Проверка email
        if not AuthManager.validate_email(email):
            return False, "Неверный формат email"
        
        # Проверка пароля
        is_valid, message = AuthManager.validate_password(password)
        if not is_valid:
            return False, message
        
        # Проверка существования пользователя
        existing_user = session.query(User).filter_by(email=email).first()
        if existing_user:
            return False, "Пользователь с таким email уже существует"
        
        # Создание пользователя
        try:
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            session.add(user)
            session.commit()
            return True, "Пользователь успешно зарегистрирован"
        except Exception as e:
            session.rollback()
            return False, f"Ошибка при регистрации: {str(e)}"
    
    @staticmethod
    def login_user(session: Session, email: str, password: str) -> Tuple[Optional[User], str]:
            """Аутентификация пользователя"""
            user = session.query(User).filter_by(email=email, is_active=True).first()

            if not user:
                return None, "Пользователь не найден или неактивен"

            if not check_password_hash(user.password_hash, password):
                return None, "Неверный пароль"

            return user, "Успешный вход"
    
    @staticmethod
    def change_password(session: Session, user: User, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Смена пароля пользователя"""
        
        if not check_password_hash(user.password_hash, old_password):
            return False, "Неверный текущий пароль"
        
        is_valid, message = AuthManager.validate_password(new_password)
        if not is_valid:
            return False, message
        
        try:
            user.password_hash = generate_password_hash(new_password)
            session.commit()
            return True, "Пароль успешно изменен"
        except Exception as e:
            session.rollback()
            return False, f"Ошибка при смене пароля: {str(e)}"
    
    @staticmethod
    def has_permission(user: User, required_role: UserRole) -> bool:
        """Проверка прав доступа"""
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.LIBRARIAN: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    @staticmethod
    def deactivate_user(session: Session, admin_user: User, user_id: int) -> Tuple[bool, str]:
        """Деактивация пользователя (только для администратора)"""
        if not AuthManager.has_permission(admin_user, UserRole.ADMIN):
            return False, "Недостаточно прав"
        
        user = session.query(User).get(user_id)
        if not user:
            return False, "Пользователь не найден"
        
        if user.id == admin_user.id:
            return False, "Нельзя деактивировать себя"
        
        try:
            user.is_active = False
            session.commit()
            return True, f"Пользователь {user.email} деактивирован"
        except Exception as e:
            session.rollback()
            return False, f"Ошибка при деактивации: {str(e)}"