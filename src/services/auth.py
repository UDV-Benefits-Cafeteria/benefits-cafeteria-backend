from typing import Optional

from src.repositories.users import UsersRepository
from src.schemas.user import UserAuth
from src.utils.security import hash_password


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
        if email:
            user = await self.users_repo.read_by_email(email)
        elif user_id:
            user = await self.users_repo.read_by_id(user_id)
        else:
            return None

        if user:
            return UserAuth.model_validate(user)
        return None

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
