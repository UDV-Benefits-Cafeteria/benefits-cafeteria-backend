"""
This file is made for testing.
"""
from src.models.benefits import BenefitImage
from src.utils.repository import SQLAlchemyRepository


class BenefitImagesRepository(SQLAlchemyRepository[BenefitImage]):
    model = BenefitImage
