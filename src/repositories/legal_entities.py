"""
This file is made for testing.
"""
from src.models import LegalEntity
from src.utils.repository import SQLAlchemyRepository


class LegalEntitiesRepository(SQLAlchemyRepository):
    model = LegalEntity
