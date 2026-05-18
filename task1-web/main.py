"""
Currency Viewer — FastAPI приложение для просмотра курсов валют.
Использует открытый API https://open.er-api.com (бесплатно, без ключа).
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import httpx

from currency_service import CurrencyService


# ── Жизненный цикл приложения ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создаём один HTTP-клиент на всё время жизни приложения."""
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    yield
    await app.state.http_client.aclose()


# ── Приложение ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Currency Viewer",
    description="Просмотр актуальных курсов валют",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Маршруты ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница с интерфейсом."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/rates/{base}")
async def get_rates(request: Request, base: str):
    """
    Возвращает курсы валют относительно базовой валюты.
    
    - **base**: трёхбуквенный код валюты (USD, EUR, RUB, …)
    """
    base = base.upper()
    service = CurrencyService(request.app.state.http_client)

    try:
        data = await service.fetch_rates(base)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return data


@app.get("/api/currencies")
async def get_currencies(request: Request):
    """Возвращает список поддерживаемых валют с названиями."""
    service = CurrencyService(request.app.state.http_client)
    try:
        return await service.fetch_currency_list()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
