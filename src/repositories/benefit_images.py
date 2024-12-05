from src.models.benefits import BenefitImage
from src.repositories.base import SQLAlchemyRepository


class BenefitImagesRepository(SQLAlchemyRepository[BenefitImage]):
    model = BenefitImage
