# Sales Aggregator API

Мини-сервис для агрегации данных о продажах с маркетплейсов (Ozon, Wildberries, Yandex Market).

## Сервис успешно создан,
## Образ собран,
## Сервис даже успешно развернут на рендере (!!!) https://render.com/ по адресу
## https://boxstore-api-image-latest.onrender.com/docs

## Для локальной проверки сервиса можно использовать докер из папки с проектом, либо запустить по инструкции main.py из главной директории проекта

## 🐳 Запуск через Docker

### Предварительные требования

- Установленный [Docker](https://www.docker.com/products/docker-desktop/)

### Шаги для запуска

```bash
# 1. Клонировать репозиторий
git clone git@github.com:Alexman2505/BOXSTORE_test.git
cd BOXSTORE_test
```

# 2. Собрать Docker образ
```bash
docker build -t boxstore-api-image .
```

# 3. Запустить контейнер и проверить
```bash
docker run -d -p 8008:8008 --name boxstore-api-container boxstore-api-image
docker ps
```

# 4. После запуска проверить в браузере:
API: http://localhost:8008
Документация: http://localhost:8008/docs

### 4. Остановка и удаление

### Остановить и удалить контейнер. Проверить контейнеры (отсутствие)
```bash
docker stop boxstore-api-container
docker rm boxstore-api-container
docker ps -a
```

### Удалить образ и кэш
```bash
docker rmi boxstore-api-image
docker images
docker system prune -f
```

## 📦 Установка и запуск (без докера)

### 1. Клонировать репозиторий

```bash
git clone git@github.com:Alexman2505/BOXSTORE_test.git
cd BOXSTORE_test
```
### 2. Создайте и активируйте виртуальное окружение. Установите в виртуальное окружение библиотеки для проекта.
```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```
### 3. Запустите одной командой
```bash
python main.py
```
### Интерактиваня документация доступна по локальному адресу http://127.0.0.1:8008/docs

### Раздел Kubernetes
```bash
Windows (хост)
│
├── D:\Dev\boxstore_test\          (исходники)
│   ├── main.py
│   ├── Dockerfile
│   └── ...
│
└── WSL (Ubuntu) — виртуальная машина
    │
    ├── /mnt/d/Dev/boxstore_test/  ← Доступ к коду (монтирование)
    │
    ├── Docker (движок)
    │   └── Образ: boxstore-api:latest
    │       └── Контейнер (если запустить docker run)
    │
    └── Minikube (Kubernetes)
        │
        ├── Копия образа boxstore-api:latest (внутренний реестр)
        │
        ├── Pod-1 (контейнер из образа)  ← управляется Kubernetes
        ├── Pod-2 (контейнер из образа)  ← управляется Kubernetes
        │
        └── Service (порт 30008) → Доступ из браузера Windows

┌───────────────────────────────────────────────────┐
│             POD ( минимальная и неделимая единица)│
│  ┌─────────────────────────────────────────────┐  │
│  │              Контейнер                      │  │
│  │  ┌───────────────────────────────────────┐  │  │
│  │  │         Docker-образ                  │  │  │
│  │  │  alexman2505/boxstore-api-image:latest│  │  │
│  │  └───────────────────────────────────────┘  │  │
│  │                                             │  │
│  │  FastAPI приложение                         │  │
│  │  (uvicorn main:app --port 8008)             │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  IP-адрес: 10.244.0.5 (внутри кластера)           │
└───────────────────────────────────────────────────┘
```

### Описание проекта
Необходимо создать мини-сервис — REST API для загрузки, хранения и агрегации данных о продажах с маркетплейсов

Сервис должен:
1. Принимать данные о продажах через API
2. Хранить их в памяти (или SQLite)
3. Отдавать агрегированные метрики
4. Забирать курс валют из открытого API

Модели данных (Pydantic)

Создай модели для представления продажи:

```python
# Пример структуры одной продажи
{
    "order_id": "ORD-001",
    "marketplace": "ozon", # ozon | wildberries | yandex_market
    "product_name": "Кабель USB-C",
    "quantity": 3,
    "price": 450.00, # цена за штуку, руб.
    "cost_price": 120.00, # себестоимость за штуку, руб.
    "status": "delivered", # delivered | returned | cancelled
    "sold_at": "2025-03-15" # дата продажи, YYYY-MM-DD
}
```

Требования:
- Валидация: `marketplace` — только допустимые значения
- Валидация: `price` и `cost_price` > 0
- Валидация: `quantity` >= 1
- Валидация: `sold_at` — корректная дата, не из будущего

===

API эндпоинты (FastAPI)

Реализуйте следующие эндпоинты:

### POST /sales
Добавление одной или нескольких продаж (batch)

- Вход: список объектов продаж
- Выход: количество добавленных записей
- Ошибки валидации должны возвращать понятные сообщения

### GET /sales
Получение списка продаж с фильтрацией

Query-параметры (все опциональные):
- `marketplace` — фильтр по маркетплейсу
- `status` — фильтр по статусу
- `date_from`, `date_to` — фильтр по диапазону дат
- `page`, `page_size` — пагинация (по умолчанию page=1, page_size=20)

### DELETE /sales/clear
Чистка базы

### GET /analytics/summary
Агрегированные метрики за период

Query-параметры:
- `date_from`, `date_to` — период (обязательные)
- `marketplace` — фильтр по маркетплейсу (опционально)
- `group_by` — группировка: `marketplace` | `date` | `status` (опционально)

Возвращаемые метрики (в каждой группе):
- `total_revenue` — сумма (price * quantity) для delivered
- `total_cost` — сумма (cost_price * quantity) для delivered
- `gross_profit` — revenue - cost
- `margin_percent` — (gross_profit / revenue) * 100
- `total_orders` — количество уникальных order_id
- `avg_order_value` — средний чек (revenue / total_orders)
- `return_rate` — доля возвратов (returned / (delivered + returned)) * 100

### GET /analytics/top-products
Топ продуктов за период

Query-параметры:
- `date_from`, `date_to` — период (обязательные)
- `sort_by` — `revenue` | `quantity` | `profit` (по умолчанию `revenue`)
- `limit` — количество (по умолчанию 10)

===

Интеграция с внешним API

Реализуйте эндпоинт:

### GET /analytics/summary-usd
То же, что `/analytics/summary`, но все денежные метрики конвертированы в USD

- Курс получать из открытого API ЦБ РФ: `https://www.cbr-xml-daily.ru/daily_json.js`
- Курс кэшировать на 1 час (не дёргать API на каждый запрос)
- Если API недоступен — возвращать ошибку 503 с понятным сообщением

===

Обработка данных (Pandas)

Реализуйте эндпоинт:

### POST /analytics/upload-csv
Загрузка продаж из CSV-файла

- Принимает файл через UploadFile
- Парсит CSV с помощью Pandas
- Валидирует данные (те же правила, что и для POST /sales)
- Возвращает: количество загруженных строк, количество ошибок, список ошибок с номерами строк

Пример CSV — файл "sample_data.csv" в этом каталоге

===

## Структура проекта

Примерная организация кода:

```
sales_aggregator/
├── main.py              # Точка входа FastAPI
├── models/
│   ├── sale.py          # Pydantic-модели (Что приходит от клиента)
│   └── analytics.py     # Модели ответов аналитики (Что возвращается клиенту)
├── routers/             # описание эндпойнтов путей
│   ├── sales.py         # CRUD эндпоинты (Использует sale.py)
│   └── analytics.py     # Аналитические эндпоинты (Использует analytics.py)
├── services/            # Бизнес логика (работа со входящими моделями и выдача данных для исходящих)
│   ├── storage.py       # Хранение данных (in-memory или SQLite)
│   ├── aggregation.py   # Логика агрегации (Pandas, Возвращает dict, а не модели)
│   └── currency.py      # Работа с API курсов валют
├── requirements.txt
└── README.md            # Инструкция по запуску
```


===

## Дополнительные задания (необязательно, но будет плюсом)

1. **Тесты** — написать pytest-тесты хотя бы для ключевых эндпоинтов
2. **Dockerfile** — контейнеризация приложения и развертка
3. **Логирование** — структурированные логи (JSON-формат)
4. **Документация API** — кастомизация Swagger (описания, примеры)
