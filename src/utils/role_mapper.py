from src.schemas.user import UserRole

ROLE_MAPPING = {
    "сотрудник": "employee",
    "hr": "hr",
}


def map_role(role_str: str) -> UserRole:
    try:
        role_value = ROLE_MAPPING[role_str.lower()]
        return UserRole(role_value)
    except KeyError:
        raise ValueError(f"Invalid role '{role_str}'")
