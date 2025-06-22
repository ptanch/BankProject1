from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

__all__ = [
    "find_p2p_transfers",
]


PERSON_PATTERN = re.compile(r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.$", re.UNICODE)


logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s – %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def find_p2p_transfers(transactions: List[Dict[str, Any]]) -> str:
    """Фильтрует «Переводы физическим лицам» и возвращает JSON‑строку"""

    logger.info("Начало поиска переводов физ. лицам: всего %d транзакций", len(transactions))

    result: List[Dict[str, Any]] = []

    for trx in transactions:
        category = str(trx.get("category", "")).strip().lower()
        description = str(trx.get("description", "")).strip()

        if category != "переводы":
            continue

        if PERSON_PATTERN.match(description):
            logger.debug("Совпадение: %s", description)
            result.append(trx)

    logger.info("Найдено переводов физ. лицам: %d", len(result))

    return json.dumps(result, ensure_ascii=False, indent=2)
