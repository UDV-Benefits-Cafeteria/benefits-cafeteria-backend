from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.params import Query

from src.api.v1.dependencies import (
    LegalEntitiesServiceDependency,
    get_active_user,
    get_hr_user,
)
from src.schemas import legalentity as schemas
from src.services.exceptions import (
    EntityCreateError,
    EntityDeleteError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)

router = APIRouter(prefix="/legal-entities", tags=["Legal Entities"])


@router.get(
    "/{entity_id}",
    dependencies=[Depends(get_active_user)],
    response_model=schemas.LegalEntityReadWithCounts,
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
    - **LegalEntityReadWithCounts**: The legal entity data including employee and staff counts.
    """
    try:
        legal_entity = await service.read_by_id_with_counts(entity_id)

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Legal entity not found"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read legal entity",
        )

    return legal_entity


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

    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create legal entity",
        )

    return created_legal_entity


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

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Legal entity not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update legal entity",
        )

    return updated_legal_entity


@router.post(
    "/upload",
    response_model=schemas.LegalEntityValidationResponse,
    responses={
        200: {"description": "Legal entities validated successfully"},
        400: {"description": "Invalid file type or error reading Excel file"},
    },
    dependencies=[Depends(get_hr_user)],
)
async def upload_legal_entities(
    service: LegalEntitiesServiceDependency,
    file: UploadFile = File(...),
):
    """
    Upload legal entities from an Excel file for validation.

    - **file**: The Excel file containing legal entity data.

    Returns:
    - **LegalEntityValidationResponse**: Information about valid legal entities and errors.
    """
    if (
        file.content_type
        != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an Excel file.",
        )

    try:
        contents = await file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error reading file",
        )

    try:
        valid_entities, errors = await service.parse_legal_entities_from_excel(contents)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error while parsing legal entities. Column for 'name' might be missing",
        )

    return schemas.LegalEntityValidationResponse(
        valid_entities=valid_entities, errors=errors
    )


@router.post(
    "/bulk_create",
    response_model=schemas.LegalEntityUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Legal entities created successfully"},
        400: {"description": "Failed to create legal entities"},
    },
    dependencies=[Depends(get_hr_user)],
)
async def bulk_create_legal_entities(
    entities_data: list[schemas.LegalEntityCreate],
    service: LegalEntitiesServiceDependency,
):
    """
    Create multiple legal entities from the provided list.

    - **entities_data**: The list of legal entity data to create.

    Returns:
    - **LegalEntityUploadResponse**: Information about created legal entities and errors.
    """
    created_entities = []
    errors = []

    for idx, entity_data in enumerate(entities_data, start=1):
        try:
            entity_data = schemas.LegalEntityCreate.model_validate(entity_data)
            created_entity = await service.create(entity_data)
            created_entities.append(created_entity)
        except EntityCreateError as e:
            errors.append({"row": idx, "error": f"Creation Error: {str(e)}"})
        except Exception as e:
            errors.append({"row": idx, "error": f"Unexpected Error: {str(e)}"})

    return schemas.LegalEntityUploadResponse(
        created_entities=created_entities, errors=errors
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

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Legal entity not found"
        )
    except EntityDeleteError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete legal entity",
        )

    return {"is_success": legal_entity_deleted}


@router.get(
    "/",
    dependencies=[Depends(get_active_user)],
    response_model=list[schemas.LegalEntityReadWithCounts],
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
    - **list[LegalEntityReadWithCounts]**: A list of legal entity data including counts.
    """
    try:
        legal_entities = await service.read_all_with_counts(page, limit)

    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read legal entities",
        )

    return legal_entities
