import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.reports import spending_by_workday
from src.services import find_p2p_transfers
from src.utils import load_transactions
from src.views import home

PERSON_PATTERN = re.compile(r"\b[А-ЯЁ][а-яё]+ [А-ЯЁ]\.?\b", re.UNICODE)
DATA_FILE = Path(__file__).resolve().parents[0] / "data" / "operations.xlsx"


def main():
    while True:
        print("\n=== Меню ===")
        print("1. Главная страница")
        print("2. Поиск переводов физлицам")
        print("3. Отчёт: Траты в будни и выходные")
        print("0. Выход")

        choice = input("Выберите пункт меню: ").strip()

        if choice == "1":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = home(now)
            print("\n=== Главная страница ===")
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif choice == "2":
            df = load_transactions(DATA_FILE)
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])

            min_date = df["date"].min().date()
            max_date = df["date"].max().date()

            print(f"Доступный диапазон: {min_date} — {max_date}")
            print("Введите дату начала (по умолчанию: начало диапазона):")

            start_input = input("Начало (ГГГГ-ММ-ДД): ").strip()
            print("Введите дату окончания (по умолчанию: конец диапазона):")
            end_input = input("Конец (ГГГГ-ММ-ДД): ").strip()

            try:
                start_date = datetime.strptime(start_input, "%Y-%m-%d").date() if start_input else min_date
                end_date = datetime.strptime(end_input, "%Y-%m-%d").date() if end_input else max_date
            except ValueError:
                print("Неверный формат даты. Используется весь диапазон.")
                start_date, end_date = min_date, max_date

            # Фильтрация по дате
            mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
            filtered_df = df[mask]
            print(f"\n=== Переводы физическим лицам ({start_date} – {end_date}) ===")
            result_json = find_p2p_transfers(filtered_df.to_dict(orient="records"))
            print(result_json)

        elif choice == "3":
            df = load_transactions(DATA_FILE)
            df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
            df = df.dropna(subset=["date"])

            if df["date"].empty:
                print("Нет данных для анализа.")
                continue

            max_date = df["date"].max().strftime("%Y-%m-%d")

            print(f"\nВведите дату отсчёта (по умолчанию {max_date}):")
            user_date = input("Дата (ГГГГ-ММ-ДД): ").strip()

            # Проверка пользовательской даты
            if user_date:
                try:
                    datetime.strptime(user_date, "%Y-%m-%d")
                    selected_date = user_date
                except ValueError:
                    print("Неверный формат даты. Используется дата по умолчанию.")
                    selected_date = max_date
            else:
                selected_date = max_date

            print(f"\n=== Отчёт: Траты в будни и выходные (до {selected_date}) ===")
            result = spending_by_workday(df, date=selected_date)
            print_json(result)

        elif choice == "0":
            print("До свидания!")
            break

        else:
            print("Неверный ввод. Попробуйте снова.")


def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
