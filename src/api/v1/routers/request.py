from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import BenefitRequestServiceDependency, get_active_user
from src.schemas import request as schemas
from src.services.exceptions import (
    EntityCreateError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)

router = APIRouter(prefix="/benefit-requests", tags=["Requests"])


@router.post(
    "/",
    response_model=schemas.BenefitRequestCreate,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Benefit request created successfully"},
        400: {"description": "Failed to create benefit request"},
    },
)
async def create_benefit_request(
    benefit_request: schemas.BenefitRequestCreate,
    service: BenefitRequestServiceDependency,
):
    """
    Create a new benefit request.

    - **benefit_request**: The data for the new benefit request.

    Raises:
    - **HTTPException**:
        - 400: If creating the benefit request fails.

    Returns:
    - **BenefitRequestCreate**: The created benefit request data.
    """
    try:
        created_benefit_request = await service.create(benefit_request)
        return created_benefit_request
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create benefit request",
        )


@router.get(
    "/user/{user_id}",
    response_model=list[schemas.BenefitRequestRead],
    responses={
        200: {"description": "Benefit requests retrieved successfully"},
        400: {"description": "Failed to read benefit requests"},
    },
)
async def get_benefit_requests_by_user(
    user_id: int, service: BenefitRequestServiceDependency
):
    """
    Get all benefit requests for a specific user by user ID.

    - **user_id**: The ID of the user whose benefit requests are being retrieved.

    Raises:
    - **HTTPException**:
        - 400: If reading the benefit requests fails.

    Returns:
    - **list[BenefitRequestRead]**: The list of benefit requests for the user.
    """
    try:
        benefit_requests = await service.read_by_user_id(user_id)
        return benefit_requests
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read benefit requests",
        )


@router.get(
    "/current-user",
    response_model=list[schemas.BenefitRequestRead],
    responses={
        200: {
            "description": "Benefit requests for current user retrieved successfully"
        },
        400: {"description": "Failed to read benefit requests for current user"},
    },
)
async def get_benefit_requests_by_current_user(
    current_user: Annotated[schemas.UserRead, Depends(get_active_user)],
    service: BenefitRequestServiceDependency,
):
    """
    Get benefit requests for the current authenticated user.

    - **current_user**: The currently authenticated user.

    Raises:
    - **HTTPException**:
        - 400: If reading the benefit requests fails.

    Returns:
    - **list[BenefitRequestRead]**: The list of benefit requests for the current user.
    """
    try:
        benefit_requests = await service.read_by_user_id(current_user.id)
        return benefit_requests
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read benefit requests",
        )


@router.get(
    "/{request_id}",
    response_model=schemas.BenefitRequestRead,
    responses={
        200: {"description": "Benefit request retrieved successfully"},
        404: {"description": "Benefit request not found"},
        400: {"description": "Failed to read benefit request"},
    },
)
async def get_benefit_request(
    request_id: int, service: BenefitRequestServiceDependency
):
    """
    Get a benefit request by ID.

    - **request_id**: The ID of the benefit request to retrieve.

    Raises:
    - **HTTPException**:
        - 404: If the benefit request is not found.
        - 400: If reading the benefit request fails.

    Returns:
    - **BenefitRequestRead**: The benefit request data.
    """
    try:
        benefit_request = await service.read_by_id(request_id)
        return benefit_request
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit request not found"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read benefit request",
        )


@router.get(
    "/",
    response_model=list[schemas.BenefitRequestRead],
    responses={
        200: {"description": "List of benefit requests retrieved successfully"},
        400: {"description": "Failed to read benefit requests"},
    },
)
async def get_benefit_requests(service: BenefitRequestServiceDependency):
    """
    Get a list of all benefit requests.

    Raises:
    - **HTTPException**:
        - 400: If reading the benefit requests fails.

    Returns:
    - **list[BenefitRequestRead]**: The list of benefit requests.
    """
    try:
        benefit_requests = await service.read_all()
        return benefit_requests
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read benefit requests",
        )


@router.patch(
    "/{request_id}",
    response_model=schemas.BenefitRequestUpdate,
    responses={
        200: {"description": "Benefit request updated successfully"},
        404: {"description": "Benefit request not found"},
        400: {"description": "Failed to update benefit request"},
    },
)
async def update_benefit_request(
    request_id: int,
    benefit_request_update: schemas.BenefitRequestUpdate,
    service: BenefitRequestServiceDependency,
):
    """
    Update a benefit request by ID.

    - **request_id**: The ID of the benefit request to update.
    - **benefit_request_update**: The updated data for the benefit request.

    Raises:
    - **HTTPException**:
        - 404: If the benefit request is not found.
        - 400: If updating the benefit request fails.

    Returns:
    - **BenefitRequestUpdate**: The updated benefit request data.
    """
    try:
        updated_benefit_request = await service.update_by_id(
            request_id, benefit_request_update
        )
        return updated_benefit_request
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit request not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update benefit request",
        )


@router.delete(
    "/{request_id}",
    responses={
        200: {"description": "Benefit request deleted successfully"},
        404: {"description": "Benefit request not found"},
    },
)
async def delete_benefit_request(
    request_id: int, service: BenefitRequestServiceDependency
):
    """
    Delete a benefit request by ID.

    - **request_id**: The ID of the benefit request to delete.

    Raises:
    - **HTTPException**:
        - 404: If the benefit request is not found.

    Returns:
    - **dict**: A confirmation of deletion (`is_success`: bool).
    """
    try:
        benefit_request_deleted = await service.delete_by_id(request_id)
        return {"is_success": benefit_request_deleted}
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit request not found"
        )
