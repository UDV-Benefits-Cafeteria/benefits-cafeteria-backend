import uuid
from datetime import datetime, timedelta, timezone

from src.models import Session
from src.repositories.abstract import SQLAlchemyRepository


class SessionsRepository(SQLAlchemyRepository[Session]):
    model = Session
    primary_key = "session_id"

    async def create_session(self, user_id: int, expires_in: int) -> str:
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        data = {
            "session_id": session_id,
            "user_id": user_id,
            "expires_at": expires_at,
        }
        await self.add_one(data)
        return session_id
