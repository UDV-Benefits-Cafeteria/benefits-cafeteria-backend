from src.models import Benefit
from src.repositories.abstract import SQLAlchemyRepository


class BenefitsRepository(SQLAlchemyRepository[Benefit]):
    model = Benefit
