from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.utils import fetch_fx_rates, fetch_sp500_prices, get_greeting


def test_get_greeting_evening():
    assert get_greeting(datetime(2025, 6, 22, 21, 15)) == "Добрый вечер"


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
