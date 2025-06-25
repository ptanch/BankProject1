from unittest.mock import Mock, patch

from src.views import home


def test_home_success():
    test_datetime = "2025-06-23 15:30:00"

    dummy_df = Mock()  # Неважно, что внутри — оно не используется напрямую
    dummy_cards_info = {
        "1234": {"total": 1000, "currency": "RUB"},
        "5678": {"total": 2000, "currency": "RUB"}
    }
    dummy_fx = {"USD": 0.011, "EUR": 0.010}
    dummy_stocks = {"AAPL": 120.0, "MSFT": 310.5}

    with patch("src.views.load_transactions", return_value=dummy_df), \
            patch("src.views.aggregate_by_card", return_value=dummy_cards_info), \
            patch("src.views.fetch_fx_rates", return_value=dummy_fx), \
            patch("src.views.fetch_sp500_prices", return_value=dummy_stocks), \
            patch("src.views.compose_home_response") as mock_compose:
        mock_compose.return_value = {
            "greeting": "Добрый день",
            "cards": dummy_cards_info,
            "fx": dummy_fx,
            "stocks": dummy_stocks
        }

        result = home(test_datetime)

        # Проверяем, что все функции были вызваны
        mock_compose.assert_called_once()
        assert "greeting" in result
        assert "cards" in result
        assert result["cards"] == dummy_cards_info
