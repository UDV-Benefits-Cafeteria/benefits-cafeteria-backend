from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query

from src.api.v1.dependencies import (
    CategoriesServiceDependency,
    get_active_user,
    get_hr_user,
)
from src.schemas import category as schemas
from src.services.exceptions import (
    EntityCreateError,
    EntityDeletionError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "/{category_id}",
    dependencies=[Depends(get_active_user)],
    response_model=schemas.CategoryRead,
    responses={
        200: {"description": "Category retrieved successfully"},
        404: {"description": "Category not found"},
        400: {"description": "Failed to read category"},
    },
)
async def get_category(category_id: int, service: CategoriesServiceDependency):
    """
    Get a category by ID.

    - **category_id**: The ID of the category to retrieve.

    Raises:
    - **HTTPException**:
        - 404: If the category is not found.
        - 400: If reading the category fails.

    Returns:
    - **CategoryRead**: The category data.
    """
    try:
        category = await service.read_by_id(category_id)
        return category
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read category"
        )


@router.post(
    "/",
    dependencies=[Depends(get_hr_user)],
    response_model=schemas.CategoryRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Category created successfully"},
        400: {"description": "Failed to create category"},
    },
)
async def create_category(
    category: schemas.CategoryCreate, service: CategoriesServiceDependency
):
    """
    Create a new category.

    - **category**: The data for the new category.

    Raises:
    - **HTTPException**:
        - 400: If creating the category fails.

    Returns:
    - **CategoryRead**: The created category data.
    """
    try:
        created_category = await service.create(category)
        return created_category
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create category"
        )


@router.patch(
    "/{category_id}",
    dependencies=[Depends(get_hr_user)],
    response_model=schemas.CategoryRead,
    responses={
        200: {"description": "Category updated successfully"},
        404: {"description": "Category not found"},
        400: {"description": "Failed to update category"},
    },
)
async def update_category(
    category_id: int,
    category_update: schemas.CategoryUpdate,
    service: CategoriesServiceDependency,
):
    """
    Update a category by ID.

    - **category_id**: The ID of the category to update.
    - **category_update**: The updated data for the category.

    Raises:
    - **HTTPException**:
        - 404: If the category is not found.
        - 400: If updating the category fails.

    Returns:
    - **CategoryRead**: The updated category data.
    """
    try:
        updated_category = await service.update_by_id(category_id, category_update)
        return updated_category
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update category"
        )


@router.delete(
    "/{category_id}",
    dependencies=[Depends(get_hr_user)],
    responses={
        200: {"description": "Category deleted successfully"},
        400: {"description": "Failed to delete category"},
        404: {"description": "Category not found"},
    },
)
async def delete_category(category_id: int, service: CategoriesServiceDependency):
    """
    Delete a category by ID.

    - **category_id**: The ID of the category to delete.

    Raises:
    - **HTTPException**:
        - 404: If the category is not found.

    Returns:
    - **dict**: A confirmation of deletion (`is_success`: bool).
    """
    try:
        category_deleted = await service.delete_by_id(category_id)
        return {"is_success": category_deleted}
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    except EntityDeletionError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete category"
        )


@router.get(
    "/",
    dependencies=[Depends(get_active_user)],
    response_model=list[schemas.CategoryRead],
    responses={
        200: {"description": "List of categories retrieved successfully"},
        400: {"description": "Failed to read categories"},
    },
)
async def get_categories(
    service: CategoriesServiceDependency,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    """
    Get a list of all categories with pagination.

    - **page**: The page number to retrieve (default is 1).
    - **limit**: The number of items per page (default is 10).

    Raises:
    - **HTTPException**:
        - 400: If reading the categories fails.

    Returns:
    - **list[CategoryRead]**: The list of categories.
    """
    try:
        categories = await service.read_all(page=page, limit=limit)
        return categories
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read categories",
        )
