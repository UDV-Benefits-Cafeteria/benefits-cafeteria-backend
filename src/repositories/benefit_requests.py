from typing import Optional, Sequence

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import repository_logger
from src.models.benefits import BenefitRequest
from src.repositories.base import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError


class BenefitRequestsRepository(SQLAlchemyRepository[BenefitRequest]):
    model = BenefitRequest

    async def read_all(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 10,
        legal_entity_id: Optional[int] = None,
    ) -> Sequence[BenefitRequest]:
        """
        Retrieve all BenefitRequest entities, with optional filtering by status,
        sorting, and pagination.

        Args:
            session: An external AsyncSession.
            status: Optional status to filter BenefitRequests.
            sort_by: Field name to sort the results by.
            sort_order: Sort order ('asc' or 'desc').
            page: Page number for pagination.
            limit: Number of items per page.
            legal_entity_id: Optional legal entity ID for filtering.

        Returns:
            A list of BenefitRequest entities.

        Raises:
            EntityReadError: If there's an error reading entities.
        """
        repository_logger.info(
            f"Fetching BenefitRequests: status={status}, sort_by={sort_by}, sort_order={sort_order}, "
            f"page={page}, limit={limit}, legal_entity_id={legal_entity_id}."
        )

        try:
            query = select(self.model)

            # HR cannot see user requests outside its legal entity, so we join tables on legal_entity_id field
            if legal_entity_id is not None:
                query = query.join(self.model.user).where(
                    self.model.user.has(legal_entity_id=legal_entity_id)
                )

            if status:
                query = query.where(self.model.status == status)

            if sort_by:
                sort_column = getattr(self.model, sort_by, None)
                if sort_column is not None:
                    order = desc if sort_order == "desc" else asc
                    query = query.order_by(order(sort_column))
            else:
                query = query.order_by(desc(self.model.created_at))

            query = query.offset((page - 1) * limit).limit(limit)

            result = await session.execute(query)
            entities = result.scalars().all()
        except Exception as e:
            repository_logger.error(
                f"Error fetching BenefitRequests: status={status}, page={page}, limit={limit}, "
                f"legal_entity_id={legal_entity_id}: {e}"
            )
            raise EntityReadError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"status: {status}, page: {page}, limit: {limit}, legal_entity_id: {legal_entity_id}",
                str(e),
            )

        repository_logger.info(
            f"Successfully fetched BenefitRequests: status={status}, page={page}, limit={limit}, "
            f"legal_entity_id={legal_entity_id}."
        )
        return entities

    async def read_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> Sequence[BenefitRequest]:
        """
        Retrieve BenefitRequest entities by user ID.

        Args:
            session: An external AsyncSession.
            user_id: The ID of the user.

        Returns:
            A list of BenefitRequest entities associated with the user ID.

        Raises:
            EntityReadError: If there's an error reading the entities.
        """
        repository_logger.info(f"Fetching BenefitRequests for user_id={user_id}.")

        try:
            result = await session.execute(
                select(self.model).where(self.model.user_id == user_id)
            )
            entities = result.scalars().all()
        except Exception as e:
            repository_logger.error(
                f"Error fetching BenefitRequests for user_id={user_id}: {e}"
            )
            raise EntityReadError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"user_id: {user_id}",
                str(e),
            )

        repository_logger.info(
            f"Successfully fetched BenefitRequests for user_id={user_id}."
        )
        return entities
