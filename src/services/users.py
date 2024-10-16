import logging
from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.schemas.user as schemas
import src.services.exceptions as service_exceptions
from src.repositories.users import UsersRepository
from src.services.abstract import BaseService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UsersService(
    BaseService[schemas.UserCreate, schemas.UserRead, schemas.UserUpdate]
):
    repo = UsersRepository()
    create_schema = schemas.UserCreate
    read_schema = schemas.UserRead
    update_schema = schemas.UserUpdate

    async def read_by_email(self, email: str) -> Optional[schemas.UserRead]:
        """
        Retrieve a user by their email address.

        This method attempts to find a user entity in the repository
        using the provided email. If the user is found, the entity is
        validated and returned. If not found, it raises a
        `service_exceptions.EntityNotFoundError`.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            Optional[schemas.UserRead]: The validated user entity if found,
            None otherwise.

        Raises:
            service_exceptions.EntityNotFoundError: If no user is found
            with the provided email.
            service_exceptions.EntityReadError: If an error occurs
            while reading from the repository.
        """
        try:
            entity = await self.repo.read_by_email(email)
            if not entity:
                logger.warning(
                    f"{self.read_schema.__name__} with email {email} not found."
                )
                raise service_exceptions.EntityNotFoundError(
                    self.read_schema.__name__, email
                )

            validated_entity = self.read_schema.model_validate(entity)
            logger.info(
                f"Successfully retrieved {self.read_schema.__name__} with email: {email}"
            )
            return validated_entity
        except repo_exceptions.EntityReadError as e:
            logger.error(
                f"Error reading {self.read_schema.__name__} with email {email}: {str(e)}"
            )
            raise service_exceptions.EntityReadError(
                self.read_schema.__name__, email, str(e)
            )
