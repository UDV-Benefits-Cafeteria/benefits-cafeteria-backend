from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.schemas.legalentity as schemas
import src.services.exceptions as service_exceptions
from src.db.db import async_session_factory
from src.repositories.legal_entities import LegalEntitiesRepository
from src.services.base import BaseService


class LegalEntitiesService(
    BaseService[
        schemas.LegalEntityCreate, schemas.LegalEntityRead, schemas.LegalEntityUpdate
    ]
):
    repo = LegalEntitiesRepository()
    create_schema = schemas.LegalEntityCreate
    read_schema = schemas.LegalEntityRead
    update_schema = schemas.LegalEntityUpdate

    async def read_by_name(self, name: str) -> Optional[schemas.LegalEntityRead]:
        async with async_session_factory() as session:
            try:
                entity = await self.repo.read_by_name(session, name)

            except repo_exceptions.EntityReadError as e:
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        if entity is None:
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"name: {name}"
            )

        return self.read_schema.model_validate(entity)
