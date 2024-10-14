from datetime import datetime, timezone
from typing import Optional

from src.repositories.sessions import SessionsRepository
from src.schemas.session import SessionRead


class SessionsService:
    repo = SessionsRepository()

    async def create_session(self, user_id: int, expires_in: int) -> str:
        session_id = await self.repo.create_session(user_id, expires_in)
        return session_id

    async def get_session(self, session_id: str) -> Optional[SessionRead]:
        session = await self.repo.find_one(session_id)
        if session and session.expires_at > datetime.now(timezone.utc):
            return SessionRead.model_validate(session)
        return None

    async def delete_session(self, session_id: str) -> bool:
        return await self.repo.delete_one(session_id)

    async def update_session_expiration(self, session_id: str, new_expires_at: datetime) -> bool:
        data = {"expires_at": new_expires_at}
        return await self.repo.update_one(session_id, data)
