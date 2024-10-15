from typing import Annotated

from fastapi import Depends, HTTPException, Request
from starlette import status

from src.config import settings
from src.schemas.user import UserRead, UserRole
from src.services.auth import AuthService
from src.services.legal_entities import LegalEntitiesService
from src.services.positions import PositionsService
from src.services.sessions import SessionsService
from src.services.users import UsersService

UsersServiceDependency = Annotated[UsersService, Depends()]
AuthServiceDependency = Annotated[AuthService, Depends()]
SessionsServiceDependency = Annotated[SessionsService, Depends()]
PositionsServiceDependency = Annotated[PositionsService, Depends()]
LegalEntitiesServiceDependency = Annotated[LegalEntitiesService, Depends()]


async def get_current_user(
    request: Request,
    users_service: UsersServiceDependency,
    sessions_service: SessionsServiceDependency,
) -> UserRead:
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def active_user(
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def hr_user(
    current_user: Annotated[UserRead, Depends(active_user)],
) -> UserRead:
    if current_user.role != UserRole.HR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: HR role required",
        )
    return current_user


async def admin_user(
    current_user: Annotated[UserRead, Depends(active_user)],
) -> UserRead:
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin role required",
        )
    return current_user
