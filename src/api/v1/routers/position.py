from fastapi import APIRouter, HTTPException, status
from fastapi.params import Query

from src.api.v1.dependencies import PositionsServiceDependency
from src.schemas import position as schemas
from src.services.exceptions import (
    EntityCreateError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)

router = APIRouter(prefix="/positions", tags=["Positions"])


@router.get(
    "/{position_id}",
    response_model=schemas.PositionRead,
    responses={
        200: {"description": "Position retrieved successfully"},
        404: {"description": "Position not found"},
        400: {"description": "Failed to read position"},
    },
)
async def get_position(position_id: int, service: PositionsServiceDependency):
    """
    Get a position by ID.

    - **position_id**: The ID of the position to retrieve.

    Raises:
    - **HTTPException**:
        - 404: If the position is not found.
        - 400: If reading the position fails.

    Returns:
    - **PositionRead**: The position data.
    """
    try:
        position = await service.read_by_id(position_id)
        return position
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read position"
        )


@router.post(
    "/",
    response_model=schemas.PositionRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Position created successfully"},
        400: {"description": "Failed to create position"},
    },
)
async def create_position(
    position: schemas.PositionCreate, service: PositionsServiceDependency
):
    """
    Create a new position.

    - **position**: The data for the new position.

    Raises:
    - **HTTPException**:
        - 400: If creating the position fails.

    Returns:
    - **PositionRead**: The created position data.
    """
    try:
        created_position = await service.create(position)
        return created_position
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create position"
        )


@router.patch(
    "/{position_id}",
    response_model=schemas.PositionRead,
    responses={
        200: {"description": "Position updated successfully"},
        404: {"description": "Position not found"},
        400: {"description": "Failed to update position"},
    },
)
async def update_position(
    position_id: int,
    position_update: schemas.PositionUpdate,
    service: PositionsServiceDependency,
):
    """
    Update an existing position by ID.

    - **position_id**: The ID of the position to update.
    - **position_update**: The data to update the position.

    Raises:
    - **HTTPException**:
        - 404: If the position is not found.
        - 400: If updating the position fails.

    Returns:
    - **PositionRead**: The updated position data.
    """
    try:
        updated_position = await service.update_by_id(position_id, position_update)
        return updated_position
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update position"
        )


@router.delete(
    "/{position_id}",
    responses={
        200: {"description": "Position deleted successfully"},
        404: {"description": "Position not found"},
    },
)
async def delete_position(position_id: int, service: PositionsServiceDependency):
    """
    Delete an existing position by ID.

    - **position_id**: The ID of the position to delete.

    Raises:
    - **HTTPException**:
        - 404: If the position is not found.

    Returns:
    - **dict**: A confirmation of deletion (`is_success`: bool).
    """
    try:
        position_deleted = await service.delete_by_id(position_id)
        return {"is_success": position_deleted}
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
        )


@router.get(
    "/",
    response_model=list[schemas.PositionRead],
    responses={
        200: {"description": "List of positions retrieved successfully"},
        400: {"description": "Failed to retrieve positions"},
    },
)
async def get_positions(
    service: PositionsServiceDependency,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1)
):
    """
    Get a list of all positions.

    - **page**: The page number to retrieve (default is 1).
    - **limit**: The number of items per page (default is 10).

    Raises:
    - **HTTPException**:
        - 400: If retrieving positions fails.

    Returns:
    - **list[PositionRead]**: A list of position data.
    """
    try:
        positions = await service.read_all(page, limit)
        return positions
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read positions",
        )
