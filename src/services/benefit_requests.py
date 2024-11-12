from typing import Optional

from fastapi import BackgroundTasks

import src.repositories.exceptions as repo_exceptions
import src.schemas.request as schemas
import src.services.exceptions as service_exceptions
from src.config import get_settings
from src.repositories.benefit_requests import BenefitRequestsRepository
from src.schemas.benefit import BenefitUpdate
from src.schemas.user import UserRole, UserUpdate
from src.services.base import BaseService
from src.services.benefits import BenefitsService
from src.services.users import UsersService

settings = get_settings()


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
        current_user: schemas.UserRead = None,
        status: Optional[schemas.BenefitStatus] = None,
        sort_by: Optional[schemas.BenefitRequestSortFields] = None,
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 10,
    ) -> list[schemas.BenefitRequestRead]:
        try:
            if current_user.role == UserRole.ADMIN.value:
                legal_entity_id = None
            elif current_user.role == UserRole.HR.value:
                legal_entity_id = current_user.legal_entity_id
                if legal_entity_id is None:
                    raise service_exceptions.EntityReadError(
                        "BenefitRequest",
                        "legal_entity_id",
                        "HR user has no legal_entity_id",
                    )
            else:
                raise service_exceptions.EntityReadError(
                    "BenefitRequest",
                    "role",
                    "User does not have access to benefit requests",
                )

            entities = await self.repo.read_all(
                status=status,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                limit=limit,
                legal_entity_id=legal_entity_id,
            )
            validated_entities = [self.read_schema.model_validate(e) for e in entities]

            return validated_entities
        except repo_exceptions.EntityReadError as e:
            raise service_exceptions.EntityReadError(
                self.read_schema.__name__, e.read_param, str(e)
            )

    async def create(
        self,
        create_schema: schemas.BenefitRequestCreate,
        background_tasks: BackgroundTasks = None,
    ) -> schemas.BenefitRequestRead:
        """
        Create a new benefit request and decrease the amount of the benefit by 1.
        """
        try:
            benefits_service = BenefitsService()
            users_service = UsersService()
            await self.change_benefit_amount(
                -1, create_schema.benefit_id, benefits_service
            )
            await self.change_coins(
                create_schema.benefit_id,
                create_schema.user_id,
                True,
                benefits_service,
                users_service,
            )
            created_request = await super().create(create_schema)

            try:
                benefit = await benefits_service.read_by_id(create_schema.benefit_id)
                user = await users_service.read_by_id(create_schema.user_id)
            except Exception:
                raise

            await self.send_email(
                user,
                "benefit-request.html",
                f"Запрос на бенефит на {settings.APP_TITLE}",
                {
                    "product": settings.APP_TITLE,
                    "name": user.firstname,
                    "benefit_image": (
                        benefit.images[0].image_url
                        if benefit.images
                        else "https://digital-portfolio.hb.ru-msk.vkcloud-storage.ru/Image.png"
                    ),
                    "benefit_name": benefit.name,
                    "benefit_price": benefit.coins_cost,
                    "benefit_url": f"https://{settings.DOMAIN}/main/benefits/{benefit.id}",
                    "requests_url": f"https://{settings.DOMAIN}/main/history",
                },
                background_tasks,
            )
            return created_request
        except (
            repo_exceptions.EntityReadError,
            repo_exceptions.EntityUpdateError,
        ) as e:
            raise service_exceptions.EntityCreateError(
                self.create_schema.__name__, str(e)
            )

    async def delete_by_id(self, entity_id: int) -> bool:
        existing_request = await self.repo.read_by_id(entity_id)
        if not existing_request:
            raise service_exceptions.EntityNotFoundError(
                self.read_schema.__name__, entity_id
            )
        try:
            benefits_service = BenefitsService()
            users_service = UsersService()

            await self.change_benefit_amount(
                1, existing_request.benefit_id, benefits_service
            )
            await self.change_coins(
                existing_request.benefit_id,
                existing_request.user_id,
                False,
                benefits_service,
                users_service,
            )
        except Exception:
            raise service_exceptions.EntityDeletionError(
                "Benefit Request", entity_id, "Failed to delete request"
            )

        deleted_request = await super().delete_by_id(entity_id)
        return deleted_request

    async def update_by_id(
        self,
        entity_id: int,
        update_schema: schemas.BenefitRequestUpdate,
        current_user: schemas.UserRead = None,
        background_tasks: BackgroundTasks = None,
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

            benefits_service = BenefitsService()
            users_service = UsersService()
            if old_status.value != "declined" and new_status.value == "declined":
                if (
                    current_user.id == existing_request.user_id
                    or current_user.role in [UserRole.HR.value, UserRole.ADMIN.value]
                ):
                    await self.change_benefit_amount(1, benefit_id, benefits_service)
                    await self.change_coins(
                        benefit_id,
                        existing_request.user_id,
                        False,
                        benefits_service,
                        users_service,
                    )
                else:
                    raise service_exceptions.EntityUpdateError(
                        self.read_schema.__name__,
                        entity_id,
                        "You cannot decline benefit request",
                    )

            elif old_status.value == "declined" and new_status.value in [
                "approved",
                "pending",
            ]:
                if current_user.role in [UserRole.HR.value, UserRole.ADMIN.value]:
                    await self.change_benefit_amount(-1, benefit_id, benefits_service)
                    await self.change_coins(
                        benefit_id,
                        existing_request.user_id,
                        True,
                        benefits_service,
                        users_service,
                    )
                else:
                    raise service_exceptions.EntityUpdateError(
                        self.read_schema.__name__,
                        entity_id,
                        "You cannot update benefit request",
                    )

            updated_request = await super().update_by_id(entity_id, update_schema)

            if new_status.value != "pending":
                try:
                    benefit = await benefits_service.read_by_id(benefit_id)
                except Exception:
                    raise

                await self.send_email(
                    current_user,
                    "benefit-response.html",
                    f"Смена статуса у запроса на {settings.APP_TITLE}",
                    {
                        "request_status": new_status.value,
                        "name": current_user.firstname,
                        "benefit_image": (
                            benefit.images[0].image_url
                            if benefit.images
                            else "https://digital-portfolio.hb.ru-msk.vkcloud-storage.ru/Image.png"
                        ),
                        "benefit_name": benefit.name,
                        "benefit_price": benefit.coins_cost,
                        "benefit_url": f"https://{settings.DOMAIN}/main/benefits/{benefit.id}",
                        "requests_url": f"https://{settings.DOMAIN}/main/history",
                    },
                    background_tasks,
                )

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
        return []

    @staticmethod
    async def change_benefit_amount(
        amount: int, benefit_id: int, benefits_service: BenefitsService
    ) -> None:
        try:
            benefit = await benefits_service.read_by_id(benefit_id)
        except Exception:
            raise

        if benefit.amount is not None:
            if benefit.amount == 0 and amount < 0:
                raise service_exceptions.EntityUpdateError(
                    "Benefit Request", benefit_id, "Amount cannot be negative"
                )
            update_data = BenefitUpdate.model_validate(
                {"amount": benefit.amount + amount}
            )
            await benefits_service.update_by_id(benefit.id, update_data)

    @staticmethod
    async def change_coins(
        benefit_id: int,
        user_id: int,
        remove: bool,
        benefits_service: BenefitsService,
        users_service: UsersService,
    ) -> None:
        try:
            benefit = await benefits_service.read_by_id(benefit_id)
        except Exception:
            raise

        try:
            user = await users_service.read_by_id(user_id)
        except Exception:
            raise

        if benefit.adaptation_required and not user.is_adapted:
            raise service_exceptions.EntityCreateError(
                "Benefit Request", "User has not passed adaptation period"
            )

        if remove:
            if user.coins < benefit.coins_cost:
                raise service_exceptions.EntityCreateError(
                    "Benefit Request", "User does not have enough coins"
                )
            if user.level < benefit.min_level_cost:
                raise service_exceptions.EntityCreateError(
                    "Benefit Request", "User does not have required level"
                )

        coins_cost = benefit.coins_cost if remove else -benefit.coins_cost
        update_data = UserUpdate.model_validate({"coins": user.coins - coins_cost})
        await users_service.update_by_id(user_id, update_data)
