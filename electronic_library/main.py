import os
import sys
from datetime import datetime, timedelta
from typing import Optional
from models.database_models import DatabaseManager, User, Publication, Order, Review, Author, Genre, Publisher, \
    UserRole, OrderItem, OrderStatus
from auth.auth_manager import AuthManager
from export.json_exporter import JSONExporter
from export.csv_exporter import CSVExporter
from export.pdf_exporter import PDFExporter
from backup.backup_manager import BackupManager
import pandas as pd
from sqlalchemy import func, desc
from models.database_models import DatabaseManager, User, Publication, Order, Review, Author, Genre, Publisher, UserRole, OrderItem, OrderStatus


class ElectronicLibraryApp:
    """Основное приложение электронной библиотеки"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthManager()
        self.backup_manager = BackupManager()
        self.current_user: Optional[User] = None
        self.session = self.db_manager.get_session()
        self.cart = []  # Временная корзина для текущей сессии

    def run(self):
        """Запуск приложения"""
        print("=" * 60)
        print("ЭЛЕКТРОННАЯ БИБЛИОТЕКА - Система управления")
        print("=" * 60)

        # Инициализация базы данных
        self.db_manager.init_db()

        while True:
            if not self.current_user:
                self.show_main_menu()
            else:
                self.show_user_menu()

    def show_main_menu(self):
        """Главное меню (неавторизованный пользователь)"""
        print("\n" + "=" * 60)
        print("ГЛАВНОЕ МЕНЮ")
        print("=" * 60)
        print("1. Вход в систему")
        print("2. Регистрация")
        print("3. Просмотр каталога (без входа)")
        print("4. Поиск изданий")
        print("5. Экспорт каталога (JSON/CSV)")
        print("6. Выход из программы")

        choice = input("\nВыберите действие (1-6): ").strip()

        if choice == "1":
            self.login()
        elif choice == "2":
            self.register()
        elif choice == "3":
            self.browse_catalog()
        elif choice == "4":
            self.search_publications()
        elif choice == "5":
            self.export_catalog_public()
        elif choice == "6":
            print("\nДо свидания!")
            self.session.close()
            sys.exit(0)
        else:
            print("\nНеверный выбор. Попробуйте снова.")

    def show_user_menu(self):
        """Меню авторизованного пользователя"""
        print(f"\n{'=' * 60}")
        print(f"ДОБРО ПОЖАЛОВАТЬ, {self.current_user.first_name}!")
        print(f"Роль: {self.current_user.role.value.upper()}")
        print(f"{'=' * 60}")

        print("\nОСНОВНЫЕ ФУНКЦИИ:")
        print("1. Просмотр каталога")
        print("2. Поиск изданий")
        print("3. Корзина покупок")
        print("4. Мои заказы")
        print("5. Мои отзывы")
        print("6. Личный кабинет")

        if self.current_user.role in [UserRole.ADMIN, UserRole.LIBRARIAN]:
            print("\nАДМИНИСТРАТИВНЫЕ ФУНКЦИИ:")
            print("7. Управление публикациями")
            print("8. Управление пользователями")
            print("9. Управление заказами")
            print("10. Отчеты и аналитика")
            print("11. Экспорт данных")
            print("12. Резервное копирование")

        print("\n13. Выйти из аккаунта")
        print("14. Выход из программы")

        choice = input("\nВыберите действие: ").strip()

        if choice == "1":
            self.browse_catalog()
        elif choice == "2":
            self.search_publications()
        elif choice == "3":
            self.cart_menu()
        elif choice == "4":
            self.view_my_orders()
        elif choice == "5":
            self.view_my_reviews()
        elif choice == "6":
            self.user_profile()
        elif choice == "7" and self.current_user.role in [UserRole.ADMIN, UserRole.LIBRARIAN]:
            self.manage_publications()
        elif choice == "8" and self.current_user.role == UserRole.ADMIN:
            self.manage_users()
        elif choice == "9" and self.current_user.role in [UserRole.ADMIN, UserRole.LIBRARIAN]:
            self.manage_orders()
        elif choice == "10" and self.current_user.role in [UserRole.ADMIN, UserRole.LIBRARIAN]:
            self.reports_menu()
        elif choice == "11" and self.current_user.role in [UserRole.ADMIN, UserRole.LIBRARIAN]:
            self.export_menu()
        elif choice == "12" and self.current_user.role == UserRole.ADMIN:
            self.backup_menu()
        elif choice == "13":
            self.current_user = None
            self.cart = []
            print("\nВы вышли из аккаунта.")
        elif choice == "14":
            print("\nДо свидания!")
            self.session.close()
            sys.exit(0)
        else:
            print("\nНеверный выбор или недостаточно прав.")

    def login(self):
        """Вход в систему"""
        print("\n" + "=" * 60)
        print("ВХОД В СИСТЕМУ")
        print("=" * 60)

        email = input("Email: ").strip()
        password = input("Пароль: ").strip()

        user, message = self.auth_manager.login_user(self.session, email, password)

        if user:
            self.current_user = user
            print(f"\n✓ {message}")
            print(f"Добро пожаловать, {user.first_name}!")
        else:
            print(f"\n✗ {message}")

    def register(self):
        """Регистрация нового пользователя"""
        print("\n" + "=" * 60)
        print("РЕГИСТРАЦИЯ")
        print("=" * 60)

        email = input("Email: ").strip()
        password = input("Пароль: ").strip()
        confirm_password = input("Подтвердите пароль: ").strip()

        if password != confirm_password:
            print("\n✗ Пароли не совпадают!")
            return

        first_name = input("Имя: ").strip()
        last_name = input("Фамилия: ").strip()

        success, message = self.auth_manager.register_user(
            self.session, email, password, first_name, last_name
        )

        if success:
            print(f"\n✓ {message}")
            # Автоматический вход после регистрации
            self.login()
        else:
            print(f"\n✗ {message}")

    def browse_catalog(self):
        """Просмотр каталога"""
        print("\n" + "=" * 60)
        print("КАТАЛОГ ИЗДАНИЙ")
        print("=" * 60)

        publications = self.session.query(Publication).limit(20).all()

        if not publications:
            print("Каталог пуст.")
            return

        for i, pub in enumerate(publications, 1):
            authors = ", ".join([a.full_name for a in pub.authors[:2]])
            if len(pub.authors) > 2:
                authors += " и др."

            print(f"\n{i}. {pub.title}")
            print(f"   Авторы: {authors}")
            print(f"   Год: {pub.publication_year} | Цена: {pub.price} руб.")
            print(f"   На складе: {pub.stock_quantity} шт.")

            if pub.description and len(pub.description) > 100:
                print(f"   Описание: {pub.description[:100]}...")
            elif pub.description:
                print(f"   Описание: {pub.description}")

            if self.current_user:
                add_to_cart = input("\nДобавить в корзину? (y/n): ").strip().lower()
                if add_to_cart == 'y':
                    try:
                        quantity = int(input("Количество: "))
                        if quantity > 0 and quantity <= pub.stock_quantity:
                            self.cart.append({
                                'publication': pub,
                                'quantity': quantity,
                                'unit_price': pub.price
                            })
                            print(f"✓ Добавлено в корзину: {pub.title}")
                        else:
                            print("✗ Неверное количество или недостаточно на складе.")
                    except ValueError:
                        print("✗ Неверный ввод.")

        print(f"\nВсего изданий: {len(publications)}")

    def search_publications(self):
        """Поиск изданий"""
        print("\n" + "=" * 60)
        print("ПОИСК ИЗДАНИЙ")
        print("=" * 60)

        print("\nКритерии поиска (оставьте пустым для пропуска):")
        title = input("Название: ").strip()
        author = input("Автор: ").strip()
        genre = input("Жанр: ").strip()
        min_year = input("Минимальный год издания: ").strip()
        max_year = input("Максимальный год издания: ").strip()
        min_price = input("Минимальная цена: ").strip()
        max_price = input("Максимальная цена: ").strip()

        # Построение запроса
        query = self.session.query(Publication)

        if title:
            query = query.filter(Publication.title.ilike(f"%{title}%"))
        if author:
            query = query.filter(Publication.authors.any(Author.full_name.ilike(f"%{author}%")))
        if genre:
            query = query.filter(Publication.genres.any(Genre.name.ilike(f"%{genre}%")))
        if min_year:
            query = query.filter(Publication.publication_year >= int(min_year))
        if max_year:
            query = query.filter(Publication.publication_year <= int(max_year))
        if min_price:
            query = query.filter(Publication.price >= float(min_price))
        if max_price:
            query = query.filter(Publication.price <= float(max_price))

        publications = query.limit(50).all()

        if not publications:
            print("\nПо вашему запросу ничего не найдено.")
            return

        print(f"\nНайдено изданий: {len(publications)}")
        for i, pub in enumerate(publications, 1):
            authors = ", ".join([a.full_name for a in pub.authors[:2]])
            print(f"\n{i}. {pub.title}")
            print(f"   Авторы: {authors}")
            print(f"   Год: {pub.publication_year} | Цена: {pub.price} руб.")

        if self.current_user:
            pub_num = input("\nВведите номер издания для детального просмотра (0 для выхода): ").strip()
            if pub_num.isdigit() and 1 <= int(pub_num) <= len(publications):
                self.show_publication_details(publications[int(pub_num) - 1])

    def show_publication_details(self, publication):
        """Показать детальную информацию об издании"""
        print(f"\n{'=' * 60}")
        print(f"{publication.title}")
        print(f"{'=' * 60}")

        print(f"\nАвторы: {', '.join([a.full_name for a in publication.authors])}")
        print(f"Жанры: {', '.join([g.name for g in publication.genres])}")
        if publication.publisher:
            print(f"Издательство: {publication.publisher.name}")
        print(f"\nISBN: {publication.isbn or 'не указан'}")
        print(f"Год издания: {publication.publication_year}")
        print(f"Язык: {publication.language}")
        print(f"Страниц: {publication.pages or 'не указано'}")
        print(f"\nЦена: {publication.price} руб.")
        print(f"На складе: {publication.stock_quantity} шт.")

        if publication.description:
            print(f"\nОписание:\n{publication.description}")

        # Отзывы
        reviews = publication.reviews
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            print(f"\nРейтинг: {avg_rating:.1f}/5 ({len(reviews)} отзывов)")
            for review in reviews[:3]:  # Показать первые 3 отзыва
                print(f"\n  {review.user.first_name}: {review.rating}★")
                if review.comment:
                    print(f"  {review.comment[:100]}...")

        if self.current_user:
            print("\nДействия:")
            print("1. Добавить в корзину")
            print("2. Написать отзыв")
            print("3. Вернуться")

            choice = input("\nВыберите действие: ").strip()

            if choice == "1":
                quantity = int(input("Количество: "))
                if 0 < quantity <= publication.stock_quantity:
                    self.cart.append({
                        'publication': publication,
                        'quantity': quantity,
                        'unit_price': publication.price
                    })
                    print(f"✓ Добавлено в корзину: {publication.title}")
                else:
                    print("✗ Неверное количество или недостаточно на складе.")
            elif choice == "2":
                self.add_review(publication)

    def cart_menu(self):
        """Управление корзиной"""
        if not self.current_user:
            print("✗ Необходимо войти в систему.")
            return

        print("\n" + "=" * 60)
        print("КОРЗИНА ПОКУПОК")
        print("=" * 60)

        if not self.cart:
            print("Корзина пуста.")
            return

        total = 0
        for i, item in enumerate(self.cart, 1):
            item_total = item['quantity'] * item['unit_price']
            total += item_total
            print(f"\n{i}. {item['publication'].title}")
            print(f"   Количество: {item['quantity']} x {item['unit_price']} = {item_total} руб.")

        print(f"\nИтого: {total} руб.")

        print("\nДействия:")
        print("1. Оформить заказ")
        print("2. Удалить товар из корзины")
        print("3. Очистить корзину")
        print("4. Продолжить покупки")

        choice = input("\nВыберите действие: ").strip()

        if choice == "1":
            self.create_order()
        elif choice == "2":
            item_num = int(input("Номер товара для удаления: "))
            if 1 <= item_num <= len(self.cart):
                removed = self.cart.pop(item_num - 1)
                print(f"✓ Удалено: {removed['publication'].title}")
        elif choice == "3":
            self.cart = []
            print("✓ Корзина очищена.")

    def create_order(self):
        """Создание заказа из корзины"""
        if not self.cart:
            print("✗ Корзина пуста.")
            return

        total = sum(item['quantity'] * item['unit_price'] for item in self.cart)

        print(f"\nОформление заказа на сумму: {total} руб.")
        print("Способы оплаты:")
        print("1. Банковская карта")
        print("2. Электронный кошелек")
        print("3. Наличные при получении")

        payment_method = input("\nВыберите способ оплаты (1-3): ").strip()
        payment_methods = {
            '1': 'Банковская карта',
            '2': 'Электронный кошелек',
            '3': 'Наличные при получении'
        }

        payment_method_text = payment_methods.get(payment_method, 'Не указан')

        print("\nАдрес доставки:")
        address = input("Введите адрес (оставьте пустым, если использовать адрес из профиля): ").strip()
        if not address and self.current_user.address:
            address = self.current_user.address
            print(f"Используется адрес из профиля: {address}")

        # Подтверждение
        print(f"\nПодтверждение заказа:")
        print(f"Сумма: {total} руб.")
        print(f"Способ оплаты: {payment_method_text}")
        print(f"Адрес доставки: {address}")

        confirm = input("\nПодтвердить заказ? (y/n): ").strip().lower()

        if confirm == 'y':
            try:
                # Создаем заказ
                order = Order(
                    order_number=f"ORD-{datetime.now().strftime('%Y%m%d')}-{self.current_user.id:04d}",
                    user_id=self.current_user.id,
                    total_amount=total,
                    status=OrderStatus.PENDING,
                    payment_method=payment_method_text,
                    shipping_address=address
                )
                self.session.add(order)
                self.session.flush()  # Получаем ID заказа

                # Добавляем позиции заказа
                for item in self.cart:
                    order_item = OrderItem(
                        order_id=order.id,
                        publication_id=item['publication'].id,
                        quantity=item['quantity'],
                        unit_price=item['unit_price']
                    )
                    self.session.add(order_item)

                    # Уменьшаем количество на складе
                    item['publication'].stock_quantity -= item['quantity']

                self.session.commit()

                # Очищаем корзину
                self.cart = []

                print(f"\n✓ Заказ успешно оформлен!")
                print(f"Номер заказа: {order.order_number}")
                print("Вы можете отслеживать статус заказа в разделе 'Мои заказы'.")

            except Exception as e:
                self.session.rollback()
                print(f"\n✗ Ошибка при оформлении заказа: {str(e)}")

    def view_my_orders(self):
        """Просмотр заказов пользователя"""
        if not self.current_user:
            print("✗ Необходимо войти в систему.")
            return

        print("\n" + "=" * 60)
        print("МОИ ЗАКАЗЫ")
        print("=" * 60)

        orders = self.session.query(Order).filter_by(user_id=self.current_user.id) \
            .order_by(desc(Order.order_date)).all()

        if not orders:
            print("У вас еще нет заказов.")
            return

        for order in orders:
            print(f"\nЗаказ #{order.order_number}")
            print(f"Дата: {order.order_date.strftime('%d.%m.%Y %H:%M')}")
            print(f"Статус: {order.status.value}")
            print(f"Сумма: {order.total_amount} руб.")
            print(f"Способ оплаты: {order.payment_method or 'Не указан'}")

            # Детали заказа
            if order.items:
                print("  Товары:")
                for item in order.items:
                    print(f"    - {item.publication.title}: {item.quantity} x {item.unit_price} руб.")

    def view_my_reviews(self):
        """Просмотр отзывов пользователя"""
        if not self.current_user:
            print("✗ Необходимо войти в систему.")
            return

        print("\n" + "=" * 60)
        print("МОИ ОТЗЫВЫ")
        print("=" * 60)

        reviews = self.session.query(Review).filter_by(user_id=self.current_user.id) \
            .order_by(desc(Review.created_at)).all()

        if not reviews:
            print("Вы еще не оставляли отзывов.")
            return

        for review in reviews:
            print(f"\nИздание: {review.publication.title}")
            print(f"Оценка: {'★' * review.rating}{'☆' * (5 - review.rating)}")
            print(f"Дата: {review.created_at.strftime('%d.%m.%Y')}")
            if review.comment:
                print(f"Комментарий: {review.comment[:100]}...")

    def add_review(self, publication):
        """Добавление отзыва к изданию"""
        if not self.current_user:
            print("✗ Необходимо войти в систему.")
            return

        print(f"\nДобавление отзыва к изданию: {publication.title}")

        rating = int(input("Оценка (1-5): "))
        if rating < 1 or rating > 5:
            print("✗ Оценка должна быть от 1 до 5.")
            return

        comment = input("Комментарий (необязательно): ").strip()

        try:
            # Проверяем, не оставлял ли пользователь уже отзыв на это издание
            existing_review = self.session.query(Review).filter_by(
                user_id=self.current_user.id,
                publication_id=publication.id
            ).first()

            if existing_review:
                update = input("У вас уже есть отзыв на это издание. Обновить? (y/n): ").strip().lower()
                if update == 'y':
                    existing_review.rating = rating
                    existing_review.comment = comment
                    print("✓ Отзыв обновлен.")
                else:
                    return
            else:
                review = Review(
                    user_id=self.current_user.id,
                    publication_id=publication.id,
                    rating=rating,
                    comment=comment
                )
                self.session.add(review)
                print("✓ Отзыв добавлен.")

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            print(f"✗ Ошибка при добавлении отзыва: {str(e)}")

    def user_profile(self):
        """Управление профилем пользователя"""
        if not self.current_user:
            print("✗ Необходимо войти в систему.")
            return

        print("\n" + "=" * 60)
        print("ЛИЧНЫЙ КАБИНЕТ")
        print("=" * 60)

        print(f"\nЛичная информация:")
        print(f"Имя: {self.current_user.first_name}")
        print(f"Фамилия: {self.current_user.last_name}")
        print(f"Email: {self.current_user.email}")
        print(f"Дата регистрации: {self.current_user.registration_date.strftime('%d.%m.%Y')}")
        print(f"Адрес: {self.current_user.address or 'Не указан'}")

        print("\nДействия:")
        print("1. Изменить личную информацию")
        print("2. Изменить пароль")
        print("3. Вернуться в меню")

        choice = input("\nВыберите действие: ").strip()

        if choice == "1":
            self.update_profile()
        elif choice == "2":
            self.change_password()

    def update_profile(self):
        """Обновление профиля пользователя"""
        print("\nОбновление профиля:")

        new_first_name = input(f"Имя ({self.current_user.first_name}): ").strip()
        new_last_name = input(f"Фамилия ({self.current_user.last_name}): ").strip()
        new_address = input(f"Адрес ({self.current_user.address or 'Не указан'}): ").strip()

        try:
            if new_first_name:
                self.current_user.first_name = new_first_name
            if new_last_name:
                self.current_user.last_name = new_last_name
            if new_address:
                self.current_user.address = new_address

            self.session.commit()
            print("✓ Профиль обновлен.")

        except Exception as e:
            self.session.rollback()
            print(f"✗ Ошибка при обновлении профиля: {str(e)}")

    def change_password(self):
        """Смена пароля"""
        print("\nСмена пароля:")

        old_password = input("Текущий пароль: ").strip()
        new_password = input("Новый пароль: ").strip()
        confirm_password = input("Подтвердите новый пароль: ").strip()

        if new_password != confirm_password:
            print("✗ Новые пароли не совпадают.")
            return

        success, message = self.auth_manager.change_password(
            self.session, self.current_user, old_password, new_password
        )

        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")

    def manage_publications(self):
        """Управление публикациями (для администраторов и библиотекарей)"""
        if not self.current_user or self.current_user.role not in [UserRole.ADMIN, UserRole.LIBRARIAN]:
            print("✗ Недостаточно прав.")
            return

        print("\n" + "=" * 60)
        print("УПРАВЛЕНИЕ ПУБЛИКАЦИЯМИ")
        print("=" * 60)

        print("\nДействия:")
        print("1. Добавить новую публикацию")
        print("2. Редактировать существующую")
        print("3. Удалить публикацию")
        print("4. Просмотр всех публикаций")
        print("5. Поиск публикаций для редактирования")
        print("6. Вернуться")

        choice = input("\nВыберите действие: ").strip()

        if choice == "1":
            self.add_publication()
        elif choice == "2":
            self.edit_publication()
        elif choice == "3":
            self.delete_publication()
        elif choice == "4":
            self.view_all_publications()
        elif choice == "5":
            self.search_publications_to_edit()

    def add_publication(self):
        """Добавление новой публикации"""
        print("\nДобавление новой публикации:")

        title = input("Название: ").strip()
        if not title:
            print("✗ Название обязательно.")
            return

        description = input("Описание: ").strip()
        isbn = input("ISBN (необязательно): ").strip()

        try:
            publication_year = int(input("Год издания: "))
        except ValueError:
            print("✗ Год должен быть числом.")
            return

        try:
            price = float(input("Цена: "))
        except ValueError:
            print("✗ Цена должна быть числом.")
            return

        try:
            stock_quantity = int(input("Количество на складе: "))
        except ValueError:
            print("✗ Количество должно быть целым числом.")
            return

        pages = input("Количество страниц (необязательно): ").strip()
        language = input("Язык (по умолчанию 'Русский'): ").strip() or "Русский"

        try:
            publication = Publication(
                title=title,
                description=description,
                isbn=isbn if isbn else None,
                publication_year=publication_year,
                price=price,
                stock_quantity=stock_quantity,
                language=language
            )

            if pages:
                publication.pages = int(pages)

            # Добавление авторов
            authors_input = input("Авторы (через запятую): ").strip()
            if authors_input:
                author_names = [name.strip() for name in authors_input.split(',')]
                for author_name in author_names:
                    author = self.session.query(Author).filter_by(full_name=author_name).first()
                    if not author:
                        author = Author(full_name=author_name)
                        self.session.add(author)
                    publication.authors.append(author)

            # Добавление жанров
            genres_input = input("Жанры (через запятую): ").strip()
            if genres_input:
                genre_names = [name.strip() for name in genres_input.split(',')]
                for genre_name in genre_names:
                    genre = self.session.query(Genre).filter_by(name=genre_name).first()
                    if not genre:
                        genre = Genre(name=genre_name)
                        self.session.add(genre)
                    publication.genres.append(genre)

            self.session.add(publication)
            self.session.commit()

            print(f"✓ Публикация '{title}' успешно добавлена.")

        except Exception as e:
            self.session.rollback()
            print(f"✗ Ошибка при добавлении публикации: {str(e)}")

    def edit_publication(self):
        """Редактирование публикации"""
        publication_id = input("\nВведите ID публикации для редактирования: ").strip()

        if not publication_id.isdigit():
            print("✗ ID должен быть числом.")
            return

        publication = self.session.query(Publication).get(int(publication_id))

        if not publication:
            print("✗ Публикация не найдена.")
            return

        print(f"\nРедактирование публикации: {publication.title}")
        print("Оставьте поле пустым, чтобы не изменять значение.")

        new_title = input(f"Название ({publication.title}): ").strip()
        if new_title:
            publication.title = new_title

        new_description = input(f"Описание ({publication.description or 'нет'}): ").strip()
        if new_description:
            publication.description = new_description

        new_price = input(f"Цена ({publication.price}): ").strip()
        if new_price:
            try:
                publication.price = float(new_price)
            except ValueError:
                print("✗ Цена должна быть числом.")

        new_stock = input(f"Количество на складе ({publication.stock_quantity}): ").strip()
        if new_stock:
            try:
                publication.stock_quantity = int(new_stock)
            except ValueError:
                print("✗ Количество должно быть целым числом.")

        try:
            self.session.commit()
            print("✓ Публикация обновлена.")
        except Exception as e:
            self.session.rollback()
            print(f"✗ Ошибка при обновлении публикации: {str(e)}")

    def delete_publication(self):
        """Удаление публикации"""
        publication_id = input("\nВведите ID публикации для удаления: ").strip()

        if not publication_id.isdigit():
            print("✗ ID должен быть числом.")
            return

        publication = self.session.query(Publication).get(int(publication_id))

        if not publication:
            print("✗ Публикация не найдена.")
            return

        confirm = input(f"Вы уверены, что хотите удалить публикацию '{publication.title}'? (y/n): ").strip().lower()

        if confirm == 'y':
            try:
                self.session.delete(publication)
                self.session.commit()
                print("✓ Публикация удалена.")
            except Exception as e:
                self.session.rollback()
                print(f"✗ Ошибка при удалении публикации: {str(e)}")

    def view_all_publications(self):
        """Просмотр всех публикаций"""
        publications = self.session.query(Publication).all()

        if not publications:
            print("Нет публикаций.")
            return

        print(f"\nВсего публикаций: {len(publications)}")
        for pub in publications:
            print(f"\nID: {pub.id} | {pub.title}")
            print(f"  Авторы: {', '.join([a.full_name for a in pub.authors])}")
            print(f"  Цена: {pub.price} руб. | На складе: {pub.stock_quantity} шт.")

    def search_publications_to_edit(self):
        """Поиск публикаций для редактирования"""
        keyword = input("\nВведите ключевое слово для поиска (название, автор, ISBN): ").strip()

        if not keyword:
            print("✗ Введите ключевое слово для поиска.")
            return

        publications = self.session.query(Publication).filter(
            Publication.title.ilike(f"%{keyword}%") |
            Publication.isbn.ilike(f"%{keyword}%")
        ).all()

        if not publications:
            print("Публикации не найдены.")
            return

        for pub in publications:
            print(f"\nID: {pub.id} | {pub.title}")
            print(f"  Авторы: {', '.join([a.full_name for a in pub.authors])}")
            print(f"  ISBN: {pub.isbn}")
            print(f"  Цена: {pub.price} руб. | На складе: {pub.stock_quantity} шт.")

    def manage_users(self):
        """Управление пользователями (только для администраторов)"""
        if not self.current_user or self.current_user.role != UserRole.ADMIN:
            print("✗ Недостаточно прав.")
            return

        print("\n" + "=" * 60)
        print("УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ")
        print("=" * 60)

        print("\nДействия:")
        print("1. Просмотр всех пользователей")
        print("2. Поиск пользователя")
        print("3. Изменить роль пользователя")
        print("4. Деактивировать/активировать пользователя")
        print("5. Просмотреть статистику пользователя")
        print("6. Вернуться")

        choice = input("\nВыберите действие: ").strip()

        if choice == "1":
            self.view_all_users()
        elif choice == "2":
            self.search_user()
        elif choice == "3":
            self.change_user_role()
        elif choice == "4":
            self.toggle_user_active()
        elif choice == "5":
            self.view_user_stats()

    def view_all_users(self):
        """Просмотр всех пользователей"""
        users = self.session.query(User).all()

        if not users:
            print("Нет пользователей.")
            return

        print(f"\nВсего пользователей: {len(users)}")
        for user in users:
            status = "Активен" if user.is_active else "Неактивен"
            print(f"\nID: {user.id} | {user.email}")
            print(f"  Имя: {user.first_name} {user.last_name}")
            print(f"  Роль: {user.role.value} | Статус: {status}")
            print(f"  Регистрация: {user.registration_date.strftime('%d.%m.%Y')}")

    def search_user(self):
        """Поиск пользователя"""
        keyword = input("\nВведите email или имя пользователя: ").strip()

        if not keyword:
            print("✗ Введите данные для поиска.")
            return

        users = self.session.query(User).filter(
            User.email.ilike(f"%{keyword}%") |
            User.first_name.ilike(f"%{keyword}%") |
            User.last_name.ilike(f"%{keyword}%")
        ).all()

        if not users:
            print("Пользователи не найдены.")
            return

        for user in users:
            status = "Активен" if user.is_active else "Неактивен"
            print(f"\nID: {user.id} | {user.email}")
            print(f"  Имя: {user.first_name} {user.last_name}")
            print(f"  Роль: {user.role.value} | Статус: {status}")

    def change_user_role(self):
        """Изменение роли пользователя"""
        user_id = input("\nВведите ID пользователя: ").strip()

        if not user_id.isdigit():
            print("✗ ID должен быть числом.")
            return

        user = self.session.query(User).get(int(user_id))

        if not user:
            print("✗ Пользователь не найден.")
            return

        if user.id == self.current_user.id:
            print("✗ Вы не можете изменить свою собственную роль.")
            return

        print(f"\nТекущая роль пользователя {user.email}: {user.role.value}")
        print("Доступные роли:")
        print("1. Пользователь (user)")
        print("2. Библиотекарь (librarian)")
        print("3. Администратор (admin)")

        role_choice = input("Выберите новую роль (1-3): ").strip()

        role_mapping = {
            '1': UserRole.USER,
            '2': UserRole.LIBRARIAN,
            '3': UserRole.ADMIN
        }

        new_role = role_mapping.get(role_choice)
        if not new_role:
            print("✗ Неверный выбор роли.")
            return

        try:
            user.role = new_role
            self.session.commit()
            print(f"✓ Роль пользователя {user.email} изменена на {new_role.value}.")
        except Exception as e:
            self.session.rollback()
            print(f"✗ Ошибка при изменении роли: {str(e)}")

    def toggle_user_active(self):
        """Активация/деактивация пользователя"""
        user_id = input("\nВведите ID пользователя: ").strip()

        if not user_id.isdigit():
            print("✗ ID должен быть числом.")
            return

        user = self.session.query(User).get(int(user_id))

        if not user:
            print("✗ Пользователь не найден.")
            return

        if user.id == self.current_user.id:
            print("✗ Вы не можете изменить свой собственный статус.")
            return

        new_status = not user.is_active
        status_text = "активирован" if new_status else "деактивирован"

        confirm = input(f"Вы уверены, что хотите {status_text} пользователя {user.email}? (y/n): ").strip().lower()

        if confirm == 'y':
            try:
                user.is_active = new_status
                self.session.commit()
                print(f"✓ Пользователь {user.email} {status_text}.")
            except Exception as e:
                self.session.rollback()
                print(f"✗ Ошибка при изменении статуса: {str(e)}")

    def view_user_stats(self):
        """Просмотр статистики пользователя"""
        user_id = input("\nВведите ID пользователя: ").strip()

        if not user_id.isdigit():
            print("✗ ID должен быть числом.")
            return

        user = self.session.query(User).get(int(user_id))

        if not user:
            print("✗ Пользователь не найден.")
            return

        # Статистика пользователя
        orders_count = self.session.query(Order).filter_by(user_id=user.id).count()
        reviews_count = self.session.query(Review).filter_by(user_id=user.id).count()

        # Сумма всех заказов
        total_spent_result = self.session.query(func.sum(Order.total_amount)) \
            .filter_by(user_id=user.id, status=OrderStatus.DELIVERED).first()
        total_spent = total_spent_result[0] or 0

        print(f"\nСтатистика пользователя: {user.email}")
        print(f"Имя: {user.first_name} {user.last_name}")
        print(f"Дата регистрации: {user.registration_date.strftime('%d.%m.%Y')}")
        print(f"Статус: {'Активен' if user.is_active else 'Неактивен'}")
        print(f"Роль: {user.role.value}")
        print(f"\nКоличество заказов: {orders_count}")
        print(f"Количество отзывов: {reviews_count}")
        print(f"Всего потрачено: {total_spent:.2f} руб.")

        if orders_count > 0:
            # Последние заказы
            last_orders = self.session.query(Order) \
                .filter_by(user_id=user.id) \
                .order_by(desc(Order.order_date)) \
                .limit(3).all()

            print("\nПоследние заказы:")
            for order in last_orders:
                print(f"  {order.order_number}: {order.total_amount} руб. ({order.status.value})")

    def manage_orders(self):
        """Управление заказами (для администраторов и библиотекарей)"""
        if not self.current_user or self.current_user.role not in [UserRole.ADMIN, UserRole.LIBRARIAN]:
            print("✗ Недостаточно прав.")
            return

        print("\n" + "=" * 60)
        print("УПРАВЛЕНИЕ ЗАКАЗАМИ")
        print("=" * 60)

        print("\nДействия:")
        print("1. Просмотр всех заказов")
        print("2. Поиск заказа")
        print("3. Изменить статус заказа")
        print("4. Просмотр деталей заказа")
        print("5. Вернуться")

        choice = input("\nВыберите действие: ").strip()

        if choice == "1":
            self.view_all_orders()
        elif choice == "2":
            self.search_order()
        elif choice == "3":
            self.change_order_status()
        elif choice == "4":
            self.view_order_details()

    def view_all_orders(self):
        """Просмотр всех заказов"""
        orders = self.session.query(Order).order_by(desc(Order.order_date)).limit(50).all()

        if not orders:
            print("Нет заказов.")
            return

        print(f"\nПоследние {len(orders)} заказов:")
        for order in orders:
            print(f"\n{order.order_number}")
            print(f"  Дата: {order.order_date.strftime('%d.%m.%Y %H:%M')}")
            print(f"  Пользователь: {order.user.email}")
            print(f"  Сумма: {order.total_amount} руб.")
            print(f"  Статус: {order.status.value}")

    def search_order(self):
        """Поиск заказа"""
        keyword = input("\nВведите номер заказа, email пользователя или ID: ").strip()

        if not keyword:
            print("✗ Введите данные для поиска.")
            return

        orders = self.session.query(Order).join(User).filter(
            Order.order_number.ilike(f"%{keyword}%") |
            User.email.ilike(f"%{keyword}%")
        ).all()

        if keyword.isdigit():
            orders_by_id = self.session.query(Order).filter_by(id=int(keyword)).all()
            orders = list(set(orders + orders_by_id))

        if not orders:
            print("Заказы не найдены.")
            return

        print(f"\nНайдено заказов: {len(orders)}")
        for order in orders:
            print(f"\n{order.order_number}")
            print(f"  Дата: {order.order_date.strftime('%d.%m.%Y %H:%M')}")
            print(f"  Пользователь: {order.user.email}")
            print(f"  Сумма: {order.total_amount} руб.")
            print(f"  Статус: {order.status.value}")

    def change_order_status(self):
        """Изменение статуса заказа"""
        order_number = input("\nВведите номер заказа: ").strip()

        order = self.session.query(Order).filter_by(order_number=order_number).first()

        if not order:
            print("✗ Заказ не найден.")
            return

        print(f"\nТекущий статус заказа {order_number}: {order.status.value}")
        print("Доступные статусы:")
        for i, status in enumerate(OrderStatus, 1):
            print(f"{i}. {status.value}")

        status_choice = input("Выберите новый статус (1-5): ").strip()

        try:
            status_index = int(status_choice) - 1
            if 0 <= status_index < len(list(OrderStatus)):
                new_status = list(OrderStatus)[status_index]
                order.status = new_status
                self.session.commit()
                print(f"✓ Статус заказа {order_number} изменен на {new_status.value}.")
            else:
                print("✗ Неверный выбор статуса.")
        except (ValueError, IndexError):
            print("✗ Неверный выбор статуса.")
        except Exception as e:
            self.session.rollback()
            print(f"✗ Ошибка при изменении статуса: {str(e)}")

    def view_order_details(self):
        """Просмотр деталей заказа"""
        order_number = input("\nВведите номер заказа: ").strip()

        order = self.session.query(Order).filter_by(order_number=order_number).first()

        if not order:
            print("✗ Заказ не найден.")
            return

        print(f"\nДетали заказа: {order.order_number}")
        print(f"Дата: {order.order_date.strftime('%d.%m.%Y %H:%M')}")
        print(f"Пользователь: {order.user.email} ({order.user.first_name} {order.user.last_name})")
        print(f"Статус: {order.status.value}")
        print(f"Способ оплаты: {order.payment_method or 'Не указан'}")
        print(f"Адрес доставки: {order.shipping_address or 'Не указан'}")
        print(f"\nТовары:")

        total = 0
        for item in order.items:
            item_total = item.quantity * item.unit_price
            total += item_total
            print(f"  - {item.publication.title}")
            print(f"    Количество: {item.quantity} x {item.unit_price} = {item_total} руб.")

        print(f"\nИтого: {total} руб.")

    def reports_menu(self):
        """Меню отчетов и аналитики"""
        if not self.current_user or self.current_user.role not in [UserRole.ADMIN, UserRole.LIBRARIAN]:
            print("✗ Недостаточно прав.")
            return

        print("\n" + "=" * 60)
        print("ОТЧЕТЫ И АНАЛИТИКА")
        print("=" * 60)

        print("\nДоступные отчеты:")
        print("1. Отчет по продажам за период")
        print("2. Отчет по популярным изданиям")
        print("3. Отчет по пользовательской активности")
        print("4. Отчет по инвентарю")
        print("5. Статистика по жанрам")
        print("6. Вернуться")

        choice = input("\nВыберите отчет (1-6): ").strip()

        if choice == "1":
            self.sales_report()
        elif choice == "2":
            self.popular_publications_report()
        elif choice == "3":
            self.user_activity_report()
        elif choice == "4":
            self.inventory_report()
        elif choice == "5":
            self.genres_report()

    def sales_report(self):
        """Отчет по продажам за период"""
        print("\nОтчет по продажам за период")

        start_date_str = input("Начальная дата (ГГГГ-ММ-ДД, пусто - за последние 30 дней): ").strip()
        end_date_str = input("Конечная дата (ГГГГ-ММ-ДД, пусто - сегодня): ").strip()

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            else:
                start_date = datetime.now() - timedelta(days=30)

            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            else:
                end_date = datetime.now()

            # Получаем данные
            result = self.session.query(
                func.date(Order.order_date).label('date'),
                func.count(Order.id).label('orders_count'),
                func.sum(Order.total_amount).label('total_revenue'),
                func.sum(func.coalesce(OrderItem.quantity, 0)).label('items_sold')
            ).join(Order.items).filter(
                Order.status.in_([OrderStatus.PAID, OrderStatus.DELIVERED]),
                Order.order_date >= start_date,
                Order.order_date <= end_date
            ).group_by(func.date(Order.order_date)).order_by('date').all()

            if not result:
                print("Нет данных за указанный период.")
                return

            total_orders = sum(row.orders_count for row in result)
            total_revenue = sum(float(row.total_revenue or 0) for row in result)
            total_items = sum(row.items_sold or 0 for row in result)

            print(f"\nОтчет по продажам за период: {start_date.date()} - {end_date.date()}")
            print("=" * 60)
            print(f"Всего заказов: {total_orders}")
            print(f"Общая выручка: {total_revenue:.2f} руб.")
            print(f"Всего товаров продано: {total_items}")
            print(f"Средний чек: {total_revenue / total_orders if total_orders > 0 else 0:.2f} руб.")

            print("\nДетали по дням:")
            print("-" * 60)
            print("Дата        | Заказов | Выручка   | Товаров")
            print("-" * 60)

            for row in result:
                print(
                    f"{row.date} | {row.orders_count:7d} | {float(row.total_revenue or 0):9.2f} | {row.items_sold or 0:7d}")

            # Предложение экспорта
            export = input("\nЭкспортировать отчет? (json/csv/pdf/n): ").strip().lower()
            if export in ['json', 'csv', 'pdf']:
                self.export_report('sales', start_date, end_date, export)

        except ValueError:
            print("✗ Неверный формат даты. Используйте ГГГГ-ММ-ДД.")

    def popular_publications_report(self):
        """Отчет по популярным изданиям"""
        print("\nОтчет по популярным изданиям")

        limit = input("Количество изданий для отчета (по умолчанию 10): ").strip()
        limit = int(limit) if limit.isdigit() else 10

        # Издания с наибольшим количеством продаж
        result = self.session.query(
            Publication.id,
            Publication.title,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_revenue'),
            func.avg(Review.rating).label('avg_rating')
        ).join(OrderItem).outerjoin(Review).group_by(Publication.id) \
            .order_by(desc('total_sold')).limit(limit).all()

        if not result:
            print("Нет данных о продажах.")
            return

        print(f"\nТоп-{limit} самых популярных изданий:")
        print("=" * 80)
        print("Название                          | Продано | Выручка   | Рейтинг")
        print("-" * 80)

        for row in result:
            title = row.title[:30] + '...' if len(row.title) > 30 else row.title.ljust(30)
            sold = row.total_sold or 0
            revenue = float(row.total_revenue or 0)
            rating = f"{row.avg_rating:.1f}" if row.avg_rating else "0.0"

            print(f"{title} | {sold:7d} | {revenue:9.2f} | {rating:>7}")

    def user_activity_report(self):
        """Отчет по пользовательской активности"""
        print("\nОтчет по пользовательской активности")

        limit = input("Количество пользователей для отчета (по умолчанию 10): ").strip()
        limit = int(limit) if limit.isdigit() else 10

        # Самые активные пользователи
        result = self.session.query(
            User.id,
            User.email,
            User.first_name,
            User.last_name,
            func.count(Order.id).label('orders_count'),
            func.sum(Order.total_amount).label('total_spent'),
            func.count(Review.id).label('reviews_count')
        ).outerjoin(Order).outerjoin(Review).group_by(User.id) \
            .order_by(desc('orders_count')).limit(limit).all()

        print(f"\nТоп-{limit} самых активных пользователей:")
        print("=" * 100)
        print("Пользователь                     | Заказов | Потрачено  | Отзывов")
        print("-" * 100)

        for row in result:
            user_info = f"{row.first_name} {row.last_name} ({row.email})"
            user_info = user_info[:35] + '...' if len(user_info) > 35 else user_info.ljust(35)
            orders = row.orders_count or 0
            spent = float(row.total_spent or 0)
            reviews = row.reviews_count or 0

            print(f"{user_info} | {orders:7d} | {spent:10.2f} | {reviews:7d}")

    def inventory_report(self):
        """Отчет по инвентарю"""
        print("\nОтчет по инвентарю")

        # Все публикации с количеством на складе
        publications = self.session.query(Publication).order_by(desc(Publication.stock_quantity)).all()

        if not publications:
            print("Нет данных об инвентаре.")
            return

        total_value = sum(p.price * p.stock_quantity for p in publications)
        low_stock = sum(1 for p in publications if p.stock_quantity < 5)
        out_of_stock = sum(1 for p in publications if p.stock_quantity == 0)

        print(f"\nОбщая статистика по инвентарю:")
        print(f"Всего изданий: {len(publications)}")
        print(f"Общая стоимость запасов: {total_value:.2f} руб.")
        print(f"Издания с низким запасом (<5): {low_stock}")
        print(f"Издания отсутствуют на складе: {out_of_stock}")

        print(f"\nИздания с низким запасом:")
        for pub in publications:
            if pub.stock_quantity < 5:
                status = "НЕТ В НАЛИЧИИ" if pub.stock_quantity == 0 else f"мало ({pub.stock_quantity} шт.)"
                print(f"  - {pub.title}: {status}")

    def genres_report(self):
        """Отчет по жанрам"""
        print("\nОтчет по жанрам")

        # Статистика по жанрам
        result = self.session.query(
            Genre.name,
            func.count(Publication.id).label('publications_count'),
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_revenue')
        ).join(publication_genres).join(Publication).outerjoin(OrderItem).group_by(Genre.id) \
            .order_by(desc('total_revenue')).all()

        if not result:
            print("Нет данных по жанрам.")
            return

        print(f"\nСтатистика по жанрам:")
        print("=" * 60)
        print("Жанр            | Изданий | Продано | Выручка")
        print("-" * 60)

        for row in result:
            genre_name = row.name[:15].ljust(15)
            publications = row.publications_count or 0
            sold = row.total_sold or 0
            revenue = float(row.total_revenue or 0)

            print(f"{genre_name} | {publications:7d} | {sold:7d} | {revenue:8.2f}")

    def export_report(self, report_type, start_date, end_date, format_type):
        """Экспорт отчета"""
        if format_type == 'json':
            exporter = JSONExporter()
            file_path = exporter.export_sales_report(self.session, start_date, end_date)
            print(f"✓ Отчет экспортирован в JSON: {file_path}")

        elif format_type == 'csv':
            exporter = CSVExporter()
            file_path = exporter.export_orders_detailed(self.session, start_date, end_date)
            print(f"✓ Отчет экспортирован в CSV: {file_path}")

        elif format_type == 'pdf':
            # Сначала получаем данные для PDF
            result = self.session.query(
                func.date(Order.order_date).label('date'),
                func.count(Order.id).label('orders_count'),
                func.sum(Order.total_amount).label('total_revenue'),
                func.sum(func.coalesce(OrderItem.quantity, 0)).label('items_sold')
            ).join(Order.items).filter(
                Order.status.in_([OrderStatus.PAID, OrderStatus.DELIVERED]),
                Order.order_date >= start_date,
                Order.order_date <= end_date
            ).group_by(func.date(Order.order_date)).order_by('date').all()

            data = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_orders': sum(row.orders_count for row in result),
                    'total_revenue': sum(float(row.total_revenue or 0) for row in result),
                    'average_order_value': 0
                },
                'daily_data': []
            }

            if data['summary']['total_orders'] > 0:
                data['summary']['average_order_value'] = data['summary']['total_revenue'] / data['summary'][
                    'total_orders']

            for row in result:
                data['daily_data'].append({
                    'date': row.date.isoformat(),
                    'orders_count': row.orders_count,
                    'total_revenue': float(row.total_revenue or 0),
                    'items_sold': row.items_sold or 0
                })

            exporter = PDFExporter()
            file_path = exporter.export_sales_report_pdf(data)
            print(f"✓ Отчет экспортирован в PDF: {file_path}")

    def export_menu(self):
        """Меню экспорта данных"""
        if not self.current_user or self.current_user.role not in [UserRole.ADMIN, UserRole.LIBRARIAN]:
            print("✗ Недостаточно прав.")
            return

        print("\n" + "=" * 60)
        print("ЭКСПОРТ ДАННЫХ")
        print("=" * 60)

        print("\nДоступные форматы экспорта:")
        print("1. JSON")
        print("2. CSV")
        print("3. PDF")
        print("4. Вернуться")

        format_choice = input("\nВыберите формат (1-3): ").strip()

        if format_choice not in ['1', '2', '3']:
            return

        print("\nЧто экспортировать:")
        print("1. Пользователей")
        print("2. Публикации")
        print("3. Заказы")
        print("4. Отзывы")
        print("5. Полный отчет по продажам")

        data_choice = input("\nВыберите данные (1-5): ").strip()

        formats = {'1': 'json', '2': 'csv', '3': 'pdf'}
        format_type = formats.get(format_choice)

        try:
            if data_choice == "1":
                if format_type == 'json':
                    file_path = JSONExporter.export_users(self.session)
                elif format_type == 'csv':
                    file_path = CSVExporter.export_to_csv(self.session, User)
                else:
                    print("✗ Экспорт пользователей в PDF не реализован.")
                    return

            elif data_choice == "2":
                if format_type == 'json':
                    file_path = JSONExporter.export_publications(self.session)
                elif format_type == 'csv':
                    file_path = CSVExporter.export_publications_with_stats(self.session)
                else:
                    # Для PDF нужны данные
                    publications = self.session.query(Publication).all()
                    pub_data = []
                    for pub in publications:
                        pub_data.append({
                            'title': pub.title,
                            'isbn': pub.isbn,
                            'price': pub.price,
                            'stock_quantity': pub.stock_quantity
                        })
                    file_path = PDFExporter.export_inventory_report_pdf(pub_data)

            elif data_choice == "3":
                start_date = input("Начальная дата (ГГГГ-ММ-ДД, пусто - без ограничения): ").strip()
                end_date = input("Конечная дата (ГГГГ-ММ-ДД, пусто - без ограничения): ").strip()

                start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
                end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

                if format_type == 'json':
                    file_path = JSONExporter.export_orders(self.session, start, end)
                elif format_type == 'csv':
                    file_path = CSVExporter.export_orders_detailed(self.session, start, end)
                else:
                    print("✗ Экспорт заказов в PDF не реализован.")
                    return

            elif data_choice == "5":
                start_date = input("Начальная дата (ГГГГ-ММ-ДД): ").strip()
                end_date = input("Конечная дата (ГГГГ-ММ-ДД): ").strip()

                if not start_date or not end_date:
                    print("✗ Для отчета по продажам нужны даты начала и конца.")
                    return

                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")

                if format_type == 'json':
                    file_path = JSONExporter.export_sales_report(self.session, start, end)
                elif format_type == 'csv':
                    # Используем детализированный экспорт заказов как отчет по продажам
                    file_path = CSVExporter.export_orders_detailed(self.session, start, end)
                else:
                    # Для PDF
                    self.export_report('sales', start, end, 'pdf')
                    return

            else:
                print("✗ Экспорт выбранных данных не реализован.")
                return

            print(f"✓ Данные успешно экспортированы в {format_type.upper()}: {file_path}")

        except Exception as e:
            print(f"✗ Ошибка при экспорте данных: {str(e)}")

    def export_catalog_public(self):
        """Экспорт каталога для неавторизованных пользователей"""
        print("\n" + "=" * 60)
        print("ЭКСПОРТ КАТАЛОГА")
        print("=" * 60)

        print("\nДоступные форматы:")
        print("1. JSON")
        print("2. CSV")

        choice = input("\nВыберите формат (1-2): ").strip()

        if choice == "1":
            try:
                file_path = JSONExporter.export_publications(self.session)
                print(f"✓ Каталог экспортирован в JSON: {file_path}")
            except Exception as e:
                print(f"✗ Ошибка при экспорте: {str(e)}")

        elif choice == "2":
            try:
                file_path = CSVExporter.export_publications_with_stats(self.session)
                print(f"✓ Каталог экспортирован в CSV: {file_path}")
            except Exception as e:
                print(f"✗ Ошибка при экспорте: {str(e)}")

    def backup_menu(self):
        """Меню резервного копирования"""
        if not self.current_user or self.current_user.role != UserRole.ADMIN:
            print("✗ Недостаточно прав.")
            return

        print("\n" + "=" * 60)
        print("РЕЗЕРВНОЕ КОПИРОВАНИЕ")
        print("=" * 60)

        print("\nДействия:")
        print("1. Создать резервную копию")
        print("2. Загрузить копию на удаленный сервер")
        print("3. Просмотреть список резервных копий")
        print("4. Восстановить из резервной копии")
        print("5. Очистить старые копии")
        print("6. Вернуться")

        choice = input("\nВыберите действие (1-6): ").strip()

        if choice == "1":
            success, message = self.backup_manager.create_backup()
            if success:
                print(f"✓ {message}")
            else:
                print(f"✗ {message}")

        elif choice == "2":
            # Показать доступные резервные копии
            backups = self.backup_manager.list_backups()
            if not backups:
                print("Нет резервных копий для загрузки.")
                return

            print("\nДоступные резервные копии:")
            for i, backup in enumerate(backups[:5], 1):
                print(f"{i}. {backup['name']} ({backup['created'].strftime('%d.%m.%Y %H:%M')})")

            backup_num = input("\nВыберите копию для загрузки (1-5): ").strip()
            if backup_num.isdigit() and 1 <= int(backup_num) <= min(5, len(backups)):
                backup_path = backups[int(backup_num) - 1]['path']

                # Параметры подключения
                print("\nПараметры подключения к удаленному серверу:")
                host = input("Хост (оставьте пустым для значений из конфига): ").strip()
                username = input("Имя пользователя: ").strip()
                password = input("Пароль: ").strip()
                remote_path = input("Путь на удаленном сервере: ").strip()

                success, message = self.backup_manager.upload_to_remote(
                    backup_path,
                    host if host else None,
                    username if username else None,
                    password if password else None,
                    remote_path if remote_path else None
                )

                if success:
                    print(f"✓ {message}")
                else:
                    print(f"✗ {message}")

        elif choice == "3":
            backups = self.backup_manager.list_backups()
            if not backups:
                print("Нет резервных копий.")
                return

            print(f"\nВсего резервных копий: {len(backups)}")
            for backup in backups[:10]:
                size_mb = backup['size'] / (1024 * 1024)
                print(f"\n{backup['name']}")
                print(f"  Дата создания: {backup['created'].strftime('%d.%m.%Y %H:%M:%S')}")
                print(f"  Размер: {size_mb:.2f} MB")
                print(f"  Путь: {backup['path']}")

        elif choice == "4":
            backups = self.backup_manager.list_backups()
            if not backups:
                print("Нет резервных копий для восстановления.")
                return

            print("\nДоступные резервные копии:")
            for i, backup in enumerate(backups[:5], 1):
                print(f"{i}. {backup['name']} ({backup['created'].strftime('%d.%m.%Y %H:%M')})")

            backup_num = input("\nВыберите копию для восстановления (1-5): ").strip()
            if backup_num.isdigit() and 1 <= int(backup_num) <= min(5, len(backups)):
                backup_path = backups[int(backup_num) - 1]['path']

                confirm = input(
                    f"\nВы уверены, что хотите восстановить базу данных из {backup_path}? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Закрываем текущую сессию
                    self.session.close()

                    success, message = self.backup_manager.restore_backup(backup_path)
                    if success:
                        print(f"✓ {message}")
                        # Перезапускаем сессию
                        self.session = self.db_manager.get_session()
                    else:
                        print(f"✗ {message}")
                        # Пытаемся переоткрыть сессию
                        self.session = self.db_manager.get_session()

        elif choice == "5":
            days = input("Удалить копии старше скольки дней? (по умолчанию 30): ").strip()
            days = int(days) if days.isdigit() else 30

            confirm = input(f"Удалить резервные копии старше {days} дней? (y/n): ").strip().lower()
            if confirm == 'y':
                success, message = self.backup_manager.cleanup_old_backups(days)
                if success:
                    print(f"✓ {message}")
                else:
                    print(f"✗ {message}")


def main():
    """Точка входа в приложение"""
    app = ElectronicLibraryApp()
    app.run()


if __name__ == "__main__":
    main()