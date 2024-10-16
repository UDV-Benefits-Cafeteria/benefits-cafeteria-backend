import random

from fastapi import APIRouter

from src.api.v1.fake.generators import (
    generate_fake_legal_entity,
    generate_fake_position,
    generate_fake_user,
)
from src.schemas.user import UserBase, UserRead, UserUpdate

router = APIRouter(prefix="/users-fake", tags=["Users Fake"])


@router.post("", response_model=UserRead)
async def create_user(user: UserBase):
    user_id = random.randint(1, 1000)

    user_data = user.model_dump()
    user_data["id"] = user_id
    user_data["is_verified"] = False
    user_data["position"] = (
        generate_fake_position(user.position_id) if user.position_id else None
    )
    user_data["legal_entity"] = (
        generate_fake_legal_entity(user.legal_entity_id)
        if user.legal_entity_id
        else None
    )
    user_read = UserRead(**user_data)
    return user_read


@router.get("/me", response_model=UserRead)
async def get_user_me():
    user = generate_fake_user(228)
    return user


@router.get("/trigger_error")
async def trigger_error():
    raise ZeroDivisionError


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int):
    user = generate_fake_user(user_id)
    return user


@router.get("", response_model=list[UserRead])
async def get_users():
    requests = []
    for i in range(1, 11):
        benefit_request = generate_fake_user(i)
        requests.append(benefit_request)
    return requests


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, user_update: UserUpdate):
    existing_user = generate_fake_user(user_id)

    update_data = user_update.model_dump(exclude_unset=True)
    updated_user_data = existing_user.model_dump()
    updated_user_data.update(update_data)

    updated_user = UserRead(**updated_user_data)

    return updated_user
