from fastapi import APIRouter, HTTPException, Response

from src.api.v1.dependencies import UsersServiceDependency
from src.schemas.user import (
    UserLogin,
    UserPasswordUpdate,
    UserRegister,
    UserVerified,
    UserVerify,
)
from src.utils.jwt import create_access_token
from src.utils.security import hash_password, verify_password

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
    user_service: UsersServiceDependency,  # Should be in AuthService
):
    user = await user_service.get(user_register.id)
    if not user or user.is_verified:
        raise HTTPException(
            status_code=400, detail="User not found or already verified"
        )

    hashed_password = hash_password(user_register.password)
    password_update = UserPasswordUpdate(password=hashed_password)

    password_updated = user_service.update_password(user.id, password_update)
    verification_completed = user_service.verify(user.id)

    is_updated = password_updated and verification_completed
    return {"is_success": is_updated}


@router.post("/signin")
async def signin(
    user_login: UserLogin,
    response: Response,
    user_service: UsersServiceDependency,  # Should be AuthService
):
    user = await user_service.get_by_email(user_login.email)
    if not user or not user.is_verified:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    is_valid_password = verify_password(user_login.password, user.password)
    if not is_valid_password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(str(user.id), str(user.role.value))

    response.set_cookie(key="access_token", value=token)
    return {"is_success": True}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"is_success": True}
