from typing import Optional

import src.schemas.position as schemas
from src.repositories.positions import PositionsRepository
from src.services.abstract import BaseService


class PositionsService(
    BaseService[schemas.PositionCreate, schemas.PositionRead, schemas.PositionUpdate]
):
    repo = PositionsRepository()
    create_schema = schemas.PositionCreate
    read_schema = schemas.PositionRead
    update_schema = schemas.PositionUpdate

    async def read_by_name(self, name: str) -> Optional[schemas.PositionRead]:
        entity = await self.repo.read_by_name(name)
        if entity:
            return self.read_schema.model_validate(entity)
        return None
