import random
from typing import List

from fastapi import APIRouter

from src.api.v1.fake.generators import generate_fake_benefit
from src.schemas.benefit import (
    BenefitCreate,
    BenefitImageRead,
    BenefitRead,
    BenefitUpdate,
)

router = APIRouter(prefix="/benefits", tags=["Benefits"])


@router.get("/{benefit_id}", response_model=BenefitRead)
async def get_benefit(benefit_id: int):
    benefit = generate_fake_benefit(benefit_id)
    return benefit


@router.post("", response_model=BenefitRead)
async def create_benefit(benefit: BenefitCreate):
    benefit_id = random.randint(1000, 9999)
    benefit_result = benefit.model_dump()
    benefit_result["id"] = benefit_id

    images = []
    if benefit.images:
        for image in benefit.images:
            image_read = BenefitImageRead(
                id=random.randint(1000, 9999),
                benefit_id=benefit_id,
                image_url=image.image_url,
                is_primary=image.is_primary,
                description=image.description,
            )
            images.append(image_read.model_dump())

    benefit_result["images"] = images
    return benefit_result


@router.patch("/{benefit_id}", response_model=BenefitRead)
async def update_benefit(benefit_id: int, benefit_update: BenefitUpdate):
    existing_benefit = generate_fake_benefit(benefit_id)

    update_data = benefit_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field != "images":
            setattr(existing_benefit, field, value)

    if "images" in update_data:
        updated_images = []
        for image in benefit_update.images:
            updated_image = BenefitImageRead(
                id=random.randint(1000, 9999),
                benefit_id=benefit_id,
                image_url=image.image_url,
                is_primary=image.is_primary,
                description=image.description,
            )
            updated_images.append(updated_image)
        existing_benefit.images = updated_images

    return existing_benefit


@router.delete("/{benefit_id}")
async def delete_benefit(benefit_id: int):
    return {"is_success": True}


@router.get("", response_model=List[BenefitRead])
async def get_benefits():
    benefits = []
    for id in range(10):
        benefit = generate_fake_benefit(id).model_dump()
        benefits.append(benefit)
    return benefits
