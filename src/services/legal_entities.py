from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.schemas.legalentity as schemas
import src.services.exceptions as service_exceptions
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
        """
        Retrieve a legal entity by its name.

        Args:
            name (str): The name of the legal entity to retrieve.

        Returns:
            Optional[schemas.LegalEntityRead]: An instance of LegalEntityRead if found, otherwise None.
        """
        try:
            entity = await self.repo.read_by_name(name)

        except repo_exceptions.EntityReadError as e:
            raise service_exceptions.EntityReadError(
                "Legal Entity", f"name: {name}", str(e)
            )

        if entity is None:
            raise service_exceptions.EntityNotFoundError(
                "Legal Entity", f"name: {name}"
            )

        return self.read_schema.model_validate(entity)
