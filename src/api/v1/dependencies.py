from src.repositories.benefit_images import BenefitImagesRepository
from src.repositories.benefits import BenefitsRepository
from src.services.benefits import BenefitsService
from src.models.benefits import Benefit

# This func is made for testing.


# This func is made for testing.
def get_benefits_service():
    return BenefitsService(BenefitsRepository())
