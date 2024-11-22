from typing import Annotated, Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status

import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.api.v1.dependencies import (
    BenefitsServiceDependency,
    get_active_user,
    get_hr_user,
)
from src.config import get_settings
from src.schemas import benefit as schemas
from src.schemas.benefit import SortOrderField
from src.utils.filter_parsers import range_filter_parser

router = APIRouter(prefix="/benefits", tags=["Benefits"])

settings = get_settings()


@router.get(
    "/",
    response_model=list[
        Union[schemas.BenefitReadShortPublic, schemas.BenefitReadShortPrivate]
    ],
    responses={
        200: {"description": "Benefits successfully retrieved"},
        400: {"description": "Failed to search benefits"},
    },
)
async def get_benefits(
    current_user: Annotated[user_schemas.UserRead, Depends(get_active_user)],
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
    created_at: Annotated[
        Optional[str],
        Query(
            description='Filter for created_at, for example: "gte:2024-01-01,lte:2024-12-31" '
        ),
    ] = None,
    categories: Annotated[Optional[list[int]], Query()] = None,
    sort_by: Annotated[Optional[schemas.BenefitSortFields], Query()] = None,
    sort_order: Annotated[SortOrderField, Query()] = SortOrderField.ASCENDING,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    filters: dict[str, Any] = {
        field: value
        for field, value in {
            "is_active": is_active,
            "adaptation_required": adaptation_required,
            "coins_cost": range_filter_parser(coins_cost, "coins_cost"),
            "real_currency_cost": range_filter_parser(
                real_currency_cost, "real_currency_cost"
            ),
            "min_level_cost": range_filter_parser(min_level_cost, "min_level_cost"),
            "created_at": range_filter_parser(created_at, "created_at"),
            "category_id": categories,
        }.items()
        if value is not None
    }

    try:
        benefits = await service.search_benefits(
            current_user=current_user,
            query=query,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except service_exceptions.EntityReadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to search benefits: {str(e)}",
        )

    return benefits


@router.get(
    "/{benefit_id}",
    response_model=Union[schemas.BenefitRead, schemas.BenefitReadPublic],
    responses={
        200: {"description": "Benefit successfully retrieved"},
        404: {"description": "Benefit not found"},
        400: {"description": "Failed to read benefit"},
    },
)
async def get_benefit(
    current_user: Annotated[user_schemas.UserRead, Depends(get_active_user)],
    benefit_id: int,
    service: BenefitsServiceDependency,
):
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
        benefit = await service.read_by_id(benefit_id, current_user)

    except service_exceptions.EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found"
        )
    except service_exceptions.EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read benefit"
        )

    return benefit


@router.post(
    "/",
    dependencies=[Depends(get_hr_user)],
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

    except service_exceptions.EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create benefit"
        )

    return created_benefit


@router.patch(
    "/{benefit_id}",
    dependencies=[Depends(get_hr_user)],
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

    except service_exceptions.EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found"
        )
    except service_exceptions.EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update benefit"
        )

    return updated_benefit


@router.delete(
    "/{benefit_id}",
    dependencies=[Depends(get_hr_user)],
    responses={
        200: {"description": True},
        400: {"description": "Failed to delete benefit"},
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

    except service_exceptions.EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found"
        )
    except service_exceptions.EntityDeleteError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete benefit"
        )

    return {"is_success": benefit_deleted}


@router.post(
    "/{benefit_id}/images",
    dependencies=[Depends(get_hr_user)],
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
    except service_exceptions.EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload benefit images",
        )
    except service_exceptions.EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read benefit",
        )
    except service_exceptions.EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to index benefit"
        )


@router.delete(
    "/{benefit_id}/images",
    dependencies=[Depends(get_hr_user)],
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
    except service_exceptions.EntityDeleteError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete benefit images",
        )
