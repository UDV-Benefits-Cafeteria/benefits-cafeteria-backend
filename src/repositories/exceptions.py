from typing import Union


class RepositoryError(Exception):
    """Base exception class for repository errors."""

    pass


class EntityCreateError(RepositoryError):
    """Raised when an entity cannot be created."""

    def __init__(self, entity_name: str, reason: str):
        super().__init__(f"Failed to create {entity_name}. Reason: {reason}")


class EntityReadError(RepositoryError):
    """Raised when an entity cannot be read."""

    def __init__(self, entity_name: str, read_param: Union[int, str], reason: str):
        self.read_param = read_param
        super().__init__(
            f"Failed to read {entity_name} with read_param {read_param}. Reason: {reason}"
        )


class EntityUpdateError(RepositoryError):
    """Raised when an entity cannot be updated."""

    def __init__(self, entity_name: str, read_param: Union[int, str], reason: str):
        self.read_param = read_param
        super().__init__(
            f"Failed to update {entity_name} with read_param {read_param}. Reason: {reason}"
        )


class EntityDeleteError(RepositoryError):
    """Raised when an entity cannot be deleted."""

    def __init__(self, entity_name: str, read_param: Union[int, str], reason: str):
        self.read_param = read_param
        super().__init__(
            f"Failed to delete {entity_name} with read_param {read_param}. Reason: {reason}"
        )
