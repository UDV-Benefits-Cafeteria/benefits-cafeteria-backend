from typing import Optional

import src.schemas.user as schemas
from src.models import LegalEntity, Position
from src.repositories.users import UsersRepository
from src.services.abstract import AbstractService


class UsersService(
    AbstractService[schemas.UserCreate, schemas.UserRead, schemas.UserUpdate]
):
    repo = UsersRepository()
    create_schema = schemas.UserCreate
    read_schema = schemas.UserRead
    update_schema = schemas.UserCreate

    async def get_by_email(self, email: str) -> Optional[schemas.UserRead]:
        entity = await self.repo.find_by_email(email)
        if entity:
            return self.read_schema.model_validate(entity)
        return None

    # Should be in AuthService
    async def update_password(
        self, entity_id: int, password_update: schemas.UserPasswordUpdate
    ) -> bool:
        data = password_update.model_dump()
        return await self.repo.update_one(entity_id, data)

    # Should be in AuthService
    async def verify(self, entity_id: int) -> bool:
        data = {"is_verified": True}
        return await self.repo.update_one(entity_id, data)

    # Should be in PositionsService
    async def get_position_by_name(self, name: str) -> Optional[Position]:
        return await self.repo.get_position_by_name(name)

    # Should be in LegalEntitiesService
    async def get_legal_entity_by_name(self, name: str) -> Optional[LegalEntity]:
        return await self.repo.get_legal_entity_by_name(name)


def get_users_service():
    return UsersService()
