"""
RPA робот для проверки API (облегчённая версия для Render)
Без браузера, только HTTP запросы
"""

from robocorp import tasks
import requests
import json


@tasks.task
def quick_health_check():
    """
    Быстрая проверка API через HTTP (без браузера)
    """
    BASE_URL = "https://boxstore-api-image-latest.onrender.com"

    print("🤖 Робот запущен (лёгкий режим, без браузера)")
    print(f"📍 Проверяем API: {BASE_URL}")

    results = {}

    # ========== Проверяем корневой эндпоинт ==========
    try:
        response = requests.get(f"{BASE_URL}/", timeout=30)
        results["root"] = {
            "status_code": response.status_code,
            "ok": response.ok,
        }
        print(f"✅ Корневой эндпоинт: {response.status_code}")
    except Exception as e:
        results["root"] = {"error": str(e)}
        print(f"❌ Ошибка корневого эндпоинта: {e}")

    # ========== Проверяем /docs ==========
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=30)
        results["docs"] = {
            "status_code": response.status_code,
            "ok": response.ok,
        }
        print(f"✅ Swagger UI: {response.status_code}")
    except Exception as e:
        results["docs"] = {"error": str(e)}
        print(f"❌ Ошибка Swagger: {e}")

    # ========== Проверяем /sales ==========
    try:
        response = requests.get(f"{BASE_URL}/sales/", timeout=30)

        if response.ok:
            try:
                data = response.json()
                data_type = type(data).__name__

                # Безопасно считаем количество
                count = None
                if isinstance(data, list):
                    count = len(data)
                elif isinstance(data, dict):
                    count = len(data.keys())

                results["sales"] = {
                    "status_code": response.status_code,
                    "ok": True,
                    "data_type": data_type,
                    "count": count,
                }
                print(
                    f"✅ /sales/: {response.status_code} (тип: {data_type}, элементов: {count})"
                )
            except json.JSONDecodeError:
                results["sales"] = {
                    "status_code": response.status_code,
                    "ok": True,
                    "data_type": "text",
                    "preview": response.text[:100],
                }
                print(f"✅ /sales/: {response.status_code} (текстовый ответ)")
        else:
            results["sales"] = {
                "status_code": response.status_code,
                "ok": False,
            }
            print(f"⚠️ /sales/: {response.status_code}")

    except Exception as e:
        results["sales"] = {"error": str(e)}
        print(f"❌ Ошибка /sales/: {e}")

    # ========== Итоговый результат ==========
    all_ok = all(
        v.get("ok", False)
        for k, v in results.items()
        if isinstance(v, dict) and k != "error"
    )

    return {
        "status": "ok" if all_ok else "partial",
        "message": (
            "Все проверки пройдены" if all_ok else "Часть проверок не пройдена"
        ),
        "url": BASE_URL,
        "checks": results,
    }


@tasks.task
def full_api_test():
    """
    Полная проверка всех эндпоинтов аналитики
    """
    BASE_URL = "https://boxstore-api-image-latest.onrender.com"
    results = {}

    print("🤖 Полное тестирование API")

    # Тест 1: GET /analytics/summary
    try:
        url = f"{BASE_URL}/analytics/summary?date_from=2024-04-01&date_to=2026-04-22"
        response = requests.get(url, timeout=30)
        results["summary"] = {
            "status_code": response.status_code,
            "ok": response.ok,
        }
        print(f"✅ /summary: {response.status_code}")
    except Exception as e:
        results["summary"] = {"error": str(e)}
        print(f"❌ /summary: {e}")

    # Тест 2: GET /analytics/top-products
    try:
        url = f"{BASE_URL}/analytics/top-products?date_from=2024-04-01&date_to=2026-04-22"
        response = requests.get(url, timeout=30)
        results["top_products"] = {
            "status_code": response.status_code,
            "ok": response.ok,
        }
        print(f"✅ /top-products: {response.status_code}")
    except Exception as e:
        results["top_products"] = {"error": str(e)}
        print(f"❌ /top-products: {e}")

    # Тест 3: GET /analytics/summary-usd
    try:
        url = f"{BASE_URL}/analytics/summary-usd?date_from=2024-04-01&date_to=2026-04-22"
        response = requests.get(url, timeout=30)
        results["summary_usd"] = {
            "status_code": response.status_code,
            "ok": response.ok,
        }
        print(f"✅ /summary-usd: {response.status_code}")
    except Exception as e:
        results["summary_usd"] = {"error": str(e)}
        print(f"❌ /summary-usd: {e}")

    # Итог
    all_ok = all(v.get("ok", False) for v in results.values())

    return {
        "status": "completed" if all_ok else "completed_with_errors",
        "results": results,
        "url": BASE_URL,
    }
