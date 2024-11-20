from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

import src.repositories.exceptions as repo_exceptions
import src.schemas.request as schemas
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.config import get_settings
from src.db.db import async_session_factory, get_transaction_session
from src.repositories.benefit_requests import BenefitRequestsRepository
from src.repositories.benefits import BenefitsRepository
from src.repositories.users import UsersRepository
from src.services.base import BaseService

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
    ) -> list[read_schema]:
        async with async_session_factory() as session:
            try:
                if current_user.role == user_schemas.UserRole.ADMIN:
                    legal_entity_id = None
                elif current_user.role == user_schemas.UserRole.HR:
                    legal_entity_id = current_user.legal_entity_id
                    if legal_entity_id is None:
                        raise service_exceptions.EntityReadError(
                            self.__class__.__name__,
                            "HR user has no legal_entity_id",
                        )

                requests = await self.repo.read_all(
                    session, status, sort_by, sort_order, page, limit, legal_entity_id
                )
            except repo_exceptions.EntityReadError as e:
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

            validated_requests = []

            for req in requests:
                validated_requests.append(self.read_schema.model_validate(req))

            return validated_requests

    async def read_by_user_id(self, user_id: int) -> Optional[list[read_schema]]:
        async with async_session_factory() as session:
            try:
                entities = await self.repo.read_by_user_id(session, user_id)

            except Exception as e:
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

            if entities:
                return [self.read_schema.model_validate(entity) for entity in entities]
            return []

    async def create(
        self,
        create_schema: schemas.BenefitRequestCreate,
        current_user: user_schemas.UserRead = None,
    ) -> read_schema:
        request_data = create_schema.model_dump(exclude_unset=True)
        request_data["user_id"] = current_user.id

        benefits_repo = BenefitsRepository()
        users_repo = UsersRepository()

        async with get_transaction_session() as session:
            try:
                benefit = await benefits_repo.read_by_id(
                    session, create_schema.benefit_id
                )
                if benefit is None:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__,
                        f"benefit_id: {create_schema.benefit_id}",
                    )

                user = await users_repo.read_by_id(session, request_data["user_id"])
                if user is None:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__,
                        f"user_id: {request_data['user_id']}",
                    )

                # Perform validations
                if benefit.adaptation_required and not user.is_adapted:
                    raise service_exceptions.EntityCreateError(
                        "Benefit Request", "User has not passed adaptation period"
                    )

                if user.coins < benefit.coins_cost:
                    raise service_exceptions.EntityCreateError(
                        "Benefit Request", "User does not have enough coins"
                    )

                if user.level < benefit.min_level_cost:
                    raise service_exceptions.EntityCreateError(
                        "Benefit Request", "User does not have required level"
                    )

                if benefit.amount is not None:
                    new_amount = benefit.amount - 1
                    if new_amount < 0:
                        raise service_exceptions.EntityUpdateError(
                            self.__class__.__name__, "Insufficient benefit amount"
                        )
                    # Decrement benefit amount
                    await benefits_repo.update_by_id(
                        session, benefit.id, {"amount": new_amount}
                    )

                # Decrement user's coins
                new_coins = user.coins - benefit.coins_cost
                await users_repo.update_by_id(session, user.id, {"coins": new_coins})

                # Set status
                if current_user.role == user_schemas.UserRole.EMPLOYEE:
                    request_data["status"] = schemas.BenefitStatus.PENDING

                # Create the benefit request
                created_request = await self.repo.create(session, request_data)

            except repo_exceptions.RepositoryError as e:
                raise service_exceptions.EntityCreateError(
                    self.create_schema.__name__, str(e)
                )

        return self.read_schema.model_validate(created_request)

    async def update_by_id(
        self,
        entity_id: int,
        update_schema: schemas.BenefitRequestUpdate,
        current_user: user_schemas.UserRead = None,
        background_tasks: BackgroundTasks = None,
    ) -> Optional[read_schema]:
        benefits_repo = BenefitsRepository()
        users_repo = UsersRepository()

        async with get_transaction_session() as session:
            try:
                existing_request = await self.repo.read_by_id(session, entity_id)
                if not existing_request:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__, f"entity_id: {entity_id}"
                    )

                benefit = await benefits_repo.read_by_id(
                    session, existing_request.benefit_id
                )
                user = await users_repo.read_by_id(session, existing_request.user_id)

                old_status = existing_request.status
                new_status = update_schema.status or old_status

                if old_status.value in [
                    schemas.BenefitStatus.DECLINED,
                    schemas.BenefitStatus.APPROVED,
                ]:
                    raise service_exceptions.EntityUpdateError(
                        self.__class__.__name__,
                        "You cannot update declined or approved benefit request",
                    )

                # Declining benefit request
                if new_status.value == schemas.BenefitStatus.DECLINED:
                    if (
                        current_user.id == existing_request.user_id
                        or current_user.role
                        in [
                            user_schemas.UserRole.HR.value,
                            user_schemas.UserRole.ADMIN.value,
                        ]
                    ):
                        # Restore amount
                        if benefit.amount is not None:
                            new_amount = benefit.amount + 1

                            await benefits_repo.update_by_id(
                                session, benefit.id, {"amount": new_amount}
                            )

                        # Restore user's coins
                        new_coins = user.coins + benefit.coins_cost
                        await users_repo.update_by_id(
                            session, user.id, {"coins": new_coins}
                        )
                    else:
                        raise service_exceptions.EntityUpdateError(
                            self.__class__.__name__,
                            "You cannot decline this benefit request",
                        )

                is_updated = await self.repo.update_by_id(
                    session,
                    entity_id,
                    update_schema.model_dump(),
                )
                if not is_updated:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__, f"entity_id: {entity_id}"
                    )

                entity = await self.repo.read_by_id(session, entity_id)

            except Exception as e:
                raise service_exceptions.EntityUpdateError(
                    self.__class__.__name__, str(e)
                )

        return self.read_schema.model_validate(entity)

    async def delete_by_id(
        self, entity_id: int, session: Optional[AsyncSession] = None
    ) -> bool:
        benefits_repo = BenefitsRepository()
        users_repo = UsersRepository()

        async with get_transaction_session() as session:
            try:
                existing_request = await self.repo.read_by_id(session, entity_id)
                if not existing_request:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__, f"entity_id {entity_id}"
                    )

                benefit = await benefits_repo.read_by_id(
                    session, existing_request.benefit_id
                )
                user = await users_repo.read_by_id(session, existing_request.user_id)

                if benefit.amount is not None:
                    new_amount = benefit.amount + 1

                    if new_amount < 0:
                        raise service_exceptions.EntityUpdateError(
                            self.__class__.__name__, "Insufficient benefit amount"
                        )

                    await benefits_repo.update_by_id(
                        session, benefit.id, {"amount": new_amount}
                    )

                new_coins = user.coins + benefit.coins_cost
                await users_repo.update_by_id(session, user.id, {"coins": new_coins})

                is_deleted = await self.repo.delete_by_id(session, entity_id=entity_id)
                if not is_deleted:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__, f"entity_id {entity_id}"
                    )
            except Exception as e:
                raise service_exceptions.EntityDeleteError(
                    self.__class__.__name__, str(e)
                )

        return is_deleted
