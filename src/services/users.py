import os
from typing import Any, Optional

from fastapi import UploadFile

import src.repositories.exceptions as repo_exceptions
import src.schemas.email as email_schemas
import src.schemas.user as schemas
import src.services.exceptions as service_exceptions
from src.celery.tasks import background_send_mail
from src.config import get_settings, logger
from src.repositories.users import UsersRepository
from src.services.base import BaseService
from src.services.legal_entities import LegalEntitiesService
from src.services.positions import PositionsService
from src.utils.excel_parser import ExcelParser
from src.utils.field_parsers import (
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
    ) -> schemas.UserRead:
        if current_user.role == schemas.UserRole.HR:
            if create_schema.legal_entity_id != current_user.legal_entity_id:
                raise service_exceptions.PermissionDeniedError(
                    "HR users cannot create users outside their own legal entity."
                )

            if create_schema.legal_entity_id is None:
                create_schema.legal_entity_id = current_user.legal_entity_id

        return await super().create(create_schema)

    async def update_by_id(
        self,
        entity_id: int,
        update_schema: schemas.UserUpdate,
        current_user: schemas.UserRead = None,
    ) -> schemas.UserRead:
        try:
            user_to_update = await self.read_by_id(entity_id)
        except service_exceptions.EntityNotFoundError:
            raise

        if current_user is not None:
            if current_user.role == schemas.UserRole.HR:
                if user_to_update.legal_entity_id != current_user.legal_entity_id:
                    raise service_exceptions.PermissionDeniedError(
                        "HR users cannot update users outside their own legal entity."
                    )
            elif current_user.role == schemas.UserRole.EMPLOYEE:
                if user_to_update.id != current_user.id:
                    raise service_exceptions.PermissionDeniedError(
                        "You can only change yourself"
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

    async def parse_users_from_excel(
        self,
        file_contents: bytes,
        positions_service: PositionsService,
        legal_entities_service: LegalEntitiesService,
    ) -> tuple[list[schemas.UserCreate], list[dict[str, Any]]]:
        """
        Parse users from the given Excel file contents.

        :param file_contents: The contents of the Excel file.
        :param positions_service: Instance of PositionsService.
        :param legal_entities_service: Instance of LegalEntitiesService.
        :return: A tuple of (valid_users, errors)
        """

        required_columns = [
            "email",
            "имя",
            "фамилия",
            "роль",
            "дата найма",
            "адаптационный период",
            "отчество",
            "ю-коины",
            "должность",
            "юр. лицо",
        ]

        column_mappings = {
            "email": "email",
            "имя": "firstname",
            "фамилия": "lastname",
            "отчество": "middlename",
            "роль": "role",
            "дата найма": "hired_at",
            "адаптационный период": "is_adapted",
            "ю-коины": "coins",
            "должность": "position_name",
            "юр. лицо": "legal_entity_name",
        }

        field_parsers = {
            "role": parse_role,
            "is_adapted": parse_is_adapted,
            "hired_at": parse_hired_at,
            "coins": parse_coins,
        }

        parser = ExcelParser(
            required_columns=required_columns,
            column_mappings=column_mappings,
            model_class=schemas.UserCreateExcel,
            field_parsers=field_parsers,
        )

        valid_users_excel, errors = parser.parse_excel(file_contents)

        valid_users = []
        final_errors = []

        for idx, user_excel in enumerate(valid_users_excel):
            try:
                data = user_excel.model_dump()
                try:
                    data["position_id"] = await self.resolve_position_id(
                        data.pop("position_name", None), positions_service
                    )

                    data["legal_entity_id"] = await self.resolve_legal_entity_id(
                        data.pop("legal_entity_name", None), legal_entities_service
                    )
                except Exception:
                    pass

                user_create = schemas.UserCreate.model_validate(data)

                try:
                    await self.read_by_email(user_create.email)
                except Exception:
                    pass

                valid_users.append(user_create)
            except Exception as e:
                final_errors.append(
                    {
                        "row": idx + 2,
                        "error": str(e),
                    }
                )

        return valid_users, errors + final_errors

    @staticmethod
    async def send_email_registration(
        user: schemas.UserCreate | schemas.UserRead,
    ) -> None:
        """
        Asynchronously sends a registration email to the user.

        :param user: The user for whom the registration email is being sent. This can be either a
                     UserCreate or UserRead schema, containing information like the user's email and
                     first name.
        :type user: schemas.UserCreate | schemas.UserRead

        :return: None. The function sends a registration email and does not return a value.
        :rtype: None
        """
        email = email_schemas.EmailSchema.model_validate(
            {
                "email": [user.email],
                "body": {
                    "name": user.firstname,
                    "product": settings.APP_TITLE,
                    "register_url": f"https://{settings.DOMAIN}/register?email={user.email}",
                },
            }
        )
        logger.info(f"Sending registration email with data: {email.model_dump()}")

        background_send_mail.delay(
            email.model_dump(),
            f"Регистрация на сайте {settings.APP_TITLE}",
            "register.html",
        )

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
