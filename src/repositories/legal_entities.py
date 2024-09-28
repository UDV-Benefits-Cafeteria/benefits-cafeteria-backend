from models import LegalEntity
from utils.repository import SQLAlchemyRepository


class LegalEntitiesRepository(SQLAlchemyRepository):
    model = LegalEntity