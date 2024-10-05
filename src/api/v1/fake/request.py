import random
from typing import List

from fastapi import APIRouter

from src.api.v1.fake.generators import (
    generate_fake_benefit,
    generate_fake_benefit_request,
    generate_fake_user,
)
from src.schemas.request import (
    BenefitRequestCreate,
    BenefitRequestRead,
    BenefitRequestUpdate,
    BenefitStatus,
)

router = APIRouter()


@router.post("/benefit-requests", response_model=BenefitRequestCreate)
async def create_benefit_request(benefit_request: BenefitRequestCreate):
    request_id = random.randint(1, 1000)

    benefit = generate_fake_benefit(
        benefit_request.benefit_id or random.randint(1, 100)
    )
    user = generate_fake_user(benefit_request.user_id or random.randint(1, 100))

    benefit_request_read = BenefitRequestRead(
        id=request_id,
        benefit_id=benefit.benefit_id,
        user_id=user.id,
        status=BenefitStatus.PENDING,
        content=benefit_request.content,
        comment=benefit_request.comment,
        benefit=benefit,
        user=user,
    )

    return benefit_request_read


@router.get("/benefit-requests/user/{user_id}", response_model=List[BenefitRequestRead])
async def get_benefit_requests_by_user(user_id: int):
    requests = []
    for i in range(1, 6):
        benefit_request = generate_fake_benefit_request(request_id=i, user_id=user_id)
        requests.append(benefit_request)
    return requests


@router.get("/benefit-requests/{request_id}", response_model=BenefitRequestRead)
async def get_benefit_request(request_id: int):
    benefit_request = generate_fake_benefit_request(request_id=request_id)
    return benefit_request


@router.get("/benefit-requests", response_model=List[BenefitRequestRead])
async def get_benefit_requests():
    requests = []
    for i in range(1, 11):
        benefit_request = generate_fake_benefit_request(request_id=i)
        requests.append(benefit_request)
    return requests


@router.patch("/benefit-requests/{request_id}", response_model=BenefitRequestUpdate)
async def update_benefit_request(
    request_id: int, benefit_request_update: BenefitRequestUpdate
):
    existing_request = generate_fake_benefit_request(request_id=request_id)

    update_data = benefit_request_update.model_dump(exclude_unset=True)
    updated_request_data = existing_request.model_dump()
    updated_request_data.update(update_data)

    updated_request = BenefitRequestRead(**updated_request_data)

    return updated_request


@router.delete("/benefit-requests/{request_id}")
async def delete_benefit_request(request_id: int):
    return {"is_success": True}
