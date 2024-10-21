from datetime import date

import pandas as pd


def parse_role(value: any) -> str:
    if value is None:
        raise ValueError("Role is required")
    value = str(value).strip().lower()
    if value in ["сотрудник", "employee"]:
        return "employee"
    elif value in ["админ", "администратор", "admin"]:
        return "admin"
    elif value == "hr":
        return "hr"
    else:
        raise ValueError(f"Invalid value for role: '{value}'")


def parse_is_adapted(value: any) -> bool:
    if value is None:
        return False
    value = str(value).strip().lower()
    if value in ["true", "1", "yes", "да"]:
        return True
    elif value in ["false", "0", "no", "нет"]:
        return False
    else:
        raise ValueError(f"Invalid value for is_adapted: '{value}'")


def parse_hired_at(value: any) -> date:
    if value is None:
        raise ValueError("hired_at date is required")
    try:
        return pd.to_datetime(value, dayfirst=True).date()
    except Exception as e:
        raise ValueError(f"Invalid date format: {str(e)}")


def parse_coins(value: any) -> int:
    if value is None or pd.isna(value):
        return 0
    try:
        value = int(value)
    except ValueError:
        raise ValueError("Coins must be an integer")
    if value < 0:
        raise ValueError("Coins must be non-negative")
    return value
