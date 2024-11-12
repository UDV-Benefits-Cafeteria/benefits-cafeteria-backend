import os
from typing import Any, Optional

from fastapi import BackgroundTasks, UploadFile
from pydantic import ValidationError

import src.repositories.exceptions as repo_exceptions
import src.schemas.user as schemas
import src.services.exceptions as service_exceptions
from src.config import get_settings, logger
from src.repositories.users import UsersRepository
from src.services.base import BaseService
from src.services.legal_entities import LegalEntitiesService
from src.services.positions import PositionsService
from src.utils.parser.excel_parser import initialize_excel_parser
from src.utils.parser.field_parsers import (
    parse_coins,
    parse_hired_at,
    parse_is_adapted,
    parse_role,
)

settings = get_settings()


class UsersService(
    BaseService[schemas.UserCreate, schemas.UserRead, schemas.UserUpdate]
):
    repo = UsersRepository()
    create_schema = schemas.UserCreate
    read_schema = schemas.UserRead
    update_schema = schemas.UserUpdate

    async def search_users(
        self,
        query: Optional[str],
        filters: dict[str, Any],
        sort_by: Optional[str],
        sort_order: str,
        limit: int,
        offset: int,
    ) -> list[schemas.UserRead]:
        try:
            search_results = await self.repo.search_users(
                query=query,
                filters=filters,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset,
            )
            for data in search_results:
                legal_entity_id = data.get("legal_entity_id")
                if legal_entity_id is not None:
                    legal_entity_data = await LegalEntitiesService().read_by_id(
                        legal_entity_id
                    )
                    data["legal_entity"] = legal_entity_data

                position_id = data.get("position_id")
                if position_id is not None:
                    position_data = await PositionsService().read_by_id(position_id)
                    data["position"] = position_data

            users = [self.read_schema.model_validate(data) for data in search_results]
            return users
        except service_exceptions.EntityReadError as e:
            logger.error(f"Error searching users: {e}")
            raise service_exceptions.EntityReadError("User", "", str(e))

    async def create(
        self,
        create_schema: schemas.UserCreate,
        current_user: schemas.UserRead = None,
        background_tasks: BackgroundTasks = None,
    ) -> schemas.UserRead:
        hr_error = self._validate_hr_permissions(
            user_create=create_schema, current_user=current_user
        )
        if hr_error is not None:
            raise service_exceptions.PermissionDeniedError(hr_error)

        await self.send_email(
            create_schema,
            "register.html",
            f"Добро пожаловать на {settings.APP_TITLE}",
            {
                "name": create_schema.firstname,
                "product": settings.APP_TITLE,
                "register_url": f"https://{settings.DOMAIN}/register?email={create_schema.email}",
            },
            background_tasks,
        )

        return await super().create(create_schema)

    async def update_by_id(
        self,
        entity_id: int,
        update_schema: schemas.UserUpdate,
        current_user: schemas.UserRead = None,
        background_tasks: BackgroundTasks = None,
    ) -> schemas.UserRead:
        try:
            user_to_update = await self.read_by_id(entity_id)
        except service_exceptions.EntityNotFoundError:
            raise

        if current_user is not None:
            if current_user.role == schemas.UserRole.HR.value:
                if user_to_update.legal_entity_id != current_user.legal_entity_id:
                    raise service_exceptions.PermissionDeniedError(
                        "HR users cannot update users outside their own legal entity."
                    )
            elif current_user.role == schemas.UserRole.EMPLOYEE:
                if user_to_update.id != current_user.id:
                    raise service_exceptions.PermissionDeniedError(
                        "You can only change yourself"
                    )

        if update_schema.coins and current_user:
            if user_to_update.coins > update_schema.coins:
                await self.send_email(
                    user_to_update,
                    "balance-changes.html",
                    f"Списание с баланса на {settings.APP_TITLE}",
                    {
                        "operation_type": "decrease",
                        "name": current_user.firstname,
                        "amount_change": user_to_update.coins - update_schema.coins,
                        "current_balance": update_schema.coins,
                        "home_url": f"https://{settings.DOMAIN}/main/account",
                    },
                    background_tasks,
                )
            elif user_to_update.coins < update_schema.coins:
                await self.send_email(
                    user_to_update,
                    "balance-changes.html",
                    f"Пополнение баланса на {settings.APP_TITLE}",
                    {
                        "operation_type": "increase",
                        "name": current_user.firstname,
                        "amount_change": update_schema.coins - user_to_update.coins,
                        "current_balance": update_schema.coins,
                        "home_url": f"https://{settings.DOMAIN}/main/account",
                    },
                    background_tasks,
                )

        return await super().update_by_id(entity_id, update_schema)

    async def read_by_email(self, email: str) -> Optional[schemas.UserRead]:
        try:
            entity = await self.repo.read_by_email(email)
            if not entity:
                logger.warning(
                    f"{self.read_schema.__name__} with email {email} not found."
                )
                raise service_exceptions.EntityNotFoundError(
                    self.read_schema.__name__, email
                )

            validated_entity = self.read_schema.model_validate(entity)
            logger.info(
                f"Successfully retrieved {self.read_schema.__name__} with email: {email}"
            )
            return validated_entity
        except repo_exceptions.EntityReadError as e:
            logger.error(
                f"Error reading {self.read_schema.__name__} with email {email}: {str(e)}"
            )
            raise service_exceptions.EntityReadError(
                self.read_schema.__name__, email, str(e)
            )

    async def parse_users_from_excel(
        self,
        file_contents: bytes,
        positions_service: PositionsService,
        legal_entities_service: LegalEntitiesService,
        current_user: schemas.UserRead,
    ) -> tuple[list[schemas.UserCreate], list[dict[str, Any]]]:
        """
        Parses users from an Excel file.

        Args:
            file_contents (bytes): The raw bytes of the uploaded Excel file.
            positions_service (PositionsService): Service to resolve position IDs.
            legal_entities_service (LegalEntitiesService): Service to resolve legal entity IDs.
            current_user (schemas.UserRead): The user performing the upload.

        Returns:
            tuple[list[schemas.UserCreate], list[dict[str, Any]]]:
                A tuple containing a list of valid `UserCreate` instances and a list of error dictionaries.
        """
        parser = initialize_excel_parser(
            required_columns=[
                "email",
                "фамилия",
                "имя",
                "отчество",
                "роль",
                "дата найма",
                "адаптационный период",
                "ю-коины",
                "должность",
                "юр. лицо",
            ],
            column_mappings={
                "email": "email",
                "фамилия": "lastname",
                "имя": "firstname",
                "отчество": "middlename",
                "роль": "role",
                "дата найма": "hired_at",
                "адаптационный период": "is_adapted",
                "ю-коины": "coins",
                "должность": "position_name",
                "юр. лицо": "legal_entity_name",
            },
            model_class=schemas.UserCreateExcel,
            field_parsers={
                "role": parse_role,
                "is_adapted": parse_is_adapted,
                "hired_at": parse_hired_at,
                "coins": parse_coins,
            },
        )

        valid_users_excel, parse_errors = parser.parse_excel(file_contents)

        valid_users = []
        service_errors = []

        for idx, user_excel_raw in enumerate(valid_users_excel):
            row_number = idx + 2

            user_excel = schemas.UserCreateExcel.model_validate(user_excel_raw)

            user_create, error = await self._process_user_row(
                user_excel,
                row_number,
                positions_service,
                legal_entities_service,
                current_user,
            )

            if error:
                service_errors.append(error)
            else:
                valid_users.append(user_create)

        return valid_users, parse_errors + service_errors

    @staticmethod
    async def resolve_position_id(
        position_name: Optional[str], positions_service: PositionsService
    ) -> Optional[int]:
        if position_name:
            position = await positions_service.read_by_name(position_name)
            return position.id
        return None

    @staticmethod
    async def resolve_legal_entity_id(
        legal_entity_name: Optional[str],
        legal_entities_service: LegalEntitiesService,
    ) -> Optional[int]:
        if legal_entity_name:
            legal_entity = await legal_entities_service.read_by_name(legal_entity_name)
            return legal_entity.id
        return None

    async def _process_user_row(
        self,
        user_excel: schemas.UserCreateExcel,
        row_number: int,
        positions_service: PositionsService,
        legal_entities_service: LegalEntitiesService,
        current_user: schemas.UserRead,
    ) -> tuple[Optional[schemas.UserCreate], Optional[dict[str, Any]]]:
        """
        Processes a single user row from the Excel file.

        Args:
            user_excel (schemas.UserCreateExcel): The user data extracted from the Excel row.
            row_number (int): The Excel row number for error reporting.
            positions_service (PositionsService): Service to resolve position IDs.
            legal_entities_service (LegalEntitiesService): Service to resolve legal entity IDs.
            current_user (schemas.UserRead): The user performing the operation.

        Returns:
            tuple[Optional[schemas.UserCreate], Optional[dict[str, Any]]]:
                A tuple containing the created `UserCreate` instance if successful,
                or an error dictionary if processing fails.
        """

        try:
            data = user_excel.model_dump()

            position_name = data.pop("position_name", None)

            if position_name:
                try:
                    data["position_id"] = await self.resolve_position_id(
                        position_name, positions_service
                    )

                except service_exceptions.EntityNotFoundError:
                    return None, {
                        "row": row_number,
                        "error": f"Должность '{position_name}' не найдена.",
                    }

            legal_entity_name = data.pop("legal_entity_name", None)

            if legal_entity_name:
                try:
                    data["legal_entity_id"] = await self.resolve_legal_entity_id(
                        legal_entity_name, legal_entities_service
                    )

                except service_exceptions.EntityNotFoundError:
                    return None, {
                        "row": row_number,
                        "error": f"Юридическое лицо '{legal_entity_name}' не найдено.",
                    }

            try:
                user_create = schemas.UserCreate.model_validate(data)

            except ValidationError as ve:
                error_messages = "; ".join(
                    [f"{err['loc'][0]}: {err['msg']}" for err in ve.errors()]
                )
                return None, {
                    "row": row_number,
                    "error": f"Ошибка валидации: {error_messages}",
                }

            try:
                existing_user = await self.read_by_email(user_create.email)
                if existing_user:
                    return None, {
                        "row": row_number,
                        "error": f"Email '{user_create.email}' уже используется.",
                    }

            except service_exceptions.EntityNotFoundError:
                pass

            hr_error = self._validate_hr_permissions(user_create, current_user)

            if hr_error:
                return None, {
                    "row": row_number,
                    "error": hr_error,
                }

            return user_create, None

        except Exception as e:
            return None, {
                "row": row_number,
                "error": f"Неожиданная ошибка: {str(e)}",
            }

    @staticmethod
    def _validate_hr_permissions(
        user_create: schemas.UserCreate, current_user: schemas.UserRead
    ) -> Optional[str]:
        if current_user.role == schemas.UserRole.HR:
            if user_create.role == schemas.UserRole.ADMIN:
                return "HR пользователи не могут создавать админов."

            if (
                user_create.legal_entity_id is not None
                and user_create.legal_entity_id != current_user.legal_entity_id
            ):
                return "HR пользователи не могут создавать пользователей вне своего юридического лица."

            if user_create.legal_entity_id is None:
                user_create.legal_entity_id = current_user.legal_entity_id

        return None

    async def update_image(
        self, image: Optional[UploadFile], user_id: int
    ) -> Optional[schemas.UserRead]:
        """
        Updates the user's profile image by uploading a new image file, updating the image URL
        in the database, and re-indexing the user data if the update is successful.

        Args:
           image (Optional[UploadFile]): The new image file to be uploaded. If provided,
               the filename is modified to include the user's unique ID and a UUID prefix.
           user_id (int): The ID of the user whose image is being updated.

        Returns:
           The updated user data after successfully updating the image URL in the database.

        Raises:
           EntityNotFoundError: If the user with the given ID is not found in the database.
           EntityUpdateError: If there is an error while updating the image URL in the database.

        Notes:
           - If the image is not provided, sets image_url to null.
           - Logs warnings if the user is not found and errors if the update operation fails.
           - Calls the `index_user` method to update the search index with the modified user data.
        """
        if image:
            _, extension = os.path.splitext(image.filename)
            image.filename = f"userdata/{user_id}/user_image" + extension
        try:
            is_updated = await self.repo.update_by_id(user_id, {"image_url": image})
            if not is_updated:
                logger.warning(
                    f"{self.read_schema.__name__} with ID {user_id} not found for update."
                )
                raise service_exceptions.EntityNotFoundError(
                    self.read_schema.__name__, user_id
                )

            logger.info(
                f"Successfully updated {self.read_schema.__name__} with ID: {user_id}"
            )
            return await self.read_by_id(user_id)
        except repo_exceptions.EntityUpdateError as e:
            logger.error(
                f"Failed to update {self.read_schema.__name__} with ID {user_id}: {str(e)}"
            )
            raise service_exceptions.EntityUpdateError(
                self.read_schema.__name__, e.read_param, str(e)
            )
