from sqlalchemy import delete

from src.db.db import async_session_factory
from src.utils.repository import SQLAlchemyRepository
from src.models.benefits import BenefitImage

class BenefitImagesRepository(SQLAlchemyRepository[BenefitImage]):
    model = BenefitImage

    async def delete_by_parent_id(self, parent_id: int) -> None:
        async with async_session_factory() as session:
            await session.execute(
                delete(BenefitImage).where(BenefitImage.benefit_id == parent_id)
            )
            await session.commit()

