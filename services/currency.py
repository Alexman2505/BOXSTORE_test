"""
Работа с курсом валют из внешнего API.
Курс кэшируется на 1 час, чтобы не дёргать API при каждом запросе.
"""

import httpx
from datetime import datetime, timedelta

# ========== КЭШ ДЛЯ КУРСА ==========
# Храним курс и время, до которого он актуален
_cached_rate: float | None = None
_cached_until: datetime | None = None


async def get_usd_rate() -> float:
    """
    Получает курс USD к RUB из API ЦБ РФ с кэшированием на 1 час.

    Алгоритм:
        1. Проверяем кэш - если есть и не истек, возвращаем из кэша
        2. Если кэша нет или он истек - идем в API ЦБ РФ
        3. Сохраняем новый курс в кэш на 1 час
        4. Возвращаем курс

    Returns:
        float: Текущий курс USD (например, 92.50)

    Raises:
        Exception: Если API недоступен или вернул ошибку

    Example:
        >>> rate = await get_usd_rate()
        >>> print(rate)  # 92.50
    """
    global _cached_rate, _cached_until

    # ========== ПРОВЕРКА КЭША ==========
    # Если курс есть и время еще не истекло - возвращаем сохраненное значение
    if _cached_rate is not None and _cached_until is not None:
        if datetime.now() < _cached_until:
            return _cached_rate

    # ========== ЗАПРОС К API ==========
    try:
        # Асинхронный HTTP запрос к API ЦБ РФ
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.cbr-xml-daily.ru/daily_json.js"
            )
            response.raise_for_status()  # Если статус не 200 - выбросит исключение

            data = response.json()

            # Извлекаем курс доллара
            # Структура ответа: {"Valute": {"USD": {"Value": 92.50}}}
            rate = data["Valute"]["USD"]["Value"]

            # ========== СОХРАНЯЕМ В КЭШ ==========
            _cached_rate = rate
            _cached_until = datetime.now() + timedelta(hours=1)

            return rate

    except Exception:
        # Если API недоступен - выбрасываем исключение
        # Оно будет поймано в роутере и преобразовано в HTTP 503
        raise Exception("Currency API unavailable")
