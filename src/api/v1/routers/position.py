import random

from fastapi import APIRouter

from src.api.v1.fake.generators import generate_fake_position
from src.schemas.position import PositionCreate, PositionRead, PositionUpdate

router = APIRouter(prefix="/positions", tags=["Positions"])


@router.get("/{position_id}", response_model=PositionRead)
async def get_position(position_id: int):
    position = generate_fake_position(position_id)
    return position


@router.post("", response_model=PositionRead)
async def create_position(position: PositionCreate):
    position_id = random.randint(1, 1000)
    position_read = PositionRead(id=position_id, name=position.name)
    return position_read


@router.patch("/{position_id}", response_model=PositionRead)
async def update_position(position_id: int, position_update: PositionUpdate):
    existing_position = generate_fake_position(position_id)

    update_data = position_update.model_dump(exclude_unset=True)
    updated_position_data = existing_position.model_dump()
    updated_position_data.update(update_data)

    updated_position = PositionRead(**updated_position_data)
    return updated_position


@router.delete("/{position_id}")
async def delete_position(position_id: int):
    return {"is_success": True}


@router.get("", response_model=list[PositionRead])
async def get_positions():
    positions = []
    for id in range(1, 11):
        position = generate_fake_position(id)
        positions.append(position)
    return positions
