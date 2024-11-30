from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi_limiter.depends import RateLimiter
from starlette import status

import src.schemas.user as user_schemas
from src.config import get_settings
from src.services.auth import AuthService
from src.services.benefit_requests import BenefitRequestsService
from src.services.benefits import BenefitsService
from src.services.categories import CategoriesService
from src.services.legal_entities import LegalEntitiesService
from src.services.positions import PositionsService
from src.services.sessions import SessionsService
from src.services.users import UsersService
from src.utils.elastic_index import ElasticClientDependency


async def get_users_service(es_client: ElasticClientDependency):
    return UsersService(es_client)


async def get_auth_service(es_client: ElasticClientDependency):
    return AuthService(es_client)


async def get_benefits_service(es_client: ElasticClientDependency):
    return BenefitsService(es_client)


async def get_benefit_requests_service(es_client: ElasticClientDependency):
    return BenefitRequestsService(es_client)


# Services that depend on ElasticSearch
AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
UsersServiceDependency = Annotated[UsersService, Depends(get_users_service)]
BenefitsServiceDependency = Annotated[BenefitsService, Depends(get_benefits_service)]
BenefitRequestsServiceDependency = Annotated[
    BenefitRequestsService, Depends(get_benefit_requests_service)
]

# Services that do NOT depend on ElasticSearch
SessionsServiceDependency = Annotated[SessionsService, Depends()]
PositionsServiceDependency = Annotated[PositionsService, Depends()]
CategoriesServiceDependency = Annotated[CategoriesService, Depends()]
LegalEntitiesServiceDependency = Annotated[LegalEntitiesService, Depends()]


BaseLimiter = Depends(RateLimiter(times=60, seconds=60))

settings = get_settings()


async def get_current_user(
    request: Request,
    users_service: UsersServiceDependency,
    sessions_service: SessionsServiceDependency,
) -> user_schemas.UserRead:
    session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    session = await sessions_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    user = await users_service.read_by_id(session.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )

    return user


async def get_active_user(
    current_user: Annotated[user_schemas.UserRead, Depends(get_current_user)],
) -> user_schemas.UserRead:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_hr_user(
    current_user: Annotated[user_schemas.UserRead, Depends(get_active_user)],
) -> user_schemas.UserRead:
    if current_user.role not in [
        user_schemas.UserRole.HR.value,
        user_schemas.UserRole.ADMIN.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: at least HR role required",
        )
    return current_user


async def get_admin_user(
    current_user: Annotated[user_schemas.UserRead, Depends(get_active_user)],
) -> user_schemas.UserRead:
    if current_user.role != user_schemas.UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin role required",
        )
    return current_user
