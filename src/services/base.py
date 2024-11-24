from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

import src.repositories.exceptions as repo_exceptions
import src.services.exceptions as service_exceptions
from src.db.db import async_session_factory, get_transaction_session
from src.logger import service_logger
from src.repositories.base import SQLAlchemyRepository

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

        Raises service_exceptions.EntityDeleteError:
            When an error occurs during entity deletion.
    """

    repo: SQLAlchemyRepository
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
        service_logger.info(f"Creating {self.create_schema.__name__} entity.")

        data = create_schema.model_dump(exclude_unset=True)

        async with get_transaction_session() as session:
            try:
                entity = await self.repo.create(session, data)

            except repo_exceptions.EntityCreateError as e:
                service_logger.error(
                    f"Error creating {self.create_schema.__name__}: {str(e)}"
                )
                raise service_exceptions.EntityCreateError(
                    self.__class__.__name__, str(e)
                )

        service_logger.info(f"Successfully created {self.create_schema.__name__}.")
        return self.read_schema.model_validate(entity)

    async def create_many(self, create_schemas: list[TCreate]) -> list[TRead]:
        """
        Create multiple entities and return their details.

        :param create_schemas: List of schemas for creating multiple entities.
        :return: List of read schemas representing the created entities.
        :raises service_exceptions.EntityCreateError: Raised when batch creation of entities fails in the service layer.
        """
        service_logger.info(
            f"Creating multiple {self.create_schema.__name__} entities."
        )

        data = [schema.model_dump(exclude_unset=True) for schema in create_schemas]

        async with get_transaction_session() as session:
            try:
                entities = await self.repo.create_many(session, data)

            except repo_exceptions.EntityCreateError as e:
                service_logger.error(f"Error creating entities: {str(e)}")
                raise service_exceptions.EntityCreateError(
                    self.__class__.__name__, str(e)
                )

        validated_entities: list[TRead] = [
            self.read_schema.model_validate(entity) for entity in entities
        ]

        service_logger.info(f"Successfully created {len(entities)} entities.")
        return validated_entities

    async def read_by_id(self, entity_id: int) -> TRead:
        """
        Retrieve a single entity by its ID.

        :param entity_id: ID of the entity to retrieve.
        :return: Schema representing the retrieved entity.
        :raises service_exceptions.EntityNotFoundError: Raised when the entity is not found.
        :raises service_exceptions.EntityReadError: Raised when an error occurs while reading the entity.
        """
        service_logger.info(f"Reading {self.read_schema.__name__} with ID: {entity_id}")

        async with async_session_factory() as session:
            try:
                entity = await self.repo.read_by_id(session, entity_id)

            except repo_exceptions.EntityReadError as e:
                service_logger.error(
                    f"Error reading {self.read_schema.__name__} with ID {entity_id}: {str(e)}"
                )
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        if not entity:
            service_logger.error(f"Entity with ID {entity_id} not found.")
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"entity_id: {entity_id}"
            )

        service_logger.info(
            f"Successfully fetched {self.update_schema.__name__} with ID {entity_id}"
        )
        return self.read_schema.model_validate(entity)

    async def read_all(self, page: int = 1, limit: int = 10) -> list[TRead]:
        """
        Retrieve all entities.

        :return: List of schemas representing all entities.
        :raises service_exceptions.EntityReadError: Raised when an error occurs while reading entities.
        """
        service_logger.info(
            f"Reading all {self.read_schema.__name__} entities (Page: {page}, Limit: {limit})"
        )

        async with async_session_factory() as session:
            try:
                entities = await self.repo.read_all(session, page, limit)

            except repo_exceptions.EntityReadError as e:
                service_logger.error(f"Error reading all entities: {str(e)}")
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        validated_entities = [self.read_schema.model_validate(e) for e in entities]

        service_logger.info(f"Successfully fetched {len(entities)} entities.")
        return validated_entities

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
        service_logger.info(
            f"Updating {self.update_schema.__name__} with ID: {entity_id}"
        )

        data = update_schema.model_dump(exclude_unset=True)

        async with get_transaction_session() as session:
            try:
                is_updated = await self.repo.update_by_id(session, entity_id, data)

                if not is_updated:
                    service_logger.error(
                        f"Entity with ID {entity_id} not found for update."
                    )
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__, f"entity_id: {entity_id}"
                    )

                entity = await self.repo.read_by_id(session, entity_id)

            except repo_exceptions.EntityUpdateError as e:
                service_logger.error(
                    f"Error updating entity with ID {entity_id}: {str(e)}"
                )
                raise service_exceptions.EntityUpdateError(
                    self.__class__.__name__, str(e)
                )

        service_logger.info(
            f"Successfully updated {self.update_schema.__name__} with ID {entity_id}."
        )
        return self.read_schema.model_validate(entity)

    async def delete_by_id(self, entity_id: int) -> bool:
        """
        Delete an entity by its ID.

        :param entity_id: ID of the entity to be deleted.
        :return: True if the delete operation was successful, False otherwise.
        :raises service_exceptions.EntityNotFoundError: Raised when the entity to be deleted is not found.
        :raises service_exceptions.EntityDeleteError: Raised when the entity deletion fails.
        """
        service_logger.info(
            f"Deleting {self.read_schema.__name__} with ID: {entity_id}"
        )

        async with get_transaction_session() as session:
            try:
                is_deleted = await self.repo.delete_by_id(session, entity_id)

            except repo_exceptions.EntityDeleteError as e:
                service_logger.error(
                    f"Error deleting entity with ID {entity_id}: {str(e)}"
                )
                raise service_exceptions.EntityDeleteError(
                    self.__class__.__name__, str(e)
                )

        if not is_deleted:
            service_logger.error(f"Entity with ID {entity_id} not found for deletion.")
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"entity_id: {entity_id}"
            )

        service_logger.info(f"Successfully deleted entity with ID {entity_id}.")
        return is_deleted
