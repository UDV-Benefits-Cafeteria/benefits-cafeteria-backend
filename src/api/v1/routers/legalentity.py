import random
from typing import List

from fastapi import APIRouter

from src.api.v1.fake.generators import generate_fake_legal_entity
from src.schemas.legalentity import (
    LegalEntityCreate,
    LegalEntityRead,
    LegalEntityUpdate,
)

router = APIRouter(prefix="/legal-entities", tags=["Legal Entities"])


@router.get("/{entity_id}", response_model=LegalEntityRead)
async def get_legal_entity(entity_id: int):
    legal_entity = generate_fake_legal_entity(entity_id)
    return legal_entity


@router.post("", response_model=LegalEntityRead)
async def create_legal_entity(legal_entity: LegalEntityCreate):
    entity_id = random.randint(1, 1000)
    legal_entity_read = LegalEntityRead(id=entity_id, name=legal_entity.name)
    return legal_entity_read


@router.patch("/{entity_id}", response_model=LegalEntityRead)
async def update_legal_entity(entity_id: int, legal_entity_update: LegalEntityUpdate):
    existing_entity = generate_fake_legal_entity(entity_id)

    update_data = legal_entity_update.model_dump(exclude_unset=True)
    updated_entity_data = existing_entity.model_dump()
    updated_entity_data.update(update_data)

    updated_entity = LegalEntityRead(**updated_entity_data)
    return updated_entity


@router.delete("/{entity_id}")
async def delete_legal_entity(entity_id: int):
    return {"is_success": True}


@router.get("", response_model=List[LegalEntityRead])
async def get_legal_entities():
    legal_entities = []
    for id in range(1, 11):
        entity = generate_fake_legal_entity(id)
        legal_entities.append(entity)
    return legal_entities
