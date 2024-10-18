from fastapi import APIRouter, HTTPException, UploadFile, status

from src.api.v1.dependencies import BenefitServiceDependency
from src.repositories.exceptions import EntityDeleteError
from src.schemas.benefit import BenefitCreate, BenefitRead, BenefitUpdate
from src.services.exceptions import (
    EntityCreateError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)

router = APIRouter(prefix="/benefits", tags=["Benefits"])


@router.get(
    "/{benefit_id}",
    response_model=BenefitRead,
    responses={
        200: {"description": "Benefit successfully retrieved"},
        404: {"description": "Benefit not found"},
        400: {"description": "Failed to read benefit"},
    },
)
async def get_benefit(benefit_id: int, service: BenefitServiceDependency):
    """
    Retrieve a benefit by its ID.

    Args:
    - **benefit_id (int)**: The ID of the benefit to retrieve.
    - **service (BenefitServiceDependency)**: The service handling the logic.

    Returns:
    - **BenefitRead**: The requested benefit.

    Raises:
    - **HTTPException**:
        - 404: If the benefit is not found.
        - 400: If there is an error reading the benefit.
    """
    try:
        benefit = await service.read_by_id(benefit_id)
        return benefit
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read benefit"
        )


@router.post(
    "/",
    response_model=BenefitRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Benefit successfully created"},
        400: {"description": "Failed to create benefit"},
    },
)
async def create_benefit(benefit: BenefitCreate, service: BenefitServiceDependency):
    """
    Create a new benefit.

    Args:
    - **benefit (BenefitCreate)**: The data for the benefit to create.
    - **service (BenefitServiceDependency)**: The service handling the logic.

    Returns:
    - **BenefitRead**: The created benefit.

    Raises:
    - **HTTPException**:
        - 400: If there is an error creating the benefit.
    """
    try:
        created_benefit = await service.create(benefit)
        return created_benefit
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create benefit"
        )


@router.patch(
    "/{benefit_id}",
    response_model=BenefitRead,
    responses={
        200: {"description": "Benefit successfully updated"},
        404: {"description": "Benefit not found"},
        400: {"description": "Failed to update benefit"},
    },
)
async def update_benefit(
    benefit_id: int, benefit_update: BenefitUpdate, service: BenefitServiceDependency
):
    """
    Update a benefit by its ID.

    Args:
    - **benefit_id (int)**: The ID of the benefit to update.
    - **benefit_update (BenefitUpdate)**: The updated benefit data.
    - **service (BenefitServiceDependency)**: The service handling the logic.

    Returns:
    - **BenefitRead**: The updated benefit.

    Raises:
    - **HTTPException**:
        - 404: If the benefit is not found.
        - 400: If there is an error updating the benefit.
    """
    try:
        updated_benefit = await service.update_by_id(benefit_id, benefit_update)
        return updated_benefit
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update benefit"
        )


@router.delete(
    "/{benefit_id}",
    responses={
        200: {"description": True},
        404: {"description": "Benefit not found"},
    },
)
async def delete_benefit(benefit_id: int, service: BenefitServiceDependency):
    """
    Delete a benefit by its ID.

    Args:
    - **benefit_id (int)**: The ID of the benefit to delete.
    - **service (BenefitServiceDependency)**: The service handling the logic.

    Returns:
    - **dict**: Confirmation of deletion.

    Raises:
    - **HTTPException**:
        - 404: If the benefit is not found.
    """
    try:
        benefit_deleted = await service.delete_by_id(benefit_id)
        return {"success": benefit_deleted}
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found"
        )


@router.get(
    "/",
    response_model=list[BenefitRead],
    responses={
        200: {"description": "Benefits successfully retrieved"},
        400: {"description": "Failed to retrieve benefits"},
    },
)
async def get_benefits(service: BenefitServiceDependency):
    """
    Retrieve all benefits.

    Args:
    - **service (BenefitServiceDependency)**: The service handling the logic.

    Returns:
    - **list[BenefitRead]**: List of all benefits.

    Raises:
    - **HTTPException**:
        - 400: If there is an error retrieving the benefits.
    """
    try:
        benefits = await service.read_all()
        return benefits
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read benefits"
        )


@router.post(
    "/{benefit_id}/images",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Images successfully uploaded"},
        400: {"description": "Failed to upload benefit images"},
    },
)
async def upload_images(
    benefit_id: int, images: list[UploadFile], service: BenefitServiceDependency
):
    """
    Upload images for a specific benefit.

    Args:
    - **benefit_id (int)**: The ID of the benefit to upload images for.
    - **images (list[UploadFile])**: A list of image files to upload.
    - **service (BenefitServiceDependency)**: The service handling the logic.

    Returns:
    - **None**: Indicates successful upload.

    Raises:
    - **HTTPException**:
        - 400: If there is an error uploading the images.
    """
    try:
        await service.add_images(images, benefit_id)
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload benefit images"
        )


@router.delete(
    "/{benefit_id}/images",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Images successfully deleted"},
        400: {"description": "Failed to delete benefit images"},
    },
)
async def remove_images(
    images: list[int], service: BenefitServiceDependency
):
    """
    Remove images for a specific benefit.

    Args:
    - **images (list[int])**: A list of image IDs to remove.
    - **service (BenefitServiceDependency)**: The service handling the logic.

    Returns:
    - **None**: Indicates successful deletion of images.

    Raises:
    - **HTTPException**:
        - 400: If there is an error deleting the images.
    """
    try:
        await service.remove_images(images)
    except EntityDeleteError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete benefit images"
        )
