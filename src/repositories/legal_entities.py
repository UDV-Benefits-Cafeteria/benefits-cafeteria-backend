"""
This file is made for testing.
"""
from src.models import LegalEntity
from src.repositories.abstract import SQLAlchemyRepository


class LegalEntitiesRepository(SQLAlchemyRepository):
    model = LegalEntity
