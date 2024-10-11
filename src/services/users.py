from typing import Optional

import src.schemas.user as schemas
from src.models import User
from src.services.abstract import AbstractService


class UsersService(
    AbstractService[schemas.UserCreate, schemas.UserRead, schemas.UserUpdate]
):
    async def get_by_email(self, email: str) -> Optional[schemas.UserRead]:
        entity = await self.repo.find_by_email(email)
        if entity:
            return self.read_schema.model_validate(entity)
        return None

    async def get_model_by_email(self, email: str) -> Optional[User]:
        return await self.repo.find_by_email(email)

    async def update_password_and_verify(
        self, id: int, password_update: schemas.UserPasswordUpdate
    ) -> bool:
        data = password_update.model_dump()
        data["is_verified"] = True
        return await self.repo.update_one(id, data)
