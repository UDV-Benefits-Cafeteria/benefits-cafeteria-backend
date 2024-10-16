import logging
from typing import Optional

from sqlalchemy import select

from src.db.db import async_session_factory
from src.models.users import User
from src.repositories.abstract import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UsersRepository(SQLAlchemyRepository[User]):
    model = User

    async def read_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a User by their email address.

        This method queries the database for a User with the specified
        email. If found, it returns the User instance; otherwise, it
        returns None.

        :param email: The email address of the user to retrieve.
        :return: An instance of User if found, None otherwise.
        :raises EntityReadError: Raised when an error occurs during
        the read operation.
        """
        async with async_session_factory() as session:
            try:
                result = await session.execute(
                    select(self.model).where(self.model.email == email)
                )
                user = result.scalar_one_or_none()

                if user:
                    logger.info(f"Found User with email: {email}")
                else:
                    logger.warning(f"No User found with email: {email}")

                return user

            except Exception as e:
                logger.error(f"Error reading User by email '{email}': {e}")
                raise EntityReadError(self.model.__name__, email, str(e))
