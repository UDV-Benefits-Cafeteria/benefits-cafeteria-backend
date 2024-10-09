from src.repositories.benefits import BenefitsRepository
from src.services.benefits import BenefitsService


# This func is made for testing.
def get_benefits_service():
    return BenefitsService(BenefitsRepository())
