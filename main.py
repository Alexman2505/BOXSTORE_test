"""
Вся документация по фастапи есть на русском языке
https://fastapi.tiangolo.com/ru/python-types/#type-hints-with-metadata-annotations
но без V** её не открыть и не прочитать
"""

from fastapi import FastAPI
from routers import (
    sales,
    analytics,
)  # Импортируем роутеры (обработчики путей URL)
import uvicorn  # (асинхронный сервер, создает словарь с параметрами подключения)

app = FastAPI(
    title="Sales Aggregator API",
    description="Мини-сервис для агрегации данных о продажах с маркетплейсов",
    version="1.0.0",
)

app.include_router(sales.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    """
    Корневой эндпоинт с информацией о сервисе. Просто показывает, что api жив.
    Интерактивная документация по адресу http://127.0.0.1:8008/docs
    """
    return {"message": "Sales Aggregator API", "docs": "/docs"}


if __name__ == "__main__":
    """
    0.0.0.0 - слушаем все интерфейсы
    localhost или 127.0.0.1 - это адрес для клиента (браузера)
    """
    uvicorn.run(app, host="0.0.0.0", port=8008)
