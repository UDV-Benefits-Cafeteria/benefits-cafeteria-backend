from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

import src.schemas.review as schemas
from src.api.v1.dependencies import (
    ReviewsServiceDependency,
    get_active_user,
    get_hr_user,
)
from src.services.exceptions import (
    EntityCreateError,
    EntityDeleteError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get(
    "/{review_id}",
    dependencies=[Depends(get_active_user)],
    response_model=schemas.ReviewRead,
    responses={
        200: {"description": "Review retrieved successfully"},
        404: {"description": "Review not found"},
        400: {"description": "Failed to read review"},
    },
)
async def get_review(review_id: int, service: ReviewsServiceDependency):
    """
    Get a review by ID.

    - **review_id**: The ID of the review to retrieve.

    Raises:
    - **HTTPException**:
        - 404: If the review is not found.
        - 400: If reading the review fails.

    Returns:
    - **ReviewRead**: The review data.
    """
    try:
        review = await service.read_by_id(review_id)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read review"
        )

    return review


@router.post(
    "/",
    response_model=schemas.ReviewRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Review created successfully"},
        400: {"description": "Failed to create review"},
    },
)
async def create_review(
    review: schemas.ReviewCreate,
    service: ReviewsServiceDependency,
    current_user: Annotated[schemas.UserRead, Depends(get_active_user)],
):
    """
    Create a new review.

    - **review**: The data for the new review.

    Raises:
    - **HTTPException**:
        - 400: If creating the review fails.

    Returns:
    - **ReviewRead**: The created review data.
    """
    try:
        created_review = await service.create(review, current_user)
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create review"
        )

    return created_review


@router.patch(
    "/{review_id}",
    response_model=schemas.ReviewRead,
    responses={
        200: {"description": "Review updated successfully"},
        404: {"description": "Review not found"},
        400: {"description": "Failed to update review"},
    },
)
async def update_review(
    review_id: int,
    review_update: schemas.ReviewUpdate,
    service: ReviewsServiceDependency,
    current_user: Annotated[schemas.UserRead, Depends(get_active_user)],
):
    """
    Update a review by ID.

    - **review_id**: The ID of the review to update.
    - **review_update**: The updated data for the review.

    Raises:
    - **HTTPException**:
        - 404: If the review is not found.
        - 400: If updating the review fails.

    Returns:
    - **ReviewRead**: The updated review data.
    """
    try:
        updated_review = await service.update_by_id(
            review_id, review_update, current_user
        )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update review"
        )

    return updated_review


@router.delete(
    "/{review_id}",
    dependencies=[Depends(get_hr_user)],
    responses={
        200: {"description": "Review deleted successfully"},
        400: {"description": "Failed to delete review"},
        404: {"description": "Review not found"},
    },
)
async def delete_review(review_id: int, service: ReviewsServiceDependency):
    """
    Delete a review by ID.

    - **review_id**: The ID of the review to delete.

    Raises:
    - **HTTPException**:
        - 404: If the review is not found.
        - 400: If deleting the review fails.

    Returns:
    - **dict**: A confirmation of deletion (`is_success`: bool).
    """
    try:
        review_deleted = await service.delete_by_id(review_id)
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    except EntityDeleteError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete review"
        )

    return {"is_success": review_deleted}


@router.get(
    "/",
    dependencies=[Depends(get_active_user)],
    response_model=List[schemas.ReviewRead],
    responses={
        200: {"description": "List of reviews retrieved successfully"},
        400: {"description": "Failed to read reviews"},
    },
)
async def get_reviews(
    service: ReviewsServiceDependency,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    """
    Get a list of all reviews with pagination.

    - **page**: The page number to retrieve (default is 1).
    - **limit**: The number of items per page (default is 10).

    Raises:
    - **HTTPException**:
        - 400: If reading the reviews fails.

    Returns:
    - **List[ReviewRead]**: The list of reviews.
    """
    try:
        reviews = await service.read_all(page=page, limit=limit)
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read reviews",
        )

    return reviews
