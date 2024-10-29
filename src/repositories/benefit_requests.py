from sqlalchemy import asc, desc, select
from typing_extensions import Optional

from src.config import logger
from src.db.db import async_session_factory
from src.models.benefits import BenefitRequest
from src.repositories.abstract import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError


class BenefitRequestsRepository(SQLAlchemyRepository[BenefitRequest]):
    model = BenefitRequest

    async def read_all(
        self,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 10,
    ) -> list[BenefitRequest]:
        async with async_session_factory() as session:
            try:
                query = select(self.model)

                if status:
                    query = query.where(self.model.status == status)

                if sort_by:
                    sort_column = getattr(self.model, sort_by, None)
                    if sort_column is not None:
                        if sort_order == "desc":
                            query = query.order_by(desc(sort_column))
                        else:
                            query = query.order_by(asc(sort_column))
                    else:
                        logger.warning(f"Invalid sort_by field: {sort_by}")
                else:
                    query = query.order_by(desc(self.model.created_at))

                query = query.offset((page - 1) * limit).limit(limit)

                result = await session.execute(query)
                entities = result.scalars().all()
                logger.info(f"Retrieved {len(entities)} {self.model.__name__} entities")
                return entities
            except Exception as e:
                logger.error(f"Error reading all {self.model.__name__} entities: {e}")
                raise EntityReadError(self.model.__name__, "", str(e))

    async def read_by_user_id(self, user_id: int) -> Optional[list[BenefitRequest]]:
        async with async_session_factory() as session:
            try:
                result = await session.execute(
                    select(self.model).where(self.model.user_id == user_id)
                )
                entities = result.scalars().all()
                return entities

            except Exception as e:
                logger.error(
                    f"Error reading Benefit Request by user_id '{user_id}': {e}"
                )
                raise EntityReadError(self.model.__name__, user_id, str(e))
