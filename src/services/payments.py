import warnings

from fastapi import BackgroundTasks

import src.repositories.exceptions as repo_exceptions
import src.schemas.payment as schemas
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.config import logger
from src.repositories.payments import CoinPaymentsRepository
from src.services.base import BaseService
from src.services.users import UsersService

warnings.warn("This file is deprecated and should not be used.", DeprecationWarning)


class CoinPaymentsService(
    BaseService[
        schemas.CoinPaymentCreate, schemas.CoinPaymentRead, schemas.CoinPaymentBase
    ]
):
    repo = CoinPaymentsRepository()
    create_schema = schemas.CoinPaymentCreate
    read_schema = schemas.CoinPaymentRead
    update_schema = schemas.CoinPaymentUpdate

    async def create(
        self,
        create_schema: schemas.CoinPaymentCreate,
        current_user: schemas.UserRead = None,
        background_tasks: BackgroundTasks = None,
    ) -> schemas.CoinPaymentRead:
        user_service = UsersService()
        try:
            receiver = await user_service.read_by_id(create_schema.user_id)
        except service_exceptions.EntityNotFoundError:
            raise service_exceptions.EntityNotFoundError("User", create_schema.user_id)

        if (
            current_user.role == user_schemas.UserRole.HR
            and receiver.legal_entity_id != current_user.legal_entity_id
        ):
            raise service_exceptions.PermissionDeniedError(
                "HR cannot create payments to employees outside their legal entity."
            )

        create_schema.payer_id = current_user.id

        try:
            coin_payment = await super().create(create_schema)
            return coin_payment
        except repo_exceptions.EntityCreateError as e:
            logger.error(f"Error creating CoinPayment: {e}")
            raise service_exceptions.EntityCreateError(
                self.create_schema.__name__, str(e)
            )

    async def update_by_id(
        self,
        entity_id: int,
        update_schema: schemas.CoinPaymentBase,
        current_user: schemas.UserRead = None,
        background_tasks: BackgroundTasks = None,
    ) -> schemas.CoinPaymentRead:
        try:
            coin_payment = await self.read_by_id(entity_id)
        except service_exceptions.EntityNotFoundError:
            raise

        user_service = UsersService()
        try:
            receiver = await user_service.read_by_id(coin_payment.user_id)
        except service_exceptions.EntityNotFoundError:
            raise service_exceptions.EntityNotFoundError("User", coin_payment.user_id)

        if (
            current_user.role == user_schemas.UserRole.HR
            and receiver.legal_entity_id != current_user.legal_entity_id
        ):
            raise service_exceptions.PermissionDeniedError(
                "HR cannot update payments to employees outside their legal entity."
            )

        try:
            updated_payment = await super().update_by_id(entity_id, update_schema)
            return updated_payment
        except repo_exceptions.EntityUpdateError as e:
            logger.error(f"Error updating CoinPayment: {e}")
            raise service_exceptions.EntityUpdateError(
                self.update_schema.__name__, entity_id, str(e)
            )
