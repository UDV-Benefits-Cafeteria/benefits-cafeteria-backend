from io import BytesIO
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

import src.schemas.user as schemas
from src.api.v1.dependencies import (
    LegalEntitiesServiceDependency,
    PositionsServiceDependency,
    UsersServiceDependency,
    get_active_user,
)
from src.services.exceptions import (
    EntityCreateError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)
from src.utils.role_mapper import map_role

router = APIRouter(prefix="/users", tags=["Users"])


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
    user: schemas.UserCreate,
    service: UsersServiceDependency,
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
        created_user = await service.create(user)
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user"
        )
    await service.send_email_registration(user)
    return created_user


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
    user_id: int,
    user_update: schemas.UserUpdate,
    service: UsersServiceDependency,
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
        updated_user = await service.update_by_id(user_id, user_update)
        return updated_user
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    except EntityUpdateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user"
        )


@router.get(
    "/{user_id}",
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
    response_model=schemas.UserUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Users uploaded successfully"},
        400: {"description": "Invalid file type or error reading Excel file"},
    },
)
async def upload_users(
    service: UsersServiceDependency,
    positions_service: PositionsServiceDependency,
    legal_entities_service: LegalEntitiesServiceDependency,
    file: UploadFile = File(...),
):
    """
    Upload users from an Excel file.

    - **file**: The Excel file containing user data.

    Raises:
    - **HTTPException**:
        - 400: If the file type is invalid or there are errors reading the file.

    Returns:
    - **schemas.UserUploadResponse**: Information about created users and errors.
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
        df = pd.read_excel(BytesIO(contents))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error reading Excel file."
        )

    required_columns = [
        "email",
        "имя",
        "фамилия",
        "отчество",
        "роль",
        "дата найма",
        "адаптационный период",
        "ю-коины",
        "должность",
        "юр. лицо",
    ]
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing columns: {', '.join(missing_columns)}",
        )

    created_users = []
    errors = []

    for idx, (_, row) in enumerate(df.iterrows(), start=2):
        try:
            role = map_role(row["роль"])

            position = await positions_service.get_by_name(row["должность"])
            if not position:
                raise ValueError(f"Position '{row['должность']}' not found.")
            position_id = position.id

            legal_entity = await legal_entities_service.get_by_name(row["юр. лицо"])
            if not legal_entity:
                raise ValueError(f"Legal entity '{row['юр. лицо']}' not found.")
            legal_entity_id = legal_entity.id

            user_data = schemas.UserCreate(
                email=row["email"],
                firstname=row["имя"],
                lastname=row["фамилия"],
                middlename=row.get("отчество"),
                role=role,
                hired_at=row["дата найма"],
                is_adapted=row["адаптационный период"],
                coins=row["ю-коины"],
                position_id=position_id,
                legal_entity_id=legal_entity_id,
            )

            created_user = await service.create(user_data)
            created_users.append(created_user)
        except ValueError as ve:
            errors.append({"row": idx, "error": f"Value Error: {str(ve)}"})
        except Exception as e:
            errors.append({"row": idx, "error": f"Error: {str(e)}"})

    return schemas.UserUploadResponse(created_users=created_users, errors=errors)
