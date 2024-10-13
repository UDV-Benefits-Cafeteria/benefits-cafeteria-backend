from typing import Optional

from sqlalchemy import select

from src.db.db import async_session_factory
from src.models import Position
from src.repositories.abstract import SQLAlchemyRepository


class PositionsRepository(SQLAlchemyRepository[Position]):
    model = Position

    async def find_by_name(self, name: str) -> Optional[Position]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.name == name)
            )
            return result.scalar_one_or_none()
