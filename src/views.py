import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from utils import (
    load_transactions,
    aggregate_by_card,
    fetch_fx_rates,
    fetch_sp500_prices,
    compose_home_response,
)

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "operations.xlsx"
FX_SYMBOLS = ["USD", "EUR"]
SP500_TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]

def home(date_time_str: str) -> Dict[str, Any]:
    """
    Главная функция. Принимает строку "YYYY-MM-DD HH:MM:SS" и
    возвращает словарь, готовый к сериализации в JSON.
    """
    dt_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")

    df = load_transactions(DATA_FILE)
    cards_info = aggregate_by_card(df)

    fx = fetch_fx_rates(base="RUB", symbols=FX_SYMBOLS)
    stocks = fetch_sp500_prices(SP500_TICKERS)

    return compose_home_response(dt_obj, cards_info, fx, stocks)


if __name__ == "__main__":
    # быстрая проверка
    print(json.dumps(home(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), ensure_ascii=False, indent=2))
