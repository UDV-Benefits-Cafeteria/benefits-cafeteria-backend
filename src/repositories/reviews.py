from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import repository_logger
from src.models import Review
from src.repositories.base import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError


class ReviewsRepository(SQLAlchemyRepository[Review]):
    model = Review

    async def read_by_benefit_id(
        self, session: AsyncSession, benefit_id: int, page: int = 1, limit: int = 10
    ) -> Sequence[Review]:
        repository_logger.info(
            f"Fetching reviews for Benefit ID {benefit_id}. Page: {page}, Limit: {limit}"
        )

        try:
            query = (
                select(self.model)
                .where(self.model.benefit_id == benefit_id)
                .offset((page - 1) * limit)
                .limit(limit)
            )
            result = await session.execute(query)
            reviews = result.scalars().all()
            return reviews
        except Exception as e:
            repository_logger.error(
                f"Error fetching reviews for Benefit ID {benefit_id}: {e}"
            )
            raise EntityReadError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"benefit_id: {benefit_id}",
                str(e),
            )
