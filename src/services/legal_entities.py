from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.schemas.legalentity as schemas
import src.services.exceptions as service_exceptions
from src.db.db import async_session_factory
from src.logger import service_logger
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
        service_logger.info(
            f"Reading {self.read_schema.__name__} by name", extra={"entity_name": name}
        )

        async with async_session_factory() as session:
            try:
                entity = await self.repo.read_by_name(session, name)

            except repo_exceptions.EntityReadError as e:
                service_logger.error(
                    f"Error reading {self.read_schema.__name__} by name",
                    extra={"entity_name": name, "error": str(e)},
                )
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        if entity is None:
            service_logger.error(
                f"Entity {self.read_schema.__name__} with name {name} not found."
            )
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"name: {name}"
            )

        service_logger.info(
            f"Successfully retrieved {self.read_schema.__name__}",
            extra={"entity_name": name},
        )
        return self.read_schema.model_validate(entity)
