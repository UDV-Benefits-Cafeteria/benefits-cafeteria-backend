from src.repositories.benefit_images import BenefitImagesRepository
from src.repositories.benefits import BenefitsRepository
from src.repositories.legal_entities import LegalEntitiesRepository
from src.services.benefits import BenefitsService
from src.services.legal_entities import LegalEntitiesService


def get_legal_entities_service():
    return LegalEntitiesService(LegalEntitiesRepository())


def get_benefits_service():
    return BenefitsService(BenefitsRepository(), BenefitImagesRepository())
