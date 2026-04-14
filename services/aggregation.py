import pandas as pd
from models.sale import Sale
from models.analytics import SummaryMetrics
from typing import List
import math


def calculate_summary(sales: List[Sale]) -> SummaryMetrics:
    """
    Рассчитывает агрегированные метрики из списка продаж.
    1. Проверка на пустые данные
    2. Превращаем список Sale в DataFrame
    3. Фильтруем только доставленные заказы
    4. Добавляем вычисляемые колонки
    5. Считаем базовые метрики
    6. Считаем производные метрики
    7. Считаем долю возвратов
    8. Возвращаем результат в виде объекта SummaryMetrics с метриками

    Args:
        sales: Список объектов Sale из storage.get_sales()

    Returns:
        SummaryMetrics: Объект со всеми метриками
    """

    # ========== ШАГ 1: Проверка на пустые данные ==========
    if not sales:
        # Если продаж нет - все метрики равны нулю
        return SummaryMetrics(
            total_revenue=0.0,
            total_cost=0.0,
            gross_profit=0.0,
            margin_percent=0.0,
            total_orders=0,
            avg_order_value=0.0,
            return_rate=0.0,
        )

    # ========== ШАГ 2: Превращаем список Sale в DataFrame ==========
    df = pd.DataFrame([s.model_dump() for s in sales])
    # s.model_dump() - превращает Pydantic модель в словарь
    # pd.DataFrame() - создает таблицу из списка словарей

    # 1: Sale(order_id="ORD-001", marketplace="ozon", price=450, ...) ->
    # 2: {"order_id": "ORD-001", "marketplace": "ozon", "price": 450, ...}
    # 3: [Sale(...), Sale(...), Sale(...)] ->
    # 4: [{...}, {...}, {...}] и вот из этого получаем таблицу для пандаса df
    # 5: Пример того, как выглядит df:

    # +----------+----------------+----------------+----------+--------+------------+------------+------------+
    # | order_id | marketplace    | product_name   | quantity | price  | cost_price | status     | sold_at    |
    # +----------+----------------+----------------+----------+--------+------------+------------+------------+
    # | ORD-001  | ozon           | Кабель USB-C   | 3        | 450.0  | 120.0      | delivered  | 2025-03-01 |
    # | ORD-002  | wildberries    | Чехол iPhone   | 1        | 1200.0 | 350.0      | delivered  | 2025-03-01 |
    # | ORD-003  | ozon           | Наушники TWS   | 2        | 2500.0 | 800.0      | delivered  | 2025-03-02 |
    # | ORD-004  | yandex_market  | Зарядка 65W    | 1        | 1800.0 | 600.0      | returned   | 2025-03-02 |
    # +----------+----------------+----------------+----------+--------+------------+------------+------------+

    # ========== ШАГ 3: Фильтруем только доставленные заказы ==========
    # Только они приносят выручку
    delivered_df = df[df["status"] == "delivered"].copy()

    # ========== ШАГ 4: Добавляем вычисляемые колонки ==========
    # Векторизованные операции - Pandas применяет формулу ко всем строкам сразу
    # Это работает на C, поэтому очень быстро

    # Выручка = цена × количество
    delivered_df["revenue"] = delivered_df["price"] * delivered_df["quantity"]

    # Себестоимость = себестоимость_единицы × количество
    delivered_df["cost"] = (
        delivered_df["cost_price"] * delivered_df["quantity"]
    )

    # Прибыль = выручка - себестоимость
    delivered_df["profit"] = delivered_df["revenue"] - delivered_df["cost"]

    # Теперь df выглядит так (добавились колонки):
    # | # | order_id | price   | quantity | revenue | cost    | profit  |
    # |---|----------|---------|----------|---------|---------|---------|
    # | 0 | ORD-001  | 450.0   | 3        | 1350.0  | 360.0   | 990.0   |
    # | 1 | ORD-002  | 1200.0  | 1        | 1200.0  | 350.0   | 850.0   |
    # | 2 | ORD-003  | 2500.0  | 2        | 5000.0  | 1600.0  | 3400.0  |

    # ========== ШАГ 5: Считаем базовые метрики ==========
    # sum() - суммирует все значения в колонке
    total_revenue = (
        delivered_df["revenue"].sum() if not delivered_df.empty else 0
    )
    total_cost = delivered_df["cost"].sum() if not delivered_df.empty else 0
    gross_profit = total_revenue - total_cost

    # Количество уникальных заказов
    # nunique() - количество уникальных значений в колонке
    total_orders = (
        delivered_df["order_id"].nunique() if not delivered_df.empty else 0
    )

    # ========== ШАГ 6: Считаем производные метрики ==========
    # Маржинальность = (прибыль / выручка) × 100%
    if total_revenue > 0:
        margin_percent = (gross_profit / total_revenue) * 100
    else:
        margin_percent = 0.0

    # Средний чек = выручка / количество заказов
    if total_orders > 0:
        avg_order_value = total_revenue / total_orders
    else:
        avg_order_value = 0.0

    # ========== ШАГ 7: Считаем долю возвратов ==========
    returned_count = len(df[df["status"] == "returned"])
    delivered_count = len(delivered_df)

    total_delivered_and_returned = delivered_count + returned_count
    if total_delivered_and_returned > 0:
        raw_rate = (returned_count / total_delivered_and_returned) * 100
        # Защита от некорректных значений (NaN, inf, больше 100)
        if pd.isna(raw_rate) or math.isinf(raw_rate):
            return_rate = 0.0
        else:
            return_rate = min(raw_rate, 100.0)
    else:
        return_rate = 0.0

    # ========== ШАГ 8: Возвращаем результат ==========
    # Округляем все числа до 2 знаков
    return SummaryMetrics(
        total_revenue=round(total_revenue, 2),
        total_cost=round(total_cost, 2),
        gross_profit=round(gross_profit, 2),
        margin_percent=round(margin_percent, 2),
        total_orders=total_orders,
        avg_order_value=round(avg_order_value, 2),
        return_rate=round(return_rate, 2),
    )


def calculate_top_products(
    sales: List[Sale], sort_by: str = "revenue", limit: int = 10
) -> List[dict]:
    """
    Рассчитывает топ продуктов по заданному критерию.

    Алгоритм работы с Pandas:
        1. Превращаем список Sale в DataFrame
        2. Фильтруем только delivered заказы
        3. Добавляем колонки revenue, profit
        4. Группируем по product_name и суммируем
        5. Сортируем и ограничиваем количество

    Args:
        sales: Список объектов Sale из storage.get_sales()
        sort_by: Критерий сортировки ("revenue", "quantity", "profit")
        limit: Сколько продуктов вернуть (по умолчанию 10)

    Returns:
        List[dict]: Список словарей с полями:
            - product_name: название продукта
            - revenue: общая выручка
            - quantity: общее количество
            - profit: общая прибыль
    """

    # ========== ШАГ 1: Проверка на пустые данные ==========
    if not sales:
        return []

    # ========== ШАГ 2: Создаем DataFrame только из доставленных заказов ==========
    # List comprehension сразу фильтрует по status
    delivered_sales = [s for s in sales if s.status == "delivered"]

    if not delivered_sales:
        return []

    df = pd.DataFrame([s.model_dump() for s in delivered_sales])
    # s.model_dump() - превращает Pydantic модель в словарь
    # pd.DataFrame() - создает таблицу из списка словарей

    # 1: Sale(order_id="ORD-001", marketplace="ozon", price=450, ...) ->
    # 2: {"order_id": "ORD-001", "marketplace": "ozon", "price": 450, ...}
    # 3: [Sale(...), Sale(...), Sale(...)] ->
    # 4: [{...}, {...}, {...}] и вот из этого получаем таблицу для пандаса df
    # 5: Пример того, как выглядит df:

    # +----------+----------------+----------------+----------+--------+------------+------------+------------+
    # | order_id | marketplace    | product_name   | quantity | price  | cost_price | status     | sold_at    |
    # +----------+----------------+----------------+----------+--------+------------+------------+------------+
    # | ORD-001  | ozon           | Кабель USB-C   | 3        | 450.0  | 120.0      | delivered  | 2025-03-01 |
    # | ORD-002  | wildberries    | Чехол iPhone   | 1        | 1200.0 | 350.0      | delivered  | 2025-03-01 |
    # | ORD-003  | ozon           | Наушники TWS   | 2        | 2500.0 | 800.0      | delivered  | 2025-03-02 |
    # +----------+----------------+----------------+----------+--------+------------+------------+------------+

    # ========== ШАГ 3: Добавляем вычисляемые колонки ==========
    # Выручка = цена × количество
    df["revenue"] = df["price"] * df["quantity"]

    # Прибыль = (цена - себестоимость) × количество
    df["profit"] = (df["price"] - df["cost_price"]) * df["quantity"]

    # ========== ШАГ 4: Группировка по названию продукта ==========
    # groupby() - группирует строки с одинаковым product_name
    # agg() - применяет агрегацию (суммирует revenue, quantity, profit)
    # reset_index() - превращает product_name из индекса обратно в колонку
    grouped = (
        df.groupby("product_name")
        .agg(
            {
                "revenue": "sum",  # Суммируем выручку по каждому продукту
                "quantity": "sum",  # Суммируем количество по каждому продукту
                "profit": "sum",  # Суммируем прибыль по каждому продукту
            }
        )
        .reset_index()
    )

    # Пример того, как выглядит grouped:
    #   product_name      revenue  quantity  profit
    # 0 Кабель USB-C       3150.0         7    2310.0
    # 1 Наушники TWS       5000.0         2    3400.0
    # 2 Чехол для iPhone   1200.0         1     850.0

    # ========== ШАГ 5: Сортировка ==========
    # sort_values() - сортирует по указанной колонке
    # ascending=False - по убыванию (от большего к меньшему)
    # head(limit) - берет первые N записей
    allowed_cols = ["revenue", "quantity", "profit"]

    if sort_by not in allowed_cols:
        sort_by = "revenue"  # значение по умолчанию

    grouped = grouped.sort_values(sort_by, ascending=False).head(limit)

    # ========== ШАГ 6: Преобразуем в список словарей ==========

    # Округляем числа
    grouped[["revenue", "profit"]] = grouped[["revenue", "profit"]].round(2)

    # to_dict("records") - превращает DataFrame в список словарей
    # Пример: [{"product_name": "...", "revenue": ..., "quantity": ..., "profit": ...}, ...]
    result = grouped.to_dict("records")
    return result
