from typing import List

from fastapi import APIRouter

from src.api.v1.fake.generators import generate_fake_benefit
from src.schemas.benefit import (
    BenefitCreate,
    BenefitImageCreate,
    BenefitRead,
    BenefitUpdate,
)

router = APIRouter()


@router.get("/benefits/{benefit_id}", response_model=BenefitRead)
async def get_benefit(benefit_id: int):
    benefit = generate_fake_benefit(benefit_id)
    return benefit


@router.post("/benefits", response_model=BenefitCreate)
async def create_benefit(benefit: BenefitCreate):
    images = []
    if benefit.images:
        for image in benefit.images:
            image_read = BenefitImageCreate(
                image_url=image.image_url,
                is_primary=image.is_primary,
                description=image.description,
            )
            images.append(image_read.model_dump())
    else:
        images = []

    benefit.model_dump()["images"] = images

    return benefit


@router.patch("/benefits/{benefit_id}")
async def update_benefit(benefit_id: int, benefit_update: BenefitUpdate):
    return {"is_success": True}


@router.delete("/benefits/{benefit_id}")
async def delete_benefit(benefit_id: int):
    return {"is_success": True}


@router.get("/benefits", response_model=List[BenefitRead])
async def get_benefits():
    benefits = []
    for id in range(10):
        benefit = generate_fake_benefit(id).model_dump()
        benefits.append(benefit)
    return benefits
