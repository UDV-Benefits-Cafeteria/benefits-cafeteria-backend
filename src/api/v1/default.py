from fastapi import APIRouter

from repositories.legal_entities import LegalEntitiesRepository
from schemas.LegalEntity import LegalEntitySchemaAdd

router = APIRouter()


@router.get("/")
async def index():
    return {"index": True}


@router.get("/ping")
async def ping():
    return {"success": True}

@router.post("/le")
async def legal_entities(legal_entity: LegalEntitySchemaAdd):
    legal_entities_dict = legal_entity.model_dump()
    legal_entity_id = await LegalEntitiesRepository().add_one(legal_entities_dict)
    return {"legal_entity_id": legal_entity_id}
