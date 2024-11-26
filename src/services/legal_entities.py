from typing import Any, Optional

from pydantic import BaseModel

import src.repositories.exceptions as repo_exceptions
import src.schemas.legalentity as schemas
import src.services.exceptions as service_exceptions
from src.db.db import async_session_factory
from src.logger import service_logger
from src.repositories.legal_entities import LegalEntitiesRepository
from src.services.base import BaseService
from src.utils.parser.excel_parser import initialize_excel_parser


class LegalEntitiesService(
    BaseService[
        schemas.LegalEntityCreate, schemas.LegalEntityRead, schemas.LegalEntityUpdate
    ]
):
    repo = LegalEntitiesRepository()
    create_schema = schemas.LegalEntityCreate
    read_schema = schemas.LegalEntityRead
    update_schema = schemas.LegalEntityUpdate

    async def parse_legal_entities_from_excel(
        self,
        file_contents: bytes,
    ) -> tuple[list[BaseModel], list[dict[str, Any]]]:
        """
        Parses legal entities from an Excel file.

        Args:
            file_contents (bytes): The raw bytes of the uploaded Excel file.

        Returns:
            tuple[list[BaseModel], list[dict[str, Any]]]:
                A tuple containing a list of valid Legal Entity instances and a list of error dictionaries.
        """
        parser = initialize_excel_parser(
            model_class=schemas.LegalEntityCreate,
            field_mappings={
                "name": ["название", "имя", "юридическое лицо"],
            },
            required_fields=["name"],
            field_parsers={},
        )

        valid_entities, parse_errors = parser.parse_excel(file_contents)

        # Check for duplicates in the file
        name_set = set()
        duplicates = []

        # If we remove an item from the list we're iterating over,
        # the next item might be skipped because the indices shift so we use .copy() to prevent that
        for idx, entity in enumerate(valid_entities.copy(), start=2):
            if entity.name in name_set:
                duplicates.append(
                    {
                        "row": idx,
                        "error": f"Duplicate legal entity name '{entity.name}' in Excel file.",
                    }
                )
                valid_entities.remove(entity)
            else:
                name_set.add(entity.name)

        parse_errors.extend(duplicates)

        # Check for existing legal entities in the database
        existing_entities = []
        for idx, entity in enumerate(valid_entities.copy(), start=2):
            try:
                await self.read_by_name(entity.name)
                existing_entities.append(
                    {
                        "row": idx,
                        "error": f"Legal entity '{entity.name}' already exists.",
                    }
                )
                valid_entities.remove(entity)
            except service_exceptions.EntityNotFoundError:
                continue  # Entity does not exist so it's valid

        parse_errors.extend(existing_entities)

        return valid_entities, parse_errors

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
