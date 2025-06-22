import os
import json
import logging
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import requests


load_dotenv()

ALPHAVANTAGE_URL = "https://www.alphavantage.co/query"
EXCHANGE_RATES_API_KEY = os.getenv("EXCHANGE_RATES_API_KEY")
STOCK_PRICES_API_KEY = os.getenv("STOCK_PRICES_API_KEY")


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s – %(message)s", handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def get_greeting(dt: datetime) -> str:
    """
    Возвращает приветствие («Доброе утро/день/вечер/ночи»)
    в зависимости от локального времени `dt`.
    """
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def load_transactions(path: Path) -> pd.DataFrame:
    """Читает XLSX с операциями и приводит к DataFrame"""
    logger.info("Читаю файл транзакций: %s", path)
    df = pd.read_excel(path, engine="openpyxl")
    df = df.fillna("")
    return df


def fetch_fx_rates(base: str = "RUB", symbols: list[str] | None = None) -> dict:
    """
    Получает курсы валют через ExchangeRate-API (требует API-ключ)
    Документация: https://www.exchangerate-api.com/docs/free
    """
    if not EXCHANGE_RATES_API_KEY:
        raise RuntimeError("Не найден EXCHANGE_RATES_API_KEY в .env")

    symbols_query = ",".join(symbols) if symbols else ""
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATES_API_KEY}/latest/{base}"

    logger.info("Запрашиваю курсы валют: %s", url)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("result") != "success":
        raise RuntimeError(f"Ошибка при получении курсов: {data}")

    all_rates = data["conversion_rates"]  # {"USD": ..., "EUR": ..., ...}

    if symbols:
        return {sym: all_rates.get(sym) for sym in symbols}
    return all_rates


def aggregate_by_card(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    По каждой карте вычисляет:
      • total_spent – сумма отрицательных amount
      • cashback – 1% от расхода
      • top5 – топ-5 расходов (словарями)
    Возвращает {last4: {...}, ...}
    """
    result: Dict[str, Dict[str, Any]] = {}

    for last4, group in df.groupby(df["card"].astype(str).str[-4:]):
        expenses = group[group["amount"] < 0]
        total = abs(expenses["amount"].sum())
        cashback = round(total / 100)
        top5 = (
            expenses.nsmallest(5, "amount")  # самые большие расходы (amount отриц.)
            .assign(amount=lambda x: x["amount"].abs())  # делаем положительными для отчёта
            .to_dict(orient="records")
        )
        result[last4] = {
            "общая_сумма_расходов": total,
            "кешбэк": cashback,
            "топ_5": top5,
        }

    return result


def fetch_sp500_prices(tickers: list[str]) -> dict[str, float]:
    """
    Берёт цены акций через Alpha Vantage API (ключ из .env).
    """
    if not STOCK_PRICES_API_KEY:
        raise RuntimeError("Не найден STOCK_PRICES_API_KEY в .env")

    prices = {}
    for symbol in tickers:
        logger.info("AlphaVantage: %s", symbol)
        params = {
            "function": "time_series_daily_adjusted",
            "symbol": symbol,
            "apikey": STOCK_PRICES_API_KEY,
            "output_size": "compact",
        }
        r = requests.get(ALPHAVANTAGE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        time_series = data.get("time_series_daily")
        if not time_series:
            logger.warning("Нет данных по %s", symbol)
            continue

        last_date = next(iter(time_series))
        prices[symbol] = float(time_series[last_date]["4. close"])

    return prices


def compose_home_response(
    dt_in: datetime, card_stats: Dict[str, Dict[str, Any]], fx_rates: Dict[str, float], stock_prices: Dict[str, float]
) -> Dict[str, Any]:
    """
    Складывает все блоки в итоговый словарь,
    который преобразуется в JSON.
    """
    return {
        "приветствие": get_greeting(dt_in),
        "дата_время": dt_in.strftime("%Y-%m-%d %H:%M:%S"),
        "по_картам": card_stats,  # сгруппировано по last4
        "курсы_валют": fx_rates,
        "акции_sp500": stock_prices,
    }
