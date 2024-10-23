from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

import src.repositories.exceptions as repo_exceptions
import src.services.exceptions as service_exceptions
from src.config import logger
from src.repositories.abstract import AbstractRepository

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)


class BaseService(Generic[TCreate, TRead, TUpdate]):
    """
    BaseService is a generic service layer class that provides common CRUD (Create, Read, Update, Delete)
    operations for managing entities. It utilizes a repository to interact with the underlying data store
    and ensures that data is validated through Pydantic schemas.

    Type Parameters:
        TCreate (BaseModel): The Pydantic model for creating new entities.
        TRead (BaseModel): The Pydantic model for reading existing entities.
        TUpdate (BaseModel): The Pydantic model for updating existing entities.

    Attributes:
        repo (AbstractRepository): An instance of the repository that handles data operations.
        create_schema (type[TCreate]): The Pydantic schema used for validating creation data.
        read_schema (type[TRead]): The Pydantic schema used for validating read data.
        update_schema (type[TUpdate]): The Pydantic schema used for validating update data.

    Methods:
        create(create_schema: TCreate) -> TRead:
            Creates a new entity based on the provided schema and returns the created entity.

        create_many(create_schemas: List[TCreate]) -> List[TRead]:
            Creates multiple entities based on the provided schemas and returns the created entities.

        read_by_id(entity_id: int) -> TRead:
            Retrieves a single entity by its ID and returns it as a validated schema.

        read_all() -> List[TRead]:
            Retrieves all entities and returns them as a list of validated schemas.

        update_by_id(entity_id: int, update_schema: TUpdate) -> Optional[TRead]:
            Updates an existing entity by its ID based on the provided update schema and returns the updated entity.

        delete(entity_id: int) -> bool:
            Deletes an entity by its ID and returns a boolean indicating the success of the operation.

    Exceptions:
        Raises service_exceptions.EntityCreateError:
            When an error occurs during entity creation.

        Raises service_exceptions.EntityNotFoundError:
            When an entity with the specified ID is not found during read, update, or delete operations.

        Raises service_exceptions.EntityReadError:
            When an error occurs while reading entities.

        Raises service_exceptions.EntityUpdateError:
            When an error occurs during entity updates.

        Raises service_exceptions.EntityDeletionError:
            When an error occurs during entity deletion.
    """

    repo: AbstractRepository
    create_schema: type(TCreate)
    read_schema: type(TRead)
    update_schema: type(TUpdate)

    async def create(self, create_schema: TCreate) -> TRead:
        """
        Create a new entity and return the created entity's details.

        :param create_schema: Schema containing data for creating a new entity.
        :return: The created entity represented by the read schema.
        :raises service_exceptions.EntityCreateError: Raised when entity creation fails in the service layer.
        """
        try:
            data = create_schema.model_dump(exclude_unset=True)
            entity = await self.repo.create(data)
            validated_entity: TRead = self.read_schema.model_validate(entity)
            logger.info(
                f"Successfully created {self.create_schema.__name__}: {validated_entity}"
            )
            return validated_entity
        except repo_exceptions.EntityCreateError as e:
            logger.error(f"Failed to create {self.create_schema.__name__}: {str(e)}")
            raise service_exceptions.EntityCreateError(
                self.create_schema.__name__, str(e)
            )

    async def create_many(self, create_schemas: List[TCreate]) -> List[TRead]:
        """
        Create multiple entities and return their details.

        :param create_schemas: List of schemas for creating multiple entities.
        :return: List of read schemas representing the created entities.
        :raises service_exceptions.EntityCreateError: Raised when batch creation of entities fails in the service layer.
        """
        try:
            data = [schema.model_dump(exclude_unset=True) for schema in create_schemas]
            entities = await self.repo.create_many(data)
            validated_entities: List[TRead] = [
                self.read_schema.model_validate(entity) for entity in entities
            ]
            logger.info(
                f"Successfully created multiple {self.create_schema.__name__} entities: {validated_entities}"
            )
            return validated_entities
        except repo_exceptions.EntityCreateError as e:
            logger.error(
                f"Failed to create multiple {self.create_schema.__name__}: {str(e)}"
            )
            raise service_exceptions.EntityCreateError(
                self.create_schema.__name__, str(e)
            )

    async def read_by_id(self, entity_id: int) -> TRead:
        """
        Retrieve a single entity by its ID.

        :param entity_id: ID of the entity to retrieve.
        :return: Schema representing the retrieved entity.
        :raises service_exceptions.EntityNotFoundError: Raised when the entity is not found.
        :raises service_exceptions.EntityReadError: Raised when an error occurs while reading the entity.
        """
        try:
            entity = await self.repo.read_by_id(entity_id)
            if not entity:
                logger.warning(
                    f"{self.read_schema.__name__} with ID {entity_id} not found."
                )
                raise service_exceptions.EntityNotFoundError(
                    self.read_schema.__name__, entity_id
                )

            validated_entity = self.read_schema.model_validate(entity)
            logger.info(
                f"Successfully retrieved {self.read_schema.__name__} with ID: {entity_id}"
            )
            return validated_entity
        except repo_exceptions.EntityReadError as e:
            logger.error(
                f"Error reading {self.read_schema.__name__} with ID {entity_id}: {str(e)}"
            )
            raise service_exceptions.EntityReadError(
                self.read_schema.__name__, entity_id, str(e)
            )

    async def read_all(self, page: int = 1, limit: int = 10) -> List[TRead]:
        """
        Retrieve all entities.

        :return: List of schemas representing all entities.
        :raises service_exceptions.EntityReadError: Raised when an error occurs while reading entities.
        """
        try:
            entities = await self.repo.read_all(page, limit)
            validated_entities = [self.read_schema.model_validate(e) for e in entities]
            logger.info(
                f"Successfully retrieved all {self.read_schema.__name__} entities."
            )
            return validated_entities
        except repo_exceptions.EntityReadError as e:
            logger.error(
                f"Error reading all {self.read_schema.__name__} entities: {str(e)}"
            )
            raise service_exceptions.EntityReadError(
                self.read_schema.__name__, e.read_param, str(e)
            )

    async def update_by_id(
        self, entity_id: int, update_schema: TUpdate
    ) -> Optional[TRead]:
        """
        Update an existing entity and return the updated entity's details if successful.

        :param entity_id: ID of the entity to be updated.
        :param update_schema: Schema containing data to update the entity.
        :return: The updated entity represented by the read schema if successful, otherwise None.
        :raises service_exceptions.EntityNotFoundError: Raised when the entity to be updated is not found.
        :raises service_exceptions.EntityUpdateError: Raised when the entity update fails.
        """
        try:
            data: dict = update_schema.model_dump(exclude_unset=True)
            is_updated: bool = await self.repo.update_by_id(entity_id, data)
            if not is_updated:
                logger.warning(
                    f"{self.read_schema.__name__} with ID {entity_id} not found for update."
                )
                raise service_exceptions.EntityNotFoundError(
                    self.read_schema.__name__, entity_id
                )

            logger.info(
                f"Successfully updated {self.read_schema.__name__} with ID: {entity_id}"
            )
            return await self.read_by_id(entity_id)
        except repo_exceptions.EntityUpdateError as e:
            logger.error(
                f"Failed to update {self.read_schema.__name__} with ID {entity_id}: {str(e)}"
            )
            raise service_exceptions.EntityUpdateError(
                self.read_schema.__name__, e.read_param, str(e)
            )

    async def delete_by_id(self, entity_id: int) -> bool:
        """
        Delete an entity by its ID.

        :param entity_id: ID of the entity to be deleted.
        :return: True if the delete operation was successful, False otherwise.
        :raises service_exceptions.EntityNotFoundError: Raised when the entity to be deleted is not found.
        :raises service_exceptions.EntityDeletionError: Raised when the entity deletion fails.
        """
        is_deleted: bool = await self.repo.delete_by_id(entity_id)
        if not is_deleted:
            logger.warning(
                f"{self.read_schema.__name__} with ID {entity_id} not found for deletion."
            )
            raise service_exceptions.EntityNotFoundError(
                self.read_schema.__name__, entity_id
            )

        logger.info(
            f"Successfully deleted {self.read_schema.__name__} with ID: {entity_id}"
        )
        return is_deleted
