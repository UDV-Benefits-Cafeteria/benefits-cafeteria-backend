from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.schemas.position as schemas
import src.services.exceptions as service_exceptions
from src.db.db import async_session_factory
from src.repositories.positions import PositionsRepository
from src.services.base import BaseService


class PositionsService(
    BaseService[schemas.PositionCreate, schemas.PositionRead, schemas.PositionUpdate]
):
    repo = PositionsRepository()
    create_schema = schemas.PositionCreate
    read_schema = schemas.PositionRead
    update_schema = schemas.PositionUpdate

    async def read_by_name(self, name: str) -> Optional[schemas.PositionRead]:
        """
        Retrieve a position by its name.

        Args:
            name (str): The name of the position to retrieve.

        Returns:
            Optional[schemas.PositionRead]: An instance of PositionRead if found, otherwise None.
        """
        async with async_session_factory() as session:
            try:
                entity = await self.repo.read_by_name(session, name)

            except repo_exceptions.EntityReadError as e:
                raise service_exceptions.EntityReadError(
                    "Position", f"name: {name}", str(e)
                )

        if entity is None:
            raise service_exceptions.EntityNotFoundError("Position", f"name: {name}")

        return self.read_schema.model_validate(entity)
