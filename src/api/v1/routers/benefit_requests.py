from typing import Annotated, BinaryIO, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.params import Query
from fastapi.responses import StreamingResponse

import src.schemas.request as schemas
import src.schemas.user as user_schemas
from src.api.v1.dependencies import (
    BenefitRequestsServiceDependency,
    get_active_user,
    get_hr_user,
)
from src.schemas.benefit import SortOrderField
from src.schemas.request import BenefitRequestSortFields
from src.services.exceptions import (
    EntityCreateError,
    EntityDeleteError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)
from src.services.users import UsersService
from src.utils.email_sender.benefit_requests import (
    send_users_benefit_request_created_email,
    send_users_benefit_request_updated_email,
)

router = APIRouter(prefix="/benefit-requests", tags=["Requests"])


@router.post(
    "/",
    response_model=schemas.BenefitRequestRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Benefit request created successfully"},
        400: {"description": "Failed to create benefit request"},
        404: {"description": "Benefit or user not found"},
    },
)
async def create_benefit_request(
    benefit_request: schemas.BenefitRequestCreate,
    current_user: Annotated[user_schemas.UserRead, Depends(get_active_user)],
    service: BenefitRequestsServiceDependency,
    background_tasks: BackgroundTasks,
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
        created_benefit_request = await service.create(
            create_schema=benefit_request, current_user=current_user
        )

    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create benefit request. Check the benefit coins cost and minimal level required",
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount cannot be negative"
        )
    except (EntityNotFoundError, EntityReadError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit or user not found"
        )

    await send_users_benefit_request_created_email(
        current_user.email,
        current_user.firstname,
        created_benefit_request.benefit.id,
        created_benefit_request.benefit.name,
        created_benefit_request.benefit.coins_cost,
        created_benefit_request.benefit.images[0].image_url
        if created_benefit_request.benefit.images
        else "https://digital-portfolio.hb.ru-msk.vkcloud-storage.ru/Image.png",
        background_tasks,
    )

    return created_benefit_request


@router.get("/export")
async def export_benefit_requests(
    current_user: Annotated[schemas.UserRead, Depends(get_hr_user)],
    service: BenefitRequestsServiceDependency,
    legal_entity_ids: Annotated[Optional[list[int]], Query()] = None,
    status: Annotated[Optional[schemas.BenefitStatus], Query()] = None,
):
    try:
        excel_file: BinaryIO = await service.export_benefit_requests(
            current_user=current_user,
            legal_entities=legal_entity_ids,
            status=status,
        )
    except EntityReadError:
        raise HTTPException(
            status_code=400,
            detail="Failed to export benefit requests. Probably no requests match the specified filters.",
        )

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=benefit_requests.xlsx"},
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
    current_user: Annotated[user_schemas.UserRead, Depends(get_hr_user)],
    user_id: int,
    service: BenefitRequestsServiceDependency,
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
        user = await UsersService().read_by_id(user_id)
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if current_user.role != user_schemas.UserRole.ADMIN:
        if user.legal_entity_id != current_user.legal_entity_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied. Check legal entity.",
            )

    try:
        benefit_requests = await service.read_by_user_id(user_id)
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read benefit requests",
        )

    return benefit_requests


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
async def get_benefit_requests_of_current_user(
    current_user: Annotated[user_schemas.UserRead, Depends(get_active_user)],
    service: BenefitRequestsServiceDependency,
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

    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read benefit requests",
        )

    return benefit_requests


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
    current_user: Annotated[user_schemas.UserRead, Depends(get_hr_user)],
    request_id: int,
    service: BenefitRequestsServiceDependency,
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
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit request not found"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read benefit request",
        )
    if current_user.role != user_schemas.UserRole.ADMIN:
        user = await UsersService().read_by_id(benefit_request.user_id)
        if user.id != current_user.id:
            if current_user.role != user_schemas.UserRole.HR:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied. Your role cannot get other users' requests.",
                )
            if user.legal_entity_id != current_user.legal_entity_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied. Check legal entity.",
                )

    return benefit_request


@router.get(
    "/",
    response_model=list[schemas.BenefitRequestRead],
    responses={
        200: {"description": "List of benefit requests retrieved successfully"},
        400: {"description": "Failed to read benefit requests"},
    },
)
async def get_benefit_requests(
    service: BenefitRequestsServiceDependency,
    current_user: Annotated[user_schemas.UserRead, Depends(get_hr_user)],
    legal_entities: Annotated[Optional[list[int]], Query()] = None,
    user_id: Annotated[Optional[int], Query()] = None,
    performer_id: Annotated[Optional[int], Query()] = None,
    status: Annotated[Optional[schemas.BenefitStatus], Query()] = None,
    sort_by: Annotated[Optional[BenefitRequestSortFields], Query()] = None,
    sort_order: Annotated[SortOrderField, Query()] = SortOrderField.ASCENDING,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    """
    Get a list of all benefit requests with optional filtering and sorting.

    - **status**: Filter benefit requests by status.
    - **sort_by**: Field to sort the benefit requests by.
    - **sort_order**: Order of sorting ('asc' or 'desc').
    - **page**: The page number to retrieve (default is 1).
    - **limit**: The number of items per page (default is 10).

    Raises:
    - **HTTPException**:
        - 400: If reading the benefit requests fails.

    Returns:
    - **list[BenefitRequestRead]**: The list of benefit requests.
    """
    try:
        benefit_requests = await service.read_all(
            current_user=current_user,
            status=status,
            legal_entities=legal_entities,
            user_id=user_id,
            performer_id=performer_id,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )

    except EntityReadError:
        raise HTTPException(
            status_code=400,
            detail="Failed to read benefit requests.",
        )

    return benefit_requests


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
    service: BenefitRequestsServiceDependency,
    background_tasks: BackgroundTasks,
    current_user: Annotated[user_schemas.UserRead, Depends(get_active_user)],
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
            entity_id=request_id,
            update_schema=benefit_request_update,
            current_user=current_user,
        )

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit request not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update benefit request",
        )
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update benefit request. Check the benefit coins cost and minimal level required",
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit or user not found"
        )

    await send_users_benefit_request_updated_email(
        current_user.email,
        current_user.firstname,
        updated_benefit_request.status,
        updated_benefit_request.benefit.id,
        updated_benefit_request.benefit.name,
        updated_benefit_request.benefit.coins_cost,
        updated_benefit_request.benefit.images[0].image_url
        if updated_benefit_request.benefit.images
        else "https://digital-portfolio.hb.ru-msk.vkcloud-storage.ru/Image.png",
        background_tasks,
    )

    return updated_benefit_request


@router.delete(
    "/{request_id}",
    dependencies=[Depends(get_active_user)],
    responses={
        200: {"description": "Benefit request deleted successfully"},
        400: {"description": "Failed to delete benefit request"},
        404: {"description": "Benefit request not found"},
    },
)
async def delete_benefit_request(
    request_id: int, service: BenefitRequestsServiceDependency
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

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Benefit request not found"
        )
    except EntityDeleteError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete benefit request",
        )

    return {"is_success": benefit_request_deleted}
