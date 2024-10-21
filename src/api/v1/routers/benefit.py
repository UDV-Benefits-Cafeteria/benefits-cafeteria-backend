from typing import Annotated, Any, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, status

from src.api.v1.dependencies import BenefitsServiceDependency
from src.config import get_settings
from src.models.benefits import BenefitSortFields
from src.repositories.exceptions import EntityDeleteError
from src.schemas import benefit as schemas
from src.services.exceptions import (
    EntityCreateError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)
from src.utils.filter_parsers import benefit_range_filter_parser

router = APIRouter(prefix="/benefits", tags=["Benefits"])

settings = get_settings()


@router.get(
    "/",
    response_model=list[schemas.BenefitReadShort],
    responses={
        200: {"description": "Benefits successfully retrieved"},
        400: {"description": "Failed to search benefits"},
    },
)
async def get_benefits(
    service: BenefitsServiceDependency,
    query: Annotated[
        Optional[str], Query(description="Search query for benefit name")
    ] = None,
    is_active: Annotated[Optional[bool], Query()] = None,
    adaptation_required: Annotated[Optional[bool], Query()] = None,
    coins_cost: Annotated[
        Optional[str],
        Query(description='Filter for coins cost, for example: "gte:100,lte:500"'),
    ] = None,
    real_currency_cost: Annotated[
        Optional[str],
        Query(
            description='Filter for real_currency_cost, for example: "gte:100,lte:500"'
        ),
    ] = None,
    min_level_cost: Annotated[
        Optional[str],
        Query(description='Filter for min_level_cost, for example: "gte:1,lte:3"'),
    ] = None,
    available_from: Annotated[
        Optional[str],
        Query(
            description='Filter for available_from, for example: "gte:2024-01-01,lte:2024-12-31"'
        ),
    ] = None,
    available_by: Annotated[
        Optional[str],
        Query(
            description='Filter for available_by, for example: "gte:2024-01-01,lte:2024-12-31"'
        ),
    ] = None,
    sort_by: Annotated[Optional[BenefitSortFields], Query()] = None,
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    try:
        filters: dict[str, Any] = {}
        if is_active is not None:
            filters["is_active"] = is_active
        if adaptation_required is not None:
            filters["adaptation_required"] = adaptation_required

        coins_cost_filter = benefit_range_filter_parser(coins_cost, "coins_cost")
        if coins_cost_filter:
            filters["coins_cost"] = coins_cost_filter

        real_currency_cost_filter = benefit_range_filter_parser(
            real_currency_cost, "real_currency_cost"
        )
        if real_currency_cost_filter:
            filters["real_currency_cost"] = real_currency_cost_filter

        min_level_cost_filter = benefit_range_filter_parser(
            min_level_cost, "min_level_cost"
        )
        if min_level_cost_filter:
            filters["min_level_cost"] = min_level_cost_filter

        available_from_filter = benefit_range_filter_parser(
            available_from, "available_from"
        )
        if available_from_filter:
            filters["available_from"] = available_from_filter

        available_by_filter = benefit_range_filter_parser(available_by, "available_by")
        if available_by_filter:
            filters["available_by"] = available_by_filter

        benefits = await service.search_benefits(
            query=query,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        return benefits
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except EntityReadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to search benefits: {str(e)}",
        )


@router.get(
    "/{benefit_id}",
    response_model=schemas.BenefitRead,
    responses={
        200: {"description": "Benefit successfully retrieved"},
        404: {"description": "Benefit not found"},
        400: {"description": "Failed to read benefit"},
    },
)
async def get_benefit(benefit_id: int, service: BenefitsServiceDependency):
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
    response_model=schemas.BenefitRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Benefit successfully created"},
        400: {"description": "Failed to create benefit"},
    },
)
async def create_benefit(
    benefit: schemas.BenefitCreate, service: BenefitsServiceDependency
):
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
    response_model=schemas.BenefitRead,
    responses={
        200: {"description": "Benefit successfully updated"},
        404: {"description": "Benefit not found"},
        400: {"description": "Failed to update benefit"},
    },
)
async def update_benefit(
    benefit_id: int,
    benefit_update: schemas.BenefitUpdate,
    service: BenefitsServiceDependency,
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
async def delete_benefit(benefit_id: int, service: BenefitsServiceDependency):
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
        return {"is_success": benefit_deleted}
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found"
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
    benefit_id: int, images: list[UploadFile], service: BenefitsServiceDependency
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload benefit images",
        )


@router.delete(
    "/{benefit_id}/images",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Images successfully deleted"},
        400: {"description": "Failed to delete benefit images"},
    },
)
async def remove_images(images: list[int], service: BenefitsServiceDependency):
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete benefit images",
        )
