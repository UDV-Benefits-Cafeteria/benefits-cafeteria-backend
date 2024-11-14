from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

import src.repositories.exceptions as repo_exceptions
import src.schemas.benefit as benefit_schemas
import src.schemas.request as schemas
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.config import get_settings, logger
from src.db.db import async_session_factory
from src.repositories.benefit_requests import BenefitRequestsRepository
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
        current_user: user_schemas.UserRead = None,
        status: Optional[schemas.BenefitStatus] = None,
        sort_by: Optional[schemas.BenefitRequestSortFields] = None,
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 10,
    ) -> list[schemas.BenefitRequestRead]:
        async with async_session_factory() as session:
            try:
                if current_user.role == user_schemas.UserRole.ADMIN.value:
                    legal_entity_id = None
                elif current_user.role == user_schemas.UserRole.HR.value:
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

                requests = await self.repo.read_all(
                    status, sort_by, sort_order, page, limit, legal_entity_id, session
                )

                validated_requests = []

                for req in requests:
                    validated_requests.append(
                        schemas.BenefitRequestRead.model_validate(req)
                    )

                return validated_requests
            except repo_exceptions.EntityReadError as e:
                raise service_exceptions.EntityReadError(
                    self.read_schema.__name__, e.read_param, str(e)
                )
            finally:
                await session.close()

    async def read_by_user_id(
        self, user_id: int
    ) -> Optional[list[schemas.BenefitRequestRead]]:
        async with async_session_factory() as session:
            try:
                entities = await self.repo.read_by_user_id(user_id, session=session)
                if entities:
                    return [
                        self.read_schema.model_validate(entity) for entity in entities
                    ]
                return []
            except Exception as e:
                logger.error(
                    f"Error reading benefit requests by user ID {user_id}: {e}"
                )
                raise service_exceptions.EntityReadError(
                    self.read_schema.__name__, user_id, str(e)
                )
            finally:
                await session.close()

    async def create(
        self,
        create_schema: schemas.BenefitRequestCreate,
        background_tasks: BackgroundTasks = None,
    ) -> schemas.BenefitRequestRead:
        async with async_session_factory() as session:
            try:
                async with session.begin():
                    benefits_service = BenefitsService()
                    users_service = UsersService()

                    await self.change_benefit_amount(
                        -1, create_schema.benefit_id, benefits_service, session
                    )

                    await self.change_coins(
                        create_schema.benefit_id,
                        create_schema.user_id,
                        True,
                        benefits_service,
                        users_service,
                        session,
                    )

                    created_request = await super().create(
                        create_schema=create_schema, session=session
                    )

                    benefit = await benefits_service.read_by_id(
                        create_schema.benefit_id, session=session
                    )
                    user = await users_service.read_by_id(
                        create_schema.user_id, session=session
                    )

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
            except Exception as e:
                logger.error(f"Error creating benefit request: {e}")
                raise service_exceptions.EntityCreateError(
                    self.create_schema.__name__, str(e)
                )
            finally:
                await session.close()

    async def update_by_id(
        self,
        entity_id: int,
        update_schema: schemas.BenefitRequestUpdate,
        current_user: user_schemas.UserRead = None,
        background_tasks: BackgroundTasks = None,
    ) -> Optional[schemas.BenefitRequestRead]:
        async with async_session_factory() as session:
            try:
                async with session.begin():
                    existing_request = await self.repo.read_by_id(
                        entity_id, session=session
                    )
                    if not existing_request:
                        raise service_exceptions.EntityNotFoundError(
                            self.read_schema.__name__, entity_id
                        )

                    old_status = existing_request.status
                    new_status = update_schema.status or old_status

                    benefit_id = existing_request.benefit_id

                    benefits_service = BenefitsService()
                    users_service = UsersService()

                    if (
                        old_status.value != "declined"
                        and new_status.value == "declined"
                    ):
                        if (
                            current_user.id == existing_request.user_id
                            or current_user.role
                            in [
                                user_schemas.UserRole.HR.value,
                                user_schemas.UserRole.ADMIN.value,
                            ]
                        ):
                            await self.change_benefit_amount(
                                1, benefit_id, benefits_service, session
                            )
                            await self.change_coins(
                                benefit_id,
                                existing_request.user_id,
                                False,
                                benefits_service,
                                users_service,
                                session,
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
                        if current_user.role in [
                            user_schemas.UserRole.HR.value,
                            user_schemas.UserRole.ADMIN.value,
                        ]:
                            await self.change_benefit_amount(
                                -1, benefit_id, benefits_service, session
                            )
                            await self.change_coins(
                                benefit_id,
                                existing_request.user_id,
                                True,
                                benefits_service,
                                users_service,
                                session,
                            )
                        else:
                            raise service_exceptions.EntityUpdateError(
                                self.read_schema.__name__,
                                entity_id,
                                "You cannot update benefit request",
                            )

                    updated_request = await super().update_by_id(
                        entity_id=entity_id,
                        update_schema=update_schema,
                        session=session,
                    )

                    if new_status.value != "pending":
                        benefit = await benefits_service.read_by_id(
                            benefit_id, session=session
                        )

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

            except Exception as e:
                logger.error(f"Error updating benefit request: {e}")
                raise service_exceptions.EntityUpdateError(
                    self.read_schema.__name__, entity_id, str(e)
                )
            finally:
                await session.close()

    async def delete_by_id(
        self, entity_id: int, session: Optional[AsyncSession] = None
    ) -> bool:
        async with async_session_factory() as session:
            try:
                async with session.begin():
                    existing_request = await self.repo.read_by_id(
                        entity_id, session=session
                    )
                    if not existing_request:
                        raise service_exceptions.EntityNotFoundError(
                            self.read_schema.__name__, entity_id
                        )

                    benefits_service = BenefitsService()
                    users_service = UsersService()

                    await self.change_benefit_amount(
                        1, existing_request.benefit_id, benefits_service, session
                    )
                    await self.change_coins(
                        existing_request.benefit_id,
                        existing_request.user_id,
                        False,
                        benefits_service,
                        users_service,
                        session,
                    )

                    deleted = await super().delete_by_id(
                        entity_id=entity_id, session=session
                    )
                    if not deleted:
                        raise service_exceptions.EntityDeletionError(
                            "Benefit Request", entity_id, "Failed to delete request"
                        )
                    return deleted
            except Exception as e:
                logger.error(f"Error deleting benefit request: {e}")
                raise service_exceptions.EntityDeletionError(
                    "Benefit Request", entity_id, str(e)
                )
            finally:
                await session.close()

    @staticmethod
    async def change_benefit_amount(
        amount: int,
        benefit_id: int,
        benefits_service: BenefitsService,
        session_external: AsyncSession,
    ) -> None:
        benefit = await benefits_service.read_by_id(
            benefit_id, session=session_external
        )
        if benefit.amount is not None:
            new_amount = benefit.amount + amount
            if new_amount < 0:
                raise service_exceptions.EntityUpdateError(
                    "Benefit", benefit_id, "Insufficient benefit amount"
                )
            update_data = benefit_schemas.BenefitUpdate(amount=new_amount)
            await benefits_service.update_by_id(
                benefit.id, update_data, session=session_external
            )

    @staticmethod
    async def change_coins(
        benefit_id: int,
        user_id: int,
        remove: bool,
        benefits_service: BenefitsService,
        users_service: UsersService,
        session_external: AsyncSession,
    ) -> None:
        benefit = await benefits_service.read_by_id(
            benefit_id, session=session_external
        )
        user = await users_service.read_by_id(user_id, session=session_external)

        if benefit.adaptation_required and not user.is_adapted:
            raise service_exceptions.EntityCreateError(
                "Benefit Request", "User has not passed adaptation period"
            )

        coins_cost = benefit.coins_cost
        if remove:
            if user.coins < coins_cost:
                raise service_exceptions.EntityCreateError(
                    "Benefit Request", "User does not have enough coins"
                )
            if user.level < benefit.min_level_cost:
                raise service_exceptions.EntityCreateError(
                    "Benefit Request", "User does not have required level"
                )
            new_coins = user.coins - coins_cost
        else:
            new_coins = user.coins + coins_cost

        update_data = user_schemas.UserUpdate(coins=new_coins)
        await users_service.update_by_id(user_id, update_data, session=session_external)
