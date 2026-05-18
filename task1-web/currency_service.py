"""
Сервис для работы с внешним API курсов валют.
Провайдер: https://open.er-api.com — бесплатный, без регистрации.
"""

import httpx
from datetime import datetime

BASE_URL = "https://open.er-api.com/v6/latest"

# Человекочитаемые названия валют
CURRENCY_NAMES: dict[str, str] = {
    "USD": "Доллар США",
    "EUR": "Евро",
    "GBP": "Фунт стерлингов",
    "JPY": "Японская иена",
    "CHF": "Швейцарский франк",
    "CNY": "Китайский юань",
    "RUB": "Российский рубль",
    "AUD": "Австралийский доллар",
    "CAD": "Канадский доллар",
    "HKD": "Гонконгский доллар",
    "SGD": "Сингапурский доллар",
    "NOK": "Норвежская крона",
    "SEK": "Шведская крона",
    "DKK": "Датская крона",
    "NZD": "Новозеландский доллар",
    "MXN": "Мексиканское песо",
    "BRL": "Бразильский реал",
    "INR": "Индийская рупия",
    "KRW": "Южнокорейская вона",
    "TRY": "Турецкая лира",
    "PLN": "Польский злотый",
    "CZK": "Чешская крона",
    "HUF": "Венгерский форинт",
    "AED": "Дирхам ОАЭ",
    "SAR": "Саудовский риял",
    "ILS": "Израильский шекель",
    "THB": "Тайский бат",
    "MYR": "Малайзийский ринггит",
    "IDR": "Индонезийская рупия",
    "PHP": "Филиппинское песо",
}

# Валюты, которые показываем по умолчанию
DEFAULT_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "CHF", "CNY",
    "AUD", "CAD", "HKD", "SGD", "TRY", "INR",
]


class CurrencyService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def fetch_rates(self, base: str) -> dict:
        """
        Запрашивает актуальные курсы для базовой валюты.
        
        Возвращает словарь с курсами, временем обновления и базовой валютой.
        Поднимает ValueError при неверном коде валюты,
        RuntimeError при сетевых проблемах.
        """
        if not base.isalpha() or len(base) != 3:
            raise ValueError(f"Неверный код валюты: «{base}». Ожидается трёхбуквенный код (напр. USD).")

        try:
            response = await self.client.get(f"{BASE_URL}/{base}")
            response.raise_for_status()
        except httpx.TimeoutException:
            raise RuntimeError("Превышено время ожидания ответа от внешнего API.")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ValueError(f"Валюта «{base}» не поддерживается.")
            raise RuntimeError(f"Внешний API вернул ошибку {exc.response.status_code}.")
        except httpx.RequestError as exc:
            raise RuntimeError(f"Ошибка сети: {exc}.")

        payload = response.json()

        if payload.get("result") != "success":
            raise RuntimeError("Внешний API вернул неуспешный результат.")

        rates = payload["rates"]

        # Формируем удобный список для фронтенда
        rate_list = [
            {
                "code": code,
                "name": CURRENCY_NAMES.get(code, code),
                "rate": round(rate, 6),
            }
            for code, rate in rates.items()
        ]
        rate_list.sort(key=lambda x: x["code"])

        # Время обновления в читаемом формате
        updated_at = datetime.utcfromtimestamp(
            payload.get("time_last_update_unix", 0)
        ).strftime("%d.%m.%Y %H:%M UTC")

        return {
            "base": base,
            "base_name": CURRENCY_NAMES.get(base, base),
            "updated_at": updated_at,
            "rates": rate_list,
        }

    async def fetch_currency_list(self) -> list[dict]:
        """Возвращает список популярных валют с кодами и названиями."""
        return [
            {"code": code, "name": CURRENCY_NAMES.get(code, code)}
            for code in sorted(CURRENCY_NAMES.keys())
        ]
