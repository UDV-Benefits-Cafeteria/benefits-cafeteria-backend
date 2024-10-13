from typing import Optional

from src.repositories.users import UsersRepository
from src.schemas.user import UserAuth
from src.utils.security import hash_password


class AuthService:
    users_repo = UsersRepository()

    async def get_auth_data(
        self, email: Optional[str] = None, user_id: Optional[int] = None
    ) -> Optional[UserAuth]:
        if email:
            user = await self.users_repo.find_by_email(email)
        elif user_id:
            user = await self.users_repo.find_one(user_id)
        else:
            return None

        if user:
            return UserAuth.model_validate(user)
        return None

    async def update_password(self, user_id: int, password: str) -> bool:
        hashed_password = hash_password(password)
        data = {"password": hashed_password}
        print(f"Updating password for user {user_id}, {data}")
        return await self.users_repo.update_one(user_id, data)

    async def verify_user(self, user_id: int) -> bool:
        data = {"is_verified": True}
        return await self.users_repo.update_one(user_id, data)
