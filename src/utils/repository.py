from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import UnaryExpression, delete, select, update

from src.db.db import async_session_factory

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    model: Type[T]

    @abstractmethod
    async def add_one(self, data: dict) -> int:
        pass

    @abstractmethod
    async def add_many(self, data_list: List[dict]) -> List[int]:
        pass

    @abstractmethod
    async def find_one(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    async def find_all(self) -> List[T]:
        pass

    @abstractmethod
    async def update_one(self, id: int, data: dict) -> bool:
        pass

    @abstractmethod
    async def delete_one(self, id: int) -> bool:
        pass

    @abstractmethod
    async def delete_by_parent_id(self, parent_id: int) -> None:
        pass


class SQLAlchemyRepository(AbstractRepository[T]):
    model: Type[T] = None

    async def add_one(self, data: dict) -> int:
        async with async_session_factory() as session:
            instance = self.model(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance.id

    async def add_many(self, data_list: List[dict]) -> List[int]:
        async with async_session_factory() as session:
            instances = [self.model(**data) for data in data_list]
            session.add_all(instances)
            await session.commit()
            for instance in instances:
                await session.refresh(instance)
            return [instance.id for instance in instances]

    async def find_one(self, id: int) -> Optional[T]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()

    async def find_all(
        self,
        *filters,
        order_by: Optional[UnaryExpression] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[T]:
        async with async_session_factory() as session:
            query = select(self.model)

            if filters:
                query = query.where(*filters)
            if order_by is not None:
                query = query.order_by(order_by)
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            result = await session.execute(query)
            return result.scalars().all()

    async def update_one(self, id: int, data: dict) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(
                update(self.model).where(self.model.id == id).values(**data)
            )
            await session.commit()
            return result.rowcount > 0

    async def delete_one(self, id: int) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(
                delete(self.model).where(self.model.id == id)
            )
            await session.commit()
            return result.rowcount > 0

    async def delete_by_parent_id(self, parent_id: int) -> None:
        raise NotImplementedError
