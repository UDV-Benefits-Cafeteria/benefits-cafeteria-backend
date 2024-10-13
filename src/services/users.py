from typing import Optional

import src.schemas.user as schemas
from src.repositories.users import UsersRepository
from src.services.abstract import AbstractService


class UsersService(
    AbstractService[schemas.UserCreate, schemas.UserRead, schemas.UserUpdate]
):
    repo = UsersRepository()
    create_schema = schemas.UserCreate
    read_schema = schemas.UserRead
    update_schema = schemas.UserUpdate

    async def get_by_email(self, email: str) -> Optional[schemas.UserRead]:
        entity = await self.repo.find_by_email(email)
        if entity:
            return self.read_schema.model_validate(entity)
        return None
