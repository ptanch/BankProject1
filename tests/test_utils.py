from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.utils import aggregate_by_card, compose_home_response, fetch_fx_rates, fetch_sp500_prices, get_greeting


def test_get_greeting_evening():
    assert get_greeting(datetime(2025, 6, 22, 21, 15)) == "Добрый вечер"


@pytest.mark.parametrize("hour, expected", [
    (6, "Доброе утро"),
    (13, "Добрый день"),
    (20, "Добрый вечер"),
    (2, "Доброй ночи"),
])
def test_get_greeting_all_times(hour, expected):
    dt = datetime(2025, 6, 22, hour, 0)
    assert get_greeting(dt) == expected


def test_fetch_fx_rates_success():
    mock_response = Mock()
    mock_response.json.return_value = {
        "result": "success",
        "conversion_rates": {
            "USD": 0.011,
            "EUR": 0.010
        }
    }

    with patch("src.utils.requests.get", return_value=mock_response) as mock_get, \
            patch("src.utils.EXCHANGE_RATES_API_KEY", "DUMMY_FX_KEY"):
        result = fetch_fx_rates(base="RUB", symbols=["USD", "EUR"])

    mock_get.assert_called_once_with(
        "https://v6.exchangerate-api.com/v6/DUMMY_FX_KEY/latest/RUB",
        timeout=10
    )
    assert result == {"USD": 0.011, "EUR": 0.010}


def test_fetch_fx_rates_all_rates():
    mock_response = Mock()
    mock_response.json.return_value = {
        "result": "success",
        "conversion_rates": {
            "USD": 0.011,
            "EUR": 0.010,
            "JPY": 1.56
        }
    }

    with patch("src.utils.requests.get", return_value=mock_response), \
         patch("src.utils.EXCHANGE_RATES_API_KEY", "DUMMY_FX_KEY"):
        result = fetch_fx_rates()
        assert result == {"USD": 0.011, "EUR": 0.010, "JPY": 1.56}


def test_fetch_fx_rates_error():
    # Мокаем ответ от requests.get с ошибкой
    mock_response = Mock()
    mock_response.json.return_value = {
        "result": "error",
        "error-type": "invalid-key"
    }

    with patch("src.utils.requests.get", return_value=mock_response), \
            patch("src.utils.EXCHANGE_RATES_API_KEY", "DUMMY_FX_KEY"):
        with pytest.raises(RuntimeError, match="Ошибка при получении курсов"):
            fetch_fx_rates(base="RUB", symbols=["USD"])


def test_fetch_sp500_prices_success():
    dummy_json = {
        "Time Series (Daily)": {
            "2025-06-20": {"4. close": "120.00"},
            "2025-06-19": {"4. close": "118.00"},
        }
    }

    mock_response = Mock()
    mock_response.json.return_value = dummy_json
    mock_response.raise_for_status = Mock()

    with patch("src.utils.requests.get", return_value=mock_response), \
            patch("src.utils.os.getenv", return_value="DUMMY_SP500_KEY"):
        result = fetch_sp500_prices(["AAPL"])
        assert result == {"AAPL": 120.0}


def test_fetch_sp500_prices_no_series():
    mock_response = Mock()
    mock_response.json.return_value = {
        "Note": "Thank you for using Alpha Vantage!"
    }
    mock_response.raise_for_status = Mock()

    with patch("src.utils.requests.get", return_value=mock_response), \
         patch("src.utils.os.getenv", return_value="DUMMY_SP500_KEY"):
        result = fetch_sp500_prices(["AAPL"])
        assert result == {}  # Ничего не найдено


def test_aggregate_by_card_basic():
    df = pd.DataFrame([
        {"card": "1234567812345678", "amount": -100, "category": "Магазин", "description": "Тест"},
        {"card": "1234567812345678", "amount": -200, "category": "Еда", "description": "Тест"},
        {"card": "1234567812345678", "amount": 300, "category": "Пополнение", "description": "Тест"},
    ])
    result = aggregate_by_card(df)
    last4 = "5678"
    assert last4 in result
    assert result[last4]["общая_сумма_расходов"] == 300
    assert result[last4]["кешбэк"] == 3
    assert len(result[last4]["топ_5"]) == 2


def test_compose_home_response_output():
    dt = datetime(2025, 6, 23, 10, 0)
    cards = {"1234": {"общая_сумма_расходов": 100, "кешбэк": 1, "топ_5": []}}
    fx = {"USD": 0.011}
    stocks = {"AAPL": 120.0}

    result = compose_home_response(dt, cards, fx, stocks)
    assert result["приветствие"] == "Доброе утро"
    assert result["дата_время"] == "2025-06-23 10:00:00"
    assert result["по_картам"] == cards
    assert result["курсы_валют"] == fx
    assert result["акции_sp500"] == stocks
