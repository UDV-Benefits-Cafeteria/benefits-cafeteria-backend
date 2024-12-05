from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import repository_logger
from src.models import Position
from src.repositories.base import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError


class PositionsRepository(SQLAlchemyRepository[Position]):
    model = Position

    async def read_by_name(
        self, session: AsyncSession, name: str
    ) -> Optional[Position]:
        position_name = name.lower()
        repository_logger.info(
            f"Reading {self.model.__name__} by name: {position_name}"
        )

        try:
            result = await session.execute(
                select(self.model).where(self.model.name == position_name)
            )
            entity = result.scalar_one_or_none()
        except Exception as e:
            repository_logger.error(
                f"Error reading {self.model.__name__} by name='{position_name}': {e}"
            )
            raise EntityReadError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"name: {position_name}",
                str(e),
            )

        if entity:
            repository_logger.info(
                f"Found {self.model.__name__} with name='{position_name}', ID={entity.id}"
            )
        else:
            repository_logger.warning(
                f"{self.model.__name__} with name='{position_name}' not found"
            )
        return entity
