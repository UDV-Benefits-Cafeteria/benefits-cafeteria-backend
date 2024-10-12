from typing import Annotated

from fastapi import Depends

from src.services.benefits import BenefitsService, get_benefits_service
from src.services.users import UsersService, get_users_service

UsersServiceDependency = Annotated[BenefitsService, Depends(get_users_service)]
BenefitsServiceDependency = Annotated[UsersService, Depends(get_benefits_service)]
