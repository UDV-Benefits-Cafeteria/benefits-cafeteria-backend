from fastapi import APIRouter, HTTPException, Request, Response

from src.api.v1.dependencies import (
    AuthServiceDependency,
    SessionsServiceDependency,
    UsersServiceDependency,
)
from src.config import settings
from src.schemas.user import UserLogin, UserRegister, UserVerified, UserVerify
from src.utils.security import verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/verify", response_model=UserVerified)
async def verify_email(
    email_data: UserVerify,
    service: UsersServiceDependency,
):
    user = await service.get_by_email(email_data.email)
    if user and not user.is_verified:
        return UserVerified(id=user.id)
    else:
        raise HTTPException(
            status_code=400, detail="User not found or already verified"
        )


@router.post("/signup")
async def signup(
    user_register: UserRegister,
    auth_service: AuthServiceDependency,
):
    user = await auth_service.get_auth_data(user_id=user_register.id)

    if not user or user.is_verified:
        raise HTTPException(
            status_code=400, detail="User not found or already verified"
        )

    if user.password:
        raise HTTPException(
            status_code=400, detail="Password already set for this user"
        )

    password_updated = await auth_service.update_password(
        user.id, user_register.password
    )
    verification_completed = await auth_service.verify_user(user.id)

    is_updated = password_updated and verification_completed
    return {"is_success": is_updated}


@router.post("/signin")
async def signin(
    user_login: UserLogin,
    response: Response,
    auth_service: AuthServiceDependency,
    sessions_service: SessionsServiceDependency,
):
    user = await auth_service.get_auth_data(email=user_login.email)

    if not user or not user.is_verified:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user.password:
        raise HTTPException(status_code=400, detail="Password not set for this user")

    is_valid_password = verify_password(user_login.password, user.password)
    if not is_valid_password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    session_id = await sessions_service.create_session(
        user.id, settings.SESSION_EXPIRE_TIME
    )

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.SESSION_EXPIRE_TIME,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return {"is_success": True}


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    sessions_service: SessionsServiceDependency,
):
    session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if session_id:
        await sessions_service.delete_session(session_id)
        response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return {"is_success": True}
