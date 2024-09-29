"""
This file is made for testing.
"""
from typing import List

import src.schemas.benefit as schemas
from src.utils.repository import AbstractRepository


class BenefitsService:
    def __init__(
        self, benefits_repo: AbstractRepository, images_repo: AbstractRepository
    ):
        self.benefits_repo = benefits_repo
        self.images_repo = images_repo

    async def create_benefit(self, benefit_create: schemas.BenefitCreate) -> int:
        benefit_data = benefit_create.model_dump(exclude_unset=True)
        images_data = benefit_data.pop("images", [])

        benefit_id = await self.benefits_repo.add_one(benefit_data)

        if images_data:
            await self._add_images(benefit_id, images_data)
        return benefit_id

    async def _add_images(self, benefit_id: int, images_data: List[dict]):
        for image_data in images_data:
            image_data["benefit_id"] = benefit_id
        await self.images_repo.add_many(images_data)

    async def get_benefit(self, id: int) -> schemas.BenefitRead:
        benefit = await self.benefits_repo.find_one(id)
        if not benefit:
            raise Exception("Бенефит не найден")
        return schemas.BenefitRead.model_validate(benefit)

    async def get_benefits(
        self, filters: schemas.BenefitFilter
    ) -> List[schemas.BenefitRead]:
        benefits = await self.benefits_repo.find_all(filters)
        return [schemas.BenefitRead.model_validate(b) for b in benefits]

    async def update_benefit(self, id: int, benefit_update: schemas.BenefitUpdate):
        benefit_data = benefit_update.model_dump(exclude_unset=True)
        images_data = benefit_data.pop("images", None)
        await self.benefits_repo.update_one(id, benefit_data)
        if images_data is not None:
            await self._update_images(id, images_data)

    async def _update_images(self, benefit_id: int, images_data: List[dict]):
        await self.images_repo.delete_by_parent_id(benefit_id)
        await self._add_images(benefit_id, images_data)

    async def delete_benefit(self, id: int):
        await self.benefits_repo.delete_one(id)
