from typing import Union


class RepositoryError(Exception):
    """Base exception class for repository errors."""

    pass


class EntityCreateError(RepositoryError):
    """Raised when an entity cannot be created."""

    def __init__(self, repo_name: str, table_name: str, reason: str):
        super().__init__(
            f"{repo_name} failed to create entity in {table_name}. Reason: {reason}"
        )


class EntityReadError(RepositoryError):
    """Raised when an entity cannot be read."""

    def __init__(
        self, repo_name: str, table_name: str, read_param: Union[int, str], reason: str
    ):
        super().__init__(
            f"{repo_name} failed to read entity from {table_name} with reading parameters: {read_param}. Reason: {reason}"
        )


class EntityUpdateError(RepositoryError):
    """Raised when an entity cannot be updated."""

    def __init__(
        self, repo_name: str, table_name: str, read_param: Union[int, str], reason: str
    ):
        super().__init__(
            f"{repo_name} failed to update entity in {table_name} with reading parameters: {read_param}. Reason: {reason}"
        )


class EntityDeleteError(RepositoryError):
    """Raised when an entity cannot be deleted."""

    def __init__(
        self, repo_name: str, table_name: str, read_param: Union[int, str], reason: str
    ):
        super().__init__(
            f"{repo_name} failed to delete entity in {table_name} with reading parameters: {read_param}. Reason: {reason}"
        )
