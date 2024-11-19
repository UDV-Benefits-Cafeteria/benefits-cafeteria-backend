from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        except Exception as e:
            raise EntityReadError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"name: {name}",
                str(e),
            )

        return position
