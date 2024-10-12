from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from src.repositories.abstract import AbstractRepository

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)
TRepo = TypeVar("TRepo", bound=AbstractRepository)


class AbstractService(Generic[TCreate, TRead, TUpdate]):
    repo: AbstractRepository
    create_schema: TCreate
    read_schema: TRead
    update_schema: TUpdate

    async def _create(self, create_schema: TCreate) -> int:
        """
        Create a new entity using the provided creation schema.

        :param create_schema: Schema containing data for creating a new entity.
        :return: ID of the created entity.
        """
        data = create_schema.model_dump(exclude_unset=True)
        entity_id = await self.repo.add_one(data)
        return entity_id

    async def create(self, create_schema: TCreate) -> TRead:
        """
        Create a new entity and return the created entity's details.

        :param create_schema: Schema containing data for creating a new entity.
        :return: The created entity represented by the read schema.
        """
        entity_id: int = await self._create(create_schema)
        entity: TRead = await self.get(entity_id)
        return entity

    async def _create_many(self, create_schemas: list[TCreate]) -> list[int]:
        """
        Create multiple entities using the provided creation schemas.

        :param create_schemas: List of schemas for creating multiple entities.
        :return: List of IDs of the created entities.
        """
        data = [schema.model_dump(exclude_unset=True) for schema in create_schemas]
        entity_ids = await self.repo.add_many(data)
        return entity_ids

    async def create_many(self, create_schemas: list[TCreate]) -> list[TRead]:
        """
        Create multiple entities and return their details.

        :param create_schemas: List of schemas for creating multiple entities.
        :return: List of read schemas representing the created entities.
        """
        entity_ids: list[int] = await self._create_many(create_schemas)
        entities: list[TRead] = [await self.get(entity) for entity in entity_ids]
        return entities

    async def _update(self, entity_id: int, update_schema: TUpdate) -> bool:
        """
        Update an existing entity using the provided update schema.

        :param entity_id: ID of the entity to be updated.
        :param update_schema: Schema containing data to update the entity.
        :return: True if the update operation was successful, False otherwise.
        """
        data = update_schema.model_dump(exclude_unset=True)
        return await self.repo.update_one(entity_id, data)

    async def update(self, entity_id: int, update_schema: TUpdate) -> Optional[TRead]:
        """
        Update an existing entity and return the updated entity's details if successful.

        :param entity_id: ID of the entity to be updated.
        :param update_schema: Schema containing data to update the entity.
        :return: The updated entity represented by the read schema if successful,
                 otherwise a boolean indicating failure.
        """
        is_updated: bool = await self.update(entity_id, update_schema)
        if is_updated:
            return await self.get(entity_id)
        return None

    async def delete(self, entity_id: int) -> bool:
        """
        Delete an entity by its ID.

        :param entity_id: ID of the entity to be deleted.
        :return: True if the delete operation was successful, False otherwise.
        """
        return await self.repo.delete_one(entity_id)

    async def get(self, entity_id: int) -> TRead:
        """
        Retrieve a single entity by its ID.

        :param entity_id: ID of the entity to retrieve.
        :return: Schema representing the retrieved entity.
        """
        entity = await self.repo.find_one(entity_id)
        return TRead.model_validate(entity)

    async def get_all(self) -> list[TRead]:
        """
        Retrieve all entities.

        :return: List of schemas representing all entities.
        """
        entities = await self.repo.find_all()
        return [TRead.model_validate(e) for e in entities]
