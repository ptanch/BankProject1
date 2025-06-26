# Приложение для анализа банковских операций

### Это консольное приложение на Python для анализа и отчётности по банковским транзакциям, полученным из Excel, CSV или JSON-файлов. Проект предоставляет сводную информацию по картам, анализирует расходы, курсы валют, цены акций и позволяет находить переводы физическим лицам.

## Цель проекта
+ Автоматизировать обработку и анализ транзакций.
+ Упростить формирование отчётов: расходы по будням и выходным, переводы физлицам.
+ Получать курсы валют и цены акций через API.
+ Тренировка навыков работы с `pandas`, регулярными выражениями, API-запросами, файловой системой и тестированием.

## Установка
### Требования

+ Python 3.10 или выше (проект проверен на 3.13)
+ pip / poetry
+ Git (для клонирования)

### Установка с помощью `poetry`
```
git clone https://github.com/yourusername/bank-transactions-analyzer.git
cd bank-transactions-analyzer
poetry install
```

#### Если `poetry` не установлен:
```
pip install poetry
```

## Используемые технологии
+ `pandas` — работа с табличными данными
+ `openpyxl`, `csv`, `json` — парсинг файлов
+ `requests` — работа с API (ExchangeRate и AlphaVantage)
+ `logging` — логирование работы
+ `pytest` — модульное тестирование
+ `.env` — безопасное хранение ключей
+ `.env_example` - инструкция для разработчиков как использовать API-ключи

## Структура проекта

```
├── data/                   # Исходные транзакции (.xlsx)
├── reports_output/         # Сгенерированные отчёты
├── src/
│   ├── views.py            # Главная функция home
│   ├── utils.py            # Работа с данными и API
│   ├── reports.py          # Отчёты (будни/выходные)
│   ├── services.py         # Поиск переводов физлицам
├── tests/                  # Тесты
├── .env                    # API-ключи
├── .env_example
├── .flake8
├── .gitignore
├── pyproject.toml
├── poetry.lock
├── README.md
└── main.py                 # Точка входа
```

### Настройка API-ключей
```
EXCHANGE_RATES_API_KEY=ваш_ключ_от_exchangerate
ALPHA_VANTAGE_API_KEY=ваш_ключ_от_alphavantage
```

### Запуск программы
```poetry run python main.py```

#### Вам будет доступно меню:
```commandline
=== Меню ===
1. Главная страница
2. Поиск переводов физлицам
3. Отчёт: Траты в будни и выходные
0. Выход
```

## Примеры использования
### Главная функция

```
from src.views import home
result = home("2025-06-23 15:00:00")
print(result)
```

### Поиск переводов физическим лицам
```
from src.services import find_p2p_transfers
with open("data/operations.xlsx", "rb") as f:
    transactions = load_transactions(f)
filtered = find_p2p_transfers(transactions)
```

### Отчёт по будням и выходным
```
from src.reports import spending_by_workday
df = load_transactions("data/operations.xlsx")
report = spending_by_workday(df)
print(report)
```

### Тестирование
```poetry run pytest tests/```

### Обратная связь
Если вы нашли баг или хотите предложить улучшения — создайте issue или pull request.