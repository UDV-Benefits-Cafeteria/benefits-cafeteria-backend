from typing import Generic, Optional, Sequence, Type, TypeVar, Union

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import logger
from src.db.db import async_session_factory
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
        session_provided = session is not None

        if not session_provided:
            session = async_session_factory()

        try:
            instance = self.model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)

            logger.info(
                f"Created {self.model} with ID: {getattr(instance, self.primary_key)}"
            )
            return instance
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise EntityCreateError(self.model.__name__, str(e))
        finally:
            if not session_provided:
                await session.close()

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
            logger.info(f"Created {len(instances)} {self.model.__name__} entities")
            return instances
        except Exception as e:
            logger.error(f"Error creating multiple {self.model.__name__} entities: {e}")
            raise EntityCreateError(self.model.__name__, str(e))

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
            if entity:
                logger.info(f"Found {self.model.__name__} with ID: {entity_id}")
            else:
                logger.warning(f"No {self.model.__name__} found with ID: {entity_id}")
            return entity
        except Exception as e:
            logger.error(f"Error reading {self.model.__name__} by ID: {entity_id}: {e}")
            raise EntityReadError(self.model.__name__, entity_id, str(e))

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
            logger.info(f"Retrieved {len(entities)} {self.model.__name__} entities")
            return entities
        except Exception as e:
            logger.error(f"Error reading all {self.model.__name__} entities: {e}")
            raise EntityReadError(self.model.__name__, "", str(e))

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
            if result.rowcount() > 0:
                logger.info(f"Updated {self.model.__name__} with ID: {entity_id}")
                return True
            else:
                logger.warning(
                    f"No {self.model.__name__} found with ID: {entity_id} for update"
                )
                return False
        except Exception as e:
            logger.error(
                f"Error updating {self.model.__name__} with ID: {entity_id}: {e}"
            )
            raise EntityUpdateError(self.model.__name__, entity_id, str(e))

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
            if result.rowcount() > 0:
                logger.info(f"Deleted {self.model.__name__} with ID: {entity_id}")
                return True
            else:
                logger.warning(
                    f"No {self.model.__name__} found with ID: {entity_id} for deletion"
                )
                return False
        except Exception as e:
            logger.error(
                f"Error deleting {self.model.__name__} with ID: {entity_id}: {e}"
            )
            raise EntityDeleteError(self.model.__name__, entity_id, str(e))
