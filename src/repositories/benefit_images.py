from src.models.benefits import BenefitImage
from src.repositories.abstract import SQLAlchemyRepository


class BenefitImagesRepository(SQLAlchemyRepository[BenefitImage]):
    model = BenefitImage
