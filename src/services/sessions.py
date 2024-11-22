import uuid
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.services.exceptions as service_exceptions
from src.db.db import async_session_factory, get_transaction_session
from src.logger import service_logger
from src.repositories.sessions import SessionsRepository
from src.schemas.session import SessionRead


class SessionsService:
    repo = SessionsRepository()

    async def create_session(self, user_id: int, expires_in: int) -> str:
        """
        Create a new session for a user.

        Generates a unique session ID and CSRF token, sets an expiration time
        based on the provided duration, and stores the session data in the database.

        Args:
            user_id (int): The ID of the user for whom the session is created.
            expires_in (int): The duration in seconds for which the session is valid.

        Returns:
            str: The unique session ID for the created session.
        """
        service_logger.info("Creating session", extra={"user_id": user_id})

        session_id = str(uuid.uuid4())
        csrf_token = token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        data = {
            "session_id": session_id,
            "user_id": user_id,
            "expires_at": expires_at,
            "csrf_token": csrf_token,
        }

        async with get_transaction_session() as async_session:
            try:
                session = await self.repo.create(session=async_session, data=data)

            except repo_exceptions.EntityCreateError as e:
                service_logger.error(
                    "Failed to create session",
                    extra={"user_id": user_id, "error": str(e)},
                )
                raise service_exceptions.EntityCreateError(
                    self.__class__.__name__, str(e)
                )

        service_logger.info(
            "Session created successfully",
            extra={"session_id": session_id, "user_id": user_id},
        )
        return session.session_id

    async def get_session(self, session_id: str) -> Optional[SessionRead]:
        service_logger.info("Retrieving session", extra={"session_id": session_id})

        async with async_session_factory() as async_session:
            try:
                session = await self.repo.read_by_id(async_session, session_id)

            except repo_exceptions.EntityReadError as e:
                service_logger.error(
                    "Failed to retrieve session",
                    extra={"session_id": session_id, "error": str(e)},
                )
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        if not session or session.expires_at <= datetime.now(timezone.utc):
            service_logger.warning(
                "Session is either expired or does not exist",
                extra={"session_id": session_id},
            )
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
        service_logger.info(
            "Updating session expiration",
            extra={"session_id": session_id, "new_expires_at": new_expires_at},
        )

        if new_expires_at <= datetime.now(timezone.utc):
            service_logger.error(
                "Cannot set expiration time in the past",
                extra={"session_id": session_id, "new_expires_at": new_expires_at},
            )
            raise ValueError("Expiration time cannot be in the past.")

        data = {"expires_at": new_expires_at, "csrf_token": new_csrf_token}
        async with get_transaction_session() as async_session:
            try:
                is_updated = await self.repo.update_by_id(
                    async_session, session_id, data
                )
            except repo_exceptions.EntityUpdateError as e:
                service_logger.error(
                    "Failed to update session",
                    extra={"session_id": session_id, "error": str(e)},
                )
                raise service_exceptions.EntityUpdateError(
                    self.__class__.__name__, str(e)
                )

        if not is_updated:
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"session_id: {session_id}"
            )

        service_logger.info(
            "Session updated successfully", extra={"session_id": session_id}
        )
        return True

    async def delete_session(self, session_id: str) -> bool:
        service_logger.info("Deleting session", extra={"session_id": session_id})

        async with get_transaction_session() as async_session:
            try:
                is_deleted = await self.repo.delete_by_id(async_session, session_id)

            except repo_exceptions.EntityDeleteError as e:
                service_logger.error(
                    "Failed to delete session",
                    extra={"session_id": session_id, "error": str(e)},
                )
                raise service_exceptions.EntityDeleteError(
                    self.__class__.__name__, str(e)
                )

        if not is_deleted:
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"session_id: {session_id}"
            )

        service_logger.info(
            "Session deleted successfully", extra={"session_id": session_id}
        )
        return True

    async def get_csrf_token(self, session_id: str) -> Optional[str]:
        service_logger.info("Retrieving CSRF token", extra={"session_id": session_id})

        session = await self.get_session(session_id)

        if not session:
            service_logger.warning(
                "Failed to retrieve CSRF token; session not found or expired",
                extra={"session_id": session_id},
            )

        return session.csrf_token

    async def cleanup_expired_sessions(self) -> int:
        """
        Delete all expired sessions.
        :return: Number of deleted sessions.
        """
        service_logger.info("Cleaning up expired sessions")

        current_time = datetime.now(timezone.utc)
        async with get_transaction_session() as async_session:
            try:
                deleted_count = await self.repo.delete_expired_sessions(
                    async_session, current_time
                )

            except repo_exceptions.EntityDeleteError as e:
                service_logger.error(
                    "Failed to clean up expired sessions", extra={"error": str(e)}
                )
                raise service_exceptions.EntityDeleteError("SessionService", str(e))

        service_logger.info(
            "Expired sessions cleaned up",
            extra={"deleted_count": deleted_count},
        )
        return deleted_count
