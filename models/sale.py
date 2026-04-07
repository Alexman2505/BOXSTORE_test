"""про Pydantic 2 и валидацию полей класса field_validator читать тут
https://habr.com/ru/companies/amvera/articles/851642/
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Literal


class Sale(BaseModel):
    """
    Модель одной продажи с маркетплейса.
    Описывает, какие данные приходят от клиента в POST /sales CSV
    FastAPI автоматически валидирует входящий JSON по этой модели.
    Хранит сырые данные о каждой продаже в базе данных (SQLite)
    -- НЕТ колонок:
    -- total_revenue (это вычисляется)
    -- margin_percent (это вычисляется)
    -- gross_profit (это вычисляется)
    """

    order_id: str = Field(
        title="Номер заказа", description="Уникальный идентификатор заказа"
    )
    marketplace: Literal["ozon", "wildberries", "yandex_market"] = Field(
        title="Маркетплейс", description="Название площадки"
    )
    product_name: str = Field(title="Товар", description="Название продукта")
    quantity: int = Field(
        title="Количество", description="Количество единиц товара"
    )
    price: float = Field(
        title="Цена за шт., руб.", description="Цена продажи за единицу"
    )
    cost_price: float = Field(
        title="Себестоимость за шт., руб.",
        description="Закупочная цена за единицу товара",
    )
    status: Literal["delivered", "returned", "cancelled"] = Field(
        title="Статус доставки", description="Статус выполнения заказа"
    )
    sold_at: date = Field(
        title="Дата продажи",
        description="Дата совершения продажи по умолчанию в формате YYYY-MM-DD без времени",
    )

    # mode='before' валидации и преобразования данных
    # до создания экземпляра модели
    @field_validator("quantity", mode='before')
    @classmethod
    def validate_quantity_positive(cls, v: int) -> int:
        """
        Проверяет, что количество товара >= 1.
        Меньше 1 штуки продать нельзя.
        """
        try:
            num_v = int(v)
        except (TypeError, ValueError):
            raise ValueError(
                f"Quantity must be an integer, got {type(v).__name__}"
            )
        if num_v < 1:
            raise ValueError("quantity must be >= 1")
        return v

    @field_validator("price", "cost_price", mode='before')
    @classmethod
    def validate_positive_price(cls, v: float) -> float:
        """
        Проверяет, что цена и себестоимость больше 0.
        Цена не может быть нулевой или отрицательной.
        """
        try:
            num_v = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"Price must be a number, got {type(v).__name__}")
        if num_v <= 0:
            raise ValueError("price and cost_price must be > 0")
        return v


@field_validator("sold_at", mode='before')
@classmethod
def validate_not_future(cls, v: str | date) -> date:
    """
    Проверяет, что дата продажи не из будущего.
    Нельзя продать товар завтрашним числом.
    """
    # Если это уже date (например, из другого источника)
    if isinstance(v, date):
        date_value = v
    else:
        # Преобразуем строку в date
        try:
            date_value = date.fromisoformat(
                v
            )  # "2025-03-15" → date(2025, 3, 15)
        except (TypeError, ValueError):
            raise ValueError(
                "sold_at must be a valid date in YYYY-MM-DD format"
            )

    # Проверяем, что дата не из будущего
    if date_value > date.today():
        raise ValueError("Дата продажи не может быть в будущем")

    # Возвращаем исходное значение (Pydantic сам преобразует в date позже)
    return v
