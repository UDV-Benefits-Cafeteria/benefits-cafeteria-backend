from typing import Optional

from sqlalchemy import select

from src.db.db import async_session_factory
from src.models.users import User
from src.repositories.abstract import SQLAlchemyRepository


class UsersRepository(SQLAlchemyRepository[User]):
    model = User

    async def find_by_email(self, email: str) -> Optional[User]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.email == email)
            )
            return result.scalar_one_or_none()
