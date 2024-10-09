import src.schemas.benefit as schemas
from src.services.abstract import AbstractService

class BenefitsService(AbstractService[schemas.BenefitCreate, schemas.BenefitRead, schemas.BenefitUpdate]):
    pass

