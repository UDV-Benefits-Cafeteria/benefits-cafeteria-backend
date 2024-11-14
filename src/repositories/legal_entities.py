from typing import Optional

from sqlalchemy import select

from src.config import logger
from src.db.db import async_session_factory
from src.models import LegalEntity
from src.repositories.base import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError


class LegalEntitiesRepository(SQLAlchemyRepository[LegalEntity]):
    model = LegalEntity

    async def read_by_name(self, name: str) -> Optional[LegalEntity]:
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
