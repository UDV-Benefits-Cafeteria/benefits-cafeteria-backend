from typing import Optional

from pydantic import EmailStr

import src.repositories.exceptions as repo_exceptions
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.config import get_settings
from src.db.db import async_session_factory
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
        async with async_session_factory() as session:
            async with session.begin():
                try:
                    user = await self.users_repo.read_by_id(session, user_id)
                except repo_exceptions.EntityReadError as e:
                    raise service_exceptions.EntityReadError(
                        self.__class__.__name__, str(e)
                    )

        if not user:
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"user_id: {user_id}"
            )

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
        async with async_session_factory() as session:
            async with session.begin():
                try:
                    user = await self.users_repo.read_by_email(session, email)
                except repo_exceptions.EntityReadError as e:
                    raise service_exceptions.EntityReadError(
                        self.__class__.__name__, str(e)
                    )

        if not user:
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"email: {email}"
            )

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
        async with async_session_factory() as session:
            async with session.begin():
                hashed_password = hash_password(password)
                data = {"password": hashed_password}
                return await self.users_repo.update_by_id(session, user_id, data)

    async def verify_user(self, user_id: int) -> bool:
        """
        Verify a user's account.

        Args:
            user_id (int): The ID of the user to verify.

        Returns:
            bool: True if the user was successfully verified, otherwise False.
        """
        async with async_session_factory() as session:
            async with session.begin():
                data = {"is_verified": True}
                return await self.users_repo.update_by_id(session, user_id, data)

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
