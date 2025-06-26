import pandas as pd
import pytest

from src.reports import spending_by_workday


@pytest.fixture
def sample_df():
    # рабочие и выходные все ДО 2025-06-22
    workdays = pd.to_datetime(["2025-06-10", "2025-06-11", "2025-06-12", "2025-06-13", "2025-06-14"])
    weekends = pd.to_datetime(["2025-06-07", "2025-06-08", "2025-06-15", "2025-06-16", "2025-06-21"])

    dates = list(workdays) + list(weekends)
    amounts = [-100, -150, -50, -200, -80, -300, -90, -70, -130, -120]

    df = pd.DataFrame({
        "date": dates,
        "amount": amounts,
        "category": ["Покупки"] * 10,
        "description": ["Тест"] * 10,
    })
    return df


def test_spending_by_workday_avg(sample_df):
    result = spending_by_workday(sample_df, date="2025-06-22")

    assert result["workday"] == pytest.approx(126.0, 0.01)  # (100+150+50+200+80)/5
    assert result["weekend"] == pytest.approx(132.0, 0.01)  # (300+90+70+130+120)/5


def test_spending_by_workday_empty():
    # Пустой датафрейм
    df = pd.DataFrame(columns=["date", "amount"])
    result = spending_by_workday(df, date="2025-01-01")
    assert result == {"workday": 0.0, "weekend": 0.0}


def test_spending_by_workday_invalid_dates():
    df = pd.DataFrame({
        "date": ["не дата", "ещё строка"],
        "amount": [-100, -200]
    })
    result = spending_by_workday(df)
    assert result == {"workday": 0.0, "weekend": 0.0}
