import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, select, update

from src.db.db import async_session_factory

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    """
    Abstract base class for a repository pattern. Provides an interface for
    basic CRUD operations on a model entity.

    Attributes:
        model: The type of model/entity class the repository operates on.
    """

    model: Type[T]
    primary_key: str = "id"

    @abstractmethod
    async def add_one(self, data: dict) -> Any:
        """
        Add a single entity to the data store.

        Args:
            data: A dictionary representing the entity to be added.

        Returns:
            The ID or unique identifier of the newly added entity.
        """
        pass

    @abstractmethod
    async def add_many(self, data_list: List[dict]) -> List[Any]:
        """
        Add multiple entities to the data store.

        Args:
            data_list: A list of dictionaries, each representing an entity to be added.

        Returns:
            A list of IDs or unique identifiers of the newly added entities.
        """
        pass

    @abstractmethod
    async def find_one(self, entity_id: Any) -> Optional[T]:
        """
        Retrieve a single entity from the data store by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity to retrieve.

        Returns:
            The entity if found, or None if no entity with the given ID exists.
        """
        pass

    @abstractmethod
    async def find_all(self) -> List[T]:
        """
        Retrieve all entities from the data store.

        Returns:
            A list of entities matching the query.
        """
        pass

    @abstractmethod
    async def update_one(self, entity_id: Any, data: dict) -> bool:
        """
        Update a single entity in the data store by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity to update.
            data: A dictionary of fields to update.

        Returns:
            True if the update was successful, False otherwise.
        """
        pass

    @abstractmethod
    async def delete_one(self, entity_id: Any) -> bool:
        """
        Delete a single entity from the data store by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity to delete.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        pass


class SQLAlchemyRepository(AbstractRepository[T]):
    """
    SQLAlchemy-based implementation of the AbstractRepository. Provides
    asynchronous CRUD operations for a specified model or entity.
    """

    model: Type[T]
    primary_key: str = "id"

    async def add_one(self, data: dict) -> Any:
        """
        Add a single entity to the data store.

        Args:
            data: A dictionary representing the entity to be added.

        Returns:
            The ID or unique identifier of the newly added entity.
        """
        async with async_session_factory() as session:
            instance = self.model(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return getattr(instance, self.primary_key)

    async def add_many(self, data_list: List[dict]) -> List[Any]:
        """
        Add multiple entities to the data store.

        Args:
            data_list: A list of dictionaries representing the entities to be added.

        Returns:
            A list of IDs or unique identifiers of the newly added entities.
        """
        async with async_session_factory() as session:
            instances = [self.model(**data) for data in data_list]
            session.add_all(instances)
            await session.commit()
            for instance in instances:
                await session.refresh(instance)
            return [getattr(instance, self.primary_key) for instance in instances]

    async def find_one(self, entity_id: Any) -> Optional[T]:
        """
        Retrieve a single entity from the data store by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity to retrieve.

        Returns:
            The entity if found, or None if no entity with the given ID exists.
        """
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model).where(
                    getattr(self.model, self.primary_key) == entity_id
                )
            )
            return result.scalar_one_or_none()

    async def find_all(self) -> List[T]:
        """
        Retrieve all entities from the data store
        Returns:
            A list of entities matching the query.
        """
        async with async_session_factory() as session:
            query = select(self.model)

            result = await session.execute(query)
            return result.scalars().all()

    async def update_one(self, entity_id: Any, data: dict) -> bool:
        """
        Update a single entity in the data store by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity to update.
            data: A dictionary of fields to update.

        Returns:
            True if the update was successful, False otherwise.
        """
        async with async_session_factory() as session:
            result = await session.execute(
                update(self.model)
                .where(getattr(self.model, self.primary_key) == entity_id)
                .values(**data)
            )
            await session.commit()
            return result.rowcount > 0

    async def delete_one(self, entity_id: Any) -> bool:
        """
        Delete a single entity from the data store by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity to delete.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        async with async_session_factory() as session:
            result = await session.execute(
                delete(self.model).where(
                    getattr(self.model, self.primary_key) == entity_id
                )
            )
            await session.commit()
            return result.rowcount > 0
