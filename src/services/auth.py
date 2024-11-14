from typing import Optional

from pydantic import EmailStr

import src.repositories.exceptions as repo_exceptions
import src.schemas.user as user_schemas
from src.config import get_settings
from src.db.db import async_session_factory
from src.repositories.users import UsersRepository
from src.services.exceptions import EntityNotFoundError, EntityReadError
from src.utils.security import decode_reset_password_token, hash_password

settings = get_settings()


class AuthService:
    users_repo = UsersRepository()

    async def read_auth_data(
        self, email: Optional[str] = None, user_id: Optional[int] = None
    ) -> Optional[user_schemas.UserAuth]:
        """
        Retrieve authentication data for a user by email or user ID.

        Args:
            email (Optional[str]): The email of the user to look up.
            user_id (Optional[int]): The ID of the user to look up.

        Returns:
            Optional[UserAuth]: An instance of UserAuth if found, otherwise None.
        """
        async with async_session_factory() as session:
            try:
                if email:
                    user = await self.users_repo.read_by_email(session, email)
                elif user_id:
                    user = await self.users_repo.read_by_id(session, user_id)
                else:
                    raise EntityReadError(
                        self.__repr__(), "", "No user_id or email provided"
                    )

                if user is not None:
                    return user_schemas.UserAuth.model_validate(user)
                else:
                    raise EntityNotFoundError(
                        self.__repr__(), email if email else user_id
                    )

            except repo_exceptions.EntityReadError:
                raise EntityReadError(
                    self.__repr__(), email or user_id, "Cannot read user"
                )

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
