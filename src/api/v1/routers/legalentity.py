from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query

from src.api.v1.dependencies import (
    LegalEntitiesServiceDependency,
    get_active_user,
    get_hr_user,
)
from src.schemas import legalentity as schemas
from src.services.exceptions import (
    EntityCreateError,
    EntityDeletionError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)

router = APIRouter(prefix="/legal-entities", tags=["Legal Entities"])


@router.get(
    "/{entity_id}",
    dependencies=[Depends(get_active_user)],
    response_model=schemas.LegalEntityRead,
    responses={
        200: {"description": "Legal entity retrieved successfully"},
        404: {"description": "Legal entity not found"},
        400: {"description": "Failed to read legal entity"},
    },
)
async def get_legal_entity(entity_id: int, service: LegalEntitiesServiceDependency):
    """
    Get a legal entity by ID.

    - **entity_id**: The ID of the legal entity to retrieve.

    Raises:
    - **HTTPException**:
        - 404: If the legal entity is not found.
        - 400: If reading the legal entity fails.

    Returns:
    - **LegalEntityRead**: The legal entity data.
    """
    try:
        legal_entity = await service.read_by_id(entity_id)
        return legal_entity
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Legal entity not found"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read legal entity",
        )


@router.post(
    "/",
    dependencies=[Depends(get_hr_user)],
    response_model=schemas.LegalEntityRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Legal entity created successfully"},
        400: {"description": "Failed to create legal entity"},
    },
)
async def create_legal_entity(
    legal_entity: schemas.LegalEntityCreate, service: LegalEntitiesServiceDependency
):
    """
    Create a new legal entity.

    - **legal_entity**: The data for the new legal entity.

    Raises:
    - **HTTPException**:
        - 400: If creating the legal entity fails.

    Returns:
    - **LegalEntityRead**: The created legal entity data.
    """
    try:
        created_legal_entity = await service.create(legal_entity)
        return created_legal_entity
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create legal entity",
        )


@router.patch(
    "/{entity_id}",
    dependencies=[Depends(get_hr_user)],
    response_model=schemas.LegalEntityRead,
    responses={
        200: {"description": "Legal entity updated successfully"},
        404: {"description": "Legal entity not found"},
        400: {"description": "Failed to update legal entity"},
    },
)
async def update_legal_entity(
    entity_id: int,
    legal_entity_update: schemas.LegalEntityUpdate,
    service: LegalEntitiesServiceDependency,
):
    """
    Update an existing legal entity by ID.

    - **entity_id**: The ID of the legal entity to update.
    - **legal_entity_update**: The data to update the legal entity.

    Raises:
    - **HTTPException**:
        - 404: If the legal entity is not found.
        - 400: If updating the legal entity fails.

    Returns:
    - **LegalEntityRead**: The updated legal entity data.
    """
    try:
        updated_legal_entity = await service.update_by_id(
            entity_id, legal_entity_update
        )
        return updated_legal_entity
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Legal entity not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update legal entity",
        )


@router.delete(
    "/{entity_id}",
    dependencies=[Depends(get_hr_user)],
    responses={
        200: {"description": "Legal entity deleted successfully"},
        400: {"description": "Failed to delete legal entity"},
        404: {"description": "Legal entity not found"},
    },
)
async def delete_legal_entity(entity_id: int, service: LegalEntitiesServiceDependency):
    """
    Delete an existing legal entity by ID.

    - **entity_id**: The ID of the legal entity to delete.

    Raises:
    - **HTTPException**:
        - 404: If the legal entity is not found.

    Returns:
    - **dict**: A confirmation of deletion (`is_success`: bool).
    """
    try:
        legal_entity_deleted = await service.delete_by_id(entity_id)
        return {"is_success": legal_entity_deleted}
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Legal entity not found"
        )
    except EntityDeletionError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete legal entity",
        )


@router.get(
    "/",
    dependencies=[Depends(get_active_user)],
    response_model=list[schemas.LegalEntityRead],
    responses={
        200: {"description": "List of legal entities retrieved successfully"},
        400: {"description": "Failed to retrieve legal entities"},
    },
)
async def get_legal_entities(
    service: LegalEntitiesServiceDependency,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    """
    Get a list of all legal entities.

    - **page**: The page number to retrieve (default is 1).
    - **limit**: The number of items per page (default is 10).

    Raises:
    - **HTTPException**:
        - 400: If retrieving legal entities fails.

    Returns:
    - **list[LegalEntityRead]**: A list of legal entity data.
    """
    try:
        legal_entities = await service.read_all(page, limit)
        return legal_entities
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read legal entities",
        )
