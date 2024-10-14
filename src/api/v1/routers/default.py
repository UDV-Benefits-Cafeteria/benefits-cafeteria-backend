from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, status

import src.schemas.benefit as schemas
from src.api.v1.dependencies import get_benefits_service
from src.celery.tasks import test_task
from src.services.benefits import BenefitsService

router = APIRouter()


@router.get("/")
async def index() -> Dict[str, str]:
    status = test_task.apply_async()
    return {"status": status.wait(timeout=None, interval=0.5)}


@router.get("/ping")
async def ping():
    return {"success": True}


ServiceDep = Annotated[BenefitsService, Depends(get_benefits_service)]


@router.post("/benefits", response_model=int)
async def create_benefit(
    benefit: schemas.BenefitCreate,
    benefits_service: ServiceDep,
):
    benefit_id = await benefits_service.create(benefit)
    return benefit_id


@router.patch("/benefits/{benefit_id}")
async def update_benefit(
    benefit_id: int,
    benefit: schemas.BenefitUpdate,
    benefits_service: ServiceDep,
):
    await benefits_service.update_by_id(benefit_id, benefit)
    return {"is_success": True}


# This func is made for testing.
@router.get("/benefits/{benefit_id}", response_model=schemas.BenefitRead)
async def read_benefit(
    benefit_id: int,
    benefits_service: Annotated[BenefitsService, Depends(get_benefits_service)],
):
    try:
        benefit = await benefits_service.read_by_id(benefit_id)
        return benefit
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# This func is made for testing.
@router.get("/benefits", response_model=list[schemas.BenefitRead])
async def read_benefits(
    benefits_service: Annotated[BenefitsService, Depends(get_benefits_service)],
):
    benefits = await benefits_service.read_all()
    return benefits


# This func is made for testing.


# This func is made for testing.
@router.delete("/benefits/{benefit_id}")
async def delete_benefit(
    benefit_id: int,
    benefits_service: Annotated[BenefitsService, Depends(get_benefits_service)],
):
    await benefits_service.delete_by_id(benefit_id)
    return {"is_success": True}
