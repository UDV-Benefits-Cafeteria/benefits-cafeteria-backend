from typing import Generic, TypeVar

from pydantic import BaseModel

from src.repositories.abstract import AbstractRepository

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)


class AbstractService(Generic[TCreate, TRead, TUpdate]):
    def __init__(
        self,
        repo: AbstractRepository,
        create_schema: type[TCreate],
        read_schema: type[TRead],
        update_schema: type[TUpdate],
    ):
        """
        Initialize the service with a repository instance and schema classes.

        :param repo: Repository that provides data access methods.
        :param create_schema: Class of the creation schema.
        :param read_schema: Class of the read schema.
        :param update_schema: Class of the update schema.
        """
        self.repo = repo
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema

    async def create(self, create_schema: TCreate) -> int:
        """
        Create a new entity using the provided creation schema.

        :param create_schema: Schema containing data for creating a new entity.
        :return: ID of the created entity.
        """
        data = create_schema.model_dump(exclude_unset=True)
        entity_id = await self.repo.add_one(data)
        return entity_id

    async def create_and_get_one(self, create_schema: TCreate) -> TRead:
        """
        Create a new entity and return the created entity's details.

        :param create_schema: Schema containing data for creating a new entity.
        :return: The created entity represented by the read schema.
        """
        entity_id: int = await self.create(create_schema)
        entity: TRead = await self.get_one(entity_id)
        return entity

    async def create_many(self, create_schemas: list[TCreate]) -> list[int]:
        """
        Create multiple entities using the provided creation schemas.

        :param create_schemas: List of schemas for creating multiple entities.
        :return: List of IDs of the created entities.
        """
        data = [schema.model_dump(exclude_unset=True) for schema in create_schemas]
        entity_ids = await self.repo.add_many(data)
        return entity_ids

    async def create_many_and_get_many(
        self, create_schemas: list[TCreate]
    ) -> list[TRead]:
        """
        Create multiple entities and return their details.

        :param create_schemas: List of schemas for creating multiple entities.
        :return: List of read schemas representing the created entities.
        """
        entity_ids: list[int] = await self.create_many(create_schemas)
        entities: list[TRead] = [await self.get_one(entity) for entity in entity_ids]
        return entities

    async def update(self, id: int, update_schema: TUpdate) -> bool:
        """
        Update an existing entity using the provided update schema.

        :param id: ID of the entity to be updated.
        :param update_schema: Schema containing data to update the entity.
        :return: True if the update operation was successful, False otherwise.
        """
        data = update_schema.model_dump(exclude_unset=True)
        return await self.repo.update_one(id, data)

    async def update_and_get_one(self, id: int, update_schema: TUpdate) -> bool | TRead:
        """
        Update an existing entity and return the updated entity's details if successful.

        :param id: ID of the entity to be updated.
        :param update_schema: Schema containing data to update the entity.
        :return: The updated entity represented by the read schema if successful,
                 otherwise a boolean indicating failure.
        """
        is_updated: bool = await self.update(id, update_schema)
        if is_updated:
            return await self.get_one(id)
        return is_updated

    async def delete(self, id: int) -> bool:
        """
        Delete an entity by its ID.

        :param id: ID of the entity to be deleted.
        :return: True if the delete operation was successful, False otherwise.
        """
        return await self.repo.delete_one(id)

    async def get_one(self, id: int) -> TRead:
        """
        Retrieve a single entity by its ID.

        :param id: ID of the entity to retrieve.
        :return: Schema representing the retrieved entity.
        """
        entity = await self.repo.find_one(id)
        return self.read_schema.model_validate(entity)

    async def get_all(self) -> list[TRead]:
        """
        Retrieve all entities.

        :return: List of schemas representing all entities.
        """
        entities = await self.repo.find_all()
        return [self.read_schema.model_validate(e) for e in entities]
