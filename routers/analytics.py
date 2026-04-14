"""
Роутер для аналитики.
Все URL начинаются с /analytics
Обрабатывает:
- GET /analytics/summary - основные метрики
- GET /analytics/top-products - топ продуктов
- GET /analytics/summary-usd - метрики в долларах
- POST /analytics/upload-csv - загрузка продаж из CSV
"""

from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from models.analytics import SummaryMetrics
from models.sale import Sale
from services.storage import add_sales, get_sales
from services.aggregation import calculate_summary, calculate_top_products
from services.currency import get_usd_rate
from typing import List
from datetime import date
import pandas as pd
from io import StringIO

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryMetrics)
async def get_summary(
    # ...,Ellipsis (многоточие)	ОБЯЗАТЕЛЬНЫЙ параметр
    date_from: date = Query(
        ..., description="Начальная дата периода (YYYY-MM-DD)"
    ),
    date_to: date = Query(
        ..., description="Конечная дата периода (YYYY-MM-DD)"
    ),
    marketplace: str | None = Query(
        None,
        description="Фильтр по маркетплейсу (ozon, wildberries, yandex_market)",
    ),
) -> SummaryMetrics:
    """
    GET /analytics/summary
    Агрегированные метрики за период.

    date_from и date_to - обязательные параметры.
    marketplace - опциональный фильтр.

    Пример запроса:
    /analytics/summary?date_from=2025-03-01&date_to=2025-03-31&marketplace=ozon

    Пример ответа:
    {
        "total_revenue": 125000.50,
        "total_cost": 35000.25,
        "gross_profit": 90000.25,
        "margin_percent": 72.0,
        "total_orders": 42,
        "avg_order_value": 2976.20,
        "return_rate": 8.5
    }
    """

    # ========== ШАГ 1: Получаем данные из БД ==========
    # Здесь вызывается storage.get_sales()
    # Возвращает список объектов Sale
    # sales = [Sale(...), Sale(...), ...]
    sales = get_sales(
        marketplace=marketplace,
        date_from=date_from,
        date_to=date_to,
    )

    # ========== ШАГ 2: Считаем метрики и возвращаем метрики в json ==========
    # Здесь вызывается aggregation.calculate_summary()
    # Передаем список продаж, получаем метрики
    # metrics = SummaryMetrics(total_revenue=125000.50, ...)
    metrics = calculate_summary(sales)
    return metrics


@router.get("/top-products")
async def get_top_products(
    date_from: date = Query(
        ..., description="Начальная дата периода (YYYY-MM-DD)"
    ),
    date_to: date = Query(
        ..., description="Конечная дата периода (YYYY-MM-DD)"
    ),
    sort_by: str = Query(
        "revenue",
        # уууу. вот они и регулярки
        regex="^(revenue|quantity|profit)$",
        description="Критерий сортировки: revenue, quantity, profit",
    ),
    limit: int = Query(
        10, ge=1, le=50, description="Количество продуктов (макс 50)"
    ),
) -> List[dict]:
    """
    GET /analytics/top-products
    Топ продуктов за период.

    date_from и date_to - обязательные параметры.
    sort_by - по какому критерию сортировать.
    limit - сколько продуктов вернуть.

    Пример запроса:
    /analytics/top-products?date_from=2025-03-01&date_to=2025-03-31&sort_by=revenue&limit=5

    Ответ
    [
        {"product_name": "Кабель USB-C", "revenue": 12500.50, "quantity": 42, "profit": 8750.25},
        {"product_name": "Наушники TWS", "revenue": 10200.00, "quantity": 15, "profit": 7200.00},
        {"product_name": "Чехол для iPhone", "revenue": 8900.00, "quantity": 8, "profit": 6200.00},
        {"product_name": "Зарядка 65W", "revenue": 7500.00, "quantity": 10, "profit": 5100.00},
        {"product_name": "Подставка для ноутбука", "revenue": 6200.00, "quantity": 5, "profit": 4300.00}
    ]
    """

    # ========== ШАГ 1: Получаем данные из БД ==========
    sales = get_sales(
        date_from=date_from,
        date_to=date_to,
    )

    # ========== ШАГ 2: Считаем топ продуктов и возвращаем ==========
    # Здесь вызывается aggregation.calculate_top_products()
    # top_products = [{"product_name": "...", "revenue": ..., ...}, ...]
    top_products = calculate_top_products(sales, sort_by, limit)
    return top_products


@router.get("/summary-usd")
async def get_summary_usd(
    date_from: date = Query(
        ..., description="Начальная дата периода (YYYY-MM-DD)"
    ),
    date_to: date = Query(
        ..., description="Конечная дата периода (YYYY-MM-DD)"
    ),
    marketplace: str | None = Query(
        None, description="Фильтр по маркетплейсу"
    ),
) -> dict:
    """
    GET /analytics/summary-usd
    Агрегированные метрики за период в USD.

    Работает как /analytics/summary, но все денежные метрики конвертированы в USD.
    Курс берется из API ЦБ РФ и кэшируется на 1 час.

    Пример ответа:
    {
        "total_revenue": 1351.35,
        "total_cost": 378.38,
        "gross_profit": 972.97,
        "margin_percent": 72.0,
        "total_orders": 42,
        "avg_order_value": 32.17,
        "return_rate": 8.5,
        "usd_rate": 92.50
    }
    """

    # ========== ШАГ 1: Получаем курс USD ==========
    try:
        usd_rate = await get_usd_rate()
    except Exception:
        raise HTTPException(status_code=503, detail="Currency API unavailable")

    # ========== ШАГ 2: Получаем метрики в рублях ==========
    # Переиспользуем функцию get_summary (которая уже делает всё нужное)
    rub_metrics = await get_summary(date_from, date_to, marketplace)

    # ========== ШАГ 3: Конвертируем в USD ==========
    return {
        "total_revenue": round(rub_metrics.total_revenue / usd_rate, 2),
        "total_cost": round(rub_metrics.total_cost / usd_rate, 2),
        "gross_profit": round(rub_metrics.gross_profit / usd_rate, 2),
        "margin_percent": rub_metrics.margin_percent,  # Процент не меняется
        "total_orders": rub_metrics.total_orders,  # Количество не меняется
        "avg_order_value": round(rub_metrics.avg_order_value / usd_rate, 2),
        "return_rate": rub_metrics.return_rate,  # Процент не меняется
        "usd_rate": round(usd_rate, 2),  # Добавляем курс в ответ
    }


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(..., description="CSV файл с данными о продажах")
) -> dict:
    """
    POST /analytics/upload-csv
    Загрузка продаж из CSV-файла.

    Принимает CSV файл со столбцами:
    - order_id: номер заказа
    - marketplace: ozon, wildberries, yandex_market
    - product_name: название продукта
    - quantity: количество
    - price: цена за штуку
    - cost_price: себестоимость за штуку
    - status: delivered, returned, cancelled
    - sold_at: дата продажи (YYYY-MM-DD)

    Returns:
        - loaded_count: количество успешно загруженных строк
        - error_count: количество строк с ошибками
        - errors: список ошибок с номерами строк

    Example:
        curl -X POST "http://localhost:8000/analytics/upload-csv" \
             -F "file=@sample_data.csv"

    Example response:
        {
            "loaded_count": 18,
            "error_count": 2,
            "errors": [
                {"row": 5, "error": "price must be > 0"},
                {"row": 12, "error": "sold_at must be a valid date"}
            ]
        }
    """

    # ========== ШАГ 1: Проверяем формат файла ==========
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400, detail="Only CSV files are allowed"
        )

    # ========== ШАГ 2: Читаем CSV файл ==========
    try:
        content = await file.read()
        # Декодируем байты в строку и читаем через pandas
        df = pd.read_csv(StringIO(content.decode('utf-8')))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error reading CSV file: {str(e)}"
        )

    # ========== ШАГ 3: Проверяем наличие обязательных колонок ==========
    required_columns = [
        'order_id',
        'marketplace',
        'product_name',
        'quantity',
        'price',
        'cost_price',
        'status',
        'sold_at',
    ]

    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing columns: {', '.join(missing_columns)}",
        )

    # ========== ШАГ 4: Валидируем каждую строку ==========
    valid_sales = []
    errors = []

    for idx, row in df.iterrows():
        try:
            # Пробуем создать объект Sale (Pydantic сам провалидирует)
            sale = Sale(
                order_id=str(row['order_id']),
                marketplace=row['marketplace'],
                product_name=row['product_name'],
                quantity=int(row['quantity']),
                price=float(row['price']),
                cost_price=float(row['cost_price']),
                status=row['status'],
                sold_at=date.fromisoformat(
                    row['sold_at']
                ),  # преобразуем строку в date
            )
            valid_sales.append(sale)
        except Exception as e:
            # Номер строки +2 потому что:
            # - idx начинается с 0
            # - первая строка (индекс 0) - это заголовки
            # - первая строка данных имеет номер 2 в CSV
            errors.append({"row": idx + 2, "error": str(e)})

    # ========== ШАГ 5: Сохраняем валидные продажи ==========
    loaded_count = 0
    if valid_sales:
        loaded_count = add_sales(valid_sales)

    # ========== ШАГ 6: Возвращаем результат ==========
    return {
        "loaded_count": loaded_count,
        "error_count": len(errors),
        "errors": errors[:20],  # возвращаем не более 20 ошибок
    }
