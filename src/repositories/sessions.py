from datetime import datetime
from typing import cast

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import logger
from src.models import Session
from src.repositories.base import SQLAlchemyRepository
from src.repositories.exceptions import EntityDeleteError


class SessionsRepository(SQLAlchemyRepository[Session]):
    model = Session
    primary_key = "session_id"

    async def delete_expired_sessions(
        self, session: AsyncSession, current_time: datetime
    ) -> int:
        """
        Delete all expired sessions.

        :return: Number of deleted sessions.
        """
        try:
            result = await session.execute(
                delete(self.model).where(self.model.expires_at < current_time)
            )

            await session.commit()

            rowcount: int = cast(int, result.rowcount)
            return rowcount
        except Exception as e:
            logger.error(f"Error deleting expired sessions: {e}")
            raise EntityDeleteError(self.model.__name__, "expired sessions", str(e))
