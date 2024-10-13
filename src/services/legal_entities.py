from typing import Optional

import src.schemas.legalentity as schemas
from src.repositories.legal_entities import LegalEntitiesRepository
from src.services.abstract import AbstractService


class LegalEntitiesService(
    AbstractService[
        schemas.LegalEntityCreate, schemas.LegalEntityRead, schemas.LegalEntityUpdate
    ]
):
    repo = LegalEntitiesRepository()
    create_schema = schemas.LegalEntityCreate
    read_schema = schemas.LegalEntityRead
    update_schema = schemas.LegalEntityUpdate

    async def get_by_name(self, name: str) -> Optional[schemas.LegalEntityRead]:
        entity = await self.repo.find_by_name(name)
        if entity:
            return self.read_schema.model_validate(entity)
        return None
