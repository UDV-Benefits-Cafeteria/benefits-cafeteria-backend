from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.schemas.category as schemas
import src.services.exceptions as service_exceptions
from src.db.db import async_session_factory
from src.logger import service_logger
from src.repositories.categories import CategoriesRepository
from src.services.base import BaseService


class CategoriesService(
    BaseService[schemas.CategoryCreate, schemas.CategoryRead, schemas.CategoryUpdate]
):
    repo = CategoriesRepository()
    create_schema = schemas.CategoryCreate
    read_schema = schemas.CategoryRead
    update_schema = schemas.CategoryUpdate

    async def read_by_name(self, name: str) -> Optional[schemas.CategoryRead]:
        category_name = name.lower()
        service_logger.info(
            f"Reading {self.read_schema.__name__} by name",
            extra={"entity_name": category_name},
        )

        async with async_session_factory() as session:
            try:
                entity = await self.repo.read_by_name(session, category_name)

            except repo_exceptions.EntityReadError as e:
                service_logger.error(
                    f"Error reading {self.read_schema.__name__} by name",
                    extra={"entity_name": category_name, "error": str(e)},
                )
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        if entity is None:
            service_logger.error(
                f"Entity {self.read_schema.__name__} with name {category_name} not found."
            )
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"name: {category_name}"
            )

        service_logger.info(
            f"Successfully retrieved {self.read_schema.__name__}",
            extra={"entity_name": category_name},
        )
        return self.read_schema.model_validate(entity)
