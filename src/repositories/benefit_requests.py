from sqlalchemy import select
from typing_extensions import Optional

from src.config import logger
from src.db.db import async_session_factory
from src.models.benefits import BenefitRequest
from src.repositories.abstract import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError


class BenefitRequestsRepository(SQLAlchemyRepository[BenefitRequest]):
    model = BenefitRequest

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
