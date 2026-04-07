"""
Роутер для работы с продажами.
Все URL начинаются с /sales
Обрабатывает:
- POST /sales - добавление продаж
- GET /sales - получение списка с фильтрацией
"""

from fastapi import APIRouter, Query
from models.sale import Sale
from services.storage import (
    add_sales,
    get_sales_with_pagination,
    get_sales_count,
)
from typing import List
from datetime import date

# Создаем роутер. Все пути будут начинаться с /sales
router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/")
async def create_sales(sales: List[Sale]) -> dict:
    """
    POST /sales
    Добавление одной или нескольких продаж.

    Вход: JSON массив объектов Sale
    Выход: количество добавленных записей

    Пример запроса:
    [
        {
            "order_id": "ORD-001",
            "marketplace": "ozon",
            "product_name": "Кабель USB-C",
            "quantity": 3,
            "price": 450.00,
            "cost_price": 120.00,
            "status": "delivered",
            "sold_at": "2025-03-15"
        }
    ]

    Пример ответа:
    {"added_count": 1}
    """
    count = add_sales(sales)
    return {"added_count": count}


@router.get("/")
async def list_sales(
    marketplace: str | None = Query(
        None,
        description="Фильтр по маркетплейсу (ozon, wildberries, yandex_market)",
    ),
    status: str | None = Query(
        None, description="Фильтр по статусу (delivered, returned, cancelled)"
    ),
    date_from: date | None = Query(
        None, description="Начальная дата (YYYY-MM-DD)"
    ),
    date_to: date | None = Query(
        None, description="Конечная дата (YYYY-MM-DD)"
    ),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(
        20, ge=1, le=100, description="Размер страницы (макс 100)"
    ),
) -> dict:
    """
    GET /sales
    Получение списка продаж с фильтрацией и пагинацией.

    Все параметры опциональные.

    Пример запроса:
    /sales?marketplace=ozon&status=delivered&page=1&page_size=10

    Пример ответа:
    {
        "total": 42,
        "page": 1,
        "page_size": 10,
        "sales": [...]
    }
    """
    total = get_sales_count(
        marketplace=marketplace,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )

    sales = get_sales_with_pagination(
        marketplace=marketplace,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "sales": sales,
    }


@router.delete("/clear")
async def clear_all_sales() -> dict:
    """
    DELETE /sales/clear
    Очищает все продажи из базы данных.
    ВНИМАНИЕ: Это действие необратимо!
    """
    from services.storage import clear_storage

    clear_storage()
    return {"message": "All sales have been cleared"}
