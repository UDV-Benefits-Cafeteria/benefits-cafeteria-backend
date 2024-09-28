from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

from src.db.db import async_session_factory

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    async def add_one(self, data: T) -> int:
        pass

    @abstractmethod
    async def find_one(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    async def find_all(self) -> list[T]:
        pass

    @abstractmethod
    async def update_one(self, id: int, data: T) -> bool:
        pass

    @abstractmethod
    async def delete_one(self, id: int) -> bool:
        pass


class SQLAlchemyRepository(AbstractRepository):
    model = None

    async def add_one(self, data: dict) -> int:
        async with async_session_factory() as session:
            instance = self.model(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance.id

    async def find_one(self, id: int):
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model)
                .options(
                    selectinload(self.model.images),
                )
                .where(self.model.id == id)
            )
            return result.scalar_one_or_none()

    async def find_all(self):
        async with async_session_factory() as session:
            result = await session.execute(select(self.model).options(
                    selectinload(self.model.images),
                ))
            return result.scalars().all()

    async def update_one(self, id: int, data: dict):
        async with async_session_factory() as session:
            await session.execute(
                update(self.model).where(self.model.id == id).values(**data)
            )
            await session.commit()

    async def delete_one(self, id: int):
        async with async_session_factory() as session:
            await session.execute(delete(self.model).where(self.model.id == id))
            await session.commit()
