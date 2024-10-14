from typing import Union


class ServiceError(Exception):
    """Base exception class for service errors."""

    pass


class EntityCreateError(ServiceError):
    """Raised when an entity cannot be created in the service layer."""

    def __init__(self, entity_name: str, reason: str):
        super().__init__(f"Failed to create {entity_name}. Reason: {reason}")


class EntityReadError(ServiceError):
    """Raised when an entity cannot be read in the service layer."""

    def __init__(self, entity_name: str, entity_id: Union[int, str], reason: str):
        super().__init__(
            f"Failed to read {entity_name} with ID {entity_id}. Reason: {reason}"
        )


class EntityNotFoundError(ServiceError):
    """Raised when an entity cannot be found for a given operation, such as update or delete."""

    def __init__(self, entity_name: str, entity_id: Union[int, str]):
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with ID {entity_id} was not found.")


class EntityUpdateError(ServiceError):
    """Raised when an entity cannot be updated in the service layer."""

    def __init__(self, entity_name: str, entity_id: Union[int, str], reason: str):
        self.entity_id = entity_id
        super().__init__(
            f"Failed to update {entity_name} with ID {entity_id}. Reason: {reason}"
        )


class EntityDeletionError(ServiceError):
    """Raised when an entity cannot be deleted in the service layer."""

    def __init__(self, entity_name: str, entity_id: Union[int, str], reason: str):
        self.entity_id = entity_id
        super().__init__(
            f"Failed to delete {entity_name} with ID {entity_id}. Reason: {reason}"
        )
