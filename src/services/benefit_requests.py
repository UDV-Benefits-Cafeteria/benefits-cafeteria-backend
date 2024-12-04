from io import BytesIO
from typing import BinaryIO, Optional

import pandas as pd
from elasticsearch import AsyncElasticsearch
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

import src.repositories.exceptions as repo_exceptions
import src.schemas.request as schemas
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.config import get_settings
from src.db.db import async_session_factory, get_transaction_session
from src.logger import service_logger
from src.repositories.benefit_requests import BenefitRequestsRepository
from src.repositories.benefits import BenefitsRepository
from src.repositories.users import UsersRepository
from src.services.base import BaseService
from src.utils.parser.export_timezone_helper import prepare_entities_for_export

settings = get_settings()


class BenefitRequestsService(
    BaseService[
        schemas.BenefitRequestCreate,
        schemas.BenefitRequestRead,
        schemas.BenefitRequestUpdate,
    ]
):
    def __init__(self, es_client: Optional[AsyncElasticsearch] = None):
        self.repo: BenefitRequestsRepository = BenefitRequestsRepository()
        self.users_repo: UsersRepository = UsersRepository(es_client)
        self.benefits_repo: BenefitsRepository = BenefitsRepository(es_client)

    create_schema = schemas.BenefitRequestCreate
    read_schema = schemas.BenefitRequestRead
    update_schema = schemas.BenefitRequestUpdate

    async def read_all(
        self,
        current_user: user_schemas.UserRead = None,
        legal_entities: Optional[list[int]] = None,
        status: Optional[schemas.BenefitStatus] = None,
        sort_by: Optional[schemas.BenefitRequestSortFields] = None,
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 10,
    ) -> list[read_schema]:
        service_logger.info(
            f"Reading all {self.read_schema.__name__} entities (Page: {page}, Limit: {limit})"
        )

        async with async_session_factory() as session:
            try:
                legal_entity_ids = await self._validate_legal_entities(
                    current_user=current_user, legal_entities=legal_entities
                )

                if status == schemas.BenefitStatus.PROCESSING:
                    requests = await self.repo.read_all(
                        session=session,
                        status=status,
                        legal_entity_ids=legal_entity_ids,
                        performer_id=current_user.id,
                        sort_by=sort_by,
                        sort_order=sort_order,
                        page=page,
                        limit=limit,
                    )
                else:
                    requests = await self.repo.read_all(
                        session=session,
                        status=status,
                        legal_entity_ids=legal_entity_ids,
                        sort_by=sort_by,
                        sort_order=sort_order,
                        page=page,
                        limit=limit,
                    )
            except repo_exceptions.EntityReadError as e:
                service_logger.error(f"Error reading all entities: {str(e)}")
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

            validated_requests = [
                self.read_schema.model_validate(req) for req in requests
            ]

        service_logger.info(f"Successfully fetched {len(validated_requests)} entities.")
        return validated_requests

    async def export_benefit_requests(
        self,
        current_user: user_schemas.UserRead,
        legal_entities: Optional[list[int]] = None,
        status: Optional[schemas.BenefitStatus] = None,
    ) -> BinaryIO:
        benefit_requests: list[
            schemas.BenefitRequestReadExcel
        ] = await self.read_all_excel(
            current_user=current_user,
            legal_entities=legal_entities,
            status=status,
        )

        if not benefit_requests:
            raise service_exceptions.EntityReadError(
                self.__class__.__name__, "No benefit requests found for export"
            )

        benefit_requests = prepare_entities_for_export(benefit_requests)

        df = pd.DataFrame([request.model_dump() for request in benefit_requests])

        column_mapping = {
            "id": "ID",
            "status": "Статус",
            "comment": "Комментарий",
            "benefit_name": "Название бенефита",
            "user_email": "email пользователя",
            "user_fullname": "ФИО пользователя",
            "performer_email": "email сотрудника HR",
            "performer_fullname": "ФИО сотрудника HR",
            "created_at": "Время создания",
            "updated_at": "Время последней модификации",
        }

        df.rename(columns=column_mapping, inplace=True)

        columns_order = list(column_mapping.values())

        df = df[columns_order]

        excel_file: BinaryIO = BytesIO()

        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        excel_file.seek(0)

        return excel_file

    # The difference from read_all method is that this method does not take sort_by, order_dy, page, limit parameters AND it returns schemas.BenefitRequestReadExcel
    async def read_all_excel(
        self,
        current_user: user_schemas.UserRead,
        legal_entities: Optional[list[int]] = None,
        status: Optional[schemas.BenefitStatus] = None,
    ) -> list[schemas.BenefitRequestReadExcel]:
        service_logger.info(f"Reading all {self.read_schema.__name__} entities")

        async with async_session_factory() as session:
            try:
                legal_entity_ids = await self._validate_legal_entities(
                    current_user=current_user, legal_entities=legal_entities
                )

                requests = await self.repo.read_all_excel(
                    session=session, status=status, legal_entity_ids=legal_entity_ids
                )
            except repo_exceptions.EntityReadError as e:
                service_logger.error(f"Error reading all entities: {str(e)}")
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

            validated_requests = [
                schemas.BenefitRequestReadExcel.model_validate(req) for req in requests
            ]

        service_logger.info(f"Successfully fetched {len(validated_requests)} entities.")
        return validated_requests

    async def _validate_legal_entities(
        self,
        current_user: user_schemas.UserRead,
        legal_entities: Optional[list[int]] = None,
    ) -> Optional[list[int]]:
        if current_user.role == user_schemas.UserRole.ADMIN:
            # Can be None
            legal_entity_ids = legal_entities
        else:
            legal_entity_ids = None
            if (
                legal_entities != [current_user.legal_entity_id]
                and current_user.legal_entity_id is not None
            ) or legal_entities == [current_user.legal_entity_id]:
                legal_entity_ids = [current_user.legal_entity_id]

            if legal_entity_ids is None:
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__,
                    "HR user has no legal_entity_id",
                )
        return legal_entity_ids

    async def read_by_user_id(self, user_id: int) -> Optional[list[read_schema]]:
        service_logger.info(
            f"Reading {self.read_schema.__name__} with User ID: {user_id}"
        )

        async with async_session_factory() as session:
            try:
                entities = await self.repo.read_by_user_id(session, user_id)

            except Exception as e:
                service_logger.error(
                    f"Error reading {self.read_schema.__name__} with User ID: {user_id}"
                )
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

        service_logger.info(f"Successfully fetched {len(entities)} entities.")
        if entities:
            return [self.read_schema.model_validate(entity) for entity in entities]
        return []

    async def create(
        self,
        create_schema: schemas.BenefitRequestCreate,
        current_user: user_schemas.UserRead = None,
    ) -> read_schema:
        service_logger.info(f"Creating benefit request for user_id: {current_user.id}")

        request_data = create_schema.model_dump(exclude_unset=True)
        request_data["user_id"] = current_user.id

        async with get_transaction_session() as session:
            try:
                benefit = await self.benefits_repo.read_by_id(
                    session, create_schema.benefit_id
                )
                if benefit is None:
                    service_logger.warning(
                        f"Benefit with ID {create_schema.benefit_id} not found"
                    )
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__,
                        f"benefit_id: {create_schema.benefit_id}",
                    )

                user = await self.users_repo.read_by_id(
                    session, request_data["user_id"]
                )
                if user is None:
                    service_logger.warning(
                        f"User with ID {request_data['user_id']} not found"
                    )
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__,
                        f"user_id: {request_data['user_id']}",
                    )

                # Perform validations
                if benefit.adaptation_required and not user.is_adapted:
                    service_logger.warning("User has not passed adaptation period")
                    raise service_exceptions.EntityCreateError(
                        "Benefit Request", "User has not passed adaptation period"
                    )

                if user.coins < benefit.coins_cost:
                    service_logger.warning("Insufficient coins for benefit")
                    raise service_exceptions.EntityCreateError(
                        "Benefit Request", "User does not have enough coins"
                    )

                if user.level < benefit.min_level_cost:
                    service_logger.warning("Insufficient level for benefit")
                    raise service_exceptions.EntityCreateError(
                        "Benefit Request", "User does not have required level"
                    )

                if benefit.amount is not None:
                    new_amount = benefit.amount - 1
                    if new_amount < 0:
                        service_logger.warning("Insufficient benefit amount")
                        raise service_exceptions.EntityUpdateError(
                            self.__class__.__name__, "Insufficient benefit amount"
                        )
                    # Decrement benefit amount
                    await self.benefits_repo.update_by_id(
                        session, benefit.id, {"amount": new_amount}
                    )

                # Decrement user's coins
                new_coins = user.coins - benefit.coins_cost
                await self.users_repo.update_by_id(
                    session, user.id, {"coins": new_coins}
                )

                # Set status
                if current_user.role == user_schemas.UserRole.EMPLOYEE:
                    request_data["status"] = schemas.BenefitStatus.PENDING

                # Create the benefit request
                created_request = await self.repo.create(session, request_data)

            except repo_exceptions.RepositoryError as e:
                service_logger.error(
                    f"Error creating {self.create_schema.__name__}: {str(e)}"
                )
                raise service_exceptions.EntityCreateError(
                    self.create_schema.__name__, str(e)
                )

        service_logger.info(
            "Benefit request created successfully",
            extra={"request_id": created_request.id},
        )
        return self.read_schema.model_validate(created_request)

    async def update_by_id(
        self,
        entity_id: int,
        update_schema: schemas.BenefitRequestUpdate,
        current_user: user_schemas.UserRead = None,
        background_tasks: BackgroundTasks = None,
    ) -> Optional[read_schema]:
        service_logger.info(
            f"Updating {self.update_schema.__name__} with ID: {entity_id}"
        )

        async with get_transaction_session() as session:
            try:
                existing_request = await self.repo.read_by_id(session, entity_id)
                if not existing_request:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__, f"entity_id: {entity_id}"
                    )

                benefit = await self.benefits_repo.read_by_id(
                    session, existing_request.benefit_id
                )
                user = await self.users_repo.read_by_id(
                    session, existing_request.user_id
                )

                old_status = existing_request.status
                new_status = update_schema.status or old_status

                if old_status.value in [
                    schemas.BenefitStatus.DECLINED,
                    schemas.BenefitStatus.APPROVED,
                ]:
                    raise service_exceptions.EntityUpdateError(
                        self.read_schema.__name__,
                        "You cannot update declined or approved benefit request",
                    )

                # If old status is 'pending' then the request was just created and needs performer_id to be set
                if old_status.value == schemas.BenefitStatus.PENDING:
                    update_schema.performer_id = current_user.id

                # These users have permission to edit the request:
                # Admin,
                # HR who is considered 'performer' for the request,
                # User if we change status from 'pending' to 'declined'.
                if current_user.role != user_schemas.UserRole.ADMIN:
                    if (
                        current_user.id
                        not in [
                            existing_request.performer_id,
                            existing_request.user_id,
                            update_schema.performer_id,
                        ]
                        or current_user.legal_entity_id != user.legal_entity_id
                    ):
                        raise service_exceptions.EntityUpdateError(
                            self.read_schema.__name__,
                            "You do not have the permission to edit this request",
                        )

                # Handle the case where employee user declines anything but pending request
                if current_user.role == user_schemas.UserRole.EMPLOYEE:
                    if (
                        new_status.value != schemas.BenefitStatus.DECLINED
                        and old_status != schemas.BenefitStatus.PENDING
                    ):
                        raise service_exceptions.EntityUpdateError(
                            self.read_schema.__name__,
                            "You do not have the permission to edit this request",
                        )

                # Perform update operation
                if benefit.amount is not None:
                    new_amount = benefit.amount + 1

                    await self.benefits_repo.update_by_id(
                        session, benefit.id, {"amount": new_amount}
                    )

                new_coins = user.coins + benefit.coins_cost
                await self.users_repo.update_by_id(
                    session, user.id, {"coins": new_coins}
                )

                is_updated: bool = await self.repo.update_by_id(
                    session,
                    entity_id,
                    update_schema.model_dump(),
                )
                if not is_updated:
                    raise service_exceptions.EntityNotFoundError(
                        self.read_schema.__name__, str(entity_id)
                    )

                entity = await self.repo.read_by_id(session, entity_id)

            except Exception as e:
                service_logger.error(
                    f"Error updating entity with ID {entity_id}: {str(e)}"
                )
                raise service_exceptions.EntityUpdateError(
                    self.__class__.__name__, str(e)
                )

        service_logger.info(
            f"Successfully updated {self.update_schema.__name__} with ID {entity_id}."
        )

        return self.read_schema.model_validate(entity)

    async def delete_by_id(
        self, entity_id: int, session: Optional[AsyncSession] = None
    ) -> bool:
        service_logger.info(
            f"Deleting {self.read_schema.__name__} with ID: {entity_id}"
        )

        async with get_transaction_session() as session:
            try:
                existing_request = await self.repo.read_by_id(session, entity_id)
                if not existing_request:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__, f"entity_id {entity_id}"
                    )

                benefit = await self.benefits_repo.read_by_id(
                    session, existing_request.benefit_id
                )
                user = await self.users_repo.read_by_id(
                    session, existing_request.user_id
                )

                if benefit.amount is not None:
                    new_amount = benefit.amount + 1

                    if new_amount < 0:
                        raise service_exceptions.EntityUpdateError(
                            self.__class__.__name__, "Insufficient benefit amount"
                        )

                    await self.benefits_repo.update_by_id(
                        session, benefit.id, {"amount": new_amount}
                    )

                new_coins = user.coins + benefit.coins_cost
                await self.users_repo.update_by_id(
                    session, user.id, {"coins": new_coins}
                )

                is_deleted = await self.repo.delete_by_id(session, entity_id=entity_id)
            except Exception as e:
                service_logger.error(
                    f"Error deleting entity with ID {entity_id}: {str(e)}"
                )
                raise service_exceptions.EntityDeleteError(
                    self.__class__.__name__, str(e)
                )

        if not is_deleted:
            service_logger.error(f"Entity with ID {entity_id} not found for deletion.")
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"entity_id {entity_id}"
            )

        service_logger.info(f"Successfully deleted entity with ID {entity_id}.")
        return is_deleted
