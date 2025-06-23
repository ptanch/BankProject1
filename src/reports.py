from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s – %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)


def save_report(arg: str | Callable | None = None):
    """Декоратор: сохраняет результат функции‑отчёта в JSON‑файл.

    * `@save_report` — файл `report_<func>_<datetime>.json` в `reports_output/`.
    * `@save_report("custom.json")` — файл по указанному пути.
    """

    def _decorator(func: Callable[..., Dict[str, Any]]):
        def _wrapper(*args, **kwargs):
            result: Dict[str, Any] = func(*args, **kwargs)

            # Определяем имя файла
            if isinstance(arg, str):
                file_path = Path(arg)
            else:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_dir = Path(__file__).resolve().parents[1] / "reports_output"
                default_dir.mkdir(exist_ok=True)
                file_path = default_dir / f"report_{func.__name__}_{ts}.json"

            # Запись
            try:
                with open(file_path, "w", encoding="utf-8") as fp:
                    json.dump(result, fp, ensure_ascii=False, indent=2)
                logger.info("Отчёт сохранён в %s", file_path)
            except Exception as exc:
                logger.error("Не удалось сохранить отчёт в %s: %s", file_path, exc)

            return result

        _wrapper.__name__ = func.__name__
        _wrapper.__doc__ = func.__doc__
        return _wrapper

    # Поддержка вызова без скобок: @save_report vs @save_report("file.json")
    if callable(arg):
        return _decorator(arg)  # type: ignore[arg-type]
    return _decorator


@save_report  # можно поменять, например, на @save_report("workday_report.json")
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> Dict[str, float]:
    """Возвращает средние траты в рабочие/выходные за последние 3 месяца"""

    df = transactions.copy()

    # Убеждаемся, что даты в нужном формате
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["date", "amount"])  # Удаляем строки без даты/суммы

    # Если дата не указана — берем максимальную дату из данных
    if date:
        ref_dt = datetime.strptime(date, "%Y-%m-%d")
    else:
        ref_dt = df["date"].max()

    start_dt = ref_dt - timedelta(days=90)
    logger.info("Формирую отчёт с %s по %s", start_dt.date(), ref_dt.date())

    # Фильтрация по диапазону
    df_period = df[(df["date"] >= start_dt) & (df["date"] <= ref_dt)]
    if df_period.empty:
        logger.warning("Нет данных за указанный период")
        return {"workday": 0.0, "weekend": 0.0}

    # Оставляем только расходы (amount < 0)
    expenses = df_period[df_period["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()

    # Сумма по дням
    daily_sum = expenses.groupby(expenses["date"].dt.date)["amount"].sum().reset_index(name="total")

    # Рабочие / выходные дни
    daily_sum["weekday"] = pd.to_datetime(daily_sum["date"]).dt.weekday
    workday_mean = daily_sum[daily_sum["weekday"] < 5]["total"].mean() or 0.0
    weekend_mean = daily_sum[daily_sum["weekday"] >= 5]["total"].mean() or 0.0

    result = {
        "workday": round(float(workday_mean), 2),
        "weekend": round(float(weekend_mean), 2),
    }

    logger.info("Средние траты – Рабочие: %.2f, Выходные: %.2f", result["workday"], result["weekend"])
    return result
