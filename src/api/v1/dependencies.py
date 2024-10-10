from src.repositories.benefits import BenefitsRepository
from src.repositories.users import UsersRepository
from src.schemas.benefit import BenefitCreate, BenefitRead, BenefitUpdate
from src.schemas.user import UserCreate, UserRead, UserUpdate
from src.services.benefits import BenefitsService
from src.services.users import UsersService


def get_benefits_service():
    return BenefitsService(
        BenefitsRepository(), BenefitCreate, BenefitRead, BenefitUpdate
    )


def get_user_service():
    return UsersService(UsersRepository(), UserCreate, UserRead, UserUpdate)
