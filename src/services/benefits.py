from typing import List

from sqlalchemy import delete

from src.db.db import async_session_factory
from src.schemas.benefit import BenefitCreate, BenefitUpdate, BenefitRead
from src.models.benefits import BenefitImage
from src.utils.repository import AbstractRepository

class BenefitsService:
    def __init__(self, benefits_repo: AbstractRepository):
        self.benefits_repo = benefits_repo

    async def create_benefit(self, benefit_create: BenefitCreate) -> int:
        benefit_data = benefit_create.dict(exclude_unset=True)
        images_data = benefit_data.pop('images', [])

        benefit_id = await self.benefits_repo.add_one(benefit_data)

        if images_data:
            await self._add_images(benefit_id, images_data)
        return benefit_id

    async def _add_images(self, benefit_id: int, images_data: List[dict]):
        async with async_session_factory() as session:
            images = [BenefitImage(benefit_id=benefit_id, **image) for image in images_data]
            session.add_all(images)
            await session.commit()

    async def get_benefit(self, id: int) -> BenefitRead:
        benefit = await self.benefits_repo.find_one(id)
        if not benefit:
            raise Exception("Бенефит не найден")
        return BenefitRead.from_orm(benefit)

    async def get_benefits(self) -> List[BenefitRead]:
        benefits = await self.benefits_repo.find_all()
        return [BenefitRead.from_orm(b) for b in benefits]

    async def update_benefit(self, id: int, benefit_update: BenefitUpdate):
        benefit_data = benefit_update.dict(exclude_unset=True)
        images_data = benefit_data.pop('images', None)
        await self.benefits_repo.update_one(id, benefit_data)
        if images_data is not None:
            await self._update_images(id, images_data)

    async def _update_images(self, benefit_id: int, images_data: List[dict]):
        async with async_session_factory() as session:

            await session.execute(
                delete(BenefitImage).where(BenefitImage.benefit_id == benefit_id)
            )

            images = [BenefitImage(benefit_id=benefit_id, **image) for image in images_data]
            session.add_all(images)
            await session.commit()

    async def delete_benefit(self, id: int):
        await self.benefits_repo.delete_one(id)
