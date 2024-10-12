import src.schemas.benefit as schemas
from src.repositories.benefits import BenefitsRepository
from src.services.abstract import AbstractService


class BenefitsService(
    AbstractService[schemas.BenefitCreate, schemas.BenefitRead, schemas.BenefitUpdate]
):
    pass


def get_benefits_service():
    return BenefitsService(
        BenefitsRepository(),
        schemas.BenefitCreate,
        schemas.BenefitRead,
        schemas.BenefitUpdate,
    )
