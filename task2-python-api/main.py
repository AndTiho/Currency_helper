import json
from datetime import datetime
from typing import Any

import requests


API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
CURRENCIES = ["USD", "EUR", "CNY"]


def fetch_currency_data() -> dict[str, Any]:
    """Получает актуальные данные о курсах валют."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise RuntimeError(f"Ошибка при запросе к API: {error}") from error
    except ValueError as error:
        raise RuntimeError("API вернул некорректный JSON") from error


def build_currency_report(data: dict[str, Any]) -> dict[str, Any]:
    """Формирует отчёт по выбранным валютам."""
    if "Valute" not in data:
        raise RuntimeError("В ответе API отсутствует раздел Valute")

    report_items = []

    for code in CURRENCIES:
        currency = data["Valute"].get(code)

        if not currency:
            report_items.append({
                "code": code,
                "error": "Валюта не найдена в ответе API",
            })
            continue

        current_value = currency["Value"]
        previous_value = currency["Previous"]
        difference = round(current_value - previous_value, 4)
        percent_change = round((difference / previous_value) * 100, 4)

        report_items.append({
            "code": code,
            "name": currency["Name"],
            "nominal": currency["Nominal"],
            "current_value": current_value,
            "previous_value": previous_value,
            "difference": difference,
            "percent_change": percent_change,
        })

    sorted_items = sorted(
        report_items,
        key=lambda item: item.get("percent_change", 0),
        reverse=True,
    )

    return {
        "source": API_URL,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": data.get("Date"),
        "previous_date": data.get("PreviousDate"),
        "currencies": sorted_items,
    }


def save_report(report: dict[str, Any], filename: str = "currency_report.json") -> None:
    """Сохраняет отчёт в JSON-файл."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)


def print_report(report: dict[str, Any]) -> None:
    """Печатает отчёт в консоль."""
    print("Отчёт по курсам валют")
    print(f"Дата данных: {report['date']}")
    print("-" * 60)

    for currency in report["currencies"]:
        if "error" in currency:
            print(f"{currency['code']}: {currency['error']}")
            continue

        print(
            f"{currency['code']} — {currency['name']}: "
            f"{currency['current_value']} ₽ "
            f"({currency['difference']:+.4f} ₽, "
            f"{currency['percent_change']:+.4f}%)"
        )

    print("-" * 60)
    print("Файл currency_report.json успешно сохранён.")


def main() -> None:
    try:
        data = fetch_currency_data()
        report = build_currency_report(data)
        save_report(report)
        print_report(report)
    except RuntimeError as error:
        print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()