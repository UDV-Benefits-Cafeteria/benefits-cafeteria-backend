"""
This file is made for testing.
"""
from src.schemas.LegalEntity import LegalEntitySchemaAdd
from src.utils.repository import AbstractRepository


class LegalEntitiesService:
    def __init__(self, legal_entities_repo: AbstractRepository):
        self.legal_entities_repo: AbstractRepository = legal_entities_repo

    async def add_legal_entity(self, legal_entity: LegalEntitySchemaAdd):
        legal_entities_dict = legal_entity.model_dump()
        legal_entity_id = await self.legal_entities_repo.add_one(legal_entities_dict)
        return legal_entity_id
