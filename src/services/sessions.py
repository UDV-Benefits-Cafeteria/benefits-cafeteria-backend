import uuid
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.services.exceptions as service_exceptions
from src.db.db import async_session_factory
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

        async with async_session_factory() as async_session:
            try:
                async with async_session.begin():
                    session = await self.repo.create(session=async_session, data=data)
            except repo_exceptions.EntityCreateError as e:
                raise service_exceptions.EntityCreateError(
                    self.__class__.__name__, str(e)
                )

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
        async with async_session_factory() as async_session:
            try:
                async with async_session.begin():
                    session = await self.repo.read_by_id(async_session, session_id)
            except repo_exceptions.EntityReadError as e:
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        if not session or session.expires_at <= datetime.now(timezone.utc):
            return None
        return SessionRead.model_validate(session)

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
        async with async_session_factory() as async_session:
            try:
                async with async_session.begin():
                    is_updated = await self.repo.update_by_id(
                        async_session, session_id, data
                    )
            except repo_exceptions.EntityUpdateError as e:
                raise service_exceptions.EntityUpdateError(
                    self.__class__.__name__, str(e)
                )

        if not is_updated:
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"session_id: {session_id}"
            )
        return True

    async def delete_session(self, session_id: str) -> bool:
        async with async_session_factory() as async_session:
            try:
                async with async_session.begin():
                    is_deleted = await self.repo.delete_by_id(async_session, session_id)
            except repo_exceptions.EntityDeleteError as e:
                raise service_exceptions.EntityDeleteError(
                    self.__class__.__name__, str(e)
                )

        if not is_deleted:
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"session_id: {session_id}"
            )
        return True

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
        return session.csrf_token

    async def cleanup_expired_sessions(self) -> int:
        """
        Delete all expired sessions.
        :return: Number of deleted sessions.
        """
        current_time = datetime.now(timezone.utc)
        async with async_session_factory() as async_session:
            async with async_session.begin():
                deleted_count = await self.repo.delete_expired_sessions(
                    async_session, current_time
                )
        return deleted_count
