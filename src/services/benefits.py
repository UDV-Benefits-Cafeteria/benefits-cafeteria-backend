from typing import Optional

from fastapi import UploadFile

import src.repositories.exceptions as repo_exceptions
import src.schemas.benefit as schemas
import src.services.exceptions as service_exceptions
from src.config import logger
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
        query: str,
        filters: Optional[dict] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0,
    ) -> list[schemas.BenefitReadShort]:
        try:
            search_results = await self.repo.search_benefits(
                query=query,
                filters=filters,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset,
            )
            benefits = [
                schemas.BenefitReadShort.model_validate(data) for data in search_results
            ]
            return benefits
        except service_exceptions.EntityReadError as e:
            logger.error(f"Error searching benefits: {e}")
            raise service_exceptions.EntityReadError("Benefit", "", str(e))

    @staticmethod
    async def add_images(images: list[UploadFile], benefit_id: int):
        """
        Add images to a specific benefit.

        Args:
        - images (list[UploadFile]): A list of image files to associate with the benefit.
        - benefit_id (int): The ID of the benefit to which the images will be linked.

        Raises:
        - service_exceptions.EntityCreateError: If an error occurs while creating one of the images in the repository.
        """
        for image_data in images:
            image = {"benefit_id": benefit_id, "image_url": image_data}
            try:
                await BenefitImagesRepository().create(data=image)
            except repo_exceptions.EntityCreateError as e:
                logger.error(f"Failed to create image {image_data.filename}: {str(e)}")
                raise service_exceptions.EntityCreateError(image_data.filename, str(e))

    @staticmethod
    async def remove_images(images: list[int]):
        """
        Remove images by their IDs.

        Args:
        - images (list[int]): A list of image IDs to delete.

        Raises:
        - service_exceptions.EntityDeletionError: If an error occurs while deleting one of the images.

        Returns:
        - None: Indicates successful deletion of images.
        """
        for image_id in images:
            try:
                await BenefitImagesRepository().delete_by_id(image_id)
            except repo_exceptions.EntityDeleteError as e:
                logger.error(f"Failed to delete image {image_id}: {str(e)}")
                raise service_exceptions.EntityDeletionError(
                    str(image_id), image_id, str(e)
                )
