from datetime import date

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
    if value is None:
        raise ValueError("Role is required")

    value = str(value).strip().lower()
    for role, aliases in ROLES_MAP.items():
        if value in aliases:
            return role

    raise ValueError(f"Invalid value for role: '{value}'")


def parse_is_adapted(value: str) -> bool:
    if value is None:
        return False

    value = str(value).strip().lower()

    for role, aliases in BOOL_MAP.items():
        if value in aliases:
            return role

    raise ValueError(f"Invalid value for is_adapted: '{value}'")


def parse_hired_at(value: str) -> date:
    if value is None:
        raise ValueError("hired_at date is required")
    try:
        return pd.to_datetime(value, dayfirst=True).date()
    except Exception as e:
        raise ValueError(f"Invalid date format: {str(e)}")


def parse_coins(value: str) -> int:
    if value is None or pd.isna(value):
        return 0

    try:
        value = int(value)
    except ValueError:
        raise ValueError("Coins must be an integer")

    if value < 0:
        raise ValueError("Coins must be non-negative")

    return value
