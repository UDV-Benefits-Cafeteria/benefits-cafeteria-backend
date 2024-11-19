from typing import Generic, Optional, Sequence, Type, TypeVar, Union, cast

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import logger
from src.repositories.exceptions import (
    EntityCreateError,
    EntityDeleteError,
    EntityReadError,
    EntityUpdateError,
)

T = TypeVar("T")


class SQLAlchemyRepository(Generic[T]):
    """
    SQLAlchemy-based implementation of a repository, providing
    asynchronous CRUD operations for a specified model/entity using SQLAlchemy.

    Type Parameters:
        T: The type of model/entity class that the repository operates on.

    Attributes:
        model (Type[T]): The entity model class that this repository will manage.
        primary_key (str): The name of the primary key field in the entity model.

    Methods:
        create(data: dict, session: AsyncSession = None) -> T:
            Add a single entity to the data store and return the created entity.

        create_many(data_list: List[dict], session: AsyncSession = None) -> List[T]:
            Add multiple entities to the data store and return the created entities.

        read_by_id(entity_id: Union[int, str], session: AsyncSession = None) -> Optional[T]:
            Retrieve a single entity from the data store by its unique identifier.

        read_all(page: int = 1, limit: int = 10, session: AsyncSession = None) -> List[T]:
            Retrieve all entities from the data store.

        update_by_id(entity_id: Union[int, str], data: dict, session: AsyncSession = None) -> bool:
            Update a single entity in the data store by its unique identifier.

        delete_by_id(entity_id: Union[int, str], session: AsyncSession = None) -> bool:
            Delete a single entity from the data store by its unique identifier.
    """

    model: Type[T]
    primary_key: str = "id"

    async def create(self, session: AsyncSession, data: dict) -> T:
        """
        Add a single entity to the data store.

        Args:
            session: An external AsyncSession.
            data: A dictionary representing the entity to be added.

        Returns:
            The newly created entity.

        Raises:
            EntityCreateError: If there is an error while creating the entity.
        """

        try:
            instance = self.model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
        except Exception as e:
            raise EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, str(e)
            )

        return instance

    async def create_many(
        self, session: AsyncSession, data_list: list[dict]
    ) -> list[T]:
        """
        Add multiple entities to the data store.

        Args:
            session: An AsyncSession instance.
            data_list: A list of dictionaries representing the entities to be added.

        Returns:
            A list of the newly created entities.

        Raises:
            EntityCreateError: If there is an error while creating the entities.
        """
        try:
            instances = [self.model(**data) for data in data_list]
            session.add_all(instances)
            await session.flush()
            for instance in instances:
                await session.refresh(instance)
        except Exception as e:
            raise EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, str(e)
            )

        return instances

    async def read_by_id(
        self, session: AsyncSession, entity_id: Union[int, str]
    ) -> Optional[T]:
        """
        Retrieve a single entity from the data store by its unique identifier.

        Args:
            session: An AsyncSession instance.
            entity_id: The unique identifier of the entity to retrieve.

        Returns:
            The entity if found, or None if no entity with the given ID exists.

        Raises:
            EntityReadError: If there is an error while reading the entity.
        """
        try:
            result = await session.execute(
                select(self.model).where(
                    getattr(self.model, self.primary_key) == entity_id
                )
            )
            entity = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error reading {self.model.__name__} by ID: {entity_id}: {e}")
            raise EntityReadError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            )

        return entity

    async def read_all(
        self, session: AsyncSession, page: int = 1, limit: int = 10
    ) -> Sequence[T]:
        """
        Retrieve all entities from the data store.

        Args:
            session: An AsyncSession instance.
            page: The page number for pagination.
            limit: The number of entities per page.

        Returns:
            A list of entities matching the query.

        Raises:
            EntityReadError: If there is an error while reading entities.
        """
        try:
            result = await session.execute(
                select(self.model).offset((page - 1) * limit).limit(limit)
            )
            entities = result.scalars().all()
        except Exception as e:
            raise EntityReadError(
                self.__class__.__name__, self.model.__tablename__, "", str(e)
            )

        return entities

    async def update_by_id(
        self, session: AsyncSession, entity_id: Union[int, str], data: dict
    ) -> bool:
        """
        Update a single entity in the data store by its unique identifier.

        Args:
            session: An AsyncSession instance.
            entity_id: The unique identifier of the entity to update.
            data: A dictionary representing the updates.

        Returns:
            True if the update was successful, False otherwise.

        Raises:
            EntityUpdateError: If there is an error while updating the entity.
        """
        try:
            result = await session.execute(
                update(self.model)
                .where(getattr(self.model, self.primary_key) == entity_id)
                .values(**data)
            )
            await session.flush()
        except Exception as e:
            raise EntityUpdateError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            )

        rowcount: int = cast(int, result.rowcount)
        if rowcount > 0:
            return True
        else:
            return False

    async def delete_by_id(
        self, session: AsyncSession, entity_id: Union[int, str]
    ) -> bool:
        """
        Delete a single entity from the data store by its unique identifier.

        Args:
            session: An AsyncSession instance.
            entity_id: The unique identifier of the entity to delete.

        Returns:
            True if the deletion was successful, False otherwise.

        Raises:
            EntityDeleteError: If there is an error while deleting the entity.
        """
        try:
            result = await session.execute(
                delete(self.model).where(
                    getattr(self.model, self.primary_key) == entity_id
                )
            )
        except Exception as e:
            raise EntityDeleteError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            )

        rowcount: int = cast(int, result.rowcount)
        if rowcount > 0:
            return True
        else:
            return False
