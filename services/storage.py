"""
Хранение данных о продажах в SQLite.
Данные сохраняются в файл и не теряются при перезапуске сервера.
"""

import sqlite3
from models.sale import Sale
from typing import List
from datetime import date
import os

# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
# Путь к файлу базы данных
DB_PATH = "sales.db"


def get_db_connection():
    """
    Создает и возвращает соединение с базой данных.

    Returns:
        sqlite3.Connection: Соединение с БД
    """
    conn = sqlite3.connect(DB_PATH)
    # Разрешаем доступ к колонкам по имени (для удобства)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """
    Инициализирует базу данных: создает таблицу, если её нет.
    Вызывается один раз при запуске приложения.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Создаем таблицу sales, если она ещё не существует
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS sales (     -- создать таблицу если её нет
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- авто-увеличивающийся ID
                order_id TEXT NOT NULL,                -- строка, обязательное поле
                marketplace TEXT NOT NULL,             -- строка, обязательное поле
                product_name TEXT NOT NULL,            -- строка, обязательное поле
                quantity INTEGER NOT NULL,             -- целое число, обязательное
                price REAL NOT NULL,                   -- дробное число, обязательное
                cost_price REAL NOT NULL,              -- дробное число, обязательное
                status TEXT NOT NULL,                  -- строка, обязательное
                sold_at TEXT NOT NULL,                 -- строка (дата хранится как текст)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- автоматическая дата
            )
    """
    )

    conn.commit()
    conn.close()


# ========== ОСНОВНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ==========


def add_sales(sales: List[Sale]) -> int:
    """
    Добавляет список продаж в базу данных.

    Args:
        sales: Список объектов Sale для добавления

    Returns:
        int: Количество добавленных записей

    Example:
        >>> sales = [Sale(...), Sale(...)]
        >>> count = add_sales(sales)
        >>> print(count)  # 2
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    count = 0
    for sale in sales:
        # Вставляем каждую продажу в таблицу
        cursor.execute(
            """
            INSERT INTO sales (
                order_id, marketplace, product_name,
                quantity, price, cost_price, status, sold_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                sale.order_id,
                sale.marketplace,
                sale.product_name,
                sale.quantity,
                sale.price,
                sale.cost_price,
                sale.status,
                # Преобразуем date в строку YYYY-MM-DD
                sale.sold_at.isoformat(),
            ),
        )
        count += 1

    conn.commit()
    conn.close()
    return count


def get_sales(
    marketplace: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> List[Sale]:
    """
    Возвращает список продаж с фильтрацией.
    Все параметры опциональные, если не указаны,
    то фильтр не применяется.

    Args:
        marketplace: Фильтр по маркетплейсу (ozon, wildberries, yandex_market)
        status: Фильтр по статусу (delivered, returned, cancelled)
        date_from: Начальная дата (включительно)
        date_to: Конечная дата (включительно)

    Returns:
        List[Sale]: Отфильтрованный список продаж (Pydantic модели)

    Example:
        >>> # Все продажи ozon за март 2025
        >>> sales = get_sales(
        ...     marketplace="ozon",
        ...     date_from=date(2025, 3, 1),
        ...     date_to=date(2025, 3, 31)
        ... )
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # ========== СТРОИМ SQL ЗАПРОС С ФИЛЬТРАМИ ==========
    # Начинаем с базового запроса
    # 1=1 значит "все строки" (удобно для добавления первого AND)
    # Это «техническая заглушка», которая всегда правдива
    # (ведь 1 всегда равно 1). Это избавляет от лишних проверок типа
    # if query.endswith("WHERE"): ... else: query += " AND".
    query = "SELECT * FROM sales WHERE 1=1"
    params = []

    # Добавляем фильтры по одному, если они указаны

    if marketplace:
        query += " AND marketplace = ?"
        params.append(marketplace)

    if status:
        query += " AND status = ?"
        params.append(status)

    if date_from:
        query += " AND sold_at >= ?"
        params.append(date_from.isoformat())

    if date_to:
        query += " AND sold_at <= ?"
        params.append(date_to.isoformat())

    # Сортируем по дате продажи (новые сверху)
    query += " ORDER BY sold_at DESC"

    # Выполняем запрос с параметрами из списка params
    cursor.execute(query, params)
    # команда базе данных передать все найденные строки в память Python
    # превращает в список кортежей
    rows = cursor.fetchall()
    conn.close()

    # ========== ПРЕОБРАЗУЕМ РЕЗУЛЬТАТ В СПИСОК МОДЕЛЕЙ SALE ==========
    sales_list = []
    for row in rows:
        # Создаем объект Sale из данных строки
        sale = Sale(
            order_id=row["order_id"],
            marketplace=row["marketplace"],
            product_name=row["product_name"],
            quantity=row["quantity"],
            price=row["price"],
            cost_price=row["cost_price"],
            status=row["status"],
            sold_at=date.fromisoformat(
                row["sold_at"]
            ),  # Преобразуем строку обратно в объект date
        )
        sales_list.append(sale)

    return sales_list


def get_sales_count(
    marketplace: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> int:
    """
    Возвращает количество продаж с фильтрацией (без загрузки всех данных).

    Args:
        marketplace: Фильтр по маркетплейсу
        status: Фильтр по статусу
        date_from: Начальная дата
        date_to: Конечная дата

    Returns:
        int: Количество продаж, подходящих под фильтры
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT COUNT(*) as cnt FROM sales WHERE 1=1"
    params = []

    if marketplace:
        query += " AND marketplace = ?"
        params.append(marketplace)

    if status:
        query += " AND status = ?"
        params.append(status)

    if date_from:
        query += " AND sold_at >= ?"
        params.append(date_from.isoformat())

    if date_to:
        query += " AND sold_at <= ?"
        params.append(date_to.isoformat())

    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()

    return result["cnt"] if result else 0


def get_sales_with_pagination(
    marketplace: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> List[Sale]:
    """
    Возвращает список продаж с фильтрацией и пагинацией.

    Args:
        marketplace: Фильтр по маркетплейсу
        status: Фильтр по статусу
        date_from: Начальная дата
        date_to: Конечная дата
        page: Номер страницы (начиная с 1)
        page_size: Размер страницы

    Returns:
        List[Sale]: Отфильтрованный список продаж для указанной страницы
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Строим запрос с фильтрами
    query = "SELECT * FROM sales WHERE 1=1"
    params = []

    if marketplace:
        query += " AND marketplace = ?"
        params.append(marketplace)

    if status:
        query += " AND status = ?"
        params.append(status)

    if date_from:
        query += " AND sold_at >= ?"
        params.append(date_from.isoformat())

    if date_to:
        query += " AND sold_at <= ?"
        params.append(date_to.isoformat())

    # Сортировка и пагинация
    query += " ORDER BY sold_at DESC"
    query += " LIMIT ? OFFSET ?"

    offset = (page - 1) * page_size
    params.extend([page_size, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # Преобразуем в список моделей Sale
    sales_list = []
    for row in rows:
        sale = Sale(
            order_id=row["order_id"],
            marketplace=row["marketplace"],
            product_name=row["product_name"],
            quantity=row["quantity"],
            price=row["price"],
            cost_price=row["cost_price"],
            status=row["status"],
            sold_at=date.fromisoformat(row["sold_at"]),
        )
        sales_list.append(sale)

    return sales_list


def clear_storage() -> None:
    """
    Очищает все данные из базы данных.
    Используется для тестов.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sales")
    conn.commit()
    conn.close()


def delete_database() -> None:
    """
    Полностью удаляет файл базы данных.
    Используется для полного сброса данных.
    """
    conn = get_db_connection()
    conn.close()

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


# ========== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ПРИ ЗАГРУЗКЕ ==========
# Эта функция вызывается один раз при первом импорте модуля
init_database()
