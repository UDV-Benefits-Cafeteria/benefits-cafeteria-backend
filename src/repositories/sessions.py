from datetime import datetime

from sqlalchemy import delete

from src.config import logger
from src.db.db import async_session_factory
from src.models import Session
from src.repositories.abstract import SQLAlchemyRepository
from src.repositories.exceptions import EntityDeleteError


class SessionsRepository(SQLAlchemyRepository[Session]):
    model = Session
    primary_key = "session_id"

    async def delete_expired_sessions(self, current_time: datetime) -> int:
        """
        Delete all expired sessions.

        :return: Number of deleted sessions.
        """
        async with async_session_factory() as session:
            try:
                result = await session.execute(
                    delete(self.model).where(self.model.expires_at < current_time)
                )

                await session.commit()

                return result.rowcount
            except Exception as e:
                logger.error(f"Error deleting expired sessions: {e}")
                raise EntityDeleteError(self.model.__name__, "expired sessions", str(e))
