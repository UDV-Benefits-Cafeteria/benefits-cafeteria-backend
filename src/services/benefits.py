import uuid
from typing import Any, Optional, Union

from elasticsearch import AsyncElasticsearch
from fastapi import UploadFile

import src.repositories.exceptions as repo_exceptions
import src.schemas.benefit as schemas
import src.schemas.category as category_schemas
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.db.db import get_transaction_session
from src.logger import service_logger
from src.repositories.benefit_images import BenefitImagesRepository
from src.repositories.benefits import BenefitsRepository
from src.services.base import BaseService
from src.services.categories import CategoriesService
from src.utils.parser.excel_parser import initialize_excel_parser
from src.utils.parser.field_parsers import parse_bool_field, parse_date_field


class BenefitsService(
    BaseService[schemas.BenefitCreate, schemas.BenefitRead, schemas.BenefitUpdate]
):
    def __init__(self, es_client: Optional[AsyncElasticsearch] = None):
        self.repo: BenefitsRepository = BenefitsRepository(es_client)

    create_schema = schemas.BenefitCreate
    read_schema = schemas.BenefitRead
    update_schema = schemas.BenefitUpdate

    async def search_benefits(
        self,
        current_user: user_schemas.UserRead,
        query: Optional[str],
        filters: Optional[dict] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0,
    ) -> list[Union[schemas.BenefitReadShortPublic, schemas.BenefitReadShortPrivate]]:
        service_logger.info("Searching benefits", extra={"user_id": current_user.id})

        try:
            search_results = await self.repo.search_benefits(
                query=query,
                filters=filters,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset,
            )
        except repo_exceptions.EntityReadError as e:
            service_logger.error(
                f"Error searching benefits: {e}", extra={"user_id": current_user.id}
            )
            raise service_exceptions.EntityReadError(self.__class__.__name__, str(e))

        benefits = []
        for data in search_results:
            # Hide unsafe data from employees
            if current_user.role in [
                user_schemas.UserRole.HR,
                user_schemas.UserRole.ADMIN,
            ]:
                benefit = schemas.BenefitReadShortPrivate.model_validate(data)
            else:
                benefit = schemas.BenefitReadShortPublic.model_validate(data)
            benefits.append(benefit)

        service_logger.info(
            f"Found {len(benefits)} benefits", extra={"user_id": current_user.id}
        )
        return benefits

    async def read_by_id(
        self, entity_id: int, current_user: user_schemas.UserRead = None
    ) -> Union[schemas.BenefitRead, schemas.BenefitReadPublic]:
        benefit = await super().read_by_id(entity_id)
        if current_user is not None:
            if current_user.role in [
                user_schemas.UserRole.HR,
                user_schemas.UserRole.ADMIN,
            ]:
                return benefit

        return schemas.BenefitReadPublic.model_validate(benefit)

    async def add_images(self, images: list[UploadFile], benefit_id: int):
        """
        Add images to a specific benefit.

        Args:
        - images (list[UploadFile]): A list of image files to associate with the benefit.
        - benefit_id (int): The ID of the benefit to which the images will be linked.

        Raises:
        - service_exceptions.EntityCreateError: If an error occurs while creating one of the images in the repository.
        """
        service_logger.info(
            "Adding images to benefit",
            extra={"benefit_id": benefit_id, "image_count": len(images)},
        )

        async with get_transaction_session() as session:
            try:
                for image_data in images:
                    image_data.filename = (
                        f"benefit/{benefit_id}/{uuid.uuid4()}_" + image_data.filename
                    )
                    image = {
                        "benefit_id": benefit_id,
                        "image_url": image_data,
                        "is_primary": True,
                    }

                    await BenefitImagesRepository().create(session, image)
                    service_logger.info(
                        "Image added",
                        extra={"benefit_id": benefit_id},
                    )

                try:
                    benefit = await self.repo.read_by_id(session, benefit_id)
                    await self.repo.index_benefit(benefit)
                    service_logger.info(
                        "Benefit re-indexed after adding images",
                        extra={"benefit_id": benefit_id},
                    )
                except repo_exceptions.EntityReadError as e:
                    raise service_exceptions.EntityReadError(
                        self.__class__.__name__, str(e)
                    )
            except repo_exceptions.EntityCreateError as e:
                service_logger.error(
                    f"Error adding images: {e}", extra={"benefit_id": benefit_id}
                )
                raise service_exceptions.EntityCreateError(
                    self.__class__.__name__, str(e)
                )

    async def remove_images(self, images: list[int]):
        """
        Remove images by their IDs.

        Args:
        - images (list[int]): A list of image IDs to delete.

        Raises:
        - service_exceptions.EntityDeleteError: If an error occurs while deleting one of the images.

        Returns:
        - None: Indicates successful deletion of images.
        """
        service_logger.info("Removing images", extra={"image_ids": images})

        async with get_transaction_session() as session:
            try:
                for image_id in images:
                    image = await BenefitImagesRepository().read_by_id(
                        session, image_id
                    )

                    if image:
                        await BenefitImagesRepository().delete_by_id(
                            session, image.benefit_id
                        )
                        service_logger.info(
                            "Image removed",
                            extra={
                                "image_id": image_id,
                                "benefit_id": image.benefit_id,
                            },
                        )
                        benefit = await self.repo.read_by_id(session, image.benefit_id)
                        await self.repo.index_benefit(benefit)

            except repo_exceptions.EntityDeleteError as e:
                service_logger.error(
                    f"Error removing images: {e}", extra={"image_ids": images}
                )
                raise service_exceptions.EntityDeleteError(
                    self.__class__.__name__, str(e)
                )

    async def parse_benefits_from_excel(
        self,
        file_contents: bytes,
    ) -> tuple[list[schemas.BenefitCreate], list[dict[str, Any]]]:
        """
        Parses benefits from an Excel file.

        Args:
            file_contents (bytes): The raw bytes of the uploaded Excel file.

        Returns:
            tuple[list[BenefitCreate], list[dict[str, Any]]]:
                A tuple containing a list of valid BenefitCreate instances and a list of error dictionaries.
        """
        parser = initialize_excel_parser(
            model_class=schemas.BenefitCreateExcel,
            field_mappings={
                "name": ["название", "имя", "бенефит", "name"],
                "coins_cost": ["стоимость в коинах", "коины", "coins_cost"],
                "min_level_cost": ["минимальный уровень", "min_level_cost"],
                "adaptation_required": ["требуется адаптация", "adaptation_required"],
                "is_active": ["активен", "is_active"],
                "description": ["описание", "description"],
                "real_currency_cost": [
                    "стоимость в валюте",
                    "стоимость в рублях",
                    "real_currency_cost",
                ],
                "amount": ["количество", "amount"],
                "is_fixed_period": ["фиксированный период", "is_fixed_period"],
                "usage_limit": ["лимит использования", "usage_limit"],
                "usage_period_days": [
                    "период использования (дней)",
                    "usage_period_days",
                ],
                "period_start_date": ["дата начала периода", "period_start_date"],
                "available_from": ["доступен с", "available_from"],
                "available_by": ["доступен до", "available_by"],
                "category_name": ["категория", "category_name"],
            },
            required_fields=["name", "coins_cost", "min_level_cost"],
            field_parsers={
                "adaptation_required": (parse_bool_field, False),
                "is_active": (parse_bool_field, True),
                "is_fixed_period": (parse_bool_field, False),
                "period_start_date": parse_date_field,
                "available_from": parse_date_field,
                "available_by": parse_date_field,
            },
        )

        valid_benefits_excel, parse_errors = parser.parse_excel(file_contents)

        valid_benefits = []
        service_errors = []

        for idx, benefit_excel_raw in enumerate(valid_benefits_excel):
            row_number = idx + 2

            benefit_excel = schemas.BenefitCreateExcel.model_validate(benefit_excel_raw)

            benefit_create, service_error = await self._process_benefit_row(
                benefit_excel,
                row_number,
            )

            if service_error:
                service_errors.append(service_error)
            else:
                valid_benefits.append(benefit_create)

        return valid_benefits, parse_errors + service_errors

    async def _process_benefit_row(
        self,
        benefit_excel: schemas.BenefitCreateExcel,
        row_number: int,
    ) -> tuple[Optional[schemas.BenefitCreate], Optional[dict[str, str]]]:
        """
        Processes a single benefit row from the Excel file.

        Args:
            benefit_excel (schemas.BenefitCreateExcel): The benefit data extracted from the Excel row.
            row_number (int): The Excel row number for error reporting.

        Returns:
            tuple[Optional[schemas.BenefitCreate], Optional[dict[str, Any]]]:
                A tuple containing the created `BenefitCreate` instance if successful,
                or an error dictionary if processing fails.
        """
        try:
            data = benefit_excel.model_dump()

            category_name = data.pop("category_name", None)

            if category_name:
                try:
                    category = await self._get_or_create_category(category_name)
                    data["category_id"] = category.id
                except Exception as e:
                    return None, {
                        "row": row_number,
                        "error": f"Error processing category '{category_name}': {str(e)}",
                    }

            benefit_create = schemas.BenefitCreate.model_validate(data)
            return benefit_create, None

        except Exception as e:
            return None, {
                "row": row_number,
                "error": f"Unexpected error: {str(e)}",
            }

    async def _get_or_create_category(self, category_name: Optional[str] = None):
        categories_service = CategoriesService()
        try:
            category = await categories_service.read_by_name(category_name)
        except service_exceptions.EntityNotFoundError:
            category_create = category_schemas.CategoryCreate(name=category_name)

            category = await categories_service.create(category_create)

        return category
