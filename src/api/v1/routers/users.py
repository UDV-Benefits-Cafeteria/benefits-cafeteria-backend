from io import BytesIO
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

import src.schemas.user as schemas
from src.api.v1.dependencies import (
    LegalEntitiesServiceDependency,
    PositionsServiceDependency,
    UsersServiceDependency,
    active_user,
)
from src.services.exceptions import (
    EntityCreateError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)
from src.utils.role_mapper import map_role

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: schemas.UserCreate,
    service: UsersServiceDependency,
):
    try:
        created_user = await service.create(user)
        return created_user
    except EntityCreateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user"
        )


@router.get("/me", response_model=schemas.UserRead)
async def get_current_user(
    current_user: Annotated[schemas.UserRead, Depends(active_user)],
):
    return current_user


@router.patch("/{user_id}", response_model=schemas.UserRead)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    service: UsersServiceDependency,
):
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


@router.get("/{user_id}", response_model=schemas.UserRead)
async def get_user(
    user_id: int,
    service: UsersServiceDependency,
):
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
)
async def upload_users(
    service: UsersServiceDependency,
    positions_service: PositionsServiceDependency,
    legal_entities_service: LegalEntitiesServiceDependency,
    file: UploadFile = File(...),
):
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
