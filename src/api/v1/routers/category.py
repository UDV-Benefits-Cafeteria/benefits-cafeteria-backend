import random

from fastapi import APIRouter

from src.api.v1.fake.generators import generate_fake_category
from src.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int):
    category = generate_fake_category(category_id)
    return category


@router.post("", response_model=CategoryRead)
async def create_category(category: CategoryCreate):
    category_id = random.randint(1, 1000)
    category_read = CategoryRead(id=category_id, name=category.name)
    return category_read


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(category_id: int, category_update: CategoryUpdate):
    existing_category = generate_fake_category(category_id)

    update_data = category_update.model_dump(exclude_unset=True)
    updated_category_data = existing_category.model_dump()
    updated_category_data.update(update_data)

    updated_category = CategoryRead(**updated_category_data)
    return updated_category


@router.delete("/{category_id}")
async def delete_category(category_id: int):
    return {"is_success": True}


@router.get("", response_model=list[CategoryRead])
async def get_categories():
    categories = []
    for id in range(1, 11):
        category = generate_fake_category(id)
        categories.append(category)
    return categories
