from typing import Annotated

from fastapi import Depends, HTTPException, Request

from src.config import settings
from src.schemas.user import UserRead
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
        raise HTTPException(status_code=400, detail="Not authenticated")

    session = await sessions_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Session expired or invalid")

    user = await users_service.read_by_id(session.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    return user
