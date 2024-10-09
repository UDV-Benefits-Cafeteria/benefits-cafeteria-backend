from typing import TypeVar, Generic
from src.repositories.abstract import AbstractRepository
from pydantic import BaseModel

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)


class AbstractService(Generic[TCreate, TRead, TUpdate]):
    def __init__(self, repo: AbstractRepository):
        self.repo = repo

    async def create(self, create_schema: TCreate) -> int:
        data = create_schema.model_dump(exclude_unset=True)
        entity_id = await self.repo.add_one(data)
        return entity_id

    async def create_many(self, create_schemas: list[TCreate]) -> list[int]:
        data = [schema.model_dump(exclude_unset=True) for schema in create_schemas]
        entity_ids = await self.repo.add_many(data)
        return entity_ids

    async def update(self, id: int, update_schema: TUpdate):
        data = update_schema.model_dump(exclude_unset=True)
        return await self.repo.update_one(id, data)

    async def delete(self, id: int):
        return await self.repo.delete_one(id)

    async def get_one(self, id: int) -> TRead:
        entity = await self.repo.find_one(id)
        return TRead.model_validate(entity)

    async def get_all(self) -> list[TRead]:
        entities = await self.repo.find_all()
        return [TRead.model_validate(e) for e in entities]
