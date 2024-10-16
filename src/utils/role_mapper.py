from src.schemas.user import UserRole

# Mapping of role strings to UserRole values
ROLE_MAPPING = {
    "сотрудник": "employee",
    "hr": "hr",
}


def map_role(role_str: str) -> UserRole:
    """
    Map a role string to a UserRole enumeration.

    This function takes a role string (e.g., "сотрудник", "hr") and
    converts it to a corresponding UserRole value. The mapping is
    defined in the ROLE_MAPPING dictionary. If the provided role string
    is not found in the mapping, a ValueError is raised.

    Args:
        role_str (str): The role string to be mapped.

    Returns:
        UserRole: The mapped UserRole corresponding to the provided role string.

    Raises:
        ValueError: If the provided role string is not valid or not found in the mapping.
    """
    try:
        role_value = ROLE_MAPPING[role_str.lower()]
        return UserRole(role_value)
    except KeyError:
        raise ValueError(f"Invalid role '{role_str}'")
