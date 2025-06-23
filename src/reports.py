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

    # 1. Подготовка даты
    ref_dt = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
    start_dt = ref_dt - timedelta(days=90)  # ≈ 3 месяца

    logger.info("Формирую отчёт с %s по %s", start_dt.date(), ref_dt.date())

    # 2. Приводим столбец даты к datetime
    df = transactions.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])  # удаляем строки без даты/суммы

    # 3. Фильтр по периоду
    mask_period = (df["date"] >= start_dt) & (df["date"] <= ref_dt)
    df_period = df.loc[mask_period]

    if df_period.empty:
        logger.warning("Нет данных за указанный период")
        return {"workday": 0.0, "weekend": 0.0}

    # 4. Оставляем только расходы (amount < 0)
    expenses = df_period[df_period["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()  # делаем положительными

    # 5. Группируем по дате, считаем дневные суммы
    daily_sum = expenses.groupby(expenses["date"].dt.date)["amount"].sum()
    daily_sum = daily_sum.reset_index(name="total")  # date|total

    # 6. Разделяем на рабочие / выходные, считаем среднее
    daily_sum["weekday"] = pd.to_datetime(daily_sum["date"]).dt.weekday
    workday_mean = daily_sum[daily_sum["weekday"] < 5]["total"].mean() or 0.0
    weekend_mean = daily_sum[daily_sum["weekday"] >= 5]["total"].mean() or 0.0

    result = {
        "workday": round(float(workday_mean), 2),
        "weekend": round(float(weekend_mean), 2),
    }

    logger.info("Средние траты – Рабочие: %.2f, Выходные: %.2f", result["workday"], result["weekend"])
    return result
