import json

import pytest

from src.services import find_p2p_transfers


@pytest.fixture
def sample_transactions():
    return [
        {"id": 1, "category": "Переводы", "description": "Сергей З."},
        {"id": 2, "category": "Переводы", "description": "Супермаркет"},
        {"id": 3, "category": "переводы", "description": "Валерий А."},
        {"id": 4, "category": "Транспорт", "description": "Метро"},
        {"id": 5, "category": "Переводы", "description": "Мария И."},
        {"id": 6, "category": "Переводы", "description": "Просто текст"},
        {"id": 7, "category": "Переводы", "description": "иван п."},
    ]


def test_find_p2p_transfers_returns_expected_transactions(sample_transactions):
    result_json = find_p2p_transfers(sample_transactions)
    result = json.loads(result_json)

    expected_ids = {1, 3, 5}
    result_ids = {trx["id"] for trx in result}

    assert result_ids == expected_ids
    assert all("description" in trx for trx in result)
    assert isinstance(result_json, str)
    assert result_json.startswith("[") and result_json.endswith("]")
