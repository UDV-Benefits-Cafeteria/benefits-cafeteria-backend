import src.schemas.benefit as schemas
from src.repositories.benefits import BenefitsRepository
from src.services.abstract import BaseService


class BenefitsService(
    BaseService[schemas.BenefitCreate, schemas.BenefitRead, schemas.BenefitUpdate]
):
    repo = BenefitsRepository
    create_schema = schemas.BenefitCreate
    read_schema = schemas.BenefitRead
    update_schema = schemas.BenefitUpdate
