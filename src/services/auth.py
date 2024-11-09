from typing import Optional

from pydantic import EmailStr

import src.repositories.exceptions as repo_exceptions
import src.schemas.email as email_schemas
from src.config import get_settings
from src.repositories.users import UsersRepository
from src.schemas.user import UserAuth, UserResetForgetPassword
from src.services.exceptions import EntityNotFoundError, EntityReadError
from src.utils.security import (
    create_reset_password_token,
    decode_reset_password_token,
    hash_password,
)

settings = get_settings()


class AuthService:
    users_repo = UsersRepository()

    async def read_auth_data(
        self, email: Optional[str] = None, user_id: Optional[int] = None
    ) -> Optional[UserAuth]:
        """
        Retrieve authentication data for a user by email or user ID.

        Args:
            email (Optional[str]): The email of the user to look up.
            user_id (Optional[int]): The ID of the user to look up.

        Returns:
            Optional[UserAuth]: An instance of UserAuth if found, otherwise None.
        """
        try:
            if email:
                user = await self.users_repo.read_by_email(email)
            elif user_id:
                user = await self.users_repo.read_by_id(user_id)
            else:
                raise EntityReadError(
                    self.__repr__(), "", "No user_id or email provided"
                )

            if user is not None:
                return UserAuth.model_validate(user)
            else:
                raise EntityNotFoundError(self.__repr__(), email if email else user_id)

        except repo_exceptions.EntityReadError:
            raise EntityReadError(self.__repr__(), email or user_id, "Cannot read user")

    async def update_password(self, user_id: int, password: str) -> bool:
        """
        Update the user's password.

        Args:
            user_id (int): The ID of the user.
            password (str): The new password to set.

        Returns:
            bool: True if the password was successfully updated, otherwise False.
        """
        hashed_password = hash_password(password)
        data = {"password": hashed_password}
        return await self.users_repo.update_by_id(user_id, data)

    async def verify_user(self, user_id: int) -> bool:
        """
        Verify a user's account.

        Args:
            user_id (int): The ID of the user to verify.

        Returns:
            bool: True if the user was successfully verified, otherwise False.
        """
        data = {"is_verified": True}
        return await self.users_repo.update_by_id(user_id, data)

    @staticmethod
    async def send_forget_password_email(email: EmailStr):
        """
        Send a password reset email to the specified email address.

        - email: The email address to which the password reset link will be sent.

        Details:
        - Generates a password reset token and includes it in a reset URL.
        - Uses the background mail sending task to send an email with a reset link.
        """
        secret_token = create_reset_password_token(email=email)

        email = email_schemas.EmailSchema.model_validate(
            {
                "email": [email],
                "body": {
                    "reset_url": f"https://{settings.DOMAIN}/reset-password?token={secret_token}",
                },
            }
        )

        background_send_mail.delay(
            email.model_dump(),
            f"Смена пароля на сайте {settings.APP_TITLE}",
            "reset-password.html",
        )

    @staticmethod
    async def verify_reset_password_data(
        rfp: UserResetForgetPassword,
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
