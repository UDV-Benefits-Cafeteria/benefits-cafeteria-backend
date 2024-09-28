from src.models import Benefit
from src.utils.repository import SQLAlchemyRepository


class BenefitsRepository(SQLAlchemyRepository):
    model = Benefit
