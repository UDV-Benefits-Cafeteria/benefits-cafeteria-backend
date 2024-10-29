from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.schemas.request as schemas
import src.services.exceptions as service_exceptions
from src.repositories.benefit_requests import BenefitRequestsRepository
from src.repositories.benefits import BenefitsRepository
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

    async def read_all(
        self,
        status: Optional[schemas.BenefitStatus] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 10,
    ) -> list[schemas.BenefitRequestRead]:
        """
        Read all benefit requests with optional filtering and sorting.
        """
        try:
            entities = await self.repo.read_all(
                status=status,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                limit=limit,
            )
            validated_entities = [self.read_schema.model_validate(e) for e in entities]

            return validated_entities
        except repo_exceptions.EntityReadError as e:
            raise service_exceptions.EntityReadError(
                self.read_schema.__name__, e.read_param, str(e)
            )

    async def create(
        self, create_schema: schemas.BenefitRequestCreate
    ) -> schemas.BenefitRequestRead:
        """
        Create a new benefit request and decrease the amount of the benefit by 1.
        """
        try:
            await self.change_benefit_amount(-1, create_schema.benefit_id)
            created_request = await super().create(create_schema)
            return created_request

        except (
            repo_exceptions.EntityReadError,
            repo_exceptions.EntityUpdateError,
        ) as e:
            raise service_exceptions.EntityCreateError(
                self.create_schema.__name__, str(e)
            )

    async def update_by_id(
        self, entity_id: int, update_schema: schemas.BenefitRequestUpdate
    ) -> Optional[schemas.BenefitRequestRead]:
        """
        Update an existing benefit request and handle benefit amount accordingly.
        """
        try:
            existing_request = await self.repo.read_by_id(entity_id)
            if not existing_request:
                raise service_exceptions.EntityNotFoundError(
                    self.read_schema.__name__, entity_id
                )

            old_status = existing_request.status

            new_status = update_schema.status or old_status

            benefit_id = existing_request.benefit_id

            if old_status.value != "declined" and new_status.value == "declined":
                await self.change_benefit_amount(1, benefit_id)

            elif old_status.value == "declined" and new_status.value in [
                "approved",
                "pending",
            ]:
                await self.change_benefit_amount(-1, benefit_id)

            updated_request = await super().update_by_id(entity_id, update_schema)

            return updated_request

        except (
            repo_exceptions.EntityReadError,
            repo_exceptions.EntityUpdateError,
        ) as e:
            raise service_exceptions.EntityUpdateError(
                self.read_schema.__name__, entity_id, str(e)
            )

    async def read_by_user_id(
        self, user_id: int
    ) -> Optional[list[schemas.BenefitRequestRead]]:
        entities = await self.repo.read_by_user_id(user_id)
        if entities:
            return [self.read_schema.model_validate(entity) for entity in entities]
        return None

    @staticmethod
    async def change_benefit_amount(amount: int, benefit_id: int) -> None:
        benefits_repo = BenefitsRepository()
        benefit = await benefits_repo.read_by_id(benefit_id)
        if not benefit:
            raise service_exceptions.EntityNotFoundError("Benefit", benefit_id)

        if benefit.amount is not None:
            if benefit.amount == 0 and amount < 0:
                raise service_exceptions.EntityUpdateError(
                    "Benefit Request", benefit_id, "Amount cannot be negative"
                )
            update_data = {"amount": benefit.amount + amount}
            await benefits_repo.update_by_id(benefit.id, update_data)
