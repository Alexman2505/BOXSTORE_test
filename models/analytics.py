"""
Модели данных для ответов аналитики.
Описывают, какие данные сервер возвращает клиенту.
"""

from pydantic import BaseModel, Field


class SummaryMetrics(BaseModel):
    """
    Это структура ответа на GET /analytics/summary
    Метрики для одной группы (маркетплейс/дата/статус или общие)
    "Кирпичик" данных. Не хранится в базе, создается на лету.

    В БД хранятся сырые продажи (каждая строка - одна продажа)
    Это то, что приходит в POST /sales
    Когда приходит запрос GET /analytics/summary:
    - Достаем из БД все продажи за период
    - Считаем метрики (суммируем, группируем, вычисляем проценты)
    - Создаем объект SummaryMetrics
    - Отдаем его как JSON по API

     В БД нет колонки "margin_percent" или "total_revenue"
    Эти значения вычисляются "на лету" при каждом запросе
    """

    # ========= Эти 3 метрики вычисляются агрегацией из БД:
    total_revenue: float = Field(
        description="Общая выручка = сумма (price × quantity) для delivered заказов",
        examples=[125000.50],
        ge=0,  # не может быть отрицательной
    )

    total_cost: float = Field(
        description="Общая себестоимость = сумма (cost_price × quantity) для delivered заказов",
        examples=[35000.25],
        ge=0,
    )

    total_orders: int = Field(
        description="Количество уникальных заказов (по order_id) со статусом delivered",
        examples=[42],
        ge=0,
    )
    # ==========  Эти 4 метрики вычисляются из первых трех:
    gross_profit: float = Field(
        description="Валовая прибыль = total_revenue - total_cost",
        examples=[90000.25],
    )

    margin_percent: float = Field(
        description="Маржинальность в процентах = (gross_profit / total_revenue) × 100",
        examples=[72.0],
        ge=0,
        le=100,
    )

    avg_order_value: float = Field(
        description="Средний чек = total_revenue / total_orders",
        examples=[2976.20],
        ge=0,
    )

    return_rate: float = Field(
        description="Доля возвратов в процентах = (returned / (delivered + returned)) × 100",
        examples=[8.5],
        ge=0,
        le=100,
    )
