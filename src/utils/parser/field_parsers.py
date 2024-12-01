from datetime import date, datetime
from typing import Optional

import pandas as pd

ROLES_MAP = {
    "employee": ["сотрудник", "employee"],
    "admin": ["админ", "администратор", "admin"],
    "hr": ["hr"],
}
BOOL_MAP = {
    True: ["да", "yes", "1", "true"],
    False: ["нет", "no", "0", "false"],
}


def parse_role(value: str) -> str:
    if pd.isnull(value):
        raise ValueError("Требуется ввести роль")

    value = str(value).strip().lower()
    for role, aliases in ROLES_MAP.items():
        if value in aliases:
            return role

    raise ValueError(f"Неверное значение: '{value}'")


def parse_bool_field(value: str, default: bool) -> bool:
    if pd.isnull(value):
        return default

    value = str(value).strip().lower()

    for field, aliases in BOOL_MAP.items():
        if value in aliases:
            return field

    raise ValueError(f"Неверное значение: '{value}'")


def parse_date_field(value: str) -> Optional[datetime]:
    if pd.isnull(value) or value == "":
        return None
    try:
        return pd.to_datetime(value)
    except Exception as e:
        raise ValueError(f"Неверный формат даты: {str(e)}")


def parse_hired_at(value: str) -> date:
    if pd.isnull(value):
        raise ValueError("Требуется дата найма")
    try:
        return pd.to_datetime(value).date()
    except Exception as e:
        raise ValueError(f"Неверный формат даты: {str(e)}")


def parse_coins(value: str) -> int:
    if pd.isnull(value):
        return 0

    try:
        value = int(value)
    except ValueError:
        raise ValueError("Монеты должны быть целым числом")

    if value < 0:
        raise ValueError("Количество монет не должно быть отрицательным")

    return value
