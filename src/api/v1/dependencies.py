from src.repositories.legal_entities import LegalEntitiesRepository
from src.services.legal_entities import LegalEntitiesService
from src.services.benefits import BenefitsService
from src.repositories.benefits import BenefitsRepository

def legal_entities_dependency():
    return LegalEntitiesService(LegalEntitiesRepository())

def get_benefits_service():
    return BenefitsService(BenefitsRepository())
