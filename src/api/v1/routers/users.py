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
    get_hr_user,
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
    response_model=schemas.UserValidationResponse,
    responses={
        200: {"description": "Users validated successfully"},
        400: {"description": "Invalid file type or error reading Excel file"},
    },
)
async def upload_users(
    current_user: Annotated[schemas.UserRead, Depends(get_hr_user)],
    service: UsersServiceDependency,
    positions_service: PositionsServiceDependency,
    legal_entities_service: LegalEntitiesServiceDependency,
    file: UploadFile = File(...),
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
        df = pd.read_excel(BytesIO(contents))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error reading Excel file"
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

    valid_users = []
    errors = []

    for idx, (_, row) in enumerate(df.iterrows(), start=2):
        try:
            role = map_role(str(row["роль"]))

            position_name = str(row["должность"])
            position = await positions_service.read_by_name(position_name)
            if not position:
                raise ValueError(f"Position '{position_name}' not found.")
            position_id = position.id

            legal_entity_name = str(row["юр. лицо"])
            legal_entity = await legal_entities_service.read_by_name(legal_entity_name)
            if not legal_entity:
                raise ValueError(f"Legal entity '{legal_entity_name}' not found.")
            legal_entity_id = legal_entity.id

            is_adapted = str(row["адаптационный период"]).strip().lower()
            if is_adapted in ["true", "1", "yes", "да"]:
                is_adapted = True
            elif is_adapted in ["false", "0", "no", "нет"]:
                is_adapted = False
            else:
                raise ValueError(
                    f"Invalid value for 'адаптационный период': '{row['адаптационный период']}'"
                )

            try:
                hired_at = pd.to_datetime(row["дата найма"], dayfirst=True).date()
            except Exception:
                raise ValueError(
                    f"Invalid date format for 'дата найма': '{row['дата найма']}'."
                )

            user_data = schemas.UserCreate(
                email=str(row["email"]).strip(),
                firstname=str(row["имя"]).strip(),
                lastname=str(row["фамилия"]).strip(),
                middlename=str(row["отчество"]).strip()
                if pd.notna(row["отчество"])
                else None,
                role=role,
                hired_at=hired_at,
                is_adapted=is_adapted,
                coins=int(row["ю-коины"]) if pd.notna(row["ю-коины"]) else 0,
                position_id=position_id,
                legal_entity_id=legal_entity_id,
            )

            user_data = schemas.UserCreate.model_validate(user_data)

            try:
                await service.read_by_email(user_data.email)
                raise ValueError(f"User with email '{user_data.email}' already exists.")
            except EntityNotFoundError:
                pass
            except EntityReadError as e:
                raise ValueError(f"Error reading user data: {str(e)}")

            valid_users.append(user_data)
        except ValueError as ve:
            errors.append({"row": idx, "error": f"Value Error: {str(ve)}"})
        except Exception as e:
            errors.append({"row": idx, "error": f"Error: {str(e)}"})

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

            created_user = await service.create(user_data)
            created_users.append(created_user)
        except EntityCreateError as e:
            errors.append({"row": idx, "error": f"Creation Error: {str(e)}"})
        except Exception as e:
            errors.append({"row": idx, "error": f"Unexpected Error: {str(e)}"})

    for user in created_users:
        await service.send_email_registration(user)

    return schemas.UserUploadResponse(created_users=created_users, errors=errors)
