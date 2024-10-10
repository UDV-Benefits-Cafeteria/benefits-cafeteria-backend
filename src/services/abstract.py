from typing import Generic, TypeVar

from pydantic import BaseModel

from src.repositories.abstract import AbstractRepository

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)


class AbstractService(Generic[TCreate, TRead, TUpdate]):
    def __init__(self, repo: AbstractRepository):
        """
        Initialize the service with a repository instance.

        :param repo: Repository that provides data access methods.
        """
        self.repo = repo

    async def create(self, create_schema: TCreate) -> int:
        """
        Create a new entity using the provided creation schema.

        :param create_schema: Schema containing data for creating a new entity.
        :return: ID of the created entity.
        """
        data = create_schema.model_dump(exclude_unset=True)
        entity_id = await self.repo.add_one(data)
        return entity_id

    async def create_many(self, create_schemas: list[TCreate]) -> list[int]:
        """
        Create multiple entities using the provided creation schemas.

        :param create_schemas: List of schemas for creating multiple entities.
        :return: List of IDs of the created entities.
        """
        data = [schema.model_dump(exclude_unset=True) for schema in create_schemas]
        entity_ids = await self.repo.add_many(data)
        return entity_ids

    async def update(self, id: int, update_schema: TUpdate):
        """
        Update an existing entity using the provided update schema.

        :param id: ID of the entity to be updated.
        :param update_schema: Schema containing data to update the entity.
        :return: Result of the update operation.
        """
        data = update_schema.model_dump(exclude_unset=True)
        return await self.repo.update_one(id, data)

    async def delete(self, id: int):
        """
        Delete an entity by its ID.

        :param id: ID of the entity to be deleted.
        :return: Result of the delete operation.
        """
        return await self.repo.delete_one(id)

    async def get_one(self, id: int) -> TRead:
        """
        Retrieve a single entity by its ID.

        :param id: ID of the entity to retrieve.
        :return: Schema representing the retrieved entity.
        """
        entity = await self.repo.find_one(id)
        return TRead.model_validate(entity)

    async def get_all(self) -> list[TRead]:
        """
        Retrieve all entities.

        :return: List of schemas representing all entities.
        """
        entities = await self.repo.find_all()
        return [TRead.model_validate(e) for e in entities]
