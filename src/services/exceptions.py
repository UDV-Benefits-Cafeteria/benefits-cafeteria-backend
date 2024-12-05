class ServiceError(Exception):
    """Base exception class for service errors."""

    pass


class EntityCreateError(ServiceError):
    """Raised when an entity cannot be created in the service layer."""

    def __init__(self, service_name: str, reason: str):
        super().__init__(f"{service_name} failed to create entity. Reason: {reason}")


class EntityReadError(ServiceError):
    """Raised when an entity cannot be read in the service layer."""

    def __init__(self, service_name: str, reason: str):
        super().__init__(f"{service_name} failed to read entity. Reason: {reason}")


class EntityNotFoundError(ServiceError):
    """Raised when an entity cannot be found for a given operation, such as update or delete."""

    def __init__(self, service_name: str, read_param: str):
        super().__init__(
            f"{service_name} couldn't find entity with reading parameters: {read_param}."
        )


class EntityUpdateError(ServiceError):
    """Raised when an entity cannot be updated in the service layer."""

    def __init__(self, service_name: str, reason: str):
        super().__init__(f"{service_name} failed to update entity. Reason: {reason}")


class EntityDeleteError(ServiceError):
    """Raised when an entity cannot be deleted in the service layer."""

    def __init__(self, service_name: str, reason: str):
        super().__init__(f"{service_name} failed to delete entity. Reason: {reason}")


class PermissionDeniedError(ServiceError):
    """Raised when an action is forbidden for the user."""

    def __init__(self, service_name: str, reason: str):
        super().__init__(f"Forbidden in {service_name}. Reason: {reason}")
