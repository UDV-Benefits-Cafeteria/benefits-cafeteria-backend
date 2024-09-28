from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import get_benefits_service, legal_entities_dependency
from src.schemas.benefit import BenefitCreate, BenefitRead, BenefitUpdate
from src.schemas.LegalEntity import LegalEntitySchemaAdd
from src.services.benefits import BenefitsService
from src.services.legal_entities import LegalEntitiesService

router = APIRouter()


@router.get("/")
async def index():
    return {"index": True}


@router.get("/ping")
async def ping():
    return {"success": True}


@router.post("/le")
async def legal_entities(
    legal_entity: LegalEntitySchemaAdd,
    legal_entities_service: Annotated[
        LegalEntitiesService, Depends(legal_entities_dependency)
    ],
):
    legal_entity_id = await legal_entities_service.add_legal_entity(legal_entity)
    return {"legal_entity_id": legal_entity_id}


@router.post("/benefits", response_model=int)
async def create_benefit(
    benefit: BenefitCreate,
    benefits_service: Annotated[BenefitsService, Depends(get_benefits_service)],
):
    benefit_id = await benefits_service.create_benefit(benefit)
    return benefit_id


@router.get("/benefits/{benefit_id}", response_model=BenefitRead)
async def read_benefit(
    benefit_id: int,
    benefits_service: Annotated[BenefitsService, Depends(get_benefits_service)],
):
    try:
        benefit = await benefits_service.get_benefit(benefit_id)
        return benefit
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/benefits", response_model=List[BenefitRead])
async def read_benefits(
    benefits_service: Annotated[BenefitsService, Depends(get_benefits_service)]
):
    benefits = await benefits_service.get_benefits()
    return benefits


@router.patch("/benefits/{benefit_id}")
async def update_benefit(
    benefit_id: int,
    benefit: BenefitUpdate,
    benefits_service: Annotated[BenefitsService, Depends(get_benefits_service)],
):
    await benefits_service.update_benefit(benefit_id, benefit)
    return {"is_success": True}


@router.delete("/benefits/{benefit_id}")
async def delete_benefit(
    benefit_id: int,
    benefits_service: Annotated[BenefitsService, Depends(get_benefits_service)],
):
    await benefits_service.delete_benefit(benefit_id)
    return {"is_success": True}
