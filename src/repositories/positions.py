from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import logger
from src.models import Position
from src.repositories.base import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError


class PositionsRepository(SQLAlchemyRepository[Position]):
    model = Position

    async def read_by_name(
        self, session: AsyncSession, name: str
    ) -> Optional[Position]:
        try:
            result = await session.execute(
                select(self.model).where(self.model.name == name)
            )
            position = result.scalar_one_or_none()

            if position:
                logger.info(f"Found Position with name: {name}")
            else:
                logger.warning(f"No Position found with name: {name}")

            return position

        except Exception as e:
            logger.error(f"Error reading Position by name '{name}': {e}")
            raise EntityReadError(self.model.__name__, name, str(e))
