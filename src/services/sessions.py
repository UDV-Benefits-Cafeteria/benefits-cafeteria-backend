import uuid
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

from src.repositories.sessions import SessionsRepository
from src.schemas.session import SessionRead


class SessionsService:
    repo = SessionsRepository()

    async def create_session(self, user_id: int, expires_in: int) -> str:
        """
        Create a new session for a user.

        Generates a unique session ID and CSRF token, sets an expiration time
        based on the provided duration, and stores the session data in the repository.

        Args:
            user_id (int): The ID of the user for whom the session is created.
            expires_in (int): The duration in seconds for which the session is valid.

        Returns:
            str: The unique session ID for the created session.
        """
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
        """
        Retrieve a session by its ID.

        Checks if the session exists and has not expired. If valid, returns
        the session data.

        Args:
            session_id (str): The ID of the session to retrieve.

        Returns:
            Optional[SessionRead]: The session data if found and valid, None otherwise.
        """
        session = await self.repo.read_by_id(session_id)
        if session and session.expires_at > datetime.now(timezone.utc):
            return SessionRead.model_validate(session)
        return None

    async def get_csrf_token(self, session_id: str) -> Optional[str]:
        """
        Get the CSRF token for a given session ID.

        Retrieves the session and returns the associated CSRF token if the session
        is valid.

        Args:
            session_id (str): The ID of the session for which to retrieve the CSRF token.

        Returns:
            Optional[str]: The CSRF token if the session is valid, None otherwise.
        """
        session = await self.get_session(session_id)
        if session:
            return session.csrf_token
        return None

    async def update_session_expiration(
        self, session_id: str, new_expires_at: datetime, new_csrf_token: str
    ) -> bool:
        """
        Update the expiration time and CSRF token for an existing session.

        This method modifies the session data in the repository with new expiration
        details.

        Args:
            session_id (str): The ID of the session to update.
            new_expires_at (datetime): The new expiration time for the session.
            new_csrf_token (str): The new CSRF token for the session.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        data = {"expires_at": new_expires_at, "csrf_token": new_csrf_token}
        return await self.repo.update_by_id(session_id, data)

    async def delete_session(self, session_id: str) -> bool:
        return await self.repo.delete_by_id(session_id)
