from typing import Optional

from pydantic import EmailStr

import src.repositories.exceptions as repo_exceptions
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.config import get_settings
from src.db.db import async_session_factory, get_transaction_session
from src.logger import service_logger
from src.repositories.users import UsersRepository
from src.utils.security import decode_reset_password_token, hash_password

settings = get_settings()


class AuthService:
    users_repo = UsersRepository()

    async def read_auth_data_by_id(
        self, user_id: int
    ) -> Optional[user_schemas.UserAuth]:
        """
        Retrieve authentication data for a user by user ID.

        Args:
            user_id (int): The ID of the user to look up.

        Returns:
            Optional[UserAuth]: An instance of UserAuth if found, otherwise None.
        """
        service_logger.info(f"Attempting to retrieve auth data for user_id: {user_id}")

        async with async_session_factory() as session:
            try:
                user = await self.users_repo.read_by_id(session, user_id)
            except repo_exceptions.EntityReadError as e:
                service_logger.error(
                    f"Error reading user auth data for user_id: {user_id}, error: {str(e)}"
                )
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        if not user:
            service_logger.error(f"User with user_id {user_id} not found.")
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"user_id: {user_id}"
            )

        service_logger.info(f"Successfully retrieved auth data for user_id: {user_id}")
        return user_schemas.UserAuth.model_validate(user)

    async def read_auth_data_by_email(
        self, email: Optional[str] = None
    ) -> Optional[user_schemas.UserAuth]:
        """
        Retrieve authentication data for a user by email or user ID.

        Args:
            email (str): The email of the user to look up.

        Returns:
            Optional[UserAuth]: An instance of UserAuth if found, otherwise None.
        """
        service_logger.info(f"Attempting to retrieve auth data for email: {email}")

        async with async_session_factory() as session:
            try:
                user = await self.users_repo.read_by_email(session, email)
            except repo_exceptions.EntityReadError as e:
                service_logger.error(
                    f"Error reading user auth data for email: {email}, error: {str(e)}"
                )
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        if not user:
            service_logger.error(f"User with email {email} not found.")
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"email: {email}"
            )

        service_logger.info(f"Successfully retrieved auth data for email: {email}")
        return user_schemas.UserAuth.model_validate(user)

    async def update_password(self, user_id: int, password: str) -> bool:
        """
        Update the user's password.

        Args:
            user_id (int): The ID of the user.
            password (str): The new password to set.

        Returns:
            bool: True if the password was successfully updated, otherwise False.
        """
        service_logger.info(f"Updating password for user_id: {user_id}")

        async with get_transaction_session() as session:
            try:
                hashed_password = hash_password(password)
                data = {"password": hashed_password}
                updated_user = await self.users_repo.update_by_id(
                    session, user_id, data
                )

            except repo_exceptions.EntityUpdateError as e:
                service_logger.error(
                    f"Failed to update password for user_id: {user_id}, error: {str(e)}"
                )
                raise service_exceptions.EntityUpdateError(
                    "AuthService",
                    f"Failed to update password for user with id {user_id}, error: {str(e)}",
                )

            service_logger.info(f"Password updated successfully for user_id: {user_id}")
            return updated_user

    async def verify_user(self, user_id: int) -> bool:
        """
        Verify a user's account.

        Args:
            user_id (int): The ID of the user to verify.

        Returns:
            bool: True if the user was successfully verified, otherwise False.
        """
        service_logger.info(f"Verifying user_id: {user_id}")

        async with get_transaction_session() as session:
            try:
                data = {"is_verified": True}
                updated_user = await self.users_repo.update_by_id(
                    session, user_id, data
                )

            except repo_exceptions.EntityUpdateError as e:
                service_logger.error(
                    f"Failed to verify user_id: {user_id}, error: {str(e)}"
                )
                raise service_exceptions.EntityUpdateError(
                    "AuthService",
                    f"Failed to set is_verified to True for user with id {user_id}, error: {str(e)}",
                )

        service_logger.info(f"User verification successful for user_id: {user_id}")
        return updated_user

    @staticmethod
    async def verify_reset_password_data(
        rfp: user_schemas.UserResetForgetPassword,
    ) -> Optional[EmailStr]:
        """
        Verify the reset password token and password confirmation.

        - rfp: Contains the reset token, new password, and password confirmation.

        Returns:
        - EmailStr: The email associated with the reset token if valid.
        - None If the token is invalid or the passwords do not match.

        Details:
        - Decodes the reset token to retrieve the email.
        - Ensures that the new password matches the confirmation password.
        """
        email = decode_reset_password_token(token=rfp.secret_token)
        if email is None or rfp.new_password != rfp.confirm_password:
            return None
        return email
