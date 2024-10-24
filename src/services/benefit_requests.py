from typing import Optional

import src.schemas.request as schemas
from src.repositories.benefit_requests import BenefitRequestsRepository
from src.services.base import BaseService


class BenefitRequestsService(
    BaseService[
        schemas.BenefitRequestCreate,
        schemas.BenefitRequestRead,
        schemas.BenefitRequestUpdate,
    ]
):
    repo = BenefitRequestsRepository()
    create_schema = schemas.BenefitRequestCreate
    read_schema = schemas.BenefitRequestRead
    update_schema = schemas.BenefitRequestUpdate

    async def read_by_user_id(
        self, user_id: int
    ) -> Optional[list[schemas.BenefitRequestRead]]:
        entities = await self.repo.read_by_user_id(user_id)
        if entities:
            return [self.read_schema.model_validate(entity) for entity in entities]
        return None
