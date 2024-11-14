from typing import Annotated, Any, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)

import src.schemas.user as schemas
from src.api.v1.dependencies import (
    LegalEntitiesServiceDependency,
    PositionsServiceDependency,
    UsersServiceDependency,
    get_active_user,
    get_hr_user,
)
from src.schemas.benefit import SortOrderField
from src.services.exceptions import (
    EntityCreateError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
    PermissionDeniedError,
)
from src.utils.email_sender.users import (
    send_user_coin_update_email,
    send_user_greeting_email,
)
from src.utils.filter_parsers import range_filter_parser

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=list[schemas.UserRead],
    responses={
        200: {"description": "Users retrieved successfully"},
        400: {"description": "Failed to retrieve users"},
    },
)
async def get_users(
    current_user: Annotated[schemas.UserRead, Depends(get_hr_user)],
    service: UsersServiceDependency,
    query: Annotated[
        Optional[str],
        Query(description="Search query for fullname"),
    ] = None,
    is_active: Annotated[Optional[bool], Query()] = None,
    is_adapted: Annotated[Optional[bool], Query()] = None,
    is_verified: Annotated[Optional[bool], Query()] = None,
    role: Annotated[Optional[schemas.UserRole], Query()] = None,
    hired_at: Annotated[
        Optional[str],
        Query(
            description='Filter for hired_at date range, e.g., "gte:2022-01-01,lte:2022-12-31"'
        ),
    ] = None,
    legal_entity_id: Annotated[Optional[int], Query()] = None,
    sort_by: Annotated[
        Optional[schemas.UserSortFields],
        Query(
            description="Sort by 'hired_at', 'coins' or 'fullname'",
        ),
    ] = None,
    sort_order: Annotated[SortOrderField, Query()] = SortOrderField.ASCENDING,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    try:
        filters: dict[str, Any] = {
            field: value
            for field, value in {
                "is_active": is_active,
                "is_adapted": is_adapted,
                "is_verified": is_verified,
                "role": role.value if role else None,
                "hired_at": range_filter_parser(hired_at, "hired_at"),
                "legal_entity_id": legal_entity_id,
            }.items()
            if value is not None
        }

        if current_user.role == schemas.UserRole.HR:
            filters["legal_entity_id"] = current_user.legal_entity_id

        users = await service.search_users(
            query=query,
            filters=filters,
            sort_by=sort_by.value if sort_by else None,
            sort_order=sort_order.value,
            limit=limit,
            offset=offset,
        )
        return users
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve users",
        )


@router.post(
    "/",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Failed to create user"},
    },
)
async def create_user(
    current_user: Annotated[schemas.UserRead, Depends(get_hr_user)],
    user: schemas.UserCreate,
    service: UsersServiceDependency,
    background_tasks: BackgroundTasks,
):
    """
    Create a new user.

    - **user**: The user creation data.

    Raises:
    - **HTTPException**:
        - 400: If user creation fails.

    Returns:
    - **schemas.UserRead**: The created user information.
    """
    try:
        created_user = await service.create(
            create_schema=user,
            current_user=current_user,
            background_tasks=background_tasks,
        )

        await send_user_greeting_email(
            created_user.email, created_user.firstname, background_tasks
        )

        return created_user
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )


@router.get(
    "/me",
    response_model=schemas.UserRead,
    responses={
        200: {"description": "Current user information"},
        401: {"description": "Unauthorized, user not authenticated"},
    },
)
async def get_current_user(
    current_user: Annotated[schemas.UserRead, Depends(get_active_user)],
):
    """
    Retrieve the current authenticated user's information.

    Returns:
    - **schemas.UserRead**: The current user's information.

    Raises:
    - **HTTPException**:
        - 401: If the user is not authenticated.
    """
    return current_user


@router.patch(
    "/{user_id}",
    response_model=schemas.UserRead,
    responses={
        200: {"description": "User updated successfully"},
        404: {"description": "User not found"},
        400: {"description": "Failed to update user"},
    },
)
async def update_user(
    current_user: Annotated[schemas.UserRead, Depends(get_active_user)],
    user_id: int,
    user_update: schemas.UserUpdate,
    service: UsersServiceDependency,
    background_tasks: BackgroundTasks,
):
    """
    Update an existing user by ID.

    - **user_id**: The ID of the user to update.
    - **user_update**: The data to update the user.

    Raises:
    - **HTTPException**:
        - 404: If the user is not found.
        - 400: If user update fails.

    Returns:
    - **schemas.UserRead**: The updated user information.
    """
    try:
        updated_user = await service.update_by_id(
            entity_id=user_id,
            update_schema=user_update,
            current_user=current_user,
            background_tasks=background_tasks,
        )

        if user_update.coins:
            await send_user_coin_update_email(
                updated_user.email,
                updated_user.firstname,
                updated_user.coins - current_user.coins,
                updated_user.coins,
                background_tasks,
            )

        return updated_user
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )


@router.get(
    "/{user_id}",
    dependencies=[Depends(get_active_user)],
    response_model=schemas.UserRead,
    responses={
        200: {"description": "User retrieved successfully"},
        404: {"description": "User not found"},
        400: {"description": "Failed to read user"},
    },
)
async def get_user(
    user_id: int,
    service: UsersServiceDependency,
):
    """
    Retrieve a user by ID.

    - **user_id**: The ID of the user to retrieve.

    Raises:
    - **HTTPException**:
        - 404: If the user is not found.
        - 400: If user read fails.

    Returns:
    - **schemas.UserRead**: The retrieved user information.
    """
    try:
        user = await service.read_by_id(user_id)
        return user
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read user"
        )


@router.post(
    "/upload",
    response_model=schemas.UserValidationResponse,
    responses={
        200: {"description": "Users validated successfully"},
        400: {"description": "Invalid file type or error reading Excel file"},
    },
)
async def upload_users(
    service: UsersServiceDependency,
    positions_service: PositionsServiceDependency,
    legal_entities_service: LegalEntitiesServiceDependency,
    file: UploadFile = File(...),
    current_user: schemas.UserRead = Depends(get_hr_user),
):
    """
    Upload users from an Excel file for validation.

    - **file**: The Excel file containing user data.

    Raises:
    - **HTTPException**:
        - 400: If the file type is invalid or there are errors reading the file.

    Returns:
    - **schemas.UserValidationResponse**: Information about users that can be created and errors.
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
        valid_users, errors = await service.parse_users_from_excel(
            contents,
            positions_service=positions_service,
            legal_entities_service=legal_entities_service,
            current_user=current_user,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error while parsing users. Some columns might be missing.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while parsing the Excel file",
        )

    return schemas.UserValidationResponse(valid_users=valid_users, errors=errors)


@router.post(
    "/bulk_create",
    response_model=schemas.UserUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Users created successfully"},
        400: {"description": "Failed to create users"},
    },
)
async def bulk_create_users(
    current_user: Annotated[schemas.UserRead, Depends(get_hr_user)],
    users_data: list[schemas.UserCreate],
    service: UsersServiceDependency,
    background_tasks: BackgroundTasks,
):
    """
    Create multiple users from the provided list.

    - **users_data**: The list of user data to create.

    Raises:
    - **HTTPException**:
        - 400: If user creation fails.

    Returns:
    - **schemas.UserUploadResponse**: Information about created users and errors.
    """
    created_users = []
    errors = []

    for idx, user_data in enumerate(users_data, start=1):
        try:
            user_data = schemas.UserCreate.model_validate(user_data)

            created_user = await service.create(
                create_schema=user_data,
                current_user=current_user,
                background_tasks=background_tasks,
            )
            created_users.append(created_user)
        except EntityCreateError:
            errors.append({"row": idx, "error": "Creation Error"})
        except PermissionDeniedError:
            errors.append(
                {"row": idx, "error": "Permission Error. Check legal entity."}
            )
        except Exception:
            errors.append({"row": idx, "error": "Unexpected Error"})

    return schemas.UserUploadResponse(created_users=created_users, errors=errors)


@router.patch(
    "/{user_id}/image",
    response_model=schemas.UserRead,
    responses={
        200: {"description": "Image successfully uploaded"},
        400: {"description": "Failed to upload image"},
        404: {"description": "User not found"},
    },
)
async def upload_image(
    current_user: Annotated[schemas.UserRead, Depends(get_active_user)],
    user_id: int,
    service: UsersServiceDependency,
    image: UploadFile = File(...),
):
    """
    Upload an image for a specific user.

    Args:
    - **user_id (int)**: The ID of the user to upload the image for.
    - **image (UploadFile)**: The image file to upload.
    - **service (UsersServiceDependency)**: The service handling the logic.

    Returns:
    - **User**: Updated user data after image upload.

    Raises:
    - **HTTPException**:
        - 400: If there is an error uploading the image.
        - 404: If the user is not found.
    """
    if current_user.role not in [schemas.UserRole.ADMIN, schemas.UserRole.HR]:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot upload images to other users",
            )
    try:
        updated_user = await service.update_image(image, user_id)
        return updated_user
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload image",
        )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.delete(
    "/{user_id}/image",
    dependencies=[Depends(get_active_user)],
    response_model=schemas.UserRead,
    responses={
        200: {"description": "Image successfully deleted"},
        400: {"description": "Failed to delete image"},
        404: {"description": "User not found"},
    },
)
async def delete_image(
    current_user: Annotated[schemas.UserRead, Depends(get_active_user)],
    user_id: int,
    service: UsersServiceDependency,
):
    """
    Delete the image of a specific user.

    Args:
    - **user_id (int)**: The ID of the user whose image will be deleted.
    - **service (UsersServiceDependency)**: The service handling the logic.

    Returns:
    - **User**: Updated user data after image deletion.

    Raises:
    - **HTTPException**:
        - 400: If there is an error deleting the image.
        - 404: If the user is not found.
    """
    if current_user.role not in [schemas.UserRole.ADMIN, schemas.UserRole.HR]:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete images from other users",
            )
    try:
        updated_user = await service.update_image(None, user_id)
        return updated_user
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete image",
        )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
