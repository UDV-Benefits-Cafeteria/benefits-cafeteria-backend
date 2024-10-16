import uuid
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

from src.repositories.sessions import SessionsRepository
from src.schemas.session import SessionRead


class SessionsService:
    repo = SessionsRepository()

    async def create_session(self, user_id: int, expires_in: int) -> str:
        session_id = str(uuid.uuid4())
        csrf_token = token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        data = {
            "session_id": session_id,
            "user_id": user_id,
            "expires_at": expires_at,
            "csrf_token": csrf_token,
        }
        session = await self.repo.create(data)
        return session.session_id

    async def get_session(self, session_id: str) -> Optional[SessionRead]:
        session = await self.repo.read_by_id(session_id)
        if session and session.expires_at > datetime.now(timezone.utc):
            return SessionRead.model_validate(session)
        return None

    async def get_csrf_token(self, session_id: str) -> Optional[str]:
        session = await self.get_session(session_id)
        if session:
            return session.csrf_token
        return None

    async def update_session_expiration(
        self, session_id: str, new_expires_at: datetime, new_csrf_token: str
    ) -> bool:
        data = {"expires_at": new_expires_at, "csrf_token": new_csrf_token}
        return await self.repo.update_by_id(session_id, data)

    async def delete_session(self, session_id: str) -> bool:
        return await self.repo.delete_by_id(session_id)
