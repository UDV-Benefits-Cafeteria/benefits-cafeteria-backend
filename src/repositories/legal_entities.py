import logging
from typing import Optional

from sqlalchemy import select

from src.db.db import async_session_factory
from src.models import LegalEntity
from src.repositories.abstract import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalEntitiesRepository(SQLAlchemyRepository[LegalEntity]):
    model = LegalEntity

    async def read_by_name(self, name: str) -> Optional[LegalEntity]:
        """
        Retrieve a LegalEntity by its name.

        This method queries the database for a LegalEntity with the
        specified name. If found, it returns the LegalEntity instance;
        otherwise, it returns None.

        :param name: The name of the legal entity to retrieve.
        :return: An instance of LegalEntity if found, None otherwise.
        :raises EntityReadError: Raised when an error occurs during
        the read operation.
        """
        async with async_session_factory() as session:
            try:
                result = await session.execute(
                    select(self.model).where(self.model.name == name)
                )
                entity = result.scalar_one_or_none()

                if entity:
                    logger.info(f"Found LegalEntity with name: {name}")
                else:
                    logger.warning(f"No LegalEntity found with name: {name}")

                return entity

            except Exception as e:
                logger.error(f"Error reading LegalEntity by name '{name}': {e}")
                raise EntityReadError(self.model.__name__, name, str(e))
