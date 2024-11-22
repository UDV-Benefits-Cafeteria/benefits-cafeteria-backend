import uuid
from typing import Optional, Union

from fastapi import UploadFile

import src.repositories.exceptions as repo_exceptions
import src.schemas.benefit as schemas
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.db.db import get_transaction_session
from src.logger import service_logger
from src.repositories.benefit_images import BenefitImagesRepository
from src.repositories.benefits import BenefitsRepository
from src.services.base import BaseService


class BenefitsService(
    BaseService[schemas.BenefitCreate, schemas.BenefitRead, schemas.BenefitUpdate]
):
    repo = BenefitsRepository()
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
