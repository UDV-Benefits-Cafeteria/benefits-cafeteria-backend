from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import src.schemas.user as schemas
from src.api.v1.dependencies import get_user_service
from src.services.users import UsersService

router = APIRouter(prefix="/users", tags=["Users"])


ServiceDependency = Annotated[UsersService, Depends(get_user_service)]


@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: schemas.UserCreate,
    service: ServiceDependency,
):
    try:
        created_user = await service.create_and_get_one(user)
        return created_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{user_id}", response_model=schemas.UserRead)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    service: ServiceDependency,
):
    try:
        updated_user = await service.update_and_get_one(user_id, user_update)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=schemas.UserRead)
async def get_user(
    user_id: int,
    service: ServiceDependency,
):
    user = await service.get_one(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post(
    "/batch", response_model=list[schemas.UserRead], status_code=status.HTTP_201_CREATED
)
async def create_users(
    users_create: schemas.UsersCreate,
    service: ServiceDependency,
):
    for user in users_create.users:
        user.is_verified = False
    try:
        created_users = await service.create_many_and_get_many(users_create.users)
        return created_users
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
